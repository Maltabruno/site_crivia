# Mapa das operações de tratamento — página "Apresentar meu cenário"

> Documento de apoio para validação jurídica. **Não define base legal.** Tudo que aparece como `[PENDENTE]` precisa ser preenchido e aprovado por quem responde pela CRIVIA.
> Controlador: [PENDENTE: razão social, CNPJ, endereço]. Responsável interno: [PENDENTE]. Encarregado: [PENDENTE: nomear ou registrar a dispensa conforme análise jurídica].

## Operações

| # | Operação | Dados | Titular | Finalidade | Necessidade | Base legal candidata (a validar) | Sistema | Acesso | Compartilhamento | Transferência internacional | Retenção | Descarte | Medidas de segurança | Direitos | Risco |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Resposta às perguntas do cenário | Escolhas de classificação, cidade/UF, documentos existentes, faixa (opcional) | Visitante (pessoa física ou representante) | Entender o cenário e preparar a conversa inicial | Escolhas fechadas reduzem texto livre | [PENDENTE: procedimentos preliminares a pedido do titular · legítimo interesse (exige teste de balanceamento) · outra] | Navegador → servidor de leads → banco | Equipe CRIVIA autorizada [PENDENTE: lista] | Nenhum previsto nesta versão | [PENDENTE: depende da hospedagem] | [PENDENTE: `LEAD_RETENTION_DAYS`] | `servidor_leads.py expurgar` | Validação no servidor, HTTPS (na publicação), logs sem conteúdo | Acesso, correção, eliminação, oposição | Médio: texto livre pode receber dado sensível |
| 2 | Texto livre (narrativa) | Texto escrito pelo visitante | Visitante e terceiros citados | Contexto da decisão | Campo limitado a 700 caracteres, com aviso para não enviar dado sensível | Idem 1 | Idem | Idem | Nenhum | Idem | Idem | Idem | Máscara de CPF/CNPJ + marcação para restrição de acesso | Idem | Alto (conteúdo imprevisível) |
| 3 | Contato | Nome, organização, cargo (opcional), canal, telefone/e-mail, período | Visitante | Responder pelo canal escolhido | Só o campo do canal escolhido é obrigatório | Idem 1 | Idem | Idem | Nenhum; futuro: provedor de e-mail/CRM [PENDENTE] | Idem | Idem | Idem | Idem | Idem | Médio |
| 4 | Origem da visita | Botão de origem, produto de interesse, UTM, categoria do dispositivo, domínio de origem | Visitante | Entender qual conteúdo gera contato | Sem IP, sem User-Agent completo | [PENDENTE] | Idem | Idem | Nenhum | Idem | Idem | Idem | Valores só de listas permitidas | Idem | Baixo |
| 5 | Ciência do Aviso | Versão do aviso e data/hora | Visitante | Prova de qual aviso foi apresentado | Mínimo | [PENDENTE] | Banco | Idem | Nenhum | Idem | Idem | Idem | Idem | Idem | Baixo |
| 6 | Pontuação e enquadramento | Pontuação, prioridade, produtos candidatos | Visitante | Priorizar a ordem de resposta | Regra determinística, sem dado sensível | [PENDENTE] | Banco | Idem | Nenhum | Idem | Idem | Idem | Não rejeita nem decide sozinha; revisão humana | Revisão de decisão automatizada, se aplicável [PENDENTE: parecer] | Médio |
| 7 | Limite de requisições / antiabuso | Hash do IP com sal aleatório (memória), eventos sem conteúdo | Visitante | Segurança do serviço | Hash não é gravado em banco | [PENDENTE] | Processo do servidor; `security_log` | Equipe de operação | Cloudflare Turnstile (somente se ativado) | Sim, se ativado [PENDENTE] | [PENDENTE: `SECURITY_LOG_RETENTION_DAYS`] | `expurgar` | Logs sem PII | Idem | Baixo |
| 8 | Informações adicionais (opcional, pós-envio) | Texto de até 700 caracteres | Visitante | Complementar a conversa | Opcional | Idem 1 | Banco (`details_json`) | Idem | Nenhum | Idem | Idem | Idem | Token por lead (HMAC) | Idem | Médio |
| 9 | Armazenamento no navegador | Escolhas não sensíveis na sessão (`sessionStorage`) | Visitante | Voltar entre etapas | Nome, contatos e texto livre não são guardados | Não aplicável a servidor | Navegador do visitante | Visitante | Nenhum | Não | Até fechar a aba ou enviar | Automático | Limpeza após o envio | Controle do visitante | Baixo |

## Itens fora desta versão (bloqueados por configuração)

Upload de documentos, agenda, e-mail/WhatsApp de confirmação, CRM, analytics, marketing e resumo por IA **não estão ativos**. Cada um exige o preenchimento de `legal-review-checklist.md` e `vendor-privacy-inventory.md` antes de ser ligado.

## Não coletado de propósito

Dados de saúde, biometria, origem racial ou étnica, religião, opinião política, filiação sindical, vida sexual, dados genéticos, dados de crianças e adolescentes, CPF, RG, documentos pessoais, dados bancários, geolocalização, endereço completo.
Se algum chegar no texto livre: não entra na pontuação, o acesso deve ser restringido, pode ser excluído e **não deve** ser reproduzido em notificação nem enviado a IA (procedimento interno: [PENDENTE]).
