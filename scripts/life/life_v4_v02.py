#!/usr/bin/env python3
"""Roccé Life · V4 «¿Vuelve?» B · máster v02 (Pedro, 25/11/2026).

Dictamen de Roma sobre v01 (piezas/LIFE_rocce_life/TANDA2/V4_vuelve/04_roma_dictamen_master_v01.md): dos cambios y nada más.
  1. Paso 5: «Dijeron que no va a ser el mismo.» (8 palabras, una cada 3 c, golpe grave en la última) y el paso dura
     hasta 4,10 s; todo lo que sigue se corre +0,20 s (+6 cuadros). Duración 16,10 s (483 cuadros).
  2. El bloque de arriba (rótulo, «Primera derrota.», «¿Vuelve?») baja 4 px para que el temblor no pase de y 270.
Montaje, grado, sonido, textos y placa son los de v01: esta receta importa life_v4 (v01, sin modificarlo) y reemplaza
solo los datos que cambian. Los tiempos fijos del sonido de v01 pasan por S(t) (t ≥ 3,90 → t + 0,20) y los cuadros
por SN(n) (n ≥ 117 → n + 6). El paso 5 sigue la misma toma (7896, caja B3) 6 cuadros más: fuente c48–c80.

Etapas (con nice -n 10 y el python de TRABAJO/venv), intermedios en TRABAJO/life2/v4/v02/:
  planos → grado → textos → audio → master → control → entregar
"""
import copy, hashlib, json, math, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/life')
import video as V           # noqa: E402
import fmt03 as U           # noqa: E402
import life_v2 as L2        # noqa: E402
import life_v4 as M         # noqa: E402

# ---------------------------------------------------------------------------------------------------------------------
# v01 de referencia (solo lectura) y mapas de tiempo
# ---------------------------------------------------------------------------------------------------------------------
T1 = M.T
FRASES1, PASOS1, GRADO1, RAMPA1, CORTES1 = copy.deepcopy(M.FRASES), list(M.PASOS), list(M.GRADO), dict(M.OSCURO_RAMPA), list(M.CORTES_IMG)
NF1, DUR1 = M.NF, M.DUR
NOMBRES1 = dict(M.NOMBRES)
DESDE_N, DN = 117, 6
DESDE_T, DT = 3.90, 0.20
FIN5_1, FIN5_2 = 116, 122           # último cuadro del paso 5 en v01 y en v02


def SN(n):
    return n if n < DESDE_N else n + DN


def S(t):
    return t if t < DESDE_T - 1e-9 else round(t + DT, 6)


def v01_de(n):
    """cuadro de v01 que corresponde al cuadro n de v02 (None en los 6 cuadros nuevos del paso 5: c117–c122)."""
    if n < DESDE_N:
        return n
    if n <= FIN5_2:
        return None
    return n - DN


# ---------------------------------------------------------------------------------------------------------------------
# datos de v02 (se escriben en el módulo de v01: sus funciones leen estos nombres al ejecutarse)
# ---------------------------------------------------------------------------------------------------------------------
T2 = T1 / 'v02'
M.T, M.P, M.A, M.MAS, M.TX, M.MED = T2, T2 / 'planos', T2 / 'audio', T2 / 'master', T2 / 'textos', T2 / 'med'
M.EVID = T2 / 'evidencia_v02'
M.PL = T1 / 'placa'                 # misma placa y firma de v01 (solo lectura)
M.NOMBRES = {'completa': 'ROCCE_LIFE_V4_VUELVE_v02.mp4', 'sinmusica': 'ROCCE_LIFE_V4_VUELVE_SINMUSICA_v02.mp4'}
M.NF = NF1 + DN                     # 483
M.DUR = M.NF / M.FPS                # 16,100 s
M.PASOS = [(p, a if a < DESDE_N else a + DN, FIN5_2 if b == FIN5_1 else SN(b), fn) for p, a, b, fn in PASOS1]
M.GRADO = [(a if a < DESDE_N else a + DN, FIN5_2 if b == FIN5_1 else SN(b), modo, k) for a, b, modo, k in GRADO1]
M.OSCURO_RAMPA = {SN(k): v for k, v in RAMPA1.items()}
M.CORTES_IMG = [SN(c) for c in CORTES1]
M.TEXTO_ULTIMO = SN(416)
M.GOLPES_EXTRA = [(1, 6, 'impacto del gancho (c0 queda quieto para la portada)'), (SN(378), 10, 'drop del reenganche')]
M.PLACA_CUADROS = {k: (SN(a), SN(b)) for k, (a, b) in M.PLACA_CUADROS.items()}
BAJA_PX = 4
E3_V02 = 'Dijeron que no va a ser el mismo.'
FR = copy.deepcopy(FRASES1)
for f in FR:
    if f['id'] in ('rotulo', 'gancho', 'vuelve'):
        f['y'] += BAJA_PX
    elif f['id'] == 'e3':
        f.update(n=(90, FIN5_2), lineas=[['Dijeron', 'que', 'no'], ['va', 'a', 'ser', 'el', 'mismo.']], cad=3, guion=E3_V02)
    elif f['n'][0] >= DESDE_N:
        f['n'] = (f['n'][0] + DN, f['n'][1] + DN)
