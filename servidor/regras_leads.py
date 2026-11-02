"""Regras do formulário "Apresentar meu cenário": esquema, validação estrita, normalização,
pontuação de prioridade e produtos candidatos.

Tudo aqui é determinístico e não tem efeitos colaterais, para poder ser testado sem rede nem banco.
A pontuação serve só para PRIORIDADE e ENCAMINHAMENTO: nunca rejeita um contato (ver docs/lead-form-data-dictionary.md).
"""
import re
import unicodedata

SCHEMA_VERSION = 1
SCORE_RULE_VERSION = "score-v1"

# ── listas permitidas (valores internos estáveis, em inglês) ───────────────────────────────
ENTRY_PATHS = ("underperforming", "decision_support", "visual_communication", "ai_decision_engineering", "other_or_unsure")
AUDIENCE = ("contractor", "large_company", "owner_investor", "technical_partner", "other")
BUSINESS_AUDIENCE = ("contractor", "large_company", "technical_partner")   # organização obrigatória
DECISION_ROLES = ("decides", "leads_evaluation", "technical_participant", "early_research", "other")
STAGES = ("planning", "execution", "delay_or_critical", "near_completion", "operation", "unsure")
ISSUES = ("schedule", "margin_cost", "measurement_receipt", "scope_change", "team_equipment_material",
          "project_info", "quality", "supplier", "undefined_responsibilities", "other")
CONSEQUENCES = ("penalty", "stoppage", "margin_cash_loss", "technical_quality_risk", "contract_conflict",
                "operation_impact", "decision_without_information", "other")
HIGH_CONSEQUENCES = ("penalty", "stoppage", "margin_cash_loss", "contract_conflict")
HORIZONS = ("up_to_7_days", "8_to_30_days", "31_to_90_days", "after_90_days", "undefined")
EVALUATE = ("land", "projects", "budget_costs", "supplier_proposals", "planning_resources",
            "measurement_change", "handover", "documentation_databook", "other")
DELIVERABLES = ("explainer_video", "image_or_3d", "technical_presentation", "visual_proposal", "combination", "undefined")
PURPOSES = ("explain_solution", "present_project", "compare_alternatives", "present_proposal", "show_process", "other")
VISUAL_AUDIENCE = ("client", "board", "technical_team", "investor", "general_public", "other")
REFERENCE_LEVELS = ("idea_only", "photos_info", "plans_projects", "existing_3d_model", "not_organized")
AI_SITUATIONS = ("expand_transition", "already_using", "evaluating")
AI_DIFFICULTIES = ("unreliable_output", "rework", "overload", "inadequate_decisions", "lack_of_checking",
                   "areas_misaligned", "people_unprepared", "tools_disconnected", "unclear_responsibilities", "other")
AI_AREAS = ("operations", "engineering", "procurement", "finance", "legal_contracts", "it", "board", "other")
PEOPLE_RANGES = ("up_to_10", "11_to_50", "51_to_200", "above_200", "undisclosed")
PROCESSES = ("planning", "execution", "procurement", "measurement", "documentation", "customer_service", "other")
RANGES = ("up_to_100k", "100k_to_1m", "1m_to_10m", "10m_to_50m", "above_50m", "undisclosed", "unknown")
DOCUMENTS = ("contract", "projects", "schedule", "budget", "measurements", "photos_records", "process_data", "none_organized", "other")
CHANNELS = ("whatsapp", "email", "phone_call")
PERIODS = ("morning", "afternoon", "evening", "business_hours_any")
UFS = ("AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
       "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO")
ORIGINS = ("hero", "industria", "produtos", "metodo", "sobre", "header", "final", "direto")
PRODUCT_HINTS = ("P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10", "P11", "P12", "IA-1", "IA-2", "CV01")
DEVICES = ("mobile", "tablet", "desktop", "unknown")

