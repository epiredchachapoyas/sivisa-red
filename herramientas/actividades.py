"""Genera <portal>/data/actividades.js de Epidemiología y Salud Ambiental desde su plantilla de actividades.

  epidemiologia/datos/ACTIVIDADES_EPIDEMIOLOGIA.xlsx      fotos en epidemiologia/fotos/
  salud-ambiental/datos/ACTIVIDADES_SALUD_AMBIENTAL.xlsx  fotos en salud-ambiental/fotos/
(PROMSA usa la hoja Actividades de PROMSA_portal.xlsx: lo hace promsa/herramientas/preparar_promsa.py.)
"""
import datetime, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sivisa_comun as C

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTALES = [("epidemiologia", "ACTIVIDADES_EPIDEMIOLOGIA.xlsx"), ("salud-ambiental", "ACTIVIDADES_SALUD_AMBIENTAL.xlsx")]


def main():
    from openpyxl import load_workbook
    for carpeta, nombre in PORTALES:
        xl = os.path.join(RAIZ, carpeta, "datos", nombre)
        fotos = os.path.join(RAIZ, carpeta, "fotos")
        acts = []
        print("Actividades %s:" % carpeta)
        if os.path.isfile(xl):
            try:
                wb = load_workbook(xl, data_only=True)
                acts = C.leer_actividades(wb["Actividades"], fotos)
            except Exception as e:
                C.aviso("No se pudo leer %s (%s); se publica sin actividades." % (nombre, e))
        else:
            C.aviso("No existe %s/datos/%s" % (carpeta, nombre))
        C.escribir_js(os.path.join(RAIZ, carpeta, "data", "actividades.js"), "ACTIVIDADES",
                      {"actualizado": datetime.date.today().isoformat(), "fotos": "fotos/", "actividades": acts},
                      "Generado por herramientas/actividades.py desde %s." % nombre)
        print("  %d actividades" % len(acts))


if __name__ == "__main__":
    main()
