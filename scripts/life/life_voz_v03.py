#!/usr/bin/env python3
"""Roccé Life · tanda 2 · locución G2 con la voz de marca Firme 04 sobre los másteres aprobados → v03 (Pedro, 25/11/2026).

Guion: piezas/LIFE_rocce_life/TANDA2/16_roma_aprobacion_locucion_G2.md (G2 aprobado por Roma con el cambio de V3 T4,
«Enero también.»). La imagen no cambia: el flujo de video de cada máster v02 se copia (mismo md5) y solo se rehace el audio.

Voz: perfil «Roccé — Firme 04» (scripts/voz/BANCO_VOCAL.md) con scripts/proxima/locucion.py sin modificar
(edge_firme.py → tratamiento_firme.py → recorte de puntas). edge-tts 7.3.1 no toma HTTPS_PROXY: la etapa «entorno» deja en
voz-env un módulo edge_proxy_patch.py cargado por un .pth (el sitecustomize del sistema tapa uno propio) que le pasa el
proxy del contenedor como argumento `proxy` (la verificación TLS no se toca).

Fondo: las pistas de cada receta aprobada, regeneradas importando las recetas sin modificarlas (life_v3 con V3_VERSION=v02,
life_v4_a_v02 → life_v4_a, life_v5) y comprobadas bit a bit contra la mezcla previa guardada de v02. Después:
  · bombeo de la música con el bombo exactamente como sonido.Mezcla.exportar / life_v4_a.pre_mezcla;
  · ambiente, música y bombo bajan con la voz: ffmpeg sidechaincompress (la voz que lo maneja con apad=whole_dur);
    efectos (obturador, barrido, golpes) y la voz de Topuria no se tocan;
  · la voz entra centrada (×√0,5 por canal); la suma sigue el orden de la receta (amb + fx + mus + bombo + voz);
  · V3 y V5: ganancia y alimiter (level=false) con life_v2.limitar_tp (−14 LUFS, pico real ≤ −1,5 dBTP antes del AAC);
    V4: la ganancia de A v02 y su mismo alimiter, para que la mezcla hasta 13,10 s sea la de A v02 bit a bit.
Etapas (nice -n 10):
  entorno · voz · audio v3|v4|v5 (un proceso por video) · master · transcribir (python de whisper-env) · entregar
Intermedios en TRABAJO/life2/voz_v03/ (fuera de git). Nada se publica; sin créditos (edge-tts es el servicio gratuito de
lectura de Edge, sin cuenta).
"""
import json, math, os, subprocess, sys, hashlib, shutil, time
from pathlib import Path

R = Path('/home/user/1')
TR = R / 'TRABAJO/life2'
T = TR / 'voz_v03'
FR = T / 'frases'
PZ = Path('/mnt/project-files/piezas/LIFE_rocce_life/TANDA2')
S_ENT = Path(os.environ.get('S', '/tmp/claude-0/-home-user/d313bd1c-f93b-5b31-95b6-3edaf7578920/scratchpad/ent'))
VOZ_PY = S_ENT / 'voz-env/bin/python'
VENV_PY = R / 'TRABAJO/venv/bin/python'
FPS, SR = 30, 48000
CUADRO = 1 / FPS
UMBRAL_DB = -45.0                    # mismo criterio de voz que locucion.py (ventanas de 10 ms, dB respecto del máximo)

# --- guion G2 aprobado: (id, tramo, entrada, fin de ventana, texto exacto, fin de ventana según, fin del paso) ---------
# Ventana = de la entrada a la entrada siguiente (tabla de 16_roma_aprobacion_locucion_G2.md); V3 T5 termina en 5,40
# porque Roma fija que la voz calla de 5,4 a 9,4 s; la última frase de cada video, al final del máster. «Fin del paso» =
# último instante del paso del máster que muestra ese texto (recetas y hojas de máster): si la voz lo pasa, se avisa.
# V3 T5 (Roma, opción A): entra en 4,74 y la voz calla desde 5,76; si el golpe del corte de 4,70 tapa el primer fonema
# (etapa golpe_t5), entra en 4,76 y calla desde 5,78.
T5_ENTRADA = float(os.environ.get('T5_ENTRADA', '4.74'))
T5_CALLA = {4.74: 5.76, 4.76: 5.78}[T5_ENTRADA]
# tomas que no salen de la etapa voz: «Diciembre.» es la toma medida en pruebas_conflicto (0,706 s) con la que Roma decidió
EXTRA = {'v3_t2b': ('pruebas_conflicto', 'alt_t2_diciembre')}
FRASES = {
    'v3': [   # con las decisiones de Roma del 25/11 (después de la hoja 17 v1): T2 «Diciembre.» sola; T5 opción A
        ('v3_t1', 'T1', 0.10, 1.92, '¿Arrancás o esperás a enero?', 'entrada de T2', 1.80),
        ('v3_t2b', 'T2', 1.92, 2.70, 'Diciembre.', 'fin del paso 2: «“Arranco en enero.”» (2,70–3,60) queda sin voz (Roma)', 2.70),
        ('v3_t4', 'T4', 3.72, T5_ENTRADA, 'Enero también.', 'entrada de T5', 4.70),
        ('v3_t5', 'T5', T5_ENTRADA, T5_CALLA, 'Cinco domingos.', f'la voz calla desde {T5_CALLA:.2f} (opción A de Roma)', 5.60),
        ('v3_t9', 'T9', 9.42, 10.95, 'Te quedan cinco.', 'entrada de T10', 10.70),
        ('v3_t10', 'T10', 10.95, 393 / FPS, 'Guardalo para el domingo.', 'fin del máster', 393 / FPS),
    ],
    'v4': [
        ('v4_t13', 'T13', 13.19, 14.25, '¿Y la tuya?', 'entrada de T14', 423 / FPS),
        ('v4_t14', 'T14', 14.25, 483 / FPS, 'Seguí al equipo.', 'fin del máster', 483 / FPS),
    ],
    'v5': [
        ('v5_t1', 'T1', 0.32, 6.10, 'Querés más.', 'entrada de T9', 36 / FPS),
        ('v5_t9', 'T9', 6.10, 335 / FPS, 'Querer más no te hace agrandado.', 'fin del máster', 248 / FPS),
    ],
}
NF = {'v3': 393, 'v4': 483, 'v5': 335}
V4_IGUAL_HASTA = 13.10               # hasta acá la mezcla de A v03 tiene que ser la de A v02

# --- másteres de partida (no se tocan) y entregas -------------------------------------------------------------------
def _v3(n, k):
    s = '_SINMUSICA' if k == 'sinmusica' else ''
    return f'ROCCE_LIFE_V3_5_DOMINGOS_{n}{s}'


