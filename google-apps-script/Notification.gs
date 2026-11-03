/**
 * E-mail NÃO é armazenamento. O alerta interno traz só o necessário para responder (protocolo, nome, canal e contato, categoria e
 * localidade) e o link privado da planilha; o relato completo fica na planilha, nunca no e-mail (menos cópias e encaminhamentos).
 * O remetente (From) nunca é falsificado: a mensagem sai da conta que executa o script; o Reply-To é o canal público.
 * Para enviar "como" contato@criviaengenharia.com.br é preciso que seja a conta executora ou um alias verificado (docs/google-apps-script-setup.md).
 */
function notificarNovoCenario_(codigo, categoria, localidade, contato, prioridade, criadoEm) {
  var para = prop_('NOTIFICATION_EMAIL');
  if (!para) return false;
  var canal = contato.preferredChannel === 'whatsapp' ? 'WhatsApp ' + contato.phone : 'E-mail ' + contato.email;
  var planilha = 'https://docs.google.com/spreadsheets/d/' + prop_('SPREADSHEET_ID');
  var corpo = 'Um novo cenário foi registrado.\n\nProtocolo: ' + codigo + '\nNome: ' + String(contato.name || '').replace(/[\r\n]/g, ' ') + '\nResposta preferida: ' + canal +
    '\nCategoria: ' + categoria + '\nLocalidade: ' + (localidade || '—') + '\nPrioridade inicial: ' + prioridade + '\nData: ' + criadoEm +
    (contato.preferredChannel === 'whatsapp' ? '\n\nAÇÃO: enviar ao WhatsApp acima a mensagem de confirmação com o protocolo ' + codigo + ' (o site informou que a CRIVIA enviará).' : '') +
    '\n\nRegistro completo (acesso restrito): ' + planilha + '\n\nO relato completo está somente na planilha. Não encaminhe esta mensagem a pessoas sem necessidade de acesso.';
  var assunto = ('[Novo cenário CRIVIA] ' + codigo + ' — ' + categoria + ' — ' + (localidade || 'sem localidade')).replace(/[\r\n]/g, ' ');
  MailApp.sendEmail({ to: para, subject: assunto, body: corpo, name: CRIVIA.SENDER_NAME, replyTo: CRIVIA.CONTACT_REPLY_EMAIL });
  return true;
}

/** Confirmação ao visitante: opcional (CONFIRMATION_EMAIL_ENABLED=true) e só quando ele informou e-mail. Sem relato, telefone, empresa, pontuação ou produtos. */
function confirmarAoVisitante_(email, nome, codigo) {
  if (!ligado_('CONFIRMATION_EMAIL_ENABLED') || !email) return false;
  var corpo = 'Recebemos o cenário apresentado à CRIVIA. O protocolo é ' + codigo + '. As informações serão analisadas e a resposta será feita pelo canal indicado. ' +
    'Se precisar complementar antes do retorno, responda a este e-mail informando o protocolo.\n\n' +
    'O envio não constitui diagnóstico, proposta, contratação ou compromisso de atendimento.\n\nCRIVIA Engenharia Consultiva\nEngenharia para Decisão';
  MailApp.sendEmail({ to: email, subject: 'Recebemos seu cenário — CRIVIA ' + codigo, body: corpo, name: CRIVIA.SENDER_NAME, replyTo: CRIVIA.CONTACT_REPLY_EMAIL });
  return true;
}
