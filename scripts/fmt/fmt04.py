#!/usr/bin/env python3
"""FMT-04 · «Pasale el dedo» · máster v01 y v02 · receta reproducible (Pedro, 17/11/2026).

Guion: /mnt/project-files/piezas/FMT_tanda_formatos/FMT-04_pasale_el_dedo/01_fede_guion_G1.md (G1, hook A)
Aprobación: 02_roma_aprobacion_G1.md (misma carpeta). Especificación: ../06_especificacion_comun.md.

Uso (con nice; la CPU es compartida). Versión con FMT04_VERSION (por defecto v02; v01 se reproduce igual que se entregó):
    FMT04_VERSION=v02 nice -n 10 /home/user/1/TRABAJO/venv/bin/python /home/user/1/scripts/fmt/fmt04.py todo
    ... fmt04.py planos | textos | audio | master | entregar | propuesta_b5 | propuesta_b5_ancha

v02 (dictamen de Roma 04_roma_dictamen_master_v01.md): B3 = 8004 3,20–3,70 (c120–c134); B4 = 7824 5,50–8,00 (c135–c209,
z 1,0→1,6 hasta el final, centro que acompaña al ROCCÉ para cerrar con el mismo encuadre que v01); B5 = 7859 con ventana
1888×2160 en y 460 sobre relleno desenfocado de la misma toma; sin música: tono de ambiente bajo en c60–c89.

Decisiones que se apartan del guion (detalle y medición en 03_pedro_hoja_master_v01.md):
  * B5 = reemplazo del guion (IMG_7824 6,00–9,00) por la indicación 2 de Roma: con la ventana 4:5 de 7859 pegada en
    y 420 el pelo queda a < 40 px del «link en bio» en todos los cuadros del CTA y la remera toca el margen al final.
    El compuesto de 7859 queda en esta receta (B5_MODO = 'compuesto_7859') y en propuesta_b5() para v02.
  * B4: el acercamiento 1,00→1,60 se hace con fmt04_util.plano_zoom (video.plano con z0≠z1 no anima en FFmpeg 6.1).
  * Foley: R3 dura 0,60 s (c38–c56) y R4 0,35 s (c90–c100): es lo que dura el movimiento medido a 30 cps.
  * CTA sobre cielo claro: degradé oscuro suave detrás (CLAUDE.md, «Texto sobre fondo claro»), metido en el plano B5
    (el overlay de video.master entraba en c209, un cuadro antes del corte); entra en c236–c240 y queda con el CTA;
    con clave de luminancia, no toca la tela negra.
"""
import sys, os, json, shutil, subprocess, time, hashlib
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V
import sonido as S
from sonido import Mezcla
import fmt04_util as U

VERSION = os.environ.get('FMT04_VERSION', 'v02')
NOMBRE = 'ROCCE_FMT04_PASALE_EL_DEDO'
BASE = Path('/home/user/1/TRABAJO/fmt/fmt04')
D = BASE if VERSION == 'v01' else BASE / VERSION; PL = D / 'planos'; AU = D / 'audio'
EXPO = Path('/home/user/1/EXPORTACIONES')
PIEZA = Path('/mnt/project-files/piezas/FMT_tanda_formatos/FMT-04_pasale_el_dedo')
# B5: v01 = reemplazo del guion (indicación 2 de Roma); v02 = 7859 con ventana 1888×2160 en y 460 (dictamen de Roma)
B5_MODO = 'reemplazo_7824' if VERSION == 'v01' else 'compuesto_7859_ancho'
B5_VENTANA, B5_Y = (1888, 2160), 460
# cortes y planos (cuadro de entrada, cuadro de salida exclusivo) para el control
CORTES = [90, 120, 165, 210] if VERSION == 'v01' else [90, 120, 135, 210]
PLANOS_QC = ([('B1', 'IMG_3453', 0, 90), ('B2', 'IMG_3375', 90, 120), ('B3', 'IMG_8004', 120, 165), ('B4', 'IMG_7824', 165, 210),
              ('B5', 'IMG_7824', 210, 300)] if VERSION == 'v01' else
             [('B1', 'IMG_3453', 0, 90), ('B2', 'IMG_3375', 90, 120), ('B3', 'IMG_8004', 120, 135), ('B4', 'IMG_7824', 135, 210),
              ('B5', 'IMG_7859', 210, 300)])
