(() => {
  const root = document.documentElement;
  const body = document.body;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  /* ───────── ponteiro, marca e campo de partículas ───────── */
  let pointerX = innerWidth * .65;
  let pointerY = innerHeight * .42;
  window.addEventListener('pointermove', (event) => {
    pointerX = event.clientX;
    pointerY = event.clientY;
    root.style.setProperty('--pointer-x', `${(pointerX / innerWidth) * 100}%`);
    root.style.setProperty('--pointer-y', `${(pointerY / innerHeight) * 100}%`);
  }, { passive: true });

  const heroLogoStage = document.querySelector('.hero-logo-stage');
  heroLogoStage.addEventListener('pointermove', (event) => {
    if (reducedMotion) return;
    const bounds = heroLogoStage.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width - .5;
    const y = (event.clientY - bounds.top) / bounds.height - .5;
    heroLogoStage.style.setProperty('--logo-rx', `${(-y * 7).toFixed(2)}deg`);
    heroLogoStage.style.setProperty('--logo-ry', `${(x * 9).toFixed(2)}deg`);
  }, { passive: true });
  heroLogoStage.addEventListener('pointerleave', () => {
    heroLogoStage.style.setProperty('--logo-rx', '0deg');
    heroLogoStage.style.setProperty('--logo-ry', '0deg');
  });

  const canvas = document.querySelector('#field');
  const ctx = canvas.getContext('2d');
  let particles = [];
  let width = 0;
  let height = 0;
  let running = true;

  const seedParticles = () => {
    const count = Math.min(95, Math.max(36, Math.floor(width / 17)));
    particles = Array.from({ length: count }, (_, index) => ({
      x: Math.random() * width, y: Math.random() * height,
      vx: (Math.random() - .5) * (.12 + (index % 5) * .015), vy: (Math.random() - .5) * .12,
      r: Math.random() * 1.25 + .3, a: Math.random() * .42 + .12
    }));
  };
  const resizeCanvas = () => {
    width = innerWidth; height = innerHeight;
    const dpr = Math.min(devicePixelRatio || 1, 1.6);
    canvas.width = Math.floor(width * dpr); canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`; canvas.style.height = `${height}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    seedParticles();
  };
  const drawField = (time = 0) => {
    if (!running) return;
    ctx.clearRect(0, 0, width, height);
    const pulse = (Math.sin(time * .00045) + 1) / 2;
    for (let i = 0; i < particles.length; i += 1) {
      const p = particles[i];
      const dx = pointerX - p.x, dy = pointerY - p.y, distance = Math.hypot(dx, dy);
      if (distance < 150 && distance > 1) { p.x -= (dx / distance) * .13; p.y -= (dy / distance) * .13; }
      p.x += p.vx; p.y += p.vy;
      if (p.x < -5) p.x = width + 5; if (p.x > width + 5) p.x = -5;
      if (p.y < -5) p.y = height + 5; if (p.y > height + 5) p.y = -5;
      ctx.beginPath(); ctx.fillStyle = `rgba(89,220,255,${p.a + pulse * .08})`; ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
      for (let j = i + 1; j < particles.length; j += 1) {
        const q = particles[j], span = Math.hypot(p.x - q.x, p.y - q.y);
        if (span < 82) { ctx.beginPath(); ctx.strokeStyle = `rgba(44,174,235,${(1 - span / 82) * .085})`; ctx.lineWidth = .55; ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke(); }
      }
    }
    requestAnimationFrame(drawField);
  };
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas, { passive: true });
  if (!reducedMotion) requestAnimationFrame(drawField);
  // pausa o campo quando a aba está escondida
  document.addEventListener('visibilitychange', () => {
    running = !document.hidden;
    if (running && !reducedMotion) requestAnimationFrame(drawField);
  });

  /* ───────── progresso, capítulos e menu ───────── */
  const chapters = [...document.querySelectorAll('.chapter')];
  const navLinks = [...document.querySelectorAll('.masthead nav a[href^="#"]')];
  const railCurrent = document.querySelector('.chapter-rail b');
  const navFor = { 'produto-2': 'produto-1', 'produto-3': 'produto-1', inicio: null, contato: null };

  const onScroll = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    const progress = max > 0 ? scrollY / max : 0;
    root.style.setProperty('--scroll', progress.toFixed(4));
    root.style.setProperty('--page-progress', progress.toFixed(4));
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  const chapterObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const id = entry.target.id;
      railCurrent.textContent = entry.target.dataset.chapter || '00';
      const alvo = id in navFor ? navFor[id] : id;
      navLinks.forEach((link) => link.classList.toggle('is-active', alvo !== null && link.getAttribute('href') === `#${alvo}`));
    });
  }, { rootMargin: '-34% 0px -48% 0px', threshold: 0 });
  chapters.forEach((chapter) => chapterObserver.observe(chapter));

  const menuButton = document.querySelector('.menu-toggle');
  menuButton.addEventListener('click', () => {
    const open = body.classList.toggle('menu-open');
    menuButton.setAttribute('aria-expanded', String(open));
  });
  navLinks.forEach((link) => link.addEventListener('click', () => {
    body.classList.remove('menu-open');
    menuButton.setAttribute('aria-expanded', 'false');
  }));
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    body.classList.remove('menu-open');
    menuButton.setAttribute('aria-expanded', 'false');
  });

  /* ───────── dados dos três trabalhos (valores de EXEMPLO ILUSTRATIVO, do Mostruário de Dossiês) ───────── */
  const TONS = {
    azul: { f: ['#4C7BE6', '#1B47B0'], t: '#8DB0F5', s: '#10307F' },
    ouro: { f: ['#F6C65A', '#C98F10'], t: '#FCE6A6', s: '#9A6D08' },
    bom: { f: ['#47BEDB', '#15809F'], t: '#9BE0F0', s: '#0D5D77' },
    aviso: { f: ['#93AACE', '#5C78A8'], t: '#C9D7EC', s: '#415B84' }
  };
  const brl = (v) => (v < 0 ? '− ' : '') + 'R$ ' + Math.abs(v).toLocaleString('pt-BR');
  const abrev = (v, sinal) => {
    const a = Math.abs(v), s = sinal ? (v < 0 ? '− ' : '+ ') : '';
    return s + (a >= 1e6 ? (a / 1e6).toFixed(2).replace('.', ',') + ' mi' : Math.round(a / 1000) + ' mil');
  };

  const LABS = {
    raiox: {
      quando: 'ANTES DE CONTRATAR', nome: 'Raio-X de Propostas e Orçamentos',
      kpis: [['Proposta', 'R$ 3.450.000', '', ''], ['Valor de referência técnica', 'R$ 2.978.400', '', ''], ['Diferença frente à referência', '+ R$ 471.600', 'ouro', '+15,8% (estimada)']],
      ponte: { base: 2900000, topo: 3500000, eixo: 'Eixo a partir de R$ 2,9 mi. Passe o cursor sobre as barras.', passos: [
        ['Referência técnica', 2978400, 'total', 'azul', 'Valor de referência técnica: SINAPI-ES com BDI de 25% para esta obra.'],
        ['Aço', 111000, 'delta', 'ouro', 'Armação CA-50, 18.500 kg: R$ 21,50 por kg na proposta contra R$ 15,50 na referência (diferença estimada de +38,7%).'],
        ['Concreto', 76928, 'delta', 'ouro', 'Concreto usinado fck 30 MPa, 680 m³: R$ 720,00 por m³ contra R$ 606,87 (diferença estimada de +18,6%).'],
        ['Estrutura', 75000, 'delta', 'ouro', 'Estrutura metálica da cobertura, 55.000 kg: R$ 12,45 por kg contra R$ 11,09 (diferença estimada de +12,3%).'],
        ['Piso', 14000, 'delta', 'aviso', 'Piso industrial polido, 2.800 m²: dentro da faixa de referência (+3,5%).'],
        ['Escavação', -51500, 'delta', 'bom', '7.900 m³ a R$ 12,02 contra R$ 18,54 (−35,1%). Preço abaixo da referência pode ensejar pedido de aditivo depois.'],
        ['Demais itens', 246172, 'delta', 'ouro', 'Diferença que sobra entre os itens críticos acima e o total da diferença estimada.'],
        ['Proposta', 3450000, 'total', 'azul', 'Valor total proposto pela empreiteira.'] ] },
      linhas: [
        ['Possível omissão identificada na análise', 'Subestação aérea de 150 kVA prevista no projeto elétrico e ausente da proposta', '≈ R$ 92.000', 'RISCO DE ADITIVO', 'ouro'],
        ['Escavação cotada 35,1% abaixo da referência', 'Preço abaixo da referência pode abrir espaço para pedido de aditivo de volume (hipótese a confirmar)', '− R$ 51.500', 'PREÇO ABAIXO DA REFERÊNCIA', 'bom']],
      como: { para: 'Donos de obra privada e empreiteiras que estão orçando serviços.', envia: 'A planilha da proposta em Excel (.xlsx).',
        passos: ['Os itens definidos no escopo, com prioridade para a Curva A, são pareados com referências técnicas como o SINAPI.', 'O BDI é aplicado e a Curva ABC mostra onde se concentra a maior parte do valor da proposta.', 'Itens acima ou abaixo da referência e possíveis omissões são sinalizados para avaliação.'],
        recebe: ['Dossiê de 5 páginas', 'Gráfico comparativo e tabela da Curva A, em vermelho e verde', 'Roteiro de pontos de negociação para levar à reunião, a critério do cliente'] },
      fonte: 'Galpão de 2.800 m², Serra/ES. Referência SINAPI-ES com BDI de 25%. Diferenças estimadas, sujeitas a escopo, data-base, BDI, especificações e condições de contratação.'
    },
    sentinela: {
      quando: 'QUANDO A OBRA TRAVA', nome: 'Diagnóstico Sentinela',
      kpis: [['Aditivo cobrado', 'R$ 485.000', '', ''], ['Valor recomendado para avaliação', 'R$ 74.200', 'bom', ''], ['Diferença entre o pleito e o valor recomendado', 'R$ 410.800', 'bom', '84,7%']],
      ponte: { base: 0, topo: 500000, eixo: 'Passe o cursor sobre as barras para ver a justificativa técnica de cada ajuste recomendado.', passos: [
        ['Cobrado', 485000, 'total', 'azul', 'Valor do aditivo cobrado pela empreiteira, com percentuais lineares e sem comprovação contábil no conjunto documental disponível.'],
        ['Chuva', -130400, 'delta', 'bom', '26,9% do pleito. Dias de chuva alegados sem registro de chuva no satélite INMET (16 de 22 dias com 0,0 mm). Diferença técnica sob análise.'],
        ['Mão de obra', -192600, 'delta', 'bom', '39,7% do pleito. Os diários assinados indicam equipe realocada para o pátio, com produção normal.'],
        ['Adm. local', -87800, 'delta', 'bom', '18,1% do pleito. Cálculo aparenta não acompanhar o avanço da obra (hipótese a confirmar).'],
        ['Valor recomendado', 74200, 'total', 'ouro', 'Valor recomendado para avaliação: 15,3% do pleito. Base para o acordo técnico, sujeita à decisão do cliente e, quando necessário, a apoio jurídico.'] ] },
      linhas: [
        ['12/08 a 16/08 · pleito alega chuva intensa', 'Satélite INMET: 0,0 a 1,8 mm · fora do caminho crítico · diário: 8 operários (32 cobrados)', 'R$ 68.400', 'EVIDÊNCIA INSUFICIENTE PARA SUSTENTAR O PLEITO', 'ouro'],
        ['24/09 a 04/10 · erro de furação nos chumbadores', 'Satélite INMET: 0,0 mm · no caminho crítico · diário: 14 operários em retrabalho', 'R$ 74.200', 'EVIDÊNCIA COMPATÍVEL COM O PLEITO', 'bom']],
      como: { para: 'Obras atrasadas, empreiteiras com medição reduzida pelo contratante e advogados que defendem empresas contra aditivos e multas.', envia: 'Diários de obra escaneados, contrato com cronograma e a notificação do pleito.',
        passos: ['A chuva real do período é buscada na base do INMET.', 'Os diários são lidos e confrontados com o cronograma.', 'As alegações do pleito são comparadas com as evidências de campo disponíveis.'],
        recebe: ['Linha do tempo com alegação, chuva medida, caminho crítico e realidade do diário', 'Análise técnica por período, fundamentada nas evidências disponíveis', 'Diferença técnica sob análise e valor recomendado para avaliação', 'Recomendação técnica: acordo, pagamento ou glosa dependem do decisor e, quando necessário, de apoio jurídico'] },
      fonte: 'Ampliação industrial, Linhares/ES. Fontes: diários de obra, INMET e contrato.'
    },
    medicao: {
      quando: 'DURANTE A EXECUÇÃO', nome: 'Planejamento e Medição',
      kpis: [['Cobrado, medição nº 04', 'R$ 280.000', '', ''], ['Valor com evidência verificada', 'R$ 235.000', 'bom', ''], ['Diferença sob análise', '− R$ 45.000', 'ouro', 'Recomendação técnica: liberação parcial, sujeita à decisão do cliente']],
      curva: true,
      linhas: [
        ['Divisórias drywall, 3º pavimento', 'Cobrado 100% · evidência verificada 70% · fechamento de lã de rocha não evidenciado', '− R$ 25.500', 'PONTO DE CONTROLE', 'ouro'],
        ['Laje técnica da cobertura', 'Cobrado 100% · evidência verificada 79,5% · aguarda laudo de rompimento', '− R$ 19.500', 'NOVA VERIFICAÇÃO', 'aviso'],
        ['Radar de 30 dias · decisão do cliente até 13/11', 'Compra do quadro geral e do transformador (prazo de fábrica de 45 dias)', '', 'CRÍTICO', 'ouro']],
      como: { para: 'Quem já contratou a obra e não quer voltar à incerteza.', envia: 'A planilha de medição da construtora, numa data de corte fixa (por exemplo, dia 25).',
        passos: ['Inspeção visual focada nos itens definidos no escopo, com fotos.', 'O que foi visto é cruzado com a planilha de medição.', 'Para os itens analisados, a CRIVIA recomenda condições técnicas de liberação, retenção ou nova verificação.'],
        recebe: ['Boletim de 4 páginas', 'Recomendação técnica de liberação ou retenção segundo os critérios definidos, com a Curva S', 'Radar dos suprimentos críticos dos próximos 30 dias e os documentos que devem embasar a decisão de pagamento'] },
      fonte: 'Edifício comercial e clínica, Vitória/ES.'
    }
  };

  /* ───────── gráficos ───────── */
  const ponteSvg = (id, g) => {
    const n = g.passos.length, W = 600, H = 214, L = 6, R = 14, T = 34, B = 30;
    const bw = (W - L - R) / n, pw = bw * .58, dx = Math.min(11, pw * .2), dy = dx * .6;
    const y = (v) => T + (H - T - B) * (1 - (v - g.base) / (g.topo - g.base));
    const defs = Object.keys(TONS).map((k) => `<linearGradient id="${id}-f-${k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${TONS[k].f[0]}"/><stop offset="1" stop-color="${TONS[k].f[1]}"/></linearGradient><linearGradient id="${id}-s-${k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${TONS[k].s}"/><stop offset="1" stop-color="${TONS[k].s}" stop-opacity=".78"/></linearGradient>`).join('');
    let grade = '';
    [0.25, 0.5, 0.75, 1].forEach((q) => { const yy = T + (H - T - B) * q; grade += `<line x1="${L}" x2="${W - R}" y1="${yy}" y2="${yy}" stroke="#7C93C4" stroke-opacity="${q === 1 ? .55 : .2}" ${q === 1 ? '' : 'stroke-dasharray="2 5"'}/>`; });
    let acc = 0, bars = '', conns = '', labels = '', hits = '';
    g.passos.forEach((p, i) => {
      let v0, v1;
      if (p[2] === 'total') { v0 = g.base; v1 = p[1]; acc = p[1]; } else { v0 = acc; v1 = acc + p[1]; acc = v1; }
      const x = L + i * bw + (bw - pw) / 2, ytop = y(Math.max(v0, v1)), ybase = y(Math.min(v0, v1)), h = Math.max(4, ybase - ytop);
      const ton = TONS[p[3]] ? p[3] : 'azul', c = TONS[ton];
      if (i < n - 1) conns += `<line class="conn" data-i="${i}" x1="${x + pw + dx}" x2="${x + bw}" y1="${y(acc) - dy}" y2="${y(acc) - dy}" stroke="#7C93C4" stroke-dasharray="3 3" style="opacity:0;transition:opacity .4s"/>`;
      bars += `<g class="bar3d" data-i="${i}"><ellipse cx="${x + (pw + dx) / 2}" cy="${ybase + 3}" rx="${pw * .72}" ry="4" fill="#000" fill-opacity=".35"/><polygon points="${x + pw},${ytop} ${x + pw + dx},${ytop - dy} ${x + pw + dx},${ytop - dy + h} ${x + pw},${ytop + h}" fill="url(#${id}-s-${ton})"/><rect x="${x}" y="${ytop}" width="${pw}" height="${h}" fill="url(#${id}-f-${ton})"/><polygon points="${x},${ytop} ${x + dx},${ytop - dy} ${x + pw + dx},${ytop - dy} ${x + pw},${ytop}" fill="${c.t}"/><rect x="${x}" y="${ytop}" width="${pw}" height="${Math.min(h, 3)}" fill="#fff" fill-opacity=".22"/><text class="vlr" x="${x + (pw + dx) / 2}" y="${ytop - dy - 7}" text-anchor="middle">${abrev(p[1], p[2] === 'delta')}</text></g>`;
      labels += `<text class="rot" data-i="${i}" x="${x + (pw + dx) / 2}" y="${H - 10}" text-anchor="middle">${esc(p[0])}</text>`;
      hits += `<rect class="hit" data-i="${i}" x="${L + i * bw}" y="0" width="${bw}" height="${H}" fill="transparent" tabindex="0" role="button" aria-label="${esc(p[0])}: ${brl(p[1])}" style="cursor:pointer"/>`;
    });
    return `<svg viewBox="0 0 ${W} ${H}" role="group" aria-label="Gráfico em cascata, de exemplo"><defs>${defs}</defs>${grade}${conns}${bars}${labels}${hits}</svg>`;
  };

  const curvaGeom = () => {
    const W = 600, H = 190, L = 10, R = 10, T = 12, B = 28, N = 64;
    const X = (u) => L + (W - L - R) * u, Y = (v) => T + (H - T - B) * (1 - v);
    const sig = (u, c, k) => { const f = (z) => 1 / (1 + Math.exp(-k * (z - c))); return (f(u) - f(0)) / (f(1) - f(0)); };
    return { W, H, L, R, T, B, N, X, Y, cob: (u) => sig(u, .45, 9), ver: (u) => sig(u, .57, 8.5) };
  };
  const curvaSvg = () => {
    const G = curvaGeom();
    const path = (fn) => { let d = ''; for (let i = 0; i <= G.N; i++) { const u = i / G.N; d += (i ? 'L' : 'M') + G.X(u).toFixed(1) + ' ' + G.Y(fn(u)).toFixed(1) + ' '; } return d; };
    let gap = path(G.cob);
    for (let i = G.N; i >= 0; i--) { const u = i / G.N; gap += 'L' + G.X(u).toFixed(1) + ' ' + G.Y(G.ver(u)).toFixed(1) + ' '; }
    return `<svg viewBox="0 0 ${G.W} ${G.H}" role="img" aria-label="Curva S de exemplo: o avanço verificado em campo fica atrás do avanço cobrado">
      <line x1="${G.L}" x2="${G.W - G.R}" y1="${G.H - G.B}" y2="${G.H - G.B}" stroke="#7C93C4" stroke-opacity=".55"/>
      <path d="${gap}Z" fill="#69e7ff" fill-opacity=".1"/>
      <path class="trace" d="${path(G.cob)}" fill="none" stroke="#6F94F0" stroke-width="3" stroke-linecap="round" pathLength="1"/>
      <path class="trace trace--2" d="${path(G.ver)}" fill="none" stroke="#F2BD5D" stroke-width="3" stroke-linecap="round" pathLength="1"/>
      <line id="cv-mk" stroke="#7C93C4" stroke-dasharray="3 3"/><line id="cv-df" stroke="#69e7ff" stroke-width="3" stroke-linecap="round"/>
      <circle id="cv-p1" r="6" fill="#6F94F0" stroke="#02101c" stroke-width="2"/><circle id="cv-p2" r="6.5" fill="#F2BD5D" stroke="#02101c" stroke-width="2"/>
      <text id="cv-tx" class="vlr" fill="#69e7ff" style="fill:#69e7ff">defasagem</text>
      <text class="rot" x="${G.L}" y="${G.H - 10}">início da obra</text><text class="rot" x="${G.W - G.R}" y="${G.H - 10}" text-anchor="end">entrega</text></svg>`;
  };

  /* ───────── montagem dos painéis ───────── */
  const labs = {};
  const rowsHtml = (linhas) => `<ul class="rows">${linhas.map((l) => `<li><div><strong>${esc(l[0])}</strong><small>${esc(l[1])}</small></div><div class="val">${l[2] ? `<span>${esc(l[2])}</span>` : ''}<i class="t-${l[4]}">${esc(l[3])}</i></div></li>`).join('')}</ul>`;
  const kpisHtml = (k) => `<div class="kpis">${k.map((x) => `<div class="kpi"><span>${esc(x[0])}</span><b class="${x[2] ? 't-' + x[2] : ''}">${esc(x[1])}</b>${x[3] ? `<em class="${x[2] ? 't-' + x[2] : ''}">${esc(x[3])}</em>` : ''}</div>`).join('')}</div>`;
  const comoHtml = (c) => `<div class="how"><div><h4>Para quem</h4><p>${esc(c.para)}</p></div><div><h4>Você envia</h4><p>${esc(c.envia)}</p></div><div class="wide"><h4>Como trabalhamos</h4><ol>${c.passos.map((p) => `<li>${esc(p)}</li>`).join('')}</ol></div><div class="wide"><h4>Você recebe</h4><ul>${c.recebe.map((p) => `<li>${esc(p)}</li>`).join('')}</ul></div></div>`;

  document.querySelectorAll('[data-lab]').forEach((section) => {
    const key = section.dataset.lab, data = LABS[key], panel = section.querySelector('[data-lab-root]');
    let vista = 0, timers = [], sel = 0;
    const lab = { played: false };
    labs[key] = lab;

    const clear = () => { timers.forEach(clearTimeout); timers = []; };
    const select = (i) => {
      const g = data.ponte; if (!g) return;
      sel = i;
      panel.querySelectorAll('.bar3d').forEach((b) => b.classList.toggle('is-ativa', +b.dataset.i === i));
      panel.querySelectorAll('.rot').forEach((t) => t.classList.toggle('is-ativo', +t.dataset.i === i));
      const s = g.passos[i], box = panel.querySelector('.reading');
      if (box) box.innerHTML = `<b class="t-${s[3]}">${esc(s[0])} · ${s[2] === 'delta' ? (s[1] < 0 ? '− ' : '+ ') : ''}R$ ${Math.abs(s[1]).toLocaleString('pt-BR')}</b><span>${esc(s[4])}</span>`;
    };
    const play = () => {
      clear();
      const chart = panel.querySelector('.chart'); if (!chart) return;
      lab.played = true;
      if (data.curva) { chart.classList.remove('is-live'); void chart.offsetWidth; chart.classList.add('is-live'); return; }
      const bars = [...panel.querySelectorAll('.bar3d')], conns = [...panel.querySelectorAll('.conn')];
      bars.forEach((b) => b.classList.remove('is-on')); conns.forEach((c) => { c.style.opacity = 0; });
      const passo = reducedMotion ? 0 : 430;
      bars.forEach((b, i) => timers.push(setTimeout(() => {
        b.classList.add('is-on'); select(i);
        if (conns[i - 1]) conns[i - 1].style.opacity = 1;
      }, 250 + i * passo)));
    };
    lab.play = play;

    const bindChart = () => {
      if (data.ponte) {
        panel.querySelectorAll('.hit').forEach((h) => {
          const i = +h.dataset.i;
          h.addEventListener('mouseenter', () => select(i)); h.addEventListener('focus', () => select(i)); h.addEventListener('click', () => select(i));
        });
        const rp = panel.querySelector('.replay'); if (rp) rp.addEventListener('click', play);
      }
      if (data.curva) {
        const G = curvaGeom(), range = panel.querySelector('input[type=range]');
        const atualiza = () => {
          const u = range.value / 100, xc = G.X(u), yc = G.Y(G.cob(u)), yv = G.Y(G.ver(u));
          const set = (id, o) => { const e = panel.querySelector('#' + id); Object.keys(o).forEach((k) => e.setAttribute(k, o[k])); };
          set('cv-mk', { x1: xc, x2: xc, y1: G.T, y2: G.H - G.B }); set('cv-df', { x1: xc, x2: xc, y1: yc, y2: yv });
          set('cv-p1', { cx: xc, cy: yc }); set('cv-p2', { cx: xc, cy: yv });
          set('cv-tx', { x: Math.min(xc + 12, G.W - 70), y: (yc + yv) / 2 + 4 });
        };
        range.addEventListener('input', atualiza); atualiza();
        const rp = panel.querySelector('.replay'); if (rp) rp.addEventListener('click', play);
      }
    };

    const render = () => {
      clear();
      const top = `<div class="lab-top"><div><small>${data.quando}</small><h3>${esc(data.nome)}</h3></div><div class="lab-views" role="tablist" aria-label="Tipo de conteúdo"><button type="button" role="tab" aria-selected="${vista === 0}" class="${vista === 0 ? 'is-on' : ''}" data-v="0">Resultado de exemplo</button><button type="button" role="tab" aria-selected="${vista === 1}" class="${vista === 1 ? 'is-on' : ''}" data-v="1">Como funciona</button></div></div>`;
      let corpo;
      if (vista === 1) corpo = comoHtml(data.como);
      else {
        const chart = data.ponte
          ? `<div class="chart"><div class="svgwrap">${ponteSvg(key, data.ponte)}</div><div class="reading" aria-live="polite"></div><div class="chart-foot"><span>${esc(data.ponte.eixo)}</span><button type="button" class="replay">↻ Reproduzir</button></div></div>`
          : `<div class="chart"><div class="svgwrap">${curvaSvg()}</div><div class="curve-ctl"><span class="t-azul">● cobrado pela construtora</span><input type="range" min="0" max="100" value="60" aria-label="Percorrer o cronograma"><span class="t-ouro">● verificado em campo</span></div><div class="chart-foot"><span>Curva S de exemplo, sem valores. Arraste para ver a defasagem em cada momento da obra.</span><button type="button" class="replay">↻ Reproduzir</button></div></div>`;
        corpo = `${kpisHtml(data.kpis)}${chart}${rowsHtml(data.linhas)}<p class="src"><span class="tag-ilus">Exemplo ilustrativo</span>${esc(data.fonte)}</p>`;
      }
      panel.innerHTML = top + corpo;
      panel.querySelectorAll('.lab-views button').forEach((b) => b.addEventListener('click', () => { vista = +b.dataset.v; render(); if (vista === 0 && lab.played) play(); }));
      if (vista === 0) { bindChart(); if (data.ponte) { select(data.ponte.passos.length - 1); if (!lab.played) panel.querySelectorAll('.bar3d').forEach((b) => b.classList.remove('is-on')); } }
    };
    render();
  });

  // entrada dos capítulos e início das animações dos gráficos
  /* a seção aparece quando 22% dela está na tela OU quando uma boa faixa da tela já é dela:
     em seções muito altas (catálogo, no celular) 22% nunca chegava e o conteúdo ficava invisível, deixando a tela preta */
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      const aparece = entry.isIntersecting && (entry.intersectionRatio >= .22 || entry.intersectionRect.height >= innerHeight * .12);
      entry.target.classList.toggle('is-visible', aparece);
      if (aparece && entry.target.dataset.lab) {
        const lab = labs[entry.target.dataset.lab];
        if (lab && !lab.played) setTimeout(lab.play, 350);
      }
    });
  }, { threshold: Array.from({ length: 51 }, (_, i) => i / 50) });
  document.querySelectorAll('.product, .method, .contact, .catalog, .about').forEach((element) => revealObserver.observe(element));

  /* ───────── catálogo: 12 produtos do modelo Sentinela 2.0 ─────────
     Textos a partir do De-Para e do Catálogo R04 (proposta, ainda não aprovada). Sem preço, prazo ou promessa de resultado.
     MOSTRAR_ESTADO = false esconde a etiqueta de disponibilidade de cada produto. */
  const MOSTRAR_ESTADO = false;
  const PRODUTOS = [
    { n: '01', apelido: 'Viabilidade e implantação do terreno', nome: 'Estudo de alternativas de implantação', estado: 'Em qualificação',
      txt: 'Compara alternativas de implantação de um terreno, com as quantidades, os custos e os riscos de cada uma.',
      ent: 'Alternativas de implantação, quantidades, custos e riscos.',
      lim: 'Não inclui levantamento, sondagem nem projeto executivo.' },
    { n: '02', apelido: 'Diagnóstico ambiental e cartográfico', nome: 'Diagnóstico cartográfico e hidrológico', estado: 'Com especialista',
      txt: 'Organiza mapas, camadas e documentos de um terreno e levanta as questões hidrológicas que precisam de resposta.',
      ent: 'Mapas analíticos, matriz de conformidade documental e questões hidrológicas.',
      lim: 'Não substitui licenciamento nem inventário de fauna e flora.' },
    { n: '03', apelido: 'Conferência do modelo 3D da obra', nome: 'Conflitos entre disciplinas e quantitativos do modelo', estado: 'Piloto',
      txt: 'Confere o modelo 3D da obra (BIM), em formato aberto: encontra conflitos entre disciplinas e confere quantitativos selecionados.',
      ent: 'Matriz de ocorrências e de quantitativos conferidos. Arquivos de apoio, quando produzidos.',
      lim: 'Não inclui remodelagem nem verificação integral de cálculo.' },
    { n: '04', apelido: 'Fiscalização 360°', nome: 'Conferência de medição com evidências', estado: 'Piloto',
      txt: 'Compara o que foi medido e cobrado com o que as evidências de campo mostram, ciclo a ciclo.',
      ent: 'Relatório do ciclo e matriz item, evidência e diferença.',
      lim: 'Não é fiscalização permanente nem controle tecnológico. Imagem 360° não mede sozinha.' },
    { n: '05', apelido: 'Equalização de propostas e pleitos', nome: 'Equalização de propostas e análise de pleitos', estado: 'Piloto',
      txt: 'Equaliza orçamentos e propostas contra as tabelas oficiais de preços (SINAPI e SICRO) e analisa pleitos de aditivo com o diário de obra, a chuva e o caminho crítico.',
      ent: 'Planilha com a estrutura de itens preservada, Curva ABC e ocorrências. Cronologia e análise de causalidade dos pleitos.',
      lim: 'Não é orçamento do zero nem prova de sobrepreço. Não inclui defesa judicial nem garante êxito.' },
    { n: '06', apelido: 'Inspeção estrutural', nome: 'Inspeção visual de ativo', estado: 'Com especialista',
      txt: 'Registra visualmente um ativo, com drone e termografia quando couber, e localiza as manifestações que pedem investigação.',
      ent: 'Registro visual, manifestações localizadas e plano de investigação.',
      lim: 'Não declara estabilidade por imagem. Ensaios e perícia são serviços separados.' },
    { n: '07', apelido: 'Custo para concluir a obra', nome: 'Monitoramento do custo para concluir', estado: 'Em estruturação',
      txt: 'Acompanha, a cada ciclo, quanto falta gastar para concluir um empreendimento, com as premissas e os riscos à vista.',
      ent: 'Relatório de custo para concluir, premissas, riscos e marcos observados.',
      lim: 'Não é rating, auditoria financeira nem autorização de crédito.' },
    { n: '08', apelido: 'Triagem técnica para compra de ativos', nome: 'Triagem técnica de ativo para aquisição', estado: 'Em estruturação',
      txt: 'Faz uma triagem técnica rápida de um ativo que será adquirido: alertas, passivos aparentes e investimento preliminar.',
      ent: 'Matriz de alertas, passivos aparentes e investimento preliminar.',
      lim: 'Não é due diligence jurídica nem ambiental integral e não garante ausência de vícios.' },
    { n: '09', apelido: 'Conferência de notas fiscais e medição', nome: 'Reconciliação de compras e medição', estado: 'Piloto',
      txt: 'Cruza as notas fiscais eletrônicas, o estoque e a medição para mostrar diferenças entre o que foi comprado, incorporado e medido.',
      ent: 'Matriz de reconciliação, exceções e questões documentais.',
      lim: 'Não valida as notas junto ao fisco nem prova fraude.' },
    { n: '10', apelido: 'Análise técnica de licitações', nome: 'Análise técnica de edital e orçamento', estado: 'Sob demanda, com apoio jurídico',
      txt: 'Lê o edital e o orçamento e organiza as questões técnicas que merecem validação jurídica.',
      ent: 'Nota técnica e matriz de questões para validação jurídica.',
      lim: 'Não inclui advocacia nem protocolo e não garante resultado.' },
    { n: '11', apelido: 'Gêmeo digital leve', nome: 'Acompanhamento evolutivo de manifestações', estado: 'Em pesquisa',
      txt: 'Compara imagens de um mesmo local ao longo do tempo para registrar variações e indicar o que merece investigação.',
      ent: 'Registro de variações, alertas revisados e plano de investigação.',
      lim: 'Não é gêmeo digital operacional nem vigilância de segurança estrutural.' },
    { n: '12', apelido: 'Carbono incorporado e custo', nome: 'Estudo de carbono incorporado e alternativas', estado: 'Em desenvolvimento',
      txt: 'Compara alternativas de materiais pelo carbono incorporado e pelas consequências de custo.',
      ent: 'Estudo comparativo de carbono incorporado e consequências de custo.',
      lim: 'Não é crédito de carbono nem certificação ambiental.' }
  ];
  const GRUPOS = [
    { nome: 'Antes de contratar', ns: ['01', '02', '03', '05', '10'] },
    { nome: 'Durante a execução', ns: ['04', '07', '09', '11'] },
    { nome: 'Ativos e estudos especializados', ns: ['06', '08', '12'] }
  ];
  const tabs = document.querySelector('#catalog-tabs'), grid = document.querySelector('#catalog-grid');
  const mostrarGrupo = (gi) => {
    tabs.querySelectorAll('button').forEach((b, i) => { b.classList.toggle('is-on', i === gi); b.setAttribute('aria-selected', String(i === gi)); });
    grid.innerHTML = GRUPOS[gi].ns.map((n, k) => {
      const p = PRODUTOS.find((x) => x.n === n);
      return `<article class="card" style="animation-delay:${k * 60}ms"><div class="card-img"><img src="assets/produtos-s/${esc(p.n)}.jpg" alt="" width="960" height="536" loading="lazy" decoding="async" onerror="this.style.display='none'"><span class="card-cod">${esc(p.n)}</span>${MOSTRAR_ESTADO ? `<span class="card-estado">${esc(p.estado)}</span>` : ''}</div><div class="card-body"><span class="card-eyebrow">${esc(p.apelido)}</span><h3>${esc(p.nome)}</h3><p>${esc(p.txt)}</p><div class="recebe"><b>Você recebe</b>${esc(p.ent)}</div><p class="limite"><b>Fora do escopo:</b> ${esc(p.lim)}</p><a href="#contato" data-abrir-contato data-assunto="${esc(p.nome)}">APRESENTAR MEU CENÁRIO ↗</a></div></article>`;
    }).join('');
  };
  tabs.innerHTML = GRUPOS.map((g, i) => `<button type="button" role="tab" aria-selected="false" data-g="${i}"><span>0${i + 1}</span>${esc(g.nome)}</button>`).join('');
  tabs.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => mostrarGrupo(+b.dataset.g)));
  mostrarGrupo(0);

  /* ───────── método: cinco movimentos, imagem de fundo com lente do cursor ───────── */
  const MOVS = [
    ['Observar', 'Consultar as referências disponíveis e verificar a realidade dentro do escopo.'],
    ['Confrontar', 'Comparar projeto, contrato, cronograma ou premissas com o que foi observado.'],
    ['Integrar', 'Relacionar equipe, materiais, equipamentos, projeto, contrato e fornecedores.'],
    ['Propor', 'Apresentar causas sustentadas e caminhos compatíveis com as condições reais.'],
    ['Apoiar', 'Apoiar quem decide e verificar os efeitos quando isso fizer parte do escopo contratado.']
  ];
  const metodo = document.querySelector('#metodo');
  const stepsEl = document.querySelector('#method-steps'), cardEl = document.querySelector('#step-card');
  const DUR = 6500;
  let atual = 0, tm = 0;
  const mostrarMov = (i, manual) => {
    atual = i;
    stepsEl.querySelectorAll('li').forEach((li, k) => {
      li.classList.toggle('is-on', k === i);
      li.querySelector('button').setAttribute('aria-selected', String(k === i));
      const bar = li.querySelector('.bar'); if (bar) { bar.style.animation = 'none'; void bar.offsetWidth; bar.style.animation = ''; }
    });
    cardEl.style.animation = 'none'; void cardEl.offsetWidth; cardEl.style.animation = '';
    cardEl.innerHTML = `<span class="big" aria-hidden="true">0${i + 1}</span><small>MOVIMENTO 0${i + 1} DE 05</small><h3>${esc(MOVS[i][0])}</h3><p>${esc(MOVS[i][1])}</p>`;
    clearTimeout(tm);
    if (!reducedMotion && !metodo.classList.contains('is-paused')) tm = setTimeout(() => mostrarMov((atual + 1) % MOVS.length), DUR);
    if (manual) metodo.classList.add('is-paused');
  };
  stepsEl.style.setProperty('--dur', DUR + 'ms');
  stepsEl.innerHTML = MOVS.map((m, i) => `<li><button type="button" role="tab" aria-selected="false" data-i="${i}"><span>0${i + 1}</span>${esc(m[0].toUpperCase())}</button><i class="bar"></i></li>`).join('');
  stepsEl.querySelectorAll('button').forEach((b) => {
    b.addEventListener('click', () => mostrarMov(+b.dataset.i, true));
    b.addEventListener('mouseenter', () => { if (matchMedia('(hover: hover)').matches) mostrarMov(+b.dataset.i, true); });
  });
  mostrarMov(0);
  // volta a avançar sozinho quando o visitante sai da dobra
  metodo.addEventListener('pointerleave', () => { metodo.classList.remove('is-hover'); if (metodo.classList.contains('is-paused')) { metodo.classList.remove('is-paused'); clearTimeout(tm); tm = setTimeout(() => mostrarMov((atual + 1) % MOVS.length), DUR); } });
  metodo.addEventListener('pointermove', (event) => {
    const r = metodo.getBoundingClientRect();
    const x = event.clientX - r.left, y = event.clientY - r.top;
    metodo.style.setProperty('--mx', x + 'px'); metodo.style.setProperty('--my', y + 'px');
    metodo.classList.add('is-hover');
    if (!reducedMotion) {
      const dx = (x / r.width - .5) * -14, dy = (y / r.height - .5) * -10;
      metodo.querySelectorAll('.method-bg img').forEach((im) => { im.style.transform = `translate3d(${dx}px, ${dy}px, 0)`; });
    }
  }, { passive: true });

  /* ───────── contato: o C e o fundo acompanham o cursor ───────── */
  const contato = document.querySelector('#contato');
  contato.addEventListener('pointermove', (event) => {
    if (reducedMotion) return;
    const r = contato.getBoundingClientRect();
    contato.style.setProperty('--cx', (((event.clientX - r.left) / r.width - .5) * 2).toFixed(3));
    contato.style.setProperty('--cy', (((event.clientY - r.top) / r.height - .5) * 2).toFixed(3));
  }, { passive: true });
  contato.addEventListener('pointerleave', () => { contato.style.setProperty('--cx', 0); contato.style.setProperty('--cy', 0); });

  /* ───────── contato: caixa de texto + WhatsApp ───────── */
  const WHATS = '5527996971800';
  const EMAIL = 'contato@criviaengenharia.com.br';
  const zap = (texto) => `https://wa.me/${WHATS}?text=${encodeURIComponent(texto)}`;
  const MSG_BASE = 'Olá! Vim pelo site da CRIVIA e gostaria de conversar sobre uma situação.';
  document.querySelectorAll('[data-whats]').forEach((a) => { a.href = zap(MSG_BASE + ' Posso explicar por aqui?'); });

  const dlg = document.querySelector('#contato-dialog');
  const txt = document.querySelector('#cd-texto'), cont = document.querySelector('#cd-cont');
  const lnkZap = document.querySelector('#cd-whats'), lnkMail = document.querySelector('#cd-email'), assuntoEl = document.querySelector('#cd-assunto');
  let assunto = '';
  const montar = () => {
    const t = txt.value.trim();
    const partes = [MSG_BASE];
    if (assunto) partes.push(`Assunto: ${assunto}.`);
    partes.push(t ? `Minha situação:\n${t}` : 'Vou explicar a situação por aqui.');
    const msg = partes.join('\n\n');
    lnkZap.href = zap(msg);
    lnkMail.href = `mailto:${EMAIL}?subject=${encodeURIComponent('Contato pelo site' + (assunto ? ' — ' + assunto : ''))}&body=${encodeURIComponent(t)}`;
    cont.textContent = `${txt.value.length} / 700`;
  };
  txt.addEventListener('input', montar);
  const abrir = (assuntoNovo) => {
    assunto = assuntoNovo || '';
    assuntoEl.hidden = !assunto; assuntoEl.textContent = assunto ? `Assunto: ${assunto}` : '';
    montar();
    if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
    setTimeout(() => txt.focus(), 60);
  };
  document.addEventListener('click', (e) => {
    const a = e.target.closest && e.target.closest('[data-abrir-contato]');
    if (!a) return;
    e.preventDefault(); body.classList.remove('menu-open'); menuButton.setAttribute('aria-expanded', 'false');
    abrir(a.dataset.assunto || '');
  });
  document.querySelector('#cd-fechar').addEventListener('click', () => dlg.close());
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
  montar();

  /* ───────── primeira tela (raio-X) e dobra dos três estados ───────── */
