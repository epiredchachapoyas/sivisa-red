/* Portal PROMSA – vistas propias: avance de metas, actividades, escenarios saludables y plan anual.
   Datos: window.PROMSA (data/promsa.js, generado por herramientas/preparar_promsa.py desde PROMSA_portal.xlsx y el reporte HIS). */
(function () {
  "use strict";
  var MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"];
  var MESL = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"];
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function n(v) { return v == null ? "–" : Number(v).toLocaleString("es-PE"); }
  function f(iso) { var p = String(iso || "").split("-"); return p.length === 3 ? p[2] + "/" + p[1] + "/" + p[0] : "–"; }
  function cap(s) { s = String(s || ""); return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase(); }
  function mr(s) { return String(s || "").toLowerCase().replace(/(^|\s)\S/g, function (m) { return m.toUpperCase(); }); }
  function pct(a, b) { return b ? a / b * 100 : null; }
  function fp(p) { return p == null ? "N/D" : (Math.round(p * 10) / 10).toLocaleString("es-PE") + " %"; }
  function nivel(p) { return p == null ? "nd" : p >= 85 ? "ok" : p >= 50 ? "medio" : "bajo"; }
  function kpi(cont, v, l, s) { var k = el("div", "pr-kpi"); k.appendChild(el("strong", null, v)); k.appendChild(el("span", null, l)); if (s) k.appendChild(el("small", null, s)); cont.appendChild(k); }
  function vacio(cont, msg) { cont.appendChild(el("div", "empty", msg)); }
  function nota(cont, t) { cont.appendChild(el("p", "pr-nota", t)); }
  var D = function () { return window.PROMSA || null; };
  function fuente() { var P = D(); return P && P.his ? "Fuente: reporte HIS de actividades de promoción de la salud, del " + f(P.his.desde) + " al " + f(P.his.hasta) + "." : ""; }

  // ---------- Avance de metas por programa ----------
  function avance(cont) {
    cont.innerHTML = ""; var P = D();
    if (!P || !P.his) { vacio(cont, "Aún no se ha cargado el reporte HIS de promoción de la salud (carpeta promsa/datos/his)."); return; }
    var est = { prog: P.programas[0].id };
    var cab = el("div", "pr-cab"); cab.appendChild(el("span", "pr-pill", "Acumulado al " + f(P.his.hasta))); cab.appendChild(el("span", "pr-pill claro", "Meta física 2026 por microred")); cont.appendChild(cab);
    var g = el("div", "pr-progs"); cont.appendChild(g);
    P.programas.forEach(function (p) {
      var pc = p.comparable ? pct(p.produccion, p.meta) : null;
      var c = el("button", "pr-prog"); c.type = "button"; c.style.setProperty("--c", p.color); c.dataset.id = p.id;
      c.appendChild(el("span", "pr-prog-id", "PP " + p.id));
      c.appendChild(el("strong", null, p.nombre));
      var v = el("div", "pr-prog-v"); v.appendChild(el("b", null, n(p.produccion))); v.appendChild(el("span", null, p.unidad)); c.appendChild(v);
      var bar = el("div", "pr-bar"); var fi = el("i"); fi.style.width = Math.min(pc || 0, 100) + "%"; bar.appendChild(fi); c.appendChild(bar);
      c.appendChild(el("span", "pr-prog-m " + nivel(pc), p.comparable ? fp(pc) + " de la meta (" + n(p.meta) + ")" : "Meta " + n(p.meta) + " · % no comparable"));
      c.addEventListener("click", function () { est.prog = p.id; pintar(); det.scrollIntoView({ behavior: "smooth", block: "start" }); });
      g.appendChild(c);
    });
    nota(cont, "El porcentaje es administrativo: registros del HIS divididos entre la meta física, por cien. No equivale a cobertura de familias únicas (una familia puede recibir varias sesiones). En Desarrollo Infantil Temprano y Salud Mental no se calcula porque el reporte no permite saber cuántos niños completaron su esquema.");
    var det = el("section", "pr-det"); cont.appendChild(det);
    function pintar() {
      det.innerHTML = "";
      g.querySelectorAll(".pr-prog").forEach(function (b) { b.classList.toggle("sel", b.dataset.id === est.prog); });
      var p = P.programas.filter(function (x) { return x.id === est.prog; })[0];
      var h = el("div", "pr-det-h"); h.style.setProperty("--c", p.color); h.appendChild(el("h3", null, "PP " + p.id + " · " + p.nombre + ": producción por microred")); det.appendChild(h);
      var filas = P.microredes.map(function (m) { var pr = m.produccion[p.id] || 0, me = m.metas[p.id] || 0; return { nombre: m.nombre, prod: pr, meta: me, pc: p.comparable ? pct(pr, me) : null }; });
      filas.sort(function (a, b) { return p.comparable ? (b.pc || 0) - (a.pc || 0) : b.prod - a.prod; });
      var max = Math.max.apply(null, filas.map(function (x) { return p.comparable ? Math.min(x.pc || 0, 200) : x.prod; }).concat([1]));
      var lista = el("div", "pr-rank");
      filas.forEach(function (x, i) {
        var r = el("div", "pr-rank-f");
        r.appendChild(el("span", "pr-rank-n", i + 1)); r.appendChild(el("span", "pr-rank-t", mr(x.nombre)));
        var b = el("div", "pr-rank-b"); var fi = el("i", nivel(x.pc)); fi.style.width = ((p.comparable ? Math.min(x.pc || 0, 200) : x.prod) / max * 100) + "%"; if (!p.comparable) fi.style.background = p.color; b.appendChild(fi);
        if (p.comparable) { var m85 = el("em"); m85.style.left = (100 / max * 100) + "%"; m85.title = "Meta (100 %)"; b.appendChild(m85); }
        r.appendChild(b);
        r.appendChild(el("span", "pr-rank-v", p.comparable ? fp(x.pc) : n(x.prod)));
        r.appendChild(el("span", "pr-rank-d", n(x.prod) + " / " + n(x.meta)));
        lista.appendChild(r);
      });
      det.appendChild(lista);
      if (p.comparable) { var ley = el("div", "pr-ley"); [["ok", "85 % a más"], ["medio", "50 a 84 %"], ["bajo", "menos de 50 %"]].forEach(function (k) { var s = el("span"); s.appendChild(el("i", k[0])); s.appendChild(document.createTextNode(k[1])); ley.appendChild(s); }); var s2 = el("span"); s2.appendChild(el("i", "linea")); s2.appendChild(document.createTextNode("meta")); ley.appendChild(s2); det.appendChild(ley); }
      nota(det, "Unidad: " + p.unidad + ". Columna derecha: registros / meta física 2026." + (p.fuera_microred ? " Además, " + n(p.fuera_microred) + " registros de establecimientos sin microred asignada no figuran en el ranking." : "") + " " + fuente());
    }
    pintar();
  }

  // ---------- Actividades ----------
  function actividades(cont) {
    cont.innerHTML = ""; var P = D(); var A = (P && P.actividades) || [];
    if (!A.length) {
      var e = el("div", "pr-vacio"); e.appendChild(el("strong", null, "Aún no hay actividades registradas"));
      e.appendChild(el("p", null, "Aquí se mostrarán las campañas, ferias, sesiones masivas, perifoneo, capacitaciones y reuniones con municipios que registre la Unidad de Promoción de la Salud cada mes."));
      cont.appendChild(e); return;
    }
    var est = { tema: "", mr: "", mes: "" };
    var k = el("div", "pr-kpis"); cont.appendChild(k);
    var fl = el("div", "filters-panel pr-filtros"); cont.appendChild(fl);
    function sel(lbl, vals, key, fmt) {
      var w = el("div"); w.appendChild(el("label", null, lbl)); var s = el("select"); s.appendChild(new Option("Todos", ""));
      vals.forEach(function (v) { s.appendChild(new Option(fmt ? fmt(v) : v, v)); });
      s.addEventListener("change", function () { est[key] = s.value; pintar(); }); w.appendChild(s); fl.appendChild(w);
    }
    function uniq(fn) { var o = {}; A.forEach(function (a) { var v = fn(a); if (v) o[v] = 1; }); return Object.keys(o).sort(); }
    sel("Mes", uniq(function (a) { return a.fecha.slice(0, 7); }).reverse(), "mes", function (m) { return cap(MESL[+m.slice(5) - 1]) + " " + m.slice(0, 4); });
    sel("Tema", uniq(function (a) { return a.tema; }), "tema");
    sel("Microred", uniq(function (a) { return a.microred; }), "mr", mr);
    var lista = el("div", "pr-acts"); cont.appendChild(lista);
    function pintar() {
      var L = A.filter(function (a) { return (!est.tema || a.tema === est.tema) && (!est.mr || a.microred === est.mr) && (!est.mes || a.fecha.slice(0, 7) === est.mes); });
      k.innerHTML = "";
      kpi(k, n(L.length), L.length === 1 ? "actividad" : "actividades");
      kpi(k, n(L.reduce(function (s, a) { return s + a.participantes; }, 0)), "participantes");
      kpi(k, n(Object.keys(L.reduce(function (o, a) { if (a.microred) o[a.microred] = 1; return o; }, {})).length), "microredes");
      kpi(k, n(Object.keys(L.reduce(function (o, a) { if (a.tema) o[a.tema] = 1; return o; }, {})).length), "temas");
      lista.innerHTML = "";
      if (!L.length) { vacio(lista, "Ninguna actividad cumple el filtro."); return; }
      L.forEach(function (a) {
        var c = el("article", "pr-act" + (a.foto ? " con-foto" : ""));
        if (a.foto) { var im = el("img"); im.src = "fotos/" + encodeURIComponent(a.foto); im.alt = a.tipo + " – " + a.tema; im.loading = "lazy"; c.appendChild(im); }
        var b = el("div", "pr-act-b");
        var top = el("div", "pr-act-top"); top.appendChild(el("span", "pr-act-f", f(a.fecha))); if (a.tema) top.appendChild(el("span", "pr-tag", a.tema)); b.appendChild(top);
        b.appendChild(el("h4", null, a.tipo || "Actividad"));
        if (a.descripcion) b.appendChild(el("p", null, a.descripcion));
        var pie = [a.microred ? "Microred " + mr(a.microred) : "", a.distrito, a.escenario, a.participantes ? n(a.participantes) + " participantes" : ""].filter(Boolean).join(" · ");
        b.appendChild(el("small", null, pie)); c.appendChild(b); lista.appendChild(c);
      });
    }
    pintar();
  }

  // ---------- Escenarios saludables ----------
  function escenarios(cont) {
    cont.innerHTML = ""; var P = D(); var E = P && P.escenarios;
    var filas = E ? E.filas.filter(function (r) { return r.valores.some(function (v) { return v != null; }); }) : [];
    if (!filas.length) {
      var e = el("div", "pr-vacio"); e.appendChild(el("strong", null, "Información en preparación"));
      e.appendChild(el("p", null, "Aquí se mostrarán, por microred, los municipios con asistencia técnica, las instituciones educativas promotoras de la salud, las comunidades saludables y los agentes comunitarios de salud activos."));
      cont.appendChild(e); return;
    }
    var k = el("div", "pr-kpis"); cont.appendChild(k);
    E.columnas.forEach(function (c, j) { kpi(k, n(filas.reduce(function (s, r) { return s + (r.valores[j] || 0); }, 0)), c); });
    var w = el("div", "pr-tab-w"), t = el("table", "pr-tab"), th = el("tr"); th.appendChild(el("th", null, "Microred")); E.columnas.forEach(function (c) { th.appendChild(el("th", "c", c)); }); th.appendChild(el("th", null, "Observación"));
    var hd = el("thead"); hd.appendChild(th); t.appendChild(hd); var tb = el("tbody"); t.appendChild(tb);
    E.filas.forEach(function (r) { var tr = el("tr"); tr.appendChild(el("td", "b", mr(r.microred))); r.valores.forEach(function (v) { tr.appendChild(el("td", "c", n(v))); }); tr.appendChild(el("td", null, r.obs)); tb.appendChild(tr); });
    w.appendChild(t); cont.appendChild(w);
    nota(cont, "Acumulado del año" + (P.escenarios_corte ? " al " + f(P.escenarios_corte) : "") + ". Fuente: Unidad de Promoción de la Salud – RIS Chachapoyas.");
  }

  // ---------- Plan anual (cronograma) ----------
  function plan(cont) {
    cont.innerHTML = ""; var P = D(); var C = (P && P.cronograma) || [];
    if (!C.length) { vacio(cont, "Cronograma en preparación."); return; }
    var cuenta = { Ejecutado: 0, Programado: 0, Reprogramado: 0, "No ejecutado": 0 };
    C.forEach(function (c) { c.meses.forEach(function (m) { if (m in cuenta) cuenta[m]++; }); });
    var k = el("div", "pr-kpis"); cont.appendChild(k);
    var tot = cuenta.Ejecutado + cuenta.Programado + cuenta.Reprogramado + cuenta["No ejecutado"];
    kpi(k, n(tot), "actividades-mes programadas", "Plan Anual 2026");
    kpi(k, n(cuenta.Ejecutado), "ejecutadas", tot ? fp(pct(cuenta.Ejecutado, tot)) : "");
    kpi(k, n(cuenta.Reprogramado), "reprogramadas"); kpi(k, n(cuenta["No ejecutado"]), "no ejecutadas");
    var w = el("div", "pr-tab-w"), t = el("table", "pr-tab pr-crono"), th = el("tr");
    th.appendChild(el("th", null, "Acción")); MESES.forEach(function (m) { th.appendChild(el("th", "c", m)); });
    var hd = el("thead"); hd.appendChild(th); t.appendChild(hd); var tb = el("tbody"); t.appendChild(tb);
    var CL = { "Ejecutado": "ej", "Programado": "pg", "Reprogramado": "rp", "No ejecutado": "ne" };
    C.forEach(function (c) {
      var tr = el("tr"), td = el("td"); td.appendChild(el("strong", null, c.accion)); td.appendChild(el("small", null, c.problema + (c.publico ? " · " + c.publico : "") + (c.lugar ? " · " + c.lugar : ""))); tr.appendChild(td);
      c.meses.forEach(function (m, i) { var x = el("td", "c"); if (m) { var s = el("span", "pr-st " + (CL[m] || "pg")); s.title = MESL[i] + ": " + m; x.appendChild(s); } tr.appendChild(x); });
      tb.appendChild(tr);
    });
    w.appendChild(t); cont.appendChild(w);
    var ley = el("div", "pr-ley"); [["ej", "Ejecutado"], ["pg", "Programado"], ["rp", "Reprogramado"], ["ne", "No ejecutado"]].forEach(function (x) { var s = el("span"); s.appendChild(el("i", "pr-st " + x[0])); s.appendChild(document.createTextNode(x[1])); ley.appendChild(s); }); cont.appendChild(ley);
    nota(cont, "Fuente: Plan Anual de Trabajo 2026 de Promoción de la Salud – RIS Chachapoyas" + (P.mes ? "; estado actualizado a " + P.mes : "") + ".");
  }

  // ---------- Cifras de la portada ----------
  function portada() {
    var P = D(), z = document.getElementById("phero-datos"); if (!P || !z) return;
    z.innerHTML = "";
    var comp = P.programas.filter(function (p) { return p.comparable && p.produccion != null; });
    var tot = P.programas.reduce(function (s, p) { return s + (p.produccion || 0); }, 0);
    [[P.mes ? cap(P.mes) : "–", "mes del reporte"], [n(tot), "registros de promoción en el HIS"], [n(P.microredes.length), "microredes"], [n(P.programas.length), "programas presupuestales"]].forEach(function (d) {
      var x = el("div", "dato"); x.appendChild(el("strong", null, d[0])); x.appendChild(el("span", null, d[1])); z.appendChild(x);
    });
    // Resumen en Inicio
    var r = document.getElementById("pr-resumen"); if (!r) return;
    r.innerHTML = ""; r.appendChild(el("h3", "pl-sub", "Avance de metas por programa"));
    var g = el("div", "pr-mini"); r.appendChild(g);
    P.programas.forEach(function (p) {
      var pc = p.comparable ? pct(p.produccion, p.meta) : null;
      var a = el("a", "pr-mini-c"); a.href = "#avance"; a.style.setProperty("--c", p.color);
      a.appendChild(el("span", null, p.corto)); a.appendChild(el("strong", null, p.comparable ? fp(pc) : n(p.produccion)));
      a.appendChild(el("small", null, p.comparable ? "de la meta" : "registros"));
      g.appendChild(a);
    });
    var U = (P.actividades || []).slice(0, 3);
    if (U.length) {
      r.appendChild(el("h3", "pl-sub", "Últimas actividades"));
      var l = el("div", "pr-acts compacta"); U.forEach(function (a) { var c = el("a", "pr-act"); c.href = "#actividades"; var b = el("div", "pr-act-b"); var top = el("div", "pr-act-top"); top.appendChild(el("span", "pr-act-f", f(a.fecha))); if (a.tema) top.appendChild(el("span", "pr-tag", a.tema)); b.appendChild(top); b.appendChild(el("h4", null, a.tipo)); b.appendChild(el("small", null, [a.microred ? "Microred " + mr(a.microred) : "", a.participantes ? n(a.participantes) + " participantes" : ""].filter(Boolean).join(" · "))); c.appendChild(b); l.appendChild(c); }); r.appendChild(l);
    }
  }

  window.VISTAS = window.VISTAS || {};
  window.VISTAS.avance = avance; window.VISTAS.actividades = actividades; window.VISTAS.escenarios = escenarios; window.VISTAS.plan = plan;
  window.Promsa = { portada: portada };
})();
