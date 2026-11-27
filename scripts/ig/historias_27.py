# 3 historias de IG para comunidad (27/11/2026, último día del Black Friday, termina 23:59 ART):
# H1 encuesta «¿Messi lo da vuelta?» (juega hoy 22:00 el juego 2 contra Columbus; si pierde, queda afuera) sobre su primer
#    plano real (clip oficial de Inter Miami CF, sin audio, sin prenda ni logo: el famoso nunca va junto al producto);
# H2 pregunta «¿Cuál es tu segundo intento?» sobre la espalda real de la remera (IMG_5325);
# H3 revelación «Termina hoy.» sobre la placa real junto a las remeras (IMG_5361) + datos verificados del BF + zona de link.
# Mismo sistema visual que las historias del 26/11 (Instrument Serif + Inter espaciada, grado «lujo silencioso»).
# Uso: python3 scripts/ig/historias_27.py SALIDA_DIR
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fomo"))
from comun import Lector, Codificador, fuente, suave, fill_cover, grano, RAIZ

OUT = sys.argv[1]
for d in ("historias", "guia"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
SW, SH = 1080, 1920
BLANCO = (255, 255, 255)
CEL = (170, 208, 240)
V = "v01"
MESSI = os.path.join(RAIZ, "TRABAJO/jornada2/messi/tt_7710039332676996365.mp4")   # @intermiamicf, primer plano 5,8–9,7 s
S5325 = os.path.join(RAIZ, "TRABAJO/fomo/gl/sdr_5325_full.mp4")
S5361 = os.path.join(RAIZ, "TRABAJO/feed/sdr_5361.mp4")


def grado(a):
    x = a.astype(np.float32) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b)[..., None]
    celeste = np.clip((b - np.maximum(r, g)) * 8, 0, 1)[..., None]
    x = lum + (x - lum) * (0.86 + 0.14 * celeste)
    x = 0.022 + 0.958 * np.power(np.clip(x, 0, 1), 1.04)
    x = np.where(x > 0.84, 0.84 + (x - 0.84) * 0.72, x)
    return np.clip(x * 255, 0, 255).astype(np.uint8)


def degrade(a, y0, y1, g, arriba=True):
    yy = np.arange(a.shape[0], dtype=np.float32)
    t = np.clip((yy - y0) / max(1.0, y1 - y0), 0, 1)
    t = t * t * (3 - 2 * t)
    m = (1 - t) if arriba else t
    return (a.astype(np.float32) * (1 - g * m)[:, None, None]).astype(np.uint8)


def capa():
    return Image.new("RGBA", (SW, SH), (0, 0, 0, 0))


def escribir(img, x, y, s, fk, size, color, track=0, al="c", sombra=0.0, radio=14):
    f = fuente(fk, size)
    w = sum(f.getlength(c) for c in s) + track * (len(s) - 1) if track else f.getlength(s)
    x0 = x - w / 2 if al == "c" else (x - w if al == "r" else x)

    def txt(d, x, fill):
        if not track:
            d.text((x, y if fill != 255 else y + 3), s, font=f, fill=fill); return
        for ch in s:
            d.text((x, y if fill != 255 else y + 3), ch, font=f, fill=fill); x += f.getlength(ch) + track
    if sombra:
        sm = Image.new("L", img.size, 0); txt(ImageDraw.Draw(sm), x0, 255)
        sm = sm.filter(ImageFilter.GaussianBlur(radio))
        sh = capa(); sh.putalpha(sm.point(lambda v: int(v * sombra))); img.alpha_composite(sh)
    txt(ImageDraw.Draw(img), x0, color + (255,))
    return w


def frames(src, t0, n):
    L = Lector(src, t0, SW, SH); out = [L.cuadro().copy() for _ in range(n)]; L.cerrar(); return out


control, GUIA = {}, {}


def historia(nombre, fr, capas, zonas):
    """capas: (desde_cuadro, capa RGBA, fundido en cuadros). Guarda MP4, último cuadro y guía con zonas de stickers."""
    cod = Codificador(os.path.join(OUT, "historias", nombre + ".mp4"), w=SW, h=SH)
    ult = None
    for k, f in enumerate(fr):
        b = Image.fromarray(f).convert("RGBA")
        for k0, cp, fd in capas:
            if k >= k0:
                al = suave((k - k0) / fd) if fd else 1.0
                if al < 1:
                    c2 = np.asarray(cp).astype(np.float32); c2[..., 3] *= al
                    b.alpha_composite(Image.fromarray(c2.astype(np.uint8), "RGBA"))
                else:
                    b.alpha_composite(cp)
        ult = grano(np.asarray(b.convert("RGB")), 2.5, k)
        cod.poner(ult)
    cod.cerrar()
    control[nombre] = dict(cuadros=cod.n, segundos=round(cod.n / 30, 2))
    Image.fromarray(ult).save(os.path.join(OUT, "historias", nombre + "_cuadro_final.png"), optimize=True)
    g = Image.fromarray(ult).convert("RGBA"); d = ImageDraw.Draw(g)
    for (x0, y0, x1, y1), t in zonas:
        for xx in range(int(x0), int(x1), 28):
            d.line([(xx, y0), (min(xx + 14, x1), y0)], fill=(255, 230, 0, 255), width=4)
            d.line([(xx, y1), (min(xx + 14, x1), y1)], fill=(255, 230, 0, 255), width=4)
        for yy in range(int(y0), int(y1), 28):
            d.line([(x0, yy), (x0, min(yy + 14, y1))], fill=(255, 230, 0, 255), width=4)
            d.line([(x1, yy), (x1, min(yy + 14, y1))], fill=(255, 230, 0, 255), width=4)
        escribir(g, (x0 + x1) / 2, (y0 + y1) / 2 - 18, t, "inter_sb", 28, (255, 230, 0), sombra=0.8)
    for y in (220, SH - 300):  # zona segura: perfil arriba, respuesta abajo
        d.line([(0, y), (SW, y)], fill=(255, 80, 80, 200), width=2)
    g.convert("RGB").save(os.path.join(OUT, "guia", nombre + "_GUIA.jpg"), quality=88)
    GUIA[nombre] = [dict(zona=z, sticker=t) for z, t in zonas]


