#!/usr/bin/env python3
"""Roccé Life · tanda 3 · V6 «¿Le llega?» (Dibu Martínez) y V7 «¿Algún día le toca?» (Di María) · másters v01
(Pedro, 26/11/2026). Una receta parametrizada para las dos piezas.

Guiones: piezas/LIFE_rocce_life/TANDA3/04_fede_guion_V6_dibu_v1.md y 05_fede_guion_V7_dimaria_v1.md, con las
correcciones de Roma (06_roma_dictamen_guiones_t3.md), que mandan: rótulo solo con el nombre (año y club van en el texto
de la historia), recortes neutros (sin número, tablero, pelota, arco ni gesto de partido), pasos 4 y 5 de V6 juntos en
1,0 s, sin Firme 04, oferta exacta. Regla de la casa de apuestas: pregunta abierta en c0, evidencia rápida y la voz real
del deportista al final; ningún término de apuestas en pantalla.

Sistema del V4 A aprobado, importado sin modificar las recetas (life_v4_a → life_v4_v02 → life_v4): B/N (croma 128) y
color, golpes E− (exposición ×0,5 + grave) / E+ (×√2 + agudo), texto cinético (mismo CSS/JS y renderizador
life_v4_render.js, con tres agregados hechos acá sobre la cadena: clase extra por frase, interlineado propio y cursiva
Instrument Serif), negro de separación de 3 cuadros, voz real con el fondo que cede por envolvente (A.envolvente),
limitador sin autonivelado (A.limitar: alimiter level=false), música TEMP propia (sonido.Mezcla) + versión SINMUSICA,
máster con M.master_v4 (H.264 High 4.0, AAC 48 kHz). Firma con L2.CSS_PLACA y life_v2_render.js.

Uso (nice -n 10, python de TRABAJO/venv):  life_t3.py v6|v7 <etapa>
  voz → planos → textos → firma → audio → master → control → entregar
Intermedios en TRABAJO/life3/t3/<pieza>/ (fuera de git). Sin servicios externos ni créditos; nada se publica.

v02 (26/11/2026, pedido de Roma después de aprobar v01):  life_t3.py v6_v02|v7_v02 <etapa>
  narracion → planos → textos → placa → audio → master → control → entregar_v02
  - narración con la voz dirigida (es-AR-TomasNeural, edge-tts 7.3.1 + Praat + FFmpeg; copia sin modificar de
    voz_dirigida.py en TRABAJO/life3/t3/narracion, corrida con voz_proxy.py), texto y dinámica de las capas 07/08 de
    Fede con los ajustes de Roma: un grito y un quiebre por pieza, tramo calmo antes del grito, golpe un cuadro antes
    del grito a ×0,6, ≥ 0,4 s de aire contra la voz real y el narrador nunca más fuerte que ella; lo que no entra a
    ritmo natural sale de la voz y queda escrito;
  - «Va a haber 100 Founders como máximo» +0,5 s (IMG_5325 desde 11,2 s; la pieza dura 0,5 s más);
  - V7: «2021», «Solo.» y el rótulo «COPA AMÉRICA 2024 · SU ÚLTIMO PARTIDO EN LA SELECCIÓN».
  El resto del montaje es el de v01: los planos sin cambios se copian de la base v01 (sin pérdida) y la voz real es el
  mismo corte. v01 se sigue reproduciendo con `v6|v7`.
"""
import copy, hashlib, json, math, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/life')
import life_v4_a as A          # noqa: E402  (importa life_v4_v02 y life_v4; no se modifica ninguno)
import life_v4_control as C    # noqa: E402

M, B2, U, V, L2 = A.M, A.B2, A.U, A.V, A.L2
R = Path('/home/user/1')
CLIPS = R / 'TRABAJO/life3/clips'
T3 = R / 'TRABAJO/life3/t3'
SDR = T3 / 'sdr'
GIAN = Path('/mnt/project-files/material_gianluca/2026-11-26')
PIEZAS = Path('/mnt/project-files/piezas/LIFE_rocce_life/TANDA3')
FPS, W, H, SR = 30, 1080, 1920, 48000
PY_WHISPER = str(R / 'TRABAJO/whisper-env/bin/python')
CEL = M.CELESTE
HLG_SDR = ('zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,'
           'zscale=t=bt709:m=bt709:r=tv,format=yuv420p')

# fuentes
CONMEBOL = 'tt_conmebol_7680653482692529426'
ESPN = 'tt_espnargentina_7649237878836333842'
TYC21 = 'tt_tycsports_7660905284776283413'
CA43 = 'tt_copaamerica_7643552343920856327'
TYC22 = 'tt_tycsports_7585191917797788940'
CA411 = 'tt_copaamerica_7411292372350340358'
AFA = 'tt_afaseleccion_7392038397776350469'
P5359, P5361, P5325 = 'IMG_5359_sdr_6.0', 'IMG_5361_sdr_0', 'IMG_5325_sdr_11.0'
SDR_TRAMOS = {P5359: ('IMG_5359', 6.0, 4.2), P5361: ('IMG_5361', 0.0, 2.9), P5325: ('IMG_5325', 11.0, 3.0)}
UTIL = {ESPN: (0, 785)}         # panel de arriba de ESPN: filas sobre los subtítulos quemados (los recortes neutros)


def nice(cmd):
    return ['nice', '-n', '10'] + list(cmd)


def jdump(o, f):
    M.jdump(o, f)


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True).stdout


# =====================================================================================================================
# piezas
# =====================================================================================================================
def W_(x0, y0, w):
    return [(0, x0, y0, w)]


def espalda(claves, w=460, arriba=332, xmax=1080):
    """recorte de espalda que deja ver la cabeza pero no el nombre ni el número: claves [(k, borde de arriba de la cabeza,
    borde de arriba del nombre, centro x de la cabeza)] medidas en la fuente (grilla de 50 px a resolución 1:2). La
    ventana deja `arriba` filas de la fuente sobre la cabeza; las filas útiles terminan 10 px antes del nombre y lo que
    queda debajo se completa con el relleno (perfil de las últimas filas: la tela de la camiseta), como A.componer."""
    ven, uti = [], []
    for k, top, nombre, hx in claves:
        x0 = min(max(0, hx - w / 2), xmax - w)
        ven.append((k, round(x0, 1), max(0, top - arriba), w)); uti.append((k, 0, nombre - 10))
    return dict(ventana=ven, util=uti, fundido_abajo=True)


def fundir_abajo(out, yb, alto=320, color=(8, 8, 8)):
    """la figura se funde a casi negro hacia abajo: opacidad 0 en yb − alto + 20 y 1 en yb + 20 (yb = última fila real
    del recorte en la salida); tapa el relleno de la tela y deja cabeza y hombros."""
    ys = np.arange(H, dtype=np.float32)
    a = np.clip((ys - (yb + 20 - alto)) / alto, 0, 1) ** 1.2
    return out * (1 - a[:, None, None]) + np.array(color, np.float32) * a[:, None, None]


# planos: m0/nf en cuadros del máster; n0 = primer cuadro de la fuente; ventana = [(k, x0, y0, ancho)] (alto = ancho·16/9,
# interpolada entre claves); E = exposición del B/N (0,5 = E−, √2 = E+, 1 = neutro); velocidad '1a1' o 'natural'.
E_M, E_P, E_N = 0.5, 2 ** 0.5, 1.0
PIEZA = {
    'v6': dict(
        nombre='V6_dibu', titulo='V6 «¿Le llega?» (Dibu Martínez)', NF=630, negro=(438, 440),
        archivos={'completa': 'ROCCE_LIFE_V6_DIBU_v01.mp4', 'sinmusica': 'ROCCE_LIFE_V6_DIBU_SINMUSICA_v01.mp4'},
        planos=[
            dict(id='01_espalda', m0=0, nf=42, clip=ESPN, n0=2289, ventana=W_(470, -330, 500), E=E_M,
                 muestra='panel de arriba (entrenamiento con Vignolo, 2023): de espaldas, mira a un costado; sin arco, pelota ni boca a la vista'),
            dict(id='03_perfil', m0=42, nf=48, clip=ESPN, n0=2217, ventana=W_(330, -290, 560), E=E_M,
                 muestra='panel de arriba: de perfil, quieto (plano medio, fondo de paredes); sin arco ni pelota'),
            dict(id='04a_cerca', m0=90, nf=15, clip=ESPN, n0=2265, ventana=W_(470, -170, 400), E=E_P,
                 muestra='panel de arriba: el mismo perfil más cerrado, boca cerrada (salto hacia adelante)'),
            dict(id='04b_nuca', m0=105, nf=15, clip=ESPN, n0=31, ventana=W_(300, -220, 560), E=E_M,
                 muestra='panel de arriba, primer plano: gira y queda de nuca (salto lateral)'),
            dict(id='06_frente', m0=120, nf=27, clip=ESPN, n0=2356, ventana=W_(300, -330, 560), E=E_P,
                 muestra='panel de arriba: gira hacia cámara en una pausa, boca cerrada; sin gesto de atajada'),
            dict(id='07_final', m0=147, nf=24, clip=CONMEBOL, n0=1388, ventana=W_(0, 0, 1080), E=E_N,
                 muestra='Argentina–Francia 2022, jugada en plano general (rótulo de CONMEBOL a la vista)'),
            dict(id='08_mano_a_mano', m0=171, nf=33, clip=CONMEBOL, n0=1573, ventana=W_(0, 0, 1080), E=E_N,
                 muestra='Kolo Muani llega mano a mano (corte del propio video en n1585 al plano desde atrás del arco); termina antes del remate'),
            dict(id='09_explica', m0=204, nf=192, clip=ESPN, n0=2591, ventana=W_(0, 0, 1080), E=E_N, franja=True,
                 muestra='pantalla dividida nativa: arriba él explica, abajo la repetición de la atajada; velocidad natural, sincronía del original'),
            dict(id='10_atajada', m0=396, nf=42, clip=CONMEBOL, n0=1735, ventana=W_(0, 0, 1080), E=E_N,
                 muestra='la atajada a Kolo Muani desde atrás del arco, completa y en color (rótulo de CONMEBOL sin tocar)'),
            dict(id='12_placa', m0=441, nf=78, clip=P5359, n0=15, ventana=W_(0, 0, 1080), E=E_N, grad=(0, 820, 0.70),
                 muestra='IMG_5359 6,5–9,1 s: la mano de Gianluca con la placa; entra en foco ≈ 7,5 s'),
            dict(id='13_oferta', m0=519, nf=60, clip=P5361, n0=27, ventana=W_(140, 260, 800), E=E_N, grad=(0, 900, 0.55),
                 muestra='IMG_5361 0,9–2,9 s: acercamiento a la placa sobre la remera negra y la blanca'),
            dict(id='14_cta', m0=579, nf=51, clip=P5325, n0=21, ventana=W_(0, -300, 1080), E=E_N, grad=(0, 760, 0.55),
                 muestra='IMG_5325 11,7–13,4 s: espalda de la blanca, bordado «ROCCÉ» y «Founders Privée»'),
        ],
        # croma: (cuadro, fracción de color) con interpolación lineal; color en 4 c desde c204
        croma=[(0, 0.0), (203, 0.0), (204, 0.25), (207, 1.0), (629, 1.0)],
        voz=dict(clip=ESPN, separada=None, src0=2591 / 30, src1=92.62, m0=204 / 30,
                 texto='“…le bloqueo toda esta parte. Después te puede entrar: si la pelota va acá, era gol.”',
                 palabras=[('“…le', 86.57), ('bloqueo', 86.687), ('toda', 87.067), ('esta', 87.187), ('parte.', 87.327),
                           ('Después', 87.967), ('te', 88.167), ('puede', 88.307), ('entrar:', 88.467), ('si', 89.227),
                           ('la', 89.587), ('pelota', 89.727), ('va', 90.027), ('acá,', 90.427), ('era', 91.547), ('gol.”', 91.807)],
                 renglones=[5, 4, 7], sub_golpe=377),
    ),
    'v7': dict(
        nombre='V7_dimaria', titulo='V7 «¿Algún día le toca?» (Di María)', NF=720, negro=(528, 530),
        archivos={'completa': 'ROCCE_LIFE_V7_DIMARIA_v01.mp4', 'sinmusica': 'ROCCE_LIFE_V7_DIMARIA_SINMUSICA_v01.mp4'},
        planos=[
            dict(id='01_espalda', m0=0, nf=42, clip=TYC21, n0=327, E=E_M, g=1.6,
                 **espalda([(0, 545, 880, 625), (7, 545, 830, 605), (14, 440, 790, 565), (28, 360, 760, 585),
                            (34, 420, 770, 660), (41, 545, 800, 620)]),
                 muestra='festejo de 2021 de espaldas (el mismo de c222): la cabeza contra el cartel azul; nombre y número fuera de las filas útiles'),
            dict(id='03_espalda2', m0=42, nf=21, clip=CA43, n0=521, E=E_M,
                 **espalda([(0, 415, 760, 390), (10, 470, 730, 760), (19, 535, 840, 805), (20, 555, 860, 805)], arriba=240),
                 muestra='Copa América 7643, 21,7–22,6 s: de espaldas contra el pasto y la parte blanca del cartel (las letras quedan arriba, fuera de la ventana)'),
            dict(id='04_hombro', m0=63, nf=21, clip=TYC21, n0=276, E=E_M,
                 **espalda([(0, 455, 680, 765), (14, 440, 680, 755), (20, 500, 740, 850)]),
                 muestra='TyC 9,2–9,9 s: corre de espaldas contra el pasto (salto lateral); sin el reloj de TyC, el nombre ni el número'),
            dict(id='05a_corre', m0=84, nf=11, clip=TYC21, n0=297, E=E_M,
                 **espalda([(0, 505, 740, 910), (5, 525, 790, 980), (9, 540, 800, 960), (10, 540, 820, 930)], arriba=190),
                 muestra='TyC 9,9–10,3 s: sigue corriendo; el cartel blanco detrás, sus letras arriba fuera de la ventana'),
            dict(id='05b_corre', m0=95, nf=10, clip=CA43, n0=556, E=E_M,
                 **espalda([(0, 520, 820, 640), (1, 545, 840, 640), (4, 450, 770, 635), (7, 450, 770, 650), (9, 480, 800, 620)],
                           arriba=300),
                 muestra='Copa América 7643, 23,2–23,6 s: de espaldas contra el cartel azul (fragmentos de letras y del logo, sin palabra legible)'),
            dict(id='06_pase', m0=105, nf=30, clip=CA43, n0=362, ventana=W_(0, 0, 1080), E=E_P,
                 muestra='final de 2021 en el Maracaná: el pase largo de De Paul, plano general (24 fps a 1,25×)'),
            dict(id='07_solo', m0=135, nf=27, clip=CA43, n0=422, ventana=W_(0, 0, 1080), E=E_N,
                 muestra='Di María se va solo, plano general (24 fps a 1,25×)'),
            dict(id='08_area', m0=162, nf=24, clip=TYC21, n0=186, ventana=W_(0, 0, 1080), E=E_N,
                 muestra='llega al área (transmisión de TyC)'),
            dict(id='09_vaselina', m0=186, nf=36, clip=TYC21, n0=210, ventana=W_(0, 0, 1080), E=E_N,
                 muestra='la vaselina; la pelota entra en n238 (c214), donde entra el color'),
            dict(id='10_festejo', m0=222, nf=48, clip=TYC21, n0=327, ventana=W_(0, 0, 1080), E=E_N,
                 muestra='el mismo festejo de c0, completo y en color'),
            dict(id='11_contra', m0=270, nf=27, clip=TYC22, n0=240, ventana=W_(0, 0, 720), E=E_M,
                 muestra='final de 2022: la contra (25 fps a 1,2×); vuelve a B/N en 4 c'),
            dict(id='12_remate', m0=297, nf=30, clip=TYC22, n0=347, ventana=W_(0, 0, 720), E=E_N,
                 muestra='el remate (n362 → c312), color en 4 c'),
            dict(id='13_lagrimas', m0=327, nf=24, clip=TYC22, n0=400, ventana=W_(0, 0, 720), E=E_N,
                 muestra='el festejo de 2022, en color'),
            dict(id='14_copa', m0=351, nf=177, clip=CA411, n0=989, ventana=W_(0, 0, 720), E=E_N, velocidad='natural',
                 grad=(1060, 1640, 0.62, 'banda'),
                 muestra='Copa América 2024, su último partido: besa la Copa y sonríe con la medalla (sin el tramo 26–31 s)'),
            dict(id='16_placa', m0=531, nf=78, clip=P5359, n0=15, ventana=W_(0, 0, 1080), E=E_N, grad=(0, 820, 0.70),
                 muestra='IMG_5359 6,5–9,1 s: la mano de Gianluca con la placa; entra en foco ≈ 7,5 s'),
            dict(id='17_oferta', m0=609, nf=60, clip=P5361, n0=27, ventana=W_(140, 260, 800), E=E_N, grad=(0, 900, 0.55),
                 muestra='IMG_5361 0,9–2,9 s: acercamiento a la placa sobre la remera negra y la blanca'),
            dict(id='18_cta', m0=669, nf=51, clip=P5325, n0=21, ventana=W_(0, -300, 1080), E=E_N, grad=(0, 760, 0.55),
                 muestra='IMG_5325 11,7–13,4 s: espalda de la blanca, bordado «ROCCÉ» y «Founders Privée»'),
        ],
        croma=[(0, 0.0), (213, 0.0), (214, 0.25), (217, 1.0), (269, 1.0), (270, 0.75), (273, 0.0), (311, 0.0), (312, 0.25),
               (315, 1.0), (719, 1.0)],
        voz=dict(clip=AFA, separada=T3 / 'voz/sep/htdemucs/dimaria_76-fin/vocals.wav', sep_desde=76.0, src0=87.08, src1=92.68,
                 m0=11.89, texto='“Algún día se iba a romper la pared. Se rompió la pared. Me la di muchas veces, pero seguí estando acá.”',
                 palabras=[('“Algún', 87.18), ('día', 87.44), ('se', 87.58), ('iba', 87.78), ('a', 87.86), ('romper', 88.00),
                           ('la', 88.18), ('pared.', 88.30), ('Se', 89.04), ('rompió', 89.22), ('la', 89.62), ('pared.', 89.76),
                           ('Me', 90.38), ('la', 90.56), ('di', 90.62), ('muchas', 90.76), ('veces,', 90.98), ('pero', 91.50),
                           ('seguí', 91.60), ('estando', 91.90), ('acá.”', 92.04)],
                 renglones=[5, 3, 4, 5, 4], tarjetas=[3, 2], sub_golpe=520),
    ),
}


# ---------------------------------------------------------------------------------------------------------------------
# v02: misma pieza con narración, Founders +0,5 s y (V7) textos achicados y rótulo nuevo
# ---------------------------------------------------------------------------------------------------------------------
NARR = T3 / 'narracion'          # copia sin modificar de voz_dirigida.py, guiones TSV y frases sintetizadas
VOZ_DIRIGIDA_ORIGINAL = Path('/mnt/project-files/voz/voz_dirigida.py')
TEXTO_NARR = {   # texto exacto de las capas 07/08 de Fede (lo que se dice; el TSV lleva la grafía para sintetizar)
    'n01': 'Diez años.', 'n02': '¿Le llega?', 'n03': 'Lo prestan.', 'n04': 'Y otra vez. Y otra.', 'n05': 'Seis veces.',
    'n06': 'A los veintiocho.', 'n07': '¡Y ataja tres penales!', 'n08': '¡Ciento veintitrés!', 'n09': 'Mano a mano…',
    'n10': '¡Campeón del mundo!', 'n11': 'Él tiene su minuto.', 'n12': 'Seguir hasta lograrlo.',
    'n13': 'Black Friday: veinticinco por ciento menos.', 'n14': 'Va a haber cien Founders como máximo.',
    'n15': 'Conseguí la tuya.',
    'm01': 'Se pierde la final.', 'm02': '¿Algún día?', 'm03': 'Lesionado.', 'm04': 'Otra vez.', 'm05': 'Tres derrotas.',
    'm06': 'Otra final.', 'm07': 'En el mismo estadio.', 'm08': 'Queda solo…', 'm09': 'Se la pica…', 'm10': '¡Gol!',
    'm11': 'Pero le falta una.', 'm12': 'Llega la del Mundial.', 'm13': '¡Otra vez él!', 'm14': 'Él tiene su copa.',
    'm15': 'Seguir hasta lograrlo.', 'm16': 'Black Friday: veinticinco por ciento menos.',
    'm17': 'Va a haber cien Founders como máximo.', 'm18': 'Conseguí la tuya.',
}
NARRACION = {
    # (frase, comienzo del habla en el máster, s): duración real de cada frase (medida en su WAV) y su momento en la capa
    'v6': dict(
        frases=[('n01', 0.10), ('n02', 1.10), ('n03', 1.70), ('n06', 3.05), ('n08', 5.30), ('n10', 13.46),
                ('n11', 14.85), ('n12', 16.05), ('n13', 17.42), ('n15', 20.52)],
        grito='n08', quiebre='n10', grito_cuadro=159, cta='n13',
        fuera={
            'n04': 'dura 1,77 s y su lugar en la capa es 0,55 s (1,95–2,50) entre «Lo prestan.» y el golpe de 2,60',
            'n05': 'con «Seis veces.» (0,84 s) «A los veintiocho.» terminaría en 4,5 s, sobre «Un mes después…»; queda escrito «Seis préstamos.» con su golpe',
            'n07': 'dura 1,13 s y terminaría en 5,2 s, pegado al grito de 5,30: no deja el tramo calmo antes del grito',
            'n09': 'dura 0,80 s; entre el final del grito (6,29 s) y 0,4 s antes de la primera palabra de Dibu (7,00 s) quedan 0,31 s',
            'n14': 'dura 2,21 s; entre el final de «Black Friday…» (19,67 s) y el CTA (20,50 s) quedan 0,83 s; queda escrito 19,30–20,50 s',
        }),
    'v7': dict(
        frases=[('m01', 0.10), ('m02', 1.30), ('m04', 2.15), ('m05', 2.84), ('m06', 3.96), ('m08', 4.62), ('m09', 6.32),
                ('m10', 215 / FPS), ('m11', 8.20), ('m12', 9.28), ('m13', 10.47), ('m14', 17.85), ('m15', 19.05),
                ('m16', 20.42), ('m18', 23.52)],
        grito='m10', quiebre='m05', grito_cuadro=215, cta='m16',
        fuera={
            'm03': 'dura 0,49 s; después de «¿Algún día?» (termina en 2,02 s) caería sobre «2016: llega tocado.» (2,10 s), que es el renglón de «Otra vez.»',
            'm07': 'dura 0,92 s; entre «Tres derrotas.» (termina en 3,85 s) y «Queda solo…» (4,62 s) entra solo «Otra final.» (0,56 s); queda escrito «En el Maracaná, como en 2014.»',
            'm17': 'dura 2,21 s; entre el final de «Black Friday…» (22,66 s) y el CTA (23,50 s) quedan 0,84 s; queda escrito 22,30–23,50 s',
        }),
}


