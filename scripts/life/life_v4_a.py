#!/usr/bin/env python3
"""Roccé Life · V4 «¿Vuelve?» versión A (clips y voz reales de Ilia Topuria) · máster A v01 (Pedro, 25/11/2026).

Encargo: piezas/LIFE_rocce_life/TANDA2/13_roma_encargo_v4_version_A.md (decisión de Gianluca 25/11 07:38 UTC: «Clips y
voz reales de él»). Base: máster V4 v02 B aprobado (05_roma_dictamen_master_v02.md). Mismos textos, tiempos, placas,
cortes, código de color y sonido que B, salvo:
  1. imagen de los pasos 1–12 (c0–c380): clips reales de cuentas oficiales (@ufc, @ufcespanol, @iliatopuria), cada uno
     con lo que dice su texto (tabla FUENTES / PLANOS);
  2. su voz real (prioridad a del encargo): «…el carácter es la única victoria que nadie puede quitarte.», TikTok
     @iliatopuria 04/09/2026, cortada en pausas naturales (103,76–107,05 s de la fuente, sin ediciones internas) y
     separada de la música del video con demucs; reemplaza la cita escrita de los pasos 11–12, con el texto en pantalla
     igual a lo que dice, palabra por palabra al ritmo de la voz;
  3. separación: c381–c383 negro y c384–c482 idénticos a B (base, capa de texto y placa copiados de los intermedios
     de B v02).
Excluido: publicidad (1win, Stake.us, otras marcas de ropa) y cuadros con una marca de apuestas legible. En el nocaut a
Volkanovski la lona trae «DraftKings Sportsbook» a la altura de los pies en todos los ángulos encontrados: se borra
con una máscara por cuadro (ver borrar_lona); no se tocan marcas de agua ni rótulos del dueño del material.

Importa life_v4_v02 (que importa life_v4) sin modificarlos y reescribe solo el estado que cambia.
Etapas (nice -n 10, python de TRABAJO/venv), intermedios en TRABAJO/life2/v4a/ (fuera de git):
  fuentes → planos → grado → voz → textos → audio → master → control → entregar
Sin servicios externos ni créditos; nada se publica.
"""
import copy, hashlib, json, math, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/life')
import life_v4_v02 as B2     # noqa: E402  (deja el módulo de v01 con el estado de B v02)

M = B2.M
U, V, L2 = B2.U, B2.V, B2.L2
R = M.R
TB = B2.T2                                   # intermedios de B v02 (solo lectura)
TA = R / 'TRABAJO/life2/v4a'
CLIPS = TA / 'clips'
PIEZA = M.PIEZA
FPS, W, H, NF = M.FPS, M.W, M.H, M.NF        # 30, 1080, 1920, 483
FIN_A = 380                                  # último cuadro con imagen de Topuria (c381–c383 negro)
DESDE_B = 381                                # desde acá, todo de B v02
PY = str(R / 'TRABAJO/venv/bin/python')

M.T, M.P, M.A, M.MAS, M.TX, M.MED = TA, TA / 'planos', TA / 'audio', TA / 'master', TA / 'textos', TA / 'med'
M.EVID = TA / 'evidencia_A_v01'
M.NOMBRES = {'completa': 'ROCCE_LIFE_V4_VUELVE_A_v01.mp4', 'sinmusica': 'ROCCE_LIFE_V4_VUELVE_A_SINMUSICA_v01.mp4'}
NOMBRES_B = {'completa': 'ROCCE_LIFE_V4_VUELVE_v02.mp4', 'sinmusica': 'ROCCE_LIFE_V4_VUELVE_SINMUSICA_v02.mp4'}


def nice(cmd):
    return ['nice', '-n', '10'] + list(cmd)


def jdump(o, f):
    M.jdump(o, f)


# =====================================================================================================================
# fuentes (cuentas oficiales, bajadas con yt-dlp de TRABAJO/ytenv sin sesión; originales + info.json en clips/)
# =====================================================================================================================
CARTA = 'tt_iliatopuria_7681713553128082702'      # carta a su hijo, 04/09/2026 (voz y planos neutros)
MONTAJE24 = 'tt_iliatopuria_7337004126477323563'  # «Cada gota de sangre valió la pena», 18/02/2024 (Herbert, retrato)
SUENO = 'tt_iliatopuria_7341380839869074730'      # «I dreamt it. Yo lo soñé.», 01/03/2024 (nocaut a Volkanovski)
VUELTA = 'tt_iliatopuria_7703890104082812173'     # «… The Matador is coming back.», 03/11/2026
CAIDA = 'tt_ufc_7651482604582997279'              # «DOWN GOES ILIA», @ufc 15/06/2026
DETENCION = 'tt_ufcespanol_7651552980042255646'   # «Gaethje destruye a Ilia Topuria», @ufcespanol 15/06/2026

# filas con imagen real (el montaje de 2024 trae franjas negras arriba y abajo; la carta, subtítulos desde la fila 951)
UTIL = {MONTAJE24: (161, 1159), CARTA: (0, 940)}

PLANOS = [  # m0 = primer cuadro del máster; ventana = (x0, y0, ancho) en píxeles de la fuente (alto = ancho × 16/9)
    dict(id='01_caida', m0=0, nf=42, clip=CAIDA, n0=152, ventana=(0, 0, 1080),
         muestra='UFC White House, 14/06/2026: Gaethje encima de Topuria, que está en la lona; llega el árbitro'),
    dict(id='02_detencion', m0=42, nf=24, clip=DETENCION, n0=426, ventana=(0, 0, 1080), post={23: 30},
         muestra='la detención vista desde la esquina de Gaethje: el árbitro para la pelea y Gaethje se levanta con el brazo arriba'),
    dict(id='03_saco', m0=66, nf=24, clip=CARTA, n0=1405, ventana=(586, 0, 528), post={0: 45, 1: 12},
         muestra='Topuria golpea una bolsa en un gimnasio oscuro (entrenamiento; no muestra lesiones)'),
    dict(id='04_cara', m0=90, nf=33, clip=CARTA, n0=1485, ventana=(516, 0, 528),
         muestra='primer plano: levanta la cabeza y mira a cámara'),
    dict(id='05_herbert_patada', m0=123, nf=15, clip=MONTAJE24, n0=1014, ventana=(79, 41, 562),
         muestra='UFC Londres, 19/03/2022 (rótulo «JAI HERBERT · MARCH 2022» del montaje): la patada de Herbert que lo sacude'),
    dict(id='06_herbert_ko', m0=138, nf=15, clip=MONTAJE24, n0=1066, ventana=(79, 41, 562),
         muestra='la misma pelea: Topuria responde y Herbert cae (nocaut del 2.º asalto)'),
    dict(id='07_volkanovski', m0=153, nf=30, clip=SUENO, n0=1070, ventana=(0, -240, 720), borrar=True,
         muestra='UFC 298, 17/02/2024 (cámara lenta del montaje): la derecha de Topuria y Volkanovski que cae'),
    dict(id='08_sentado', m0=183, nf=24, clip=CARTA, n0=2340, ventana=(512, 0, 528),
         muestra='sentado solo en un banco, fondo oscuro'),
    dict(id='09_escalera', m0=207, nf=21, clip=VUELTA, n0=170, ventana=(0, 0, 720),
         muestra='del posteo en que escribe «The Matador is coming back»: sube corriendo la escalera de un monumento'),
    dict(id='10_solo', m0=228, nf=21, clip=CARTA, n0=1451, ventana=(536, 0, 528),
         muestra='de pie, solo, frente a un fondo de estudio en un gimnasio oscuro'),
    dict(id='11_retrato', m0=249, nf=132, clip=MONTAJE24, n0=50, velocidad='natural', ventana=(0, -260, 720),
         muestra='primer plano quieto, boca cerrada (no habla: no simula sincronía con la voz de otro video)'),
]
CORTES_A = [p['m0'] for p in PLANOS[1:]] + [DESDE_B, 384, 423]


