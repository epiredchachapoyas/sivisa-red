"""Genera los datos del portal PROMSA a partir de dos Excel:

  promsa/datos/PROMSA_portal.xlsx   plantilla mensual (Nosotros, Metas, Actividades, Escenarios, Cronograma)
  promsa/datos/his/*.xlsx           reporte HIS de promoción de la salud, tal como se descarga
                                    (si hay varios, se usa el más reciente por fecha de corte)

Salida: promsa/data/promsa.js y promsa/data/nosotros.js
Uso:    python3 promsa/herramientas/preparar_promsa.py
Solo se publican cifras agregadas por microred. Nunca nombres ni DNI de beneficiarios.
"""
import datetime, json, os, re, sys
from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string as ci

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANTILLA = os.path.join(RAIZ, "datos", "PROMSA_portal.xlsx")
HIS = os.path.join(RAIZ, "datos", "his")
FOTOS = os.path.join(RAIZ, "fotos")
SALIDA = os.path.join(RAIZ, "data")

# Programas presupuestales y columnas de la hoja "Desagregado" del reporte HIS que se cuentan como producción
# (misma correspondencia del Informe de evaluación de indicadores de PROMSA, noviembre 2026).
PROGRAMAS = [
    {"id": "1001", "nombre": "Desarrollo Infantil Temprano", "corto": "DIT", "cols": ("T", "AQ"), "comparable": False,
     "unidad": "consejerías por tema y edad", "color": "#e0802e"},
    {"id": "002", "nombre": "Materno Neonatal", "corto": "Materno", "cols": ["FX", "GA"], "comparable": True,
     "unidad": "segundas consejerías a la gestante", "color": "#d1477a"},
    {"id": "016", "nombre": "TBC - VIH/SIDA", "corto": "TBC-VIH", "cols": ["JT"], "comparable": True,
     "unidad": "segundas consejerías de TBC en visita domiciliaria", "color": "#7a5cc4"},
    {"id": "017", "nombre": "Metaxénicas y Zoonosis", "corto": "Metaxénicas", "cols": ("OY", "PF"), "comparable": True,
     "unidad": "segundas sesiones demostrativas por enfermedad", "color": "#2e9e5b"},
    {"id": "018", "nombre": "No Transmisibles", "corto": "No transmisibles", "cols": ("AUO", "AUU"), "comparable": True,
     "unidad": "sesiones por temática", "color": "#2f7fc1"},
    {"id": "024", "nombre": "Cáncer", "corto": "Cáncer", "cols": ("AXP", "AXS"), "comparable": True,
     "unidad": "sesiones educativas a familias", "color": "#c0392b"},
    {"id": "131", "nombre": "Salud Mental", "corto": "Salud mental", "cols": ("AZT", "BBM"), "comparable": False,
     "unidad": "consejerías de crianza por edad y modalidad", "color": "#16a0a0"},
]
SIN_MR = "ESTABLECIMIENTO QUE NO PERTENECE A NINGUNA MICRORED"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "septiembre", "octubre", "noviembre", "diciembre"]
PROHIBIDO = re.compile(r"\b\d{8}\b")  # posible DNI en textos libres


def txt(v):
    return re.sub(r"\s+", " ", str(v)).strip() if v is not None else ""


def num(v):
    if isinstance(v, (int, float)): return v
    try: return float(str(v).replace(",", "."))
    except Exception: return None


def fecha(v):
    if isinstance(v, datetime.datetime): return v.date().isoformat()
    if isinstance(v, datetime.date): return v.isoformat()
    m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", txt(v))
    return "%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1))) if m else ""


def aviso(m): print("  ! " + m)


def nombre_mr(s): return txt(s).upper().replace("MCR ", "").replace("MICRORED ", "").strip()


# ---------------- Reporte HIS ----------------
def leer_his():
    if not os.path.isdir(HIS): return None
    cands = []
    for f in os.listdir(HIS):
        if not f.lower().endswith(".xlsx") or f.startswith("~$"): continue
        try:
            wb = load_workbook(os.path.join(HIS, f), read_only=True, data_only=True)
            if "Desagregado" not in wb.sheetnames: aviso(f + ": no tiene la hoja Desagregado; se omite."); continue
            ws = wb["Desagregado"]
            ini, fin = ws["B3"].value, ws["B4"].value
            cands.append((fecha(fin) or "", fecha(ini) or "", f, wb))
        except Exception as e:
            aviso(f + ": no se pudo leer (" + str(e) + ")")
    if not cands: return None
    cands.sort(key=lambda x: x[0])
    fin, ini, f, wb = cands[-1]
    ws = wb["Desagregado"]
    filas = [list(r) for r in ws.iter_rows(min_row=13, max_row=60, values_only=True)]
    prod, otros = {}, {}
    for r in filas:
        mr = txt(r[0]).upper() if r and r[0] else ""
        if not mr or mr.startswith("TOTAL"): continue
        d = {}
        for p in PROGRAMAS:
            c = p["cols"]
            idx = list(range(ci(c[0]) - 1, ci(c[1]))) if isinstance(c, tuple) else [ci(x) - 1 for x in c]
            d[p["id"]] = int(sum(r[i] for i in idx if i < len(r) and isinstance(r[i], (int, float))))
        if mr == SIN_MR: otros = d
        else: prod[mr] = d
    print("  HIS: %s (%s a %s), %d microredes" % (f, ini, fin, len(prod)))
    return {"archivo": f, "desde": ini, "hasta": fin, "microredes": prod, "sin_microred": otros}


