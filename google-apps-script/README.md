# Backend sem servidor — Google Apps Script + Google Sheets

Estes arquivos são **cópia local, não publicada**. Nenhum recurso Google foi criado e nenhum deploy foi feito.
O front-end nunca acessa a planilha: ele envia o formulário ao Web App, que valida, grava e responde só `{ok, publicCode, detailsToken}`.
Não existe endpoint de leitura, listagem, busca ou edição de leads.

## Pré-requisitos (decisões suas, pendentes)
- `{{GOOGLE_ACCOUNT_OWNER}}`: conta **institucional** (Workspace da CRIVIA, com verificação em duas etapas, sessões revisadas e recuperação configurada) dona da planilha e do projeto Apps Script. Não use conta pessoal, de agência ou de prestador; se for a única opção, registre como risco e peça autorização antes. Princípio do menor privilégio: acesso só a quem precisa.
- Quatro endereços com finalidades **diferentes** (não presumir que são o mesmo):
  | Propriedade | Para quê | Situação |
  |---|---|---|
  | `CONTACT_REPLY_EMAIL` | responde ao visitante (Reply-To, tela de sucesso/erro) | **`contato@criviaengenharia.com.br`** (fixo em `Config.gs` e `cenario/config.js`) |
  | `NOTIFICATION_EMAIL` | alerta interno de novo cenário | pendente (pode ser o mesmo endereço comercial, se a CRIVIA aprovar) |
  | `PRIVACY_CONTACT_EMAIL` | solicitações de titulares (LGPD) | definido pelo responsável: `contato@criviaengenharia.com.br` |
  | conta proprietária | dona dos recursos Google | pendente |

## Arquivos
`Code.gs` (entrada `doPost`) · `Validation.gs` (esquema v2 e localização) · `Municipios.gs` (**gerado** do IBGE por `scripts/gerar_localidades.py`; não editar) · `Classification.gs` (score-v2) ·
`Security.gs` (token, fórmulas, limites, anti-bot opcional) · `SheetsRepository.gs` (abas `Leads`, `Config`, `Audit`) · `Notification.gs` · `Privacy.gs` · `Tests.gs` · `appsscript.json`.

## Passo a passo (manual)
1. **Planilha:** no Drive institucional, crie "CRIVIA — Cenários recebidos pelo site". Compartilhamento **Restrito**; sem "qualquer pessoa com o link", sem publicar na web. Anote o ID (trecho entre `/d/` e `/edit` da URL).
2. **Projeto:** na planilha, *Extensões > Apps Script*. Copie cada `.gs` (inclusive `Municipios.gs`) e o `appsscript.json` (ative *Mostrar arquivo de manifesto* em Configurações do projeto). Não usamos `clasp`.
3. **Script Properties** (Configurações do projeto > Propriedades do script): `SPREADSHEET_ID`, `NOTIFICATION_EMAIL`, `PRIVACY_NOTICE_VERSION` (obrigatórias; sem elas o Web App recusa tudo). Opcionais: `PRIVACY_CONTACT_EMAIL`, `ALLOWED_SITE_ORIGIN`, `TURNSTILE_SECRET_KEY`, `LEAD_RETENTION_POLICY_ID`, `UNQUALIFIED_LEAD_RETENTION_DAYS`, `SECURITY_LOG_RETENTION_DAYS`, `ENVIRONMENT`. Desligada por padrão (só vale se for exatamente `true`): `CONFIRMATION_EMAIL_ENABLED`. **Não preencha valores jurídicos fictícios.** Nenhum ID, e-mail administrativo ou segredo vai para o JavaScript público ou para o repositório.
4. **Preparar a planilha:** no editor, execute `prepararPlanilha` (cria `Leads` com filtro, linha congelada, lista de status e proteção com aviso no cabeçalho e nas colunas técnicas; `Config` e `Audit`). Autorize os escopos pedidos.
5. **Testes (sem tocar a produção):** execute `rodarTestes` (21 testes em memória). Testes de gravação só em planilha de TESTE separada.
6. **Implantar:** *Implantar > Nova implantação > App da Web*; executar como **você (proprietário)**; acesso **Qualquer pessoa** (necessário para o formulário público; o endpoint só aceita o JSON do formulário e nunca devolve dados). Copie a URL `.../exec`.
7. **Ligar o site:** gere o site com `CRIVIA_LEAD_ENDPOINT` apontando para essa URL:
   ```bash
   CRIVIA_LEAD_ENDPOINT="https://script.google.com/macros/s/SEU_ID/exec" python -I Site_crivia.py --no-browser --port 8080
   ```
   (a política CSP da página já inclui `script.google.com` e `script.googleusercontent.com`).
