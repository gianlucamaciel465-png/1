#!/usr/bin/env python3
"""BOC-SUD P3 «Los que estaban» · valor: pertenencia (estar desde el principio) · receta v03 (24/11/2026; v03 = video real).

v03: vuelve el diseño original del filtro de ideas (03): «¿Cuántos son?» → «Miles.» → «Primera internacional desde
2008.» → «Campeón.» → «Antes de los miles, estuvo uno.». Salen las fotos del Día del Hincha 2013 (y con ellas la
foto de la final de licencia dudosa, las fotos CC BY-SA, la cara desenfocada del nene y el festejo que terminó con
incidentes). Entran clips oficiales (TikTok @sudamericana, © CONMEBOL: material de terceros, ver 06_licencias.md):
  171912 (la tribuna de Boca en Barranquilla), 965384 (el Obelisco la noche del título), 352840 (la copa desde
  arriba y el estadio rodeado de fuegos artificiales; su sonido trae música y no se usa).
Tomas propias: 7887 (Gianluca, de espaldas con la Negra, fotografía la Blanca) y 7857 (la Blanca puesta, de espaldas); placa real.
Hechos (Pepe): 21/11/2026 campeón de la Sudamericana; primer título internacional desde la Recopa 2008.
La receta v02 (fotos animadas) está en el commit 380c65c.

Etapas: python3 p3.py planos | trans | audio | master | todo
"""
import sys, json
from pathlib import Path
sys.path.insert(0, '/home/user/1/scripts/bocsud')
import comun as C
V = C.V

T = C.T / 'p3'
FPS = 30
SALIDA = C.T / 'borradores' / 'p3_borrador.mp4'

S1 = (0, 36)        # ¿Cuántos son?  (la tribuna)
S2 = (36, 69)       # Miles.  (el Obelisco)
S3 = (69, 108)      # Primera internacional / desde 2008.  (la copa desde arriba)
S4 = (108, 138)     # Campeón.  (el estadio rodeado de fuegos)
S5 = (138, 204)     # 7887: Antes de los miles, (c138–c168) / estuvo uno. (c168–c204)
S6 = (204, 240)     # placa: Del 001 al 100.
S7 = (240, 312)     # 7857: Bancá desde el principio. / link en bio
NF = 312
UNO = S5[0] + 30
CAMPEON_Y = 420       # en el cielo oscuro, arriba de los fuegos


def d(s):
    return (s[1] - s[0]) / FPS


def planos():
    P = []
    # S1: la tribuna de Boca al atardecer (24 fps, un cuadro por cuadro); tramo 10,3–11,8 s y recorte que se corre a la derecha:
    # sin los carteles de cerveza del principio ni la pantalla gigante con un jugador que entra por la izquierda al final
    P.append(C.real('171912', 10.3, S1[1] - S1[0], T / 's1_tribuna.mp4', c0=(0.5, 0.5), c1=(0.58, 0.5), z0=1.08, z1=1.15, uno_a_uno=True))
    # S2: el Obelisco esa noche: un hincha arriba del semáforo con los brazos en alto, la multitud abajo
    P.append(C.real('965384', 0.0, S2[1] - S2[0], T / 's2_obelisco.mp4', c0=(0.5, 0.55), z0=1.0, z1=1.12))
    # S3: la copa desde arriba: el arco «CAMPEÓN 2026», el papel picado y el fuego artificial que sube (hasta el corte de la fuente en 17,77 s)
    P.append(C.real('352840', 16.45, S3[1] - S3[0], T / 's3_copa.mp4', c0=(0.5, 0.42), z0=1.0, z1=1.12))
    # S4: el estadio rodeado de fuegos artificiales
    P.append(C.real('352840', 17.83, S4[1] - S4[0], T / 's4_fuegos.mp4', c0=(0.5, 0.42), z0=1.0, z1=1.1))   # sin acercar más: la marca de agua del clip queda entera, no cortada por el borde
    P.append(C.propia('IMG_7887', 0.0, d(S5), T / 's5_7887.mp4', cx=0.55, cy=0.5, z0=1.0, z1=1.10))
    # cierre distinto al de P1 y P2: la Blanca puesta, de espaldas, frente a las olas
    cta = C.propia('IMG_7857', 2.7, 2.7 + d(S7), T / 's7_7857.mp4', z0=1.0, z1=1.04)
    P.append(C.placa(d(S6), T / 's6_placa.mp4', fondo=T / 's7_7857.mp4'))
    P.append(cta)
    n = C.armar(P, T / 'p3_video.mp4')
    assert n == NF, n
    json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('cuadros', n)


def t(c):
    return c / FPS


def tx(c):
    """tiempo de un cuadro para los textos: 4 ms antes, así el redondeo a centésimas del .ass no lo corre un cuadro"""
    return max(c / FPS - 0.004, 0.0)


