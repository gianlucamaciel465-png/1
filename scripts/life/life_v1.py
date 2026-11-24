#!/usr/bin/env python3
"""Roccé Life · V1 «Del piso» · receta del máster v01 (Pedro, 24/11/2026).

Guion aprobado: piezas/LIFE_rocce_life/V1_del_piso/01_fede_guion_G1.md (G1 v1, 10,000 s, 300 cuadros)
+ condiciones de Roma: 02_roma_aprobacion_G1.md.

Usa scripts/fmt/video.py, scripts/fmt/fmt03.py y scripts/fmt/sonido.py SIN modificarlos (se importan). La placa de cierre
usa el CSS de scripts/life/pines.py (importado, sin tocarlo) y una copia propia de render.js con fondo transparente
(life_v1_render.js). Intermedios en TRABAJO/life/v1/.

Etapas (cada una por separado, con nice -n 10; python = /home/user/1/TRABAJO/venv/bin/python):
  hojas    -> hojas cada cuadro / cada 0,1 s de los tramos críticos (cuadro y tiempo de la FUENTE impresos)
  medir    -> validaciones de fuente con numpy (contacto con la arena, pelo, antebrazo, dedo, cielo)
  planos   -> sub-planos (plano_n / plano_z) + unión (300 cuadros)
  color    -> medición B−R de la Blanca por toma y neutralización por cuadro (solo neutros claros de la Blanca)
  placa    -> PNG transparentes 1080×1920 de la frase y la firma (Chromium, omitBackground)
  audio    -> mezcla completa y sin música (−14 LUFS, pico ≤ −1 dBTP)
  master   -> textos (libass) + placa (overlays por cuadro) + codificación de los dos MP4
  control  -> evidencia (hoja, cortes ±1, validaciones §8, color, sonoridad, ffprobe, md5)
  entregar -> EXPORTACIONES/ + carpeta de la pieza + evidencia_v01, verificación de copias
"""
import json, math, os, shutil, subprocess, sys, hashlib, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/life')
import video as V        # noqa: E402
import fmt03 as U        # noqa: E402

R = Path('/home/user/1')
T = R / 'TRABAJO/life/v1'
HJ = T / 'hojas'
P = T / 'planos'
FONT = U.FONT
FPS, W, H = 30, 1080, 1920
NF = 300
DUR = NF / FPS
PIEZA = Path('/mnt/project-files/piezas/LIFE_rocce_life/V1_del_piso')
EXP = R / 'EXPORTACIONES'
NOMBRES = {'completa': 'ROCCE_LIFE_V1_DEL_PISO_v01.mp4', 'sinmusica': 'ROCCE_LIFE_V1_DEL_PISO_SINMUSICA_v01.mp4'}
EVID = T / 'evidencia_v01'


def nice(cmd):
    return ['nice', '-n', '10', *cmd]


# --- entorno compartido con V2 (4 CPU): nice -n 10 y 2 hilos en cada FFmpeg. video.py y fmt03.py NO se modifican: se
#     envuelve V.sh en memoria (inserta -threads 2 -filter_threads 2 para el decodificador y los filtros) y se agrega
#     -threads 2 a los intermedios (V.ENC_INT, lista del módulo leída en cada llamada).
_sh_orig = V.sh
THR = ['-threads', '2']


def _sh2(cmd, **kw):
    if isinstance(cmd, list) and cmd and cmd[0] == 'ffmpeg':
        cmd = ['nice', '-n', '10', 'ffmpeg', '-threads', '2', '-filter_threads', '2', *cmd[1:]]
    return _sh_orig(cmd, **kw)


V.sh = _sh2
if '-threads' not in V.ENC_INT:
    V.ENC_INT = V.ENC_INT + THR


def run(cmd):
    if cmd and cmd[0] == 'ffmpeg':
        cmd = ['nice', '-n', '10', 'ffmpeg', '-threads', '2', '-filter_threads', '2', *cmd[1:]]
    return U.run(cmd)


# =====================================================================================================
# etapa hojas · §6 del guion: hojas antes del render
# =====================================================================================================
def etapa_hojas():
    HJ.mkdir(parents=True, exist_ok=True)
    hs = U.hoja_src
    # 7999 1,4–2,5 (c42–c75): cuadro entero cada 3 (pelo arriba) y la caja del guion cada cuadro (contacto)
    hs('IMG_7999', 42, 75, HJ / '7999_c42-c75_entero_c3.jpg', cada=3, ancho=240, cols=12)
    hs('IMG_7999', 45, 72, HJ / '7999_c45-c72_caja_c1.jpg', cada=1, ancho=200, cols=14, caja=(120, 420, 1920, 3413))
    hs('IMG_7999', 40, 75, HJ / '7999_c40-c75_arriba_c1.jpg', cada=1, ancho=300, cols=9, caja=(0, 0, 2160, 900))
    # 7996 3,2–3,5 (c96–c105) y todo el tramo usado 3,3–5,1 (c99–c153) cada 3 (cara / pelo / quién tira)
    hs('IMG_7996', 96, 106, HJ / '7996_c96-c106_c1.jpg', cada=1, ancho=240, cols=11)
    hs('IMG_7996', 99, 153, HJ / '7996_c99-c153_c3.jpg', cada=3, ancho=200, cols=10)
    # 3375 0,0–1,3 (c0–c39) cada cuadro, entero (antebrazo)
    hs('IMG_3375', 0, 39, HJ / '3375_c0-c39_c1.jpg', cada=1, ancho=180, cols=14)
    # 4625 1,8–3,9 (c54–c117) cada 3
    hs('IMG_4625', 54, 117, HJ / '4625_c54-c117_c3.jpg', cada=3, ancho=180, cols=11)
    # 8002 0,0–1,2 (c0–c36) cada cuadro
    hs('IMG_8002', 0, 36, HJ / '8002_c0-c36_c1.jpg', cada=1, ancho=200, cols=13)
    # 4641 todos los cuadros (c0–c119), entero cada 3 y la esquina inferior izquierda cada cuadro (dedo)
    hs('IMG_4641', 0, 119, HJ / '4641_c0-c119_c3.jpg', cada=3, ancho=150, cols=14)
    hs('IMG_4641', 0, 119, HJ / '4641_esquina_inf_izq_c0-c119_c1.jpg', cada=1, ancho=150, cols=15, caja=(0, 1520, 400, 400))


# =====================================================================================================
# etapa planos · tabla §2 del guion (cuadros fijados con las hojas y las mediciones de la etapa medir)
# =====================================================================================================
def plano_z(toma, n0, zs, cxs, cys, salida, caja=None, post=None):
    """= fmt03.plano_z (acercamiento real cuadro a cuadro, recorte subpíxel + Lanczos sobre Y, U, V en yuv444p), copiado
    para agregar -threads 2 / -filter_threads 2 (entorno compartido). Sin grano."""
    from PIL import Image
    nw, nh = V.TOMAS[toma]['nat']
    x0, y0, cw, ch = caja or (0, 0, nw, nh)
    nf = len(zs)
    cxs = cxs if isinstance(cxs, (list, tuple)) else [cxs] * nf
    cys = cys if isinstance(cys, (list, tuple)) else [cys] * nf
    d = U.desde_cuadro(toma, n0)
    dec = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', '2', '-filter_threads', '2',
                            '-ss', f'{d:.4f}', '-i', str(V._src(toma)), '-t', f'{nf / FPS + 0.2:.4f}', '-an', '-vf',
                            V.color(toma) + f',fps={FPS},format=yuv444p', '-frames:v', str(nf), '-f', 'rawvideo',
                            '-pix_fmt', 'yuv444p', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv444p',
                            '-s', f'{W}x{H}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-i', '-', '-filter_threads', '2',
                            *(['-vf', post] if post else []), *V.ENC_INT, str(salida)], stdin=subprocess.PIPE)
    fs = nw * nh * 3
    ventanas = []
    for k in range(nf):
        b = dec.stdout.read(fs)
        if len(b) < fs:
            break
        fr = np.frombuffer(b, np.uint8).reshape(3, nh, nw)
        Z = max(1.0, round(zs[k], 6)); w, h = cw / Z, ch / Z
        x = min(max(cxs[k] - w / 2, x0), x0 + cw - w); y = min(max(cys[k] - h / 2, y0), y0 + ch - h)
        ventanas.append([round(Z, 4), round(x, 1), round(y, 1), round(w, 1), round(h, 1)])
        out = np.empty((3, H, W), np.uint8)
        for c in range(3):
            out[c] = np.asarray(Image.fromarray(fr[c]).resize((W, H), Image.LANCZOS, box=(x, y, x + w, y + h)))
        enc.stdin.write(out.tobytes())
    dec.stdout.close(); dec.wait()
    enc.stdin.close(); enc.wait()
    if len(ventanas) != nf or enc.returncode:
        raise RuntimeError(f'plano_z {toma}: {len(ventanas)} cuadros de {nf}')
    return dict(toma=toma, n0=n0, cuadros=nf, salida=str(salida), caja=caja, ventanas=ventanas, post=post)


def ease(a, b, n_ease, n_tot):
    """§2: Z(k) = Zf + (Zi − Zf)·(1 − k/(N−1))² en los primeros N cuadros; después Zf."""
    return [b + (a - b) * (1 - k / (n_ease - 1)) ** 2 if k < n_ease else b for k in range(n_tot)]


def blur_cuadros(spec):
    """desenfoques por cuadro del plano: [(k, sizeX, sizeY), ...] → cadena de avgblur con enable por número de cuadro."""
    return ','.join(f"avgblur=sizeX={sx}:sizeY={sy}:enable='eq(n\\,{k})'" for k, sx, sy in spec)


# 1a · DESVÍO medido (etapa medir, 7999_pelo_*.json): con la caja del guion (120, 420, 1920, 3413) el pelo de quien tira
# entra en c48–c52 de la fuente (punta más baja y 577 en c51, x 380–760). Caja 9:16 que arranca en y 624 (47 px debajo
# de la punta) y llega al borde inferior de la toma: (176, 624, 1809, 3216), centrada en el mismo x 1080 (acercamiento
# 1,06× sobre la caja del guion). La cola de 1a sigue terminando 3 cuadros antes del contacto (c65; contacto c68).
CAJA_1A = (176, 624, 1809, 3216)
# 2 · DESVÍO medido (etapa medir, 3375_estampado_bbox_c0-c40.json y medición sobre el plano renderizado): en la fuente
# c6–c12 (el tramo del guion empieza en c6 = 0,200 s) el estampado llega a x 16–41 de la toma: ninguna ventana (ni a Z 1,0)
# le deja 30 px de margen a la izquierda, y la ventana del guion (x 100→249 a Z 1,3) corta «so» y la «R» en c72–c84.
# En c14–c15 el movimiento de cámara estira el estampado (desenfoque) y a Z 1,3 no entra con 30 px por lado (medido
# 20/35 px en c15). Se usa c16–c42 (0,533–1,400 s, 27 cuadros) a Z 1,3 fijo y cy 889 como el guion, con la ventana que
# centra el estampado (medido con desenfoque) mientras se mueve: x 103 → 249 en 7 cuadros y después 249 (= borde derecho de
# la toma), donde el tatuaje (x < 140 desde c30) y la muñeca quedan afuera. Control: márgenes y tatuaje medidos en el plano.
X2 = [102.8, 125.0, 145.0, 170.0, 195.0, 220.0, 240.0] + [249.0] * 20
CX2 = [x + 1080 / 1.3 / 2 for x in X2]
N0_2 = 16


