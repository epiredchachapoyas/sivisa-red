"""SIVISA · Tableros de vigilancia de toda la Red (versión Python de epidemiologia/preparar_vigilancia.R).

Lee las bases NotiSP de la carpeta BASES_NOTISP (al lado de la carpeta del portal) y escribe
epidemiologia/data/vigilancia_red.js. Solo publica CONTEOS agregados: ningún nombre, DNI ni dirección.

    <carpeta>\\BASES_NOTISP\\2026\\      bases del año (edas, iras, febril(es), individual .csv;
                                         lesiones…transito .xlsx, diabetes .xlsx; opcionales: mnp, vfamiliar,
                                         brotes (+ brotes_indicadores) .csv, Depresion, Psicotico, suicidio .xls)
    <carpeta>\\BASES_NOTISP\\Maestros\\  establecimientos, microredes, distritos, provincias, departamentos,
                                         enfermedades, localidades (.csv)
Se usa la carpeta del año más reciente (2026, 2027…).

Uso:  python herramientas/vigilancia.py [ruta_BASES_NOTISP]
Requiere pandas y openpyxl.
"""
import datetime as dt
import json, math, os, re, sys, unicodedata
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "epidemiologia", "data", "vigilancia_red.js")
SUBREG, RED = "36", "01"
AMBITO = "Red Integrada de Salud Chachapoyas"


class Falta(Exception):
    pass


# ---------------- Utilidades ----------------
def ubicar_bases(arg=None):
    cands = [arg] if arg else []
    cands += [os.path.join(os.path.dirname(RAIZ), "BASES_NOTISP"), os.path.join(RAIZ, "..", "BASES_NOTISP")]
    for c in cands:
        if c and os.path.isdir(c):
            base = os.path.abspath(c)
            anios = sorted(d for d in os.listdir(base) if re.fullmatch(r"\d{4}", d) and os.path.isdir(os.path.join(base, d)))
            if not anios:
                raise Falta("Dentro de %s falta la carpeta del año (por ejemplo 2026)." % base)
            return os.path.join(base, anios[-1]), os.path.join(base, "Maestros")
    raise Falta("No existe la carpeta BASES_NOTISP al lado de la carpeta del portal.")


def busca(carpeta, patron, obligatorio=True):
    rx = re.compile(patron, re.I)
    f = sorted(x for x in os.listdir(carpeta) if rx.search(x) and not x.startswith("~$"))
    if not f:
        if obligatorio:
            raise Falta("No se encontró %s en %s" % (patron, carpeta))
        return None
    return os.path.join(carpeta, f[-1])


