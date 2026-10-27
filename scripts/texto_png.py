# Texto de placa en PNG RGBA de cuadro completo (1080×1920), centrado en X, con tramos de distinto color y sombra suave.
# Fuente de la casa: Inter Display Bold (sustituto de la grotesca de las referencias).
# Uso: python3 texto_png.py SALIDA.png TAMAÑO_PX CENTRO_Y "texto|#RRGGBB" ["texto|#RRGGBB" ...]
#   El texto final es la concatenación exacta de los tramos (respetar espacios, raya — y tildes).
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

out, size, cy = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
parts = [p.rsplit("|", 1) for p in sys.argv[4:]]
W, H = 1080, 1920
ft = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", size)
full = "".join(t for t, _ in parts)
bb = ft.getbbox(full); tw = ft.getlength(full)
capt = ft.getbbox("H")
x = (W - tw) / 2; y = cy - (capt[1] + capt[3]) / 2          # centra la altura de mayúscula en cy
txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
mask = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(mask)
xx = x
for t, col in parts:
    d.text((xx, y), t, font=ft, fill=col); dm.text((xx, y), t, font=ft, fill=255)
    xx += ft.getlength(t)
import os
sc = os.environ.get("SOMBRA", "#000000")   # texto oscuro → SOMBRA=#FFFFFF (halo claro, sin desplazar)
rgb = tuple(int(sc[i:i + 2], 16) for i in (1, 3, 5)); clara = sum(rgb) > 382
sh = mask.filter(ImageFilter.GaussianBlur(7 if clara else 5)).point(lambda v: int(v * (0.45 if clara else 0.55)))
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); shadow.paste(rgb + (255,), (0, 0) if clara else (2, 3), sh)
Image.alpha_composite(shadow, txt).save(out)
l, t_, r, b_ = mask.getbbox()
print(f"{out}: '{full}' x {l}–{r} y {t_}–{b_} (ancho {r - l})")
