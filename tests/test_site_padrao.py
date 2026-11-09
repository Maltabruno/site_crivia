# -*- coding: utf-8 -*-
"""Testes do Site CRIVIA padrão (pasta site_crivia_padrao/). Só biblioteca padrão do Python.

    python -I -m unittest discover -s tests -v
"""
import http.server
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
        for n in range(1, 13):
            self.assertTrue((SITE / "assets" / "produtos-s" / f"{n:02d}.jpg").is_file(), n)
        js = (SITE / "app.js").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"\{ n: '\d\d', apelido:", js)), 12)

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
                for caminho in ("/index.html", "/aviso-privacidade.html", "/styles.css", "/app.js", "/assets/bni-80.png"):
                    with urllib.request.urlopen(f"http://127.0.0.1:{porta}{caminho}", timeout=5) as r:
                        self.assertEqual(r.status, 200, caminho)
            finally:
                srv.shutdown()


if __name__ == "__main__":
    unittest.main()
