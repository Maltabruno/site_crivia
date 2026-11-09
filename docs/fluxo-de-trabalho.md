# Fluxo de trabalho: Git Bash, VS Code e GitHub

Para todos seguirem o mesmo caminho. Pasta do projeto: `G:\Meu Drive\98_site_crivia\site_crivia`.

## 1. Abrir o projeto

- **VS Code:** *Arquivo*, *Abrir Pasta*, escolha `site_crivia` (a pasta que tem a pasta `.git` dentro). Não abra a pasta `98_site_crivia`, que é a de cima.
- **Git Bash:** abra o terminal dentro de `site_crivia`. Confirme com `git rev-parse --show-toplevel`. A resposta deve terminar em `site_crivia`.
- O VS Code usa as tarefas e as configurações da pasta `.vscode/`, que vêm junto com o repositório.

## 2. Antes de começar o dia

```
git pull origin main
```

## 3. Abrir e testar

```
python -I Site_crivia.py
python -I -m unittest discover -s tests -v
```

Os dois também estão como tarefas no VS Code (*Terminal*, *Executar tarefa*).

## 4. Salvar o que foi feito (commit) e enviar (push)

1. Ver o que mudou: `git status`
2. Marcar tudo: `git add -A`
3. Salvar: `git commit -m "Frase curta dizendo o que mudou"`
4. Enviar: `git push origin main`

Regras:
- Sempre o ramo **`main`**. Não existe `master`.
- Rode os testes antes do commit. Se algum falhar, não envie.
- Não coloque senhas, chaves ou dados de clientes no repositório.
- Arquivos grandes (mais de 20 MB) ficam fora do Git.

## 5. Um único repositório

O repositório do GitHub é o da pasta `site_crivia`. Existe uma pasta acima (`98_site_crivia`) com um Git antigo e separado, sem ligação com o GitHub. Não faça `git add`, `commit` nem `push` nela.

## 6. Se algo der errado

- "python não é reconhecido": instale o Python 3 em python.org e marque *Add to PATH*.
- Aviso `LF will be replaced by CRLF`: é só sobre o fim de linha no Windows. O arquivo `.gitattributes` cuida disso. Pode seguir.
- O `git push` foi recusado: rode `git pull origin main`, resolva o que aparecer e envie de novo.
- Dúvida antes de enviar: pare e pergunte. O que foi enviado ao GitHub fica no histórico.
