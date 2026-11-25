#!/usr/bin/env python3
"""Roccé Life · V4 «¿Vuelve?» versión B · receta del máster v01 (Pedro, 25/11/2026).

Guion: piezas/LIFE_rocce_life/TANDA2/V4_vuelve/01_fede_guion_G1_v1.md (G1 v1) + base común de la tanda
(V3_5_domingos/01_fede_guion_G1_v1.md) + condiciones de Roma (07_roma_aprobacion_guiones_t2.md: paso 9 = «Noviembre:
escribe que vuelve.»; 0–12,50 s sin remera, logo ni firma; citas idénticas a 02b_roma_ensayo_topuria_extractos.md).
Topuria solo como texto: ni su imagen ni su voz. Sin términos de apuestas en pantalla.

Reutiliza sin modificarlos: scripts/fmt/video.py (color/HDR→SDR, plano, unir, foto_srgb), fmt03.py (plano_n, plano_z,
leer, md5_stream, ebur, audio_np, niveles_tramos, hoja_contacto, cuadros_corte, color_parche), fmt03_v02.py
(momentánea), sonido.py (Mezcla) y life_v2.py (CSS de la placa, limitar_tp, medir_ebur, atomos, silencio_final, tira,
hoja_cuadros; al importarlo, los ffmpeg de video.py corren con nice y 2 hilos). life_v2_render.js renderiza la placa.
Lo nuevo vive acá y en life_v4_render.js: texto cinético palabra por palabra renderizado cuadro a cuadro en Chromium
(capa RGBA), grado B/N con exposición por tramo (E−/E+), seguimiento de las remeras para probar la separación.

Etapas (con nice -n 10 y el python de TRABAJO/venv):
  hojas → medir → planos → grado → textos → placa → audio → master → control → entregar
Intermedios en TRABAJO/life2/v4/. Nada se publica; sin servicios externos ni créditos.
"""
import json, math, subprocess, sys, hashlib, shutil, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/life')
import video as V          # noqa: E402
import fmt03 as U          # noqa: E402
import life_v2 as L2       # noqa: E402  (envuelve V.sh: nice -n 10 y 2 hilos)

R = Path('/home/user/1')
T = R / 'TRABAJO/life2/v4'
HJ, MED, P, A, MAS, TX, PL = T / 'hojas', T / 'med', T / 'planos', T / 'audio', T / 'master', T / 'textos', T / 'placa'
EVID = T / 'evidencia_v01'
EXP = R / 'EXPORTACIONES'
PIEZA = Path('/mnt/project-files/piezas/LIFE_rocce_life/TANDA2/V4_vuelve')
ENSAYO = Path('/mnt/project-files/piezas/LIFE_rocce_life/TANDA2/02b_roma_ensayo_topuria_extractos.md')
FPS, W, H = 30, 1080, 1920
NF = 477
DUR = NF / FPS                      # 15,900 s
SR = 48000
NW, NH = 2160, 3840
FULL = (0, 0, NW, NH)
FONT = U.FONT
NOMBRES = {'completa': 'ROCCE_LIFE_V4_VUELVE_v01.mp4', 'sinmusica': 'ROCCE_LIFE_V4_VUELVE_SINMUSICA_v01.mp4'}
PY = str(R / 'TRABAJO/venv/bin/python')


def nice(cmd):
    return ['nice', '-n', '10'] + list(cmd)


def jdump(obj, f):
    Path(f).parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(f, 'w'), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))


# =====================================================================================================
# línea de tiempo (guion §tabla; cuadros del máster a 30 fps, inclusive)
# =====================================================================================================
PASOS = [  # (paso, cuadro inicial, cuadro final, función)
    (1, 0, 17, 'APUESTA'), (2, 18, 41, 'GRAN PREGUNTA'), (3, 42, 65, 'E− 1'), (4, 66, 89, 'E− 2'), (5, 90, 116, 'E− 3'),
    (6, 117, 146, 'E+ 1 + PISTA'), (7, 147, 176, 'E+ 2'), (8, 177, 200, 'E− 4'), (9, 201, 221, 'E+ 3'),
    (10, 222, 242, 'E− 5 + SUBE'), (11, 243, 284, 'GIRO'), (12, 285, 374, 'RESOLUCIÓN'), ('negro', 375, 377, 'negro'),
    (13, 378, 416, 'REENGANCHE (color)'), (14, 417, 476, 'CTA'),
]
# cajas del guion en píxeles de la toma ya rotada (x0, y0, ancho); alto = ancho × 16/9
CAJAS = {'A': (0, 0, 844), 'B1': (0, 0, 731), 'B2': (700, 0, 731), 'B3': (1400, 0, 731), 'C': (0, 0, 788),
         'D': (1080, 200, 731), 'E': (0, 0, 900)}


def zc(c):
    """caja (x0, y0, ancho) o clave de CAJAS → (Z, cx, cy) para fmt03.plano_z sobre el cuadro entero 2160×3840."""
    x0, y0, w = CAJAS[c] if isinstance(c, str) else c
    Z = NW / w
    return Z, x0 + w / 2, y0 + NH / Z / 2


def _blur(cuadros):
    """desenfoque horizontal (barrido) en cuadros del plano: {n: radio}."""
    return ','.join(f"avgblur=sizeX={r}:sizeY=1:enable='eq(n\\,{n})'" for n, r in cuadros.items())


def plan_planos():
    v2 = []
    for n in range(42, 117):          # 7896 0,00–2,50: pasos 3 (B1), 4 (B2, «salto lateral») y 5 (B3, seco)
        v2.append('B1' if n <= 64 else (140, 0, 731) if n == 65 else (490, 0, 731) if n == 66 else 'B2' if n <= 89 else 'B3')
    v5 = ['B1'] * 24 + ['B3'] * 21  # 7896 2,50–4,00: pasos 8 (B1) y 9 (B3)
    return [
        dict(id='01_7895_apuesta', m0=0, tipo='z', toma='IMG_7895', n0=0, v=['A'] * 42),
        dict(id='02_7896_e1-e3', m0=42, tipo='z', toma='IMG_7896', n0=0, v=v2, post=_blur({23: 30, 24: 45, 25: 12})),
        dict(id='03_7884_p1', m0=117, tipo='z', toma='IMG_7884', n0=0, v=['C'] * 30),
        dict(id='04_7896_p2', m0=147, tipo='z', toma='IMG_7896', n0=147, v=['D'] * 30),
        dict(id='05_7896_e4-p3', m0=177, tipo='z', toma='IMG_7896', n0=75, v=v5),
        dict(id='06_8002_e5', m0=222, tipo='z', toma='IMG_8002', n0=0, v=['E'] * 21),
        dict(id='07_7896_giro', m0=243, tipo='z', toma='IMG_7896', n0=0, v=['B1'] * 132),
        dict(id='08_negro', m0=375, tipo='negro', nf=3),
        dict(id='09_7895_color', m0=378, tipo='n', toma='IMG_7895', n0=0, nf=39, caja=FULL, post=_blur({37: 24, 38: 48})),
        dict(id='10_4631_cta', m0=417, tipo='n', toma='IMG_4631', n0=129, nf=60, caja=(0, 0, 1080, 1920),
             post=_blur({0: 48, 1: 20})),
    ]


# exposición por cuadro (guion: E− = −1 de exposición, E+ = +0,5; pasos 11–12 luminancia ×0,35, «oscurece en 4 c»)
GRADO = [(0, 41, 'bn', 1.0), (42, 116, 'bn', 0.5), (117, 176, 'bn', 2 ** 0.5), (177, 200, 'bn', 0.5),
         (201, 221, 'bn', 2 ** 0.5), (222, 242, 'bn', 0.5), (243, 374, 'oscuro', None), (375, 377, 'negro', None),
         (378, 476, 'color', None)]
