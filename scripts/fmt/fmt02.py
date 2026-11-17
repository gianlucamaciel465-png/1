#!/usr/bin/env python3
"""FMT-02 · «19 años, Cañuelas» · receta del máster v01 · Pedro · 17/11/2026

Guion: /mnt/project-files/piezas/FMT_tanda_formatos/FMT-02_19_anios_canuelas/01_fede_guion_G1.md (G1)
Aprobación: 02_roma_aprobacion_G1.md (hook A; último texto con \\N sin .replace).
Herramientas: scripts/fmt/video.py, scripts/fmt/sonido.py (sin cambios) + scripts/fmt/fmt0205_util.py (medición/control).

Uso:  nice -n 10 /home/user/1/TRABAJO/venv/bin/python /home/user/1/scripts/fmt/fmt02.py [medir] [planos] [mezclas] [masters] [control] [textos_cuadros] [extra] [copiar]
Sin argumentos corre todo. Intermedios en /home/user/1/TRABAJO/fmt/fmt02/.

Desvíos respecto del guion (medidos antes del render; detalle en 03_pedro_hoja_master_v01.md):
- Plano 4: 7896 3,2333–5,6333 (c97–c168) en lugar de 3,600–6,000. La salpicadura empieza en 7896 c151 (medido), no en c162:
  con el tramo del guion caía en máster c277; corrido 11 cuadros cae en c288 (golpe + impacto en la grilla).
- Ambiente de 7885: tiene viento (graves < 120 Hz 10–20 dB sobre el lecho limpio de 7884 en 0–1,4 s y ráfagas en 3,5–4,3 s).
  Se usa la alternativa prevista (lecho de 7884 0,0–2,6) en 3,6–6,2 y el tramo limpio de la propia 7885 (1,4–3,0,
  sincronizado con la imagen) en 6,2–7,8. Ganancias igualadas por medición para que el lecho no salte.
- 7887: las dos ráfagas (1,45–1,60 y 2,88–3,05) se reemplazan por audio limpio de la misma toma (1,28–1,46 y 2,55–2,75)
  con fundidos cruzados de 20 ms, en lugar de dejar el hueco cubierto solo por el lecho de 7884 a −12.
- 7896 propia a 0 dB (el guion decía −6) para igualar el lecho medido (−28 dBFS) con el de los otros planos.
- Fundido final de música 9,8–10,2 también sobre las colas de reverberación e impacto (pistas fx y bombo).
"""
import json, shutil, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V  # noqa: E402
from sonido import Mezcla  # noqa: E402
import fmt0205_util as U  # noqa: E402

VERSION = 'v01'
NOMBRE = 'ROCCE_FMT02_19_ANIOS_CANUELAS'
T = Path('/home/user/1/TRABAJO/fmt/fmt02')
PL, AN, MZ = T / 'planos', T / 'an', T / 'mez'
EXP = Path('/home/user/1/EXPORTACIONES')
DEST = Path('/mnt/project-files/piezas/FMT_tanda_formatos/FMT-02_19_anios_canuelas')
EVI = T / f'evidencia_{VERSION}'
DUR = 10.2   # 306 cuadros

# ---------------- planos (toma, desde, hasta, kwargs) ----------------
PLANOS = [
    ('s1', 'IMG_7887', 0.0000, 3.6000, {}),                                # c0–c107   (108) apuesta + pregunta
    ('s2', 'IMG_7885', 3.1333, 4.3333, {}),                                # c108–c143 (36)  giro (7885 c94–c129)
    ('s3', 'IMG_7885', 0.0000, 3.0000, {}),                                # c144–c233 (90)  reenganche
    ('s4', 'IMG_7896', 3.2333, 5.6333, {'caja': (100, 300, 1800, 3200)}),  # c234–c305 (72)  CTA (7896 c97–c168)
]
CORTES = [108, 144, 234]   # cuadros del máster

