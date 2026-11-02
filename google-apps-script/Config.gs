/**
 * Configuração do backend "Apresentar meu cenário" (Google Apps Script).
 * Valores NÃO sigilosos ficam aqui (versionados). Segredos e IDs operacionais ficam em Script Properties
 * (Configurações do projeto > Propriedades do script) e nunca no repositório nem no navegador.
 */
var CRIVIA = {
  SCHEMA_VERSION: 1,
  SCORE_RULE_VERSION: 'score-v1',
  TIMEZONE: 'America/Sao_Paulo',
  // Canal público de contato comercial. NÃO é o e-mail de privacidade nem o destinatário dos alertas internos.
  CONTACT_REPLY_EMAIL: 'contato@criviaengenharia.com.br',
  SENDER_NAME: 'CRIVIA Engenharia Consultiva',
  MAX_BODY_CHARS: 20000,
  RATE_MAX: 30,            // envios aceitos por janela (contador global; o Apps Script não informa o IP do visitante)
  RATE_WINDOW_SEC: 600,
  SHEETS: { CENARIOS: 'Cenarios', HISTORICO: 'Historico', CONSENTIMENTOS: 'Consentimentos', LISTAS: 'Listas',
            INDICADORES: 'Indicadores', CONFIGURACAO: 'Configuracao', ERROS: 'Erros_Operacionais' }
};

/** Propriedades de script esperadas. Obrigatórias: SPREADSHEET_ID, NOTIFICATION_EMAIL, PRIVACY_NOTICE_VERSION. */
var PROPS_OBRIGATORIAS = ['SPREADSHEET_ID', 'NOTIFICATION_EMAIL', 'PRIVACY_NOTICE_VERSION'];
var PROPS_OPCIONAIS = ['PRIVACY_CONTACT_EMAIL', 'DRIVE_ROOT_FOLDER_ID', 'SECURE_UPLOAD_FOLDER_ID', 'TURNSTILE_SECRET_KEY',
  'ALLOWED_SITE_ORIGIN', 'LEAD_RETENTION_POLICY_ID', 'UNQUALIFIED_LEAD_RETENTION_DAYS', 'SECURITY_LOG_RETENTION_DAYS',
  'UPLOAD_RETENTION_DAYS', 'SECURE_UPLOAD_ENABLED', 'AI_LEAD_SUMMARY_ENABLED', 'CALENDAR_ENABLED', 'CONFIRMATION_EMAIL_ENABLED',
  'ENVIRONMENT', 'TOKEN_SECRET'];

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

/** Cabeçalhos estáveis da aba Cenarios (os 5 últimos são técnicos). */
var CABECALHOS_CENARIOS = ['lead_id', 'public_code', 'schema_version', 'created_at', 'updated_at', 'status', 'priority', 'review_status',
  'source_page', 'referrer', 'origin_cta', 'product_hint', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
  'device_category', 'entry_path', 'audience_context', 'decision_role', 'stage', 'issues', 'consequences', 'decision_horizon', 'city',
  'state', 'estimated_range', 'available_documents', 'narrative', 'branch_data_json', 'contact_name', 'organization', 'role_title',
  'preferred_channel', 'phone', 'email', 'preferred_contact_period', 'candidate_products', 'missing_information',
  'privacy_notice_version', 'privacy_acknowledged_at', 'marketing_consent', 'marketing_consent_at', 'marketing_consent_text_version',
  'next_action', 'reviewed_by', 'reviewed_at', 'internal_notes',
  'idempotency_key_hash', 'additional_info', 'notification_status', 'score_json', 'sensitive_content_suspected'];

var CABECALHOS_HISTORICO = ['at', 'public_code', 'event', 'detail'];
var CABECALHOS_CONSENTIMENTOS = ['at', 'public_code', 'privacy_notice_version', 'acknowledged', 'requested_channel', 'marketing_consent',
  'marketing_consent_text_version'];
var CABECALHOS_ERROS = ['at', 'stage', 'error_code'];