# ---------------- Plantilla ----------------
def leer_plantilla():
    wb = load_workbook(PLANTILLA, data_only=True)
    out = {}
    ws = wb["Instrucciones"]
    out["mes"] = ""
    for r in ws.iter_rows(min_row=1, max_row=12):
        if txt(r[0].value).lower().startswith("mes del reporte"): out["mes"] = txt(r[1].value)
    # Nosotros
    ws = wb["Nosotros"]; nos = {"equipo": []}
    for r in ws.iter_rows(min_row=3, max_row=9):
        k = txt(r[0].value).lower()
        for clave in ("misión", "visión", "finalidad", "objetivo general", "áreas de trabajo"):
            if k.startswith(clave): nos[clave] = txt(r[1].value)
    for r in ws.iter_rows(min_row=11, max_row=40):
        n = txt(r[0].value)
        if not n or n.lower().startswith("no incluir"):
            if n.lower().startswith("no incluir"): break
            continue
        nos["equipo"].append({"nombre": n, "profesion": txt(r[1].value), "cargo": txt(r[2].value)})
    for r in ws.iter_rows(min_row=20, max_row=30):
        v = txt(r[0].value)
        if "@" in v: nos["correo"] = v
    out["nosotros"] = nos
    # Metas
    ws = wb["Metas"]
    cab = [txt(c.value) for c in ws[4]]
    metas = {}
    for r in ws.iter_rows(min_row=5, values_only=True):
        mr = nombre_mr(r[0])
        if not mr or mr.startswith("TOTAL"): continue
        metas[mr] = {}
        for j, h in enumerate(cab[1:], 1):
            pid = h.split(" ")[0]
            v = num(r[j]) if j < len(r) else None
            if v is not None: metas[mr][pid] = v
    out["metas"] = metas
    # Actividades
    ws = wb["Actividades"]; acts = []
    for r in ws.iter_rows(min_row=4, values_only=True):
        if not any(r[:8]): continue
        f, desc = fecha(r[0]), txt(r[7])
        if not f: aviso("Actividades: fila sin fecha válida (%s); se omite." % desc[:40]); continue
        if PROHIBIDO.search(desc): aviso("Actividades: la descripción del %s parece tener un DNI; se omite." % f); continue
        foto = txt(r[8])
        if foto and not os.path.isfile(os.path.join(FOTOS, foto)): aviso("Foto no encontrada en promsa/fotos: " + foto); foto = ""
        acts.append({"fecha": f, "microred": nombre_mr(r[1]), "distrito": txt(r[2]), "escenario": txt(r[3]), "tipo": txt(r[4]),
                     "tema": txt(r[5]), "participantes": int(num(r[6]) or 0), "descripcion": desc[:250], "foto": foto})
    acts.sort(key=lambda a: a["fecha"], reverse=True)
    out["actividades"] = acts
    # Escenarios
    ws = wb["Escenarios"]
    out["escenarios_corte"] = fecha(ws["B2"].value)
    cab = [txt(c.value) for c in ws[4]][1:5]
    esc = []
    for r in ws.iter_rows(min_row=5, values_only=True):
        mr = nombre_mr(r[0])
        if not mr or mr.startswith("TOTAL"): continue
        vals = [int(num(x)) if num(x) is not None else None for x in r[1:5]]
        esc.append({"microred": mr, "valores": vals, "obs": txt(r[5]) if len(r) > 5 else ""})
    out["escenarios"] = {"columnas": cab, "filas": esc}
    # Cronograma
    ws = wb["Cronograma"]; cro = []
    for r in ws.iter_rows(min_row=5, values_only=True):
        if not r[0] or not r[1] or txt(r[0]).lower().startswith("valores"): continue
        cro.append({"problema": txt(r[0]), "accion": txt(r[1]), "publico": txt(r[2]), "lugar": txt(r[3]),
                    "meses": [txt(x) for x in r[4:16]]})
    out["cronograma"] = cro
    return out


