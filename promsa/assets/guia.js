/* Guía animado del portal PROMSA: la Casita saludable, con un gesto por sección (saluda, abraza, megáfono, gráfico, árbol, calendario).
   Se puede ocultar; se recuerda la elección. En Inicio aparece dentro de la portada y baja a la esquina al desplazarse. */
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";
  var CLAVE = "guia-promsa-oculto";
  function sv(t, a, p) { var e = document.createElementNS(NS, t); for (var k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; }
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function cara(g, x, y, sep, r, colorOjo, boca) {
    [x - sep, x + sep].forEach(function (cx) {
      sv("circle", { cx: cx, cy: y, r: r, fill: "#fff" }, g);
      var pu = sv("g", { class: "gu-pupila" }, g); sv("circle", { cx: cx, cy: y + 1, r: r * .55, fill: colorOjo || "#10202a" }, pu); sv("circle", { cx: cx + r * .25, cy: y - r * .25, r: r * .2, fill: "#fff" }, pu);
      sv("circle", { cx: cx, cy: y, r: r + .5, class: "gu-parpado", style: "transform-origin:" + cx + "px " + (y - r) + "px" }, g);
    });
    if (boca !== false) sv("path", { d: boca || ("M" + (x - 9) + " " + (y + 15) + " Q" + x + " " + (y + 24) + " " + (x + 9) + " " + (y + 15)), fill: "none", stroke: "#10202a", "stroke-width": 3.5, "stroke-linecap": "round" }, g);
    sv("ellipse", { cx: x - sep - 4, cy: y + 13, rx: 6, ry: 3.5, fill: "#ff8a8a", opacity: ".5" }, g); sv("ellipse", { cx: x + sep + 4, cy: y + 13, rx: 6, ry: 3.5, fill: "#ff8a8a", opacity: ".5" }, g);
  }

  // ---------- Personaje: Casita saludable ----------
  function casita() {
    var s = sv("svg", { viewBox: "0 0 200 200", class: "gu-svg gu-casita", "aria-hidden": "true" });
    sv("ellipse", { cx: 100, cy: 188, rx: 58, ry: 7, fill: "#7a5f12", opacity: ".15" }, s);
    var hu = sv("g", { class: "gu-humo" }, s); sv("path", { d: "M140 34 C140 28 148 27 149 32 C150 27 158 28 158 34 C158 40 149 44 149 48 C149 44 140 40 140 34Z", fill: "#e5484d" }, hu);
    var G = sv("g", { class: "gu-cuerpo" }, s);
    sv("rect", { x: 132, y: 46, width: 16, height: 26, rx: 2, fill: "#b5651d", stroke: "#7a3f12", "stroke-width": 3 }, G);
    sv("path", { d: "M46 98 L46 176 Q46 182 52 182 L148 182 Q154 182 154 176 L154 98", fill: "#fff3d6", stroke: "#a17f1a", "stroke-width": 4, "stroke-linejoin": "round" }, G);
    sv("path", { d: "M30 104 L100 44 L170 104", fill: "none", stroke: "#c0392b", "stroke-width": 14, "stroke-linecap": "round", "stroke-linejoin": "round" }, G);
    sv("path", { d: "M58 82 L100 46 L142 82", fill: "none", stroke: "#e35d4f", "stroke-width": 4, "stroke-linecap": "round", opacity: ".6" }, G);
    sv("rect", { x: 86, y: 146, width: 28, height: 36, rx: 12, fill: "#2e9e5b", stroke: "#1f7a43", "stroke-width": 3 }, G);
    sv("circle", { cx: 108, cy: 166, r: 2.6, fill: "#fde68a" }, G);
    sv("path", { d: "M56 160 q6 -10 12 0 q6 -10 12 0", fill: "#4cbf72" }, G); sv("path", { d: "M122 160 q6 -10 12 0 q6 -10 12 0", fill: "#4cbf72" }, G);
    cara(G, 100, 112, 22, 11, "#3a2a06");
    var bi = sv("g", { class: "gu-brazo gu-brazo-i" }, G); sv("path", { d: "M46 128 Q28 136 24 152", fill: "none", stroke: "#a17f1a", "stroke-width": 7, "stroke-linecap": "round" }, bi); sv("circle", { cx: 23, cy: 154, r: 7, fill: "#fff", stroke: "#a17f1a", "stroke-width": 3 }, bi);
    var bd = sv("g", { class: "gu-brazo gu-brazo-d" }, G); sv("path", { d: "M154 128 Q172 136 176 152", fill: "none", stroke: "#a17f1a", "stroke-width": 7, "stroke-linecap": "round" }, bd); sv("circle", { cx: 177, cy: 154, r: 7, fill: "#fff", stroke: "#a17f1a", "stroke-width": 3 }, bd);
    // Megáfono (actividades)
    var me = sv("g", { class: "gu-megafono" }, bd); sv("path", { d: "M170 150 L196 136 L196 170 Z", fill: "#e3b11c", stroke: "#a17f1a", "stroke-width": 3, "stroke-linejoin": "round" }, me); sv("path", { d: "M202 140 q8 13 0 26", fill: "none", stroke: "#a17f1a", "stroke-width": 3, "stroke-linecap": "round", class: "gu-ondas2" }, me);
    // Gráfico de barras (avance)
    var gr = sv("g", { class: "gu-grafico" }, s); sv("rect", { x: 160, y: 96, width: 36, height: 40, rx: 4, fill: "#fff", stroke: "#a17f1a", "stroke-width": 2.5 }, gr);
    [[166, 124, 12], [175, 116, 20], [184, 106, 30]].forEach(function (b, i) { sv("rect", { x: b[0], y: b[1], width: 7, height: b[2] - 0, rx: 1.5, fill: ["#e0802e", "#2e9e5b", "#2f7fc1"][i], class: "gu-barra" }, gr); });
    // Árbol (escenarios)
    var ar = sv("g", { class: "gu-arbol" }, s); sv("rect", { x: 12, y: 150, width: 6, height: 30, fill: "#7a3f12" }, ar); sv("circle", { cx: 15, cy: 140, r: 16, fill: "#2e9e5b" }, ar); sv("circle", { cx: 8, cy: 134, r: 7, fill: "#4cbf72" }, ar);
    // Calendario (plan anual)
    var ca = sv("g", { class: "gu-calendario" }, s); sv("rect", { x: 160, y: 92, width: 34, height: 34, rx: 4, fill: "#fff", stroke: "#a17f1a", "stroke-width": 2.5 }, ca); sv("rect", { x: 160, y: 92, width: 34, height: 9, rx: 3, fill: "#c0392b" }, ca); sv("path", { d: "M167 113 l5 5 l10 -10", fill: "none", stroke: "#2e9e5b", "stroke-width": 3.5, "stroke-linecap": "round", "stroke-linejoin": "round" }, ca);
    var on = sv("g", { class: "gu-ondas" }, s); sv("path", { d: "M184 64 Q192 72 186 84 M192 56 Q204 72 194 90", fill: "none", stroke: "#2e9e5b", "stroke-width": 3, "stroke-linecap": "round" }, on);
    return s;
  }
  var PJ = { casita: casita };
  var MSJ = {
    inicio: ["casita", "saludo", "¡Hola! Bienvenido al portal de Promoción de la Salud de la Red de Salud Chachapoyas."],
    nosotros: ["casita", "abraza", "Promovemos familias, escuelas, municipios y comunidades saludables."],
    avance: ["casita", "grafico", "Mira cómo avanza cada microred en sus metas de promoción de la salud."],
    actividades: ["casita", "megafono", "Campañas, ferias y sesiones: así llevamos la salud a tu comunidad."],
    escenarios: ["casita", "arbol", "Municipios, escuelas y comunidades que trabajan por su salud."],
    plan: ["casita", "calendario", "Nuestro plan del año, mes a mes."]
  };

  function montar() {
    if (document.getElementById("guia-promsa")) return;
    var oculto = false; try { oculto = localStorage.getItem(CLAVE) === "1"; } catch (e) { }
    var raiz = el("div", "guia"); raiz.id = "guia-promsa";
    var globo = el("div", "gu-globo"); globo.setAttribute("role", "status"); globo.setAttribute("aria-live", "polite");
    var txt = el("p"); globo.appendChild(txt);
    var cerrar = el("button", "gu-cerrar", "×"); cerrar.type = "button"; cerrar.setAttribute("aria-label", "Ocultar al guía"); globo.appendChild(cerrar);
    var fig = el("button", "gu-fig"); fig.type = "button"; fig.setAttribute("aria-label", "Guía de Promoción de la Salud: mostrar mensaje");
    var cache = {}; Object.keys(PJ).forEach(function (k) { cache[k] = PJ[k](); cache[k].style.display = "none"; fig.appendChild(cache[k]); });
    raiz.appendChild(globo); raiz.appendChild(fig);
    var volver = el("button", "gu-volver"); volver.type = "button"; volver.setAttribute("aria-label", "Mostrar al guía"); volver.title = "Mostrar al guía";
    volver.appendChild(casita());
    var heroIn = document.querySelector(".phero-in"), hero = document.querySelector(".phero"), heroVisible = true;
    // Portada (Inicio): arriba, dentro de la barra del portal; al bajar y salir la barra de la pantalla, pasa a la
    // esquina inferior derecha para no perderse, y vuelve a la barra al subir. Demás pestañas: abajo a la derecha, fijo.
    function esInicio() { var h = (location.hash || "").slice(1); return !h || h === "inicio"; }
    function ubicar() {
      var arriba = esInicio() && !!heroIn && heroVisible, antes = raiz.classList.contains("en-hero");
      [raiz, volver].forEach(function (n) {
        var dest = arriba ? heroIn : document.body;
        if (n.parentNode !== dest) dest.appendChild(n);
        n.classList.toggle("en-hero", arriba);
      });
      if (esInicio() && antes !== arriba && !raiz.hidden) { raiz.classList.remove("baja", "sube"); void raiz.offsetWidth; raiz.classList.add(arriba ? "sube" : "baja"); }
    }
    if (hero && "IntersectionObserver" in window) new IntersectionObserver(function (en) { heroVisible = en[0].isIntersecting; ubicar(); }, { threshold: 0.15 }).observe(hero);
    ubicar();
    window.addEventListener("hashchange", ubicar);
    var t = null, actual = null;
    function decir(m) { txt.textContent = m; raiz.classList.add("habla"); clearTimeout(t); t = setTimeout(function () { raiz.classList.remove("habla"); }, 8500); }
    function clave() {
      var id = (location.hash || "#inicio").slice(1) || "inicio";
      return MSJ[id] ? id : "inicio";
    }
    function pose() {
      var k = clave(); if (k === actual) return; actual = k;
      var m = MSJ[k];
      Object.keys(cache).forEach(function (n) { cache[n].style.display = n === m[0] ? "" : "none"; });
      raiz.setAttribute("data-pj", m[0]); raiz.setAttribute("data-pose", m[1]);
      raiz.classList.remove("entra"); void raiz.offsetWidth; raiz.classList.add("entra");
      decir(m[2]);
    }
    function mostrar(v) { raiz.hidden = !v; volver.hidden = v; try { localStorage.setItem(CLAVE, v ? "0" : "1"); } catch (e) { } if (v) { actual = null; pose(); } }
    cerrar.addEventListener("click", function () { mostrar(false); });
    volver.addEventListener("click", function () { mostrar(true); });
    fig.addEventListener("click", function () { if (raiz.classList.contains("habla")) raiz.classList.remove("habla"); else decir(MSJ[actual || "inicio"][2]); raiz.classList.remove("salta"); void raiz.offsetWidth; raiz.classList.add("salta"); });
    window.addEventListener("hashchange", function () { if (!raiz.hidden) pose(); });
    raiz.hidden = oculto; volver.hidden = !oculto;
    if (!oculto) setTimeout(pose, 500);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", montar); else montar();
})();