def fps_de(clip):
    s = U.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate,width,height',
               '-of', 'json', str(CLIPS / f'{clip}.mp4')])
    st = json.loads(s)['streams'][0]
    a, b = st['r_frame_rate'].split('/')
    return float(a) / float(b), st['width'], st['height']


def indices(p):
    """cuadros de la fuente para cada cuadro del plano: uno a uno (24/25 fps quedan 1,25/1,2 veces más rápidos, sin
    repetir cuadros) o, en el retrato quieto, a velocidad natural (un cuadro repetido cada 5 o 6)."""
    if p.get('velocidad') == 'natural':
        f, _, _ = fps_de(p['clip'])
        return [p['n0'] + int(math.floor(k * f / FPS + 1e-9)) for k in range(p['nf'])]
    return [p['n0'] + k for k in range(p['nf'])]


def info_clip(clip):
    d = json.load(open(CLIPS / f'{clip}.info.json'))
    ts = d.get('timestamp')
    return dict(cuenta='@' + (d.get('uploader') or '?'), id=d.get('id'), url=d.get('webpage_url'),
                fecha_publicacion=time.strftime('%d/%m/%Y %H:%M UTC', time.gmtime(ts)) if ts else d.get('upload_date'),
                descripcion=(d.get('description') or d.get('title') or '')[:300], duracion=d.get('duration'))


def etapa_fuentes():
    """tabla de clips usados (cuenta, URL, fecha, id, tramo, qué muestra) desde los info.json."""
    filas = []
    for p in PLANOS:
        f, w, h = fps_de(p['clip'])
        ix = indices(p)
        r = info_clip(p['clip'])
        r.update(plano=p['id'], cuadros_master=[p['m0'], p['m0'] + p['nf'] - 1], fps_fuente=round(f, 3), resolucion=[w, h],
                 cuadros_fuente=[ix[0], ix[-1]], tramo_s=[round(ix[0] / f, 3), round((ix[-1] + 1) / f, 3)],
                 ventana=p['ventana'], muestra=p['muestra'], borrado_lona=bool(p.get('borrar')))
        filas.append(r)
    voz = info_clip(CARTA)
    voz.update(uso='voz (pasos 11–12)', tramo_s=[VOZ['src0'], VOZ['src1']])
    jdump(dict(planos=filas, voz=voz), TA / 'fuentes.json')
    for r in filas:
        print(r['plano'], r['cuenta'], r['id'], r['fecha_publicacion'], r['tramo_s'])


# =====================================================================================================================
# borrado de la marca de apuestas de la lona (UFC 298: «DraftKings Sportsbook» al lado de los pies)
# =====================================================================================================================
# banda inclinada que contiene el logo, por cuadro clave de la fuente: (cuadro, x0, x1, techo en x0, pendiente, alto)
LONA_CLAVES = [(1070, 420, 720, 850, 0.075, 78), (1076, 375, 720, 850, 0.075, 80), (1082, 345, 720, 852, 0.08, 80),
               (1088, 285, 650, 858, 0.085, 80), (1094, 250, 630, 858, 0.085, 84), (1099, 215, 610, 858, 0.085, 86)]
LONA_Z = (820, 980)


def banda_lona(n):
    ks = [c[0] for c in LONA_CLAVES]
    if n <= ks[0]:
        return LONA_CLAVES[0][1:]
    if n >= ks[-1]:
        return LONA_CLAVES[-1][1:]
    i = int(np.searchsorted(ks, n)) - 1
    t = (n - ks[i]) / (ks[i + 1] - ks[i])
    return tuple((1 - t) * a + t * b for a, b in zip(LONA_CLAVES[i][1:], LONA_CLAVES[i + 1][1:]))


def borrar_lona(f, n):
    """dentro de la banda del logo, los trazos oscuros finos que no son piel (cierre morfológico 15 px − luma) se
    reemplazan por la lona vecina (convolución normalizada con los píxeles de lona limpia). La piel (tono cálido: R − B
    > −4 o R > G + 3, abierta 3×3) y los 3 px debajo de cada pie (sombra de contacto) quedan intactos. La zona tocada
    (máscara dilatada 5 px) se suaviza con σ 2,2 para que el borde de los pies, ya movido en la cámara lenta, no quede
    dentado. Devuelve la imagen y la máscara (0–1)."""
    from scipy import ndimage as nd
    Z0, Z1 = LONA_Z
    x0, x1, y0, s, h = banda_lona(n)
    Rr, Gg, Bb = [f[Z0:Z1, :, c] for c in range(3)]
    Y = 0.2126 * Rr + 0.7152 * Gg + 0.0722 * Bb
    cal = ((Rr - Bb) > -4) | (Rr > Gg + 3)
    cal = nd.binary_opening(cal, structure=np.ones((3, 3)))
    Cl = nd.grey_closing(Y, size=(15, 15))
    d = (Cl - Y) / np.maximum(Cl, 20)
    xx = np.arange(f.shape[1])[None, :]
    yy = np.arange(Z1 - Z0)[:, None] + Z0
    techo = y0 + s * (xx - x0)
    dentro = (xx >= x0) & (xx <= x1) & (yy >= techo) & (yy <= techo + h)
    dentro_s = nd.gaussian_filter(dentro.astype(np.float32), 3)
    debajo_pie = nd.binary_dilation(cal, structure=np.ones((7, 3)), origin=(-3, 0))
    a = np.clip((d - 0.045) / 0.08, 0, 1) * dentro_s * (~cal) * (~debajo_pie)
    a = nd.maximum_filter(a, size=5)
    a = np.clip(nd.gaussian_filter(a, 1.0) * 1.6, 0, 1)
    a[cal] = 0
    valido = ((a < 0.02) & (~cal) & (d < 0.04)).astype(np.float32)
    out = f[Z0:Z1].copy()
    for ch in range(3):
        X = f[Z0:Z1, :, ch]
        rel = None
        for sg in (3, 8, 20):
            num = nd.gaussian_filter(X * valido, sg); den = nd.gaussian_filter(valido, sg)
            r = np.where(den > 0.04, num / np.maximum(den, 1e-6), np.nan)
            rel = r if rel is None else np.where(np.isnan(rel), r, rel)
        rel = np.where(np.isnan(rel), X, rel)
        out[..., ch] = a * rel + (1 - a) * X
    zona = nd.gaussian_filter(nd.binary_dilation(a > 0.05, iterations=5).astype(np.float32), 2.0)
    for ch in range(3):
        out[..., ch] = zona * nd.gaussian_filter(out[..., ch], 2.2) + (1 - zona) * out[..., ch]
    g = f.copy()
    g[Z0:Z1] = out
    mask = np.zeros(f.shape[:2], np.float32)
    mask[Z0:Z1] = a
    return g, mask


