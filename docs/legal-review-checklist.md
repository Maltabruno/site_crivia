# Checklist de revisão jurídica e operacional

Nenhum item abaixo está concluído. Só marque `[x]` com evidência anexada (documento, contrato, e-mail de aprovação, print).
Esta implementação traz **controles técnicos e documentação preparada para validação jurídica**; ela não afirma conformidade com a LGPD.

## Bloqueadores de publicação (placeholders — não inventar)
Enquanto estes itens não forem definidos/validados pela CRIVIA, **não publicar**:
`[DEFINIR_CNPJ]` · `[DEFINIR_ENDERECO]` (a CRIVIA usa os mesmos dados cadastrais da BM Serviços; falta informar CNPJ e endereço) ·
E-mail de privacidade: **definido pelo responsável como `contato@criviaengenharia.com.br`** (o mesmo canal comercial; tratar na rotina de direitos dos titulares) ·
`[VALIDAR_BASE_LEGAL]` (a coluna `legal_basis_code` grava este marcador) · `[DEFINIR_PRAZO_DE_RETENCAO]` · `[APROVAR_AVISO_DE_PRIVACIDADE]` (a versão começa com "minuta").
Também antes de publicar: responsável interno por pedidos de titulares; operadores (Google e ferramentas); transferência internacional no ambiente Google; processo de revogação do marketing;
regras de acesso, exportação, correção e exclusão; política para arquivos futuros (upload desligado).

## Controlador e responsáveis
- [ ] Dados completos do controlador (razão social, CNPJ, endereço) — preencher em `cenario/aviso-privacidade.html`.
- [ ] Contato de privacidade e canal para solicitações de titulares — preencher `canalPrivacidade` em `cenario/config.js` e no Aviso.
- [ ] Necessidade de encarregado (ou registro da dispensa, quando cabível).

## Base legal e finalidades
- [ ] Base legal por finalidade (resposta ao contato, triagem, pontuação, segurança). Hipóteses candidatas: procedimentos preliminares relacionados a contrato, a pedido do titular; legítimo interesse; consentimento (marketing, se existir).
- [ ] Se legítimo interesse: teste de balanceamento documentado (finalidade, necessidade, legítima expectativa, impacto, salvaguardas, oposição, conclusão).
- [ ] Finalidade por campo (confirmar que cada campo do `lead-form-data-dictionary.md` é necessário).
- [ ] Revisão do aviso curto junto ao botão: "Usaremos seus dados para analisar o cenário, responder ao contato e avaliar uma possível contratação. Consulte o Aviso de Privacidade." (registra a **ciência**, separada da base legal; **não** é consentimento obrigatório genérico).
- [ ] Localização do cenário (país, UF, cidade): finalidade documentada (atendimento, deslocamento, contexto local); em relatórios, país e UF.
- [ ] Avaliar se a pontuação interna configura decisão automatizada e qual o dever de informação/revisão.

## Aviso de Privacidade
- [ ] Revisar a minuta (`cenario/aviso-privacidade.html`, versão `minuta-0`) e preencher todos os `[PENDENTE]`.
- [ ] Definir a versão aprovada e a data de vigência; atualizar `privacyNoticeVersion` em `cenario/config.js` (deixar de começar com "minuta").
- [ ] Decidir onde o Aviso será publicado (URL permanente) e ligar no rodapé do site.

## Retenção e descarte
- [ ] Prazos por categoria: lead sem continuidade, cliente, contrato, logs de segurança, documentos enviados, consentimento de marketing, backup.
- [ ] Definir `LEAD_RETENTION_POLICY_ID`, `LEAD_RETENTION_DAYS`, `UNQUALIFIED_LEAD_RETENTION_DAYS`, `SECURITY_LOG_RETENTION_DAYS`, `UPLOAD_RETENTION_DAYS`.
- [ ] Como a exclusão alcança cópias, integrações e backups.
- [ ] Procedimento de suspensão do descarte por obrigação legal ou exercício regular de direitos (`servidor_leads.py suspender on`).

## Operadores, fornecedores e transferência internacional
- [ ] Preencher `vendor-privacy-inventory.md` (hospedagem, banco, e-mail, CRM, agenda, antiabuso, armazenamento, IA, analytics).
- [ ] Contratos de tratamento com cada operador.
- [ ] Mecanismo de transferência internacional por fornecedor, conforme a regulamentação vigente.

## Cookies, analytics e marketing
- [ ] Confirmar que o site não usa cookies não essenciais (estado atual: nenhum). Antes de qualquer analytics, pixel, chat ou gravação de sessão: gerenciador de consentimento com "Aceitar", "Rejeitar" e "Gerenciar" de mesmo destaque e link permanente de preferências no rodapé.
- [x] Marketing: a caixa de opt-in foi **retirada** do formulário (decisão do responsável); ninguém entra em lista de marketing. Se voltar, exige caixa separada, opcional, desmarcada, registro de consentimento e descadastramento.
- [ ] Aprovar o plano de métricas (`lead-form-analytics.md`).

## Integrações e canais
- [ ] Agenda (provedor, regras operacionais, dados mínimos, carregamento só após clique).
- [ ] CRM e fila com retentativa (hoje: banco local + tabela `outbox`).
- [ ] E-mail de confirmação (domínio autenticado, conteúdo sem narrativa) e WhatsApp (somente para o contato solicitado, sem marketing).
- [ ] IA para resumo interno (`AI_LEAD_SUMMARY_ENABLED=false`): fornecedor, contrato, finalidade, operador e suboperadores, local de processamento, retenção, treinamento, transferência internacional, base legal, aprovação humana.
- [ ] Upload seguro (`SECURE_UPLOAD_ENABLED=false`): arquitetura completa conforme `security-threat-model.md`.

## Direitos dos titulares e incidentes
- [ ] Procedimento de atendimento a solicitações (confirmação, acesso, correção, anonimização/eliminação, portabilidade, informação sobre compartilhamento, revogação, oposição), com verificação de identidade proporcional.
- [ ] Procedimento de incidentes aprovado (`incident-response-checklist.md`) e responsável designado.

## Revisões finais
- [ ] Textos do formulário e da página aprovados.
- [ ] Revisão do texto do Aviso aprovada.
- [ ] Consulta às fontes oficiais vigentes na data da publicação (LGPD, ANPD, resoluções de incidentes e de transferência internacional).
- [ ] Autorização separada para: visual, textos, Aviso, dados jurídicos, analytics, marketing, agenda, IA, upload, commit e publicação.