B3_FUENTE = (2.50, 4.00) if VERSION == 'v01' else (3.20, 3.70)
B4_FUENTE = (5.50, 7.00) if VERSION == 'v01' else (5.50, 8.00)
RELLENO_7859 = 'crop=700:2160:0:0,scale=1080:-2,crop=1080:1920,gblur=sigma=40,eq=brightness=-0.10'
DUR = 10.0
for p in (PL, AU):
    p.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ color por toma (indicación 4 de Roma)
# Medido por Pedro el 17/11 sobre el máster contra PRODUCTO/ (qc/color.json). Se agrega en tiempo de ejecución, sin tocar
# video.py, con los mismos mecanismos de video.TOMAS ('g' = ganancias en gbrp; 'extra' = filtros después del tonemap).
#  * IMG_3453: con la corrección de video.py la Negra seguía marrón (tela 35/20/18, B−R −17; foto 21/19/20) y el
#    estampado verdoso (182/190/184). Curvas por canal: tela → 25/23/24 (carbón), estampado → 190/188/182 (gris claro
#    apenas cálido, como la foto de detalle 176/174/166).
#  * IMG_8004: la tela blanca al sol salía azulada (214/223/232, B−R +18; foto de detalle 186/186/181). Ganancias que la
#    dejan neutra con la misma luma; el celeste de «Founders Privée» queda más cerca de la foto de estudio (B/R 1,30 vs 1,26).
CURVAS_3453 = ("curves=r='0/0 0.1376/0.0980 0.7141/0.7451 1/1':g='0/0 0.0804/0.0902 0.7451/0.7373 1/1':"
               "b='0/0 0.0710/0.0941 0.7231/0.7137 1/1'")
V.TOMAS['IMG_3453'] = dict(V.TOMAS['IMG_3453'], extra=V.TOMAS['IMG_3453']['extra'] + ',' + CURVAS_3453)
V.TOMAS['IMG_8004'] = dict(V.TOMAS['IMG_8004'], g=(1.036, 0.993, 0.955))
#  * IMG_7859 (v02, B5): la Blanca puesta frente al mar nublado salía celeste (tela 158/162/176, B−R +17,4, medido en
#    c225/c260/c290 del primer render de v02). Ganancias que la llevan a B−R ≈ +4, como la Blanca de 8004 en B3 (+4,8).
if VERSION != 'v01':
    V.TOMAS['IMG_7859'] = dict(V.TOMAS['IMG_7859'], g=(1.02, 1.0, 0.945))