# =====================================================================================================================
# planos · luma (el máster es B/N hasta c380) compuesta a 1080×1920 sin pérdida
# =====================================================================================================================
def decodificar(clip, ix):
    """cuadros RGB float32 (matriz BT.709, rango tv → 0–255) para los índices pedidos (pueden repetirse)."""
    f, w, h = fps_de(clip)
    a, b = min(ix), max(ix)
    raw = U.run(nice(['ffmpeg', '-v', 'error', '-i', str(CLIPS / f'{clip}.mp4'), '-an', '-vf',
                      f"select='between(n\\,{a}\\,{b})',scale=in_color_matrix=bt709:in_range=tv,format=rgb24",
                      '-fps_mode', 'passthrough', '-f', 'rawvideo', '-']))
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    assert len(fr) == b - a + 1, (clip, len(fr), a, b)
    return {n: fr[n - a] for n in sorted(set(ix))}, (w, h)


def relleno(prof, filas, borde):
    """filas de relleno: el perfil de las filas del borde de la toma (zona sin persona), desenfocado en horizontal."""
    from scipy import ndimage as nd
    p = nd.gaussian_filter1d(prof, 30, mode='nearest')
    return np.repeat(p[None, :], filas, 0)


def componer(rgb, p, wh):
    """luma de salida (código 8 bits, rango tv, float) de un cuadro de la fuente según la ventana del plano; donde la
    ventana sale de la imagen útil, relleno con el borde de la toma (sin persona) y transición de 48 filas."""
    from PIL import Image
    from scipy import ndimage as nd
    w_s, h_s = wh
    Yf = rgb.astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32)       # 0–255
    x0, y0, w = p['ventana']
    hv = w * 16 / 9
    s = W / w
    u0, u1 = UTIL.get(p['clip'], (0, h_s))
    Ya = max(0, int(math.ceil((u0 - y0) * s - 1e-6)))
    Yb = min(H, int(math.floor((u1 - y0) * s + 1e-6)))
    assert 0 <= x0 and x0 + w <= w_s + 1e-6, p['id']
    img = Image.fromarray(Yf, 'F')
    part = np.asarray(img.resize((W, Yb - Ya), Image.LANCZOS, box=(x0, y0 + Ya / s, x0 + w, y0 + Yb / s)), np.float32)
    out = np.empty((H, W), np.float32)
    out[Ya:Yb] = part
    T_ = 48
    if Ya > 0:
        prof = np.median(part[:16], 0)
        out[:Ya] = relleno(prof, Ya, 'arriba')
        r = np.linspace(0, 1, T_)[:, None]
        out[Ya:Ya + T_] = (1 - r) * relleno(prof, T_, 'arriba') + r * part[:T_]
    if Yb < H:
        prof = np.median(part[-16:], 0)
        out[Yb:] = relleno(prof, H - Yb, 'abajo')
        r = np.linspace(1, 0, T_)[:, None]
        out[Yb - T_:Yb] = (1 - r) * relleno(prof, T_, 'abajo') + r * part[-T_:]
    return 16 + 219 * np.clip(out, 0, 255) / 255


def cortes_internos(clip, ix):
    """diferencia media de luma entre cuadros consecutivos de la fuente dentro del tramo (un corte del montaje
    original dentro de un plano daría un salto > 12)."""
    fr, wh = decodificar(clip, list(range(min(ix), max(ix) + 1)))
    ks = sorted(fr)
    g = [np.asarray(fr[k], np.float32)[::8, ::8].mean(2) for k in ks]
    d = [float(np.abs(g[i + 1] - g[i]).mean()) for i in range(len(g) - 1)]
    return dict(dif_max=round(max(d), 2), saltos_mayores_12=[ks[i + 1] for i, v in enumerate(d) if v > 12])


def etapa_planos():
    M.P.mkdir(parents=True, exist_ok=True)
    from scipy import ndimage as nd
    dst = TA / 'v4a_base0.mp4'
    cs = (W // 2) * (H // 2)
    enc = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{W}x{H}',
                                 '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-qp', '0', '-preset', 'veryfast', '-threads', '2',
                                 '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                                 '-color_range', 'tv', str(dst)]), stdin=subprocess.PIPE)
    reg, n_tot = [], 0
    mascaras = {}
    for p in PLANOS:
        assert p['m0'] == n_tot, (p['id'], p['m0'], n_tot)
        ix = indices(p)
        fr, wh = decodificar(p['clip'], ix)
        stats = []
        for k, n in enumerate(ix):
            rgb = fr[n].astype(np.float32)
            if p.get('borrar'):
                rgb, mk = borrar_lona(rgb, n)
                mascaras[p['m0'] + k] = dict(fuente=n, px_borrados=int((mk > 0.5).sum()))
            Y = componer(rgb, p, wh)
            r = p.get('post', {}).get(k)
            if r:
                Y = nd.uniform_filter1d(Y, 2 * r + 1, axis=1, mode='nearest')     # = avgblur sizeX=r de B (salto lateral)
            Y8 = np.clip(np.round(Y), 0, 255).astype(np.uint8)
            enc.stdin.write(Y8.tobytes()); enc.stdin.write(bytes([128]) * (2 * cs))
            stats.append(dict(media=float(Y8.mean()), p99=float(np.percentile(Y8[::4, ::4], 99.5))))
        ci = cortes_internos(p['clip'], ix)
        reg.append(dict(id=p['id'], m0=p['m0'], cuadros=p['nf'], clip=p['clip'], fuente=[ix[0], ix[-1]], indices=ix,
                        ventana=p['ventana'], post=p.get('post'), velocidad=p.get('velocidad', 'uno a uno'),
                        luma_media=round(float(np.mean([s['media'] for s in stats])), 1),
                        luma_p995=round(float(np.mean([s['p99'] for s in stats])), 1), cortes_en_la_fuente=ci))
        n_tot += p['nf']
        print(p['id'], p['nf'], reg[-1]['luma_media'], reg[-1]['luma_p995'], ci, flush=True)
    enc.stdin.close(); enc.wait()
    assert enc.returncode == 0 and n_tot == FIN_A + 1, n_tot
    jdump(dict(cuadros=n_tot, planos=reg, borrado_lona=mascaras), TA / 'planos.json')
    print('base0', n_tot)


# =====================================================================================================================
# grado · B/N con el mismo código de B (E− ×0,5 / E+ ×√2 de exposición, oscuro ×0,35 con rampa) sobre una ganancia
# base por plano que iguala la exposición de tomas muy distintas (la carta es casi negra; el ring, claro)
# =====================================================================================================================
G_BASE = {'01_caida': 1.0, '02_detencion': 1.0, '03_saco': 4.5, '04_cara': 3.0, '05_herbert_patada': 1.0,
          '06_herbert_ko': 1.0, '07_volkanovski': 1.0, '08_sentado': 3.0, '09_escalera': 1.0, '10_solo': 3.2,
          '11_retrato': 1.0}


def plano_de(n):
    for p in PLANOS:
        if p['m0'] <= n < p['m0'] + p['nf']:
            return p
    return None


def lut_a(g, modo, k):
    v = np.clip((np.arange(256) - 16) / 219, 0, 1)
    L = v ** 2.4 * g * (k if modo == 'bn' else 1.0)
    kn = 0.8
    L = np.where(L > kn, kn + (1 - kn) * np.tanh((L - kn) / (1 - kn)), L)
    v2 = L ** (1 / 2.4)
    if modo == 'oscuro':
        v2 = v2 * k
    return np.clip(np.round(16 + 219 * v2), 16, 235).astype(np.uint8)


def frames_yuv(mp4):
    ys, cs = W * H, (W // 2) * (H // 2)
    p = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(mp4), '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-']),
                         stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(ys + 2 * cs)
        if len(b) < ys + 2 * cs:
            break
        yield b
    p.stdout.close(); p.wait()


