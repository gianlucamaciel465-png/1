# Rótulos en español para R14 (Neuron Visuals, "perfeccionista vs. accionista") con el estilo del original:
# mayúsculas cuadradas redondeadas, blancas, espaciadas, con un halo suave. Sustituto de la fuente original:
# Orbitron (OFL) comprimida en horizontal para igualar la proporción de las letras (ancho ≈ 0,75 del alto).
# Genera un PNG RGBA de cuadro completo (1080×1920) por rótulo, para superponer con FFmpeg.
# Uso: python3 rotulos_r14.py SALIDA_DIR [alto_mayúscula=35] [hueco=0.32]
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
CAP = float(sys.argv[2]) if len(sys.argv) > 2 else 35.0      # original: 27 px
GAP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.32      # hueco entre letras / alto (original: 0,39)
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes", "Orbitron-Variable.ttf")
WGHT = int(os.environ.get("WGHT", 600))
DIL = float(os.environ.get("DIL", 0.06))   # engrosado horizontal (fracción del alto, a cada lado)
W, H = 1080, 1920
SS = 4  # sobremuestreo para bordes limpios

def font(px):
    f = ImageFont.truetype(FONT, int(px)); f.set_variation_by_axes([WGHT]); return f

# tamaño de fuente para que la H mida CAP (en sobremuestreo)
probe = font(400); bb = probe.getbbox("H"); size = 400 * CAP * SS / (bb[3] - bb[1])
ft = font(size)
capH = ft.getbbox("H")[3] - ft.getbbox("H")[1]
target_w = 0.75 * capH                      # ancho de letra del original
ref_w = np.median([ft.getbbox(c)[2] - ft.getbbox(c)[0] for c in "ACEKNORST"])
SX = target_w / ref_w                        # compresión horizontal