TEXTOS = [
    dict(t0=0.0, t1=1.2, txt='19 años. Cañuelas.', estilo='CajaN', y=300, pop=True),
    dict(t0=1.2, t1=3.6, txt='Labura en la fábrica\\Nde ladrillos de su familia.', estilo='CajaN', y=300),
    dict(t0=3.6, t1=4.8, txt='Y en paralelo,', estilo='CajaN', y=240, pop=True),
    dict(t0=3.6, t1=4.8, txt='Roccé.', estilo='Grande', y=350, pop=True),
    dict(t0=5.4, t1=7.8, txt='GIVE HISTORY\\NYOUR NAME.', estilo='CajaN', y=300),
    dict(t0=7.8, t1=10.2, txt='Contanos qué estás\\Nconstruyendo.', estilo='Caja', y=300),
]

# ganancias de lecho (dB) igualadas a ≈ −28/−29 dBFS RMS medidos en la fuente (ver an/ambiente_niveles.json)
G_7884_LECHO_B = +3.5    # 7884 0,0–2,6 (−32,4 dBFS) → ≈ −29
G_7885_LIMPIO = -4.0     # 7885 1,4–3,0 (−25,1 dBFS) → ≈ −29
G_7896 = 0.0             # 7896 3,23–5,63 (−28 dBFS)
G_GOLPE_C2 = 0.0         # golpe de 7884 en c2 (guion −4): la apertura sin música necesita el golpe presente
AMB_DB = 4.0             # subida global del ambiente en las dos mezclas


def sh(*a):
    return U.run(list(a))


# ---------------- 1. medición previa (pendientes del guion) ----------------
def medir():
    AN.mkdir(parents=True, exist_ok=True)
    # audio de todas las tomas usadas o candidatas
    for t in ('IMG_7887', 'IMG_7885', 'IMG_7884', 'IMG_7896'):
        U.audio_tramos(t, AN / f'audio_{t}.json', AN / f'espectro_{t}.png')
    # hojas de la fuente cada 0,1 s (y cada cuadro donde hace falta)
    U.hoja_src('IMG_7887', 0, 110, AN / 'hoja01_7887_c0-110.jpg', cada=3, ancho=180, cols=10)
    U.hoja_src('IMG_7885', 84, 156, AN / 'hoja01_7885_c84-156.jpg', cada=3, ancho=180, cols=10)
    U.hoja_src('IMG_7885', 118, 141, AN / 'hoja02_7885_c118-141_c1.jpg', cada=1, ancho=360, cols=8)
    U.hoja_src('IMG_7896', 100, 184, AN / 'hoja01_7896_c100-184.jpg', cada=3, ancho=180, cols=10,
               caja=(100, 300, 1800, 3200))
    U.hoja_src('IMG_7896', 144, 171, AN / 'hoja02_7896_c144-171_c1.jpg', cada=1, ancho=240, cols=7)
    # salpicadura de 7896: fracción de píxeles claros sobre la línea de rocas (mitad derecha)
    import numpy as np
    fr = U.leer_src('IMG_7896', 95, 184, 540, 960)
    sal = []
    for i, f in enumerate(fr):
        Y = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
        yr = 250 + int(np.argmin(Y[250:480].mean(1)))
        sal.append({'c_fuente': 95 + i, 'blanco_der': round(float((Y[yr - 40:yr + 15, 270:] > 165).mean()), 3)})
    (AN / 'salpicadura_7896.json').write_text(json.dumps(sal, indent=0))
    # niveles de lecho por tramo usado
    import numpy as np
    from scipy.signal import butter, sosfilt
    res = {}
    m = Mezcla(1.0)
    for t, tramos in (('IMG_7887', [(0, 1.2), (1.2, 3.6), (1.28, 1.46), (2.55, 2.75)]),
                      ('IMG_7885', [(0, 1.4), (1.4, 3.0), (3.133, 4.333)]),
                      ('IMG_7884', [(0, 2.6), (3.4, 4.133), (3.85, 5.05)]), ('IMG_7896', [(3.2333, 5.6333)])):
        a = m.leer(t)
        lf = sosfilt(butter(4, 120, 'low', fs=48000, output='sos'), a)
        res[t] = [{'tramo': [s, e], 'rms_dbfs': round(float(20 * np.log10(np.sqrt((a[int(s * 48000):int(e * 48000)] ** 2).mean()))), 1),
                   'rms_graves_120_dbfs': round(float(20 * np.log10(np.sqrt((lf[int(s * 48000):int(e * 48000)] ** 2).mean()))), 1)}
                  for s, e in tramos]
    (AN / 'ambiente_niveles.json').write_text(json.dumps(res, indent=1))


