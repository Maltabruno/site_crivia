/**
 * Validação estrita e normalização da submissão (porta de servidor/regras_leads.py).
 * O navegador nunca é fonte de confiança: tudo é revalidado aqui. Valores internos são estáveis (inglês).
 */
var LISTAS = {
  ENTRY: ['underperforming', 'decision_support', 'visual_communication', 'ai_decision_engineering', 'other_or_unsure'],
  AUDIENCE: ['contractor', 'large_company', 'owner_investor', 'technical_partner', 'other'],
  BUSINESS: ['contractor', 'large_company', 'technical_partner'],
  ROLES: ['decides', 'leads_evaluation', 'technical_participant', 'early_research', 'other'],
  STAGES: ['planning', 'execution', 'delay_or_critical', 'near_completion', 'operation', 'unsure'],
  ISSUES: ['schedule', 'margin_cost', 'measurement_receipt', 'scope_change', 'team_equipment_material', 'project_info', 'quality', 'supplier', 'undefined_responsibilities', 'other'],
  CONSEQUENCES: ['penalty', 'stoppage', 'margin_cash_loss', 'technical_quality_risk', 'contract_conflict', 'operation_impact', 'decision_without_information', 'other'],
  HIGH_CONSEQUENCES: ['penalty', 'stoppage', 'margin_cash_loss', 'contract_conflict'],
  HORIZONS: ['up_to_7_days', '8_to_30_days', '31_to_90_days', 'after_90_days', 'undefined'],
  EVALUATE: ['land', 'projects', 'budget_costs', 'supplier_proposals', 'planning_resources', 'measurement_change', 'handover', 'documentation_databook', 'other'],
  DELIVERABLES: ['explainer_video', 'image_or_3d', 'technical_presentation', 'visual_proposal', 'combination', 'undefined'],
  PURPOSES: ['explain_solution', 'present_project', 'compare_alternatives', 'present_proposal', 'show_process', 'other'],
  VISUAL_AUDIENCE: ['client', 'board', 'technical_team', 'investor', 'general_public', 'other'],
  REFERENCE_LEVELS: ['idea_only', 'photos_info', 'plans_projects', 'existing_3d_model', 'not_organized'],
  AI_SITUATIONS: ['expand_transition', 'already_using', 'evaluating'],
  AI_DIFFICULTIES: ['unreliable_output', 'rework', 'overload', 'inadequate_decisions', 'lack_of_checking', 'areas_misaligned', 'people_unprepared', 'tools_disconnected', 'unclear_responsibilities', 'other'],
  AI_AREAS: ['operations', 'engineering', 'procurement', 'finance', 'legal_contracts', 'it', 'board', 'other'],
  PEOPLE: ['up_to_10', '11_to_50', '51_to_200', 'above_200', 'undisclosed'],
  PROCESSES: ['planning', 'execution', 'procurement', 'measurement', 'documentation', 'customer_service', 'other'],
  RANGES: ['up_to_100k', '100k_to_1m', '1m_to_10m', '10m_to_50m', 'above_50m', 'undisclosed', 'unknown'],
  DOCUMENTS: ['contract', 'projects', 'schedule', 'budget', 'measurements', 'photos_records', 'process_data', 'none_organized', 'other'],
  CHANNELS: ['whatsapp', 'email', 'phone_call'],
  PERIODS: ['morning', 'afternoon', 'evening', 'business_hours_any'],
  UFS: ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
  ORIGINS: ['hero', 'industria', 'produtos', 'metodo', 'sobre', 'header', 'final', 'direto'],
  PRODUCTS: ['P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11', 'P12', 'IA-1', 'IA-2', 'CV01'],
  DEVICES: ['mobile', 'tablet', 'desktop', 'unknown']
};
var LIMITES = { narrative: 700, shortText: 500, name: 120, organization: 120, roleTitle: 80, city: 80, additionalInfo: 700 };

function ErroValidacao_(campos) { this.campos = campos; }

