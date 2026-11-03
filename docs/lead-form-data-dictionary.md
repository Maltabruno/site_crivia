# Dicionário de dados — formulário "Apresentar meu cenário" (página única)

Versão do esquema: **3** · Regra de pontuação: **score-v3** · Fonte da verdade: `servidor/regras_leads.py` e `google-apps-script/Validation.gs`
(o navegador usa `cenario/regras.js`, com os mesmos códigos). Os códigos internos são estáveis; os textos mostrados ao visitante ficam só em `cenario/regras.js`.

O formulário é **uma única página**: situação → (pergunta curta opcional) → perfil e participação → localização → relato → contato → envio.
O visitante **não escolhe produto** (P01–P12, CV01): a CRIVIA faz o enquadramento depois, como hipótese de triagem.

## Campos enviados

| Bloco | Campo | Obrigatório | Valores / regra |
|---|---|---|---|
| `scenario` | `situationCodes` | sim, ao menos 1 (**múltipla escolha**) | `obra_contrato_dificuldade`, `atraso_custo_margem`, `projeto_terreno_propostas`, `planejamento_recursos_recuperacao`, `medicao_alteracao_documentacao`, `vistoria_recebimento_conferencia`, `comunicacao_ia_3d`, `outra_nao_sei` (exclusiva) |
| | `contextAnswers` | não | objeto `{situação: resposta}`: a pergunta curta de **cada situação marcada** (todas têm `unknown` = "Ainda não sei"). Chave de situação não marcada ou resposta de outra situação é rejeitada (`valor_invalido`, sem reproduzir a chave). Desmarcar a situação remove a resposta |
| | `audienceProfiles` | sim, ao menos 1 (**múltipla escolha**) | `company_manager`, `contractor`, `owner_investor`, `technical_team`, `other` |
| | `decisionRole` | sim | `decides`, `recommends`, `gathering`, `referring`, `other_unsure` |
| | `narrative` | sim | texto livre de 10 a 1.200 caracteres; sem HTML; quebras de linha preservadas |
| | `urgencies` | não (múltipla) | `immediate`, `this_week`, `this_month`, `undefined` (exclusiva) — "Quando essa decisão precisa avançar?" |
| | `consequences` | não (múltipla, sem limite) | `penalty`, `stoppage`, `margin_cash_loss`, `technical_quality_risk`, `contract_conflict`, `decision_without_information`, `other` |
| | `documents` | não (múltipla) | `yes`, `partial`, `no`, `unknown` (exclusiva); só a indicação, não há upload |
| | `estimatedRanges` | não (múltipla) | `up_to_100k`, `100k_to_1m`, `1m_to_10m`, `10m_to_50m`, `above_50m`, `undisclosed` e `unknown` (exclusivas); faixas provisórias |
| `scenario.location` | `type` | sim | `brazil` ou `international` |
| (Brasil) | `stateCode`, `cityCode` | sim | UF (27) e código IBGE de 7 dígitos **do município dentro da UF** (conferido contra a tabela do IBGE); `cityName` opcional e, se vier, deve ser o oficial; `countryCode` opcional e só `BR` |
| (Exterior) | `countryCode`, `cityName` | sim | ISO 3166-1 alfa-2 (lista local; `BR` é rejeitado: usar o modo Brasil) e cidade (até 80); `foreignRegion` opcional (até 80) |
| `contact` | `name` | sim | 2 a 120 caracteres |
| | `organization` | não | até 120 |
| | `contactPeriods` | não (múltipla) | `morning`, `afternoon`, `evening`, `any` (exclusiva) |
| | `preferredChannel` | sim | `whatsapp` ou `email` |
| | `phone` / `email` | o do canal escolhido | o segundo canal é opcional, mas, se informado, é validado. Telefone vira E.164 (brasileiro com/sem +55 ou internacional) |
| `privacy` | `privacyNoticeVersion`, `acknowledged` | sim | `acknowledged=true` registra que o aviso foi apresentado e o visitante o conhece; **não** é a base legal |
| | `marketingConsent` | não | **sem caixa no formulário**: o site não envia o campo e o servidor assume `false` (campo mantido só por compatibilidade) |
| `source` | `originCta`, `productHint`, `utm*`, `referrer`, `deviceCategory` | não | só valores das listas; `referrer` = apenas o domínio |
| topo | `idempotencyKey`, `schemaVersion=3`, `formVersion`, `elapsedMs`, `website` (armadilha) | chave e tempo: sim | `elapsedMs` < 4.000 ms é recusado (sinal contra robôs, não prova); `website` preenchido = resposta neutra, nada é gravado |

