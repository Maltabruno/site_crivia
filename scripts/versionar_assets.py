# -*- coding: utf-8 -*-
"""Atualiza o parâmetro ?v= de styles.css e app.js no index.html com um resumo do conteúdo de cada arquivo.

    python -I scripts/versionar_assets.py

Rode depois de editar styles.css ou app.js e antes de publicar: sem isso o navegador pode servir a versão antiga em cache.
Só biblioteca padrão.
"""
import hashlib
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site_crivia_padrao"
ARQUIVOS = ("styles.css", "app.js")


def versao(nome):
    return hashlib.sha1((SITE / nome).read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:8]   # ignora CRLF do Windows


def main():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    for nome in ARQUIVOS:
        html, n = re.subn(re.escape(nome) + r"\?v=[0-9a-z]+", f"{nome}?v={versao(nome)}", html)
        if n != 1:
            raise SystemExit(f"{nome}: esperava 1 referência em index.html, achei {n}")
    (SITE / "index.html").write_text(html, encoding="utf-8", newline="\n")
    print({n: versao(n) for n in ARQUIVOS})


if __name__ == "__main__":
    main()
