# Roteiro de teste manual — "Apresentar meu cenário"

Use **dados fictícios** e uma planilha/servidor de TESTE. Nunca teste com leads reais nem contra a planilha de produção.
Servidor local: `python -I servidor/servidor_leads.py` (porta 8787) e o site em `http://localhost:8080/assets/overview/apresentar-cenario.html`.

## Funcional
1. Página única, sem barra de etapas; ao escolher a situação aparece **uma** pergunta curta (opcional, com "Ainda não sei").
2. Escolher o perfil revela a pergunta de participação.
3. Brasil: Estado → Cidade (desabilitada até escolher o estado; busca sem acento/maiúsculas, teclado ↑ ↓ Enter Esc); trocar o estado **limpa a cidade** e anuncia a mudança.
4. Exterior: País (busca), Cidade (texto), Região (opcional). Escolher "Brasil" na lista de países volta ao modo Brasil e leva o foco ao Estado.
5. Trocar Brasil ↔ Exterior e enviar: o que foi preenchido no outro modo não vai no envio.
6. WhatsApp como canal (campo de WhatsApp obrigatório); E-mail como canal; "Informar também…" abre o segundo canal (opcional).
7. Enviar vazio: resumo de erros com links que levam ao campo; cada campo mostra o erro perto.
8. Relato com 1.201 caracteres: o contador avisa e o envio é bloqueado **sem cortar o texto**.
9. Desligar o servidor (ou usar endpoint errado) e enviar: mensagem de falha, **nada digitado se perde**, botão volta ao normal. Ligar e reenviar: sucesso (sem protocolo na tela).
10. Clique duplo rápido no botão: um único registro.
11. Perguntas opcionais ("Para adiantar a análise"): recolhível; podem ficar em branco; **múltipla escolha** com caixas, "Marcar todas" e "Limpar" em cada pergunta. Sucesso: **sem protocolo na tela**, com aviso de que a confirmação segue ao e-mail ou ao WhatsApp escolhido; "Voltar ao início do site" leva à Hero.
11b. Múltipla escolha em situação, perfil e nas cinco opcionais: marcar várias; "Marcar todas" não marca as exclusivas ("Outra situação", "Sem urgência definida", "Ainda não sei", "Prefiro não informar", "Indiferente");
marcar uma exclusiva desmarca as outras e vice-versa; "Limpar" zera só aquela pergunta; a pergunta curta de contexto só aparece com **uma** situação marcada. Enviar e conferir que cada opção marcada aparece em `lead_answers` (servidor local) ou na aba `Respostas` (Apps Script de teste).
12. Atualizar a página no meio do preenchimento: o rascunho volta (mesma aba); após o sucesso o rascunho some.
13. Com `?origem=hero&utm_source=teste` na URL: aparecem no registro; sem parâmetros, ficam vazios.

## Segurança (servidor local; `python -I -m unittest discover -s tests -v`)
Cobertos pelos testes automáticos: payload grande, campo inesperado, HTML no relato, `=` `+` `-` `@` (Apps Script), honeypot, envio rápido demais, token inválido no complemento, país inválido,
município adulterado ou de outra UF, repetição, erros sem detalhes internos, logs sem conteúdo do formulário.

## Acessibilidade
Percorrer tudo só com teclado; foco visível; mensagens de erro anunciadas (`role="alert"`); combobox anuncia a quantidade de resultados; zoom 200% sem perda; `prefers-reduced-motion`; alvos de toque ≥ 44 px no celular.

## Larguras
360×800, 390×844, tablet (768×1024), 1280×800 e desktop largo. Sem rolagem horizontal.

## Apps Script (só em planilha de TESTE)
`rodarTestes` → gravar um cenário de teste → conferir colunas, telefone como texto, `city_code` como texto, `legal_basis_code=[VALIDAR_BASE_LEGAL]`, Audit sem dados pessoais → e-mail interno sem relato →
confirmação ao visitante desligada → `sinalizarRetencaoVencida` em modo de teste → planilha e pasta **privadas**.
