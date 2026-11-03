"""Regras do formulário "Apresentar meu cenário" (página única): esquema v2, validação estrita, normalização,
pontuação de prioridade e produtos candidatos.

Tudo aqui é determinístico e não tem efeitos colaterais, para poder ser testado sem rede nem banco.
A pontuação serve só para PRIORIDADE e ENCAMINHAMENTO: nunca rejeita um contato (ver docs/lead-form-data-dictionary.md).
A localização é conferida contra as tabelas do IBGE geradas no projeto (cenario/data/locations); nada é consultado na internet.
"""
import json
import os
import re
import unicodedata
from functools import lru_cache

SCHEMA_VERSION = 2
SCORE_RULE_VERSION = "score-v3"
MIN_ELAPSED_MS = 4000        # tempo mínimo plausível entre abrir a página e enviar

# ── listas permitidas (códigos internos estáveis; o rótulo exibido pode mudar sem quebrar os dados) ──────────────
SITUATIONS = {
    "obra_contrato_dificuldade": ("Obra ou contrato com dificuldade", "Em que momento está?",
                                  {"before_start": "Antes de iniciar", "running": "Em execução", "stopped": "Paralisado", "closing": "Encerramento", "unknown": "Ainda não sei"}),
    "atraso_custo_margem": ("Atraso, custo, produtividade ou perda de margem", "Qual efeito preocupa mais?",
                            {"deadline": "Prazo", "cost": "Custo", "margin": "Margem", "penalty": "Multa", "production": "Produção", "measurement": "Medição", "combination": "Combinação", "unknown": "Ainda não sei"}),
    "projeto_terreno_propostas": ("Projeto, terreno ou propostas para comparar", "O que precisa ser decidido?",
                                  {"feasibility": "Viabilidade", "project": "Projeto", "land": "Terreno", "contracting": "Contratação", "comparison": "Comparação", "unknown": "Ainda não sei"}),
    "planejamento_recursos_recuperacao": ("Planejamento, recursos ou recuperação", "Qual é a prioridade?",
                                          {"plan": "Planejar", "recover_deadline": "Recuperar prazo", "organize_resources": "Organizar recursos", "integrate_fronts": "Integrar frentes", "unknown": "Ainda não sei"}),
    "medicao_alteracao_documentacao": ("Medição, alteração contratual ou documentação", "Onde está o impasse?",
                                       {"measurement": "Medição", "scope": "Escopo", "change": "Alteração", "approval": "Aprovação", "databook": "Data book", "unknown": "Ainda não sei"}),
    "vistoria_recebimento_conferencia": ("Vistoria, recebimento ou conferência final", "O que será verificado?",
                                         {"property": "Imóvel", "service": "Serviço", "work": "Obra", "documentation": "Documentação", "handover": "Entrega", "unknown": "Ainda não sei"}),
    "comunicacao_ia_3d": ("Comunicação técnica com Inteligência Artificial, vídeo ou 3D", "Qual é o objetivo?",
                          {"explain": "Explicar", "present": "Apresentar", "sell": "Vender", "train": "Treinar", "compare": "Comparar", "unknown": "Ainda não sei"}),
    "outra_nao_sei": ("Outra situação / ainda não sei", "O que você busca agora?",
                      {"understand": "Entender", "compare": "Comparar", "plan": "Planejar", "verify": "Verificar", "decide": "Decidir", "unknown": "Ainda não sei"}),
}
AUDIENCE = {"company_manager": "Empresa / gestor", "contractor": "Empreiteira / prestador", "owner_investor": "Proprietário / investidor",
            "technical_team": "Profissional ou equipe técnica", "other": "Outro perfil"}
DECISION_ROLES = {"decides": "Decido ou aprovo a contratação", "recommends": "Participo da análise e recomendo", "gathering": "Estou levantando informações",
                  "referring": "Estou indicando a situação", "other_unsure": "Outro / ainda não sei"}