LIMITS = {"narrative": 700, "short_text": 500, "name": 120, "organization": 120, "role_title": 80, "city": 80,
          "additional_info": 700, "utm": 80, "referrer": 120}

# Pontuação provisória (centralizada e configurável). Ver docs/lead-form-data-dictionary.md.
PONTUACAO = {
    "pesos_max": {"relevance": 3, "decisionRole": 3, "consequence": 3, "timing": 2, "readiness": 2},
    "role": {"decides": 3, "leads_evaluation": 2, "technical_participant": 1, "early_research": 0, "other": 0},
    "horizonte": {"up_to_7_days": 2, "8_to_30_days": 2, "31_to_90_days": 1, "after_90_days": 0, "undefined": 0},
    "faixas": {"A": 10, "B": 6},   # total >= 10 -> A; >= 6 -> B; senão C
}

# Produtos candidatos (hipótese de encaminhamento; sempre revisão humana)
PRODUTOS_POR_PROBLEMA = {
    "schedule": "P06", "margin_cost": "P07", "measurement_receipt": "P09", "scope_change": "P09",
    "team_equipment_material": "P08", "project_info": "P02", "quality": "P10", "supplier": "P05",
    "undefined_responsibilities": "P01",
}
PRODUTOS_POR_AVALIACAO = {
    "land": "P03", "projects": "P02", "budget_costs": "P04", "supplier_proposals": "P05", "planning_resources": "P06",
    "measurement_change": "P09", "handover": "P11", "documentation_databook": "P12",
}
PRODUTO_POR_ETAPA = {"delay_or_critical": "P07", "execution": "P10", "near_completion": "P11", "planning": "P06"}


class ErroValidacao(Exception):
    def __init__(self, campos):
        super().__init__("validacao")
        self.campos = campos


# ── utilitários de texto ─────────────────────────────────────────────────────────────────────
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_CNPJ = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
_EMAIL = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")
_NOME = re.compile(r"^[^\d<>{}\[\]\\|^~`@#$%*=+_]{2,}$")
_IDEM = re.compile(r"^[A-Za-z0-9-]{8,64}$")
_VERSAO = re.compile(r"^[A-Za-z0-9._-]{1,40}$")
_UTM = re.compile(r"^[A-Za-z0-9._~ +-]{0,80}$")


def limpar_texto(valor, maximo):
    """NFC, sem caracteres de controle, espaços aparados; devolve (texto, suspeita_de_dado_pessoal)."""
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

    def lista(self, valor, caminho, permitidos, maximo, obrigatorio=False):
        if valor in (None, []):
            if obrigatorio:
                self.erro(caminho, "obrigatorio")
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
        if obrigatorio and len(texto) < max(1, minimo):
            self.erro(caminho, "muito_curto" if texto else "obrigatorio")
        elif minimo and texto and len(texto) < minimo:
            self.erro(caminho, "muito_curto")
        return texto