def etapa_grado():
    M.MED.mkdir(parents=True, exist_ok=True)
    ys, cs = W * H, (W // 2) * (H // 2)
    dst = TA / 'v4_base.mp4'
    enc = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{W}x{H}', '-r', str(FPS),
                                 '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                                 '-i', '-', '-c:v', 'libx264', '-qp', '0', '-preset', 'veryfast', '-threads', '2', '-pix_fmt', 'yuv420p',
                                 '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
                                 str(dst)]), stdin=subprocess.PIPE)
    filas, luts, n = [], {}, 0
    for b in frames_yuv(TA / 'v4a_base0.mp4'):
        Y = np.frombuffer(b[:ys], np.uint8).reshape(H, W)
        modo, k = M.grado_de(n)
        p = plano_de(n)
        g = G_BASE[p['id']]
        key = (g, modo, k)
        if key not in luts:
            luts[key] = lut_a(g, modo, k)
        Y2 = luts[key][Y]
        enc.stdin.write(Y2.tobytes()); enc.stdin.write(bytes([128]) * (2 * cs))
        filas.append(dict(cuadro=n, plano=p['id'], g_base=g, modo=modo, k=round(k, 4), luma_antes=round(float(Y.mean()), 2),
                          luma_despues=round(float(Y2.mean()), 2)))
        n += 1
    assert n == FIN_A + 1, n
    # c381–c482: los cuadros de la base graduada de B v02, tal cual (decodificados de un archivo sin pérdida)
    md5_b = []
    for i, b in enumerate(frames_yuv(TB / 'v4_base.mp4')):
        if i >= DESDE_B:
            enc.stdin.write(b); md5_b.append(hashlib.md5(b).hexdigest()); n += 1
    enc.stdin.close(); enc.wait()
    assert enc.returncode == 0 and n == NF, n
    jdump(dict(metodo=('c0–c380: luma de la composición × ganancia base por plano (exposición en luz lineal, gamma 2,4) '
                       '× E de B (E− ×0,5, E+ ×√2, hombro tanh desde 0,8); pasos 11–12: ×0,75/0,62/0,48 y ×0,35 sobre el '
                       'código como en B; croma 128. c381–c482: cuadros de TRABAJO/life2/v4/v02/v4_base.mp4 sin tocar.'),
               g_base=G_BASE, por_cuadro=filas, md5_cuadros_b_381_482=md5_b), M.MED / 'grado.json')
    print('grado ok', n)


# =====================================================================================================================
# voz real (prioridad a): «…el carácter es la única victoria que nadie puede quitarte.»
# =====================================================================================================================
VOZ = dict(clip=CARTA, src0=103.76, src1=107.05, sep=TA / 'voz/sep/htdemucs/carta_96-fin/vocals.wav', sep_desde=96.0,
           texto='“…el carácter es la única victoria que nadie puede quitarte.”')
V0 = 8.60                       # entra 0,30 s después del corte de la música (8,30); termina 11,79, antes del sub-golpe (11,80)
# comienzo de cada palabra en la fuente (s), de la envolvente de la voz separada y la transcripción (ver la hoja 06)
PALABRAS_VOZ = [('“…el', 103.80), ('carácter', 104.00), ('es', 104.30), ('la', 104.50), ('única', 104.60),
                ('victoria', 104.94), ('que', 105.82), ('nadie', 105.92), ('puede', 106.16), ('quitarte.”', 106.40)]
RENGLONES_VOZ = [5, 3, 2]       # «“…el carácter es la única» / «victoria que nadie» / «puede quitarte.”»


def cuadro_de_fuente(t):
    return int(math.floor((t - VOZ['src0'] + V0) * FPS + 1e-9))


def etapa_voz():
    d = TA / 'voz'
    out = d / 'voz_topuria_48k.wav'
    dur = VOZ['src1'] - VOZ['src0']
    V.sh(['ffmpeg', '-v', 'error', '-y', '-ss', f"{VOZ['src0'] - VOZ['sep_desde']:.3f}", '-t', f'{dur:.3f}', '-i', str(VOZ['sep']),
          '-af', f"pan=mono|c0=0.5*c0+0.5*c1,aresample=48000,afade=t=in:d=0.010,afade=t=out:st={dur - 0.030:.3f}:d=0.030",
          '-c:a', 'pcm_f32le', str(out)])
    # el mismo tramo sin separar (para comparar la transcripción) y de la fuente original, sin pasar por el WAV de demucs
    V.sh(['ffmpeg', '-v', 'error', '-y', '-ss', f"{VOZ['src0']:.3f}", '-t', f'{dur:.3f}', '-i', str(CLIPS / f'{CARTA}.mp4'),
          '-vn', '-af', 'pan=mono|c0=0.5*c0+0.5*c1,aresample=48000', '-c:a', 'pcm_f32le', str(d / 'tramo_original_48k.wav')])
    import soundfile as sf
    x, sr = sf.read(str(out))
    jdump(dict(fuente=info_clip(CARTA), tramo_fuente_s=[VOZ['src0'], VOZ['src1']], entra_en_master_s=V0,
               termina_en_master_s=round(V0 + len(x) / sr, 3), muestras=len(x), sr=sr,
               metodo=('demucs 4.1 htdemucs --two-stems=vocals sobre 96,0 s–fin de la fuente (44,1 kHz); tramo cortado en '
                       'silencios (antes: pausa de ≈1,8 s después de «recuerda siempre esto,», corte a −73 dB, 40 ms antes de «el»; '
                       'después: la cola de «quitarte» ya en el piso de ruido, −59 dB a 107,05 s; con 106,95 s la sílaba «te» '
                       'quedaba cortada y la transcripción decía «quitar»); mono, 48 kHz, fundidos de 10 ms y 30 ms; sin cortes internos, sin cambio de tono ni de tiempo'),
               palabras=[dict(palabra=w, fuente_s=t, master_s=round(t - VOZ['src0'] + V0, 3), cuadro=cuadro_de_fuente(t))
                         for w, t in PALABRAS_VOZ]), d / 'voz.json')
    print('voz', out, len(x) / sr)


