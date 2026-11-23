/* Páginas adicionales del portal de Epidemiología (se editan a mano; no las genera ningún Excel). */
window.PAGINAS = window.PAGINAS || {};

/* Recordatorios que se muestran en la sección Calendario epidemiológico */
window.CAL_NOTAS = [
    "La notificación semanal de las DIRESA al CDC Perú se realiza los martes antes de las 14:00 horas.",
  "Todo brote o epizootia debe notificarse de manera inmediata a Siepibrote.",
  "22 de septiembre: Día de la Epidemiología Peruana."
];

/* Indicadores de notificación (pestaña propia). Se llenará con data/unidades/indicadores_notificacion.xlsx */
window.PAGINAS["indicadores-notificacion"] = [
  {
    tipo: "destacado", titulo: "En preparación", icono: "grafico",
    texto: "Aquí se publicarán los indicadores de monitoreo de la notificación por microred y establecimiento (unidades notificantes e informantes), por semana epidemiológica de corte, a partir de la plantilla indicadores_notificacion.xlsx."
  },
  {
    tipo: "tarjetas", titulo: "Indicadores que se medirán", columnas: 2, compacto: true,
    intro: "Para cada establecimiento se calcula el porcentaje de cumplimiento de cada indicador y un puntaje total. Nivel óptimo según los estratos nacionales:",
    items: [
      { titulo: "Oportunidad", icono: "reloj", texto: "Óptimo: 100 %." },
      { titulo: "Cobertura", icono: "check", texto: "Óptimo: 100 %." },
      { titulo: "Calidad del dato", icono: "estrella", texto: "Óptimo: 95 a 100 %." },
      { titulo: "Retroalimentación", icono: "equipo", texto: "Óptimo: 90 a 100 %." }
    ]
  },
  {
    tipo: "tarjetas", titulo: "Calificación del puntaje total", columnas: 4, compacto: true,
    intro: "Estratos nacionales del Centro Nacional de Epidemiología, Prevención y Control de Enfermedades (CDC-MINSA).",
    items: [
      { titulo: "Óptimo", icono: "estrella", texto: "90 % o más." },
      { titulo: "Bueno", icono: "check", texto: "80 a 89,9 %." },
      { titulo: "Regular", icono: "reloj", texto: "70 a 79,9 %." },
      { titulo: "Débil", icono: "alerta", texto: "Menos de 70 %." }
    ]
  }
];
