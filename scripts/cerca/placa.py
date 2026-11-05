# Placa final de "ESTUVISTE CERCA": celeste humo (#CDDDE5), tipografía azul oscuro (#233A55), logo oficial
# (LOGO/ROCCE_logo_sin_fondo.png, alfa real del original, solo escalado). Tres líneas; el CTA es el elemento más fuerte.
# Todo dentro de la zona segura de Reels (sin texto en el 22 % inferior ni pegado al borde derecho).
# Uso: python placa.py SALIDA.png
import sys
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
HUMO, AZUL = (0xCD, 0xDD, 0xE5), (0x23, 0x3A, 0x55)
im = Image.new("RGB", (W, H), HUMO); d = ImageDraw.Draw(im)
logo = Image.open("LOGO/ROCCE_logo_sin_fondo.png").convert("RGBA")
logo = logo.crop(logo.getbbox()); lh = 330; logo = logo.resize((round(logo.width * lh / logo.height), lh), Image.LANCZOS)
im.paste(logo, ((W - logo.width) // 2, 390), logo)
F = "/usr/share/fonts/opentype/inter/"
def centrado(y, txt, font, fill, track=0):
    ws = [d.textlength(ch, font=font) for ch in txt]; tot = sum(ws) + track * (len(txt) - 1)
    x = (W - tot) / 2
    for ch, w in zip(txt, ws):
        d.text((x, y), ch, font=font, fill=fill); x += w + track
    return tot
f1 = ImageFont.truetype(F + "Inter-SemiBold.otf", 44)
centrado(830, "DROP FOUNDERS PRIVÉE", f1, AZUL, track=9)
f2 = ImageFont.truetype("scripts/fuentes/InstrumentSerif-Regular.ttf", 118)
centrado(910, "YA ESTÁ DISPONIBLE", f2, AZUL, track=1)
f3 = ImageFont.truetype(F + "InterDisplay-Bold.otf", 84)
txt = "COMPRÁ LA TUYA"; tw = d.textlength(txt, font=f3) + 4 * (len(txt) - 1)
bx0, by0 = (W - tw) / 2 - 56, 1112; bx1, by1 = (W + tw) / 2 + 56, 1112 + 150
d.rounded_rectangle((bx0, by0, bx1, by1), radius=75, fill=AZUL)
asc, desc = f3.getmetrics(); bb = d.textbbox((0, 0), "COMPRÁ", font=f3)
centrado(by0 + (150 - (bb[3] - bb[1])) / 2 - bb[1] + 4, txt, f3, HUMO, track=4)
im.save(sys.argv[1]); print("placa", sys.argv[1])