8. **Atualizar:** *Implantar > Gerenciar implantações > Editar > Nova versão*. A URL não muda. Se as localidades forem regeneradas, copie o novo `Municipios.gs`.
9. **Revogar / rollback:** *Gerenciar implantações > Arquivar* (o formulário passa a mostrar a mensagem de falha com o e-mail alternativo) ou voltar para uma versão anterior. Para trocar o `TOKEN_SECRET`, apague a propriedade (invalida os links de complemento em aberto).
10. **Monitorar:** *Execuções* (logs sem corpo de formulário) e a aba `Audit` (eventos `error:*`). Cotas de `MailApp` e de execução: consulte a documentação do Google vigente. Notificação que falhar fica `notification_status=failed`; execute `reenviarNotificacoesPendentes`.
11. **Retenção:** com a política aprovada, defina `UNQUALIFIED_LEAD_RETENTION_DAYS` (preenche `retention_review_at` dos novos registros) e agende `sinalizarRetencaoVencida` (só **sinaliza** no `Audit`; excluir/anonimizar é decisão humana segundo a política).

## Comportamento
- Entrada: `POST` com corpo JSON como `text/plain` (`{"action":"submit"|"details","data":{...}}`). Sem parâmetros pessoais na URL, sem JSONP.
- Valida tudo de novo (listas fechadas, limites, formatos), confere UF, município (código IBGE dentro da UF) e país contra tabela do projeto, rejeita campos desconhecidos, mascara CPF/CNPJ no texto livre, **neutraliza fórmulas** (`= + - @`), grava tudo como texto, nunca devolve dados da planilha.
- Antiabuso em camadas: honeypot invisível; tempo mínimo plausível (4 s); limite global por janela; limite por contato normalizado (só hash, no cache, 3 por 10 min); idempotência; Turnstile opcional (só se houver abuso real; cliente ainda não implementado).
- **Idempotência:** o hash da chave do navegador é gravado; reenvio devolve o mesmo protocolo sem nova linha. `LockService` protege a gravação.
- Protocolo `CRV-AAAA-XXXXXX` (aleatório, sem caracteres ambíguos), nunca o número da linha; o complemento exige o token HMAC.
- Cenário gravado **antes** do e-mail; falha de e-mail não apaga o cenário.
- E-mail interno: protocolo, nome, canal/contato, categoria, localidade e link privado; **sem o relato**. Confirmação ao visitante **desligada**; quando ligada, usa `replyTo = contato@criviaengenharia.com.br` e **nunca falsifica o `From`**: sai da conta executora; para sair "como" `contato@…` essa conta precisa ser a executora ou o endereço precisa ser alias verificado.
- Classificação provisória `score-v3` (máx. 16; A ≥ 10, B ≥ 6, C), sem rejeição automática.
- **Protocolo:** não aparece na tela. E-mail: confirmação automática (`CONFIRMATION_EMAIL_ENABLED=true` + remetente autorizado). WhatsApp: o alerta interno traz a **AÇÃO** de enviar a confirmação com o protocolo; a resposta ao site (`confirmation`) faz a página prometer só o que vai acontecer. Envio automático por WhatsApp exigiria provedor/API contratado (não implementado).

## Limitações conhecidas
- O Web App **não recebe IP nem `Origin`** do visitante: o limite de uso é global e a validação de origem não é possível aqui. Mitigações: honeypot, tempo mínimo, validação, idempotência, limite por contato, Turnstile opcional.
- O tempo mínimo e a chave de idempotência vêm do navegador: são sinais, não provas.
- Tempo de resposta do Apps Script é maior que o de um servidor dedicado (alguns segundos).
- Não testado contra o Google real (sem conta/credenciais): a lógica foi testada em memória com simulações de `Utilities`/`PropertiesService`; Sheets, MailApp, LockService e CacheService **não foram exercitados**.
- Retenção/expurgo automáticos **não implementados** (só a sinalização); upload, agenda e IA desligados.
