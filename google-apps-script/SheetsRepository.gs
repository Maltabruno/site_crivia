/**
 * Acesso à planilha privada "CRIVIA — Cenários recebidos pelo site". Somente este arquivo abre a planilha.
 * O ID vem de Script Properties (SPREADSHEET_ID). Nada daqui é devolvido ao navegador.
 * Abas: Leads (uma linha por cenário), Respostas (uma linha por opção marcada), Config (não sigilosa, só leitura humana) e Audit (eventos mínimos, sem dados pessoais).
 */
function planilha_() { return SpreadsheetApp.openById(prop_('SPREADSHEET_ID')); }

function aba_(nome, cabecalhos) {
  var ss = planilha_(), a = ss.getSheetByName(nome);
  if (!a) {
    a = ss.insertSheet(nome);
    a.getRange(1, 1, 1, cabecalhos.length).setValues([cabecalhos]).setFontWeight('bold');
    a.setFrozenRows(1);
    a.getRange(2, 1, a.getMaxRows() - 1, cabecalhos.length).setNumberFormat('@');   // tudo como texto: fórmulas, telefones e códigos não são reinterpretados
  }
  return a;
}

/** Executar UMA vez, manualmente, depois de configurar as Script Properties. Cria as abas, filtros, validação de status e proteções. */
function prepararPlanilha() {
  if (!configuracaoCompleta_()) throw new Error('Configure SPREADSHEET_ID, NOTIFICATION_EMAIL e PRIVACY_NOTICE_VERSION em Script Properties.');
  var leads = aba_(CRIVIA.SHEETS.LEADS, CABECALHOS_LEADS);
  aba_(CRIVIA.SHEETS.ANSWERS, CABECALHOS_RESPOSTAS);
  aba_(CRIVIA.SHEETS.AUDIT, CABECALHOS_AUDIT);
  var ss = planilha_();
  var col = function (nome) { return CABECALHOS_LEADS.indexOf(nome) + 1; };
  // filtro + validação de dados do status
  if (!leads.getFilter()) leads.getRange(1, 1, leads.getMaxRows(), CABECALHOS_LEADS.length).createFilter();
  leads.getRange(2, col('status'), leads.getMaxRows() - 1, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(STATUS_INICIAIS, true).setAllowInvalid(false).build());
  // proteção com aviso: cabeçalho e colunas técnicas (quem edita é alertado antes; proprietários continuam podendo corrigir)
  leads.getRange(1, 1, 1, CABECALHOS_LEADS.length).protect().setDescription('Cabeçalho do modelo').setWarningOnly(true);
  var primeiraTecnica = col('priority');
  leads.getRange(2, primeiraTecnica, leads.getMaxRows() - 1, CABECALHOS_LEADS.length - primeiraTecnica + 1).protect().setDescription('Colunas técnicas').setWarningOnly(true);
  // Config: somente valores não sigilosos (segredos ficam em Script Properties)
  var cfg = ss.getSheetByName(CRIVIA.SHEETS.CONFIG) || ss.insertSheet(CRIVIA.SHEETS.CONFIG);
  cfg.clear();
  cfg.getRange(1, 1, 8, 2).setValues([['chave', 'valor (não sigiloso)'], ['schema_version', CRIVIA.SCHEMA_VERSION], ['score_rule_version', CRIVIA.SCORE_RULE_VERSION],
    ['timezone', CRIVIA.TIMEZONE], ['privacy_notice_version', prop_('PRIVACY_NOTICE_VERSION')], ['legal_basis', CRIVIA.LEGAL_BASIS_PLACEHOLDER],
    ['retention_policy', prop_('LEAD_RETENTION_POLICY_ID') || '[DEFINIR_PRAZO_DE_RETENCAO]'], ['locations_source', 'IBGE (ver Municipios.gs)']]);
  return 'Planilha preparada. Confira o compartilhamento: deve estar como Restrito (nunca "qualquer pessoa com o link").';
}

function agora_() { return Utilities.formatDate(new Date(), CRIVIA.TIMEZONE, "yyyy-MM-dd'T'HH:mm:ssXXX"); }

function acrescentar_(nome, cabecalhos, linha) {
  var a = aba_(nome, cabecalhos);
  var r = a.getLastRow() + 1;
  a.getRange(r, 1, 1, linha.length).setNumberFormat('@').setValues([linha]);
  return r;
}