def nosotros_js(n):
    bl = []
    tj = [{"titulo": "Misión", "icono": "mision", "texto": n.get("misión", "")}, {"titulo": "Visión", "icono": "vision", "texto": n.get("visión", "")}]
    tj = [t for t in tj if t["texto"]]
    if tj: bl.append({"tipo": "tarjetas", "columnas": 2, "items": tj})
    if n.get("finalidad"): bl.append({"tipo": "destacado", "titulo": "Finalidad", "icono": "objetivo", "texto": n["finalidad"]})
    if n.get("objetivo general"): bl.append({"tipo": "tarjetas", "titulo": "Objetivo general", "columnas": 1, "items": [{"titulo": "Lo que buscamos", "icono": "estrella", "texto": n["objetivo general"]}]})
    areas = [a.strip() for a in re.split(r"[;\n]", n.get("áreas de trabajo", "")) if a.strip()]
    DESC = {"promoción de vida sana": "Comportamientos saludables, salud mental y entornos saludables en la persona, la familia y la comunidad.",
            "educación para la salud": "Intervenciones educativas y comunicacionales, materiales y contenidos para construir una cultura de la salud.",
            "participación comunitaria en salud": "Agentes comunitarios, AIEPI comunitario y participación ciudadana para el cuidado de la salud."}
    ICO = ["corazon", "libro", "equipo"]
    if areas: bl.append({"tipo": "tarjetas", "titulo": "Áreas de trabajo", "columnas": 3, "compacto": True,
                         "items": [{"titulo": a.rstrip("."), "icono": ICO[i % 3], "texto": DESC.get(a.rstrip(".").lower(), "")} for i, a in enumerate(areas)]})
    if n["equipo"]:
        bl.append({"tipo": "equipo", "titulo": "Equipo técnico", "items": [
            {"nombre": p["nombre"], "cargo": " · ".join(x for x in (p["cargo"], p["profesion"]) if x), "destacado": i == 0} for i, p in enumerate(n["equipo"])]})
    return "/* Generado por promsa/herramientas/preparar_promsa.py desde la hoja Nosotros de PROMSA_portal.xlsx. No editar a mano. */\nwindow.PAGINAS = window.PAGINAS || {};\nwindow.PAGINAS.nosotros = " + json.dumps(bl, ensure_ascii=False, indent=1) + ";\n"


def main():
    if not os.path.isfile(PLANTILLA): print("No existe " + PLANTILLA); sys.exit(0)
    print("PROMSA:")
    P = leer_plantilla()
    H = leer_his()
    mrs = sorted(set(P["metas"]) | set((H or {}).get("microredes", {})))
    progs = []
    for p in PROGRAMAS:
        meta = sum(P["metas"].get(m, {}).get(p["id"], 0) for m in mrs)
        prod = sum((H or {}).get("microredes", {}).get(m, {}).get(p["id"], 0) for m in mrs) if H else None
        fuera = (H or {}).get("sin_microred", {}).get(p["id"], 0) if H else 0
        progs.append({"id": p["id"], "nombre": p["nombre"], "corto": p["corto"], "unidad": p["unidad"], "color": p["color"],
                      "comparable": p["comparable"], "meta": meta, "produccion": prod, "fuera_microred": fuera})
    datos = {
        "actualizado": datetime.date.today().isoformat(),
        "mes": P["mes"],
        "his": {k: H[k] for k in ("desde", "hasta")} if H else None,
        "programas": progs,
        "microredes": [{"nombre": m, "metas": P["metas"].get(m, {}), "produccion": (H or {}).get("microredes", {}).get(m, {})} for m in mrs],
        "actividades": P["actividades"],
        "escenarios": P["escenarios"], "escenarios_corte": P["escenarios_corte"],
        "cronograma": P["cronograma"],
        "correo": P["nosotros"].get("correo", ""),
    }
    os.makedirs(SALIDA, exist_ok=True)
    with open(os.path.join(SALIDA, "promsa.js"), "w", encoding="utf-8") as f:
        f.write("/* Generado por promsa/herramientas/preparar_promsa.py. No editar a mano. */\nwindow.PROMSA = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";\n")
    with open(os.path.join(SALIDA, "nosotros.js"), "w", encoding="utf-8") as f:
        f.write(nosotros_js(P["nosotros"]))
    print("  %d actividades, %d acciones del cronograma, mes: %s" % (len(P["actividades"]), len(P["cronograma"]), P["mes"] or "–"))


if __name__ == "__main__":
    main()
