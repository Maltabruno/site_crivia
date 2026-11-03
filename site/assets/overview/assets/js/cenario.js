/* Página "Apresentar meu cenário": uma única tela, com perguntas que aparecem conforme as respostas.
   - Todo texto vindo do usuário é inserido com textContent (nunca innerHTML).
   - Nada é enviado ao servidor antes do clique final. O rascunho fica só neste navegador (sessionStorage, mesma aba) e some após o envio confirmado.
   - Localidades: arquivos locais gerados do IBGE (data/locations), carregados por UF sob demanda; nenhuma API externa durante o preenchimento. */
(function () {
  "use strict";
  var CFG = window.CRIVIA_CENARIO_CONFIG;
  var R = window.CRIVIA_REGRAS;
  var app = document.getElementById("app");
  var STORE = "crivia_cenario_v3";
  var ORIGEM = R.lerOrigem(location.search);
  var inicio = Date.now();
  var FORM_VERSION = "form-3";

  // Perguntas de múltipla escolha guardam listas de códigos; a participação na decisão é de escolha única; a pergunta curta de cada situação marcada guarda {situação: resposta}.
  var estado = { situationCodes: [], contextAnswers: {}, audienceProfiles: [], decisionRole: "", narrative: "",
    urgencies: [], consequences: [], documents: [], estimatedRanges: [],
    location: { type: "brazil", stateCode: "", cityCode: "", cityName: "", countryCode: "", countryName: "", intlCity: "", foreignRegion: "" },
    contact: { name: "", organization: "", preferredChannel: "", phone: "", email: "", contactPeriods: [] } };
  var LISTAS_MULTI = ["situationCodes", "audienceProfiles", "urgencies", "consequences", "documents", "estimatedRanges"];
  var ui = { erros: {}, enviando: false, erroEnvio: "", resultado: null, idem: null, mostrarOutroCanal: false };
  var reg = {};        // campo -> { caixa, ctrl, msg }: onde mostrar o erro de cada campo
  var refs = {};       // elementos usados por várias funções

  // ── DOM ───────────────────────────────────────────────────────────────────────────────────────
  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === "class") el.className = v;
      else if (k === "texto") el.textContent = v;
      else if (k.slice(0, 2) === "on") el.addEventListener(k.slice(2), v);
      else if (k === "valor") el.value = v;
      else el.setAttribute(k, v === true ? "" : v);
    });
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c === null || c === undefined || c === false) continue;
      el.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }
    return el;
  }
  var anuncio = document.getElementById("anuncio");
  var tAnuncio = null;
  function anunciar(msg) { if (!anuncio) return; clearTimeout(tAnuncio); anuncio.textContent = ""; tAnuncio = setTimeout(function () { anuncio.textContent = msg; }, 60); }

  // ── analytics do funil (sem PII; desligado por padrão) ──────────────────────────────────────────
  var PARAMS_OK = ["branch", "device", "origin", "productHint", "errorType", "duration"];
  function rastrear(evento, params) {
    try {
      if (!CFG.analyticsEnabled || !window.CRIVIA_CONSENT || window.CRIVIA_CONSENT.analytics !== true) return;
      var limpo = {};
      Object.keys(params || {}).forEach(function (k) { if (PARAMS_OK.indexOf(k) >= 0) limpo[k] = params[k]; });
      window.dispatchEvent(new CustomEvent("crivia:evento", { detail: { evento: evento, params: limpo } }));
    } catch (e) { /* nunca interrompe o formulário */ }
  }
  function dispositivo() { var w = window.innerWidth; return w < 768 ? "mobile" : w < 1100 ? "tablet" : "desktop"; }

  // ── rascunho (sessionStorage; sem honeypot, sem marketing, sem ciência) ─────────────────────────────
  var tSalvar = null;
  function salvar() {
    clearTimeout(tSalvar);
    tSalvar = setTimeout(function () {
      try { sessionStorage.setItem(STORE, JSON.stringify({ v: 3, e: { situationCodes: estado.situationCodes, contextAnswers: estado.contextAnswers, audienceProfiles: estado.audienceProfiles,
        decisionRole: estado.decisionRole, narrative: estado.narrative, urgencies: estado.urgencies, consequences: estado.consequences, documents: estado.documents,
        estimatedRanges: estado.estimatedRanges, location: estado.location, contact: estado.contact } })); } catch (e) { /* armazenamento indisponível: segue sem salvar */ }
    }, 300);
  }
  function restaurar() {
    try {
      var d = JSON.parse(sessionStorage.getItem(STORE) || "null");
      if (!d || d.v !== 3 || !d.e) return;
      ["decisionRole", "narrative"].forEach(function (k) { if (typeof d.e[k] === "string") estado[k] = d.e[k]; });
      if (d.e.contextAnswers && typeof d.e.contextAnswers === "object") {
        R.SITUACOES.forEach(function (s) { var x = d.e.contextAnswers[s.v]; if (typeof x === "string" && R.achar(s.opcoes, x)) estado.contextAnswers[s.v] = x; });
      }
      LISTAS_MULTI.forEach(function (k) { if (Array.isArray(d.e[k])) estado[k] = d.e[k].filter(function (x) { return typeof x === "string"; }); });
      Object.keys(estado.location).forEach(function (k) { if (d.e.location && typeof d.e.location[k] === "string") estado.location[k] = d.e.location[k]; });
      ["name", "organization", "preferredChannel", "phone", "email"].forEach(function (k) { if (d.e.contact && typeof d.e.contact[k] === "string") estado.contact[k] = d.e.contact[k]; });
      if (d.e.contact && Array.isArray(d.e.contact.contactPeriods)) estado.contact.contactPeriods = d.e.contact.contactPeriods.filter(function (x) { return typeof x === "string"; });
    } catch (e) { /* ignora */ }
  }
  function limparRascunho() { clearTimeout(tSalvar); try { sessionStorage.removeItem(STORE); } catch (e) { /* ignora */ } }

  // ── erros por campo ───────────────────────────────────────────────────────────────────────────────
  function registrar(chave, caixa, ctrl, msg) { reg[chave] = { caixa: caixa, ctrl: ctrl, msg: msg }; }
  function marcarErro(chave, texto) {
    var r = reg[chave]; if (!r) return;
    r.msg.textContent = texto || "";
    r.caixa.classList.toggle(r.caixa.classList.contains("grupo") ? "grupo--erro" : "campo--erro", !!texto);
    if (r.ctrl) { if (texto) r.ctrl.setAttribute("aria-invalid", "true"); else r.ctrl.removeAttribute("aria-invalid"); }
    if (!texto) delete ui.erros[chave];
  }
  function limpar(chave) { if (ui.erros[chave]) marcarErro(chave, ""); }

  // ── componentes ───────────────────────────────────────────────────────────────────────────────
  var contador = 0;
  /** Organiza as opções em colunas alinhadas, sem caixa em volta: 4 colunas para rótulos curtos (até ~15 letras, cabem numa linha), 3 para médios (~22), 2 para longos
      (nunca mais colunas que opções). No celular: 2 colunas só se tudo for curto; senão 1. O número vai em variáveis CSS. */
  function colunas(cx, lista) {
    var m = 0, n = lista.length;
    lista.forEach(function (o) { m = Math.max(m, o.l.length); });
    cx.classList.add("opcoes");
    cx.style.setProperty("--cols", Math.min(n, m <= 15 ? 4 : m <= 22 ? 3 : 2));
    cx.style.setProperty("--cols-m", m <= 14 ? Math.min(n, 2) : 1);
  }

  function chips(nome, lista, aoEscolher, classe) {
    contador += 1;
    var seg = classe === "segmento";       // Brasil/Exterior e canal continuam como botões segmentados; o resto é lista de escolha única
    var cx = h("div", { class: classe || "chips" });
    lista.forEach(function (o) {
      var inp = h("input", { type: "radio", name: nome + "-" + contador, value: o.v, onchange: function () { aoEscolher(o.v); } });
      cx.appendChild(h("label", { class: seg ? "chip" : "chip chip--caixa" }, inp, seg ? null : h("span", { class: "chip__caixa chip__caixa--radio", "aria-hidden": "true" }), h("span", { texto: o.l })));
    });
    if (!seg) colunas(cx, lista);
    return cx;
  }
  function marcar(cx, valor) { Array.prototype.forEach.call(cx.querySelectorAll("input"), function (i) { i.checked = Array.isArray(valor) ? valor.indexOf(i.value) >= 0 : i.value === valor; }); }

  /** Múltipla escolha: caixas de seleção, "Marcar todas" e "Limpar". `exclusivas` são opções que não combinam com as demais
      (ex.: "Ainda não sei"): ao marcá-las as outras saem; ao marcar outra, elas saem. O resultado segue a ordem da lista. */
  function multi(nome, lista, aoMudar, o) {
    o = o || {};
    contador += 1;
    var excl = o.exclusivas || [];
    var cx = h("div", { class: "chips" });
    colunas(cx, lista);
    function entradas() { return Array.prototype.slice.call(cx.querySelectorAll("input")); }
    function lidos() { return entradas().filter(function (i) { return i.checked; }).map(function (i) { return i.value; }); }
    lista.forEach(function (op) {
      var inp = h("input", { type: "checkbox", name: nome + "-" + contador, value: op.v, onchange: function (ev) {
        if (ev.target.checked) {
          var eExcl = excl.indexOf(op.v) >= 0;
          entradas().forEach(function (i) { if (i !== ev.target && (eExcl || excl.indexOf(i.value) >= 0)) i.checked = false; });
        }
        aoMudar(lidos());
      } });
      cx.appendChild(h("label", { class: "chip chip--caixa" }, inp, h("span", { class: "chip__caixa", "aria-hidden": "true" }), h("span", { texto: op.l })));
    });
    function todas() { entradas().forEach(function (i) { i.checked = excl.indexOf(i.value) < 0; }); aoMudar(lidos()); anunciar("Todas as opções marcadas."); }
    function nenhuma() { entradas().forEach(function (i) { i.checked = false; }); aoMudar(lidos()); anunciar("Seleção limpa."); }
    return { cx: cx, todas: todas, nenhuma: nenhuma };
  }

  /** Pergunta de múltipla escolha com os botões "Marcar todas" e "Limpar" no canto da pergunta. */
  function grupoMulti(chave, rotulo, m, opcional) {
    var erId = "er-" + chave.replace(/\W/g, "-");
    var msg = h("p", { class: "campo__erro", id: erId, role: "alert" });
    var botoes = h("div", { class: "grupo__acoes" },
      h("button", { type: "button", class: "grupo__acao", "aria-label": "Marcar todas as opções de: " + rotulo, texto: "Marcar todas", onclick: m.todas }),
      h("span", { class: "grupo__sep", "aria-hidden": "true", texto: "·" }),
      h("button", { type: "button", class: "grupo__acao", "aria-label": "Limpar a seleção de: " + rotulo, texto: "Limpar", onclick: m.nenhuma }));
    // div com role="group" (e não fieldset): o botão fica ao lado do título, e o título nomeia o grupo para leitores de tela
    var lid = "lb-" + chave.replace(/\W/g, "-");
    var fs = h("div", { class: "grupo grupo--multi grupo--num", role: "group", "aria-labelledby": lid, "aria-describedby": erId },
      h("div", { class: "grupo__rotulo", id: lid }, rotulo, opcional ? h("span", { class: "grupo__opcional", texto: " (opcional)" }) : null), botoes, m.cx, msg);
    registrar(chave, fs, null, msg);
    return fs;
  }

  function grupo(chave, rotulo, conteudo, opcional) {
    var erId = "er-" + chave.replace(/\W/g, "-");
    var msg = h("p", { class: "campo__erro", id: erId, role: "alert" });
    var lid = "lb-" + chave.replace(/\W/g, "-");
    var fs = h("div", { class: "grupo grupo--num", role: "group", "aria-labelledby": lid, "aria-describedby": erId }, h("div", { class: "grupo__rotulo", id: lid }, rotulo, opcional ? h("span", { class: "grupo__opcional", texto: " (opcional)" }) : null), conteudo, msg);
    registrar(chave, fs, null, msg);
    return fs;
  }

  /** Campo de texto com rótulo real, ajuda e mensagem de erro associados. */
  function campo(chave, rotulo, o) {
    var id = "c-" + chave.replace(/\W/g, "-");
    var ajId = o.ajuda ? id + "-aj" : null, erId = id + "-er";
    var ctrl = h(o.area ? "textarea" : "input", { id: id, name: o.nome || chave, type: o.area ? null : (o.tipo || "text"), rows: o.area ? "4" : null, autocomplete: o.autocomplete || "off",
      inputmode: o.inputmode || null, spellcheck: o.tipo === "email" || o.tipo === "tel" ? "false" : null, "aria-required": o.obrigatorio ? "true" : null,
      "aria-describedby": [ajId, erId, o.area ? id + "-ct" : null].filter(Boolean).join(" "),
      oninput: function (ev) { o.aoMudar(ev.target.value); limpar(chave); salvar(); } });
    var msg = h("p", { class: "campo__erro", id: erId, role: "alert" });
    var caixa = h("div", { class: "campo" }, h("label", { for: id, class: o.numerar ? "rotulo-num" : null }, rotulo, o.obrigatorio === false ? h("span", { class: "grupo__opcional", texto: " (opcional)" }) : null),
      o.ajuda ? h("p", { class: "campo__ajuda", id: ajId, texto: o.ajuda }) : null, ctrl, o.area ? h("p", { class: "campo__contador", id: id + "-ct", texto: "0 / " + R.LIMITES.narrativa }) : null, msg);
    registrar(chave, caixa, ctrl, msg);
    return { caixa: caixa, ctrl: ctrl };
  }

  /** Seletor com busca (padrão ARIA combobox/listbox): teclado completo, sem acento e sem diferença de maiúsculas, até 60 itens por vez. */
  function combobox(chave, rotulo, o) {
    var id = "c-" + chave.replace(/\W/g, "-"), erId = id + "-er", lbId = id + "-lb";
    var itens = [], visiveis = [], ativo = -1, escolhido = null, tAnun = null;
    var ctrl = h("input", { id: id, type: "text", role: "combobox", "aria-autocomplete": "list", "aria-expanded": "false", "aria-controls": lbId, "aria-required": "true",
      "aria-describedby": erId, autocomplete: "off", autocapitalize: "off", spellcheck: "false", placeholder: o.placeholder || "" });
    var lista = h("ul", { id: lbId, class: "combo__lista", role: "listbox", "aria-label": rotulo, hidden: "hidden" });
    var msg = h("p", { class: "campo__erro", id: erId, role: "alert" });
    var caixa = h("div", { class: "campo" }, h("label", { for: id, texto: rotulo }), ctrl, lista, msg);   // Estado/Cidade/País: campos, sem número
    registrar(chave, caixa, ctrl, msg);

    function abrir() { lista.hidden = false; ctrl.setAttribute("aria-expanded", "true"); }
    function fechar() { lista.hidden = true; ctrl.setAttribute("aria-expanded", "false"); ctrl.removeAttribute("aria-activedescendant"); ativo = -1; }
    function desenhar() {
      visiveis = R.filtrar(itens, ctrl.value, 60);
      lista.textContent = "";
      if (!visiveis.length) {
        lista.appendChild(h("li", { class: "combo__vazio", role: "option", "aria-disabled": "true", "aria-selected": "false", texto: itens.length ? "Nenhum resultado" : (o.semItens || "Sem opções") }));
      }
      visiveis.forEach(function (it, i) {
        lista.appendChild(h("li", { id: id + "-op-" + i, role: "option", "aria-selected": i === ativo ? "true" : "false", texto: it[1],
          onmousedown: function (ev) { ev.preventDefault(); escolher(it); } }));
      });
      if (ativo >= 0 && visiveis[ativo]) ctrl.setAttribute("aria-activedescendant", id + "-op-" + ativo); else ctrl.removeAttribute("aria-activedescendant");
      var el = ativo >= 0 ? document.getElementById(id + "-op-" + ativo) : null;
      if (el && el.scrollIntoView) el.scrollIntoView({ block: "nearest" });
      clearTimeout(tAnun); tAnun = setTimeout(function () { anunciar(visiveis.length ? visiveis.length + (visiveis.length === 1 ? " resultado" : " resultados") : "Nenhum resultado"); }, 500);
    }
    function escolher(it) { escolhido = it; ctrl.value = it[1]; fechar(); limpar(chave); o.aoEscolher(it); }
    ctrl.addEventListener("input", function () {
      if (escolhido) { escolhido = null; o.aoEscolher(null); }
      ativo = -1; abrir(); desenhar();
    });
    ctrl.addEventListener("focus", function () { if (!ctrl.disabled) { abrir(); desenhar(); } });
    ctrl.addEventListener("click", function () { if (!ctrl.disabled && lista.hidden) { abrir(); desenhar(); } });
    ctrl.addEventListener("keydown", function (ev) {
      if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
        ev.preventDefault();
        if (lista.hidden) { abrir(); desenhar(); }
        if (!visiveis.length) return;
        ativo = ev.key === "ArrowDown" ? (ativo + 1) % visiveis.length : (ativo <= 0 ? visiveis.length - 1 : ativo - 1);
        desenhar();
      } else if (ev.key === "Enter") {
        if (!lista.hidden && ativo >= 0 && visiveis[ativo]) { ev.preventDefault(); escolher(visiveis[ativo]); }
        else if (!lista.hidden && visiveis.length === 1 && ctrl.value) { ev.preventDefault(); escolher(visiveis[0]); }
      } else if (ev.key === "Escape") {
        if (!lista.hidden) { ev.preventDefault(); fechar(); }
      }
    });
    ctrl.addEventListener("blur", function () {
      // texto idêntico a uma opção (sem acento/caixa) vale como escolha; qualquer outro texto fica sem escolha e a validação avisa
      if (!escolhido && ctrl.value) {
        var n = R.normalizar(ctrl.value), achado = itens.filter(function (it) { return R.normalizar(it[1]) === n; });
        if (achado.length === 1) escolher(achado[0]);
      }
      fechar();
    });
    return {
      caixa: caixa, ctrl: ctrl,
      definirItens: function (lst) { itens = lst || []; if (!lista.hidden) desenhar(); },
      definir: function (it) { escolhido = it; ctrl.value = it ? it[1] : ""; },
      habilitar: function (sim, placeholder) { ctrl.disabled = !sim; ctrl.setAttribute("aria-disabled", sim ? "false" : "true"); ctrl.placeholder = placeholder || ""; if (!sim) fechar(); },
      limparTudo: function () { escolhido = null; ctrl.value = ""; fechar(); }
    };
  }

  // ── localidades: arquivos locais, por UF, com cache ─────────────────────────────────────────────────
  var cache = {};
  function carregar(caminho) {
    if (!cache[caminho]) {
      cache[caminho] = fetch(caminho, { credentials: "omit", referrerPolicy: "no-referrer" })
        .then(function (r) { if (!r.ok) throw new Error("http"); return r.json(); })
        .catch(function (e) { delete cache[caminho]; throw e; });
    }
    return cache[caminho];
  }

  // ── montagem da página ────────────────────────────────────────────────────────────────────────────
  function montar() {
    app.textContent = "";
    var e = estado, l = e.location, c = e.contact;

    var topo = h("div", null,
      h("h1", { class: "etapa__titulo etapa__titulo--grande", id: "titulo-pagina", tabindex: "-1", texto: "Apresente o cenário. A CRIVIA ajuda a encontrar o que precisa ser decidido." }),
      h("p", { class: "etapa__desc", texto: "Conte o essencial sobre a situação. A CRIVIA analisa o contexto e responde pelo canal indicado, sem compromisso de contratação." }),
      h("p", { class: "micro", texto: "Leva cerca de 1 minuto. Não envie documentos confidenciais nesta etapa." }));
    refs.resumo = h("div", { id: "resumo" });

    // 1. situação + pergunta curta que depende dela
    var sitMulti = multi("sit", R.SITUACOES.map(function (s) { return { v: s.v, l: s.l }; }), function (sel) {
      var antes = e.situationCodes.length;
      e.situationCodes = sel; limpar("situationCodes"); desenharContexto(); salvar();
      if (sel.length && sel.length > antes) rastrear("scenario_branch_selected", { branch: sel[0] });
    }, { exclusivas: R.EXCLUSIVAS.situationCodes });
    refs.situacao = sitMulti.cx;
    // pergunta curta de CADA situação marcada: aparece logo abaixo, só para as marcadas (opcional; sai junto se a situação for desmarcada)
    refs.ctxBlocos = {};
    refs.contextos = h("div", { class: "ctx", hidden: "hidden" });
    R.SITUACOES.forEach(function (s) {
      var cx = chips("ctx", s.opcoes, function (v) { e.contextAnswers[s.v] = v; salvar(); });
      var lid = "lb-ctx-" + s.v;
      var el = h("div", { class: "grupo grupo--ctx", role: "group", "aria-labelledby": lid, hidden: "hidden" },
        h("div", { class: "ctx__rotulo", id: lid }, h("span", { class: "ctx__sit", texto: s.l }), h("span", { class: "ctx__perg", texto: s.q }), h("span", { class: "grupo__opcional", texto: " (opcional)" })), cx);
      refs.ctxBlocos[s.v] = { el: el, cx: cx };
      refs.contextos.appendChild(el);
    });
    var b1 = h("div", { class: "bloco" }, grupoMulti("situationCodes", "O que mais se aproxima do seu cenário hoje?", sitMulti), refs.contextos);

    // 2. perfil e participação
    var perfMulti = multi("perfil", R.PERFIS, function (sel) { e.audienceProfiles = sel; limpar("audienceProfiles"); sincronizar(); salvar(); });
    refs.perfil = perfMulti.cx;
    refs.papel = chips("papel", R.PAPEIS, function (v) { e.decisionRole = v; limpar("decisionRole"); salvar(); });
    refs.papelGrupo = grupo("decisionRole", "Qual é a sua participação nessa decisão?", refs.papel);
    refs.papelGrupo.classList.add("sub");
    var b2 = h("div", { class: "bloco" }, grupoMulti("audienceProfiles", "Você está falando como:", perfMulti), refs.papelGrupo);

    // 3. localização (Brasil estruturado | Exterior)
    refs.tipoLoc = chips("loc", [{ v: "brazil", l: "Brasil" }, { v: "international", l: "Exterior" }], function (v) { l.type = v; limpar("location.type"); sincronizar(); salvar();
      anunciar(v === "brazil" ? "Brasil: escolha estado e cidade." : "Exterior: escolha país e cidade."); if (v === "international") prepararPaises(); }, "segmento");
    refs.tipoLoc.setAttribute("role", "presentation");
    refs.uf = h("select", { id: "c-location-state", name: "state", "aria-required": "true", "aria-describedby": "c-location-state-er", autocomplete: "off",
      onchange: function (ev) { aoMudarUF(ev.target.value); } }, h("option", { value: "", texto: "Selecione…" }));
    var msgUf = h("p", { class: "campo__erro", id: "c-location-state-er", role: "alert" });
    var caixaUf = h("div", { class: "campo" }, h("label", { for: "c-location-state", texto: "Estado" }), refs.uf, msgUf);
    registrar("location.state", caixaUf, refs.uf, msgUf);
    refs.cidade = combobox("location.city", "Cidade", { placeholder: "Escolha primeiro o estado", semItens: "Carregando cidades…", aoEscolher: function (it) {
      l.cityCode = it ? it[0] : ""; l.cityName = it ? it[1] : ""; salvar(); } });
    refs.cidade.habilitar(false, "Escolha primeiro o estado");
    refs.brasil = h("div", { class: "par sub" }, caixaUf, refs.cidade.caixa);

    refs.pais = combobox("location.country", "País", { placeholder: "Digite para buscar o país", semItens: "Carregando países…", aoEscolher: function (it) {
      if (it && it[0] === "BR") {   // Brasil escolhido na lista de países: volta ao modo estruturado
        l.type = "brazil"; l.countryCode = ""; l.countryName = ""; refs.pais.limparTudo(); sincronizar(); salvar();
        anunciar("Brasil selecionado. Escolha o estado e a cidade."); refs.uf.focus(); return;
      }
      l.countryCode = it ? it[0] : ""; l.countryName = it ? it[1] : ""; salvar(); } });
    var cidadeEx = campo("location.cityName", "Cidade", { autocomplete: "address-level2", obrigatorio: true, aoMudar: function (v) { l.intlCity = v; } });
    var regiaoEx = campo("location.foreignRegion", "Estado, província ou região", { autocomplete: "address-level1", obrigatorio: false, aoMudar: function (v) { l.foreignRegion = v; } });
    refs.cidadeEx = cidadeEx.ctrl; refs.regiaoEx = regiaoEx.ctrl;
    refs.exterior = h("div", { class: "par sub" }, refs.pais.caixa, cidadeEx.caixa, regiaoEx.caixa);
    var b3 = h("div", { class: "bloco" }, grupo("location.type", "Onde está o projeto, a empresa ou o cenário que você quer apresentar?", refs.tipoLoc),
      refs.brasil, refs.exterior,
      h("p", { class: "campo__ajuda", texto: "É a localização do cenário, não a sua residência. Usamos para avaliar atendimento e contexto local; não coletamos GPS nem endereço." }));

    // 4. relato
    var rel = campo("narrative", "O que está acontecendo e qual decisão você precisa tomar?", { area: true, obrigatorio: true, numerar: true, autocomplete: "off",
      ajuda: "Se puder, diga o que já aconteceu, o que mais preocupa e o que precisa ser definido. Não inclua senhas, documentos pessoais, dados bancários, informações médicas ou arquivos confidenciais.",
      aoMudar: function (v) { e.narrative = v; var ct = document.getElementById("c-narrative-ct"); if (ct) { ct.textContent = v.length + " / " + R.LIMITES.narrativa; ct.style.color = v.length > R.LIMITES.narrativa ? "#B3261E" : ""; } } });
    refs.narrativa = rel.ctrl;
    var b4 = h("div", { class: "bloco" }, rel.caixa);

    // 4b. perguntas opcionais que ajudam a preparar a conversa (na mesma página; podem ser recolhidas)
    var X = R.EXCLUSIVAS;
    var mUrg = multi("urg", R.URGENCIAS, function (sel) { e.urgencies = sel; salvar(); }, { exclusivas: X.urgencies });
    var mCons = multi("cons", R.CONSEQUENCIAS, function (sel) { e.consequences = sel; salvar(); });
    var mDocs = multi("docs", R.DOCUMENTOS, function (sel) { e.documents = sel; salvar(); }, { exclusivas: X.documents });
    var mFaixa = multi("faixa", R.FAIXAS, function (sel) { e.estimatedRanges = sel; salvar(); }, { exclusivas: X.estimatedRanges });
    var mPer = multi("per", R.PERIODOS, function (sel) { c.contactPeriods = sel; salvar(); }, { exclusivas: X.contactPeriods });
    refs.urgencia = mUrg.cx; refs.consequencias = mCons.cx; refs.documentos = mDocs.cx; refs.faixa = mFaixa.cx; refs.periodo = mPer.cx;
    // sempre visível: o que não for preenchido simplesmente não é enviado
    var b4b = h("section", { class: "bloco opcionais" },
      h("h2", { class: "opcionais__titulo" }, "Para adiantar a análise ", h("span", { class: "grupo__opcional", texto: "(opcional — responda o que souber; pode marcar mais de uma)" })),
      h("div", { class: "opcionais__corpo" },
        grupoMulti("urgencies", "Quando essa decisão precisa avançar?", mUrg),
        grupoMulti("consequences", "O que mais preocupa se nada mudar?", mCons),
        grupoMulti("documents", "Você já tem documentos do caso (contrato, projeto, cronograma, medições)?", mDocs),
        grupoMulti("estimatedRanges", "Faixa aproximada do empreendimento ou contrato", mFaixa),
        grupoMulti("contactPeriods", "Melhor período para contato", mPer)));

    // 5. contato mínimo
    var nome = campo("contact.name", "Nome", { autocomplete: "name", obrigatorio: true, aoMudar: function (v) { c.name = v; } });
    var org = campo("contact.organization", "Empresa ou organização", { autocomplete: "organization", obrigatorio: false, aoMudar: function (v) { c.organization = v; } });
    refs.nome = nome.ctrl; refs.org = org.ctrl;
    refs.canal = chips("canal", R.CANAIS, function (v) { c.preferredChannel = v; limpar("contact.preferredChannel"); sincronizar(); salvar(); }, "segmento");
    var fone = campo("contact.phone", "WhatsApp", { tipo: "tel", inputmode: "tel", autocomplete: "tel", obrigatorio: true, ajuda: "Com DDD, ou com + e o código do país.", aoMudar: function (v) { c.phone = v; } });
    var mail = campo("contact.email", "E-mail", { tipo: "email", inputmode: "email", autocomplete: "email", obrigatorio: true, aoMudar: function (v) { c.email = v; } });
    refs.fone = fone; refs.mail = mail;
    refs.maisCanal = h("button", { type: "button", class: "mais", onclick: function () { ui.mostrarOutroCanal = true; sincronizar(); (c.preferredChannel === "whatsapp" ? refs.mail.ctrl : refs.fone.ctrl).focus(); } });
    var b5 = h("div", { class: "bloco" },
      h("div", { class: "par" }, nome.caixa, org.caixa),
      grupo("contact.preferredChannel", "Como prefere receber a resposta?", refs.canal),
      fone.caixa, mail.caixa, refs.maisCanal,
      h("p", { class: "resposta" }, "A resposta da CRIVIA será feita por ", h("strong", { texto: CFG.contactEmail }), " ou pelo WhatsApp informado, conforme sua preferência."));

    // 6. privacidade em camadas + envio
    var privac = h("div", { class: "privacidade" }, h("p", null, "Usaremos seus dados para analisar o cenário, responder ao contato e avaliar uma possível contratação. Consulte o ",
      h("a", { href: CFG.privacyNoticeUrl, target: "_blank", rel: "noopener", texto: "Aviso de Privacidade" }), "."));
    var armadilha = h("div", { class: "armadilha", "aria-hidden": "true" }, h("label", null, "Não preencha este campo", h("input", { type: "text", name: "website", id: "campo-website", tabindex: "-1", autocomplete: "off" })));
    refs.erroEnvio = h("p", { class: "erro-envio", role: "alert", hidden: "hidden" });
    // mesmo botão do "Conhecer o método" da Hero: pílula azul com brilho ciano na base e pontos de luz subindo
    var pontos = h("span", { class: "btn__pontos", "aria-hidden": "true" });
    for (var p = 0; p < 7; p++) pontos.appendChild(h("i", { class: "btn__ponto" }));
    var seta = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    seta.setAttribute("viewBox", "0 0 24 24"); seta.setAttribute("fill", "none"); seta.setAttribute("stroke", "currentColor");
    seta.setAttribute("stroke-width", "2"); seta.setAttribute("stroke-linecap", "round"); seta.setAttribute("stroke-linejoin", "round"); seta.setAttribute("aria-hidden", "true");
    ["M5 12h14", "M13 6l6 6-6 6"].forEach(function (d) {
      var tr = document.createElementNS("http://www.w3.org/2000/svg", "path"); tr.setAttribute("d", d); seta.appendChild(tr);
    });
    refs.rotuloBotao = h("span", { class: "btn__rotulo", texto: "Enviar meu cenário" });
    refs.botao = h("button", { type: "submit", class: "btn btn--metodo", id: "btn-enviar" },
      pontos, h("span", { class: "btn__interno" }, refs.rotuloBotao, h("span", { class: "btn__seta", "aria-hidden": "true" }, seta)));
    var b6 = h("div", { class: "bloco" }, privac, armadilha, refs.erroEnvio, h("div", { class: "acoes" }, refs.botao));

    var form = h("form", { id: "form-cenario", novalidate: "novalidate", onsubmit: function (ev) { ev.preventDefault(); enviar(); } }, refs.resumo, b1, b2, b3, b4, b4b, b5, b6);
    app.appendChild(h("div", { class: "etapa" }, topo, form));

    aplicarEstado();
  }

  function desenharContexto() {
    var marcadas = estado.situationCodes, algum = false;
    R.SITUACOES.forEach(function (s) {
      var bl = refs.ctxBlocos[s.v], ligado = marcadas.indexOf(s.v) >= 0;
      bl.el.hidden = !ligado;
      if (ligado) algum = true;
      else if (estado.contextAnswers[s.v]) { delete estado.contextAnswers[s.v]; marcar(bl.cx, ""); }   // situação desmarcada: a resposta sai junto
    });
    refs.contextos.hidden = !algum;
  }

  /** Mostra/oculta o que depende das respostas, sem recriar controles (o foco e o texto digitado ficam intactos). */
  function sincronizar() {
    var e = estado, l = e.location, c = e.contact;
    refs.papelGrupo.hidden = !e.audienceProfiles.length;
    refs.brasil.hidden = l.type !== "brazil";
    refs.exterior.hidden = l.type !== "international";
    marcar(refs.tipoLoc, l.type);
    var temFone = c.preferredChannel === "whatsapp" || (ui.mostrarOutroCanal && c.preferredChannel === "email") || (c.phone || "").trim() !== "";
    var temMail = c.preferredChannel === "email" || (ui.mostrarOutroCanal && c.preferredChannel === "whatsapp") || (c.email || "").trim() !== "";
    refs.fone.caixa.hidden = !c.preferredChannel ? true : !temFone;
    refs.mail.caixa.hidden = !c.preferredChannel ? true : !temMail;
    var obrigFone = c.preferredChannel === "whatsapp", obrigMail = c.preferredChannel === "email";
    refs.fone.ctrl.setAttribute("aria-required", obrigFone ? "true" : "false");
    refs.mail.ctrl.setAttribute("aria-required", obrigMail ? "true" : "false");
    refs.fone.caixa.querySelector("label").textContent = obrigFone ? "WhatsApp" : "WhatsApp (opcional)";
    refs.mail.caixa.querySelector("label").textContent = obrigMail ? "E-mail" : "E-mail (opcional)";
    var faltaOutro = c.preferredChannel === "whatsapp" ? refs.mail.caixa.hidden : c.preferredChannel === "email" ? refs.fone.caixa.hidden : true;
    refs.maisCanal.hidden = !faltaOutro;
    refs.maisCanal.textContent = c.preferredChannel === "whatsapp" ? "+ Informar também um e-mail" : "+ Informar também um WhatsApp";
  }

  // ── estados e cidades ──────────────────────────────────────────────────────────────────────────────
  var estadosCarregados = null;
  function carregarEstados() {
    return carregar("data/locations/states.json").then(function (lst) {
      estadosCarregados = lst;
      lst.forEach(function (u) { refs.uf.appendChild(h("option", { value: u[0], texto: u[1] + " (" + u[0] + ")" })); });
      refs.uf.value = estado.location.stateCode;
    }).catch(function () { refs.uf.appendChild(h("option", { value: "", texto: "Não foi possível carregar os estados. Recarregue a página." })); });
  }
  function carregarCidades(uf) {
    refs.cidade.habilitar(false, "Carregando cidades…");
    return carregar("data/locations/municipalities/" + uf + ".json").then(function (lst) {
      if (estado.location.stateCode !== uf) return;   // o visitante já trocou de estado
      refs.cidade.definirItens(lst);
      refs.cidade.habilitar(true, "Digite para buscar a cidade");
      var l = estado.location;
      if (l.cityCode) { var it = lst.filter(function (x) { return x[0] === l.cityCode; })[0]; if (it) refs.cidade.definir(it); else { l.cityCode = ""; l.cityName = ""; } }
    }).catch(function () { refs.cidade.habilitar(false, "Não foi possível carregar as cidades"); anunciar("Não foi possível carregar as cidades. Tente escolher o estado de novo."); });
  }
  function aoMudarUF(uf) {
    var l = estado.location, tinha = !!l.cityCode;
    l.stateCode = uf; l.cityCode = ""; l.cityName = "";
    limpar("location.state"); limpar("location.city");
    refs.cidade.limparTudo(); refs.cidade.definirItens([]);
    if (!uf) { refs.cidade.habilitar(false, "Escolha primeiro o estado"); }
    else { carregarCidades(uf); if (tinha) anunciar("Estado alterado. A cidade anterior foi limpa; escolha uma cidade."); }
    salvar();
  }
  function prepararPaises() {
    if (refs.paisesOk) return;
    carregar("data/locations/countries.json").then(function (lst) {
      refs.paisesOk = true; refs.pais.definirItens(lst);
      var l = estado.location; if (l.countryCode) { var it = lst.filter(function (x) { return x[0] === l.countryCode; })[0]; if (it) refs.pais.definir(it); }
    }).catch(function () { anunciar("Não foi possível carregar a lista de países. Recarregue a página."); });
  }

  function aplicarEstado() {
    var e = estado, l = e.location, c = e.contact;
    marcar(refs.situacao, e.situationCodes); desenharContexto();
    R.SITUACOES.forEach(function (s) { marcar(refs.ctxBlocos[s.v].cx, e.contextAnswers[s.v] || ""); });
    marcar(refs.perfil, e.audienceProfiles); marcar(refs.papel, e.decisionRole);
    marcar(refs.canal, c.preferredChannel);
    marcar(refs.urgencia, e.urgencies); marcar(refs.consequencias, e.consequences); marcar(refs.documentos, e.documents); marcar(refs.faixa, e.estimatedRanges); marcar(refs.periodo, c.contactPeriods);
    refs.nome.value = c.name; refs.org.value = c.organization; refs.fone.ctrl.value = c.phone; refs.mail.ctrl.value = c.email;
    refs.narrativa.value = e.narrative; refs.narrativa.dispatchEvent(new Event("input"));
    refs.cidadeEx.value = l.intlCity; refs.regiaoEx.value = l.foreignRegion;
    sincronizar();
    carregarEstados().then(function () { if (l.stateCode) carregarCidades(l.stateCode); });
    if (l.type === "international") prepararPaises();
  }

  // ── envio ─────────────────────────────────────────────────────────────────────────────────────────
  var MSG_FALHA = "Não foi possível enviar seu cenário agora. Suas respostas permanecem nesta página. Tente novamente" + (CFG.contactEmail ? " ou escreva para " + CFG.contactEmail : "") + ".";

  // Protocolo: POST com corpo JSON enviado como text/plain (requisição "simples": o Google Apps Script não responde a preflight CORS).
  // Nenhum dado pessoal vai na URL; a resposta é sempre JSON {ok, ...}. O servidor local de testes fala o mesmo protocolo.
  function chamar(acao, dados) {
    var ctl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = ctl ? setTimeout(function () { ctl.abort(); }, 20000) : null;
    return fetch(String(CFG.endpoint || ""), { method: "POST", headers: { "Content-Type": "text/plain;charset=utf-8" }, body: JSON.stringify({ action: acao, data: dados }),
      credentials: "omit", mode: "cors", redirect: "follow", referrerPolicy: "no-referrer", signal: ctl ? ctl.signal : undefined })
      .then(function (resp) { if (timer) clearTimeout(timer); return resp.json().catch(function () { return { ok: false }; }).then(function (j) { return { status: resp.status, json: j || {} }; }); });
  }

  function mostrarErros(erros) {
    Object.keys(reg).forEach(function (k) { marcarErro(k, erros[k] || ""); });
    ui.erros = erros;
    var chaves = Object.keys(erros);
    refs.resumo.textContent = "";
    if (!chaves.length) return;
    var ul = h("ul");
    chaves.forEach(function (k) {
      var r = reg[k];
      ul.appendChild(h("li", null, h("a", { href: "#", onclick: function (ev) {
        ev.preventDefault();
        var alvo = r && (r.ctrl || r.caixa.querySelector("input,select,textarea"));
        if (alvo) { alvo.focus(); if (alvo.scrollIntoView) alvo.scrollIntoView({ block: "center" }); }
      }, texto: erros[k] })));
    });
    refs.resumo.appendChild(h("div", { class: "resumo-erros", role: "alert", tabindex: "-1", id: "resumo-erros" }, h("strong", { texto: "Revise antes de enviar:" }), ul));
    var rs = document.getElementById("resumo-erros"); if (rs) { rs.focus(); }
  }

  function definirEnvio(sim, erro) {
    ui.enviando = sim;
    refs.botao.disabled = sim; refs.rotuloBotao.textContent = sim ? "Enviando com segurança…" : "Enviar meu cenário";
    refs.erroEnvio.hidden = !erro; refs.erroEnvio.textContent = erro || "";
  }

  function enviar() {
    if (ui.enviando) return;
    var erros = R.validar(estado);
    mostrarErros(erros);
    if (Object.keys(erros).length) { rastrear("scenario_validation_error", { errorType: "required" }); return; }
    if (!CFG.endpoint || CFG.endpoint.indexOf("__CRIVIA") === 0) { definirEnvio(false, MSG_FALHA); return; }
    definirEnvio(true, "");
    ui.idem = ui.idem || (window.crypto && crypto.randomUUID ? crypto.randomUUID() : (Date.now().toString(36) + Math.random().toString(36).slice(2) + "00000000"));
    var hp = document.getElementById("campo-website");
    var ref = ""; try { ref = document.referrer ? new URL(document.referrer).hostname : ""; } catch (x) { ref = ""; }
    var payload = R.montarPayload(estado, ORIGEM, { idempotencyKey: ui.idem, deviceCategory: dispositivo(), referrer: ref, privacyNoticeVersion: CFG.privacyNoticeVersion,
      honeypot: hp ? hp.value : "", formVersion: FORM_VERSION, elapsedMs: Date.now() - inicio });
    chamar("submit", payload).then(function (res) {
      if (res.json.ok === true) {
        ui.resultado = { confirmation: res.json.confirmation || "" };
        limparRascunho();
        rastrear("scenario_submit_success", { duration: Math.round((Date.now() - inicio) / 10000) * 10 });
        telaSucesso(); anunciar("Cenário recebido.");
      } else if (res.json.error === "validation" && res.json.fields) {
        definirEnvio(false, "Algumas respostas não foram aceitas. Revise os campos e envie de novo.");
        rastrear("scenario_submit_error", { errorType: "validation" });
      } else {
        definirEnvio(false, MSG_FALHA); rastrear("scenario_submit_error", { errorType: res.json.error === "rate" ? "rate" : "server" });
      }
    }).catch(function () { definirEnvio(false, MSG_FALHA); rastrear("scenario_submit_error", { errorType: "network" }); });
  }

  // ── depois do envio confirmado ──────────────────────────────────────────────────────────────────────
  // O protocolo NÃO é mostrado na tela: vai ao visitante pelo canal que ele escolheu (e-mail automático; WhatsApp enviado pela equipe).
  var AVISO_CONFIRMACAO = {
    email: "Enviamos uma confirmação, com o protocolo, para o e-mail informado. Guarde essa mensagem para qualquer contato futuro.",
    whatsapp: "A CRIVIA enviará a confirmação, com o protocolo, ao WhatsApp informado. Guarde essa mensagem para qualquer contato futuro."
  };
  function telaSucesso() {
    var res = ui.resultado;
    app.textContent = "";
    app.appendChild(h("div", { class: "etapa" },
      h("p", { class: "etiqueta" }, h("i"), "Enviado"),
      h("h1", { class: "etapa__titulo etapa__titulo--grande", id: "titulo-pagina", tabindex: "-1", texto: "Cenário recebido." }),
      h("p", { class: "etapa__desc", texto: "A CRIVIA vai analisar as informações e responder pelo canal indicado. O envio não constitui diagnóstico, proposta, contratação ou compromisso de atendimento." }),
      AVISO_CONFIRMACAO[res.confirmation] ? h("p", { class: "confirmacao", role: "status", texto: AVISO_CONFIRMACAO[res.confirmation] }) : null,
      h("div", { class: "pos-volta" }, h("a", { class: "btn btn--prim", id: "btn-voltar-hero", href: CFG.voltarAoSiteUrl || "index.html", texto: "Voltar ao início do site" })),
      CFG.contactEmail ? h("p", { class: "ciencia" }, "Para acrescentar algo, escreva para ", h("a", { href: "mailto:" + CFG.contactEmail + "?subject=" + encodeURIComponent("Complemento ao cenário enviado pelo site"), texto: CFG.contactEmail }),
        ". Não envie dados pessoais sensíveis nem documentos sigilosos por e-mail.") : null));
    var t = document.getElementById("titulo-pagina"); if (t) t.focus({ preventScroll: true });
    window.scrollTo({ top: 0 });
  }

  // ── início ────────────────────────────────────────────────────────────────────────────────────────
  restaurar();
  montar();
  rastrear("scenario_view", { device: dispositivo(), origin: ORIGEM.originCta, productHint: ORIGEM.productHint || undefined });
})();