M.FRASES = FR
M.AMB = [(toma, s0, S(t0), M.DUR if abs(t1 - DUR1) < 1e-9 else S(t1), g, kw) for toma, s0, t0, t1, g, kw in M.AMB]


def plan_planos():
    """el plano 02 de v01 (c42–c116, 75 cuadros) se reutiliza tal cual (mismo archivo: cuadros idénticos a v01) y se agrega
    un plano de 6 cuadros con la misma toma y la misma caja B3, fuente c75–c80 (continúa sin salto la fuente del paso 5)."""
    return [
        dict(id='01_7895_apuesta', m0=0, reusa=True),
        dict(id='02_7896_e1-e3', m0=42, reusa=True),
        dict(id='02b_7896_e3_6c', m0=FIN5_1 + 1, tipo='z', toma='IMG_7896', n0=75, v=['B3'] * DN),
        dict(id='03_7884_p1', m0=SN(117), reusa=True),
        dict(id='04_7896_p2', m0=SN(147), reusa=True),
        dict(id='05_7896_e4-p3', m0=SN(177), reusa=True),
        dict(id='06_8002_e5', m0=SN(222), reusa=True),
        dict(id='07_7896_giro', m0=SN(243), reusa=True),
        dict(id='08_negro', m0=SN(375), reusa=True),
        dict(id='09_7895_color', m0=SN(378), reusa=True),
        dict(id='10_4631_cta', m0=SN(417), reusa=True),
    ]


# ---------------------------------------------------------------------------------------------------------------------
# sonido de v02: las mismas llamadas de v01 con sus tiempos fijos pasados por S(t); los golpes salen de FRASES (v02)
# ---------------------------------------------------------------------------------------------------------------------
SR = M.SR


def sfx_a(m):
    m.impacto(0.0, 0.70); M.campana_ring(m, 0.0)
    m.barrido(0.62, 0.30, 0.12)
    golpes, _ = M.eventos_texto()
    cortado = False
    for n, tipo, _id in golpes:
        t = M.tf(n)
        if t >= S(8.1):
            continue
        if t > S(5.9) and not cortado:
            g = np.ones(m.N); i0, i1 = int(S(5.90) * SR), int(S(5.97) * SR)
            g[i0:i1] = np.linspace(1, 10 ** (-18 / 20), i1 - i0); g[i1:] = 10 ** (-18 / 20)
            m.pistas['fx'] *= g[:, None]; m.log(S(5.90), 'corte seco de la cola del Nocaut (−18 dB)')
            cortado = True
        if tipo == 'grave':
            M.golpe_grave(m, t)
        elif tipo == 'agudo':
            M.golpe_agudo(m, t)
        elif tipo == 'impacto':
            m.impacto(t, 0.80); M.golpe_grave(m, t, 0.55)


def sfx_c(m):
    m.impacto(S(12.60), 0.55)
    golpes, _ = M.eventos_texto()
    for n, tipo, _id in golpes:
        if tipo == 'acento':
            m.toque(M.tf(n), 0.16, 2400)
    m.barrido(S(13.90), 0.30, 0.16); m.toque(S(13.90), 0.14, 2400)


def subida_v01(m, t0, t1, g):
    """subida corrida +0,20 s con el MISMO largo en muestras que en v01. Con S(t1) − S(t0) el redondeo da 8639 en vez de
    8640 (5,22–5,40) y 23040 en vez de 23039 (7,62–8,10): el ruido consume otra cantidad del generador aleatorio común y
    cambian las fases de los colchones entre las dos subidas (medido en la primera pasada del control de v02)."""
    L = int((t1 - t0) * SR)
    a = S(t0)
    b = a + (L + 0.5) / SR
    assert int((b - a) * SR) == L
    m.subida(a, b, g)


