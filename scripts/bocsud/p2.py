#!/usr/bin/env python3
"""BOC-SUD P2 «La cuarta final» · valor: GIVE HISTORY YOUR NAME (el casi como etapa) · receta v03 (24/11/2026; v03 = video real del partido).

Hechos (01_pepe_verificacion.md): finales internacionales perdidas desde la Recopa 2008: Libertadores 2012 (vuelta en
Pacaembú), 2018 (vuelta en el Bernabéu, alargue), 2023 (Maracaná, alargue). 21/11/2026: 2-0 a Mineiro en Barranquilla.
v03: la final 2026 entra con clips oficiales (TikTok @sudamericana, © CONMEBOL: material de terceros, ver 06_licencias.md):
  726600 (dron sobre el equipo formado, de espaldas), 622854 (tribuna general), 452807 (el 2-0 desde arriba: la pelota
  cruza la línea en 5,33 s), 568392 (la copa, el arco «CAMPEÓN 2026» y el papel picado).
  El primer cuadro pasa a ser video real de 2026 («Cuarta final. / ¿La gana?»); las tres finales perdidas son un
  recuerdo rápido con las fotos de los estadios (Commons: muestran el lugar, no el partido; créditos en la descripción).
Sin hinchas rivales ni festejos de River. La receta v02 (fotos animadas) está en el commit 380c65c.

Etapas: python3 p2.py planos | trans | audio | master | todo
"""
import sys, json
from pathlib import Path
sys.path.insert(0, '/home/user/1/scripts/bocsud')
import comun as C
V = C.V

T = C.T / 'p2'
FPS = 30
A = C.ARCH


PACAEMBU = A / 'pacaembu_1920.jpg'          # Commons «Estádio do Pacaembu 1.jpg» (Rodrigo Soldon, CC BY 2.0)
BERNABEU = A / 'bernabeu_noche_1920.jpg'    # Commons «Estadio Santiago Bernabéu 13.jpg» (Luis García, CC BY-SA 3.0)
MARACANA = A / 'maracana_1920.jpg'          # Commons «Maracana 2022.jpg» (Arne Müseler, CC BY-SA 3.0 de)
TELONES = A / 'telones_2560.jpg'            # Commons «Hinchada de Boca desplegando sus telones.JPG» (Gonzaloges, dominio público)
SALIDA = C.T / 'borradores' / 'p2_borrador.mp4'

# encuadres por foto (centro x, y en 0..1)
ENC = {'pacaembu': (0.54, 0.48), 'bernabeu': (0.36, 0.48), 'maracana': (0.5, 0.47)}

S0 = (0, 36)                     # Cuarta final. / ¿La gana?
F1, NO1 = (36, 60), 44           # las tres finales perdidas: 24, 26 y 26 cuadros; «NO.» + «Alargue.» quedan 16–18 cuadros
F2, NO2 = (60, 86), 68
F3, NO3 = (86, 112), 94
SEQ = (112, 142)                 # Desde 2008, ninguna internacional.
NO_Y, ALARGUE_Y, DOS_Y = 1200, 1362, 1330
GOL = (142, 198); GOL_T = 178    # Final 2026 / ¿Otra vez? → 2-0. (la pelota cruza la línea en k = 36)
CAMP = (198, 234)
CASI = (234, 270)
PLACA = (270, 306)
CTA = (306, 366)
NF = 366


def gris_desde(k0):
    return lambda k, f: C.destenir(f, 0.85) if k >= k0 else f


