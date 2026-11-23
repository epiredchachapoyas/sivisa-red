"""Reduce las fotos pesadas de las carpetas */fotos antes de publicar (no cambia el nombre del archivo).
Lado mayor máximo 1600 px y calidad JPEG 82. Se ejecuta en GitHub al publicar: los originales del repositorio
no se tocan, solo la copia que se publica. Requiere Pillow (se instala solo si falta)."""
import os, subprocess, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETAS = ["promsa/fotos", "epidemiologia/fotos", "salud-ambiental/fotos", "assets/campanas"]
MAX_LADO, MAX_BYTES = 1600, 700_000


def main():
    try:
        from PIL import Image, ImageOps
    except ImportError:
        subprocess.call([sys.executable, "-m", "pip", "install", "--quiet", "pillow"])
        try:
            from PIL import Image, ImageOps
        except ImportError:
            print("  ! Pillow no disponible; las fotos se publican sin reducir.")
            return
    n = 0
    for c in CARPETAS:
        d = os.path.join(RAIZ, c)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            p = os.path.join(d, f)
            ext = os.path.splitext(f)[1].lower()
            if ext not in (".jpg", ".jpeg", ".png", ".webp") or os.path.getsize(p) <= MAX_BYTES:
                continue
            try:
                im = ImageOps.exif_transpose(Image.open(p))
                im.thumbnail((MAX_LADO, MAX_LADO))
                if ext in (".jpg", ".jpeg"):
                    im.convert("RGB").save(p, "JPEG", quality=82, optimize=True, progressive=True)
                elif ext == ".png":
                    im.save(p, "PNG", optimize=True)
                else:
                    im.save(p, quality=82)
                n += 1
            except Exception as e:
                print("  ! No se pudo reducir %s/%s: %s" % (c, f, e))
    print("Fotos reducidas: %d" % n)


if __name__ == "__main__":
    main()