OSCURO_RAMPA = {243: 0.75, 244: 0.62, 245: 0.48}       # c246 en adelante: ×0,35 (c243 parte del nivel de E−)
OSCURO = 0.35


def grado_de(n):
    for a, b, modo, k in GRADO:
        if a <= n <= b:
            if modo == 'oscuro':
                return modo, OSCURO_RAMPA.get(n, OSCURO)
            return modo, k
    raise ValueError(n)


# =====================================================================================================
# etapa hojas · fuentes con las cajas del guion y grillas para ubicar las remeras
# =====================================================================================================
def hoja_fuente(toma, n0, n1, cada, cajas, salida, ancho=270, cols=10):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 16)
    nw, nh = V.TOMAS[toma]['nat']
    h = round(ancho * nh / nw)
    fr = U.leer(V._src(toma), ancho, h, n0=n0, n1=n1, vf_pre=V.color(toma))
    s = ancho / nw
    tiles = []
    for k in range(0, len(fr), cada):
        im = Image.fromarray(fr[k]); d = ImageDraw.Draw(im)
        for c, col in cajas:
            x0, y0, w = CAJAS[c]
            d.rectangle([x0 * s, y0 * s, (x0 + w) * s, (y0 + w * 16 / 9) * s], outline=col, width=2)
        d.rectangle([0, 0, 110, 20], fill=(0, 0, 0)); d.text((3, 1), f'c{n0 + k} {(n0 + k) / 30:.2f}s', font=fnt, fill=(255, 255, 0))
        tiles.append(im)
    rows = math.ceil(len(tiles) / cols)
    Wd = Image.new('RGB', (cols * (ancho + 2), rows * (h + 2)), (30, 30, 30))
    for i, t in enumerate(tiles):
        Wd.paste(t, ((i % cols) * (ancho + 2), (i // cols) * (h + 2)))
    Wd.save(salida, quality=88)


def etapa_hojas():
    HJ.mkdir(parents=True, exist_ok=True)
    hoja_fuente('IMG_7895', 0, 68, 2, [('A', (255, 0, 0))], HJ / '7895_c0-c68_c2.jpg')
    hoja_fuente('IMG_7896', 0, 184, 4, [('B1', (255, 0, 0)), ('B2', (0, 255, 0)), ('B3', (0, 128, 255)), ('D', (255, 0, 255))],
                HJ / '7896_c0-c184_c4.jpg')
    hoja_fuente('IMG_7884', 0, 40, 2, [('C', (255, 0, 0))], HJ / '7884_c0-c40_c2.jpg')
    hoja_fuente('IMG_8002', 0, 30, 2, [('E', (255, 0, 0))], HJ / '8002_c0-c30_c2.jpg')
    hoja_fuente('IMG_4631', 120, 200, 4, [], HJ / '4631_c120-c200_c4.jpg')


# =====================================================================================================
# etapa medir · dónde están las remeras (y la persona de 7884) en cada cuadro de fuente usado
# =====================================================================================================
# Referencias medidas a mano sobre cuadros a resolución completa con grilla (hojas/grilla_*.jpg; coordenadas de la toma
# rotada, con margen de ≈ 10–20 px). El seguimiento lleva esas cajas a cada cuadro: semejanza (escala + traslación) de una
# plantilla de rocas y remeras (gris a 1/4) anclada SIEMPRE al cuadro de referencia (sin deriva acumulada), búsqueda por
# correlación normalizada (FFT) ±24 px alrededor de la predicción y escalas ±1,2 % alrededor de la anterior, pico con
# interpolación parabólica. Cada toma se valida contra una segunda medición a mano (CONTROL_MANUAL).
OBJETOS = {   # toma: (cuadros, cuadro de referencia, plantilla x0, y0, x1, y1, {objeto: caja x0, y0, x1, y1})
    'IMG_7895': ((0, 41), 0, (600, 1450, 1900, 2150), {'remeras': (740, 1560, 1710, 1990)}),
    'IMG_7896': ((0, 176), 0, (150, 1950, 1400, 2800), {'remeras': (310, 2100, 1180, 2610)}),
    'IMG_7884': ((0, 29), 0, (500, 1500, 2100, 2800), {'persona': (1080, 1590, 2160, 3430), 'blanca': (640, 2090, 1340, 2610)}),
    'IMG_8002': ((0, 20), 20, (250, 1650, 2150, 2700), {'blanca': (345, 1715, 2160, 3840)}),
    'IMG_4631': ((129, 188), 188, (0, 550, 1080, 1400), {'remeras': (120, 690, 1080, 1270)}),
}
CONTROL_MANUAL = {   # segunda lectura a mano (grillas): borde superior e izquierdo esperados
    'IMG_7895': (41, 'remeras', (670, 1610, 1600, 2000)),
    'IMG_7896': (176, 'remeras', (190, 1670, 1750, 2590)),
    'IMG_7884': (29, 'persona', (1270, 1420, 2160, 3700)),
    'IMG_8002': (0, 'blanca', (700, 1850, 1640, 2780)),
    'IMG_4631': (129, 'remeras', (130, 1015, 1080, 1700)),
}


def _ncc(img, tpl):
    from scipy.signal import fftconvolve
    t = tpl - tpl.mean(); tn = math.sqrt(float((t * t).sum())) + 1e-9
    k = np.ones(tpl.shape)
    num = fftconvolve(img, t[::-1, ::-1], mode='valid')
    s1 = fftconvolve(img, k, mode='valid'); s2 = fftconvolve(img * img, k, mode='valid')
    var = np.maximum(s2 - s1 * s1 / tpl.size, 1e-6)
    return num / (np.sqrt(var) * tn)


def _parab(a, b, c):
    d = a - 2 * b + c
    return 0.0 if abs(d) < 1e-9 else 0.5 * (a - c) / d


def seguir(toma):
    from scipy import ndimage as nd
    (n0, n1), nref, tb, objs = OBJETOS[toma]
    nw, nh = V.TOMAS[toma]['nat']
    q = 4 if nw > 1080 else 2
    w4, h4 = nw // q, nh // q
    fr = U.leer(V._src(toma), w4, h4, n0=n0, n1=n1, vf_pre=V.color(toma)).astype(np.float32) @ np.array([.2126, .7152, .0722], np.float32)
    x0, y0, x1, y1 = [v / q for v in tb]
    ref = fr[nref - n0]
    tx0, ty0 = int(round(x0)), int(round(y0))
    tpl0 = ref[ty0:int(round(y1)), tx0:int(round(x1))]
    th, tw = tpl0.shape
    res = {nref: dict(s=1.0, x=float(tx0), y=float(ty0), ncc=1.0)}
    Rs = 24
    for orden in (range(nref + 1, n1 + 1), range(nref - 1, n0 - 1, -1)):
        prev = res[nref]
        for n in orden:
            img = fr[n - n0]
            mejor = None
            for ds in np.arange(-0.012, 0.0121, 0.003):
                s = prev['s'] * (1 + ds)
                tpl = nd.zoom(tpl0, s, order=1)
                ex, ey = prev['x'] - (tpl.shape[1] - tw * prev['s']) / 2, prev['y'] - (tpl.shape[0] - th * prev['s']) / 2
                ax, ay = int(round(ex)) - Rs, int(round(ey)) - Rs
                bx, by = ax + tpl.shape[1] + 2 * Rs, ay + tpl.shape[0] + 2 * Rs
                cx0, cy0 = max(ax, 0), max(ay, 0)
                cx1, cy1 = min(bx, w4), min(by, h4)
                zona = img[cy0:cy1, cx0:cx1]
                if zona.shape[0] < tpl.shape[0] + 2 or zona.shape[1] < tpl.shape[1] + 2:
                    # la plantilla escalada no entra (borde): se recorta la plantilla al cuadro
                    continue
                c = _ncc(zona, tpl)
                iy, ix = np.unravel_index(int(np.argmax(c)), c.shape)
                v = float(c[iy, ix])
                if mejor is None or v > mejor[0]:
                    sx = _parab(c[iy, ix - 1], v, c[iy, ix + 1]) if 0 < ix < c.shape[1] - 1 else 0.0
                    sy = _parab(c[iy - 1, ix], v, c[iy + 1, ix]) if 0 < iy < c.shape[0] - 1 else 0.0
                    mejor = (v, s, cx0 + ix + sx, cy0 + iy + sy, tpl.shape)
            v, s, mx, my, shp = mejor
            # (mx, my) = esquina de la plantilla escalada por nd.zoom (tamaño entero); esquina «exacta» = misma (zoom ancla 0,0)
            res[n] = dict(s=float(s), x=float(mx), y=float(my), ncc=round(v, 4))
            prev = res[n]
    out = {}
    for n in range(n0, n1 + 1):
        r = res[n]
        cajas = {}
        for nombre, (a0, b0, a1, b1) in objs.items():
            f = lambda X, Y: (((X / q - tx0) * r['s'] + r['x']) * q, ((Y / q - ty0) * r['s'] + r['y']) * q)
            p0, p1 = f(a0, b0), f(a1, b1)
            cajas[nombre] = [round(max(0, p0[0]), 1), round(max(0, p0[1]), 1), round(min(nw, p1[0]), 1), round(min(nh, p1[1]), 1)]
        out[n] = dict(escala=round(r['s'], 4), ncc=r['ncc'], cajas=cajas)
    return out


def etapa_medir():
    MED.mkdir(parents=True, exist_ok=True)
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 22)
    rep = {}
    for toma in OBJETOS:
        t0 = time.time()
        tr = seguir(toma)
        nc, nombre, man = CONTROL_MANUAL[toma]
        got = tr[nc]['cajas'][nombre]
        rep[toma] = dict(por_cuadro=tr, control_manual=dict(cuadro=nc, objeto=nombre, a_mano=man, seguido=got,
                                                            dif_px=[round(g - m_, 1) for g, m_ in zip(got, man)]),
                         ncc_min=min(v['ncc'] for v in tr.values()))
        print(toma, 'ncc mín', rep[toma]['ncc_min'], 'control', rep[toma]['control_manual'], f'{time.time() - t0:.0f}s', flush=True)
        # hoja de control del seguimiento: cuadros cada 3 con las cajas seguidas
        (n0, n1), *_ = OBJETOS[toma]
        nw, nh = V.TOMAS[toma]['nat']
        ancho = 216; alto = round(ancho * nh / nw); s = ancho / nw
        ns = list(range(n0, n1 + 1, 3)) + ([n1] if (n1 - n0) % 3 else [])
        fr = {n: U.leer(V._src(toma), ancho, alto, n0=n, n1=n, vf_pre=V.color(toma))[0] for n in ns}
        tiles = []
        for n in ns:
            im = Image.fromarray(fr[n]); d = ImageDraw.Draw(im)
            for nombre_, c in tr[n]['cajas'].items():
                d.rectangle([c[0] * s, c[1] * s, c[2] * s, c[3] * s], outline=(0, 255, 0), width=2)
            d.rectangle([0, 0, 120, 24], fill=(0, 0, 0)); d.text((3, 1), f'c{n} {tr[n]["ncc"]:.2f}', font=fnt, fill=(255, 255, 0))
            tiles.append(im)
        cols = 10; rows = math.ceil(len(tiles) / cols)
        Wd = Image.new('RGB', (cols * (ancho + 2), rows * (alto + 2)), (30, 30, 30))
        for i, t in enumerate(tiles):
            Wd.paste(t, ((i % cols) * (ancho + 2), (i // cols) * (alto + 2)))
        Wd.save(MED / f'seguimiento_{toma}.jpg', quality=88)
    jdump(rep, MED / 'seguimiento.json')


# =====================================================================================================
# etapa planos · cortes, encuadres y barridos del guion (intermedios x264 crf 12, como video.py)
# =====================================================================================================
def etapa_planos():
    P.mkdir(parents=True, exist_ok=True)
    reg = []
    for p in plan_planos():
        out = P / f"{p['id']}.mp4"
        if p['tipo'] == 'z':
            z = [zc(c) for c in p['v']]
            r = U.plano_z(p['toma'], p['n0'], [a[0] for a in z], [a[1] for a in z], [a[2] for a in z], out, caja=FULL,
                          post=p.get('post'))
        elif p['tipo'] == 'n':
            r = U.plano_n(p['toma'], p['n0'], p['nf'], out, caja=p['caja'], post=p.get('post'))
        else:
            V.sh(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}', '-frames:v',
                  str(p['nf']), *V.ENC_INT, str(out)])
            r = dict(toma=None, cuadros=p['nf'], salida=str(out))
        r.update(id=p['id'], m0=p['m0'], post=p.get('post'), cajas_guion=p.get('v') and sorted({str(c) for c in p['v']}))
        reg.append(r)
        print(p['id'], r['cuadros'], flush=True)
    n = V.unir(reg, T / 'v4_base0.mp4')
    assert n == NF, n
    jdump(dict(cuadros=n, planos=reg), T / 'planos.json')
    print('total', n)


# =====================================================================================================
# etapa grado · B/N (croma neutro) con exposición por tramo, oscuro del giro y negro 12,50–12,60 (x264 sin pérdida)
# =====================================================================================================
def lut_exposicion(k):
    """luma 8 bits (rango tv) → luma con la exposición multiplicada por k en luz lineal (gamma 2,4); con k > 1 un hombro
    (tanh desde 0,8) evita recortar la espuma."""
    v = np.clip((np.arange(256) - 16) / 219, 0, 1)
    L = v ** 2.4 * k
    if k > 1:
        kn = 0.8
        L = np.where(L > kn, kn + (1 - kn) * np.tanh((L - kn) / (1 - kn)), L)
    return np.clip(np.round(16 + 219 * L ** (1 / 2.4)), 16, 235).astype(np.uint8)


def lut_mult(m):
    v = np.clip((np.arange(256) - 16) / 219, 0, 1)
    return np.clip(np.round(16 + 219 * v * m), 16, 235).astype(np.uint8)


def etapa_grado():
    src, dst = T / 'v4_base0.mp4', T / 'v4_base.mp4'
    ys, cs = W * H, (W // 2) * (H // 2)
    dec = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(src), '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-']),
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{W}x{H}', '-r', str(FPS),
                                 '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                                 '-i', '-', '-c:v', 'libx264', '-qp', '0', '-preset', 'veryfast', '-threads', '2', '-pix_fmt', 'yuv420p',
                                 '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
                                 str(dst)]), stdin=subprocess.PIPE)
    luts = {}
    filas = []
    for n in range(NF):
        b = dec.stdout.read(ys + 2 * cs)
        assert len(b) == ys + 2 * cs, n
        Y = np.frombuffer(b[:ys], np.uint8).reshape(H, W); Cb = b[ys:ys + cs]; Cr = b[ys + cs:]
        modo, k = grado_de(n)
        if modo == 'negro':
            Y2 = np.full_like(Y, 16); c2 = bytes([128]) * (2 * cs)
        elif modo == 'color':
            Y2 = Y; c2 = Cb + Cr
        else:
            key = (modo, k)
            if key not in luts:
                luts[key] = lut_exposicion(k) if modo == 'bn' else lut_mult(k)
            Y2 = luts[key][Y]; c2 = bytes([128]) * (2 * cs)
        enc.stdin.write(Y2.tobytes()); enc.stdin.write(c2)
        cb = np.frombuffer(c2[:cs], np.uint8)
        filas.append(dict(cuadro=n, modo=modo, k=None if k is None else round(k, 4), luma_media_antes=round(float(Y.mean()), 2),
                          luma_media_despues=round(float(Y2.mean()), 2), croma_max_desvio=int(np.abs(cb.astype(int) - 128).max())))
    dec.stdout.close(); dec.wait(); enc.stdin.close(); enc.wait()
    assert enc.returncode == 0
    n = int(U.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames',
                   '-of', 'csv=p=0', str(dst)]).decode().strip())
    assert n == NF, n
    jdump(dict(metodo=('B/N: croma 128 (luma BT.709 de la toma ya pasada a SDR). E−/E+: exposición ×k en luz lineal (gamma 2,4) '
                       'con hombro tanh desde 0,8 para k > 1. Giro: luma ×0,35 (rampa c243–c246 desde el nivel de E−). Negro: '
                       'Y 16, croma 128. Color: sin tocar.'), por_cuadro=filas), MED / 'grado.json')
    print('grado ok', n)


