#!/usr/bin/env python3
"""MARCA · MC-01 «LADRILLO A LADRILLO · Cap. 1» · receta de los másteres v01 (Pedro A, 25/11/2026).

Guion aprobado: piezas/MARCA_comunidad/04_fede_guiones_G1.md §0, §MC-01, §8 + condiciones 06_roma_aprobacion_G1.md
+ especificación 05_especificacion_comun.md. Interfaz con scripts/marca/comun.py (sin modificar) vía mc0102_util.py.

Etapas (python de TRABAJO/venv, cada una por separado):
  hojas   → hojas cada 0,1 s de los tramos dudosos (cuadro y ms de la FUENTE impresos)
  planos  → 13 planos (color de video.py) + Blanca neutralizada donde sale fría (8008, 7894) + unión (462 cuadros)
  capa    → interfaz por cuadro (marcador, ficha, textos, VAR) para los hooks A y B
  audio   → mezcla completa y sin música (−14 LUFS, pico ≤ −1 dBTP)
  master  → A, B y A_SINMUSICA (mismo flujo de video que A)
  control → evidencia_v01/ (ffprobe, md5 de flujos, sonoridad, cortes, hojas, 360 px, texto vs estampado, marcador)
  entregar→ EXPORTACIONES/ + carpeta de la pieza
Intermedios: TRABAJO/marca/MC-01/. Sin servicios externos ni créditos.
"""
import json, math, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, '/home/user/1/scripts/marca')
import mc0102_util as M          # noqa: E402  (envuelve V.sh con nice)
from mc0102_util import V, U, C, D, W, H, FPS   # noqa: E402

R = Path('/home/user/1')
T = R / 'TRABAJO/marca/MC-01'
HJ, P, A, MAS, EVID = T / 'hojas', T / 'planos', T / 'audio', T / 'master', T / 'evidencia_v01'
PIEZA = Path('/mnt/project-files/piezas/MARCA_comunidad/MC-01_ladrillo_a_ladrillo')
NF = 462
REUSAR = '--rehacer' not in sys.argv     # planos ya renderizados se reutilizan (la Blanca se recalcula siempre)
DUR = NF / FPS                       # 15,400 s
NOMBRES = {'A': 'ROCCE_MC01_LADRILLO_A_LADRILLO_A_v01.mp4', 'B': 'ROCCE_MC01_LADRILLO_A_LADRILLO_B_v01.mp4',
           'SINMUSICA': 'ROCCE_MC01_LADRILLO_A_LADRILLO_SINMUSICA_v01.mp4'}


def cuadro_de(toma, t):
    pts = U.tiempos_src(toma) if toma not in U._PTS else U._PTS[toma]
    U._PTS[toma] = pts
    return int(np.argmin(np.abs(np.array(pts) - t)))


# =====================================================================================================
# hojas cada 0,1 s (lista de §8 de Fede para MC-01 + el final de 4631 cuadro a cuadro)
# =====================================================================================================
def etapa_hojas():
    HJ.mkdir(parents=True, exist_ok=True)
    U.hoja_src('IMG_7887', 0, 110, HJ / '7887_0.0-3.7_c3.jpg', cada=3, ancho=180, cols=10)
    U.hoja_src('IMG_8008', 6, 64, HJ / '8008_0.2-2.2_c3.jpg', cada=3, ancho=180, cols=10)
    U.hoja_src('IMG_7885', 30, 138, HJ / '7885_1.0-4.6_c3.jpg', cada=3, ancho=180, cols=10)
    U.hoja_src('IMG_4631', 168, 192, HJ / '4631_5.6-6.4_c1.jpg', cada=1, ancho=150, cols=13)


# =====================================================================================================
# planos · tabla §MC-01 con los cuadros reales (desvíos anotados en la hoja de máster)
# =====================================================================================================
SAT9 = "hue=s='1-0.85*min(t/0.9667\\,1)'"            # plano 9: saturación 1 → 0,15 por cuadro (t relativo al plano)
VAR_POST = 'hue=s=0.35,eq=contrast=1.08'             # plano 10: repetición


# Blanca por plano (criterio común de la tanda, 25/11): caja de la remera a mano (mitad de cada plano, hoja
# rev/mids_grid.jpg); neutralizar_blanca la mide en la tela lisa (L > 170, sat < 0,15) y la lleva a B−R ≤ +8 solo si pasa
# de +12. 09 (4641) y 10 (VAR) quedan afuera de la corrección: su saturación baja a propósito (falso final, repetición).
BLANCA = {'01': ((360, 860, 660, 1090), '7887: la Blanca en la roca, detrás de Gianluca'),
          '02': ((40, 930, 620, 1340), '7887 z 1,25'),
          '03': ((0, 600, 1080, 1920), '8008: espalda en arena mojada'),
          '04': ((100, 790, 730, 1100), '7887: la Blanca en la roca'),
          '07': ((0, 680, 450, 1100), '7894: las dos en las rocas'),
          '08': ((60, 690, 1020, 1710), '4641: de frente en la roca'),
          '11': ((0, 450, 1080, 1500), '7885: acercamiento a la espalda'),
          '12': ((60, 1070, 610, 1600), '4631: las dos, la ola atrás'),
          '13': ((60, 1070, 610, 1600), '4631: las dos, el mar se calma')}
MEDIR_SOLO = {'09': ((60, 690, 1020, 1710), '4641: saturación 1 → 0,15 a propósito (falso final)'),
              '10': ((100, 790, 730, 1100), 'VAR 7887: saturación 0,35 a propósito')}


