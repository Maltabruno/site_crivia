/* Configuração da página "Apresentar meu cenário". Tudo que depende de decisão jurídica ou operacional fica AQUI,
   vazio ou desligado, e consta em docs/legal-review-checklist.md. Nada abaixo foi inventado.
   O gerador (Site_crivia.py) substitui http://localhost:8787 pela variável de ambiente CRIVIA_LEAD_ENDPOINT. */
window.CRIVIA_CENARIO_CONFIG = {
  // URL da implantação do Google Apps Script (Web App) que recebe o formulário e grava na planilha privada.
  // Em testes locais, aponta para servidor/servidor_leads.py (mesmo protocolo). Vazio = o envio é recusado com mensagem clara.
  endpoint: "http://localhost:8787",

  // Canal público de contato comercial (CONTACT_REPLY_EMAIL). NÃO é o e-mail de privacidade nem o destinatário dos alertas internos.
  contactEmail: "contato@criviaengenharia.com.br",

  // Versão do Aviso de Privacidade exibido. Enquanto for minuta, a versão começa com "minuta".
  privacyNoticeVersion: "minuta-0",
  privacyNoticeUrl: "aviso-privacidade.html",
  voltarAoSiteUrl: "index.html",

  // Texto do microtexto do botão do site (configurável; o tempo é uma hipótese a validar com testes de uso).
  microtexto: "Leva cerca de 1 minuto. Você não precisa saber qual serviço escolher.",

  // Canal de solicitações de titulares: PENDENTE (não inventar). Ainda não é exibido na interface: entra no Aviso quando for definido.
  canalPrivacidade: "contato@criviaengenharia.com.br",   // definido pelo responsável: o mesmo e-mail atende privacidade

  // Recursos desligados até existir arquitetura/validação (ver docs):
  secureUploadEnabled: false,          // upload seguro de documentos
  agendaUrl: "",                       // link do provedor de agenda; vazio = botão não aparece. Só é aberto após clique.
  analyticsEnabled: false,             // eventos do funil; só disparam com consentimento aplicável (ver docs/lead-form-analytics.md)
  turnstileSiteKey: "",                // Cloudflare Turnstile: o servidor já valida o token se TURNSTILE_SECRET existir; o componente no cliente ainda NÃO foi implementado (pendência)
  aiLeadSummaryEnabled: false          // resumo interno por IA: sem implementação nesta versão
};