# ---------------- 2. planos ----------------
def planos():
    PL.mkdir(parents=True, exist_ok=True)
    info = []
    for nom, toma, d, h, kw in PLANOS:
        info.append(V.plano(toma, d, h, PL / f'{nom}.mp4', **kw))
    n = V.unir(info, PL / 'unido.mp4')
    (PL / 'planos.json').write_text(json.dumps(info, indent=1, ensure_ascii=False))
    print('unido:', n, 'cuadros')


# ---------------- 3. mezclas ----------------
def ambiente_y_foley(m, k_foley=1.0):
    # 0,0–3,6 · 7887 (apuesta + pregunta)
    m.ambiente('IMG_7884', 0.000, 0.000, 3.400, g_db=-12)                    # lecho limpio (guion)
    m.ambiente('IMG_7884', 3.470, 0.000, 1.200, g_db=G_GOLPE_C2)             # golpe 3,53 → c2, bajo la espuma de 7887 c0
    m.ambiente('IMG_7887', 0.000, 0.000, 1.460, ini_fade=0.004, fin_fade=0.02)
    m.ambiente('IMG_7887', 1.280, 1.440, 1.620, fade=0.02)                   # reemplaza la ráfaga 1,45–1,60
    m.ambiente('IMG_7887', 1.600, 1.600, 2.880, fade=0.02)
    m.ambiente('IMG_7887', 2.550, 2.860, 3.060, fade=0.02)                   # reemplaza la ráfaga 2,88–3,05
    m.ambiente('IMG_7887', 3.040, 3.040, 3.600, ini_fade=0.02, fin_fade=0.006)
    # 3,6–7,8 · 7885 tiene viento → lecho de 7884 (alternativa prevista) + tramo limpio de 7885 sincronizado
    m.ambiente('IMG_7884', 0.000, 3.600, 6.260, g_db=G_7884_LECHO_B, ini_fade=0.006, fin_fade=0.06)
    m.ambiente('IMG_7885', 1.400, 6.200, 7.800, g_db=G_7885_LIMPIO, ini_fade=0.06, fin_fade=0.006)
    m.ambiente('IMG_7884', 3.850, 4.800, 6.000, g_db=-6)                     # resaca 3,91 → c146, sobre la espuma de 7885 c0
    # 7,8–10,2 · 7896 (salpicadura en 7896 c151 = máster c288)
    m.ambiente('IMG_7896', 3.2333, 7.800, 10.200, g_db=G_7896)
    m.ambiente('IMG_7884', 3.400, 9.467, 10.200, g_db=-3)                    # golpe 3,53 → 9,597 s (c288)
    # foley (k_foley: escala para que el foley tenga el mismo nivel absoluto en las dos mezclas)
    if k_foley:
        m.obturador(1.200, g=0.45 * k_foley)
        m.barrido(7.800, dur=0.30, g=0.15 * k_foley)


