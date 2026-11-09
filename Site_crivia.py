#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Site_crivia.py — construtor e servidor do site da CRIVIA Engenharia Consultiva.

O que faz
---------
Parte do site-modelo Auralis (assets/references/auralis-design-system.zip) e gera
o site da CRIVIA na pasta `site/`, trocando identidade, formas, cores e textos:

  * glifo "X"  ->  "C" tridimensional (arco de 270 graus, abertura à direita);
  * mão        ->  indústria (nuvem de pontos gerada aqui);
  * árvore     ->  "Obra-circuito": obra em construção atravessada por uma malha
                   de nós ligados a um núcleo âmbar (IA aplicada aos processos);
  * paleta     ->  tintas claras da paleta CRIVIA (fundo leve, partículas azul-marinho);
  * textos     ->  português, conforme Documento Mestre v4.3 e Segundo Cérebro v0.6.

Todo patch no código do modelo usa uma âncora de texto com contagem esperada:
se o modelo mudar e a âncora não for encontrada, o script FALHA com mensagem
clara e não gera nada pela metade. A geração é determinística (semente fixa):
rodar duas vezes produz arquivos idênticos.

Uso (a partir de agora, o padrão é o SITE CRIVIA PADRÃO, na pasta `site_crivia_padrao/`)
---
    python Site_crivia.py                       # serve o Site CRIVIA padrão em http://localhost:8080
    python Site_crivia.py --no-browser          # serve sem abrir o navegador
    python Site_crivia.py --port 9000           # porta preferida
    python Site_crivia.py --antigo              # constrói e serve o site anterior (modelo Auralis, pasta site/)
    python Site_crivia.py --antigo --build-only # só constrói o site anterior

O resultado também abre por duplo clique em `site/design-system.html` (file://).
Só biblioteca padrão do Python 3. O arquivo anterior foi descartado por decisão
do usuário: nada do conteúdo antigo é reaproveitado aqui.
"""

import argparse
import base64
import bisect
import hashlib
import http.server
import json
import math
import os
import random
import shutil
import socketserver
import struct
import sys
import tempfile
import threading
import webbrowser
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
PASTA_PADRAO = REPO / "site_crivia_padrao"   # o site oficial: HTML, CSS e JS simples, sem etapa de construção
ZIP_MODELO = REPO / "assets" / "references" / "auralis-design-system.zip"
ZIP_NEXUS = REPO / "assets" / "references" / "nexus-cyber-design-system.zip"   # só a tipografia
SAIDA = REPO / "site"
PREFIXO = "[CRIVIA]"

SEMENTE_INDUSTRIA = 20261031
SEMENTE_OBRA = 20261101
N_INDUSTRIA = 12600  # x densidade 4 (hand.density) = 50.400 = colunas x linhas da onda (336 x 150)
N_OBRA = 50000      # mesma contagem da árvore do modelo (desempenho idêntico)


def log(msg):
    print(f"{PREFIXO} {msg}", flush=True)


class ErroDePatch(RuntimeError):
    """Âncora do modelo não encontrada (ou encontrada em número diferente do esperado)."""


# ════════════════════════════════════════════════════════════════════════════
#  DADOS DOS PATCHES  (paleta, configuração da cena, textos)
#  Cada item: (rótulo, trecho antigo, trecho novo, ocorrências esperadas)
# ════════════════════════════════════════════════════════════════════════════

# ── Paleta: variáveis CSS (main.css) ────────────────────────────────────────
PATCHES_CSS = [
    ("css:root",
     "  --background: #fff;\n  --foreground: #171717;\n  --scene-backdrop: #8d959e;\n"
     "  --overlay-ink: #fff;\n  --overlay-scrim: #0000001a;\n  --overlay-glass: #ffffff1a;\n"
     "  --overlay-line: #fff3;\n  --overlay-edge: #fff6;\n  --overlay-strong: #fffc;\n"
     "  --overlay-solid: #000;\n  --overlay-accent: #6fff85;\n  --grain-opacity: .13;\n",
     "  --background: #F4FAFD;\n  --foreground: #001D3D;\n  --scene-backdrop: #D9ECF5;\n"
     "  --overlay-ink: #001D3D;\n  --overlay-scrim: #F4FAFD26;\n  --overlay-glass: #001D3D14;\n"
     "  --overlay-line: #001D3D33;\n  --overlay-edge: #001D3D55;\n  --overlay-strong: #001D3DCC;\n"
     "  --overlay-solid: #F4FAFD;\n  --overlay-accent: #00B4D8;\n  --grain-opacity: .06;\n", 1),
    # o modelo escurece o fundo no modo escuro do sistema; a CRIVIA mantém o fundo leve sempre
    ("css:modo-escuro",
     "    --background: #0a0a0a;\n    --foreground: #ededed;\n",
     "    --background: #F4FAFD;\n    --foreground: #001D3D;\n", 1),
]

# ── Cena 3D (app.js): configuração ──────────────────────────────────────────
PATCHES_CENA = [
    # celular / janela estreita: a indústria acompanha a escala do C (mesma proporção de tela)
    ("cena:industria-escala-tela", "const handT = { ...hand, density: scaled(hand.density, 4) };", "const handT = { ...hand, density: scaled(hand.density, 4), scale: hand.scale * glyphScale * (isMobile ? 0.6 : 1), ...(isMobile ? { center: [-0.6, hand.center[1] - 3.3, hand.center[2]] } : {}) };", 1),
    ("cena:rede-hero-altura", "height: field.height * field.heroScale,\n        centerY: heroFieldBase + field.height * field.heroScale / 2", "height: field.height * field.heroScale * glyphScale,\n        centerY: field.centerY + (isMobile ? 1.8 : 0)", 1),
    # a rede do hero acompanha o tamanho do C (janela estreita / celular)
    ("cena:rede-hero-r1", "radiusTop: field.radiusTop * field.heroScale,", "radiusTop: field.radiusTop * field.heroScale * glyphScale,", 1),
    ("cena:rede-hero-r2", "radiusBottom: field.radiusBottom * field.heroScale,", "radiusBottom: field.radiusBottom * field.heroScale * glyphScale,", 1),
    # a cena precisa acompanhar o redimensionamento da janela (no modelo, o modo celular não observava o tamanho)
    ("cena:observador", "const sizeObserver = isMobile ? null : new ResizeObserver(() => applySize());", "const sizeObserver = new ResizeObserver(() => applySize());", 1),
    # celular: o C fica menor para caber entre as frases de cima e as de baixo
    ("cena:c-celular", "const glyphT = { ...glyph, count: scaled(glyph.count, 8e3) };",
     "const glyphAspect = window.innerWidth / window.innerHeight;\n      const glyphScale = isMobile ? 0.52 : (glyphAspect > 0 && Number.isFinite(glyphAspect) ? Math.min(1, Math.max(0.58, glyphAspect / 1.55)) : 1);\n"
     "      const glyphT = { ...glyph, count: scaled(glyph.count, 8e3), ...(glyphScale < 1 ? { barLength: glyph.barLength * glyphScale, barWidth: glyph.barWidth * glyphScale, barDepth: glyph.barDepth * glyphScale, particleSize: glyph.particleSize * (0.4 + 0.6 * glyphScale), spill: glyph.spill * glyphScale, edgeNoise: glyph.edgeNoise * glyphScale } : {}), ...(isMobile ? { center: [glyph.center[0], 12.3, glyph.center[2]] } : {}) };", 1),
    ("cena:bloom-particulas",
     'color: "#b552ff",\n    glow: 5.5', 'color: "#00B4D8",\n    glow: 1.5', 1),
    # com tone mapping linear não há "estouro" para o branco: brilhos transitórios em nível baixo
    ("cena:brilho-intro", "spread: 11, glow: 4.2,", "spread: 11, glow: 1.3,", 1),
    ("cena:brilho-industria", "      scanGlow: 6,", "      scanGlow: 1.5,", 1),
    ("cena:brilho-obra", "      scanGlow: 4.2,", "      scanGlow: 1.3,", 1),
    # o cursor "abre" as partículas com um brilho âmbar (acento da marca), bem visível sobre o azul
    ("cena:brilho-cursor", "      glow: 3.6\n", "      glow: 1.9\n", 1),
    ("cena:cursor-alcance", "      radius: 5,\n      strength: 6,", "      radius: 6.5,\n      strength: 8,", 1),
    ("cena:fog", 'fog: "#868e96",\n      backdropTop: "#aab2ba",',
     'fog: "#F7FBFE",\n      backdropTop: "#FFFFFF",', 1),
    ("cena:backdropBottom", 'backdropBottom: "#868e96",\n      particle: "#ffffff",\n      field: "#ffffff",',
     'backdropBottom: "#F7FBFE",\n      particle: "#001D3D",\n      field: "#0A369D",', 1),
    ("cena:luzes", 'skyFill: "#e6ecf2",\n      groundFill: "#8a929a",',
     'skyFill: "#F4FAFD",\n      groundFill: "#B9D4E6",', 1),
    # bloom sutil em fundo claro
    ("cena:bloom", "bloom: { threshold: 3.5, strength: 1.5, radius: 1.9 },",
     "bloom: { threshold: 3.5, strength: 0.6, radius: 1.4 },", 1),
    # a vinheta do modelo escurece as bordas; aqui só um respiro claro
    ("cena:vinheta", "vignette: { offset: 1, darkness: 1.25 },",
     "vignette: { offset: 1, darkness: 0.05 },", 1),
    # fio de acento (fluxo, cursor): ciano em lugar do rosa/âmbar
    ("cena:life-cor", "color: BLOOM_PARTICLES.color,\n      // Flow strengths",
     'color: "#00B4D8",\n      // Flow strengths', 1),
    ("cena:cursor", 'color: "#b579ff",', 'color: "#F5B82E",', 1),   # dourado
    # névoa mais curta: o C (a ~50 unidades da câmera) não pode "esbranquiçar" contra o fundo claro
    ("cena:nevoa", "fog: { near: 25, far: 130 },", "fog: { near: 40, far: 150 },", 1),
    # na fase da onda o modelo clareia as contas até o branco (invisível em fundo claro): o alvo passa a ser o azul royal
    ("cena:onda-cor-r", "colR += (1 - colR) * wlE;", "colR += (CRIVIA_ROYAL.r - colR) * wlE;", 1),
    ("cena:onda-cor-g", "colG += (1 - colG) * wlE;", "colG += (CRIVIA_ROYAL.g - colG) * wlE;", 1),
    ("cena:onda-cor-b", "colB += (1 - colB) * wlE;", "colB += (CRIVIA_ROYAL.b - colB) * wlE;", 1),
    # a onda levantava as contas até o branco; em fundo claro elas ficariam invisíveis
    ("cena:onda-lift", "      lift: 2,", "      lift: 0,", 1),
    # contas "grandes" (4%): brilho ciano em vez de branco
    ("cena:grande-R", "sTintR * bloom, bloomGlowVal, scanGlowR, waveLift",
     "sTintR * bloom, bloomGlowVal * 0.0, scanGlowR, waveLift", 1),
    ("cena:grande-G", "sTintG * bloom, bloomGlowVal, scanGlowG, waveLift",
     "sTintG * bloom, bloomGlowVal * 0.1, scanGlowG, waveLift", 1),
    ("cena:grande-B", "sTintB * bloom, bloomGlowVal, scanGlowB, waveLift",
     "sTintB * bloom, bloomGlowVal * 0.16, scanGlowB, waveLift", 1),
    # parte das contas em azul royal (detalhe); as demais ficam azul-marinho
    ("cena:royal",
     "      color3.copy(base2).multiplyScalar(shadeValue);\n",
     "      color3.copy(base2).multiplyScalar(shadeValue);\n"
     "      if (random() < 0.18) color3.lerp(CRIVIA_ROYAL, 0.85);\n", 1),
    ("cena:royal-const", "  var buildParticleCloud = (points, options) => {",
     '  var CRIVIA_ROYAL = new Color("#0A369D");\n  var buildParticleCloud = (points, options) => {', 1),
    # fundo leve: o tone mapping ACES do modelo acinzenta e dessatura qualquer tom claro; o linear
    # preserva o azul-gelo exato da paleta
    ("cena:tonemap", "renderer.toneMapping = ACESFilmicToneMapping;",
     "renderer.toneMapping = LinearToneMapping;", 1),
    # menos névoa ciano nas formas (o fluxo do modelo é forte demais sobre contas escuras)
    ("cena:fluxo-c", "glyph: { flow: 0.55,", "glyph: { flow: 0.15,", 1),
    ("cena:fluxo-i", "hand: { flow: 0.45,", "hand: { flow: 0.28,", 1),
    ("cena:fluxo-o", "tree: { flow: 0.8, sway: 0.14, rock: 0.055, bob: 0.18", "tree: { flow: 0.12, sway: 0.14, rock: 0.26, bob: 0.2", 1),
    # o material multiplicava a cor da partícula duas vezes (material x instância): o âmbar virava
    # preto e o azul-marinho, quase preto. Com o material branco, a cor real fica só na instância.
    ("cena:material-branco", "    const material = new MeshStandardMaterial({\n      color,\n      roughness: finish.roughness,",
     "    const material = new MeshStandardMaterial({\n      color: 0xffffff,\n      roughness: finish.roughness,", 1),
    # enquadramento: a indústria é mais larga que a mão, e vista em três quartos
    ("cena:industria-escala", "      scale: 7,\n      // Same bead size as the glyph.",
     "      scale: 6.3,\n      // Same bead size as the glyph.", 1),
    ("cena:industria-centro", "      center: [0, 8, -110],", "      center: [5.6, 9.4, -110],", 1),
    ("cena:industria-densa", "      sparse: 0.55,", "      sparse: 0,", 1),
    # traço técnico: menos cópias por ponto (nitidez) e contas mais finas; mesma grade da onda (4 x 12.600 = 50.400)
    ("cena:industria-nitida", "      density: 12,", "      density: 4,", 1),
    ("cena:industria-conta", "      // Same bead size as the glyph.\n      particleSize: 0.1,", "      // Same bead size as the glyph.\n      particleSize: 0.052,", 1),
    ("cena:industria-rotacao", "      rotation: -Math.PI / 6,", "      rotation: -Math.PI / 16,", 1),
    # última dobra: poeira (aDust/uDust) no shader das contas; a mesma uniform vale 1 (sem efeito) nas outras nuvens
    ("cena:dust-uniform", "      shader.uniforms.uFlowAmp = life.uFlowAmp;\n",
     "      shader.uniforms.uFlowAmp = life.uFlowAmp;\n      shader.uniforms.uDust = life.uDust;\n      shader.uniforms.uCloudHide = life.uCloudHide;\n", 1),
    ("cena:dust-decl", 'uniform float uFlowAmp;" + (relax ?', 'uniform float uFlowAmp;\\nattribute vec4 aDust;\\nuniform float uDust;\\nuniform float uCloudHide;" + (relax ?', 1),
    ("cena:dust-vida", "      uFlowAmp: { value: 0 }\n    };\n    patchParticleShader",
     "      uFlowAmp: { value: 0 },\n      uDust: { value: 1 },\n      uCloudHide: { value: 0 }\n    };\n    patchParticleShader", 1),
    ("cena:dust-shader", '          "vGlow += uFlowTint * ( lifeBand * lifeBand * lifeBand );",\n',
     '          "vGlow += uFlowTint * ( lifeBand * lifeBand * lifeBand );",\n'
     '          "float dSpin = ( 1.0 - dT ) * 7.0;",\n'
     '          "vec3 dOff = vec3( aDust.x * cos( dSpin ) - aDust.z * sin( dSpin ), aDust.y, aDust.x * sin( dSpin ) + aDust.z * cos( dSpin ) );",\n'
     '          "dOff.z *= 0.3;",\n'
     '          "dOff += ( 1.0 - dRush ) * vec3( sin( uTime * 0.4 + aDust.y ), cos( uTime * 0.3 + aDust.x ), sin( uTime * 0.5 + aDust.z ) ) * 1.4;",\n'
     '          "wPos.xyz += dOff * ( 1.0 - dRush ) * dHas;",\n'
     '          "vGlow += vec3( 0.0, 0.4, 0.6 ) * ( 1.0 - dT ) * 0.22 * dHas;",\n', 1),
    ("cena:dust-escala", '          "vec3 scanned = transformed * sRev;",\n',
     '          "float dHas = step( 0.0001, dot( aDust.xyz, aDust.xyz ) );",\n'
     '          "float dT = clamp( ( uDust - aDust.w * 0.4 ) / max( 0.0001, 1.0 - aDust.w * 0.4 ), 0.0, 1.0 );",\n'
     '          "float dRush = 1.0 - pow( 1.0 - dT, 4.0 );",\n'
     '          "float dBoost = mix( 1.0 + 0.9 * dHas, 1.0, dRush );",\n'
     '          "vec3 scanned = transformed * sRev * dBoost;",\n', 1),
    ("cena:dust-scroll",
     "          treeCloud.scan.uScan.value = range(\n            progress,\n            sequence.treeScanRange[0],\n            sequence.treeScanRange[1]\n          );\n",
     "          treeCloud.scan.uScan.value = 1;\n          treeCloud.life.uDust.value = range(progress, 0.885, 0.935);\n", 1),
    ("cena:sem-rede-final", "        treeNet.uBuild.value = range(progress, treeScanMid, sequence.treeScanRange[1]);", "        treeNet.uBuild.value = 0;", 1),
    ("cena:logo-gira", "Math.sin(time * 0.24 + 3) * life.tree.rock + cursorYaw", "Math.sin(time * 0.34 + 3) * life.tree.rock + cursorYaw", 1),
    ("cena:logo-revela", "treeCloud.life.uDust.value = range(progress, 0.885, 0.935);\n",
     "treeCloud.life.uDust.value = range(progress, 0.885, 0.935);\n          if (treeCloud.logo) treeCloud.logo.setReveal(range(progress, 0.94, 0.96));\n", 1),
    ("cena:logo-cursor", "            treeRelax?.step(renderer, pointerOnPlaneCam(treeCamera, treeCenter));\n",
     "            const logoHit = pointerOnPlaneCam(treeCamera, treeCenter);\n            treeRelax?.step(renderer, logoHit);\n            if (treeCloud.logo) treeCloud.logo.setPointer(logoHit);\n", 1),
    ("cena:nuvem-oculta", '            "vGlow = max( vGlow, uPointerTint * rel.w );"\n',
     '            "vGlow = max( vGlow, uPointerTint * rel.w );",\n'
     '            "if ( uCloudHide > 0.0 ) { float cVis = mix( 1.0, smoothstep( 0.08, 0.3, rel.w ), uCloudHide ); if ( cVis < 0.02 ) wPos.xyz = vec3( 1e5 ); }"\n', 1),
    ("cena:dust-wipe", "      wipeRange: [0.74, 0.95],", "      wipeRange: [0.74, 0.9],", 1),
    # nome do mapa de dados embutidos
    ("cena:embutidos", "window.__AURALIS_EMBEDDED_ASSETS__", "window.__CRIVIA_EMBEDDED_ASSETS__", 1),
]

# ── Glifo: do X ao C (substitui o trecho de geometria de createGlyphParticles) ──
GLIFO_INI = "    const halfWidth = barWidth / 2;\n    const halfLength = barLength / 2;\n"
GLIFO_FIM = "\n  };\n\n  // shims/embedded-fetch.ts"
GLIFO_C = r"""    // CRIVIA: o "C" é um arco de 270° (abertura à direita, entre -45° e +45°), com pontas arredondadas,
    // e uma esfera dourada no centro. `dist` mede a distância ao eixo do arco.
    const halfWidth = barWidth / 2;
    const halfDepth = barDepth / 2;
    const outerR = barLength / 2 * 0.92;
    const coreR = outerR - halfWidth;
    const GAP = Math.PI / 4;
    const extent = outerR + spill + edgeNoise;
    const depthExtent = halfDepth + spill * 0.5;
    const points = [];
    const normalList = [];
    const nGold = Math.round(count * 0.07);
    const nArc = count - nGold;
    const maxAttempts = count * 60;
    let attempts = 0;
    while (points.length < nArc && attempts < maxAttempts) {
      attempts += 1;
      const x = (random() * 2 - 1) * extent;
      const y = (random() * 2 - 1) * extent;
      const z = (random() * 2 - 1) * depthExtent;
      const theta = Math.atan2(y, x);
      const thetaCore = Math.abs(theta) >= GAP ? theta : (theta >= 0 ? GAP : -GAP);
      const cx = coreR * Math.cos(thetaCore);
      const cy = coreR * Math.sin(thetaCore);
      const dist = Math.hypot(x - cx, y - cy);
      let keep = dist <= halfWidth && Math.abs(z) <= halfDepth;
      if (!keep) {
        const inSpill = dist <= halfWidth + spill && Math.abs(z) <= halfDepth + spill * 0.5;
        keep = inSpill && random() < spillChance;
      }
      if (!keep) continue;
      const fx = (x - cx) / halfWidth;
      const fy = (y - cy) / halfWidth;
      const fz = z / halfDepth;
      let snx = Math.sign(fx) * Math.abs(fx) ** SHARP;
      let sny = Math.sign(fy) * Math.abs(fy) ** SHARP;
      let snz = Math.sign(fz) * Math.abs(fz) ** SHARP;
      const slen = Math.hypot(snx, sny, snz) || 1;
      snx /= slen;
      sny /= slen;
      snz /= slen;
      const jx = x + (random() - 0.5) * edgeNoise;
      const jy = y + (random() - 0.5) * edgeNoise;
      const jz = z + (random() - 0.5) * edgeNoise;
      points.push({
        x: jx * cos + jz * sin,
        y: jy,
        z: -jx * sin + jz * cos
      });
      normalList.push(snx * cos + snz * sin, sny, -snx * sin + snz * cos);
    }
    // esfera dourada no centro do C
    const goldFrom = points.length;
    const goldR = coreR * 0.24;
    while (points.length < count) {
      const gx = Math.sqrt(-2 * Math.log(random() + 1e-9)) * Math.cos(6.2831853 * random());
      const gy = Math.sqrt(-2 * Math.log(random() + 1e-9)) * Math.cos(6.2831853 * random());
      const gz = Math.sqrt(-2 * Math.log(random() + 1e-9)) * Math.cos(6.2831853 * random());
      const gl = Math.hypot(gx, gy, gz) || 1;
      const rr = goldR * Math.cbrt(random());
      const px = gx / gl * rr;
      const py = gy / gl * rr;
      const pz = gz / gl * rr;
      points.push({
        x: px * cos + pz * sin,
        y: py,
        z: -px * sin + pz * cos
      });
      const nx = gx / gl;
      const nz = gz / gl;
      normalList.push(nx * cos + nz * sin, gy / gl, -nx * sin + nz * cos);
    }
    const cloud = buildParticleCloud(points, {
      particleSize,
      sizeJitter,
      bigFraction,
      bigScale,
      color: baseColor,
      finish,
      center,
      extent,
      lightDirection,
      normals: new Float32Array(normalList),
      seed: seed + 1
    });
    const gold = new Color("#F5B82E");
    for (let i = goldFrom; i < count; i += 1) {
      cloud.mesh.setColorAt(i, gold);
      cloud.baseColors[i * 3] = gold.r;
      cloud.baseColors[i * 3 + 1] = gold.g;
      cloud.baseColors[i * 3 + 2] = gold.b;
    }
    cloud.mesh.instanceColor.needsUpdate = true;
    return cloud;
"""

# ── Árvore -> Obra-circuito: etiquetas por ponto (núcleo âmbar, contas ciano) ──
ARVORE_BUSCA_ANTIGA = (
    '    const base2 = "/assets/tree";\n'
    "    const [manifest, binary] = await Promise.all([\n"
    "      embeddedFetch(`${base2}/points.manifest.json`).then((r) => r.json()),\n"
    "      embeddedFetch(`${base2}/points.bin`).then((r) => r.arrayBuffer())\n"
    "    ]);\n")
ARVORE_BUSCA_NOVA = (
    '    const base2 = "/assets/tree";\n'
    "    const [manifest, binary, tagsBinary] = await Promise.all([\n"
    "      embeddedFetch(`${base2}/points.manifest.json`).then((r) => r.json()),\n"
    "      embeddedFetch(`${base2}/points.bin`).then((r) => r.arrayBuffer()),\n"
    "      embeddedFetch(`${base2}/tags.bin`).then((r) => r.arrayBuffer())\n"
    "    ]);\n")
ARVORE_FIM_ANTIGO = "      pointerRelax: true,\n      seed: seed + 1\n    });\n  };\n"
ARVORE_FIM_NOVO = r"""      pointerRelax: true,
      seed: seed + 1
    });
    // CRIVIA: etiquetas por ponto (0 = comum, 1 = núcleo âmbar do decisor, 2 = conta ciano)
    const tags = new Uint8Array(tagsBinary);
    const amber = new Color("#F59E0B");
    const cyan = new Color("#00B4D8");
    const glowArray = cloud.glowAttribute.array;
    for (let i = 0; i < source; i += 1) {
      const t = tags[i];
      if (!t) continue;
      const tint = t === 1 ? amber : cyan;
      const gain = t === 1 ? 0.9 : 0.8;
      for (let d = 0; d < dup; d += 1) {
        const w2 = i * dup + d;
        cloud.mesh.setColorAt(w2, tint);
        cloud.baseColors[w2 * 3] = tint.r;
        cloud.baseColors[w2 * 3 + 1] = tint.g;
        cloud.baseColors[w2 * 3 + 2] = tint.b;
        glowArray[w2 * 3] = tint.r * gain;
        glowArray[w2 * 3 + 1] = tint.g * gain;
        glowArray[w2 * 3 + 2] = tint.b * gain;
      }
    }
    cloud.mesh.instanceColor.needsUpdate = true;
    cloud.glowAttribute.needsUpdate = true;
    return cloud;
  };
"""

# ── Textos e comportamento (app.js) ─────────────────────────────────────────
MAILTO_JS = r"""var CRIVIA_EMAIL = "contato@criviaengenharia.com.br";
  var CRIVIA_MAILTO = (comDados) => {
    let corpo = "";
    if (comDados) {
      const nome = document.querySelector('input[aria-label="Nome"]')?.value ?? "";
      const email = document.querySelector('input[aria-label="E-mail"]')?.value ?? "";
      const prod = window.__criviaProduto ? `Produto de interesse: ${window.__criviaProduto}\n` : "";
      corpo = `Nome: ${nome}\nE-mail: ${email}\n${prod}\n`;
    }
    return `mailto:${CRIVIA_EMAIL}?subject=${encodeURIComponent("Solicitação de Diagnóstico")}&body=${encodeURIComponent(corpo)}`;
  };
  var CTA = "Diagnóstico Sentinela";"""

REDE_INI = "    const cylinder = new CylinderGeometry(\n"
REDE_FIM = '    geometry.setAttribute("aSeed", new BufferAttribute(seeds, 1));'
REDE_NOVA = r"""    // CRIVIA: no lugar da gaiola cilíndrica, uma rede de comunicação — nós ligados aos vizinhos mais próximos,
    // sobre uma casca cilíndrica que gira devagar; os pulsos do modelo viram "sinais" correndo pelas conexões.
    const random = createRandom(BUILD_SEED);
    const NODES = 84;
    const RAD = config2.radiusTop;
    const HGT = config2.height;
    const nodes = [];
    for (let i = 0; i < NODES; i += 1) {
      const a = random() * Math.PI * 2;
      const rr = RAD * (0.86 + random() * 0.14);
      const y = ((i + random() * 0.8) / NODES - 0.5) * HGT * 0.92;
      nodes.push([Math.cos(a) * rr, y, Math.sin(a) * rr]);
    }
    const segs = [];
    const seen = new Set();
    for (let i = 0; i < NODES; i += 1) {
      const near = nodes.map((n, j) => [j, Math.hypot(n[0] - nodes[i][0], n[1] - nodes[i][1], n[2] - nodes[i][2])]).filter((e) => e[0] !== i).sort((x, y) => x[1] - y[1]).slice(0, 3);
      for (const [j] of near) {
        const key = i < j ? i + "-" + j : j + "-" + i;
        if (seen.has(key)) continue;
        seen.add(key);
        segs.push([nodes[i], nodes[j]]);
      }
    }
    const edgeList = segs.slice();
    for (const n of nodes) {
      const k = 0.22;
      segs.push([[n[0] - k, n[1], n[2]], [n[0] + k, n[1], n[2]]], [[n[0], n[1] - k, n[2]], [n[0], n[1] + k, n[2]]], [[n[0], n[1], n[2] - k], [n[0], n[1], n[2] + k]]);
    }
    const vertexCount = segs.length * 2;
    const positions = new Float32Array(vertexCount * 3);
    const seeds = new Float32Array(vertexCount);
    const ends = new Float32Array(vertexCount);
    segs.forEach((sg, k) => {
      positions.set(sg[0], k * 6);
      positions.set(sg[1], k * 6 + 3);
      const r = random();
      seeds[k * 2] = r;
      seeds[k * 2 + 1] = r;
      ends[k * 2] = 0;
      ends[k * 2 + 1] = 1;
    });
    const geometry = new BufferGeometry();
    geometry.setAttribute("position", new BufferAttribute(positions, 3));
"""

PATCHES_REDE_OPACIDADE = [("cena:rede-opacidade", "      opacity: 0.32,\n      centerY: 10.5,", "      opacity: 0.55,\n      centerY: 10.5,", 1)]

MAO_BUSCA_ANTIGA = (
    '    const base2 = "/assets/hand";\n'
    "    const [manifest, binary] = await Promise.all([\n"
    "      embeddedFetch(`${base2}/points.manifest.json`).then((r) => r.json()),\n"
    "      embeddedFetch(`${base2}/points.bin`).then((r) => r.arrayBuffer())\n"
    "    ]);\n")
MAO_BUSCA_NOVA = (
    '    const base2 = "/assets/hand";\n'
    "    const [manifest, binary, tagsBinary] = await Promise.all([\n"
    "      embeddedFetch(`${base2}/points.manifest.json`).then((r) => r.json()),\n"
    "      embeddedFetch(`${base2}/points.bin`).then((r) => r.arrayBuffer()),\n"
    "      embeddedFetch(`${base2}/tags.bin`).then((r) => r.arrayBuffer())\n"
    "    ]);\n")
MAO_FIM_ANTIGO = "      scatterDest: buildWaveDestinations(count, wave, center),\n      seed: seed + 1\n    });\n  };\n"
MAO_FIM_NOVO = r"""      scatterDest: buildWaveDestinations(count, wave, center),
      seed: seed + 1
    });
    // CRIVIA: cores por parte (0 azul-marinho, 1 dourado, 2 royal, 3 ciano)
    const tagsMao = new Uint8Array(tagsBinary);
    const paletaMao = [null, new Color("#F5B82E"), new Color("#0A369D"), new Color("#00B4D8")];
    for (let i = 0; i < source; i += 1) {
      const col = paletaMao[tagsMao[i]];
      if (!col) continue;
      for (let d = 0; d < dup; d += 1) {
        const w2 = i * dup + d;
        cloud.mesh.setColorAt(w2, col);
        cloud.baseColors[w2 * 3] = col.r;
        cloud.baseColors[w2 * 3 + 1] = col.g;
        cloud.baseColors[w2 * 3 + 2] = col.b;
      }
    }
    cloud.mesh.instanceColor.needsUpdate = true;
    return cloud;
  };
