#!/usr/bin/env python3
"""BOC-SUD P1 «Tres veces» · valor: el Casi (seguir pateando) · receta v01 (24/11/2026).

Hechos (01_pepe_verificacion.md): travesaño de Merentiel (3'), gol de Ascacíbar anulado por offside (11'),
«minutos después» gol de Ascacíbar (15'), Merentiel el 2-0 (47'). Sin minutos en pantalla.
Las olas sobre la roca de las remeras hacen de remates (tomas propias); el partido aparece en la foto de la final
(Commons, licencia dudosa: avisado) La foto de Merentiel (tomada de Facebook) no se usa: retrato de un jugador en un aviso de marca.

Etapas: python3 p1.py planos | trans | audio | master | todo
"""
import sys, json
from pathlib import Path
sys.path.insert(0, '/home/user/1/scripts/bocsud')
import comun as C
V = C.V

T = C.T / 'p1'
FPS = 30
ESTADIO = C.ARCH / 'final2026_1920.jpg'      # Commons «Estadio Metropolitano de Barranquilla.jpg», 1920 px
OBELISCO_A = C.ARCH / 'Buenos_Aires_-_Boca_Juniors_-_D_a_del_hincha_-_131212a.webm'
SALIDA = C.T / 'borradores' / 'p1_borrador.mp4'


def planos():
    P = []
    P.append(C.foto_movil(ESTADIO, 1.0, T / 's01_estadio_arco.mp4', 'cubrir', z0=1.0, z1=1.45,
                          c0=(0.42, 0.6), c1=(0.385, 0.66)))                                   # c0–c29 ¿Entra?
    P.append(C.propia('IMG_4631', 3.45, 4.35, T / 's02_4631.mp4', z0=1.0, z1=1.06))            # c30–c56 travesaño (golpe c40 = 3,78 s)
    P.append(C.propia('IMG_7895', 0.0, 0.8, T / 's03_7895.mp4', cx=0.45, cy=0.45, z0=1.05, z1=1.12))  # c57–c80 ¿Y ahora? / GOL
    P.append(C.congelar(T / 's03_7895.mp4', 23, 15, T / 's04_anulado.mp4',
                        por_cuadro=lambda k, f: C.destenir(f, 1.0, min(1.0, 0.25 + k * 0.08))))   # c81–c95 ANULADO
    P.append(C.propia('IMG_3453', 0.2, 1.4, T / 's05_3453.mp4', z0=1.0, z1=1.08))              # c96–c131 ¿casi?
    P.append(C.propia('IMG_4627', 10.0, 11.9, T / 's06_4627.mp4', z0=1.0, z1=1.10))            # c132–c188 tercera / GOL (ola c165 = 11,1 s)
    P.append(C.foto_movil(ESTADIO, 1.3, T / 's07_estadio_grupo.mp4', 'cubrir', z0=1.15, z1=1.35,
                          c0=(0.66, 0.64), c1=(0.68, 0.63)))                                   # c189–c227 el del anulado
    # vuelve al arco del primer cuadro (el del travesaño); golpe y destello en el «2-0.» (k = 20)
    P.append(C.foto_movil(ESTADIO, 1.3, T / 's08_estadio_arco2.mp4', 'cubrir', z0=1.5, z1=1.9,
                          c0=(0.385, 0.66), c1=(0.38, 0.665), sacudida=[(20, 12)],
                          por_cuadro=lambda k, f: C.flash(f, max(0.0, 0.5 - 0.17 * (k - 20))) if k >= 20 else f))   # c228–c266
    P.append(C.placa(1.2, T / 's09_placa.mp4'))                                                  # c267–c302 primeros 100
    P.append(C.propia('IMG_4627', 4.0, 6.4, T / 's10_4627.mp4', z0=1.0, z1=1.05))              # c303–c374 CTA
    n = C.armar(P, T / 'p1_video.mp4')
    json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('cuadros', n)


def t(c):
    return c / FPS


def textos():
    X = []
    def caja(a, b, txt, y=245, maximo='CajaN_hook', **kw):
        est = C.caja(txt, maximo)
        X.append(dict(t0=t(a), t1=t(b), txt=txt, estilo=est, y=C.Y_HOOK if est == 'CajaN_hook' else y, pop=True, **kw))
    caja(0, 30, '¿Entra?')
    X.append(dict(t0=t(0), t1=t(30), txt='Final de la Sudamericana', estilo='CajaN_ctx', y=455))
    caja(40, 57, 'Travesaño.')
    caja(57, 66, '¿Y ahora?')
    X.append(dict(t0=t(66), t1=t(81), txt='GOL.', estilo='Golpe', y=560, pop=True))
    X.append(dict(t0=t(81), t1=t(96), txt='ANULADO.', estilo='Sello', y=560, pop=True, extra='\\frz8'))
    caja(96, 132, '¿Se queda en casi?')
    caja(132, 165, 'Minutos después.')
    X.append(dict(t0=t(165), t1=t(189), txt='GOL.', estilo='Golpe', y=430, pop=True))
    caja(189, 228, 'Lo hizo el del anulado.')
    caja(228, 267, 'Y el del travesaño:')
    X.append(dict(t0=t(248), t1=t(267), txt='2-0.', estilo='Golpe', y=1180, pop=True))
    caja(267, 303, 'Uno de los primeros 100.')
    caja(303, 375, 'Pateá la tercera.')
    X.append(dict(t0=t(312), t1=t(375), txt='link en bio', estilo='CajaN_link', y=445))
    return X