def textos():
    X = []
    def caja(a, b, txt, y=245, maximo='CajaN_hook', **kw):
        est = C.caja(txt, maximo)
        X.append(dict(t0=tx(a), t1=tx(b), txt=txt, estilo=est, y=C.Y_HOOK if est == 'CajaN_hook' else y, pop=True, **kw))
    caja(S1[0], S1[1], '¿Cuántos son?')
    caja(S2[0], S2[1], 'Miles.')
    X.append(dict(t0=tx(S2[0] + 4), t1=tx(S2[1]), txt='Obelisco · esa noche', estilo='CajaN_125', y=452, pop=True))
    caja(S3[0], S3[1], 'Primera internacional\\Ndesde 2008.')
    X.append(dict(t0=tx(S4[0]), t1=tx(S4[1]), txt='Campeón.', estilo='Golpe', y=CAMPEON_Y, pop=True))
    caja(S5[0], UNO, 'Antes de los miles,')
    caja(UNO, S5[1], 'estuvo uno.')
    caja(S6[0], S6[1], 'Del 001 al 100.')
    # en 7857 la cabeza ocupa el tercio superior: el texto va abajo, sobre el pantalón (sin tapar cabeza ni estampado)
    X.append(dict(t0=tx(S7[0]), t1=tx(NF), txt='Bancá desde\\Nel principio.', estilo='CajaN_108', y=1160, pop=True))
    X.append(dict(t0=tx(S7[0] + 10), t1=tx(NF), txt='link en bio', estilo='CajaN_link', y=1436))
    return X


# S5 entra por corte seco: de los fuegos al mar casi en silencio (el contraste es el giro); S7: la placa sale y el fondo queda en foco
TRANS = {S2[0]: 'barrido', S3[0]: 'barrido_izq', S4[0]: 'zoom+destello', S7[0]: 'zoom'}


def trans():
    C.transiciones(T / 'p3_video.mp4', T / 'p3_video_t.mp4', TRANS, NF)
    print('transiciones', TRANS)


def audio(con_musica=True):
    DUR = NF / FPS
    m = C.MezclaB(DUR)
    # hinchada real de la final (clips filmados desde la tribuna, «sonido original»; sin escuchar: medido por niveles y espectro).
    # No es el sonido de cada plano: es la tribuna en el festejo del 1-0 (701384) y en el gol visto desde la tribuna (774354).
    FEST, TRIB1 = C.clip('701384'), C.clip('774354')
    m.real(FEST, 4.0, t(S1[0]), t(S3[0]) + 0.1, -8, hp=120, ini=0.05, fin=0.15, etiqueta='hinchada real (festejo)')
    m.real(TRIB1, 1.7, t(S3[0]), t(S5[0]), -2, ini=0.1, fin=0.04, etiqueta='hinchada real: sube y estalla (pico en 3,0 s = c108)')
    m.toma('IMG_7887', 0.0, t(S5[0]), t(S5[1]), 7, ini=0.005, fin=0.05)   # el mar de 7887 mide −25 a −30 dBFS: +7 para que se oiga
    m.toma('IMG_7857', 2.7, t(S7[0]), t(NF), -8, ini=0.05, fin=0.3)
    for c, tp in TRANS.items():
        if 'barrido' in tp: m.barrido(t(c), 0.3, 0.15)
    m.latido(t(2), 0.5); m.latido(t(18), 0.5)
    m.subida(t(S3[0]), t(S4[0]), 0.16)
    m.impacto(t(S4[0]), 0.75)
    m.clang(t(S6[0]), 0.22)
    if con_musica:
        b = 60 / 132
        k = 0
        while k * b < t(S5[0]) - 0.05:       # tramo 1: pulso a 132 (bombo a tierra, palma en el contratiempo, bajo): ritmo, no un bombo de cancha
            tt = k * b
            if k % 2 == 0: m.bombo(tt, 0.8)
            if k % 4 == 2: m.palma(tt, 0.24)
            m.charles(tt + b / 2, 0.06)
            if k % 8 == 0: m.ocho08(tt, [33, 36][(k // 8) % 2], b * 7, 0.42)
            k += 1
        m.pad(t(S5[0]) + 0.3, [45, 52, 57], t(S6[0] - S5[0]) - 0.3, 0.05, corte=1100, a=0.4)   # con el mar: pad suave
        k = 0; t0 = t(S6[0])
        while t0 + k * b < t(NF) - 0.05:      # tramo 3: vuelve el ritmo con la placa y el CTA
            tt = t0 + k * b
            if k % 4 == 0: m.bombo(tt, 0.8); m.ocho08(tt, [33, 36][(k // 4) % 2], b * 3.6, 0.45)
            if k % 4 == 2: m.palma(tt, 0.24)
            m.charles(tt, 0.07); m.charles(tt + b / 2, 0.045)
            k += 1
        m.silenciar('mus', t(S5[0]), t(S5[0]) + 0.3, rampa=0.02); m.silenciar('bombo', t(S5[0]), t(S6[0]), rampa=0.02)
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
