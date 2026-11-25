#!/usr/bin/env python3
"""MARCA_momento · LIB-2 «Le faltaba uno» · receta con variables (Pedro, 25/11/2026).

Guion: 08_fede_guiones_LIB_v01.md (LIB-2 v01) + 09_roma_aprobacion_LIB.md (condiciones 4 y 6, agregado IGLIB)
+ 10_fede_guiones_ronda2_v02.md «Cambios en LIB» (giro G «LA PRIMERA Y LA QUINTA: / MISMO RIVAL, MISMA CANCHA.»;
P2 S6 = IMG_7894 0,000–2,500, 75 cuadros; P2 = 522 cuadros) + 11 (aprobado).
Uso:  python lib2.py <G1|G2|P1|P2|todas> [planos|capas|audio|voz|mezcla|master|control|todo]
Variables del sábado: lib2_variables.json (fc.id = null → placeholders T1/T3 con la etiqueta PLACEHOLDER en pantalla).
Intermedios en TRABAJO/momento/lib2/. Sin servicios externos. Sin commit. Ningún MP4/clip/audio va al repo.
"""
import json, os, sys, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
import lib_comun as L     # noqa: E402
from lib_comun import V, C, W, H, SR  # noqa: E402

T = L.R / 'TRABAJO/momento/lib2'
LIB1 = L.R / 'TRABAJO/momento/lib1'
VAR = json.load(open(Path(__file__).parent / 'lib2_variables.json'))
for toma in ('IMG_7894', 'IMG_8004'):          # rango completo (yuvj420p, pc según ffprobe) → limitado
    V.TOMAS[toma]['full'] = True

FC = VAR['fc']
SIN_FC = FC['id'] is None
# Sin clip oficial a las 21:00 (09, condición 6): fc.respaldo = true → congelado de S1/S3 = T13 33,0 y el resto con T1/T3,
# sin la etiqueta PLACEHOLDER (sale como _RESPALDO).
RESPALDO = SIN_FC and bool(FC.get('respaldo'))
PLACEHOLDER = SIN_FC and not RESPALDO
if not SIN_FC:                             # el clip de la final se baja a clips/tt/tt_<id>.mp4 con su info.json
    L.TT['FC'] = FC['id']; L.FPS_SRC['FC'] = FC['fps']


def modo_de(clipid):
    f = L.FPS_SRC[clipid]
    return 'cuadro' if f < 25 else ('descarte' if f > 50 else '1:1')


# ------------------------------------------------------------------------------------------------ textos
def textos(ver):
    t = VAR['textos']
    ap, x, y, a, b = t['apellido'], t['goles_est'], t['goles_pal'], t['penales_est'], t['penales_pal']
    hook_g1 = 'A ESTUDIANTES LE\nFALTABA UN GOL.'
    hook_g2 = 'ESTUDIANTES, OTRA\nVEZ A PENALES.' if t['g2_empate_con_goles'] else 'ESTUDIANTES, OTRA\nVEZ SIN UN GOL.'
    giro_g = 'LA PRIMERA Y LA QUINTA:\nMISMO RIVAL, MISMA CANCHA.'
    giro_p = ('PALMEIRAS PERDIÓ LA\nFINAL DEL AÑO PASADO.', 'HOY ES CAMPEÓN.')
    if ver == 'G1':
        return dict(hook=hook_g1, s4='ADENTRO.' if t['g1_gol_en_contra'] else f'{ap}.', giro=giro_g,
                    dato=f'Estudiantes {x}-{y} Palmeiras', cta='MANDÁSELO A QUIEN\nLA GRITÓ CON VOS.')
    if ver == 'G2':
        return dict(hook=hook_g2, s4=f'{ap}.', giro=giro_g, dato=f'Estudiantes {x}-{x} Palmeiras · penales {a}-{b}',
                    cta='MANDÁSELO A QUIEN\nLA GRITÓ CON VOS.')
    if ver == 'P1':
        pen = t['p1_por_penales']
        return dict(hook=hook_g2 if pen else hook_g1, s4='POR UNO.' if t['p1_solo_gol_de_palmeiras'] else 'ASÍ DE CERCA.',
                    giro=giro_p, dato=(f'Palmeiras {x}-{x} Estudiantes · penales {b}-{a}' if pen
                                       else f'Palmeiras {y}-{x} Estudiantes'),
                    cta='MANDÁSELO A QUIEN\nLA SUFRIÓ CON VOS.')
    if ver == 'P2':
        return dict(hook='ESTUDIANTES ESPERÓ\n17 AÑOS ESTA FINAL.', s4='HOY NO.', giro=giro_p,
                    dato=f'Palmeiras {y}-{x} Estudiantes', cta='MANDÁSELO A QUIEN\nLO BANCÓ IGUAL.')
    raise ValueError(ver)