# ------------------------------------------------------------------ imagen
def ventana_7859(t0=0.0, t1=3.0, y_dest=420):
    """X(t) de la ventana 4:5 (1728 px) centrada en la remera: centro = centro de ROCCÉ + desvío medido de la remera
    (29 px en 0,0 s y 67 px en 3,0 s, mangas medidas con regla sobre los cuadros completos), suavizado 9 cuadros."""
    tr = U.seguir_torso_7859(t0, t1)
    t = np.array([d['t'] for d in tr]); cx = np.array([(d['roc_x0'] + d['roc_x1']) / 2 for d in tr], float)
    w = np.array([d['roc_x1'] - d['roc_x0'] for d in tr], float)
    off = 29 + (67 - 29) * (t / 3.0)
    centro = cx + off
    k = 9; pad = np.pad(centro, (k // 2, k // 2), mode='edge'); suave = np.convolve(pad, np.ones(k) / k, 'valid')
    xs = suave - 864
    medio_ancho = w * (0.8385 + (0.8475 - 0.8385) * (w - 820) / (956 - 820))   # mangas: 1375 px a 0 s, 1620 px a 3 s
    esc = 1080 / 1728
    filas = []
    for i, d in enumerate(tr):
        izq = (centro[i] - medio_ancho[i]) - xs[i]; der = xs[i] + 1728 - (centro[i] + medio_ancho[i])
        filas.append(dict(t=d['t'], x_ventana=round(float(xs[i]), 1), margen_remera_izq_master=round(izq * esc, 1),
                          margen_remera_der_master=round(der * esc, 1),
                          pelo_y_master=None if d.get('pelo_y0') is None else round(y_dest + d['pelo_y0'] * esc, 1),
                          founders_y1_master=None if d.get('founders_y1') is None else round(y_dest + d['founders_y1'] * esc, 1)))
    return xs, filas


# B4 v02: cierre con el mismo encuadre que v01 (z 1,6, ROCCÉ arriba en y ≈ 715). Medido en la toma (v02/an/roc7824.json,
# detector de fmt04_qc.roc_b4 a escala 0,5): el borde superior de ROCCÉ está en y 1394 a 6,967 s (cierre de v01) y en
# y 1688 a 7,967 s (cierre de v02) → el centro baja de 1700 a 1994 en línea recta mientras se acerca; cx queda en 1125
# (centro de ROCCÉ 1108–1117 en los dos cierres).
B4_CX, B4_CY = 1125, (1700, 1994)


def planos():
    p = [V.plano('IMG_3453', 0.20, 3.20, PL / 'p1_3453.mp4'),                         # B1 c0–c89   nativa
         V.plano('IMG_3375', 0.40, 1.40, PL / 'p2_3375.mp4')]                         # B2 c90–c119 nativa
    if VERSION == 'v01':
        p += [V.plano('IMG_8004', 2.50, 4.00, PL / 'p3_8004.mp4', caja=(0, 0, 2160, 3840)),  # B3 c120–c164
              U.plano_zoom('IMG_7824', 5.50, 7.00, PL / 'p4_7824.mp4', (0, 0, 2160, 3840), 1.0, 1.6, 1125, 1700)]  # B4
    else:
        nf4 = round((B4_FUENTE[1] - B4_FUENTE[0]) * 30)
        cy = lambda k: B4_CY[0] + (B4_CY[1] - B4_CY[0]) * k / (nf4 - 1)
        p += [V.plano('IMG_8004', *B3_FUENTE, PL / 'p3_8004.mp4', caja=(0, 0, 2160, 3840)),          # B3 c120–c134
              U.plano_zoom('IMG_7824', *B4_FUENTE, PL / 'p4_7824.mp4', (0, 0, 2160, 3840), 1.0, 1.6, B4_CX, cy)]  # B4 c135–c209
    if B5_MODO == 'reemplazo_7824':
        # B5 c210–c299 (nativa) con el degradé del CTA metido en el plano (el overlay de video.master entraba 1 cuadro
        # antes, c209, medido). Entra en 4 cuadros (c236→c240) y queda completo con el CTA: el cielo sigue continuo en
        # el corte c209/c210 (misma toma que B4). Clave por luminancia: solo oscurece el cielo y lo claro (Y > 75); la
        # remera negra y el ROCCÉ tono sobre tono no se tocan
        p.append(U.plano_zoom('IMG_7824', 6.00, 9.00, PL / 'p5_7824.mp4', (0, 0, 2160, 3840), 1.0, 1.0, 1080, 1920,
                              por_cuadro=U.degrade_negro(alfa_degrade(), rampa=(26, 30), clave=(75, 125))))
    elif B5_MODO == 'compuesto_7859_ancho':
        # B5 v02: ventana 1888×2160 (más ancha que 4:5) que sigue la remera, pegada en y 460 sobre el relleno desenfocado de
        # la misma toma. El degradé del CTA (mismo perfil, rampa y clave que v01) solo sobre el relleno de arriba (y < 460):
        # no toca la ventana (la remera blanca y el chico)
        xs, _ = ventana_7859(y_dest=B5_Y); d = (B5_VENTANA[0] - 1728) / 2
        p.append(U.compuesto_ventana('IMG_7859', 0.0, 3.0, PL / 'p5_7859.mp4', [x - d for x in xs], ventana=B5_VENTANA,
                                     y_dest=B5_Y, relleno_vf=RELLENO_7859,
                                     por_cuadro=U.degrade_negro(alfa_degrade()[:B5_Y], rampa=(26, 30), clave=(75, 125))))
    else:
        xs, _ = ventana_7859()
        p.append(U.compuesto_ventana('IMG_7859', 0.0, 3.0, PL / 'p5_7859.mp4', list(xs), y_dest=420,
                                     relleno_vf=RELLENO_7859))
    n = V.unir(p, D / 'base.mp4')
    for q in p:
        q.pop('ventanas', None)
    json.dump(dict(version=VERSION, planos=p, cuadros=n, b5=B5_MODO), open(D / 'planos.json', 'w'), indent=1,
              ensure_ascii=False, default=str)
    return n


# ------------------------------------------------------------------ textos
TEXTOS = [
    dict(t0=0.0, t1=2.0, txt='Pasale el dedo.', estilo='Nativo', y=220, pop=True),                    # hook A, c0–c60
    dict(t0=2.0, t1=3.0, txt='Relieve.', estilo='Caja', y=560),                                         # c60–c90
    dict(t0=3.0, t1=4.0, txt='Dala vuelta.', estilo='CajaN', y=330),                                    # c90–c120
    dict(t0=4.0, t1=6.0, txt='Letras de denim.\\NCostura a la vista.', estilo='Caja', y=400, pop=True),  # giro c120–c180
    dict(t0=8.0, t1=10.0, txt='Hacela tuya.', estilo='Grande', y=236),                                  # CTA c240–c300
    dict(t0=8.0, t1=10.0, txt='link en bio', estilo='Chico', y=372),
]


def textos():
    V.ass(TEXTOS, D / 'textos.ass')
    return D / 'textos.ass'


def alfa_degrade():
    """degradé oscuro suave detrás del CTA (B5 sobre cielo claro): alfa 0,58 hasta y 440 (debajo de «link en bio»,
    que termina en y 407) y baja con curva suave a 0 en y 760."""
    y = np.arange(760); u = np.clip((y - 440) / (760 - 440), 0, 1)
    return (1 - u * u * (3 - 2 * u)) * 0.58


# ------------------------------------------------------------------ sonido
G_AMB = dict(IMG_8004=-2.0, IMG_7824=-8.5, IMG_7824_B5=-5.0, IMG_7859=-3.0 if VERSION == 'v01' else -7.8)
# v02: el mar de 7859 a −3 dB (guion) quedaba 16,8 dB sobre 8004 y 15,0 dB sobre 7824 (medido, audio/sonoridad.json);
# el guion pide 10–12 dB → −7,8 dB lo deja en 12,0 y 10,2 dB
GM = 10 ** (-13 / 20)   # música TEMP 13 dB más baja que los valores de sonido.py: el drop queda ≈ 6 dB arriba del foley del
                        # hook (antes, 20 dB: los primeros 2 s quedaban casi mudos después de normalizar a −14 LUFS)
G_PAD0 = 0.069          # pad de la apertura (c0–c120): foley ≥ 8 dB arriba en c0–c60 (medido en audio/niveles.json)


G_TONO_3453 = -2.6     # v02, solo sin música: tono de la sala de 3453 (fuente 2,20–3,20, hp 150: −54,9 LUFS medido) en c60–c89,
                       # ≈ 30 dB por debajo del roce (dictamen de Roma, punto 3). Con −5,6 quedó 33,1 dB abajo; con −2,6, 29,9 dB
                       # (medido sobre la mezcla sin música normalizada, audio/sonoridad.json)


def capa_ambiente(m, tono=False):
    S.rng = np.random.default_rng(101)
    t3 = 4.0 + (B3_FUENTE[1] - B3_FUENTE[0])                     # corte B3/B4: 5,5 (v01) · 4,5 (v02)
    m.ambiente('IMG_8004', B3_FUENTE[0], 4.0, t3, G_AMB['IMG_8004'], hp=120, lp=9000)
    m.ambiente('IMG_7824', B4_FUENTE[0], t3, 7.0, G_AMB['IMG_7824'], hp=150, lp=8000)
    if B5_MODO == 'reemplazo_7824':
        m.ambiente('IMG_7824', 6.00, 7.0, 10.0, G_AMB['IMG_7824_B5'], hp=150, lp=8000, fin_fade=0.25)
    else:
        m.ambiente('IMG_7859', 0.00, 7.0, 10.0, G_AMB['IMG_7859'], hp=50, fin_fade=0.25)
    if tono:                                                      # dictamen de Roma, punto 3 (solo la versión sin música)
        m.ambiente('IMG_3453', 2.20, 2.0, 3.0, G_TONO_3453, hp=150, ini_fade=0.08, fin_fade=0.08)


def capa_foley(m):
    """Foley PROVISORIO (sintético). Tiempos fijados con el movimiento medido a 30 cps (hoja de máster, §Foley)."""
    S.rng = np.random.default_rng(202)
    m.tela(0.000, .60, .14)      # R1 c0–c18   yemas suben (3453 fuente 0,20–0,80)
    m.tela(0.600, .60, .18)      # R2 c18–c36  siguen subiendo hasta el giro (fuente 0,80–1,40)
    m.tela(1.267, .60, .08)      # R3 c38–c56  bajan cruzando ROCCÉ (fuente 1,47–2,07)  [guion: 0,35]
    m.tela(3.000, .35, .10)      # R4 c90–c100 la Blanca se inclina (3375 fuente 0,40–0,77) [guion: 0,25]
    m.tela(3.600, .30, .09)      # R5 c108–c117 segundo movimiento (fuente 1,00–1,30)
    m.barrido(4.0, .30, .16)     # corte al giro c120
    t_r6 = 5.500 if VERSION == 'v01' else 4.500
    m.tela(t_r6, .40, .07)       # R6 la Negra termina de subir (7824 fuente 5,50–5,90): c165–c177 (v01) · c135–c147 (v02)
    m.subida(6.133, 6.967, .10)  # c184–c209


def capa_musica(m):
    """Música propia TEMP, 120 BPM, Re menor. Tiempo = 0,5 s = 15 cuadros; compás = 60 cuadros."""
    S.rng = np.random.default_rng(303)
    m.pad(0.0, [50, 53, 57, 64], 4.0, g=GM * G_PAD0, corte=900, a=0.30, r=0.25)          # Dm(add9) c0–c120
    m.bombo(2.0, g=GM * 0.40)                                                              # c60 suave
    m.bombo(3.0, g=GM * 0.40); m.campana(3.0, 69, g=GM * 0.05)                                  # c90 + campana A4
    m.redoble(3.5, 4.0, g=GM * 0.10)                                                       # c105–c120
    m.bombo(4.0, g=GM * 0.90); m.ocho08(4.0, 38, dur=1.45, g=GM * 0.50)                         # DROP c120: bombo + 808 D2
    m.pad(4.0, [46, 50, 53, 57], 1.45, g=GM * 0.060, corte=1400, a=0.02, r=0.20)          # B♭maj7 c120–c165
    for k in range(6):
        m.charles(4.0 + 0.25 * k, g=GM * (0.10 if k % 2 else 0.06))                          # charles en corcheas c120–c165
    m.palma(5.0, g=GM * 0.32)                                                                    # c150
    m.pad(5.5, [43, 46, 50, 57], 1.43, g=GM * 0.050, corte=700, a=0.02, r=0.15)           # Gm(add9) c165–c208
    m.ocho08(5.5, 31, dur=0.90, g=GM * 0.50)                                               # 808 G1
    m.bombo(6.0, g=GM * 0.45)                                                              # c180 suave
    m.bombo(7.0, g=GM * 0.90); m.palma(7.0, g=GM * 0.32); m.ocho08(7.0, 38, dur=0.95, g=GM * 0.50, glide_desde=45)  # c210 (glide A2→D2)
    m.pad(7.0, [50, 53, 57, 60, 64], 3.0, g=GM * 0.055, corte=1400, a=0.02, r=0.30)       # Dm9 c210–c300
    m.bombo(8.0, g=GM * 0.90); m.campana(8.0, 81, g=GM * 0.06); m.ocho08(8.0, 38, dur=1.40, g=GM * 0.50)  # c240 CTA


def construir(capas):
    m = Mezcla(DUR)
    if 'amb' in capas: capa_ambiente(m, tono='tono' in capas)
    if 'foley' in capas: capa_foley(m)
    if 'mus' in capas: capa_musica(m)
    # hueco c208–c210 (casi silencio: queda el ambiente) y fundido final de la música c285–c300
    m.silenciar('mus', 6.933, 7.0, rampa=0.02); m.silenciar('bombo', 6.933, 7.0, rampa=0.02)
    m.silenciar('fx', 6.967, 7.0, rampa=0.01)
    for p in ('mus', 'bombo'):
        m.fundido(p, 9.5, 10.0)
    if 'mus' in capas:
        m.fundido('fx', 9.5, 10.0)
    return m


def medir(f, t0=None, t1=None):
    af = (f'atrim={t0}:{t1},' if t0 is not None else '') + 'ebur128=peak=true:framelog=quiet'
    r = subprocess.run(['ffmpeg', '-nostats', '-i', str(f), '-af', af, '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = float([l for l in r.splitlines() if l.strip().startswith('I:')][-1].split()[1])
    Pk = float([l for l in r.splitlines() if l.strip().startswith('Peak:')][-1].split()[1])
    return I, Pk


def audio():
    out = {}
    for nombre, capas in (('completa', ('amb', 'foley', 'mus')),
                          ('sinmusica', ('amb', 'foley') + (('tono',) if VERSION != 'v01' else ()))):
        m = construir(capas)
        wav = AU / f'mezcla_{nombre}.wav'
        I, Pk = m.exportar(str(wav), lufs=-14.0)
        ajuste = 0.0
        if Pk > -1.05:                       # el limitador de exportar() muestrea a 48 kHz: el pico verdadero puede pasar
            ajuste = round(-1.15 - Pk, 2)
            tmp = wav.with_name(wav.stem + '_lim.wav')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav), '-af', f'volume={ajuste}dB', '-c:a', 'pcm_f32le',
                            str(tmp)], check=True)
            tmp.replace(wav)
            I, Pk = medir(wav)
        out[nombre] = dict(lufs=I, pico_dbtp=Pk, ajuste_final_db=ajuste)
    # capas por separado con las mismas semillas (idénticas a las de la mezcla) para medir foley contra música
    for nombre, capas in (('solo_foley', ('foley',)), ('solo_musica', ('mus',)), ('solo_amb', ('amb',))):
        m = construir(capas)
        mix = sum(m.pistas.values())
        import soundfile as sf
        sf.write(str(AU / f'{nombre}.wav'), mix.astype(np.float32), S.SR, subtype='FLOAT')
    tramos = [(0, 2), (2, 4), (4, 5.5), (5.5, 7), (7, 10)] if VERSION == 'v01' else [(0, 2), (2, 3), (3, 4), (4, 4.5), (4.5, 7), (7, 10)]
    niv = {n: {f'{a}-{b}': medir(AU / f'{n}.wav', a, b)[0] for a, b in tramos} for n in ('solo_foley', 'solo_musica', 'solo_amb')}
    niv['foley_sobre_musica_c0_c60_db'] = round(niv['solo_foley']['0-2'] - niv['solo_musica']['0-2'], 1)
    if VERSION != 'v01':
        # tono de c60–c89 en la mezcla sin música entregada (ya normalizada): roce c0–c60 contra tono c60–c89
        sm = AU / 'mezcla_sinmusica.wav'
        niv['sinmusica_roce_c0_c60_LUFS'] = medir(sm, 0, 2)[0]; niv['sinmusica_tono_c60_c89_LUFS'] = medir(sm, 2, 3)[0]
        niv['sinmusica_tono_bajo_roce_db'] = round(niv['sinmusica_roce_c0_c60_LUFS'] - niv['sinmusica_tono_c60_c89_LUFS'], 1)
        # ambiente: 8004 y 7824 contra 7859 (guion: 10–12 dB por debajo)
        niv['amb_7859_sobre_8004_db'] = round(niv['solo_amb']['7-10'] - niv['solo_amb']['4-4.5'], 1)
        niv['amb_7859_sobre_7824_db'] = round(niv['solo_amb']['7-10'] - niv['solo_amb']['4.5-7'], 1)
    out['capas_LUFS_pre_normalizacion'] = niv
    json.dump(out, open(AU / 'sonoridad.json', 'w'), indent=1)
    return out


# ------------------------------------------------------------------ máster
def master():
    ass = D / 'textos.ass'
    res = {}
    for nombre, wav, sal in (('completa', AU / 'mezcla_completa.wav', D / f'{NOMBRE}_{VERSION}.mp4'),
                             ('sinmusica', AU / 'mezcla_sinmusica.wav', D / f'{NOMBRE}_SINMUSICA_{VERSION}.mp4')):
        V.master(D / 'base.mp4', wav, sal, ass_path=ass)
        res[nombre] = str(sal)
    return res


def md5_stream(f, sel):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(f), '-map', f'0:{sel}', '-c', 'copy', '-f', 'md5', '-'],
                       capture_output=True, text=True, check=True).stdout.strip()
    return r.split('=')[-1]


