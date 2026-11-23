"""SIVISA · Autorización de equipos (candado de la publicación automática).

Cada computadora tiene un "código de equipo" (derivado del identificador de Windows). La publicación automática
solo funciona si junto a la carpeta del portal existe SIVISA_LICENCIA.txt con la autorización firmada por el autor
para ese código. La firma se verifica con la clave pública de abajo (Ed25519); la clave privada NO está en el
repositorio: la guarda el autor.
Mientras un equipo no esté autorizado, funciona durante un periodo de gracia y deja su código en
SIVISA_CODIGO_EQUIPO.txt para solicitar la autorización.
© M.C. Yhojar A. Pisfil-Farroñay. Todos los derechos reservados.
"""
import base64, datetime as dt, hashlib, json, os, platform, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PADRE = os.path.dirname(RAIZ)
LICENCIA = os.path.join(PADRE, "SIVISA_LICENCIA.txt")
AUTORIZADOS = os.path.join(RAIZ, "herramientas", "equipos_autorizados.txt")   # firmas por equipo (inútiles en otra PC)
SOLICITUDES = os.path.join(RAIZ, "herramientas", "solicitudes")
CODIGO = os.path.join(PADRE, "SIVISA_CODIGO_EQUIPO.txt")
GRACIA = os.path.join(PADRE, ".sivisa_gracia")
DIAS_GRACIA = 15
CLAVE_PUBLICA = "jEPtg3kSGIeBvu+URJUklDmifXZl2Uml0K3H4GvdWZE="

# ---- Ed25519 (verificación, RFC 8032; Python puro, sin librerías) ----
_p = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_d = -121665 * pow(121666, _p - 2, _p) % _p
_I = pow(2, (_p - 1) // 4, _p)


def _inv(x):
    return pow(x, _p - 2, _p)


def _add(P, Q):
    A = (P[1] - P[0]) * (Q[1] - Q[0]) % _p
    B = (P[1] + P[0]) * (Q[1] + Q[0]) % _p
    C = 2 * P[3] * Q[3] * _d % _p
    D = 2 * P[2] * Q[2] % _p
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % _p, G * H % _p, F * G % _p, E * H % _p)


def _mul(s, P):
    Q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            Q = _add(Q, P)
        P = _add(P, P)
        s >>= 1
    return Q


def _eq(P, Q):
    return (P[0] * Q[2] - Q[0] * P[2]) % _p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % _p == 0


def _recx(y, sign):
    if y >= _p:
        return None
    x2 = (y * y - 1) * _inv(_d * y * y + 1)
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_p + 3) // 8, _p)
    if (x * x - x2) % _p != 0:
        x = x * _I % _p
    if (x * x - x2) % _p != 0:
        return None
    if (x & 1) != sign:
        x = _p - x
    return x


_gy = 4 * _inv(5) % _p
_gx = _recx(_gy, 0)
_G = (_gx, _gy, 1, _gx * _gy % _p)


def _dec(s):
    y = int.from_bytes(s, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recx(y, sign)
    return None if x is None else (x, y, 1, x * y % _p)


def _enc(P):
    zi = _inv(P[2])
    x, y = P[0] * zi % _p, P[1] * zi % _p
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _h(m):
    return int.from_bytes(hashlib.sha512(m).digest(), "little")


def verificar_firma(pub, msg, sig):
    if len(pub) != 32 or len(sig) != 64:
        return False
    A, R = _dec(pub), _dec(sig[:32])
    if not A or not R:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= _L:
        return False
    k = _h(sig[:32] + pub + msg) % _L
    return _eq(_mul(s, _G), _add(R, _mul(k, A)))


def firmar(secreto32, msg):
    """Solo la usa herramientas/autorizar_equipo.py con la clave privada del autor."""
    h = hashlib.sha512(secreto32).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    pub = _enc(_mul(a, _G))
    r = _h(h[32:] + msg) % _L
    R = _enc(_mul(r, _G))
    s = (r + _h(R + pub + msg) * a) % _L
    return R + int.to_bytes(s, 32, "little"), pub


# ---- Equipo ----
def _id_equipo():
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        return winreg.QueryValueEx(k, "MachineGuid")[0]
    except Exception:
        for f in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                return open(f).read().strip()
            except Exception:
                pass
        return platform.node()


def codigo_equipo():
    h = hashlib.sha256(("SIVISA|" + _id_equipo().strip().lower()).encode()).hexdigest().upper()[:16]
    return "-".join(h[i:i + 4] for i in range(0, 16, 4))


def mensaje(codigo):
    return ("SIVISA|" + codigo).encode()


def autorizado():
    """(True|False, texto). Lee SIVISA_LICENCIA.txt (una o más líneas 'CODIGO FIRMA')."""
    cod = codigo_equipo()
    pub = base64.b64decode(CLAVE_PUBLICA)
    for archivo in (AUTORIZADOS, LICENCIA):
        try:
            for linea in open(archivo, encoding="utf-8"):
                partes = linea.split()
                if len(partes) >= 2 and partes[0].upper() == cod:
                    try:
                        if verificar_firma(pub, mensaje(cod), base64.b64decode(partes[1])):
                            return True, "Equipo autorizado (%s)." % cod
                    except Exception:
                        pass
        except FileNotFoundError:
            pass
    try:   # solicitud de autorización que viaja sola a GitHub con la siguiente publicación
        os.makedirs(SOLICITUDES, exist_ok=True)
        f = os.path.join(SOLICITUDES, cod + ".txt")
        if not os.path.isfile(f):
            open(f, "w", encoding="utf-8").write("Solicitud de autorización SIVISA\nCódigo: %s\nFecha: %s\n" % (cod, dt.date.today().isoformat()))
    except Exception:
        pass
    try:
        open(CODIGO, "w", encoding="utf-8").write(
            "Código de este equipo para autorizar SIVISA:\n\n    %s\n\nEnvíelo al autor (M.C. Yhojar A. Pisfil-Farroñay). "
            "Él le dará una línea de autorización que se pega en el archivo SIVISA_LICENCIA.txt, en esta misma carpeta.\n" % cod)
    except Exception:
        pass
    hoy = dt.date.today()
    try:
        ini = dt.date.fromisoformat(json.load(open(GRACIA)).get("desde"))
    except Exception:
        ini = hoy
        try:
            json.dump({"desde": hoy.isoformat()}, open(GRACIA, "w"))
        except Exception:
            pass
    quedan = DIAS_GRACIA - (hoy - ini).days
    if quedan > 0:
        return True, "Equipo SIN autorizar (código %s): funciona %d día(s) más. Ver SIVISA_CODIGO_EQUIPO.txt." % (cod, quedan)
    return False, "Equipo NO autorizado (código %s). La publicación automática está detenida. Ver SIVISA_CODIGO_EQUIPO.txt." % cod


if __name__ == "__main__":
    print(codigo_equipo(), autorizado())
