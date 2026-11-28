# Piezas comunes de las historias Roccé Life del 28/11/2026 (Cetré, Paredes, Leclerc), sobre el motor reel.py.
# Clip con zoom y cámara lenta, banda negra que tapa los rótulos incrustados (con el descargo adentro), etiquetas, tarjetas de
# cita (Instrument Serif cursiva sobre azul noche), titulares con palabra clave en celeste y placa negra de firma.
import os
from reel import *

estado = {}


def clip(nombre, src, t0, zoom=1.0, cx=0.5, cy=0.5, lento=1.0, osc=None, congelar_en=None, bn_=False):
    """lento=2.0 → mitad de velocidad (con interpolación por mezcla de cuadros)."""
    def f(c, k):
        if k == 0 or nombre not in estado:
            if nombre in estado: estado[nombre].cerrar()
            pre = f"scale={W}:{H}"
            if lento != 1.0:
                pre += f",setpts={lento}*PTS,framerate=fps=30"
            crop = None
            if zoom != 1.0:
                cw, ch = int(W / zoom) // 2 * 2, int(H / zoom) // 2 * 2
                x = int(max(0, min(W - cw, cx * W - cw / 2))); y = int(max(0, min(H - ch, cy * H - ch / 2)))
                crop = f"{cw}:{ch}:{x}:{y}"
            estado[nombre] = Lector(src, t0, W, H, crop=crop, uno_a_uno=False, vf_pre=pre)
        a = estado[nombre].ult if (congelar_en is not None and k >= congelar_en) else estado[nombre].cuadro()
        a = a.copy()
        if osc: a = oscurecer(a, *osc)
        return a
    return f


def cerrar(nombre):
    return lambda: estado.pop(nombre).cerrar() if nombre in estado else None


def seg(a, b, fuente_, nombre=None):
    d = dict(c0=cs(a) if isinstance(a, float) else a, c1=cs(b) if isinstance(b, float) else b, fuente=fuente_)
    if nombre: d["cerrar"] = cerrar(nombre)
    return d


def negro(c, k):
    return np.zeros((H, W, 3), np.uint8)


# ---------- capas ----------
def banda(y0=1200, y1=1345, alfa=0.85, descargo=None):
    """banda negra a todo el ancho que tapa los rótulos incrustados; el descargo (40 px) va adentro."""
    img = Image.new("RGBA", (W, y1 - y0), (0, 0, 0, int(255 * alfa)))
    if descargo:
        f = fuente("inter_m", 40)
        lh = 48
        y = (y1 - y0 - lh * len(descargo)) // 2
        d = ImageDraw.Draw(img)
        for l in descargo:
            assert 60 + f.getlength(l) <= 950, f"descargo largo: {l}"
            d.text((60, y), l, font=f, fill=(236, 236, 236, 255)); y += lh
    return img


def titular(lineas, size=92, clave=None, ancho=900, fk="disp_xb"):
    """líneas en blanco; la palabra o línea `clave` (índice de línea) en celeste. Ajusta el tamaño al ancho."""
    while max(fuente(fk, size).getlength(l) for l in lineas) > ancho: size -= 2
    if clave is None:
        return capa_texto(lineas, fk, size, sombra=0.8, radio_sombra=14)
    capas = [capa_texto([l], fk, size, color=(CEL if i == clave else (255, 255, 255)), sombra=0.8, radio_sombra=14)
             for i, l in enumerate(lineas)]
    lh = int(size * 1.08)
    img = Image.new("RGBA", (W, lh * (len(lineas) - 1) + capas[-1].size[1]), (0, 0, 0, 0))
    for i, cp in enumerate(capas):
        img.alpha_composite(cp, (0, i * lh))
    return img


def etiqueta(txt, size=40):
    """pastilla celeste con texto azul noche (ATAJADA 1, INTENTO 2, +10 s)."""
    f = fuente("disp_xb", size)
    tw = f.getlength(txt) + 2 * 3 * len(txt)
    bw, bh = int(tw + 44), int(size * 1.55)
    img = Image.new("RGBA", (W, bh + 20), (0, 0, 0, 0))
    x0 = (W - bw) // 2
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, 6, x0 + bw, 6 + bh], radius=bh // 2, fill=CEL + (255,))
    x = x0 + 22
    for ch in txt:
        d.text((x, 6 + (bh - size * 1.2) / 2), ch, font=f, fill=NOCHE + (255,)); x += f.getlength(ch) + 6
    return img