def huella(f):
    return dict(archivo=str(f), bytes=Path(f).stat().st_size, md5_video=md5_stream(f, 'v'), md5_audio=md5_stream(f, 'a'),
                md5_archivo=hashlib.md5(Path(f).read_bytes()).hexdigest())


def entregar():
    hs = []
    for n in (f'{NOMBRE}_{VERSION}.mp4', f'{NOMBRE}_SINMUSICA_{VERSION}.mp4'):
        src = D / n
        h0 = huella(src)
        for dst_dir in (EXPO, PIEZA):
            dst = dst_dir / n
            if dst.exists():
                h1 = huella(dst)
                if h1['md5_archivo'] != h0['md5_archivo']:
                    raise RuntimeError(f'{dst} ya existe y es distinto: no se sobrescribe')
            else:
                shutil.copyfile(src, dst)
        time.sleep(5)
        for dst_dir in (EXPO, PIEZA):
            h1 = huella(dst_dir / n)
            if (h1['bytes'], h1['md5_video'], h1['md5_audio']) != (h0['bytes'], h0['md5_video'], h0['md5_audio']):
                raise RuntimeError(f'copia distinta en {dst_dir / n}')
        hs.append(dict(h0, copias=[str(EXPO / n), str(PIEZA / n)]))
    json.dump(hs, open(D / 'huellas.json', 'w'), indent=1)
    return hs