def musica(m):
    m.pad(1.2, [57, 60, 64], 1.2, g=0.05); m.ocho08(1.2, 33, dur=1.1, g=0.40)
    m.pad(2.4, [53, 57, 60], 1.2, g=0.05); m.ocho08(2.4, 29, dur=1.1, g=0.40)
    m.campana(2.4, 76, g=0.05); m.campana(3.0, 72, g=0.05); m.subida(2.4, 3.6, g=0.18); m.campana(3.6, 76, g=0.06)
    for B, c1, c2, r1, r2 in ((3.6, [60, 64, 67], [55, 59, 62], 36, 31), (6.0, [57, 60, 64], [53, 57, 60], 33, 29),
                              (8.4, [60, 64, 67], None, 36, None)):
        m.bombo(B); m.bombo(B + 0.9); m.palma(B + 1.2); m.pad(B, c1, 1.2)
        m.ocho08(B, r1, dur=1.1, glide_desde=31 if B == 3.6 else None)
        if c2:
            m.pad(B + 1.2, c2, 1.2); m.ocho08(B + 1.2, r2, dur=1.1)
        t = B
        while t < B + 2.4 - 0.01:
            m.charles(t, g=0.08); t += 0.3
    m.redoble(7.5, 7.8, g=0.10)
    m.pad(9.6, [57, 60, 64], 0.6); m.ocho08(9.6, 33, dur=0.6); m.impacto(9.6, g=0.45)
    for p in ('mus', 'fx', 'bombo'):
        m.fundido(p, 9.8, 10.2)
    m.log(9.8, 'fundido de música (mus, fx, bombo) 9,8–10,2')


def mezclas():
    """completa = ambiente + foley + música TEMP; sinmusica = ambiente + foley (mezcla aparte, sin colas de música).
    El ambiente sube AMB_DB en las dos (la apertura sin música quedaba 7–14 dB por debajo del resto, medido con
    sonoridad momentánea). En la sin música el foley se escala para quedar al mismo nivel absoluto que en la completa
    (si no, el obturador pasaba el pico verdadero: −0,3 dBTP)."""
    MZ.mkdir(parents=True, exist_ok=True)
    res = {}
    m = Mezcla(DUR); ambiente_y_foley(m); musica(m)
    I, Pk = m.exportar(str(MZ / 'fmt02_completa.wav'), lufs=-14, g_pistas={'amb': AMB_DB})
    gc = json.loads((MZ / 'fmt02_completa_eventos.json').read_text())['ganancia_db']
    res['completa'] = {'lufs': I, 'pico_dbtp': Pk, 'ganancia_db': gc}
    m = Mezcla(DUR); ambiente_y_foley(m, k_foley=0)                       # pasada 1: ganancia sin foley
    m.exportar(str(MZ / 'tmp_sinmusica.wav'), lufs=-14, g_pistas={'amb': AMB_DB})
    gs = json.loads((MZ / 'tmp_sinmusica_eventos.json').read_text())['ganancia_db']
    k = 10 ** ((gc - gs) / 20)
    m = Mezcla(DUR); ambiente_y_foley(m, k_foley=k)
    I, Pk = m.exportar(str(MZ / 'fmt02_sinmusica.wav'), lufs=-14, g_pistas={'amb': AMB_DB})
    gs2 = json.loads((MZ / 'fmt02_sinmusica_eventos.json').read_text())['ganancia_db']
    res['sinmusica'] = {'lufs': I, 'pico_dbtp': Pk, 'ganancia_db': gs2, 'k_foley': round(k, 4)}
    for f in MZ.glob('tmp_sinmusica*'):
        f.unlink()
    for nom in ('completa', 'sinmusica'):
        res[nom]['momentanea'] = U.sonoridad_momentanea(MZ / f'fmt02_{nom}.wav')
        print(nom, {k2: v for k2, v in res[nom].items() if k2 != 'momentanea'})
    (MZ / 'mezclas.json').write_text(json.dumps(res, indent=1))


