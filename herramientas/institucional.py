"""Lee data/SIVISA_INSTITUCIONAL.xlsx y genera:
  data/institucional.js            portada (misión, visión, bloque informativo, sede), autoridades, contacto
                                   y responsables de cada portal (se aplica encima de data/sitio.js)
  epidemiologia/data/nosotros.js   página Nosotros de Epidemiología
  salud-ambiental/data/nosotros.js página Nosotros de Salud Ambiental
(El Nosotros de PROMSA sale de la hoja Nosotros de promsa/datos/PROMSA_portal.xlsx.)
Si el Excel no existe o una hoja falla, se conserva lo que ya estaba publicado."""
import datetime, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sivisa_comun as C

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XL = os.path.join(RAIZ, "data", "SIVISA_INSTITUCIONAL.xlsx")
PORTAL_ID = {"epidemiologia": "epidemiologia", "salud ambiental": "salud-ambiental", "promsa": "promsa",
             "promocion de la salud": "promsa"}

ICONOS = [("responsab", "check"), ("compromiso", "corazon"), ("integridad", "escudo"), ("etica", "escudo"),
          ("trabajo en equipo", "equipo"), ("oportun", "reloj"), ("calidad", "estrella"), ("vigilancia", "lupa"),
          ("analisis", "grafico"), ("investig", "brote"), ("brote", "brote"), ("prevenc", "escudo"), ("control", "escudo"),
          ("asistencia", "equipo"), ("capacit", "libro"), ("informacion", "documento"), ("agua", "gota"),
          ("residuo", "residuos"), ("aliment", "alimento"), ("vector", "vector"), ("zoonosis", "vector"),
          ("saneamiento", "casa"), ("vivienda", "casa"), ("entorno", "equipo"), ("comunidad", "equipo"),
          ("respeto", "corazon"), ("transparen", "escudo"), ("innova", "estrella"), ("equidad", "check")]
CICLO = ["check", "estrella", "escudo", "equipo", "reloj", "corazon", "grafico", "documento"]


def icono(titulo, i):
    k = C.clave(titulo)
    for p, ic in ICONOS:
        if p in k:
            return ic
    return CICLO[i % len(CICLO)]


def etiquetas(ws):
    """Filas 'Etiqueta | Valor' (columna A | columna B) de una hoja simple."""
    d = {}
    for r in ws.iter_rows(values_only=True):
        if r and r[0] and len(r) > 1:
            d[C.clave(C.txt(r[0]))] = C.txt(r[1])
    return d


def tomar(d, *pal):
    for k, v in d.items():
        if any(k.startswith(p) for p in pal):
            return v
    return ""


def secciones(ws):
    """Hoja de portal: bloques que empiezan con una celda '▸ NOMBRE' en la columna A; la fila siguiente es el
    encabezado y luego vienen los datos hasta el próximo '▸'."""
    out, actual, cab = {}, None, None
    for r in ws.iter_rows(values_only=True):
        a = C.txt(r[0]) if r else ""
        if a.startswith("▸"):
            actual, cab = C.clave(a.lstrip("▸ ")), None
            out[actual] = []
            continue
        if actual is None:
            continue
        if cab is None:
            cab = [C.txt(x) for x in r]
            continue
        if any(C.txt(x) for x in r):
            out[actual].append([C.txt(x) for x in r])
    return out


def nosotros(ws, nombre_portal):
    S = secciones(ws)
    t = {C.clave(f[0]): (f[1] if len(f) > 1 else "") for f in S.get("textos", []) if f and f[0]}
    g = lambda *p: next((v for k, v in t.items() if any(k.startswith(x) for x in p)), "")
    bl = []
    mv = [x for x in ({"titulo": "Misión", "icono": "mision", "texto": g("mision")},
                      {"titulo": "Visión", "icono": "vision", "texto": g("vision")}) if x["texto"]]
    if mv:
        bl.append({"tipo": "tarjetas", "columnas": 2, "items": mv})
    grupos, previo = [], "Líneas de trabajo"
    for f in S.get("tarjetas", []):
        grupo, tit, tx = (f + ["", "", ""])[:3]
        if not tit:
            continue
        grupo = grupo or previo
        previo = grupo
        if not grupos or grupos[-1]["titulo"] != grupo:
            grupos.append({"tipo": "tarjetas", "titulo": grupo, "columnas": 3, "compacto": True, "items": []})
        grupos[-1]["items"].append({"titulo": tit, "icono": icono(tit, len(grupos[-1]["items"])), "texto": tx})
    obj = g("objetivo")
    cifras = [{"valor": (f + ["", "", ""])[0], "etiqueta": (f + ["", "", ""])[1], **({"detalle": f[2]} if len(f) > 2 and f[2] else {})}
              for f in S.get("cifras", []) if f and f[0]]
    if grupos:
        bl.append(grupos[0])
    if obj:
        bl.append({"tipo": "destacado", "titulo": g("titulo del objetivo") or "Objetivo institucional", "icono": "objetivo", "texto": obj})
    if cifras:
        b = {"tipo": "cifras", "titulo": g("titulo de cifras") or "En cifras", "items": cifras}
        if g("introduccion de cifras"):
            b["intro"] = g("introduccion de cifras")
        bl.append(b)
    bl.extend(grupos[1:])
    funciones = [f[0] for f in S.get("funciones", []) if f and f[0]]
    if funciones:
        b = {"tipo": "lista", "titulo": g("titulo de funciones") or "Funciones", "mostrar": 6, "items": funciones}
        if g("introduccion de funciones"):
            b["intro"] = g("introduccion de funciones")
        bl.append(b)
    eq = [f for f in S.get("equipo", []) if f and f[0]]
    if eq:
        bl.append({"tipo": "equipo", "titulo": g("titulo del equipo") or "Equipo técnico",
                   "items": [{"nombre": f[0], "cargo": " · ".join(x for x in ((f + ["", "", ""])[2], (f + ["", "", ""])[1]) if x),
                              **({"destacado": True} if i == 0 else {})} for i, f in enumerate(eq)]})
    return bl