/* 1 · raio-X: a mira segue o ponteiro; sem ponteiro, ela passeia sozinha pela planta */
  const xr = document.querySelector('#inicio');
  let lastMove = -1e9, px = 0, py = 0;
  xr.addEventListener('pointermove', (e) => {
    const r = xr.getBoundingClientRect();
    px = e.clientX - r.left; py = e.clientY - r.top; lastMove = performance.now();
    body.style.setProperty('--lx', px + 'px'); body.style.setProperty('--ly', py + 'px');
  }, { passive: true });
  /* celular e tablet: a mira passeia mais devagar e para durante a rolagem, para não pesar na primeira tela */
  const toque = window.matchMedia('(max-width: 900px), (hover: none)');
  let ultimoQuadro = 0, ultimaRolagem = -1e9;
  addEventListener('scroll', () => { ultimaRolagem = performance.now(); }, { passive: true });
  const passeio = (t) => {
    requestAnimationFrame(passeio);
    if (toque.matches && (t - ultimoQuadro < 70 || t - ultimaRolagem < 250)) return;
    ultimoQuadro = t;
    if (reducedMotion || t - lastMove < 3000) return;
    const r = xr.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) return;
    const x = r.width * (.58 + .22 * Math.sin(t * .00055)), y = r.height * (.46 + .2 * Math.sin(t * .00085 + 1));
    body.style.setProperty('--lx', x + 'px'); body.style.setProperty('--ly', y + 'px');
  };
  requestAnimationFrame(passeio);

  /* 2 · três estados guiados pela rolagem (ou pelo clique) */
  const tri = document.querySelector('#visao');
  const steps = [...tri.querySelectorAll('.tri-steps li')];
  const status = tri.querySelector('#tri-status');
  const NOMES = ['INCERTEZA', 'MÉTODO', 'DECISÃO ROBUSTA'];
  const marcas = { 1: '?', 2: '', 3: '✓' };
  let estado = 0, manualAte = 0;
  const definir = (s) => {
    if (s === estado) return;
    estado = s;
    tri.classList.remove('s1', 's2', 's3'); tri.classList.add('s' + s);
    tri.style.setProperty('--st', s);
    steps.forEach((li, k) => li.classList.toggle('is-on', k === s - 1));
    tri.querySelectorAll('.tri-node i').forEach((i) => { i.textContent = s === 2 ? '' : marcas[s]; });
    status.textContent = `ESTADO ${s} DE 3 · ${NOMES[s - 1]}`;
  };
  const porRolagem = () => {
    if (performance.now() < manualAte) return;
    const r = tri.getBoundingClientRect();
    const p = Math.min(1, Math.max(0, -r.top / (r.height - innerHeight)));
    definir(p < .3 ? 1 : p < .64 ? 2 : 3);
  };
  addEventListener('scroll', porRolagem, { passive: true });
  tri.querySelectorAll('.tri-steps button').forEach((b) => b.addEventListener('click', () => { manualAte = performance.now() + 6000; definir(+b.dataset.s); }));
  tri.style.setProperty('--st', 1);
  porRolagem();

  /* ───────── dobra "A obra física": os três pontos ficam sobre partes reais da foto ─────────
     Pontos em fração da imagem (1920×1081): interface (encontro tubulação × pilar), registro (tablet) e impacto (chumbadores da base). */
  const triImg = tri.querySelector('.tri-media img');
  const triNos = [...tri.querySelectorAll('.tri-node')];
  const triLinhas = [...tri.querySelectorAll('.tri-lines line')];
  const PONTOS = [[0.699, 0.350], [0.526, 0.516], [0.695, 0.714]];
  const LIGA = [[0, 1], [1, 2], [0, 2]];
  const ancorar = () => {
    const box = tri.querySelector('.tri-media');
    const w = box.clientWidth, h = box.clientHeight, nw = 1920, nh = 1081;
    const s = Math.max(w / nw, h / nh), dw = nw * s, dh = nh * s, px = w < 900 ? 0.64 : 0.5, l0 = (w - dw) * px, t0 = (h - dh) / 2;
    const pos = PONTOS.map(([u, v]) => [((l0 + u * dw) - w / 2) * 1.05 + w / 2, ((t0 + v * dh) - h / 2) * 1.05 + h / 2]);
    triNos.forEach((n, i) => { n.style.left = pos[i][0] + 'px'; n.style.top = pos[i][1] + 'px'; });
    triLinhas.forEach((ln, k) => {
      const [a, b] = LIGA[k];
      ln.setAttribute('x1', pos[a][0] / w * 100); ln.setAttribute('y1', pos[a][1] / h * 100);
      ln.setAttribute('x2', pos[b][0] / w * 100); ln.setAttribute('y2', pos[b][1] / h * 100);
    });
  };
  addEventListener('resize', ancorar, { passive: true });
  ancorar();
})();
