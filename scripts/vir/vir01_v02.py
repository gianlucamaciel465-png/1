#!/usr/bin/env python3
"""VIR-01 «A nada» · receta del máster v02 (Pedro, 18/11/2026). Responde a 04_roma_dictamen_master_v01.md.

Importa vir01.py como módulo y NO lo modifica: v01 sigue saliendo igual con `python vir01.py <etapa>`. Acá se redefinen
solo los puntos del dictamen y las rutas (TRABAJO/vir/vir01_v02/, evidencia_v02/, nombres _v02):
  1. textos más grandes: hook (A y B) con mayúscula ≥ 70 px; «El fundador fue por la foto.» y «¿Y esta?» 1,25×;
  2. «link en bio» con caja (CajaN chica, caja ≥ 44 px de alto);
  3. color: Blanca neutra en 7887, 7884 y 7857 (mapa de ganancias R/G/B por zona, medido cuadro a cuadro sobre la tela
     blanca, aplicado solo a lo que queda neutro con la ganancia de su zona: el celeste, la piel y las rocas no se tocan)
     y Negra carbón en el macro 3453 (corrimiento de croma por franja de luminancia, solo oscuros: el relieve no se toca);
  4. sonido: ambiente de 7884 a +4 dB en 4,45–5,0 (+ hombros de +3 dB en 3,95–4,45 y 5,0–5,5, desvío); campana, pad
     (y subida, desvío) de la pista en una mezcla aparte a +6 dB en 7,0–7,5 y +9 dB en 7,5–7,8 (desvío); r del pad de
     entrada 0,15; huecos de `mus` iguales;
  5. sin música: mar bajo en 7,0–7,8 (7884 fuente 0,40–1,20, sin voces medido por periodicidad), +8 dB a 7887/7857 y
     +2 dB al ambiente de 7884 (desvío, para LRA ≤ 8).
El montaje (planos S1–S6 de v01), los cuadros, los textos exactos, los golpes y los efectos son los de v01.

Etapas (python vir01_v02.py <etapa>, con nice -n 10):
  preparar → color → efectos → audio → master → control → entregar
"""
import json, math, subprocess, sys, hashlib, shutil, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/vir')
import vir01 as B          # noqa: E402  (receta v01: funciones y constantes)
V, U, U2, F4 = B.V, B.U, B.U2, B.F4

R, W, H, FPS, NF, DUR = B.R, B.W, B.H, B.FPS, B.NF, B.DUR
T1 = B.T                                   # TRABAJO/vir/vir01 (v01, solo lectura)
BASE_V01 = T1 / 'vir01_base.mp4'           # montaje de v01 sin efectos ni textos (planos S1–S6)
T2 = R / 'TRABAJO/vir/vir01_v02'
PIEZA = B.PIEZA
EXP = B.EXP
VERSION = 'v02'

# --- rutas y nombres de v02 (las funciones de vir01 leen estas variables del módulo en cada llamada) ---
B.T = T2
B.BASE = T2 / 'vir01_v02_base.mp4'         # base de v01 con la corrección de color (x264 sin pérdida)
B.VID = T2 / 'vir01_v02_video.mp4'         # + fundidos, desenfoques y degradé (sin textos)
B.A = T2 / 'audio'
B.MAS = T2 / 'master'
B.EVID = T2 / 'evidencia_v02'
B.NOMBRES = {'A': 'ROCCE_VIR01_A_NADA_A_v02.mp4', 'B': 'ROCCE_VIR01_A_NADA_B_v02.mp4',
             'A_sinmusica': 'ROCCE_VIR01_A_NADA_A_SINMUSICA_v02.mp4', 'B_sinmusica': 'ROCCE_VIR01_A_NADA_B_SINMUSICA_v02.mp4'}
EVID = B.EVID


# =====================================================================================================
# 1–2 · textos (dictamen 1 y 2)
# =====================================================================================================
# altura de mayúscula medida (H de Inter Display SemiBold renderizada por libass): cuerpo 58 → 34 px (v01).
# DESVÍO medido: «≈1,5×» da cuerpo 87 → 53 px, por debajo de los ≥ 70 px pedidos. Manda el criterio medible: cuerpo 120
# (2,07×) → 72 px. La caja (borde 16 en cuerpo 58) escala igual: 33.
FS_HOOK, BORDE_HOOK = 120, 33
FS_125, BORDE_125 = 72, 20                 # 1,24× (cuerpo entero más cercano a 72,5)
FS_LINK, BORDE_LINK = 38, 10               # caja ≈ 57 px de alto (pedido ≥ 44)
V.ESTILOS.update({   # se agregan en memoria al dict de video.py (el archivo no se toca)
    'CajaN_hook': ('Inter Display SemiBold', FS_HOOK, '&H00FFFFFF', '&H00141414', '&H00141414', 0, BORDE_HOOK, 0, 3, 8, 0),
    'CajaN_125': ('Inter Display SemiBold', FS_125, '&H00FFFFFF', '&H00141414', '&H00141414', 0, BORDE_125, 0, 3, 8, 0),
    'CajaN_link': ('Inter Display SemiBold', FS_LINK, '&H00FFFFFF', '&H00141414', '&H00141414', 0, BORDE_LINK, 0, 3, 8, 0),
})
Y_HOOK = 259     # con el pop (118 %) la caja de c0 empieza en y ≥ 220 (se comprueba en control: pop_hook)
Y_125 = 240      # caja desde y 220 (borde 20)
Y_LINK = 336     # caja desde y 326: 16 px debajo de la caja de «Llevala hasta donde rompe.» (220–310)


def textos_v02(hook):
    t = [dict(t0=0 / FPS, t1=45 / FPS, txt=B.HOOK[hook], estilo='CajaN_hook', y=Y_HOOK, pop=True),          # c0–c44
         None,                                                                                                # c54–c104
         dict(t0=120 / FPS, t1=142 / FPS, txt='¿Y esta?', estilo='CajaN_125', y=Y_125),                    # c120–c141
         dict(t0=255 / FPS, t1=285 / FPS, txt='so f★cking close.', estilo='Grande', y=236, pop=True),      # c255–c284
         dict(t0=285 / FPS, t1=318 / FPS, txt='Llevala hasta donde rompe.', estilo='Caja', y=236),         # c285–c317
         dict(t0=285 / FPS, t1=318 / FPS, txt='link en bio', estilo='CajaN_link', y=Y_LINK)]               # c285–c317
    w = ancho_glifos(dict(t0=0, t1=1, txt=B.FUNDADOR, estilo='CajaN_125', y=Y_125))
    if w <= 900:
        t[1] = dict(t0=54 / FPS, t1=105 / FPS, txt=B.FUNDADOR, estilo='CajaN_125', y=Y_125)
        return [x for x in t if x]
    t[1] = dict(t0=54 / FPS, t1=105 / FPS, txt='El fundador', estilo='CajaN_125', y=Y_125)
    t.insert(2, dict(t0=54 / FPS, t1=105 / FPS, txt='fue por la foto.', estilo='CajaN_125', y=Y_125 + 100))
    return t


def _render_gris(textos_, n):
    S = T2 / 'ctrl'; S.mkdir(parents=True, exist_ok=True)
    p = S / 'render_tmp.ass'; V.ass(textos_, p)
    r = U.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=black:s=1080x1920:r=30:d=2', '-vf',
               f"subtitles={p}:fontsdir=/usr/share/fonts/opentype/inter,trim=start_frame={n}:end_frame={n + 1},format=gray",
               '-frames:v', '1', '-f', 'rawvideo', '-'])
    return np.frombuffer(r, np.uint8).reshape(1920, 1080)


def ancho_glifos(texto):
    """ancho de las letras sin la caja (mismo estilo con borde 0 y sin caja)."""
    fn, fs = V.ESTILOS[texto['estilo']][:2]
    V.ESTILOS['_medir'] = (fn, fs, '&H00FFFFFF', '&H00000000', '&H00000000', 0, 0, 0, 1, 8, 0)
    g = _render_gris([dict(texto, t0=0, t1=1, estilo='_medir', pop=False, blur=False)], 10) > 128
    del V.ESTILOS['_medir']
    xs = np.nonzero(g.any(0))[0]
    return int(xs.max() - xs.min() + 1)


