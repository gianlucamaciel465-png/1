#!/usr/bin/env python3
"""MARCA_momento · LIB-1 «Sin un gol» · receta del máster v01 (Pedro, 25/11/2026).

Guion: piezas/MARCA_momento/08_fede_guiones_LIB_v01.md (LIB-1 v01) + 09_roma_aprobacion_LIB.md (condiciones y agregado)
+ 10_fede_guiones_ronda2_v02.md «Cambios en LIB» (B12 = «58 AÑOS DESPUÉS: / MISMO RIVAL, MISMA CANCHA.»).
Etapas (python lib1.py <etapa>, python de TRABAJO/venv, con nice): planos → capas → audio → voz → mezcla → master → control\n(sin voz_LIB1.tsv se salta «voz» y sale una premezcla sin locución, con _v00_PREMEZCLA_SINLOCUCION en el nombre)
Intermedios en TRABAJO/momento/lib1/. Clips de @libertadores en TRABAJO/momento/clips/tt (fuera de git).
Sin servicios externos ni créditos. Sin commit (lo hace Roma). Ningún MP4/clip/audio va al repo.
"""
import json, os, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import lib_comun as L     # noqa: E402
from lib_comun import V, C, W, H, SR  # noqa: E402

T = L.R / 'TRABAJO/momento/lib1'
PL, CAPA, A, MAS = T / 'planos', T / 'capa', T / 'audio', T / 'master'
NF = 815
DUR = NF / 30
NOMBRES = {'completa': 'ROCCE_LIB1_SIN_UN_GOL_v01.mp4', 'sinmusica': 'ROCCE_LIB1_SIN_UN_GOL_SINMUSICA_v01.mp4'}

# T13, cuadro 915 (15,265 s): la placa «1968 / Club Estudiantes de La Plata / ARGENTINA» nítida; el resto se desenfoca
# para que ningún otro año (1960, 1961, 1969, 1976, 1977…) se lea debajo de «1968.». Marca CONMEBOL intacta encima.
N_1968 = 915
CAJA_1968 = (224, 476, 582, 640)
MARCA_T13 = (66, 330, 258, 402)

# (id, f0, n, fuente, modo, t0/tramo) · f0 = primer cuadro del máster
PLANOS = [
    ('B1', 0, 78, 'T4', '1:1', 4.000),
    ('B2', 78, 63, 'T8', '1:1', 5.000),
    ('B3', 141, 80, 'T2', 'real', 15.547),      # voz «De dar lucha con diez jugadores en Maracaná,» (corte por nivel)
    ('B4', 221, 47, 'T7', 'cuadro', 3.900),
    ('B5', 268, 61, 'T1', 'cuadro', 2.252),
    ('B6', 329, 38, 'T2', 'real', 22.955),      # voz «todavía no ganamos nada,»
    ('B7', 367, 48, 'T13', 'descarte', 1170 / (60000 / 1001)),   # túnel (corte del original en 19,236)
    ('B8', 415, 47, 'T13', 'descarte', 1267 / (60000 / 1001)),   # FPV; B7/B8 sobre el corte túnel→cancha (21,121)
    ('B9', 462, 38, 'T1', 'cuadro', 17.000),
    ('B10', 500, 38, 'T3', 'cuadro', 11.000),
    ('B11a', 538, 29, 'T13', 'descarte', 372 / (60000 / 1001)),  # copa en el Centenario (corte del original 6,190)
    ('B11b', 567, 30, 'T13', 'foco1968', None),                  # cuadro 915 congelado con foco en la placa de 1968
    ('B12', 597, 89, 'T13', 'descarte', 34.000),
    ('B13', 686, 69, 'IMG_7895', 'img', (0.000, 2.300, None)),
    ('B14', 755, 60, 'IMG_7896', 'img', (4.150, 6.150, (52, 269, 1862, 3310))),  # recorte 1,16× (x 2,4 %, y 7 %)
]
assert sum(p[2] for p in PLANOS) == NF and all(PLANOS[i][1] + PLANOS[i][2] == PLANOS[i + 1][1] for i in range(len(PLANOS) - 1))
CORTES = [p[1] for p in PLANOS[1:]]


