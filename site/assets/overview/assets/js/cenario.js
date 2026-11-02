/* Página "Apresentar meu cenário": formulário progressivo de 4 etapas.
   - Todo texto vindo do usuário é inserido com textContent (nunca innerHTML).
   - Nada é enviado ao servidor antes do envio consciente; nenhuma captura parcial.
   - sessionStorage guarda apenas ESCOLHAS não sensíveis (nunca nome, telefone, e-mail, empresa ou texto livre). */
(function () {
  "use strict";
  var CFG = window.CRIVIA_CENARIO_CONFIG;
  var R = window.CRIVIA_REGRAS;
  var app = document.getElementById("app");
  var STORE = "crivia_cenario_v1";
  var ORIGEM = R.lerOrigem(location.search);
  var inicio = Date.now();

  var estado = { etapa: 0, r: { contact: {}, branch: {} }, erros: {}, enviando: false, erroEnvio: "", resultado: null, idem: null };

  // ── utilidades de DOM ───────────────────────────────────────────────────────────────────────
  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === "class") el.className = v;
      else if (k === "texto") el.textContent = v;
      else if (k.slice(0, 2) === "on") el.addEventListener(k.slice(2), v);
      else if (k === "valor") el.value = v;
      else if (k === "style") el.style.cssText = v;   // CSSOM: compatível com a CSP (style-src 'self')
      else el.setAttribute(k, v === true ? "" : v);
    });
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c === null || c === undefined || c === false) continue;
      el.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }
    return el;
  }
  var uid = (function () { var n = 0; return function (p) { n += 1; return p + "-" + n; }; })();
  var anuncio = document.getElementById("anuncio");
  function anunciar(msg) { if (anuncio) { anuncio.textContent = ""; setTimeout(function () { anuncio.textContent = msg; }, 30); } }

  // ── analytics do funil (sem PII; desligado por padrão) ──────────────────────────────────────────
  var PARAMS_OK = ["step", "branch", "device", "origin", "productHint", "errorType", "duration"];
  function rastrear(evento, params) {
    try {
      if (!CFG.analyticsEnabled || !window.CRIVIA_CONSENT || window.CRIVIA_CONSENT.analytics !== true) return;
      var limpo = {};
      Object.keys(params || {}).forEach(function (k) { if (PARAMS_OK.indexOf(k) >= 0) limpo[k] = params[k]; });
      window.dispatchEvent(new CustomEvent("crivia:evento", { detail: { evento: evento, params: limpo } }));
    } catch (e) { /* nunca interrompe o formulário */ }
  }
  function dispositivo() { var w = window.innerWidth; return w < 768 ? "mobile" : w < 1100 ? "tablet" : "desktop"; }

  // ── sessionStorage: somente escolhas não sensíveis ─────────────────────────────────────────────
  function salvar() {
    try {
      var r = estado.r, b = r.branch || {};
      var copia = { etapa: estado.etapa, r: {}, branch: {} };
      ["entryPath", "audienceContext", "decisionRole", "stage", "issues", "consequences", "decisionHorizon", "state", "estimatedRange", "availableDocuments"].forEach(function (k) { if (r[k] !== undefined) copia.r[k] = r[k]; });
      Object.keys(b).forEach(function (k) { if (typeof b[k] !== "string" || k !== "decisionNeeded") copia.branch[k] = b[k]; });
      sessionStorage.setItem(STORE, JSON.stringify(copia));
    } catch (e) { /* armazenamento indisponível: segue sem salvar */ }
  }
  function restaurar() {
    try {
      var bruto = sessionStorage.getItem(STORE);
      if (!bruto) return;
      var d = JSON.parse(bruto);
      if (d && typeof d === "object") {
        Object.keys(d.r || {}).forEach(function (k) { estado.r[k] = d.r[k]; });
        estado.r.branch = d.branch || {};
        estado.etapa = Math.min(Number(d.etapa) || 0, 4);
      }
    } catch (e) { /* ignora */ }
  }
  function limparArmazenamento() { try { sessionStorage.removeItem(STORE); } catch (e) { /* ignora */ } }

  // ── componentes ───────────────────────────────────────────────────────────────────────────────
  // tira a marca de erro assim que o visitante corrige o campo (o resumo é refeito na próxima validação)
  function limparErroVisual(caixa) {
    if (!caixa) return;
    caixa.classList.remove("campo--erro", "grupo--erro");
    var ctrl = caixa.querySelector("[aria-invalid]"); if (ctrl) ctrl.removeAttribute("aria-invalid");
    var er = caixa.querySelector(".campo__erro"); if (er) er.textContent = "";
  }

  function opcoes(id, tipo, lista, atual, max, aoMudar) {
    var multi = tipo === "multi";
    var nome = uid("n");
    var contador = multi && max && max < lista.length ? h("p", { class: "opcoes__contador", "aria-live": "polite", texto: (atual || []).length + " de " + max + " selecionadas" }) : null;
    var cont = h("div", { class: "opcoes" + (lista.some(function (o) { return o.d; }) ? " opcoes--descritas" : "") });
    lista.forEach(function (o) {
      var marcado = multi ? (atual || []).indexOf(o.v) >= 0 : atual === o.v;
      var inp = h("input", { type: multi ? "checkbox" : "radio", name: nome, value: o.v, checked: marcado ? "checked" : null, "data-campo": id,
        onchange: function (ev) {
          limparErroVisual(ev.target.closest("fieldset"));
          if (multi) {
            var sel = Array.prototype.slice.call(cont.querySelectorAll("input:checked")).map(function (i) { return i.value; });
            if (max && sel.length > max) {
              ev.target.checked = false;
              anunciar("Você pode escolher até " + max + " opções.");
              if (contador) { contador.textContent = "Você pode escolher até " + max + " opções."; contador.classList.add("opcoes__contador--aviso"); }
              return;
            }
            if (contador) { contador.textContent = sel.length + " de " + max + " selecionadas"; contador.classList.remove("opcoes__contador--aviso"); }
            aoMudar(sel);
          } else aoMudar(o.v);
        } });
      cont.appendChild(h("label", { class: "opc" }, inp, h("span", { class: "opc__marca", "aria-hidden": "true" }),
        h("span", { class: "opc__texto" }, h("strong", { texto: o.l }), o.d ? h("small", { texto: o.d }) : null)));
    });
    var frag = document.createDocumentFragment();
    frag.appendChild(cont); if (contador) frag.appendChild(contador);
    return frag;
  }

  function grupo(id, rotulo, ajuda, conteudo, erro, obrigatorio) {
    var ajId = ajuda ? id + "-aj" : null, erId = id + "-er";
    var fs = h("fieldset", { class: "grupo" + (erro ? " grupo--erro" : ""), id: "g-" + id, "aria-describedby": [ajId, erro ? erId : null].filter(Boolean).join(" ") || null },
      h("legend", { class: "grupo__rotulo" }, rotulo, obrigatorio === false ? h("span", { class: "grupo__opcional", texto: " (opcional)" }) : null),
      ajuda ? h("p", { class: "campo__ajuda", id: ajId, texto: ajuda }) : null, conteudo,
      h("p", { class: "campo__erro", id: erId, texto: erro || "" }));
    return fs;
  }

  function campoTexto(id, rotulo, o) {
    var erro = estado.erros[id];
    var ajId = o.ajuda ? id + "-aj" : null;
    var area = o.area;
    var ctrl = h(area ? "textarea" : "input", {
      id: "c-" + id, name: id, type: area ? null : (o.tipo || "text"), rows: area ? "5" : null, maxlength: o.max ? String(o.max) : null,
      autocomplete: o.autocomplete || "off", inputmode: o.inputmode || null, "aria-invalid": erro ? "true" : null,
      "aria-describedby": [ajId, erro ? id + "-er" : null, area && o.max ? id + "-ct" : null].filter(Boolean).join(" ") || null,
      "aria-required": o.obrigatorio ? "true" : null, valor: o.valor || "", spellcheck: o.tipo === "email" || o.tipo === "tel" ? "false" : null,
      oninput: function (ev) { o.aoMudar(ev.target.value); limparErroVisual(ev.target.closest(".campo")); if (contador) contador.textContent = ev.target.value.length + " / " + o.max; },
      onblur: o.aoSair ? function (ev) { o.aoSair(ev.target); } : null });
    var contador = area && o.max ? h("p", { class: "campo__contador", id: id + "-ct", texto: (o.valor || "").length + " / " + o.max }) : null;
    return h("div", { class: "campo" + (erro ? " campo--erro" : "") },
      h("label", { for: "c-" + id }, rotulo, o.obrigatorio === false ? h("span", { class: "grupo__opcional", texto: " (opcional)" }) : null),
      o.ajuda ? h("p", { class: "campo__ajuda", id: ajId, texto: o.ajuda }) : null, ctrl, contador,
      h("p", { class: "campo__erro", id: id + "-er", texto: erro || "" }));
  }

  function resumoErros() {
    var chaves = Object.keys(estado.erros);
    if (!chaves.length) return null;
    var lista = h("ul");
    chaves.forEach(function (k) {
      var alvo = document.getElementById("c-" + k) || document.getElementById("g-" + k);
      lista.appendChild(h("li", null, h("a", { href: "#" + (alvo ? alvo.id : "app"), onclick: function (ev) { ev.preventDefault(); if (alvo) { (alvo.querySelector && alvo.querySelector("input,select,textarea") || alvo).focus(); alvo.scrollIntoView({ block: "center" }); } } }, estado.erros[k])));
    });
    return h("div", { class: "resumo-erros", role: "alert", tabindex: "-1", id: "resumo-erros" }, h("strong", { texto: "Revise antes de continuar:" }), lista);
  }

  function moldura(etapa, titulo, descricao, corpo, rodape) {
    var pct = Math.round(((etapa - 1) / 4) * 100);
    return h("div", { class: "etapa" },
      h("div", { class: "progresso" },
        h("p", { class: "progresso__texto", texto: "Etapa " + etapa + " de 4" }),
        h("div", { class: "progresso__barra", role: "progressbar", "aria-valuemin": "0", "aria-valuemax": "4", "aria-valuenow": String(etapa), "aria-label": "Etapa " + etapa + " de 4" },
          h("span", { style: "width:" + Math.max(pct, 6) + "%" }))),
      h("h1", { class: "etapa__titulo", tabindex: "-1", id: "titulo-etapa", texto: titulo }),
      descricao ? h("p", { class: "etapa__desc", texto: descricao }) : null,
      resumoErros(), corpo, rodape);
  }

  function botoes(etapa, rotuloAvancar, aoAvancar) {
    return h("div", { class: "acoes" },
      etapa > 1 ? h("button", { type: "button", class: "btn btn--sec", onclick: function () { ir(etapa - 1); } }, "Voltar") : h("span"),
      h("button", { type: "button", class: "btn btn--prim", id: "btn-avancar", disabled: estado.enviando ? "disabled" : null, onclick: aoAvancar }, rotuloAvancar));
  }

  // ── telas ────────────────────────────────────────────────────────────────────────────────────
  function telaIntro() {
    var dica = ORIGEM.productHint ? h("p", { class: "dica-origem" }, "Você chegou pelo interesse em ", h("strong", { texto: R.NOMES_PRODUTOS[ORIGEM.productHint] }), ". É só uma pista: você pode escolher outra situação abaixo.") : null;
    return h("div", { class: "etapa etapa--intro" },
      h("p", { class: "etiqueta" }, h("i"), "Conversa inicial"),
      h("h1", { class: "etapa__titulo etapa__titulo--grande", tabindex: "-1", id: "titulo-etapa", texto: "Apresente seu cenário. Nós organizamos o ponto de partida." }),
      h("p", { class: "etapa__desc", texto: "Conte o essencial sobre a obra, o contrato, a operação ou a decisão que precisa avançar. As perguntas se ajustam ao seu caso e você não precisa saber qual serviço escolher." }),
      dica,
      h("p", { class: "transparencia", texto: "Este formulário não gera diagnóstico ou orçamento automático. Ele reúne as informações necessárias para uma conversa inicial mais objetiva." }),
      h("div", { class: "acoes acoes--intro" },
        h("button", { type: "button", class: "btn btn--prim btn--grande", id: "btn-comecar", onclick: function () { rastrear("scenario_start", { device: dispositivo(), origin: ORIGEM.originCta, productHint: ORIGEM.productHint || undefined }); ir(1); } }, "Começar"),
        h("p", { class: "aviso-curto", texto: "Não envie dados pessoais sensíveis, segredos comerciais ou documentos confidenciais nesta etapa." })));
  }

  function telaEtapa1() {
    var r = estado.r;
    var corpo = grupo("entryPath", "Qual situação melhor descreve o que você precisa agora?", null,
      opcoes("entryPath", "single", R.ENTRADAS, r.entryPath, 1, function (v) {
        if (r.entryPath !== v) { r.entryPath = v; r.branch = {}; ["stage", "issues", "consequences", "decisionHorizon", "narrative"].forEach(function (k) { delete r[k]; }); }
        delete estado.erros.entryPath; salvar();
        rastrear("scenario_branch_selected", { branch: v });
      }), estado.erros.entryPath);
    return moldura(1, "Situação reconhecida", "Escolha a opção mais próxima. Se nenhuma servir, use a última.", corpo, botoes(1, "Continuar", function () { avancar(1); }));
  }

  function telaEtapa2() {
    var r = estado.r;
    var c1 = grupo("audienceContext", "Em qual contexto esse cenário acontece?", null,
      opcoes("audienceContext", "single", R.CONTEXTOS, r.audienceContext, 1, function (v) { r.audienceContext = v; delete estado.erros.audienceContext; salvar(); }), estado.erros.audienceContext);
    var c2 = grupo("decisionRole", "Qual é o seu papel nessa decisão?", "Isso ajuda a entender com quem a conversa deve acontecer. Não é uma avaliação de cargo.",
      opcoes("decisionRole", "single", R.PAPEIS, r.decisionRole, 1, function (v) { r.decisionRole = v; delete estado.erros.decisionRole; salvar(); }), estado.erros.decisionRole);
    return moldura(2, "Contexto e relação com a decisão", null, h("div", { class: "grupos" }, c1, c2), botoes(2, "Continuar", function () { avancar(2); }));
  }

  function telaEtapa3() {
    var r = estado.r;
    var perguntas = R.perguntasEtapa3(r);
    var corpo = h("div", { class: "grupos" });
    perguntas.forEach(function (p) {
      var id = p.id, erro = estado.erros[id], atual = R.obter(r, id);
      if (p.tipo === "note") { corpo.appendChild(h("p", { class: "nota", texto: p.texto })); return; }
      if (p.tipo === "single" || p.tipo === "multi") {
        corpo.appendChild(grupo(id, p.rotulo, p.ajuda, opcoes(id, p.tipo, p.opcoes, atual, p.max, function (v) {
          R.definir(r, id, v); delete estado.erros[id]; salvar();
          if (id === "branch.aiSituation") { render(true); }
        }), erro, p.obrigatorio));
      } else if (p.tipo === "select") {
        var sel = h("select", { id: "c-" + id, name: id, autocomplete: p.autocomplete || "off", "aria-invalid": erro ? "true" : null, "aria-required": "true",
          onchange: function (ev) { R.definir(r, id, ev.target.value); delete estado.erros[id]; salvar(); limparErroVisual(ev.target.closest(".campo")); } },
          h("option", { value: "", texto: "Selecione…" }));
        p.opcoes.forEach(function (o) { sel.appendChild(h("option", { value: o.v, selected: atual === o.v ? "selected" : null, texto: o.l })); });
        corpo.appendChild(h("div", { class: "campo" + (erro ? " campo--erro" : "") }, h("label", { for: "c-" + id, texto: p.rotulo }), sel, h("p", { class: "campo__erro", id: id + "-er", texto: erro || "" })));
      } else {
        corpo.appendChild(campoTexto(id, p.rotulo, { area: p.tipo === "area", max: p.max, ajuda: p.ajuda, valor: atual || "", autocomplete: p.autocomplete, obrigatorio: p.obrigatorio,
          aoMudar: function (v) { R.definir(r, id, v); delete estado.erros[id]; } }));
      }
    });
    return moldura(3, "Sobre o seu cenário", "As perguntas abaixo foram ajustadas à sua escolha.", corpo, botoes(3, "Continuar", function () { avancar(3); }));
  }

  function telaEtapa4() {
    var r = estado.r, c = r.contact;
    var empresarial = R.CONTEXTOS_EMPRESARIAIS.indexOf(r.audienceContext) >= 0;
    var corpo = h("div", { class: "grupos" });
    corpo.appendChild(campoTexto("contact.name", "Nome", { autocomplete: "name", obrigatorio: true, max: 120, valor: c.name, aoMudar: function (v) { c.name = v; delete estado.erros["contact.name"]; } }));
    corpo.appendChild(campoTexto("contact.organization", "Empresa ou organização", { autocomplete: "organization", max: 120, valor: c.organization, obrigatorio: empresarial,
      ajuda: empresarial ? "Ajuda a CRIVIA a entender o contexto contratual da conversa." : "Opcional para pessoa física.", aoMudar: function (v) { c.organization = v; delete estado.erros["contact.organization"]; } }));
    corpo.appendChild(grupo("contact.preferredChannel", "Como você prefere receber o retorno?", null,
      opcoes("contact.preferredChannel", "single", R.CANAIS, c.preferredChannel, 1, function (v) { c.preferredChannel = v; delete estado.erros["contact.preferredChannel"]; render(true); }), estado.erros["contact.preferredChannel"]));
    if (c.preferredChannel === "whatsapp" || c.preferredChannel === "phone_call") {
      corpo.appendChild(campoTexto("contact.phone", c.preferredChannel === "whatsapp" ? "WhatsApp (com DDD)" : "Telefone (com DDD)", { tipo: "tel", inputmode: "tel", autocomplete: "tel", obrigatorio: true, max: 25, valor: c.phone,
        ajuda: "Pode ser número brasileiro ou internacional (com +).",
        aoMudar: function (v) { c.phone = v; delete estado.erros["contact.phone"]; }, aoSair: function (el) { var n = R.normalizarTelefone(el.value); if (n && n.indexOf("+55") === 0 && n.length >= 13) { var d = n.slice(3); el.value = "(" + d.slice(0, 2) + ") " + (d.length === 11 ? d.slice(2, 7) + "-" + d.slice(7) : d.slice(2, 6) + "-" + d.slice(6)); c.phone = el.value; } } }));
    }
    if (c.preferredChannel === "email") {
      corpo.appendChild(campoTexto("contact.email", "E-mail", { tipo: "email", inputmode: "email", autocomplete: "email", obrigatorio: true, max: 254, valor: c.email,
        aoMudar: function (v) { c.email = v; delete estado.erros["contact.email"]; } }));
    }
    // segundo canal (opcional)
    var tipo2 = c.secondChannel || "";
    var sel2 = h("select", { id: "c-contact.secondChannel", name: "secondChannel", onchange: function (ev) { c.secondChannel = ev.target.value; c.secondValue = ""; render(true); } },
      h("option", { value: "", texto: "Não quero informar" }));
    R.CANAIS.filter(function (o) { return o.v !== c.preferredChannel; }).forEach(function (o) { sel2.appendChild(h("option", { value: o.v, selected: tipo2 === o.v ? "selected" : null, texto: o.l })); });
    var seg = h("div", { class: "campo" }, h("label", { for: "c-contact.secondChannel" }, "Segundo canal", h("span", { class: "grupo__opcional", texto: " (opcional)" })), sel2);
    corpo.appendChild(seg);
    if (tipo2) corpo.appendChild(campoTexto("contact.secondValue", tipo2 === "email" ? "E-mail alternativo" : "Telefone alternativo", { tipo: tipo2 === "email" ? "email" : "tel", inputmode: tipo2 === "email" ? "email" : "tel", max: 254, valor: c.secondValue,
      aoMudar: function (v) { c.secondValue = v; delete estado.erros["contact.secondValue"]; } }));
    corpo.appendChild(grupo("contact.preferredContactPeriod", "Melhor período para contato", "É uma preferência; não representa compromisso de horário.",
      opcoes("contact.preferredContactPeriod", "single", R.PERIODOS, c.preferredContactPeriod, 1, function (v) { c.preferredContactPeriod = v; }), null, false));
    corpo.appendChild(campoTexto("contact.roleTitle", "Cargo", { autocomplete: "organization-title", max: 80, obrigatorio: false, valor: c.roleTitle, aoMudar: function (v) { c.roleTitle = v; } }));
    // armadilha de robô acessível: fora da tela, ignorada por leitores de tela e teclado
    corpo.appendChild(h("div", { class: "armadilha", "aria-hidden": "true" }, h("label", null, "Não preencha este campo", h("input", { type: "text", name: "website", id: "campo-website", tabindex: "-1", autocomplete: "off" }))));

    var privacidade = h("div", { class: "privacidade" },
      h("p", null, "A CRIVIA usará as informações enviadas para compreender seu cenário, avaliar a aderência da demanda e responder pelo canal escolhido. Não use este formulário para enviar dados pessoais sensíveis, informações sigilosas ou documentos confidenciais. Consulte o ",
        h("a", { href: CFG.privacyNoticeUrl, target: "_blank", rel: "noopener", texto: "Aviso de Privacidade" }), "."));
    var erroEnvio = estado.erroEnvio ? h("p", { class: "erro-envio", role: "alert", texto: estado.erroEnvio }) : null;
    var rodape = h("div", null, privacidade, erroEnvio,
      botoes(4, estado.enviando ? "Enviando com segurança…" : "Enviar meu cenário", enviar),
      h("p", { class: "ciencia", texto: "Ao enviar, confirmo que li o Aviso de Privacidade e solicito que a CRIVIA entre em contato pelo canal escolhido." }));
    return moldura(4, "Como você prefere receber o retorno?", "Só pedimos o necessário para responder.", corpo, rodape);
  }

  function telaSucesso() {
    var res = estado.resultado || {};
    var cont = h("div", { class: "etapa etapa--ok" },
      h("p", { class: "etiqueta etiqueta--ok" }, h("i"), "Enviado"),
      h("h1", { class: "etapa__titulo etapa__titulo--grande", tabindex: "-1", id: "titulo-etapa", texto: "Seu cenário foi registrado." }),
      h("p", { class: "etapa__desc", texto: "A CRIVIA recebeu as informações essenciais. O envio não constitui diagnóstico, proposta, contratação ou compromisso de atendimento. O próximo passo será definido após a análise inicial." }),
      h("div", { class: "pos-acoes" },
        h("button", { type: "button", class: "btn btn--sec", id: "btn-detalhes", "aria-expanded": res.detalhesAbertos ? "true" : "false", onclick: function () { res.detalhesAbertos = !res.detalhesAbertos; render(); document.getElementById("btn-detalhes").focus(); } }, "Quero acrescentar informações"),
        CFG.secureUploadEnabled ? h("button", { type: "button", class: "btn btn--sec", id: "btn-upload" }, "Enviar documentos com segurança") : null,
        CFG.agendaUrl ? h("button", { type: "button", class: "btn btn--prim", id: "btn-agenda", onclick: function () { rastrear("scenario_schedule_view", {}); window.open(CFG.agendaUrl, "_blank", "noopener,noreferrer"); } }, "Agendar conversa inicial de enquadramento") : null));
    if (res.detalhesOk) {
      cont.appendChild(h("div", { class: "detalhes" },
        h("p", { class: "detalhes__ok", role: "status", texto: "Informações adicionais registradas. Obrigado." })));
    } else if (res.detalhesAbertos) {
      cont.appendChild(h("div", { class: "detalhes" },
        campoTexto("additionalInfo", "O que mais ajudaria a conversa inicial?", { area: true, max: 700, valor: res.adicional || "", obrigatorio: false,
          ajuda: "Etapa opcional. Não inclua dados pessoais sensíveis, segredos comerciais ou documentos confidenciais.", aoMudar: function (v) { res.adicional = v; res.erroDetalhes = ""; } }),
        res.erroDetalhes ? h("p", { class: "erro-envio", role: "alert", texto: res.erroDetalhes }) : null,
        h("button", { type: "button", class: "btn btn--prim", onclick: enviarDetalhes, disabled: res.enviandoDetalhes ? "disabled" : null }, res.enviandoDetalhes ? "Enviando…" : "Enviar informações adicionais")));
    }
    cont.appendChild(h("div", { class: "pos-volta" },
      h("a", { class: "btn btn--prim", id: "btn-voltar-hero", href: CFG.voltarAoSiteUrl || "index.html", texto: "Voltar ao início do site" })));
    if (CFG.contactEmail) {
      cont.appendChild(h("p", { class: "ciencia" }, "Precisa acrescentar uma informação essencial? Escreva para ",
        h("a", { href: "mailto:" + CFG.contactEmail + "?subject=" + encodeURIComponent("Contato pelo site — Apresentar meu cenário"), texto: CFG.contactEmail }),
        " e informe o código do seu cenário", res.publicCode ? " (" : "", res.publicCode ? h("strong", { texto: res.publicCode }) : "", res.publicCode ? ")" : "",
        ". Não envie dados pessoais sensíveis ou documentos sigilosos por e-mail; a CRIVIA indicará o canal adequado quando necessário."));
    }
    cont.appendChild(h("p", { class: "ciencia", texto: "Você pode fechar esta página. Se precisar corrigir algo, responda ao contato que a CRIVIA fizer." }));
    return cont;
  }

  // ── fluxo ───────────────────────────────────────────────────────────────────────────────────────
  function render(manterPosicao) {
    var y = window.scrollY;
    var foco = document.activeElement && document.activeElement.id;
    app.textContent = "";
    var tela = estado.resultado ? telaSucesso() : [telaIntro, telaEtapa1, telaEtapa2, telaEtapa3, telaEtapa4][estado.etapa]();
    app.appendChild(tela);
    var apoio = document.querySelector(".apoio"); if (apoio) apoio.hidden = !!estado.resultado;   // depois do envio, o painel "Antes de começar" não faz mais sentido
    if (manterPosicao) {
      window.scrollTo(0, y);
      var el = foco && document.getElementById(foco);
      if (el) { try { el.focus({ preventScroll: true }); } catch (e) { el.focus(); } }
    } else {
      var t = document.getElementById("titulo-etapa");
      if (t) { t.focus({ preventScroll: true }); }
      window.scrollTo({ top: 0 });
    }
    var resumo = document.getElementById("resumo-erros");
    if (resumo && !manterPosicao) resumo.focus();
  }

  function ir(n) { estado.etapa = n; estado.erros = {}; estado.erroEnvio = ""; salvar(); render(); anunciar(n === 0 ? "" : "Etapa " + n + " de 4"); }

  function avancar(n) {
    var e = R.validarEtapa(n, estado.r);
    if (Object.keys(e).length) {
      estado.erros = e; render();
      rastrear("scenario_validation_error", { step: n, errorType: "required" });
      var alvo = document.getElementById("resumo-erros"); if (alvo) alvo.focus();
      return;
    }
    rastrear("scenario_step_complete", { step: n, branch: estado.r.entryPath });
    ir(n + 1);
  }

  var MSG_FALHA = "Não foi possível enviar seu cenário agora. Suas respostas permanecem nesta página. Tente novamente" + (CFG.contactEmail ? " ou entre em contato pelo e-mail " + CFG.contactEmail : "") + ".";

  // Protocolo: POST com corpo JSON enviado como text/plain (requisição "simples": o Google Apps Script não responde a preflight CORS).
  // Nenhum dado pessoal vai na URL; a resposta é sempre JSON {ok, ...}. O servidor local de testes fala o mesmo protocolo.
  function chamar(acao, dados) {
    var ctl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = ctl ? setTimeout(function () { ctl.abort(); }, 20000) : null;
    return fetch(String(CFG.endpoint || ""), { method: "POST", headers: { "Content-Type": "text/plain;charset=utf-8" }, body: JSON.stringify({ action: acao, data: dados }),
      credentials: "omit", mode: "cors", redirect: "follow", referrerPolicy: "no-referrer", signal: ctl ? ctl.signal : undefined })
      .then(function (resp) { if (timer) clearTimeout(timer); return resp.json().catch(function () { return { ok: false }; }).then(function (j) { return { status: resp.status, json: j || {} }; }); });
  }

  function enviar() {
    if (estado.enviando) return;
    // revalida tudo antes de enviar; se algo anterior estiver inválido, volta para a etapa correspondente
    for (var n = 1; n <= 4; n++) {
      var e = R.validarEtapa(n, estado.r);
      if (Object.keys(e).length) { estado.etapa = n; estado.erros = e; render(); var a = document.getElementById("resumo-erros"); if (a) a.focus(); return; }
    }
    if (!CFG.endpoint || CFG.endpoint.indexOf("__CRIVIA") === 0) {
      estado.erroEnvio = MSG_FALHA; render(true); return;
    }
    estado.enviando = true; estado.erroEnvio = ""; render(true);
    estado.idem = estado.idem || (window.crypto && crypto.randomUUID ? crypto.randomUUID() : (Date.now().toString(36) + Math.random().toString(36).slice(2) + "00000000"));
    var hp = document.getElementById("campo-website");
    var ref = ""; try { ref = document.referrer ? new URL(document.referrer).hostname : ""; } catch (x) { ref = ""; }
    var payload = R.montarPayload(estado.r, ORIGEM, { idempotencyKey: estado.idem, deviceCategory: dispositivo(), referrer: ref, privacyNoticeVersion: CFG.privacyNoticeVersion, honeypot: hp ? hp.value : "" });
    chamar("submit", payload).then(function (res) {
      estado.enviando = false;
      if (res.json.ok === true) {
        estado.resultado = { id: res.json.publicCode || res.json.id, publicCode: res.json.publicCode || "", token: res.json.detailsToken || "" };
        limparArmazenamento(); estado.r = { contact: {}, branch: {} };
        rastrear("scenario_submit_success", { duration: Math.round((Date.now() - inicio) / 10000) * 10 });
        render(); anunciar("Seu cenário foi registrado.");
      } else if (res.json.error === "validation" && res.json.fields) {
        var e2 = {};
        Object.keys(res.json.fields).forEach(function (k) { if (/^contact\./.test(k)) e2[k] = "Confira este campo."; });
        estado.erros = e2; estado.erroEnvio = Object.keys(e2).length ? "" : "Algumas respostas não foram aceitas. Volte e revise as etapas anteriores.";
        rastrear("scenario_submit_error", { errorType: "validation" }); render();
      } else {
        estado.erroEnvio = MSG_FALHA; rastrear("scenario_submit_error", { errorType: res.json.error === "rate" ? "rate" : "server" }); render(true);
      }
    }).catch(function () {
      estado.enviando = false; estado.erroEnvio = MSG_FALHA; rastrear("scenario_submit_error", { errorType: "network" }); render(true);
    });
  }

  function enviarDetalhes() {
    var res = estado.resultado; if (!res || res.enviandoDetalhes) return;
    var texto = (res.adicional || "").trim();
    if (texto.length < 5) { res.erroDetalhes = "Escreva ao menos 5 caracteres."; render(true); return; }
    res.enviandoDetalhes = true; res.erroDetalhes = ""; render(true);
    rastrear("scenario_details_started", {});
    chamar("details", { leadRef: res.id, token: res.token, additionalInfo: texto }).then(function (r) {
      res.enviandoDetalhes = false;
      if (r.json.ok === true) { res.detalhesOk = true; res.adicional = ""; rastrear("scenario_details_completed", {}); } else res.erroDetalhes = MSG_FALHA;
      render(true);
    }).catch(function () { res.enviandoDetalhes = false; res.erroDetalhes = MSG_FALHA; render(true); });
  }

  // ── início ────────────────────────────────────────────────────────────────────────────────────
  restaurar();
  if (estado.etapa > 0 && !estado.r.entryPath) estado.etapa = 0;
  render();
  rastrear("scenario_view", { device: dispositivo(), origin: ORIGEM.originCta, productHint: ORIGEM.productHint || undefined });
})();