def plan():
    n8 = cuadro_de('IMG_4641', 1.20); n6 = cuadro_de('IMG_7824', 4.80)
    bc = lambda k: BLANCA[k][0]
    return [
        dict(id='01', m0=0, tipo='n', toma='IMG_7887', n0=0, nf=36, blanca=bc('01')),
        dict(id='02', m0=36, tipo='z', toma='IMG_7887', n0=36, zs=[1.25] * 24, cx=1500, cy=1740, blanca=bc('02')),
        # 8008 tiene 65 cuadros (0–64): 1,40–2,20 pediría el cuadro 66. Se usan 41–64 (1,367–2,167); MC-02 usa 5–40.
        dict(id='03', m0=60, tipo='n', toma='IMG_8008', n0=41, nf=24, blanca=bc('03')),
        dict(id='04', m0=84, tipo='n', toma='IMG_7887', n0=81, nf=30, blanca=bc('04')),
        # 3453 con la corrección de video.TOMAS sigue marrón (tela R−B +13): se neutraliza solo la tela oscura (neutralizar_negra)
        dict(id='05', m0=114, tipo='n', toma='IMG_3453', n0=99, nf=27, negra=True),
        dict(id='06', m0=141, tipo='n', toma='IMG_7824', n0=n6, nf=30),
        dict(id='07', m0=171, tipo='n', toma='IMG_7894', n0=9, nf=27, blanca=bc('07')),
        dict(id='08', m0=198, tipo='n', toma='IMG_4641', n0=n8, nf=27, blanca=bc('08')),
        dict(id='09', m0=225, tipo='z', toma='IMG_4641', n0=n8 + 27, zs=[1.0 + 0.08 * k / 29 for k in range(30)],
             cx=540, cy=960, post=SAT9),
        # VAR: 7887 cuadros 93–110 (3,10–3,667; el 111 no existe) estirados a 45 cuadros con mezcla (vel 0,386)
        dict(id='10', m0=255, tipo='lento', toma='IMG_7887', n0=93, n_src=18, nf=45, post=VAR_POST),
        dict(id='11', m0=300, tipo='n', toma='IMG_7885', n0=93, nf=45, blanca=bc('11')),
        dict(id='12', m0=345, tipo='n', toma='IMG_4631', n0=72, nf=30, blanca=bc('12')),
        dict(id='13', m0=375, tipo='n', toma='IMG_4631', n0=102, nf=87, blanca=bc('13')),
    ]


def etapa_planos():
    P.mkdir(parents=True, exist_ok=True)
    reg, colores, negras = [], {}, {}
    for p in plan():
        out = P / f"{p['id']}.mp4"
        crudo = P / f"{p['id']}_sin_neutralizar.mp4"
        neutra = p.get('blanca') or p.get('negra')
        hecho = crudo if neutra else out
        reusar = hecho.exists() and hecho.with_suffix('.json').exists() and REUSAR
        if reusar:                                         # intermedio ya hecho con la misma receta: se reutiliza
            r = json.load(open(hecho.with_suffix('.json')))
        elif p['tipo'] == 'n':
            r = M.plano(p['toma'], p['n0'], p['nf'], out)
        elif p['tipo'] == 'z':
            r = M.plano_z(p['toma'], p['n0'], p['zs'], p['cx'], p['cy'], out, post=p.get('post'))
        else:
            r = M.plano_lento(p['toma'], p['n0'], p['n_src'], p['nf'], out, post=p.get('post'))
        if not reusar:
            r = {k: v for k, v in r.items() if k != 'ventanas'}
            if neutra:
                shutil.move(out, crudo); r['salida'] = str(crudo)
            M.jdump(r, hecho.with_suffix('.json'))
        if p.get('blanca'):
            colores[p['id']] = M.neutralizar_blanca(crudo, out, p['blanca'])
            r = dict(r, salida=str(out))
        if p.get('negra'):
            negras[p['id']] = M.neutralizar_negra(crudo, out)
            r = dict(r, salida=str(out))
        r.update(id=p['id'], m0=p['m0'])
        assert M.contar(out) == r['cuadros'], (p['id'], M.contar(out), r['cuadros'])
        reg.append(r); print(p['id'], p['toma'], r['cuadros'], flush=True)
    n = M.unir(reg, T / 'mc01_base.mp4')
    assert n == NF, n
    for r in reg:
        r.pop('ventanas', None)
    M.jdump(dict(cuadros=n, planos=reg, blanca=colores, negra=negras), T / 'planos.json')
    print('total', n)


# =====================================================================================================
# interfaz (§MC-01: gráfica, textos exactos, micro-apuestas 6 cuadros después de cada corte)
# =====================================================================================================
CORTES = [36, 60, 84, 114, 141, 171, 198, 225, 255, 300, 345, 375]
# marcador: (cuadro, a favor, en contra) — secuencia exacta de Fede / Roma
PUNTOS = [(0, 0, 0), (42, 0, 1), (66, 1, 1), (90, 1, 2), (120, 2, 2), (147, 3, 2), (177, 3, 3), (204, 3, 4), (323, 4, 3)]
PLACA_XY = (130, 300, 820, 112)            # x, y, ancho, alto
FICHA_ON, VIAJE = 90, (315, 323)
SERIE = 'LADRILLO A LADRILLO · CAP. 1'
HOOK = {'A': ('¿Una marca para el mundo\ndesde Cañuelas?', '¿Una marca para el mundo desde Cañuelas?'),
        'B': ('¿Me sale una marca\npremium?', '¿Me sale una marca premium?')}

