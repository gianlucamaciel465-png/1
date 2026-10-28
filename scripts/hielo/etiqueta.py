# Etiqueta "Remera roccé>" en el estilo de la referencia ("Baggy Nike Jogger>"): blanca, negrita itálica, con sombra
# oscura suave, centrada arriba del bloque. Texto exacto (con ">"). Sale un PNG RGBA de 1080×1920.
# Uso: python etiqueta.py SALIDA.png [y_mayuscula]
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
out = sys.argv[1]; Y = int(sys.argv[2]) if len(sys.argv) > 2 else 318
TXT = "Remera roccé>"
f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-ExtraBoldItalic.otf", 58)
W, H = 1080, 1920
w = f.getlength(TXT); top = f.getbbox("R")[1]; x = (W - w) / 2
sombra = Image.new("L", (W, H), 0); ImageDraw.Draw(sombra).text((x + 2, Y - top + 4), TXT, font=f, fill=150)
sombra = sombra.filter(ImageFilter.GaussianBlur(5))
capa = Image.new("RGBA", (W, H), (0, 0, 0, 0)); capa.putalpha(sombra)
txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(txt).text((x, Y - top), TXT, font=f, fill=(255, 255, 255, 255))
capa.alpha_composite(txt); capa.save(out)
print(out, "ancho", round(w), "px")