# ---------------- 4. másters ----------------
def masters():
    EXP.mkdir(exist_ok=True)
    a = V.ass(TEXTOS, T / 'textos.ass')
    comp, sinm = salidas()
    for out in (comp, sinm):
        if out.exists():
            raise SystemExit(f'ya existe {out}: no se sobrescribe')
    V.master(PL / 'unido.mp4', MZ / 'fmt02_completa.wav', comp, ass_path=a)
    # sin música: el mismo stream de video copiado bit a bit (dos codificaciones de x264 no salían idénticas)
    U.remux_audio(comp, MZ / 'fmt02_sinmusica.wav', sinm)
    print('másters', comp, sinm)


def salidas():
    return [EXP / f'{NOMBRE}_{VERSION}.mp4', EXP / f'{NOMBRE}_SINMUSICA_{VERSION}.mp4']


# ---------------- 5. control ----------------
def control():
    import fmt0205_control as C
    C.control_pieza(salidas(), EVI, PL / 'unido.mp4', TEXTOS, CORTES, DUR, pieza='FMT-02',
                    puntos=puntos_fmt02, telas=TELAS, ass_path=T / 'textos.ass')


# zonas de tela lisa (sin estampado) para comparar color con PRODUCTO/ (cuadro del máster, x0,y0,x1,y1 en 1080×1920)
TELAS = {'blanca': [(120, (40, 600, 820, 1150)), (288, (170, 1090, 340, 1190))],
         'negra': [(80, (720, 1280, 1000, 1400)), (288, (380, 1150, 600, 1260))]}


def puntos_fmt02(mp4, unido, evi):
    """Tres puntos comprobables del guion."""
    import numpy as np
    from PIL import Image
    r = {}
    # 1. c36: celular arriba (cuadro de la fuente 7887 c36), obturador en 1,200 s y T2 entra en c36 (no en c35)
    fr = U.leer_mp4(mp4, c0=34, c1=37)
    mt = U.mascara_textos(T / 'textos.ass', [34, 35, 36, 37])
    r['1_texto_por_cuadro'] = {c: {'pixeles': int(m.sum()), 'renglones_y': [int(np.nonzero(m.any(1))[0].min()),
                                                                          int(np.nonzero(m.any(1))[0].max())]}
                               for c, m in mt.items()}
    r['1_fuente_c36'] = 'IMG_7887 c36 (alineación verificada en an/alineacion_planos.json; celular arriba en c30–c57)'
    ev = json.loads((MZ / 'fmt02_completa_eventos.json').read_text())
    r['1_obturador_evento'] = [e for e in ev['eventos'] if e['evento'] == 'obturador']
    # onset del obturador en la pista fx exportada (cruce de umbral)
    import soundfile as sf
    fx, sr = sf.read(str(MZ / 'fmt02_completa_fx.wav'))
    env = np.abs(fx).max(1); i0 = int(1.1 * sr); i1 = int(1.3 * sr)
    k = i0 + int(np.argmax(env[i0:i1] > 0.5 * env[i0:i1].max()))
    r['1_obturador_onset_s'] = round(k / sr, 4)
    Image.fromarray(fr[2]).save(evi / 'p1_c36_master.png')
    # 2. c108–c143: Blanca con estampado completo y sin texto encima. Huella exacta de los textos (quemados sobre gris)
    #    contra la remera (píxeles claros/celestes/negros del estampado en el plano sin textos).
    cs = list(range(108, 144))
    mt = U.mascara_textos(T / 'textos.ass', cs)
    base = U.leer_mp4(unido, c0=108, c1=143)
    sol = []
    for c, b in zip(cs, base):
        bb = b.astype(int); Y = bb.mean(2)
        cel = (bb[..., 2] - bb[..., 0] > 30) & (bb[..., 2] > 150)
        # letras negras de ROCCÉ: píxeles oscuros rodeados de tela blanca (en el plano sin textos)
        from scipy.ndimage import uniform_filter
        claro = uniform_filter((Y > 175).astype(float), 41) > 0.45
        negro = (Y < 90) & claro
        t = mt[c]; ys = np.nonzero(t.any(1))[0]
        yc = np.nonzero(cel.sum(1) > 5)[0]; yn = np.nonzero(negro.sum(1) > 8)[0]
        sol.append({'c': c, 'texto_y': [int(ys.min()), int(ys.max())] if len(ys) else None,
                    'estampado_celeste_y_min': int(yc.min()) if len(yc) else None,
                    'letras_negras_ROCCE_y_min': int(yn.min()) if len(yn) else None,
                    'solape_texto_estampado_px': int((t & (cel | negro)).sum())})
    r['2_giro_texto_vs_estampado'] = sol
    # 3. textos por tramo (desde el .ass): edad/Cañuelas/fábrica solo en c0–c107; CTA en c234–c305
    r['3_textos'] = [{'c_desde': round(k['t0'] * 30), 'c_hasta': round(k['t1'] * 30) - 1, 'texto': k['txt']} for k in TEXTOS]
    return r