# textos por tramo: (n0, n1, tipo, texto, y, opciones). y = borde superior del renglón (guion).
# Tamaños de placa: 88 px salvo que no entre en 940 px (se baja al tamaño que entra, ≥ 80) — ver hoja de máster.
TEXTOS = [
    (36, 59, 'placa', 'TENGO 19.', 460, {}),
    (60, 83, 'placa', 'PARCHE DE DENIM.', 460, {}),
    (84, 113, 'placa', 'MI LABURO: LADRILLOS.', 460, dict(size=80)),
    (84, 113, 'datoC', 'en la fábrica de mi familia', 570, {}),
    (114, 140, 'placa', 'RELIEVE EN EL PECHO.', 460, dict(size=86)),
    (141, 170, 'placa', 'TONO SOBRE TONO.', 460, {}),
    (171, 197, 'placa', 'ROCCÉ, EN PARALELO.', 460, dict(size=86, halo=0.75)),
    (198, 224, 'placa', 'Y EL MAR, EN CONTRA.', 460, dict(size=84, halo=0.75)),
    (225, 254, 'cajaN', '3–4. ¿PERDÍ?', 460, dict(pop=True)),
    (255, 299, 'cajaN', 'REVISIÓN · VAR', 460, {}),
    (255, 299, 'datoC', 'LA FÁBRICA: ¿EN CONTRA?', 620, {}),
    # 7885 se acerca y desde c339 ROCCÉ sube hasta el renglón de y 460 (contacto medido): placa 76 px en y 448 con
    # interlineado 1,0 y salida en c337–c338 (fundido); c339–c344 sin texto, la espalda entera (prueba de ropa)
    (300, 338, 'placa', 'En casa se construye\nde a un ladrillo.', 448, dict(size=76, interlineado=1.0, salida=2)),
    (345, 374, 'caja', 'Roccé también.', 460, dict(pop=True)),
    (375, 461, 'placa', 'PARTIDO ABIERTO.', 460, {}),
    (399, 461, 'caja', '¿ME BANCÁS?', 600, dict(pop=True)),
    (423, 461, 'datoC', 'Seguí el marcador: Cap. 2.', 760, {}),
]


def puntos_en(n):
    af = ec = 0; cambio = None
    for c, a, e in PUNTOS:
        if n >= c:
            if (a, e) != (af, ec):
                cambio = (c, a != af, e != ec)
            af, ec = a, e
    return af, ec, cambio


def _ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


_LAY = {}


def layout():
    if not _LAY:
        fl, fn = C.fuente('semibold', 46), C.fuente('extrabold', 72)
        x0, y0, w, h = PLACA_XY
        _LAY.update(fl=fl, fn=fn, lab_af_x=x0 + 30, lab_ec_x1=x0 + w - 30, num_af_x1=W // 2 - 34, num_ec_x0=W // 2 + 34,
                    cy=y0 + h / 2)
        _LAY['cx_af'] = _LAY['lab_af_x'] + fl.getlength('A FAVOR') / 2
        _LAY['cx_ec'] = _LAY['lab_ec_x1'] - fl.getlength('EN CONTRA') / 2
    return _LAY


def marcador_img(af, ec, pulso_af=1.0, pulso_ec=1.0):
    """placa #141414 al 85 % de 820×112 (radio 20) en x 130, y 300; A FAVOR y su número en celeste de marca
    (comun.CELESTE), EN CONTRA en blanco; etiquetas 46 px (SemiBold), números 72 px (ExtraBold)."""
    lay = layout(); x0, y0, w, h = PLACA_XY
    L = C.lienzo(); d = ImageDraw.Draw(L)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=20, fill=C.TINTA + (217,))
    cy = lay['cy']; fl = lay['fl']
    d.text((lay['lab_af_x'], cy), 'A FAVOR', font=fl, fill=C.CELESTE + (255,), anchor='lm')
    d.text((lay['lab_ec_x1'], cy), 'EN CONTRA', font=fl, fill=C.BLANCO + (255,), anchor='rm')
    d.text((W // 2, cy), '·', font=lay['fn'], fill=C.BLANCO + (255,), anchor='mm')
    for val, x, anc, col, pul in ((af, lay['num_af_x1'], 'rm', C.CELESTE, pulso_af), (ec, lay['num_ec_x0'], 'lm', C.BLANCO, pulso_ec)):
        fn = C.fuente('extrabold', int(round(72 * pul)))
        d.text((x, cy), str(val), font=fn, fill=col + (255,), anchor=anc)
    return L


def ficha_img(cx, k_color):
    """pastilla «LADRILLOS» de 46 px colgada del borde inferior de la placa (y 396–446): blanca en EN CONTRA, celeste en
    A FAVOR (k_color 0 → 1 en el viaje), texto #141414."""
    fl = layout()['fl']
    col = tuple(int(round(a + (b - a) * k_color)) for a, b in zip(C.BLANCO, C.CELESTE))
    tw = fl.getlength('LADRILLOS'); pw, ph = int(tw + 44), 50
    L = C.lienzo(); d = ImageDraw.Draw(L)
    x = int(round(cx - pw / 2)); y = 396
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=25, fill=col + (255,))
    d.text((cx, y + ph / 2 + 1), 'LADRILLOS', font=fl, fill=C.TINTA + (255,), anchor='mm')
    return L


def fin_img():
    fl = layout()['fl']; cx = layout()['cx_ec']
    tw = fl.getlength('FIN DEL CAP. 1'); pw, ph = int(tw + 44), 50
    L = C.lienzo(); d = ImageDraw.Draw(L)
    x = int(round(cx - pw / 2)); y = 396
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=25, fill=C.TINTA + (255,), outline=C.BLANCO + (255,), width=3)
    d.text((cx, y + ph / 2 + 1), 'FIN DEL CAP. 1', font=fl, fill=C.BLANCO + (255,), anchor='mm')
    return L