MASTERS = {   # video: [(etiqueta, versión de audio, archivo v02, archivo v03, md5 del flujo de video aprobado)]
    'v3': [(f'{n}_{k}', k, PZ / 'V3_5_domingos' / f'{_v3(n, k)}_v02.mp4', f'{_v3(n, k)}_v03.mp4', md5)
           for n, md5 in ((36, '6c8e8fc4c77455e7938b0f165efd9337'), (35, '0792c5cfad29541057efbb65cb2c7f91'),
                          (34, 'fb8222d5e9ddab8c98283a8dc0ec8ce2'), (33, '37f28c236a923bb08d9e6667ee634efc'))
           for k in ('completa', 'sinmusica')],
    'v4': [('A_completa', 'completa', PZ / 'V4_vuelve' / 'ROCCE_LIFE_V4_VUELVE_A_v02.mp4', 'ROCCE_LIFE_V4_VUELVE_A_v03.mp4',
            '20ddf4ec383b22caab44b3b2d50f9b6d'),
           ('A_sinmusica', 'sinmusica', PZ / 'V4_vuelve' / 'ROCCE_LIFE_V4_VUELVE_A_SINMUSICA_v02.mp4',
            'ROCCE_LIFE_V4_VUELVE_A_SINMUSICA_v03.mp4', '20ddf4ec383b22caab44b3b2d50f9b6d')],
    'v5': [('completa', 'completa', PZ / 'V5_agrandado' / 'ROCCE_LIFE_V5_AGRANDADO_v02.mp4', 'ROCCE_LIFE_V5_AGRANDADO_v03.mp4',
            '2574aebeeff032334bf22992bcacfb3f'),
           ('sinmusica', 'sinmusica', PZ / 'V5_agrandado' / 'ROCCE_LIFE_V5_AGRANDADO_SINMUSICA_v02.mp4',
            'ROCCE_LIFE_V5_AGRANDADO_SINMUSICA_v03.mp4', '2574aebeeff032334bf22992bcacfb3f')],
}
CARPETA = {'v3': PZ / 'V3_5_domingos', 'v4': PZ / 'V4_vuelve', 'v5': PZ / 'V5_agrandado'}
EVID = {'v3': 'evidencia_v03', 'v4': 'evidencia_A_v03', 'v5': 'evidencia_v03'}

# --- mezcla ---------------------------------------------------------------------------------------------------------
SC = dict(threshold=0.02, ratio=6, attack=15, release=250, makeup=1, knee=2.82843, link='average', detection='rms')
PISTAS_QUE_BAJAN = ('amb', 'fx', 'mus', 'bombo')  # todo el fondo (ambiente, efectos, música con su bombo); la voz de Topuria, no
OBJETIVO_DB = 12.5                                # voz sobre fondo, dentro de 10–15 dB
L_VOZ = -15.0                                     # la voz sola, con la ganancia final de la mezcla (LUFS integrados)
SC_ADELANTO = 0.030                               # el control del sidechain va 30 ms antes que la voz (anticipo)
SC_MIN, SC_MAX = -36.0, 24.0                      # nivel de control del sidechain por frase (dB sobre la voz normalizada)
RANGO_DB = (10.0, 15.0)


def nice(cmd):
    return ['nice', '-n', '10'] + [str(c) for c in cmd]


def run(cmd, **k):
    return subprocess.run(nice(cmd), check=True, capture_output=True, **k).stdout


def jdump(o, f):
    Path(f).parent.mkdir(parents=True, exist_ok=True)
    json.dump(o, open(f, 'w'), indent=1, ensure_ascii=False)


def md5f(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


# =====================================================================================================================
# entorno · edge-tts 7.3.1 abre su websocket con aiohttp sin leer HTTPS_PROXY (en esta sesión fallaba con «Name or service
# not known»). Un módulo cargado por .pth en voz-env le pasa el proxy como argumento; certifi ya apunta al CA del proxy en edge_firme.py.
# =====================================================================================================================
SITECUSTOM = '''# Agregado por scripts/life/life_voz_v03.py (etapa entorno): edge-tts 7.3.1 no toma HTTPS_PROXY.
# Se le pasa el proxy del contenedor como argumento `proxy` de Communicate. No toca la verificación TLS.
import os
_p = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
if _p:
    try:
        import edge_tts as _e
        _o = _e.Communicate.__init__
        def _i(self, *a, **k):
            k.setdefault("proxy", _p)
            _o(self, *a, **k)
        _e.Communicate.__init__ = _i
    except Exception:
        pass
'''


def etapa_entorno():
    sp = Path(run([VOZ_PY, '-c', 'import site; print(site.getsitepackages()[0])']).decode().strip())
    (sp / 'sitecustomize.py').unlink(missing_ok=True)       # /usr/local/lib/python3.13/sitecustomize.py lo tapa: no sirve
    f = sp / 'edge_proxy_patch.py'; f.write_text(SITECUSTOM)
    (sp / 'zz_edge_proxy.pth').write_text('import edge_proxy_patch\n')   # los .pth se procesan también con python -I
    chk = run([VOZ_PY, '-I', '-c', 'import edge_tts, inspect; print(edge_tts.Communicate.__init__.__name__)']).decode().strip()
    assert chk == '_i', chk
    print(f, md5f(f), 'parche activo con -I')


# =====================================================================================================================
# voz · Firme 04 con locucion.py (sin modificar), una frase por línea; después, ataque y fin medidos en cada frase
# =====================================================================================================================
def leer_mono(p):
    import numpy as np
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(p), '-ac', '1', '-ar', str(SR), '-f', 'f64le', '-'])
    return np.frombuffer(raw, np.float64).copy()


def ataque_fin(x, hop_ms=1, win_ms=10, umbral_db=UMBRAL_DB):
    """primer y último instante con voz: ventanas RMS de 10 ms cada 1 ms sobre −45 dB del máximo (criterio de
    locucion.py, con más resolución). Ataque = inicio de la primera ventana; fin = final de la última."""
    import numpy as np
    w, h = int(win_ms * SR / 1000), int(hop_ms * SR / 1000)
    c = np.concatenate([[0.0], np.cumsum(x ** 2)])
    i = np.arange(0, len(x) - w, h)
    rms = np.sqrt((c[i + w] - c[i]) / w) + 1e-12
    db = 20 * np.log10(rms / rms.max())
    v = np.where(db > umbral_db)[0]
    return i[v[0]] / SR, (i[v[-1]] + w) / SR


