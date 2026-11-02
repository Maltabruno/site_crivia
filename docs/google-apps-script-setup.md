# Google Apps Script — configuração

O guia passo a passo (planilha, projeto, Script Properties, implantação, atualização, rollback, cotas) está em
[`google-apps-script/README.md`](../google-apps-script/README.md). Este documento registra o estado e as pendências.

## Estado
| Item | Situação |
|---|---|
| Código (`google-apps-script/*.gs`) | Escrito localmente; **não publicado** |
| Planilha, projeto e implantação no Google | **Não criados** (faltam conta proprietária e autorização) |
| Lógica de validação/classificação/segurança | Testada em memória (17 testes) |
| Sheets, MailApp, LockService, CacheService | **Não exercitados** em ambiente Google real |
| Servidor local `servidor/servidor_leads.py` | Fala o mesmo protocolo; **apenas para desenvolvimento/testes** |

## E-mail oficial `contato@criviaengenharia.com.br`
- Tratado como canal público comercial: `Reply-To`, tela de sucesso, alternativa quando o formulário falha. O `mailto:` leva **apenas o assunto** ("Contato pelo site — Apresentar meu cenário"), nunca a narrativa.
- **Não** é o e-mail de privacidade (`PRIVACY_CONTACT_EMAIL`, pendente), nem o destinatário dos alertas (`NOTIFICATION_EMAIL`, pendente), nem a conta proprietária (`{{GOOGLE_ACCOUNT_OWNER}}`, pendente).
- Remetente: não é falsificado. Ver README (conta executora ou alias verificado).
- Checklist antes de publicar (nada verificado ainda): existência da conta; acesso autorizado; verificação em duas etapas; alias no Workspace; **SPF, DKIM e DMARC** (não alterar DNS sem autorização; não declarar configurados sem verificar); nome de exibição; recuperação da conta; responsáveis; troca de senha e revogação.
- O Aviso de Privacidade cita o endereço apenas como canal comercial e de continuidade do atendimento.

## Pendências de aprovação (separadas)
Conta proprietária · planilha · estrutura do Drive · Aviso e bases legais · retenção · implantação do Apps Script · anti-bot · cookies · analytics · marketing · agenda · upload · commit · deploy.