def etapa_planos():
    PL.mkdir(parents=True, exist_ok=True)
    fichas = []
    png = T / 't13_n915.png'; L.cuadro_tt('T13', N_1968, png)
    L.foco_placa(png, T / 't13_n915_foco.png', CAJA_1968, MARCA_T13)
    for pid, f0, n, src, modo, arg in PLANOS:
        out = PL / f'{pid}.mp4'
        if modo == 'img':
            d0, d1, caja = arg
            fi = V.plano(src, d0, d1, out, caja=caja)
            fi['cuadros'] = n
            assert L.nframes(out) == n, pid
        elif modo == 'foco1968':
            fi = L.png_a_plano(T / 't13_n915_foco.png', n, out)
            fi.update(clip='T13', cuadro_fuente=N_1968, t_fuente=round(N_1968 / (60000 / 1001), 3))
        else:
            fi = L.plano_tt(src, modo, arg, n, out)
        fi.update(id=pid, f0=f0, f1=f0 + n - 1)
        fichas.append(fi); print(pid, n, flush=True)
    L.unir(fichas, T / 'imagen.mp4')
    json.dump(fichas, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)


# ------------------------------------------------------------------------------------------------ textos
# Textos en pantalla como parámetro (Roma, 25/11: con locución algunos pueden achicarse a palabras clave).
# lib1_textos.json: {"nombre_de_capa": "texto nuevo" | null (se saca) | {"texto": ..., "f0": ..., "f1": ...}}.
# Los nombres son los de capas(); sin archivo quedan los textos aprobados del guion.
TXT_PARAM = Path(__file__).parent / 'lib1_textos.json'
TXT = json.load(open(TXT_PARAM)) if TXT_PARAM.exists() else {}


def tx(nombre, defecto):
    v = TXT.get(nombre, defecto)
    if isinstance(v, dict):
        v = v.get('texto', defecto)
    return v or defecto


def aplicar_parametros(K):
    """Saca las capas puestas en null y corre f0/f1 de las que traen tiempos nuevos."""
    out = []
    for k in K:
        v = TXT.get(k['nombre'], '')
        if v is None:
            continue
        if isinstance(v, dict):
            k = dict(k, f0=v.get('f0', k['f0']), f1=v.get('f1', k['f1']))
        out.append(k)
    return out


