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

    def test_versao_dos_arquivos_acompanha_o_conteudo(self):
        """Evita cache antigo: o ?v= de styles.css e app.js no index.html deve ser o resumo atual do arquivo (rode scripts/versionar_assets.py)."""
        import hashlib
        html = (SITE / "index.html").read_text(encoding="utf-8")
        for nome in ("styles.css", "app.js"):
            esperado = hashlib.sha1((SITE / nome).read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:8]
            self.assertIn(f"{nome}?v={esperado}", html, f"{nome} mudou sem atualizar a versão: rode python -I scripts/versionar_assets.py")

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

    def test_ofertas_adotadas_sem_selo_em_estruturacao(self):
        """23/11/2026: o Bruno adotou 14–17 e 21; nenhuma oferta mostra "Em estruturação". 13 segue sob demanda."""
        estados = {o["numero"]: o.get("estado_publico") for o in self.ofertas}
        self.assertNotIn("Em estruturação", estados.values())
        self.assertEqual(estados["13"], "Sob demanda")
        for n in [f"{i:02d}" for i in range(1, 13)] + ["14", "15", "16", "17", "18", "19", "20", "21"]:
            self.assertIsNone(estados[n], n)
        bloco = (SITE / "app.js").read_text(encoding="utf-8").split("CATALOGO:INICIO")[1].split("CATALOGO:FIM")[0]
        self.assertNotIn("Em estruturação", bloco)

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

    def test_selo_de_estado_aparece_com_e_sem_imagem(self):
        js = (SITE / "app.js").read_text(encoding="utf-8")
        self.assertEqual(js.count("card-estado"), 2, "o selo precisa existir nas duas variantes do cabeçalho do card")

    def test_todos_os_18_cards_tem_imagem(self):
        js = (SITE / "app.js").read_text(encoding="utf-8")
        declaradas = set(re.findall(r"'(\d\d)'", re.search(r"const IMAGENS = new Set\(\[(.*?)\]\)", js).group(1)))
        cards = {o["numero"] for o in self.ofertas if o["tipo"] == "catalogo"}
        self.assertEqual(declaradas, cards)
        for n in cards:
            self.assertTrue((SITE / "assets" / "produtos-s" / f"{n}.jpg").is_file(), n)

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
                      "codigo", "papel_no_servico", "aplicacao", "condicao", "entrega_vinculada", "partes_para_selecao", "partes_detalhadas", "assunto",
                      # revisão editorial (23/11/2026): as quatro respostas e o aprofundamento de cada oferta
                      "apresentacao", "chamada", "quando", "resumo", "entrega", "como", "empresa", "profissional", "por_que_crivia",
                      "detalhe", "destinatario", "frase_acao"}
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


