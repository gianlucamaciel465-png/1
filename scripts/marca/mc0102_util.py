#!/usr/bin/env python3
"""MARCA · comunidad · MC-01 y MC-02 (Pedro A, 25/11/2026) · utilidades que usan las dos recetas (mc01.py, mc02.py).

No modifica scripts/fmt/video.py, fmt03.py, sonido.py ni scripts/marca/comun.py: los importa y usa tal cual.
Lo que hace falta y no está ahí vive acá:
  - envoltura de V.sh con nice y 2 hilos (la máquina la comparten tres Pedros en paralelo);
  - plano_lento: cámara lenta con MEZCLA DE CUADROS (condición 2 de Roma: sin tartamudeo, sin cuadros repetidos);
  - neutralizar_blanca: Blanca a B−R ≈ +8 solo en neutros claros de la Blanca (criterio de scripts/life/life_v2.py
    «corregir», ganancias por franja de luminancia; el resto del cuadro queda idéntico);
  - Capa de interfaz por cuadro con los estilos de comun.py (caja, placa, pegar, pop 118 → 109 → 100 %), escrita como
    secuencia PNG RGBA de 1080×1920 (cuadros repetidos = enlaces duros) y superpuesta con UN overlay exacto por cuadro;
  - master_ui: mismos parámetros de codificación que video.master (H.264 High 4.0, yuv420p, BT.709, AAC-LC 48 kHz,
    faststart, sin metadatos); sin_musica: mismo flujo de video copiado sin recodificar + otra mezcla;
  - detector de estampado (ROCCÉ, «Founders Privée», «so f★cking close.») para controlar que ningún texto lo toque;
  - control y entrega (ffprobe, decodificación, md5 de flujos, sonoridad, cuadros, hojas, vista a 360 px).
"""
import hashlib, json, math, os, shlex, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/marca')
import video as V      # noqa: E402
import fmt03 as U      # noqa: E402
import comun as C      # noqa: E402

R = Path('/home/user/1')
EXP = R / 'EXPORTACIONES'
FPS, W, H, SR = 30, 1080, 1920, 48000
FONT = U.FONT
FUENTES = R / 'scripts' / 'fuentes'
KY = np.array([0.2126, 0.7152, 0.0722], np.float32)

# Instrument Serif para el estilo «Serif» del guion (comun.F no la trae): se agrega en memoria, comun.py no se toca.
C.F.setdefault('serif', FUENTES / 'InstrumentSerif-Regular.ttf')

# ---------------------------------------------------------------------------------------------------------------
# ffmpeg con nice y 2 hilos (V.sh se envuelve en este proceso; video.py no se modifica)
# ---------------------------------------------------------------------------------------------------------------
_SH0 = V.sh


def _sh_hilos(cmd, **kw):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    cmd = list(cmd)
    if cmd and cmd[0] == 'ffmpeg':
        cmd = ['nice', '-n', '10', 'ffmpeg', '-threads', '2', '-filter_threads', '2'] + cmd[1:-1] + ['-threads', '2', cmd[-1]]
    return _SH0(cmd, **kw)


V.sh = _sh_hilos


def run(cmd, **kw):
    r = subprocess.run(list(map(str, cmd)), capture_output=True, **kw)
    if r.returncode:
        raise RuntimeError(' '.join(map(str, cmd)) + '\n' + r.stderr.decode(errors='replace')[-3000:])
    return r.stdout


def jdump(obj, f):
    Path(f).parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(f, 'w'), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))


# ---------------------------------------------------------------------------------------------------------------
# planos
# ---------------------------------------------------------------------------------------------------------------
def plano(toma, n0, nf, salida, post=None):
    """cuadro completo (ventana 9:16 más grande), definido por cuadro de fuente n0 y cantidad nf (fmt03.plano_n)."""
    return U.plano_n(toma, n0, nf, salida, caja=None, post=post)


def plano_z(toma, n0, zs, cx, cy, salida, post=None):
    """acercamiento real por cuadro (fmt03.plano_z): zs lista por cuadro; cx, cy en coordenadas naturales."""
    nw, nh = V.TOMAS[toma]['nat']
    nf = len(zs)
    return U.plano_z(toma, n0, list(zs), [cx] * nf if not isinstance(cx, (list, tuple)) else list(cx),
                     [cy] * nf if not isinstance(cy, (list, tuple)) else list(cy), salida, caja=(0, 0, nw, nh), post=post)


def _decode_1080(toma, n0, n, extra_vf=''):
    """n cuadros 1080×1920 yuv444p (3, H, W) uint8 desde el cuadro de fuente n0, con la cadena de color de video.py."""
    d = U.desde_cuadro(toma, n0)
    vf = V.color(toma) + ',' + V.encuadre(toma) + f',fps={FPS}' + (',' + extra_vf if extra_vf else '') + ',format=yuv444p'
    raw = run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', '2', '-ss', f'{d:.4f}', '-i', V._src(toma),
               '-t', f'{n / FPS + 0.3:.4f}', '-an', '-vf', vf, '-frames:v', str(n), '-f', 'rawvideo', '-pix_fmt', 'yuv444p', '-'])
    a = np.frombuffer(raw, np.uint8).reshape(-1, 3, H, W)
    if len(a) != n:
        raise RuntimeError(f'_decode_1080 {toma}: {len(a)} de {n}')
    return a


def _encoder(salida, post=None):
    return subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv444p',
                             '-s', f'{W}x{H}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709',
                             '-color_primaries', 'bt709', '-color_trc', 'bt709', '-i', '-', *(['-vf', post] if post else []),
                             '-threads', '2', *V.ENC_INT, str(salida)], stdin=subprocess.PIPE)


def plano_lento(toma, n0, n_src, nf, salida, post=None):
    """Cámara lenta con mezcla de cuadros: el cuadro k del plano es la mezcla lineal (en Y'CbCr de 8 bits, como
    minterpolate=mi_mode=blend) de los cuadros de fuente vecinos a p = k·(n_src−1)/(nf−1). El primero y el último son
    cuadros reales exactos (n0 y n0+n_src−1). Ningún cuadro se repite: no hay tartamudeo."""
    src = _decode_1080(toma, n0, n_src).astype(np.float32)
    enc = _encoder(salida, post)
    pos = []
    for k in range(nf):
        p = k * (n_src - 1) / (nf - 1)
        i = min(int(math.floor(p)), n_src - 2); f = p - i
        o = src[i] * (1 - f) + src[i + 1] * f
        enc.stdin.write(np.clip(np.round(o), 0, 255).astype(np.uint8).tobytes())
        pos.append(round(p, 4))
    enc.stdin.close(); enc.wait()
    if enc.returncode:
        raise RuntimeError('plano_lento: codificación')
    return dict(toma=toma, n0=n0, n_src=n_src, cuadros=nf, salida=str(salida), vel=round((n_src - 1) / (nf - 1), 4),
                posiciones_fuente=pos, post=post)


def _mci(src, i0, i1, m):
    """cuadros intermedios por interpolación con compensación de movimiento (FFmpeg minterpolate, mi_mode=mci):
    devuelve m+1 cuadros yuv444p en las posiciones i0 + (i1 − i0)·k/m (k = 0..m) de src. Se le pasan 2 cuadros de más
    para que minterpolate no pierda los últimos al cerrar."""
    j1 = min(len(src), i1 + 3)
    # base de tiempo exacta: con la de 1/30, PTS·m/(i1−i0) se redondea a enteros y los cuadros caen corridos
    vf = (f'settb=1/{FPS * (i1 - i0) * m},setpts=N*{m * m},'
          f'minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1')
    raw = run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'yuv444p', '-s', f'{W}x{H}',
               '-r', str(FPS), '-i', '-', '-vf', vf, '-frames:v', str(m + 1), '-f', 'rawvideo', '-pix_fmt', 'yuv444p', '-'],
              input=np.ascontiguousarray(src[i0:j1]).tobytes())
    out = np.frombuffer(raw, np.uint8).reshape(-1, 3, H, W)
    if len(out) != m + 1:
        raise RuntimeError(f'_mci: {len(out)} de {m + 1}')
    return out


