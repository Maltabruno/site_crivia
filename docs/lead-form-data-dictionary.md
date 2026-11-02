# Dicionário de dados — formulário "Apresentar meu cenário"

Versão do esquema: **1** · Regra de pontuação: **score-v1** · Fonte da verdade: `servidor/regras_leads.py` (o navegador usa `cenario/regras.js`, com os mesmos valores).

Os valores internos são estáveis e em inglês; os textos mostrados ao visitante ficam só em `cenario/regras.js`.

## Estrutura do registro (`LeadScenario`)

| Bloco | Conteúdo |
|---|---|
| `id`, `schemaVersion`, `createdAt`, `status` | Identificador aleatório (20 caracteres), versão do esquema, data (UTC) e estado (`novo`). |
| `source` | `landingPage`, `referrer` (somente o domínio), `originCta`, `productHint`, `utmSource/Medium/Campaign/Content/Term`, `deviceCategory`. |
| `scenario` | Respostas das etapas 1 a 3 (abaixo). |
| `contact` | Nome, organização, cargo, canal preferido, telefone (E.164), e-mail, segundo canal, período preferido. |
| `privacy` | `privacyNoticeVersion`, `privacyAcknowledgedAt`, `requestedContactChannel`, `marketingConsent` (sempre `false` nesta versão). |
| `qualification` | Pontuações, `priority`, `ruleVersion`, `candidateProducts[]`, `missingInformation[]`. |
| `internalReview` (coluna própria) | `reviewStatus`, `reviewedBy`, `reviewedAt`, `nextAction`, `notes`. |

Não são gravados: IP, User-Agent completo, fingerprint, localização precisa, endereço completo, CPF, RG, documentos, dados bancários.
O IP existe apenas como hash com sal aleatório, em memória, para o limite de requisições; some quando o processo reinicia.

## Campos de `scenario`

| Campo | Obrigatório | Valores internos |
|---|---|---|
| `entryPath` | sim | `underperforming`, `decision_support`, `visual_communication`, `ai_decision_engineering`, `other_or_unsure` |
| `audienceContext` | sim | `contractor`, `large_company`, `owner_investor`, `technical_partner`, `other` |
| `decisionRole` | sim | `decides`, `leads_evaluation`, `technical_participant`, `early_research`, `other` |
| `stage` | rotas A e B | `planning`, `execution`, `delay_or_critical`, `near_completion`, `operation`, `unsure` |
| `issues` (máx. 3) | rota A | `schedule`, `margin_cost`, `measurement_receipt`, `scope_change`, `team_equipment_material`, `project_info`, `quality`, `supplier`, `undefined_responsibilities`, `other` |
| `consequences` (máx. 2) | rotas A, B, D, E | `penalty`, `stoppage`, `margin_cash_loss`, `technical_quality_risk`, `contract_conflict`, `operation_impact`, `decision_without_information`, `other` |
| `decisionHorizon` | sim | `up_to_7_days`, `8_to_30_days`, `31_to_90_days`, `after_90_days`, `undefined` |
| `city` / `state` | sim | texto de 2 a 80 caracteres / uma das 27 UFs |
| `estimatedRange` | não | `up_to_100k`, `100k_to_1m`, `1m_to_10m`, `10m_to_50m`, `above_50m`, `undisclosed`, `unknown` (faixas provisórias e configuráveis) |
| `availableDocuments` | sim | `contract`, `projects`, `schedule`, `budget`, `measurements`, `photos_records`, `process_data`, `none_organized`, `other` |
| `narrative` | sim | texto livre, 10 a 700 caracteres |

### `branchSpecificData` por rota

- **B** `decision_support`: `evaluate[]` (máx. 3): `land`, `projects`, `budget_costs`, `supplier_proposals`, `planning_resources`, `measurement_change`, `handover`, `documentation_databook`, `other`.
- **C** `visual_communication`: `deliverable`, `purpose`, `audience`, `referenceLevel`.
- **D** `ai_decision_engineering`: `aiSituation`, `difficulties[]` (só se `already_using`), `areas[]`, `peopleRange`, `affectedProcess`.
- **E** `other_or_unsure`: `decisionNeeded` (texto, 10 a 500 caracteres).
- **A** `underperforming`: sem campos extras.

