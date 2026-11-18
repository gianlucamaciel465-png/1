#!/usr/bin/env python3
"""VIR-02 «Lo que no se mueve» (respaldo sin voz) · receta del máster v01 (Pedro, 18/11/2026).

Guion: piezas/VIR_marcas_nuevas_virales/VIR-02_nombre/01_fede_guion_G1.md (G1 v1) + 02_roma_aprobacion_G1.md
(las correcciones de Roma mandan: hook nuevo A/B, cortes 3-2-2-1 sobre la grilla de 100 BPM, tamaños de texto, color).
Reutiliza sin modificarlos scripts/fmt/video.py (color HLG→SDR, ass, master), sonido.py (Mezcla), fmt03.py (plano_z,
leer, hoja_src, seguir_estampado, md5_stream, ebur, audio_np), fmt03_v02.py (contraste_blanco, mascara_texto,
textos_limites, momentanea) y fmt04_util.py (hoja_c). No toca nada de vir01.

Lo nuevo de esta pieza vive acá:
  - medición de «Founders Privée» por cuadro de fuente (recuadro del estampado: celeste en la Blanca, gris claro en la
    Negra) y encuadre calculado para que en cada cuadro de corte quede en centro (540, 1000) y ancho 920 px;
  - ganancias de color medidas sobre la tela blanca lisa de 4530, 4625, 8002 y 7885 (blanco neutro, celeste intacto).

Etapas (python vir02n.py <etapa>, con nice -n 10):
  hojas → medir → planos → audio → master → control → entregar
"""
import json, math, subprocess, sys, hashlib, shutil, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V          # noqa: E402
import fmt03 as U          # noqa: E402
import fmt03_v02 as U2     # noqa: E402
import fmt04_util as F4    # noqa: E402

R = Path('/home/user/1')
T = R / 'TRABAJO/vir/vir02n'
EXP = R / 'EXPORTACIONES'
PIEZA = Path('/mnt/project-files/piezas/VIR_marcas_nuevas_virales/VIR-02_nombre/')
FPS = 30
W, H = 1080, 1920
FONT = U.FONT
SR = 48000


def nice(cmd):
    return ['nice', '-n', '10'] + list(cmd)


# =====================================================================================================
# etapa 1 · hojas cada 0,1 s de las fuentes (cadena de color de video.py; cuadro y ms de la FUENTE impresos)
#           + niveles de audio cada 0,1 s de los mismos tramos
# =====================================================================================================
HOJAS = [  # toma, cuadro inicial, cuadro final, cada, nombre
    ('IMG_7824', 0, 60, 3, '7824_0.0-2.0'),
    ('IMG_4530', 24, 69, 3, '4530_0.8-2.3'),
    ('IMG_4625', 0, 42, 3, '4625_0.0-1.4'),
    ('IMG_8002', 87, 106, 1, '8002_2.9-3.567_c1'),
    ('IMG_7885', 0, 150, 3, '7885_0.0-5.0'),
]
NIVELES_TRAMOS = [('IMG_7824', 0.0, 2.0), ('IMG_4530', 0.8, 2.3), ('IMG_4625', 0.0, 1.4), ('IMG_8002', 2.9, 3.6),
                  ('IMG_7885', 0.0, 5.0)]


def audio_toma(toma, sr=SR):
    raw = U.run(['ffmpeg', '-v', 'error', '-i', str(V._src(toma)), '-vn', '-map', '0:a:0', '-f', 'f32le', '-ac', '2',
                 '-ar', str(sr), '-'])
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def db(x):
    return round(float(20 * np.log10(max(float(x), 1e-9))), 1)


def niveles_01(toma, t0, t1, sr=SR):
    """RMS y pico (dBFS, mono = media de canales) cada 100 ms + energía por banda (< 200 Hz «viento/retumbo»,
    200–2000, > 2000 Hz) en dB relativos, para decidir el pasa-altos."""
    from scipy.signal import butter, sosfilt
    a = audio_toma(toma).mean(1)
    bandas = {'lt200': butter(4, 200, 'low', fs=sr, output='sos'), '200_2k': butter(4, [200, 2000], 'band', fs=sr, output='sos'),
              'gt2k': butter(4, 2000, 'high', fs=sr, output='sos')}
    fb = {k: sosfilt(s, a) for k, s in bandas.items()}
    w = int(0.1 * sr)
    filas = []
    t = t0
    while t < t1 - 1e-6:
        i = int(round(t * sr)); seg = a[i:i + w]
        if len(seg) < w // 2:
            break
        f = dict(t=round(t, 1), rms_dbfs=db(np.sqrt((seg ** 2).mean())), pico_dbfs=db(np.abs(seg).max()))
        for k, x in fb.items():
            f[f'rms_{k}'] = db(np.sqrt((x[i:i + w] ** 2).mean()))
        filas.append(f); t += 0.1
    return filas


def etapa_hojas():
    Hd = T / 'hojas'; Hd.mkdir(parents=True, exist_ok=True)
    for toma, n0, n1, cada, nom in HOJAS:
        U.hoja_src(toma, n0, n1, Hd / f'hoja_fuente_{nom}.jpg', cada=cada, ancho=216 if cada == 1 else 240,
                   cols=10, rot=toma[4:] + ' ')
        print('hoja', nom, flush=True)
    niv = {}
    md = ['# Niveles de audio de las fuentes cada 0,1 s (dBFS, mono)', '',
          'RMS y pico por ventana de 100 ms; bandas: < 200 Hz (viento/retumbo), 200–2000 Hz, > 2000 Hz. Medido, no escuchado.', '']
    for toma, t0, t1 in NIVELES_TRAMOS:
        f = niveles_01(toma, t0, t1)
        niv[f'{toma} {t0:.1f}-{t1:.1f}'] = f
        md += [f'## {toma} {t0:.1f}–{t1:.1f} s', '', '| t | RMS | pico | <200 | 200–2k | >2k |', '|---|---|---|---|---|---|']
        md += [f"| {x['t']:.1f} | {x['rms_dbfs']} | {x['pico_dbfs']} | {x['rms_lt200']} | {x['rms_200_2k']} | {x['rms_gt2k']} |"
               for x in f]
        md.append('')
    json.dump(niv, open(Hd / 'niveles_fuentes_0.1s.json', 'w'), ensure_ascii=False, indent=1)
    (Hd / 'niveles_fuentes_0.1s.md').write_text('\n'.join(md), encoding='utf-8')
    print('niveles listos', flush=True)


# =====================================================================================================
# etapa 2 · mediciones sobre las fuentes: «Founders Privée» por cuadro de fuente + color de la tela
# =====================================================================================================
# Recuadro del estampado = caja de los píxeles de «Founders Privée» (letras + rúbrica) detectados por color con
# fmt03.seguir_estampado: celeste en la Blanca (B−R > 20, B−G > 4, L > 105), gris claro en la Negra (L > 95, sat < 0,2),
# siguiendo el recuadro del cuadro anterior (+24 px) desde una zona inicial fijada a mano en la hoja de 0,1 s.
# Se mide sobre la toma con la MISMA cadena de color de video.py, leída a 1080×1920 (las 4K a la mitad: ×2 para pasar a
# coordenadas de la toma rotada).
MED = {  # clave: (tipo, cuadro inicial, cuadro final, zona (x0, y0, x1, y1) en 1080×1920, zona fija, parámetros)
    # zona fija = sin seguimiento (el estampado se mueve poco y alrededor hay tela, mar o roca que confunden al seguidor)
    'IMG_7824': ('negra', 0, 66, (0, 760, 1079, 1200), False, {}),
    'IMG_4530': ('blanca', 18, 72, (0, 900, 1079, 1320), True, {}),
    'IMG_4625': ('blanca', 0, 45, (150, 870, 770, 1090), True, dict(min_frac=0.02)),
    'IMG_8002': ('blanca', 78, 106, (0, 940, 1079, 1440), True, {}),
    # Negra al sol (tela gris oscura, L 60–90): fondo hasta 115; zona solo sobre la espalda (sin la Blanca ni el pantalón)
    'IMG_7885': ('negra', 0, 6, (500, 860, 930, 1020), True, dict(lf_max=115, dl_min=60, media_max=150)),
    # Blanca del final de 5b (¿sigue completa?) y tela al sol para la ganancia de color
    'IMG_7885b': ('blanca', 100, 128, (200, 600, 1000, 1200), True, {}),
    # alternativa propuesta para el plano 4 (plano general colgada de la baranda, antes del acercamiento)
    'IMG_8002a': ('blanca', 0, 26, (300, 820, 1000, 1180), False, {}),
}


def escala(toma):
    return V.TOMAS[toma]['nat'][0] / W     # 2 en las 4K, 1 en las 1080p


def estampado(img, tipo, roi, tam=41, lf_max=70, dl_min=55, media_max=110, min_frac=0.0, excluir=()):
    """«Founders Privée» en un cuadro 1080×1920 RGB (uint8). Reemplaza el umbral fijo de fmt03.seguir_estampado, que en
    estas tomas toma la tela blanca en sombra (azulada en 4625/8002) y la Blanca vecina en 7885 como estampado (primera
    corrida). Se compara cada píxel con el FONDO LOCAL de la tela:
      - Blanca: fondo = cierre en gris (máx → mín, `tam` px) por canal (llena los trazos). Azul relativo
        d = B/Bf − R/Rf, sin la sombra suave de los pliegues (sombrero de copa: d − apertura(d, 61 px)). Celeste =
        d > máx(0,06; 0,45 × p99,5 de d en la zona), luma relativa > 0,72 (ROCCÉ azul marino queda afuera) y tela clara
        alrededor (L del fondo > 140).
      - Negra: fondo = apertura en gris (mín → máx) de la luma (la tela sin las letras). Letra = L − Lf > 55, Lf < 70,
        sat < 0,25 y media local (41 px) < 110: el cielo, la Blanca vecina, la piel y la roca quedan afuera.
    Agrupado: trazos unidos con dilatación 8; queda el grupo mayor y los grupos (≥ 3 %) cuyo centro cae dentro de su caja
    agrandada (±15 % del ancho, ±60 % del alto); se recortan arriba/abajo las filas con < 8 % de la fila más cargada
    (restos de pliegues). Con min_frac > 0, antes de agrupar se borran las manchas sueltas de menos de esa fracción de
    la máscara (en 4625 una mancha de sombra a 25 px de la cola de la F se unía al grupo y corría el borde izquierdo
    30 px; en el máster, una roca azulada en el borde de c125). Devuelve caja (x0, y0, x1, y1) en px 1080×1920 y la
    máscara."""
    from scipy import ndimage as nd
    f = img.astype(np.float32)
    x0, y0, x1, y1 = [int(round(v)) for v in roi]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W - 1, x1), min(H - 1, y1)
    pad = tam
    ya, yb, xa, xb = max(0, y0 - pad), min(H, y1 + pad + 1), max(0, x0 - pad), min(W, x1 + pad + 1)
    sub = f[ya:yb, xa:xb]
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    L = 0.2126 * r + 0.7152 * g + 0.0722 * b
    sat = (sub.max(-1) - sub.min(-1)) / (sub.max(-1) + 1)
    if tipo == 'blanca':
        bg = [nd.grey_closing(c, size=(tam, tam)) + 1 for c in (r, g, b)]
        Lf = 0.2126 * bg[0] + 0.7152 * bg[1] + 0.0722 * bg[2]
        d = b / bg[2] - r / bg[0]
        d = d - nd.grey_opening(d, size=(61, 61))
        dentro = np.zeros_like(d, bool); dentro[y0 - ya:y1 - ya + 1, x0 - xa:x1 - xa + 1] = True
        thr = max(0.06, 0.45 * float(np.percentile(d[dentro & (Lf > 140)], 99.5))) if (dentro & (Lf > 140)).any() else 0.06
        m = (d > thr) & (L / Lf > 0.72) & (Lf > 140)
    else:
        Lf = nd.grey_opening(L, size=(tam, tam))
        m = ((L - Lf) > dl_min) & (Lf < lf_max) & (sat < 0.25) & (nd.uniform_filter(L, size=tam) < media_max)
    m = nd.binary_opening(m, iterations=1)
    full = np.zeros((H, W), bool); full[ya:yb, xa:xb] = m
    lim = np.zeros((H, W), bool); lim[y0:y1 + 1, x0:x1 + 1] = True
    full &= lim
    for ex0, ey0, ex1, ey1 in excluir:          # zonas que no son el estampado (p. ej. la R de ROCCÉ en 7885 ampliado)
        full[ey0:ey1 + 1, ex0:ex1 + 1] = False
    if min_frac > 0 and full.any():
        lab0, n0_ = nd.label(full)
        s0 = nd.sum(full, lab0, np.arange(1, n0_ + 1))
        full &= np.isin(lab0, 1 + np.nonzero(s0 >= min_frac * full.sum())[0])
    lab, n = nd.label(nd.binary_dilation(full, iterations=8))
    if n == 0:
        return None, full
    idx = np.arange(1, n + 1)
    s_ = nd.sum(full, lab, idx)
    k = int(np.argmax(s_)) + 1
    sl = nd.find_objects(lab)
    gy0, gy1, gx0, gx1 = sl[k - 1][0].start, sl[k - 1][0].stop, sl[k - 1][1].start, sl[k - 1][1].stop
    gw, gh = gx1 - gx0, gy1 - gy0
    cm = nd.center_of_mass(full, lab, idx)
    keep = [i + 1 for i in range(n) if i + 1 == k or (s_[i] >= 0.03 * s_[k - 1] and
            gx0 - 0.15 * gw <= cm[i][1] <= gx1 + 0.15 * gw and gy0 - 0.6 * gh <= cm[i][0] <= gy1 + 0.6 * gh)]
    full &= np.isin(lab, keep)
    rows = full.sum(1); ok = np.nonzero(rows >= 0.08 * rows.max())[0]
    full[:ok.min()] = False; full[ok.max() + 1:] = False
    ys, xs = np.nonzero(full)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), full


