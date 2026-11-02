"""Testes do servidor de leads e das regras. Execução (na pasta site_crivia):
    python -I -m unittest discover -s tests -v
Sem dependências externas.
"""
import copy
import io
import json
import os
import sqlite3
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stderr

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "servidor"))
import regras_leads as R  # noqa: E402
import servidor_leads as S  # noqa: E402


def base(entrada="underperforming"):
    """Payload mínimo válido para cada rota."""
    sc = {"entryPath": entrada, "audienceContext": "contractor", "decisionRole": "decides", "stage": "execution",
          "issues": ["schedule"], "consequences": ["penalty"], "decisionHorizon": "up_to_7_days", "city": "Belo Horizonte", "state": "MG",
          "estimatedRange": "undisclosed", "availableDocuments": ["contract", "schedule", "projects"],
          "narrative": "O cronograma atrasou e precisamos decidir como recuperar sem estourar a margem do contrato.", "branchSpecificData": {}}
    if entrada == "decision_support":
        sc.update({"issues": [], "branchSpecificData": {"evaluate": ["land", "budget_costs"]}})
    elif entrada == "visual_communication":
        sc.update({"issues": [], "stage": None, "consequences": [], "branchSpecificData": {
            "deliverable": "image_or_3d", "purpose": "present_project", "audience": "investor", "referenceLevel": "plans_projects"}})
    elif entrada == "ai_decision_engineering":
        sc.update({"issues": [], "stage": None, "branchSpecificData": {
            "aiSituation": "already_using", "difficulties": ["rework"], "areas": ["operations"], "peopleRange": "11_to_50", "affectedProcess": "planning"}})
    elif entrada == "other_or_unsure":
        sc.update({"issues": [], "stage": None, "branchSpecificData": {"decisionNeeded": "Definir se contratamos uma revisão do projeto."}})
    return {"idempotencyKey": "chave-" + entrada.replace("_", "-") + "-0001", "schemaVersion": 1,
            "source": {"originCta": "produtos", "productHint": "P06", "deviceCategory": "desktop", "utmSource": "teste"},
            "scenario": sc,
            "contact": {"name": "Maria Souza", "organization": "Construtora Alfa", "roleTitle": "Diretora", "preferredChannel": "email",
                        "email": "Maria@Exemplo.com.br", "preferredContactPeriod": "morning"},
            "privacy": {"privacyNoticeVersion": "minuta-0", "acknowledged": True, "marketingConsent": False}}


