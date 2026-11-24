#!/usr/bin/env python3
"""BOC-SUD P1 «Tres veces» · valor: el Casi (seguir pateando) · receta v03 (24/11/2026; v03 = video real del partido).

Hechos (01_pepe_verificacion.md): travesaño de Merentiel (3'), gol de Ascacíbar anulado por offside (11'),
«minutos después» gol de Ascacíbar (15'), Merentiel el 2-0 (47'). Sin minutos en pantalla.
v03: el partido entra con clips oficiales (TikTok @sudamericana, © CONMEBOL: material de terceros, ver 06_licencias.md):
  447124 «¡Uff, casi!» (cámara táctica: la pelota llega al travesaño en 3,90 s), 035221 «Ups» (la tribuna grita el gol
  anulado; recorte sobre la tribuna general, sin el rótulo ni las caras cercanas), 134017 (gol de Ascacíbar: red en
  9,67 s), 701384 (festejo del 1-0 frente a la tribuna), 589650 (gol de Merentiel: red en 12,0 s).
El producto entra por el corte del travesaño (la ola de 4631 revienta en el golpe), 3453, la placa y el cierre (4641).
La receta v02 (fotos animadas) está en el commit 380c65c.

Etapas: python3 p1.py planos | trans | audio | master | todo
"""
import sys, json
from pathlib import Path
sys.path.insert(0, '/home/user/1/scripts/bocsud')
import comun as C
V = C.V

T = C.T / 'p1'
FPS = 30
SALIDA = C.T / 'borradores' / 'p1_borrador.mp4'
NF = 375
GOL1_Y, GOL2_Y, DOS_Y = 560, 1300, 610      # altura de «GOL.» (tribuna), «GOL.» (debajo del arco) y «2-0.» (sobre el arco)


def planos():
    P = []
    # c0–c29 ¿Entra?: la jugada real. Remate en 3,47–3,53 s; la pelota llega al travesaño en 3,90 s → corte.
    P.append(C.real('447124', 2.90, 30, T / 's01_travesano.mp4', c0=(0.33, 0.35), c1=(0.29, 0.335), z0=1.45, z1=1.75))
    # c30–c56 la ola de 4631 revienta en el corte (golpe en 3,78 s de la toma = c31)
    P.append(C.propia('IMG_4631', 3.75, 4.65, T / 's02_4631.mp4', z0=1.0, z1=1.06))
    # c57–c80 la tribuna real: de la tensión al grito en un plano continuo (24 fps, un cuadro por cuadro).
    # Ventana anclada arriba a la izquierda de la fuente (x 0, y 250): 417 px de ancho en «¿Y ahora?» y se cierra a 385 en el
    # grito. Afuera quedan el rótulo del clip (y 1215–1280), los perfiles cercanos del borde derecho (Roma, máster v03) y la
    # cara que aparecía abajo en los últimos cuadros y en el congelado. No se puede correr más a la izquierda: x 0 es el borde.
    def v_grito(k):
        return C.anclada(0, 250.5, 2.16 * (1.2 if k < 9 else 1.2 + 0.1 * (k - 9) / 14))
    P.append(C.real('035221', 1.625, 24, T / 's03_grito.mp4', ventana=v_grito, uno_a_uno=True,
                    por_cuadro=lambda k, f: C.sombra(f, 540, GOL1_Y, k=0.4) if k >= 9 else f))   # ¿Y ahora? / GOL (c66)
    P.append(C.congelar(T / 's03_grito.mp4', 23, 15, T / 's04_anulado.mp4',
                        por_cuadro=lambda k, f: C.destenir(C.sombra(f, 540, GOL1_Y, k=0.35), 1.0, 0.12)))   # c81–c95 ANULADO: gris
    # 3453 2,3–3,5 s: «so f★cking close.» entra completa en todos los cuadros y los dedos llegan al final
    P.append(C.propia('IMG_3453', 2.3, 3.5, T / 's05_3453.mp4', z0=1.0, z1=1.03))              # c96–c131 ¿casi?
    # c132–c188 el gol real: remate en 8,9 s, pelota en la red en 9,67 s (k = 33 → c165)
    P.append(C.real('134017', 8.57, 57, T / 's06_gol1.mp4', c0=(0.5, 0.45), c1=(0.62, 0.42), z0=1.0, z1=1.12,
                    por_cuadro=lambda k, f: C.sombra(f, 540, GOL2_Y, k=0.4) if k >= 33 else f))
    # c189–c227 el festejo frente a la tribuna (24 fps, un cuadro por cuadro; jugadores chicos y de espaldas)
    P.append(C.real('701384', 2.1, 39, T / 's07_festejo.mp4', c0=(0.5, 0.62), z0=1.15, z1=1.25, uno_a_uno=True))
    # c228–c266 el 2-0 real: la pelota cruza la línea en 12,0 s (k = 20 → c248); golpe y destello
    P.append(C.real('589650', 11.33, 39, T / 's08_gol2.mp4', c0=(0.3, 0.44), z0=1.2, z1=1.32,
                    por_cuadro=lambda k, f: C.flash(C.sombra(f, 540, DOS_Y, k=0.4), max(0.0, 0.45 - 0.15 * (k - 20))) if k >= 20 else f))
    # cierre: 4641 (la Blanca de frente en la roca; la ola rompe detrás en 1,5–2,5 s)
    cta = C.propia('IMG_4641', 0.6, 3.0, T / 's10_4641.mp4', z0=1.0, z1=1.06)                  # c303–c374 CTA
    P.append(C.placa(1.2, T / 's09_placa.mp4', fondo=T / 's10_4641.mp4'))                        # c267–c302 primeros 100
    P.append(cta)
    n = C.armar(P, T / 'p1_video.mp4')
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
    caja(0, 30, '¿Entra?')
    X.append(dict(t0=tx(0), t1=tx(30), txt='Boca · Final de la Sudamericana', estilo='CajaN_ctx', y=455))
    caja(30, 57, 'Travesaño.')
    caja(57, 66, '¿Y ahora?')
    X.append(dict(t0=tx(66), t1=tx(81), txt='GOL.', estilo='Golpe', y=GOL1_Y, pop=True))
    X.append(dict(t0=tx(81), t1=tx(96), txt='ANULADO.', estilo='Sello', y=560, pop=True, extra='\\frz8'))
    caja(96, 132, '¿Se queda en casi?')
    caja(132, 165, 'Minutos después.')
    X.append(dict(t0=tx(165), t1=tx(189), txt='GOL.', estilo='Golpe', y=GOL2_Y, pop=True))
    caja(189, 228, 'Lo hizo\\Nel del anulado.')
    caja(228, 267, 'Y el del travesaño:')
    X.append(dict(t0=tx(248), t1=tx(267), txt='2-0.', estilo='Golpe', y=DOS_Y, pop=True))
    caja(267, 303, 'Uno de los primeros 100.')
    caja(303, 375, 'Pateá la tercera.')
    X.append(dict(t0=tx(312), t1=tx(375), txt='link en bio', estilo='CajaN_link', y=445))
    return X


