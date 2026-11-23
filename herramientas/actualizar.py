"""SIVISA · Publicación automática (la ejecuta sola la tarea de Windows "SIVISA - publicar", cada 30 minutos).

1. Trae de GitHub los cambios hechos desde otras computadoras.
2. Si cambió alguna base en BASES_NOTISP\\<año>, genera epidemiologia/data/vigilancia_red.js (solo conteos).
3. Si hay algo nuevo en la carpeta del portal (PDF, Excel de plantillas, fotos, datos), lo sube a GitHub.
   El archivo .gitignore impide que se suban bases nominales.
Registro: BASES_NOTISP\\ULTIMA_ACTUALIZACION.txt (lo puede revisar cualquiera).
Uso manual:  python herramientas/actualizar.py  [--forzar]
"""
import datetime as dt
import glob, hashlib, json, os, shutil, subprocess, sys, traceback

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASES = os.path.join(os.path.dirname(RAIZ), "BASES_NOTISP")
SOLO_PUBLICAR = os.path.join(os.path.dirname(RAIZ), "SIVISA_SOLO_PUBLICAR.txt")   # este equipo no procesa bases
_DIR = BASES if os.path.isdir(BASES) else os.path.dirname(RAIZ)   # sin bases (p. ej. laptop): junto al portal
ESTADO = os.path.join(_DIR, ".estado_sivisa.json")
REGISTRO = os.path.join(_DIR, "ULTIMA_ACTUALIZACION.txt")
NOSHOW = 0x08000000 if os.name == "nt" else 0          # sin ventanas negras en Windows
lineas = []


def log(m):
    m = "%s  %s" % (dt.datetime.now().strftime("%d/%m/%Y %H:%M"), m)
    lineas.append(m)
    print(m)


def git_exe():
    c = shutil.which("git")
    if c:
        return c
    for p in [r"C:\Program Files\Git\cmd\git.exe", r"C:\Program Files (x86)\Git\cmd\git.exe",
              os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe")] + \
             sorted(glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\GitHubDesktop\app-*\resources\app\git\cmd\git.exe")), reverse=True):
        if os.path.isfile(p):
            return p
    raise RuntimeError("No se encontró Git. Ejecute INSTALAR.bat.")


def git(*args, ok=(0,)):
    r = subprocess.run([git_exe(), "-C", RAIZ] + list(args), capture_output=True, text=True, encoding="utf-8",
                       errors="replace", creationflags=NOSHOW)
    if r.returncode not in ok:
        raise RuntimeError("git %s: %s" % (" ".join(args), (r.stderr or r.stdout).strip()[-400:]))
    return r.stdout


def traer_cambios():
    """git pull. Si un mismo archivo cambió aquí y en otra computadora (p. ej. un Excel), se conserva el de ESTA
    computadora y el aviso queda en el registro; nunca deja el repositorio a medio combinar."""
    for a in (("rebase", "--abort"), ("merge", "--abort")):          # restos de un intento anterior
        git(*a, ok=(0, 1, 128))
    try:
        git("pull", "--rebase", "--autostash", "--quiet")
        return
    except Exception:
        git("rebase", "--abort", ok=(0, 1, 128))
    try:
        git("add", "-A")
        git("commit", "-m", "Cambios locales antes de combinar", ok=(0, 1))
        git("pull", "--no-rebase", "--no-edit", "-X", "ours", "--quiet")
        log("Aviso: un archivo cambió aquí y en otra computadora; se conservó la versión de esta computadora.")
    except Exception as e:
        git("merge", "--abort", ok=(0, 1, 128))
        log("Aviso: no se pudo traer cambios de GitHub (%s). Se reintenta en la próxima vuelta." % str(e)[:200])


def huella():
    """Nombre, tamaño y fecha de cada archivo de la carpeta del año más reciente y de Maestros."""
    if not os.path.isdir(BASES):
        return None
    anios = sorted(d for d in os.listdir(BASES) if d.isdigit() and len(d) == 4)
    if not anios:
        return None
    h = hashlib.sha1()
    for carpeta in (os.path.join(BASES, anios[-1]), os.path.join(BASES, "Maestros")):
        for f in sorted(os.listdir(carpeta)) if os.path.isdir(carpeta) else []:
            p = os.path.join(carpeta, f)
            if os.path.isfile(p) and not f.startswith("~$"):
                st = os.stat(p)
                h.update(("%s|%d|%d\n" % (f, st.st_size, int(st.st_mtime))).encode())
    return h.hexdigest()


def leer_estado():
    try:
        return json.load(open(ESTADO, encoding="utf-8"))
    except Exception:
        return {}


def main():
    forzar = "--forzar" in sys.argv
    est = leer_estado()
    # 0) Candado: solo equipos autorizados por el autor (ver herramientas/licencia.py)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import licencia
        ok, msg = licencia.autorizado()
    except Exception as e:
        ok, msg = False, "No se pudo verificar la autorización del equipo (%s)." % e
    if not ok or msg != est.get("licencia") or forzar:
        log(msg)
        est["licencia"] = msg
    if not ok:
        guardar(est)
        return
    # 1) Cambios de otras computadoras
    traer_cambios()
    # 2) Bases semanales
    hu = None if os.path.isfile(SOLO_PUBLICAR) else huella()
    if hu and (forzar or hu != est.get("huella")):
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import vigilancia
            se = vigilancia.generar(BASES)
            est["huella"], est["se"] = hu, se
            log("Bases procesadas: datos de vigilancia hasta la SE %s." % se)
        except Exception as e:
            log("ERROR al procesar las bases: %s. Revise que los archivos sean los descargados de NotiSP." % e)
            traceback.print_exc()
    # 3) Publicar todo lo nuevo de la carpeta del portal
    try:
        git("add", "-A")
        cambios = [l[3:] for l in git("status", "--porcelain").splitlines() if l.strip()]
        if cambios:
            msg = "Actualización automática %s (%d archivo%s)" % (dt.datetime.now().strftime("%d/%m/%Y %H:%M"), len(cambios), "" if len(cambios) == 1 else "s")
            git("commit", "-m", msg, "-m", "\n".join(cambios[:40]))
            git("push", "--quiet")
            log("Publicado en GitHub: %d archivo(s). El sitio se actualiza en 2-3 minutos." % len(cambios))
            for c in cambios[:15]:
                log("   · " + c.strip('"'))
        elif git("rev-list", "--count", "@{u}..HEAD", ok=(0, 128)).strip() not in ("", "0"):
            git("push", "--quiet")                       # commits que quedaron sin subir (p. ej. tras combinar)
            log("Publicado en GitHub: cambios pendientes de esta computadora.")
        elif not lineas:
            log("Sin cambios.")
    except Exception as e:
        log("ERROR al publicar: %s" % str(e)[:300])
    guardar(est)


def guardar(est):
    est["ultima"] = dt.datetime.now().isoformat(timespec="seconds")
    try:
        json.dump(est, open(ESTADO, "w", encoding="utf-8"))
        if any(not l.endswith("Sin cambios.") for l in lineas):
            previo = open(REGISTRO, encoding="utf-8").read().splitlines()[-300:] if os.path.isfile(REGISTRO) else []
            open(REGISTRO, "w", encoding="utf-8").write("\n".join(previo + lineas) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    if sys.stdout is None or sys.stderr is None:          # pythonw (tarea programada): sin consola
        sys.stdout = sys.stderr = open(os.devnull, "w")
    main()
