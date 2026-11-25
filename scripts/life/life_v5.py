#!/usr/bin/env python3
"""Roccé Life · tanda 2 · V5 «Agrandado» · receta del máster v01 (Pedro, 25/11/2026).

Guion: piezas/LIFE_rocce_life/TANDA2/V5_agrandado/01_fede_guion_G1_v1.md (G1 v1) + base común de la tanda
(V3_5_domingos/01_fede_guion_G1_v1.md) + condiciones de Roma (TANDA2/07_roma_aprobacion_guiones_t2.md, mandan).
Reutiliza sin modificarlos scripts/fmt/video.py (color, encuadre, ass, foto_srgb), fmt03.py (leer, plano_n, plano_z,
hoja_src, md5_stream, ebur, audio_np, control…), sonido.py (Mezcla) y scripts/life/life_v2.py (neutralización de la Blanca,
detector de «Founders Privée», master_v2, limitar_tp, utilidades de control). Lo nuevo de V5 vive acá:
  · medición de nitidez (varianza del laplaciano sobre el estampado, a 1080) de los clips 576×1024 contra las tomas 4K;
  · ancho de «ROCCÉ» por cuadro (cadena «Otra.» con el ancho creciente y corte por forma);
  · etiquetas de prenda (rectángulo hueso #F4F1EA, Inter Display ExtraBold negra) como objeto con sombra que cae en 4 c
    con rebote, capa RGBA por cuadro compuesta en YUV solo donde hay etiqueta;
  · saturación que baja con cada etiqueta, destello de 2 c en el giro, barrido;
  · música TEMP con un pasabajos que se cierra con cada etiqueta (sonido.Mezcla + filtro variable propio) y «sello».
Etapas (nice -n 10 y el python de TRABAJO/venv):
  hojas → medir → planos → color → etiquetas → placa → audio → master → control → entregar
Intermedios en TRABAJO/life2/v5/. Nada se publica; sin servicios externos ni créditos.
"""
import json, math, os, subprocess, sys, hashlib, shutil, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/life')
import video as V          # noqa: E402
import fmt03 as U          # noqa: E402
import life_v2 as L2       # noqa: E402  (al importarlo envuelve V.sh con nice -n 10 y 2 hilos: lo mismo que queremos acá)

R = Path('/home/user/1')
T = R / 'TRABAJO/life2/v5'
HJ = T / 'hojas'
MED = T / 'med'
A = T / 'audio'
# versión: v01 = máster entregado el 25/11/2026; v02 = corrección de Roma (04_roma_dictamen_master_v01.md): la espalda
# crece ≥ 12 % en cada corte de la cadena «Otra.» (solo cambian los empujes de p6–p8; audio, textos, placas, etiquetas y
# los demás planos son los mismos archivos de v01). V5_VER=v01 rehace v01 en las carpetas de v01.
VER = os.environ.get('V5_VER', 'v02')
TV = T if VER == 'v01' else T / VER               # salidas que cambian con la versión
P = TV / 'planos'
MAS = TV / 'master'
EVID = TV / f'evidencia_{VER}'
MEDV = MED if VER == 'v01' else TV / 'med'
EXP = R / 'EXPORTACIONES'
PIEZA = Path('/mnt/project-files/piezas/LIFE_rocce_life/TANDA2/V5_agrandado')
FPS, W, H = 30, 1080, 1920
SR = 48000
FONT = U.FONT
KY = np.array([0.2126, 0.7152, 0.0722], np.float32)
NOMBRES = {'completa': f'ROCCE_LIFE_V5_AGRANDADO_{VER}.mp4', 'sinmusica': f'ROCCE_LIFE_V5_AGRANDADO_SINMUSICA_{VER}.mp4'}
V01 = {'completa': EXP / 'ROCCE_LIFE_V5_AGRANDADO_v01.mp4', 'sinmusica': EXP / 'ROCCE_LIFE_V5_AGRANDADO_SINMUSICA_v01.mp4'}
PY = str(R / 'TRABAJO/venv/bin/python')


def nice(cmd):
    return ['nice', '-n', '10'] + list(cmd)


def jdump(obj, f):
    Path(f).parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(f, 'w'), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))


def tt(n):
    return L2.tt(n)


# =====================================================================================================
# línea de tiempo (cuadros del máster, 30 fps). Guion en segundos → cuadros; desvíos en la hoja (§4).
# =====================================================================================================
# Plano: id, toma, cuadro de fuente inicial, cuadros, ventana (x, y, w, h en coordenadas naturales 4K; None = completo)
NW, NH = 2160, 3840
FULL = (0, 0, NW, NH)


# =====================================================================================================
# detectores (Blanca: «ROCCÉ» oscuro guiado por el celeste de «Founders Privée»; Negra: L2.estampado)
# =====================================================================================================
def detectar_blanca(rgb, caja=None):
    """Blanca y su «ROCCÉ» en un cuadro RGB (float, cualquier escala; umbrales en escala 540 de ancho).
    1) celeste del estampado: B − R > 22, sat > 0,13, 100 < L < 245 (abierto 1 px);
    2) Blanca = componente de tela clara y neutra (L > 150, sat < 0,17) que más celeste toca (dilatado 6 px de 540),
       cerrado y relleno (así la elige aunque la espuma del mar sea más grande);
    3) «ROCCÉ» = componentes oscuros (L < 100) dentro de la Blanca (erosionada 2 px de 540), de área ≥ 8 px de 540, con
       centro por encima del centro del celeste y alto ≤ 3 veces la mediana, en el renglón de la mediana ponderada por
       área (± 2,5 alturas de letra: la palabra va en arco).
    Devuelve dict(rocce=(x0, y0, x1, y1), toca=[izq, der], blanca=(x0, y0, x1, y1), letras=n, roc=máscara) o None."""
    from scipy import ndimage as nd
    a = rgb.astype(np.float32); L = a @ KY; mx = a.max(-1); mn = a.min(-1); sat = (mx - mn) / (mx + 1)
    h, w = L.shape; s = w / 540.0
    lim = np.ones((h, w), bool)
    if caja is not None:
        lim[:] = False; x0, y0, x1, y1 = caja; lim[y0:y1, x0:x1] = True
    cel = nd.binary_opening((a[..., 2] - a[..., 0] > 22) & (sat > 0.13) & (L > 100) & (L < 245) & lim, iterations=1)
    bright = nd.binary_closing(nd.binary_opening((L > 150) & (sat < 0.17) & lim, iterations=1), iterations=max(1, int(2 * s)))
    lab, n = nd.label(bright)
    if n == 0 or cel.sum() < 10:
        return None
    sc = nd.sum(nd.binary_dilation(cel, iterations=max(2, int(6 * s))), lab, range(1, n + 1))
    k = int(np.argmax(sc)) + 1
    if sc[k - 1] < 10:
        return None
    shirt = nd.binary_fill_holes(nd.binary_closing(lab == k, iterations=max(2, int(8 * s))))
    cel &= shirt
    if not cel.any():
        return None
    dark = nd.binary_opening(nd.binary_erosion(shirt, iterations=max(1, int(2 * s))) & (L < 100), iterations=1)
    ld, nl = nd.label(dark)
    if nl == 0:
        return None
    idx = np.arange(1, nl + 1)
    area = nd.sum(dark, ld, idx); cm = np.array(nd.center_of_mass(dark, ld, idx)).reshape(-1, 2)
    sl = nd.find_objects(ld)
    hs = np.array([o[0].stop - o[0].start for o in sl])
    cy = np.argwhere(cel)[:, 0].mean()
    ok = (area >= max(4, 8 * s * s)) & (cm[:, 0] < cy)
    if not ok.any():
        return None
    hmed = float(np.median(hs[ok]))
    ok &= hs <= 3 * hmed
    if not ok.any():
        return None
    ys, ar = cm[ok, 0], area[ok]
    o = np.argsort(ys); cum = np.cumsum(ar[o]); ymed = ys[o][min(len(o) - 1, np.searchsorted(cum, cum[-1] / 2))]
    keep = ok & (np.abs(cm[:, 0] - ymed) <= 2.5 * hmed)
    roc = np.isin(ld, idx[keep])
    yy, xx = np.nonzero(roc)
    rb = (int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max()))
    sy, sx = np.nonzero(shirt.any(1))[0], np.nonzero(shirt.any(0))[0]
    return dict(rocce=rb, ancho=rb[2] - rb[0] + 1, toca=[bool(rb[0] <= 1), bool(rb[2] >= w - 2)], letras=int(keep.sum()),
                blanca=(int(sx.min()), int(sy.min()), int(sx.max()), int(sy.max())), roc=roc, shirt=shirt)


def blanca_7887(rgb, caja=(0, 760, 1080, 1500)):
    """7887 (Blanca chica y nublado: el celeste no alcanza): mayor componente de tela clara y neutra (L > 150, sat < 0,15)
    dentro de la caja (debajo de la espuma), cerrado y relleno. Devuelve su caja."""
    from scipy import ndimage as nd
    a = rgb.astype(np.float32); L = a @ KY; sat = (a.max(-1) - a.min(-1)) / (a.max(-1) + 1)
    x0, y0, x1, y1 = caja
    m = np.zeros(L.shape, bool); m[y0:y1, x0:x1] = True
    m &= (L > 150) & (sat < 0.15)
    m = nd.binary_opening(m, iterations=2)
    lab, n = nd.label(m)
    if n == 0:
        return None
    s = nd.sum(m, lab, range(1, n + 1)); k = int(np.argmax(s)) + 1
    ys, xs = np.nonzero(nd.binary_fill_holes(nd.binary_closing(lab == k, iterations=8)))
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def lapvar(Y, bb):
    from scipy import ndimage as nd
    x0, y0, x1, y1 = bb
    return float(nd.laplace(Y[y0:y1 + 1, x0:x1 + 1].astype(np.float32))[2:-2, 2:-2].var())


