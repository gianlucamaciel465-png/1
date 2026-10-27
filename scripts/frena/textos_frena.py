# Textos fijos de ROCCE_lo_que_te_frena (PNG RGBA de cuadro completo 1080×1920), tipografía de la casa (Inter Display).
#   gancho.png   "Lo que te frena" / "no está adelante."  (sobre el negro de la animación, tercio superior)
#   placa1.png   "Drop Founders Privée —"                    (cierre de campaña, pedido así)
#   placa2.png   "01/11/2026"                                (el dato principal, el más grande)
#   placa3.png   botón blanco "Sé uno de los primeros 100."  (única llamada a la acción)
#   placa_fondo.png  degradé oscuro suave detrás del cierre (texto blanco sobre cielo claro)
# Uso: python3 textos_frena.py SALIDA_DIR
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
W, H, SS = 1080, 1920, 2
D = "/usr/share/fonts/opentype/inter/"
F = lambda w, px: ImageFont.truetype(D + f"InterDisplay-{w}.otf", px * SS)

def lienzo(): return Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
def guardar(im, nombre, fuerza=0.55):
    a = im.split()[3].filter(ImageFilter.GaussianBlur(7 * SS)).point(lambda v: int(v * fuerza))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 255), (0, 3 * SS), a)
    im = Image.alpha_composite(sh, im)
    im.resize((W, H), Image.LANCZOS).save(os.path.join(out, nombre)); print(nombre)

def centrada(d, cy, texto, ft, color=(255, 255, 255)):
    d.text((W * SS / 2, cy * SS), texto, font=ft, fill=color + (255,), anchor="ms")

# gancho: dos líneas, arriba de la escalera (zona negra libre en toda la animación)
im = lienzo(); d = ImageDraw.Draw(im); ft = F("SemiBold", 66)
centrada(d, 392, "Lo que te frena", ft)
centrada(d, 474, "no está adelante.", ft)
guardar(im, "gancho.png", fuerza=0.0)

# cierre sobre la toma real: degradé + textos
g = np.zeros((H, W, 4), np.uint8)
y = np.arange(H)[:, None]
alpha = np.clip(1 - (y - 160) / 700, 0, 1) ** 1.4 * 150
g[..., 3] = np.broadcast_to(alpha, (H, W)).astype(np.uint8)
Image.fromarray(g, "RGBA").save(os.path.join(out, "placa_fondo.png")); print("placa_fondo.png")
im = lienzo(); d = ImageDraw.Draw(im); centrada(d, 318, "Drop Founders Privée —", F("Bold", 60)); guardar(im, "placa1.png", 0.45)
im = lienzo(); d = ImageDraw.Draw(im); centrada(d, 470, "01/11/2026", F("ExtraBold", 150)); guardar(im, "placa2.png", 0.45)
# llamada a la acción en botón (se lee sobre la espuma; mismo recurso que ROCCE_crea_v01)
im = lienzo(); d = ImageDraw.Draw(im); ft = F("SemiBold", 46); t = "Sé uno de los primeros 100."
w = ft.getlength(t); h = 92 * SS; x0, y0 = (W * SS - w) / 2 - 42 * SS, 600 * SS - h / 2
d.rounded_rectangle([x0, y0, x0 + w + 84 * SS, y0 + h], radius=h / 2, fill=(255, 255, 255, 255))
d.text((W * SS / 2, 600 * SS), t, font=ft, fill=(11, 31, 58, 255), anchor="mm")
guardar(im, "placa3.png", 0.30)