def altura_mayuscula(estilo):
    fn, fs = V.ESTILOS[estilo][:2]
    V.ESTILOS['_medir'] = (fn, fs, '&H00FFFFFF', '&H00000000', '&H00000000', 0, 0, 0, 1, 8, 0)
    g = _render_gris([dict(t0=0, t1=1, txt='HLE', estilo='_medir', y=300, blur=False)], 10) > 128
    del V.ESTILOS['_medir']
    ys = np.nonzero(g.any(1))[0]
    return int(ys.max() - ys.min() + 1)


B.textos = textos_v02
B.LIMITES.update({'El fundador': (54, 104), 'fue por la foto.': (54, 104)})


def contrastes_v02(textos_, carpeta):
    """= vir01.contrastes, con los estilos de caja nuevos (CajaN_*: caja #141414; Caja: caja blanca)."""
    out = {}
    t_caja = round(1.05 / (float(U2.lin(20)) + 0.05), 1)
    for i, t in enumerate(textos_):
        a, b = round(t['t0'] * FPS), round(t['t1'] * FPS) - 1
        caja = t['estilo'].startswith('Caja')
        filas = []
        for n in sorted(set(list(range(a, b + 1, 3)) + [b])):
            mk, g = U2.mascara_texto(t, max(0.0, n / FPS - 0.004), carpeta, f'cont_{i}', dil=8)
            f = U.leer(B.VID, W, H, n0=n, n1=n)[0]
            c = B.contraste_caja(f, g, (255, 255, 255) if t['estilo'] == 'Caja' else (20, 20, 20)) if caja \
                else U2.contraste_blanco(f, mk)
            filas.append(dict(cuadro=n, **c))
        if caja:
            res = dict(texto_sobre_caja=f'{t_caja}:1 (' + ('#141414 sobre blanco' if t['estilo'] == 'Caja' else 'blanco sobre #141414') + ')',
                       caja_fondo_mediana_min=min(x['caja_fondo_mediana'] for x in filas),
                       caja_fondo_p10_min=min(x['caja_fondo_p10'] for x in filas))
        else:
            res = dict(blanco_fondo_mediana_min=min(x['contraste_mediana'] for x in filas),
                       blanco_fondo_p10_min=min(x['contraste_p10'] for x in filas),
                       borde='contorno negro opaco de 6 px (estilo Grande)')
        out[f"{t['txt']} ({t['estilo']}, c{a}–c{b})"] = dict(resumen=res, por_cuadro=filas)
    return out


B.contrastes = contrastes_v02


# =====================================================================================================
# 3 · color (dictamen 3): corrección secundaria por cuadro sobre la base de v01, en YUV de rango limitado BT.709
# =====================================================================================================
# Medido en v01 (mediana de la tela blanca lisa por franja de luminancia, RGB BT.709 como fmt03.leer):
#   7887 sol L 215+ B−R +12, L 190–215 +19 · 7884 L 215+ +5 (sol), 150–190 +17 (sombra) · 7857 +5…+9 (nublado)
#   3453 tela lisa (48, 40, 38) B−R −10, G−R −8 (marrón) · PRODUCTO Blanca +1/+1, Negra −1/−1.
# Una ganancia global no sirve: en 7884 el sol y la sombra piden ganancias distintas, y en 7887 el celeste pasaría de
# B/R 1,21 a 1,13 (PRODUCTO 1,24). Por eso: ganancias por franja de luminancia medidas sobre la tela, aplicadas solo a
# neutros claros (sat < 0,10 entera, se apaga hasta 0,15; L desde 120–150) —el celeste (sat 0,17–0,26) y las rocas,
# la piel y el negro quedan iguales— y en 3453 solo a oscuros (L < 100, se apaga hasta 140): el relieve (L ≥ 171) igual.
COLOR = {
    # banda = franja del «Founders Privée» celeste (para medir el celeste sin la sombra azulada de la tela)
    'IMG_7887': dict(tipo='blanco', cuadros=(45, 104), medir=[60, 75, 90, 100], caja=(200, 830, 640, 1100),
                     banda=(230, 915, 520, 995)),
    'IMG_7884': dict(tipo='blanco', cuadros=(105, 149), medir=[110, 120, 130, 140], caja=(150, 900, 1000, 1500),
                     banda=(200, 1040, 900, 1180)),
    'IMG_7857': dict(tipo='blanco', cuadros=(150, 209), medir=[180, 190, 200, 205], caja=(150, 760, 820, 1800),
                     banda=(100, 950, 850, 1320)),
    'IMG_3453': dict(tipo='negro', cuadros=(210, 239), medir=[215, 222, 228, 234], caja=(0, 0, 1080, 1920)),
}
FRANJAS = {'blanco': [150, 190, 215, 256], 'negro': [0, 35, 60, 100]}
SAT0, SAT1 = 0.10, 0.15                 # calificador de neutros (blanco)
LB0, LB1 = 120, 150                     # blanco: entra desde L 120, entero desde 150
LN0, LN1 = 100, 140                     # negro: entero hasta L 100, se apaga en 140
N_MIN_FRANJA = 3000


def yuv_rgb(Y, Cb, Cr):
    cb = np.repeat(np.repeat(Cb, 2, 0), 2, 1); cr = np.repeat(np.repeat(Cr, 2, 0), 2, 1)
    y = (Y - 16) / 219; u = (cb - 128) / 224; v = (cr - 128) / 224
    Rr = y + 1.5748 * v; Bb = y + 1.8556 * u; Gg = (y - 0.2126 * Rr - 0.0722 * Bb) / 0.7152
    return np.stack([Rr, Gg, Bb], -1) * 255.0


