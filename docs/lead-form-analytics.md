# Analytics do funil — "Apresentar meu cenário"

**Estado atual: desligado.** `analyticsEnabled=false` em `cenario/config.js` e não existe nenhum fornecedor de analytics no site. O código só dispara um evento do navegador (`crivia:evento`) quando houver **consentimento aplicável** (`window.CRIVIA_CONSENT.analytics === true`) e a configuração estiver ligada. Quando existir um gerenciador de consentimento e um fornecedor, basta ouvir `crivia:evento`.

## Eventos (sem dados pessoais)

| Evento | Quando |
|---|---|
| `scenario_view` | página carregada |
| `scenario_start` | clique em "Começar" |
| `scenario_step_complete` | etapa validada (parâmetros: `step`, `branch`) |
| `scenario_branch_selected` | escolha da situação (etapa 1) |
| `scenario_validation_error` | erro ao avançar (`step`, `errorType`) |
| `scenario_submit_success` | envio aceito pelo servidor (`duration` arredondada) |
| `scenario_submit_error` | falha no envio (`errorType`: `validation`, `network`, `server`, `rate`) |
| `scenario_details_started` / `scenario_details_completed` | complemento opcional |
| `scenario_schedule_view` / `scenario_schedule_booked` | agenda (só quando configurada) |

Parâmetros permitidos (lista fechada em `cenario.js`): `step`, `branch` (categoria genérica), `device` (mobile/tablet/desktop), `origin`, `productHint`, `errorType`, `duration`.
**Nunca** enviar: narrativa, nome, telefone, e-mail, empresa, cidade ligada a contato, identificador que aponte para o titular, valores de campos.

## Métricas a acompanhar (sem metas fixas)
Visualização → início · início → conclusão · abandono por etapa · tempo mediano · erros por tipo · percentual de contatos úteis · agendamentos · comparecimento · propostas · contratações.
Os dados de comparecimento, proposta e contratação vêm de operação interna, não do navegador. Não adotar números de referência de mercado como meta automática: definir metas depois de coletar dados próprios.
O microtexto "Leva cerca de 2 minutos" é uma hipótese: medir o tempo mediano real e ajustar (`microtexto` em `config.js` e `CRIVIA_CTA_MICRO` no gerador).