def capas():
    K = []
    # B1 · APUESTA
    c1 = L.caja_fit(tx('hook1', 'ESTUDIANTES NO HIZO\nUN GOL EN LA SEMI.'), tema='blanca')
    K.append(L.capa(c1, 0, 78, 470, pop=True, nombre='hook1'))
    c2 = L.caja_fit(tx('hook2', 'Y EL SÁBADO\nJUEGA LA FINAL.'), tema='negra')
    K.append(L.capa(c2, 27, 78, 470 + c1.height + 14, pop=True, nombre='hook2'))
    d1 = L.dato(tx('dato_f45', 'Copa Libertadores ·\ncontra Palmeiras ·\nsábado 17:00'))
    K.append(L.capa(d1, 45, 78, 1540 - d1.height, cx=490, nombre='dato_f45'))
    # B2 · EN CONTRA
    p1 = L.placa_fit(tx('ida', 'IDA: 0-0.')); f = C.fuente('extrabold', 96); asc, desc = f.getmetrics()
    K.append(L.capa(p1, 78, 141, 470, nombre='ida'))
    K.append(L.capa(L.placa_fit(tx('vuelta', 'VUELTA: 0-0.')), 116, 141, 470 + round((asc + desc) * 1.05), nombre='vuelta'))
    # B3 · EN CONTRA (sube)
    p3 = L.placa_fit(tx('con_diez', 'CON DIEZ'))
    K.append(L.capa(p3, 141, 221, 470, nombre='con_diez'))
    K.append(L.capa(L.dato(tx('dato_b3', 'desde el arranque\ndel segundo tiempo.')), 141, 221, 470 + p3.height - 20, nombre='dato_b3'))
    # B4 · A FAVOR
    K.append(L.capa(L.placa_fit(tx('tapa', 'LA TAPA MUSLERA.')), 241, 268, 470, nombre='tapa'))
    # B5 · A FAVOR + respuesta
    K.append(L.capa(L.placa_fit(tx('penales', 'PENALES.')), 268, 298, 470, nombre='penales'))
    K.append(L.capa(L.placa_fit(tx('ataja', 'MUSLERA ATAJA TRES.')), 298, 329, 470, nombre='ataja'))
    # B6 · reenganche: sin texto nuestro (queda el subtítulo CONMEBOL)
    # B7 · A FAVOR
    p7 = L.placa_fit(tx('centenario', 'EL SÁBADO,\nEN EL CENTENARIO.'))
    K.append(L.capa(p7, 367, 415, 450, nombre='centenario'))
    K.append(L.capa(L.dato(tx('dato_b7', 'la cancha de la selección\nde su arquero.')), 367, 415, 450 + p7.height - 20, nombre='dato_b7'))
    # B8 · EN CONTRA
    K.append(L.capa(L.placa_fit(tx('palmeiras', 'PALMEIRAS:\nSEGUNDA FINAL SEGUIDA.')), 415, 462, 450, nombre='palmeiras'))
    # B9 · A FAVOR
    K.append(L.capa(L.placa_fit(tx('cinco', 'ESTUDIANTES:\nCINCO FINALES, CUATRO COPAS.')), 462, 500, 450, nombre='cinco'))
    # B10 · EN CONTRA
    K.append(L.capa(L.placa_fit(tx('2009', 'LA ÚLTIMA, EN 2009.')), 500, 538, 470, nombre='2009'))
    # B11 · GIRO (la placa de 1968 ocupa y 476–640 en B11b: los textos van debajo, sin taparla)
    q = L.caja_fit(tx('primera_a', '¿Y LA PRIMERA?'), tema='blanca')
    K.append(L.capa(q, 538, 567, 470, pop=True, nombre='primera_a'))
    K.append(L.capa(q, 567, 597, 690, cx=490, nombre='primera_b'))
    p68 = L.placa_fit(tx('1968', '1968.'))
    K.append(L.capa(p68, 567, 597, 690 + q.height - 10, cx=490, nombre='1968'))
    K.append(L.capa(L.caja_fit(tx('contra', 'CONTRA PALMEIRAS.'), tema='blanca', maxw=860), 576, 597, 690 + q.height - 10 + p68.height - 20,
                    cx=490, pop=True, nombre='contra'))
    # B12 · GRAN PREGUNTA
    K.append(L.capa(L.placa_fit(tx('58', '58 AÑOS DESPUÉS:\nMISMO RIVAL, MISMA CANCHA.')), 597, 686, 450, nombre='58'))
    K.append(L.capa(L.caja_fit(tx('pregunta', '¿VUELVE A GRABAR\nSU NOMBRE?'), tema='blanca', maxw=860), 633, 686, 1180, cx=490, pop=True,
                    nombre='pregunta'))
    # B13 · REENGANCHE 2 + producto
    K.append(L.capa(L.caja_fit(tx('editamos', 'YA EDITAMOS\nLOS DOS FINALES.'), tema='blanca'), 686, 755, 300, pop=True, nombre='editamos'))
    rb = C.caja('GIVE HISTORY\nYOUR NAME.', 52, tema='negra')
    rn = C.caja('so f★cking\nclose.', 52, tema='negra')
    K.append(L.rotulo(rb, 704, 755, 600, 290, (470, 895), nombre='rot_blanca'))
    K.append(L.rotulo(rn, 704, 755, 600, 800, (675, 893), nombre='rot_negra'))
    K.append(L.capa(L.caja_fit(tx('borra', 'EL SÁBADO SE BORRA UNO.'), tema='negra', maxw=860), 731, 755, 1330, cx=490, pop=True,
                    nombre='borra'))
    # B14 · CTA (rótulos reubicados sobre IMG_7896)
    K.append(L.rotulo(rb, 755, NF, 640, 270, PUNTA_7896['blanca'], pop=False, nombre='rot_blanca2'))
    K.append(L.rotulo(rn, 755, NF, 640, 790, PUNTA_7896['negra'], pop=False, nombre='rot_negra2'))
    K.append(L.capa(L.caja_fit(tx('cta', 'COMENTÁ CUÁL QUEDA.'), tema='blanca', maxw=860), 755, NF, 1330, cx=490, pop=True, nombre='cta'))
    return K