S2_TEXTOS = ['0-0 Y 0-0.', 'CON DIEZ.', 'TRES ATAJADAS.', '1968: PALMEIRAS.']
DATO_S1 = 'Final de la Libertadores ·\nMontevideo'


# ------------------------------------------------------------------------------------------------ estructura
def estructura(ver):
    """Tramos (id, f0, n). P2 (dictamen 13 de Roma): S6 = los 74 cuadros de IMG_7894 sin repetir ninguno y S7 entra un
    cuadro antes, en f446, con 76 cuadros (T6 desde 96,408): 522 en total."""
    n6, n7 = (74, 76) if ver == 'P2' else (81, 75)
    S = [('S1', 0, 48), ('R1', 48, 24), ('R2', 72, 24), ('R3', 96, 24), ('R4', 120, 24), ('S3', 144, 36),
         ('S4', 180, 120), ('S5', 300, 72), ('S6', 372, n6), ('S7', 372 + n6, n7)]
    return S, 372 + n6 + n7


S6_TOMA = {'G1': ('IMG_8004', 0.750, 3.450), 'G2': ('IMG_8004', 0.750, 3.450),   # 14: termina con «ROCCÉ» completo
           'P1': ('IMG_3453', 0.500, 3.200), 'P2': ('IMG_7894', 0.000, 2.500)}
MARCA_TT = (60, 236, 272, 410)       # marca CONMEBOL (copa + «CONMEBOL LIBERTADORES») en los clips 1080×1920


# ------------------------------------------------------------------------------------------------ imagen
def mascara_png(clipid, salida, hasta_s):
    m = L.mascara_marca(MARCA_TT, t=clipid, cada=30, hasta_s=hasta_s)
    m.save(salida)
    return salida


def plano_marca(clipid, modo, t0, n, salida, efecto, mascara):
    """Plano con `efecto` (cadena -vf: desaturar, desenfocar) y la marca CONMEBOL devuelta nítida e intacta encima."""
    f = L.FPS_SRC[clipid]
    s = round(t0 * f)
    if modo in ('1:1', 'cuadro'):
        tr = f'trim=start_frame={s}:end_frame={s + n},setpts=N/(30*TB)'
    elif modo == 'descarte':
        tr = f"trim=start_frame={s}:end_frame={s + 2 * n},select='not(mod(n\\,2))',setpts=N/(30*TB)"
    else:
        raise ValueError(modo)
    x0, y0, x1, y1 = MARCA_TT
    fc = (f'[0:v]{tr},scale=1080:1920:flags=lanczos,setsar=1,format=yuv420p,split[a][b];'
          f'[a]{efecto}[fx];[b]crop={x1 - x0}:{y1 - y0}:{x0}:{y0},format=yuva420p[c];'
          f'[1:v]format=gray,scale={x1 - x0}:{y1 - y0}[m];[c][m]alphamerge[cm];'
          f'[fx][cm]overlay={x0}:{y0}:shortest=1,format=yuv420p[v]')
    L.sh(['ffmpeg', '-v', 'error', '-y', '-i', L.clip(clipid), '-loop', 1, '-i', mascara, '-filter_complex', fc,
          '-map', '[v]', '-frames:v', n, '-r', 30, *L.ENC_INT, salida])
    k = L.nframes(salida)
    if k != n:
        raise RuntimeError(f'{salida}: {k} != {n}')
    return dict(clip=clipid, modo=modo, t0=t0, cuadros=n, salida=str(salida), efecto=efecto)


DESAT = "eq=saturation=0.25,lutyuv=y='16+(val-16)*0.85':u='128+(val-128)*0.85':v='128+(val-128)*0.85'"
BLUR = "gblur=sigma=22,lutyuv=y='16+(val-16)*0.80'"


def congelado_png(salida):
    if RESPALDO:
        c, t = VAR['respaldo_sin_fc']['clip'], VAR['respaldo_sin_fc']['congelado_s']
    elif PLACEHOLDER:
        c, t = VAR['placeholder']['congelado']
    else:
        c, t = 'FC', FC['congelado_s']
    return L.cuadro_tt(c, round(t * L.FPS_SRC[c]), salida), (c, t)