Qualquer campo fora destas listas é rejeitado (HTTP 422, `campo_desconhecido`).

## Regras de validação (servidor)

Esquema estrito, listas permitidas, limites de arrays e de tamanho, normalização Unicode (NFC), remoção de caracteres de controle,
organização obrigatória só em contexto empresarial (`contractor`, `large_company`, `technical_partner`), telefone obrigatório para WhatsApp e ligação,
e-mail obrigatório para o canal e-mail (sintaxe apenas; não prova que o endereço é do visitante). Telefone brasileiro (com ou sem +55) e internacional (+ e 8 a 15 dígitos) são aceitos.
Se o texto livre tiver padrão de CPF ou CNPJ, o trecho é substituído por `[removido]` e o registro fica com `sensitiveContentSuspected=true`.

## Pontuação (`score-v1`) — só prioridade e encaminhamento

| Critério | Faixa | Regra provisória |
|---|---|---|
| Aderência ao portfólio | 0–3 | 3 nas rotas A–D; na rota E, 2 se o texto tiver 80 caracteres ou mais, senão 1 |
| Relação com a decisão | 0–3 | decide 3 · lidera 2 · participa tecnicamente 1 · pesquisa inicial 0 · outro 0 |
| Consequência | 0–3 | 1 se houver alguma + 1 se houver consequência alta (multa, paralisação, perda de caixa, conflito contratual) + 1 se houver duas |
| Horizonte | 0–2 | até 30 dias 2 · 31 a 90 dias 1 · depois ou indefinido 0 |
| Prontidão | 0–2 | 3 ou mais tipos de documento 2 · 1 a 2 tipos 1 · nenhum 0 |

Prioridade: total 10–13 = **A**, 6–9 = **B**, 0–5 = **C**. Valores e faixas ficam em `PONTUACAO` (`regras_leads.py`) e a versão da regra é gravada em cada registro.
A pontuação **nunca** rejeita, bloqueia ou descarta um contato e não usa porte, valor, capacidade financeira ou dado sensível. A correção manual é feita na revisão interna.
Esta regra é provisória e precisa de aprovação do responsável comercial e revisão jurídica (ver `legal-review-checklist.md`).

## Produtos candidatos (hipótese de encaminhamento, sempre com revisão humana)

| Entrada | Candidatos |
|---|---|
| Rota A, problema | prazo→P06 · margem/custo→P07 · medição/recebimento→P09 · escopo/alteração→P09 · equipe/equipamento/material→P08 · projeto/informação técnica→P02 · qualidade→P10 · fornecedor→P05 · responsabilidades indefinidas→P01 |
| Rota A, fase | atraso/crítica→P07 · execução→P10 · próximo da conclusão→P11 · planejamento→P06 · "não sei" ou nenhum candidato→P01 |
| Rota B | terreno→P03 · projetos→P02 · orçamento→P04 · propostas→P05 · planejamento→P06 · medição/alteração→P09 · recebimento→P11 · documentação→P12 |
| Rota C | CV01 |
| Rota D | IA (Engenharia de Decisão com IA) |
| Rota E | nenhum (a revisão humana define) |

O visitante não vê estes códigos. O interesse que vem do botão (`interesse=P06`) é só uma pista guardada em `source.productHint`: não define a rota nem o enquadramento.

## Notificação interna e confirmação

A fila `outbox` guarda apenas: identificador do lead, data, categoria (rota) e prioridade. Nenhum dado pessoal vai para a notificação.
O envio de e-mail/WhatsApp de confirmação **não está implementado** (depende de fornecedor e domínio autenticado; ver `vendor-privacy-inventory.md`).