# =====================================================================================================
# textos · texto cinético (guion: palabra por palabra, una cada 3 c, la última cae en el golpe)
# =====================================================================================================
FS_PASO, FS_GANCHO, FS_VUELVE, FS_NOCAUT, FS_CITA = 86, 100, 116, 102, 96   # mayúscula ≈ 62 / 73 / 84 / 74 / 67 px
LH_CHIP = round(FS_PASO * 1.42)                                              # alto de la caja de un renglón: 122 px
LH_CITA = round(FS_CITA * 1.14)
CELESTE = '#7EB2DE'                                                          # celeste de marca (126, 178, 222)
Y_CITA = 480
Y_C2 = 420                                                                    # c2 en 3 renglones (ver desvíos)
FRASES = [
    # tipo, id, cuadros (inclusive), y (borde superior), renglones, cadencia (c por palabra), golpe del último, acentos
    dict(id='rotulo', tipo='label', n=(0, 41), y=270, lineas=[['ILIA', 'TOPURIA', '·', '14/06/2026']], cad=0,
         acento=['14/06/2026'], pop=False, guion='ILIA TOPURIA · 14/06/2026'),
    dict(id='gancho', tipo='chip', fs=FS_GANCHO, n=(0, 17), y=330, lineas=[['Primera', 'derrota.']], cad=0, pop=False,
         guion='Primera derrota.'),
    dict(id='vuelve', tipo='grande', fs=FS_VUELVE, n=(18, 41), y=352, lineas=[['¿Vuelve?']], cad=3, golpe='slam',
         guion='¿Vuelve?'),
    dict(id='e1', tipo='chip', n=(42, 65), y=300, lineas=[['Su', 'esquina'], ['paró', 'la', 'pelea.']], cad=3, golpe='grave',
         guion='Su esquina paró la pelea.'),
    dict(id='e2', tipo='chip', n=(66, 89), y=300, lineas=[['Órbitas,', 'tabique,', 'pie,'], ['según', 'él.']], cad=3,
         golpe='grave', guion='Órbitas, tabique, pie,\\Nsegún él.'),
    dict(id='e3', tipo='chip', n=(90, 116), y=300, lineas=[['Dijeron', 'que', 'no'], ['iba', 'a', 'volver'], ['a', 'ser', 'el', 'mismo.']],
         cad=2, golpe='grave', guion='Dijeron que no iba a volver\\Na ser el mismo.'),
    dict(id='p1a', tipo='chip', n=(117, 146), y=300, lineas=[['2022:', 'lo', 'tiraron.']], cad=3, golpe='agudo', acento=['2022:'],
         guion='2022: lo tiraron.'),
    dict(id='p1b', tipo='chip', n=(132, 146), y=300 + LH_CHIP + 14, lineas=[['Se', 'levantó.', 'Ganó.']], cad=3, golpe='agudo',
         guion='Se levantó. Ganó.'),
    dict(id='p2a', tipo='chip', n=(147, 176), y=300, lineas=[['2024:', 'le', 'prometieron'], ['humillarlo.']], cad=3,
         acento=['2024:'], guion='2024: le prometieron humillarlo.'),
    dict(id='p2b', tipo='grande', fs=FS_NOCAUT, n=(162, 176), y=300 + 2 * LH_CHIP + 26, lineas=[['Nocaut.']], cad=3,
         golpe='impacto', guion='Nocaut.'),
    dict(id='e4', tipo='chip', n=(177, 200), y=300, lineas=[['Septiembre:'], ['no', 'vuelve', 'en', '2026.']], cad=3,
         golpe='grave', acento=['Septiembre:'], guion='Septiembre: no vuelve en 2026.'),
    dict(id='p3', tipo='chip', n=(201, 221), y=300, lineas=[['Noviembre:'], ['escribe', 'que', 'vuelve.']], cad=3, golpe='agudo',
         acento=['Noviembre:'], guion='Noviembre: escribe que vuelve.'),
    dict(id='e5', tipo='chip', n=(222, 242), y=300, lineas=[['Sin', 'pelea', 'confirmada.']], cad=3, golpe='grave',
         guion='Sin pelea confirmada.'),
    dict(id='c1', tipo='cita', fs=FS_CITA, n=(243, 284), y=Y_CITA, lineas=[['“…no', 'puedo', 'prometer'], ['ningún', 'resultado.”']],
         cad=3, guion='“…no puedo prometer\\Nningún resultado.”'),
    dict(id='c2', tipo='cita', fs=FS_CITA, n=(285, 374), y=Y_C2,
         lineas=[['“Sí', 'puedo', 'prometer', 'algo'], ['que', 'depende'], ['exclusivamente', 'de', 'mí:”']], cad=3, toques=True,
         guion='“Sí puedo prometer algo\\Nque depende exclusivamente de mí:”'),
    dict(id='c3', tipo='cita', fs=FS_CITA, n=(327, 374), y=Y_C2 + 3 * LH_CITA + 26,
         lineas=[['“no', 'me', 'van', 'a', 'ver'], ['dejar', 'de', 'intentarlo.”']], cad=3, toques=True, golpe='sub',
         guion='“no me van a ver\\Ndejar de intentarlo.”'),
    dict(id='atrib', tipo='atrib', fs=36, n=(327, 374), y=Y_C2 + 5 * LH_CITA + 26 + 36,
         lineas=[['—', 'Ilia', 'Topuria,', '«Este', 'soy', 'yo»']], cad=0, guion='— Ilia Topuria, «Este soy yo»'),
    dict(id='reeng', tipo='chip', n=(378, 416), y=300, lineas=[['¿Y', 'vos,'], ['qué', 'prometés?']], cad=3, golpe='acento',
         guion='¿Y vos, qué prometés?'),
]
CITAS = ['c1', 'c2', 'c3']
TEXTO_ULTIMO = 416
# sacudida del bloque de texto en el golpe (px): amplitud por tipo; patrón de 5 cuadros
SACUDIDA = {'grave': 9, 'agudo': 6, 'impacto': 16, 'sub': 5, 'slam': 7, 'acento': 4}
GOLPES_EXTRA = [(1, 6, 'impacto del gancho (c0 queda quieto para la portada)'), (378, 10, 'drop del reenganche')]