# =====================================================================================================================
# textos · los de B v02 hasta c248; en los pasos 11–12 la frase de su voz en lugar de las citas del ensayo
# =====================================================================================================================
LH_CITA = M.LH_CITA
Y_VOZ = 300


def frases_a():
    fr = [f for f in copy.deepcopy(M.FRASES) if f['id'] not in ('c1', 'c2', 'c3', 'atrib')]
    ws, k, lineas = [w for w, _ in PALABRAS_VOZ], 0, []
    for nw in RENGLONES_VOZ:
        lineas.append(ws[k:k + nw]); k += nw
    ap = [cuadro_de_fuente(t) for _, t in PALABRAS_VOZ]
    assert ap == sorted(ap) and ap[0] >= 249 and ap[-1] <= FIN_A
    voz = dict(id='voz', tipo='cita', fs=M.FS_CITA, n=(ap[0], FIN_A), y=Y_VOZ, lineas=lineas, aparece=ap, cad=0,
               golpe='sub', golpe_n=354, guion=VOZ['texto'])
    atr = dict(id='atrib_voz', tipo='atrib', fs=36, n=(ap[0], FIN_A), y=Y_VOZ + len(lineas) * LH_CITA + 26,
               lineas=[['—', 'Ilia', 'Topuria', '·', 'TikTok', '@iliatopuria', '·', '04/09/2026']], cad=0,
               guion='— Ilia Topuria · TikTok @iliatopuria · 04/09/2026')
    i = [j for j, f in enumerate(fr) if f['id'] == 'reeng'][0]
    return fr[:i] + [voz, atr] + fr[i:]


_palabras_b = M.palabras


def palabras_a(f):
    if 'aparece' not in f:
        return _palabras_b(f)
    out, k = [], 0
    for i, ln in enumerate(f['lineas']):
        for j, w in enumerate(ln):
            out.append((w, f['aparece'][k], i, j)); k += 1
    return out


def golpe_de_a(f):
    if not f.get('golpe'):
        return None
    return f.get('golpe_n', palabras_a(f)[-1][1])


# toques por palabra que ponía B v02 (c2/c3): se calculan con las frases de B antes de reemplazarlas
_FR_B = copy.deepcopy(M.FRASES)
_golpe_de_b = M.golpe_de
N_TOQUES_B = sum(len(_palabras_b(f)) - (1 if f.get('golpe') else 0) for f in _FR_B if f.get('toques'))
M.FRASES = frases_a()
M.palabras, M.golpe_de = palabras_a, golpe_de_a


def etapa_textos():
    """capa de texto c0–c380 con la receta de B (mismo HTML/CSS/JS y renderizador) y c381–c422 copiada de B v02."""
    M.TX.mkdir(parents=True, exist_ok=True)
    sp = M.spec_texto()
    css = M.CSS_TEXTO % dict(F=L2.FUENTES, CEL=M.CELESTE, LHC=LH_CITA)
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body><div id="raiz"></div>'
            f'<script>{M.JS_TEXTO.replace("__SPEC__", json.dumps(sp, ensure_ascii=False))}</script></body></html>')
    (M.TX / 'texto_v4a.html').write_text(html, encoding='utf-8')
    jdump(sp, M.TX / 'spec_texto.json')
    sec = M.TX / 'cuadros'
    if sec.exists():
        shutil.rmtree(sec)                              # intermedio propio de A (TRABAJO/life2/v4a/textos)
    trabajo = dict(html=str(M.TX / 'texto_v4a.html'), outdir=str(sec), n0=0, n1=FIN_A, w=W, h=H, dump=str(M.TX / 'visible.json'))
    (M.TX / '_trabajo.json').write_text(json.dumps(trabajo, indent=1))
    subprocess.run(nice(['node', str(R / 'scripts/life/life_v4_render.js'), str(M.TX / '_trabajo.json')]), check=True)
    for n in range(DESDE_B, M.TEXTO_ULTIMO + 1):
        shutil.copyfile(TB / 'textos' / 'cuadros' / f'f_{n:04d}.png', sec / f'f_{n:04d}.png')
    k = len(list(sec.glob('f_*.png')))
    assert k == M.TEXTO_ULTIMO + 1, k
    print('textos', k)


# =====================================================================================================================
# audio · sonido de B v02 (mar, golpes, campana, música TEMP) + su voz con el fondo que cede; mismo generador aleatorio
# =====================================================================================================================
DUCK_DB = {'completa': 20.0, 'sinmusica': 22.0}     # cuánto cede el fondo (mar, colchón) bajo la voz
VOZ_DB = {'completa': 3.0, 'sinmusica': 0.8}       # la sin música sale con +3,2 dB de ganancia y el mar 3,2 dB más alto: la voz 1 dB más
GAN_B = {}                                          # ganancia de exportación de B v02 (se lee de sus _eventos.json)


def sfx_b_a(m):
    """B v02 ponía aquí un toque por palabra de las citas (16, con ruido del generador común) y el sub-golpe en
    «intentarlo» (c354). En A no hay toques (el ritmo lo marca su voz), pero se consume la misma cantidad de ruido para
    que todo lo que sigue salga idéntico a B; el sub-golpe queda en c354 (11,80 s), apenas termina la voz."""
    S_ = M._s()
    for _ in range(N_TOQUES_B):
        S_.ruido(int(0.05 * S_.SR))
    golpes, toques = M.eventos_texto()
    assert not toques
    for n, tipo, _id in golpes:
        if tipo == 'sub':
            M.sub_golpe(m, M.tf(n))


_sfx_b_original = M.sfx_b
M.sfx_b = sfx_b_a


def envolvente(x, sr, ataque=0.015, suelta=0.25, umbral_db=-45.0):
    """0–1: 1 donde la voz suena (ventanas de 10 ms sobre umbral relativo al máximo), con ataque y suelta exponenciales."""
    w = int(0.010 * sr)
    nb = int(math.ceil(len(x) / w))
    xx = np.zeros(nb * w); xx[:len(x)] = x
    rms = np.sqrt((xx.reshape(nb, w) ** 2).mean(1)) + 1e-12
    db_ = 20 * np.log10(rms / rms.max())
    act = np.clip((db_ - umbral_db) / 10, 0, 1)
    e = np.zeros(nb); acc = 0.0
    ka, ks = math.exp(-0.010 / ataque), math.exp(-0.010 / suelta)
    for i in range(nb):
        acc = act[i] + (acc - act[i]) * (ka if act[i] > acc else ks)
        e[i] = acc
    return np.repeat(e, w)[:len(x)]