def musica_a(m):
    m.subida(0.60, 1.333, 0.20)
    m.pad(1.40, [38, 45, 50, 53], 1.50, .055, 650, a=.05)
    m.pad(3.00, [38, 45, 50], 0.85 + DT, .028, 450, a=.05)            # «la música baja»: el paso 5 dura 0,20 s más
    m.pad(S(3.90), [41, 48, 53, 57, 60], 0.95, .055, 1500, a=.03)
    m.pad(S(4.90), [41, 48, 53, 57], 0.45, .050, 1300, a=.03)
    subida_v01(m, 5.22, 5.40, 0.10)
    m.pad(S(5.40), [41, 48, 53, 57, 60, 64], 0.45, .060, 2000, a=.01)
    m.pad(S(5.90), [38, 45, 50, 53], 0.75, .050, 650, a=.03)
    m.pad(S(6.70), [46, 53, 58, 62], 0.65, .055, 1500, a=.03)
    m.pad(S(7.40), [38, 45, 50, 53], 0.70, .055, 600, a=.03)
    subida_v01(m, 7.62, 8.10, 0.16)
    for t, g in ((1.40, .8), (2.20, .8), (3.00, .45), (3.90, .75), (4.90, .75), (5.90, .8), (6.70, .75), (7.40, .9)):
        M.latido(m, S(t), g, doble=(t != 7.40))
    m.campana(S(5.40), 81, .05)


def musica_b(m):
    m.pad(S(9.50), [38, 45, 50, 52, 57], 2.90, .035, 800, a=.6, r=.3)


def musica_c(m):
    ch = lambda t0, t1, g=.08: [m.charles(round(float(t), 3), g) for t in np.arange(t0, t1 - 1e-6, 0.3)]
    m.bombo(S(12.60), 1.0); m.ocho08(S(12.60), 38, .55, .55, glide_desde=45); m.pad(S(12.60), [50, 53, 57, 62], .55, .06, 1600)
    m.campana(S(12.60), 74, .06); m.campana(S(12.90), 81, .05)
    m.bombo(S(13.20), .85); m.palma(S(13.20)); m.pad(S(13.20), [46, 50, 53, 58], .55, .06, 1600); m.ocho08(S(13.20), 34, .5, .5)
    m.bombo(S(13.80), .85); m.pad(S(13.80), [48, 52, 55, 60], .55, .06, 1600); m.ocho08(S(13.80), 36, .5, .5)
    m.bombo(S(14.40), .9); m.palma(S(14.40)); m.pad(S(14.40), [41, 48, 53, 57, 60], 1.4, .065, 1800, r=.5); m.ocho08(S(14.40), 41, .9, .5)
    m.campana(S(14.40), 77, .06, .9)
    m.bombo(S(15.00), .8); m.palma(S(15.00), .22)
    ch(S(12.60), S(15.31))


def mezcla(con_musica):
    from sonido import Mezcla
    m = Mezcla(M.DUR)
    M.ambientes(m)
    sfx_a(m)
    if con_musica:
        musica_a(m)
    for p in ('mus', 'bombo', 'fx'):
        m.silenciar(p, S(8.10), S(9.50), rampa=0.008)
    M.sfx_b(m)
    if con_musica:
        musica_b(m)
    for p in ('mus', 'bombo', 'fx'):
        m.silenciar(p, S(12.50), S(12.60), rampa=0.03)
    sfx_c(m)
    if con_musica:
        musica_c(m)
    golpes, _ = M.eventos_texto()
    for n, tipo, _id in golpes:
        if tipo in ('grave', 'impacto', 'sub'):
            M.agachar(m, M.tf(n), -4.0, pistas=('amb',))
            if con_musica:
                M.agachar(m, M.tf(n))
    for p in ('amb', 'mus', 'bombo', 'fx'):
        m.fundido(p, S(15.40), M.DUR)
    return m


M.sfx_a, M.sfx_c, M.musica_a, M.musica_b, M.musica_c, M.mezcla = sfx_a, sfx_c, musica_a, musica_b, musica_c, mezcla


# ---------------------------------------------------------------------------------------------------------------------
# etapas
# ---------------------------------------------------------------------------------------------------------------------
def jdump(o, f):
    M.jdump(o, f)


def etapa_planos():
    """solo se renderizan los 6 cuadros nuevos del paso 5; los otros diez planos son los intermedios de v01."""
    M.P.mkdir(parents=True, exist_ok=True)
    reg1 = {r['id']: r for r in json.load(open(T1 / 'planos.json'))['planos']}
    reg = []
    for p in plan_planos():
        if p.get('reusa'):
            r = dict(reg1[p['id']]); r.update(m0=p['m0'], reusado_de_v01=True)
        else:
            out = M.P / f"{p['id']}.mp4"
            z = [M.zc(c) for c in p['v']]
            r = U.plano_z(p['toma'], p['n0'], [a[0] for a in z], [a[1] for a in z], [a[2] for a in z], out, caja=M.FULL,
                          post=p.get('post'))
            r.update(id=p['id'], m0=p['m0'], post=p.get('post'), cajas_guion=sorted({str(c) for c in p['v']}))
        reg.append(r)
        print(r['id'], r['cuadros'], r.get('reusado_de_v01', False), flush=True)
    n = V.unir(reg, T2 / 'v4_base0.mp4')
    assert n == M.NF, n
    jdump(dict(cuadros=n, planos=reg), T2 / 'planos.json')
    print('total', n)


