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
      fonte: 'Ampliação industrial. Fontes: diários de obra, INMET e contrato.'
    },
    medicao: {
      quando: 'DURANTE A EXECUÇÃO', nome: 'Planejamento e Medição',
      kpis: [['Cobrado, medição nº 04', 'R$ 280.000', '', ''], ['Valor com evidência verificada', 'R$ 235.000', 'bom', ''], ['Diferença sob análise', '− R$ 45.000', 'ouro', 'Condições técnicas e pendências para a decisão do cliente']],
      curva: true,
      linhas: [
        ['Divisórias drywall, 3º pavimento', 'Cobrado 100% · evidência verificada 70% · fechamento de lã de rocha não evidenciado', '− R$ 25.500', 'PONTO DE CONTROLE', 'ouro'],
        ['Laje técnica da cobertura', 'Cobrado 100% · evidência verificada 79,5% · aguarda laudo de rompimento', '− R$ 19.500', 'NOVA VERIFICAÇÃO', 'aviso'],
        ['Radar de 30 dias · decisão do cliente até 13/11', 'Compra do quadro geral e do transformador (prazo de fábrica de 45 dias)', '', 'CRÍTICO', 'ouro']],
      como: { para: 'Quem já contratou a obra e não quer voltar à incerteza.', envia: 'A planilha de medição da construtora, numa data de corte fixa (por exemplo, dia 25).',
        passos: ['Inspeção visual focada nos itens definidos no escopo, com fotos.', 'O que foi visto é cruzado com a planilha de medição.', 'Para os itens analisados, a CRIVIA aponta as condições técnicas e as pendências; a decisão permanece com o cliente.'],
        recebe: ['Boletim de 4 páginas', 'Recomendação técnica e pendências segundo os critérios definidos, com a Curva S', 'Radar dos suprimentos críticos dos próximos 30 dias e os documentos que embasam a decisão do cliente'] },
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
  document.querySelectorAll('.product, .method, .contact, .catalog, .about, .exp').forEach((element) => revealObserver.observe(element));

  /* ───────── catálogo: 18 produtos em quatro frentes + 3 entradas destacadas (18, 19 e 20) ─────────
     Fonte: catalogo-publico.json (R02), gerado por scripts/gerar_catalogo.py. Sem preço, prazo ou promessa de resultado. */
  /* CATALOGO:INICIO — gerado por scripts/gerar_catalogo.py a partir de catalogo-publico.json (revisão R03). Não editar à mão. */
const PRODUTOS = [
  {"numero": "01", "nome": "Viabilidade e implantação do terreno", "grupo": "antes-de-contratar", "tipo": "catalogo", "dor": "Alternativas parecem comparáveis, mas usam programas, quantidades ou restrições diferentes.", "para_quem": {"decisor": "Proprietário ou diretor de incorporação com alternativas de implantação ainda abertas.", "prestadora": "Dono de projetista ou prestadora que precisa apresentar ao cliente uma comparação tecnicamente fundamentada."}, "beneficios": ["Clareza para decidir", "Organização de premissas", "Demonstração de planejamento técnico"], "resultado_pratico": "Fixar o programa, explicitar restrições, comparar alternativas na mesma base e testar as premissas que poderiam inverter a recomendação.", "entregas": "Quadro de alternativas; premissas e fontes; consequências técnicas e estimativas no nível contratado; recomendação e diligências.", "limites": "Projeto executivo, aprovação urbanística, topografia, geotecnia e viabilidade integral não são presumidos.", "referencia": "ABNT NBR 13133 — Levantamento topográfico: Conferir identificação e alcance do levantamento topográfico usado no estudo.; ABNT NBR 14645 (série) — Como construído, levantamentos e controle dimensional: Relacionar o estudo aos levantamentos/controles do imóvel pertinentes à parte selecionada.; ABNT NBR 12721 — Custos de construção para incorporação e condomínios: Contextualizar CUB/quadros de incorporação usados na comparação.; SINAPI — CAIXA — Referências técnicas e custos da construção: Formar comparações de custos de serviços efetivamente quantificados.", "cta": "Apresente o terreno, as alternativas e a decisão necessária.", "anchor": "servico-01", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Analisar a implantação usando bases físicas identificadas e referências de custo adequadas.", "criterios_principais": "Contrato, programa do empreendimento e regras urbanísticas locais.", "referencias": [{"id": "N13133", "codigo": "ABNT NBR 13133", "nome": "Levantamento topográfico", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "base_tecnica", "aplicacao": "Conferir identificação e alcance do levantamento topográfico usado no estudo.", "condicao": "Quando houver levantamento topográfico como entrada; execução de campo é atividade própria.", "entrega_vinculada": "Registro da base física e de suas limitações.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N14645", "codigo": "ABNT NBR 14645 (série)", "nome": "Como construído, levantamentos e controle dimensional", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "base_tecnica", "aplicacao": "Relacionar o estudo aos levantamentos/controles do imóvel pertinentes à parte selecionada.", "condicao": "Somente a parte aplicável ao objeto; não presume levantamento ou as built novo.", "entrega_vinculada": "Quadro de referências e diligências sobre a base.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N12721", "codigo": "ABNT NBR 12721", "nome": "Custos de construção para incorporação e condomínios", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "complementar_condicional", "aplicacao": "Contextualizar CUB/quadros de incorporação usados na comparação.", "condicao": "Quando a contratação envolver finalidade coberta pela norma; não substitui orçamento completo.", "entrega_vinculada": "Premissas da estimativa no campo correspondente.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "R_SINAPI", "codigo": "SINAPI — CAIXA", "nome": "Referências técnicas e custos da construção", "tipo": "referencia_tecnica_ou_regulamentar", "papel_no_servico": "referencia_de_custo", "aplicacao": "Formar comparações de custos de serviços efetivamente quantificados.", "condicao": "Selecionar UF, data-base, composição e condições.", "entrega_vinculada": "Memória de custos de alternativas.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 13133", "Levantamento topográfico", "13133", "NBR 13133", "ABNT NBR 14645 (série)", "Como construído, levantamentos e controle dimensional", "14645", "NBR 14645", "ABNT NBR 12721", "Custos de construção para incorporação e condomínios", "12721", "NBR 12721", "SINAPI — CAIXA", "Referências técnicas e custos da construção"]},
  {"numero": "02", "nome": "Diagnóstico ambiental e cartográfico", "grupo": "antes-de-contratar", "tipo": "catalogo", "dor": "Mapas e documentos dispersos não permitem distinguir condição conhecida de hipótese ou falta de levantamento.", "para_quem": {"decisor": "Comprador de terreno ou gestor que precisa orientar diligências antes de decidir.", "prestadora": "Projetista ou prestadora que deve reunir condicionantes para a proposta ou estudo de seu cliente."}, "beneficios": ["Organização da informação do terreno", "Visibilidade de incertezas", "Diligência técnica demonstrável"], "resultado_pratico": "Inventariar camadas e documentos, conferir escala/data/origem, localizar alertas e encaminhar os estudos que exigem confirmação física.", "entregas": "Inventário de fontes; quadro/mapa de condicionantes; incertezas; diligências e estudos necessários.", "limites": "Não presume licenciamento, laudo ambiental integral, estudo de inundação, sondagem ou regularidade integral do imóvel.", "referencia": "ABNT NBR 13133 — Levantamento topográfico: Conferir origem e condições da base topográfica usada para localizar o imóvel.; ABNT NBR 15515 (série) — Passivo ambiental em solo e água subterrânea: Enquadrar a avaliação/investigação de passivo em solo e água subterrânea.", "cta": "Informe a localização, o uso pretendido e a dúvida sobre o terreno.", "anchor": "servico-02", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Localizar condicionantes e definir o alcance das investigações ambientais/cartográficas necessárias.", "criterios_principais": "Identificação do imóvel, fontes cartográficas e regras dos órgãos competentes.", "referencias": [{"id": "N13133", "codigo": "ABNT NBR 13133", "nome": "Levantamento topográfico", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "base_tecnica", "aplicacao": "Conferir origem e condições da base topográfica usada para localizar o imóvel.", "condicao": "Não substitui levantamento de campo quando necessário.", "entrega_vinculada": "Inventário de bases e limites de precisão.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N15515", "codigo": "ABNT NBR 15515 (série)", "nome": "Passivo ambiental em solo e água subterrânea", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "modulo_especializado", "aplicacao": "Enquadrar a avaliação/investigação de passivo em solo e água subterrânea.", "condicao": "Somente se a etapa ambiental correspondente for contratada com competência específica.", "entrega_vinculada": "Matriz de indícios/diligências; relatório da etapa apenas quando incluída.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 13133", "Levantamento topográfico", "13133", "NBR 13133", "ABNT NBR 15515 (série)", "Passivo ambiental em solo e água subterrânea", "15515", "NBR 15515"]},
  {"numero": "03", "nome": "Conferência do modelo 3D da obra", "grupo": "antes-de-contratar", "tipo": "catalogo", "dor": "Ocorrências do modelo não chegam a uma resposta validada dos projetistas e a uma decisão registrável.", "para_quem": {"decisor": "Gestor de engenharia com interfaces que precisam de resposta antes da compra ou execução.", "prestadora": "Projetista ou instaladora que deve explicar compatibilidade e pendências ao contratante."}, "beneficios": ["Coordenação entre disciplinas", "Rastreabilidade das revisões", "Controle técnico demonstrável"], "resultado_pratico": "Congelar versões, validar ocorrências, localizar consequência, diligenciar o autor e verificar a resposta na rodada incluída.", "entregas": "Matriz de ocorrências validadas; localizações e imagens; questões aos autores; registro das respostas e situação do recorte.", "limites": "Não presume modelagem nova, projeto executivo, revisão integral de cálculo ou solução assinada em nome do projetista.", "referencia": "ABNT NBR ISO 19650 (série) — Gestão da informação usando BIM: Organizar versões, intercâmbio, ocorrências e respostas no fluxo BIM adotado.; ABNT NBR 6492 — Documentação e representação de projetos arquitetônicos e urbanísticos: Conferir a documentação/representação de arquitetura no recorte examinado.; ABNT NBR 16636 (série) — Serviços técnicos de projetos arquitetônicos e urbanísticos: Relacionar a conferência às etapas/documentos dos serviços de projeto pertinentes.", "cta": "Envie as disciplinas, as versões e a interface que precisa de resposta.", "anchor": "servico-03", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Conferir interfaces de modelos e documentação com versões e respostas rastreáveis.", "criterios_principais": "Requisitos de informação do contrato e normas dos sistemas/disciplinas examinados.", "referencias": [{"id": "N19650", "codigo": "ABNT NBR ISO 19650 (série)", "nome": "Gestão da informação usando BIM", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "gestao_da_informacao", "aplicacao": "Organizar versões, intercâmbio, ocorrências e respostas no fluxo BIM adotado.", "condicao": "Selecionar partes pertinentes e requisitos de informação acordados.", "entrega_vinculada": "Matriz de ocorrências, responsáveis e revisões.", "partes_para_selecao": ["ABNT NBR ISO 19650-1", "ABNT NBR ISO 19650-2", "ABNT NBR ISO 19650-3", "ABNT NBR ISO 19650-4", "ABNT NBR ISO 19650-5"], "partes_detalhadas": [{"codigo": "ABNT NBR ISO 19650-1", "assunto": "Conceitos e princípios"}, {"codigo": "ABNT NBR ISO 19650-2", "assunto": "Fase de entrega de ativos"}, {"codigo": "ABNT NBR ISO 19650-3", "assunto": "Fase operacional dos ativos"}, {"codigo": "ABNT NBR ISO 19650-4", "assunto": "Troca de informação"}, {"codigo": "ABNT NBR ISO 19650-5", "assunto": "Segurança na gestão da informação"}]}, {"id": "N6492", "codigo": "ABNT NBR 6492", "nome": "Documentação e representação de projetos arquitetônicos e urbanísticos", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "documentacao_de_projeto", "aplicacao": "Conferir a documentação/representação de arquitetura no recorte examinado.", "condicao": "Quando a documentação arquitetônica/urbanística integrar o serviço.", "entrega_vinculada": "Registro de divergências documentais e representação.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N16636", "codigo": "ABNT NBR 16636 (série)", "nome": "Serviços técnicos de projetos arquitetônicos e urbanísticos", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "complementar_condicional", "aplicacao": "Relacionar a conferência às etapas/documentos dos serviços de projeto pertinentes.", "condicao": "Não constitui elaboração ou revisão integral de projeto.", "entrega_vinculada": "Quadro de entregas e interfaces de projeto.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR ISO 19650 (série)", "Gestão da informação usando BIM", "ABNT NBR ISO 19650-1", "ABNT NBR ISO 19650-2", "ABNT NBR ISO 19650-3", "ABNT NBR ISO 19650-4", "ABNT NBR ISO 19650-5", "Conceitos e princípios", "Fase de entrega de ativos", "Fase operacional dos ativos", "Troca de informação", "Segurança na gestão da informação", "19650", "NBR 19650", "ABNT NBR 6492", "Documentação e representação de projetos arquitetônicos e urbanísticos", "6492", "NBR 6492", "ABNT NBR 16636 (série)", "Serviços técnicos de projetos arquitetônicos e urbanísticos", "16636", "NBR 16636"]},
  {"numero": "04", "nome": "Fiscalização 360°", "grupo": "durante-a-execucao", "tipo": "catalogo", "dor": "As partes não conseguem relacionar o cobrado a critério contratual, quantidade e evidência suficiente.", "para_quem": {"decisor": "Gestor autorizado a decidir sobre medição/pagamento.", "prestadora": "Dono de prestadora que precisa estruturar e sustentar sua medição ao cliente."}, "beneficios": ["Transparência", "Prestação de contas", "Qualidade da primeira submissão"], "resultado_pratico": "Fixar critérios e corte, reconciliar itens/registros, conferir quantidades e diligenciar as exceções antes da recomendação.", "entregas": "Memória do ciclo; matriz item/evidência/diferença; diligências; recomendação técnica e pendências.", "limites": "Não presume fiscalização permanente, controle tecnológico, decisão de pagamento ou imagem capaz de medir sozinha.", "referencia": "Contrato, anexos de medição, projeto, especificações e normas do serviço medido. Não foi definida uma NBR única transversal para este produto.", "cta": "Apresente o contrato, o boletim e a data de corte.", "anchor": "servico-04", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Confrontar medição, critério contratual, quantidade e evidência de execução.", "criterios_principais": "Contrato, anexos de medição, projeto, especificações e normas do serviço medido.", "referencias": [], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": []},
  {"numero": "05", "nome": "Equalização de propostas e pleitos", "grupo": "antes-de-contratar", "tipo": "catalogo", "dor": "Bases incomparáveis na contratação ou cronologia e suporte insuficientes para discutir o evento contratual.", "para_quem": {"decisor": "Decisor que compara propostas ou deve responder a uma solicitação de alteração.", "prestadora": "Prestadora que precisa organizar uma comparação ou fundamentar tecnicamente um pedido ao seu cliente."}, "beneficios": ["Negociação mais clara", "Preparo técnico-contratual demonstrável", "Organização das evidências"], "resultado_pratico": "Contratação: equalizar escopo/unidades/bases. Pleitos: reconstruir evento/período, evidências, causas concorrentes e impacto, com encaminhamento jurídico próprio.", "entregas": "Aplicação contratação: mapa de equalização e questões. Aplicação pleito: cronologia, matriz de suporte, memória de impacto e questões para negociação.", "limites": "Não presume orçamento do zero, defesa jurídica, perícia integral ou procedência do pedido.", "referencia": "SINAPI — CAIXA — Referências técnicas e custos da construção: Comparar itens orçados com referência contextualizada, quando pertinente.; ABNT NBR 12721 — Custos de construção para incorporação e condomínios: Conferir referências de CUB/custos/quadros no campo de incorporação.; ABNT NBR 13752 — Perícias de engenharia na construção civil: Aplicar procedimento pericial quando houver contratação de natureza pericial.", "cta": "Informe se a questão é uma contratação ou um pleito e apresente a base disponível.", "anchor": "servico-05", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Comparar propostas equivalentes ou fundamentar tecnicamente um pleito delimitado.", "criterios_principais": "Escopo contratual, bases de preço e registros do evento analisado.", "referencias": [{"id": "R_SINAPI", "codigo": "SINAPI — CAIXA", "nome": "Referências técnicas e custos da construção", "tipo": "referencia_tecnica_ou_regulamentar", "papel_no_servico": "referencia_de_custo", "aplicacao": "Comparar itens orçados com referência contextualizada, quando pertinente.", "condicao": "Não constitui preço obrigatório nem economia já obtida.", "entrega_vinculada": "Mapa de equalização e memória das diferenças.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N12721", "codigo": "ABNT NBR 12721", "nome": "Custos de construção para incorporação e condomínios", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "complementar_condicional", "aplicacao": "Conferir referências de CUB/custos/quadros no campo de incorporação.", "condicao": "Apenas se essa finalidade integrar a comparação.", "entrega_vinculada": "Premissas e limites da referência de custos.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N13752", "codigo": "ABNT NBR 13752", "nome": "Perícias de engenharia na construção civil", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "servico_adicional", "aplicacao": "Aplicar procedimento pericial quando houver contratação de natureza pericial.", "condicao": "Não incluído automaticamente na análise comercial de proposta/pleito.", "entrega_vinculada": "Peça pericial própria apenas se contratada e enquadrada.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["SINAPI — CAIXA", "Referências técnicas e custos da construção", "ABNT NBR 12721", "Custos de construção para incorporação e condomínios", "12721", "NBR 12721", "ABNT NBR 13752", "Perícias de engenharia na construção civil", "13752", "NBR 13752"]},
  {"numero": "06", "nome": "Inspeção estrutural", "grupo": "ativos-e-estudos", "tipo": "catalogo", "dor": "Falta registro localizável do observado, da cobertura e das perguntas que exigem investigação.", "para_quem": {"decisor": "Proprietário ou gestor com manifestação aparente e necessidade de encaminhamento.", "prestadora": "Prestadora que deve registrar condições observadas e apresentar providências ao contratante."}, "beneficios": ["Condição registrada", "Comunicação ao gestor", "Continuidade da investigação"], "resultado_pratico": "Definir finalidade/cobertura, observar e identificar ocorrências, registrar limitações e propor investigação/prioridade pertinente.", "entregas": "Registro da cobertura e das condições; manifestações localizadas; limitações; encaminhamentos e plano de investigação no alcance.", "limites": "Não presume declaração de estabilidade, diagnóstico estrutural integral, ensaio, cálculo ou projeto de recuperação.", "referencia": "ABNT NBR 16747 — Inspeção predial: Definir o alcance de inspeção predial quando esse serviço for contratado.; ABNT NBR 5674 — Gestão da manutenção de edificações: Relacionar as constatações com programa/histórico de manutenção.", "cta": "Informe o ativo, a ocorrência e a finalidade da inspeção.", "anchor": "servico-06", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Registrar manifestações, cobertura e encaminhamentos de investigação no alcance contratado.", "criterios_principais": "Escopo de inspeção, histórico e normas dos sistemas efetivamente examinados.", "referencias": [{"id": "N16747", "codigo": "ABNT NBR 16747", "nome": "Inspeção predial", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "escopo_de_inspecao_a_enquadrar", "aplicacao": "Definir o alcance de inspeção predial quando esse serviço for contratado.", "condicao": "Vistoria visual localizada não equivale, por si, à inspeção predial abrangida pela norma.", "entrega_vinculada": "Relatório de cobertura, constatações, limitações e prioridades no método adotado.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N5674", "codigo": "ABNT NBR 5674", "nome": "Gestão da manutenção de edificações", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "interface_de_manutencao", "aplicacao": "Relacionar as constatações com programa/histórico de manutenção.", "condicao": "Somente registros e avaliações incluídos; não comprova manutenção passada.", "entrega_vinculada": "Pendências e encaminhamentos de manutenção.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 16747", "Inspeção predial", "16747", "NBR 16747", "ABNT NBR 5674", "Gestão da manutenção de edificações", "5674", "NBR 5674"]},
  {"numero": "07", "nome": "Custo para concluir a obra", "grupo": "durante-a-execucao", "tipo": "catalogo", "dor": "Custo incorrido, desembolso, compromissos e serviços restantes são misturados, impedindo uma visão explicável da conclusão.", "para_quem": {"decisor": "Proprietário, financiador ou diretor que precisa decidir novo aporte ou prioridade de conclusão.", "prestadora": "Dono de prestadora que precisa explicar saldo, recursos e condições para concluir seu contrato."}, "beneficios": ["Previsibilidade de conclusão", "Alinhamento entre interessados", "Domínio das premissas demonstrável"], "resultado_pratico": "Fixar corte, reconciliar avanço/custos/compromissos, estimar remanescentes por pacote e explicitar cenários e decisões.", "entregas": "Mapa do saldo e sua base; cenários; premissas e riscos; decisões e marcos; atualização no ciclo contratado.", "limites": "Não presume rating, autorização de crédito, auditoria financeira ou garantia de preço final.", "referencia": "SINAPI — CAIXA — Referências técnicas e custos da construção: Contextualizar custos do saldo por serviço, UF e data-base.; SICRO — DNIT — Custos referenciais de infraestrutura de transportes: Contextualizar itens de infraestrutura de transportes, quando pertinentes.; ABNT NBR 12721 — Custos de construção para incorporação e condomínios: Identificar limites de referência baseada em CUB/quadros de incorporação.", "cta": "Apresente o saldo de serviços, os compromissos e a próxima decisão de aporte.", "anchor": "servico-07", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Estimar o saldo de serviços e distinguir custo, compromissos e desembolso.", "criterios_principais": "Quantidades do saldo, compromissos, escopo vigente e condições de execução.", "referencias": [{"id": "R_SINAPI", "codigo": "SINAPI — CAIXA", "nome": "Referências técnicas e custos da construção", "tipo": "referencia_tecnica_ou_regulamentar", "papel_no_servico": "referencia_de_custo", "aplicacao": "Contextualizar custos do saldo por serviço, UF e data-base.", "condicao": "Conferir adequação da composição ao saldo real.", "entrega_vinculada": "Memória de custo para concluir e cenários.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "R_SICRO", "codigo": "SICRO — DNIT", "nome": "Custos referenciais de infraestrutura de transportes", "tipo": "referencia_tecnica_ou_regulamentar", "papel_no_servico": "referencia_de_custo", "aplicacao": "Contextualizar itens de infraestrutura de transportes, quando pertinentes.", "condicao": "Somente serviços cobertos e condições comparáveis.", "entrega_vinculada": "Memória específica de itens de infraestrutura.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N12721", "codigo": "ABNT NBR 12721", "nome": "Custos de construção para incorporação e condomínios", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "complementar_condicional", "aplicacao": "Identificar limites de referência baseada em CUB/quadros de incorporação.", "condicao": "Não é método universal para fechar saldo de obra.", "entrega_vinculada": "Premissas e maturidade da estimativa.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["SINAPI — CAIXA", "Referências técnicas e custos da construção", "SICRO — DNIT", "Custos referenciais de infraestrutura de transportes", "ABNT NBR 12721", "Custos de construção para incorporação e condomínios", "12721", "NBR 12721"]},
  {"numero": "08", "nome": "Triagem técnica para compra de ativos", "grupo": "ativos-e-estudos", "tipo": "catalogo", "dor": "Informação incompleta impede separar alertas aparentes, investimento preliminar e investigações necessárias.", "para_quem": {"decisor": "Comprador ou investidor com negociação aberta e dúvida técnica delimitada.", "prestadora": "Assessora/gerenciadora que precisa entregar ao comprador um recorte técnico da diligência."}, "beneficios": ["Diligência organizada", "Clareza sobre incertezas", "Fundamentação da recomendação"], "resultado_pratico": "Fixar uso pretendido e cobertura, examinar documentos/acesso, localizar alertas e encaminhar aprofundamento.", "entregas": "Matriz de alertas; fontes/cobertura; investimento preliminar quando incluído; diligências e condições a verificar.", "limites": "Não presume avaliação integral, diligência jurídica/ambiental completa ou ausência de vícios.", "referencia": "ABNT NBR 16747 — Inspeção predial: Relacionar a triagem ao alcance de inspeção física efetivamente incluído.; ABNT NBR 14653 (série) — Avaliação de bens: Orientar avaliação de valor do bem quando contratada separadamente.; ABNT NBR 15515 (série) — Passivo ambiental em solo e água subterrânea: Enquadrar diligências de passivo ambiental se a tese de compra exigir.", "cta": "Informe o ativo, o uso pretendido e o prazo da aquisição.", "anchor": "servico-08", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Identificar alertas e diligências antes da aquisição de um ativo.", "criterios_principais": "Finalidade da aquisição, documentação do imóvel e sistemas incluídos.", "referencias": [{"id": "N16747", "codigo": "ABNT NBR 16747", "nome": "Inspeção predial", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "atividade_delimitada", "aplicacao": "Relacionar a triagem ao alcance de inspeção física efetivamente incluído.", "condicao": "Inspeção predial completa exige contratação correspondente.", "entrega_vinculada": "Relatório de alertas e cobertura da visita.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N14653", "codigo": "ABNT NBR 14653 (série)", "nome": "Avaliação de bens", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "servico_adicional", "aplicacao": "Orientar avaliação de valor do bem quando contratada separadamente.", "condicao": "Triagem técnica não é laudo de avaliação imobiliária.", "entrega_vinculada": "Laudo de avaliação apenas se incluído e enquadrado.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N15515", "codigo": "ABNT NBR 15515 (série)", "nome": "Passivo ambiental em solo e água subterrânea", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "modulo_especializado", "aplicacao": "Enquadrar diligências de passivo ambiental se a tese de compra exigir.", "condicao": "Investigação ambiental depende de etapa/competência/recursos específicos.", "entrega_vinculada": "Lista de diligências e evidências ambientais contratadas.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 16747", "Inspeção predial", "16747", "NBR 16747", "ABNT NBR 14653 (série)", "Avaliação de bens", "14653", "NBR 14653", "ABNT NBR 15515 (série)", "Passivo ambiental em solo e água subterrânea", "15515", "NBR 15515"]},
  {"numero": "09", "nome": "Conferência de notas fiscais e medição", "grupo": "durante-a-execucao", "tipo": "catalogo", "dor": "Cadastros, unidades e movimentos não conciliados tornam diferenças inexplicáveis.", "para_quem": {"decisor": "Gestor/dono que precisa compreender diferenças de materiais e apropriação.", "prestadora": "Prestadora que deve prestar contas das compras, incorporações e medições ao cliente."}, "beneficios": ["Organização entre suprimentos e obra", "Prestação de contas", "Controle de materiais demonstrável"], "resultado_pratico": "Fixar corte/saldo inicial, mapear itens/unidades, incorporar movimentos e diligenciar as exceções com fonte.", "entregas": "Mapa de conciliação; critérios de associação/conversão; exceções e justificativas; pendências e recomendações.", "limites": "Não presume validação fiscal, prova de fraude, inventário físico ou integração de sistemas.", "referencia": "Contrato, documentos de compra, critérios de associação/conversão e registros de estoque/consumo. Não foi definida uma NBR única transversal para este produto.", "cta": "Apresente o período, os materiais e a divergência a esclarecer.", "anchor": "servico-09", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Conciliar documentos, unidades e movimentos de materiais com a medição.", "criterios_principais": "Contrato, documentos de compra, critérios de associação/conversão e registros de estoque/consumo.", "referencias": [], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": []},
  {"numero": "10", "nome": "Análise técnica de licitações", "grupo": "antes-de-contratar", "tipo": "catalogo", "dor": "Obrigações, quantitativos ou condições técnicas não estão claros para preço, capacidade e execução.", "para_quem": {"decisor": "Dono de prestadora que decide participar, pedir esclarecimento ou formar preço.", "prestadora": "Consultora que deve entregar uma análise técnica do edital ao seu cliente."}, "beneficios": ["Preparo para participar", "Alinhamento comercial-execução", "Capacidade de explicar a proposta"], "resultado_pratico": "Confrontar anexos, referências e orçamento, formular a questão, estimar consequência no nível possível e encaminhar aspectos jurídicos.", "entregas": "Nota técnica com fonte, questão, consequência e premissas; matriz para esclarecimento e validação jurídica.", "limites": "Não presume advocacia, protocolo, habilitação, acervo ou vitória.", "referencia": "SINAPI — CAIXA — Referências técnicas e custos da construção: Conferir referência de custos usada no orçamento analisado.; SICRO — DNIT — Custos referenciais de infraestrutura de transportes: Conferir referência de infraestrutura quando adotada no objeto.", "cta": "Apresente o edital, sua dúvida técnica e o prazo disponível.", "anchor": "servico-10", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Identificar exigências e divergências técnicas que afetam a proposta do licitante.", "criterios_principais": "Edital e retificações, anexos, projetos, especificações e normas expressamente pertinentes ao objeto.", "referencias": [{"id": "R_SINAPI", "codigo": "SINAPI — CAIXA", "nome": "Referências técnicas e custos da construção", "tipo": "referencia_tecnica_ou_regulamentar", "papel_no_servico": "referencia_de_custo", "aplicacao": "Conferir referência de custos usada no orçamento analisado.", "condicao": "Quando pertinente ao edital, serviço e regime de referência.", "entrega_vinculada": "Nota técnica com memória de divergências.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "R_SICRO", "codigo": "SICRO — DNIT", "nome": "Custos referenciais de infraestrutura de transportes", "tipo": "referencia_tecnica_ou_regulamentar", "papel_no_servico": "referencia_de_custo", "aplicacao": "Conferir referência de infraestrutura quando adotada no objeto.", "condicao": "Não se aplica automaticamente a qualquer edital.", "entrega_vinculada": "Memória técnica contextualizada.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["SINAPI — CAIXA", "Referências técnicas e custos da construção", "SICRO — DNIT", "Custos referenciais de infraestrutura de transportes"]},
  {"numero": "11", "nome": "Gêmeo digital leve", "grupo": "durante-a-execucao", "tipo": "catalogo", "dor": "Fotos avulsas e equipes diferentes não permitem uma comparação confiável entre campanhas.", "para_quem": {"decisor": "Gestor de ativo com necessidade de observar evolução e decidir aprofundamento.", "prestadora": "Prestadora que deve manter um histórico técnico comparável para o contratante."}, "beneficios": ["Continuidade de informação", "Comunicação objetiva", "Rotina de acompanhamento demonstrável"], "resultado_pratico": "Definir pergunta, protocolo e condição inicial; coletar campanhas; verificar comparabilidade/incerteza e encaminhar o que exige investigação.", "entregas": "Protocolo; séries revisadas; comparabilidade e limitações; alertas e encaminhamentos.", "limites": "Não presume monitoramento contínuo, vigilância estrutural, estabilidade ou diagnóstico da causa.", "referencia": "ABNT NBR 16747 — Inspeção predial: Vincular registros de campanha às informações de inspeção no alcance incluído.; ABNT NBR 5674 — Gestão da manutenção de edificações: Organizar o histórico para apoiar gestão de manutenção.; ABNT NBR ISO 19650 (série) — Gestão da informação usando BIM: Organizar a informação do ativo quando adotado processo de gestão BIM.", "cta": "Informe o que precisa ser acompanhado e qual decisão depende da evolução.", "anchor": "servico-11", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Produzir registros comparáveis de manifestações entre campanhas.", "criterios_principais": "Protocolo de observação, pontos, método, condições e frequência contratados.", "referencias": [{"id": "N16747", "codigo": "ABNT NBR 16747", "nome": "Inspeção predial", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "interface_de_inspecao", "aplicacao": "Vincular registros de campanha às informações de inspeção no alcance incluído.", "condicao": "Série visual não substitui inspeção integral ou diagnóstico causal.", "entrega_vinculada": "Histórico localizado, comparabilidade e encaminhamentos.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N5674", "codigo": "ABNT NBR 5674", "nome": "Gestão da manutenção de edificações", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "registros_de_manutencao", "aplicacao": "Organizar o histórico para apoiar gestão de manutenção.", "condicao": "Não comprova segurança nem execução de manutenção.", "entrega_vinculada": "Séries e registros com versão/data/ponto.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N19650", "codigo": "ABNT NBR ISO 19650 (série)", "nome": "Gestão da informação usando BIM", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "complementar_condicional", "aplicacao": "Organizar a informação do ativo quando adotado processo de gestão BIM.", "condicao": "Modelo digital leve não atende automaticamente à série.", "entrega_vinculada": "Cadastro informacional conforme recorte acordado.", "partes_para_selecao": ["ABNT NBR ISO 19650-1", "ABNT NBR ISO 19650-2", "ABNT NBR ISO 19650-3", "ABNT NBR ISO 19650-4", "ABNT NBR ISO 19650-5"], "partes_detalhadas": [{"codigo": "ABNT NBR ISO 19650-1", "assunto": "Conceitos e princípios"}, {"codigo": "ABNT NBR ISO 19650-2", "assunto": "Fase de entrega de ativos"}, {"codigo": "ABNT NBR ISO 19650-3", "assunto": "Fase operacional dos ativos"}, {"codigo": "ABNT NBR ISO 19650-4", "assunto": "Troca de informação"}, {"codigo": "ABNT NBR ISO 19650-5", "assunto": "Segurança na gestão da informação"}]}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 16747", "Inspeção predial", "16747", "NBR 16747", "ABNT NBR 5674", "Gestão da manutenção de edificações", "5674", "NBR 5674", "ABNT NBR ISO 19650 (série)", "Gestão da informação usando BIM", "ABNT NBR ISO 19650-1", "ABNT NBR ISO 19650-2", "ABNT NBR ISO 19650-3", "ABNT NBR ISO 19650-4", "ABNT NBR ISO 19650-5", "Conceitos e princípios", "Fase de entrega de ativos", "Fase operacional dos ativos", "Troca de informação", "Segurança na gestão da informação", "19650", "NBR 19650"]},
  {"numero": "12", "nome": "Carbono incorporado e custo", "grupo": "ativos-e-estudos", "tipo": "catalogo", "dor": "Custo e carbono são comparados com funções, fronteiras ou dados incompatíveis.", "para_quem": {"decisor": "Gestor de projeto/compras com alternativa material ou requisito ambiental definido.", "prestadora": "Fornecedor ou prestadora que precisa demonstrar ao cliente a base da alternativa proposta."}, "beneficios": ["Transparência ambiental", "Capacidade analítica demonstrável", "Resposta a exigências de clientes"], "resultado_pratico": "Definir função, fronteira e método; qualificar dados; calcular alternativas; testar sensibilidade e explicar limites.", "entregas": "Memória de cálculo; dados/fontes/qualidade; comparação e sensibilidade; condições de uso da conclusão.", "limites": "Não presume neutralidade, crédito de carbono, certificação, EPD ou ACV completa.", "referencia": "ISO 14040 — Avaliação do ciclo de vida — princípios e estrutura: Definir objetivo, função, fronteira e estrutura de comparação.; ISO 14044 — Avaliação do ciclo de vida — requisitos e diretrizes: Fundamentar inventário, cálculos, interpretação e revisão no alcance contratado.", "cta": "Apresente as alternativas, a função e a exigência ambiental.", "anchor": "servico-12", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Comparar carbono e custo de alternativas na mesma função e fronteira.", "criterios_principais": "Objetivo, unidade funcional, fronteira, dados de materiais e fontes de fatores.", "referencias": [{"id": "I14040", "codigo": "ISO 14040", "nome": "Avaliação do ciclo de vida — princípios e estrutura", "tipo": "norma_ISO_internacional", "papel_no_servico": "referencia_metodologica", "aplicacao": "Definir objetivo, função, fronteira e estrutura de comparação.", "condicao": "Adoção nacional e método do estudo são confirmados no enquadramento.", "entrega_vinculada": "Objetivo/escopo e inventário de fontes.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "I14044", "codigo": "ISO 14044", "nome": "Avaliação do ciclo de vida — requisitos e diretrizes", "tipo": "norma_ISO_internacional", "papel_no_servico": "referencia_metodologica", "aplicacao": "Fundamentar inventário, cálculos, interpretação e revisão no alcance contratado.", "condicao": "Comparação simplificada não se torna ACV integral, EPD ou crédito.", "entrega_vinculada": "Memória, sensibilidade, interpretação e limites.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ISO 14040", "Avaliação do ciclo de vida — princípios e estrutura", "14040", "ISO 14044", "Avaliação do ciclo de vida — requisitos e diretrizes", "14044"]},
  {"numero": "13", "nome": "Desempenho e requisitos", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "Requisito, configuração comprada, evidência de produto e condição instalada não estão relacionados de forma suficiente.", "para_quem": {"decisor": "Dono/gestor com requisito de sistema que precisa avaliar compra, substituição ou comprovação.", "prestadora": "Prestadora/fornecedora que deve reunir e demonstrar ao cliente as evidências do seu escopo."}, "beneficios": ["Atendimento aos requisitos demonstrável", "Coordenação de fornecedores", "Organização da comprovação"], "resultado_pratico": "Verificar aplicabilidade, identificar requisitos/métodos, vincular evidência à configuração, tratar lacunas e emitir conclusão humana delimitada.", "entregas": "Ficha de aplicabilidade; matriz por requisito/configuração; diligências; conclusões e pendências; pasta de comprovação do recorte.", "limites": "Não presume certificação integral, ensaios/simulações incluídos ou conclusão sobre edificação inteira.", "referencia": "ABNT NBR 15575 — Desempenho de edificações habitacionais: Analisar requisitos e evidências dos sistemas habitacionais contratados.; ABNT NBR 10151 — Avaliação de ruído em áreas habitadas: Enquadrar perguntas de ruído em áreas habitadas.; ABNT NBR 10152 — Níveis de pressão sonora em ambientes internos: Enquadrar perguntas de condições acústicas internas.; ABNT NBR 10821 (série) — Esquadrias para edificações: Conferir referências da esquadria/configuração pertinente.; ABNT NBR ISO/IEC 17025 — Competência de laboratórios de ensaio e calibração: Conferir pertinência da evidência laboratorial e do escopo exigido.", "cta": "Apresente o sistema, a exigência e o marco de compra ou entrega.", "anchor": "servico-13", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": "Sob demanda", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Relacionar requisito de desempenho, configuração instalada e evidência pertinente.", "criterios_principais": "Uso habitacional, sistemas, configurações, partes e métodos aplicáveis.", "referencias": [{"id": "N15575", "codigo": "ABNT NBR 15575", "nome": "Desempenho de edificações habitacionais", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "requisito_do_objeto", "aplicacao": "Analisar requisitos e evidências dos sistemas habitacionais contratados.", "condicao": "Selecionar partes 1 a 6, sistemas/requisitos e método; não declarar desempenho integral por uma análise parcial.", "entrega_vinculada": "Matriz requisito/configuração/método/evidência, relatório e pasta de comprovação.", "partes_para_selecao": ["ABNT NBR 15575-1", "ABNT NBR 15575-2", "ABNT NBR 15575-3", "ABNT NBR 15575-4", "ABNT NBR 15575-5", "ABNT NBR 15575-6"], "partes_detalhadas": [{"codigo": "ABNT NBR 15575-1", "assunto": "Requisitos gerais"}, {"codigo": "ABNT NBR 15575-2", "assunto": "Sistemas estruturais"}, {"codigo": "ABNT NBR 15575-3", "assunto": "Sistemas de pisos"}, {"codigo": "ABNT NBR 15575-4", "assunto": "Vedações verticais internas e externas"}, {"codigo": "ABNT NBR 15575-5", "assunto": "Sistemas de coberturas"}, {"codigo": "ABNT NBR 15575-6", "assunto": "Sistemas hidrossanitários"}]}, {"id": "N10151", "codigo": "ABNT NBR 10151", "nome": "Avaliação de ruído em áreas habitadas", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "modulo_acustico", "aplicacao": "Enquadrar perguntas de ruído em áreas habitadas.", "condicao": "Somente quando essa grandeza responder à pergunta contratada.", "entrega_vinculada": "Análise da evidência de ruído ambiental; medição própria só quando incluída.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N10152", "codigo": "ABNT NBR 10152", "nome": "Níveis de pressão sonora em ambientes internos", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "modulo_acustico", "aplicacao": "Enquadrar perguntas de condições acústicas internas.", "condicao": "Não é método intercambiável de isolamento de sistema.", "entrega_vinculada": "Análise de evidências internas ou relatório específico contratado.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N10821", "codigo": "ABNT NBR 10821 (série)", "nome": "Esquadrias para edificações", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "sistema_especifico", "aplicacao": "Conferir referências da esquadria/configuração pertinente.", "condicao": "Selecionar parte, sistema e método; documento de produto diferente não comprova a instalação.", "entrega_vinculada": "Quadro configuração/evidência e diligências da esquadria.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N17025", "codigo": "ABNT NBR ISO/IEC 17025", "nome": "Competência de laboratórios de ensaio e calibração", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "qualificacao_da_evidencia", "aplicacao": "Conferir pertinência da evidência laboratorial e do escopo exigido.", "condicao": "Acreditação é conferida por laboratório/atividade/método; CRIVIA não se torna laboratório acreditado.", "entrega_vinculada": "Registro de conferência da evidência/escopo do laboratório.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 15575", "Desempenho de edificações habitacionais", "ABNT NBR 15575-1", "ABNT NBR 15575-2", "ABNT NBR 15575-3", "ABNT NBR 15575-4", "ABNT NBR 15575-5", "ABNT NBR 15575-6", "Requisitos gerais", "Sistemas estruturais", "Sistemas de pisos", "Vedações verticais internas e externas", "Sistemas de coberturas", "Sistemas hidrossanitários", "15575", "NBR 15575", "ABNT NBR 10151", "Avaliação de ruído em áreas habitadas", "10151", "NBR 10151", "ABNT NBR 10152", "Níveis de pressão sonora em ambientes internos", "10152", "NBR 10152", "ABNT NBR 10821 (série)", "Esquadrias para edificações", "10821", "NBR 10821", "ABNT NBR ISO/IEC 17025", "Competência de laboratórios de ensaio e calibração", "17025", "NBR 17025"]},
  {"numero": "14", "nome": "Organização da entrega documental", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "Arquivos, versões e faltantes impedem uma entrega utilizável e deixam o controle da prestadora pouco visível.", "para_quem": {"decisor": "Contratante que precisa conferir o pacote recebido e conduzir pendências.", "prestadora": "Dono de prestadora/instaladora que precisa entregar documentação organizada ao cliente final."}, "beneficios": ["Organização utilizável", "Capacidade técnica efetivamente exercida demonstrada", "Continuidade para o cliente"], "resultado_pratico": "Fixar lista e profundidade, inventariar, organizar, atribuir faltantes, conduzir diligências, conferir, produzir índice e submeter o pacote.", "entregas": "Índice mestre e estrutura; matriz de completude; arquivos organizados; instrumentos próprios contratados; diligências, pendências e protocolo.", "limites": "Não presume emissão por terceiros, validação integral de disciplinas, aceite garantido, comando da obra ou entrega que a contratante não executou.", "referencia": "ABNT NBR 14037 — Manuais de uso, operação e manutenção: Organizar/conferir o manual de uso, operação e manutenção que integrar o pacote.; ABNT NBR 5674 — Gestão da manutenção de edificações: Organizar programa/registros de manutenção exigidos na passagem à operação.; ABNT NBR 15575 — Desempenho de edificações habitacionais: Relacionar evidências de desempenho às exigências do pacote habitacional.; ABNT NBR 14645 (série) — Como construído, levantamentos e controle dimensional: Organizar registros de levantamento/controle pertinentes ao como construído.; ABNT NBR ISO 19650 (série) — Gestão da informação usando BIM: Organizar informações de entrega do ativo no processo BIM adotado.", "cta": "Apresente a lista de entrega, uma amostra do acervo e o prazo.", "anchor": "servico-14", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": null, "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Fechar um pacote documental utilizável, com exigências, versões e faltantes controlados.", "criterios_principais": "Lista de entrega do contrato, profundidade de conferência e documentos dos sistemas.", "referencias": [{"id": "N14037", "codigo": "ABNT NBR 14037", "nome": "Manuais de uso, operação e manutenção", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "documento_de_entrega", "aplicacao": "Organizar/conferir o manual de uso, operação e manutenção que integrar o pacote.", "condicao": "Elaboração própria e validação técnica precisam estar expressamente incluídas.", "entrega_vinculada": "Manual no alcance contratado, índice e matriz de pendências.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N5674", "codigo": "ABNT NBR 5674", "nome": "Gestão da manutenção de edificações", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "documento_de_entrega", "aplicacao": "Organizar programa/registros de manutenção exigidos na passagem à operação.", "condicao": "Não presume implantar ou executar toda a gestão de manutenção.", "entrega_vinculada": "Programa/registros incluídos e responsabilidades.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N15575", "codigo": "ABNT NBR 15575", "nome": "Desempenho de edificações habitacionais", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "comprovacao_documental", "aplicacao": "Relacionar evidências de desempenho às exigências do pacote habitacional.", "condicao": "Suficiência técnica é conferida no alcance; organização não equivale a desempenho comprovado.", "entrega_vinculada": "Pasta de evidências indexada e pendências por requisito.", "partes_para_selecao": ["ABNT NBR 15575-1", "ABNT NBR 15575-2", "ABNT NBR 15575-3", "ABNT NBR 15575-4", "ABNT NBR 15575-5", "ABNT NBR 15575-6"], "partes_detalhadas": [{"codigo": "ABNT NBR 15575-1", "assunto": "Requisitos gerais"}, {"codigo": "ABNT NBR 15575-2", "assunto": "Sistemas estruturais"}, {"codigo": "ABNT NBR 15575-3", "assunto": "Sistemas de pisos"}, {"codigo": "ABNT NBR 15575-4", "assunto": "Vedações verticais internas e externas"}, {"codigo": "ABNT NBR 15575-5", "assunto": "Sistemas de coberturas"}, {"codigo": "ABNT NBR 15575-6", "assunto": "Sistemas hidrossanitários"}]}, {"id": "N14645", "codigo": "ABNT NBR 14645 (série)", "nome": "Como construído, levantamentos e controle dimensional", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "complementar_condicional", "aplicacao": "Organizar registros de levantamento/controle pertinentes ao como construído.", "condicao": "A série não é norma universal para todo as built de todas as disciplinas.", "entrega_vinculada": "Registros identificados por parte, disciplina e autoria.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N19650", "codigo": "ABNT NBR ISO 19650 (série)", "nome": "Gestão da informação usando BIM", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "gestao_da_informacao", "aplicacao": "Organizar informações de entrega do ativo no processo BIM adotado.", "condicao": "Requisitos informacionais/partes aplicáveis precisam estar acordados.", "entrega_vinculada": "Índice de informações, versões e protocolo de entrega.", "partes_para_selecao": ["ABNT NBR ISO 19650-1", "ABNT NBR ISO 19650-2", "ABNT NBR ISO 19650-3", "ABNT NBR ISO 19650-4", "ABNT NBR ISO 19650-5"], "partes_detalhadas": [{"codigo": "ABNT NBR ISO 19650-1", "assunto": "Conceitos e princípios"}, {"codigo": "ABNT NBR ISO 19650-2", "assunto": "Fase de entrega de ativos"}, {"codigo": "ABNT NBR ISO 19650-3", "assunto": "Fase operacional dos ativos"}, {"codigo": "ABNT NBR ISO 19650-4", "assunto": "Troca de informação"}, {"codigo": "ABNT NBR ISO 19650-5", "assunto": "Segurança na gestão da informação"}]}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 14037", "Manuais de uso, operação e manutenção", "14037", "NBR 14037", "ABNT NBR 5674", "Gestão da manutenção de edificações", "5674", "NBR 5674", "ABNT NBR 15575", "Desempenho de edificações habitacionais", "ABNT NBR 15575-1", "ABNT NBR 15575-2", "ABNT NBR 15575-3", "ABNT NBR 15575-4", "ABNT NBR 15575-5", "ABNT NBR 15575-6", "Requisitos gerais", "Sistemas estruturais", "Sistemas de pisos", "Vedações verticais internas e externas", "Sistemas de coberturas", "Sistemas hidrossanitários", "15575", "NBR 15575", "ABNT NBR 14645 (série)", "Como construído, levantamentos e controle dimensional", "14645", "NBR 14645", "ABNT NBR ISO 19650 (série)", "Gestão da informação usando BIM", "ABNT NBR ISO 19650-1", "ABNT NBR ISO 19650-2", "ABNT NBR ISO 19650-3", "ABNT NBR ISO 19650-4", "ABNT NBR ISO 19650-5", "Conceitos e princípios", "Fase de entrega de ativos", "Fase operacional dos ativos", "Troca de informação", "Segurança na gestão da informação", "19650", "NBR 19650"]},
  {"numero": "15", "nome": "Manutenção e registros de garantias", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "Atividades, responsáveis e registros não permitem continuidade ou explicação adequada das providências.", "para_quem": {"decisor": "Gestor/proprietário que precisa estruturar plano e histórico ou encaminhar ocorrência.", "prestadora": "Prestadora que deve entregar registros e orientação de manutenção ao cliente."}, "beneficios": ["Rotina organizada", "Continuidade e autonomia", "Cuidado com o ativo demonstrável"], "resultado_pratico": "Identificar ativo/sistemas e referências, estruturar plano/evidência, conferir histórico e acompanhar ações no ciclo contratado.", "entregas": "Plano/estrutura de registros no alcance; matriz de responsabilidades; histórico organizado; pendências e encaminhamentos.", "limites": "Não presume execução diária da manutenção, reparos, parecer jurídico ou garantia preservada automaticamente.", "referencia": "ABNT NBR 5674 — Gestão da manutenção de edificações: Estruturar programa, responsáveis e registros de manutenção no alcance contratado.; ABNT NBR 14037 — Manuais de uso, operação e manutenção: Relacionar o programa às instruções do manual específico da edificação.; ABNT NBR 17170 — Garantias de edificações: Organizar referências, datas, condições e registros das ocorrências.", "cta": "Apresente o ativo, os registros existentes e a necessidade de operação.", "anchor": "servico-15", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": null, "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Organizar programa, responsabilidades, histórico de manutenção e registros de garantias.", "criterios_principais": "Ativo, sistemas, fontes das atividades/frequências e fatos das ocorrências.", "referencias": [{"id": "N5674", "codigo": "ABNT NBR 5674", "nome": "Gestão da manutenção de edificações", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "requisito_de_gestao", "aplicacao": "Estruturar programa, responsáveis e registros de manutenção no alcance contratado.", "condicao": "Execução declarada e execução verificada têm estados separados.", "entrega_vinculada": "Programa, calendário, matriz de responsabilidades e histórico.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N14037", "codigo": "ABNT NBR 14037", "nome": "Manuais de uso, operação e manutenção", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "interface_documental", "aplicacao": "Relacionar o programa às instruções do manual específico da edificação.", "condicao": "Revisão/elaboração de manual só se incluída.", "entrega_vinculada": "Lista de instruções/fontes e pendências do manual.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N17170", "codigo": "ABNT NBR 17170", "nome": "Garantias de edificações", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "registro_de_garantias", "aplicacao": "Organizar referências, datas, condições e registros das ocorrências.", "condicao": "Não determina automaticamente direito ou perda de garantia.", "entrega_vinculada": "Histórico das ocorrências e encaminhamento técnico/jurídico pertinente.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 5674", "Gestão da manutenção de edificações", "5674", "NBR 5674", "ABNT NBR 14037", "Manuais de uso, operação e manutenção", "14037", "NBR 14037", "ABNT NBR 17170", "Garantias de edificações", "17170", "NBR 17170"]},
  {"numero": "16", "nome": "Documentação e interfaces de reformas", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "Escopo, interfaces, responsabilidades e documentação não estão organizados nos marcos necessários.", "para_quem": {"decisor": "Proprietário/gestor que precisa compreender documentos e responsabilidades para a intervenção.", "prestadora": "Responsável pela execução da obra, seja um projeto novo ou uma reforma, que deve apresentar ao cliente ou à gestão do imóvel o plano e os registros pertinentes."}, "beneficios": ["Planejamento demonstrável", "Comunicação entre partes", "Controle das alterações"], "resultado_pratico": "Enquadrar intervenção, selecionar requisitos, confrontar plano e registros, diligenciar responsáveis e preparar a entrega do recorte.", "entregas": "Matriz de requisitos/documentos; interfaces; diligências; responsabilidades; alterações e pacote de entrega no alcance.", "limites": "Não presume projeto integral, autorização formal, execução, aprovação do condomínio/órgão ou ausência de risco.", "referencia": "ABNT NBR 16280 — Gestão de reformas em edificações: Estruturar a documentação e as responsabilidades da reforma no recorte contratado.; ABNT NBR 14037 — Manuais de uso, operação e manutenção: Organizar instruções/manuais das partes reformadas quando exigidos e incluídos.; ABNT NBR 17170 — Garantias de edificações: Relacionar registros e termos pertinentes às partes reformadas.; ABNT NBR 15575 — Desempenho de edificações habitacionais: Examinar interface com requisitos de desempenho quando o caso justificar.", "cta": "Descreva a intervenção, os sistemas e o marco previsto.", "anchor": "servico-16", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": null, "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Organizar requisitos, documentos, interfaces e alterações da reforma.", "criterios_principais": "Intervenção, sistemas afetados, responsáveis e regras do imóvel/órgãos.", "referencias": [{"id": "N16280", "codigo": "ABNT NBR 16280", "nome": "Gestão de reformas em edificações", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "requisito_de_gestao", "aplicacao": "Estruturar a documentação e as responsabilidades da reforma no recorte contratado.", "condicao": "Gestão documental não equivale à aprovação integral nem substitui projetos/execução.", "entrega_vinculada": "Matriz documental, interfaces, alterações e protocolo.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N14037", "codigo": "ABNT NBR 14037", "nome": "Manuais de uso, operação e manutenção", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "documento_de_encerramento", "aplicacao": "Organizar instruções/manuais das partes reformadas quando exigidos e incluídos.", "condicao": "Autoria/atualização técnica devem ser definidas por disciplina.", "entrega_vinculada": "Documentos de uso/manutenção das partes modificadas.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N17170", "codigo": "ABNT NBR 17170", "nome": "Garantias de edificações", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "interface_de_garantias", "aplicacao": "Relacionar registros e termos pertinentes às partes reformadas.", "condicao": "Prazo/direito dependem de fatos e enquadramento; não são automatizados.", "entrega_vinculada": "Registro de garantias e pendências do encerramento.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N15575", "codigo": "ABNT NBR 15575", "nome": "Desempenho de edificações habitacionais", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "complementar_condicional", "aplicacao": "Examinar interface com requisitos de desempenho quando o caso justificar.", "condicao": "Não aplicar automaticamente todos os requisitos de obra nova à reforma.", "entrega_vinculada": "Enquadramento e diligências de desempenho no recorte.", "partes_para_selecao": ["ABNT NBR 15575-1", "ABNT NBR 15575-2", "ABNT NBR 15575-3", "ABNT NBR 15575-4", "ABNT NBR 15575-5", "ABNT NBR 15575-6"], "partes_detalhadas": [{"codigo": "ABNT NBR 15575-1", "assunto": "Requisitos gerais"}, {"codigo": "ABNT NBR 15575-2", "assunto": "Sistemas estruturais"}, {"codigo": "ABNT NBR 15575-3", "assunto": "Sistemas de pisos"}, {"codigo": "ABNT NBR 15575-4", "assunto": "Vedações verticais internas e externas"}, {"codigo": "ABNT NBR 15575-5", "assunto": "Sistemas de coberturas"}, {"codigo": "ABNT NBR 15575-6", "assunto": "Sistemas hidrossanitários"}]}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 16280", "Gestão de reformas em edificações", "16280", "NBR 16280", "ABNT NBR 14037", "Manuais de uso, operação e manutenção", "14037", "NBR 14037", "ABNT NBR 17170", "Garantias de edificações", "17170", "NBR 17170", "ABNT NBR 15575", "Desempenho de edificações habitacionais", "ABNT NBR 15575-1", "ABNT NBR 15575-2", "ABNT NBR 15575-3", "ABNT NBR 15575-4", "ABNT NBR 15575-5", "ABNT NBR 15575-6", "Requisitos gerais", "Sistemas estruturais", "Sistemas de pisos", "Vedações verticais internas e externas", "Sistemas de coberturas", "Sistemas hidrossanitários", "15575", "NBR 15575"]},
  {"numero": "17", "nome": "Adequações de redes e ativos", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "Unidades não são comparáveis e a carteira não distingue prioridade técnica de preferência ou informação incompleta.", "para_quem": {"decisor": "Diretor de operação/patrimônio com várias unidades e necessidade de priorizar adequações.", "prestadora": "Prestadora que deve apresentar diagnóstico/plano e comprovação do recorte ao cliente de uma rede."}, "beneficios": ["Governança da carteira", "Padronização útil", "Priorização explicável"], "resultado_pratico": "Definir uso e sistemas, avaliar condição local por protocolo, priorizar, dimensionar ações e conferir comprovação no alcance.", "entregas": "Protocolo; diagnóstico por unidade; matriz de prioridades; plano e estimativas incluídas; pendências e verificação por etapa.", "limites": "Não presume alvará, licença, projeto/obra incluídos ou adequação integral de toda a rede.", "referencia": "ABNT NBR 9050 — Acessibilidade: Conferir condições de acessibilidade do recorte da unidade.; ABNT NBR 9077 — Projeto de saídas de emergência: Examinar requisitos pertinentes das saídas de emergência.; Normas Técnicas do CBMES — Segurança contra incêndio e pânico no Espírito Santo: Relacionar a unidade às NTs de incêndio pertinentes no Espírito Santo.; ABNT NBR 16280 — Gestão de reformas em edificações: Organizar a gestão documental das reformas decorrentes da adequação.", "cta": "Informe as unidades, os sistemas e a exigência a tratar.", "anchor": "servico-17", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": null, "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Diagnosticar unidades de uma rede e priorizar adequações por sistema e local.", "criterios_principais": "Tipologias, unidades, uso, município e disciplinas efetivamente incluídas.", "referencias": [{"id": "N9050", "codigo": "ABNT NBR 9050", "nome": "Acessibilidade", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "modulo_de_acessibilidade", "aplicacao": "Conferir condições de acessibilidade do recorte da unidade.", "condicao": "Amostra de pontos não comprova acessibilidade integral; projeto é atividade própria.", "entrega_vinculada": "Diagnóstico localizado e plano de adequação no alcance.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N9077", "codigo": "ABNT NBR 9077", "nome": "Projeto de saídas de emergência", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "modulo_de_saidas", "aplicacao": "Examinar requisitos pertinentes das saídas de emergência.", "condicao": "Projeto, verificação e licenciamento têm responsabilidades próprias.", "entrega_vinculada": "Quadro de condições, referências e providências.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "R_CBMES", "codigo": "Normas Técnicas do CBMES", "nome": "Segurança contra incêndio e pânico no Espírito Santo", "tipo": "referencia_tecnica_ou_regulamentar", "papel_no_servico": "regulamentacao_local", "aplicacao": "Relacionar a unidade às NTs de incêndio pertinentes no Espírito Santo.", "condicao": "Selecionar NT/parte por uso/local; obtenção de licença não é automática.", "entrega_vinculada": "Matriz de requisitos locais e diligências por unidade.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N16280", "codigo": "ABNT NBR 16280", "nome": "Gestão de reformas em edificações", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "modulo_de_intervencao", "aplicacao": "Organizar a gestão documental das reformas decorrentes da adequação.", "condicao": "Somente se a gestão da intervenção integrar o escopo.", "entrega_vinculada": "Documentação da intervenção por unidade.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 9050", "Acessibilidade", "9050", "NBR 9050", "ABNT NBR 9077", "Projeto de saídas de emergência", "9077", "NBR 9077", "Normas Técnicas do CBMES", "Segurança contra incêndio e pânico no Espírito Santo", "ABNT NBR 16280", "Gestão de reformas em edificações", "16280", "NBR 16280"]},
  {"numero": "21", "nome": "Visualização e comunicação técnica", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "O conteúdo técnico não está claro para o destinatário e a apresentação não evidencia adequadamente a solução real.", "para_quem": {"decisor": "Gestor que precisa compreender ou apresentar um projeto, processo ou alternativa.", "prestadora": "Dono de prestadora que precisa explicar ao cliente sua proposta, escopo, etapas e solução."}, "beneficios": ["Compreensão da solução", "Apresentação técnica profissional", "Capacidade real melhor demonstrada"], "resultado_pratico": "Organizar as fontes e a mensagem, preparar roteiro/quadros, validar o conteúdo técnico, produzir e revisar os formatos contratados.", "entregas": "Roteiro e quadros de validação; imagens, vídeo ou apresentação; formatos e revisões incluídos na proposta.", "limites": "Não substitui projeto executivo, cálculo ou simulação validada; arquivos nativos/BIM só se efetivamente produzidos e contratados.", "referencia": "ABNT NBR 6492 — Documentação e representação de projetos arquitetônicos e urbanísticos: Referenciar peças de arquitetura/urbanismo efetivamente representadas.; ABNT NBR 16636 (série) — Serviços técnicos de projetos arquitetônicos e urbanísticos: Relacionar a representação às etapas/documentos do projeto de origem.", "cta": "Apresente o conteúdo técnico e o objetivo da apresentação.", "anchor": "servico-21", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": null, "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Explicar solução, escopo e etapas com representação técnica coerente.", "criterios_principais": "Projeto e revisão de origem, finalidade, fidelidade, direitos de uso e formatos.", "referencias": [{"id": "N6492", "codigo": "ABNT NBR 6492", "nome": "Documentação e representação de projetos arquitetônicos e urbanísticos", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "representacao_documental", "aplicacao": "Referenciar peças de arquitetura/urbanismo efetivamente representadas.", "condicao": "Vídeo ilustrativo ou apresentação comercial não se torna projeto executivo.", "entrega_vinculada": "Quadros/representações revisados conforme finalidade.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N16636", "codigo": "ABNT NBR 16636 (série)", "nome": "Serviços técnicos de projetos arquitetônicos e urbanísticos", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "complementar_condicional", "aplicacao": "Relacionar a representação às etapas/documentos do projeto de origem.", "condicao": "Não presume elaboração de projeto ou modelagem completa.", "entrega_vinculada": "Registro de fontes, revisões e validação do conteúdo.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 6492", "Documentação e representação de projetos arquitetônicos e urbanísticos", "6492", "NBR 6492", "ABNT NBR 16636 (série)", "Serviços técnicos de projetos arquitetônicos e urbanísticos", "16636", "NBR 16636"]}
];
const ENTRADAS = [
  {"numero": "18", "nome": "Raio-X de Propostas e Orçamentos", "grupo": null, "tipo": "entrada", "dor": "O decisor não distingue diferença de escopo de diferença de preço e não sabe o que esclarecer.", "para_quem": {"decisor": "Decisor que recebeu proposta e precisa de base para negociar/contratar.", "prestadora": "Prestadora ou assessora que analisa propostas recebidas pelo seu cliente; a apresentação visual da própria proposta comercial corresponde à oferta 21."}, "beneficios": ["Clareza para negociar", "Preparo do decisor", "Registro dos esclarecimentos"], "resultado_pratico": "Fixar cobertura e referência, parear itens, analisar prioridades, tratar omissões e devolver roteiro de negociação.", "entregas": "Questões priorizadas; quadro de diferenças/omissões; referências e limites; roteiro para negociação.", "limites": "Não presume auditoria integral, preço justo, detecção de fraude ou negociação em nome do cliente.", "referencia": "SINAPI — CAIXA — Referências técnicas e custos da construção: Confrontar itens selecionados com composições/referências contextualizadas.; SICRO — DNIT — Custos referenciais de infraestrutura de transportes: Confrontar serviços pertinentes de infraestrutura de transportes.; ABNT NBR 12721 — Custos de construção para incorporação e condomínios: Contextualizar CUB/quadros de incorporação presentes na proposta.", "cta": "Envie a proposta e a data da decisão de contratação.", "anchor": "produto-1", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Conferir pontos relevantes de orçamento/proposta para preparar a negociação.", "criterios_principais": "Escopo, quantidades, condições comerciais e seleção de itens contratada.", "referencias": [{"id": "R_SINAPI", "codigo": "SINAPI — CAIXA", "nome": "Referências técnicas e custos da construção", "tipo": "referencia_tecnica_ou_regulamentar", "papel_no_servico": "referencia_de_custo", "aplicacao": "Confrontar itens selecionados com composições/referências contextualizadas.", "condicao": "Referência não é preço justo universal nem economia realizada.", "entrega_vinculada": "Mapa de diferenças/omissões e questões para negociação.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "R_SICRO", "codigo": "SICRO — DNIT", "nome": "Custos referenciais de infraestrutura de transportes", "tipo": "referencia_tecnica_ou_regulamentar", "papel_no_servico": "referencia_de_custo", "aplicacao": "Confrontar serviços pertinentes de infraestrutura de transportes.", "condicao": "Apenas quando houver equivalência de serviço/condições.", "entrega_vinculada": "Memória dos itens selecionados.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N12721", "codigo": "ABNT NBR 12721", "nome": "Custos de construção para incorporação e condomínios", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "complementar_condicional", "aplicacao": "Contextualizar CUB/quadros de incorporação presentes na proposta.", "condicao": "Não é norma universal de auditoria nem orçamento executivo.", "entrega_vinculada": "Limites e premissas da referência de custos.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["SINAPI — CAIXA", "Referências técnicas e custos da construção", "SICRO — DNIT", "Custos referenciais de infraestrutura de transportes", "ABNT NBR 12721", "Custos de construção para incorporação e condomínios", "12721", "NBR 12721"]},
  {"numero": "19", "nome": "Diagnóstico Sentinela", "grupo": null, "tipo": "entrada", "dor": "Ações tratam o sintoma sem comprovar a causa ou resolver a interface responsável pelo impedimento.", "para_quem": {"decisor": "Dono/gestor com autoridade para mobilizar informações e decidir sobre um impedimento.", "prestadora": "Prestadora que precisa explicar ao cliente uma situação, suas evidências e caminhos de resposta."}, "beneficios": ["Compreensão do problema", "Alinhamento da equipe", "Gestão estruturada demonstrável"], "resultado_pratico": "Aplicar Observar, Confrontar, Integrar, Propor e Apoiar no alcance contratado; testar explicações e formular recomendação condicionada.", "entregas": "Diagnóstico com achados/fontes; causas fundamentadas e hipóteses; impedimentos; alternativas/prioridades e devolutiva.", "limites": "Não presume causa sempre conclusiva, prazo fixo universal, plano detalhado de recuperação, execução ou perícia integral.", "referencia": "ABNT NBR 13752 — Perícias de engenharia na construção civil: Aplicar procedimento pericial quando a finalidade contratada exigir perícia.; ABNT NBR 16747 — Inspeção predial: Incluir inspeção predial quando o diagnóstico exigir esse serviço.", "cta": "Descreva o que não está funcionando e a decisão que precisa tomar.", "anchor": "produto-2", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Organizar fatos, hipóteses e alternativas para uma decisão sobre o impasse.", "criterios_principais": "Pergunta de decisão, cronologia, contratos e evidências do caso.", "referencias": [{"id": "N13752", "codigo": "ABNT NBR 13752", "nome": "Perícias de engenharia na construção civil", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "servico_adicional", "aplicacao": "Aplicar procedimento pericial quando a finalidade contratada exigir perícia.", "condicao": "Diagnóstico consultivo não é perícia automaticamente; contratação/enquadramento próprios.", "entrega_vinculada": "Peça pericial no alcance somente quando contratada.", "partes_para_selecao": [], "partes_detalhadas": []}, {"id": "N16747", "codigo": "ABNT NBR 16747", "nome": "Inspeção predial", "tipo": "norma_ABNT_ou_serie", "papel_no_servico": "modulo_de_inspecao", "aplicacao": "Incluir inspeção predial quando o diagnóstico exigir esse serviço.", "condicao": "Cobertura, método e responsabilidade precisam corresponder à atividade.", "entrega_vinculada": "Relatório de inspeção no alcance incluído.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["ABNT NBR 13752", "Perícias de engenharia na construção civil", "13752", "NBR 13752", "ABNT NBR 16747", "Inspeção predial", "16747", "NBR 16747"]},
  {"numero": "20", "nome": "Planejamento e Medição", "grupo": null, "tipo": "entrada", "dor": "Plano, suprimentos e registros do realizado não se conectam às próximas decisões.", "para_quem": {"decisor": "Dono/gestor que precisa de controle compreensível para decidir sobre próximos compromissos e medições.", "prestadora": "Prestadora que precisa planejar e demonstrar avanço, restrições e medição ao seu cliente."}, "beneficios": ["Previsibilidade", "Coordenação das frentes", "Prestação de contas recorrente"], "resultado_pratico": "Fixar base e corte, confrontar avanço/medição, integrar restrições e compras, recomendar ações e verificar efeitos incluídos.", "entregas": "Base de planejamento incluída; instrumentos por ciclo; memória de medição no alcance; restrições e ações; decisões e efeitos verificados.", "limites": "Não presume presença contínua, comando diário, disponibilidade ilimitada, garantia de prazo ou resultado financeiro.", "referencia": "SINAPI — CAIXA — Referências técnicas e custos da construção: Contextualizar itens de custo quando essa análise integrar o planejamento.", "cta": "Apresente as frentes, a rotina atual e os próximos marcos.", "anchor": "produto-3", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas_e_referencias": {"titulo": "Normas e aplicação no serviço", "objetivo": "Conectar planejamento, avanço, restrições e medição por ciclo.", "criterios_principais": "Contrato, baseline, cronograma, unidades/critério de medição e evidências de execução.", "referencias": [{"id": "R_SINAPI", "codigo": "SINAPI — CAIXA", "nome": "Referências técnicas e custos da construção", "tipo": "referencia_tecnica_ou_regulamentar", "papel_no_servico": "referencia_de_custo", "aplicacao": "Contextualizar itens de custo quando essa análise integrar o planejamento.", "condicao": "Cronograma/medição não decorrem de uma norma universal do SINAPI.", "entrega_vinculada": "Memória de referências dos itens incluídos.", "partes_para_selecao": [], "partes_detalhadas": []}], "alcance": "As referências e os requisitos aplicáveis são definidos no escopo. As entregas documentais, verificações, ensaios e projetos incluídos são identificados na proposta."}, "palavras_chave_normativas": ["SINAPI — CAIXA", "Referências técnicas e custos da construção"]}
];
const GRUPOS = [
  {"id": "antes-de-contratar", "nome": "Antes de contratar", "ns": ["01", "02", "03", "05", "10"]},
  {"id": "durante-a-execucao", "nome": "Durante a execução", "ns": ["04", "07", "09", "11"]},
  {"id": "ativos-e-estudos", "nome": "Ativos e estudos especializados", "ns": ["06", "08", "12"]},
  {"id": "requisitos-e-entrega", "nome": "Requisitos, documentação e entrega ao cliente", "ns": ["13", "14", "15", "16", "17", "21"]}
];
/* CATALOGO:FIM */
  // cards com imagem aprovada em assets/produtos-s/; todas as 18 ofertas têm imagem
  const IMAGENS = new Set(['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '21']);
  const TIPOS = { norma_ABNT_ou_serie: 'Norma ABNT', norma_ISO_internacional: 'Norma ISO', referencia_tecnica_ou_regulamentar: 'Referência técnica (não é NBR)' };
  const ehCondicional = (r) => /^modulo_/.test(r.papel_no_servico) || ['complementar_condicional', 'servico_adicional', 'atividade_delimitada', 'escopo_de_inspecao_a_enquadrar', 'regulamentacao_local', 'sistema_especifico', 'qualificacao_da_evidencia'].includes(r.papel_no_servico);
  const normasHtml = (o) => {
    const nr = o.normas_e_referencias, refs = nr.referencias;
    const chips = refs.length
      ? `<ul>${refs.map((r) => `<li class="${ehCondicional(r) ? 'cond' : ''}">${esc(r.codigo)}</li>`).join('')}</ul>`
      : `<p class="normas-sem">Critério contratual e normas do objeto, selecionadas no escopo. ${esc(nr.criterios_principais)}</p>`;
    const itens = refs.map((r) => `<li class="${ehCondicional(r) ? 'cond' : ''}"><strong>${esc(r.codigo)} — ${esc(r.nome)}</strong><span class="tag">${esc(TIPOS[r.tipo] || r.tipo)}${ehCondicional(r) ? ' · condicional ou atividade adicional' : ''}</span><p>${esc(r.aplicacao)}</p><p><b>Entrega:</b> ${esc(r.entrega_vinculada)}</p><p><b>Alcance:</b> ${esc(r.condicao)}</p>${r.partes_detalhadas.length ? `<p><b>Partes identificadas</b> (sem impor uma edição única à série): ${r.partes_detalhadas.map((x) => `${esc(x.codigo.replace(/^ABNT /, ''))} (${esc(x.assunto)})`).join('; ')}.</p>` : ''}</li>`).join('');
    return `<div class="normas"><b>Normas e referências</b>${chips}</div><details class="mais normas-det"><summary>${esc(nr.titulo)}</summary><p>${esc(nr.objetivo)}</p><p><b>Critérios principais:</b> ${esc(nr.criterios_principais)}</p>${refs.length ? `<ul class="refs">${itens}</ul>` : ''}<p class="alcance">${esc(nr.alcance)}</p></details>`;
  };
  const assuntoDe = (o) => `${o.numero} — ${o.nome}${o.estado_publico === 'Em estruturação' ? ' (em estruturação)' : ''}`;
  const cardHtml = (p, k) => {
    const grupo = GRUPOS.find((g) => g.ns.includes(p.numero));
    const img = IMAGENS.has(p.numero)
      ? `<div class="card-img"><img src="assets/produtos-s/${esc(p.numero)}.jpg" alt="" width="960" height="536" loading="lazy" decoding="async" onerror="this.style.display='none'"><span class="card-cod">${esc(p.numero)}</span>${p.estado_publico ? `<span class="card-estado">${esc(p.estado_publico)}</span>` : ''}</div>`
      : `<div class="card-img card-img--sem"><span class="card-cod">${esc(p.numero)}</span>${p.estado_publico ? `<span class="card-estado">${esc(p.estado_publico)}</span>` : ''}</div>`;
    const mais = `<details class="mais"><summary>Para quem é, benefícios e disponibilidade</summary><dl>`
      + `<dt>Se você decide</dt><dd>${esc(p.para_quem.decisor)}</dd>`
      + `<dt>Se você entrega a um cliente</dt><dd>${esc(p.para_quem.prestadora)}</dd>`
      + `<dt>Benefícios a verificar no seu caso</dt><dd><ul>${p.beneficios.map((b) => `<li>${esc(b)}</li>`).join('')}</ul></dd>`
      + `<dt>Disponibilidade</dt><dd>${esc(p.disponibilidade)}</dd></dl></details>`;
    return `<article class="card" id="${esc(p.anchor)}" style="animation-delay:${k * 60}ms">${img}<div class="card-body"><span class="card-eyebrow">${esc(grupo ? grupo.nome : '')}</span><h3>${esc(p.nome)}</h3><p class="dor">${esc(p.dor)}</p><p>${esc(p.resultado_pratico)}</p><div class="recebe"><b>Você recebe</b>${esc(p.entregas)}</div><p class="limite"><b>Fora do escopo:</b> ${esc(p.limites)}</p>${normasHtml(p)}${mais}<p class="cta-txt">${esc(p.cta)}</p><a href="#contato" data-abrir-contato data-assunto="${esc(assuntoDe(p))}">${p.estado_publico === 'Em estruturação' ? 'CONVERSAR SOBRE O INTERESSE ↗' : 'APRESENTAR MEU CENÁRIO ↗'}</a></div></article>`;
  };
  const tabs = document.querySelector('#catalog-tabs'), grid = document.querySelector('#catalog-grid');
  const mostrarGrupo = (gi) => {
    tabs.querySelectorAll('button').forEach((b, i) => { b.classList.toggle('is-on', i === gi); b.setAttribute('aria-selected', String(i === gi)); b.tabIndex = i === gi ? 0 : -1; });
    grid.setAttribute('aria-labelledby', `aba-${gi}`);
    grid.innerHTML = GRUPOS[gi].ns.map((n, k) => cardHtml(PRODUTOS.find((x) => x.numero === n), k)).join('');
  };
  tabs.innerHTML = GRUPOS.map((g, i) => `<button type="button" role="tab" id="aba-${i}" aria-controls="catalog-grid" aria-selected="false" tabindex="-1" data-g="${i}"><span>0${i + 1}</span>${esc(g.nome)}</button>`).join('');
  tabs.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => mostrarGrupo(+b.dataset.g)));
  tabs.addEventListener('keydown', (e) => {
    const atual = +document.activeElement.dataset.g;
    if (Number.isNaN(atual)) return;
    const alvo = { ArrowRight: (atual + 1) % GRUPOS.length, ArrowLeft: (atual + GRUPOS.length - 1) % GRUPOS.length, Home: 0, End: GRUPOS.length - 1 }[e.key];
    if (alvo === undefined) return;
    e.preventDefault(); mostrarGrupo(alvo); tabs.querySelectorAll('button')[alvo].focus();
  });
  mostrarGrupo(0);

  // frente 04: o botão leva à quarta aba
  document.querySelectorAll('[data-grupo]').forEach((b) => b.addEventListener('click', () => {
    mostrarGrupo(+b.dataset.grupo);
    tabs.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'start' });
    tabs.querySelectorAll('button')[+b.dataset.grupo].focus({ preventScroll: true });
  }));
  // links diretos (#servico-13) abrem a frente certa e levam ao card
  const irParaCard = () => {
    const m = /^#servico-(\d\d)$/.exec(location.hash);
    if (!m) return;
    const gi = GRUPOS.findIndex((g) => g.ns.includes(m[1]));
    if (gi < 0) return;
    mostrarGrupo(gi);
    const card = document.getElementById(`servico-${m[1]}`);
    if (card) card.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'center' });
  };
  addEventListener('hashchange', irParaCard);
  irParaCard();

  // as três entradas (18, 19 e 20) vêm dos mesmos dados: entregas, limites e assunto do contato
  document.querySelectorAll('[data-oferta]').forEach((sec) => {
    const o = ENTRADAS.find((x) => x.numero === sec.dataset.oferta);
    if (!o) return;
    const lim = sec.querySelector('[data-limite]'); if (lim) lim.innerHTML = `<b>Fora do escopo:</b> ${esc(o.limites)} <span>${esc(o.disponibilidade)}</span>`;
    const nb = sec.querySelector('[data-normas]'); if (nb) nb.innerHTML = normasHtml(o);
    const ent = sec.querySelector('[data-entregas]'); if (ent) ent.textContent = o.entregas;
    const cta = sec.querySelector('[data-abrir-contato]'); if (cta) cta.dataset.assunto = assuntoDe(o);
  });

  /* ───────── "Encontre o serviço pela norma": índice norma → produtos, com busca local ─────────
     Normaliza caixa, acentos, espaços, pontuação e hífens (NBR15.575, nbr 15575 e 15575 levam ao mesmo lugar). Sem backend. */
  const norm = (s) => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '');
  const todas = PRODUTOS.concat(ENTRADAS).sort((x, y) => x.numero.localeCompare(y.numero));
  const indice = new Map();
  todas.forEach((o) => o.normas_e_referencias.referencias.forEach((r) => {
    if (!indice.has(r.codigo)) indice.set(r.codigo, { codigo: r.codigo, nome: r.nome, tipo: r.tipo, partes: r.partes_detalhadas, usos: [], hay: '' });
    const e = indice.get(r.codigo);
    e.usos.push({ oferta: o, ref: r });
    e.hay += norm([r.codigo, r.nome, r.aplicacao, TIPOS[r.tipo] || '', ...r.partes_detalhadas.map((x) => `${x.codigo} ${x.assunto}`)].join(' '));
  }));
  const entradasDoIndice = [...indice.values()];
  const buscaQ = document.querySelector('#busca-q'), buscaSug = document.querySelector('#busca-sug'), buscaRes = document.querySelector('#busca-res');
  const casa = (e, q) => {
    const tokens = q.split(/\s+/).map(norm).filter(Boolean);
    return tokens.length > 0 && (tokens.every((tk) => e.hay.includes(tk)) || e.hay.includes(norm(q)));
  };
  const linkDe = (o) => `#${o.anchor}`;
  const renderBusca = () => {
    const q = buscaQ.value.trim();
    if (!q) { buscaRes.innerHTML = ''; return; }
    const achados = entradasDoIndice.filter((e) => casa(e, q));
    if (!achados.length) {
      buscaRes.innerHTML = `<p class="busca-vazio">Nenhuma norma ou referência encontrada para “${esc(q)}”. A lista abaixo mostra o que o catálogo cita; se a sua norma não está nela, descreva o seu caso.</p><a href="#contato" data-abrir-contato data-assunto="${esc('Norma procurada: ' + q)}">DESCREVER O MEU CASO ↗</a>`;
      return;
    }
    buscaRes.innerHTML = achados.map((e) => `<article class="busca-item"><h4>${esc(e.codigo)} — ${esc(e.nome)} <span class="tag">${esc(TIPOS[e.tipo] || e.tipo)}</span></h4>${e.partes.length ? `<p class="busca-partes"><b>Partes identificadas:</b> ${e.partes.map((x) => `${esc(x.codigo.replace(/^ABNT /, ''))} (${esc(x.assunto)})`).join('; ')}.</p>` : ''}<ul>${e.usos.map((u) => `<li><a class="busca-prod" href="${esc(linkDe(u.oferta))}"><b>${esc(u.oferta.numero)}</b> ${esc(u.oferta.nome)}</a>${ehCondicional(u.ref) ? ' <span class="tag">condicional</span>' : ''}<p>${esc(u.ref.aplicacao)}</p><p><b>Alcance:</b> ${esc(u.ref.condicao)}</p><a class="busca-cta" href="#contato" data-abrir-contato data-assunto="${esc(assuntoDe(u.oferta) + ' — norma: ' + e.codigo)}">CONVERSAR SOBRE ESTE SERVIÇO ↗</a></li>`).join('')}</ul></article>`).join('');
  };
  if (buscaQ) {
    const grupos = [['Normas ABNT e ISO', (e) => e.tipo !== 'referencia_tecnica_ou_regulamentar'], ['Referências técnicas (não são NBR)', (e) => e.tipo === 'referencia_tecnica_ou_regulamentar']];
    buscaSug.innerHTML = grupos.map(([titulo, f]) => `<div class="busca-grupo"><b>${titulo}</b><ul>${entradasDoIndice.filter(f).map((e) => `<li><button type="button" data-q="${esc(e.codigo)}">${esc(e.codigo.replace(/^ABNT (NBR )?/, '').replace(/ — .*/, ''))}</button></li>`).join('')}</ul></div>`).join('');
    buscaQ.addEventListener('input', renderBusca);
    buscaSug.addEventListener('click', (ev) => {
      const b = ev.target.closest('button[data-q]'); if (!b) return;
      buscaQ.value = b.dataset.q; renderBusca(); buscaRes.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'nearest' });
    });
  }

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