/** Acumulador de erros de validação. */
function novoValidador_() {
  var erros = {}, suspeita = false;
  var v = {
    erros: erros,
    suspeita: function () { return suspeita; },
    erro: function (caminho, codigo) { if (!erros[caminho]) erros[caminho] = codigo; },
    obj: function (valor, caminho, permitidas, obrigatorias) {
      if (valor === null || typeof valor !== 'object' || Array.isArray(valor)) { v.erro(caminho, 'tipo'); return {}; }
      Object.keys(valor).forEach(function (k) { if (permitidas.indexOf(k) < 0) v.erro(caminho + '.' + k, 'campo_desconhecido'); });
      (obrigatorias || []).forEach(function (k) { if (!(k in valor)) v.erro(caminho + '.' + k, 'obrigatorio'); });
      return valor;
    },
    enm: function (valor, caminho, permitidos, obrigatorio) {
      if (valor === null || valor === undefined || valor === '') { if (obrigatorio) v.erro(caminho, 'obrigatorio'); return null; }
      if (typeof valor !== 'string' || permitidos.indexOf(valor) < 0) { v.erro(caminho, 'valor_invalido'); return null; }
      return valor;
    },
    lista: function (valor, caminho, permitidos, maximo, obrigatorio) {
      if (valor === null || valor === undefined || (Array.isArray(valor) && !valor.length)) { if (obrigatorio) v.erro(caminho, 'obrigatorio'); return []; }
      if (!Array.isArray(valor)) { v.erro(caminho, 'tipo'); return []; }
      if (valor.length > maximo) { v.erro(caminho, 'limite_de_selecoes'); return []; }
      var saida = [];
      for (var i = 0; i < valor.length; i++) {
        if (typeof valor[i] !== 'string' || permitidos.indexOf(valor[i]) < 0) { v.erro(caminho, 'valor_invalido'); return []; }
        if (saida.indexOf(valor[i]) < 0) saida.push(valor[i]);
      }
      return saida;
    },
    texto: function (valor, caminho, maximo, obrigatorio, minimo) {
      if (valor === null || valor === undefined || valor === '') { if (obrigatorio) v.erro(caminho, 'obrigatorio'); return ''; }
      if (typeof valor !== 'string') { v.erro(caminho, 'tipo'); return ''; }
      var t = limparTexto_(valor);
      if (t.length > maximo) { v.erro(caminho, 'tamanho'); return ''; }
      var cpf = /\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/, cnpj = /\b\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}\b/;
      if (cpf.test(t) || cnpj.test(t)) { suspeita = true; t = t.replace(cpf, '[removido]').replace(cnpj, '[removido]'); }
      if (obrigatorio && t.length < Math.max(1, minimo || 0)) v.erro(caminho, t ? 'muito_curto' : 'obrigatorio');
      else if (minimo && t && t.length < minimo) v.erro(caminho, 'muito_curto');
      return t;
    }
  };
  return v;
}

function limparTexto_(s) {
  var t = String(s).normalize('NFC').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, '');
  return t.replace(/[ \t]{2,}/g, ' ').trim();
}

/** E.164 a partir de número brasileiro (com ou sem +55) ou internacional (+ e 8–15 dígitos). Devolve null se inválido. */
function normalizarTelefone_(valor) {
  var b = String(valor).replace(/[\s().-]/g, '');
  if (!/^\+?\d{8,15}$/.test(b)) return null;
  if (b.charAt(0) === '+') return b;
  if (b.indexOf('55') === 0 && (b.length === 12 || b.length === 13)) return '+' + b;
  if (b.length === 10 || b.length === 11) {
    var ddd = b.slice(0, 2), resto = b.slice(2);
    if (ddd.charAt(0) !== '0' && ddd.charAt(1) !== '0' && (resto.length === 8 || (resto.length === 9 && resto.charAt(0) === '9'))) return '+55' + b;
  }
  return null;
}