def etapa_grado():
    M.MED.mkdir(parents=True, exist_ok=True)
    M.etapa_grado()


def etapa_textos():
    M.etapa_textos()


def etapa_audio():
    M.etapa_audio()


def etapa_master():
    M.etapa_master()


# ---------------------------------------------------------------------------------------------------------------------
# control v02 (lo que pidió Roma + pruebas de que el resto quedó igual a v01)
# ---------------------------------------------------------------------------------------------------------------------
def md5_decodificado(f):
    out = U.run(M.nice(['ffmpeg', '-v', 'error', '-i', str(f), '-map', '0:v', '-f', 'md5', '-'])).decode()
    return out.strip().split('=')[-1]


def tecnico(f, tr):
    err = subprocess.run(M.nice(['ffmpeg', '-v', 'error', '-i', str(f), '-f', 'null', '-']), capture_output=True, text=True).stderr.strip()
    pj = json.loads(U.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(f)]))
    cuerpo = f.read_bytes()
    gps = [m_.decode() for m_ in (b'ISO6709', b'\xa9xyz', b'com.apple.quicktime.location', b'location') if m_ in cuerpo]
    a = U.audio_np(f)
    niv, v100, sil = U.niveles_tramos(a, tr)
    vs = [s for s in pj['streams'] if s['codec_type'] == 'video'][0]
    au = [s for s in pj['streams'] if s['codec_type'] == 'audio'][0]
    ncuad = int(U.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                       'stream=nb_read_frames', '-of', 'csv=p=0', str(f)]).decode().strip())
    I, Pk, LRA = L2.medir_ebur(f)
    at = L2.atomos(f)
    return pj, dict(
        archivo=str(f), bytes=f.stat().st_size, sha256=hashlib.sha256(cuerpo).hexdigest(),
        md5_flujo_video=U.md5_stream(f, 'v'), md5_flujo_audio=U.md5_stream(f, 'a'), md5_video_decodificado=md5_decodificado(f),
        decodifica_completo=(err == ''), errores_decodificacion=err[:500], cuadros_decodificados=ncuad,
        video=dict(codec=vs['codec_name'], perfil=vs.get('profile'), nivel=vs.get('level'), pix_fmt=vs['pix_fmt'],
                   ancho=vs['width'], alto=vs['height'], fps=vs['r_frame_rate'], cuadros=int(vs['nb_frames']),
                   duracion=float(vs['duration']), rango=vs.get('color_range'), matriz=vs.get('color_space'),
                   transferencia=vs.get('color_transfer'), primarios=vs.get('color_primaries'), bitrate=int(vs.get('bit_rate', 0))),
        audio=dict(codec=au['codec_name'], perfil=au.get('profile'), hz=int(au['sample_rate']), canales=au['channels'],
                   duracion=float(au['duration']), bitrate=int(au.get('bit_rate', 0))),
        duracion_formato=float(pj['format']['duration']), atomos=at, faststart=at.index('moov') < at.index('mdat'),
        marcas_gps_o_ubicacion=gps, sonoridad=dict(lufs_integrado=I, pico_real_dbtp=Pk, lra=LRA),
        niveles_por_tramo=niv, ventanas_100ms_bajo_menos50dbfs=sil, silencio_final_s=L2.silencio_final(a),
        audio_igual_video=abs(float(au['duration']) - float(vs['duration'])) < 1 / M.FPS)


def tramos2():
    out = [(f'paso {p} · {fn}', round(a / M.FPS, 3), round((b + 1) / M.FPS, 3)) for p, a, b, fn in M.PASOS]
    return out + [('solo mar (música cortada)', S(8.10), S(9.50)), ('negro', S(12.50), S(12.60)), ('último 0,5 s', M.DUR - 0.5, M.DUR)]


def md5_cuadros(mp4):
    ys, cs = M.W * M.H, (M.W // 2) * (M.H // 2)
    p = subprocess.Popen(M.nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(mp4), '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-']),
                         stdout=subprocess.PIPE)
    out = []
    while True:
        b = p.stdout.read(ys + 2 * cs)
        if len(b) < ys + 2 * cs:
            break
        out.append(hashlib.md5(b).hexdigest())
    p.stdout.close(); p.wait()
    return out