### Múltipla escolha

Situação, perfil e as cinco perguntas opcionais aceitam **mais de uma opção** (caixas de seleção, com "Marcar todas" e "Limpar" em cada pergunta). O servidor ignora repetições, devolve os códigos na ordem da lista e rejeita:
valor fora da lista (`valor_invalido`), lista vazia em situação ou perfil (`obrigatorio`) e uma opção **exclusiva** misturada com outras (`opcoes_incompativeis`). "Marcar todas" não marca as exclusivas.
Opções exclusivas (não combinam com as demais): `outra_nao_sei`, `undefined` (urgência), `unknown` (documentos), `undisclosed` e `unknown` (faixa), `any` (período).
Pontuação: vale a opção de maior peso marcada. Produtos candidatos: união dos produtos de cada situação, sem repetir.

Qualquer campo fora destas listas é rejeitado (`campo_desconhecido`). Trocar Brasil ↔ Exterior não envia campos residuais do outro modo.
Se o texto livre tiver padrão de CPF ou CNPJ, o trecho vira `[removido]` e o registro fica com `sensitiveContentSuspected=true`.

Não são gravados: IP, User-Agent completo, fingerprint, GPS, CEP, endereço completo, CPF, RG, documentos, dados bancários. A localização é a **do cenário**, não a residência.

## Perguntas opcionais e protocolo

As perguntas opcionais ("Para adiantar a análise") ficam **na mesma página**, em bloco sempre visível (não abre nem fecha), e vão no envio principal. Não existe mais passo extra depois do envio.
O **protocolo não aparece na tela**: a confirmação com o protocolo segue ao canal escolhido. E-mail: automática (Apps Script, só com `CONFIRMATION_EMAIL_ENABLED=true` e remetente autorizado). WhatsApp: **enviada pela equipe** (o alerta interno traz a ação e o número); não há envio automático por WhatsApp sem um provedor/API contratado.
A resposta do servidor informa `confirmation` (`email`, `whatsapp` ou `none`) e a página só promete o que de fato vai acontecer. A ação `details` (complemento por token) continua no backend, mas a página atual não a usa.

## Aba `Leads` do Google Sheets (uma linha por cenário)

`submission_id` (protocolo `CRV-AAAA-XXXXXX`), `created_at`, `updated_at`, `status`, `situation_code/label`, `context_question_code/answer_code/answer_label` (uma entrada por situação marcada respondida, na mesma ordem e separadas por ` | `),
`audience_profile_code/label` (nas colunas de múltipla escolha os valores vêm na mesma célula, separados por ` | `), `decision_role_code/label`, `location_type`, `country_code/name`, `state_code/name`, `city_code/name`, `foreign_region`, `scenario_description`,
`contact_name`, `organization_name`, `preferred_channel`, `whatsapp`, `email`, `privacy_notice_version`, `privacy_notice_acknowledged_at`, `legal_basis_code` (**`[VALIDAR_BASE_LEGAL]`** até decisão jurídica),
`marketing_consent`, `marketing_consent_at`, `source_page`, `source_cta`, `utm_*`, `referrer_domain`, `optional_urgency/documents/contact_period/consequences/estimated_range`, `assigned_to`, `internal_notes`,
`retention_review_at` (vazio até existir prazo aprovado), `deletion_or_anonymization_at`; técnicas ao final: `priority`, `candidate_products`, `missing_information`, `idempotency_key_hash`, `notification_status`, `form_version`, `schema_version`, `sensitive_content_suspected`, `score_json`.

### Aba `Respostas` (formato "longo")

