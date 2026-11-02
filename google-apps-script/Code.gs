/**
 * Ponto de entrada do Web App. O navegador envia POST com corpo JSON ({action, data}) como text/plain
 * (requisição simples, sem preflight). Respostas: sempre JSON {ok, ...}; nunca dados da planilha, IDs, e-mails internos ou stack trace.
 * Ações: "submit" (cenário completo) e "details" (complemento opcional, exige token).
 */
function doGet() { return json_({ ok: true }); }   // verificação de saúde; não lista nada

function json_(obj) { return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON); }

function doPost(e) {
  try {
    if (!configuracaoCompleta_()) { registrarErroSeguro_('config', 'configuracao_ausente'); return json_({ ok: false, error: 'unavailable' }); }
    var bruto = e && e.postData && e.postData.contents;
    if (!bruto || bruto.length > CRIVIA.MAX_BODY_CHARS) return json_({ ok: false, error: 'too_large' });
    var env;
    try { env = JSON.parse(bruto); } catch (x) { return json_({ ok: false, error: 'bad_request' }); }
    if (!env || typeof env !== 'object' || !env.data || typeof env.data !== 'object') return json_({ ok: false, error: 'bad_request' });
    if (!dentroDoLimite_()) return json_({ ok: false, error: 'rate' });
    if (env.action === 'submit') return json_(receberCenario_(env.data));
    if (env.action === 'details') return json_(receberDetalhes_(env.data));
    return json_({ ok: false, error: 'bad_request' });
  } catch (err) {
    registrarErroSeguro_('doPost', err && err.message ? err.message : 'erro');
    return json_({ ok: false, error: 'unavailable' });
  }
}

function registrarErroSeguro_(etapa, codigo) { try { if (prop_('SPREADSHEET_ID')) registrarErro_(etapa, codigo); } catch (x) { console.error(etapa); } }

function receberCenario_(dados) {
  if (dados.website) return { ok: true, publicCode: 'CRV-0000-000000', detailsToken: '' };   // armadilha de robô: resposta neutra, nada é gravado
  if (!antibotAprovado_(dados.turnstileToken)) return { ok: false, error: 'antibot' };
  var lead;
  try { lead = validarLead_(dados); }
  catch (err) { if (err instanceof ErroValidacao_) return { ok: false, error: 'validation', fields: err.campos }; throw err; }
  var q = enquadrar_(lead), hashChave = hash_(lead.idempotencyKey);

  var trava = LockService.getScriptLock();
  if (!trava.tryLock(20000)) return { ok: false, error: 'unavailable' };
  var gravado;
  try {
    var existente = procurarLinha_('idempotency_key_hash', hashChave);
    if (existente) return respostaDeSucesso_(codigoDaLinha_(existente));       // reenvio acidental: mesma resposta, sem nova linha
    gravado = gravarCenario_(lead, q, hashChave);
  } finally { trava.releaseLock(); }

  // Só depois da gravação confirmada. Falha de e-mail não apaga o cenário: fica registrada para reenvio.
  try {
    notificarNovoCenario_(gravado.codigo, lead.scenario.entryPath, q.priority, agora_());
    atualizarStatusNotificacao_(gravado.linha, 'sent');
  } catch (err) { atualizarStatusNotificacao_(gravado.linha, 'failed'); registrarErro_('notification', 'falha_no_envio'); }
  try { confirmarAoVisitante_(lead.contact.email, lead.contact.name, gravado.codigo); } catch (err) { registrarErro_('confirmation', 'falha_no_envio'); }
  return respostaDeSucesso_(gravado.codigo);
}

function receberDetalhes_(dados) {
  var codigo = String(dados.leadRef || '');
  if (!/^CRV-\d{4}-[A-Z0-9]{6}$/.test(codigo) || !tokenConfere_(codigo, dados.token)) return { ok: false, error: 'unauthorized' };
  var d;
  try { d = validarDetalhes_({ additionalInfo: dados.additionalInfo }); }
  catch (err) { if (err instanceof ErroValidacao_) return { ok: false, error: 'validation', fields: err.campos }; throw err; }
  var trava = LockService.getScriptLock();
  if (!trava.tryLock(20000)) return { ok: false, error: 'unavailable' };
  try { return gravarDetalhes_(codigo, d) ? { ok: true } : { ok: false, error: 'not_found' }; }
  finally { trava.releaseLock(); }
}

/** Reenvio manual de notificações que falharam (executar no editor). Não reenvia o que já saiu. */
function reenviarNotificacoesPendentes() {
  var a = aba_(CRIVIA.SHEETS.CENARIOS, CABECALHOS_CENARIOS), n = a.getLastRow();
  if (n < 2) return 0;
  var idx = function (c) { return CABECALHOS_CENARIOS.indexOf(c); };
  var linhas = a.getRange(2, 1, n - 1, CABECALHOS_CENARIOS.length).getValues(), enviados = 0;
  linhas.forEach(function (l, i) {
    if (l[idx('notification_status')] !== 'failed') return;
    try { notificarNovoCenario_(l[idx('public_code')], l[idx('entry_path')], l[idx('priority')], l[idx('created_at')]); atualizarStatusNotificacao_(i + 2, 'sent'); enviados++; }
    catch (err) { registrarErro_('notification_retry', 'falha_no_envio'); }
  });
  return enviados;
}
