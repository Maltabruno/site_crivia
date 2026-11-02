# Checklist operacional de incidente de segurança

Documento de apoio. **Não automatiza comunicação jurídica.** O prazo regulatório e o conteúdo da comunicação devem ser conferidos na norma vigente no momento do incidente (resolução da ANPD sobre comunicação de incidentes; verificar no portal oficial da ANPD). Nenhuma comunicação à ANPD ou aos titulares é feita automaticamente nem antes da validação do responsável designado, salvo procedimento formal aprovado.

Responsável pelo incidente: [PENDENTE] · Suplente: [PENDENTE] · Contato jurídico: [PENDENTE] · Contato de privacidade: [PENDENTE]

1. **Detecção** — registrar quem percebeu, quando e como (alerta, relato, log de segurança, `security_log`). Anotar data e hora (UTC e local).
2. **Contenção** — isolar o que for necessário (desligar o servidor de leads, revogar credenciais, trocar `token_secret` se houver suspeita, bloquear origem). Não apagar nada que sirva de evidência.
3. **Preservação de evidências** — cópia do `leads.db`, dos logs e da configuração; registrar quem teve acesso à cópia.
4. **Avaliação dos dados afetados** — quais campos (contato, texto livre, informações adicionais), quantos registros, período, se houve dado sensível ou de terceiros.
5. **Risco ou dano relevante** — avaliar probabilidade e gravidade para os titulares; registrar o raciocínio.
6. **Titulares** — identificar quais foram afetados e por qual canal seriam contatados.
7. **Fornecedores** — notificar operadores envolvidos e pedir as informações deles (hospedagem, e-mail, CRM, antiabuso).
8. **Cronologia** — linha do tempo única, com horários.
9. **Mitigação** — correções técnicas, rotação de segredos, reforço de acesso; registrar o que foi feito e quando.
10. **Avaliação jurídica** — decidir se há dever de comunicar à ANPD e aos titulares, prazo e conteúdo. Decisão do responsável jurídico, registrada.
11. **Comunicação (somente após a decisão acima)** — ANPD e titulares, conforme a norma vigente.
12. **Registro do incidente** — manter registro interno, mesmo quando não houver comunicação.
13. **Lições aprendidas** — causa raiz, falhas de controle, ações corretivas com responsável e prazo.