def main():
    print("Institucional:")
    if not os.path.isfile(XL):
        C.aviso("No existe data/SIVISA_INSTITUCIONAL.xlsx; se mantiene lo publicado.")
        return
    from openpyxl import load_workbook
    wb = load_workbook(XL, data_only=True)
    inst = {"actualizado": datetime.date.today().isoformat()}
    try:
        p = etiquetas(wb["Portada"])
        inst["mision"], inst["vision"] = tomar(p, "mision"), tomar(p, "vision")
        sobre = {"titulo": tomar(p, "titulo del bloque"), "texto": tomar(p, "texto del bloque"),
                 "puntos": [v for k, v in p.items() if k.startswith("punto") and v]}
        if sobre["texto"]:
            inst["sobre"] = sobre
        inst["sede"] = {"titulo": "Sede institucional", "direccion": tomar(p, "direccion"), "correo": tomar(p, "correo"),
                        "telefono": tomar(p, "telefono"), "horario": tomar(p, "horario")}
    except Exception as e:
        C.aviso("Hoja Portada: %s" % e)
    try:
        ws = wb["Autoridades"]
        filas = [[C.txt(x) for x in r] for r in ws.iter_rows(values_only=True)]
        aut, contacto, modo = [], {}, None
        for f in filas:
            a = f[0] if f else ""
            if a.startswith("▸"):
                modo = C.clave(a.lstrip("▸ "))
                continue
            if modo and modo.startswith("autoridades") and a and len(f) > 1 and f[1] and C.clave(a) != "cargo":
                aut.append({"cargo": a, "nombre": f[1]})
            if modo and modo.startswith("contacto") and a and len(f) > 1:
                contacto[C.clave(a)] = f[1]
        inst["autoridades"] = aut
        inst["contacto"] = {"nombre": tomar(contacto, "nombre"), "cargo": tomar(contacto, "cargo"),
                            "area": tomar(contacto, "area"), "correo": tomar(contacto, "correo"), "foto": ""}
    except Exception as e:
        C.aviso("Hoja Autoridades: %s" % e)
    try:
        resp = {}
        for r in wb["Responsables"].iter_rows(min_row=4, values_only=True):
            pid = PORTAL_ID.get(C.clave(C.txt(r[0])))
            if pid and C.txt(r[2]):
                resp[pid] = {"titulo": C.txt(r[1]) or "Responsable", "nombre": C.txt(r[2]), "cargo": C.txt(r[3]), "correo": C.txt(r[4])}
        inst["responsables"] = resp
    except Exception as e:
        C.aviso("Hoja Responsables: %s" % e)
    with open(os.path.join(RAIZ, "data", "institucional.js"), "w", encoding="utf-8") as f:
        f.write("/* Generado por herramientas/institucional.py desde data/SIVISA_INSTITUCIONAL.xlsx. No editar a mano.\n"
                "   Se aplica encima de data/sitio.js. */\n(function () {\n  var I = %s;\n"
                "  var S = window.SITIO = window.SITIO || {};\n"
                "  if (I.mision) S.mision = I.mision; if (I.vision) S.vision = I.vision;\n"
                "  if (I.sobre) S.sobre = I.sobre;\n"
                "  if (I.sede && I.sede.direccion) S.sede = I.sede;\n"
                "  if (I.autoridades && I.autoridades.length) S.autoridades = I.autoridades;\n"
                "  if (I.contacto && I.contacto.nombre) S.contacto = I.contacto;\n"
                "  (S.portales || []).forEach(function (p) { var r = (I.responsables || {})[p.id]; if (r) p.responsable = r; });\n"
                "})();\n" % json.dumps(inst, ensure_ascii=False, indent=1))
    print("  portada, %d autoridades, %d responsables" % (len(inst.get("autoridades", [])), len(inst.get("responsables", {}))))
    for hoja, carpeta, titulo in (("Epidemiología", "epidemiologia", "Oficina de Epidemiología"), ("Salud Ambiental", "salud-ambiental", "Salud Ambiental")):
        try:
            bl = nosotros(wb[hoja], titulo)
            if not bl:
                C.aviso("Hoja %s vacía; se mantiene el Nosotros publicado." % hoja)
                continue
            with open(os.path.join(RAIZ, carpeta, "data", "nosotros.js"), "w", encoding="utf-8") as f:
                f.write("/* Generado por herramientas/institucional.py desde la hoja \"%s\" de data/SIVISA_INSTITUCIONAL.xlsx. No editar a mano. */\n"
                        "window.PAGINAS = window.PAGINAS || {};\nwindow.PAGINAS.nosotros = %s;\n" % (hoja, json.dumps(bl, ensure_ascii=False, indent=1)))
            print("  Nosotros %s: %d bloques" % (hoja, len(bl)))
        except Exception as e:
            C.aviso("Hoja %s: %s (se mantiene lo publicado)" % (hoja, e))


if __name__ == "__main__":
    main()