def seguir(frames, tipo, roi0, margen=30, tam=41, fijo=False, **par):
    res = []; roi = roi0
    for img in frames:
        bb, m = estampado(img, tipo, roi, tam, **par)
        res.append(dict(founders=bb, mask=m))
        if bb is not None and not fijo:
            roi = (bb[0] - margen, bb[1] - margen, bb[2] + margen, bb[3] + margen)
    return res


def medir_estampado(clave):
    tipo, n0, n1, roi0, fijo, par = MED[clave]
    toma = clave[:8]
    fr = U.leer(V._src(toma), W, H, n0=n0, n1=n1, vf_pre=V.color(toma))
    res = seguir(fr, tipo, roi0, fijo=fijo, **par)
    s = escala(toma)
    filas = []
    for k, r in enumerate(res):
        x0, y0, x1, y1 = r['founders']
        filas.append(dict(cuadro_fuente=n0 + k, bbox_1080=[x0, y0, x1, y1],
                          bbox_nat=[x0 * s, y0 * s, (x1 + 1) * s, (y1 + 1) * s],
                          cx_nat=round((x0 + x1 + 1) / 2 * s, 1), cy_nat=round((y0 + y1 + 1) / 2 * s, 1),
                          w_nat=(x1 + 1 - x0) * s, h_nat=(y1 + 1 - y0) * s,
                          margen_izq_1080=x0, margen_der_1080=W - 1 - x1))
    return fr, res, filas