def palabras(f):
    """[(texto, cuadro de aparición, renglón, índice en renglón)] de una frase."""
    out, k = [], 0
    for i, ln in enumerate(f['lineas']):
        for j, w in enumerate(ln):
            out.append((w, f['n'][0] + f['cad'] * k, i, j)); k += 1
    return out


def golpe_de(f):
    return palabras(f)[-1][1] if f.get('golpe') else None


def eventos_texto():
    """golpes (cuadro, tipo, frase) y toques por palabra, desde FRASES (fuente única para imagen y sonido)."""
    golpes = [(golpe_de(f), f['golpe'], f['id']) for f in FRASES if f.get('golpe')]
    toques = []
    for f in FRASES:
        if f.get('toques'):
            ps = palabras(f)
            toques += [p[1] for p in (ps[:-1] if f.get('golpe') else ps)]
    return sorted(golpes), sorted(toques)


CSS_TEXTO = """
@font-face{font-family:'IDS';src:url('file:///usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf');font-weight:600}
@font-face{font-family:'IDX';src:url('file:///usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf');font-weight:800}
@font-face{font-family:'ISB';src:url('file:///usr/share/fonts/opentype/inter/Inter-SemiBold.otf');font-weight:600}
@font-face{font-family:'IM';src:url('file:///usr/share/fonts/opentype/inter/Inter-Medium.otf');font-weight:500}
@font-face{font-family:'IS';src:url('file://%(F)s/InstrumentSerif-Regular.ttf')}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:transparent}
#raiz{position:absolute;left:0;top:0;width:1080px;height:1920px}
.frase{position:absolute;left:0;right:0;text-align:center;display:none}
.linea{display:block;white-space:nowrap;font-size:0;line-height:0}
.w{display:inline-block;vertical-align:top;font-size:var(--fs);font-feature-settings:'kern','liga'}
.g{display:inline-block;transform-origin:50%% 58%%}
.chip .w{background:#141414;color:#FFFFFF;font-family:'IDS';font-weight:600;line-height:1;margin-left:-1px;
  padding:calc(var(--fs)*0.21) calc(var(--fs)*0.15)}
.chip .w.ini{margin-left:0}
.chip .w.flash{background:#FFFFFF;color:#141414} .chip .w.flash2{background:#CFCFCF;color:#141414}
.chip .w.ini{padding-left:calc(var(--fs)*0.34)} .chip .w.fin{padding-right:calc(var(--fs)*0.34)}
.label .w{background:#141414;color:#FFFFFF;font-family:'ISB';font-weight:600;line-height:1;letter-spacing:.06em;margin-left:-1px;
  padding:10px calc(var(--fs)*0.16) 10px calc(var(--fs)*0.16)}
.label .w.ini{padding-left:22px} .label .w.fin{padding-right:calc(22px - .06em)}
.w.ac{color:%(CEL)s} .chip .w.ac.flash,.chip .w.ac.flash2{color:#141414}
.grande .w{position:relative;z-index:0;font-family:'IDX';font-weight:800;color:#FFFFFF;line-height:1;padding:0 .1em}
.grande .g{position:relative;z-index:0}
.grande .g::before{content:attr(data-t);position:absolute;left:0;top:0;z-index:-1;color:#000;
  -webkit-text-stroke:7px rgba(0,0,0,.85);text-shadow:0 0 40px rgba(0,0,0,.5),0 4px 22px rgba(0,0,0,.6)}
.cita .linea{font-size:var(--fs);line-height:%(LHC)dpx;height:%(LHC)dpx}
.cita .w{font-family:'IS';color:#F6F5F1;line-height:%(LHC)dpx;text-shadow:0 2px 18px rgba(0,0,0,.6)}
.atrib .linea{font-size:var(--fs);line-height:44px}
.atrib .w{font-family:'IM';font-weight:500;color:rgba(255,255,255,.86);letter-spacing:.02em;
  text-shadow:0 1px 10px rgba(0,0,0,.6)}
"""

