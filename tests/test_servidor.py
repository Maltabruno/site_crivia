"""Testes do servidor de leads e das regras (esquema v2, página única). Execução (na pasta site_crivia):
    python -I -m unittest discover -s tests -v
Sem dependências externas.
"""
import io
import json
import os
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

BH = "3106200"   # Belo Horizonte (MG)
SP_CAPITAL = "3550308"


def base(situacao="obra_contrato_dificuldade"):
    """Payload mínimo válido (modo Brasil)."""
    return {"idempotencyKey": "chave-" + situacao.replace("_", "-") + "-0001", "schemaVersion": 3, "formVersion": "form-3", "elapsedMs": 45000,
            "source": {"originCta": "produtos", "productHint": "P06", "deviceCategory": "desktop", "utmSource": "teste"},
            "scenario": {"situationCodes": [situacao], "contextAnswerCode": "running" if situacao == "obra_contrato_dificuldade" else "unknown", "audienceProfiles": ["contractor"], "decisionRole": "decides",
                         "location": {"type": "brazil", "countryCode": "BR", "stateCode": "MG", "cityCode": BH, "cityName": "Belo Horizonte"},
                         "narrative": "O cronograma atrasou e precisamos decidir como recuperar sem estourar a margem do contrato, que já tem multa prevista.",
                         "urgencies": ["this_week"], "consequences": ["penalty", "stoppage"], "documents": ["partial"], "estimatedRanges": ["1m_to_10m"]},
            "contact": {"name": "Maria Souza", "organization": "Construtora Alfa", "preferredChannel": "email", "email": "Maria@Exemplo.com.br", "contactPeriods": ["morning"]},
            "privacy": {"privacyNoticeVersion": "minuta-0", "acknowledged": True, "marketingConsent": False}}


def exterior():
    p = base()
    p["idempotencyKey"] = "chave-exterior-0001"
    p["scenario"]["location"] = {"type": "international", "countryCode": "PT", "cityName": "Lisboa", "foreignRegion": "Lisboa"}
    return p


class TestLocalidades(unittest.TestCase):
    def test_tabelas_oficiais(self):
        self.assertEqual(len(R.estados()), 27)
        self.assertIn("DF", R.estados())
        self.assertEqual(R.municipios("MG")[BH], "Belo Horizonte")
        self.assertEqual(R.municipios("DF"), {"5300108": "Brasília"})
        self.assertGreater(sum(len(R.municipios(u)) for u in R.estados()), 5500)
        self.assertEqual(R.paises()["BR"], "Brasil")
        for uf, (_n, cod) in R.estados().items():            # o código do município começa com o código da UF
            self.assertTrue(all(c.startswith(cod) for c in R.municipios(uf)), uf)