def mezcla_a(con_musica, k):
    import soundfile as sf
    m = B2.mezcla(con_musica)                       # = B v02 con sfx_b_a (mismas llamadas al generador)
    x, sr = sf.read(str(TA / 'voz' / 'voz_topuria_48k.wav'))
    assert sr == M.SR
    g = 10 ** (VOZ_DB[k] / 20)
    i0 = int(round(V0 * sr))
    voz = np.zeros(m.N); voz[i0:i0 + len(x)] = x * g
    m.pistas['voz'][:, 0] += voz * math.sqrt(0.5); m.pistas['voz'][:, 1] += voz * math.sqrt(0.5)
    e = np.zeros(m.N); e[i0:i0 + len(x)] = envolvente(x, sr)
    # suelta después del final de la voz (sin cortar en seco) y 1,0 exacto desde 12,40 s
    j = i0 + len(x); cola = int(0.25 * sr)
    e[j:j + cola] = e[j - 1] * np.exp(-np.arange(cola) / (0.08 * sr))
    assert e[int(12.4 * sr):].max() == 0
    duck = 10 ** (-DUCK_DB[k] * e / 20)
    for p in ('amb', 'mus', 'bombo'):
        m.pistas[p] *= duck[:, None]
    m.log(V0, f'voz de Topuria (carta 04/09/2026, {VOZ["src0"]}–{VOZ["src1"]} s), {VOZ_DB[k]:+.1f} dB; fondo cede {DUCK_DB[k]} dB')
    return m, voz, e


def pre_mezcla(m, salida):
    """la mezcla antes del limitador, exactamente como sonido.Mezcla.exportar (bombeo de la música con el bombo)."""
    import soundfile as sf
    S_ = M._s()
    P = {k: v * S_.db(0) for k, v in m.pistas.items()}
    bk = np.abs(P['bombo']).mean(1)
    a = np.exp(-1 / (0.12 * S_.SR))
    e = np.zeros(m.N); acc = 0.0
    pk = np.convolve(bk, np.ones(64) / 64, 'same')
    for i in range(0, m.N, 64):
        v = pk[i:i + 64].max() if i < m.N else 0
        acc = max(v, acc * a ** 64); e[i:i + 64] = acc
    e = e / (e.max() + 1e-9)
    duck = 1 - (1 - S_.db(-6.0)) * e
    mix = P['amb'] + P['fx'] + P['mus'] * duck[:, None] + P['bombo'] + P['voz']
    sf.write(str(salida), mix.astype(np.float32), S_.SR, subtype='FLOAT')
    for k, v in P.items():
        if np.abs(v).max() > 0:
            sf.write(str(salida).replace('_pre.wav', f'_{k}.wav'), v.astype(np.float32), S_.SR, subtype='FLOAT')
    return mix


def limitar(pre, salida, gan):
    V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af',
          f'volume={gan:.2f}dB,alimiter=limit=0.83:level=false:attack=3:release=60:latency=1', '-c:a', 'pcm_f32le', str(salida)])
    return L2.medir_ebur(salida)


def voz_vs_fondo(m, voz, e, gan):
    """nivel de la voz contra todo lo demás durante las frases (ventanas de 50 ms con la voz activa), antes del limitador;
    las dos señales como promedio de los canales (la voz va centrada, ×√0,5 por canal)."""
    import soundfile as sf
    sr = M.SR
    fondo = (m.pistas['amb'] + m.pistas['fx'] + m.pistas['mus'] + m.pistas['bombo']).mean(1)
    w = int(0.05 * sr); filas = []
    for i in range(int(V0 * sr), int((V0 + 3.2) * sr) - w, w):
        if e[i:i + w].min() > 0.9:
            v = 20 * math.log10(np.sqrt(((voz[i:i + w] * math.sqrt(0.5)) ** 2).mean()) + 1e-12)
            f = 20 * math.log10(np.sqrt((fondo[i:i + w] ** 2).mean()) + 1e-12)
            filas.append(dict(t=round(i / sr, 2), voz_db=round(v, 1), fondo_db=round(f, 1), dif_db=round(v - f, 1)))
    difs = [f_['dif_db'] for f_ in filas]
    return dict(ventanas=len(filas), dif_mediana_db=round(float(np.median(difs)), 1), dif_min_db=round(min(difs), 1),
                dif_max_db=round(max(difs), 1), por_ventana=filas)


def etapa_audio():
    """mezcla completa y sin música en el MISMO orden que B v02 (completa primero), con la ganancia de exportación de
    B (para que desde c384 la mezcla final salga igual); se controla −14 ±1 LUFS y pico real ≤ −1 dBTP."""
    M.A.mkdir(parents=True, exist_ok=True)
    out = {}
    for k, con in (('completa', True), ('sinmusica', False)):
        GAN_B[k] = json.load(open(TB / 'audio' / f'v4_{k}_eventos.json'))['ganancia_db']
        m, voz, e = mezcla_a(con, k)
        pre = M.A / f'v4_{k}_pre.wav'
        pre_mezcla(m, pre)
        gan = GAN_B[k]
        I, Pk, LRA = limitar(pre, M.A / f'v4_{k}.wav', gan)
        nota = 'ganancia de B'
        if not (-15.0 <= I <= -13.0 and Pk <= -1.0):
            for _ in range(3):
                gan = gan + (-14.0 - I) - (max(0.0, Pk + 1.2))
                I, Pk, LRA = limitar(pre, M.A / f'v4_{k}.wav', gan)
                if -15.0 <= I <= -13.0 and Pk <= -1.0:
                    break
            nota = 'ganancia corregida (fuera de tolerancia con la de B)'
        json.dump({'lufs': I, 'pico_dbtp': Pk, 'ganancia_db': round(gan, 2), 'eventos': m.ev},
                  open(M.A / f'v4_{k}_eventos.json', 'w'), ensure_ascii=False, indent=1)
        out[k] = dict(lufs=I, pico_dbtp=Pk, lra=LRA, ganancia_db=round(gan, 2), ganancia_b_db=GAN_B[k], nota=nota,
                      voz_db=VOZ_DB[k], fondo_cede_db=DUCK_DB[k], voz_vs_fondo=voz_vs_fondo(m, voz, e, gan))
        print(k, {kk: vv for kk, vv in out[k].items() if kk != 'voz_vs_fondo'},
              {kk: vv for kk, vv in out[k]['voz_vs_fondo'].items() if kk != 'por_ventana'}, flush=True)
    golpes, toques = M.eventos_texto()
    out['golpes_texto'] = [dict(cuadro=n, t=round(M.tf(n), 3), tipo=t_, frase=i) for n, t_, i in golpes]
    out['toques_b_reemplazados_por_ruido_descartado'] = N_TOQUES_B
    jdump(out, M.A / 'audio.json')