CHANNELS = ("whatsapp", "email")
URGENCIES = ("immediate", "this_week", "this_month", "undefined")
DOCS_AVAILABLE = ("yes", "partial", "no", "unknown")
CONTACT_PERIODS = ("morning", "afternoon", "evening", "any")
CONSEQUENCES = ("penalty", "stoppage", "margin_cash_loss", "technical_quality_risk", "contract_conflict", "decision_without_information", "other")
HIGH_CONSEQUENCES = ("penalty", "stoppage", "margin_cash_loss", "contract_conflict")
MAX_CONSEQUENCES = 2
RANGES = ("up_to_100k", "100k_to_1m", "1m_to_10m", "10m_to_50m", "above_50m", "undisclosed", "unknown")
ORIGINS = ("hero", "industria", "produtos", "metodo", "sobre", "header", "final", "direto")
PRODUCT_HINTS = ("P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10", "P11", "P12", "IA-1", "IA-2", "CV01")
DEVICES = ("mobile", "tablet", "desktop", "unknown")

LIMITS = {"narrative": 1200, "narrative_min": 10, "name": 120, "organization": 120, "city_foreign": 80, "region": 80, "utm": 80, "referrer": 120}

# Pontuação provisória (centralizada e configurável). Ver docs/lead-form-data-dictionary.md.
PONTUACAO = {
    "role": {"decides": 3, "recommends": 2, "gathering": 1, "referring": 0, "other_unsure": 0},
    "perfil": {"contractor": 2, "company_manager": 2, "owner_investor": 1, "technical_team": 1, "other": 0},
    "urgencia": {"immediate": 2, "this_week": 2, "this_month": 1, "undefined": 0},
    "documentos": {"yes": 2, "partial": 1, "no": 0, "unknown": 0},
    "faixas": {"A": 10, "B": 6},   # máximo 16; total >= 10 -> A; >= 6 -> B; senão C
}

# Hipótese de encaminhamento (sempre revisão humana; o visitante não escolhe produto)
PRODUTOS_POR_SITUACAO = {
    "obra_contrato_dificuldade": ["P01"], "atraso_custo_margem": ["P08", "P07"], "projeto_terreno_propostas": ["P02", "P03", "P05"],
    "planejamento_recursos_recuperacao": ["P06", "P07"], "medicao_alteracao_documentacao": ["P09", "P12"],
    "vistoria_recebimento_conferencia": ["P11"], "comunicacao_ia_3d": ["CV01"], "outra_nao_sei": [],
}


class ErroValidacao(Exception):
    def __init__(self, campos):
        super().__init__("validacao")
        self.campos = campos


# ── localidades (tabelas do IBGE geradas no projeto) ─────────────────────────────────────────────
def _pasta_localidades():
    return os.environ.get("CRIVIA_LOCATIONS_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cenario", "data", "locations")


