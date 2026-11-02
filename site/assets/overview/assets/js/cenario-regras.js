/* Regras do formulário "Apresentar meu cenário": perguntas, ramificações e validação do lado do navegador.
   Dados puros (sem DOM): podem ser testados em tests/regras.test.html. O servidor revalida tudo (servidor/regras_leads.py);
   os valores internos abaixo são os mesmos do servidor e NÃO devem ser traduzidos. */
(function (global) {
  "use strict";

  var o = function (v, l, d) { return d ? { v: v, l: l, d: d } : { v: v, l: l }; };

  var ENTRADAS = [
    o("underperforming", "Algo não está entregando como deveria", "Obra, contrato, prazo, custo, medição, produtividade ou recursos."),
    o("decision_support", "Preciso avaliar antes de decidir", "Terreno, projeto, proposta, orçamento, planejamento, contratação ou recebimento."),
    o("visual_communication", "Preciso tornar uma solução técnica mais clara", "Imagens, 3D, apresentações, vídeos ou proposta técnico-comercial."),
    o("ai_decision_engineering", "Quero preparar ou corrigir o uso de IA", "Integração de pessoas, áreas e inteligência artificial."),
    o("other_or_unsure", "Ainda não sei ou meu caso é diferente", "Conte o essencial e a CRIVIA avaliará o melhor enquadramento para a conversa.")
  ];

  var CONTEXTOS = [
    o("contractor", "Empreiteira ou prestadora de serviços"),
    o("large_company", "Grande empresa, indústria ou contratante"),
    o("owner_investor", "Proprietário, investidor ou condomínio"),
    o("technical_partner", "Escritório, projetista ou parceiro técnico"),
    o("other", "Outro contexto")
  ];
  var CONTEXTOS_EMPRESARIAIS = ["contractor", "large_company", "technical_partner"];

  var PAPEIS = [
    o("decides", "Decido ou autorizo a contratação"),
    o("leads_evaluation", "Lidero a avaliação e apresento a decisão"),
    o("technical_participant", "Participo tecnicamente do processo"),
    o("early_research", "Estou fazendo uma pesquisa inicial"),
    o("other", "Outro papel")
  ];

  var FASES = [
    o("planning", "Em planejamento"), o("execution", "Em execução"), o("delay_or_critical", "Em atraso ou situação crítica"),
    o("near_completion", "Próximo da conclusão"), o("operation", "Em operação"), o("unsure", "Não tenho certeza")
  ];
  var PROBLEMAS = [
    o("schedule", "Prazo"), o("margin_cost", "Margem ou custo"), o("measurement_receipt", "Medição ou recebimento"),
    o("scope_change", "Escopo ou alteração contratual"), o("team_equipment_material", "Equipe, equipamento ou material"),
    o("project_info", "Projeto ou informação técnica"), o("quality", "Qualidade"), o("supplier", "Fornecedor"),
    o("undefined_responsibilities", "Responsabilidades indefinidas"), o("other", "Outro")
  ];
  var CONSEQUENCIAS = [
    o("penalty", "Multa ou penalidade"), o("stoppage", "Paralisação ou atraso"), o("margin_cash_loss", "Perda de margem ou caixa"),
    o("technical_quality_risk", "Risco técnico ou de qualidade"), o("contract_conflict", "Conflito contratual"),
    o("operation_impact", "Impacto na operação"), o("decision_without_information", "Decisão sem informação suficiente"),
    o("other", "Outra consequência")
  ];
  var HORIZONTES = [
    o("up_to_7_days", "Até 7 dias"), o("8_to_30_days", "Entre 8 e 30 dias"), o("31_to_90_days", "Entre 31 e 90 dias"),
    o("after_90_days", "Depois de 90 dias"), o("undefined", "Ainda não definido")
  ];
  var AVALIAR = [
    o("land", "Terreno"), o("projects", "Projetos"), o("budget_costs", "Orçamento ou custos"),
    o("supplier_proposals", "Propostas de fornecedores"), o("planning_resources", "Planejamento e recursos"),
    o("measurement_change", "Medição ou alteração contratual"), o("handover", "Recebimento da obra"),
    o("documentation_databook", "Documentação ou data book"), o("other", "Outro")
  ];
  var ENTREGAS = [
    o("explainer_video", "Vídeo explicativo"), o("image_or_3d", "Imagem ou representação 3D"), o("technical_presentation", "Apresentação técnica"),
    o("visual_proposal", "Proposta técnico-comercial visual"), o("combination", "Combinação dessas entregas"), o("undefined", "Ainda não definido")
  ];
  var FINALIDADES = [
    o("explain_solution", "Explicar uma solução"), o("present_project", "Apresentar um projeto"), o("compare_alternatives", "Comparar alternativas"),
    o("present_proposal", "Apresentar uma proposta"), o("show_process", "Demonstrar etapas ou processo"), o("other", "Outra")
  ];
  var PUBLICOS_VISUAIS = [
    o("client", "Cliente"), o("board", "Diretoria"), o("technical_team", "Equipe técnica"), o("investor", "Investidor"),
    o("general_public", "Público geral"), o("other", "Outro")
  ];
  var REFERENCIAS = [
    o("idea_only", "Apenas ideia ou conceito"), o("photos_info", "Fotografias e informações"), o("plans_projects", "Plantas ou projetos"),
    o("existing_3d_model", "Modelo 3D existente"), o("not_organized", "Ainda não tenho material organizado")
  ];
  var SITUACOES_IA = [
    o("expand_transition", "Vai ampliar o uso de IA e precisa preparar a transição"),
    o("already_using", "Já utiliza IA, mas enfrenta dificuldades"),
    o("evaluating", "Ainda está avaliando por onde começar")
  ];
  var DIFICULDADES_IA = [
    o("unreliable_output", "Erros ou informações não confiáveis"), o("rework", "Retrabalho"), o("overload", "Sobrecarga"),
    o("inadequate_decisions", "Decisões inadequadas"), o("lack_of_checking", "Falta de conferência"), o("areas_misaligned", "Desencontro entre áreas"),
    o("people_unprepared", "Pessoas sem preparo suficiente"), o("tools_disconnected", "Ferramentas desconectadas do processo"),
    o("unclear_responsibilities", "Falta de responsabilidades claras"), o("other", "Outra")
  ];
  var AREAS_IA = [
    o("operations", "Operações"), o("engineering", "Engenharia"), o("procurement", "Suprimentos"), o("finance", "Financeiro"),
    o("legal_contracts", "Jurídico ou contratos"), o("it", "Tecnologia da informação"), o("board", "Diretoria"), o("other", "Outras áreas")
  ];
  var PESSOAS = [
    o("up_to_10", "Até 10 pessoas"), o("11_to_50", "De 11 a 50 pessoas"), o("51_to_200", "De 51 a 200 pessoas"),
    o("above_200", "Mais de 200 pessoas"), o("undisclosed", "Prefiro não informar")
  ];
  var PROCESSOS = [
    o("planning", "Planejamento"), o("execution", "Execução"), o("procurement", "Compras e suprimentos"), o("measurement", "Medição"),
    o("documentation", "Documentação"), o("customer_service", "Atendimento"), o("other", "Outro")
  ];
  var FAIXAS = [
    o("up_to_100k", "Até R$ 100 mil"), o("100k_to_1m", "De R$ 100 mil a R$ 1 milhão"), o("1m_to_10m", "De R$ 1 milhão a R$ 10 milhões"),
    o("10m_to_50m", "De R$ 10 milhões a R$ 50 milhões"), o("above_50m", "Acima de R$ 50 milhões"),
    o("undisclosed", "Prefiro não informar"), o("unknown", "Ainda não sei")
  ];
  var DOCUMENTOS = [
    o("contract", "Contrato"), o("projects", "Projetos"), o("schedule", "Cronograma"), o("budget", "Orçamento"), o("measurements", "Medições"),
    o("photos_records", "Fotografias ou registros"), o("process_data", "Procedimentos ou dados do processo"),
    o("none_organized", "Ainda não tenho documentos organizados"), o("other", "Outro")
  ];
  var CANAIS = [o("whatsapp", "WhatsApp"), o("email", "E-mail"), o("phone_call", "Ligação")];
  var PERIODOS = [o("morning", "Manhã"), o("afternoon", "Tarde"), o("evening", "Noite"), o("business_hours_any", "Qualquer horário comercial")];
  var UFS = [["AC", "Acre"], ["AL", "Alagoas"], ["AP", "Amapá"], ["AM", "Amazonas"], ["BA", "Bahia"], ["CE", "Ceará"], ["DF", "Distrito Federal"],
    ["ES", "Espírito Santo"], ["GO", "Goiás"], ["MA", "Maranhão"], ["MT", "Mato Grosso"], ["MS", "Mato Grosso do Sul"], ["MG", "Minas Gerais"],
    ["PA", "Pará"], ["PB", "Paraíba"], ["PR", "Paraná"], ["PE", "Pernambuco"], ["PI", "Piauí"], ["RJ", "Rio de Janeiro"], ["RN", "Rio Grande do Norte"],
    ["RS", "Rio Grande do Sul"], ["RO", "Rondônia"], ["RR", "Roraima"], ["SC", "Santa Catarina"], ["SP", "São Paulo"], ["SE", "Sergipe"], ["TO", "Tocantins"]];

  var ORIGENS = ["hero", "industria", "produtos", "metodo", "sobre", "header", "final", "direto"];
  var PRODUTOS = ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10", "P11", "P12", "IA-1", "IA-2", "CV01"];
  var NOMES_PRODUTOS = {
    P01: "Diagnóstico de obra ou contrato", P02: "Análise crítica de projetos", P03: "Avaliação preliminar de terreno", P04: "Orçamento e análise de custos",
    P05: "Comparação técnica de propostas", P06: "Planejamento de obra e recursos", P07: "Plano de recuperação de obra", P08: "Análise de processo e produtividade",
    P09: "Medições e alterações contratuais", P10: "Acompanhamento técnico das obras", P11: "Vistoria para recebimento", P12: "Organização e conferência de documentos",
    "IA-1": "Preparação da transição para IA", "IA-2": "Diagnóstico e ajustes após a adoção", CV01: "Visualização e comunicação técnica com IA e 3D"
  };

  // Perguntas por tipo: single (uma escolha), multi (várias, com limite), text (campo curto), area (texto longo), select (lista), note (aviso)
  var q = function (id, tipo, rotulo, extra) {
    var base = { id: id, tipo: tipo, rotulo: rotulo, obrigatorio: true };
    for (var k in extra) base[k] = extra[k];
    return base;
  };

  var P_FASE = q("stage", "single", "Em qual fase o cenário está?", { opcoes: FASES });
  var P_HORIZONTE = q("decisionHorizon", "single", "Quando essa decisão precisa avançar?", { opcoes: HORIZONTES });
  var P_CONSEQ = q("consequences", "multi", "Qual consequência mais preocupa?", { opcoes: CONSEQUENCIAS, max: 2 });
  var P_NARRATIVA = function (rotulo, ajuda) {
    return q("narrative", "area", rotulo, { max: 700, min: 10, ajuda: ajuda || "Não precisa usar linguagem técnica. Não inclua dados pessoais sensíveis, segredos comerciais ou documentos confidenciais." });
  };

  function ramo(entrada) {
    switch (entrada) {
      case "underperforming":
        return [
          P_FASE,
          q("issues", "multi", "O que está mais comprometido?", { opcoes: PROBLEMAS, max: 3 }),
          P_CONSEQ, P_HORIZONTE,
          P_NARRATIVA("Em poucas linhas, o que está acontecendo e qual decisão precisa ser tomada?")
        ];
      case "decision_support":
        return [
          q("branch.evaluate", "multi", "O que você precisa avaliar?", { opcoes: AVALIAR, max: 3 }),
          q("stage", "single", "Qual é a fase atual?", { opcoes: FASES }),
          P_HORIZONTE,
          q("consequences", "multi", "Qual a consequência de decidir sem essa informação?", { opcoes: CONSEQUENCIAS, max: 2 }),
          P_NARRATIVA("Qual decisão você precisa tomar com mais segurança?")
        ];
      case "visual_communication":
        return [
          q("branch.deliverable", "single", "O que precisa ser produzido?", { opcoes: ENTREGAS }),
          q("note", "note", "", { texto: "Imagem conceitual, imagem baseada em projeto e modelo 3D editável são entregas diferentes. A definição final depende dos arquivos e da fidelidade necessários.", obrigatorio: false }),
          q("branch.purpose", "single", "Qual é a finalidade?", { opcoes: FINALIDADES }),
          q("branch.audience", "single", "Para quem será apresentado?", { opcoes: PUBLICOS_VISUAIS }),
          q("branch.referenceLevel", "single", "Qual nível de referência existe?", { opcoes: REFERENCIAS }),
          q("decisionHorizon", "single", "Quando precisa estar pronto?", { opcoes: HORIZONTES, ajuda: "São faixas de referência para a conversa; não representam promessa de entrega." }),
          P_NARRATIVA("O que precisa ficar claro para quem verá esse material?")
        ];
      case "ai_decision_engineering":
        return [
          q("branch.aiSituation", "single", "Em qual situação sua empresa está?", { opcoes: SITUACOES_IA }),
          q("branch.difficulties", "multi", "Quais dificuldades são observadas?", { opcoes: DIFICULDADES_IA, max: 10, condicao: function (r) { return r.branch && r.branch.aiSituation === "already_using"; } }),
          q("branch.areas", "multi", "Quais áreas ou funções estão envolvidas?", { opcoes: AREAS_IA, max: 8 }),
          q("branch.peopleRange", "single", "Quantas pessoas, aproximadamente, estão envolvidas?", { opcoes: PESSOAS }),
          q("branch.affectedProcess", "single", "Qual é o processo mais afetado?", { opcoes: PROCESSOS }),
          P_CONSEQ, P_HORIZONTE,
          P_NARRATIVA("O que precisa melhorar na relação entre pessoas, áreas e IA?")
        ];
      default: // other_or_unsure
        return [
          q("note", "note", "", { texto: "Não precisa classificar o problema. Conte o essencial e a CRIVIA fará o enquadramento inicial.", obrigatorio: false }),
          P_NARRATIVA("O que está acontecendo?", "Descreva o contexto em poucas linhas. Não inclua dados pessoais sensíveis, segredos comerciais ou documentos confidenciais."),
          q("branch.decisionNeeded", "area", "Qual decisão precisa ser tomada?", { max: 500, min: 10 }),
          P_CONSEQ, P_HORIZONTE
        ];
    }
  }

  var COMUNS = [
    q("city", "text", "Cidade", { max: 80, min: 2, autocomplete: "address-level2", ajuda: "Somente a cidade; não peça nem informe endereço completo." }),
    q("state", "select", "Estado", { opcoes: UFS.map(function (u) { return o(u[0], u[1] + " (" + u[0] + ")"); }), autocomplete: "address-level1" }),
    q("availableDocuments", "multi", "Quais documentos você já tem?", { opcoes: DOCUMENTOS, max: 9, ajuda: "Nesta etapa não é preciso enviar nada." }),
    q("estimatedRange", "single", "Faixa aproximada do empreendimento, contrato ou processo", { opcoes: FAIXAS, obrigatorio: false, ajuda: "Opcional. Ajuda a CRIVIA a se preparar para a conversa." })
  ];

  function perguntasEtapa3(respostas) {
    return ramo(respostas.entryPath).concat(COMUNS).filter(function (p) { return !p.condicao || p.condicao(respostas); });
  }

  function obter(respostas, id) {
    if (id.indexOf("branch.") === 0) return (respostas.branch || {})[id.slice(7)];
    return respostas[id];
  }
  function definir(respostas, id, valor) {
    if (id.indexOf("branch.") === 0) { respostas.branch = respostas.branch || {}; respostas.branch[id.slice(7)] = valor; }
    else respostas[id] = valor;
  }

  // validação por etapa: devolve { campo: mensagem }
  function validarEtapa(etapa, r) {
    var e = {};
    var vazio = function (v) { return v === undefined || v === null || v === "" || (Array.isArray(v) && !v.length); };
    if (etapa === 1) {
      if (vazio(r.entryPath)) e.entryPath = "Escolha a situação que melhor descreve o que você precisa agora.";
    } else if (etapa === 2) {
      if (vazio(r.audienceContext)) e.audienceContext = "Escolha o contexto em que esse cenário acontece.";
      if (vazio(r.decisionRole)) e.decisionRole = "Escolha o seu papel nessa decisão.";
    } else if (etapa === 3) {
      perguntasEtapa3(r).forEach(function (p) {
        if (p.tipo === "note") return;
        var v = obter(r, p.id);
        if (p.obrigatorio && vazio(v)) { e[p.id] = p.tipo === "multi" ? "Escolha ao menos uma opção." : p.tipo === "text" || p.tipo === "area" ? "Preencha este campo." : "Escolha uma opção."; return; }
        if ((p.tipo === "text" || p.tipo === "area") && typeof v === "string" && v.trim().length) {
          if (p.min && v.trim().length < p.min) e[p.id] = "Escreva ao menos " + p.min + " caracteres.";
          if (p.max && v.length > p.max) e[p.id] = "Use no máximo " + p.max + " caracteres.";
        }
        if (p.tipo === "multi" && Array.isArray(v) && p.max && v.length > p.max) e[p.id] = "Escolha no máximo " + p.max + " opções.";
      });
    } else if (etapa === 4) {
      var c = r.contact || {};
      var empresarial = CONTEXTOS_EMPRESARIAIS.indexOf(r.audienceContext) >= 0;
      if (!c.name || c.name.trim().length < 2) e["contact.name"] = "Informe seu nome.";
      if (empresarial && !(c.organization || "").trim()) e["contact.organization"] = "Informe a empresa ou organização.";
      if (!c.preferredChannel) e["contact.preferredChannel"] = "Escolha como prefere receber o retorno.";
      if (c.preferredChannel === "whatsapp" || c.preferredChannel === "phone_call") {
        if (!normalizarTelefone(c.phone || "")) e["contact.phone"] = "Informe um telefone válido, com DDD.";
      }
      if (c.preferredChannel === "email" || (c.email || "").trim()) {
        if (!emailValido(c.email || "")) e["contact.email"] = "Informe um e-mail válido.";
      }
      if (c.secondChannel) {
        var ok = c.secondChannel === "email" ? emailValido(c.secondValue || "") : !!normalizarTelefone(c.secondValue || "");
        if (!ok) e["contact.secondValue"] = "Confira o segundo contato.";
      }
    }
    return e;
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

  // Monta o corpo enviado ao servidor (o servidor valida de novo)
  function montarPayload(r, origem, extra) {
    var c = r.contact || {};
    var s = {
      entryPath: r.entryPath, audienceContext: r.audienceContext, decisionRole: r.decisionRole,
      stage: r.stage || null, issues: r.entryPath === "underperforming" ? (r.issues || []) : [], consequences: r.consequences || [],
      decisionHorizon: r.decisionHorizon, city: (r.city || "").trim(), state: r.state, estimatedRange: r.estimatedRange || null,
      availableDocuments: r.availableDocuments || [], narrative: (r.narrative || "").trim(), branchSpecificData: {}
    };
    var b = r.branch || {};
    var chaves = {
      decision_support: ["evaluate"], visual_communication: ["deliverable", "purpose", "audience", "referenceLevel"],
      ai_decision_engineering: ["aiSituation", "difficulties", "areas", "peopleRange", "affectedProcess"], other_or_unsure: ["decisionNeeded"], underperforming: []
    }[r.entryPath] || [];
    chaves.forEach(function (k) { if (b[k] !== undefined && b[k] !== "") s.branchSpecificData[k] = typeof b[k] === "string" ? b[k].trim() : b[k]; });
    if (s.branchSpecificData.aiSituation !== "already_using") delete s.branchSpecificData.difficulties;
    var contact = {
      name: (c.name || "").trim(), organization: (c.organization || "").trim(), roleTitle: (c.roleTitle || "").trim(),
      preferredChannel: c.preferredChannel, phone: c.phone || "", email: (c.email || "").trim(), preferredContactPeriod: c.preferredContactPeriod || null
    };
    if (c.secondChannel) { contact.secondChannel = c.secondChannel; contact.secondValue = (c.secondValue || "").trim(); }
    return {
      idempotencyKey: extra.idempotencyKey, schemaVersion: 1,
      source: { originCta: origem.originCta, productHint: origem.productHint, utmSource: origem.utmSource, utmMedium: origem.utmMedium,
        utmCampaign: origem.utmCampaign, utmContent: origem.utmContent, utmTerm: origem.utmTerm, deviceCategory: extra.deviceCategory, referrer: extra.referrer || "" },
      scenario: s, contact: contact,
      privacy: { privacyNoticeVersion: extra.privacyNoticeVersion, acknowledged: true, marketingConsent: false },
      website: extra.honeypot || ""
    };
  }

  global.CRIVIA_REGRAS = {
    ENTRADAS: ENTRADAS, CONTEXTOS: CONTEXTOS, PAPEIS: PAPEIS, CANAIS: CANAIS, PERIODOS: PERIODOS, NOMES_PRODUTOS: NOMES_PRODUTOS,
    CONTEXTOS_EMPRESARIAIS: CONTEXTOS_EMPRESARIAIS, ORIGENS: ORIGENS, PRODUTOS: PRODUTOS,
    perguntasEtapa3: perguntasEtapa3, validarEtapa: validarEtapa, obter: obter, definir: definir,
    normalizarTelefone: normalizarTelefone, emailValido: emailValido, lerOrigem: lerOrigem, montarPayload: montarPayload
  };
})(window);