def lee_csv(f):
    for enc in ("utf-8-sig", "latin1"):
        try:
            d = pd.read_csv(f, dtype=str, keep_default_na=False, na_values=["NA"], encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    d.columns = [str(c).strip().upper() for c in d.columns]
    return d


def _texto(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, dt.datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def lee_xls(f):
    from openpyxl import load_workbook
    wb = load_workbook(f, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    cab = [str(c).strip().upper() if c is not None else "" for c in next(it)]
    filas = [[_texto(v) for v in r] for r in it if any(v not in (None, "") for v in r)]
    wb.close()
    n = len(cab)
    return pd.DataFrame([(r + [None] * n)[:n] for r in filas], columns=cab)


def col(d, c):
    return d[c] if c in d.columns else pd.Series([None] * len(d), index=d.index, dtype=object)


def num1(s):
    return pd.to_numeric(s, errors="coerce")


def num(d, cols):
    cols = [c for c in cols if c in d.columns]
    if not cols:
        return pd.Series(0.0, index=d.index)
    return sum(num1(d[c]).fillna(0) for c in cols)


def limpio(s):
    return s.fillna("").astype(str).str.strip()


def titulo(s):
    s = re.sub(r"\s+", " ", str(s if s is not None else "").strip().lower())
    s = re.sub(r"(^|[\s\-/(.])(\w)", lambda m: m.group(1) + m.group(2).upper(), s)
    for a, b in ((" De ", " de "), (" Del ", " del "), (" La ", " la "), (" Y ", " y "), ("Maria", "María"),
                 ("Tomas", "Tomás"), ("Fatima", "Fátima"), ("Asuncion", "Asunción")):
        s = s.replace(a, b)
    return s


def inicio_se1(a):
    d = dt.date(a, 1, 1)
    dow = (d.weekday() + 1) % 7          # domingo = 0
    ini = d - dt.timedelta(days=dow)
    return ini if dow <= 3 else ini + dt.timedelta(days=7)


def se_de(f):
    if f is None or (isinstance(f, float) and math.isnan(f)) or f is pd.NaT:
        return None, None
    a = f.year
    if f < inicio_se1(a):
        a -= 1
    elif f >= inicio_se1(a + 1):
        a += 1
    return a, (f - inicio_se1(a)).days // 7 + 1


def fecha(s, formato=None):
    s = "" if s is None else str(s).strip()
    if not s:
        return None
    for fm in ([formato] if formato else []) + ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
        try:
            return dt.datetime.strptime(s[:10], fm).date()
        except ValueError:
            pass
    return None


def q(x, p):
    x = sorted(x)
    if not x:
        return None
    h = (len(x) - 1) * p          # cuantil tipo 7 (el de R por defecto)
    lo = math.floor(h)
    v = x[lo] + (h - lo) * ((x[lo + 1] if lo + 1 < len(x) else x[lo]) - x[lo])
    return int(v) if float(v).is_integer() else round(v, 10)


def entero(v):
    return int(round(v))


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def items(serie, orden=None):
    cnt = serie.value_counts()
    if orden is not None:
        return [[k, int(cnt.get(k, 0))] for k in orden]
    cnt = sorted(cnt.items(), key=lambda kv: (-kv[1], str(kv[0])))
    return [[k, int(v)] for k, v in cnt]


def rep_na(s, de=None, a=None):
    s = s.fillna("").astype(str)
    s = s.where(s != "", "Sin dato")
    if de:
        s = s.replace(dict(zip(de, a)))
    return s


# ---------------- Principal ----------------
def generar(ruta_bases=None):
    RUTA_BASES, RUTA_MAESTROS = ubicar_bases(ruta_bases)
    print("Bases: %s | Maestros: %s" % (RUTA_BASES, RUTA_MAESTROS))

    E = lee_csv(busca(RUTA_MAESTROS, r"establecimientos.*\.csv$"))
    E = E[(E["SUBREGION"] == SUBREG) & (E["RED"] == RED)]
    M = lee_csv(busca(RUTA_MAESTROS, r"microredes.*\.csv$"))
    M = M[(M["SUBREGION"] == SUBREG) & (M["RED"] == RED)]
    DI = lee_csv(busca(RUTA_MAESTROS, r"distritos.*\.csv$"))
    PR = lee_csv(busca(RUTA_MAESTROS, r"provincias.*\.csv$"))
    DP = lee_csv(busca(RUTA_MAESTROS, r"departamentos.*\.csv$"))
    EN = lee_csv(busca(RUTA_MAESTROS, r"enfermedades.*\.csv$"))
    nom_mr = {c: titulo(n) for c, n in zip(M["CODIGO"], M["NOMBRE"])}
    nom_mr["99"] = "Hospital Regional Virgen de Fátima"
    nom_es = {c: titulo(n if str(n).strip() else r) for c, n, r in zip(E["COD_EST"], E["NOMBRE"].fillna(""), E["RAZ_SOC"].fillna(""))}
    mr_es = dict(zip(E["COD_EST"], E["MICRORED"]))
    cie_nom = {str(c).strip(): str(n).strip() for c, n in zip(EN["CIE_10"], EN["DIAGNO"])}
    di_nom = dict(zip(DI["UBIGEO"], DI["NOMBRE"]))
    pr_nom = dict(zip(PR["UBIGEO"], PR["NOMBRE"]))
    dp_nom = dict(zip(DP["UBIGEO"], DP["NOMBRE"]))

    def nom_dist(u):
        u = str(u if u is not None else "").strip()
        if u not in di_nom:
            return u if u else "Sin dato"
        pv = titulo(pr_nom.get(u[:4], ""))
        if u.startswith("01"):
            return "%s (%s)" % (titulo(di_nom[u]), pv)
        return "%s (%s, %s)" % (titulo(di_nom[u]), pv, titulo(dp_nom.get(u[:2], "")))

    def prep(d, ano, se, es):
        d = d.copy()
        d["ANO"] = num1(col(d, ano))
        d["SEMANA"] = num1(col(d, se))
        d["E_SALUD"] = limpio(col(d, es))
        base_mr = limpio(d["MICRORED"]) if "MICRORED" in d.columns else pd.Series("", index=d.index)
        conocido = d["E_SALUD"].map(mr_es)
        d["MR"] = conocido.where(conocido.notna(), base_mr)
        for e, m in zip(d.loc[conocido.isna(), "E_SALUD"], d.loc[conocido.isna(), "MR"]):
            mr_es.setdefault(e, m)
        d = d[d["ANO"].notna() & d["SEMANA"].notna() & (d["SEMANA"] >= 1) & (d["SEMANA"] <= 53)].copy()
        d["ANO"] = d["ANO"].astype(int)
        d["SEMANA"] = d["SEMANA"].astype(int)
        return d

    def serie_de(d, v, anios):
        out = {}
        for a in anios:
            x = [0] * 53
            s = d[d["ANO"] == a]
            for w, t in s.groupby("SEMANA")[v].sum().items():
                x[int(w) - 1] = entero(t)
            out[str(a)] = x
        return out

    def series(d, v):
        anios = sorted(d["ANO"].unique())
        res = {"TOTAL": serie_de(d, v, anios)}
        for k in sorted(x for x in d["MR"].dropna().unique() if x != ""):
            res["MR" + k] = serie_de(d[d["MR"] == k], v, anios)
        for k in sorted(x for x in d["E_SALUD"].unique() if x != ""):
            s = d[d["E_SALUD"] == k]
            if s[v].sum() > 0:
                res[k] = serie_de(s, v, anios)
        return res

    def edad_tabla(d, grupos, se):
        out = {}
        for a in sorted(d["ANO"].unique()):
            s = d[(d["ANO"] == a) & (d["SEMANA"] <= se)]
            out[str(a)] = [entero(num(s, c if isinstance(c, list) else [c]).sum()) for c in grupos.values()]
        return {"grupos": list(grupos), "anios": out}

    def suma(d, cols):
        return entero(num(d, cols).sum())

    def empiezan(d, rx):
        return [c for c in d.columns if re.match(rx, c)]

    # ---------- EDA, IRA, febriles ----------
    eda = prep(lee_csv(busca(RUTA_BASES, r"edas.*\.csv$")), "ANO", "SEMANA", "E_SALUD")
    ANIO = int(eda["ANO"].max())
    eda["V"] = num(eda, empiezan(eda, r"^DAA_C"))
    eda["DIS"] = num(eda, empiezan(eda, r"^DIS_C"))
    se_eda = int(eda.loc[eda["ANO"] == ANIO, "SEMANA"].max())
    cur = eda[eda["ANO"] == ANIO]
    mod_eda = {"titulo": "EDA acuosa", "corto": "EDA", "unidad": "episodios", "tasa_k": 0, "se_corte": se_eda, "series": series(eda, "V"),
               "edad": edad_tabla(eda, {"< 1 a": "DAA_C1", "1-4 a": "DAA_C1_4", "5-11 a": "DAA_C5_11", "12-17 a": "DAA_C12_17",
                                        "18-29 a": "DAA_C18_29", "30-59 a": "DAA_C30_59", "60+ a": "DAA_C60"}, se_eda),
               "extra": {"Disentéricas": entero(cur["DIS"].sum()),
                         "Hospitalizados": suma(cur, empiezan(cur, r"^(DAA|DIS)_H")),
                         "Defunciones": suma(cur, empiezan(cur, r"^(DAA|DIS)_D"))},
               "fuente": "NotiSP – notificación colectiva semanal de EDA"}

    ira = prep(lee_csv(busca(RUTA_BASES, r"iras.*\.csv$")), "ANO", "SEMANA", "E_SALUD")
    ira["V"] = num(ira, ["IRA_M2", "IRA_2_11", "IRA_1_4A"])
    se_ira = int(ira.loc[ira["ANO"] == ANIO, "SEMANA"].max())
    cur = ira[ira["ANO"] == ANIO]
    mod_ira = {"titulo": "IRA en menores de 5 años", "corto": "IRA < 5 años", "unidad": "episodios", "tasa_k": 0, "se_corte": se_ira,
               "series": series(ira, "V"), "edad": edad_tabla(ira, {"< 2 m": "IRA_M2", "2-11 m": "IRA_2_11", "1-4 a": "IRA_1_4A"}, se_ira),
               "extra": {"Neumonías < 5 a": suma(cur, ["NEU_2_11", "NEU_1_4A", "NGR_M2", "NGR_2_11", "NGR_1_4A"]),
                         "Neumonías 5 a y más": suma(cur, ["NEU_5_9A", "NEU_10_19", "NEU_20_59", "NEU_60A", "NGR_5_9A", "NGR_60A"]),
                         "SOB/asma < 5 a": suma(cur, ["SOB_2A", "SOB_2_4A"]),
                         "Defunciones por neumonía": suma(cur, empiezan(cur, r"^(DIH|DEH)_"))},
               "fuente": "NotiSP – notificación colectiva semanal de IRA"}

    feb = prep(lee_csv(busca(RUTA_BASES, r"febril.*\.csv$")), "ANO", "SEMANA", "E_SALUD")
    feb["V"] = num(feb, ["FEB_TOT"])
    se_feb = int(feb.loc[feb["ANO"] == ANIO, "SEMANA"].max())
    mod_feb = {"titulo": "Síndrome febril", "corto": "Febriles", "unidad": "casos", "tasa_k": 0, "se_corte": se_feb, "series": series(feb, "V"),
               "edad": edad_tabla(feb, {"< 1 a": "FEB_M1", "1-4 a": "FEB_1_4", "5-9 a": "FEB_5_9", "10-19 a": "FEB_10_19",
                                        "20-59 a": "FEB_20_59", "60+ a": "FEB_M60"}, se_feb),
               "fuente": "NotiSP – vigilancia de febriles"}
    SE = max(se_eda, se_ira, se_feb)

    # ---------- Individuales ----------
    CURSOS = ["Niño (0-11)", "Adolescente (12-17)", "Joven (18-29)", "Adulto (30-59)", "Adulto mayor (60+)"]

    def curso(e):
        e = num1(e)
        return pd.cut(e, [-1, 11, 17, 29, 59, 200], labels=CURSOS).astype(object)

    def caract(d, formas=None, dias=None):
        dd = [float(x) for x in d[dias].dropna()] if dias else []
        return {"n": len(d), "sexo": {"Masculino": int((d["SEXO_N"] == "M").sum()), "Femenino": int((d["SEXO_N"] == "F").sum())},
                "curso": [int((d["CURSO"] == c).sum()) for c in CURSOS],
                "forma": {k: int((d["DIAGNOSTIC"] == v).sum()) for k, v in formas.items()} if formas else {},
                "dias_mediana": q(dd, .5), "dias_q1": q(dd, .25), "dias_q3": q(dd, .75)}

    VACIO = {"n": 0, "sexo": {"Masculino": 0, "Femenino": 0}, "curso": [0] * 5, "forma": {}, "dias_mediana": None, "dias_q1": None, "dias_q3": None}

    def residencia(d, c):
        t = d.loc[d["ANO"] == ANIO, c].fillna("").astype(str)
        cnt = sorted(t.value_counts().items(), key=lambda kv: (-kv[1], kv[0]))
        return {"anios": [str(ANIO)], "filas": [{"ubigeo": u, "nombre": nom_dist(u), "casos": [int(n)]} for u, n in cnt]}

    def modulo_ind(nombre, X, fuente, formas=None, dias=None, res_col="UBIGEO", distrib=None, extra=None, unidad="casos"):
        X = X.copy()
        X["V"] = 1
        return {"titulo": nombre, "corto": nombre, "unidad": unidad, "tasa_k": 0, "se_corte": SE, "series": series(X, "V"), "individual": True,
                "caract": {"actual": caract(X[X["ANO"] == ANIO], formas, dias), "historico": VACIO},
                "curso_grupos": CURSOS, "residencia": residencia(X, res_col), "distrib": distrib or [], "extra": extra or {}, "fuente": fuente}

    ind = prep(lee_csv(busca(RUTA_BASES, r"individual.*\.csv$")), "ANO", "SEMANA", "E_SALUD")
    ind["DIAGNOSTIC"] = limpio(ind["DIAGNOSTIC"]).str.upper()
    ind["TIPO_DX"] = ind["TIPO_DX"].fillna("")
    ind["CURSO"] = curso(num1(ind["EDAD"]).where(ind["TIPO_EDAD"] == "A", 0))
    ind["SEXO_N"] = ind["SEXO"].fillna("").str.upper().str[:1]
    fn = pd.to_datetime(ind["FECHA_NOT"].fillna("").str[:10], errors="coerce", format="%Y-%m-%d")
    fi = pd.to_datetime(ind["FECHA_INI"].fillna("").str[:10], errors="coerce", format="%Y-%m-%d")
    ind["DIAS"] = (fn - fi).dt.days
    CLASIF = {"C": "Confirmado", "P": "Probable", "D": "Descartado"}

    EVENTOS = [
        ("leish", "Leishmaniasis", r"^B55", "metaxenicas", True, {"Cutánea (B55.1)": "B55.1", "Mucocutánea (B55.2)": "B55.2"}),
        ("dengue", "Dengue", r"^A97", "metaxenicas", True, {"Sin signos de alarma (A97.0)": "A97.0", "Con signos de alarma (A97.1)": "A97.1", "Grave (A97.2)": "A97.2"}),
        ("carrion", "Enfermedad de Carrión", r"^A44", "metaxenicas", False, None),
        ("chagas", "Enfermedad de Chagas", r"^B57", "metaxenicas", False, None),
        ("malaria", "Malaria", r"^B5[0-4]", "metaxenicas", False, None),
        ("zika", "Zika", r"^U06", "metaxenicas", False, None),
        ("chikungunya", "Chikungunya", r"^A92\.0", "metaxenicas", False, None),
        ("leptospirosis", "Leptospirosis", r"^A27", "zoonosis", True, None),
        ("ofidismo", "Ofidismo", r"^X20", "zoonosis", False, None),
        ("loxoscelismo", "Loxoscelismo", r"^X21", "zoonosis", False, None),
        ("rabia", "Rabia", r"^A82", "zoonosis", False, None),
        ("peste", "Peste", r"^A20", "zoonosis", False, None),
        ("varicela", "Varicela", r"^B01", "inmunoprevenibles", True, {"Con otras complicaciones (B01.8)": "B01.8", "Sin complicaciones (B01.9)": "B01.9"}),
        ("sarampion", "Sarampión", r"^B05", "inmunoprevenibles", False, None),
        ("rubeola", "Rubéola", r"^B06", "inmunoprevenibles", False, None),
        ("parotiditis", "Parotiditis", r"^B26", "inmunoprevenibles", False, None),
        ("tosferina", "Tos ferina", r"^A37", "inmunoprevenibles", False, None),
        ("pfa", "Parálisis flácida aguda", r"^G83", "inmunoprevenibles", False, None),
        ("tb", "Tuberculosis", r"^A1[5-9]", "tbc-vih", False, None),
        ("vih", "VIH/Sida", r"^B2[0-4]", "tbc-vih", False, None),
        ("sifilis", "Sífilis", r"^A5[0-3]", "tbc-vih", False, None),
        ("hepb", "Hepatitis B", r"^B16", "tbc-vih", False, None),
        ("muerte_materna", "Muerte materna", r"^O9[56]", "materno-perinatal", False, None),
        ("sifilis_materna", "Sífilis materna", r"^O98\.1", "materno-perinatal", False, None),
        ("plaguicidas", "Intoxicación por plaguicidas", r"^T60", "no-transmisibles", False, None)]

    def ficha_evento(id_, nombre, T, X, unidad, modulo):
        ult = None
        if len(X):
            u = X.sort_values(["ANO", "SEMANA"], kind="stable").iloc[-1]
            ult = {"anio": int(u["ANO"]), "se": int(u["SEMANA"])}
        pa = X["ANO"].value_counts().sort_index()
        return {"id": id_, "nombre": nombre, "cie": ", ".join(sorted(T["DIAGNOSTIC"].unique())), "unidad": unidad, "modulo": modulo,
                "por_anio": {str(k): int(v) for k, v in pa.items()},
                "confirmados": int((T["TIPO_DX"] == "C").sum()), "probables": int((T["TIPO_DX"] == "P").sum()), "total": len(X),
                "descartados": int((T["TIPO_DX"] == "D").sum()), "ultimo": ult}

    def defunciones(X):
        return int(((limpio(X["FECHA_DEF"]) != "") & (X["ANO"] == ANIO)).sum()) if "FECHA_DEF" in X.columns else 0

    modulos_ind, eventos = {}, []
    usados = pd.Series(False, index=ind.index)
    RED_UB = set(E["UBIGEO_RN"].dropna())
    MAPA = []

    def al_mapa(eid, d, col_ub, col_loc=None, valor=None):
        if not len(d):
            return
        MAPA.append(pd.DataFrame({"ev": eid, "ub": d[col_ub].fillna("").astype(str).values,
                                  "loc": (d[col_loc].fillna("").astype(str).values if col_loc else ""),
                                  "se": d["SEMANA"].values, "v": (d[valor].values if valor else 1)}))

    for eid, nombre, rx, unidad, propio, formas in EVENTOS:
        sel = ind["DIAGNOSTIC"].str.contains(rx, regex=True)
        if not sel.any():
            continue
        usados |= sel
        T = ind[sel]
        X = T[T["TIPO_DX"] != "D"]
        XA = X[X["ANO"] == ANIO]
        al_mapa(eid, XA, "UBIGEO", "LOCALCOD")
        aut = int(XA["UBIGEO"].isin(RED_UB).sum())
        fe = ficha_evento(eid, nombre, T, X, unidad, eid if propio else None)
        fe["autoctonos"], fe["importados"] = aut, len(XA) - aut
        fe["ultimo"] = fe.pop("ultimo")
        eventos.append(fe)
        if not propio:
            continue
        clas = T["TIPO_DX"].map(CLASIF).fillna("Sin dato")
        fuente = "NotiSP – notificación individual (%s), por establecimiento notificante" % ", ".join(sorted(T["DIAGNOSTIC"].unique()))
        modulos_ind[eid] = modulo_ind(nombre, X, fuente, formas, "DIAS", "UBIGEO",
                                      [{"titulo": "Clasificación del caso", "nota": "Incluye descartados, que no se cuentan en los gráficos.",
                                        "items": items(clas, ["Confirmado", "Probable", "Descartado"])}],
                                      {"Defunciones": defunciones(X)})
        modulos_ind[eid]["origen"] = {"autoctonos": aut, "importados": len(XA) - aut}
        for suf, sub in (("__aut", X[X["UBIGEO"].isin(RED_UB)]), ("__imp", X[~X["UBIGEO"].isin(RED_UB)])):
            if len(sub):
                modulos_ind[eid + suf] = modulo_ind(nombre, sub, fuente, formas, "DIAS", "UBIGEO", [], {"Defunciones": defunciones(sub)})
    for cie in sorted(ind.loc[~usados, "DIAGNOSTIC"].unique()):
        T = ind[~usados & (ind["DIAGNOSTIC"] == cie)]
        X = T[T["TIPO_DX"] != "D"]
        e = ficha_evento("cie_" + cie, titulo(cie_nom.get(cie, cie)), T, X, "otros", None)
        e["ultimo"] = None
        eventos.append(e)

    # ---------- Lesiones por accidente de tránsito ----------
    L = lee_xls(busca(RUTA_BASES, r"lesiones.*transito.*\.xlsx$"))
    s = [se_de(fecha(x, "%d/%m/%Y")) for x in col(L, "FEC_ACCD")]
    L["ANO_SE"] = [a for a, _ in s]
    L["SE_"] = [w for _, w in s]
    L = prep(L, "ANO_SE", "SE_", "COD_EESS")
    L = L[L["ANO"] == ANIO].copy()
    al_mapa("lesiones", L, "UBIGEO_AC")
    L["SEXO_N"] = L["SEXO"].fillna("").str.upper().str[:1]
    L["CURSO"] = curso(num1(L["EDAD"]).where(L["TIPO_EDAD"] == "A", 0))
    mod_les = modulo_ind("Lesiones por accidente de tránsito", L,
                         "Vigilancia de lesiones por accidentes de tránsito – fecha del accidente; por establecimiento que atendió",
                         res_col="UBIGEO_AC", unidad="lesionados",
                         distrib=[
                             {"titulo": "Gravedad (diagnóstico principal)", "items": items(rep_na(col(L, "DX1_CATEG"), ["Pot.Grave"], ["Potencialmente grave"]), ["Leve", "Potencialmente grave", "Grave", "Sin dato"])},
                             {"titulo": "Momento del accidente", "items": items(rep_na(col(L, "MOME_ACCID"), ["Manana"], ["Mañana"]), ["Madrugada", "Mañana", "Tarde", "Noche", "Sin dato"])},
                             {"titulo": "Día de la semana", "items": items(rep_na(col(L, "DIA_ACCD"), ["Miercoles", "Sabado"], ["Miércoles", "Sábado"]),
                                                                           ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])}],
                         extra={"Accidentes (eventos)": int(col(L, "EVENTO").nunique())})
    mod_les["nota_residencia"] = "Distrito donde ocurrió el accidente."

    # ---------- Diabetes ----------
    B = prep(lee_xls(busca(RUTA_BASES, r"diabetes.*\.xlsx$")), "ANO", "SEMANA", "EESS")
    B = B[B["ANO"] == ANIO].copy()
    al_mapa("diabetes", B, "UBIGEO_RES")
    B["SEXO_N"] = B["SEXO"].map({"1": "M", "2": "F"})
    B["CURSO"] = curso(B["EDAD"])
    hb = [x for x in num1(col(B, "HEMOGLIC")).dropna() if x > 0]
    comor = {"HTA": ["HTA"], "Obesidad": ["OBESIDAD"], "Dislipidemia": ["DISPLIDEMIA"], "Nefropatía": ["NEFROPATIA"], "Neuropatía": ["NEUROPATIA"],
             "Pie diabético sin amputación": ["SINAMPUTACION"], "Pie diabético con amputación": ["CONAMPUTACION"],
             "Retinopatía": ["NOPROLIFERATIVA", "PROLIFERATIVA"], "Enf. isquémica cardiaca": ["ENFISQUEMICA"], "Enf. cerebrovascular": ["ENFCEREBROVASCULAR"]}
    cm = sorted(((k, int((num(B, c) > 0).sum())) for k, c in comor.items()), key=lambda kv: -kv[1])
    mod_dm = modulo_ind("Diabetes", B, "Vigilancia centinela de diabetes – semana de captación; por establecimiento", res_col="UBIGEO_RES", unidad="casos",
                        distrib=[{"titulo": "Comorbilidades y complicaciones", "nota": "Casos de %d con cada condición registrada (un caso puede tener varias)." % ANIO,
                                  "items": [[k, v] for k, v in cm]},
                                 {"titulo": "Tipo de caso", "items": items(rep_na(col(B, "TCASO").map({"1": "Incidente (nuevo)", "2": "Prevalente"})))}],
                        extra={"Con HbA1c registrada": len(hb), "HbA1c < 7 % (controlados)": sum(1 for x in hb if x < 7)})
    mod_dm["nota_residencia"] = "Distrito de residencia."

    # ---------- Bases opcionales ----------
    extra_mod, extra_ev = {}, []

    def ficha_simple(id_, nombre, cie, unidad, d):
        return {"id": id_, "nombre": nombre, "cie": cie, "unidad": unidad, "modulo": id_, "por_anio": {str(ANIO): len(d)}, "total": len(d),
                "descartados": 0, "ultimo": {"anio": ANIO, "se": int(d["SEMANA"].max())} if len(d) else None}

    def si(d, c):
        return int((d[c].fillna("").astype(str).str.upper() == "S").sum()) if c in d.columns else 0

    def lista_cnt(v):
        return sorted(v, key=lambda x: -x[1])

    def cap(s):
        s = s.fillna("").astype(str).str.lower()
        return s.str[:1].str.upper() + s.str[1:]

    fm = busca(RUTA_BASES, r"mnp.*\.xlsx$", False)
    if fm:
        N = prep(lee_xls(fm), "ANIO", "SEMANA", "E_SALUD")
        N = N[N["ANO"] == ANIO].copy()
        N["SEXO_N"] = N["SEXO"].fillna("").str.upper().str[:1]
        N["CURSO"] = "Sin dato"
        N["DIAGNOSTIC"] = N["TIPO_MTE"]
        EG = rep_na(pd.cut(num1(N["EDADGES"]), [0, 27, 31, 36, 60], labels=["< 28 semanas", "28–31 semanas", "32–36 semanas", "37 semanas o más"]).astype(object))
        ME = rep_na(pd.cut(num1(N["MADRE_EDAD"]), [0, 17, 34, 60], labels=["Adolescente (< 18)", "18–34 años", "35 años o más"]).astype(object))
        m = modulo_ind("Muerte fetal y neonatal", N, "Vigilancia de muerte fetal y neonatal – semana de notificación; por establecimiento notificante",
                       res_col="UBIGEO_RES", unidad="defunciones",
                       distrib=[
                           {"titulo": "Grupo de causa básica", "items": items(rep_na(cap(col(N, "CATEGORIA")).replace("", None)))},
                           {"titulo": "Momento de la muerte", "items": items(rep_na(col(N, "MOMENTO").map({"1": "Anteparto", "2": "Intraparto", "3": "Posparto (neonatal)"})), ["Anteparto", "Intraparto", "Posparto (neonatal)"])},
                           {"titulo": "Peso al nacer", "items": items(rep_na(cap(col(N, "CATPESO2")).replace("", None)), ["Extremo bajo peso", "Muy bajo peso", "Bajo peso", "Normal", "Sin dato"])},
                           {"titulo": "Edad gestacional", "items": items(EG, ["< 28 semanas", "28–31 semanas", "32–36 semanas", "37 semanas o más", "Sin dato"])},
                           {"titulo": "Edad de la madre", "items": items(ME, ["Adolescente (< 18)", "18–34 años", "35 años o más", "Sin dato"])},
                           {"titulo": "Lugar del parto", "items": items(rep_na(col(N, "LUGAR_PAR").map({"PI": "Institucional", "PD": "Domiciliario"})))}],
                       extra={"Muertes neonatales": int((N["TIPO_MTE"] == "N").sum()), "Muertes fetales": int((N["TIPO_MTE"] == "F").sum()),
                              "Evitables (según registro)": int((col(N, "EVITABLE") == "SI").sum())})
        m["sin_curso"] = True
        m["nota_residencia"] = "Distrito de residencia de la madre."
        extra_mod["mnp"] = m
        al_mapa("mnp", N, "UBIGEO_RES")
        extra_ev.append(ficha_simple("mnp", "Muerte fetal y neonatal", "P00–P96 y otras", "materno-perinatal", N))

    fv = busca(RUTA_BASES, r"vfamiliar.*\.xlsx$", False)
    if fv:
        V = lee_xls(fv)
        s = [se_de(fecha(x)) for x in col(V, "FREG")]
        V["ANO_SE"] = [a for a, _ in s]
        V["SE_"] = [w for _, w in s]
        V = prep(V, "ANO_SE", "SE_", "ESTABLEC")
        V = V[V["ANO"] == ANIO].copy()
        V["SEXO_N"] = V["SEXO"].fillna("").str.upper().str[:1]
        V["CURSO"] = curso(num1(V["EDAD"]).where(V["T_EDAD"] == "A", 0))
        vinc = rep_na(col(V, "VINCULO")).str.replace("(a)", "", regex=False).str.replace("CONYUGUE", "CÓNYUGE", regex=False)
        vinc = vinc.str[:1] + vinc.str[1:].str.lower()
        m = modulo_ind("Violencia familiar", V, "Vigilancia de violencia familiar – fecha de registro; por establecimiento", res_col="UBIGEO2", unidad="casos",
                       distrib=[
                           {"titulo": "Tipo de violencia", "nota": "Un caso puede tener más de un tipo.",
                            "items": lista_cnt([["Psicológica", si(V, "PSICOL")], ["Física", si(V, "FISICA")], ["Sexual", si(V, "RELSEX")], ["Abandono", si(V, "ABAND")]])},
                           {"titulo": "Vínculo con la persona agresora", "items": items(vinc)},
                           {"titulo": "Circunstancias", "nota": "Casos con cada condición registrada (puede haber varias).",
                            "items": lista_cnt([["Agresor con alcohol", si(V, "ALCOHOL")], ["Agresor con drogas", si(V, "DROGA")], ["Ocurrió en la casa", si(V, "CASA")],
                                                ["Ocurrió en la calle", si(V, "CALLE")], ["Víctima gestante", si(V, "GESTA")], ["Primera vez", si(V, "PRIMVEZ")]])}],
                       extra={"Mujeres": int((V["SEXO_N"] == "F").sum()), "Derivados": si(V, "DERIVADO"), "Con denuncia policial": si(V, "DENUNPOLIC")})
        m["nota_residencia"] = "Distrito de residencia de la víctima."
        extra_mod["violencia"] = m
        al_mapa("violencia", V, "UBIGEO2", "LOCAL")
        extra_ev.append(ficha_simple("violencia", "Violencia familiar", "T74, Y05–Y07", "violencia", V))

    modulos = {"eda": mod_eda, "ira": mod_ira, "feb": mod_feb, **modulos_ind, "lesiones": mod_les, "diabetes": mod_dm, **extra_mod}

    # ---------- Salud mental (solo conteos de personas) ----------
    def lista_tsv(f):
        raw = open(f, "rb").read()
        for enc in ("utf-16", "utf-8-sig", "latin1"):
            try:
                txt = raw.decode(enc)
                if "\t" in txt:
                    break
            except UnicodeDecodeError:
                continue
        filas = [l.split("\t") for l in txt.splitlines() if l.strip()]
        cab = [c.strip().lstrip("﻿").upper() for c in filas[0]]
        return [dict(zip(cab, [x.strip() for x in r])) for r in filas[1:]]

    def unicos(x):
        vistos, out = set(), []
        for r in x:
            k = "|".join((r.get("APEPAT", ""), r.get("APEMAT", ""), r.get("NOMBRES", ""), r.get("DNI", ""))).upper()
            if k not in vistos:
                vistos.add(k)
                out.append(r)
        return out

    def fmt_es(v, d=1):
        s = ("{:,.%df}" % d).format(round(v, d))
        return s.replace(",", " ").replace(".", ",")

    registros = []
    f = busca(RUTA_BASES, r"Depresion.*\.xls", False)
    if f:
        x = unicos(lista_tsv(f))
        n = len(x)
        det = []
        if x and "1ER SEGUIMIENTO" in x[0]:
            seg = sum(1 for r in x if r.get("1ER SEGUIMIENTO", "").strip())
            det = [["Con primer seguimiento registrado", seg, fmt_es(seg / n * 100) + " % del registro"],
                   ["Sin primer seguimiento", n - seg, "pendientes de seguimiento"]]
        registros.append({"unidad": "salud-mental", "nombre": "Episodio depresivo moderado y grave", "n": n, "medida": "personas en el registro", "detalle": det})
    f = busca(RUTA_BASES, r"Psicotico.*\.xls", False)
    if f:
        x = unicos(lista_tsv(f))
        dias = []
        for r in x:
            m_ = re.match(r"^\D*(\d+)", r.get("FECHA", ""))
            if m_:
                dias.append(int(m_.group(1)))
        det = []
        if dias:
            det = [["Más de 1 año sin atención", sum(1 for d in dias if d > 365), "según días desde la última atención"],
                   ["Mediana desde la última atención", fmt_es(q(dias, .5), 0) + " días", ""]]
        registros.append({"unidad": "salud-mental", "nombre": "Primer episodio psicótico", "n": len(x), "medida": "personas en el registro", "detalle": det})
    f = busca(RUTA_BASES, r"suicidio.*\.xls", False)
    if f:
        registros.append({"unidad": "salud-mental", "nombre": "Intento de suicidio", "n": len(unicos(lista_tsv(f))), "medida": "personas en el registro", "detalle": []})

    eventos.append({"id": "lesiones", "nombre": "Lesiones por accidente de tránsito", "cie": "V01–V89", "unidad": "no-transmisibles", "modulo": "lesiones",
                    "por_anio": {str(ANIO): len(L)}, "total": len(L), "descartados": 0, "ultimo": {"anio": ANIO, "se": int(L["SEMANA"].max())}})
    eventos.append({"id": "diabetes", "nombre": "Diabetes", "cie": "E10–E14", "unidad": "no-transmisibles", "modulo": "diabetes",
                    "por_anio": {str(ANIO): len(B)}, "total": len(B), "descartados": 0, "ultimo": {"anio": ANIO, "se": int(B["SEMANA"].max())}})
    eventos += extra_ev

    # ---------- Brotes, epizootias y EVISAP (sin datos de quien notifica) ----------
    def norm_txt(x):
        return sin_tildes(str(x if x is not None else "")).strip().upper()

    def evento_brote(diag, tipo):
        d = norm_txt(diag)
        for a, b, r in (("MAN", "PIE", "Enfermedad mano, pie y boca"), ("ALIMENTO", "", "Enfermedad transmitida por alimentos (ETA)"), ("RABIA HUMANA", "", "Rabia humana"),
                        ("RABIA", "", "Rabia animal"), ("SARAMPION", "", "Sarampión"), ("VARICELA", "", "Varicela"), ("TOS FERINA", "", "Tos ferina"),
                        ("FIEBRE AMARILLA", "", "Fiebre amarilla"), ("DENGUE", "", "Dengue"), ("ERUPCION", "", "Síndrome febril con erupción dérmica"),
                        ("HEMORR", "", "Síndrome febril con manifestaciones hemorrágicas"), ("DIFTERIA", "", "Difteria"), ("TETANOS", "", "Tétanos"),
                        ("PARALISIS FLACIDA", "", "Parálisis flácida aguda")):
            if a in d and b in d:
                return r
        if not d:
            return "Epizootia (sin especificar)" if tipo == "EPIZOOTIA" else "Sin especificar"
        return d[:1] + d[1:].lower()

    def f10(x):
        x = "" if x is None or (isinstance(x, float) and math.isnan(x)) else str(x).strip()
        if not x:
            return None
        return "%s-%s-%s" % (x[6:10], x[3:5], x[:2]) if x[2:3] == "/" else x[:10]

    def n0(v):
        v = pd.to_numeric(v, errors="coerce")
        return 0 if v is None or pd.isna(v) else int(v)

    brotes = None
    fb = sorted(x for x in os.listdir(RUTA_BASES) if re.search(r"brotes.*\.csv$", x, re.I))
    fi_ = [x for x in fb if "indicador" in x.lower()]
    fb = [x for x in fb if x not in fi_]
    if fb:
        Bt = pd.read_csv(os.path.join(RUTA_BASES, fb[-1]), dtype=str, keep_default_na=False, na_values=["NA"], encoding="utf-8")
        Bt.columns = [c.strip().lower() for c in Bt.columns]
        Bt = Bt[Bt["cod_dist"].isin(RED_UB)]
        I = {}
        if fi_:
            Id = pd.read_csv(os.path.join(RUTA_BASES, fi_[-1]), dtype=str, keep_default_na=False, na_values=["NA"])
            Id.columns = [c.strip().lower() for c in Id.columns]
            I = {r["id"]: r for r in Id.to_dict("records")}

        def g(id_, c):
            v = I.get(id_, {}).get(c)
            return None if v is None or (isinstance(v, float) and math.isnan(v)) or v == "" else v

        lista = []
        for r in Bt.to_dict("records"):
            id_ = r["id"]
            tipo = str(r.get("clasificacion_evento") or "").strip().upper()
            ini, seg, fin = g(id_, "informe_inicial") == "1", g(id_, "informe_seguimiento") == "1", g(id_, "informe_final") == "1"
            hn, hi, on, oi = g(id_, "diferencia_horas_notif_conoc"), g(id_, "horas_carga_informe"), g(id_, "ind_oportunidad_notificacion"), g(id_, "ind_oportunidad_informe_inicial")
            loc = r.get("localidad")
            lista.append({"id": id_, "tipo": tipo, "evento": evento_brote(r.get("diagnostico"), tipo), "grupo": oracion(r.get("grupo_danio")),
                          "inicio": f10(r.get("fecha_inicio_evento")), "se_inicio": n0(r.get("semana_inicio_evento")),
                          "conocimiento": f10(r.get("fecha_conocimiento_evento")), "se": n0(r.get("semana_conocimiento_evento")),
                          "ubigeo": r["cod_dist"], "distrito": titulo(r.get("distrito")), "provincia": titulo(r.get("provincia")),
                          "localidad": "" if not isinstance(loc, str) or loc == "" else titulo(loc),
                          "eess": "" if not isinstance(r.get("eess"), str) else titulo(r["eess"]),
                          "casos": n0(r.get("numero_casos")), "hosp": n0(r.get("numero_hospitalizados")), "fall": n0(r.get("numero_fallecidos")),
                          "muestra": r.get("toma_muestra") == "S",
                          "estado": "Cerrado" if fin else "En curso" if seg else "Inicial" if ini else "Sin informe",
                          "inf": {"inicial": f10(g(id_, "fecha_informe_inicial")) if ini else None,
                                  "seguimiento": f10(g(id_, "fecha_informe_seguimiento")) if seg else None,
                                  "final": f10(g(id_, "fecha_informe_final")) if fin else None},
                          "horas_notif": None if hn is None else n0(hn), "horas_inicial": None if hi is None else n0(hi),
                          "oport_notif": None if on is None else on == "1", "oport_inicial": None if oi is None else oi == "1",
                          "lat": _flt(r.get("latitud")), "lon": _flt(r.get("longitud"))})
        lista.sort(key=lambda b: b["conocimiento"] or "", reverse=True)
        brotes = {"lista": lista, "fuente": "Notificación de brotes, epizootias y EVISAP – Red Integrada de Salud Chachapoyas"}

    # ---------- Establecimientos y microredes con datos ----------
    cods = []
    for m in modulos.values():
        for k in m["series"]:
            if k != "TOTAL" and not k.startswith("MR") and k not in cods:
                cods.append(k)
    eess = [{"cod": c, "nombre": nom_es.get(c, "EE.SS. " + c), "mr": "MR" + (mr_es.get(c) or "??"), "pob": None} for c in cods]
    eess.sort(key=lambda e: e["nombre"])
    mrs = sorted({e["mr"] for e in eess})
    microredes = [{"cod": k, "nombre": nom_mr["99"] if k[2:] == "99" else "Microred " + nom_mr.get(k[2:], k[2:])} for k in mrs]
    microredes.sort(key=lambda m: (m["cod"] == "MR99", m["nombre"]))

    # ---------- Mapa epidemiológico ----------
    ub_es = dict(zip(E["COD_EST"], E["UBIGEO_RN"]))
    for k, d in (("eda", eda), ("ira", ira), ("feb", feb)):
        d = d[d["ANO"] == ANIO].copy()
        d["UB"] = d["E_SALUD"].map(ub_es)
        al_mapa(k, d[d["UB"].notna()], "UB", None, "V")
    LOC = lee_csv(busca(RUTA_MAESTROS, r"localidades.*\.csv$"))
    nom_loc = {str(c).strip(): titulo(n) for c, n in zip(LOC["CODLOC"], LOC["NOMBRE"])}
    MP = pd.concat(MAPA, ignore_index=True)
    nombres = {e["id"]: e["nombre"] for e in eventos}
    nombres.update({"eda": "EDA", "ira": "IRA < 5 años", "feb": "Febriles"})
    dist_mapa = {}
    for u in [u for u in MP["ub"].unique() if u in RED_UB]:
        g_ = MP[MP["ub"] == u]
        ev = {}
        for e in g_["ev"].unique():
            h = g_[g_["ev"] == e]
            ev[e] = [entero(h["v"].sum()), entero(h.loc[h["se"] > SE - 4, "v"].sum()), entero(h.loc[(h["se"] > SE - 8) & (h["se"] <= SE - 4), "v"].sum())]
        loc = {}
        gl = g_[g_["loc"] != ""]
        for lc in gl["loc"].unique():
            n = nom_loc.get(lc, lc)
            hl = gl[gl["loc"] == lc]
            for e in hl["ev"].unique():
                loc.setdefault(n, {})[e] = entero(hl.loc[hl["ev"] == e, "v"].sum())
        dist_mapa[u] = {"ev": ev, "loc": loc}
    fu = MP[~MP["ub"].isin(RED_UB) & (MP["ub"].str.len() == 6)]
    fuera = [{"ev": ev, "ub": ub, "lugar": nom_dist(ub), "n": entero(h["v"].sum())}
             for (ev, ub), h in sorted(fu.groupby(["ev", "ub"]), key=lambda kv: kv[0][0] + " " + kv[0][1])]
    mapa = {"se": SE, "nombres": nombres, "colectivos": ["eda", "ira", "feb"], "distritos": dist_mapa, "fuera": fuera}

    anios_datos = sorted({int(a) for m in modulos.values() for a in m["series"]["TOTAL"]})
    hoy = dt.date.today()
    DASH = {"generado": hoy.isoformat(), "anio": ANIO, "ref_n": 5, "ambito": AMBITO, "ambito_corto": "Red", "anios_datos": anios_datos,
            "microredes": microredes, "eess": eess, "modulos": modulos, "eventos": eventos, "registros": registros, "brotes": brotes, "mapa": mapa,
            "registros_nota": "Listas exportadas del aplicativo de vigilancia de salud mental al %s. Se cuentan personas distintas; son registros acumulados, "
                              "no casos nuevos del año. La exportación no incluye fecha, establecimiento ni lugar de residencia." % hoy.strftime("%d/%m/%Y")}
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write("window.DASHBOARD_RED = " + json.dumps(DASH, ensure_ascii=False, separators=(",", ":"), default=_json) + ";\n")
    print("Listo: %s · SE %d %d %d · %d EE.SS. · %d microredes" % (os.path.relpath(SALIDA, RAIZ), se_eda, se_ira, se_feb, len(eess), len(microredes)))
    return SE


def oracion(s):
    s = str(s or "").strip()
    return s[:1].upper() + s[1:].lower()


def _flt(v):
    v = pd.to_numeric(v, errors="coerce")
    return None if v is None or pd.isna(v) else float(v)


def _json(o):
    if hasattr(o, "item"):
        return o.item()
    raise TypeError(type(o))


if __name__ == "__main__":
    try:
        generar(sys.argv[1] if len(sys.argv) > 1 else None)
    except Falta as e:
        print("ERROR: %s" % e)
        sys.exit(2)
