"""Genera los datos del portal PROMSA a partir de dos Excel:

  promsa/datos/PROMSA_portal.xlsx   plantilla mensual (Nosotros, Metas, Actividades, Escenarios, Cronograma)
  promsa/datos/his/*.xlsx           reporte HIS de promoción de la salud, tal como se descarga
                                    (si hay varios, se usa el más reciente por fecha de corte)

Salida: promsa/data/promsa.js, promsa/data/actividades.js, promsa/data/emergencias.js y promsa/data/nosotros.js
Antes ejecuta las herramientas generales de SIVISA (herramientas/fotos.py, institucional.py y actividades.py),
así el flujo de publicación no necesita cambios.
Uso:    python3 promsa/herramientas/preparar_promsa.py
Solo se publican cifras agregadas por microred. Nunca nombres ni DNI de beneficiarios.
"""
import datetime, json, os, re, sys
from openpyxl import load_workbook
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "herramientas"))
import sivisa_comun as C
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


def indices(c):
    """Columnas del HIS -> índices: ("T","AQ") o ["FX","GA"] (forma interna) o texto "T:AQ, FX, GA" (hoja Programas)."""
    if isinstance(c, tuple):
        return list(range(ci(c[0]) - 1, ci(c[1])))
    if isinstance(c, list):
        return [ci(x) - 1 for x in c]
    out, txtc = [], str(c).upper()
    resto = re.sub(r"[A-Z]{1,3}\s*[:\-–]\s*[A-Z]{1,3}|[A-Z]{1,3}|[\s,;]+", "", txtc)
    if resto:
        raise ValueError("columnas no válidas: " + txtc)
    for t in re.findall(r"[A-Z]{1,3}\s*[:\-–]\s*[A-Z]{1,3}|[A-Z]{1,3}", txtc):
        m = re.fullmatch(r"([A-Z]{1,3})\s*[:\-–]\s*([A-Z]{1,3})", t)
        out += list(range(ci(m.group(1)) - 1, ci(m.group(2)))) if m else [ci(t) - 1]
    return out


def leer_programas(wb):
    """Hoja Programas de la plantilla (si existe): reemplaza la lista PROGRAMAS por defecto."""
    global PROGRAMAS
    if "Programas" not in wb.sheetnames:
        return
    nuevos = []
    for n, r in enumerate(wb["Programas"].iter_rows(min_row=4, values_only=True), 4):
        if not r or not txt(r[0]) or not txt(r[3]):
            continue
        pid = txt(r[0]).split(".")[0]
        try:
            indices(txt(r[3]))
        except Exception as e:
            aviso("Programas fila %d (PP %s): %s; se usa la configuración anterior." % (n, pid, e)); return
        previo = next((p for p in PROGRAMAS if p["id"] == pid), {})
        nuevos.append({"id": pid, "nombre": txt(r[1]) or previo.get("nombre", pid), "corto": txt(r[2]) or txt(r[1]) or pid,
                       "cols": txt(r[3]), "comparable": C.clave(txt(r[5])) in ("si", "s", "yes", "1", "true"),
                       "unidad": txt(r[4]) or previo.get("unidad", "registros"),
                       "color": txt(r[6]) if len(r) > 6 and re.fullmatch(r"#[0-9a-fA-F]{6}", txt(r[6])) else previo.get("color", "#8a6a12")})
    if nuevos:
        PROGRAMAS = nuevos


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
            idx = indices(p["cols"])
            d[p["id"]] = int(sum(r[i] for i in idx if i < len(r) and isinstance(r[i], (int, float))))
        if mr == SIN_MR: otros = d
        else: prod[mr] = d
    print("  HIS: %s (%s a %s), %d microredes" % (f, ini, fin, len(prod)))
    return {"archivo": f, "desde": ini, "hasta": fin, "microredes": prod, "sin_microred": otros}


# ---------------- Plantilla ----------------
def leer_plantilla():
    wb = load_workbook(PLANTILLA, data_only=True)
    leer_programas(wb)
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
    # Actividades (lectura común a los tres portales: textos libres normalizados, fotos tolerantes a la extensión)
    out["actividades"] = C.leer_actividades(wb["Actividades"], FOTOS)
    # Emergencias sanitarias (opcional)
    out["emergencias"] = leer_emergencias(wb, out["actividades"])
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