def r4_png(salida):
    """R4 = el congelado con foco en la placa de 1968 de LIB-1 (B11b), desaturado y −15 % de luz; marca intacta."""
    im = Image.open(LIB1 / 't13_n915_foco.png').convert('RGB')
    g = im.convert('L').convert('RGB')
    d = Image.blend(g, im, 0.25)
    d = Image.eval(d, lambda v: int(v * 0.85))
    from lib1 import MARCA_T13
    d.paste(im.crop(MARCA_T13), MARCA_T13[:2], L.mascara_marca(MARCA_T13))
    d.save(salida)
    return salida


def etapa_planos(ver):
    P = T / ver / 'planos'; P.mkdir(parents=True, exist_ok=True)
    CO = T / 'comun'; CO.mkdir(parents=True, exist_ok=True)
    fichas = []
    S, NF = estructura(ver)
    ph = VAR['placeholder']
    # máscaras de marca por clip (una vez)
    # Máscara de la marca CONMEBOL sacada de T13 (tiene túnel y vestuario oscuros: el mínimo temporal deja solo las
    # letras). La marca está en el mismo lugar en todos los clips de @libertadores; con el mínimo de cada clip, T8 y
    # T10 (niebla y tribuna claras en todos sus cuadros) daban un rectángulo visible sobre el destello desaturado.
    p = CO / 'marca_T13_global.png'
    if not p.exists():
        L.mascara_marca(MARCA_TT, t='T13', cada=60, hasta_s=43.0).save(p)
    mk = {c: p for c in ('T1', 'T3', 'T6', 'T8', 'T10')}
    cong, cong_src = congelado_png(CO / 'congelado.png')
    for sid, f0, n in S:
        out = P / f'{sid}.mp4'
        if sid == 'S1':
            fi = L.png_a_plano(cong, n, out, zoom=(1.0, 1.03)); fi['fuente'] = cong_src
        elif sid == 'S3':
            fi = L.png_a_plano(cong, n, out, zoom=(1.03, 1.03)); fi['fuente'] = cong_src
        elif sid == 'R1':
            fi = plano_marca('T8', '1:1', 3.500, n, out, DESAT, mk['T8'])
        elif sid == 'R2':
            fi = plano_marca('T10', 'cuadro', 1.000, n, out, DESAT, mk['T10'])
        elif sid == 'R3':
            fi = plano_marca('T1', 'cuadro', 3.300, n, out, DESAT, mk['T1'])
        elif sid == 'R4':
            fi = L.png_a_plano(r4_png(CO / 'r4.png'), n, out); fi['fuente'] = ('T13', 915)
        elif sid == 'S4':
            c, t0 = (ph['s4'] if SIN_FC else ('FC', FC['entrada_s']))
            fi = L.plano_tt(c, modo_de(c), t0, n, out)
        elif sid == 'S5':
            c, t0 = (ph['s5_G'] if ver.startswith('G') else ph['s5_P']) if SIN_FC else ('FC', FC['s5_desde_s'])
            fi = L.plano_tt(c, modo_de(c), t0, n, out)
        elif sid == 'S6':
            toma, d0, d1 = S6_TOMA[ver]
            # IMG_7894 tiene 74 cuadros (2,467 s): en P2 S6 dura 74 y no se repite ningún cuadro (dictamen 13)
            fi = V.plano(toma, d0, d1, out)
            assert L.nframes(out) == n, (sid, L.nframes(out), n)
            fi['cuadros'] = n
        elif sid == 'S7':
            if ver.startswith('P'):
                c, t0 = ph['s7_P2'] if ver == 'P2' else ph['s7_P']   # T6 96,45 (P1) · 96,408 en P2 (un cuadro antes)
            else:
                c, t0 = ph['s7_G'] if SIN_FC else ('FC', FC['s7_desde_s'])
            fi = plano_marca(c, modo_de(c), t0, n, out, BLUR, mk.get(c, mk['T1']))
        fi.update(id=sid, f0=f0, f1=f0 + n - 1, cuadros=n)
        fichas.append(fi); print(ver, sid, n, flush=True)
    L.unir(fichas, T / ver / 'imagen.mp4')
    json.dump(fichas, open(T / ver / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)


# ------------------------------------------------------------------------------------------------ capas
def etiqueta(texto):
    f = C.fuente('semibold', 30)
    w = int(f.getlength(texto)) + 28
    im = Image.new('RGBA', (w, 46), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, 45], radius=8, fill=(255, 212, 0, 235))
    d.text((14, 6), texto, font=f, fill=(20, 20, 20, 255))
    return im


