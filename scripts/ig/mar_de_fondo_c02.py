# Publicación de feed «Mar de fondo» · Capítulo 02 «De cerca» (28/11/2026). Carrusel 4:5 de 7 láminas, 2 con video real, sin
# precio. Guion de Fede (04_fede_guiones.md §6) con los cambios de Roma (06_roma_revision_guiones.md §6). Mismo sistema que el
# capítulo 01 (scripts/ig/mar_de_fondo.py): grado «lujo silencioso», Instrument Serif + Inter espaciada, papel celeste humo.
# En las dos láminas de video el texto va en una banda de papel debajo de la ventana (de cerca: el detalle no se tapa).
# Material real: IMG_7793 y IMG_7857 (4K vertical), IMG_7896, tomas del 26/11 (IMG_5325, IMG_5333), IMG_3453 (HLG → SDR con
# la corrección de CAMPANA, negra carbón) y PRODUCTO/blanca_frente_detalle_estampado.jpg (Display P3 → sRGB).
# Uso: python3 scripts/ig/mar_de_fondo_c02.py SALIDA_DIR
import sys, os, io, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageCms, ImageOps
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fomo"))
from comun import Lector, Codificador, fuente, suave, fill_cover, grano, RAIZ

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
PW, PH = 1080, 1350
BLANCO = (255, 255, 255)
HUMO = (214, 225, 233)
NOCHE = (16, 28, 48)
CEL = (170, 208, 240)
M = 84
V = "v01"
OR = os.path.join(RAIZ, "ORIGINALES")
GL = os.path.join(RAIZ, "TRABAJO/fomo/gl")
S3453 = os.path.join(RAIZ, "TRABAJO/jornada3/h28/sdr_3453.mp4")
VENTANA = 1110                       # alto de la ventana de video en las láminas 2 y 5; debajo, papel


# ---------- imagen ----------
def srgb(p):
    im = Image.open(p)
    icc = im.info.get("icc_profile")
    if icc:
        im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile("sRGB"),
                                       outputMode="RGB")
    return ImageOps.exif_transpose(im).convert("RGB")


def cuadro(src, t):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", "-f", "image2pipe",
                        "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(b)).convert("RGB")


def recorte(im, x0, y0, w, h, ow, oh):
    assert 0 <= x0 and 0 <= y0 and x0 + w <= im.width and y0 + h <= im.height, (x0, y0, w, h, im.size)
    return im.crop((x0, y0, x0 + w, y0 + h)).resize((ow, oh), Image.LANCZOS)


def grado(a, sat=0.84, lev=0.026):
    x = a.astype(np.float32) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b)[..., None]
    celeste = np.clip((b - np.maximum(r, g)) * 8, 0, 1)[..., None]
    x = lum + (x - lum) * (sat + (1 - sat) * celeste)
    x = lev + (1 - lev - 0.02) * np.power(np.clip(x, 0, 1), 1.05)
    x = np.where(x > 0.84, 0.84 + (x - 0.84) * 0.7, x)
    x[..., 2] *= 1.0 + 0.010 * (1 - lum[..., 0])
    return np.clip(x * 255, 0, 255).astype(np.uint8)


def degrade(a, y0, y1, g, arriba=True):
    yy = np.arange(a.shape[0], dtype=np.float32)
    t = np.clip((yy - y0) / max(1.0, y1 - y0), 0, 1)
    t = t * t * (3 - 2 * t)
    m = (1 - t) if arriba else t
    return (a.astype(np.float32) * (1 - g * m)[:, None, None]).astype(np.uint8)


# ---------- texto ----------
def capa():
    return Image.new("RGBA", (PW, PH), (0, 0, 0, 0))


def ancho(s, f, track=0):
    return sum(f.getlength(c) for c in s) + track * (len(s) - 1) if track else f.getlength(s)


def _txt(d, x, y, s, f, fill, track):
    if not track:
        d.text((x, y), s, font=f, fill=fill); return
    for c in s:
        d.text((x, y), c, font=f, fill=fill); x += f.getlength(c) + track