def planos():
    P = []
    # S0: el dron pasa sobre el equipo formado, de espaldas, con el estadio lleno (24 fps, un cuadro por cuadro)
    P.append(C.real('726600', 17.25, S0[1] - S0[0], T / 's_dron.mp4', c0=(0.5, 0.5), z0=1.0, z1=1.08, uno_a_uno=True))
    for (a, b), no, img, key in ((F1, NO1, PACAEMBU, 'pacaembu'), (F2, NO2, BERNABEU, 'bernabeu'), (F3, NO3, MARACANA, 'maracana')):
        cx, cy = ENC[key]
        P.append(C.foto_movil(img, (b - a) / FPS, T / f's_{key}.mp4', 'cubrir', z0=1.05, z1=1.22, c0=(cx, cy),
                              sacudida=[(no - a, 14)], por_cuadro=gris_desde(no - a)))
    # la tribuna de Barranquilla (plano general)
    P.append(C.real('622854', 0.4, SEQ[1] - SEQ[0], T / 's_tribuna.mp4', c0=(0.5, 0.5), z0=1.0, z1=1.06))
    # el 2-0 desde arriba, en un plano continuo: la jugada (¿Otra vez?) y la pelota que cruza la línea en 5,33 s (2-0.)
    k0 = GOL_T - GOL[0]
    P.append(C.real('452807', 4.13, GOL[1] - GOL[0], T / 's_gol.mp4', c0=(0.685, 0.393), c1=(0.72, 0.39), z0=1.588, z1=1.75,
                    por_cuadro=lambda k, f: C.flash(C.sombra(f, 540, DOS_Y, k=0.4), max(0.0, 0.45 - 0.15 * (k - k0))) if k >= k0 else f))
    # la copa: el arco «CAMPEÓN 2026» y el papel picado
    P.append(C.real('568392', 6.2, CAMP[1] - CAMP[0], T / 's_campeon.mp4', c0=(0.5, 0.5), z0=1.0, z1=1.08))
    P.append(C.propia('IMG_3375', 0.3, 0.3 + (CASI[1] - CASI[0]) / FPS, T / 's_3375.mp4', z0=1.0, z1=1.06))
    cta = C.propia('IMG_7896', 4.15, 4.15 + (CTA[1] - CTA[0]) / FPS, T / 's_7896.mp4', cx=0.5, cy=0.42, z0=1.16, z1=1.20)
    P.append(C.placa((PLACA[1] - PLACA[0]) / FPS, T / 's_placa.mp4', empuje=0.18, foco=(0.5, 0.78), fondo=T / 's_7896.mp4'))
    P.append(cta)
    n = C.armar(P, T / 'p2_video.mp4')
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
        X.append(dict(t0=tx(a), t1=tx(b), txt=txt, estilo=est, y=C.Y_HOOK if est == 'CajaN_hook' else y, pop=kw.pop('pop', True), **kw))
    caja(S0[0], S0[1], 'Cuarta final.\\N¿La gana?')
    # «Cuarta final.» lleva su calificador al lado (regla: siempre «internacional»): 2012, 2018, 2023 y 2026. «tras» y no
    # «desde»: la Recopa 2008 también fue una final. Sin esto, junto a «Sudamericana» se leía como cuarta final de esa copa.
    X.append(dict(t0=tx(S0[0]), t1=tx(S0[1]), txt='Boca · finales internacionales tras 2008', estilo='CajaN_ctx', y=585))
    for (a, b), no, anio, lugar, extra in ((F1, NO1, 'Final 2012', 'São Paulo', None),
                                           (F2, NO2, 'Final 2018', 'Madrid', 'Alargue.'),
                                           (F3, NO3, 'Final 2023', 'Río', 'Alargue.')):
        caja(a, b, anio)
        X.append(dict(t0=tx(a), t1=tx(b), txt=f'Boca · Libertadores · {lugar}', estilo='CajaN_ctx', y=455))
        X.append(dict(t0=tx(no), t1=tx(b), txt='NO.', estilo='SelloG', y=NO_Y, pop=True, extra='\\frz6'))
        if extra:       # entra junto con el «NO.»: es la pista que cobra «Sin alargue.»
            X.append(dict(t0=tx(no), t1=tx(b), txt=extra, estilo='CajaN_96', y=ALARGUE_Y, pop=True))
    caja(SEQ[0], SEQ[1], 'Desde 2008,\\Nninguna internacional.')
    caja(GOL[0], GOL_T, 'Final 2026\\N¿Otra vez?')
    X.append(dict(t0=tx(GOL[0]), t1=tx(GOL_T), txt='Boca · Sudamericana · Barranquilla', estilo='CajaN_ctx', y=585))
    X.append(dict(t0=tx(GOL_T), t1=tx(GOL[1]), txt='2-0.', estilo='Golpe', y=DOS_Y, pop=True))
    caja(CAMP[0], CAMP[1], 'Sin alargue.\\NCampeón.')
    caja(CASI[0], CASI[1], 'Tres casi.\\NDespués, historia.')
    caja(PLACA[0], PLACA[1], '2026.')
    caja(CTA[0], NF, 'Cerrá tu 2026.')
    X.append(dict(t0=tx(CTA[0] + 8), t1=tx(NF), txt='Con placa y número.', estilo='CajaN_ctx', y=455))
    X.append(dict(t0=tx(CTA[0] + 14), t1=tx(NF), txt='link en bio', estilo='CajaN_link', y=555))
    return X


TRANS = {F1[0]: 'barrido', F2[0]: 'barrido', F3[0]: 'barrido', SEQ[0]: 'zoom', GOL[0]: 'barrido', CAMP[0]: 'zoom',
         CASI[0]: 'barrido', CTA[0]: 'barrido_izq'}


