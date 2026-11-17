#!/usr/bin/env python3
"""FMT-05 · «Tres movimientos de celular» · receta del máster v01 (hook A) · Pedro · 17/11/2026

Guion: /mnt/project-files/piezas/FMT_tanda_formatos/FMT-05_tres_movimientos/01_fede_guion_G1.md (G1)
Aprobación: 02_roma_aprobacion_G1.md (1,5× con mezcla de cuadros; C3 fuera de la columna de botones; loop 8002 c89 → c90).
Herramientas: scripts/fmt/video.py, scripts/fmt/sonido.py (sin cambios) + fmt0205_util.py / fmt0205_control.py.

Uso:  nice -n 10 /home/user/1/TRABAJO/venv/bin/python /home/user/1/scripts/fmt/fmt05.py [medir] [planos] [alinear] [mezclas] [masters] [control] [textos_cuadros] [extra] [copiar]

Desvíos respecto del guion (medidos; detalle en 03_pedro_hoja_master_v01.md):
- C2 y C3: 8004 1,0–2,0 y 2,0–3,0 a velocidad 1 (guion: 1,0–2,5 a 1,5× y 2,5–3,5). En 8004 2,5–3,5 «Privée» entra en la
  columna de botones (x > 940, y 1266–1455) desde 8004 c84 y queda cortado a la derecha desde c97; el reencuadre que
  pide Roma (z ≤ 1,15 y cy más abajo) no alcanza: con la ventana abajo de todo «Privée» queda en y ≈ 1168–1380 y el
  acercamiento corta más el estampado por los costados. Con 2,0–3,0 el estampado está fuera de la columna en
  c180–c203 (8004 c60–c83) y el foco llega en c180–c186 (8004 c60–c66, medido con nitidez), sobre el compás.
- B2 a 1,5× con mezcla de cuadros (núcleo triangular, fmt0205_util.vel_mezcla) en lugar de saltar cuadros.
- Lechos de 8002 y 8004 a 0 dB (guion −6/−8) para igualar el nivel medido del lecho de 7884; 8004 en un solo tramo
  continuo 0,0–3,0 (la imagen ahora es continua).
- Colas de música y efectos que pasan de 10,0 s se suman al principio (loop sin corte ni fundido).
"""
import json, shutil, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V  # noqa: E402
from sonido import Mezcla, SR  # noqa: E402
import fmt0205_util as U  # noqa: E402

VERSION = 'v01'
NOMBRE = 'ROCCE_FMT05_TRES_MOVIMIENTOS'
T = Path('/home/user/1/TRABAJO/fmt/fmt05')
PL, AN, MZ = T / 'planos', T / 'an', T / 'mez'
EXP = Path('/home/user/1/EXPORTACIONES')
DEST = Path('/mnt/project-files/piezas/FMT_tanda_formatos/FMT-05_tres_movimientos')
EVI = T / f'evidencia_{VERSION}'
DUR = 10.0   # 300 cuadros, 5 compases de 120 BPM

PLANOS = [
    ('a',  'IMG_8002', 3.0000, 3.5000, {}),               # c0–c14    (15) 8002 c90–c104
    ('b1', 'IMG_7884', 0.0000, 0.8000, {}),               # c15–c38   (24) 7884 c0–c23
    ('b2', 'IMG_7884', 0.8000, 3.3000, {'vel': 1.5}),     # c39–c88   (50) 7884 c24–c98 a 1,5× (mezcla de cuadros)
    ('b3', 'IMG_7884', 3.3000, 4.3333, {}),               # c89–c119  (31) 7884 c99–c129
    ('c1', 'IMG_8004', 0.0000, 1.0000, {}),               # c120–c149 (30) 8004 c0–c29
    ('c2', 'IMG_8004', 1.0000, 2.0000, {}),               # c150–c179 (30) 8004 c30–c59  (desvío)
    ('c3', 'IMG_8004', 2.0000, 3.0000, {}),               # c180–c209 (30) 8004 c60–c89  (desvío)
    ('d',  'IMG_8002', 0.0000, 3.0000, {}),               # c210–c299 (90) 8002 c0–c89 → loop a 8002 c90 (c0)
]
CORTES = [15, 120, 210]          # cortes de toma (c39, c89, c150, c180 son empalmes dentro de la misma toma)
EMPALMES = [39, 89]              # cambios de velocidad dentro de 7884