JS_TEXTO = r"""
const SPEC = __SPEC__;
const SX = [0.9, -0.7, 0.45, -0.2, 0.05], SY = [-0.45, 0.6, -0.35, 0.15, 0];
const raiz = document.getElementById('raiz');
for (const f of SPEC.frases) {
  const d = document.createElement('div'); d.className = 'frase ' + f.tipo; d.style.top = f.y + 'px';
  d.style.setProperty('--fs', f.fs + 'px'); f.el = d; f.ws = [];
  f.lineas.forEach((ln, i) => {
    const l = document.createElement('div'); l.className = 'linea';
    ln.forEach((w, j) => {
      const s = document.createElement('span'); s.className = 'w';
      const g = document.createElement('span'); g.className = 'g'; g.textContent = w.t; g.dataset.t = w.t; s.appendChild(g);
      if (j === 0) s.classList.add('ini'); if (j === ln.length - 1) s.classList.add('fin');
      if (w.ac) s.classList.add('ac');
      l.appendChild(s); f.ws.push({el: s, g, a: w.a, t: w.t, i, last: w.last});
      if (f.tipo === 'cita' || f.tipo === 'atrib') l.appendChild(document.createTextNode(' '));
    });
    d.appendChild(l);
  });
  raiz.appendChild(d);
}
window.cargarFuentes = async () => {
  const muestra = 'AaÁáÉéÍíÓóÚúÑñ¿?…“”«»—·:,.0123456789';
  await Promise.all(['600 86px IDS', '800 116px IDX', '600 40px ISB', '500 36px IM', '96px IS'].map(f => document.fonts.load(f, muestra)));
};
function pop(f, w, age) {
  if (f.pop === false) return [1, 1, 0, 0];
  if (f.tipo === 'chip' || f.tipo === 'label') { const S = w.last && f.golpe ? [1.16, 1.06, 1.015] : [0.80, 1.05, 1.0]; return [age < 3 ? S[age] : 1, 1, 0, 0]; }
  if (f.tipo === 'grande') { const S = [1.55, 1.10, 0.985], B = [6, 1.5, 0], O = [0.85, 1, 1]; return age < 3 ? [S[age], O[age], B[age], 0] : [1, 1, 0, 0]; }
  if (f.tipo === 'cita' && w.last && f.golpe) { w.g.style.transformOrigin = '0% 70%'; const S = [1.06, 1.02, 1.0], O = [0.92, 1, 1]; return age < 3 ? [S[age], O[age], 0, 0] : [1, 1, 0, 0]; }
  if (f.tipo === 'cita') { const O = [0.30, 0.70, 0.92], TY = [14, 6, 2], B = [4, 1.5, 0]; return age < 3 ? [1, O[age], B[age], TY[age]] : [1, 1, 0, 0]; }
  if (f.tipo === 'atrib') return [1, Math.min(1, (age + 1) / 9), 0, 0];
  return [1, 1, 0, 0];
}
window.frame = n => {
  let dx = 0, dy = 0;
  for (const g of SPEC.golpes) { const k = n - g.n; if (k >= 0 && k < 5) { dx += g.a * SX[k]; dy += g.a * SY[k]; } }
  raiz.style.transform = `translate(${dx.toFixed(2)}px,${dy.toFixed(2)}px)`;
  for (const f of SPEC.frases) {
    const vis = n >= f.n[0] && n <= f.n[1];
    f.el.style.display = vis ? 'block' : 'none';
    if (!vis) continue;
    for (const w of f.ws) {
      const age = n - w.a;
      if (age < 0) { w.el.style.visibility = 'hidden'; continue; }
      const [s, o, b, ty] = pop(f, w, age);
      w.el.style.visibility = 'visible';
      w.el.style.opacity = o;
      w.g.style.transform = `translateY(${ty}px) scale(${s})`;
      w.g.style.filter = b ? `blur(${b}px)` : 'none';
      const fl = f.tipo === 'chip' && w.last && f.golpe && f.pop !== false;
      w.el.classList.toggle('flash', fl && age === 0);
      w.el.classList.toggle('flash2', fl && age === 1);
    }
  }
};
window.visible = n => SPEC.frases.filter(f => n >= f.n[0] && n <= f.n[1]).map(f => ({id: f.id,
  lineas: f.lineas.map(ln => ln.filter(w => w.a <= n).map(w => w.t).join(' ')),
  completa: f.ws.every(w => w.a <= n)}));
"""