"""

# Dobra da indústria (logo após a hero): duas áreas — texto, sequência e ação à esquerda; a indústria em pontos à direita —
# e uma faixa de indicadores separada, embaixo. Tipografia no padrão da hero (Plus Jakarta Sans nos títulos, Geist nos textos).
PATCHES_TIPO_IND = [
    # a chegada em blur-up, linha por linha, vale também para esta dobra
    ("ind:chegada", '    const layer = act === "hero" ? {', '    const layer = act === "hero" || act === "hand" ? {', 1),
    # a rede de fundo some nesta dobra: menos linhas finas ao redor da forma
    ("ind:rede", "handNet.uBuild.value = range(seqP, 0.3, 0.47);", "handNet.uBuild.value = 0;", 1),
]

HAND_INI = "  var HandOverlay = () => {"
HAND_FIM = "\n\n  // orig/src/components/common/hero-overlay/wave-overlay.tsx"
HAND_NOVO = r"""  var HandOverlay = () => {
    const passos = ["Incerteza", "Método", "Prova"];
    const indicadores = [
      { n: "20", u: "anos", r: "de experiência em engenharia e gestão de projetos" },
      { n: "35", u: "projetos", r: "conduzidos simultaneamente" },
      { n: "R$ 380", u: "mi", r: "valor global de empreendimento industrial" }
    ];
    return /* @__PURE__ */ (0, import_jsx_runtime19.jsxs)("div", { className: "crivia-ind pointer-events-none select-none font-display text-overlay-ink", children: [
      /* @__PURE__ */ (0, import_jsx_runtime19.jsxs)("div", { className: "crivia-ind__topo", children: [
        /* @__PURE__ */ (0, import_jsx_runtime19.jsx)(RevealText, { tag: "h2", variant: "heading", act: "hand", className: "crivia-ind-titulo", children: "O problema quase nunca está onde aparece." }),
        /* @__PURE__ */ (0, import_jsx_runtime19.jsx)(RevealText, { tag: "p", variant: "copy", act: "hand", delayIn: 160, className: "font-geist crivia-ind-texto", children: "Atrasos, medições travadas e informações contraditórias podem ser sinais. A CRIVIA cruza contratos, cronogramas, custos e realidade de campo para identificar causas, avaliar riscos e apoiar decisões com caminhos claros." }),
        /* @__PURE__ */ (0, import_jsx_runtime19.jsx)("ol", { className: "crivia-ind-seq", "aria-label": "Incerteza, método, prova", children: passos.map((nome, i) => /* @__PURE__ */ (0, import_jsx_runtime19.jsx)(RevealItem, { tag: "li", act: "hand", index: i, count: passos.length, delay: 320, className: "crivia-ind-passo" + (i === passos.length - 1 ? " crivia-ind-passo--ouro" : ""), children: nome }, nome)) })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime19.jsxs)("div", { className: "crivia-ind__acao", children: [
        /* @__PURE__ */ (0, import_jsx_runtime19.jsx)(RevealItem, { act: "hand", index: 0, count: 1, delay: 520, className: "flex-none", children: /* @__PURE__ */ (0, import_jsx_runtime19.jsx)(CriviaCtaPrimary, { onClick: () => CRIVIA_ABRIR_CENARIO("industria"), children: "Apresentar meu cenário" }) }),
        /* @__PURE__ */ (0, import_jsx_runtime19.jsx)(RevealText, { tag: "p", variant: "copy", act: "hand", delayIn: 640, className: "font-geist crivia-ind-nota", children: "O formulário reúne as informações iniciais para compreender o contexto." })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime19.jsxs)("div", { className: "crivia-ind-faixa", children: [
        /* @__PURE__ */ (0, import_jsx_runtime19.jsxs)("div", { className: "crivia-ind-faixa__cab", children: [
          /* @__PURE__ */ (0, import_jsx_runtime19.jsx)(RevealText, { tag: "h3", variant: "heading", act: "hand", delayIn: 240, className: "crivia-ind-faixa__titulo", children: "Experiência que sustenta a atuação da CRIVIA" }),
          /* @__PURE__ */ (0, import_jsx_runtime19.jsx)(RevealText, { tag: "p", variant: "copy", act: "hand", delayIn: 340, className: "font-geist crivia-ind-faixa__apoio", children: "A CRIVIA aplica experiência técnica e executiva em engenharia, gestão de contratos e empreendimentos complexos." })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime19.jsx)("ul", { className: "crivia-ind-stats", children: indicadores.map((ind, i) => /* @__PURE__ */ (0, import_jsx_runtime19.jsxs)(RevealItem, { tag: "li", act: "hand", index: i, count: indicadores.length, delay: 260, className: "crivia-ind-stat", children: [
          /* @__PURE__ */ (0, import_jsx_runtime19.jsxs)("span", { className: "crivia-ind-valor", children: [
            /* @__PURE__ */ (0, import_jsx_runtime19.jsx)("span", { className: "crivia-ind-valor__n", children: ind.n }),
            /* @__PURE__ */ (0, import_jsx_runtime19.jsx)("span", { className: "crivia-ind-valor__u", children: ind.u })
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime19.jsx)("span", { className: "crivia-ind-rotulo", children: ind.r })
        ] }, ind.n)) })
      ] })
    ] });
  };"""

CSS_IND = r"""
/* ════ CRIVIA ════ dobra da indústria: texto, percurso e ação à esquerda; indústria à direita; faixa de experiência embaixo ════ */
.crivia-ind { position: absolute; inset: 0; box-sizing: border-box; display: grid; padding: 4.5rem 1.25rem 1.1rem; row-gap: .75rem;
  grid-template-columns: minmax(0, 1fr); grid-template-rows: auto auto minmax(0, 1fr) auto;
  grid-template-areas: "topo" "acao" "meio" "faixa"; }
.crivia-ind__topo { grid-area: topo; display: flex; flex-direction: column; align-items: flex-start; gap: .7rem; }
.crivia-ind__acao { grid-area: acao; display: flex; flex-direction: column; align-items: flex-start; width: fit-content; gap: .5rem; pointer-events: auto; }
.crivia-ind-faixa { grid-area: faixa; }
.crivia-ind-titulo { font-size: clamp(1.65rem, 3.5vw, 3.35rem); font-weight: 650; line-height: 1.05; letter-spacing: -.035em; color: #001D3D; margin-left: -.04em; }
.crivia-ind-texto { position: relative; padding-top: .8rem; width: 100%; max-width: 100%; font-size: .86rem; font-weight: 500; line-height: 1.45; letter-spacing: -.005em; color: #001D3D; text-align: justify; -webkit-hyphens: auto; hyphens: auto; }
.crivia-ind-texto { justify-content: space-between; }
.crivia-ind-texto::after { content: ""; flex: 1 1 0; }
.crivia-ind-texto::before { content: ""; position: absolute; top: 0; left: 0; width: 2.6rem; height: 3px; border-radius: 2px;
  background: linear-gradient(90deg, #F5B82E, #0A369D); }
/* percurso: três etapas em texto, ligadas por setas (sem fundo nem borda, para não parecerem botões) */
.crivia-ind-seq { display: flex; flex-wrap: wrap; align-items: center; gap: .3rem 2.6rem; margin: 0; padding: 0; list-style: none; }
.crivia-ind-passo { position: relative; padding-left: .95rem; font-size: .88rem; font-weight: 650; line-height: 1.2; letter-spacing: -.01em; color: #0A369D; }
.crivia-ind-passo::before { content: ""; position: absolute; left: 0; top: 50%; width: 6px; height: 6px; margin-top: -3px; border-radius: 50%; background: #0A369D; }
.crivia-ind-passo:not(:last-child)::after { content: "\2192"; position: absolute; right: -1.95rem; top: 50%; transform: translateY(-54%); font-size: 1.7em; line-height: 1; font-weight: 500; color: #0A369D; opacity: .75; }
.crivia-ind-passo--ouro { color: #001D3D; }
.crivia-ind-passo--ouro::before { background: #F5B82E; box-shadow: 0 0 0 3px rgba(245,184,46,.28); }
.crivia-ind-nota { font-family: "Geist", system-ui, sans-serif; font-size: .76rem; font-weight: 450; line-height: 1.45; color: #2B4A6B; width: 0; min-width: 100%; }
/* faixa de experiência */
.crivia-ind-faixa { padding: .75rem .9rem .85rem; border-radius: 1.15rem;
  background: linear-gradient(180deg, rgba(255,255,255,.72) 0%, rgba(240,248,252,.46) 100%);
  -webkit-backdrop-filter: blur(20px) saturate(1.3); backdrop-filter: blur(20px) saturate(1.3);
  border: 1px solid rgba(255,255,255,.78); box-shadow: 0 14px 44px rgba(0,29,61,.1), inset 0 1px 0 rgba(255,255,255,.85); }
.crivia-ind-faixa__cab { display: flex; flex-direction: column; gap: .3rem; margin-bottom: .6rem; padding-bottom: .55rem; border-bottom: 1px solid rgba(10,54,157,.13); }
.crivia-ind-faixa__titulo { font-size: .9rem; font-weight: 650; line-height: 1.2; letter-spacing: -.02em; color: #001D3D; max-width: 13em; }
.crivia-ind-faixa__apoio { font-family: "Geist", system-ui, sans-serif; font-size: .62rem; font-weight: 450; line-height: 1.35; color: #2B4A6B; }
.crivia-ind-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 0; padding: 0; list-style: none; }
.crivia-ind-stat { display: flex; flex-direction: column; align-items: flex-start; gap: .3rem; padding: 0 .6rem; min-width: 0; }
.crivia-ind-stat + .crivia-ind-stat { border-left: 1px solid rgba(10,54,157,.16); }
.crivia-ind-stat:first-child { padding-left: .1rem; }
.crivia-ind-valor { display: flex; align-items: baseline; gap: .28em; font-size: 1.1rem; font-weight: 700; line-height: 1.1; letter-spacing: -.03em; white-space: nowrap; }
.crivia-ind-valor__n { padding-right: .06em; background: linear-gradient(180deg, #1A4CA8 0%, #001D3D 100%); -webkit-background-clip: text; background-clip: text;
  color: transparent; -webkit-text-fill-color: transparent; }
.crivia-ind-valor__u { font-size: .52em; font-weight: 650; letter-spacing: -.01em; color: #0A369D; }
.crivia-ind-rotulo { font-family: "Geist", system-ui, sans-serif; font-size: .58rem; font-weight: 500; line-height: 1.28; color: #001D3D; opacity: .86; max-width: 15.5em; }
@media (min-width: 48rem) {
  .crivia-ind { padding: 7rem 4.5rem 2.5rem; row-gap: 0; column-gap: 2rem;
    grid-template-columns: min(31rem, 46vw) minmax(0, 1fr); grid-template-rows: auto minmax(0, 1fr) auto;
    grid-template-areas: "topo meio" "acao meio" "faixa faixa"; }
  .crivia-ind__topo { gap: 1.1rem; }
  .crivia-ind__acao { margin-top: 1.6rem; gap: .7rem; align-self: start; }
  .crivia-ind-texto { font-size: 1.04rem; padding-top: 1.05rem; }
  .crivia-ind-passo { font-size: 1rem; }
  .crivia-ind-nota { font-size: .82rem; }
  .crivia-ind-faixa { padding: clamp(1.1rem, 1.5vw, 1.7rem) clamp(1.7rem, 2.2vw, 2.6rem) clamp(1.3rem, 1.7vw, 2rem); }
  .crivia-ind-faixa__cab { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: end; gap: 0; margin-bottom: 1rem; padding-bottom: .85rem; }
  .crivia-ind-faixa__titulo { grid-column: 1; }
  .crivia-ind-faixa__titulo { font-size: clamp(1.2rem, 1.55vw, 1.85rem); }
  .crivia-ind-faixa__apoio { grid-column: 2 / span 2; max-width: none; padding-left: clamp(1.7rem, 2.2vw, 2.6rem); font-size: clamp(.88rem, 1.02vw, 1.2rem); line-height: 1.45; }
  .crivia-ind-stat { padding: 0 clamp(1.7rem, 2.2vw, 2.6rem); gap: .4rem; }
  .crivia-ind-stat:first-child { padding-left: 0; }
  .crivia-ind-valor { font-size: clamp(2.15rem, 2.75vw, 3.4rem); }
  .crivia-ind-rotulo { font-size: clamp(.82rem, 1vw, 1.2rem); }
}
@media (min-width: 48rem) and (max-height: 760px) {
  .crivia-ind { padding-top: 5.75rem; padding-bottom: 1.75rem; }
  .crivia-ind__topo { gap: .8rem; }
  .crivia-ind__acao { margin-top: 1.1rem; }
  .crivia-ind-faixa { padding: .85rem 1.5rem 1rem; }
  .crivia-ind-valor { font-size: 1.7rem; }
}
@media (prefers-reduced-motion: reduce) {
  .crivia-ind-faixa, .crivia-ind-passo { transition: none; }
}
"""

# Dobra "Quatro frentes de trabalho" (cena da onda) = catálogo: quatro grupos iguais na tela; cada grupo é um baralho de cartas alinhadas
# (faixa + pedaço da foto); a carta sob o mouse abre pela lateral. Cartas em azul com degradê (escuro em cima, mais claro embaixo).
# Botão primário da hero em versão mini. Conteúdo: Catálogo R03 (pedido do cliente e entregas).
CAT_INI = "  var WaveOverlay = () => {"
CAT_FIM = "\n\n  // orig/src/components/common/hero-overlay/live-dot.tsx"
CAT_NOVO = r"""  var CRIVIA_ICONES = {
    clipboard: ["M9 3.5h6v3H9z", "M7 5H6.2A1.2 1.2 0 0 0 5 6.2v13.6A1.2 1.2 0 0 0 6.2 21h11.6a1.2 1.2 0 0 0 1.2-1.2V6.2A1.2 1.2 0 0 0 17.8 5H17", "M8.5 11.5h7", "M8.5 15.5h4.5"],
    layers: ["M12 3 3 8l9 5 9-5-9-5z", "M3 12.5l9 5 9-5", "M3 17l9 5 9-5"],
    pin: ["M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21z", "M12 12.2a2.7 2.7 0 1 0 0-5.4 2.7 2.7 0 0 0 0 5.4z"],
    calc: ["M6 3h12a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z", "M8 7h8", "M8.5 12h.01", "M12 12h.01", "M15.5 12h.01", "M8.5 16h.01", "M12 16h.01", "M15.5 16h.01"],
    scale: ["M12 3v18", "M5 7h14", "M5 7l-3 7a3 3 0 0 0 6 0L5 7z", "M19 7l-3 7a3 3 0 0 0 6 0l-3-7z", "M8 21h8"],
    calendar: ["M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z", "M4 10h16", "M8 3v4", "M16 3v4"],
    rotate: ["M20 12a8 8 0 1 1-2.4-5.7", "M20 4v5h-5"],
    pulse: ["M3 12h4l3-8 4 16 3-8h4"],
    ruler: ["M3 17 17 3l4 4L7 21l-4-4z", "M7.5 12.5l2 2", "M10.5 9.5l2 2", "M13.5 6.5l2 2"],
    eye: ["M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z", "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"],
    check: ["M3.5 4h17a.5.5 0 0 1 .5.5v15a.5.5 0 0 1-.5.5h-17a.5.5 0 0 1-.5-.5v-15a.5.5 0 0 1 .5-.5z", "M8 12.5l3 3 5-6"],
    folder: ["M3 6.5A1.5 1.5 0 0 1 4.5 5H9l2 2.5h8.5A1.5 1.5 0 0 1 21 9v9.5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18.5v-12z"],
    video: ["M3 6.5h12a1.5 1.5 0 0 1 1.5 1.5v8a1.5 1.5 0 0 1-1.5 1.5H3A1.5 1.5 0 0 1 1.5 16V8A1.5 1.5 0 0 1 3 6.5z", "M16.5 10l5-2.5v9l-5-2.5"],
    chip: ["M12 3v3", "M12 18v3", "M3 12h3", "M18 12h3", "M7 7h10v10H7z", "M10 10h4v4h-4z"]
  };
  var CRIVIA_PRODUTOS = [
    { cod: "P01", ico: "clipboard", nome: "Diagnóstico de obra ou contrato", txt: "Compreender por que o projeto, a obra ou o contrato não entrega o resultado esperado, ou esclarecer uma situação técnica ainda indefinida.", ent: "Relatório de diagnóstico · Registro de evidências · Matriz de impedimentos, riscos e pendências · Síntese de decisões e reunião de devolutiva" },
    { cod: "P02", ico: "layers", nome: "Análise crítica de projetos", txt: "Os projetos recebidos estão completos e coerentes para a decisão que preciso tomar?", ent: "Relatório de análise · Matriz de interfaces · Pranchas comentadas · Registro de respostas e pendências" },
    { cod: "P03", ico: "pin", nome: "Avaliação preliminar de terreno", txt: "Quais condições deste terreno preciso conhecer antes de contratar projetos ou construir?", ent: "Parecer preliminar · Registro de visita · Matriz de informações e estudos · Roteiro de contratação dos estudos" },
    { cod: "P04", ico: "calc", nome: "Orçamento e análise de custos", txt: "Quanto preciso prever e quais itens explicam o custo apresentado?", ent: "Planilha orçamentária · Memória de quantitativos · Relatório de premissas · Análise dos itens relevantes" },
    { cod: "P05", ico: "scale", nome: "Comparação técnica de propostas", txt: "Qual proposta atende ao que preciso e o que está faltando em cada preço?", ent: "Quadro comparativo · Lista de esclarecimentos · Relatório de recomendação · Anexo de escopo técnico" },
    { cod: "P06", ico: "calendar", nome: "Planejamento de obra e recursos", txt: "Qual sequência, prazo e recurso preciso pactuar com quem vai executar?", ent: "Estrutura de atividades e cronograma físico · Cronograma físico-financeiro · Histogramas · Plano de suprimentos e controle" },
    { cod: "P07", ico: "rotate", nome: "Plano de recuperação de obra", txt: "Decidir o que precisa mudar e qual caminho cabe nos recursos, nas restrições e nos compromissos existentes.", ent: "Proposta técnica de solução · Plano de ação · Cronograma ou programação de recursos · Análise de custos, quando contratada" },
    { cod: "P08", ico: "pulse", nome: "Análise de processo e produtividade", txt: "Onde o processo perde tempo e recursos e qual mudança merece ser testada?", ent: "Mapa do processo · Base de observações · Estudo comparativo · Plano de teste" },
    { cod: "P09", ico: "ruler", nome: "Medições e alterações contratuais", txt: "Como demonstrar o que foi executado e organizar as diferenças de escopo e pagamento?", ent: "Boletim de medição · Memória e evidências · Registro de alterações · Dossiê técnico" },
    { cod: "P10", ico: "eye", nome: "Acompanhamento técnico das decisões", txt: "Verificar se as providências estão ocorrendo, se produzem o efeito esperado e o que precisa ser revisto.", ent: "Relatório periódico · Painel de acompanhamento · Registro de visitas e evidências · Registro de decisões e mudanças" },
    { cod: "P11", ico: "check", nome: "Vistoria para recebimento", txt: "Quais pendências preciso registrar antes de receber a obra ou uma etapa?", ent: "Relatório de vistoria · Registro fotográfico · Lista de pendências" },
    { cod: "P12", ico: "folder", nome: "Organização e conferência do data book", txt: "Quais documentos da obra devem ser reunidos e o que ainda falta entregar?", ent: "Índice mestre · Pasta digital organizada · Matriz de lacunas · Relatório de conferência" },
    { cod: "IA-1", ico: "chip", nome: "Preparação da transição para IA", txt: "A empresa vai ampliar o uso de IA e precisa definir como funções, competências, verificações e interfaces mudarão.", ent: "Plano de Transição e Integração do Trabalho com IA" },
    { cod: "IA-2", ico: "pulse", nome: "Diagnóstico e ajustes após a adoção", txt: "Ferramentas já em uso, mas persistem erros, retrabalho, decisões inadequadas, sobrecarga ou desencontro entre áreas.", ent: "Relatório de Diagnóstico e Ajustes do Trabalho com IA · Plano de ação editável" },
    { cod: "CV01", ico: "video", nome: "Visualização e comunicação técnica com IA e 3D", txt: "Tornar compreensíveis uma situação, um projeto, uma solução ou uma proposta técnico-comercial, por meio de imagens, representações 3D, apresentações e vídeos.", ent: "Vídeos explicativos de engenharia · Apresentações visuais de projetos e soluções · Propostas técnico-comerciais visuais" }
  ];
  var CRIVIA_GRUPOS = [
    { id: "g1", nome: "Diagnóstico e recuperação", curto: "Diagnóstico", cods: ["P01", "P07", "P08", "P10"] },
    { id: "g2", nome: "Projetos, terreno e propostas", curto: "Projetos", cods: ["P02", "P03", "P05"] },
    { id: "g3", nome: "Custos, planejamento e medições", curto: "Custos", cods: ["P04", "P06", "P09", "P11", "P12"] },
    { id: "g4", nome: "Portfólio de IA", curto: "IA", cods: ["IA-1", "IA-2", "CV01"] }
  ];
  var CriviaCarta = ({ p, ordem, total, aberto, pedir, fixar, grupo }) => {
    const abre = aberto === p.cod;
    const corpoRef = (0, import_react35.useRef)(null);
    (0, import_react35.useEffect)(() => {
      const el = corpoRef.current;
      if (!el || !el.parentElement) return;
      const q = el.parentElement;
      const medir = () => q.style.setProperty("--hn", (el.scrollHeight + 8) + "px");
      medir();
      if (typeof ResizeObserver === "undefined") return;
      const ro = new ResizeObserver(medir);
      ro.observe(el);
      return () => ro.disconnect();
    }, []);
    return /* @__PURE__ */ (0, import_jsx_runtime20.jsx)(RevealItem, { tag: "li", act: "wave", index: ordem, count: total, delay: 200, className: "crivia-carta" + (abre ? " is-aberta" : ""), children: /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("div", {
      className: "crivia-carta__quadro",
      style: { "--z": ordem + 1 },
      tabIndex: 0,
      "aria-expanded": abre,
      onPointerEnter: (e) => { if (e.pointerType === "mouse") pedir(p.cod); },
      onFocus: () => fixar(p.cod),
      onClick: (e) => { if (e.target.closest && e.target.closest("button")) return; fixar(abre ? null : p.cod); },
      children: [
        /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("div", { ref: corpoRef, className: "crivia-carta__corpo", children: [
          /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("div", { className: "crivia-carta__topo", children: [
            /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("span", { className: "crivia-carta__icone", children: criviaIcon(CRIVIA_ICONES[p.ico]) }),
            /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("span", { className: "font-geist crivia-carta__cod", children: p.cod }),
            /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("span", { className: "crivia-carta__nome-curto", children: p.nome }),
            /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("span", { className: "font-geist crivia-carta__chip", children: grupo })
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("div", { className: "crivia-carta__img", children: [
            /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("span", { className: "crivia-carta__ph", "aria-hidden": true, children: criviaIcon(CRIVIA_ICONES[p.ico]) }),
            /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("img", { src: "assets/images/produtos/" + p.cod + ".jpg", alt: "", loading: "lazy", decoding: "async", onError: (e) => { e.currentTarget.style.display = "none"; } })
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("h3", { className: "crivia-carta__titulo", children: p.nome }),
          /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("p", { className: "font-geist crivia-carta__txt", children: p.txt }),
          /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("p", { className: "font-geist crivia-carta__ent", children: [/* @__PURE__ */ (0, import_jsx_runtime20.jsx)("b", { children: "Você recebe" }), p.ent] }),
          /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("div", { className: "crivia-carta__acao", children: /* @__PURE__ */ (0, import_jsx_runtime20.jsx)(CriviaCtaPrimary, { compacto: true, onClick: () => { CRIVIA_ABRIR_CENARIO("produtos", p.cod); }, children: "Apresentar meu cenário" }) })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("span", { className: "crivia-carta__vert", "aria-hidden": true, children: p.nome })
      ]
    }) });
  };
  var CriviaGrupo = ({ g, gi, base, total, aberto, pedir, fixar }) => {
    const itens = g.cods.map((c) => CRIVIA_PRODUTOS.find((p) => p.cod === c));
    const abre = itens.some((p) => p.cod === aberto);
    return /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("li", { className: "crivia-g" + (abre ? " is-aberto" : ""), style: { "--n": itens.length }, children: [
      /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("div", { className: "crivia-g__rotulo", children: [
        /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("span", { className: "font-geist crivia-g__num", children: ["0", gi + 1] }),
        /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("span", { className: "crivia-g__nome", children: g.nome }),
        /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("span", { className: "crivia-g__linha", "aria-hidden": true }),
        /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("span", { className: "font-geist crivia-g__qtd", children: [itens.length, " produtos"] })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("ul", { className: "crivia-g__deck", children: itens.map((p, k) => /* @__PURE__ */ (0, import_jsx_runtime20.jsx)(CriviaCarta, { p, ordem: base + k, total, aberto, pedir, fixar, grupo: g.curto }, p.cod)) })
    ] });
  };
  var CriviaCatalogo = () => {
    const [aberto, setAberto] = (0, import_react35.useState)(null);
    const timer = (0, import_react35.useRef)(0);
    const pedir = (cod) => { clearTimeout(timer.current); timer.current = setTimeout(() => setAberto(cod), cod === null ? 140 : 70); };
    const fixar = (cod) => { clearTimeout(timer.current); setAberto(cod); };
    let base = 0;
    return /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("div", { className: "crivia-cat", children: /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("div", { className: "crivia-cat__in", children: [
      /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("header", { className: "crivia-cat__cab", children: [
        /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("div", { className: "crivia-cat__cab-esq", children: [
          /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("span", { className: "font-geist crivia-cat__selo", children: [
            /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("span", { className: "crivia-cat__selo-ponto", "aria-hidden": true }),
            "Catálogo de produtos"
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime20.jsx)(RevealText, { tag: "h2", variant: "heading", act: "wave", className: "crivia-cat__titulo", children: "Produtos para cada decisão." })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime20.jsx)(RevealText, { tag: "p", variant: "copy", act: "wave", delayIn: 160, className: "font-geist crivia-cat__intro", children: "Os 12 produtos de engenharia estão disponíveis conforme a necessidade, o objeto e a capacidade técnica. Podem ser contratados individualmente, combinados ou em ciclos definidos; a proposta discrimina as entregas incluídas." })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("ul", { "data-lenis-prevent": true, className: "crivia-grupos", onPointerLeave: (e) => { if (e.pointerType === "mouse") pedir(null); }, children: CRIVIA_GRUPOS.map((g, gi) => {
        const b = base;
        base += g.cods.length;
        return /* @__PURE__ */ (0, import_jsx_runtime20.jsx)(CriviaGrupo, { g, gi, base: b, total: CRIVIA_PRODUTOS.length, aberto, pedir, fixar }, g.id);
      }) }),
      /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("div", { className: "crivia-cat__rodape", children: [
        /* @__PURE__ */ (0, import_jsx_runtime20.jsxs)("div", { className: "crivia-cat__metodo-bloco", children: [
          /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("button", { type: "button", className: "font-geist crivia-cat__metodo-sel", onClick: () => CRIVIA_NAV["Método"](), children: "Método Sentinela" }),
          /* @__PURE__ */ (0, import_jsx_runtime20.jsx)(RevealText, { tag: "p", variant: "copy", act: "wave", delayIn: 320, className: "font-geist crivia-cat__metodo", children: "Observar, confrontar, integrar, propor e apoiar. Primeiro a referência, depois o campo, depois o confronto entre os dois." })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("p", { className: "font-geist crivia-cat__dica", children: "Passe o cursor ou toque em uma carta para abri-la." })
      ] })
    ] }) });
  };
  var WaveOverlay = () => {
    const rootRef = (0, import_react35.useRef)(null);
    const contentRef = (0, import_react35.useRef)(null);
    (0, import_react35.useEffect)(() => {
      const root = rootRef.current;
      const content = contentRef.current;
      if (!root || !content) return;
      let raf3 = 0;
      let last = Number.NaN;
      const tick2 = () => {
        raf3 = requestAnimationFrame(tick2);
        const progress = getScrollProgress();
        const fator = criviaCatalogoFator();
        const chave = progress + ":" + fator;
        if (chave === last) return;
        last = chave;
        const { left: l, right: r } = wipeLineAt(progress);
        root.style.clipPath = l >= 100 && r >= 100 ? "none" : `polygon(0% 0%, 100% 0%, 100% ${r}%, 0% ${l}%)`;
        content.style.transform = `translateY(${waveDriftAt(progress)}vh)`;
        const opac = waveUiOpacityAt(progress) * fator;
        content.style.opacity = `${opac}`;
        content.style.visibility = opac <= 0.01 || progress < 0.57 ? "hidden" : "visible";
      };
      raf3 = requestAnimationFrame(tick2);
      return () => cancelAnimationFrame(raf3);
    }, []);
    return /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("div", { ref: rootRef, className: "pointer-events-none absolute inset-0 select-none font-display text-overlay-ink", children: /* @__PURE__ */ (0, import_jsx_runtime20.jsx)("div", { ref: contentRef, className: "absolute inset-0", children: /* @__PURE__ */ (0, import_jsx_runtime20.jsx)(CriviaCatalogo, {}) }) });
  };"""

CSS_CAT = r"""
/* ════ CRIVIA ════ catálogo: quatro grupos iguais; cada um é um baralho de cartas alinhadas que abre pela lateral ════ */
.crivia-cat { position: absolute; inset: 0; overflow: hidden; box-sizing: border-box;
  background: linear-gradient(180deg, rgba(247,251,254,.6) 0%, rgba(240,248,252,.78) 100%); }
.crivia-cat__in { box-sizing: border-box; height: 100%; max-width: 82rem; margin: 0 auto; padding: 4.5rem 1.25rem 1rem;
  display: flex; flex-direction: column; gap: .85rem; pointer-events: auto; }
.crivia-cat__cab { display: flex; flex-direction: column; gap: .6rem; }
.crivia-cat__cab-esq { display: flex; flex-direction: column; align-items: flex-start; gap: .6rem; }
.crivia-cat__selo { display: inline-flex; align-items: center; gap: .5rem; padding: .3rem .8rem; border-radius: 999px; font-size: .66rem; font-weight: 600;
  letter-spacing: .12em; text-transform: uppercase; color: #2B4A6B; background: rgba(255,255,255,.75); border: 1px solid rgba(10,54,157,.16); }
.crivia-cat__selo-ponto { width: 6px; height: 6px; border-radius: 50%; background: #F5B82E; box-shadow: 0 0 0 3px rgba(245,184,46,.28); }
.crivia-cat__titulo { font-size: clamp(1.65rem, 3vw, 2.75rem); font-weight: 650; line-height: 1.05; letter-spacing: -.035em; color: #001D3D; }
.crivia-cat__intro, .crivia-cat__metodo, .crivia-cat__metodo-bloco { display: none !important; }
.crivia-cat__dica { margin: 0; font-size: .7rem; font-weight: 500; letter-spacing: .03em; color: #2B4A6B; opacity: .8; text-align: center; }

/* grupos (celular: um embaixo do outro) */
.crivia-grupos { flex: 1; min-height: 0; overflow-y: auto; margin: 0; padding: .3rem .15rem 1rem; list-style: none; display: flex; flex-direction: column; gap: 1.1rem; scrollbar-width: none; }
.crivia-grupos::-webkit-scrollbar { display: none; }
.crivia-g { --cw: 17rem; --min: 3rem; position: relative; }
.crivia-g__rotulo { display: flex; align-items: center; gap: .6rem; min-height: 2rem; margin-bottom: .55rem; }
.crivia-g__num { flex: none; display: inline-flex; align-items: center; justify-content: center; min-width: 1.9rem; height: 1.9rem; padding: 0 .45rem; border-radius: 999px;
  font-size: .74rem; font-weight: 700; letter-spacing: .06em; color: #fff; background: linear-gradient(135deg, #0A369D, #2F6BFF);
  box-shadow: 0 6px 16px rgba(47,107,255,.34), inset 0 1px 0 rgba(255,255,255,.35); }
.crivia-g__nome { min-width: 0; font-size: 1.2rem; font-weight: 700; line-height: 1.1; letter-spacing: -.03em; padding-bottom: .08em;
  background: linear-gradient(90deg, #0A369D 0%, #1F5BFF 55%, #2F8CFF 100%); -webkit-background-clip: text; background-clip: text; color: transparent; -webkit-text-fill-color: transparent;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.crivia-g__linha, .crivia-g__qtd { display: none; }
.crivia-g__deck { display: flex; flex-direction: column; margin: 0; padding: 0; list-style: none; }

/* carta: azul em degradê, escuro em cima e mais claro embaixo */
.crivia-carta { position: relative; z-index: 1; flex: 0 0 auto; margin-top: -.55rem; }
.crivia-carta:first-child { margin-top: 0; }
.crivia-carta__quadro { position: relative; z-index: var(--z); box-sizing: border-box; width: 100%; max-height: 3.6rem; overflow: hidden; border-radius: 20px; border: 1.5px solid transparent; outline: none; cursor: pointer;
  background: linear-gradient(180deg, #021033 0%, #07236B 42%, #1B4CC0 100%) padding-box, linear-gradient(140deg, #2F6BFF, #0A369D 36%, #12286E 64%, #1FCBDD) border-box;
  box-shadow: 0 -6px 18px rgba(0,29,61,.2), 0 16px 34px rgba(0,29,61,.28), inset 0 1px 0 rgba(255,255,255,.1);
  transition: max-height .55s cubic-bezier(.2,.8,.2,1), transform .55s cubic-bezier(.2,.8,.2,1), box-shadow .4s ease; }
.crivia-carta.is-aberta { z-index: 80; }
.crivia-carta.is-aberta .crivia-carta__quadro { max-height: 44rem; box-shadow: 0 30px 70px rgba(0,29,61,.4), inset 0 1px 0 rgba(255,255,255,.12); }
.crivia-carta__corpo { box-sizing: border-box; padding: .8rem .9rem 1rem; display: flex; flex-direction: column; gap: .6rem; color: #fff; }
.crivia-carta__topo { display: flex; align-items: center; gap: .6rem; min-height: 2rem; }
.crivia-carta__icone { width: 2rem; height: 2rem; padding: .45rem; border-radius: 50%; flex: none; color: #BDE8FF; background: rgba(0,0,0,.45); border: 1px solid rgba(255,255,255,.14); }
.crivia-carta__icone svg, .crivia-carta__ph svg { width: 100%; height: 100%; display: block; }
.crivia-carta__cod { font-size: .72rem; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: #BDE8FF; flex: none; }
.crivia-carta__nome-curto { font-size: .84rem; font-weight: 600; letter-spacing: -.01em; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
.crivia-carta__chip { margin-left: auto; flex: none; max-width: 9.5rem; padding: .22rem .6rem; border-radius: 6px; font-size: .58rem; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: #EAF2FF;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background: rgba(255,255,255,.12); border: 1px solid rgba(190,215,255,.35); }
/* local da imagem: grade fina sobre azul-escuro (aparece enquanto não há foto); a foto fica em assets/produtos/<código>.jpg */
.crivia-carta__img { position: relative; aspect-ratio: 2 / 1; overflow: hidden; border-radius: 14px; border: 1px solid rgba(255,255,255,.14); flex: none;
  background: radial-gradient(120% 100% at 80% 0%, rgba(47,107,255,.35), transparent 60%), linear-gradient(160deg, #0B1F5C, #001D3D); }
.crivia-carta__img::before { content: ""; position: absolute; inset: 0; background-image: linear-gradient(rgba(125,170,255,.12) 1px, transparent 1px), linear-gradient(90deg, rgba(125,170,255,.12) 1px, transparent 1px); background-size: 22px 22px; }
.crivia-carta__ph { position: absolute; left: 50%; top: 50%; width: 2.4rem; height: 2.4rem; margin: -1.2rem 0 0 -1.2rem; color: rgba(125,211,252,.55); }
.crivia-carta__img img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.crivia-carta__img::after { content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(180deg, rgba(10,54,157,.04), rgba(0,29,61,.32)), repeating-linear-gradient(transparent 0 2px, rgba(0,0,0,.14) 2px 4px); }
.crivia-carta__titulo { font-size: 1.1rem; font-weight: 650; line-height: 1.2; letter-spacing: -.02em; color: #fff; }
.crivia-carta__txt { font-size: .86rem; font-weight: 450; line-height: 1.5; color: #F2F7FF; }
.crivia-carta__ent { font-size: .78rem; font-weight: 450; line-height: 1.5; color: #DCE8FF; }
.crivia-carta__ent b { display: block; margin-bottom: .1rem; font-size: .6rem; font-weight: 650; letter-spacing: .14em; text-transform: uppercase; color: #BDE8FF; }
.crivia-carta__acao { display: flex; padding-top: .15rem; }
.crivia-carta__vert { display: none; }
.crivia-carta:not(.is-aberta) .crivia-carta__chip { display: none; }
/* botão primário da hero, em versão mini para sobrar espaço ao texto */
.crivia-cta--compacto { font-size: .72rem; }
.crivia-cta--compacto.crivia-cta--primary .crivia-cta__inner { padding: .36rem .6rem .36rem .45rem; font-size: .7rem; gap: .4rem; }
.crivia-cta--compacto .crivia-cta__icon { width: 1.2rem; height: 1.2rem; padding: .28rem; }
.crivia-cta--compacto .crivia-cta__chip { width: 1.1rem; height: 1.1rem; padding: .26rem; margin-left: .05rem; }
.crivia-carta__titulo, .crivia-carta__txt, .crivia-carta__ent, .crivia-carta__acao, .crivia-carta__img { transition: opacity .3s ease; }

@media (min-width: 48rem) {
  .crivia-cat__in { padding: 5.75rem 3rem 1.2rem; gap: .9rem; }
  .crivia-cat__cab { flex-direction: row; align-items: flex-end; justify-content: space-between; gap: 3rem; }
  .crivia-cat__intro { display: flex !important; max-width: 29rem; font-size: .84rem; font-weight: 450; line-height: 1.5; color: #2B4A6B; }
  .crivia-cat__rodape { display: flex; align-items: flex-end; justify-content: space-between; gap: 2rem; margin-top: auto; }
  .crivia-cat__metodo-bloco { display: flex !important; align-items: center; gap: 1rem; min-width: 0; }
  .crivia-cat__metodo-sel { cursor: pointer; border: 0; pointer-events: auto; transition: transform .3s ease, filter .3s ease; flex: none; padding: .5rem 1rem; border-radius: 999px; font-size: .68rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; white-space: nowrap; color: #fff;
    background: linear-gradient(135deg, #0A369D, #2F6BFF); box-shadow: 0 8px 20px rgba(47,107,255,.32), inset 0 1px 0 rgba(255,255,255,.35); }
  .crivia-cat__metodo-sel:hover, .crivia-cat__metodo-sel:focus-visible { transform: translateY(-2px) scale(1.04); filter: brightness(1.12); outline: none; }
  .crivia-cat__metodo { display: flex !important; max-width: 36rem; font-size: 1rem; font-weight: 550; line-height: 1.45; letter-spacing: -.01em; color: #001D3D; }
  .crivia-cat__dica { font-size: .72rem; font-weight: 500; letter-spacing: .04em; color: #2B4A6B; opacity: .8; text-align: right; }
  /* dois grupos em cima e dois embaixo (um em cada canto); a carta aberta cresce sobre a outra linha */
  .crivia-grupos { flex: none; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: start; gap: 1.7rem 2rem; overflow: visible; padding: 0; margin-top: 1.5rem; }
  .crivia-g { --cw: 17rem; --min: 2.6rem; --chc: clamp(11rem, calc((100vh - 28rem) / 2), 17rem); --cho: clamp(26rem, calc(100vh - 17rem), 31rem); min-width: 0; }
  .crivia-g.is-aberto { z-index: 20; }
  .crivia-g__rotulo { min-height: 2.3rem; margin-bottom: .7rem; gap: .75rem; }
  .crivia-g__num { min-width: 2.15rem; height: 2.15rem; font-size: .82rem; }
  .crivia-g__nome { flex: 0 1 auto; font-size: clamp(1.15rem, 1.95vw, 1.6rem); display: block; white-space: nowrap; text-overflow: ellipsis; -webkit-line-clamp: unset; }
  .crivia-g__linha { display: block; flex: 1 1 1.5rem; min-width: 1rem; height: 2px; border-radius: 2px; background: linear-gradient(90deg, rgba(47,107,255,.55), rgba(47,107,255,0)); }
  .crivia-g__qtd { display: inline-block; flex: none; font-size: .68rem; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; color: #2B4A6B; }
  .crivia-g__deck { flex-direction: row; height: var(--chc); align-items: flex-start; }
  .crivia-g:nth-child(n+3) .crivia-g__deck { align-items: flex-end; }
  .crivia-carta { flex: 1 1 0px; min-width: 0; margin: 0 0 0 -.55rem; transition: flex .6s cubic-bezier(.2,.8,.2,1); }
  .crivia-carta:first-child { margin-left: 0; }
  .crivia-g__deck .crivia-carta.is-aberta { flex: 0 0 var(--cw); }
  .crivia-carta__quadro { height: var(--chc); max-height: none; border-radius: 20px; transition: height .55s cubic-bezier(.2,.8,.2,1), box-shadow .4s ease;
    box-shadow: -10px 0 22px rgba(0,29,61,.2), 0 14px 32px rgba(0,29,61,.24), inset 0 1px 0 rgba(255,255,255,.1); }
  .crivia-carta__quadro:hover, .crivia-carta__quadro:focus-visible { box-shadow: -10px 0 22px rgba(0,29,61,.2), 0 18px 40px rgba(47,107,255,.32), inset 0 1px 0 rgba(255,255,255,.1); }
  .crivia-carta.is-aberta .crivia-carta__quadro { height: max(var(--cho), var(--hn, 0px)); max-height: none; box-shadow: 0 30px 70px rgba(0,29,61,.4), inset 0 1px 0 rgba(255,255,255,.12); }
  .crivia-carta__corpo { position: absolute; left: 0; top: 0; width: var(--cw); padding: 1rem; }
  .crivia-carta__nome-curto { display: none; }
  .crivia-carta:not(.is-aberta) .crivia-carta__titulo, .crivia-carta:not(.is-aberta) .crivia-carta__txt, .crivia-carta:not(.is-aberta) .crivia-carta__ent,
  .crivia-carta:not(.is-aberta) .crivia-carta__acao { opacity: 0; }
  .crivia-carta.is-aberta .crivia-carta__titulo, .crivia-carta.is-aberta .crivia-carta__txt, .crivia-carta.is-aberta .crivia-carta__ent, .crivia-carta.is-aberta .crivia-carta__acao { transition-delay: .22s; }
  /* faixa fechada: ícone e código no topo, pedaço da foto e o nome embaixo */
  .crivia-carta__vert { display: -webkit-box; position: absolute; z-index: 2; left: .75rem; right: .4rem; bottom: .55rem; white-space: normal; overflow: hidden; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    font-size: .64rem; font-weight: 600; line-height: 1.25; letter-spacing: 0; color: rgba(240,246,255,.96); transition: opacity .3s ease; }
  .crivia-carta.is-aberta .crivia-carta__vert { opacity: 0; }
  .crivia-carta__corpo { gap: .5rem; }
  .crivia-carta__topo { min-height: 1.8rem; }
}
@media (min-width: 48rem) and (max-width: 69.99rem) {
  .crivia-g { --cw: 15.5rem; --min: 2.2rem; }
  .crivia-g__qtd { display: none; }
  .crivia-g__rotulo { min-height: 2.7rem; }
  .crivia-g__nome { font-size: 1.12rem; white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; text-overflow: clip; }
  .crivia-grupos { gap: .9rem 1.2rem; }
  .crivia-cat__in { padding-left: 2rem; padding-right: 2rem; }
}
@media (min-width: 70rem) and (min-height: 900px) {
  .crivia-g { --cw: 19rem; --min: 3rem; }
  .crivia-carta__titulo { font-size: 1.15rem; }
  .crivia-carta__txt { font-size: .88rem; }
  .crivia-carta__ent { font-size: .8rem; }
  .crivia-carta__vert { font-size: .72rem; }
}
@media (min-width: 48rem) and (max-height: 760px) {
  .crivia-cat__in { padding-top: 5rem; padding-bottom: .8rem; gap: .6rem; }
  .crivia-cat__titulo { font-size: clamp(1.5rem, 2.4vw, 2.1rem); }
  .crivia-g { --chc: clamp(9.5rem, calc((100vh - 23.5rem) / 2), 17rem); }
  .crivia-cat__selo { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .crivia-g, .crivia-carta, .crivia-carta__quadro, .crivia-carta__titulo, .crivia-carta__txt, .crivia-carta__ent, .crivia-carta__acao, .crivia-carta__vert { transition: none; }
}
"""

# Dobra "Motores" (direção B, claro técnico): três momentos da obra, cada um com um painel de números e gráfico em pontos.
# Valores de EXEMPLO ILUSTRATIVO (Mostruário de Dossiês); a marca aparece em cada painel até haver confirmação de que os casos são reais e autorizados.
MOTORES_JS = r"""  // ── CRIVIA ── dobra "Motores": três momentos da obra, com resultado de exemplo e explicação de cada trabalho ──
  var CRIVIA_COR = { azul: "#123A8F", claro: "#A9C1EE", ouro: "#E0A21A", ruim: "#9A6D08", bom: "#15809F", aviso: "#5C78A8" };
  var criviaBRL = (v) => (v < 0 ? "− " : "") + "R$ " + Math.abs(v).toLocaleString("pt-BR");
  var criviaAbrev = (v, sinal) => {
    const a = Math.abs(v), s = sinal ? (v < 0 ? "− " : "+ ") : "";
    return s + (a >= 1e6 ? (a / 1e6).toFixed(2).replace(".", ",") + " mi" : Math.round(a / 1000) + " mil");
  };
  var CRIVIA_MOTORES = [
    { id: "raiox", quando: "Antes de contratar", nome: "Raio-X de Propostas e Orçamentos",
      desc: "Cada item da proposta é comparado com a referência do SINAPI. Você vê onde há sobrepreço, onde o preço está baixo demais e o que ficou de fora da planilha.",
      kpis: [["Proposta", "R$ 3.450.000", "", ""], ["Valor justo", "R$ 2.978.400", "", ""], ["Sobrepreço", "+ R$ 471.600", "ruim", "+15,8%"]],
      ponte: { base: 2900000, topo: 3500000, eixo: "Eixo a partir de R$ 2,9 mi", passos: [
        ["Valor justo", 2978400, "total", "azul", "Referência do SINAPI-ES com BDI de 25% para esta obra."],
        ["Aço", 111000, "delta", "ouro", "Armação CA-50, 18.500 kg: R$ 21,50 por kg na proposta contra R$ 15,50 na referência (+38,7%)."],
        ["Concreto", 76928, "delta", "ouro", "Concreto usinado fck 30 MPa, 680 m³: R$ 720,00 por m³ contra R$ 606,87 (+18,6%)."],
        ["Estrutura", 75000, "delta", "ouro", "Estrutura metálica da cobertura, 55.000 kg: R$ 12,45 por kg contra R$ 11,09 (+12,3%)."],
        ["Piso", 14000, "delta", "aviso", "Piso industrial polido, 2.800 m²: dentro do esperado (+3,5%). Conforme."],
        ["Escavação", -51500, "delta", "bom", "7.900 m³ a R$ 12,02 contra R$ 18,54 (−35,1%). Preço baixo demais pode virar aditivo depois."],
        ["Demais itens", 246172, "delta", "ouro", "Diferença que sobra entre os itens críticos acima e o total do sobrepreço."],
        ["Proposta", 3450000, "total", "azul", "Valor total proposto pela empreiteira."] ] },
      linhas: [
        ["Omissão detectada na planilha", "Subestação aérea de 150 kVA prevista no projeto elétrico e ausente da proposta", "≈ R$ 92.000", "ADITIVO SURPRESA", "ruim"],
        ["Escavação cotada 35,1% abaixo", "Preço baixo no início costuma abrir espaço para pedir aditivo de volume", "− R$ 51.500", "SUBPREÇO", "aviso"]],
      como: { para: "Donos de obra privada e empreiteiras que estão orçando serviços.", envia: "A planilha da proposta em Excel (.xlsx).",
        passos: ["Cada item é pareado com a referência do SINAPI.", "O BDI é aplicado e a Curva ABC mostra onde está 80% do dinheiro da obra.", "Itens caros, baratos demais e omitidos são marcados."],
        recebe: ["Dossiê de 5 páginas", "Gráfico comparativo e tabela da Curva A, em vermelho e verde", "Roteiro de negociação para levar à reunião"] },
      fonte: "Galpão de 2.800 m², Serra/ES. Referência SINAPI-ES com BDI de 25%." },
    { id: "sentinela", quando: "Quando a obra trava", nome: "Diagnóstico Sentinela",
      desc: "O pleito de aditivo é confrontado, dia a dia, com o diário de obra e a chuva medida pelo INMET. Cada período recebe um veredito.",
      kpis: [["Aditivo cobrado", "R$ 485.000", "", ""], ["Devido", "R$ 74.200", "bom", ""], ["Economia", "R$ 410.800", "bom", "84,7%"]],
      ponte: { base: 0, topo: 500000, eixo: "", passos: [
        ["Cobrado", 485000, "total", "azul", "Valor do aditivo cobrado pela empreiteira, com percentuais lineares e sem prova contábil."],
        ["Chuva", -130400, "delta", "bom", "26,9% do pleito. Dias de chuva alegados sem chuva no satélite INMET (16 de 22 dias com 0,0 mm)."],
        ["Mão de obra", -192600, "delta", "bom", "39,7% do pleito. Os diários assinados mostram equipe realocada para o pátio, com produção normal."],
        ["Adm. local", -87800, "delta", "bom", "18,1% do pleito. Cálculo não acompanha o avanço da obra."],
        ["Devido", 74200, "total", "ouro", "15,3% do pleito. Valor recomendado para o acordo técnico."] ] },
      linhas: [
        ["12/08 a 16/08 · pleito alega chuva intensa", "Satélite INMET: 0,0 a 1,8 mm · fora do caminho crítico · diário: 8 operários (cobrou 32)", "R$ 68.400", "IMPROCEDENTE", "ruim"],
        ["24/09 a 04/10 · erro de furação nos chumbadores", "Satélite INMET: 0,0 mm · no caminho crítico · diário: 14 operários em retrabalho", "R$ 74.200", "PROCEDENTE", "bom"]],
      como: { para: "Obras atrasadas, empreiteiras com medição glosada e advogados que defendem empresas contra aditivos e multas.", envia: "Diários de obra escaneados, contrato com cronograma e a notificação do pleito.",
        passos: ["A chuva real do período é buscada na base do INMET.", "Os diários são lidos e confrontados com o cronograma.", "Cada alegação é comparada com o que o campo mostra."],
        recebe: ["Linha do tempo com alegação, chuva medida, caminho crítico e realidade do diário", "Veredito por período: procedente ou improcedente", "Valor a glosar calculado"] },
      fonte: "Ampliação industrial, Linhares/ES. Fontes: diários de obra, INMET e contrato." },
    { id: "medicao", quando: "Durante a execução", nome: "Planejamento e Medição",
      desc: "Todo mês, o que a construtora cobra é comparado com o que foi feito em campo. Você libera o que está pronto, retém o resto e vê o que pode travar nos próximos 30 dias.",
      kpis: [["Cobrado, medição nº 04", "R$ 280.000", "", ""], ["Aprovado", "R$ 235.000", "bom", ""], ["Retido", "− R$ 45.000", "ruim", "Liberado com retenção"]],
      curva: true,
      linhas: [
        ["Divisórias drywall, 3º pavimento", "Cobrado 100% · verificado 70% · falta fechamento de lã de rocha", "− R$ 25.500", "RETENÇÃO", "ruim"],
        ["Laje técnica da cobertura", "Cobrado 100% · verificado 79,5% · aguarda laudo de rompimento", "− R$ 19.500", "HOLD POINT", "aviso"],
        ["Radar de 30 dias · decidir até 13/11", "Compra do quadro geral e do transformador (prazo de fábrica de 45 dias)", "", "CRÍTICO", "ruim"]],
      como: { para: "Quem já contratou a obra e não quer voltar à incerteza.", envia: "A planilha de medição da construtora, numa data de corte fixa (por exemplo, dia 25).",
        passos: ["Inspeção visual focada, com fotos, no que foi cobrado.", "O que foi visto é cruzado com a planilha de medição.", "Cada pagamento recebe uma condição de liberação."],
        recebe: ["Boletim de 4 páginas", "Certificado de liberação e glosa, com a Curva S", "Radar dos suprimentos críticos dos próximos 30 dias e os documentos exigidos para pagar"] },
      fonte: "Edifício comercial e clínica, Vitória/ES." }
  ];
  var CRIVIA_TONS = {
    azul: { f: ["#2F5BC4", "#0B2C80"], t: "#6F94E0", s: "#071F5C" },
    ouro: { f: ["#F6C65A", "#C98F10"], t: "#FCE6A6", s: "#9A6D08" },
    bom: { f: ["#47BEDB", "#15809F"], t: "#9BE0F0", s: "#0D5D77" },
    aviso: { f: ["#93AACE", "#5C78A8"], t: "#C9D7EC", s: "#415B84" }
  };
  var CriviaPonte = ({ g }) => {
    const n = g.passos.length;
    const [sel, setSel] = (0, import_react35.useState)(n - 1);
    const [ligado, setLigado] = (0, import_react35.useState)(0);
    const [rodada, setRodada] = (0, import_react35.useState)(0);
    (0, import_react35.useEffect)(() => {
      setLigado(0);
      let k = 0;
      const id = setInterval(() => { k += 1; setLigado(k); setSel(Math.min(k, n) - 1); if (k >= n) clearInterval(id); }, 430);
      return () => clearInterval(id);
    }, [rodada, n]);
    const W = 600, H = 214, L = 6, R = 14, T = 34, B = 30;
    const bw = (W - L - R) / n, pw = bw * 0.58, dx = Math.min(11, pw * 0.2), dy = dx * 0.6;
    const y = (v) => T + (H - T - B) * (1 - (v - g.base) / (g.topo - g.base));
    let acc = 0;
    const barras = g.passos.map((p, i) => {
      let v0, v1;
      if (p[2] === "total") { v0 = g.base; v1 = p[1]; acc = p[1]; } else { v0 = acc; v1 = acc + p[1]; acc = v1; }
      return { p, i, v0, v1, topo: Math.max(v0, v1), fim: acc };
    });
    const defs = Object.keys(CRIVIA_TONS).map((k) => {
      const c = CRIVIA_TONS[k];
      return (0, import_jsx_runtime26.jsxs)("g", { children: [
        (0, import_jsx_runtime26.jsxs)("linearGradient", { id: "cmf-" + k, x1: 0, y1: 0, x2: 0, y2: 1, children: [(0, import_jsx_runtime26.jsx)("stop", { offset: "0", stopColor: c.f[0] }), (0, import_jsx_runtime26.jsx)("stop", { offset: "1", stopColor: c.f[1] })] }),
        (0, import_jsx_runtime26.jsxs)("linearGradient", { id: "cms-" + k, x1: 0, y1: 0, x2: 0, y2: 1, children: [(0, import_jsx_runtime26.jsx)("stop", { offset: "0", stopColor: c.s }), (0, import_jsx_runtime26.jsx)("stop", { offset: "1", stopColor: c.s, stopOpacity: 0.78 })] })
      ] }, k);
    });
    const grade = [0.25, 0.5, 0.75, 1].map((q, i) => (0, import_jsx_runtime26.jsx)("line", { x1: L, x2: W - R, y1: T + (H - T - B) * q - (H - T - B) * 0, y2: T + (H - T - B) * q, stroke: "#7C93C4", strokeOpacity: q === 1 ? 0.55 : 0.18, strokeDasharray: q === 1 ? "none" : "2 5" }, "gr" + i));
    const el = [];
    barras.forEach((b, i) => {
      const x = L + i * bw + (bw - pw) / 2, ytop = y(b.topo), ybase = y(Math.min(b.v0, b.v1)), h = Math.max(4, ybase - ytop);
      const ton = CRIVIA_TONS[b.p[3]] ? b.p[3] : "azul", c = CRIVIA_TONS[ton], on = i < ligado, ativo = i === sel;
      if (i < n - 1) el.push((0, import_jsx_runtime26.jsx)("line", { x1: x + pw + dx, x2: x + bw, y1: y(b.fim) - dy, y2: y(b.fim) - dy, stroke: "#7C93C4", strokeWidth: 1, strokeDasharray: "3 3", style: { opacity: ligado > i + 1 ? 1 : 0, transition: "opacity .4s ease" } }, "c" + i));
      el.push((0, import_jsx_runtime26.jsxs)("g", { className: "crivia-mot__bar3d" + (on ? " is-on" : "") + (ativo ? " is-ativa" : ""), children: [
        (0, import_jsx_runtime26.jsx)("ellipse", { cx: x + (pw + dx) / 2, cy: ybase + 3, rx: pw * 0.72, ry: 4, fill: "#001D3D", fillOpacity: 0.16 }),
        (0, import_jsx_runtime26.jsx)("polygon", { points: (x + pw) + "," + ytop + " " + (x + pw + dx) + "," + (ytop - dy) + " " + (x + pw + dx) + "," + (ytop - dy + h) + " " + (x + pw) + "," + (ytop + h), fill: "url(#cms-" + ton + ")" }),
        (0, import_jsx_runtime26.jsx)("rect", { x, y: ytop, width: pw, height: h, fill: "url(#cmf-" + ton + ")" }),
        (0, import_jsx_runtime26.jsx)("polygon", { points: x + "," + ytop + " " + (x + dx) + "," + (ytop - dy) + " " + (x + pw + dx) + "," + (ytop - dy) + " " + (x + pw) + "," + ytop, fill: c.t }),
        (0, import_jsx_runtime26.jsx)("rect", { x, y: ytop, width: pw, height: Math.min(h, 3), fill: "#fff", fillOpacity: 0.22 }),
        (0, import_jsx_runtime26.jsx)("text", { x: x + (pw + dx) / 2, y: ytop - dy - 7, textAnchor: "middle", className: "crivia-mot__vlr", children: criviaAbrev(b.p[1], b.p[2] === "delta") })
      ] }, "b" + i));
      el.push((0, import_jsx_runtime26.jsx)("text", { x: x + (pw + dx) / 2, y: H - 10, textAnchor: "middle", className: "crivia-mot__rot-x" + (ativo ? " is-ativo" : ""), children: b.p[0] }, "t" + i));
      el.push((0, import_jsx_runtime26.jsx)("rect", { x: L + i * bw, y: 0, width: bw, height: H, fill: "transparent", tabIndex: 0, role: "button", "aria-label": b.p[0] + ": " + criviaBRL(b.p[1]), style: { cursor: "pointer" },
        onMouseEnter: () => setSel(i), onFocus: () => setSel(i), onClick: () => setSel(i) }, "h" + i));
    });
    const s = g.passos[sel] || g.passos[n - 1];
    return criviaH("div", { className: "crivia-mot__graf" },
      criviaH("svg", { viewBox: "0 0 " + W + " " + H, className: "crivia-mot__svg", role: "group", "aria-label": "Gráfico em cascata, de exemplo", children: [(0, import_jsx_runtime26.jsx)("defs", { children: defs }, "defs"), ...grade, ...el] }),
      criviaH("div", { className: "crivia-mot__leitura font-geist" },
        criviaH("b", { className: "t-" + s[3] }, s[0] + " · " + (s[2] === "delta" ? (s[1] < 0 ? "− " : "+ ") : "") + "R$ " + Math.abs(s[1]).toLocaleString("pt-BR")),
        criviaH("span", {}, s[4])),
      criviaH("div", { className: "crivia-mot__rodape-graf font-geist" },
        criviaH("span", {}, g.eixo || "Passe o cursor sobre as barras para ler cada etapa."),
        criviaH("button", { type: "button", className: "crivia-mot__replay", onClick: () => setRodada((r) => r + 1) }, "↻ Reproduzir")));
  };
  var CriviaCurvaS = () => {
    const [t, setT] = (0, import_react35.useState)(60);
    const W = 600, H = 190, L = 10, R = 10, T = 12, B = 28, N = 64;
    const X = (u) => L + (W - L - R) * u, Y = (v) => T + (H - T - B) * (1 - v);
    const sig = (u, c, k) => { const f = (z) => 1 / (1 + Math.exp(-k * (z - c))); return (f(u) - f(0)) / (f(1) - f(0)); };
    const cob = (u) => sig(u, 0.45, 9), ver = (u) => sig(u, 0.57, 8.5);
    const ponto = (fn) => { let d = ""; for (let i = 0; i <= N; i++) { const u = i / N; d += (i ? "L" : "M") + X(u).toFixed(1) + " " + Y(fn(u)).toFixed(1) + " "; } return d; };
    let gap = ponto(cob);
    for (let i = N; i >= 0; i--) { const u = i / N; gap += "L" + X(u).toFixed(1) + " " + Y(ver(u)).toFixed(1) + " "; }
    const u = t / 100, xc = X(u), yc = Y(cob(u)), yv = Y(ver(u));
    return criviaH("div", { className: "crivia-mot__graf" },
      criviaH("svg", { viewBox: "0 0 " + W + " " + H, className: "crivia-mot__svg", role: "img", "aria-label": "Curva S de exemplo: o avanço verificado em campo fica atrás do avanço cobrado", children: [
        (0, import_jsx_runtime26.jsx)("line", { x1: L, x2: W - R, y1: H - B, y2: H - B, stroke: "#7C93C4", strokeOpacity: 0.5 }, "eixo"),
        (0, import_jsx_runtime26.jsx)("path", { d: gap + "Z", fill: CRIVIA_COR.ruim, fillOpacity: 0.12 }, "gap"),
        (0, import_jsx_runtime26.jsx)("path", { d: ponto(cob), fill: "none", stroke: CRIVIA_COR.azul, strokeWidth: 3, strokeLinecap: "round", pathLength: 1, className: "crivia-mot__traco" }, "cob"),
        (0, import_jsx_runtime26.jsx)("path", { d: ponto(ver), fill: "none", stroke: CRIVIA_COR.ouro, strokeWidth: 3, strokeLinecap: "round", pathLength: 1, className: "crivia-mot__traco crivia-mot__traco--2" }, "ver"),
        (0, import_jsx_runtime26.jsx)("line", { x1: xc, x2: xc, y1: T, y2: H - B, stroke: "#7C93C4", strokeDasharray: "3 3" }, "mk"),
        (0, import_jsx_runtime26.jsx)("line", { x1: xc, x2: xc, y1: yc, y2: yv, stroke: CRIVIA_COR.ruim, strokeWidth: 3, strokeLinecap: "round" }, "df"),
        (0, import_jsx_runtime26.jsx)("circle", { cx: xc, cy: yc, r: 6, fill: CRIVIA_COR.azul, stroke: "#fff", strokeWidth: 2 }, "p1"),
        (0, import_jsx_runtime26.jsx)("circle", { cx: xc, cy: yv, r: 6.5, fill: CRIVIA_COR.ouro, stroke: "#fff", strokeWidth: 2 }, "p2"),
        (0, import_jsx_runtime26.jsx)("text", { x: Math.min(xc + 12, W - 70), y: (yc + yv) / 2 + 4, className: "crivia-mot__vlr", fill: CRIVIA_COR.ruim, children: "defasagem" }, "tx"),
        (0, import_jsx_runtime26.jsx)("text", { x: L, y: H - 10, className: "crivia-mot__rot-x", children: "início da obra" }, "x0"),
        (0, import_jsx_runtime26.jsx)("text", { x: W - R, y: H - 10, textAnchor: "end", className: "crivia-mot__rot-x", children: "entrega" }, "x1")
      ] }),
      criviaH("div", { className: "crivia-mot__curva-ctl font-geist" },
        criviaH("span", { style: { color: CRIVIA_COR.azul } }, "● cobrado pela construtora"),
        criviaH("input", { type: "range", min: 0, max: 100, value: t, "aria-label": "Percorrer o cronograma", onChange: (e) => setT(+e.target.value), className: "crivia-mot__range" }),
        criviaH("span", { style: { color: CRIVIA_COR.aviso } }, "● verificado em campo")),
      criviaH("p", { className: "crivia-mot__eixo font-geist" }, "Curva S de exemplo, sem valores. Arraste para ver a defasagem em cada momento da obra."));
  };
  var CriviaComo = ({ c }) => criviaH("div", { className: "crivia-mot__como" },
    criviaH("div", { className: "crivia-mot__bloco" }, criviaH("span", { className: "font-geist crivia-mot__rot" }, "Para quem"), criviaH("p", {}, c.para)),
    criviaH("div", { className: "crivia-mot__bloco" }, criviaH("span", { className: "font-geist crivia-mot__rot" }, "Você envia"), criviaH("p", {}, c.envia)),
    criviaH("div", { className: "crivia-mot__bloco crivia-mot__bloco--larga" }, criviaH("span", { className: "font-geist crivia-mot__rot" }, "Como trabalhamos"),
      criviaH("ol", {}, c.passos.map((p) => criviaH("li", { key: p }, p)))),
    criviaH("div", { className: "crivia-mot__bloco crivia-mot__bloco--larga crivia-mot__bloco--recebe" }, criviaH("span", { className: "font-geist crivia-mot__rot" }, "Você recebe"),
      criviaH("ul", {}, c.recebe.map((p) => criviaH("li", { key: p }, p)))));
  var CriviaMotores = () => {
    const [i, setI] = (0, import_react35.useState)(0);
    const [vista, setVista] = (0, import_react35.useState)(0);
    const esq = (0, import_react35.useRef)(null), cx = (0, import_react35.useRef)(null), ex = (0, import_react35.useRef)(null);
    const m = CRIVIA_MOTORES[i];
    (0, import_react35.useEffect)(() => {
      let raf = 0;
      const ss = (a, b, p) => { const k = Math.min(1, Math.max(0, (p - a) / (b - a))); return k * k * (3 - 2 * k); };
      const tick = () => {
        raf = requestAnimationFrame(tick);
        const p = getScrollProgress();
        const ent = ss(0.14, 0.19, p), sai = ss(0.30, 0.335, p);
        if (cx.current) {
          const esc = (0.74 + 0.26 * ent) * (1 + 0.12 * sai), bl = (1 - ent) * 16 + sai * 8;
          cx.current.style.transform = "scale(" + esc.toFixed(4) + ")";
          cx.current.style.filter = bl > 0.3 ? "blur(" + bl.toFixed(1) + "px)" : "none";
        }
        if (esq.current) esq.current.style.transform = "translateX(" + ((1 - ent) * -56 - sai * 30).toFixed(1) + "px)";
        if (ex.current) { ex.current.style.opacity = (Math.sin(Math.PI * ent) * 0.85).toFixed(3); ex.current.style.transform = "translate(-50%, -50%) scale(" + (0.5 + ent * 1.5).toFixed(3) + ")"; }
      };
      raf = requestAnimationFrame(tick);
      return () => cancelAnimationFrame(raf);
    }, []);
    const escolher = (k) => { setI(k); setVista(0); };
    const mover = (e) => { const r = e.currentTarget.getBoundingClientRect(); e.currentTarget.style.setProperty("--mx", (e.clientX - r.left) + "px"); e.currentTarget.style.setProperty("--my", (e.clientY - r.top) + "px"); };
    return criviaH("div", { className: "crivia-mot" },
      criviaH("div", { className: "crivia-mot__in" },
        criviaH("div", { className: "crivia-mot__esq", ref: esq },
          criviaH("span", { className: "font-geist crivia-cat__selo" }, criviaH("span", { className: "crivia-cat__selo-ponto", "aria-hidden": true }), "Onde a CRIVIA entra"),
          criviaH("h2", { className: "crivia-mot__titulo" }, "Três momentos da obra. Três decisões com número na mesa."),
          criviaH("p", { className: "font-geist crivia-mot__sub" }, "Cada trabalho termina em um documento que você lê na reunião e usa para negociar, destravar ou pagar."),
          criviaH("div", { className: "crivia-mot__abas", role: "tablist", "aria-label": "Momentos da obra" }, CRIVIA_MOTORES.map((x, k) =>
            criviaH("button", { key: x.id, type: "button", role: "tab", "aria-selected": k === i, className: "crivia-mot__aba" + (k === i ? " is-on" : ""), onClick: () => escolher(k) },
              criviaH("span", { className: "font-geist crivia-mot__quando" }, x.quando),
              criviaH("strong", {}, x.nome),
              criviaH("span", { className: "font-geist crivia-mot__desc" }, x.desc)))),
          criviaH("div", { className: "crivia-mot__acao" }, criviaH(CriviaCtaPrimary, { onClick: () => CRIVIA_ABRIR_CENARIO("produtos"), children: "Apresentar meu cenário" }))),
        criviaH("div", { className: "crivia-mot__dir" },
          criviaH("span", { className: "crivia-mot__explosao", ref: ex, "aria-hidden": true }),
          criviaH("div", { className: "crivia-mot__caixa", ref: cx },
            criviaH("div", { className: "crivia-mot__painel", role: "tabpanel", key: m.id, onPointerMove: mover },
              criviaH("div", { className: "crivia-mot__pcab" },
                criviaH("div", {}, criviaH("span", { className: "font-geist crivia-mot__quando" }, m.quando), criviaH("h3", {}, m.nome)),
                criviaH("div", { className: "crivia-mot__vistas font-geist", role: "tablist", "aria-label": "Tipo de conteúdo" }, ["Resultado de exemplo", "Como funciona"].map((r, k) =>
                  criviaH("button", { key: r, type: "button", role: "tab", "aria-selected": k === vista, className: k === vista ? "is-on" : "", onClick: () => setVista(k) }, r)))),
              vista === 1 ? criviaH(CriviaComo, { c: m.como }) : criviaH(import_react35.Fragment, {},
                criviaH("div", { className: "crivia-mot__kpis" }, m.kpis.map((k) =>
                  criviaH("div", { key: k[0], className: "crivia-mot__kpi" },
                    criviaH("span", { className: "font-geist" }, k[0]),
                    criviaH("b", { className: k[2] ? "t-" + k[2] : "" }, k[1]),
                    k[3] ? criviaH("em", { className: "font-geist " + (k[2] ? "t-" + k[2] : "") }, k[3]) : null))),
                m.curva ? criviaH(CriviaCurvaS, {}) : criviaH(CriviaPonte, { g: m.ponte }),
                criviaH("ul", { className: "crivia-mot__linhas" }, m.linhas.map((l) =>
                  criviaH("li", { key: l[0] },
                    criviaH("div", {}, criviaH("strong", {}, l[0]), criviaH("small", { className: "font-geist" }, l[1])),
                    criviaH("div", { className: "crivia-mot__val font-geist" }, l[2] ? criviaH("span", {}, l[2]) : null, criviaH("i", { className: "t-" + l[4] }, l[3]))))),
                criviaH("p", { className: "font-geist crivia-mot__fonte" }, criviaH("span", { className: "crivia-mot__ilus" }, "Exemplo ilustrativo"), " ", m.fonte)))))));
  };
  var MotoresOverlay = () => criviaH("div", { className: "pointer-events-none absolute inset-0 select-none font-display text-overlay-ink" }, criviaH(CriviaMotores, {}));
"""

CSS_MOTORES = r"""
/* ════ CRIVIA ════ dobra dos motores (direção B, claro técnico): abas à esquerda, painel de números à direita ════ */
@property --mot-ang { syntax: "<angle>"; initial-value: 0deg; inherits: false; }
.crivia-mot { position: absolute; inset: 0; overflow: hidden; background: linear-gradient(180deg, rgba(247,251,254,.74) 0%, rgba(236,245,252,.88) 100%); }
.crivia-mot__in { box-sizing: border-box; height: 100%; max-width: 82rem; margin: 0 auto; padding: 4.5rem 1.25rem 1rem; display: flex; flex-direction: column; gap: 1rem; pointer-events: auto; overflow-y: auto; scrollbar-width: none; }
.crivia-mot__in::-webkit-scrollbar { display: none; }
.crivia-mot__esq { display: flex; flex-direction: column; align-items: flex-start; gap: .75rem; min-width: 0; will-change: transform; }
.crivia-mot__titulo { font-size: clamp(1.55rem, 2.7vw, 2.55rem); font-weight: 650; line-height: 1.07; letter-spacing: -.035em; color: #001D3D; text-wrap: balance; }
.crivia-mot__sub { font-size: .86rem; font-weight: 450; line-height: 1.5; color: #2B4A6B; max-width: 34rem; }
.crivia-mot__abas { display: flex; flex-direction: column; gap: .5rem; width: 100%; margin-top: .25rem; }
.crivia-mot__aba { display: flex; flex-direction: column; align-items: flex-start; gap: .12rem; width: 100%; text-align: left; cursor: pointer; padding: .7rem .9rem; border-radius: 1rem; color: #001D3D;
  background: rgba(255,255,255,.72); border: 1px solid rgba(10,54,157,.16); -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px); transition: transform .25s ease, background .25s ease, box-shadow .25s ease, color .25s ease; }
.crivia-mot__aba strong { font-size: .98rem; font-weight: 650; letter-spacing: -.02em; }
.crivia-mot__aba:hover, .crivia-mot__aba:focus-visible { transform: translateX(3px); outline: none; box-shadow: 0 10px 26px rgba(10,54,157,.18); }
.crivia-mot__aba.is-on { color: #fff; background: linear-gradient(135deg, #0A369D 0%, #1B4CC0 100%); border-color: transparent; box-shadow: 0 14px 30px rgba(10,54,157,.32), inset 0 1px 0 rgba(255,255,255,.25); }
.crivia-mot__quando { font-size: .62rem; font-weight: 650; letter-spacing: .14em; text-transform: uppercase; color: #0A5FA8; }
.crivia-mot__aba.is-on .crivia-mot__quando { color: #BDE8FF; }
.crivia-mot__desc { display: none; font-size: .78rem; font-weight: 450; line-height: 1.4; color: #2B4A6B; }
.crivia-mot__aba.is-on .crivia-mot__desc { display: block; color: #E4EEFF; }
.crivia-mot__acao { padding-top: .35rem; }

/* lado direito: o "estouro" de chegada, a caixa que cresce e o painel com borda giratória */
.crivia-mot__dir { position: relative; min-width: 0; }
.crivia-mot__explosao { position: absolute; left: 50%; top: 50%; width: 46rem; height: 46rem; max-width: 150%; border-radius: 50%; pointer-events: none; opacity: 0; z-index: 0;
  background: radial-gradient(closest-side, rgba(56,189,248,.5), rgba(27,76,192,.22) 45%, rgba(245,184,46,.16) 62%, transparent 74%); will-change: transform, opacity; }
.crivia-mot__caixa { position: relative; z-index: 1; will-change: transform, filter; }
.crivia-mot__painel { --mx: 70%; --my: 0%; position: relative; box-sizing: border-box; min-width: 0; display: flex; flex-direction: column; gap: .85rem; padding: 1rem; border-radius: 1.25rem; color: #0B1F4A; isolation: isolate;
  border: 1.5px solid transparent;
  background:
    linear-gradient(165deg, rgba(232,243,255,.95) 0%, rgba(212,230,255,.86) 52%, rgba(255,246,222,.84) 100%) padding-box,
    conic-gradient(from var(--mot-ang), rgba(27,76,192,0) 0%, #1B4CC0 9%, #38BDF8 19%, #F5B82E 29%, #1B4CC0 41%, rgba(27,76,192,0) 54%, rgba(27,76,192,0) 100%) border-box;
  box-shadow: 0 30px 80px -20px rgba(10,54,157,.42), 0 0 0 1px rgba(255,255,255,.7) inset, 0 0 46px rgba(56,189,248,.16);
  animation: crivia-mot-in .4s ease both, crivia-mot-giro 10s linear infinite; }
.crivia-mot__painel::before { content: ""; position: absolute; inset: 0; z-index: -1; border-radius: inherit; pointer-events: none;
  background: radial-gradient(26rem circle at var(--mx) var(--my), rgba(56,189,248,.28), rgba(56,189,248,0) 62%); }
.crivia-mot__painel::after { content: ""; position: absolute; left: 1.25rem; right: 1.25rem; top: 0; height: 2px; z-index: 1; border-radius: 2px; pointer-events: none;
  background: linear-gradient(90deg, rgba(245,184,46,0), #F5B82E 30%, #38BDF8 70%, rgba(56,189,248,0)); opacity: .85; }
@keyframes crivia-mot-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@keyframes crivia-mot-giro { to { --mot-ang: 360deg; } }
.crivia-mot__pcab { display: flex; justify-content: space-between; align-items: flex-start; gap: .75rem; flex-wrap: wrap; }
.crivia-mot__pcab h3 { margin: .1rem 0 0; font-size: 1.1rem; font-weight: 650; letter-spacing: -.02em; color: #001D3D; }
.crivia-mot__vistas { display: inline-flex; padding: .2rem; gap: .15rem; border-radius: 999px; background: rgba(10,54,157,.09); }
.crivia-mot__vistas button { cursor: pointer; border: 0; background: transparent; padding: .3rem .75rem; border-radius: 999px; font-size: .64rem; font-weight: 650; letter-spacing: .04em; color: #2B4A6B; transition: background .2s ease, color .2s ease; }
.crivia-mot__vistas button.is-on { background: #fff; color: #0A369D; box-shadow: 0 2px 8px rgba(10,54,157,.18); }
.crivia-mot__vistas button:focus-visible { outline: 2px solid #1B4CC0; outline-offset: 1px; }
.crivia-mot__ilus { font-size: .56rem; font-weight: 650; letter-spacing: .1em; text-transform: uppercase; padding: .16rem .45rem; border-radius: 6px; border: 1px dashed rgba(10,54,157,.4); color: #2B4A6B; white-space: nowrap; }
.crivia-mot__kpis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .6rem; }
.crivia-mot__kpi { display: flex; flex-direction: column; gap: .12rem; padding: .55rem .7rem; border-radius: .8rem; background: rgba(255,255,255,.7); border: 1px solid rgba(10,54,157,.14); min-width: 0; }
.crivia-mot__kpi span { font-size: .56rem; font-weight: 600; letter-spacing: .07em; text-transform: uppercase; color: #46608E; }
.crivia-mot__kpi b { font-size: clamp(.95rem, 1.5vw, 1.4rem); font-weight: 700; letter-spacing: -.025em; font-variant-numeric: tabular-nums; white-space: nowrap; color: #001D3D; }
.crivia-mot__kpi em { font-style: normal; font-size: .64rem; font-weight: 650; }
.t-ruim, .t-ouro { color: #8A5D00 !important; } .t-bom { color: #0F6E8C !important; } .t-aviso { color: #46608E !important; } .t-azul { color: #123A8F !important; }
/* gráficos interativos */
.crivia-mot__graf { display: flex; flex-direction: column; gap: .35rem; }
.crivia-mot__svg { display: block; width: 100%; height: auto; overflow: visible; }
.crivia-mot__vlr { font: 650 11px "Geist", system-ui, sans-serif; fill: #001D3D; font-variant-numeric: tabular-nums; }
.crivia-mot__rot-x { font: 500 10.5px "Geist", system-ui, sans-serif; fill: #46608E; }
.crivia-mot__bar3d { transform-box: fill-box; transform-origin: 50% 100%; transform: scaleY(0); opacity: 0; transition: transform .7s cubic-bezier(.2,.9,.25,1), opacity .35s ease, filter .25s ease; }
.crivia-mot__bar3d.is-on { transform: none; opacity: 1; }
.crivia-mot__bar3d.is-ativa { filter: drop-shadow(0 6px 10px rgba(10,54,157,.35)) brightness(1.07); }
.crivia-mot__rot-x.is-ativo { fill: #0A369D; font-weight: 700; }
.crivia-mot__rodape-graf { display: flex; justify-content: space-between; align-items: center; gap: .6rem; font-size: .58rem; font-weight: 450; color: #46608E; }
.crivia-mot__replay { cursor: pointer; border: 1px solid rgba(10,54,157,.22); background: rgba(255,255,255,.7); border-radius: 999px; padding: .18rem .6rem; font-size: .6rem; font-weight: 650; color: #0A369D; }
.crivia-mot__replay:hover { background: #fff; }
.crivia-mot__traco { stroke-dasharray: 1; stroke-dashoffset: 1; animation: crivia-mot-traco 1.4s cubic-bezier(.3,.7,.2,1) .15s forwards; }
.crivia-mot__traco--2 { animation-delay: .45s; }
@keyframes crivia-mot-traco { to { stroke-dashoffset: 0; } }
.crivia-mot__leitura { display: flex; flex-direction: column; gap: .1rem; min-height: 2.9rem; padding: .5rem .7rem; border-radius: .8rem; background: rgba(255,255,255,.72); border: 1px solid rgba(10,54,157,.14); font-size: .72rem; line-height: 1.4; color: #2B4A6B; }
.crivia-mot__leitura b { font-size: .86rem; font-weight: 700; letter-spacing: -.01em; color: #123A8F; font-variant-numeric: tabular-nums; }
.crivia-mot__eixo { margin: 0; font-size: .58rem; font-weight: 450; color: #46608E; }
.crivia-mot__curva-ctl { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: .7rem; font-size: .66rem; font-weight: 600; }
.crivia-mot__range { width: 100%; height: 1.1rem; accent-color: #1B4CC0; cursor: ew-resize; }
.crivia-mot__linhas { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; }
.crivia-mot__linhas li { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .75rem; align-items: center; padding: .5rem 0; border-top: 1px solid rgba(10,54,157,.14); }
.crivia-mot__linhas strong { display: block; font-size: .8rem; font-weight: 650; letter-spacing: -.01em; color: #001D3D; }
.crivia-mot__linhas small { display: block; font-size: .64rem; font-weight: 450; line-height: 1.35; color: #46608E; }
.crivia-mot__val { display: flex; flex-direction: column; align-items: flex-end; gap: .15rem; text-align: right; font-size: .78rem; font-weight: 650; font-variant-numeric: tabular-nums; color: #001D3D; }
.crivia-mot__val i { font-style: normal; font-size: .56rem; font-weight: 700; letter-spacing: .06em; padding: .12rem .45rem; border-radius: 999px; background: rgba(10,54,157,.08); }
.crivia-mot__val i.t-ruim { background: rgba(224,162,26,.2); } .crivia-mot__val i.t-bom { background: rgba(21,128,159,.14); } .crivia-mot__val i.t-aviso { background: rgba(92,120,168,.16); }
.crivia-mot__fonte { margin: 0; display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; font-size: .6rem; font-weight: 450; color: #46608E; }
/* "Como funciona" */
.crivia-mot__como { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .6rem; }
.crivia-mot__bloco { display: flex; flex-direction: column; gap: .3rem; padding: .7rem .85rem; border-radius: .9rem; background: rgba(255,255,255,.72); border: 1px solid rgba(10,54,157,.14); font-size: .8rem; line-height: 1.45; color: #0B1F4A; }
.crivia-mot__bloco p { margin: 0; }
.crivia-mot__bloco--larga { grid-column: 1 / -1; }
.crivia-mot__rot { font-size: .58rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #0A5FA8; }
.crivia-mot__bloco ol, .crivia-mot__bloco ul { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: .3rem; counter-reset: p; }
.crivia-mot__bloco li { position: relative; padding-left: 1.5rem; }
.crivia-mot__bloco ol li { counter-increment: p; }
.crivia-mot__bloco ol li::before { content: counter(p); position: absolute; left: 0; top: .05rem; width: 1.05rem; height: 1.05rem; border-radius: 50%; display: grid; place-items: center; font-size: .58rem; font-weight: 700; color: #fff; background: linear-gradient(135deg, #0A369D, #2F6BFF); }
.crivia-mot__bloco ul li::before { content: ""; position: absolute; left: .25rem; top: .5rem; width: 6px; height: 6px; border-radius: 50%; background: #F5B82E; box-shadow: 0 0 0 3px rgba(245,184,46,.28); }
@media (min-width: 56rem) {
  .crivia-mot__in { display: grid; grid-template-columns: minmax(0, 27rem) minmax(0, 1fr); column-gap: 2.75rem; align-items: center; padding: 6rem 3rem 2rem; overflow: visible; }
  .crivia-mot__sub { font-size: .92rem; }
  .crivia-mot__painel { padding: 1.25rem 1.4rem; gap: 1rem; }
  .crivia-mot__pcab h3 { font-size: 1.3rem; }
  .crivia-mot__linhas strong { font-size: .88rem; }
  .crivia-mot__linhas small { font-size: .7rem; }
  .crivia-mot__val { font-size: .86rem; }
  .crivia-mot__bloco { font-size: .88rem; }
}
@media (min-width: 56rem) and (max-height: 780px) {
  .crivia-mot__in { padding-top: 5rem; padding-bottom: 1rem; }
  .crivia-mot__painel { gap: .55rem; padding: .9rem 1.1rem; }
  .crivia-mot__linhas li { padding: .3rem 0; }
  .crivia-mot__sub { display: none; }
  .crivia-mot__leitura { min-height: 2.5rem; }
  .crivia-mot__kpi { padding: .4rem .6rem; }
}
@media (prefers-reduced-motion: reduce) { .crivia-mot__painel { animation: none; } .crivia-mot__bar3d { transition: none; } .crivia-mot__traco { animation: none; stroke-dashoffset: 0; } .crivia-mot__aba { transition: none; } }
"""

PATCHES_TEXTO = [
    ("txt:cabecalho-esq",'var LEFT_NAV = ["Projects", "Studio", "Process"];',
     'var LEFT_NAV = ["Início", "Produtos", "Método", "Sobre"];', 1),
    ("txt:cabecalho-dir", 'var RIGHT_NAV = ["Journal", "About"];',
     'var RIGHT_NAV = ["Decisão com IA"];', 1),
    ("txt:marca", 'var BRAND = "Auralis";', 'var BRAND = "CRIVIA";', 1),
    ("txt:cta", 'var CTA = "Say Hello";', MAILTO_JS, 1),
    # hero
    ("txt:hero-tags", 'var TAGS = ["Lorem ipsum", "Dolor sit amet", "Consectetur", "Adipiscing elit"];',
     'var TAGS = ["Realidade", "Causa", "Risco", "Decisão"];', 1),
    ("txt:hero-texto",
     'children: "Particle forms in a wireframe cylinder, soft light leaks, and film grain on cool slate."',
     'children: "Engenharia independente para decisões críticas: vamos à realidade e encontramos a causa por trás do sintoma."', 1),
    # hero: tipografia do Nexus (títulos em Plus Jakarta Sans; textos e etiquetas em Geist); apoio em caixa normal
    ("txt:hero-texto-fonte",
     'delayIn: 1300,\n              className: "text-[0.8125rem] font-normal uppercase leading-[1.2] md:text-[1rem]"',
     'delayIn: 2000,\n              className: "font-geist crivia-hero-copy"', 1),
    # hero: a sequência da chegada (frase 1, frase 2, apoio, etiquetas, botões)
    # hero: chegada dos textos linha por linha, subindo (só nesta cena)
    ("txt:hero-chegada", '    const layer = variant === "heading" ? {',
     '    const layer = act === "hero" ? {\n'
     '      lineOut: { y: "70%", opacity: 0, filter: "blur(18px)" },\n'
     '      lineIn: { y: "0%", opacity: 1, filter: "blur(0px)" },\n'
     '      lineStagger: 260,\n'
     '      lineConfig: { mass: 1, tension: 34, friction: 21 }\n'
     '    } : variant === "heading" ? {', 1),
    # hero: os dois botões (estilo Lumina, nas cores da CRIVIA) ficam em pílulas que quebram linha no celular
    ("txt:hero-botoes-caixa",
     'className: "pointer-events-auto flex shrink-0 items-center gap-[0.5rem] md:gap-[0.75rem]"',
     'className: "pointer-events-auto flex shrink-0 flex-wrap items-center gap-[0.75rem] md:flex-nowrap md:gap-[1rem]"', 1),
    # cena da indústria
    ("txt:ind-titulo", 'children: "Lorem ipsum dolor sit"',
     'children: "O problema quase nunca está onde aparece."', 1),
    ("txt:ind-texto",
     'children: "Lorem ipsum dolor sit amet — consectetur adipiscing elit, sed do eiusmod tempor."',
     'children: "Atraso, medição que não sai, informações contraditórias. Controle mostra o sintoma. Compreensão revela a causa. Boa decisão precisa dos dois."', 1),
    ("txt:ind-indicadores",
     '    { value: "4.9", label: "Lorem ipsum" },\n    { value: "240+", label: "Dolor sit amet" },\n    { value: "16yr", label: "Consectetur" }\n',
     '    { value: "+19.000 m²", label: "projetos gerenciados" },\n    { value: "R$ 380 mi", label: "valores somados" },\n    { value: "35", label: "projetos simultâneos" }\n', 1),
    ("txt:ind-grande-1", 'delayIn: 80, children: "Consectetur"', 'delayIn: 80, children: "Do sintoma"', 1),
    ("txt:ind-grande-2", 'delayIn: 170, children: "adipiscing elit"', 'delayIn: 170, children: "à decisão"', 1),
    # onda: quatro frentes de trabalho
    ("txt:onda-1", 'act: "wave", children: "Sed tempor"', 'act: "wave", children: "Quatro frentes"', 1),
    ("txt:onda-2", 'delayIn: 90, children: "ut labore magna"', 'delayIn: 90, children: "de trabalho"', 1),
    ("txt:onda-texto",
     'children: "Ut enim ad minim veniam, quis nostrud exercitation — ullamco laboris nisi aliquip."',
     'children: "Método Sentinela: observar, confrontar, integrar, propor e apoiar. Primeiro a referência, depois o campo, depois o confronto entre os dois."', 1),
    ("txt:onda-cards",
     '    { num: "01", desc: "Lorem ipsum dolor sit amet, consectetur elit." },\n'
     '    { num: "02", desc: "Sed do eiusmod — tempor incididunt ut labore." },\n'
     '    { num: "03", desc: "Ut enim ad minim veniam, quis nostrud." },\n'
     '    { num: "04", desc: "Duis aute irure dolor in voluptate." }\n',
     '    { num: "01", desc: "Diagnóstico de Obra ou Contrato — confrontamos o planejado com o que acontece e separamos sintoma, causa e responsabilidade." },\n'
     '    { num: "02", desc: "Projetos, Terreno e Propostas — análise crítica de projetos, avaliação preliminar de terreno e comparação técnica de propostas." },\n'
     '    { num: "03", desc: "Custos, Planejamento e Medições — orçamento, planejamento e medições, com premissas que permitem conferir." },\n'
     '    { num: "04", desc: "Engenharia de Decisão com IA — preparamos a transição para a IA ou corrigimos o que falha depois dela." }\n', 1),
    # cena final: obra-circuito
    ("txt:final-titulo", 'children: "Voluptas"', 'children: "Comece pela realidade."', 1),
    # no celular o título final tem 3 palavras: quebra em duas linhas, centralizado, e o texto desce
    ("txt:final-titulo-mobile",
     'className: "whitespace-nowrap text-[2.5rem] font-extralight uppercase leading-[1.1] md:text-[4rem]",\n          children: "Comece pela realidade."',
     'className: "text-center text-[1.75rem] font-extralight uppercase leading-[1.1] md:whitespace-nowrap md:text-[4rem]",\n          children: "Comece pela realidade."', 1),
    ("txt:final-caixa-mobile", 'className: "absolute left-1/2 top-[4.75rem] -translate-x-1/2 md:top-[6.0625rem]"',
     'className: "absolute left-1/2 top-[4.75rem] w-[88vw] -translate-x-1/2 md:top-[6.0625rem] md:w-auto"', 1),
    ("txt:final-texto-mobile", "absolute inset-x-[1.25rem] top-[8.5rem] text-center",
     "absolute inset-x-[1.25rem] top-[11rem] text-center", 1),
    ("txt:final-esq",
     'var TAGLINE_LEFT = "Duis aute irure dolor in reprehenderit? In voluptate velit esse cillum dolore — eu fugiat nulla.";',
     'var TAGLINE_LEFT = "Projeto em risco? A IA organiza e compara. Quem decide continua sendo você.";', 1),
    ("txt:final-dir",
     'var TAGLINE_RIGHT = "Excepteur sint occaecat cupidatat non proident. Sunt in culpa qui officia deserunt mollit.";',
     'var TAGLINE_RIGHT = "A CRIVIA ajuda as pessoas e as áreas a trabalhar com ela, com conferência e responsabilidade claras.";', 1),
    ("txt:final-nome", '"aria-label": "Name",\n                placeholder: "Name",',
     '"aria-label": "Nome",\n                placeholder: "Nome",', 1),
    ("txt:final-email", '"aria-label": "Email",\n                type: "email",\n                placeholder: "Email",',
     '"aria-label": "E-mail",\n                type: "email",\n                placeholder: "E-mail",', 1),
    ("txt:final-botao", 'children: [\n                  "Lorem ipsum sit",',
     'onClick: () => { window.location.href = CRIVIA_MAILTO(true); },\n                children: [\n                  "Solicitar Diagnóstico",', 1),
    ("txt:final-botao-cor", "gap-[0.625rem] whitespace-nowrap bg-overlay-solid px-[1rem]",
     "gap-[0.625rem] whitespace-nowrap bg-overlay-ink text-overlay-solid px-[1rem]", 1),
    # marca na tela de carregamento, título oculto e comentário de abertura
    ("txt:carregamento", 'var BRAND2 = "Auralis";', 'var BRAND2 = "CRIVIA";', 1),
    ("txt:h1", 'children: "Auralis — imagine, manifest"',
     'children: "CRIVIA Engenharia Consultiva — Engenharia para Decisão"', 1),
    ("txt:abertura", "/* Auralis — static build of the Next.js app (React 19 + three.js + react-spring + Lenis).",
     "/* CRIVIA — site estático (React 19 + three.js + react-spring + Lenis), gerado por Site_crivia.py.", 1),
    # o HTML pré-renderizado do modelo é descartado: a página monta do zero (sem hidratação)
    ("app:createRoot",
     "if (container) (0, import_client.hydrateRoot)(container, /* @__PURE__ */ (0, import_jsx_runtime29.jsx)(App, {}));",
     "if (container) (0, import_client.createRoot)(container).render(/* @__PURE__ */ (0, import_jsx_runtime29.jsx)(App, {}));", 1),
    # o site não usa cookies nem rastreadores: o aviso de cookies do modelo (em inglês) sai
    ("app:sem-cookies", "    /* @__PURE__ */ (0, import_jsx_runtime28.jsx)(LazyCookie, {}),\n", "", 1),
]

# ── Hero: fundo e botões no estilo Lumina, nas cores da CRIVIA ───────────────
# Componentes novos (inseridos antes de HomeView; usam o mesmo runtime JSX do modelo).
JS_CRIVIA = r"""var CRIVIA_IR_CENARIO = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const foco = () => { const campo = document.querySelector('.crivia-fim .crivia-cta--primary'); if (campo) campo.focus({ preventScroll: true }); };
    const l = window.lenis;
    if (l && l.scrollTo) l.scrollTo(max, { duration: 3.4, onComplete: foco });
    else { window.scrollTo({ top: max, behavior: "smooth" }); setTimeout(foco, 1200); }
  };
  var CRIVIA_IR_CENARIO_GERAL = () => { window.__criviaProduto = null; CRIVIA_IR_CENARIO(); };
  var CRIVIA_CTA_MICRO = "Você não precisa saber qual serviço escolher.";
  var CRIVIA_ABRIR_CENARIO = (origem, interesse) => {
    const q = "?origem=" + encodeURIComponent(origem || "direto") + (interesse ? "&interesse=" + encodeURIComponent(interesse) : "");
    window.location.assign("apresentar-cenario.html" + q);
  };
  var CRIVIA_IR_METODO = () => CRIVIA_NAV["Método"]();
  var criviaIcon = (paths) => /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("svg", {
    viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round",
    "aria-hidden": true, children: paths.map((d, i) => /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("path", { d }, i))
  });
  var CriviaCtaPrimary = ({ onClick, children, compacto }) => /* @__PURE__ */ (0, import_jsx_runtime26.jsxs)("button", {
    type: "button", onClick, className: "crivia-cta crivia-cta--primary" + (compacto ? " crivia-cta--compacto" : ""), children: [
      /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("span", { className: "crivia-cta__spin", "aria-hidden": true }),
      /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("span", { className: "crivia-cta__face", "aria-hidden": true }),
      /* @__PURE__ */ (0, import_jsx_runtime26.jsxs)("span", { className: "crivia-cta__inner", children: [
        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("span", { className: "crivia-cta__icon", children: criviaIcon(["M9 3.5h6v3H9z", "M7 5H6.2A1.2 1.2 0 0 0 5 6.2v13.6A1.2 1.2 0 0 0 6.2 21h11.6a1.2 1.2 0 0 0 1.2-1.2V6.2A1.2 1.2 0 0 0 17.8 5H17", "M8.5 11.5h7", "M8.5 15.5h4.5"]) }),
        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("span", { className: "crivia-cta__label", children }),
        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("span", { className: "crivia-cta__chip", children: criviaIcon(["M5 12h14", "M13 6l6 6-6 6"]) })
      ] })
    ]
  });
  var CriviaCtaSecondary = ({ onClick, children, icone }) => /* @__PURE__ */ (0, import_jsx_runtime26.jsxs)("button", {
    type: "button", onClick, className: "crivia-cta crivia-cta--secondary", children: [
      /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("span", { className: "crivia-cta__points", "aria-hidden": true, children: [0, 1, 2, 3, 4, 5, 6].map((i) => /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("i", { className: "crivia-cta__point" }, i)) }),
      /* @__PURE__ */ (0, import_jsx_runtime26.jsxs)("span", { className: "crivia-cta__inner", children: [
        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("span", { className: "crivia-cta__label", children }),
        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("span", { className: "crivia-cta__arrow", children: criviaIcon(icone || ["M12 5v14", "M6 13l6 6 6-6"]) })
      ] })
    ]
  });
  var CriviaBackdrop = () => /* @__PURE__ */ (0, import_jsx_runtime26.jsxs)("div", {
    "aria-hidden": true, className: "crivia-backdrop pointer-events-none absolute inset-0 overflow-hidden", children: [
      /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("div", { className: "crivia-bg-wash" }),
      /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("div", { className: "crivia-bg-rays" }),
      /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("div", { className: "crivia-bg-glow" }),
      /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("div", { className: "crivia-bg-grid", children: [0, 1, 2, 3, 4].map((i) => /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("div", {
        className: "crivia-bg-col", children: i > 0 && i < 4 ? /* @__PURE__ */ (0, import_jsx_runtime26.jsx)("span", { className: "crivia-bg-beam crivia-bg-beam--" + i }) : null
      }, i)) })
    ]
  });
  var HomeView = () => {"""

# CSS novo (anexado ao main.css): tipografia do Nexus, fundo e botões estilo Lumina.
CSS_CRIVIA = r"""
/* ════ CRIVIA ════ tipografia (Nexus): Plus Jakarta Sans nos títulos, Geist nos textos ════ */
@font-face { font-family: "Plus Jakarta Sans"; font-style: normal; font-weight: 200 800; font-display: swap;
  src: url(../fonts/PlusJakartaSans-latin.woff2) format("woff2"); }
@font-face { font-family: "Geist"; font-style: normal; font-weight: 100 900; font-display: swap;
  src: url(../fonts/Geist-latin.woff2) format("woff2"); }
.googleSans_variable { --font-google-sans: "Plus Jakarta Sans", system-ui, sans-serif; }
.onest_variable { --font-onest: "Geist", system-ui, sans-serif; }
.font-geist { font-family: "Geist", system-ui, sans-serif; }

/* ════ CRIVIA ════ hero: título em duas frases (Nexus: Plus Jakarta Sans em caixa alta, Geist nos detalhes) ════ */
.crivia-hero-title { text-align: center; }
.crivia-hero-title > p { display: block; margin: 0; }
.crivia-hero-wordmark { white-space: nowrap; font-size: 4.5rem; font-weight: 700; line-height: 1; letter-spacing: -.035em; text-transform: uppercase;
  filter: drop-shadow(0 .3rem .45rem rgba(0,29,61,.26)); }
.crivia-hero-title .crivia-hero-wordmark { text-shadow: none !important; }
.crivia-hero-wordmark .line-word > span { color: transparent; -webkit-text-fill-color: transparent;
  background: linear-gradient(180deg, #5C759A 0%, #2F5599 38%, #0F3A8C 68%, #001D3D 100%);
  -webkit-background-clip: text; background-clip: text; }
.crivia-hero-eyebrow { white-space: nowrap; font-family: "Geist", system-ui, sans-serif; font-size: .8125rem; font-weight: 600;
  letter-spacing: .26em; text-transform: uppercase; margin-top: .6rem; padding-left: .26em; color: #0B7FA3; }
.crivia-hero-tagline { font-size: 1.5rem; font-weight: 650; letter-spacing: -.03em; line-height: 1.1; margin-top: 1rem; color: #0A369D; }
.crivia-hero-copy { font-size: .9375rem; font-weight: 400; line-height: 1.55; }
/* frase lateral: cheio (grotesca firme) em contraste com contorno (a palavra "impossível" vazada, que ganha corpo em "possível") */
.crivia-hero-tagline--right { font-family: "Geist", system-ui, sans-serif; font-weight: 700; letter-spacing: -.02em; line-height: 1.12; text-transform: uppercase; }
.crivia-hero-tagline--right .line-word:has(.crivia-tg-oco) { flex-basis: 100%; }
.crivia-tg-oco { font-weight: 500; letter-spacing: -.01em; color: transparent; -webkit-text-fill-color: transparent;
  -webkit-text-stroke: max(1px, .028em) #0A369D; paint-order: stroke fill; }
@media (min-width: 48rem) {
  .crivia-hero-title { text-align: left; }
  .crivia-hero-wordmark { font-size: clamp(3.5rem, 7.2vw, 6rem); }
  .crivia-hero-eyebrow { font-size: clamp(.6875rem, 1.3vw, 1.0625rem); margin-top: 1rem; padding-left: 0; }
  .crivia-hero-tagline { font-size: clamp(1.25rem, 3vw, 2.625rem); max-width: 7.4em; margin-top: 1.5rem; }
  .crivia-hero-copy { font-size: 1.0625rem; }
  .crivia-hero-title { top: 40%; }
  .crivia-hero-right { top: 40%; text-align: right; }
  .crivia-hero-tagline--right { margin: 0 0 0 auto; text-align: right; justify-content: flex-end; }
}

.crivia-hero-frase2 { text-align: left; }
.crivia-hero-tagline.crivia-hero-tagline--rodape { white-space: nowrap; max-width: none; margin: 0; font-size: clamp(1.5rem, 2.7vw, 2.5rem); }
@media (max-width: 47.99rem) {
  .crivia-hero-frase2 { text-align: center; }
  .crivia-hero-tagline.crivia-hero-tagline--rodape { justify-content: center; text-align: center; font-size: 1.45rem; }
}

/* ════ CRIVIA ════ celular: nome acima do C; "Tornando o impossível…" abaixo; sem etiquetas ════ */
@media (max-width: 47.99rem) {
  .crivia-hero-title { top: 4.6rem; }
  .crivia-hero-right { display: block !important; left: 1.25rem; right: 1.25rem; top: auto; bottom: 17.2rem;
    translate: none !important; transform: none !important; text-align: center; }
  .crivia-hero-tagline--right { margin: 0 auto; justify-content: center; text-align: center; max-width: none; font-size: 1.3rem;
    text-shadow: 0 0 .4em rgba(240,248,253,.95), 0 0 .9em rgba(240,248,253,.75); }
  .crivia-hero-tags { display: none !important; }
  .crivia-hero-copy { font-size: .875rem; line-height: 1.45; }
}

/* ════ CRIVIA ════ barra superior em vidro (translúcida, desfoque forte, brilho na borda) ════ */
header.bg-overlay-scrim {
  background: linear-gradient(180deg, rgba(255,255,255,.34) 0%, rgba(240,248,252,.10) 100%) !important;
  -webkit-backdrop-filter: blur(24px) saturate(1.3) !important; backdrop-filter: blur(24px) saturate(1.3) !important;
  border-bottom: 1px solid rgba(255,255,255,.6) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.75), 0 10px 32px rgba(0,29,61,.07);
}

/* ════ CRIVIA ════ tipografia das barras (mesmo padrão do hero: Plus Jakarta Sans na marca, Geist nos menus) ════ */
header.bg-overlay-scrim { font-family: "Geist", system-ui, sans-serif; font-weight: 500; }
header.bg-overlay-scrim nav a { position: relative; font-size: .78rem; font-weight: 500; letter-spacing: .14em; text-transform: uppercase;
  white-space: nowrap; opacity: .92; transition: opacity .25s ease, color .25s ease; }
header.bg-overlay-scrim nav a::after { content: ""; position: absolute; left: 0; right: 0; bottom: -.4rem; height: 1px;
  background: #F5B82E; transform: scaleX(0); transform-origin: left; transition: transform .35s ease; }
header.bg-overlay-scrim nav a:hover { opacity: 1; }
header.bg-overlay-scrim nav a:hover::after { transform: scaleX(1); }
header.bg-overlay-scrim nav a.underline { text-decoration: none; font-weight: 600; opacity: 1; }
header.bg-overlay-scrim nav a.underline::after { transform: scaleX(1); }
header.bg-overlay-scrim > a { font-family: "Plus Jakarta Sans", system-ui, sans-serif; font-size: .9375rem; font-weight: 700;
  letter-spacing: .36em; text-indent: .36em; text-transform: uppercase; }
@media (max-width: 70rem) { header.bg-overlay-scrim nav a { font-size: .72rem; letter-spacing: .08em; }
  header.bg-overlay-scrim > a { letter-spacing: .24em; text-indent: .24em; font-size: .875rem; }
  header.bg-overlay-scrim > a > span[aria-hidden] { display: none !important; } }
/* rodapé do hero: texto de apoio e divisória com o mesmo acabamento */
footer .crivia-hero-copy { letter-spacing: .004em; color: rgba(0,29,61,.88); }
footer .h-px.bg-overlay-line { background: linear-gradient(90deg, rgba(0,29,61,.30), rgba(0,29,61,.07)); }
.crivia-cta__label { font-weight: 600; letter-spacing: .01em; }

/* ════ CRIVIA ════ fundo (Lumina): imagem de raios ao fundo, grade vertical e feixes ════ */
.crivia-canvas { mix-blend-mode: multiply; }
.crivia-backdrop { background: #F4FAFD; }
.crivia-bg-wash { position: absolute; inset: 0;
  background: radial-gradient(ellipse at 50% 40%, #F8FCFE 0%, #E6F3FA 52%, #D3E8F3 100%); }
.crivia-bg-rays { position: absolute; inset: -6%;
  background: url(../images/lights/light_1.png) 70% 0 / cover no-repeat;
  filter: invert(1) sepia(1) hue-rotate(172deg) saturate(2.4) brightness(1.08);
  mix-blend-mode: multiply; opacity: .3; animation: crivia-drift 26s ease-in-out infinite alternate; }
.crivia-bg-glow { position: absolute; inset: 0;
  background: radial-gradient(ellipse at 16% 92%, rgba(245,158,11,.10), transparent 55%),
              radial-gradient(ellipse at 86% 12%, rgba(0,180,216,.16), transparent 55%); }
.crivia-bg-grid { position: absolute; inset: 0; margin: 0 auto; max-width: 80rem; display: flex; opacity: .75; }
.crivia-bg-col { position: relative; flex: 1; overflow: hidden; border-left: 1px solid rgba(0,29,61,.07); }
.crivia-bg-col:last-child { border-right: 1px solid rgba(0,29,61,.07); }
.crivia-bg-beam { position: absolute; top: 0; left: -1px; width: 1px; opacity: 0;
  background: linear-gradient(to bottom, transparent, rgba(0,180,216,.8), transparent);
  animation: crivia-beam 8s ease-in infinite; }
.crivia-bg-beam--1 { height: 16rem; animation-delay: .8s; }
.crivia-bg-beam--2 { height: 24rem; animation-duration: 10s; animation-delay: 3s;
  background: linear-gradient(to bottom, transparent, rgba(245,158,11,.75), transparent); }
.crivia-bg-beam--3 { height: 12rem; animation-delay: 5s; }
@keyframes crivia-beam { 0% { transform: translateY(-120%); opacity: 0; } 15% { opacity: 1; }
  100% { transform: translateY(110vh); opacity: 0; } }
@keyframes crivia-drift { from { transform: translate3d(-1.5%, 0, 0) scale(1.02); }
  to { transform: translate3d(1.5%, 1%, 0) scale(1.06); } }

/* ════ CRIVIA ════ botões (Lumina): pílula com borda giratória e pílula gradiente com partículas ════ */
.crivia-cta { position: relative; display: inline-flex; align-items: center; justify-content: center; isolation: isolate;
  overflow: hidden; border: 0; border-radius: 9999px; cursor: pointer; padding: 0; white-space: nowrap;
  font-family: "Geist", system-ui, sans-serif; transition: transform .3s ease, box-shadow .3s ease; }
.crivia-cta__inner { position: relative; z-index: 2; display: inline-flex; align-items: center; gap: .75rem;
  font-size: .9375rem; font-weight: 500; letter-spacing: -.01em; }
.crivia-cta svg { width: 100%; height: 100%; }
.crivia-cta--primary { background: linear-gradient(to bottom, rgba(34,211,238,.45), rgba(0,29,61,0) 45%, rgba(34,211,238,.18));
  box-shadow: 0 0 22px rgba(0,180,216,.28), 0 8px 36px rgba(10,54,157,.2); }
.crivia-cta--primary:hover { transform: scale(1.05); box-shadow: 0 0 64px 14px rgba(245,184,46,.5), 0 0 30px 4px rgba(10,54,157,.4); }
.crivia-cta__spin { position: absolute; z-index: 0; left: 50%; top: 50%; width: 320%; aspect-ratio: 1; border-radius: 50%;
  transform: translate(-50%, -50%); animation: crivia-spin 3s linear infinite;
  background: conic-gradient(from 0deg, transparent 0deg, transparent 80deg, rgba(245,158,11,.95) 180deg, transparent 280deg, transparent 360deg); }
.crivia-cta__face { position: absolute; inset: 1px; z-index: 1; border-radius: 9999px; background: rgba(0,29,61,.96);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); transition: inset .3s ease; }
/* brilho no hover: borda de luz mais grossa e uma segunda luz que entra girando junto, acelerando o giro (3 s -> ~2 s) */
.crivia-cta--primary:hover .crivia-cta__face { inset: 2px; }
.crivia-cta__spin { transition: filter .35s ease; }
.crivia-cta--primary:hover .crivia-cta__spin { filter: brightness(1.3) saturate(1.25); }
.crivia-cta__spin::after { content: ""; position: absolute; inset: 0; border-radius: 50%; opacity: 0; transition: opacity .35s ease;
  animation: crivia-spin-extra 6s linear infinite;
  background: conic-gradient(from 90deg, transparent 0deg, transparent 70deg, rgba(255,214,102,1) 165deg, #fff 185deg, rgba(255,214,102,1) 205deg, transparent 300deg, transparent 360deg); }
.crivia-cta--primary:hover .crivia-cta__spin::after { opacity: 1; }
.crivia-cta--primary .crivia-cta__inner { padding: .7rem 1.1rem .7rem .85rem; color: #F4FAFD; }
.crivia-cta__icon { width: 1.75rem; height: 1.75rem; padding: .4rem; border-radius: 9999px; color: #001D3D;
  background: linear-gradient(to bottom, #FBBF24, #F59E0B); box-shadow: 0 4px 10px rgba(245,158,11,.35), inset 0 0 0 1px rgba(255,255,255,.28);
  transition: transform .3s ease; }
.crivia-cta--primary:hover .crivia-cta__icon { transform: scale(1.1); }
.crivia-cta__chip { width: 1.5rem; height: 1.5rem; padding: .35rem; border-radius: 9999px; margin-left: .15rem;
  background: rgba(244,250,253,.14); color: rgba(244,250,253,.85); transition: transform .3s ease; }
.crivia-cta--primary:hover .crivia-cta__chip { transform: translateX(2px); color: #fff; }
.crivia-cta--secondary { min-height: 2.75rem; padding: .6rem 1.4rem; color: #fff;
  background: radial-gradient(65% 65% at 50% 100%, rgba(34,211,238,.85) 0%, rgba(34,211,238,0) 100%), linear-gradient(0deg, #0A369D, #0A369D);
  box-shadow: 0 6px 24px rgba(10,54,157,.28); }
.crivia-cta--secondary::before { content: ""; position: absolute; inset: 1px; z-index: 0; border-radius: 9999px;
  background: linear-gradient(177.95deg, rgba(255,255,255,.3) 0%, rgba(255,255,255,0) 100%); }
.crivia-cta--secondary::after { content: ""; position: absolute; inset: 2px; z-index: 0; border-radius: 9999px;
  background: radial-gradient(65% 65% at 50% 100%, rgba(34,211,238,.85) 0%, rgba(34,211,238,0) 100%), linear-gradient(0deg, #0A369D, #0A369D); }
.crivia-cta--secondary:hover { transform: translateY(-1px); box-shadow: 0 10px 30px rgba(10,54,157,.38); }
.crivia-cta--secondary .crivia-cta__inner { gap: .5rem; }
.crivia-cta__arrow { width: 1rem; height: 1rem; transition: transform .3s ease; }
.crivia-cta--secondary:hover .crivia-cta__arrow { transform: translateY(2px); }
.crivia-cta__points { position: absolute; inset: 0; z-index: 1; overflow: hidden; pointer-events: none; }
.crivia-cta__point { position: absolute; bottom: -10px; width: 2px; height: 2px; border-radius: 9999px; background: #fff;
  pointer-events: none; animation: crivia-float infinite ease-in-out; }
.crivia-cta__point:nth-child(1) { left: 10%; opacity: 1; animation-duration: 2.35s; animation-delay: .2s; }
.crivia-cta__point:nth-child(2) { left: 30%; opacity: .7; animation-duration: 2.5s; animation-delay: .5s; }
.crivia-cta__point:nth-child(3) { left: 25%; opacity: .8; animation-duration: 2.2s; animation-delay: .1s; }
.crivia-cta__point:nth-child(4) { left: 44%; opacity: .6; animation-duration: 2.05s; }
.crivia-cta__point:nth-child(5) { left: 50%; opacity: 1; animation-duration: 1.9s; }
.crivia-cta__point:nth-child(6) { left: 75%; opacity: .5; animation-duration: 1.5s; animation-delay: 1.5s; }
.crivia-cta__point:nth-child(7) { left: 88%; opacity: .9; animation-duration: 2.2s; animation-delay: .2s; }
@keyframes crivia-float { 0% { transform: translateY(0); } 85% { opacity: 0; } 100% { transform: translateY(-55px); opacity: 0; } }
@keyframes crivia-spin { to { transform: translate(-50%, -50%) rotate(360deg); } }
@keyframes crivia-spin-extra { to { transform: rotate(360deg); } }
@media (max-width: 47.99rem) {
  .crivia-cta__inner { font-size: .8125rem; gap: .5rem; }
  .crivia-cta--primary .crivia-cta__inner { padding: .55rem .8rem .55rem .65rem; }
  .crivia-cta__icon { width: 1.5rem; height: 1.5rem; padding: .35rem; }
  .crivia-cta--secondary { padding: .5rem 1.1rem; min-height: 2.4rem; }
}
@media (prefers-reduced-motion: reduce) {
  .crivia-bg-beam, .crivia-bg-rays, .crivia-cta__spin, .crivia-cta__spin::after, .crivia-cta__point { animation: none; }
}
"""

SOBRE_JS = r"""  // ── CRIVIA ── dobra "Sobre": pausa na rolagem + painel de apresentação ──
  var CRIVIA_PCE_VIDEO = "";
  var criviaH = (tag, props, ...kids) => kids.length ? (0, import_jsx_runtime26.jsxs)(tag, { ...props, children: kids }) : (0, import_jsx_runtime26.jsx)(tag, props);
  var CRIVIA_FORMULAS = [
    ["Visão", "Tornar possível o que parecia impossível."],
    ["Missão", "Encontrar rápido a causa por trás do sintoma em projetos críticos e entregar a quem decide uma solução que cabe na realidade."],
    ["Filosofia", "Controle mostra o sintoma. Compreensão revela a causa. Boa decisão precisa dos dois."],
    ["Marca de liderança", "Vemos a realidade antes de opinar e tornamos compreensível o que precisa ser decidido."],
    ["Lógica de atuação", "Observar → Confrontar → Integrar → Propor → Apoiar."],
    ["Método Sentinela", "A inteligência da CRIVIA aplicada a cada problema: perguntas estruturantes, critérios de risco, diagnóstico e padrões de entrega."]
  ];
  var criviaIrY = (y, dur) => {
    const l = window.lenis;
    if (l && l.scrollTo) l.scrollTo(y, { duration: dur });
    else window.scrollTo({ top: y, behavior: "smooth" });
  };
  var CRIVIA_NAV = {
    "Início": () => criviaIrY(0, 2.6),
    "CRIVIA": () => criviaIrY(0, 2.6),
    "Produtos": () => { const m = document.documentElement.scrollHeight - window.innerHeight; criviaIrY(criviaS0(m) + (window.__criviaHoldPx || 0) * 0.02, 2.6); },
    "Decisão com IA": () => CRIVIA_NAV["Produtos"](),
    "Diagnóstico Sentinela": () => CRIVIA_NAV["Produtos"](),
    "Sobre": () => { const m = document.documentElement.scrollHeight - window.innerHeight; criviaIrY(criviaS0(m) + (window.__criviaHoldPx || 0) * 0.78, 3); },
    "Fale conosco": () => CRIVIA_IR_CENARIO_GERAL(),
    "Método": () => { const m = document.documentElement.scrollHeight - window.innerHeight; criviaIrY(criviaS0(m) + (window.__criviaHoldPx || 0) + (window.__criviaMetodoPx || 0) * 0.22, 3); }
  };
  document.addEventListener("click", (e) => {
    const a = e.target && e.target.closest ? e.target.closest("a") : null;
    if (!a) return;
    const nome = a.textContent.trim() || (a.getAttribute("aria-label") || "").split(" — ")[0];
    const ir = CRIVIA_NAV[nome];
    if (!ir || !(a.getAttribute("href") === "#" || a.closest("header"))) return;
    e.preventDefault();
    if (a.closest('nav[aria-label="Mobile"]')) setTimeout(ir, 450);
    else ir();
  }, true);
  var CriviaVideoPce = () => {
    const [tocando, setTocando] = (0, import_react35.useState)(false);
    const tem = !!CRIVIA_PCE_VIDEO;
    return criviaH("div", { className: "crivia-sobre__pilha" },
      criviaH("div", { className: "crivia-sobre__video" },
        tocando
          ? criviaH("video", { className: "crivia-sobre__video-el", src: CRIVIA_PCE_VIDEO, controls: true, autoPlay: true, playsInline: true })
          : criviaH("button", { type: "button", className: "crivia-sobre__play", "aria-label": "Assistir ao vídeo", onClick: () => { if (tem) setTocando(true); } },
              criviaH("span", { className: "crivia-sobre__play-anel", "aria-hidden": true }),
              criviaH("svg", { viewBox: "0 0 24 24", "aria-hidden": true }, criviaH("path", { d: "M8 5.2v13.6a.6.6 0 0 0 .92.5l10.6-6.8a.6.6 0 0 0 0-1L8.92 4.7A.6.6 0 0 0 8 5.2z", fill: "currentColor" }))),
        tocando || tem ? null : criviaH("div", { className: "crivia-sobre__legenda" }, criviaH("span", { className: "crivia-sobre__legenda-breve" }, "Vídeo em breve"))));
  };
  var SobreOverlay = () => {
    const rootRef = (0, import_react35.useRef)(null);
    const rolaRef = (0, import_react35.useRef)(null);
    (0, import_react35.useEffect)(() => {
      const root = rootRef.current;
      const rola = rolaRef.current;
      if (!root || !rola) return;
      let raf = 0;
      let chave = "";
      let ligado = false;
      const marcar = () => {
        if (rola.scrollHeight > rola.clientHeight + 2) rola.setAttribute("data-lenis-prevent", "");
        else rola.removeAttribute("data-lenis-prevent");
      };
      const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(marcar) : null;
      if (ro) { ro.observe(rola); if (rola.firstElementChild) ro.observe(rola.firstElementChild); }
      marcar();
      const tick = () => {
        raf = requestAnimationFrame(tick);
        const y = window.scrollY;
        const k = y + ":" + window.innerHeight + ":" + (window.__criviaHoldPx || 0);
        if (k === chave) return;
        const max = document.documentElement.scrollHeight - window.innerHeight;
        const hold = window.__criviaHoldPx || 0;
        if (max <= 0 || !hold) return;
        chave = k;
        const s0 = criviaS0(max);
        const t = (y - s0) / hold;
        const o = clamp01(Math.min((t - 0.5) / 0.16, (1 - t) / 0.08));
        root.style.opacity = o.toFixed(3);
        root.style.visibility = o <= 0.001 ? "hidden" : "visible";
        root.style.pointerEvents = o > 0.5 ? "auto" : "none";
        root.style.transform = "translateY(" + ((1 - o) * 1.2).toFixed(2) + "rem)";
        const on = t > 0.58 && t < 0.95;
        if (on !== ligado) { ligado = on; root.classList.toggle("is-on", on); }
      };
      raf = requestAnimationFrame(tick);
      return () => { cancelAnimationFrame(raf); if (ro) ro.disconnect(); };
    }, []);
    const rev = (i, cls) => ({ className: "crivia-rev" + (cls ? " " + cls : ""), style: { "--i": i } });
    return criviaH("section", { ref: rootRef, id: "sobre", className: "crivia-sobre", "aria-label": "Sobre a CRIVIA" },
      criviaH("div", { className: "crivia-sobre__eixo", "aria-hidden": true }, criviaH("i", {})),
      criviaH("div", { ref: rolaRef, className: "crivia-sobre__rola" },
        criviaH("div", { className: "crivia-sobre__in" },
          criviaH("div", { className: "crivia-sobre__cab" },
            criviaH("div", { className: "crivia-sobre__cab-tit" },
              criviaH("span", { className: "crivia-sobre__eyebrow crivia-rev", style: { "--i": 0 } }, criviaH("i", {}), "Sobre a CRIVIA"),
              criviaH("h2", { className: "crivia-sobre__titulo" },
                criviaH("span", { className: "crivia-ln" }, criviaH("span", { style: { "--i": 1 } }, "Engenharia")),
                criviaH("span", { className: "crivia-ln" }, criviaH("span", { style: { "--i": 2 } }, "para decisão.")))),
            criviaH("p", rev(4, "crivia-sobre__lead"), "A CRIVIA é engenharia independente para decisões críticas: encontra a causa por trás do sintoma e entrega a quem decide uma solução que cabe na realidade.")),
          criviaH("div", rev(3, "crivia-sobre__videobox"), criviaH(CriviaVideoPce, {})),
          criviaH("div", rev(5, "crivia-sobre__bruno"),
            criviaH("div", { className: "crivia-sobre__bruno-topo" },
              criviaH("span", { className: "crivia-sobre__mono", "aria-hidden": true }, "BM"),
              criviaH("div", {}, criviaH("strong", {}, "Bruno Malta"), criviaH("span", {}, "Engenheiro e fundador da CRIVIA"))),
            criviaH("p", { className: "crivia-sobre__bruno-txt" }, "Sou engenheiro e, há mais de 20 anos, lidero grandes projetos e equipes multidisciplinares. Fui chamado para o que ninguém queria assumir, e aprendi que, quase sempre, a causa não está onde o sintoma aparece."),
            criviaH("p", { className: "crivia-sobre__bruno-cham" }, "Por isso criei a CRIVIA.")),
          criviaH("div", { className: "crivia-sobre__formulas" },
            criviaH("p", rev(4, "crivia-sobre__rotulo"), "Fórmulas centrais"),
            criviaH("ol", {}, CRIVIA_FORMULAS.map((f, i) =>
              criviaH("li", { key: f[0], className: "crivia-sobre__f", style: { "--i": 5 + i } },
                criviaH("span", { className: "crivia-sobre__num" }, String(i + 1).padStart(2, "0")),
                criviaH("div", { className: "crivia-sobre__f-corpo" }, criviaH("strong", {}, f[0]), criviaH("p", {}, ...(f[1].indexOf("→") < 0 ? [f[1]] : f[1].split(" → ").flatMap((x, k) => k ? [criviaH("span", { key: "s" + k, className: "crivia-sobre__seta" }, "→"), x] : [x])))))))))));
  };

  var CRIVIA_MOV = [
    ["Observar", "Consultar as referências disponíveis e verificar a realidade dentro do escopo.", "olho"],
    ["Confrontar", "Comparar projeto, contrato, cronograma ou premissas com o que foi observado.", "comparar"],
    ["Integrar", "Relacionar equipe, materiais, equipamentos, projeto, contrato e fornecedores.", "integrar"],
    ["Propor", "Apresentar causas sustentadas e caminhos compatíveis com as condições reais.", "caminhos"],
    ["Apoiar", "Apoiar quem decide e verificar os efeitos quando isso fizer parte do escopo contratado.", "apoio"]
  ];
  var CRIVIA_MOV_ICONES = {
    olho: ["M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z", "M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0z"],
    comparar: ["M4 5h6v14H4z", "M14 5h6v14h-6z", "M10.5 9h3", "M10.5 15h3"],
    integrar: ["M8 6a2 2 0 1 1-4 0 2 2 0 0 1 4 0z", "M20 6a2 2 0 1 1-4 0 2 2 0 0 1 4 0z", "M14 18a2 2 0 1 1-4 0 2 2 0 0 1 4 0z", "M8 6h8", "M5.6 7.8l5.2 8.6", "M18.4 7.8l-5.2 8.6"],
    caminhos: ["M12 21v-8", "M12 13c0-3-6-3-6-8", "M12 13c0-3 6-3 6-8", "M3.5 7.5 6 5l2.5 2.5", "M15.5 7.5 18 5l2.5 2.5"],
    apoio: ["M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z", "M9 12l2 2 4-4"]
  };
  var CRIVIA_ORDEM = ["Realidade", "causa", "risco", "responsabilidade", "decisão", "dinheiro", "execução", "verificação"];
  var CRIVIA_PARTES = [[-1, 0.34], [0.34, 0.67], [0.67, 2]];
  var CriviaIcone = ({ nome }) => criviaH("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true },
    ...CRIVIA_MOV_ICONES[nome].map((d, i) => criviaH("path", { key: i, d })));
  var CRIVIA_IR_MOVIMENTOS = () => {
    const m = document.documentElement.scrollHeight - window.innerHeight;
    criviaIrY(criviaS0(m) + (window.__criviaHoldPx || 0) + (window.__criviaMetodoPx || 0) * 0.51, 2.4);
  };
  var MetodoOverlay = () => {
    const rootRef = (0, import_react35.useRef)(null);
    const partesRef = (0, import_react35.useRef)([]);
    const figRef = (0, import_react35.useRef)(null);
    (0, import_react35.useEffect)(() => {
      const root = rootRef.current;
      if (!root) return;
      const partes = partesRef.current;
      const ligadas = [false, false, false];
      let raf = 0, chave = "";
      const marcar = () => partes.forEach((p) => {
        const rola = p && p.firstElementChild;
        if (!rola) return;
        if (rola.scrollHeight > rola.clientHeight + 2) rola.setAttribute("data-lenis-prevent", "");
        else rola.removeAttribute("data-lenis-prevent");
      });
      const escala = () => { const f = figRef.current; if (f && f.clientWidth) f.style.setProperty("--k", (f.clientWidth / 1200).toFixed(4)); };
      const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(() => { marcar(); escala(); }) : null;
      if (ro) { partes.forEach((p) => { if (p && p.firstElementChild) { ro.observe(p.firstElementChild); if (p.firstElementChild.firstElementChild) ro.observe(p.firstElementChild.firstElementChild); } }); if (figRef.current) ro.observe(figRef.current); }
      marcar(); escala();
      const tick = () => {
        raf = requestAnimationFrame(tick);
        const y = window.scrollY;
        const k = y + ":" + window.innerHeight;
        if (k === chave) return;
        const max = document.documentElement.scrollHeight - window.innerHeight;
        const hold = window.__criviaHoldPx || 0;
        const hold2 = window.__criviaMetodoPx || 0;
        if (max <= 0 || !hold2) return;
        chave = k;
        const u = (y - criviaS0(max) - hold) / hold2;
        const o = clamp01(Math.min((u - 0.04) / 0.2, (1 - u) / 0.12));
        root.style.opacity = o.toFixed(3);
        root.style.visibility = o <= 0.001 ? "hidden" : "visible";
        root.style.pointerEvents = o > 0.5 ? "auto" : "none";
        CRIVIA_PARTES.forEach(([a, b], i) => {
          const p = partes[i];
          if (!p) return;
          const po = clamp01(Math.min((u - a) / 0.07, (b - u) / 0.07));
          p.style.opacity = po.toFixed(3);
          p.style.visibility = po <= 0.001 ? "hidden" : "visible";
          p.style.pointerEvents = po > 0.5 ? "auto" : "none";
          const on = i === 0 ? u > 0.14 && u < b - 0.03 : u > a + 0.05 && u < (i === 2 ? 0.96 : b - 0.03);
          if (on !== ligadas[i]) { ligadas[i] = on; p.classList.toggle("is-on", on); }
        });
      };
      raf = requestAnimationFrame(tick);
      return () => { cancelAnimationFrame(raf); if (ro) ro.disconnect(); };
    }, []);
    const rev = (i, cls) => ({ className: "crivia-rev" + (cls ? " " + cls : ""), style: { "--i": i } });
    const ln = (i, txt) => criviaH("span", { className: "crivia-ln" }, criviaH("span", { style: { "--i": i } }, txt));
    const eyebrow = (txt) => criviaH("span", { className: "crivia-sobre__eyebrow crivia-rev", style: { "--i": 0 } }, criviaH("i", {}), txt);
    const parte = (i, ...kids) => criviaH("div", { ref: (el) => { partesRef.current[i] = el; }, className: "crivia-metodo__parte" },
      criviaH("div", { className: "crivia-sobre__rola" }, criviaH("div", { className: "crivia-metodo__in crivia-metodo__in--" + (i + 1) }, ...kids)));
    return criviaH("section", { ref: rootRef, id: "metodo", className: "crivia-sobre crivia-metodo", "aria-label": "Método Sentinela" },
      parte(0,
        criviaH("div", { className: "crivia-metodo__txt" },
          eyebrow("Método"),
          criviaH("h2", { className: "crivia-sobre__titulo" }, ln(1, "Método"), ln(2, "Sentinela")),
          criviaH("p", rev(3, "crivia-metodo__frase"), "Compreender antes de decidir."),
          criviaH("p", rev(4, "crivia-metodo__corpo"), "Em projetos e operações complexas, atrasos, custos acima do previsto e conflitos podem ser sintomas de uma situação ainda não compreendida. O Método Sentinela orienta a leitura da realidade, o confronto entre referências e evidências e a integração das interfaces para identificar causas sustentadas e apoiar caminhos compatíveis com as condições reais."),
          criviaH("div", rev(5, "crivia-metodo__acoes"),
            criviaH(CriviaCtaPrimary, { onClick: () => CRIVIA_ABRIR_CENARIO("metodo"), children: "Apresentar meu cenário" }),
            criviaH("button", { type: "button", className: "crivia-metodo__link", onClick: CRIVIA_IR_MOVIMENTOS },
              "Conhecer os movimentos do método",
              criviaH("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true }, criviaH("path", { d: "M12 5v14" }), criviaH("path", { d: "M6 13l6 6 6-6" })))),
          criviaH("p", rev(6, "crivia-metodo__micro"), CRIVIA_CTA_MICRO),
          criviaH("p", rev(7, "crivia-metodo__nota"), "Metodologia própria da CRIVIA, em desenvolvimento. A aplicação é ajustada ao problema, às evidências, aos riscos e ao escopo de cada trabalho.")),
        criviaH("figure", { ref: figRef, className: "crivia-rev crivia-metodo__fig", style: { "--i": 4 } },
          criviaH("div", { className: "crivia-metodo__quadro" },
            criviaH("img", { src: "assets/images/metodo/tablet-industrial.png", width: 1200, height: 896, loading: "lazy", decoding: "async",
              alt: "Tablet em primeiro plano sobre uma bancada, com uma instalação industrial de tubulações e tanques de aço inox ao fundo; a tela mostra os cinco movimentos do método: observar, confrontar, integrar, propor e apoiar." }),
            criviaH("div", { className: "crivia-metodo__tela", "aria-hidden": true },
              criviaH("div", { className: "crivia-metodo__tela-top" }, criviaH("i", {}), "Método Sentinela"),
              criviaH("div", { className: "crivia-metodo__tela-trilha" }, ...CRIVIA_MOV.map((m) =>
                criviaH("div", { key: m[0], className: "crivia-metodo__tela-mov" }, criviaH("span", {}, criviaH(CriviaIcone, { nome: m[2] })), criviaH("b", {}, m[0])))))))),
      parte(1,
        criviaH("div", { className: "crivia-metodo__cab" },
          eyebrow("Método Sentinela"),
          criviaH("h2", { className: "crivia-sobre__titulo" }, ln(1, "Cinco movimentos"), ln(2, "orientadores")),
          criviaH("p", rev(3, "crivia-sobre__lead"), "Eles organizam a leitura do problema e podem ser ajustados conforme a situação, as evidências e o trabalho contratado.")),
        criviaH("ol", { className: "crivia-metodo__movs" }, CRIVIA_MOV.map((m, i) =>
          criviaH("li", { key: m[0], className: "crivia-metodo__mov crivia-rev", style: { "--i": 4 + i } },
            criviaH("span", { className: "crivia-metodo__ico" }, criviaH(CriviaIcone, { nome: m[2] })),
            criviaH("strong", {}, m[0]),
            criviaH("p", {}, m[1]))))),
      parte(2,
        criviaH("div", { className: "crivia-metodo__cab" },
          eyebrow("Ordem de referência"),
          criviaH("h2", { className: "crivia-sobre__titulo" }, ln(1, "Da realidade"), ln(2, "à verificação"))),
        criviaH("ol", { className: "crivia-metodo__ordem" }, CRIVIA_ORDEM.map((t, i) =>
          criviaH("li", { key: t, className: "crivia-metodo__no crivia-rev", style: { "--i": 3 + i } }, criviaH("span", {}, t)))),
        criviaH("p", rev(11, "crivia-metodo__apoio"), "Essa ordem ajuda a relacionar a recomendação à situação observada e à decisão que precisa ser tomada. A decisão e a execução cabem ao cliente; a CRIVIA oferece apoio estratégico dentro do escopo contratado.")));
  };
"""

CSS_METODO = r"""
/* ════ CRIVIA ════ dobra "Método" (três partes na pausa de rolagem; mesma entrada de texto da Sobre) ════ */
.crivia-metodo__parte { position: absolute; inset: 0; opacity: 0; visibility: hidden; pointer-events: none; }
.crivia-metodo .crivia-metodo__parte.is-on .crivia-rev, .crivia-metodo .crivia-metodo__parte.is-on .crivia-ln > span {
  opacity: 1; transform: none; filter: none; transition: opacity 1.5s cubic-bezier(.16,1,.3,1), transform 1.6s cubic-bezier(.16,1,.3,1), filter 1.5s cubic-bezier(.16,1,.3,1);
  transition-delay: calc(var(--i, 0) * 260ms + 120ms); }
.crivia-metodo__in { box-sizing: border-box; min-height: 100%; max-width: 80rem; margin: 0 auto; padding: 5rem 1.25rem 2.5rem;
  display: flex; flex-direction: column; justify-content: center; gap: 1.6rem; }
.crivia-metodo__txt { display: flex; flex-direction: column; align-items: flex-start; gap: 1rem; }
.crivia-metodo__txt .crivia-sobre__titulo { margin-top: .5rem; }
.crivia-metodo__cab { display: flex; flex-direction: column; gap: 1rem; }
.crivia-metodo__frase { margin: .2rem 0 0; position: relative; padding-left: 1.1rem; font-family: "Plus Jakarta Sans", system-ui, sans-serif; font-size: clamp(1.15rem, 1.7vw, 1.5rem); font-weight: 650; letter-spacing: -.02em; color: #2F6BFF; }
.crivia-metodo__frase::before { content: ""; position: absolute; left: 0; top: .2em; bottom: .2em; width: 2px; border-radius: 2px; background: linear-gradient(180deg, #F5B82E, rgba(245,184,46,.15)); }
.crivia-metodo__corpo { margin: 0; max-width: 35rem; font-size: clamp(.93rem, 1.05vw, 1rem); line-height: 1.62; color: #1E3B63; }
.crivia-metodo__acoes { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem 1.6rem; margin-top: .3rem; }
.crivia-metodo__link { display: inline-flex; align-items: center; gap: .5rem; padding: .4rem 0; border: 0; background: none; cursor: pointer; font: inherit; font-size: .88rem; font-weight: 600; color: #0A369D;
  border-bottom: 1px solid rgba(10,54,157,.3); transition: color .3s ease, border-color .3s ease, gap .3s ease; }
.crivia-metodo__link svg { width: .95rem; height: .95rem; }
.crivia-metodo__link:hover, .crivia-metodo__link:focus-visible { color: #2F6BFF; border-color: #2F6BFF; gap: .75rem; outline: none; }
.crivia-metodo__micro { margin: -.2rem 0 0; font-size: .8rem; color: #3F5E82; }
.crivia-metodo__nota { margin: .4rem 0 0; max-width: 34rem; font-size: .76rem; line-height: 1.5; color: #5A7595; }

/* imagem: quadro com bordas empilhadas como a caixa de vídeo da Sobre; a tela do tablet recebe os ícones em HTML */
.crivia-metodo__fig { position: relative; margin: 0; width: 100%; --k: .5; }
.crivia-metodo__fig::before, .crivia-metodo__fig::after { content: ""; position: absolute; z-index: 0; height: 50%; border-radius: 1.2rem; background: linear-gradient(180deg, #0A369D, #001D3D); }
.crivia-metodo__fig::before { left: 5%; right: 5%; bottom: -.6rem; opacity: .5; }
.crivia-metodo__fig::after { left: 10%; right: 10%; bottom: -1.15rem; opacity: .26; }
.crivia-metodo__quadro { position: relative; z-index: 1; width: 100%; aspect-ratio: 1200 / 896; border-radius: 1.4rem; overflow: hidden; border: 1px solid rgba(255,255,255,.35);
  box-shadow: 0 2rem 3.4rem -1.6rem rgba(0,29,61,.6); background: #0A2A5E; }
.crivia-metodo__quadro img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; display: block; }
.crivia-metodo__tela { position: absolute; left: 0; top: 0; width: 480px; height: 340px; box-sizing: border-box; padding: 26px 22px; transform-origin: 0 0; pointer-events: none;
  transform: scale(var(--k)) matrix3d(0.73971,-0.100311,0,-0.000240962,-0.205346,0.862302,0,-7.76226e-05,0,0,1,0,432,401,0,1);
  display: flex; flex-direction: column; justify-content: space-between; color: #E8F4FF;
  background: radial-gradient(120% 90% at 50% 0%, rgba(47,107,255,.55), rgba(47,107,255,0) 60%), linear-gradient(170deg, #0B2C6B, #061B44 70%, #04122D); font-family: "Geist", system-ui, sans-serif; }
.crivia-metodo__tela-top { display: flex; align-items: center; gap: 10px; font-size: 17px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: #BFE6FF; }
.crivia-metodo__tela-top i { width: 9px; height: 9px; border-radius: 50%; background: #F5B82E; box-shadow: 0 0 0 4px rgba(245,184,46,.25); }
.crivia-metodo__tela-trilha { position: relative; display: grid; grid-template-columns: repeat(5, 1fr); align-items: start; padding-bottom: 30px; }
.crivia-metodo__tela-trilha::before { content: ""; position: absolute; left: 10%; right: 10%; top: 35px; height: 2px; background: linear-gradient(90deg, rgba(34,211,238,.15), rgba(34,211,238,.8), rgba(34,211,238,.15)); }
.crivia-metodo__tela-mov { position: relative; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.crivia-metodo__tela-mov span { width: 70px; height: 70px; border-radius: 50%; display: grid; place-items: center; color: #7EE3FF; background: rgba(6,27,68,.92);
  border: 2px solid rgba(34,211,238,.7); box-shadow: 0 0 22px rgba(34,211,238,.35); }
.crivia-metodo__tela-mov span svg { width: 38px; height: 38px; }
.crivia-metodo__tela-mov b { font-size: 17px; font-weight: 600; letter-spacing: .01em; color: #E8F4FF; }

/* segunda parte: cinco movimentos ligados por um traço sutil */
.crivia-metodo__movs { list-style: none; margin: 1rem 0 0; padding: 0; position: relative; display: grid; grid-template-columns: minmax(0, 1fr); gap: 1.4rem; }
.crivia-metodo__movs::before { content: ""; position: absolute; left: 1.7rem; top: 1.7rem; bottom: 1.7rem; width: 1px; background: linear-gradient(180deg, rgba(10,54,157,.4), rgba(10,54,157,.12)); }
.crivia-metodo__mov { position: relative; display: grid; grid-template-columns: 3.4rem 1fr; column-gap: 1.1rem; align-items: center; }
.crivia-metodo__mov strong { font-family: "Plus Jakarta Sans", system-ui, sans-serif; font-size: 1.35rem; font-weight: 700; letter-spacing: -.03em; color: #001D3D; }
.crivia-metodo__mov p { grid-column: 2; margin: .15rem 0 0; font-size: .92rem; line-height: 1.5; color: #2F4A70; }
.crivia-metodo__ico { grid-row: 1 / span 2; width: 3.4rem; height: 3.4rem; border-radius: 50%; display: grid; place-items: center; color: #0A369D; position: relative; z-index: 1;
  background: linear-gradient(160deg, rgba(255,255,255,.95), rgba(236,243,255,.85)); border: 1px solid rgba(47,107,255,.3);
  box-shadow: 0 1rem 1.8rem -1rem rgba(10,54,157,.5), 0 0 0 5px rgba(47,107,255,.07); transition: transform .4s cubic-bezier(.16,1,.3,1), color .3s ease, box-shadow .3s ease; }
.crivia-metodo__ico svg { width: 1.5rem; height: 1.5rem; }
.crivia-metodo__mov:hover .crivia-metodo__ico { transform: translateY(-3px) scale(1.06); color: #2F6BFF; box-shadow: 0 1.2rem 2rem -1rem rgba(47,107,255,.6), 0 0 0 7px rgba(47,107,255,.1); }

/* terceira parte: a ordem de referência */
.crivia-metodo__ordem { list-style: none; margin: .8rem 0 0; padding: 1.2rem 1.2rem; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem .4rem; align-items: center;
  border-radius: 1.25rem; background: linear-gradient(160deg, rgba(255,255,255,.92), rgba(238,245,255,.78)); border: 1px solid rgba(47,107,255,.24);
  -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px); box-shadow: 0 26px 60px -28px rgba(10,54,157,.45), 0 2px 0 rgba(255,255,255,.9) inset; }
.crivia-metodo__no { display: flex; align-items: center; min-width: 0; }
.crivia-metodo__no span { flex: 1; min-width: 0; box-sizing: border-box; padding: .75rem .6rem; border-radius: 9999px; text-align: center; font-family: "Plus Jakarta Sans", system-ui, sans-serif; font-size: clamp(.9rem, 1.5vw, 1.3rem); font-weight: 650; letter-spacing: -.01em;
  color: #0A369D; background: rgba(47,107,255,.08); border: 1px solid rgba(47,107,255,.25); }
.crivia-metodo__no:first-child span { color: #fff; background: linear-gradient(145deg, #2F6BFF, #0A369D); border-color: transparent; }
.crivia-metodo__no:last-child span { color: #fff; background: linear-gradient(145deg, #0A369D, #001D3D); border-color: transparent; }
.crivia-metodo__no:not(:nth-child(2n))::after { content: ""; width: 1.7rem; height: 1.7rem; flex: none; background: no-repeat center / 1.1rem 1.1rem;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232F6BFF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12h14'/%3E%3Cpath d='M13 6l6 6-6 6'/%3E%3C/svg%3E"); }
.crivia-metodo__apoio { margin: .4rem 0 0; max-width: 46rem; font-size: clamp(.95rem, 1.15vw, 1.05rem); line-height: 1.6; color: #1E3B63; }

@media (min-width: 48rem) {
  .crivia-metodo__in { padding: 5.25rem 2.5rem 2rem; }
  .crivia-metodo__movs { grid-template-columns: repeat(5, minmax(0, 1fr)); column-gap: 1.2rem; margin-top: 1.6rem; }
  .crivia-metodo__movs::before { left: 8%; right: 8%; top: 1.7rem; bottom: auto; width: auto; height: 1px; background: linear-gradient(90deg, rgba(10,54,157,.08), rgba(10,54,157,.4), rgba(10,54,157,.08)); }
  .crivia-metodo__mov { grid-template-columns: 1fr; justify-items: start; row-gap: .6rem; }
  .crivia-metodo__mov p { grid-column: 1; }
  .crivia-metodo__ico { grid-row: auto; }
}
@media (min-width: 48rem) {
  .crivia-metodo__ordem { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1.4rem .3rem; padding: 1.8rem 1.8rem; }
  .crivia-metodo__no:not(:nth-child(2n))::after { display: block; }
  .crivia-metodo__no:nth-child(2n)::after { content: ""; width: 1.7rem; height: 1.7rem; flex: none; background: no-repeat center / 1.1rem 1.1rem;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232F6BFF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12h14'/%3E%3Cpath d='M13 6l6 6-6 6'/%3E%3C/svg%3E"); }
  .crivia-metodo__no:nth-child(4n)::after { display: none; }
  .crivia-metodo__no span { padding: .95rem .8rem; }
  .crivia-metodo__in--2 .crivia-metodo__cab { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 21rem); column-gap: 2rem; }
  .crivia-metodo__in--2 .crivia-sobre__eyebrow { grid-column: 1; }
  .crivia-metodo__in--2 .crivia-sobre__titulo { grid-column: 1; grid-row: 2; }
  .crivia-metodo__in--2 .crivia-sobre__lead { grid-column: 2; grid-row: 2; align-self: end; padding-bottom: .6rem; }
  .crivia-metodo__in--3 { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 22rem); grid-template-areas: "cab apoio" "ordem ordem"; column-gap: 2rem; row-gap: 2.2rem; align-content: center; }
  .crivia-metodo__in--3 .crivia-metodo__cab { grid-area: cab; }
  .crivia-metodo__in--3 .crivia-metodo__apoio { grid-area: apoio; align-self: end; margin: 0; padding-bottom: .6rem; }
  .crivia-metodo__in--3 .crivia-metodo__ordem { grid-area: ordem; margin: 0; }
}
@media (min-width: 64rem) {
  .crivia-metodo__in--1 { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr); column-gap: 4rem; align-items: center; padding: 4.6rem 3rem 1.6rem; }
  .crivia-metodo__in { padding: 5rem 3rem 1.6rem; }
  .crivia-metodo__in--3 .crivia-metodo__ordem { padding: 1.5rem 1.6rem; }
  .crivia-metodo__in--2 .crivia-metodo__cab { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 31rem); column-gap: 4rem; }
  .crivia-metodo__in--2 .crivia-sobre__eyebrow { grid-column: 1; }
  .crivia-metodo__in--2 .crivia-sobre__titulo { grid-column: 1; grid-row: 2; }
  .crivia-metodo__in--2 .crivia-sobre__lead { grid-column: 2; grid-row: 2; align-self: end; padding-bottom: .6rem; }
  .crivia-metodo__in--3 { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 31rem); grid-template-areas: "cab apoio" "ordem ordem"; column-gap: 4rem; row-gap: 2.2rem; align-content: center; }
  .crivia-metodo__in--3 .crivia-metodo__cab { grid-area: cab; }
  .crivia-metodo__in--3 .crivia-metodo__apoio { grid-area: apoio; align-self: end; margin: 0; padding-bottom: .6rem; }
  .crivia-metodo__in--3 .crivia-metodo__ordem { grid-area: ordem; margin: 0; }
}
@media (max-height: 760px) and (min-width: 64rem) {
  .crivia-metodo__in--1 .crivia-sobre__titulo { font-size: clamp(2.2rem, 4vw, 3.4rem); }
  .crivia-metodo__corpo { font-size: .9rem; line-height: 1.55; }
}
@media (prefers-reduced-motion: reduce) {
  .crivia-metodo .crivia-rev, .crivia-metodo .crivia-ln > span { transition: none; }
}
"""

CSS_SOBRE = r"""
/* ════ CRIVIA ════ dobra "Sobre" (forma da hero Lumina, cores CRIVIA) ════ */
.crivia-sobre { position: absolute; inset: 0; z-index: 12; overflow: hidden; opacity: 0; visibility: hidden; pointer-events: none;
  background: radial-gradient(90% 80% at 50% 45%, rgba(242,246,253,.94), rgba(236,243,252,.88)); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); font-family: "Geist", system-ui, sans-serif; color: #001D3D; will-change: opacity, transform; }
.crivia-sobre__rola { position: absolute; inset: 0; overflow-x: hidden; overflow-y: auto; scrollbar-width: thin; scrollbar-color: rgba(10,54,157,.3) transparent; }
.crivia-sobre__in { box-sizing: border-box; min-height: 100%; max-width: 80rem; margin: 0 auto; padding: 5rem 1.25rem 2.5rem;
  display: grid; grid-template-columns: minmax(0, 1fr); gap: 1.4rem; align-content: center; }
.crivia-sobre__cab { display: flex; flex-direction: column; gap: 1rem; }
.crivia-sobre__eixo { display: none; }

/* surgimento igual ao da hero: cada linha sobe devagar, saindo do desfoque, uma depois da outra (260 ms) */
.crivia-sobre .crivia-rev { opacity: 0; transform: translateY(70%); filter: blur(18px); transition: opacity .45s ease, transform .45s ease, filter .45s ease; }
.crivia-sobre .crivia-ln { display: block; overflow: hidden; padding: .04em .08em .34em 0; margin-bottom: -.22em; }
.crivia-sobre .crivia-ln > span { display: inline-block; opacity: 0; transform: translateY(100%); filter: blur(18px); transition: opacity .4s ease, transform .4s ease, filter .4s ease; }
.crivia-sobre.is-on .crivia-rev, .crivia-sobre.is-on .crivia-ln > span {
  opacity: 1; transform: none; filter: none; transition: opacity 1.5s cubic-bezier(.16,1,.3,1), transform 1.6s cubic-bezier(.16,1,.3,1), filter 1.5s cubic-bezier(.16,1,.3,1);
  transition-delay: calc(var(--i, 0) * 260ms + 120ms); }
.crivia-sobre .crivia-sobre__f { opacity: 0; transform: translateY(40%); filter: blur(14px); transition: opacity .4s ease, transform .4s ease, filter .4s ease; }
.crivia-sobre.is-on .crivia-sobre__f { opacity: 1; transform: none; filter: none;
  transition: opacity 1.3s cubic-bezier(.16,1,.3,1), transform 1.4s cubic-bezier(.16,1,.3,1), filter 1.3s cubic-bezier(.16,1,.3,1), background .4s ease;
  transition-delay: calc(var(--i, 0) * 200ms + 120ms), calc(var(--i, 0) * 200ms + 120ms), calc(var(--i, 0) * 200ms + 120ms), 0s; }

.crivia-sobre__eyebrow { display: inline-flex; align-items: center; gap: .65rem; font-size: .76rem; font-weight: 600; letter-spacing: .24em; text-transform: uppercase; color: #0A369D; }
.crivia-sobre__eyebrow i { width: 7px; height: 7px; border-radius: 50%; background: #F5B82E; box-shadow: 0 0 0 4px rgba(245,184,46,.25); }
.crivia-sobre__titulo { margin: .85rem 0 0; font-family: "Plus Jakarta Sans", system-ui, sans-serif; font-weight: 700; font-size: clamp(2.6rem, 5.6vw, 5rem);
  line-height: 1.03; letter-spacing: -.04em; }
.crivia-sobre .crivia-ln > span { padding: .06em .08em .3em 0; margin-bottom: -.3em; background-clip: text; -webkit-background-clip: text; color: transparent; -webkit-text-fill-color: transparent; }
.crivia-sobre .crivia-ln:nth-child(1) > span { background-image: linear-gradient(180deg, #2F6BFF 0%, #0A369D 100%); }
.crivia-sobre .crivia-ln:nth-child(2) > span { background-image: linear-gradient(180deg, #0A369D 0%, #001D3D 100%); }
.crivia-sobre__lead { margin: 0; max-width: 31rem; font-size: clamp(.95rem, 1.2vw, 1.075rem); line-height: 1.55; color: #2B4A6B; }

.crivia-sobre__bruno { box-sizing: border-box; padding: 1.1rem 1.3rem 1.15rem; border-radius: 1.25rem;
  background: rgba(255,255,255,.62); -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px);
  border: 1px solid rgba(10,54,157,.14); box-shadow: 0 1.4rem 2.8rem -1.6rem rgba(0,29,61,.38); }
.crivia-sobre__bruno-topo { display: flex; align-items: center; gap: .8rem; }
.crivia-sobre__mono { flex: none; width: 2.7rem; height: 2.7rem; border-radius: 50%; display: grid; place-items: center; font-family: "Plus Jakarta Sans", sans-serif;
  font-size: .85rem; font-weight: 700; letter-spacing: .02em; color: #fff; background: linear-gradient(145deg, #2F6BFF, #0A369D 70%, #001D3D);
  box-shadow: 0 .4rem 1rem -.3rem rgba(10,54,157,.65), inset 0 0 0 1px rgba(255,255,255,.25); }
.crivia-sobre__bruno-topo strong { display: block; font-size: 1rem; font-weight: 650; letter-spacing: -.01em; }
.crivia-sobre__bruno-topo span:not(.crivia-sobre__mono) { display: block; margin-top: .1rem; font-size: .74rem; color: #4B6585; }
.crivia-sobre__bruno-txt { margin: .85rem 0 0; font-size: .92rem; line-height: 1.55; color: #14305A; }
.crivia-sobre__bruno-cham { margin: .65rem 0 0; font-size: .86rem; font-weight: 650; color: #0A369D; }

.crivia-sobre__pilha { position: relative; margin-bottom: 1.25rem; }
.crivia-sobre__pilha::before, .crivia-sobre__pilha::after { content: ""; position: absolute; z-index: 0; height: 50%; border-radius: 1.2rem;
  background: linear-gradient(180deg, #0A369D, #001D3D); }
.crivia-sobre__pilha::before { left: 5%; right: 5%; bottom: -.6rem; opacity: .5; }
.crivia-sobre__pilha::after { left: 10%; right: 10%; bottom: -1.15rem; opacity: .26; }
.crivia-sobre__video { position: relative; z-index: 1; width: 100%; aspect-ratio: 16 / 9; border-radius: 1.2rem; overflow: hidden; display: grid; place-items: center;
  background: radial-gradient(120% 90% at 20% 0%, #2F6BFF 0%, rgba(47,107,255,0) 55%), linear-gradient(150deg, #0A369D 0%, #07245F 55%, #001D3D 100%);
  border: 1px solid rgba(255,255,255,.2); box-shadow: 0 2rem 3.4rem -1.6rem rgba(0,29,61,.6); }
.crivia-sobre__video::before { content: ""; position: absolute; inset: 0; opacity: .5;
  background-image: radial-gradient(rgba(255,255,255,.22) 1px, transparent 1.4px); background-size: 22px 22px;
  -webkit-mask-image: radial-gradient(70% 70% at 50% 50%, #000, transparent); mask-image: radial-gradient(70% 70% at 50% 50%, #000, transparent); }
.crivia-sobre__video-el { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; background: #001D3D; }
.crivia-sobre__play { position: relative; z-index: 2; width: 4.6rem; height: 4.6rem; border-radius: 50%; display: grid; place-items: center; cursor: pointer; color: #fff;
  background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.6); -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
  box-shadow: 0 .8rem 2rem -.6rem rgba(0,13,40,.7); transition: transform .35s ease, background .35s ease; }
.crivia-sobre__play svg { width: 1.7rem; height: 1.7rem; margin-left: .2rem; }
.crivia-sobre__play:hover { transform: scale(1.07); background: rgba(255,255,255,.28); }
.crivia-sobre__play-anel { position: absolute; inset: -1px; border-radius: 50%; border: 1px solid rgba(255,255,255,.55); animation: crivia-play-anel 2.6s ease-out infinite; }
@keyframes crivia-play-anel { 0% { transform: scale(1); opacity: .8; } 100% { transform: scale(1.6); opacity: 0; } }
.crivia-sobre__legenda { position: absolute; left: 0; right: 0; bottom: 0; z-index: 2; display: flex; justify-content: flex-end; padding: 1.4rem 1rem .7rem;
  background: linear-gradient(180deg, rgba(0,13,40,0), rgba(0,13,40,.55)); color: #fff; font-size: .7rem; }
.crivia-sobre__legenda-breve { opacity: .75; font-size: .68rem; letter-spacing: .04em; white-space: nowrap; }

/* Fórmulas centrais: números grandes e legenda discreta, separados por fios de luz (como a lista de indicadores da Lumina) */
.crivia-sobre__formulas { padding: .7rem 1.3rem .2rem; border-radius: 1.25rem; background: linear-gradient(160deg, rgba(255,255,255,.92), rgba(238,245,255,.78)); -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px); border: 1px solid rgba(47,107,255,.24); box-shadow: 0 26px 60px -28px rgba(10,54,157,.45), 0 2px 0 rgba(255,255,255,.9) inset; }
.crivia-sobre__formulas ol { list-style: none; margin: 0; padding: 0; }
.crivia-sobre__rotulo { margin: 0 0 .25rem; font-size: .66rem; font-weight: 600; letter-spacing: .24em; text-transform: uppercase; color: #3F6A99; }
.crivia-sobre__seta { display: inline-block; margin: 0 .38em; color: #2F6BFF; font-weight: 700; }
.crivia-sobre__f { position: relative; display: flex; align-items: center; gap: 1rem; padding: .4rem .2rem .4rem 0; cursor: default; }
.crivia-sobre__f::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 1px; background: linear-gradient(90deg, rgba(10,54,157,.4), rgba(10,54,157,.12) 60%, rgba(10,54,157,0)); }
.crivia-sobre__f::after { content: ""; position: absolute; top: 0; left: 0; width: 18%; height: 1px; opacity: 0;
  background: linear-gradient(90deg, rgba(47,107,255,0), #2F6BFF, rgba(47,107,255,0)); animation: crivia-fio 7s ease-in-out infinite; animation-delay: calc(var(--i, 0) * .7s); }
@keyframes crivia-fio { 0%, 55% { left: -20%; opacity: 0; } 62% { opacity: 1; } 100% { left: 100%; opacity: 0; } }
.crivia-sobre__num { flex: none; width: 1.6rem; font-family: "Geist", monospace; font-size: .7rem; font-weight: 600; letter-spacing: .08em; color: #2F6BFF; }
.crivia-sobre__f-corpo { min-width: 0; transition: transform .45s cubic-bezier(.16,1,.3,1); }
.crivia-sobre__f strong { display: block; width: fit-content; font-family: "Plus Jakarta Sans", system-ui, sans-serif; font-size: clamp(1.25rem, 1.7vw, 1.6rem); font-weight: 700; line-height: 1.08; letter-spacing: -.035em;
  background: linear-gradient(100deg, #001D3D 0%, #0A369D 70%, #2F6BFF 100%); background-clip: text; -webkit-background-clip: text; color: transparent; -webkit-text-fill-color: transparent; }
.crivia-sobre__f p { margin: .2rem 0 0; font-size: .88rem; line-height: 1.36; color: #2F4A70; max-width: 38rem; transition: color .4s ease; }
.crivia-sobre__f:hover .crivia-sobre__f-corpo { transform: translateX(.45rem); }
.crivia-sobre__f:hover p { color: #14305A; }
.crivia-sobre__f:hover .crivia-sobre__num { color: #0A369D; }
.crivia-sobre__f:last-child::after { display: none; }
.crivia-sobre__f:last-child { border-bottom: 1px solid rgba(10,54,157,.2); }

@media (min-width: 48rem) {
  .crivia-sobre__in { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); column-gap: 2.5rem; row-gap: 1.6rem; padding: 5.25rem 2.5rem 2rem; }
  .crivia-sobre__cab { grid-column: 1 / -1; flex-direction: row; align-items: flex-end; justify-content: space-between; gap: 2.5rem; }
  .crivia-sobre__lead { padding-bottom: .5rem; }
  .crivia-sobre__formulas { grid-column: 1 / -1; }
  .crivia-sobre__formulas ol { display: grid; grid-template-columns: 1fr 1fr; column-gap: 2.5rem; }
  .crivia-sobre__f:last-child { border-bottom: 0; }
}
@media (min-width: 64rem) {
  .crivia-sobre__in { grid-template-columns: minmax(0, .78fr) minmax(0, 1.3fr); column-gap: 3rem; row-gap: 1.1rem; padding: 4.6rem 3rem .9rem; grid-template-areas: "cab cab" "video formulas" "bruno formulas"; align-content: center; }
  .crivia-sobre__cab { grid-area: cab; }
  .crivia-sobre__videobox { grid-area: video; }
  .crivia-sobre__bruno { grid-area: bruno; }
  .crivia-sobre__formulas { grid-area: formulas; grid-column: auto; }
  .crivia-sobre__formulas ol { display: block; }
  .crivia-sobre__f:last-child { border-bottom: 1px solid rgba(10,54,157,.2); }
  .crivia-sobre__eixo { display: block; position: absolute; z-index: 1; left: calc(3rem + (100% - 9rem) * .3750 + 1.5rem); top: 4.6rem; bottom: 0; width: 0; border-left: 1px dashed rgba(10,54,157,.2); pointer-events: none; }
  .crivia-sobre__eixo i { position: absolute; left: -5px; top: 0; width: 0; height: 0; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 7px solid #2F6BFF;
    filter: drop-shadow(0 0 6px rgba(47,107,255,.7)); animation: crivia-eixo 6.5s ease-in-out infinite; }
}
@keyframes crivia-eixo { 0% { top: 4%; opacity: 0; } 12% { opacity: 1; } 88% { opacity: 1; } 100% { top: 94%; opacity: 0; } }
@media (min-width: 64rem) and (max-height: 760px) {
  .crivia-sobre__in { padding-top: 4.4rem; padding-bottom: 1rem; row-gap: 1rem; }
  .crivia-sobre__titulo { font-size: clamp(2.4rem, 4.6vw, 3.6rem); }
  .crivia-sobre__bruno { padding: .85rem 1.1rem; }
  .crivia-sobre__bruno-txt { font-size: .84rem; margin-top: .6rem; }
  .crivia-sobre__f { padding-top: .55rem; padding-bottom: .55rem; }
  .crivia-sobre__f p { font-size: .74rem; line-height: 1.35; }
  .crivia-sobre__pilha { margin-bottom: .9rem; }
}
@media (prefers-reduced-motion: reduce) {
  .crivia-sobre .crivia-rev, .crivia-sobre .crivia-ln > span, .crivia-sobre .crivia-sobre__f { transition: none; }
  .crivia-sobre__play-anel, .crivia-sobre__f::after, .crivia-sobre__eixo i { animation: none; }
}
"""

PATCHES_SOBRE = [
    ("sobre:progresso", "  var cachedProgress = 0;\n",
     "  var CRIVIA_BASE_VH = 760;\n"
     "  var CRIVIA_SOBRE_EM = 0.63;\n"
     "  var CRIVIA_SOBRE_VH = 4;\n"
     "  var CRIVIA_METODO_VH = 2.4;\n"
     "  var CRIVIA_FIM_VH = 3;\n"
     "  var criviaS0 = (max) => CRIVIA_SOBRE_EM * (CRIVIA_BASE_VH / 100) * window.innerHeight;\n"
     "  var criviaLogico = (y, max) => {\n"
     "    const vh = window.innerHeight;\n"
     "    const hold = Math.round(vh * CRIVIA_SOBRE_VH);\n"
     "    const hold2 = Math.round(vh * CRIVIA_METODO_VH);\n"
     "    const tail = Math.round(vh * CRIVIA_FIM_VH);\n"
     "    window.__criviaHoldPx = hold;\n"
     "    window.__criviaMetodoPx = hold2;\n"
     "    const base = (CRIVIA_BASE_VH / 100) * vh;\n"
     "    const s0 = CRIVIA_SOBRE_EM * base;\n"
     "    if (y <= s0) return clamp01(y / base);\n"
     "    if (y <= s0 + hold) {\n"
     "      const t = (y - s0) / hold;\n"
     "      const b = t < 0.12 ? 0 : t < 0.3 ? (t - 0.12) / 0.18 : t < 0.62 ? 1 - (t - 0.3) / 0.32 : 0;\n"
     "      return CRIVIA_SOBRE_EM - 0.075 * b * b * (3 - 2 * b);\n"
     "    }\n"
     "    if (y <= s0 + hold + hold2) return CRIVIA_SOBRE_EM;\n"
     "    return clamp01(CRIVIA_SOBRE_EM + (1 - CRIVIA_SOBRE_EM) * (y - s0 - hold - hold2) / tail);\n"
     "  };\n"
     "  var criviaCatalogoFator = () => {\n"
     "    const max = document.documentElement.scrollHeight - window.innerHeight;\n"
     "    const hold = window.__criviaHoldPx || 0;\n"
     "    if (max <= 0 || !hold) return 1;\n"
     "    const t = (window.scrollY - criviaS0(max)) / hold;\n"
     "    return t <= 0.05 ? 1 : t >= 0.15 ? 0 : +(1 - (t - 0.05) / 0.1).toFixed(3);\n"
     "  };\n"
     "  var cachedProgress = 0;\n", 1),
    ("sobre:progresso-calc", "cachedProgress = max > 0 ? clamp01(window.scrollY / max) : 0;",
     "cachedProgress = max > 0 ? criviaLogico(window.scrollY, max) : 0;", 1),
    ("sobre:componentes", "  var HomeView = () => {", SOBRE_JS + "  var HomeView = () => {", 1),
    ("motores:componentes", "  var HomeView = () => {", MOTORES_JS + "  var HomeView = () => {", 1),
    ("motores:no-palco", "        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(ScrollFade, { appear: [0.34, 0.41]",
     "        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(ScrollFade, { appear: [0.14, 0.18], disappear: [0.30, 0.335], className: \"pointer-events-none absolute inset-0 z-10\", children: /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(MotoresOverlay, {}) }),\n"
     "        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(ScrollFade, { appear: [0.34, 0.41]", 1),
    ("sobre:espaco", "style: { height: `${sceneConfig.sequence.scrollVh}vh` } }",
     "style: { height: `calc(${CRIVIA_SOBRE_EM * CRIVIA_BASE_VH}vh + ${(CRIVIA_SOBRE_VH + CRIVIA_METODO_VH + CRIVIA_FIM_VH) * 100 + 100}vh)` } }", 1),
    ("sobre:no-palco", "        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(ScrollFade, { appear: [0.93, 0.98]",
     "        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(SobreOverlay, {}),\n"
     "        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(MetodoOverlay, {}),\n"
     "        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(ScrollFade, { appear: [0.88, 0.93]", 1),
    ("sobre:catalogo-surge", "(ScrollFade, { appear: [0.6, 0.67]", "(ScrollFade, { appear: [0.575, 0.615]", 1),
    ("sobre:ato-onda", "    wave: [0.61, 0.955]", "    wave: [0.58, 0.955]", 1),
    ("sobre:ato-final", "    tree: [0.94, 1]", "    tree: [0.962, 1]", 1),
    # entrada direta: fora da abertura (act "hero"), texto e itens aparecem prontos, sem animação de letras, palavras ou linhas
    ("direta:texto", "    const active = useActActive(act);\n    const layer = act === \"hero\" || act === \"hand\" ? {",
     "    const active = useActActive(act);\n    if (act !== \"hero\") return (0, import_jsx_runtime14.jsx)(tag, { className, children });\n    const layer = act === \"hero\" || act === \"hand\" ? {", 1),
    ("direta:item", "    const active = useActActive(act);\n    return /* @__PURE__ */ (0, import_jsx_runtime17.jsx)(\n      Inview,",
     "    const active = useActActive(act);\n    if (act !== \"hero\") return (0, import_jsx_runtime17.jsx)(tag, { className, ...rest, children });\n    return /* @__PURE__ */ (0, import_jsx_runtime17.jsx)(\n      Inview,", 1),
]

PATCHES_NAV = [
    ("nav:fale-conosco", """            children: CTA
          }
        )
      ] }),""", """            children: CTA
          }
        ),
        /* @__PURE__ */ (0, import_jsx_runtime12.jsx)("a", { href: "#", className: "crivia-nav-fale", children: "Fale conosco" })
      ] }),""", 1),
    ("nav:logo", "            BRAND,\n            /* @__PURE__ */ (0, import_jsx_runtime12.jsx)(\n              \"span\",",
     "            /* @__PURE__ */ (0, import_jsx_runtime12.jsx)(\"span\", { className: \"crivia-nav-logo\", children: \"CRIVIA\" }),\n            /* @__PURE__ */ (0, import_jsx_runtime12.jsx)(\n              \"span\",", 1),
    ("nav:logo-rotulo", "          href: \"/\",\n          className: \"flex items-center gap-[0.5rem] whitespace-nowrap md:absolute md:left-1/2 md:-translate-x-1/2\",",
     "          href: \"/\",\n          \"aria-label\": \"CRIVIA — voltar ao início\",\n          className: \"flex items-center gap-[0.5rem] whitespace-nowrap md:absolute md:left-1/2 md:-translate-x-1/2\",", 1),
    ("nav:fale-conosco-movel", "items: [...LEFT_NAV, ...RIGHT_NAV], cta: CTA", 'items: [...LEFT_NAV, ...RIGHT_NAV, "Fale conosco"], cta: CTA', 1),
]

CSS_NAV = r"""
/* ════ CRIVIA ════ cabeçalho: grupos ancorados nas bordas, marca ao centro, espaços homogêneos e botão "Fale conosco" ════ */
@media (min-width: 48rem) {
  header.fixed { display: grid !important; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); justify-content: normal !important; }
  header.fixed nav[aria-label="Primary"] { justify-self: start; }
  header.fixed nav[aria-label="Secondary"] { justify-self: end; }
  header.fixed nav[aria-label="Primary"], header.fixed nav[aria-label="Secondary"] { gap: clamp(.85rem, 1.8vw, 2.1rem) !important; align-items: center; }
  header.fixed nav a { font-size: clamp(.58rem, .86vw, .7rem) !important; letter-spacing: .07em !important; }
  header.fixed > a { position: static !important; transform: none !important; translate: none !important; flex: none; justify-self: center; }
  header.fixed > a > span[aria-hidden] { display: none !important; }
}
@media (min-width: 90rem) {
  header.fixed > a > span[aria-hidden] { display: block !important; }
}
header.fixed nav a.crivia-nav-fale { font-size: clamp(.58rem, .8vw, .72rem) !important; letter-spacing: .1em !important; }
.crivia-nav-fale { display: inline-flex; align-items: center; white-space: nowrap; padding: .42rem clamp(.75rem, 1.3vw, 1.05rem); border-radius: 9999px; font-size: .72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: #fff !important;
  background: linear-gradient(135deg, #0A369D, #2F6BFF); box-shadow: 0 6px 16px rgba(47,107,255,.32), inset 0 1px 0 rgba(255,255,255,.35); transition: transform .3s ease, filter .3s ease, box-shadow .3s ease; }
.crivia-nav-fale:hover, .crivia-nav-fale:focus-visible { transform: translateY(-1px) scale(1.04); filter: brightness(1.1); box-shadow: 0 10px 22px rgba(47,107,255,.42), inset 0 1px 0 rgba(255,255,255,.4); outline: none; opacity: 1 !important; }
"""

PATCHES_HERO_FUNDO = [
    # componentes novos entram antes de HomeView; o fundo vem ANTES da cena 3D (atrás de tudo)
    ("hero:componentes", "  var HomeView = () => {", JS_CRIVIA, 1),
    ("hero:fundo-atras", "        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(ParticleScene, {}),\n"
                         "        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(HeroLights, {}),\n",
     "        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(CriviaBackdrop, {}),\n"
     "        /* @__PURE__ */ (0, import_jsx_runtime26.jsx)(ParticleScene, {}),\n", 1),
    # a cena 3D passa a "multiplicar" sobre o fundo: o fundo aparece por trás e o C se destaca
    ("hero:tela-transparente",
     'className: "h-full w-full transform-gpu backface-hidden will-change-transform",\n        "aria-hidden": "true"',
     'className: "crivia-canvas h-full w-full transform-gpu backface-hidden will-change-transform",\n        "aria-hidden": "true"', 1),
]
BOTOES_INI = ('            /* @__PURE__ */ (0, import_jsx_runtime18.jsx)(RevealItem, { act: "hero", index: 0, count: 2, delay: 1600, '
              'className: "flex-1 md:flex-none", children: /* @__PURE__ */ (0, import_jsx_runtime18.jsx)(\n')
BOTOES_FIM = "\n          ] })\n        ] })\n      ] })\n    ] });\n  };\n\n  // orig/src/components/common/hero-overlay/hand-overlay.tsx"
BOTOES_NOVOS = (
    '            /* @__PURE__ */ (0, import_jsx_runtime18.jsx)(RevealItem, { act: "hero", index: 0, count: 2, delay: 2300, className: "flex-none", '
    'children: /* @__PURE__ */ (0, import_jsx_runtime18.jsx)(CriviaCtaPrimary, { onClick: () => CRIVIA_ABRIR_CENARIO("hero"), children: "Apresentar meu cenário" }) }),\n'
    '            /* @__PURE__ */ (0, import_jsx_runtime18.jsx)(RevealItem, { act: "hero", index: 1, count: 2, delay: 2300, className: "flex-none", '
    'children: /* @__PURE__ */ (0, import_jsx_runtime18.jsx)(CriviaCtaSecondary, { onClick: CRIVIA_IR_METODO, children: "Conhecer o método" }) })')

# Hero: bloco do título. Frase 1 = "CRIVIA / ENGENHARIA CONSULTIVA"; frase 2 = "Engenharia para Decisão".
# Substitui o título do modelo (esquerda) e o texto grande da direita; cada frase sobe e escurece em sequência.
HERO_BLOCO_INI = ('      /* @__PURE__ */ (0, import_jsx_runtime18.jsxs)("div", { className: "absolute inset-x-[1.25rem] top-[22%]')
HERO_BLOCO_FIM = ('      /* @__PURE__ */ (0, import_jsx_runtime18.jsxs)("footer", { className: "absolute inset-x-0 bottom-0')
HERO_BLOCO_NOVO = r"""      /* @__PURE__ */ (0, import_jsx_runtime18.jsxs)("div", { className: "absolute inset-x-[1.25rem] top-[22%] flex flex-col items-center gap-[0.25rem] md:inset-x-auto md:left-[1.875rem] md:top-1/2 md:block md:-translate-y-1/2 crivia-hero-title", children: [
        /* @__PURE__ */ (0, import_jsx_runtime18.jsx)(RevealText, { act: "hero", tag: "p", variant: "heading", delayIn: 200, className: "crivia-hero-wordmark", children: "CRIVIA" }),
        /* @__PURE__ */ (0, import_jsx_runtime18.jsx)(RevealText, { act: "hero", tag: "p", variant: "heading", delayIn: 800, className: "crivia-hero-eyebrow", children: "Engenharia Consultiva" })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime18.jsx)("div", { className: "absolute right-[1.875rem] top-1/2 hidden -translate-y-1/2 md:block crivia-hero-right", children: /* @__PURE__ */ (0, import_jsx_runtime18.jsx)(RevealText, { act: "hero", tag: "p", variant: "heading", delayIn: 1900, className: "crivia-hero-tagline crivia-hero-tagline--right", children: ["Tornando o ", /* @__PURE__ */ (0, import_jsx_runtime18.jsx)("span", { className: "crivia-tg-oco", children: "impossível" }), " em possível."] }) }),
"""

FRASE2_INI = '        /* @__PURE__ */ (0, import_jsx_runtime18.jsx)("ul", { className: "grid grid-cols-2 gap-[0.5rem] md:w-fit", children: TAGS.map('
FRASE2_FIM = '        /* @__PURE__ */ (0, import_jsx_runtime18.jsx)("div", { className: "my-[1.25rem] h-px bg-overlay-line md:my-[1.875rem]" }),'
FRASE2_NOVA = r"""        /* @__PURE__ */ (0, import_jsx_runtime18.jsx)("div", { className: "crivia-hero-frase2", children: /* @__PURE__ */ (0, import_jsx_runtime18.jsx)(RevealText, { act: "hero", tag: "p", variant: "heading", delayIn: 1400, className: "crivia-hero-tagline crivia-hero-tagline--rodape", children: "Engenharia para Decisão" }) }),
"""

# ── HTML da página (assets/overview/index.html) ─────────────────────────────
PATCHES_HTML = [
    ("html:faixa", "</head>", '<script>(function(){var f=function(){var w=innerWidth,h=innerHeight;if(!(w>0&&h>0))return 0;return (w<=768?1:w<=1180?2:3)*100+Math.round(w/h*2)},c=f(),t,k="criviaReload";addEventListener("resize",function(){clearTimeout(t);t=setTimeout(function(){var n=f();if(!n||n===c)return;try{var l=+sessionStorage.getItem(k)||0;if(Date.now()-l<3000)return;sessionStorage.setItem(k,String(Date.now()))}catch(e){}location.reload()},500)})})();</script>'+"</head>", 1),
    ("html:lang", '<html lang="en">', '<html lang="pt-BR">', 1),
    ("html:titulo", "<title>Auralis Design System</title>",
     "<title>CRIVIA Engenharia Consultiva — Engenharia para Decisão</title>", 1),
    ("html:descricao", '<meta name="description" content="Auralis Design System">',
     '<meta name="description" content="CRIVIA Engenharia Consultiva. Engenharia independente para decisões críticas: vamos à realidade, encontramos a causa por trás do sintoma e entregamos a quem decide uma solução que cabe na realidade.">', 1),
    # no celular o título cai sobre o C escuro: halo claro atrás das letras para manter a leitura
    ("html:halo-mobile", "p { justify-content: center; } }",
     "p { justify-content: center; text-shadow: 0 0 14px #F4FAFD, 0 0 5px #F4FAFD, 0 0 2px #F4FAFD; } }", 1),
    ("html:cor-tema", '<meta name="theme-color" content="#000000">', '<meta name="theme-color" content="#F4FAFD">', 1),
    # no catálogo, a barra da própria página continua visível (o catálogo CRIVIA não duplica o menu)
    ("html:menu-visivel", "  .ds-embed main > div.fixed > header { display: none !important; }\n", "", 1),
]
RAIZ_INI = '<div id="root" style="display: contents">'
RAIZ_FIM = '\n  <script src="assets/js/embedded-assets.js"></script>'


# ════════════════════════════════════════════════════════════════════════════
#  PATCHES: utilitários
# ════════════════════════════════════════════════════════════════════════════
def aplicar(texto, patches, arquivo):
    for rotulo, antigo, novo, esperado in patches:
        n = texto.count(antigo)
        if n != esperado:
            raise ErroDePatch(
                f"[{arquivo}] âncora '{rotulo}' encontrada {n}x (esperado {esperado}x):\n    {antigo[:120]!r}")
        texto = texto.replace(antigo, novo)
    return texto


def trocar_trecho(texto, ini, fim, novo, rotulo):
    """Troca [ini, fim) por `novo`; `ini` e `fim` precisam existir exatamente uma vez."""
    for nome, ancora in (("início", ini), ("fim", fim)):
        n = texto.count(ancora)
        if n != 1:
            raise ErroDePatch(f"[app.js] âncora '{rotulo}' ({nome}) encontrada {n}x (esperado 1x): {ancora[:100]!r}")
    i, j = texto.index(ini), texto.index(fim)
    if j <= i:
        raise ErroDePatch(f"[app.js] âncora '{rotulo}': fim antes do início")
    return texto[:i] + novo + texto[j:]


def trocar_apos(texto, ancora_regiao, antigo, novo, rotulo, janela=6000):
    """Troca a primeira ocorrência de `antigo` dentro de `janela` caracteres após `ancora_regiao`."""
    if texto.count(ancora_regiao) != 1:
        raise ErroDePatch(f"[app.js] região '{rotulo}' não é única: {ancora_regiao!r}")
    base = texto.index(ancora_regiao)
    k = texto.find(antigo, base, base + janela)
    if k < 0:
        raise ErroDePatch(f"[app.js] âncora '{rotulo}' não encontrada após a região")
    return texto[:k] + novo + texto[k + len(antigo):]


# ════════════════════════════════════════════════════════════════════════════
#  GEOMETRIA: amostragem de superfícies (determinística, só biblioteca padrão)
# ════════════════════════════════════════════════════════════════════════════
def v_sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def v_add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def v_mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def v_len(a): return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
def v_cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def v_unit(a):
    n = v_len(a) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


class Item:
    """Um pedaço de geometria: peso relativo, função de amostragem e etiqueta (0/1/2)."""
    __slots__ = ("peso", "fn", "tag")

    def __init__(self, peso, fn, tag=0):
        self.peso, self.fn, self.tag = peso, fn, tag


def paralelogramo(o, u, v, mult=1.0):
    area = v_len(v_cross(u, v))
    return Item(area * mult,
                lambda r: v_add(o, v_add(v_mul(u, r.random()), v_mul(v, r.random()))))


def triangulo(a, b, c, mult=1.0):
    ab, ac = v_sub(b, a), v_sub(c, a)

    def fn(r):
        s, t = r.random(), r.random()
        if s + t > 1:
            s, t = 1 - s, 1 - t
        return v_add(a, v_add(v_mul(ab, s), v_mul(ac, t)))
    return Item(0.5 * v_len(v_cross(ab, ac)) * mult, fn)


def caixa(cx, cy, cz, sx, sy, sz, mult=1.0):
    """Caixa por faces (topo, frente, fundo e laterais; sem a base). Retorna lista de Items."""
    x0, x1, y0, y1, z0, z1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2
    return [
        paralelogramo((x0, y1, z0), (sx, 0, 0), (0, 0, sz), mult),            # topo
        paralelogramo((x0, y0, z1), (sx, 0, 0), (0, sy, 0), mult),            # frente
        paralelogramo((x0, y0, z0), (sx, 0, 0), (0, sy, 0), mult),            # fundo
        paralelogramo((x0, y0, z0), (0, 0, sz), (0, sy, 0), mult),            # esquerda
        paralelogramo((x1, y0, z0), (0, 0, sz), (0, sy, 0), mult),            # direita
    ]


def tronco(cx, cz, y0, y1, r0, r1, mult=1.0):
    """Superfície lateral de um tronco de cone (cilindro se r0 == r1)."""
    s = math.hypot(y1 - y0, r0 - r1)
    area = math.pi * (r0 + r1) * s

    def fn(r):
        u = r.random()
        a = (r1 - r0) / 2.0
        if abs(a) > 1e-9:
            t = (-r0 + math.sqrt(max(0.0, r0 * r0 + 4 * a * u * (r0 + r1) / 2.0))) / (2 * a)
        else:
            t = u
        rad = r0 + (r1 - r0) * t
        ang = r.random() * 2 * math.pi
        return (cx + rad * math.cos(ang), y0 + (y1 - y0) * t, cz + rad * math.sin(ang))
    return Item(area * mult, fn)


def disco(cx, cz, y, raio, mult=1.0):
    def fn(r):
        rad = raio * math.sqrt(r.random())
        ang = r.random() * 2 * math.pi
        return (cx + rad * math.cos(ang), y, cz + rad * math.sin(ang))
    return Item(math.pi * raio * raio * mult, fn)


def cone(cx, cz, y0, raio, altura, mult=1.0):
    return tronco(cx, cz, y0, y0 + altura, raio, 0.0, mult)


def tubo(p0, p1, raio, peso, tag=0):
    """Tubo fino entre dois pontos (pontos sobre a superfície lateral)."""
    d = v_sub(p1, p0)
    eixo = v_unit(d)
    ref = (0, 1, 0) if abs(eixo[1]) < 0.95 else (1, 0, 0)
    a = v_unit(v_cross(eixo, ref))
    b = v_cross(eixo, a)

    def fn(r):
        t, ang = r.random(), r.random() * 2 * math.pi
        c = v_add(p0, v_mul(d, t))
        return v_add(c, v_add(v_mul(a, raio * math.cos(ang)), v_mul(b, raio * math.sin(ang))))
    return Item(peso, fn, tag)


def grupo_tubos(segmentos, raio, peso_total):
    """Reparte `peso_total` entre segmentos proporcionalmente ao comprimento."""
    comp = [v_len(v_sub(q, p)) for p, q in segmentos]
    soma = sum(comp) or 1.0
    return [tubo(p, q, raio, peso_total * c / soma) for (p, q), c in zip(segmentos, comp)]


def esfera_casca(c, raio, peso, tag=0):
    def fn(r):
        while True:
            x, y, z = r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1)
            n = math.sqrt(x * x + y * y + z * z)
            if n > 1e-9:
                return (c[0] + raio * x / n, c[1] + raio * y / n, c[2] + raio * z / n)
    return Item(peso, fn, tag)


def esfera_cheia(c, raio, peso, tag=0):
    def fn(r):
        x, y, z = r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1)
        n = math.sqrt(x * x + y * y + z * z) or 1.0
        k = raio * r.random() ** (1 / 3) / n
        return (c[0] + x * k, c[1] + y * k, c[2] + z * k)
    return Item(peso, fn, tag)


def caixa_orientada(p0, p1, largura, altura, mult=1.0):
    """Viga/esteira inclinada: 4 faces longas entre p0 e p1."""
    d = v_sub(p1, p0)
    eixo = v_unit(d)
    lado = v_unit(v_cross(eixo, (0, 1, 0)))
    cima = v_cross(lado, eixo)
    hw, hh = largura / 2, altura / 2

    def canto(sw, sh):
        return v_add(p0, v_add(v_mul(lado, sw * hw), v_mul(cima, sh * hh)))
    itens = []
    for (a, b), (c, e) in (((-1, 1), (1, 1)), ((-1, -1), (1, -1)), ((-1, -1), (-1, 1)), ((1, -1), (1, 1))):
        o = canto(a, b)
        u = v_sub(canto(c, e), o)
        itens.append(paralelogramo(o, u, d, mult))
    return itens


def amostrar(itens, n, rng, jitter=0.012):
    """n pontos distribuídos por peso; devolve (pontos, etiquetas)."""
    acum, total = [], 0.0
    for it in itens:
        total += it.peso
        acum.append(total)
    pts, tags = [], bytearray()
    for _ in range(n):
        k = min(bisect.bisect_left(acum, rng.random() * total), len(itens) - 1)
        x, y, z = itens[k].fn(rng)
        pts.append((x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter), z + rng.uniform(-jitter, jitter)))
        tags.append(itens[k].tag)
    return pts, bytes(tags)


def normalizar(pts):
    """Altura = 2 (y de -1 a 1), Y para cima, centrado em x e z."""
    ys = [p[1] for p in pts]
    k = 2.0 / (max(ys) - min(ys))
    cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
    cz = (min(p[2] for p in pts) + max(p[2] for p in pts)) / 2
    y0 = min(ys)
    return [((x - cx) * k, (y - y0) * k - 1.0, (z - cz) * k) for x, y, z in pts]


# ── Quantização no formato do modelo (bin_u16, xyz intercalado, little-endian) ──
def quantizar(pts):
    mins = [min(p[i] for p in pts) for i in range(3)]
    maxs = [max(p[i] for p in pts) for i in range(3)]
    escala = [max(maxs[i] - mins[i], 1e-9) for i in range(3)]
    buf = bytearray()
    for p in pts:
        for i in range(3):
            q = int(round((p[i] - mins[i]) / escala[i] * 65535))
            buf += struct.pack("<H", max(0, min(65535, q)))
    manifesto = {"objects": [{
        "name": "points", "file": "points.bin", "format": "bin_u16", "count": len(pts), "up_axis": "Y",
        "decode_offset": mins, "decode_scale": escala}]}
    return bytes(buf), json.dumps(manifesto, indent=2)


def entrada_embutida(bin_, manifesto, pasta, extra=None):
    d = {
        f"/assets/{pasta}/points.manifest.json": {"type": "application/json", "text": manifesto},
        f"/assets/{pasta}/points.bin": {"type": "application/octet-stream", "base64": base64.b64encode(bin_).decode("ascii")},
    }
    if extra:
        d.update(extra)
    return d


# ════════════════════════════════════════════════════════════════════════════
#  GERADORES DE FORMAS
# ════════════════════════════════════════════════════════════════════════════
def gerar_c():
    """O "C" 3D é gerado no navegador (createGlyphParticles, GLIFO_C). Aqui, só as marcas SVG."""
    logo = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="CRIVIA">\n'
            '  <!-- Monograma da CRIVIA: o "C" do glifo 3D (arco de 270°, abertura à direita) achatado.\n'
            '       Campo azul-marinho, marca clara, ponto âmbar (o decisor). Sem gradiente: legível em 16 px. -->\n'
            '  <rect width="512" height="512" fill="#001D3D" />\n'
            '  <path d="M362 150 A150 150 0 1 0 362 362" fill="none" stroke="#EAF6FB" stroke-width="66" stroke-linecap="round" />\n'
            '  <circle cx="276" cy="256" r="26" fill="#F59E0B" />\n'
            '</svg>\n')
    favicon = ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
               '<rect width="64" height="64" fill="#001D3D"/>'
               '<path d="M45.4 18.6 A19 19 0 1 0 45.4 45.4" fill="none" stroke="#EAF6FB" stroke-width="9" stroke-linecap="round"/>'
               '<circle cx="34" cy="32" r="3.4" fill="#F59E0B"/></svg>\n')
    return logo, favicon


def gerar_industria():
    """Complexo industrial em traço técnico (linhas de contas): nítido, simétrico e sóbrio. Galpão com treliças,
    três chaminés, tanques, silo, pipe-rack e esteira. Devolve (pontos normalizados, etiquetas):
    0 azul-marinho (estrutura), 1 dourado (pontos de decisão), 2 royal (tubulações e esteira), 3 ciano (faixas de dados)."""
    rng = random.Random(SEMENTE_INDUSTRIA)
    it = []
    NAVY, OURO, ROYAL, CIANO = 0, 1, 2, 3

    def fio(a, b, mult=1.0, tag=NAVY, raio=0.016):
        it.append(tubo(a, b, raio, v_len(v_sub(b, a)) * mult, tag))

    def anel(cx, cy, cz, r, mult=1.0, tag=NAVY, raio=0.016):
        def fn(rr):
            a = rr.random() * 2 * math.pi
            u = math.sqrt(rr.random()) * raio
            ang = rr.random() * 2 * math.pi
            rad = r + u * math.cos(ang)
            return (cx + rad * math.cos(a), cy + u * math.sin(ang), cz + rad * math.sin(a))
        it.append(Item(2 * math.pi * r * mult, fn, tag))

    def no(c, r=0.14, peso=9.0, tag=OURO):
        it.append(esfera_cheia(c, r, peso, tag))

    def caixa_arestas(x0, x1, y0, y1, z0, z1, mult=1.0, tag=NAVY):
        for y in (y0, y1):
            for z in (z0, z1):
                fio((x0, y, z), (x1, y, z), mult, tag)
            for x in (x0, x1):
                fio((x, y, z0), (x, y, z1), mult, tag)
        for x in (x0, x1):
            for z in (z0, z1):
                fio((x, y0, z), (x, y1, z), mult, tag)

    def cilindro(cx, cz, r, y0, y1, aneis, tags_aneis=None):
        for k in range(4):
            a = k * math.pi / 2
            px, pz = cx + r * math.cos(a), cz + r * math.sin(a)
            fio((px, y0, pz), (px, y1, pz))
        for i, y in enumerate(aneis):
            tg = tags_aneis[i] if tags_aneis else NAVY
            anel(cx, y, cz, r, 1.35 if tg != NAVY else 1.0, tg)

    def cone_linhas(cx, cz, y0, r, h):
        for k in range(8):
            a = k * math.pi / 4
            fio((cx + r * math.cos(a), y0, cz + r * math.sin(a)), (cx, y0 + h, cz), 0.8)

    def chamine(cx, cz, h, r0, r1):
        for k in range(4):
            a = k * math.pi / 2
            fio((cx + r0 * math.cos(a), 0.0, cz + r0 * math.sin(a)), (cx + r1 * math.cos(a), h, cz + r1 * math.sin(a)), 1.1)
        for f in (0.0, 0.2, 0.4, 0.6, 0.8):
            anel(cx, h * f, cz, r0 + (r1 - r0) * f)
        anel(cx, h, cz, r1, 1.7, OURO)
        anel(cx, h - 0.2, cz, r1 * 1.0, 1.2, OURO)

    # refinaria em traço fino (miniatura da foto): torre de estrutura azul à frente com reator dourado,
    # chaminé à esquerda, dois tanques à direita e pipe-rack longo no primeiro plano. Uma só composição, sem espelhamento.
    def poli(pts, mult=1.0, tag=NAVY, fechar=False):
        n = len(pts)
        for i in range(n if fechar else n - 1):
            fio(pts[i], pts[(i + 1) % n], mult, tag)

    def circulo(cx, cy, cz, r, plano, tag=NAVY, seg=28):
        pts = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            if plano == "xy":
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a), cz))
            else:
                pts.append((cx, cy + r * math.sin(a), cz + r * math.cos(a)))
        poli(pts, 1.0, tag, True)

    def laco(x0, x1, y, z0, z1, mult=1.0, tag=NAVY):
        poli([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], mult, tag, True)

    # chão e base de concreto
    fio((-11.5, 0.0, 2.4), (15.5, 0.0, 2.4), 1.0, NAVY)
    fio((-11.5, 0.0, -1.6), (15.5, 0.0, -1.6), 0.8, NAVY)
    fio((-11.5, 0.35, 2.4), (15.5, 0.35, 2.4), 0.8, NAVY)

    # torre central: estrutura azul em cinco andares, guarda-corpo dourado, vaso interno e reator dourado
    tx0, tx1, tz0, tz1, topo = -1.8, 2.2, -1.2, 1.2, 14.0
    andares = [0.0, 2.8, 5.6, 8.4, 11.2, 14.0]
    for x in (tx0, tx1):
        for z in (tz0, tz1):
            fio((x, 0.0, z), (x, topo, z), 1.2, ROYAL)
    for y in andares:
        laco(tx0, tx1, y, tz0, tz1, 0.9, ROYAL)
    for y in andares[1:]:
        laco(tx0 - 0.35, tx1 + 0.35, y + 0.45, tz0 - 0.35, tz1 + 0.35, 0.8, OURO)
    for i in range(5):
        y0, y1 = andares[i], andares[i + 1]
        if i % 2 == 0:
            fio((tx0, y0, tz1), (tx1, y1, tz1), 0.8, ROYAL)
            fio((tx1, y0, tz1), (tx0, y1, tz1), 0.8, ROYAL)
        else:
            fio((tx1, y0, tz1), (tx1, y1, tz0), 0.8, ROYAL)
            fio((tx1, y0, tz0), (tx1, y1, tz1), 0.8, ROYAL)
    cilindro(0.2, 0.0, 0.75, 0.4, 13.4, [0.4, 3.0, 5.6, 8.2, 10.8, 13.4])
    circulo(0.2, 5.6, 0.0, 0.95, "xy", OURO)
    circulo(0.2, 5.6, 0.0, 0.95, "zy", OURO)
    no((0.2, 5.6, 0.0), 0.42, 20.0)
    poli([(0.2, topo, 0.0), (0.2, 15.4, 0.0), (0.7, 15.9, 0.0), (1.7, 15.9, 0.0), (2.2, 15.4, 0.0), (2.2, topo, 0.0)], 1.2, NAVY)
    no((0.2, 15.4, 0.0), 0.12, 4.0)

    # chaminé à esquerda, com plataforma dourada
    chamine(-6.5, 0.0, 10.8, 0.55, 0.38)
    anel(-6.5, 6.6, 0.0, 0.72, 1.4, OURO)

    # tanques à direita (faixas em ciano) com guarda-corpo, escada e luminárias douradas
    cilindro(8.2, 0.0, 2.0, 0.0, 6.8, [0.0, 1.7, 3.4, 5.1, 6.8], [NAVY, CIANO, CIANO, CIANO, NAVY])
    anel(8.2, 7.3, 0.0, 2.15, 1.5, OURO)
    cilindro(12.9, 0.0, 1.45, 0.0, 5.0, [0.0, 1.25, 2.5, 3.75, 5.0], [NAVY, CIANO, CIANO, CIANO, NAVY])
    anel(12.9, 5.4, 0.0, 1.58, 1.4, OURO)
    fio((10.0, 0.0, 1.3), (11.4, 5.2, 1.0), 1.0, OURO)
    fio((6.2, 0.0, 0.8), (6.2, 7.0, 0.8), 1.0, OURO)
    no((8.2, 7.9, 0.0), 0.15, 5.0)
    no((12.9, 5.95, 0.0), 0.13, 4.0)

    # vasos: dois verticais, um à esquerda e um junto da torre, e um tambor horizontal em primeiro plano
    cilindro(-9.0, 0.0, 0.6, 0.0, 3.4, [0.0, 1.1, 2.3, 3.4], [NAVY, CIANO, CIANO, NAVY])
    cilindro(4.4, 0.8, 0.65, 0.0, 4.4, [0.0, 1.4, 2.9, 4.4], [NAVY, CIANO, CIANO, NAVY])
    fio((1.6, 1.8, 1.4), (5.6, 1.8, 1.4), 1.1, NAVY)
    fio((1.6, 0.6, 1.4), (5.6, 0.6, 1.4), 1.1, NAVY)
    circulo(1.6, 1.2, 1.4, 0.6, "zy", CIANO)
    circulo(5.6, 1.2, 1.4, 0.6, "zy", CIANO)
    circulo(3.6, 1.2, 1.4, 0.6, "zy", CIANO)

    # pipe-rack longo no primeiro plano: pilares azuis, vigas, contraventos e dois tubos
    zr = 1.9
    px = [-10.5 + 2.5 * i for i in range(9)]
    for x in px:
        fio((x, 0.0, zr), (x, 2.7, zr), 1.0, ROYAL)
    fio((px[0], 2.7, zr), (px[-1], 2.7, zr), 1.0, ROYAL)
    fio((px[0], 1.4, zr), (px[-1], 1.4, zr), 0.8, ROYAL)
    for i in (0, 2, 5):
        fio((px[i], 0.0, zr), (px[i + 1], 2.7, zr), 0.8, ROYAL)
        fio((px[i + 1], 0.0, zr), (px[i], 2.7, zr), 0.8, ROYAL)
    fio((px[0] - 0.3, 3.15, zr), (px[-1] - 1.4, 3.15, zr), 1.6, NAVY)
    fio((px[0] - 0.3, 3.55, zr), (px[-1] - 1.4, 3.55, zr), 1.6, NAVY)
    fio((px[-1] - 1.4, 3.15, zr), (px[-1] - 1.4, 0.4, zr), 1.0, NAVY)
    fio((px[0], 0.55, zr + 0.45), (px[-1], 0.55, zr + 0.45), 0.9, OURO)
    pts, tags = amostrar(it, N_INDUSTRIA, rng, jitter=0.006)
    return normalizar(pts), tags


def gerar_obra_circuito():
    """Obra em construção + malha de nós ligados a um núcleo âmbar (IA aplicada aos processos).
    Devolve (pontos normalizados, etiquetas): 0 comum, 1 núcleo âmbar, 2 conta ciano."""
    rng = random.Random(SEMENTE_OBRA)
    it = []
    NIVEIS = [0.3 + 1.25 * k for k in range(5)]          # cotas das lajes
    COLX, COLZ = (-2.6, -0.87, 0.87, 2.6), (-1.6, 1.6)
    NUCLEO = (0.0, 3.4, 0.0)

    # 1. base e fundação: estacas, laje e linhas de projeto sobrepostas
    for x in (-2.4, 0.0, 2.4):
        for z in (-1.4, 0.0, 1.4):
            it.append(tubo((x, -0.9, z), (x, 0.0, z), 0.17, 70))
    it += caixa(0, 0.15, 0, 6.0, 0.3, 4.0, mult=60)
    linhas = [((-4.4, 0.0, z), (4.4, 0.0, z)) for z in (-2.9, -1.6, 0.0, 1.6, 2.9)] + \
             [((x, 0.0, -3.1), (x, 0.0, 3.1)) for x in (-3.6, -2.6, 0.0, 2.6, 3.6)]
    it += grupo_tubos(linhas, 0.012, 1400)

    # 2. estrutura em pavimentos: pilares, vigas (lajes em quadro) e anéis de nós
    for k in range(4):
        for x in COLX:
            for z in COLZ:
                it.append(tubo((x, NIVEIS[k], z), (x, NIVEIS[k + 1], z), 0.095, 52))
    for y in NIVEIS[:-1]:
        per = [((-2.9, y, -1.9), (2.9, y, -1.9)), ((-2.9, y, 1.9), (2.9, y, 1.9)),
               ((-2.9, y, -1.9), (-2.9, y, 1.9)), ((2.9, y, -1.9), (2.9, y, 1.9))]
        mid = [((x, y, -1.9), (x, y, 1.9)) for x in (-1.45, 0.0, 1.45)] + [((-2.9, y, 0.0), (2.9, y, 0.0))]
        it += grupo_tubos(per, 0.06, 760)
        it += grupo_tubos(mid, 0.045, 460)
    # arranques de ferragem acima da última laje (obra em andamento)
    for x, z in ((-2.6, -1.6), (2.6, 1.6), (-0.87, 1.6)):
        it.append(tubo((x, NIVEIS[4], z), (x, NIVEIS[4] + 0.75, z), 0.05, 26))

    # camada de IA: anel de nós por pavimento, filamentos entre nós e de cada nó ao núcleo
    n_nos = 10
    for k in range(1, 5):
        y = NIVEIS[k] + 0.06
        nos = []
        for i in range(n_nos):
            a = 2 * math.pi * (i + 0.5 * (k % 2)) / n_nos
            nos.append((2.35 * math.cos(a), y, 1.45 * math.sin(a)))
        for i, n in enumerate(nos):
            it.append(esfera_cheia(n, 0.15, 56))
            it.append(tubo(n, nos[(i + 1) % n_nos], 0.014, 54))        # aresta do anel
            it.append(tubo(n, NUCLEO, 0.014, 150))                     # convergência para o decisor

    # 3. grua ao lado, com nó pendente (ponto de verificação)
    cx = 4.7
    cantos = [(cx - 0.3, 0.3, -0.3), (cx + 0.3, 0.3, -0.3), (cx - 0.3, 0.3, 0.3), (cx + 0.3, 0.3, 0.3)]
    topo = 7.8
    for p in cantos:
        it.append(tubo(p, (p[0], topo, p[2]), 0.07, 190))
    diag = []
    y = 0.3
    while y + 0.6 <= topo:
        diag.append(((cx - 0.3, y, 0.3), (cx + 0.3, y + 0.6, 0.3)))
        diag.append(((cx + 0.3, y, -0.3), (cx - 0.3, y + 0.6, -0.3)))
        diag.append(((cx - 0.3, y, -0.3), (cx - 0.3, y + 0.6, 0.3)))
        y += 0.6
    it += grupo_tubos(diag, 0.03, 1900)
    lanca_a, lanca_b = (-2.4, 8.2, 0.0), (7.4, 8.2, 0.0)
    it.append(tubo((-2.4, 7.85, 0.0), (7.4, 7.85, 0.0), 0.06, 380))
    it.append(tubo(lanca_a, lanca_b, 0.06, 380))
    zz = [((-2.4 + i * 0.7, 7.85, 0.0), (-2.4 + (i + 1) * 0.7, 8.2, 0.0)) if i % 2 == 0
          else ((-2.4 + i * 0.7, 8.2, 0.0), (-2.4 + (i + 1) * 0.7, 7.85, 0.0)) for i in range(14)]
    it += grupo_tubos(zz, 0.03, 560)
    apice = (cx, 9.2, 0.0)
    it += grupo_tubos([(apice, lanca_a), (apice, lanca_b), (apice, (cx, topo, 0.0))], 0.025, 360)
    it += caixa(6.8, 7.55, 0.0, 0.8, 0.5, 0.5, mult=40)               # contrapeso
    it.append(tubo((0.9, 7.85, 0.0), (0.9, 6.3, 0.0), 0.02, 120))     # cabo
    it.append(esfera_cheia((0.9, 6.3, 0.0), 0.2, 150))                # nó pendente
    it.append(tubo((0.9, 6.3, 0.0), NUCLEO, 0.014, 210))              # verificação ligada ao núcleo

    # 4. cobertura e fachada limpa
    ytopo = NIVEIS[4]
    it += caixa(0, ytopo + 0.05, 0, 5.9, 0.1, 3.9, mult=80)           # laje de cobertura (fechada)
    it += grupo_tubos([((-2.95, ytopo + 0.35, -1.95), (2.95, ytopo + 0.35, -1.95)),
                       ((-2.95, ytopo + 0.35, 1.95), (2.95, ytopo + 0.35, 1.95)),
                       ((-2.95, ytopo + 0.35, -1.95), (-2.95, ytopo + 0.35, 1.95)),
                       ((2.95, ytopo + 0.35, -1.95), (2.95, ytopo + 0.35, 1.95))], 0.05, 520)
    for x in [-2.9 + i * 0.725 for i in range(9)]:                    # montantes da fachada limpa (2 pavimentos)
        it.append(tubo((x, NIVEIS[2], 1.92), (x, ytopo, 1.92), 0.03, 38))
    for yy in (NIVEIS[3], ytopo):
        it.append(tubo((-2.9, yy, 1.92), (2.9, yy, 1.92), 0.03, 120))
    for x, z in ((-2.9, -1.9), (-1.45, -1.9), (0.0, -1.9), (1.45, 1.9), (2.9, 1.9), (2.9, 0.0),
                 (-2.9, 1.9), (-1.45, 1.9), (0.0, 1.9), (1.45, -1.9), (2.9, -1.9), (-2.9, 0.0)):
        it.append(esfera_cheia((x, ytopo + 0.35, z), 0.09, 8, tag=2))  # contas ciano (vistoria e entrega)

    # 5. núcleo âmbar no centro, para onde convergem todos os filamentos
    it.append(esfera_cheia(NUCLEO, 0.58, 3400, tag=1))
    it.append(esfera_casca(NUCLEO, 0.85, 600, tag=1))

    pts, tags = amostrar(it, N_OBRA, rng, jitter=0.006)
    return normalizar(pts), tags


def quantizar_e_embutir():
    """Gera as duas nuvens e devolve (conteúdo de embedded-assets.js, resumo)."""
    ind, tags_ind = gerar_industria()
    obra, tags = gerar_obra_circuito()
    b_ind, m_ind = quantizar(ind)
    b_obra, m_obra = quantizar(obra)
    mapa = {}
    mapa.update(entrada_embutida(b_ind, m_ind, "hand", {
        "/assets/hand/tags.bin": {"type": "application/octet-stream", "base64": base64.b64encode(tags_ind).decode("ascii")}}))
    mapa.update(entrada_embutida(b_obra, m_obra, "tree", {
        "/assets/tree/tags.bin": {"type": "application/octet-stream", "base64": base64.b64encode(tags).decode("ascii")}}))
    logo = REPO / "assets" / "logo" / "crivia-pontos.png"
    mapa["/assets/logo/crivia-pontos.png"] = {"type": "image/png", "base64": base64.b64encode(logo.read_bytes()).decode("ascii")}
    linhas = ['/* Dados que a cena 3D busca com fetch() (bloqueado em file://): nuvens de pontos da indústria',
              '   ("hand") e da obra-circuito ("tree"), quantizadas em uint16 (ver *.manifest.json). Gerado por',
              '   Site_crivia.py — não edite à mão. Lido por embeddedFetch() em app.js. */',
              "window.__CRIVIA_EMBEDDED_ASSETS__ = {"]
    itens = [f"  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}" for k, v in mapa.items()]
    linhas.append(",\n".join(itens))
    linhas.append("};\n")
    resumo = {"industria": len(ind), "obra": len(obra), "ambar": tags.count(1), "ciano": tags.count(2)}
    return "\n".join(linhas), resumo


# ════════════════════════════════════════════════════════════════════════════
#  CATÁLOGO (design-system.html): Overview | Components (desabilitado até a aprovação)
# ════════════════════════════════════════════════════════════════════════════
CATALOGO = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CRIVIA Design System</title>
<meta name="description" content="Catálogo do design system da CRIVIA Engenharia Consultiva.">
<link rel="icon" href="assets/overview/assets/images/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/overview/assets/css/fonts.css">
<link rel="stylesheet" href="assets/overview/assets/css/main.css">
<style>
/* Casca do catálogo: só roteamento e layout. Cores, tipos e a cena vêm do Overview (main.css). */
html, body { height: 100%; margin: 0; }
body { overflow: hidden; background: var(--background); color: var(--overlay-ink); font-family: var(--font-google-sans), system-ui, sans-serif; min-height: 0; }
:root { --ds-bar-h: 2.5rem; }
#ds-bar { position: fixed; top: 0; left: 0; right: 0; height: var(--ds-bar-h); z-index: 60; display: flex; align-items: center;
  justify-content: space-between; padding: 0 1.25rem; background: linear-gradient(180deg, rgba(255,255,255,.40) 0%, rgba(240,248,252,.14) 100%); -webkit-backdrop-filter: blur(24px) saturate(1.3); backdrop-filter: blur(24px) saturate(1.3); border-bottom: 1px solid rgba(255,255,255,.6); box-shadow: inset 0 1px 0 rgba(255,255,255,.75); }
@media (min-width: 48rem) { #ds-bar { padding: 0 1.875rem; } }
#ds-bar .marca { display: flex; align-items: center; gap: .6rem; font-family: "Plus Jakarta Sans", system-ui, sans-serif; font-weight: 700; letter-spacing: .3em; text-transform: uppercase; font-size: .8125rem; }
#ds-bar .marca img { width: 1.25rem; height: 1.25rem; display: block; }
#ds-bar nav { display: flex; gap: 1.75rem; font-family: "Geist", system-ui, sans-serif; font-size: .75rem; font-weight: 500; letter-spacing: .16em; text-transform: uppercase; }
.ds-tab { position: relative; padding: .25rem 0; color: var(--overlay-strong); text-decoration: none; transition: opacity .2s; }
.ds-tab[aria-current="page"] { color: var(--overlay-ink); }
.ds-tab[aria-current="page"]::after { content: ""; position: absolute; left: 0; right: 0; bottom: -2px; height: 1px; background: #F59E0B; }
.ds-tab[aria-disabled="true"] { opacity: .4; cursor: not-allowed; }
#overview-frame { position: fixed; top: var(--ds-bar-h); left: 0; right: 0; bottom: 0; width: 100%; height: calc(100% - var(--ds-bar-h)); border: 0; background: var(--background); }
#components-view { position: fixed; top: var(--ds-bar-h); left: 0; right: 0; bottom: 0; overflow: auto; display: none; }
body.view-components #overview-frame { display: none; }
body.view-components #components-view { display: block; }
</style>
</head>
<body class="onest_variable googleSans_variable">
  <header id="ds-bar">
    <a href="#overview" class="marca" style="color:inherit;text-decoration:none"><img src="assets/overview/assets/images/favicon.svg" alt="" width="20" height="20"><span>CRIVIA</span></a>
    <nav aria-label="Catálogo">
      <a href="#overview" id="tab-overview" class="ds-tab">Overview</a>
      <a href="#components" id="tab-components" class="ds-tab" aria-disabled="true" tabindex="-1" title="Disponível após a aprovação do Overview">Components</a>
    </nav>
  </header>
  <iframe id="overview-frame" src="assets/overview/index.html" title="CRIVIA — Overview"></iframe>
  <main id="components-view"></main>
<script>
  var tabs = { overview: document.getElementById('tab-overview'), components: document.getElementById('tab-components') };
  var COMPONENTS_ENABLED = false; // liberado somente após a aprovação do Overview
  function route() {
    var h = (location.hash || '#overview').slice(1);
    if (h === 'components' && !COMPONENTS_ENABLED) { h = 'overview'; history.replaceState(null, '', '#overview'); }
    document.body.classList.toggle('view-components', h === 'components');
    tabs.overview.setAttribute('aria-current', h === 'overview' ? 'page' : 'false');
    tabs.components.setAttribute('aria-current', h === 'components' ? 'page' : 'false');
  }
  tabs.components.addEventListener('click', function (e) { if (!COMPONENTS_ENABLED) e.preventDefault(); });
  window.addEventListener('hashchange', route);
  route();
</script>
</body>
</html>
"""


def montar_catalogo(saida):
    (saida / "design-system.html").write_text(CATALOGO, encoding="utf-8", newline="\n")


# ════════════════════════════════════════════════════════════════════════════
#  CONSTRUÇÃO
# ════════════════════════════════════════════════════════════════════════════
def extrair_modelo(destino):
    if not ZIP_MODELO.is_file():
        raise SystemExit(f"{PREFIXO} ERRO: modelo não encontrado: {ZIP_MODELO}")
    with zipfile.ZipFile(ZIP_MODELO) as z:
        z.extractall(destino)
    achados = list(Path(destino).glob("*/design-system.html"))
    if len(achados) != 1:
        raise ErroDePatch(f"estrutura inesperada no zip do modelo (design-system.html: {len(achados)})")
    return achados[0].parent


def copiar_fontes_nexus(destino):
    """Tipografia do Nexus: Plus Jakarta Sans (títulos) e Geist (textos), variáveis, subconjunto latino."""
    if not ZIP_NEXUS.is_file():
        raise SystemExit(f"{PREFIXO} ERRO: modelo de tipografia não encontrado: {ZIP_NEXUS}")
    with tempfile.TemporaryDirectory(prefix="crivia_nexus_") as tmp:
        with zipfile.ZipFile(ZIP_NEXUS) as z:
            z.extractall(tmp)
        for familia, nome in (("plusjakartasans", "PlusJakartaSans-latin.woff2"), ("geist", "Geist-latin.woff2")):
            achados = sorted(Path(tmp).glob(f"**/{familia}/**/*.woff2"))
            if len(achados) != 1:
                raise ErroDePatch(f"fonte '{familia}' no Nexus: {len(achados)} arquivo(s) woff2 (esperado 1)")
            shutil.copyfile(achados[0], destino / nome)


def publicar_cenario(ov):
    """Página "Apresentar meu cenário" + minuta do Aviso de Privacidade (fontes em ./cenario)."""
    fonte = REPO / "cenario"
    endpoint = os.environ.get("CRIVIA_LEAD_ENDPOINT", "http://localhost:8787").rstrip("/")
    if "CRIVIA_LEAD_ENDPOINT" not in os.environ:
        print("[CRIVIA] aviso: CRIVIA_LEAD_ENDPOINT não definido; usando o servidor local de desenvolvimento (%s)." % endpoint)
    conexoes = endpoint + (" https://script.googleusercontent.com" if "script.google.com" in endpoint else "")   # o Apps Script responde por redirecionamento
    csp = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self' %s; "
           "form-action 'self'; base-uri 'none'; object-src 'none'" % conexoes)
    (ov / "assets" / "css").mkdir(parents=True, exist_ok=True)
    (ov / "assets" / "js").mkdir(parents=True, exist_ok=True)
    html = (fonte / "cenario.html").read_text(encoding="utf-8").replace("__CRIVIA_CSP__", csp)
    (ov / "apresentar-cenario.html").write_text(html, encoding="utf-8", newline=chr(10))
    shutil.copyfile(fonte / "cenario.css", ov / "assets" / "css" / "cenario.css")
    shutil.copyfile(fonte / "regras.js", ov / "assets" / "js" / "cenario-regras.js")
    shutil.copyfile(fonte / "cenario.js", ov / "assets" / "js" / "cenario.js")
    # localidades (IBGE) servidas pelo próprio site: a página nunca chama o IBGE durante o preenchimento
    destino_loc = ov / "data" / "locations"
    if destino_loc.exists():
        shutil.rmtree(destino_loc)
    shutil.copytree(fonte / "data" / "locations", destino_loc, ignore=shutil.ignore_patterns("README.md"))
    cfg =(fonte / "config.js").read_text(encoding="utf-8").replace("__CRIVIA_LEAD_ENDPOINT__", endpoint)
    (ov / "assets" / "js" / "cenario-config.js").write_text(cfg, encoding="utf-8", newline=chr(10))
    aviso = (fonte / "aviso-privacidade.html").read_text(encoding="utf-8")
    (ov / "aviso-privacidade.html").write_text(aviso, encoding="utf-8", newline=chr(10))


# ════════════════════════════════════════════════════════════════════════════
#  ÚLTIMA DOBRA: o C sólido em 3D (com a esfera dourada) chega "esfarelado" em poeira e firma na tela
# ════════════════════════════════════════════════════════════════════════════
FINAL_ARVORE_INI = "  var createTreeParticles = async (config2, baseColor, finish) => {"
FINAL_ARVORE_FIM = "\n  // orig/src/components/common/scene/tuning.ts"
FINAL_ARVORE_NOVA = r"""  var createTreeParticles = async (config2, baseColor, finish) => {
    // CRIVIA: a cena final deixa de ser a obra-circuito. A marca (C em 3D com a esfera dourada + CRIVIA + Engenharia Consultiva)
    // é amostrada da arte oficial (PNG com fundo transparente, embutido) e vira uma nuvem de pontos com a cor de cada pixel e volume
    // dado pela distância à borda. Cada conta tem uma origem de "poeira" (aDust) que o shader desfaz por rolagem, no ritmo do Clarix.
    const { lightDirection, center, density, seed } = config2;
    const random = createRandom(seed + 5);
    const mobile = window.innerWidth <= 768;
    const aspect = window.innerWidth / window.innerHeight;
    const stacked = aspect < 0.7;
    const rec = window.__CRIVIA_EMBEDDED_ASSETS__["/assets/logo/crivia-pontos.png"];
    const img = new Image();
    img.src = "data:" + rec.type + ";base64," + rec.base64;
    await img.decode();
    const W = img.naturalWidth;
    const H = img.naturalHeight;
    const cv = document.createElement("canvas");
    cv.width = W;
    cv.height = H;
    const cx = cv.getContext("2d", { willReadFrequently: true });
    cx.drawImage(img, 0, 0);
    const px = cx.getImageData(0, 0, W, H).data;
    const mask = new Uint8Array(W * H);
    for (let k = 0; k < W * H; k += 1) mask[k] = px[k * 4 + 3] > 110 ? 1 : 0;
    // distância à borda (chanfro em duas passadas): dá o arredondado do volume
    const dt = new Float32Array(W * H);
    for (let k = 0; k < W * H; k += 1) dt[k] = mask[k] ? 1e4 : 0;
    for (let y = 0; y < H; y += 1) for (let x = 0; x < W; x += 1) {
      const k = y * W + x;
      if (!mask[k]) continue;
      let v = dt[k];
      if (x > 0) v = Math.min(v, dt[k - 1] + 1);
      if (y > 0) { v = Math.min(v, dt[k - W] + 1); if (x > 0) v = Math.min(v, dt[k - W - 1] + 1.4); if (x < W - 1) v = Math.min(v, dt[k - W + 1] + 1.4); }
      dt[k] = v;
    }
    for (let y = H - 1; y >= 0; y -= 1) for (let x = W - 1; x >= 0; x -= 1) {
      const k = y * W + x;
      if (!mask[k]) continue;
      let v = dt[k];
      if (x < W - 1) v = Math.min(v, dt[k + 1] + 1);
      if (y < H - 1) { v = Math.min(v, dt[k + W] + 1); if (x < W - 1) v = Math.min(v, dt[k + W + 1] + 1.4); if (x > 0) v = Math.min(v, dt[k + W - 1] + 1.4); }
      dt[k] = v;
    }
    // onde separar o C do texto (versão empilhada do celular): coluna com menos pixels entre 27% e 34% da largura
    let splitX = Math.round(W * 0.3);
    let best = 1e9;
    for (let x = Math.round(W * 0.27); x < Math.round(W * 0.34); x += 1) {
      let n = 0;
      for (let y = 0; y < H; y += 1) n += mask[y * W + x];
      if (n < best) { best = n; splitX = x; }
    }
    const fov = 32 * Math.PI / 180;
    const visH = 2 * 50 * Math.tan(fov / 2);
    const visW = visH * aspect;
    const total = Math.max(40e3, Math.round(Math.max(1, density) * (mobile ? 40e3 : 80e3)));
    let maskCount = 0;
    for (let k = 0; k < W * H; k += 1) maskCount += mask[k];
    const p = Math.min(1, total / (maskCount * 2));
    // linhas ocupadas por cada parte (C e texto) para empilhar no celular
    let cTop = H, cBot = 0, tTop = H, tBot = 0;
    for (let y = 0; y < H; y += 1) for (let x = 0; x < W; x += 1) {
      if (!mask[y * W + x]) continue;
      if (x < splitX) { if (y < cTop) cTop = y; if (y > cBot) cBot = y; } else { if (y < tTop) tTop = y; if (y > tBot) tBot = y; }
    }
    // pixel -> mundo: uma peça horizontal (desktop) ou duas empilhadas (celular)
    let partC;
    let partT;
    if (!stacked) {
      // marca 30% menor que a versão anterior (visW * 0.86 / 0.7 e teto de 36): mais harmônica com os cartões laterais
      const lw = Math.min(visW * (aspect < 1.1 ? 0.86 : 0.7), 36) * 0.7;
      partC = partT = { s: lw / W, x0: 0, cxw: -lw / 2, cyPix: H / 2, cyw: visH * 0.14 };
    } else {
      const cw = visW * 0.38;
      const tw = visW * 0.8;
      const sC = cw / splitX;
      const sT = tw / (W - splitX);
      const hC = (cBot - cTop) * sC;
      const hT = (tBot - tTop) * sT;
      const gap = 0.6;
      const top = (hC + gap + hT) / 2 + visH * 0.255;
      partC = { s: sC, x0: 0, cxw: -cw / 2 - 0, cyPix: (cTop + cBot) / 2, cyw: top - hC / 2 };
      partT = { s: sT, x0: splitX, cxw: -tw / 2, cyPix: (tTop + tBot) / 2, cyw: top - hC - gap - hT / 2 };
    }
    const points = [];
    const normalList = [];
    const colorList = [];
    for (let y = 1; y < H - 1; y += 1) {
      for (let x = 1; x < W - 1; x += 1) {
        const k = y * W + x;
        if (!mask[k]) continue;
        const part = x < splitX ? partC : partT;
        const s = part.s;
        const gx = (dt[k + 1] - dt[k - 1]) * 0.5;
        const gy = (dt[k + W] - dt[k - W]) * 0.5;
        const dd = dt[k];
        const zMax = Math.sqrt(Math.min(dd, 70)) * s * 1.7;
        for (let layer = 0; layer < 2; layer += 1) {
          if (random() > p) continue;
          const side = layer === 0 ? 1 : -1;
          const wx = part.cxw + (x - part.x0 + random() - 0.5) * s;
          const wy = part.cyw - (y - part.cyPix + random() - 0.5) * s;
          const wz = side * zMax * (0.55 + 0.45 * random()) - 0.14;
          points.push({ x: wx, y: wy, z: wz });
          const nl = Math.hypot(gx, gy, 1.2) || 1;
          normalList.push(-gx / nl, gy / nl, side * 1.2 / nl);
          const shade = side > 0 ? 0.95 : 0.8;
          colorList.push(px[k * 4] / 255 * shade, px[k * 4 + 1] / 255 * shade, px[k * 4 + 2] / 255 * shade);
        }
      }
    }
    const count = points.length;
    const beadSize = Math.max(0.024, Math.min(0.085, partC.s * 1.2));
    const cloud = buildParticleCloud(points, {
      particleSize: beadSize,
      sizeJitter: 0.16,
      bigFraction: 0,
      bigScale: 1,
      color: baseColor,
      finish,
      center,
      lightDirection,
      extent: visW,
      normals: new Float32Array(normalList),
      pointerRelax: true,
      seed: seed + 1
    });
    const col = new Color();
    const glow = cloud.glowAttribute.array;
    for (let i = 0; i < count; i += 1) {
      col.setRGB(colorList[i * 3], colorList[i * 3 + 1], colorList[i * 3 + 2], SRGBColorSpace);
      cloud.mesh.setColorAt(i, col);
      cloud.baseColors[i * 3] = col.r;
      cloud.baseColors[i * 3 + 1] = col.g;
      cloud.baseColors[i * 3 + 2] = col.b;
      glow[i * 3] = col.r * 0.06;
      glow[i * 3 + 1] = col.g * 0.06;
      glow[i * 3 + 2] = col.b * 0.06;
    }
    cloud.mesh.instanceColor.needsUpdate = true;
    cloud.glowAttribute.needsUpdate = true;
    // poeira: origem aleatória de cada conta (curva em sino; larga na horizontal) e ordem de chegada
    const dust = new Float32Array(count * 4);
    const bell = () => (random() + random() + random() - 1.5) / 1.5;
    for (let i = 0; i < count; i += 1) {
      dust[i * 4] = bell() * Math.max(visW, 26) * 0.7;
      dust[i * 4 + 1] = bell() * visH * 0.6;
      dust[i * 4 + 2] = bell() * 30;
      dust[i * 4 + 3] = random();
    }
    cloud.mesh.geometry.setAttribute("aDust", new InstancedBufferAttribute(dust, 4));
    // ── logo 3D: relevo (frente e verso) com a arte oficial como textura. Gira e flutua com a cena; materializa por blocos
    // no fim da chegada e abre sob o cursor (a poeira aparece por baixo). A esfera dourada é uma calota de verdade.
    const logoTex = new Texture(img);
    logoTex.colorSpace = SRGBColorSpace;
    logoTex.anisotropy = 8;
    logoTex.minFilter = LinearMipmapLinearFilter;
    logoTex.generateMipmaps = true;
    logoTex.needsUpdate = true;
    let gxMin = 1e9;
    let gxMax = -1;
    let gyMin = 1e9;
    let gyMax = -1;
    let gCount = 0;
    for (let y = 0; y < H; y += 1) for (let x = 0; x < W; x += 1) {
      const k = y * W + x;
      if (!mask[k]) continue;
      const r = px[k * 4];
      const g = px[k * 4 + 1];
      const b = px[k * 4 + 2];
      if (r > 150 && g > 90 && b < 100 && r > b * 2.1 && r > g) {
        gCount += 1;
        if (x < gxMin) gxMin = x;
        if (x > gxMax) gxMax = x;
        if (y < gyMin) gyMin = y;
        if (y > gyMax) gyMax = y;
      }
    }
    const ball = gCount > 200 ? { cx: (gxMin + gxMax) / 2, cy: (gyMin + gyMax) / 2, R: ((gxMax - gxMin) + (gyMax - gyMin)) / 4 * 1.05 } : null;
    const logoUniforms = {
      uReveal: { value: 0 },
      uPointer: { value: new Vector3(0, -1e4, 0) },
      uHoleR: { value: 5.2 },
      uHole: { value: 0 },
      uFlash: { value: 0 }
    };
    const makeLogoMat = (cutBall) => {
      const mat = new MeshStandardMaterial({
      map: logoTex,
      roughness: 0.42,
      metalness: 0.18,
      alphaTest: 0.45,
      emissive: 0xffffff,
      emissiveMap: logoTex,
      emissiveIntensity: 0.55
    });
      mat.customProgramCacheKey = () => "crivia-logo3d" + (cutBall ? "-cut" : "");
      mat.onBeforeCompile = (shader) => {
      shader.uniforms.uReveal = logoUniforms.uReveal;
      shader.uniforms.uPointer = logoUniforms.uPointer;
      shader.uniforms.uHoleR = logoUniforms.uHoleR;
      shader.uniforms.uHole = logoUniforms.uHole;
      shader.uniforms.uFlash = logoUniforms.uFlash;
      shader.vertexShader = shader.vertexShader.replace("#include <common>", "#include <common>\nvarying vec3 vWPos;").replace("#include <begin_vertex>", "#include <begin_vertex>\n	vWPos = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz;");
      shader.fragmentShader = shader.fragmentShader.replace("#include <common>", "#include <common>\nvarying vec3 vWPos;\nuniform float uReveal;\nuniform vec3 uPointer;\nuniform float uHoleR;\nuniform float uHole;\nuniform float uFlash;\nfloat cNoise( vec2 p ) { return fract( sin( dot( floor( p ), vec2( 12.9898, 78.233 ) ) ) * 43758.5453 ); }").replace(
        "#include <clipping_planes_fragment>",
        [
          "#include <clipping_planes_fragment>",
          "float cN = cNoise( vWPos.xy * 24.0 );",
          "float cReveal = clamp( uReveal * 1.25 - cN * 0.25, 0.0, 1.0 );",
          "if ( cN > uReveal * 1.1 ) discard;",
          "float cD = distance( vWPos, uPointer );",
          "float cHole = uHole * step( cD, uHoleR * ( 0.72 + 0.28 * cNoise( vWPos.xy * 18.0 + 3.0 ) ) );",
          "if ( cHole > 0.5 ) discard;",
          "float cRim = uHole * smoothstep( uHoleR * 1.12, uHoleR * 0.78, cD );"
        ].concat(cutBall ? [ "if ( distance( vMapUv * vec2( " + W + ".0, " + H + ".0 ), vec2( " + ball.cx.toFixed(2) + ", " + (H - ball.cy).toFixed(2) + " ) ) < " + (ball.R * 0.97).toFixed(2) + " ) discard;" ] : []).join("\n")
      ).replace("#include <emissivemap_fragment>", "#include <emissivemap_fragment>\n	totalEmissiveRadiance += vec3( 1.0, 0.72, 0.2 ) * cRim * 0.9 + vec3( 0.4, 0.8, 1.0 ) * ( 1.0 - uReveal ) * 0.4 + vec3( 1.0, 0.96, 0.85 ) * uFlash;");
    };
      return mat;
    };
    const logoMat = makeLogoMat(!!ball);
    const ballMat = new ShaderMaterial({
      uniforms: { uReveal: logoUniforms.uReveal, uPointer: logoUniforms.uPointer, uHoleR: logoUniforms.uHoleR, uHole: logoUniforms.uHole, uFlash: logoUniforms.uFlash },
      vertexShader: "varying vec3 vN;\nvarying vec3 vW;\nvoid main() {\n  vec4 w = modelMatrix * vec4( position, 1.0 );\n  vW = w.xyz;\n  vN = normalize( mat3( modelMatrix ) * normal );\n  gl_Position = projectionMatrix * viewMatrix * w;\n}",
      fragmentShader: "uniform float uReveal;\nuniform vec3 uPointer;\nuniform float uHoleR;\nuniform float uHole;\nuniform float uFlash;\nvarying vec3 vN;\nvarying vec3 vW;\nfloat cNoise( vec2 p ) { return fract( sin( dot( floor( p ), vec2( 12.9898, 78.233 ) ) ) * 43758.5453 ); }\nvoid main() {\n  float cN = cNoise( vW.xy * 24.0 );\n  if ( cN > uReveal * 1.1 ) discard;\n  float cD = distance( vW, uPointer );\n  if ( uHole * step( cD, uHoleR * ( 0.72 + 0.28 * cNoise( vW.xy * 18.0 + 3.0 ) ) ) > 0.5 ) discard;\n  float cRim = uHole * smoothstep( uHoleR * 1.12, uHoleR * 0.78, cD );\n  vec3 N = normalize( vN );\n  vec3 V = normalize( cameraPosition - vW );\n  vec3 R = reflect( -V, N );\n  float up = R.y * 0.5 + 0.5;\n  vec3 sky = mix( vec3( 0.50, 0.24, 0.03 ), vec3( 1.0, 0.88, 0.5 ), smoothstep( 0.0, 1.0, up ) );\n  float key = pow( max( dot( R, normalize( vec3( -0.45, 0.75, 0.55 ) ) ), 0.0 ), 16.0 );\n  float fill = pow( max( dot( R, normalize( vec3( 0.65, 0.2, 0.75 ) ) ), 0.0 ), 28.0 );\n  float horizon = smoothstep( 0.4, 0.0, abs( R.y ) ) * 0.22;\n  float fres = pow( 1.0 - max( dot( N, V ), 0.0 ), 3.0 );\n  vec3 gold = vec3( 1.0, 0.70, 0.16 );\n  vec3 col = sky * gold * 1.05 + vec3( 1.0, 0.97, 0.88 ) * ( key * 1.3 + fill * 0.55 ) + vec3( 1.0, 0.8, 0.35 ) * ( horizon + fres * 0.35 );\n  col *= 0.8 + 0.2 * N.y;\n  col += vec3( 1.0, 0.72, 0.2 ) * cRim * 0.9 + vec3( 0.4, 0.8, 1.0 ) * ( 1.0 - uReveal ) * 0.4 + vec3( 1.0, 0.96, 0.85 ) * uFlash;\n  gl_FragColor = vec4( col, 1.0 );\n  #include <tonemapping_fragment>\n  #include <colorspace_fragment>\n}"
    });
    const ST = 2;
    const BEV = 9;
    const HPLATE = 0.42;
    const makeLogoMesh = (xa, xb, part) => {
      const s = part.s;
      const nx = Math.floor((xb - 1 - xa) / ST) + 1;
      const ny = Math.floor((H - 2) / ST) + 1;
      const n = nx * ny;
      const zA = new Float32Array(n);
      const ins = new Uint8Array(n);
      const wxA = new Float32Array(n);
      const wyA = new Float32Array(n);
      const pxA = new Float32Array(n);
      const pyA = new Float32Array(n);
      for (let j = 0; j < ny; j += 1) {
        for (let i = 0; i < nx; i += 1) {
          const x = Math.min(W - 2, xa + i * ST);
          const y = Math.min(H - 2, j * ST + 1);
          const k = y * W + x;
          const v = j * nx + i;
          pxA[v] = x;
          pyA[v] = y;
          wxA[v] = part.cxw + (x - part.x0) * s;
          wyA[v] = part.cyw - (y - part.cyPix) * s;
          ins[v] = mask[k] || mask[k + 1] || mask[k + W] ? 1 : 0;
          let z = 0;
          if (mask[k]) {
            const t = Math.min(1, dt[k] / BEV);
            z = HPLATE * Math.min(1.3, s / 0.0327) * (1 - (1 - t) * (1 - t));
          }
          if (ball) {
            const dx = (x - ball.cx) * s;
            const dy = (y - ball.cy) * s;
            const Rw = ball.R * s;
            const rr = dx * dx + dy * dy;
            if (rr < Rw * Rw) z = Math.max(z, Math.sqrt(Rw * Rw - rr) * 0.92);
          }
          zA[v] = z;
        }
      }
      // suaviza a altura (2 passadas): o sombreamento varia só com o volume, sem granulado
      const tmp = new Float32Array(n);
      for (let pass = 0; pass < 2; pass += 1) {
        for (let j = 0; j < ny; j += 1) {
          for (let i = 0; i < nx; i += 1) {
            let acc = 0;
            let cnt = 0;
            for (let dj = -1; dj <= 1; dj += 1) for (let di = -1; di <= 1; di += 1) {
              const jj = j + dj;
              const ii = i + di;
              if (jj < 0 || jj >= ny || ii < 0 || ii >= nx) continue;
              acc += zA[jj * nx + ii];
              cnt += 1;
            }
            tmp[j * nx + i] = acc / cnt;
          }
        }
        zA.set(tmp);
      }
      const pos = new Float32Array(n * 6);
      const nor = new Float32Array(n * 6);
      const uv = new Float32Array(n * 4);
      for (let j = 0; j < ny; j += 1) {
        for (let i = 0; i < nx; i += 1) {
          const v = j * nx + i;
          const i0 = Math.max(0, i - 1);
          const i1 = Math.min(nx - 1, i + 1);
          const j0 = Math.max(0, j - 1);
          const j1 = Math.min(ny - 1, j + 1);
          const dzdx = (zA[j * nx + i1] - zA[j * nx + i0]) / ((i1 - i0) * ST * s);
          const dzdy = -(zA[j1 * nx + i] - zA[j0 * nx + i]) / ((j1 - j0) * ST * s);
          let nxv = -dzdx;
          let nyv = -dzdy;
          let nzv = 1;
          const nl = Math.hypot(nxv, nyv, nzv) || 1;
          nxv /= nl; nyv /= nl; nzv /= nl;
          pos[v * 3] = wxA[v] + center[0];
          pos[v * 3 + 1] = wyA[v] + center[1];
          pos[v * 3 + 2] = zA[v] + center[2];
          nor[v * 3] = nxv; nor[v * 3 + 1] = nyv; nor[v * 3 + 2] = nzv;
          const vb = v + n;
          pos[vb * 3] = pos[v * 3];
          pos[vb * 3 + 1] = pos[v * 3 + 1];
          pos[vb * 3 + 2] = center[2] - zA[v];
          nor[vb * 3] = nxv; nor[vb * 3 + 1] = nyv; nor[vb * 3 + 2] = -nzv;
          uv[v * 2] = pxA[v] / W;
          uv[v * 2 + 1] = 1 - pyA[v] / H;
          uv[vb * 2] = uv[v * 2];
          uv[vb * 2 + 1] = uv[v * 2 + 1];
        }
      }
      const tri = [];
      for (let j = 0; j < ny - 1; j += 1) {
        for (let i = 0; i < nx - 1; i += 1) {
          const a = j * nx + i;
          const b = a + 1;
          const c = a + nx;
          const d = c + 1;
          if (!(ins[a] || ins[b] || ins[c] || ins[d])) continue;
          tri.push(a, c, b, b, c, d);
          tri.push(a + n, b + n, c + n, b + n, d + n, c + n);
        }
      }
      const geo = new BufferGeometry();
      geo.setAttribute("position", new Float32BufferAttribute(pos, 3));
      geo.setAttribute("normal", new Float32BufferAttribute(nor, 3));
      geo.setAttribute("uv", new Float32BufferAttribute(uv, 2));
      geo.setIndex(new BufferAttribute(new Uint32Array(tri), 1));
      const m = new Mesh(geo, logoMat);
      m.frustumCulled = false;
      m.visible = false;
      return m;
    };
    const logoMeshesAll = stacked ? [makeLogoMesh(0, splitX, partC), makeLogoMesh(splitX, W, partT)] : [makeLogoMesh(0, W, partC)];
    let ballMesh = null;
    if (ball) {
      const Rw = ball.R * partC.s;
      const gx = partC.cxw + (ball.cx - partC.x0) * partC.s + center[0];
      const gy = partC.cyw - (ball.cy - partC.cyPix) * partC.s + center[1];
      const sgeo = new SphereGeometry(Rw * 0.985, 64, 48);
      sgeo.translate(gx, gy, center[2]);
      ballMesh = new Mesh(sgeo, ballMat);
      ballMesh.frustumCulled = false;
      ballMesh.visible = false;
    }
    const logoMeshes = ballMesh ? [...logoMeshesAll, ballMesh] : logoMeshesAll;
    // centro da marca (para a chegada "maior" assentar sobre o próprio centro)
    let pxMin = 1e9;
    let pxMax = -1e9;
    let pyMin = 1e9;
    let pyMax = -1e9;
    for (const part of (stacked ? [partC, partT] : [partC])) {
      const x0 = part.cxw;
      const y0 = part.cyw;
      pxMin = Math.min(pxMin, x0);
      pyMin = Math.min(pyMin, y0 - H * part.s * 0.5);
      pyMax = Math.max(pyMax, y0 + H * part.s * 0.5);
      pxMax = Math.max(pxMax, x0 + W * part.s);
    }
    const pivot = stacked
      ? [center[0], center[1] + (partC.cyw + partT.cyw) / 2, center[2]]
      : [center[0] + (pxMin + pxMax) / 2, center[1] + (pyMin + pyMax) / 2, center[2]];
    logoMeshes.forEach((m) => cloud.mesh.add(m));
    cloud.logo = {
      setReveal: (v) => {
        logoUniforms.uReveal.value = v;
        cloud.life.uCloudHide.value = v;
        const k = 1 + 0.07 * (1 - v) * (1 - v);
        logoUniforms.uFlash.value = 0.9 * Math.max(0, Math.sin(Math.min(1, v) * Math.PI)) ** 2;
        for (const m of logoMeshes) {
          m.scale.setScalar(k);
          m.position.set(pivot[0] * (1 - k), pivot[1] * (1 - k), pivot[2] * (1 - k));
        }
        const on = v > 0.001;
        for (const m of logoMeshes) m.visible = on;
      },
      setPointer: (hit) => {
        if (hit) { logoUniforms.uPointer.value.copy(hit); logoUniforms.uHole.value = 1; } else logoUniforms.uHole.value = 0;
      }
    };
    return cloud;
  };
"""

# Rodapé da última dobra: marca, contatos e créditos (componente que substitui o TreeOverlay do modelo)
FINAL_OVERLAY_INI = "  var TreeOverlay = () => {"
FINAL_OVERLAY_FIM = "\n  // orig/src/components/common/hero-overlay/scroll-fade.tsx"
FINAL_OVERLAY_NOVO = r"""  var TreeOverlay = () => {
    return /* @__PURE__ */ (0, import_jsx_runtime22.jsxs)("div", { className: "crivia-fim pointer-events-none absolute inset-0 select-none font-display text-overlay-ink", children: [
      /* @__PURE__ */ (0, import_jsx_runtime22.jsxs)("div", { className: "crivia-fim__lados", children: [
        /* @__PURE__ */ (0, import_jsx_runtime22.jsx)(RevealItem, { act: "tree", delay: 380, className: "crivia-fim__lado", children: /* @__PURE__ */ (0, import_jsx_runtime22.jsxs)("p", { className: "font-geist crivia-fim__texto", children: [/* @__PURE__ */ (0, import_jsx_runtime22.jsx)("strong", { children: "Projeto em risco?" }), " A Inteligência Artificial organiza e compara. Quem decide continua sendo você."] }) }),
        /* @__PURE__ */ (0, import_jsx_runtime22.jsx)(RevealItem, { act: "tree", delay: 520, className: "crivia-fim__lado", children: /* @__PURE__ */ (0, import_jsx_runtime22.jsxs)("p", { className: "font-geist crivia-fim__texto", children: [/* @__PURE__ */ (0, import_jsx_runtime22.jsx)("strong", { children: "A CRIVIA ajuda" }), " as pessoas e as áreas a trabalhar com conferência e responsabilidade claras."] }) })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime22.jsxs)(RevealItem, { act: "tree", delay: 700, className: "crivia-fim__base pointer-events-auto", children: [
        /* @__PURE__ */ (0, import_jsx_runtime22.jsx)("p", { className: "crivia-fim__chamada", children: "Comece pela realidade." }),
        /* @__PURE__ */ (0, import_jsx_runtime22.jsxs)("div", { className: "crivia-fim__acoes", children: [
          /* @__PURE__ */ (0, import_jsx_runtime22.jsx)(CriviaCtaPrimary, { compacto: true, onClick: () => CRIVIA_ABRIR_CENARIO("final"), children: "Apresentar meu cenário" }),
          /* @__PURE__ */ (0, import_jsx_runtime22.jsx)(CriviaCtaSecondary, { icone: ["M4 6.5h16v11H4z", "M4.5 7l7.5 6 7.5-6"], onClick: () => { window.location.href = "mailto:" + CRIVIA_EMAIL + "?subject=" + encodeURIComponent("Contato pelo site"); }, children: "Escrever para a CRIVIA" })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime22.jsxs)("p", { className: "font-geist crivia-fim__contato", children: [
          /* @__PURE__ */ (0, import_jsx_runtime22.jsx)("a", { href: "mailto:" + CRIVIA_EMAIL, children: CRIVIA_EMAIL }),
          /* @__PURE__ */ (0, import_jsx_runtime22.jsx)("span", { "aria-hidden": true, children: "·" }),
          /* @__PURE__ */ (0, import_jsx_runtime22.jsx)("a", { href: "aviso-privacidade.html", children: "Aviso de Privacidade" })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime22.jsxs)("p", { className: "font-geist crivia-fim__credito", children: [
          /* @__PURE__ */ (0, import_jsx_runtime22.jsx)("span", { children: "© 2026 CRIVIA Engenharia Consultiva · Engenharia para Decisão" }),
          /* @__PURE__ */ (0, import_jsx_runtime22.jsx)("span", { "aria-hidden": true, children: "·" }),
          /* @__PURE__ */ (0, import_jsx_runtime22.jsx)("span", { children: "Site produzido pela CRIVIA" })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime22.jsx)("img", { className: "crivia-fim__selo", src: "assets/images/bni/proud-member.png", width: 900, height: 526, alt: "Selo Proud BNI Member", loading: "lazy", decoding: "async" })
      ] })
    ] });
  };
"""

CSS_FINAL = r"""
/* ════ CRIVIA ════ última dobra: marca, chamada, contatos e créditos sobre o C em poeira ════ */
/* palavra da barra: mesma tipografia da Hero (títulos, 700, caixa alta, degradê azul), em corpo de barra */
.crivia-nav-logo { display: block; font-family: "Plus Jakarta Sans", system-ui, sans-serif; font-size: 1.15rem; font-weight: 700; line-height: 1; letter-spacing: -.02em; text-transform: uppercase; white-space: nowrap;
  color: transparent; -webkit-text-fill-color: transparent; background: linear-gradient(180deg, #2F5599 0%, #0F3A8C 55%, #001D3D 100%); -webkit-background-clip: text; background-clip: text; }
@media (min-width: 48rem) { .crivia-nav-logo { font-size: 1.4rem; } }
.crivia-fim { --fim-gutter: clamp(1rem, 3.2vw, 2.5rem); }
.crivia-fim__lados { position: absolute; left: var(--fim-gutter); right: var(--fim-gutter); top: 61%; display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
.crivia-fim__lado { width: min(21rem, 31vw); height: 6.6rem; display: flex; align-items: center; padding: 1rem 1.3rem; border-radius: 1.1rem; text-align: left;
  background: linear-gradient(160deg, rgba(255,255,255,.58), rgba(255,255,255,.26)); border: 1px solid rgba(255,255,255,.72);
  box-shadow: 0 14px 44px rgba(10,54,157,.10), inset 0 1px 0 rgba(255,255,255,.8); -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px); }
.crivia-fim__texto { margin: 0; font-size: 1rem; font-weight: 400; line-height: 1.5; color: #123A7A; }
.crivia-fim__texto strong { font-family: var(--font-google-sans), system-ui, sans-serif; font-weight: 700; letter-spacing: -.02em; color: #001D3D; }
.crivia-fim__acoes .crivia-cta { width: 12.6rem; height: 2.1rem; min-height: 0; padding: 0; justify-content: center; box-shadow: 0 3px 12px rgba(0,29,61,.24); }
.crivia-fim__acoes .crivia-cta .crivia-cta__inner { width: 100%; height: 100%; justify-content: center; padding: 0 .65rem; gap: .45rem; font-size: .76rem; white-space: nowrap; }
.crivia-fim__acoes .crivia-cta svg, .crivia-fim__acoes .crivia-cta .crivia-cta__icon, .crivia-fim__acoes .crivia-cta .crivia-cta__chip, .crivia-fim__acoes .crivia-cta .crivia-cta__arrow { flex: none; }
.crivia-fim__acoes .crivia-cta .crivia-cta__icon { width: 1.3rem; height: 1.3rem; padding: .3rem; }
.crivia-fim__acoes .crivia-cta .crivia-cta__chip, .crivia-fim__acoes .crivia-cta .crivia-cta__arrow { width: 1.1rem; height: 1.1rem; padding: .22rem; }

.crivia-fim__base { position: absolute; left: 0; right: 0; bottom: clamp(.9rem, 2.4vh, 1.8rem); display: flex; flex-direction: column; align-items: center; gap: .85rem; padding: 0 1rem; text-align: center; }
.crivia-fim__chamada { margin: 0; font-size: clamp(1.45rem, 2.5vw, 2.1rem); font-weight: 650; letter-spacing: -.02em; color: #001D3D; }
.crivia-fim__acoes { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: .75rem 1rem; }
.crivia-fim__contato, .crivia-fim__credito { margin: 0; font-size: .8125rem; line-height: 1.4; color: #40597F; display: flex; flex-wrap: wrap; justify-content: center; gap: .3rem .7rem; }
.crivia-fim__contato a { color: #0A369D; font-weight: 600; text-decoration: none; border-bottom: 1px solid rgba(10,54,157,.3); transition: border-color .2s; }
.crivia-fim__contato a:hover, .crivia-fim__contato a:focus-visible { border-bottom-color: #0A369D; outline: none; }
.crivia-fim__credito { font-size: .75rem; color: #5B7396; }
/* selo Proud Member: no canto inferior direito, alinhado ao mesmo gutter dos cartões laterais; arte original, só muda o tamanho */
.crivia-fim__selo { position: absolute; right: var(--fim-gutter); bottom: 0; width: clamp(4.4rem, 5.4vw, 5.8rem); height: auto; display: block; pointer-events: none; }
@media (max-width: 47.99rem) {
  .crivia-fim__selo { right: 1rem; width: 3.8rem; }
  .crivia-fim__lados { top: 47.5%; flex-direction: column; gap: .55rem; left: 1rem; right: 1rem; }
  .crivia-fim__lado { width: 100%; height: 4.6rem; padding: .6rem .9rem; border-radius: .9rem; }
  .crivia-fim__texto { font-size: .8rem; line-height: 1.4; }
  .crivia-fim__base { gap: .45rem; bottom: .6rem; }
  .crivia-fim__chamada { font-size: 1.3rem; }
  .crivia-fim__contato, .crivia-fim__credito { flex-direction: column; align-items: center; gap: .2rem; }
  .crivia-fim__contato span[aria-hidden], .crivia-fim__credito span[aria-hidden] { display: none; }
  .crivia-fim__acoes { flex-direction: column; width: min(15rem, 100%); }
  .crivia-fim__acoes .crivia-cta { width: 100%; height: 2.2rem; justify-content: center; }
}
/* menu do celular: todos os itens centralizados; o último (CTA do modelo) não pode encostar na borda nem quebrar */
nav[aria-label="Mobile"] a { text-align: center; }
nav[aria-label="Mobile"] a.underline { width: auto; max-width: 100%; font-size: 1.05rem; letter-spacing: .16em; white-space: nowrap; }
"""


def aplicar_patches(raiz_modelo):
    """Aplica todos os patches sobre a cópia temporária do modelo e devolve o resumo da geração."""
    ov = raiz_modelo / "assets" / "overview"
    app = ov / "assets" / "js" / "app.js"
    js = app.read_text(encoding="utf-8")
    js = aplicar(js, PATCHES_CENA, "app.js")
    js = trocar_trecho(js, GLIFO_INI, GLIFO_FIM, GLIFO_C, "glifo X->C")
    js = trocar_trecho(js, FINAL_ARVORE_INI, FINAL_ARVORE_FIM, FINAL_ARVORE_NOVA, "final:C-em-poeira")
    js = trocar_trecho(js, REDE_INI, REDE_FIM, REDE_NOVA, "rede de comunicação")
    js = trocar_trecho(js, FRASE2_INI, FRASE2_FIM, FRASE2_NOVA, "hero:frase2")
    js = trocar_trecho(js, HERO_BLOCO_INI, HERO_BLOCO_FIM, HERO_BLOCO_NOVO, "hero:titulo")
    js = trocar_trecho(js, BOTOES_INI, BOTOES_FIM, BOTOES_NOVOS, "hero:botoes")
    js = aplicar(js, [("mao:busca", MAO_BUSCA_ANTIGA, MAO_BUSCA_NOVA, 1), ("mao:fim", MAO_FIM_ANTIGO, MAO_FIM_NOVO, 1)], "app.js")
    js = trocar_apos(js, "var createHandParticles = async", "    return buildParticleCloud(points, {", "    const cloud = buildParticleCloud(points, {", "mao:retorno")
    js = aplicar(js, PATCHES_REDE_OPACIDADE, "app.js")
    js = aplicar(js, PATCHES_TEXTO, "app.js")
    js = trocar_trecho(js, FINAL_OVERLAY_INI, FINAL_OVERLAY_FIM, FINAL_OVERLAY_NOVO, "final:overlay")
    js = aplicar(js, PATCHES_TIPO_IND, "app.js")
    js = trocar_trecho(js, HAND_INI, HAND_FIM, HAND_NOVO, "ind:overlay")
    js = trocar_trecho(js, CAT_INI, CAT_FIM, CAT_NOVO, "cat:overlay")
    js = aplicar(js, PATCHES_HERO_FUNDO, "app.js")
    js = aplicar(js, PATCHES_SOBRE, "app.js")
    js = aplicar(js, PATCHES_NAV, "app.js")
    app.write_text(js, encoding="utf-8", newline="\n")

    css = ov / "assets" / "css" / "main.css"
    css.write_text(aplicar(css.read_text(encoding="utf-8"), PATCHES_CSS, "main.css") + CSS_CRIVIA + CSS_IND + CSS_MOTORES + CSS_CAT + CSS_SOBRE + CSS_METODO + CSS_NAV + CSS_FINAL,
                   encoding="utf-8", newline="\n")
    copiar_fontes_nexus(ov / "assets" / "fonts")
    publicar_cenario(ov)
    destino_logo = ov / "assets" / "images" / "logo"
    destino_logo.mkdir(parents=True, exist_ok=True)
    for nome_logo in ("crivia-palavra.png",):
        shutil.copyfile(REPO / "assets" / "logo" / nome_logo, destino_logo / nome_logo)
    selo_bni = REPO / "assets" / "bni" / "proud-member.png"
    if selo_bni.is_file():
        destino_bni = ov / "assets" / "images" / "bni"
        destino_bni.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(selo_bni, destino_bni / selo_bni.name)
    img_metodo = REPO / "assets" / "metodo" / "tablet-industrial.png"
    if img_metodo.is_file():
        destino_metodo = ov / "assets" / "images" / "metodo"
        destino_metodo.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(img_metodo, destino_metodo / img_metodo.name)
    fotos = REPO / "assets" / "produtos"
    if fotos.is_dir():
        destino_fotos = ov / "assets" / "images" / "produtos"
        destino_fotos.mkdir(parents=True, exist_ok=True)
        for f in sorted(fotos.glob("*.jpg")):
            shutil.copyfile(f, destino_fotos / f.name)

    idx = ov / "index.html"
    html = aplicar(idx.read_text(encoding="utf-8"), PATCHES_HTML, "index.html")
    if html.count(RAIZ_INI) != 1 or html.count(RAIZ_FIM) != 1:
        raise ErroDePatch("[index.html] âncoras da raiz (#root) não encontradas")
    i, j = html.index(RAIZ_INI) + len(RAIZ_INI), html.index(RAIZ_FIM)
    html = html[:i] + "</div>" + html[j:]    # remove o HTML pré-renderizado; o React monta a página
    idx.write_text(html, encoding="utf-8", newline="\n")

    embutidos, resumo = quantizar_e_embutir()
    (ov / "assets" / "js" / "embedded-assets.js").write_text(embutidos, encoding="utf-8", newline="\n")

    logo, favicon = gerar_c()
    (ov / "assets" / "images" / "brand" / "logo.svg").write_text(logo, encoding="utf-8", newline="\n")
    (ov / "assets" / "images" / "favicon.svg").write_text(favicon, encoding="utf-8", newline="\n")
    return resumo


def verificar(saida):
    """Checagens estruturais do site gerado."""
    ov = saida / "assets" / "overview"
    obrigatorios = [saida / "design-system.html", ov / "index.html", ov / "assets/js/app.js", ov / "assets/js/embedded-assets.js",
                    ov / "assets/css/main.css", ov / "assets/css/fonts.css", ov / "assets/images/favicon.svg",
                    ov / "assets/fonts/PlusJakartaSans-latin.woff2", ov / "assets/fonts/Geist-latin.woff2"]
    for p in obrigatorios:
        if not p.is_file():
            raise ErroDePatch(f"arquivo esperado ausente: {p}")
    txt = (ov / "assets/js/embedded-assets.js").read_text(encoding="utf-8")
    mapa = json.loads(txt[txt.index("= {") + 2: txt.rindex("};") + 1])
    contagens = {}
    for pasta in ("hand", "tree"):
        manifesto = json.loads(mapa[f"/assets/{pasta}/points.manifest.json"]["text"])
        n = manifesto["objects"][0]["count"]
        tam = len(base64.b64decode(mapa[f"/assets/{pasta}/points.bin"]["base64"]))
        if tam != n * 3 * 2:
            raise ErroDePatch(f"{pasta}: points.bin tem {tam} bytes, esperado {n * 6}")
        contagens[pasta] = n
    if len(base64.b64decode(mapa["/assets/hand/tags.bin"]["base64"])) != contagens["hand"]:
        raise ErroDePatch("tags.bin não confere com a contagem de pontos da indústria")
    if len(base64.b64decode(mapa["/assets/tree/tags.bin"]["base64"])) != contagens["tree"]:
        raise ErroDePatch("tags.bin não confere com a contagem de pontos da obra-circuito")
    restos = []
    for p in (ov / "index.html", ov / "assets/js/app.js", ov / "assets/css/main.css", saida / "design-system.html"):
        t = p.read_text(encoding="utf-8")
        for termo in ("Lorem", "Design System", "Say Hello", "Auralis", "#b552ff", "#6fff85"):
            if termo == "Design System" and p.name == "design-system.html":
                continue  # "CRIVIA Design System" é o título do catálogo, de propósito
            if termo in t:
                restos.append(f"{p.name}: '{termo}'")
    if restos:
        raise ErroDePatch("restos do modelo no site gerado: " + "; ".join(restos))


def hash_pasta(pasta):
    h = hashlib.sha256()
    for p in sorted(x for x in pasta.rglob("*") if x.is_file()):
        h.update(str(p.relative_to(pasta)).encode("utf-8"))
        h.update(p.read_bytes())
    return h.hexdigest()


def construir():
    log("lendo o modelo Auralis (somente leitura): " + str(ZIP_MODELO))
    with tempfile.TemporaryDirectory(prefix="crivia_modelo_") as tmp:
        raiz = extrair_modelo(tmp)
        log("aplicando patches (paleta, C, indústria, obra-circuito, textos)…")
        resumo = aplicar_patches(raiz)
        log(f"nuvens de pontos: indústria={resumo['industria']} · obra-circuito={resumo['obra']} "
            f"(núcleo âmbar={resumo['ambar']}, contas ciano={resumo['ciano']})")
        # monta e verifica numa pasta temporária; só então troca `site/` (nada sai pela metade)
        pronto = Path(tmp) / "site_pronto"
        (pronto / "assets").mkdir(parents=True)
        shutil.copytree(raiz / "assets" / "overview", pronto / "assets" / "overview")
        montar_catalogo(pronto)
        log("verificando a estrutura do site gerado…")
        verificar(pronto)
        # só apaga `site/` se for a pasta site/ deste repositório
        if SAIDA.exists():
            if SAIDA.resolve().parent != REPO or SAIDA.name != "site":
                raise SystemExit(f"{PREFIXO} ERRO: recusei apagar uma pasta fora do esperado: {SAIDA}")
            shutil.rmtree(SAIDA)
        shutil.copytree(pronto, SAIDA)
    tam = sum(p.stat().st_size for p in SAIDA.rglob("*") if p.is_file()) / 1e6
    log(f"pronto: {SAIDA / 'design-system.html'}  ({tam:.1f} MB · hash {hash_pasta(SAIDA)[:12]})")


# ════════════════════════════════════════════════════════════════════════════
#  SERVIDOR
# ════════════════════════════════════════════════════════════════════════════
class Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # sem ruído no console
        pass


def servir(porta, abrir, pasta=None, caminho="design-system.html"):
    class Servidor(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    def handler(*a, **k):
        return Silencioso(*a, directory=str(pasta or SAIDA), **k)

    servidor, escolhida = None, None
    for p in range(porta, porta + 20):
        try:
            servidor = Servidor(("127.0.0.1", p), handler)
            escolhida = p
            break
        except OSError:
            log(f"porta {p} ocupada, tentando a próxima…")
    if servidor is None:
        raise SystemExit(f"{PREFIXO} ERRO: nenhuma porta livre entre {porta} e {porta + 19}.")
    url = f"http://localhost:{escolhida}/{caminho}"
    log(f"servindo em {url}  (Ctrl+C para encerrar)")
    if abrir:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        log("encerrado.")
    finally:
        servidor.server_close()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Serve o Site CRIVIA padrão (pasta site_crivia_padrao/). Com --antigo, constrói e serve o site anterior (modelo Auralis).")
    ap.add_argument("--antigo", action="store_true", help="constrói e serve o site anterior (pasta site/), em vez do site padrão")
    ap.add_argument("--build-only", action="store_true", help="com --antigo: só constrói a pasta site/, sem servir")
    ap.add_argument("--no-browser", action="store_true", help="não abre o navegador")
    ap.add_argument("--port", type=int, default=8080, help="porta preferida (padrão 8080)")
    args = ap.parse_args()
    if not args.antigo:
        if args.build_only:
            raise SystemExit(f"{PREFIXO} --build-only só vale com --antigo. O site padrão não precisa ser construído.")
        if not (PASTA_PADRAO / "index.html").is_file():
            raise SystemExit(f"{PREFIXO} ERRO: não achei {PASTA_PADRAO / 'index.html'}.")
        log(f"Site CRIVIA padrão: {PASTA_PADRAO}")
        servir(args.port, not args.no_browser, PASTA_PADRAO, "index.html")
        return
    try:
        construir()
    except ErroDePatch as e:
        raise SystemExit(f"{PREFIXO} FALHA NO PATCH — nada foi publicado em site/.\n{e}")
    if not args.build_only:
        servir(args.port, not args.no_browser)


if __name__ == "__main__":
    main()