TEXTOS = [
    dict(t0=0.0, t1=1.5, txt='Todo esto,\\Ncon un celular.', estilo='CajaN', y=260, pop=True),
    dict(t0=1.5, t1=3.0, txt='Por arriba del hombro', estilo='CajaN', y=260),
    dict(t0=4.0, t1=5.5, txt='Arrancá desenfocado', estilo='CajaN', y=260),
    dict(t0=7.0, t1=8.5, txt='Entrá de golpe al detalle', estilo='CajaN', y=260),
    dict(t0=8.0, t1=10.0, txt='Guardalo para tu próxima foto.', estilo='Caja', y=380),
]

G_PLAYA = 0.0      # 8002 / 8004 con hp 120: ≈ −35 dBFS, igualado al lecho de 7884 (−32)
AMB_DB = 10.0      # medido: con 0 dB el ambiente quedaba ~24 dB bajo la música (−36 contra −12 LUFS momentáneos)


# ---------------- 1. medición previa ----------------
def medir():
    AN.mkdir(parents=True, exist_ok=True)
    for t in ('IMG_8002', 'IMG_8004', 'IMG_7884'):
        U.audio_tramos(t, AN / f'audio_{t}.json', AN / f'espectro_{t}.png')
    U.hoja_src('IMG_7884', 0, 40, AN / 'hoja01_7884_c0-40.jpg', cada=2, ancho=200, cols=7)
    U.hoja_src('IMG_8004', 60, 111, AN / 'hoja01_8004_c60-111.jpg', cada=3, ancho=180, cols=9)
    U.hoja_src('IMG_8002', 78, 106, AN / 'hoja01_8002_c78-106_c1.jpg', cada=1, ancho=160, cols=10)
    from scipy.ndimage import laplace
    from PIL import Image, ImageDraw
    # 8004: nitidez (llegada del foco) y posición del estampado contra la columna de botones (escala del máster, z=1)
    fr = U.leer_src('IMG_8004', 0, 112, 1080, 1920)
    filas = []
    for i, f in enumerate(fr):
        Y = f.astype(float).mean(2); g = np.hypot(*np.gradient(Y[1000:1700]))
        ff = f.astype(int); cel = (ff[..., 2] - ff[..., 0] > 45) & (ff[..., 2] > 140)
        der = cel[1000:, 940:]; rd = np.nonzero(der.sum(1) >= 3)[0]
        cc = np.nonzero(cel[1000:1700].sum(0) >= 4)[0]
        filas.append({'c_fuente': i, 'nitidez_grad_p99': round(float(np.percentile(g, 99)), 1),
                      'celeste_x_max': int(cc.max()) if len(cc) else None,
                      'celeste_en_columna_botones_y': [int(rd.min()) + 1000, int(rd.max()) + 1000] if len(rd) else None})
    (AN / 'medicion_8004.json').write_text(json.dumps(filas, indent=0))
    # vistas con la columna de botones dibujada
    tiles = []
    for i in range(60, 106, 3):
        im = Image.fromarray(fr[i]).copy(); d = ImageDraw.Draw(im)
        d.rectangle([940, 1000, 1079, 1919], outline='red', width=4)
        for yy in (220, 1380):
            d.line([(0, yy), (1080, yy)], fill='yellow', width=3)
        im = im.crop((0, 800, 1080, 1700)).resize((360, 300)); d = ImageDraw.Draw(im); d.text((4, 4), f'8004 c{i}', fill='yellow')
        tiles.append(im)
    lien = Image.new('RGB', (360 * 8, 300 * 2)); [lien.paste(t, (360 * (k % 8), 300 * (k // 8))) for k, t in enumerate(tiles)]
    lien.save(AN / '8004_c60-105_columna_botones.jpg', quality=90)
    # reencuadre de Roma (z = 1,15, ventana abajo): dónde quedaría «Privée»
    sim = []
    for c in (84, 87, 90, 93, 96):
        f = fr[c].astype(int); cel = (f[..., 2] - f[..., 0] > 45) & (f[..., 2] > 140); cel[:1000] = False
        ys, xs = np.nonzero(cel[:, 700:]); xs = xs + 700
        Y4, X4 = 2 * ys, 2 * xs                                # 4K
        for x0, nom in ((141, 'centrado'), (282, 'a la derecha')):
            esc = 1080 / 1878
            sim.append({'c': c, 'ventana': nom, 'privee_x_max_master': int((X4.max() - x0) * esc),
                        'privee_y_master': [int((Y4.min() - 501) * esc), int((Y4.max() - 501) * esc)],
                        'recorte_izquierdo_4k': x0})
    (AN / 'reencuadre_roma_z115.json').write_text(json.dumps(sim, indent=0))


# ---------------- 2. planos ----------------
def planos():
    PL.mkdir(parents=True, exist_ok=True)
    info = []
    for nom, toma, d, h, kw in PLANOS:
        kw = dict(kw)
        vel = kw.pop('vel', 1.0)
        if vel != 1.0:
            info.append(U.vel_mezcla(toma, d, h, vel, PL / f'{nom}.mp4', **kw))
        else:
            info.append(V.plano(toma, d, h, PL / f'{nom}.mp4', **kw))
    n = V.unir(info, PL / 'unido.mp4')
    (PL / 'planos.json').write_text(json.dumps(info, indent=1, ensure_ascii=False))
    # referencia para el control del 1,5×: el mismo tramo saltando cuadros (setpts + fps de video.plano)
    V.plano('IMG_7884', 0.8, 3.3, PL / 'ref_b2_salto.mp4', vel=1.5)
    print('unido:', n, 'cuadros')


def alinear():
    """Primer y último cuadro de cada plano a velocidad 1 contra la fuente (±2 cuadros)."""
    r = {}
    for nom, toma, d, h, kw in PLANOS:
        if kw.get('vel', 1.0) != 1.0:
            continue
        c0, n = round(d * 30), round((h - d) * 30)
        r[nom] = {'primero': U.alinear_plano(PL / f'{nom}.mp4', toma, c0, k=0),
                  'ultimo': U.alinear_plano(PL / f'{nom}.mp4', toma, c0 + n - 1, k=n - 1)}
        print(nom, r[nom]['primero']['mejor'], r[nom]['ultimo']['mejor'])
    (AN / 'alineacion_planos.json').write_text(json.dumps(r, indent=1))


# ---------------- 3. mezclas ----------------
def ambiente_y_foley(m, k_foley=1.0):
    m.ambiente('IMG_8002', 3.000, 0.000, 0.500, g_db=G_PLAYA, hp=120, ini_fade=0.002, fin_fade=0.02)
    m.ambiente('IMG_7884', 0.000, 0.480, 2.987, fade=0.02)            # B1 sincronizado + lecho a velocidad normal en B2
    m.ambiente('IMG_7884', 3.280, 2.947, 4.000, fade=0.02)            # B3 sincronizado: golpe 3,53 → 3,197 s (c96)
    m.ambiente('IMG_8004', 0.000, 3.980, 7.020, g_db=G_PLAYA, hp=120, fade=0.02)   # C1–C3 continuo
    m.ambiente('IMG_8002', 0.000, 7.000, 10.000, g_db=G_PLAYA, hp=120, ini_fade=0.02, fin_fade=0.002)
    if k_foley:
        k = k_foley
        m.barrido(0.5, g=0.15 * k); m.obturador(1.0, g=0.45 * k); m.toque(1.5, g=0.12 * k)
        m.barrido(4.0, g=0.18 * k); m.barrido(7.0, g=0.15 * k)
        m.barrido(8.0, dur=0.5, g=0.25 * k); m.impacto(8.0, g=0.5 * k)


def musica(m):
    for t, ch, r in ((0, [62, 65, 69], 38), (2, [58, 62, 65], 34), (6, [60, 64, 67], 36), (8, [57, 61, 64], 33)):
        m.pad(t, ch, 2.0 if t != 6 else 1.5, g=0.05); m.ocho08(t, r, dur=0.9); m.ocho08(t + 1, r, dur=0.9 if t != 6 else 0.4)
    m.pad(4, [53, 57, 60], 2.0, g=0.05, corte=600); m.ocho08(4, 29, dur=1.9, g=0.35); m.subida(5.0, 6.0, g=0.2)
    m.campana(6.0, 79, g=0.06)
    for k in (0, 1, 2, 3, 6, 7, 8, 9):
        m.bombo(k)
    for p in (0.5, 1.5, 2.5, 3.5, 6.5, 8.5, 9.5):
        m.palma(p)
    for a, b in ((0, 4), (6, 7.5), (8, 10)):
        t = a
        while t < b - 0.01:
            m.charles(t, g=0.08); t += 0.25


def plegar(m, dur=DUR):
    """Loop: todo lo que pasa de `dur` (colas de pad, reverberación, impacto) se suma al principio y se corta en dur."""
    N = int(round(dur * SR))
    for p, x in m.pistas.items():
        cola = x[N:]
        x[:len(cola)] += cola
        m.pistas[p] = x[:N].copy()
    m.N = N; m.dur = dur
    m.log(dur, 'colas posteriores a 10,0 s sumadas al principio (loop)')


def mezclas():
    MZ.mkdir(parents=True, exist_ok=True)
    res = {}
    m = Mezcla(DUR + 3.0); ambiente_y_foley(m); musica(m); plegar(m)
    I, Pk = m.exportar(str(MZ / 'fmt05_completa.wav'), lufs=-14, g_pistas={'amb': AMB_DB})
    gc = json.loads((MZ / 'fmt05_completa_eventos.json').read_text())['ganancia_db']
    res['completa'] = {'lufs': I, 'pico_dbtp': Pk, 'ganancia_db': gc}
    m = Mezcla(DUR + 3.0); ambiente_y_foley(m, k_foley=0); plegar(m)
    m.exportar(str(MZ / 'tmp_sinmusica.wav'), lufs=-14, g_pistas={'amb': AMB_DB})
    gs = json.loads((MZ / 'tmp_sinmusica_eventos.json').read_text())['ganancia_db']
    k = 10 ** ((gc - gs) / 20)
    m = Mezcla(DUR + 3.0); ambiente_y_foley(m, k_foley=k); plegar(m)
    I, Pk = m.exportar(str(MZ / 'fmt05_sinmusica.wav'), lufs=-14, g_pistas={'amb': AMB_DB})
    gs2 = json.loads((MZ / 'fmt05_sinmusica_eventos.json').read_text())['ganancia_db']
    res['sinmusica'] = {'lufs': I, 'pico_dbtp': Pk, 'ganancia_db': gs2, 'k_foley': round(k, 4)}
    for f in MZ.glob('tmp_sinmusica*'):
        f.unlink()
    for nom in ('completa', 'sinmusica'):
        res[nom]['momentanea'] = U.sonoridad_momentanea(MZ / f'fmt05_{nom}.wav')
        print(nom, {k2: v for k2, v in res[nom].items() if k2 != 'momentanea'})
    (MZ / 'mezclas.json').write_text(json.dumps(res, indent=1))


# ---------------- 4. másters ----------------
def salidas():
    return [EXP / f'{NOMBRE}_{VERSION}.mp4', EXP / f'{NOMBRE}_SINMUSICA_{VERSION}.mp4']


def masters():
    a = V.ass(TEXTOS, T / 'textos.ass')
    comp, sinm = salidas()
    for out in (comp, sinm):
        if out.exists():
            raise SystemExit(f'ya existe {out}: no se sobrescribe')
    V.master(PL / 'unido.mp4', MZ / 'fmt05_completa.wav', comp, ass_path=a)
    U.remux_audio(comp, MZ / 'fmt05_sinmusica.wav', sinm)
    print('másters', comp, sinm)


# ---------------- 5. control ----------------
TELAS = {'blanca': [(0, (0, 1250, 1080, 1700)), (100, (0, 1250, 1080, 1750)), (195, (0, 1450, 1080, 1900))],
         'negra': [(25, (560, 1150, 900, 1450))]}


def puntos_fmt05(mp4, unido, evi):
    from PIL import Image, ImageDraw
    r = {}
    # 1. la Negra en c15–c38
    fr = U.leer_mp4(mp4, c0=15, c1=38)
    tiles = []
    for i in (0, 8, 15, 23):
        im = Image.fromarray(fr[i]).crop((420, 700, 1080, 1400)).resize((330, 350)); d = ImageDraw.Draw(im)
        d.text((4, 4), f'c{15 + i}', fill='yellow'); tiles.append(im)
    lien = Image.new('RGB', (330 * 4, 350)); [lien.paste(t, (330 * k, 0)) for k, t in enumerate(tiles)]
    lien.save(evi / 'p1_negra_c15-c38.jpg', quality=92)
    r['1_negra'] = 'ver p1_negra_c15-c38.jpg (lectura visual en la hoja)'
    # 2. loop: d termina en 8002 c89 y a empieza en 8002 c90; diferencia c299→c0 contra las internas
    r['2_alineacion'] = {'d_ultimo': U.alinear_plano(PL / 'd.mp4', 'IMG_8002', 89, k=89),
                         'a_primero': U.alinear_plano(PL / 'a.mp4', 'IMG_8002', 90, k=0)}
    # sobre la imagen sin textos (unido): en el máster el cambio de rótulo CTA → hook suma diferencia en la costura
    Y = U.leer_mp4(unido, 270, 480).astype(np.float32).mean(3)
    seam = float(np.abs(Y[0] - Y[-1]).mean())
    dif_d = np.abs(np.diff(Y[270:300], axis=0)).mean((1, 2)); dif_a = np.abs(np.diff(Y[0:15], axis=0)).mean((1, 2))
    r['2_dif_c299_a_c0_sin_textos'] = round(seam, 2)
    r['2_dif_internas_c270-c299_y_c0-c14(mediana,max,mediana,max)'] = [
        round(float(np.median(dif_d)), 2), round(float(dif_d.max()), 2),
        round(float(np.median(dif_a)), 2), round(float(dif_a.max()), 2)]
    Ym = U.leer_mp4(mp4, 270, 480, c0=0, c1=0).astype(np.float32).mean(3)
    Ym1 = U.leer_mp4(mp4, 270, 480, c0=299, c1=299).astype(np.float32).mean(3)
    r['2_dif_c299_a_c0_master_con_textos'] = round(float(np.abs(Ym[0] - Ym1[0]).mean()), 2)
    import soundfile as sf
    for nom in ('completa', 'sinmusica'):
        a, sr = sf.read(str(MZ / f'fmt05_{nom}.wav'))
        n = int(0.05 * sr)
        r[f'2_audio_{nom}'] = {'muestras': len(a), 'dur_s': len(a) / sr,
                               'rms_ultimos_50ms_dbfs': round(float(20 * np.log10(np.sqrt((a[-n:] ** 2).mean()))), 1),
                               'rms_primeros_50ms_dbfs': round(float(20 * np.log10(np.sqrt((a[:n] ** 2).mean()))), 1),
                               'salto_muestra_final_a_inicial': round(float(np.abs(a[-1] - a[0]).max()), 4),
                               'salto_tipico_entre_muestras_p99': round(float(np.percentile(np.abs(np.diff(a, axis=0)), 99)), 4)}
    # 3. movimientos que terminan en la remera sin texto encima del estampado
    sets = {'b3_c89-c119': range(89, 120), 'c3_c180-c209': range(180, 210), 'd_c240-c269': range(240, 270),
            'a_c0-c14': range(0, 15)}
    from scipy.ndimage import uniform_filter
    r['3_texto_vs_estampado'] = {}
    for nom, cs in sets.items():
        cs = list(cs); mt = U.mascara_textos(T / 'textos.ass', cs)
        base = U.leer_mp4(unido, c0=cs[0], c1=cs[-1])
        fil = []
        for c, b in zip(cs, base):
            bb = b.astype(int); Yb = bb.mean(2)
            cel = (bb[..., 2] - bb[..., 0] > 30) & (bb[..., 2] > 140)
            claro = uniform_filter((Yb > 170).astype(float), 41) > 0.5
            negro = (Yb < 90) & claro
            # celeste DE LA TELA: celeste con entorno claro (excluye el cielo azul de D y de A, que es oscuro: Y < 170)
            cel = cel & claro
            est = cel | negro
            t = mt[c]; ys = np.nonzero(t.any(1))[0]
            ye = np.nonzero(cel.sum(1) > 5)[0]
            col = cel[1000:, 940:]; yc = np.nonzero(col.sum(1) >= 3)[0]
            fil.append({'c': c, 'texto_y': [int(ys.min()), int(ys.max())] if len(ys) else None,
                        'celeste_y': [int(ye.min()), int(ye.max())] if len(ye) else None,
                        'solape_texto_estampado_px': int((t & est).sum()),
                        'celeste_en_columna_botones_y': [int(yc.min()) + 1000, int(yc.max()) + 1000] if len(yc) else None})
        r['3_texto_vs_estampado'][nom] = fil
    # pico de la ola en c105 (7884 c115): fracción de rocío (claro y poco saturado) arriba del borde de la roca
    # (máster y < 510), sobre la imagen sin textos. El agua del mar es más oscura y parda; el rocío es blanco grisáceo.
    fb = U.leer_mp4(unido, 540, 960, c0=86, c1=119).astype(float)
    ola = {}
    for i, f in enumerate(fb):
        top = f[0:255]; Yt = top.mean(2); sat = top.max(2) - top.min(2)
        ola[86 + i] = round(float(((Yt > 175) & (sat < 45)).mean()), 3)
    r['3_ola_rocio_por_cuadro'] = ola
    r['3_ola_pico_c'] = max(ola, key=ola.get)
    # 1,5×: diferencias entre cuadros consecutivos en B2 (mezcla) contra el mismo tramo saltando cuadros
    def alterna(path, c0=None, c1=None):
        x = U.leer_mp4(path, 270, 480, c0=c0, c1=c1).astype(np.float32).mean(3)
        d = np.abs(np.diff(x, axis=0)).mean((1, 2))
        return d, float(np.abs(np.diff(d)).mean() / d.mean())
    d_m, a_m = alterna(mp4, 38, 89)
    d_s, a_s = alterna(PL / 'ref_b2_salto.mp4')
    r['vel15_diferencias_mezcla_c38-c89'] = [round(float(x), 2) for x in d_m]
    r['vel15_diferencias_salto_referencia'] = [round(float(x), 2) for x in d_s]
    r['vel15_indice_alternancia(media|Δd|/media d)'] = {'mezcla': round(a_m, 3), 'salto': round(a_s, 3)}
    par = d_m[1::2]; impar = d_m[0::2]
    r['vel15_media_dif_pares_impares_mezcla'] = [round(float(par.mean()), 2), round(float(impar.mean()), 2)]
    return r


def control():
    import fmt0205_control as C
    C.control_pieza(salidas(), EVI, PL / 'unido.mp4', TEXTOS, CORTES, DUR, pieza='FMT-05',
                    puntos=puntos_fmt05, telas=TELAS, ass_path=T / 'textos.ass')


def textos_cuadros():
    """Cuadro real de entrada y salida de cada texto en el máster contra el guion (aviso de Roma del 17/11 sobre
    video.master: los overlays PNG entran un cuadro antes; acá no hay overlays, solo .ass, y se comprueba igual)."""
    import fmt0205_control as C
    r = C.entradas_textos(salidas()[0], TEXTOS, EVI, n_cuadros=300)
    print('todos coinciden:', all(x['coincide'] for x in r))


def extra():
    mp = EVI / 'medicion_previa'; mp.mkdir(parents=True, exist_ok=True)
    for f in sorted(AN.glob('*')):
        if f.suffix in ('.json', '.jpg', '.png'):
            shutil.copy2(f, mp / f.name)
    for f in ('audio_IMG_8002.json', 'audio_IMG_8004.json', 'espectro_IMG_8002.png', 'espectro_IMG_8004.png'):
        pass
    mz = EVI / 'mezcla'; mz.mkdir(exist_ok=True)
    for f in ('mezclas.json', 'fmt05_completa_eventos.json', 'fmt05_sinmusica_eventos.json'):
        shutil.copy2(MZ / f, mz / f)
    import soundfile as sf
    for nom in ('completa', 'sinmusica'):
        a, sr = sf.read(str(MZ / f'fmt05_{nom}.wav'))
        fil = [{'t0': x['t0'], 'rms_dbfs': x['rms_dbfs'], 'periodicidad': 0}
               for x in U.niveles_tramos(MZ / f'fmt05_{nom}.wav', paso=0.1)['tramos']]
        U.espectrograma_png(a.mean(1), sr, fil, f'FMT-05 mezcla {nom} (wav antes de AAC)', mz / f'espectro_{nom}.png')
    shutil.copy2(T / 'textos.ass', EVI / 'textos.ass')
    shutil.copy2(PL / 'planos.json', EVI / 'planos.json')
    shutil.copy2(PL / 'b2.mp4.pesos.json', EVI / 'b2_pesos_mezcla_1.5x.json')


def copiar():
    import fmt0205_control as C
    C.copiar_pieza(salidas(), EVI, DEST / f'evidencia_{VERSION}', extra=[T / '03_pedro_hoja_master_v01.md'])


if __name__ == '__main__':
    etapas = sys.argv[1:] or ['medir', 'planos', 'alinear', 'mezclas', 'masters', 'control', 'textos_cuadros', 'extra', 'copiar']
    for e in etapas:
        t0 = time.time(); globals()[e](); print(f'== {e}: {time.time() - t0:.0f} s')