# =====================================================================================================
# «ROCCÉ» de la Blanca por seguimiento: letras oscuras sobre tela clara dentro de la caja del cuadro anterior
# =====================================================================================================
def rocce_roi(img, roi, l_rel=0.52, con_largo=False):
    """letras de «ROCCÉ» dentro de roi=(x0, y0, x1, y1) (1080×1920): píxeles con luma < l_rel × tela (percentil 85 de la
    luma del roi = la tela blanca), solo componentes rodeados de tela (≥ 55 % de un anillo de 4 px con luma > 0,72 × tela:
    descarta la Negra, la arena, sombras y rocas) y, entre esos, de alto entre 0,45 y 1,8 veces el del mayor componente
    que no toca el borde del roi, de área ≥ 6 % del mayor, en el grupo de letras vecinas más numeroso.
    Devuelve (caja, n_letras) o, con con_largo, (caja, n_letras, largo): largo = extensión de las letras sobre su eje
    principal (la palabra girada, como en 8008, no se mide por la caja)."""
    from scipy import ndimage as nd
    h, w = img.shape[:2]
    x0, y0, x1, y1 = [int(round(v)) for v in roi]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
    nada = (None, 0, None) if con_largo else (None, 0)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return nada
    sub = img[y0:y1, x0:x1].astype(np.float32)
    L = sub @ KY
    tela = float(np.percentile(L, 85))
    osc = nd.binary_opening(L < l_rel * tela, iterations=1)
    clara = np.pad(L > 0.72 * tela, 5, constant_values=False)   # fuera del roi no cuenta como tela
    osc = np.pad(osc, 5, constant_values=False); L = np.pad(L, 5, constant_values=0); x0 -= 5; y0 -= 5
    lab, n = nd.label(osc)
    if n == 0:
        return nada
    sl = nd.find_objects(lab)
    cand = []
    for i, o in enumerate(sl):
        if (o[0].stop - o[0].start) < 4:
            continue
        hh = o[0].stop - o[0].start
        r1, r2 = max(3, int(0.08 * hh)), max(8, int(0.24 * hh))      # anillo proporcional a la letra (borde bordado)
        ya, yb = max(0, o[0].start - r2 - 1), min(L.shape[0], o[0].stop + r2 + 1)
        xa, xb = max(0, o[1].start - r2 - 1), min(L.shape[1], o[1].stop + r2 + 1)
        m = lab[ya:yb, xa:xb] == i + 1
        anillo = nd.binary_dilation(m, iterations=r2) & ~nd.binary_dilation(m, iterations=r1)
        if anillo.any() and clara[ya:yb, xa:xb][anillo].mean() >= 0.55:
            borde = o[0].start <= 6 or o[1].start <= 6 or o[0].stop >= L.shape[0] - 6 or o[1].stop >= L.shape[1] - 6
            cand.append((i + 1, int(m.sum()), o[0].stop - o[0].start, borde))
    if not cand:
        return nada
    # altura de referencia: la del componente más grande que no toca el borde del roi (una letra entera)
    ref = max([c for c in cand if not c[3]] or cand, key=lambda c: c[1])
    cand = [c for c in cand if 0.45 * ref[2] <= c[2] <= 1.8 * ref[2]]
    amax = max(c[1] for c in cand)
    cand = [c for c in cand if c[1] >= 0.06 * amax]
    # letras vecinas: grupos de componentes a menos de 1,2 alturas de letra entre cajas; queda el grupo más numeroso
    cj = {c[0]: sl[c[0] - 1] for c in cand}
    hm = float(np.median([c[2] for c in cand]))
    dist = lambda a, b: max(0, max(a[1].start, b[1].start) - min(a[1].stop, b[1].stop),
                            max(a[0].start, b[0].start) - min(a[0].stop, b[0].stop))
    grupo = {c[0]: c[0] for c in cand}
    def raiz(i):
        while grupo[i] != i:
            i = grupo[i]
        return i
    ids = [c[0] for c in cand]
    for i in ids:
        for j in ids:
            if i < j and dist(cj[i], cj[j]) < 1.2 * hm:
                grupo[raiz(j)] = raiz(i)
    from collections import Counter
    cnt = Counter(raiz(i) for i in ids)
    mejor = max(cnt, key=lambda r: (cnt[r], sum(c[1] for c in cand if raiz(c[0]) == r)))
    keep = [i for i in ids if raiz(i) == mejor]
    if not keep:
        return nada
    yy, xx = np.nonzero(np.isin(lab, keep))
    caja = (int(xx.min()) + x0, int(yy.min()) + y0, int(xx.max()) + x0, int(yy.max()) + y0)
    if not con_largo:
        return caja, len(keep)
    P_ = np.stack([xx, yy], 1).astype(np.float64); P_ -= P_.mean(0)
    ev, evec = np.linalg.eigh(np.cov(P_.T))
    pr = P_ @ evec[:, -1]
    return caja, len(keep), float(pr.max() - pr.min() + 1)


def seguir_rocce(frames, k0, bb0, mx=0.22, my=0.9):
    """sigue «ROCCÉ» desde el cuadro k0 (bb0 = roi amplio donde está la palabra en ese cuadro) hacia adelante y hacia
    atrás; el roi de cada cuadro es la caja del vecino agrandada mx del ancho a los lados y my del alto arriba y abajo.
    Devuelve por cuadro (caja, n_letras, largo)."""
    n = len(frames); out = [None] * n

    def roi_de(bb):
        x0, y0, x1, y1 = bb; w_, h_ = x1 - x0, y1 - y0
        return (x0 - mx * w_, y0 - my * h_, x1 + mx * w_, y1 + my * h_)
    bb_s, nl_s, lg_s = rocce_roi(frames[k0], bb0, con_largo=True)
    assert bb_s is not None, ('sin semilla', bb0)
    out[k0] = (bb_s, nl_s, lg_s)
    for rng_ in (range(k0 + 1, n), range(k0 - 1, -1, -1)):
        prev, lg_prev = bb_s, lg_s
        for k in rng_:
            bb, nl, largo = rocce_roi(frames[k], roi_de(prev), con_largo=True)
            # coherencia: al menos 3 letras y largo dentro de ±25 % del último bueno (si no, el cuadro queda sin medir
            # y el roi sigue siendo el del último bueno)
            if bb is None or nl < 3 or abs(largo - lg_prev) > 0.25 * lg_prev:
                out[k] = (None, nl, largo); continue
            out[k] = (bb, nl, largo); prev, lg_prev = bb, largo
    return out


