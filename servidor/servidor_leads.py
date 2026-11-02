#!/usr/bin/env python3
"""Servidor de referência do formulário "Apresentar meu cenário" (somente biblioteca padrão do Python).

Faz, no servidor, tudo o que não pode depender do navegador: validação estrita, normalização, pontuação de
prioridade, proteção contra abuso (limite de requisições, armadilha de robô, Turnstile opcional), idempotência,
gravação em SQLite, fila de notificação SEM dados pessoais e logs sem o conteúdo do formulário.

Comandos:
    python servidor_leads.py              sobe o servidor (porta CRIVIA_PORT, padrão 8787)
    python servidor_leads.py listar       lista os registros (acesso local ao banco; sem painel web)
    python servidor_leads.py expurgar     remove registros vencidos (exige a política de retenção configurada)
    python servidor_leads.py suspender on|off   suspende/retoma o descarte (guarda legal)

Variáveis de ambiente: ver docs/deployment-readiness.md. Nada aqui define base legal, retenção ou fornecedor:
tudo isso é configuração obrigatória e pendência jurídica (docs/legal-review-checklist.md).
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import socket
import sqlite3
import sys
import threading
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request as urlrequest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import regras_leads as regras  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
LIMITE_CORPO = 32 * 1024


def config():
    """Lida a cada uso, para os testes poderem alterar o ambiente."""
    e = os.environ.get
    return {
        "db": e("CRIVIA_DB", os.path.join(AQUI, "leads.db")),
        "porta": int(e("CRIVIA_PORT", "8787")),
        "origens": [o.strip() for o in e("CRIVIA_ALLOWED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",") if o.strip()],
        "versao_aviso": e("CRIVIA_PRIVACY_NOTICE_VERSION", "minuta-0"),
        "turnstile_secret": e("TURNSTILE_SECRET", ""),
        "limite_max": int(e("CRIVIA_RATE_MAX", "5")),
        "limite_janela": int(e("CRIVIA_RATE_WINDOW", "600")),
        "retencao_id": e("LEAD_RETENTION_POLICY_ID", ""),
        "retencao_dias": e("LEAD_RETENTION_DAYS", ""),
        "retencao_c_dias": e("UNQUALIFIED_LEAD_RETENTION_DAYS", ""),
        "log_seg_dias": e("SECURITY_LOG_RETENTION_DAYS", ""),
        "ia_resumo": e("AI_LEAD_SUMMARY_ENABLED", "false").lower() == "true",   # sem implementação: ver docs
    }


def agora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── banco ───────────────────────────────────────────────────────────────────────────────────────
def abrir_banco(caminho):
    novo = not os.path.exists(caminho)
    con = sqlite3.connect(caminho, timeout=10, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY, idem_key TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            status TEXT NOT NULL, schema_version INTEGER NOT NULL, priority TEXT NOT NULL, total_score INTEGER NOT NULL,
            rule_version TEXT NOT NULL, data_json TEXT NOT NULL, details_json TEXT, review_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id TEXT NOT NULL, created_at TEXT NOT NULL,
            categoria TEXT NOT NULL, prioridade TEXT NOT NULL, estado TEXT NOT NULL DEFAULT 'pendente');
        CREATE TABLE IF NOT EXISTS security_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, evento TEXT NOT NULL, detalhe TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL);
    """)
    if not con.execute("SELECT 1 FROM meta WHERE k='token_secret'").fetchone():
        con.execute("INSERT INTO meta(k,v) VALUES('token_secret', ?)", (secrets.token_hex(32),))
    con.commit()
    if novo:
        try:
            os.chmod(caminho, 0o600)
        except OSError:
            pass
    return con


