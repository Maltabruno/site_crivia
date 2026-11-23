# -*- coding: utf-8 -*-
"""Testes do Site CRIVIA padrão (pasta site_crivia_padrao/). Só biblioteca padrão do Python.

    python -I -m unittest discover -s tests -v
"""
import http.server
import json
import re
import socketserver
import threading
import unittest
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SITE = REPO / "site_crivia_padrao"
WHATS = "5527996971800"


def referencias_locais(html):
    achadas = re.findall(r'(?:src|href)="([^"]+)"', html)
    achadas += re.findall(r'srcset="([^"]+)"', html)
    saida = []
    for ref in achadas:
        for parte in ref.split(","):
            alvo = parte.strip().split(" ")[0]
            if not alvo or alvo.startswith(("#", "http:", "https:", "mailto:", "tel:", "data:", "javascript:")):
                continue
            saida.append(alvo.split("#")[0].split("?")[0])
    return [a for a in saida if a]


class SitePadrao(unittest.TestCase):
    def test_arquivos_principais_existem(self):
        for nome in ("index.html", "aviso-privacidade.html", "styles.css", "app.js"):
            self.assertTrue((SITE / nome).is_file(), nome)

    def test_referencias_das_paginas_existem(self):
        for pagina in ("index.html", "aviso-privacidade.html"):
            html = (SITE / pagina).read_text(encoding="utf-8")
            for alvo in referencias_locais(html):
                self.assertTrue((SITE / alvo).exists(), f"{pagina} aponta para {alvo}, que não existe")

    def test_fontes_e_imagens_do_css_existem(self):
        css = (SITE / "styles.css").read_text(encoding="utf-8")
        for alvo in re.findall(r'url\("?([^)"]+)"?\)', css):
            if alvo.startswith(("data:", "http", "#")):
                continue
            self.assertTrue((SITE / alvo.split("?")[0]).exists(), f"styles.css aponta para {alvo}")

    def test_catalogo_tem_as_12_imagens(self):
        """As 12 imagens aprovadas continuam existindo; as ofertas novas (13 a 17 e 21) não exigem imagem."""
        for n in range(1, 13):
            self.assertTrue((SITE / "assets" / "produtos-s" / f"{n:02d}.jpg").is_file(), n)
        js = (SITE / "app.js").read_text(encoding="utf-8")
        declaradas = re.search(r"const IMAGENS = new Set\(\[(.*?)\]\)", js).group(1)
        for n in re.findall(r"'(\d\d)'", declaradas):
            self.assertTrue((SITE / "assets" / "produtos-s" / f"{n}.jpg").is_file(), f"imagem {n} declarada e ausente")
        self.assertTrue({f"{n:02d}" for n in range(1, 13)} <= set(re.findall(r"'(\d\d)'", declaradas)))

    def test_whatsapp_e_email_confirmados(self):
        js = (SITE / "app.js").read_text(encoding="utf-8")
        self.assertIn(f"const WHATS = '{WHATS}';", js)
        self.assertIn("contato@criviaengenharia.com.br", js)

    def test_nada_do_que_foi_retirado_voltou(self):
        todos = "".join((SITE / n).read_text(encoding="utf-8") for n in ("index.html", "app.js", "styles.css"))
        for proibido in ("apresentar-cenario.html", "estrutura-edificio", "proud-member.png", "FALAR NO WHATSAPP", "SISTEMA SENTINELA", "INICIALIZANDO"):
            self.assertNotIn(proibido, todos, proibido)

    def test_rodape_e_aviso(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn("Serra, Espírito Santo, Brasil", html)
        self.assertIn("Site criado pela CRIVIA", html)
        self.assertIn("CRIVIA Engenharia Consultiva Ltda.", html)
        aviso = (SITE / "aviso-privacidade.html").read_text(encoding="utf-8")
        self.assertIn("revisão jurídica", aviso)
        self.assertNotIn("LGPD", aviso)

    def test_painéis_estao_marcados_como_exemplo(self):
        js = (SITE / "app.js").read_text(encoding="utf-8")
        self.assertIn("Exemplo ilustrativo", js)


def bloco_js(nome):
    """Lê uma constante do bloco CATALOGO do app.js (array JSON, uma linha por objeto)."""
    js = (SITE / "app.js").read_text(encoding="utf-8")
    bloco = js.split("/* CATALOGO:INICIO", 1)[1].split("/* CATALOGO:FIM */", 1)[0]
    m = re.search(r"const " + nome + r" = (\[.*?\n\]);", bloco, re.S)
    assert m, nome
    return json.loads(m.group(1))


class Catalogo21(unittest.TestCase):
    """Catálogo R02: 21 ofertas = 18 cards em quatro frentes + 3 entradas (18, 19 e 20)."""

    CAMPOS_PRIVADOS = ("custo", "hora", "margem", "preco", "preço", "tir", "reserva", "especialista", "cliente_real", "cnpj", "razao", "razão", "meta", "valor", "r$")

    @classmethod
    def setUpClass(cls):
        cls.dados = json.loads((SITE / "catalogo-publico.json").read_text(encoding="utf-8"))
        cls.ofertas = cls.dados["ofertas"]
        cls.html = (SITE / "index.html").read_text(encoding="utf-8")

    def test_json_tem_21_ofertas_numeradas_e_4_grupos(self):
        self.assertEqual([o["numero"] for o in self.ofertas], sorted({o["numero"] for o in self.ofertas}))
        self.assertEqual({o["numero"] for o in self.ofertas}, {f"{n:02d}" for n in range(1, 22)})
        self.assertEqual(len(self.dados["grupos"]), 4)
        self.assertEqual(sum(o["tipo"] == "catalogo" for o in self.ofertas), 18)
        self.assertEqual({o["numero"] for o in self.ofertas if o["tipo"] == "entrada"}, {"18", "19", "20"})

    def test_grupos_cobrem_os_18_cards_sem_orfao_nem_duplicado(self):
        ns = [n for g in self.dados["grupos"] for n in g["ns"]]
        self.assertEqual(len(ns), len(set(ns)), "card em mais de um grupo")
        self.assertEqual(set(ns), {o["numero"] for o in self.ofertas if o["tipo"] == "catalogo"})
        for g in self.dados["grupos"]:
            for n in g["ns"]:
                oferta = next(o for o in self.ofertas if o["numero"] == n)
                self.assertEqual(oferta["grupo"], g["id"], n)
        self.assertEqual(self.dados["grupos"][3]["ns"], ["13", "14", "15", "16", "17", "21"])

    def test_entradas_nao_aparecem_nos_grupos(self):
        ns = {n for g in self.dados["grupos"] for n in g["ns"]}
        self.assertFalse(ns & {"18", "19", "20"})

    def test_campos_obrigatorios_em_todas_as_ofertas(self):
        for o in self.ofertas:
            for campo in ("nome", "dor", "para_quem", "beneficios", "resultado_pratico", "entregas", "limites", "referencia", "cta", "anchor", "disponibilidade"):
                self.assertTrue(o.get(campo), f"{o['numero']} sem {campo}")
            self.assertTrue(o["para_quem"].get("decisor") and o["para_quem"].get("prestadora"), o["numero"])
            self.assertTrue(o["limites"].lower().startswith(("não", "nao")) or "não" in o["limites"].lower(), o["numero"])
            self.assertEqual(o["disponibilidade"], "Consulte o escopo e a disponibilidade para o seu caso.", o["numero"])

    def test_ancoras_unicas_e_ancoras_legadas_preservadas(self):
        self.assertEqual(len({o["anchor"] for o in self.ofertas}), 21)
        legadas = {"18": "produto-1", "19": "produto-2", "20": "produto-3"}
        for n, ancora in legadas.items():
            self.assertEqual(next(o for o in self.ofertas if o["numero"] == n)["anchor"], ancora)
            self.assertIn(f'id="{ancora}"', self.html)
        for o in self.ofertas:
            if o["tipo"] == "catalogo":
                self.assertEqual(o["anchor"], f"servico-{o['numero']}")

    def test_codigos_internos_nao_aparecem_no_site_publico(self):
        """IDs históricos do Painel (ND, ENT, MAN, REF, ADE, RX, DS, PM, CV01) são internos."""
        publico = "".join((SITE / n).read_text(encoding="utf-8") for n in ("catalogo-publico.json", "index.html", "app.js"))
        for codigo in ("CV01", "id_estavel"):
            self.assertNotIn(codigo, publico, codigo)
        for o in self.ofertas:
            self.assertNotIn("id_estavel", o)

    def test_ofertas_nao_liberadas_aparecem_como_em_estruturacao(self):
        """Catálogo R07: 14–17 e 21 inativas (preparação operacional); 13 sob demanda. O site não as apresenta como prontas."""
        estados = {o["numero"]: o.get("estado_publico") for o in self.ofertas}
        for n in ("14", "15", "16", "17", "21"):
            self.assertEqual(estados[n], "Em estruturação", n)
        self.assertEqual(estados["13"], "Sob demanda")
        for n in [f"{i:02d}" for i in range(1, 13)] + ["18", "19", "20"]:
            self.assertIsNone(estados[n], n)
        js = (SITE / "app.js").read_text(encoding="utf-8")
        self.assertIn("CONVERSAR SOBRE O INTERESSE", js)
        self.assertIn("(em estruturação)", js)

    # ---- Normas por produto (R03) e busca por norma ----
    @staticmethod
    def norm(s):
        import unicodedata
        s = unicodedata.normalize("NFD", str(s))
        s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
        return re.sub(r"[^a-z0-9]+", "", s)

    def refs(self, n):
        return next(o for o in self.ofertas if o["numero"] == n)["normas_e_referencias"]["referencias"]

    def produtos_da_busca(self, consulta):
        """Reproduz a busca do app.js: por norma, todos os tokens (ou o texto compacto) precisam estar no código, nome, partes ou aplicação."""
        achou = set()
        for o in self.ofertas:
            for r in o["normas_e_referencias"]["referencias"]:
                hay = self.norm(" ".join([r["codigo"], r["nome"], r["aplicacao"]] + [f"{x['codigo']} {x['assunto']}" for x in r["partes_detalhadas"]]))
                tokens = [self.norm(x) for x in consulta.split() if self.norm(x)]
                if tokens and (all(tk in hay for tk in tokens) or self.norm(consulta) in hay):
                    achou.add(o["numero"])
        return achou

    def test_21_produtos_tem_bloco_normativo_ou_criterio_contratual(self):
        for o in self.ofertas:
            nr = o["normas_e_referencias"]
            self.assertEqual(nr["titulo"], "Normas e aplicação no serviço", o["numero"])
            self.assertTrue(nr["objetivo"] and nr["criterios_principais"] and nr["alcance"], o["numero"])
            for r in nr["referencias"]:
                for campo in ("codigo", "nome", "aplicacao", "entrega_vinculada", "condicao"):
                    self.assertTrue(r.get(campo), f"{o['numero']} {r.get('codigo')} sem {campo}")
        for n in ("04", "09"):
            self.assertEqual(self.refs(n), [], f"{n} não deve ganhar NBR genérica")

    def test_busca_por_norma_leva_aos_produtos_certos(self):
        casos = {
            "15575": {"13", "14", "16"}, "NBR15.575": {"13", "14", "16"}, "nbr 15575": {"13", "14", "16"}, "15575-3": {"13", "14", "16"},
            "14037": {"14", "15", "16"}, "5674": {"06", "11", "14", "15"}, "16280": {"16", "17"}, "9050": {"17"}, "9077": {"17"},
        }
        for consulta, esperado in casos.items():
            self.assertEqual(self.produtos_da_busca(consulta), esperado, consulta)
        self.assertEqual(self.produtos_da_busca("ABNT NBR 15575"), {"13", "14", "16"})
        self.assertIn("17", self.produtos_da_busca("acessibilidade"))

    def test_partes_da_15575_identificadas_sem_edicao_unica(self):
        ref = next(r for r in self.refs("13") if r["codigo"] == "ABNT NBR 15575")
        self.assertEqual([p["codigo"] for p in ref["partes_detalhadas"]], [f"ABNT NBR 15575-{i}" for i in range(1, 7)])
        js = (SITE / "app.js").read_text(encoding="utf-8")
        self.assertIn("sem impor uma edição única à série", js)
        self.assertNotRegex(json.dumps(ref, ensure_ascii=False), r"15575[-:]?\d?:?(19|20)\d\d")

    def test_sinapi_sicro_e_nts_nao_levam_rotulo_de_nbr(self):
        for o in self.ofertas:
            for r in o["normas_e_referencias"]["referencias"]:
                if r["tipo"] == "referencia_tecnica_ou_regulamentar":
                    self.assertNotIn("NBR", r["codigo"], r["codigo"])
                else:
                    self.assertTrue(r["codigo"].startswith(("ABNT", "ISO")), r["codigo"])
        for n in ("10", "20"):
            self.assertTrue(all(r["tipo"] == "referencia_tecnica_ou_regulamentar" for r in self.refs(n)), f"{n} não recebe norma universal")

    def test_texto_normativo_nao_afirma_conformidade_nem_certificacao(self):
        texto = json.dumps([o["normas_e_referencias"] for o in self.ofertas], ensure_ascii=False).lower()
        for proibido in ("100% conforme", "edificação certificada", "atendimento integral garantido", "laudo garante"):
            self.assertNotIn(proibido, texto, proibido)
        r17025 = next(r for r in self.refs("13") if "17025" in r["codigo"])
        self.assertNotIn("crivia é acreditada", json.dumps(r17025, ensure_ascii=False).lower())

    def test_app_renderiza_bloco_e_busca(self):
        js = (SITE / "app.js").read_text(encoding="utf-8")
        for trecho in ("normasHtml", "busca-q", "ehCondicional", "data-normas"):
            self.assertIn(trecho, js, trecho)
        self.assertIn('id="busca-norma"', self.html)
        self.assertIn("Encontre o serviço pela norma", self.html)
        self.assertEqual(self.html.count("data-normas></div>"), 3)

    def test_gerador_preserva_campos_normativos(self):
        for campo in ("normas_e_referencias", "palavras_chave_normativas"):
            self.assertTrue(all(campo in o for o in bloco_js("PRODUTOS") + bloco_js("ENTRADAS")), campo)

    def test_imagens_de_rascunho_fora_do_site(self):
        for n in ("14", "15", "16", "17", "21"):
            self.assertFalse((SITE / "assets" / "produtos-s" / f"{n}.jpg").exists(), n)

    def test_json_publico_sem_chaves_privadas(self):
        def chaves(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    yield k
                    yield from chaves(v)
            elif isinstance(x, list):
                for v in x:
                    yield from chaves(v)
        permitidas = {"versao", "estado", "grupos", "ofertas", "id", "nome", "ns", "numero", "estado_publico", "grupo", "tipo", "dor", "para_quem",
                      "decisor", "prestadora", "beneficios", "resultado_pratico", "entregas", "limites", "referencia", "cta", "anchor", "disponibilidade",
                      "normas_e_referencias", "palavras_chave_normativas", "titulo", "objetivo", "criterios_principais", "referencias", "alcance",
                      "codigo", "papel_no_servico", "aplicacao", "condicao", "entrega_vinculada", "partes_para_selecao", "partes_detalhadas", "assunto"}
        self.assertEqual(set(chaves(self.dados)) - permitidas, set())
        texto = json.dumps(self.dados, ensure_ascii=False)
        self.assertNotIn("R$", texto)
        self.assertNotRegex(texto, r"\d+\s?%")

    def test_app_js_equivale_ao_json_publico(self):
        self.assertEqual(bloco_js("PRODUTOS"), [o for o in self.ofertas if o["tipo"] == "catalogo"])
        self.assertEqual(bloco_js("ENTRADAS"), [o for o in self.ofertas if o["tipo"] == "entrada"])
        self.assertEqual(bloco_js("GRUPOS"), self.dados["grupos"])

    def test_gerador_e_idempotente(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("gerar_catalogo", REPO / "scripts" / "gerar_catalogo.py")
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        js = (SITE / "app.js").read_text(encoding="utf-8")
        self.assertIn(modulo.bloco(self.dados), js)

    def test_entradas_no_html_usam_numero_publico_e_assunto_codificado(self):
        for n, ancora in (("18", "produto-1"), ("19", "produto-2"), ("20", "produto-3")):
            m = re.search(r'<section[^>]*id="%s"[^>]*data-oferta="%s"' % (ancora, n), self.html)
            self.assertTrue(m, ancora)
            oferta = next(o for o in self.ofertas if o["numero"] == n)
            self.assertIn(f'data-assunto="{n} — {oferta["nome"]}"', self.html)
            self.assertIn(f"OFERTA {n} · ", self.html)

    def test_frente_entrega_ao_cliente_leva_a_quarta_aba(self):
        self.assertIn('id="frente-entrega-cliente"', self.html)
        self.assertIn('data-grupo="3"', self.html)
        self.assertIn("#frente-entrega-cliente", self.html)

    def test_ctas_do_catalogo_enviam_codigo_e_nome(self):
        js = (SITE / "app.js").read_text(encoding="utf-8")
        self.assertIn("const assuntoDe = (o) => `${o.numero} — ${o.nome}${o.estado_publico", js)
        self.assertIn('data-assunto="${esc(assuntoDe(p))}"', js)

    def test_nao_ha_formulario_nem_backend_de_captacao(self):
        self.assertNotIn("<form action", self.html)
        js = (SITE / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("fetch(", js)
        self.assertNotIn("XMLHttpRequest", js)

    def test_catalogo_menciona_dezoito_produtos(self):
        self.assertIn("Dezoito produtos em quatro frentes", self.html)
        self.assertNotIn("Doze produtos", self.html)


class Servidor(unittest.TestCase):
    """Sobe o servidor do Site_crivia.py na pasta padrão e confere as páginas."""

    def test_servir_pasta_padrao(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("site_crivia", REPO / "Site_crivia.py")
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        self.assertEqual(modulo.PASTA_PADRAO, SITE)

        class Sv(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        def handler(*a, **k):
            return http.server.SimpleHTTPRequestHandler(*a, directory=str(modulo.PASTA_PADRAO), **k)

        with Sv(("127.0.0.1", 0), handler) as srv:
            porta = srv.server_address[1]
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            try:
                for caminho in ("/index.html", "/aviso-privacidade.html", "/styles.css", "/app.js", "/catalogo-publico.json", "/assets/bni-80.png"):
                    with urllib.request.urlopen(f"http://127.0.0.1:{porta}{caminho}", timeout=5) as r:
                        self.assertEqual(r.status, 200, caminho)
            finally:
                srv.shutdown()


if __name__ == "__main__":
    unittest.main()
