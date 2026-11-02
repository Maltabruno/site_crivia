# Modelo de ameaças e controles — "Apresentar meu cenário"

Escopo: página estática `apresentar-cenario.html` + servidor de leads (`servidor/servidor_leads.py`). O servidor é um **servidor de referência** (biblioteca padrão do Python, SQLite): serve para validar o fluxo e pode ser a base de uma publicação, mas a hospedagem, o HTTPS e o painel interno são decisões pendentes.

## Ativos
Dados do visitante (contato e texto livre), a fila de notificação, o segredo de tokens (`meta.token_secret`), o banco `leads.db` e os logs.

## Ameaças e controles

| Ameaça | Controle implementado | Onde |
|---|---|---|
| Validação só no cliente (bypass) | O servidor revalida tudo: esquema estrito, listas permitidas, limites, normalização | `regras_leads.validar_lead` |
| XSS armazenado/refletido | O navegador usa `textContent` (nunca `innerHTML`); o servidor guarda texto puro; CSP sem `unsafe-inline` | `cenario.js`, meta CSP |
| Injeção SQL | Consultas parametrizadas; teste com `');DROP TABLE leads;--` | `servidor_leads.py`, `test_xss_e_sql_injection...` |
| Parâmetros de URL maliciosos | `origem` e `interesse` só aceitam listas permitidas; o resto vira "direto"/vazio; nada é renderizado sem validação | `regras.js lerOrigem`, servidor |
| Corpo gigante / arrays grandes | 32 KB por requisição; limites por campo e por lista | `LIMITE_CORPO`, `regras_leads` |
| Abuso e robôs | Limite por IP (hash em memória), armadilha de robô acessível, Turnstile opcional validado no servidor (`Siteverify`) | `servidor_leads.py` |
| Envio duplicado / repetição | Chave de idempotência (UNIQUE no banco); botão desabilitado durante o envio | `idem_key` |
| CORS | Somente origens listadas em `CRIVIA_ALLOWED_ORIGINS`; sem cookies (`credentials: omit`) | `servidor_leads.py` |
| CSRF | A API não usa cookie nem sessão; exige `Content-Type: application/json` e origem permitida | `do_POST` |
| Vazamento por logs | Log de acesso só com método, rota (sem query) e status; log de segurança sem conteúdo | `log_request`, `registrar_seguranca` |
| Acesso a registros por terceiros | Sem painel web; leitura apenas local (`listar`); IDs aleatórios; token HMAC por lead para o complemento | `token_do_lead` |
| Segredos no código | Nenhum segredo no navegador; segredos por variável de ambiente; `token_secret` gerado no primeiro uso | `config()` |
| Erros com detalhes internos | Respostas genéricas (`{"erro": "..."}`); validação devolve só caminhos de campo e códigos, nunca o valor | `_responder` |
| Falha da integração | O registro é salvo primeiro; a notificação é uma fila (`outbox`) sem PII | `criar_lead` |

## Cabeçalhos e CSP
A página traz `Content-Security-Policy` por `<meta>`: `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self' <endereço do servidor de leads>; form-action 'self'; base-uri 'none'; object-src 'none'`.
**Exceções/limites:** (1) `frame-ancestors` não funciona por `<meta>`; configure por cabeçalho HTTP na hospedagem. (2) A página principal do site (`index.html`, cena 3D) tem sua própria necessidade de scripts e não recebeu esta política; revisar separadamente. (3) A CSP depende do endereço do servidor de leads definido em `CRIVIA_LEAD_ENDPOINT` na geração.
Configurar na hospedagem: `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy` (sem câmera, microfone ou geolocalização) e proteção de framing. O servidor de leads já envia `nosniff`, `no-store` e `Referrer-Policy: no-referrer`.

## Upload de arquivos (desligado: `SECURE_UPLOAD_ENABLED=false`)
Não há upload nesta versão. Para ligar, é preciso, no mínimo: lead válido, token curto de uso limitado, expiração, lista de extensões, validação de MIME e de assinatura, limite de tamanho, renomeação, armazenamento privado fora da raiz web, URLs temporárias assinadas, antivírus com quarentena, controle e registro de acesso, retenção e exclusão. Bloquear executáveis, scripts, macros, HTML, SVG sem sanitização, compactados, arquivos de configuração e extensões duplas. Não enviar anexo por e-mail nem a IA.

## Riscos residuais e pendências técnicas
- O servidor de referência não faz TLS: publicar atrás de HTTPS.
- O limite de requisições vive em memória: com várias instâncias, usar um limitador compartilhado.
- Turnstile: o lado do servidor está implementado, mas **não foi testado** (sem credencial) e o componente visual não foi incluído no cliente.
- Sem autenticação nem painel interno: definir perfis, MFA e trilha de acesso antes de qualquer interface administrativa.
- Backup e criptografia em repouso do `leads.db` dependem da hospedagem.
- Não há teste de penetração independente; recomenda-se um antes da publicação.
