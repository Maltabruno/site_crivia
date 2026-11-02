/**
 * Privacidade por padrão. Aqui ficam as decisões que o código toma sobre dados pessoais.
 * - A versão do Aviso gravada é a do SERVIDOR (PRIVACY_NOTICE_VERSION); a que o navegador mostrou é guardada à parte para auditoria.
 * - Nada de CPF/RG, saúde etc. é solicitado; se aparecer CPF/CNPJ no texto livre, é mascarado e o registro é marcado.
 * - Marketing não é oferecido nesta versão: sempre gravado como "não".
 * - Nenhuma base legal é definida aqui: depende de validação jurídica (docs/legal-review-checklist.md).
 */
function registroDeConsentimento_(lead, codigo, agora) {
  return [agora, codigo, prop_('PRIVACY_NOTICE_VERSION'), true, lead.privacy.requestedContactChannel, false, ''];
}

/** Devolve ao navegador somente o necessário (código público e token de complemento). */
function respostaDeSucesso_(codigo) {
  return { ok: true, publicCode: codigo, detailsToken: tokenDoLead_(codigo) };
}
