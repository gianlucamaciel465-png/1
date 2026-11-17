#!/usr/bin/env python3
"""FMT-01 · «Perfil bajo» · receta del máster v01, hook A (Pedro, 17/11/2026).

Guion: piezas/FMT_tanda_formatos/FMT-01_perfil_bajo/01_fede_guion_G1.md (G1) + 02_roma_aprobacion_G1.md.
Usa scripts/fmt/video.py y scripts/fmt/sonido.py sin modificarlos, y las utilidades nuevas de fmt03.py
(plano_n / plano_z por cuadro de fuente, hojas con cuadro de fuente, medición del estampado, control y entrega).

Etapas: hojas → medir → planos → audio → master → control → entregar   (python fmt01.py <etapa>, con nice)

Desvío medido (indicación 3 de Roma): la manga beige de otra persona se ve en 4531 c12–c33 (0,400–1,100 s; hojas
4531_c14-c25_abajo_der_1a1.jpg, 4531_c22-c45_esquina_1a1.jpg, 4531_c25-c36_esquina_x3.jpg). Primer cuadro limpio:
c34 (1,133 s). Se aplica la alternativa de la aprobación: 4a arranca en c34 con sus 45 cuadros y 4b se acorta lo
mismo (22 cuadros); el final sigue en c116 (3,868 s) y el loop se mantiene. Máster: 278 cuadros = 9,267 s.
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V  # noqa: E402
import fmt03 as U  # noqa: E402  (utilidades de Pedro; no ejecuta nada al importarse)

R = Path('/home/user/1')
T = R / 'TRABAJO/fmt/fmt01'
P = T / 'planos'
M = T / 'med'
FPS = 30
FULL = (0, 0, 2160, 3840)
N4 = 34                       # primer cuadro de 4531 sin la manga beige (medido a 1:1)
N4_FIN = 116                  # último cuadro de 4b = cuadro anterior a 1a (4531 c117): loop
NF = 26 + 4 + 4 + 56 + 105 + (N4_FIN - N4 + 1)   # 278
DUR = NF / FPS
BLUR = 'avgblur=sizeX=32:sizeY=1'


def etapa_hojas():
    H = T / 'hojas'; H.mkdir(parents=True, exist_ok=True)
    pts = {t: U.tiempos_src(t) for t in ('IMG_4531', 'IMG_4530', 'IMG_7824')}
    n = lambda t, s: min(range(len(pts[t])), key=lambda i: abs(pts[t][i] - s))
    U.hoja_src('IMG_4531', n('IMG_4531', 3.3), n('IMG_4531', 4.9), H / '4531_3.3-4.9.jpg', cada=3, ancho=216, cols=9)
    U.hoja_src('IMG_4531', n('IMG_4531', 4.5), n('IMG_4531', 5.0), H / '4531_4.5-5.0_c1.jpg', cada=1, ancho=216, cols=8)
    U.hoja_src('IMG_4531', n('IMG_4531', 0.0), n('IMG_4531', 0.9), H / '4531_0.0-0.9_c1.jpg', cada=1, ancho=180, cols=14)
    U.hoja_src('IMG_4530', n('IMG_4530', 0.4), n('IMG_4530', 0.9), H / '4530_0.4-0.9_c1.jpg', cada=1, ancho=216, cols=8)
    U.hoja_src('IMG_7824', n('IMG_7824', 7.4), n('IMG_7824', 8.6), H / '7824_7.4-8.6.jpg', cada=3, ancho=216, cols=7)
    U.hoja_src('IMG_4531', n('IMG_4531', 3.7), n('IMG_4531', 4.0), H / '4531_loop_3.7-4.0_c1.jpg', cada=1, ancho=270, cols=10)
    U.hoja_src('IMG_7824', 180, 284, H / '7824_c180-c284_c6.jpg', cada=6, ancho=300, cols=9)
    json.dump({t: v for t, v in pts.items()}, open(H / 'pts.json', 'w'))


# =====================================================================================================
# etapa 2 · mediciones con numpy sobre las FUENTES (antes del render)
# =====================================================================================================
def src(toma, n0, n1, w=540, h=960, crop=None):
    pre = V.color(toma) + (f',crop={crop}' if crop else '')
    return U.leer(V._src(toma), w, h, n0=n0, n1=n1, vf_pre=pre)


def nitidez(L):
    """varianza del laplaciano (luma, float)"""
    lap = -4 * L[1:-1, 1:-1] + L[:-2, 1:-1] + L[2:, 1:-1] + L[1:-1, :-2] + L[1:-1, 2:]
    return float(lap.var())


def angulo(mask):
    """orientación (grados, positivo = baja hacia la derecha) del eje principal de una máscara"""
    ys, xs = np.nonzero(mask)
    x = xs - xs.mean(); y = ys - ys.mean()
    cxx, cyy, cxy = (x * x).mean(), (y * y).mean(), (x * y).mean()
    return float(np.degrees(0.5 * np.arctan2(2 * cxy, cxx - cyy)))


def logo_pecho(f):
    """caja del logo chico del pecho (1080×1920): píxeles oscuros y poco saturados rodeados de remera blanca
    (fracción de L > 170 en 61×61 > 0,6), componente más grande. Probado en c0, c25, c195, c240, c260, c277."""
    from scipy import ndimage as nd
    ff = f.astype(np.float32); L = U.luma(f); sat = (ff.max(-1) - ff.min(-1)) / (ff.max(-1) + 1)
    blanco = nd.uniform_filter((L > 170).astype(np.float32), 61) > 0.6
    osc = (L < 120) & (sat < 0.35) & blanco
    osc[:600] = False; osc[1400:] = False; osc[:, :300] = False
    lab, n = nd.label(nd.binary_dilation(osc, iterations=10)); s_ = nd.sum(osc, lab, range(1, n + 1))
    ys, xs = np.nonzero(osc & (lab == int(np.argmax(s_)) + 1))
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def mano_arriba(f):
    """caja de la mano que sostiene la remera arriba a la derecha (piel: R > 150, R−G > 30, R−B > 40; y < 1000,
    x > 600; la arena de la playa queda afuera por R−G)."""
    from scipy import ndimage as nd
    g = f[:1000].astype(np.int16); r, gg, b = g[..., 0], g[..., 1], g[..., 2]
    m = (r > 150) & (r - gg > 30) & (r - b > 40); m[:, :600] = False
    m = nd.binary_opening(m, iterations=2)
    lab, n = nd.label(m)
    if not n:
        return None
    s_ = nd.sum(m, lab, range(1, n + 1)); ys, xs = np.nonzero(lab == int(np.argmax(s_)) + 1)
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def etapa_medir():
    M.mkdir(parents=True, exist_ok=True)
    out = {}
    # --- 1) §7.2 · 7824 c180–c284 (plano 3, máster c90–c194): estampado de la Negra dentro del cuadro -------------
    fr = src('IMG_7824', 180, 284)                                       # 540×960 = cuadro del máster a 1/2
    res = U.seguir_estampado(fr, 'negra', (0, 380, 539, 640))
    U.dibujar_margenes(fr, res, M / 'margenes_7824_plano3.jpg', cada=3, ancho=180, cols=12, rotulo='m')
    filas = []
    for k, r in enumerate(res):
        filas.append(dict(master=90 + k, fuente=180 + k, bbox_1080=[2 * v for v in r['bbox']],
                          izq=2 * r['izq'], der=2 * r['der'], arr=2 * r['arr'], abj=2 * r['abj'],
                          founders_ancho_1080=2 * (r['founders'][2] - r['founders'][0]),
                          angulo_founders=round(angulo(r['mask']), 2)))
    mins = {k: min(f[k] for f in filas) for k in ('izq', 'der', 'arr', 'abj')}
    peor = {k: min(filas, key=lambda f: f[k])['master'] for k in mins}
    inc = [f for f in filas if 120 <= f['master'] <= 150]
    out['7824_plano3'] = dict(minimos_px_1080=mins, cuadro_master_del_minimo=peor,
                              minimos_c120_c150={k: min(f[k] for f in inc) for k in ('izq', 'der', 'arr', 'abj')},
                              por_cuadro=filas)
    print('7824 mínimos', mins, 'en', peor, '| c120–c150', out['7824_plano3']['minimos_c120_c150'], flush=True)
    ang = np.array([f['angulo_founders'] for f in filas]); anc = np.array([f['founders_ancho_1080'] for f in filas])
    va = np.abs(np.diff(ang))
    out['7824_inclinacion'] = dict(angulo_por_cuadro=[round(float(a), 2) for a in ang],
                                   ancho_founders_por_cuadro=[int(a) for a in anc],
                                   cuadro_master_angulo_max=int(90 + np.argmax(np.abs(ang))),
                                   cuadro_master_ancho_min=int(90 + np.argmin(anc)),
                                   cuadro_master_mayor_giro=int(91 + np.argmax(va)))
    print('7824 ángulo', out['7824_inclinacion']['cuadro_master_angulo_max'], 'ancho mín',
          out['7824_inclinacion']['cuadro_master_ancho_min'], 'mayor giro', out['7824_inclinacion']['cuadro_master_mayor_giro'])
    # --- 2) §7.1 · 4530 c14–c76: estampado de la Blanca completo y nítido (fuente) -------------------------------
    fr = src('IMG_4530', 14, 76)
    res = U.seguir_estampado(fr, 'blanca', (20, 430, 539, 640))
    U.dibujar_margenes(fr, res, M / 'margenes_4530.jpg', cada=1, ancho=150, cols=16, rotulo='c')
    full = src('IMG_4530', 14, 76, 1080, 1920)
    filas = []
    for k, r in enumerate(res):
        x0, y0, x1, y1 = [2 * v for v in r['bbox']]
        L = U.luma(full[k])[max(0, y0 - 10):y1 + 10, max(0, x0 - 10):x1 + 10]
        filas.append(dict(fuente=14 + k, master=(None if 14 + k < 17 else 30 + (14 + k - 17)),
                          bbox_1080=[x0, y0, x1, y1], izq=2 * r['izq'], der=2 * r['der'], arr=2 * r['arr'],
                          abj=2 * r['abj'], nitidez=round(nitidez(L), 1)))
    ref = float(np.median([f['nitidez'] for f in filas if f['fuente'] >= 30]))
    for f in filas:
        f['nitidez_rel'] = round(f['nitidez'] / ref, 3)
    out['4530'] = dict(nitidez_ref_mediana_c30_c76=round(ref, 1), por_cuadro=filas,
                       minimos_px_1080_c21_c76={k: min(f[k] for f in filas if f['fuente'] >= 21)
                                                for k in ('izq', 'der', 'arr', 'abj')})
    for f in filas[:16]:
        print('4530', f['fuente'], 'master', f['master'], 'márgenes', f['izq'], f['der'], f['arr'], f['abj'],
              'nitidez rel', f['nitidez_rel'])
    # --- 3) 4531: logo del pecho (movimiento en 3,9; posición) y loop c116 → c117 ------------------------------
    fr = src('IMG_4531', 100, 146, 1080, 1920)
    logo = []
    for k, f in enumerate(fr):
        b = logo_pecho(f)
        logo.append(dict(fuente=100 + k, cx=(b[0] + b[2]) / 2, cy=(b[1] + b[3]) / 2, bbox_1080=b))
    v = [round(math.hypot(logo[k + 1]['cx'] - logo[k]['cx'], logo[k + 1]['cy'] - logo[k]['cy']), 1) for k in range(len(logo) - 1)]
    out['4531_logo_pecho'] = dict(por_cuadro=logo, desplazamiento_px_por_cuadro=dict(zip(range(101, 147), v)))
    print('4531 logo px/cuadro c101–c146:', v)
    sm = src('IMG_4531', 30, 146, 270, 480).astype(np.float32)
    d = np.abs(np.diff(sm, axis=0)).mean(axis=(1, 2, 3))          # d[i] = |c(31+i) − c(30+i)|
    dd = {30 + i + 1: round(float(x), 2) for i, x in enumerate(d)}
    out['loop'] = dict(dif_c116_c117=dd[117], mediana_dif_consecutiva_c35_c146=round(float(np.median(d[4:])), 2),
                       p90=round(float(np.percentile(d[4:], 90)), 2), por_cuadro=dd)
    print('loop dif c116→c117', dd[117], 'mediana', out['loop']['mediana_dif_consecutiva_c35_c146'], 'p90', out['loop']['p90'])
    json.dump(out, open(M / 'mediciones.json', 'w'), ensure_ascii=False, indent=1)


# =====================================================================================================
# etapa 3 · planos (§2 del guion) + unión
# =====================================================================================================
def lista_planos():
    return [
        # id, función, args                                                                máster      fuente (s)
        ('1a', 'n', dict(toma='IMG_4531', n0=117, nf=26)),                                # c0–c25    3,902–4,736
        ('1b', 'z', dict(toma='IMG_4531', n0=143, zs=[1 + 0.15 * k / 3 for k in range(4)], cxs=540, cys=960,
                         post=BLUR)),                                                     # c26–c29   4,770–4,870
        ('2a', 'z', dict(toma='IMG_4530', n0=17, zs=[1.15 - 0.15 * k / 3 for k in range(4)], cxs=540, cys=960,
                         post=BLUR)),                                                     # c30–c33   0,567–0,667
        ('2b', 'n', dict(toma='IMG_4530', n0=21, nf=56)),                                 # c34–c89   0,700–2,535
        ('3', 'n', dict(toma='IMG_7824', n0=180, nf=105, caja=FULL)),                     # c90–c194  6,002–9,470
        ('4', 'n', dict(toma='IMG_4531', n0=N4, nf=N4_FIN - N4 + 1)),                     # c195–c277 1,133–3,868
    ]


def etapa_planos():
    P.mkdir(parents=True, exist_ok=True)
    reg = []
    for pid, tipo, a in lista_planos():
        out = P / f'{pid}.mp4'
        if tipo == 'n':
            p = U.plano_n(a['toma'], a['n0'], a['nf'], out, caja=a.get('caja'), post=a.get('post'))
        else:
            p = U.plano_z(a['toma'], a['n0'], a['zs'], a['cxs'], a['cys'], out, caja=a.get('caja'), post=a.get('post'))
        p['id'] = pid; reg.append(p); print(pid, p['cuadros'], flush=True)
    n = V.unir(reg, T / 'fmt01_video.mp4')
    assert n == NF, (n, NF)
    json.dump(dict(cuadros=n, planos=reg), open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1)
    print('total', n)
    mapa_cuadros()


def mapa_cuadros():
    """Indicación 6 de Roma: qué cuadro de FUENTE quedó en cada cuadro del máster (4530/4531 son 29,97 fps con saltos
    de 0,035 s). Para cada cuadro de los planos sin zoom se busca el cuadro de fuente más parecido entre n−2 y n+2."""
    out = {}
    m0 = 0
    for pid, tipo, a in lista_planos():
        nf = a.get('nf', len(a.get('zs', [])))
        if tipo == 'n':
            o = U.leer(P / f'{pid}.mp4', 270, 480).astype(np.float32)
            s = src(a['toma'], max(0, a['n0'] - 2), a['n0'] + nf + 2, 270, 480,
                    crop=None).astype(np.float32)
            base = max(0, a['n0'] - 2)
            mapa = []
            for k in range(nf):
                cand = range(max(0, k - 2 + (a['n0'] - base)), min(len(s), k + 3 + (a['n0'] - base)))
                err = {base + j: float(np.abs(o[k] - s[j]).mean()) for j in cand}
                j = min(err, key=err.get)
                mapa.append(dict(master=m0 + k, fuente=j, esperado=a['n0'] + k, err=round(err[j], 2)))
            rep = [x['master'] for i, x in enumerate(mapa) if i and x['fuente'] == mapa[i - 1]['fuente']]
            sal = [x['master'] for i, x in enumerate(mapa) if i and x['fuente'] - mapa[i - 1]['fuente'] > 1]
            out[pid] = dict(toma=a['toma'], cuadros_repetidos_master=rep, saltos_master=sal,
                            primero=mapa[0], ultimo=mapa[-1],
                            desvios=[x for x in mapa if x['fuente'] != x['esperado']], err_max=max(x['err'] for x in mapa))
            print(pid, 'repetidos', rep, 'saltos', sal, 'primero', mapa[0]['fuente'], 'último', mapa[-1]['fuente'],
                  'desvíos', len(out[pid]['desvios']), 'err máx', out[pid]['err_max'], flush=True)
        m0 += nf
    json.dump(out, open(T / 'mapa_cuadros.json', 'w'), ensure_ascii=False, indent=1)


# =====================================================================================================
# etapa 3b · degradé oscuro suave detrás de los textos blancos sobre cielo claro (regla de CLAUDE.md: «Texto sobre
# fondo claro (espuma, cielo): usar blanco con degradé oscuro suave detrás»). Medido en el video sin textos: el cielo
# detrás de «Perfil bajo…», «…hasta que la das vuelta.» y «Ya sabés…» tiene luma mediana ≈ 229 (relleno blanco ≈ 1,25:1).
# Solo en los planos de 4531/4530 (c0–c89 y c195–c277; los cambios caen en cortes y el loop queda igual): negro con
# alfa 0,38 hasta y 330 y fundido coseno a 0 en y 480. Manos y horizonte empiezan en y ≥ 531 (medido): no toca la prenda.
# Se aplica por número de cuadro sobre los planos YUV decodificados (no con overlay+enable: la imagen en bucle entra a
# 25 fps y «n» se corre 2–3 cuadros, y la conversión yuv→rgb→yuv oscurecía ≈ 1 nivel todo el cuadro; medido).
# =====================================================================================================
VID_DEG = T / 'fmt01_video_degrade.mp4'
DEG = dict(alfa=0.38, y_plano=330, y_cero=480, cuadros=[(0, 89), (195, NF - 1)])


def etapa_degrade():
    from PIL import Image
    a = np.zeros(1920, np.float32)
    y = np.arange(1920)
    a[y <= DEG['y_plano']] = DEG['alfa']
    t = (y - DEG['y_plano']) / (DEG['y_cero'] - DEG['y_plano'])
    m = (y > DEG['y_plano']) & (y < DEG['y_cero'])
    a[m] = DEG['alfa'] * 0.5 * (1 + np.cos(np.pi * t[m]))
    # en YUV de rango limitado, mezclar con negro (alfa a) es Y' = 16 + (Y − 16)(1 − a), U' = 128 + (U − 128)(1 − a):
    # se aplica sobre los planos decodificados (yuv420p, sin conversión de color) solo en los cuadros elegidos
    from PIL import Image
    Image.fromarray(np.round(a * 255).astype(np.uint8)[:, None].repeat(1080, 1)).save(T / 'degrade_alfa.png')
    W_, H_ = 1080, 1920; ny = W_ * H_; nc = ny // 4
    fy = (1 - a)[:, None]; fc = (1 - 0.5 * (a[0::2] + a[1::2]))[:, None]
    on = np.zeros(NF, bool)
    for a_, b_ in DEG['cuadros']:
        on[a_:b_ + 1] = True
    dec = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(T / 'fmt01_video.mp4'), '-f', 'rawvideo',
                            '-pix_fmt', 'yuv420p', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p',
                            '-s', f'{W_}x{H_}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-i', '-', *V.ENC_INT, str(VID_DEG)],
                           stdin=subprocess.PIPE)
    k = 0
    while True:
        b = dec.stdout.read(ny + 2 * nc)
        if len(b) < ny + 2 * nc:
            break
        if on[k]:
            f = np.frombuffer(b, np.uint8).astype(np.float32)
            Y = f[:ny].reshape(H_, W_); U_ = f[ny:ny + nc].reshape(H_ // 2, W_ // 2); V_ = f[ny + nc:].reshape(H_ // 2, W_ // 2)
            Y = 16 + (Y - 16) * fy; U_ = 128 + (U_ - 128) * fc; V_ = 128 + (V_ - 128) * fc
            b = np.concatenate([Y.ravel(), U_.ravel(), V_.ravel()]).round().clip(0, 255).astype(np.uint8).tobytes()
        enc.stdin.write(b); k += 1
    dec.stdout.close(); dec.wait(); enc.stdin.close(); enc.wait()
    assert k == NF and enc.returncode == 0, (k, enc.returncode)
    png = T / 'degrade_alfa.png'
    # comprobación: dónde cambió la imagen (filas y cuadros) respecto del video sin degradé
    a0 = U.leer(T / 'fmt01_video.mp4', 270, 480).astype(np.float32); a1 = U.leer(VID_DEG, 270, 480).astype(np.float32)
    d = (a0 - a1).mean(axis=(2, 3))                          # oscurecimiento medio por cuadro × fila (filas de 4 px);
    filas_cambiadas = {}                                       # el ruido de recodificar es de media 0
    for k in range(NF):
        r = np.nonzero(d[k] > 2.0)[0]
        filas_cambiadas[k] = [int(r.min()) * 4, int(r.max()) * 4 + 3] if len(r) else None
    con = [k for k, v in filas_cambiadas.items() if v]
    rep = dict(png=str(png), parametros=DEG, cuadros_con_cambio=[con[0], con[-1]] if con else None,
               cuadros_con_cambio_lista=con, y_max_cambiada=max(v[1] for v in filas_cambiadas.values() if v),
               osc_medio_bajo_y480=round(float((a0 - a1)[:, 120:].mean()), 3),
               dif_abs_media_bajo_y480_recodificacion=round(float(np.abs(a1 - a0)[:, 120:].mean()), 3),
               osc_max_fila_bajo_y480=round(float(d[:, 120:].max()), 2),
               osc_max_c90_c194=round(float(d[90:195].max()), 2))
    json.dump(rep, open(T / 'degrade.json', 'w'), ensure_ascii=False, indent=1)
    print({k: v for k, v in rep.items() if k != 'cuadros_con_cambio_lista'}, 'n cuadros con cambio', len(con))


# =====================================================================================================
# etapa 4 · sonido (§5 del guion; música TEMP propia 120 BPM Mi menor; foley de tela PROVISORIO)
# =====================================================================================================
T_INCL = 4.40   # tela de la inclinación de la Negra: máster c132 = 7824 c222 (7,40 s). Medido: el ancho visible de
                # Founders cae más rápido en c132→c135 (−54 px) y el ángulo salta en c135→c138; el guion decía 4,50.


def ambientes(m):
    m.ambiente('IMG_4531', 3.90, 0.0, 1.0, -4, hp=120)
    m.ambiente('IMG_4530', 0.567, 1.0, 3.0, -4, hp=120)
    m.ambiente('IMG_7824', 6.00, 3.0, 6.5, -6, hp=150, lp=8000)
    # 4a–4b: el video es 4531 1,133–3,868 (con charla en su audio); el ambiente sale de 4531 3,90–6,67, sin voz
    # (espectrograma IMG_4531_espectro.png: voz con armónicos en 0,2–1,1 y 2,3–3,3 s; nada de eso desde 3,4 s)
    m.ambiente('IMG_4531', 3.90, 6.5, DUR, -4, hp=120, fin_fade=.25)


def foley(m):
    m.tela(0.867, .22, .22)          # el giro (c26)
    m.barrido(1.00, .25, .20)
    m.tela(T_INCL, .40, .10)         # la Negra se inclina


def musica(m):
    ch = lambda t0, t1, g: [m.charles(round(float(t), 3), g) for t in np.arange(t0, t1 - 1e-6, 0.25)]
    # entrada c0–c29
    m.pad(0.0, [52, 55, 59], .95, .04, 900, a=.1)
    for t in (0, .25, .5, .75):
        m.charles(t, .05)
    m.campana(0.0, 71, .05)
    # giro c30
    m.bombo(1.0, .95); m.ocho08(1.0, 40, .9, .55, glide_desde=47); m.impacto(1.0, .35)
    m.pad(1.0, [52, 55, 59], .95, .06); m.pad(2.0, [48, 52, 55], .95, .06)
    m.bombo(2.0, .6); m.bombo(2.75, .6)
    m.palma(1.5); m.palma(2.5)
    ch(1.0, 3.0, .08)
    m.ocho08(2.0, 36, .45); m.ocho08(2.5, 38, .45)
    # «bajito» c90–c194
    m.pad(3.0, [52, 55, 59], 1.95, .035, 600); m.pad(5.0, [45, 48, 52], 1.45, .035, 600)
    for t in (3.0, 4.0, 5.0, 6.0):
        m.bombo(t, .45, f0=90)
    m.ocho08(3.0, 40, .9, .30)
    # vuelta c195
    m.palma(6.5); ch(6.5, 9.5, .08)
    m.bombo(7.0, .9); m.ocho08(7.0, 43, .45); m.pad(7.0, [43, 47, 50], .95, .06)
    m.palma(7.5)
    # CTA c240
    m.bombo(8.0, .9); m.ocho08(8.0, 45, .45); m.pad(8.0, [45, 48, 52], .95, .06); m.campana(8.0, 76, .06)
    m.palma(8.5)
    # final c270 (la pieza termina en c277: la palma de 9,5 queda afuera)
    m.bombo(9.0, .9); m.ocho08(9.0, 40, .9, .5); m.pad(9.0, [52, 55, 59, 64], .9, .06, r=.5)
    m.palma(9.5, .25)
    # huecos y final (después de colocar todo)
    m.silenciar('mus', 0.933, 1.000)
    # guion: fundido('mus', 9.55, 10.00) para 10,000 s. Con 9,267 s: el golpe de c270 entero y fundido de su cola
    # hasta el último cuadro (también el bombo, para no cortar seco su decaimiento)
    m.fundido('mus', 9.05, DUR); m.fundido('bombo', 9.05, DUR)


def etapa_audio():
    from sonido import Mezcla
    A = T / 'audio'; A.mkdir(exist_ok=True)
    m = Mezcla(DUR); ambientes(m); foley(m); musica(m)
    r1 = m.exportar(str(A / 'fmt01_completa.wav'), lufs=-14)
    s = Mezcla(DUR); ambientes(s); foley(s)              # sin música: solo ambiente, tela y barrido
    r2 = s.exportar(str(A / 'fmt01_sinmusica.wav'), lufs=-14)
    print('completa', r1, 'sin música', r2)


# =====================================================================================================
# etapa 5 · textos exactos (§4) + máster (en TRABAJO; la entrega copia después del control)
# =====================================================================================================
NOMBRES = {'completa': 'ROCCE_FMT01_PERFIL_BAJO_v01.mp4', 'sinmusica': 'ROCCE_FMT01_PERFIL_BAJO_SINMUSICA_v01.mp4'}
MAS = T / 'master'
TEXTOS = [
    dict(t0=0 / FPS, t1=90 / FPS, txt='Perfil bajo…', estilo='Nativo', y=250, pop=True),                          # c0–c89
    dict(t0=34 / FPS, t1=90 / FPS, txt='…hasta que la das vuelta.', estilo='Nativo', y=330, pop=True),            # c34–c89
    dict(t0=90 / FPS, t1=180 / FPS, txt='Y la Negra lo dice bajito.', estilo='Nativo', y=250),                    # c90–c179
    dict(t0=195 / FPS, t1=240 / FPS, txt='Ya sabés\\Nlo que tiene atrás.', estilo='Nativo', y=250),               # c195–c239
    dict(t0=240 / FPS, t1=NF / FPS, txt='Pasáselo al más perfil bajo\\Nque conocés.', estilo='Caja', y=250),      # c240–c277
]
# cuadros de entrada/salida de cada texto (para comprobar en el máster que no hay corrimiento de un cuadro)
LIMITES_TEXTO = [(0, 89), (34, 89), (90, 179), (195, 239), (240, NF - 1)]


def etapa_master():
    MAS.mkdir(exist_ok=True)
    a = V.ass(TEXTOS, T / 'fmt01_textos.ass')
    for k, nombre in NOMBRES.items():
        V.master(VID_DEG, T / 'audio' / f'fmt01_{k}.wav', MAS / nombre, ass_path=a)
        print('->', MAS / nombre)


# =====================================================================================================
# etapa 6 · control y evidencia (U.control + comprobaciones propias de FMT-01)
# =====================================================================================================
EVID = T / 'evidencia_v01'
VID = VID_DEG                       # mismo video sin textos, con el degradé (referencia para medir los textos)


def extra_fmt01():
    from PIL import Image, ImageDraw, ImageFont
    S = T / 'ctrl'; S.mkdir(exist_ok=True)
    f0 = MAS / NOMBRES['completa']
    fnt = ImageFont.truetype(U.FONT, 26)
    out = {}
    # --- textos: presencia en el primer y último cuadro pedidos (y ausencia en el anterior y el siguiente) ---------
    # máscara de cada texto (libass, ese texto solo, en su cuadro medio, dilatada 8 px). En cada cuadro de borde se
    # mide |máster − video sin textos| en los píxeles de ESE texto que no tocan otro texto que deba verse ahí.
    from scipy import ndimage as nd
    mascaras = []
    for i, (a, b) in enumerate(LIMITES_TEXTO):
        p1 = S / f'texto_{i}.ass'; V.ass([TEXTOS[i]], p1)
        r = U.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=black:s=1080x1920:r=30:d=11', '-vf',
                   f"subtitles={p1}:fontsdir=/usr/share/fonts/opentype/inter,trim=start={(a + b) / 2 / FPS:.4f},"
                   f"setpts=PTS-STARTPTS,format=gray", '-frames:v', '1', '-f', 'rawvideo', '-'])
        mascaras.append(nd.binary_dilation(np.frombuffer(r, np.uint8).reshape(1920, 1080) > 8, iterations=8))
    filas = []
    for i, (a, b) in enumerate(LIMITES_TEXTO):
        for n in (a - 1, a, b, b + 1):
            if n < 0 or n >= NF:
                continue
            otros = [j for j, (aa, bb) in enumerate(LIMITES_TEXTO) if j != i and aa <= n <= bb]
            mk = mascaras[i].copy()
            for j in otros:
                mk &= ~nd.binary_dilation(mascaras[j], iterations=8)
            m_ = U.leer(f0, 1080, 1920, n0=n, n1=n)[0].astype(np.float32)
            v_ = U.leer(VID, 1080, 1920, n0=n, n1=n)[0].astype(np.float32)
            d = float(np.abs(m_ - v_)[mk].mean())
            filas.append(dict(texto=TEXTOS[i]['txt'], pedido=f'c{a}–c{b}', cuadro=n, pixeles_medidos=int(mk.sum()),
                              dif_media=round(d, 2), visible=d > 4, debe_verse=a <= n <= b))
    out['textos_limites'] = filas
    out['textos_ok'] = all(f['visible'] == f['debe_verse'] for f in filas)
    cajas = U.cajas_texto(T / 'fmt01_textos.ass', [(a + b) / 2 / FPS for a, b in LIMITES_TEXTO])
    # contraste de los textos Nativo sobre cielo claro: luma del fondo dentro de la caja
    out['fondo_textos_luma'] = {}
    for i, (a, b) in enumerate(LIMITES_TEXTO):
        ys, xs = np.nonzero(mascaras[i]); caja = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        L = U.luma(U.leer(VID, 1080, 1920, n0=(a + b) // 2, n1=(a + b) // 2)[0])[mascaras[i]]
        out['fondo_textos_luma'][TEXTOS[i]['txt']] = dict(caja_dilatada=caja, mediana=round(float(np.median(L)), 1),
                                                          p10=round(float(np.percentile(L, 10)), 1),
                                                          p90=round(float(np.percentile(L, 90)), 1))
    # --- §7.1 · la espalda en c30 y nítida: estampado celeste presente y nitidez relativa al 4530 limpio ----------
    med = json.load(open(M / 'mediciones.json'))
    ref = med['4530']['nitidez_ref_mediana_c30_c76']
    cajas_src = {f_['fuente']: f_['bbox_1080'] for f_ in med['4530']['por_cuadro']}
    zs2a = [1.15 - 0.15 * k / 3 for k in range(4)]
    vv = U.leer(VID, 1080, 1920, n0=26, n1=40)
    esp = []
    for k, f in enumerate(vv):
        n = 26 + k
        ff = f.astype(np.float32); L = U.luma(f)
        cel = (ff[..., 2] - ff[..., 0] > 20) & (ff[..., 2] - ff[..., 1] > 4) & (L > 105) & (L < 240)
        nit = None
        if n >= 30:
            x0, y0, x1, y1 = cajas_src[17 + (n - 30)]
            z = zs2a[n - 30] if n < 34 else 1.0
            x0, x1 = [int(round((x - 540) * z + 540)) for x in (x0, x1)]
            y0, y1 = [int(round((y - 960) * z + 960)) for y in (y0, y1)]
            nit = round(nitidez(L[max(0, y0 - 10):y1 + 10, max(0, x0 - 10):x1 + 10]) / ref, 3)
        esp.append(dict(cuadro=n, pixeles_celestes=int(cel[400:1400].sum()), nitidez_rel_4530=nit))
    out['espalda_c26_c40'] = esp
    # --- §7.3 · loop c277 → c0 y CTA lejos del logo del pecho y de las manos ---------------------------------------
    a = U.leer(VID, 270, 480).astype(np.float32)
    d = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2, 3))           # d[i] = |c(i+1) − c(i)|
    dl = float(np.abs(a[-1] - a[0]).mean())
    plano4 = d[195:NF - 1]
    out['loop'] = dict(dif_c277_c0=round(dl, 2), mediana_dif_plano4=round(float(np.median(plano4)), 2),
                       p90_plano4=round(float(np.percentile(plano4, 90)), 2), max_plano4=round(float(plano4.max()), 2))
    out['cuadros_casi_iguales_al_anterior'] = [(i + 1, round(float(x), 2)) for i, x in enumerate(d) if x < 0.8]
    cta = cajas[f'{(240 + NF - 1) / 2 / FPS:.3f}']
    cta_fil = []
    for n in range(240, NF, 1):
        f = U.leer(VID, 1080, 1920, n0=n, n1=n)[0] if n % 4 == 0 or n == NF - 1 else None
        if f is None:
            continue
        logo = logo_pecho(f); mano = mano_arriba(f)
        cta_fil.append(dict(cuadro=n, logo_pecho_bbox=logo, mano_arriba_bbox=mano,
                            sep_cta_logo_px=logo[1] - cta[3], sep_cta_mano_px=(mano[1] - cta[3]) if mano else None))
    out['cta'] = dict(caja=cta, por_cuadro=cta_fil, sep_min_logo=min(f['sep_cta_logo_px'] for f in cta_fil),
                      sep_min_mano=min(f['sep_cta_mano_px'] for f in cta_fil if f['sep_cta_mano_px'] is not None))
    # --- color: blanco y negro de las remeras y celeste contra PRODUCTO/ ------------------------------------------
    prod = {}
    for nom in ('blanca_frente_estudio', 'blanca_frente_detalle_estampado', 'blanca_espalda_estudio', 'negra_espalda_estudio'):
        V.foto_srgb(R / 'PRODUCTO' / f'{nom}.jpg', S / f'{nom}_srgb.png')
        prod[nom] = np.asarray(Image.open(S / f'{nom}_srgb.png').convert('RGB'))
    fr = {n: U.leer(f0, 1080, 1920, n0=n, n1=n)[0] for n in (10, 60, 100, 230)}
    col = dict(
        producto_blanca_frente_detalle=U.color_parche(prod['blanca_frente_detalle_estampado'], (400, 150, 1100, 500)),
        producto_blanca_espalda=U.color_parche(prod['blanca_espalda_estudio'], (292, 1316, 877, 1755)),
        master_blanca_frente_4531_c10=U.color_parche(fr[10], (100, 1000, 500, 1400)),
        master_blanca_frente_4531_c230=U.color_parche(fr[230], (150, 1150, 550, 1500)),
        master_blanca_espalda_4530_c60=U.color_parche(fr[60], (150, 1200, 600, 1450)),
        producto_negra_espalda=U.color_parche(prod['negra_espalda_estudio'], (292, 1228, 877, 1462)),
        master_negra_espalda_7824_c100=U.color_parche(fr[100], (150, 1000, 650, 1250)))

    def celeste(img, caja):
        import colorsys
        x0, y0, x1, y1 = caja; p = img[y0:y1, x0:x1].reshape(-1, 3).astype(np.float64)
        m_ = (p[:, 2] - p[:, 0] > 20) & (p[:, 2] - p[:, 1] > 4)
        q = p[m_].mean(0); h, l_, s_ = colorsys.rgb_to_hls(*(q / 255))
        return dict(pixeles=int(m_.sum()), rgb=[round(x, 1) for x in q], tono_grados=round(h * 360, 1))
    col['celeste_producto_espalda'] = celeste(prod['blanca_espalda_estudio'], (100, 800, 1100, 1300))
    col['celeste_master_4530_c60'] = celeste(fr[60], (0, 650, 1080, 1150))
    out['color'] = col
    # --- fidelidad del logo del pecho: máster (1a y 4) al lado del producto -----------------------------------------
    tiles = []
    for n in (10, 230):
        f = fr[n]; b = logo_pecho(f)
        x0, y0, x1, y1 = b[0] - 30, b[1] - 30, b[2] + 30, b[3] + 30
        im = Image.fromarray(f[y0:y1, x0:x1]); im = im.resize((im.width * 4, im.height * 4), Image.LANCZOS)
        tiles.append((f'máster c{n} (4531, 1:1 ampliado ×4, Lanczos)', im))
    pd = Image.fromarray(prod['blanca_frente_detalle_estampado'][800:1500, 120:1500])
    pd.thumbnail((tiles[0][1].width, 10_000)); tiles.append(('PRODUCTO/blanca_frente_detalle_estampado.jpg (sRGB)', pd))
    pe = Image.fromarray(prod['blanca_frente_estudio']); pe.thumbnail((540, 760))
    fe = Image.fromarray(fr[10]).resize((428, 760))
    Wd = max(t.width for _, t in tiles) + 20
    Hh = sum(t.height + 50 for _, t in tiles) + 820
    hoja = Image.new('RGB', (max(Wd, 1000), Hh), (24, 24, 24)); d_ = ImageDraw.Draw(hoja); yy = 0
    for txt, t in tiles:
        d_.text((10, yy + 8), txt, font=fnt, fill=(255, 255, 0)); hoja.paste(t, (10, yy + 45)); yy += t.height + 50
    d_.text((10, yy + 8), 'posición: PRODUCTO/blanca_frente_estudio.jpg | máster c10', font=fnt, fill=(255, 255, 0))
    hoja.paste(pe, (10, yy + 45)); hoja.paste(fe, (20 + pe.width, yy + 45))
    hoja.save(EVID / 'logo_pecho_vs_producto.jpg', quality=92)
    # --- manga beige: dónde queda en el plano 4 del máster (esquina inferior derecha, 1:1) -------------------------
    ns = list(range(232, 262, 2))
    cs = U.leer(f0, 1080, 1920, n0=ns[0], n1=ns[-1])[::2]
    tira = Image.new('RGB', (5 * 302, 3 * 222), (30, 30, 30)); d_ = ImageDraw.Draw(tira)
    for i, (n, f) in enumerate(zip(ns, cs)):
        t = Image.fromarray(f[1700:1920, 780:1080]); dd = ImageDraw.Draw(t)
        dd.rectangle([0, 0, 62, 24], fill=(0, 0, 0)); dd.text((4, 2), f'c{n}', font=ImageFont.truetype(U.FONT, 18), fill=(255, 255, 0))
        tira.paste(t, ((i % 5) * 302, (i // 5) * 222))
    tira.save(EVID / 'manga_beige_master_c232-c260_esquina_1a1.jpg', quality=92)
    # --- Founders Privée de la Negra: tapado por el pliegue (no por el borde) en la inclinación ---------------------
    ns = [120, 126, 132, 138, 150, 162, 174, 180]
    t2 = Image.new('RGB', (4 * 542, 2 * 302), (30, 30, 30))
    for i, n in enumerate(ns):
        f = U.leer(f0, 1080, 1920, n0=n, n1=n)[0]
        t = Image.fromarray(f[700:1300, 0:1080]).resize((540, 300)); dd = ImageDraw.Draw(t)
        dd.rectangle([0, 0, 70, 26], fill=(0, 0, 0)); dd.text((4, 2), f'c{n}', font=ImageFont.truetype(U.FONT, 20), fill=(255, 255, 0))
        t2.paste(t, ((i % 4) * 542, (i // 4) * 302))
    t2.save(EVID / 'negra_founders_pliegue_c120-c180.jpg', quality=92)
    out['mediciones'] = dict(
        plano3_7824_minimos_px=med['7824_plano3']['minimos_px_1080'],
        plano3_7824_cuadro_del_minimo=med['7824_plano3']['cuadro_master_del_minimo'],
        plano3_7824_minimos_c120_c150=med['7824_plano3']['minimos_c120_c150'],
        plano2b_4530_minimos_px=med['4530']['minimos_px_1080_c21_c76'],
        loop_fuente=dict((k, med['loop'][k]) for k in ('dif_c116_c117', 'mediana_dif_consecutiva_c35_c146', 'p90')))
    out['mapa_cuadros'] = {k: dict((kk, v[kk]) for kk in ('toma', 'cuadros_repetidos_master', 'saltos_master', 'err_max'))
                           | dict(primero=v['primero']['fuente'], ultimo=v['ultimo']['fuente'])
                           for k, v in json.load(open(T / 'mapa_cuadros.json')).items()}
    return out


def etapa_control():
    import shutil
    EVID.mkdir(parents=True, exist_ok=True)
    tramos = [('1 frente Blanca + barrido (4531)', 0.0, 1.0), ('2 espalda Blanca (4530)', 1.0, 3.0),
              ('3 Negra «bajito» (7824)', 3.0, 6.5), ('4a vuelve el frente (4531)', 6.5, 8.0),
              ('4b CTA (4531)', 8.0, DUR), ('último 0,5 s', DUR - 0.5, DUR)]
    rep = U.control(NOMBRES, EVID, [26, 30, 34, 90, 195, 240], NF - 1, tramos, T / 'fmt01_textos.ass', TEXTOS,
                    [1.5, 4.5, 7.0, 8.5], extra=extra_fmt01, carpeta=MAS)
    for f in ('margenes_7824_plano3.jpg', 'margenes_4530.jpg', 'mediciones.json', 'barrido_c24-c37.jpg'):
        shutil.copy2(M / f, EVID / f)
    H = T / 'hojas'
    for f in ('4531_0.0-0.9_c1.jpg', '4531_abajo_c12-c116.jpg', '4531_c14-c25_abajo_der_1a1.jpg',
              '4531_c22-c45_esquina_1a1.jpg', '4531_c25-c36_esquina_x3.jpg', '4531_c74-c99_esquina_1a1.jpg',
              '4531_c32-c117_franja_inferior.jpg', '4531_3.3-4.9.jpg', '4531_4.5-5.0_c1.jpg', '4531_loop_3.7-4.0_c1.jpg',
              '4530_0.4-0.9_c1.jpg', '7824_7.4-8.6.jpg', '7824_c180-c284_c6.jpg'):
        shutil.copy2(H / f, EVID / f'hoja_fuente_{f}')
    for f in ('IMG_4531_espectro.png', 'IMG_4530_espectro.png'):
        shutil.copy2(T / 'audio' / f, EVID / f'espectro_{f}')
    for k in ('completa', 'sinmusica'):
        shutil.copy2(T / 'audio' / f'fmt01_{k}_eventos.json', EVID / f'audio_eventos_{k}.json')
    shutil.copy2(T / 'planos.json', EVID / 'planos.json'); shutil.copy2(T / 'mapa_cuadros.json', EVID / 'mapa_cuadros.json')
    shutil.copy2(T / 'degrade.json', EVID / 'degrade.json'); shutil.copy2(T / 'degrade_alfa.png', EVID / 'degrade_alfa.png')
    print(json.dumps({k: v for k, v in rep.items() if k not in ('archivos',)}, ensure_ascii=False)[:6000])


# =====================================================================================================
# etapa 7 · entrega: EXPORTACIONES/ + carpeta de la pieza + evidencia; verificación de las copias (fmt03.entregar)
# =====================================================================================================
PIEZA = Path('/mnt/project-files/piezas/FMT_tanda_formatos/FMT-01_perfil_bajo')


def etapa_entregar():
    r = U.entregar(NOMBRES, MAS, EVID, PIEZA)
    json.dump(r, open(T / 'entrega.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    {'hojas': etapa_hojas, 'medir': etapa_medir, 'planos': etapa_planos, 'mapa': mapa_cuadros, 'audio': etapa_audio,
     'degrade': etapa_degrade, 'master': etapa_master, 'control': etapa_control, 'entregar': etapa_entregar}[etapa]()
