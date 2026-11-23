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
  /* CATALOGO:INICIO — gerado por scripts/gerar_catalogo.py a partir de catalogo-publico.json (revisão R02). Não editar à mão. */
const PRODUTOS = [
  {"numero": "01", "nome": "Viabilidade e implantação do terreno", "grupo": "antes-de-contratar", "tipo": "catalogo", "dor": "Alternativas parecem comparáveis, mas usam programas, quantidades ou restrições diferentes.", "para_quem": {"decisor": "Proprietário ou diretor de incorporação com alternativas de implantação ainda abertas.", "prestadora": "Dono de projetista ou prestadora que precisa apresentar ao cliente uma comparação tecnicamente fundamentada."}, "beneficios": ["Clareza para decidir", "Organização de premissas", "Demonstração de planejamento técnico"], "resultado_pratico": "Fixar o programa, explicitar restrições, comparar alternativas na mesma base e testar as premissas que poderiam inverter a recomendação.", "entregas": "Quadro de alternativas; premissas e fontes; consequências técnicas e estimativas no nível contratado; recomendação e diligências.", "limites": "Projeto executivo, aprovação urbanística, topografia, geotecnia e viabilidade integral não são presumidos.", "referencia": "Levantamento e implantação, projetos e regras urbanísticas pertinentes ao terreno e ao estudo.", "cta": "Apresente o terreno, as alternativas e a decisão necessária.", "anchor": "servico-01", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 13133", "NBR 14645", "NBR 12721", "NBR 14653", "SINAPI", "SICRO"]},
  {"numero": "02", "nome": "Diagnóstico ambiental e cartográfico", "grupo": "antes-de-contratar", "tipo": "catalogo", "dor": "Mapas e documentos dispersos não permitem distinguir condição conhecida de hipótese ou falta de levantamento.", "para_quem": {"decisor": "Comprador de terreno ou gestor que precisa orientar diligências antes de decidir.", "prestadora": "Projetista ou prestadora que deve reunir condicionantes para a proposta ou estudo de seu cliente."}, "beneficios": ["Organização da informação do terreno", "Visibilidade de incertezas", "Diligência técnica demonstrável"], "resultado_pratico": "Inventariar camadas e documentos, conferir escala/data/origem, localizar alertas e encaminhar os estudos que exigem confirmação física.", "entregas": "Inventário de fontes; quadro/mapa de condicionantes; incertezas; diligências e estudos necessários.", "limites": "Não presume licenciamento, laudo ambiental integral, estudo de inundação, sondagem ou regularidade integral do imóvel.", "referencia": "Referências de cartografia, levantamento, hidrologia e investigação ambiental conforme o recorte contratado.", "cta": "Informe a localização, o uso pretendido e a dúvida sobre o terreno.", "anchor": "servico-02", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 13133", "NBR 14645", "NBR 15515"]},
  {"numero": "03", "nome": "Conferência do modelo 3D da obra", "grupo": "antes-de-contratar", "tipo": "catalogo", "dor": "Ocorrências do modelo não chegam a uma resposta validada dos projetistas e a uma decisão registrável.", "para_quem": {"decisor": "Gestor de engenharia com interfaces que precisam de resposta antes da compra ou execução.", "prestadora": "Projetista ou instaladora que deve explicar compatibilidade e pendências ao contratante."}, "beneficios": ["Coordenação entre disciplinas", "Rastreabilidade das revisões", "Controle técnico demonstrável"], "resultado_pratico": "Congelar versões, validar ocorrências, localizar consequência, diligenciar o autor e verificar a resposta na rodada incluída.", "entregas": "Matriz de ocorrências validadas; localizações e imagens; questões aos autores; registro das respostas e situação do recorte.", "limites": "Não presume modelagem nova, projeto executivo, revisão integral de cálculo ou solução assinada em nome do projetista.", "referencia": "Referências de projeto e gestão da informação, além das normas dos sistemas examinados.", "cta": "Envie as disciplinas, as versões e a interface que precisa de resposta.", "anchor": "servico-03", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 16636", "NBR 6492", "ISO 19650"]},
  {"numero": "04", "nome": "Fiscalização 360°", "grupo": "durante-a-execucao", "tipo": "catalogo", "dor": "As partes não conseguem relacionar o cobrado a critério contratual, quantidade e evidência suficiente.", "para_quem": {"decisor": "Gestor autorizado a decidir sobre medição/pagamento.", "prestadora": "Dono de prestadora que precisa estruturar e sustentar sua medição ao cliente."}, "beneficios": ["Transparência", "Prestação de contas", "Qualidade da primeira submissão"], "resultado_pratico": "Fixar critérios e corte, reconciliar itens/registros, conferir quantidades e diligenciar as exceções antes da recomendação.", "entregas": "Memória do ciclo; matriz item/evidência/diferença; diligências; recomendação técnica e pendências.", "limites": "Não presume fiscalização permanente, controle tecnológico, decisão de pagamento ou imagem capaz de medir sozinha.", "referencia": "Critérios contratuais de medição e normas técnicas dos serviços verificados.", "cta": "Apresente o contrato, o boletim e a data de corte.", "anchor": "servico-04", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["Critérios contratuais de medição", "Normas específicas dos sistemas examinados"]},
  {"numero": "05", "nome": "Equalização de propostas e pleitos", "grupo": "antes-de-contratar", "tipo": "catalogo", "dor": "Bases incomparáveis na contratação ou cronologia e suporte insuficientes para discutir o evento contratual.", "para_quem": {"decisor": "Decisor que compara propostas ou deve responder a uma solicitação de alteração.", "prestadora": "Prestadora que precisa organizar uma comparação ou fundamentar tecnicamente um pedido ao seu cliente."}, "beneficios": ["Negociação mais clara", "Preparo técnico-contratual demonstrável", "Organização das evidências"], "resultado_pratico": "Contratação: equalizar escopo/unidades/bases. Pleitos: reconstruir evento/período, evidências, causas concorrentes e impacto, com encaminhamento jurídico próprio.", "entregas": "Aplicação contratação: mapa de equalização e questões. Aplicação pleito: cronologia, matriz de suporte, memória de impacto e questões para negociação.", "limites": "Não presume orçamento do zero, defesa jurídica, perícia integral ou procedência do pedido.", "referencia": "Referências de custo e especificação dos serviços; método pericial apenas quando essa atividade estiver contratada.", "cta": "Informe se a questão é uma contratação ou um pleito e apresente a base disponível.", "anchor": "servico-05", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 12721", "NBR 13752", "SINAPI", "SICRO"]},
  {"numero": "06", "nome": "Inspeção estrutural", "grupo": "ativos-e-estudos", "tipo": "catalogo", "dor": "Falta registro localizável do observado, da cobertura e das perguntas que exigem investigação.", "para_quem": {"decisor": "Proprietário ou gestor com manifestação aparente e necessidade de encaminhamento.", "prestadora": "Prestadora que deve registrar condições observadas e apresentar providências ao contratante."}, "beneficios": ["Condição registrada", "Comunicação ao gestor", "Continuidade da investigação"], "resultado_pratico": "Definir finalidade/cobertura, observar e identificar ocorrências, registrar limitações e propor investigação/prioridade pertinente.", "entregas": "Registro da cobertura e das condições; manifestações localizadas; limitações; encaminhamentos e plano de investigação no alcance.", "limites": "Não presume declaração de estabilidade, diagnóstico estrutural integral, ensaio, cálculo ou projeto de recuperação.", "referencia": "Referências de inspeção, manutenção e sistemas, conforme finalidade e abrangência contratadas.", "cta": "Informe o ativo, a ocorrência e a finalidade da inspeção.", "anchor": "servico-06", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 16747", "NBR 14037", "NBR 5674"]},
  {"numero": "07", "nome": "Custo para concluir a obra", "grupo": "durante-a-execucao", "tipo": "catalogo", "dor": "Custo incorrido, desembolso, compromissos e serviços restantes são misturados, impedindo uma visão explicável da conclusão.", "para_quem": {"decisor": "Proprietário, financiador ou diretor que precisa decidir novo aporte ou prioridade de conclusão.", "prestadora": "Dono de prestadora que precisa explicar saldo, recursos e condições para concluir seu contrato."}, "beneficios": ["Previsibilidade de conclusão", "Alinhamento entre interessados", "Domínio das premissas demonstrável"], "resultado_pratico": "Fixar corte, reconciliar avanço/custos/compromissos, estimar remanescentes por pacote e explicitar cenários e decisões.", "entregas": "Mapa do saldo e sua base; cenários; premissas e riscos; decisões e marcos; atualização no ciclo contratado.", "limites": "Não presume rating, autorização de crédito, auditoria financeira ou garantia de preço final.", "referencia": "Metodologia de custos, critérios de avanço e referências dos serviços remanescentes.", "cta": "Apresente o saldo de serviços, os compromissos e a próxima decisão de aporte.", "anchor": "servico-07", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 12721", "NBR 14653", "SINAPI", "SICRO"]},
  {"numero": "08", "nome": "Triagem técnica para compra de ativos", "grupo": "ativos-e-estudos", "tipo": "catalogo", "dor": "Informação incompleta impede separar alertas aparentes, investimento preliminar e investigações necessárias.", "para_quem": {"decisor": "Comprador ou investidor com negociação aberta e dúvida técnica delimitada.", "prestadora": "Assessora/gerenciadora que precisa entregar ao comprador um recorte técnico da diligência."}, "beneficios": ["Diligência organizada", "Clareza sobre incertezas", "Fundamentação da recomendação"], "resultado_pratico": "Fixar uso pretendido e cobertura, examinar documentos/acesso, localizar alertas e encaminhar aprofundamento.", "entregas": "Matriz de alertas; fontes/cobertura; investimento preliminar quando incluído; diligências e condições a verificar.", "limites": "Não presume avaliação integral, diligência jurídica/ambiental completa ou ausência de vícios.", "referencia": "Referências de inspeção, avaliação e sistemas apenas nas atividades efetivamente incluídas na triagem.", "cta": "Informe o ativo, o uso pretendido e o prazo da aquisição.", "anchor": "servico-08", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 14653", "NBR 16747", "NBR 15515"]},
  {"numero": "09", "nome": "Conferência de notas fiscais e medição", "grupo": "durante-a-execucao", "tipo": "catalogo", "dor": "Cadastros, unidades e movimentos não conciliados tornam diferenças inexplicáveis.", "para_quem": {"decisor": "Gestor/dono que precisa compreender diferenças de materiais e apropriação.", "prestadora": "Prestadora que deve prestar contas das compras, incorporações e medições ao cliente."}, "beneficios": ["Organização entre suprimentos e obra", "Prestação de contas", "Controle de materiais demonstrável"], "resultado_pratico": "Fixar corte/saldo inicial, mapear itens/unidades, incorporar movimentos e diligenciar as exceções com fonte.", "entregas": "Mapa de conciliação; critérios de associação/conversão; exceções e justificativas; pendências e recomendações.", "limites": "Não presume validação fiscal, prova de fraude, inventário físico ou integração de sistemas.", "referencia": "Critérios de conciliação, unidades e movimentos de materiais, com referências técnicas pertinentes à pergunta examinada.", "cta": "Apresente o período, os materiais e a divergência a esclarecer.", "anchor": "servico-09", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["Critérios de conciliação e medição", "Normas específicas dos materiais"]},
  {"numero": "10", "nome": "Análise técnica de licitações", "grupo": "antes-de-contratar", "tipo": "catalogo", "dor": "Obrigações, quantitativos ou condições técnicas não estão claros para preço, capacidade e execução.", "para_quem": {"decisor": "Dono de prestadora que decide participar, pedir esclarecimento ou formar preço.", "prestadora": "Consultora que deve entregar uma análise técnica do edital ao seu cliente."}, "beneficios": ["Preparo para participar", "Alinhamento comercial-execução", "Capacidade de explicar a proposta"], "resultado_pratico": "Confrontar anexos, referências e orçamento, formular a questão, estimar consequência no nível possível e encaminhar aspectos jurídicos.", "entregas": "Nota técnica com fonte, questão, consequência e premissas; matriz para esclarecimento e validação jurídica.", "limites": "Não presume advocacia, protocolo, habilitação, acervo ou vitória.", "referencia": "Edital, projetos, metodologia de custos e normas técnicas do objeto; questões jurídicas têm encaminhamento próprio.", "cta": "Apresente o edital, sua dúvida técnica e o prazo disponível.", "anchor": "servico-10", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 12721", "SINAPI", "SICRO"]},
  {"numero": "11", "nome": "Gêmeo digital leve", "grupo": "durante-a-execucao", "tipo": "catalogo", "dor": "Fotos avulsas e equipes diferentes não permitem uma comparação confiável entre campanhas.", "para_quem": {"decisor": "Gestor de ativo com necessidade de observar evolução e decidir aprofundamento.", "prestadora": "Prestadora que deve manter um histórico técnico comparável para o contratante."}, "beneficios": ["Continuidade de informação", "Comunicação objetiva", "Rotina de acompanhamento demonstrável"], "resultado_pratico": "Definir pergunta, protocolo e condição inicial; coletar campanhas; verificar comparabilidade/incerteza e encaminhar o que exige investigação.", "entregas": "Protocolo; séries revisadas; comparabilidade e limitações; alertas e encaminhamentos.", "limites": "Não presume monitoramento contínuo, vigilância estrutural, estabilidade ou diagnóstico da causa.", "referencia": "Protocolo de acompanhamento e referências do sistema, da inspeção e da manutenção pertinentes.", "cta": "Informe o que precisa ser acompanhado e qual decisão depende da evolução.", "anchor": "servico-11", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 16747", "NBR 14037", "NBR 5674"]},
  {"numero": "12", "nome": "Carbono incorporado e custo", "grupo": "ativos-e-estudos", "tipo": "catalogo", "dor": "Custo e carbono são comparados com funções, fronteiras ou dados incompatíveis.", "para_quem": {"decisor": "Gestor de projeto/compras com alternativa material ou requisito ambiental definido.", "prestadora": "Fornecedor ou prestadora que precisa demonstrar ao cliente a base da alternativa proposta."}, "beneficios": ["Transparência ambiental", "Capacidade analítica demonstrável", "Resposta a exigências de clientes"], "resultado_pratico": "Definir função, fronteira e método; qualificar dados; calcular alternativas; testar sensibilidade e explicar limites.", "entregas": "Memória de cálculo; dados/fontes/qualidade; comparação e sensibilidade; condições de uso da conclusão.", "limites": "Não presume neutralidade, crédito de carbono, certificação, EPD ou ACV completa.", "referencia": "Referências de ciclo de vida, como ISO 14040/14044 e adoções aplicáveis, conforme o método e o alcance definidos.", "cta": "Apresente as alternativas, a função e a exigência ambiental.", "anchor": "servico-12", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["ISO 14040", "ISO 14044", "NBR 12721", "SINAPI", "SICRO"]},
  {"numero": "13", "nome": "Desempenho e requisitos", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "Requisito, configuração comprada, evidência de produto e condição instalada não estão relacionados de forma suficiente.", "para_quem": {"decisor": "Dono/gestor com requisito de sistema que precisa avaliar compra, substituição ou comprovação.", "prestadora": "Prestadora/fornecedora que deve reunir e demonstrar ao cliente as evidências do seu escopo."}, "beneficios": ["Atendimento aos requisitos demonstrável", "Coordenação de fornecedores", "Organização da comprovação"], "resultado_pratico": "Verificar aplicabilidade, identificar requisitos/métodos, vincular evidência à configuração, tratar lacunas e emitir conclusão humana delimitada.", "entregas": "Ficha de aplicabilidade; matriz por requisito/configuração; diligências; conclusões e pendências; pasta de comprovação do recorte.", "limites": "Não presume certificação integral, ensaios/simulações incluídos ou conclusão sobre edificação inteira.", "referencia": "Partes e métodos pertinentes da NBR 15575, quando aplicável, e normas específicas dos sistemas. A edição, a configuração e o alcance são definidos para o caso.", "cta": "Apresente o sistema, a exigência e o marco de compra ou entrega.", "anchor": "servico-13", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": "Sob demanda", "normas": ["NBR 15575", "NBR 10151", "NBR 10152", "NBR ISO/IEC 17025"]},
  {"numero": "14", "nome": "Organização da entrega documental", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "Arquivos, versões e faltantes impedem uma entrega utilizável e deixam o controle da prestadora pouco visível.", "para_quem": {"decisor": "Contratante que precisa conferir o pacote recebido e conduzir pendências.", "prestadora": "Dono de prestadora/instaladora que precisa entregar documentação organizada ao cliente final."}, "beneficios": ["Organização utilizável", "Capacidade técnica efetivamente exercida demonstrada", "Continuidade para o cliente"], "resultado_pratico": "Fixar lista e profundidade, inventariar, organizar, atribuir faltantes, conduzir diligências, conferir, produzir índice e submeter o pacote.", "entregas": "Índice mestre e estrutura; matriz de completude; arquivos organizados; instrumentos próprios contratados; diligências, pendências e protocolo.", "limites": "Não presume emissão por terceiros, validação integral de disciplinas, aceite garantido, comando da obra ou entrega que a contratante não executou.", "referencia": "Lista de entrega do contrato e normas das disciplinas. A NBR 14037 entra quando o escopo inclui manual de uso, operação e manutenção.", "cta": "Apresente a lista de entrega, uma amostra do acervo e o prazo.", "anchor": "servico-14", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": "Em estruturação", "normas": ["NBR 14037", "NBR 5674", "NBR 15575", "ISO 19650"]},
  {"numero": "15", "nome": "Manutenção e registros de garantias", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "Atividades, responsáveis e registros não permitem continuidade ou explicação adequada das providências.", "para_quem": {"decisor": "Gestor/proprietário que precisa estruturar plano e histórico ou encaminhar ocorrência.", "prestadora": "Prestadora que deve entregar registros e orientação de manutenção ao cliente."}, "beneficios": ["Rotina organizada", "Continuidade e autonomia", "Cuidado com o ativo demonstrável"], "resultado_pratico": "Identificar ativo/sistemas e referências, estruturar plano/evidência, conferir histórico e acompanhar ações no ciclo contratado.", "entregas": "Plano/estrutura de registros no alcance; matriz de responsabilidades; histórico organizado; pendências e encaminhamentos.", "limites": "Não presume execução diária da manutenção, reparos, parecer jurídico ou garantia preservada automaticamente.", "referencia": "NBR 5674, NBR 14037 e referências de garantias como a NBR 17170, conforme o objeto e a aplicação.", "cta": "Apresente o ativo, os registros existentes e a necessidade de operação.", "anchor": "servico-15", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": "Em estruturação", "normas": ["NBR 5674", "NBR 14037", "NBR 17170", "NBR 16747"]},
  {"numero": "16", "nome": "Documentação e interfaces de reformas", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "Escopo, interfaces, responsabilidades e documentação não estão organizados nos marcos necessários.", "para_quem": {"decisor": "Proprietário/gestor que precisa compreender documentos e responsabilidades para a intervenção.", "prestadora": "Prestadora de reforma que deve apresentar ao cliente/gestão do imóvel o plano e os registros pertinentes."}, "beneficios": ["Planejamento demonstrável", "Comunicação entre partes", "Controle das alterações"], "resultado_pratico": "Enquadrar intervenção, selecionar requisitos, confrontar plano e registros, diligenciar responsáveis e preparar a entrega do recorte.", "entregas": "Matriz de requisitos/documentos; interfaces; diligências; responsabilidades; alterações e pacote de entrega no alcance.", "limites": "Não presume projeto integral, autorização formal, execução, aprovação do condomínio/órgão ou ausência de risco.", "referencia": "NBR 16280 quando aplicável, normas dos sistemas e regras pertinentes ao imóvel e à intervenção.", "cta": "Descreva a intervenção, os sistemas e o marco previsto.", "anchor": "servico-16", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": "Em estruturação", "normas": ["NBR 16280", "NBR 15575"]},
  {"numero": "17", "nome": "Adequações de redes e ativos", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "Unidades não são comparáveis e a carteira não distingue prioridade técnica de preferência ou informação incompleta.", "para_quem": {"decisor": "Diretor de operação/patrimônio com várias unidades e necessidade de priorizar adequações.", "prestadora": "Prestadora que deve apresentar diagnóstico/plano e comprovação do recorte ao cliente de uma rede."}, "beneficios": ["Governança da carteira", "Padronização útil", "Priorização explicável"], "resultado_pratico": "Definir uso e sistemas, avaliar condição local por protocolo, priorizar, dimensionar ações e conferir comprovação no alcance.", "entregas": "Protocolo; diagnóstico por unidade; matriz de prioridades; plano e estimativas incluídas; pendências e verificação por etapa.", "limites": "Não presume alvará, licença, projeto/obra incluídos ou adequação integral de toda a rede.", "referencia": "Referências dos sistemas avaliados, como acessibilidade e saídas de emergência, e regulamentação competente de cada local.", "cta": "Informe as unidades, os sistemas e a exigência a tratar.", "anchor": "servico-17", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": "Em estruturação", "normas": ["NBR 9050", "NBR 9077", "NBR 16747"]},
  {"numero": "21", "nome": "Visualização e comunicação técnica", "grupo": "requisitos-e-entrega", "tipo": "catalogo", "dor": "O conteúdo técnico não está claro para o destinatário e a apresentação não evidencia adequadamente a solução real.", "para_quem": {"decisor": "Gestor que precisa compreender ou apresentar um projeto, processo ou alternativa.", "prestadora": "Dono de prestadora que precisa explicar ao cliente sua proposta, escopo, etapas e solução."}, "beneficios": ["Compreensão da solução", "Apresentação técnica profissional", "Capacidade real melhor demonstrada"], "resultado_pratico": "Organizar as fontes e a mensagem, preparar roteiro/quadros, validar o conteúdo técnico, produzir e revisar os formatos contratados.", "entregas": "Roteiro e quadros de validação; imagens, vídeo ou apresentação; formatos e revisões incluídos na proposta.", "limites": "Não substitui projeto executivo, cálculo ou simulação validada; arquivos nativos/BIM só se efetivamente produzidos e contratados.", "referencia": "Projeto, especificações e normas dos sistemas representados, com fidelidade e finalidade definidas para a comunicação.", "cta": "Apresente o conteúdo técnico e o objetivo da apresentação.", "anchor": "servico-21", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "estado_publico": "Em estruturação", "normas": ["NBR 16636", "NBR 6492"]}
];
const ENTRADAS = [
  {"numero": "18", "nome": "Raio-X de Propostas e Orçamentos", "grupo": null, "tipo": "entrada", "dor": "O decisor não distingue diferença de escopo de diferença de preço e não sabe o que esclarecer.", "para_quem": {"decisor": "Decisor que recebeu proposta e precisa de base para negociar/contratar.", "prestadora": "Prestadora ou assessora que analisa propostas recebidas pelo seu cliente; a apresentação visual da própria proposta comercial corresponde à oferta 21."}, "beneficios": ["Clareza para negociar", "Preparo do decisor", "Registro dos esclarecimentos"], "resultado_pratico": "Fixar cobertura e referência, parear itens, analisar prioridades, tratar omissões e devolver roteiro de negociação.", "entregas": "Questões priorizadas; quadro de diferenças/omissões; referências e limites; roteiro para negociação.", "limites": "Não presume auditoria integral, preço justo, detecção de fraude ou negociação em nome do cliente.", "referencia": "Projeto, especificações, referências de custo pertinentes e normas dos serviços comparados.", "cta": "Envie a proposta e a data da decisão de contratação.", "anchor": "produto-1", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 12721", "SINAPI", "SICRO"]},
  {"numero": "19", "nome": "Diagnóstico Sentinela", "grupo": null, "tipo": "entrada", "dor": "Ações tratam o sintoma sem comprovar a causa ou resolver a interface responsável pelo impedimento.", "para_quem": {"decisor": "Dono/gestor com autoridade para mobilizar informações e decidir sobre um impedimento.", "prestadora": "Prestadora que precisa explicar ao cliente uma situação, suas evidências e caminhos de resposta."}, "beneficios": ["Compreensão do problema", "Alinhamento da equipe", "Gestão estruturada demonstrável"], "resultado_pratico": "Aplicar Observar, Confrontar, Integrar, Propor e Apoiar no alcance contratado; testar explicações e formular recomendação condicionada.", "entregas": "Diagnóstico com achados/fontes; causas fundamentadas e hipóteses; impedimentos; alternativas/prioridades e devolutiva.", "limites": "Não presume causa sempre conclusiva, prazo fixo universal, plano detalhado de recuperação, execução ou perícia integral.", "referencia": "Referências técnicas e contratuais do objeto investigado; atividades especializadas têm método e responsabilidade próprios.", "cta": "Descreva o que não está funcionando e a decisão que precisa tomar.", "anchor": "produto-2", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 13752", "NBR 12721", "SINAPI", "SICRO"]},
  {"numero": "20", "nome": "Planejamento e Medição", "grupo": null, "tipo": "entrada", "dor": "Plano, suprimentos e registros do realizado não se conectam às próximas decisões.", "para_quem": {"decisor": "Dono/gestor que precisa de controle compreensível para decidir sobre próximos compromissos e medições.", "prestadora": "Prestadora que precisa planejar e demonstrar avanço, restrições e medição ao seu cliente."}, "beneficios": ["Previsibilidade", "Coordenação das frentes", "Prestação de contas recorrente"], "resultado_pratico": "Fixar base e corte, confrontar avanço/medição, integrar restrições e compras, recomendar ações e verificar efeitos incluídos.", "entregas": "Base de planejamento incluída; instrumentos por ciclo; memória de medição no alcance; restrições e ações; decisões e efeitos verificados.", "limites": "Não presume presença contínua, comando diário, disponibilidade ilimitada, garantia de prazo ou resultado financeiro.", "referencia": "Projetos, contrato, critérios de medição e normas dos serviços incluídos; boas práticas de gestão apoiam a organização.", "cta": "Apresente as frentes, a rotina atual e os próximos marcos.", "anchor": "produto-3", "disponibilidade": "Consulte o escopo e a disponibilidade para o seu caso.", "normas": ["NBR 12721", "SINAPI", "SICRO"]}
];
const GRUPOS = [
  {"id": "antes-de-contratar", "nome": "Antes de contratar", "ns": ["01", "02", "03", "05", "10"]},
  {"id": "durante-a-execucao", "nome": "Durante a execução", "ns": ["04", "07", "09", "11"]},
  {"id": "ativos-e-estudos", "nome": "Ativos e estudos especializados", "ns": ["06", "08", "12"]},
  {"id": "requisitos-e-entrega", "nome": "Requisitos, documentação e entrega ao cliente", "ns": ["13", "14", "15", "16", "17", "21"]}
];
/* CATALOGO:FIM */
  // cards com imagem aprovada em assets/produtos-s/; os demais usam o cabeçalho em CSS (o 13 aguarda a imagem)
  const IMAGENS = new Set(['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13']);
  const assuntoDe = (o) => `${o.numero} — ${o.nome}${o.estado_publico === 'Em estruturação' ? ' (em estruturação)' : ''}`;
  const cardHtml = (p, k) => {
    const grupo = GRUPOS.find((g) => g.ns.includes(p.numero));
    const img = IMAGENS.has(p.numero)
      ? `<div class="card-img"><img src="assets/produtos-s/${esc(p.numero)}.jpg" alt="" width="960" height="536" loading="lazy" decoding="async" onerror="this.style.display='none'"><span class="card-cod">${esc(p.numero)}</span></div>`
      : `<div class="card-img card-img--sem"><span class="card-cod">${esc(p.numero)}</span>${p.estado_publico ? `<span class="card-estado">${esc(p.estado_publico)}</span>` : ''}</div>`;
    const mais = `<details class="mais"><summary>Para quem é, benefícios e referência</summary><dl>`
      + `<dt>Se você decide</dt><dd>${esc(p.para_quem.decisor)}</dd>`
      + `<dt>Se você entrega a um cliente</dt><dd>${esc(p.para_quem.prestadora)}</dd>`
      + `<dt>Benefícios a verificar no seu caso</dt><dd><ul>${p.beneficios.map((b) => `<li>${esc(b)}</li>`).join('')}</ul></dd>`
      + `<dt>Referência do trabalho</dt><dd>${esc(p.referencia)}</dd>`
      + `<dt>Disponibilidade</dt><dd>${esc(p.disponibilidade)}</dd></dl></details>`;
    return `<article class="card" id="${esc(p.anchor)}" style="animation-delay:${k * 60}ms">${img}<div class="card-body"><span class="card-eyebrow">${esc(grupo ? grupo.nome : '')}</span><h3>${esc(p.nome)}</h3><p class="dor">${esc(p.dor)}</p><p>${esc(p.resultado_pratico)}</p><div class="recebe"><b>Você recebe</b>${esc(p.entregas)}</div><p class="limite"><b>Fora do escopo:</b> ${esc(p.limites)}</p><div class="normas"><b>Normas e referências relacionadas</b><ul>${p.normas.map((n) => `<li>${esc(n)}</li>`).join('')}</ul></div>${mais}<p class="cta-txt">${esc(p.cta)}</p><a href="#contato" data-abrir-contato data-assunto="${esc(assuntoDe(p))}">${p.estado_publico === 'Em estruturação' ? 'CONVERSAR SOBRE O INTERESSE ↗' : 'APRESENTAR MEU CENÁRIO ↗'}</a></div></article>`;
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
    const lim = sec.querySelector('[data-limite]'); if (lim) lim.innerHTML = `<b>Fora do escopo:</b> ${esc(o.limites)} <span><b>Normas e referências relacionadas:</b> ${esc(o.normas.join(' · '))}.</span> <span>${esc(o.disponibilidade)}</span>`;
    const ent = sec.querySelector('[data-entregas]'); if (ent) ent.textContent = o.entregas;
    const cta = sec.querySelector('[data-abrir-contato]'); if (cta) cta.dataset.assunto = assuntoDe(o);
  });

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
