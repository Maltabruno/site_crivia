# -*- coding: utf-8 -*-
"""Gera o bloco do catálogo em site_crivia_padrao/app.js a partir de site_crivia_padrao/catalogo-publico.json.

    python -I scripts/gerar_catalogo.py

A projeção pública (R02) é a fonte. O bloco entre CATALOGO:INICIO e CATALOGO:FIM do app.js
não deve ser editado à mão. Só biblioteca padrão.
"""
import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site_crivia_padrao"
JSON_PUBLICO = SITE / "catalogo-publico.json"
APP = SITE / "app.js"
INICIO = "/* CATALOGO:INICIO"
FIM = "/* CATALOGO:FIM */"


def js(valor):
    return json.dumps(valor, ensure_ascii=False, separators=(", ", ": "))


def bloco(dados):
    catalogo = [o for o in dados["ofertas"] if o["tipo"] == "catalogo"]
    entradas = [o for o in dados["ofertas"] if o["tipo"] == "entrada"]
    linhas = [f"{INICIO} — gerado por scripts/gerar_catalogo.py a partir de catalogo-publico.json (revisão {dados['versao']}). Não editar à mão. */"]
    linhas.append("const PRODUTOS = [")
    linhas += [f"  {js(o)}{',' if i < len(catalogo) - 1 else ''}" for i, o in enumerate(catalogo)]
    linhas.append("];")
    linhas.append("const ENTRADAS = [")
    linhas += [f"  {js(o)}{',' if i < len(entradas) - 1 else ''}" for i, o in enumerate(entradas)]
    linhas.append("];")
    linhas.append("const GRUPOS = [")
    linhas += [f"  {js(g)}{',' if i < len(dados['grupos']) - 1 else ''}" for i, g in enumerate(dados["grupos"])]
    linhas.append("];")
    linhas.append(FIM)
    return "\n".join(linhas)


def main():
    dados = json.loads(JSON_PUBLICO.read_text(encoding="utf-8"))
    texto = APP.read_text(encoding="utf-8")
    padrao = re.compile(re.escape(INICIO) + r".*?" + re.escape(FIM), re.S)
    if not padrao.search(texto):
        raise SystemExit("Marcadores CATALOGO:INICIO/FIM não encontrados em app.js")
    novo = padrao.sub(lambda _m: bloco(dados), texto, count=1)
    APP.write_text(novo, encoding="utf-8", newline="\n")
    print("app.js atualizado:", sum(o["tipo"] == "catalogo" for o in dados["ofertas"]), "cards,",
          sum(o["tipo"] == "entrada" for o in dados["ofertas"]), "entradas,", len(dados["grupos"]), "grupos")


if __name__ == "__main__":
    main()