# Textos en pantalla como parámetro (Roma, 25/11: con locución pueden achicarse a palabras clave).
# lib2_textos.json: {"todas": {clave: valor}, "G1": {...}, ...}; la versión pisa a "todas". Claves: hook, dato_s1,
# s2_1…s2_4, pregunta, s4, giro (en P es una lista de dos placas), dato, ghyn, se_vuelve, cta. null = se saca la capa.
TXT2_PARAM = Path(__file__).parent / 'lib2_textos.json'
TXT2 = json.load(open(TXT2_PARAM)) if TXT2_PARAM.exists() else {}
NULOS = {'hook': ['hook'], 'dato_s1': ['dato_s1'], 'pregunta': ['pregunta'], 's4': ['s4'], 'giro': ['giro', 'giro1', 'giro2'],
         'dato': ['dato_res'], 'ghyn': ['ghyn'], 'se_vuelve': ['se_vuelve'], 'cta': ['cta'],
         **{f's2_{k}': [f's2_{k}'] for k in range(1, 5)}}


def _param(ver, clave):
    for d in (TXT2.get(ver, {}), TXT2.get('todas', {})):
        if clave in d:
            return True, d[clave]
    return False, None


def tx2(ver, clave, defecto):
    hay, v = _param(ver, clave)
    return v if (hay and v) else defecto


def sin_nulos(ver, K):
    fuera = {n for c, ns in NULOS.items() for n in ns if _param(ver, c) == (True, None)}
    return [k for k in K if k['nombre'] not in fuera]


def capas(ver):
    tx = textos(ver)
    for k in ('hook', 's4', 'giro', 'dato', 'cta'):
        tx[k] = tx2(ver, k, tx[k])
    S, NF = estructura(ver)
    fr = {sid: (f0, f0 + n) for sid, f0, n in S}
    K = []
    # S1 · APUESTA
    h = L.caja_fit(tx['hook'], tema='blanca')
    a, z = fr['S1']; K.append(L.capa(h, a, z, 470, pop=True, nombre='hook'))
    d1 = L.dato(tx2(ver, 'dato_s1', DATO_S1))
    K.append(L.capa(d1, a + 12, z, 1540 - d1.height, cx=490, nombre='dato_s1'))
    # S2 · PISTAS (placas secas sobre los destellos)
    for k, (sid, txt) in enumerate(zip(('R1', 'R2', 'R3', 'R4'), S2_TEXTOS)):
        a, z = fr[sid]
        y = 690 if sid == 'R4' else 450            # R4: debajo de la placa de 1968 (y 476–640), sin taparla
        K.append(L.capa(L.placa_fit(tx2(ver, f's2_{k + 1}', txt)), a, z, y, cx=(490 if sid == 'R4' else 540), nombre=f's2_{k + 1}'))
    # S3 · GRAN PREGUNTA
    a, z = fr['S3']
    K.append(L.capa(L.caja_fit(tx2(ver, 'pregunta', '¿VUELVE A GRABAR\nSU NOMBRE?'), tema='blanca'), a, z, 470, pop=True, nombre='pregunta'))
    # S4 · RESPUESTA: texto en el cuadro decisivo, arriba
    a, z = fr['S4']; dec = FC['decisivo_f']
    K.append(L.capa(L.placa_fit(tx['s4']), dec, z, 450, nombre='s4'))
    # S5 · GIRO + dato del resultado
    a, z = fr['S5']
    if ver.startswith('G'):
        g = L.placa_fit(tx['giro'])
        K.append(L.capa(g, a, z, 450, nombre='giro'))
        K.append(L.capa(L.dato(tx['dato']), a + 12, z, 450 + g.height - 10, nombre='dato_res'))
    else:
        g1 = L.placa_fit(tx['giro'][0]); g2 = L.placa_fit(tx['giro'][1])
        K.append(L.capa(g1, a, z, 450, nombre='giro1'))
        K.append(L.capa(g2, 330, z, 450 + g1.height - 20, nombre='giro2'))
        K.append(L.capa(L.dato(tx['dato']), 330, z, 450 + g1.height - 20 + g2.height - 10, nombre='dato_res'))
    # S6 · VEREDICTO (nunca apellidos)
    a, z = fr['S6']
    if ver.startswith('G'):
        K.append(L.capa(L.caja_fit(tx2(ver, 'ghyn', 'GIVE HISTORY YOUR NAME.'), tema='negra', maxw=980), 405, z, 300, pop=True,
                        nombre='ghyn'))
    elif ver == 'P2':
        K.append(L.capa(L.caja_fit(tx2(ver, 'se_vuelve', 'SE VUELVE.'), tema='blanca'), 390, z, 1330, cx=490, pop=True, nombre='se_vuelve'))
    # S7 · CTA
    a, z = fr['S7']
    K.append(L.capa(L.caja_fit(tx['cta'], tema='blanca', maxw=860), a, z, 860, cx=490, pop=True, nombre='cta'))
    # PLACEHOLDER en los tramos del clip de la final
    if PLACEHOLDER:
        et = etiqueta('PLACEHOLDER · clip de la final')
        tramos = ['S1', 'S3', 'S4', 'S5'] + (['S7'] if ver.startswith('G') else [])
        for sid in tramos:
            a, z = fr[sid]
            K.append(L.capa(et, a, z, 120, x=1040 - et.width, nombre=f'ph_{sid}'))
    return K, NF