function procurarLinha_(coluna, valor) {
  var a = aba_(CRIVIA.SHEETS.LEADS, CABECALHOS_LEADS);
  var col = CABECALHOS_LEADS.indexOf(coluna) + 1;
  if (a.getLastRow() < 2) return 0;
  var achado = a.getRange(2, col, a.getLastRow() - 1, 1).createTextFinder(String(valor)).matchEntireCell(true).matchCase(true).findNext();
  return achado ? achado.getRow() : 0;
}

function codigoDaLinha_(linha) {
  var a = aba_(CRIVIA.SHEETS.LEADS, CABECALHOS_LEADS);
  return String(a.getRange(linha, 1).getValue());
}

function codigoJaExiste_(codigo) { return procurarLinha_('submission_id', codigo) > 0; }

/** Registro de auditoria mínimo: sem relato, telefone ou e-mail. */
function auditar_(submissionId, evento, ator, resultado) {
  try { acrescentar_(CRIVIA.SHEETS.AUDIT, CABECALHOS_AUDIT, [agora_(), submissionId || '', evento, ator || 'sistema', resultado || 'ok']); }
  catch (e) { console.error('audit:' + evento); }
}

/** Grava o cenário. Chamar somente com o LockService obtido. */
function gravarCenario_(lead, q, hashChave) {
  var codigo;
  do { codigo = gerarCodigoPublico_(); } while (codigoJaExiste_(codigo));
  var agora = agora_(), s = lead.scenario, c = lead.contact, o = lead.source, loc = s.location, p = lead.privacy;
  var texto = seguroParaPlanilha_;
  var dias = Number(prop_('UNQUALIFIED_LEAD_RETENTION_DAYS'));
  var revisao = dias > 0 ? Utilities.formatDate(new Date(Date.now() + dias * 86400000), CRIVIA.TIMEZONE, 'yyyy-MM-dd') : '';   // sem prazo aprovado, fica vazio
  var junta = function (lista) { return lista.join(' | '); };   // múltipla escolha: códigos/rótulos na mesma célula; a aba Respostas traz uma linha por opção
  var linha = [codigo, agora, agora, 'Novo', junta(s.situationCodes), junta(s.situationLabels),
    junta(s.contextAnswers.map(function (c) { return 'ctx_' + c.situationCode; })), junta(s.contextAnswers.map(function (c) { return c.answerCode; })), junta(s.contextAnswers.map(function (c) { return c.answerLabel; })), junta(s.audienceProfiles), junta(s.audienceProfileLabels), s.decisionRole, s.decisionRoleLabel,
    loc.type, loc.countryCode, texto(loc.countryName), loc.stateCode, texto(loc.stateName), loc.cityCode, texto(loc.cityName), texto(loc.foreignRegion), texto(s.narrative),
    texto(c.name), texto(c.organization), c.preferredChannel, telefoneParaPlanilha_(c.phone), texto(c.email), prop_('PRIVACY_NOTICE_VERSION'), agora,
    CRIVIA.LEGAL_BASIS_PLACEHOLDER, p.marketingConsent ? 'true' : 'false', p.marketingConsent ? agora : '',
    o.landingPage, o.originCta, texto(o.utmSource), texto(o.utmMedium), texto(o.utmCampaign), texto(o.utmContent), texto(o.utmTerm), texto(o.referrer),
    junta(s.urgencies), junta(s.documents), junta(c.contactPeriods), junta(s.consequences), junta(s.estimatedRanges), '', '', revisao, '',
    q.priority, q.candidateProducts.join('|'), q.missingInformation.join('|'), hashChave, 'pending', lead.formVersion, CRIVIA.SCHEMA_VERSION,
    lead.sensitiveContentSuspected ? 'true' : 'false', JSON.stringify(q)];
  if (linha.length !== CABECALHOS_LEADS.length) throw new Error('colunas_inconsistentes');
  var numero = acrescentar_(CRIVIA.SHEETS.LEADS, CABECALHOS_LEADS, linha);
  gravarRespostas_(codigo, respostas_(lead));
  auditar_(codigo, 'created', 'site', 'schema=' + CRIVIA.SCHEMA_VERSION + ';priority=' + q.priority);
  return { codigo: codigo, linha: numero };
}