class TestValidacao(unittest.TestCase):
    def test_todas_as_rotas_validam(self):
        for rota in R.ENTRY_PATHS:
            lead = R.validar_lead(base(rota))
            self.assertEqual(lead["scenario"]["entryPath"], rota)
            self.assertFalse(lead["privacy"]["marketingConsent"])
            self.assertEqual(lead["contact"]["email"], "maria@exemplo.com.br")

    def test_campo_desconhecido_e_enum_invalido(self):
        p = base(); p["scenario"]["extra"] = 1
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertIn("scenario.extra", e.exception.campos)
        p = base(); p["scenario"]["entryPath"] = "hack"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)

    def test_limites_de_selecao_e_tamanho(self):
        p = base(); p["scenario"]["issues"] = ["schedule", "quality", "supplier", "scope_change"]
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertEqual(e.exception.campos["scenario.issues"], "limite_de_selecoes")
        p = base(); p["scenario"]["consequences"] = ["penalty", "stoppage", "other"]
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["scenario"]["narrative"] = "x" * 701
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertEqual(e.exception.campos["scenario.narrative"], "tamanho")

    def test_branch_exige_campos_da_rota(self):
        p = base("decision_support"); p["scenario"]["branchSpecificData"] = {}
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base("visual_communication"); p["scenario"]["branchSpecificData"]["extra"] = "x"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base("ai_decision_engineering"); p["scenario"]["branchSpecificData"]["difficulties"] = []
        with self.assertRaises(R.ErroValidacao):   # "já utiliza" exige ao menos uma dificuldade
            R.validar_lead(p)
        p = base("ai_decision_engineering"); p["scenario"]["branchSpecificData"].update({"aiSituation": "evaluating", "difficulties": ["rework"]})
        self.assertEqual(R.validar_lead(p)["scenario"]["branchSpecificData"]["difficulties"], [])

    def test_telefone_email_e_canal(self):
        self.assertEqual(R.normalizar_telefone("(31) 98888-7777"), "+5531988887777")
        self.assertEqual(R.normalizar_telefone("+55 31 3333-4444"), "+553133334444")
        self.assertEqual(R.normalizar_telefone("5531988887777"), "+5531988887777")
        self.assertEqual(R.normalizar_telefone("+351 912 345 678"), "+351912345678")
        for ruim in ("123", "abc", "(00) 98888-7777", "31 8888-77"):
            self.assertIsNone(R.normalizar_telefone(ruim))
        p = base(); p["contact"]["preferredChannel"] = "whatsapp"; p["contact"].pop("email")
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertEqual(e.exception.campos["contact.phone"], "obrigatorio")
        p = base(); p["contact"]["email"] = "sem-arroba"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)

    def test_organizacao_so_obrigatoria_em_contexto_empresarial(self):
        p = base(); p["contact"].pop("organization")
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p["scenario"]["audienceContext"] = "owner_investor"
        R.validar_lead(p)

    def test_privacidade_e_marketing(self):
        p = base(); p["privacy"]["acknowledged"] = False
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["privacy"]["marketingConsent"] = True
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertEqual(e.exception.campos["privacy.marketingConsent"], "nao_oferecido")

    def test_dado_pessoal_no_texto_livre_e_mascarado_e_sinalizado(self):
        p = base(); p["scenario"]["narrative"] = "Meu CPF é 123.456.789-09 e o contrato está atrasado há semanas."
        lead = R.validar_lead(p)
        self.assertNotIn("123.456.789-09", lead["scenario"]["narrative"])
        self.assertTrue(lead["sensitiveContentSuspected"])

    def test_parametros_de_origem_so_na_lista(self):
        p = base(); p["source"]["originCta"] = "<script>"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["source"]["productHint"] = "P99"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["source"]["utmSource"] = "<b>x</b>"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)


class TestPontuacao(unittest.TestCase):
    def test_prioridade_a_b_c_e_nunca_rejeita(self):
        alta = R.enquadrar(R.validar_lead(base()))
        self.assertEqual(alta["priority"], "A")
        self.assertGreaterEqual(alta["totalScore"], 10)
        p = base("other_or_unsure")
        p["scenario"].update({"decisionRole": "early_research", "decisionHorizon": "undefined", "availableDocuments": ["none_organized"],
                              "consequences": ["other"], "narrative": "Quero entender o que vocês fazem."})
        baixa = R.enquadrar(R.validar_lead(p))
        self.assertEqual(baixa["priority"], "C")
        self.assertIn("organized_documents", baixa["missingInformation"])
        meio = base(); meio["scenario"].update({"decisionRole": "technical_participant", "decisionHorizon": "after_90_days", "consequences": ["other"],
                                                "availableDocuments": ["contract"]})
        self.assertEqual(R.enquadrar(R.validar_lead(meio))["priority"], "B")

    def test_produtos_candidatos_por_rota(self):
        self.assertEqual(R.produtos_candidatos(R.validar_lead(base("decision_support"))), ["P03", "P04"])
        self.assertEqual(R.produtos_candidatos(R.validar_lead(base("visual_communication"))), ["CV01"])
        self.assertEqual(R.produtos_candidatos(R.validar_lead(base("ai_decision_engineering"))), ["IA"])
        self.assertEqual(R.produtos_candidatos(R.validar_lead(base("other_or_unsure"))), [])
        p = base(); p["scenario"]["issues"] = ["undefined_responsibilities", "measurement_receipt"]
        cand = R.produtos_candidatos(R.validar_lead(p))
        self.assertIn("P01", cand); self.assertIn("P09", cand)

    def test_faixas_vem_da_configuracao_central(self):
        self.assertEqual(R.PONTUACAO["faixas"], {"A": 10, "B": 6})
        self.assertEqual(R.SCORE_RULE_VERSION, "score-v1")


class TestHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ.update({"CRIVIA_DB": os.path.join(cls.tmp.name, "t.db"), "CRIVIA_RATE_MAX": "1000",
                           "CRIVIA_ALLOWED_ORIGINS": "http://localhost:8080"})
        os.environ.pop("TURNSTILE_SECRET", None)
        cls.srv = S.criar_servidor(porta=0)
        cls.url = "http://127.0.0.1:%d" % cls.srv.server_address[1]
        cls.t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.t.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.srv.server_close(); cls.srv.estado.con.close(); cls.tmp.cleanup()

    def post(self, caminho, corpo, cabecalhos=None, bruto=None):
        dados = bruto if bruto is not None else json.dumps(corpo).encode()
        h = {"Content-Type": "application/json", "Origin": "http://localhost:8080"}
        h.update(cabecalhos or {})
        req = urllib.request.Request(self.url + caminho, data=dados, headers=h, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read() or b"{}"), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}"), dict(e.headers)

    def linhas(self):
        return self.srv.estado.con.execute("SELECT COUNT(*) FROM leads").fetchone()[0]

    def test_envio_completo_e_idempotencia(self):
        p = base(); p["idempotencyKey"] = "idem-completo-0001"
        antes = self.linhas()
        s1, r1, h1 = self.post("/api/leads", p)
        self.assertEqual(s1, 201); self.assertTrue(r1["id"]); self.assertTrue(r1["detailsToken"])
        self.assertEqual(h1.get("Access-Control-Allow-Origin"), "http://localhost:8080")
        s2, r2, _ = self.post("/api/leads", p)
        self.assertEqual(s2, 200); self.assertEqual(r2["id"], r1["id"]); self.assertTrue(r2["duplicado"])
        self.assertEqual(self.linhas(), antes + 1)
        con = self.srv.estado.con
        data = json.loads(con.execute("SELECT data_json FROM leads WHERE id=?", (r1["id"],)).fetchone()[0])
        self.assertEqual(data["qualification"]["priority"], "A")
        self.assertFalse(data["privacy"]["marketingConsent"])
        self.assertEqual(data["privacy"]["privacyNoticeVersion"], "minuta-0")
        self.assertNotIn("ip", json.dumps(data).lower().replace("zip", ""))   # IP bruto nunca no registro
        fila = con.execute("SELECT lead_id, categoria, prioridade FROM outbox WHERE lead_id=?", (r1["id"],)).fetchone()
        self.assertIsNotNone(fila)
        self.assertNotIn("Maria", json.dumps(fila))                            # notificação sem dados pessoais

    def test_validacao_no_servidor_nao_ecoa_valores(self):
        p = base(); p["idempotencyKey"] = "idem-invalido-0001"; p["scenario"]["entryPath"] = "SEGREDO<script>"
        s, r, _ = self.post("/api/leads", p)
        self.assertEqual(s, 422)
        self.assertNotIn("SEGREDO", json.dumps(r))

    def test_xss_e_sql_injection_sao_apenas_texto(self):
        p = base(); p["idempotencyKey"] = "idem-xss-sql-0001"
        p["scenario"]["narrative"] = "<img src=x onerror=alert(1)> ');DROP TABLE leads;-- fim"
        p["contact"]["name"] = "Ana Maria"
        s, r, _ = self.post("/api/leads", p)
        self.assertEqual(s, 201)
        existe = self.srv.estado.con.execute("SELECT name FROM sqlite_master WHERE name='leads'").fetchone()
        self.assertIsNotNone(existe)
        data = json.loads(self.srv.estado.con.execute("SELECT data_json FROM leads WHERE id=?", (r["id"],)).fetchone()[0])
        self.assertIn("DROP TABLE", data["scenario"]["narrative"])            # guardado como texto; o front usa textContent

    def test_armadilha_de_robo_nao_grava(self):
        p = base(); p["idempotencyKey"] = "idem-robo-00001"; p["website"] = "http://spam"
        antes = self.linhas()
        s, r, _ = self.post("/api/leads", p)
        self.assertEqual(s, 201)
        self.assertEqual(self.linhas(), antes)

    def test_limites_de_protocolo(self):
        s, _, _ = self.post("/api/leads", None, bruto=b"x" * (S.LIMITE_CORPO + 10))
        self.assertEqual(s, 413)
        s, _, _ = self.post("/api/leads", None, bruto=b"{nao-json")
        self.assertEqual(s, 400)
        s, _, _ = self.post("/api/leads", base(), cabecalhos={"Content-Type": "text/plain"})
        self.assertEqual(s, 415)
        s, _, _ = self.post("/api/leads", base(), cabecalhos={"Origin": "http://malicioso.example"})
        self.assertEqual(s, 403)
        p = base(); p["scenario"]["availableDocuments"] = ["contract"] * 50
        p["idempotencyKey"] = "idem-array-0001"
        s, _, _ = self.post("/api/leads", p)
        self.assertEqual(s, 422)

    def test_detalhes_exigem_token(self):
        p = base(); p["idempotencyKey"] = "idem-detalhes-001"
        _, r, _ = self.post("/api/leads", p)
        s, _, _ = self.post("/api/leads/%s/detalhes" % r["id"], {"additionalInfo": "Mais contexto sobre o contrato."}, {"X-Lead-Token": "falso"})
        self.assertEqual(s, 403)
        s, _, _ = self.post("/api/leads/%s/detalhes" % r["id"], {"additionalInfo": "Mais contexto sobre o contrato."}, {"X-Lead-Token": r["detailsToken"]})
        self.assertEqual(s, 200)
        det = self.srv.estado.con.execute("SELECT details_json FROM leads WHERE id=?", (r["id"],)).fetchone()[0]
        self.assertIn("Mais contexto", det)
        s, _, _ = self.post("/api/leads/%s/detalhes" % r["id"], {"additionalInfo": "ok", "x": 1}, {"X-Lead-Token": r["detailsToken"]})
        self.assertEqual(s, 422)

    def test_logs_nao_contem_o_formulario(self):
        p = base(); p["idempotencyKey"] = "idem-log-0000001"; p["contact"]["name"] = "Fulano Sigiloso"
        buf = io.StringIO()
        with redirect_stderr(buf):
            self.post("/api/leads", p)
        saida = buf.getvalue() + json.dumps(self.srv.estado.con.execute("SELECT * FROM security_log").fetchall())
        self.assertNotIn("Fulano", saida)
        self.assertNotIn("exemplo.com.br", saida)
        self.assertIn("/api/leads", buf.getvalue())

    def test_limite_de_requisicoes(self):
        self.srv.estado.cfg["limite_max"] = 3
        self.srv.estado.janelas.clear()
        codigos = []
        for i in range(5):
            p = base(); p["idempotencyKey"] = "idem-limite-%04d" % i
            codigos.append(self.post("/api/leads", p)[0])
        self.srv.estado.cfg["limite_max"] = 1000
        self.srv.estado.janelas.clear()
        self.assertEqual(codigos[:3], [201, 201, 201])
        self.assertEqual(codigos[3:], [429, 429])

    def test_saude(self):
        with urllib.request.urlopen(self.url + "/api/saude", timeout=5) as r:
            self.assertEqual(json.loads(r.read()), {"ok": True})


