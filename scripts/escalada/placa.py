# Placa final de ROCCE_02_HACETE_FOUNDER: fondo negro de la animación, título blanco (último renglón en celeste),
# subtítulo celeste y el logo original sobre su propio fondo (#FEFEFE) en una ficha de esquinas redondeadas
# (solo se escala; las esquinas recortan fondo, no el trazo: el dibujo empieza a 182 px del borde de 1254).
# Textos exactos del encargo, separados en renglones sin cambiar palabras. Entrada escalonada y luego quieta.
# Uso: python placa.py SALIDA_DIR cuadros [fps]
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.join(AQUI, "..", "..")
FUENTES = os.path.join(RAIZ, "CARRUSEL", "prelanzamiento", "fuentes")
out, N = sys.argv[1], int(sys.argv[2]); FPS = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
os.makedirs(out, exist_ok=True)
W, H = 1080, 1920
FONDO = (6, 7, 10); BLANCO = (255, 255, 255); CELESTE = (126, 178, 222)
TITULO = [("SI TAMBIÉN", BLANCO), ("PASASTE POR ESO,", BLANCO), ("HACETE FOUNDER", CELESTE)]
SUB = ["Lista privada de Roccé para vos", "y creás prendas con nosotros."]
assert " ".join(t for t, _ in TITULO) == "SI TAMBIÉN PASASTE POR ESO, HACETE FOUNDER"
assert " ".join(SUB) == "Lista privada de Roccé para vos y creás prendas con nosotros."
fb = ImageFont.truetype(os.path.join(FUENTES, "InterDisplay-Bold.otf"), 100)
# tamaño del título: el renglón más ancho ocupa ~880 px
ancho = max(fb.getlength(t) for t, _ in TITULO); TS = int(100 * 880 / ancho)
ft = ImageFont.truetype(os.path.join(FUENTES, "InterDisplay-Bold.otf"), TS)
fs = ImageFont.truetype(os.path.join(FUENTES, "InterDisplay-Medium.otf"), 46)
logo = Image.open(os.path.join(RAIZ, "LOGO", "rocce_logo.png")).convert("RGB")
LT = 232
ficha = logo.resize((LT, LT), Image.LANCZOS)
mask = Image.new("L", (LT * 4, LT * 4), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, LT * 4 - 1, LT * 4 - 1], radius=26 * 4, fill=255)
mask = mask.resize((LT, LT), Image.LANCZOS)

capH = ft.getbbox("H")[3] - ft.getbbox("H")[1]
lh = capH * 1.36
sub_capH = fs.getbbox("H")[3] - fs.getbbox("H")[1]
# alturas: bloque centrado un poco arriba del centro (abajo queda la interfaz de Reels)
y_tit = 560
y_sub = y_tit + 2 * lh + capH + 92
y_logo = y_sub + sub_capH * 2 + 26 + 118

def ease(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3

def capa_texto(texto, font, color, y_cap, alpha, dy):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    w = font.getlength(texto); top = font.getbbox("H")[1]
    d.text(((W - w) / 2, y_cap - top + dy), texto, font=font, fill=color + (int(255 * alpha),))
    return im

for i in range(N):
    t = i / FPS
    fr = Image.new("RGBA", (W, H), FONDO + (255,))
    for k, (txt, col) in enumerate(TITULO):
        a = ease((t - 0.10 - 0.09 * k) / 0.45)
        if a > 0: fr.alpha_composite(capa_texto(txt, ft, col, y_tit + k * lh, a, 26 * (1 - a)))
    for k, txt in enumerate(SUB):
        a = ease((t - 0.55 - 0.08 * k) / 0.45)
        if a > 0: fr.alpha_composite(capa_texto(txt, fs, CELESTE, y_sub + k * (sub_capH + 26), a, 18 * (1 - a)))
    a = ease((t - 0.85) / 0.5)
    if a > 0:
        sc = 0.94 + 0.06 * a; s = int(round(LT * sc))
        fi = ficha.resize((s, s), Image.LANCZOS); mk = mask.resize((s, s), Image.LANCZOS)
        mk = Image.fromarray((np.asarray(mk, np.float32) * a).astype(np.uint8))
        fr.paste(fi, ((W - s) // 2, int(y_logo + (LT - s) / 2)), mk)
    # entrada desde negro
    fade = ease(t / 0.3)
    arr = np.asarray(fr.convert("RGB"), np.float32) * (0.15 + 0.85 * fade) if fade < 1 else np.asarray(fr.convert("RGB"), np.float32)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(os.path.join(out, f"{i + 1:04d}.png"), compress_level=1)
print("placa:", N, "cuadros; título", TS, "px; renglones en y", y_tit, y_sub, y_logo)
