# Site CRIVIA padrão

Engenharia para decisão. Este repositório guarda o site da CRIVIA Engenharia Consultiva.

**O site oficial é a pasta `site_crivia_padrao/`.** É HTML, CSS e JavaScript simples, sem etapa de construção. Quem abrir o repositório deve começar por ela.

## Como abrir o site

Qualquer uma das três formas serve. As três servem a mesma pasta.

| Onde | O que fazer |
|---|---|
| Windows | Dê dois cliques em `Abrir site.bat`. |
| Git Bash | `python -I Site_crivia.py` |
| VS Code | Menu *Terminal*, *Executar tarefa*, **Abrir Site CRIVIA padrão (porta 8080)** |

O endereço é `http://localhost:8080/index.html`. Para encerrar, feche a janela ou use `Ctrl+C`.

## Como testar

```
python -I -m unittest discover -s tests -v
```

No VS Code: *Terminal*, *Executar tarefa*, **Rodar os testes**. O teste do site confere se todas as páginas, imagens e fontes existem, se o WhatsApp e o e-mail estão certos, se nada do que foi retirado voltou e se o servidor entrega as páginas.

## Mapa das pastas

| Pasta ou arquivo | Para que serve |
|---|---|
| `site_crivia_padrao/` | O site oficial (`index.html`, `aviso-privacidade.html`, `styles.css`, `app.js`, `assets/`). |
| `Site_crivia.py` | Serve o site padrão. Com `--antigo`, gera e serve o site anterior (modelo Auralis). |
| `Abrir site.bat` | Atalho do Windows para abrir o site padrão. |
| `index.html` (raiz) | Leva ao `site_crivia_padrao/`. Serve também para a página do GitHub. |
| `site/`, `assets/`, `cenario/`, `servidor/`, `google-apps-script/` | Site anterior e o que ele usava (formulário e servidor de contatos). Não fazem parte do site padrão. |
| `arquivo/` | Versões antigas guardadas (`index_antigo.html`, backup do `Site_crivia.py`). |
| `docs/` | Documentos do site anterior e o fluxo de trabalho (`docs/fluxo-de-trabalho.md`). |
| `tests/` | Testes automáticos. |

## Regras do projeto

- O ramo principal se chama **`main`**. Não existe `master`.
- Nada vai para a hospedagem sem o OK de Bruno Malta.
- Não inventar números. Os valores dos painéis do site são **exemplo ilustrativo** até haver confirmação.
- O Aviso de Privacidade está **em revisão jurídica**. Não afirmar conformidade com lei alguma.
- O contato é feito por WhatsApp e e-mail. Não há formulário nem servidor de contatos no site padrão.

## Contato e conteúdo que não mudam sem decisão

- WhatsApp: `5527996971800`, definido em `WHATS` no `site_crivia_padrao/app.js`.
- E-mail: `contato@criviaengenharia.com.br`.
- Localização no rodapé: Serra, Espírito Santo, Brasil.

Para o passo a passo de Git, VS Code e GitHub, veja `docs/fluxo-de-trabalho.md`.