class RevisaoEditorial(unittest.TestCase):
    """Revisão editorial de 23/11/2026 (Brecha de Mercado e Governante): ordem das seções, quatro respostas, âncoras e fechamento."""

    ORDEM = [("inicio", "00"), ("metodo", "01"), ("experiencia", "02"), ("catalogo", "03"), ("produto-1", "04"),
             ("produto-2", "05"), ("produto-3", "06"), ("sobre", "07"), ("contato", "08")]
    NOMES_FINAIS = {
        "01": "Viabilidade e implantação do terreno", "02": "Diagnóstico ambiental e cartográfico", "03": "Conferência do modelo 3D da obra",
        "04": "Fiscalização 360°", "05": "Equalização de propostas e pleitos", "06": "Inspeção estrutural", "07": "Custo para concluir a obra",
        "08": "Triagem técnica para compra de ativos", "09": "Conferência de notas fiscais e medição", "10": "Análise técnica de licitações",
        "11": "Gêmeo digital leve", "12": "Carbono incorporado e custo", "13": "Desempenho e requisitos", "14": "Organização da entrega documental",
        "15": "Manutenção e registros de garantias", "16": "Documentação e interfaces de obras e reformas", "17": "Adequações de redes e ativos",
        "18": "Raio-X de Propostas e Orçamentos", "19": "Diagnóstico Sentinela", "20": "Planejamento e Medição", "21": "Visualização e comunicação técnica",
    }

    @classmethod
    def setUpClass(cls):
        cls.html = (SITE / "index.html").read_text(encoding="utf-8")
        cls.js = (SITE / "app.js").read_text(encoding="utf-8")
        cls.dados = json.loads((SITE / "catalogo-publico.json").read_text(encoding="utf-8"))
        cls.ofertas = {o["numero"]: o for o in cls.dados["ofertas"]}

    def test_ordem_final_das_secoes_e_data_chapter(self):
        achadas = re.findall(r'<section[^>]*class="[^"]*\bchapter\b[^"]*"[^>]*id="([^"]+)"[^>]*data-chapter="(\d\d)"', self.html)
        self.assertEqual(achadas, self.ORDEM)
        self.assertEqual(self.html.count("class=\"chapter-rail\""), 1)
        self.assertIn("<span>08</span>", self.html)

    def test_visao_e_ancora_de_compatibilidade_sem_segunda_chapter(self):
        self.assertIn('id="visao"', self.html)
        self.assertNotRegex(self.html, r'<section[^>]*id="visao"')
        self.assertLess(self.html.index('id="metodo"'), self.html.index('id="visao"'))
        self.assertLess(self.html.index('id="visao"'), self.html.index('id="experiencia"'))

    def test_inventario_de_ancoras_do_plano(self):
        for destino in ("inicio", "conteudo", "visao", "metodo", "experiencia", "catalogo", "busca-norma", "frente-entrega-cliente",
                        "produto-1", "produto-2", "produto-3", "sobre", "contato", "contato-dialog"):
            self.assertEqual(self.html.count(f'id="{destino}"'), 1, destino)
        ids = re.findall(r'\bid="([^"]+)"', self.html)
        self.assertEqual(len(ids), len(set(ids)), "IDs duplicados no index.html")
        for n, o in self.ofertas.items():
            if o["tipo"] == "catalogo":
                self.assertEqual(o["anchor"], f"servico-{n}")

    def test_menu_e_rodape(self):
        menu = re.search(r'<nav id="main-nav".*?</nav>', self.html, re.S).group(0)
        alvos = re.findall(r'<a [^>]*href="(#[^"]+)"[^>]*>([^<]+)', menu)
        self.assertEqual([a[0] for a in alvos], ["#catalogo", "#metodo", "#experiencia", "#sobre", "#contato"])
        self.assertEqual([a[1].strip() for a in alvos][:4], ["SOLUÇÕES", "COMO ATUAMOS", "EXPERIÊNCIA", "SOBRE"])
        self.assertIn("data-abrir-contato", menu)
        self.assertIn("APRESENTAR MEU CENÁRIO", menu)
        # todo destino interno do menu e do rodapé existe
        rodape = re.search(r'<div class="footer-links">.*?</div>', self.html, re.S).group(0)
        for alvo in re.findall(r'href="#([^"]+)"', menu + rodape):
            self.assertIn(f'id="{alvo}"', self.html, alvo)

    def test_navegacao_destaca_solucoes_nas_entradas_e_regua_termina_em_08(self):
        self.assertIn("'produto-1': 'catalogo'", self.js)
        self.assertIn("'produto-2': 'catalogo'", self.js)
        self.assertIn("'produto-3': 'catalogo'", self.js)

    def test_nada_do_controlador_antigo_de_visao_e_metodo_sobrou(self):
        todos = self.html + self.js + (SITE / "styles.css").read_text(encoding="utf-8")
        for resto in ("tri-steps", "tri-status", "tri-media", "tri-node", "tri-lines", "MOVS", "method-steps", "step-card", "method-order"):
            self.assertNotIn(resto, todos, resto)

    def test_hero_com_acao_principal_e_secundaria(self):
        hero = re.search(r'<section class="xr chapter" id="inicio".*?</section>', self.html, re.S).group(0)
        self.assertIn("Veja o que a obra<br><em>ainda não revelou.</em>", hero)
        self.assertIn("Clareza para decidir. Prioridades para agir. Base para prestar contas.", hero)
        self.assertRegex(hero, r'<a class="button button--primary" href="#contato" data-abrir-contato>APRESENTAR MEU CENÁRIO')
        self.assertRegex(hero, r'<a class="button button--ghost" href="#catalogo">CONHECER AS SOLUÇÕES')
        self.assertNotIn("wa.me", hero)

    def test_21_ofertas_com_nome_final_e_apresentacao_completa(self):
        self.assertEqual({n: o["nome"] for n, o in self.ofertas.items()}, self.NOMES_FINAIS)
        for n, o in self.ofertas.items():
            ap = o["apresentacao"]
            for campo in ("chamada", "quando", "frase_acao"):
                self.assertTrue(ap[campo].strip(), f"{n} sem {campo}")
            self.assertEqual(set(ap["resumo"]), {"entrega", "como", "empresa", "profissional", "por_que_crivia"}, n)
            self.assertTrue(all(v.strip() for v in ap["resumo"].values()), n)
            self.assertEqual(set(ap["detalhe"]), {"entrega", "como", "empresa", "profissional", "destinatario", "por_que_crivia"}, n)
            self.assertTrue(isinstance(ap["detalhe"]["como"], list) and len(ap["detalhe"]["como"]) >= 3, n)
            self.assertTrue(o["cta"].strip(), n)
            # a mesclagem não apagou o bloco normativo nem as palavras-chave
            self.assertTrue(o["normas_e_referencias"]["objetivo"] and o["palavras_chave_normativas"] is not None, n)

    def test_oferta_16_cobre_obras_novas_e_reformas_sem_perder_a_condicao_da_16280(self):
        o = self.ofertas["16"]
        self.assertEqual(o["normas_e_referencias"]["objetivo"], "Organizar requisitos, documentos, interfaces e alterações da obra ou reforma, conforme o enquadramento da intervenção.")
        ref = next(r for r in o["normas_e_referencias"]["referencias"] if r["codigo"] == "ABNT NBR 16280")
        self.assertIn("reforma", (ref["condicao"] + ref["aplicacao"]).lower())
        self.assertEqual(self.ofertas["13"]["estado_publico"], "Sob demanda")

    def test_quatro_respostas_nos_dois_caminhos_de_render(self):
        for rotulo in ("O que você recebe", "Como fazemos", "O que melhora para você", "Por que escolher a CRIVIA", "<b>Empresa:</b>", "<b>Profissional:</b>"):
            self.assertIn(rotulo, self.js, rotulo)
        # cards (cardHtml) e entradas (data-respostas) usam a mesma função, alimentada pela fonte do catálogo
        self.assertRegex(self.js, re.compile(r"const cardHtml = .*?\$\{respostasHtml\(p\)\}", re.S))
        self.assertIn("rp.innerHTML = respostasHtml(o) + detalheHtml(o)", self.js)
        self.assertEqual(self.html.count("data-respostas></div>"), 3)
        for n in ("18", "19", "20"):
            self.assertIn("resumo", self.ofertas[n]["apresentacao"])

    def test_entradas_usam_o_nome_final_no_titulo_e_no_assunto(self):
        for n, ancora in (("18", "produto-1"), ("19", "produto-2"), ("20", "produto-3")):
            sec = re.search(r'<section[^>]*id="%s".*?</section>' % ancora, self.html, re.S).group(0)
            titulo = re.sub(r"<[^>]+>", " ", re.search(r"<h2>(.*?)</h2>", sec, re.S).group(1))
            self.assertEqual(" ".join(titulo.split()).rstrip("."), self.NOMES_FINAIS[n])
            self.assertIn(f'data-assunto="{n} — {self.NOMES_FINAIS[n]}"', sec)

    def test_demonstracoes_identificadas_como_exemplo(self):
        for trecho in ("Uma aplicação ilustrativa deste trabalho", "Como funciona neste exemplo", "Exemplo ilustrativo",
                       "Cobertura, formatos, quantidade de páginas, visitas e revisões são definidos na proposta."):
            self.assertIn(trecho, self.js, trecho)
        self.assertNotIn("nome: 'Raio-X de Propostas e Orçamentos'", self.js, "o título do painel vem do catálogo, não de LABS")

    def test_atalhos_do_catalogo(self):
        bloco = re.search(r'<nav class="catalog-atalhos".*?</nav>', self.html, re.S).group(0)
        self.assertEqual(re.findall(r'href="([^"]+)"><b>(\d\d)</b>', bloco), [("#produto-1", "18"), ("#servico-14", "14"), ("#servico-13", "13"), ("#produto-3", "20")])
        entradas = re.search(r'<nav class="catalog-entradas".*?</nav>', self.html, re.S).group(0)
        self.assertEqual(re.findall(r'href="([^"]+)"><b>(\d\d)</b><span>([^<]+)', entradas),
                         [("#produto-1", "18", self.NOMES_FINAIS["18"]), ("#produto-2", "19", self.NOMES_FINAIS["19"]), ("#produto-3", "20", self.NOMES_FINAIS["20"])])
        self.assertNotIn("#servico-18", self.html)

    def test_fechamento_e_dialogo(self):
        for trecho in ("Traga o cenário. Vamos definir o próximo passo.", "O que sua empresa precisa<br><em>decidir ou entregar agora?</em>",
                       "Apresente seu cenário.", "CONTINUAR NO WHATSAPP", "Não envie documentos confidenciais nesta etapa.",
                       'maxlength="700"', "Preciso decidir ou entregar __.", "contato@criviaengenharia.com.br"):
            self.assertIn(trecho, self.html, trecho)
        contato = re.search(r'<section class="contact chapter".*?</section>', self.html, re.S).group(0)
        self.assertEqual(len(re.findall(r'data-abrir-contato', contato)), 1, "um único CTA principal no fechamento")
        self.assertIn("encodeURIComponent", self.js)
        self.assertIn('rel="noopener"', contato)

    def test_experiencia_vem_antes_do_catalogo_com_marcadores_e_links_seguros(self):
        self.assertLess(self.html.index('id="experiencia"'), self.html.index('id="catalogo"'))
        self.assertIn("<!-- EXPERIENCIAS:INICIO -->", self.html)
        self.assertIn("<!-- EXPERIENCIAS:FIM -->", self.html)
        for href in re.findall(r'<a class="exp-go" href="([^"]+)" target="_blank" rel="noopener"', self.html):
            self.assertTrue((SITE / href).is_file(), href)
        self.assertEqual(self.html.count('class="exp-go"'), 2)

    def test_numeros_do_sobre_preservados(self):
        sobre = re.search(r'<section class="about chapter".*?</section>', self.html, re.S).group(0)
        for trecho in ("20<small>anos</small>", "35<small>projetos</small>", "R$ 380<small>mi</small>", "Bruno Malta", "Engenheiro e fundador da CRIVIA", "VISÃO", "MISSÃO", "FILOSOFIA"):
            self.assertIn(trecho, sobre, trecho)


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
