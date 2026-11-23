/* SIVISA © M.C. Yhojar A. Pisfil-Farroñay. Todos los derechos reservados. Uso autorizado solo en la dirección oficial. */
(function () {
  var h = location.hostname, ok = ["ZXBpcmVkY2hhY2hhcG95YXMuZ2l0aHViLmlv", "bG9jYWxob3N0", "MTI3LjAuMC4x"];
  if (location.protocol === "file:" || h === "" || ok.indexOf(btoa(h)) >= 0) return;
  var m = '<div style="font:16px/1.6 system-ui,Arial,sans-serif;max-width:620px;margin:12vh auto;padding:28px;border:2px solid #b00020;border-radius:12px;color:#222;background:#fff">' +
    '<h1 style="margin:0 0 10px;color:#b00020;font-size:22px">Copia no autorizada</h1>' +
    '<p>SIVISA – Sistema de Información de Vigilancia Sanitaria de la Red Integrada de Salud Chachapoyas es una obra protegida por derechos de autor de <b>M.C. Yhojar A. Pisfil-Farroñay</b>.</p>' +
    '<p>Esta copia se está mostrando fuera de su dirección oficial sin autorización. Sitio oficial: <a href="https://epiredchachapoyas.github.io/sivisa-red/">epiredchachapoyas.github.io/sivisa-red</a></p></div>';
  function bloquear() { document.documentElement.innerHTML = "<head><meta charset='utf-8'><title>Copia no autorizada</title></head><body style='background:#f4f4f4'>" + m + "</body>"; window.stop && window.stop(); }
  if (document.body) bloquear(); else document.addEventListener("DOMContentLoaded", bloquear);
  window.VISTAS = {}; window.SITIO = {};
})();
