/**
 * Configuração do backend "Apresentar meu cenário" (Google Apps Script).
 * Valores NÃO sigilosos ficam aqui (versionados). Segredos e IDs operacionais ficam em Script Properties
 * (Configurações do projeto > Propriedades do script) e nunca no repositório nem no navegador.
 */
var CRIVIA = {
  SCHEMA_VERSION: 2,
  SCORE_RULE_VERSION: 'score-v3',
  TIMEZONE: 'America/Sao_Paulo',
  // Canal público de contato comercial. NÃO é o e-mail de privacidade nem o destinatário dos alertas internos.
  CONTACT_REPLY_EMAIL: 'contato@criviaengenharia.com.br',
  SENDER_NAME: 'CRIVIA Engenharia Consultiva',
  MAX_BODY_CHARS: 20000,
  MIN_ELAPSED_MS: 4000,    // tempo mínimo plausível entre abrir a página e enviar (sinal contra robôs, não prova)
  RATE_MAX: 30,            // envios aceitos por janela (contador global; o Apps Script não informa o IP do visitante)
  RATE_WINDOW_SEC: 600,
  CONTACT_RATE_MAX: 3,     // envios por contato normalizado na mesma janela (guardado só como hash, no cache)
  SHEETS: { LEADS: 'Leads', CONFIG: 'Config', AUDIT: 'Audit' },
  LEGAL_BASIS_PLACEHOLDER: '[VALIDAR_BASE_LEGAL]'   // a base legal NÃO é definida em código: depende de validação jurídica
};

/** Propriedades de script esperadas. Obrigatórias: SPREADSHEET_ID, NOTIFICATION_EMAIL, PRIVACY_NOTICE_VERSION. */
var PROPS_OBRIGATORIAS = ['SPREADSHEET_ID', 'NOTIFICATION_EMAIL', 'PRIVACY_NOTICE_VERSION'];
var PROPS_OPCIONAIS = ['PRIVACY_CONTACT_EMAIL', 'TURNSTILE_SECRET_KEY', 'ALLOWED_SITE_ORIGIN', 'LEAD_RETENTION_POLICY_ID',
  'UNQUALIFIED_LEAD_RETENTION_DAYS', 'SECURITY_LOG_RETENTION_DAYS', 'CONFIRMATION_EMAIL_ENABLED', 'ENVIRONMENT', 'TOKEN_SECRET'];

function prop_(nome) {
  var v = PropertiesService.getScriptProperties().getProperty(nome);
  return v === null || v === '' ? null : v;
}

/** Recursos opcionais: desligados a menos que a propriedade valha exatamente "true". */
function ligado_(nome) { return prop_(nome) === 'true'; }

/** Falha de forma segura: se faltar configuração obrigatória, nada é gravado. */
function configuracaoCompleta_() {
  for (var i = 0; i < PROPS_OBRIGATORIAS.length; i++) if (!prop_(PROPS_OBRIGATORIAS[i])) return false;
  return true;
}

/** Cabeçalhos estáveis da aba Leads: uma linha por cenário. Os últimos são técnicos. */
var CABECALHOS_LEADS = ['submission_id', 'created_at', 'updated_at', 'status', 'situation_code', 'situation_label', 'context_question_code',
  'context_answer_code', 'context_answer_label', 'audience_profile_code', 'audience_profile_label', 'decision_role_code', 'decision_role_label',
  'location_type', 'country_code', 'country_name', 'state_code', 'state_name', 'city_code', 'city_name', 'foreign_region', 'scenario_description',
  'contact_name', 'organization_name', 'preferred_channel', 'whatsapp', 'email', 'privacy_notice_version', 'privacy_notice_acknowledged_at',
  'legal_basis_code', 'marketing_consent', 'marketing_consent_at', 'source_page', 'source_cta', 'utm_source', 'utm_medium', 'utm_campaign',
  'utm_content', 'utm_term', 'referrer_domain', 'optional_urgency', 'optional_documents', 'optional_contact_period', 'optional_consequences',
  'optional_estimated_range', 'assigned_to',
  'internal_notes', 'retention_review_at', 'deletion_or_anonymization_at',
  // técnicas (protegidas contra edição acidental)
  'priority', 'candidate_products', 'missing_information', 'idempotency_key_hash', 'notification_status', 'form_version', 'schema_version',
  'sensitive_content_suspected', 'score_json'];

var STATUS_INICIAIS = ['Novo', 'Em análise', 'Aguardando informação', 'Contatado', 'Qualificado', 'Proposta em preparação', 'Proposta enviada', 'Não aderente', 'Encerrado'];

/** Audit: eventos mínimos, sem relato, telefone ou e-mail. */
var CABECALHOS_AUDIT = ['at', 'submission_id', 'event', 'actor', 'result'];