def etapa_voz():
    # tratamiento_firme.py no es determinista (Praat: dos corridas sobre la misma síntesis dan md5 distintos y ±3 ms de
    # duración): las frases usadas quedan fijas con su sha256 en frases.json; rehacerlas pide «voz --rehacer».
    if (FR / 'frases.json').exists() and '--rehacer' not in sys.argv:
        sys.exit('las frases ya están hechas (frases.json); para rehacerlas: voz --rehacer')
    FR.mkdir(parents=True, exist_ok=True)
    guion = FR / 'guion_G2.tsv'
    guion.write_text(''.join(f'{fid}\t{txt}\n' for v in FRASES.values() for fid, _, _, _, txt, _, _ in v), encoding='utf-8')
    env = dict(os.environ, VOZ_PY=str(VOZ_PY))
    subprocess.run(nice([VENV_PY, R / 'scripts/proxima/locucion.py', guion, FR]), check=True, env=env)
    loc = json.load(open(FR / 'locucion.json'))
    info = {f['id']: f for f in loc['frases']}
    rep = dict(perfil=loc['perfil'], motor=loc['motor'], frases=[])
    for vid, fr in FRASES.items():
        for fid, tramo, t0, t1, txt, fuente_fin, fin_paso in fr:
            x = leer_mono(FR / f'{fid}.wav')
            a, b = ataque_fin(x)
            dur_voz = b - a
            rep['frases'].append(dict(
                video=vid, id=fid, tramo=tramo, texto=txt, texto_sintetizado=info[fid]['texto_sintetizado'],
                entrada=t0, fin_ventana=round(t1, 3), ventana_s=round(t1 - t0, 3), fin_ventana_de=fuente_fin,
                clip_s=round(len(x) / SR, 3), ataque_en_clip_s=round(a, 4), fin_en_clip_s=round(b, 4),
                voz_s=round(dur_voz, 3), entra=bool(dur_voz <= t1 - t0 + 1e-9), margen_s=round(t1 - t0 - dur_voz, 3),
                fin_del_paso=round(fin_paso, 3), fin_de_voz_en_master=round(t0 + dur_voz, 3),
                pasa_el_fin_del_paso_s=round(max(0.0, t0 + dur_voz - fin_paso), 3),
                sha256_wav=hashlib.sha256((FR / f'{fid}.wav').read_bytes()).hexdigest()))
            r = rep['frases'][-1]
            print(f"{fid:7s} voz {r['voz_s']:.3f} s / ventana {r['ventana_s']:.3f} s  {'ENTRA' if r['entra'] else 'NO ENTRA'} "
                  f"({r['margen_s']:+.3f})  fin {r['fin_de_voz_en_master']:.3f} · paso hasta {r['fin_del_paso']:.3f}  {txt}", flush=True)
    jdump(rep, FR / 'frases.json')


def etapa_frases():
    """sin sintetizar: copia las tomas EXTRA a frases/ y vuelve a medir ataque, fin y ventana de todas las frases de
    FRASES (frases.json; la versión anterior queda como frases_G2v1.json)."""
    for fid, (car, nom) in EXTRA.items():
        for suf in ('.wav', '_base.mp3', '_tratada.wav'):
            src, dst = T / car / f'{nom}{suf}', FR / f'{fid}{suf}'
            if not dst.exists():
                shutil.copyfile(src, dst)
    if not (FR / 'frases_G2v1.json').exists():
        shutil.copyfile(FR / 'frases.json', FR / 'frases_G2v1.json')
    loc = {f['id']: f for f in json.load(open(FR / 'locucion.json'))['frases']}
    for fid, (car, nom) in EXTRA.items():
        e = {f['id']: f for f in json.load(open(T / car / 'locucion.json'))['frases']}[nom]
        loc[fid] = dict(e, id=fid, origen=f'{car}/{nom}')
    viejo = json.load(open(FR / 'frases_G2v1.json'))
    rep = dict(perfil=viejo['perfil'], motor=viejo['motor'], frases=[])
    for vid, fr in FRASES.items():
        for fid, tramo, t0, t1, txt, fuente_fin, fin_paso in fr:
            x = leer_mono(FR / f'{fid}.wav'); a, b = ataque_fin(x); d = b - a
            rep['frases'].append(dict(
                video=vid, id=fid, tramo=tramo, texto=txt, texto_sintetizado=loc[fid]['texto_sintetizado'],
                origen=loc[fid].get('origen', 'frases/ (etapa voz)'),
                entrada=t0, fin_ventana=round(t1, 3), ventana_s=round(t1 - t0, 3), fin_ventana_de=fuente_fin,
                clip_s=round(len(x) / SR, 3), ataque_en_clip_s=round(a, 4), fin_en_clip_s=round(b, 4),
                voz_s=round(d, 3), entra=bool(d <= t1 - t0 + 1e-9), margen_s=round(t1 - t0 - d, 3),
                fin_del_paso=round(fin_paso, 3), fin_de_voz_en_master=round(t0 + d, 3),
                pasa_el_fin_del_paso_s=round(max(0.0, t0 + d - fin_paso), 3),
                sha256_wav=hashlib.sha256((FR / f'{fid}.wav').read_bytes()).hexdigest()))
            r = rep['frases'][-1]
            print(f"{fid:7s} {t0:.2f}–{r['fin_de_voz_en_master']:.3f} voz {r['voz_s']:.3f} / ventana {r['ventana_s']:.3f} "
                  f"{'ENTRA' if r['entra'] else 'NO ENTRA'} · paso hasta {r['fin_del_paso']:.2f}  {txt}", flush=True)
    jdump(rep, FR / 'frases.json')


# =====================================================================================================================
# golpe_t5 · ¿el golpe del corte de 4,70 tapa el primer fonema de T5? (sobre la mezcla de V3 ya hecha con T5_ENTRADA)
# =====================================================================================================================
def etapa_golpe_t5():
    """el golpe del corte de 4,70 (agudo: bombo 150→55 Hz, palma 0,9–3,2 kHz, toque 3,2 kHz; solo en la mezcla completa:
    la sin música no tiene golpes de música) contra el primer fonema de T5, la /s/ de «Cinco». Perfil cada 10 ms de voz
    y fondo (fondo = mezcla previa − voz, o sea ya bajado por el sidechain) en 3–10 kHz (banda de la /s/) y < 1 kHz
    (banda del bombo). La /s/ va del ataque al comienzo de la vocal (primer tramo en que la voz < 1 kHz supera a la voz
    3–10 kHz). Tapado por el golpe = la parte aguda del golpe sigue sonando después del ataque: en la mezcla v02 (sin voz
    ni sidechain) el fondo 3–10 kHz está más de 3 dB sobre su nivel de antes del golpe (mediana 4,60–4,69)."""
    import numpy as np
    import soundfile as sf
    from scipy.signal import butter, sosfiltfilt
    A = T / 'v3' / 'audio'
    au = json.load(open(A / 'audio.json'))
    ev = json.load(open(str(au['completa']['ref_previa_v02']).replace('_pre.wav', '_eventos.json')))['eventos']
    golpe = [e['t'] for e in ev if abs(e['t'] - 4.70) < 0.02]
    t_golpe = 4.70
    pos = [p for p in au['completa']['posiciones'] if p['id'] == 'v3_t5'][0]
    out = dict(metodo=etapa_golpe_t5.__doc__, t5_entrada=T5_ENTRADA, golpe_s=t_golpe, eventos_en_4_70=len(golpe),
               ataque_t5_s=pos['ataque'], distancia_ataque_golpe_s=round(pos['ataque'] - t_golpe, 4), perfil={})
    for k in ('completa', 'sinmusica'):
        pre, _ = sf.read(str(A / f'v3_{k}_pre.wav'), dtype='float64', always_2d=True)
        voz, _ = sf.read(str(A / f'v3_{k}_voz_firme.wav'), dtype='float64', always_2d=True)
        f, v = (pre - voz).mean(1), voz.mean(1)
        r2, _ = sf.read(str(au[k]['ref_previa_v02']), dtype='float64', always_2d=True); f2 = r2.mean(1)
        hb = butter(4, [3000, 10000], 'band', fs=SR, output='sos'); lb = butter(4, 1000, 'low', fs=SR, output='sos')
        vh, fh, vl, fl = sosfiltfilt(hb, v), sosfiltfilt(hb, f), sosfiltfilt(lb, v), sosfiltfilt(lb, f)
        f2h = sosfiltfilt(hb, f2)
        w = int(0.01 * SR); filas = []
        for t in np.arange(4.69, 4.905, 0.01):
            i = int(round(t * SR))
            filas.append(dict(t=round(float(t), 2), voz_3_10k=round(rms_db(vh[i:i + w]), 1), fondo_3_10k=round(rms_db(fh[i:i + w]), 1),
                              voz_bajo_1k=round(rms_db(vl[i:i + w]), 1), fondo_bajo_1k=round(rms_db(fl[i:i + w]), 1),
                              v02_fondo_3_10k=round(rms_db(f2h[i:i + w]), 1)))
        estable = float(np.median([rms_db(f2h[int(round(t * SR)):int(round(t * SR)) + w]) for t in np.arange(4.60, 4.695, 0.01)]))
        vocal = next(r['t'] for r in filas if r['t'] > pos['ataque'] and r['voz_bajo_1k'] > r['voz_3_10k'])
        s_ = [r for r in filas if pos['ataque'] <= r['t'] < vocal]
        golpe_agudo_hasta = max([r['t'] for r in filas if r['t'] >= 4.70 and r['v02_fondo_3_10k'] > estable + 3] or [None], key=lambda x: x or 0)
        out['perfil'][k] = dict(
            cada_10ms=filas, fondo_3_10k_antes_del_golpe_db=round(estable, 1), golpe_agudo_sobre_estable_hasta_s=golpe_agudo_hasta,
            s_de_cinco=[pos['ataque'], vocal], s_margen_3_10k_db=[round(r['voz_3_10k'] - r['fondo_3_10k'], 1) for r in s_],
            s_sobre_el_fondo_desde_s=next((r['t'] for r in s_ if r['voz_3_10k'] > r['fondo_3_10k']), None),
            s_margen_3_10k_mediana_db=round(float(np.median([r['voz_3_10k'] - r['fondo_3_10k'] for r in s_])), 1))
        print(k, {kk: vv for kk, vv in out['perfil'][k].items() if kk != 'cada_10ms'}, flush=True)
    print('distancia ataque − golpe', out['distancia_ataque_golpe_s'], flush=True)
    jdump(out, A / f'golpe_t5_{T5_ENTRADA:.2f}.json')