TRANS = {30: 'barrido', 57: 'zoom', 132: 'barrido', 189: 'zoom+destello', 228: 'zoom', 303: 'barrido_izq'}


def trans():
    C.transiciones(T / 'p1_video.mp4', T / 'p1_video_t.mp4', TRANS, 375)
    print('transiciones', TRANS)


def audio(con_musica=True):
    DUR = 375 / FPS
    m = C.MezclaB(DUR)
    # ambiente real: mar de cada toma propia; hinchada real (Obelisco 2013) donde hay estadio y en los goles
    hay_hinchada = OBELISCO_A.exists()
    if hay_hinchada:
        m.real(OBELISCO_A, 2.0, t(0), t(57), -14, hp=120, ini=0.05, fin=0.08, etiqueta='Obelisco 2013 (murmullo)')
    m.toma('IMG_4631', 3.45, t(30), t(57), -6, ini=0.01, fin=0.05)
    m.toma('IMG_7895', 0.0, t(57), t(81), -4, fin=0.02)
    m.toma('IMG_3453', 0.2, t(96), t(132), -18, ini=0.1, fin=0.05)
    m.toma('IMG_4627', 10.0, t(132), t(189), -5, ini=0.05, fin=0.05)
    m.toma('IMG_4627', 4.0, t(303), t(375), -8, ini=0.05, fin=0.3)
    if hay_hinchada:
        m.real(OBELISCO_A, 20.0, t(66), t(81), -6, ini=0.01, fin=0.01, etiqueta='Obelisco 2013 (grito)')
        m.real(OBELISCO_A, 30.0, t(165), t(267), -4, ini=0.01, fin=0.4, etiqueta='Obelisco 2013 (festejo)')
    # efectos
    m.latido(t(2), 0.5); m.latido(t(22), 0.55)
    m.subida(t(8), t(40), 0.12)
    m.clang(t(40), 0.55)
    m.latido(t(58), 0.5)
    m.impacto(t(66), 0.55)
    m.silbato(t(80), 0.5, 0.28)
    m.impacto(t(81), 0.35)
    m.latido(t(100), 0.45); m.latido(t(120), 0.45)
    m.redoble(t(142), t(165), 0.10); m.subida(t(142), t(165), 0.16)
    m.impacto(t(165), 0.7)
    for c, tp in TRANS.items():
        if 'barrido' in tp or 'zoom' in tp: m.barrido(t(c), 0.3, 0.15)
    m.impacto(t(248), 0.45)
    m.clang(t(267), 0.22)
    if con_musica:
        b = 60 / 140
        # tramo 1 (c0–c95): bajo sostenido que sube de tensión; corta en el ANULADO
        m.pad(t(0), [45, 52, 57], t(80), 0.05, corte=900)
        m.ocho08(t(66), 33, 0.45, 0.5, glide_desde=40)
        # tramo 2 (c96–c162): casi silencio con pad grave
        m.pad(t(96), [45, 48, 52], t(69), 0.04, corte=700)
        # tramo 3 (c163–fin): ritmo a 140 (medio tiempo)
        k = 0; t0 = t(165)
        while t0 + k * b < t(375) - 0.05:
            tt = t0 + k * b
            if k % 4 == 0:
                m.bombo(tt, 0.85); m.ocho08(tt, [33, 33, 36, 31][(k // 4) % 4], b * 3.6, 0.5)
            if k % 4 == 2:
                m.palma(tt, 0.28); m.bombo(tt + b * 0.5, 0.5)
            m.charles(tt, 0.08); m.charles(tt + b / 2, 0.05)
            k += 1
        m.pad(t(165), [45, 52, 57, 60], t(210), 0.05, corte=1600)
        m.fundido('mus', t(375) - 0.35, t(375))
        m.fundido('bombo', t(375) - 0.35, t(375))
    m.silenciar('amb', t(81), t(96), rampa=0.01)
    nombre = 'p1_completa.wav' if con_musica else 'p1_sinmusica.wav'
    (T / 'audio').mkdir(exist_ok=True)
    r = m.exportar(str(T / 'audio' / nombre), lufs=-14)
    print(nombre, r, 'hinchada real' if hay_hinchada else 'SIN hinchada real')


def master():
    a = V.ass(textos(), T / 'p1.ass')
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    V.master(T / 'p1_video_t.mp4', T / 'audio' / 'p1_completa.wav', SALIDA, ass_path=a)
    print(SALIDA)


if __name__ == '__main__':
    T.mkdir(parents=True, exist_ok=True)
    et = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    if et in ('planos', 'todo'): planos()
    if et in ('trans', 'todo'): trans()
    if et in ('audio', 'todo'): audio(True)
    if et in ('master', 'todo'): master()
