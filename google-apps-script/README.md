# Backend sem servidor — Google Apps Script + Google Sheets

Estes arquivos são **cópia local, não publicada**. Nenhum recurso Google foi criado e nenhum deploy foi feito.
O front-end nunca acessa a planilha: ele envia o formulário ao Web App, que valida, grava e responde só `{ok, publicCode, detailsToken}`.

## Pré-requisitos (decisões suas, pendentes)
- `{{GOOGLE_ACCOUNT_OWNER}}`: conta **institucional** (Workspace da CRIVIA, com verificação em duas etapas e recuperação configurada) que será dona da planilha, do projeto Apps Script e das pastas. Não use conta pessoal, de agência ou de prestador; se for a única opção, registre como risco e peça autorização antes.
- Quatro e-mails com finalidades **diferentes** (não presumir que são o mesmo):
  | Propriedade | Para quê | Situação |
  |---|---|---|
  | `CONTACT_REPLY_EMAIL` | responde ao visitante (Reply-To, tela de sucesso/erro) | **`contato@criviaengenharia.com.br`** (fixo em `Config.gs` e `cenario/config.js`) |
  | `NOTIFICATION_EMAIL` | alerta interno de novo cenário | pendente |
  | `PRIVACY_CONTACT_EMAIL` | solicitações de titulares (LGPD) | `{{PENDENTE_DE_DEFINICAO}}` |
  | conta proprietária | dona dos recursos Google | pendente |

## Passo a passo (manual)
1. **Planilha:** no Drive institucional, crie "CRIVIA — Cenários recebidos pelo site". Compartilhamento **Restrito**; sem link público, sem publicar na web. Anote o ID (trecho entre `/d/` e `/edit` da URL).
2. **Projeto:** na planilha, *Extensões > Apps Script* (ou crie um projeto avulso). Copie cada `.gs` e o `appsscript.json` (ative *Mostrar arquivo de manifesto* em Configurações do projeto). Não usamos `clasp`.
3. **Script Properties** (Configurações do projeto > Propriedades do script): `SPREADSHEET_ID`, `NOTIFICATION_EMAIL`, `PRIVACY_NOTICE_VERSION` (obrigatórias; sem elas o Web App recusa tudo). Opcionais: `PRIVACY_CONTACT_EMAIL`, `ALLOWED_SITE_ORIGIN`, `TURNSTILE_SECRET_KEY`, `LEAD_RETENTION_POLICY_ID`, `UNQUALIFIED_LEAD_RETENTION_DAYS`, `SECURITY_LOG_RETENTION_DAYS`, `UPLOAD_RETENTION_DAYS`, `DRIVE_ROOT_FOLDER_ID`, `SECURE_UPLOAD_FOLDER_ID`, `ENVIRONMENT`. Recursos desligados por padrão (só valem se a propriedade for exatamente `true`): `SECURE_UPLOAD_ENABLED`, `AI_LEAD_SUMMARY_ENABLED`, `CALENDAR_ENABLED`, `CONFIRMATION_EMAIL_ENABLED`. **Não preencha valores jurídicos fictícios.**
4. **Preparar a planilha:** no editor, execute `prepararPlanilha` (cria as abas `Cenarios`, `Historico`, `Consentimentos`, `Listas`, `Indicadores`, `Configuracao`, `Erros_Operacionais`). Autorize os escopos pedidos.
5. **Testes (sem tocar a produção):** execute `rodarTestes` (17 testes em memória). Testes de gravação só em planilha de TESTE separada.
6. **Implantar:** *Implantar > Nova implantação > App da Web*; executar como **você (proprietário)**; acesso **Qualquer pessoa** (necessário para o formulário público; o endpoint só aceita o JSON do formulário e nunca devolve dados). Copie a URL `.../exec`.
7. **Ligar o site:** gere o site com `CRIVIA_LEAD_ENDPOINT` apontando para essa URL:
   ```bash
   CRIVIA_LEAD_ENDPOINT="https://script.google.com/macros/s/SEU_ID/exec" python -I Site_crivia.py --no-browser --port 8080
   ```
   (a política CSP da página já inclui `script.google.com` e `script.googleusercontent.com`).
8. **Atualizar:** *Implantar > Gerenciar implantações > Editar > Nova versão*. A URL não muda.
9. **Revogar / rollback:** *Gerenciar implantações > Arquivar* (o formulário passa a mostrar a mensagem de falha com o e-mail alternativo) ou voltar para uma versão anterior da implantação. Para trocar o `TOKEN_SECRET`, apague a propriedade (invalida os links de complemento em aberto).
10. **Monitorar:** *Execuções* (logs sem corpo de formulário) e a aba `Erros_Operacionais`. Cotas de `MailApp` (conta Workspace ~1.500 destinatários/dia; conta gratuita ~100) e de execução: consulte a documentação do Google vigente. Notificação que falhar fica `notification_status=failed`; execute `reenviarNotificacoesPendentes`.

## Comportamento
- Entrada: `POST` com corpo JSON como `text/plain` (`{"action":"submit"|"details","data":{...}}`). Sem GET, sem parâmetros pessoais na URL, sem JSONP.
- Valida tudo de novo (enums, limites, formatos), mascara CPF/CNPJ no texto livre e marca o registro, **neutraliza fórmulas** (`= + - @`), grava tudo como texto, nunca devolve dados da planilha.
- **Idempotência:** o hash da chave do navegador é gravado; reenvio devolve o mesmo código sem nova linha. `LockService` protege a gravação.
- Código público `CRV-AAAA-XXXXXX` (aleatório, sem ambíguos) e UUID interno (não exposto).
- Cenário + consentimento + histórico gravados juntos; **e-mail só depois**; falha de e-mail não apaga o cenário.
- E-mail interno mínimo (sem narrativa/contato). Confirmação ao visitante **desligada** (`CONFIRMATION_EMAIL_ENABLED`); quando ligada, usa `replyTo = contato@criviaengenharia.com.br` e **nunca falsifica o `From`**: sai da conta executora; para sair "como" `contato@…` essa conta precisa ser a executora ou o endereço precisa ser alias verificado.
- Classificação provisória `score-v1` (A ≥ 10, B ≥ 6, C), sem rejeição automática.

## Limitações conhecidas
- O Web App **não recebe IP nem `Origin`** do visitante: o limite de uso é global (30 envios/10 min) e a validação de origem não é possível aqui. Mitigações: honeypot, validação, idempotência, Turnstile opcional (cliente ainda não implementado).
- Tempo de resposta do Apps Script é maior que o de um servidor dedicado (alguns segundos).
- Não testado nesta sessão contra o Google real (sem conta/credenciais): a lógica foi testada em memória com simulações; Sheets, MailApp, LockService e CacheService **não foram exercitados**.
- Retenção/expurgo **não implementados** (dependem de política aprovada); upload e agenda desligados.