# =====================================================================================================================
# audio · pistas de cada receta aprobada (importada sin modificar) + voz + sidechain + sonoridad
# =====================================================================================================================
def _bombeo(P, N):
    """la música baja con el bombo: copia exacta de sonido.Mezcla.exportar / life_v4_a.pre_mezcla."""
    import numpy as np
    import sonido as S_
    bk = np.abs(P['bombo']).mean(1)
    a = np.exp(-1 / (0.12 * S_.SR))
    e = np.zeros(N); acc = 0.0
    pk = np.convolve(bk, np.ones(64) / 64, 'same')
    for i in range(0, N, 64):
        v = pk[i:i + 64].max() if i < N else 0
        acc = max(v, acc * a ** 64); e[i:i + 64] = acc
    e = e / (e.max() + 1e-9)
    return 1 - (1 - S_.db(-6.0)) * e


def pistas_v3():
    os.environ['V3_VERSION'] = 'v02'
    import life_v3 as L3
    import sonido as S
    out = {}
    for k in ('completa', 'sinmusica'):                       # = life_v3.etapa_audio (generadores con semilla propia)
        m = S.Mezcla(L3.DUR)
        L3._ambiente(m); L3._foley(m, S)
        if k == 'completa':
            L3._musica(m, S); L3._pasabajos_y_hueco(m)
            m.fundido('mus', 12.60, L3.DUR); m.fundido('bombo', 12.60, L3.DUR)
            m.fundido('fx', 12.60, L3.DUR)
        out[k] = dict(m=m, ref_pre=L3.A / f'v3_{k}_pre.wav', ref_final=L3.WAV[k], receta='scripts/life/life_v3.py (V3_VERSION=v02)')
    return out, None


def pistas_v5():
    import life_v5 as L5
    from sonido import Mezcla
    m = Mezcla(L5.DUR); L5.ambientes5(m); L5.foley5(m); L5.musica5(m); L5.huecos_y_final(m)      # = life_v5.etapa_audio
    s_ = Mezcla(L5.DUR); L5.ambientes5(s_); L5.foley5(s_); L5.huecos_y_final(s_)
    rec = 'scripts/life/life_v5.py (+ life_v5_golpes.py para medir golpes)'
    return {'completa': dict(m=m, ref_pre=L5.A / 'v5_completa_pre.wav', ref_final=L5.A / 'v5_completa.wav', receta=rec),
            'sinmusica': dict(m=s_, ref_pre=L5.A / 'v5_sinmusica_pre.wav', ref_final=L5.A / 'v5_sinmusica.wav', receta=rec)}, None


def pistas_v4():
    import life_v4_a_v02 as A2                     # deja life_v4_a con la mezcla de A v02 (mezcla_v02) y sus rutas
    A = A2.A
    out, gan = {}, {}
    for k, con in (('completa', True), ('sinmusica', False)):          # = life_v4_a.etapa_audio, mismo orden
        A.GAN_B[k] = json.load(open(A.TB / 'audio' / f'v4_{k}_eventos.json'))['ganancia_db']
        m, voz, e = A.mezcla_a(con, k)
        ev = json.load(open(A2.M.A / f'v4_{k}_eventos.json'))
        out[k] = dict(m=m, ref_pre=A2.M.A / f'v4_{k}_pre.wav', ref_final=A2.M.A / f'v4_{k}.wav',
                      receta='scripts/life/life_v4_a_v02.py → life_v4_a.py → life_v4_v02.py → life_v4.py')
        gan[k] = ev['ganancia_db']
    return out, gan


def pista_voz(vid, N):
    """la pista de voz del video: cada frase con su ataque en la entrada (muestra exacta). Devuelve la pista y las
    posiciones medidas."""
    import numpy as np
    fr = {f['id']: f for f in json.load(open(FR / 'frases.json'))['frases']}
    v = np.zeros(N); pos = []
    for fid, tramo, t0, t1, txt, _, _ in FRASES[vid]:
        x = leer_mono(FR / f'{fid}.wav')
        i0 = int(round((t0 - fr[fid]['ataque_en_clip_s']) * SR))
        cola = 0.0
        i_fin = int(round(t1 * SR))
        if i0 + len(x) > i_fin:            # la cola del recorte (debajo de −45 dB) pasa el fin de la ventana: se corta ahí
            a_, b_ = ataque_fin(x)
            corte, f = i_fin - i0, int(0.005 * SR)
            assert b_ * SR <= corte - f, f'{fid}: la voz llega al fin de la ventana'
            cola = (len(x) - corte) / SR
            x = x[:corte].copy(); x[-f:] *= np.linspace(1, 0, f)
        assert i0 >= 0 and i0 + len(x) <= N, (fid, i0)
        assert not v[i0:i0 + len(x)].any(), f'{fid} se pisa con otra frase'
        v[i0:i0 + len(x)] = x
        a, b = ataque_fin(x)
        pos.append(dict(id=fid, tramo=tramo, texto=txt, entrada_guion=t0, fin_ventana=round(t1, 3),
                        clip=[round(i0 / SR, 4), round((i0 + len(x)) / SR, 4)],
                        ataque=round(i0 / SR + a, 4), fin=round(i0 / SR + b, 4), cola_cortada_s=round(cola, 4)))
    return v, pos