def _ler(*partes):
    with open(os.path.join(_pasta_localidades(), *partes), encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def estados():
    """{sigla: (nome, codigo_ibge_da_uf)}"""
    return {s: (n, c) for s, n, c in _ler("states.json")}


@lru_cache(maxsize=32)
def municipios(uf):
    """{codigo_ibge_7_digitos: nome} da UF"""
    return {c: n for c, n in _ler("municipalities", uf + ".json")}


@lru_cache(maxsize=1)
def paises():
    """{iso2: nome_pt}"""
    return {i: n for i, n in _ler("countries.json")}


# ── utilitários de texto ─────────────────────────────────────────────────────────────────────
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_CNPJ = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
_EMAIL = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")
_NOME = re.compile(r"^[^\d<>{}\[\]\\|^~`@#$%*=+_]{2,}$")
_IDEM = re.compile(r"^[A-Za-z0-9-]{8,64}$")
_VERSAO = re.compile(r"^[A-Za-z0-9._-]{1,40}$")
_UTM = re.compile(r"^[A-Za-z0-9._~ +-]{0,80}$")
_HTML = re.compile(r"<\s*/?\s*[A-Za-z!][^>]*>")


def limpar_texto(valor, maximo):
    """NFC, sem caracteres de controle, espaços excedentes aparados (preserva quebras de linha); devolve (texto, suspeita_de_dado_pessoal)."""
    if not isinstance(valor, str):
        raise ValueError("tipo")
    texto = unicodedata.normalize("NFC", valor)
    texto = _CTRL.sub("", texto)
    texto = re.sub(r"[ \t]{2,}", " ", texto).strip()
    if len(texto) > maximo:
        raise ValueError("tamanho")
    suspeita = bool(_CPF.search(texto) or _CNPJ.search(texto))
    if suspeita:
        texto = _CNPJ.sub("[removido]", _CPF.sub("[removido]", texto))
    return texto, suspeita


def normalizar_telefone(valor):
    """Aceita número brasileiro (DDD + número, com ou sem +55) e internacional (+ e 8–15 dígitos). Devolve E.164 ou None."""
    bruto = re.sub(r"[\s().-]", "", valor)
    if not re.fullmatch(r"\+?\d{8,15}", bruto):
        return None
    if bruto.startswith("+"):
        return bruto
    if bruto.startswith("55") and len(bruto) in (12, 13):
        return "+" + bruto
    if len(bruto) in (10, 11):
        ddd, resto = bruto[:2], bruto[2:]
        if ddd[0] in "123456789" and ddd[1] != "0" and (len(resto) == 8 or (len(resto) == 9 and resto[0] == "9")):
            return "+55" + bruto
    return None


# ── validação ────────────────────────────────────────────────────────────────────────────────
class _V:
    def __init__(self):
        self.erros = {}
        self.suspeita = False

    def erro(self, caminho, codigo):
        self.erros.setdefault(caminho, codigo)

    def objeto(self, valor, caminho, permitidas, obrigatorias=()):
        if not isinstance(valor, dict):
            self.erro(caminho, "tipo")
            return {}
        for chave in valor:
            if chave not in permitidas:
                self.erro(f"{caminho}.{chave}", "campo_desconhecido")
        for chave in obrigatorias:
            if chave not in valor:
                self.erro(f"{caminho}.{chave}", "obrigatorio")
        return valor

    def enum(self, valor, caminho, permitidos, obrigatorio=True):
        if valor in (None, ""):
            if obrigatorio:
                self.erro(caminho, "obrigatorio")
            return None
        if not isinstance(valor, str) or valor not in permitidos:
            self.erro(caminho, "valor_invalido")
            return None
        return valor

    def lista(self, valor, caminho, permitidos, maximo):
        if valor in (None, []):
            return []
        if not isinstance(valor, list):
            self.erro(caminho, "tipo")
            return []
        if len(valor) > maximo:
            self.erro(caminho, "limite_de_selecoes")
            return []
        saida = []
        for item in valor:
            if not isinstance(item, str) or item not in permitidos:
                self.erro(caminho, "valor_invalido")
                return []
            if item not in saida:
                saida.append(item)
        return saida

    def texto(self, valor, caminho, maximo, obrigatorio=False, minimo=0):
        if valor in (None, ""):
            if obrigatorio:
                self.erro(caminho, "obrigatorio")
            return ""
        try:
            texto, suspeita = limpar_texto(valor, maximo)
        except ValueError as e:
            self.erro(caminho, str(e))
            return ""
        self.suspeita = self.suspeita or suspeita
        if _HTML.search(texto):
            self.erro(caminho, "html_nao_permitido")
            return ""
        if obrigatorio and len(texto) < max(1, minimo):
            self.erro(caminho, "muito_curto" if texto else "obrigatorio")
        elif minimo and texto and len(texto) < minimo:
            self.erro(caminho, "muito_curto")
        return texto


def envio_rapido_demais(corpo):
    """True se o tempo informado pelo navegador é implausível para uma pessoa (a checagem é um sinal, não uma prova)."""
    ms = corpo.get("elapsedMs") if isinstance(corpo, dict) else None
    return isinstance(ms, int) and not isinstance(ms, bool) and 0 <= ms < MIN_ELAPSED_MS


def _localizacao(v, bruto):
    caminho = "scenario.location"
    tipo = bruto.get("type") if isinstance(bruto, dict) else None
    if tipo == "brazil":
        b = v.objeto(bruto, caminho, {"type", "countryCode", "stateCode", "cityCode", "cityName"}, ("stateCode", "cityCode"))
        uf = v.enum(b.get("stateCode"), f"{caminho}.stateCode", tuple(estados()))
        codigo, nome = None, ""
        v.enum(b.get("countryCode"), f"{caminho}.countryCode", ("BR",), False)
        if uf:
            tabela = municipios(uf)
            codigo = b.get("cityCode")
            if not isinstance(codigo, str) or codigo not in tabela:
                v.erro(f"{caminho}.cityCode", "valor_invalido")      # inclui município de outra UF
                codigo = None
            else:
                nome = tabela[codigo]
                enviado = b.get("cityName")
                if enviado not in (None, "") and (not isinstance(enviado, str) or unicodedata.normalize("NFC", enviado).strip() != nome):
                    v.erro(f"{caminho}.cityName", "valor_invalido")
        return {"type": "brazil", "countryCode": "BR", "countryName": "Brasil", "stateCode": uf or "", "stateName": estados()[uf][0] if uf else "",
                "cityCode": codigo or "", "cityName": nome, "foreignRegion": ""}
    if tipo == "international":
        b = v.objeto(bruto, caminho, {"type", "countryCode", "cityName", "foreignRegion"}, ("countryCode", "cityName"))
        pais = v.enum(b.get("countryCode"), f"{caminho}.countryCode", tuple(paises()))
        if pais == "BR":
            v.erro(f"{caminho}.countryCode", "use_modo_brasil")
        return {"type": "international", "countryCode": pais or "", "countryName": paises().get(pais, "") if pais else "", "stateCode": "", "stateName": "",
                "cityCode": "", "cityName": v.texto(b.get("cityName"), f"{caminho}.cityName", LIMITS["city_foreign"], True, 1),
                "foreignRegion": v.texto(b.get("foreignRegion"), f"{caminho}.foreignRegion", LIMITS["region"])}
    v.erro(f"{caminho}.type", "valor_invalido" if tipo else "obrigatorio")
    return {"type": "", "countryCode": "", "countryName": "", "stateCode": "", "stateName": "", "cityCode": "", "cityName": "", "foreignRegion": ""}


def validar_lead(corpo):
    """Valida e normaliza a submissão completa. Levanta ErroValidacao. Devolve o registro normalizado (sem id/datas)."""
    v = _V()
    topo = v.objeto(corpo, "$", {"idempotencyKey", "schemaVersion", "formVersion", "elapsedMs", "source", "scenario", "contact", "privacy", "website", "turnstileToken"},
                    ("idempotencyKey", "scenario", "contact", "privacy"))
    chave = topo.get("idempotencyKey")
    if not isinstance(chave, str) or not _IDEM.match(chave):
        v.erro("idempotencyKey", "valor_invalido")
    if topo.get("schemaVersion", SCHEMA_VERSION) != SCHEMA_VERSION:
        v.erro("schemaVersion", "valor_invalido")
    versao_form = topo.get("formVersion")
    if versao_form not in (None, "") and not (isinstance(versao_form, str) and _VERSAO.match(versao_form)):
        v.erro("formVersion", "valor_invalido")
    ms = topo.get("elapsedMs")
    if isinstance(ms, bool) or not isinstance(ms, int) or ms < 0 or ms > 7 * 24 * 3600 * 1000:
        v.erro("elapsedMs", "valor_invalido" if ms is not None else "obrigatorio")

    # origem (somente listas permitidas; nada é reproduzido sem validação)
    o = v.objeto(topo.get("source") or {}, "source", {"landingPage", "referrer", "originCta", "productHint", "utmSource", "utmMedium", "utmCampaign",
                                                      "utmContent", "utmTerm", "deviceCategory"})
    source = {
        "landingPage": "/apresentar-cenario", "referrer": "",
        "originCta": v.enum(o.get("originCta"), "source.originCta", ORIGINS, False) or "direto",
        "productHint": v.enum(o.get("productHint"), "source.productHint", PRODUCT_HINTS, False),
        "deviceCategory": v.enum(o.get("deviceCategory"), "source.deviceCategory", DEVICES, False) or "unknown",
    }
    ref = o.get("referrer")
    if ref:
        if isinstance(ref, str) and re.fullmatch(r"[A-Za-z0-9.-]{1,120}", ref):
            source["referrer"] = ref.lower()
        else:
            v.erro("source.referrer", "valor_invalido")
    for utm in ("utmSource", "utmMedium", "utmCampaign", "utmContent", "utmTerm"):
        valor = o.get(utm)
        if valor in (None, ""):
            source[utm] = ""
        elif isinstance(valor, str) and _UTM.match(valor):
            source[utm] = valor
        else:
            v.erro(f"source.{utm}", "valor_invalido")

    # cenário
    s = v.objeto(topo.get("scenario"), "scenario", {"situationCode", "contextAnswerCode", "audienceProfile", "decisionRole", "location", "narrative",
                                                "urgency", "consequences", "documents", "estimatedRange"},
                 ("situationCode", "audienceProfile", "decisionRole", "location", "narrative"))
    situacao = v.enum(s.get("situationCode"), "scenario.situationCode", tuple(SITUATIONS))
    rotulo_sit, pergunta, respostas = SITUATIONS[situacao] if situacao else ("", "", {})
    resposta = v.enum(s.get("contextAnswerCode"), "scenario.contextAnswerCode", tuple(respostas), False)
    perfil = v.enum(s.get("audienceProfile"), "scenario.audienceProfile", tuple(AUDIENCE))
    papel = v.enum(s.get("decisionRole"), "scenario.decisionRole", tuple(DECISION_ROLES))
    cenario = {
        "situationCode": situacao, "situationLabel": rotulo_sit,
        "contextQuestion": pergunta if resposta else "", "contextAnswerCode": resposta or "", "contextAnswerLabel": respostas.get(resposta, "") if resposta else "",
        "audienceProfile": perfil, "audienceProfileLabel": AUDIENCE.get(perfil, ""),
        "decisionRole": papel, "decisionRoleLabel": DECISION_ROLES.get(papel, ""),
        "location": _localizacao(v, s.get("location")),
        "urgency": v.enum(s.get("urgency"), "scenario.urgency", URGENCIES, False) or "",
        "consequences": v.lista(s.get("consequences"), "scenario.consequences", CONSEQUENCES, MAX_CONSEQUENCES),
        "documents": v.enum(s.get("documents"), "scenario.documents", DOCS_AVAILABLE, False) or "",
        "estimatedRange": v.enum(s.get("estimatedRange"), "scenario.estimatedRange", RANGES, False) or "",
        "narrative": v.texto(s.get("narrative"), "scenario.narrative", LIMITS["narrative"], True, LIMITS["narrative_min"]),
    }

    # contato
    c = v.objeto(topo.get("contact"), "contact", {"name", "organization", "preferredChannel", "phone", "email", "contactPeriod"}, ("name", "preferredChannel"))
    canal = v.enum(c.get("preferredChannel"), "contact.preferredChannel", CHANNELS)
    nome = v.texto(c.get("name"), "contact.name", LIMITS["name"], True, 2)
    if nome and not _NOME.match(nome):
        v.erro("contact.name", "valor_invalido")
    telefone = email = None
    if c.get("phone") not in (None, ""):
        telefone = normalizar_telefone(c["phone"]) if isinstance(c["phone"], str) else None
        if not telefone:
            v.erro("contact.phone", "valor_invalido")
    if c.get("email") not in (None, ""):
        valor = c["email"].strip() if isinstance(c["email"], str) else ""
        if len(valor) <= 254 and _EMAIL.match(valor):
            email = valor.lower()
        else:
            v.erro("contact.email", "valor_invalido")
    if canal == "whatsapp" and not telefone and "contact.phone" not in v.erros:
        v.erro("contact.phone", "obrigatorio")
    if canal == "email" and not email and "contact.email" not in v.erros:
        v.erro("contact.email", "obrigatorio")
    contato = {"name": nome, "organization": v.texto(c.get("organization"), "contact.organization", LIMITS["organization"]),
               "preferredChannel": canal, "phone": telefone or "", "email": email or "",
               "contactPeriod": v.enum(c.get("contactPeriod"), "contact.contactPeriod", CONTACT_PERIODS, False) or ""}

    # privacidade: ciência do aviso registrada; marketing só se marcado e sempre opcional
    p = v.objeto(topo.get("privacy"), "privacy", {"privacyNoticeVersion", "acknowledged", "marketingConsent"}, ("privacyNoticeVersion", "acknowledged"))
    versao = p.get("privacyNoticeVersion")
    if not isinstance(versao, str) or not _VERSAO.match(versao):
        v.erro("privacy.privacyNoticeVersion", "valor_invalido")
    if p.get("acknowledged") is not True:
        v.erro("privacy.acknowledged", "obrigatorio")
    marketing = p.get("marketingConsent", False)
    if not isinstance(marketing, bool):
        v.erro("privacy.marketingConsent", "valor_invalido")
        marketing = False

    if v.erros:
        raise ErroValidacao(v.erros)
    return {
        "idempotencyKey": chave, "schemaVersion": SCHEMA_VERSION, "formVersion": versao_form or "", "source": source, "scenario": cenario, "contact": contato,
        "privacy": {"privacyNoticeVersion": versao, "requestedContactChannel": canal, "marketingConsent": marketing},
        "sensitiveContentSuspected": v.suspeita,
    }


def validar_detalhes(corpo):
    """Complemento opcional pós-envio: três perguntas curtas, todas de lista fechada."""
    v = _V()
    c = v.objeto(corpo, "$", {"urgency", "documents", "contactPeriod"})
    saida = {"urgency": v.enum(c.get("urgency"), "urgency", URGENCIES, False), "documents": v.enum(c.get("documents"), "documents", DOCS_AVAILABLE, False),
             "contactPeriod": v.enum(c.get("contactPeriod"), "contactPeriod", CONTACT_PERIODS, False)}
    if not any(saida.values()) and not v.erros:
        v.erro("$", "vazio")
    if v.erros:
        raise ErroValidacao(v.erros)
    return {k: x for k, x in saida.items() if x}


# ── pontuação e enquadramento ───────────────────────────────────────────────────────────────────
def pontuar(lead):
    s = lead["scenario"]
    relevancia = 3 if s["situationCode"] != "outra_nao_sei" else (2 if len(s["narrative"]) >= 200 else 1)
    papel = PONTUACAO["role"].get(s["decisionRole"], 0)
    perfil = PONTUACAO["perfil"].get(s["audienceProfile"], 0)
    detalhe = 2 if len(s["narrative"]) >= 200 else 1 if len(s["narrative"]) >= 80 else 0
    tempo = PONTUACAO["urgencia"].get(s["urgency"], 0)
    cons = s["consequences"]
    consequencia = min(2, (1 if cons else 0) + (1 if any(c in HIGH_CONSEQUENCES for c in cons) else 0))
    prontidao = PONTUACAO["documentos"].get(s["documents"], 0)
    parcial = {"relevanceScore": relevancia, "decisionRoleScore": papel, "audienceScore": perfil, "detailScore": detalhe,
               "timingScore": tempo, "consequenceScore": consequencia, "readinessScore": prontidao}
    total = sum(parcial.values())
    faixas = PONTUACAO["faixas"]
    prioridade = "A" if total >= faixas["A"] else "B" if total >= faixas["B"] else "C"
    return {**parcial, "totalScore": total, "priority": prioridade, "ruleVersion": SCORE_RULE_VERSION}


def produtos_candidatos(lead):
    return list(PRODUTOS_POR_SITUACAO.get(lead["scenario"]["situationCode"], []))   # vazio = revisão humana define o enquadramento


def informacoes_ausentes(lead):
    s = lead["scenario"]
    falta = []
    if not s["contextAnswerCode"] or s["contextAnswerCode"] == "unknown":
        falta.append("context_answer")
    if len(s["narrative"]) < 80:
        falta.append("narrative_detail")
    if s["decisionRole"] in ("gathering", "referring", "other_unsure"):
        falta.append("decision_owner")
    if not s["urgency"] or s["urgency"] == "undefined":
        falta.append("decision_horizon")
    if s["documents"] in ("", "no", "unknown"):
        falta.append("documents")
    if s["estimatedRange"] in ("", "undisclosed", "unknown"):
        falta.append("estimated_range")
    return falta


def enquadrar(lead):
    """Qualificação interna completa: pontuação + produtos candidatos + lacunas. Nada aqui rejeita o contato."""
    q = pontuar(lead)
    q["candidateProducts"] = produtos_candidatos(lead)
    q["missingInformation"] = informacoes_ausentes(lead)
    return q