def etapa_capas(ver):
    K, NF = capas(ver)
    K = sin_nulos(ver, K)
    malas = [(k['nombre'], k['caja']) for k in K if not k['nombre'].startswith('ph_') and C.fuera_de_zona([k['caja']])]
    L.rasterizar(K, NF, T / ver / 'capa')
    json.dump([dict(nombre=k['nombre'], f0=k['f0'], f1=k['f1'] - 1, caja=k['caja'], pop=k['pop']) for k in K],
              open(T / ver / 'capas.json', 'w'), ensure_ascii=False, indent=1)
    print(ver, 'fuera de zona:', malas)


# ------------------------------------------------------------------------------------------------ sonido
def stems(ver):
    S, NF = estructura(ver)
    fr = {sid: (f0, f0 + n) for sid, f0, n in S}
    dur = NF / 30; N = int(round(dur * SR))
    amb = np.zeros((N, 2), np.float32); fx = np.zeros((N, 2), np.float32)
    G = ver.startswith('G')
    tempo = 30 / (24000 / 1001)
    ph = VAR['placeholder']
    # S1: tribuna cortada a silencio (0,20 s) + latidos graves f0 y f24
    c, t = ph['congelado'] if SIN_FC else ('FC', FC['congelado_s'])
    tri = L.leer_audio(L.clip(c), max(0, t - 0.2), 0.22)
    tri = tri * 10 ** ((-24 - L.rms_db(tri)) / 20)
    L.put(amb, L.fades(tri, 0.004, 0.03), 0)
    L.put(fx, L.grave(-6), 0); L.put(fx, L.grave(-8), 24 / 30)
    # S2: seco, seco, grave, grave (+ pulso de la música)
    for tipo, f in (('seco', 48), ('seco', 72), ('grave', 96), ('grave', 120)):
        L.put(fx, L.seco(-9) if tipo == 'seco' else L.grave(-6), f / 30)
    # S3: silencio + un latido
    L.put(fx, L.grave(-8), 150 / 30)
    # S4: ambiente del clip; G: estallido (T1 10,0–11,9) en el cuadro decisivo · P: casi silencio después
    a, z = fr['S4']; dec = FC['decisivo_f']
    c, t0 = ph['s4'] if SIN_FC else ('FC', FC['entrada_s'])
    s4 = L.leer_audio(L.clip(c), t0, (dec - a) / 30 + 0.05, tempo=(tempo if modo_de(c) == 'cuadro' else 1.0))
    s4 = s4 * 10 ** ((-28 - L.rms_db(s4)) / 20)
    L.put(amb, L.fades(s4, 0.01, 0.05), a / 30)
    if G:
        est = L.leer_audio(L.clip('T1'), 10.0, 1.9)
        est = est * 10 ** ((-20 - L.rms_db(est)) / 20)
        L.put(amb, L.fades(est, 0.005, 0.15), dec / 30)
        L.put(fx, L.grave(-5), dec / 30)
    else:
        L.put(amb, L.fades(L.aire((z - dec) / 30, -46), 0.05, 0.05), dec / 30)
        L.put(fx, L.seco(-10), dec / 30)
    # S5: G tribuna · P casi silencio + nota grave; P: seco en f330 («HOY ES CAMPEÓN.»)
    a, z = fr['S5']
    if G:
        c, t0 = ph['s5_G'] if SIN_FC else ('FC', FC['s5_desde_s'])
        s5 = L.leer_audio(L.clip(c), t0, (z - a) / 30, tempo=tempo)
        s5 = s5 * 10 ** ((-27 - L.rms_db(s5)) / 20)
        L.put(amb, L.fades(s5, 0.02, 0.05), a / 30)
        L.put(fx, L.grave(-7), a / 30)
    else:
        L.put(amb, L.fades(L.aire((z - a) / 30, -46), 0.02, 0.05), a / 30)
        L.put(fx, L.grave(-9, dec=0.8), a / 30); L.put(fx, L.seco(-9), 330 / 30)
    # S6: G grave y sube · P1 roce de dedos · P2 ola real; las tres con el sonido real de la toma
    a, z = fr['S6']
    toma, d0, d1 = S6_TOMA[ver]
    s6 = L.leer_audio(L.R / f'ORIGINALES/{toma}.mov', d0, (z - a) / 30)
    s6 = s6 * 10 ** ((-27 - L.rms_db(s6)) / 20)
    L.put(amb, L.fades(s6, 0.004, 0.03), a / 30)
    if G:
        L.put(fx, L.grave(-5), a / 30); L.put(fx, L.subida(1.0, -20), a / 30 + 0.02)
    elif ver == 'P1':
        L.put(fx, L.roce((z - a) / 30 * 0.6, -26), a / 30 + 0.1)
    else:
        L.put(fx, L.grave(-8), 390 / 30)
    # S7: P sin audio del clip; G festejo bajo
    a, z = fr['S7']
    if G:
        c, t0 = ph['s7_G'] if SIN_FC else ('FC', FC['s7_desde_s'])
        s7 = L.leer_audio(L.clip(c), t0, (z - a) / 30, tempo=tempo)
        s7 = s7 * 10 ** ((-34 - L.rms_db(s7)) / 20)
        L.put(amb, L.fades(s7, 0.05, 0.3), a / 30)
    L.put(fx, L.grave(-8), a / 30)
    # música TEMP original
    t = lambda f: f / 30
    if G:
        tr = [(0, t(48), 'silencio'), (t(48), t(144), 'pulso'), (t(144), t(300), 'silencio'), (t(300), dur + 1, 'pleno')]
    else:
        tr = [(0, t(48), 'silencio'), (t(48), t(144), 'pulso'), (t(144), t(fr['S6'][0]), 'silencio'),
              (t(fr['S6'][0]), dur + 1, 'lento')]
    mus = L.musica(dur, tr)
    ref = mus[int(t(48) * SR):int(t(144) * SR)]
    mus *= 10 ** ((-24 - L.rms_db(ref)) / 20)
    nf = int(0.4 * SR); mus[-nf:] *= np.linspace(1, 0, nf)[:, None]
    amb[-nf:] *= np.linspace(1, 0.1, nf)[:, None]
    return dict(amb=amb, fx=fx, mus=mus)