def etapa_regen_b():
    """control de determinismo (en un proceso propio, generador desde cero): rehace la mezcla previa de B v02 con su
    receta y la compara con la guardada. Si es igual bit a bit, la comparación A/B desde c384 es válida."""
    import soundfile as sf
    M.sfx_b = _sfx_b_original
    M.FRASES, M.palabras, M.golpe_de = _FR_B, _palabras_b, _golpe_de_b
    out = {}
    d = TA / 'med' / 'regen_b'; d.mkdir(parents=True, exist_ok=True)
    for k, con in (('completa', True), ('sinmusica', False)):
        m = B2.mezcla(con)
        x = pre_mezcla(m, d / f'v4_{k}_pre.wav').astype(np.float32)
        y, _ = sf.read(str(TB / 'audio' / f'v4_{k}_pre.wav'), dtype='float32')
        out[k] = dict(muestras=len(y), identico_bit_a_bit=bool(np.array_equal(x, y)), dif_max=float(np.abs(x - y).max()))
        print(k, out[k], flush=True)
    jdump(out, TA / 'med' / 'regen_b.json')


# =====================================================================================================================
# master · base + capa de texto + placa de B + mezcla (receta de B: master_v4); la sin música copia el flujo de video
# =====================================================================================================================
def etapa_master():
    M.etapa_master()


# =====================================================================================================================
# control
# =====================================================================================================================
def tramos_a():
    return B2.tramos2() + [('voz de Topuria', V0, V0 + (VOZ['src1'] - VOZ['src0']))]


def md5_cuadros(mp4, n0=0, n1=None):
    out = []
    for i, b in enumerate(frames_yuv(mp4)):
        if i >= n0 and (n1 is None or i <= n1):
            out.append(hashlib.md5(b).hexdigest())
    return out