# ------------------------------------------------------------------ propuesta B5 (para v02, no entra en v01)
def propuesta_b5(y_props=(420, 460), cuadros_b5=(30, 63, 89)):
    """Mide el compuesto de 7859 con la ventana en y 420 (guion) y en y 460 y saca cuadros con el CTA encima."""
    xs, filas = ventana_7859()
    salida = {}
    for yd in y_props:
        _, f2 = ventana_7859(y_dest=yd) if yd != 420 else (xs, filas)
        salida[yd] = f2
        for k in cuadros_b5:
            t = k / 30
            mp4 = D / 'propuesta' / f'b5_y{yd}_c{210 + k}.mp4'; mp4.parent.mkdir(exist_ok=True)
            U.compuesto_ventana('IMG_7859', t, t + 1 / 30, mp4, [xs[k]], y_dest=yd, relleno_vf=RELLENO_7859)
            png = mp4.with_suffix('.png')
            # textos del CTA encima (mismo .ass, desplazado al tiempo 8,0 s del máster)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-itsoffset', '8.0', '-i', str(mp4), '-vf',
                            f"subtitles={D / 'textos.ass'}:fontsdir=/usr/share/fonts/opentype/inter", '-frames:v', '1',
                            str(png)], check=True)
    json.dump({str(k): v for k, v in salida.items()}, open(D / 'propuesta' / 'b5_medidas.json', 'w'), indent=0)
    return salida