def textos_cuadros():
    """Cuadro real de entrada y salida de cada texto en el máster contra el guion (aviso de Roma del 17/11 sobre
    video.master: los overlays PNG entran un cuadro antes; acá no hay overlays, solo .ass, y se comprueba igual)."""
    import fmt0205_control as C
    r = C.entradas_textos(salidas()[0], TEXTOS, EVI, n_cuadros=306)
    print('todos coinciden:', all(x['coincide'] for x in r))


def extra():
    """medición previa y datos de mezcla dentro de la evidencia"""
    mp = EVI / 'medicion_previa'; mp.mkdir(parents=True, exist_ok=True)
    for f in sorted(AN.glob('*')):
        if f.suffix in ('.json', '.jpg', '.png') and not f.name.startswith(('7887_c', '7885_c')) and 'mini' not in f.name \
                and not f.name.endswith('_srgb.png'):
            shutil.copy2(f, mp / f.name)
    for f in ('7887_c30-63_cabeza.jpg', '7885_privee_c126-138.jpg', '7896_salpicadura_c145-162.jpg'):
        if (AN / f).exists():
            shutil.copy2(AN / f, mp / f)
    mz = EVI / 'mezcla'; mz.mkdir(exist_ok=True)
    for f in ('mezclas.json', 'fmt02_completa_eventos.json', 'fmt02_sinmusica_eventos.json'):
        shutil.copy2(MZ / f, mz / f)
    import numpy as np, soundfile as sf
    for nom in ('completa', 'sinmusica'):
        a, sr = sf.read(str(MZ / f'fmt02_{nom}.wav'))
        fil = U.niveles_tramos(MZ / f'fmt02_{nom}.wav', paso=0.1)['tramos']
        fil = [{'t0': x['t0'], 'rms_dbfs': x['rms_dbfs'], 'periodicidad': 0} for x in fil]
        U.espectrograma_png(a.mean(1), sr, fil, f'FMT-02 mezcla {nom} (wav antes de AAC)', mz / f'espectro_{nom}.png')
    shutil.copy2(T / 'textos.ass', EVI / 'textos.ass')
    shutil.copy2(PL / 'planos.json', EVI / 'planos.json')


# ---------------- 6. copiar a la carpeta de la pieza ----------------
def copiar():
    import fmt0205_control as C
    C.copiar_pieza(salidas(), EVI, DEST / f'evidencia_{VERSION}', extra=[T / '03_pedro_hoja_master_v01.md'])


if __name__ == '__main__':
    etapas = sys.argv[1:] or ['medir', 'planos', 'mezclas', 'masters', 'control', 'textos_cuadros', 'extra', 'copiar']
    for e in etapas:
        t0 = time.time(); globals()[e](); print(f'== {e}: {time.time() - t0:.0f} s')