def rgb_yuv(rgb):
    r, g, b = rgb[..., 0] / 255, rgb[..., 1] / 255, rgb[..., 2] / 255
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Cb = 128 + 224 * (b - y) / 1.8556; Cr = 128 + 224 * (r - y) / 1.5748
    Cb = Cb.reshape(H // 2, 2, W // 2, 2).mean((1, 3)); Cr = Cr.reshape(H // 2, 2, W // 2, 2).mean((1, 3))
    return 16 + 219 * y, Cb, Cr


def lum_sat(rgb):
    c = np.clip(rgb, 0, 255)
    L = c @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    mx = c.max(-1); mn = c.min(-1)
    return L, (mx - mn) / (mx + 1)


def _ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def peso(tipo, L, sat):
    if tipo == 'blanco':
        return np.clip((SAT1 - sat) / (SAT1 - SAT0), 0, 1) * _ss((L - LB0) / (LB1 - LB0))
    return 1 - _ss((L - LN0) / (LN1 - LN0))


def mascara_tela(tipo, L, sat, caja):
    m = np.zeros(L.shape, bool); x0, y0, x1, y1 = caja; m[y0:y1, x0:x1] = True
    return m & (L > 150) & (sat < 0.12) if tipo == 'blanco' else m & (L < 100)


def leer_yuv(src, n):
    r = U.run(['ffmpeg', '-v', 'error', '-i', str(src), '-vf', f"select='eq(n\\,{n})'", '-fps_mode', 'passthrough',
               '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'])
    return B._yuv(r)


def franjas(rgb_list, tipo, caja):
    """mediana RGB de la tela por franja de L (sumando los cuadros de medición) → [(L_centro, gR, gG, gB, n, rgb)]."""
    ed = FRANJAS[tipo]; acc = {k: [] for k in range(len(ed) - 1)}
    for rgb in rgb_list:
        L, sat = lum_sat(rgb); m = mascara_tela(tipo, L, sat, caja)
        for k in range(len(ed) - 1):
            mm = m & (L >= ed[k]) & (L < ed[k + 1])
            acc[k].append(np.concatenate([rgb[mm], L[mm][:, None]], 1))
    out = []
    for k, v in acc.items():
        p = np.concatenate(v, 0)
        if len(p) < N_MIN_FRANJA:
            continue
        med = np.median(p[:, :3], 0); Lc = float(np.median(p[:, 3]))
        y = float(med @ np.array([0.2126, 0.7152, 0.0722]))
        g = y / np.maximum(med, 1e-3)
        out.append(dict(L_centro=round(Lc, 1), ganancias=[round(float(x), 4) for x in g], n=int(len(p)),
                        rgb_mediana=[round(float(x), 1) for x in med], b_menos_r=round(float(med[2] - med[0]), 1),
                        g_menos_r=round(float(med[1] - med[0]), 1)))
    return out


CELDA = 24          # blanco: mapa de ganancias en celdas de 24 px (45 × 80)
SIGMA_CELDAS = 1.5  # suavizado espacial del mapa (≈ 36 px)
PRIOR_PX = 60       # celdas sin tela: tienden a la ganancia media del cuadro (peso equivalente a 60 píxeles)
ALFA_T = 0.5        # promedio temporal de las sumas dentro de cada toma (cuadro actual 0,5 + anterior 0,5)


SAT_MED = 0.24      # primera estimación: píxeles claros (L > 140) con sat < 0,24 dentro de la caja (incluye la sombra azulada)
SAT_TELA = 0.08     # vueltas 2 y 3: «tela» = lo que queda con sat < 0,08 con la ganancia de su zona
VUELTAS = 3
SATC0, SATC1 = 0.07, 0.12   # calificador al aplicar (saturación con la ganancia local): entero < 0,07, nada desde 0,12


class MapaBlanco:
    """ganancias R/G/B por zona de luz, medidas cuadro a cuadro sobre la tela blanca, en tres vueltas:
    1) por celda de 24 px, media de los píxeles claros de la caja (L > 140, sat < 0,24); 2–3) se recalcula solo con la
    «tela»: los píxeles que con la ganancia de su zona quedan con sat < 0,08 (las letras celestes, la piel y las rocas
    siguen saturadas y salen). Ganancia = Σ luma / Σ canal (la luma se conserva); suavizado gaussiano normalizado de 1,5
    celdas; celdas sin tela → media del cuadro; promedio temporal 0,5 de las sumas de la última vuelta. Al aplicar, peso
    w = clip((0,12 − sat_corregida)/0,05) · suave((L − 120)/30), con sat_corregida calculada con la ganancia de la zona
    sin pendiente. Además, dentro de cada zona la ganancia depende del brillo del píxel (pendiente medida en la tela del
    cuadro): el sol directo no se pasa a cálido."""
    def __init__(self, caja):
        self.caja = caja; self.prev = None; self.prev_p = None; self.pendientes = []
        self.gy, self.gx = H // CELDA, W // CELDA
        yy, xx = np.mgrid[0:H, 0:W]
        self.idx = ((yy // CELDA) * self.gx + xx // CELDA).ravel()
        self.box = np.zeros((H, W), bool); x0, y0, x1, y1 = caja; self.box[y0:y1, x0:x1] = True

    def _sumas(self, rgb, L, m):
        n = self.gy * self.gx; m = m.ravel(); idx = self.idx[m]; c = np.clip(rgb, 0, 255).reshape(-1, 3)
        return np.stack([np.bincount(idx, c[m, j], n) for j in range(3)] +
                        [np.bincount(idx, L.ravel()[m], n), np.bincount(idx, None, n)], 1)

    def _mapa(self, S):
        from scipy import ndimage as nd
        tot = S.sum(0)
        if tot[4] < 500:
            return None
        Sb = np.stack([nd.gaussian_filter(S[:, j].reshape(self.gy, self.gx), SIGMA_CELDAS, mode='nearest') for j in range(5)], -1)
        Sb = Sb + PRIOR_PX * (tot / tot[4])[None, None, :]
        g = Sb[..., 3:4] / np.maximum(Sb[..., :3], 1e-6)
        G = np.stack([nd.zoom(g[..., c], (H / self.gy, W / self.gx), order=1, mode='nearest')[:H, :W] for c in range(3)], -1)
        return g, G

    def __call__(self, rgb):
        L, sat = lum_sat(rgb)
        base = self.box & (L > 140)
        m = base & (sat < SAT_MED)
        for v in range(VUELTAS):
            S = self._sumas(rgb, L, m)
            if v == VUELTAS - 1 and self.prev is not None:
                S = ALFA_T * S + (1 - ALFA_T) * self.prev
            r = self._mapa(S)
            if r is None:
                self.prev = None
                return rgb, np.zeros(L.shape, np.float32), None
            g, G = r
            _, sat_c = lum_sat(rgb * G)
            m = base & (sat_c < SAT_TELA)
        self.prev = S
        # brillo dentro de la zona: en la tela, lo más claro (sol directo) es menos azul que lo más oscuro del pliegue.
        # Cociente canal/luma predicho q = Q_zona + pendiente · (L − L_zona), pendiente por mínimos cuadrados sobre la
        # tela del cuadro (promedio temporal 0,5); ganancia = 1/q.
        from scipy import ndimage as nd
        tot = S.sum(0)
        Sb = np.stack([nd.gaussian_filter(S[:, j].reshape(self.gy, self.gx), SIGMA_CELDAS, mode='nearest') for j in range(5)], -1)
        Sb = Sb + PRIOR_PX * (tot / tot[4])[None, None, :]
        up = lambda a: nd.zoom(a, (H / self.gy, W / self.gx), order=1, mode='nearest')[:H, :W]
        Q = np.stack([up(Sb[..., c] / Sb[..., 3]) for c in range(3)], -1); Lz = up(Sb[..., 3] / Sb[..., 4])
        x = np.clip(L - Lz, -60, 60)
        mm = m.copy(); mm[:, 1::2] = False; mm[1::2, :] = False
        q = np.clip(rgb, 0, 255)[mm] / np.maximum(L[mm], 1)[:, None] - Q[mm]
        xx = x[mm]
        pend = (q * xx[:, None]).sum(0) / max(float((xx ** 2).sum()), 1e-6) if mm.sum() > 2000 else np.zeros(3)
        if self.prev_p is not None:
            pend = ALFA_T * pend + (1 - ALFA_T) * self.prev_p
        self.prev_p = pend; self.pendientes.append([round(float(v), 6) for v in pend])
        G = 1 / np.maximum(Q + pend[None, None, :] * x[..., None], 1e-3)
        # el calificador usa la ganancia de la zona SIN la pendiente: si no, en el celeste (más oscuro que la tela,
        # x < 0) la pendiente quita azul, baja su saturación y le da peso (el celeste se corría −2 a −5 % en B/R).
        _, sat_c = lum_sat(rgb / np.maximum(Q, 1e-3))
        w = np.clip((SATC1 - sat_c) / (SATC1 - SATC0), 0, 1) * _ss((L - LB0) / (LB1 - LB0))
        return rgb * (1 + w[..., None] * (G - 1)), w.astype(np.float32), g


def corregir_negro(Y, Cb, Cr, fr):
    """3453: corrimiento de croma por franja de luminancia (medido sobre la tela lisa), con peso por L (oscuros enteros,
    se apaga entre L 100 y 140). La luma no cambia y no se amplifica el ruido de los negros."""
    Lc = ((Y.reshape(H // 2, 2, W // 2, 2).mean((1, 3)) - 16) / 219 * 255)
    xs = np.array([f['L_centro'] for f in fr])
    dcb = np.interp(Lc, xs, [f['d_cb'] for f in fr]); dcr = np.interp(Lc, xs, [f['d_cr'] for f in fr])
    w = 1 - _ss((Lc - LN0) / (LN1 - LN0))
    return Y, Cb - w * dcb, Cr - w * dcr, w


def franjas_croma(yuvs, caja):
    """3453: mediana de (Cb − 128, Cr − 128) de la tela (L < 100) por franja de L."""
    ed = FRANJAS['negro']; out = []
    acc = {k: [] for k in range(len(ed) - 1)}
    for Y, Cb, Cr in yuvs:
        rgb = yuv_rgb(Y, Cb, Cr); L, sat = lum_sat(rgb); m = mascara_tela('negro', L, sat, caja)
        cb = np.repeat(np.repeat(Cb, 2, 0), 2, 1); cr = np.repeat(np.repeat(Cr, 2, 0), 2, 1)
        for k in range(len(ed) - 1):
            mm = m & (L >= ed[k]) & (L < ed[k + 1])
            acc[k].append(np.stack([cb[mm] - 128, cr[mm] - 128, L[mm]], 1))
    for k, v in acc.items():
        p = np.concatenate(v, 0)
        if len(p) < N_MIN_FRANJA:
            continue
        out.append(dict(L_centro=round(float(np.median(p[:, 2])), 1), d_cb=round(float(np.median(p[:, 0])), 2),
                        d_cr=round(float(np.median(p[:, 1])), 2), n=int(len(p))))
    return out


def medir_conjuntos(rgb, tipo, caja, m_tela, m_cel, m_rel):
    def med(m):
        if m is None or not m.any():
            return None
        x = np.median(rgb[m], 0)
        return dict(rgb=[round(float(v), 1) for v in x], b_menos_r=round(float(x[2] - x[0]), 1),
                    g_menos_r=round(float(x[1] - x[0]), 1), g_sobre_r=round(float(x[1] / max(x[0], 1)), 3),
                    b_sobre_r=round(float(x[2] / max(x[0], 1)), 3), n=int(m.sum()))
    return dict(tela=med(m_tela), celeste=med(m_cel), relieve=med(m_rel))


def etapa_color():
    """1) mide las franjas de tela en la base de v01; 2) corrige c45–c239 cuadro a cuadro y escribe la base de v02 sin
    pérdida; 3) mide antes/después con las MISMAS máscaras (definidas en el cuadro antes) y el resto de la imagen."""
    T2.mkdir(parents=True, exist_ok=True)
    rep = dict(metodo=('Blanca (7887, 7884, 7857): mapa de ganancias R/G/B por zona de luz, medido cuadro a cuadro sobre '
                       'la tela blanca en tres vueltas: por celda de 24 px, media de los píxeles claros de la caja '
                       '(L > 140, sat < 0,24) y después solo de la «tela» (lo que con la ganancia de su zona queda con '
                       'sat < 0,08); ganancia = Σ luma / Σ canal (la luma se conserva), más una pendiente con el brillo '
                       'del píxel dentro de la zona (mínimos cuadrados sobre la tela del cuadro), suavizado gaussiano de '
                       '1,5 celdas, promedio temporal 0,5, celdas sin tela → media del cuadro. Se aplica con peso '
                       'w = clip((0,12 − sat_corregida)/0,05) · suave((L − 120)/30), donde sat_corregida es la saturación '
                       'con la ganancia de su zona sin la pendiente: la tela (también la sombra profunda) y la espuma/nubes quedan neutras; '
                       'el celeste, las rocas, la piel y los negros siguen saturados o oscuros y tienen w = 0. Negra del macro (3453): corrimiento de croma (Cb, Cr) por franja de luminancia medido '
                       'sobre la tela lisa, con w = 1 − suave((L − 100)/40); la luma no cambia y el relieve (L ≥ 171) '
                       'queda con w = 0.'),
               calificador=dict(SAT0=SAT0, SAT1=SAT1, LB0=LB0, LB1=LB1, LN0=LN0, LN1=LN1), tomas={})
    rep['nota_medicion'] = ('RGB BT.709 desde el YUV de rango limitado (igual que fmt03.leer, ±1 nivel); mediana por '
                            'conjunto. Máscaras fijadas en el cuadro de antes: tela = L > 150 y sat < 0,12 dentro de la '
                            'caja (blanco) o L < 100 (negro); celeste = B−R > 25, L > 90, sat > 0,15 dentro de la caja; '
                            'relieve 3453 = L > 140.')
    FR = {}; FRC = {}
    for toma, c in COLOR.items():
        yuvs = [leer_yuv(BASE_V01, n) for n in c['medir']]
        FR[toma] = franjas([yuv_rgb(*x) for x in yuvs], c['tipo'], c['caja'])     # medición (antes), por franja de L
        rep['tomas'][toma] = dict(cuadros=f"c{c['cuadros'][0]}–c{c['cuadros'][1]}", medir=c['medir'], caja=c['caja'],
                                  tipo=c['tipo'], franjas_antes=FR[toma])
        if c['tipo'] == 'negro':
            FRC[toma] = franjas_croma(yuvs, c['caja']); rep['tomas'][toma]['corrimiento_croma'] = FRC[toma]
        print(toma, json.dumps(FR[toma], ensure_ascii=False), FRC.get(toma, ''), flush=True)
    # 2) corrección y escritura (x264 -qp 0: sin pérdida; las etapas de v01 leen este archivo como leían la base)
    rango = {n: t for t, c in COLOR.items() for n in range(c['cuadros'][0], c['cuadros'][1] + 1)}
    ny = W * H; nc = ny // 4
    dec = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(BASE_V01), '-f', 'rawvideo',
                            '-pix_fmt', 'yuv420p', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p',
                            '-s', f'{W}x{H}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-i', '-', '-c:v', 'libx264', '-qp', '0',
                            '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries',
                            'bt709', '-color_trc', 'bt709', '-color_range', 'tv', str(B.BASE)], stdin=subprocess.PIPE)
    k = 0; pesos = {}; mapas = {}; mapa_ej = {}; W_MED = {}
    medir_set = {n for c in COLOR.values() for n in c['medir']}
    while True:
        b = dec.stdout.read(ny + 2 * nc)
        if len(b) < ny + 2 * nc:
            break
        if k in rango:
            toma = rango[k]; Y, Cb, Cr = B._yuv(b)
            if COLOR[toma]['tipo'] == 'blanco':
                if toma not in mapas:
                    mapas[toma] = MapaBlanco(COLOR[toma]['caja'])
                rgb2, w, g = mapas[toma](yuv_rgb(Y, Cb, Cr))
                Y2, Cb2, Cr2 = rgb_yuv(rgb2)
                if g is not None and k == COLOR[toma]['medir'][2]:
                    gc = g[g[..., 0] > 0]
                    mapa_ej[toma] = dict(cuadro=k, ganancia_min=[round(float(x), 3) for x in gc.min(0)],
                                         ganancia_max=[round(float(x), 3) for x in gc.max(0)])
            else:
                Y2, Cb2, Cr2, w = corregir_negro(Y, Cb, Cr, FRC[toma])
            pesos[k] = round(float((w > 0.01).mean() * 100), 1)
            if k in medir_set:
                W_MED[k] = w if w.shape == (H, W) else np.repeat(np.repeat(w, 2, 0), 2, 1)
            b = np.concatenate([Y2.ravel(), Cb2.ravel(), Cr2.ravel()]).round().clip(0, 255).astype(np.uint8).tobytes()
        enc.stdin.write(b); k += 1
    rep['rango_ganancias_mapa'] = mapa_ej
    rep['pendiente_brillo_por_toma'] = {t: dict(cuadros=len(mp.pendientes), mediana=[round(float(v), 6) for v in np.median(mp.pendientes, 0)])
                                        for t, mp in mapas.items() if mp.pendientes}
    dec.stdout.close(); dec.wait(); enc.stdin.close(); enc.wait()
    assert k == NF and enc.returncode == 0, (k, enc.returncode)
    rep['pct_pixeles_tocados_por_cuadro'] = pesos
    # 3) antes / después
    ims = []
    for toma, c in COLOR.items():
        filas = []
        for n in c['medir']:
            a = yuv_rgb(*leer_yuv(BASE_V01, n)); d = yuv_rgb(*leer_yuv(B.BASE, n))
            L, sat = lum_sat(a)
            m_tela = mascara_tela(c['tipo'], L, sat, c['caja'])
            box = np.zeros(L.shape, bool); x0, y0, x1, y1 = c.get('banda', c['caja']); box[y0:y1, x0:x1] = True
            m_cel = box & (a[..., 2] - a[..., 0] > 25) & (L > 90) & (sat > 0.15) if c['tipo'] == 'blanco' else None
            m_rel = (L > 140) if c['tipo'] == 'negro' else None
            fuera = W_MED[n] <= 0.01
            filas.append(dict(cuadro=n, antes=medir_conjuntos(a, c['tipo'], c['caja'], m_tela, m_cel, m_rel),
                              despues=medir_conjuntos(d, c['tipo'], c['caja'], m_tela, m_cel, m_rel),
                              resto_sin_tocar_dif_media=round(float(np.abs(np.clip(d, 0, 255) - np.clip(a, 0, 255))[fuera].mean()), 2),
                              resto_pct=round(float(fuera.mean() * 100), 1)))
        rep['tomas'][toma]['antes_despues'] = filas
        # parches de v01 (fmt03.color_parche) antes/después
        rep['tomas'][toma]['parches_v01'] = {}
        for nom, (n, caja) in B.MASTER_PARCHES.items():
            if c['cuadros'][0] <= n <= c['cuadros'][1]:
                rep['tomas'][toma]['parches_v01'][nom] = dict(
                    antes=U.color_parche(np.clip(yuv_rgb(*leer_yuv(BASE_V01, n)), 0, 255).round().astype(np.uint8), caja),
                    despues=U.color_parche(np.clip(yuv_rgb(*leer_yuv(B.BASE, n)), 0, 255).round().astype(np.uint8), caja))
        ims.append((toma, c['medir'][2]))
    # sin cambios fuera de c45–c239 (4631)
    rep['fuera_de_rango_identico'] = {f'c{n}': bool(np.array_equal(leer_yuv(BASE_V01, n)[0], leer_yuv(B.BASE, n)[0]))
                                      for n in (0, 44, 240, 317)}
    json.dump(rep, open(T2 / 'color_v02.json', 'w'), ensure_ascii=False, indent=1)
    hoja_color(ims)
    for toma in COLOR:
        f = rep['tomas'][toma]['antes_despues']
        print(toma, [(x['cuadro'], x['antes']['tela']['b_menos_r'], x['despues']['tela']['b_menos_r'],
                      x['antes']['tela']['g_menos_r'], x['despues']['tela']['g_menos_r'],
                      (x['antes']['celeste'] or x['antes']['relieve'] or {}).get('b_sobre_r'),
                      (x['despues']['celeste'] or x['despues']['relieve'] or {}).get('b_sobre_r'),
                      x['resto_sin_tocar_dif_media']) for x in f], flush=True)
    print('fuera de rango idéntico', rep['fuera_de_rango_identico'])


def hoja_color(ims):
    """antes / después a 1:2 de un cuadro por toma, con PRODUCTO al lado."""
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(U.FONT, 24)
    tiles = []
    recortes = {'IMG_7887': (150, 780, 750, 1180), 'IMG_7884': (100, 880, 1080, 1560), 'IMG_7857': (100, 650, 1000, 1700),
                'IMG_3453': (0, 0, 1080, 1300)}
    for toma, n in ims:
        x0, y0, x1, y1 = recortes[toma]
        par = []
        for nom, src in (('v01', BASE_V01), ('v02', B.BASE)):
            im = Image.fromarray(np.clip(yuv_rgb(*leer_yuv(src, n)), 0, 255).round().astype(np.uint8)[y0:y1, x0:x1])
            s = 520 / im.height; im = im.resize((int(im.width * s), 520))
            d = ImageDraw.Draw(im); d.rectangle([0, 0, 330, 32], fill=(0, 0, 0))
            d.text((6, 3), f'{toma[4:]} c{n} {nom}', font=fnt, fill=(255, 255, 0)); par.append(im)
        tiles.append(par)
    prod = []
    for nom in ('blanca_espalda_estudio', 'negra_frente_detalle_estampado'):
        im = Image.open(T1 / 'ctrl' / f'{nom}_srgb.png').convert('RGB')
        s = 520 / im.height; im = im.resize((int(im.width * s), 520)); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 330, 32], fill=(0, 0, 0)); d.text((6, 3), 'PRODUCTO ' + nom.split('_')[0], font=fnt, fill=(255, 255, 0))
        prod.append(im)
    ww = max(sum(p.width for p in par) + 10 for par in tiles + [prod]); hh = 530 * (len(tiles) + 1)
    hoja = Image.new('RGB', (ww, hh), (30, 30, 30))
    for r_, par in enumerate(tiles + [prod]):
        x = 0
        for im in par:
            hoja.paste(im, (x, r_ * 530)); x += im.width + 10
    EVID.mkdir(parents=True, exist_ok=True)
    hoja.save(EVID / 'color_antes_despues_v01_v02.jpg', quality=90)


# =====================================================================================================
# 4–5 · sonido (dictamen 4 y 5)
# =====================================================================================================
# ambiente de 7884 (−2 dB en v01): +6 dB en 4,45–5,00 (queda en +4 dB, dictamen 4). Los hombros de +3 dB en 3,95–4,45 y
# 5,00–5,50 son DESVÍO mío para el objetivo de −24 LUFS por tramo de 0,5 s (sin ellos: 4,0–4,5 −24,3 y 5,0–5,5 −25,7).
CURVA_7884 = [(3.95, 4.45, 3.0), (4.45, 5.00, 6.0), (5.00, 5.50, 3.0)]
# pista del relieve en la mezcla aparte: campana y pad +6 dB (dictamen 4). DESVÍO: la subida (7,30–7,80) también pasa a la
# mezcla aparte y el último tramo 7,50–7,80 va a +9 dB (sin eso, 7,5–8,0 queda en −24,4 por los 0,2 s del hueco 3).
CURVA_PISTA = [(7.00, 7.50, 6.0), (7.50, 7.80, 9.0)]   # vuelve a 0 dB en 7,80–7,83 (dentro del hueco 3: mus en silencio)
PISTA_M2 = ('campana', 'pad', 'subida')
RAMPA = 0.03
MAR_BAJO = dict(toma='IMG_7884', src0=0.40, t0=7.00, t1=7.80, bajo_db=4.0)   # sin música: 4 dB debajo del mar de 7857
SM_MAS_DB = 8.0                     # sin música: +8 dB a 7887 y 7857
SM_7884_DB = 2.0                    # sin música: DESVÍO, +2 dB al ambiente de 7884 (con +0: LRA 8,2; con +2: 6,8)


def curva(t0, t1, g_db, n, sr=48000, rampa=RAMPA, sube_antes=True):
    """ganancia lineal por muestra: 0 dB afuera, g_db en [t0, t1), rampas de `rampa` s (antes de t0 y después de t1)."""
    t = np.arange(n) / sr; G = 10 ** (g_db / 20)
    g = np.ones(n)
    a0 = t0 - rampa if sube_antes else t0
    g[(t >= a0) & (t < t0)] = 1 + (G - 1) * (t[(t >= a0) & (t < t0)] - a0) / max(t0 - a0, 1e-9)
    g[(t >= t0) & (t < t1)] = G
    m = (t >= t1) & (t < t1 + rampa); g[m] = G + (1 - G) * (t[m] - t1) / rampa
    return g


def curva_tramos(segs, n, sr=48000, rampa=RAMPA):
    """ganancia por muestra a partir de tramos [(t0, t1, dB)] contiguos o no: 0 dB afuera; entre niveles, rampa lineal
    de `rampa` s que termina en el borde (sube antes de t0 / baja después de t1 si el vecino es 0 dB)."""
    t = np.arange(n) / sr
    pts = [(0.0, 0.0)]
    segs = sorted(segs)
    for i, (t0, t1, gdb) in enumerate(segs):
        prev = segs[i - 1][2] if i and abs(segs[i - 1][1] - t0) < 1e-6 else 0.0
        if prev == 0.0:
            pts += [(t0 - rampa, 0.0), (t0, gdb)]
        else:
            pts += [(t0, prev), (t0 + rampa, gdb)]
        nxt = segs[i + 1][2] if i + 1 < len(segs) and abs(segs[i + 1][0] - t1) < 1e-6 else None
        pts += [(t1, gdb)] + ([(t1 + rampa, 0.0)] if nxt is None else [])
    pts.append((n / sr + 1, pts[-1][1]))
    xs, ys = zip(*pts)
    return 10 ** (np.interp(t, xs, ys) / 20)


def musica_v02(m, m2):
    """= vir01.musica con dos cambios: r del pad de entrada 0,15 y campana + pad de la pista en `m2` (mezcla aparte).
    Mismo orden de llamadas: el generador de ruido de sonido.py da los mismos sonidos que v01 (m2 comparte las
    respuestas de reverberación de m, así no se generan nuevas)."""
    def charles(t0, t1, g=.08):
        for t in np.arange(t0, t1 - 1e-6, 0.25):
            m.charles(round(float(t), 3), g)
    m.pad(0.0, [45, 48, 52], 0.95, .06, 1000, a=.12, r=.15); m.campana(0.0, 76, .05)      # r 0,30 → 0,15 (dictamen 4)
    for t, g in zip((0.0, 0.25, 0.5, 0.75), (.07, .08, .09, .10)):
        m.charles(t, g)
    m.subida(0.40, 0.95, .16)
    m.bombo(1.5, .9); m.ocho08(1.5, 33, .9, .55, glide_desde=40); m.pad(1.5, [45, 48, 52], 1.9, .06, 1400)
    charles(1.5, 3.5); m.palma(2.0); m.palma(3.0); m.bombo(2.5, .6); m.ocho08(2.5, 33, .45); m.ocho08(3.0, 36, .45)
    m.bombo(3.5, .7); m.pad(3.5, [41, 45, 48], .9, .06, 1200, r=.3); charles(3.5, 4.25)
    m.redoble(3.70, 4.45, .12); m.subida(3.85, 4.45, .14)
    m.bombo(5.5, 1.0); m.impacto(5.5, .40); m.ocho08(5.5, 33, 1.0, .6, glide_desde=40)
    m.pad(5.5, [45, 48, 52, 57], 1.3, .07); charles(5.5, 7.0); m.palma(6.0); m.palma(6.5); m.bombo(6.0, .6)
    q = {k: (m2 if k in PISTA_M2 else m) for k in ('campana', 'pad', 'subida')}                       # pista → m2
    q['campana'].campana(7.0, 76, .06, .9); q['pad'].pad(7.0, [48, 52, 55], .8, .05, 900, r=.3); q['subida'].subida(7.30, 7.80, .14)
    m.bombo(8.5, 1.0); m.ocho08(8.5, 33, 1.1, .6, glide_desde=40); m.pad(8.5, [45, 48, 52, 57], 1.0, .07)
    m.campana(8.5, 76, .07, .9); charles(8.5, 9.5); m.palma(9.0)
    m.bombo(9.5, .8); m.ocho08(9.5, 36, .5); m.ocho08(10.0, 33, .6); m.pad(9.5, [45, 48, 52], .8, .06, r=.5)
    m.palma(10.0, .25)
    for x in (m, m2):
        for t0, t1 in B.HUECOS:
            x.silenciar('mus', t0, t1)
        x.fundido('mus', 10.10, 10.60); x.fundido('fx', 10.10, 10.60)
    g = curva_tramos(CURVA_PISTA, m2.N)          # m2 no tiene nada antes de 7,0: la rampa previa no actúa
    for k in ('mus', 'fx'):
        m2.pistas[k] *= g[:, None]
    for t0, t1, gdb in CURVA_PISTA:
        m2.log(t0, f'{" + ".join(PISTA_M2)} de la pista {gdb:+.1f} dB en {t0:.2f}–{t1:.2f} (mezcla aparte)')


def rms_fuente(toma, src0, dur, hp=None):
    from sonido import Mezcla, filt
    a = Mezcla(0.1).leer(toma)[int(src0 * 48000):int((src0 + dur) * 48000)]
    if hp:
        a = filt(a, 'high', hp)
    return float(20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-12))


def ambientes_v02(m, sinmusica=False):
    from sonido import Mezcla
    s = SM_MAS_DB if sinmusica else 0.0
    m.ambiente('IMG_4631', 2.433, 0.000, 2.000, 0, hp=40, fin_fade=.45)
    m.ambiente('IMG_7887', 0.000, 1.500, 2.900, -6 + s, hp=150, ini_fade=.3, fin_fade=.1)
    m.ambiente('IMG_7857', 3.500, 2.850, 3.500, -8 + s, ini_fade=.1)
    a2 = Mezcla(m.dur)                                                                    # 7884 aparte, con la curva
    base = -2 + (SM_7884_DB if sinmusica else 0.0)
    a2.ambiente('IMG_7884', 2.300, 3.500, 5.800, base, hp=40, fin_fade=.5)
    m.pistas['amb'] += a2.pistas['amb'] * curva_tramos(CURVA_7884, m.N)[:, None]
    m.ev += a2.ev
    for t0, t1, gdb in CURVA_7884:
        m.log(t0, f'ambiente IMG_7884 {gdb:+.1f} dB en {t0:.2f}–{t1:.2f} (de {base:+.1f} a {base + gdb:+.1f} dB)')
    m.ambiente('IMG_7857', 1.400, 5.400, 7.000, -8 + s, ini_fade=.3, fin_fade=.2)
    if sinmusica:
        mb = MAR_BAJO
        ref = rms_fuente('IMG_7857', 1.400, 1.600) + (-8 + s)
        g_mar = round(ref - mb['bajo_db'] - rms_fuente(mb['toma'], mb['src0'], mb['t1'] - mb['t0'], hp=40), 1)
        m.ambiente(mb['toma'], mb['src0'], mb['t0'], mb['t1'], g_mar, hp=40, ini_fade=.08, fin_fade=.08)
        m.log(mb['t0'], f'mar bajo (sin música): {mb["toma"]} fuente {mb["src0"]:.2f}, {g_mar:+.1f} dB = '
                        f'{mb["bajo_db"]:.0f} dB debajo del mar de 7857 (RMS)')
    m.ambiente('IMG_4631', 3.500, 8.000, 10.600, 0, hp=40, fin_fade=.25)


def mezclas_v02():
    from sonido import Mezcla
    mus, m2, amb, amb_s, fol = (Mezcla(DUR) for _ in range(5))
    m2._ir = mus._ir
    musica_v02(mus, m2); ambientes_v02(amb); ambientes_v02(amb_s, sinmusica=True); B.foley(fol)
    def suma(*ms):
        t = Mezcla(DUR)
        for k in t.pistas:
            t.pistas[k] = sum(x.pistas[k] for x in ms)
        t.ev = [e for x in ms for e in x.ev]
        return t
    musT = suma(mus, m2)
    return dict(mus=musT, amb=amb, amb_s=amb_s, fol=fol, completa=suma(musT, amb, fol), sinmusica=suma(amb_s, fol))


B.mezclas = mezclas_v02


# --- sonoridad por tramos de 0,5 s (K-weighting BS.1770 en numpy, comprobado contra la M de ebur128) ---
def kpond(x):
    from scipy.signal import lfilter
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]; a1 = [1, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]; a2 = [1, -1.99004745483398, 0.99007225036621]
    return lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)