class Estado:
    """Estado do processo: banco, limitador de requisições e sal do hash de IP (somente em memória)."""

    def __init__(self):
        self.cfg = config()
        self.con = abrir_banco(self.cfg["db"])
        self.trava = threading.Lock()
        self.sal = secrets.token_bytes(16)
        self.janelas = defaultdict(deque)

    def token_secret(self):
        return self.con.execute("SELECT v FROM meta WHERE k='token_secret'").fetchone()[0].encode()

    def token_do_lead(self, lead_id):
        return hmac.new(self.token_secret(), lead_id.encode(), hashlib.sha256).hexdigest()[:40]

    def registrar_seguranca(self, evento, detalhe=""):
        with self.trava:
            self.con.execute("INSERT INTO security_log(ts, evento, detalhe) VALUES(?,?,?)", (agora(), evento, detalhe[:80]))
            self.con.commit()

    def limitar(self, ip):
        """True se a requisição pode seguir. O IP só existe aqui como hash em memória; nunca vai ao banco."""
        chave = hashlib.sha256(self.sal + ip.encode()).hexdigest()
        agora_s = time.monotonic()
        janela = self.janelas[chave]
        while janela and agora_s - janela[0] > self.cfg["limite_janela"]:
            janela.popleft()
        if len(janela) >= self.cfg["limite_max"]:
            return False
        janela.append(agora_s)
        return True

    def criar_lead(self, lead):
        """Grava (ou devolve o já gravado, se a chave de idempotência se repetir). Retorna (id, criado)."""
        with self.trava:
            existente = self.con.execute("SELECT id FROM leads WHERE idem_key=?", (lead["idempotencyKey"],)).fetchone()
            if existente:
                return existente[0], False
            lead_id = uuid.uuid4().hex[:20]
            ts = agora()
            q = regras.enquadrar(lead)
            registro = {k: v for k, v in lead.items() if k != "idempotencyKey"}
            registro.update({"id": lead_id, "createdAt": ts, "status": "novo"})
            registro["privacy"]["privacyAcknowledgedAt"] = ts
            registro["qualification"] = q
            revisao = {"reviewStatus": "pending", "reviewedBy": None, "reviewedAt": None, "nextAction": None, "notes": ""}
            self.con.execute(
                "INSERT INTO leads(id, idem_key, created_at, updated_at, status, schema_version, priority, total_score, rule_version, data_json, review_json)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (lead_id, lead["idempotencyKey"], ts, ts, "novo", regras.SCHEMA_VERSION, q["priority"], q["totalScore"], q["ruleVersion"],
                 json.dumps(registro, ensure_ascii=False), json.dumps(revisao)))
            # notificação interna: sem dados pessoais (identificador, data, categoria, prioridade)
            self.con.execute("INSERT INTO outbox(lead_id, created_at, categoria, prioridade) VALUES(?,?,?,?)",
                             (lead_id, ts, lead["scenario"]["entryPath"], q["priority"]))
            self.con.commit()
            return lead_id, True

    def adicionar_detalhes(self, lead_id, detalhes):
        with self.trava:
            cur = self.con.execute("UPDATE leads SET details_json=?, updated_at=? WHERE id=?",
                                   (json.dumps(detalhes, ensure_ascii=False), agora(), lead_id))
            self.con.commit()
            return cur.rowcount == 1