def leer_emergencias(wb, acts):
    """Hojas Emergencias, Emergencias_metas y Emergencias_avance. Devuelve la lista de emergencias con sus
    indicadores, el avance acumulado frente a la meta, el avance por mes y por microred."""
    if "Emergencias" not in wb.sheetnames:
        return []
    ems, por_clave = [], {}
    for r in wb["Emergencias"].iter_rows(min_row=4, values_only=True):
        nom = C.normal(r[0]) if r and r[0] else ""
        if not nom:
            continue
        e = {"nombre": nom, "estado": C.normal(r[1]) or "Activa", "inicio": C.fecha(r[2]), "fin": C.fecha(r[3]),
             "ambito": C.txt(r[4]), "objetivo": C.txt(r[5]), "contexto": C.txt(r[6]) if len(r) > 6 else "",
             "indicadores": [], "meses": [], "microredes": [], "actividades": 0}
        ems.append(e); por_clave[C.clave(nom)] = e
    if not ems:
        return []
    ind_de = {}
    if "Emergencias_metas" in wb.sheetnames:
        for r in wb["Emergencias_metas"].iter_rows(min_row=4, values_only=True):
            if not r or not r[0] or not r[2]:
                continue
            e = por_clave.get(C.clave(C.txt(r[0])))
            if not e:
                C.aviso("Emergencias_metas: la emergencia '%s' no está en la hoja Emergencias." % C.txt(r[0])); continue
            i = {"componente": C.txt(r[1]), "indicador": C.normal(r[2]), "unidad": C.txt(r[3]), "meta": C.num(r[4]), "avance": 0}
            e["indicadores"].append(i); ind_de[(C.clave(e["nombre"]), C.clave(i["indicador"]))] = i
    meses, mrs = {}, {}
    if "Emergencias_avance" in wb.sheetnames:
        for n, r in enumerate(wb["Emergencias_avance"].iter_rows(min_row=4, values_only=True), 4):
            if not r or not any(x not in (None, "") for x in r[:4]):
                continue
            m, e = C.mes(r[0]), por_clave.get(C.clave(C.txt(r[1])))
            v = C.num(r[3])
            if not m or not e or v is None:
                C.aviso("Emergencias_avance fila %d: falta mes, emergencia o avance válido; se omite." % n); continue
            k = (C.clave(e["nombre"]), C.clave(C.txt(r[2])))
            i = ind_de.get(k)
            if not i:
                i = {"componente": "", "indicador": C.normal(r[2]), "unidad": "", "meta": None, "avance": 0}
                e["indicadores"].append(i); ind_de[k] = i
                C.aviso("Emergencias_avance fila %d: indicador sin meta registrada: %s" % (n, i["indicador"]))
            i["avance"] += v
            meses.setdefault(id(e), {}).setdefault(m, {}).setdefault(i["indicador"], 0)
            meses[id(e)][m][i["indicador"]] += v
            mr = C.nombre_mr(r[4]) if len(r) > 4 else ""
            if mr:
                mrs.setdefault(id(e), {}).setdefault(mr, {}).setdefault(i["indicador"], 0)
                mrs[id(e)][mr][i["indicador"]] += v
    for e in ems:
        e["meses"] = [{"mes": m, "valores": v} for m, v in sorted(meses.get(id(e), {}).items())]
        e["microredes"] = [{"microred": m, "valores": v} for m, v in sorted(mrs.get(id(e), {}).items())]
        e["actividades"] = sum(1 for a in acts if C.clave(a.get("emergencia", "")) == C.clave(e["nombre"]))
    ems.sort(key=lambda e: e["inicio"] or "", reverse=True)
    ems.sort(key=lambda e: C.clave(e["estado"]) != "activa")
    return ems


def extras():
    """Herramientas generales de SIVISA que se ejecutan al publicar (sin tocar el flujo de GitHub)."""
    for mod in ("fotos", "institucional", "actividades"):
        try:
            __import__(mod).main()
        except Exception as e:
            print("  ! herramientas/%s.py: %s" % (mod, e))


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
    extras()
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
    C.escribir_js(os.path.join(SALIDA, "actividades.js"), "ACTIVIDADES",
                  {"actualizado": datos["actualizado"], "fotos": "fotos/", "actividades": P["actividades"]},
                  "Generado por promsa/herramientas/preparar_promsa.py desde la hoja Actividades de PROMSA_portal.xlsx.")
    C.escribir_js(os.path.join(SALIDA, "emergencias.js"), "EMERGENCIAS",
                  {"actualizado": datos["actualizado"], "emergencias": P["emergencias"]},
                  "Generado por promsa/herramientas/preparar_promsa.py desde las hojas Emergencias de PROMSA_portal.xlsx.")
    print("  %d emergencias sanitarias" % len(P["emergencias"]))
    print("  %d actividades, %d acciones del cronograma, mes: %s" % (len(P["actividades"]), len(P["cronograma"]), P["mes"] or "–"))


if __name__ == "__main__":
    main()