def sonoridad_ventana(y, a, b, sr=48000):
    s = y[int(round(a * sr)):int(round(b * sr))]
    return round(float(-0.691 + 10 * np.log10((s ** 2).mean(0).sum() + 1e-12)), 1)


def sonoridad_tramos(mp4_o_wav):
    if str(mp4_o_wav).endswith('.wav'):
        import soundfile as sf
        x = sf.read(str(mp4_o_wav))[0]
    else:
        x = U.audio_np(mp4_o_wav).astype(np.float64)
    y = kpond(x)
    grilla = [dict(tramo=f'{k * 0.5:.1f}–{min(k * 0.5 + 0.5, DUR):.1f}', L=sonoridad_ventana(y, k * 0.5, min(k * 0.5 + 0.5, DUR)))
              for k in range(21)] + [dict(tramo='10.1–10.6 (último 0,5 s)', L=sonoridad_ventana(y, 10.1, 10.6))]
    desliz = [dict(t0=round(t, 1), L=sonoridad_ventana(y, t, t + 0.5)) for t in np.arange(0, DUR - 0.5 + 1e-6, 0.1)]
    return dict(grilla=grilla, deslizante=desliz)


def periodicidad(x, sr=48000, marco=0.04):
    """indicador de voz sin modelo: por marco de 40 ms, máximo de la autocorrelación normalizada entre 2,5 y 12,5 ms
    (80–400 Hz, tono de voz) sobre la banda 80–1000 Hz. Tono armónico ≈ 0,8; ruido de mar ≈ 0,2."""
    from sonido import filt
    y = filt(filt(x.mean(1) if x.ndim > 1 else x, 'high', 80), 'low', 1000)
    n = int(marco * sr); l0, l1 = int(sr / 400), int(sr / 80); v = []
    for i in range(0, len(y) - n, n // 2):
        s = y[i:i + n] - y[i:i + n].mean()
        if (s ** 2).sum() < 1e-10:
            continue
        ac = np.correlate(s, s, 'full')[n - 1:]; ac = ac / ac[0]
        v.append(float(ac[l0:l1].max()))
    v = np.array(v)
    return dict(marcos=int(len(v)), mediana=round(float(np.median(v)), 2), p95=round(float(np.percentile(v, 95)), 2),
                max=round(float(v.max()), 2))


def control_voces():
    from sonido import Mezcla, SR
    a = Mezcla(0.1).leer(MAR_BAJO['toma'])
    t = np.arange(int(1.0 * SR)) / SR
    tono = sum(np.sin(2 * np.pi * 160 * k * t) / k for k in range(1, 8))[:, None] * np.ones((1, 2))
    ruido = np.random.default_rng(0).standard_normal((len(t), 2))
    i0, i1 = int(MAR_BAJO['src0'] * SR), int((MAR_BAJO['src0'] + MAR_BAJO['t1'] - MAR_BAJO['t0']) * SR)
    return dict(metodo=periodicidad.__doc__.strip(), mar_bajo=periodicidad(a[i0:i1]),
                referencia_7884_0_a_2_6s=periodicidad(a[:int(2.6 * SR)]), tono_armonico_160Hz=periodicidad(tono),
                ruido_blanco=periodicidad(ruido),
                nota='heurística, no transcripción ni escucha: descarta voz sostenida, no garantiza ausencia de un susurro')


def validar_kpond(mp4):
    """mi sonoridad de 400 ms contra la M de ffmpeg ebur128 en algunos instantes."""
    mom = U2.momentanea(mp4); y = kpond(U.audio_np(mp4).astype(np.float64)); out = []
    for t in (1.2, 3.0, 4.8, 6.0, 7.5, 9.0):
        M = min(mom, key=lambda r: abs(r['t'] - t))
        out.append(dict(t=M['t'], M_ffmpeg=M['M'], M_numpy=sonoridad_ventana(y, M['t'] - 0.4, M['t'])))
    return out


# =====================================================================================================
# etapas
# =====================================================================================================
def etapa_preparar():
    """copia de v01 lo que el control reutiliza (mediciones del montaje, que no cambia)."""
    T2.mkdir(parents=True, exist_ok=True); (T2 / 'hojas').mkdir(exist_ok=True)
    for f in ('medir.json', 'planos.json', 'dif_consecutiva.json', 'gotas_4631_c110-c118_ventana_1a1.jpg'):
        shutil.copy2(T1 / f, T2 / f)
    for f in ('4631_c111-c115_791_1157_x4.jpg', '4631_c109-c120_3.63-4.0.jpg', '7884_c105-c114_3.5-3.8.jpg',
              '3453_c90-c99_3.0-3.3.jpg', '7857_c0-c12_0.0-0.4.jpg', '4631_c180-c186_6.0-6.2.jpg'):
        shutil.copy2(T1 / 'hojas' / f, T2 / 'hojas' / f)
    print('preparado', T2)


def etapa_master():
    for k in B.NOMBRES.values():
        for d in (B.MAS / k, EXP / k, PIEZA / k):
            if d.exists():
                raise RuntimeError(f'{d} ya existe: no se sobrescribe')
    B.etapa_master()


def control_v02():
    """lo que v02 agrega al control de v01: medidas de los textos, hoja a 360 px, sonoridad por tramos de 0,5 s y LRA,
    color antes/después, una sola variable entre A y B."""
    S = T2 / 'ctrl'; S.mkdir(exist_ok=True)
    rep = dict(version=VERSION, dictamen='04_roma_dictamen_master_v01.md')
    # textos
    ts = textos_v02('A'); tb = textos_v02('B')
    cajas = B.cajas_por_texto(ts + tb[:1], S)
    rep['textos'] = dict(
        mayuscula_px={'v01 CajaN (cuerpo 58)': altura_mayuscula('CajaN'), f'hook CajaN_hook (cuerpo {FS_HOOK})': altura_mayuscula('CajaN_hook'),
                      f'CajaN_125 (cuerpo {FS_125})': altura_mayuscula('CajaN_125'), f'link CajaN_link (cuerpo {FS_LINK})': altura_mayuscula('CajaN_link'),
                      'Caja (cuerpo 58)': altura_mayuscula('Caja')},
        mayuscula_si_1_5x_px=None,
        anchos_glifos={t['txt']: ancho_glifos(t) for t in ts + tb[:1]},
        cajas=cajas,
        caja_alto_px={k: v['caja'][3] - v['caja'][1] + 1 for k, v in cajas.items()},
        caja_ancho_pct={k: round((v['caja'][2] - v['caja'][0] + 1) / W * 100, 1) for k, v in cajas.items()},
        pop={h: B.pop_hook(textos_v02(h)[0], S) for h in ('A', 'B')})
    V.ESTILOS['_p15'] = ('Inter Display SemiBold', 87, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 24, 0, 3, 8, 0)
    rep['textos']['mayuscula_si_1_5x_px'] = altura_mayuscula('_p15'); del V.ESTILOS['_p15']
    # hoja a 360 px de ancho (como la de v01) + recorte del CTA a 360
    mA = B.MAS / B.NOMBRES['A']; mB = B.MAS / B.NOMBRES['B']
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(U.FONT, 16)
    tiles = []
    for m, n, rot in ((mA, 6, 'A c6'), (mA, 80, 'A c80'), (mA, 130, 'A c130'), (mA, 270, 'A c270'), (mA, 300, 'A c300'), (mB, 6, 'B c6')):
        f = U.leer(m, W, H, n0=n, n1=n)[0]
        im = Image.fromarray(f).resize((360, 640), Image.LANCZOS); tiles.append((im, rot))
    o = Image.new('RGB', (len(tiles) * 366, 670), (32, 32, 32)); d = ImageDraw.Draw(o)
    for i, (im, rot) in enumerate(tiles):
        o.paste(im, (i * 366, 30)); d.text((i * 366 + 6, 6), rot + ' · 360 px', fill=(255, 230, 0), font=fnt)
    o.save(EVID / 'textos_ancho_telefono_360px.jpg', quality=92)
    f = U.leer(mA, W, H, n0=300, n1=300)[0]
    im = Image.fromarray(f).resize((360, 640), Image.LANCZOS).crop((0, 50, 360, 150)).resize((720, 200), Image.NEAREST)
    im.save(EVID / 'cta_link_en_bio_360px_ampliado_x2.png')
    # sonoridad por tramos de 0,5 s y LRA
    rep['sonoridad_0_5s'] = {k: sonoridad_tramos(B.MAS / B.NOMBRES[k]) for k in ('A', 'A_sinmusica')}
    rep['sonoridad_0_5s']['validacion_contra_ebur128_M'] = validar_kpond(mA)
    for k in ('A', 'A_sinmusica'):
        g = rep['sonoridad_0_5s'][k]['grilla']
        rep['sonoridad_0_5s'][k]['bajo_menos_24'] = [x for x in g if x['L'] < -24]
        rep['sonoridad_0_5s'][k]['minimo'] = min(g, key=lambda x: x['L'])
        dl = rep['sonoridad_0_5s'][k]['deslizante']
        rep['sonoridad_0_5s'][k]['deslizante_bajo_menos_24'] = [x for x in dl if x['L'] < -24]
    # M de 400 ms cada 0,1 s (fin de ventana) fuera del hueco 1, y los dos tramos que cita el dictamen
    for k in ('A', 'A_sinmusica'):
        y = kpond(U.audio_np(B.MAS / B.NOMBRES[k]).astype(np.float64))
        Mv = [dict(t=round(float(t), 1), M=sonoridad_ventana(y, t - 0.4, t)) for t in np.arange(0.4, DUR + 1e-6, 0.1)]
        h0, h1 = B.HUECOS[0]
        rep['sonoridad_0_5s'][k]['M_400ms_bajo_menos_24_fuera_hueco1'] = [x for x in Mv if x['M'] < -24 and not (h0 <= x['t'] - 0.2 <= h1)]
        rep['sonoridad_0_5s'][k]['tramos_dictamen'] = {f'{a:.2f}–{b:.2f}': sonoridad_ventana(y, a, b) for a, b in ((4.45, 5.5), (7.0, 7.8))}
    # LRA, I y pico de las cuatro (ebur128 de ffmpeg sobre el MP4)
    rep['ebur128'] = {}
    for k, n in B.NOMBRES.items():
        o = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(B.MAS / n), '-map', '0:a', '-af', 'ebur128=peak=true',
                            '-f', 'null', '-'], capture_output=True, text=True).stderr.splitlines()
        val = lambda key: float([l for l in o if l.strip().startswith(key)][-1].split()[1])
        rep['ebur128'][k] = dict(I=val('I:'), LRA=val('LRA:'), pico_dBTP=val('Peak:'))
    rep['voces_mar_bajo'] = control_voces()
    # comparación con v01 (mismo método)
    rep['sonoridad_0_5s']['v01'] = {k: sonoridad_tramos(T1 / 'master' / n)['grilla'] for k, n in
                                    (('A', 'ROCCE_VIR01_A_NADA_A_v01.mp4'), ('A_sinmusica', 'ROCCE_VIR01_A_NADA_A_SINMUSICA_v01.mp4'))}
    # color: copia del antes/después de la etapa color
    shutil.copy2(T2 / 'color_v02.json', EVID / 'color_v02.json')
    # A/B: una sola variable (PSNR por zonas)
    rep['ab_una_variable'] = ab_psnr(mA, mB)
    json.dump(rep, open(EVID / 'control_v02.json', 'w'), ensure_ascii=False, indent=1)
    sonoridad_md(rep)
    print(json.dumps({k: rep['textos'][k] for k in ('mayuscula_px', 'mayuscula_si_1_5x_px', 'caja_alto_px', 'caja_ancho_pct')}, ensure_ascii=False))
    print('pop', {h: rep['textos']['pop'][h]['primer_cuadro_igual_a_c10'] for h in ('A', 'B')}, rep['textos']['pop']['A']['c0'])
    for k in ('A', 'A_sinmusica'):
        print(k, 'mín 0,5 s', rep['sonoridad_0_5s'][k]['minimo'], 'bajo −24:', rep['sonoridad_0_5s'][k]['bajo_menos_24'])
    print('validación', rep['sonoridad_0_5s']['validacion_contra_ebur128_M'])
    print('ebur128', rep['ebur128']); print('voces', rep['voces_mar_bajo'])
    for k in ('A', 'A_sinmusica'):
        print(k, 'M<−24 fuera del hueco 1', rep['sonoridad_0_5s'][k]['M_400ms_bajo_menos_24_fuera_hueco1'], rep['sonoridad_0_5s'][k]['tramos_dictamen'])
    print('AB', rep['ab_una_variable'])