def plano_pos(toma, n0, n_src, posiciones, salida, post=None, tramo_mci=None):
    """Plano con rampa de velocidad: el cuadro k es la fuente en la posición posiciones[k] (relativa a n0, 0..n_src−1);
    posición entera = cuadro real exacto. Fraccionaria: mezcla lineal de los dos vecinos (como plano_lento) o, con
    tramo_mci=(i0, i1, m), el cuadro interpolado con compensación de movimiento en i0 + (i1 − i0)·k/m (sin fantasmas
    cuando la cámara se mueve)."""
    src = _decode_1080(toma, n0, n_src)
    mci = None
    if tramo_mci:
        i0, i1, m = tramo_mci
        mci = _mci(src, i0, i1, m)
    srcf = src.astype(np.float32)
    enc = _encoder(salida, post)
    origen = []
    for p in posiciones:
        i = min(int(math.floor(p)), n_src - 2); f = p - i
        if f < 1e-6 or f > 1 - 1e-6:
            o = src[i] if f < 1e-6 else src[i + 1]; origen.append('real')
        elif mci is not None:
            k = (p - i0) * m / (i1 - i0)
            assert abs(k - round(k)) < 1e-6 and 0 <= round(k) <= m, (p, k)
            o = mci[int(round(k))]; origen.append('mci')
        else:
            o = np.clip(np.round(srcf[i] * (1 - f) + srcf[i + 1] * f), 0, 255).astype(np.uint8); origen.append('mezcla')
        enc.stdin.write(np.ascontiguousarray(o).tobytes())
    enc.stdin.close(); enc.wait()
    if enc.returncode:
        raise RuntimeError('plano_pos: codificación')
    return dict(toma=toma, n0=n0, n_src=n_src, cuadros=len(posiciones), salida=str(salida),
                posiciones_fuente=[round(n0 + p, 4) for p in posiciones], origen=origen, tramo_mci=tramo_mci, post=post)


def unir(planos, salida):
    return V.unir(planos, salida)


def contar(mp4):
    return int(run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                    'stream=nb_read_frames', '-of', 'csv=p=0', mp4]).decode().strip())


def leer_rgb(mp4, n0, n1, w=W, h=H):
    return U.leer(mp4, w, h, n0=n0, n1=n1)


# ---------------------------------------------------------------------------------------------------------------
# color · Blanca (criterio de life_v2.corregir / pines.neutralizar, aprobado)
# ---------------------------------------------------------------------------------------------------------------
FRANJAS = [(150, 190), (190, 215), (215, 256)]
OBJ_BR = (-1.65, -0.15, 6.35)     # blanco objetivo: B−R = +8, G−R = +1,5 con la misma luminancia (como video.TOMAS)


def yuv_rgb(Y, Cb, Cr):
    """Y'CbCr BT.709 rango limitado (planos de igual tamaño) -> RGB 0..255 float32."""
    y = (Y.astype(np.float32) - 16) / 219; u = (Cb.astype(np.float32) - 128) / 224; v = (Cr.astype(np.float32) - 128) / 224
    r = y + 1.5748 * v; b = y + 1.8556 * u; g = (y - 0.2126 * r - 0.0722 * b) / 0.7152
    return np.stack([r, g, b], -1) * 255.0


def rgb_yuv(rgb):
    r, g, b = rgb[..., 0] / 255, rgb[..., 1] / 255, rgb[..., 2] / 255
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return 16 + 219 * y, 128 + 224 * (b - y) / 1.8556, 128 + 224 * (r - y) / 1.5748


def lum_sat(rgb):
    c = np.clip(rgb, 0, 255)
    L = c @ KY
    mx = c.max(-1); mn = c.min(-1)
    return L, (mx - mn) / (mx + 1)


def mascara_blanca(rgb, caja, area_min=2000, solidez=0.40, union=False):
    """mayor componente de tela clara y neutra (L > 150, sat < 0,15) dentro de la caja, con ≥ area_min px y solidez
    (área / recuadro) ≥ 0,40 (deja afuera la espuma suelta). union=True suma los demás componentes de la caja con
    ≥ 10 % del área del mayor y solidez ≥ 0,25: cuando un pliegue o una sombra parte la remera en dos, la mitad que
    queda afuera no se pierde (8008, cuadros 16–21 del plano 3 de MC-01)."""
    from scipy import ndimage as nd
    L, sat = lum_sat(rgb)
    x0, y0, x1, y1 = caja
    m = np.zeros(L.shape, bool); m[y0:y1, x0:x1] = True
    lab, n = nd.label(m & (L > 150) & (sat < 0.15))
    if n == 0:
        return np.zeros(L.shape, bool), L, sat
    tam = nd.sum(np.ones(L.shape), lab, range(1, n + 1))
    objs = nd.find_objects(lab)
    sol = [tam[i] / ((sl[0].stop - sl[0].start) * (sl[1].stop - sl[1].start)) for i, sl in enumerate(objs)]
    best, ar = None, 0
    for i in range(n):
        if tam[i] >= area_min and sol[i] >= solidez and tam[i] > ar:
            best, ar = i + 1, tam[i]
    if not best:
        return np.zeros(L.shape, bool), L, sat
    if not union:
        return lab == best, L, sat
    ids = [i + 1 for i in range(n) if i + 1 == best or (tam[i] >= max(area_min, 0.10 * ar) and sol[i] >= 0.25)]
    return np.isin(lab, ids), L, sat


def ganancias_blanca(rgbs, caja):
    """ganancias R/G/B por franja de L que llevan la mediana de la tela de la Blanca al blanco objetivo (B−R +8)."""
    acc = {k: [] for k in range(len(FRANJAS))}
    for rgb in rgbs:
        bl, L, sat = mascara_blanca(rgb, caja)
        for k, (lo, hi) in enumerate(FRANJAS):
            m = bl & (L >= lo) & (L < hi) & (sat < 0.12)
            acc[k].append(np.concatenate([rgb[m], L[m][:, None]], 1))
    cent, gan, med = [], [], []
    for k, v in acc.items():
        p = np.concatenate(v, 0)
        if len(p) < 3000:
            continue
        md = np.median(p[:, :3], 0); y = float(md @ KY)
        obj = np.array([y + OBJ_BR[0], y + OBJ_BR[1], y + OBJ_BR[2]])
        g = obj / np.maximum(md, 1e-3)
        if md[2] - md[0] <= 12:          # franja que no sale fría (B−R ≤ +12, regla de 05): no se toca
            g = np.ones(3)
        cent.append(float(np.median(p[:, 3]))); gan.append(g)
        med.append(dict(franja=FRANJAS[k], L_centro=round(cent[-1], 1), n=int(len(p)), rgb_mediana=[round(float(x), 1) for x in md],
                        b_menos_r=round(float(md[2] - md[0]), 1), ganancia=[round(float(x), 4) for x in gan[-1]]))
    return np.array(cent), np.array(gan), med


def tela_br(rgb, bl):
    L, sat = lum_sat(rgb)
    m = bl & (L > 150) & (sat < 0.12)
    if m.sum() < 500:
        return None
    q = rgb[m]; q = q[L[m] >= np.median(L[m])]
    md = np.median(q, 0)
    return dict(rgb=[round(float(x), 1) for x in md], b_menos_r=round(float(md[2] - md[0]), 1),
                g_menos_r=round(float(md[1] - md[0]), 1))


def blanca_lisa(rgb, caja):
    """criterio común de la tanda: B−R de la Blanca medido en la tela lisa (L > 170, sat < 0,15) dentro del componente
    de la remera (mascara_blanca en la caja: deja afuera cielo, espuma y arena sueltos). Devuelve (dict | None, máscara)."""
    bl, L, sat = mascara_blanca(rgb, caja, union=True)
    m = bl & (L > 170) & (sat < 0.15)
    if m.sum() < 500:
        return None, m
    md = np.median(rgb[m], 0)
    return dict(n_px=int(m.sum()), rgb=[round(float(x), 1) for x in md], b_menos_r=round(float(md[2] - md[0]), 1),
                g_menos_r=round(float(md[1] - md[0]), 1), amarillenta=bool(md[2] < md[0] - 1)), m


def celeste_privee(rgb, caja):
    """«Founders Privée» celeste: píxeles junto a la tela de la Blanca (15 px) con B−R > 25, sat > 0,22 y L > 140.
    Devuelve (dict | None, máscara): mediana RGB y tono (grados HSV; el celeste del arte ronda 200–210°)."""
    import colorsys
    from scipy import ndimage as nd
    bl, L, sat = mascara_blanca(rgb, caja, union=True)
    if not bl.any():
        return None, bl
    x0, y0, x1, y1 = caja
    dentro = np.zeros(L.shape, bool); dentro[y0:y1, x0:x1] = True
    cerca = nd.binary_dilation(nd.binary_fill_holes(bl), iterations=15) & dentro
    m = cerca & ((rgb[..., 2] - rgb[..., 0]) > 25) & (sat > 0.22) & (L > 140)   # sin las sombras azuladas de la tela
    if m.sum() < 300:
        return None, m
    md = np.median(rgb[m], 0)
    h, s_, v = colorsys.rgb_to_hsv(*(np.clip(md, 0, 255) / 255))
    return dict(n_px=int(m.sum()), rgb=[round(float(x), 1) for x in md], b_menos_r=round(float(md[2] - md[0]), 1),
                tono_grados=round(h * 360, 1), saturacion=round(s_, 3)), m