def igual_a_v01_base():
    """base graduada sin pérdida: md5 de cada cuadro de v02 contra su cuadro de v01."""
    a1, a2 = md5_cuadros(T1 / 'v4_base.mp4'), md5_cuadros(T2 / 'v4_base.mp4')
    distintos, nuevos = [], []
    for n, h in enumerate(a2):
        m_ = v01_de(n)
        if m_ is None:
            nuevos.append(n); continue
        if a1[m_] != h:
            distintos.append(n)
    return dict(cuadros_v01=len(a1), cuadros_v02=len(a2), nuevos_paso5=nuevos, distintos_del_cuadro_v01_correspondiente=distintos)


def igual_a_v01_texto():
    """capa de texto: v02 contra v01 cuadro a cuadro. c0–c41: v01 corrida 4 px hacia abajo; c42–c89 y c123–c422:
    idéntica al cuadro de v01 que corresponde; c90–c122: paso 5 nuevo."""
    from PIL import Image
    r = dict(corridos_4px_identicos=[], identicos=[], distintos=[], nuevos_paso5=[])
    for n in range(0, M.TEXTO_ULTIMO + 1):
        m_ = v01_de(n)
        if m_ is None or 90 <= n <= FIN5_2:
            r['nuevos_paso5'].append(n); continue
        a2 = np.asarray(Image.open(M.TX / 'cuadros' / f'f_{n:04d}.png'))
        a1 = np.asarray(Image.open(T1 / 'textos' / 'cuadros' / f'f_{m_:04d}.png'))
        if n <= 41:
            b = np.zeros_like(a1); b[BAJA_PX:] = a1[:-BAJA_PX]
            (r['corridos_4px_identicos'] if np.array_equal(a2, b) else r['distintos']).append(n)
        else:
            (r['identicos'] if np.array_equal(a2, a1) else r['distintos']).append(n)
    return {k: (v if k == 'distintos' else [v[0], v[-1], len(v)] if v else []) for k, v in r.items()}


def igual_a_v01_audio():
    """mezcla antes del limitador: v02 contra v01 (v01 corrida +0,20 s desde 3,90). Residuo por ventana de 0,5 s en dB
    respecto de la señal de v02."""
    import soundfile as sf
    out = {}
    for k in ('completa', 'sinmusica'):
        x1, sr = sf.read(str(T1 / 'audio' / f'v4_{k}_pre.wav')); x2, _ = sf.read(str(M.A / f'v4_{k}_pre.wav'))
        y1 = np.zeros_like(x2)
        c = int(DESDE_T * sr); d = int(DT * sr)
        y1[:c] = x1[:c]
        y1[c + d:c + d + len(x1) - c] = x1[c:len(x2) - d]
        w = sr // 2; filas = []
        for i in range(0, len(x2) - w + 1, w):
            s2 = np.sqrt((x2[i:i + w] ** 2).mean()) + 1e-12; e = np.sqrt(((x2[i:i + w] - y1[i:i + w]) ** 2).mean()) + 1e-12
            filas.append(dict(t0=round(i / sr, 2), residuo_db=round(float(20 * np.log10(e / s2)), 1)))
        out[k] = dict(ventanas_residuo_mayor_menos40db=[f for f in filas if f['residuo_db'] > -40], por_ventana=filas)
    return out


def igual_a_v01_audio_final():
    """mezcla final (después del limitador y la ganancia a −14 LUFS, antes del AAC): 0–3,40 s contra v01 sin correr y
    6,00 s–fin contra v01 corrida +0,20 s; residuo en dB respecto de la señal de v02 y ganancia aplicada en cada versión."""
    import soundfile as sf
    out = {}
    for k in ('completa', 'sinmusica'):
        x1, sr = sf.read(str(T1 / 'audio' / f'v4_{k}.wav')); x2, _ = sf.read(str(M.A / f'v4_{k}.wav'))
        d = int(DT * sr)
        r = lambda a, b: round(float(20 * np.log10(np.sqrt(((b - a) ** 2).mean() / (b ** 2).mean()) + 1e-12)), 1)
        a, b = x1[:int(3.4 * sr)], x2[:int(3.4 * sr)]
        c1 = x1[int(6 * sr):]; c2 = x2[int(6 * sr) + d:int(6 * sr) + d + len(c1)]; n = min(len(c1), len(c2))
        g1 = json.load(open(T1 / 'audio' / f'v4_{k}_eventos.json'))['ganancia_db']
        g2 = json.load(open(M.A / f'v4_{k}_eventos.json'))['ganancia_db']
        out[k] = dict(residuo_db_0_a_3_40=r(a, b), residuo_db_6_00_a_fin_corrido=r(c1[:n], c2[:n]), ganancia_db_v01=g1, ganancia_db_v02=g2)
    return out


