/**
 * Acesso à planilha privada "CRIVIA — Cenários recebidos pelo site". Somente este arquivo abre a planilha.
 * O ID vem de Script Properties (SPREADSHEET_ID). Nada daqui é devolvido ao navegador.
 */
function planilha_() { return SpreadsheetApp.openById(prop_('SPREADSHEET_ID')); }

function aba_(nome, cabecalhos) {
  var ss = planilha_(), a = ss.getSheetByName(nome);
  if (!a) {
    a = ss.insertSheet(nome);
    a.getRange(1, 1, 1, cabecalhos.length).setValues([cabecalhos]).setFontWeight('bold');
    a.setFrozenRows(1);
    a.getRange(2, 1, a.getMaxRows() - 1, cabecalhos.length).setNumberFormat('@');   // tudo como texto: fórmulas não são interpretadas
  }
  return a;
}

/** Executar UMA vez, manualmente, depois de configurar as Script Properties. Cria as abas e os cabeçalhos. */
function prepararPlanilha() {
  if (!configuracaoCompleta_()) throw new Error('Configure SPREADSHEET_ID, NOTIFICATION_EMAIL e PRIVACY_NOTICE_VERSION em Script Properties.');
  aba_(CRIVIA.SHEETS.CENARIOS, CABECALHOS_CENARIOS);
  aba_(CRIVIA.SHEETS.HISTORICO, CABECALHOS_HISTORICO);
  aba_(CRIVIA.SHEETS.CONSENTIMENTOS, CABECALHOS_CONSENTIMENTOS);
  aba_(CRIVIA.SHEETS.ERROS, CABECALHOS_ERROS);
  var ss = planilha_();
  ['Listas', 'Indicadores', 'Configuracao'].forEach(function (n) { if (!ss.getSheetByName(n)) ss.insertSheet(n); });
  var cfg = ss.getSheetByName(CRIVIA.SHEETS.CONFIGURACAO);
  cfg.clear();
  cfg.getRange(1, 1, 4, 2).setValues([['chave', 'valor (não sigiloso)'], ['schema_version', CRIVIA.SCHEMA_VERSION], ['score_rule_version', CRIVIA.SCORE_RULE_VERSION], ['timezone', CRIVIA.TIMEZONE]]);
  var lst = ss.getSheetByName(CRIVIA.SHEETS.LISTAS);
  lst.clear();
  var chaves = Object.keys(LISTAS);
  lst.getRange(1, 1, 1, chaves.length).setValues([chaves]).setFontWeight('bold');
  chaves.forEach(function (k, i) { lst.getRange(2, i + 1, LISTAS[k].length, 1).setValues(LISTAS[k].map(function (x) { return [x]; })); });
  return 'Planilha preparada. Confira o compartilhamento: deve estar como Restrito.';
}

function agora_() { return Utilities.formatDate(new Date(), CRIVIA.TIMEZONE, "yyyy-MM-dd'T'HH:mm:ssXXX"); }

function acrescentar_(nome, cabecalhos, linha) {
  var a = aba_(nome, cabecalhos);
  var r = a.getLastRow() + 1;
  a.getRange(r, 1, 1, linha.length).setNumberFormat('@').setValues([linha]);
  return r;
}

function procurarLinha_(coluna, valor) {
  var a = aba_(CRIVIA.SHEETS.CENARIOS, CABECALHOS_CENARIOS);
  var col = CABECALHOS_CENARIOS.indexOf(coluna) + 1;
  if (a.getLastRow() < 2) return 0;
  var achado = a.getRange(2, col, a.getLastRow() - 1, 1).createTextFinder(String(valor)).matchEntireCell(true).matchCase(true).findNext();
  return achado ? achado.getRow() : 0;
}

function codigoDaLinha_(linha) {
  var a = aba_(CRIVIA.SHEETS.CENARIOS, CABECALHOS_CENARIOS);
  return String(a.getRange(linha, CABECALHOS_CENARIOS.indexOf('public_code') + 1).getValue());
}

function codigoJaExiste_(codigo) { return procurarLinha_('public_code', codigo) > 0; }