function emailValido_(s) {
  return typeof s === 'string' && s.length <= 254 &&
    /^[A-Za-z0-9.!#$%&'*+\/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/.test(s);
}

/** Valida a submissão completa. Lança ErroValidacao_. Devolve o registro normalizado (sem id nem datas). */
function validarLead_(corpo) {
  var v = novoValidador_(), L = LISTAS;
  var topo = v.obj(corpo, '$', ['idempotencyKey', 'schemaVersion', 'source', 'scenario', 'contact', 'privacy', 'website', 'turnstileToken'],
    ['idempotencyKey', 'scenario', 'contact', 'privacy']);
  var chave = topo.idempotencyKey;
  if (typeof chave !== 'string' || !/^[A-Za-z0-9-]{8,64}$/.test(chave)) v.erro('idempotencyKey', 'valor_invalido');
  if (topo.schemaVersion !== undefined && topo.schemaVersion !== CRIVIA.SCHEMA_VERSION) v.erro('schemaVersion', 'valor_invalido');

  var o = v.obj(topo.source || {}, 'source', ['landingPage', 'referrer', 'originCta', 'productHint', 'utmSource', 'utmMedium', 'utmCampaign', 'utmContent', 'utmTerm', 'deviceCategory']);
  var source = {
    landingPage: '/apresentar-cenario', referrer: '',
    originCta: v.enm(o.originCta, 'source.originCta', L.ORIGINS, false) || 'direto',
    productHint: v.enm(o.productHint, 'source.productHint', L.PRODUCTS, false),
    deviceCategory: v.enm(o.deviceCategory, 'source.deviceCategory', L.DEVICES, false) || 'unknown'
  };
  if (o.referrer) { if (typeof o.referrer === 'string' && /^[A-Za-z0-9.-]{1,120}$/.test(o.referrer)) source.referrer = o.referrer.toLowerCase(); else v.erro('source.referrer', 'valor_invalido'); }
  ['utmSource', 'utmMedium', 'utmCampaign', 'utmContent', 'utmTerm'].forEach(function (k) {
    var x = o[k];
    if (x === null || x === undefined || x === '') source[k] = '';
    else if (typeof x === 'string' && /^[A-Za-z0-9._~ +-]{0,80}$/.test(x)) source[k] = x;
    else v.erro('source.' + k, 'valor_invalido');
  });

  var s = v.obj(topo.scenario, 'scenario', ['entryPath', 'audienceContext', 'decisionRole', 'stage', 'issues', 'consequences', 'decisionHorizon', 'city', 'state', 'estimatedRange', 'availableDocuments', 'narrative', 'branchSpecificData'],
    ['entryPath', 'audienceContext', 'decisionRole', 'narrative', 'city', 'state']);
  var entrada = v.enm(s.entryPath, 'scenario.entryPath', L.ENTRY, true);
  var cenario = {
    entryPath: entrada,
    audienceContext: v.enm(s.audienceContext, 'scenario.audienceContext', L.AUDIENCE, true),
    decisionRole: v.enm(s.decisionRole, 'scenario.decisionRole', L.ROLES, true),
    stage: v.enm(s.stage, 'scenario.stage', L.STAGES, entrada === 'underperforming' || entrada === 'decision_support'),
    issues: entrada === 'underperforming' ? v.lista(s.issues, 'scenario.issues', L.ISSUES, 3, true) : [],
    consequences: v.lista(s.consequences, 'scenario.consequences', L.CONSEQUENCES, 2, ['underperforming', 'decision_support', 'ai_decision_engineering', 'other_or_unsure'].indexOf(entrada) >= 0),
    decisionHorizon: v.enm(s.decisionHorizon, 'scenario.decisionHorizon', L.HORIZONS, true),
    city: v.texto(s.city, 'scenario.city', LIMITES.city, true, 2),
    state: v.enm(s.state, 'scenario.state', L.UFS, true),
    estimatedRange: v.enm(s.estimatedRange, 'scenario.estimatedRange', L.RANGES, false),
    availableDocuments: v.lista(s.availableDocuments, 'scenario.availableDocuments', L.DOCUMENTS, L.DOCUMENTS.length, true),
    narrative: v.texto(s.narrative, 'scenario.narrative', LIMITES.narrative, true, 10),
    branchSpecificData: {}
  };
  if (cenario.city && !/^[^\d<>{}\[\]\\|^~`@#$%*=+_]{2,80}$/.test(cenario.city)) v.erro('scenario.city', 'valor_invalido');
  cenario.branchSpecificData = ramo_(v, entrada, s.branchSpecificData);

  var c = v.obj(topo.contact, 'contact', ['name', 'organization', 'roleTitle', 'preferredChannel', 'phone', 'email', 'secondChannel', 'secondValue', 'preferredContactPeriod'], ['name', 'preferredChannel']);
  var canal = v.enm(c.preferredChannel, 'contact.preferredChannel', L.CHANNELS, true);
  var nome = v.texto(c.name, 'contact.name', LIMITES.name, true, 2);
  if (nome && !/^[^\d<>{}\[\]\\|^~`@#$%*=+_]{2,}$/.test(nome)) v.erro('contact.name', 'valor_invalido');
  var organizacao = v.texto(c.organization, 'contact.organization', LIMITES.organization, L.BUSINESS.indexOf(cenario.audienceContext) >= 0);
  var telefone = null, email = null;
  if (c.phone !== undefined && c.phone !== null && c.phone !== '') { telefone = typeof c.phone === 'string' ? normalizarTelefone_(c.phone) : null; if (!telefone) v.erro('contact.phone', 'valor_invalido'); }
  if (c.email !== undefined && c.email !== null && c.email !== '') {
    var e = typeof c.email === 'string' ? c.email.trim() : '';
    if (emailValido_(e)) email = e.toLowerCase(); else v.erro('contact.email', 'valor_invalido');
  }
  if ((canal === 'whatsapp' || canal === 'phone_call') && !telefone && !v.erros['contact.phone']) v.erro('contact.phone', 'obrigatorio');
  if (canal === 'email' && !email && !v.erros['contact.email']) v.erro('contact.email', 'obrigatorio');
  var segundo = v.enm(c.secondChannel, 'contact.secondChannel', L.CHANNELS, false), segundoValor = '';
  if (segundo) {
    var bruto = c.secondValue;
    if (segundo === 'email') segundoValor = (typeof bruto === 'string' && emailValido_(bruto.trim())) ? bruto.trim().toLowerCase() : '';
    else segundoValor = typeof bruto === 'string' ? (normalizarTelefone_(bruto) || '') : '';
    if (!segundoValor) v.erro('contact.secondValue', 'valor_invalido');
  }
  var contato = {
    name: nome, organization: organizacao, roleTitle: v.texto(c.roleTitle, 'contact.roleTitle', LIMITES.roleTitle, false),
    preferredChannel: canal, phone: telefone || '', email: email || '', secondChannel: segundo, secondValue: segundoValor,
    preferredContactPeriod: v.enm(c.preferredContactPeriod, 'contact.preferredContactPeriod', L.PERIODS, false)
  };

  var p = v.obj(topo.privacy, 'privacy', ['privacyNoticeVersion', 'acknowledged', 'marketingConsent'], ['privacyNoticeVersion', 'acknowledged']);
  if (typeof p.privacyNoticeVersion !== 'string' || !/^[A-Za-z0-9._-]{1,40}$/.test(p.privacyNoticeVersion)) v.erro('privacy.privacyNoticeVersion', 'valor_invalido');
  if (p.acknowledged !== true) v.erro('privacy.acknowledged', 'obrigatorio');
  if (p.marketingConsent !== undefined && p.marketingConsent !== null && p.marketingConsent !== false) v.erro('privacy.marketingConsent', 'nao_oferecido');

  if (Object.keys(v.erros).length) throw new ErroValidacao_(v.erros);
  return { idempotencyKey: chave, source: source, scenario: cenario, contact: contato,
    privacy: { clientNoticeVersion: p.privacyNoticeVersion, requestedContactChannel: canal }, sensitiveContentSuspected: v.suspeita() };
}

function ramo_(v, entrada, bruto) {
  var L = LISTAS, c = 'scenario.branchSpecificData', b;
  if (entrada === 'decision_support') {
    b = v.obj(bruto || {}, c, ['evaluate'], ['evaluate']);
    return { evaluate: v.lista(b.evaluate, c + '.evaluate', L.EVALUATE, 3, true) };
  }
  if (entrada === 'visual_communication') {
    b = v.obj(bruto || {}, c, ['deliverable', 'purpose', 'audience', 'referenceLevel'], ['deliverable', 'purpose', 'audience', 'referenceLevel']);
    return { deliverable: v.enm(b.deliverable, c + '.deliverable', L.DELIVERABLES, true), purpose: v.enm(b.purpose, c + '.purpose', L.PURPOSES, true),
      audience: v.enm(b.audience, c + '.audience', L.VISUAL_AUDIENCE, true), referenceLevel: v.enm(b.referenceLevel, c + '.referenceLevel', L.REFERENCE_LEVELS, true) };
  }
  if (entrada === 'ai_decision_engineering') {
    b = v.obj(bruto || {}, c, ['aiSituation', 'difficulties', 'areas', 'peopleRange', 'affectedProcess'], ['aiSituation', 'peopleRange', 'affectedProcess']);
    var sit = v.enm(b.aiSituation, c + '.aiSituation', L.AI_SITUATIONS, true);
    return { aiSituation: sit, difficulties: sit === 'already_using' ? v.lista(b.difficulties, c + '.difficulties', L.AI_DIFFICULTIES, L.AI_DIFFICULTIES.length, true) : [],
      areas: v.lista(b.areas, c + '.areas', L.AI_AREAS, L.AI_AREAS.length, true), peopleRange: v.enm(b.peopleRange, c + '.peopleRange', L.PEOPLE, true),
      affectedProcess: v.enm(b.affectedProcess, c + '.affectedProcess', L.PROCESSES, true) };
  }
  if (entrada === 'other_or_unsure') {
    b = v.obj(bruto || {}, c, ['decisionNeeded'], ['decisionNeeded']);
    return { decisionNeeded: v.texto(b.decisionNeeded, c + '.decisionNeeded', LIMITES.shortText, true, 10) };
  }
  if (entrada === 'underperforming') { v.obj(bruto || {}, c, []); }
  return {};
}

function validarDetalhes_(dados) {
  var v = novoValidador_();
  var t = v.texto(dados.additionalInfo, 'additionalInfo', LIMITES.additionalInfo, true, 5);
  if (Object.keys(v.erros).length) throw new ErroValidacao_(v.erros);
  return { additionalInfo: t, sensitiveContentSuspected: v.suspeita() };
}