def etapa_audio(ver):
    A = T / ver / 'audio'; A.mkdir(parents=True, exist_ok=True)
    for k, v in stems(ver).items():
        L.escribir_wav_f32(v, A / f'stem_{k}.wav')


# Locución Firme 04 por versión (guion 12 de Fede, aprobado por Roma el 25/11). Archivos en scripts/momento/:
#   voz_LIB2_<ver>.tsv            id<TAB>texto («Royé» por Roccé; {APELLIDO}, {X}, {Y}, {A}, {B} se completan con
#                                 lib2_variables.json: el apellido del sábado se sintetiza esa noche)
#   voz_LIB2_<ver>_ubicacion.tsv  plan: id<TAB>entra<TAB>tope<TAB>alternativa → voz_mezcla.resolver con la duración real
# La voz calla en S2 (destellos), en S4 entero (manda el estadio), en S6 de P1 y P2 y ±3 cuadros de cada golpe.
def voz_paths(ver):
    d = Path(__file__).parent
    return d / f'voz_LIB2_{ver}.tsv', d / f'voz_LIB2_{ver}_ubicacion.tsv'


def golpes(ver):
    """Cuadros de los golpes de stems() (no se mueven): latidos, destellos, latido de S3, decisivo, S5, S6, S7."""
    S, NF = estructura(ver); fr = {sid: f0 for sid, f0, n in S}
    g = [0, 24, 48, 72, 96, 120, 150, FC['decisivo_f'], 300, fr['S7']]
    g += [372] if ver.startswith('G') else [330]
    g += [390] if ver == 'P2' else []
    return sorted(g)