def sonoridad_md(rep):
    s = rep['sonoridad_0_5s']
    L = ['# VIR-01 v02 · sonoridad por tramos de 0,5 s (LUFS, K-weighting BS.1770) · medido, no escuchado', '',
         'Tramos de la grilla de 120 BPM (0,5 s). La validación contra la M (400 ms) de ffmpeg ebur128 está en '
         '`control_v02.json` → sonoridad_0_5s.validacion_contra_ebur128_M. Objetivo del dictamen: ninguno por debajo de '
         '−24 salvo el hueco 1.', '', '| tramo (s) | v01 completa | **v02 completa** | v01 sin música | **v02 sin música** |',
         '|---|---|---|---|---|']
    for i, x in enumerate(s['A']['grilla']):
        L.append(f"| {x['tramo']} | {s['v01']['A'][i]['L']:.1f} | **{x['L']:.1f}** | {s['v01']['A_sinmusica'][i]['L']:.1f} | "
                 f"**{s['A_sinmusica']['grilla'][i]['L']:.1f}** |".replace('.', ','))
    (EVID / 'sonoridad_0.5s.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


def ab_psnr(mA, mB):
    import re
    S = T2 / 'ctrl'
    U.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(mA), '-i', str(mB), '-lavfi',
           f"[0:v]split[a1][a2];[1:v]split[b1][b2];[a1]crop=1080:1480:0:440[ab];[b1]crop=1080:1480:0:440[bb];"
           f"[ab][bb]psnr=stats_file={S}/psnr_bajo.txt;[a2]crop=1080:440:0:0[at];[b2]crop=1080:440:0:0[bt];"
           f"[at][bt]psnr=stats_file={S}/psnr_alto.txt", '-f', 'null', '-'])
    def load(f):
        out = []
        for l in open(f):
            n = int(re.search(r'n:(\d+)', l).group(1)); p = re.search(r'psnr_avg:(\S+)', l).group(1)
            out.append((n - 1, None if p == 'inf' else float(p)))
        return out
    b = load(S / 'psnr_bajo.txt'); a = load(S / 'psnr_alto.txt')
    fin = [x[1] for x in b if x[1] is not None]
    return dict(zona_y440_1920_todos=dict(psnr_min=min(fin) if fin else None, identicos=sum(1 for x in b if x[1] is None)),
                zona_y0_440_c0_c44_hook=dict(psnr_min=min(x[1] for x in a if x[0] <= 44 and x[1] is not None),
                                              psnr_max=max(x[1] for x in a if x[0] <= 44 and x[1] is not None)),
                zona_y0_440_c45_c317=dict(psnr_min=min((x[1] for x in a if x[0] >= 45 and x[1] is not None), default=None),
                                           identicos=sum(1 for x in a if x[0] >= 45 and x[1] is None)))


