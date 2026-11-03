/**
 * Testes de unidade que NÃO tocam a planilha de produção (só validação, classificação e segurança em memória).
 * Executar `rodarTestes` no editor do Apps Script. Testes de gravação exigem uma planilha de TESTE separada
 * (configure SPREADSHEET_ID dela em um projeto de teste; nunca rode contra a planilha de produção).
 */
function leadValido_() {
  return { idempotencyKey: 'abc12345-test', schemaVersion: 3, formVersion: 'form-3', elapsedMs: 45000,
    source: { originCta: 'hero', productHint: 'P06', deviceCategory: 'desktop' },
    scenario: { situationCodes: ['obra_contrato_dificuldade'], contextAnswers: { obra_contrato_dificuldade: 'running' }, audienceProfiles: ['contractor'], decisionRole: 'decides',
      location: { type: 'brazil', countryCode: 'BR', stateCode: 'MG', cityCode: '3106200', cityName: 'Belo Horizonte' },
      narrative: 'A obra está atrasada e precisamos decidir como recuperar o prazo sem perder a margem do contrato.',
      urgencies: ['this_week'], consequences: ['penalty', 'stoppage'], documents: ['partial'], estimatedRanges: ['1m_to_10m'] },
    contact: { name: 'Maria Souza', organization: 'Construtora X', preferredChannel: 'email', email: 'maria@exemplo.com.br', contactPeriods: ['morning'] },
    privacy: { privacyNoticeVersion: 'minuta-0', acknowledged: true, marketingConsent: false }, website: '' };
}
function afirma_(cond, msg) { if (!cond) throw new Error('FALHOU: ' + msg); }
function falha_(fn) { try { fn(); } catch (e) { return e instanceof ErroValidacao_ ? e.campos : null; } return null; }

