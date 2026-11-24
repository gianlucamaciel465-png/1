#!/usr/bin/env python3
"""BOC-SUD P3 «Los que estaban» · valor: pertenencia (bancar sin copa) · receta v02 (24/11/2026; v02 = correcciones de Roma).

Material: fotos de Barcex en Commons (Día del Hincha de Boca, Obelisco, 12/12/2013, CC BY-SA 3.0); foto de la final
2026 (Commons, licencia dudosa: avisada); tomas propias 7887 (Gianluca, confirmado) y 7857 (la Blanca puesta, de espaldas); placa real.
El video de esa noche (131212a/b/c.webm, mismo autor y licencia) no se pudo bajar: el host de archivos de Wikimedia
respondió 429 «Too many requests» a esta red durante más de una hora. Si llega el archivo, reemplaza a S1–S4.
Hechos: el 12/12 es el Día del Hincha de Boca; en 2013 no se festejaba ningún título; la última internacional había
sido la Recopa 2008 (Pepe); 21/11/2026 campeón de la Sudamericana.

Etapas: python3 p3.py planos | trans | audio | master | todo
"""
import sys, json
from pathlib import Path
sys.path.insert(0, '/home/user/1/scripts/bocsud')
import comun as C
V = C.V

T = C.T / 'p3'
FPS = 30
A = C.ARCH
BANDERAS = A / 'ob_234636_3600.jpg'      # «…Día del hincha - 131212 234636.jpg» (miniatura estándar de 3840 px)
OBELISCO = A / 'ob_234353_1920.jpg'      # «…131212 234353.jpg»
MULTITUD = A / 'ob_235007_3840.jpg'      # «…131212 235007.jpg»
ESPALDAS = A / 'ob_234519_3840.jpg'      # «…131212 234519.jpg»
ESTADIO = A / 'final2026_3840.jpg'
SALIDA = C.T / 'borradores' / 'p3_borrador.mp4'

S1 = (0, 36)        # ¿Qué festejan?
S2 = (36, 72)       # Ningún título. · Obelisco · 12/12/2013
S3 = (72, 108)      # Festejan ser de Boca.
S4 = (108, 144)     # Sin una internacional desde 2008.
S5 = (144, 183)     # 21/11/2026. → Campeón. (c160)
S6 = (183, 249)     # 7887: Antes de los miles, (c183–c213) / estuvo uno. (c213–c249)
S7 = (249, 285)     # placa: Del 001 al 100.
S8 = (285, 357)     # 7857: Bancá desde el principio. / link en bio
NF = 357
CAMPEON = 160


def d(s):
    return (s[1] - s[0]) / FPS


def planos():
    P = []
    # S1: banderas con el escudo y un brazo que filma con el teléfono; gente de espaldas (sin caras de frente ni
    # los arcos del local de comidas que está arriba en la foto): empuje y leve paneo
    # al lado del brazo quedaba la cara de un nene de perfil: se desenfoca solo esa zona (copia de trabajo, la foto original no se toca)
    ban = C.foto_desenfocada(BANDERAS, [(2815, 1958, 26, 40, 8, 7)], T / 's1_banderas_src.jpg')
    P.append(C.foto_movil(ban, d(S1), T / 's1_banderas.mp4', 'cubrir', z0=3.0, z1=3.2, c0=(0.70, 0.745), c1=(0.70, 0.74)))
    # S2: el Obelisco: baja de la aguja a la gente
    # (recorrido completo dentro de la foto: con z=1,2 el centro puede ir de 0,4167 a 0,5833; antes el paneo se frenaba al llegar al borde)
    P.append(C.foto_movil(OBELISCO, d(S2), T / 's2_obelisco.mp4', 'cubrir', z0=1.2, z1=1.2, c0=(0.47, 0.4167), c1=(0.47, 0.5833)))
    # S3: multitud con la bandera grande
    # (la bandera, los edificios y la multitud lejana: el recorte termina arriba de las caras cercanas (y < 1010 px de la foto)
    #  y empieza debajo del cartel publicitario de la cornisa (y > 235 px); sin el local de comidas)
    P.append(C.foto_movil(MULTITUD, d(S3), T / 's3_multitud.mp4', 'cubrir', z0=2.787, z1=2.95, c0=(0.6089, 0.2882), c1=(0.6146, 0.298)))
    # S4: espaldas, esperando
    # (recorte sin la gorra con logo de la derecha ni la cara del chico de la izquierda)
    P.append(C.foto_movil(ESPALDAS, d(S4), T / 's4_espaldas.mp4', 'cubrir', z0=2.7, z1=2.9, c0=(0.455, 0.83), c1=(0.45, 0.84)))
    k0 = CAMPEON - S5[0]
    # un teléfono filma la cancha (eco del brazo que filma las banderas en el primer plano)
    P.append(C.foto_movil(ESTADIO, d(S5), T / 's5_2026.mp4', 'cubrir', z0=1.6, z1=1.75,
                          c0=(0.69, 0.70), c1=(0.69, 0.70), sacudida=[(k0, 10)],
                          por_cuadro=lambda k, f: C.flash(f, max(0.0, 0.55 - 0.18 * (k - k0))) if k >= k0 else f))
    P.append(C.propia('IMG_7887', 0.0, d(S6), T / 's6_7887.mp4', cx=0.55, cy=0.5, z0=1.0, z1=1.10))
    # cierre distinto al de P1 y P2: la Blanca puesta, de espaldas, frente a las olas
    cta = C.propia('IMG_7857', 2.7, 2.7 + d(S8), T / 's8_7857.mp4', z0=1.0, z1=1.04)
    P.append(C.placa(d(S7), T / 's7_placa.mp4', fondo=T / 's8_7857.mp4'))
    P.append(cta)
    n = C.armar(P, T / 'p3_video.mp4')
    assert n == NF, n
    json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('cuadros', n)