def lista_planos():
    return [
        # id, cuadros del máster, tipo, args
        ('1a', (0, 17), 'n', dict(toma='IMG_7999', n0=48, nf=18, caja=CAJA_1A)),                   # 1,600–2,200
        ('1b', (18, 71), 'n', dict(toma='IMG_7996', n0=99, nf=54, caja=(0, 0, 2160, 3840))),       # 3,300–5,100
        ('2', (72, 98), 'z', dict(toma='IMG_3375', n0=N0_2, zs=[1.3] * 27, cxs=CX2, cys=889,       # 0,533–1,400
                                  post=blur_cuadros([(24, 1, 12), (25, 1, 24), (26, 1, 36)]))),
        ('3', (99, 161), 'z', dict(toma='IMG_4625', n0=54, zs=ease(1.5, 1.0, 12, 63), cxs=540,     # 1,800–3,900
                                   cys=ease(1280, 960, 12, 63),
                                   post=blur_cuadros([(0, 1, 30), (1, 1, 20), (2, 1, 10)]))),
        ('4', (162, 197), 'z', dict(toma='IMG_8002', n0=0, zs=ease(3.0, 1.0, 12, 36),             # 0,000–1,200 (4a+4b)
                                    cxs=ease(400, 1080, 12, 36), cys=ease(3300, 1920, 12, 36),
                                    post=blur_cuadros([(0, 1, 36), (1, 1, 24), (2, 1, 12), (3, 1, 6),
                                                       (33, 12, 12), (34, 12, 12), (35, 12, 12)]))),
        ('5', (198, 299), 'z', dict(toma='IMG_4641', n0=17, zs=ease(1.8, 1.1, 12, 102),           # 0,567–3,967
                                    cxs=ease(560, 540, 12, 102), cys=ease(950, 873, 12, 102))),
    ]


def etapa_planos():
    P.mkdir(parents=True, exist_ok=True)
    reg = []
    for pid, (m0, m1), tipo, a in lista_planos():
        out = P / f'{pid}.mp4'
        if tipo == 'n':
            p = U.plano_n(a['toma'], a['n0'], a['nf'], out, caja=a.get('caja'), post=a.get('post'))
        else:
            p = plano_z(a['toma'], a['n0'], a['zs'], a['cxs'], a['cys'], out, caja=a.get('caja'), post=a.get('post'))
        assert p['cuadros'] == m1 - m0 + 1, (pid, p['cuadros'])
        p.update(id=pid, master=[m0, m1], fuente_s=[round(U.desde_cuadro(a['toma'], a['n0']) + 0.0005, 4)])
        reg.append(p); print(pid, p['cuadros'], flush=True)
    n = V.unir(reg, T / 'life_v1_base.mp4')
    json.dump(dict(cuadros=n, planos=reg), open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1)
    print('total', n)


# =====================================================================================================
# etapa color · condición 3 de Roma: Blanca neutra (B−R de la tela lisa por toma; PRODUCTO ≈ +1) y 3375 contra 4625
# =====================================================================================================
BASE = T / 'life_v1_base.mp4'            # montaje (intermedios x264 crf 12)
BASE2 = T / 'life_v1_base_color.mp4'     # + neutralización de la Blanca (x264 sin pérdida)
TOMA_DE = {}                              # cuadro del máster → toma
for _pid, (_a, _b), _t, _d in lista_planos():
    for _n in range(_a, _b + 1):
        TOMA_DE[_n] = _d['toma']
# cuadros de medición (máster) y caja donde buscar la Blanca (x0, y0, x1, y1 en el máster)
MEDIR = {
    'IMG_7999': dict(cuadros=[2, 8, 14], caja=(0, 200, 1080, 1920)),   # arriba: espuma del mar (blanca y más grande)
    'IMG_7996': dict(cuadros=[22, 40, 58, 70], caja=(0, 0, 1080, 1920)),
    'IMG_3375': dict(cuadros=[76, 84, 92], caja=(0, 0, 1080, 1920)),
    'IMG_4625': dict(cuadros=[112, 130, 150], caja=(0, 560, 1080, 1760)),
    'IMG_8002': dict(cuadros=[172, 180, 190], caja=(0, 600, 1080, 1920)),
    'IMG_4641': dict(cuadros=[212, 250, 290], caja=(0, 800, 1080, 1800)),
}
FRANJAS_L = [(150, 190), (190, 215), (215, 256)]
UMBRAL_FRIO = 4.0         # B−R de la tela > +4 → se corrige (PRODUCTO ≈ +1); |B−R(3375) − B−R(4625)| > 6 → se iguala