def var_img():
    """capa VAR: marco (esquinas) centrado x 140–940, y 230–1530; rótulo «● VAR»; dos líneas al 15 % fuera de las remeras."""
    L = C.lienzo(); d = ImageDraw.Draw(L)
    x0, y0, x1, y1, lg = 144, 230, 936, 1530, 70          # trazo de 6 px: queda dentro de x ≤ 940
    col = (255, 255, 255, 200)
    for (xa, ya, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(xa, ya), (xa + sx * lg, ya)], fill=col, width=6); d.line([(xa, ya), (xa, ya + sy * lg)], fill=col, width=6)
    for y in (700, 1450):
        d.line([(x0, y), (x1, y)], fill=(255, 255, 255, 38), width=3)
    f = C.fuente('semibold', 46)
    tw = f.getlength('VAR'); px, py = 172, 1440
    d.rounded_rectangle([px, py - 30, px + tw + 92, py + 30], radius=30, fill=C.TINTA + (230,))
    d.ellipse([px + 20, py - 11, px + 42, py + 11], fill=C.CELESTE + (255,))
    d.text((px + 60, py + 1), 'VAR', font=f, fill=C.BLANCO + (255,), anchor='lm')
    return L


def capa_img(clave, hacer):
    return M.img(('capa',) + tuple(clave), hacer)