def _v02(base, archivos):
    p = copy.deepcopy(PIEZA[base])
    p.update(version='v02', pieza=base, reusar=base, NF=p['NF'] + 15, cta_dn=36, pad_cta=2.2, archivos=archivos,
             narracion=NARRACION[base], golpe_grito=0.6)
    ult = p['planos'][-1]
    assert ult['clip'] == P5325 and ult['n0'] == 21 and ult['nf'] == 51
    ult.update(n0=6, nf=66, muestra='IMG_5325 11,2–13,4 s: espalda de la blanca, bordado «ROCCÉ» y «Founders Privée» '
                                    '(0,5 s más que v01, sin pasar de 13,4 s, donde la cámara sube)')
    p['croma'][-1] = (p['NF'] - 1, 1.0)
    return p


PIEZA['v6_v02'] = _v02('v6', {'completa': 'ROCCE_LIFE_V6_DIBU_v02.mp4', 'sinmusica': 'ROCCE_LIFE_V6_DIBU_SINMUSICA_v02.mp4'})
PIEZA['v7_v02'] = _v02('v7', {'completa': 'ROCCE_LIFE_V7_DIMARIA_v02.mp4', 'sinmusica': 'ROCCE_LIFE_V7_DIMARIA_SINMUSICA_v02.mp4'})

P = None          # pieza activa
TP = None         # carpeta de intermedios de la pieza


def activar(clave):
    global P, TP
    P = PIEZA[clave]; P['clave'] = clave
    P.setdefault('pieza', clave); P.setdefault('version', 'v01')
    TP = T3 / clave
    TP.mkdir(parents=True, exist_ok=True)
    tot = 0
    for p in P['planos']:
        if p['m0'] == P['negro'][1] + 1 and tot == P['negro'][0]:
            tot = P['negro'][1] + 1
        assert p['m0'] == tot, (p['id'], p['m0'], tot)
        tot += p['nf']
    assert tot == P['NF'], tot


# =====================================================================================================================
# fuentes · decodificación
# =====================================================================================================================
def ruta(clip):
    return SDR / f'{clip}.mp4' if clip.startswith('IMG_') else CLIPS / f'{clip}.mp4'


_PROBE = {}


def probe(clip):
    if clip not in _PROBE:
        st = json.loads(run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate,width,height',
                             '-of', 'json', str(ruta(clip))]))['streams'][0]
        a, b = st['r_frame_rate'].split('/')
        _PROBE[clip] = (float(a) / float(b), st['width'], st['height'])
    return _PROBE[clip]


def indices(p):
    f, _, _ = probe(p['clip'])
    if p.get('velocidad') == 'natural':
        return [p['n0'] + int(math.floor(k * f / FPS + 1e-9)) for k in range(p['nf'])]
    return [p['n0'] + k for k in range(p['nf'])]


def decodificar(clip, ix):
    f, w, h = probe(clip)
    a, b = min(ix), max(ix)
    raw = run(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(ruta(clip)), '-an', '-vf',
                    f"select='between(n\\,{a}\\,{b})',scale=in_color_matrix=bt709:in_range=tv,format=rgb24",
                    '-fps_mode', 'passthrough', '-f', 'rawvideo', '-']))
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    assert len(fr) == b - a + 1, (clip, len(fr), a, b)
    return {n: fr[n - a] for n in sorted(set(ix))}, (w, h)


def info_clip(clip):
    if clip.startswith('IMG_'):
        src, s0, d = SDR_TRAMOS[clip]
        return dict(cuenta='material de Gianluca (09/11/2026)', id=src, url=str(GIAN / f'{src}.mov'), fecha_publicacion='—',
                    descripcion=f'HLG → SDR BT.709 (cadena mobius de CLAUDE.md), tramo {s0}–{s0 + d} s', duracion=None)
    d = json.load(open(CLIPS / f'{clip}.info.json'))
    ts = d.get('timestamp')
    return dict(cuenta='@' + (d.get('uploader') or '?'), id=d.get('id'), url=d.get('webpage_url'),
                fecha_publicacion=time.strftime('%d/%m/%Y %H:%M UTC', time.gmtime(ts)) if ts else d.get('upload_date'),
                descripcion=(d.get('description') or d.get('title') or '')[:200], duracion=d.get('duration'))


# =====================================================================================================================
# planos · composición en RGB, grado (B/N con E−/E+ y color) y base sin pérdida
# =====================================================================================================================
def ventana_en(p, k):
    cl = p['ventana']
    if len(cl) == 1 or k <= cl[0][0]:
        return cl[0][1:]
    for (ka, *va), (kb, *vb) in zip(cl, cl[1:]):
        if ka <= k <= kb:
            t = (k - ka) / (kb - ka)
            return tuple(a + (b - a) * t for a, b in zip(va, vb))
    return cl[-1][1:]


def util_en(p, k):
    """filas útiles de la fuente (u0, u1) del plano en el cuadro k: claves [(k, u0, u1)] interpoladas, o las de la
    fuente (UTIL) si la ventana es más angosta que la toma."""
    cl = p.get('util')
    if not cl:
        return None
    if len(cl) == 1 or k <= cl[0][0]:
        return cl[0][1:]
    for (ka, *va), (kb, *vb) in zip(cl, cl[1:]):
        if ka <= k <= kb:
            t = (k - ka) / (kb - ka)
            return tuple(a + (b - a) * t for a, b in zip(va, vb))
    return cl[-1][1:]


def _relleno(prof, filas):
    from scipy import ndimage as nd
    p = nd.gaussian_filter1d(prof, 30, axis=0, mode='nearest')
    return np.repeat(p[None], filas, 0)


def componer(rgb, x0, y0, w, util):
    """RGB float (0–255) 1080×1920 de la ventana (x0, y0, ancho); fuera de las filas útiles, relleno con el perfil de
    las filas del borde desenfocado en horizontal y 48 filas de transición (como A.componer, en color)."""
    from PIL import Image
    h_s, w_s = rgb.shape[:2]
    s = W / w
    u0, u1 = util or (0, h_s)
    Ya = max(0, int(math.ceil((u0 - y0) * s - 1e-6)))
    Yb = min(H, int(math.floor((u1 - y0) * s + 1e-6)))
    assert -1e-6 <= x0 and x0 + w <= w_s + 1e-6, (x0, w, w_s)
    part = np.asarray(Image.fromarray(rgb).resize((W, Yb - Ya), Image.LANCZOS, box=(x0, y0 + Ya / s, x0 + w, y0 + Yb / s)),
                      np.float32)
    out = np.empty((H, W, 3), np.float32)
    out[Ya:Yb] = part
    T_ = 48
    if Ya > 0:
        prof = np.median(part[:16], 0)
        out[:Ya] = _relleno(prof, Ya)
        r = np.linspace(0, 1, T_)[:, None, None]
        out[Ya:Ya + T_] = (1 - r) * _relleno(prof, T_) + r * part[:T_]
    if Yb < H:
        prof = np.median(part[-16:], 0)
        out[Yb:] = _relleno(prof, H - Yb)
        r = np.linspace(1, 0, T_)[:, None, None]
        out[Yb - T_:Yb] = (1 - r) * _relleno(prof, T_) + r * part[-T_:]
    return out


# franja de la cita de V6: tapa los subtítulos quemados de ESPN (contorno negro desde y = 777, blanco 781–889, medido en
# los 192 cuadros de la fuente; v01 empezaba en 786 y asomaban las puntas de las letras altas) sin tocar el logo de ESPN
# (caja desde y ≈ 893) ni la cara (arriba de y ≈ 560 en todo el tramo)
FRANJA = dict(solida=(768, 891), color=(14, 14, 14), degrade=(500, 768), opac_degrade=0.86)


def pintar_franja(out):
    y0, y1 = FRANJA['solida']; d0, d1 = FRANJA['degrade']
    c = np.array(FRANJA['color'], np.float32)
    a = np.linspace(0, FRANJA['opac_degrade'], d1 - d0)[:, None, None] ** 1.2
    out[d0:d1] = out[d0:d1] * (1 - a) + c * a
    out[y0:y1] = c
    return out


def oscurecer(out, g):
    """degradé oscuro para leer el texto: ('arriba') desde y0 con opacidad op que baja a 0 en y1, o ('banda') una banda
    suave centrada entre y0 e y1 (sube y baja)."""
    y0, y1, op = g[:3]
    modo = g[3] if len(g) > 3 else 'arriba'
    ys = np.arange(H, dtype=np.float32)
    if modo == 'arriba':
        a = np.clip((y1 - ys) / (y1 - y0), 0, 1) ** 1.3 * op
    else:
        c, m = (y0 + y1) / 2, (y1 - y0) / 2
        a = np.clip(1 - np.abs(ys - c) / m, 0, 1) ** 0.7 * op
    tinte = np.array([12, 18, 26], np.float32)
    return out * (1 - a[:, None, None]) + tinte * a[:, None, None]


def lut_bn(g, k):
    return A.lut_a(g, 'bn', k)


def croma_en(n):
    pts = P['croma']
    for (na, a), (nb, b) in zip(pts, pts[1:]):
        if na <= n <= nb:
            return a if nb == na else a + (b - a) * (n - na) / (nb - na)
    return pts[-1][1]