PUNTA_7896 = {'blanca': (228, 1000), 'negra': (650, 1100)}   # medidos sobre B14 en c0, c30 y c59; la blanca baja por la izquierda para no cruzar «ROCCE»


def etapa_capas():
    K = aplicar_parametros(capas())
    malas = [(k['nombre'], k['caja']) for k in K if C.fuera_de_zona([k['caja']])]
    L.rasterizar(K, NF, CAPA)
    json.dump([dict(nombre=k['nombre'], f0=k['f0'], f1=k['f1'] - 1, caja=k['caja'], pop=k['pop']) for k in K],
              open(T / 'capas.json', 'w'), ensure_ascii=False, indent=1)
    print('fuera de zona:', malas)


# ------------------------------------------------------------------------------------------------ sonido
GOLPES = [('seco', 78), ('seco', 116), ('seco', 141), ('grave', 241), ('seco', 268), ('grave', 298), ('grave', 367),
          ('seco', 415), ('grave', 462), ('seco', 500), ('fuerte', 567), ('grave', 686)]
VOZ = [(141, 221), (329, 367)]


def stems():
    N = int(round(DUR * SR))
    amb = np.zeros((N, 2), np.float32); voz = np.zeros((N, 2), np.float32)
    fps23 = 24000 / 1001
    tempo = 30 / fps23
    for pid, f0, n, src, modo, arg in PLANOS:
        t0, d = f0 / 30, n / 30
        if modo in ('1:1', 'cuadro'):
            a = L.leer_audio(L.clip(src), arg, d, tempo=(tempo if modo == 'cuadro' else 1.0))
            a = a * 10 ** ((-28 - L.rms_db(a)) / 20)
            if pid == 'B9':
                a *= 10 ** (-4 / 20)          # «ambiente T1 bajo»
            L.put(amb, L.fades(a), t0)
        elif modo == 'real':          # voz de Muslera (T2) a velocidad real
            a = L.leer_audio(L.clip(src), arg, d)
            a = a * 10 ** ((-19 - L.rms_db(a)) / 20)
            L.put(voz, L.fades(a, 0.012, 0.030), t0)
        elif pid in ('B13', 'B14'):
            d0 = arg[0]
            a = L.leer_audio(L.R / f'ORIGINALES/{src}.mov', d0, d)
            a = a * 10 ** ((-25 - L.rms_db(a)) / 20)
            L.put(amb, L.fades(a, 0.004, 0.02), t0)
        else:                          # T13 sin audio propio: aire de estadio vacío
            db = -50 if pid in ('B11a',) else -42
            L.put(amb, L.fades(L.aire(d, db), 0.02, 0.02), t0)
    fx = np.zeros((N, 2), np.float32)
    for tipo, f in GOLPES:
        t = f / 30
        if tipo == 'seco':
            L.put(fx, L.seco(-9), t)
        elif tipo == 'grave':
            L.put(fx, L.grave(-6), t)
        else:
            L.put(fx, L.grave(-3, dec=0.6), t); L.put(fx, L.seco(-14), t)
            L.put(fx, L.subida(1.0, -20), t + 0.02)
    mus = L.musica(DUR, [(0, 538 / 30, 'pulso'), (538 / 30, 567 / 30, 'silencio'), (567 / 30, 597 / 30, 'silencio'),
                         (597 / 30, 686 / 30, 'lento'), (686 / 30, DUR + 1, 'pleno')])
    mus *= 10 ** ((-24 - L.rms_db(mus[:int(538 / 30 * SR)])) / 20)
    nf = int(0.4 * SR); mus[-nf:] *= np.linspace(1, 0, nf)[:, None]
    # fundido final ≤ 0,4 s también en ambiente (la ola) para no cortar seco
    amb[-nf:] *= np.linspace(1, 0.15, nf)[:, None]
    return dict(amb=amb, voz=voz, fx=fx, mus=mus)