class TestRetencao(unittest.TestCase):
    def test_expurgo_recusa_sem_politica_e_respeita_suspensao(self):
        with tempfile.TemporaryDirectory() as d:
            for k in ("LEAD_RETENTION_POLICY_ID", "LEAD_RETENTION_DAYS", "UNQUALIFIED_LEAD_RETENTION_DAYS", "SECURITY_LOG_RETENTION_DAYS"):
                os.environ.pop(k, None)
            os.environ["CRIVIA_DB"] = os.path.join(d, "r.db")
            self.assertEqual(S.cmd_expurgar(), 2)
            os.environ.update({"LEAD_RETENTION_POLICY_ID": "teste", "LEAD_RETENTION_DAYS": "1", "UNQUALIFIED_LEAD_RETENTION_DAYS": "1", "SECURITY_LOG_RETENTION_DAYS": "1"})
            S.cmd_suspender("on")
            self.assertEqual(S.cmd_expurgar(), 3)
            S.cmd_suspender("off")
            self.assertEqual(S.cmd_expurgar(), 0)
            for k in ("LEAD_RETENTION_POLICY_ID", "LEAD_RETENTION_DAYS", "UNQUALIFIED_LEAD_RETENTION_DAYS", "SECURITY_LOG_RETENTION_DAYS"):
                os.environ.pop(k, None)


if __name__ == "__main__":
    unittest.main()
