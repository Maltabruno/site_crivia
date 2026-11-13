# -*- coding: utf-8 -*-
"""Gera os cartões e as páginas de Experiência e Resultados do site da CRIVIA.

Fonte única: experiencias/experiencias.json (textos) e experiencias/visuais/*.svg (desenhos).
Saída:
  - site_crivia_padrao/experiencias/<id>.html  (uma página por caso, todas com o mesmo modelo)
  - bloco entre <!-- EXPERIENCIAS:INICIO --> e <!-- EXPERIENCIAS:FIM --> em site_crivia_padrao/index.html

Só entra no site o caso com "autorizada": true e "publicada": true. A página de um caso que deixa de
atender a isso é apagada, para não ficar acessível por endereço direto.

Uso:  python -I scripts/gerar_experiencias.py
"""
import html
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DADOS = RAIZ / "experiencias" / "experiencias.json"
VISUAIS = RAIZ / "experiencias" / "visuais"
SITE = RAIZ / "site_crivia_padrao"
SAIDA = SITE / "experiencias"
INDEX = SITE / "index.html"
DOMINIO = "https://www.criviaengenharia.com.br"
INICIO, FIM = "<!-- EXPERIENCIAS:INICIO -->", "<!-- EXPERIENCIAS:FIM -->"
ID_VALIDO = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def e(texto):
    return html.escape(str(texto), quote=True)


def versao_css():
    """Usa a mesma versão de arquivo que a página inicial, para o navegador não guardar estilo antigo."""
    m = re.search(r'styles\.css\?v=([0-9a-z]+)', INDEX.read_text(encoding="utf-8"))
    return m.group(1) if m else "1"


def visual(x):
    return (VISUAIS / x["visual"]).read_text(encoding="utf-8").strip()


def titulo_corrido(x):
    return " ".join(x["titulo"])


def cartao(x, numero):
    t = titulo_corrido(x)
    return f"""          <article class="exp-card">
            <figure class="exp-visual">{visual(x)}</figure>
            <span class="exp-cat">{e(x["categoria"])}</span>
            <span class="exp-num" aria-hidden="true">{numero:02d}</span>
            <div class="exp-body">
              <p class="exp-local">{e(x["local"])}</p>
              <h3>{e(t)}</h3>
              <p class="exp-desc">{e(x["resumo"])}</p>
              <ul class="exp-meta">
                <li><b>Origem</b><span>{e(x["origem"])}</span></li>
                <li><b>Evidência</b><span>{e(x["evidencia"])}</span></li>
              </ul>
              <a class="exp-go" href="experiencias/{x["id"]}.html" target="_blank" rel="noopener" aria-label="Conhecer esta experiência: {e(t)} (abre em nova aba)"><span>CONHECER ESTA EXPERIÊNCIA →</span><small>NOVA ABA ↗</small></a>
            </div>
          </article>"""


def secao(s, numero):
    partes = []
    if s.get("itens"):
        linhas = "".join(f"<li><b>{e(n)}</b><span>{e(t)}</span></li>" for n, t in s["itens"])
        partes.append(f'<ul class="expp-itens">{linhas}</ul>')
    partes += [f"<p>{e(p)}</p>" for p in s.get("paragrafos", [])]
    if s.get("destaque"):
        partes.append(f'<p class="expp-destaque">{e(s["destaque"])}</p>')
    corpo = "\n          ".join(partes)
    return f"""      <section class="expp-sec">
        <h2><span aria-hidden="true">{numero:02d}</span>{e(s["rotulo"])}</h2>
        <div class="expp-txt">
          {corpo}
        </div>
      </section>"""


def pagina(x, outras, v):
    p = x["pagina"]
    secoes = "\n".join(secao(s, i + 1) for i, s in enumerate(p["secoes"]))
    r = p["representa"]
    antes = "".join(f"<p>{e(t)}</p>" for t in r.get("antes", []))
    depois = "".join(f"<p>{e(t)}</p>" for t in r.get("depois", []))
    nota = "".join(f"<p>{e(t)}</p>" for t in p["nota"])
    links_outras = "".join(
        f'<a class="expp-outra" href="{o["id"]}.html">OUTRA EXPERIÊNCIA: {e(titulo_corrido(o))} →</a>' for o in outras
    )
    url = f'{DOMINIO}/experiencias/{x["id"]}.html'
    # marca d'água: imagem ilustrativa do assunto (opcional), atrás do título e no painel final
    marca = marca_painel = ""
    legenda = "Composição gráfica ilustrativa"
    if x.get("imagem"):
        caminho = f'../assets/experiencias/{x["imagem"]}'
        if not (SITE / "assets" / "experiencias" / x["imagem"]).exists():
            sys.exit(f'ERRO: imagem "{x["imagem"]}" não encontrada em site_crivia_padrao/assets/experiencias/.')
        marca = f'<div class="expp-marca" aria-hidden="true"><img src="{caminho}" alt="" fetchpriority="high"></div>'
        marca_painel = f'<div class="expp-marca expp-marca--painel" aria-hidden="true"><img src="{caminho}" alt="" loading="lazy"></div>'
        legenda = "Composição gráfica e imagem de fundo ilustrativas"
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{e(p["seo_descricao"])}">
  <meta name="theme-color" content="#020812">
  <meta name="color-scheme" content="dark">
  <title>{e(p["seo_titulo"])}</title>
  <link rel="canonical" href="{url}">
  <link rel="icon" href="../assets/images/favicon.svg" type="image/svg+xml">
  <link rel="preload" href="../assets/fonts/PlusJakartaSans-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="../assets/fonts/Geist-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="../styles.css?v={v}">