def tabla_blanca(cajas, base_mp4, planos_json, evid_img=None, rotulo=''):
    """tabla por plano (criterio común de la tanda): B−R de la tela lisa de la Blanca en el máster (base sin interfaz) en
    3 cuadros (2 después de la entrada, medio, 3 antes de la salida) y, si el plano se neutralizó, en el intermedio sin
    neutralizar; celeste de «Founders Privée» antes/después. cajas: {id_plano: (caja, nota)}. Con evid_img guarda la
    hoja de máscaras (verde = tela lisa medida, magenta = celeste) del cuadro medio de cada plano."""
    pj = json.load(open(planos_json))
    filas, vistas = [], []
    for pl in pj['planos']:
        if pl['id'] not in cajas:
            continue
        caja, nota = cajas[pl['id']]
        m0, nf = pl['m0'], pl['cuadros']
        ks = [min(2, nf - 1), nf // 2, max(0, nf - 3)]
        crudo = Path(pl['salida']).with_name(f"{pl['id']}_sin_neutralizar.mp4")
        # «neutralizada» = la regla se aplicó (B−R previo > +12); si no, el plano pasó sin tocar y no hay «antes»
        neutra = bool(pj.get('blanca', {}).get(pl['id'], {}).get('aplicada', False))
        medidas = []
        for k in ks:
            fr = leer_rgb(base_mp4, m0 + k, m0 + k)[0].astype(np.float32)
            d, mk = blanca_lisa(fr, caja); c, mc = celeste_privee(fr, caja)
            fila = dict(cuadro_master=m0 + k, despues=d, celeste_despues=c)
            if neutra and crudo.exists():
                fa = leer_rgb(crudo, k, k)[0].astype(np.float32)
                fila['antes'] = blanca_lisa(fa, caja)[0]; fila['celeste_antes'] = celeste_privee(fa, caja)[0]
            medidas.append(fila)
            if k == nf // 2 and evid_img:
                im = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)).convert('RGBA')
                ov = np.zeros((H, W, 4), np.uint8); ov[mk] = (0, 255, 0, 110); ov[mc] = (255, 0, 255, 160)
                im = Image.alpha_composite(im, Image.fromarray(ov)).convert('RGB')
                dr = ImageDraw.Draw(im); dr.rectangle(list(caja), outline=(255, 255, 0), width=4)
                dr.rectangle([0, 0, 1080, 70], fill=(0, 0, 0))
                br = '—' if d is None else f"{d['b_menos_r']:+.0f}"
                dr.text((12, 8), f"{rotulo} plano {pl['id']} {pl['toma']} c{m0 + k} B−R {br}", font=ImageFont.truetype(FONT, 46), fill=(255, 255, 0))
                vistas.append(im.resize((360, 640)))
        vals = [f['despues']['b_menos_r'] for f in medidas if f['despues']]
        antes = [f['antes']['b_menos_r'] for f in medidas if f.get('antes')]
        filas.append(dict(plano=pl['id'], toma=pl['toma'], cuadros=[m0, m0 + nf - 1], caja=list(caja), nota=nota,
                          neutralizada=neutra, b_menos_r_antes=antes or None, b_menos_r_master=vals,
                          cumple=bool(vals) and max(vals) <= (8 if neutra else 12)
                          and not any(f['despues'] and f['despues']['amarillenta'] for f in medidas),
                          medidas=medidas))
    if evid_img and vistas:
        cols = min(6, len(vistas)); rows = (len(vistas) + cols - 1) // cols
        S = Image.new('RGB', (cols * 360, rows * 640))
        for i, v in enumerate(vistas):
            S.paste(v, ((i % cols) * 360, (i // cols) * 640))
        S.save(evid_img, quality=85)
    return filas


OBJ_BR7 = (-1.506, -0.006, 4.494)   # blanco objetivo v2: B−R = +6, G−R = +1,5 con la misma luminancia (margen bajo +8:
                                     # el croma 4:2:0 de los bordes y el peso parcial dejan ~1 punto sin corregir)


def neutralizar_blanca(entrada, salida, caja, umbral=12.0, sigma=3.0):
    """Criterio común de la tanda (25/11): si la tela lisa de la Blanca (L > 170, sat < 0,15; blanca_lisa) pasa de
    B−R +12 en alguno de 3 cuadros del plano, se lleva a B−R ≤ +8 (objetivo +6) solo en los neutros claros de la tela;
    si no pasa, el plano se copia sin tocar.
    Ganancias R/G/B por franja de L y POR CUADRO (la luz cambia dentro del plano), suavizadas en el tiempo (gaussiana
    de sigma cuadros: sin parpadeo); una franja con B−R ≤ +8 no se toca. Peso = clip((0,20 − sat)/0,05) ·
    suave((L − 120)/30) · borde (máscara de la remera +8 px, borde 3 px): el celeste de «Founders Privée» (sat > 0,3),
    ROCCÉ, la arena, el cielo y la piel quedan en 0; los píxeles con peso ≤ 0,002 no se tocan."""
    from scipy import ndimage as nd
    n = contar(entrada)
    ny = W * H; nc = ny // 4
    raw = run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', '2', '-i', entrada, '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'])
    fr = np.frombuffer(raw, np.uint8).reshape(n, ny + 2 * nc)

    def partir(b):
        return b[:ny].reshape(H, W), b[ny:ny + nc].reshape(H // 2, W // 2), b[ny + nc:].reshape(H // 2, W // 2)

    def a_rgb(Y, Cb, Cr):
        return yuv_rgb(Y, np.repeat(np.repeat(Cb, 2, 0), 2, 1), np.repeat(np.repeat(Cr, 2, 0), 2, 1))

    ks = [min(2, n - 1), n // 2, max(0, n - 3)]
    previa = [blanca_lisa(a_rgb(*partir(fr[k])), caja)[0] for k in ks]
    vals = [m['b_menos_r'] for m in previa if m]
    base = dict(entrada=str(entrada), salida=str(salida), caja=list(caja), umbral=umbral, medida_previa=dict(zip(ks, previa)))
    if not vals or max(vals) <= umbral:
        shutil.copyfile(entrada, salida)
        return dict(base, aplicada=False, motivo='B−R ≤ +12 en la tela lisa: no se toca')
    # 1) ganancias por cuadro y franja
    nb = len(FRANJAS)
    G = np.full((n, nb, 3), np.nan); Lc = np.full((n, nb), np.nan); BR = np.full((n, nb), np.nan)
    for k in range(n):
        rgb = a_rgb(*partir(fr[k]))
        bl, L, sat = mascara_blanca(rgb, caja, union=True)
        for b, (lo, hi) in enumerate(FRANJAS):
            m = bl & (L >= lo) & (L < hi) & (sat < 0.15)
            if m.sum() < 2000:
                continue
            md = np.median(rgb[m], 0); y = float(md @ KY)
            Lc[k, b] = y; BR[k, b] = md[2] - md[0]
            G[k, b] = (np.array([y + OBJ_BR7[0], y + OBJ_BR7[1], y + OBJ_BR7[2]]) / np.maximum(md, 1e-3)
                       if md[2] - md[0] > 8 else np.ones(3))
    for b in range(nb):                      # cuadros sin medida: el valor del cuadro medido más cercano
        ok = np.where(~np.isnan(G[:, b, 0]))[0]
        if not len(ok):
            G[:, b] = 1.0; Lc[:, b] = np.mean(FRANJAS[b]); continue
        for k in range(n):
            if np.isnan(G[k, b, 0]):
                j = ok[np.argmin(np.abs(ok - k))]; G[k, b] = G[j, b]; Lc[k, b] = Lc[j, b]
    Gs = nd.gaussian_filter1d(G, sigma, axis=0, mode='nearest')
    cent = np.nanmedian(Lc, 0)
    orden = np.argsort(cent); cent = cent[orden]; Gs = Gs[:, orden]
    # 2) aplicar
    enc = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s',
                            f'{W}x{H}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries',
                            'bt709', '-color_trc', 'bt709', '-i', '-', '-threads', '2', *V.ENC_INT, str(salida)],
                           stdin=subprocess.PIPE)
    ss = lambda x: (lambda c: c * c * (3 - 2 * c))(np.clip(x, 0, 1))
    por_cuadro = []
    for k in range(n):
        Y, Cb, Cr = partir(fr[k])
        rgb = a_rgb(Y, Cb, Cr)
        bl, L, sat = mascara_blanca(rgb, caja, union=True)
        zona = nd.binary_dilation(bl, iterations=8)
        borde = np.asarray(Image.fromarray((zona * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
        g = np.stack([np.interp(L, cent, Gs[k, :, c]) for c in range(3)], -1)
        w = np.clip((0.20 - sat) / 0.05, 0, 1) * ss((L - 120) / 30) * borde
        rgb2 = rgb * (1 + w[..., None] * (g - 1))
        Y2, Cb2, Cr2 = rgb_yuv(rgb2)
        mw = w > 0.002
        mc = mw.reshape(H // 2, 2, W // 2, 2).any((1, 3))
        Cb2 = Cb2.reshape(H // 2, 2, W // 2, 2).mean((1, 3)); Cr2 = Cr2.reshape(H // 2, 2, W // 2, 2).mean((1, 3))
        Yo = np.where(mw, np.clip(np.round(Y2), 0, 255), Y).astype(np.uint8)
        Cbo = np.where(mc, np.clip(np.round(Cb2), 0, 255), Cb).astype(np.uint8)
        Cro = np.where(mc, np.clip(np.round(Cr2), 0, 255), Cr).astype(np.uint8)
        enc.stdin.write(Yo.tobytes() + Cbo.tobytes() + Cro.tobytes())
        if k in ks or k % 6 == 0:
            por_cuadro.append(dict(cuadro=k, pct_tocado=round(float(mw.mean() * 100), 2), antes=blanca_lisa(rgb, caja)[0],
                                   despues=blanca_lisa(a_rgb(Yo, Cbo, Cro), caja)[0]))
    enc.stdin.close(); enc.wait()
    if enc.returncode:
        raise RuntimeError('neutralizar_blanca: codificación')
    franjas = [dict(franja=list(FRANJAS[orden[b]]), L_centro=round(float(cent[b]), 1),
                    b_menos_r_mediana_cuadros=round(float(np.nanmedian(BR[:, orden[b]])), 1),
                    ganancia_media=[round(float(x), 4) for x in Gs[:, b].mean(0)]) for b in range(nb)]
    return dict(base, aplicada=True, objetivo='B−R +6, G−R +1,5 (≤ +8)', franjas=franjas, control=por_cuadro)


FRANJAS_N = [(0, 30), (30, 55), (55, 90)]
OBJ_RB_N = (1.5748, -0.4252, -0.4252)   # negro objetivo: R−B = +2, G−R = −2 con la misma luminancia (fotos de PRODUCTO:
                                         # negra_frente_detalle_estampado R−B +3,8; negra_espalda_estudio −1,9)


def _negra_peso(L, sat):
    ss = lambda x: (lambda c: c * c * (3 - 2 * c))(np.clip(x, 0, 1))
    return ss((95 - L) / 25) * np.clip((0.45 - sat) / 0.10, 0, 1)


def tela_negra(rgb, caja=None):
    """color de la Negra: media de la mitad más oscura de los píxeles de tela (L < 90, sat < 0,40) en la caja."""
    if caja is not None:
        x0, y0, x1, y1 = caja; rgb = rgb[y0:y1, x0:x1]
    L, sat = lum_sat(rgb)
    m = (L < 90) & (sat < 0.40)
    if m.sum() < 500:
        return None
    q = rgb[m]; q = q[L[m] <= np.median(L[m])]; md = q.mean(0)
    return dict(rgb=[round(float(x), 1) for x in md], r_menos_b=round(float(md[0] - md[2]), 1),
                g_menos_r=round(float(md[1] - md[0]), 1))


def neutralizar_negra(entrada, salida, caja=(0, 0, W, H), medir=(0, 0.33, 0.66, 1.0)):
    """Reescribe un plano corrigiendo solo la tela oscura de la Negra cuando sale marrón (R−B > +6 en su franja):
    peso = suave((95 − L)/25) · clip((0,45 − sat)/0,10) dentro de la caja. Las letras claras, la piel (sat ≥ 0,45 o
    L ≥ 95) quedan con peso 0 y los píxeles con peso ≤ 0,002 no se tocan. Ganancias UNA por plano (sin parpadeo)."""
    n = contar(entrada)
    ny = W * H; nc = ny // 4
    raw = run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', '2', '-i', entrada, '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'])
    fr = np.frombuffer(raw, np.uint8).reshape(n, ny + 2 * nc)

    def partir(b):
        return b[:ny].reshape(H, W), b[ny:ny + nc].reshape(H // 2, W // 2), b[ny + nc:].reshape(H // 2, W // 2)

    def a_rgb(Y, Cb, Cr):
        return yuv_rgb(Y, np.repeat(np.repeat(Cb, 2, 0), 2, 1), np.repeat(np.repeat(Cr, 2, 0), 2, 1))

    x0, y0, x1, y1 = caja
    dentro = np.zeros((H, W), bool); dentro[y0:y1, x0:x1] = True
    idx = sorted({min(n - 1, int(round(m * (n - 1)))) for m in medir})
    acc = {k: [] for k in range(len(FRANJAS_N))}
    for i in idx:
        rgb = a_rgb(*partir(fr[i])); L, sat = lum_sat(rgb)
        for k, (lo, hi) in enumerate(FRANJAS_N):
            m = dentro & (L >= lo) & (L < hi) & (sat < 0.40)
            acc[k].append(rgb[m])
    cent, gan, med = [], [], []
    for k, v in acc.items():
        q = np.concatenate(v, 0)
        if len(q) < 3000:
            continue
        md = np.median(q, 0); y = float(md @ KY)
        g = np.array([y + OBJ_RB_N[0], y + OBJ_RB_N[1], y + OBJ_RB_N[2]]) / np.maximum(md, 1e-3)
        if md[0] - md[2] <= 6:           # franja que no sale marrón: no se toca
            g = np.ones(3)
        cent.append(y); gan.append(g)
        med.append(dict(franja=list(FRANJAS_N[k]), L_centro=round(y, 1), n=int(len(q)),
                        rgb_mediana=[round(float(x), 1) for x in md], r_menos_b=round(float(md[0] - md[2]), 1),
                        ganancia=[round(float(x), 4) for x in g]))
    cent = np.array(cent); gan = np.array(gan)
    enc = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s',
                            f'{W}x{H}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries',
                            'bt709', '-color_trc', 'bt709', '-i', '-', '-threads', '2', *V.ENC_INT, str(salida)],
                           stdin=subprocess.PIPE)
    por_cuadro = []
    for k in range(n):
        Y, Cb, Cr = partir(fr[k])
        rgb = a_rgb(Y, Cb, Cr)
        L, sat = lum_sat(rgb)
        g = np.stack([np.interp(L, cent, gan[:, c]) for c in range(3)], -1)
        w = _negra_peso(L, sat) * dentro
        rgb2 = rgb * (1 + w[..., None] * (g - 1))
        Y2, Cb2, Cr2 = rgb_yuv(rgb2)
        mw = w > 0.002
        mc = mw.reshape(H // 2, 2, W // 2, 2).any((1, 3))
        Cb2 = Cb2.reshape(H // 2, 2, W // 2, 2).mean((1, 3)); Cr2 = Cr2.reshape(H // 2, 2, W // 2, 2).mean((1, 3))
        Yo = np.where(mw, np.clip(np.round(Y2), 0, 255), Y).astype(np.uint8)
        Cbo = np.where(mc, np.clip(np.round(Cb2), 0, 255), Cb).astype(np.uint8)
        Cro = np.where(mc, np.clip(np.round(Cr2), 0, 255), Cr).astype(np.uint8)
        enc.stdin.write(Yo.tobytes() + Cbo.tobytes() + Cro.tobytes())
        if k in idx or k % 6 == 0:
            por_cuadro.append(dict(cuadro=k, pct_tocado=round(float(mw.mean() * 100), 2), antes=tela_negra(rgb, caja),
                                   despues=tela_negra(a_rgb(Yo, Cbo, Cro), caja)))
    enc.stdin.close(); enc.wait()
    if enc.returncode:
        raise RuntimeError('neutralizar_negra: codificación')
    return dict(entrada=str(entrada), salida=str(salida), caja=list(caja), cuadros_medicion=idx, franjas=med,
                objetivo='R−B +2, G−R −2 (misma luminancia)', control=por_cuadro)


# ---------------------------------------------------------------------------------------------------------------
# interfaz · elementos con los estilos de comun.py
# ---------------------------------------------------------------------------------------------------------------
_IMG = {}


def img(clave, hacer):
    if clave not in _IMG:
        _IMG[clave] = hacer()
    return _IMG[clave]


def margen_placa(size):
    return int(size * 0.6)          # comun.placa deja este margen alrededor del renglón


def t_placa(txt, size=88, halo=0.55, peso='extrabold', color=C.BLANCO, interlineado=1.05):
    return img(('placa', txt, size, halo, peso, color, interlineado),
               lambda: C.placa(txt, size, peso=peso, color=color, halo=halo, interlineado=interlineado))


def t_dato(txt, size=48, halo=0.6):
    return img(('dato', txt, size, halo), lambda: C.placa(txt, size, peso='medium', halo=halo))


def t_serif(txt, size=96, halo=0.6):
    return img(('serif', txt, size, halo), lambda: C.placa(txt, size, peso='serif', halo=halo))


def t_caja(txt, size=76, tema='blanca'):
    return img(('caja', txt, size, tema), lambda: C.caja(txt, size, tema=tema))


class D:
    """un elemento dibujado en un cuadro: imagen RGBA, posición (borde superior y; centro cx o x izquierda), escala, alfa.
    y_texto: el borde superior del renglón del guion (para placas se descuenta el margen del PNG)."""
    __slots__ = ('clave', 'im', 'y', 'cx', 'x', 'escala', 'alfa')

    def __init__(self, clave, im, y, cx=W // 2, x=None, escala=1.0, alfa=1.0):
        self.clave, self.im, self.y, self.cx, self.x, self.escala, self.alfa = clave, im, y, cx, x, escala, alfa

    def key(self):
        return (self.clave, round(self.y, 2), self.cx if self.x is None else ('x', self.x), round(self.escala, 4), round(self.alfa, 3))


def placa_en(txt, y, size=88, halo=0.55, cx=W // 2, x=None, escala=1.0, alfa=1.0, peso='extrabold', interlineado=1.05):
    im = t_placa(txt, size, halo, peso, interlineado=interlineado)
    return D(('placa', txt, size, halo, peso, interlineado), im, y - margen_placa(size), cx=cx,
             x=None if x is None else x - margen_placa(size), escala=escala, alfa=alfa)


def dato_en(txt, y, size=48, halo=0.6, cx=W // 2, x=None, alfa=1.0):
    im = t_dato(txt, size, halo)
    return D(('dato', txt, size, halo), im, y - margen_placa(size), cx=cx, x=None if x is None else x - margen_placa(size), alfa=alfa)


def serif_en(txt, y, size=96, halo=0.6, cx=W // 2, alfa=1.0):
    im = t_serif(txt, size, halo)
    return D(('serif', txt, size, halo), im, y - margen_placa(size), cx=cx, alfa=alfa)


POP_ANCHO_MAX = W - 2 * 24          # el pop nunca saca una caja del cuadro (deja 24 px por lado)


def caja_en(txt, y, size=76, tema='blanca', cx=W // 2, escala=1.0, alfa=1.0):
    im = t_caja(txt, size, tema)
    if escala > 1.0 and im.width * escala > POP_ANCHO_MAX:      # caja ancha: el pop se limita al ancho del cuadro
        escala = max(1.0, POP_ANCHO_MAX / im.width)
    return D(('caja', txt, size, tema), im, y, cx=cx, escala=escala, alfa=alfa)


def t_dato_caja(txt, size=50):
    return img(('datoC', txt, size), lambda: C.caja(txt, size, tema='negra', peso='semibold'))


def dato_caja_en(txt, y, cx=W // 2, x=None, alfa=1.0, size=50):
    """dato chico sobre fondo claro (criterio común de la tanda, 25/11): C.caja(texto, 50, tema='negra',
    peso='semibold'); y = borde superior de la caja, como las demás cajas; x = borde izquierdo si se alinea a la izquierda."""
    return D(('datoC', txt, size), t_dato_caja(txt, size), y, cx=cx, x=x, alfa=alfa)


POP = (1.18, 1.09)                  # comun.pop: 118 % → 109 % → 100 % en 3 cuadros


def escala_pop(n, n0):
    k = n - n0
    return POP[k] if 0 <= k < len(POP) else 1.0


def componer(dibujos):
    L = C.lienzo()
    cajas = []
    for d in dibujos:
        im = d.im
        if d.alfa < 0.999:
            im = im.copy(); a = np.asarray(im.getchannel('A'), np.float32) * max(0.0, d.alfa)
            im.putalpha(Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8)))
        cajas.append(C.pegar(L, im, d.y, cx=d.cx, x=d.x, escala=d.escala))
    return L, cajas


def escribir_capa(nf, dibujos_de, carpeta):
    """dibujos_de(n) -> lista de D. Escribe carpeta/%04d.png (RGBA 1080×1920); cuadros iguales = enlace duro.
    Devuelve el registro por cuadro (claves y cajas) para el control."""
    carpeta = Path(carpeta)
    if carpeta.exists():
        shutil.rmtree(carpeta)
    carpeta.mkdir(parents=True)
    vistos, reg = {}, []
    for n in range(nf):
        ds = dibujos_de(n)
        k = tuple(d.key() for d in ds)
        p = carpeta / f'{n:04d}.png'
        if k in vistos:
            os.link(vistos[k][0], p); cajas = vistos[k][1]
        else:
            L, cajas = componer(ds)
            L.save(p, compress_level=1)
            vistos[k] = (p, cajas)
        reg.append(dict(cuadro=n, elementos=[str(d.clave[1]) if len(d.clave) > 1 else str(d.clave) for d in ds],
                        cajas=[list(map(int, c)) for c in cajas]))
    return reg, len(vistos)


# ---------------------------------------------------------------------------------------------------------------
# máster (mismos parámetros que video.master) y versión sin música (mismo flujo de video)
# ---------------------------------------------------------------------------------------------------------------
ENC_MASTER = ['-c:v', 'libx264', '-profile:v', 'high', '-level:v', '4.0', '-preset', 'slow', '-crf', '17',
              '-maxrate', '20M', '-bufsize', '25M', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-g', '30',
              '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']
ENC_AUDIO = ['-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2']
META = ['-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
        '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler']


def _mtime_dir(d):
    return max(f.stat().st_mtime for f in Path(d).glob('*.png'))


def video_ui(base, capa_dir, salida_video, nf):
    """flujo de video del máster: base (planos unidos) + capa de interfaz (secuencia PNG RGBA, un cuadro por cuadro)
    con UN overlay sincronizado por cuadro (sin ventanas enable). Mismos parámetros que video.master. Se reutiliza si
    ya existe y es más nuevo que la base y la capa (cambiar solo el sonido no recodifica la imagen)."""
    sv = Path(salida_video)
    if sv.exists() and sv.stat().st_mtime > max(Path(base).stat().st_mtime, _mtime_dir(capa_dir)):
        return sv, False
    fc = ('[0:v]setsar=1[b];[1:v]format=rgba,setsar=1[u];[b][u]overlay=0:0:format=auto:eof_action=pass:shortest=0,'
          'format=yuv420p[vout]')
    V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(base), '-framerate', str(FPS), '-start_number', '0', '-i',
          str(Path(capa_dir) / '%04d.png'), '-filter_complex', fc, '-map', '[vout]', '-an',
          '-frames:v', str(nf), *ENC_MASTER, *META[:4], '-metadata:s:v:0', 'handler_name=VideoHandler',
          '-movflags', '+faststart', str(sv)])
    return sv, True


def master_ui(base, capa_dir, audio_wav, salida, nf, video_cache=None):
    """máster = video_ui (copiado sin recodificar) + mezcla en AAC-LC 48 kHz; faststart; sin metadatos."""
    vc = Path(video_cache or (str(salida) + '.video.mp4'))
    _, nuevo = video_ui(base, capa_dir, vc, nf)
    V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(vc), '-i', str(audio_wav), '-map', '0:v:0', '-map', '1:a:0',
          '-c:v', 'copy', *ENC_AUDIO, *META, '-shortest', '-movflags', '+faststart', str(salida)])
    return dict(salida=str(salida), video=str(vc), video_recodificado=nuevo)


def sin_musica(master, audio_wav, salida):
    V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(master), '-i', str(audio_wav), '-map', '0:v:0', '-map', '1:a:0',
          '-c:v', 'copy', *ENC_AUDIO, *META, '-shortest', '-movflags', '+faststart', str(salida)])
    return salida


# ---------------------------------------------------------------------------------------------------------------
# sonido
# ---------------------------------------------------------------------------------------------------------------
def medir_ebur(f):
    r = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-nostats', '-threads', '2', '-i', str(f), '-af',
                        'ebur128=peak=true:framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True).stderr
    g = lambda k: float([l for l in r.splitlines() if l.strip().startswith(k)][-1].split()[1])
    return g('I:'), g('Peak:'), g('LRA:')


def limitar_tp(salida, lufs=-14.0, tp_max=-1.5, pre_af=None):
    """copia del criterio de life_v2.limitar_tp: rehace la última etapa de sonido.Mezcla.exportar desde _pre.wav con
    alimiter (level=false) bajando el techo 0,5 dB por vuelta hasta pico verdadero ≤ tp_max y −14 LUFS."""
    pre = str(salida).replace('.wav', '_pre.wav')
    I0, _, _ = medir_ebur(pre)
    gan = lufs - I0; lim_db = -1.6; hist = []
    for _ in range(14):
        lim = 10 ** (lim_db / 20)
        run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', pre, '-af',
             (f'{pre_af},' if pre_af else '') +
             f'volume={gan:.2f}dB,alimiter=limit={lim:.4f}:level=false:attack=3:release=60:latency=1', '-c:a', 'pcm_f32le', str(salida)])
        I, Pk, LRA = medir_ebur(salida); hist.append(dict(techo_db=lim_db, ganancia_db=round(gan, 2), lufs=I, pico_dbtp=Pk))
        if abs(I - lufs) < 0.3 and Pk <= tp_max:
            break
        if Pk > tp_max:
            lim_db -= 0.5
        gan += (lufs - I)
    return dict(lufs=I, pico_dbtp=Pk, lra=LRA, vueltas=hist, pre_af=pre_af)


TP_WAV = -2.0      # pico verdadero del WAV: el AAC sube ≈ 0,5–0,7 dB (medido: −1,7 → −1,0 dBTP), el máster queda ≤ −1,2
COMP_SM = 'acompressor=threshold=0.03:ratio=3:attack=5:release=150:knee=4'   # −30 dBFS, 3:1 (solo mezclas sin música)


def exportar(m, wav, lufs=-14.0, g_pistas=None, comp=None):
    """sonido.Mezcla.exportar; si el pico pasa de −1,5 dBTP, la sonoridad se va ±0,4 o se pide compresión previa
    (mezclas sin música: ambiente muy desparejo entre tomas), se rehace la última etapa con limitar_tp."""
    r = m.exportar(str(wav), lufs=lufs, g_pistas=g_pistas)
    out = dict(exportar=dict(lufs=r[0], pico_dbtp=r[1]), g_pistas=g_pistas)
    if comp or r[1] > TP_WAV or abs(r[0] - lufs) >= 0.4:
        out['limitado'] = limitar_tp(wav, lufs, tp_max=TP_WAV, pre_af=comp)
    I, Pk, LRA = medir_ebur(wav)
    out.update(lufs=I, pico_dbtp=Pk, lra=LRA)
    return out


def rms_fuente(toma, src0, dur, hp=None):
    from sonido import Mezcla, filt
    a = Mezcla(0.1).leer(toma)
    seg = a[int(src0 * SR):int((src0 + dur) * SR)]
    if hp:
        seg = filt(seg, 'high', hp)
    return 20 * math.log10(float(np.sqrt((seg ** 2).mean())) + 1e-12)


# ---------------------------------------------------------------------------------------------------------------
# detector de estampado (para controlar que ningún texto lo toque)
# ---------------------------------------------------------------------------------------------------------------
def _std_local(L, s=7):
    from scipy import ndimage as nd
    m = nd.uniform_filter(L, s); m2 = nd.uniform_filter(L * L, s)
    return np.sqrt(np.maximum(m2 - m * m, 0))


def tela(rgb):
    """máscaras (H/2 × W/2) de la tela de la Blanca y de la Negra, rellenas (el estampado queda adentro).
    Tela = superficie lisa (desvío local de L < 12 en 7×7) y neutra; Blanca L > 165, sat < 0,12; Negra L < 55.
    Se descartan las componentes que tocan el borde superior del cuadro (mar, cielo, espuma lejana), salvo una Negra
    que ocupe > 35 % del cuadro (macro de 3453), y las chicas (Blanca < 0,4 %, Negra < 1 % del cuadro)."""
    from scipy import ndimage as nd
    a = rgb[::2, ::2].astype(np.float32)
    L, sat = lum_sat(a)
    sd = _std_local(L)
    tot = L.size
    out = {}
    for nom, m0, amin in (('blanca', (L > 165) & (sat < 0.12) & (sd < 12), 0.004), ('negra', (L < 55) & (sd < 12), 0.01)):
        m = nd.binary_opening(m0, iterations=2)
        lab, n = nd.label(m)
        keep = np.zeros(L.shape, bool)
        for i, sl in enumerate(nd.find_objects(lab)):
            comp = lab[sl] == i + 1
            ar = comp.sum()
            if ar < amin * tot:
                continue
            if sl[0].start == 0 and not (nom == 'negra' and ar > 0.35 * tot):
                continue
            keep[sl] |= comp
        out[nom] = nd.binary_fill_holes(nd.binary_closing(keep, iterations=8)) if keep.any() else keep
    return out, a, L, sat


def estampado(rgb):
    """máscara (H/2 × W/2) de los estampados visibles en un cuadro 1080×1920 RGB, solo DENTRO de la tela detectada:
    Blanca → letras oscuras de ROCCÉ (L < fondo local − 45) y celeste de «Founders Privée» (sombrero de copa de B/R con
    disco de 31 px > 0,06, sat > 0,08); Negra → trazos claros («Founders Privée» gris, relieve, ROCCÉ tono sobre tono:
    sombrero de copa de L con disco de 21 px > 18, sat < 0,25). Dilatada 6 px (12 px a tamaño real) para medir con margen."""
    from scipy import ndimage as nd
    tl, a, L, sat = tela(rgb)
    r, b = a[..., 0] + 1, a[..., 2] + 1
    out = np.zeros(L.shape, bool)
    if tl['blanca'].any():
        bgL = nd.grey_closing(L, size=(15, 15))
        osc = tl['blanca'] & (L < bgL - 45)
        az = b / r
        th = az - nd.grey_opening(az, size=(31, 31))
        cel = tl['blanca'] & (th > 0.06) & (sat > 0.08)
        out |= nd.binary_opening(osc | cel, iterations=1)
    if tl['negra'].any():
        th = L - nd.grey_opening(L, size=(21, 21))
        out |= nd.binary_opening(tl['negra'] & (th > 18) & (sat < 0.25), iterations=1)
    lab, n = nd.label(out)
    if n:
        s_ = nd.sum(out, lab, range(1, n + 1))
        out = np.isin(lab, 1 + np.nonzero(s_ >= 12)[0])
    return nd.binary_dilation(out, iterations=6)


def estampado_roi(rgb, roi):
    """estampado dentro de la zona de las prendas de ese plano (roi = x0, y0, x1, y1 a tamaño real, marcada a mano por
    plano), a media resolución. Tela de la Blanca = (L > 165, sat < 0,15) cerrada y rellena (componentes ≥ 0,2 % del
    cuadro); tela de la Negra = (L < 60) cerrada y rellena (≥ 0,5 %). Dentro de cada tela:
      · Blanca (hasta 30 px de la tela: el borde del cuadro puede abrir el hueco del relleno): letras azul marino de
        ROCCÉ (L < 100, B − R > 10) y celeste de «Founders Privée» con su subrayado (B − R > 22, sombrero de copa de
        B − R con disco de 31 px > 15, sat > 0,15, L > 140);
      · Negra: trazos claros (sombrero de copa de L con disco de 21 px > 15, L > 70, sat < 0,3, B − R > −8).
    Se quitan las motas y pelusas (< 40 px a media resolución) y se dilata 6 px (12 px a tamaño real)."""
    from scipy import ndimage as nd
    a = rgb[::2, ::2].astype(np.float32)
    L, sat = lum_sat(a)
    br = a[..., 2] - a[..., 0]
    x0, y0, x1, y1 = [int(v) // 2 for v in roi]
    zona = np.zeros(L.shape, bool); zona[max(0, y0):y1, max(0, x0):x1] = True
    tot = L.size

    def tela_de(m, amin):
        m = nd.binary_closing(m & zona, iterations=4)
        lab, n = nd.label(m)
        if not n:
            return m
        s_ = nd.sum(m, lab, range(1, n + 1))
        return nd.binary_fill_holes(np.isin(lab, 1 + np.nonzero(s_ >= amin * tot)[0]))

    bl = tela_de((L > 165) & (sat < 0.15), 0.002)
    ng = tela_de(L < 60, 0.005)
    m = np.zeros(L.shape, bool)
    if bl.any():
        th = br - nd.grey_opening(br, size=(31, 31))
        cerca = nd.binary_dilation(bl, iterations=15)
        m |= cerca & (L < 100) & (br > 10)
        m |= cerca & (br > 22) & (th > 15) & (sat > 0.15) & (L > 140)
    if ng.any():
        thL = L - nd.grey_opening(L, size=(21, 21))
        m |= ng & (thL > 15) & (L > 70) & (sat < 0.3) & (br > -8)
    m &= zona
    m = nd.binary_opening(m, iterations=1)
    lab, n = nd.label(m)
    if n:
        s_ = nd.sum(m, lab, range(1, n + 1))
        m = np.isin(lab, 1 + np.nonzero(s_ >= 40)[0])
    return nd.binary_dilation(m, iterations=6)


def roi_en(tabla, n):
    """tabla: [(c0, c1, caja0, caja1)] → caja interpolada en el cuadro n (None si no hay prenda marcada)."""
    for c0, c1, b0, b1 in tabla:
        if c0 <= n <= c1:
            k = 0 if c1 == c0 else (n - c0) / (c1 - c0)
            return [b0[i] + (b1[i] - b0[i]) * k for i in range(4)]
    return None


def choque_roi(base_mp4, capa_dir, cuadros, tabla, alfa_min=60):
    """por cuadro: contacto entre la interfaz visible (alfa > alfa_min) y el estampado (dilatado 12 px) dentro de la
    zona de prendas del plano; y la distancia mínima en px (a tamaño real) entre la interfaz y el estampado sin dilatar."""
    from scipy import ndimage as nd
    out = {}
    cuadros = sorted(cuadros)
    bloques = [cuadros[i:i + 48] for i in range(0, len(cuadros), 48)]
    for bl in bloques:
        lo, hi = bl[0], bl[-1]
        fr = leer_rgb(base_mp4, lo, hi)
        for n in bl:
            _choque_un(out, fr[n - lo], n, capa_dir, tabla, alfa_min, nd)
        del fr
    return out


def _choque_un(out, rgb, n, capa_dir, tabla, alfa_min, nd):
    if True:
        roi = roi_en(tabla, n)
        if roi is None:
            return
        m = estampado_roi(rgb, roi)
        a = alfa_capa(capa_dir, n) > alfa_min
        inter = m & a
        nuc = nd.binary_erosion(m, iterations=6) if m.any() else m
        dist = None
        if nuc.any() and a.any():
            dt = nd.distance_transform_edt(~a)
            dist = int(round(float(dt[nuc].min()) * 2))
        ys, xs = np.nonzero(inter)
        out[n] = dict(pix=int(inter.sum()), dist_px=dist, roi=[int(v) for v in roi],
                      caja=None if not len(ys) else [int(xs.min()) * 2, int(ys.min()) * 2, int(xs.max()) * 2, int(ys.max()) * 2])


def vista_roi(fr_rgb, capa_dir, n, roi, salida, rot=''):
    m = estampado_roi(fr_rgb, roi)
    base = Image.fromarray(fr_rgb).convert('RGBA')
    ov = np.zeros((H // 2, W // 2, 4), np.uint8); ov[m] = (255, 0, 0, 120)
    base = Image.alpha_composite(base, Image.fromarray(ov).resize((W, H), Image.NEAREST))
    base = Image.alpha_composite(base, Image.open(Path(capa_dir) / f'{n:04d}.png'))
    d = ImageDraw.Draw(base); fnt = ImageFont.truetype(FONT, 34)
    d.rectangle(list(map(int, roi)), outline=(255, 255, 0, 255), width=3)
    d.rectangle([0, 0, 760, 50], fill=(0, 0, 0, 255))
    d.text((10, 6), f'{rot} c{n} · rojo = estampado (+12 px) · amarillo = zona de prendas', font=fnt, fill=(255, 255, 0, 255))
    base.convert('RGB').save(salida, quality=88)


def alfa_capa(capa_dir, n):
    a = np.asarray(Image.open(Path(capa_dir) / f'{n:04d}.png'))[..., 3]
    return a[::2, ::2]


def choque_texto_estampado(base_mp4, capa_dir, cuadros, alfa_min=60):
    """por cuadro: píxeles (a media resolución) donde la interfaz (alfa > alfa_min, sin contar el halo tenue) cae sobre
    el estampado detectado (dilatado 12 px)."""
    out = {}
    lo, hi = min(cuadros), max(cuadros)
    fr = leer_rgb(base_mp4, lo, hi)
    for n in cuadros:
        m = estampado(fr[n - lo])
        a = alfa_capa(capa_dir, n) > alfa_min
        inter = m & a
        ys, xs = np.nonzero(inter)
        out[n] = dict(pix=int(inter.sum()), caja=None if not len(ys) else [int(xs.min()) * 2, int(ys.min()) * 2,
                                                                            int(xs.max()) * 2, int(ys.max()) * 2],
                      estampado_pix=int(m.sum()))
    return out, fr


def vista_choque(fr_rgb, capa_dir, n, salida, rot=''):
    m = estampado(fr_rgb)
    base = Image.fromarray(fr_rgb).convert('RGBA')
    ov = np.zeros((H // 2, W // 2, 4), np.uint8); ov[m] = (255, 0, 0, 110)
    ovi = Image.fromarray(ov).resize((W, H), Image.NEAREST)
    base = Image.alpha_composite(base, ovi)
    capa = Image.open(Path(capa_dir) / f'{n:04d}.png')
    base = Image.alpha_composite(base, capa)
    d = ImageDraw.Draw(base); fnt = ImageFont.truetype(FONT, 34)
    d.rectangle([0, 0, 560, 50], fill=(0, 0, 0, 255)); d.text((10, 6), f'{rot} c{n} (rojo = estampado detectado)', font=fnt, fill=(255, 255, 0, 255))
    base.convert('RGB').save(salida, quality=90)


# ---------------------------------------------------------------------------------------------------------------
# control
# ---------------------------------------------------------------------------------------------------------------
def ffprobe_json(f):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', f]))


def ficha(f):
    f = Path(f)
    err = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', '2', '-i', str(f), '-f', 'null', '-'],
                         capture_output=True, text=True).stderr.strip()
    pj = ffprobe_json(f)
    vs = [s for s in pj['streams'] if s['codec_type'] == 'video'][0]
    au = [s for s in pj['streams'] if s['codec_type'] == 'audio'][0]
    cuerpo = f.read_bytes()
    gps = [m.decode() for m in (b'ISO6709', b'location', b'com.apple.quicktime', b'\xa9xyz') if m in cuerpo]
    i_moov, i_mdat = cuerpo.find(b'moov'), cuerpo.find(b'mdat')
    I, Pk, LRA = medir_ebur(f)
    return dict(archivo=str(f), bytes=f.stat().st_size, sha256=hashlib.sha256(cuerpo).hexdigest(),
                md5_video=U.md5_stream(f, 'v'), md5_audio=U.md5_stream(f, 'a'), decodifica_completo=(err == ''),
                errores=err[:400],
                video=dict(codec=vs['codec_name'], perfil=vs.get('profile'), nivel=vs.get('level'), pix_fmt=vs['pix_fmt'],
                           ancho=vs['width'], alto=vs['height'], fps=vs['r_frame_rate'], cuadros=int(vs['nb_frames']),
                           duracion=float(vs['duration']), color=[vs.get('color_range'), vs.get('color_space'),
                                                                  vs.get('color_transfer'), vs.get('color_primaries')]),
                audio=dict(codec=au['codec_name'], perfil=au.get('profile'), hz=int(au['sample_rate']), canales=au['channels'],
                           duracion=float(au['duration'])),
                duracion_formato=float(pj['format']['duration']), etiquetas_formato=pj['format'].get('tags', {}),
                faststart_moov_antes_de_mdat=bool(0 <= i_moov < i_mdat), marcas_gps_o_ubicacion=gps,
                sonoridad=dict(lufs_integrado=I, pico_dbtp=Pk, lra=LRA))


def hoja_cada(mp4, salida, cada=15, cols=8, ancho=200):
    return U.hoja_contacto(mp4, salida, cada=cada, cols=cols, ancho=ancho)


def cuadros(mp4, ns, carpeta, prefijo='c'):
    carpeta = Path(carpeta); carpeta.mkdir(parents=True, exist_ok=True)
    ns = sorted(set(ns))
    sel = '+'.join(f'eq(n\\,{k})' for k in ns)
    run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-threads', '2', '-i', mp4, '-vf', f"select='{sel}'", '-fps_mode',
         'vfr', '-q:v', '2', carpeta / 'tmp_%03d.jpg'])
    out = []
    for k, n in enumerate(ns):
        p = carpeta / f'{prefijo}{n:03d}.jpg'
        (carpeta / f'tmp_{k + 1:03d}.jpg').rename(p); out.append(p)
    return out


def tira(paths, rotulos, salida, ancho=360):
    fnt = ImageFont.truetype(FONT, 22)
    ims = []
    for p, r in zip(paths, rotulos):
        im = Image.open(p).convert('RGB'); im = im.resize((ancho, round(ancho * im.height / im.width)), Image.LANCZOS)
        d = ImageDraw.Draw(im); tw = d.textlength(r, font=fnt); d.rectangle([0, 0, tw + 12, 30], fill=(0, 0, 0))
        d.text((6, 3), r, font=fnt, fill=(255, 255, 0)); ims.append(im)
    Wd = Image.new('RGB', (sum(i.width + 2 for i in ims), max(i.height for i in ims)), (30, 30, 30))
    x = 0
    for i in ims:
        Wd.paste(i, (x, 0)); x += i.width + 2
    Wd.save(salida, quality=90)
    return salida


def vista_360(mp4, ns, salida, cols=6):
    """cuadros a 360 px de ancho (lectura en teléfono), sin rótulos encima de la imagen (rótulo debajo)."""
    tmp = Path(salida).parent / '_v360'; tmp.mkdir(exist_ok=True)
    ps = cuadros(mp4, ns, tmp)
    fnt = ImageFont.truetype(FONT, 18)
    tiles = []
    for p, n in zip(ps, sorted(set(ns))):
        im = Image.open(p).convert('RGB').resize((360, 640), Image.LANCZOS)
        t = Image.new('RGB', (360, 666), (20, 20, 20)); t.paste(im, (0, 0))
        ImageDraw.Draw(t).text((6, 643), f'c{n} · {n / FPS:.2f} s', font=fnt, fill=(255, 255, 0)); tiles.append(t)
    filas = math.ceil(len(tiles) / cols)
    Wd = Image.new('RGB', (cols * 362, filas * 668), (40, 40, 40))
    for i, t in enumerate(tiles):
        Wd.paste(t, ((i % cols) * 362, (i // cols) * 668))
    Wd.save(salida, quality=90)
    shutil.rmtree(tmp)
    return salida


def niveles(mp4, tramos):
    a = U.audio_np(mp4)
    niv, v100, sil = U.niveles_tramos(a, tramos)
    fin = a[-SR // 2:]
    return dict(tramos=niv, ventanas_100ms_bajo_menos50dbfs=sil,
                rms_ultimo_05s_dbfs=round(float(20 * np.log10(np.sqrt((fin ** 2).mean()) + 1e-12)), 1),
                rms_100ms=v100)


def reduccion_limitador(wav, info):
    """reducción de ganancia del limitador (dB) por ventanas de 10 ms: final contra _pre × ganancia aplicada."""
    import soundfile as sf
    pre, sr = sf.read(str(wav).replace('.wav', '_pre.wav')); fin, _ = sf.read(str(wav))
    if 'limitado' in info and not info['limitado'].get('pre_af'):
        g = info['limitado']['vueltas'][-1]['ganancia_db']
    else:
        g = 20 * np.log10(np.sqrt((fin ** 2).mean()) / np.sqrt((pre ** 2).mean()))
    n = int(0.01 * sr); k = min(len(pre), len(fin)) // n
    pp = np.abs(pre[:k * n]).max(1).reshape(k, n).max(1) * 10 ** (g / 20); pf = np.abs(fin[:k * n]).max(1).reshape(k, n).max(1)
    gr = 20 * np.log10((pf + 1e-9) / (pp + 1e-9))
    peor = np.argsort(gr)[:5]
    return dict(reduccion_max_db=round(float(gr.min()), 1), en_s=[round(float(i * 0.01), 2) for i in peor],
                pct_ventanas_mas_de_1db=round(float((gr < -1).mean() * 100), 1),
                nota='con compresión previa la cifra mezcla compresor + limitador' if info.get('limitado', {}).get('pre_af') else '')


def momentanea(mp4):
    """sonoridad momentánea (400 ms) cada 100 ms con ebur128 (framelog)."""
    r = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-nostats', '-threads', '2', '-i', str(mp4), '-af', 'ebur128=peak=true',
                        '-f', 'null', '-'], capture_output=True, text=True).stderr
    out = []
    for l in r.splitlines():
        if l.strip().startswith('[Parsed_ebur128') and ' M:' in l:
            try:
                t = float(l.split('t:')[1].split()[0]); M = float(l.split('M:')[1].split()[0])
                out.append((round(t, 2), M))
            except Exception:
                pass
    return out


# ---------------------------------------------------------------------------------------------------------------
# entrega
# ---------------------------------------------------------------------------------------------------------------
def entregar(archivos, carpeta_pieza, evid_local, intermedios):
    """copia cada MP4 a EXPORTACIONES/ y a la carpeta de la pieza (sin sobrescribir) y la evidencia; verifica por
    bytes/sha256 en EXPORTACIONES y por md5 de flujos en la carpeta de la pieza (que puede agregar una caja C2PA)."""
    res = {}
    carpeta_pieza = Path(carpeta_pieza); carpeta_pieza.mkdir(parents=True, exist_ok=True)
    for nombre in archivos:
        src = Path(intermedios) / nombre
        for dst in (EXP / nombre, carpeta_pieza / nombre):
            if dst.exists():
                raise RuntimeError(f'{dst} ya existe: no se sobrescribe (corregir = v02)')
            shutil.copyfile(src, dst)
    ev = carpeta_pieza / Path(evid_local).name
    if ev.exists():
        raise RuntimeError(f'{ev} ya existe')
    shutil.copytree(evid_local, ev)
    time.sleep(8)
    for nombre in archivos:
        src = Path(intermedios) / nombre
        ref = dict(bytes=src.stat().st_size, sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                   md5_video=U.md5_stream(src, 'v'), md5_audio=U.md5_stream(src, 'a'))
        for dst in (EXP / nombre, carpeta_pieza / nombre):
            got = dict(bytes=dst.stat().st_size, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
                       md5_video=U.md5_stream(dst, 'v'), md5_audio=U.md5_stream(dst, 'a'))
            res[str(dst)] = dict(got, flujos_iguales=(got['md5_video'] == ref['md5_video'] and got['md5_audio'] == ref['md5_audio']),
                                 archivo_identico=(got == ref))
    n_local = sum(1 for _ in Path(evid_local).rglob('*') if _.is_file()); n_red = sum(1 for _ in ev.rglob('*') if _.is_file())
    res['evidencia'] = dict(carpeta=str(ev), archivos_local=n_local, archivos_red=n_red)
    return res


def zona_visible(capa_dir, alfa_min=60):
    """zona segura medida sobre los píxeles VISIBLES de la capa (alfa > alfa_min, sin el halo tenue ni los márgenes
    transparentes del PNG): por cuadro único, recuadro de lo visible y si sale de y 220–1540 o de x ≤ 940 abajo.
    Revisa por componentes conexos (cada texto/gráfica por separado)."""
    from scipy import ndimage as nd
    out, vistos = [], {}
    for p in sorted(Path(capa_dir).glob('*.png')):
        ino = p.stat().st_ino
        n = int(p.stem)
        if ino in vistos:
            if vistos[ino]:
                out.append(dict(cuadro=n, igual_a=vistos[ino][0]['cuadro'], fuera=vistos[ino][0]['fuera']))
            continue
        a = np.asarray(Image.open(p))[..., 3] > alfa_min
        lab, k = nd.label(nd.binary_dilation(a[::2, ::2], iterations=6))
        malas = []
        for sl in nd.find_objects(lab):
            y0, y1, x0, x1 = sl[0].start * 2, sl[0].stop * 2, sl[1].start * 2, sl[1].stop * 2
            # se descuenta la dilatación de 12 px
            y0, y1, x0, x1 = y0 + 12, y1 - 12, x0 + 12, x1 - 12
            if y0 < C.ZONA['y_min'] or y1 > C.ZONA['y_max'] or (y1 > H / 2 and x1 > C.ZONA['x_max_abajo'] and x1 - x0 < 900):
                malas.append([x0, y0, x1, y1])
        rec = [dict(cuadro=n, fuera=malas)] if malas else []
        vistos[ino] = rec
        out += rec
    return out