Uma linha por opção marcada: `submission_id`, `question`, `code`, `label`, `position`. Uma pessoa que marca 3 consequências gera 3 linhas com o mesmo `submission_id`.
Perguntas (`question`): `situation`, `context:<situação>` (uma por situação marcada que teve resposta), `audience_profile`, `decision_role`, `urgency`, `consequence`, `documents`, `estimated_range`, `contact_period`. Só códigos e rótulos fixos (nada digitado).
Serve para contar, filtrar e cruzar (tabela dinâmica, `COUNTIF`) sem separar texto; a aba `Leads` continua com uma linha por cenário.
No servidor de testes (SQLite) é a tabela `lead_answers` (`lead_id`, `question`, `code`, `label`, `position`), apagada junto com o lead no descarte.

Status: Novo · Em análise · Aguardando informação · Contatado · Qualificado · Proposta em preparação · Proposta enviada · Não aderente · Encerrado (rótulos de acompanhamento, **não** promessa de contratação).
Telefone, códigos de município e identificadores são gravados como **texto**; valores iniciados por `=`, `+`, `-`, `@` recebem apóstrofo (sem injeção de fórmula). `internal_notes` nunca é exposto pelo endpoint. Abas `Config` (não sigilosa) e `Audit` (evento, protocolo, ator, resultado; sem relato, telefone ou e-mail).

## Localidades (IBGE)

Arquivos locais em `cenario/data/locations/` (`states.json`, `municipalities/{UF}.json`, `countries.json`), carregados **por UF, sob demanda**; a página nunca chama o IBGE.
Regenerar: `python scripts/gerar_localidades.py` (ver `cenario/data/locations/README.md`). A mesma tabela alimenta `google-apps-script/Municipios.gs` (arquivo gerado) e o servidor de testes.
Em relatórios agregados, preferir país e UF; não expor a cidade ligada ao contato sem necessidade operacional.

## Pontuação (`score-v3`) — só prioridade e encaminhamento

| Critério | Faixa | Regra provisória |
|---|---|---|
| Aderência | 0–3 | 3 nas situações com tema definido; em "outra / não sei": 2 se o relato tiver 200+ caracteres, senão 1 |
| Participação na decisão | 0–3 | decide 3 · recomenda 2 · levantando informações 1 · indicando 0 · outro 0 |
| Perfil | 0–2 | empreiteira/prestador 2 · empresa/gestor 2 · proprietário/investidor 1 · equipe técnica 1 · outro 0 |
| Detalhe do relato | 0–2 | 200+ caracteres 2 · 80+ caracteres 1 |
| Prazo da decisão | 0–2 | imediata ou nesta semana 2 · neste mês 1 · indefinido/não informado 0 |
| Consequência | 0–2 | alguma escolhida 1 + consequência alta (multa, paralisação, perda de caixa, conflito contratual) 1 |
| Prontidão | 0–2 | documentos: sim 2 · parcialmente 1 · não/não sei 0 |

Prioridade (máx. 16): total ≥ 10 = **A**, ≥ 6 = **B**, abaixo = **C**. Valores em `PONTUACAO` (`regras_leads.py`) e `PONTUACAO_` (`Classification.gs`); a versão da regra é gravada em cada registro.
A pontuação **nunca** rejeita, bloqueia ou descarta um contato e não usa porte, valor, localização ou dado sensível. A faixa do empreendimento **não** entra na pontuação (só no registro). Regra provisória: precisa de aprovação do responsável comercial e revisão jurídica (ver `legal-review-checklist.md`; avaliar se configura decisão automatizada).

## Produtos candidatos (hipótese interna, sempre com revisão humana; o visitante não os vê)

obra/contrato com dificuldade→P01 · atraso/custo/margem→P08, P07 · projeto/terreno/propostas→P02, P03, P05 · planejamento/recuperação→P06, P07 ·
medição/alteração/documentação→P09, P12 · vistoria/recebimento→P11 · comunicação IA/3D→CV01 · outra/não sei→nenhum (a revisão humana define).
O interesse que vem do botão (`interesse=P06`) é só uma pista em `source.productHint`: não define a situação.

## Notificação interna e confirmação

Alerta interno (Apps Script): protocolo, nome, canal e contato, categoria, país/UF/cidade, prioridade e link privado da planilha. **O relato completo não vai no e-mail.**
Confirmação com o protocolo: ver a seção "Perguntas opcionais e protocolo".