def dibujar(frames, res, salida, n0, rot, cada=1, ancho=216, cols=10):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 30)
    tiles = []
    for k in range(0, len(frames), cada):
        ov = frames[k].copy(); r = res[k]
        ov[r['mask']] = [255, 0, 0]
        im = Image.fromarray(ov); d = ImageDraw.Draw(im)
        d.rectangle(list(r['founders']), outline=(255, 255, 0), width=4)
        d.rectangle([0, 0, 1079, 44], fill=(0, 0, 0))
        x0, y0, x1, y1 = r['founders']
        d.text((8, 6), f'{rot} c{n0 + k} x{x0}-{x1} y{y0}-{y1}', font=fnt, fill=(255, 255, 0))
        tiles.append(im.resize((ancho, round(ancho * im.height / im.width))))
    th = tiles[0].height; filas = math.ceil(len(tiles) / cols)
    Wd = Image.new('RGB', (cols * (ancho + 2), filas * (th + 2)), (32, 32, 32))
    for i, t in enumerate(tiles):
        Wd.paste(t, ((i % cols) * (ancho + 2), (i // cols) * (th + 2)))
    Wd.save(salida, quality=90)


def parche_tela(f, bb, tipo):
    """tela lisa debajo de «Founders Privée» (1080×1920 RGB): franja de 0,10–0,45 × ancho del estampado por debajo de su
    borde inferior, en el 60 % central de su ancho; Blanca: L > 150 y sat < 0,2 (sin sombras fuertes ni piel ni celeste);
    Negra: L < 60. Devuelve RGB medio, B−R, G−R."""
    x0, y0, x1, y1 = bb; bw = x1 - x0
    ya, yb = int(y1 + 0.10 * bw), int(min(H, y1 + 0.45 * bw)); xa, xb = int(x0 + 0.2 * bw), int(x1 - 0.2 * bw)
    p = f[ya:yb, xa:xb].reshape(-1, 3).astype(np.float64)
    L = p @ [0.2126, 0.7152, 0.0722]; sat = (p.max(1) - p.min(1)) / (p.max(1) + 1)
    m = ((L > 150) & (sat < 0.2)) if tipo == 'blanca' else (L < 60)
    if m.sum() < 200:
        return None
    q = p[m]
    if tipo == 'blanca':                      # la mitad más clara (la cara iluminada de la tela)
        Lq = q @ [0.2126, 0.7152, 0.0722]; q = q[Lq >= np.median(Lq)]
    mm = q.mean(0)
    return dict(zona_1080=[xa, ya, xb, yb], pixeles=int(len(q)), rgb=[round(v, 1) for v in mm],
                b_menos_r=round(mm[2] - mm[0], 1), g_menos_r=round(mm[1] - mm[0], 1))


def celeste_medio(f, mask):
    import colorsys
    q = f[mask].reshape(-1, 3).astype(np.float64).mean(0)
    h, l_, s_ = colorsys.rgb_to_hls(*(q / 255))
    return dict(rgb=[round(v, 1) for v in q], tono_grados=round(h * 360, 1), sat_hls=round(s_, 3))


def etapa_medir():
    M = T / 'med'; M.mkdir(parents=True, exist_ok=True)
    rep = {}
    for clave in MED:
        fr, res, filas = medir_estampado(clave)
        tipo, n0 = MED[clave][0], MED[clave][1]
        dibujar(fr, res, M / f'estampado_{clave}.jpg', n0, clave[4:])
        col = []
        for k in range(0, len(fr), 6):
            c = parche_tela(fr[k], res[k]['founders'], tipo)
            if c:
                c['cuadro_fuente'] = n0 + k
                if tipo == 'blanca':
                    c['celeste'] = celeste_medio(fr[k], res[k]['mask'])
                col.append(c)
        rep[clave] = dict(tipo=tipo, ganancias_video_py=V.TOMAS[clave[:8]].get('g'), por_cuadro=filas, tela=col)
        print(clave, 'cuadros', len(filas), flush=True)
        for f in filas[::6]:
            print('  ', f['cuadro_fuente'], f['bbox_nat'], 'cx', f['cx_nat'], 'cy', f['cy_nat'], 'w', f['w_nat'], flush=True)
        for c in col:
            print('   tela', c['cuadro_fuente'], c['rgb'], 'B-R', c['b_menos_r'], 'G-R', c['g_menos_r'],
                  c.get('celeste', ''), flush=True)
    # referencia de producto (fotos de estudio, Display P3 → sRGB con video.foto_srgb)
    from PIL import Image
    prod = {}
    for nom, caja in (('blanca_espalda_estudio', (292, 1316, 877, 1755)), ('negra_espalda_estudio', (292, 1228, 877, 1462))):
        V.foto_srgb(R / 'PRODUCTO' / f'{nom}.jpg', M / f'{nom}_srgb.png')
        im = np.asarray(Image.open(M / f'{nom}_srgb.png').convert('RGB'))
        prod[nom] = U.color_parche(im, caja)
        if nom.startswith('blanca'):
            x0, y0, x1, y1 = (100, 800, 1100, 1300); p = im[y0:y1, x0:x1].reshape(-1, 3).astype(np.float64)
            m = (p[:, 2] - p[:, 0] > 20) & (p[:, 2] - p[:, 1] > 4)
            import colorsys
            q = p[m].mean(0); h, l_, s_ = colorsys.rgb_to_hls(*(q / 255))
            prod['celeste_espalda_estudio'] = dict(rgb=[round(v, 1) for v in q], tono_grados=round(h * 360, 1),
                                                   sat_hls=round(s_, 3))
    rep['producto'] = prod
    rep.update(medir_tela_fija())
    print('producto', prod, flush=True)
    json.dump(rep, open(M / 'medir.json', 'w'), ensure_ascii=False, indent=1)


# 7885: la Blanca del final de 5b está tendida sobre la roca y su estampado es chico (a 1080 el detector tomaba la roca
# y el parche «debajo del estampado» medía piedra: tono 31°, B−R −30, y la ganancia azulaba la Blanca a B−R +45 en el
# primer render). Se mide la tela en una zona fija de la espalda, debajo de «Founders Privée» y arriba del brazo de
# Gianluca, en los cuadros de fuente 116–124 (c260–c268, z 1: coordenadas de la toma / 2 = máster).
TELA_FIJA = {'IMG_7885c': ('IMG_7885', (116, 120, 124), (450, 900, 850, 1150))}


def medir_tela_fija():
    out = {}
    for clave, (toma, cuadros, (x0, y0, x1, y1)) in TELA_FIJA.items():
        fr = U.leer(V._src(toma), W, H, n0=min(cuadros), n1=max(cuadros), vf_pre=_COLOR0(toma))
        tela = []
        for n in cuadros:
            pz = fr[n - min(cuadros)][y0:y1, x0:x1].reshape(-1, 3).astype(np.float64)
            L = pz @ [0.2126, 0.7152, 0.0722]; sat = (pz.max(1) - pz.min(1)) / (pz.max(1) + 1)
            q = pz[(L > 150) & (sat < 0.3)]
            Lq = q @ [0.2126, 0.7152, 0.0722]; q = q[Lq >= np.median(Lq)]
            mm = q.mean(0)
            tela.append(dict(cuadro_fuente=n, zona_1080=[x0, y0, x1, y1], pixeles=int(len(q)),
                             rgb=[round(v, 1) for v in mm], b_menos_r=round(mm[2] - mm[0], 1),
                             g_menos_r=round(mm[1] - mm[0], 1)))
        out[clave] = dict(tipo='blanca', zona_fija=True, por_cuadro=[], tela=tela)
        print(clave, tela, flush=True)
    return out


def etapa_tela():
    med = json.load(open(T / 'med' / 'medir.json'))
    med.update(medir_tela_fija())
    json.dump(med, open(T / 'med' / 'medir.json', 'w'), ensure_ascii=False, indent=1)


# =====================================================================================================
# color: blanco neutro (corrección 4 de Roma) sobre las ganancias de video.py
# =====================================================================================================
# Ganancia por canal calculada con la tela blanca lisa medida (etapa medir, mediana de los cuadros usados): g = media
# RGB / RGB, así el blanco queda con R = G = B (producto de estudio: B−R +0,7, G−R +0,7). Se aplica como CURVA que pesa
# la ganancia por el valor (0 hasta 0,15, completa desde 0,45, suave en el medio) y por la saturación (ver lut_cube):
# neutraliza la tela clara, no corre los negros (en 7885 una ganancia plana volvía azul la Negra: B−R +2,4 → +10) ni el
# celeste. Va después de la cadena de video.py
# (en las HLG, después de su colorchannelmixer). video.py no se modifica: se envuelve video.color en este proceso.
COLOR_RANGO = {'IMG_4530': ('IMG_4530', 18, 72), 'IMG_4625': ('IMG_4625', 0, 45), 'IMG_8002': ('IMG_8002', 78, 106),
               'IMG_7885': ('IMG_7885c', 116, 124)}
COLOR_RANGO_ALT = {'IMG_8002': ('IMG_8002a', 0, 26)}
CURVAS = {}
_COLOR0 = V.color


def _color_vir02(toma):
    c = _COLOR0(toma)
    if toma not in CURVAS:
        return c
    assert c.endswith('format=yuv420p'), c
    return c[:-len('format=yuv420p')] + 'format=gbrp,' + CURVAS[toma] + ',format=yuv420p'


V.color = _color_vir02


def curva(g, x0=0.15, x1=0.45):
    pts = []
    for x in np.linspace(0, 1, 21):
        u = float(np.clip((x - x0) / (x1 - x0), 0, 1)); s = u * u * (3 - 2 * u)
        y = float(np.clip(x * (1 + (g - 1) * s), 0, 1))
        pts.append(f'{x:.2f}/{y:.4f}')
    return ' '.join(pts)


def ganancias(rangos=COLOR_RANGO):
    med = json.load(open(T / 'med' / 'medir.json'))
    out = {}
    for toma, (clave, a, b) in rangos.items():
        tela = [t for t in med[clave]['tela'] if a <= t['cuadro_fuente'] <= b]
        rgb = np.median([t['rgb'] for t in tela], axis=0)
        g = rgb.mean() / rgb
        out[toma] = dict(medido_en=clave, cuadros=[t['cuadro_fuente'] for t in tela], rgb_tela=[round(v, 1) for v in rgb],
                         b_menos_r=round(rgb[2] - rgb[0], 1), g_menos_r=round(rgb[1] - rgb[0], 1),
                         ganancia_rgb=[round(v, 4) for v in g])
    return out


# v01 final: LUT 3D en vez de curvas por canal. Con las curvas (primer máster de prueba) la tela quedaba neutra pero el
# celeste giraba 1,6–3,7° (4530 211,1° → 207,4°; 4625 211,6° → 209,2°; 8002 208,2° → 206,6°): «celeste intacto» no se
# cumplía. La LUT aplica la ganancia solo a lo poco saturado: peso = valor (0 hasta 0,15, completo desde 0,45) ×
# saturación (completo hasta 0,12, nada desde 0,20). La tela blanca mide saturación 0,05–0,10 (también en sombra) y el
# celeste 0,23–0,32: la tela se corrige y el celeste queda como en la fuente.
LUT_SAT = (0.12, 0.20)
LUT_VAL = (0.15, 0.45)


def _suave(x, a, b):
    u = np.clip((x - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


def lut_cube(g, salida, n=33):
    v = np.linspace(0, 1, n)
    B_, G_, R_ = np.meshgrid(v, v, v, indexing='ij')          # en .cube el rojo cambia más rápido
    c = np.stack([R_, G_, B_], -1).reshape(-1, 3)
    mx = c.max(1); mn = c.min(1); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0)
    w = _suave(mx, *LUT_VAL) * (1 - _suave(sat, *LUT_SAT))
    o = np.clip(c * (1 + (np.array(g)[None, :] - 1) * w[:, None]), 0, 1)
    with open(salida, 'w') as f:
        f.write(f'TITLE "vir02n {Path(salida).stem}"\nLUT_3D_SIZE {n}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        f.writelines(f'{x:.6f} {y:.6f} {z:.6f}\n' for x, y, z in o)
    return salida


def activar_color(rangos=COLOR_RANGO):
    gs = ganancias(rangos)
    (T / 'lut').mkdir(parents=True, exist_ok=True)
    for toma, d in gs.items():
        f = lut_cube(d['ganancia_rgb'], T / 'lut' / f"{toma}_{d['medido_en']}.cube")
        CURVAS[toma] = f'lut3d=file={f}:interp=tetrahedral'
    return gs


# =====================================================================================================
# etapa 3 · planos: encuadre que deja «Founders Privée» en (540, 1000) y 920 px de ancho en cada cuadro de corte
# =====================================================================================================
P = T / 'planos'
OBJ = (540.0, 1000.0, 920.0)          # centro x, centro y, ancho (guion G1 §Regla del empalme)
TOL = (40.0, 60.0, 110.0)
ZMAX = 2.5
NOMINAL = {  # plano: (toma, cuadro de fuente nominal (tabla de Roma), cuadros, modo)
    'P1': ('IMG_7824', 0, 54, 'seguir'),      # c0–c53    7824 0,000–1,800
    'P2': ('IMG_4530', 27, 36, 'seguir'),     # c54–c89   4530 ≈0,9–2,1
    'P3': ('IMG_4625', 0, 36, 'seguir'),      # c90–c125  4625 0,0–1,2
    'P4': ('IMG_8002', 89, 18, 'fijo'),       # c126–c143 8002 3,0–3,6 → 2,967–3,567 (la toma termina en el cuadro 106)
    'P5': ('IMG_7885', 0, 126, 'abrir'),      # c144–c269 7885 0,0–4,2 (5a c144–c173 abre 30 cuadros; 5b c174–c269 z 1)
}
M0 = {'P1': 0, 'P2': 54, 'P3': 90, 'P4': 126, 'P5': 144}
NF = 270
DUR = NF / FPS


def lin(a, b, n):
    return [a + (b - a) * k / (n - 1) for k in range(n)] if n > 1 else [a]


_PTS = {}


def pts_toma(toma):
    """pts de cada cuadro de la fuente (ffprobe por cuadro, una vez por toma)."""
    if toma not in _PTS:
        _PTS[toma] = U.tiempos_src(toma)
    return _PTS[toma]


def mapa_fuente(toma, n0, nf):
    """índice de cuadro de la fuente que entrega fps=30 en cada cuadro k del plano (plano_z busca el pts del cuadro n0):
    el cuadro j cae en k = round((pts_j − pts_n0)·30); si dos caen en el mismo k gana el último, si ninguno se repite."""
    pts = pts_toma(toma)
    k_de = {}
    for j in range(n0, len(pts)):
        k = round((pts[j] - pts[n0]) * FPS)
        if k >= nf:
            break
        k_de[k] = j
    out, ult = [], n0
    for k in range(nf):
        ult = k_de.get(k, ult); out.append(ult)
    return out


def salida(toma, bb, Z, cx, cy):
    """dónde cae el recuadro bb (x0, y0, x1, y1, coordenadas de la toma) en 1080×1920 con la ventana de plano_z."""
    nw, nh = V.TOMAS[toma]['nat']
    Z = max(1.0, round(Z, 6)); w, h = nw / Z, nh / Z
    x = min(max(cx - w / 2, 0), nw - w); y = min(max(cy - h / 2, 0), nh - h)
    x0, y0, x1, y1 = bb
    return ((x0 + x1) / 2 - x) * W / w, ((y0 + y1) / 2 - y) * H / h, (x1 - x0) * W / w


def error(o):
    return max(abs(o[0] - OBJ[0]) / TOL[0], abs(o[1] - OBJ[1]) / TOL[1], abs(o[2] - OBJ[2]) / TOL[2])


def optimo(toma, bb):
    """z en [1, 2,5] y ventana (limitada al cuadro) que minimizan el error normalizado máx(|dx|/40, |dy|/60, |dw|/110)."""
    nw, nh = V.TOMAS[toma]['nat']
    x0, y0, x1, y1 = bb; bcx, bcy = (x0 + x1) / 2, (y0 + y1) / 2
    mejor = None
    for Z in np.arange(1.0, ZMAX + 1e-9, 0.002):
        w, h = nw / Z, nh / Z
        x = min(max(bcx - w / 2, 0), nw - w); y = min(max(bcy - OBJ[1] * h / H, 0), nh - h)
        cx, cy = x + w / 2, y + h / 2
        o = salida(toma, bb, Z, cx, cy); e = error(o)
        clave = (round(e, 4), abs(o[2] - OBJ[2]))
        if mejor is None or clave < mejor[0]:
            mejor = (clave, float(Z), cx, cy, o, e)
    return dict(Z=round(mejor[1], 4), cx=round(mejor[2], 2), cy=round(mejor[3], 2),
                salida=[round(v, 1) for v in mejor[4]], error=round(mejor[5], 3))


def bbox_fuente(clave):
    """recuadro por cuadro de fuente (coordenadas de la toma); si la etapa refinar midió ese cuadro sobre la imagen
    ampliada del plano, manda esa medición."""
    med = json.load(open(T / 'med' / 'medir.json'))
    out = {f['cuadro_fuente']: f['bbox_nat'] for f in med[clave]['por_cuadro']}
    if REFINADO.exists():
        out.update({int(k): v for k, v in json.load(open(REFINADO)).get(clave, {}).items()})
    return out


REFINADO = T / 'med' / 'refinado.json'


def medir_render(video, toma, fuente, zs, cxs, cys, cuadros, tipo, par, roi):
    """mide el estampado en cuadros de un plano ya renderizado (la imagen ampliada separa mejor la tela, la sombra y
    las letras que la toma a 1080) y lo devuelve en coordenadas de la toma con la ventana de plano_z de cada cuadro."""
    nw, nh = V.TOMAS[toma]['nat']
    fr = U.leer(video, W, H, n0=min(cuadros), n1=max(cuadros))
    out = {}
    for k in cuadros:
        bb, _ = estampado(fr[k - min(cuadros)], tipo, roi, **par)
        Z = max(1.0, round(zs[k], 6)); w, h = nw / Z, nh / Z
        x = min(max(cxs[k] - w / 2, 0), nw - w); y = min(max(cys[k] - h / 2, 0), nh - h)
        x0, y0, x1, y1 = bb
        out[fuente[k]] = [round(x + x0 * w / W, 1), round(y + y0 * h / H, 1), round(x + (x1 + 1) * w / W, 1),
                          round(y + (y1 + 1) * h / H, 1)]
    return out


def etapa_refinar():
    """(1) 7885 cuadro 0 (c144): la medición a 1080 recortaba «Privée» contra el borde de la zona y daba z 2,36 con el
    estampado corrido (medido en el render: centro 474, ancho 791); se mide sobre ese cuadro ampliado, sin la R de
    ROCCÉ. (2) 8002 0,2–0,8 (alternativa del plano 4): el borde superior saltaba ±30 px entre cuadros a 1080; se mide
    cada cuadro sobre el render de la alternativa."""
    pl = json.load(open(T / 'planos.json'))['plan']
    ref = json.load(open(REFINADO)) if REFINADO.exists() else {}
    d = pl['P5']
    ref['IMG_7885'] = {str(k): v for k, v in medir_render(
        P / 'P5.mp4', 'IMG_7885', d['fuente'], d['zs'], d['cxs'], d['cys'], [0], 'negra',
        dict(lf_max=115, dl_min=60, media_max=150, excluir=[(90, 870, 310, 995), (90, 1180, 330, 1260)]),
        (40, 880, 1040, 1250)).items()}
    a = json.load(open(T / 'plano4_alternativa.json'))
    ref['IMG_8002a'] = {str(k): v for k, v in medir_render(
        P / 'P4_alternativa_8002_0.2-0.8.mp4', 'IMG_8002', a['fuente'], a['zs'], a['cxs'], a['cys'], list(range(18)),
        'blanca', {}, (0, 820, 1079, 1300)).items()}
    json.dump(ref, open(REFINADO, 'w'), ensure_ascii=False, indent=1)
    for k, v in ref.items():
        print(k, v, flush=True)


def camino(toma, clave, n0, nf, suave=13, pin=6):
    """zoom y centro por cuadro: óptimo por cuadro (con el recuadro medido del cuadro de fuente que entrega fps=30),
    suavizado (Savitzky-Golay de `suave` cuadros, orden 2) y fijado al óptimo en los extremos (mezcla lineal en `pin`
    cuadros): los cuadros de corte quedan con el óptimo y en el medio el estampado no tiembla."""
    from scipy.signal import savgol_filter
    bbs = bbox_fuente(clave); src = mapa_fuente(toma, n0, nf)
    raw = [optimo(toma, bbs[j]) for j in src]
    R_ = {k: np.array([r[k] for r in raw]) for k in ('Z', 'cx', 'cy')}
    S_ = {k: savgol_filter(v, min(suave, nf - (1 - nf % 2)), 2, mode='interp') for k, v in R_.items()}
    wend = np.array([max(0.0, 1 - min(k, nf - 1 - k) / pin) for k in range(nf)])
    F_ = {k: S_[k] + (R_[k] - S_[k]) * wend for k in R_}
    F_['Z'] = np.clip(F_['Z'], 1.0, ZMAX)
    pred = [salida(toma, bbs[j], F_['Z'][k], F_['cx'][k], F_['cy'][k]) for k, j in enumerate(src)]
    return dict(fuente=src, zs=[float(v) for v in F_['Z']], cxs=[float(v) for v in F_['cx']],
                cys=[float(v) for v in F_['cy']], optimo=raw,
                prevision=[[round(a, 1), round(b, 1), round(c, 1), round(error((a, b, c)), 3)] for a, b, c in pred])


def elegir_n0(toma, clave, nominal, nf, rango):
    """cuadro inicial dentro de ±0,3 s (lo autoriza Roma) que minimiza el peor error de los dos cuadros de corte;
    a igual error, el más cercano al nominal. Solo se corre si el nominal no entra en tolerancia."""
    bbs = bbox_fuente(clave)
    def peor(n0):
        src = mapa_fuente(toma, n0, nf)
        if src[0] not in bbs or src[-1] not in bbs:
            return 9e9
        return max(optimo(toma, bbs[src[0]])['error'], optimo(toma, bbs[src[-1]])['error'])
    e_nom = peor(nominal)
    if e_nom <= 1.0:
        return nominal, e_nom, False
    cands = sorted(rango, key=lambda n: (round(peor(n), 3), abs(n - nominal)))
    return cands[0], peor(cands[0]), True


def plan():
    pl = {}
    for pid, (toma, n0, nf, modo) in NOMINAL.items():
        d = dict(toma=toma, n0_nominal=n0, cuadros=nf, modo=modo, m0=M0[pid])
        if modo == 'seguir':
            rango = {'P2': range(18, 37), 'P3': range(0, 10)}.get(pid, [n0])
            n0b, e, movido = elegir_n0(toma, toma, n0, nf, rango)
            d.update(n0=n0b, corrido=movido, peor_error_extremos=round(e, 3))
            d.update(camino(toma, toma, n0b, nf))
        elif modo == 'fijo':
            d.update(n0=n0, corrido=True, zs=[1.0] * nf, cxs=[V.TOMAS[toma]['nat'][0] / 2] * nf,
                     cys=[V.TOMAS[toma]['nat'][1] / 2] * nf, fuente=mapa_fuente(toma, n0, nf))
        else:   # abrir: 5a z0 → 1 lineal en 30 cuadros (guion), centro lineal al del cuadro entero; 5b z 1
            bb = bbox_fuente('IMG_7885')[0]
            o = optimo(toma, bb)
            nw, nh = V.TOMAS[toma]['nat']
            d.update(n0=n0, corrido=False, optimo_c144=o, zs=lin(o['Z'], 1.0, 30) + [1.0] * (nf - 30),
                     cxs=lin(o['cx'], nw / 2, 30) + [nw / 2] * (nf - 30), cys=lin(o['cy'], nh / 2, 30) + [nh / 2] * (nf - 30),
                     fuente=mapa_fuente(toma, n0, nf))
        d['t_fuente'] = [round(pts_toma(toma)[d['fuente'][0]], 4), round(pts_toma(toma)[d['fuente'][-1]], 4)]
        pl[pid] = d
        print(pid, toma, 'n0', d['n0'], 'fuente', d['t_fuente'], 'z', round(d['zs'][0], 3), '→', round(d['zs'][-1], 3),
              'prev', (d.get('prevision') or [None])[0], (d.get('prevision') or [None])[-1], flush=True)
    return pl


def etapa_planos():
    """python vir02n.py planos [P5 ...]: con nombres, vuelve a renderizar solo esos planos (el resto se reutiliza si su
    plan no cambió; se comprueba) y no rehace la alternativa del plano 4."""
    P.mkdir(parents=True, exist_ok=True)
    solo = sys.argv[2:]
    previo = json.load(open(T / 'planos.json')) if solo and (T / 'planos.json').exists() else None
    gs = activar_color()
    pl = plan()
    reg = []
    for pid, d in pl.items():
        if solo and pid not in solo:
            q = previo['plan'][pid]
            assert q['zs'] == d['zs'] and q['cxs'] == d['cxs'] and q['cys'] == d['cys'] and q['n0'] == d['n0'], pid
            p = next(x for x in previo['planos'] if x['id'] == pid)
        else:
            p = U.plano_z(d['toma'], d['n0'], d['zs'], d['cxs'], d['cys'], P / f'{pid}.mp4')
            p.update(id=pid, m0=d['m0'])
        reg.append(p); print(pid, p['cuadros'], flush=True)
    n = V.unir(reg, T / 'vir02n_video.mp4')
    assert n == NF, n
    json.dump(dict(cuadros=n, color=gs, curvas=CURVAS, plan=pl, planos=reg, refinado=json.load(open(REFINADO))
                   if REFINADO.exists() else None), open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1)
    if not solo:
        etapa_p4alt()


def etapa_p4alt():
    """alternativa propuesta para el plano 4 (solo prueba, no entra en el máster): 8002 0,200–0,767 (c6–c23)."""
    CURVAS.clear(); activar_color(); ga = activar_color(COLOR_RANGO_ALT)
    alt = dict(toma='IMG_8002', n0=6, cuadros=18); alt.update(camino('IMG_8002', 'IMG_8002a', 6, 18))
    pa = U.plano_z('IMG_8002', 6, alt['zs'], alt['cxs'], alt['cys'], P / 'P4_alternativa_8002_0.2-0.8.mp4')
    alt['color'] = ga['IMG_8002']
    json.dump(alt, open(T / 'plano4_alternativa.json', 'w'), ensure_ascii=False, indent=1)
    print('alternativa P4', alt['prevision'][0], alt['prevision'][-1], flush=True)


# =====================================================================================================
# etapa 3b · medición del empalme sobre el video RENDERIZADO (no sobre la previsión): recuadro de «Founders Privée» en
# los cuadros de corte del máster, con el mismo detector de la etapa medir (tipo y parámetros de cada toma)
# =====================================================================================================
EMP = {  # plano: (tipo, parámetros del detector, zona de búsqueda en el máster 1080×1920)
    # Negra: «Privée» sale en trazos sueltos (tono sobre tono), sin filtro de manchas
    'P1': ('negra', {}, (0, 700, 1079, 1300)),
    'P2': ('blanca', {}, (0, 700, 1079, 1300)),
    # 4625: una roca azulada en el borde izquierdo de c125 (2 % de la máscara) se sumaba al recuadro
    'P3': ('blanca', dict(min_frac=0.03), (0, 700, 1079, 1300)),
    'P4': ('blanca', {}, (0, 700, 1079, 1300)),
    # 7885 ampliado: sin la R de ROCCÉ (tono sobre tono, al sol pasa el umbral de la Negra) ni las rocas de abajo
    'P5': ('negra', dict(lf_max=115, dl_min=60, media_max=150, excluir=[(90, 870, 310, 995), (90, 1180, 330, 1260)]),
           (40, 880, 1040, 1250)),
}
CORTES_EMP = [(53, 'P1'), (54, 'P2'), (89, 'P2'), (90, 'P3'), (125, 'P3'), (126, 'P4'), (143, 'P4'), (144, 'P5')]


def plano_de(c):
    return [pid for pid, m0 in sorted(M0.items(), key=lambda x: x[1]) if c >= m0][-1]


def medir_cuadros(video, cuadros, quien=plano_de, tipo_par=None):
    """recuadro del estampado en cuadros del video (índices); devuelve filas y (cuadro, máscara, recuadro) para hojas."""
    fr = U.leer(video, W, H, n0=min(cuadros), n1=max(cuadros))
    filas, vis = [], []
    for c in cuadros:
        img = fr[c - min(cuadros)]
        pid = quien(c)
        tipo, par, roi = tipo_par or EMP[pid]
        bb, m = estampado(img, tipo, roi, **par)
        if bb is None:
            filas.append(dict(cuadro=c, plano=pid, recuadro=None)); continue
        x0, y0, x1, y1 = bb
        o = ((x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2, x1 + 1 - x0)
        filas.append(dict(cuadro=c, plano=pid, recuadro=[x0, y0, x1, y1], centro_x=o[0], centro_y=o[1], ancho=o[2],
                          dx=round(o[0] - OBJ[0], 1), dy=round(o[1] - OBJ[1], 1), dw=round(o[2] - OBJ[2], 1),
                          error_norm=round(error(o), 3), dentro=bool(error(o) <= 1.0)))
        vis.append((c, img, m, bb))
    return filas, vis


def hoja_emp(vis, salida, rot, ancho=270, cols=4):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 34)
    tiles = []
    for c, img, m, bb in vis:
        ov = img.copy(); ov[m] = (ov[m] * 0.3 + np.array([255, 0, 0]) * 0.7).astype(np.uint8)
        im = Image.fromarray(ov); d = ImageDraw.Draw(im)
        d.rectangle(list(bb), outline=(255, 255, 0), width=5)
        tx0, ty0 = OBJ[0] - OBJ[2] / 2, OBJ[1]
        d.rectangle([OBJ[0] - TOL[0], OBJ[1] - TOL[1], OBJ[0] + TOL[0], OBJ[1] + TOL[1]], outline=(0, 255, 0), width=4)
        d.line([OBJ[0] - (OBJ[2] - TOL[2]) / 2, 1250, OBJ[0] + (OBJ[2] - TOL[2]) / 2, 1250], fill=(0, 255, 0), width=8)
        d.line([OBJ[0] - (OBJ[2] + TOL[2]) / 2, 1275, OBJ[0] + (OBJ[2] + TOL[2]) / 2, 1275], fill=(0, 200, 255), width=8)
        d.rectangle([0, 0, 1079, 52], fill=(0, 0, 0))
        x0, y0, x1, y1 = bb
        d.text((10, 8), f'{rot} c{c}  centro ({(x0 + x1 + 1) / 2:.0f}, {(y0 + y1 + 1) / 2:.0f})  ancho {x1 + 1 - x0}',
               font=fnt, fill=(255, 255, 0))
        tiles.append(im.resize((ancho, round(ancho * H / W))))
    th = tiles[0].height; filas = math.ceil(len(tiles) / cols)
    Wd = Image.new('RGB', (cols * (ancho + 2), filas * (th + 2)), (32, 32, 32))
    for i, t in enumerate(tiles):
        Wd.paste(t, ((i % cols) * (ancho + 2), (i // cols) * (th + 2)))
    Wd.save(salida, quality=90)


def etapa_empalmes():
    """mide el estampado en los cuadros de corte del video base y de la alternativa del plano 4; tabla + hojas."""
    E = T / 'empalmes'; E.mkdir(parents=True, exist_ok=True)
    cuadros = sorted({c for c, _ in CORTES_EMP})
    filas, vis = medir_cuadros(T / 'vir02n_video.mp4', cuadros)
    hoja_emp(vis, E / 'empalmes_master.jpg', 'máster')
    # alternativa del plano 4 (8002 0,200–0,767): sus cuadros 0 y 17 irían en c126 y c143
    fa, va = medir_cuadros(P / 'P4_alternativa_8002_0.2-0.8.mp4', [0, 17], quien=lambda c: 'P4')
    for f in fa:
        f['cuadro_en_maestro'] = 126 + f['cuadro']
    hoja_emp(va, E / 'empalmes_alternativa_P4.jpg', 'alt P4')
    # c0 (inicio) y final de 5b: la Blanca completa (márgenes del estampado; z = 1, coordenadas de la toma / 2)
    f0, v0 = medir_cuadros(T / 'vir02n_video.mp4', [0])
    fb, vb = medir_cuadros(T / 'vir02n_video.mp4', list(range(240, 270)),
                           tipo_par=('blanca', dict(min_frac=0.03), (0, 450, 1079, 1350)))
    from scipy import ndimage as nd
    fr5 = U.leer(T / 'vir02n_video.mp4', W, H, n0=240, n1=269)
    for f, img in zip(fb, fr5):
        if f['recuadro']:
            f['margen_izq'] = f['recuadro'][0]; f['margen_der'] = W - 1 - f['recuadro'][2]
        # silueta de la Blanca: tela clara (mín. de canales > 185) conectada, la mayor en y 450–1400
        m = img[450:1400].min(2) > 185
        m = nd.binary_opening(m, iterations=2)
        lab, n = nd.label(m)
        if n:
            k = 1 + int(np.argmax(nd.sum(m, lab, np.arange(1, n + 1))))
            ys, xs = np.nonzero(lab == k)
            f['remera'] = [int(xs.min()), int(ys.min()) + 450, int(xs.max()), int(ys.max()) + 450]
            f['remera_margen_izq'] = int(xs.min()); f['remera_margen_der'] = int(W - 1 - xs.max())
    hoja_emp(vb[::3], E / 'blanca_final_5b.jpg', 'Blanca 5b', cols=5)
    rep = dict(objetivo=dict(centro=OBJ[:2], ancho=OBJ[2], tolerancia=TOL), master=filas, alternativa_P4=fa, c0=f0,
               blanca_final_5b=[{k: v for k, v in f.items() if k in ('cuadro', 'recuadro', 'margen_izq', 'margen_der', 'remera',
                                                                     'remera_margen_izq', 'remera_margen_der')}
                                for f in fb])
    json.dump(rep, open(E / 'empalmes.json', 'w'), ensure_ascii=False, indent=1)
    for f in filas + fa + f0:
        print(f, flush=True)
    for f in rep['blanca_final_5b'][::3]:
        print(f)


# =====================================================================================================
# etapa 4 · sonido: plan de Fede (TEMP, 100 BPM, Re menor) trasladado a los cortes de Roma con las mismas funciones
# (hueco antes de cada corte, toque en cada empalme, drop en la revelación). Música, ambiente y foley en mezclas
# separadas que se suman (como vir01): la tabla de niveles por capa es exacta.
# Cortes c54 (1,8 = k3), c90 (3,0 = k5), c126 (4,2 = k7), c144 (4,8 = k8, DROP); CTA c198 (6,6 = k11); fin 9,0.
# =====================================================================================================
A = T / 'audio'
HUECOS = [(1.65, 1.80), (2.85, 3.00), (4.50, 4.80)]   # Fede: 2,25–2,40 / 4,05–4,20 / 5,70–6,00 (mismas duraciones)


def musica(m):
    ch = lambda t0, t1, g=.08: [m.charles(round(float(t), 3), g) for t in np.arange(t0, t1 - 1e-6, 0.3)]
    # intro c0–c53 (Fede: pad 2,2 s; acá 1,5 s con r 0,15 para que termine antes del hueco 1,65)
    # niveles: con los de Fede (pad .06, charles .07–.10, subida .14) el gancho medía −30 LUFS M contra −10…−15 del
    # resto (falla 4 de VIR-01 v01); se suben para que ningún tramo de 0,4 s quede bajo −24 salvo los huecos
    m.pad(0.0, [50, 53, 57], 1.5, MG['pad_intro'], 1000, a=.1, r=.15)
    for i, t in enumerate(np.arange(0.0, 1.51, 0.3)):
        m.charles(round(float(t), 3), MG['ch_intro'][0] + (MG['ch_intro'][1] - MG['ch_intro'][0]) * i / 5)
    m.subida(1.05, 1.65, MG['subida'])
    # corte 1 (c54, 4530)
    m.bombo(1.8, .8); m.ocho08(1.8, 38, .55, .5, glide_desde=45); m.pad(1.8, [50, 53, 57], 1.0, .06, 1300, r=.3)
    m.palma(2.4); ch(1.8, 2.85)
    # corte 2 (c90, 4625)
    m.bombo(3.0, .85); m.ocho08(3.0, 41, .5, .5, glide_desde=45); m.pad(3.0, [46, 50, 53], 1.2, MG['pad_c90'], 1300, r=.3)
    m.redoble(3.60, 4.50, MG['redoble']); m.subida(3.80, 4.50, MG['subida_c90'])
    # corte 3 (c126, 8002)
    m.bombo(4.2, .6)
    # drop (c144, 7885: revelación)
    m.bombo(4.8, 1.0); m.impacto(4.8, .40); m.ocho08(4.8, 38, 1.1, .6, glide_desde=45)
    m.pad(4.8, [50, 53, 57, 62], 1.8, MG['pad_drop']); ch(4.8, 6.6); m.palma(5.4); m.palma(6.0)
    # CTA (c198). Fede dejaba 1,2 s sin música entre la segunda nota y el toque final (8,9–9,6 en su tabla = 7,7–8,4
    # acá: −32 LUFS M medido); se completa con la misma línea (charles, tercera nota y un pad bajo), sin elementos nuevos
    m.bombo(6.6, .8); m.ocho08(6.6, 38, .5); m.ocho08(7.2, 41, .5); m.palma(7.2); m.ocho08(7.8, 38, .5)
    m.pad(6.6, [50, 53, 57], 1.8, MG['pad_cta'], 1200, r=.3); ch(6.6, 8.41, MG['ch_cta']); m.bombo(8.4, .8)
    for t0, t1 in HUECOS:
        m.silenciar('mus', t0, t1)
    m.fundido('mus', 8.50, 9.00)
    m.fundido('fx', 8.50, 9.00)      # colas de reverberación de la música (pista fx de ESTA mezcla)


MG = dict(pad_intro=.16, ch_intro=(.12, .18), subida=.30, pad_c90=.16, redoble=.50, subida_c90=.50, pad_drop=.10,
          pad_cta=.06, ch_cta=.09)

GAN_AMB = {   # toma: (fuente desde, máster desde, máster hasta, dB completa, dB sin música, pasa-altos)
    'IMG_7824': (0.000, 0.0, 1.8, -2, -3, 200),
    'IMG_4530': (0.900, 1.8, 3.0, -10, 4, 200),
    'IMG_4625': (0.000, 3.0, 4.2, 0, 6, None),
    'IMG_8002': (2.967, 4.2, 4.8, -10, -2, None),
    'IMG_7885': (0.000, 4.8, 9.0, -2, -8, None),
}
# sin música: la ola de 7885 (4,8–6,4) es 10 dB más fuerte que el resto del ambiente; se sube el tramo del CTA
# (curva de ganancia sobre la pista amb, rampa de 0,3 s) para que el LRA quede ≤ 8 (falla 5 de VIR-01 v01)
CURVA_AMB_SIN = [(6.4, 9.0, 8.0, 0.3, 0.0)]


def ambientes(m, sin_musica=False):
    for toma, (s0, t0, t1, gc, gs, hp) in GAN_AMB.items():
        m.ambiente(toma, s0, t0, t1, gs if sin_musica else gc, hp=hp, fin_fade=.25 if toma == 'IMG_7885' else None)


def foley(m):
    m.tela(0.50, .6, .08)              # la Negra sostenida (7824)
    m.tela(2.10, .4, .10)              # la Blanca con viento (4530)
    # toque en cada empalme (Fede: 2400 / 2600 / 2800 / 3000 Hz) y toque final del CTA
    for t, f in ((1.80, 2400), (3.00, 2600), (4.20, 2800), (4.80, 3000)):
        m.toque(t, .20, f); m.log(t, f'toque {f} Hz')
    m.toque(8.40, .16, 2400); m.log(8.40, 'toque final 2400 Hz')
    # Fede llevaba un barrido en 2,40 por el barrido de 3 cuadros del corte 1; Roma lo sacó de la imagen (empalme
    # limpio): sin causa visible, el barrido de sonido no va (se anota en la hoja).


def mezclas():
    from sonido import Mezcla
    mus, amb, ambs, fol = Mezcla(DUR), Mezcla(DUR), Mezcla(DUR), Mezcla(DUR)
    musica(mus); ambientes(amb); ambientes(ambs, sin_musica=True); foley(fol)
    ambs.pistas['amb'] *= U2.curva(ambs.N, CURVA_AMB_SIN)[:, None]

    def suma(*ms):
        t = Mezcla(DUR)
        for k in t.pistas:
            t.pistas[k] = sum(x.pistas[k] for x in ms)
        t.ev = [e for x in ms for e in x.ev]
        return t
    return dict(mus=mus, amb=amb, fol=fol, completa=suma(mus, amb, fol), sinmusica=suma(ambs, fol))


def duck(P_bombo, duck_db=6.0, sr=48000):
    N = len(P_bombo); bk = np.abs(P_bombo).mean(1)
    a = np.exp(-1 / (0.12 * sr)); e = np.zeros(N); acc = 0.0
    pk = np.convolve(bk, np.ones(64) / 64, 'same')
    for i in range(0, N, 64):
        acc = max(pk[i:i + 64].max(), acc * a ** 64); e[i:i + 64] = acc
    e = e / (e.max() + 1e-9)
    return 1 - (1 - 10 ** (-duck_db / 20)) * e


def bajos(mom, lim=-24.0):
    """ventanas de 400 ms (que terminan en t) bajo `lim` LUFS M que no tocan ningún hueco ni el primer 0,4 s."""
    out = []
    for x in mom:
        t = x['t']
        if t < 0.4 - 1e-6 or t > DUR + 1e-6:
            continue
        if any(t - 0.4 < h1 - 1e-6 and t > h0 + 1e-6 for h0, h1 in HUECOS):
            continue
        if x['M'] < lim:
            out.append([round(t, 1), x['M']])
    return out


def etapa_audio():
    A.mkdir(parents=True, exist_ok=True)
    Mz = mezclas()
    res = {}
    for k in ('completa', 'sinmusica'):
        res[k] = Mz[k].exportar(str(A / f'vir02n_{k}.wav'), lufs=-14)
        print(k, res[k], flush=True)
    import soundfile as sf
    gan = json.load(open(A / 'vir02n_completa_eventos.json'))['ganancia_db']; g = 10 ** (gan / 20)
    mu = Mz['mus'].pistas
    capas = dict(mus=(mu['mus'] * duck(mu['bombo'])[:, None] + mu['bombo']) * g, mus_fx=mu['fx'] * g,
                 fol=Mz['fol'].pistas['fx'] * g, amb=Mz['amb'].pistas['amb'] * g)
    for k, v in capas.items():
        sf.write(str(A / f'capa_{k}.wav'), v.astype(np.float32), SR, subtype='FLOAT')
    gan_s = json.load(open(A / 'vir02n_sinmusica_eventos.json'))['ganancia_db']
    mom = {k: U2.momentanea(A / f'vir02n_{k}.wav') for k in ('completa', 'sinmusica')}
    tr = TRAMOS_M
    rep = dict(completa=res['completa'], sinmusica=res['sinmusica'], ganancia_completa_db=gan, ganancia_sinmusica_db=gan_s,
               momentanea_por_tramo={k: U2.momentanea_tramos(v, tr) for k, v in mom.items()},
               lra={k: U.ebur(A / f'vir02n_{k}.wav')['lra'] for k in mom})
    rep['bajo_-24_fuera_de_huecos'] = {k: bajos(v) for k, v in mom.items()}
    rep['momentanea_0.1s'] = {k: [[round(x['t'], 1), x['M']] for x in v] for k, v in mom.items()}
    json.dump(rep, open(A / 'audio.json', 'w'), ensure_ascii=False, indent=1)
    print('bajo -24 fuera de huecos', rep['bajo_-24_fuera_de_huecos'])
    for k, v in rep['momentanea_por_tramo'].items():
        for x in v:
            print(k, x, flush=True)
    print('LRA', rep['lra'])


TRAMOS_M = [('1 7824 Negra balcón 0,0–1,65', 0.0, 1.65), ('hueco 1 1,65–1,80', 1.65, 1.80),
            ('2 4530 Blanca balcón 1,8–2,85', 1.8, 2.85), ('hueco 2 2,85–3,00', 2.85, 3.0),
            ('3 4625 Blanca roca 3,0–4,2', 3.0, 4.2), ('4 8002 baranda 4,2–4,5', 4.2, 4.5),
            ('hueco 3 4,5–4,8', 4.5, 4.8), ('5a drop + revelación 4,8–5,8', 4.8, 5.8),
            ('5b 5,8–6,6', 5.8, 6.6), ('CTA 6,6–9,0', 6.6, 9.0), ('último 0,5 s', 8.5, 9.0)]


# =====================================================================================================
# etapa 5 · textos y máster (A/B × con/sin música)
# =====================================================================================================
# Tamaños de VIR-01 v02 (corrección 3 de Roma): hook cuerpo 120 (mayúscula 72 px), «El nombre.» CajaN_125 (cuerpo 72,
# borde 20), CTA en Caja (cuerpo 58, como VIR-01 v02), «link en bio» CajaN_link (cuerpo 38, borde 10: caja ≈ 57 px).
EST = {
    'CajaN_hook': ('Inter Display SemiBold', 120, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 33, 0, 3, 8, 0),
    'HookTexto': ('Inter Display SemiBold', 120, '&H00FFFFFF', '&H00000000', '&H00000000', 0, 0, 0, 1, 8, 0),
    'CajaN_125': ('Inter Display SemiBold', 72, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 20, 0, 3, 8, 0),
    'CajaN_link': ('Inter Display SemiBold', 38, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 10, 0, 3, 8, 0),
}
V.ESTILOS.update(EST)           # en memoria (video.py no se toca)
HOOKS = {'A': ['Cambia todo', 'menos una cosa.'], 'B': ['¿Qué no cambia?']}
HOOK_C = (0, 49)                # c0–c49: termina donde empieza el hueco 1 (1,65 s), como «¿La suelta?» en el guion
Y_HOOK, PASO, XB, YB = 250, 80, 33, 10
# Pop: mismo 118 % → 100 % en 90 ms del estilo de la casa, pero calculado por cuadro y alrededor del centro del bloque.
# Con el \t de libass cada renglón crece desde su ancla y en el hook A de dos renglones (a) la caja de c0 llegaba a
# y 504 (> 480) y (b) los renglones se pisaban. Además libass agranda la caja BorderStyle 3 más que el texto al escalar
# (medido: caja ×1,30, letras ×1,18), así que la caja se dibuja (\p1) con la geometría exacta de la caja de libass en
# reposo (medida en cajas_reposo; diferencia con la de libass ≤ 9/255 solo en los bordes) y se escala igual que el texto.
ESCALAS = [(0, 0.02, 1.18), (0.02, 0.05, 1.1133), (0.05, 0.08, 1.0467), (0.08, None, 1.0)]   # c0, c1, c2, c3→
Y_125, Y_CTA, Y_LINK = 240, 236, 336
TEXTOS_FIJOS = [  # (c inicial, c final, texto, estilo, y)
    (150, 197, 'El nombre.', 'CajaN_125', Y_125),
    (198, 269, 'GIVE HISTORY YOUR NAME.', 'Caja', Y_CTA),
    (198, 269, 'link en bio', 'CajaN_link', Y_LINK),
]
MAS = T / 'master'
NOMBRES = {'A': 'ROCCE_VIR02_NOMBRE_A_v01.mp4', 'B': 'ROCCE_VIR02_NOMBRE_B_v01.mp4',
           'A_sinmusica': 'ROCCE_VIR02_NOMBRE_A_SINMUSICA_v01.mp4', 'B_sinmusica': 'ROCCE_VIR02_NOMBRE_B_SINMUSICA_v01.mp4'}


def render_ass(textos, n, fondo='black', gris=False):
    p = T / 'ctrl' / f'render_{fondo}.ass'; p.parent.mkdir(parents=True, exist_ok=True)
    V.ass(textos, p)
    fmt = 'gray' if gris else 'rgb24'
    r = U.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color={fondo}:s=1080x1920:r=30:d={DUR + 1}', '-vf',
               f"subtitles={p}:fontsdir=/usr/share/fonts/opentype/inter,trim=start_frame={n}:end_frame={n + 1},format={fmt}",
               '-frames:v', '1', '-f', 'rawvideo', '-'])
    a = np.frombuffer(r, np.uint8)
    return a.reshape(H, W) if gris else a.reshape(H, W, 3)


def cajas_reposo(lineas):
    """caja de libass (CajaN_hook, \\xbord33 \\ybord10) de cada renglón en reposo, sobre blanco: (x0, y0, x1, y1) excl."""
    out = []
    for i, txt in enumerate(lineas):
        im = render_ass([dict(t0=0, t1=DUR, txt=txt, estilo='CajaN_hook', y=Y_HOOK + i * PASO,
                              extra=f'\\xbord{XB}\\ybord{YB}')], 10, 'white')
        ys, xs = np.nonzero(im.max(2) < 100)
        out.append([int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1])
    return out


def hook_eventos(hook):
    lineas = HOOKS[hook]; cj = cajas_reposo(lineas)
    yc = (min(c[1] for c in cj) + max(c[3] for c in cj)) / 2
    t_fin = (HOOK_C[1] + 0.5) / FPS     # tiempos a mitad de cuadro: el .ass redondea a centésimas (50/30 → 1,67 mostraba c50)
    ev = []
    for t0, t1, s in ESCALAS:
        t1 = t_fin if t1 is None else t1
        f = lambda x, y: (540 + (x - 540) * s, yc + (y - yc) * s)
        dib = []
        for x0, y0, x1, y1 in cj:
            a, b = f(x0, y0); c, d = f(x1, y1)
            dib.append(f'm {a:.1f} {b:.1f} l {c:.1f} {b:.1f} l {c:.1f} {d:.1f} l {a:.1f} {d:.1f}')
        ev.append(dict(t0=t0, t1=t1, txt='{\\p1}' + ' '.join(dib) + '{\\p0}', estilo='HookTexto', x=0, y=0, blur=False,
                       capa=0, extra='\\an7\\bord0\\shad0\\1c&H141414&', rol='caja hook'))
        for i, txt in enumerate(lineas):
            ev.append(dict(t0=t0, t1=t1, txt=txt, estilo='HookTexto', y=round(yc + (Y_HOOK + i * PASO - yc) * s, 2),
                           blur=False, capa=1, extra=f'\\fscx{s * 100:.2f}\\fscy{s * 100:.2f}', rol='hook'))
    return ev, dict(cajas_reposo=cj, centro_y=yc)


def textos(hook):
    ev, _ = hook_eventos(hook)
    for a, b, txt, est, y in TEXTOS_FIJOS:
        ev.append(dict(t0=(a - 0.5) / FPS, t1=(b + 0.5) / FPS, txt=txt, estilo=est, y=y, rol='fijo'))
    return ev


def remux_audio(master, wav, out):
    """= vir01.remux_audio: la versión sin música lleva EXACTAMENTE el flujo de video de la completa (x264 con VBV y
    4 hilos no repite el mismo flujo en dos corridas)."""
    V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(master), '-i', str(wav), '-map', '0:v:0', '-map', '1:a:0',
          '-c:v', 'copy', '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
          '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
          '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
          '-shortest', '-movflags', '+faststart', str(out)])
    return out


def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    for hook in ('A', 'B'):
        out = MAS / NOMBRES[hook]; out_sm = MAS / NOMBRES[f'{hook}_sinmusica']
        for o in (out, out_sm):
            if o.exists():
                raise RuntimeError(f'{o} ya existe: no se sobrescribe')
        a = V.ass(textos(hook), T / f'vir02n_textos_{hook}.ass')
        V.master(T / 'vir02n_video.mp4', A / 'vir02n_completa.wav', out, ass_path=a)
        remux_audio(out, A / 'vir02n_sinmusica.wav', out_sm)
        print('->', out, out_sm, flush=True)


# =====================================================================================================
# etapa 6 · control y evidencia (evidencia_v01/): todo medido sobre los MP4 entregados salvo donde se indica
# =====================================================================================================
EVID = T / 'evidencia_v01'
CORTES = [54, 90, 126, 144]


def hoja_cuadros(mp4, cuadros, salida, rot='', ancho=240, cols=9):
    """cuadros exactos (por número) con su número impreso, en una tira o grilla."""
    from PIL import Image, ImageDraw, ImageFont
    fr = U.leer(mp4, W, H, n0=min(cuadros), n1=max(cuadros))
    fnt = ImageFont.truetype(FONT, 22); tiles = []
    for c in cuadros:
        im = Image.fromarray(fr[c - min(cuadros)]).resize((ancho, round(ancho * H / W)), Image.LANCZOS)
        d = ImageDraw.Draw(im); d.rectangle([0, 0, ancho, 28], fill=(0, 0, 0))
        d.text((5, 2), f'{rot}c{c} {c / FPS:.3f}s', font=fnt, fill=(255, 255, 0)); tiles.append(im)
    th = tiles[0].height; filas = math.ceil(len(tiles) / cols)
    Wd = Image.new('RGB', (min(cols, len(tiles)) * (ancho + 2), filas * (th + 2)), (30, 30, 30))
    for i, t in enumerate(tiles):
        Wd.paste(t, ((i % cols) * (ancho + 2), (i // cols) * (th + 2)))
    Wd.save(salida, quality=90)


def atomos(f):
    """átomos de primer nivel del MP4 en orden (faststart = moov antes de mdat)."""
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


def silencio_final(a, sr=SR, umbral=-60.0):
    """segundos al final del archivo con RMS de 10 ms por debajo de `umbral` dBFS."""
    w = sr // 100; m = a.mean(1); n = len(m) // w
    v = 20 * np.log10(np.sqrt(np.square(m[:n * w].reshape(n, w)).mean(1)) + 1e-12)
    k = 0
    while k < n and v[n - 1 - k] < umbral:
        k += 1
    return round(k * 0.01, 2)


def control_archivo(f):
    err = subprocess.run(nice(['ffmpeg', '-v', 'error', '-i', str(f), '-f', 'null', '-']), capture_output=True,
                         text=True).stderr.strip()
    pj = json.loads(U.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(f)]))
    cuerpo = f.read_bytes()
    gps = [m.decode() for m in (b'ISO6709', b'\xa9xyz', b'location', b'com.apple.quicktime') if m in cuerpo]
    vs = [s_ for s_ in pj['streams'] if s_['codec_type'] == 'video'][0]
    au = [s_ for s_ in pj['streams'] if s_['codec_type'] == 'audio'][0]
    a = U.audio_np(f)
    niv, v100, sil = U.niveles_tramos(a, TRAMOS_M)
    at = atomos(f)
    return dict(archivo=str(f), bytes=f.stat().st_size, sha256=hashlib.sha256(cuerpo).hexdigest(),
                md5_video=U.md5_stream(f, 'v'), md5_audio=U.md5_stream(f, 'a'),
                decodifica_completo=(err == ''), errores_decodificacion=err[:500],
                video=dict(codec=vs['codec_name'], perfil=vs.get('profile'), nivel=vs.get('level'), pix_fmt=vs['pix_fmt'],
                           ancho=vs['width'], alto=vs['height'], fps=vs['r_frame_rate'], cuadros=int(vs['nb_frames']),
                           duracion=float(vs['duration']), bitrate=int(vs.get('bit_rate', 0)),
                           color=dict(rango=vs.get('color_range'), matriz=vs.get('color_space'),
                                      transferencia=vs.get('color_transfer'), primarios=vs.get('color_primaries'))),
                audio=dict(codec=au['codec_name'], perfil=au.get('profile'), hz=int(au['sample_rate']),
                           canales=au['channels'], duracion=float(au['duration'])),
                audio_menos_video_s=round(float(au['duration']) - float(vs['duration']), 4),
                duracion_formato=float(pj['format']['duration']), etiquetas_formato=pj['format'].get('tags', {}),
                atomos=at, faststart=('moov' in at and 'mdat' in at and at.index('moov') < at.index('mdat')),
                marcas_gps_o_ubicacion=gps, sonoridad=U.ebur(f), niveles_por_tramo=niv,
                ventanas_100ms_bajo_menos50dbfs=sil, silencio_final_s=silencio_final(a), rms_100ms=v100), pj


def textos_limpios(ass_path):
    import re
    out = []
    for l in Path(ass_path).read_text(encoding='utf-8').splitlines():
        if l.startswith('Dialogue:'):
            cuerpo = l.split(',,0,0,0,,', 1)[1]
            if '\\p1' in cuerpo:
                continue
            t = re.sub(r'\{[^}]*\}', '', cuerpo)
            if t not in out:
                out.append(t)
    return out


def logicos(hook):
    """textos lógicos del máster: (nombre, c inicial, c final, eventos que lo dibujan)."""
    ev = textos(hook)
    hk = [e for e in ev if e['rol'] in ('hook', 'caja hook')]
    out = [(' / '.join(HOOKS[hook]), HOOK_C[0], HOOK_C[1], hk)]
    for a, b, txt, est, y in TEXTOS_FIJOS:
        out.append((txt, a, b, [e for e in ev if e['txt'] == txt]))
    return out


def mascara(evs, n, dil=0):
    from scipy import ndimage as nd
    g = render_ass(evs, n, gris=True) > 8
    return nd.binary_dilation(g, iterations=dil) if dil else g


def ctrl_textos():
    from scipy import ndimage as nd
    from PIL import Image, ImageDraw, ImageFont
    rep = dict(exactos={h: textos_limpios(T / f'vir02n_textos_{h}.ass') for h in 'AB'})
    base = T / 'vir02n_video.mp4'
    Yc = float(U2.lin(np.array([20.0, 20.0, 20.0])) @ [0.2126, 0.7152, 0.0722])
    t_caja = round(1.05 / (Yc + 0.05), 1)
    t_caja_blanca = round(1.05 / (Yc + 0.05), 1)           # #141414 sobre blanco: mismo cociente
    cajas, cont, lim, pop = {}, {}, [], {}
    for h in 'AB':
        mp4 = MAS / NOMBRES[h]
        for nom, a, b, evs in logicos(h):
            if h == 'B' and nom != ' / '.join(HOOKS['B']):
                continue
            # caja dibujada en el primer, medio y último cuadro, y en c0–c6 del hook (pop)
            ns = sorted({a, (a + b) // 2, b} | (set(range(0, 7)) if a == 0 else set()) | ({10} if a == 0 else set()))
            cj = {}
            for n in ns:
                ys, xs = np.nonzero(mascara(evs, n))
                cj[f'c{n}'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
            cajas[f'{h} · {nom}'] = dict(cuadros=f'c{a}–c{b}', cajas=cj,
                                         dentro_y_220_480=all(v[1] >= 220 and v[3] <= 480 for v in cj.values()))
            if a == 0:
                fin = cj['c10']
                pop[h] = dict(cajas=cj, termina_en=next((f'c{n}' for n in range(7) if cj[f'c{n}'] == fin), None))
            # contraste: texto sobre su caja (colores fijos) y caja contra el fondo (anillo de 4–16 px, video sin textos)
            filas = []
            for n in sorted(set(range(a, b + 1, 6)) | {b}):
                g = mascara(evs, n)
                f_ = U.leer(base, W, H, n0=n, n1=n)[0]
                anillo = nd.binary_dilation(g, iterations=16) & ~nd.binary_dilation(g, iterations=4)
                p = f_[anillo].astype(np.float64)
                Yb = U2.lin(p) @ np.array([0.2126, 0.7152, 0.0722])
                Ycaja = 1.0 if nom == 'GIVE HISTORY YOUR NAME.' else Yc
                r = (np.maximum(Yb, Ycaja) + 0.05) / (np.minimum(Yb, Ycaja) + 0.05)
                filas.append(dict(cuadro=n, caja_fondo_mediana=round(float(np.median(r)), 2),
                                  caja_fondo_p10=round(float(np.percentile(r, 10)), 2)))
            cont[f'{h} · {nom}'] = dict(
                texto_sobre_caja=f'{t_caja}:1 ' + ('(#141414 sobre caja blanca)' if nom == 'GIVE HISTORY YOUR NAME.'
                                                   else '(blanco sobre caja #141414)'),
                caja_fondo_mediana_min=min(x['caja_fondo_mediana'] for x in filas),
                caja_fondo_p10_min=min(x['caja_fondo_p10'] for x in filas), por_cuadro=filas)
            # límites: el texto se ve en [a, b] y no en a−1 ni b+1 (|máster − video sin textos| en su máscara)
            mk = mascara(evs, (a + b) // 2 if a else 10, dil=0)
            for n in (a - 1, a, b, b + 1):
                if n < 0 or n >= NF:
                    continue
                otros = [x for x in logicos(h) if x[0] != nom and x[1] <= n <= x[2]]
                m2 = mk.copy()
                for o in otros:
                    m2 &= ~mascara(o[3], n, dil=8)
                d = float(np.abs(U.leer(mp4, W, H, n0=n, n1=n)[0].astype(np.float32) -
                                 U.leer(base, W, H, n0=n, n1=n)[0].astype(np.float32))[m2].mean())
                lim.append(dict(maestro=h, texto=nom, pedido=f'c{a}–c{b}', cuadro=n, dif_media=round(d, 2),
                                visible=d > 20, debe_verse=a <= n <= b))   # texto: 60–145; ruido de códec en zona movida: ≤ 4,4
    rep.update(cajas=cajas, pop_hook=pop, contraste=cont, limites=lim,
               limites_ok=all(x['visible'] == x['debe_verse'] for x in lim))
    # tamaños: altura de mayúscula (H, L, E sin caja) y alto de la caja del link
    def mayus(est):
        fn, fs = V.ESTILOS[est][:2]
        V.ESTILOS['_m'] = (fn, fs, '&H00FFFFFF', '&H00000000', '&H00000000', 0, 0, 0, 1, 8, 0)
        g = render_ass([dict(t0=0, t1=DUR, txt='HLE', estilo='_m', y=300, blur=False)], 10, gris=True) > 128
        del V.ESTILOS['_m']
        ys = np.nonzero(g.any(1))[0]
        return int(ys.max() - ys.min() + 1)
    lk = cajas['A · link en bio']['cajas']['c230'] if 'c230' in cajas['A · link en bio']['cajas'] else \
        list(cajas['A · link en bio']['cajas'].values())[0]
    rep['tamanos'] = dict(mayuscula_hook_px=mayus('HookTexto'), mayuscula_el_nombre_px=mayus('CajaN_125'),
                          mayuscula_cta_px=mayus('Caja'), mayuscula_link_px=mayus('CajaN_link'),
                          caja_link_alto_px=lk[3] - lk[1] + 1,
                          a_360px=dict(mayuscula_hook=round(mayus('HookTexto') / 3, 1), caja_link=round((lk[3] - lk[1] + 1) / 3, 1),
                                       mayuscula_link=round(mayus('CajaN_link') / 3, 1)))
    # hoja a 360 px de ancho (escala de teléfono chico): cuadros enteros + zona de textos ampliada ×2 desde los 360 px
    fnt = ImageFont.truetype(FONT, 14)
    sel = [('A', 10, 'hook A c10'), ('A', 0, 'hook A c0 (pop)'), ('B', 10, 'hook B c10'), ('A', 175, 'El nombre. c175'),
           ('A', 230, 'CTA + link c230')]
    tiles = []
    for h, n, rot in sel:
        im = Image.fromarray(U.leer(MAS / NOMBRES[h], W, H, n0=n, n1=n)[0]).resize((360, 640), Image.LANCZOS)
        z = im.crop((0, 60, 360, 170)).resize((360, 110), Image.NEAREST)
        t = Image.new('RGB', (360, 640 + 110 + 20), (40, 40, 40)); t.paste(im, (0, 0)); t.paste(z, (0, 660))
        d = ImageDraw.Draw(t); d.text((4, 642), rot + ' · 360 px (abajo: y 180–510 a la misma escala)', font=fnt, fill=(255, 255, 0))
        tiles.append(t)
    Wd = Image.new('RGB', (len(tiles) * 362, tiles[0].height), (20, 20, 20))
    for i, t in enumerate(tiles):
        Wd.paste(t, (i * 362, 0))
    Wd.save(EVID / 'textos_360px.png')
    return rep


def ctrl_color():
    """tela blanca (B−R, G−R) y celeste (tono) en el máster contra la fuente sin corrección y PRODUCTO/."""
    med = json.load(open(T / 'med' / 'medir.json'))
    mp4 = MAS / NOMBRES['A']
    out = dict(producto=med['producto'], fuente_sin_correccion={}, master={})
    for clave in ('IMG_4530', 'IMG_4625', 'IMG_8002', 'IMG_7885c', 'IMG_7824', 'IMG_7885'):
        tl = med[clave]['tela']
        out['fuente_sin_correccion'][clave] = dict(
            b_menos_r_mediana=round(float(np.median([t['b_menos_r'] for t in tl])), 1),
            g_menos_r_mediana=round(float(np.median([t['g_menos_r'] for t in tl])), 1),
            celeste_tono_mediana=(round(float(np.median([t['celeste']['tono_grados'] for t in tl if t.get('celeste')])), 1)
                                  if any(t.get('celeste') for t in tl) else None))
    plan_ = {'P1': ('negra', [20, 53]), 'P2': ('blanca', [54, 72, 89]), 'P3': ('blanca', [90, 108, 125]),
             'P4': ('blanca', [126, 134, 143]), 'P5': ('negra', [144])}
    for pid, (tipo, ns) in plan_.items():
        filas, vis = medir_cuadros(mp4, ns, quien=lambda c, p=pid: p)
        for (c, img, m, bb) in vis:
            t_ = parche_tela(img, bb, tipo)
            fila = dict(cuadro=c, tela=t_)
            if tipo == 'blanca':
                fila['celeste'] = celeste_medio(img, m)
            out['master'][f'{pid} c{c}'] = fila
    # Blanca de 5b: misma zona fija que la medición de la ganancia
    x0, y0, x1, y1 = TELA_FIJA['IMG_7885c'][2]
    for c in (260, 264, 268):
        f_ = U.leer(mp4, W, H, n0=c, n1=c)[0]
        pz = f_[y0:y1, x0:x1].reshape(-1, 3).astype(np.float64)
        L = pz @ [0.2126, 0.7152, 0.0722]; sat = (pz.max(1) - pz.min(1)) / (pz.max(1) + 1)
        q = pz[(L > 150) & (sat < 0.3)]; Lq = q @ [0.2126, 0.7152, 0.0722]; q = q[Lq >= np.median(Lq)]; mm = q.mean(0)
        out['master'][f'P5 Blanca c{c}'] = dict(cuadro=c, tela=dict(zona_1080=[x0, y0, x1, y1], rgb=[round(v, 1) for v in mm],
                                                                     b_menos_r=round(mm[2] - mm[0], 1), g_menos_r=round(mm[1] - mm[0], 1)))
    return out


def ctrl_prendas():
    """Negra puesta en 5a (estampado medido c144–c173) y Blanca completa al final de 5b (silueta y márgenes)."""
    from scipy import ndimage as nd
    mp4 = MAS / NOMBRES['A']
    ns = list(range(144, 174, 3)) + [173]
    filas, vis = medir_cuadros(mp4, ns, quien=lambda c: 'P5',
                               tipo_par=('negra', dict(lf_max=115, dl_min=60, media_max=150), (0, 700, 1079, 1400)))
    negra = [{k: f.get(k) for k in ('cuadro', 'recuadro', 'centro_x', 'centro_y', 'ancho')} for f in filas]
    hoja_cuadros(mp4, ns, EVID / 'negra_puesta_5a_c144-c173.jpg', cols=11)
    fr = U.leer(mp4, W, H, n0=252, n1=269)
    blanca = []
    for k, img in enumerate(fr):
        c = 252 + k
        f = img.astype(np.float64); L = f @ [0.2126, 0.7152, 0.0722]; sat = (f.max(2) - f.min(2)) / (f.max(2) + 1)
        m = (L > 140) & (sat < 0.22); m[:450] = False
        m = nd.binary_opening(m, iterations=3)
        lab, n = nd.label(m)
        kk = 1 + int(np.argmax(nd.sum(m, lab, np.arange(1, n + 1))))
        ys, xs = np.nonzero(lab == kk)
        blanca.append(dict(cuadro=c, silueta=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                           margen_izq=int(xs.min()), margen_der=int(W - 1 - xs.max()), pixeles=int(len(xs))))
    hoja_cuadros(mp4, list(range(252, 270)), EVID / 'blanca_final_5b_c252-c269.jpg', cols=9)
    return dict(negra_5a=negra, blanca_5b=blanca)


def etapa_control():
    import shutil
    EVID.mkdir(parents=True, exist_ok=True); (EVID / 'cortes').mkdir(exist_ok=True)
    rep = dict(fecha='2026-11-18', pieza='VIR-02 «Lo que no se mueve» (respaldo sin voz) · máster v01', archivos={})
    for k, nombre in NOMBRES.items():
        r, pj = control_archivo(MAS / nombre)
        json.dump(pj, open(EVID / f'ffprobe_{k}.json', 'w'), indent=1)
        rep['archivos'][k] = r
        print(k, r['sonoridad'], r['md5_video'], r['md5_audio'], 'gps', r['marcas_gps_o_ubicacion'], 'faststart',
              r['faststart'], 'a−v', r['audio_menos_video_s'], 'silencio final', r['silencio_final_s'], flush=True)
    # hojas: ±4 cuadros alrededor de cada corte, inicio c0–c12 (A y B), final c257–c269, cada 0,5 s
    mA, mB = MAS / NOMBRES['A'], MAS / NOMBRES['B']
    for c in CORTES:
        hoja_cuadros(mA, list(range(c - 4, c + 5)), EVID / 'cortes' / f'corte_c{c:03d}_c{c - 4}-c{c + 4}.jpg')
    hoja_cuadros(mA, list(range(194, 203)), EVID / 'cortes' / 'entrada_CTA_c194-c202.jpg')
    hoja_cuadros(mA, list(range(0, 13)), EVID / 'inicio_A_c0-c12.jpg', cols=13)
    hoja_cuadros(mB, list(range(0, 13)), EVID / 'inicio_B_c0-c12.jpg', cols=13)
    hoja_cuadros(mA, list(range(257, 270)), EVID / 'final_c257-c269.jpg', cols=13)
    U.hoja_contacto(mA, EVID / 'hoja_A_cada_0.5s.jpg', cada=15, cols=6)
    U.hoja_contacto(mB, EVID / 'hoja_B_cada_0.5s.jpg', cada=15, cols=6)
    # empalmes medidos sobre el máster A (además de la medición sobre el video base de la etapa empalmes)
    cuadros = sorted({c for c, _ in CORTES_EMP})
    filas, vis = medir_cuadros(mA, cuadros)
    hoja_emp(vis, EVID / 'empalmes_maestro_A.jpg', 'máster A')
    rep['empalmes'] = dict(objetivo=dict(centro=OBJ[:2], ancho=OBJ[2], tolerancia=TOL), maestro_A=filas,
                           alternativa_P4=json.load(open(T / 'empalmes' / 'empalmes.json'))['alternativa_P4'])
    for f in (T / 'empalmes' / 'empalmes_alternativa_P4.jpg', T / 'empalmes' / 'empalmes.json'):
        shutil.copy2(f, EVID / f.name)
    shutil.copy2(P / 'P4_alternativa_8002_0.2-0.8.mp4', EVID / 'P4_alternativa_8002_0.2-0.8_prueba_sin_audio.mp4')
    rep['textos'] = ctrl_textos()
    rep['color'] = ctrl_color()
    rep['prendas'] = ctrl_prendas()
    au = json.load(open(A / 'audio.json'))
    ev = json.load(open(A / 'vir02n_completa_eventos.json'))
    rep['audio'] = dict(mezcla_wav=dict(completa=au['completa'], sinmusica=au['sinmusica'], lra_wav=au['lra']),
                        momentanea_por_tramo=au['momentanea_por_tramo'],
                        bajo_menos24_fuera_de_huecos=au['bajo_-24_fuera_de_huecos'], huecos=HUECOS,
                        eventos=[e for e in ev['eventos']])
    for k in ('A', 'A_sinmusica'):
        mom = U2.momentanea(MAS / NOMBRES[k])
        rep['audio'][f'momentanea_mp4_{k}'] = U2.momentanea_tramos(mom, TRAMOS_M)
        rep['audio'][f'bajo_menos24_mp4_{k}'] = bajos(mom)
    rep['ab'] = dict(
        ass_lineas_distintas=sorted(set(Path(T / 'vir02n_textos_A.ass').read_text().splitlines()) ^
                                    set(Path(T / 'vir02n_textos_B.ass').read_text().splitlines()))[:40],
        audio_A_igual_B=rep['archivos']['A']['md5_audio'] == rep['archivos']['B']['md5_audio'],
        video_sinmusica_igual_completa={h: rep['archivos'][h]['md5_video'] == rep['archivos'][f'{h}_sinmusica']['md5_video']
                                        for h in 'AB'})
    for f in (T / 'vir02n_textos_A.ass', T / 'vir02n_textos_B.ass', T / 'planos.json', T / 'med' / 'medir.json',
              T / 'med' / 'refinado.json', A / 'audio.json', A / 'vir02n_completa_eventos.json',
              A / 'vir02n_sinmusica_eventos.json', T / 'hojas' / 'niveles_fuentes_0.1s.md'):
        shutil.copy2(f, EVID / f.name)
    json.dump(rep, open(EVID / 'control.json', 'w'), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(dict(empalmes=[(f['cuadro'], f.get('centro_x'), f.get('centro_y'), f.get('ancho'), f.get('error_norm'))
                                    for f in filas], textos_ok=rep['textos']['limites_ok'],
                          cajas={k: v['dentro_y_220_480'] for k, v in rep['textos']['cajas'].items()},
                          pop={k: v['termina_en'] for k, v in rep['textos']['pop_hook'].items()},
                          tamanos=rep['textos']['tamanos'], ab=rep['ab']['audio_A_igual_B'],
                          v_sm=rep['ab']['video_sinmusica_igual_completa']), ensure_ascii=False, default=float))


def blanca_regiones(img):
    """Blanca tendida (5b): silueta de la tela clara (la mayor, debajo de y 450, con los agujeros de las letras
    rellenos) y estampado = lo que no es tela dentro de la silueta (ROCCÉ azul marino + «Founders Privée» celeste),
    sin un borde de 12 px. Devuelve (silueta, estampado) como cajas (x0, y0, x1, y1) o None."""
    from scipy import ndimage as nd
    f = img.astype(np.float64); L = f @ [0.2126, 0.7152, 0.0722]; sat = (f.max(2) - f.min(2)) / (f.max(2) + 1)
    m = (L > 140) & (sat < 0.22); m[:450] = False
    m = nd.binary_opening(m, iterations=3)
    lab, n = nd.label(m)
    if not n:
        return None, None
    tela = lab == 1 + int(np.argmax(nd.sum(m, lab, np.arange(1, n + 1))))
    llena = nd.binary_fill_holes(tela)
    dentro = nd.binary_erosion(llena, iterations=12) & ~tela
    dentro = nd.binary_opening(dentro, iterations=1)
    lab2, n2 = nd.label(nd.binary_dilation(dentro, iterations=10))
    ys, xs = np.nonzero(tela)
    sil = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    if not n2:
        return sil, None
    s2 = nd.sum(dentro, lab2, np.arange(1, n2 + 1))
    keep = 1 + np.nonzero(s2 >= 0.05 * s2.max())[0]
    py, px = np.nonzero(dentro & np.isin(lab2, keep))
    return sil, [int(px.min()), int(py.min()), int(px.max()), int(py.max())]


def etapa_blanca():
    """evidencia de «Blanca completa al final de 5b» y de por qué 5b termina en 4,167 s (máster de 9,0 s)."""
    from PIL import Image, ImageDraw, ImageFont
    EVID.mkdir(parents=True, exist_ok=True)
    fnt = ImageFont.truetype(FONT, 26)
    out = dict(maestro_A_c252_c269=[], **{'fuente_7885_4.2_a_4.8': []})
    fr = U.leer(MAS / NOMBRES['A'], W, H, n0=252, n1=269)
    vis = []
    for k, img in enumerate(fr):
        sil, est = blanca_regiones(img)
        out['maestro_A_c252_c269'].append(dict(cuadro=252 + k, silueta=sil, silueta_margen_izq=sil[0], silueta_margen_der=W - 1 - sil[2],
                                               estampado=est, estampado_margen_izq=est[0] if est else None,
                                               estampado_margen_der=(W - 1 - est[2]) if est else None))
        if k in (0, 9, 17):
            vis.append((f'máster c{252 + k}', img, sil, est))
    activar_color()
    pts = pts_toma('IMG_7885')
    fs = U.leer(V._src('IMG_7885'), W, H, n0=125, n1=144, vf_pre=V.color('IMG_7885'))
    for k, img in enumerate(fs):
        sil, est = blanca_regiones(img)
        out['fuente_7885_4.2_a_4.8'].append(dict(cuadro_fuente=125 + k, t=round(pts[125 + k], 3), silueta=sil,
                                                  silueta_margen_der=W - 1 - sil[2], estampado=est,
                                                  estampado_margen_der=(W - 1 - est[2]) if est else None))
        if 125 + k in (131, 137, 144):
            vis.append((f'7885 fuente {pts[125 + k]:.3f} s (fuera)', img, sil, est))
    tiles = []
    for rot, img, sil, est in vis:
        im = Image.fromarray(img); d = ImageDraw.Draw(im)
        d.rectangle(sil, outline=(0, 255, 0), width=5)
        if est:
            d.rectangle(est, outline=(255, 0, 255), width=5)
        d.rectangle([0, 0, 1079, 40], fill=(0, 0, 0)); d.text((8, 6), rot, font=fnt, fill=(255, 255, 0))
        tiles.append(im.resize((270, 480)))
    Wd = Image.new('RGB', (len(tiles) * 272, 480), (30, 30, 30))
    for i, t in enumerate(tiles):
        Wd.paste(t, (i * 272, 0))
    Wd.save(EVID / 'blanca_5b_silueta_verde_estampado_magenta.jpg', quality=90)
    json.dump(out, open(EVID / 'blanca_5b.json', 'w'), ensure_ascii=False, indent=1)
    for x in out['maestro_A_c252_c269'][::3] + out['fuente_7885_4.2_a_4.8'][::3]:
        print(x, flush=True)


# =====================================================================================================
# etapa 7 · entrega: EXPORTACIONES/ y carpeta de la pieza (montaje de red: verificación por md5 de flujos ~10 s después)
# =====================================================================================================
def etapa_entregar():
    import shutil
    res = {}
    for k, nombre in NOMBRES.items():
        for dst in (EXP / nombre, PIEZA / nombre):
            if dst.exists():
                raise RuntimeError(f'{dst} ya existe: no se sobrescribe')
    ev = PIEZA / EVID.name
    if ev.exists():
        raise RuntimeError(f'{ev} ya existe')
    for k, nombre in NOMBRES.items():
        shutil.copyfile(MAS / nombre, EXP / nombre)
        shutil.copyfile(MAS / nombre, PIEZA / nombre)
    shutil.copytree(EVID, ev)
    time.sleep(10)
    for k, nombre in NOMBRES.items():
        src = MAS / nombre
        ref = dict(md5_video=U.md5_stream(src, 'v'), md5_audio=U.md5_stream(src, 'a'))
        for dst in (EXP / nombre, PIEZA / nombre):
            got = dict(md5_video=U.md5_stream(dst, 'v'), md5_audio=U.md5_stream(dst, 'a'), bytes=dst.stat().st_size,
                       sha256=hashlib.sha256(dst.read_bytes()).hexdigest())
            res[str(dst)] = dict(got, flujos_iguales=(got['md5_video'] == ref['md5_video'] and got['md5_audio'] == ref['md5_audio']),
                                 sha256_igual_al_local=(got['sha256'] == hashlib.sha256(src.read_bytes()).hexdigest()))
            print(dst, res[str(dst)], flush=True)
    n_local = sum(1 for _ in EVID.rglob('*') if _.is_file()); n_red = sum(1 for _ in ev.rglob('*') if _.is_file())
    res['evidencia'] = dict(carpeta=str(ev) + '/', archivos_local=n_local, archivos_red=n_red)
    print('evidencia', n_local, n_red)
    json.dump(res, open(T / 'entrega.json', 'w'), ensure_ascii=False, indent=1)


# =====================================================================================================
if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    g = globals()
    if f'etapa_{etapa}' not in g:
        raise SystemExit(f'etapas: {[k[6:] for k in g if k.startswith("etapa_")]}')
    g[f'etapa_{etapa}']()