def etapa_control():
    B.etapa_control()
    control_v02()


def _huella(p, sha=True):
    d = dict(bytes=p.stat().st_size, md5_video=U.md5_stream(p, 'v'), md5_audio=U.md5_stream(p, 'a'))
    if sha:
        d['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
    return d


def etapa_entregar():
    destinos = []
    for k, nombre in B.NOMBRES.items():
        for d in (EXP / nombre, PIEZA / nombre):
            if d.exists():
                raise RuntimeError(f'{d} ya existe: no se sobrescribe')
            destinos.append((B.MAS / nombre, d))
    ev_red = PIEZA / 'evidencia_v02'
    if ev_red.exists():
        raise RuntimeError(f'{ev_red} ya existe')
    for src, d in destinos:
        shutil.copyfile(src, d)
    shutil.copytree(EVID, str(ev_red) + '/')
    time.sleep(12)                                   # montaje de red: esperar antes de verificar
    res = dict(local={}, exportaciones={}, pieza={})
    for k, nombre in B.NOMBRES.items():
        ref = _huella(B.MAS / nombre); res['local'][nombre] = ref
        e = _huella(EXP / nombre)
        res['exportaciones'][nombre] = dict(e, igual=(e == ref), decodifica=B._decodifica(EXP / nombre))
        p = _huella(PIEZA / nombre)
        res['pieza'][nombre] = dict(p, flujos_iguales=(p['md5_video'] == ref['md5_video'] and p['md5_audio'] == ref['md5_audio']),
                                    bytes_extra_c2pa=p['bytes'] - ref['bytes'], decodifica=B._decodifica(PIEZA / nombre))
        print(nombre, 'EXP', res['exportaciones'][nombre]['igual'], res['exportaciones'][nombre]['decodifica'],
              '| PIEZA flujos', res['pieza'][nombre]['flujos_iguales'], '+', res['pieza'][nombre]['bytes_extra_c2pa'],
              'B', res['pieza'][nombre]['decodifica'], flush=True)
    from PIL import Image
    loc = sorted(str(f.relative_to(EVID)) for f in EVID.rglob('*') if f.is_file())
    red = sorted(str(f.relative_to(ev_red)) for f in ev_red.rglob('*') if f.is_file())
    dist = []
    for f in loc:
        a, b = EVID / f, ev_red / f
        if not b.exists():
            continue
        if a.stat().st_size == b.stat().st_size and a.read_bytes() == b.read_bytes():
            continue
        if f.lower().endswith(('.jpg', '.png')):
            if np.array_equal(np.asarray(Image.open(a)), np.asarray(Image.open(b))):
                continue
        dist.append(f)
    res['evidencia'] = dict(carpeta=str(ev_red) + '/', archivos_local=len(loc), archivos_red=len(red),
                            faltan=[f for f in loc if f not in red], distintos=dist,
                            nota='los JPG/PNG de la red pesan más por la caja C2PA; se comparan los píxeles decodificados')
    print('evidencia', len(loc), len(red), res['evidencia']['faltan'], dist)
    json.dump(res, open(T2 / 'entrega.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    {'preparar': etapa_preparar, 'color': etapa_color, 'efectos': B.etapa_efectos, 'audio': B.etapa_audio,
     'master': etapa_master, 'control': etapa_control, 'entregar': etapa_entregar}[etapa]()