/** Respostas de lista fechada em formato "longo": [pergunta, código, rótulo, posição] por opção marcada. Só códigos e rótulos fixos (nada digitado). */
function respostas_(lead) {
  var s = lead.scenario, c = lead.contact, linhas = [];
  var add = function (pergunta, codigos, rotulo) { codigos.forEach(function (cod, i) { linhas.push([pergunta, cod, rotulo(cod), i + 1]); }); };
  add('situation', s.situationCodes, function (x) { return SITUACOES_[x][0]; });
  s.contextAnswers.forEach(function (c) { add('context:' + c.situationCode, [c.answerCode], function () { return c.answerLabel; }); });   // uma pergunta por situação marcada
  add('audience_profile', s.audienceProfiles, function (x) { return AUDIENCIA_[x]; });
  add('decision_role', [s.decisionRole], function (x) { return PAPEIS_[x]; });
  add('urgency', s.urgencies, function (x) { return URGENCIAS_[x]; });
  add('consequence', s.consequences, function (x) { return CONSEQUENCIAS_[x]; });
  add('documents', s.documents, function (x) { return DOCUMENTOS_[x]; });
  add('estimated_range', s.estimatedRanges, function (x) { return FAIXAS_[x]; });
  add('contact_period', c.contactPeriods, function (x) { return PERIODOS_[x]; });
  return linhas;
}

function gravarRespostas_(codigo, linhas) {
  if (!linhas.length) return;
  var a = aba_(CRIVIA.SHEETS.ANSWERS, CABECALHOS_RESPOSTAS), r = a.getLastRow() + 1;
  var valores = linhas.map(function (l) { return [codigo, l[0], l[1], l[2], String(l[3])]; });
  a.getRange(r, 1, valores.length, CABECALHOS_RESPOSTAS.length).setNumberFormat('@').setValues(valores);
}

/** Complemento opcional: atualiza o MESMO registro pelo identificador público (nunca pelo número da linha). */
function gravarDetalhes_(codigo, d) {
  var linha = procurarLinha_('submission_id', codigo);
  if (!linha) return false;
  var a = aba_(CRIVIA.SHEETS.LEADS, CABECALHOS_LEADS);
  var col = function (n) { return CABECALHOS_LEADS.indexOf(n) + 1; };
  if (d.urgency) a.getRange(linha, col('optional_urgency')).setNumberFormat('@').setValue(d.urgency);
  if (d.documents) a.getRange(linha, col('optional_documents')).setNumberFormat('@').setValue(d.documents);
  if (d.contactPeriod) a.getRange(linha, col('optional_contact_period')).setNumberFormat('@').setValue(d.contactPeriod);
  a.getRange(linha, col('updated_at')).setValue(agora_());
  auditar_(codigo, 'details_added', 'site', 'ok');
  return true;
}

function atualizarStatusNotificacao_(linha, status) {
  aba_(CRIVIA.SHEETS.LEADS, CABECALHOS_LEADS).getRange(linha, CABECALHOS_LEADS.indexOf('notification_status') + 1).setValue(status);
}

/** Erro operacional mínimo: etapa e código, nunca o corpo da submissão. */
function registrarErro_(etapa, codigo) { auditar_('', 'error:' + etapa, 'sistema', String(codigo).slice(0, 120)); }

/**
 * Rotina de retenção (agendar com gatilho de tempo SOMENTE depois de aprovada a política): apenas SINALIZA registros com
 * retention_review_at vencido no Audit. Não apaga nada: exclusão/anonimização é decisão humana conforme a política aprovada.
 */
function sinalizarRetencaoVencida() {
  var a = aba_(CRIVIA.SHEETS.LEADS, CABECALHOS_LEADS), n = a.getLastRow();
  if (n < 2) return 0;
  var hoje = Utilities.formatDate(new Date(), CRIVIA.TIMEZONE, 'yyyy-MM-dd'), col = CABECALHOS_LEADS.indexOf('retention_review_at');
  var linhas = a.getRange(2, 1, n - 1, CABECALHOS_LEADS.length).getValues(), vencidos = 0;
  linhas.forEach(function (l) {
    var data = String(l[col] || '');
    if (data && data <= hoje && !l[CABECALHOS_LEADS.indexOf('deletion_or_anonymization_at')]) { vencidos++; auditar_(l[0], 'retention_review_due', 'rotina', 'pendente'); }
  });
  return vencidos;
}
