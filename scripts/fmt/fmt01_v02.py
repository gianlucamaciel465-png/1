#!/usr/bin/env python3
"""FMT-01 · «Perfil bajo» · receta del máster v02, hook A (Pedro, 17/11/2026).

Dictamen: piezas/FMT_tanda_formatos/FMT-01_perfil_bajo/04_roma_dictamen_master_v01.md. Se conserva el montaje de v01
(planos 1a, 1b, 2a, 2b y 3 son los mismos archivos de TRABAJO/fmt/fmt01/planos/); cambia:
  1. plano 4 desde 4531 c12 (0,400 s) como el guion: 4 = 4531 c12–c116 (105 cuadros), máster 300 cuadros = 10,000 s;
     «Ya sabés…» c195–c239 y CTA c240–c299 (2,0 s). Roma acepta la mano con puño beige (esquina inferior);
  2. degradé corto detrás de «Y la Negra lo dice bajito.» que termina ≥ 20 px por encima del punto más alto de las
     manos (y de la remera) en c90–c194; el degradé de v01 sigue en c0–c89 y c195–c299 (ajustado por cuadro);
  3. +8 dB a la entrada (pad, charles y campana de 0–1,0 s) y ambiente de 7824 a 0 dB (era −6), sin pozos en «bajito»;
  4. muesca angosta en la banda de ≈ 500 Hz del ambiente de 4530/4531 si es un tono estacionario (etapa banda500);
  5. fundido de música 9,55–10,00 y palma de 9,5 como el guion; loop 4531 c116 → c117.
Usa video.py y sonido.py sin modificarlos, fmt03.py / fmt01.py (v01) y las utilidades de fmt03_v02.py.

Etapas (python fmt01_v02.py <etapa>, con nice -n 10):
  planos → medir → banda500 → degrade → audio → master → control → entregar
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V  # noqa: E402
import fmt03 as U  # noqa: E402
import fmt01 as F  # noqa: E402
import fmt03_v02 as W  # noqa: E402

R = U.R
T = F.T                        # TRABAJO/fmt/fmt01 (v01)
T2 = T / 'v02'
P2 = T2 / 'planos'
FPS = 30
N4, N4_FIN = 12, 116           # guion: 4a/4b = 4531 0,400–3,900 (c12–c116); c116 → c117 (1a) es el loop
NF = 26 + 4 + 4 + 56 + 105 + (N4_FIN - N4 + 1)   # 300
DUR = NF / FPS                 # 10,000 s
VID0 = T2 / 'fmt01_video.mp4'  # sin textos ni degradé
VID = T2 / 'fmt01_video_degrade.mp4'


# =====================================================================================================
# etapa 1 · plano 4 nuevo + unión con los planos de v01 + mapa de cuadros de fuente
# =====================================================================================================
def mapa_plano(toma, n0, nf, archivo, m0):
    """qué cuadro de FUENTE quedó en cada cuadro del plano (el más parecido entre n−2 y n+2), como fmt01.mapa_cuadros."""
    o = U.leer(archivo, 270, 480).astype(np.float32)
    base = max(0, n0 - 2)
    s = F.src(toma, base, n0 + nf + 2, 270, 480).astype(np.float32)
    mapa = []
    for k in range(nf):
        cand = range(max(0, k - 2 + (n0 - base)), min(len(s), k + 3 + (n0 - base)))
        err = {base + j: float(np.abs(o[k] - s[j]).mean()) for j in cand}
        j = min(err, key=err.get)
        mapa.append(dict(master=m0 + k, fuente=j, esperado=n0 + k, err=round(err[j], 2)))
    rep = [x['master'] for i, x in enumerate(mapa) if i and x['fuente'] == mapa[i - 1]['fuente']]
    sal = [x['master'] for i, x in enumerate(mapa) if i and x['fuente'] - mapa[i - 1]['fuente'] > 1]
    return dict(toma=toma, cuadros_repetidos_master=rep, saltos_master=sal, primero=mapa[0], ultimo=mapa[-1],
                desvios=[x for x in mapa if x['fuente'] != x['esperado']], err_max=max(x['err'] for x in mapa))


def etapa_planos():
    P2.mkdir(parents=True, exist_ok=True)
    p4 = U.plano_n('IMG_4531', N4, N4_FIN - N4 + 1, P2 / '4.mp4')
    p4['id'] = '4'
    v1 = json.load(open(T / 'planos.json'))['planos']
    reg = [p for p in v1 if p['id'] != '4'] + [p4]
    assert [p['id'] for p in reg] == ['1a', '1b', '2a', '2b', '3', '4']
    n = V.unir(reg, VID0)
    assert n == NF, (n, NF)
    json.dump(dict(cuadros=n, planos=reg), open(T2 / 'planos.json', 'w'), ensure_ascii=False, indent=1)
    # mapa: planos sin zoom de v01 (mismos archivos) + plano 4 nuevo
    mapa = {k: v for k, v in json.load(open(T / 'mapa_cuadros.json')).items() if k != '4'}
    mapa['4'] = mapa_plano('IMG_4531', N4, N4_FIN - N4 + 1, P2 / '4.mp4', 195)
    json.dump(mapa, open(T2 / 'mapa_cuadros.json', 'w'), ensure_ascii=False, indent=1)
    m4 = mapa['4']
    print('total', n, '| plano 4: primero', m4['primero'], 'último', m4['ultimo'], 'repetidos', m4['cuadros_repetidos_master'],
          'saltos', m4['saltos_master'], 'desvíos', len(m4['desvios']), 'err máx', m4['err_max'])


# =====================================================================================================
# etapa 2 · mediciones para el degradé (topes de lo que no es cielo; manos y remera en el plano 3)
# =====================================================================================================
def tope_no_cielo(f, x0=100, x1=980, umbral=30, frac=0.02, ref=(0, 150)):
    """primera fila (desde arriba) donde más de `frac` de los píxeles de x0–x1 se apartan > `umbral` niveles del color
    del cielo de ese cuadro (mediana de las filas ref): horizonte, mar, edificios, manos o remera. Conservador."""
    g = f[:, x0:x1].astype(np.int16)
    cielo = np.median(g[ref[0]:ref[1]].reshape(-1, 3), 0)
    d = np.abs(g - cielo).max(-1) > umbral
    fila = d.mean(1) > frac
    fila = fila & np.r_[fila[1:], False] & np.r_[fila[2:], False, False]     # 3 filas seguidas
    r = np.nonzero(fila[ref[1]:])[0]
    return int(r[0]) + ref[1] if len(r) else None


def manos_plano3(f):
    """punto más alto de manos (piel) y de la remera (tela oscura L < 60) en 7824, componentes > 3000 px."""
    from scipy import ndimage as nd
    g = f.astype(np.int16); r, gg, b = g[..., 0], g[..., 1], g[..., 2]
    out = {}
    for nom, m in (('piel', (r > 120) & (r - gg > 25) & (r - b > 35)), ('tela', U.luma(f) < 60)):
        m = nd.binary_opening(m, iterations=2)
        lab, k = nd.label(m)
        s = nd.sum(m, lab, range(1, k + 1)) if k else []
        big = [i + 1 for i, v in enumerate(s) if v > 3000]
        if big:
            ys, xs = np.nonzero(np.isin(lab, big)); i = int(np.argmin(ys))
            out[nom] = dict(y=int(ys[i]), x=int(xs[i]))
        else:
            out[nom] = None
    return out


def etapa_medir():
    T2.mkdir(parents=True, exist_ok=True)
    out = {'cielo': {}, 'plano3': {}}
    for a, b in ((0, 89), (195, NF - 1)):
        for k0 in range(a, b + 1, 30):
            k1 = min(b, k0 + 29)
            fr = U.leer(VID0, 1080, 1920, n0=k0, n1=k1)
            for k, f in enumerate(fr):
                # tope_no_cielo en x 100–980 incluye los edificios de la izquierda; en x 350–1080 da el horizonte (o
                # la mano); la piel da las manos en todo el ancho
                pi = manos_plano3(f)['piel']
                out['cielo'][k0 + k] = dict(no_cielo=tope_no_cielo(f), horizonte_x350=tope_no_cielo(f, 350, 1080),
                                            piel=pi['y'] if pi else None)
            del fr
    for k0 in range(90, 195, 35):
        fr = U.leer(VID0, 1080, 1920, n0=k0, n1=min(194, k0 + 34))
        for k, f in enumerate(fr):
            out['plano3'][k0 + k] = manos_plano3(f)
        del fr
    c = out['cielo']
    p3 = out['plano3']
    barrido = range(26, 34)                    # 1b + 2a (desenfoque horizontal: el horizonte se corre hacia arriba)
    ym = lambda n: min(v['y'] for v in p3[n].values() if v)
    n_min = min(p3, key=ym)
    out['resumen'] = dict(
        no_cielo_min_c0_c89=min(v['no_cielo'] for k, v in c.items() if k <= 89 and v['no_cielo'] is not None),
        no_cielo_min_c195_c299=min(v['no_cielo'] for k, v in c.items() if k >= 195 and v['no_cielo'] is not None),
        horizonte_min_c0_c89_sin_barrido=min(v['horizonte_x350'] for k, v in c.items() if k <= 89 and k not in barrido),
        horizonte_min_barrido_c26_c33=min(v['horizonte_x350'] for k, v in c.items() if k in barrido),
        horizonte_min_c195_c299=min(v['horizonte_x350'] for k, v in c.items() if k >= 195),
        piel_min_c0_c89=min((v['piel'], k) for k, v in c.items() if k <= 89 and v['piel'] is not None),
        piel_min_c195_c299=min((v['piel'], k) for k, v in c.items() if k >= 195 and v['piel'] is not None),
        plano3_punto_mas_alto=dict(cuadro=n_min, y=ym(n_min), detalle=p3[n_min]),
        plano3_piel_min=min((v['piel']['y'], n) for n, v in p3.items() if v['piel']),
        plano3_tela_min=min((v['tela']['y'], n) for n, v in p3.items() if v['tela']))
    json.dump(out, open(T2 / 'medir.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(out['resumen'], ensure_ascii=False))
    print('cielo por cuadro (cada 10):', {k: v for k, v in c.items() if k % 10 == 0})


# =====================================================================================================
# etapa 3 · banda de ≈ 500 Hz del ambiente de 4530/4531 (indicación 4): ¿tono estacionario? → muesca angosta
# =====================================================================================================
AMB_4 = [('IMG_4531', 3.90, 0.0, 1.0), ('IMG_4530', 0.567, 1.0, 3.0), ('IMG_4531', 3.90, 6.5, DUR)]


def _hp120(x):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, 120, 'high', fs=48000, output='sos'), x)


def psd(x, n=16384):
    from scipy.signal import welch
    f, P = welch(x, 48000, nperseg=n)
    return f, 10 * np.log10(P + 1e-20)


def picos_banda(f, PdB, lo=300, hi=900, umbral=6.0):
    """picos que sobresalen ≥ umbral dB de la envolvente (mediana móvil de ±60 Hz); ancho a −3 dB del pico."""
    from scipy.ndimage import median_filter
    df = f[1] - f[0]
    env = median_filter(PdB, size=int(round(120 / df)) | 1, mode='nearest')
    exc = PdB - env
    sel = np.nonzero((f >= lo) & (f <= hi) & (exc >= umbral))[0]
    grupos = np.split(sel, np.nonzero(np.diff(sel) > 2)[0] + 1) if len(sel) else []
    out = []
    for g in grupos:
        k = g[np.argmax(PdB[g])]
        a = k
        while a > 0 and PdB[a - 1] >= PdB[k] - 3:
            a -= 1
        b = k
        while b < len(f) - 1 and PdB[b + 1] >= PdB[k] - 3:
            b += 1
        out.append(dict(f_hz=round(float(f[k]), 1), sobre_envolvente_db=round(float(exc[k]), 1),
                        ancho_3db_hz=round(float(f[b] - f[a] + df), 1)))
    return out, exc


def estacionariedad(x, f0, ancho=15.0):
    """cada 100 ms (STFT 8192 = 5,9 Hz): frecuencia del máximo en f0 ± ancho y cuánto sobresale de la envolvente
    local (mediana de ±60 Hz). Estacionario = sobresale ≥ 3 dB en ≥ 80 % de las ventanas con frecuencia estable."""
    from scipy.signal import stft
    from scipy.ndimage import median_filter
    f, t, Z = stft(x, 48000, nperseg=8192, noverlap=8192 - 4800)
    A = 20 * np.log10(np.abs(Z) + 1e-12)
    env = median_filter(A, size=(21, 1), mode='nearest')
    m = (f >= f0 - ancho) & (f <= f0 + ancho)
    idx = np.nonzero(m)[0]
    k = idx[np.argmax(A[idx], 0)]
    sob = A[k, np.arange(A.shape[1])] - env[k, np.arange(A.shape[1])]
    fr = f[k]
    return dict(ventanas=int(A.shape[1]), sobresale_3db_pct=round(float((sob >= 3).mean() * 100), 1),
                sobresale_mediana_db=round(float(np.median(sob)), 1), f_mediana_hz=round(float(np.median(fr)), 1),
                f_desvio_hz=round(float(np.std(fr)), 1))


def peaking(f0, gdb, q, fs=48000):
    """biquad «peaking EQ» (RBJ): ganancia gdb en f0 con ancho f0/q; 0 dB lejos de f0."""
    A = 10 ** (gdb / 40); w0 = 2 * np.pi * f0 / fs; al = np.sin(w0) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w0), 1 - al * A]); a = np.array([1 + al / A, -2 * np.cos(w0), 1 - al / A])
    return b / a[0], a / a[0]


MUESCA = dict(g_db=-12.0)      # dentro de −10 a −15 dB (Roma); f0 y Q salen de la medición (banda500.json)


def etapa_banda500():
    O = R / 'ORIGINALES'
    rep = {}
    figs = []
    for toma, t0, t1, nom in (('IMG_4531', 3.90, 7.40, '4531_3.90-7.40'), ('IMG_4530', 0.567, 2.567, '4530_0.567-2.567'),
                              ('IMG_7824', 6.00, 9.50, '7824_6.00-9.50 (comparación)')):
        x = _hp120(W.wav_np(O / f'{toma}.mov', t0, t1))
        f, P = psd(x)
        pk, exc = picos_banda(f, P)
        est = [dict(p, **estacionariedad(x, p['f_hz'])) for p in pk]
        rep[nom] = dict(toma=toma, fuente=[t0, t1], picos_300_900hz=est,
                        voz=W.tonales(x, 48000, t0)['voz_probable'] if toma == 'IMG_4531' else None)
        figs.append((nom, f, P))
        print(nom, est, flush=True)
    # tono común a 4530 y 4531: el pico estacionario de mayor nivel presente en las dos
    c31 = [p for p in rep['4531_3.90-7.40']['picos_300_900hz'] if p['sobresale_3db_pct'] >= 80 and p['f_desvio_hz'] <= 5]
    c30 = [p for p in rep['4530_0.567-2.567']['picos_300_900hz'] if p['sobresale_3db_pct'] >= 80 and p['f_desvio_hz'] <= 5]
    comunes = [(a, b) for a in c31 for b in c30 if abs(a['f_hz'] - b['f_hz']) <= 6]
    if comunes:
        a, b = max(comunes, key=lambda ab: ab[0]['sobre_envolvente_db'] + ab[1]['sobre_envolvente_db'])
        f0 = round((a['f_hz'] + b['f_hz']) / 2, 1); bw = max(a['ancho_3db_hz'], b['ancho_3db_hz'])
        q = float(np.clip(f0 / max(2 * bw, 12.0), 8, 30))
        rep['decision'] = dict(estacionario=True, f0_hz=f0, ancho_3db_hz=bw, q=round(q, 1), g_db=MUESCA['g_db'],
                               ancho_muesca_hz=round(f0 / q, 1))
    else:
        rep['decision'] = dict(estacionario=False, nota='no hay un tono estacionario común: no se aplica muesca')
    print('decisión', rep['decision'])
    # rastros de voz en el tramo nuevo del ambiente de 4531 (6,67–7,40 no estaba en v01)
    x = _hp120(W.wav_np(O / 'IMG_4531.mov', 6.60, 7.40))
    rep['4531_6.60-7.40_tonales'] = W.tonales(x, 48000, 6.60)
    W.espectrograma(_hp120(W.wav_np(O / 'IMG_4531.mov', 3.90, 7.40)), 48000, T2 / 'espectro_4531_3.90-7.40.png', 3.90,
                    'IMG_4531 fuente 3,90–7,40 s (pasa-altos 120): ambiente de 0–1,0 y 6,5–10,0 del máster', fmax=4000)
    rep['artefacto_showspectrumpic'] = artefacto_showspectrum()
    json.dump(rep, open(T2 / 'banda500.json', 'w'), ensure_ascii=False, indent=1)
    # gráfico de las PSD
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(U.FONT, 16)
    im = Image.new('RGB', (1200, 500), (20, 20, 20)); d = ImageDraw.Draw(im)
    fx = lambda hz: int(60 + (hz - 100) / (1500 - 100) * 1120)
    allp = np.concatenate([P[(f >= 100) & (f <= 1500)] for _, f, P in figs]); lo, hi = allp.min(), allp.max()
    fy = lambda v: int(470 - (v - lo) / (hi - lo) * 440)
    for hz in range(100, 1501, 100):
        d.line([fx(hz), 470, fx(hz), 475], fill=(200, 200, 200)); d.text((fx(hz) - 12, 478), str(hz), font=fnt, fill=(200, 200, 200))
    for (nom, f, P), col in zip(figs, ((255, 200, 0), (0, 200, 255), (160, 160, 160))):
        m = (f >= 100) & (f <= 1500)
        d.line(list(zip(map(fx, f[m]), map(fy, P[m]))), fill=col, width=2)
        d.text((70, 10 + 20 * figs.index((nom, f, P))), nom, font=fnt, fill=col)
    if rep['decision'].get('estacionario'):
        x0 = fx(rep['decision']['f0_hz']); d.line([x0, 30, x0, 470], fill=(255, 0, 0))
    im.save(T2 / 'psd_ambientes_100-1500hz.png')


def artefacto_showspectrum():
    """La «banda fija de ≈ 500 Hz» de la hoja v01 salía de un espectrograma de FFmpeg (showspectrumpic, 0–6000 Hz). Prueba:
    el mismo audio (4531 mono, pasa-altos 120, el que entra a la mezcla) con cuatro escalas de frecuencia. Si la franja
    es sonido, cambia de fila al cambiar la escala; si queda en la misma fila de píxeles, es del dibujo."""
    from PIL import Image, ImageDraw, ImageFont
    from scipy.ndimage import median_filter
    wav = T2 / '4531_mono_hp120.wav'
    U.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', str(R / 'ORIGINALES/IMG_4531.mov'), '-vn', '-ac', '1',
           '-ar', '48000', '-af', 'highpass=f=120', str(wav)])
    out, tiras = {}, []
    fnt = ImageFont.truetype(U.FONT, 18)
    for z in (2000, 4000, 6000, 12000):
        png = T2 / f'ssp_{z}.png'
        U.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', str(wav), '-lavfi',
               f'showspectrumpic=s=1400x500:legend=1:stop={z}', str(png)])
        a = np.asarray(Image.open(png).convert('L')).astype(float)
        reg = a[62:561, 142 + int(1400 * 3.5 / 7.47):142 + 1400]          # 3,5–7,4 s (sin la charla)
        prof = reg.mean(1); exc = prof - median_filter(prof, 31)
        # la franja puede ser más clara o más oscura que sus vecinas: fila de mayor desvío absoluto (sin bordes)
        r = int(np.argmax(np.abs(exc[5:-5]))) + 5
        fila = 499 - r
        out[z] = dict(fila_desde_abajo=fila, hz_equivalentes=round(fila * z / 500), desvio_niveles_gris=round(float(exc[r]), 1))
        filas = [fila]
        im = Image.open(png).convert('RGB').crop((0, 400, 1684, 600)); d = ImageDraw.Draw(im)
        d.text((150, 5), f'showspectrumpic 0–{z} Hz · franja en la fila {fila} desde abajo = {round(fila * z / 500)} Hz '
                         f'según la escala (desvío {exc[r]:+.1f} niveles)', font=fnt, fill=(255, 255, 0))
        tiras.append(im)
    H = Image.new('RGB', (1684, 4 * 202), (0, 0, 0))
    for i, t in enumerate(tiras):
        H.paste(t, (0, i * 202))
    H.save(T2 / 'showspectrumpic_franja_fija_4_escalas.png')
    print('artefacto', out)
    return out


def muesca_sos():
    dec = json.load(open(T2 / 'banda500.json'))['decision']
    if not dec.get('estacionario'):
        return None, dec
    return peaking(dec['f0_hz'], dec['g_db'], dec['q']), dec


# =====================================================================================================
# etapa 4 · degradé: el de v01 en c0–c89 y c195–c299; corto detrás de «Y la Negra lo dice bajito.» en c90–c194
# =====================================================================================================
DEG = dict(alfa=0.38, y_plano=330, y_cero=480, cuadros=[(0, 89), (195, NF - 1)])   # v01 (aprobado por Roma)
SEP = 20


def textos(estilo_bajito='Nativo'):
    return [
        dict(t0=0 / FPS, t1=90 / FPS, txt='Perfil bajo…', estilo='Nativo', y=250, pop=True),                      # c0–c89
        dict(t0=34 / FPS, t1=90 / FPS, txt='…hasta que la das vuelta.', estilo='Nativo', y=330, pop=True),        # c34–c89
        dict(t0=90 / FPS, t1=180 / FPS, txt='Y la Negra lo dice bajito.', estilo=estilo_bajito, y=250),           # c90–c179
        dict(t0=195 / FPS, t1=240 / FPS, txt='Ya sabés\\Nlo que tiene atrás.', estilo='Nativo', y=250),           # c195–c239
        dict(t0=240 / FPS, t1=NF / FPS, txt='Pasáselo al más perfil bajo\\Nque conocés.', estilo='Caja', y=250),  # c240–c299
    ]


LIMITES_TEXTO = [(0, 89), (34, 89), (90, 179), (195, 239), (240, NF - 1)]


def opciones_plano3():
    """degradé corto del plano 3: y_cero = punto más alto de manos/remera en c90–c194 − 20 (fijo en todo el plano, para
    que no «respire»); se prueba y_plano de más suave a más duro y se elige el más suave con contraste mediano ≥ 3,0:1 y
    p10 ≥ 2,5:1 (FMT-01 v01, aprobado, daba 2,9–3,3:1) en c90, c105, c120, c135, c150, c165 y c179."""
    med = json.load(open(T2 / 'medir.json'))
    top = med['resumen']['plano3_punto_mas_alto']['y']
    yc = top - SEP
    mk, gl = W.mascara_texto(textos()[2], 4.5, T2, 'texto_bajito')
    ns = (90, 105, 120, 135, 150, 165, 179)
    fr = {n: U.leer(VID0, 1080, 1920, n0=n, n1=n)[0].astype(np.float32) for n in ns}
    ys, xs = np.nonzero(gl)
    filas = []
    for yp in (yc - 150, yc - 120, yc - 90, yc - 70, yc - 50, yc - 35, yc - 25):
        a = W.perfil(DEG['alfa'], yp, yc)
        cs = [W.contraste_blanco(np.clip(fr[n] * (1 - a)[:, None, None], 0, 255).astype(np.uint8), mk) for n in ns]
        filas.append(dict(y_plano=yp, y_cero=yc, fundido_px=yc - yp,
                          contraste_mediana_min=min(c['contraste_mediana'] for c in cs),
                          contraste_p10_min=min(c['contraste_p10'] for c in cs)))
    sin = [W.contraste_blanco(fr[n].astype(np.uint8), mk) for n in ns]
    ok = [f_ for f_ in filas if f_['contraste_mediana_min'] >= 3.0 and f_['contraste_p10_min'] >= 2.5]
    eleg = ok[0] if ok else None
    return dict(tope_manos_remera=top, cuadro_del_tope=med['resumen']['plano3_punto_mas_alto']['cuadro'],
                glifos_caja=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], opciones=filas,
                sin_degrade=dict(contraste_mediana_min=min(c['contraste_mediana'] for c in sin),
                                 contraste_p10_min=min(c['contraste_p10'] for c in sin)),
                elegida=eleg, caja_n=eleg is None)


def etapa_degrade():
    op = opciones_plano3()
    print(json.dumps(op, ensure_ascii=False, indent=0))
    alfas = {}
    a0 = W.perfil(DEG['alfa'], DEG['y_plano'], DEG['y_cero'])
    for a, b in DEG['cuadros']:
        for n in range(a, b + 1):
            alfas[n] = a0
    if op['elegida']:
        a3 = W.perfil(DEG['alfa'], op['elegida']['y_plano'], op['elegida']['y_cero'])
        for n in range(90, 195):
            alfas[n] = a3
    W.aplicar_degrade(VID0, VID, NF, alfas)
    # comprobación sobre el video codificado: fila oscurecida más baja por cuadro contra el tope de lo que no se toca
    med = json.load(open(T2 / 'medir.json'))
    filas = []
    for k0 in range(0, NF, 30):
        k1 = min(NF - 1, k0 + 29)
        x0 = U.leer(VID0, 1080, 1920, n0=k0, n1=k1); x1 = U.leer(VID, 1080, 1920, n0=k0, n1=k1)
        for k in range(len(x0)):
            n = k0 + k
            d = (x0[k].astype(np.float32) - x1[k].astype(np.float32)).mean(axis=(1, 2)).reshape(-1, 2).mean(1)
            r = np.nonzero(d > 1.5)[0]
            ymax = int(r.max()) * 2 + 1 if len(r) else None
            if 90 <= n <= 194:
                p3 = med['plano3'][str(n)]
                tope = min(v['y'] for v in p3.values() if v); que = 'manos/remera'
            else:
                c = med['cielo'][str(n)]
                tope = min(v for v in (c['horizonte_x350'], c['piel']) if v is not None); que = 'horizonte (x ≥ 350) o manos'
            filas.append(dict(cuadro=n, y_max_oscurecida=ymax, tope=tope, que=que,
                              separacion_px=(tope - ymax) if ymax is not None else None,
                              osc_medio_desde_tope=round(float((x0[k][tope:].astype(np.float32) - x1[k][tope:]).mean()), 3)))
        del x0, x1
    sep = [f_ for f_ in filas if f_['separacion_px'] is not None]
    bar = range(26, 34)
    rep = dict(parametros=DEG, plano3=op, por_cuadro=filas,
               cuadros_con_cambio=len(sep), cuadros_sin_cambio=[f_['cuadro'] for f_ in filas if f_['y_max_oscurecida'] is None],
               separacion_min_plano3=min(f_['separacion_px'] for f_ in sep if 90 <= f_['cuadro'] <= 194) if op['elegida'] else None,
               separacion_min_resto_sin_barrido=min(f_['separacion_px'] for f_ in sep if not 90 <= f_['cuadro'] <= 194 and f_['cuadro'] not in bar),
               separacion_min_barrido_c26_c33=min(f_['separacion_px'] for f_ in sep if f_['cuadro'] in bar),
               separacion_min_manos_resto=min(med['cielo'][str(f_['cuadro'])]['piel'] - f_['y_max_oscurecida'] for f_ in sep
                                               if not 90 <= f_['cuadro'] <= 194 and med['cielo'][str(f_['cuadro'])]['piel']),
               osc_max_desde_tope=max(f_['osc_medio_desde_tope'] for f_ in filas))
    json.dump(rep, open(T2 / 'degrade.json', 'w'), ensure_ascii=False, indent=1)
    print({k: v for k, v in rep.items() if k not in ('por_cuadro', 'plano3', 'parametros')})


# =====================================================================================================
# etapa 5 · sonido (indicaciones 3, 4 y 5)
# =====================================================================================================
def ambientes(m, sos=None, g7824=0.0):
    """4530/4531 en una mezcla aparte (para la muesca) + 7824: 0 dB en la completa (v02, Roma; era −6) para tapar los
    pozos de «bajito» bajo la música; en la versión sin música sigue en −6 (no hay pozos que tapar y +6 dB la dejaría
    con «bajito» como el tramo más fuerte)."""
    from sonido import Mezcla
    from scipy.signal import lfilter
    a = Mezcla(DUR)
    for toma, s0, t0, t1 in AMB_4:
        a.ambiente(toma, s0, t0, t1, -4, hp=120, fin_fade=(.25 if t1 == DUR else None))
    if sos is not None:
        b, a_ = sos
        a.pistas['amb'] = lfilter(b, a_, a.pistas['amb'], axis=0)
        a.log(0.0, 'muesca v02 en el ambiente de 4530/4531 (banda500.json)')
    m.pistas['amb'] += a.pistas['amb']; m.ev += a.ev
    m.ambiente('IMG_7824', 6.00, 3.0, 6.5, g7824, hp=150, lp=8000)
    return a.pistas['amb']


# «bajito» sin pozos (indicación 3): con 7824 a 0 dB los pozos antes de los bombos de 5,0 y 6,0 seguían en −31/−33 LUFS
# momentáneos (mediana del tramo −18,7): entre las colas de los bombos solo quedan el ambiente y los pads (−42 dBFS).
# Medido en procesos separados (pad_bajito.json): .035 → pozo 14,1 LU bajo la mediana; .10 → 8,6; .12 → 7,5; .14 → 6,5;
# .17 → 5,2. Se usa .14 (+12 dB, mismo filtro de 600 Hz, sin palma ni charles): «bajito» sigue ≈ 5 LU debajo del groove.
PAD_BAJITO = .14
GANANCIA = [(0.0, 0.933, 8.0, 0.0, 0.067)]   # entrada +8 dB; vuelve a 0 dentro del hueco 0,933–1,000


def musica(m, g):
    """como fmt01.musica (guion §5) con la entrada (pad, charles y campana) en la mezcla g, que recibe la curva; final
    del guion para 10,000 s: palma 9,5 y fundido de música 9,55–10,00."""
    ch = lambda t0, t1, gg: [m.charles(round(float(t), 3), gg) for t in np.arange(t0, t1 - 1e-6, 0.25)]
    g.pad(0.0, [52, 55, 59], .95, .04, 900, a=.1)
    for t in (0, .25, .5, .75):
        g.charles(t, .05)
    g.campana(0.0, 71, .05)
    m.bombo(1.0, .95); m.ocho08(1.0, 40, .9, .55, glide_desde=47); m.impacto(1.0, .35)
    m.pad(1.0, [52, 55, 59], .95, .06); m.pad(2.0, [48, 52, 55], .95, .06)
    m.bombo(2.0, .6); m.bombo(2.75, .6)
    m.palma(1.5); m.palma(2.5)
    ch(1.0, 3.0, .08)
    m.ocho08(2.0, 36, .45); m.ocho08(2.5, 38, .45)
    m.pad(3.0, [52, 55, 59], 1.95, PAD_BAJITO, 600); m.pad(5.0, [45, 48, 52], 1.45, PAD_BAJITO, 600)
    for t in (3.0, 4.0, 5.0, 6.0):
        m.bombo(t, .45, f0=90)
    m.ocho08(3.0, 40, .9, .30)
    m.palma(6.5); ch(6.5, 9.5, .08)
    m.bombo(7.0, .9); m.ocho08(7.0, 43, .45); m.pad(7.0, [43, 47, 50], .95, .06)
    m.palma(7.5)
    m.bombo(8.0, .9); m.ocho08(8.0, 45, .45); m.pad(8.0, [45, 48, 52], .95, .06); m.campana(8.0, 76, .06)
    m.palma(8.5)
    m.bombo(9.0, .9); m.ocho08(9.0, 40, .9, .5); m.pad(9.0, [52, 55, 59, 64], .9, .06, r=.5)
    m.palma(9.5, .25)
    c = W.curva(m.N, GANANCIA)[:, None]
    for k in ('mus', 'fx'):
        m.pistas[k] += g.pistas[k] * c
    m.ev += [dict(e, evento=e['evento'] + ' (con curva v02)') for e in g.ev]
    m.log(0.0, 'curva v02: +8 dB 0,000–0,933 (rampa de salida en el hueco) a pad/charles/campana de la entrada')
    m.silenciar('mus', 0.933, 1.000)
    m.fundido('mus', 9.55, 10.00)
    m.fundido('fx', 9.55, 10.00)       # colas de reverberación de la música: sin corte seco en el último cuadro


def etapa_audio():
    from sonido import Mezcla
    from scipy.signal import welch
    A = T2 / 'audio'; A.mkdir(parents=True, exist_ok=True)
    sos, dec = muesca_sos()
    m = Mezcla(DUR); g = Mezcla(DUR)
    ambientes(m, sos); F.foley(m); musica(m, g)
    r1 = m.exportar(str(A / 'fmt01_completa.wav'), lufs=-14)
    s = Mezcla(DUR); ambientes(s, sos, g7824=-6.0); F.foley(s)
    r2 = s.exportar(str(A / 'fmt01_sinmusica.wav'), lufs=-14)
    print('completa', r1, 'sin música', r2, 'muesca', dec)
    # medida de la muesca: ambiente de 4530/4531 sin y con muesca (misma señal), PSD y RMS por octava
    if sos is not None:
        x0 = ambientes(Mezcla(DUR), None).mean(1); x1 = ambientes(Mezcla(DUR), sos).mean(1)
        f, P0 = psd(x0); _, P1 = psd(x1)
        dP = P1 - P0; f0 = dec['f0_hz']; bw = dec['ancho_muesca_hz']
        fuera = (np.abs(f - f0) > 3 * bw) & (f >= 60) & (f <= 16000)
        oct_ = {}
        for fc in (125, 250, 500, 1000, 2000, 4000, 8000):
            mm = (f >= fc / np.sqrt(2)) & (f < fc * np.sqrt(2))
            oct_[fc] = round(float(10 * np.log10(10 ** (P1[mm] / 10).sum() / 10 ** (P0[mm] / 10).sum())), 2)
        rms = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()))
        rep = dict(decision=dec, atenuacion_en_f0_db=round(float(dP[np.argmin(np.abs(f - f0))]), 2),
                   max_abs_cambio_fuera_de_f0_mas_menos_3_anchos_db=round(float(np.abs(dP[fuera]).max()), 2),
                   cambio_rms_total_db=round(float(rms(x1) - rms(x0)), 3), cambio_por_octava_db=oct_)
        json.dump(rep, open(A / 'muesca_medida.json', 'w'), ensure_ascii=False, indent=1)
        print(rep)


TRAMOS_M = [('entrada 0,0–1,0', 0.0, 1.0), ('giro + espalda 1,0–3,0', 1.0, 3.0), ('«bajito» 3,0–6,5', 3.0, 6.5),
            ('vuelta 6,5–8,0', 6.5, 8.0), ('CTA 8,0–9,5', 8.0, 9.5), ('fundido 9,5–10,0', 9.5, 10.0)]


def etapa_prueba_pad():
    """una prueba de PAD_BAJITO en un proceso nuevo (el generador aleatorio de sonido.py arranca igual que en la mezcla)."""
    global PAD_BAJITO
    from sonido import Mezcla
    PAD_BAJITO = float(sys.argv[2])
    A = T2 / 'audio' / 'pruebas_pad'; A.mkdir(parents=True, exist_ok=True)
    m = Mezcla(DUR); g = Mezcla(DUR); ambientes(m, None); F.foley(m); musica(m, g)
    f = A / f'prueba_pad_{PAD_BAJITO}.wav'
    m.exportar(str(f), lufs=-14)
    t = W.momentanea_tramos(W.momentanea(f), TRAMOS_M)
    b = t[2]
    print(json.dumps(dict(pad=PAD_BAJITO, tramos=t, pozo_lu=round(b['M_mediana'] - b['M_min'], 1))))


def etapa_pads():
    res = []
    for v in (.035, .10, .12, .14, .17):
        out = U.run(['nice', '-n', '10', sys.executable, __file__, 'prueba_pad', str(v)]).decode()
        res.append(json.loads(out.strip().splitlines()[-1]))
        print(res[-1]['pad'], 'pozo', res[-1]['pozo_lu'], [(x['tramo'], x['M_min'], x['M_mediana']) for x in res[-1]['tramos']], flush=True)
    json.dump(res, open(T2 / 'pad_bajito.json', 'w'), ensure_ascii=False, indent=1)


# =====================================================================================================
# etapa 6 · máster
# =====================================================================================================
NOMBRES = {'completa': 'ROCCE_FMT01_PERFIL_BAJO_v02.mp4', 'sinmusica': 'ROCCE_FMT01_PERFIL_BAJO_SINMUSICA_v02.mp4'}
MAS = T2 / 'master'
ASS = T2 / 'fmt01_textos.ass'


def textos_v02():
    op = json.load(open(T2 / 'degrade.json'))['plano3']
    return textos('CajaN' if op['caja_n'] else 'Nativo')


def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    a = V.ass(textos_v02(), ASS)
    for k, nombre in NOMBRES.items():
        if (MAS / nombre).exists():
            raise RuntimeError(f'{MAS / nombre} ya existe')
        V.master(VID, T2 / 'audio' / f'fmt01_{k}.wav', MAS / nombre, ass_path=a)
        print('->', MAS / nombre)


# =====================================================================================================
# etapa 7 · control y evidencia
# =====================================================================================================
EVID = T2 / 'evidencia_v02'
TRAMOS = [('1 frente Blanca + barrido (4531)', 0.0, 1.0), ('2 espalda Blanca (4530)', 1.0, 3.0),
          ('3 Negra «bajito» (7824)', 3.0, 6.5), ('4a vuelve el frente (4531)', 6.5, 8.0),
          ('4b CTA (4531)', 8.0, DUR), ('último 0,5 s', DUR - 0.5, DUR)]


def _tira(frames_ns, caja, ancho, salida, video, cols=6, rotulo=''):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(U.FONT, 20)
    x0, y0, x1, y1 = caja
    ims = []
    for n in frames_ns:
        f = U.leer(video, 1080, 1920, n0=n, n1=n)[0][y0:y1, x0:x1]
        im = Image.fromarray(f); im = im.resize((ancho, round(ancho * im.height / im.width)), Image.LANCZOS)
        d = ImageDraw.Draw(im); d.rectangle([0, 0, 150, 26], fill=(0, 0, 0)); d.text((4, 2), f'{rotulo}c{n}', font=fnt, fill=(255, 255, 0))
        ims.append(im)
    filas = (len(ims) + cols - 1) // cols
    Wd = Image.new('RGB', (cols * (ancho + 2), filas * (ims[0].height + 2)), (30, 30, 30))
    for k, im in enumerate(ims):
        Wd.paste(im, ((k % cols) * (ancho + 2), (k // cols) * (ims[0].height + 2)))
    Wd.save(salida, quality=92)


def extra_v02():
    tx = textos_v02()
    # comprobaciones de v01 (fmt01.extra_fmt01) con las variables de v02
    F.T, F.MAS, F.NOMBRES, F.TEXTOS, F.LIMITES_TEXTO, F.NF, F.VID, F.EVID = T2, MAS, NOMBRES, tx, LIMITES_TEXTO, NF, VID, EVID
    out = F.extra_fmt01()
    (EVID / 'manga_beige_master_c232-c260_esquina_1a1.jpg').unlink(missing_ok=True)   # cuadros de v01: se rehace abajo
    lp = out.pop('loop')
    out['loop_c299_c0'] = dict(dif_c299_c0=lp['dif_c277_c0'], mediana_dif_plano4=lp['mediana_dif_plano4'],
                               p90_plano4=lp['p90_plano4'], max_plano4=lp['max_plano4'])
    mp = json.load(open(T2 / 'mapa_cuadros.json'))
    out['loop_c299_c0'].update(c299_fuente=mp['4']['ultimo']['fuente'], c0_fuente=mp['1a']['primero']['fuente'])
    # contraste de cada texto, sin y con degradé, en su primer cuadro, el medio y el último
    S = T2 / 'ctrl'; S.mkdir(exist_ok=True)
    cont = {}
    for i, (a, b) in enumerate(LIMITES_TEXTO):
        mk, _ = W.mascara_texto(tx[i], (a + b) / 2 / FPS, S, f'cont_{i}')
        fil = {}
        for n in (a, (a + b) // 2, b):
            f0 = U.leer(VID0, 1080, 1920, n0=n, n1=n)[0]; f1 = U.leer(VID, 1080, 1920, n0=n, n1=n)[0]
            fil[f'c{n}'] = dict(sin_degrade=W.contraste_blanco(f0, mk), con_degrade=W.contraste_blanco(f1, mk))
        c = dict(estilo=tx[i]['estilo'], cuadros=fil)
        if tx[i]['estilo'] in ('Caja', 'CajaN'):
            c['nota'] = 'caja opaca blanca con texto #141414 (18,4:1); el fondo medido queda alrededor de la caja'
        cont[f"{tx[i]['txt']} (c{a}–c{b})"] = c
    out['contraste_textos'] = cont
    out['degrade'] = {k: v for k, v in json.load(open(T2 / 'degrade.json')).items() if k != 'por_cuadro'}
    # sonoridad momentánea por tramo: v02 y v01
    mom = {}
    for k, nombre in NOMBRES.items():
        mm = W.momentanea(MAS / nombre)
        json.dump(mm, open(EVID / f'sonoridad_momentanea_100ms_{k}.json', 'w'), indent=0)
        mom[k] = W.momentanea_tramos(mm, TRAMOS_M)
    for k, nombre in (('completa_v01', 'ROCCE_FMT01_PERFIL_BAJO_v01.mp4'), ('sinmusica_v01', 'ROCCE_FMT01_PERFIL_BAJO_SINMUSICA_v01.mp4')):
        mom[k] = W.momentanea_tramos(W.momentanea(U.EXP / nombre),
                                     [t for t in TRAMOS_M if t[2] <= 9.267] + [('CTA 8,0–9,267 (v01)', 8.0, 9.267)])
    out['sonoridad_momentanea_por_tramo'] = mom
    b = [t for t in mom['completa'] if t['tramo'].startswith('«bajito»')][0]
    out['bajito_pozo_lu'] = round(b['M_mediana'] - b['M_min'], 1)
    out['banda500'] = json.load(open(T2 / 'banda500.json'))
    out['pad_bajito'] = [dict(pad=r['pad'], pozo_lu=r['pozo_lu']) for r in json.load(open(T2 / 'pad_bajito.json'))]
    return out


def etapa_control():
    import shutil
    EVID.mkdir(parents=True, exist_ok=True)
    rep = U.control(NOMBRES, EVID, [26, 30, 34, 90, 195, 240], NF - 1, TRAMOS, ASS, textos_v02(), [1.5, 4.5, 7.0, 9.0],
                    extra=extra_v02, carpeta=MAS)
    for f in ('planos.json', 'mapa_cuadros.json', 'medir.json', 'degrade.json', 'banda500.json', 'pad_bajito.json',
              'psd_ambientes_100-1500hz.png', 'showspectrumpic_franja_fija_4_escalas.png', 'espectro_4531_3.90-7.40.png'):
        shutil.copy2(T2 / f, EVID / f)
    for k in ('completa', 'sinmusica'):
        shutil.copy2(T2 / 'audio' / f'fmt01_{k}_eventos.json', EVID / f'audio_eventos_{k}.json')
    f0 = MAS / NOMBRES['completa']; m1 = U.EXP / 'ROCCE_FMT01_PERFIL_BAJO_v01.mp4'
    # «Y la Negra lo dice bajito.»: v01 y v02 (1:1, franja y 150–480) y al ancho de un teléfono
    _tira([90, 120, 150, 179], (0, 150, 1080, 480), 540, EVID / 'bajito_v01_c90-c179_1a1.jpg', m1, cols=2, rotulo='v01 ')
    _tira([90, 120, 150, 179], (0, 150, 1080, 480), 540, EVID / 'bajito_v02_c90-c179_1a1.jpg', f0, cols=2, rotulo='v02 ')
    _tira([95, 135, 179], (0, 0, 1080, 1920), 360, EVID / 'bajito_v02_ancho_telefono_360px.jpg', f0, cols=3, rotulo='v02 ')
    # mano con puño beige (aceptada por Roma): 4531 c12–c33 = máster c195–c216, y c75–c96 = máster c258–c279
    _tira(list(range(195, 217, 3)), (480, 1320, 1080, 1920), 300, EVID / 'puno_beige_c195-c216_abajo_der_1a1.jpg', f0,
          cols=8)
    _tira(list(range(258, 280, 3)), (480, 1320, 1080, 1920), 300, EVID / 'puno_beige_c258-c279_abajo_der_1a1.jpg', f0,
          cols=8)
    _tira([297, 298, 299, 0, 1, 2], (0, 0, 1080, 1920), 270, EVID / 'loop_c297-c299_c0-c2.jpg', f0, cols=6)
    json.dump(rep, open(EVID / 'control.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k not in ('archivos', 'color', 'banda500', 'espalda_c26_c40',
                                                                 'textos_limites', 'cta', 'mediciones')}, ensure_ascii=False)[:6000])
    print('textos_ok', rep.get('textos_ok'), 'cta', {k: rep['cta'][k] for k in ('caja', 'sep_min_logo', 'sep_min_mano')})
    for k, v in rep['archivos'].items():
        print(k, v['bytes'], v['sha256'], v['md5_video'], v['md5_audio'], v['sonoridad'], v['video']['cuadros'],
              v['video']['duracion'], v['audio']['duracion'], v['decodifica_completo'], v['marcas_gps_o_ubicacion'],
              [(t['tramo'], t['rms_dbfs']) for t in v['niveles_por_tramo']], v['ventanas_100ms_bajo_menos50dbfs'])


# =====================================================================================================
# etapa 8 · entrega (fmt03.entregar: no sobrescribe; verifica bytes, sha256 y md5 de flujos de las copias)
# =====================================================================================================
def etapa_entregar():
    r = U.entregar(NOMBRES, MAS, EVID, F.PIEZA)
    json.dump(r, open(T2 / 'entrega.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    globals()['etapa_' + etapa]()