def validar_lead(corpo):
    """Valida e normaliza a submissão completa. Levanta ErroValidacao. Devolve o registro normalizado (sem id/datas)."""
    v = _V()
    topo = v.objeto(corpo, "$", {"idempotencyKey", "schemaVersion", "source", "scenario", "contact", "privacy", "website", "turnstileToken"},
                    ("idempotencyKey", "scenario", "contact", "privacy"))
    chave = topo.get("idempotencyKey")
    if not isinstance(chave, str) or not _IDEM.match(chave):
        v.erro("idempotencyKey", "valor_invalido")
    if topo.get("schemaVersion", SCHEMA_VERSION) != SCHEMA_VERSION:
        v.erro("schemaVersion", "valor_invalido")

    # origem (somente listas permitidas; nada é reproduzido sem validação)
    origem_in = topo.get("source") or {}
    o = v.objeto(origem_in, "source", {"landingPage", "referrer", "originCta", "productHint", "utmSource", "utmMedium", "utmCampaign",
                                       "utmContent", "utmTerm", "deviceCategory"})
    source = {
        "landingPage": "/apresentar-cenario",
        "referrer": "",
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
    sc_in = topo.get("scenario")
    comuns = {"entryPath", "audienceContext", "decisionRole", "stage", "issues", "consequences", "decisionHorizon", "city", "state",
              "estimatedRange", "availableDocuments", "narrative", "branchSpecificData"}
    s = v.objeto(sc_in, "scenario", comuns, ("entryPath", "audienceContext", "decisionRole", "narrative", "city", "state"))
    entrada = v.enum(s.get("entryPath"), "scenario.entryPath", ENTRY_PATHS)
    cenario = {
        "entryPath": entrada,
        "audienceContext": v.enum(s.get("audienceContext"), "scenario.audienceContext", AUDIENCE),
        "decisionRole": v.enum(s.get("decisionRole"), "scenario.decisionRole", DECISION_ROLES),
        "stage": v.enum(s.get("stage"), "scenario.stage", STAGES, entrada in ("underperforming", "decision_support")),
        "issues": v.lista(s.get("issues"), "scenario.issues", ISSUES, 3, entrada == "underperforming") if entrada == "underperforming" else [],
        "consequences": v.lista(s.get("consequences"), "scenario.consequences", CONSEQUENCES, 2,
                                entrada in ("underperforming", "decision_support", "ai_decision_engineering", "other_or_unsure")),
        "decisionHorizon": v.enum(s.get("decisionHorizon"), "scenario.decisionHorizon", HORIZONS),
        "city": v.texto(s.get("city"), "scenario.city", LIMITS["city"], True, 2),
        "state": v.enum(s.get("state"), "scenario.state", UFS),
        "estimatedRange": v.enum(s.get("estimatedRange"), "scenario.estimatedRange", RANGES, False),
        "availableDocuments": v.lista(s.get("availableDocuments"), "scenario.availableDocuments", DOCUMENTS, len(DOCUMENTS), True),
        "narrative": v.texto(s.get("narrative"), "scenario.narrative", LIMITS["narrative"], True, 10),
        "branchSpecificData": {},
    }
    if cenario["city"] and not re.fullmatch(r"[^\d<>{}\[\]\\|^~`@#$%*=+_]{2,80}", cenario["city"]):
        v.erro("scenario.city", "valor_invalido")
    cenario["branchSpecificData"] = _ramo(v, entrada, s.get("branchSpecificData"))

    # contato
    ct_in = topo.get("contact")
    c = v.objeto(ct_in, "contact", {"name", "organization", "roleTitle", "preferredChannel", "phone", "email", "secondChannel",
                                    "secondValue", "preferredContactPeriod"}, ("name", "preferredChannel"))
    canal = v.enum(c.get("preferredChannel"), "contact.preferredChannel", CHANNELS)
    nome = v.texto(c.get("name"), "contact.name", LIMITS["name"], True, 2)
    if nome and not _NOME.match(nome):
        v.erro("contact.name", "valor_invalido")
    organizacao = v.texto(c.get("organization"), "contact.organization", LIMITS["organization"],
                          cenario["audienceContext"] in BUSINESS_AUDIENCE)
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
    if canal in ("whatsapp", "phone_call") and not telefone and "contact.phone" not in v.erros:
        v.erro("contact.phone", "obrigatorio")
    if canal == "email" and not email and "contact.email" not in v.erros:
        v.erro("contact.email", "obrigatorio")
    segundo = v.enum(c.get("secondChannel"), "contact.secondChannel", CHANNELS, False)
    segundo_valor = ""
    if segundo:
        bruto = c.get("secondValue")
        if segundo == "email":
            ok = isinstance(bruto, str) and len(bruto.strip()) <= 254 and _EMAIL.match(bruto.strip())
            segundo_valor = bruto.strip().lower() if ok else ""
        else:
            segundo_valor = normalizar_telefone(bruto) if isinstance(bruto, str) else None
        if not segundo_valor:
            v.erro("contact.secondValue", "valor_invalido")
    contato = {
        "name": nome, "organization": organizacao,
        "roleTitle": v.texto(c.get("roleTitle"), "contact.roleTitle", LIMITS["role_title"]),
        "preferredChannel": canal, "phone": telefone or "", "email": email or "",
        "secondChannel": segundo, "secondValue": segundo_valor or "",
        "preferredContactPeriod": v.enum(c.get("preferredContactPeriod"), "contact.preferredContactPeriod", PERIODS, False),
    }

    # privacidade: ciência registrada; marketing nunca "verdadeiro" por padrão (e nesta versão não é oferecido)
    p = v.objeto(topo.get("privacy"), "privacy", {"privacyNoticeVersion", "acknowledged", "marketingConsent"}, ("privacyNoticeVersion", "acknowledged"))
    versao = p.get("privacyNoticeVersion")
    if not isinstance(versao, str) or not _VERSAO.match(versao):
        v.erro("privacy.privacyNoticeVersion", "valor_invalido")
    if p.get("acknowledged") is not True:
        v.erro("privacy.acknowledged", "obrigatorio")
    if p.get("marketingConsent") not in (None, False):
        v.erro("privacy.marketingConsent", "nao_oferecido")

    if v.erros:
        raise ErroValidacao(v.erros)
    return {
        "idempotencyKey": chave, "schemaVersion": SCHEMA_VERSION, "source": source, "scenario": cenario, "contact": contato,
        "privacy": {"privacyNoticeVersion": versao, "requestedContactChannel": canal, "marketingConsent": False},
        "sensitiveContentSuspected": v.suspeita,
    }


def _ramo(v, entrada, bruto):
    """Campos específicos de cada rota (A–E); qualquer chave fora da lista da rota é rejeitada."""
    caminho = "scenario.branchSpecificData"
    if entrada == "decision_support":
        b = v.objeto(bruto or {}, caminho, {"evaluate"}, ("evaluate",))
        return {"evaluate": v.lista(b.get("evaluate"), f"{caminho}.evaluate", EVALUATE, 3, True)}
    if entrada == "visual_communication":
        b = v.objeto(bruto or {}, caminho, {"deliverable", "purpose", "audience", "referenceLevel"},
                     ("deliverable", "purpose", "audience", "referenceLevel"))
        return {"deliverable": v.enum(b.get("deliverable"), f"{caminho}.deliverable", DELIVERABLES),
                "purpose": v.enum(b.get("purpose"), f"{caminho}.purpose", PURPOSES),
                "audience": v.enum(b.get("audience"), f"{caminho}.audience", VISUAL_AUDIENCE),
                "referenceLevel": v.enum(b.get("referenceLevel"), f"{caminho}.referenceLevel", REFERENCE_LEVELS)}
    if entrada == "ai_decision_engineering":
        b = v.objeto(bruto or {}, caminho, {"aiSituation", "difficulties", "areas", "peopleRange", "affectedProcess"},
                     ("aiSituation", "peopleRange", "affectedProcess"))
        situacao = v.enum(b.get("aiSituation"), f"{caminho}.aiSituation", AI_SITUATIONS)
        dificuldades = v.lista(b.get("difficulties"), f"{caminho}.difficulties", AI_DIFFICULTIES, len(AI_DIFFICULTIES),
                               situacao == "already_using") if situacao == "already_using" else []
        return {"aiSituation": situacao, "difficulties": dificuldades,
                "areas": v.lista(b.get("areas"), f"{caminho}.areas", AI_AREAS, len(AI_AREAS), True),
                "peopleRange": v.enum(b.get("peopleRange"), f"{caminho}.peopleRange", PEOPLE_RANGES),
                "affectedProcess": v.enum(b.get("affectedProcess"), f"{caminho}.affectedProcess", PROCESSES)}
    if entrada == "other_or_unsure":
        b = v.objeto(bruto or {}, caminho, {"decisionNeeded"}, ("decisionNeeded",))
        return {"decisionNeeded": v.texto(b.get("decisionNeeded"), f"{caminho}.decisionNeeded", LIMITS["short_text"], True, 10)}
    if entrada == "underperforming":
        v.objeto(bruto or {}, caminho, set())
        return {}
    return {}


# ── pontuação e enquadramento ───────────────────────────────────────────────────────────────────
def pontuar(lead):
    s = lead["scenario"]
    caminho = s["entryPath"]
    relevancia = 3 if caminho != "other_or_unsure" else (2 if len(s["narrative"]) >= 80 else 1)
    papel = PONTUACAO["role"].get(s["decisionRole"], 0)
    cons = s["consequences"]
    consequencia = 0
    if cons:
        consequencia = min(3, 1 + (1 if any(c in HIGH_CONSEQUENCES for c in cons) else 0) + (1 if len(cons) >= 2 else 0))
    tempo = PONTUACAO["horizonte"].get(s["decisionHorizon"], 0)
    docs = [d for d in s["availableDocuments"] if d != "none_organized"]
    prontidao = 2 if len(docs) >= 3 else 1 if docs else 0
    parcial = {"relevanceScore": relevancia, "decisionRoleScore": papel, "consequenceScore": consequencia,
               "timingScore": tempo, "readinessScore": prontidao}
    total = sum(parcial.values())
    faixas = PONTUACAO["faixas"]
    prioridade = "A" if total >= faixas["A"] else "B" if total >= faixas["B"] else "C"
    return {**parcial, "totalScore": total, "priority": prioridade, "ruleVersion": SCORE_RULE_VERSION}


def produtos_candidatos(lead):
    s = lead["scenario"]
    caminho = s["entryPath"]
    saida = []

    def somar(codigo):
        if codigo and codigo not in saida:
            saida.append(codigo)

    if caminho == "underperforming":
        for problema in s["issues"]:
            somar(PRODUTOS_POR_PROBLEMA.get(problema))
        somar(PRODUTO_POR_ETAPA.get(s["stage"]))
        if not saida or "undefined_responsibilities" in s["issues"] or s["stage"] == "unsure":
            somar("P01")
    elif caminho == "decision_support":
        for item in s["branchSpecificData"].get("evaluate", []):
            somar(PRODUTOS_POR_AVALIACAO.get(item))
    elif caminho == "visual_communication":
        somar("CV01")
    elif caminho == "ai_decision_engineering":
        somar("IA")
    return saida   # rota E: vazio = revisão humana define o enquadramento


def informacoes_ausentes(lead):
    s = lead["scenario"]
    falta = []
    if s["decisionHorizon"] in (None, "undefined"):
        falta.append("decision_horizon")
    if not s["availableDocuments"] or s["availableDocuments"] == ["none_organized"]:
        falta.append("organized_documents")
    if s["estimatedRange"] in (None, "undisclosed", "unknown"):
        falta.append("estimated_range")
    if len(s["narrative"]) < 80:
        falta.append("narrative_detail")
    if s["decisionRole"] == "early_research":
        falta.append("decision_owner")
    return falta


def enquadrar(lead):
    """Qualificação interna completa: pontuação + produtos candidatos + lacunas. Nada aqui rejeita o contato."""
    q = pontuar(lead)
    q["candidateProducts"] = produtos_candidatos(lead)
    q["missingInformation"] = informacoes_ausentes(lead)
    return q


def validar_detalhes(corpo):
    v = _V()
    c = v.objeto(corpo, "$", {"additionalInfo"}, ("additionalInfo",))
    texto = v.texto(c.get("additionalInfo"), "additionalInfo", LIMITS["additional_info"], True, 5)
    if v.erros:
        raise ErroValidacao(v.erros)
    return {"additionalInfo": texto, "sensitiveContentSuspected": v.suspeita}
