/**
 * Validação estrita e normalização da submissão (porta de servidor/regras_leads.py).
 * O navegador nunca é fonte de confiança: tudo é revalidado aqui. Códigos internos são estáveis.
 * UF, município e país são conferidos contra a tabela do IBGE gerada no projeto (Municipios.gs); nada é consultado na internet.
 */
var SITUACOES_ = {
  obra_contrato_dificuldade: ['Obra ou contrato com dificuldade', { before_start: 'Antes de iniciar', running: 'Em execução', stopped: 'Paralisado', closing: 'Encerramento', unknown: 'Ainda não sei' }],
  atraso_custo_margem: ['Atraso, custo, produtividade ou perda de margem', { deadline: 'Prazo', cost: 'Custo', margin: 'Margem', penalty: 'Multa', production: 'Produção', measurement: 'Medição', combination: 'Combinação', unknown: 'Ainda não sei' }],
  projeto_terreno_propostas: ['Projeto, terreno ou propostas para comparar', { feasibility: 'Viabilidade', project: 'Projeto', land: 'Terreno', contracting: 'Contratação', comparison: 'Comparação', unknown: 'Ainda não sei' }],
  planejamento_recursos_recuperacao: ['Planejamento, recursos ou recuperação', { plan: 'Planejar', recover_deadline: 'Recuperar prazo', organize_resources: 'Organizar recursos', integrate_fronts: 'Integrar frentes', unknown: 'Ainda não sei' }],
  medicao_alteracao_documentacao: ['Medição, alteração contratual ou documentação', { measurement: 'Medição', scope: 'Escopo', change: 'Alteração', approval: 'Aprovação', databook: 'Data book', unknown: 'Ainda não sei' }],
  vistoria_recebimento_conferencia: ['Vistoria, recebimento ou conferência final', { property: 'Imóvel', service: 'Serviço', work: 'Obra', documentation: 'Documentação', handover: 'Entrega', unknown: 'Ainda não sei' }],
  comunicacao_ia_3d: ['Comunicação técnica com Inteligência Artificial, vídeo ou 3D', { explain: 'Explicar', present: 'Apresentar', sell: 'Vender', train: 'Treinar', compare: 'Comparar', unknown: 'Ainda não sei' }],
  outra_nao_sei: ['Outra situação / ainda não sei', { understand: 'Entender', compare: 'Comparar', plan: 'Planejar', verify: 'Verificar', decide: 'Decidir', unknown: 'Ainda não sei' }]
};
var AUDIENCIA_ = { company_manager: 'Empresa / gestor', contractor: 'Empreiteira / prestador', owner_investor: 'Proprietário / investidor', technical_team: 'Profissional ou equipe técnica', other: 'Outro perfil' };
var PAPEIS_ = { decides: 'Decido ou aprovo a contratação', recommends: 'Participo da análise e recomendo', gathering: 'Estou levantando informações', referring: 'Estou indicando a situação', other_unsure: 'Outro / ainda não sei' };
var URGENCIAS_ = { immediate: 'Imediata', this_week: 'Nesta semana', this_month: 'Neste mês', undefined: 'Sem urgência definida' };
var DOCUMENTOS_ = { yes: 'Sim', partial: 'Parcialmente', no: 'Não', unknown: 'Ainda não sei' };
var PERIODOS_ = { morning: 'Manhã', afternoon: 'Tarde', evening: 'Noite', any: 'Indiferente' };
var CONSEQUENCIAS_ = { penalty: 'Multa ou penalidade', stoppage: 'Paralisação ou atraso', margin_cash_loss: 'Perda de margem ou caixa', technical_quality_risk: 'Risco técnico ou de qualidade',
  contract_conflict: 'Conflito contratual', decision_without_information: 'Decisão sem informação suficiente', other: 'Outra' };
var FAIXAS_ = { up_to_100k: 'Até R$ 100 mil', '100k_to_1m': 'R$ 100 mil a R$ 1 milhão', '1m_to_10m': 'R$ 1 a 10 milhões', '10m_to_50m': 'R$ 10 a 50 milhões',
  above_50m: 'Acima de R$ 50 milhões', undisclosed: 'Prefiro não informar', unknown: 'Ainda não sei' };
// Múltipla escolha: opções que não combinam com as outras da mesma pergunta (ex.: "Ainda não sei")
var EXCLUSIVAS_ = { situationCodes: ['outra_nao_sei'], urgencies: ['undefined'], documents: ['unknown'], estimatedRanges: ['undisclosed', 'unknown'], contactPeriods: ['any'] };
var LISTAS = {
  CHANNELS: ['whatsapp', 'email'],
  ORIGINS: ['hero', 'industria', 'produtos', 'metodo', 'sobre', 'header', 'final', 'direto'],
  PRODUCTS: ['P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11', 'P12', 'IA-1', 'IA-2', 'CV01'],
  DEVICES: ['mobile', 'tablet', 'desktop', 'unknown']
};
var LIMITES = { narrative: 1200, narrativeMin: 10, name: 120, organization: 120, cityForeign: 80, region: 80 };