</head>
<body class="exp-page">
  <!-- Página gerada por scripts/gerar_experiencias.py a partir de experiencias/experiencias.json. Não editar à mão. -->
  <a class="skip-link" href="#conteudo">Ir para o conteúdo</a>

  <header class="masthead masthead--simples">
    <a class="brand" href="../index.html" aria-label="CRIVIA — página inicial"><img src="../assets/logo-icon.png" alt="" width="38" height="38"><span><b>CRIVIA</b><small>ENGENHARIA CONSULTIVA</small></span></a>
    <nav aria-label="Navegação da página"><a href="../index.html#experiencia">VOLTAR AO SITE</a><a href="../index.html#contato">FALAR COM A CRIVIA</a></nav>
  </header>

  <main id="conteudo">
    <header class="expp-hero">
      {marca}
      <div class="expp-hero-wrap">
        <div>
          <p class="section-code">EXPERIÊNCIA · {e(x["categoria"])}</p>
          <h1>{e(x["titulo"][0])}<br><em>{e(x["titulo"][1])}</em></h1>
          <p class="expp-sub">{e(p["subtitulo"])}</p>
          <p class="expp-autoria">{e(p["autoria"])}</p>
          <p class="expp-lead">{e(x["resumo"])}</p>
        </div>
        <figure class="expp-visual">
          <div class="exp-visual">{visual(x)}</div>
          <figcaption>{legenda}</figcaption>
        </figure>
      </div>
    </header>

    <div class="expp-body">
{secoes}

      <section class="expp-crivia" aria-labelledby="expp-crivia-t">
        {marca_painel}
        <h2 id="expp-crivia-t">O QUE ESSA EXPERIÊNCIA REPRESENTA PARA A CRIVIA</h2>
        <div class="expp-txt">
          {antes}
          <p class="expp-destaque">{e(r["destaque"])}</p>
          {depois}
          <p class="expp-assina">CRIVIA — Engenharia para Decisão.</p>
        </div>
      </section>

      <aside class="expp-nota" aria-labelledby="expp-nota-t">
        <h2 id="expp-nota-t">Nota de transparência</h2>
        {nota}
      </aside>

      <nav class="expp-fim" aria-label="Continuar a navegação">
        {links_outras}
        <div>
          <a class="button button--ghost" href="../index.html#experiencia">← VOLTAR AO SITE</a>
          <a class="button button--primary" href="../index.html#contato">FALAR COM A CRIVIA <span>→</span></a>
        </div>
      </nav>
    </div>
  </main>

  <footer>
    <a class="brand" href="../index.html" aria-label="CRIVIA — página inicial"><img src="../assets/logo-icon.png" alt="" width="38" height="38"><span><b>CRIVIA</b><small>ENGENHARIA CONSULTIVA</small></span></a>
    <p>Engenharia para decisão.<br>Serra, Espírito Santo, Brasil</p>
    <div class="footer-links"><a href="../index.html#produto-1">Trabalhos</a><a href="../index.html#catalogo">Catálogo</a><a href="../index.html#metodo">Método</a><a href="../aviso-privacidade.html">Aviso de Privacidade</a></div>
    <img class="footer-seal" src="../assets/bni-160.png" srcset="../assets/bni-80.png 1x, ../assets/bni-160.png 2x, ../assets/bni-240.png 3x" alt="Selo Proud BNI Member" width="80" height="46" decoding="async">
    <small>© 2026 CRIVIA Engenharia Consultiva Ltda. · Site criado pela CRIVIA</small>
  </footer>
</body>
</html>
"""


def main():
    dados = json.loads(DADOS.read_text(encoding="utf-8"))
    todas = dados["experiencias"]
    ids = [x["id"] for x in todas]
    for i in ids:
        if not ID_VALIDO.match(i):
            sys.exit(f'ERRO: id "{i}" inválido. Use só letras minúsculas sem acento, números e hífen.')
    if len(set(ids)) != len(ids):
        sys.exit("ERRO: há dois casos com o mesmo id.")

    ativas = sorted((x for x in todas if x.get("autorizada") is True and x.get("publicada") is True), key=lambda x: x["ordem"])
    v = versao_css()
    SAIDA.mkdir(exist_ok=True)

    for x in ativas:
        outras = [o for o in ativas if o["id"] != x["id"]]
        (SAIDA / f'{x["id"]}.html').write_text(pagina(x, outras, v), encoding="utf-8", newline="\n")
        print(f'  página  experiencias/{x["id"]}.html')

    validos = {f'{x["id"]}.html' for x in ativas}
    for antigo in SAIDA.glob("*.html"):
        if antigo.name not in validos:
            antigo.unlink()
            print(f"  apagada {antigo.name} (caso não autorizado ou não publicado)")

    na_home = [x for x in ativas if x.get("na_home") is True]
    cartoes = "\n".join(cartao(x, n + 1) for n, x in enumerate(na_home))
    texto = INDEX.read_text(encoding="utf-8")
    if INICIO not in texto or FIM not in texto:
        sys.exit("ERRO: marcadores EXPERIENCIAS:INICIO / EXPERIENCIAS:FIM não encontrados em index.html.")
    a, resto = texto.split(INICIO, 1)
    _, b = resto.split(FIM, 1)
    novo = f"{a}{INICIO}\n{cartoes}\n          {FIM}{b}"
    INDEX.write_text(novo, encoding="utf-8", newline="\n")
    print(f"  página inicial: {len(na_home)} cartão(ões)")

    fora = [x["id"] for x in todas if x not in ativas]
    if fora:
        print("  fora do site (não autorizados ou não publicados): " + ", ".join(fora))
    if not na_home:
        print("  AVISO: nenhum cartão na página inicial. A dobra ficará vazia.")


if __name__ == "__main__":
    main()