def sidechain(pistas, sc, dur, carpeta):
    """ffmpeg sidechaincompress sobre cada pista con la misma señal de control (la voz, con apad=whole_dur). Todo en
    doble precisión (WAV pcm_f64le de entrada y de salida): donde la voz no actúa la ganancia es 1 y la muestra sale igual."""
    import numpy as np
    import soundfile as sf
    carpeta.mkdir(parents=True, exist_ok=True)
    fsc = carpeta / 'sc.wav'; sf.write(str(fsc), sc, SR, subtype='DOUBLE')
    ins, fc, maps = [], [], []
    for j, (nom, x) in enumerate(pistas.items()):
        f = carpeta / f'in_{nom}.wav'; sf.write(str(f), x, SR, subtype='DOUBLE'); ins += ['-i', f]
    n = len(pistas)
    ins += ['-i', fsc]
    p = ':'.join(f'{k}={v}' for k, v in SC.items())
    fc.append(f'[{n}:a]apad=whole_dur={dur:.6f},asplit={n}' + ''.join(f'[s{j}]' for j in range(n)))
    for j, nom in enumerate(pistas):
        fc.append(f'[{j}:a][s{j}]sidechaincompress={p}[o{j}]')
        maps += ['-map', f'[o{j}]', '-c:a', 'pcm_f64le', carpeta / f'out_{nom}.wav']
    run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(fc), *maps])
    out = {}
    for nom, x in pistas.items():
        y, sr = sf.read(str(carpeta / f'out_{nom}.wav'), dtype='float64', always_2d=True)
        assert sr == SR and y.shape == x.shape, (nom, y.shape, x.shape)
        out[nom] = y
    return out


def rms_db(x):
    import numpy as np
    return 20 * math.log10(math.sqrt(float(np.mean(x ** 2))) + 1e-12)


def voz_vs_fondo(voz, fondo, pos):
    """por frase: ventanas de 50 ms entre el ataque y el fin con la voz activa (≥ máximo de la frase − 20 dB). La voz que
    se oye está apagada en «fondo»; la que maneja el sidechain no (el fondo ya está bajado). Promedio de canales.
    Medida principal: mediana de las ventanas (como en A v01/v02); también energía de la frase, mínimo y máximo."""
    import numpy as np
    w = int(0.05 * SR); out = []
    for p in pos:
        i0, i1 = int(p['ataque'] * SR), int(p['fin'] * SR)
        filas = []
        for i in range(i0, i1 - w + 1, w):
            filas.append((i / SR, rms_db(voz[i:i + w]), rms_db(fondo[i:i + w])))
        vmax = max(f[1] for f in filas)
        act = [f for f in filas if f[1] >= vmax - 20]
        vv = np.array([10 ** (f[1] / 10) for f in act]); ff = np.array([10 ** (f[2] / 10) for f in act])
        dif = [f[1] - f[2] for f in act]
        out.append(dict(id=p['id'], ventanas_50ms=len(act),
                        voz_db=round(10 * math.log10(vv.mean()), 1), fondo_db=round(10 * math.log10(ff.mean()), 1),
                        dif_frase_db=round(10 * math.log10(vv.mean() / ff.mean()), 1),
                        dif_mediana_db=round(float(np.median(dif)), 1), dif_min_db=round(min(dif), 1),
                        dif_max_db=round(max(dif), 1), fondo_sin_bajar_db=None,
                        ventanas_en_rango=f"{sum(RANGO_DB[0] <= d <= RANGO_DB[1] for d in dif)}/{len(dif)}",
                        ventanas_bajo_10db=sum(d < RANGO_DB[0] for d in dif),
                        por_ventana=[dict(t=round(f[0], 2), voz_db=round(f[1], 1), fondo_db=round(f[2], 1),
                                          dif_db=round(f[1] - f[2], 1)) for f in act]))
    return out


def silencio_fuera(voz, pos, N):
    """la pista de voz es cero exacto fuera de [entrada − 1 cuadro, fin de ventana] de cada frase."""
    import numpy as np
    dentro = np.zeros(N, bool); extensiones = []
    for p in pos:
        a = int(round((p['entrada_guion'] - CUADRO) * SR)); b = int(round(p['fin_ventana'] * SR))
        dentro[max(0, a):b] = True
        extensiones.append(dict(id=p['id'], clip=p['clip'], ventana=[round(p['entrada_guion'] - CUADRO, 4), p['fin_ventana']],
                                clip_dentro_de_ventana=bool(p['clip'][0] >= p['entrada_guion'] - CUADRO - 1e-9
                                                            and p['clip'][1] <= p['fin_ventana'] + 1e-9)))
    nz = np.nonzero(voz)[0]
    return dict(max_abs_fuera=float(np.abs(voz[~dentro]).max()), muestras_no_cero_fuera=int((voz[~dentro] != 0).sum()),
                primera_muestra_no_cero_s=round(nz[0] / SR, 4), ultima_muestra_no_cero_s=round(nz[-1] / SR, 4),
                por_frase=extensiones)


def lufs_de(x, tmp):
    import soundfile as sf
    sf.write(str(tmp), x.astype('float32'), SR, subtype='FLOAT')
    return medir_ebur(tmp)[0]


def medir_ebur(f):
    r = subprocess.run(nice(['ffmpeg', '-nostats', '-i', f, '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-']),
                       capture_output=True, text=True).stderr
    g = lambda k: float([l for l in r.splitlines() if l.strip().startswith(k)][-1].split()[1])
    return g('I:'), g('Peak:'), g('LRA:')


