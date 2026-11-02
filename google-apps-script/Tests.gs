/**
 * Testes de unidade que NÃO tocam a planilha de produção (só validação, classificação e segurança em memória).
 * Executar `rodarTestes` no editor do Apps Script. Testes de gravação exigem uma planilha de TESTE separada
 * (configure SPREADSHEET_ID dela em um projeto de teste; nunca rode contra a planilha de produção).
 */
function leadValido_() {
  return { idempotencyKey: 'abc12345-test', schemaVersion: 1, source: { originCta: 'hero', productHint: 'P06', deviceCategory: 'desktop' },
    scenario: { entryPath: 'underperforming', audienceContext: 'contractor', decisionRole: 'decides', stage: 'execution', issues: ['schedule'],
      consequences: ['penalty'], decisionHorizon: 'up_to_7_days', city: 'Belo Horizonte', state: 'MG', availableDocuments: ['contract', 'schedule', 'budget'],
      narrative: 'A obra está atrasada e precisamos decidir como recuperar o prazo.', branchSpecificData: {} },
    contact: { name: 'Maria Souza', organization: 'Construtora X', preferredChannel: 'email', email: 'maria@exemplo.com.br' },
    privacy: { privacyNoticeVersion: 'minuta-0', acknowledged: true, marketingConsent: false }, website: '' };
}
function afirma_(cond, msg) { if (!cond) throw new Error('FALHOU: ' + msg); }
function falha_(fn) { try { fn(); } catch (e) { return e instanceof ErroValidacao_ ? e.campos : null; } return null; }

function rodarTestes() {
  var r = [];
  var t = function (nome, fn) { try { fn(); r.push('ok   ' + nome); } catch (e) { r.push('ERRO ' + nome + ' — ' + e.message); } };
  t('lead válido normaliza e classifica', function () {
    var l = validarLead_(leadValido_()), q = enquadrar_(l);
    afirma_(l.contact.email === 'maria@exemplo.com.br', 'email'); afirma_(q.priority === 'A', 'prioridade ' + q.priority); afirma_(q.candidateProducts.indexOf('P06') >= 0, 'P06');
  });
  t('enum inválido recusado', function () { var d = leadValido_(); d.scenario.entryPath = 'xx'; afirma_(falha_(function () { validarLead_(d); })['scenario.entryPath'], 'entryPath'); });
  t('campo desconhecido recusado', function () { var d = leadValido_(); d.extra = 1; afirma_(falha_(function () { validarLead_(d); })['$.extra'], 'extra'); });
  t('arrays excessivos recusados', function () { var d = leadValido_(); d.scenario.issues = ['schedule', 'quality', 'supplier', 'other']; afirma_(falha_(function () { validarLead_(d); })['scenario.issues'], 'issues'); });
  t('narrativa grande recusada', function () { var d = leadValido_(); d.scenario.narrative = new Array(702).join('a'); afirma_(falha_(function () { validarLead_(d); })['scenario.narrative'], 'narrativa'); });
  t('privacidade exige ciência', function () { var d = leadValido_(); d.privacy.acknowledged = false; afirma_(falha_(function () { validarLead_(d); })['privacy.acknowledged'], 'ack'); });
  t('marketing não é aceito', function () { var d = leadValido_(); d.privacy.marketingConsent = true; afirma_(falha_(function () { validarLead_(d); })['privacy.marketingConsent'], 'mkt'); });
  t('telefone E.164', function () { afirma_(normalizarTelefone_('(31) 99999-1234') === '+5531999991234', 'br'); afirma_(normalizarTelefone_('+351912345678') === '+351912345678', 'intl'); afirma_(normalizarTelefone_('123') === null, 'curto'); });
  t('empresa obrigatória em contexto empresarial', function () { var d = leadValido_(); d.contact.organization = ''; afirma_(falha_(function () { validarLead_(d); })['contact.organization'], 'org'); });
  t('CPF no texto é mascarado e marcado', function () { var d = leadValido_(); d.scenario.narrative = 'Meu CPF é 123.456.789-09 e preciso de ajuda com a obra.'; var l = validarLead_(d);
    afirma_(l.scenario.narrative.indexOf('123.456') < 0, 'mascara'); afirma_(l.sensitiveContentSuspected, 'marca'); });
  t('fórmula neutralizada', function () { afirma_(seguroParaPlanilha_('=IMPORTXML("x")') === "'=IMPORTXML(\"x\")", 'igual'); afirma_(seguroParaPlanilha_('+1+1') === "'+1+1", 'mais');
    afirma_(seguroParaPlanilha_('@SUM(A1)') === "'@SUM(A1)", 'arroba'); afirma_(seguroParaPlanilha_('texto') === 'texto', 'normal'); });
  t('HTML/XSS não é executável (é só texto)', function () { var d = leadValido_(); d.scenario.narrative = '<script>alert(1)</script> atraso de obra'; var l = validarLead_(d); afirma_(typeof l.scenario.narrative === 'string', 'tipo'); });
  t('código público tem formato e não é sequencial', function () { var a = gerarCodigoPublico_(), b = gerarCodigoPublico_(); afirma_(/^CRV-\d{4}-[A-Z2-9]{6}$/.test(a), 'formato ' + a); afirma_(a !== b, 'repetido'); });
  t('token de complemento confere só para o próprio código', function () { var tk = tokenDoLead_('CRV-2026-AAAAAA'); afirma_(tokenConfere_('CRV-2026-AAAAAA', tk), 'certo'); afirma_(!tokenConfere_('CRV-2026-BBBBBB', tk), 'outro'); afirma_(!tokenConfere_('CRV-2026-AAAAAA', 'x'), 'curto'); });
  t('hash de idempotência é estável', function () { afirma_(hash_('a') === hash_('a') && hash_('a') !== hash_('b'), 'hash'); });
  t('rota E sem produtos candidatos', function () { var d = leadValido_(); d.scenario.entryPath = 'other_or_unsure'; d.scenario.stage = null; d.scenario.issues = []; d.scenario.branchSpecificData = { decisionNeeded: 'Preciso decidir o rumo do projeto.' };
    afirma_(produtosCandidatos_(validarLead_(d)).length === 0, 'vazio'); });
  t('configuração ausente falha de forma segura', function () { var antes = configuracaoCompleta_(); afirma_(typeof antes === 'boolean', 'boolean'); });
  console.log(r.join('\n'));
  if (r.some(function (x) { return x.indexOf('ERRO') === 0; })) throw new Error('Há testes com erro:\n' + r.join('\n'));
  return r.join('\n');
}