def etapa_audio_final():
    """agrega la comparación de la mezcla final a control_v02.json (sin rehacer el resto del control)."""
    f = M.EVID / 'control_v02.json'
    rep = json.load(open(f))
    rep['igual_a_v01']['audio_final_wav'] = igual_a_v01_audio_final()
    jdump(rep, f)
    print(rep['igual_a_v01']['audio_final_wav'])


def temblor(carpeta):
    """y mínima de lo dibujado (alfa > 8) en cada cuadro de la capa de texto y comparación v01/v02 de c1, c3, c18, c20."""
    from PIL import Image, ImageDraw, ImageFont
    carpeta.mkdir(parents=True, exist_ok=True)
    filas = []
    for n in range(0, M.TEXTO_ULTIMO + 1):
        a = np.asarray(Image.open(M.TX / 'cuadros' / f'f_{n:04d}.png'))[..., 3]
        r = np.nonzero((a > 8).any(1))[0]
        if len(r):
            filas.append(dict(cuadro=n, y_min=int(r.min()), y_max=int(r.max())))
    fuera = [f for f in filas if f['y_min'] < 270 or f['y_max'] > 1130]
    fnt = ImageFont.truetype(M.FONT, 26)
    f1, f2 = T1 / 'master' / NOMBRES1['completa'], M.MAS / M.NOMBRES['completa']
    tiles = []
    for n in (1, 3, 18, 20):
        for etiqueta, f in (('v01', f1), ('v02', f2)):
            im = Image.fromarray(U.leer(f, M.W, M.H, n0=n, n1=n)[0])
            if etiqueta == 'v02':
                im.save(carpeta / f'v02_c{n:03d}.png')
            c = im.crop((0, 200, M.W, 700)); d = ImageDraw.Draw(c)
            d.line([(0, 70), (M.W, 70)], fill=(255, 40, 40), width=1)          # y 270 del cuadro
            al = np.asarray(Image.open((T1 if etiqueta == 'v01' else T2) / 'textos' / 'cuadros' / f'f_{n:04d}.png'))[..., 3]
            ymin = int(np.nonzero((al > 8).any(1))[0].min())
            d.rectangle([0, 0, 520, 36], fill=(0, 0, 0)); d.text((8, 4), f'{etiqueta} c{n} · y mín {ymin} (rojo = y 270)', font=fnt, fill=(255, 255, 0))
            tiles.append(c)
    W_ = Image.new('RGB', (2 * (M.W + 4), 4 * 504), (30, 30, 30))
    for i, t in enumerate(tiles):
        W_.paste(t, ((i % 2) * (M.W + 4), (i // 2) * 504))
    W_.save(carpeta / 'temblor_v01_v02_c1-c3-c18-c20.jpg', quality=90)
    return dict(y_min_global=min(f['y_min'] for f in filas), y_max_global=max(f['y_max'] for f in filas),
                cuadros_fuera_270_1130=fuera, por_cuadro=filas)


def etapa_control():
    import life_v4_control as C          # se importa después de cargar los datos de v02 (lee M al importarse)
    C.FIN_SEP = SN(374)
    EV = M.EVID; EV.mkdir(parents=True, exist_ok=True)
    rep = dict(fecha='2026-11-25', pieza='Roccé Life · V4 «¿Vuelve?» versión B · máster v02',
               cambios=['paso 5: «' + E3_V02 + '» hasta 4,10 s; lo que sigue +0,20 s (16,10 s)',
                        'bloque de arriba 4 px más abajo'], archivos={})
    tr = tramos2()
    for k, nombre in M.NOMBRES.items():
        pj, d = tecnico(M.MAS / nombre, tr)
        json.dump(pj, open(EV / f'ffprobe_{k}.json', 'w'), indent=1)
        rep['archivos'][k] = d
        print(k, d['sonoridad'], d['md5_flujo_video'], d['md5_flujo_audio'], d['md5_video_decodificado'], flush=True)
    rep['video_identico_en_las_dos'] = rep['archivos']['completa']['md5_flujo_video'] == rep['archivos']['sinmusica']['md5_flujo_video']
    f0 = M.MAS / M.NOMBRES['completa']
    U.hoja_contacto(f0, EV / 'hoja_contacto_cada_0.5s.jpg', cada=15, cols=8, ancho=240)
    # paso 5: todos sus cuadros (más 6 antes y 6 después) y cuadros a resolución completa
    p5 = EV / 'paso5'; p5.mkdir(parents=True, exist_ok=True)
    C.hoja_master_todos(f0, p5 / 'paso5_c84-c128_todos.jpg', n0=84, n1=128, cols=9, ancho=240)
    ns = (90, 96, 102, 108, 111, 114, 116, 117, 120, 122, 123)
    sel = '+'.join(f'eq(n\\,{k})' for k in ns)
    U.run(M.nice(['ffmpeg', '-v', 'error', '-y', '-i', str(f0), '-vf', f"select='{sel}'", '-fps_mode', 'vfr', '-q:v', '2',
                  str(p5 / 'tmp_%02d.jpg')]))
    for i, n in enumerate(ns):
        (p5 / f'tmp_{i + 1:02d}.jpg').rename(p5 / f'c{n:03d}.jpg')
    # temblor
    tb = temblor(EV / 'temblor')
    jdump(tb, EV / 'temblor' / 'y_por_cuadro.json')
    rep['temblor'] = {k: v for k, v in tb.items() if k != 'por_cuadro'}
    print('temblor', rep['temblor'], flush=True)
    # textos
    vis = json.load(open(M.TX / 'visible.json')); vis1 = json.load(open(T1 / 'textos' / 'visible.json'))
    dict_roma = (M.PIEZA / '04_roma_dictamen_master_v01.md').read_text(encoding='utf-8')
    e3 = [(int(n), x['lineas']) for n, fr in vis['cuadros'].items() for x in fr if x['id'] == 'e3' and x['completa']]
    otros_distintos = []
    for n, fr in vis['cuadros'].items():
        n = int(n); m_ = v01_de(n)
        if m_ is None or 90 <= n <= FIN5_2:
            continue
        a = [x for x in fr if x['id'] != 'e3']; b = [x for x in vis1['cuadros'][str(m_)] if x['id'] != 'e3']
        if a != b:
            otros_distintos.append(n)
    rep['textos'] = dict(e3_texto=E3_V02, e3_en_dictamen_de_roma=('«' + E3_V02 + '»') in dict_roma,
                         e3_completo_desde=min(n for n, _ in e3), e3_completo_hasta=max(n for n, _ in e3),
                         e3_renglones=e3[0][1], e3_igual=(' '.join(e3[0][1]) == E3_V02),
                         e3_palabras=[(w, a) for w, a, *_ in M.palabras([f for f in M.FRASES if f['id'] == 'e3'][0])],
                         resto_igual_a_v01_cuadro_a_cuadro=(not otros_distintos), cuadros_distintos=otros_distintos)
    shutil.copy2(M.TX / 'visible.json', EV / 'visible_por_cuadro_v02.json')
    print('textos', rep['textos'], flush=True)
    # igual a v01
    rep['igual_a_v01'] = dict(base_graduada=igual_a_v01_base(), capa_de_texto=igual_a_v01_texto())
    au = igual_a_v01_audio()
    jdump(au, EV / 'audio_v02_contra_v01.json')
    rep['igual_a_v01']['audio'] = {k: v['ventanas_residuo_mayor_menos40db'] for k, v in au.items()}
    rep['igual_a_v01']['audio_final_wav'] = igual_a_v01_audio_final()
    print('igual a v01', json.dumps(rep['igual_a_v01'], ensure_ascii=False)[:1500], flush=True)
    # separación (todos los cuadros 0–380) y hoja del plano que cambió
    seg = json.load(open(T1 / 'med' / 'seguimiento.json'))
    d1 = json.load(open(T1 / 'evidencia_v01' / 'separacion' / 'deteccion_directa_blanca_8002.json'))
    directo = {'IMG_8002': {int(k): v for k, v in d1['IMG_8002'].items()}}
    mapa = C.mapa_cuadros()
    sep = C.separacion(seg, mapa, directo)
    jdump(sep, EV / 'separacion_por_cuadro_v02.json')
    pp = {}
    for f in sep:
        if f.get('negro'):
            continue
        p = pp.setdefault(f['plano'], dict(cuadros=[f['cuadro'], f['cuadro']], min_px_master=1e9))
        p['cuadros'][1] = f['cuadro']; p['min_px_master'] = min(p['min_px_master'], f['minimo_peor_caso_px_master'])
    mapa2 = {n: (v if v['plano'] in ('02_7896_e1-e3', '02b_7896_e3_6c') else dict(v, toma=None)) for n, v in mapa.items()}
    C.hojas_separacion(seg, mapa2, EV / 'separacion', directo)
    rep['separacion'] = dict(por_plano=pp, todos_positivos=all(f.get('negro') or f['minimo_peor_caso_px_master'] > 0 for f in sep),
                             cuadros_nuevos_paso5=[dict(cuadro=f['cuadro'], fuente=f['fuente'], ventana=f['ventana'],
                                                        hueco_px=f['minimo_peor_caso_px_master']) for f in sep if 117 <= f['cuadro'] <= 122])
    print('separación', json.dumps(rep['separacion'], ensure_ascii=False)[:1200], flush=True)
    # logo y B/N cuadro a cuadro
    filas, ficha = C.analisis_cuadros(f0)
    jdump(filas, EV / 'por_cuadro_v02.json')
    rep['logo'] = dict(ncc_max_0_380=max(filas[n]['logo_ncc_max'] for n in range(0, SN(374) + 1)),
                       ncc_firma=[min(filas[n]['logo_ncc_max'] for n in range(M.PLACA_CUADROS['firma'][0], M.NF)),
                                  max(filas[n]['logo_ncc_max'] for n in range(M.PLACA_CUADROS['firma'][0], M.NF))])
    rep['bn_croma_max_0_380'] = max(filas[n]['croma_fuera_texto_max'] for n in range(0, SN(374) + 1))
    # golpes (el de e3 pasa a 3,70 s)
    import soundfile as sf
    fx, sr = sf.read(str(M.A / 'v4_completa_fx.wav'))
    mp4 = U.audio_np(f0).astype(np.float64)
    gl = []
    for n, tipo, fid in M.eventos_texto()[0]:
        ev = dict(cuadro=n, t=round(M.tf(n), 3), tipo=tipo, frase=fid)
        gl.append(dict(ev, pista_fx=C._salto(fx, sr, ev['t'], tipo), mp4_en_banda=C._banda(mp4, ev)))
    jdump(gl, EV / 'golpes_v02.json')
    rep['golpes'] = [(g['cuadro'], g['tipo'], g['pista_fx']['desvio_ms'], g['mp4_en_banda'] and g['mp4_en_banda']['salto_db']) for g in gl]
    print('golpes', rep['golpes'], flush=True)
    for k in ('completa', 'sinmusica'):
        shutil.copy2(M.A / f'v4_{k}_eventos.json', EV / f'eventos_audio_{k}.json')
    shutil.copy2(T2 / 'planos.json', EV / 'planos_v02.json')
    jdump(rep, EV / 'control_v02.json')
    print('control ok')


def etapa_entregar():
    res = {}
    for nombre in M.NOMBRES.values():
        for dst in (M.EXP / nombre, M.PIEZA / nombre):
            if dst.exists():
                raise RuntimeError(f'{dst} ya existe: no se sobrescribe')
    ev = M.PIEZA / M.EVID.name
    if ev.exists():
        raise RuntimeError(f'{ev} ya existe')
    for nombre in M.NOMBRES.values():
        for dst in (M.EXP / nombre, M.PIEZA / nombre):
            shutil.copyfile(M.MAS / nombre, dst)
    shutil.copytree(M.EVID, ev)
    time.sleep(8)
    for nombre in M.NOMBRES.values():
        src = M.MAS / nombre
        ref = (U.md5_stream(src, 'v'), U.md5_stream(src, 'a'))
        for dst in (M.EXP / nombre, M.PIEZA / nombre):
            err = subprocess.run(M.nice(['ffmpeg', '-v', 'error', '-i', str(dst), '-f', 'null', '-']), capture_output=True, text=True).stderr.strip()
            got = (U.md5_stream(dst, 'v'), U.md5_stream(dst, 'a'))
            res[str(dst)] = dict(bytes=dst.stat().st_size, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(), md5_flujo_video=got[0],
                                 md5_flujo_audio=got[1], flujos_iguales=(got == ref), decodifica_completo=(err == ''),
                                 bytes_agregados=dst.stat().st_size - src.stat().st_size)
            print(dst, res[str(dst)], flush=True)
    from PIL import Image
    dif, pix = [], 0
    for f in M.EVID.rglob('*'):
        if not f.is_file():
            continue
        g = ev / f.relative_to(M.EVID)
        if hashlib.md5(f.read_bytes()).hexdigest() == hashlib.md5(g.read_bytes()).hexdigest():
            continue
        if f.suffix.lower() in ('.jpg', '.png') and np.array_equal(np.asarray(Image.open(f)), np.asarray(Image.open(g))):
            pix += 1
        else:
            dif.append(str(f.relative_to(M.EVID)))
    res['evidencia'] = dict(carpeta=str(ev), archivos=sum(1 for _ in ev.rglob('*') if _.is_file()),
                            imagenes_con_bloque_agregado_y_pixeles_identicos=pix, distintos=dif)
    print('evidencia', res['evidencia'])
    jdump(res, T2 / 'entrega_v02.json')
    shutil.copy2(T2 / 'entrega_v02.json', ev / 'entrega_v02.json')


if __name__ == '__main__':
    globals()['etapa_' + sys.argv[1]]()