# 30: la pelota pega y la ola revienta (golpe de zoom + destello); 303: la placa sale y el fondo queda en foco
TRANS = {30: 'zoom+destello', 57: 'barrido', 132: 'barrido', 189: 'zoom', 228: 'barrido_izq', 303: 'zoom'}


def trans():
    C.transiciones(T / 'p1_video.mp4', T / 'p1_video_t.mp4', TRANS, NF)
    print('transiciones', TRANS)


def audio(con_musica=True):
    DUR = NF / FPS
    m = C.MezclaB(DUR)
    # hinchada real de la final (clips filmados desde la tribuna, «sonido original»; sin escuchar: medido por niveles y espectro)
    GRITO, TRIB1, FEST, TRIB2 = C.clip('035221'), C.clip('774354'), C.clip('701384'), C.clip('652180')
    m.real(FEST, 6.0, t(0), t(30), -15, hp=150, ini=0.05, fin=0.02, etiqueta='hinchada real (fondo)')
    m.toma('IMG_4631', 3.75, t(30), t(57), -6, ini=0.01, fin=0.05)
    m.real(GRITO, 0.95, t(57), t(81), -3, ini=0.03, fin=0.01, etiqueta='hinchada real: el grito del gol anulado (sube en 1,25 s = c66)')
    m.toma('IMG_3453', 2.3, t(96), t(132), -18, ini=0.1, fin=0.05)
    m.real(TRIB1, 1.9, t(132), t(232), -5, ini=0.08, fin=0.3, etiqueta='hinchada real: el 1-0 desde la tribuna (pico en 3,0 s = c165)')
    m.real(FEST, 2.0, t(189), t(250), -9, hp=120, ini=0.3, fin=0.2, etiqueta='hinchada real: festejo del 1-0')
    m.real(TRIB2, 0.0, t(247), t(296), -4, ini=0.03, fin=0.6, etiqueta='hinchada real: el 2-0 desde la tribuna')
    m.toma('IMG_4641', 0.6, t(303), t(375), -9, ini=0.05, fin=0.3)
    # efectos
    m.latido(t(2), 0.5); m.latido(t(16), 0.55)
    m.subida(t(4), t(30), 0.12)
    m.clang(t(30), 0.55)
    m.latido(t(58), 0.5)
    m.impacto(t(66), 0.5)
    m.silbato(t(80), 0.5, 0.28)
    m.impacto(t(81), 0.35)
    m.latido(t(100), 0.45); m.latido(t(120), 0.45)
    m.redoble(t(142), t(165), 0.10); m.subida(t(142), t(165), 0.16)
    m.impacto(t(165), 0.55)
    for c, tp in TRANS.items():
        if 'barrido' in tp or 'zoom' in tp: m.barrido(t(c), 0.3, 0.15)
    m.impacto(t(248), 0.5)
    m.clang(t(267), 0.22)
    if con_musica:
        b = 60 / 140
        # tramo 1 (c0–c95): bajo sostenido que sube de tensión; corta en el ANULADO
        m.pad(t(0), [45, 52, 57], t(80), 0.05, corte=900)
        m.ocho08(t(66), 33, 0.45, 0.5, glide_desde=40)
        # tramo 2 (c96–c162): casi silencio con pad grave
        m.pad(t(96), [45, 48, 52], t(69), 0.04, corte=700)
        # tramo 3 (c165–fin): ritmo a 140 (medio tiempo)
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
    print(nombre, r)


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
