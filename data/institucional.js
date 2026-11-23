/* Generado por herramientas/institucional.py desde data/SIVISA_INSTITUCIONAL.xlsx. No editar a mano.
   Se aplica encima de data/sitio.js. */
(function () {
  var I = {
 "actualizado": "2026-11-22",
 "mision": "",
 "vision": "",
 "sobre": {
  "titulo": "Vigilancia en salud pública",
  "texto": "SIVISA reúne en un solo lugar la información de vigilancia sanitaria de la Red Integrada de Salud Chachapoyas: epidemiología, salud ambiental y promoción de la salud, para apoyar la toma de decisiones de los equipos de salud y la comunidad.",
  "puntos": [
   "Información elaborada por las oficinas de la Red.",
   "Actualización periódica de publicaciones e indicadores."
  ]
 },
 "sede": {
  "titulo": "Sede institucional",
  "direccion": "Jr. Triunfo 242 - Chachapoyas",
  "correo": "",
  "telefono": "",
  "horario": ""
 },
 "autoridades": [
  {
   "cargo": "Directora de la Red de Salud Chachapoyas",
   "nombre": "Lic. Enf. Marly Asunta Zumaeta Villavicencio"
  },
  {
   "cargo": "Responsable de Salud Pública",
   "nombre": "Psic. Ingrid Carmela Peralta Vega"
  }
 ],
 "contacto": {
  "nombre": "M.C. Yhojar A. Pisfil-Farroñay",
  "cargo": "",
  "area": "",
  "correo": "yhojar.minsa@gmail.com",
  "foto": ""
 },
 "responsables": {
  "epidemiologia": {
   "titulo": "Responsable de la oficina",
   "nombre": "Lic. Enf. Lith Mariela Malqui Zuta",
   "cargo": "Oficina de Epidemiología",
   "correo": "epiredchachapoyas@gmail.com"
  },
  "salud-ambiental": {
   "titulo": "Responsable del área",
   "nombre": "Blgo. John Herbert Zúñiga Díaz",
   "cargo": "Salud Ambiental",
   "correo": ""
  },
  "promsa": {
   "titulo": "Responsable de la unidad",
   "nombre": "Obsta. Marleny Ponce Delgado",
   "cargo": "Unidad de Promoción de la Salud",
   "correo": ""
  }
 }
};
  var S = window.SITIO = window.SITIO || {};
  if (I.mision) S.mision = I.mision; if (I.vision) S.vision = I.vision;
  if (I.sobre) S.sobre = I.sobre;
  if (I.sede && I.sede.direccion) S.sede = I.sede;
  if (I.autoridades && I.autoridades.length) S.autoridades = I.autoridades;
  if (I.contacto && I.contacto.nombre) S.contacto = I.contacto;
  (S.portales || []).forEach(function (p) { var r = (I.responsables || {})[p.id]; if (r) p.responsable = r; });
})();
