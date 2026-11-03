/**
 * Privacidade por padrão. Aqui ficam as decisões que o código toma sobre dados pessoais.
 * - A versão do Aviso gravada é a do SERVIDOR (PRIVACY_NOTICE_VERSION).
 * - Nada de CPF/RG, saúde etc. é solicitado; se aparecer CPF/CNPJ no texto livre, é mascarado e o registro é marcado.
 * - Marketing é opcional e separado: só vale "true" se o visitante marcou; grava data. Sem marcação, nada é adicionado a listas de marketing.
 * - Nenhuma base legal é definida aqui: a coluna legal_basis_code recebe o marcador [VALIDAR_BASE_LEGAL] até a validação jurídica
 *   (docs/legal-review-checklist.md). A "ciência do aviso" é registrada à parte da base legal.
 * - Sem IP, GPS, CEP, endereço completo, cookies ou identificadores publicitários.
 */

/**
 * Devolve ao navegador somente o necessário. O protocolo NÃO é mostrado na tela: segue ao visitante pelo canal que ele escolheu.
 * `confirmation`: 'email' (confirmação automática enviada), 'whatsapp' (a equipe envia; aparece no alerta interno) ou 'none'.
 * O código público e o token de complemento ficam na resposta só por compatibilidade com a ação "details" (não usada pela página atual).
 */
function respostaDeSucesso_(codigo, confirmation) {
  return { ok: true, publicCode: codigo, detailsToken: tokenDoLead_(codigo), confirmation: confirmation || 'none' };
}

function confirmacaoPorCanal_(canal, emailEnviado) { return canal === 'whatsapp' ? 'whatsapp' : (canal === 'email' && emailEnviado ? 'email' : 'none'); }
