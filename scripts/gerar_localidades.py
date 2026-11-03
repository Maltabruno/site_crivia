#!/usr/bin/env python3
"""Gera os dados de localidade do formulário "Apresentar meu cenário" a partir das APIs oficiais do IBGE.

Executar SOMENTE pela manutenção (a página do visitante nunca chama o IBGE):
    python scripts/gerar_localidades.py

Saídas:
    cenario/data/locations/states.json                 UFs: [[sigla, nome, codigo_ibge], ...]
    cenario/data/locations/municipalities/{UF}.json    municípios da UF: [[codigo_ibge_7_digitos, nome], ...]
    cenario/data/locations/countries.json              países: [[iso2, nome_pt], ...]
    cenario/data/locations/README.md                   fonte e data da geração
    google-apps-script/Municipios.gs                   mesma tabela, para o servidor conferir UF/município/país (arquivo gerado)
"""
import gzip
import json
import re
import sys
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "cenario" / "data" / "locations"
GAS = RAIZ / "google-apps-script" / "Municipios.gs"
IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades"
PAISES = "https://servicodados.ibge.gov.br/api/v1/paises"


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "crivia-gerar-localidades/1.0", "Accept": "application/json", "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=60) as r:   # noqa: S310 (URLs fixas do IBGE)
        bruto = r.read()
    if bruto[:2] == b"\x1f\x8b":
        bruto = gzip.decompress(bruto)
    return json.loads(bruto.decode("utf-8"))


def chave(texto):
    """Ordem alfabética amigável em português: sem acento, sem diferença de caixa."""
    base = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in base if not unicodedata.combining(c)).lower()


def gravar(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")


def main():
    estados = baixar(IBGE + "/estados?orderBy=nome")
    ufs = sorted(([e["sigla"], e["nome"], str(e["id"])] for e in estados), key=lambda x: chave(x[1]))
    if len(ufs) != 27:
        sys.exit("Esperadas 27 UFs, recebidas %d" % len(ufs))
    gravar(SAIDA / "states.json", ufs)

    por_uf = {}
    total = 0
    for sigla, _nome, _cod in ufs:
        municipios = baixar("%s/estados/%s/municipios?orderBy=nome" % (IBGE, sigla))
        lista = sorted(([str(m["id"]), m["nome"]] for m in municipios), key=lambda x: chave(x[1]))
        for codigo, _ in lista:
            if not re.fullmatch(r"\d{7}", codigo):
                sys.exit("Código de município inesperado: " + codigo)
        gravar(SAIDA / "municipalities" / (sigla + ".json"), lista)
        por_uf[sigla] = lista
        total += len(lista)

    paises_brutos = baixar(PAISES)
    paises = []
    for p in paises_brutos:
        iso = (p.get("id") or {}).get("ISO-3166-1-ALPHA-2")
        nome = (p.get("nome") or {}).get("abreviado")
        if iso and nome and re.fullmatch(r"[A-Z]{2}", iso):
            paises.append([iso, nome])
    paises = sorted({p[0]: p for p in paises}.values(), key=lambda x: chave(x[1]))
    if not any(p[0] == "BR" for p in paises):
        sys.exit("Lista de países sem o Brasil: fonte inesperada.")
    gravar(SAIDA / "countries.json", paises)

    (SAIDA / "README.md").write_text(
        "# Localidades do formulário\n\n"
        "- Fonte: API de Localidades do IBGE (%s) e API de Países do IBGE (%s).\n"
        "- Gerado em: %s (%d UFs, %d municípios, %d países).\n"
        "- Como atualizar: `python scripts/gerar_localidades.py` e depois reconstruir o site. A página do visitante nunca chama o IBGE.\n"
        "- Formato: `states.json` = [sigla, nome, código IBGE da UF]; `municipalities/{UF}.json` = [código IBGE (7 dígitos), nome];"
        " `countries.json` = [ISO 3166-1 alfa-2, nome em português].\n"
        "- `google-apps-script/Municipios.gs` é gerado junto: é a tabela que o servidor usa para conferir UF, município e país.\n"
        % (IBGE, PAISES, date.today().isoformat(), len(ufs), total, len(paises)), encoding="utf-8", newline="\n")

    # tabela compacta para o Apps Script: "UF" -> "codigo:nome|codigo:nome"
    linhas = ["/** ARQUIVO GERADO por scripts/gerar_localidades.py em %s a partir do IBGE. Não editar à mão. */" % date.today().isoformat(),
              "var UFS_IBGE_ = " + json.dumps({u[0]: u[2] for u in ufs}, ensure_ascii=False) + ";",
              "var UFS_NOMES_ = " + json.dumps({u[0]: u[1] for u in ufs}, ensure_ascii=False) + ";",
              "var MUNICIPIOS_ = {"]
    for sigla, lista in por_uf.items():
        corpo = "|".join("%s:%s" % (c, n.replace("|", " ")) for c, n in lista)
        linhas.append("  %s: %s," % (json.dumps(sigla), json.dumps(corpo, ensure_ascii=False)))
    linhas.append("};")
    linhas.append("var PAISES_ = " + json.dumps({p[0]: p[1] for p in paises}, ensure_ascii=False) + ";")
    GAS.write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")
    print("ok: %d UFs, %d municípios, %d países" % (len(ufs), total, len(paises)))


if __name__ == "__main__":
    main()