def cita(lineas, clave=None, encabezado=None, size=60, autor=None):
    """tarjeta de cita: azul noche al 90 %, radio 18, Instrument Serif cursiva blanca, palabra clave en celeste."""
    fi = fuente("serif_i", size)
    fe = fuente("inter_sb", 30)
    fa = fuente("inter_m", 32)
    lh = int(size * 1.12)
    while max(fi.getlength(l) for l in lineas) > 820:
        size -= 2; fi = fuente("serif_i", size); lh = int(size * 1.12)
    wmax = max([fi.getlength(l) for l in lineas] + [fe.getlength(encabezado) + 2 * len(encabezado) if encabezado else 0])
    pad = 40
    bw = int(min(980, wmax + 2 * pad))
    bh = pad + (52 if encabezado else 0) + lh * len(lineas) + (50 if autor else 0) + pad - 10
    img = Image.new("RGBA", (W, bh + 40), (0, 0, 0, 0))
    x0 = (W - bw) // 2
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0, 14, x0 + bw, 14 + bh], radius=18, fill=(0, 0, 0, 120))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, 6, x0 + bw, 6 + bh], radius=18, fill=NOCHE + (230,))
    y = 6 + pad - 8
    if encabezado:
        x = (W - (fe.getlength(encabezado) + 2 * (len(encabezado) - 1))) / 2
        for ch in encabezado:
            d.text((x, y), ch, font=fe, fill=CEL + (255,)); x += fe.getlength(ch) + 2
        y += 52
    for l in lineas:
        if clave and clave in l:
            a, b = l.split(clave, 1)
            x = (W - fi.getlength(l)) / 2
            d.text((x, y), a, font=fi, fill=(255, 255, 255, 255)); x += fi.getlength(a)
            d.text((x, y), clave, font=fi, fill=CEL + (255,)); x += fi.getlength(clave)
            d.text((x, y), b, font=fi, fill=(255, 255, 255, 255))
        else:
            d.text(((W - fi.getlength(l)) / 2, y), l, font=fi, fill=(255, 255, 255, 255))
        y += lh
    if autor:
        d.text(((W - fa.getlength(autor)) / 2, y + 8), autor, font=fa, fill=(200, 210, 225, 255))
    return img


def _partes(txt):
    """separa la estrella (★), que la serif no tiene: va en Inter Display ExtraBold al 62 % del tamaño."""
    out, buf = [], ""
    for ch in txt:
        if ch == "★":
            if buf: out.append((buf, False)); buf = ""
            out.append((ch, True))
        else:
            buf += ch
    if buf: out.append((buf, False))
    return out


def ancho_mixto(txt, fk, size):
    return sum(fuente("disp_xb", int(size * 0.62)).getlength(t) if e else fuente(fk, size).getlength(t) for t, e in _partes(txt))


def escribir_mixto(d, x, y, txt, fk, size, fill=(255, 255, 255, 255)):
    f = fuente(fk, size); fs = fuente("disp_xb", int(size * 0.62))
    asc = f.getmetrics()[0]; asc_s = fs.getmetrics()[0]
    for t, e in _partes(txt):
        if e:
            d.text((x, y + asc - asc_s - size * 0.12), t, font=fs, fill=fill); x += fs.getlength(t)
        else:
            d.text((x, y), t, font=f, fill=fill); x += f.getlength(t)


def placa_firma(frase=None, serif=True):
    """placa negra: frase (serif) + ROCCÉ LIFE en mayúsculas chicas espaciadas."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    y = 820
    if frase:
        fk = "serif" if serif else "disp_xb"
        size = 104
        while ancho_mixto(frase, fk, size) > 900: size -= 2
        escribir_mixto(d, (W - ancho_mixto(frase, fk, size)) / 2, y - 60, frase, fk, size)
        y += 90
    fr = fuente("inter_sb", 34)
    s = "ROCCÉ LIFE"
    tw = fr.getlength(s) + 10 * (len(s) - 1)
    x = (W - tw) / 2
    for ch in s:
        d.text((x, y + 30), ch, font=fr, fill=CEL + (255,)); x += fr.getlength(ch) + 10
    return img