class TestValidacao(unittest.TestCase):
    def test_brasil_valido_e_normalizado(self):
        lead = R.validar_lead(base())
        loc = lead["scenario"]["location"]
        self.assertEqual((loc["countryCode"], loc["stateCode"], loc["stateName"], loc["cityCode"], loc["cityName"]), ("BR", "MG", "Minas Gerais", BH, "Belo Horizonte"))
        self.assertEqual(lead["contact"]["email"], "maria@exemplo.com.br")
        self.assertFalse(lead["privacy"]["marketingConsent"])
        self.assertEqual(lead["scenario"]["situationLabels"], ["Obra ou contrato com dificuldade"])
        self.assertEqual(lead["scenario"]["contextAnswerLabel"], "Em execução")

    def test_todas_as_situacoes_validam(self):
        for cod in R.SITUATIONS:
            R.validar_lead(base(cod))

    def test_exterior_valido_e_sem_campos_do_brasil(self):
        loc = R.validar_lead(exterior())["scenario"]["location"]
        self.assertEqual((loc["type"], loc["countryCode"], loc["countryName"], loc["cityName"], loc["stateCode"], loc["cityCode"]), ("international", "PT", "Portugal", "Lisboa", "", ""))
        p = exterior(); p["scenario"]["location"]["stateCode"] = "SP"       # resíduo inconsistente do modo Brasil
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertEqual(e.exception.campos["scenario.location.stateCode"], "campo_desconhecido")

    def test_cidade_de_outra_uf_ou_adulterada_e_rejeitada(self):
        p = base(); p["scenario"]["location"].update({"stateCode": "SP"})            # BH não pertence a SP
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertEqual(e.exception.campos["scenario.location.cityCode"], "valor_invalido")
        p = base(); p["scenario"]["location"]["cityCode"] = "9999999"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["scenario"]["location"]["cityName"] = "Cidade Inventada"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["scenario"]["location"].update({"stateCode": "SP", "cityCode": SP_CAPITAL, "cityName": "São Paulo"})
        R.validar_lead(p)

    def test_pais_invalido_e_brasil_no_modo_exterior(self):
        p = exterior(); p["scenario"]["location"]["countryCode"] = "ZZ"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = exterior(); p["scenario"]["location"]["countryCode"] = "BR"
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertEqual(e.exception.campos["scenario.location.countryCode"], "use_modo_brasil")

    def test_campo_desconhecido_enum_e_resposta_de_outra_situacao(self):
        p = base(); p["scenario"]["extra"] = 1
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertIn("scenario.extra", e.exception.campos)
        p = base(); p["scenario"]["situationCodes"] = ["hack"]
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["scenario"]["contextAnswerCode"] = "deadline"             # resposta de outra situação
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["scenario"].pop("contextAnswerCode")                       # a pergunta contextual é opcional
        self.assertEqual(R.validar_lead(p)["scenario"]["contextAnswerCode"], "")

    def test_relato_limites_html_e_quebras_de_linha(self):
        p = base(); p["scenario"]["narrative"] = "curto"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["scenario"]["narrative"] = "x" * 1201
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertEqual(e.exception.campos["scenario.narrative"], "tamanho")
        p = base(); p["scenario"]["narrative"] = "<img src=x onerror=alert(1)> texto suficiente"
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertEqual(e.exception.campos["scenario.narrative"], "html_nao_permitido")
        p = base(); p["scenario"]["narrative"] = "Primeira linha com acentuação e ção.\n\nSegunda linha continua aqui."
        self.assertIn("\n\n", R.validar_lead(p)["scenario"]["narrative"])

    def test_telefone_email_e_canal(self):
        self.assertEqual(R.normalizar_telefone("(31) 98888-7777"), "+5531988887777")
        self.assertEqual(R.normalizar_telefone("+351 912 345 678"), "+351912345678")
        for ruim in ("123", "abc", "(00) 98888-7777", "31 8888-77"):
            self.assertIsNone(R.normalizar_telefone(ruim))
        p = base(); p["contact"]["preferredChannel"] = "whatsapp"; p["contact"].pop("email")
        with self.assertRaises(R.ErroValidacao) as e:
            R.validar_lead(p)
        self.assertEqual(e.exception.campos["contact.phone"], "obrigatorio")
        p["contact"]["phone"] = "+351 912 345 678"
        self.assertEqual(R.validar_lead(p)["contact"]["phone"], "+351912345678")
        p = base(); p["contact"]["phone"] = "(31) 98888-7777"                    # segundo canal opcional
        self.assertEqual(R.validar_lead(p)["contact"]["phone"], "+5531988887777")
        p = base(); p["contact"]["email"] = "sem-arroba"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["contact"]["preferredChannel"] = "phone_call"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)

    def test_perguntas_opcionais_do_formulario(self):
        lead = R.validar_lead(base())
        s = lead["scenario"]
        self.assertEqual((s["urgencies"], s["consequences"], s["documents"], s["estimatedRanges"], lead["contact"]["contactPeriods"]),
                         (["this_week"], ["penalty", "stoppage"], ["partial"], ["1m_to_10m"], ["morning"]))
        p = base()
        for campo in ("urgencies", "consequences", "documents", "estimatedRanges"):
            p["scenario"].pop(campo)
        p["contact"].pop("contactPeriods")
        s = R.validar_lead(p)["scenario"]                                         # todas opcionais
        self.assertEqual((s["urgencies"], s["consequences"], s["documents"], s["estimatedRanges"]), ([], [], [], []))
        for campo, valor in (("urgencies", ["ontem"]), ("urgencies", "this_week"), ("consequences", ["xx"]), ("documents", ["talvez"]), ("estimatedRanges", ["1 bilhão"])):
            p = base(); p["scenario"][campo] = valor
            with self.assertRaises(R.ErroValidacao):
                R.validar_lead(p)
        p = base(); p["contact"]["contactPeriods"] = ["madrugada"]
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)

    def test_multipla_escolha(self):
        # várias opções em todas as perguntas; o servidor devolve na ordem da lista, sem repetição
        p = base()
        p["scenario"].update({"situationCodes": ["atraso_custo_margem", "obra_contrato_dificuldade", "atraso_custo_margem"], "contextAnswerCode": None,
                              "audienceProfiles": ["technical_team", "contractor"], "urgencies": ["this_month", "immediate"],
                              "consequences": list(R.CONSEQUENCES), "documents": ["partial", "yes"], "estimatedRanges": ["10m_to_50m", "1m_to_10m"]})
        p["contact"]["contactPeriods"] = ["evening", "morning"]
        lead = R.validar_lead(p)
        s = lead["scenario"]
        self.assertEqual(s["situationCodes"], ["obra_contrato_dificuldade", "atraso_custo_margem"])
        self.assertEqual(s["situationLabels"], ["Obra ou contrato com dificuldade", "Atraso, custo, produtividade ou perda de margem"])
        self.assertEqual(s["audienceProfiles"], ["contractor", "technical_team"])
        self.assertEqual((s["urgencies"], s["documents"], s["estimatedRanges"]), (["immediate", "this_month"], ["yes", "partial"], ["1m_to_10m", "10m_to_50m"]))
        self.assertEqual(s["consequences"], list(R.CONSEQUENCES))                  # "marcar todas" não tem limite
        self.assertEqual(lead["contact"]["contactPeriods"], ["morning", "evening"])
        # a pergunta curta de contexto só vale com uma única situação
        p["scenario"]["contextAnswerCode"] = "running"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        # situação e perfil exigem ao menos uma escolha
        for campo in ("situationCodes", "audienceProfiles"):
            for valor in ([], None):
                q = base(); q["scenario"][campo] = valor
                with self.assertRaises(R.ErroValidacao):
                    R.validar_lead(q)

    def test_opcoes_exclusivas_nao_combinam_com_outras(self):
        for campo, exclusiva, outra in (("urgencies", "undefined", "immediate"), ("documents", "unknown", "yes"), ("estimatedRanges", "undisclosed", "up_to_100k"),
                                        ("estimatedRanges", "unknown", "undisclosed"), ("situationCodes", "outra_nao_sei", "obra_contrato_dificuldade")):
            p = base(); p["scenario"][campo] = [exclusiva, outra]; p["scenario"]["contextAnswerCode"] = None
            with self.assertRaises(R.ErroValidacao) as e:
                R.validar_lead(p)
            self.assertEqual(e.exception.campos["scenario." + campo], "opcoes_incompativeis")
        p = base(); p["contact"]["contactPeriods"] = ["any", "morning"]
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["scenario"]["documents"] = ["unknown"]                      # sozinha, vale
        self.assertEqual(R.validar_lead(p)["scenario"]["documents"], ["unknown"])

    def test_respostas_em_formato_longo(self):
        p = base()
        p["scenario"].update({"situationCodes": ["obra_contrato_dificuldade", "atraso_custo_margem"], "contextAnswerCode": None, "audienceProfiles": ["contractor", "technical_team"]})
        linhas = R.respostas(R.validar_lead(p))
        self.assertIn(("situation", "atraso_custo_margem", "Atraso, custo, produtividade ou perda de margem", 2), linhas)
        self.assertEqual([x[1] for x in linhas if x[0] == "audience_profile"], ["contractor", "technical_team"])
        self.assertEqual([x[1] for x in linhas if x[0] == "consequence"], ["penalty", "stoppage"])
        self.assertEqual([x[1] for x in linhas if x[0] == "decision_role"], ["decides"])

    def test_organizacao_e_opcional(self):
        p = base(); p["contact"].pop("organization")
        self.assertEqual(R.validar_lead(p)["contact"]["organization"], "")

    def test_privacidade_e_marketing(self):
        p = base(); p["privacy"]["acknowledged"] = False
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)
        p = base(); p["privacy"]["marketingConsent"] = True
        self.assertTrue(R.validar_lead(p)["privacy"]["marketingConsent"])
        p = base(); p["privacy"]["marketingConsent"] = "sim"
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)

    def test_dado_pessoal_no_texto_livre_e_mascarado_e_sinalizado(self):
        p = base(); p["scenario"]["narrative"] = "Meu CPF é 123.456.789-09 e o contrato está atrasado há semanas."
        lead = R.validar_lead(p)
        self.assertNotIn("123.456.789-09", lead["scenario"]["narrative"])
        self.assertTrue(lead["sensitiveContentSuspected"])

    def test_parametros_de_origem_so_na_lista(self):
        for campo, valor in (("originCta", "<script>"), ("productHint", "P99"), ("utmSource", "<b>x</b>")):
            p = base(); p["source"][campo] = valor
            with self.assertRaises(R.ErroValidacao):
                R.validar_lead(p)

    def test_tempo_minimo_e_obrigatoriedade(self):
        self.assertTrue(R.envio_rapido_demais({"elapsedMs": 800}))
        self.assertFalse(R.envio_rapido_demais({"elapsedMs": 45000}))
        p = base(); p.pop("elapsedMs")
        with self.assertRaises(R.ErroValidacao):
            R.validar_lead(p)

    def test_complemento_opcional(self):
        self.assertEqual(R.validar_detalhes({"urgency": "this_week", "documents": "partial"}), {"urgency": "this_week", "documents": "partial"})
        for ruim in ({}, {"urgency": "ontem"}, {"urgency": "immediate", "extra": 1}):
            with self.assertRaises(R.ErroValidacao):
                R.validar_detalhes(ruim)