def prohibidas(ver):
    S, NF = estructura(ver); fr = {sid: (f0, f0 + n) for sid, f0, n in S}
    p = [(48, 144, 'S2 · destellos'), (180, 300, 'S4 · manda el estadio')]
    if ver.startswith('P'):
        p.append((*fr['S6'], 'S6 · remera en silencio'))
    return p


# Topes duros autorizados por Roma (14) para los CTA hablados; el resto sigue con el tope del guion.
_t = os.environ.get('TOPES', 'L2_07,L2_09,L2_10')
TOPES = _t if _t in ('guion', 'duros') else set(_t.split(','))


def etapa_voz(ver):
    import voz_mezcla as VM
    tsv, plan = voz_paths(ver)
    if not tsv.exists():
        print(ver, 'sin guion de voz:', tsv.name); return
    t = VAR['textos']
    rep = dict(APELLIDO=t['apellido'].strip('[]'),       # el sábado: el apellido real, escrito como se pronuncia
               X=t['goles_est'].strip('[]'), Y=t['goles_pal'].strip('[]'), A=t['penales_est'].strip('[]'),
               B=t['penales_pal'].strip('[]'))
    loc = T / ver / 'locucion'
    VM.generar(tsv, loc, reemplazos=rep, palabras=os.environ.get('PALABRAS', '1') == '1')
    S, NF = estructura(ver)
    forzar = {'L2_01': 'L2_02'} if ver == 'P1' and t.get('p1_por_penales') else {}
    dec, av1 = VM.resolver(loc, plan, golpes(ver), prohibidas(ver), salida=loc / 'ubicacion_resuelta.tsv', forzar=forzar,
                           topes=TOPES, nf=NF)
    solo = [d['id'] for d in dec if not d.get('bloqueada')]
    a, frases, av2 = VM.pista(loc, loc / 'ubicacion_resuelta.tsv', NF, prohibidas=prohibidas(ver), solo=solo)
    VM.escribir(a, T / ver / 'audio' / 'stem_loc.wav')
    json.dump(dict(guion=str(tsv), plan=str(plan), topes=sorted(TOPES) if isinstance(TOPES, set) else TOPES, ubicacion=str(loc / 'ubicacion_resuelta.tsv'), elegidas=solo,
                   golpes=golpes(ver), prohibidas=prohibidas(ver), decisiones=dec, frases=frases, avisos=av1 + av2,
                   reemplazos=rep), open(loc / 'pista.json', 'w'), ensure_ascii=False, indent=1)
    for d in dec:
        print(ver, f"{d['plan']:7s} {d['id']:7s} guion f{d['entra_guion']} → f{d['f0']}–{d['fin_f']} (tope f{d['tope']}, "
              f"{d['dur_s']} s) {d['accion']}")
    print(ver, 'avisos:', av1 + av2 or 'ninguno')


def con_locucion(ver):
    return (T / ver / 'audio' / 'stem_loc.wav').exists()


def etapa_mezcla(ver):
    import voz_mezcla as VM
    A = T / ver / 'audio'; S, NF = estructura(ver); dur = NF / 30
    loc = A / 'stem_loc.wav'
    if not loc.exists():
        loc = VM.escribir(np.zeros((int(round(dur * SR)), 2), np.float32), A / 'stem_loc_vacia.wav')
    muda = VM.escribir(np.zeros((int(round(dur * SR)), 2), np.float32), A / 'stem_voz_vacia.wav')   # LIB-2 no tiene voz de Muslera
    st = dict(loc=loc, voz=muda, mus=A / 'stem_mus.wav', amb=A / 'stem_amb.wav', fx=A / 'stem_fx.wav')
    tramos = ([(f['id'], f['t0'], f['t1']) for f in json.load(open(T / ver / 'locucion' / 'pista.json'))['frases']]
              if con_locucion(ver) else [])
    med = {}
    for nombre, niv in (('completa', {}), ('sinmusica', {'mus_db': -120})):
        med[nombre] = VM.mezclar(st, dur, A / f'mezcla_{nombre}.wav', niveles=niv, tramos_voz=tramos,
                                 auto_claves=(('amb_db',) if nombre == 'sinmusica' else None))
        g = VM.ganancias_frases(med[nombre], [t[0] for t in tramos]) if tramos else {}
        if g:
            pj = json.load(open(T / ver / 'locucion' / 'pista.json'))
            a, _, _ = VM.pista(T / ver / 'locucion', Path(pj['ubicacion']), NF, ganancias=g, solo=pj['elegidas'])
            VM.escribir(a, A / f'stem_loc_{nombre}.wav')
            med[nombre] = VM.mezclar(dict(st, loc=A / f'stem_loc_{nombre}.wav'), dur, A / f'mezcla_{nombre}.wav',
                                     niveles=med[nombre]['niveles_fondo_db'], tramos_voz=tramos, auto=False)
            med[nombre]['ganancia_por_frase_db'] = g
        print(ver, nombre, med[nombre]['sonoridad'], flush=True)
    med['locucion'] = 'Firme 04' if con_locucion(ver) else 'sin locución (premezcla)'
    json.dump(med, open(A / 'medidas.json', 'w'), ensure_ascii=False, indent=1)