def tira_cajas(frames, cajas, salida, rot=None, cada=1, ancho=180, cols=12):
    """hoja con la caja medida dibujada (control visual de la medición)."""
    from PIL import Image, ImageDraw
    ims = []
    for k in range(0, len(frames), cada):
        im = Image.fromarray(frames[k]); d = ImageDraw.Draw(im)
        if cajas[k] is not None:
            d.rectangle(cajas[k], outline=(255, 0, 255), width=6)
        d.text((10, 10), (rot[k] if rot else str(k)), fill=(255, 255, 0))
        s = ancho / im.width
        im = im.resize((ancho, int(im.height * s)))
        ims.append(im)
    filas = math.ceil(len(ims) / cols)
    hoja = Image.new('RGB', (cols * ancho, filas * ims[0].height), (32, 32, 32))
    for i, im in enumerate(ims):
        hoja.paste(im, ((i % cols) * ancho, (i // cols) * im.height))
    hoja.save(salida, quality=88)


# =====================================================================================================
# etapa hojas · cuadro a cuadro de los tramos críticos
# =====================================================================================================
def etapa_hojas():
    HJ.mkdir(parents=True, exist_ok=True)
    for toma, a, b, c, ancho, cols in (('IMG_7887', 0, 110, 3, 200, 12), ('IMG_7887', 48, 68, 1, 200, 11),
                                       ('IMG_7885', 48, 156, 3, 200, 12), ('IMG_8008', 26, 64, 1, 160, 13),
                                       ('IMG_8002', 75, 106, 1, 160, 13), ('IMG_8004', 80, 120, 1, 160, 13),
                                       ('IMG_7894', 0, 73, 2, 160, 13), ('clip_a2c1cbe8', 20, 80, 4, 200, 8),
                                       ('clip_a592f367', 0, 129, 6, 200, 11)):
        U.hoja_src(toma, a, b, HJ / f'{toma}_c{a}-c{b}_c{c}.jpg', cada=c, ancho=ancho, cols=cols)
    U.hoja_src('IMG_7885', 48, 80, HJ / 'IMG_7885_c48-c80_c2_cabeza.jpg', cada=2, ancho=300, cols=9,
               caja=(1100, 500, 1060, 1300))


# =====================================================================================================
# etapa medir
# =====================================================================================================
def leer_toma(toma, n0, n1, caja=None, esc=(W, H)):
    """cuadros n0..n1 de la fuente, con la cadena de color de video.py y la ventana `caja` (natural) llevada a `esc`."""
    vf = V.color(toma)
    if caja is not None:
        x, y, w, h = [int(round(v)) for v in caja]
        vf += f',crop={w}:{h}:{x}:{y}'
    return U.leer(V._src(toma), esc[0], esc[1], n0=n0, n1=n1, vf_pre=vf)


def medir_7887():
    """por cuadro de 7887 c0–c107 (cuadro completo a 1080×1920): caja de la Blanca (blanca_7887) y de la Negra («Founders
    Privée» con L2.estampado, parámetros de V2, y la franja de ROCCÉ tono sobre tono: 0,40 × ancho por encima)."""
    fr = leer_toma('IMG_7887', 0, 107)
    par = dict(lf_max=115, dl_min=60, media_max=150)
    roi = (420, 760, 1079, 1300)
    filas = []
    for k, img in enumerate(fr):
        bc = blanca_7887(img)
        bbn, mn = L2.estampado(img, 'negra', roi, **par)
        neg_top = None
        if bbn is not None:
            x0, y0, x1, y1 = bbn
            roi = (x0 - 40, y0 - 40, x1 + 40, y1 + 40)
            neg_top = int(y0 - 0.40 * (x1 - x0))
        filas.append(dict(cuadro=k, blanca_caja=bc, negra_founders=bbn, negra_rocce_tope_conservador=neg_top,
                          tope=min([v for v in ((bc[1] if bc else None), neg_top) if v is not None], default=None)))
    return filas


def medir_rocce(toma, n0, n1, caja=None, laplaciano=True):
    """«ROCCÉ» por cuadro en la ventana dada (1080×1920): caja, ancho, si toca un borde y varianza del laplaciano de la luma
    sobre la caja de ROCCÉ agrandada 8 % (las letras oscuras sobre la tela blanca: el detalle más fino del estampado)."""
    fr = leer_toma(toma, n0, n1, caja)
    out = []
    for k, img in enumerate(fr):
        d = detectar_blanca(img.astype(np.float32))
        if d is None:
            out.append(dict(cuadro=n0 + k, rocce=None)); continue
        x0, y0, x1, y1 = d['rocce']; px = int(0.08 * (x1 - x0)); py = int(0.08 * (y1 - y0)) + 4
        bb = (max(0, x0 - px), max(0, y0 - py), min(W - 1, x1 + px), min(H - 1, y1 + py))
        f = dict(cuadro=n0 + k, rocce=list(d['rocce']), ancho=d['ancho'], toca=d['toca'], letras=d['letras'],
                 blanca=list(d['blanca']))
        if laplaciano:
            f['lapvar'] = round(lapvar(img.astype(np.float32) @ KY, bb), 1)
        out.append(f)
    return out


# tramos del guion con clips de baja resolución, en su encuadre (completo: 576×1024 → 1080×1920 con lanczos)
NITIDEZ_CLIPS = {
    'paso5_clip_a2c1cbe8_0.90-1.50': ('clip_a2c1cbe8', 27, 44),
    'paso7_clip_a592f367_0.20-0.65': ('clip_a592f367', 6, 19),
    'paso8_clip_a2c1cbe8_2.10-2.50': ('clip_a2c1cbe8', 63, 74),
    'paso9_clip_a592f367_1.30-4.00': ('clip_a592f367', 39, 119),
}


def etapa_medir():
    MED.mkdir(parents=True, exist_ok=True)
    rep = {}
    f87 = medir_7887()
    rep['7887'] = f87
    tr = [(a, b, min(f['tope'] for f in f87[a:b] if f['tope'])) for a, b in ((0, 36), (36, 60), (60, 75), (75, 108))]
    print('7887 tope de las remeras/estampados por tramo', tr, flush=True)
    for toma, a, b in (('IMG_7885', 48, 156), ('IMG_8008', 40, 64), ('IMG_8002', 84, 106), ('IMG_8004', 92, 112),
                       ('IMG_7894', 0, 73)):
        rep[f'rocce_{toma}'] = medir_rocce(toma, a, b, laplaciano=False)
        print(toma, [(x['cuadro'], x.get('ancho'), x.get('toca')) for x in rep[f'rocce_{toma}']], flush=True)
    for k, (toma, a, b) in NITIDEZ_CLIPS.items():
        fr = U.leer(V._src(toma), W, H, n0=a, n1=b, vf_pre=V.color(toma) + ',' + V.encuadre(toma, None))
        filas = []
        for i, img in enumerate(fr):
            d = detectar_blanca(img.astype(np.float32))
            if d is None:
                filas.append(dict(cuadro=a + i, rocce=None)); continue
            x0, y0, x1, y1 = d['rocce']; px = int(0.08 * (x1 - x0)); py = int(0.08 * (y1 - y0)) + 4
            bb = (max(0, x0 - px), max(0, y0 - py), min(W - 1, x1 + px), min(H - 1, y1 + py))
            filas.append(dict(cuadro=a + i, rocce=list(d['rocce']), ancho=d['ancho'], toca=d['toca'],
                              lapvar=round(lapvar(img.astype(np.float32) @ KY, bb), 1)))
        rep[f'nitidez_{k}'] = filas
        v = [f_['lapvar'] for f_ in filas if f_.get('lapvar') is not None]
        print(k, 'n', len(v), 'mediana', np.median(v) if v else None, [(f_['cuadro'], f_.get('ancho'), f_.get('lapvar')) for f_ in filas], flush=True)
    jdump(rep, MED / 'medidas.json')



# =====================================================================================================
# línea de tiempo del máster v01 (335 cuadros = 11,167 s; guion 11,15 s) · desvíos en la hoja §4
# =====================================================================================================
NF = 335
DUR = NF / FPS
# cuadros del máster donde empieza cada paso del guion
M = dict(p1=0, e1=6, p2=36, e2=36, obt1=46, e3=60, p4=75, e4=75, salida=102, hueco=106, p5=108, p6=126, p7=141, p8=154,
         p9=166, placa=176, p10=248, p11=278)
CORTES = [108, 126, 141, 154, 166, 248]          # 278 no es corte: 4530 sigue (entra la placa del CTA)
ROCCE_4K = MED / 'rocce_4k.json'                # «ROCCÉ» medido por seguimiento en 7885, 8008, 8002, 8004 (etapa medir)
SEGUIR = {   # toma: (cuadro inicial, final, cuadro semilla, roi semilla en 1080×1920)
    'IMG_7885': (30, 131, 48, (380, 680, 700, 820)), 'IMG_8008': (40, 64, 50, (300, 650, 1080, 1300)),
    'IMG_8002': (80, 106, 95, (80, 720, 1000, 1020)), 'IMG_8004': (88, 112, 100, (20, 950, 1000, 1230)),
}


def medir_rocce_4k():
    out = {}
    for toma, (a, b, ks, roi) in SEGUIR.items():
        fr = leer_toma(toma, a, b)
        r = seguir_rocce(fr, ks - a, roi)
        out[toma] = [dict(cuadro=a + i, caja=c, letras=n, largo=None if lg is None else round(lg, 1))
                     for i, (c, n, lg) in enumerate(r)]
        print(toma, [(a + i, None if c is None else c[2] - c[0] + 1) for i, (c, n, lg) in enumerate(r)], flush=True)
    jdump(out, ROCCE_4K)
    return out


def _cajas(toma, n0, nf):
    d = {f['cuadro']: f['caja'] for f in json.load(open(ROCCE_4K))[toma]}
    return [d.get(n0 + k) for k in range(nf)]


def _ajuste_lineal(vals):
    """recta por mínimos cuadrados (ignora None): centro de ROCCÉ suavizado, sin estabilizar el pulso de la cámara."""
    k = np.array([i for i, v in enumerate(vals) if v is not None], float)
    v = np.array([vals[int(i)] for i in k], float)
    a, b = np.polyfit(k, v, 1)
    return [float(a * i + b) for i in range(len(vals))]


def ventana_rocce(toma, n0, nf, z_a, z_b, ty=960):
    """zoom por cuadro de z_a a z_b (exponencial: velocidad de acercamiento pareja) y centro de la ventana tal que el centro
    de ROCCÉ (recta ajustada) caiga en x 540, y ty de la pantalla; plano_z lo limita a la toma (nunca agranda > 2×)."""
    cj = _cajas(toma, n0, nf)
    cx = _ajuste_lineal([None if c is None else (c[0] + c[2]) for c in cj])            # ×2 (1080 → natural) / 2
    cy = _ajuste_lineal([None if c is None else (c[1] + c[3]) for c in cj])
    if isinstance(z_a, tuple) and z_a[0] == 'largo':
        # zoom que lleva el largo de ROCCÉ en pantalla de z_a[1] a z_a[2] en línea recta: compensa que la remera se aleja
        # (largo de la toma ajustado con una parábola para no copiar el ruido del seguimiento)
        d = {f['cuadro']: f['largo'] for f in json.load(open(ROCCE_4K))[toma]}
        lg = np.array([d[n0 + k] for k in range(nf)], float); kk = np.arange(nf)
        lf = np.polyval(np.polyfit(kk, lg, 2), kk)
        zs = [float(v) for v in np.linspace(z_a[1], z_a[2], nf) / lf]
    else:
        zs = [z_a * (z_b / z_a) ** (k / max(1, nf - 1)) for k in range(nf)]
    cys = [cy[k] + (1920 - 2 * ty) / zs[k] for k in range(nf)]
    assert max(zs) <= 2.0 and min(zs) >= 1.0
    return zs, cx, cys


# cadena «Otra.» por versión: (toma, primer cuadro, cuadros, zoom inicial, zoom final, y de pantalla del centro de ROCCÉ)
CADENA = {
    'v01': dict(p6=('IMG_8008', 47, 15, 1.232, 1.824, 960), p7=('IMG_8002', 90, 13, 1.0, 1.0, None),
                p8=('IMG_8004', 97, 12, 1.14, 1.14, 960)),
    # v02 · largo de ROCCÉ en pantalla: p6 700→735 en línea recta (el empuje frena y compensa que la remera se aleja,
    # 634→458 px en la toma: Z 1,10→1,60), p7 866→878 (Z 1,00→1,065), p8 igual que v01 (1011→1019)
    # → cortes c141 ≈ +18 %, c154 ≈ +15 % (primera prueba medida sobre la base sin color).
    # p7 entra en 8002 c91 (un cuadro después que v01): en c90 la É está a 38 px del borde derecho de la toma 4K y el margen
    # en pantalla es −1 + 19,5·Z; con Z ≥ 1,05 llega a 20 px pero ROCCÉ ya mide ≥ 917 y el corte a p8 no llega al 12 %.
    # El audio no cambia (ambiente de 8002 3,000–3,433 s, sin sincronía visible).
    'v02': dict(p6=('IMG_8008', 47, 15, ('largo', 700.0, 735.0), None, 960), p7=('IMG_8002', 91, 13, 1.0, 1.065, 900),
                p8=('IMG_8004', 97, 12, 1.14, 1.14, 960)),
}


def plan_planos():
    c = CADENA[VER]
    z6 = ventana_rocce(*c['p6'][:5], ty=c['p6'][5])
    z8 = ventana_rocce(*c['p8'][:5], ty=c['p8'][5])
    t7, n7, nf7, za7, zb7, ty7 = c['p7']
    p7 = (dict(id='p7', m0=141, tipo='n', toma=t7, n0=n7, nf=nf7, caja=FULL) if ty7 is None else
          dict(id='p7', m0=141, tipo='z', toma=t7, n0=n7, zs=None, cxs=None, cys=None))
    if ty7 is not None:
        z7 = ventana_rocce(t7, n7, nf7, za7, zb7, ty=ty7); p7.update(zs=z7[0], cxs=z7[1], cys=z7[2])
    return [
        dict(id='p1-4', m0=0, tipo='n', toma='IMG_7887', n0=0, nf=108, caja=FULL),
        dict(id='p5', m0=108, tipo='n', toma='IMG_7885', n0=32, nf=18, caja=FULL),
        dict(id='p6', m0=126, tipo='z', toma=c['p6'][0], n0=c['p6'][1], zs=z6[0], cxs=z6[1], cys=z6[2]),
        p7,
        dict(id='p8', m0=154, tipo='z', toma=c['p8'][0], n0=c['p8'][1], zs=z8[0], cxs=z8[1], cys=z8[2]),
        dict(id='p9', m0=166, tipo='n', toma='IMG_7885', n0=50, nf=82, caja=FULL),
        dict(id='p10-11', m0=248, tipo='n', toma='IMG_4530', n0=0, nf=87, caja=None),      # 1080×1920 nativo
    ]


def etapa_planos():
    P.mkdir(parents=True, exist_ok=True)
    if not ROCCE_4K.exists():
        medir_rocce_4k()
    reg = []
    v01 = {r['id']: r for r in json.load(open(T / 'planos.json'))['planos']} if VER != 'v01' else {}
    for p in plan_planos():
        out = P / f"{p['id']}.mp4"
        if p['id'] in v01 and (p['id'] not in ('p6', 'p7', 'p8') or CADENA[VER][p['id']] == CADENA['v01'][p['id']]):
            # plano sin cambios: el MISMO archivo intermedio de v01 (una recodificación x264 no es bit a bit igual)
            shutil.copy2(T / 'planos' / out.name, out)
            r = dict(v01[p['id']], salida=str(out), reutilizado_de_v01=True)
            reg.append(r); print(p['id'], r['cuadros'], 'reutilizado de v01', flush=True)
            continue
        if p['tipo'] == 'n':
            r = U.plano_n(p['toma'], p['n0'], p['nf'], out, caja=p['caja'])
        else:
            r = U.plano_z(p['toma'], p['n0'], p['zs'], p['cxs'], p['cys'], out, caja=FULL)
        r.update(id=p['id'], m0=p['m0'])
        reg.append(r); print(p['id'], r['cuadros'], flush=True)
    assert [r['m0'] for r in reg] == list(np.cumsum([0] + [r['cuadros'] for r in reg[:-1]]))
    n = V.unir(reg, TV / 'v5_base0.mp4')
    assert n == NF, n
    jdump(dict(cuadros=n, planos=reg), TV / 'planos.json')
    print('total', n)



# =====================================================================================================
# etiquetas de prenda · objeto con sombra que cae en 4 cuadros con rebote (capa RGBA por cuadro, encima de todo)
# =====================================================================================================
F_EXTRA = '/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf'
HUESO = (0xF4, 0xF1, 0xEA)
TINTA = (0x12, 0x12, 0x12)
ETQ = T / 'etiquetas'
# texto exacto, cuadro de impacto (aterriza), centro final (x, y) y giro final (grados, + = antihorario)
ETIQUETAS = [   # posiciones verticales buscadas para que ninguna etiqueta tape el texto de otra (≥ 4 px de aire)
    dict(txt='AGRANDADO.', n=M['e1'], c=(350, 475), giro=5.0),
    dict(txt='¿Quién te creés?', n=M['e2'], c=(600, 562), giro=-4.0),
    dict(txt='Bajá un cambio.', n=M['e3'], c=(345, 625), giro=-4.5),
    dict(txt='Eso no es para vos.', n=M['e4'], c=(490, 714), giro=5.0),
]
FS_ETQ = 54
# caída: 4 cuadros hasta el impacto (k = 0..3, impacto en k = 3) y rebote en k = 4, 5
CAIDA = [  # (escala, desplazamiento y, giro extra, altura sobre la superficie 0..1)
    (1.42, -150, 9.0, 1.00), (1.24, -78, 5.0, 0.62), (1.08, -24, 1.8, 0.25), (0.965, 5, -0.6, 0.0),
    (1.012, -3, 0.25, 0.04), (1.0, 0, 0.0, 0.0)]
SALIDA = [  # desde el cuadro M['salida'] (3,40 s), 5 cuadros: (desplazamiento x × sentido, y, giro extra × sentido)
    (30, 4, 1.5), (120, 12, 4.0), (300, 22, 7.0), (600, 32, 10.0), (1100, 40, 13.0)]
SUPER = 2   # la etiqueta se dibuja al doble y se reduce al componer (bordes limpios)


def _etiqueta_img(txt, fs=FS_ETQ):
    """etiqueta tejida de prenda (RGBA, a SUPER×): rectángulo hueso con extremos doblados (franja apenas más oscura),
    costura punteada cerca de cada extremo, trama horizontal fina, sombreado de tela (más clara arriba) y el texto en
    Inter Display ExtraBold negra centrado ópticamente."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    S = SUPER
    f = ImageFont.truetype(F_EXTRA, fs * S)
    x0, y0, x1, y1 = f.getbbox(txt)
    tw, th = x1 - x0, y1 - y0
    cap = f.getbbox('H')[3] - f.getbbox('H')[1]
    padx, pady, doblez = 34 * S, 16 * S, 12 * S
    w, h = tw + 2 * padx + 2 * doblez, cap + 2 * pady + int(0.5 * cap)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    base = np.zeros((h, w, 3), np.float32) + np.array(HUESO, np.float32)
    yy = np.linspace(0, 1, h)[:, None]
    base *= (1.015 - 0.045 * yy)[..., None]                       # tela: luz de arriba
    rng_ = np.random.default_rng(len(txt) * 7 + fs)
    trama = (np.arange(h) // (2 * S) % 2)[:, None] * 0.012        # trama horizontal tejida
    base *= (1 - trama)[..., None]
    base *= (1 + rng_.normal(0, 0.010, (h, w)))[..., None]       # grano de hilo
    xx = np.arange(w)[None, :]
    dobl = ((xx < doblez) | (xx >= w - doblez)).astype(np.float32)
    base *= (1 - 0.055 * dobl)[..., None]                         # extremos doblados
    a = np.full((h, w), 255, np.uint8)
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert('RGBA')
    im.putalpha(Image.fromarray(a))
    d = ImageDraw.Draw(im)
    # costura punteada a 9 px del doblez
    for xc in (doblez + 8 * S, w - doblez - 8 * S):
        for yc in range(7 * S, h - 7 * S, 9 * S):
            d.line([(xc, yc), (xc, yc + 5 * S)], fill=(0xC9, 0xC2, 0xB4, 255), width=2 * S)
    # línea fina del doblez
    for xc in (doblez, w - doblez):
        d.line([(xc, 0), (xc, h)], fill=(0xD8, 0xD2, 0xC6, 255), width=S)
    tx = (w - tw) // 2 - x0
    ty = (h - cap) // 2 - (f.getbbox('H')[1])
    d.text((tx, ty), txt, font=f, fill=TINTA + (255,))
    # esquinas apenas redondeadas (tela cortada)
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=3 * S, fill=255)
    im.putalpha(Image.fromarray(np.minimum(np.asarray(im)[..., 3], np.asarray(m))))
    return im


def _transformar(img, escala, giro):
    from PIL import Image
    w, h = img.size
    im = img.resize((max(1, int(round(w * escala / SUPER))), max(1, int(round(h * escala / SUPER)))), Image.LANCZOS)
    return im.rotate(giro, resample=Image.BICUBIC, expand=True)


def _estado(e, n):
    """(visible, escala, cx, cy, giro, altura) de la etiqueta e en el cuadro n del máster."""
    k = n - (e['n'] - 3)
    if k < 0 or n >= M['salida'] + len(SALIDA):
        return None
    cx, cy = e['c']; g = e['giro']
    sgn = -1 if e['c'][0] < 540 else 1                         # sale por el costado más cercano
    if n >= M['salida']:
        dx, dy, dg = SALIDA[n - M['salida']]
        return (1.0, cx + sgn * dx, cy + dy, g + sgn * -dg, 0.0)
    esc, dy, dg, alt = CAIDA[min(k, len(CAIDA) - 1)]
    return (esc, cx, cy + dy, g + dg * (1 if g >= 0 else -1), alt)


def capa_etiquetas(n, imgs=None):
    """RGBA 1080×1920 del cuadro n: sombra suave + sombra de contacto (proyectadas sobre la escena, más lejanas y
    difusas mientras la etiqueta está en el aire) y la etiqueta; las posteriores encima."""
    from PIL import Image, ImageFilter
    imgs = imgs or [_etiqueta_img(e['txt']) for e in ETIQUETAS]
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for e, img in zip(ETIQUETAS, imgs):
        st = _estado(e, n)
        if st is None:
            continue
        esc, cx, cy, g, alt = st
        im = _transformar(img, esc, g)
        x = int(round(cx - im.width / 2)); y = int(round(cy - im.height / 2))
        al = im.split()[3]
        for off, blur, op in ((10 + 46 * alt, 13 + 22 * alt, 0.36 * (1 - 0.45 * alt)), (3 + 30 * alt, 2.5 + 10 * alt, 0.30 * (1 - 0.8 * alt))):
            sh = Image.new('RGBA', im.size, (8, 10, 14, 0)); sh.putalpha(al.point(lambda v, o=op: int(v * o)))
            pad = int(blur * 3) + 2
            shp = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (8, 10, 14, 0)); shp.paste(sh, (pad, pad))
            shp = shp.filter(ImageFilter.GaussianBlur(blur))
            _pegar(capa, shp, x - pad + int(off * 0.35), y - pad + int(off))
        _pegar(capa, im, x, y)
    return capa


def _pegar(capa, im, x, y):
    """alpha_composite que admite salir del cuadro (la etiqueta se va por el costado)."""
    from PIL import Image
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + im.width), min(H, y + im.height)
    if x1 <= x0 or y1 <= y0:
        return
    capa.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))



# =====================================================================================================
# etapa color · (1) Blanca neutra solo sobre la Blanca (método de life_v2/pines: ganancias por franja de L por plano +
# residuo por cuadro suavizado; el resto del cuadro queda idéntico) · (2) saturación que baja con cada etiqueta
# (−25/−50/−75 %: croma × 0,75/0,50/0,25 desde el cuadro de impacto) y vuelve entera en el giro · (3) destello de 2 c en
# el giro · (4) barrido horizontal (desenfoque direccional) en el corte al reenganche
# =====================================================================================================
COLOR5 = {   # plano: (cuadros del máster, cuadros de medición, caja de búsqueda de la Blanca en 1080×1920, suavizado)
    'p1-4': ((0, 107), (20, 50, 80, 100), (60, 790, 820, 1260), (5, 7)),
    'p5': ((108, 125), (110, 115, 120, 124), (250, 560, 820, 1000), (3, 3)),
    'p6': ((126, 140), (127, 131, 135, 139), (0, 0, 1080, 1920), (3, 3)),
    'p7': ((141, 153), (142, 145, 148, 152), (0, 600, 1080, 1920), (3, 3)),
    'p8': ((154, 165), (155, 158, 161, 164), (0, 800, 1080, 1920), (3, 3)),
    'p9': ((166, 247), (170, 195, 220, 245), (0, 450, 1000, 1500), (5, 7)),
    'p10-11': ((248, 334), (255, 280, 305, 330), (0, 640, 1080, 1920), (5, 7)),
}


def saturacion(n):
    if M['p5'] <= n:
        return 1.0
    if n >= M['e4']:
        return 0.25
    if n >= M['e3']:
        return 0.50
    if n >= M['e2']:
        return 0.75
    return 1.0


DESTELLO = {M['p5']: 0.85, M['p5'] + 1: 0.35}                   # fracción hacia el blanco (Y 235, croma neutra)
BARRIDO = {M['p10'] - 2: 10, M['p10'] - 1: 30, M['p10']: 30, M['p10'] + 1: 10}   # ancho del desenfoque horizontal (px)


def etapa_color():
    from scipy.ndimage import uniform_filter1d
    base0, base = TV / 'v5_base0.mp4', TV / 'v5_base.mp4'
    ny = W * H; nc = ny // 4
    rep = dict(metodo=('Blanca: método de scripts/life/life_v2.py (etapa_color, aprobado en V1/V2) por plano: ganancias '
                       'por franja de L medidas en 4 cuadros + residuo por cuadro (cara iluminada de la tela visible) '
                       'suavizado; peso 0 en el celeste, las letras, la piel, la arena, las rocas y la Negra; solo se '
                       'reescriben los píxeles con peso > 0,002. Después, sobre el cuadro entero: croma × saturación '
                       '(0,75 desde c36, 0,50 desde c60, 0,25 desde c75 hasta c107), destello c108–c109 y barrido '
                       'c246–c249.'), planos={})
    G = {}
    for pl, (rango, medir, caja, _) in COLOR5.items():
        rgbs = [L2.yuv_rgb(*L2.leer_yuv(base0, n)) for n in medir]
        cent, gan, med = L2.ganancias_toma(rgbs, caja)
        G[pl] = (cent, gan)
        rep['planos'][pl] = dict(cuadros_master=list(rango), medicion=list(medir), caja=list(caja), franjas=med)
        print(pl, json.dumps(med, ensure_ascii=False), flush=True)
    plano_de = {n: pl for pl, (r, _, _, _) in COLOR5.items() for n in range(r[0], r[1] + 1)}
    assert sorted(plano_de) == list(range(NF))

    def cuadros():
        dec = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(base0), '-f', 'rawvideo',
                                     '-pix_fmt', 'yuv420p', '-']), stdout=subprocess.PIPE)
        k = 0
        while True:
            b = dec.stdout.read(ny + 2 * nc)
            if len(b) < ny + 2 * nc:
                break
            yield k, b
            k += 1
        dec.stdout.close(); dec.wait()

    # pasada 1: residuo por cuadro a media resolución
    res = {}
    for k, b in cuadros():
        pl = plano_de[k]; x0, y0, x1, y1 = COLOR5[pl][2]
        Y, Cb, Cr = L2.partir(b)
        Yh = Y.reshape(H // 2, 2, W // 2, 2).mean((1, 3))
        y = (Yh - 16) / 219; u = (Cb.astype(np.float32) - 128) / 224; v = (Cr.astype(np.float32) - 128) / 224
        Rr = y + 1.5748 * v; Bb = y + 1.8556 * u; Gg = (y - 0.2126 * Rr - 0.0722 * Bb) / 0.7152
        rgb = np.stack([Rr, Gg, Bb], -1) * 255.0
        a0 = L2.AREA_MIN; L2.AREA_MIN = a0 // 4
        try:
            bl, _, _ = L2.blanca(rgb, (x0 // 2, y0 // 2, x1 // 2, y1 // 2))
        finally:
            L2.AREA_MIN = a0
        res[k] = L2.residuo(rgb, bl, *G[pl])
    RES = {}
    for pl, ((a, b_), _, _, (md_, mm_)) in COLOR5.items():
        sm = L2.suavizar([res.get(n) for n in range(a, b_ + 1)], md_, mm_)
        for i, n in enumerate(range(a, b_ + 1)):
            RES[n] = sm[i]
    rep['residuo_por_cuadro'] = {n: dict(medido=None if res.get(n) is None else [round(float(x), 4) for x in res[n]],
                                         suavizado=[round(float(x), 4) for x in RES[n]]) for n in sorted(RES)}
    # pasada 2: aplicar
    enc = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{W}x{H}',
                                 '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                                 '-color_trc', 'bt709', '-i', '-', '-c:v', 'libx264', '-threads', '2', '-qp', '0',
                                 '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries',
                                 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', str(base)]), stdin=subprocess.PIPE)
    por_cuadro = {}; n_out = 0
    for k, b in cuadros():
        pl = plano_de[k]; caja = COLOR5[pl][2]
        cent, gan = G[pl]
        Y, Cb, Cr = L2.partir(b)
        rgb = L2.yuv_rgb(Y, Cb, Cr)
        rgb2, w, bl = L2.corregir(rgb, caja, cent, gan * RES[k][None, :])
        Y2, Cb2, Cr2 = L2.rgb_yuv(rgb2)
        mw = w > 0.002
        mc = mw.reshape(H // 2, 2, W // 2, 2).any((1, 3))
        Yo = np.where(mw, np.clip(np.round(Y2), 0, 255), Y).astype(np.float32)
        Cbo = np.where(mc, np.clip(np.round(Cb2), 0, 255), Cb).astype(np.float32)
        Cro = np.where(mc, np.clip(np.round(Cr2), 0, 255), Cr).astype(np.float32)
        rgb_d = L2.yuv_rgb(Yo.astype(np.uint8), Cbo.astype(np.uint8), Cro.astype(np.uint8))
        fila = dict(plano=pl, pct_luma_tocada=round(float(mw.mean() * 100), 2), blanca_px=int(bl.sum()),
                    tela_antes=L2.tela_br(rgb, bl), tela_despues=L2.tela_br(rgb_d, bl),
                    celeste_antes=L2.celeste(rgb, bl), celeste_despues=L2.celeste(rgb_d, bl))
        s_ = saturacion(k)
        if s_ != 1.0:
            Cbo = 128 + (Cbo - 128) * s_; Cro = 128 + (Cro - 128) * s_
        if k in DESTELLO:
            a = DESTELLO[k]
            Yo = Yo + (235 - Yo) * a; Cbo = 128 + (Cbo - 128) * (1 - a); Cro = 128 + (Cro - 128) * (1 - a)
        if k in BARRIDO:
            r = BARRIDO[k]
            Yo = uniform_filter1d(Yo, r, axis=1, mode='nearest')
            Cbo = uniform_filter1d(Cbo, max(1, r // 2), axis=1, mode='nearest')
            Cro = uniform_filter1d(Cro, max(1, r // 2), axis=1, mode='nearest')
        fila.update(saturacion=s_, destello=DESTELLO.get(k, 0.0), barrido_px=BARRIDO.get(k, 0))
        por_cuadro[k] = fila
        b = (np.clip(np.round(Yo), 0, 255).astype(np.uint8).tobytes() + np.clip(np.round(Cbo), 0, 255).astype(np.uint8).tobytes()
             + np.clip(np.round(Cro), 0, 255).astype(np.uint8).tobytes())
        enc.stdin.write(b); n_out += 1
    enc.stdin.close(); enc.wait()
    assert n_out == NF and enc.returncode == 0, (n_out, enc.returncode)
    rep['por_cuadro'] = por_cuadro
    MEDV.mkdir(parents=True, exist_ok=True)
    jdump(rep, MEDV / 'color.json')
    for pl, ((a, b_), _, _, _) in COLOR5.items():
        an = [por_cuadro[n]['tela_antes']['b_menos_r'] for n in range(a, b_ + 1) if por_cuadro[n]['tela_antes']]
        de = [por_cuadro[n]['tela_despues']['b_menos_r'] for n in range(a, b_ + 1) if por_cuadro[n]['tela_despues']]
        print(pl, 'B−R antes', np.median(an) if an else None, '· después', np.median(de) if de else None,
              (min(de), max(de)) if de else None, 'cuadros con medida', len(de), 'de', b_ - a + 1, flush=True)



def etapa_etiquetas():
    """PNG RGBA 1080×1920 por cuadro c0–c107 (capa de etiquetas con sombra) + prueba de la condición 3 de Roma: la caja
    del alfa (> 2/255, sombra incluida) de cada cuadro entre 0 y 3,60 s nunca baja de y 940."""
    ETQ.mkdir(parents=True, exist_ok=True)
    imgs = [_etiqueta_img(e['txt']) for e in ETIQUETAS]
    filas = []
    for n in range(M['p5']):
        capa = capa_etiquetas(n, imgs)
        capa.save(ETQ / f'e_{n:04d}.png', compress_level=3)
        al = np.asarray(capa)[..., 3]
        ys, xs = np.nonzero(al > 2)
        visibles = [e['txt'] for e in ETIQUETAS if _estado(e, n) is not None]
        filas.append(dict(cuadro=n, t=round(n / FPS, 3), etiquetas=visibles,
                          caja_alfa=None if len(ys) == 0 else [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                          y_max=None if len(ys) == 0 else int(ys.max())))
    ymax = max(f['y_max'] for f in filas if f['y_max'] is not None)
    ymin = min(f['caja_alfa'][1] for f in filas if f['caja_alfa'])
    assert ymax < 940, ymax
    rep = dict(condicion='Roma V5 §3: etiquetas nunca debajo de y 940 entre 0 y 3,60 s (c0–c107)',
               y_max_alfa_con_sombra=ymax, y_min_alfa=ymin, cumple=ymax < 940, por_cuadro=filas,
               etiquetas=[dict(e, tam_px=[i.width // SUPER, i.height // SUPER]) for e, i in zip(ETIQUETAS, imgs)],
               caida=CAIDA, salida=SALIDA)
    jdump(rep, MED / 'etiquetas.json')
    print('etiquetas: y máx del alfa (con sombra)', ymax, '· y mín', ymin, flush=True)


# =====================================================================================================
# etapa placa · sistema Roccé Life (pines + V1/V2): degradé + Instrument Serif con cursiva + firma con el logo original
# =====================================================================================================
FUENTES = R / 'scripts' / 'fuentes'
LOGO = R / 'LOGO' / 'rocce_logo.png'
PLACAS = {
    # resolución (paso 9): la frase del pin P4 (texto y salto de línea del guion), alineada a la izquierda como el pin
    'resolucion': dict(html='Querer más<br>no te hace <em>agrandado</em>.', txt='Querer más\\Nno te hace *agrandado*.',
                       fs=96, top=284, alinear='left', grad=(640, 0.74)),
    # CTA (paso 11): texto exacto del guion, sin cursiva (el guion no marca ninguna), centrado como V1/V2
    # degradé del CTA más denso (alto, opacidad arriba, posición y factor del punto medio): con (760, 0.70) del sistema
    # V1/V2 solo el 33 % del trazo llegaba a 3:1 sobre el cielo nublado claro de 4530 (control v01, mediana 2,75:1);
    # con (720, 0.90, 0.55, 0.90) el 100 % pasa 4,5:1 y el degradé termina en y 720, arriba de la remera (y ≈ 700–760)
    'cta': dict(html='Mandáselo a quien<br>está construyendo lo suyo.', txt='Mandáselo a quien\\Nestá construyendo lo suyo.',
                fs=82, top=300, alinear='center', grad=(720, 0.90, 0.55, 0.90)),
}
FIRMA = dict(logo=96, ffs=30, top=500)
CSS5 = """
@font-face{font-family:'IS';src:url('file://%(F)s/InstrumentSerif-Regular.ttf')}
@font-face{font-family:'ISI';src:url('file://%(F)s/InstrumentSerif-Italic.ttf')}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:transparent}
.grad{position:absolute;left:0;right:0;top:0}
.frase{position:absolute;left:72px;right:72px;font-family:'IS';font-weight:400;color:#FFFFFF;
  line-height:1.0;letter-spacing:-0.012em;text-shadow:0 2px 24px rgba(0,0,0,.28);font-feature-settings:'kern','liga'}
.frase em{font-family:'ISI';font-style:normal}
.firma{position:absolute;left:50%%;transform:translateX(-50%%);display:flex;align-items:center;gap:16px}
.firma img{width:%(logo)dpx;height:%(logo)dpx;border-radius:%(radio)dpx;display:block}
.firma span{font-family:'Inter';font-weight:500;font-size:%(ffs)dpx;letter-spacing:.34em;margin-right:-.34em;
  color:#FFFFFF;text-shadow:0 1px 8px rgba(0,0,0,.35)}
"""


def etapa_placa():
    C = T / 'placa'; C.mkdir(parents=True, exist_ok=True)
    t = dict(F=FUENTES, logo=FIRMA['logo'], radio=round(FIRMA['logo'] * 0.11), ffs=FIRMA['ffs'])
    docs = {}
    for k, p_ in PLACAS.items():
        alto, op, pm, fm = (tuple(p_['grad']) + (0.45, 0.55))[:4]; r, g, b = (12, 18, 26)
        grad = (f'<div class="grad" style="height:{alto}px;background:linear-gradient(to bottom,rgba({r},{g},{b},{op}) 0%,'
                f'rgba({r},{g},{b},{op * fm:.3f}) {pm * 100:.0f}%,rgba({r},{g},{b},0) 100%)"></div>')
        docs[f'{k}_frase'] = (f'{grad}<div class="frase" style="top:{p_["top"]}px;font-size:{p_["fs"]}px;'
                              f'text-align:{p_["alinear"]}">{p_["html"]}</div>')
        docs[f'{k}_solo_degrade'] = grad                                   # para medir contraste sin el texto
    docs['cta_firma'] = (f'<div class="firma" style="top:{FIRMA["top"]}px"><img src="file://{LOGO}">'
                         f'<span>ROCCÉ LIFE</span></div>')
    trabajos = []
    for nombre, cuerpo in docs.items():
        h = C / f'{nombre}.html'
        h.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS5 % t}</style></head>'
                     f'<body>{cuerpo}</body></html>', encoding='utf-8')
        trabajos.append(dict(html=str(h), out=str(C / f'{nombre}.png'), w=W, h=H))
    (C / '_trabajos.json').write_text(json.dumps(trabajos, indent=1))
    subprocess.run(nice(['node', str(R / 'scripts' / 'life' / 'life_v2_render.js'), str(C / '_trabajos.json')]), check=True)
    from PIL import Image
    rep = {}
    for tr in trabajos:
        im = Image.open(tr['out']); a = np.asarray(im)
        assert im.size == (W, H) and im.mode == 'RGBA', (im.size, im.mode)
        al = a[..., 3]; filas = np.nonzero((al > 8).any(1))[0]; cols = np.nonzero((al > 8).any(0))[0]
        rep[Path(tr['out']).name] = dict(md5_pixeles=hashlib.md5(a.tobytes()).hexdigest(),
                                         caja_alfa_gt8=None if len(filas) == 0 else
                                         [int(cols.min()), int(filas.min()), int(cols.max()), int(filas.max())])
    for k in PLACAS:
        a = np.asarray(Image.open(C / f'{k}_frase.png')).astype(int)
        m = (a[..., 3] > 200) & (a[..., :3].min(-1) > 200)
        ys, xs = np.nonzero(m)
        rep[f'{k}_letras'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    a = np.asarray(Image.open(C / 'cta_firma.png')).astype(int)
    ys, xs = np.nonzero(a[..., 3] > 8)
    rep['firma'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    jdump(rep, C / 'placa.json')
    print(json.dumps(rep, ensure_ascii=False))



# =====================================================================================================
# etapa audio · ambiente real + foley + música TEMP propia (Mi menor). Cada etiqueta: «sello» y el pasabajos de la
# música se cierra (9 kHz → 3,5 → 1,6 → 0,8 → 0,42 kHz); subida, salida, hueco 3,53–3,60 y DROP con el filtro abierto en
# el giro; el bajo sube una nota en cada «Otra.» (Mi–Sol–La–Si) y resuelve en Mi con el pad en la resolución.
# =====================================================================================================
def ts(n):
    return n / FPS


XF5 = 0.03
FILTRO = [(0.0, 9000.0), (ts(M['e1']), 3500.0), (ts(M['e2']), 1600.0), (ts(M['e3']), 800.0), (ts(M['e4']), 420.0)]
HUECO = (ts(M['hueco']), ts(M['p5']))


def sello(m, t, g=0.55):
    """etiqueta de tela que golpea: golpe grave corto (95→55 Hz, 70 ms) + palmada de tela (ruido 700–3200 Hz, 25 ms)
    + roce breve (ruido 2,5–7 kHz, 12 ms antes del golpe). Sintetizado, sin material de terceros."""
    from sonido import filt, ruido, satur, SR as _SR
    L = int(0.35 * _SR); tt_ = np.arange(L) / _SR
    f = 55 + 40 * np.exp(-tt_ / 0.02)
    golpe = np.sin(2 * np.pi * np.cumsum(f) / _SR) * np.exp(-tt_ / 0.07)
    palm = filt(ruido(L), 'band', [700, 3200]) * np.exp(-tt_ / 0.025)
    palm /= np.abs(palm).max() + 1e-9
    s_ = satur(0.9 * golpe + 0.55 * palm, 1.5)
    pre = int(0.012 * _SR)
    roce = filt(ruido(pre), 'band', [2500, 7000]) * np.linspace(0, 1, pre) ** 2
    roce /= np.abs(roce).max() + 1e-9
    m.put('fx', np.concatenate([0.18 * roce, s_]), t - 0.012, g)
    m.rev(s_ * g * 0.18, t, seg=0.9)
    m.log(t, 'sello')


def pasabajos_variable(x, puntos, t_fin, glide=0.05, bloque=256):
    """pasabajos Butterworth de 4.º orden con frecuencia de corte por escalones (puntos = [(t, fc)]) y deslizamiento
    exponencial de `glide` s entre escalones; estado del filtro arrastrado entre bloques. Después de t_fin no filtra."""
    from scipy.signal import butter, sosfilt
    from sonido import SR as _SR
    y = x.copy(); n_fin = int(t_fin * _SR)
    zi = np.zeros((2, 2, x.shape[1]))
    fc = puntos[0][1]
    for i in range(0, min(n_fin, len(x)), bloque):
        t = i / _SR
        obj = [f for (t0, f) in puntos if t0 <= t][-1]
        fc = obj + (fc - obj) * np.exp(-bloque / _SR / glide)
        sos = butter(4, fc, btype='low', fs=_SR, output='sos')
        y[i:i + bloque], zi = sosfilt(sos, x[i:i + bloque], axis=0, zi=zi)
    return y


def ambientes5(m):
    s = lambda toma, src0, t0, t1, g, **kw: m.ambiente(toma, src0, t0, t1, g, **kw)
    s('IMG_7887', 0.000, 0.000, HUECO[0], -4, hp=50, fin_fade=0.03)                   # la ola real del hook
    s('IMG_7885', 32 / FPS, ts(M['p5']), ts(M['p6']), -7, hp=50, ini_fade=0.005, fin_fade=XF5)   # la ola del giro
    s('IMG_8008', 47 / FPS, ts(M['p6']), ts(M['p7']), -3, hp=80, fade=XF5)
    s('IMG_8002', 90 / FPS, ts(M['p7']), ts(M['p8']), 4, hp=80, fade=XF5)
    s('IMG_8004', 97 / FPS, ts(M['p8']), ts(M['p9']), 5, hp=80, fade=XF5)
    s('IMG_7885', 50 / FPS, ts(M['p9']), ts(M['p10']), -3, hp=50, fade=XF5)           # mar de la resolución
    s('IMG_7896', 1.500, ts(M['p10']), DUR, 2, hp=50, ini_fade=XF5, fin_fade=0.4)       # mar (sin el audio de 4530)


def foley5(m):
    for e in ETIQUETAS:
        sello(m, ts(e['n']))
    m.obturador(ts(M['obt1']), .45)                    # ≈ 1,55: está sacando la foto (pista 1)
    m.barrido(ts(M['salida']) + 0.10, .28, .16)        # las etiquetas se van por los costados (3,40)
    for n in (M['p5'], M['p6'], M['p7'], M['p8']):     # giro y cada «Otra.» sobre un obturador
        m.obturador(ts(n), .70)
    m.impacto(ts(M['p8']), .42)                        # «Otra.» final: ROCCÉ llena el ancho
    m.barrido(ts(M['p10']), .30, .14); m.toque(ts(M['p10']), .17, 2400)       # reenganche


def musica5(m):
    ch = lambda t0, t1, g=.07, paso=0.3: [m.charles(round(float(t), 3), g) for t in np.arange(t0, t1 - 1e-6, paso)]
    # A · 0–3,53: groove a 100 BPM que se va apagando con cada etiqueta (pasabajos variable, abajo)
    for t, g in ((0.0, .55), (0.6, .55), (1.2, .6), (1.8, .6), (2.4, .62), (3.0, .62)):
        m.bombo(t, g, f0=105)
    ch(0.3, 3.5, .06, 0.6)
    m.ocho08(0.0, 40, 1.1, .45); m.ocho08(1.2, 36, 1.1, .45); m.ocho08(2.4, 38, 1.0, .45)
    m.pad(0.0, [52, 55, 59], 1.15, .05, 2600, a=.05); m.pad(1.2, [48, 52, 55], 1.15, .05, 2600)
    m.pad(2.4, [50, 54, 57], 1.05, .05, 2600)
    m.campana(0.0, 76, .05)
    A = HUECO[0]
    for k in ('mus', 'bombo'):
        m.pistas[k] = pasabajos_variable(m.pistas[k], FILTRO, A)
    m.subida(2.95, A, .17)
    # B · DROP en el giro (3,60) y cadena «Otra.»: golpe y nota de bajo en cada corte (Mi–Sol–La–Si, acelera)
    m.impacto(ts(M['p5']), .45); m.campana(ts(M['p5']), 83, .06)
    for n, nota, dur in ((M['p5'], 40, .6), (M['p6'], 43, .5), (M['p7'], 45, .43), (M['p8'], 47, .4)):
        m.bombo(ts(n), .95); m.ocho08(ts(n), nota, dur, .55, glide_desde=nota + 7 if n == M['p5'] else None)
    m.pad(ts(M['p5']), [52, 55, 59, 64], ts(M['p9']) - ts(M['p5']) - .05, .055, 2600)
    # sin palmas en los cortes: en v01 la palma caía en el mismo instante que el obturador y lo tapaba en 2–8 kHz
    # (control: obturador −38 dBFS contra música −38/−37 en 4,20 y 4,70); el obturador hace de palma
    # charles cada 0,15 s, salvo a ±40 ms de un obturador de la cadena (en v01 uno caía justo en 4,20)
    for t in np.arange(ts(M['p5']) + .15, ts(M['p9']) - .02 - 1e-6, 0.15):
        if min(abs(t - ts(n)) for n in (M['p6'], M['p7'], M['p8'])) > 0.04:
            m.charles(round(float(t), 3), .07)
    # C · resolución (5,53–8,27): pad + mar, bajo largo en Mi, sin batería
    m.pad(ts(M['p9']), [40, 52, 55, 59, 66], ts(M['p10']) - ts(M['p9']), .065, 1800, a=.35)
    m.ocho08(ts(M['p9']), 28, 2.2, .35); m.campana(ts(M['p9']), 71, .05, 1.4)
    # D · reenganche (8,27–9,27)
    m.bombo(ts(M['p10']), .6); m.pad(ts(M['p10']), [48, 52, 55], .95, .055, 2000); ch(ts(M['p10']) + .3, ts(M['p11']), .05)
    m.ocho08(ts(M['p10']), 36, .9, .4)
    # E · CTA: cadencia Re → Mi menor y fundido 10,67–11,17
    t1 = ts(M['p11']); t2 = t1 + 0.6
    m.bombo(t1, .7); m.pad(t1, [50, 54, 57], .55, .06, 2200); m.ocho08(t1, 38, .55, .45)
    m.bombo(t2, .8); m.pad(t2, [52, 55, 59, 64], DUR - t2, .065, 2200, r=.5); m.ocho08(t2, 40, 1.4, .45)
    m.campana(t2, 76, .06, 1.0)
    ch(t1 + .3, DUR - .4, .05)


OBTURADORES = [ts(M['obt1']), ts(M['p6']), ts(M['p7']), ts(M['p8'])]   # el de 3,60 va con el drop: sin hueco extra
ABRIR = dict(antes=0.03, plano=0.09, salida=0.12, mus_db=-9.0, amb_db=-8.0, corte_hz=1500)


def huecos_y_final(m):
    """hueco 3,533–3,600: la rampa de 15 ms va ANTES del hueco y la ganancia vuelve a 1 justo en 3,600 (rampa de 1 ms
    que termina en 3,600). En v01 (control) la rampa de vuelta caía en 3,600–3,615 y se comía el ataque del drop y el
    primer clic del obturador del giro (fx a −62,7 dBFS en 2–8 kHz en la versión sin música).
    Obturadores: banda alta (≥ 1,5 kHz) de música/bombo −9 dB y de ambiente −8 dB desde 30 ms antes hasta 90 ms después,
    con salida en 120 ms.
    Medido en v01: en 4,20 y 4,70 la música (charles y palmas) quedaba ~10 dB por encima del obturador en 2–8 kHz."""
    i0, i1 = int(HUECO[0] * SR), int(HUECO[1] * SR); k = int(0.015 * SR); k1 = int(0.001 * SR)
    g = np.ones(m.N); g[i0 - k:i0] = np.linspace(1, 0, k); g[i0:i1 - k1] = 0; g[i1 - k1:i1] = np.linspace(0, 1, k1)
    for p_ in ('amb', 'fx', 'mus', 'bombo'):
        m.pistas[p_] *= g[:, None]
    from scipy.signal import butter, sosfiltfilt
    sos_bajo = butter(4, ABRIR['corte_hz'], 'low', fs=SR, output='sos')
    for p_, d_ in (('mus', ABRIR['mus_db']), ('bombo', ABRIR['mus_db']), ('amb', ABRIR['amb_db'])):
        g = np.ones(m.N); a = 10 ** (d_ / 20)
        for t in OBTURADORES:
            j0 = int((t - ABRIR['antes']) * SR); j1 = int((t + ABRIR['plano']) * SR); j2 = j1 + int(ABRIR['salida'] * SR)
            r0 = int(0.01 * SR)
            seg = np.ones(j2 - j0 + r0)
            seg[:r0] = np.linspace(1, a, r0); seg[r0:r0 + j1 - j0] = a; seg[r0 + j1 - j0:] = np.linspace(a, 1, j2 - j1)
            g[j0 - r0:j2] = np.minimum(g[j0 - r0:j2], seg)
        # solo la banda alta (≥ 1,5 kHz, división de fase cero: bajo + alto = original): el bajo y el bombo de cada corte
        # (Mi–Sol–La–Si) conservan su golpe; en la primera prueba, con el despeje de banda completa, el impacto de 5,13
        # subía apenas +1,1 dB en 30–150 Hz
        bajo = sosfiltfilt(sos_bajo, m.pistas[p_], axis=0)
        m.pistas[p_] = bajo + (m.pistas[p_] - bajo) * g[:, None]
    m.log(OBTURADORES[0], f"obturadores despejados: música/bombo {ABRIR['mus_db']} dB, ambiente {ABRIR['amb_db']} dB")
    m.fundido('mus', DUR - 0.5, DUR); m.fundido('bombo', DUR - 0.5, DUR)
    m.fundido('fx', DUR - 0.35, DUR)


def etapa_audio():
    from sonido import Mezcla
    A.mkdir(parents=True, exist_ok=True)
    m = Mezcla(DUR); ambientes5(m); foley5(m); musica5(m); huecos_y_final(m)
    r1 = m.exportar(str(A / 'v5_completa.wav'), lufs=-14)
    s_ = Mezcla(DUR); ambientes5(s_); foley5(s_); huecos_y_final(s_)
    r2 = s_.exportar(str(A / 'v5_sinmusica.wav'), lufs=-14)
    out = dict(filtro_musica=FILTRO, hueco=HUECO, exportar_completa=r1, exportar_sinmusica=r2, eventos=m.ev)
    for k, r in (('completa', r1), ('sinmusica', r2)):
        if r[1] > -1.5:
            out[f'limitado_{k}'] = L2.limitar_tp(A / f'v5_{k}.wav')
        out[k] = dict(zip(('lufs', 'pico_dbtp', 'lra'), L2.medir_ebur(A / f'v5_{k}.wav')))
        print(k, out[k], flush=True)
    jdump(out, A / 'audio.json')



# =====================================================================================================
# textos (exactos del guion; tamaños de la base común: hook CajaN \fs120, pasos \fs104, palabra fuerte Grande \fs124)
# =====================================================================================================
TEXTOS5 = [
    dict(n=(M['p1'], M['p5'] - 1), txt='Querés más.', estilo='CajaN', y=270, pop=True, extra='\\fs120\\xbord33\\ybord10'),
    dict(n=(M['p5'], M['p6'] - 1), txt='Querés otra.', estilo='Grande', y=300, pop=True, extra='\\fs124'),
    dict(n=(M['p6'], M['p7'] - 1), txt='Otra.', estilo='Grande', y=300, pop=True, extra='\\fs124'),
    dict(n=(M['p7'], M['p8'] - 1), txt='Otra.', estilo='Grande', y=300, pop=True, extra='\\fs124'),
    dict(n=(M['p8'], M['p9'] - 1), txt='Otra.', estilo='Grande', y=300, pop=True, extra='\\fs124'),
    # salto de línea por ancho (27 caracteres no entran en 1080 a \fs104): el texto es el del guion
    dict(n=(M['p10'], M['p11'] - 1), txt='¿A quién le dicen\\Nagrandado?', estilo='CajaN', y=270, pop=True,
         extra='\\fs104\\xbord29\\ybord9'),
]
PLACA_CUADROS = dict(resolucion=(M['placa'], M['p10'] - 1), cta_frase=(M['p11'], NF - 1), cta_firma=(M['p11'] + 6, NF - 1))
FADE_PLACA = 0.2


def textos_ass():
    ev = [dict(t0=tt(d['n'][0]), t1=tt(d['n'][1] + 1), txt=d['txt'], estilo=d['estilo'], y=d['y'], pop=d.get('pop', False),
               extra=d.get('extra')) for d in TEXTOS5]
    return V.ass(ev, T / 'v5_textos.ass')


# =====================================================================================================
# etapa master · base (color) → textos ASS → etiquetas (secuencia RGBA) → placas (PNG con fundido de alfa) → H.264/AAC
# Las capas RGB entran convertidas a YUV con matriz BT.709 explícita y se componen en 4:4:4.
# =====================================================================================================
def master5(video, audio_wav, salida, ass_path):
    C = T / 'placa'
    inputs = ['-i', str(video), '-i', str(audio_wav), '-framerate', str(FPS), '-start_number', '0', '-i', str(ETQ / 'e_%04d.png')]
    capas = [('resolucion_frase', *PLACA_CUADROS['resolucion']), ('cta_frase', *PLACA_CUADROS['cta_frase']),
             ('cta_firma', *PLACA_CUADROS['cta_firma'])]
    for nombre, n0, n1 in capas:
        inputs += ['-framerate', str(FPS), '-loop', '1', '-t', f'{DUR:.4f}', '-i', str(C / f'{nombre}.png')]
    a709 = 'scale=out_color_matrix=bt709:out_range=tv,format=yuva444p'
    fc = ['[0:v]setsar=1,format=yuv420p', f'subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter', 'format=yuv444p[v0]']
    fc = [','.join(fc)]
    fc.append(f'[2:v]format=rgba,{a709}[e]')
    fc.append('[v0][e]overlay=0:0:eof_action=pass:format=yuv444[v1]')
    lab = 'v1'
    for i, (nombre, n0, n1) in enumerate(capas):
        t0 = (n0 - 0.5) / FPS; t1 = (n1 + 0.5) / FPS
        fc.append(f"[{i + 3}:v]format=rgba,fade=t=in:st={n0 / FPS:.4f}:d={FADE_PLACA}:alpha=1,{a709}[p{i}]")
        fc.append(f"[{lab}][p{i}]overlay=0:0:format=yuv444:enable='between(t,{t0:.5f},{t1:.5f})'[w{i}]")
        lab = f'w{i}'
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


def sinmusica_por_copia():
    """versión sin música = el MISMO flujo de video de la completa (copia, sin recodificar) + la mezcla sin música.
    Dos codificaciones x264 por separado daban flujos distintos en c197–c277 (decisiones del codificador, misma
    calidad contra la base): con la copia, el ID de video es uno solo para las dos versiones."""
    f0, f1 = MAS / NOMBRES['completa'], MAS / NOMBRES['sinmusica']
    if f1.exists():
        f1.unlink()                          # intermedio de trabajo (nunca entregado): se rehace
    V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(f0), '-i', str(A / 'v5_sinmusica.wav'), '-map', '0:v:0', '-map', '1:a:0',
          '-c:v', 'copy', '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
          '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
          '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
          '-t', f'{DUR:.6f}', '-movflags', '+faststart', str(f1)])
    print('->', f1, flush=True)


def etapa_sinmusica():
    sinmusica_por_copia()


def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    a = textos_ass()
    f0 = MAS / NOMBRES['completa']
    if f0.exists():
        f0.unlink()                          # intermedio de trabajo (nunca entregado): se rehace
    master5(TV / 'v5_base.mp4', A / 'v5_completa.wav', f0, a)
    print('->', f0, flush=True)
    sinmusica_por_copia()



# =====================================================================================================
# etapa control · evidencia (evidencia_v01/)
# =====================================================================================================
TRAMOS = [('1 apuesta 7887', 0.0, ts(M['p2'])), ('2 etiqueta 2', ts(M['p2']), ts(M['e3'])),
          ('3 etiqueta 3', ts(M['e3']), ts(M['p4'])), ('4 etiqueta 4 + salida', ts(M['p4']), HUECO[0]),
          ('hueco', HUECO[0], HUECO[1]), ('5 giro 7885', ts(M['p5']), ts(M['p6'])),
          ('6–8 cadena «Otra.»', ts(M['p6']), ts(M['p9'])), ('9 resolución 7885', ts(M['p9']), ts(M['p10'])),
          ('10 reenganche 4530', ts(M['p10']), ts(M['p11'])), ('11 CTA 4530', ts(M['p11']), DUR)]
CRITICOS = sorted({0, 3, 4, 5, 6, 8, 36, 46, 60, 75, 101, 102, 104, 106, 107, 108, 109, 110, 125, 126, 140, 141, 153, 154,
                   165, 166, 176, 182, 247, 248, 249, 277, 278, 290, 334})
PLANOS_CADENA = [('p5 giro', 'IMG_7885', M['p5'], M['p6']), ('p6 «Otra.» 1', 'IMG_8008', M['p6'], M['p7']),
                 ('p7 «Otra.» 2', 'IMG_8002', M['p7'], M['p8']), ('p8 «Otra.» 3', 'IMG_8004', M['p8'], M['p9']),
                 ('p9 resolución', 'IMG_7885', M['p9'], M['p10'])]


def _caja_en_master(pl_reg, k_local, caja_1080):
    """caja de ROCCÉ medida en la toma completa (1080×1920) llevada al cuadro del máster con la ventana del plano."""
    if caja_1080 is None:
        return None
    vs = pl_reg.get('ventanas')
    if not vs:
        return caja_1080
    Z, x, y, w, h = vs[k_local]
    f = W / w
    x0, y0, x1, y1 = caja_1080
    return (int((2 * x0 - x) * f), int((2 * y0 - y) * f), int((2 * x1 - x) * f), int((2 * y1 - y) * f))


def rocce_en_master(mp4):
    """ROCCÉ en cada cuadro de los planos p5–p9 del archivo dado: roi = caja medida en la toma (rocce_4k.json) llevada
    al máster con la ventana del plano y agrandada; devuelve caja, ancho, largo (eje de la palabra) y varianza del
    laplaciano de la luma sobre la caja + 8 %."""
    reg = {r['id']: r for r in json.load(open(TV / 'planos.json'))['planos']}
    d4k = {t: {f['cuadro']: f['caja'] for f in v} for t, v in json.load(open(ROCCE_4K)).items()}
    ids = {'p5 giro': 'p5', 'p6 «Otra.» 1': 'p6', 'p7 «Otra.» 2': 'p7', 'p8 «Otra.» 3': 'p8', 'p9 resolución': 'p9'}
    out = {}
    for nombre, toma, a, b in PLANOS_CADENA:
        r = reg[ids[nombre]]; fr = U.leer(mp4, W, H, n0=a, n1=b - 1)
        filas = []
        for k, img in enumerate(fr):
            c = _caja_en_master(r, k, d4k[toma].get(r['n0'] + k))
            if c is None:
                filas.append(dict(cuadro=a + k, caja=None)); continue
            # margen chico: la caja viene de la misma imagen con una transformación conocida. Con 0,25/0,9 la roi de p6
            # (palabra en diagonal, caja alta) tomaba un sexto componente de la arena (largo 1288–1370 en c128–c140)
            x0, y0, x1, y1 = c; mw_, mh_ = 0.12 * (x1 - x0), 0.25 * (y1 - y0)
            bb, nl, lg = rocce_roi(img, (x0 - mw_, y0 - mh_, x1 + mw_, y1 + mh_), con_largo=True)
            if bb is None:
                filas.append(dict(cuadro=a + k, caja=None)); continue
            px = int(0.08 * (bb[2] - bb[0])); py = int(0.08 * (bb[3] - bb[1])) + 4
            b8 = (max(0, bb[0] - px), max(0, bb[1] - py), min(W - 1, bb[2] + px), min(H - 1, bb[3] + py))
            filas.append(dict(cuadro=a + k, caja=list(bb), ancho=bb[2] - bb[0] + 1, largo=round(lg, 1), letras=nl,
                              margen_izq=bb[0], margen_der=W - 1 - bb[2], lapvar=round(lapvar(img.astype(np.float32) @ KY, b8), 1)))
        out[nombre] = filas
    return out


def nitidez_clips():
    """los tramos del guion con clips 576×1024 en su encuadre (completo, Lanczos a 1080×1920), con ROCCÉ seguido."""
    semillas = {'paso5_clip_a2c1cbe8_0.90-1.50': ('clip_a2c1cbe8', 27, 44, 44, (60, 1060, 680, 1260)),
                'paso7_clip_a592f367_0.20-0.65': ('clip_a592f367', 6, 19, 15, (380, 780, 920, 1010)),
                'paso8_clip_a2c1cbe8_2.10-2.50': ('clip_a2c1cbe8', 63, 74, 66, (240, 830, 910, 1040)),
                'paso9_clip_a592f367_1.30-4.00': ('clip_a592f367', 39, 119, 45, (100, 720, 830, 1040))}
    out = {}
    for k, (toma, a, b, ks, roi) in semillas.items():
        fr = U.leer(V._src(toma), W, H, n0=a, n1=b, vf_pre=V.color(toma) + ',' + V.encuadre(toma, None))
        r = seguir_rocce(fr, ks - a, roi)
        filas = []
        for i, (bb, nl, lg) in enumerate(r):
            if bb is None:
                filas.append(dict(cuadro=a + i, caja=None)); continue
            px = int(0.08 * (bb[2] - bb[0])); py = int(0.08 * (bb[3] - bb[1])) + 4
            b8 = (max(0, bb[0] - px), max(0, bb[1] - py), min(W - 1, bb[2] + px), min(H - 1, bb[3] + py))
            filas.append(dict(cuadro=a + i, caja=list(bb), ancho=bb[2] - bb[0] + 1, largo=round(lg, 1),
                              lapvar=round(lapvar(fr[i].astype(np.float32) @ KY, b8), 1)))
        out[k] = filas
    return out


def contraste_placa(mp4_base, nombre, cuadros):
    """fracción del trazo de la frase (píxeles casi blancos y opacos del PNG) con contraste ≥ 3:1 y ≥ 4,5:1 (WCAG)
    contra el fondo real del cuadro con el degradé (base + PNG solo_degrade, desenfocado 4 px)."""
    from PIL import Image, ImageFilter
    C = T / 'placa'
    fr_png = np.asarray(Image.open(C / f'{nombre}_frase.png')).astype(np.float32) / 255
    dg = np.asarray(Image.open(C / f'{nombre}_solo_degrade.png')).astype(np.float32) / 255
    trazo = (fr_png[..., 3] > 0.8) & (fr_png[..., :3].min(-1) > 0.8)
    trazo_f = None
    if nombre == 'cta':                     # letras de la firma «ROCCÉ LIFE» (a la derecha de la ficha del logo)
        fi = np.asarray(Image.open(C / 'cta_firma.png')).astype(np.float32) / 255
        trazo_f = (fi[..., 3] > 0.6) & (fi[..., :3].min(-1) > 0.8)
        trazo_f[:, :FIRMA_X_LETRAS] = False
    lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    res = []
    for n in cuadros:
        bg = U.leer(mp4_base, W, H, n0=n, n1=n)[0].astype(np.float32) / 255
        comp = bg * (1 - dg[..., 3:4]) + dg[..., :3] * dg[..., 3:4]
        comp = np.asarray(Image.fromarray((comp * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255
        Lb = (lin(comp) @ np.array([0.2126, 0.7152, 0.0722], np.float32))[trazo]
        cr = 1.05 / (Lb + 0.05)
        fila = dict(cuadro=n, frac_3a1=round(float((cr >= 3).mean()), 4), frac_4_5a1=round(float((cr >= 4.5).mean()), 4),
                    contraste_mediano=round(float(np.median(cr)), 2))
        if trazo_f is not None:
            cf = 1.05 / ((lin(comp) @ np.array([0.2126, 0.7152, 0.0722], np.float32))[trazo_f] + 0.05)
            fila.update(firma_frac_3a1=round(float((cf >= 3).mean()), 4), firma_frac_4_5a1=round(float((cf >= 4.5).mean()), 4),
                        firma_contraste_mediano=round(float(np.median(cf)), 2))
        res.append(fila)
    return res


FIRMA_X_LETRAS = 460   # x desde donde empiezan las letras de la firma (ficha del logo: x 351–447)


def gancho_vs_etiquetas(mp4):
    """letras blancas de «Querés más.» (c0 del máster, dentro de su caja) tapadas por el alfa > 128 de la capa de
    etiquetas en cada cuadro c0–c107."""
    from PIL import Image
    from scipy import ndimage as ndi
    f = U.leer(mp4, W, H, n0=0, n1=0)[0].astype(int)
    m = f.max(-1) < 45; m[600:] = False
    lab, k = ndi.label(m); i = int(np.argmax(ndi.sum(m, lab, range(1, k + 1)))) + 1
    ys, xs = np.nonzero(lab == i); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    g = np.zeros((H, W), bool); g[y0:y1 + 1, x0:x1 + 1] = f[y0:y1 + 1, x0:x1 + 1].min(-1) > 200
    filas = []
    for n in range(M['p5']):
        a = np.asarray(Image.open(ETQ / f'e_{n:04d}.png'))[..., 3]
        c = int(((a > 128) & g).sum())
        filas.append(dict(cuadro=n, letras_tapadas_px=c, pct=round(100 * c / g.sum(), 1)))
    return dict(caja_gancho=[int(x0), int(y0), int(x1), int(y1)], letras_px=int(g.sum()),
                cuadros_con_letras_tapadas=[r for r in filas if r['letras_tapadas_px'] > 0])


def texto_vs_estampado(rm):
    """pasos 9 y 11: la placa (letras y firma, PNG) contra ROCCÉ medido en cada cuadro de p9 (c176–c245; c246–c247 son
    el barrido) y contra el borde superior de la Blanca en 4530 (primera fila con remera blanca en la columna central)."""
    pj = json.load(open(T / 'placa' / 'placa.json'))
    res_b = pj['resolucion_letras'][3]
    p9 = [f for f in rm['p9 resolución'] if f.get('caja') and M['placa'] <= f['cuadro'] <= M['p10'] - 3]
    y_rocce = min(f['caja'][1] for f in p9)
    fr = U.leer(MAS / NOMBRES['completa'], W, H, n0=M['p11'], n1=NF - 1)
    tope = []
    for img in fr:
        col = img[:, 380:700].astype(int)
        blanco = (col.min(-1) > 205) & (np.abs(col[..., 2] - col[..., 0]) < 14)
        filas = np.nonzero(blanco.mean(1) > 0.9)[0]
        filas = filas[filas > 640]
        tope.append(int(filas.min()) if len(filas) else None)
    return dict(resolucion_letras_y_max=res_b, p9_rocce_y_min=y_rocce, hueco_p9_px=y_rocce - res_b,
                cta_firma_y_max=pj['firma'][3], blanca_4530_tope_min=min(t for t in tope if t),
                hueco_cta_px=min(t for t in tope if t) - pj['firma'][3])


def psnr_vs_v01():
    """PSNR por cuadro (promedio Y/U/V, filtro psnr de FFmpeg) del máster de esta versión contra el v01 entregado, dentro y
    fuera de la cadena c126–c165; los cuadros idénticos dan inf."""
    st = EVID / 'psnr_vs_v01_por_cuadro.log'
    subprocess.run(nice(['ffmpeg', '-v', 'error', '-i', str(MAS / NOMBRES['completa']), '-i', str(V01['completa']),
                         '-lavfi', f'[0:v][1:v]psnr=stats_file={st}', '-f', 'null', '-']), check=True)
    filas = []
    for ln in st.read_text().splitlines():
        d = dict(kv.split(':', 1) for kv in ln.split() if ':' in kv)
        filas.append((int(d['n']) - 1, float(d['psnr_avg']), float(d['psnr_y'])))
    fuera = [f for f in filas if not (M['p6'] <= f[0] < M['p9'])]
    dentro = [f for f in filas if M['p6'] <= f[0] < M['p9']]
    fin = [f[1] for f in fuera if math.isfinite(f[1])]
    return dict(cuadros=len(filas), fuera=dict(cuadros=len(fuera), identicos=sum(1 for f in fuera if not math.isfinite(f[1])),
                                               psnr_min_db=round(min(fin), 2) if fin else None,
                                               cuadro_min=min((f for f in fuera if math.isfinite(f[1])), key=lambda f: f[1])[0] if fin else None,
                                               psnr_mediana_db=round(float(np.median(fin)), 2) if fin else None),
                dentro=dict(cuadros=len(dentro), psnr_min_db=round(min(f[1] for f in dentro), 2),
                            psnr_mediana_db=round(float(np.median([f[1] for f in dentro])), 2)),
                archivo_v01=str(V01['completa']), stats=st.name)


def cadena_resumen(rm):
    """largo de ROCCÉ por cuadro c126–c165, salto en cada corte (último cuadro del plano anterior → primero del nuevo),
    margen mínimo y ancho de fuente mínimo (ventana en px naturales de la toma 4K de 2160 × 3840)."""
    reg = {r['id']: r for r in json.load(open(TV / 'planos.json'))['planos']}
    por = {}
    for nombre in ('p5 giro', 'p6 «Otra.» 1', 'p7 «Otra.» 2', 'p8 «Otra.» 3'):
        for f in rm[nombre]:
            por[f['cuadro']] = f
    vent = {}
    for pid in ('p6', 'p7', 'p8'):
        r = reg[pid]
        for k in range(r['cuadros']):
            vent[r['m0'] + k] = r['ventanas'][k][3] if r.get('ventanas') else float(V.TOMAS[r['toma']]['nat'][0])
    filas = [dict(cuadro=n, largo=por[n].get('largo'), ancho=por[n].get('ancho'), margen_izq=por[n].get('margen_izq'),
                  margen_der=por[n].get('margen_der'), ancho_fuente_px=round(vent[n], 1)) for n in range(M['p6'], M['p9'])]
    cortes = []
    for c in (M['p6'], M['p7'], M['p8']):
        a_, b_ = por[c - 1], por[c]
        cortes.append(dict(corte=c, antes=a_['largo'], despues=b_['largo'], sube_pct=round(100 * (b_['largo'] / a_['largo'] - 1), 1)))
    return dict(cortes=cortes, criterio_pct=12.0, cumple_cortes=all(c['sube_pct'] >= 12 for c in cortes),
                margen_min_px=min(min(f['margen_izq'], f['margen_der']) for f in filas),
                ancho_fuente_min_px=min(f['ancho_fuente_px'] for f in filas), por_cuadro=filas,
                ventanas={pid: reg[pid].get('ventanas') for pid in ('p6', 'p7', 'p8')},
                fuentes={pid: dict(toma=reg[pid]['toma'], n0=reg[pid]['n0'], cuadros=reg[pid]['cuadros']) for pid in ('p6', 'p7', 'p8')})


def etapa_control():
    from PIL import Image, ImageDraw
    EVID.mkdir(parents=True, exist_ok=True)
    a = T / 'v5_textos.ass'
    tiempos = [tt(d['n'][0]) + 0.1 for d in TEXTOS5]

    def extra():
        e = {}
        f0 = MAS / NOMBRES['completa']
        e['atomos'] = {k: L2.atomos(MAS / n) for k, n in NOMBRES.items()}
        e['silencio_final_s'] = {k: L2.silencio_final(U.audio_np(MAS / n)) for k, n in NOMBRES.items()}
        e['etiquetas'] = {k: v for k, v in json.load(open(MED / 'etiquetas.json')).items() if k != 'por_cuadro'}
        e['rocce_en_master'] = rocce_en_master(f0)
        e['nitidez_clips_guion'] = nitidez_clips()
        e['contraste_resolucion'] = contraste_placa(TV / 'v5_base.mp4', 'resolucion', list(range(M['placa'], M['p10'], 6)))
        e['contraste_cta'] = contraste_placa(TV / 'v5_base.mp4', 'cta', list(range(M['p11'], NF, 6)))
        e['gancho_vs_etiquetas'] = gancho_vs_etiquetas(f0)
        e['cadena'] = cadena_resumen(e['rocce_en_master'])
        if VER != 'v01':
            e['psnr_vs_v01'] = psnr_vs_v01()
        e['texto_vs_estampado'] = texto_vs_estampado(e['rocce_en_master'])
        e['placa'] = json.load(open(T / 'placa' / 'placa.json'))
        col = json.load(open(MEDV / 'color.json'))
        e['blanca_por_plano'] = {}
        for pl, ((x, y), _, _, _) in COLOR5.items():
            an = [col['por_cuadro'][str(n)]['tela_antes']['b_menos_r'] for n in range(x, y + 1) if col['por_cuadro'][str(n)]['tela_antes']]
            de = [col['por_cuadro'][str(n)]['tela_despues']['b_menos_r'] for n in range(x, y + 1) if col['por_cuadro'][str(n)]['tela_despues']]
            e['blanca_por_plano'][pl] = dict(b_menos_r_antes_mediana=float(np.median(an)) if an else None,
                                             b_menos_r_despues_mediana=float(np.median(de)) if de else None,
                                             despues_rango=[min(de), max(de)] if de else None, cuadros_medidos=len(de))
        return e
    rep = U.control(NOMBRES, EVID, CORTES, NF - 1, TRAMOS, a, TEXTOS5, tiempos, extra=extra, carpeta=MAS)
    rep['fecha'] = '2026-11-25'; rep['version'] = VER
    jdump(rep, EVID / 'control.json')
    f0 = MAS / NOMBRES['completa']
    L2.hoja_cuadros(f0, CRITICOS, EVID / 'cuadros_criticos.jpg', ancho=240, cols=9)
    crit = EVID / 'criticos'; crit.mkdir(exist_ok=True)
    fr = U.leer(f0, W, H)
    for n in CRITICOS:
        Image.fromarray(fr[n]).save(crit / f'c{n:03d}.jpg', quality=92)
    # prueba de y 940: c0–c107 del máster cada 3 cuadros con la línea y 940 dibujada
    tiles = []
    for n in range(0, M['p5'], 3):
        im = Image.fromarray(fr[n]).resize((216, 384)); d = ImageDraw.Draw(im)
        d.line([(0, 940 * 0.2), (216, 940 * 0.2)], fill=(255, 0, 0), width=1); d.text((3, 3), f'c{n}', fill=(255, 255, 0))
        tiles.append(im)
    cols = 12; filas = math.ceil(len(tiles) / cols)
    hoja = Image.new('RGB', (cols * 218, filas * 386), (30, 30, 30))
    for i, t_ in enumerate(tiles):
        hoja.paste(t_, ((i % cols) * 218, (i // cols) * 386))
    hoja.save(EVID / 'prueba_y940_c0-c107_cada3.jpg', quality=90)
    # «Otra.»: el cuadro de cada corte con la caja de ROCCÉ medida
    rm = rep['rocce_en_master']
    from PIL import ImageFont
    FNT = ImageFont.truetype(str(FUENTES / 'Montserrat-Bold.ttf'), 120)
    FNT2 = ImageFont.truetype(str(FUENTES / 'Montserrat-Bold.ttf'), 72)
    tiles = []
    for nombre, toma, a_, b_ in PLANOS_CADENA[:4]:
        for f in (rm[nombre][0], rm[nombre][-1]):
            im = Image.fromarray(fr[f['cuadro']]); d = ImageDraw.Draw(im)
            if f.get('caja'):
                d.rectangle(f['caja'], outline=(255, 0, 255), width=6)
                d.rectangle((0, 1560, 1080, 1920), fill=(0, 0, 0))
                d.text((30, 1590), f"c{f['cuadro']}", fill=(255, 255, 0), font=FNT)
                d.text((30, 1740), f"ancho {f['ancho']} · largo {f['largo']:.0f}", fill=(255, 255, 0), font=FNT2)
            tiles.append(im.resize((270, 480)))
    hoja = Image.new('RGB', (len(tiles) * 272, 480), (30, 30, 30))
    for i, t_ in enumerate(tiles):
        hoja.paste(t_, (i * 272, 0))
    hoja.save(EVID / 'otra_ancho_rocce.jpg', quality=92)
    for k in ('etiquetas.json', 'rocce_4k.json', 'textos_vs_guion.json'):
        if (MED / k).exists():
            shutil.copy2(MED / k, EVID / k)
    if (MED / 'medidas.json').exists():
        shutil.copy2(MED / 'medidas.json', EVID / 'medidas_tomas.json')
    for k in ('color.json', 'golpes_completa.json', 'golpes_sinmusica.json'):
        if (MEDV / k).exists():
            shutil.copy2(MEDV / k, EVID / k)
    shutil.copy2(A / 'audio.json', EVID / 'audio.json'); shutil.copy2(TV / 'planos.json', EVID / 'planos.json')
    shutil.copy2(T / 'placa' / 'placa.json', EVID / 'placa.json')
    print(json.dumps({k: rep['archivos'][k]['md5_video'] + ' / ' + rep['archivos'][k]['md5_audio'] for k in NOMBRES}), flush=True)


def etapa_entregar():
    r = U.entregar(NOMBRES, MAS, EVID, PIEZA)
    jdump(r, TV / 'entrega.json')


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    globals()['etapa_' + etapa]()
