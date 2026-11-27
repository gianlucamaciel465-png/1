# Publicación de feed «Mar de fondo» · Capítulo 01 (27/11/2026). Carrusel 4:5 de 7 láminas, 2 con video real, sin precio.
# Idea (Cata, aprobada por Roma): «mar de fondo» es lo que se mueve antes de que se vea; la lámina 6 revela que son los
# primeros 100 (Founders Privée). Estatus por imagen y casi sin texto. Material real: PRODUCTO/ (Display P3 → sRGB) y tomas
# de Gianluca del 26/11 (IMG_5327, IMG_5361; HLG → SDR con la receta de CLAUDE.md, en TRABAJO/feed/).
# Uso: python3 scripts/ig/mar_de_fondo.py SALIDA_DIR
import sys, os, io, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageCms
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fomo"))
from comun import Lector, Codificador, fuente, suave, fill_cover, grano, RAIZ

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
PW, PH = 1080, 1350
BLANCO = (255, 255, 255)
HUMO = (214, 225, 233)        # papel celeste humo
NOCHE = (16, 28, 48)          # azul noche
M = 84                         # margen (la grilla 3:4 recorta ~34 px por lado)
FEED = os.path.join(RAIZ, "TRABAJO/feed")
V = "v02"

TX = json.load(open(os.path.join(os.path.dirname(__file__), "mar_de_fondo_textos.json")))


# ---------- imagen ----------
def srgb(p):
    im = Image.open(p)
    icc = im.info.get("icc_profile")
    if icc:
        im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile("sRGB"),
                                       outputMode="RGB")
    from PIL import ImageOps
    return ImageOps.exif_transpose(im).convert("RGB")


def grado(a, sat=0.84, lev=0.026):
    """lujo silencioso: negros apenas levantados, altas redondeadas, menos saturación salvo el celeste del estampado."""
    x = a.astype(np.float32) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b)[..., None]
    celeste = np.clip((b - np.maximum(r, g)) * 8, 0, 1)[..., None]
    x = lum + (x - lum) * (sat + (1 - sat) * celeste)
    x = lev + (1 - lev - 0.02) * np.power(np.clip(x, 0, 1), 1.05)
    x = np.where(x > 0.84, 0.84 + (x - 0.84) * 0.7, x)
    x[..., 2] *= 1.0 + 0.010 * (1 - lum[..., 0])   # sombras apenas frías
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


def parrafo(img, x, y, s, fk, size, color, ancho_max, inter=1.32, al="l", sombra=0.0):
    f = fuente(fk, size)
    lineas, ln = [], ""
    for p in s.split():
        prueba = (ln + " " + p).strip()
        if f.getlength(prueba) > ancho_max and ln:
            lineas.append(ln); ln = p
        else:
            ln = prueba
    lineas.append(ln)
    if len(lineas) > 1 and len(lineas[-1].split()) == 1:          # sin viudas: baja la última palabra del renglón anterior
        a, _, b = lineas[-2].rpartition(" ")
        if a: lineas[-2], lineas[-1] = a, b + " " + lineas[-1]
    for i, l in enumerate(lineas):
        escribir(img, x, y + i * size * inter, l, fk, size, color, al=al, sombra=sombra)
    return y + len(lineas) * size * inter


def compo(base, cap):
    im = Image.fromarray(base).convert("RGBA")
    im.alpha_composite(cap)
    return np.asarray(im.convert("RGB"))