def dibujos(n, hook):
    ds = []
    # línea de serie / hook (Dato 46 · y 228): rótulo del marcador, pegado a su placa de y 300. Una caja negra de 105 px
    # se montaría sobre el marcador (y la del hook A mide 1070 px): queda con halo, más denso (0,75), como rótulo de interfaz
    if n <= 35 or n >= 375:
        ds.append(M.dato_en(SERIE, 228, size=46, halo=0.75))
    elif n <= 59:
        ds.append(M.dato_en(HOOK[hook][1], 228, size=46, halo=0.75))
    # marcador
    af, ec, cambio = puntos_en(n)
    pa = pe = 1.0
    if cambio and 0 <= n - cambio[0] < 4:
        s = [1.30, 1.20, 1.10, 1.04][n - cambio[0]]
        pa = s if cambio[1] else 1.0; pe = s if cambio[2] else 1.0
    alfa = 1.0
    if 225 <= n <= 254 and ((n - 225) // 6) % 2 == 1:
        alfa = 0.40                                   # plano 9: el marcador titila cada 6 c (sigue encendido)
    ds.append(D(('marcador', af, ec, pa, pe), capa_img(('marcador', af, ec, pa, pe), lambda: marcador_img(af, ec, pa, pe)),
                0, x=0, alfa=alfa))
    # ficha LADRILLOS
    if n >= FICHA_ON:
        lay = layout()
        k = _ease((n - VIAJE[0]) / (VIAJE[1] - VIAJE[0])) if n >= VIAJE[0] else 0.0
        cx = round(lay['cx_ec'] + (lay['cx_af'] - lay['cx_ec']) * k, 1)
        fa = alfa
        if n in (FICHA_ON, FICHA_ON + 1):
            fa = (0.45, 0.8)[n - FICHA_ON]            # se enciende
        if 255 <= n <= 299 and ((n - 255) // 6) % 2 == 1:
            fa = 0.30                                 # plano 10: la ficha titila en EN CONTRA
        ds.append(D(('ficha', cx, round(k, 3)), capa_img(('ficha', cx, round(k, 3)), lambda: ficha_img(cx, k)), 0, x=0, alfa=fa))
    if n >= 375:
        ds.append(D(('fin',), capa_img(('fin',), fin_img), 0, x=0))
    if 255 <= n <= 299:
        ds.append(D(('var',), capa_img(('var',), var_img), 0, x=0))
    # hook caja (c0–c35, pop c0)
    if n <= 35:
        ds.append(M.caja_en(HOOK[hook][0], 440, 76, 'blanca', escala=M.escala_pop(n, 0)))
    for n0, n1, tipo, txt, y, op in TEXTOS:
        if not (n0 <= n <= n1):
            continue
        esc = M.escala_pop(n, n0) if op.get('pop') else 1.0
        k_sal = n1 - n                                # fundido de salida en los últimos `salida` cuadros
        alfa = 1.0 if k_sal >= op.get('salida', 0) else (k_sal + 1) / (op['salida'] + 1)
        if tipo == 'placa':
            ds.append(M.placa_en(txt, y, size=op.get('size', 88), halo=op.get('halo', 0.55), escala=esc, alfa=alfa,
                                 interlineado=op.get('interlineado', 1.05)))
        elif tipo == 'dato':
            ds.append(M.dato_en(txt, y, size=op.get('size', 48)))
        elif tipo == 'datoC':                         # dato sobre fondo claro: caja negra 50 (criterio de la tanda)
            ds.append(M.dato_caja_en(txt, y, alfa=alfa))
        elif tipo == 'caja':
            ds.append(M.caja_en(txt, y, 76, 'blanca', escala=esc))
        elif tipo == 'cajaN':
            ds.append(M.caja_en(txt, y, 76, 'negra', escala=esc))
    return ds


def etapa_capa():
    rep = {}
    for hook in ('A', 'B'):
        reg, unicos = M.escribir_capa(NF, lambda n: dibujos(n, hook), T / f'capa_{hook}')
        rep[hook] = dict(unicos=unicos, registro=reg)
        print(hook, 'cuadros únicos', unicos, flush=True)
    # zona segura: cajas de textos (no se cuentan marcador, ficha, VAR: gráficas dentro de 220–1540 por construcción)
    malas = []
    for hook in ('A', 'B'):
        for r in rep[hook]['registro']:
            for c in r['cajas']:
                if C.fuera_de_zona([c]):
                    malas.append((hook, r['cuadro'], c))
    rep['fuera_de_zona'] = malas
    M.jdump(rep, T / 'capa.json')
    print('fuera de zona (incluye márgenes transparentes del PNG):', len(malas))


# =====================================================================================================
# audio (§MC-01 Sonido; música TEMP propia 120 BPM La menor; foley PROVISORIO; ambiente real)
# =====================================================================================================
from sonido import Mezcla, filt, db as dB, SR      # noqa: E402


def amb(m, toma, src0, t0, t1, g, hp=None, lp=None, atenuar=(), fi=0.012, ff=0.012):
    """ambiente real de la toma con curva de ganancia (rampas de 30 ms en las atenuaciones)."""
    a = m.leer(toma)
    n = int(round((t1 - t0) * SR)); s0 = int(round(src0 * SR))
    seg = a[s0:s0 + n].copy()
    if len(seg) < n:
        seg = np.concatenate([seg, np.zeros(n - len(seg))])
    if hp: seg = filt(seg, 'high', hp)
    if lp: seg = filt(seg, 'low', lp)
    gc = np.full(n, dB(g))
    tt = t0 + np.arange(n) / SR
    for a0, a1, dd in atenuar:
        k = np.clip(np.minimum((tt - (a0 - 0.03)) / 0.03, ((a1 + 0.03) - tt) / 0.03), 0, 1)
        gc *= 1 - (1 - dB(dd)) * k
    r = np.ones(n); k1, k2 = int(fi * SR), int(ff * SR)
    if k1: r[:k1] = np.linspace(0, 1, k1)
    if k2: r[-k2:] = np.minimum(r[-k2:], np.linspace(1, 0, k2))
    m.put('amb', seg * gc * r, t0)
    m.log(t0, f'ambiente {toma} fuente {src0:.3f}–{src0 + t1 - t0:.3f} s, {g:+.1f} dB' + (f', atenuado {atenuar}' if atenuar else ''))


def ambientes(m):
    amb(m, 'IMG_7887', 0.0, 0.0, 2.0, -4, atenuar=[(1.45, 1.60, -12)], fi=0.0)          # planos 1–2 (ola) + ráfaga
    amb(m, 'IMG_8008', 41 / 30, 2.0, 2.8, -8, hp=200)                                  # plano 3
    amb(m, 'IMG_7887', 2.70, 2.8, 3.8, -6, atenuar=[(2.98, 3.15, -12)], ff=0.06)       # plano 4 (ráfaga 2,88–3,05)
    # plano 5 (3453): sin audio útil (−56 dBFS) → solo foley
    amb(m, 'IMG_7824', 4.80, 4.7, 5.7, -8, hp=150, fi=0.04)                            # plano 6
    amb(m, 'IMG_7894', 0.30, 5.7, 6.6, -6)                                             # plano 7
    amb(m, 'IMG_4641', 1.20, 6.6, 7.5, -8)                                             # plano 8
    amb(m, 'IMG_4641', 2.10, 7.5, 8.5, -14, lp=2500, ff=0.08)                          # plano 9 (falso final)
    # plano 10 (VAR): sin ambiente
    amb(m, 'IMG_7885', 3.10, 10.0, 11.5, -6, fi=0.06)                                  # plano 11
    amb(m, 'IMG_4631', 2.40, 11.5, DUR, -6, ff=0.45)                                   # planos 12–13 (ola real 12,10)


def tic(m, n, favor):
    t = n / FPS
    if favor:
        m.toque(t, .22, 2400); m.palma(t, .15)          # palma va a 'mus': en la mezcla sin música se usa tic_sm
    else:
        m.toque(t, .22, 650); m.bombo(t, .30, f0=90, f1=50, dec=.15, pista='fx')
    m.log(t, f'tic {"A FAVOR" if favor else "EN CONTRA"} c{n}')


def tic_sm(m, n, favor):
    """tic del marcador para la mezcla sin música: mismo toque; la palma (a favor) se reemplaza por un golpe en 'fx'."""
    t = n / FPS
    if favor:
        m.toque(t, .22, 2400); m.toque(t + 0.004, .10, 3600)
    else:
        m.toque(t, .22, 650); m.bombo(t, .30, f0=90, f1=50, dec=.15, pista='fx')
    m.log(t, f'tic {"A FAVOR" if favor else "EN CONTRA"} c{n}')


def foley_interfaz(m, sin_musica=False):
    m.obturador(0.50, .40)                                     # celular arriba (7887 0,4–0,6)
    m.barrido(1.20, .30, .16)                                  # corte al acercamiento
    m.tela(3.85, .35, .16)                                     # dedos sobre el relieve
    m.tela(4.75, .35, .14)                                     # la Negra viene a cámara
    f = tic_sm if sin_musica else tic
    for c, a, e in PUNTOS[1:-1]:
        f(m, c, favor=(a > e) or (c in (66, 120, 147)))
    m.toque(8.30, .25, 3100); m.toque(8.42, .25, 3100); m.log(8.30, 'pitazo provisorio')
    m.toque(8.60, .20, 1760); m.toque(8.75, .20, 1760); m.log(8.60, 'bips VAR')
    m.barrido(10.62, .28, .14)                                 # la ficha viaja (c315–c323)
    f(m, 323, favor=True)                                      # 4–3
    m.toque(14.10, .18, 2400); m.log(14.10, 'toque CTA c423')


def musica(m):
    for t in np.arange(0.0, 7.5 - 1e-6, 0.25):
        m.charles(round(float(t), 3), .08 if (t * 4) % 2 else .10)
    m.pad(0.0, [45, 48, 52], 7.5, .05, 1000)
    m.campana(0.0, 76, .06)                                    # campana c0
    for t in (1.2, 2.0, 2.8, 3.8, 4.7, 5.7, 6.6):
        m.bombo(t, .7)
    for t in (2.0, 3.8, 5.7):
        m.ocho08(t, 33, .8, .5)
    m.subida(5.7, 7.4, .14)
    # falso final: latidos (sin música)
    for t in (7.8, 8.3):
        m.bombo(t, .55, f0=70, f1=42, dec=.12, pista='fx'); m.bombo(t + .16, .35, f0=65, f1=40, dec=.10, pista='fx')
        m.log(t, 'latido')
    # VAR
    m.pad(8.5, [40, 43, 47], 1.5, .06, 900)
    m.redoble(9.3, 10.0, .10)
    # drop 10,5 (la ficha empieza a viajar)
    m.bombo(10.5, 1.0); m.impacto(10.5, .55)
    m.ocho08(10.5, 33, 1.2, .6, glide_desde=40)
    m.pad(10.5, [45, 48, 52, 57], 2.0, .07)
    # groove hasta 15,0
    for t in np.arange(10.5, 15.0 - 1e-6, 0.25):
        m.charles(round(float(t), 3), .07)
    for t in (11.0, 11.5, 12.5, 13.0, 13.5, 14.0, 14.5):
        m.bombo(t, .55)
    m.bombo(12.10, .9)                                         # con el golpe real de la ola (fuente 3,0)
    for t in (11.0, 12.0, 13.0, 14.0):
        m.palma(t, .26)
    m.pad(12.5, [41, 45, 48, 53], 1.0, .06); m.ocho08(12.5, 29, .9, .5)
    m.pad(13.5, [48, 52, 55], 0.5, .06); m.ocho08(13.5, 36, .45, .5)
    m.pad(14.0, [43, 47, 50, 55], 1.4, .06); m.ocho08(14.0, 31, .9, .5)
    m.campana(13.30, 76, .07)                                  # ¿ME BANCÁS? (c399)
    m.silenciar('mus', 7.5, 8.5)
    m.fundido('mus', 14.9, DUR)
    m.fundido('fx', 15.05, DUR)


def etapa_audio():
    A.mkdir(parents=True, exist_ok=True)
    niveles = {k: round(M.rms_fuente(*v), 1) for k, v in {
        '7887_0.0': ('IMG_7887', 0.0, 1.4), '8008_1.37': ('IMG_8008', 41 / 30, 0.8, 200), '7887_2.7': ('IMG_7887', 3.1, 0.6),
        '7824_4.8': ('IMG_7824', 4.8, 1.0, 150), '7894_0.3': ('IMG_7894', 0.3, 0.9), '4641_1.2': ('IMG_4641', 1.2, 0.9),
        '4641_2.1': ('IMG_4641', 2.1, 1.0), '7885_3.1': ('IMG_7885', 3.1, 1.5), '4631_2.4': ('IMG_4631', 2.4, 1.0),
        '4631_3.4': ('IMG_4631', 3.4, 2.9), '3453': ('IMG_3453', 3.3, 0.9)}.items()}
    print('RMS fuente (dBFS):', niveles, flush=True)
    m = Mezcla(DUR); ambientes(m); foley_interfaz(m); musica(m)
    r1 = M.exportar(m, A / 'mc01_completa.wav')
    s = Mezcla(DUR); ambientes(s); foley_interfaz(s, sin_musica=True)
    s.fundido('amb', 14.95, DUR)
    r2 = M.exportar(s, A / 'mc01_sinmusica.wav', g_pistas={'fx': -3}, comp=M.COMP_SM)
    r1['limitador'] = M.reduccion_limitador(A / 'mc01_completa.wav', r1)
    r2['limitador'] = M.reduccion_limitador(A / 'mc01_sinmusica.wav', r2)
    M.jdump(dict(rms_fuente=niveles, completa=r1, sinmusica=r2), A / 'audio.json')
    print('completa', r1, '\nsin música', r2)


# =====================================================================================================
# máster
# =====================================================================================================
def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    for k in ('A', 'B'):
        out = MAS / NOMBRES[k]
        if out.exists():
            out.unlink()               # intermedio de trabajo no entregado
        print(M.master_ui(T / 'mc01_base.mp4', T / f'capa_{k}', A / 'mc01_completa.wav', out, NF,
                          video_cache=MAS / f'_video_{k}.mp4'))
        print('->', out, flush=True)
    out = MAS / NOMBRES['SINMUSICA']
    if out.exists():
        out.unlink()
    M.sin_musica(MAS / NOMBRES['A'], A / 'mc01_sinmusica.wav', out)
    print('->', out)


# =====================================================================================================
# control
# =====================================================================================================
TRAMOS = [('1 apuesta 7887', 0.0, 1.2), ('2 tengo 19', 1.2, 2.0), ('3 parche', 2.0, 2.8), ('4 ladrillos', 2.8, 3.8),
          ('5 relieve 3453', 3.8, 4.7), ('6 tono sobre tono', 4.7, 5.7), ('7 en paralelo', 5.7, 6.6), ('8 el mar', 6.6, 7.5),
          ('9 falso final', 7.5, 8.5), ('10 VAR', 8.5, 10.0), ('11 giro 7885', 10.0, 11.5), ('12 Roccé también', 11.5, 12.5),
          ('13 CTA', 12.5, DUR), ('último 0,5 s', DUR - 0.5, DUR)]
PRUEBA_ROPA = {'03': range(60, 84), '05': range(114, 141), '06': range(141, 171), '11': range(300, 345)}
# contactos del detector revisados a tamaño real (rev/contactos.jpg, rev/c60_zoom.jpg): no son estampado
FALSOS_POSITIVOS = {**{n: 'falso positivo: granos de arena mojada y sombra de pliegue en el hombro de la Blanca '
                          '(8008), unos 160 px por encima de ROCCÉ' for n in range(60, 65)},
                    **{n: 'falso positivo: pelusa e hilos blancos sobre la Negra (macro 3453) debajo del marcador; '
                          'el relieve está más abajo' for n in range(114, 141)}}
# zona de las prendas por plano (a mano, sobre las hojas de reglas y los cuadros del máster): (c0, c1, caja c0, caja c1)
ROI_PRENDAS = [
    (0, 35, (0, 760, 1080, 1320), (0, 760, 1080, 1320)),
    (36, 59, (0, 880, 1080, 1520), (0, 880, 1080, 1520)),
    (60, 83, (0, 440, 1080, 1920), (0, 440, 1080, 1920)),
    (84, 113, (0, 720, 1080, 1500), (0, 720, 1080, 1500)),
    (114, 140, (0, 0, 1080, 1920), (0, 0, 1080, 1920)),
    (141, 170, (0, 380, 1080, 1750), (0, 380, 1080, 1750)),
    (171, 197, (0, 640, 1080, 1150), (0, 640, 1080, 1150)),
    (198, 254, (0, 560, 1080, 1450), (0, 560, 1080, 1450)),
    (255, 299, (0, 720, 1080, 1500), (0, 720, 1080, 1500)),
    (300, 344, (0, 430, 1080, 1700), (0, 430, 1080, 1700)),
    (345, 461, (0, 940, 1080, 1650), (0, 940, 1080, 1650)),
]


def etapa_control():
    if EVID.exists():
        shutil.rmtree(EVID)                       # evidencia local (aún no entregada): se rehace entera
    EVID.mkdir(parents=True)
    rep = dict(fecha='2026-11-25', archivos={})
    for k, nombre in NOMBRES.items():
        f = MAS / nombre
        rep['archivos'][k] = M.ficha(f)
        rep['archivos'][k]['niveles'] = M.niveles(f, TRAMOS)
        r = rep['archivos'][k]
        r['audio_igual_video'] = abs(r['video']['duracion'] - r['audio']['duracion']) < 0.5 / FPS + 0.022
        print(k, r['video'], r['audio'], r['sonoridad'], r['md5_video'], r['md5_audio'], flush=True)
    rep['sinmusica_mismo_video_que_A'] = rep['archivos']['SINMUSICA']['md5_video'] == rep['archivos']['A']['md5_video']
    for k in ('A', 'SINMUSICA'):
        M.jdump(M.momentanea(MAS / NOMBRES[k]), EVID / f'sonoridad_momentanea_{k}.json')
    fA, fB = MAS / NOMBRES['A'], MAS / NOMBRES['B']
    # cuadros: c0, antes/después de cada corte, giro (c315–c323), CTA, último
    ns = {0, NF - 1, 315, 319, 323, 330, 399, 423} | {c + d for c in CORTES for d in (-1, 0)}
    M.cuadros(fA, ns, EVID / 'cuadros_A')
    M.cuadros(fB, {0, 20, 35, 36, 50, 59, 60}, EVID / 'cuadros_B')
    for c in CORTES:
        M.tira([EVID / 'cuadros_A' / f'c{c - 1:03d}.jpg', EVID / 'cuadros_A' / f'c{c:03d}.jpg'], [f'c{c - 1}', f'c{c}'],
               EVID / 'cuadros_A' / f'corte_c{c:03d}.jpg')
    M.hoja_cada(fA, EVID / 'hoja_A_cada_0.5s.jpg', cada=15)
    M.hoja_cada(fB, EVID / 'hoja_B_cada_0.5s.jpg', cada=15)
    M.vista_360(fA, [0, 20, 40, 70, 100, 125, 155, 185, 210, 240, 270, 320, 360, 390, 410, 440, 461], EVID / 'vista_360_A.jpg')
    M.vista_360(fB, [0, 20, 40], EVID / 'vista_360_B_hook.jpg', cols=3)
    # marcador: estado por cuadro (registro de la capa) en los cuadros de control
    capa = json.load(open(T / 'capa.json'))
    est = {}
    for c in [0, 41, 42, 65, 66, 89, 90, 119, 120, 146, 147, 176, 177, 203, 204, 322, 323, 461]:
        e = [x for x in capa['A']['registro'][c]['elementos']]
        est[c] = dict(puntos=puntos_en(c)[:2], elementos=e)
    rep['marcador'] = dict(secuencia_guion=PUNTOS, por_cuadro=est)
    rep['zona_segura_pixeles_visibles'] = {k: M.zona_visible(T / f'capa_{k}') for k in ('A', 'B')}
    M.cuadros(fA, [41, 42, 65, 66, 89, 90, 119, 120, 146, 147, 176, 177, 203, 204, 322, 323], EVID / 'marcador')
    # texto vs estampado: TODOS los cuadros (A; B en c0–c59, lo único que cambia), estampado detectado dentro de la zona
    # de prendas de cada plano (ROI_PRENDAS); contactos revisados uno por uno a tamaño real (FALSOS_POSITIVOS)
    ch = M.choque_roi(T / 'mc01_base.mp4', T / 'capa_A', list(range(NF)), ROI_PRENDAS)
    chB = M.choque_roi(T / 'mc01_base.mp4', T / 'capa_B', list(range(60)), ROI_PRENDAS)
    malos = {n: dict(v, revision=FALSOS_POSITIVOS.get(n, 'SIN REVISAR')) for n, v in ch.items() if v['pix'] > 0}
    dist = sorted((v['dist_px'], n) for n, v in ch.items() if v['dist_px'] is not None and v['pix'] == 0)[:8]
    rep['texto_vs_estampado'] = dict(metodo='mc0102_util.estampado_roi + choque_roi (contacto = interfaz alfa > 60 a '
                                            'menos de 12 px del estampado)', cuadros_revisados_A=len(ch),
                                     cuadros_revisados_B=len(chB), contactos_A=malos,
                                     contactos_B={n: v for n, v in chB.items() if v['pix'] > 0},
                                     distancia_minima_sin_contacto_px=dist,
                                     contactos_reales=[n for n, v in malos.items() if v['revision'] == 'SIN REVISAR'])
    base = M.leer_rgb(T / 'mc01_base.mp4', 0, NF - 1)
    (EVID / 'estampado').mkdir(exist_ok=True)
    for n in (20, 62, 100, 117, 128, 160, 168, 185, 210, 270, 318, 336, 338, 339, 344, 400, 430):
        M.vista_roi(base[n], T / 'capa_A', n, M.roi_en(ROI_PRENDAS, n), EVID / 'estampado' / f'c{n:03d}.jpg', 'MC-01 A')
    # VAR: cámara lenta sin cuadros repetidos (diferencia entre cuadros consecutivos del plano 10 en la base)
    dif = [float(np.abs(base[n].astype(np.int16) - base[n - 1].astype(np.int16)).mean()) for n in range(256, 300)]
    rep['var_lento'] = dict(dif_media_consecutivos_min=round(min(dif), 3), max=round(max(dif), 3),
                            cuadros_identicos=[255 + i + 1 for i, d in enumerate(dif) if d < 0.05])
    M.cuadros(T / 'mc01_base.mp4', [262, 263, 264, 265], EVID / 'var_tamano_real', prefijo='base_c')
    # color de la Blanca y la Negra en el máster (sin interfaz: base)
    col = {}
    # Blanca: tabla por plano en la tela lisa (L > 170, sat < 0,15), antes/después, con el celeste de «Founders Privée»
    rep['blanca_tabla'] = M.tabla_blanca({**BLANCA, **MEDIR_SOLO}, T / 'mc01_base.mp4', T / 'planos.json',
                                         EVID / 'blanca_medicion_por_plano.jpg', 'MC-01')
    for nom, n, caja in (('negra_3453_c125', 125, (100, 200, 1000, 700)), ('negra_7824_c160', 160, (150, 1250, 900, 1500)),
                         ('negra_7887_c100', 100, (700, 1350, 1000, 1500))):
        x0, y0, x1, y1 = caja; q = base[n][y0:y1, x0:x1].reshape(-1, 3).astype(float)
        Lq = q @ [.2126, .7152, .0722]; q = q[Lq <= np.percentile(Lq, 50)]; md = q.mean(0)
        col[nom] = dict(rgb=[round(x, 1) for x in md], r_menos_b=round(md[0] - md[2], 1), nota='marrón si R − B > +6')
    rep['color'] = col
    pj = json.load(open(T / 'planos.json'))
    rep['blanca_neutralizada'] = {k: dict({kk: vv for kk, vv in v.items() if kk != 'control'}, control=v.get('control', [])[:4])
                                  for k, v in pj['blanca'].items()}
    rep['negra_neutralizada'] = {k: dict(franjas=v['franjas'], objetivo=v['objetivo'], control=v['control'][:4])
                                 for k, v in pj.get('negra', {}).items()}
    for k in pj.get('negra', {}):                  # antes / después a tamaño real (tela, letras y dedos)
        a0 = M.leer_rgb(P / f'{k}_sin_neutralizar.mp4', 11, 11)[0]; a1 = M.leer_rgb(P / f'{k}.mp4', 11, 11)[0]
        im = Image.new('RGB', (1200, 1000))
        for i, fr in enumerate((a0, a1)):
            im.paste(Image.fromarray(fr).crop((150, 1000, 750, 1500)), (600 * i, 0))
            im.paste(Image.fromarray(fr).resize((540, 960)).crop((0, 0, 540, 500)), (600 * i + 30, 500))
        im.save(EVID / f'negra_plano{k}_antes_despues.jpg', quality=90)
    for f in HJ.glob('*.jpg'):
        shutil.copy2(f, EVID / f'hoja_fuente_{f.name}')
    shutil.copy2(A / 'audio.json', EVID / 'audio.json')
    for k in ('completa', 'sinmusica'):
        shutil.copy2(A / f'mc01_{k}_eventos.json', EVID / f'audio_eventos_{k}.json')
    shutil.copy2(T / 'planos.json', EVID / 'planos.json')
    M.jdump(rep, EVID / 'control.json')
    print(json.dumps({k: v for k, v in rep.items() if k not in ('archivos',)}, ensure_ascii=False, default=str)[:4000])


def etapa_revision():
    """sin recalcular el resto del control: vuelve a rotular los contactos con FALSOS_POSITIVOS y rehace la tabla de la
    Blanca (columna «neutralizada» = la regla se aplicó; «antes» solo donde se aplicó)."""
    rep = json.load(open(EVID / 'control.json'))
    t = rep['texto_vs_estampado']
    for n, v in t['contactos_A'].items():
        v['revision'] = FALSOS_POSITIVOS.get(int(n), 'SIN REVISAR')
    t['contactos_reales'] = [int(n) for n, v in t['contactos_A'].items() if v['revision'] == 'SIN REVISAR']
    print('contactos B (hook B, c0–c59):', sorted(int(n) for n in t['contactos_B']))
    rep['blanca_tabla'] = M.tabla_blanca({**BLANCA, **MEDIR_SOLO}, T / 'mc01_base.mp4', T / 'planos.json',
                                         EVID / 'blanca_medicion_por_plano.jpg', 'MC-01')
    M.jdump(rep, EVID / 'control.json')
    print('contactos sin revisar:', t['contactos_reales'])
    for r in rep['blanca_tabla']:
        print(r['plano'], r['neutralizada'], r['b_menos_r_antes'], r['b_menos_r_master'], r['cumple'])


def etapa_entregar():
    r = M.entregar(list(NOMBRES.values()), PIEZA, EVID, MAS)
    M.jdump(r, T / 'entrega.json')
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    {'hojas': etapa_hojas, 'planos': etapa_planos, 'capa': etapa_capa, 'audio': etapa_audio, 'master': etapa_master,
     'control': etapa_control, 'revision': etapa_revision, 'entregar': etapa_entregar}[sys.argv[1]]()
