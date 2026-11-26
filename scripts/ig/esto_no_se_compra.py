# Publicación de Instagram «Esto no se compra.» (carrusel 4:5 de 7 láminas, 2 con video real) + 3 historias interactivas
# (encuesta → quiz → revelación con link). Black Friday −25 % · $48.750 (antes $65.000) · envío gratis (rocce.shop, 26/11/2026).
# Apuesta: la portada afirma «Esto no se compra.» sobre la placa; cada lámina suma una pista (viene con la remera, el frente
# dice «casi», la espalda es de los que estuvieron desde el principio, la placa significa una sola cosa) y la 6 resuelve:
# «Seguir hasta lograrlo. Eso no se compra. Se cumple.» → CTA. Historias: ¿blanca o negra? (encuesta) → ¿qué significa la
# placa? (quiz, placa desenfocada) → «Seguir hasta lograrlo.» con el foco real de IMG_5359 (+ pregunta y link).
# Material real: tomas de Gianluca del 26/11 (IMG_5325, 5333, 5359, 5361; HLG → SDR) y fotos de PRODUCTO/ (Display P3 → sRGB).
# Uso: python3 scripts/ig/esto_no_se_compra.py SALIDA_DIR
import sys, os, io, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageCms
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fomo"))
from comun import Lector, Codificador, fuente, pegar, suave, fill_cover, grano, RAIZ, CELESTE

GL = os.path.join(RAIZ, "TRABAJO/fomo/gl")
OUT = sys.argv[1]
for d in ("publicacion", "historias", "guia"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
PW, PH = 1080, 1350  # lámina 4:5
SW, SH = 1080, 1920  # historia 9:16
PAPEL = (254, 254, 254)  # = fondo del logo
TINTA = (17, 17, 17)
BLANCO = (255, 255, 255)
M = 72
TOTAL = 7


# ---------- imagen ----------
def srgb(p):
    im = Image.open(p)
    icc = im.info.get("icc_profile")
    if icc:
        im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile("sRGB"),
                                       outputMode="RGB")
    return im.convert("RGB")


def grado(a):
    """Lujo silencioso: negros apenas levantados, altas que se redondean, menos saturación salvo el celeste."""
    x = a.astype(np.float32) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b)[..., None]
    celeste = np.clip((b - np.maximum(r, g)) * 8, 0, 1)[..., None]
    x = lum + (x - lum) * (0.86 + 0.14 * celeste)
    x = 0.022 + 0.958 * np.power(np.clip(x, 0, 1), 1.04)
    x = np.where(x > 0.84, 0.84 + (x - 0.84) * 0.72, x)
    x[..., 0] *= 1.0 + 0.012 * lum[..., 0]
    x[..., 2] *= 1.0 - 0.012 * lum[..., 0]
    return np.clip(x * 255, 0, 255).astype(np.uint8)


def degrade(a, y0, y1, g, arriba=True):
    """oscurece suave: arriba=True → máximo en y<=y0 y nada desde y1; arriba=False → nada hasta y0 y máximo desde y1."""
    yy = np.arange(a.shape[0], dtype=np.float32)
    t = np.clip((yy - y0) / max(1.0, y1 - y0), 0, 1)
    t = t * t * (3 - 2 * t)
    m = (1 - t) if arriba else t
    return (a.astype(np.float32) * (1 - g * m)[:, None, None]).astype(np.uint8)