class TestPontuacao(unittest.TestCase):
    def test_prioridade_a_b_c_e_nunca_rejeita(self):
        alta = R.enquadrar(R.validar_lead(base()))
        self.assertEqual(alta["priority"], "A")
        p = base("outra_nao_sei")
        p["scenario"].update({"decisionRole": "gathering", "audienceProfiles": ["other"], "contextAnswerCode": "unknown", "narrative": "Quero entender o que vocês fazem.",
                              "urgencies": ["undefined"], "consequences": [], "documents": ["no"], "estimatedRanges": ["unknown"]})
        baixa = R.enquadrar(R.validar_lead(p))
        self.assertEqual(baixa["priority"], "C")
        self.assertIn("context_answer", baixa["missingInformation"])
        self.assertTrue({"decision_horizon", "documents", "estimated_range"} <= set(baixa["missingInformation"]))
        self.assertEqual(alta["timingScore"], 2); self.assertEqual(alta["consequenceScore"], 2); self.assertEqual(alta["readinessScore"], 1)
        meio = base(); meio["scenario"].update({"decisionRole": "recommends", "audienceProfiles": ["owner_investor"], "narrative": "x" * 100,
                                                "urgencies": ["undefined"], "consequences": [], "documents": ["unknown"]})
        self.assertEqual(R.enquadrar(R.validar_lead(meio))["priority"], "B")

    def test_produtos_candidatos_sao_hipotese_interna(self):
        self.assertEqual(R.produtos_candidatos(R.validar_lead(base("projeto_terreno_propostas"))), ["P02", "P03", "P05"])
        self.assertEqual(R.produtos_candidatos(R.validar_lead(base("comunicacao_ia_3d"))), ["CV01"])
        self.assertEqual(R.produtos_candidatos(R.validar_lead(base("outra_nao_sei"))), [])

    def test_pontuacao_com_multipla_escolha_usa_a_melhor_opcao(self):
        p = base("outra_nao_sei")
        p["scenario"].update({"audienceProfiles": ["other", "contractor"], "urgencies": ["this_month", "immediate"], "documents": ["no", "yes"], "contextAnswerCode": None})
        q = R.enquadrar(R.validar_lead(p))
        self.assertEqual((q["audienceScore"], q["timingScore"], q["readinessScore"]), (2, 2, 2))
        m = base(); m["scenario"].update({"situationCodes": ["comunicacao_ia_3d", "projeto_terreno_propostas", "obra_contrato_dificuldade"], "contextAnswerCode": None})
        qm = R.enquadrar(R.validar_lead(m))
        self.assertEqual(qm["candidateProducts"], ["P01", "P02", "P03", "P05", "CV01"])   # união na ordem da lista, sem repetir
        self.assertNotIn("context_answer", qm["missingInformation"])

    def test_faixas_vem_da_configuracao_central(self):
        self.assertEqual(R.PONTUACAO["faixas"], {"A": 10, "B": 6})
        self.assertEqual(R.SCORE_RULE_VERSION, "score-v3")


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

    def envelope(self, acao, dados):
        return self.post("/", {"action": acao, "data": dados}, {"Content-Type": "text/plain;charset=utf-8"})[1]

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
        self.assertIsNone(data["privacy"]["marketingConsentAt"])
        self.assertEqual(data["scenario"]["location"]["cityCode"], BH)
        self.assertNotIn("ip", json.dumps(data).lower().replace("zip", ""))   # IP bruto nunca no registro
        fila = con.execute("SELECT lead_id, categoria, prioridade FROM outbox WHERE lead_id=?", (r1["id"],)).fetchone()
        self.assertIsNotNone(fila)
        self.assertNotIn("Maria", json.dumps(fila))                            # notificação sem dados pessoais

    def test_envelope_do_site_exterior_e_complemento(self):
        p = exterior(); p["idempotencyKey"] = "idem-envelope-001"
        r = self.envelope("submit", p)
        self.assertTrue(r["ok"]); self.assertTrue(r["publicCode"]); self.assertTrue(r["detailsToken"])
        self.assertEqual(r["confirmation"], "email")
        ruim = self.envelope("details", {"leadRef": r["id"], "token": "falso", "urgency": "immediate"})
        self.assertEqual(ruim["error"], "unauthorized")
        bom = self.envelope("details", {"leadRef": r["id"], "token": r["detailsToken"], "urgency": "immediate", "documents": "partial", "contactPeriod": "any"})
        self.assertTrue(bom["ok"])
        det = json.loads(self.srv.estado.con.execute("SELECT details_json FROM leads WHERE id=?", (r["id"],)).fetchone()[0])
        self.assertEqual(det, {"urgency": "immediate", "documents": "partial", "contactPeriod": "any"})

    def test_envio_rapido_demais_nao_grava(self):
        p = base(); p["idempotencyKey"] = "idem-rapido-0001"; p["elapsedMs"] = 500
        antes = self.linhas()
        self.assertEqual(self.envelope("submit", p)["error"], "too_fast")
        self.assertEqual(self.linhas(), antes)

    def test_validacao_no_servidor_nao_ecoa_valores(self):
        p = base(); p["idempotencyKey"] = "idem-invalido-0001"; p["scenario"]["situationCodes"] = ["SEGREDO<script>"]
        s, r, _ = self.post("/api/leads", p)
        self.assertEqual(s, 422)
        self.assertNotIn("SEGREDO", json.dumps(r))

    def test_xss_e_sql_injection_sao_apenas_texto(self):
        p = base(); p["idempotencyKey"] = "idem-xss-sql-0001"
        p["scenario"]["narrative"] = "Texto com aspas e ');DROP TABLE leads;-- fim da frase longa o bastante"
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
        p = base(); p["idempotencyKey"] = "idem-array-0001"; p["scenario"]["narrative"] = ["a"] * 50
        s, _, _ = self.post("/api/leads", p)
        self.assertEqual(s, 422)

    def test_detalhes_exigem_token(self):
        p = base(); p["idempotencyKey"] = "idem-detalhes-001"
        _, r, _ = self.post("/api/leads", p)
        s, _, _ = self.post("/api/leads/%s/detalhes" % r["id"], {"urgency": "immediate"}, {"X-Lead-Token": "falso"})
        self.assertEqual(s, 403)
        s, _, _ = self.post("/api/leads/%s/detalhes" % r["id"], {"urgency": "immediate"}, {"X-Lead-Token": r["detailsToken"]})
        self.assertEqual(s, 200)
        det = self.srv.estado.con.execute("SELECT details_json FROM leads WHERE id=?", (r["id"],)).fetchone()[0]
        self.assertIn("immediate", det)
        s, _, _ = self.post("/api/leads/%s/detalhes" % r["id"], {"urgency": "immediate", "x": 1}, {"X-Lead-Token": r["detailsToken"]})
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