def etapa_audio():
    import numpy as np
    import soundfile as sf
    sys.path.insert(0, str(R / 'scripts/fmt')); sys.path.insert(0, str(R / 'scripts/life'))
    vid = sys.argv[2]
    gen, gan_v4 = {'v3': pistas_v3, 'v4': pistas_v4, 'v5': pistas_v5}[vid]()
    import life_v2 as L2
    A = T / vid / 'audio'; A.mkdir(parents=True, exist_ok=True)
    rep = dict(video=vid, sidechain=SC, sidechain_anticipo_s=SC_ADELANTO, pistas_que_bajan=PISTAS_QUE_BAJAN, objetivo_voz_sobre_fondo_db=OBJETIVO_DB,
               voz_sola_lufs_objetivo=L_VOZ)
    N = None
    for k, g in gen.items():
        m = g['m']; N = m.N
        P = {kk: v.copy() for kk, v in m.pistas.items()}
        duck_b = _bombeo(P, N)
        mus_p = P['mus'] * duck_b[:, None]
        # 1) las pistas regeneradas son las de v02: la mezcla previa sale igual bit a bit a la guardada
        pre_v02 = (P['amb'] + P['fx'] + mus_p + P['bombo'] + P['voz']).astype(np.float32)
        ref, _ = sf.read(str(g['ref_pre']), dtype='float32', always_2d=True)
        igual = bool(ref.shape == pre_v02.shape and np.array_equal(ref, pre_v02))
        assert igual, (k, 'las pistas regeneradas no dan la mezcla previa de v02')
        # 2) voz: una sola ganancia por versión, para que la voz sola quede en L_VOZ LUFS con la ganancia FINAL de la mezcla.
        #    V4: ganancia de A v02 (fija). V3/V5: limitar_tp elige la ganancia final; si difiere de la supuesta en más de
        #    0,3 dB se rehace todo con la ganancia medida (máximo 4 vueltas).
        voz_m, pos = pista_voz(vid, N)
        sf.write(str(A / f'{vid}_voz_firme_mono.wav'), voz_m.astype(np.float32), SR, subtype='FLOAT')
        g_mezcla = gan_v4[k] if vid == 'v4' else -14.0 - medir_ebur(g['ref_pre'])[0]
        s_sc0 = {p_['id']: 0.0 for p_ in pos}; vueltas_mezcla = []
        for vuelta in range(4):
            # ganancia de la voz para esta vuelta
            L0 = lufs_de(np.stack([voz_m, voz_m], 1) * math.sqrt(0.5) * 10 ** (g_mezcla / 20), A / '_tmp_voz.wav')
            g_v = L_VOZ - L0
            g_frase = {p_['id']: g_v for p_ in pos}
            s_sc = dict(s_sc0)
            clip = {p_['id']: tuple(int(round(t * SR)) for t in p_['clip']) for p_ in pos}

            def por_frase(x, d):
                y = np.zeros(N)
                for fid, (a, b) in clip.items():
                    y[a:b] = x[a:b] * 10 ** (d[fid] / 20)
                return y
            # 3) sidechain: la voz SIN la ganancia de arriba maneja el compresor, con un nivel de control por frase que se ajusta
            #    hasta que la voz quede OBJETIVO_DB sobre el fondo (más control = el fondo baja más). Si el fondo ya está más de
            #    15 dB abajo sin bajar nada, se baja esa frase de voz (no se puede subir el fondo).
            todas = {'amb': P['amb'], 'fx': P['fx'], 'mus': mus_p, 'bombo': P['bombo']}
            baja = {kk: v for kk, v in todas.items() if kk in PISTAS_QUE_BAJAN and np.abs(v).max() > 0}
            fondo_sin_bajar = P['amb'] + P['fx'] + mus_p + P['bombo'] + P['voz']
            hist = []
            for it in range(8):
                sc = np.roll(por_frase(voz_m, s_sc), -int(round(SC_ADELANTO * SR)))     # el control se adelanta (anticipo)
                bajadas = sidechain(baja, sc, N / SR, A / f'sc_{k}')
                for kk, v in todas.items():
                    bajadas.setdefault(kk, v)                 # pista que no baja o que está vacía: tal cual
                fondo = bajadas['amb'] + bajadas['fx'] + bajadas['mus'] + bajadas['bombo'] + P['voz']   # la voz de Firme apagada
                voz_g = por_frase(voz_m, g_frase)
                voz_st = np.stack([voz_g, voz_g], 1) * math.sqrt(0.5)
                med = voz_vs_fondo(voz_st.mean(1), fondo.mean(1), pos)
                hist.append({r['id']: dict(control_db=round(s_sc[r['id']], 2), voz_db=round(g_frase[r['id']], 2),
                                           dif_mediana=r['dif_mediana_db'], dif_energia=r['dif_frase_db']) for r in med})
                if all(abs(r['dif_mediana_db'] - OBJETIVO_DB) <= 0.5 for r in med):
                    break
                for r in med:
                    fid = r['id']; err = OBJETIVO_DB - r['dif_mediana_db']        # > 0: el fondo tiene que bajar más
                    s_sc[fid] = min(SC_MAX, max(SC_MIN, s_sc[fid] + err / (1 - 1 / SC['ratio'])))
                    if s_sc[fid] <= SC_MIN and r['dif_mediana_db'] > RANGO_DB[1] - 0.5:
                        g_frase[fid] -= r['dif_mediana_db'] - OBJETIVO_DB
            sin_bajar = voz_vs_fondo(voz_st.mean(1), fondo_sin_bajar.mean(1), pos)
            for r, s_ in zip(med, sin_bajar):
                r['fondo_sin_bajar_db'] = s_['fondo_db']; r['el_fondo_baja_db'] = round(s_['fondo_db'] - r['fondo_db'], 1)
                r['ganancia_voz_db'] = round(g_frase[r['id']], 2); r['nivel_de_control_sidechain_db'] = round(s_sc[r['id']], 2)
                r['en_rango'] = bool(RANGO_DB[0] <= r['dif_mediana_db'] <= RANGO_DB[1])
            sf.write(str(A / f'{vid}_{k}_sidechain.wav'), sc.astype(np.float32), SR, subtype='FLOAT')
            # 4) mezcla previa (orden de la receta) y sonoridad
            pre = bajadas['amb'] + bajadas['fx'] + bajadas['mus'] + bajadas['bombo'] + (P['voz'] + voz_st)
            fpre = A / f'{vid}_{k}_pre.wav'; ffin = A / f'{vid}_{k}.wav'
            sf.write(str(fpre), pre.astype(np.float32), SR, subtype='FLOAT')
            sf.write(str(A / f'{vid}_{k}_voz_firme.wav'), voz_st.astype(np.float32), SR, subtype='FLOAT')
            if vid == 'v4':                         # la ganancia y el limitador de A v02, sin corrección
                gan = gan_v4[k]
                run(['ffmpeg', '-v', 'error', '-y', '-i', fpre, '-af',
                     f'volume={gan:.2f}dB,alimiter=limit=0.83:level=false:attack=3:release=60:latency=1', '-c:a', 'pcm_f32le', ffin])
                I, Pk, LRA = medir_ebur(ffin)
                son = dict(metodo='ganancia de A v02 y su alimiter (limit=0.83, level=false), sin corrección', ganancia_db=gan,
                           lufs=I, pico_dbtp=Pk, lra=LRA, dentro_de_tolerancia=bool(-15 <= I <= -13 and Pk <= -1.0))
            else:
                r_ = L2.limitar_tp(ffin)
                son = dict(metodo='life_v2.limitar_tp (alimiter level=false; −14 LUFS; pico real ≤ −1,5 dBTP)', **r_)
            gl_db = son.get('ganancia_db', son.get('vueltas', [{}])[-1].get('ganancia_db', 0))
            vueltas_mezcla.append(dict(ganancia_supuesta_db=round(g_mezcla, 2), ganancia_final_db=gl_db, lufs=son['lufs'],
                                       pico_dbtp=son['pico_dbtp']))
            s_sc0 = dict(s_sc)
            if vid == 'v4' or abs(gl_db - g_mezcla) <= 0.3:
                break
            g_mezcla = gl_db
        # 5) comparación con v02 (antes de codificar)
        fin, _ = sf.read(str(ffin), dtype='float32', always_2d=True)
        ref_f, _ = sf.read(str(g['ref_final']), dtype='float32', always_2d=True)
        comp = {}
        if vid == 'v4':
            j = int(round(V4_IGUAL_HASTA * SR))
            comp = dict(muestras_hasta_13_10=j,
                        previa_igual_bit_a_bit_hasta_13_10=bool(np.array_equal(pre.astype(np.float32)[:j], ref[:j])),
                        final_igual_bit_a_bit_hasta_13_10=bool(np.array_equal(fin[:j], ref_f[:j])),
                        primera_muestra_distinta_previa_s=round(int(np.argmax(np.any(pre.astype(np.float32) != ref, 1))) / SR, 5),
                        primera_muestra_distinta_final_s=round(int(np.argmax(np.any(fin != ref_f, 1))) / SR, 5))
        # cuánto aprieta el limitador durante cada frase: final contra previa × ganancia (pico y energía, en dB)
        gl = 10 ** (gl_db / 20)
        lim = []
        for p in pos:
            a_, b_ = int(p['ataque'] * SR), int(p['fin'] * SR)
            x_ = pre[a_:b_] * gl; y_ = fin[a_:b_].astype(np.float64)
            lim.append(dict(id=p['id'], pico_antes_dbfs=round(20 * math.log10(np.abs(x_).max()), 2),
                            pico_despues_dbfs=round(20 * math.log10(np.abs(y_).max()), 2),
                            baja_el_pico_db=round(20 * math.log10(np.abs(x_).max() / np.abs(y_).max()), 2),
                            baja_la_energia_db=round(10 * math.log10((x_ ** 2).sum() / (y_ ** 2).sum()), 3)))
        voz_lufs = lufs_de(voz_st * 10 ** (gl_db / 20), A / '_tmp_voz.wav')
        rep[k] = dict(receta=g['receta'], pistas_regeneradas_igual_a_v02=igual, ref_previa_v02=str(g['ref_pre']),
                      vueltas_ganancia=vueltas_mezcla, voz_sola_lufs_final=voz_lufs, ajuste_sidechain=hist,
                      posiciones=pos, voz_vs_fondo=med, sonoridad_wav=son, comparacion_v02=comp, limitador_en_frases=lim,
                      silencio_voz=silencio_fuera(voz_g, pos, N), duracion_s=round(N / SR, 6),
                      wav=str(ffin), md5_wav=md5f(ffin))
        print(vid, k, 'igual v02:', igual, json.dumps(son, ensure_ascii=False)[:200], flush=True)
        for r in med:
            print('  ', r['id'], r['dif_frase_db'], 'dB (mediana', r['dif_mediana_db'], ') fondo baja', r['el_fondo_baja_db'],
                  'dB · ganancia', r['ganancia_voz_db'], flush=True)
        if comp:
            print('  ', comp, flush=True)
    jdump(rep, A / 'audio.json')


