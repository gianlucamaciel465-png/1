# Pines de Pinterest P13–P15 (27/11/2026), rama aprobada por Gianluca el 25/11 (pines v06/v07): foto de otra persona, sola,
# frase en mayúsculas condensadas (Anton) en el tercio superior, el primer renglón abre la tensión y el último (celeste) la
# resuelve; logo original sin fondo, chico, justo debajo de la frase, con borde blanco fino sobre fondo oscuro.
# Sin Black Friday en la imagen (el pin circula meses). Fotos: cuadros de videos de Mixkit (licencia libre de Mixkit: uso
# comercial, sin atribución), en TRABAJO/pines/mixkit/ (fuera de git). Uso: python3 scripts/pines/pines_27.py SALIDA_DIR
import os, sys, io, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageCms

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
PW, PH = 1000, 1500
ANTON = os.path.join(RAIZ, "scripts/fuentes/Anton-Regular.ttf")
CEL = (170, 208, 240)
MX = os.path.join(RAIZ, "TRABAJO/pines/mixkit")
V = "v03"
ANCHO = {13: 0.72}   # P13: frase más chica para que no toque al jugador (la cabeza queda a y≈600)

PINES = [
    # (n, slug, video, t, centro x (0–1), líneas, oscurecer arriba)
    (13, "el_segundo", "44448", 0.575, 0.36, ["EL PRIMER TIRO", "CASI NUNCA ENTRA.", "POR ESO EXISTE", "EL SEGUNDO."], 0.55),
    (14, "el_gol", "43494", 0.15, 0.52, ["TE VAN A RECORDAR", "POR EL PENAL ERRADO", "HASTA QUE", "HAGAS EL GOL."], 0.35),
    (15, "cuenta_doble", "44448", 0.944, 0.361, ["A LAS 6 AM", "NO APLAUDE NADIE.", "POR ESO", "CUENTA DOBLE."], 0.55),
]


def cuadro(vid, frac, cx):
    src = os.path.join(MX, vid + ".mp4")
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                             capture_output=True, text=True).stdout)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{d * frac:.3f}", "-i", src, "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(1080, 1920, 3)
    cw = 720; x0 = int(min(1920 - cw, max(0, cx * 1920 - cw / 2)))
    return Image.fromarray(a[:, x0:x0 + cw]).resize((PW, PH), Image.LANCZOS)


def grado(im, g_arr):
    x = np.asarray(im).astype(np.float32) / 255
    lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    x = lum + (x - lum) * 0.82                                     # menos saturación
    x = 0.02 + 0.96 * np.power(np.clip(x, 0, 1), 1.12)             # más contraste, negros apenas levantados
    yy = np.arange(PH, dtype=np.float32)[:, None, None]
    m = 1 - g_arr * np.clip(1 - yy / (PH * 0.55), 0, 1) ** 1.4     # oscurece el tercio superior (texto)
    x *= m
    rng = np.random.default_rng(7)
    x += rng.normal(0, 0.012, x.shape[:2])[..., None]              # grano
    return Image.fromarray(np.clip(x * 255, 0, 255).astype(np.uint8))


def frase(img, lineas, ancho=0.82):
    """Anton centrado; renglón más ancho ≈ 82 % del ancho; degradé blanco→gris claro, sombra marcada; último renglón celeste."""
    s = 200
    while max(ImageFont.truetype(ANTON, s).getlength(l) for l in lineas) > PW * ancho: s -= 2
    f = ImageFont.truetype(ANTON, s)
    lh = int(s * 1.08)
    y0 = int(PH * (0.075 if ancho >= 0.8 else 0.06))
    capa = Image.new("L", (PW, PH), 0); dc = ImageDraw.Draw(capa)
    for i, l in enumerate(lineas):
        dc.text(((PW - f.getlength(l)) / 2, y0 + i * lh), l, font=f, fill=255)
    sombra = capa.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.85))
    som2 = Image.new("L", (PW, PH), 0); som2.paste(capa, (0, 6)); som2 = som2.filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * 0.6))
    base = img.convert("RGBA")
    for sm in (sombra, som2):
        sh = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); sh.putalpha(sm); base = Image.alpha_composite(base, sh)
    # relleno: degradé vertical por renglón (blanco → gris muy claro); el último en celeste
    rel = np.zeros((PH, PW, 3), np.float32)
    for i, l in enumerate(lineas):
        ya, yb = y0 + i * lh, y0 + i * lh + lh
        t = np.linspace(0, 1, yb - ya)[:, None]
        c0, c1 = (np.array(CEL, np.float32), np.array(CEL, np.float32) * 0.9) if i == len(lineas) - 1 else \
                 (np.array([255, 255, 255], np.float32), np.array([222, 226, 230], np.float32))
        rel[ya:yb] = (c0 * (1 - t) + c1 * t)[:, None, :]
    txt = Image.fromarray(rel.astype(np.uint8)).convert("RGBA"); txt.putalpha(capa)
    base = Image.alpha_composite(base, txt)
    bbox = capa.getbbox()
    return base, bbox


def logo(base, y, alto_rel=0.12):
    lg = Image.open(os.path.join(RAIZ, "LOGO/ROCCE_logo_sin_fondo.png")).convert("RGBA")
    lg = lg.crop(lg.getbbox())
    h = int(PW * alto_rel); w = int(lg.width * h / lg.height)
    lg = lg.resize((w, h), Image.LANCZOS)
    a = lg.split()[3]
    borde = a.filter(ImageFilter.MaxFilter(5))                       # borde blanco fino (fondo oscuro)
    b = Image.new("RGBA", lg.size, (255, 255, 255, 0)); b.putalpha(borde)
    x = (PW - w) // 2
    base.alpha_composite(b, (x, y)); base.alpha_composite(lg, (x, y))
    return base


srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
for n, slug, vid, frac, cx, lineas, g in PINES:
    im = grado(cuadro(vid, frac, cx), g)
    base, bb = frase(im, lineas, ANCHO.get(n, 0.82))
    base = logo(base, bb[3] + 34)
    p = os.path.join(OUT, f"ROCCE_LIFE_PIN_{n}_{slug}_{V}.png")
    base.convert("RGB").save(p, optimize=True, icc_profile=srgb)
    print(p, bb)
