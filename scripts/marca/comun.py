#!/usr/bin/env python3
"""MARCA · comunidad (24-25/11/2026) · interfaz nativa común a los 5 videos UGC y las 3 historias.

Todo se dibuja con Pillow como capas RGBA de 1080x1920 (una por estado) y se superpone con
`video.master(overlays=[(png, 0, 0, t0, t1), ...])`. Así los cinco videos comparten exactamente el mismo
lenguaje de texto (caja redondeada tipo TikTok, placa con halo, burbuja de comentario) y la misma zona segura.

Uso típico:
    import comun as C
    L = C.lienzo()
    C.pegar(L, C.caja('¿ME SALE UNA MARCA PREMIUM?', 78), y=260)
    C.pegar(L, C.placa('TENGO 19.', 92), y=820)
    L.save('estado_01.png')
    C.pop(lambda e: armar(e), 'TRABAJO/marca/MC-01/hook', t0=0.0, t1=1.2)  -> lista de overlays con «pop» de 3 cuadros
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
FUENTES = Path('/usr/share/fonts/opentype/inter')
F = {
    'medium': FUENTES / 'InterDisplay-Medium.otf',
    'semibold': FUENTES / 'InterDisplay-SemiBold.otf',
    'extrabold': FUENTES / 'InterDisplay-ExtraBold.otf',
    'black': FUENTES / 'InterDisplay-Black.otf',
}
TINTA = (20, 20, 20)            # #141414
BLANCO = (255, 255, 255)
CELESTE = (205, 221, 229)       # #CDDDE5, celeste de marca (solo sobre fondo oscuro)
ZONA = dict(y_min=220, y_max=1540, x_max_abajo=940)   # zona segura de la tanda (05_especificacion_comun.md)


def fuente(peso, size):
    return ImageFont.truetype(str(F[peso]), size)


def lienzo():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))


def _medir(txt, fnt):
    x0, y0, x1, y1 = fnt.getbbox(txt)
    return x1 - x0, y1 - y0, x0, y0


def caja(texto, size=78, tema='blanca', peso='semibold', pad=(30, 18), radio=20, interlineado=1.12):
    """Texto con caja redondeada por renglón (como el estilo «fondo» de TikTok/IG). '\n' separa renglones.
    tema 'blanca' = caja blanca, texto #141414; 'negra' = caja #141414, texto blanco."""
    fnt = fuente(peso, size)
    fondo, tinta = (BLANCO, TINTA) if tema == 'blanca' else (TINTA, BLANCO)
    renglones = texto.split('\n')
    asc, desc = fnt.getmetrics()
    alto_r = int(round((asc + desc) * interlineado))
    anchos = [fnt.getlength(r) for r in renglones]
    Wc = int(max(anchos) + 2 * pad[0]) + 4
    Hc = alto_r * len(renglones) + 2 * pad[1]
    im = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, (r, a) in enumerate(zip(renglones, anchos)):
        x0 = (Wc - a) / 2 - pad[0]
        y0 = i * alto_r
        d.rounded_rectangle([x0, y0, x0 + a + 2 * pad[0], y0 + alto_r + 2 * pad[1] - (0 if i == len(renglones) - 1 else 0)],
                            radius=radio, fill=fondo + (255,))
    for i, (r, a) in enumerate(zip(renglones, anchos)):
        d.text(((Wc - a) / 2, i * alto_r + pad[1] + (alto_r - (asc + desc)) / 2), r, font=fnt, fill=tinta + (255,))
    return im