def medidas_b5_ancha(y_dest=460, ancho=1888):
    """Medidas por cuadro de B5 con la ventana ancho×2160 (seguimiento real del torso en 7859): márgenes de la remera,
    pelo y borde inferior de «Founders Privée» en px del máster. Devuelve (xs de la ventana 1728, d, medidas)."""
    xs, filas = ventana_7859(y_dest=y_dest)
    d = (ancho - 1728) / 2; esc0 = 1080 / 1728; esc = 1080 / ancho
    med = []
    for f in filas:
        izq = (f['margen_remera_izq_master'] / esc0 + d) * esc; der = (f['margen_remera_der_master'] / esc0 + d) * esc
        pelo = None if f['pelo_y_master'] is None else y_dest + (f['pelo_y_master'] - y_dest) / esc0 * esc
        fo = None if f['founders_y1_master'] is None else y_dest + (f['founders_y1_master'] - y_dest) / esc0 * esc
        med.append(dict(t=f['t'], margen_remera_izq_master=round(izq, 1), margen_remera_der_master=round(der, 1),
                        pelo_y_master=None if pelo is None else round(pelo, 1), founders_y1_master=None if fo is None else round(fo, 1)))
    return xs, d, med


def propuesta_b5_ancha(y_dest=460, ancho=1888, cuadros_b5=(30, 63, 89)):
    """Variante para v02: ventana más ancha que 4:5 (ancho×2160) centrada en la misma remera, pegada en y_dest.
    Con 1728 px las mangas (1620 px a 3,0 s) dejan como máximo 34 px por lado en el máster: el margen de 40 px no entra."""
    xs, d, med = medidas_b5_ancha(y_dest, ancho); h = round(1080 * 2160 / ancho)
    for k in cuadros_b5:
        t = k / 30
        mp4 = D / 'propuesta' / f'b5_y{y_dest}_w{ancho}_c{210 + k}.mp4'; mp4.parent.mkdir(exist_ok=True)
        U.compuesto_ventana('IMG_7859', t, t + 1 / 30, mp4, [xs[k] - d], ventana=(ancho, 2160), y_dest=y_dest,
                            relleno_vf=RELLENO_7859)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-itsoffset', '8.0', '-i', str(mp4), '-vf',
                        f"subtitles={D / 'textos.ass'}:fontsdir=/usr/share/fonts/opentype/inter", '-frames:v', '1',
                        str(mp4.with_suffix('.png'))], check=True)
    r = dict(y_dest=y_dest, ancho=ancho, alto_master=h, borde_inferior_ventana=y_dest + h, filas=med)
    json.dump(r, open(D / 'propuesta' / f'b5_medidas_y{y_dest}_w{ancho}.json', 'w'), indent=0)
    return dict(min_izq=min(m['margen_remera_izq_master'] for m in med), min_der=min(m['margen_remera_der_master'] for m in med),
                max_founders=max(m['founders_y1_master'] for m in med if m['founders_y1_master'] is not None))

if __name__ == '__main__':
    pasos = sys.argv[1:] or ['todo']
    if 'todo' in pasos:
        pasos = ['planos', 'textos', 'audio', 'master']
    for p in pasos:
        t = time.time()
        r = globals()[p]()
        print(p, f'{time.time() - t:.1f} s', r if not isinstance(r, (list, dict)) or len(str(r)) < 2000 else '')