def etapa_audio():
    """Stems a WAV (ambiente, golpes, música sin bajar, voz de Muslera). La mezcla va en la etapa `mezcla`."""
    A.mkdir(parents=True, exist_ok=True)
    s = stems()
    for k, v in s.items():
        L.escribir_wav_f32(v, A / f'stem_{k}.wav')


# Locución Firme 04 (guion 12 de Fede, aprobado por Roma el 25/11). Archivos en scripts/momento/:
#   voz_LIB1.tsv            id<TAB>texto a sintetizar (con las alternativas «b»)
#   voz_LIB1_ubicacion.tsv  plan: id<TAB>entra<TAB>tope<TAB>alternativa → voz_mezcla.resolver con la duración real
# La voz calla en la voz de Muslera (B3 f141–220, B6 f329–366), en el giro (f565–605) y ±3 cuadros de cada golpe.
VOZ_TSV = Path(__file__).parent / 'voz_LIB1.tsv'
VOZ_UBIC = Path(__file__).parent / 'voz_LIB1_ubicacion.tsv'
LOC = T / 'locucion'
PROHIB = [(141, 221, 'voz de Muslera B3', 3), (329, 367, 'voz de Muslera B6', 3), (565, 606, 'giro «1968.» / «CONTRA PALMEIRAS.»')]
# Topes duros autorizados por Roma (14) para L1_04 y para probar L1_05 entera; el resto sigue con el tope del guion.
# TOPES=guion | duros | lista separada por comas (variable de entorno) para otra decisión.
_t = os.environ.get('TOPES', 'L1_04,L1_05')
TOPES = _t if _t in ('guion', 'duros') else set(_t.split(','))
# Cola del grave de f367 (14): mientras suena la frase de B7 se baja solo la cola, desde la entrada de la frase; el golpe
# no se mueve y su ataque (los primeros 100 ms) no se toca. La frase entra ≥ 3 cuadros (100 ms) después del golpe.
# El mismo criterio se aplica al grave de f462 (B9): la frase que entra ahí («Perdió una.», respaldo de L1_07 del 14)
# arranca 4 cuadros después y quedaba a 9,7 dB del fondo. Cuando Roma lo decidió, L1_07 estaba bloqueada.
COLAS = {367: -24.0, 462: -24.0}
DUR_GRAVE = 0.9
# L1_10 depende de que se lea la inscripción en B11b: se lee en el cuadro 585 a resolución completa
# (control/inscripcion_1968_f585_recorte.png) → va L1_10. Si no se leyera: FORZAR = {'L1_10': 'L1_10b'}.
FORZAR = {}


def etapa_voz():
    import voz_mezcla as VM
    tsv = Path(os.environ.get('VOZ_TSV', VOZ_TSV)); plan = Path(os.environ.get('VOZ_UBIC', VOZ_UBIC))
    VM.generar(tsv, LOC, palabras=os.environ.get('PALABRAS', '1') == '1')
    dec, av1 = VM.resolver(LOC, plan, [f for _, f in GOLPES], PROHIB, salida=LOC / 'ubicacion_resuelta.tsv', forzar=FORZAR,
                           topes=TOPES, nf=NF)
    solo = [d['id'] for d in dec if not d.get('bloqueada')]
    a, frases, av2 = VM.pista(LOC, LOC / 'ubicacion_resuelta.tsv', NF, prohibidas=PROHIB, solo=solo)
    VM.escribir(a, A / 'stem_loc.wav')
    json.dump(dict(guion=str(tsv), plan=str(plan), topes=sorted(TOPES) if isinstance(TOPES, set) else TOPES, ubicacion=str(LOC / 'ubicacion_resuelta.tsv'), elegidas=solo,
                   decisiones=dec, frases=frases, avisos=av1 + av2), open(LOC / 'pista.json', 'w'), ensure_ascii=False, indent=1)
    for d in dec:
        print(f"{d['plan']:7s} {d['id']:7s} guion f{d['entra_guion']} → f{d['f0']}–{d['fin_f']} (tope f{d['tope']}, "
              f"{d['dur_s']} s) {d['accion']}")
    bloq = [d['plan'] for d in dec if d.get('bloqueada')]
    if bloq:
        print('CORTE PARCIAL: sin', bloq)
    print('avisos:', av1 + av2 or 'ninguno')