function ErroValidacao_(campos) { this.campos = campos; }

function chaves_(o) { return Object.keys(o); }

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
    /** Múltipla escolha: lista de códigos permitidos, sem repetição e sem misturar opção exclusiva com outras. Devolve na ordem da lista permitida. */
    lista: function (valor, caminho, permitidos, obrigatorio, exclusivas) {
      if (valor === null || valor === undefined || (Array.isArray(valor) && !valor.length)) { if (obrigatorio) v.erro(caminho, 'obrigatorio'); return []; }
      if (!Array.isArray(valor)) { v.erro(caminho, 'tipo'); return []; }
      if (valor.length > 2 * permitidos.length) { v.erro(caminho, 'limite_de_selecoes'); return []; }
      for (var i = 0; i < valor.length; i++) {
        if (typeof valor[i] !== 'string' || permitidos.indexOf(valor[i]) < 0) { v.erro(caminho, 'valor_invalido'); return []; }
      }
      var escolhidos = permitidos.filter(function (k) { return valor.indexOf(k) >= 0; });
      if (escolhidos.length > 1 && (exclusivas || []).some(function (x) { return escolhidos.indexOf(x) >= 0; })) { v.erro(caminho, 'opcoes_incompativeis'); return []; }
      return escolhidos;
    },
    texto: function (valor, caminho, maximo, obrigatorio, minimo) {
      if (valor === null || valor === undefined || valor === '') { if (obrigatorio) v.erro(caminho, 'obrigatorio'); return ''; }
      if (typeof valor !== 'string') { v.erro(caminho, 'tipo'); return ''; }
      var t = limparTexto_(valor);
      if (t.length > maximo) { v.erro(caminho, 'tamanho'); return ''; }
      var cpf = /\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/, cnpj = /\b\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}\b/;
      if (cpf.test(t) || cnpj.test(t)) { suspeita = true; t = t.replace(cpf, '[removido]').replace(cnpj, '[removido]'); }
      if (/<\s*\/?\s*[A-Za-z!][^>]*>/.test(t)) { v.erro(caminho, 'html_nao_permitido'); return ''; }
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

/** Nome oficial do município se o código pertence à UF; senão null. A tabela vem de Municipios.gs (IBGE). */
function nomeDoMunicipio_(uf, codigo) {
  var tabela = MUNICIPIOS_[uf];
  if (!tabela || typeof codigo !== 'string' || !/^\d{7}$/.test(codigo) || codigo.indexOf(UFS_IBGE_[uf]) !== 0) return null;
  var corpo = '|' + tabela, i = corpo.indexOf('|' + codigo + ':');
  if (i < 0) return null;
  var ini = i + 9, fim = corpo.indexOf('|', ini);
  return corpo.substring(ini, fim < 0 ? corpo.length : fim);
}

function localizacao_(v, bruto) {
  var caminho = 'scenario.location', tipo = bruto && typeof bruto === 'object' ? bruto.type : null;
  var vazio = { type: '', countryCode: '', countryName: '', stateCode: '', stateName: '', cityCode: '', cityName: '', foreignRegion: '' };
  if (tipo === 'brazil') {
    var b = v.obj(bruto, caminho, ['type', 'countryCode', 'stateCode', 'cityCode', 'cityName'], ['stateCode', 'cityCode']);
    v.enm(b.countryCode, caminho + '.countryCode', ['BR'], false);
    var uf = v.enm(b.stateCode, caminho + '.stateCode', chaves_(UFS_IBGE_), true), nome = '', codigo = '';
    if (uf) {
      var oficial = nomeDoMunicipio_(uf, b.cityCode);
      if (oficial === null) v.erro(caminho + '.cityCode', 'valor_invalido');   // inclui município de outra UF
      else {
        codigo = b.cityCode; nome = oficial;
        if (b.cityName !== undefined && b.cityName !== null && b.cityName !== '' && (typeof b.cityName !== 'string' || b.cityName.normalize('NFC').trim() !== oficial)) v.erro(caminho + '.cityName', 'valor_invalido');
      }
    }
    return { type: 'brazil', countryCode: 'BR', countryName: 'Brasil', stateCode: uf || '', stateName: uf ? UFS_NOMES_[uf] : '', cityCode: codigo, cityName: nome, foreignRegion: '' };
  }
  if (tipo === 'international') {
    var e = v.obj(bruto, caminho, ['type', 'countryCode', 'cityName', 'foreignRegion'], ['countryCode', 'cityName']);
    var pais = v.enm(e.countryCode, caminho + '.countryCode', chaves_(PAISES_), true);
    if (pais === 'BR') v.erro(caminho + '.countryCode', 'use_modo_brasil');
    return { type: 'international', countryCode: pais || '', countryName: pais ? PAISES_[pais] : '', stateCode: '', stateName: '', cityCode: '',
      cityName: v.texto(e.cityName, caminho + '.cityName', LIMITES.cityForeign, true, 1), foreignRegion: v.texto(e.foreignRegion, caminho + '.foreignRegion', LIMITES.region, false) };
  }
  v.erro(caminho + '.type', tipo ? 'valor_invalido' : 'obrigatorio');
  return vazio;
}