def stems():
    """Grosor de trazo vertical (palo de la H) y horizontal (barra de la E) ya procesados."""
    h = np.asarray(glyph_raw("H")) > 128; ys = np.where(h.any(1))[0]; row = h[ys.min() + (ys.max() - ys.min()) // 4]   # fila sin la barra de la H
    sv = int(np.argmax(~row[np.argmax(row):]))           # ancho del primer palo
    e = np.asarray(glyph_raw("E")) > 128; col = e[:, e.shape[1] // 2]; top = np.argmax(col)
    sh = int(np.argmax(~col[top:]))
    return sv, sh

def glyph(c):
    if c == " ":
        return None
    if c == "I":   # la I del original tiene remates arriba y abajo (ancho ≈ 0,44 del alto)
        ref = np.asarray(glyph_raw("H")); rows = np.where(ref.max(1) > 128)[0]; y0, y1 = rows.min(), rows.max() + 1
        sv, sh = STEMS; wI = int(round(0.44 * capH)); a = np.zeros((ref.shape[0], wI), np.uint8)
        a[y0:y0 + sh, :] = 255; a[y1 - sh:y1, :] = 255; x0 = (wI - sv) // 2; a[y0:y1, x0:x0 + sv] = 255
        return Image.fromarray(a, "L")
    if c == "Í":   # misma I con remates + la tilde de la fuente, centrada
        base = np.asarray(glyph("I")).copy(); top = np.where(base.max(1) > 128)[0].min()
        acc = np.asarray(glyph_raw("Í")); acc = acc[:top - 1]
        cols = np.where(acc.max(0) > 0)[0]; acc = acc[:, cols.min():cols.max() + 1]
        x0 = max(0, (base.shape[1] - acc.shape[1]) // 2 + int(0.06 * capH))
        w = min(acc.shape[1], base.shape[1] - x0)
        base[:acc.shape[0], x0:x0 + w] = np.maximum(base[:acc.shape[0], x0:x0 + w], acc[:, :w])
        return Image.fromarray(base, "L")
    return glyph_raw(c)

def glyph_raw(c):
    bb = ft.getbbox(c); gw, gh = bb[2] - bb[0], bb[3] - bb[1]
    im = Image.new("L", (gw + 8 * SS, int(capH * 1.6)), 0)
    ImageDraw.Draw(im).text((4 * SS - bb[0], int(capH * 0.3) - ft.getbbox("H")[1]), c, font=ft, fill=255)
    im = im.crop((0, 0, im.width, im.height))
    cols = np.where(np.asarray(im).max(0) > 0)[0]; im = im.crop((cols.min(), 0, cols.max() + 1, im.height))
    im = im.resize((max(1, round(im.width * SX)), im.height), Image.LANCZOS)
    # la compresión adelgaza los palos verticales: se engrosan solo en horizontal para volver al trazo parejo del original
    d = int(round(DIL * capH))
    if d > 0:
        a = np.pad(np.asarray(im), ((0, 0), (d, d)))
        a = np.max(np.stack([a[:, k:k + a.shape[1] - 2 * d] for k in range(2 * d + 1)]), 0)
        im = Image.fromarray(a.astype(np.uint8), "L")
    return im

def render(text, cx, cy, name, xmin=70, xmax=1010):
    gl = [glyph(c) for c in text]; gap = GAP * capH; space = max(0.0, 1.0 * capH - 2 * gap)   # espacio entre palabras: 1,0 del alto de borde a borde
    widths = [g.width if g else space for g in gl]
    total = sum(widths) + gap * (len(gl) - 1)
    line = Image.new("L", (int(total) + 2, int(capH * 1.6)), 0); x = 0.0
    for g, w in zip(gl, widths):
        if g: line.paste(g, (int(round(x)), 0), g)
        x += w + gap
    line = line.resize((max(1, round(line.width / SS)), max(1, round(line.height / SS))), Image.LANCZOS)
    canvas = Image.new("L", (W, H), 0)
    cx = min(cx, xmax - line.width / 2); cx = max(cx, xmin + line.width / 2)   # dentro de la zona libre
    x0 = int(round(cx - line.width / 2)); y0 = int(round(cy - line.height / 2))
    canvas.paste(line, (x0, y0))
    a = np.asarray(canvas).astype(np.float32) / 255
    halo = np.asarray(canvas.filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
    alpha = np.clip(a + 0.10 * halo / max(halo.max(), 1e-6) * 0.9, 0, 1)   # halo suave (original: ~5–10/255)
    rgba = np.zeros((H, W, 4), np.uint8); rgba[..., :3] = 255; rgba[..., 3] = (alpha * 255).round()
    Image.fromarray(rgba, "RGBA").save(os.path.join(out, name))
    ys, xs = np.where(a > 0.5)
    print(f"{name}: '{text}' x {xs.min()}–{xs.max()} y {ys.min()}–{ys.max()} (ancho {xs.max()-xs.min()+1}, alto {ys.max()-ys.min()+1})")

STEMS = stems()
if os.environ.get("TEXTO"):   # texto libre en el mismo estilo: TEXTO="..." CX=540 CY=600 SALIDA=nombre.png
    render(os.environ["TEXTO"], float(os.environ.get("CX", 540)), float(os.environ.get("CY", 600)),
           os.environ.get("SALIDA", "texto.png"), xmin=60, xmax=1020)
    sys.exit(0)
# centros de los rótulos originales: derecha (570–903, 599–625), izquierda (146–509, 797–822).
# Zona libre medida en toda la animación: arriba de y=683 todo el ancho; a la altura del izquierdo, x 86–595.
render("ACCIONISTA SERIAL", 736.5, 612, "rotulo_der.png", xmax=1000)
render("PERFECCIONISTA", 327.5, 809.5, "rotulo_izq.png", xmin=80, xmax=575)
# capa única con los dos rótulos
a = np.asarray(Image.open(os.path.join(out, "rotulo_der.png"))).copy()
b = np.asarray(Image.open(os.path.join(out, "rotulo_izq.png")))
a[..., 3] = np.maximum(a[..., 3], b[..., 3])
Image.fromarray(a, "RGBA").save(os.path.join(out, "rotulos.png"))
