"""Funciones comunes de SIVISA para leer plantillas Excel.

- Actividades (PROMSA, Epidemiología y Salud Ambiental): misma hoja, mismas columnas, textos libres
  con normalización (mayúscula inicial, sin espacios dobles ni punto final) y agrupación de variantes.
- Fotos: se encuentran aunque la extensión cambie (.jpg/.jpeg/.png, mayúsculas o minúsculas).
Solo se publican datos agregados y descripciones sin nombres de personas.
"""
import datetime, json, os, re, unicodedata

EXT_FOTO = (".jpg", ".jpeg", ".png", ".webp")
DNI = re.compile(r"\b\d{8}\b")
MAX_CORTO = 60


def txt(v):
    return re.sub(r"\s+", " ", str(v)).strip() if v is not None else ""


def num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return None


def fecha(v):
    if isinstance(v, datetime.datetime):
        return v.date().isoformat()
    if isinstance(v, datetime.date):
        return v.isoformat()
    s = txt(v)
    m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", s)
    if m:
        return "%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1)))
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))) if m else ""


def mes(v):
    """Devuelve AAAA-MM a partir de una fecha, '2026-10', '10/2026' u 'octubre 2026'."""
    if isinstance(v, (datetime.date, datetime.datetime)):
        return "%04d-%02d" % (v.year, v.month)
    s = txt(v).lower()
    m = re.match(r"(\d{4})[-/](\d{1,2})", s)
    if m:
        return "%s-%02d" % (m.group(1), int(m.group(2)))
    m = re.match(r"(\d{1,2})[-/](\d{4})", s)
    if m:
        return "%s-%02d" % (m.group(2), int(m.group(1)))
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"]
    s2 = s.replace("septiembre", "setiembre")
    for i, n in enumerate(meses):
        if s2.startswith(n) or s2.startswith(n[:3] + " ") or s2.startswith(n[:3] + "-"):
            a = re.search(r"(\d{4})", s2)
            if a:
                return "%s-%02d" % (a.group(1), i + 1)
    return ""


def aviso(m):
    print("  ! " + m)


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def clave(s):
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes(s.lower())).strip()


def normal(s):
    """Texto corto estandarizado: sin espacios dobles ni punto final; si viene TODO EN MAYÚSCULAS o
    todo en minúsculas, se deja con mayúscula inicial. Las siglas cortas (I.E., EE.SS.) se respetan."""
    s = txt(s).rstrip(" .;,")
    if not s:
        return ""
    letras = [c for c in s if c.isalpha()]
    if letras and (all(c.isupper() for c in letras) and len(letras) > 6 or all(c.islower() for c in letras)):
        s = s.lower()
    return s[:1].upper() + s[1:]


class Agrupador:
    """Une variantes que solo difieren en mayúsculas, tildes o signos: se muestra la primera forma vista."""

    def __init__(self):
        self.vistos = {}

    def __call__(self, s, campo="", fila=""):
        s = normal(s)
        if not s:
            return ""
        if len(s) > MAX_CORTO:
            aviso("%s demasiado largo (%d caracteres, máx. %d) %s: %s…" % (campo, len(s), MAX_CORTO, fila, s[:40]))
        k = clave(s)
        return self.vistos.setdefault(k, s)


def buscar_foto(nombre, carpeta):
    """Devuelve el nombre real del archivo en `carpeta` que corresponde a `nombre`, tolerando la extensión
    (.jpg/.jpeg/.png/.webp) y mayúsculas. '' si no existe."""
    nombre = txt(nombre)
    if not nombre or not os.path.isdir(carpeta):
        return ""
    base = os.path.splitext(nombre)[0] if os.path.splitext(nombre)[1].lower() in EXT_FOTO else nombre
    kb = clave(base)
    for f in sorted(os.listdir(carpeta)):
        b, e = os.path.splitext(f)
        if e.lower() in EXT_FOTO and clave(b) == kb:
            return f
    return ""


def nombre_mr(s):
    return txt(s).upper().replace("MCR ", "").replace("MICRORED ", "").replace("MICRORRED ", "").strip()


def leer_actividades(ws, carpeta_fotos, fila_cab=3):
    """Lee una hoja 'Actividades' con encabezados en la fila `fila_cab` (columnas reconocidas por su nombre).
    Columnas: Fecha, Microred, Distrito, Escenario, Tipo de actividad, Tema, N° participantes, Descripción,
    Foto y, opcional, Emergencia."""
    cab = [clave(txt(c.value)) for c in ws[fila_cab]]

    def col(*pal):
        for i, h in enumerate(cab):
            if any(h.startswith(p) for p in pal):
                return i
        return None

    C = {"fecha": col("fecha"), "mr": col("microred", "microrred"), "dist": col("distrito"), "esc": col("escenario"),
         "tipo": col("tipo"), "tema": col("tema"), "part": col("n participantes", "participantes", "no participantes"),
         "desc": col("descripcion"), "foto": col("foto"), "emerg": col("emergencia")}
    g_tipo, g_tema, g_esc, g_em = Agrupador(), Agrupador(), Agrupador(), Agrupador()
    acts = []
    for n, r in enumerate(ws.iter_rows(min_row=fila_cab + 1, values_only=True), fila_cab + 1):
        def v(k):
            i = C[k]
            return r[i] if i is not None and i < len(r) else None
        if not any(x not in (None, "") for x in r[:10]):
            continue
        f, desc = fecha(v("fecha")), txt(v("desc"))
        donde = "(fila %d)" % n
        if not f:
            aviso("Actividades: fila %d sin fecha válida; se omite." % n)
            continue
        if DNI.search(desc):
            aviso("Actividades: la descripción de la fila %d parece tener un DNI; se omite." % n)
            continue
        foto_pedida = txt(v("foto"))
        foto = buscar_foto(foto_pedida, carpeta_fotos)
        if foto_pedida and not foto:
            aviso("Foto no encontrada en %s: %s" % (os.path.basename(carpeta_fotos.rstrip("/\\")) or "fotos", foto_pedida))
        tipo = g_tipo(v("tipo"), "Tipo de actividad", donde)
        if clave(tipo) in ("otra", "otro", "otras", "otros"):
            tipo = ""
        tema = g_tema(v("tema"), "Tema", donde)
        if clave(tema) in ("otra", "otro"):
            tema = ""
        acts.append({"fecha": f, "microred": nombre_mr(v("mr")), "distrito": normal(v("dist")),
                     "escenario": g_esc(v("esc"), "Escenario", donde), "tipo": tipo, "tema": tema,
                     "participantes": int(num(v("part")) or 0), "descripcion": desc[:300], "foto": foto,
                     "emergencia": g_em(v("emerg"), "Emergencia", donde) if C["emerg"] is not None else ""})
    acts.sort(key=lambda a: a["fecha"], reverse=True)
    return acts


def escribir_js(ruta, variable, datos, comentario):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("/* %s No editar a mano. */\nwindow.%s = %s;\n" % (comentario, variable, json.dumps(datos, ensure_ascii=False, separators=(",", ":"))))