def spec_texto():
    golpes, _ = eventos_texto()
    fr = []
    for f in FRASES:
        ps = palabras(f); ult = ps[-1][1]
        lineas = [[] for _ in f['lineas']]
        for w, a, i, j in ps:
            lineas[i].append(dict(t=w, a=a, ac=w in f.get('acento', []), last=(a == ult and (i, j) == ps[-1][2:])))
        fr.append(dict(id=f['id'], tipo=f['tipo'], n=list(f['n']), y=f['y'], fs=f.get('fs', FS_PASO if f['tipo'] == 'chip' else 40),
                       lineas=lineas, pop=f.get('pop', True), golpe=f.get('golpe')))
    gs = [dict(n=n, a=SACUDIDA[t]) for n, t, _ in golpes if n > 0] + [dict(n=n, a=a) for n, a, _ in GOLPES_EXTRA]
    return dict(frases=fr, golpes=gs)


def etapa_textos():
    TX.mkdir(parents=True, exist_ok=True)
    sp = spec_texto()
    css = CSS_TEXTO % dict(F=L2.FUENTES, CEL=CELESTE, LHC=LH_CITA)
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body><div id="raiz"></div>'
            f'<script>{JS_TEXTO.replace("__SPEC__", json.dumps(sp, ensure_ascii=False))}</script></body></html>')
    (TX / 'texto_v4.html').write_text(html, encoding='utf-8')
    jdump(sp, TX / 'spec_texto.json')
    sec = TX / 'cuadros'
    if sec.exists():
        shutil.rmtree(sec)                              # intermedio propio (TRABAJO/life2/v4): se rehace entero
    trabajo = dict(html=str(TX / 'texto_v4.html'), outdir=str(sec), n0=0, n1=TEXTO_ULTIMO, w=W, h=H, dump=str(TX / 'visible.json'))
    (TX / '_trabajo.json').write_text(json.dumps(trabajo, indent=1))
    subprocess.run(nice(['node', str(R / 'scripts/life/life_v4_render.js'), str(TX / '_trabajo.json')]), check=True)
    n = len(list(sec.glob('f_*.png')))
    assert n == TEXTO_ULTIMO + 1, n
    print('textos', n)


# =====================================================================================================
# etapa placa · cierre del sistema Roccé Life (CSS de life_v2: degradé + frase Instrument Serif + firma con logo original)
# =====================================================================================================
PLACA = dict(frase_html='Seguí al <em>equipo</em>.', frase_txt='Seguí al equipo.', fs=100, top_frase=300,
             grad=(760, 0.62, (12, 18, 26)), logo=96, ffs=30, top_firma=450)     # = life_v2.PLACA (mismo CTA, guion)
PLACA_CUADROS = dict(frase=(419, 476), firma=(429, 476))   # después de los 2 cuadros del barrido; firma +10 c (como V2)


