/**
 * E-mail NÃO é armazenamento. O alerta interno não contém narrativa, contato, documentos nem dados pessoais.
 * O remetente (From) nunca é falsificado: a mensagem sai da conta que executa o script; o Reply-To é o canal público.
 * Para enviar "como" contato@criviaengenharia.com.br é preciso que seja a conta executora ou um alias verificado (docs/google-apps-script-setup.md).
 */
function notificarNovoCenario_(codigo, categoria, prioridade, criadoEm) {
  var para = prop_('NOTIFICATION_EMAIL');
  if (!para) return false;
  var corpo = 'Um novo cenário foi registrado.\n\nCódigo: ' + codigo + '\nCategoria: ' + categoria + '\nPrioridade inicial: ' + prioridade +
    '\nData: ' + criadoEm + '\n\nAcesse o registro privado no Google Sheets ou no painel autorizado.\n\n' +
    'Esta mensagem não contém a narrativa nem os documentos do visitante.';
  MailApp.sendEmail({ to: para, subject: 'Novo cenário CRIVIA — ' + codigo + ' — Prioridade ' + prioridade, body: corpo, name: CRIVIA.SENDER_NAME, replyTo: CRIVIA.CONTACT_REPLY_EMAIL });
  return true;
}

/** Confirmação ao visitante: opcional (CONFIRMATION_EMAIL_ENABLED=true) e só quando ele informou e-mail. Sem narrativa, telefone, empresa, pontuação ou produtos. */
function confirmarAoVisitante_(email, nome, codigo) {
  if (!ligado_('CONFIRMATION_EMAIL_ENABLED') || !email) return false;
  var primeiro = String(nome).split(' ')[0].replace(/[\r\n]/g, '');
  var contato = CRIVIA.CONTACT_REPLY_EMAIL;
  var corpo = 'Olá, ' + primeiro + '.\n\nRecebemos as informações iniciais sobre o seu cenário, registrado com o código ' + codigo + '.\n\n' +
    'A CRIVIA fará o enquadramento inicial da demanda e indicará o próximo passo pelo canal escolhido. O envio deste formulário não constitui diagnóstico, proposta, contratação ou compromisso de atendimento.\n\n' +
    'Se precisar acrescentar uma informação essencial, responda a este e-mail ou escreva para ' + contato + ', informando o código ' + codigo + '.\n\n' +
    'Atenciosamente,\nCRIVIA Engenharia Consultiva\nEngenharia para Decisão';
  MailApp.sendEmail({ to: email, subject: 'Recebemos seu cenário — CRIVIA ' + codigo, body: corpo, name: CRIVIA.SENDER_NAME, replyTo: contato });
  return true;
}
