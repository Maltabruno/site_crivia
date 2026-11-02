/**
 * Segurança: identificadores, token de complemento, proteção contra fórmulas, limite de uso, anti-bot opcional.
 * Limitação conhecida: um Web App do Apps Script não recebe o IP nem o cabeçalho Origin do visitante.
 * Por isso o limite de uso é global (contador no cache) e a "origem" não pode ser validada aqui; ver docs/security-threat-model.md.
 */
var ALFABETO_CODIGO = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';   // sem caracteres ambíguos (0/O, 1/I)

function uuid_() { return Utilities.getUuid(); }

/** Código público não sequencial, ex.: CRV-2026-A7K9P2. Não revela volume de contatos. */
function gerarCodigoPublico_() {
  var bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, Utilities.getUuid() + Utilities.getUuid());
  var s = '';
  for (var i = 0; i < 6; i++) s += ALFABETO_CODIGO.charAt((bytes[i] + 256) % 256 % ALFABETO_CODIGO.length);
  return 'CRV-' + Utilities.formatDate(new Date(), CRIVIA.TIMEZONE, 'yyyy') + '-' + s;
}

function hash_(texto) {
  return Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, texto)).replace(/=+$/, '');
}

function segredoDeToken_() {
  var p = PropertiesService.getScriptProperties(), s = p.getProperty('TOKEN_SECRET');
  if (!s) { s = Utilities.getUuid() + Utilities.getUuid(); p.setProperty('TOKEN_SECRET', s); }
  return s;
}

/** Token do complemento opcional: prova que quem complementa é quem acabou de enviar. Não é autenticação de usuário. */
function tokenDoLead_(codigoPublico) {
  var assinatura = Utilities.computeHmacSha256Signature(codigoPublico, segredoDeToken_());
  return Utilities.base64EncodeWebSafe(assinatura).replace(/=+$/, '');
}

function tokenConfere_(codigoPublico, token) {
  var esperado = tokenDoLead_(codigoPublico);
  if (typeof token !== 'string' || token.length !== esperado.length) return false;
  var d = 0;
  for (var i = 0; i < esperado.length; i++) d |= esperado.charCodeAt(i) ^ token.charCodeAt(i);
  return d === 0;
}

/** Neutraliza injeção de fórmula: valores que começam com = + - @ (ou TAB/CR) recebem apóstrofo. Telefones E.164 são validados antes. */
function seguroParaPlanilha_(valor) {
  if (valor === null || valor === undefined) return '';
  var t = String(valor);
  if (/^[=+\-@\t\r]/.test(t)) t = "'" + t;
  return t;
}
function telefoneParaPlanilha_(e164) { return /^\+\d{8,15}$/.test(e164) ? e164 : seguroParaPlanilha_(e164); }

/** Limite de uso global por janela. Devolve false quando excedido. */
function dentroDoLimite_() {
  var cache = CacheService.getScriptCache(), chave = 'rl:' + Math.floor(Date.now() / (CRIVIA.RATE_WINDOW_SEC * 1000));
  var n = Number(cache.get(chave) || 0) + 1;
  cache.put(chave, String(n), CRIVIA.RATE_WINDOW_SEC);
  return n <= CRIVIA.RATE_MAX;
}

/** Anti-bot opcional (Cloudflare Turnstile, modo gerenciado). Só exigido se TURNSTILE_SECRET_KEY existir. Nunca confia apenas no token recebido. */
function antibotAprovado_(token) {
  var segredo = prop_('TURNSTILE_SECRET_KEY');
  if (!segredo) return true;
  if (typeof token !== 'string' || !token || token.length > 2048) return false;
  try {
    var r = UrlFetchApp.fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'post', muteHttpExceptions: true,
      payload: { secret: segredo, response: token } });
    return r.getResponseCode() === 200 && JSON.parse(r.getContentText()).success === true;
  } catch (e) { return false; }
}