def t(c):
    return c / FPS


def textos():
    X = []
    def caja(a, b, txt, y=245, maximo='CajaN_hook', **kw):
        est = C.caja(txt, maximo)
        X.append(dict(t0=t(a), t1=t(b), txt=txt, estilo=est, y=C.Y_HOOK if est == 'CajaN_hook' else y, pop=True, **kw))
    caja(S1[0], S1[1], '¿Qué festejan?')
    caja(S2[0], S2[1], 'Ningún título.')
    X.append(dict(t0=t(S2[0] + 4), t1=t(S2[1]), txt='Obelisco · 12/12/2013', estilo='CajaN_125', y=452, pop=True))   # el año tiene que leerse: da vuelta el gancho
    caja(S3[0], S3[1], 'Festejan ser de Boca.')
    caja(S4[0], S4[1], 'Sin una internacional\\Ndesde 2008.')
    caja(S5[0], CAMPEON, '21/11/2026.')
    X.append(dict(t0=t(CAMPEON), t1=t(S5[1]), txt='Campeón.', estilo='Golpe', y=545, pop=True))
    caja(S6[0], S6[0] + 30, 'Antes de los miles,')
    caja(S6[0] + 30, S6[1], 'estuvo uno.')
    caja(S7[0], S7[1], 'Del 001 al 100.')
    # en 7857 la cabeza ocupa el tercio superior: el texto va abajo, sobre el pantalón (sin tapar cabeza ni estampado)
    X.append(dict(t0=t(S8[0]), t1=t(NF), txt='Bancá desde\\Nel principio.', estilo='CajaN_108', y=1160, pop=True))
    X.append(dict(t0=t(S8[0] + 10), t1=t(NF), txt='link en bio', estilo='CajaN_link', y=1436))
    return X


TRANS = {S2[0]: 'barrido', S3[0]: 'barrido_izq', S4[0]: 'barrido', S5[0]: 'zoom', S8[0]: 'zoom'}   # S8: la placa sale y el fondo queda en foco


def trans():
    C.transiciones(T / 'p3_video.mp4', T / 'p3_video_t.mp4', TRANS, NF)
    print('transiciones', TRANS)


def audio(con_musica=True):
    DUR = NF / FPS
    m = C.MezclaB(DUR)
    m.toma('IMG_7887', 0.0, t(S6[0]), t(S6[1]), 7, ini=0.005, fin=0.05)   # el mar de 7887 mide −25 a −30 dBFS: +7 para que se oiga
    m.toma('IMG_7857', 2.7, t(S8[0]), t(NF), -8, ini=0.05, fin=0.3)
    for c, tp in TRANS.items():
        if 'barrido' in tp: m.barrido(t(c), 0.3, 0.15)
    m.latido(t(S5[0] + 2), 0.55)
    m.subida(t(S5[0]), t(CAMPEON), 0.16)
    m.impacto(t(CAMPEON), 0.75)
    m.clang(t(S7[0]), 0.22)
    if con_musica:
        b = 60 / 132
        k = 0
        while k * b < t(S5[0]) - 0.05:       # tramo 1: bombo de cancha a 132 (bombo, redoblante de palmas, platillo)
            tt = k * b
            if k % 4 in (0, 2): m.bombo(tt, 0.8, f0=100, f1=50, dec=0.3)
            if k % 4 == 3: m.bombo(tt, 0.55, f0=100, f1=50, dec=0.25); m.bombo(tt + b / 2, 0.6, f0=100, f1=50, dec=0.25)
            if k % 2 == 1: m.palma(tt, 0.22)
            m.charles(tt + b / 2, 0.06, abierto=(k % 4 == 3))
            if k % 8 == 0: m.ocho08(tt, [33, 36][(k // 8) % 2], b * 7, 0.4)
            k += 1
        m.pad(t(S6[0]) + 0.3, [45, 52, 57], t(S7[0] - S6[0]) - 0.3, 0.05, corte=1100, a=0.4)   # con el mar: pad suave
        k = 0; t0 = t(S7[0])
        while t0 + k * b < t(NF) - 0.05:      # tramo 3: vuelve el ritmo con la placa y el CTA
            tt = t0 + k * b
            if k % 4 == 0: m.bombo(tt, 0.8); m.ocho08(tt, [33, 36][(k // 4) % 2], b * 3.6, 0.45)
            if k % 4 == 2: m.palma(tt, 0.24)
            m.charles(tt, 0.07); m.charles(tt + b / 2, 0.045)
            k += 1
        m.silenciar('mus', t(S5[0]), t(CAMPEON), rampa=0.02); m.silenciar('bombo', t(S5[0]) + 0.3, t(CAMPEON), rampa=0.02)
        m.fundido('mus', t(NF) - 0.35, t(NF)); m.fundido('bombo', t(NF) - 0.35, t(NF))
    (T / 'audio').mkdir(exist_ok=True)
    nombre = 'p3_completa.wav' if con_musica else 'p3_sinmusica.wav'
    r = m.exportar(str(T / 'audio' / nombre), lufs=-14)
    print(nombre, r)


def master():
    a = V.ass(textos(), T / 'p3.ass')
    V.master(T / 'p3_video_t.mp4', T / 'audio' / 'p3_completa.wav', SALIDA, ass_path=a)
    print(SALIDA)


if __name__ == '__main__':
    T.mkdir(parents=True, exist_ok=True)
    et = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    if et in ('planos', 'todo'): planos()
    if et in ('trans', 'todo'): trans()
    if et in ('audio', 'todo'): audio(True)
    if et in ('master', 'todo'): master()
