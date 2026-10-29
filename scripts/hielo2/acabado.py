# ROCCE_01_HIELO_REVELACION v02 — paso 2: limpieza de la grabación de referencia y rótulo propio.
#   1. borra el rótulo "Baggy Nike Jogger>" (fijo en pantalla): se copia el piso de la MISMA toma desde la franja de
#      arriba (se mueve con la cámara: sin parpadeo), con borde suave y corrección de luz de baja frecuencia;
#   2. recorta la barra del teléfono (hora, señal, batería): ventana 512×910 desde y = 100;
#   3. escala a 1080×1920 (lanczos) con nitidez leve;
#   4. rótulo "Remera roccé>" (texto exacto) en el estilo de la referencia: blanco, negrita itálica, contorno oscuro
#      fino y sombra suave, en el mismo lugar que el original.
# Uso: python acabado.py COMP_DIR REF_DIR SALIDA_DIR
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

comp, ref, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
PLANOS = [(305, 402, -62), (440, 469, -62), (472, 497, -62)]    # cuadros y desplazamiento de la fuente (arriba)
Y0, HC = 100, 910                                                 # ventana 9:16 sin barra de estado
W, H = 1080, 1920
TXT = "Remera roccé>"
FUENTE = "/usr/share/fonts/opentype/inter/Inter-ExtraBoldItalic.otf"

# máscara del rótulo: letras blancas o contorno oscuro en ≥ 70 % de los cuadros, ensanchada (contorno, halo, sombra)
fs = [f for a, b, _ in PLANOS for f in range(a, b + 1)]
st = np.stack([cv2.imread(f"{ref}/{f:04d}.png").astype(np.float32) for f in fs[::2]])
le = (((st.min(3) > 200).mean(0) > 0.7) | ((st.max(3) < 70).mean(0) > 0.7)).astype(np.uint8)
del st
le[:180] = 0; le[250:] = 0
m = cv2.dilate(le, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
m = m | np.roll(m, 4, axis=0)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
ys, xs = np.nonzero(m)
print("rótulo original (con halo): x", xs.min(), xs.max(), "y", ys.min(), ys.max())
alfa = np.clip(cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.5) * 1.6, 0, 1)[..., None]
anillo = (cv2.dilate(m, np.ones((11, 11), np.uint8)) - m).astype(np.float32)[..., None]

def borrar(im, dy):
    """Copia el piso de la misma toma desde dy píxeles más arriba (se mueve con la cámara) y corrige la luz de
    baja frecuencia con la diferencia medida en un anillo alrededor (sin costura)."""
    im = im.astype(np.float32)
    src = np.roll(im, -dy, axis=0)
    d = (im - src) * anillo
    corr = cv2.GaussianBlur(d, (0, 0), 14) / np.maximum(cv2.GaussianBlur(anillo, (0, 0), 14)[..., None], 1e-3)
    return im * (1 - alfa) + (src + corr) * alfa

# rótulo nuevo (capa RGBA a 1080×1920), centrado donde estaba el original
esc = W / 512.0
f_ = ImageFont.truetype(FUENTE, 60)
yc_orig = (203 + 230) / 2 - Y0                     # centro vertical de las letras originales en la ventana
tw = f_.getlength(TXT); bb = f_.getbbox(TXT)
x = (W - tw) / 2; y = yc_orig * esc - (bb[1] + bb[3]) / 2
capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sombra = Image.new("L", (W, H), 0)
ImageDraw.Draw(sombra).text((x + 2, y + 4), TXT, font=f_, fill=120, stroke_width=4)
sombra = sombra.filter(ImageFilter.GaussianBlur(6))
capa.putalpha(sombra)
txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(txt).text((x, y), TXT, font=f_, fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(24, 24, 26, 255))
capa.alpha_composite(txt)
capa.save(os.path.join(out, "_rotulo.png"))
rot = np.asarray(capa).astype(np.float32) / 255.0

n = 0
for a, b, dy in PLANOS:
    for f in range(a, b + 1):
        im = cv2.imread(f"{comp}/{f:04d}.png")
        v = np.clip(borrar(im, dy), 0, 255).astype(np.uint8)[Y0:Y0 + HC]
        v = cv2.resize(v, (W, H), interpolation=cv2.INTER_LANCZOS4)
        bl = cv2.GaussianBlur(v, (0, 0), 1.2)
        v = cv2.addWeighted(v, 1.35, bl, -0.35, 0)                  # nitidez leve
        rgb = v[..., ::-1].astype(np.float32) / 255.0
        rgb = rgb * (1 - rot[..., 3:4]) + rot[..., :3] * rot[..., 3:4]
        n += 1
        Image.fromarray(np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)).save(f"{out}/{n:04d}.png", compress_level=1)
print("cuadros:", n)