def trans():
    C.transiciones(T / 'p2_video.mp4', T / 'p2_video_t.mp4', TRANS, NF)
    print('transiciones', TRANS)


def audio(con_musica=True):
    DUR = NF / FPS
    m = C.MezclaB(DUR)
    # hinchada real de la final (clips filmados desde la tribuna, «sonido original»; sin escuchar: medido por niveles y espectro)
    FEST, TRIB2 = C.clip('701384'), C.clip('652180')
    m.real(FEST, 6.0, t(S0[0]), t(F1[0]), -10, hp=150, ini=0.05, fin=0.03, etiqueta='hinchada real (fondo)')
    m.real(FEST, 9.0, t(SEQ[0]), t(GOL_T), 3, hp=150, ini=0.12, fin=0.03, etiqueta='hinchada real (espera)')
    m.real(TRIB2, 0.0, t(GOL_T), t(CASI[0]) + 0.2, -3, ini=0.02, fin=0.4, etiqueta='hinchada real: el 2-0 desde la tribuna')
    m.toma('IMG_3375', 0.3, t(CASI[0]), t(CASI[1]), -20, ini=0.05, fin=0.05)
    m.toma('IMG_7896', 4.15, t(CTA[0]), t(NF), -8, ini=0.05, fin=0.3)
    b = 60 / 128
    m.latido(t(4), 0.5); m.latido(t(20), 0.55)
    for no in (NO1, NO2, NO3):
        m.golpe_sordo(t(no), 0.7); m.impacto(t(no), 0.25)
    for c, tp in TRANS.items():
        if 'barrido' in tp or 'zoom' in tp: m.barrido(t(c), 0.3, 0.15)
    m.latido(t(GOL[0] + 4), 0.55); m.latido(t(GOL[0] + 20), 0.6)
    m.subida(t(GOL[0]), t(GOL_T), 0.16)
    m.impacto(t(GOL_T), 0.75)
    m.silbato(t(CAMP[0]) - 0.05, 0.7, 0.18)
    m.clang(t(PLACA[0]), 0.22)
    if con_musica:
        m.pad(t(0), [45, 52], t(F1[0]), 0.045, corte=900)
        # tramo 1: pulso grave que baja de tono con cada final perdida
        for k, (c, nota) in enumerate(((F1[0], 40), (F2[0], 38), (F3[0], 36))):
            m.ocho08(t(c), nota, 0.75, 0.42)
            m.charles(t(c), 0.06); m.charles(t(c) + b, 0.06)
        m.pad(t(SEQ[0]), [45, 48, 52], t(GOL_T - SEQ[0]), 0.045, corte=800)
        m.redoble(t(GOL[0] + 10), t(GOL_T), 0.10)
        # tramo 2: desde el 2-0, ritmo a 128 hasta el final
        k = 0; t0 = t(GOL_T)
        while t0 + k * b < t(NF) - 0.05:
            tt = t0 + k * b
            if k % 4 == 0:
                m.bombo(tt, 0.85); m.ocho08(tt, [33, 36, 31, 33][(k // 4) % 4], b * 3.6, 0.5, glide_desde=40 if k == 0 else None)
            if k % 4 == 2:
                m.palma(tt, 0.28); m.bombo(tt + b * 0.5, 0.45)
            m.charles(tt, 0.08); m.charles(tt + b / 2, 0.05)
            k += 1
        m.pad(t(GOL_T), [45, 52, 57, 60], t(NF - GOL_T), 0.045, corte=1600)
        m.fundido('mus', t(NF) - 0.35, t(NF)); m.fundido('bombo', t(NF) - 0.35, t(NF))
    (T / 'audio').mkdir(exist_ok=True)
    nombre = 'p2_completa.wav' if con_musica else 'p2_sinmusica.wav'
    r = m.exportar(str(T / 'audio' / nombre), lufs=-14)
    print(nombre, r)


def master():
    a = V.ass(textos(), T / 'p2.ass')
    V.master(T / 'p2_video_t.mp4', T / 'audio' / 'p2_completa.wav', SALIDA, ass_path=a)
    print(SALIDA)


if __name__ == '__main__':
    T.mkdir(parents=True, exist_ok=True)
    faltan = [n for n, p in (('Pacaembú', PACAEMBU), ('Bernabéu', BERNABEU), ('Maracaná', MARACANA)) if not p.exists()]
    if faltan:
        sys.exit(f'faltan fotos: {faltan}')
    et = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    if et in ('planos', 'todo'): planos()
    if et in ('trans', 'todo'): trans()
    if et in ('audio', 'todo'): audio(True)
    if et in ('master', 'todo'): master()
