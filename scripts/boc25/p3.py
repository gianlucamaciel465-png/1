#!/usr/bin/env python3
"""BOC-25 · P3 «Adiviná quién» (Merentiel) · receta v01 (25/11/2026) · Pedro.

Guion: guiones/P3_G1_fede.md con la aprobación de Roma (guiones/P3_G1_roma.md, manda sobre el guion).
Mecánica de casa de apuestas: apuesta abierta desde c0 («¿Lo sacás antes de verle la cara?» + contador en c54), pistas
▲▼ cada 1–1,8 s, la cara recién en c717 (78 % de la pieza) y la pregunta de hoy abierta hasta las 21:00.

Decisiones tomadas mirando la fuente (detalle en 06_pedro_P3.md):
- Los tiempos de fuente del guion salen de las tiras del inventario, que están corridas un paso (el filtro fps toma el
  último cuadro de cada tramo): tira + 7,195 s en EMO, + 6,873 s en GOL, + 2,434 s en MAN. Acá van los tiempos reales.
- R12 va con video real: 827156 (MAN) es la jugada del travesaño en cámara lenta; se lee «M. MERENTIEL 16» en el que
  remata de chilena (9,87–9,93 s) y la pelota pega en el travesaño en 11,07–11,10 s y vuelve. Es la misma jugada que
  447124. Impacto en c489.
- R13 sale: MAN no es un mano a mano atajado, es el travesaño (va en R12). Todo lo que sigue se corre −45 cuadros.
- R8: recorte que sigue el hueco entre el nombre y el «16» cuadro a cuadro (el nombre queda arriba, fuera del cuadro).
- EMO tiene cortes internos (14,01 / 18,25 / 24,92 / 36,60 / 43,44 / 49,48 / 52,22 s): ningún plano cruza uno.
  R16 dura 81 cuadros (el plano de la fuente dura 2,74 s) y R15 pasa a 45 (lectura de «La misma copa que se le había
  escapado.»); el total y el cuadro de la cara no cambian.
- CARA: banda superior de EMO (y 0–880, ancho completo, escala 1:1). Las nenas escoltas empiezan más abajo (y ≥ 900 en
  los tramos usados), así que quedan fuera del recorte; la marca de agua queda en su lugar. Debajo, la banda se funde a
  oscuro y ahí va el texto.
- Marca de agua de CONMEBOL: donde la imagen se desenfoca, oscurece o reencuadra (CARA, R8, R9–R10, R16) se vuelve a
  poner encima la marca de la propia fuente (alfa estimada con 48 cuadros de 16 tramos de EMO) en su lugar y tamaño de pantalla.
- Sonido: EMO, MAN y GOL traen música (espectro con líneas armónicas sostenidas); 447124 trae voz. No se usa ninguno.
  Tribuna real solo de 774354 («El gol del Ruso desde la tribuna», 1-0, sin relator) + efectos sintetizados.

Etapas: python3 p3.py marca | planos | plano R8 R16 … | audio | master | control | todo
"""
import sys, json, subprocess, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from scipy import ndimage as ndi
sys.path.insert(0, '/home/user/1/scripts/bocsud')
import comun as C
V = C.V

T = Path('/home/user/1/TRABAJO/boc25/p3')
FPS, W, H = 30, 1080, 1920
NF = 918
EMO, GOL, MAN, TRIB = '281237', '589650', '827156', '774354'
UNO = 'setpts=N/(30*TB)'          # EMO es 29,97: cada cuadro de la fuente es un cuadro de la pieza (0,1 % más rápido)
PIEZA = Path('/mnt/project-files/piezas/BOC-25_octavos_hoy/')
VERSION = 'v02'                  # v02 (Roma, 25/11): R11 y el final de R16 más desenfocados; tiempos, textos y audio iguales
SALIDA = PIEZA / f'ROCCE_BOC25_P3_ADIVINA_QUIEN_{VERSION}.mp4'
LOCAL = T / f'ROCCE_BOC25_P3_ADIVINA_QUIEN_{VERSION}.mp4'

# planos: (nombre, primer cuadro, cuadros)
PLANOS = [('R1', 0, 84), ('R2', 84, 30), ('R3', 114, 30), ('R4', 144, 30), ('R5', 174, 30), ('R6', 204, 54),
          ('R7', 258, 45), ('R8', 303, 27), ('R9', 330, 36), ('R10', 366, 45), ('R11', 411, 54), ('R12', 465, 54),
          ('R14', 519, 72), ('R15', 591, 45), ('R16', 636, 81), ('R17', 717, 60), ('R18', 777, 78), ('R19', 855, 63)]
C0 = {n: a for n, a, _ in PLANOS}
CARA_C = 717                      # primer cuadro con la cara (σ8 → 0 en 717–723)
X_GOL = 558                       # la pelota aparece adentro del arco (GOL 11,733 s)
IMPACTO = 489                     # la pelota pega en el travesaño (MAN 11,10 s)
CTA_C = 874                       # el CTA entra con el primer cuadro nítido del estampado (3375, cuadro 22 = 0,733 s; antes, barrido de la mano)

# ---------------- marca de agua de CONMEBOL (EMO) ----------------
WX0, WY0, WX1, WY1 = 20, 200, 320, 450          # región de la marca en EMO (px de la fuente 1080x1920)
LX0, LY0, LX1, LY1 = 62, 240, 268, 408          # el logo


def marca():
    """alfa de la marca de agua (blanca) por píxel: fondo estimado por convolución normalizada alrededor del logo,
    mediana sobre 48 cuadros de 16 tramos (siete planos) de EMO."""
    src = C.clip(EMO); als = []
    for t0 in (0.5, 2.5, 4.5, 6.5, 8.5, 10.5, 12.5, 15.0, 17.0, 19.5, 21.5, 23.5, 38.0, 40.0, 45.0, 50.0):
        for a in C.leer_video(src, t0, 0.5, W, H)[::5]:
            reg = a[WY0:WY1, WX0:WX1].astype(np.float64)
            M = np.ones(reg.shape[:2]); M[LY0 - WY0:LY1 - WY0, LX0 - WX0:LX1 - WX0] = 0
            bg = np.stack([ndi.gaussian_filter(reg[..., c] * M, 22) / np.maximum(ndi.gaussian_filter(M, 22), 1e-3)
                           for c in range(3)], -1)
            als.append(((reg - bg) / np.maximum(255 - bg, 8)).mean(-1))
    A = np.median(np.array(als), 0)
    A[A < 0.04] = 0                                # el piso de ruido no se aplica (si no, queda un rectángulo)
    A = np.clip(A, 0, 1)
    np.save(T / 'marca_alfa.npy', A)
    Image.fromarray((A / A.max() * 255).astype(np.uint8)).save(T / 'marca_alfa.png')
    print('marca: alfa máx', round(float(A.max()), 3), 'cuadros', len(als))