# H1 · encuesta: su primer plano (plano único 5,47–7,87 s; se usa 5,5–7,5) bajado 200 px para que el título no le tape la cara; arriba, el verde
# desenfocado del fondo se completa con el color medio de las primeras filas.
BAJA = 200
fr = []
for a in frames(MESSI, 5.5, 60):
    n = np.empty_like(a)
    n[BAJA:] = a[:SH - BAJA]
    tope = a[:40].astype(np.float32).mean(axis=0)
    n[:BAJA] = np.asarray(Image.fromarray(np.repeat(tope[None], BAJA, 0).astype(np.uint8)).filter(ImageFilter.GaussianBlur(30)))
    fr.append(degrade(grado(n), 0, 760, 0.5))
fr = fr + fr[::-1][1:]                         # ida y vuelta dentro del mismo plano: 4 s sin salto
c = capa()
escribir(c, SW / 2, 250, "MESSI · HOY 22:00 · JUEGO 2", "inter_sb", 26, BLANCO, track=8, sombra=0.6)
escribir(c, SW / 2, 290, "¿Lo da vuelta?", "serif", 132, BLANCO, sombra=0.5, radio=18)
escribir(c, SW / 2, 448, "Perdió 3-0 el primero.", "inter_m", 36, BLANCO, sombra=0.7)
escribir(c, SW / 2, 494, "Si pierde hoy, queda afuera.", "inter_m", 36, CEL, sombra=0.7)
escribir(c, 64, SH - 330, "Video: Inter Miami CF", "inter_m", 24, (225, 225, 225), al="l", sombra=0.8)
historia(f"ROCCE_IG_27_HISTORIA_1_ENCUESTA_{V}", fr, [(0, c, 0)],
         [((150, 1390, 930, 1600), "ENCUESTA: «SÍ, LO DA VUELTA» / «NO, SE VA»")])

# H2 · pregunta: la espalda real de la remera (IMG_5325, cámara en mano 0,5–4,5 s)
def bajar(a, baja):
    """corre el cuadro hacia abajo y completa arriba con el color medio de las primeras filas, desenfocado."""
    n = np.empty_like(a); n[baja:] = a[:SH - baja]
    tope = a[:40].astype(np.float32).mean(axis=0)
    n[:baja] = np.asarray(Image.fromarray(np.repeat(tope[None], baja, 0).astype(np.uint8)).filter(ImageFilter.GaussianBlur(30)))
    return n


fr = [degrade(grado(bajar(a, 160)), 0, 900, 0.6) for a in frames(S5325, 0.5, 120)]   # el título no pisa la remera
c = capa()
escribir(c, SW / 2, 250, "TODOS ERRAMOS EL PRIMERO", "inter_sb", 26, BLANCO, track=8, sombra=0.6)
escribir(c, SW / 2, 296, "¿Cuál es tu", "serif", 138, BLANCO, sombra=0.5, radio=18)
escribir(c, SW / 2, 432, "segundo intento?", "serif_i", 120, BLANCO, sombra=0.5, radio=18)
historia(f"ROCCE_IG_27_HISTORIA_2_PREGUNTA_{V}", fr, [(0, c, 0)],
         [((150, 1410, 930, 1610), "PREGUNTA: «¿QUÉ ESTÁS INTENTANDO DE NUEVO?»")])

# H3 · revelación: el recorrido llega a la placa (IMG_5361, 2,9 s) y se queda con un zoom lento; datos verificados del BF
f = frames(S5361, 0.0, 87)
ult = Image.fromarray(f[-1])
f += [np.asarray(fill_cover(ult, SW, SH, cy=0.7, zoom=1.0 + 0.04 * suave(k / 90))) for k in range(90)]
fr = [degrade(grado(x), 0, 960, 0.62) for x in f]
c1 = capa()
escribir(c1, SW / 2, 250, "ÚLTIMO DÍA · HASTA LAS 23:59", "inter_sb", 26, BLANCO, track=8, sombra=0.6)
escribir(c1, SW / 2, 296, "Termina", "serif", 138, BLANCO, sombra=0.5, radio=18)
escribir(c1, SW / 2, 432, "hoy.", "serif_i", 138, BLANCO, sombra=0.5, radio=18)
c2 = capa()
escribir(c2, SW / 2, 606, "Black Friday · −25 %", "serif", 64, BLANCO, sombra=0.6)
escribir(c2, SW / 2, 690, "$48.750 · antes $65.000", "inter_sb", 38, BLANCO, sombra=0.7)
escribir(c2, SW / 2, 740, "Envío gratis · placa incluida", "inter_m", 34, BLANCO, sombra=0.7)
historia(f"ROCCE_IG_27_HISTORIA_3_REVELACION_{V}", fr, [(0, c1, 0), (45, c2, 8)],
         [((290, 810, 790, 900), "LINK: rocce.shop")])

json.dump(dict(control=control, guia=GUIA), open(os.path.join(OUT, "guia", "control.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(control))
