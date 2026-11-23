/* SIVISA – vista compartida "Actividades" (Epidemiología, Salud Ambiental y PROMSA).
   Lee window.ACTIVIDADES = {actualizado, fotos, actividades:[{fecha, microred, distrito, escenario, tipo, tema,
   participantes, descripcion, foto, emergencia}]}, que generan herramientas/actividades.py y preparar_promsa.py. */
(function () {
  var MESL = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"];
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function n(v) { return v == null ? "–" : Number(v).toLocaleString("es-PE"); }
  function f(iso) { var p = String(iso || "").split("-"); return p.length === 3 ? p[2] + "/" + p[1] + "/" + p[0] : "–"; }
  function cap(s) { s = String(s || ""); return s.charAt(0).toUpperCase() + s.slice(1); }
  function mr(s) { return String(s || "").toLowerCase().replace(/(^|\s)\S/g, function (m) { return m.toUpperCase(); }); }
  function mesTxt(m) { return cap(MESL[+m.slice(5) - 1]) + " " + m.slice(0, 4); }
  function datos() { return window.ACTIVIDADES || { actividades: [] }; }
  function lista() { return datos().actividades || []; }
  function base() { return datos().fotos || "fotos/"; }
  function kpi(c, v, l) { var k = el("div", "ac-kpi"); k.appendChild(el("strong", null, v)); k.appendChild(el("span", null, l)); c.appendChild(k); }

  function tarjeta(a, compacta, href) {
    var c = el(href ? "a" : "article", "ac-card" + (a.foto && !compacta ? " con-foto" : ""));
    if (href) c.href = href;
    if (a.foto && !compacta) {
      var ln = el("a", "ac-foto"); ln.href = base() + encodeURIComponent(a.foto); ln.target = "_blank"; ln.rel = "noopener"; ln.title = "Ver foto completa";
      var im = el("img"); im.src = ln.href; im.alt = (a.tipo || "Actividad") + (a.tema ? " – " + a.tema : ""); im.loading = "lazy";
      im.onerror = function () { ln.remove(); c.classList.remove("con-foto"); };
      ln.appendChild(im); c.appendChild(ln);
    }
    var b = el("div", "ac-b"), top = el("div", "ac-top");
    top.appendChild(el("span", "ac-f", f(a.fecha)));
    if (a.tema) top.appendChild(el("span", "ac-tag", a.tema));
    if (a.emergencia) top.appendChild(el("span", "ac-tag em", a.emergencia));
    b.appendChild(top);
    b.appendChild(el("h4", null, a.tipo || (a.tema ? "Actividad: " + a.tema : "Actividad")));
    if (a.descripcion && !compacta) b.appendChild(el("p", null, a.descripcion));
    var pie = [a.microred ? "Microred " + mr(a.microred) : "", compacta ? "" : a.distrito, compacta ? "" : a.escenario,
               a.participantes ? n(a.participantes) + " participantes" : ""].filter(Boolean).join(" · ");
    if (pie) b.appendChild(el("small", null, pie));
    c.appendChild(b);
    return c;
  }

  /* Vista completa con indicadores y filtros. opc.filtro: {emergencia:"Sarampión 2026"} fija un filtro. */
  function vista(cont, sec, secs, opc) {
    opc = opc || {}; cont.innerHTML = "";
    var A = lista().filter(function (a) { return !opc.filtro || !opc.filtro.emergencia || a.emergencia === opc.filtro.emergencia; });
    if (!A.length) {
      var e = el("div", "ac-vacio"); e.appendChild(el("strong", null, "Aún no hay actividades registradas"));
      e.appendChild(el("p", null, opc.vacio || "Aquí se mostrarán las campañas, capacitaciones, visitas, reuniones y demás actividades que registre el equipo en su plantilla de actividades."));
      cont.appendChild(e); return;
    }
    var est = { mes: "", tipo: "", tema: "", mr: "", em: "" };
    var k = el("div", "ac-kpis"); cont.appendChild(k);
    var fl = el("div", "filters-panel ac-filtros"); cont.appendChild(fl);
    function uniq(fn) { var o = {}; A.forEach(function (a) { var v = fn(a); if (v) o[v] = 1; }); return Object.keys(o).sort(function (x, y) { return x.localeCompare(y, "es"); }); }
    function sel(lbl, vals, key, fmt) {
      if (vals.length < 2) return;
      var w = el("div"); w.appendChild(el("label", null, lbl)); var s = el("select"); s.appendChild(new Option("Todos", ""));
      vals.forEach(function (v) { s.appendChild(new Option(fmt ? fmt(v) : v, v)); });
      s.addEventListener("change", function () { est[key] = s.value; pintar(); }); w.appendChild(s); fl.appendChild(w);
    }
    sel("Mes", uniq(function (a) { return a.fecha.slice(0, 7); }).reverse(), "mes", mesTxt);
    sel("Tipo de actividad", uniq(function (a) { return a.tipo; }), "tipo");
    sel("Tema", uniq(function (a) { return a.tema; }), "tema");
    sel("Microred", uniq(function (a) { return a.microred; }), "mr", mr);
    if (!opc.filtro) sel("Emergencia sanitaria", uniq(function (a) { return a.emergencia; }), "em");
    if (!fl.children.length) fl.remove();
    var L0 = el("div", "ac-lista"); cont.appendChild(L0);
    function pintar() {
      var L = A.filter(function (a) {
        return (!est.mes || a.fecha.slice(0, 7) === est.mes) && (!est.tipo || a.tipo === est.tipo) && (!est.tema || a.tema === est.tema) &&
               (!est.mr || a.microred === est.mr) && (!est.em || a.emergencia === est.em);
      });
      k.innerHTML = "";
      kpi(k, n(L.length), L.length === 1 ? "actividad" : "actividades");
      kpi(k, n(L.reduce(function (s, a) { return s + (a.participantes || 0); }, 0)), "participantes");
      kpi(k, n(Object.keys(L.reduce(function (o, a) { if (a.microred) o[a.microred] = 1; return o; }, {})).length), "microredes");
      kpi(k, n(L.filter(function (a) { return a.foto; }).length), "con foto");
      L0.innerHTML = "";
      if (!L.length) { L0.appendChild(el("div", "empty", "Ninguna actividad cumple el filtro.")); return; }
      L.forEach(function (a) { L0.appendChild(tarjeta(a)); });
    }
    pintar();
    if (datos().actualizado) cont.appendChild(el("p", "ac-nota", "Registro del equipo técnico. Actualizado: " + f(datos().actualizado) + "."));
  }

  /* Bloque "Últimas actividades" para la portada de cada portal. */
  function ultimas(cont, cuantas) {
    if (!cont) return; var U = lista().slice(0, cuantas || 3); cont.innerHTML = "";
    if (!U.length) return;
    cont.appendChild(el("h3", "pl-sub", "Últimas actividades"));
    var g = el("div", "ac-lista compacta"); U.forEach(function (a) { g.appendChild(tarjeta(a, true, "#actividades")); }); cont.appendChild(g);
  }

  window.VISTAS = window.VISTAS || {};
  window.VISTAS.actividades = function (c, s, ss) { vista(c, s, ss); };
  window.Actividades = { vista: vista, ultimas: ultimas, tarjeta: tarjeta };
})();