_MARCA = None


def poner_marca(a, peso=1.0):
    """a: arreglo HxWx3 float/uint8 (1080x1920). Vuelve a poner la marca de agua en su lugar de pantalla."""
    global _MARCA
    if _MARCA is None:
        _MARCA = np.load(T / 'marca_alfa.npy')[..., None]
    o = a.astype(np.float32)
    reg = o[WY0:WY1, WX0:WX1]
    al = _MARCA * peso
    o[WY0:WY1, WX0:WX1] = reg * (1 - al) + 255 * al
    return o


# ---------------- apoyos de imagen ----------------
def _grad(y0, y1, y2, y3, k):
    """máscara vertical 0→k (y0..y1), k (y1..y2), k→0 (y2..y3)"""
    y = np.arange(H, dtype=np.float32)
    g = np.clip((y - y0) / max(y1 - y0, 1), 0, 1) * np.clip((y3 - y) / max(y3 - y2, 1), 0, 1)
    g = g * g * (3 - 2 * g)
    return (1 - k * g)[:, None, None]


SOMBRA_TXT = _grad(860, 1000, 1440, 1600, 0.55)      # detrás del bloque de texto (y 1000–1440)
SOMBRA_CTA = _grad(-1, 0, 260, 820, 0.62)            # tercio superior del cierre
SOMBRA_TOP = _grad(-1, 0, 0, 70, 0.55)               # borde superior de R8


def oscurecer(a, m):
    return a.astype(np.float32) * m


BANDA = 880                                          # alto de la banda CARA
OSCURO = np.array([8, 10, 20], np.float32)
_rng = np.random.default_rng(25)
_GRANO = _rng.normal(0, 1.1, (H - BANDA + 60, W, 1)).astype(np.float32)


def cara(fr, sigma):
    """banda superior de EMO (y 0–880, escala 1:1) desenfocada σ, y abajo un fundido a oscuro desde su propio borde."""
    banda = Image.fromarray(fr[:BANDA])
    if sigma > 0.05:
        banda = banda.filter(ImageFilter.GaussianBlur(sigma))       # solo la banda: no arrastra nada de abajo
    b = np.asarray(banda, np.float32)
    o = np.empty((H, W, 3), np.float32)
    o[:BANDA] = b
    fila = ndi.gaussian_filter1d(b[BANDA - 24:BANDA].mean(0), 40, axis=0)    # color del borde, suavizado
    y = np.arange(BANDA - 60, H, dtype=np.float32)
    f = np.exp(-np.maximum(y - (BANDA - 60), 0) / 150)[:, None, None]
    relleno = fila[None] * f + OSCURO * (1 - f) + _GRANO[:len(y)]
    al = np.clip((y - (BANDA - 60)) / 60, 0, 1)[:, None, None]
    al = al * al * (3 - 2 * al)
    o[BANDA - 60:] = np.concatenate([b[BANDA - 60:], np.zeros((H - BANDA, W, 3), np.float32)]) * (1 - al) + relleno * al
    return o