# ------------------------------------------------------------------------------------------------ máster y control
def parcial(ver):
    p = T / ver / 'locucion' / 'pista.json'
    return con_locucion(ver) and p.exists() and any(d.get('bloqueada') for d in json.load(open(p))['decisiones'])


def nombre(ver, sinmus=False):
    tag = ('_PLACEHOLDER' if PLACEHOLDER else '_RESPALDO' if RESPALDO else '') + ('' if con_locucion(ver) else '_SINLOCUCION')
    v = ('v01' + ('_PARCIAL' if parcial(ver) else '')) if con_locucion(ver) else 'v00'
    return f'ROCCE_LIB2_{ver}{tag}{"_SINMUSICA" if sinmus else ""}_{v}.mp4'


def etapa_master(ver, sinmus=False):
    M = T / ver / 'master'; M.mkdir(parents=True, exist_ok=True)
    out = M / nombre(ver, sinmus)
    L.master(T / ver / 'imagen.mp4', T / ver / 'audio' / f'mezcla_{"sinmusica" if sinmus else "completa"}.wav',
             T / ver / 'capa', out)
    print(out, flush=True)


def etapa_master_dos(ver):
    etapa_master(ver); etapa_master(ver, sinmus=True)


def etapa_control(ver):
    M = T / ver / 'master'; mp4 = M / nombre(ver)
    S, NF = estructura(ver)
    reps = {}
    for clave, sm in (('completa', False), ('sinmusica', True)):
        m4 = M / nombre(ver, sm)
        if not m4.exists():
            continue
        ok, err = L.decodifica(m4)
        f = L.ficha(m4)
        reps[clave] = dict(archivo=m4.name, sha256=L.sha256(m4), md5_video=L.md5_stream(m4, 'v:0'),
                           md5_audio=L.md5_stream(m4, 'a:0'), decodifica=ok, error=err, faststart=L.faststart(m4),
                           gps=[k for k in f['formato']['tags'] if 'location' in k.lower()], ficha=f, sonoridad=L.ebur(m4))
    json.dump(reps, open(M / 'tecnico.json', 'w'), ensure_ascii=False, indent=1)
    rep = reps['completa']; ok = rep['decodifica']; f = rep['ficha']
    cuadros = [0, 30, 60, 84, 108, 132, 160, 200, 240, 270, 310, 340, 360]
    a6 = S[8][1]; a7 = S[9][1]
    cuadros += [a6 + 5, a6 + 40, a7 - 3, a7 + 10, NF - 1]
    L.vista_360(mp4, M / f'vista_360px_{ver}.jpg', cuadros, cols=9)
    print(ver, ok, rep['sonoridad'], f['video']['cuadros'], flush=True)


ETAPAS = ('planos', 'capas', 'audio', 'voz', 'mezcla', 'master', 'control')

if __name__ == '__main__':
    vers = ['G1', 'G2', 'P1', 'P2'] if sys.argv[1] == 'todas' else [sys.argv[1]]
    et = sys.argv[2] if len(sys.argv) > 2 else 'todo'
    for v in vers:
        for e in (ETAPAS if et == 'todo' else (et,)):
            {'planos': etapa_planos, 'capas': etapa_capas, 'audio': etapa_audio, 'voz': etapa_voz,
             'mezcla': etapa_mezcla, 'master': etapa_master_dos, 'control': etapa_control}[e](v)
