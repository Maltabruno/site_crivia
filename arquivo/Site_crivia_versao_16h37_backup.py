"""
Site CRIVIA — Engenharia para Decisão & Auditoria Forense
==========================================================
Gera o index.html na pasta site/ e inicia um servidor local na porta 8080.

Uso:
    python site_crivia.py              → Constrói e serve (abre navegador)
    python site_crivia.py --build-only → Só gera os arquivos em site/
    python site_crivia.py --no-browser → Serve sem abrir o navegador
    python site_crivia.py --port 3000  → Serve na porta especificada
"""

import os
import sys
import http.server
import socketserver
import webbrowser
import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parent
SAIDA = REPO / "site"

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CRIVIA | Engenharia para Decisão & Auditoria Forense</title>
    
    <!-- Fontes Técnicas e Executivas -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">

    <!-- Tailwind CSS (CDN para arquivo único) -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        obsidian: '#06090F',
                        carbon: '#0C121E',
                        grid: '#1A2436',
                        titanium: '#F8FAFC',
                        slate: '#94A3B8',
                        forense: '#F43F5E',
                        sentinela: '#00D2FF',
                        prova: '#10B981',
                        alerta: '#F59E0B'
                    },
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                        display: ['Space Grotesk', 'sans-serif'],
                        mono: ['JetBrains Mono', 'monospace']
                    },
                    animation: {
                        'scanline': 'scanline 8s linear infinite',
                        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                    },
                    keyframes: {
                        scanline: {
                            '0%': { top: '-10%' },
                            '100%': { top: '110%' },
                        }
                    }
                }
            }
        }
    </script>
    <style>
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #06090F; }
        ::-webkit-scrollbar-thumb { background: #1A2436; }
        ::-webkit-scrollbar-thumb:hover { background: #00D2FF; }
        
        .hairline-grid {
            background-image: 
                linear-gradient(to right, #1A2436 1px, transparent 1px),
                linear-gradient(to bottom, #1A2436 1px, transparent 1px);
            background-size: 40px 40px;
            background-position: center top;
        }

        .triage-radio:checked + label {
            background-color: #00D2FF;
            color: #06090F;
            border-color: #00D2FF;
        }
    </style>
</head>
<body class="bg-obsidian text-slate font-sans antialiased selection:bg-sentinela/30 selection:text-sentinela flex flex-col min-h-screen relative overflow-x-hidden">

    <!-- Fundo de Grade Sutil -->
    <div class="fixed inset-0 hairline-grid opacity-20 pointer-events-none z-0"></div>

    <!-- DOBRA 0: Barra de Telemetria Topo -->
    <div class="relative z-50 border-b border-grid bg-obsidian/90 backdrop-blur-sm">
        <div class="max-w-7xl mx-auto px-4 py-1.5 flex justify-between items-center text-[10px] font-mono text-sentinela uppercase tracking-widest">
            <div class="flex space-x-6">
                <span class="flex items-center"><span class="w-1.5 h-1.5 rounded-full bg-prova animate-pulse mr-2"></span>[SYS: SENTINELA 2.0]</span>
                <span class="hidden md:inline-block">[ESCOPO: 100% DADOS AUDITADOS]</span>
            </div>
            <div class="flex space-x-6">
                <span class="hidden sm:inline-block text-slate">[JURISDIÇÃO: SERRA/VITÓRIA - ES]</span>
                <span class="text-prova">[CREA-ES / ART ATIVA]</span>
            </div>
        </div>
    </div>

    <!-- HEADER: Navegação Principal -->
    <header class="relative z-50 border-b border-grid bg-obsidian/80 backdrop-blur-md sticky top-0">
        <div class="max-w-7xl mx-auto px-4 h-16 flex justify-between items-center">
            <div class="flex items-center space-x-2">
                <div class="w-3 h-3 bg-titanium"></div>
                <span class="font-display font-bold text-lg text-titanium tracking-tight">CRIVIA <span class="text-slate font-normal text-sm font-sans tracking-normal ml-2 hidden sm:inline-block">// Engenharia para Decisão</span></span>
            </div>
            <nav class="hidden md:flex space-x-8 text-sm font-medium text-slate">
                <a href="#tese" class="hover:text-titanium transition-colors">01. A Tese</a>
                <a href="#metodo" class="hover:text-titanium transition-colors">02. O Método</a>
                <a href="#provas" class="hover:text-titanium transition-colors">03. Provas</a>
                <a href="#portfolio" class="hover:text-titanium transition-colors">04. Portfólio (12)</a>
            </nav>
            <a href="#triagem" class="border border-grid hover:border-sentinela text-titanium hover:text-sentinela px-4 py-2 text-xs font-mono transition-all duration-300 bg-carbon">
                [ Agendar Triagem ↗ ]
            </a>
        </div>
    </header>

    <main class="relative z-10 flex-grow">
        
        <!-- DOBRA 1: HERO SECTION -->
        <section class="max-w-7xl mx-auto px-4 py-16 md:py-24 border-b border-grid">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
                
                <!-- Coluna Esquerda: Copy -->
                <div class="lg:col-span-7 space-y-8 pr-0 lg:pr-8 border-r-0 lg:border-r border-grid">
                    <div class="inline-flex items-center px-2 py-1 border border-grid bg-carbon text-[10px] font-mono text-sentinela tracking-widest uppercase">
                        [ 00 // Critério · Visão · Ação ]
                    </div>
                    <h1 class="font-display text-4xl md:text-5xl lg:text-6xl font-bold text-titanium leading-[1.1] tracking-tight">
                        Onde há incerteza na interface, há sangria no caixa. Onde entra o nosso método, você governa com a <span class="text-prova">prova.</span>
                    </h1>
                    <p class="text-base md:text-lg text-slate leading-relaxed max-w-2xl">
                        Controle comum só mostra o sintoma. A CRIVIA une mais de 30 anos de engenharia de contratos ao Sistema Sentinela para auditar 100% dos seus orçamentos, medições e diários de obra — revelando a causa real e entregando a prova técnica com ART para você decidir e destravar seu projeto.
                    </p>
                    
                    <!-- Tríade -->
                    <div class="flex flex-wrap gap-4 font-mono text-[10px] sm:text-xs uppercase tracking-wider">
                        <div class="flex items-center text-forense border border-grid px-3 py-1.5 bg-carbon"><span class="w-1.5 h-1.5 bg-forense rounded-full mr-2"></span>1. Dor: Incerteza</div>
                        <div class="flex items-center text-sentinela border border-grid px-3 py-1.5 bg-carbon"><span class="w-1.5 h-1.5 bg-sentinela rounded-full mr-2"></span>2. Meio: Método Sentinela</div>
                        <div class="flex items-center text-prova border border-grid px-3 py-1.5 bg-carbon"><span class="w-1.5 h-1.5 bg-prova rounded-full mr-2"></span>3. Valor: Prova Material</div>
                    </div>

                    <div class="pt-4 flex flex-col sm:flex-row gap-4">
                        <a href="#triagem" class="bg-prova text-obsidian font-display font-semibold px-6 py-3 text-center hover:bg-emerald-400 transition-colors">
                            Solicitar Triagem de 20 Min →
                        </a>
                        <a href="#produtos" class="border border-grid text-titanium font-display font-medium px-6 py-3 text-center hover:border-slate transition-colors bg-carbon">
                            Inspecionar Produtos ↓
                        </a>
                    </div>
                </div>

                <!-- Coluna Direita: Interactive Terminal -->
                <div class="lg:col-span-5 relative">
                    <div class="absolute -top-1 -left-1 w-2 h-2 border-t border-l border-sentinela"></div>
                    <div class="absolute -top-1 -right-1 w-2 h-2 border-t border-r border-sentinela"></div>
                    <div class="absolute -bottom-1 -left-1 w-2 h-2 border-b border-l border-sentinela"></div>
                    <div class="absolute -bottom-1 -right-1 w-2 h-2 border-b border-r border-sentinela"></div>

                    <div class="border border-grid bg-carbon relative overflow-hidden flex flex-col h-[400px]">
                        <div class="absolute left-0 w-full h-[1px] bg-sentinela shadow-[0_0_10px_#00D2FF] opacity-50 z-20 animate-scanline pointer-events-none"></div>

                        <div class="flex border-b border-grid bg-obsidian text-[10px] font-mono text-slate uppercase overflow-x-auto">
                            <button class="term-tab px-4 py-2 border-r border-grid text-sentinela border-b border-b-sentinela whitespace-nowrap" data-target="prova01">Prova 01: Orçamento</button>
                            <button class="term-tab px-4 py-2 border-r border-grid hover:text-titanium whitespace-nowrap" data-target="prova02">Prova 02: Contrato</button>
                            <button class="term-tab px-4 py-2 hover:text-titanium whitespace-nowrap" data-target="prova03">Prova 03: Medição</button>
                        </div>

                        <div class="p-5 flex-grow font-mono text-sm relative z-10 flex flex-col justify-center">
                            
                            <div id="prova01" class="term-content block space-y-4">
                                <div class="text-sentinela text-xs mb-4">>[SYS_QUERY]: COMPARAR(PROPOSTA_A, BASE_SINAPI_ES)</div>
                                <div class="flex justify-between border-b border-grid pb-2">
                                    <span class="text-slate">PROPOSTO (EMPREITEIRA):</span>
                                    <span class="text-titanium">R$ 3.450.000</span>
                                </div>
                                <div class="flex justify-between border-b border-grid pb-2">
                                    <span class="text-slate">AUDITADO (SINAPI-ES):</span>
                                    <span class="text-titanium">R$ 2.978.400</span>
                                </div>
                                <div class="pt-2">
                                    <span class="text-xs text-slate uppercase block mb-1">Diagnóstico na Curva A:</span>
                                    <div class="text-forense text-lg md:text-xl font-bold bg-forense/10 px-3 py-2 border border-forense/30">
                                        +R$ 471.600 (+15,8%) DE SOBREPREÇO
                                    </div>
                                </div>
                                <div class="text-alerta text-xs mt-2">> AVISO: 3 Bombas-Relógio (Subpreço) detectadas.</div>
                            </div>

                            <div id="prova02" class="term-content hidden space-y-4">
                                <div class="text-sentinela text-xs mb-4">>[SYS_QUERY]: CRUZAR(RDO, INMET, CPM)</div>
                                <div class="flex justify-between border-b border-grid pb-2">
                                    <span class="text-slate">PLEITO (EMPREITEIRA):</span>
                                    <span class="text-titanium">R$ 485.000</span>
                                </div>
                                <div class="flex justify-between border-b border-grid pb-2">
                                    <span class="text-slate">PROCEDENTE (VERIFICADO):</span>
                                    <span class="text-titanium">R$ 74.200</span>
                                </div>
                                <div class="pt-2">
                                    <span class="text-xs text-slate uppercase block mb-1">Economia Líquida Gerada:</span>
                                    <div class="text-prova text-lg md:text-xl font-bold bg-prova/10 px-3 py-2 border border-prova/30">
                                        -R$ 410.800 (84,7%) GLOSADOS
                                    </div>
                                </div>
                                <div class="text-sentinela text-xs mt-2">> FATO: Desconstituído por prova meteorológica (INMET).</div>
                            </div>

                            <div id="prova03" class="term-content hidden space-y-4">
                                <div class="text-sentinela text-xs mb-4">>[SYS_QUERY]: VERIFICAR_AVANÇO(BM_04, CAMPO_360)</div>
                                <div class="flex justify-between border-b border-grid pb-2">
                                    <span class="text-slate">COBRADO (BM 04):</span>
                                    <span class="text-titanium">R$ 280.000</span>
                                </div>
                                <div class="flex justify-between border-b border-grid pb-2">
                                    <span class="text-slate">VERIFICADO CRIVIA:</span>
                                    <span class="text-titanium">R$ 235.000</span>
                                </div>
                                <div class="pt-2">
                                    <span class="text-xs text-slate uppercase block mb-1">Status da Medição:</span>
                                    <div class="text-alerta text-lg md:text-xl font-bold bg-alerta/10 px-3 py-2 border border-alerta/30">
                                        -R$ 45.000 RETIDOS (HOLD POINT)
                                    </div>
                                </div>
                                <div class="text-slate text-xs mt-2">> MOTIVO: Laje técnica sem laudo de rompimento fck 28d.</div>
                            </div>

                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- DOBRA 2: BENTO BOX TESE -->
        <section id="tese" class="max-w-7xl mx-auto border-b border-grid border-x border-x-grid bg-carbon">
            <div class="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-grid">
                
                <div class="p-8 space-y-4">
                    <div class="font-mono text-forense text-xs uppercase tracking-widest border border-forense/20 bg-forense/5 px-2 py-1 inline-block mb-2">01. O Sintoma Cego</div>
                    <h3 class="font-display text-xl text-titanium">A Incerteza (A Dor)</h3>
                    <p class="text-sm text-slate leading-relaxed">O problema apresentado quase nunca é o problema real. Você vê o atraso, a medição retida ou o orçamento estourado. A engenharia tradicional analisa &lt;5% por amostragem, deixando a causa raiz escondida na interface entre projeto, equipe, material e contrato.</p>
                </div>

                <div class="p-8 space-y-4 relative overflow-hidden group">
                    <div class="absolute inset-0 bg-sentinela/5 translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
                    <div class="relative z-10">
                        <div class="font-mono text-sentinela text-xs uppercase tracking-widest border border-sentinela/20 bg-sentinela/5 px-2 py-1 inline-block mb-2">02. A Execução</div>
                        <h3 class="font-display text-xl text-titanium">O Método Sentinela</h3>
                        <ul class="text-sm text-slate space-y-2 mt-2 font-mono">
                            <li class="flex items-start"><span class="text-sentinela mr-2">></span> Ingestão de 100% dos Dados Brutos</li>
                            <li class="flex items-start"><span class="text-sentinela mr-2">></span> Motor SINAPI/SICRO em Python</li>
                            <li class="flex items-start"><span class="text-sentinela mr-2">></span> Matriz Forense: RDO vs. INMET</li>
                            <li class="flex items-start"><span class="text-sentinela mr-2">></span> Auditoria XML vs. BIM 5D</li>
                        </ul>
                    </div>
                </div>

                <div class="p-8 space-y-4">
                    <div class="font-mono text-prova text-xs uppercase tracking-widest border border-prova/20 bg-prova/5 px-2 py-1 inline-block mb-2">03. O Veredito</div>
                    <h3 class="font-display text-xl text-titanium">A Prova Material</h3>
                    <p class="text-sm text-slate leading-relaxed">Você não recebe relatórios verbais. Você recebe um Dossiê Forense com números cravados, roteiro de negociação item a item, memória de glosa financeira e Anotação de Responsabilidade Técnica (ART) pronta para a mesa da diretoria ou do juiz.</p>
                </div>

            </div>
        </section>

        <!-- DOBRA 3: OS 3 PRODUTOS CHEFE -->
        <section id="produtos" class="max-w-7xl mx-auto px-4 py-16 md:py-24 border-b border-grid">
            <div class="mb-12">
                <h2 class="font-display text-3xl text-titanium mb-2">Engenharia de Intervenção</h2>
                <p class="text-slate font-mono text-sm uppercase">Motores de Tração [Os 3 Produtos-Chefe]</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="group border border-grid bg-carbon p-6 flex flex-col hover:border-sentinela transition-colors duration-300 relative overflow-hidden">
                    <div class="font-mono text-[10px] text-sentinela uppercase tracking-widest mb-4 border-b border-grid pb-2">Chefe 01 // Pré-Contratação</div>
                    <h3 class="font-display text-xl text-titanium mb-3">Raio-X Sentinela de Propostas e Orçamentos</h3>
                    <p class="text-sm text-slate mb-6 flex-grow">Para quem recebeu propostas de construtoras e tem dúvida se o preço é justo. Varredura integral no SINAPI-ES identificando sobrepreços na Curva A.</p>
                    <div class="space-y-2 font-mono text-xs text-slate border-t border-grid pt-4">
                        <div class="flex justify-between"><span class="text-titanium">Ticket:</span> <span>R$ 5.8k a 8.9k</span></div>
                        <div class="flex justify-between"><span class="text-titanium">Entrega:</span> <span class="group-hover:text-sentinela transition-colors">72h Úteis</span></div>
                        <div class="flex justify-between"><span class="text-titanium">ID:</span> <span>[P05A]</span></div>
                    </div>
                </div>

                <div class="group border border-grid bg-carbon p-6 flex flex-col hover:border-sentinela transition-colors duration-300 relative overflow-hidden">
                    <div class="font-mono text-[10px] text-sentinela uppercase tracking-widest mb-4 border-b border-grid pb-2">Chefe 02 // Crise & Destrave</div>
                    <h3 class="font-display text-xl text-titanium mb-3">Diagnóstico Forense de Contrato e Pleitos</h3>
                    <p class="text-sm text-slate mb-6 flex-grow">Para contratos com medição travada, atraso, risco de multa ou cobrança de aditivo. Confronto matemático de RDO × INMET × Contrato.</p>
                    <div class="space-y-2 font-mono text-xs text-slate border-t border-grid pt-4">
                        <div class="flex justify-between"><span class="text-titanium">Ticket:</span> <span>R$ 12.5k a 18k</span></div>
                        <div class="flex justify-between"><span class="text-titanium">Entrega:</span> <span class="group-hover:text-sentinela transition-colors">5 a 10 Dias</span></div>
                        <div class="flex justify-between"><span class="text-titanium">ID:</span> <span>[P01+]</span></div>
                    </div>
                </div>

                <div class="group border border-grid bg-carbon p-6 flex flex-col hover:border-sentinela transition-colors duration-300 relative overflow-hidden">
                    <div class="font-mono text-[10px] text-sentinela uppercase tracking-widest mb-4 border-b border-grid pb-2">Chefe 03 // Obra Viva</div>
                    <h3 class="font-display text-xl text-titanium mb-3">Planejamento & Verificação de Medição</h3>
                    <p class="text-sm text-slate mb-6 flex-grow">Para garantir que o combinado saia no prazo e reter pagamentos sem comprovação. Boletim mensal com glosa preventiva e Hold Points digitais.</p>
                    <div class="space-y-2 font-mono text-xs text-slate border-t border-grid pt-4">
                        <div class="flex justify-between"><span class="text-titanium">Ticket:</span> <span>R$ 4.9k a 6.5k/mês</span></div>
                        <div class="flex justify-between"><span class="text-titanium">Frequência:</span> <span class="group-hover:text-sentinela transition-colors">Mensal</span></div>
                        <div class="flex justify-between"><span class="text-titanium">ID:</span> <span>[P06+]</span></div>
                    </div>
                </div>
            </div>
        </section>

        <!-- DOBRA 4: MATRIZ DE PORTFÓLIO (12 PRODUTOS) -->
        <section id="portfolio" class="max-w-7xl mx-auto px-4 py-16 border-b border-grid">
            <div class="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 class="font-display text-2xl text-titanium mb-1">Matriz Operacional Completa</h2>
                    <p class="text-slate text-sm">Painel de 12 soluções por estágio do contrato e ciclo de vida do ativo.</p>
                </div>
                <div class="font-mono text-[10px] text-sentinela border border-sentinela/30 px-3 py-1 bg-carbon">
                    [ ACERVO TÉCNICO: CRIVIA ]
                </div>
            </div>

            <div class="flex overflow-x-auto border-b border-grid font-mono text-xs uppercase text-slate mb-8 scrollbar-hide">
                <button class="matrix-tab px-6 py-3 border-b-2 border-sentinela text-titanium whitespace-nowrap" data-target="fase1">Fase 1: Viabilidade</button>
                <button class="matrix-tab px-6 py-3 border-b-2 border-transparent hover:text-titanium whitespace-nowrap" data-target="fase2">Fase 2: Obra Viva</button>
                <button class="matrix-tab px-6 py-3 border-b-2 border-transparent hover:text-titanium whitespace-nowrap" data-target="fase3">Fase 3: Crise & Litígio</button>
                <button class="matrix-tab px-6 py-3 border-b-2 border-transparent hover:text-titanium whitespace-nowrap" data-target="fase4">Fase 4: Entrega & IA</button>
            </div>

            <div class="relative min-h-[200px]">
                
                <div id="fase1" class="matrix-content grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="border border-grid p-4 bg-carbon"><div class="text-sentinela font-mono text-[10px] mb-2">[P05A]</div><h4 class="text-titanium text-sm font-semibold mb-1">Raio-X de Orçamentos SINAPI</h4><p class="text-xs text-slate">Confronto de Curva A.</p></div>
                    <div class="border border-grid p-4 bg-carbon"><div class="text-slate font-mono text-[10px] mb-2">[P01-DD]</div><h4 class="text-titanium text-sm font-semibold mb-1">Due Diligence de Áreas</h4><p class="text-xs text-slate">Avaliação expressa de passivos pré-aquisição.</p></div>
                    <div class="border border-grid p-4 bg-carbon"><div class="text-slate font-mono text-[10px] mb-2">[P03]</div><h4 class="text-titanium text-sm font-semibold mb-1">Auditoria BIM 5D</h4><p class="text-xs text-slate">Compatibilização via BlenderBIM.</p></div>
                    <div class="border border-grid p-4 bg-carbon"><div class="text-slate font-mono text-[10px] mb-2">[P02]</div><h4 class="text-titanium text-sm font-semibold mb-1">Eng. de Contratação</h4><p class="text-xs text-slate">Blindagem de escopo técnico.</p></div>
                </div>

                <div id="fase2" class="matrix-content hidden grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="border border-grid p-4 bg-carbon"><div class="text-sentinela font-mono text-[10px] mb-2">[P06+]</div><h4 class="text-titanium text-sm font-semibold mb-1">Planejamento Pactuado</h4><p class="text-xs text-slate">Verificação mensal de medição.</p></div>
                    <div class="border border-grid p-4 bg-carbon"><div class="text-slate font-mono text-[10px] mb-2">[P09]</div><h4 class="text-titanium text-sm font-semibold mb-1">Forense de Suprimentos (XML)</h4><p class="text-xs text-slate">Leitura em lote de notas fiscais SEFAZ.</p></div>
                    <div class="border border-grid p-4 bg-carbon"><div class="text-slate font-mono text-[10px] mb-2">[P04]</div><h4 class="text-titanium text-sm font-semibold mb-1">Fiscalização 360°</h4><p class="text-xs text-slate">Varredura visual imersiva mensal.</p></div>
                    <div class="border border-grid p-4 bg-carbon"><div class="text-slate font-mono text-[10px] mb-2">[CV01]</div><h4 class="text-titanium text-sm font-semibold mb-1">Comunicação Visual 3D</h4><p class="text-xs text-slate">Tradução técnica para diretoria.</p></div>
                </div>

                <div id="fase3" class="matrix-content hidden grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div class="border border-grid p-4 bg-carbon"><div class="text-sentinela font-mono text-[10px] mb-2">[P01+]</div><h4 class="text-titanium text-sm font-semibold mb-1">Diagnóstico Sentinela Forense</h4><p class="text-xs text-slate">Destrave de obra (RDO x INMET).</p></div>
                    <div class="border border-grid p-4 bg-carbon"><div class="text-slate font-mono text-[10px] mb-2">[P05B]</div><h4 class="text-titanium text-sm font-semibold mb-1">Defesa Anti-Claim Pericial</h4><p class="text-xs text-slate">Desconstituição matemática de pleitos.</p></div>
                    <div class="border border-grid p-4 bg-carbon"><div class="text-slate font-mono text-[10px] mb-2">[P10]</div><h4 class="text-titanium text-sm font-semibold mb-1">Licitações Lei 14.133</h4><p class="text-xs text-slate">Impugnação de editais e viabilidade técnica.</p></div>
                </div>

                <div id="fase4" class="matrix-content hidden grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div class="border border-grid p-4 bg-carbon"><div class="text-slate font-mono text-[10px] mb-2">[P11/P12]</div><h4 class="text-titanium text-sm font-semibold mb-1">Recebimento Definitivo</h4><p class="text-xs text-slate">Comissionamento técnico e Punch-List.</p></div>
                    <div class="border border-grid p-4 bg-carbon"><div class="text-slate font-mono text-[10px] mb-2">[P06-R]</div><h4 class="text-titanium text-sm font-semibold mb-1">Reforma Exata com Drone</h4><p class="text-xs text-slate">Inspeção térmica e fotogrametria (WebODM).</p></div>
                    <div class="border border-grid p-4 bg-carbon"><div class="text-slate font-mono text-[10px] mb-2">[IA]</div><h4 class="text-titanium text-sm font-semibold mb-1">Decisão com IA P/ Equipes</h4><p class="text-xs text-slate">Estruturação de engenharia interna.</p></div>
                </div>

            </div>
        </section>

        <!-- DOBRA 5: GOVERNANÇA E BLINDAGEM -->
        <section class="max-w-7xl mx-auto px-4 py-16 border-b border-grid bg-obsidian">
            <div class="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
                <div class="md:col-span-4 lg:col-span-3">
                    <div class="w-full aspect-square border border-grid bg-carbon relative flex items-center justify-center overflow-hidden grayscale">
                        <div class="absolute inset-0 bg-gradient-to-tr from-obsidian via-carbon to-slate/10"></div>
                        <span class="font-mono text-slate text-xs relative z-10">[ IDENTIDADE: B. MALTA ]<br>Eng. Produção Civil</span>
                    </div>
                </div>
                
                <div class="md:col-span-8 lg:col-span-9 space-y-6">
                    <div>
                        <h2 class="font-display text-2xl text-titanium mb-2">Quem Assina a Prova Técnica</h2>
                        <p class="text-slate text-sm leading-relaxed max-w-3xl">
                            Com mais de 30 anos de trajetória — da manutenção de aeronaves em 1996 à gerência de grandes obras industriais —, <strong>Bruno Malta</strong> construiu uma carreira focada na resolução de problemas onde ninguém mais queria assumir o risco. A CRIVIA nasceu dessa bagagem: o hábito inegociável de voltar ao manual, respeitar a premissa e separar a causa do sintoma.
                        </p>
                    </div>

                    <div class="inline-flex flex-col sm:flex-row items-start sm:items-center gap-4 border border-grid bg-carbon p-4">
                        <div class="w-10 h-10 flex items-center justify-center border border-sentinela/30 bg-sentinela/10 text-sentinela shrink-0">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                        </div>
                        <div>
                            <h4 class="text-titanium text-sm font-semibold font-mono tracking-tight uppercase">Selo de Independência (Art. 618 CC)</h4>
                            <p class="text-xs text-slate">A CRIVIA atua com <strong>escopo não-executivo</strong>. Não construímos, não vendemos materiais e não possuímos conflito de interesse. Nosso compromisso é exclusivo com a defesa do caixa e a verdade técnica do nosso cliente.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- DOBRA 6: TRIAGEM E CONVERSÃO -->
        <section id="triagem" class="max-w-7xl mx-auto px-4 py-20 lg:py-32">
            <div class="max-w-3xl mx-auto border border-grid bg-carbon p-6 md:p-10 shadow-2xl relative">
                <div class="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-[1px] bg-prova shadow-[0_0_15px_#10B981]"></div>
                
                <div class="text-center mb-8">
                    <h2 class="font-display text-2xl text-titanium">Terminal de Triagem de Caso</h2>
                    <p class="text-sm text-slate font-mono mt-2">Configure os parâmetros abaixo para gerar seu diagnóstico de 20 minutos.</p>
                </div>

                <div class="space-y-8">
                    <div>
                        <span class="block text-xs font-mono text-sentinela uppercase mb-3">> 1. Defina sua Posição Contratual:</span>
                        <div class="flex flex-col sm:flex-row gap-3">
                            <input type="radio" name="perfil" id="p_empreiteira" value="Dono de Empreiteira" class="triage-radio hidden" checked>
                            <label for="p_empreiteira" class="flex-1 border border-grid text-slate text-sm text-center py-3 cursor-pointer hover:border-sentinela transition-colors font-mono">Empreiteira / Prestador</label>
                            
                            <input type="radio" name="perfil" id="p_dono" value="Dono de Indústria ou Galpão" class="triage-radio hidden">
                            <label for="p_dono" class="flex-1 border border-grid text-slate text-sm text-center py-3 cursor-pointer hover:border-sentinela transition-colors font-mono">Indústria / Galpão / Clínica</label>
                            
                            <input type="radio" name="perfil" id="p_parceiro" value="Advogado ou Contador parceiro" class="triage-radio hidden">
                            <label for="p_parceiro" class="flex-1 border border-grid text-slate text-sm text-center py-3 cursor-pointer hover:border-sentinela transition-colors font-mono">Advogado / Contador</label>
                        </div>
                    </div>

                    <div>
                        <span class="block text-xs font-mono text-sentinela uppercase mb-3">> 2. Qual é a causa da Incerteza hoje?</span>
                        <div class="flex flex-col gap-3">
                            <input type="radio" name="dor" id="d_orcamento" value="avaliar propostas de construtoras e orçamentos" class="triage-radio hidden" checked>
                            <label for="d_orcamento" class="w-full border border-grid text-slate text-sm py-3 px-4 cursor-pointer hover:border-sentinela transition-colors flex items-center">
                                <span class="w-2 h-2 bg-slate rounded-full mr-3 indicator"></span> Tenho planilhas e propostas para auditar antes de assinar.
                            </label>

                            <input type="radio" name="dor" id="d_travada" value="destravar medições e analisar o atraso da obra" class="triage-radio hidden">
                            <label for="d_travada" class="w-full border border-grid text-slate text-sm py-3 px-4 cursor-pointer hover:border-sentinela transition-colors flex items-center">
                                <span class="w-2 h-2 bg-slate rounded-full mr-3 indicator"></span> Minha obra atrasou, a medição travou ou estou perdendo margem.
                            </label>

                            <input type="radio" name="dor" id="d_pleito" value="analisar uma disputa técnica de aditivo ou multa" class="triage-radio hidden">
                            <label for="d_pleito" class="w-full border border-grid text-slate text-sm py-3 px-4 cursor-pointer hover:border-sentinela transition-colors flex items-center">
                                <span class="w-2 h-2 bg-slate rounded-full mr-3 indicator"></span> Estou sofrendo cobrança de aditivo abusivo ou risco de multa.
                            </label>
                        </div>
                    </div>

                    <div class="pt-4 border-t border-grid text-center">
                        <a id="btn-whatsapp" href="#" target="_blank" class="inline-block bg-prova text-obsidian font-display font-semibold px-8 py-4 text-center hover:bg-emerald-400 transition-colors w-full sm:w-auto shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                            [ INICIAR SESSÃO DIAGNÓSTICA ]
                        </a>
                        <p class="text-xs text-slate mt-4 font-mono opacity-70">A triagem dura 20 minutos e ocorre na tela do computador via call.</p>
                    </div>
                </div>
            </div>
        </section>

    </main>

    <!-- FOOTER -->
    <footer class="border-t border-grid bg-obsidian py-8">
        <div class="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4">
            <div class="text-slate text-xs font-mono">
                © 2026 CRIVIA Engenharia Consultiva Ltda.<br>
                Serra / Vitória - ES
            </div>
            <div class="text-slate text-xs font-mono text-center md:text-right">
                Zero Data Retention (LGPD Compliant).<br>
                Nenhum dado trafegado é utilizado para treinamento.
            </div>
        </div>
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            // 1. Lógica das Abas do Terminal Hero
            const termTabs = document.querySelectorAll('.term-tab');
            const termContents = document.querySelectorAll('.term-content');

            termTabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    termTabs.forEach(t => {
                        t.classList.remove('text-sentinela', 'border-b-sentinela');
                        t.classList.add('border-b-transparent', 'hover:text-titanium');
                    });
                    termContents.forEach(c => c.classList.add('hidden'));

                    tab.classList.remove('border-b-transparent', 'hover:text-titanium');
                    tab.classList.add('text-sentinela', 'border-b-sentinela');
                    const target = document.getElementById(tab.getAttribute('data-target'));
                    if(target) target.classList.remove('hidden');
                });
            });

            // 2. Lógica da Matriz Completa de 12 Produtos
            const matrixTabs = document.querySelectorAll('.matrix-tab');
            const matrixContents = document.querySelectorAll('.matrix-content');

            matrixTabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    matrixTabs.forEach(t => {
                        t.classList.remove('border-sentinela', 'text-titanium');
                        t.classList.add('border-transparent', 'hover:text-titanium');
                    });
                    matrixContents.forEach(c => c.classList.add('hidden'));

                    tab.classList.remove('border-transparent', 'hover:text-titanium');
                    tab.classList.add('border-sentinela', 'text-titanium');
                    const target = document.getElementById(tab.getAttribute('data-target'));
                    if(target) target.classList.remove('hidden');
                });
            });

            // 3. Lógica do Configurador Dinâmico de WhatsApp
            const radios = document.querySelectorAll('.triage-radio');
            const btnWhatsapp = document.getElementById('btn-whatsapp');
            const WHATSAPP_NUMBER = "5527996971800";

            function updateWhatsappLink() {
                const perfil = document.querySelector('input[name="perfil"]:checked').value;
                const dor = document.querySelector('input[name="dor"]:checked').value;
                
                const message = `Olá, Bruno! Sou ${perfil} e estou precisando ${dor}. Gostaria de agendar a sessão de triagem técnica de 20 minutos com a Crivia.`;
                
                btnWhatsapp.href = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;

                document.querySelectorAll('input[name="dor"]').forEach(input => {
                    const indicator = input.nextElementSibling.querySelector('.indicator');
                    if(input.checked) {
                        indicator.classList.remove('bg-slate');
                        indicator.classList.add('bg-obsidian');
                    } else {
                        indicator.classList.add('bg-slate');
                        indicator.classList.remove('bg-obsidian');
                    }
                });
            }

            radios.forEach(radio => radio.addEventListener('change', updateWhatsappLink));
            updateWhatsappLink();
        });
    </script>
