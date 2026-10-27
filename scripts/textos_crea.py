# Textos de ROCCE_crea_vNN ("¿Y si la próxima Roccé la creás vos?"). PNG RGBA de cuadro completo (1080×1920).
#   pregunta.png   barra translúcida estilo Snapchat (gancho de la casa) con la pregunta
#   resp1.png      "Los primeros 100" / "son Founders."           (contexto, más chico)
#   resp2.png      "El 001 diseña" / "la próxima."   001 celeste    (la respuesta, más grande)
#   cta1/2/3.png   "FOUNDERS PRIVÉE" espaciado · "01/11/2026" grande · botón blanco "Sé uno de los primeros 100."
# Textos exactos; tipografía de la casa (Inter Display, sustituto de la grotesca de las referencias).
# Uso: python3 textos_crea.py SALIDA_DIR
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
W, H, SS = 1080, 1920, 2
D = "/usr/share/fonts/opentype/inter/"
F = lambda w, px: ImageFont.truetype(D + f"InterDisplay-{w}.otf", px * SS)
BLANCO, CEL, MARINO = (255, 255, 255), (169, 200, 232), (11, 31, 58)

def lienzo(): return Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
def guardar(im, nombre, sombra=True, fuerza=0.55):
    if sombra:
        a = im.split()[3].filter(ImageFilter.GaussianBlur(6 * SS)).point(lambda v: int(v * fuerza))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 255), (2 * SS, 3 * SS), a)
        im = Image.alpha_composite(sh, im)
    im.resize((W, H), Image.LANCZOS).save(os.path.join(out, nombre)); print(nombre)

def linea(d, x, y, tramos, ft):           # tramos: [(texto, color)], x = borde izquierdo, y = línea de base
    for t, c in tramos:
        d.text((x, y), t, font=ft, fill=c + (255,), anchor="ls"); x += ft.getlength(t)

def centrada(d, cy, texto, ft, color, tracking=0):
    if tracking:
        w = sum(ft.getlength(ch) for ch in texto) + tracking * SS * (len(texto) - 1); x = (W * SS - w) / 2
        for ch in texto:
            d.text((x, cy * SS), ch, font=ft, fill=color + (255,), anchor="lm"); x += ft.getlength(ch) + tracking * SS
    else:
        d.text((W * SS / 2, cy * SS), texto, font=ft, fill=color + (255,), anchor="mm")

# 1) pregunta en barra
im = lienzo(); d = ImageDraw.Draw(im); ft = F("SemiBold", 46)
d.rectangle([0, 514 * SS, W * SS, 606 * SS], fill=(0, 0, 0, 150))
centrada(d, 560, "¿Y si la próxima Roccé la creás vos?", ft, BLANCO)
guardar(im, "pregunta.png", sombra=False)

# 2) respuesta: contexto y remate (alineados a la izquierda, sobre la tela oscura de arriba)
im = lienzo(); d = ImageDraw.Draw(im); ft = F("Bold", 70)
linea(d, 88 * SS, 300 * SS, [("Los primeros 100", BLANCO)], ft)
linea(d, 88 * SS, 380 * SS, [("son Founders.", BLANCO)], ft)
guardar(im, "resp1.png")
im = lienzo(); d = ImageDraw.Draw(im); ft = F("ExtraBold", 108)
linea(d, 84 * SS, 545 * SS, [("El ", BLANCO), ("001", CEL), (" diseña", BLANCO)], ft)
linea(d, 84 * SS, 660 * SS, [("la próxima.", BLANCO)], ft)
guardar(im, "resp2.png")

# 3) cierre sobre el cielo
im = lienzo(); d = ImageDraw.Draw(im)
centrada(d, 300, "FOUNDERS PRIVÉE", F("SemiBold", 40), BLANCO, tracking=10)
guardar(im, "cta1.png", fuerza=0.35)
im = lienzo(); d = ImageDraw.Draw(im)
centrada(d, 430, "01/11/2026", F("Bold", 168), BLANCO)
guardar(im, "cta2.png", fuerza=0.35)
im = lienzo(); d = ImageDraw.Draw(im); ft = F("SemiBold", 48)
t = "Sé uno de los primeros 100."; w = ft.getlength(t); h = 96 * SS
x0, y0 = (W * SS - w) / 2 - 44 * SS, 620 * SS - h / 2
d.rounded_rectangle([x0, y0, x0 + w + 88 * SS, y0 + h], radius=h / 2, fill=BLANCO + (255,))
d.text((W * SS / 2, 620 * SS), t, font=ft, fill=MARINO + (255,), anchor="mm")
guardar(im, "cta3.png", fuerza=0.3)
