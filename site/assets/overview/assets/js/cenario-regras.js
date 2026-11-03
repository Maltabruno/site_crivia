/* Regras do formulário "Apresentar meu cenário" (uma única página): listas, perguntas condicionais, validação e payload.
   Dados puros (sem DOM): testáveis em tests/regras.test.html. O servidor revalida tudo (servidor/regras_leads.py e
   google-apps-script/Validation.gs); os códigos internos abaixo são estáveis e NÃO devem ser traduzidos. */
(function (global) {
  "use strict";

  var o = function (v, l) { return { v: v, l: l }; };
  var NAO_SEI = o("unknown", "Ainda não sei");

  // Situação principal + pergunta curta que depende dela (toda com "Ainda não sei"; nenhuma é obrigatória)
  var SITUACOES = [
    { v: "obra_contrato_dificuldade", l: "Obra ou contrato com dificuldade", q: "Em que momento está?",
      opcoes: [o("before_start", "Antes de iniciar"), o("running", "Em execução"), o("stopped", "Paralisado"), o("closing", "Encerramento"), NAO_SEI] },
    { v: "atraso_custo_margem", l: "Atraso, custo, produtividade ou perda de margem", q: "Qual efeito preocupa mais?",
      opcoes: [o("deadline", "Prazo"), o("cost", "Custo"), o("margin", "Margem"), o("penalty", "Multa"), o("production", "Produção"), o("measurement", "Medição"), o("combination", "Combinação"), NAO_SEI] },
    { v: "projeto_terreno_propostas", l: "Projeto, terreno ou propostas para comparar", q: "O que precisa ser decidido?",
      opcoes: [o("feasibility", "Viabilidade"), o("project", "Projeto"), o("land", "Terreno"), o("contracting", "Contratação"), o("comparison", "Comparação"), NAO_SEI] },
    { v: "planejamento_recursos_recuperacao", l: "Planejamento, recursos ou recuperação", q: "Qual é a prioridade?",
      opcoes: [o("plan", "Planejar"), o("recover_deadline", "Recuperar prazo"), o("organize_resources", "Organizar recursos"), o("integrate_fronts", "Integrar frentes"), NAO_SEI] },
    { v: "medicao_alteracao_documentacao", l: "Medição, alteração contratual ou documentação", q: "Onde está o impasse?",
      opcoes: [o("measurement", "Medição"), o("scope", "Escopo"), o("change", "Alteração"), o("approval", "Aprovação"), o("databook", "Data book"), NAO_SEI] },
    { v: "vistoria_recebimento_conferencia", l: "Vistoria, recebimento ou conferência final", q: "O que será verificado?",
      opcoes: [o("property", "Imóvel"), o("service", "Serviço"), o("work", "Obra"), o("documentation", "Documentação"), o("handover", "Entrega"), NAO_SEI] },
    { v: "comunicacao_ia_3d", l: "Comunicação técnica com Inteligência Artificial, vídeo ou 3D", q: "Qual é o objetivo?",
      opcoes: [o("explain", "Explicar"), o("present", "Apresentar"), o("sell", "Vender"), o("train", "Treinar"), o("compare", "Comparar"), NAO_SEI] },
    { v: "outra_nao_sei", l: "Outra situação / ainda não sei", q: "O que você busca agora?",
      opcoes: [o("understand", "Entender"), o("compare", "Comparar"), o("plan", "Planejar"), o("verify", "Verificar"), o("decide", "Decidir"), NAO_SEI] }
  ];

  var PERFIS = [o("company_manager", "Empresa / gestor"), o("contractor", "Empreiteira / prestador"), o("owner_investor", "Proprietário / investidor"),
    o("technical_team", "Profissional ou equipe técnica"), o("other", "Outro perfil")];
  var PAPEIS = [o("decides", "Decido ou aprovo a contratação"), o("recommends", "Participo da análise e recomendo"), o("gathering", "Estou levantando informações"),
    o("referring", "Estou indicando a situação"), o("other_unsure", "Outro / ainda não sei")];
  var CANAIS = [o("whatsapp", "WhatsApp"), o("email", "E-mail")];
  // Complemento opcional, depois do envio confirmado
  var URGENCIAS = [o("immediate", "Imediata"), o("this_week", "Nesta semana"), o("this_month", "Neste mês"), o("undefined", "Sem urgência definida")];
  var DOCUMENTOS = [o("yes", "Sim"), o("partial", "Parcialmente"), o("no", "Não"), o("unknown", "Ainda não sei")];
  var PERIODOS = [o("morning", "Manhã"), o("afternoon", "Tarde"), o("evening", "Noite"), o("any", "Indiferente")];
  // Perguntas opcionais "para adiantar a análise" (na mesma página; nenhuma é obrigatória)
  var CONSEQUENCIAS = [o("penalty", "Multa ou penalidade"), o("stoppage", "Paralisação ou atraso"), o("margin_cash_loss", "Perda de margem ou caixa"),
    o("technical_quality_risk", "Risco técnico ou de qualidade"), o("contract_conflict", "Conflito contratual"), o("decision_without_information", "Decisão sem informação suficiente"), o("other", "Outra")];
  var FAIXAS = [o("up_to_100k", "Até R$ 100 mil"), o("100k_to_1m", "R$ 100 mil a R$ 1 milhão"), o("1m_to_10m", "R$ 1 a 10 milhões"), o("10m_to_50m", "R$ 10 a 50 milhões"),
    o("above_50m", "Acima de R$ 50 milhões"), o("undisclosed", "Prefiro não informar"), o("unknown", "Ainda não sei")];
  var MAX_CONSEQUENCIAS = 2;

  var LIMITES = { narrativa: 1200, narrativaMin: 10, nome: 120, organizacao: 120, cidadeExterior: 80, regiao: 80 };
  var ORIGENS = ["hero", "industria", "produtos", "metodo", "sobre", "header", "final", "direto"];
  var PRODUTOS = ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10", "P11", "P12", "IA-1", "IA-2", "CV01"];

  function achar(lista, v) { for (var i = 0; i < lista.length; i++) if (lista[i].v === v) return lista[i]; return null; }

  // busca sem diferença de maiúsculas ou acentos
  function normalizar(t) { return String(t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim(); }

  /** Filtra [codigo, nome] pela busca: começa-com antes de contém. Devolve no máximo `max` itens. */
  function filtrar(itens, busca, max) {
    var b = normalizar(busca), ini = [], meio = [];
    for (var i = 0; i < itens.length; i++) {
      var n = normalizar(itens[i][1]);
      if (!b) ini.push(itens[i]);
      else if (n.indexOf(b) === 0) ini.push(itens[i]);
      else if (n.indexOf(b) > 0) meio.push(itens[i]);
      if (ini.length >= max && !b) break;
    }
    return ini.concat(meio).slice(0, max);
  }

  function emailValido(v) {
    v = (v || "").trim();
    return v.length <= 254 && /^[^\s@<>()\[\]\\,;:"]+@[^\s@<>()\[\]\\,;:"]+\.[^\s@<>()\[\]\\,;:"]{2,}$/.test(v);
  }
  // Mesma lógica do servidor: brasileiro (com ou sem +55) e internacional (+ e 8–15 dígitos). Devolve E.164 ou null.
  function normalizarTelefone(v) {
    var b = String(v).replace(/[\s().-]/g, "");
    if (!/^\+?\d{8,15}$/.test(b)) return null;
    if (b[0] === "+") return b;
    if (b.indexOf("55") === 0 && (b.length === 12 || b.length === 13)) return "+" + b;
    if (b.length === 10 || b.length === 11) {
      var ddd = b.slice(0, 2), resto = b.slice(2);
      if (ddd[0] !== "0" && ddd[1] !== "0" && (resto.length === 8 || (resto.length === 9 && resto[0] === "9"))) return "+55" + b;
    }
    return null;
  }

  /** Validação da página inteira. r = estado; devolve { campo: mensagem } (vazio = pode enviar). */
  function validar(r) {
    var e = {}, c = r.contact || {}, l = r.location || {};
    if (!achar(SITUACOES, r.situationCode)) e.situationCode = "Escolha o que mais se aproxima do seu cenário.";
    if (!achar(PERFIS, r.audienceProfile)) e.audienceProfile = "Escolha como você está falando.";
    if (!achar(PAPEIS, r.decisionRole)) e.decisionRole = "Escolha qual é a sua participação.";
    if (l.type === "brazil") {
      if (!l.stateCode) e["location.state"] = "Escolha o estado.";
      if (!l.cityCode) e["location.city"] = l.stateCode ? "Escolha uma cidade da lista." : "Escolha primeiro o estado.";
    } else if (l.type === "international") {
      if (!l.countryCode) e["location.country"] = "Escolha o país na lista.";
      if (!(l.intlCity || "").trim()) e["location.cityName"] = "Informe a cidade.";
      else if (l.intlCity.trim().length > LIMITES.cidadeExterior) e["location.cityName"] = "Use no máximo " + LIMITES.cidadeExterior + " caracteres.";
      if ((l.foreignRegion || "").trim().length > LIMITES.regiao) e["location.foreignRegion"] = "Use no máximo " + LIMITES.regiao + " caracteres.";
    } else e["location.type"] = "Informe se o cenário está no Brasil ou no exterior.";
    var n = (r.narrative || "").trim();
    if (n.length < LIMITES.narrativaMin) e.narrative = "Conte o essencial em ao menos " + LIMITES.narrativaMin + " caracteres.";
    else if (n.length > LIMITES.narrativa) e.narrative = "Use no máximo " + LIMITES.narrativa + " caracteres.";
    if ((c.name || "").trim().length < 2) e["contact.name"] = "Informe seu nome.";
    if (!achar(CANAIS, c.preferredChannel)) e["contact.preferredChannel"] = "Escolha como prefere receber a resposta.";
    if (c.preferredChannel === "whatsapp" && !normalizarTelefone(c.phone || "")) e["contact.phone"] = "Informe um WhatsApp válido, com DDD ou código do país (+).";
    if (c.preferredChannel === "email" && !emailValido(c.email)) e["contact.email"] = "Informe um e-mail válido.";
    if (c.preferredChannel !== "whatsapp" && (c.phone || "").trim() && !normalizarTelefone(c.phone)) e["contact.phone"] = "Confira o número do WhatsApp.";
    if (c.preferredChannel !== "email" && (c.email || "").trim() && !emailValido(c.email)) e["contact.email"] = "Confira o e-mail.";
    if ((r.consequences || []).length > MAX_CONSEQUENCIAS) e.consequences = "Escolha no máximo " + MAX_CONSEQUENCIAS + " opções.";
    return e;
  }

  // Parâmetros de origem: só valores das listas permitidas; o resto é descartado
  function lerOrigem(busca) {
    var p = new URLSearchParams(busca || "");
    var origem = p.get("origem"), interesse = p.get("interesse");
    var utm = function (k) { var v = p.get(k); return v && /^[A-Za-z0-9._~ +-]{1,80}$/.test(v) ? v : ""; };
    return {
      originCta: ORIGENS.indexOf(origem) >= 0 ? origem : "direto",
      productHint: PRODUTOS.indexOf(interesse) >= 0 ? interesse : null,
      utmSource: utm("utm_source"), utmMedium: utm("utm_medium"), utmCampaign: utm("utm_campaign"), utmContent: utm("utm_content"), utmTerm: utm("utm_term")
    };
  }

  /** Corpo enviado ao servidor. Só vai o que pertence ao modo escolhido (nada residual de Brasil ↔ Exterior). */
  function montarPayload(r, origem, extra) {
    var c = r.contact || {}, l = r.location || {};
    var loc = l.type === "brazil"
      ? { type: "brazil", countryCode: "BR", stateCode: l.stateCode, cityCode: l.cityCode, cityName: l.cityName }
      : { type: "international", countryCode: l.countryCode, cityName: (l.intlCity || "").trim(), foreignRegion: (l.foreignRegion || "").trim() };
    var contato = { name: (c.name || "").trim(), organization: (c.organization || "").trim(), preferredChannel: c.preferredChannel };
    if (c.contactPeriod) contato.contactPeriod = c.contactPeriod;
    var cenario = { situationCode: r.situationCode, contextAnswerCode: r.contextAnswerCode || null, audienceProfile: r.audienceProfile,
      decisionRole: r.decisionRole, location: loc, narrative: (r.narrative || "").trim() };
    if (r.urgency) cenario.urgency = r.urgency;
    if ((r.consequences || []).length) cenario.consequences = r.consequences.slice();
    if (r.documents) cenario.documents = r.documents;
    if (r.estimatedRange) cenario.estimatedRange = r.estimatedRange;
    if ((c.phone || "").trim()) contato.phone = c.phone.trim();
    if ((c.email || "").trim()) contato.email = c.email.trim();
    return {
      idempotencyKey: extra.idempotencyKey, schemaVersion: 2, formVersion: extra.formVersion, elapsedMs: extra.elapsedMs,
      source: { originCta: origem.originCta, productHint: origem.productHint, utmSource: origem.utmSource, utmMedium: origem.utmMedium,
        utmCampaign: origem.utmCampaign, utmContent: origem.utmContent, utmTerm: origem.utmTerm, deviceCategory: extra.deviceCategory, referrer: extra.referrer || "" },
      scenario: cenario,
      contact: contato,
      privacy: { privacyNoticeVersion: extra.privacyNoticeVersion, acknowledged: true },
      website: extra.honeypot || ""
    };
  }

  global.CRIVIA_REGRAS = {
    SITUACOES: SITUACOES, PERFIS: PERFIS, PAPEIS: PAPEIS, CANAIS: CANAIS, URGENCIAS: URGENCIAS, DOCUMENTOS: DOCUMENTOS, PERIODOS: PERIODOS,
    CONSEQUENCIAS: CONSEQUENCIAS, FAIXAS: FAIXAS, MAX_CONSEQUENCIAS: MAX_CONSEQUENCIAS,
    LIMITES: LIMITES, ORIGENS: ORIGENS, PRODUTOS: PRODUTOS,
    achar: achar, normalizar: normalizar, filtrar: filtrar, validar: validar, normalizarTelefone: normalizarTelefone, emailValido: emailValido,
    lerOrigem: lerOrigem, montarPayload: montarPayload
  };
})(window);
