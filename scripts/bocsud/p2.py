#!/usr/bin/env python3
"""BOC-SUD P2 «La cuarta final» · valor: GIVE HISTORY YOUR NAME (el casi como etapa) · receta v01 (24/11/2026).

Hechos (01_pepe_verificacion.md): finales internacionales perdidas desde la Recopa 2008: Libertadores 2012 (vuelta en
Pacaembú), 2018 (vuelta en el Bernabéu, alargue), 2023 (Maracaná, alargue). 21/11/2026: 2-0 a Mineiro en Barranquilla.
Fotos de los estadios: Wikimedia Commons (licencias en 06_licencias.md). Sin hinchas rivales ni festejos de River.
Las fechas de las fotos no son las de las finales: muestran el estadio, no el partido (se dice en la entrega).

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
TELONES = A / 'telones_1920.jpg'            # Commons «Hinchada de Boca desplegando sus telones.JPG» (Gonzaloges, dominio público)
ESTADIO = A / 'final2026_1920.jpg'          # Commons «Estadio Metropolitano de Barranquilla.jpg» (licencia dudosa)
OBELISCO_A = A / 'Buenos_Aires_-_Boca_Juniors_-_D_a_del_hincha_-_131212a.webm'
SALIDA = C.T / 'borradores' / 'p2_borrador.mp4'

# encuadres por foto (centro x, y en 0..1)
ENC = {'pacaembu': (0.54, 0.48), 'bernabeu': (0.36, 0.48), 'maracana': (0.5, 0.47), 'telones': (0.42, 0.55)}

# cuadros (las tres finales aceleran: 36, 28 y 26 cuadros)
F1, NO1 = (0, 36), 22
F2, NO2 = (36, 64), 52
F3, NO3 = (64, 90), 78
SEQ = (90, 126)
F4 = (126, 162)
GOL = (162, 195); GOL_T = 171
CAMP = (195, 231)
CASI = (231, 267)
PLACA = (267, 303)
CTA = (303, 363)
NF = 363


def gris_desde(k0):
    return lambda k, f: C.destenir(f, 0.85) if k >= k0 else f


def planos():
    P = []
    for (a, b), no, img, key in ((F1, NO1, PACAEMBU, 'pacaembu'), (F2, NO2, BERNABEU, 'bernabeu'), (F3, NO3, MARACANA, 'maracana')):
        cx, cy = ENC[key]
        P.append(C.foto_movil(img, (b - a) / FPS, T / f's_{key}.mp4', 'cubrir', z0=1.05, z1=1.22, c0=(cx, cy),
                              sacudida=[(no - a, 14)], por_cuadro=gris_desde(no - a)))
    cx, cy = ENC['telones']
    P.append(C.foto_movil(TELONES, (SEQ[1] - SEQ[0]) / FPS, T / 's_telones.mp4', 'cubrir', z0=1.0, z1=1.12, c0=(cx, cy)))
    P.append(C.foto_movil(ESTADIO, (F4[1] - F4[0]) / FPS, T / 's_2026.mp4', 'cubrir', z0=1.0, z1=1.3,
                          c0=(0.5, 0.55), c1=(0.42, 0.62)))
    P.append(C.propia('IMG_7895', 0.0, (GOL[1] - GOL[0]) / FPS, T / 's_7895.mp4', cx=0.45, cy=0.45, z0=1.05, z1=1.12))
    P.append(C.foto_movil(ESTADIO, (CAMP[1] - CAMP[0]) / FPS, T / 's_campeon.mp4', 'cubrir', z0=1.15, z1=1.35,
                          c0=(0.66, 0.64), c1=(0.68, 0.63)))
    P.append(C.propia('IMG_3375', 0.3, 0.3 + (CASI[1] - CASI[0]) / FPS, T / 's_3375.mp4', z0=1.0, z1=1.06))
    P.append(C.placa((PLACA[1] - PLACA[0]) / FPS, T / 's_placa.mp4', empuje=0.18, foco=(0.5, 0.78)))
    P.append(C.propia('IMG_7896', 4.15, 4.15 + (CTA[1] - CTA[0]) / FPS, T / 's_7896.mp4', cx=0.5, cy=0.42, z0=1.16, z1=1.20))
    n = C.armar(P, T / 'p2_video.mp4')
    assert n == NF, n
    json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('cuadros', n)


def t(c):
    return c / FPS


def textos():
    X = []
    def caja(a, b, txt, y=245, maximo='CajaN_hook', **kw):
        est = C.caja(txt, maximo)
        X.append(dict(t0=t(a), t1=t(b), txt=txt, estilo=est, y=C.Y_HOOK if est == 'CajaN_hook' else y, pop=kw.pop('pop', True), **kw))
    for (a, b), no, anio, lugar, preg, extra in ((F1, NO1, 'Final 2012', 'São Paulo', '¿La gana?', None),
                                                 (F2, NO2, 'Final 2018', 'Madrid', '¿Y esta?', 'Alargue.'),
                                                 (F3, NO3, 'Final 2023', 'Río', '¿Esta sí?', 'Alargue.')):
        caja(a, b, f'{anio}\\N{preg}', pop=(a == 0))
        X.append(dict(t0=t(a), t1=t(b), txt=f'Boca · Libertadores · {lugar}', estilo='CajaN_ctx', y=585))
        X.append(dict(t0=t(no), t1=t(b), txt='NO.', estilo='SelloG', y=1040, pop=True, extra='\\frz6'))
        if extra:
            X.append(dict(t0=t(no + 3), t1=t(b), txt=extra, estilo='CajaN_96', y=1260))
    caja(SEQ[0], SEQ[1], 'Desde 2008,\\Nninguna internacional.')
    caja(F4[0], F4[1], 'Final 2026\\N¿Otra vez?')
    X.append(dict(t0=t(F4[0]), t1=t(F4[1]), txt='Boca · Sudamericana · Barranquilla', estilo='CajaN_ctx', y=585))
    X.append(dict(t0=t(GOL_T), t1=t(GOL[1]), txt='2-0.', estilo='Golpe', y=560, pop=True))
    caja(CAMP[0], CAMP[1], 'Sin alargue. Campeón.')
    caja(CASI[0], CASI[1], 'Tres casi.\\NDespués, historia.')
    caja(PLACA[0], PLACA[1], '2026.')
    caja(CTA[0], NF, 'Cerrá tu 2026.')
    X.append(dict(t0=t(CTA[0] + 8), t1=t(NF), txt='Con placa y número.', estilo='CajaN_ctx', y=455))
    X.append(dict(t0=t(CTA[0] + 14), t1=t(NF), txt='link en bio', estilo='CajaN_link', y=555))
    return X


TRANS = {F2[0]: 'barrido', F3[0]: 'barrido', SEQ[0]: 'zoom', F4[0]: 'barrido', GOL[0]: 'destello', CAMP[0]: 'zoom',
         CASI[0]: 'barrido', CTA[0]: 'barrido_izq'}


def trans():
    C.transiciones(T / 'p2_video.mp4', T / 'p2_video_t.mp4', TRANS, NF)
    print('transiciones', TRANS)


def audio(con_musica=True):
    DUR = NF / FPS
    m = C.MezclaB(DUR)
    hay = OBELISCO_A.exists()
    if hay:
        m.real(OBELISCO_A, 2.0, t(0), t(NO1), -16, hp=120, ini=0.05, fin=0.02, etiqueta='Obelisco 2013 (murmullo)')
        m.real(OBELISCO_A, 8.0, t(SEQ[0]), t(F4[1]), -16, hp=120, ini=0.2, fin=0.05, etiqueta='Obelisco 2013 (espera)')
        m.real(OBELISCO_A, 30.0, t(GOL_T), t(CASI[0]), -4, ini=0.01, fin=0.3, etiqueta='Obelisco 2013 (festejo)')
    m.toma('IMG_7895', 0.0, t(GOL[0]), t(GOL[1]), -6, fin=0.02)
    m.toma('IMG_3375', 0.3, t(CASI[0]), t(CASI[1]), -20, ini=0.05, fin=0.05)
    m.toma('IMG_7896', 4.15, t(CTA[0]), t(NF), -8, ini=0.05, fin=0.3)
    b = 60 / 128
    for no in (NO1, NO2, NO3):
        m.golpe_sordo(t(no), 0.7); m.impacto(t(no), 0.25)
    for c, tp in TRANS.items():
        if 'barrido' in tp or 'zoom' in tp: m.barrido(t(c), 0.3, 0.15)
    m.latido(t(F4[0] + 4), 0.55); m.latido(t(F4[0] + 20), 0.6)
    m.subida(t(F4[0]), t(GOL_T), 0.16)
    m.impacto(t(GOL_T), 0.75)
    m.silbato(t(CAMP[0]) - 0.05, 0.7, 0.18)
    m.clang(t(PLACA[0]), 0.22)
    if con_musica:
        # tramo 1: pulso grave que baja de tono con cada final perdida
        for k, (c, nota) in enumerate(((F1[0], 40), (F2[0], 38), (F3[0], 36))):
            m.ocho08(t(c), nota, 0.85, 0.42)
            m.charles(t(c), 0.06); m.charles(t(c) + b, 0.06)
        m.pad(t(SEQ[0]), [45, 48, 52], t(F4[1] - SEQ[0]), 0.045, corte=800)
        m.redoble(t(F4[0] + 10), t(GOL_T), 0.10)
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
    print(nombre, r, 'hinchada real' if hay else 'SIN hinchada real')


def master():
    a = V.ass(textos(), T / 'p2.ass')
    V.master(T / 'p2_video_t.mp4', T / 'audio' / 'p2_completa.wav', SALIDA, ass_path=a)
    print(SALIDA)


if __name__ == '__main__':
    T.mkdir(parents=True, exist_ok=True)
    faltan = [n for n, p in (('Pacaembú', PACAEMBU), ('Bernabéu', BERNABEU), ('Maracaná', MARACANA), ('telones', TELONES)) if not p]
    if faltan:
        sys.exit(f'faltan fotos: {faltan}')
    et = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    if et in ('planos', 'todo'): planos()
    if et in ('trans', 'todo'): trans()
    if et in ('audio', 'todo'): audio(True)
    if et in ('master', 'todo'): master()
