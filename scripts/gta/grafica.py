#!/usr/bin/env python3
"""GTA6 «La misión» · sistema gráfico (Pedro, 19/11/2026). Capa RGBA por cuadro, 1080×1920, 30 fps, D = 16,00.

Textos EXACTOS de 01_fede_guion_G1.md §4 con las correcciones de 02_roma_aprobacion_G1.md:
  - «antes de que caiga el sol» y los detalles «te faltó…» a 62 px (corrección 1);
  - hook: logo y «ZONA NUEVA» en c0, caja de misión en 0,40, «NADIE LA TERMINA» en 0,50; si a 360 px se pegan,
    «ZONA NUEVA» sale en 0,50 y «NADIE LA TERMINA» toma su lugar (corrección 2: se mide en `layout_hook`);
  - logo: evocación propia («VI» con degradé de atardecer rosa→naranja→violeta + «GRAND THEFT AUTO» en Saira
    condensada), solo 0,00–1,50; nada de Pricedown ni archivos de Rockstar (corrección 3).
Convención: `y` = borde superior de la tinta del texto (sin contorno ni caja), centrado en x 540 salvo indicación.
Zonas prohibidas (guion §4): nada en x 940–1060 · y 1150–1700, nada debajo de y 1560 (`control_zonas`).

Uso:
    from grafica import Grafica
    g = Grafica('A')            # o 'B'
    capa = g.capa(n)            # Lienzo; capa.p = RGBA premultiplicado float32 (1920, 1080, 4)
    python grafica.py control   # zonas, textos, separaciones del hook → TRABAJO/gta/grafica_control.json
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, '/home/user/1/scripts/gta')
from comun import (W, H, FPS, D, ND, CELESTE, BLANCO, NEGRO, CAJA_A, CAJA_R, saira, inter, Sprite, Lienzo,  # noqa
                   texto_sprite, caja_sprite, clamp, ease_out, ease_in_out, lerp, T, guardar_json)
import math as _m


def c(t):
    """segundo → cuadro, redondeo hacia arriba en .5 (13,55 → 407), sin el redondeo bancario de Python."""
    return int(_m.floor(t * FPS + 0.5 + 1e-9))


# ============================================================================== textos exactos (guion §4)
TXT = {
    'zona': 'ZONA NUEVA', 'nadie': 'NADIE LA TERMINA',                 # hook A
    'pero': 'PERO SIEMPRE', 'falta': 'TE FALTA 1 CM',                  # hook B
    'mision': 'MISIÓN', 'oculto': 'so f★cking close.',                 # bloques = distribución de «so f★cking close.»
    'gana': 'GANÁ UNA', 'sol': 'antes de que caiga el sol',
    'casi': 'CASI.', 'cm': 'te faltó 1 cm', 'mm': 'te faltó 1 mm', 'una': 'te faltó una', 'nada': 'te faltó nada',
    'rep': '19/20', 'inspirado': 'INSPIRADO EN EL DROP', 'frase': 'so f★cking close.',
    'logo_sup': ('GRAND', 'THEFT', 'AUTO'), 'logo_vi': 'VI',
}
CONTADOR = ('0,80 m', '0,01 m')

# ============================================================================== tiempos (máster, s)
TM = dict(
    logo=(0.00, 1.50), hook1=(0.00, 1.50), hook2=(0.50, 1.80), caja_in=0.40,
    achica=(1.50, 1.80), descifra=(13.20, 13.55), viaja=(13.55, 13.75), fin_textos=15.70, fundido_c=3,
    carga=(0.00, 1.50), carga_llena=1.40,
    mini=(1.50, 15.00), anillo=(1.50, 13.20),
    gana=(1.90, 3.70),
    casi=[(5.70, 6.30, 'cm', 640), (7.70, 8.30, 'mm', 640), (9.40, 10.00, 'una', 1150), (12.00, 12.60, 'nada', 640)],
    rep=(8.30, 10.00), contador=(10.10, 11.70), contador_llega=11.45,
)
# posiciones (guion §3; y = borde superior de la tinta)
Y = dict(logo=(150, 310), hook1=340, hook2=540, caja=460, esquina=(60, 170), esquina_escala=0.75,
         gana=300, sol=400, casi_det=180, rep=300, contador=640, frase=520, inspirado=414,
         mini=(60, 1215, 290, 1445), carga=(540, 1430))
SEPARACION_MIN = 30          # px a 1080 (10 px a 360) entre cajas de tinta+contorno/caja de los elementos del hook

# degradé de FMT-03 detrás de textos sobre cielo: alfa 0,38 hasta y_plano, coseno a 0 en y_cero (por tramo)
DEGRADE = [  # (t0, t1, y_plano, y_cero)
    (0.00, 1.80, 380, 700),       # hook (logo + hooks + caja)
    (1.90, 3.70, 330, 640),       # GANÁ UNA / antes de que caiga el sol
    (8.30, 10.00, 250, 560),      # 19/20
    (13.20, 15.70, 470, 800),     # INSPIRADO EN EL DROP / so f★cking close.
]
DEG_ALFA = 0.38
DEG_FUNDIDO_C = 3


def perfil(alfa, y_plano, y_cero):
    y = np.arange(H, dtype=np.float32); a = np.zeros(H, np.float32)
    a[y <= y_plano] = alfa
    m = (y > y_plano) & (y < y_cero)
    a[m] = alfa * 0.5 * (1 + np.cos(np.pi * (y[m] - y_plano) / (y_cero - y_plano)))
    return a


# ============================================================================== piezas
def sp_hook(txt, px):
    """Hook84/76: Inter Display ExtraBold mayúsculas, blanco con contorno negro 6 px."""
    return texto_sprite([(txt, inter(px), BLANCO)], stroke=6, stroke_fill=NEGRO)


def sp_logo():
    """evocación del logo de GTA VI (dibujo propio): «VI» con degradé rosa→naranja→violeta y «GRAND / THEFT / AUTO» en
    Saira condensada (wdth 62, wght 800) blanca. Alto total = 160 px (y 150–310)."""
    alto = Y['logo'][1] - Y['logo'][0]
    f_vi = saira(int(alto / 0.70), 900, 78)                     # altura de mayúscula de Saira ≈ 0,70 del cuerpo
    bb = f_vi.getbbox('VI', anchor='ls')
    cap = -bb[1]; f_vi = saira(int(round(f_vi.size * alto / cap)), 900, 78); bb = f_vi.getbbox('VI', anchor='ls')
    vw, vh = bb[2] - bb[0], -bb[1]
    # texto de arriba: tres renglones apilados que ocupan la altura del VI
    gap = 12
    hl = (alto - 2 * gap) / 3
    f_s = saira(int(hl / 0.70), 800, 62); b2 = f_s.getbbox('GRAND', anchor='ls'); f_s = saira(int(round(f_s.size * hl / -b2[1])), 800, 62)
    sup = TXT['logo_sup']
    sw = max(f_s.getlength(s) for s in sup)
    sep = 18
    PAD = 24
    tw = int(sw + sep + vw + 2 * PAD); th = int(alto + 2 * PAD)
    ss = 3   # supermuestreo
    im = Image.new('L', (tw * ss, th * ss), 0); m_vi = Image.new('L', (tw * ss, th * ss), 0)
    d = ImageDraw.Draw(im); dv = ImageDraw.Draw(m_vi)
    from PIL import ImageFont
    fs3 = ImageFont.truetype(f_s.path, f_s.size * ss); fs3.set_variation_by_axes([800, 62])
    fv3 = ImageFont.truetype(f_vi.path, f_vi.size * ss); fv3.set_variation_by_axes([900, 78])
    for k, s in enumerate(sup):          # alineado a la derecha, pegado al VI
        yb = (PAD + hl * (k + 1) + gap * k) * ss
        d.text(((PAD + sw - f_s.getlength(s)) * ss, yb), s, font=fs3, fill=255, anchor='ls')
    xv = (PAD + sw + sep - bb[0]) * ss
    dv.text((xv, (PAD + alto) * ss), 'VI', font=fv3, fill=255, anchor='ls')
    im = im.resize((tw, th), Image.LANCZOS); m_vi = m_vi.resize((tw, th), Image.LANCZOS)
    a_s = np.asarray(im, np.float32) / 255; a_v = np.asarray(m_vi, np.float32) / 255
    # degradé vertical del VI: rosa (arriba) → naranja (medio) → violeta (abajo)
    ROSA, NARANJA, VIOLETA = np.array([255, 79, 163]), np.array([255, 146, 64]), np.array([118, 60, 232])
    u = np.clip((np.arange(th) - PAD) / alto, 0, 1)[:, None, None]
    g = np.where(u < 0.5, ROSA + (NARANJA - ROSA) * (u / 0.5), NARANJA + (VIOLETA - NARANJA) * ((u - 0.5) / 0.5)) / 255
    g = np.broadcast_to(g, (th, tw, 3))
    rgba = np.zeros((th, tw, 4), np.float32)
    # sombra suave para que se lea sobre cualquier fondo
    al = np.maximum(a_s, a_v)
    sh = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
    sh = np.roll(sh, 4, 0) * 0.55
    rgba[..., 3] = sh
    for col, a in ((np.ones(3), a_s), (g, a_v)):
        outa = a + rgba[..., 3] * (1 - a)
        rgba[..., :3] = np.where(outa[..., None] > 1e-4, (col * a[..., None] + rgba[..., :3] * rgba[..., 3:4] * (1 - a[..., None])) / np.maximum(outa[..., None], 1e-4), 0)
        rgba[..., 3] = outa
    sp = Sprite(rgba, 0, PAD)
    sp.ink = (tw - 2 * PAD, alto)
    sp.ox = PAD
    return sp


class CajaMision:
    """caja de misión de una línea: «MISIÓN» (Saira 700, celeste) + bloques ▮ dibujados como rectángulos con la
    distribución letra por letra de «so f★cking close.» (★ U+2605 de Inter Display, celeste; punto final visible).
    Fondo: caja negra α 0,55 radio 10, raya celeste a la izquierda."""
    PX = 56                     # cuerpo de los bloques / del texto descifrado (Saira 800)
    PX_LBL = 36
    PADX, PADY, GAP = 22, 15, 26

    def __init__(self):
        self.f = saira(self.PX, 800); self.fl = saira(self.PX_LBL, 700); self.fs = inter(self.PX, 'ExtraBold')
        s = TXT['oculto']
        self.chars = list(s)
        self.adv = [self.fs.getlength(ch) if ch == '★' else self.f.getlength(ch) for ch in self.chars]
        bb = self.f.getbbox('H', anchor='ls'); self.cap = -bb[1]
        bx = self.f.getbbox('x', anchor='ls'); self.xh = -bx[1]
        self.lbl_w = self.fl.getlength(TXT['mision']) + 3 * (len(TXT['mision']) - 1)
        bl = self.fl.getbbox('M', anchor='ls'); self.lbl_cap = -bl[1]
        self.txt_w = sum(self.adv)
        self.w = int(self.PADX * 2 + 6 + self.lbl_w + self.GAP + self.txt_w)
        self.h = int(self.cap + 2 * self.PADY)
        self.base = self.PADY + self.cap                     # línea de base dentro de la caja
        self.x_txt = self.PADX + 6 + self.lbl_w + self.GAP
        rng = np.random.default_rng(605)
        self.revuelto = [[rng.choice(list('ABCDEFGHJKLMNPRSTUVWXZ0123456789#%&')) for _ in range(40)] for _ in self.chars]
        self._cache = {}

    def letras(self):
        return [i for i, ch in enumerate(self.chars) if ch not in ' ★.']

    def sprite(self, estado='bloques', k=0, alfa_lbl=1.0, alfa_caja=1.0, alfa_txt=1.0):
        """estado: 'bloques' | 'descifra' (k = cuadro desde 13,20, 0–10) | 'texto'."""
        key = (estado, k, round(alfa_lbl, 3), round(alfa_caja, 3), round(alfa_txt, 3))
        if key in self._cache:
            return self._cache[key]
        ss = 3
        im = Image.new('RGBA', (self.w * ss, self.h * ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if alfa_caja > 0:
            d.rounded_rectangle([0, 0, self.w * ss - 1, self.h * ss - 1], radius=CAJA_R * ss,
                                fill=(0, 0, 0, int(255 * CAJA_A * alfa_caja)))
            d.rectangle([0, CAJA_R * ss, 6 * ss, (self.h - CAJA_R) * ss], fill=CELESTE + (int(255 * alfa_caja),))
        from PIL import ImageFont
        fl3 = ImageFont.truetype(self.fl.path, self.fl.size * ss); fl3.set_variation_by_axes([700, 100])
        f3 = ImageFont.truetype(self.f.path, self.f.size * ss); f3.set_variation_by_axes([800, 100])
        fs3 = ImageFont.truetype(self.fs.path, self.fs.size * ss)
        if alfa_lbl > 0:     # «MISIÓN» con espaciado +3, centrado en la altura de la caja
            x = (self.PADX + 6) * ss; yb = (self.h / 2 + self.lbl_cap / 2) * ss
            for ch in TXT['mision']:
                d.text((x, yb), ch, font=fl3, fill=CELESTE + (int(255 * alfa_lbl),), anchor='ls')
                x += (self.fl.getlength(ch) + 3) * ss
        orden = self.letras()
        x = self.x_txt
        a8 = int(255 * alfa_txt)
        for i, ch in enumerate(self.chars):
            a = self.adv[i]
            if ch == ' ':
                pass
            elif ch == '★':
                d.text((x * ss, self.base * ss), ch, font=fs3, fill=CELESTE + (a8,), anchor='ls')
            elif ch == '.':
                d.text((x * ss, self.base * ss), ch, font=f3, fill=(255, 255, 255, a8), anchor='ls')
            else:
                j = orden.index(i)
                if estado == 'bloques':
                    resuelto, revuelto = False, False
                elif estado == 'texto':
                    resuelto, revuelto = True, False
                else:   # descifra: la letra j se resuelve en el cuadro 1 + round(9 j / 12); antes, glifo revuelto
                    kr = 1 + round(9 * j / (len(orden) - 1))
                    resuelto = k >= kr; revuelto = not resuelto
                if resuelto:
                    d.text((x * ss, self.base * ss), ch, font=f3, fill=(255, 255, 255, a8), anchor='ls')
                elif revuelto:
                    g = self.revuelto[i][k % 40]
                    gw = self.f.getlength(g)
                    d.text(((x + (a - gw) / 2) * ss, self.base * ss), g, font=f3, fill=CELESTE + (a8,), anchor='ls')
                else:   # bloque ▮: rectángulo de altura de mayúscula, ancho del avance menos 3 px
                    d.rectangle([(x + 1.5) * ss, (self.base - self.cap) * ss, (x + a - 1.5) * ss, self.base * ss],
                                fill=(255, 255, 255, a8))
            x += a
        im = im.resize((self.w, self.h), Image.LANCZOS)
        sp = Sprite.de_pil(im, 0, 0)
        self._cache[key] = sp
        return sp

    def caja_texto_rel(self):
        """caja de la tinta del texto (x0, y0, w, h) relativa a la caja (para el viaje)."""
        return (self.x_txt, self.base - self.cap - (self.cap * 0.12), self.txt_w, self.cap * 1.12 + self.cap * 0.28)


def sp_hud(txt, px, acento=True, fuente=None):
    """HUD: Saira 800, blanco, en caja negra α 0,55 radio 10 con raya celeste a la izquierda."""
    t = texto_sprite([(txt, fuente or saira(px, 800), BLANCO)], pad=4)
    return t


def panel(lineas, padx=30, pady=22, raya=True, interlineado=None):
    """lineas: [(sprite_texto, y_rel_tinta)] con x centrado. Devuelve Sprite de la caja completa con (ox, oy) = esquina
    superior izquierda de la tinta de la primera línea (para ubicarla con y del guion)."""
    wmax = max(s.ink[0] for s, _ in lineas)
    y_top = min(yr for _, yr in lineas)
    y_bot = max(yr + s.ink[1] for s, yr in lineas)
    bw = int(wmax + 2 * padx + (8 if raya else 0)); bh = int(y_bot - y_top + 2 * pady)
    lz = np.zeros((bh, bw, 4), np.float32)
    caja = caja_sprite(bw, bh)
    lz[...] = caja.a
    if raya:
        lz[CAJA_R:bh - CAJA_R, 0:6, :3] = np.array(CELESTE) / 255; lz[CAJA_R:bh - CAJA_R, 0:6, 3] = 1.0
    out = Lienzo.__new__(Lienzo); out.p = np.zeros((bh, bw, 4), np.float32)
    out.p[..., :3] = lz[..., :3] * lz[..., 3:4]; out.p[..., 3] = lz[..., 3]
    xoff = (8 if raya else 0) / 2
    for s, yr in lineas:
        x = bw / 2 + xoff - s.ink[0] / 2; y = pady + (yr - y_top)
        _poner_local(out.p, s, x, y)
    a = out.p[..., 3:4]
    rgb = np.where(a > 1e-4, out.p[..., :3] / np.maximum(a, 1e-4), 0)
    sp = Sprite(np.concatenate([rgb, a], -1), padx + 2 * xoff + (wmax - lineas[0][0].ink[0]) / 2, pady + (lineas[0][1] - y_top))
    sp.caja = (bw, bh)
    sp.ink = (lineas[0][0].ink[0], lineas[0][0].ink[1])
    return sp


def _poner_local(p, sp, x, y):
    xi, yi = int(round(x - sp.ox)), int(round(y - sp.oy))
    a = sp.a; h, w = p.shape[:2]
    x1, y1 = max(0, xi), max(0, yi); x2, y2 = min(w, xi + a.shape[1]), min(h, yi + a.shape[0])
    s = a[y1 - yi:y2 - yi, x1 - xi:x2 - xi]; al = s[..., 3:4]
    d = p[y1:y2, x1:x2]
    d[..., :3] = s[..., :3] * al + d[..., :3] * (1 - al); d[..., 3:4] = al + d[..., 3:4] * (1 - al)


def tarjeta(detalle):
    """Tarjeta «CASI.»: Saira 800 150 px + raya celeste 220×4 + detalle Inter Display Bold 62 px (corrección 1);
    detalle con la tinta 180 px debajo de la de «CASI.» (640 → 820 del guion)."""
    t_casi = texto_sprite([(TXT['casi'], saira(150, 800), BLANCO)], pad=4)
    t_det = texto_sprite([(TXT[detalle], inter(62, 'Bold'), BLANCO)], pad=4)
    raya = Sprite(np.concatenate([np.broadcast_to(np.array(CELESTE, np.float32) / 255, (4, 220, 3)),
                                  np.ones((4, 220, 1), np.float32)], -1), 0, 0)
    raya.ink = (220, 4)
    y_raya = t_casi.ink[1] + (Y['casi_det'] - t_casi.ink[1]) / 2 - 2
    return panel([(t_casi, 0), (raya, y_raya), (t_det, Y['casi_det'])], padx=34, pady=26, raya=False)


class Anillo:
    """anillo de progreso con antialias (supermuestreo 4×)."""
    def __init__(self, r, grosor, pista_a=0.28, color=CELESTE, fondo=None):
        self.r, self.g, self.pa, self.col, self.fondo = r, grosor, pista_a, color, fondo

    def sprite(self, frac, brillo=0.0):
        ss = 4; S = int((self.r * 2 + 8) * ss)
        im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        o = 4 * ss; bbox = [o, o, S - o, S - o]
        if self.fondo is not None:
            d.ellipse(bbox, fill=self.fondo)
        d.ellipse(bbox, outline=(255, 255, 255, int(255 * self.pa)), width=int(self.g * ss))
        if frac > 0.001:
            col = tuple(int(lerp(cc, 255, brillo)) for cc in self.col)
            d.arc(bbox, -90, -90 + 360 * min(frac, 1.0) if frac < 0.9995 else 270, fill=col + (255,), width=int(self.g * ss))
        im = im.resize((S // ss, S // ss), Image.LANCZOS)
        return Sprite.de_pil(im, S // ss / 2, S // ss / 2)


def sp_minimapa_fondo(r):
    """radar propio: mar azul noche, costa y calles esquemáticas, flecha del jugador. Sin rótulos."""
    ss = 4; S = int(2 * r * ss)
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, S - 1, S - 1], fill=(14, 28, 56, 215))
    # tierra (costa curva a la derecha) en gris pizarra
    pts = [(S * 0.62, 0), (S * 0.55, S * 0.25), (S * 0.60, S * 0.45), (S * 0.52, S * 0.7), (S * 0.58, S), (S, S), (S, 0)]
    land = Image.new('L', (S, S), 0); ImageDraw.Draw(land).polygon([(S - x, y) for x, y in pts], fill=255)
    tierra = Image.new('RGBA', (S, S), (52, 66, 88, 235))
    im.paste(tierra, (0, 0), land)
    # calles
    for (x0, y0, x1, y1, w) in [(0.05, 0.30, 0.47, 0.34, 0.035), (0.05, 0.62, 0.45, 0.58, 0.035), (0.22, 0.0, 0.26, 1.0, 0.03),
                                (0.36, 0.05, 0.40, 0.95, 0.022), (0.10, 0.46, 0.44, 0.47, 0.018)]:
        d.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=(150, 162, 180, 230), width=int(w * S))
    m = Image.new('L', (S, S), 0); ImageDraw.Draw(m).ellipse([0, 0, S - 1, S - 1], fill=255)
    im.putalpha(Image.fromarray(np.minimum(np.asarray(im)[..., 3], np.asarray(m)).astype(np.uint8)))
    # flecha del jugador (blanca) y objetivo (celeste)
    d = ImageDraw.Draw(im)
    cx = cy = S / 2; a = 0.11 * S
    d.polygon([(cx, cy - a), (cx + a * 0.62, cy + a * 0.7), (cx, cy + a * 0.35), (cx - a * 0.62, cy + a * 0.7)], fill=(255, 255, 255, 255))
    d.ellipse([S * 0.70 - 0.045 * S, S * 0.22 - 0.045 * S, S * 0.70 + 0.045 * S, S * 0.22 + 0.045 * S], fill=CELESTE + (255,))
    im = im.resize((S // ss, S // ss), Image.LANCZOS)
    return Sprite.de_pil(im, S // ss / 2, S // ss / 2)


def sp_contador(txt, px=120):
    """«0,80 m»: Saira 800 con dígitos en celdas de ancho fijo (sin baile al cambiar de número)."""
    f = saira(px, 800)
    celda = max(f.getlength(ch) for ch in '0123456789')
    ss = 3
    from PIL import ImageFont
    f3 = ImageFont.truetype(f.path, px * ss); f3.set_variation_by_axes([800, 100])
    ancho = sum(celda if ch.isdigit() else f.getlength(ch) for ch in txt)
    asc, desc = f.getmetrics()
    im = Image.new('RGBA', (int(ancho + 8) * ss, int(asc + desc + 8) * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = 4; yb = 4 + asc
    for ch in txt:
        a = celda if ch.isdigit() else f.getlength(ch)
        d.text(((x + (a - f.getlength(ch)) / 2) * ss, yb * ss), ch, font=f3, fill=(255, 255, 255, 255), anchor='ls')
        x += a
    im = im.resize((im.width // ss, im.height // ss), Image.LANCZOS)
    bb = im.getbbox()
    sp = Sprite.de_pil(im, bb[0], bb[1]); sp.ink = (bb[2] - bb[0], bb[3] - bb[1])
    return sp


def valor_contador(n):
    """cuadro → texto del contador. 10,10–11,45: 80 → 1 cm con n(u) = 1 + ceil(79·(1−u)^2,6) (se desacelera, como
    tics_contador.py); 11,45–11,70: queda en «0,01 m»."""
    t = n / FPS; t0 = TM['contador'][0]; t1 = TM['contador_llega']
    u = clamp((t - t0) / (t1 - t0))
    cm = 1 if u >= 1 else 1 + math.ceil(79 * (1 - u) ** 2.6)
    return f'0,{cm:02d} m', cm


# ============================================================================== sistema
class Grafica:
    def __init__(self, variante='A'):
        assert variante in ('A', 'B')
        self.v = variante
        self.logo = sp_logo()
        k1, k2 = ('zona', 'nadie') if variante == 'A' else ('pero', 'falta')
        self.txt_h1, self.txt_h2 = TXT[k1], TXT[k2]
        self.h1 = sp_hook(self.txt_h1, 84)
        self.h2 = sp_hook(self.txt_h2, 76)
        self.mision = CajaMision()
        self.gana = panel([(texto_sprite([(TXT['gana'], saira(84, 800), BLANCO)], pad=4), 0),
                           (texto_sprite([(TXT['sol'], inter(62, 'Bold'), BLANCO)], pad=4), Y['sol'] - Y['gana'])])
        self.tarjetas = {k: tarjeta(k) for k in ('cm', 'mm', 'una', 'nada')}
        self.rep = panel([(texto_sprite([(TXT['rep'], saira(120, 800), BLANCO)], pad=4), 0)])
        self.frase = texto_sprite([('so f', inter(98), BLANCO), ('★', inter(98), CELESTE), ('cking close.', inter(98), BLANCO)],
                                  stroke=6, stroke_fill=NEGRO)
        # v01 (03 de Roma, corrección 1): ×1,41 (Saira 44 → 62, caja 24/14 → 34/20): tinta 692 px, caja 768 px ≤ 814 (frase)
        self.insp = panel([(texto_sprite([(TXT['inspirado'], saira(62, 700), CELESTE)], pad=4), 0)], padx=34, pady=20)
        x0, y0, x1, y1 = Y['mini']; self.mini_r = (x1 - x0) / 2; self.mini_c = ((x0 + x1) / 2, (y0 + y1) / 2)
        self.mini_fondo = sp_minimapa_fondo(self.mini_r - 9)
        self.mini_anillo = Anillo(self.mini_r - 4.5, 9)
        self.carga = Anillo(56, 9)
        self._cont = {}
        self.layout = self.layout_hook()

    # ---------------------------------------------------------------- hook
    def _caja_hook(self, que):
        """caja de lo dibujado (incluye contorno o caja) en coordenadas del cuadro."""
        if que == 'logo':
            s = self.logo; x = 540 - s.ink[0] / 2; y = Y['logo'][0]
            return (x - 4, y - 4, x + s.ink[0] + 4, y + s.ink[1] + 8)
        if que in ('h1', 'h2', 'h2_arriba'):
            s = self.h1 if que == 'h1' else self.h2
            y = Y['hook1'] if que in ('h1', 'h2_arriba') else Y['hook2']
            x = 540 - s.ink[0] / 2
            return (x - 6, y - 6, x + s.ink[0] + 6, y + s.ink[1] + 6)
        if que == 'caja':
            m = self.mision; x = 540 - m.w / 2; y = Y['caja'] - m.PADY
            return (x, y, x + m.w, y + m.h)
        if que == 'carga':
            cx, cy = Y['carga']; r = self.carga.r + 5
            return (cx - r, cy - r, cx + r, cy + r)

    @staticmethod
    def _sep(a, b):
        """separación vertical entre dos cajas (negativa = se pisan)."""
        return max(b[1] - a[3], a[1] - b[3])

    def layout_hook(self):
        """corrección 2: con el orden original (h1 en 340 desde c0, caja en 460 desde 0,40, h2 en 540 desde 0,50) se mide
        la separación vertical entre los cuatro elementos. Si alguna es < SEPARACION_MIN (10 px a 360 de ancho), se aplica
        lo que dejó escrito Roma: h1 sale en 0,50 y h2 toma su lugar (y 340)."""
        cajas = {k: self._caja_hook(k) for k in ('logo', 'h1', 'caja', 'h2')}
        seps = {'logo-h1': self._sep(cajas['logo'], cajas['h1']), 'h1-caja': self._sep(cajas['h1'], cajas['caja']),
                'caja-h2': self._sep(cajas['caja'], cajas['h2'])}
        pegados = [k for k, v in seps.items() if v < SEPARACION_MIN]
        alt = {k: self._caja_hook(k) for k in ('logo', 'h2_arriba', 'caja')}
        seps_alt = {'logo-h2': self._sep(alt['logo'], alt['h2_arriba']), 'h2-caja': self._sep(alt['h2_arriba'], alt['caja'])}
        anchos = {'h1': round(self.h1.ink[0]), 'h2': round(self.h2.ink[0]), 'caja': self.mision.w, 'logo': round(self.logo.ink[0])}
        return dict(variante=self.v, cajas={k: [round(v) for v in b] for k, b in cajas.items()},
                    separaciones_px_1080=seps, separaciones_px_360={k: round(v / 3, 1) for k, v in seps.items()},
                    pegados=pegados, aplica_reemplazo=bool(pegados),
                    separaciones_reemplazo_px_1080=seps_alt, anchos_px=anchos,
                    h1=(0.00, 0.50) if pegados else (0.00, 1.50),
                    h2=dict(t=(0.50, 1.80), y=Y['hook1'] if pegados else Y['hook2']))

    # ---------------------------------------------------------------- capa por cuadro
    def capa(self, n, degrade=True):
        t = n / FPS
        lz = Lienzo()
        vis = []
        # degradé de FMT-03 (detrás de todo)
        if degrade:
            for (t0, t1, yp, yc) in DEGRADE:
                if c(t0) <= n < c(t1):
                    fi = clamp((n - c(t0) + 1) / DEG_FUNDIDO_C); fo = clamp((c(t1) - n) / DEG_FUNDIDO_C)
                    a = perfil(DEG_ALFA, yp, yc) * min(fi, fo)
                    lz.p[..., 3] = a[:, None]
                    vis.append('degradé')
        # anillo de carga del hook: 0 → 100 % (llega en 1,40, «ping»), sale con el corte de 1,50
        if c(TM['carga'][0]) <= n < c(TM['carga'][1]):
            fr = ease_in_out(t / TM['carga_llena']) if t < TM['carga_llena'] else 1.0
            fr = clamp(0.92 * (t / TM['carga_llena']) + 0.08 * fr) if t < TM['carga_llena'] else 1.0
            brillo = 0.6 if c(TM['carga_llena']) <= n < c(TM['carga_llena']) + 2 else 0.0
            lz.poner(self.carga.sprite(fr, brillo), *Y['carga'])
            vis.append('anillo de carga')
        # logo (solo 0,00–1,50)
        if c(TM['logo'][0]) <= n < c(TM['logo'][1]):
            lz.poner(self.logo, 540 - self.logo.ink[0] / 2 + self.logo.ox - self.logo.ox, Y['logo'][0])
            vis.append('logo')
        L = self.layout
        # caja de misión / descifrado / viaje (debajo de los hooks: entre 1,50 y 1,80 la caja pasa por detrás de
        # «NADIE LA TERMINA» camino a la esquina)
        self._mision(n, lz, vis)
        # hook 1 (ZONA NUEVA / PERO SIEMPRE)
        if c(L['h1'][0]) <= n < c(L['h1'][1]):
            lz.poner(self.h1, 540 - self.h1.ink[0] / 2, Y['hook1']); vis.append(self.txt_h1)
        # hook 2 (NADIE LA TERMINA / TE FALTA 1 CM): cruza el corte
        t0, t1 = L['h2']['t']
        if c(t0) <= n < c(t1):
            k = n - c(t0); s = [1.12, 1.08, 1.04][k] if k < 3 else 1.0
            lz.poner(self.h2, 540 - self.h2.ink[0] / 2, L['h2']['y'], escala=s); vis.append(self.txt_h2)
        # minimapa con anillo que se vacía de 1,50 a 13,20
        if c(TM['mini'][0]) <= n < c(TM['mini'][1]) + 3:
            k = n - c(TM['mini'][0])
            s = [1.12, 1.08, 1.04][k] if 0 <= k < 3 else 1.0
            fo = clamp((c(TM['mini'][1]) + 3 - n) / 3) if n >= c(TM['mini'][1]) else 1.0
            fr = 1 - clamp((t - TM['anillo'][0]) / (TM['anillo'][1] - TM['anillo'][0]))
            n0 = c(TM['anillo'][1])
            brillo = 1.0 if n0 <= n < n0 + 4 and (n - n0) % 2 == 0 else 0.0
            cx, cy = self.mini_c
            lz.poner(self.mini_fondo, cx, cy, alfa=fo, escala=s)
            an = self.mini_anillo.sprite(fr, 0)
            if brillo:   # al llegar a 0, la pista parpadea en blanco
                an = Anillo(self.mini_r - 4.5, 9, pista_a=0.9).sprite(0)
            lz.poner(an, cx, cy, alfa=fo, escala=s)
            vis.append(f'minimapa {fr * 100:.0f} %')
        # GANÁ UNA / antes de que caiga el sol
        self._panel(n, lz, vis, self.gana, TM['gana'], Y['gana'], 'GANÁ UNA + antes de que caiga el sol')
        # 19/20
        self._panel(n, lz, vis, self.rep, TM['rep'], Y['rep'], TXT['rep'], pop=True)
        # tarjetas CASI.
        for (a, b, det, y) in TM['casi']:
            if c(a) <= n < c(b):
                k = n - c(a); s = [1.12, 1.08, 1.04, 1.0][k] if k < 4 else 1.0
                tj = self.tarjetas[det]
                cx = 540; cy = y - tj.oy + tj.h / 2
                lz.poner(tj, 540 - tj.ink[0] / 2, y, escala=s, ancla=(cx, cy))
                vis.append(f'CASI. + {TXT[det]}')
        # contador
        if c(TM['contador'][0]) <= n < c(TM['contador'][1]):
            txt, cm = valor_contador(n)
            if txt not in self._cont:
                self._cont[txt] = panel([(sp_contador(txt), 0)])
            sp = self._cont[txt]
            # la caja se fija con el ancho de «0,80 m» (las celdas son fijas: el ancho no cambia)
            lz.poner(sp, 540 - sp.ink[0] / 2, Y['contador']); vis.append(f'contador {txt}')
        return lz, vis

    def _panel(self, n, lz, vis, sp, tt, y, nombre, pop=False):
        a, b = tt
        if c(a) <= n < c(b):
            k = n - c(a)
            s = ([1.12, 1.08, 1.04][k] if k < 3 else 1.0) if pop else ([1.06, 1.03][k] if k < 2 else 1.0)
            al = clamp((k + 1) / 2) if not pop else 1.0
            al *= clamp((c(b) - n) / 2)
            cy = y - sp.oy + sp.h / 2
            lz.poner(sp, 540 - sp.ink[0] / 2, y, alfa=al, escala=s, ancla=(540, cy))
            vis.append(nombre)

    def _mision(self, n, lz, vis):
        m = self.mision
        n_in = c(TM['caja_in']); a0, a1 = c(TM['achica'][0]), c(TM['achica'][1])
        d0, d1 = c(TM['descifra'][0]), c(TM['descifra'][1])
        v0, v1 = c(TM['viaja'][0]), c(TM['viaja'][1])
        nf = c(TM['fin_textos']); fc = TM['fundido_c']
        if n < n_in or n >= nf:
            return
        # posición de la caja: centro (y 460) → esquina (60, 170) con escala 0,55 entre 1,50 y 1,80
        xc, yc = 540 - m.w / 2, Y['caja'] - m.PADY
        xe, ye = Y['esquina']; se = Y['esquina_escala']
        u = ease_in_out((n - a0) / (a1 - a0)) if n >= a0 else 0.0
        x = lerp(xc, xe, u); y = lerp(yc, ye, u); s = lerp(1.0, se, u)
        if n < d0:
            al = clamp((n - n_in + 1) / 3)
            sp = m.sprite('bloques')
            lz.poner(sp, x, y, alfa=al, escala=s, ancla=(x, y))
            vis.append('caja de misión (bloques, ★)')
            return
        if n < v0:      # descifrado en 0,35 s (11 cuadros)
            sp = m.sprite('descifra', k=n - d0)
            lz.poner(sp, x, y, escala=s, ancla=(x, y))
            vis.append(f'caja de misión descifrando k={n - d0}')
            return
        # viaje: la caja de tinta pasa de la caja chica (Saira) a la frase Grande (Inter Display ExtraBold, y 520)
        fr = self.frase
        tx, ty, tw, th = m.caja_texto_rel()
        r0 = (x + tx * s, y + (m.base - m.cap) * s, m.txt_w * s)               # x, y de tinta, ancho
        r1 = (540 - fr.ink[0] / 2, Y['frase'], fr.ink[0])
        al_fin = clamp((nf - n) / fc) if n >= nf - fc else 1.0
        if n < v1:
            u = ease_in_out((n - v0 + 1) / (v1 - v0 + 1))
            xs = lerp(r0[0], r1[0], u); ys = lerp(r0[1], r1[1], u); ws = lerp(r0[2], r1[2], u)
            # caja y «MISIÓN» se apagan; el texto chico se funde en el grande mientras viaja
            caja = m.sprite('texto', alfa_lbl=1 - u, alfa_caja=1 - u, alfa_txt=0.0)
            lz.poner(caja, x, y, escala=s, ancla=(x, y))
            chico = m.sprite('texto', alfa_lbl=0, alfa_caja=0, alfa_txt=1.0)
            sc = ws / (m.txt_w * s)
            # el sprite chico tiene su tinta en (tx, base - cap) dentro de la caja
            lz.poner(chico, xs - tx * s * sc, ys - (m.base - m.cap) * s * sc, alfa=1 - u, escala=s * sc, ancla=(xs - tx * s * sc, ys - (m.base - m.cap) * s * sc))
            sg = ws / fr.ink[0]
            lz.poner(fr, xs, ys, alfa=u, escala=sg, ancla=(xs, ys))
            vis.append(f'viaje de la frase u={u:.2f}')
            return
        # final: «INSPIRADO EN EL DROP» (Etiqueta 62 px, y 414) + «so f★cking close.» (Grande, y 520) hasta 15,70
        k = n - v1
        si = [1.06, 1.04, 1.02][k] if k < 3 else 1.0       # v01: el pop no pasa el ancho de la frase (768 × 1,06 = 814)
        cy = Y['inspirado'] - self.insp.oy + self.insp.h / 2
        lz.poner(self.insp, 540 - self.insp.ink[0] / 2, Y['inspirado'], alfa=al_fin, escala=si, ancla=(540, cy))
        lz.poner(fr, 540 - fr.ink[0] / 2, Y['frase'], alfa=al_fin)
        vis.append(f"{TXT['inspirado']} + {TXT['frase']}")


# ============================================================================== control
def control_zonas(g, n0=0, n1=ND):
    """alfa > 0,02 en las zonas prohibidas, cuadro por cuadro (sin el degradé, que es de arriba)."""
    malos = []
    cajas = {}
    for n in range(n0, n1):
        lz, vis = g.capa(n, degrade=False)
        a = lz.p[..., 3]
        z1 = a[1150:1701, 940:1061].max(); z2 = a[1561:, :].max()
        if z1 > 0.02 or z2 > 0.02:
            malos.append(dict(cuadro=n, zona_botones=round(float(z1), 3), bajo_1560=round(float(z2), 3), vis=vis))
        ys, xs = np.nonzero(a > 0.02)
        if len(ys):
            cajas[n] = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return malos, cajas


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else 'control'
    if etapa == 'control':
        rep = {}
        for v in ('A', 'B'):
            g = Grafica(v)
            malos, cajas = control_zonas(g)
            yb = max(b[3] for b in cajas.values()); xr = [b for b in cajas.values()]
            rep[v] = dict(layout_hook=g.layout, zonas_prohibidas_cuadros_con_algo=malos,
                          y_max_dibujado=yb, x_min=min(b[0] for b in xr), x_max=max(b[2] for b in xr),
                          textos=dict(h1=g.txt_h1, h2=g.txt_h2))
            print(v, json.dumps(g.layout, ensure_ascii=False), 'malos', len(malos), 'y_max', yb)
        rep['textos_exactos'] = {k: v for k, v in TXT.items()}
        rep['contador'] = {n: valor_contador(n)[0] for n in range(c(TM['contador'][0]), c(TM['contador'][1]))}
        guardar_json(rep, T / 'grafica_control.json')