def con_locucion():
    return (A / 'stem_loc.wav').exists()


def etapa_mezcla():
    """Dos mezclas (completa y sin música) con sidechain manejado por la voz (locución + Muslera), a −14 LUFS."""
    import voz_mezcla as VM
    loc = A / 'stem_loc.wav'
    if not loc.exists():                       # premezcla sin locución: pista de voz muda del largo del video
        VM.escribir(np.zeros((int(round(DUR * SR)), 2), np.float32), A / 'stem_loc_vacia.wav')
        loc = A / 'stem_loc_vacia.wav'
    st = dict(loc=loc, voz=A / 'stem_voz.wav', mus=A / 'stem_mus.wav', amb=A / 'stem_amb.wav', fx=A / 'stem_fx.wav')
    tramos = [('Muslera B3', 141 / 30, 221 / 30), ('Muslera B6', 329 / 30, 367 / 30)]
    colas = []
    if con_locucion():
        for g, db in COLAS.items():
            for f in json.load(open(LOC / 'pista.json'))['frases']:
                if g / 30 + 0.1 <= f['t0'] < g / 30 + DUR_GRAVE:
                    colas.append(dict(golpe=g, frase=f['id'], desde_s=f['t0'], hasta_s=round(g / 30 + DUR_GRAVE, 3), db=db))
        if colas:
            st['fx'] = VM.escalar_tramos(st['fx'], [(c['desde_s'], c['hasta_s'], c['db']) for c in colas],
                                         A / 'stem_fx_colas.wav', fundido=0.015)
    if con_locucion():
        for f in json.load(open(LOC / 'pista.json'))['frases']:
            tramos.append((f['id'], f['t0'], f['t1']))
    med = {}
    pj = json.load(open(LOC / 'pista.json')) if con_locucion() else {}
    for nombre, niv in (('completa', {}), ('sinmusica', {'mus_db': -120})):
        med[nombre] = VM.mezclar(st, DUR, A / f'mezcla_{nombre}.wav', niveles=niv, tramos_voz=tramos,
                                 auto_claves=(('amb_db',) if nombre == 'sinmusica' else None))
        ids = [t[0] for t in tramos[2:]]
        gl, gm = {}, {}                        # corrección por frase (locución) y por tramo (voz de Muslera), ±4 dB
        for _ in range(2):                     # dos vueltas: bajar una voz cambia cuánto baja el fondo (sidechain)
            dl = VM.ganancias_frases(med[nombre], ids) if con_locucion() else {}
            dm = VM.ganancias_frases(med[nombre], ['Muslera B3', 'Muslera B6'], fondo_min=-40.0)
            nl = {k: round(max(-4.0, min(4.0, gl.get(k, 0) + v)), 1) for k, v in dl.items()}
            nm = {k: round(max(-4.0, min(4.0, gm.get(k, 0) + v)), 1) for k, v in dm.items()}
            if all(gl.get(k) == v for k, v in nl.items()) and all(gm.get(k) == v for k, v in nm.items()):
                break
            gl.update(nl); gm.update(nm)
            st2 = dict(st)
            if gl:
                a, _, _ = VM.pista(LOC, Path(pj['ubicacion']), NF, prohibidas=PROHIB, ganancias=gl, solo=pj['elegidas'])
                st2['loc'] = VM.escribir(a, A / f'stem_loc_{nombre}.wav')
            if gm:                             # nivel de la voz de Muslera por tramo (el contenido y el corte no cambian)
                st2['voz'] = VM.escalar_tramos(st['voz'], [(t0, t1, gm[n]) for n, t0, t1 in tramos[:2] if n in gm],
                                               A / f'stem_voz_{nombre}.wav')
            niv = med[nombre]['niveles_fondo_db']
            med[nombre] = VM.mezclar(st2, DUR, A / f'mezcla_{nombre}.wav', niveles=niv, tramos_voz=tramos, auto=False)
            med[nombre]['ganancia_por_frase_db'] = {**gl, **gm}
        print(nombre, med[nombre]['sonoridad'], flush=True)
        for t in med[nombre]['voz_vs_fondo']:
            print('  ', t['tramo'], t['voz_db'], t['fondo_db'], t['diferencia_db'], 'ok' if t['ok'] else 'FUERA DE 10–15')
    med['locucion'] = 'Firme 04' if con_locucion() else 'sin locución (premezcla)'
    med['colas_bajadas'] = colas
    json.dump(med, open(A / 'medidas.json', 'w'), ensure_ascii=False, indent=1)