/** Grava cenário, histórico e consentimento. Chamar somente com o LockService obtido. */
function gravarCenario_(lead, q, hashChave) {
  var codigo;
  do { codigo = gerarCodigoPublico_(); } while (codigoJaExiste_(codigo));
  var agora = agora_(), s = lead.scenario, c = lead.contact, o = lead.source;
  var junta = function (l) { return (l || []).join('|'); };
  var linha = [uuid_(), codigo, CRIVIA.SCHEMA_VERSION, agora, agora, 'new', q.priority, 'pending',
    o.landingPage, seguroParaPlanilha_(o.referrer), o.originCta, o.productHint || '', seguroParaPlanilha_(o.utmSource), seguroParaPlanilha_(o.utmMedium),
    seguroParaPlanilha_(o.utmCampaign), seguroParaPlanilha_(o.utmContent), seguroParaPlanilha_(o.utmTerm), o.deviceCategory,
    s.entryPath, s.audienceContext, s.decisionRole, s.stage || '', junta(s.issues), junta(s.consequences), s.decisionHorizon,
    seguroParaPlanilha_(s.city), s.state, s.estimatedRange || '', junta(s.availableDocuments), seguroParaPlanilha_(s.narrative),
    JSON.stringify(s.branchSpecificData), seguroParaPlanilha_(c.name), seguroParaPlanilha_(c.organization), seguroParaPlanilha_(c.roleTitle),
    c.preferredChannel, telefoneParaPlanilha_(c.phone), seguroParaPlanilha_(c.email), c.preferredContactPeriod || '', junta(q.candidateProducts),
    junta(q.missingInformation), prop_('PRIVACY_NOTICE_VERSION'), agora, false, '', '', '', '', '', '',
    hashChave, '', 'pending', JSON.stringify(q), lead.sensitiveContentSuspected ? 'true' : 'false'];
  if (linha.length !== CABECALHOS_CENARIOS.length) throw new Error('colunas_inconsistentes');
  var numero = acrescentar_(CRIVIA.SHEETS.CENARIOS, CABECALHOS_CENARIOS, linha);
  acrescentar_(CRIVIA.SHEETS.CONSENTIMENTOS, CABECALHOS_CONSENTIMENTOS, registroDeConsentimento_(lead, codigo, agora));
  acrescentar_(CRIVIA.SHEETS.HISTORICO, CABECALHOS_HISTORICO, [agora, codigo, 'created', 'schema=' + CRIVIA.SCHEMA_VERSION + ';priority=' + q.priority]);
  return { codigo: codigo, linha: numero };
}

function gravarDetalhes_(codigo, detalhes) {
  var linha = procurarLinha_('public_code', codigo);
  if (!linha) return false;
  var a = aba_(CRIVIA.SHEETS.CENARIOS, CABECALHOS_CENARIOS);
  a.getRange(linha, CABECALHOS_CENARIOS.indexOf('additional_info') + 1).setNumberFormat('@').setValue(seguroParaPlanilha_(detalhes.additionalInfo));
  a.getRange(linha, CABECALHOS_CENARIOS.indexOf('updated_at') + 1).setValue(agora_());
  acrescentar_(CRIVIA.SHEETS.HISTORICO, CABECALHOS_HISTORICO, [agora_(), codigo, 'details_added', detalhes.sensitiveContentSuspected ? 'sensitive_suspected' : '']);
  return true;
}

function atualizarStatusNotificacao_(linha, status) {
  aba_(CRIVIA.SHEETS.CENARIOS, CABECALHOS_CENARIOS).getRange(linha, CABECALHOS_CENARIOS.indexOf('notification_status') + 1).setValue(status);
}

/** Erro operacional mínimo: etapa e código, nunca o corpo da submissão. */
function registrarErro_(etapa, codigo) {
  try { acrescentar_(CRIVIA.SHEETS.ERROS, CABECALHOS_ERROS, [agora_(), etapa, String(codigo).slice(0, 120)]); } catch (e) { console.error('erro_operacional:' + etapa); }
}
