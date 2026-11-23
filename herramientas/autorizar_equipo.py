"""Uso exclusivo del autor: genera la línea de autorización de un equipo.

    python herramientas/autorizar_equipo.py  RUTA\\sivisa_clave_privada.txt  XXXX-XXXX-XXXX-XXXX

Pegue la línea que imprime en SIVISA_LICENCIA.txt (junto a la carpeta del portal) de ese equipo.
La clave privada NUNCA va dentro de la carpeta del portal ni en GitHub.
"""
import base64, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import licencia as L

if len(sys.argv) != 3:
    print(__doc__); sys.exit(1)
sk = base64.b64decode(open(sys.argv[1], encoding="utf-8").read().strip())
cod = sys.argv[2].strip().upper()
firma, pub = L.firmar(sk, L.mensaje(cod))
if base64.b64encode(pub).decode() != L.CLAVE_PUBLICA:
    print("Esa clave privada no corresponde a esta versión de SIVISA."); sys.exit(2)
print("%s %s" % (cod, base64.b64encode(firma).decode()))
