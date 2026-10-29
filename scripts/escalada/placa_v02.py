# Placa final v02 de ROCCE_02_HACETE_FOUNDER: fondo celeste Roccé (el logo original es negro: sobre negro no se
# lee y no hay versión blanca oficial), título negro protagonista, subtítulo azul oscuro y el logo ORIGINAL sin
# fondo (LOGO/ROCCE_logo_sin_fondo.png, alfa real; sin placa ni recuadro detrás). Textos exactos del encargo,
# separados en renglones sin cambiar palabras. Entrada rápida (todo legible a los 0,6 s) y después quieta.
# Uso: python placa_v02.py SALIDA_DIR cuadros [fps]
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.join(AQUI, "..", "..")
FUENTES = os.path.join(RAIZ, "CARRUSEL", "prelanzamiento", "fuentes")
out, N = sys.argv[1], int(sys.argv[2]); FPS = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
os.makedirs(out, exist_ok=True)
W, H = 1080, 1920
CELESTE = np.array([126, 178, 222], np.float32)
NEGRO = (11, 12, 15); AZUL = (14, 32, 60)
TITULO = ["SI TAMBIÉN", "PASASTE POR ESO,", "HACETE FOUNDER"]
SUB = ["Lista privada de Roccé para vos", "y creás prendas con nosotros."]
assert " ".join(TITULO) == "SI TAMBIÉN PASASTE POR ESO, HACETE FOUNDER"
assert " ".join(SUB) == "Lista privada de Roccé para vos y creás prendas con nosotros."
fb = ImageFont.truetype(os.path.join(FUENTES, "InterDisplay-Bold.otf"), 100)
TS = int(100 * 900 / max(fb.getlength(t) for t in TITULO))
ft = ImageFont.truetype(os.path.join(FUENTES, "InterDisplay-Bold.otf"), TS)
fs = ImageFont.truetype(os.path.join(FUENTES, "InterDisplay-SemiBold.otf"), 50)
logo = Image.open(os.path.join(RAIZ, "LOGO", "ROCCE_logo_sin_fondo.png")).convert("RGBA")
bb = logo.getchannel("A").getbbox(); logo = logo.crop(bb)          # solo se quita el margen transparente
LH = 330; logo = logo.resize((round(logo.width * LH / logo.height), LH), Image.LANCZOS)
capH = ft.getbbox("H")[3] - ft.getbbox("H")[1]; lh = capH * 1.34
scap = fs.getbbox("H")[3] - fs.getbbox("H")[1]
y_tit = 470
y_sub = y_tit + 2 * lh + capH + 80
y_logo = y_sub + scap * 2 + 30 + 110

def ease(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
fondo = np.zeros((H, W, 3), np.float32) + CELESTE
yy = np.linspace(-1, 1, H)[:, None]; xx = np.linspace(-1, 1, W)[None, :]
fondo *= (1.04 - 0.07 * (xx ** 2 + yy ** 2) * 0.5)[..., None]        # viñeta muy suave
base = Image.fromarray(np.clip(fondo, 0, 255).astype(np.uint8)).convert("RGBA")

def texto(im, t, font, color, y_cap, a, dy):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    d.text(((W - font.getlength(t)) / 2, y_cap - font.getbbox("H")[1] + dy), t, font=font, fill=color + (int(255 * a),))
    im.alpha_composite(capa)

for i in range(N):
    t = i / FPS
    fr = base.copy()
    for k, tx in enumerate(TITULO):
        a = ease((t - 0.04 * k) / 0.32)
        if a > 0: texto(fr, tx, ft, NEGRO, y_tit + k * lh, a, 22 * (1 - a))
    for k, tx in enumerate(SUB):
        a = ease((t - 0.18 - 0.05 * k) / 0.32)
        if a > 0: texto(fr, tx, fs, AZUL, y_sub + k * (scap + 30), a, 14 * (1 - a))
    a = ease((t - 0.28) / 0.32)
    if a > 0:
        lg = logo.copy(); lg.putalpha(Image.fromarray((np.asarray(lg.getchannel("A"), np.float32) * a).astype(np.uint8)))
        fr.alpha_composite(lg, ((W - lg.width) // 2, int(y_logo)))
    arr = np.asarray(fr.convert("RGB"), np.float32)
    k = ease(t / 0.22)                                   # sale del negro del final de la animación
    arr = arr * (0.08 + 0.92 * k)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(os.path.join(out, f"{i + 1:04d}.png"), compress_level=1)
print("placa v02:", N, "cuadros; título", TS, "px; y", y_tit, round(y_sub), round(y_logo), "logo", logo.size)
