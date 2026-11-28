# Pines de Pinterest P16–P18 (28/11/2026; mismo sistema que P13–P15 del 27/11), rama aprobada por Gianluca el 25/11 (pines v06/v07): foto de otra persona, sola,
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
V = "v01"
ANCHO = {16: 0.70, 17: 0.74, 18: 0.70}
BAJAR = {}   # opción para bajar la toma si la cabeza queda alta (no se usa en P16–P18)

PINES = [
    # (n, slug, video, t, centro x (0–1), líneas, oscurecer arriba)
    (16, "titular", "43495", 0.70, 0.55, ["NO NECESITÁS", "PÚBLICO", "PARA ENTRENAR", "COMO TITULAR."], 0.45),
    (17, "hecho", "610", 0.50, 0.57, ["NO TERMINÁS", "CUANDO TE CANSÁS.", "TERMINÁS", "CUANDO ESTÁ HECHO."], 0.60),
    (18, "kilometro", "32807", 0.01, 0.0, ["NADIE VE", "EL KILÓMETRO 1.", "TODOS VEN", "LA LLEGADA."], 0.45),
]


def cuadro(vid, frac, cx):
    src = os.path.join(MX, vid + ".mp4")
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                             capture_output=True, text=True).stdout)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{d * frac:.3f}", "-i", src, "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height", "-of", "csv=p=0", src],
                                   capture_output=True, text=True).stdout.strip().split(","))
    a = np.frombuffer(raw, np.uint8).reshape(h, w, 3)
    if w > h:  # horizontal: ventana 2:3 a lo alto, centrada en cx
        cw = h * 2 // 3; x0 = int(min(w - cw, max(0, cx * w - cw / 2)))
        return Image.fromarray(a[:, x0:x0 + cw]).resize((PW, PH), Image.LANCZOS)
    # vertical: ventana 2:3 a lo ancho; cx se usa como posición vertical (0 = arriba, 1 = abajo)
    ch = w * 3 // 2; y0 = int((h - ch) * cx)
    return Image.fromarray(a[y0:y0 + ch, :]).resize((PW, PH), Image.LANCZOS)


def bajar(im, k):
    """Achica la toma al k y la apoya abajo; arriba, las primeras filas de cielo estiradas y desenfocadas (sin persona)."""
    w, h = int(PW * k), int(PH * k)
    chico = im.resize((w, h), Image.LANCZOS)
    fondo = im.crop((0, 0, PW, int(PH * 0.10))).resize((PW, PH), Image.BICUBIC).filter(ImageFilter.GaussianBlur(18))
    lado = im.resize((PW, PH)).filter(ImageFilter.GaussianBlur(30))
    base = Image.composite(fondo, lado, Image.linear_gradient("L").resize((PW, PH)).point(lambda v: 255 - v))
    m = Image.new("L", (w, h), 255)
    m = m.filter(ImageFilter.GaussianBlur(0))
    borde = Image.new("L", (w, h), 0); ImageDraw.Draw(borde).rectangle((40, 60, w - 41, h), fill=255)
    borde = borde.filter(ImageFilter.GaussianBlur(28))
    base.paste(chico, ((PW - w) // 2, PH - h), borde)
    return base


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
    im = cuadro(vid, frac, cx)
    if n in BAJAR: im = bajar(im, BAJAR[n])
    im = grado(im, g)
    base, bb = frase(im, lineas, ANCHO.get(n, 0.82))
    base = logo(base, bb[3] + 34)
    p = os.path.join(OUT, f"ROCCE_LIFE_PIN_{n}_{slug}_{V}.png")
    base.convert("RGB").save(p, optimize=True, icc_profile=srgb)
    print(p, bb)