def separacion():
    """(1) mapa de fuentes: c0–c380 solo clips de Topuria/UFC; (2) c381–c482 de la base idénticos a B; (3) capa de texto
    c381–c422 idéntica a B; (4) placa: mismos archivos; (5) NCC de la ficha del logo en el máster A, cuadro a cuadro."""
    import life_v4_control as C
    from PIL import Image
    r = {}
    pj = json.load(open(TA / 'planos.json'))
    r['mapa_c0_c380'] = [dict(plano=p['id'], cuadros=[p['m0'], p['m0'] + p['cuadros'] - 1], clip=p['clip'], fuente=p['fuente'])
                         for p in pj['planos']]
    a = md5_cuadros(TA / 'v4_base.mp4', DESDE_B); b = md5_cuadros(TB / 'v4_base.mp4', DESDE_B)
    r['base_c381_c482_identica_a_B'] = dict(cuadros=len(a), identicos=sum(x == y for x, y in zip(a, b)))
    neg = md5_cuadros(TA / 'v4_base.mp4', 381, 383)
    r['negro_c381_c383_md5'] = neg
    t_id = [n for n in range(DESDE_B, M.TEXTO_ULTIMO + 1)
            if hashlib.md5((M.TX / 'cuadros' / f'f_{n:04d}.png').read_bytes()).hexdigest()
            == hashlib.md5((TB / 'textos' / 'cuadros' / f'f_{n:04d}.png').read_bytes()).hexdigest()]
    r['texto_c381_c422_identico_a_B'] = dict(cuadros=M.TEXTO_ULTIMO + 1 - DESDE_B, identicos=len(t_id))
    r['placa'] = dict(archivos=[str(M.PL / 'cierre_frase.png'), str(M.PL / 'cierre_firma.png')], cuadros=M.PLACA_CUADROS)
    # NCC del logo (misma prueba que B): en c0–c380 no puede aparecer
    tpl, _ = C.plantilla_logo(2)
    filas = []
    for n, Y, Cb, Cr in C.cuadros_yuv(M.MAS / M.NOMBRES['completa']):
        y2 = np.asarray(Image.fromarray(Y).resize((W // 2, H // 2), Image.BOX), np.float32)
        c = C._ncc(y2, tpl)
        filas.append(dict(cuadro=n, logo_ncc_max=round(float(c.max()), 4), croma_desvio_max=int(max(np.abs(Cb.astype(int) - 128).max(),
                                                                                                     np.abs(Cr.astype(int) - 128).max()))))
    sep = filas[:FIN_A + 1]
    r['logo_ncc_max_c0_c380'] = max(f['logo_ncc_max'] for f in sep)
    r['cuadros_c0_c380_ncc_mayor_0_6'] = [f['cuadro'] for f in sep if f['logo_ncc_max'] > 0.6]
    r['logo_ncc_firma_min_max'] = [min(f['logo_ncc_max'] for f in filas[M.PLACA_CUADROS['firma'][0]:]),
                                   max(f['logo_ncc_max'] for f in filas[M.PLACA_CUADROS['firma'][0]:])]
    r['croma_desvio_max_c0_c383'] = max(f['croma_desvio_max'] for f in filas[:384])
    r['por_cuadro'] = filas
    return r


def psnr_vs_b(desde=384):
    """máster A contra máster B decodificados, cuadro a cuadro (luma), desde c384."""
    out = []
    ga, gb = frames_yuv(M.MAS / M.NOMBRES['completa']), frames_yuv(TB / 'master' / NOMBRES_B['completa'])
    ys = W * H
    for n, (a, b) in enumerate(zip(ga, gb)):
        if n < desde:
            continue
        ya = np.frombuffer(a[:ys], np.uint8).astype(np.float32); yb = np.frombuffer(b[:ys], np.uint8).astype(np.float32)
        mse = float(((ya - yb) ** 2).mean())
        out.append(dict(cuadro=n, psnr_db=round(99.0 if mse == 0 else 10 * math.log10(255 ** 2 / mse), 2)))
    return dict(psnr_min=min(o['psnr_db'] for o in out), psnr_mediana=float(np.median([o['psnr_db'] for o in out])), por_cuadro=out)


def audio_vs_b(desde_s=12.80):
    """mezcla previa y final (WAV) de A contra B desde c384 (12,80 s): residuo en dB respecto de B."""
    import soundfile as sf
    out = {}
    for k in ('completa', 'sinmusica'):
        fila = {}
        for etapa, sufijo in (('previa', '_pre'), ('final', '')):
            xa, sr = sf.read(str(M.A / f'v4_{k}{sufijo}.wav')); xb, _ = sf.read(str(TB / 'audio' / f'v4_{k}{sufijo}.wav'))
            i = int(desde_s * sr)
            a, b = xa[i:], xb[i:len(xa)]
            e = np.sqrt(((a - b) ** 2).mean()) + 1e-15; s = np.sqrt((b ** 2).mean())
            fila[etapa] = dict(identico_bit_a_bit=bool(np.array_equal(a, b)), residuo_db=round(float(20 * math.log10(e / s)), 1),
                               dif_max=float(np.abs(a - b).max()))
        out[k] = fila
    return out


def textos_vs_b():
    """lo visible cuadro a cuadro (window.visible) de A contra B: c0–c248 deben ser iguales; c249–c380 cambian por la
    frase de la voz; c381–c422 son las capas de B copiadas."""
    va = json.load(open(M.TX / 'visible.json'))['cuadros']; vb = json.load(open(TB / 'textos' / 'visible.json'))['cuadros']
    iguales, distintos = [], []
    for n in range(0, 249):
        (iguales if va[str(n)] == vb[str(n)] else distintos).append(n)
    voz = sorted({' / '.join(x['lineas']) for n in range(249, FIN_A + 1) for x in va[str(n)] if x['id'] == 'voz' and x['completa']})
    atr = sorted({' / '.join(x['lineas']) for n in range(249, FIN_A + 1) for x in va[str(n)] if x['id'] == 'atrib_voz' and x['completa']})
    b_citas = sorted({x['id'] + ': ' + ' / '.join(x['lineas']) for n in range(249, FIN_A + 1) for x in vb[str(n)] if x['completa']})
    primera = {}
    for n in range(249, FIN_A + 1):
        for x in va[str(n)]:
            if x['id'] == 'voz':
                for w in ' '.join(x['lineas']).split():
                    primera.setdefault(w, n)
    return dict(c0_c248_iguales=len(iguales), c0_c248_distintos=distintos, voz_completa=voz, atribucion=atr,
                b_en_c249_c380=b_citas, aparicion_por_palabra=primera)


def hoja_cortes(mp4, carpeta):
    """cuadros a ambos lados de cada corte de A (incluidos negro y placa), con su número."""
    from PIL import Image, ImageDraw, ImageFont
    carpeta.mkdir(parents=True, exist_ok=True)
    fnt = ImageFont.truetype(M.FONT, 22)
    tiles = []
    for c in [p['m0'] for p in PLANOS[1:]] + [381, 384, 423]:
        for n in (c - 1, c):
            im = Image.fromarray(U.leer(mp4, 270, 480, n0=n, n1=n)[0]); d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 92, 28], fill=(0, 0, 0)); d.text((4, 2), f'c{n}', font=fnt, fill=(255, 255, 0))
            tiles.append(im)
    cols = 8
    S = Image.new('RGB', (cols * 274, -(-len(tiles) // cols) * 484), (30, 30, 30))
    for i, t in enumerate(tiles):
        S.paste(t, ((i % cols) * 274, (i // cols) * 484))
    S.save(carpeta / 'cortes_A_v01.jpg', quality=88)


def hoja_lona(carpeta):
    """antes/después del borrado de la marca de apuestas (luma, contraste ×2,5 para ver restos), cada 3 cuadros."""
    from PIL import Image, ImageDraw, ImageFont
    p = [q for q in PLANOS if q.get('borrar')][0]
    ix = indices(p)
    fr, wh = decodificar(p['clip'], ix)
    fnt = ImageFont.truetype(M.FONT, 18)
    Z0, Z1 = LONA_Z
    sel = ix[::3] + [ix[-1]]
    S = Image.new('RGB', (2 * 722, len(sel) * (Z1 - Z0 + 2)), (30, 30, 30))
    for r, n in enumerate(sel):
        a = fr[n].astype(np.float32)
        b, _ = borrar_lona(a, n)
        for j, im in enumerate((a, b)):
            Y = (im @ np.array([0.2126, 0.7152, 0.0722], np.float32))[Z0:Z1]
            v = np.clip((Y - np.median(Y)) * 2.5 + 150, 0, 255).astype(np.uint8)
            I = Image.fromarray(v).convert('RGB'); d = ImageDraw.Draw(I)
            d.text((4, 2), f'fuente n{n} → c{p["m0"] + ix.index(n)} · {"original" if j == 0 else "borrado"}', font=fnt, fill=(255, 255, 0))
            S.paste(I, (j * 722, r * (Z1 - Z0 + 2)))
    S.save(carpeta / 'lona_borrado_A_v01.jpg', quality=88)


def etapa_control():
    ev = M.EVID; ev.mkdir(parents=True, exist_ok=True)
    rep = {}
    for k in ('completa', 'sinmusica'):
        f = M.MAS / M.NOMBRES[k]
        pj, t = B2.tecnico(f, tramos_a())
        rep[k] = t
        json.dump(pj, open(ev / f'ffprobe_{k}.json', 'w'), indent=1)
        print(k, t['md5_flujo_video'], t['md5_flujo_audio'], t['sonoridad'], flush=True)
    rep['separacion'] = separacion()
    rep['psnr_vs_b_desde_c384'] = psnr_vs_b()
    rep['audio_vs_b_desde_c384'] = audio_vs_b()
    rep['textos_vs_b'] = textos_vs_b()
    U.hoja_contacto(M.MAS / M.NOMBRES['completa'], ev / 'hoja_cada_0_5s_A_v01.jpg', cada=15, cols=7, ancho=240)
    hoja_cortes(M.MAS / M.NOMBRES['completa'], ev)
    hoja_lona(ev)
    jdump(rep, ev / 'control_A_v01.json')
    s = rep['separacion']
    print('separación', s['base_c381_c482_identica_a_B'], s['texto_c381_c422_identico_a_B'], s['logo_ncc_max_c0_c380'],
          s['cuadros_c0_c380_ncc_mayor_0_6'], s['logo_ncc_firma_min_max'])
    print('psnr', rep['psnr_vs_b_desde_c384']['psnr_min'], 'audio', rep['audio_vs_b_desde_c384'])
    print('textos', {k: v for k, v in rep['textos_vs_b'].items() if k != 'aparicion_por_palabra'})


def etapa_entregar():
    """copia a la carpeta de la pieza sin sobrescribir, espera 10 s, relee y compara md5 de flujos."""
    rep = json.load(open(M.EVID / 'control_A_v01.json'))
    out = {}
    for k in ('completa', 'sinmusica'):
        src = M.MAS / M.NOMBRES[k]; dst = PIEZA / M.NOMBRES[k]
        assert not dst.exists(), f'ya existe {dst}'
        shutil.copyfile(src, dst)
        out[k] = dict(destino=str(dst))
    time.sleep(10)
    for k in ('completa', 'sinmusica'):
        dst = PIEZA / M.NOMBRES[k]
        out[k].update(bytes=dst.stat().st_size, md5_flujo_video=U.md5_stream(dst, 'v'), md5_flujo_audio=U.md5_stream(dst, 'a'),
                      sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
                      flujos_iguales_al_master=(U.md5_stream(dst, 'v') == rep[k]['md5_flujo_video']
                                                and U.md5_stream(dst, 'a') == rep[k]['md5_flujo_audio']))
        print(k, out[k], flush=True)
    evd = PIEZA / 'evidencia_A_v01'
    evd.mkdir(exist_ok=True)
    for f in sorted(M.EVID.iterdir()):
        if f.is_file() and not (evd / f.name).exists():
            shutil.copyfile(f, evd / f.name)
    for f in (TA / 'fuentes.json', TA / 'planos.json', TA / 'voz' / 'voz.json', M.A / 'audio.json', M.MED / 'grado.json'):
        if not (evd / f.name).exists():
            shutil.copyfile(f, evd / f.name)
    jdump(out, TA / 'entrega_A_v01.json')
    shutil.copyfile(TA / 'entrega_A_v01.json', evd / 'entrega_A_v01.json')


if __name__ == '__main__':
    etapa = sys.argv[1]
    globals()['etapa_' + etapa]()