def escribir(salida, cuadros_fn, n):
    enc = C.encoder(salida)
    for k in range(n):
        enc.stdin.write(np.asarray(cuadros_fn(k)).round().clip(0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()


def plano_cara(nombre, t0, n, sigma_fn):
    fr = C.leer_video(C.clip(EMO), t0, n / FPS, W, H, vf=UNO)
    def f(k):
        s = sigma_fn(k)
        o = cara(fr[k], s)
        if s > 0.05:
            o = poner_marca(o, min(1.0, s / 4))
        return o
    escribir(T / f'{nombre}.mp4', f, n)
    return dict(plano=nombre, clip=EMO, desde=t0, cuadros=n, salida=str(T / f'{nombre}.mp4'), sigma=[sigma_fn(0), sigma_fn(n - 1)])


# ---------------- R8: el «16» sin el nombre ----------------
def medir_r8(fr):
    """por cuadro: borde inferior del nombre, borde superior del «16» y centro x del número"""
    r = []
    for a in fr:
        A = a.astype(np.int16)
        bl = (A[..., 0] > 185) & (A[..., 1] > 185) & (A[..., 2] > 185)
        bl[:600] = False; bl[1400:] = False
        lab, nl = ndi.label(bl)
        objs = ndi.find_objects(lab)
        dig = [o for o in objs if 150 < (o[0].stop - o[0].start) < 330 and (o[1].stop - o[1].start) > 25
               and o[1].start > 330 and o[1].stop < 1060]
        dt = min(o[0].start for o in dig); dx0 = min(o[1].start for o in dig); dx1 = max(o[1].stop for o in dig)
        nom = [o for o in objs if 12 < (o[0].stop - o[0].start) < 80 and o[0].stop <= dt + 2
               and o[1].stop > dx0 - 80 and o[1].start < dx1 + 80 and dt - o[0].stop < 140]
        nb = max(o[0].stop for o in nom) if nom else dt - 30
        r.append((nb, dt, (dx0 + dx1) / 2))
    return np.array(r, np.float64)


def borde_jugador(a, y0=880, y1=1300):
    """x del borde izquierdo del jugador (camiseta azul o short amarillo saturados, tramo de ≥ 40 px) en el cuadro ya recortado"""
    A = a[y0:y1].astype(np.float32) / 255
    mx, mn = A.max(-1), A.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-3)
    R, G, B = A[..., 0], A[..., 1], A[..., 2]
    col = (sat > 0.45) & (mx > 0.30) & (((B > R + 0.15) & (B > G)) | ((R > B + 0.25) & (G > B + 0.15) & (G > 0.55 * R)))
    xs = []
    for fila in col[::4]:
        run = ndi.uniform_filter1d(fila.astype(np.float32), 40, mode='constant') > 0.9
        i = np.argmax(run)
        if run[i]: xs.append(i - 20)
    return float(np.percentile(xs, 30)) if xs else 200.0


def fondo_r8(o, borde, y0=700, y1=1500, margen=28, sigma=16, pluma=24):
    """desenfoca el fondo a la izquierda del jugador (fotógrafo / personal identificable detrás)"""
    xb = int(max(borde - margen, 0))
    if xb < 8: return o
    x1 = min(xb + 3 * pluma, W)
    reg = o[max(y0 - 3 * pluma, 0):min(y1 + 3 * pluma, H), :x1]
    bl = np.stack([ndi.gaussian_filter(reg[..., c], sigma) for c in range(3)], -1)
    yy, xx = np.mgrid[max(y0 - 3 * pluma, 0):min(y1 + 3 * pluma, H), :x1]
    m = np.clip((xb - xx) / pluma + 0.5, 0, 1) * np.clip((yy - y0) / pluma + 0.5, 0, 1) * np.clip((y1 - yy) / pluma + 0.5, 0, 1)
    o = o.copy()
    o[max(y0 - 3 * pluma, 0):min(y1 + 3 * pluma, H), :x1] = reg * (1 - m[..., None]) + bl * m[..., None]
    return o


def plano_r8(t0=37.50, n=27):
    fr = C.leer_video(C.clip(EMO), t0, n / FPS, W, H, vf=UNO)
    med = medir_r8(fr)
    nb = ndi.median_filter(med[:, 0], 3, mode='nearest'); dt = ndi.median_filter(med[:, 1], 3, mode='nearest')
    cx = ndi.uniform_filter1d(ndi.median_filter(med[:, 2], 3, mode='nearest'), 5, mode='nearest')
    top = np.maximum(nb + 0.55 * (dt - nb), nb + 6)            # dentro del hueco, más cerca del número
    top = np.minimum(top, dt - 3)
    bordes = np.empty(n)
    for k in range(n):
        h = H - top[k]; w = h * W / H; x0 = min(max(cx[k] - w / 2, 0), W - w)
        bordes[k] = borde_jugador(np.asarray(Image.fromarray(fr[k]).resize((W, H), Image.LANCZOS, box=(x0, top[k], x0 + w, H))))
    bordes = ndi.uniform_filter1d(ndi.median_filter(bordes, 5, mode='nearest'), 5, mode='nearest')
    def f(k):
        h = H - top[k]; w = h * W / H
        x0 = min(max(cx[k] - w / 2, 0), W - w)
        im = Image.fromarray(fr[k]).resize((W, H), Image.LANCZOS, box=(x0, top[k], x0 + w, H))
        o = fondo_r8(np.asarray(im, np.float32), bordes[k])
        o = oscurecer(o, SOMBRA_TOP * SOMBRA_TXT)
        return poner_marca(o)
    escribir(T / 'R8.mp4', f, n)
    json.dump(dict(nombre_abajo=med[:, 0].tolist(), numero_arriba=med[:, 1].tolist(), centro=med[:, 2].tolist(),
                   borde_recorte=top.tolist()), open(T / 'r8_medidas.json', 'w'), indent=0)
    json.dump(bordes.tolist(), open(T / 'r8_borde_jugador.json', 'w'))
    return dict(plano='R8', clip=EMO, desde=t0, cuadros=n, salida=str(T / 'R8.mp4'),
                margen_min_nombre=float((top - nb).min()), margen_min_numero=float((dt - top).min()))


# ---------------- R9–R10: tribuna + gráfico ARCO (penal de 2024) ----------------
def arco(o, bola=None):
    """travesaño de 8 px (x 170–910, y 640), palos hasta y 920, con un halo suave; bola (x, y, diámetro)"""
    S = 2
    capa = Image.new('L', (W * S, H * S), 0); d = ImageDraw.Draw(capa)
    d.rectangle([170 * S, 636 * S, 910 * S, 644 * S], fill=255)
    d.rectangle([170 * S, 636 * S, 178 * S, 920 * S], fill=255); d.rectangle([902 * S, 636 * S, 910 * S, 920 * S], fill=255)
    if bola:
        x, y, r = bola[0] * S, bola[1] * S, bola[2] * S / 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    capa = capa.resize((W, H), Image.LANCZOS)
    m = np.asarray(capa, np.float32)[..., None] / 255
    halo = np.asarray(capa.filter(ImageFilter.GaussianBlur(14)), np.float32)[..., None] / 255
    o = o + (255 - o) * np.clip(halo * 0.55, 0, 1)
    return o * (1 - m) + 250 * m


def plano_r9_r10():
    n9, n10 = 36, 45
    fr = C.leer_video(C.clip(EMO), 28.20, (n9 + n10) / FPS, W, H, vf=UNO)
    def fondo(a):
        im = Image.fromarray(a).resize((W, H), Image.LANCZOS, box=(720, 0, 1024, 540))   # solo tribuna: los jugadores entran por debajo de y 560
        return np.asarray(im.filter(ImageFilter.GaussianBlur(30)), np.float32) * 0.35
    def bola9(k):
        u = k / (n9 - 1); e = 1 - (1 - u) ** 2.2
        return (610 - 60 * e, 1560 - 800 * e, 52 - 18 * e)
    def bola10(k):
        if k > 13: return None
        u = k / 13
        return (550 - 20 * u, 760 - 840 * u ** 1.1, 34 - 10 * u)
    escribir(T / 'R9.mp4', lambda k: poner_marca(arco(fondo(fr[k]), bola9(k))), n9)
    escribir(T / 'R10.mp4', lambda k: poner_marca(arco(fondo(fr[n9 + k]), bola10(k))), n10)
    return [dict(plano='R9', clip=EMO, desde=28.20, cuadros=n9, salida=str(T / 'R9.mp4'), grafico='ARCO'),
            dict(plano='R10', clip=EMO, desde=28.20 + n9 / 29.97, cuadros=n10, salida=str(T / 'R10.mp4'), grafico='ARCO')]


# ---------------- R14–R15: desenfoque que sigue al jugador de Boca (nombre, sponsor del pecho y cara) ----------------
def seguir_boca(fr, ymin=500):
    """centro x y borde superior del short amarillo del único jugador de Boca en cuadro, por cuadro"""
    r = []
    for a in fr:
        A = a.astype(np.int16); R, G, B = A[..., 0], A[..., 1], A[..., 2]
        m = (R > 170) & (G > 110) & (B < 110) & (R - G > 25) & (R - G < 120)
        m[:ymin] = False
        lab, nl = ndi.label(ndi.binary_dilation(m, iterations=3))
        s = ndi.sum(m, lab, range(1, nl + 1)); i = int(np.argmax(s)) + 1
        ys, xs = np.nonzero((lab == i) & m)
        y0 = ys.min(); sel = ys < y0 + 22
        r.append((xs[sel].mean(), y0))
    r = np.array(r, np.float64)
    return np.stack([ndi.uniform_filter1d(ndi.median_filter(r[:, c], 5, mode='nearest'), 5, mode='nearest')
                     for c in range(2)], 1)


def desenfoque_eliptico(o, cx, cy, rx, ry, sigma, pluma=10):
    x0, x1 = int(max(cx - rx - 4 * pluma, 0)), int(min(cx + rx + 4 * pluma, W))
    y0, y1 = int(max(cy - ry - 4 * pluma, 0)), int(min(cy + ry + 4 * pluma, H))
    reg = o[y0:y1, x0:x1]
    bl = np.stack([ndi.gaussian_filter(reg[..., c], sigma) for c in range(3)], -1)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    m = np.clip((1.0 - d) * max(rx, ry) / pluma + 0.5, 0, 1)[..., None]
    o[y0:y1, x0:x1] = reg * (1 - m) + bl * m
    return o


def plano_gol(nombre, t0, n, alto_torso, ancho, sombra_desde=None):
    """GOL a cuadro completo; desenfoque elíptico sobre torso y cabeza del jugador de Boca (sigue el short)."""
    fr = C.leer_video(C.clip(GOL), t0, n / FPS, W, H)
    tr = seguir_boca(fr)
    def f(k):
        o = fr[k].astype(np.float32)
        cx, ys = tr[k]
        o = desenfoque_eliptico(o, cx, ys - alto_torso * 0.55, ancho, alto_torso * 0.62, 6.0, pluma=8)
        if sombra_desde is None or k >= sombra_desde:
            o = oscurecer(o, SOMBRA_TXT)
        return o
    escribir(T / f'{nombre}.mp4', f, n)
    json.dump(tr.tolist(), open(T / f'{nombre}_seguimiento.json', 'w'))
    return dict(plano=nombre, clip=GOL, desde=t0, cuadros=n, salida=str(T / f'{nombre}.mp4'), desenfoque='torso y cabeza')


# ---------------- R16: σ8 en todo el cuadro ----------------
def sigma_r16(k, sigma=8.0):
    """v01: σ8 fijo. v02: σ8 hasta k50 y sube a σ16 en k58 (la cara de perfil asoma desde k≈58–60), fijo hasta el final"""
    if VERSION == 'v01' or k <= 50:
        return sigma
    u = min((k - 50) / 8, 1.0)
    return sigma + (16.0 - sigma) * u * u * (3 - 2 * u)


def plano_r16(t0=49.50, n=81, sigma=8.0):
    fr = C.leer_video(C.clip(EMO), t0, n / FPS, W, H, vf=UNO)
    def f(k):
        o = np.asarray(Image.fromarray(fr[k]).filter(ImageFilter.GaussianBlur(sigma_r16(k, sigma))), np.float32)
        return poner_marca(oscurecer(o, SOMBRA_TXT))
    escribir(T / 'R16.mp4', f, n)
    return dict(plano='R16', clip=EMO, desde=t0, cuadros=n, salida=str(T / 'R16.mp4'),
                sigma=[sigma_r16(k, sigma) for k in (0, 50, 54, 58, n - 1)])


# ---------------- R12: el travesaño real (MAN, cámara lenta) ----------------
def plano_r12(t0=10.30, n=54):
    r = C.real(MAN, t0, n, T / 'R12.mp4', por_cuadro=lambda k, f: Image.fromarray(
        oscurecer(np.asarray(f), SOMBRA_TXT).round().clip(0, 255).astype(np.uint8)))
    r['plano'] = 'R12'
    return r


# ---------------- R19: IMG_3375 ----------------
def tela_3375(a):
    """RGB medio de la tela justo debajo del estampado (la zona se ubica por las letras oscuras dentro de la remera)"""
    L = a.astype(np.float32).mean(-1)
    claro = ndi.binary_fill_holes(ndi.binary_closing(L > 150, iterations=4))
    letras = claro & (L < 100)
    ys, xs = np.nonzero(letras)
    x0, x1 = np.percentile(xs, [3, 97]); y1 = np.percentile(ys, 97)
    caja = a[int(y1 + 40):int(y1 + 300), int(x0):int(x1)].reshape(-1, 3).astype(np.float32)
    Lc = caja.mean(1); sat = caja.max(1) - caja.min(1)
    return caja[(Lc > 150) & (sat < 60)].mean(0)


def balance_3375(fr):
    """ganancias por cuadro (luz lineal) que llevan la tela a gris neutro; la toma deriva a crema desde 1,2 s"""
    lin = lambda v: (np.asarray(v, np.float64) / 255) ** 2.2
    g = []
    for a in fr:
        m = lin(tela_3375(a)); y = m @ np.array([0.2126, 0.7152, 0.0722])
        g.append(y / m)
    g = np.array(g)
    return np.stack([ndi.uniform_filter1d(ndi.median_filter(g[:, c], 5, mode='nearest'), 9, mode='nearest') for c in range(3)], 1)


def aplicar_balance(a, g):
    lin = (a.astype(np.float32) / 255) ** 2.2 * g.astype(np.float32)
    return np.clip(lin, 0, 1) ** (1 / 2.2) * 255


def plano_r19(n=63):
    p, a0 = C.lib('IMG_3375')
    fr = C.leer_video(p, 0.0, 66 / FPS, W, H)
    g = balance_3375(fr[3:3 + n])
    escribir(T / 'R19.mp4', lambda k: oscurecer(aplicar_balance(fr[3 + k], g[k]), SOMBRA_CTA), n)
    json.dump(g.tolist(), open(T / 'r19_balance.json', 'w'))
    return dict(plano='R19', toma='IMG_3375', desde=0.10, hasta=0.10 + n / FPS, cuadros=n, salida=str(T / 'R19.mp4'),
                biblioteca=str(p), balance='tela a gris neutro por cuadro (r19_balance.json)')


RECETA = {
    'R1': lambda: plano_cara('R1', 19.50, 84, lambda k: 48),
    'R2': lambda: plano_cara('R2', 8.20, 30, lambda k: 42),
    'R3': lambda: plano_cara('R3', 9.20, 30, lambda k: 37),
    'R4': lambda: plano_cara('R4', 10.20, 30, lambda k: 32),
    'R5': lambda: plano_cara('R5', 11.20, 30, lambda k: 27),
    'R6': lambda: plano_cara('R6', 12.20, 54, lambda k: 22),
    'R7': lambda: plano_cara('R7', 14.05, 45, lambda k: 18),
    'R8': lambda: plano_r8(),
    'R9': lambda: plano_r9_r10(),                 # devuelve R9 y R10
    'R11': lambda: plano_cara('R11', 16.40, 54, lambda k: 13 if VERSION == 'v01' else 22),   # v02: con σ18 todavía se
                                                                                                # leen cejas y ojos a 1080
    'R12': lambda: plano_r12(),
    'R14': lambda: plano_gol('R14', 11.733 - 39 / FPS, 72, alto_torso=170, ancho=80),     # la cabeza va adelante del short
    'R15': lambda: plano_gol('R15', 27.10, 45, alto_torso=205, ancho=64),
    'R16': lambda: plano_r16(),
    'R17': lambda: plano_cara('R17', 20.30 - 1 / 29.97, 60, lambda k: max(0.0, 8.0 * (1 - k / 6))),
    # R18 como el guion: «cabeza baja antes de jugar» (tira 0:00,000 + 7,195 s). El pelo de la nena escolta queda
    # 8–24 px debajo del borde de la banda (y 880), revisado cada 4 cuadros; es el tramo que R2–R4 muestran desenfocado.
    'R18': lambda: plano_cara('R18', 7.195, 78, lambda k: 0.0),
    'R19': lambda: plano_r19(),
}


def planos(solo=None):
    """renderiza todos los planos (o solo los nombrados, reutilizando planos.json para el resto) y los une"""
    previo = {p['plano']: p for p in json.load(open(T / 'planos.json'))} if solo and (T / 'planos.json').exists() else {}
    hechos = {}
    for nom, fn in RECETA.items():
        if solo and nom not in solo and nom in previo:
            hechos[nom] = previo[nom]
            if nom == 'R9': hechos['R10'] = previo['R10']
            continue
        r = fn()
        for d in (r if isinstance(r, list) else [r]):
            hechos[d['plano']] = d
    P = [hechos[nom] for nom, a, n in PLANOS]
    for p, (nom, a, n) in zip(P, PLANOS):
        assert p['cuadros'] == n, (nom, p['cuadros'], n)
        p['c0'] = a
    n = C.armar(P, T / 'p3_video.mp4')
    assert n == NF, n
    json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('cuadros', n)


# ---------------- textos ----------------
CEL = '&H00DEB27E'               # celeste de marca (#7EB2DE)
# Tamaños: en libass el cuerpo de la letra sale a 0,822 del Fontsize (medido en P5). Fontsize = cuerpo ÷ 0,822, con los
# cuerpos que Roma aprobó en P5 v02: pistas 76, apuesta 82, CTA 84 (la v01 de P5, con 59–66, no se aprobó por chica).
V.ESTILOS.update({
    'P3_main': ('Inter Display ExtraBold', 92, '&H00FFFFFF', '&H66000000', '&H88000000', 0, 3.5, 2, 1, 7, 0),
    'P3_head': ('Inter Display Bold', 52, CEL, '&H66000000', '&H88000000', 0, 2.5, 2, 1, 7, 0),
    'P3_src': ('Inter Display Medium', 34, '&H40FFFFFF', '&H77000000', '&H88000000', 0, 2, 1, 1, 7, 0),
    'P3_cita': ('Inter Display Bold', 80, '&H00FFFFFF', '&H66000000', '&H88000000', 0, 3, 2, 1, 7, 0),
    'P3_nombre': ('Inter Display ExtraBold', 130, '&H00FFFFFF', '&H66000000', '&H88000000', 0, 3.5, 3, 1, 7, 0),
    'P3_q': ('Inter Display SemiBold', 100, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 26, 0, 3, 8, 0),
    'P3_cta': ('Inter Display ExtraBold', 102, '&H00FFFFFF', '&H66000000', '&H88000000', 0, 3.5, 2, 1, 8, 0),
    'P3_cnt_lbl': ('Inter Display Bold', 40, CEL, '&H00000000', '&H00000000', 0, 0, 0, 1, 8, 0),
    'P3_cnt': ('Inter Display ExtraBold', 150, '&H00FFFFFF', '&H00000000', '&H00000000', 0, 0, 0, 1, 8, 0),
    'P3_placa': ('Inter Display Bold', 10, '&H00000000', '&H00000000', '&H00000000', 0, 0, 0, 1, 7, 0),
})
CUERPO = 0.822
FUENTES = {'P3_main': ('InterDisplay-ExtraBold.otf', 92), 'P3_head': ('InterDisplay-Bold.otf', 52),
           'P3_src': ('InterDisplay-Medium.otf', 34), 'P3_cita': ('InterDisplay-Bold.otf', 80),
           'P3_nombre': ('InterDisplay-ExtraBold.otf', 130), 'P3_cta': ('InterDisplay-ExtraBold.otf', 102),
           'P3_q': ('InterDisplay-SemiBold.otf', 100)}
INTERVALO = {'P3_main': 96, 'P3_head': 58, 'P3_src': 40, 'P3_cita': 86, 'P3_nombre': 134, 'P3_cta': 106, 'P3_q': 130}
LIMITE_TXT = 1480                # el bloque termina antes de la franja de abajo de TikTok (y ≥ 1500)
X_TXT, Y_TXT, ANCHO_TXT = 70, 1000, 870      # borde derecho ≤ 940: la columna de íconos de TikTok empieza en x ≈ 950
ANCHO_EST = {'P3_nombre': 620}               # el nombre de la revelación va en dos renglones grandes
_F = {}


def renglones(txt, estilo, ancho=ANCHO_TXT):
    """corta txt en el mínimo de renglones que entran en `ancho` px (métrica real de la fuente) y, entre los cortes
    posibles con ese número de renglones, elige el más parejo (sin viudas tipo «club.»)"""
    from itertools import combinations
    fn, fs = FUENTES[estilo]
    if estilo not in _F:
        _F[estilo] = ImageFont.truetype(f'/usr/share/fonts/opentype/inter/{fn}', fs * CUERPO)   # tamaño real en libass
    f = _F[estilo]; ws = txt.split(' ')
    for n in range(1, len(ws) + 1):
        mejor = None
        for cortes in combinations(range(1, len(ws)), n - 1):
            idx = (0,) + cortes + (len(ws),)
            rs = [' '.join(ws[idx[i]:idx[i + 1]]) for i in range(n)]
            m = max(f.getlength(r) for r in rs)
            if m <= ancho and (mejor is None or m < mejor[0]):
                mejor = (m, rs)
        if mejor:
            return mejor[1]
    return ws


def tx(c):
    # medio cuadro antes: con c/FPS exacto en centésimas (c múltiplo de 3) libass lo mostraba un cuadro tarde
    return max((c - 0.5) / FPS, 0.0)


def flecha(txt):
    """▲/▼ en celeste dentro de un renglón blanco"""
    for s in ('▲', '▼'):
        txt = txt.replace(s, '{\\c' + CEL + '&}' + s + '{\\c&H00FFFFFF&}')
    return txt


EMPUJE = '\\fscx104\\fscy104\\t(0,200,\\fscx100\\fscy100)'


def alto_bloque(elems):
    return sum(INTERVALO[est] * len(renglones(txt, est, ANCHO_EST.get(est, ANCHO_TXT))) + (10 if est != 'P3_src' else 0)
               for est, txt, c in elems)


def bloque(X, fin, elems, y=Y_TXT, x=X_TXT):
    """elems: [(estilo, texto, cuadro_de_entrada)] apilados desde y; todos salen en `fin` (primer cuadro del plano
    siguiente). Si el bloque entero no entra antes de LIMITE_TXT, sube lo justo (los renglones que entran después no
    se mueven). Devuelve el y final."""
    y = min(y, LIMITE_TXT - alto_bloque(elems))
    for est, txt, c in elems:
        rs = renglones(txt, est, ANCHO_EST.get(est, ANCHO_TXT))
        cuerpo = '\\N'.join(flecha(r) if est != 'P3_head' else r for r in rs)
        X.append(dict(t0=tx(c), t1=tx(fin), txt=cuerpo, estilo=est, x=x, y=y, extra=EMPUJE))
        y += INTERVALO[est] * len(rs) + (10 if est != 'P3_src' else 0)
    return y


def contador(X):
    """placa oscura + «PISTAS» + número (8→0); cada cambio entra con un golpe de escala"""
    tramos = [(54, 114, '8'), (114, 144, '7'), (144, 174, '6'), (174, 204, '5'), (204, 258, '4'), (258, 303, '3'),
              (303, 465, '2'), (465, CARA_C, '1'), (CARA_C, CARA_C + 15, '0')]
    placa = ('{\\p1\\bord0\\shad0\\1a&H6A&\\c&H000000&}m 22 0 l 148 0 b 160 0 170 10 170 22 l 170 198 b 170 210 160 '
             '220 148 220 l 22 220 b 10 220 0 210 0 198 l 0 22 b 0 10 10 0 22 0{\\p0}')
    X.append(dict(t0=tx(54), t1=tx(CARA_C + 15), txt=placa, estilo='P3_placa', x=850, y=232, blur=False, capa=0))
    X.append(dict(t0=tx(54), t1=tx(CARA_C + 15), txt='PISTAS', estilo='P3_cnt_lbl', x=935, y=250, blur=False, capa=1,
                  extra='\\fsp3'))
    for a, b, n in tramos:
        X.append(dict(t0=tx(a), t1=tx(b), txt=n, estilo='P3_cnt', x=935, y=280, blur=False, capa=1,
                      extra='\\fscx125\\fscy125\\t(0,120,\\fscx100\\fscy100)'))


def textos():
    X = []
    fin = {n: a + k for n, a, k in PLANOS}
    # R1 · APUESTA
    bloque(X, fin['R1'], [('P3_main', 'No pudo debutar en su club.', 0), ('P3_main', 'El sábado lloró en una final.', 24)])
    X.append(dict(t0=tx(54), t1=tx(fin['R1']), txt='\\N'.join(renglones('¿Lo sacás antes de verle la cara?', 'P3_q', 860)),
                  estilo='P3_q', x=540, y=520, extra='\\fscx112\\fscy112\\t(0,120,\\fscx100\\fscy100)'))
    contador(X)
    fuente18 = 'ESPN, 18/11/2026'
    bloque(X, fin['R2'], [('P3_head', 'Paysandú, 1996.', 84), ('P3_main', 'Inferiores de Peñarol.', 84), ('P3_src', fuente18, 84)])
    bloque(X, fin['R3'], [('P3_head', '2017', 114), ('P3_main', 'Tanque Sisley: 7 goles en 20.', 114), ('P3_src', fuente18, 114)])
    bloque(X, fin['R4'], [('P3_head', '2017–2019', 144), ('P3_main', 'España: Lorca y Valencia Mestalla.', 144), ('P3_src', fuente18, 144)])
    bloque(X, fin['R5'], [('P3_head', '2019', 174), ('P3_main', 'Godoy Cruz: 6 goles en 29.', 174), ('P3_src', fuente18, 174)])
    bloque(X, fin['R6'], [('P3_head', '▲ 2020 · Defensa y Justicia', 204), ('P3_main', 'Campeón de la Sudamericana.', 204),
                          ('P3_main', 'Entró de suplente en la final.', 225), ('P3_src', fuente18, 204)])
    bloque(X, fin['R7'], [('P3_head', '▼ Enero 2023 · Palmeiras', 258), ('P3_main', '3 minutos oficiales.', 258), ('P3_src', fuente18, 258)])
    bloque(X, fin['R8'], [('P3_main', '▲ Ese año: Boca.', 303)])
    bloque(X, fin['R9'], [('P3_head', '▼ Agosto 2024 · Sudamericana, octavos', 330),
                          ('P3_main', 'Quinto penal. Hasta ahí, todos gol.', 330), ('P3_src', 'ESPN, 22/08/2024', 330)])
    bloque(X, fin['R10'], [('P3_main', 'Por encima del travesaño.', 366), ('P3_main', 'Cruzeiro 5-4. Boca, afuera.', 387),
                           ('P3_src', 'ESPN, 22/08/2024', 366)])
    bloque(X, fin['R11'], [('P3_main', '▲ En el hotel, los hinchas le cantaron.', 411), ('P3_main', 'Para bancarlo.', 411),
                           ('P3_src', 'ESPN, 23/08/2024', 411)])
    bloque(X, fin['R12'], [('P3_head', '▼ Sábado 21/11 · Final de la Sudamericana', 465), ('P3_main', 'Minuto 3: travesaño.', IMPACTO),
                           ('P3_main', 'Otra vez, tan cerca.', 498), ('P3_src', 'Montevideo Portal, 21/11', 465)])
    bloque(X, fin['R14'], [('P3_main', '▲ Segundo tiempo: 2-0.', X_GOL)])
    bloque(X, fin['R15'], [('P3_main', '▲ La misma copa que se le había escapado.', 591)])
    bloque(X, fin['R16'], [('P3_cita', '«Sabía que me iba a quedar otra oportunidad. Lo busqué hasta lo último.»', 636),
                           ('P3_src', 'Los Primeros TV, 22/11', 636)])
    bloque(X, fin['R17'], [('P3_nombre', 'Miguel Merentiel.', 726), ('P3_main', '¿Lo sacaste?', 744)])
    bloque(X, fin['R18'], [('P3_head', 'Hoy · 21:00 · Octavos del Clausura', 777),
                           ('P3_main', 'En el once probable de Los Andes, no figura.', 777),
                           ('P3_main', '¿Le toca otra?', 816), ('P3_src', 'Los Andes, 24/11', 777)])
    cta = '\\N'.join(renglones('Mandáselo a quien viene pegando en el travesaño.', 'P3_cta', 900))
    # halo oscuro suave solo detrás de las letras (la remera blanca queda sin oscurecer debajo de y 260)
    X.append(dict(t0=tx(CTA_C), t1=tx(NF), txt=cta, estilo='P3_cta', x=540, y=240, blur=False, capa=0,
                  extra=EMPUJE + '\\1a&HFF&\\3c&H000000&\\3a&H78&\\bord18\\shad0\\blur14'))
    X.append(dict(t0=tx(CTA_C), t1=tx(NF), txt=cta, estilo='P3_cta', x=540, y=240, capa=1, extra=EMPUJE))
    return X


# ---------------- sonido ----------------
def t(c):
    return c / FPS


def rampa(m, pista, t0, t1, g0, g1):
    i0, i1 = int(t0 * C.SR), int(t1 * C.SR)
    g = np.ones(m.N); g[i0:i1] = C.db(np.linspace(g0, g1, i1 - i0)); g[i1:] = C.db(g1)
    m.pistas[pista][i0:] *= g[i0:, None]


def audio():
    m = C.MezclaB(NF / FPS)
    trib = C.clip(TRIB)
    # pulso del gancho (latido) desde el primer cuadro; en R7 se hace más lento («en contra»)
    c = 1
    while c < 258:
        m.latido(t(c), 0.55); c += 18
    for c in (262, 286):
        m.latido(t(c), 0.42)
    m.pad(0.0, [40, 47, 52], t(366), 0.045, corte=650)                    # tensión grave por debajo
    # tics del contador / cortes de pista
    for c, f in ((54, 2400), (84, 2400), (114, 3200), (144, 2400), (174, 2600)):
        m.toque(t(c), 0.24, f); m.log(t(c), f'tic {f} Hz')
    m.subida(t(204), t(257), 0.10); m.toque(t(204), 0.24, 2600); m.log(t(204), 'tic + subida')
    m.toque(t(258), 0.26, 1300); m.bombo(t(258), 0.35, f0=70, f1=38, dec=0.5); m.log(t(258), 'tic grave, el pulso baja')
    m.bombo(t(303), 0.5, f0=95, f1=48, dec=0.35); m.log(t(303), 'golpe suave (R8)')
    # R9: pulso rápido sin tics, el penal
    c = 330
    while c < 365:
        m.latido(t(c), 0.5); c += 10
    m.barrido(t(368), 0.32, 0.25)                                          # la pelota pasa por encima (c366–371)
    m.pad(t(372), [28], t(398) - t(372), 0.012, corte=200, a=0.05, r=0.1)  # «sala»: casi silencio
    # la tribuna entra antes del corte (c399) y sigue bajo en R11 (774354: hinchada sostenida, sin relator)
    m.real(trib, 7.0, t(399), t(465), -4, ini=0.6, fin=0.15, etiqueta='tribuna real 774354 (aguante)')
    m.toque(t(464), 0.22, 2400); m.log(t(464), 'tic')
    # R12: el pulso acelera hasta el travesaño
    c, paso = 465.0, 9.0
    while c < IMPACTO - 2:
        m.latido(t(c), 0.5); c += paso; paso = max(3.5, paso * 0.8)
    m.subida(t(465), t(IMPACTO), 0.13)
    m.clang(t(IMPACTO), 0.6)
    m.pad(t(492), [38, 45], t(518) - t(492), 0.03, corte=500)
    # R14: tensión hasta la pelota adentro, estallido de la tribuna real en X (pico de 774354 en 3,0 s)
    m.subida(t(519), t(X_GOL), 0.12)
    c = 520
    while c < X_GOL - 2:
        m.latido(t(c), 0.45); c += 12
    src0 = 3.0 - (X_GOL - 519) / FPS
    m.real(trib, src0, t(519), t(717), -3, ini=0.08, fin=0.9, etiqueta='tribuna real 774354 (estallido)')
    rampa(m, 'amb', t(591), t(717), 0, -16)                                 # R15 baja, R16 sale
    m.impacto(t(X_GOL), 0.55)
    m.pad(t(636), [45, 52, 56], t(716) - t(636), 0.035, corte=900)
    # R17: casi silencio + golpe grave en la cara, subida suave
    m.golpe_sordo(t(CARA_C), 0.6)
    m.subida(t(CARA_C + 2), t(776), 0.06)
    m.pad(t(CARA_C), [45, 49, 52], t(776) - t(CARA_C), 0.03, corte=1200)
    # R18: vuelve el pulso del gancho
    c = 778
    while c < 852:
        m.latido(t(c), 0.5); c += 18
    m.pad(t(777), [40, 47, 52], t(854) - t(777), 0.04, corte=650)
    m.toque(t(816), 0.22, 2400); m.log(t(816), 'tic (¿Le toca otra?)')
    # R19: eco del travesaño, −18 dB respecto del de R12
    m.clang(t(CTA_C), 0.6 * 10 ** (-18 / 20))
    m.pad(t(855), [45, 52, 57], t(NF) - t(855), 0.035, corte=1000)
    for p in m.pistas:
        m.fundido(p, t(NF - 12), t(NF))
    (T / 'audio').mkdir(exist_ok=True)
    r = m.exportar(str(T / 'audio' / 'p3.wav'), lufs=-14)
    print('audio', r)


def master():
    a = V.ass(textos(), T / 'p3.ass')
    V.master(T / 'p3_video.mp4', T / 'audio' / 'p3.wav', LOCAL, ass_path=a)
    print(LOCAL)


# ---------------- control del máster ----------------
CTRL = PIEZA / 'control'
ZONAS_TT = [(900, 760, 1080, 1620), (0, 1600, 1080, 1920), (0, 0, 1080, 200)]   # columna derecha, pie y pestañas de TikTok


def _sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def _cuadro(video, n):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-vf', f"select='eq(n\\,{n})'", '-frames:v', '1',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return Image.fromarray(np.frombuffer(raw, np.uint8).reshape(H, W, 3))


def _guardar(im, nombre, local):
    im.save(local / nombre)


def control(video=LOCAL):
    loc = T / ('control' if VERSION == 'v01' else f'control_{VERSION}'); loc.mkdir(exist_ok=True)
    P = 'P3_' if VERSION == 'v01' else f'P3_{VERSION}_'
    # hoja cada 0,5 s con tiempo y cuadro de la pieza
    _sh(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vf',
         "select='not(mod(n\\,15))',scale=216:-2,drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-Bold.otf:"
         "text='%{pts\\:hms} c%{eif\\:n*15\\:d}':x=4:y=4:fontsize=15:fontcolor=yellow:box=1:boxcolor=black@0.65,"
         "tile=8x8:padding=2", '-frames:v', '1', '-fps_mode', 'vfr', str(loc / f'{P}hoja_0.5s.png')])
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 22)
    # cada corte: último cuadro del plano anterior | primer cuadro del plano nuevo
    cortes = [a for _, a, _ in PLANOS[1:]]
    filas = []
    for c in cortes:
        a, b = _cuadro(video, c - 1).resize((360, 640)), _cuadro(video, c).resize((360, 640))
        f = Image.new('RGB', (730, 676), (20, 20, 20)); f.paste(a, (0, 36)); f.paste(b, (370, 36))
        nom = [n for n, x, _ in PLANOS if x == c][0]
        ImageDraw.Draw(f).text((6, 6), f'c{c - 1} | c{c} ({nom}, {c / FPS:.3f} s)', font=fnt, fill=(255, 220, 0))
        filas.append(f)
    for i in range(0, len(filas), 6):
        g = Image.new('RGB', (730 * 3, 676 * 2), (0, 0, 0))
        for j, f in enumerate(filas[i:i + 6]):
            g.paste(f, ((j % 3) * 730, (j // 3) * 676))
        g.save(loc / f'{P}cortes_{i // 6 + 1}.png')
    # cara, CTA y lectura a 360 px; zonas de la interfaz de TikTok
    for n, nom in ((CARA_C - 1, 'antes_cara'), (CARA_C, 'cara'), (CARA_C + 6, 'cara_nitida'),
                   (CTA_C, 'cta'), (NF - 13, 'cta_final'), (304, 'R8_dorsal'), (437, 'R11'), (700, 'R16'), (716, 'R16_fin')):
        nom = P + nom
        _cuadro(video, n).save(loc / f'{nom}_c{n}.png')
    for n in (60, 120, 320, 489, 600, 760, 840, CTA_C + 10):
        im = _cuadro(video, n)
        z = im.copy(); d = ImageDraw.Draw(z, 'RGBA')
        for r in ZONAS_TT:
            d.rectangle(r, outline=(255, 40, 40, 255), width=6, fill=(255, 40, 40, 40))
        g = Image.new('RGB', (360 * 2 + 10, 640), (0, 0, 0))
        g.paste(im.resize((360, 640), Image.LANCZOS), (0, 0)); g.paste(z.resize((360, 640), Image.LANCZOS), (370, 0))
        g.save(loc / f'{P}360_zonas_c{n}.png')
    print('control', loc)


if __name__ == '__main__':
    T.mkdir(parents=True, exist_ok=True)
    et = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    if et in ('marca', 'todo'): marca()
    if et in ('planos', 'todo'): planos()
    if et == 'plano': planos(set(sys.argv[2:]))
    if et in ('audio', 'todo'): audio()
    if et in ('master', 'todo'): master()
    if et in ('control', 'todo'): control()