def guardar_png(a, nombre):
    p = os.path.join(OUT, nombre)
    Image.fromarray(a).save(p, optimize=True, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    return p


def foto(nombre, cx=0.5, cy=0.5, zoom=1.0):
    return grado(np.asarray(fill_cover(srgb(os.path.join(RAIZ, "PRODUCTO", nombre)), PW, PH, cx=cx, cy=cy, zoom=zoom)))


def frames(src, t0, n, y0):
    L = Lector(src, t0, 1080, 1920)
    out = [L.cuadro()[y0:y0 + PH].copy() for _ in range(n)]
    L.cerrar(); return out


control = {}
nom = lambda n, ext: f"ROCCE_FEED_MAR_DE_FONDO_{n:02d}_{V}.{ext}"


def lamina_video(n, fr, cap=None, entra=10):
    cod = Codificador(os.path.join(OUT, nom(n, "mp4")), w=PW, h=PH)
    for k, f in enumerate(fr):
        a = grado(f)
        if cap is not None:
            b = Image.fromarray(a).convert("RGBA")
            al = suave(min(1.0, k / entra))
            cc = cap if al >= 1 else Image.fromarray((np.asarray(cap).astype(np.float32) * np.array([1, 1, 1, al])).astype(np.uint8), "RGBA")
            b.alpha_composite(cc); a = np.asarray(b.convert("RGB"))
        cod.poner(grano(a, 2.2, k))
    cod.cerrar()
    control[nom(n, "mp4")] = dict(cuadros=cod.n, segundos=round(cod.n / 30, 2))


# 01 · portada: la espalda puesta frente al mar
t = TX["01"]
a = foto("blanca_puesta_espalda_balcon_playa.jpg", cy=0.52)
a = degrade(degrade(a, 0, 300, 0.28), PH - 560, PH, 0.62, arriba=False)
c = capa()
escribir(c, PW / 2, 70, t["arriba"], "inter_sb", 26, BLANCO, track=12, al="c", sombra=0.45)
_a = ancho(t["titulo"] + " ", fuente("serif", 150)); _b = ancho(t["titulo_cursiva"], fuente("serif_i", 150))
_x = (PW - _a - _b) / 2
escribir(c, _x, PH - 300, t["titulo"] + " ", "serif", 150, BLANCO, sombra=0.42, radio=20)
escribir(c, _x + _a, PH - 300, t["titulo_cursiva"], "serif_i", 150, BLANCO, sombra=0.42, radio=20)
escribir(c, PW / 2, PH - 118, t["abajo"], "inter_m", 24, BLANCO, track=11, al="c", sombra=0.45)
guardar_png(grano(compo(a, c), 2.2, 1), nom(1, "png"))

# 02 · video: del macro a la espalda completa (IMG_5327, 1,9–5,1 s; antes de 1,9 s la toma pasa por el pasto, desenfocada)
lamina_video(2, frames(os.path.join(FEED, "sdr_5327.mp4"), 1.9, 97, 300))

# 03 · macro del estampado frontal de la negra
a = foto("negra_frente_detalle_estampado.jpg", cy=0.48, zoom=1.04)
guardar_png(grano(a, 2.2, 3), nom(3, "png"))

# 04 · detrás de escena: el teléfono en alto, la blanca en la roca, la espalda negra
t = TX["04"]
a = foto("detras_escena_negra_puesta_fotografia_blanca_rocas.jpg", cy=0.5)
a = degrade(a, 0, 520, 0.55)
c = capa()
yy = 120
for i, ln in enumerate(t["titulo"]):
    escribir(c, M, yy + i * 92, ln, "serif_i" if i == len(t["titulo"]) - 1 and t.get("cursiva_ultima") else "serif", 84,
             BLANCO, sombra=0.45)
guardar_png(grano(compo(a, c), 2.2, 4), nom(4, "png"))

# 05 · video: de las dos remeras a la placa (IMG_5361, 0–2,9 s)
t = TX["05"]
fr = [degrade(f, 0, 520, 0.5) for f in frames(os.path.join(FEED, "sdr_5361.mp4"), 0.0, 87, 380)]
c = capa()
for i, ln in enumerate(t["titulo"]):
    escribir(c, M, 110 + i * 92, ln, "serif", 84, BLANCO, sombra=0.5)
escribir(c, M, 110 + len(t["titulo"]) * 92 + 24, t["chico"], "inter_m", 42, BLANCO, sombra=0.5)
lamina_video(5, fr, c)

# 06 · papel celeste humo: la revelación
t = TX["06"]
a = np.full((PH, PW, 3), HUMO, np.uint8)
c = capa()
escribir(c, M, 150, t["rotulo"], "inter_sb", 22, NOCHE, track=12)
y = 230
for i, ln in enumerate(t["titulo"]):
    escribir(c, M, y, ln, "serif_i" if i == len(t["titulo"]) - 1 and t.get("cursiva_ultima") else "serif", 118, NOCHE)
    y += 128
ImageDraw.Draw(c).line([(M, y + 70), (M + 64, y + 70)], fill=NOCHE + (255,), width=2)
y = y + 120
for p in t["cuerpo"]:
    y = parrafo(c, M, y, p, "inter_m", 42, NOCHE, PW - 2 * M - 20) + 28
guardar_png(grano(compo(a, c), 1.0, 6), nom(6, "png"))

# 07 · cierre: las dos espaldas en la arena + logo original (ficha #FEFEFE) + lema
t = TX["07"]
a = foto("blanca_negra_espalda_playa_2.jpg", cy=0.58)
a = degrade(a, PH - 470, PH, 0.6, arriba=False)
c = capa()
_s = 72                                    # lema grande (guion de Fede): serif, ajustado al ancho seguro de la grilla
while ancho(t["lema"], fuente("serif", _s)) > PW - 2 * M - 40: _s -= 2
escribir(c, PW / 2, PH - 276, t["lema"], "serif", _s, BLANCO, al="c", sombra=0.5, radio=18)
escribir(c, PW / 2, PH - 168, t["web"], "serif_i", 48, BLANCO, al="c", sombra=0.45)
b = Image.fromarray(compo(a, c)).convert("RGBA")
lg = 210
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