def placa(texto, size=92, peso='extrabold', color=BLANCO, halo=0.55, interlineado=1.05, sombra_px=None):
    """Texto grande con halo oscuro suave (legible sobre espuma o cielo sin caja). '\n' separa renglones."""
    fnt = fuente(peso, size)
    renglones = texto.split('\n')
    asc, desc = fnt.getmetrics()
    alto_r = int(round((asc + desc) * interlineado))
    anchos = [fnt.getlength(r) for r in renglones]
    m = int(size * 0.6)
    Wc, Hc = int(max(anchos)) + 2 * m, alto_r * len(renglones) + 2 * m
    txt = Image.new('L', (Wc, Hc), 0)
    d = ImageDraw.Draw(txt)
    for i, (r, a) in enumerate(zip(renglones, anchos)):
        d.text(((Wc - a) / 2, m + i * alto_r), r, font=fnt, fill=255)
    rad = sombra_px or max(6, size // 7)
    som = txt.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(rad))
    im = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0))
    im.putalpha(som.point(lambda v: int(v * halo)))
    capa = Image.new('RGBA', (Wc, Hc), color + (0,))
    capa.putalpha(txt)
    return Image.alpha_composite(im, capa)


def burbuja(comentario, etiqueta='Comentario en TikTok', size=52, ancho_max=760):
    """Tarjeta blanca redondeada con un comentario real (sin usuario ni foto)."""
    f1, f2 = fuente('semibold', size), fuente('medium', int(size * 0.62))
    pad = 34
    w_txt = min(max(f1.getlength(comentario), f2.getlength(etiqueta)), ancho_max)
    a1, d1 = f1.getmetrics(); a2, d2 = f2.getmetrics()
    Wc = int(w_txt + 2 * pad); Hc = int(pad * 2 + (a2 + d2) + 10 + (a1 + d1))
    im = Image.new('RGBA', (Wc + 24, Hc + 24), (0, 0, 0, 0))
    sh = Image.new('L', im.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle([12, 16, 12 + Wc, 16 + Hc], radius=28, fill=110)
    im.putalpha(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([12, 12, 12 + Wc, 12 + Hc], radius=28, fill=BLANCO + (255,))
    d.text((12 + pad, 12 + pad), etiqueta, font=f2, fill=(120, 120, 124, 255))
    d.text((12 + pad, 12 + pad + a2 + d2 + 10), comentario, font=f1, fill=TINTA + (255,))
    return im


def pegar(L, im, y, cx=W // 2, x=None, escala=1.0):
    """Pega `im` en el lienzo L, centrado en cx (o desde x), con su borde superior en y. Controla la zona segura."""
    if escala != 1.0:
        im = im.resize((max(1, round(im.width * escala)), max(1, round(im.height * escala))), Image.LANCZOS)
    x0 = x if x is not None else round(cx - im.width / 2)
    y0 = round(y - (im.height * (escala - 1) / 2 if escala != 1.0 else 0))
    L.alpha_composite(im, (int(x0), int(y0)))
    return (int(x0), int(y0), int(x0 + im.width), int(y0 + im.height))


def fuera_de_zona(cajas):
    """Devuelve las cajas (x0,y0,x1,y1) que salen de la zona segura de la tanda."""
    malas = []
    for c in cajas:
        x0, y0, x1, y1 = c
        if y0 < ZONA['y_min'] or y1 > ZONA['y_max'] or (y1 > H / 2 and x1 > ZONA['x_max_abajo'] and x1 - x0 < 900):
            malas.append(c)
    return malas


def pop(armar, base, t0, t1):
    """Genera la capa con «pop» (118 % → 109 % → 100 % en 3 cuadros, como el resto de la casa).
    armar(escala) -> lienzo RGBA. Devuelve overlays [(png, 0, 0, t0, t1), ...] para video.master."""
    base = Path(base); base.parent.mkdir(parents=True, exist_ok=True)
    out = []
    escalas = [1.18, 1.09]
    for k, e in enumerate(escalas):
        p = base.with_name(f'{base.name}_pop{k}.png'); armar(e).save(p)
        out.append((str(p), 0, 0, t0 + k / FPS, t0 + (k + 1) / FPS))
    p = base.with_name(f'{base.name}.png'); armar(1.0).save(p)
    out.append((str(p), 0, 0, t0 + len(escalas) / FPS, t1))
    return out


def fijo(L, base, t0, t1):
    p = Path(base).with_suffix('.png'); p.parent.mkdir(parents=True, exist_ok=True); L.save(p)
    return [(str(p), 0, 0, t0, t1)]
