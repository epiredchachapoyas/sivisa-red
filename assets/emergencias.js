/* SIVISA – vista "Emergencias sanitarias" (window.VISTAS.emergencias).
   Lee window.EMERGENCIAS (promsa/herramientas/preparar_promsa.py, hojas Emergencias*, de PROMSA_portal.xlsx):
   ficha de la emergencia, avance acumulado frente a la meta, avance por mes, por microred y actividades vinculadas. */
(function () {
  var MESL = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"];
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function n(v) { return v == null ? "–" : Number(v).toLocaleString("es-PE"); }
  function f(iso) { var p = String(iso || "").split("-"); return p.length === 3 ? p[2] + "/" + p[1] + "/" + p[0] : "–"; }
  function mesTxt(m) { var s = MESL[+m.slice(5) - 1] || m; return s.charAt(0).toUpperCase() + s.slice(1) + " " + m.slice(0, 4); }
  function mr(s) { return String(s || "").toLowerCase().replace(/(^|\s)\S/g, function (m) { return m.toUpperCase(); }); }
  function nivel(p) { return p == null ? "" : p >= 85 ? "ok" : p >= 50 ? "medio" : "bajo"; }
  function fp(p) { return (Math.round(p * 10) / 10).toLocaleString("es-PE") + " %"; }

  function tabla(cont, titulo, primera, filas, inds, fmt) {
    if (!filas.length) return;
    cont.appendChild(el("h3", "pl-sub", titulo));
    var w = el("div", "em-tab-w"), t = el("table", "em-tab"), h = el("tr");
    h.appendChild(el("th", null, primera)); inds.forEach(function (i) { h.appendChild(el("th", "c", i.indicador)); });
    var th = el("thead"); th.appendChild(h); t.appendChild(th);
    var tb = el("tbody"), tot = {};
    filas.forEach(function (r) {
      var tr = el("tr"); tr.appendChild(el("td", "b", fmt(r)));
      inds.forEach(function (i) { var v = r.valores[i.indicador]; if (v != null) tot[i.indicador] = (tot[i.indicador] || 0) + v; tr.appendChild(el("td", "c", v == null ? "–" : n(v))); });
      tb.appendChild(tr);
    });
    if (filas.length > 1) { var tr = el("tr", "tot"); tr.appendChild(el("td", null, "Total")); inds.forEach(function (i) { tr.appendChild(el("td", "c", tot[i.indicador] == null ? "–" : n(tot[i.indicador]))); }); tb.appendChild(tr); }
    t.appendChild(tb); w.appendChild(t); cont.appendChild(w);
  }

  function ficha(cont, e) {
    var cerrada = /cerrad/i.test(e.estado);
    var c = el("section", "em-ficha" + (cerrada ? " cerrada" : ""));
    c.appendChild(el("h3", null, e.nombre));
    var m = el("div", "em-meta"); m.appendChild(el("span", "em-estado" + (cerrada ? " cerrada" : ""), e.estado));
    function d(l, v) { if (!v) return; var s = el("span"); s.appendChild(el("b", null, l + ": ")); s.appendChild(document.createTextNode(v)); m.appendChild(s); }
    d("Inicio", e.inicio ? f(e.inicio) : ""); d("Fin", e.fin ? f(e.fin) : ""); d("Ámbito", e.ambito);
    c.appendChild(m);
    if (e.objetivo) { var p = el("p"); p.appendChild(el("b", null, "Objetivo general: ")); p.appendChild(document.createTextNode(e.objetivo)); c.appendChild(p); }
    if (e.contexto) c.appendChild(el("p", null, e.contexto));
    cont.appendChild(c);

    if (e.indicadores.length) {
      cont.appendChild(el("h3", "pl-sub", "Avance acumulado de los indicadores"));
      var g = el("div", "em-inds");
      e.indicadores.forEach(function (i) {
        var k = el("div", "em-ind");
        if (i.componente) k.appendChild(el("small", "comp", i.componente));
        k.appendChild(el("strong", null, i.indicador));
        var v = el("div", "v", n(i.avance)); if (i.meta) v.appendChild(el("span", null, " de " + n(i.meta) + " " + (i.unidad || ""))); else if (i.unidad) v.appendChild(el("span", null, " " + i.unidad)); k.appendChild(v);
        if (i.meta) {
          var pc = i.avance / i.meta * 100, b = el("div", "em-bar"), x = el("i", nivel(pc)); x.style.width = Math.min(pc, 100) + "%"; b.appendChild(x); k.appendChild(b);
          k.appendChild(el("span", "pc", fp(pc) + " de la meta"));
        } else k.appendChild(el("span", "pc", "Sin meta: se reporta el avance"));
        g.appendChild(k);
      });
      cont.appendChild(g);
    }
    if (!e.meses.length) cont.appendChild(el("div", "ac-vacio", "Aún no se registra avance mensual de esta emergencia."));
    tabla(cont, "Avance por mes", "Mes", e.meses, e.indicadores, function (r) { return mesTxt(r.mes); });
    tabla(cont, "Avance por microred (acumulado)", "Microred", e.microredes, e.indicadores, function (r) { return mr(r.microred); });
    if (window.Actividades && (window.ACTIVIDADES || {}).actividades) {
      var A = window.ACTIVIDADES.actividades.filter(function (a) { return a.emergencia === e.nombre; });
      if (A.length) { cont.appendChild(el("h3", "pl-sub", "Actividades vinculadas")); var z = el("div"); cont.appendChild(z); Actividades.vista(z, null, null, { filtro: { emergencia: e.nombre }, sinIntro: true }); }
    }
    cont.appendChild(el("p", "ac-nota", "Fuente: registro mensual de avance del equipo técnico, según los indicadores y metas del plan de la emergencia." +
      ((window.EMERGENCIAS || {}).actualizado ? " Actualizado: " + f(window.EMERGENCIAS.actualizado) + "." : "")));
  }

  function vista(cont, sec) {
    cont.innerHTML = ""; var E = ((window.EMERGENCIAS || {}).emergencias) || [];
    if (!E.length) { var v = el("div", "ac-vacio"); v.appendChild(el("strong", null, "No hay emergencias sanitarias registradas")); cont.appendChild(v); return; }
    var sel = el("div", "em-sel"), cuerpo = el("div");
    if (E.length > 1) cont.appendChild(sel);
    cont.appendChild(cuerpo);
    function abrir(i) {
      sel.querySelectorAll(".em-chip").forEach(function (b, j) { b.classList.toggle("sel", i === j); });
      cuerpo.innerHTML = ""; ficha(cuerpo, E[i]);
    }
    E.forEach(function (e, i) {
      var b = el("button", "em-chip"); b.type = "button"; var d = el("i", /cerrad/i.test(e.estado) ? "" : "activa"); b.appendChild(d); b.appendChild(document.createTextNode(e.nombre));
      b.addEventListener("click", function () { abrir(i); }); sel.appendChild(b);
    });
    abrir(0);
  }
  window.VISTAS = window.VISTAS || {};
  window.VISTAS.emergencias = vista;
})();