# =====================================================================================================================
# master · flujo de video del v02 copiado + AAC del WAV nuevo (mismos ajustes que life_v3.sinmusica_de) y control técnico
# =====================================================================================================================
def md5_flujo(mp4, sel):
    return run(['ffmpeg', '-v', 'error', '-i', mp4, '-map', f'0:{sel}', '-c', 'copy', '-f', 'md5', '-']).decode().strip().split('=')[-1]


def atomos(mp4):
    import struct
    b = Path(mp4).read_bytes(); i, out = 0, []
    while i + 8 <= len(b):
        n, t = struct.unpack('>I4s', b[i:i + 8])
        if n == 1:
            n = struct.unpack('>Q', b[i + 8:i + 16])[0]
        out.append(t.decode('latin1')); i += n if n else len(b)
    return out


def tecnico(mp4):
    pj = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-count_frames', '-of', 'json', mp4]))
    v = [s for s in pj['streams'] if s['codec_type'] == 'video'][0]
    a = [s for s in pj['streams'] if s['codec_type'] == 'audio'][0]
    err = subprocess.run(nice(['ffmpeg', '-v', 'error', '-i', mp4, '-f', 'null', '-']), capture_output=True, text=True).stderr
    I, Pk, LRA = medir_ebur(mp4)
    raw = Path(mp4).read_bytes()
    gps = [m.decode('latin1') for m in (b'ISO6709', b'location', b'com.apple.quicktime', b'\xa9xyz') if m in raw]
    return dict(
        video=dict(codec=v['codec_name'], perfil=v.get('profile'), nivel=v.get('level'), pix_fmt=v['pix_fmt'],
                   ancho=v['width'], alto=v['height'], fps=v['r_frame_rate'], cuadros=int(v['nb_read_frames']),
                   duracion=float(v['duration']), rango=v.get('color_range'), matriz=v.get('color_space'),
                   transferencia=v.get('color_transfer'), primarios=v.get('color_primaries')),
        audio=dict(codec=a['codec_name'], perfil=a.get('profile'), hz=int(a['sample_rate']), canales=a['channels'],
                   duracion=float(a['duration']), kbps=round(int(a.get('bit_rate', 0)) / 1000)),
        dif_duracion_audio_video_s=round(float(a['duration']) - float(v['duration']), 4),
        faststart=atomos(mp4).index('moov') < atomos(mp4).index('mdat'), atomos=atomos(mp4),
        decodifica_sin_errores=(err.strip() == ''), errores=err.strip()[:500], marcas_ubicacion=gps,
        etiquetas=pj['format'].get('tags', {}), ebur128=dict(lufs=I, pico_dbtp=Pk, lra=LRA),
        md5_flujo_video=md5_flujo(mp4, 'v'), md5_flujo_audio=md5_flujo(mp4, 'a'), bytes=Path(mp4).stat().st_size,
        sha256=hashlib.sha256(raw).hexdigest())