# ---------- texto ----------
def capa(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def ancho(s, f, track=0):
    return sum(f.getlength(c) for c in s) + track * (len(s) - 1) if track else f.getlength(s)


def escribir(img, x, y, s, fk, size, color, track=0, al="l", sombra=0.0, radio=14):
    """escribe en una capa RGBA; al = l/c/r respecto de x."""
    f = fuente(fk, size)
    w = ancho(s, f, track)
    x0 = x - w / 2 if al == "c" else (x - w if al == "r" else x)
    if sombra:
        sm = Image.new("L", img.size, 0)
        _txt(ImageDraw.Draw(sm), x0, y + 3, s, f, 255, track)
        sm = sm.filter(ImageFilter.GaussianBlur(radio))
        sh = capa(*img.size); sh.putalpha(sm.point(lambda v: int(v * sombra)))
        img.alpha_composite(sh)
    _txt(ImageDraw.Draw(img), x0, y, s, f, color + (255,), track)
    return w


def _txt(d, x, y, s, f, fill, track):
    if not track:
        d.text((x, y), s, font=f, fill=fill); return
    for c in s:
        d.text((x, y), c, font=f, fill=fill); x += f.getlength(c) + track


def folio(c, n, color, sombra=0.0, abajo=True):
    escribir(c, M, 50, "ROCCÉ", "inter_sb", 22, color, track=7, sombra=sombra)
    escribir(c, PW - M, 52, "FOUNDERS PRIVÉE · 2026", "inter_m", 19, color, track=5, al="r", sombra=sombra)
    if abajo:
        escribir(c, PW - M, PH - 78, f"{n:02d} / {TOTAL:02d}", "inter_m", 19, color, track=3, al="r", sombra=sombra)


def tachar(c, x, y, s, fk, size, color, track=0):
    f = fuente(fk, size)
    w = escribir(c, x, y, s, fk, size, color, track)
    a = f.getmetrics()[0]
    ImageDraw.Draw(c).line([(x - 2, y + a * 0.62), (x + w + 2, y + a * 0.62)], fill=color + (255,), width=3)
    return w


def compo(base, cap):
    im = Image.fromarray(base).convert("RGBA")
    im.alpha_composite(cap)
    return np.asarray(im.convert("RGB"))


def guardar_png(a, p):
    Image.fromarray(a).save(p, optimize=True)


# ---------- fuentes de imagen ----------
def cuadro(src, t, w=1080, h=1920):
    L = Lector(src, t, w, h); a = L.cuadro().copy(); L.cerrar(); return a


def frames(src, t0, n, w=1080, h=1920):
    L = Lector(src, t0, w, h); out = [L.cuadro().copy() for _ in range(n)]; L.cerrar(); return out


S5325 = os.path.join(GL, "sdr_5325_full.mp4")
S5333 = os.path.join(GL, "sdr_5333.mp4")
S5359 = os.path.join(GL, "sdr_5359.mp4")
Y_PLACA = 273  # recorte 4:5 de IMG_5359 con la placa en el 62 % de la altura
Y_5325 = 150

control = {}

# ===================== PUBLICACIÓN =====================
# 01 · portada: la placa nítida en su mano (IMG_5359, 8,45 s) — «Esto no se compra.»
a = grado(cuadro(S5359, 8.45)[Y_PLACA:Y_PLACA + PH])
a = degrade(degrade(a, 0, 620, 0.5), PH - 260, PH, 0.45, arriba=False)
c = capa(PW, PH)
folio(c, 1, BLANCO, 0.5)
escribir(c, M, 170, "Esto no se", "serif", 132, BLANCO, sombra=0.45, radio=18)
escribir(c, M, 300, "compra.", "serif", 132, BLANCO, sombra=0.45, radio=18)
escribir(c, M, PH - 78, "DESLIZÁ  →", "inter_m", 19, BLANCO, track=4, sombra=0.5)
guardar_png(grano(compo(a, c), 2.5, 1), os.path.join(OUT, "publicacion", "ROCCE_IG_ESTO_NO_SE_COMPRA_01_v01.png"))


def lamina_video(nombre, fr, cap, n_lam, fade_cap=8):
    cod = Codificador(os.path.join(OUT, "publicacion", nombre), w=PW, h=PH)
    for k, f in enumerate(fr):
        b = Image.fromarray(f).convert("RGBA")
        cc = cap if k >= fade_cap else Image.fromarray((np.asarray(cap).astype(np.float32) *
                                                         np.array([1, 1, 1, suave(k / fade_cap)])).astype(np.uint8), "RGBA")
        b.alpha_composite(cc)
        cod.poner(grano(np.asarray(b.convert("RGB")), 2.5, k))
    cod.cerrar()
    control[nombre] = dict(cuadros=cod.n, segundos=round(cod.n / 30, 2))


# 02 · video: recorrido macro por la espalda (IMG_5325, 10,0–13,3 s) — «Viene con cada remera Founders Privée.»
fr = [degrade(grado(f[Y_5325:Y_5325 + PH]), PH - 640, PH, 0.7, arriba=False) for f in frames(S5325, 10.0, 99)]
c = capa(PW, PH)
folio(c, 2, BLANCO, 0.5)
escribir(c, M, PH - 330, "FIG. 01 — ESPALDA", "inter_m", 19, BLANCO, track=4, sombra=0.5)
escribir(c, M, PH - 290, "Viene con cada remera", "serif", 76, BLANCO, sombra=0.45)
escribir(c, M, PH - 206, "Founders Privée.", "serif_i", 76, BLANCO, sombra=0.45)
lamina_video("ROCCE_IG_ESTO_NO_SE_COMPRA_02_v01.mp4", fr, c, 2)

# 03 · papel: el frente «so f★cking close.» (PRODUCTO/blanca_frente_detalle_estampado.jpg)
a = np.full((PH, PW, 3), PAPEL, np.uint8)
foto = srgb(os.path.join(RAIZ, "PRODUCTO/blanca_frente_detalle_estampado.jpg"))
bw, bh = PW - 2 * M, 860
ins = grado(np.asarray(fill_cover(foto, bw, bh, cx=0.5, cy=0.42, zoom=1.0)))
a[132:132 + bh, M:M + bw] = ins
c = capa(PW, PH)
folio(c, 3, TINTA)
escribir(c, M, 1030, "FIG. 02 — FRENTE", "inter_m", 19, TINTA, track=4)
escribir(c, M, 1068, "Adelante, lo que pasa", "serif", 70, TINTA)
escribir(c, M, 1146, "casi siempre.", "serif_i", 70, TINTA)
guardar_png(grano(compo(a, c), 1.2, 3), os.path.join(OUT, "publicacion", "ROCCE_IG_ESTO_NO_SE_COMPRA_03_v01.png"))

# 04 · espalda puesta mirando el mar (PRODUCTO/blanca_puesta_espalda_balcon_playa.jpg)
foto = srgb(os.path.join(RAIZ, "PRODUCTO/blanca_puesta_espalda_balcon_playa.jpg"))
a = grado(np.asarray(fill_cover(foto, PW, PH, cx=0.5, cy=0.56)))
a = degrade(a, PH - 560, PH, 0.6, arriba=False)
a = degrade(a, 0, 220, 0.35)
c = capa(PW, PH)
folio(c, 4, BLANCO, 0.5)
escribir(c, M, PH - 330, "FIG. 03 — ESPALDA", "inter_m", 19, BLANCO, track=4, sombra=0.5)
escribir(c, M, PH - 290, "Atrás, los que estuvieron", "serif", 76, BLANCO, sombra=0.45)
escribir(c, M, PH - 206, "desde el principio.", "serif_i", 76, BLANCO, sombra=0.45)
guardar_png(grano(compo(a, c), 2.5, 4), os.path.join(OUT, "publicacion", "ROCCE_IG_ESTO_NO_SE_COMPRA_04_v01.png"))

# 05 · video: la placa entra en foco (IMG_5359, 5,6–8,7 s) — «Y una placa que significa una sola cosa:»
fr = [degrade(degrade(grado(f[Y_PLACA:Y_PLACA + PH]), 0, 640, 0.5), PH - 260, PH, 0.45, arriba=False)
      for f in frames(S5359, 5.6, 93)]
c = capa(PW, PH)
folio(c, 5, BLANCO, 0.5)
escribir(c, M, 150, "FIG. 04 — LA PLACA", "inter_m", 19, BLANCO, track=4, sombra=0.5)
escribir(c, M, 190, "Y una placa que significa", "serif", 76, BLANCO, sombra=0.45)
escribir(c, M, 274, "una sola cosa:", "serif_i", 76, BLANCO, sombra=0.45)
lamina_video("ROCCE_IG_ESTO_NO_SE_COMPRA_05_v01.mp4", fr, c, 5)

# 06 · papel: la resolución
a = np.full((PH, PW, 3), PAPEL, np.uint8)
c = capa(PW, PH)
folio(c, 6, TINTA)
ImageDraw.Draw(c).line([(PW / 2 - 30, 452), (PW / 2 + 30, 452)], fill=TINTA + (255,), width=2)
escribir(c, PW / 2, 482, "SIGNIFICA", "inter_m", 20, TINTA, track=8, al="c")
escribir(c, PW / 2, 540, "Seguir hasta", "serif", 150, TINTA, al="c")
escribir(c, PW / 2, 690, "lograrlo.", "serif_i", 150, TINTA, al="c")
escribir(c, PW / 2, 900, "Eso no se compra. Se cumple.", "serif", 52, TINTA, al="c")
guardar_png(grano(compo(a, c), 1.2, 5), os.path.join(OUT, "publicacion", "ROCCE_IG_ESTO_NO_SE_COMPRA_06_v01.png"))

# 07 · papel: CTA con la foto real de la placa sobre las dos remeras (primer cuadro de IMG_5361)
a = np.full((PH, PW, 3), PAPEL, np.uint8)
foto = Image.open(os.path.join(GL, "f5361_0.png")).convert("RGB")
bw, bh = PW - 2 * M, 600
ins = grado(np.asarray(fill_cover(foto, bw, bh, cx=0.5, cy=0.645, zoom=1.0)))
a[124:124 + bh, M:M + bw] = ins
c = capa(PW, PH)
folio(c, 7, TINTA, abajo=False)
escribir(c, M, 768, "BLACK FRIDAY", "inter_sb", 22, TINTA, track=8)
escribir(c, M, 800, "−25 %", "serif", 168, TINTA)
x = M + 6
w = escribir(c, x, 990, "$48.750", "serif", 76, TINTA)
tachar(c, x + w + 26, 1018, "antes $65.000", "inter_m", 28, (120, 120, 120))
escribir(c, M, 1092, "REMERA FOUNDERS PRIVÉE + PLACA  ·  ENVÍO GRATIS", "inter_m", 19, TINTA, track=4)
escribir(c, M, 1130, "rocce.shop", "serif_i", 52, TINTA)
escribir(c, M, PH - 78, "GIVE HISTORY YOUR NAME.", "inter_sb", 19, TINTA, track=6)
lg = 190  # logo original sobre el papel #FEFEFE (su mismo fondo); el dibujo ocupa ~71 % del cuadro
logo = np.asarray(Image.open(os.path.join(RAIZ, "LOGO/rocce_logo.png")).convert("RGB").resize((lg, lg), Image.LANCZOS))
y1, x1 = PH - 22, PW - M + 27
a[y1 - lg:y1, x1 - lg:x1] = logo
guardar_png(grano(compo(a, c), 1.2, 6), os.path.join(OUT, "publicacion", "ROCCE_IG_ESTO_NO_SE_COMPRA_07_v01.png"))

# ===================== HISTORIAS =====================
GUIA = {}


def historia(nombre, fr, capas, zonas):
    """capas: lista de (desde_cuadro, capa RGBA, fundido en cuadros)."""
    cod = Codificador(os.path.join(OUT, "historias", nombre + ".mp4"), w=SW, h=SH)
    primero = None
    for k, f in enumerate(fr):
        b = Image.fromarray(f).convert("RGBA")
        for k0, cp, fd in capas:
            if k >= k0:
                al = suave((k - k0) / fd) if fd else 1.0
                if al < 1:
                    cp2 = np.asarray(cp).astype(np.float32); cp2[..., 3] *= al
                    b.alpha_composite(Image.fromarray(cp2.astype(np.uint8), "RGBA"))
                else:
                    b.alpha_composite(cp)
        a = grano(np.asarray(b.convert("RGB")), 2.5, k)
        cod.poner(a)
        if k == len(fr) - 1:
            primero = a
    cod.cerrar()
    control[nombre] = dict(cuadros=cod.n, segundos=round(cod.n / 30, 2))
    guardar_png(primero, os.path.join(OUT, "historias", nombre + "_cuadro_final.png"))
    # guía: último cuadro con las zonas de los stickers marcadas
    g = Image.fromarray(primero).convert("RGBA"); d = ImageDraw.Draw(g)
    for (x0, y0, x1, y1), txt in zonas:
        for xx in range(int(x0), int(x1), 28):
            d.line([(xx, y0), (min(xx + 14, x1), y0)], fill=(255, 230, 0, 255), width=4)
            d.line([(xx, y1), (min(xx + 14, x1), y1)], fill=(255, 230, 0, 255), width=4)
        for yy in range(int(y0), int(y1), 28):
            d.line([(x0, yy), (x0, min(yy + 14, y1))], fill=(255, 230, 0, 255), width=4)
            d.line([(x1, yy), (x1, min(yy + 14, y1))], fill=(255, 230, 0, 255), width=4)
        escribir(g, (x0 + x1) / 2, (y0 + y1) / 2 - 18, txt, "inter_sb", 30, (255, 230, 0), al="c", sombra=0.8)
    for y in (220, SH - 300):  # bordes de la zona segura (perfil arriba, respuesta abajo)
        d.line([(0, y), (SW, y)], fill=(255, 80, 80, 200), width=2)
    g.convert("RGB").save(os.path.join(OUT, "guia", nombre + "_GUIA.jpg"), quality=88)
    GUIA[nombre] = [dict(zona=z, sticker=t) for z, t in zonas]


def arriba(fr, g=0.55, hasta=820):
    return [degrade(grado(f), 0, hasta, g) for f in fr]


# H1 · encuesta: ¿Blanca o negra? (IMG_5333 ida y vuelta: espalda blanca → negra → blanca)
f = frames(S5333, 0.0, 92)
fr = arriba(f + f[::-1][1:])
c = capa(SW, SH)
escribir(c, SW / 2, 262, "FOUNDERS PRIVÉE", "inter_sb", 24, BLANCO, track=8, al="c", sombra=0.5)
escribir(c, SW / 2, 304, "¿Blanca", "serif", 150, BLANCO, al="c", sombra=0.45, radio=18)
escribir(c, SW / 2, 452, "o negra?", "serif_i", 150, BLANCO, al="c", sombra=0.45, radio=18)
historia("ROCCE_IG_HISTORIA_1_ENCUESTA_v01", fr, [(0, c, 0)],
         [((140, 640, 940, 820), "ENCUESTA: «BLANCA» / «NEGRA»")])

# H2 · quiz: ¿Qué significa esta placa? (IMG_5359 desenfocada, 2,5–6,5 s)
fr = arriba(frames(S5359, 2.5, 120), 0.5, 760)
c = capa(SW, SH)
escribir(c, SW / 2, 262, "ADIVINÁ ANTES DE PASAR", "inter_sb", 24, BLANCO, track=8, al="c", sombra=0.5)
escribir(c, SW / 2, 304, "¿Qué significa", "serif", 132, BLANCO, al="c", sombra=0.45, radio=18)
escribir(c, SW / 2, 436, "esta placa?", "serif_i", 132, BLANCO, al="c", sombra=0.45, radio=18)
historia("ROCCE_IG_HISTORIA_2_QUIZ_v01", fr, [(0, c, 0)],
         [((120, 1240, 960, 1620), "QUIZ: 3 OPCIONES (VER LEEME)")])

# H3 · revelación: el foco llega (IMG_5359, 6,0–8,6 s) y se queda en la placa nítida; pregunta + link
f = frames(S5359, 6.0, 78)
nit = cuadro(S5359, 8.45)
f += [np.asarray(fill_cover(Image.fromarray(nit), SW, SH, cy=0.58, zoom=1.0 + 0.035 * suave(k / 84))) for k in range(84)]
fr = [degrade(degrade(grado(x), 0, 760, 0.55), SH - 560, SH, 0.6, arriba=False) for x in f]
c1 = capa(SW, SH)
escribir(c1, SW / 2, 262, "SIGNIFICA", "inter_sb", 24, BLANCO, track=8, al="c", sombra=0.5)
escribir(c1, SW / 2, 304, "Seguir hasta", "serif", 140, BLANCO, al="c", sombra=0.45, radio=18)
escribir(c1, SW / 2, 444, "lograrlo.", "serif_i", 140, BLANCO, al="c", sombra=0.45, radio=18)
c2 = capa(SW, SH)
escribir(c2, SW / 2, 1392, "VIENE CON CADA REMERA FOUNDERS PRIVÉE", "inter_sb", 22, BLANCO, track=6, al="c", sombra=0.5)
escribir(c2, SW / 2, 1432, "Black Friday · −25 % · $48.750", "serif", 62, BLANCO, al="c", sombra=0.45)
k_foco = int((7.2 - 6.0) * 30)
historia("ROCCE_IG_HISTORIA_3_REVELACION_v01", fr, [(k_foco, c1, 8), (k_foco + 12, c2, 8)],
         [((170, 600, 910, 800), "PREGUNTA: «¿QUÉ ESTÁS PERSIGUIENDO VOS?»"), ((290, 1520, 790, 1610), "LINK: rocce.shop")])

json.dump(dict(control=control, guia=GUIA), open(os.path.join(OUT, "guia", "control.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(control, indent=1))