def escribir(img, x, y, s, fk, size, color, track=0, al="l", sombra=0.0, radio=16):
    f = fuente(fk, size)
    w = ancho(s, f, track)
    x0 = x - w / 2 if al == "c" else (x - w if al == "r" else x)
    if sombra:
        sm = Image.new("L", img.size, 0)
        _txt(ImageDraw.Draw(sm), x0, y + 3, s, f, 255, track)
        sm = sm.filter(ImageFilter.GaussianBlur(radio))
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(sm.point(lambda v: int(v * sombra)))
        img.alpha_composite(sh)
    _txt(ImageDraw.Draw(img), x0, y, s, f, color + (255,), track)
    return w


def estrella(d, cx, cy, r, color):
    pts = []
    for i in range(10):
        a = -np.pi / 2 + i * np.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * np.cos(a), cy + rr * np.sin(a)))
    d.polygon(pts, fill=color + (255,))


def con_estrella(img, x, y, partes, fk, size, color, color_estrella, al="l", sombra=0.0):
    """escribe partes[0] + ★ + partes[1] (Instrument Serif no tiene la estrella: va dibujada, del alto de la x)."""
    f = fuente(fk, size)
    asc, _ = f.getmetrics()
    xh = f.getbbox("x")
    r = (xh[3] - xh[1]) * 0.62
    w_e = r * 2.0
    w = ancho(partes[0], f) + w_e + ancho(partes[1], f)
    x0 = x - w / 2 if al == "c" else x
    if sombra:
        sm = Image.new("L", img.size, 0); ds = ImageDraw.Draw(sm)
        ds.text((x0, y + 3), partes[0], font=f, fill=255)
        estrella(ds, x0 + ancho(partes[0], f) + w_e / 2, y + 3 + (xh[1] + xh[3]) / 2, r, (255,))
        ds.text((x0 + ancho(partes[0], f) + w_e, y + 3), partes[1], font=f, fill=255)
        sm = sm.filter(ImageFilter.GaussianBlur(14))
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(sm.point(lambda v: int(v * sombra)))
        img.alpha_composite(sh)
    d = ImageDraw.Draw(img)
    d.text((x0, y), partes[0], font=f, fill=color + (255,))
    estrella(d, x0 + ancho(partes[0], f) + w_e / 2, y + (xh[1] + xh[3]) / 2, r, color_estrella)
    d.text((x0 + ancho(partes[0], f) + w_e, y), partes[1], font=f, fill=color + (255,))
    return w


def ajustar(s, fk, size, maximo):
    while ancho(s, fuente(fk, size)) > maximo: size -= 2
    return size


def compo(base, cap):
    im = Image.fromarray(base).convert("RGBA")
    im.alpha_composite(cap)
    return np.asarray(im.convert("RGB"))


