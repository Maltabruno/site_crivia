# Analytics do funil — "Apresentar meu cenário"

**Estado atual: desligado.** `analyticsEnabled=false` em `cenario/config.js` e não existe nenhum fornecedor de analytics no site. O código só dispara um evento do navegador (`crivia:evento`) quando houver **consentimento aplicável** (`window.CRIVIA_CONSENT.analytics === true`) e a configuração estiver ligada. Quando existir um gerenciador de consentimento e um fornecedor, basta ouvir `crivia:evento`.

## Eventos (sem dados pessoais)

| Evento | Quando |
|---|---|
| `scenario_view` | página carregada |
| `scenario_branch_selected` | escolha da situação principal (parâmetro: `branch`) |
| `scenario_validation_error` | erro ao tentar enviar (`errorType`) |
| `scenario_submit_success` | envio aceito pelo servidor (`duration` arredondada) |
| `scenario_submit_error` | falha no envio (`errorType`: `validation`, `network`, `server`, `rate`) |
| `scenario_schedule_view` / `scenario_schedule_booked` | agenda (só quando configurada) |

A página é única (sem etapas): não há evento de etapa nem de "começar".
Parâmetros permitidos (lista fechada em `cenario.js`): `branch` (categoria genérica), `device` (mobile/tablet/desktop), `origin`, `productHint`, `errorType`, `duration`.
**Nunca** enviar: narrativa, nome, telefone, e-mail, empresa, cidade ligada a contato, identificador que aponte para o titular, valores de campos.

## Métricas a acompanhar (sem metas fixas)
Visualização → início · início → conclusão · abandono (página vista sem envio) · tempo mediano · erros por tipo · percentual de contatos úteis · agendamentos · comparecimento · propostas · contratações.
Os dados de comparecimento, proposta e contratação vêm de operação interna, não do navegador. Não adotar números de referência de mercado como meta automática: definir metas depois de coletar dados próprios.
O microtexto "Leva cerca de 1 minuto" é uma hipótese: medir o tempo mediano real e ajustar (`microtexto` em `config.js` e `CRIVIA_CTA_MICRO` no gerador).