def verificar_turnstile(segredo, token, ip):
    """Siteverify da Cloudflare (somente se TURNSTILE_SECRET estiver definido). Não testado sem credencial real."""
    if not token or not isinstance(token, str) or len(token) > 2048:
        return False
    dados = ("secret=%s&response=%s&remoteip=%s" % (segredo, token, ip)).encode()
    req = urlrequest.Request("https://challenges.cloudflare.com/turnstile/v0/siteverify", data=dados,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urlrequest.urlopen(req, timeout=5) as r:   # noqa: S310 (URL fixa)
            return bool(json.loads(r.read(4096)).get("success"))
    except Exception:
        return False


# ── HTTP ────────────────────────────────────────────────────────────────────────────────────────
ROTA_LEADS = re.compile(r"^/api/leads$")
ROTA_DETALHES = re.compile(r"^/api/leads/([0-9a-f]{20})/detalhes$")


def fabricar_handler(estado):
    class Handler(BaseHTTPRequestHandler):
        server_version = "CriviaLeads"
        sys_version = ""
        timeout = 10

        # logs: método, rota (sem query) e status. Nunca o corpo, nunca cabeçalhos.
        def log_message(self, formato, *args):
            pass

        def log_request(self, code="-", size="-"):
            caminho = self.path.split("?")[0]
            sys.stderr.write("%s %s %s %s\n" % (agora(), self.command, caminho, code))

        def _origem_permitida(self):
            origem = self.headers.get("Origin")
            return origem if origem and origem in estado.cfg["origens"] else None

        def _cabecalhos_comuns(self):
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            origem = self._origem_permitida()
            if origem:
                self.send_header("Access-Control-Allow-Origin", origem)
                self.send_header("Vary", "Origin")

        def _responder(self, status, corpo):
            dados = json.dumps(corpo, ensure_ascii=False).encode()
            self.send_response(status)
            self._cabecalhos_comuns()
            self.send_header("Content-Length", str(len(dados)))
            self.end_headers()
            self.wfile.write(dados)

        def do_OPTIONS(self):
            self.send_response(204)
            origem = self._origem_permitida()
            if origem:
                self.send_header("Access-Control-Allow-Origin", origem)
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Lead-Token")
                self.send_header("Access-Control-Max-Age", "600")
                self.send_header("Vary", "Origin")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self):
            if self.path.split("?")[0] == "/api/saude":
                return self._responder(200, {"ok": True})
            self._responder(404, {"erro": "nao_encontrado"})

        def _ler_json(self):
            if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
                self._responder(415, {"erro": "tipo_de_conteudo"})
                return None
            try:
                tamanho = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self._responder(411, {"erro": "tamanho_obrigatorio"})
                return None
            if tamanho <= 0 or tamanho > LIMITE_CORPO:
                self._responder(413, {"erro": "corpo_grande_demais"})
                return None
            try:
                return json.loads(self.rfile.read(tamanho).decode("utf-8"))
            except (ValueError, UnicodeDecodeError, socket.timeout):
                self._responder(400, {"erro": "json_invalido"})
                return None

        def do_POST(self):
            caminho = self.path.split("?")[0]
            origem = self.headers.get("Origin")
            if origem and origem not in estado.cfg["origens"]:
                estado.registrar_seguranca("origem_recusada")
                return self._responder(403, {"erro": "origem_nao_permitida"})
            ip = self.client_address[0]
            if not estado.limitar(ip):
                estado.registrar_seguranca("limite_de_requisicoes")
                return self._responder(429, {"erro": "muitas_tentativas"})
            if caminho in ("/", ""):
                return self._envelope()
            if ROTA_LEADS.match(caminho):
                return self._criar()
            m = ROTA_DETALHES.match(caminho)
            if m:
                return self._detalhes(m.group(1))
            self._responder(404, {"erro": "nao_encontrado"})

        def _envelope(self):
            """Protocolo do site (idêntico ao do Google Apps Script): POST / com {action, data} enviado como text/plain.
            Existe para testar localmente o mesmo cliente que falará com o Apps Script. Respostas: {ok, ...}."""
            try:
                tamanho = int(self.headers.get("Content-Length", ""))
                if tamanho <= 0 or tamanho > LIMITE_CORPO:
                    return self._responder(413, {"ok": False, "error": "too_large"})
                env = json.loads(self.rfile.read(tamanho).decode("utf-8"))
            except (ValueError, UnicodeDecodeError, socket.timeout):
                return self._responder(400, {"ok": False, "error": "bad_request"})
            if not isinstance(env, dict) or not isinstance(env.get("data"), dict):
                return self._responder(400, {"ok": False, "error": "bad_request"})
            dados = env["data"]
            if env.get("action") == "submit":
                if dados.get("website"):
                    estado.registrar_seguranca("armadilha_de_robo")
                    return self._responder(200, {"ok": True, "publicCode": "CRV-0000-000000", "detailsToken": ""})
                try:
                    lead = regras.validar_lead({k: v for k, v in dados.items() if k not in ("website", "turnstileToken")})
                except regras.ErroValidacao as e:
                    estado.registrar_seguranca("validacao_reprovada", ",".join(sorted(e.campos))[:80])
                    return self._responder(200, {"ok": False, "error": "validation", "fields": e.campos})
                try:
                    lead_id, criado = estado.criar_lead(lead)
                except sqlite3.Error:
                    estado.registrar_seguranca("falha_de_gravacao")
                    return self._responder(200, {"ok": False, "error": "unavailable"})
                return self._responder(200, {"ok": True, "id": lead_id, "publicCode": lead_id, "detailsToken": estado.token_do_lead(lead_id)})
            if env.get("action") == "details":
                lead_id = str(dados.get("leadRef", ""))
                if not hmac.compare_digest(str(dados.get("token", "")), estado.token_do_lead(lead_id)):
                    estado.registrar_seguranca("token_invalido")
                    return self._responder(200, {"ok": False, "error": "unauthorized"})
                try:
                    detalhes = regras.validar_detalhes({"additionalInfo": dados.get("additionalInfo")})
                except regras.ErroValidacao as e:
                    return self._responder(200, {"ok": False, "error": "validation", "fields": e.campos})
                if not estado.adicionar_detalhes(lead_id, detalhes):
                    return self._responder(200, {"ok": False, "error": "not_found"})
                return self._responder(200, {"ok": True})
            self._responder(400, {"ok": False, "error": "bad_request"})

        def _criar(self):
            corpo = self._ler_json()
            if corpo is None:
                return
            if isinstance(corpo, dict) and corpo.get("website"):       # armadilha de robô preenchida
                estado.registrar_seguranca("armadilha_de_robo")
                return self._responder(201, {"id": "0" * 20, "detailsToken": ""})   # resposta neutra; nada é gravado
            segredo = estado.cfg["turnstile_secret"]
            if segredo and not verificar_turnstile(segredo, corpo.get("turnstileToken") if isinstance(corpo, dict) else None, self.client_address[0]):
                estado.registrar_seguranca("antiabuso_reprovado")
                return self._responder(403, {"erro": "antiabuso"})
            if isinstance(corpo, dict):
                corpo = {k: v for k, v in corpo.items() if k not in ("website", "turnstileToken")}
            try:
                lead = regras.validar_lead(corpo)
            except regras.ErroValidacao as e:
                estado.registrar_seguranca("validacao_reprovada", ",".join(sorted(e.campos))[:80])
                return self._responder(422, {"erro": "validacao", "campos": e.campos})
            try:
                lead_id, criado = estado.criar_lead(lead)
            except sqlite3.Error:
                estado.registrar_seguranca("falha_de_gravacao")
                return self._responder(503, {"erro": "indisponivel"})
            self._responder(201 if criado else 200, {"id": lead_id, "detailsToken": estado.token_do_lead(lead_id), "duplicado": not criado})

        def _detalhes(self, lead_id):
            token = self.headers.get("X-Lead-Token", "")
            if not hmac.compare_digest(token, estado.token_do_lead(lead_id)):
                estado.registrar_seguranca("token_invalido")
                return self._responder(403, {"erro": "nao_autorizado"})
            corpo = self._ler_json()
            if corpo is None:
                return
            try:
                detalhes = regras.validar_detalhes(corpo)
            except regras.ErroValidacao as e:
                return self._responder(422, {"erro": "validacao", "campos": e.campos})
            if not estado.adicionar_detalhes(lead_id, detalhes):
                return self._responder(404, {"erro": "nao_encontrado"})
            self._responder(200, {"ok": True})

    return Handler


