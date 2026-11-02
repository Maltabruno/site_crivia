# Inventário de fornecedores e transferência internacional

Nada foi presumido. Uma política de privacidade genérica do fornecedor **não** resolve a transferência internacional: cada linha precisa de análise jurídica e de contrato de tratamento.
Colunas por fornecedor: razão social · país · função · dados recebidos · suboperadores · retenção · segurança · contrato de tratamento · mecanismo de transferência internacional · exclusão possível · documentação pendente.

| Função | Fornecedor atual | Situação |
|---|---|---|
| Hospedagem do site estático | [PENDENTE] | A definir. Para teste local não há fornecedor. |
| Armazenamento e backend (Google Apps Script + Google Sheets + Drive + MailApp) | Google (conta institucional [PENDENTE]) | Arquitetura escolhida; **não implantada**. Requer análise de operador/fornecedor, termos de tratamento, local de armazenamento e transferência internacional. |
| Servidor local de testes (`servidor_leads.py` + SQLite) | Nenhum (máquina de desenvolvimento) | Somente desenvolvimento; não usar em produção. |
| E-mail (alerta interno e confirmação opcional) | Google (MailApp) | Alerta mínimo implementado no Apps Script; confirmação desligada. Exige SPF/DKIM/DMARC verificados para `criviaengenharia.com.br`. |
| CRM | Nenhum | Não integrado; a fila `outbox` prepara a integração. |
| Agenda | Nenhum | `agendaUrl` vazio; só carrega após clique do visitante, sem a narrativa. |
| Antiabuso (Cloudflare Turnstile) | Nenhum | Opcional. Se ativado, incluir no Aviso, tratar transferência internacional e validar no servidor. |
| Analytics | Nenhum | Desligado; só com gerenciador de consentimento. |
| Armazenamento de arquivos | Nenhum | Upload desligado. |
| IA (resumo interno) | Nenhum | `AI_LEAD_SUMMARY_ENABLED=false`, sem implementação. |
| Fontes do site | Arquivos locais (self-hosted) | Sem chamada a terceiros. |

Para cada fornecedor que entrar: preencher a linha, anexar o contrato/DPA, registrar o mecanismo de transferência, atualizar `privacy-data-map.md` e o Aviso de Privacidade.
Não habilitar enriquecimento de dados, IA, analytics, marketing ou armazenamento internacional antes dessa avaliação.