function rodarTestes() {
  var r = [];
  var t = function (nome, fn) { try { fn(); r.push('ok   ' + nome); } catch (e) { r.push('ERRO ' + nome + ' — ' + e.message); } };
  t('lead válido (Brasil) normaliza e classifica', function () {
    var l = validarLead_(leadValido_()), q = enquadrar_(l);
    afirma_(l.contact.email === 'maria@exemplo.com.br', 'email'); afirma_(q.priority === 'A', 'prioridade ' + q.priority); afirma_(q.candidateProducts.indexOf('P01') >= 0, 'P01');
    afirma_(l.scenario.location.stateName === 'Minas Gerais' && l.scenario.location.cityName === 'Belo Horizonte', 'local oficial');
  });
  t('exterior válido não carrega campos do Brasil', function () {
    var d = leadValido_(); d.scenario.location = { type: 'international', countryCode: 'PT', cityName: 'Lisboa', foreignRegion: 'Lisboa' };
    var l = validarLead_(d); afirma_(l.scenario.location.countryName === 'Portugal' && l.scenario.location.stateCode === '' && l.scenario.location.cityCode === '', 'exterior');
    d.scenario.location.stateCode = 'SP'; afirma_(falha_(function () { validarLead_(d); })['scenario.location.stateCode'], 'resíduo recusado');
  });
  t('cidade de outra UF ou adulterada é recusada', function () {
    var d = leadValido_(); d.scenario.location.stateCode = 'SP'; afirma_(falha_(function () { validarLead_(d); })['scenario.location.cityCode'], 'outra UF');
    d = leadValido_(); d.scenario.location.cityCode = '9999999'; afirma_(falha_(function () { validarLead_(d); })['scenario.location.cityCode'], 'inexistente');
    d = leadValido_(); d.scenario.location.cityName = 'Cidade Inventada'; afirma_(falha_(function () { validarLead_(d); })['scenario.location.cityName'], 'nome');
  });
  t('país inválido e Brasil no modo exterior', function () {
    var d = leadValido_(); d.scenario.location = { type: 'international', countryCode: 'ZZ', cityName: 'X' }; afirma_(falha_(function () { validarLead_(d); })['scenario.location.countryCode'], 'ZZ');
    d.scenario.location.countryCode = 'BR'; afirma_(falha_(function () { validarLead_(d); })['scenario.location.countryCode'] === 'use_modo_brasil', 'BR');
  });
  t('enum inválido e resposta de outra situação recusados', function () {
    var d = leadValido_(); d.scenario.situationCodes = ['xx']; afirma_(falha_(function () { validarLead_(d); })['scenario.situationCodes'], 'situação');
    d = leadValido_(); d.scenario.contextAnswers = { obra_contrato_dificuldade: 'deadline' }; afirma_(falha_(function () { validarLead_(d); })['scenario.contextAnswers'], 'contexto');
    d = leadValido_(); d.scenario.contextAnswers = { atraso_custo_margem: 'cost' }; afirma_(falha_(function () { validarLead_(d); })['scenario.contextAnswers'], 'situação não marcada');
  });
  t('campo desconhecido recusado', function () { var d = leadValido_(); d.extra = 1; afirma_(falha_(function () { validarLead_(d); })['$.extra'], 'extra'); });
  t('relato: limite, HTML e quebras de linha', function () {
    var d = leadValido_(); d.scenario.narrative = new Array(1202).join('a'); afirma_(falha_(function () { validarLead_(d); })['scenario.narrative'], 'tamanho');
    d = leadValido_(); d.scenario.narrative = '<script>alert(1)</script> atraso de obra'; afirma_(falha_(function () { validarLead_(d); })['scenario.narrative'] === 'html_nao_permitido', 'html');
    d = leadValido_(); d.scenario.narrative = 'Linha um com texto suficiente.\n\nLinha dois continua aqui.'; afirma_(validarLead_(d).scenario.narrative.indexOf('\n\n') > 0, 'quebras');
  });
  t('privacidade exige ciência; marketing é opcional', function () {
    var d = leadValido_(); d.privacy.acknowledged = false; afirma_(falha_(function () { validarLead_(d); })['privacy.acknowledged'], 'ack');
    d = leadValido_(); d.privacy.marketingConsent = true; afirma_(validarLead_(d).privacy.marketingConsent === true, 'mkt');
  });
  t('telefone E.164 e canal preferencial', function () {
    afirma_(normalizarTelefone_('(31) 99999-1234') === '+5531999991234', 'br'); afirma_(normalizarTelefone_('+351912345678') === '+351912345678', 'intl'); afirma_(normalizarTelefone_('123') === null, 'curto');
    var d = leadValido_(); d.contact.preferredChannel = 'whatsapp'; delete d.contact.email; afirma_(falha_(function () { validarLead_(d); })['contact.phone'], 'whatsapp exige telefone');
  });
  t('perguntas opcionais: listas fechadas e todas opcionais', function () {
    var l = validarLead_(leadValido_()); afirma_(l.scenario.urgencies[0] === 'this_week' && l.scenario.consequences.length === 2 && l.contact.contactPeriods[0] === 'morning', 'lidas');
    var d = leadValido_(); delete d.scenario.urgencies; delete d.scenario.consequences; delete d.scenario.documents; delete d.scenario.estimatedRanges; delete d.contact.contactPeriods;
    var s = validarLead_(d).scenario; afirma_(!s.urgencies.length && !s.consequences.length && !s.documents.length && !s.estimatedRanges.length, 'opcionais');
    d = leadValido_(); d.scenario.urgencies = ['ontem']; afirma_(falha_(function () { validarLead_(d); })['scenario.urgencies'], 'urgência');
    d = leadValido_(); d.scenario.urgencies = 'this_week'; afirma_(falha_(function () { validarLead_(d); })['scenario.urgencies'], 'tipo');
  });
  t('múltipla escolha: várias opções, ordem da lista, sem repetição, sem limite em "todas"', function () {
    var d = leadValido_(); d.scenario.situationCodes = ['atraso_custo_margem', 'obra_contrato_dificuldade', 'atraso_custo_margem']; d.scenario.contextAnswers = { atraso_custo_margem: 'cost', obra_contrato_dificuldade: 'stopped' };
    d.scenario.audienceProfiles = ['technical_team', 'contractor']; d.scenario.urgencies = ['this_month', 'immediate']; d.scenario.documents = ['partial', 'yes'];
    d.scenario.consequences = chaves_(CONSEQUENCIAS_); d.contact.contactPeriods = ['evening', 'morning'];
    var l = validarLead_(d), s = l.scenario;
    afirma_(s.situationCodes.join() === 'obra_contrato_dificuldade,atraso_custo_margem', 'situações ' + s.situationCodes.join());
    afirma_(s.audienceProfiles.join() === 'contractor,technical_team' && s.urgencies.join() === 'immediate,this_month' && s.documents.join() === 'yes,partial', 'ordem');
    afirma_(s.consequences.length === 7 && l.contact.contactPeriods.join() === 'morning,evening', 'todas');
    var q = enquadrar_(l); afirma_(q.candidateProducts.join() === 'P01,P08,P07', 'produtos ' + q.candidateProducts.join()); afirma_(q.timingScore === 2 && q.readinessScore === 2, 'melhor opção');
    afirma_(l.scenario.contextAnswers.map(function (c) { return c.situationCode + ':' + c.answerCode; }).join() === 'obra_contrato_dificuldade:stopped,atraso_custo_margem:cost', 'contexto por situação');
    d.scenario.contextAnswers = { projeto_terreno_propostas: 'land' }; afirma_(falha_(function () { validarLead_(d); })['scenario.contextAnswers'], 'contexto de situação não marcada');
    d = leadValido_(); d.scenario.situationCodes = []; afirma_(falha_(function () { validarLead_(d); })['scenario.situationCodes'] === 'obrigatorio', 'situação obrigatória');
    d = leadValido_(); d.scenario.audienceProfiles = []; afirma_(falha_(function () { validarLead_(d); })['scenario.audienceProfiles'] === 'obrigatorio', 'perfil obrigatório');
  });
  t('opções exclusivas não combinam com outras', function () {
    [['urgencies', ['undefined', 'immediate']], ['documents', ['unknown', 'yes']], ['estimatedRanges', ['undisclosed', 'unknown']]].forEach(function (par) {
      var d = leadValido_(); d.scenario[par[0]] = par[1]; afirma_(falha_(function () { validarLead_(d); })['scenario.' + par[0]] === 'opcoes_incompativeis', par[0]);
    });
    var d = leadValido_(); d.contact.contactPeriods = ['any', 'morning']; afirma_(falha_(function () { validarLead_(d); })['contact.contactPeriods'], 'período');
    d = leadValido_(); d.scenario.documents = ['unknown']; afirma_(validarLead_(d).scenario.documents[0] === 'unknown', 'sozinha vale');
  });
  t('respostas em formato longo: uma linha por opção marcada', function () {
    var d = leadValido_(); d.scenario.audienceProfiles = ['contractor', 'technical_team']; var linhas = respostas_(validarLead_(d));
    afirma_(linhas.filter(function (x) { return x[0] === 'audience_profile'; }).length === 2, 'perfis'); afirma_(linhas.filter(function (x) { return x[0] === 'consequence'; }).length === 2, 'consequências');
    afirma_(linhas.some(function (x) { return x[0] === 'situation' && x[1] === 'obra_contrato_dificuldade' && x[3] === 1; }), 'situação'); afirma_(CABECALHOS_RESPOSTAS.length === 5, 'cabeçalhos');
  });
  t('confirmação segue o canal escolhido', function () {
    afirma_(confirmacaoPorCanal_('email', true) === 'email' && confirmacaoPorCanal_('email', false) === 'none' && confirmacaoPorCanal_('whatsapp', false) === 'whatsapp', 'canais');
  });
  t('tempo mínimo', function () { afirma_(envioRapidoDemais_({ elapsedMs: 800 }) && !envioRapidoDemais_({ elapsedMs: 45000 }), 'tempo'); });
  t('CPF no texto é mascarado e marcado', function () { var d = leadValido_(); d.scenario.narrative = 'Meu CPF é 123.456.789-09 e preciso de ajuda com a obra.'; var l = validarLead_(d);
    afirma_(l.scenario.narrative.indexOf('123.456') < 0, 'mascara'); afirma_(l.sensitiveContentSuspected, 'marca'); });
  t('fórmula neutralizada', function () { afirma_(seguroParaPlanilha_('=IMPORTXML("x")') === "'=IMPORTXML(\"x\")", 'igual'); afirma_(seguroParaPlanilha_('+1+1') === "'+1+1", 'mais');
    afirma_(seguroParaPlanilha_('-2+3') === "'-2+3", 'menos'); afirma_(seguroParaPlanilha_('@SUM(A1)') === "'@SUM(A1)", 'arroba'); afirma_(seguroParaPlanilha_('texto') === 'texto', 'normal'); });
  t('código público tem formato e não é sequencial', function () { var a = gerarCodigoPublico_(), b = gerarCodigoPublico_(); afirma_(/^CRV-\d{4}-[A-Z2-9]{6}$/.test(a), 'formato ' + a); afirma_(a !== b, 'repetido'); });
  t('token de complemento confere só para o próprio código', function () { var tk = tokenDoLead_('CRV-2026-AAAAAA'); afirma_(tokenConfere_('CRV-2026-AAAAAA', tk), 'certo'); afirma_(!tokenConfere_('CRV-2026-BBBBBB', tk), 'outro'); afirma_(!tokenConfere_('CRV-2026-AAAAAA', 'x'), 'curto'); });
  t('complemento aceita só listas fechadas', function () {
    afirma_(validarDetalhes_({ urgency: 'immediate' }).urgency === 'immediate', 'ok'); afirma_(falha_(function () { validarDetalhes_({}); }), 'vazio'); afirma_(falha_(function () { validarDetalhes_({ urgency: 'ontem' }); }), 'inválido');
  });
  t('hash de idempotência é estável', function () { afirma_(hash_('a') === hash_('a') && hash_('a') !== hash_('b'), 'hash'); });
  t('situação "outra" sem produtos candidatos', function () { var d = leadValido_(); d.scenario.situationCodes = ['outra_nao_sei']; d.scenario.contextAnswers = { outra_nao_sei: 'unknown' };
    afirma_(enquadrar_(validarLead_(d)).candidateProducts.length === 0, 'vazio'); });
  t('cabeçalhos e colunas consistentes', function () { afirma_(CABECALHOS_LEADS[0] === 'submission_id' && CABECALHOS_LEADS.indexOf('city_code') > 0, 'cabeçalhos'); });
  t('configuração ausente falha de forma segura', function () { var antes = configuracaoCompleta_(); afirma_(typeof antes === 'boolean', 'boolean'); });
  console.log(r.join('\n'));
  if (r.some(function (x) { return x.indexOf('ERRO') === 0; })) throw new Error('Há testes com erro:\n' + r.join('\n'));
  return r.join('\n');
}
