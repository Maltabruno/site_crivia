# Experiência e Resultados — como manter

A dobra "Experiência e Resultados" da página inicial e as páginas individuais saem de **um único arquivo**: `experiencias.json`.
Ninguém edita os cartões nem as páginas à mão.

## Incluir um caso novo

1. Prepare a história e confira o que os documentos sustentam.
2. Confirme a confidencialidade e as autorizações necessárias.
3. Copie um bloco de `experiencias.json`, troque o `id` (letras minúsculas, sem acento, com hífen) e os textos.
4. Escolha o desenho em `visuais/` (ou crie um novo `.svg` no mesmo estilo).
5. Marque `"autorizada": true` e `"publicada": true`. Use `"na_home": true` para o cartão aparecer na página inicial.
6. Dê dois cliques em `Gerar experiencias.bat` (pasta acima desta).
7. Confira no navegador e só então publique.

## Regras

- Só entra no site o caso com `autorizada` **e** `publicada` em `true`. Se um deles virar `false`, a página do caso é apagada na próxima geração.
- O repositório é público no GitHub. Caso ainda não aprovado **não** entra em `experiencias.json`: guarde o rascunho em `experiencias/rascunhos/`, que não é enviada.
- Não use nome de contratante, de pessoa, CNPJ, valor de contrato nem resultado sem documento.
- Experiência anterior à CRIVIA é sempre "Experiência profissional do fundador da CRIVIA", com a nota de transparência.
- O texto de abertura da dobra diz "duas experiências". Ao incluir a terceira, ajuste essa frase em `site_crivia_padrao/index.html`.
- `competencia_central` é anotação interna: cada caso deve demonstrar uma capacidade diferente. Não aparece no site.

## Arquivos

- `experiencias.json` — textos e situação de cada caso.
- `visuais/*.svg` — composições gráficas (desenho institucional, não é registro do empreendimento).
- `../scripts/gerar_experiencias.py` — monta os cartões em `index.html` e as páginas em `site_crivia_padrao/experiencias/`.
