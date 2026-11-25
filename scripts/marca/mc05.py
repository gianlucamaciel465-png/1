#!/usr/bin/env python3
"""MARCA · MC-05 «NADIE TE VA A DAR PERMISO.» · receta del máster v02 (Pedro C, 25/11/2026).
v02 = dictamen de Roma 02_roma_dictamen_master_v01.md: plano 10 con rampa (ROCCÉ completo ≥ 0,8 s al final),
«Queda una acción.» y dato de c12 en caja negra SemiBold 50. La receta exacta de v01 quedó en mc05_v01.py.

Guion: piezas/MARCA_comunidad/04_fede_guiones_G1.md §MC-05 (G1 v1) + 06_roma_aprobacion_G1.md (condiciones)
+ 05_especificacion_comun.md. Usa sin modificarlos scripts/fmt/video.py (color, plano, unir, cuadro), fmt03.py (hojas
de fuente, md5 de flujos, sonoridad, cortes, hoja de contacto), fmt04_util.py (plano_zoom con retoque por cuadro),
sonido.py (Mezcla) y scripts/marca/comun.py (caja, placa, pegar, pop, fijo, fuera_de_zona).
Lo que falta y vive acá: candado de color (etiqueta + 7 casillas, sacudón, latido, desbloqueo), placa serif, rasterizado
de la interfaz por cuadro (una sola capa PNG por cuadro del máster: entra exacta, sin ventanas de tiempo), neutralización
de la Blanca solo en neutros claros, máster con capa (mismos códecs que video.master) y el control.

Etapas (python mc05.py <etapa>, con el python de TRABAJO/venv; todo con nice):
  hojas → planos → capas → audio → master → control → entregar
Intermedios en TRABAJO/marca/MC-05/. Sin servicios externos ni créditos. Sin commit (lo hace Roma).
"""
import json, math, subprocess, sys, hashlib, shutil, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/marca')
import video as V          # noqa: E402
import fmt03 as U          # noqa: E402
import fmt04_util as F4    # noqa: E402
import comun as C          # noqa: E402

R = Path('/home/user/1')
T = R / 'TRABAJO/marca/MC-05'
HJ, PL, CAPA, A, MAS, EVID = T / 'hojas', T / 'planos', T / 'capa', T / 'audio', T / 'master', T / 'evidencia_v02'
EXP = R / 'EXPORTACIONES'
PIEZA = Path('/mnt/project-files/piezas/MARCA_comunidad/MC-05_permiso')
W, H, FPS, SR = 1080, 1920, 30, 48000
NF = 408
DUR = NF / FPS                       # 13,600 s
NOMBRES = {'completa': 'ROCCE_MC05_NADIE_TE_VA_A_DAR_PERMISO_v02.mp4',
           'sinmusica': 'ROCCE_MC05_NADIE_TE_VA_A_DAR_PERMISO_SINMUSICA_v02.mp4'}
SERIF = '/home/user/1/scripts/fuentes/InstrumentSerif-Regular.ttf'
FONT = U.FONT


def nice(cmd):
    return ['nice', '-n', '10'] + [str(c) for c in cmd]


def jdump(obj, f):
    Path(f).parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(f, 'w'), ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))


# =====================================================================================================
# hojas cada 0,1 s de los tramos dudosos (cuadro y ms de la FUENTE impresos, misma cadena de color)
# =====================================================================================================
HOJAS = [('IMG_3453', 0, 139, 2), ('IMG_7996', 0, 84, 3), ('IMG_7824', 0, 290, 3), ('IMG_8004', 27, 152, 3),
         ('IMG_7885', 0, 26, 3), ('IMG_7884', 0, 26, 3), ('IMG_7895', 0, 68, 3), ('IMG_4531', 0, 62, 3)]


def etapa_hojas():
    HJ.mkdir(parents=True, exist_ok=True)
    for toma, n0, n1, c in HOJAS:
        f = HJ / f'{toma}_c{n0}-{n1}_cada{c}.jpg'
        if not f.exists():
            U.hoja_src(toma, n0, n1, f, cada=c, ancho=180, cols=12)
        print(f, flush=True)
    f = HJ / 'IMG_3453_c30-62_cada2_grande.jpg'
    if not f.exists():
        U.hoja_src('IMG_3453', 30, 62, f, cada=2, ancho=300, cols=6)


# =====================================================================================================
# planos
# =====================================================================================================
BN = "hue=s=0,eq=contrast=1.10,lutyuv=y='clip(val,16,235)':u=128:v=128"
# giro (plano 9): saturación 0 hasta 0,8 s del plano (c240) y de 0 a 1 entre c240 y c263 (k = 24…47 del plano)
GIRO = ("hue=s='clip((t-0.8)*30/23,0,1)',eq=contrast='1.10-0.10*clip((t-0.8)*30/23,0,1)':eval=frame,"
        "lutyuv=y='clip(val,16,235)'")
# (id, toma, desde, hasta, modo, función) · segundos de la fuente
PLANOS = [
    ('P01', 'IMG_7824', 8.00, 9.60, 'bn', 'APUESTA'),
    ('P02', 'IMG_7996', 0.30, 1.10, 'bn', 'INTENTO 1 · agarra'),
    ('P03', 'IMG_7996', 64 / 30, 88 / 30, 'bn', 'INTENTO 2 · tira'),    # desvío: guion 1,90–2,70 → c64–c87 (2,133–2,933)
    ('P04', 'IMG_7884', 0.00, 0.80, 'bn', 'INTENTO 3 · foto'),
    ('P05', 'IMG_7895', 0.00, 0.80, 'bn', 'INTENTO 4 · ola'),
    ('P06', 'IMG_7885', 0.00, 0.80, 'bn', 'INTENTO 5 · puesta'),
    ('P07', 'IMG_4531', 0.40, 1.20, 'bn', 'INTENTO 6 · muestra'),
    ('P08', 'IMG_4531', 1.20, 2.00, 'bn', 'GRAN PREGUNTA'),
    ('P09', 'IMG_3453', 0.00, 1.60, 'giro', 'GIRO'),
    # v02: 1,000–3,667 con rampa (≈1,48× hasta src c95; 0,5× con mezcla compensada desde src c96, ROCCÉ completo)
    ('P10', 'IMG_8004', 1.00, 110 / 30, 'rampa', 'giro cobrado · prueba de ropa'),
    ('P11', 'IMG_7824', 2.00, 4.40, 'color', 'CTA'),
]
CORTES = [48, 72, 96, 120, 144, 168, 192, 216, 264, 336]


# ---- neutralización de la Blanca (solo neutros claros), medida sobre la tela ----
def _rgb_frame(toma, t, w=540, h=960):
    vf = V.color(toma) + f',scale={w}:{h}:flags=area:in_color_matrix=bt709:in_range=tv,format=rgb24'
    r = U.run(nice(['ffmpeg', '-v', 'error', '-ss', f'{t:.4f}', '-i', V._src(toma), '-frames:v', '1', '-vf', vf,
                    '-f', 'rawvideo', '-']))
    return np.frombuffer(r, np.uint8).reshape(h, w, 3).astype(np.float64)


def ycc(rgb):
    """RGB de 0–255 (sin rango limitado) -> Y, Cb, Cr BT.709 de rango limitado."""
    r, g, b = rgb
    yf = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return 16 + 219 * yf / 255, 128 + 224 * (b - yf) / (1.8556 * 255), 128 + 224 * (r - yf) / (1.5748 * 255)


def medir_blanca(toma, ts, reg):
    """media RGB de la tela blanca (L > 150, sat < 0,15) dentro de reg=(y0,y1,x0,x1) en fracciones del cuadro."""
    acc = []
    for t in ts:
        a = _rgb_frame(toma, t); h, w, _ = a.shape
        y0, y1, x0, x1 = int(reg[0] * h), int(reg[1] * h), int(reg[2] * w), int(reg[3] * w)
        a = a[y0:y1, x0:x1]
        L = a.mean(2); sat = (a.max(2) - a.min(2)) / (a.max(2) + 1)
        m = (L > 150) & (sat < 0.15)
        acc.append([a[..., i][m].mean() for i in range(3)] + [int(m.sum())])
    acc = np.array(acc)
    rgb = acc[:, :3].mean(0)
    return dict(rgb=[round(float(v), 1) for v in rgb], b_r=round(float(rgb[2] - rgb[0]), 1),
                g_r=round(float(rgb[1] - rgb[0]), 1), pixeles=[int(v) for v in acc[:, 3]])


def delta_neutra(rgb, br=8.0, gr=1.5):
    """corrimiento de croma (dCb, dCr) que lleva el blanco medido a B−R = br, G−R = gr con la misma luma."""
    r, g, b = rgb
    yf = 0.2126 * r + 0.7152 * g + 0.0722 * b
    rt = yf - 0.7152 * gr - 0.0722 * br
    _, cb_m, cr_m = ycc(rgb)
    _, cb_t, cr_t = ycc((rt, rt + gr, rt + br))
    return (cb_m - cb_t, cr_m - cr_t), (cb_m, cr_m)


def _ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def neutralizar(delta, centro, y0=140.0, y1=180.0, d0=5.0, d1=11.0):
    """por_cuadro para fmt04_util.plano_zoom: corre Cb/Cr solo en lo claro y cercano al croma del blanco medido
    (el celeste, la piel, la arena y las rocas quedan fuera del peso)."""
    dcb, dcr = delta; cbm, crm = centro

    def f(k, o):
        Y = o[0].astype(np.float32); Cb = o[1].astype(np.float32); Cr = o[2].astype(np.float32)
        w = _ss((Y - y0) / (y1 - y0)) * (1 - _ss((np.hypot(Cb - cbm, Cr - crm) - d0) / (d1 - d0)))
        o = o.copy()
        o[1] = np.clip(np.round(Cb - w * dcb), 0, 255).astype(np.uint8)
        o[2] = np.clip(np.round(Cr - w * dcr), 0, 255).astype(np.uint8)
        return o
    return f


