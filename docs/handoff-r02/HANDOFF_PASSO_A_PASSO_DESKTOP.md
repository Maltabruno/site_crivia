# Aplicar o Catálogo R02 no desktop — passo a passo

Arquivo do trabalho: `catalogo-r02.patch` (1 commit, 7 arquivos, +871/−82).
SHA-256: `0e3569dddbc044b4cbbfede13dfaf6cbea089f04aff1cbe5fbf844eebdf34198`

Conferido aqui: o patch aplica limpo sobre `a0d7ac5` (HEAD do main) e os 22 testes do site passam depois de aplicar.
Não inclui `integracao.jpg` nem `planejamento.jpg`.

## 1. Colocar o patch no PC
Baixe `catalogo-r02.patch` e salve na pasta do repositório, **fora do que será commitado**, em uma pasta acima do repositório.

## 2. Abrir o Git Bash no repositório
```
cd "<pasta do repositório>"
git status
git log --oneline -1
```
Esperado: HEAD em `a0d7ac5` (se for outro, siga mesmo assim, mas leia o passo 5).

## 3. Guardar as imagens que você alterou (só se aparecerem no `git status`)
```
git stash push -m "imagens experiencias" -- site_crivia_padrao/assets/experiencias/integracao.jpg site_crivia_padrao/assets/experiencias/planejamento.jpg
```
Não use `git add -A` nem `git reset --hard`.

## 4. Criar a branch e aplicar
```
git checkout -b claude/site-adjustments-study-xg2930
sha256sum "../catalogo-r02.patch"     # confira com o SHA acima
git am "../catalogo-r02.patch"
```
Se der erro: `git am --abort` e me mande a mensagem.

## 5. Testar antes de enviar
```
python -I -m unittest discover -s tests -v
node --check site_crivia_padrao/app.js
```
Esperado: todos os testes OK (57 no total na suíte inteira).
Se o `main` do seu PC estiver à frente de `a0d7ac5`, rode também `python -I scripts/gerar_catalogo.py` e veja se o `git status` fica limpo.

## 6. Ver o site
Dê dois cliques em `Abrir site.bat` e abra `http://localhost:8080/index.html`. Confira:
- Catálogo com 4 abas (a quarta: "Requisitos, documentação e entrega ao cliente", 6 cards).
- Bloco "Frente 04" abaixo dos cards, com botão que leva à quarta aba.
- Seções Raio-X, Diagnóstico e Planejamento com "OFERTA 18/19/20".
- Um CTA de cada aba: o assunto sai como "13 — Desempenho e requisitos".
- Celular (F12 → modo dispositivo, 360 px): sem rolagem lateral.

## 7. Enviar para o GitHub
```
git push -u origin claude/site-adjustments-study-xg2930
```
Não abra Pull Request nem faça merge no `main` sem o seu OK: o site publicado é o `main`.

## 8. Recuperar as imagens (se usou o passo 3)
```
git stash pop
```

## Antes de publicar de verdade
- Confirmar responsável, procedimento e capacidade das ofertas 13–17 e 21 (ou marcá-las "em estruturação").
- Corrigir na fonte o campo da oferta 18 que cita um identificador interno em `catalogo-publico.json`.
- Revisar o parágrafo da oferta 20 ("liberação ou retenção") frente ao limite do cadastro.