</body>
</html>
"""


def construir():
    """Gera o site completo na pasta site/."""
    if SAIDA.exists():
        import shutil
        # Segurança: só apaga se for a pasta site/ dentro do repositório
        if SAIDA.parent == REPO and SAIDA.name == "site":
            shutil.rmtree(SAIDA)
    
    SAIDA.mkdir(parents=True, exist_ok=True)
    
    html_file = SAIDA / "index.html"
    html_file.write_text(HTML_CONTENT, encoding="utf-8")
    print(f"[CRIVIA] Página gerada: {html_file}")
    print(f"[CRIVIA] Tamanho: {html_file.stat().st_size:,} bytes")
    return html_file


def servir(porta=8080, abrir_navegador=True):
    """Inicia servidor HTTP local com fallback de porta."""
    os.chdir(SAIDA)
    
    socketserver.TCPServer.allow_reuse_address = True
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Fallback de porta
    for tentativa in range(10):
        try:
            httpd = socketserver.TCPServer(("", porta), Handler)
            break
        except OSError:
            print(f"[CRIVIA] Porta {porta} ocupada, tentando {porta + 1}...")
            porta += 1
    else:
        print("[CRIVIA] ERRO: Nenhuma porta disponível entre 8080 e 8089.")
        sys.exit(1)
    
    url = f"http://localhost:{porta}"
    print(f"[CRIVIA] Servidor ativo em {url}")
    print(f"[CRIVIA] Pressione Ctrl+C para encerrar.")
    
    if abrir_navegador:
        webbrowser.open(url)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[CRIVIA] Servidor encerrado.")
        httpd.shutdown()


def main():
    parser = argparse.ArgumentParser(
        description="CRIVIA — Construtor e servidor do site de Engenharia Consultiva"
    )
    parser.add_argument("--build-only", action="store_true",
                        help="Só gera os arquivos em site/, sem servir")
    parser.add_argument("--no-browser", action="store_true",
                        help="Serve sem abrir o navegador automaticamente")
    parser.add_argument("--port", type=int, default=8080,
                        help="Porta do servidor local (padrão: 8080)")
    
    args = parser.parse_args()
    
    print("[CRIVIA] ═══════════════════════════════════════════")
    print("[CRIVIA] CRIVIA — Engenharia para Decisão")
    print("[CRIVIA] Construindo site...")
    print("[CRIVIA] ═══════════════════════════════════════════")
    
    construir()
    
    if args.build_only:
        print(f"[CRIVIA] Build completo. Abra: {SAIDA / 'index.html'}")
        return
    
    servir(porta=args.port, abrir_navegador=not args.no_browser)


if __name__ == "__main__":
    main()