_TRAMA = {}


def _trama(h, w, canal):
    """tramado fijo en [0, 1) por bloques de 2×2 (para que sobreviva al 4:2:0), semilla fija: el mismo en todos los cuadros."""
    if (h, w) not in _TRAMA:
        rng = np.random.default_rng(20261125)
        _TRAMA[(h, w)] = [np.repeat(np.repeat(rng.random(((h + 1) // 2, (w + 1) // 2), dtype=np.float32), 2, 0), 2, 1)[:h, :w]
                          for _ in range(2)]
    return _TRAMA[(h, w)][canal]


def neutralizar_fino(delta, centro, y0=140.0, y1=180.0, d0=5.0, d1=11.0):
    """como neutralizar, pero redondea con un tramado fijo: la media corre exactamente w·delta. Para correcciones que
    cambian por cuadro (v02): con el redondeo simple, cuando delta cruza x,5 toda la tela con peso 1 salta 1 nivel de
    croma de un cuadro al siguiente (medido en H3 v02 primera pasada: 3 saltos en 7884 y 5 en 4627, uno de ida y vuelta).
    Con delta = 0 no cambia ningún píxel (piso de x + t con t < 1)."""
    dcb, dcr = delta; cbm, crm = centro

    def f(k, o):
        Y = o[0].astype(np.float32); Cb = o[1].astype(np.float32); Cr = o[2].astype(np.float32)
        w = _ss((Y - y0) / (y1 - y0)) * (1 - _ss((np.hypot(Cb - cbm, Cr - crm) - d0) / (d1 - d0)))
        o = o.copy()
        o[1] = np.clip(np.floor(Cb - w * dcb + _trama(*Cb.shape, 0)), 0, 255).astype(np.uint8)
        o[2] = np.clip(np.floor(Cr - w * dcr + _trama(*Cr.shape, 1)), 0, 255).astype(np.uint8)
        return o
    return f


# regiones de tela blanca para medir (fracciones del cuadro natural) y tiempos dentro del tramo
REG_BLANCA = {'IMG_8004': (0.60, 0.95, 0.10, 0.90), 'IMG_7894': (0.40, 0.55, 0.00, 0.40),
              'IMG_7895': (0.43, 0.50, 0.38, 0.50), 'IMG_7896': (0.53, 0.62, 0.20, 0.40),
              'IMG_7887': (0.42, 0.55, 0.35, 0.55)}


def plano_neutro(toma, desde, hasta, salida, ts_med, caja=None, z=1.0, cx=None, cy=None, extra_pad=0):
    nw, nh = V.TOMAS[toma]['nat']
    med = medir_blanca(toma, ts_med, REG_BLANCA[toma])
    delta, centro = delta_neutra(med['rgb'])
    caja = caja or (0, 0, nw, nh)
    cx = caja[0] + caja[2] / 2 if cx is None else cx
    cy = caja[1] + caja[3] / 2 if cy is None else cy
    p = F4.plano_zoom(toma, desde, hasta, salida, caja, z, z, cx, cy, por_cuadro=neutralizar(delta, centro))
    p.pop('ventanas', None)
    p.update(neutra=dict(medido=med, delta_cb_cr=[round(d, 2) for d in delta], centro_cb_cr=[round(c, 2) for c in centro]))
    return p


def _fase(a, b):
    """desplazamiento (dy, dx) del contenido de a hacia b por correlación de fase con ventana de Hann y ajuste parabólico."""
    wy = np.hanning(a.shape[0])[:, None]; wx = np.hanning(a.shape[1])[None, :]
    A = np.fft.fft2((a - a.mean()) * wy * wx); B = np.fft.fft2((b - b.mean()) * wy * wx)
    R = B * np.conj(A); R /= np.abs(R) + 1e-9
    c = np.real(np.fft.ifft2(R))
    iy, ix = np.unravel_index(np.argmax(c), c.shape)
    def par(m1, c0, p1):
        den = m1 - 2 * c0 + p1
        return 0.0 if den == 0 else 0.5 * (m1 - p1) / den
    h, w = c.shape
    dy = iy + par(c[(iy - 1) % h, ix], c[iy, ix], c[(iy + 1) % h, ix])
    dx = ix + par(c[iy, (ix - 1) % w], c[iy, ix], c[iy, (ix + 1) % w])
    if dy > h / 2: dy -= h
    if dx > w / 2: dx -= w
    return float(dy), float(dx)


def _mover(o, dy, dx):
    """corre el contenido de un cuadro yuv444 (3, H, W) en (dy, dx) px con spline cúbica; fuera de cuadro = NaN."""
    from scipy.ndimage import shift
    return np.stack([shift(o[c].astype(np.float32), (dy, dx), order=3, mode='constant', cval=np.nan) for c in range(3)])


def intermedio_compensado(o0, o1, reg=(880, 1500, 0, 1080)):
    """cuadro a mitad de camino entre o0 y o1: cada uno se corre la mitad del desplazamiento medido SOBRE LA REMERA
    (las letras quedan una sobre otra: sin fantasma) y se promedian. Donde a uno le falta borde, se usa el otro. El fondo
    desenfocado (médano) tiene otra paralaje y puede quedar levemente doble: no tiene detalle que lo delate."""
    y0, y1, x0, x1 = reg
    dy, dx = _fase(o0[0, y0:y1, x0:x1].astype(np.float32), o1[0, y0:y1, x0:x1].astype(np.float32))
    a = _mover(o0, dy / 2, dx / 2); b = _mover(o1, -dy / 2, -dx / 2)
    m = np.where(np.isnan(a), b, np.where(np.isnan(b), a, 0.5 * (a + b)))
    m = np.where(np.isnan(m), 0.5 * (o0.astype(np.float32) + o1.astype(np.float32)), m)
    # control: con el desplazamiento medido, o0 corrido entero tiene que caer sobre o1 en la remera
    al = _mover(o0, dy, dx)[0, y0:y1, x0:x1]; ref = o1[0, y0:y1, x0:x1].astype(np.float32)
    ok = ~np.isnan(al)
    err = dict(dy=round(dy, 2), dx=round(dx, 2), mad_alineado=round(float(np.abs(al[ok] - ref[ok]).mean()), 2),
               mad_sin_alinear=round(float(np.abs(o0[0, y0:y1, x0:x1].astype(np.float32) - ref).mean()), 2))
    return np.clip(np.round(m), 0, 255).astype(np.uint8), err


def tope_blanca(reg, tope=7.4, alfa=0.3, y0=140.0, y1=180.0, d0=5.0, d1=11.0, registro=None):
    """por_cuadro que va DESPUÉS de neutralizar (P10 v02): mide el blanco de la tela en cada cuadro (yuv444, región reg,
    L > 150, sat < 0,15) y, solo si B−R pasa de tope, suma el corrimiento que lo baja a tope con el mismo G−R (dividido
    por el peso medio, suavizado con media móvil alfa) con neutralizar_fino (sin saltos de 1 nivel). Por debajo del
    tope no toca nada: el comienzo de P10 queda como v01.
    Motivo medido: con la rampa, el final de P10 usa cuadros de 8004 más fríos (src c96–c109, B−R +8,6 a +9,4 en el
    control del máster) que los de v01 (máx. +8,6). Tope 7,4: en 8004 el control sobre el MP4 da hasta +0,23 más."""
    est = {}

    def f(k, o):
        h_, w_ = o.shape[1:]
        r0, r1, c0, c1 = int(reg[0] * h_), int(reg[1] * h_), int(reg[2] * w_), int(reg[3] * w_)
        Y = o[0, r0:r1:2, c0:c1:2].astype(np.float32); Cb = o[1, r0:r1:2, c0:c1:2].astype(np.float32)
        Cr = o[2, r0:r1:2, c0:c1:2].astype(np.float32)
        Rr = 1.164 * (Y - 16) + 1.793 * (Cr - 128); G = 1.164 * (Y - 16) - 0.213 * (Cb - 128) - 0.533 * (Cr - 128)
        B = 1.164 * (Y - 16) + 2.112 * (Cb - 128)
        rgb = np.clip(np.stack([Rr, G, B], -1), 0, 255)
        L = rgb.mean(-1); sat = (rgb.max(-1) - rgb.min(-1)) / (rgb.max(-1) + 1)
        m = (L > 150) & (sat < 0.15)
        v = np.zeros(4)
        if m.sum() >= 500:
            med = rgb[m].mean(0); br = float(med[2] - med[0]); gr = float(med[1] - med[0])
            (dcb, dcr), (cbm, crm) = delta_neutra(med, min(br, tope), gr)
            wt = _ss((Y - y0) / (y1 - y0)) * (1 - _ss((np.hypot(Cb - cbm, Cr - crm) - d0) / (d1 - d0)))
            mw = float(max(wt[m].mean(), 0.5))
            v = np.array([dcb / mw, dcr / mw, cbm, crm])
            est['v'] = v if 'v' not in est else np.array([*((1 - alfa) * est['v'][:2] + alfa * v[:2]), cbm, crm])
            if registro is not None:
                registro.append(dict(k=k, b_r_antes=round(br, 2), g_r=round(gr, 2), peso_medio=round(mw, 3),
                                     extra=[round(float(x), 3) for x in est['v'][:2]]))
        if 'v' not in est or abs(est['v'][0]) + abs(est['v'][1]) < 0.01:
            return o
        dcb, dcr, cbm, crm = est['v']
        return neutralizar_fino((dcb, dcr), (cbm, crm), y0, y1, d0, d1)(k, o)
    return f


def plano_neutro_rampa(toma, salida, ts_med, f0=30, n_a=45, a_fin=65, n_b=27, tope=None):
    """P10 v02 (dictamen de Roma §1): mismo largo (72 c). Tramo A: n_a cuadros que recorren los cuadros de la fuente
    f0 … f0+a_fin a ≈ a_fin/(n_a−1) × (cuadros reales, sin mezcla). Tramo B: desde f0+a_fin+1 (ROCCÉ entra completo,
    medido: src c96 = 3,200 s, R a 12 px del borde) a 0,5×: cuadros pares = cuadros reales, impares = intermedio
    compensado por movimiento. Último cuadro de la fuente: f0+a_fin+1+(n_b−1)/2 (src c109 = 3,633 s; É a 18 px del borde).
    Misma neutralización de la Blanca que v01 (medida en ts_med)."""
    nw, nh = V.TOMAS[toma]['nat']
    med = medir_blanca(toma, ts_med, REG_BLANCA[toma]); delta, centro = delta_neutra(med['rgb'])
    neut = neutralizar(delta, centro)
    reg_tope = []
    tp = tope_blanca(REG_BLANCA[toma], tope, registro=reg_tope) if tope is not None else (lambda k, o: o)
    b0 = a_fin + 1
    ult = b0 + (n_b - 1) / 2
    n_src = int(math.ceil(ult)) + 1
    src = []
    for k, fr in enumerate(F4._decode_yuv444(V._src(toma), f0 / FPS - 0.0005, n_src / FPS, V.color(toma) + f',fps={FPS}', nw, nh, n_src)):
        src.append(tp(k, neut(k, F4._resize_planos(fr, (0, 0, nw, nh), W, H))))
    if len(src) != n_src:
        raise RuntimeError(f'rampa: {len(src)} cuadros de la fuente, esperaba {n_src}')
    mapa, errores = [], []
    enc = F4._encoder(salida)
    for k in range(n_a):
        i = int(math.floor(a_fin * k / (n_a - 1) + 0.5))
        enc.stdin.write(src[i].tobytes()); mapa.append(f0 + i)
    for j in range(n_b):
        pos = b0 + j / 2
        if j % 2 == 0:
            enc.stdin.write(src[int(pos)].tobytes()); mapa.append(f0 + int(pos))
        else:
            i0 = int(math.floor(pos)); m, e = intermedio_compensado(src[i0], src[i0 + 1])
            enc.stdin.write(m.tobytes()); mapa.append(f0 + pos); errores.append(dict(e, entre=[f0 + i0, f0 + i0 + 1]))
    enc.stdin.close(); enc.wait()
    return dict(toma=toma, desde=f0 / FPS, hasta=(f0 + n_src) / FPS, cuadros=n_a + n_b, salida=str(salida),
                rampa=dict(tramo_a=dict(cuadros=n_a, src=[f0, f0 + a_fin], velocidad=round(a_fin / (n_a - 1), 3), mezcla=False),
                           tramo_b=dict(cuadros=n_b, src=[f0 + b0, f0 + ult], velocidad=0.5, mezcla='compensada por movimiento'),
                           cuadro_fuente_por_cuadro=mapa, intermedios=errores),
                neutra=dict(medido=med, delta_cb_cr=[round(d, 2) for d in delta], centro_cb_cr=[round(c, 2) for c in centro],
                            tope_b_r=tope, tope_por_cuadro_fuente=[dict(r, src=f0 + r['k']) for r in reg_tope]))


# ---- Negra carbón en 3453 (después de la corrección de TOMAS): corrimiento de croma por franja de luminancia ----
# Motivo medido: con TOMAS sola, la tela oscura del macro a color queda RGB ≈ (29, 15, 11) → marrón. Método de
# scripts/vir/vir01_v02.py (corregir_negro): mediana de (Cb−128, Cr−128) de la tela (L < 100) por franja de L y resta con
# peso 1 hasta L 100 que se apaga en L 140: la luma no cambia, el relieve (L ≥ 170) y los dedos claros quedan iguales.
FRANJAS_NEGRA = [0, 35, 60, 100]


def _yuv444_cuadros(toma, ts):
    nw, nh = V.TOMAS[toma]['nat']
    out = []
    for t in ts:
        r = U.run(nice(['ffmpeg', '-v', 'error', '-ss', f'{t:.4f}', '-i', V._src(toma), '-frames:v', '1', '-vf',
                        V.color(toma) + ',format=yuv444p', '-f', 'rawvideo', '-pix_fmt', 'yuv444p', '-']))
        out.append(np.frombuffer(r, np.uint8).reshape(3, nh, nw).astype(np.float32))
    return out


def medir_negra(toma, ts):
    acc = {k: [] for k in range(len(FRANJAS_NEGRA) - 1)}
    for Y, Cb, Cr in _yuv444_cuadros(toma, ts):
        L = (Y - 16) / 219 * 255
        for k in range(len(FRANJAS_NEGRA) - 1):
            m = (L >= FRANJAS_NEGRA[k]) & (L < FRANJAS_NEGRA[k + 1])
            acc[k].append(np.stack([Cb[m] - 128, Cr[m] - 128, L[m]], 1))
    out = []
    for k, v in acc.items():
        q = np.concatenate(v, 0)
        if len(q) < 3000:
            continue
        out.append(dict(L_centro=round(float(np.median(q[:, 2])), 1), d_cb=round(float(np.median(q[:, 0])), 2),
                        d_cr=round(float(np.median(q[:, 1])), 2), n=int(len(q))))
    return out


def corregir_negra(fr, LN0=100.0, LN1=140.0):
    xs = np.array([f['L_centro'] for f in fr]); cbs = np.array([f['d_cb'] for f in fr]); crs = np.array([f['d_cr'] for f in fr])

    def f(k, o):
        Y = o[0].astype(np.float32); L = (Y - 16) / 219 * 255
        w = 1 - _ss((L - LN0) / (LN1 - LN0))
        o = o.copy()
        o[1] = np.clip(np.round(o[1] - w * np.interp(L, xs, cbs)), 0, 255).astype(np.uint8)
        o[2] = np.clip(np.round(o[2] - w * np.interp(L, xs, crs)), 0, 255).astype(np.uint8)
        return o
    return f


def corregir_negra_adapt(alfa=0.3, LN0=100.0, LN1=140.0, log=None):
    """variante por cuadro (historias, 3453 a color entero): la mediana de croma por franja se mide en cada cuadro
    (sobre una grilla de 1 de cada 4 píxeles) y se suaviza con media móvil exponencial (alfa) para que no titile. La
    luz de la toma cambia: con una sola medición el comienzo quedaba tibio (R−B +9 en el cuadro 10)."""
    est = {}

    def f(k, o):
        Y = o[0].astype(np.float32); L = (Y - 16) / 219 * 255
        Ls, cbs_, crs_ = L[::4, ::4], o[1][::4, ::4].astype(np.float32) - 128, o[2][::4, ::4].astype(np.float32) - 128
        xs, cb, cr = [], [], []
        for i in range(len(FRANJAS_NEGRA) - 1):
            m = (Ls >= FRANJAS_NEGRA[i]) & (Ls < FRANJAS_NEGRA[i + 1])
            if m.sum() < 400:
                continue
            v = np.array([np.median(Ls[m]), np.median(cbs_[m]), np.median(crs_[m])])
            est[i] = v if i not in est else (1 - alfa) * est[i] + alfa * v
        for i in sorted(est):
            xs.append(est[i][0]); cb.append(est[i][1]); cr.append(est[i][2])
        if log is not None:
            log.append(dict(k=k, franjas=[[round(float(a), 1), round(float(b), 2), round(float(c), 2)] for a, b, c in zip(xs, cb, cr)]))
        w = 1 - _ss((L - LN0) / (LN1 - LN0))
        o = o.copy()
        o[1] = np.clip(np.round(o[1] - w * np.interp(L, xs, cb)), 0, 255).astype(np.uint8)
        o[2] = np.clip(np.round(o[2] - w * np.interp(L, xs, cr)), 0, 255).astype(np.uint8)
        return o
    return f


def plano_negra(toma, desde, hasta, salida, ts_med, post=None, pad=0, adapt=False):
    """3453 a color corregido (TOMAS + Negra carbón); con post (B/N, rampa) se aplica después, en una segunda pasada;
    pad = cuadros congelados al final (tpad, clon del último cuadro)."""
    fr = medir_negra(toma, ts_med)
    nw, nh = V.TOMAS[toma]['nat']
    tmp = Path(str(salida).replace('.mp4', '_negra.mp4')) if (post or pad) else Path(salida)
    log = []
    corr = corregir_negra_adapt(log=log) if adapt else corregir_negra(fr)
    p = F4.plano_zoom(toma, desde, hasta, tmp, (0, 0, nw, nh), 1.0, 1.0, nw / 2, nh / 2, por_cuadro=corr)
    p.pop('ventanas', None)
    if post or pad:
        vf = ','.join([x for x in (post, f'tpad=stop_mode=clone:stop={pad}' if pad else None) if x])
        V.sh(nice(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-vf', vf, '-frames:v', str(p['cuadros'] + pad), *V.ENC_INT, salida]))
        p['cuadros'] += pad; p['salida'] = str(salida)
    p.update(negra=dict(franjas=fr, ts_medicion=ts_med, adaptativa=adapt, por_cuadro=log[::10] if adapt else None))
    return p


def tela_oscura(mp4, n, reg=(0.0, 1.0, 0.0, 1.0)):
    a = U.leer(mp4, 540, 960, n0=n, n1=n, vf_pre='scale=in_color_matrix=bt709:in_range=tv')[0].astype(np.float64)
    h, w, _ = a.shape
    a = a[int(reg[0] * h):int(reg[1] * h), int(reg[2] * w):int(reg[3] * w)]
    L = a.mean(2); m = (L < 70) & (L > 8)
    rgb = [a[..., i][m].mean() for i in range(3)]
    return dict(rgb=[round(float(v), 1) for v in rgb], r_menos_b=round(float(rgb[0] - rgb[2]), 1), n=int(m.sum()))


def rgb_plano(mp4, n, reg):
    """media RGB de la tela blanca en el cuadro n de un intermedio 1080x1920 (para comprobar la neutralización)."""
    a = U.leer(mp4, 540, 960, n0=n, n1=n, vf_pre='scale=in_color_matrix=bt709:in_range=tv')[0].astype(np.float64)
    h, w, _ = a.shape
    a = a[int(reg[0] * h):int(reg[1] * h), int(reg[2] * w):int(reg[3] * w)]
    L = a.mean(2); sat = (a.max(2) - a.min(2)) / (a.max(2) + 1)
    m = (L > 150) & (sat < 0.15)
    rgb = [a[..., i][m].mean() for i in range(3)]
    return dict(rgb=[round(float(v), 1) for v in rgb], b_r=round(float(rgb[2] - rgb[0]), 1), g_r=round(float(rgb[1] - rgb[0]), 1))


def etapa_planos():
    PL.mkdir(parents=True, exist_ok=True)
    lista = []
    rehacer = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None      # p. ej. «planos P09»
    for pid, toma, d, h, modo, fn in PLANOS:
        out = PL / f'{pid}_{toma}.mp4'
        js = out.with_suffix('.json')
        if rehacer is not None and pid not in rehacer and js.exists():
            lista.append(json.load(open(js))); print(pid, 'reutilizado', flush=True); continue
        d, h = d - 0.0005, h - 0.0005          # -ss descarta pts < ss: así el primer cuadro es el del segundo pedido
        if modo == 'bn':
            p = V.plano(toma, d, h, out, post=BN)
        elif modo == 'giro':
            p = plano_negra(toma, d, h, out, ts_med=[0.9, 1.2, 1.5], post=GIRO)
            p['control_negra'] = {f'k{k}': tela_oscura(out, k, (0.55, 0.95, 0.0, 1.0)) for k in (47,)}
        elif modo == 'rampa':
            p = plano_neutro_rampa(toma, out, ts_med=[1.5, 2.2, 3.1], tope=7.4)   # misma medición que v01 + tope del final
            p['control_neutra'] = {f'k{k}': rgb_plano(out, k, REG_BLANCA[toma]) for k in (0, 15, 36, 45, 60, 66, 71)}
        elif modo == 'neutra':
            p = plano_neutro(toma, d, h, out, ts_med=[d + 0.5, (d + h) / 2, h - 0.3])
            p['control_neutra'] = {f'k{k}': rgb_plano(out, k, REG_BLANCA[toma]) for k in (15, 36, 66)}
        else:
            p = V.plano(toma, d, h, out)
        p.update(id=pid, modo=modo, funcion=fn)
        jdump(p, js)
        lista.append(p)
        print(pid, toma, d, h, p['cuadros'], p.get('control_neutra', ''), flush=True)
    n = V.unir(lista, T / 'mc05_base.mp4')
    assert n == NF, n
    jdump(lista, T / 'planos.json')
    print('base', n, 'cuadros')


# =====================================================================================================
# interfaz: candado de color + textos, rasterizados por cuadro
# =====================================================================================================
GRIS_PILL = (24, 24, 24, 222)
GRIS_LINEA = (235, 235, 235, 255)
CELESTE = C.CELESTE + (255,)
X_CUADROS = [56, 80, 104, 128, 152, 176]          # ✕ = corte + 8 cuadros (intentos 1–6)
SACUDON = [18, -14, 9, -5, 2]                     # desplazamiento horizontal por cuadro
SACUDONES = [56, 80, 104, 128, 152, 158, 176]     # 152 + 158 = sacudón doble («PONETELA.»)
LATIDOS = [196, 208]                              # «Queda una.»: la etiqueta late dos veces
DESBLOQUEO = 246                                  # «COLOR: ✓» celeste
SALE = (300, 304)                                 # la etiqueta sale (fundido de 4 cuadros desde c300)
# Posiciones (y = borde superior del texto; de la caja en las cajas). Desvíos sobre el guion, medidos en la base:
#  · la etiqueta va arriba (236–320) todo el tramo: en y 420–584 tapaba el bollo de la Blanca en c72–c80 (P03) y el gancho
#    de 2 renglones (244 px) no entra entre 236 y 420; el gancho baja a 348, el dato a 612, «FIRMALA.» a 348 y la serif a 380;
#  · «TIRALA.» a 1400 (izquierda, x ≤ 940): con el tramo real del tiro la remera cae en y ≈ 1050–1345 (c86–c95).
Y_HUD = 236
Y_HOOK, Y_DATO, Y_XL, Y_TIRALA = 348, 612, 640, 1400
Y_FIRMALA, Y_SERIF, Y_CTA, Y_XL2 = 348, 380, 236, 470   # CTA a 236: a 300 la caja rozaba el cuello de la Negra en c395–c407
Y_PONETELA = 1400                                   # a 640 tapaba ROCCÉ de la Blanca tendida detrás (c144–c152)


def candado(d, x, y, s, color, abierto=False, grosor=4):
    """candado dibujado (cuerpo + arco) en un cuadro de s×s con esquina (x, y)."""
    bw, bh = s * 0.78, s * 0.52
    bx, by = x + (s - bw) / 2, y + s - bh
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=s * 0.1, fill=color)
    aw = bw * 0.62; ax = x + (s - aw) / 2
    dy = -s * 0.16 if abierto else 0
    dx = s * 0.22 if abierto else 0
    d.arc([ax + dx, y + dy, ax + aw + dx, y + s * 0.62 + dy], 180, 360, fill=color, width=grosor)
    d.line([ax + dx + grosor / 2 - 0.5, y + s * 0.31 + dy, ax + dx + grosor / 2 - 0.5, by + 2 + (0 if not abierto else dy)],
           fill=color, width=grosor)
    if not abierto:
        d.line([ax + aw - grosor / 2 + 0.5, y + s * 0.31, ax + aw - grosor / 2 + 0.5, by + 2], fill=color, width=grosor)
    # ojo de la cerradura
    d.ellipse([x + s / 2 - s * 0.06, by + bh * 0.32, x + s / 2 + s * 0.06, by + bh * 0.32 + s * 0.12], fill=GRIS_PILL)


def tilde(d, cx, cy, r, color, grosor):
    d.line([cx - r * 0.55, cy + r * 0.02, cx - r * 0.12, cy + r * 0.45, cx + r * 0.6, cy - r * 0.42], fill=color,
           width=grosor, joint='curve')


def cruz(d, cx, cy, r, color, grosor):
    k = r * 0.42
    d.line([cx - k, cy - k, cx + k, cy + k], fill=color, width=grosor)
    d.line([cx - k, cy + k, cx + k, cy - k], fill=color, width=grosor)


def hud(n):
    """etiqueta del candado en el cuadro n (o None). Devuelve (imagen RGBA, x, y)."""
    if n >= SALE[1]:
        return None
    S = 2                                     # dibujo al doble y reducción (bordes suaves)
    fnt = ImageFont.truetype(str(C.F['semibold']), 46 * S)
    desbloq = n >= DESBLOQUEO
    txt = 'COLOR:' if desbloq else 'COLOR: BLOQUEADO'
    padx, alto, ic, gap, rs, gs = 28 * S, 84 * S, 44 * S, 14 * S, 22 * S, 9 * S       # casillas de 44 px (legibles a 360 px)
    w_txt_max = fnt.getlength('COLOR: BLOQUEADO')
    Wp = int(padx * 2 + ic + gap + w_txt_max + 30 * S + 7 * (2 * rs) + 6 * gs)
    im = Image.new('RGBA', (Wp, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, Wp - 1, alto - 1], radius=alto // 2, fill=GRIS_PILL)
    col = CELESTE if desbloq else GRIS_LINEA
    candado(d, padx, (alto - ic) / 2, ic, col, abierto=desbloq, grosor=5 * S)
    asc, desc = fnt.getmetrics()
    xt = padx + ic + gap
    d.text((xt, (alto - (asc + desc)) / 2 + 2 * S), txt, font=fnt, fill=col)
    if desbloq:
        tilde(d, xt + fnt.getlength('COLOR: ') + 22 * S, alto / 2, 24 * S, CELESTE, 7 * S)
    # 7 casillas: 6 intentos + la que queda
    x0 = Wp - padx - 7 * (2 * rs) - 6 * gs
    for i in range(7):
        cx = x0 + rs + i * (2 * rs + gs); cy = alto / 2
        hecha = i < 6 and n >= X_CUADROS[i]
        if i == 6 and desbloq:
            d.ellipse([cx - rs, cy - rs, cx + rs, cy + rs], fill=CELESTE)
            tilde(d, cx, cy, rs * 0.95, GRIS_PILL, 4 * S)
        elif hecha:
            e = 1.0
            k = n - X_CUADROS[i]
            if k < 3:
                e = (1.45, 1.22, 1.08)[k]
            r = rs * e
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GRIS_LINEA)
            cruz(d, cx, cy, r, GRIS_PILL, 4 * S)
        else:
            lat = i == 6 and 192 <= n < DESBLOQUEO
            d.ellipse([cx - rs, cy - rs, cx + rs, cy + rs], outline=GRIS_LINEA, width=(5 if lat else 3) * S)
    im = im.resize((Wp // S, alto // S), Image.LANCZOS)
    # escala (latido / pop del desbloqueo) y sacudón
    e = 1.0
    for c0 in LATIDOS:
        k = n - c0
        if 0 <= k < 6:
            e = max(e, (1.03, 1.06, 1.07, 1.05, 1.03, 1.01)[k])
    k = n - DESBLOQUEO
    if 0 <= k < 3:
        e = (1.06, 1.03, 1.0)[k]          # pop más corto que el de los textos: la etiqueta ya mide 963 px
    dx = 0
    for c0 in SACUDONES:
        k = n - c0
        if 0 <= k < len(SACUDON):
            dx = SACUDON[k]
    if e != 1.0:
        im = im.resize((round(im.width * e), round(im.height * e)), Image.LANCZOS)
    if SALE[0] <= n < SALE[1]:
        a = 1 - (n - SALE[0] + 1) / (SALE[1] - SALE[0] + 1)
        im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    x = round(W / 2 - im.width / 2) + dx
    y = round(Y_HUD + 42 - im.height / 2)
    return im, x, y


def placa_serif(texto, size=88, halo=0.55, interlineado=1.08):
    """como comun.placa pero con Instrument Serif (la fuente que pide el guion para la firma)."""
    fnt = ImageFont.truetype(SERIF, size)
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
    som = txt.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(max(6, size // 7)))
    im = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0))
    im.putalpha(som.point(lambda v: int(v * halo)))
    capa = Image.new('RGBA', (Wc, Hc), (255, 255, 255, 0)); capa.putalpha(txt)
    return Image.alpha_composite(im, capa)


def tope_glifo(im, umbral=200):
    """fila del primer píxel de texto (alfa alta, sin el halo) de una placa: para que `y` sea el borde del texto."""
    a = np.asarray(im.getchannel('A')); rgb = np.asarray(im.convert('RGB')).mean(2)
    ys = np.nonzero(((a > umbral) & (rgb > 200)).any(1))[0]
    return int(ys.min()) if len(ys) else 0


class Capa:
    """elementos de texto con su ventana de cuadros [n0, n1] (inclusive) y su caja en el máster."""
    def __init__(self, base):
        self.base = Path(base); self.base.mkdir(parents=True, exist_ok=True)
        self.items = []          # (png, x, y, n0, n1, nombre)
        self.cajas = []          # dict(nombre, texto, n0, n1, caja)

    def _guardar(self, im, nombre):
        p = self.base / f'{nombre}.png'; im.save(p); return str(p)

    def texto(self, nombre, texto, im, y_txt, n0, n1, pop=False, cx=W // 2, x=None, y_es_caja=False):
        """y_txt = borde superior del texto (placas) o de la caja (cajas, y_es_caja=True)."""
        y = y_txt if y_es_caja else y_txt - tope_glifo(im)
        if pop:
            emax = min(1.18, 1040 / im.width)          # el pop no puede sacar la caja del cuadro (H2: caja de 961 px)
            for k, e in enumerate((emax, (1 + emax) / 2)):
                L = C.lienzo(); C.pegar(L, im, y, cx=cx, x=x, escala=e)
                self.items.append((self._guardar(L, f'{nombre}_pop{k}'), 0, 0, n0 + k, n0 + k, nombre))
            L = C.lienzo(); bb = C.pegar(L, im, y, cx=cx, x=x)
            self.items.append((self._guardar(L, nombre), 0, 0, n0 + 2, n1, nombre))
        else:
            L = C.lienzo(); bb = C.pegar(L, im, y, cx=cx, x=x)
            self.items.append((self._guardar(L, nombre), 0, 0, n0, n1, nombre))
        a = np.asarray(L.getchannel('A'))
        ys, xs = np.nonzero(a > 24)
        self.cajas.append(dict(nombre=nombre, texto=texto, n0=n0, n1=n1, pop=pop,
                               caja_visible=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                               caja_imagen=list(bb)))

    def rasterizar(self, carpeta, nf, dinamico=None):
        carpeta = Path(carpeta); carpeta.mkdir(parents=True, exist_ok=True)
        cache = {}
        for n in range(nf):
            L = C.lienzo()
            for png, x, y, n0, n1, _ in self.items:
                if n0 <= n <= n1:
                    if png not in cache:
                        cache[png] = Image.open(png).convert('RGBA')
                    L.alpha_composite(cache[png], (x, y))
            if dinamico:
                r = dinamico(n)
                if r is not None:
                    im, x, y = r
                    L.alpha_composite(im, (x, y))
            L.save(carpeta / f'{n:04d}.png', compress_level=1)
        return nf


def textos_mc05(cp):
    C_ = lambda t, s=76, tema='blanca': C.caja(t, s, tema=tema)
    cp.texto('hook', 'NADIE TE VA A DAR PERMISO.', C_('NADIE TE VA A\nDAR PERMISO.'), Y_HOOK, 0, 47, pop=True, y_es_caja=True)
    cp.texto('dato', 'El color vuelve con una sola acción. ¿Cuál?',
             C.caja('El color vuelve con una sola acción.\n¿Cuál?', 50, tema='negra', peso='semibold'), Y_DATO, 12, 47,
             y_es_caja=True)      # v02: caja negra SemiBold 50 (Medium 50 sin caja no se leía sobre el cielo a 360 px)
    xl = lambda t: C.placa(t, 120)
    cp.texto('v1', 'AGARRALA.', xl('AGARRALA.'), Y_XL, 48, 71)
    im = xl('TIRALA.')
    cp.texto('v2', 'TIRALA.', im, Y_TIRALA, 72, 95, x=40)          # mitad de abajo: a la izquierda, x ≤ 940
    cp.texto('v3', 'SACALE UNA FOTO.', xl('SACALE\nUNA FOTO.'), Y_XL2, 96, 119)   # 2 renglones: más arriba (no tapa la cabeza en c110–c119)
    cp.texto('v4', 'AGUANTALA.', xl('AGUANTALA.'), Y_XL, 120, 143)
    cp.texto('v5', 'PONETELA.', xl('PONETELA.'), Y_PONETELA, 144, 167)   # abajo, sobre las rocas: libre de estampado en todo el plano
    cp.texto('v6', 'MOSTRALA.', xl('MOSTRALA.'), Y_XL, 168, 191)
    cp.texto('queda', 'Queda una acción.', C_('Queda una acción.', 76, 'negra'), Y_XL, 192, 215, pop=True,
             y_es_caja=True)      # v02: «Queda una.» se leía como escasez (dictamen de Roma §2)
    cp.texto('firmala', 'FIRMALA.', xl('FIRMALA.'), Y_FIRMALA, 216, 263, pop=True)
    cp.texto('serif', 'Que tu historia lleve tu nombre.', placa_serif('Que tu historia\nlleve tu nombre.', 88), Y_SERIF, 276, 335)
    cp.texto('cta', 'Guardalo para el día que estés esperando permiso.',
             C_('Guardalo para el día\nque estés esperando\npermiso.'), Y_CTA, 336, 407, pop=True, y_es_caja=True)


def etapa_capas():
    if CAPA.exists():
        shutil.rmtree(CAPA)
    cp = Capa(T / 'textos')
    textos_mc05(cp)
    n = cp.rasterizar(CAPA, NF, dinamico=hud)
    hud_cajas = {}
    for c in [0, 56, 152, 192, 196, 246, 299]:
        im, x, y = hud(c); hud_cajas[f'c{c}'] = [x, y, x + im.width, y + im.height]
    malas = C.fuera_de_zona([tuple(c['caja_visible']) for c in cp.cajas] + [tuple(v) for v in hud_cajas.values()])
    jdump(dict(textos=cp.cajas, hud=hud_cajas, fuera_de_zona=malas), T / 'capas.json')
    print('capa', n, 'cuadros; fuera de zona:', malas)


# =====================================================================================================
# sonido
# =====================================================================================================
def lp_var(x, t_abre0, t_abre1, t0, fc=3000):
    """pasa-bajos que se abre: (1−r)·lp(x) + r·x con r de 0 a 1 entre t_abre0 y t_abre1 (s del máster); x empieza en t0."""
    from sonido import filt
    t = t0 + np.arange(len(x)) / SR
    r = np.clip((t - t_abre0) / (t_abre1 - t_abre0), 0, 1)
    r = r * r * (3 - 2 * r)
    return (1 - r) * filt(x, 'low', fc) + r * x


def amb_seg(m, toma, src0, t0, t1, g_db, lp=None, fade=0.008):
    from sonido import filt, db
    a = m.leer(toma); n = int(round((t1 - t0) * SR)); s0 = int(round(src0 * SR))
    seg = a[s0:s0 + n].copy()
    if len(seg) < n:
        seg = np.concatenate([seg, np.zeros(n - len(seg))])
    if lp:
        seg = filt(seg, 'low', lp)
    k = int(fade * SR); r = np.ones(n); r[:k] = np.linspace(0, 1, k); r[-k:] = np.minimum(r[-k:], np.linspace(1, 0, k))
    m.put('amb', seg * r * db(g_db), t0)
    m.log(t0, f'ambiente {toma} fuente {src0:.3f}–{src0 + t1 - t0:.3f} s, {g_db:+.1f} dB' + (f', lp {lp}' if lp else ''))


def ambientes(m):
    LP = 3000                                   # B/N «suena gris»
    amb_seg(m, 'IMG_7824', 8.00, 0.0, 1.6, -8, LP)
    amb_seg(m, 'IMG_7996', 0.30, 1.6, 2.4, -8, LP)
    amb_seg(m, 'IMG_7996', 64 / 30, 2.4, 3.2, -8, LP)
    amb_seg(m, 'IMG_7884', 0.00, 3.2, 4.0, -8, LP)
    amb_seg(m, 'IMG_7895', 0.00, 4.0, 4.8, -4, LP)          # ola
    amb_seg(m, 'IMG_7885', 0.00, 4.8, 5.6, -8, LP)
    amb_seg(m, 'IMG_7824', 3.00, 5.6, 6.4, -10, LP)         # 4531 sin su audio (conversación): ambiente de 7824
    amb_seg(m, 'IMG_7824', 3.80, 6.4, 7.2, -24, 1500)       # casi silencio
    # 3453 no tiene ambiente útil (−50 LUFS): entra antes el ambiente real de 8004 (misma toma del plano 10), con el
    # pasa-bajos de 3000 Hz que se abre junto con el color (c240–c264 = 8,0–8,8 s) y sigue sin filtro.
    from sonido import db
    a = m.leer('IMG_8004')
    t0, t1, src0 = 7.6, 11.2, 0.0
    n = int(round((t1 - t0) * SR)); seg = a[int(src0 * SR):int(src0 * SR) + n].copy()
    seg = lp_var(seg, 8.0, 8.8, t0, 3000)
    r = np.ones(n); k = int(0.25 * SR); r[:k] = np.linspace(0, 1, k) ** 2; r[-int(0.008 * SR):] = np.linspace(1, 0, int(0.008 * SR))
    m.put('amb', seg * r * db(-2), t0)
    m.log(t0, 'ambiente IMG_8004 fuente 0,000–3,600 s, −2 dB; pasa-bajos 3000 Hz que se abre entre 8,0 y 8,8 s')
    amb_seg(m, 'IMG_7824', 2.00, 11.2, DUR, -6, fade=0.02)


def cerrojo(m, t):
    m.impacto(t, .22); m.toque(t, .25, 220); m.log(t, 'cerrojo')


def foley(m):
    for c in X_CUADROS + [158]:
        cerrojo(m, c / FPS)
    m.tela(2.52, 0.35, .2)                      # tira la remera
    m.obturador(3.45, .45)                      # foto
    m.tela(7.25, 1.20, .16)                     # dedos sobre el relieve
    m.log(7.25, 'tela 7,25–8,45')
    for c in LATIDOS:                           # latido de la etiqueta (suave)
        m.bombo(c / FPS, .22, f0=70, f1=40, dec=.18, pista='fx'); m.log(c / FPS, 'latido')
    # desbloqueo
    t = DESBLOQUEO / FPS
    m.toque(t, .28, 1760); m.toque(t + 0.06, .22, 2640); m.log(t, 'desbloqueo ✓')


def musica(m):
    # 75 BPM (pulso 0,8 s): todos los cortes caen en el pulso
    m.pad(0.0, [38, 41, 45], 6.4, .05, 700)
    for t in (0.0, 1.6, 3.2, 4.8):
        m.ocho08(t, 26, .6, .45)
    for t in np.arange(1.6, 6.41, 0.8):        # golpe grave en cada corte de los intentos
        m.bombo(round(float(t), 3), .38, f0=95, f1=44, dec=.32)
    m.silenciar('mus', 6.4, 7.2)
    m.silenciar('bombo', 6.45, 7.2)
    m.campana(6.4, 50, .07, dec=1.2)            # campana grave (en el hueco)
    m.pad(7.2, [38, 41, 45], 1.55, .035, 520, a=.5, r=.2)
    m.subida(7.6, 8.75, .2)
    m.campana(DESBLOQUEO / FPS, 79, .05)
    # drop 8,8: mayor
    m.bombo(8.8, 1.0); m.impacto(8.8, .5); m.campana(8.8, 72, .07)
    m.pad(8.8, [48, 52, 55, 60], 4.8, .07, 2200)
    for t in np.arange(9.6, 13.3, 0.8):
        m.bombo(round(float(t), 3), .78)
    for t in (9.6, 11.2, 12.8):
        m.palma(t, .26)
    for t in np.arange(8.8, 13.45, 0.4):
        m.charles(round(float(t), 3), .07)
    for t, nota in ((8.8, 36), (10.4, 41), (12.0, 43)):
        m.ocho08(t, nota, 1.4, .42)
    m.campana(11.2, 76, .06)
    m.fundido('mus', 13.1, DUR)
    m.fundido('bombo', 13.1, DUR)
    m.fundido('fx', 13.3, DUR)                  # colas de reverberación de la música (van en 'fx')


def medir_ebur(f):
    r = subprocess.run(nice(['ffmpeg', '-nostats', '-i', f, '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-']),
                       capture_output=True, text=True).stderr
    g = lambda k: float([l for l in r.splitlines() if l.strip().startswith(k)][-1].split()[1])
    return g('I:'), g('Peak:'), g('LRA:')


def limitar_tp(salida, lufs=-14.0, tp_max=-1.2):
    """(copiado de life_v2) rehace la última etapa desde el _pre.wav bajando el techo del alimiter (level=false) hasta
    que el pico real queda ≤ tp_max, con la ganancia corregida a −14 LUFS en cada vuelta."""
    pre = str(salida).replace('.wav', '_pre.wav')
    I0, _, _ = medir_ebur(pre)
    gan = lufs - I0; lim_db = -1.6; hist = []
    for _ in range(14):
        lim = 10 ** (lim_db / 20)
        subprocess.run(nice(['ffmpeg', '-v', 'error', '-y', '-i', pre, '-af',
                             f'volume={gan:.2f}dB,alimiter=limit={lim:.4f}:level=false:attack=3:release=60:latency=1',
                             '-c:a', 'pcm_f32le', str(salida)]), check=True)
        I, Pk, LRA = medir_ebur(str(salida)); hist.append(dict(techo_db=lim_db, ganancia_db=round(gan, 2), lufs=I, pico_dbtp=Pk))
        if abs(I - lufs) < 0.3 and Pk <= tp_max:
            break
        if Pk > tp_max:
            lim_db -= 0.5
        gan += (lufs - I)
    return dict(lufs=I, pico_dbtp=Pk, lra=LRA, vueltas=hist)


def mezclar(nombre, dur, partes, carpeta):
    from sonido import Mezcla
    carpeta.mkdir(parents=True, exist_ok=True)
    m = Mezcla(dur)
    for p in partes:
        p(m)
    f = carpeta / f'{nombre}.wav'
    r = m.exportar(str(f), lufs=-14)
    out = dict(exportar=r)
    I, Pk, LRA = medir_ebur(str(f))
    if Pk > -1.2 or abs(I + 14) > 0.4:
        out['limitado'] = limitar_tp(f)
    out['final'] = dict(zip(('lufs', 'pico_dbtp', 'lra'), medir_ebur(str(f))))
    return out


def etapa_audio():
    out = dict(completa=mezclar('mc05_completa', DUR, [ambientes, foley, musica], A),
               sinmusica=mezclar('mc05_sinmusica', DUR, [ambientes, foley], A))
    jdump(out, A / 'audio.json')
    print(json.dumps({k: v['final'] for k, v in out.items()}))


# =====================================================================================================
# máster: base + capa por cuadro + mezcla → H.264 High 4.0 / AAC-LC (mismos parámetros que video.master)
# =====================================================================================================
ENC_MASTER = ['-c:v', 'libx264', '-profile:v', 'high', '-level:v', '4.0', '-preset', 'slow', '-crf', '17',
              '-maxrate', '20M', '-bufsize', '25M', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-g', '30',
              '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']
ENC_AUDIO = ['-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2']
META = ['-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
        '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler', '-movflags', '+faststart']


def master_capa(base, capa_dir, audio_wav, salida):
    """la capa entra como secuencia PNG a 30 fps (cuadro n de la capa = cuadro n del video: sin ventanas de tiempo),
    convertida a YUV con matriz BT.709 de rango limitado y superpuesta en 4:4:4."""
    fc = ('[0:v]setsar=1,format=yuv444p[b];'
          '[2:v]scale=out_color_matrix=bt709:out_range=tv,format=yuva444p[c];'
          '[b][c]overlay=0:0:format=yuv444:eof_action=pass,format=yuv420p[vout]')
    V.sh(nice(['ffmpeg', '-v', 'error', '-y', '-i', base, '-i', audio_wav, '-framerate', str(FPS), '-i', f'{capa_dir}/%04d.png',
               '-filter_complex', fc, '-map', '[vout]', '-map', '1:a:0', *ENC_MASTER, *ENC_AUDIO, *META,
               '-shortest', salida]))
    return salida


def remux_audio(master, audio_wav, salida):
    """mismo flujo de video (copia, sin recodificar) con otra mezcla."""
    V.sh(nice(['ffmpeg', '-v', 'error', '-y', '-i', master, '-i', audio_wav, '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy',
               *ENC_AUDIO, *META, '-shortest', salida]))
    return salida


def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    f1 = MAS / NOMBRES['completa']; f2 = MAS / NOMBRES['sinmusica']
    master_capa(T / 'mc05_base.mp4', CAPA, A / 'mc05_completa.wav', f1)
    remux_audio(f1, A / 'mc05_sinmusica.wav', f2)
    for f in (f1, f2):
        print(f, U.md5_stream(f, 'v'), U.md5_stream(f, 'a'))


# =====================================================================================================
# control (evidencia_v01)
# =====================================================================================================
def atomos(f):
    import struct
    out = []
    with open(f, 'rb') as h:
        while True:
            hd = h.read(8)
            if len(hd) < 8:
                break
            n, k = struct.unpack('>I4s', hd)
            if n == 1:
                n = struct.unpack('>Q', h.read(8))[0]; h.seek(n - 16, 1)
            else:
                h.seek(n - 8, 1)
            out.append(k.decode('latin1'))
            if n == 0:
                break
    return out


def silencio_final(a, umbral=-60.0):
    w = SR // 100; m = a.mean(1); n = len(m) // w
    v = 20 * np.log10(np.sqrt(np.square(m[:n * w].reshape(n, w)).mean(1)) + 1e-12)
    k = 0
    while k < n and v[n - 1 - k] < umbral:
        k += 1
    return round(k * 0.01, 2)


def ficha(f):
    """ffprobe + decodificación + md5 de flujos + sonoridad + GPS + átomos."""
    f = Path(f)
    err = subprocess.run(nice(['ffmpeg', '-v', 'error', '-i', f, '-f', 'null', '-']), capture_output=True, text=True).stderr.strip()
    pj = json.loads(U.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(f)]))
    vs = [s for s in pj['streams'] if s['codec_type'] == 'video'][0]
    au = [s for s in pj['streams'] if s['codec_type'] == 'audio'][0]
    n = int(U.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames',
                   '-of', 'csv=p=0', str(f)]).decode().strip())
    cuerpo = f.read_bytes()
    return dict(archivo=str(f), bytes=f.stat().st_size, sha256=hashlib.sha256(cuerpo).hexdigest(),
                md5_video=U.md5_stream(f, 'v'), md5_audio=U.md5_stream(f, 'a'),
                decodifica_completo=(err == ''), errores=err[:400],
                video=dict(codec=vs['codec_name'], perfil=vs.get('profile'), nivel=vs.get('level'), pix_fmt=vs['pix_fmt'],
                           ancho=vs['width'], alto=vs['height'], fps=vs['r_frame_rate'], cuadros_decodificados=n,
                           duracion=float(vs['duration']),
                           color=[vs.get('color_range'), vs.get('color_space'), vs.get('color_transfer'), vs.get('color_primaries')]),
                audio=dict(codec=au['codec_name'], perfil=au.get('profile'), hz=int(au['sample_rate']), canales=au['channels'],
                           duracion=float(au['duration'])),
                duracion_formato=float(pj['format']['duration']), etiquetas_formato=pj['format'].get('tags', {}),
                marcas_ubicacion=[m.decode() for m in (b'ISO6709', b'location', b'com.apple.quicktime') if m in cuerpo],
                atomos=atomos(f), sonoridad=U.ebur(f))


def saturacion_por_cuadro(mp4):
    """|Cb−128| + |Cr−128| medio y máximo por cuadro (yuv444p a 270×480, sin conversión de matriz)."""
    r = U.run(nice(['ffmpeg', '-v', 'error', '-i', mp4, '-vf', 'scale=270:480:flags=area,format=yuv444p', '-f', 'rawvideo', '-']))
    a = np.frombuffer(r, np.uint8).reshape(-1, 3, 480, 270).astype(np.int16)
    d = np.abs(a[:, 1] - 128) + np.abs(a[:, 2] - 128)
    return d.mean((1, 2)), d.reshape(len(d), -1).max(1)


def movimiento(mp4, n0, n1):
    """diferencia media absoluta de luma entre cuadros consecutivos (n0..n1) a 270×480."""
    a = U.leer(mp4, 270, 480, n0=n0, n1=n1).astype(np.int16).mean(3)
    return [round(float(np.abs(a[i + 1] - a[i]).mean()), 3) for i in range(len(a) - 1)]


def tira(ims, rotulos, salida, ancho=360):
    fnt = ImageFont.truetype(FONT, 22)
    tiles = []
    for im, r in zip(ims, rotulos):
        im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 12 + d.textlength(r, font=fnt), 30], fill=(0, 0, 0)); d.text((6, 3), r, font=fnt, fill=(255, 255, 0))
        tiles.append(im)
    Wd = Image.new('RGB', (len(tiles) * (ancho + 4), tiles[0].height), (30, 30, 30))
    for i, t in enumerate(tiles):
        Wd.paste(t, (i * (ancho + 4), 0))
    Wd.save(salida, quality=90)


def vista_360(mp4, cuadros, salida, cols=6):
    from PIL import Image as I
    fr = U.leer(mp4, 360, 640, n0=min(cuadros), n1=max(cuadros))
    ims = [I.fromarray(fr[c - min(cuadros)]) for c in cuadros]
    filas = math.ceil(len(ims) / cols)
    fnt = ImageFont.truetype(FONT, 18)
    Wd = I.new('RGB', (cols * 362, filas * 642), (30, 30, 30))
    for i, (im, c) in enumerate(zip(ims, cuadros)):
        d = ImageDraw.Draw(im); d.rectangle([0, 0, 64, 24], fill=(0, 0, 0)); d.text((4, 2), f'c{c}', font=fnt, fill=(255, 255, 0))
        Wd.paste(im, ((i % cols) * 362, (i // cols) * 642))
    Wd.save(salida, quality=90)


def tope_letras_3453(mp4, n0, n1):
    """fila más alta con letras del estampado (gris claro, sin saturación; los dedos quedan fuera por saturación) en el
    plano de 3453 del máster, por cuadro. Sirve para comprobar que «FIRMALA.» y la etiqueta quedan arriba de ROCCÉ."""
    fr = U.leer(mp4, 540, 960, n0=n0, n1=n1).astype(np.float32)
    out = []
    for f in fr:
        L = f.mean(2); sat = (f.max(2) - f.min(2)) / (f.max(2) + 1)
        m = (L > 150) & (sat < 0.18)
        filas = np.nonzero(m.sum(1) >= 25)[0]       # ≥ 25 px por fila: deja fuera las pelusas claras de la tela
        out.append(int(filas.min() * 2) if len(filas) else None)
    return out


def niveles(f, tramos):
    a = U.audio_np(f)
    niv, v100, sil = U.niveles_tramos(a, tramos)
    return dict(por_tramo=niv, ventanas_100ms_bajo_menos50=sil, silencio_final_s=silencio_final(a),
                muestras=len(a), duracion_audio=round(len(a) / SR, 4))


def etapa_control():
    EVID.mkdir(parents=True, exist_ok=True)
    f1 = MAS / NOMBRES['completa']; f2 = MAS / NOMBRES['sinmusica']
    rep = dict(fecha='2026-11-25', pieza='MC-05', archivos={k: ficha(MAS / v) for k, v in NOMBRES.items()})
    rep['mismo_flujo_de_video'] = rep['archivos']['completa']['md5_video'] == rep['archivos']['sinmusica']['md5_video']
    tramos = [(f'{p[0]} {p[1]}', c0 / FPS, c1 / FPS) for p, c0, c1 in zip(PLANOS, [0] + CORTES, CORTES + [NF])]
    rep['niveles'] = {k: niveles(MAS / v, tramos) for k, v in NOMBRES.items()}
    # saturación por cuadro (criterio de Roma)
    sm, sx = saturacion_por_cuadro(f1)
    rep['saturacion'] = dict(max_media_c0_c239=round(float(sm[:240].max()), 4), max_pixel_c0_c239=int(sx[:240].max()),
                             media_c240_c263=[round(float(v), 2) for v in sm[240:264]],
                             media_c264=round(float(sm[264]), 2), media_c300=round(float(sm[300]), 2))
    jdump(dict(media=sm, maximo=sx), EVID / 'saturacion_por_cuadro.json')
    # gráfico de saturación
    from PIL import Image as I
    g = I.new('RGB', (NF * 2 + 60, 260), (250, 250, 250)); d = ImageDraw.Draw(g)
    mx = max(1.0, float(sm.max()))
    for n in range(NF):
        y = 230 - int(200 * sm[n] / mx); d.line([30 + 2 * n, 230, 30 + 2 * n, y], fill=(40, 40, 40) if n < 240 else (60, 120, 200))
    for c in (240, 264):
        d.line([30 + 2 * c, 20, 30 + 2 * c, 235], fill=(220, 0, 0))
        d.text((32 + 2 * c, 20), f'c{c}', fill=(220, 0, 0))
    d.text((32, 236), 'saturación media por cuadro (|Cb−128|+|Cr−128|), c0–c407', fill=(0, 0, 0))
    g.save(EVID / 'saturacion_por_cuadro.png')
    # estampado de 3453 vs. textos de arriba
    tope = tope_letras_3453(T / 'mc05_base.mp4', 216, 263)      # base sin textos (en el máster detectaría los textos)
    cap = json.load(open(T / 'capas.json'))
    fondo_textos = max([c['caja_visible'][3] for c in cap['textos'] if c['nombre'] == 'firmala'] +
                       [v[3] for k, v in cap['hud'].items() if k in ('c246', 'c0')])
    rep['3453_estampado'] = dict(tope_letras_por_cuadro=dict(zip(range(216, 264), tope)), fondo_textos=fondo_textos,
                                 minimo_tope=min(t for t in tope if t is not None),
                                 margen_px=min(t for t in tope if t is not None) - fondo_textos)
    rep['movimiento_ultimo_plano'] = movimiento(f1, 380, 407)
    rep['color_prenda'] = dict(
        negra_3453={f'c{c}': tela_oscura(f1, c, (0.55, 0.95, 0.0, 1.0)) for c in (252, 258, 263)},
        negra_7824={f'c{c}': tela_oscura(f1, c, (0.5, 0.9, 0.15, 0.85)) for c in (336, 370, 407)},
        blanca_8004={f'c{c}': rgb_plano(f1, c, REG_BLANCA['IMG_8004']) for c in (264, 279, 291, 300, 309, 318, 324, 330, 335)},
        criterio='Negra: |R−B| ≤ 5 en la tela oscura (no marrón); Blanca: B−R ≤ +12 (objetivo +8)')
    U.hoja_contacto(f1, EVID / 'hoja_cada_0.5s.jpg', cada=15, cols=7, ancho=240)
    U.cuadros_corte(f1, CORTES, EVID / 'cortes', NF - 1)
    sel = sorted({0, 12, 47, 56, 80, 96, 104, 120, 128, 144, 152, 168, 176, 192, 196, 216, 240, 246, 252, 258, 263, 276,
                  300, 336, 360, 407})
    vista_360(f1, sel, EVID / 'vista_360px.jpg')
    for c in (0, 216, 240, 246, 252, 263, 264, 276, 336, 407):
        V.cuadro(f1, c, EVID / f'cuadro_c{c:03d}.png')
    shutil.copy2(T / 'capas.json', EVID / 'capas_textos.json')
    shutil.copy2(T / 'planos.json', EVID / 'planos.json')
    shutil.copy2(A / 'audio.json', EVID / 'audio.json')
    for k in ('completa', 'sinmusica'):
        shutil.copy2(A / f'mc05_{k}_eventos.json', EVID / f'eventos_{k}.json')
    jdump(rep, EVID / 'control.json')
    print(json.dumps({k: (v['md5_video'], v['md5_audio'], v['sonoridad'], v['video']['cuadros_decodificados'],
                          v['video']['duracion'], v['audio']['duracion'], v['decodifica_completo'], v['marcas_ubicacion'])
                      for k, v in rep['archivos'].items()}, ensure_ascii=False))
    print('saturación', rep['saturacion'])
    print('3453', rep['3453_estampado']['minimo_tope'], rep['3453_estampado']['fondo_textos'])
    print('mov', rep['movimiento_ultimo_plano'][-10:])
    print('color', json.dumps(rep['color_prenda'], ensure_ascii=False))


# =====================================================================================================
# entregar
# =====================================================================================================
def entregar(nombres, carpeta_mas, evid_local, pieza, extras=(), ev_dst=None):
    """copia a EXPORTACIONES/ y a la carpeta de la pieza (no sobrescribe) y verifica por md5 de flujos (la carpeta de la
    pieza agrega una caja C2PA: los bytes cambian, los flujos no)."""
    pieza.mkdir(parents=True, exist_ok=True)
    for nombre in nombres:
        for dst in (EXP / nombre, pieza / nombre):
            if dst.exists():
                raise RuntimeError(f'{dst} ya existe: no se sobrescribe')
    for nombre in nombres:
        for dst in (EXP / nombre, pieza / nombre):
            shutil.copyfile(carpeta_mas / nombre, dst)
    for src in extras:
        shutil.copyfile(src, pieza / Path(src).name)
    ev = ev_dst or (pieza / evid_local.name)
    if ev.exists():
        shutil.rmtree(ev)
    shutil.copytree(evid_local, ev)
    time.sleep(10)
    res = {}
    for nombre in nombres:
        src = carpeta_mas / nombre
        ref = dict(md5_video=U.md5_stream(src, 'v'), md5_audio=U.md5_stream(src, 'a'), sha256=hashlib.sha256(src.read_bytes()).hexdigest())
        for dst in (EXP / nombre, pieza / nombre):
            err = subprocess.run(nice(['ffmpeg', '-v', 'error', '-i', dst, '-f', 'null', '-']), capture_output=True, text=True).stderr.strip()
            got = dict(md5_video=U.md5_stream(dst, 'v'), md5_audio=U.md5_stream(dst, 'a'), sha256=hashlib.sha256(dst.read_bytes()).hexdigest())
            res[str(dst)] = dict(got, bytes=dst.stat().st_size, flujos_iguales=(got['md5_video'] == ref['md5_video'] and got['md5_audio'] == ref['md5_audio']),
                                 bytes_iguales=(got['sha256'] == ref['sha256']), decodifica=(err == ''), atomos=atomos(dst))
            print(dst, res[str(dst)]['flujos_iguales'], res[str(dst)]['bytes_iguales'], res[str(dst)]['decodifica'], flush=True)
    res['evidencia'] = dict(carpeta=str(ev), local=sum(1 for _ in evid_local.rglob('*') if _.is_file()),
                            red=sum(1 for _ in ev.rglob('*') if _.is_file()))
    return res


def hoja_cajas(base, capas_json, salida, cada=4, cols=10, ancho=270):
    """hoja de la base (sin textos) con la caja de cada texto marcada en rojo: control cuadro a cuadro de que ningún
    texto tapa el estampado (ROCCÉ, «Founders Privée», «so f★cking close.»)."""
    from PIL import ImageDraw
    alto = ancho * 16 // 9; k = W / ancho
    cap = json.load(open(capas_json))['textos']
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(base), '-vf', f"select='not(mod(n\\,{cada}))',scale={ancho}:{alto}",
                          '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, alto, ancho, 3)
    filas = (len(a) + cols - 1) // cols
    out = Image.new('RGB', (ancho * cols, alto * filas), (30, 30, 30))
    for i in range(len(a)):
        n = i * cada; im = Image.fromarray(a[i]).copy(); d = ImageDraw.Draw(im)
        for t in cap:
            if t['n0'] <= n <= t['n1']:
                d.rectangle([v / k for v in t['caja_visible']], outline=(255, 0, 0), width=2)
        d.rectangle([0, 0, 44, 13], fill=(0, 0, 0)); d.text((2, 0), f'c{n}', fill=(255, 255, 0))
        out.paste(im, ((i % cols) * ancho, (i // cols) * alto))
    out.save(salida, quality=85)
    return salida


def etapa_cajas():
    print(hoja_cajas(T / 'mc05_base.mp4', T / 'capas.json', EVID / 'textos_vs_estampado_cada4.jpg'))


def rocce_extremos(f):
    """x izquierda / derecha de las letras de denim de ROCCÉ (oscuras, sin saturación) en la franja y 880–1280 de un
    cuadro RGB 1080×1920 del plano 10. Completo = la R y la É dentro del cuadro (≥ 4 px del borde)."""
    band = f[880:1280].astype(np.float32)
    L = band.mean(2); sat = band.max(2) - band.min(2)
    cols = np.nonzero(((L < 80) & (sat < 60)).sum(0) >= 6)[0]
    if not len(cols):
        return None, None, False
    x0, x1 = int(cols.min()), int(cols.max())
    return x0, x1, bool(x0 >= 4 and x1 <= W - 5)


def etapa_evid_v02():
    """evidencia que pide el dictamen de Roma para v02: tira c300–c335 cada 2 cuadros a tamaño real, cuadros c12 y c192,
    hoja cada 0,1 s del plano 10 con la medición de ROCCÉ completo y la comparación de la mezcla."""
    from PIL import ImageDraw
    fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
    f1 = MAS / NOMBRES['completa']
    fr = U.leer(f1, W, H, n0=264, n1=335)
    p10 = json.load(open(PL / 'P10_IMG_8004.json'))
    mapa = p10['rampa']['cuadro_fuente_por_cuadro']
    med = []
    for i, f in enumerate(fr):
        x0, x1, ok = rocce_extremos(f)
        med.append(dict(c=264 + i, src=mapa[i], x_izq=x0, x_der=x1, completo=ok))
    compl = [m['c'] for m in med if m['completo']]
    tramo = dict(primero=min(compl), ultimo=max(compl), cuadros=len(compl), segundos=round(len(compl) / FPS, 3),
                 continuo=(max(compl) - min(compl) + 1 == len(compl)))
    jdump(dict(criterio='ROCCÉ completo = letras de denim con x ≥ 4 y x ≤ 1075 (franja y 880–1280)', tramo=tramo,
               por_cuadro=med), EVID / 'P10_rocce_completo.json')
    # hoja cada 0,1 s (3 cuadros) + último
    sel = list(range(0, 72, 3)) + [71]
    ancho = 270; alto = 480; cols = 9
    out = Image.new('RGB', (ancho * cols, alto * ((len(sel) + cols - 1) // cols)), (30, 30, 30))
    for j, i in enumerate(sel):
        im = Image.fromarray(fr[i]).resize((ancho, alto), Image.LANCZOS); d = ImageDraw.Draw(im)
        m = med[i]
        d.rectangle([0, 0, ancho, 34], fill=(0, 0, 0))
        d.text((4, 2), f"c{m['c']}  src c{m['src']}", font=fnt, fill=(255, 255, 0))
        d.text((4, 17), 'ROCCÉ COMPLETO' if m['completo'] else 'cortado', font=fnt, fill=(80, 255, 80) if m['completo'] else (255, 90, 90))
        if m['x_izq'] is not None:
            y = int(1080 * alto / H)
            d.line([m['x_izq'] * ancho / W, y, m['x_der'] * ancho / W, y], fill=(80, 255, 80) if m['completo'] else (255, 90, 90), width=3)
        out.paste(im, ((j % cols) * ancho, (j // cols) * alto))
    out.save(EVID / 'P10_hoja_cada_0.1s_rocce.jpg', quality=88)
    # tira c300–c335 cada 2 cuadros, tamaño real
    td = EVID / 'tira_c300-c335_cada2'; td.mkdir(exist_ok=True)
    for c in list(range(300, 336, 2)) + [335]:
        Image.fromarray(fr[c - 264]).save(td / f'c{c:03d}.jpg', quality=92)
    for c in (12, 192):
        V.cuadro(f1, c, EVID / f'cuadro_c{c:03d}.png')
    print(tramo)


def etapa_entregar():
    res = entregar(list(NOMBRES.values()), MAS, EVID, PIEZA)
    jdump(res, T / 'entrega.json')
    print(res['evidencia'])


if __name__ == '__main__':
    globals()['etapa_' + (sys.argv[1] if len(sys.argv) > 1 else 'hojas')]()
