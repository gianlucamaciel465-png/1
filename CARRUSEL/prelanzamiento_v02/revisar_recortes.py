# Hoja de control del encuadre: para cada clip de cada ventana, su cuadro inicial, medio y final con el recorte exacto
# que usa el MP4 (sirve para ajustar "centro" y "ancho" en proyecto.py sin renderizar todo).
# Uso: python3 revisar_recortes.py SALIDA.jpg
import os, sys, json, io, subprocess
from PIL import Image, ImageDraw
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
from proyecto import PAGINAS, ORIG
from video import cadena, RAIZ
vent = json.load(open(os.path.join(AQUI, "capas", "ventanas.json")))
filas = []
for n, pag in PAGINAS.items():
    for v in vent.get(n, []):
        for toma, a, b, centro, ancho in pag["ventanas"][v["id"]]:
            ims = []
            for t in (a + 0.02, (a + b) / 2, b - 0.05):
                raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", os.path.join(RAIZ, ORIG, toma + ".mov"), "-frames:v", "1",
                                      "-vf", cadena(toma, centro, ancho, v["w"], v["h"]).replace("format=yuv444p", "format=rgb24"),
                                      "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
                ims.append(Image.open(io.BytesIO(raw)).convert("RGB"))
            filas.append((f"{n} {v['id']} {toma} {a:.2f}-{b:.2f}", ims))
H = 260; hoja = Image.new("RGB", (3 * 470 + 40, len(filas) * (H + 30) + 10), (40, 44, 48)); d = ImageDraw.Draw(hoja)
for i, (txt, ims) in enumerate(filas):
    y = 10 + i * (H + 30); d.text((10, y), txt, fill="yellow")
    for j, im in enumerate(ims):
        im.thumbnail((460, H)); hoja.paste(im, (10 + j * 470, y + 18))
hoja.save(sys.argv[1], quality=85); print(sys.argv[1], len(filas), "clips")