def a_yuv(out, n, p, g_base, luts):
    """RGB (0–255, BT.709 con gamma) → Y′CbCr 4:2:0 rango tv; B/N = luma con la exposición E (×g_base en luz lineal)."""
    R_, G_, B_ = out[..., 0], out[..., 1], out[..., 2]
    Yf = 0.2126 * R_ + 0.7152 * G_ + 0.0722 * B_
    Yc = 16 + 219 * np.clip(Yf, 0, 255) / 255
    a = croma_en(n)
    if a < 1:
        key = (round(g_base, 4), p['E'])
        if key not in luts:
            luts[key] = lut_bn(g_base, p['E']).astype(np.float32)
        Ybn = luts[key][np.clip(np.round(Yc), 0, 255).astype(np.uint8)]
        Y = (1 - a) * Ybn + a * Yc
    else:
        Y = Yc
    Cb = 128 + 224 * (B_ - Yf) / (1.8556 * 255)
    Cr = 128 + 224 * (R_ - Yf) / (1.5748 * 255)
    sub = lambda c: c.reshape(H // 2, 2, W // 2, 2).mean((1, 3))
    Cb, Cr = 128 + a * (sub(Cb) - 128), 128 + a * (sub(Cr) - 128)
    q = lambda x: np.clip(np.round(x), 0, 255).astype(np.uint8)
    return q(Y), q(Cb), q(Cr), a


def g_base_de(muestras):
    """ganancia base en luz lineal que lleva la mediana de luma del plano a ≈ 0,16 (como G_BASE del V4 A, medida)."""
    v = np.clip((np.median(np.concatenate(muestras)) - 16) / 219, 1e-3, 1)
    return float(np.clip(0.16 / v ** 2.4, 0.6, 4.5))


def etapa_planos():
    dst = TP / 'base.mp4'
    cs = (W // 2) * (H // 2)
    enc = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{W}x{H}',
                                 '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-qp', '0', '-preset', 'veryfast', '-threads', '2',
                                 '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                                 '-color_range', 'tv', str(dst)]), stdin=subprocess.PIPE)
    reg, luts, n_tot = [], {}, 0
    # v02: los planos idénticos a los de v01 (mismo id, cuadros y parámetros) se copian de la base v01, que es sin
    # pérdida (x264 qp 0): los cuadros son los mismos bytes Y′CbCr. Solo se compone lo que cambió.
    lector, src_n, src_reg, igual = None, 0, {}, set()
    if P.get('reusar'):
        fuente = PIEZA[P['reusar']]
        sp = {p['id']: p for p in fuente['planos']}
        igual = {p['id'] for p in P['planos'] if sp.get(p['id']) == p}
        assert fuente['negro'] == P['negro']
        src_reg = {r['id']: r for r in json.load(open(T3 / P['reusar'] / 'planos.json'))['planos']}
        lector = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(T3 / P['reusar'] / 'base.mp4'),
                                        '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-']), stdout=subprocess.PIPE)
    fsz = W * H + 2 * cs

    def de_fuente():
        nonlocal src_n
        assert src_n == n_tot, (src_n, n_tot)
        b = lector.stdout.read(fsz); assert len(b) == fsz
        src_n += 1
        return b
    for p in P['planos']:
        if n_tot == P['negro'][0]:
            for _ in range(P['negro'][1] - P['negro'][0] + 1):
                negro = bytes([16]) * (W * H) + bytes([128]) * (2 * cs)
                if lector and src_n == n_tot:
                    assert de_fuente() == negro
                enc.stdin.write(negro); n_tot += 1
        if p['id'] in igual and lector and src_n == n_tot:
            for _ in range(p['nf']):
                enc.stdin.write(de_fuente()); n_tot += 1
            reg.append(dict(src_reg[p['id']], reutilizado=f"cuadros copiados de la base {P['reusar']} (sin pérdida)"))
            print(p['id'], p['nf'], 'copiado de', P['reusar'], flush=True)
            continue
        if lector:
            lector.kill(); lector.wait(); lector = None
        ix = indices(p)
        fr, wh = decodificar(p['clip'], ix)
        util0 = UTIL.get(p['clip']) if p['ventana'][0][3] < wh[0] else None
        util = lambda k: util_en(p, k) or util0
        # ganancia base medida sobre 5 cuadros compuestos
        ks = sorted({0, len(ix) // 4, len(ix) // 2, 3 * len(ix) // 4, len(ix) - 1})
        mu = []
        for k in ks:
            x0, y0, w = ventana_en(p, k)
            o = componer(fr[ix[k]], x0, y0, w, util(k))
            filas = H
            if p.get('fundido_abajo'):           # la ganancia se mide arriba del fundido (cabeza y fondo), no en el negro
                filas = int((util(k)[1] - y0) * W / w) - 320
            mu.append((16 + 219 * (o[:filas] @ np.array([.2126, .7152, .0722], np.float32)) / 255)[::8, ::8].ravel())
        g = g_base_de(mu) if p['E'] != E_N or p.get('g') else 1.0
        g = p.get('g', g)
        st = []
        for k, n in enumerate(ix):
            x0, y0, w = ventana_en(p, k)
            o = componer(fr[n], x0, y0, w, util(k))
            if p.get('fundido_abajo'):
                o = fundir_abajo(o, (util(k)[1] - y0) * W / w)
            if p.get('franja'):
                o = pintar_franja(o)
            if p.get('grad'):
                o = oscurecer(o, p['grad'])
            Y, Cb, Cr, a = a_yuv(o, n_tot, p, g, luts)
            enc.stdin.write(Y.tobytes()); enc.stdin.write(Cb.tobytes()); enc.stdin.write(Cr.tobytes())
            st.append(dict(c=n_tot, fuente=n, ventana=[round(x0, 1), round(y0, 1), round(w, 1)], croma=round(a, 3),
                           luma=round(float(Y[::8, ::8].mean()), 1)))
            n_tot += 1
        f_, w_, h_ = probe(p['clip'])
        reg.append(dict(id=p['id'], m0=p['m0'], cuadros=p['nf'], clip=p['clip'], fps_fuente=round(f_, 3), resolucion=[w_, h_],
                        fuente=[ix[0], ix[-1]], tramo_s=[round(ix[0] / f_, 3), round((ix[-1] + 1) / f_, 3)],
                        velocidad=p.get('velocidad', '1a1'), ventana=p['ventana'], filas_utiles=p.get('util'), E=p['E'], g_base=round(g, 3),
                        franja=bool(p.get('franja')), degrade=p.get('grad'), fundido_abajo=bool(p.get('fundido_abajo')), muestra=p['muestra'],
                        luma_media=round(float(np.mean([s['luma'] for s in st])), 1)))
        print(p['id'], p['nf'], 'g', round(g, 2), reg[-1]['luma_media'], flush=True)
        del fr
    if lector:
        lector.kill(); lector.wait()
    enc.stdin.close(); enc.wait()
    assert enc.returncode == 0 and n_tot == P['NF'], n_tot
    jdump(dict(cuadros=n_tot, planos=reg), TP / 'planos.json')
    print('base', n_tot)


def etapa_muestra():
    """revisión rápida de recortes sin codificar la base: por plano (ids en argv[3:]), cada clave compuesta (B/N sin
    grado) al lado de la fuente con la ventana (verde) y las filas útiles (rojo) marcadas."""
    from PIL import Image, ImageDraw
    ids = sys.argv[3:]
    tiles = []
    for p in P['planos']:
        if ids and p['id'] not in ids:
            continue
        ix = indices(p)
        ks = sorted({c[0] for c in p['ventana']} | {0, p['nf'] - 1})
        fr, wh = decodificar(p['clip'], [ix[k] for k in ks])
        for k in ks:
            x0, y0, w = ventana_en(p, k)
            o = componer(fr[ix[k]], x0, y0, w, util_en(p, k) or (UTIL.get(p['clip']) if w < wh[0] else None))
            if p.get('fundido_abajo'):
                o = fundir_abajo(o, (util_en(p, k)[1] - y0) * W / w)
            a = Image.fromarray(np.clip(o, 0, 255).astype(np.uint8)).resize((270, 480))
            src = Image.fromarray(fr[ix[k]]); d = ImageDraw.Draw(src)
            d.rectangle([x0, y0, x0 + w, y0 + w * 16 / 9], outline=(0, 255, 0), width=6)
            u = util_en(p, k)
            if u:
                for y in u:
                    d.line([(0, y), (wh[0], y)], fill=(255, 0, 0), width=5)
            b = src.resize((270, round(270 * wh[1] / wh[0])))
            t = Image.new('RGB', (544, 480), (30, 30, 30)); t.paste(a, (0, 0)); t.paste(b, (274, 0))
            ImageDraw.Draw(t).text((4, 4), f"{p['id']} k{k} n{ix[k]}", fill=(255, 255, 0))
            tiles.append(t)
    cols = 4
    S = Image.new('RGB', (cols * 548, -(-len(tiles) // cols) * 484), (0, 0, 0))
    for i, t in enumerate(tiles):
        S.paste(t, ((i % cols) * 548, (i // cols) * 484))
    S.save(TP / 'muestra.jpg', quality=85)
    print(TP / 'muestra.jpg', S.size)


def etapa_revisar():
    """hoja de composición para revisar antes de los textos: primer, medio y último cuadro de cada plano (base)."""
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(M.FONT, 18)
    tiles = []
    for p in P['planos']:
        for k in (0, p['nf'] // 2, p['nf'] - 1):
            n = p['m0'] + k
            im = Image.fromarray(U.leer(TP / 'base.mp4', 216, 384, n0=n, n1=n)[0]); d = ImageDraw.Draw(im)
            for y in (270, 1130):
                d.line([(0, y / 5), (216, y / 5)], fill=(255, 0, 0))
            d.rectangle([0, 0, 120, 22], fill=(0, 0, 0)); d.text((3, 2), f'c{n} {p["id"][:9]}', font=fnt, fill=(255, 255, 0))
            tiles.append(im)
    cols = 9
    S = Image.new('RGB', (cols * 218, -(-len(tiles) // cols) * 386), (30, 30, 30))
    for i, t in enumerate(tiles):
        S.paste(t, ((i % cols) * 218, (i // cols) * 386))
    S.save(TP / 'revisar_base.jpg', quality=82)
    print(TP / 'revisar_base.jpg')



# =====================================================================================================================
# voz real · corte medido en el piso de ruido, sin cortes internos ni cambio de tono o tiempo
# =====================================================================================================================
WHISPER_PY = r"""
import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('small', device='cpu', compute_type='int8')
out = {}
for f in sys.argv[2:]:
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-vn', '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(pcm, dtype=np.float32)
    segs, info = m.transcribe(a, language='es', vad_filter=False, word_timestamps=True, beam_size=5,
                              condition_on_previous_text=False)
    out[f] = [dict(texto=s.text.strip(), ini=round(s.start, 2), fin=round(s.end, 2), p_sin_voz=round(s.no_speech_prob, 3),
                   palabras=[[w.word.strip(), round(w.start, 2), round(w.end, 2), round(w.probability, 2)] for w in (s.words or [])])
              for s in segs]
json.dump(out, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
"""


def whisper(salida, archivos):
    """faster-whisper small (whisper-env), audio ya decodificado a 16 kHz, sin initial_prompt (solo idioma)."""
    subprocess.run(nice([PY_WHISPER, '-c', WHISPER_PY, str(salida)] + [str(a) for a in archivos]), check=True)
    return json.load(open(salida))


def nivel_db(x, sr, t0, t1):
    i0, i1 = max(0, int(t0 * sr)), min(len(x), int(t1 * sr))
    return round(20 * math.log10(np.sqrt((x[i0:i1] ** 2).mean()) + 1e-12), 1)


def etapa_voz():
    import soundfile as sf
    vz = P['voz']; d = TP / 'voz'; d.mkdir(parents=True, exist_ok=True)
    dur = vz['src1'] - vz['src0']
    out = d / 'voz_48k.wav'
    fad = f"pan=mono|c0=0.5*c0+0.5*c1,aresample=48000,afade=t=in:d=0.010,afade=t=out:st={dur - 0.030:.4f}:d=0.030"
    if vz['separada']:
        src, ss = vz['separada'], vz['src0'] - vz['sep_desde']
    else:
        src, ss = CLIPS / f"{vz['clip']}.mp4", vz['src0']
    V.sh(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss:.4f}', '-t', f'{dur:.4f}', '-i', str(src), '-vn', '-af', fad,
          '-c:a', 'pcm_f32le', str(out)])
    # el mismo tramo de la fuente original sin separar, y un contexto de ±1,5 s (para ver qué queda afuera)
    V.sh(['ffmpeg', '-v', 'error', '-y', '-ss', f"{vz['src0']:.4f}", '-t', f'{dur:.4f}', '-i', str(CLIPS / f"{vz['clip']}.mp4"),
          '-vn', '-af', 'pan=mono|c0=0.5*c0+0.5*c1,aresample=48000', '-c:a', 'pcm_f32le', str(d / 'tramo_original_48k.wav')])
    ctx = d / 'contexto_48k.wav'
    V.sh(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ss - 1.5:.4f}', '-t', f'{dur + 3.0:.4f}', '-i', str(src), '-vn', '-af',
          'pan=mono|c0=0.5*c0+0.5*c1,aresample=48000', '-c:a', 'pcm_f32le', str(ctx)])
    x, sr = sf.read(str(out)); xc, _ = sf.read(str(ctx))
    tr = whisper(d / 'whisper.json', [out, ctx])
    # piso de ruido en los bordes del corte (contexto: el corte empieza en 1,5 s y termina en 1,5 + dur)
    bordes = dict(antes_del_corte_db=nivel_db(xc, sr, 1.5 - 0.06, 1.5), despues_del_inicio_db=nivel_db(xc, sr, 1.5, 1.56),
                  antes_del_final_db=nivel_db(xc, sr, 1.5 + dur - 0.06, 1.5 + dur),
                  despues_del_final_db=nivel_db(xc, sr, 1.5 + dur, 1.5 + dur + 0.06),
                  voz_mediana_db=round(float(np.median([nivel_db(x, sr, t, t + 0.05) for t in np.arange(0.2, dur - 0.2, 0.05)])), 1))
    pal = vz.get('palabras')
    jdump(dict(fuente=info_clip(vz['clip']), tramo_fuente_s=[round(vz['src0'], 4), round(vz['src1'], 4)],
               duracion_s=round(len(x) / sr, 4), entra_en_master_s=round(vz['m0'], 4),
               termina_en_master_s=round(vz['m0'] + len(x) / sr, 4),
               separacion=('demucs 4.1 htdemucs --two-stems=vocals desde %.1f s' % vz['sep_desde']) if vz['separada'] else
               'sin separar: audio original del clip (sin música en el tramo; piso ≈ −60 dB)',
               metodo='mono 48 kHz, fundidos de 10 ms y 30 ms; sin cortes internos, sin cambio de tono ni de tiempo',
               bordes_nivel_db=bordes, texto_fijado=vz['texto'], whisper=tr,
               palabras=[dict(palabra=w, fuente_s=t, master_s=round(t - vz['src0'] + vz['m0'], 3),
                              cuadro=cuadro_voz(t)) for w, t in (pal or [])]), d / 'voz.json')
    print(json.dumps(bordes), flush=True)
    for f, segs in tr.items():
        print(Path(f).name, ' | '.join(s['texto'] for s in segs))
        print('   ', ' '.join(f'{w}@{a:.2f}' for s in segs for w, a, b, p in s['palabras']))


def cuadro_voz(t):
    """cuadro del máster en que suena el instante t de la fuente de la voz."""
    vz = P['voz']
    return int(math.floor((t - vz['src0'] + vz['m0']) * FPS + 1e-9))


# =====================================================================================================================
# v02 · narración con la voz oficial de Roccé (voz dirigida: edge-tts es-AR-TomasNeural + Praat + FFmpeg)
# =====================================================================================================================
VOZ_OFICIAL = Path('/mnt/project-files/voz_rocce')     # versión oficial (aprobada por Gianluca el 26/11/2026)


def sha256_de(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def k_pond(x):
    """ponderación K de BS.1770 a 48 kHz (estante + paso alto)."""
    from scipy.signal import lfilter
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x)
    return lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y)


def sonoridad_habla(x):
    """sonoridad de habla (ponderación K, señal mono centrada = LUFS de la versión estéreo): bloques de 50 ms a menos de
    20 dB del bloque más fuerte (deja afuera los silencios de la frase)."""
    y = k_pond(np.asarray(x, np.float64)); w = int(0.05 * SR); nb = len(y) // w
    ms = (y[:nb * w].reshape(nb, w) ** 2).mean(1)
    return round(-0.691 + 10 * math.log10(ms[ms > ms.max() * 0.01].mean() + 1e-20), 2)


def momentanea_max(x):
    """sonoridad momentánea máxima (ventana de 400 ms cada 10 ms, ponderación K)."""
    y = k_pond(np.asarray(x, np.float64)); w = int(0.4 * SR); h = int(0.01 * SR)
    if len(y) <= w:
        return round(-0.691 + 10 * math.log10((y ** 2).sum() / w + 1e-20), 2)
    c = np.concatenate([[0.0], np.cumsum(y ** 2)]); i = np.arange(0, len(y) - w, h)
    return round(-0.691 + 10 * math.log10(((c[i + w] - c[i]) / w).max() + 1e-20), 2)


def extension_habla(x, umbral=-40.0):
    """primer y último instante (s) con ventanas de 10 ms a menos de |umbral| dB del máximo."""
    w = int(0.01 * SR); nb = len(x) // w
    r = np.sqrt((x[:nb * w].reshape(nb, w) ** 2).mean(1)) + 1e-12
    i = np.nonzero(20 * np.log10(r / r.max()) > umbral)[0]
    return round(i[0] * w / SR, 3), round((i[-1] + 1) * w / SR, 3)


def offset_oficial(f):
    """mezcla de la voz oficial (LEEME_VOZ_OFICIAL.md): voz baja +5 dB, grito y CTA +2 dB, el resto 0."""
    if 'bajo' in f['estilos']:
        return 5.0
    if 'grito' in f['estilos'] or f['id'] == P['narracion']['cta']:
        return 2.0
    return 0.0


def comparar_muestra():
    """control de que el servicio sigue dando la voz aprobada: dos frases de la muestra oficial (w4 [lento], w3 con grito
    y quiebre) resintetizadas hoy con la misma receta (NARR/control_oficial) contra muestra_04_v02 (LEEME_VOZ_OFICIAL:
    «si el servicio cambia la voz, comparar contra esta muestra»). Medidas, no escucha."""
    import soundfile as sf
    from scipy.signal import correlate, stft
    out = {}
    for w in ('w4', 'w3'):
        a, _ = sf.read(str(NARR / 'control_oficial' / f'{w}.wav')); b, _ = sf.read(str(VOZ_OFICIAL / 'muestra_04_v02' / f'{w}.wav'))
        lag = int(np.argmax(correlate(a, b, 'full'))) - (len(b) - 1)
        a2, b2 = (a[lag:], b) if lag >= 0 else (a, b[-lag:])
        n = min(len(a2), len(b2)); a2, b2 = a2[:n], b2[:n]
        _, _, SA = stft(a2, SR, nperseg=1024); _, _, SB = stft(b2, SR, nperseg=1024)
        out[w] = dict(sha256_hoy=sha256_de(NARR / 'control_oficial' / f'{w}.wav'),
                      sha256_muestra=sha256_de(VOZ_OFICIAL / 'muestra_04_v02' / f'{w}.wav'),
                      muestras_hoy=len(a), muestras_muestra=len(b), desfase_muestras=lag,
                      correlacion_forma_de_onda=round(float(np.corrcoef(a2, b2)[0, 1]), 4),
                      correlacion_espectrograma_log=round(float(np.corrcoef(np.log10(np.abs(SA) + 1e-6).ravel(),
                                                                           np.log10(np.abs(SB) + 1e-6).ravel())[0, 1]), 4),
                      rms_db_hoy=round(20 * math.log10(np.sqrt((a ** 2).mean())), 2),
                      rms_db_muestra=round(20 * math.log10(np.sqrt((b ** 2).mean())), 2))
    out['f0_mediana_hz'] = 'w4 114,5 / 114,5 · w3 117,9 / 117,9 (Praat, voz-env; medido el 26/11 al recibir la versión oficial)'
    return out


def etapa_narracion():
    """frases sintetizadas con la copia sin modificar de voz_dirigida.py (sha256 igual a la oficial), medidas y ubicadas
    por el comienzo de su habla; Whisper de cada frase (sin escucha)."""
    import soundfile as sf
    nz, pieza = P['narracion'], P['pieza']
    d, tsv = NARR / pieza, NARR / f'{pieza}_guion.tsv'
    hs = dict(copia_usada=sha256_de(NARR / 'voz_dirigida.py'), oficial_voz_rocce=sha256_de(VOZ_OFICIAL / 'voz_dirigida.py'),
              anterior_voz=sha256_de(VOZ_DIRIGIDA_ORIGINAL))
    assert hs['copia_usada'] == hs['oficial_voz_rocce'], hs
    if not (d / 'voz.json').exists():
        subprocess.run([str(R / 'TRABAJO/voz-env/bin/python'), '-I', str(R / 'scripts/life/voz_proxy.py'), 'voz_dirigida.py',
                        tsv.name, pieza], cwd=str(NARR), check=True)
    vj = json.load(open(d / 'voz.json'))
    guion = dict(l.rstrip('\n').split('\t', 1) for l in open(tsv, encoding='utf-8') if l.strip() and not l.startswith('#'))
    frases = []
    for fid, t_on in nz['frases']:
        x, sr = sf.read(str(d / f'{fid}.wav')); assert sr == SR
        a, b = extension_habla(x)
        ini = round(t_on - a, 4)
        frases.append(dict(id=fid, texto=TEXTO_NARR[fid], guion_tsv=guion[fid],
                           estilos=[t['estilo'] for t in vj['frases'][fid]['tramos']], wav=str(d / f'{fid}.wav'),
                           sha256=sha256_de(d / f'{fid}.wav'), duracion_wav=round(len(x) / SR, 3), habla_en_wav=[a, b],
                           habla_s=round(b - a, 3), wav_entra_s=ini, habla_master_s=[round(t_on, 3), round(t_on + b - a, 3)],
                           cuadros_habla=[int(math.floor(t_on * FPS + 1e-9)), int(math.floor((t_on + b - a) * FPS - 1e-9))],
                           sonoridad_habla_cruda=sonoridad_habla(x),
                           palabras=[[round(ini + o, 3), w] for t in vj['frases'][fid]['tramos'] for o, w in t['palabras']]))
    for f0, f1 in zip(frases, frases[1:]):
        assert f1['habla_master_s'][0] - f0['habla_master_s'][1] >= 0.095, (f0['id'], f1['id'])   # ≥ 0,1 s entre frases
    tr = whisper(TP / 'narracion_whisper_frases.json', [f['wav'] for f in frases])
    for f in frases:
        f['whisper_frase_sola'] = ' '.join(s['texto'] for s in tr[f['wav']])
        print(f"{f['id']} {f['habla_master_s'][0]:6.2f}–{f['habla_master_s'][1]:6.2f}  {f['texto']:<45} Whisper: {f['whisper_frase_sola']}")
    # aire contra la voz real: habla real medida en su WAV (ventanas de 10 ms a menos de 30 dB del máximo)
    xr, _ = sf.read(str(T3 / pieza / 'voz' / 'voz_48k.wav'))
    a, b = extension_habla(xr, -30.0)
    vz = P['voz']; r0, r1 = round(vz['m0'] + a, 3), round(vz['m0'] + b, 3)
    c0, c1 = round(vz['m0'], 3), round(vz['m0'] + len(xr) / SR, 3)
    antes = max(f['habla_master_s'][1] for f in frases if f['habla_master_s'][1] <= r0)
    despues = min(f['habla_master_s'][0] for f in frases if f['habla_master_s'][0] >= r1)
    aire = dict(voz_real_habla_s=[r0, r1], voz_real_corte_s=[c0, c1], narracion_termina_antes_s=antes,
                narracion_vuelve_s=despues, aire_antes_s=round(r0 - antes, 3), aire_despues_s=round(despues - r1, 3),
                aire_antes_del_corte_s=round(c0 - antes, 3), aire_despues_del_corte_s=round(despues - c1, 3))
    assert aire['aire_antes_s'] >= 0.4 and aire['aire_despues_s'] >= 0.4, aire
    print('aire', aire)
    jdump(dict(voz=dict(proveedor='servicio de lectura en voz alta de Microsoft Edge vía edge-tts 7.3.1',
                        voz=vj['voz'], motor=vj['motor'], sha256_voz_dirigida=hs,
                        guion_tsv=str(tsv), sha256_guion=sha256_de(tsv)),
               frases=frases, fuera_de_la_voz=[dict(id=k, texto=TEXTO_NARR[k], motivo=v) for k, v in nz['fuera'].items()],
               grito=nz['grito'], quiebre=nz['quiebre'], aire_voz_real=aire, control_muestra_oficial=comparar_muestra()),
          TP / 'narracion.json')


# =====================================================================================================================
# textos · texto cinético del V4 (M.CSS_TEXTO, M.JS_TEXTO, life_v4_render.js) con tres agregados sobre la cadena:
# clase extra por frase, interlineado propio (--lh) para citas más chicas y acento celeste dentro de la cita
# =====================================================================================================================
NB = ' '
PCT = '−25' + NB + '%'
CHIP = M.LH_CHIP                                   # 122 px por renglón a 86 px


def lh_chip(fs):
    return round(fs * 1.42)


def frases_oferta(o):
    """paso de la oferta (o = primer cuadro) y CTA (o + 60): textos de Roma (06, corrección 5), sin fecha ni «solo hoy»."""
    y1 = 300 + lh_chip(66) + 18
    y3 = y1 + 160 + 18
    y4 = y3 + 44 + 22
    c = o + 60
    dn = P.get('cta_dn', 21)                       # v02: Founders 36 c (1,2 s) en vez de 21 (pedido de Roma, +0,5 s)
    fin = c + P['planos'][-1]['nf'] - 1            # el CTA queda hasta el último cuadro (v01: c + 50)
    return [
        dict(id='bf', tipo='chip', fs=66, n=(o, o + 59), y=300, lineas=[['Black', 'Friday', '·', PCT]], cad=3, golpe='agudo',
             acento=[PCT], guion='Black Friday · −25 %'),
        dict(id='precio', tipo='grande', fs=160, n=(o + 15, o + 59), y=y1, lineas=[['$48.750']], cad=0, golpe='acento',
             guion='$48.750'),
        dict(id='antes', tipo='atrib', fs=44, n=(o + 21, o + 59), y=y3, lineas=[['antes', '$65.000']], cad=0, guion='antes $65.000'),
        dict(id='placa_remera', tipo='chip', fs=66, n=(o + 27, o + 59), y=y4, lineas=[['La', 'placa', 'viene'], ['con', 'la', 'remera.']],
             cad=3, guion='La placa viene con la remera.'),
        # control del primer render: con cad 2 el renglón quedaba completo solo 7 c (c+14–c+20) antes del CTA. Ahora entra
        # entero en c (cad 0) y se lee los 0,7 s del guion. Apilado con el CTA hasta el final se probó y se descartó: en
        # c+52–c+59 la cámara sube y el CTA tapa la parte de arriba del bordado «RO».
        dict(id='founders', tipo='chip', fs=76, n=(c, c + dn - 1), y=396, lineas=[['Va', 'a', 'haber', '100', 'Founders'], ['como', 'máximo']],
             cad=0, acento=['100'], guion='Va a haber 100 Founders como máximo'),
        dict(id='cta', tipo='chip', fs=76, n=(c + dn, fin), y=396, lineas=[['Conseguí', 'la', 'tuya'], ['en', 'rocce.shop']], cad=3,
             golpe='acento', acento=['rocce.shop'], guion='Conseguí la tuya en rocce.shop'),
        dict(id='bf_cta', tipo='chip', fs=48, n=(c + dn, fin), y=396 + 2 * lh_chip(76) + 14, lineas=[['Black', 'Friday', '·', PCT]],
             cad=0, pop=False, acento=[PCT], guion='Black Friday · −25 %'),
    ]


def frases_voz(y, fs, lh, tarjetas=None, atrib=None):
    vz = P['voz']
    ap = [cuadro_voz(t) for _, t in vz['palabras']]
    ws = [w for w, _ in vz['palabras']]
    assert ' '.join(ws) == vz['texto'], (' '.join(ws), vz['texto'])
    lineas, k = [], 0
    for nw in vz['renglones']:
        lineas.append(list(zip(ws[k:k + nw], ap[k:k + nw]))); k += nw
    grupos = [lineas] if not tarjetas else []
    if tarjetas:
        k = 0
        for nr in tarjetas:
            grupos.append(lineas[k:k + nr]); k += nr
    fin = P['negro'][0] - 1 if P['pieza'] == 'v7' else 395
    out = []
    for i, g in enumerate(grupos):
        n0 = g[0][0][1]
        n1 = (grupos[i + 1][0][0][1] - 1) if i + 1 < len(grupos) else fin
        f = dict(id=f'voz{i + 1}', tipo='cita', fs=fs, lh=lh, cls='lh', n=(n0, n1), y=y, cad=0,
                 lineas=[[w for w, _ in ln] for ln in g], aparece=[a for ln in g for _, a in ln],
                 acento=['seguí'], guion=' '.join(w for ln in g for w, _ in ln))
        if i == len(grupos) - 1:
            f.update(golpe='sub', golpe_n=vz['sub_golpe'])
        out.append(f)
    if atrib:
        out.append(dict(atrib, id='atrib_voz', tipo='atrib', n=(ap[0], fin), cad=0))
    return out


def frases_v6():
    clubes = ['Oxford', 'Sheffield', 'Rotherham', 'Wolves', 'Getafe', 'Reading']
    fr = [
        dict(id='rotulo', tipo='label', n=(0, 41), y=270, lineas=[['DIBU', 'MARTÍNEZ']], cad=0, pop=False, guion='DIBU MARTÍNEZ'),
        dict(id='gancho', tipo='chip', fs=92, n=(0, 17), y=338, lineas=[['10', 'años', 'en', 'el', 'Arsenal.'], ['39', 'partidos.']],
             cad=0, pop=False, guion='10 años en el Arsenal. 39 partidos.'),
        dict(id='pregunta', tipo='grande', fs=116, n=(18, 41), y=360, lineas=[['¿Le', 'llega?']], cad=3, golpe='slam',
             guion='¿Le llega?'),
    ]
    for i, c in enumerate(clubes):
        fr.append(dict(id=f'club{i + 1}', tipo='chip', n=(42 + 6 * i, 47 + 6 * i if i < 5 else 89), y=300, lineas=[[c]], cad=0,
                       guion=c))
    fr += [
        dict(id='prestamos', tipo='grande', fs=102, n=(78, 89), y=300 + CHIP + 26, lineas=[['Seis', 'préstamos.']], cad=0,
             golpe='grave', guion='Seis préstamos.'),
        dict(id='debut', tipo='chip', n=(90, 119), y=300, lineas=[['28', 'años:', 'debuta'], ['en', 'la', 'Selección.']], cad=2,
             golpe='agudo', acento=['28', 'años:'], guion='28 años: debuta en la Selección.'),
        dict(id='covid', tipo='chip', n=(105, 119), y=300 + 2 * CHIP + 14, lineas=[['Entra', 'porque', 'Armani'], ['tiene', 'COVID.']],
             cad=2, golpe='grave', guion='Entra porque Armani tiene COVID.'),
        dict(id='penales', tipo='chip', n=(120, 146), y=300, lineas=[['Un', 'mes', 'después:'], ['ataja', 'tres', 'penales.']], cad=3,
             golpe='agudo', acento=['Un', 'mes', 'después:'], guion='Un mes después: ataja tres penales.'),
        dict(id='final', tipo='chip', n=(147, 170), y=300, lineas=[['Final', 'del', 'Mundial.']], cad=3, guion='Final del Mundial.'),
        dict(id='min123', tipo='chip', n=(159, 170), y=300 + CHIP + 14, lineas=[['Minuto', '123.', '3-3.']], cad=3,
             acento=['123.'], guion='Minuto 123. 3-3.'),
        dict(id='mano', tipo='chip', n=(171, 203), y=300, lineas=[['Mano', 'a', 'mano.']], cad=3, guion='Mano a mano.'),
    ]
    fr += frases_voz(600, 74, 84, atrib=dict(fs=34, y=1040, lineas=[['—', 'Emiliano', '“Dibu”', 'Martínez'],
                                                                    ['ESPN', '·', 'TikTok', '@espnargentina', '·', '09/06/2026']],
                                              guion='— Emiliano “Dibu” Martínez · ESPN · TikTok @espnargentina · 09/06/2026'))
    fr.append(dict(id='campeon', tipo='chip', n=(396, 437), y=300, lineas=[['Campeón', 'del', 'mundo.']], cad=3, golpe='acento',
                   guion='Campeón del mundo.'))
    return fr + frases_oferta(519), [(1, 6, 'impacto del gancho (c0 queda quieto para la portada)'),
                                     (204, 8, 'golpe y color: entra su voz'), (396, 10, 'drop de «Campeón del mundo.»')]


# en un renglón no entra en 1080 px con la letra del rótulo (40 px): se cortaba en «…PARTIDO EN LA». Dos renglones con la
# misma letra; el segundo (y 330–390) queda sobre el pelo, arriba de la cara
ROTULO2_V02 = [['COPA', 'AMÉRICA', '2024', '·', 'SU', 'ÚLTIMO', 'PARTIDO'], ['EN', 'LA', 'SELECCIÓN']]


def frases_v7():
    v01 = P['version'] == 'v01'
    fr = [
        dict(id='rotulo', tipo='label', n=(0, 41), y=270, lineas=[['ÁNGEL', 'DI', 'MARÍA']], cad=0, pop=False, guion='ÁNGEL DI MARÍA'),
        dict(id='gancho', tipo='chip', fs=92, n=(0, 17), y=338, lineas=[['2014:', 'lesionado,'], ['se', 'pierde', 'la', 'final.']],
             cad=0, pop=False, acento=['2014:'], guion='2014: lesionado, se pierde la final.'),
        dict(id='pregunta', tipo='grande', fs=116, n=(18, 41), y=360, lineas=[['¿Algún', 'día'], ['le', 'toca?']], cad=3, golpe='slam',
             guion='¿Algún día le toca?'),
        dict(id='e1', tipo='chip', n=(42, 62), y=300, lineas=[['2015:', 'sale', 'lesionado'], ['a', 'los', '28’.']], cad=2,
             golpe='grave', acento=['2015:'], guion='2015: sale lesionado a los 28’.'),
        dict(id='e2a', tipo='chip', n=(63, 83), y=300, lineas=[['2016:', 'llega', 'tocado.']], cad=2, golpe='grave', acento=['2016:'],
             guion='2016: llega tocado.'),
        dict(id='e2b', tipo='chip', n=(74, 83), y=300 + CHIP + 14, lineas=[['Sale', 'a', 'los', '57’.']], cad=2, golpe='grave',
             guion='Sale a los 57’.'),
        dict(id='e3a', tipo='chip', n=(84, 104), y=300, lineas=[['Tres', 'finales.']], cad=3, golpe='grave', guion='Tres finales.'),
        dict(id='e3b', tipo='grande', fs=102, n=(95, 104), y=300 + CHIP + 26, lineas=[['Tres', 'derrotas.']], cad=0, golpe='grave',
             guion='Tres derrotas.'),
        dict(id='p1a', tipo='chip', n=(105, 134), y=300, lineas=[['2021:', 'otra', 'final.']], cad=3, golpe='agudo', acento=['2021:'],
             guion='2021: otra final.') if v01 else
        dict(id='p1a', tipo='chip', n=(105, 134), y=300, lineas=[['2021']], cad=0, golpe='agudo', acento=['2021'], guion='2021'),
        dict(id='p1b', tipo='chip', n=(120, 134), y=300 + CHIP + 14, lineas=[['En', 'el', 'Maracaná,'], ['como', 'en', '2014.']],
             cad=2, golpe='agudo', guion='En el Maracaná, como en 2014.'),
        dict(id='p2', tipo='chip', n=(135, 161), y=300, lineas=[['Queda', 'solo.']], cad=3, golpe='agudo', guion='Queda solo.') if v01 else
        dict(id='p2', tipo='chip', n=(135, 161), y=300, lineas=[['Solo.']], cad=0, golpe='agudo', guion='Solo.'),
        dict(id='gol1', tipo='grande', fs=150, n=(214, 221), y=360, lineas=[['Gol.']], cad=0, golpe='impacto', guion='Gol.'),
        dict(id='r1a', tipo='chip', n=(222, 269), y=300, lineas=[['Campeón', 'de', 'América.']], cad=3, guion='Campeón de América.'),
        dict(id='r1b', tipo='chip', n=(246, 269), y=300 + CHIP + 14, lineas=[['Le', 'faltaba'], ['la', 'del', 'Mundial.']], cad=3,
             golpe='acento', guion='Le faltaba la del Mundial.'),
        dict(id='c2', tipo='chip', n=(270, 296), y=300, lineas=[['2022:', 'final', 'del', 'Mundial.']], cad=3, golpe='grave',
             acento=['2022:'], guion='2022: final del Mundial.'),
        dict(id='gol2', tipo='grande', fs=150, n=(312, 326), y=360, lineas=[['Gol.']], cad=0, golpe='impacto', guion='Gol.'),
        dict(id='r2', tipo='chip', n=(327, 350), y=300, lineas=[['Campeón', 'del', 'mundo.']], cad=3, golpe='acento',
             guion='Campeón del mundo.'),
        dict(id='rotulo2', tipo='label', n=(351, 390), y=270, lineas=[['COPA', 'AMÉRICA', '2024', '·', 'SU', 'ÚLTIMO', 'PARTIDO']],
             cad=0, pop=False, guion='COPA AMÉRICA 2024 · SU ÚLTIMO PARTIDO') if v01 else
        dict(id='rotulo2', tipo='label', n=(351, 390), y=270, lineas=ROTULO2_V02, cad=0, pop=False,
             guion='COPA AMÉRICA 2024 · SU ÚLTIMO PARTIDO EN LA SELECCIÓN'),
    ]
    fr += frases_voz(1150, 88, 100, tarjetas=P['voz']['tarjetas'],
                     atrib=dict(fs=32, y=1466, lineas=[['—', 'Ángel', 'Di', 'María', '·', 'TikTok', '@afaseleccion', '·', '16/07/2024']],
                                guion='— Ángel Di María · TikTok @afaseleccion · 16/07/2024'))
    return fr + frases_oferta(609), [(1, 6, 'impacto del gancho (c0 queda quieto para la portada)')]


CSS_EXTRA = """
.cita.lh .linea{line-height:var(--lh);height:var(--lh)} .cita.lh .w{line-height:var(--lh)}
.cita .w.ac{color:%(CEL)s}
"""


def preparar_textos():
    fr, extra = frases_v6() if P['pieza'] == 'v6' else frases_v7()
    M.FRASES = fr
    M.GOLPES_EXTRA = extra
    return fr


def etapa_textos():
    fr = preparar_textos()
    TX = TP / 'textos'; TX.mkdir(parents=True, exist_ok=True)
    sp = M.spec_texto()
    for f, g in zip(fr, sp['frases']):
        assert f['id'] == g['id']
        if f.get('cls'):
            g['cls'] = f['cls']
        if f.get('lh'):
            g['lh'] = f['lh']
    js = M.JS_TEXTO
    a = "d.className = 'frase ' + f.tipo;"
    b = "d.style.setProperty('--fs', f.fs + 'px');"
    assert js.count(a) == 1 and js.count(b) == 1
    js = js.replace(a, "d.className = 'frase ' + f.tipo + (f.cls ? ' ' + f.cls : '');")
    js = js.replace(b, b + " if (f.lh) d.style.setProperty('--lh', f.lh + 'px');")
    css = M.CSS_TEXTO % dict(F=L2.FUENTES, CEL=CEL, LHC=M.LH_CITA) + CSS_EXTRA % dict(CEL=CEL)
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body><div id="raiz"></div>'
            f'<script>{js.replace("__SPEC__", json.dumps(sp, ensure_ascii=False))}</script></body></html>')
    (TX / 'texto.html').write_text(html, encoding='utf-8')
    jdump(dict(sp, guion={f['id']: f.get('guion') for f in fr}), TX / 'spec_texto.json')
    sec = TX / 'cuadros'
    if sec.exists():
        shutil.rmtree(sec)
    ult = max(f['n'][1] for f in fr)
    trabajo = dict(html=str(TX / 'texto.html'), outdir=str(sec), n0=0, n1=ult, w=W, h=H, dump=str(TX / 'visible.json'))
    (TX / '_trabajo.json').write_text(json.dumps(trabajo, indent=1))
    subprocess.run(nice(['node', str(R / 'scripts/life/life_v4_render.js'), str(TX / '_trabajo.json')]), check=True)
    n = len(list(sec.glob('f_*.png')))
    assert n == ult + 1, n
    # texto exacto: cada frase completa, tal como quedó visible, contra el guion corregido
    vis = json.load(open(TX / 'visible.json'))['cuadros']
    comp = {}
    for f in fr:
        v = [x for x in vis[str(f['n'][1])] if x['id'] == f['id']][0]
        txt = ' '.join(v['lineas']).replace(NB, ' ')
        comp[f['id']] = dict(visible=txt, guion=f.get('guion'), igual=txt == (f.get('guion') or '').replace(NB, ' '))
    jdump(comp, TX / 'textos_vs_guion.json')
    mal = {k: v for k, v in comp.items() if not v['igual']}
    print('textos', n, 'distintos del guion:', mal or 'ninguno')


# =====================================================================================================================
# cierre · frases de la placa (Instrument Serif, CSS_PLACA de life_v2) y firma con el logo original
# =====================================================================================================================
def etapa_placa():
    PL = TP / 'placa'; PL.mkdir(parents=True, exist_ok=True)
    t = dict(F=L2.FUENTES, fs=84, logo=96, radio=round(96 * 0.11), ffs=30)
    suyo = 'minuto 123' if P['pieza'] == 'v6' else 'copa'
    L = [f'Él tiene su <em>{suyo}</em>.', 'Esta placa significa lo mismo:',
         f'<span style="color:{CEL}">seguir</span> hasta <em>lograrlo</em>.']
    tops = [300, 410, 520]
    docs = {}
    for i in range(3):
        docs[f'cierre_{i + 1}'] = ''.join(f'<div class="frase" style="top:{tops[j]}px">{L[j]}</div>' for j in range(i + 1))
    docs['firma'] = (f'<div class="firma" style="top:280px"><img src="file://{L2.LOGO}"><span>ROCCÉ LIFE</span></div>')
    trabajos = []
    for nombre, cuerpo in docs.items():
        h = PL / f'{nombre}.html'
        h.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{L2.CSS_PLACA % t}</style></head>'
                     f'<body>{cuerpo}</body></html>', encoding='utf-8')
        trabajos.append(dict(html=str(h), out=str(PL / f'{nombre}.png'), w=W, h=H))
    (PL / '_trabajos.json').write_text(json.dumps(trabajos, indent=1))
    subprocess.run(nice(['node', str(R / 'scripts/life/life_v2_render.js'), str(PL / '_trabajos.json')]), check=True)
    from PIL import Image
    rep = {}
    for tr in trabajos:
        a = np.asarray(Image.open(tr['out']))
        assert a.shape == (H, W, 4)
        al = a[..., 3]; fil = np.nonzero((al > 8).any(1))[0]; col = np.nonzero((al > 8).any(0))[0]
        rep[Path(tr['out']).name] = dict(md5_pixeles=hashlib.md5(a.tobytes()).hexdigest(),
                                         caja_alfa_gt8=[int(col.min()), int(fil.min()), int(col.max()), int(fil.max())])
    a = np.asarray(Image.open(PL / 'firma.png')).astype(int)
    ys, xs = np.nonzero((a[..., 3] > 250) & (a[..., :3].min(-1) >= 250))
    rep['ficha_logo'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    o = P['negro'][1] + 1
    # la firma entra con el CTA: 78 c de placa + 60 de oferta + cta_dn (v01 21, v02 36: Founders +0,5 s)
    rep['cuadros'] = dict(cierre_1=[o, o + 17], cierre_2=[o + 18, o + 41], cierre_3=[o + 42, o + 77],
                          firma=[o + 138 + P.get('cta_dn', 21), P['NF'] - 1])
    rep['texto'] = [re_txt(x) for x in L]
    jdump(rep, PL / 'placa.json')
    print(json.dumps(rep, ensure_ascii=False))


def re_txt(h):
    import re
    return re.sub('<[^>]+>', '', h)


# =====================================================================================================================
# audio · golpes y música TEMP propia del sistema V4 (sonido.Mezcla, M.golpe_grave/agudo, M.sub_golpe, M.latido,
# M.agachar), ambiente de estadio sintetizado (el sonido de los clips trae relato o música: no se usa), su voz real con
# el fondo que cede por envolvente (A.envolvente), mezcla previa A.pre_mezcla y limitador A.limitar (level=false)
# =====================================================================================================================
DUCK_DB = 6.0            # cuánto cede el colchón bajo cada frase (envolvente de la voz)
OBJ_VOZ = {'completa': (11.0, 14.0, 12.5), 'sinmusica': (13.0, 15.0, 14.0)}   # voz sobre el fondo: mín, máx, objetivo


def tf(n):
    return n / FPS


def rumor(m, t0, t1, g=0.035, brillo=2600, ini=0.25, fin=0.25):
    """murmullo de estadio sintetizado: ruido en banda (300 Hz–brillo) con modulación lenta, dos canales distintos;
    no tiene voces ni palabras (no puede adelantarse a la voz del deportista)."""
    S_ = M._s()
    L = int((t1 - t0) * SR)
    if L <= 0:
        return
    tt = np.arange(L) / SR
    out = np.zeros((L, 2))
    for c in range(2):
        n = S_.filt(S_.ruido(L), 'band', [300, brillo])
        lfo = S_.filt(S_.ruido(L), 'low', 2.5)
        lfo = lfo / (np.abs(lfo).max() + 1e-9)
        out[:, c] = n / (np.abs(n).max() + 1e-9) * (0.75 + 0.25 * lfo)
    e = np.ones(L)
    ki, kf = int(ini * SR), int(fin * SR)
    e[:ki] = np.linspace(0, 1, ki); e[L - kf:] = np.minimum(e[L - kf:], np.linspace(1, 0, kf))
    m.put('amb', out * e[:, None], t0, g)
    m.log(t0, f'murmullo de estadio sintetizado {t0:.2f}–{t1:.2f} s')


def grito(m, t, g=0.11, dur=2.4):
    """el estadio que explota (sintetizado): banda ancha que sube en 0,12 s y cae en ≈ dur."""
    S_ = M._s()
    L = int(dur * SR); tt = np.arange(L) / SR
    out = np.zeros((L, 2))
    e = (1 - np.exp(-tt / 0.06)) * np.exp(-np.maximum(0, tt - 0.25) / (dur / 3.2))
    for c in range(2):
        n = S_.filt(S_.ruido(L), 'band', [350, 4200]) + 0.35 * S_.filt(S_.ruido(L), 'band', [1800, 6500])
        out[:, c] = n / (np.abs(n).max() + 1e-9) * e
    m.put('amb', out, t, g)
    m.log(t, 'estadio que explota (sintetizado)')


def sfx_texto(m):
    """un sonido por golpe de texto (fuente única: las frases), como B v02. v02: el golpe que cae un cuadro antes del
    grito del narrador va a ×0,6 (pedido de Roma: el grito no coincide con un golpe fuerte)."""
    golpes, _ = M.eventos_texto()
    kg = P.get('golpe_grito')
    cg = P['narracion']['grito_cuadro'] - 1 if kg else None
    for n, tipo, _id in golpes:
        t = tf(n)
        if kg and n == cg:
            if tipo == 'impacto':
                m.impacto(t, 0.80 * kg); M.golpe_grave(m, t, 0.55 * kg)
                m.log(t, f'golpe del grito ×{kg} (un cuadro antes del grito)')
                continue
            raise SystemExit(f'golpe {tipo} en el cuadro del grito: falta definir su escala')
        if tipo == 'grave':
            M.golpe_grave(m, t)
        elif tipo == 'agudo':
            M.golpe_agudo(m, t)
        elif tipo == 'impacto':
            m.impacto(t, 0.80); M.golpe_grave(m, t, 0.55)
        elif tipo == 'sub':
            M.sub_golpe(m, t)
        elif tipo == 'acento':
            m.toque(t, 0.16, 2400)
    return golpes


def cierre_sonido(m, o, con):
    """placa, oferta y CTA (o = primer cuadro después del negro): pad, golpe suave en el foco de la placa, cadencia."""
    t0 = tf(o)
    M.sub_golpe(m, t0 + 1.0, 0.30)                                # IMG_5359 entra en foco ≈ 1,0 s después del corte
    m.barrido(tf(o + 78), 0.30, 0.12); m.barrido(tf(o + 138), 0.30, 0.12)
    if not con:
        return
    m.pad(t0, [38, 45, 50, 53, 57], 2.6, .045, 1200, a=.3)
    m.campana(t0 + 1.0, 81, .05)
    tb = tf(o + 78)
    for i in range(7):
        t = tb + 0.6 * i
        if t > tf(P['NF']) - 0.35:
            break
        m.bombo(t, 0.85 if i % 2 == 0 else 0.7)
        if i % 2 == 1:
            m.palma(t, 0.22)
        m.ocho08(t, [41, 41, 46, 46, 43, 43, 38][i], 0.5, 0.45)
    m.pad(tb, [41, 48, 53, 57], 2.0, .05, 1500); m.pad(tf(o + 138), [46, 50, 53, 58], P.get('pad_cta', 1.7), .05, 1500)
    for t in np.arange(tb, tf(P['NF']) - 0.4, 0.3):
        m.charles(round(float(t), 3), .07)


def mezcla_v6(con):
    from sonido import Mezcla
    m = Mezcla(P['NF'] / FPS)
    rumor(m, 0.0, 13.25, 0.030); grito(m, 13.20, 0.10, 1.6); rumor(m, 13.20, 14.60, 0.040, 3200, ini=0.05, fin=0.05)
    m.impacto(0.0, 0.70); M.golpe_grave(m, 0.0, 0.6)
    m.barrido(0.62, 0.30, 0.12); m.subida(0.60, 1.333, 0.20)
    for i in range(6):
        m.toque(tf(42 + 6 * i), 0.10, 1800)                       # un clic por club
    golpes = sfx_texto(m)
    m.subida(5.00, 5.67, 0.16)                                    # «Minuto 123. 3-3.»: SUBE
    M.golpe_grave(m, tf(204), 0.75)                               # golpe y color: entra su voz
    m.impacto(tf(396), 0.55)                                      # drop de «Campeón del mundo.»
    kg = P.get('golpe_grito')
    t123, k123 = (tf(P['narracion']['grito_cuadro'] - 1), kg) if kg else (5.30, 1.0)
    if con:
        m.pad(1.40, [38, 45, 50, 53], 1.55, .055, 650, a=.05)
        m.pad(3.00, [41, 48, 53, 57, 60], 0.45, .055, 1500, a=.03)
        m.pad(3.50, [38, 45, 50], 0.45, .040, 500, a=.03)
        m.pad(4.00, [46, 53, 58, 62], 0.85, .055, 1500, a=.03)
        m.pad(4.90, [38, 45, 50, 53], 0.40, .050, 650, a=.03)
        m.pad(t123, [41, 48, 53, 57, 60, 64], 0.40, .060 * k123, 2000, a=.01)
        m.pad(5.70, [38, 45, 50], 0.80, .040, 500, a=.03)
        for t, g in ((1.40, .8), (2.20, .8), (3.00, .75), (3.50, .7), (4.00, .75), (4.90, .8), (t123, .7 * k123), (5.70, .8),
                     (6.10, .85)):
            M.latido(m, t, g, doble=(t not in (3.50, 6.10)))
        if kg:
            m.log(t123, f'golpe del 123 (latido y acorde de 5,30) un cuadro antes del grito, ×{kg}')
    for p_ in ('mus', 'bombo', 'fx'):
        m.silenciar(p_, 6.50, 6.80, rampa=0.008)                   # la música se corta en 6,50: solo ambiente
    if con:
        m.pad(6.80, [38, 45, 50, 52, 57], 6.30, .035, 800, a=.6, r=.3)
        ch = lambda t0, t1, g=.08: [m.charles(round(float(t), 3), g) for t in np.arange(t0, t1 - 1e-6, 0.3)]
        m.bombo(13.20, 1.0); m.ocho08(13.20, 38, .55, .55, glide_desde=45); m.pad(13.20, [50, 53, 57, 62], .55, .06, 1600)
        m.campana(13.20, 74, .06); m.campana(13.50, 81, .05)
        m.bombo(13.80, .85); m.palma(13.80); m.pad(13.80, [46, 50, 53, 58], .55, .06, 1600); m.ocho08(13.80, 34, .5, .5)
        m.bombo(14.40, .8); ch(13.20, 14.55)
    for p_ in ('amb', 'mus', 'bombo', 'fx'):
        m.silenciar(p_, tf(438), tf(441), rampa=0.02)              # negro de 3 cuadros
    cierre_sonido(m, 441, con)
    return m, golpes


def mezcla_v7(con):
    from sonido import Mezcla
    m = Mezcla(P['NF'] / FPS)
    rumor(m, 0.0, 7.20, 0.030); grito(m, tf(214), 0.12, 2.6); rumor(m, 7.10, 9.05, 0.045, 3400, ini=0.05)
    rumor(m, 9.00, 10.45, 0.028); grito(m, tf(312), 0.11, 2.2); rumor(m, 10.40, 17.65, 0.034, 3000, ini=0.05)
    m.impacto(0.0, 0.70); M.golpe_grave(m, 0.0, 0.6)
    m.barrido(0.62, 0.30, 0.12); m.subida(0.60, 1.333, 0.20)
    golpes = sfx_texto(m)
    m.subida(9.95, tf(312), 0.18)                                 # antes del remate de 2022
    if con:
        m.pad(1.40, [38, 45, 50, 53], 0.70, .055, 650, a=.05)
        m.pad(2.10, [38, 45, 50, 53], 0.70, .050, 600, a=.05)
        m.pad(2.80, [38, 45, 50], 0.70, .028, 450, a=.05)           # la música baja
        m.pad(3.50, [41, 48, 53, 57, 60], 0.95, .055, 1500, a=.03)
        m.pad(4.50, [46, 53, 58, 62], 0.85, .055, 1500, a=.03)
        for t, g in ((1.40, .8), (2.10, .8), (2.45, .6), (2.80, .5), (3.50, .75), (4.00, .75), (4.50, .8), (4.95, .8)):
            M.latido(m, t, g, doble=(t not in (2.45, 4.95)))
    for p_ in ('mus', 'fx'):
        m.silenciar(p_, 5.40, tf(214) - 0.01, rampa=0.008)        # la música se corta en 5,40: ambiente + pulso
    if con:
        for t, g in ((5.40, .7), (5.90, .7), (6.33, .75), (6.70, .8), (6.98, .85)):
            M.latido(m, t, g, doble=False)
        ch = lambda t0, t1, g=.08: [m.charles(round(float(t), 3), g) for t in np.arange(t0, t1 - 1e-6, 0.3)]
        g1 = tf(214)
        m.bombo(g1, 1.0 * P.get('golpe_grito', 1.0)); m.ocho08(g1, 38, .55, .55, glide_desde=45); m.pad(g1, [50, 53, 57, 62], 1.1, .06, 1800)
        m.campana(g1, 74, .06); m.campana(g1 + 0.3, 81, .05)
        for i, t in enumerate(np.arange(g1 + 0.6, 8.99, 0.6)):
            m.bombo(float(t), .85); m.palma(float(t), .25) if i % 2 == 0 else None
            m.ocho08(float(t), [34, 36, 41][i % 3], .5, .5)
        m.pad(tf(246), [46, 50, 53, 58], 0.75, .055, 1600)
        ch(g1, 8.99)
        m.pad(9.00, [38, 45, 50], 1.35, .035, 500, a=.05)          # 2022: la música baja
        for t, g in ((9.00, .75), (9.45, .7), (9.90, .75)):
            M.latido(m, t, g, doble=False)
        g2 = tf(312)
        m.bombo(g2, 1.0); m.ocho08(g2, 41, .5, .55, glide_desde=46); m.pad(g2, [53, 57, 60, 65], .5, .06, 1800)
        m.bombo(10.90, .9); m.palma(10.90); m.pad(10.90, [50, 53, 57, 62, 65], 0.80, .065, 2000, r=.5)   # se abre
        m.campana(10.90, 77, .06); ch(g2, 11.65)
        m.pad(11.70, [38, 45, 50, 52, 57], 5.90, .035, 800, a=.6, r=.3)
    for p_ in ('amb', 'mus', 'bombo', 'fx'):
        m.silenciar(p_, tf(528), tf(531), rampa=0.02)              # negro de 3 cuadros
    cierre_sonido(m, 531, con)
    return m, golpes


def cola_fx_bajo_voz(m):
    """la pista de efectos (golpes y la reverberación de golpes y colchones) baja 24 dB desde 0,05 s antes de la primera
    palabra hasta 0,06 s antes del sub-golpe: la cola del golpe de entrada tapaba «le bloqueo toda» (medido en v01)."""
    vz = P['voz']
    t0 = vz['palabras'][0][1] - vz['src0'] + vz['m0'] - 0.05
    t1 = tf(vz['sub_golpe']) - 0.06
    g = np.ones(m.N); i0, i1 = int((t0 - 0.06) * SR), int(t0 * SR); i2, i3 = int(t1 * SR), int((t1 + 0.02) * SR)
    lo = 10 ** (-24 / 20)
    g[i0:i1] = np.linspace(1, lo, i1 - i0); g[i1:i2] = lo; g[i2:i3] = np.linspace(lo, 1, i3 - i2)
    m.pistas['fx'] *= g[:, None]
    m.log(t0, f'efectos −24 dB bajo la voz hasta {t1:.2f} s')


def cama_bajo_voz(m, db_):
    """ganancia del colchón (ambiente y música) mientras suena la voz, para dejarla 10–15 dB arriba del fondo."""
    if abs(db_) < 1e-6:
        return
    vz = P['voz']
    t0 = vz['m0']; t1 = vz['m0'] + (vz['src1'] - vz['src0']) + 0.25
    g = np.ones(m.N); i0, i1 = int(t0 * SR), int(t1 * SR); k = int(0.15 * SR)
    v = 10 ** (db_ / 20)
    g[i0:i1] = v; g[i0 - k:i0] = np.linspace(1, v, k); g[i1:i1 + k] = np.linspace(v, 1, k)
    for p_ in ('amb', 'mus'):
        m.pistas[p_] *= g[:, None]


def voz_al_mix(m, gan_db):
    import soundfile as sf
    x, sr = sf.read(str(T3 / P['pieza'] / 'voz' / 'voz_48k.wav'))      # v02 usa el mismo corte de v01
    assert sr == SR
    act = [np.sqrt((x[i:i + 2400] ** 2).mean()) for i in range(0, len(x) - 2400, 2400)]
    ref = 20 * math.log10(np.median([a for a in act if a > max(act) * 0.1]) + 1e-12)
    g = 10 ** ((-20.0 - ref + gan_db) / 20)                      # habla a −20 dBFS (mediana de 50 ms) + ajuste
    i0 = int(round(P['voz']['m0'] * SR))
    voz = np.zeros(m.N); voz[i0:i0 + len(x)] = x * g
    m.pistas['voz'][:, 0] += voz * math.sqrt(0.5); m.pistas['voz'][:, 1] += voz * math.sqrt(0.5)
    e = np.zeros(m.N); e[i0:i0 + len(x)] = A.envolvente(x, sr)
    j = i0 + len(x); cola = int(0.25 * sr)
    e[j:j + cola] = e[j - 1] * np.exp(-np.arange(cola) / (0.08 * sr))
    duck = 10 ** (-DUCK_DB * e / 20)
    for p_ in ('amb', 'mus', 'bombo'):
        m.pistas[p_] *= duck[:, None]
    m.log(P['voz']['m0'], f"voz real ({P['voz']['clip']}, {P['voz']['src0']:.3f}–{P['voz']['src1']:.3f} s); fondo cede {DUCK_DB} dB")
    return voz, e, round(ref, 1), round(20 * math.log10(g), 2)


def voz_vs_fondo(m, voz, e):
    sr = SR
    fondo = (m.pistas['amb'] + m.pistas['fx'] + m.pistas['mus'] + m.pistas['bombo']).mean(1)
    w = int(0.05 * sr); filas = []
    i0 = int(P['voz']['m0'] * sr); i1 = i0 + int((P['voz']['src1'] - P['voz']['src0']) * sr)
    vs = [20 * math.log10(np.sqrt(((voz[i:i + w] * math.sqrt(0.5)) ** 2).mean()) + 1e-12) for i in range(i0, i1 - w, w)]
    med = float(np.median([v for v in vs if v > max(vs) - 30]))
    for j, i in enumerate(range(i0, i1 - w, w)):
        # ventanas de habla: envolvente arriba de 0,9 y la voz a menos de 10 dB de su mediana (no las pausas)
        if e[i:i + w].min() > 0.9 and vs[j] >= med - 10:
            v = vs[j]
            f = 20 * math.log10(np.sqrt((fondo[i:i + w] ** 2).mean()) + 1e-12)
            filas.append(dict(t=round(i / sr, 2), voz_db=round(v, 1), fondo_db=round(f, 1), dif_db=round(v - f, 1)))
    d = [x['dif_db'] for x in filas]
    return dict(ventanas=len(filas), dif_mediana_db=round(float(np.median(d)), 1), dif_min_db=round(min(d), 1),
                dif_max_db=round(max(d), 1), por_ventana=filas)


DUCK_NARR = 12.0         # voz oficial: el fondo baja 12 dB con la narración (envolvente)


def niveles_narracion(frases, voz_real):
    """ganancia de cada frase: mezcla oficial (salida de la receta + voz baja +5 / grito y CTA +2) y, encima, la regla de
    la capa de Fede (±3 dB del resto): lo que queda a más de 3 dB de la mediana va al borde. La frase más fuerte queda
    1 dB bajo la voz real (sonoridad de habla) y ninguna supera su sonoridad momentánea máxima."""
    import soundfile as sf
    real = voz_real[np.abs(voz_real) > 0]
    L_real, M_real = sonoridad_habla(real), momentanea_max(real)
    v = {f['id']: f['sonoridad_habla_cruda'] + offset_oficial(f) for f in frases}
    med = float(np.median(list(v.values())))
    w = {k: min(max(x, med - 3.0), med + 3.0) for k, x in v.items()}
    sh = (L_real - 1.0) - max(w.values())
    g = {f['id']: w[f['id']] + sh - f['sonoridad_habla_cruda'] for f in frases}
    mom = {f['id']: momentanea_max(sf.read(f['wav'])[0] * 10 ** (g[f['id']] / 20)) for f in frases}
    exceso = max(mom.values()) - (M_real - 0.5)
    if exceso > 0:
        g = {k: x - exceso for k, x in g.items()}; mom = {k: x - exceso for k, x in mom.items()}
    return dict(voz_real_sonoridad_habla=L_real, voz_real_momentanea_max=M_real, mediana_oficial=round(med, 2),
                por_frase={f['id']: dict(cruda=f['sonoridad_habla_cruda'], offset_oficial=offset_oficial(f),
                                         llevada_al_borde_db=round(w[f['id']] - v[f['id']], 2), ganancia_db=round(g[f['id']], 2),
                                         sonoridad_habla_mezcla=round(f['sonoridad_habla_cruda'] + g[f['id']], 2),
                                         momentanea_max_mezcla=round(mom[f['id']], 2)) for f in frases})


def ventana(N, t0, t1, rampa):
    """0–1 con rampas lineales: 1 entre t0 y t1."""
    w = np.zeros(N); i0, i1 = int(t0 * SR), int(t1 * SR); k = max(1, int(rampa * SR))
    w[max(0, i0):min(N, i1)] = 1.0
    a = np.linspace(0, 1, k)
    j = np.arange(i0 - k, i0); ok = (j >= 0) & (j < N); w[j[ok]] = np.maximum(w[j[ok]], a[ok])
    j = np.arange(i1, i1 + k); ok = (j >= 0) & (j < N); w[j[ok]] = np.maximum(w[j[ok]], a[::-1][ok])
    return w


def narracion_al_mix(m, frases, niv, dips, tope_fx=None):
    """la narración en la pista de voz (mono al centro); el colchón (ambiente, música, bombo) cede DUCK_NARR por
    envolvente; los efectos bajan 6 dB mientras habla (los golpes que pisan una palabra, regla de la capa de Fede); y
    cada frase lleva su ajuste del fondo (dips, dB) para quedar 10–15 dB arriba."""
    import soundfile as sf
    narr, e = np.zeros(m.N), np.zeros(m.N)
    for f in frases:
        x = sf.read(f['wav'])[0] * 10 ** (niv['por_frase'][f['id']]['ganancia_db'] / 20)
        i0 = int(round(f['wav_entra_s'] * SR)); i1 = min(m.N, i0 + len(x))
        narr[i0:i1] += x[:i1 - i0]
        ee = A.envolvente(x, SR)[:i1 - i0]
        cola = int(0.25 * SR); j = np.arange(i1, min(m.N, i1 + cola))
        e[i0:i1] = np.maximum(e[i0:i1], ee); e[j] = np.maximum(e[j], ee[-1] * np.exp(-(j - i1) / (0.08 * SR)))
    m.pistas['voz'][:, 0] += narr * math.sqrt(0.5); m.pistas['voz'][:, 1] += narr * math.sqrt(0.5)
    duck = 10 ** (-DUCK_NARR * e / 20)
    for p_ in ('amb', 'mus', 'bombo'):
        m.pistas[p_] *= duck[:, None]
    fx6 = np.ones(m.N)
    for f in frases:
        a, b = f['habla_master_s']
        fx6 = np.minimum(fx6, 1 - (1 - 10 ** (-6 / 20)) * ventana(m.N, a - 0.03, b + 0.03, 0.015))
    m.pistas['fx'] *= fx6[:, None]
    # ajuste del fondo por frase. El colchón no vuelve entre frases cercanas (hueco < 1 s): cambia de un ajuste al otro
    # en la mitad del hueco (sin bombeo). Los efectos solo bajan mientras habla: los golpes entre frases quedan enteros
    gdb_c, gdb_fx = np.zeros(m.N), np.zeros(m.N)
    for i, f in enumerate(frases):
        dv = dips.get(f['id'], 0.0)
        if not dv:
            continue
        a, b = f['habla_master_s']; pre, post = 0.20, 0.30
        if i > 0 and a - frases[i - 1]['habla_master_s'][1] < 1.0:
            pre = (a - frases[i - 1]['habla_master_s'][1]) / 2
        if i + 1 < len(frases) and frases[i + 1]['habla_master_s'][0] - b < 1.0:
            post = (frases[i + 1]['habla_master_s'][0] - b) / 2
        w = ventana(m.N, a - pre, b + post, 0.06)
        gdb_c = gdb_c * (1 - w) + dv * w
        w = ventana(m.N, a - 0.02, b + 0.03, 0.015)
        gdb_fx = gdb_fx * (1 - w) + min(dv, (tope_fx or {}).get(f['id'], 0.0)) * w     # efectos: como mucho, su nivel de v01
    for p_ in ('amb', 'mus', 'bombo'):
        m.pistas[p_] *= (10 ** (gdb_c / 20))[:, None]
    m.pistas['fx'] *= (10 ** (gdb_fx / 20))[:, None]
    m.log(frases[0]['habla_master_s'][0], f'narración: {len(frases)} frases; fondo cede {DUCK_NARR} dB, efectos −6 dB bajo las palabras')
    return narr, e


def narracion_vs_fondo(m, narr, e, frases):
    """por frase: narración contra todo el fondo (ambiente + efectos + música + bombo, sin la voz real), ventanas de
    50 ms de habla (envolvente > 0,9 y a menos de 10 dB de la mediana de la frase)."""
    fondo = (m.pistas['amb'] + m.pistas['fx'] + m.pistas['mus'] + m.pistas['bombo']).mean(1)
    w = int(0.05 * SR); out = {}
    for f in frases:
        a, b = f['habla_master_s']; i0, i1 = int(a * SR), int(b * SR)
        idx = list(range(i0, i1 - w, w))
        vs = [20 * math.log10(np.sqrt(((narr[i:i + w] * math.sqrt(0.5)) ** 2).mean()) + 1e-12) for i in idx]
        med = float(np.median(vs)); filas = []
        for j, i in enumerate(idx):
            if e[i:i + w].min() > 0.9 and vs[j] >= med - 10:
                fd = 20 * math.log10(np.sqrt((fondo[i:i + w] ** 2).mean()) + 1e-12)
                filas.append((vs[j], fd))
        d = [v_ - f_ for v_, f_ in filas]
        out[f['id']] = dict(ventanas=len(filas), dif_mediana_db=round(float(np.median(d)), 1), dif_min_db=round(min(d), 1),
                            dif_max_db=round(max(d), 1), fondo_mediana_dbfs=round(float(np.median([f_ for _, f_ in filas])), 1))
    return out


def offset_secciones(m, x_antes, x_despues):
    """v02: el fondo de las partes narradas baja parejo (ambiente, efectos, música y bombo), fuera de la cita: x_antes dB
    hasta 0,1 s antes del corte de la voz real (rampa de 0,4 s) y x_despues dB desde 0,05 s después del corte (rampa de
    0,3 s). Dentro de la cita no cambia nada (su colchón es el de v01)."""
    vz = P['voz']; c0, c1 = vz['m0'], vz['m0'] + (vz['src1'] - vz['src0'])
    t = np.arange(m.N) / SR
    g = np.where(t < c0, x_antes * np.clip((c0 - 0.1 - t) / 0.4, 0, 1), 0.0)
    g = np.where(t > c1, x_despues * np.clip((t - c1 - 0.05) / 0.3, 0, 1), g)
    for p_ in ('amb', 'fx', 'mus', 'bombo'):
        m.pistas[p_] *= (10 ** (g / 20))[:, None]


def limitar_aac(pre, salida, gan, tmp):
    """v02: el mismo alimiter (level=false), con un techo que baja 0,5 dB por vuelta hasta que el pico real del AAC (mismo
    codificador y parámetros que el máster) queda ≤ −1,2 dBTP; la ganancia se corrige en cada vuelta para −14 LUFS."""
    lim_db, hist = -1.6, []
    for _ in range(12):
        V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(pre), '-af',
              f'volume={gan:.2f}dB,alimiter=limit={10 ** (lim_db / 20):.4f}:level=false:attack=3:release=60:latency=1',
              '-c:a', 'pcm_f32le', str(salida)])
        V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(salida), '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000',
              '-ac', '2', str(tmp)])
        I, Pk, LRA = L2.medir_ebur(salida); Ia, Pa, _ = L2.medir_ebur(tmp)
        hist.append(dict(techo_dbfs=round(lim_db, 2), ganancia_db=round(gan, 2), lufs_wav=I, pico_wav=Pk, lufs_aac=Ia, pico_aac=Pa))
        if -14.5 <= Ia <= -13.5 and Pa <= -1.2:
            break
        if Pa > -1.2:
            lim_db -= 0.5
        gan += -14.0 - Ia
    return I, Pk, LRA, hist


def etapa_audio():
    preparar_textos()
    AU = TP / 'audio'; AU.mkdir(parents=True, exist_ok=True)
    out = {}
    if P.get('narracion'):
        nar = json.load(open(TP / 'narracion.json'))
        frases = nar['frases']
    for k, con in (('completa', True), ('sinmusica', False)):
        gan_voz, cama = 0.0, 0.0
        fija = None
        if P.get('reusar'):
            # v02: la voz real y el colchón bajo ella quedan con los valores de v01 (el montaje de la cita no cambia; si se
            # vuelve a iterar, el ruido sintético nuevo lleva a otro punto de convergencia: medido, +2 dB en V6)
            fija = json.load(open(T3 / P['reusar'] / 'audio' / 'audio.json'))[k]
        for _ in range(6):                                       # voz 10–15 dB sobre el fondo (objetivo 12,5)
            m, golpes = (mezcla_v6 if P['pieza'] == 'v6' else mezcla_v7)(con)
            for n, tipo, _id in golpes:
                if tipo in ('grave', 'impacto', 'sub'):
                    M.agachar(m, tf(n), -4.0, pistas=('amb',))
                    if con:
                        M.agachar(m, tf(n))
            fin = tf(P['NF'])
            for p_ in ('amb', 'mus', 'bombo', 'fx'):
                m.fundido(p_, fin - 0.40, fin)
            cola_fx_bajo_voz(m)
            if fija:
                import soundfile as sf
                xr, _ = sf.read(str(T3 / P['pieza'] / 'voz' / 'voz_48k.wav'))
                act = [np.sqrt((xr[i:i + 2400] ** 2).mean()) for i in range(0, len(xr) - 2400, 2400)]
                ref_ = 20 * math.log10(np.median([a_ for a_ in act if a_ > max(act) * 0.1]) + 1e-12)
                gan_voz = fija['voz_ganancia_db'] + 20.0 + ref_; cama = fija['colchon_bajo_voz_db']
            voz, e, ref, g_aplicada = voz_al_mix(m, gan_voz)
            cama_bajo_voz(m, cama)
            vf = voz_vs_fondo(m, voz, e)
            lo, hi, obj = OBJ_VOZ[k]
            if fija or lo <= vf['dif_mediana_db'] <= hi:
                break
            if vf['dif_mediana_db'] < lo:                        # la voz sube; si sobra, sube el colchón (la voz no baja)
                gan_voz += obj - vf['dif_mediana_db']
            else:
                cama += vf['dif_mediana_db'] - obj
        nres = None
        if P.get('narracion'):
            # v02: la narración entra sobre la mezcla con la voz real ya resuelta (no se pisan: ≥ 0,4 s de aire). El fondo
            # se ajusta frase por frase hasta dejar cada una 10–15 dB arriba (la narración no sube: queda bajo la voz real)
            niv = niveles_narracion(frases, voz)
            base = {p_: v_.copy() for p_, v_ in m.pistas.items()}
            lo, hi, obj = OBJ_VOZ[k]
            antes_ = [f['id'] for f in frases if f['habla_master_s'][1] < P['voz']['m0']]

            def resolver(xa, xd):
                dips = {f['id']: 0.0 for f in frases}
                for it in range(14):
                    m.pistas = {p_: v_.copy() for p_, v_ in base.items()}
                    offset_secciones(m, xa, xd)
                    narr, en = narracion_al_mix(m, frases, niv, dips, {f['id']: -(xa if f['id'] in antes_ else xd) for f in frases})
                    nf_ = narracion_vs_fondo(m, narr, en, frases)
                    cambio = False
                    for fid, r in nf_.items():
                        dm = r['dif_mediana_db']
                        if dm < lo and dips[fid] > -30.0:
                            dips[fid] = max(-30.0, dips[fid] - (obj - dm)); cambio = True
                        elif dm > hi and dips[fid] < DUCK_NARR - (xa if fid in antes_ else xd):
                            # puede devolver la envolvente y el offset de su sección (el colchón vuelve a su nivel de v01)
                            dips[fid] = min(DUCK_NARR - (xa if fid in antes_ else xd), dips[fid] + (dm - obj)); cambio = True
                    if not cambio:
                        break
                return dips, narr, en, nf_, it
            # primera pasada sin offset; el fondo de cada sección baja lo que pide la mediana de sus frases menos 6 dB
            # (lo que queda lo ajusta cada frase): así no hay saltos de 20–30 dB entre una frase y el hueco que sigue
            d0 = resolver(0.0, 0.0)[0]
            med = lambda ids: float(np.median([d0[i] for i in ids])) if ids else 0.0
            xa = round(min(0.0, med(antes_) + 6.0), 1)
            xd = round(min(0.0, med([f['id'] for f in frases if f['id'] not in antes_]) + 6.0), 1)
            dips, narr, en, nf_, it = resolver(xa, xd)
            golpes_bajo = [dict(cuadro=n, t=round(tf(n), 3), tipo=t_, frase=i, bajo_la_narracion=f['id'])
                           for n, t_, i in golpes for f in frases
                           if f['habla_master_s'][0] - 0.03 <= tf(n) <= f['habla_master_s'][1] + 0.03]
            nres = dict(niveles=niv, fondo_cede_db=DUCK_NARR, offset_seccion_db=dict(antes_de_la_cita=xa, despues_de_la_cita=xd),
                        ajuste_primera_pasada_db={a_: round(b_, 2) for a_, b_ in d0.items()},
                        ajuste_fondo_db={a_: round(b_, 2) for a_, b_ in dips.items()},
                        iteraciones=it + 1, voz_vs_fondo=nf_, golpes_bajo_las_palabras_menos6db=golpes_bajo)
            vf = voz_vs_fondo(m, voz, e)                          # la voz real, medida otra vez con la narración puesta
            print(k, 'narración', {a_: (r['dif_mediana_db'], r['dif_min_db'], round(dips[a_], 1)) for a_, r in nf_.items()},
                  flush=True)
        pre = AU / f'{k}_pre.wav'
        A.pre_mezcla(m, pre)
        I0 = L2.medir_ebur(pre)[0]
        gan = -14.0 - I0
        lim_hist = None
        if P.get('narracion'):
            I, Pk, LRA, lim_hist = limitar_aac(pre, AU / f'{k}.wav', gan, AU / f'{k}_prueba_aac.m4a')
            gan = lim_hist[-1]['ganancia_db']
        else:
            for _ in range(5):
                I, Pk, LRA = A.limitar(pre, AU / f'{k}.wav', gan)
                if -14.5 <= I <= -13.5 and Pk <= -1.0:
                    break
                gan += (-14.0 - I) - max(0.0, Pk + 1.2)
        json.dump({'lufs': I, 'pico_dbtp': Pk, 'ganancia_db': round(gan, 2), 'eventos': m.ev},
                  open(AU / f'{k}_eventos.json', 'w'), ensure_ascii=False, indent=1)
        out[k] = dict(lufs=I, pico_dbtp=Pk, lra=LRA, ganancia_db=round(gan, 2), voz_habla_db_original=ref,
                      voz_ganancia_db=g_aplicada, fondo_cede_db=DUCK_DB, colchon_bajo_voz_db=round(cama, 2), voz_vs_fondo=vf)
        if nres:
            out[k]['narracion'] = nres
            out[k]['limitador_con_aac'] = lim_hist
        print(k, {a: b for a, b in out[k].items() if a not in ('voz_vs_fondo', 'narracion')},
              {a: b for a, b in vf.items() if a != 'por_ventana'}, flush=True)
    out['golpes_texto'] = [dict(cuadro=n, t=round(tf(n), 3), tipo=t_, frase=i) for n, t_, i in M.eventos_texto()[0]]
    jdump(out, AU / 'audio.json')


# =====================================================================================================================
# master · base + capa de texto + frases y firma del cierre + mezcla (M.master_v4); la sin música copia el video
# =====================================================================================================================
def etapa_master():
    MA = TP / 'master'; MA.mkdir(parents=True, exist_ok=True)
    pl = json.load(open(TP / 'placa' / 'placa.json'))['cuadros']
    ov = [(TP / 'placa' / f'{k}.png', a, b) for k, (a, b) in pl.items()]
    M.NF = P['NF']
    out = MA / P['archivos']['completa']
    M.master_v4(TP / 'base.mp4', TP / 'audio' / 'completa.wav', out, TP / 'textos' / 'cuadros' / 'f_%04d.png', ov)
    print('ok', out, out.stat().st_size, flush=True)
    out2 = MA / P['archivos']['sinmusica']
    V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(out), '-i', str(TP / 'audio' / 'sinmusica.wav'), '-map', '0:v:0', '-map', '1:a:0',
          '-c:v', 'copy', '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
          '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
          '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
          '-shortest', '-movflags', '+faststart', str(out2)])
    print('ok', out2, out2.stat().st_size)


# =====================================================================================================================
# control · técnico (B2.tecnico), separación, textos, voz en el máster, hoja de fotogramas cada 0,5 s
# =====================================================================================================================
OFERTA_IDS = ('bf', 'precio', 'antes', 'placa_remera', 'founders', 'cta', 'bf_cta')


def tramos_control():
    pj = json.load(open(TP / 'planos.json'))
    tr = [(f"{p['id']}", round(p['m0'] / FPS, 3), round((p['m0'] + p['cuadros']) / FPS, 3)) for p in pj['planos']]
    vz = P['voz']
    tr.append(('voz', round(vz['m0'], 3), round(vz['m0'] + vz['src1'] - vz['src0'], 3)))
    a, b = P['negro']
    tr.append(('negro', round(a / FPS, 3), round((b + 1) / FPS, 3)))
    tr.append(('último 0,5 s', P['NF'] / FPS - 0.5, P['NF'] / FPS))
    return tr


def logo_ncc(mp4):
    """NCC de la ficha del logo (luma, 1/2, como C.analisis_cuadros) en cada cuadro; control positivo: la firma."""
    from PIL import Image
    pj = json.load(open(TP / 'placa' / 'placa.json'))
    x0, y0, x1, y1 = pj['ficha_logo']
    a = np.asarray(Image.open(TP / 'placa' / 'firma.png').convert('RGBA')).astype(np.float32)
    Y = a[y0:y1 + 1, x0:x1 + 1, :3] @ np.array([.2126, .7152, .0722], np.float32)
    tpl = np.asarray(Image.fromarray(Y.astype(np.uint8)).resize(((x1 + 1 - x0) // 2, (y1 + 1 - y0) // 2), Image.BOX)).astype(np.float32)
    tpl = 16 + tpl * 219 / 255                                   # a rango tv, como la luma del máster
    out = []
    for n, Yf, _, _ in C.cuadros_yuv(mp4):
        y2 = Yf.astype(np.float32).reshape(H // 2, 2, W // 2, 2).mean((1, 3))
        c = C._ncc(y2, tpl)
        iy, ix = np.unravel_index(int(np.argmax(c)), c.shape)
        out.append(dict(cuadro=n, ncc=round(float(c[iy, ix]), 4), pos=[int(ix * 2), int(iy * 2)]))
    return out


def etapa_control():
    preparar_textos()
    MA = TP / 'master'; CO = TP / 'control'; CO.mkdir(parents=True, exist_ok=True)
    rep = dict(pieza=P['titulo'], archivos={})
    for k, nombre in P['archivos'].items():
        pj, t = B2.tecnico(MA / nombre, tramos_control())
        jdump(pj, CO / f'ffprobe_{k}.json')
        rep['archivos'][k] = t
        print(k, t['md5_flujo_video'], t['sonoridad'], t['decodifica_completo'], t['audio_igual_video'], flush=True)
    a, b = P['negro']
    pj = json.load(open(TP / 'planos.json'))
    antes = [p for p in pj['planos'] if p['m0'] < a]
    rep['mapa_fuentes'] = [dict(plano=p['id'], cuadros=[p['m0'], p['m0'] + p['cuadros'] - 1], clip=p['clip'], fuente=p['fuente'],
                                tramo_s=p['tramo_s']) for p in pj['planos']]
    rep['separacion'] = dict(
        clips_antes_del_negro=sorted({p['clip'] for p in antes}),
        material_de_gianluca_antes_del_negro=[p['id'] for p in antes if p['clip'].startswith('IMG_')],
        conmebol_desde_s=min([p['tramo_s'][0] for p in pj['planos'] if p['clip'] == CONMEBOL], default=None),
        copa_7411_tramo_s=[p['tramo_s'] for p in pj['planos'] if p['clip'] == CA411])
    vis = json.load(open(TP / 'textos' / 'visible.json'))['cuadros']
    rep['separacion']['oferta_visible_antes_del_negro'] = sorted({x['id'] for n, fr in vis.items() if int(n) < a for x in fr
                                                                   if x['id'] in OFERTA_IDS})
    rep['separacion']['primer_cuadro_con_oferta'] = min(int(n) for n, fr in vis.items() for x in fr if x['id'] in OFERTA_IDS)
    # negro de 3 cuadros y logo por NCC (máster completo)
    lg = logo_ncc(MA / P['archivos']['completa'])
    pl = json.load(open(TP / 'placa' / 'placa.json'))['cuadros']
    f0 = pl['firma'][0]
    neg = []
    for n, Yf, Cb, Cr in C.cuadros_yuv(MA / P['archivos']['completa']):
        if a - 1 <= n <= b + 1:
            neg.append(dict(cuadro=n, luma_media=round(float(Yf.mean()), 2), luma_max=int(Yf.max()), croma_max_desvio=int(max(abs(int(Cb.max()) - 128), abs(int(Cb.min()) - 128), abs(int(Cr.max()) - 128), abs(int(Cr.min()) - 128)))))
    rep['negro'] = neg
    rep['logo'] = dict(metodo='NCC de la ficha del logo de la firma (luma 1/2) en cada cuadro del máster; control positivo: cuadros con firma',
                       ncc_max_c0_hasta_negro=max(x['ncc'] for x in lg[:a]),
                       cuadro_del_max=max(lg[:a], key=lambda x: x['ncc']),
                       ncc_firma_min=min(x['ncc'] for x in lg[f0:]), ncc_firma_max=max(x['ncc'] for x in lg[f0:]))
    print('logo', rep['logo'], flush=True)
    # la voz dentro del máster: transcripción del tramo (completa y sin música)
    vz = P['voz']; t0, t1 = vz['m0'] - 0.3, vz['m0'] + (vz['src1'] - vz['src0']) + 0.3
    wavs = []
    for k, nombre in P['archivos'].items():
        w = CO / f'voz_en_master_{k}.wav'
        V.sh(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t0:.3f}', '-t', f'{t1 - t0:.3f}', '-i', str(MA / nombre), '-vn', '-ac', '1',
              '-ar', '16000', '-c:a', 'pcm_s16le', str(w)])
        wavs.append(w)
    vent = []
    if P.get('narracion'):
        # v02: cada frase de la narración en su ventana del máster (±0,15 s), completa y sin música: Whisper en tramos
        # cortos (en el archivo largo se saltea palabras gritadas, LEEME_VOZ_OFICIAL)
        NW = CO / 'narracion_ventanas'; NW.mkdir(exist_ok=True)
        for f in json.load(open(TP / 'narracion.json'))['frases']:
            a_, b_ = f['habla_master_s']
            for k, nombre in P['archivos'].items():
                w = NW / f"{f['id']}_{k}.wav"
                V.sh(['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0, a_ - 0.15):.3f}', '-t', f'{b_ - a_ + 0.30:.3f}', '-i', str(MA / nombre),
                      '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(w)])
                vent.append((f['id'], k, round(max(0, a_ - 0.15), 3), w))
    tr = whisper(CO / 'whisper_master.json', wavs + [x[3] for x in vent])
    if vent:
        rep['narracion_en_master'] = [dict(frase=fid, version=k, desde_s=t0_, texto=' '.join(sg['texto'] for sg in tr[str(w)]),
                                           palabras=[[p_[0], round(t0_ + p_[1], 2), round(t0_ + p_[2], 2), p_[3]]
                                                     for sg in tr[str(w)] for p_ in sg['palabras']])
                                      for fid, k, t0_, w in vent]
        for x in rep['narracion_en_master']:
            print('narración', x['frase'], x['version'], x['texto'], flush=True)
    tr = {f: segs for f, segs in tr.items() if f in [str(w) for w in wavs]}
    rep['voz_en_master'] = {Path(f).stem: ' '.join(sg['texto'] for sg in segs) for f, segs in tr.items()}
    rep['voz_en_master_tramo_s'] = [round(t0, 3), round(t1, 3)]
    print('voz', rep['voz_en_master'], flush=True)
    rep['textos_vs_guion'] = json.load(open(TP / 'textos' / 'textos_vs_guion.json'))
    rep['audio'] = json.load(open(TP / 'audio' / 'audio.json'))
    U.hoja_contacto(MA / P['archivos']['completa'], CO / 'hoja_0,5s.jpg', cada=15, cols=7, ancho=240)
    jdump(rep, CO / 'control.json')
    print('control ok')

# =====================================================================================================================
# entrega · copia sin pisar + hoja del máster (todo sale de los JSON medidos; los desvíos van escritos a mano)
# =====================================================================================================================
DESVIOS = {
    'v6': [
        'Pasos 1–2 (c0–41) y 3–6: recortes neutros del panel de arriba de ESPN 7649 (entrenamiento con Vignolo, 2023), no '
        'CONMEBOL 57,9–59,3. En el plano de atrás del arco de 7680 se ven la red, el arco, la pelota y el número, que el '
        'dictamen saca («sin número de camiseta, tablero, pelota, arco ni gesto»). El plano completo de 7680 queda para el '
        'paso 10 (c396), como el pago del gancho. Efecto: c0 ya no «era el 123»; la revelación del paso 10 es la atajada '
        'misma, no el mismo plano. Propuesta si Roma quiere el pago literal: c0 con un recorte de 7680 57,9 que deje solo '
        'la espalda (sin red ni número), si aparece uno limpio.',
        'Pasos 3–6 con los tiempos del dictamen: 4 y 5 juntos en 1,0 s (c90–119: «28 años: debuta en la Selección.» y, desde c105, «Entra porque Armani tiene COVID.» debajo) y el resto −0,6 s. Los '
        'clubes entran de a uno cada 0,2 s (Oxford → Reading) y «Seis préstamos.» queda en c78.',
        'Voz: corte A medido. Termina antes de «y de ahí jugás con la suerte» (la «y» queda afuera). El audio es el '
        'original del clip, sin separar: en el tramo no hay música y el piso es ≈ −60 dB.',
        'El fondo no cede 20 dB, como decía el guion. Cede 6 dB por envolvente y el colchón se ajusta para dejar la voz '
        '10–15 dB arriba (medido: tabla «voz contra fondo»). Con 20 dB, la voz quedaba 18–31 dB arriba y el fondo '
        'desaparecía.',
        'Franja sobre los subtítulos de ESPN: sólida entre y 768 y 891, con un degradé de 500 a 768 (opacidad 0,86). En '
        'el primer render empezaba en 786 y asomaban las puntas de las letras altas: en la fuente, el contorno del subtítulo '
        'arranca en y 777 (medido en los 192 cuadros). Ahora no queda nada: las filas 768–891 del máster base tienen luma '
        '14 plana en todo el tramo. No le tapa la cara: la cara está arriba de y 560.',
        'Atribución en dos renglones: «— Emiliano “Dibu” Martínez» / «ESPN · TikTok @espnargentina · 09/06/2026». El salto '
        'de línea reemplaza el primer « · » (por eso figura como distinta del guion). Las palabras y la fecha son las mismas.',
        'Ambiente de estadio sintético (sonido.Mezcla). El audio de los clips está silenciado porque tiene relato o música.',
        'Cierre: IMG_5359 de 6,5 a 9,1 s (el guion pedía 6,9–9,5; el foco entra igual en ≈ 7,5). IMG_5325 de 11,7 a 13,4 s '
        '(el guion pedía 10,0–11,7), con el bordado «ROCCÉ» / «Founders Privée» entero. La ventana empieza 300 filas arriba '
        'y se completa con el relleno de la misma toma.',
        'Founders: «Va a haber 100 Founders como máximo» entra entero en c579 y se lee completo 0,7 s (19,30–20,00 s), hasta '
        'el CTA, como en el guion. En el primer render entraba palabra por palabra y quedaba completo solo 7 c (0,23 s). '
        '**Para Roma:** 0,7 s es poco para seis palabras. Propuesta: alargar el plano 14 0,5 s empezando IMG_5325 en 11,2 s '
        '(sigue siendo el macro del bordado) y sin pasar de 13,4 s, donde la cámara sube: Founders 19,30–20,50 s y CTA '
        'desde 20,50 s, con la pieza 0,5 s más larga. Probé dejarlo arriba del CTA hasta el final y lo descarté: en '
        'c612–619 la cámara sube y el CTA tapa la parte de arriba del bordado «RO».',
        'Oferta: los « · » del guion se reemplazan por renglones y tamaños. «Black Friday · −25 %» lleva «−25 %» en celeste, «$48.750» '
        'es el elemento más grande, debajo «antes $65.000» y «La placa viene con la remera.». El texto es letra por letra '
        'el del dictamen.',
    ],
    'v7': [
        'Pasos 1–5 (c0–104): recortes de espalda con fundido abajo, que dejan la cabeza y tapan nombre y número. No se ve '
        'el 11 en ningún cuadro (hoja 0,5 s y hoja cada 4 c de c0–104). En c44 asoma parte del nombre («…MARÍ…»), que el '
        'dictamen permite. Copa América 7097 (paso 4 del guion) se reemplazó por TyC 7660 n276 y CA 7643 n556, porque en '
        '7097 no hay un recorte sin pelota ni tablero. Detrás se ven fragmentos de letras del cartel (UNINTER) y del logo de '
        'la Copa, sin una palabra de apuestas legible, y la marca de agua «COPA AMERICA» del dueño (no se borra).',
        'Gol de 2021: el color entra en c214 (la pelota cruza la línea en n238 de 7660). Gol de 2022 en c312 (n362 de 7585).',
        'Voz: corte A medido. Va de «Algún día…» hasta el primer «acá», sobre la voz separada con demucs (htdemucs, '
        'two-stems) de AFA 7392. Whisper oye «Te rompió» en el corte y «se rompió» con contexto. El texto fijado sale de '
        'los subtítulos quemados de AFA («Se rompió», «seguí estando acá»). No se escuchó: queda para escucha humana.',
        'La cita va en y 1150–1510, fuera del rango 270–1130 de Fede, porque en 7411 la cara ocupa el tercio de arriba. '
        'Detrás de las tarjetas hay un degradé en banda (y 1060–1640, opacidad 0,62).',
        'El rótulo «COPA AMÉRICA 2024 · SU ÚLTIMO PARTIDO» (c351–390) queda como en el guion. Es ambiguo, porque después '
        'jugó con clubes. Propuesta: «COPA AMÉRICA 2024 · SU ÚLTIMO PARTIDO EN LA SELECCIÓN» (o «· SU DESPEDIDA»).',
        '7411 de 33,0 a 38,9 s a velocidad natural: no entra nada del tramo 26–31 s.',
        'El grito del gol no es el «grito real de 7097» del guion. Es sintético, porque el audio de 7097 tiene música o '
        'relato medido como periódico. El ambiente también es sintético. El audio de los clips está silenciado.',
        'El fondo cede 6 dB por envolvente, no 20 dB, y el colchón se ajusta para dejar la voz 10–15 dB arriba (ver V6).',
        'Founders: «Va a haber 100 Founders como máximo» entra entero en c669 y se lee completo 0,7 s (22,30–23,00 s), hasta '
        'el CTA, como en el guion. En el primer render entraba palabra por palabra y quedaba completo solo 7 c (0,23 s). '
        '**Para Roma:** 0,7 s es poco para seis palabras. Propuesta: alargar el plano 18 0,5 s empezando IMG_5325 en 11,2 s '
        '(sigue siendo el macro del bordado) y sin pasar de 13,4 s, donde la cámara sube: Founders 22,30–23,50 s y CTA '
        'desde 23,50 s, con la pieza 0,5 s más larga. Probé dejarlo arriba del CTA hasta el final y lo descarté: en '
        'c712–719 la cámara sube y el CTA tapa la parte de arriba del bordado «RO».',
        'Cierre y oferta: los mismos tramos y el mismo criterio de V6 (IMG_5359 6,5–9,1 · IMG_5361 0,9–2,9 · IMG_5325 11,7–13,4).',
        'Atribución: usa la fecha AFA 16/07/2024, el upload_date del info.json. El timestamp es 16/07/2024 01:24 UTC, que en '
        'Argentina es el 15/07 a las 22:24.',
    ],
}


ESCUCHA = {          # notas para la escucha humana, con el segundo exacto (salen del control; la ASR no mide escucha)
    'v6': ('Whisper sobre el máster completo oye «Le he bloqueado» entre 7,0 y 7,8 s; sobre la sin música, «Le bloqueo». '
           'La suma de pistas sin limitador ni AAC se transcribe «le bloqueo» con el fondo tal cual, a −4 dB, a −8 dB y con los '
           'efectos a −12 dB. La única ventana con poco margen es la primera, de 50 ms: a 7,00 s la voz está 3,6 dB arriba de la '
           'cola del golpe de c204. Escuchar 6,8–7,8 s. Si «le bloqueo» no se entiende, bajar 12 dB más los efectos desde 6,95 s '
           '(la cola del golpe), sin tocar la voz.'),
    'v7': ('Whisper sobre la sin música no entiende la segunda mitad de la cita (13,4–16,1 s, «Me la di muchas veces, pero '
           'seguí estando acá»): oye «…pero ha habido muchas veces que se quita todo el mar». Con la voz sola y en la completa la '
           'lee casi bien («me la di/vi muchas veces, pero seguí tanto acá»). Con el colchón de tribuna 8 dB más bajo (≈ 22 dB '
           'bajo la voz) la lectura no cambia, así que no hay una mejora medible para aplicar. La voz es la separada con demucs, '
           'y Whisper oye «te rompió» y «seguí tanto» también en la voz sola; el texto fijado sale de los subtítulos quemados de '
           'AFA. Escuchar la sin música entre 12,0 y 17,6 s. Si no se entiende, bajar 6 dB el colchón bajo la voz en la sin '
           'música (de +18,2 a +12,2 dB).'),
}


def rangos_visibles():
    vis = json.load(open(TP / 'textos' / 'visible.json'))['cuadros']
    r = {}
    for n, fr in vis.items():
        for x in fr:
            a = r.setdefault(x['id'], [int(n), int(n)])
            a[0] = min(a[0], int(n)); a[1] = max(a[1], int(n))
    return r


def cajas_mp4(p):
    import struct
    b = Path(p).read_bytes(); out = []; i = 0
    while i < len(b):
        n, t = struct.unpack('>I4s', b[i:i + 8])
        if n == 1:
            n = struct.unpack('>Q', b[i + 8:i + 16])[0]
        out.append((t.decode('latin1'), i, n)); i += n if n else len(b)
    return b, out


def sin_c2pa(p):
    """el MP4 sin la caja uuid de Content Credentials (C2PA) que el almacenamiento de /mnt/project-files agrega al guardar
    (medido el 26/11: 'uuid' de 5875 bytes después de 'ftyp', firmada por «Anthropic Files»)."""
    import struct
    b, cj = cajas_mp4(p)
    quitar = [(i, n) for t, i, n in cj if t == 'uuid' and b'c2pa' in b[i:i + n]]
    if not quitar:
        return b, False
    assert len(quitar) == 1
    i0, n0 = quitar[0]
    m = [(i, n) for t, i, n in cj if t == 'moov']
    assert len(m) == 1 and m[0][0] > i0
    mi, mn = m[0]
    moov = bytearray(b[mi:mi + mn])
    # la caja va antes de moov y mdat: el almacenamiento corrió n0 bytes los offsets de stco/co64; se deshace solo eso
    for tipo, tam in ((b'stco', 4), (b'co64', 8)):
        j = moov.find(tipo)
        while j != -1:
            cnt = struct.unpack('>I', moov[j + 8:j + 12])[0]
            fmt = '>I' if tam == 4 else '>Q'
            for e in range(cnt):
                k = j + 12 + e * tam
                moov[k:k + tam] = struct.pack(fmt, struct.unpack(fmt, moov[k:k + tam])[0] - n0)
            j = moov.find(tipo, j + 4)
    b = b[:mi] + bytes(moov) + b[mi + mn:]
    return b[:i0] + b[i0 + n0:], True


def copiar_sin_pisar(src, dst):
    """copia y verifica sin pisar. El almacenamiento agrega un manifiesto C2PA al guardar, así que el sha256 del archivo
    entregado no es el del máster de trabajo: se comprueba que, sin esa caja, los bytes sean idénticos (MP4), o que los
    píxeles sean idénticos (JPG)."""
    h = hashlib.sha256(Path(src).read_bytes()).hexdigest()
    nuevo = not dst.exists()
    if nuevo:
        shutil.copy2(src, dst)
    if dst.suffix == '.mp4':
        limpio, c2pa = sin_c2pa(dst)
        assert hashlib.sha256(limpio).hexdigest() == h, f'{dst} ya existe con otro contenido: no se pisa'
    else:
        from PIL import Image
        assert np.array_equal(np.asarray(Image.open(src)), np.asarray(Image.open(dst))), f'{dst} ya existe con otros píxeles'
        c2pa = b'c2pa' in dst.read_bytes()[:20000]
    h2 = hashlib.sha256(dst.read_bytes()).hexdigest()
    return dict(sha256_master=h, sha256_entregado=h2, bytes_entregado=dst.stat().st_size, c2pa=c2pa,
                estado=('copiado' if nuevo else 'ya estaba') + ('; quitando la caja C2PA y el corrimiento que deja en los offsets de stco, idéntico byte a byte al máster' if dst.suffix == '.mp4' else ''))


def s_(n):
    return f'{n / FPS:.2f}'.replace('.', ',')


def etapa_entregar():
    CO, MA = TP / 'control', TP / 'master'
    rep = json.load(open(CO / 'control.json'))
    voz = json.load(open(TP / 'voz' / 'voz.json'))
    pl = json.load(open(TP / 'placa' / 'placa.json'))
    aud = rep['audio']
    D = PIEZAS / P['nombre']; D.mkdir(parents=True, exist_ok=True)
    copias = {}
    for k, nombre in P['archivos'].items():
        cp = copiar_sin_pisar(MA / nombre, D / nombre)
        assert cp['sha256_master'] == rep['archivos'][k]['sha256']
        assert U.md5_stream(D / nombre, 'v') == rep['archivos'][k]['md5_flujo_video']
        assert U.md5_stream(D / nombre, 'a') == rep['archivos'][k]['md5_flujo_audio']
        cuerpo = (D / nombre).read_bytes()
        cp['marcas_ubicacion'] = [m_.decode() for m_ in (b'ISO6709', b'\xa9xyz', b'com.apple.quicktime.location', b'location')
                                  if m_ in cuerpo]
        cp['decodifica'] = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(D / nombre), '-f', 'null', '-'],
                                          capture_output=True, text=True).stderr.strip() == ''
        copias[k] = cp
    hoja_img = D / '01_pedro_hoja_0,5s_v01.jpg'
    copiar_sin_pisar(CO / 'hoja_0,5s.jpg', hoja_img)
    jdump(copias, CO / 'entrega.json')
    a, b = P['negro']; vz = P['voz']; rv = rangos_visibles()
    L = []
    w = L.append
    w(f"# LIFE T3 · {P['titulo']} · máster v01 · hoja de Pedro · 26/11/2026\n")
    w('Máster v01 para revisión privada de Roma. **No se publicó nada, no hubo commit ni push y se usaron 0 créditos.** '
      '**El audio no se escuchó:** se midió con ebur128, niveles por tramo, voz contra fondo y Whisper (faster-whisper '
      '`small`). La imagen se revisó por fotogramas, sin reproducir el video en tiempo real.\n')
    w('## Archivos\n')
    w('| versión | archivo entregado | bytes | sha256 del archivo entregado | md5 del flujo de video | md5 del flujo de audio |')
    w('|---|---|---|---|---|---|')
    for k, nombre in P['archivos'].items():
        t, cp = rep['archivos'][k], copias[k]
        w(f"| {k} v01 | `{D / nombre}` | {cp['bytes_entregado']} | `{cp['sha256_entregado']}` | `{t['md5_flujo_video']}` | `{t['md5_flujo_audio']}` |")
    w('\n**ID inmutable del máster: el md5 de los flujos.** El almacenamiento de `/mnt/project-files` agrega al guardar un '
      'manifiesto C2PA firmado (Content Credentials, «Anthropic Files»: «Claude provided this file…») en una caja `uuid` '
      'después de `ftyp`. Por eso el sha256 del archivo entregado no es el del máster de trabajo. Comprobado en cada archivo '
      'entregado: quitando esa caja y el corrimiento de 5875 bytes que deja en los offsets de `stco` (lo único que cambia en '
      '`moov`; `ftyp`, `free` y `mdat` son iguales), es idéntico byte a byte al máster; los md5 de video y de audio son los '
      'del control; decodifica '
      'sin errores; la caja no tiene datos de ubicación.\n')
    w('| versión | sha256 del máster de trabajo (sin C2PA) | bytes del máster | C2PA en el entregado | decodifica | marcas de ubicación |')
    w('|---|---|---|---|---|---|')
    for k, nombre in P['archivos'].items():
        t, cp = rep['archivos'][k], copias[k]
        w(f"| {k} | `{t['sha256']}` | {t['bytes']} | {'sí' if cp['c2pa'] else 'no'} ({cp['estado']}) | "
          f"{'sin errores' if cp['decodifica'] else 'CON ERRORES'} | {cp['marcas_ubicacion'] or 'ninguna'} |")
    w(f"\nLas dos versiones comparten el flujo de video (se copia sin recodificar) y solo cambia la mezcla. md5 del video "
      f"decodificado (yuv420p): `{rep['archivos']['completa']['md5_video_decodificado']}`. Receta: "
      f"`/home/user/1/scripts/life/life_t3.py {P['clave']} voz|planos|textos|placa|audio|master|control|entregar`. "
      f"Intermedios en `/home/user/1/TRABAJO/life3/t3/{P['clave']}/` (fuera de git). El control completo está en "
      f"`/home/user/1/TRABAJO/life3/t3/{P['clave']}/control/control.json`.\n")
    # --- lo que Roma comprueba
    sep = rep['separacion']; lg = rep['logo']; ng = rep['negro']
    ng_in = [x for x in ng if a <= x['cuadro'] <= b]
    tc, ts = rep['archivos']['completa'], rep['archivos']['sinmusica']
    w('## Lo que Roma comprueba en el máster\n')
    w('| control | resultado | evidencia |')
    w('|---|---|---|')
    w(f"| c0 hasta el negro sin remera, logo, placa ni oferta | cumple | Antes de c{a} solo hay clips de terceros: "
      f"{', '.join(sep['clips_antes_del_negro'])}. Material de Gianluca antes del negro: "
      f"{sep['material_de_gianluca_antes_del_negro'] or 'ninguno'}. Ningún texto de oferta es visible antes del negro "
      f"({sep['oferta_visible_antes_del_negro'] or 'ninguno'}); el primer cuadro con oferta es c{sep['primer_cuadro_con_oferta']}. "
      f"NCC del logo: máximo {lg['ncc_max_c0_hasta_negro']} entre c0 y el negro (c{lg['cuadro_del_max']['cuadro']}), "
      f"contra {lg['ncc_firma_min']}–{lg['ncc_firma_max']} en la firma (control positivo). |")
    w(f"| negro de 3 cuadros | cumple | c{a}–c{b}: luma media {', '.join(str(x['luma_media']) for x in ng_in)}, "
      f"luma máxima {max(x['luma_max'] for x in ng_in)} (negro de rango tv = 16) y desvío máximo de croma "
      f"{max(x['croma_max_desvio'] for x in ng_in)}. Vecinos: c{a - 1} = {ng[0]['luma_media']} y c{b + 1} = {ng[-1]['luma_media']}. |")
    bd = voz['bordes_nivel_db']
    w(f"| cita igual al audio, cortada en una pausa medida | cumple (por transcripción; sin escucha) | Corte "
      f"{vz['src0']:.3f}–{vz['src1']:.3f} s de la fuente. Nivel: {bd['antes_del_corte_db']} dB antes del corte, "
      f"{bd['despues_del_inicio_db']} dB al empezar, {bd['antes_del_final_db']} dB antes del final y "
      f"{bd['despues_del_final_db']} dB después; mediana del habla {bd['voz_mediana_db']} dB. La pantalla dice "
      f"{vz['texto']}. Whisper en el máster: «{rep['voz_en_master'].get('voz_en_master_completa', '')}». |")
    if sep['conmebol_desde_s'] is not None:
        marcas = (f"CONMEBOL 7680 se usa solo desde {sep['conmebol_desde_s']} s (la regla pide desde 46,3 s): Betsson y Betano "
                  f"están entre 0 y 46 s. En sus carteles se lee FIFA Store. En el buzo de ESPN 7649 hay tres rayas, sin logo "
                  f"legible. No se usa imagen de Telefe 7391714 ni de ESPN 7408.")
        rot2 = ''
    else:
        marcas = ('En los carteles se leen UNINTER (una universidad; final de 2021) y Wanda (final de 2022), además de las '
                  'marcas de agua de los dueños (TyC Sports, CONMEBOL Copa América). En la camiseta, adidas (aceptado por Roma). '
                  'No se usa imagen de Telefe 7391714 ni de ESPN 7408.')
        rot2 = (' El segundo rótulo, «COPA AMÉRICA 2024 · SU ÚLTIMO PARTIDO» (c351–390), va sobre imágenes de ese mismo '
                'partido (7411, final de 2024).')
    w(f"| ninguna marca de apuestas legible | cumple (revisado a ojo) | Se revisaron la hoja cada 0,5 s y las hojas de cada "
      f"plano. {marcas} |")
    w('| ninguna imagen con un rótulo de otro momento | cumple | El rótulo lleva solo el nombre. El año y el club van en el '
      f'texto de la historia.{rot2} Los rótulos de los dueños (CONMEBOL, TyC, ESPN, Copa América) son los de su propio '
      'material y quedan sin tocar. |')
    w(f"| HLG→SDR con `mobius`, sin GPS | cumple | Cadena `{HLG_SDR}` en IMG_5359, IMG_5361 e IMG_5325. Marcas de ubicación "
      f"en los MP4: completa {tc['marcas_gps_o_ubicacion'] or 'ninguna'} · sin música {ts['marcas_gps_o_ubicacion'] or 'ninguna'}. |")
    for k, t in rep['archivos'].items():
        so = t['sonoridad']
        w(f"| −14 LUFS ±1, ≤ −1 dBTP ({k}) | {'cumple' if -15 <= so['lufs_integrado'] <= -13 and so['pico_real_dbtp'] <= -1 else 'NO cumple'} | "
          f"ebur128 sobre el MP4: {so['lufs_integrado']} LUFS, {so['pico_real_dbtp']} dBTP, LRA {so['lra']} |")
        w(f"| audio y video de la misma duración ({k}) | {'cumple' if t['audio_igual_video'] else 'NO cumple'} | "
          f"video {t['video']['duracion']:.4f} s, audio {t['audio']['duracion']:.4f} s, {t['cuadros_decodificados']} cuadros |")
    # --- formato
    w('\n## Formato (ffprobe) y decodificación\n')
    w('| | completa | sin música |')
    w('|---|---|---|')
    v1, v2 = tc['video'], ts['video']
    fila = lambda n, x, y: w(f'| {n} | {x} | {y} |')
    fila('video', f"{v1['codec']} {v1['perfil']} nivel {v1['nivel']}, {v1['pix_fmt']}, {v1['ancho']}×{v1['alto']}, {v1['fps']}",
         f"{v2['codec']} {v2['perfil']} nivel {v2['nivel']}, {v2['pix_fmt']}, {v2['ancho']}×{v2['alto']}, {v2['fps']}")
    fila('color (rango / matriz / transferencia / primarios)', f"{v1['rango']} / {v1['matriz']} / {v1['transferencia']} / {v1['primarios']}",
         f"{v2['rango']} / {v2['matriz']} / {v2['transferencia']} / {v2['primarios']}")
    fila('audio', f"{tc['audio']['codec']} {tc['audio']['perfil']}, {tc['audio']['hz']} Hz, {tc['audio']['canales']} canales, {tc['audio']['bitrate'] // 1000} kb/s",
         f"{ts['audio']['codec']} {ts['audio']['perfil']}, {ts['audio']['hz']} Hz, {ts['audio']['canales']} canales, {ts['audio']['bitrate'] // 1000} kb/s")
    fila('duración video / audio / formato', f"{v1['duracion']:.4f} / {tc['audio']['duracion']:.4f} / {tc['duracion_formato']:.4f} s",
         f"{v2['duracion']:.4f} / {ts['audio']['duracion']:.4f} / {ts['duracion_formato']:.4f} s")
    fila('cuadros (ffprobe / decodificados)', f"{v1['cuadros']} / {tc['cuadros_decodificados']}", f"{v2['cuadros']} / {ts['cuadros_decodificados']}")
    fila('faststart (moov antes de mdat)', tc['faststart'], ts['faststart'])
    fila('`ffmpeg -v error -i … -f null -`', 'sin errores' if tc['decodifica_completo'] else tc['errores_decodificacion'],
         'sin errores' if ts['decodifica_completo'] else ts['errores_decodificacion'])
    fila('silencio al final', f"{tc['silencio_final_s']} s", f"{ts['silencio_final_s']} s")
    # --- sonoridad + voz/fondo
    w('\n## Sonoridad y voz contra fondo\n')
    w('| versión | MP4: LUFS integrado | MP4: pico real dBTP | LRA | mezcla WAV: LUFS / dBTP | ganancia de la voz | el fondo cede | ajuste del colchón bajo la voz | voz − fondo (mediana · mín–máx, ventanas de 50 ms de habla) |')
    w('|---|---|---|---|---|---|---|---|---|')
    for k in P['archivos']:
        t, au = rep['archivos'][k], aud[k]; vf = au['voz_vs_fondo']
        w(f"| {k} | {t['sonoridad']['lufs_integrado']} | {t['sonoridad']['pico_real_dbtp']} | {t['sonoridad']['lra']} | "
          f"{au['lufs']} / {au['pico_dbtp']} | {au['voz_ganancia_db']:+.2f} dB (habla original {au['voz_habla_db_original']} dBFS) | "
          f"{au['fondo_cede_db']} dB por envolvente | {au['colchon_bajo_voz_db']:+.2f} dB | {vf['dif_mediana_db']} · {vf['dif_min_db']}–{vf['dif_max_db']} dB ({vf['ventanas']} ventanas) |")
    w('\nObjetivo: la voz 10–15 dB arriba del fondo durante las frases (CLAUDE.md); los golpes van entre frases. El limitador '
      'es `alimiter` con `level=false`. Niveles por tramo del MP4 completo (dBFS):\n')
    w('| tramo | desde–hasta (s) | RMS | pico |')
    w('|---|---|---|---|')
    for x in tc['niveles_por_tramo']:
        w(f"| {x['tramo']} | {x['t0']}–{x['t1']} | {x['rms_dbfs']} | {x['pico_dbfs']} |")
    w(f"\nVentanas de 100 ms bajo −50 dBFS en el MP4 completo (s): {tc['ventanas_100ms_bajo_menos50dbfs']} (huecos de la mezcla: "
      f"silencios buscados del guion, el negro y el final). Silencio final (RMS de 10 ms bajo −60 dBFS): completa {tc['silencio_final_s']} s · sin música "
      f"{ts['silencio_final_s']} s"
      f"{' (es el fundido del ambiente de 0,40 s: sin música, el fundido llega antes al piso)' if ts['silencio_final_s'] > 0.5 else ''}.\n")
    if P['clave'] in ESCUCHA:
        w(f"**Para la escucha:** {ESCUCHA[P['clave']]}\n")
    # --- clips
    w('\n## Clips y tramos\n')
    w('| plano | cuadros del máster | s del máster | fuente (cuenta · id · publicación) | tramo de la fuente (s) | velocidad | imagen |')
    w('|---|---|---|---|---|---|---|')
    pj = json.load(open(TP / 'planos.json'))
    neg_ok = False
    for p in pj['planos']:
        if p['m0'] > a and not neg_ok:
            w(f"| negro | c{a}–c{b} | {s_(a)}–{s_(b + 1)} | — | — | — | negro de separación |"); neg_ok = True
        ic = info_clip(p['clip'])
        if p['clip'].startswith('IMG_'):
            s0 = SDR_TRAMOS[p['clip']][1]
            tramo = f"{s0 + p['tramo_s'][0]:.2f}–{s0 + p['tramo_s'][1]:.2f}"
            fu = f"{ic['cuenta']} · `{ic['url']}` · HLG→SDR mobius"
        else:
            tramo = f"{p['tramo_s'][0]:.2f}–{p['tramo_s'][1]:.2f}"
            fu = f"{ic['cuenta']} · {ic['id']} · {ic['fecha_publicacion']}"
        w(f"| {p['id']} | c{p['m0']}–c{p['m0'] + p['cuadros'] - 1} | {s_(p['m0'])}–{s_(p['m0'] + p['cuadros'])} | {fu} | "
          f"{tramo} | {p['velocidad']} | {p['muestra']} |")
    w(f"\nLa voz es audio de {voz['fuente']['cuenta']} {voz['fuente']['id']} ({voz['fuente']['fecha_publicacion']}), "
      f"{vz['src0']:.3f}–{vz['src1']:.3f} s, y entra en el máster de {voz['entra_en_master_s']:.3f} a {voz['termina_en_master_s']:.3f} s. "
      f"Es la primera voz humana que se oye: el audio de todos los clips está silenciado.\n")
    # --- voz
    w('## Voz real: corte medido y transcripción\n')
    w(f"- Separación: {voz['separacion']}.")
    w(f"- Método: {voz['metodo']}.")
    w(f"- Texto fijado (en pantalla): {voz['texto_fijado']}")
    w('- Ataque de cada palabra (s de la fuente → s del máster), usado para que cada palabra aparezca con su ataque:')
    w('  ' + ' · '.join(f"{t_} {s:.2f}→{s - vz['src0'] + vz['m0']:.2f}" for t_, s in vz['palabras']))
    w('- Whisper sobre el corte (s desde el inicio del corte):')
    for f_, segs in voz['whisper'].items():
        w(f"  - `{Path(f_).name}`: " + ' | '.join(f"{sg['ini']:.2f}–{sg['fin']:.2f} «{sg['texto']}»" for sg in segs))
    w(f"- Whisper sobre el máster ({rep['voz_en_master_tramo_s'][0]}–{rep['voz_en_master_tramo_s'][1]} s): " +
      ' · '.join(f"{k}: «{v}»" for k, v in rep['voz_en_master'].items()))
    w('- No se cambió el tono ni el tiempo y no hay cortes internos: la frase es un solo tramo continuo de la fuente.\n')
    # --- textos
    w('## Textos en pantalla contra el guion corregido\n')
    w('| id | en pantalla | guion corregido (Fede v1 + dictamen de Roma) | igual | cuadros visibles |')
    w('|---|---|---|---|---|')
    for k, x in rep['textos_vs_guion'].items():
        r = rv.get(k)
        w(f"| {k} | {x['visible']} | {x['guion']} | {'sí' if x['igual'] else '**no**'} | {f'c{r[0]}–c{r[1]}' if r else '—'} |")
    guion_cierre = [f"Él tiene su {'minuto 123' if P['clave'] == 'v6' else 'copa'}.", 'Esta placa significa lo mismo:', 'seguir hasta lograrlo.']
    for i, (t_, g_) in enumerate(zip(pl['texto'], guion_cierre)):
        c_ = pl['cuadros'][f'cierre_{i + 1}']
        w(f"| cierre_{i + 1} | {t_} | {g_} | {'sí' if t_ == g_ else '**no**'} | c{c_[0]}– (acumulativo hasta c{pl['cuadros']['cierre_3'][1]}) |")
    w(f"| firma | logo `LOGO/rocce_logo.png` en ficha #FEFEFE + «ROCCÉ LIFE» | firma ROCCÉ LIFE | sí | c{pl['cuadros']['firma'][0]}–c{pl['cuadros']['firma'][1]} |")
    w('\nTodas las tildes, rayas, comillas y «−» (signo menos) son los del dictamen. «seguí» (V7) y «seguir» van en celeste. '
      'No hay subtítulos automáticos.\n')
    # --- hoja
    w('## Hoja de fotogramas cada 0,5 s\n')
    w(f"`{hoja_img}`: un cuadro cada 15 (0,5 s) del máster completo, de c0 a c{P['NF'] - 1}.\n")
    # --- desvíos
    w('## Desvíos del guion y propuestas\n')
    for x in DESVIOS[P['clave']]:
        w(f'- {x}')
    # --- estado
    w('\n## Verificado / revisado a ojo / pendiente\n')
    w('- **Verificado técnicamente:** decodificación completa sin errores, ffprobe (formato, color, duración, cuadros), '
      'faststart, sin marcas de ubicación, ebur128 sobre el MP4 (LUFS y pico real), duración del audio igual a la del video, '
      'md5 de los flujos, texto en pantalla carácter por carácter contra el guion corregido (capa de texto), oferta ausente '
      'antes del negro (capa de texto), NCC del logo, luma del negro, bordes del corte de voz por nivel, Whisper del corte '
      'y del máster.')
    w('- **Revisado a ojo (fotogramas):** encuadres y recortes neutros, franja o degradé sobre los subtítulos quemados, que '
      'no haya marcas de apuestas legibles, cierre con la placa y la remera y legibilidad de los textos a tamaño real en los '
      'cuadros de las hojas.')
    w('- **Pendiente de revisión humana:** escuchar el máster entero (voz, corte, golpes, ambiente sintético, música TEMP '
      'propia), mirarlo en movimiento en un teléfono y la decisión de Roma sobre los desvíos. Aviso: todo el material de '
      'terceros (TyC, ESPN, CONMEBOL, Copa América, AFA) puede generar reclamos o audio silenciado.')
    md = D / '01_pedro_hoja_master_v01.md'
    texto = '\n'.join(L) + '\n'
    if md.exists() and md.read_text(encoding='utf-8') != texto:
        raise SystemExit(f'{md} ya existe con otro contenido: no se pisa')
    md.write_text(texto, encoding='utf-8')
    print(md)
    print(json.dumps({k: dict(md5_flujo_video=t['md5_flujo_video'], sonoridad=t['sonoridad'], sha256=t['sha256'])
                      for k, t in rep['archivos'].items()}, ensure_ascii=False))


def f_(x, d=2):
    s = f'{x:.{d}f}'
    if float(s) == 0:
        s = s.lstrip('-')
    return s.replace('.', ',')


NOTAS_HOJA_V02 = {
    'v6': dict(
        sintesis='En las frases que quedan en la voz se sintetiza «Blac Fraidei» y los números en palabras («diez», «veintiocho», '
                 '«ciento veintitrés», «veinticinco»). «Fáunders» y «cien» van en n14, que queda fuera de la voz.',
        asr='«¿Le llega?» con la ll rioplatense (sh) sale «Le shega» / «le chega»; «Seguir hasta lograrlo» sale «Seguirá…» en la '
            'completa; Whisper no marca la tilde de «Él»/«él» y escribe las cifras con números. Queda para la escucha.',
        pendiente='el grito «¡Ciento veintitrés!», el quiebre «¡Campeón del mundo!», «¿Le llega?» (ll rioplatense; ventana corta '
                  'vacía en la completa), «Seguir hasta lograrlo» (Whisper oye «Seguirá» en la completa), la narración sobre el colchón '
                  'y la cita con el limitador (6,80–13,05 s)'),
    'v7': dict(
        sintesis='En las frases que quedan en la voz se sintetiza «Blac Fraidei» y los números en palabras («tres», «veinticinco»). '
                 '«Fáunders» y «cien» van en m17, que queda fuera de la voz.',
        asr='«Se la pica…», en voz baja, sale «C\'est la pica» / «Es la pica»; «Llega la del Mundial» sale «Llegala» / «Llegó a la»; '
            '«Seguir hasta lograrlo» sale «Seguirá…»; Whisper no marca la tilde de «él» («Otra vez el») y escribe las cifras con '
            'números. Queda para la escucha.',
        pendiente='el grito «¡Gol!», el quiebre «Tres derrotas.», «Se la pica…» y «Queda solo…» en voz baja (Whisper oye «C\'est la '
                  'pica»), «Llega la del Mundial» (ll rioplatense; Whisper oye «Llegala»), «Seguir hasta lograrlo» (Whisper oye «Seguirá»), '
                  'la narración sobre el colchón y la cita con el limitador (11,89–17,49 s)'),
}


def limitador_en_tramo(k, t0, t1):
    """reducción del limitador en un tramo: la mezcla previa × ganancia contra la salida limitada, ventanas de 50 ms."""
    import soundfile as sf
    g = json.load(open(TP / 'audio' / 'audio.json'))[k]['ganancia_db']
    pre, sr = sf.read(str(TP / 'audio' / f'{k}_pre.wav')); out, _ = sf.read(str(TP / 'audio' / f'{k}.wav'))
    pre = pre * 10 ** (g / 20); w = int(0.05 * sr); r = []
    for i in range(int(t0 * sr), int(t1 * sr) - w, w):
        e1 = np.sqrt((pre[i:i + w] ** 2).mean())
        if e1 > 1e-4:
            r.append(20 * math.log10(np.sqrt((out[i:i + w] ** 2).mean()) / e1 + 1e-12))
    r = np.array(r)
    return dict(mediana_db=round(float(np.median(r)), 1), peor_db=round(float(r.min()), 1),
                ventanas_mas_de_1db_pct=round(float((r < -1).mean() * 100), 1))


def etapa_entregar_v02():
    """copia sin pisar junto a v01 + hoja v02 con SOLO lo que cambió (todo sale de los JSON medidos)."""
    assert P['version'] == 'v02'
    CO, MA = TP / 'control', TP / 'master'
    rep = json.load(open(CO / 'control.json'))
    nar = json.load(open(TP / 'narracion.json'))
    pl = json.load(open(TP / 'placa' / 'placa.json'))
    aud = rep['audio']
    v01 = json.load(open(T3 / P['pieza'] / 'control' / 'control.json'))
    D = PIEZAS / P['nombre']; assert D.exists()
    copias = {}
    for k, nombre in P['archivos'].items():
        cp = copiar_sin_pisar(MA / nombre, D / nombre)
        assert cp['sha256_master'] == rep['archivos'][k]['sha256']
        assert U.md5_stream(D / nombre, 'v') == rep['archivos'][k]['md5_flujo_video']
        assert U.md5_stream(D / nombre, 'a') == rep['archivos'][k]['md5_flujo_audio']
        cuerpo = (D / nombre).read_bytes()
        cp['marcas_ubicacion'] = [m_.decode() for m_ in (b'ISO6709', b'\xa9xyz', b'com.apple.quicktime.location', b'location')
                                  if m_ in cuerpo]
        cp['decodifica'] = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(D / nombre), '-f', 'null', '-'],
                                          capture_output=True, text=True).stderr.strip() == ''
        copias[k] = cp
    hoja_img = D / '02_pedro_hoja_0,5s_v02.jpg'
    copiar_sin_pisar(CO / 'hoja_0,5s.jpg', hoja_img)
    jdump(copias, CO / 'entrega.json')
    rv = rangos_visibles(); tc, ts = rep['archivos']['completa'], rep['archivos']['sinmusica']
    nz = P['narracion']; fr = nar['frases']; n_ = {f['id']: f for f in fr}
    L = []; w = L.append
    w(f"# LIFE T3 · {P['titulo']} · máster v02 · hoja de Pedro · 26/11/2026\n")
    w('Solo lo que cambió desde v01. Para todo lo demás (clips, recortes, separación, marcas, cita, negro, logo) vale '
      '`01_pedro_hoja_master_v01.md`. **No se publicó nada, no hubo commit ni push y se usaron 0 créditos.** **El audio no '
      'se escuchó:** se midió con ebur128, niveles, voz contra fondo y Whisper (faster-whisper `small`, sin texto de '
      'contexto). La imagen se revisó por fotogramas, sin reproducir el video en tiempo real.\n')
    w('## Qué cambió\n')
    ult = P['planos'][-1]; o_pl = P['negro'][1] + 1; c_ = o_pl + 138; dn = P['cta_dn']
    w(f"1. **Narración con la voz oficial de Roccé** (voz dirigida): {len(fr)} frases de la capa "
      f"{'07' if P['pieza'] == 'v6' else '08'} de Fede, con los ajustes de Roma. Las demás frases salen de la voz y quedan escritas (abajo, con el motivo).")
    w(f"2. **«Va a haber 100 Founders como máximo» +0,5 s:** c{c_}–c{c_ + dn - 1} ({s_(c_)}–{s_(c_ + dn)} s, 1,20 s; en v01 0,70 s). "
      f"El CTA y la firma van desde c{c_ + dn} ({s_(c_ + dn)} s) hasta el final. Plano {ult['id']}: IMG_5325 de 11,2 a 13,4 s "
      f"(en v01 11,7–13,4). La pieza dura {s_(P['NF'])} s ({P['NF']} cuadros; v01: {s_(P['NF'] - 15)} s).")
    if P['pieza'] == 'v7':
        w('3. **Textos:** «2021: otra final.» → «2021» y «Queda solo.» → «Solo.» (la voz los dice). Rótulo de c351–390: '
          '«COPA AMÉRICA 2024 · SU ÚLTIMO PARTIDO EN LA SELECCIÓN».')
    pj = json.load(open(TP / 'planos.json'))
    cop = [p['id'] for p in pj['planos'] if p.get('reutilizado')]
    w(f"\nLo demás es el montaje de v01. En la base sin pérdida, los planos {cop[0]} a {cop[-1]} (c0–c{c_ - 1}) son los mismos cuadros Y′CbCr de "
      f"la base v01 (copiados y comprobados en la receta; el negro, byte a byte); solo se compuso {ult['id']}. La voz real es el mismo corte.\n")
    # --- archivos
    w('## Archivos\n')
    w('| versión | archivo entregado | bytes | sha256 del archivo entregado | sha256 del máster (sin C2PA) | md5 del flujo de video | md5 del flujo de audio |')
    w('|---|---|---|---|---|---|---|')
    for k, nombre in P['archivos'].items():
        t, cp = rep['archivos'][k], copias[k]
        w(f"| {k} v02 | `{D / nombre}` | {cp['bytes_entregado']} | `{cp['sha256_entregado']}` | `{t['sha256']}` | "
          f"`{t['md5_flujo_video']}` | `{t['md5_flujo_audio']}` |")
    w('\n**ID inmutable del máster: el md5 de los flujos.** Como en v01, el almacenamiento agrega al guardar una caja C2PA '
      '(«Anthropic Files»). Sin esa caja y el corrimiento que deja en `stco`, cada archivo entregado es idéntico byte a byte '
      f"al máster, y los md5 de los flujos son los del control. Decodificación del entregado: completa "
      f"{'sin errores' if copias['completa']['decodifica'] else 'CON ERRORES'}, sin música "
      f"{'sin errores' if copias['sinmusica']['decodifica'] else 'CON ERRORES'}. Marcas de ubicación: "
      f"{copias['completa']['marcas_ubicacion'] or 'ninguna'} / {copias['sinmusica']['marcas_ubicacion'] or 'ninguna'}. "
      f"Las dos versiones comparten el flujo de video. Los v01 siguen en la misma carpeta, sin tocar.\n")
    # --- formato y sonoridad
    w('## Formato (ffprobe), sonoridad (ebur128 sobre el MP4) y duración\n')
    w('| | completa | sin música |')
    w('|---|---|---|')
    v1, v2 = tc['video'], ts['video']
    fila = lambda n, x, y: w(f'| {n} | {x} | {y} |')
    fila('video', f"{v1['codec']} {v1['perfil']} {v1['nivel']}, {v1['pix_fmt']}, {v1['ancho']}×{v1['alto']}, {v1['fps']}, "
                  f"{v1['rango']}/{v1['matriz']}/{v1['transferencia']}/{v1['primarios']}",
         f"{v2['codec']} {v2['perfil']} {v2['nivel']}, {v2['pix_fmt']}, {v2['ancho']}×{v2['alto']}, {v2['fps']}, "
         f"{v2['rango']}/{v2['matriz']}/{v2['transferencia']}/{v2['primarios']}")
    fila('audio', f"{tc['audio']['codec']} {tc['audio']['perfil']}, {tc['audio']['hz']} Hz, {tc['audio']['canales']} canales",
         f"{ts['audio']['codec']} {ts['audio']['perfil']}, {ts['audio']['hz']} Hz, {ts['audio']['canales']} canales")
    fila('duración video / audio (s) · cuadros', f"{v1['duracion']:.4f} / {tc['audio']['duracion']:.4f} · {tc['cuadros_decodificados']}",
         f"{v2['duracion']:.4f} / {ts['audio']['duracion']:.4f} · {ts['cuadros_decodificados']}")
    fila('audio = video', 'sí' if tc['audio_igual_video'] else '**no**', 'sí' if ts['audio_igual_video'] else '**no**')
    fila('decodificación completa · faststart', f"{'sin errores' if tc['decodifica_completo'] else tc['errores_decodificacion']} · {tc['faststart']}",
         f"{'sin errores' if ts['decodifica_completo'] else ts['errores_decodificacion']} · {ts['faststart']}")
    so1, so2 = tc['sonoridad'], ts['sonoridad']
    cum = lambda so: 'cumple' if -15 <= so['lufs_integrado'] <= -13 and so['pico_real_dbtp'] <= -1 else '**NO cumple**'
    fila('LUFS integrado · pico real · LRA', f"{so1['lufs_integrado']} LUFS · {so1['pico_real_dbtp']} dBTP · {so1['lra']} LU ({cum(so1)})",
         f"{so2['lufs_integrado']} LUFS · {so2['pico_real_dbtp']} dBTP · {so2['lra']} LU ({cum(so2)})")
    fila('silencio al final', f"{tc['silencio_final_s']} s", f"{ts['silencio_final_s']} s")
    lh = lambda k: aud[k]['limitador_con_aac'][-1]
    fila('limitador (alimiter level=false): techo · pico real del AAC de prueba', f"{f_(lh('completa')['techo_dbfs'], 1)} dBFS · {f_(lh('completa')['pico_aac'], 1)} dBTP",
         f"{f_(lh('sinmusica')['techo_dbfs'], 1)} dBFS · {f_(lh('sinmusica')['pico_aac'], 1)} dBTP")
    w('\nEl techo del limitador baja hasta que el pico real medido después del AAC queda ≤ −1,2 dBTP. En el primer render de V6, el '
      'AAC subía 2 dB el golpe agudo de 4,50 s (+0,2 / +1,0 dBTP).' if P['pieza'] == 'v6' else '')
    # --- voz oficial
    vo = nar['voz']; hs = vo['sha256_voz_dirigida']; cm = nar['control_muestra_oficial']
    w('\n## Voz oficial (`/mnt/project-files/voz_rocce/`)\n')
    w(f"- `voz_dirigida.py`: sha256 `{hs['oficial_voz_rocce']}` en `voz_rocce/`, el mismo de `/mnt/project-files/voz/` y el de la "
      f"copia usada (`{NARR / 'voz_dirigida.py'}`, sin modificar). LEEME_VOZ_OFICIAL no trae el hash del script (SHA256.txt trae los de la "
      "muestra); la comparación es contra el archivo oficial. Los parámetros de cada marca de la tabla del LEEME son los de "
      "`ESTILOS` del script. Voz `" + vo['voz'] + "`, edge-tts 7.3.1 y parselmouth 0.4.7 (voz-env). **Son idénticos: no se volvió a "
      "sintetizar.** Las frases salieron de la corrida de hoy con esa misma receta.")
    w(f"- Control de que el servicio da la misma voz: w4 y w3 de la muestra, resintetizadas hoy con la receta, contra "
      f"`muestra_04_v02/`. w4: forma de onda {f_(cm['w4']['correlacion_forma_de_onda'], 4)}, espectrograma "
      f"{f_(cm['w4']['correlacion_espectrograma_log'], 4)}, RMS {f_(cm['w4']['rms_db_hoy'])} / {f_(cm['w4']['rms_db_muestra'])} dB. "
      f"w3 (grito y quiebre): espectrograma {f_(cm['w3']['correlacion_espectrograma_log'], 4)}, RMS {f_(cm['w3']['rms_db_hoy'])} / "
      f"{f_(cm['w3']['rms_db_muestra'])} dB. F0 mediana: {cm['f0_mediana_hz']}. No son idénticas byte a byte "
      f"({cm['w4']['muestras_hoy']} contra {cm['w4']['muestras_muestra']} muestras en w4): el servicio no devuelve el mismo MP3 en cada llamada.")
    w(f"- {NOTAS_HOJA_V02[P['pieza']]['sintesis']} En pantalla quedan la grafía real y las cifras.\n")
    # --- narración
    w('## Narración: frases, tiempos y Whisper sobre el máster\n')
    w(f"Whisper corre sobre la ventana de cada frase en el MP4 (±0,15 s), completa y sin música. Grito: "
      f"{nz['grito']} «{TEXTO_NARR[nz['grito']]}». Quiebre: {nz['quiebre']} «{TEXTO_NARR[nz['quiebre']]}» (^ en "
      f"`{n_[nz['quiebre']]['guion_tsv']}`).\n")
    w('| frase | dice (capa de Fede) | marca | habla en el máster (s) | cuadros | Whisper · completa | Whisper · sin música |')
    w('|---|---|---|---|---|---|---|')
    wm = {(x['frase'], x['version']): x for x in rep['narracion_en_master']}
    for f in fr:
        a, b = f['habla_master_s']
        w(f"| {f['id']} | {f['texto']} | {' · '.join(f['estilos'])} | {f_(a)}–{f_(b)} | c{f['cuadros_habla'][0]}–c{f['cuadros_habla'][1]} | "
          f"«{wm[(f['id'], 'completa')]['texto']}» | «{wm[(f['id'], 'sinmusica')]['texto']}» |")
    w(f"\nLa primera frase entra en {f_(fr[0]['habla_master_s'][0])} s, no en 0,05 s como en la capa: así el ataque del impacto de c0 (el gancho) "
      "suena entero antes de la voz.")
    an = CO / 'whisper_n02_ventanas_anchas.json'
    if an.exists():
        r_ = {Path(a_).name: ' '.join(x['texto'] for x in b_) for a_, b_ in json.load(open(an)).items()}
        w(f"\nn02 en la completa: la ventana de ±0,15 s sale vacía. Con más contexto se lee: 0,80–1,90 s «{r_.get('n02_ancha.wav')}» y "
          f"0,00–2,40 s «{r_.get('n01_n03.wav')}» (`{an}`).")
    w(f"\nLecturas de Whisper que no son la frase, anotadas tal cual: {NOTAS_HOJA_V02[P['pieza']]['asr']}\n")
    w('**Frases que salen de la voz y quedan escritas** (no entran a ritmo natural):\n')
    for x in nar['fuera_de_la_voz']:
        w(f"- {x['id']} «{x['texto']}»: {x['motivo']}.")
    # --- grito, golpe, aire, niveles
    gc = nz['grito_cuadro']
    w('\n## Grito, golpe y aire contra la voz real\n')
    if P['pieza'] == 'v6':
        w(f"- El grito entra en c{gc} ({s_(gc)} s), con el renglón «Minuto 123. 3-3.». El golpe que caía ahí (latido y acorde de "
          f"5,30 s de la música TEMP) pasa a c{gc - 1} a ×0,6. En la sin música no hay golpe en ese momento. Antes del grito hay un tramo "
          f"calmo: la última frase termina en {f_(n_['n06']['habla_master_s'][1])} s.")
    else:
        w(f"- El grito «¡Gol!» entra en c{gc} ({s_(gc)} s). El golpe del gol (impacto + golpe grave del texto «Gol.», el bombo de la "
          f"música) queda en c{gc - 1}, el cuadro en que la pelota cruza y entra el color, a ×0,6. Antes, «Queda solo…» y «Se la pica…» "
          f"en voz baja, con silencio entre {f_(n_['m08']['habla_master_s'][1])} y {f_(n_['m09']['habla_master_s'][0])} s. "
          "«¡Otra vez él!» va en enérgico, sin grito.")
    ai = nar['aire_voz_real']
    w(f"- Aire contra la voz real (habla medida en su WAV, ventanas de 10 ms a menos de 30 dB del máximo: "
      f"{f_(ai['voz_real_habla_s'][0])}–{f_(ai['voz_real_habla_s'][1])} s): la narración termina en {f_(ai['narracion_termina_antes_s'])} s "
      f"(**{f_(ai['aire_antes_s'])} s antes**) y vuelve en {f_(ai['narracion_vuelve_s'])} s (**{f_(ai['aire_despues_s'])} s después**). "
      f"Contra los bordes del corte ({f_(ai['voz_real_corte_s'][0])}–{f_(ai['voz_real_corte_s'][1])} s, con el aire de la toma): "
      f"{f_(ai['aire_antes_del_corte_s'])} s y {f_(ai['aire_despues_del_corte_s'])} s.")
    nv = aud['completa']['narracion']['niveles']
    pf = nv['por_frase']
    hm = [x['sonoridad_habla_mezcla'] for x in pf.values()]; mm = [x['momentanea_max_mezcla'] for x in pf.values()]
    w(f"- Nivel (ponderación K, antes del limitador; el limitador afecta igual a las dos voces): voz real "
      f"{f_(nv['voz_real_sonoridad_habla'], 1)} LUFS de habla y {f_(nv['voz_real_momentanea_max'], 1)} de momentánea máxima. "
      f"Narración: {f_(min(hm), 1)} a {f_(max(hm), 1)} de habla (rango {f_(max(hm) - min(hm), 1)} dB) y {f_(max(mm), 1)} de momentánea máxima. "
      f"**El narrador nunca está más fuerte que la voz real.**")
    bj = [fid for fid in pf if 'bajo' in n_[fid]['estilos']]
    al_borde = {fid: x['llevada_al_borde_db'] for fid, x in pf.items() if x['llevada_al_borde_db']}
    w(f"- Mezcla de la voz oficial: la salida de la receta, con la voz baja +5 dB y el grito y el CTA +2 dB. Encima va la regla de Fede "
      f"(±3 dB del resto): lo que quedaba a más de 3 dB de la mediana se llevó al borde "
      f"({', '.join(f'{k} {v:+.1f} dB'.replace('.', ',') for k, v in al_borde.items()) or 'ninguna'}). "
      + (f"[bajo] ({', '.join(bj)}): " + ', '.join(f"{k} {pf[k]['offset_oficial'] + pf[k]['llevada_al_borde_db']:+.1f} dB".replace('.', ',') for k in bj)
         + ' sobre la salida de la receta.' if bj else '[bajo]: ninguna frase [bajo] quedó en la voz (n09 «Mano a mano…», la única, quedó fuera).'))
    w('\n## Narración contra el fondo, frase por frase\n')
    w(f"El fondo (ambiente, efectos, música y bombo) cede {f_(DUCK_NARR, 0)} dB por envolvente con la narración (voz oficial), y además se "
      'ajusta frase por frase. Los efectos bajan 6 dB mientras habla, para los golpes que pisan una palabra. Se mide en ventanas de 50 ms '
      'de habla, antes del limitador. Objetivo: 10–15 dB (completa 11–14, sin música 13–15).\n')
    w('| frase | completa: voz − fondo (mediana · mín–máx) | ajuste del fondo | sin música: voz − fondo | ajuste del fondo |')
    w('|---|---|---|---|---|')
    nc, ns = aud['completa']['narracion'], aud['sinmusica']['narracion']
    for f in fr:
        a1, a2 = nc['voz_vs_fondo'][f['id']], ns['voz_vs_fondo'][f['id']]
        nota = lambda r: '' if 10 <= r['dif_mediana_db'] <= 15 else (f" (fondo {f_(r['fondo_mediana_dbfs'], 1)} dBFS)" if r['fondo_mediana_dbfs'] > -200 else ' (fondo: silencio digital)')
        w(f"| {f['id']} | {f_(a1['dif_mediana_db'], 1)} · {f_(a1['dif_min_db'], 1)}–{f_(a1['dif_max_db'], 1)}{nota(a1)} | "
          f"{nc['ajuste_fondo_db'][f['id']]:+.1f} dB | {f_(a2['dif_mediana_db'], 1)} · {f_(a2['dif_min_db'], 1)}–{f_(a2['dif_max_db'], 1)}{nota(a2)} | "
          f"{ns['ajuste_fondo_db'][f['id']]:+.1f} dB |".replace('+-', '−'))
    oc, os_ = nc['offset_seccion_db'], ns['offset_seccion_db']
    aj = [v_ for v_ in nc['ajuste_fondo_db'].values()]
    w(f"\nEl colchón de v01 se hizo sin narración (latidos, bombo y golpes al frente). La narración no sube: tiene que quedar bajo la voz real. "
      f"Por eso el fondo de las partes narradas baja parejo. Completa: {f_(oc['antes_de_la_cita'], 1)} dB antes de la cita y "
      f"{f_(oc['despues_de_la_cita'], 1)} dB después. Sin música: {f_(os_['antes_de_la_cita'], 1)} y {f_(os_['despues_de_la_cita'], 1)} dB. "
      "Es la mediana de lo que pedían sus frases en la primera pasada, con 6 dB menos de recorte (nunca positivo), y entra con rampas. Dentro de la cita no cambia nada: el colchón es el de v01. "
      f"Encima, cada frase ajusta el resto (completa: de {f_(min(aj), 1)} a {f_(max(aj), 1)} dB) y el fondo cede 12 dB por envolvente. "
      "Entre frases separadas por menos de 1 s el colchón no vuelve (sin bombeo). Los golpes entre frases quedan enteros; los que pisan "
      "una palabra suenan 6 dB más bajos.")
    fuera = [(k, f['id']) for k, nn in (('completa', nc), ('sinmusica', ns)) for f in fr
             if not (10 <= nn['voz_vs_fondo'][f['id']]['dif_mediana_db'] <= 15)]
    if fuera:
        w(f"\nFuera de 10–15 dB: {', '.join(f'{b} ({a})' for a, b in fuera)}. "
          + ('Todas por arriba y en la sin música, donde el fondo bajo esas frases es solo el murmullo sintético (−46 a −50 dBFS) o nada (después '
             'del negro solo quedan los barridos y el sub-golpe del cierre). Ahí el ajuste ya devolvió todo lo que había bajado: no hay colchón que '
             'subir sin agregar sonido, y la narración no sube porque tiene que quedar bajo la voz real.'
             if all(a == 'sinmusica' and nn_['voz_vs_fondo'][b]['dif_mediana_db'] > 15 for a, b in fuera for nn_ in [ns]) else '**Revisar.**'))
    gb = nc['golpes_bajo_las_palabras_menos6db']
    lista = sorted({f"c{g['cuadro']} {g['tipo']} ({g['frase']}) bajo {g['bajo_la_narracion']}" for g in gb})
    w(f"\nGolpes de texto que caen dentro de una frase y suenan 6 dB más bajos: {', '.join(lista) or 'ninguno'}.\n")
    # --- voz real
    w('## Voz real contra fondo (sin cambios de método)\n')
    w('| versión | v01: mediana · mín–máx | v02: mediana · mín–máx |')
    w('|---|---|---|')
    for k in ('completa', 'sinmusica'):
        a1, a2 = v01['audio'][k]['voz_vs_fondo'], aud[k]['voz_vs_fondo']
        w(f"| {k} | {f_(a1['dif_mediana_db'], 1)} · {f_(a1['dif_min_db'], 1)}–{f_(a1['dif_max_db'], 1)} dB | "
          f"{f_(a2['dif_mediana_db'], 1)} · {f_(a2['dif_min_db'], 1)}–{f_(a2['dif_max_db'], 1)} dB |")
    w(f"\nWhisper sobre la cita en el máster v02: completa «{rep['voz_en_master'].get('voz_en_master_completa', '')}» · sin música "
      f"«{rep['voz_en_master'].get('voz_en_master_sinmusica', '')}». En v01: completa «{v01['voz_en_master'].get('voz_en_master_completa', '')}» · "
      f"sin música «{v01['voz_en_master'].get('voz_en_master_sinmusica', '')}».\n")
    # --- para la escucha: el limitador en la cita
    vz = P['voz']; c0, c1 = vz['m0'], vz['m0'] + vz['src1'] - vz['src0']
    lc = {k: limitador_en_tramo(k, c0, c1) for k in P['archivos']}
    lr = {k: limitador_en_tramo(k, 0.0, c0 - 0.3) for k in P['archivos']}
    jdump(dict(cita=lc, antes_de_la_cita=lr), CO / 'limitador_por_tramo.json')
    ga = {k: aud[k]['ganancia_db'] for k in P['archivos']}; g1 = {k: v01['audio'][k]['ganancia_db'] for k in P['archivos']}
    w('## Para Roma: el limitador en la cita (segundo exacto y propuesta)\n')
    w(f"Para cumplir a la vez −14 LUFS, la narración 10–15 dB sobre su fondo y el narrador nunca más fuerte que la voz real, la cita "
      f"queda como el tramo más fuerte de la pieza. La ganancia final de la mezcla pasa de {f_(g1['completa'], 1)} dB (v01) a "
      f"{f_(ga['completa'], 1)} dB (completa); sin música, de {f_(g1['sinmusica'], 1)} a {f_(ga['sinmusica'], 1)}. Por eso el limitador "
      f"(alimiter, level=false) ahora trabaja en la cita, {f_(c0)}–{f_(c1)} s. Completa: mediana {f_(lc['completa']['mediana_db'], 1)} dB, "
      f"{f_(lc['completa']['ventanas_mas_de_1db_pct'], 1)} % de las ventanas de 50 ms con más de 1 dB y la peor "
      f"{f_(lc['completa']['peor_db'], 1)} dB. Sin música: {f_(lc['sinmusica']['ventanas_mas_de_1db_pct'], 1)} % y "
      f"{f_(lc['sinmusica']['peor_db'], 1)} dB. Antes de la cita: peor {f_(lr['completa']['peor_db'], 1)} / {f_(lr['sinmusica']['peor_db'], 1)} dB. "
      "Son las puntas de la voz real (y del colchón que va con ella). No se escuchó.\n")
    w(f"**Propuesta**, si en la escucha la cita suena apretada en {f_(c0)}–{f_(c1)} s: (a) entregar a −14,8 LUFS (dentro de ±1): el "
      "limitador recibe 0,8 dB menos. (b) Bajar 2–3 dB solo las puntas de la voz real antes de la mezcla, para que el limitador general "
      "no apriete también el colchón: no cambia lo que dice, sí su dinámica, y por eso lo decide Roma.\n")
    # --- textos que cambiaron
    w('## Textos e imagen que cambiaron\n')
    w('| id | en pantalla | guion | igual | cuadros visibles |')
    w('|---|---|---|---|---|')
    ids = ['founders', 'cta', 'bf_cta'] + (['p1a', 'p2', 'rotulo2'] if P['pieza'] == 'v7' else [])
    for k in ids:
        x = rep['textos_vs_guion'][k]; r = rv.get(k)
        w(f"| {k} | {x['visible']} | {x['guion']} | {'sí' if x['igual'] else '**no**'} | c{r[0]}–c{r[1]} |")
    w(f"| firma | logo + «ROCCÉ LIFE» | firma | sí | c{pl['cuadros']['firma'][0]}–c{pl['cuadros']['firma'][1]} |")
    mal = [k for k, x in rep['textos_vs_guion'].items() if not x['igual'] and k != 'atrib_voz']
    w(f"\nEl resto de los textos es igual a v01 (control carácter por carácter: distintos del guion, además de la atribución "
      f"ya explicada en v01: {mal or 'ninguno'}). Sin subtítulos automáticos. El primer cuadro con oferta es "
      f"c{rep['separacion']['primer_cuadro_con_oferta']}, después del negro (c{P['negro'][0]}–c{P['negro'][1]}). NCC del logo entre c0 y el "
      f"negro: máximo {rep['logo']['ncc_max_c0_hasta_negro']}, contra {rep['logo']['ncc_firma_min']}–{rep['logo']['ncc_firma_max']} en la firma.\n")
    w('## Hoja de fotogramas\n')
    w(f"`{hoja_img}`: un cuadro cada 15 (0,5 s) del máster completo v02, de c0 a c{P['NF'] - 1}.\n")
    w('## Verificado / revisado a ojo / pendiente\n')
    w('- **Verificado técnicamente:** sha256 de la receta de voz contra la oficial, frases y tiempos medidos en sus WAV, aire contra la '
      'voz real, sonoridad de narrador contra voz real, voz contra fondo por frase, Whisper por ventana en los dos MP4, ffprobe, '
      'ebur128, md5 de los flujos, decodificación, duración de audio igual a la de video, textos carácter por carácter, oferta después '
      'del negro y NCC del logo.')
    w('- **Revisado a ojo (fotogramas):** el plano del CTA desde 11,2 s (bordado entero, sin la subida de cámara), Founders y CTA sin tapar '
      'el bordado' + (', «2021», «Solo.» y el rótulo largo dentro del ancho' if P['pieza'] == 'v7' else '') + '.')
    w(f"- **Pendiente de revisión humana:** escuchar las dos versiones enteras. En especial {NOTAS_HOJA_V02[P['pieza']]['pendiente']}. "
      'También mirarlo en un teléfono. Nadie del equipo puede escuchar: la escucha final es de Gianluca.')
    md = D / '02_pedro_hoja_master_v02.md'
    texto = '\n'.join(L) + '\n'
    if md.exists() and md.read_text(encoding='utf-8') != texto:
        raise SystemExit(f'{md} ya existe con otro contenido: no se pisa')
    md.write_text(texto, encoding='utf-8')
    print(md)
    print(json.dumps({k: dict(md5_flujo_video=t['md5_flujo_video'], md5_flujo_audio=t['md5_flujo_audio'], sonoridad=t['sonoridad'],
                              sha256=t['sha256']) for k, t in rep['archivos'].items()}, ensure_ascii=False))


if __name__ == '__main__':
    activar(sys.argv[1])
    globals()['etapa_' + sys.argv[2]]()