def etapa_placa():
    PL.mkdir(parents=True, exist_ok=True)
    t = dict(F=L2.FUENTES, fs=PLACA['fs'], logo=PLACA['logo'], radio=round(PLACA['logo'] * 0.11), ffs=PLACA['ffs'])
    alto, op, (r, g, b) = PLACA['grad']
    grad = (f'<div class="grad" style="height:{alto}px;background:linear-gradient(to bottom,rgba({r},{g},{b},{op}) 0%,'
            f'rgba({r},{g},{b},{op * 0.55:.3f}) 45%,rgba({r},{g},{b},0) 100%)"></div>')
    docs = {'cierre_frase': f'{grad}<div class="frase" style="top:{PLACA["top_frase"]}px">{PLACA["frase_html"]}</div>',
            'cierre_firma': (f'<div class="firma" style="top:{PLACA["top_firma"]}px"><img src="file://{L2.LOGO}">'
                             f'<span>ROCCÉ LIFE</span></div>')}
    trabajos = []
    for nombre, cuerpo in docs.items():
        h = PL / f'{nombre}.html'
        h.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{L2.CSS_PLACA % t}</style></head>'
                     f'<body>{cuerpo}</body></html>', encoding='utf-8')
        trabajos.append(dict(html=str(h), out=str(PL / f'{nombre}.png'), w=W, h=H))
    (PL / '_trabajos.json').write_text(json.dumps(trabajos, indent=1))
    subprocess.run(nice(['node', str(R / 'scripts/life/life_v2_render.js'), str(PL / '_trabajos.json')]), check=True)
    from PIL import Image
    rep = {}
    for tr in trabajos:
        im = Image.open(tr['out']); a = np.asarray(im)
        assert im.size == (W, H) and im.mode == 'RGBA', (im.size, im.mode)
        al = a[..., 3]; filas = np.nonzero((al > 8).any(1))[0]; cols = np.nonzero((al > 8).any(0))[0]
        rep[Path(tr['out']).name] = dict(md5_pixeles=hashlib.md5(a.tobytes()).hexdigest(),
                                         caja_alfa_gt8=[int(cols.min()), int(filas.min()), int(cols.max()), int(filas.max())])
    a = np.asarray(Image.open(PL / 'cierre_frase.png')).astype(int)
    ys, xs = np.nonzero((a[..., 3] > 200) & (a[..., :3].min(-1) > 200))
    rep['frase_letras'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    a = np.asarray(Image.open(PL / 'cierre_firma.png')).astype(int)
    ys, xs = np.nonzero(a[..., 3] > 8)
    rep['firma'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    # ficha del logo (96 × 96, #FEFEFE): caja de los píxeles opacos casi blancos dentro de la firma
    ys, xs = np.nonzero((a[..., 3] > 250) & (a[..., :3].min(-1) >= 250))
    rep['ficha_logo'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    jdump(rep, PL / 'placa.json')
    print(json.dumps(rep, ensure_ascii=False))


# =====================================================================================================
# etapa audio · ambiente real + sonidos de la jugada (ambas mezclas) + música TEMP propia (solo la completa)
# =====================================================================================================
def _s():
    import sonido as S_
    return S_


def campana_ring(m, t, g=0.30):
    """campana de ring sintetizada: parciales inarmónicos de campana (Do6) con batimiento, golpe metálico; dos toques."""
    S_ = _s(); L = int(2.6 * SR); tt = np.arange(L) / SR
    f0 = 1046.5
    s = np.zeros(L)
    for r, a, d in ((1.0, 1.0, 1.5), (1.004, 0.55, 1.3), (2.0, 0.35, 0.9), (2.76, 0.55, 0.7), (3.91, 0.30, 0.45),
                    (5.40, 0.22, 0.30), (6.80, 0.12, 0.20)):
        s += a * np.sin(2 * np.pi * f0 * r * tt + 0.7 * r) * np.exp(-tt / d)
    s += 0.6 * S_.filt(S_.ruido(L), 'high', 3500) * np.exp(-tt / 0.004)
    s /= np.abs(s).max()
    for k, dt in enumerate((0.0, 0.17)):
        m.put('fx', s, t + dt, g * (1.0 if k == 0 else 0.85))
        m.rev(s * g * 0.30, t + dt, seg=1.8)
    m.log(t, 'campana de ring (dos toques)')


def golpe_grave(m, t, g=0.95):
    S_ = _s(); L = int(0.8 * SR); tt = np.arange(L) / SR
    f = 44 + 96 * np.exp(-tt / 0.045)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.24)
    s += 0.55 * S_.filt(S_.ruido(L), 'low', 700) * np.exp(-tt / 0.035)
    s += 0.18 * S_.filt(S_.ruido(L), 'band', [1800, 5000]) * np.exp(-tt / 0.003)
    s = S_.satur(s, 1.7); s /= np.abs(s).max()
    m.put('fx', s, t, g); m.rev(s * g * 0.22, t, seg=1.6); m.log(t, 'golpe grave')


def golpe_agudo(m, t, g=0.55):
    S_ = _s(); L = int(0.5 * SR); tt = np.arange(L) / SR
    s = S_.filt(S_.ruido(L), 'band', [1600, 9000]) * np.exp(-tt / 0.035)
    s += 0.45 * np.sin(2 * np.pi * 1760 * tt) * np.exp(-tt / 0.07) + 0.25 * np.sin(2 * np.pi * 2640 * tt) * np.exp(-tt / 0.05)
    s += 0.5 * np.sin(2 * np.pi * 190 * tt) * np.exp(-tt / 0.04)
    s = S_.satur(s, 1.4); s /= np.abs(s).max()
    m.put('fx', s, t, g); m.rev(s * g * 0.30, t, seg=1.3); m.log(t, 'golpe agudo')


def sub_golpe(m, t, g=0.60):
    S_ = _s(); L = int(1.3 * SR); tt = np.arange(L) / SR
    f = 73.4 + (98 - 73.4) * np.exp(-tt / 0.06)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.55)
    s = S_.satur(1.4 * s, 2.5) * 0.8
    s += 0.4 * S_.filt(S_.ruido(L), 'low', 400) * np.exp(-tt / 0.03)
    s /= np.abs(s).max()
    m.put('fx', s, t, g); m.rev(s * g * 0.2, t, seg=2.2); m.log(t, 'sub-golpe')


def latido(m, t, g=0.8, doble=True):
    m.bombo(t, g, f0=75, f1=42, dec=0.28)
    if doble:
        m.bombo(t + 0.17, g * 0.55, f0=65, f1=40, dec=0.22)
    m.log(t, 'latido' + ('' if doble else ' (simple)'))


def tf(n):
    return n / FPS


CORTES_IMG = [18, 42, 66, 90, 117, 147, 177, 201, 222, 243, 285, 375, 378, 417]
AMB = [  # (toma, segundo de fuente, t0, t1, dB, fundidos)
    ('IMG_7895', 0.000, 0.000, 1.400, 0.0, {}),
    ('IMG_7896', 0.000, 1.400, 3.900, 8.0, {}),
    ('IMG_7884', 0.000, 3.900, 4.900, 8.0, {}),
    ('IMG_7896', 4.900, 4.900, 5.900, 8.0, {}),
    ('IMG_7896', 2.500, 5.900, 7.400, 8.0, {}),
    ('IMG_8002', 0.000, 7.400, 8.100, 8.0, {}),
    ('IMG_7896', 0.000, 8.100, 12.530, 11.0, dict(fin_fade=0.08)),       # «solo mar» desde el corte de la música
    ('IMG_7895', 0.000, 12.600, 13.900, 0.0, dict(ini_fade=0.005)),
    ('IMG_4631', 4.300, 13.900, DUR, -3.0, {}),
]


def ambientes(m):
    for toma, s0, t0, t1, g, kw in AMB:
        m.ambiente(toma, s0, t0, t1, g, **kw)


def sfx_a(m):
    """hasta el corte de 8,10: gancho y golpes de la cadena (los del texto salen de FRASES)."""
    m.impacto(0.0, 0.70); campana_ring(m, 0.0)
    m.barrido(0.62, 0.30, 0.12)                                       # entra «¿Vuelve?» (c18)
    golpes, _ = eventos_texto()
    cortado = False
    for n, tipo, _id in golpes:
        t = tf(n)
        if t >= 8.1:
            continue
        if t > 5.9 and not cortado:
            # corte seco en 5,90 (paso 8): la cola del «Nocaut.» (impacto de 5,40 con reverberación de 2,4 s) baja 18 dB
            # antes de poner los golpes siguientes (control v01: el golpe grave de 6,30 subía solo 4,5 dB en 35–200 Hz)
            g = np.ones(m.N); i0, i1 = int(5.90 * SR), int(5.97 * SR)
            g[i0:i1] = np.linspace(1, 10 ** (-18 / 20), i1 - i0); g[i1:] = 10 ** (-18 / 20)
            m.pistas['fx'] *= g[:, None]; m.log(5.90, 'corte seco de la cola del Nocaut (−18 dB)')
            cortado = True
        if tipo == 'grave':
            golpe_grave(m, t)
        elif tipo == 'agudo':
            golpe_agudo(m, t)
        elif tipo == 'impacto':
            m.impacto(t, 0.80); golpe_grave(m, t, 0.55)                # «Nocaut.» con el salpicón real de 7896


def sfx_b(m):
    """9,50–12,50: un toque por palabra y sub-golpe en «intentarlo»."""
    golpes, toques = eventos_texto()
    for n in toques:
        m.toque(tf(n), 0.07, 1500)
    for n, tipo, _id in golpes:
        if tipo == 'sub':
            sub_golpe(m, tf(n))


def sfx_c(m):
    """12,60 en adelante: impacto del drop con el salpicón real, acento en «prometés?», barrido al CTA."""
    m.impacto(12.60, 0.55)
    golpes, _ = eventos_texto()
    for n, tipo, _id in golpes:
        if tipo == 'acento':
            m.toque(tf(n), 0.16, 2400)
    m.barrido(13.90, 0.30, 0.16); m.toque(13.90, 0.14, 2400)


def musica_a(m):
    """TEMP propia: subida del gancho; pulso (latido en cada corte) y colchón Re menor / Fa / Si♭ según E−/E+."""
    m.subida(0.60, 1.333, 0.20)
    m.pad(1.40, [38, 45, 50, 53], 1.50, .055, 650, a=.05)
    m.pad(3.00, [38, 45, 50], 0.85, .028, 450, a=.05)                  # «la música baja»
    m.pad(3.90, [41, 48, 53, 57, 60], 0.95, .055, 1500, a=.03)
    m.pad(4.90, [41, 48, 53, 57], 0.45, .050, 1300, a=.03)
    m.subida(5.22, 5.40, 0.10)
    m.pad(5.40, [41, 48, 53, 57, 60, 64], 0.45, .060, 2000, a=.01)
    m.pad(5.90, [38, 45, 50, 53], 0.75, .050, 650, a=.03)
    m.pad(6.70, [46, 53, 58, 62], 0.65, .055, 1500, a=.03)
    m.pad(7.40, [38, 45, 50, 53], 0.70, .055, 600, a=.03)
    m.subida(7.62, 8.10, 0.16)                                        # SUBE
    for t, g in ((1.40, .8), (2.20, .8), (3.00, .45), (3.90, .75), (4.90, .75), (5.90, .8), (6.70, .75), (7.40, .9)):
        latido(m, t, g, doble=(t != 7.40))     # en 7,40 el segundo latido (7,57) tapaba el golpe grave de 7,60
    m.campana(5.40, 81, .05)


def musica_b(m):
    m.pad(9.50, [38, 45, 50, 52, 57], 2.90, .035, 800, a=.6, r=.3)    # pad bajo Rem(add9)


def musica_c(m):
    ch = lambda t0, t1, g=.08: [m.charles(round(float(t), 3), g) for t in np.arange(t0, t1 - 1e-6, 0.3)]
    m.bombo(12.60, 1.0); m.ocho08(12.60, 38, .55, .55, glide_desde=45); m.pad(12.60, [50, 53, 57, 62], .55, .06, 1600)
    m.campana(12.60, 74, .06); m.campana(12.90, 81, .05)
    m.bombo(13.20, .85); m.palma(13.20); m.pad(13.20, [46, 50, 53, 58], .55, .06, 1600); m.ocho08(13.20, 34, .5, .5)
    m.bombo(13.80, .85); m.pad(13.80, [48, 52, 55, 60], .55, .06, 1600); m.ocho08(13.80, 36, .5, .5)
    m.bombo(14.40, .9); m.palma(14.40); m.pad(14.40, [41, 48, 53, 57, 60], 1.4, .065, 1800, r=.5); m.ocho08(14.40, 41, .9, .5)
    m.campana(14.40, 77, .06, .9)
    m.bombo(15.00, .8); m.palma(15.00, .22)
    ch(12.60, 15.31)


def agachar(m, t, db_=-9.0, ataque=0.04, sostener=0.12, suelta=0.25, pistas=('mus', 'bombo')):
    """la música (colchón y latido) baja db_ dB justo en un golpe grave para que el golpe se lea (control v01: en la
    mezcla completa el golpe de 6,30 subía 2,0 dB y el de 7,60 0,8 dB en 35–200 Hz, tapados por el colchón y el latido)."""
    from sonido import SR as SR_
    N = m.N; g = np.ones(N)
    i0 = int((t - ataque) * SR_); i1 = int(t * SR_); i2 = int((t + sostener) * SR_); i3 = int((t + sostener + suelta) * SR_)
    lo = 10 ** (db_ / 20)
    g[max(0, i0):i1] = np.linspace(1, lo, i1 - max(0, i0)) if i1 > max(0, i0) else lo
    g[i1:i2] = lo
    g[i2:min(N, i3)] = np.linspace(lo, 1, i3 - i2)[:min(N, i3) - i2]
    for p in pistas:
        m.pistas[p] *= g[:, None]


def mezcla(con_musica):
    from sonido import Mezcla
    m = Mezcla(DUR)
    ambientes(m)
    sfx_a(m)
    if con_musica:
        musica_a(m)
    for p in ('mus', 'bombo', 'fx'):
        m.silenciar(p, 8.10, 9.50, rampa=0.008)                        # «la música se corta en 8,10»: solo mar
    sfx_b(m)
    if con_musica:
        musica_b(m)
    for p in ('mus', 'bombo', 'fx'):
        m.silenciar(p, 12.50, 12.60, rampa=0.03)                        # negro 12,50–12,60
    sfx_c(m)
    if con_musica:
        musica_c(m)
    golpes, _ = eventos_texto()
    for n, tipo, _id in golpes:
        if tipo in ('grave', 'impacto', 'sub'):
            agachar(m, tf(n), -4.0, pistas=('amb',))                     # el mar cede 4 dB en el golpe (las dos mezclas)
            if con_musica:
                agachar(m, tf(n))
    for p in ('amb', 'mus', 'bombo', 'fx'):
        m.fundido(p, 15.40, DUR)                                         # fundido 15,4–15,9
    return m


def etapa_audio():
    A.mkdir(parents=True, exist_ok=True)
    out = {}
    for k, con in (('completa', True), ('sinmusica', False)):
        m = mezcla(con)
        r = m.exportar(str(A / f'v4_{k}.wav'), lufs=-14)
        out[f'exportar_{k}'] = r
        if r[1] > -1.5:
            out[f'limitado_{k}'] = L2.limitar_tp(A / f'v4_{k}.wav')
        out[k] = dict(zip(('lufs', 'pico_dbtp', 'lra'), L2.medir_ebur(A / f'v4_{k}.wav')))
        print(k, out[k], flush=True)
    golpes, toques = eventos_texto()
    out['golpes_texto'] = [dict(cuadro=n, t=round(tf(n), 3), tipo=t_, frase=i) for n, t_, i in golpes]
    out['toques'] = [dict(cuadro=n, t=round(tf(n), 3)) for n in toques]
    out['ambientes'] = [dict(toma=a[0], fuente_s=a[1], t0=a[2], t1=a[3], db=a[4]) for a in AMB]
    jdump(out, A / 'audio.json')


# =====================================================================================================
# etapa master · base graduada + capa de texto (secuencia RGBA) + placa + mezcla → H.264 High 4.0 / AAC-LC
# =====================================================================================================
def master_v4(video, audio_wav, salida, secuencia, overlays):
    """como life_v1.master_v1 (overlays RGBA → yuva444p BT.709 tv, composición en 4:4:4, enable por número de cuadro,
    PNG a 30 fps) más la capa de texto: secuencia f_0000…f_0416 a 30 fps que termina con eof_action=pass."""
    inputs = ['-i', str(video), '-i', str(audio_wav), '-framerate', str(FPS), '-start_number', '0', '-i', str(secuencia)]
    fc = ['[0:v]setsar=1,format=yuv444p[v0]',
          '[2:v]format=rgba,scale=out_color_matrix=bt709:out_range=tv,format=yuva444p[t]',
          '[v0][t]overlay=0:0:format=yuv444:eof_action=pass[v1]']
    lab = 'v1'
    for i, (png, n0, n1) in enumerate(overlays):
        inputs += ['-loop', '1', '-framerate', str(FPS), '-i', str(png)]
        fc.append(f'[{i + 3}:v]format=rgba,scale=out_color_matrix=bt709:out_range=tv,format=yuva444p[o{i}]')
        fc.append(f"[{lab}][o{i}]overlay=0:0:format=yuv444:enable='between(n,{n0},{n1})':shortest=1[p{i}]")
        lab = f'p{i}'
    fc.append(f'[{lab}]format=yuv420p[vout]')
    V.sh(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '1:a:0',
          '-c:v', 'libx264', '-profile:v', 'high', '-level:v', '4.0', '-preset', 'slow', '-crf', '17',
          '-maxrate', '20M', '-bufsize', '25M', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-g', '30',
          '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
          '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
          '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
          '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
          '-frames:v', str(NF), '-shortest', '-movflags', '+faststart', str(salida)])
    return salida


def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    ov = [(PL / 'cierre_frase.png', *PLACA_CUADROS['frase']), (PL / 'cierre_firma.png', *PLACA_CUADROS['firma'])]
    out = MAS / NOMBRES['completa']
    master_v4(T / 'v4_base.mp4', A / 'v4_completa.wav', out, TX / 'cuadros' / 'f_%04d.png', ov)
    print('ok', out, out.stat().st_size, flush=True)
    # sin música: MISMO flujo de video (copia; x264 con hilos no da dos codificaciones idénticas bit a bit)
    out2 = MAS / NOMBRES['sinmusica']
    V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(out), '-i', str(A / 'v4_sinmusica.wav'), '-map', '0:v:0', '-map', '1:a:0',
          '-c:v', 'copy', '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
          '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
          '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
          '-shortest', '-movflags', '+faststart', str(out2)])
    print('ok', out2, out2.stat().st_size)


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    if etapa in ('control', 'entregar'):
        import life_v4_control as C   # noqa: E402
        getattr(C, 'etapa_' + etapa)()
    else:
        globals()['etapa_' + etapa]()
