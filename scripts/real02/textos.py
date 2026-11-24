#!/usr/bin/env python3
"""REAL-02 v01 · capas de texto del guion G1 (§5): grafía exacta, Inter Display ExtraBold/Bold, relleno blanco,
contorno negro (T1–T6), sombra negra 45 % (0,4) desenfoque 10 px, entrada «pop» 112 → 106 → 100 % en 3 cuadros.
La posición (x0, y0) es la esquina de la caja de tinta CON contorno; 'c' = centrado horizontal en 540."""
import os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

XB = '/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf'
BD = '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
POP = (1.12, 1.06, 1.00)
# id, líneas, fuente, tamaño, contorno, interlineado, x0, y0, desde, hasta (inclusive), pop
TEXTOS = [
    ('T1', ['¿Cuál se la lleva?'], XB, 104, 9, None, 'c', 126, 0, 45, True),
    ('T2', ['1'], XB, 240, 10, None, 50, 836, 0, 45, True),   # tamaño de respaldo del guion (280 px quedaba a 6,7 px de la remera en f38)
    ('T3', ['2'], XB, 280, 10, None, 50, 593, 46, 62, True),
    ('T4', ['3'], XB, 280, 10, None, 836, 519, 63, 73, True),
    ('T5', ['Ninguna.'], XB, 120, 10, None, 'c', 143, 74, 93, False),
    ('T6', ['Llevátela vos.'], XB, 116, 10, None, 'c', 122, 184, 228, True),
    ('T7', ['Incluye la placa Founders Privée', 'y tu número, del 001 al 100.'], BD, 46, 0, 60, 'c', 80, 229, 306, False),
    ('T8', ['rocce.shop'], XB, 116, 0, None, 'c', 246, 244, 306, True),
]
# v1.1 (dictamen de Roma 08): REAL02_VER=v1_1. Sin la variable, todo queda como v1.
VER = os.environ.get('REAL02_VER', 'v1')
if VER == 'v1_1':
    TEXTOS = [t for t in TEXTOS if t[0] not in ('T4', 'T6', 'T7', 'T8')] + [
        ('T4', ['3'], XB, 240, 10, None, 860, 770, 63, 73, True),        # cambio 1: sobre la roca, igual al «1»
        ('T6', ['Llevátela vos.'], XB, 116, 10, None, 'c', 122, 184, 258, True),   # P6 llega a f258
        ('T8', ['rocce.shop'], XB, 116, 10, None, 'c', 255, 229, 306, True),       # mismo estilo que T6, pop en f229
        ('T7', ['Con placa y número', 'del 001 al 100.'], BD, 72, 0, 86, 'c', 91, 259, 306, False),  # P7, arriba de la foto
    ]
    TEXTOS.sort(key=lambda t: int(t[0][1:]))
PAD = 48


@lru_cache(maxsize=None)
def parche(tid):
    """RGBA del texto a escala 1 (con sombra) y caja de tinta con contorno dentro del parche."""
    t = next(x for x in TEXTOS if x[0] == tid)
    _, lineas, fuente, tam, sw, inter, *_ = t
    f = ImageFont.truetype(fuente, tam)
    cajas = [f.getbbox(l, stroke_width=sw) for l in lineas]
    anchos = [c[2] - c[0] for c in cajas]
    paso = inter if inter else 0
    alto_total = (cajas[0][3] - cajas[0][1]) + paso * (len(lineas) - 1) if len(lineas) > 1 else cajas[0][3] - cajas[0][1]
    if len(lineas) > 1:
        alto_total = paso * (len(lineas) - 1) + max(c[3] for c in cajas) - min(c[1] for c in cajas)
    W = max(anchos) + 2 * PAD; H = alto_total + 2 * PAD
    tinta = Image.new('L', (W, H), 0); relleno = Image.new('L', (W, H), 0)
    dt, dr = ImageDraw.Draw(tinta), ImageDraw.Draw(relleno)
    top = min(c[1] for c in cajas)
    for k, (l, c) in enumerate(zip(lineas, cajas)):
        x = PAD + (max(anchos) - (c[2] - c[0])) / 2 - c[0]
        y = PAD - top + k * paso
        dt.text((x, y), l, font=f, fill=255, stroke_width=sw, stroke_fill=255)
        dr.text((x, y), l, font=f, fill=255)
    a_t = np.asarray(tinta, np.float32) / 255; a_r = np.asarray(relleno, np.float32) / 255
    sombra = Image.fromarray((a_t * 255 * 0.45).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10))
    s = np.zeros_like(a_t); s[4:] = (np.asarray(sombra, np.float32) / 255)[:-4]
    alfa = np.clip(a_t + s * (1 - a_t), 0, 1)                    # sombra debajo de la tinta
    blanco = np.where(alfa > 0, a_r / np.maximum(alfa, 1e-6), 0)  # fracción blanca dentro de la capa
    rgb = np.repeat((np.clip(blanco, 0, 1) * 255)[..., None], 3, -1)
    rgba = np.dstack([rgb, alfa * 255]).astype(np.uint8)
    nz = np.nonzero(a_t > 0.02); caja = (nz[1].min(), nz[0].min(), nz[1].max() + 1, nz[0].max() + 1)
    return Image.fromarray(rgba, 'RGBA'), Image.fromarray((a_t * 255).astype(np.uint8)), caja


def capas(f):
    """[(id, rgba, tinta(L), x, y)] para el cuadro f del máster (pop incluido)."""
    out = []
    for t in TEXTOS:
        tid, *_, x0, y0, d, h, pop = t
        if not (d <= f <= h):
            continue
        im, tinta, (cx0, cy0, cx1, cy1) = parche(tid)
        cw = cx1 - cx0
        X = (540 - cw / 2) if x0 == 'c' else x0
        ox, oy = X - cx0, y0 - cy0                     # origen del parche a escala 1
        k = f - d; s = POP[k] if (pop and k < 3) else 1.0
        if s != 1.0:
            w, hh = round(im.width * s), round(im.height * s)
            ccx, ccy = ox + (cx0 + cx1) / 2, oy + (cy0 + cy1) / 2   # escala alrededor del centro de la caja
            im = im.resize((w, hh), Image.LANCZOS); tinta = tinta.resize((w, hh), Image.LANCZOS)
            ox = ccx - (cx0 + cx1) / 2 * s; oy = ccy - (cy0 + cy1) / 2 * s
        out.append((tid, im, tinta, int(round(ox)), int(round(oy))))
    return out


def caja_tinta(tid):
    """caja de tinta (con contorno) en coordenadas del máster a escala 1."""
    t = next(x for x in TEXTOS if x[0] == tid); _, tinta, (cx0, cy0, cx1, cy1) = parche(tid)
    x0, y0 = t[6], t[7]; X = round(540 - (cx1 - cx0) / 2) if x0 == 'c' else x0
    return (X, y0, X + cx1 - cx0, y0 + cy1 - cy0)


if __name__ == '__main__':
    for t in TEXTOS:
        print(t[0], repr(' / '.join(t[1])), 'caja', caja_tinta(t[0]), f'f{t[8]}-f{t[9]}')