def criar_servidor(host="127.0.0.1", porta=None):
    estado = Estado()
    servidor = ThreadingHTTPServer((host, estado.cfg["porta"] if porta is None else porta), fabricar_handler(estado))
    servidor.daemon_threads = True
    servidor.estado = estado
    return servidor


# ── comandos de operação ────────────────────────────────────────────────────────────────────────
def cmd_listar():
    con = abrir_banco(config()["db"])
    try:
        for lead_id, criado, prioridade, total, status in con.execute(
                "SELECT id, created_at, priority, total_score, status FROM leads ORDER BY created_at DESC"):
            print(lead_id, criado, "prioridade", prioridade, "pontos", total, status)
    finally:
        con.close()


def cmd_suspender(valor):
    con = abrir_banco(config()["db"])
    con.execute("INSERT INTO meta(k,v) VALUES('descarte_suspenso',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", ("1" if valor == "on" else "0",))
    con.commit()
    con.close()
    print("descarte suspenso" if valor == "on" else "descarte liberado")


def cmd_expurgar():
    cfg = config()
    faltando = [n for n, v in (("LEAD_RETENTION_POLICY_ID", cfg["retencao_id"]), ("LEAD_RETENTION_DAYS", cfg["retencao_dias"]),
                               ("UNQUALIFIED_LEAD_RETENTION_DAYS", cfg["retencao_c_dias"]), ("SECURITY_LOG_RETENTION_DAYS", cfg["log_seg_dias"])) if not v]
    if faltando:
        print("Recusado: defina a política de retenção aprovada (%s). Nenhum valor é assumido." % ", ".join(faltando))
        return 2
    con = abrir_banco(cfg["db"])
    suspenso = con.execute("SELECT v FROM meta WHERE k='descarte_suspenso'").fetchone()
    if suspenso and suspenso[0] == "1":
        con.close()
        print("Descarte suspenso (guarda legal). Nada foi removido.")
        return 3
    agora_dt = datetime.now(timezone.utc)
    corte = (agora_dt - timedelta(days=int(cfg["retencao_dias"]))).strftime("%Y-%m-%dT%H:%M:%SZ")
    corte_c = (agora_dt - timedelta(days=int(cfg["retencao_c_dias"]))).strftime("%Y-%m-%dT%H:%M:%SZ")
    cur = con.execute("DELETE FROM leads WHERE created_at < ? OR (priority='C' AND created_at < ?)", (corte, corte_c))
    removidos = cur.rowcount
    corte_log = (agora_dt - timedelta(days=int(cfg["log_seg_dias"]))).strftime("%Y-%m-%dT%H:%M:%SZ")
    con.execute("DELETE FROM security_log WHERE ts < ?", (corte_log,))
    con.execute("INSERT INTO security_log(ts, evento, detalhe) VALUES(?,?,?)", (agora(), "descarte", "politica=%s;registros=%d" % (cfg["retencao_id"][:30], removidos)))
    con.commit()
    con.close()
    print("Descarte concluído: %d registro(s). Backups e cópias externas seguem a política aprovada (ver docs)." % removidos)
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "listar":
        return cmd_listar() or 0
    if len(argv) >= 3 and argv[1] == "suspender" and argv[2] in ("on", "off"):
        return cmd_suspender(argv[2]) or 0
    if len(argv) >= 2 and argv[1] == "expurgar":
        return cmd_expurgar()
    servidor = criar_servidor()
    cfg = servidor.estado.cfg
    print("Servidor de leads em http://127.0.0.1:%d (origens permitidas: %s)" % (cfg["porta"], ", ".join(cfg["origens"])))
    print("Aviso: o servidor de referência não faz TLS; publique atrás de HTTPS (ver docs/deployment-readiness.md).")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
