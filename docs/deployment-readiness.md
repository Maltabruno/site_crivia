# Prontidão para publicação — "Apresentar meu cenário"

> **Armazenamento (atualizado):** a fonte oficial dos cenários passa a ser uma planilha privada no Google Sheets, gravada por um Google Apps Script (`google-apps-script/`, ver `google-apps-script-setup.md`). O servidor Python + SQLite descrito abaixo vira **apenas ambiente local de teste** (mesmo protocolo). Nada do Google foi criado nem implantado.

**Nada foi publicado, commitado ou implantado.** Este documento lista como rodar, o que configurar, o que está bloqueado e o que falta antes de produção.

## Arquivos
- `cenario/` — fontes da página: `cenario.html`, `cenario.css`, `cenario.js`, `regras.js`, `config.js`, `aviso-privacidade.html` (minuta).
- `servidor/` — `regras_leads.py` (validação, pontuação, produtos), `servidor_leads.py` (HTTP + SQLite + comandos).
- `tests/` — `test_servidor.py` (22 testes), `regras.test.html` (16 testes no navegador).
- `Site_crivia.py` — publica a página em `site/assets/overview/apresentar-cenario.html` (+ css/js) e liga todos os botões "Apresentar meu cenário".
- `docs/` — estes documentos.

## Rodar localmente
```bash
# 1) servidor de leads (porta 8787), banco em servidor/leads.db
python -I servidor/servidor_leads.py

# 2) site (gera e serve em http://localhost:8080)
python -I Site_crivia.py --no-browser --port 8080
# abrir http://localhost:8080/assets/overview/apresentar-cenario.html

# ver os registros (acesso local ao banco)
python -I servidor/servidor_leads.py listar

# testes
python -I -m unittest discover -s tests -v
# regras no navegador: servir a pasta site_crivia (python -I -m http.server 8090) e abrir /tests/regras.test.html
```
A página só envia quando o servidor está no ar; sem ele, mostra a mensagem de erro e mantém as respostas.
Abrir por `file://` não funciona para o envio (CORS exige origem http/https).

## Variáveis de ambiente
| Variável | Padrão | Uso |
|---|---|---|
| `CRIVIA_LEAD_ENDPOINT` | `http://localhost:8787` (teste) | URL do Web App do Apps Script (`.../exec`) em produção; servidor local em teste. Lido na **geração** do site (entra no `config.js` e na CSP). **Definir em produção.** |
| `CRIVIA_DB` | `servidor/leads.db` | Caminho do banco |
| `CRIVIA_PORT` | `8787` | Porta |
| `CRIVIA_ALLOWED_ORIGINS` | `http://localhost:8080,http://127.0.0.1:8080` | Origens aceitas (CORS e POST). **Definir em produção.** |
| `CRIVIA_PRIVACY_NOTICE_VERSION` | `minuta-0` | Versão do aviso (o navegador envia a sua; mantenha igual) |
| `CRIVIA_RATE_MAX` / `CRIVIA_RATE_WINDOW` | `5` / `600` | Envios por IP por janela (segundos) |
| `TURNSTILE_SECRET` | vazio | Se definido, o servidor exige e valida o token (cliente ainda sem o componente) |
| `LEAD_RETENTION_POLICY_ID`, `LEAD_RETENTION_DAYS`, `UNQUALIFIED_LEAD_RETENTION_DAYS`, `SECURITY_LOG_RETENTION_DAYS` | vazias | **Obrigatórias** para `expurgar`; sem elas o comando recusa. `UPLOAD_RETENTION_DAYS` fica para quando houver upload. |
| `AI_LEAD_SUMMARY_ENABLED` | `false` | Sem implementação nesta versão |

## Itens bloqueados por feature flag (`cenario/config.js`)
`secureUploadEnabled=false` · `agendaUrl=""` · `analyticsEnabled=false` · `turnstileSiteKey=""` · `aiLeadSummaryEnabled=false` · `canalPrivacidade="contato@criviaengenharia.com.br"`.

## Testes executados (esta sessão)
- Python: 22 testes passaram (validação, todas as rotas, limites, telefone/e-mail, pontuação A/B/C, produtos, idempotência, armadilha de robô, XSS e SQL, 413/415/403/429, token de detalhes, logs sem PII, retenção recusada sem política e respeitando suspensão).
- Navegador: 16 testes das regras passaram; fluxo completo das cinco rotas enviado ao servidor e conferido no banco; erro com servidor parado (respostas mantidas); limite de 3 opções; voltar sem perder respostas; complemento opcional; teclado (Enter e barra de espaço); auditoria de rótulos/legendas/ids; tela de 375 px sem rolagem lateral; botões do site (hero, indústria, catálogo, Método) levam à página.
- **Não executado:** leitor de tela, contraste automatizado, Playwright, teste de carga, Turnstile real, `file://`, navegadores além do embutido.

## Reversão
Nada foi commitado. Para desfazer: `git checkout -- Site_crivia.py site/` e remover `cenario/`, `servidor/`, `tests/`, `docs/` (pastas novas, não rastreadas). Os botões voltam ao comportamento anterior (rolar até a dobra final).

## Recomendações antes de produção
1. Resolver `legal-review-checklist.md` (dados do controlador, bases legais, retenção, fornecedores) e substituir a minuta do Aviso.
2. Hospedar o servidor com HTTPS, definir `CRIVIA_ALLOWED_ORIGINS` e `CRIVIA_LEAD_ENDPOINT`, backup e criptografia em repouso.
3. Cabeçalhos HTTP na hospedagem (HSTS, CSP por cabeçalho com `frame-ancestors`, Permissions-Policy).
4. Definir acesso interno aos leads (perfis, MFA, trilha) e a notificação interna sem PII.
5. Teste de uso e de acessibilidade com pessoas e leitor de tela; revisar contraste.
6. Teste de segurança independente.
7. Aprovar separadamente: visual, textos, Aviso, dados jurídicos, analytics, marketing, agenda, IA, upload, commit e publicação.