def decodificar(mp4):
    import numpy as np
    raw = run(['ffmpeg', '-v', 'error', '-i', mp4, '-map', '0:a:0', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'])
    return np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, 2)


def aac_v4_contra_v02(v03, v02):
    """informativo: el AAC decodificado de A v03 contra el de A v02 (las dos codificaciones salen de WAV iguales hasta
    13,10 s; el codificador trabaja por bloques de 1024 muestras)."""
    import numpy as np
    a, b = decodificar(v03), decodificar(v02)
    n = min(len(a), len(b)); d = np.abs(a[:n] - b[:n]).max(1)
    ultimo_igual = int(np.argmax(d > 0)) if (d > 0).any() else n
    return dict(muestras=n, decodificado_igual_hasta_s=round(ultimo_igual / SR, 4),
                dif_max_hasta_13_10=float(d[:int(13.10 * SR)].max()), dif_max_hasta_13_00=float(d[:int(13.00 * SR)].max()))


def alineacion(mp4, wav):
    """el AAC decodificado contra el WAV que lo originó: desfase por correlación (debe ser 0) y diferencia de nivel."""
    import numpy as np
    import soundfile as sf
    d = decodificar(mp4).mean(1)
    w, _ = sf.read(str(wav), dtype='float64', always_2d=True); w = w.mean(1)
    n = min(len(d), len(w)); seg = slice(int(0.5 * SR), n - int(0.5 * SR))
    best = max(range(-240, 241), key=lambda L: float(np.dot(d[seg], np.roll(w, L)[seg])))
    return dict(muestras_decodificadas=len(d), muestras_wav=len(w), desfase_muestras=best,
                diferencia_rms_db=round(rms_db(d[:n] - w[:n]) - rms_db(w[:n]), 1))


def etapa_master():
    solo = sys.argv[2:] or list(MASTERS)
    for vid in solo:
        MAS = T / vid / 'master'; MAS.mkdir(parents=True, exist_ok=True)
        rep = {}
        for et, k, src, nombre, md5_ok in MASTERS[vid]:
            wav = T / vid / 'audio' / f'{vid}_{k}.wav'
            dst = MAS / nombre
            if dst.exists():
                dst.unlink()                          # intermedio de trabajo (la entrega se copia aparte y nunca se pisa)
            assert md5_flujo(src, 'v') == md5_ok, (src, 'el v02 de partida no es el aprobado')
            run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-i', wav, '-map', '0:v:0', '-map', '1:a:0',
                 '-c:v', 'copy', '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
                 '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
                 '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
                 '-shortest', '-movflags', '+faststart', dst])
            t = tecnico(dst)
            t.update(origen_video=str(src), md5_flujo_video_aprobado=md5_ok,
                     flujo_video_igual_al_aprobado=(t['md5_flujo_video'] == md5_ok), wav=str(wav), md5_wav=md5f(wav),
                     alineacion_aac_vs_wav=alineacion(dst, wav))
            if vid == 'v4':
                t['aac_decodificado_contra_A_v02'] = aac_v4_contra_v02(dst, src)
            rep[et] = t
            print(vid, et, t['md5_flujo_video'], t['flujo_video_igual_al_aprobado'], t['md5_flujo_audio'], t['ebur128'],
                  t['video']['cuadros'], t['dif_duracion_audio_video_s'], t['alineacion_aac_vs_wav'], flush=True)
        jdump(rep, MAS / 'control.json')


# =====================================================================================================================
# transcribir · faster-whisper «small», español, SIN initial_prompt (correr con el python de whisper-env)
# =====================================================================================================================
def etapa_transcribir():
    import numpy as np
    from faster_whisper import WhisperModel
    mod = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=2)

    def tr(a):
        segs, _ = mod.transcribe(a.astype(np.float32), language='es', word_timestamps=True, beam_size=5)
        pal = [[w.word.strip(), round(w.start, 2), round(w.end, 2)] for s in segs for w in s.words]
        return ' '.join(p[0] for p in pal), pal

    def pcm(f, t0=None, t1=None):
        cmd = ['ffmpeg', '-v', 'error']
        if t0 is not None:
            cmd += ['-ss', f'{t0:.3f}', '-to', f'{t1:.3f}']
        cmd += ['-i', str(f), '-map', '0:a:0', '-ac', '1', '-ar', '16000', '-f', 's16le', '-']
        return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768

    out = dict(modelo='faster-whisper 1.2.1, small, int8, language=es, beam_size=5, sin initial_prompt',
               aviso='transcripción automática; nadie escuchó el audio', frases={}, masters={})
    if (T / 'transcripcion.json').exists():
        viejo = json.load(open(T / 'transcripcion.json'))
        out['frases'].update(viejo['frases']); out['masters'].update(viejo['masters'])
    for vid, fr in FRASES.items():
        if sys.argv[2:] and vid not in sys.argv[2:]:
            continue
        for fid, tramo, t0, t1, txt, _, _ in fr:
            s, pal = tr(pcm(FR / f'{fid}.wav'))
            out['frases'][fid] = dict(guion=txt, transcripcion=s, palabras=pal)
            print(fid, '|', txt, '→', s, flush=True)
        for et, k, src, nombre, _ in MASTERS[vid]:
            if vid == 'v3' and not et.startswith('36'):
                continue                       # misma pista de audio en los cuatro números: se transcribe el 36
            f = T / vid / 'master' / nombre
            if not f.exists():
                continue
            fila = {}
            for fid, tramo, t0, t1, txt, _, _ in fr:
                a, b = max(0.0, t0 - 0.25), min(NF[vid] / FPS, t1 + 0.25)
                s, pal = tr(pcm(f, a, b))
                fila[fid] = dict(guion=txt, tramo_s=[round(a, 2), round(b, 2)], transcripcion=s,
                                 palabras=[[w, round(x + a, 2), round(y + a, 2)] for w, x, y in pal])
                print(nombre, fid, '|', txt, '→', s, flush=True)
            out['masters'][nombre] = fila
    jdump(out, T / 'transcripcion.json')


# =====================================================================================================================
# entregar · copia en la carpeta de cada video (nunca pisa), relectura 10 s después y evidencia
# =====================================================================================================================
def etapa_entregar():
    solo = sys.argv[2:] or list(MASTERS)
    rep = {}
    for vid in solo:
        ctrl = json.load(open(T / vid / 'master' / 'control.json'))
        for et, k, src, nombre, _ in MASTERS[vid]:
            dst = CARPETA[vid] / nombre
            assert not dst.exists(), f'ya existe {dst}: no se pisa'
            shutil.copyfile(T / vid / 'master' / nombre, dst)
    time.sleep(10)
    for vid in solo:
        ctrl = json.load(open(T / vid / 'master' / 'control.json'))
        for et, k, src, nombre, _ in MASTERS[vid]:
            dst = CARPETA[vid] / nombre
            err = subprocess.run(nice(['ffmpeg', '-v', 'error', '-i', dst, '-f', 'null', '-']), capture_output=True, text=True).stderr
            got = dict(bytes=dst.stat().st_size, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
                       md5_flujo_video=md5_flujo(dst, 'v'), md5_flujo_audio=md5_flujo(dst, 'a'),
                       decodifica_sin_errores=(err.strip() == ''), atomos=atomos(dst))
            got['flujos_iguales_al_master'] = (got['md5_flujo_video'] == ctrl[et]['md5_flujo_video']
                                               and got['md5_flujo_audio'] == ctrl[et]['md5_flujo_audio'])
            rep[str(dst)] = got
            print(dst.name, got['md5_flujo_video'], got['md5_flujo_audio'], got['flujos_iguales_al_master'],
                  got['decodifica_sin_errores'], flush=True)
        ev = CARPETA[vid] / EVID[vid]; ev.mkdir(exist_ok=True)
        for f in (T / vid / 'audio' / 'audio.json', T / vid / 'master' / 'control.json'):
            shutil.copyfile(f, ev / f.name)
        for f in (FR / 'frases.json', FR / 'locucion.json', FR / 'guion_G2.tsv', T / 'transcripcion.json'):
            if f.exists():
                shutil.copyfile(f, ev / f.name)
    jdump(rep, T / f'entrega_{"_".join(solo)}.json')
    for vid in solo:
        shutil.copyfile(T / f'entrega_{"_".join(solo)}.json', CARPETA[vid] / EVID[vid] / 'entrega.json')


if __name__ == '__main__':
    globals()['etapa_' + sys.argv[1]]()