/** True se o tempo informado é implausível para uma pessoa. */
function envioRapidoDemais_(dados) { return typeof dados.elapsedMs === 'number' && dados.elapsedMs >= 0 && dados.elapsedMs < CRIVIA.MIN_ELAPSED_MS; }

/** Valida a submissão completa. Lança ErroValidacao_. Devolve o registro normalizado (sem id nem datas). */
function validarLead_(corpo) {
  var v = novoValidador_(), L = LISTAS;
  var topo = v.obj(corpo, '$', ['idempotencyKey', 'schemaVersion', 'formVersion', 'elapsedMs', 'source', 'scenario', 'contact', 'privacy', 'website', 'turnstileToken'],
    ['idempotencyKey', 'scenario', 'contact', 'privacy']);
  var chave = topo.idempotencyKey;
  if (typeof chave !== 'string' || !/^[A-Za-z0-9-]{8,64}$/.test(chave)) v.erro('idempotencyKey', 'valor_invalido');
  if (topo.schemaVersion !== undefined && topo.schemaVersion !== CRIVIA.SCHEMA_VERSION) v.erro('schemaVersion', 'valor_invalido');
  var versaoForm = topo.formVersion;
  if (versaoForm !== undefined && versaoForm !== null && versaoForm !== '' && !(typeof versaoForm === 'string' && /^[A-Za-z0-9._-]{1,40}$/.test(versaoForm))) v.erro('formVersion', 'valor_invalido');
  var ms = topo.elapsedMs;
  if (typeof ms !== 'number' || ms !== Math.floor(ms) || ms < 0 || ms > 7 * 24 * 3600 * 1000) v.erro('elapsedMs', ms === undefined ? 'obrigatorio' : 'valor_invalido');

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
    if (x === undefined || x === null || x === '') source[k] = '';
    else if (typeof x === 'string' && /^[A-Za-z0-9._~ +-]{0,80}$/.test(x)) source[k] = x;
    else v.erro('source.' + k, 'valor_invalido');
  });

  var s = v.obj(topo.scenario, 'scenario', ['situationCodes', 'contextAnswers', 'audienceProfiles', 'decisionRole', 'location', 'narrative', 'urgencies', 'consequences', 'documents', 'estimatedRanges'],
    ['situationCodes', 'audienceProfiles', 'decisionRole', 'location', 'narrative']);
  var situacoes = v.lista(s.situationCodes, 'scenario.situationCodes', chaves_(SITUACOES_), true, EXCLUSIVAS_.situationCodes);
  // pergunta curta de cada situação marcada: { situação: resposta }. Só vale para situações marcadas e respostas daquela situação.
  // (o caminho do erro é fixo: nenhuma chave enviada pelo visitante é reproduzida na resposta)
  var contextos = [], bruto = s.contextAnswers;
  if (bruto !== undefined && bruto !== null && !(typeof bruto === 'object' && !Array.isArray(bruto) && !Object.keys(bruto).length)) {
    if (typeof bruto !== 'object' || Array.isArray(bruto)) v.erro('scenario.contextAnswers', 'tipo');
    else if (Object.keys(bruto).some(function (k) { return situacoes.indexOf(k) < 0 || typeof bruto[k] !== 'string' || !SITUACOES_[k][1].hasOwnProperty(bruto[k]); })) v.erro('scenario.contextAnswers', 'valor_invalido');
    else situacoes.forEach(function (sit) { if (bruto.hasOwnProperty(sit)) contextos.push({ situationCode: sit, answerCode: bruto[sit], answerLabel: SITUACOES_[sit][1][bruto[sit]] }); });
  }
  var perfis = v.lista(s.audienceProfiles, 'scenario.audienceProfiles', chaves_(AUDIENCIA_), true);
  var papel = v.enm(s.decisionRole, 'scenario.decisionRole', chaves_(PAPEIS_), true);
  var cenario = {
    situationCodes: situacoes, situationLabels: situacoes.map(function (x) { return SITUACOES_[x][0]; }),
    contextAnswers: contextos,
    audienceProfiles: perfis, audienceProfileLabels: perfis.map(function (x) { return AUDIENCIA_[x]; }), decisionRole: papel, decisionRoleLabel: papel ? PAPEIS_[papel] : '',
    location: localizacao_(v, s.location),
    urgencies: v.lista(s.urgencies, 'scenario.urgencies', chaves_(URGENCIAS_), false, EXCLUSIVAS_.urgencies),
    consequences: v.lista(s.consequences, 'scenario.consequences', chaves_(CONSEQUENCIAS_), false),
    documents: v.lista(s.documents, 'scenario.documents', chaves_(DOCUMENTOS_), false, EXCLUSIVAS_.documents),
    estimatedRanges: v.lista(s.estimatedRanges, 'scenario.estimatedRanges', chaves_(FAIXAS_), false, EXCLUSIVAS_.estimatedRanges),
    narrative: v.texto(s.narrative, 'scenario.narrative', LIMITES.narrative, true, LIMITES.narrativeMin)
  };

  var c = v.obj(topo.contact, 'contact', ['name', 'organization', 'preferredChannel', 'phone', 'email', 'contactPeriods'], ['name', 'preferredChannel']);
  var canal = v.enm(c.preferredChannel, 'contact.preferredChannel', L.CHANNELS, true);
  var nome = v.texto(c.name, 'contact.name', LIMITES.name, true, 2);
  if (nome && /[\d<>{}\[\]\\|^~`@#$%*=+_]/.test(nome)) v.erro('contact.name', 'valor_invalido');
  var telefone = null, email = null;
  if (c.phone !== undefined && c.phone !== null && c.phone !== '') { telefone = typeof c.phone === 'string' ? normalizarTelefone_(c.phone) : null; if (!telefone) v.erro('contact.phone', 'valor_invalido'); }
  if (c.email !== undefined && c.email !== null && c.email !== '') {
    var em = typeof c.email === 'string' ? c.email.trim() : '';
    if (emailValido_(em)) email = em.toLowerCase(); else v.erro('contact.email', 'valor_invalido');
  }
  if (canal === 'whatsapp' && !telefone && !v.erros['contact.phone']) v.erro('contact.phone', 'obrigatorio');
  if (canal === 'email' && !email && !v.erros['contact.email']) v.erro('contact.email', 'obrigatorio');
  var contato = { name: nome, organization: v.texto(c.organization, 'contact.organization', LIMITES.organization, false), preferredChannel: canal, phone: telefone || '', email: email || '',
    contactPeriods: v.lista(c.contactPeriods, 'contact.contactPeriods', chaves_(PERIODOS_), false, EXCLUSIVAS_.contactPeriods) };

  var p = v.obj(topo.privacy, 'privacy', ['privacyNoticeVersion', 'acknowledged', 'marketingConsent'], ['privacyNoticeVersion', 'acknowledged']);
  if (typeof p.privacyNoticeVersion !== 'string' || !/^[A-Za-z0-9._-]{1,40}$/.test(p.privacyNoticeVersion)) v.erro('privacy.privacyNoticeVersion', 'valor_invalido');
  if (p.acknowledged !== true) v.erro('privacy.acknowledged', 'obrigatorio');
  var marketing = p.marketingConsent === undefined ? false : p.marketingConsent;
  if (typeof marketing !== 'boolean') { v.erro('privacy.marketingConsent', 'valor_invalido'); marketing = false; }

  if (Object.keys(v.erros).length) throw new ErroValidacao_(v.erros);
  return { idempotencyKey: chave, schemaVersion: CRIVIA.SCHEMA_VERSION, formVersion: versaoForm || '', source: source, scenario: cenario, contact: contato,
    privacy: { privacyNoticeVersion: p.privacyNoticeVersion, requestedContactChannel: canal, marketingConsent: marketing }, sensitiveContentSuspected: v.suspeita() };
}

/** Complemento opcional pós-envio: três perguntas curtas de lista fechada; ao menos uma. */
function validarDetalhes_(corpo) {
  var v = novoValidador_(), L = LISTAS;
  var c = v.obj(corpo, '$', ['urgency', 'documents', 'contactPeriod']);
  var saida = { urgency: v.enm(c.urgency, 'urgency', chaves_(URGENCIAS_), false), documents: v.enm(c.documents, 'documents', chaves_(DOCUMENTOS_), false), contactPeriod: v.enm(c.contactPeriod, 'contactPeriod', chaves_(PERIODOS_), false) };
  if (!saida.urgency && !saida.documents && !saida.contactPeriod && !Object.keys(v.erros).length) v.erro('$', 'vazio');
  if (Object.keys(v.erros).length) throw new ErroValidacao_(v.erros);
  return saida;
}
