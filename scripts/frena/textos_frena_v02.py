# Textos nuevos de ROCCE_lo_que_te_frena_v02 (los de v01 se generan con textos_frena.py y no cambian).
#   ruta.png         "Mandanos FOUNDERS y pedí acceso."  — la única acción, con las mismas palabras que la voz;
#                    FOUNDERS en una cajita tipo mensaje (es lo que hay que escribir)
#   placa_fondo2.png degradé oscuro más largo, para que la ruta también se lea sobre la espuma
# Uso: python3 textos_frena_v02.py SALIDA_DIR
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
W, H, SS = 1080, 1920, 2
D = "/usr/share/fonts/opentype/inter/"
F = lambda w, px: ImageFont.truetype(D + f"InterDisplay-{w}.otf", px * SS)
BLANCO = (255, 255, 255, 255)

im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
fa, fb = F("SemiBold", 44), F("ExtraBold", 44)
partes = [("Mandanos ", fa, False), ("FOUNDERS", fb, True), (" y pedí acceso.", fa, False)]
pad = 16 * SS
total = sum(f.getlength(t) for t, f, _ in partes) + 2 * pad
x = (W * SS - total) / 2; y = 722 * SS
for t, f, caja in partes:
    w = f.getlength(t)
    if caja:
        hb = 64 * SS
        d.rounded_rectangle([x, y - hb * 0.72, x + w + 2 * pad, y + hb * 0.28], radius=14 * SS, outline=BLANCO, width=3 * SS)
        x += pad; d.text((x, y), t, font=f, fill=BLANCO, anchor="ls"); x += w + pad
    else:
        d.text((x, y), t, font=f, fill=BLANCO, anchor="ls"); x += w
a = im.split()[3].filter(ImageFilter.GaussianBlur(7 * SS)).point(lambda v: int(v * 0.5))
sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 255), (0, 3 * SS), a)
Image.alpha_composite(sh, im).resize((W, H), Image.LANCZOS).save(os.path.join(out, "ruta.png")); print("ruta.png")

g = np.zeros((H, W, 4), np.uint8); yy = np.arange(H)[:, None]
alpha = np.clip(1 - (yy - 200) / 760, 0, 1) ** 1.3 * 160
g[..., 3] = np.broadcast_to(alpha, (H, W)).astype(np.uint8)
Image.fromarray(g, "RGBA").save(os.path.join(out, "placa_fondo2.png")); print("placa_fondo2.png")