def yuv_a_rgb(b):
    """cuadro yuv420p (bytes, rango limitado BT.709) → RGB float (0–255), como vir01_v02.yuv_rgb."""
    ny = W * H
    Y = np.frombuffer(b, np.uint8, ny).reshape(H, W).astype(np.float32)
    Cb = np.frombuffer(b, np.uint8, ny // 4, ny).reshape(H // 2, W // 2).astype(np.float32)
    Cr = np.frombuffer(b, np.uint8, ny // 4, ny + ny // 4).reshape(H // 2, W // 2).astype(np.float32)
    cb = np.repeat(np.repeat(Cb, 2, 0), 2, 1); cr = np.repeat(np.repeat(Cr, 2, 0), 2, 1)
    y = (Y - 16) / 219; u = (cb - 128) / 224; v = (cr - 128) / 224
    Rr = y + 1.5748 * v; Bb = y + 1.8556 * u; Gg = (y - 0.2126 * Rr - 0.0722 * Bb) / 0.7152
    return np.stack([Rr, Gg, Bb], -1) * 255.0


def rgb_a_yuv(rgb):
    r, g, b = rgb[..., 0] / 255, rgb[..., 1] / 255, rgb[..., 2] / 255
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Cb = 128 + 224 * (b - y) / 1.8556; Cr = 128 + 224 * (r - y) / 1.5748
    Cb = Cb.reshape(H // 2, 2, W // 2, 2).mean((1, 3)); Cr = Cr.reshape(H // 2, 2, W // 2, 2).mean((1, 3))
    Y = 16 + 219 * y
    return np.concatenate([Y.ravel(), Cb.ravel(), Cr.ravel()]).round().clip(0, 255).astype(np.uint8).tobytes()


def lum_sat(a):
    c = np.clip(a, 0, 255)
    L = c @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    mx, mn = c.max(-1), c.min(-1)
    return L, (mx - mn) / (mx + 1)


def leer_cuadro(src, n):
    r = run(['ffmpeg', '-v', 'error', '-i', str(src), '-vf', f"select='eq(n\\,{n})'", '-fps_mode', 'passthrough',
             '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'])
    return yuv_a_rgb(r)


def mascara_amplia(rgb, L, sat):
    """tela blanca al sol y a la sombra: clara (L > 100), poco saturada (sat < 0,25) y no cálida (B ≥ R − 3): la arena,
    las rocas, los troncos y la piel (R > B) y el cielo saturado quedan afuera."""
    return (L > 100) & (sat < 0.25) & (rgb[..., 2] >= rgb[..., 0] - 3)


def blob_blanca(rgb, L, sat, caja, prev=None, amplia=True):
    """la Blanca = componente conexo de la máscara dentro de la caja: el de mayor superposición con la del cuadro
    anterior (el primero: el más grande). amplia=False: criterio de pines.neutralizar (L > 150, sat < 0,12)."""
    from scipy import ndimage as ndi
    x0, y0, x1, y1 = caja
    m = np.zeros(L.shape, bool); m[y0:y1, x0:x1] = True
    base = mascara_amplia(rgb, L, sat) if amplia else (L > 150) & (sat < 0.12)
    lab, n = ndi.label(m & base, structure=np.ones((3, 3)))
    if n == 0:
        return None
    if prev is not None:
        sup = ndi.sum(prev, lab, index=np.arange(1, n + 1))
        if sup.max() > 0:
            return lab == (1 + int(np.argmax(sup)))
    tam = ndi.sum(np.ones(L.shape), lab, index=np.arange(1, n + 1))
    return lab == (1 + int(np.argmax(tam)))


FRANJAS_G = [(100, 130), (130, 150), (150, 190), (190, 215), (215, 256)]   # franjas para las ganancias (sol y sombra)


def _franjas(rgb, L, m, franjas, minimo=3000):
    out = []
    for lo, hi in franjas:
        mm = m & (L >= lo) & (L < hi)
        if mm.sum() < minimo:
            continue
        md = np.median(rgb[mm], 0)
        out.append(dict(L=[lo, hi], L_centro=round(float(np.median(L[mm])), 1), rgb=[round(float(v), 1) for v in md],
                        b_menos_r=round(float(md[2] - md[0]), 1), g_menos_r=round(float(md[1] - md[0]), 1),
                        n=int(mm.sum())))
    return out


def _med(rgb, m):
    md = np.median(rgb[m], 0)
    return dict(rgb=[round(float(v), 1) for v in md], b_menos_r=round(float(md[2] - md[0]), 1),
                g_menos_r=round(float(md[1] - md[0]), 1), n=int(m.sum()))


def medir_tela(rgb, blob, blob_lisa=None):
    """«tela» = tela lisa al sol (criterio de pines: componente de L > 150 y sat < 0,12 → blob_lisa); «sombra» =
    100 < L ≤ 150 dentro de la Blanca (blob amplio). Franjas para las ganancias: tela del blob amplio sin letras (sat < 0,12
    si L > 150; sat < 0,22 si L ≤ 150: el celeste del estampado, sat 0,17–0,4, y el negro quedan afuera), en dos vueltas
    (la segunda solo con lo que queda neutro, sat < 0,08, con la ganancia de la primera)."""
    L, sat = lum_sat(rgb)
    out = {}
    lisa = (blob_lisa if blob_lisa is not None else blob) & (L > 150) & (sat < 0.12)
    sombra = blob & (L > 100) & (L <= 150) & (sat < 0.22)
    out['tela'] = _med(rgb, lisa) if lisa.sum() > 500 else None
    out['sombra'] = _med(rgb, sombra) if sombra.sum() > 500 else None
    m = blob & (L > 100) & (((L > 150) & (sat < 0.12)) | ((L <= 150) & (sat < 0.22)))
    f1 = _franjas(rgb, L, m, FRANJAS_G)
    if f1:
        cent = np.array([f['L_centro'] for f in f1]); rr = np.array([f['rgb'] for f in f1])
        gan = (rr @ np.array([0.2126, 0.7152, 0.0722]))[:, None] / rr
        G = np.stack([np.interp(L, cent, gan[:, k]) for k in range(3)], -1)
        _, sat_c = lum_sat(rgb * G)
        m = m & (sat_c < 0.08)
    out['franjas'] = _franjas(rgb, L, m, FRANJAS_G)
    return out


def producto_ref():
    from PIL import Image
    S = T / 'ctrl'; S.mkdir(parents=True, exist_ok=True)
    res = {}
    for nom in ('blanca_espalda_estudio', 'blanca_frente_estudio', 'blanca_frente_detalle_estampado'):
        V.foto_srgb(R / 'PRODUCTO' / f'{nom}.jpg', S / f'{nom}_srgb.png')
        a = np.asarray(Image.open(S / f'{nom}_srgb.png').convert('RGB'), np.float32)
        L, sat = lum_sat(a)
        from scipy import ndimage as ndi
        lab, n = ndi.label((L > 150) & (sat < 0.12), structure=np.ones((3, 3)))
        tam = ndi.sum(np.ones(L.shape), lab, index=np.arange(1, n + 1))
        blob = lab == (1 + int(np.argmax(tam)))
        res[nom] = _med(a, blob)
    return res


def ganancias(med):
    """ganancia por franja de L (mediana de los cuadros de medición) = luma / canal: lleva la tela a neutro conservando
    la luma (pines.neutralizar)."""
    acc = {}
    for m in med:
        for f in m['franjas']:
            acc.setdefault(tuple(f['L']), []).append((f['L_centro'], f['rgb'], f['n']))
    cent, gan = [], []
    for k in sorted(acc):
        v = acc[k]
        w = np.array([x[2] for x in v], float)
        rgb = (np.array([x[1] for x in v]) * w[:, None]).sum(0) / w.sum()
        y = float(rgb @ np.array([0.2126, 0.7152, 0.0722]))
        cent.append(float(np.average([x[0] for x in v], weights=w))); gan.append((y / rgb).tolist())
    return np.array(cent), np.array(gan)


def corregir(rgb, blob, cent, gan):
    """ganancia por L (interpolada entre las franjas) aplicada solo a lo que queda neutro con esa ganancia
    (w = clip((0,12 − sat_corregida)/0,05), criterio de vir01_v02) y claro (rampa suave de L 95 → 120), y solo sobre la
    Blanca (blob ensanchado 8 px, borde suavizado 3 px): el celeste y el negro del estampado, la arena, las rocas, la piel
    y el cielo quedan iguales."""
    from scipy import ndimage as ndi
    from PIL import Image, ImageFilter
    L, sat = lum_sat(rgb)
    g = np.stack([np.interp(L, cent, gan[:, k]) for k in range(3)], -1)
    ss = lambda x: (lambda c: c * c * (3 - 2 * c))(np.clip(x, 0, 1))
    _, sat_c = lum_sat(rgb * g)
    w = np.clip((0.12 - sat_c) / 0.05, 0, 1) * ss((L - 95) / 25)
    dentro = ndi.binary_dilation(blob, iterations=8)
    borde = np.asarray(Image.fromarray((dentro * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    w = w * borde
    return rgb * (1 + w[..., None] * (g - 1)), w


def etapa_color():
    C = T / 'color'; C.mkdir(parents=True, exist_ok=True)
    rep = dict(metodo=('Medición: mediana RGB (BT.709 desde el YUV de rango limitado del montaje) de la Blanca = componente '
                       'conexo de tela clara, poco saturada y no cálida (L > 100, sat < 0,25, B ≥ R − 3) dentro de la caja de '
                       'la toma (el de mayor superposición con el cuadro anterior). «tela» = tela lisa al sol (L > 150, '
                       'sat < 0,12, criterio de pines); «sombra» = 100 < L ≤ 150. La toma se corrige si la mediana de B−R de '
                       f'la tela lisa al sol supera +{UMBRAL_FRIO:g} (PRODUCTO ≈ +1). 3375 se compara con 4625 ya '
                       'corregida (aprobación de Roma: igualar si la diferencia supera 6). Corrección por cuadro: ganancia '
                       'por franja de L (100–130, 130–150, 150–190, 190–215, 215–256; luma/canal, conserva la luma) medida '
                       'en la tela del cuadro en dos vueltas (la segunda sin lo que no queda neutro: letras), promedio '
                       'temporal 0,5; se aplica solo donde el píxel queda neutro con esa ganancia (sat corregida < 0,07 '
                       'entera, nada desde 0,12), con rampa de L 95 → 120, y solo sobre la Blanca (blob ensanchado 8 px, '
                       'borde 3 px).'),
               producto=producto_ref(), tomas={})
    print('PRODUCTO', json.dumps(rep['producto'], ensure_ascii=False), flush=True)
    MED = {}
    for toma, c in MEDIR.items():
        filas = []
        for n in c['cuadros']:
            rgb = leer_cuadro(BASE, n); L, sat = lum_sat(rgb)
            b = blob_blanca(rgb, L, sat, c['caja'])
            bz = blob_blanca(rgb, L, sat, c['caja'], amplia=False)
            filas.append(dict(cuadro=n, **medir_tela(rgb, b, bz)))
        MED[toma] = filas
        sol = [f['tela']['b_menos_r'] for f in filas if f['tela']]; som = [f['sombra']['b_menos_r'] for f in filas if f['sombra']]
        rep['tomas'][toma] = dict(caja=c['caja'], antes=filas,
                                  b_menos_r_mediana_antes=round(float(np.median(sol)), 1) if sol else None,
                                  b_menos_r_sombra_mediana_antes=round(float(np.median(som)), 1) if som else None)
        print(toma, 'B−R sol', sol, 'sombra', som, 'franjas', [[x['b_menos_r'] for x in f['franjas']] for f in filas], flush=True)
    # decisión por toma: fría si B−R > UMBRAL_FRIO. 3375 se compara con 4625 YA corregida (≈ neutra): si 3375 no está
    # fría queda como está (corregir una toma que ya mide como PRODUCTO la entibia) y se controla la diferencia después.
    corr = {t for t in MEDIR if (rep['tomas'][t]['b_menos_r_mediana_antes'] or -99) > UMBRAL_FRIO}
    rep['decision'] = {t: ('corrige' if t in corr else 'queda') for t in MEDIR}
    G = {t: ganancias(MED[t]) for t in corr}
    for t in corr:
        rep['tomas'][t]['ganancias_por_L_toma'] = dict(L_centro=[round(x, 1) for x in G[t][0]],
                                                       ganancias=np.round(G[t][1], 4).tolist())
    print('decisión', rep['decision'], flush=True)
    # corrección cuadro a cuadro (x264 -qp 0). Ganancias por cuadro: mediana RGB de la tela del cuadro por franja de L
    # (si la franja tiene ≥ 3000 px), promedio temporal 0,5 con el cuadro anterior de la misma toma; franjas sin tela →
    # ganancias de la toma (cuadros de medición).
    ny = W * H; fsz = ny * 3 // 2
    dec = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', '2', '-i', str(BASE), '-f', 'rawvideo',
                            '-pix_fmt', 'yuv420p', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p',
                            '-s', f'{W}x{H}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-i', '-', '-c:v', 'libx264', '-qp', '0',
                            '-preset', 'veryfast', '-threads', '2', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', str(BASE2)],
                           stdin=subprocess.PIPE)
    prev = {}; prev_rgb = {}; tocados = {}; gan_cuadro = {}; k = 0
    while True:
        b = dec.stdout.read(fsz)
        if len(b) < fsz:
            break
        t = TOMA_DE[k]
        if t in corr:
            rgb = yuv_a_rgb(b); L, sat = lum_sat(rgb)
            bl = blob_blanca(rgb, L, sat, MEDIR[t]['caja'], prev.get(t))
            if bl is not None:
                prev[t] = bl
                mt = medir_tela(rgb, bl)
                pr = prev_rgb.setdefault(t, {})
                cent_t, gan_t = G[t]
                cent, gan = [], []
                for lo, hi in FRANJAS_G:
                    f = [x for x in mt['franjas'] if x['L'] == [lo, hi]]
                    if f:
                        c_rgb = np.array(f[0]['rgb'])
                        if (lo, hi) in pr:
                            c_rgb = 0.5 * c_rgb + 0.5 * pr[(lo, hi)][1]
                        pr[(lo, hi)] = (f[0]['L_centro'], c_rgb)
                        y = float(c_rgb @ np.array([0.2126, 0.7152, 0.0722]))
                        cent.append(f[0]['L_centro']); gan.append(y / c_rgb)
                    else:
                        pr.pop((lo, hi), None)
                        i_t = [i for i, cc in enumerate(cent_t) if lo <= cc < hi]
                        if i_t:
                            cent.append(cent_t[i_t[0]]); gan.append(gan_t[i_t[0]])
                o = np.argsort(cent); cent = np.array(cent)[o]; gan = np.array(gan)[o]
                rgb2, w = corregir(rgb, bl, cent, gan)
                b = rgb_a_yuv(rgb2)
                tocados[k] = round(float((w > 0.01).mean() * 100), 1)
                gan_cuadro[k] = dict(L=[round(float(x), 1) for x in cent], g=np.round(gan, 4).tolist())
        enc.stdin.write(b); k += 1
    rep['ganancias_por_cuadro'] = gan_cuadro
    dec.stdout.close(); dec.wait(); enc.stdin.close(); enc.wait()
    assert k == NF and enc.returncode == 0, (k, enc.returncode)
    rep['pct_pixeles_tocados_por_cuadro'] = tocados
    # después (mismos cuadros, mismo blob del cuadro de antes)
    for toma, c in MEDIR.items():
        filas = []
        for n in c['cuadros']:
            a = leer_cuadro(BASE, n); d = leer_cuadro(BASE2, n)
            La, sa = lum_sat(a); bl = blob_blanca(a, La, sa, c['caja']); bz = blob_blanca(a, La, sa, c['caja'], amplia=False)
            mt = medir_tela(d, bl, bz)
            # celeste del estampado (dentro de la Blanca) y cambio del resto de la imagen
            from scipy import ndimage as ndi
            cerca = ndi.binary_dilation(bl, iterations=12)
            cel = cerca & (a[..., 2] - a[..., 0] > 25) & (La > 90) & (sa > 0.15) & (sa < 0.45)
            dif = np.abs(np.clip(d, 0, 255) - np.clip(a, 0, 255)).max(-1)
            fuera = ~ndi.binary_dilation(bl, iterations=12)
            filas.append(dict(cuadro=n, tela_despues=mt['tela'], sombra_despues=mt['sombra'], franjas_despues=mt['franjas'],
                              celeste_px=int(cel.sum()),
                              celeste_b_sobre_r_antes=round(float(np.median(a[cel][:, 2] / np.maximum(a[cel][:, 0], 1))), 3) if cel.sum() > 500 else None,
                              celeste_b_sobre_r_despues=round(float(np.median(d[cel][:, 2] / np.maximum(d[cel][:, 0], 1))), 3) if cel.sum() > 500 else None,
                              fuera_de_la_blanca_dif_max=round(float(dif[fuera].max()), 2),
                              pct_pixeles_cambio_mayor_2_niveles=round(float((dif > 2).mean() * 100), 1)))
        rep['tomas'][toma]['despues'] = filas
        print(toma, 'después B−R sol', [(f['tela_despues'] or {}).get('b_menos_r') for f in filas],
              'sombra', [(f['sombra_despues'] or {}).get('b_menos_r') for f in filas],
              'celeste', [(f['celeste_b_sobre_r_antes'], f['celeste_b_sobre_r_despues']) for f in filas],
              'fuera máx', [f['fuera_de_la_blanca_dif_max'] for f in filas], flush=True)
    def _md(t, k):
        v = [f[k]['b_menos_r'] for f in rep['tomas'][t]['despues'] if f[k]]
        return round(float(np.median(v)), 1) if v else None
    rep['b_menos_r_mediana_despues'] = {t: dict(sol=_md(t, 'tela_despues'), sombra=_md(t, 'sombra_despues')) for t in MEDIR}
    rep['dif_3375_vs_4625_despues'] = round(_md('IMG_3375', 'tela_despues') - _md('IMG_4625', 'tela_despues'), 1)
    rep['iguala_3375'] = abs(rep['dif_3375_vs_4625_despues']) > 6
    print('después (mediana)', rep['b_menos_r_mediana_despues'], '3375−4625', rep['dif_3375_vs_4625_despues'], flush=True)
    json.dump(rep, open(C / 'color_v01.json', 'w'), ensure_ascii=False, indent=1)
    hoja_color(corr)


def hoja_color(corr):
    """antes / después a 1:3 de un cuadro por toma + PRODUCTO."""
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 22)
    filas = []
    for toma, c in MEDIR.items():
        n = c['cuadros'][len(c['cuadros']) // 2]
        par = []
        for nom, src in (('antes', BASE), ('después', BASE2)):
            im = Image.fromarray(np.clip(leer_cuadro(src, n), 0, 255).round().astype(np.uint8)).resize((360, 640))
            d = ImageDraw.Draw(im); d.rectangle([0, 0, 359, 30], fill=(0, 0, 0))
            d.text((6, 3), f"{toma[4:]} c{n} {nom}{'' if toma in corr else ' (sin cambio)'}", font=fnt, fill=(255, 255, 0))
            par.append(im)
        filas.append(par)
    prod = Image.open(T / 'ctrl' / 'blanca_espalda_estudio_srgb.png').convert('RGB')
    prod = prod.resize((round(640 * prod.width / prod.height), 640))
    d = ImageDraw.Draw(prod); d.rectangle([0, 0, 300, 30], fill=(0, 0, 0)); d.text((6, 3), 'PRODUCTO Blanca', font=fnt, fill=(255, 255, 0))
    hoja = Image.new('RGB', (3 * 364 + max(prod.width, 364), 2 * 644 * 2), (30, 30, 30))
    for i, (a, b) in enumerate(filas):
        x = (i % 3) * 364 * 1; y = (i // 3) * 1288
        hoja.paste(a, (x, y)); hoja.paste(b, (x, y + 644))
    hoja.paste(prod, (3 * 364, 0))
    (T / 'color').mkdir(exist_ok=True)
    hoja.save(T / 'color' / 'color_antes_despues_v01.jpg', quality=88)


# =====================================================================================================
# etapa placa · cierre en el sistema de los pines v02 (CSS de scripts/life/pines.py, sin tocarlo)
# =====================================================================================================
PL = T / 'placa'
FRASE_HTML = 'Guardalo para el<br><em>próximo</em> no.'     # «Guardalo para el\N*próximo* no.» (cursiva solo de estilo)
FRASE_TXT = 'Guardalo para el próximo no.'
FIRMA_TXT = 'ROCCÉ LIFE'
PLACA = dict(fs=92, lh='1.03', top_frase=290, logo=96, ffs=30, top_firma=520,
             grad=(820, 0.62, (12, 18, 26)))                 # degradé arriba: rgb(12,18,26) α 0,62 → 0 en y 820 (pines)
OV_FRASE = (210, 299)                                         # cuadros del máster (inclusive)
OV_FIRMA = (216, 299)


def etapa_placa():
    import pines
    PL.mkdir(parents=True, exist_ok=True)
    t = dict(F=pines.F, W=W, H=H, mx=72, color='#FFFFFF', fs=PLACA['fs'], lh=PLACA['lh'], acento='#CDDDE5',
             logo=PLACA['logo'], ffs=PLACA['ffs'], radio=round(PLACA['logo'] * 0.11), fcolor='rgba(255,255,255,.92)',
             sombra='0 2px 24px rgba(0,0,0,.28)', sombra_f='0 1px 8px rgba(0,0,0,.35)')
    css = pines.CSS % t + 'html,body{background:transparent !important}' \
        '.firma{left:0;right:0;justify-content:center}.firma span{margin-right:-.34em}'
    alto, op, (r, g, b) = PLACA['grad']
    grad = (f'<div class="grad" style="top:0;height:{alto}px;background:linear-gradient(to bottom,'
            f'rgba({r},{g},{b},{op}) 0%,rgba({r},{g},{b},{op * 0.55:.3f}) 45%,rgba({r},{g},{b},0) 100%)"></div>')
    logo = R / 'LOGO' / 'rocce_logo.png'
    docs = {
        'cierre_frase': f'{grad}<div class="frase" style="top:{PLACA["top_frase"]}px;text-align:center">{FRASE_HTML}</div>',
        'cierre_firma': (f'<div class="firma" style="top:{PLACA["top_firma"]}px"><img src="file://{logo}">'
                         f'<span>{FIRMA_TXT}</span></div>'),
    }
    trabajos = []
    for nom, body in docs.items():
        h = PL / f'{nom}.html'
        h.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>',
                     encoding='utf-8')
        trabajos.append(dict(html=str(h), out=str(PL / f'{nom}.png'), w=W, h=H))
    j = PL / '_trabajos.json'; j.write_text(json.dumps(trabajos, indent=1))
    subprocess.run(['nice', '-n', '10', 'node', str(R / 'scripts/life/life_v1_render.js'), str(j)], check=True)
    from PIL import Image
    rep = {}
    for tr in trabajos:
        im = Image.open(tr['out']); a = np.asarray(im)
        assert im.size == (W, H) and im.mode == 'RGBA', (im.size, im.mode)
        al = a[..., 3]
        ys, xs = np.nonzero(al > 8)
        rep[Path(tr['out']).name] = dict(modo=im.mode, tam=im.size, bbox_alfa_mayor_8=[int(xs.min()), int(ys.min()),
                                                                                       int(xs.max()), int(ys.max())])
    # cajas: letras de la frase (blanco casi opaco) y logo
    a = np.asarray(Image.open(PL / 'cierre_frase.png').convert('RGBA')).astype(np.float32)
    letras = (a[..., 3] > 200) & (a[..., :3].min(-1) > 200)
    ys, xs = np.nonzero(letras)
    rep['frase_letras_bbox'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    f = np.asarray(Image.open(PL / 'cierre_firma.png').convert('RGBA')).astype(np.float32)
    op_ = f[..., 3] > 200
    ys, xs = np.nonzero(op_)
    rep['firma_bbox_opaco'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    # ficha del logo: el cuadrado de 96 px más claro (#FEFEFE)
    ficha = (f[..., 3] > 250) & (f[..., :3].min(-1) > 250)
    ys, xs = np.nonzero(ficha)
    rep['ficha_logo_bbox'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    rep['radio_px'] = t['radio']; rep['radio_pct'] = round(t['radio'] / PLACA['logo'] * 100, 1)
    json.dump(rep, open(PL / 'placa.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))


# =====================================================================================================
# etapa audio · guion §5, llamadas en el orden del guion (sonido.py sin tocar)
# =====================================================================================================
AU = T / 'audio'
WAV = {'completa': AU / 'mezcla_completa.wav', 'sinmusica': AU / 'mezcla_sinmusica.wav'}


def _base_sonido(m, S, sinmusica=False):
    """ambiente real + foley PROVISORIO. Semilla fija antes del foley: el roce de tela, los barridos y el toque salen
    idénticos (muestra por muestra) en la mezcla completa y en la sin música."""
    S.rng = np.random.default_rng(11)
    m.ambiente('IMG_7999', 1.600, 0.000, 0.600, -8, hp=200)
    m.ambiente('IMG_7996', 3.300, 0.600, 2.400, -6, hp=200, fin_fade=.05)
    if not sinmusica:
        m.ambiente('IMG_4625', 1.500, 3.000, 5.400, -6, ini_fade=.3, fin_fade=.05)   # 3375 casi sin audio (−73 dBFS)
    else:
        # desvío anotado (solo sin música): tal cual el guion quedaba silencio digital (−240 dBFS) de 2,80 a 3,00 s
        # (termina la tela de 2,40 y el ambiente de 4625 recién entra en 3,00). Se adelanta la entrada del mismo ambiente
        # a 2,60 s (fuente 1,100 s, sin golpes: −23 a −31 dBFS) con fundido de 0,7 s: llega a nivel pleno en 3,30 s, igual
        # que en el guion (3,00 + 0,3).
        m.ambiente('IMG_4625', 1.100, 2.600, 5.400, -6, ini_fade=.7, fin_fade=.05)
    m.ambiente('IMG_8002', 0.000, 5.400, 6.600, -10, hp=150)
    m.ambiente('IMG_4641', 0.567, 6.600, 10.000, -4, fin_fade=.3)
    m.tela(0.05, .45, .16)      # vuelo
    m.tela(0.60, .25, .14)      # cae
    m.tela(2.40, .40, .18)      # la levantan
    m.barrido(3.18, .25, .18)
    m.barrido(5.28, .30, .22)
    m.barrido(6.50, .25, .18)
    m.toque(6.60, .16, 2400)


def _charles(m, t0, t1, paso=0.3):
    k = 0
    while t0 + k * paso < t1 - 1e-6:
        m.charles(round(t0 + k * paso, 3)); k += 1


def _musica(m, S):
    S.rng = np.random.default_rng(23)
    # Entrada
    m.pad(0.0, [50, 53, 57], 2.3, .05, 900, a=.1)
    m.campana(0.0, 74, .05)
    m.bombo(0.6, .75, f0=90, f1=38); m.impacto(0.6, .28)
    m.ocho08(1.2, 38, .35, .35); m.ocho08(1.8, 38, .35, .35)
    m.subida(1.80, 2.35, .16)
    m.silenciar('mus', 2.33, 2.40)
    # Drop 1
    m.bombo(2.4, .95); m.impacto(2.4, .40)
    m.ocho08(2.4, 38, 1.0, .55, glide_desde=45)
    m.pad(2.4, [50, 53, 57, 62], 1.1, .06, 1400)
    m.campana(2.4, 81, .06)
    _charles(m, 2.4, 3.3)
    # 4625
    m.palma(3.0); m.bombo(3.6, .8); m.palma(4.2); m.bombo(4.8, .7)
    m.pad(3.3, [46, 50, 53], .9, .06, 1200); m.pad(4.2, [48, 52, 55], 1.1, .06, 1200)
    m.ocho08(3.6, 34, .5); m.ocho08(4.2, 36, .5); m.ocho08(4.8, 36, .4)
    _charles(m, 3.3, 4.8)
    m.redoble(4.8, 5.35, .12); m.subida(4.60, 5.35, .16)
    m.silenciar('mus', 5.35, 5.40)
    # Drop 2
    m.bombo(5.4, 1.0); m.impacto(5.4, .5)
    m.ocho08(5.4, 38, 1.1, .6, glide_desde=33)
    m.pad(5.4, [50, 54, 57, 62], 1.2, .07)
    m.campana(5.6, 78, .07)
    _charles(m, 5.4, 6.6); m.palma(6.0)
    m.subida(6.05, 6.55, .12)
    # Cierre
    m.bombo(6.6, .75); m.pad(6.6, [50, 54, 57], .6, .06); m.ocho08(6.6, 38, .5)
    m.bombo(7.2, .9); m.pad(7.2, [55, 59, 62], .6, .06); m.ocho08(7.2, 43, .5)
    m.bombo(7.8, .8); m.palma(7.8); m.pad(7.8, [57, 61, 64], .6, .06); m.ocho08(7.8, 45, .5)
    m.bombo(8.4, .9); m.pad(8.4, [50, 54, 57, 62], 1.1, .06, r=.6); m.campana(8.4, 74, .07, .9); m.ocho08(8.4, 38, 1.0, .5)
    m.fundido('mus', 9.50, 10.00)
    # desvío anotado: la reverberación de la música vive en la pista 'fx' (sonido.rev) y seguía sonando en 10,000 s;
    # mismo fundido 9,50–10,00 en 'fx' para que el final no corte una cola (el foley de 'fx' termina en 6,66 s).
    m.fundido('fx', 9.50, 10.00)


def etapa_audio():
    import sonido as S
    AU.mkdir(parents=True, exist_ok=True)
    rep = {}
    for nom in ('completa', 'sinmusica'):
        m = S.Mezcla(DUR)
        _base_sonido(m, S, sinmusica=(nom == 'sinmusica'))
        if nom == 'completa':
            _musica(m, S)
        I, Pk = m.exportar(str(WAV[nom]), lufs=-14.0)
        rep[nom] = dict(lufs=I, pico_dbtp=Pk, muestras=m.N)
        print(nom, I, Pk)
    # control: el foley de las dos mezclas es el mismo (pista fx de la sin música = fx de la completa antes de la música)
    json.dump(rep, open(AU / 'audio_v01.json', 'w'), ensure_ascii=False, indent=1)


# =====================================================================================================
# etapa textos · guion §2/§4 (libass, estilos de video.py) + medidas: mayúscula del hook, cajas dentro de y 270–1130
# =====================================================================================================
TX = T / 'textos'
ASS = TX / 'life_v1_textos.ass'
F_CAJA_HOOK, F_CAJA_PASO = r'\fs120\xbord33\ybord10', r'\fs104\xbord29\ybord9'
TEXTOS = [  # cuadros del máster inclusive; y = borde superior del texto (guion: ancla arriba al centro, x 540)
    dict(id='hook', c=(0, 41), txt=r'Te dijeron\Nque no.', estilo='CajaN', extra=F_CAJA_HOOK, pop=True, y=270),
    dict(id='pregunta', c=(42, 71), txt='¿Se queda ahí?', estilo='CajaN', extra=F_CAJA_PASO, pop=False, y=270),
    # desvío anotado: el guion pide c72–c107 (cruza el corte). En c99 (primer cuadro de 4625, Z 1,5, desenfocado) la caja
    # tapa la parte de arriba de «ROCCÉ» de la espalda y en c100–c101 pisa el cuello (control v01: 89 552 / 79 578 /
    # 25 351 px de la Blanca dentro de la caja). Guion §4: «Ningún texto va sobre un estampado». Termina con el corte (c98);
    # c99–c107 quedan sin texto y «Otra vez.» entra seco en c108 como en el guion.
    dict(id='giro1', c=(72, 98), txt='Fue un casi.', estilo='CajaN', extra=F_CAJA_PASO, pop=True, y=270),
    dict(id='reenganche', c=(108, 161), txt='Otra vez.', estilo='CajaN', extra=F_CAJA_PASO, pop=False, y=270),
    # desvío anotado: el guion pide c166–c197; en c166 y c167 la remera todavía está debajo de la caja del texto
    # (control v01: 23 176 px y 879 px de la Blanca dentro de la caja de «Más arriba.»). Entra en c168, junto con la
    # campana F#5 «cuando entra el cielo» (guion §2), con el mismo pop.
    dict(id='giro2', c=(168, 197), txt='Más arriba.', estilo='Grande', extra=r'\fs124', pop=True, y=330),
]
Y_MIN, Y_MAX = 270, 1130


def _eventos(textos, dy=None):
    """tiempos ASS a medio cuadro de cada borde (n0 − ½ … n1 + ½): libass decide por milisegundos y 6,6 s puede
    quedar en 6599 ms; así ningún texto entra o sale un cuadro antes/después."""
    dy = dy or {}
    ev = []
    for t in textos:
        n0, n1 = t['c']
        ev.append(dict(t0=max(0.0, (n0 - 0.5) / FPS), t1=(n1 + 0.5) / FPS, txt=t['txt'], estilo=t['estilo'],
                       x=540, y=t['y'] + dy.get(t['id'], 0), pop=t['pop'], extra=t['extra']))
    return ev


def _render_ass(ass_path, n):
    r = run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}:d={DUR + 1}', '-vf',
             f"subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter,select='eq(n\\,{n})',format=gray",
             '-frames:v', '1', '-fps_mode', 'vfr', '-f', 'rawvideo', '-'])
    return np.frombuffer(r, np.uint8).reshape(H, W)


def _bbox(a, thr=8):
    ys, xs = np.nonzero(a > thr)
    return None if len(ys) == 0 else [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def altura_mayuscula(fuente, fs):
    est = {'_m': (fuente, fs, '&H00FFFFFF', '&H00000000', '&H00000000', 0, 0, 0, 1, 8, 0)}
    p = TX / '_mayus.ass'
    V.ass([dict(t0=0, t1=1, txt='HLE', estilo='_m', y=300, blur=False)], p, est)
    g = _render_ass(p, 10) > 128
    ys = np.nonzero(g.any(1))[0]
    return int(ys.max() - ys.min() + 1)


def etapa_textos():
    TX.mkdir(parents=True, exist_ok=True)
    rep = dict(regla='todas las cajas y letras dentro de y 270–1130; mayúscula del hook ≥ 70 px')
    rep['mayuscula_px'] = {'hook CajaN fs120': altura_mayuscula('Inter Display SemiBold', 120),
                           'pasos CajaN fs104': altura_mayuscula('Inter Display SemiBold', 104),
                           'giro2 Grande fs124': altura_mayuscula('Inter Display ExtraBold', 124)}
    # 1) tal cual el guion: medir lo dibujado (caja incluida) en cada cuadro del pop y en un cuadro estable
    def medir(ass_path, dy):
        out = {}
        for t in TEXTOS:
            n0, n1 = t['c']
            cs = sorted(set([n0, n0 + 1, n0 + 2, n0 + 3, n0 + 6, (n0 + n1) // 2, n1]))
            bbs = {n: _bbox(_render_ass(ass_path, n)) for n in cs}
            top = min(b[1] for b in bbs.values() if b); bot = max(b[3] for b in bbs.values() if b)
            out[t['id']] = dict(y_ancla=t['y'] + dy.get(t['id'], 0), cuadros={str(k): v for k, v in bbs.items()},
                                y_arriba_min=top, y_abajo_max=bot)
        return out
    p0 = TX / 'textos_guion_tal_cual.ass'
    V.ass(_eventos(TEXTOS), p0)
    m0 = medir(p0, {})
    rep['tal_cual'] = m0
    # 2) corrección mínima: bajar el ancla lo justo para que la caja no suba de y 270 (condición de Roma)
    dy = {k: max(0, Y_MIN - v['y_arriba_min']) for k, v in m0.items()}
    rep['desplazamiento_y'] = dy
    V.ass(_eventos(TEXTOS, dy), ASS)
    m1 = medir(ASS, dy)
    rep['final'] = m1
    rep['dentro_270_1130'] = all(Y_MIN <= v['y_arriba_min'] and v['y_abajo_max'] <= Y_MAX for v in m1.values())
    # presencia exacta por cuadro: cada texto aparece en su primer cuadro y no en el anterior / desaparece después del último
    bordes = {}
    for t in TEXTOS:
        n0, n1 = t['c']
        bordes[t['id']] = {f'c{n}': _bbox(_render_ass(ASS, n)) for n in (n0 - 1, n0, n1, n1 + 1) if 0 <= n < NF}
    rep['bordes'] = bordes
    json.dump(rep, open(TX / 'textos_v01.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: rep[k] for k in ('mayuscula_px', 'desplazamiento_y', 'dentro_270_1130')}, ensure_ascii=False))
    for k, v in m1.items():
        print(k, v['y_ancla'], v['y_arriba_min'], v['y_abajo_max'])


# =====================================================================================================
# etapa master · copia de video.master con: 2 hilos, PNG convertidos con matriz BT.709 (overlay en yuv444) y
# overlays por número de cuadro (inclusive)
# =====================================================================================================
BASE2 = T / 'life_v1_base_color.mp4'
MA = T / 'master'


def master_v1(video, audio_wav, salida, ass_path, overlays):
    inputs = ['-i', str(video), '-i', str(audio_wav)]
    fc = ['[0:v]setsar=1,format=yuv444p[v0]']
    lab = 'v0'
    for i, (png, n0, n1) in enumerate(overlays):
        inputs += ['-loop', '1', '-framerate', str(FPS), '-i', str(png)]
        fc.append(f'[{i + 2}:v]format=rgba,scale=out_color_matrix=bt709:out_range=tv,format=yuva444p[o{i}]')
        fc.append(f"[{lab}][o{i}]overlay=0:0:format=yuv444:enable='between(n,{n0},{n1})':shortest=1[v{i + 1}]")
        lab = f'v{i + 1}'
    fc.append(f"[{lab}]subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter[vs]")
    fc.append('[vs]format=yuv420p[vout]')
    run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '1:a:0',
         '-c:v', 'libx264', '-profile:v', 'high', '-level:v', '4.0', '-preset', 'slow', '-crf', '17',
         '-maxrate', '20M', '-bufsize', '25M', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-g', '30',
         '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
         '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
         '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
         '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
         '-frames:v', str(NF), '-shortest', '-movflags', '+faststart', str(salida)])
    return salida


def etapa_master():
    MA.mkdir(parents=True, exist_ok=True)
    ov = [(PL / 'cierre_frase.png', *OV_FRASE), (PL / 'cierre_firma.png', *OV_FIRMA)]
    out = MA / NOMBRES['completa']
    master_v1(BASE2, WAV['completa'], out, ASS, ov)
    print('ok', out, out.stat().st_size)
    # sin música: MISMO flujo de video (copia, sin recodificar: x264 con hilos y VBV no da dos codificaciones idénticas
    # bit a bit) + la mezcla sin música codificada igual (AAC-LC 192k 48 kHz estéreo)
    out2 = MA / NOMBRES['sinmusica']
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(out), '-i', str(WAV['sinmusica']), '-map', '0:v:0', '-map', '1:a:0',
         '-c:v', 'copy', '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
         '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
         '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
         '-shortest', '-movflags', '+faststart', str(out2)])
    print('ok', out2, out2.stat().st_size)


# =====================================================================================================
# etapa control · evidencia_v01 (hoja del máster, cortes ±1, validaciones §8, color, sonoridad, ffprobe, md5)
# =====================================================================================================
CORTES = [18, 72, 99, 162, 198]
ROL = {0: '1a apuesta', 18: '1b pregunta', 72: '2 giro 1', 99: '3 reenganche', 162: '4 giro 2', 198: '5 CTA'}
TRAMOS = [('1a 7999', 0.0, 0.6), ('1b 7996', 0.6, 2.4), ('2 3375', 2.4, 3.3), ('3 4625', 3.3, 5.4), ('4 8002', 5.4, 6.6),
          ('5 4641', 6.6, 10.0), ('últimos 0,5 s', 9.5, 10.0)]


def _rol(n):
    k = max(c for c in ROL if c <= n)
    return ROL[k]


def iter_rgb(src, ns, fn=None):
    """una sola decodificación; devuelve {n: fn(n, rgb float)} para los cuadros pedidos (por defecto, rgb uint8 para
    las tiras: 6 MB por cuadro en vez de 25)."""
    ns = set(ns); out = {}
    fn = fn or (lambda n, a: np.clip(a, 0, 255).round().astype(np.uint8))
    pr = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', '2', '-i', str(src), '-f', 'rawvideo',
                           '-pix_fmt', 'yuv420p', '-'], stdout=subprocess.PIPE)
    sz = W * H * 3 // 2; n = 0
    while True:
        b = pr.stdout.read(sz)
        if len(b) < sz:
            break
        if n in ns:
            out[n] = fn(n, yuv_a_rgb(b))
        n += 1
    pr.wait()
    return out, n


def _probe(f):
    err = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', '2', '-i', str(f), '-f', 'null', '-'],
                         capture_output=True, text=True).stderr.strip()
    pj = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(f)]))
    nb = int(run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                  'stream=nb_read_frames', '-of', 'csv=p=0', str(f)]).decode().strip())
    return err, pj, nb


def _hoja_master(src, ns, salida, cols=6, ancho=300):
    from PIL import Image, ImageDraw, ImageFont
    carpeta = EVID / 'cuadros'; carpeta.mkdir(parents=True, exist_ok=True)
    sel = '+'.join(f'eq(n\\,{k})' for k in ns)
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-vf', f"select='{sel}'", '-fps_mode', 'vfr', '-q:v', '2',
         str(carpeta / 'tmp_%03d.jpg')])
    for k, n in enumerate(ns):
        (carpeta / f'tmp_{k + 1:03d}.jpg').replace(carpeta / f'c{n:03d}.jpg')
    alto = ancho * 16 // 9; filas = math.ceil(len(ns) / cols)
    hoja = Image.new('RGB', (cols * (ancho + 4), filas * (alto + 40)), (24, 24, 24))
    fnt = ImageFont.truetype(FONT, 17)
    for i, n in enumerate(ns):
        im = Image.open(carpeta / f'c{n:03d}.jpg').resize((ancho, alto), Image.LANCZOS)
        x, y = (i % cols) * (ancho + 4), (i // cols) * (alto + 40)
        hoja.paste(im, (x, y + 36))
        d = ImageDraw.Draw(hoja)
        d.text((x + 4, y + 2), f'c{n:03d} · {n / FPS:.3f} s', font=fnt, fill=(255, 230, 0))
        d.text((x + 4, y + 19), _rol(n), font=fnt, fill=(200, 200, 200))
    hoja.save(salida, quality=90)


def _tira(src_rgb, ns, salida, caja=None, ancho=180, cols=9, rot=None, marcas=None):
    """tira de cuadros (desde rgb ya decodificados) con número; caja = recorte (x0,y0,x1,y1); marcas = {n: [(rect,color)]}"""
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 16)
    ims = []
    for n in ns:
        im = Image.fromarray(src_rgb[n])
        d = ImageDraw.Draw(im)
        for (r, col) in (marcas or {}).get(n, []):
            d.rectangle(r, outline=col, width=6)
        if caja:
            im = im.crop(caja)
        im = im.resize((ancho, round(ancho * im.height / im.width)), Image.LANCZOS)
        d = ImageDraw.Draw(im); d.rectangle([0, 0, 64, 20], fill=(0, 0, 0)); d.text((3, 1), f'c{n}', font=fnt, fill=(255, 230, 0))
        ims.append(im)
    w, h = ims[0].size; filas = math.ceil(len(ims) / cols)
    hoja = Image.new('RGB', (cols * (w + 3), filas * (h + 3)), (24, 24, 24))
    for i, im in enumerate(ims):
        hoja.paste(im, ((i % cols) * (w + 3), (i // cols) * (h + 3)))
    hoja.save(salida, quality=88)


def presencia(mp4):
    """presencia cuadro a cuadro de la placa y de los textos EN EL MP4: diferencia media de luma |máster − base sin
    textos ni placa| por zona. Zonas: degradé (y 0–250, sin letras), letras de la frase, ficha del logo, y la caja de cada
    texto. Una capa está si su zona cambia (umbral en `umbrales`); se compara con la ventana pedida (cuadros inclusivos)."""
    plj = json.load(open(PL / 'placa.json'))
    txj = json.load(open(TX / 'textos_v01.json'))['final']
    zonas = {'degrade': (0, 0, W - 1, 250), 'frase': tuple(plj['frase_letras_bbox']), 'firma': tuple(plj['ficha_logo_bbox'])}
    for t in TEXTOS:
        bbs = [v for v in txj[t['id']]['cuadros'].values() if v]
        # caja estable (sin el pop) achicada 6 px: ahí la caja #141414 o las letras siempre están
        b = bbs[-1]
        zonas['texto_' + t['id']] = (b[0] + 6, b[1] + 6, b[2] - 6, b[3] - 6)
    ventanas = {'degrade': OV_FRASE, 'frase': OV_FRASE, 'firma': OV_FIRMA}
    ventanas.update({'texto_' + t['id']: tuple(t['c']) for t in TEXTOS})
    cmd = lambda f: subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', '2', '-i', str(f), '-f',
                                      'rawvideo', '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE)
    a, b = cmd(mp4), cmd(BASE2)
    sz = W * H; n = 0; dif = {k: [] for k in zonas}; ficha = []
    fx0, fy0, fx1, fy1 = zonas['firma']
    while True:
        x = a.stdout.read(sz); y = b.stdout.read(sz)
        if len(x) < sz or len(y) < sz:
            break
        X = np.frombuffer(x, np.uint8).reshape(H, W).astype(np.int16); Y = np.frombuffer(y, np.uint8).reshape(H, W).astype(np.int16)
        for k, (x0, y0, x1, y1) in zonas.items():
            dif[k].append(round(float(np.abs(X[y0:y1 + 1, x0:x1 + 1] - Y[y0:y1 + 1, x0:x1 + 1]).mean()), 2))
        # ficha del logo (#FEFEFE): % de píxeles casi blancos (> 240) en su caja; el degradé solo no la enciende
        z = X[fy0:fy1 + 1, fx0:fx1 + 1]
        ficha.append(round(float((z > 240).mean() * 100), 1))
        n += 1
    a.wait(); b.wait()
    # umbral 20: la compresión (crf 17 contra la base sin pérdida) da hasta ≈ 6 de diferencia media en la arena; una capa
    # presente da ≥ 40. Las zonas se pisan entre sí (todos los textos y la frase están en y 270–600), así que la ausencia
    # se controla en los cuadros SIN ninguna capa activa (c99–c107, c162–c167, c198–c209) y la presencia en TODOS los
    # cuadros de la ventana de cada capa (los textos no se superponen en el tiempo entre sí ni con la placa).
    umbrales = {k: 20.0 for k in zonas}
    activo = set()
    for v in ventanas.values():
        activo |= set(range(v[0], v[1] + 1))
    libres = [i for i in range(n) if i not in activo]
    out = dict(cuadros=n, zonas=zonas, umbral_dif_media_luma=umbrales, cuadros_sin_capas=libres, capas={})
    for k in zonas:
        n0, n1 = ventanas[k]
        dentro = list(range(n0, n1 + 1))
        faltan = [i for i in dentro if dif[k][i] <= umbrales[k]]
        sobran = [i for i in libres if dif[k][i] > umbrales[k]]
        out['capas'][k] = dict(ventana=[n0, n1], cuadros_en_ventana=len(dentro), faltan_en_ventana=faltan,
                               aparece_en_cuadros_sin_capas=sobran, dif_min_dentro=min(dif[k][i] for i in dentro),
                               dif_max_en_cuadros_sin_capas=max(dif[k][i] for i in libres), ok=(not faltan and not sobran))
    n0, n1 = OV_FIRMA
    out['capas']['firma_ficha_blanca'] = dict(
        criterio='% de píxeles > 240 en la caja de la ficha: presente > 50 %, ausente < 5 % (c198 → c215: sin ficha)',
        ventana=[n0, n1], faltan_en_ventana=[i for i in range(n0, n1 + 1) if ficha[i] <= 50],
        aparece_antes=[i for i in range(198, n0) if ficha[i] >= 5], min_dentro=min(ficha[n0:n1 + 1]),
        max_c198_c215=max(ficha[198:n0]))
    out['capas']['firma_ficha_blanca']['ok'] = (not out['capas']['firma_ficha_blanca']['faltan_en_ventana'] and
                                               not out['capas']['firma_ficha_blanca']['aparece_antes'])
    out['ficha_pct_blancos_por_cuadro'] = ficha
    out['todo_ok'] = all(v['ok'] for v in out['capas'].values())
    out['dif_por_cuadro'] = dif
    return out


def etapa_presencia():
    r = presencia(MA / NOMBRES['completa'])
    EVID.mkdir(parents=True, exist_ok=True); (EVID / 'medidas').mkdir(exist_ok=True)
    json.dump(r, open(EVID / 'medidas' / 'presencia_placa_y_textos_por_cuadro_v01.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: {kk: vv for kk, vv in v.items()} for k, v in r['capas'].items()}, ensure_ascii=False))
    print('todo_ok', r['todo_ok'])


def etapa_control():
    import hashlib
    from scipy import ndimage as ndi
    EVID.mkdir(parents=True, exist_ok=True)
    MED = EVID / 'medidas'; MED.mkdir(exist_ok=True)
    VAL = EVID / 'validaciones_s8'; VAL.mkdir(exist_ok=True)
    rep = dict(fecha='2026-11-24', version='v01', archivos={})
    # ---------- 1) archivos ----------
    for k, nom in NOMBRES.items():
        f = MA / nom
        err, pj, nb = _probe(f)
        json.dump(pj, open(MED / f'ffprobe_{k}.json', 'w'), indent=1)
        cuerpo = f.read_bytes()
        gps = [m.decode() for m in (b'ISO6709', b'location', b'com.apple.quicktime', b'\xa9xyz') if m in cuerpo]
        a = U.audio_np(f)
        niv, v100, sil = U.niveles_tramos(a, TRAMOS)
        vs = [x for x in pj['streams'] if x['codec_type'] == 'video'][0]
        au = [x for x in pj['streams'] if x['codec_type'] == 'audio'][0]
        r = dict(archivo=str(f), bytes=f.stat().st_size, sha256=hashlib.sha256(cuerpo).hexdigest(),
                 md5_flujo_video=U.md5_stream(f, 'v'), md5_flujo_audio=U.md5_stream(f, 'a'),
                 decodifica_completo=(err == ''), errores_decodificacion=err[:500], cuadros_decodificados=nb,
                 video=dict(codec=vs['codec_name'], perfil=vs.get('profile'), nivel=vs.get('level'), pix_fmt=vs['pix_fmt'],
                            ancho=vs['width'], alto=vs['height'], fps=vs['r_frame_rate'], cuadros=int(vs['nb_frames']),
                            duracion=float(vs['duration']),
                            color=dict(rango=vs.get('color_range'), matriz=vs.get('color_space'),
                                       transferencia=vs.get('color_transfer'), primarios=vs.get('color_primaries'))),
                 audio=dict(codec=au['codec_name'], perfil=au.get('profile'), hz=int(au['sample_rate']),
                            canales=au['channels'], disposicion=au.get('channel_layout'), duracion=float(au['duration'])),
                 duracion_formato=float(pj['format']['duration']), faststart=None,
                 etiquetas_formato=pj['format'].get('tags', {}), marcas_gps_o_ubicacion=gps,
                 sonoridad=U.ebur(f), niveles_por_tramo=niv, ventanas_100ms_bajo_menos50dbfs=sil, rms_100ms=v100)
        r['dif_video_audio_s'] = round(r['video']['duracion'] - r['audio']['duracion'], 4)
        i_moov, i_mdat = cuerpo.find(b'moov'), cuerpo.find(b'mdat')
        r['faststart'] = bool(0 <= i_moov < i_mdat)
        rep['archivos'][k] = r
        print(k, r['sonoridad'], r['md5_flujo_video'], r['md5_flujo_audio'], 'gps', gps, 'sil', sil,
              'dur', r['video']['duracion'], r['audio']['duracion'], 'faststart', r['faststart'], flush=True)
    rep['mismo_video_en_las_dos'] = rep['archivos']['completa']['md5_flujo_video'] == rep['archivos']['sinmusica']['md5_flujo_video']
    f0 = MA / NOMBRES['completa']
    # ---------- 2) hoja del máster: inicio, ±1 de cada corte, medio, final ----------
    ns = sorted({0, 150, NF - 1} | {c + d for c in CORTES for d in (-1, 0, 1)})
    _hoja_master(f0, ns, EVID / 'hoja_master_v01_inicio_cortes_medio_final.jpg')
    U.hoja_contacto(f0, EVID / 'hoja_contacto_cada_0.5s.jpg', cada=15, cols=7, ancho=240)
    U.cuadros_corte(f0, CORTES, EVID / 'cortes', NF - 1)
    # ---------- 3) negros, congelados y duplicados (luma 270×480 de todo el máster) ----------
    raw = run(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(f0), '-vf', 'scale=270:480', '-f', 'rawvideo',
               '-pix_fmt', 'gray', '-'])
    g = np.frombuffer(raw, np.uint8).reshape(-1, 480, 270).astype(np.float32)
    dif = np.abs(np.diff(g, axis=0)).mean((1, 2))
    rep['cuadros'] = dict(total=int(len(g)), luma_media_min=round(float(g.mean((1, 2)).min()), 1),
                          negros_luma_media_menor_16=[int(i) for i in np.nonzero(g.mean((1, 2)) < 16)[0]],
                          dif_consecutiva_min=round(float(dif.min()), 3),
                          posibles_duplicados_dif_menor_0_3=[int(i + 1) for i in np.nonzero(dif < 0.3)[0]],
                          dif_por_cuadro=[round(float(x), 2) for x in dif])
    print('cuadros', {k: v for k, v in rep['cuadros'].items() if k != 'dif_por_cuadro'}, flush=True)
    # ---------- 4) validaciones §8 ----------
    pl = json.load(open(T / 'planos.json'))['planos']
    V8 = {}
    # 4.1 · 7999/7996: pelo y contacto (medidos en la fuente, etapa medir) + tiras del máster
    pelo = json.load(open(T / 'med' / '7999_pelo_c40-c70.json'))
    # el detector oscuro de la etapa medir marca pelo en c43–c61 de la fuente; en c62–c66 lo que marca es la manga de la
    # campera y la mano que suelta la remera (x hasta 1505, revisado a tamaño real en el máster c11–c16: ver
    # v1_master_arriba_c00-c16_1a1.jpg). Brazo, campera y mano están permitidos (guion §2); pelo y cara no.
    usados = [x for x in pelo if 43 <= x['c'] <= 61 and x.get('n', 0) > 0]
    manga = [x for x in pelo if 62 <= x['c'] <= 66 and x.get('n', 0) > 0]
    V8['1_pelo_y_contacto'] = dict(
        caja_1a=list(CAJA_1A), borde_superior_caja_y=CAJA_1A[1], cuadros_fuente_1a='c48–c65 (1,600–2,167 s)',
        pelo_ymax_en_fuente_c43_c61=max((x['ymax'] for x in usados), default=None),
        pelo_cuadros_con_pixeles=[x['c'] for x in usados],
        margen_pelo_caja_px=CAJA_1A[1] - max((x['ymax'] for x in usados), default=0),
        detector_c62_c66_es_manga_y_mano=[dict(c=x['c'], ymax=x['ymax'], x=[x['xmin'], x['xmax']]) for x in manga],
        ultimo_cuadro_1a_fuente='c65 (2,167 s)', contacto_arena_fuente='c68 (2,267 s), visto en 7999_contacto_c62-c71.jpg',
        c18_master='la Blanca ya en la arena (7996 3,300 s): ver cuadros/c018.jpg')
    for nombre in ('7999_pelo_mascara_c48-c65.jpg', '7999_contacto_c62-c71.jpg', '7999_arriba_c46-c67_linea_y420.jpg',
                   '3375_tatuaje_c20-c45.jpg', '3375_arriba_izq_c4-c37_ventana.jpg'):
        shutil.copy2(T / 'med' / nombre, VAL / f'fuente_{nombre}')
    pedidos = set(range(0, 72)) | set(range(72, 99)) | set(range(162, 198)) | set(range(198, 300, 3)) | {299}
    rgb_m, _ = iter_rgb(f0, pedidos)
    _tira(rgb_m, list(range(0, 17)), VAL / 'v1_master_arriba_c00-c16_1a1.jpg', caja=(0, 0, W, 420), ancho=540, cols=3)
    _tira(rgb_m, list(range(0, 18)), VAL / 'v1_master_c00-c17_1a.jpg', cols=9)
    _tira(rgb_m, list(range(18, 72, 3)) + [71], VAL / 'v1_master_c18-c71_1b_cada3.jpg', cols=10)
    # 4.2 · 3375: márgenes del estampado en la ventana y antebrazo fuera
    # estampado medido EN EL MÁSTER: letras negras (L < 110) + estrella celeste (B − R > 25, sat > 0,2) en y 480–1400
    # (debajo del texto), componentes que no tocan el borde del cuadro (dedos y sombras sí lo tocan). c96–c98 llevan el
    # desenfoque vertical de salida (avgblur 12/24/36) y la máscara sólo toma parte de las letras.
    p2 = [x for x in pl if x['id'] == '2'][0]
    marg = []
    for n in range(72, 99):
        a = rgb_m[n].astype(np.float32); L, sat = lum_sat(a)
        reg = np.zeros(L.shape, bool); reg[480:1400, :] = True
        m = reg & ((L < 110) | ((a[..., 2] - a[..., 0] > 25) & (sat > 0.2) & (L > 90)))
        lab, kk = ndi.label(m, structure=np.ones((3, 3)))
        area = ndi.sum(np.ones(L.shape), lab, index=np.arange(1, kk + 1))
        keep = np.zeros(kk + 1, bool)
        for i, sl in enumerate(ndi.find_objects(lab)):
            if area[i] < 15 or sl[1].start == 0 or sl[1].stop >= W or sl[0].start <= 480 or sl[0].stop >= 1400 \
                    or sl[0].stop - sl[0].start > 260:
                continue
            keep[i + 1] = True
        ys, xs = np.nonzero(keep[lab])
        marg.append(dict(cuadro_master=n, cuadro_fuente=p2['n0'] + n - 72, x=[int(xs.min()), int(xs.max())],
                         y=[int(ys.min()), int(ys.max())], izq=int(xs.min()), der=int(W - 1 - xs.max()),
                         desenfoque_de_salida=n >= 96))
    con = [m for m in marg if not m['desenfoque_de_salida']]
    V8['2_3375'] = dict(margenes_estampado_px=marg, metodo='medido en el máster (ver comentario en la receta)',
                        margen_min_px_c72_c95=min(min(m['izq'], m['der']) for m in con),
                        estampado_y_arriba_min=min(m['y'][0] for m in marg),
                        texto_fue_un_casi_y_abajo_max=None,
                        antebrazo='medido en la fuente: x ≤ ≈140 desde ≈ c30 (1,0 s); la ventana arranca en x 102,8 (c72) y '
                                  'está en x ≥ 249 desde c79 (fuente c23), antes de que entre el antebrazo',
                        ventana_x0_por_cuadro=[round(v[1], 1) for v in p2['ventanas']])
    _tira(rgb_m, list(range(72, 99)), VAL / 'v2_master_c72-c98_3375.jpg', cols=9)
    _tira(rgb_m, list(range(72, 99, 2)), VAL / 'v2_master_c72-c98_arriba_izq.jpg', caja=(0, 0, 540, 700), cols=7)
    # 4.3 · 8002: cielo en c162 y c173; «Más arriba.» sin pisar la remera (medido sobre la base sin textos)
    tx = json.load(open(TX / 'textos_v01.json'))['final']['giro2']['cuadros']
    caja_g2 = [min(v[0] for v in tx.values()), min(v[1] for v in tx.values()), max(v[2] for v in tx.values()),
               max(v[3] for v in tx.values())]
    cielo = {}; texto_remera = {}; top_remera = {}; est = {'p4': None, 'p4a': None, 'p5': None, 'p5a': None}

    def blanca_union(a, L, sat, caja, k):
        """la Blanca = unión del blob estricto (tela al sol, L > 150, sat < 0,12) y del amplio (sombra incluida), cada uno
        seguido por superposición con su cuadro anterior: el amplio sólo pierde las partes más cálidas al sol."""
        b1 = blob_blanca(a, L, sat, caja, prev=est[k], amplia=False); est[k] = b1
        b2 = blob_blanca(a, L, sat, caja, prev=est[k + 'a'], amplia=True); est[k + 'a'] = b2
        if b1 is None:
            return b2
        return b1 if b2 is None else (b1 | b2)


    def medir_base(n, a):
        L, sat = lum_sat(a)
        if n in (162, 165, 168, 170, 173, 176, 179):
            m = (a[..., 2] > a[..., 0] + 25) & (a[..., 2] > 110) & (sat > 0.18)
            filas = m.mean(1) >= 0.5
            cielo[n] = dict(pct_pixeles=round(float(m.mean() * 100), 1),
                            pct_alto_filas_cielo=round(float(filas.mean() * 100), 1),
                            fila_mas_baja_cielo=int(np.nonzero(filas)[0].max()) if filas.any() else None)
        if 166 <= n <= 197:
            blob = blanca_union(a, L, sat, (0, 0, W, H), 'p4')
            x0, y0, x1, y1 = caja_g2
            inter = int(blob[y0:y1 + 1, x0:x1 + 1].sum()) if blob is not None else 0
            ys = np.nonzero(blob.any(1))[0] if blob is not None else []
            texto_remera[n] = dict(px_remera_en_caja_texto=inter, remera_y_arriba=int(ys.min()) if len(ys) else None)
        if n >= 198:
            blob = blanca_union(a, L, sat, (0, 300, W, H), 'p5')
            if blob is not None:
                ys, xs = np.nonzero(blob)
                top_remera[n] = dict(y_arriba=int(ys.min()), x=[int(xs.min()), int(xs.max())], px=int(blob.sum()))
        return None

    iter_rgb(BASE2, set(range(162, 300)), medir_base)
    g2 = [t for t in TEXTOS if t['id'] == 'giro2'][0]['c']
    V8['3a_8002'] = dict(cielo=cielo, c162_sin_cielo=cielo[162]['pct_pixeles'] < 1.0,
                         c173_cielo_ge_35pct_alto=cielo[173]['pct_alto_filas_cielo'] >= 35,
                         caja_mas_arriba_union=caja_g2, cuadros_del_texto=list(g2),
                         texto_sobre_remera_c166_c197=texto_remera,
                         max_px_remera_bajo_texto_en_cuadros_del_texto=max(
                             v['px_remera_en_caja_texto'] for n, v in texto_remera.items() if g2[0] <= n <= g2[1]),
                         nota='c166–c167 se miden para documentar por qué el texto entra en c168 (guion: c166)')
    # 4.3b · todos los textos contra la Blanca (base sin textos; caja = unión de lo dibujado de cada texto, pop incluido).
    # En 3375 (c72–c98) la tela llena el cuadro: ahí la regla es «ningún texto sobre un estampado» (estampado de 4.2).
    txj = json.load(open(TX / 'textos_v01.json'))['final']
    ev_bb = {}
    for t in TEXTOS:
        bbs = [v for v in txj[t['id']]['cuadros'].values() if v]
        u = [min(b[0] for b in bbs), min(b[1] for b in bbs), max(b[2] for b in bbs), max(b[3] for b in bbs)]
        for n in range(t['c'][0], t['c'][1] + 1):
            ev_bb[n] = (t['id'], u)
    est2 = {}; tvb = {}

    def texto_vs_blanca(n, a):
        # se sigue la Blanca en TODOS los cuadros de la toma (no sólo en los que tienen texto): el primer cuadro de cada
        # toma elige la remera dentro de la caja de medición (MEDIR: deja afuera la espuma) y después se sigue por
        # superposición en el cuadro entero
        toma = TOMA_DE[n]; L, sat = lum_sat(a)
        if est2.get('toma') != toma:
            est2.update(toma=toma, p=None, pa=None)
            caja = MEDIR[toma]['caja']
        else:
            caja = (0, 200, W, H) if toma == 'IMG_7999' else (0, 0, W, H)
        b1 = blob_blanca(a, L, sat, caja, prev=est2['p'], amplia=False); est2['p'] = b1
        b2 = blob_blanca(a, L, sat, caja, prev=est2['pa'], amplia=True); est2['pa'] = b2
        bl = b1 if b2 is None else (b2 if b1 is None else (b1 | b2))
        if n not in ev_bb:
            return None
        x0, y0, x1, y1 = ev_bb[n][1]
        ys = np.nonzero(bl.any(1))[0] if bl is not None else []
        tvb[n] = dict(texto=ev_bb[n][0], toma=toma, caja_texto=ev_bb[n][1],
                      px_blanca_en_caja=int(bl[y0:y1 + 1, x0:x1 + 1].sum()) if bl is not None else 0,
                      blanca_y_arriba=int(ys.min()) if len(ys) else None)
        return None

    iter_rgb(BASE2, set(range(0, 72)) | set(range(99, 162)), texto_vs_blanca)
    g1 = [t for t in TEXTOS if t['id'] == 'giro1'][0]
    V8['textos_vs_remera'] = dict(
        por_cuadro=tvb, max_px_blanca_bajo_texto=max(v['px_blanca_en_caja'] for v in tvb.values()),
        cuadros_con_superposicion=[n for n, v in tvb.items() if v['px_blanca_en_caja'] > 0],
        fue_un_casi_sobre_3375=dict(caja_texto=ev_bb[72][1], estampado_y_arriba_min=V8['2_3375']['estampado_y_arriba_min'],
                                    separacion_px=V8['2_3375']['estampado_y_arriba_min'] - ev_bb[72][1][3]),
        mas_arriba=dict(caja_texto=caja_g2, max_px=V8['3a_8002']['max_px_remera_bajo_texto_en_cuadros_del_texto']))
    V8['2_3375']['texto_fue_un_casi_y_abajo_max'] = ev_bb[72][1][3]
    marcas = {n: [(caja_g2, (255, 60, 60))] for n in range(g2[0], g2[1] + 1)}
    _tira(rgb_m, list(range(162, 198)), VAL / 'v3_master_c162-c197_8002.jpg', cols=9, marcas=marcas)
    # 4.4 · 4641: placa (degradé, frase, firma) sin tocar la remera; dedo fuera
    plj = json.load(open(PL / 'placa.json'))
    tops = [v['y_arriba'] for n, v in top_remera.items() if n >= OV_FRASE[0]]
    p5 = [x for x in pl if x['id'] == '5'][0]
    dedo = json.load(open(T / 'med' / '4641_dedo_por_cuadro.json'))
    dedo_usados = [x for x in dedo if p5['n0'] <= x['c'] < p5['n0'] + 102]
    vent_abajo = max(v[2] + v[4] for v in p5['ventanas'])
    V8['3b_4641'] = dict(
        degrade_visible_hasta_y=plj['cierre_frase.png']['bbox_alfa_mayor_8'][3], degrade_alfa_0_en_y=PLACA['grad'][0],
        frase_letras_bbox=plj['frase_letras_bbox'], firma_bbox=plj['firma_bbox_opaco'],
        remera_y_arriba_min_c210_c299=min(tops) if tops else None, remera_por_cuadro=top_remera,
        separacion_firma_remera_px=(min(tops) - plj['firma_bbox_opaco'][3]) if tops else None,
        separacion_degrade_alfa0_remera_px=(min(tops) - PLACA['grad'][0]) if tops else None,
        dedo_y_tope_min_fuente=min(x['y_tope_en_x49_1031'] for x in dedo_usados),
        ventana_y_abajo_max_fuente=round(vent_abajo, 1),
        dedo_fuera=min(x['y_tope_en_x49_1031'] for x in dedo_usados) > vent_abajo)
    marcas = {n: [((0, top_remera[n]['y_arriba'], W - 1, top_remera[n]['y_arriba'] + 2), (255, 60, 60))]
              for n in range(198, 300) if n in top_remera}
    ns5 = list(range(198, 300, 6)) + [299]
    _tira(rgb_m, ns5, VAL / 'v3_master_c198-c299_placa_y_remera.jpg', cols=9, marcas=marcas)
    _tira(rgb_m, ns5, VAL / 'v3_master_c198-c299_esquina_inf_izq.jpg', caja=(0, 1380, 540, 1920), cols=9)
    rep['validaciones_s8'] = V8
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ('margenes_estampado_px', 'texto_sobre_remera',
                                                                         'remera_por_cuadro', 'ventana_x0_por_cuadro', 'por_cuadro',
                                                                         'texto_sobre_remera_c166_c197')}
                      for k, v in V8.items()}, ensure_ascii=False, default=str)[:4000], flush=True)
    # ---------- 4.5) presencia cuadro a cuadro de la placa y los textos en el MP4 entregado ----------
    pres = presencia(f0)
    json.dump(pres, open(MED / 'presencia_placa_y_textos_por_cuadro_v01.json', 'w'), ensure_ascii=False, indent=1)
    rep['presencia_por_cuadro'] = {k: {kk: vv for kk, vv in v.items()} for k, v in pres['capas'].items()}
    rep['presencia_todo_ok'] = pres['todo_ok']
    print('presencia', pres['todo_ok'], flush=True)
    # ---------- 5) medidas adjuntas ----------
    for src_, dst in ((T / 'color' / 'color_v01.json', MED / 'color_blanca_por_toma_v01.json'),
                      (T / 'color' / 'color_antes_despues_v01.jpg', EVID / 'color_antes_despues_v01.jpg'),
                      (TX / 'textos_v01.json', MED / 'textos_v01.json'), (ASS, EVID / ASS.name),
                      (PL / 'placa.json', MED / 'placa_v01.json'), (T / 'planos.json', MED / 'planos_v01.json'),
                      (AU / 'mezcla_completa_eventos.json', MED / 'audio_eventos_completa.json'),
                      (AU / 'mezcla_sinmusica_eventos.json', MED / 'audio_eventos_sinmusica.json')):
        shutil.copy2(src_, dst)
    son = {k: dict(archivo=NOMBRES[k], **v['sonoridad'], niveles_por_tramo=v['niveles_por_tramo'],
                   ventanas_100ms_bajo_menos50dbfs=v['ventanas_100ms_bajo_menos50dbfs'], rms_100ms=v['rms_100ms'],
                   metodo='ffmpeg ebur128=peak=true sobre el MP4 entregado (AAC decodificado); niveles por tramo con numpy')
           for k, v in rep['archivos'].items()}
    json.dump(son, open(MED / 'sonoridad_v01.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(rep, open(EVID / 'control_v01.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('ok control')


# =====================================================================================================
# etapa entregar · EXPORTACIONES/ + carpeta de la pieza + evidencia_v01 (sin sobrescribir) y verificación de copias
# (la carpeta del proyecto puede agregar un bloque C2PA al MP4: el sha256 cambia; el ID son los md5 de los flujos)
# =====================================================================================================
def etapa_entregar():
    import hashlib
    res = {}
    for k, nom in NOMBRES.items():
        src = MA / nom
        for dst in (EXP / nom, PIEZA / nom):
            if dst.exists():
                raise RuntimeError(f'{dst} ya existe: no se sobrescribe')
    ev = PIEZA / EVID.name
    if ev.exists():
        raise RuntimeError(f'{ev} ya existe')
    for k, nom in NOMBRES.items():
        for dst in (EXP / nom, PIEZA / nom):
            shutil.copyfile(MA / nom, dst)
    shutil.copytree(EVID, ev)
    time.sleep(8)
    for k, nom in NOMBRES.items():
        src = MA / nom
        ref = dict(bytes=src.stat().st_size, sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                   md5_flujo_video=U.md5_stream(src, 'v'), md5_flujo_audio=U.md5_stream(src, 'a'))
        res[str(src)] = ref
        for dst in (EXP / nom, PIEZA / nom):
            got = dict(bytes=dst.stat().st_size, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
                       md5_flujo_video=U.md5_stream(dst, 'v'), md5_flujo_audio=U.md5_stream(dst, 'a'))
            err = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', '2', '-i', str(dst), '-f', 'null',
                                  '-'], capture_output=True, text=True).stderr.strip()
            res[str(dst)] = dict(got, flujos_iguales=(got['md5_flujo_video'] == ref['md5_flujo_video'] and
                                                      got['md5_flujo_audio'] == ref['md5_flujo_audio']),
                                 archivo_identico=(got == ref), decodifica_completo=(err == ''))
            print(dst, res[str(dst)], flush=True)
    n_local = sum(1 for _ in EVID.rglob('*') if _.is_file()); n_red = sum(1 for _ in ev.rglob('*') if _.is_file())
    res['evidencia'] = dict(carpeta=str(ev), archivos_local=n_local, archivos_copia=n_red)
    print('evidencia', n_local, n_red)
    json.dump(res, open(T / 'entrega_v01.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    globals()[f'etapa_{etapa}']()