def guardar_png(a, nombre):
    p = os.path.join(OUT, nombre)
    Image.fromarray(a).save(p, optimize=True, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    return p


control = {}
nom = lambda n, ext: f"ROCCE_FEED_MAR_DE_FONDO_C02_{n:02d}_{V}.{ext}"


def neutro_oscuros(a, umbral=0.42, ancho_=0.22):
    """quita el tinte cálido de los oscuros (la negra de 3453 queda marrón con la luz interior); la piel y el estampado no cambian."""
    x = a.astype(np.float32) / 255.0
    lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    w = np.clip((umbral - lum) / ancho_, 0, 1)
    x = x + (lum - x) * w
    return np.clip(x * 255, 0, 255).astype(np.uint8)


def balance(a, k):
    """multiplica cada canal (la blanca de 5325 sale lavanda: blanco medido 216/208/222)."""
    return np.clip(a.astype(np.float32) * np.array(k, np.float32), 0, 255).astype(np.uint8)


def lamina_video(n, src, t0, nfr, y0, papel, neutro=False, wb=None):
    """ventana de video (1080×VENTANA, recorte desde y0 del cuadro vertical) + banda de papel con el texto fijo debajo."""
    L = Lector(src, t0, 1080, 1920)
    cod = Codificador(os.path.join(OUT, nom(n, "mp4")), w=PW, h=PH)
    pap = np.full((PH - VENTANA, PW, 3), HUMO, np.uint8)
    pap = compo(np.vstack([np.zeros((VENTANA, PW, 3), np.uint8), pap]), papel)[VENTANA:]
    for k in range(nfr):
        f = L.cuadro()[y0:y0 + VENTANA]
        f = neutro_oscuros(f) if neutro else f
        f = balance(f, wb) if wb else f
        a = np.vstack([grado(f), pap])
        cod.poner(grano(a, 2.2, k))
    L.cerrar(); cod.cerrar()
    control[nom(n, "mp4")] = dict(cuadros=cod.n, segundos=round(cod.n / 30, 2), fuente=os.path.basename(src), desde=t0,
                                  recorte_y=y0)


def papel_textos(titulo, chico, estrella_en=None):
    c = capa()
    y = VENTANA + 58
    if estrella_en:
        size = 50
        while ancho(estrella_en[0] + "MM" + estrella_en[1], fuente("serif", size)) > PW - 2 * M: size -= 2
        con_estrella(c, M, y, estrella_en, "serif", size, NOCHE, NOCHE)
    else:
        size = ajustar(titulo, "serif", 56, PW - 2 * M)
        escribir(c, M, y, titulo, "serif", size, NOCHE)
    escribir(c, M, y + 84, chico, "inter_m", 34, NOCHE)
    return c


# 01 · portada: la negra puesta de espaldas (IMG_7793, 3,5 s; balcón, playa y ciudad). Hace par con la blanca del capítulo 01.
im = cuadro(os.path.join(OR, "IMG_7793.mov"), 3.5)               # 2160×3840 tras la rotación
a = grado(np.asarray(recorte(im, 0, 100, 2160, 2700, PW, PH)))
a = degrade(degrade(a, 0, 260, 0.30), PH - 470, PH, 0.66, arriba=False)
c = capa()
escribir(c, PW / 2, 64, "ROCCÉ", "inter_sb", 26, BLANCO, track=12, al="c", sombra=0.5)
_a = ancho("Mar ", fuente("serif", 140)); _b = ancho("de fondo", fuente("serif_i", 140))
_x = (PW - _a - _b) / 2
escribir(c, _x, PH - 262, "Mar ", "serif", 140, BLANCO, sombra=0.42, radio=20)
escribir(c, _x + _a, PH - 262, "de fondo", "serif_i", 140, BLANCO, sombra=0.42, radio=20)
escribir(c, PW / 2, PH - 92, "CAPÍTULO 02 · DE CERCA", "inter_m", 24, BLANCO, track=11, al="c", sombra=0.45)
guardar_png(grano(compo(a, c), 2.2, 1), nom(1, "png"))

# 02 · video: el parche de cerca (IMG_5325 12,9–15,9 s: ROC → OCC con el pespunte → CÉ / Privée), sin audio, en loop
lamina_video(2, os.path.join(GL, "sdr_5325_full.mp4"), 12.9, 90, 0,
             papel_textos("En la espalda, ROCCÉ no está impreso.", "ROCCÉ es un parche de jean con pespunte."),
             wb=(1.0, 1.035, 0.975))

# 03 · díptico: la negra a la sombra (IMG_7793, 4,0 s) y al sol (IMG_5333, 2,4 s)
arriba = grado(np.asarray(recorte(cuadro(os.path.join(OR, "IMG_7793.mov"), 4.0), 0, 1250, 2160, 1340, PW, 670)))
abajo = grado(np.asarray(recorte(cuadro(os.path.join(GL, "sdr_5333.mp4"), 2.4), 0, 440, 1080, 670, PW, 670)))
arriba = degrade(arriba, 670 - 230, 670, 0.55, arriba=False)
abajo = degrade(abajo, 670 - 210, 670, 0.6, arriba=False)
a = np.vstack([arriba, np.full((10, PW, 3), HUMO, np.uint8), abajo])
c = capa()
s1 = "En la negra, el jean es negro: tono sobre tono."
escribir(c, M, 670 - 92, s1, "serif", ajustar(s1, "serif", 50, PW - 2 * M), BLANCO, sombra=0.55)
escribir(c, M, PH - 100, "Al sol, se marca.", "serif_i", 56, BLANCO, sombra=0.55)
guardar_png(grano(compo(a, c), 2.2, 3), nom(3, "png"))

# 04 · la estrella: frente de la blanca (PRODUCTO/blanca_frente_detalle_estampado.jpg)
a = grado(np.asarray(fill_cover(srgb(os.path.join(RAIZ, "PRODUCTO", "blanca_frente_detalle_estampado.jpg")), PW, PH, cy=0.62)))
c = capa()
escribir(c, PW / 2, 92, "La estrella va", "serif", 84, NOCHE, al="c")
escribir(c, PW / 2, 186, "donde falta una letra.", "serif_i", 84, NOCHE, al="c")
guardar_png(grano(compo(a, c), 1.6, 4), nom(4, "png"))

# 05 · video: los dedos sobre el pecho de la negra (IMG_3453 1,9–4,6 s: el estampado entra entero; 0,2–1,6 se sale del cuadro)
lamina_video(5, S3453, 1.9, 81, 715,
             papel_textos(None, "Gris claro sobre negro.", estrella_en=("En el pecho, ROCCÉ y so f", "cking close.")),
             neutro=True)

# 06 · de lejos / de cerca: la blanca puesta frente al mar (IMG_7857, 1,0 s)
a = grado(np.asarray(recorte(cuadro(os.path.join(OR, "IMG_7857.mov"), 1.0), 0, 400, 2160, 2700, PW, PH)))
a = degrade(a, PH - 520, PH, 0.66, arriba=False)
c = capa()
escribir(c, M, PH - 262, "De lejos se lee el nombre.", "serif", 64, BLANCO, sombra=0.5)
escribir(c, M, PH - 182, "De cerca se ve el trabajo.", "serif_i", 64, BLANCO, sombra=0.5)
guardar_png(grano(compo(a, c), 2.2, 6), nom(6, "png"))

# 07 · cierre: las dos remeras y la ola (IMG_7896, 5,7 s, a 1,16×) + ficha del logo original
im = cuadro(os.path.join(OR, "IMG_7896.mov"), 5.7)
cw, ch = int(2160 / 1.16) // 2 * 2, int(2160 / 1.16 * PH / PW) // 2 * 2
a = grado(np.asarray(recorte(im, 39, 907, cw, ch, PW, PH)))
a = degrade(a, PH - 470, PH, 0.6, arriba=False)
c = capa()
escribir(c, PW / 2, PH - 262, "Mirala de cerca.", "serif", 84, BLANCO, al="c", sombra=0.5, radio=18)
escribir(c, PW / 2, PH - 150, "rocce.shop", "serif_i", 48, BLANCO, al="c", sombra=0.45)
b = Image.fromarray(compo(a, c)).convert("RGBA")
lg = 200
logo = Image.open(os.path.join(RAIZ, "LOGO/rocce_logo.png")).convert("RGB").resize((lg, lg), Image.LANCZOS)
mask = Image.new("L", (lg, lg), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, lg - 1, lg - 1], radius=int(lg * 0.11), fill=255)
sh = Image.new("RGBA", (lg + 80, lg + 80), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle([40, 46, 40 + lg, 46 + lg], radius=int(lg * 0.11), fill=(0, 0, 0, 90))
sh = sh.filter(ImageFilter.GaussianBlur(16))
x0, y0 = (PW - lg) // 2, 70
b.alpha_composite(sh, (x0 - 40, y0 - 40))
b.paste(logo, (x0, y0), mask)
guardar_png(grano(np.asarray(b.convert("RGB")), 2.2, 7), nom(7, "png"))

json.dump(control, open(os.path.join(OUT, "control_videos.json"), "w"), indent=1)
print(json.dumps(control, indent=1))