def parcial():
    p = LOC / 'pista.json'
    return con_locucion() and p.exists() and any(d.get('bloqueada') for d in json.load(open(p))['decisiones'])


def nombre_salida(nombre):
    n = NOMBRES[nombre]
    if not con_locucion():
        return n.replace('_v01.mp4', '_v00_PREMEZCLA_SINLOCUCION.mp4')
    return n.replace('_v01.mp4', '_v01_PARCIAL.mp4') if parcial() else n


def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    for nombre in ('completa', 'sinmusica'):
        L.master(T / 'imagen.mp4', A / f'mezcla_{nombre}.wav', CAPA, MAS / nombre_salida(nombre))
        print(MAS / nombre_salida(nombre), flush=True)


# ------------------------------------------------------------------------------------------------ control
ZONAS_360 = [0, 27, 45, 77, 100, 116, 140, 160, 200, 230, 250, 280, 310, 340, 380, 430, 470, 510, 545, 575, 590, 615,
             640, 670, 695, 715, 740, 765, 790, 814]


def etapa_control():
    CT = T / 'control'; CT.mkdir(parents=True, exist_ok=True)
    rep = {}
    for nombre in NOMBRES:
        arch = nombre_salida(nombre); mp4 = MAS / arch
        ok, err = L.decodifica(mp4)
        f = L.ficha(mp4)
        m = L.ebur(mp4)
        rep[nombre] = dict(archivo=arch, sha256=L.sha256(mp4), md5_video=L.md5_stream(mp4, 'v:0'),
                           md5_audio=L.md5_stream(mp4, 'a:0'), decodifica=ok, error=err, faststart=L.faststart(mp4),
                           gps=[k for k in f['formato']['tags'] if 'location' in k.lower() or 'gps' in k.lower()],
                           ficha=f, sonoridad=m)
        print(nombre, ok, m, flush=True)
    json.dump(rep, open(CT / 'tecnico.json', 'w'), ensure_ascii=False, indent=1)
    mp4 = MAS / nombre_salida('completa')
    # hojas de corte: n−1, n, n+1 de cada corte, a 360 px
    cs = CORTES
    for k, grupo in enumerate((cs[:7], cs[7:])):
        L.vista_360(mp4, CT / f'cortes_{k + 1}.jpg', [n + d for n in grupo for d in (-1, 0, 1)], cols=6)
    L.vista_360(mp4, CT / 'vista_360px.jpg', ZONAS_360, cols=10)
    # cuadro de la inscripción de 1968 (máster, resolución completa) y recorte 1:1 de la placa
    L.sh(['ffmpeg', '-v', 'error', '-y', '-i', mp4, '-vf', "select='eq(n\\,585)'", '-frames:v', '1', CT / 'inscripcion_1968_f585.png'])
    from PIL import Image
    Image.open(CT / 'inscripcion_1968_f585.png').crop((150, 300, 700, 1200)).save(CT / 'inscripcion_1968_f585_recorte.png')


if __name__ == '__main__':
    etapa = sys.argv[1]
    {'planos': etapa_planos, 'capas': etapa_capas, 'audio': etapa_audio, 'voz': etapa_voz, 'mezcla': etapa_mezcla,
     'master': etapa_master, 'control': etapa_control}[etapa]()
