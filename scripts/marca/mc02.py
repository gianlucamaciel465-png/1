#!/usr/bin/env python3
"""MARCA · MC-02 «Respuesta a "me comí alto anuncio"» · receta de los másteres v01 (Pedro A, 25/11/2026).

Guion aprobado: piezas/MARCA_comunidad/04_fede_guiones_G1.md §0, §MC-02, §8 + condiciones 06_roma_aprobacion_G1.md
(hook B solo en MC-01 y MC-03: MC-02 sale solo con el hook A) + especificación 05_especificacion_comun.md.
Interfaz con los estilos de scripts/marca/comun.py (sin modificar) vía mc0102_util.py.

Etapas (python de TRABAJO/venv, cada una por separado):
  hojas   → hojas cada 0,1 s de 4625 0,4–2,8 (y las de reglas ya hechas en TRABAJO/marca/MC-02/hojas)
  planos  → 11 planos (color de video.py) + Blanca neutralizada donde sale fría (8008, 7999, 8002) + unión (495 c)
  capa    → interfaz por cuadro (burbuja, medidor ANUNCIO %, flecha, textos, caja tipeada)
  audio   → mezcla completa y sin música (−14 LUFS, pico ≤ −1 dBTP)
  master  → máster y _SINMUSICA (mismo flujo de video)
  control → evidencia_v01/
  entregar→ EXPORTACIONES/ + carpeta de la pieza
"""
import json, math, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, '/home/user/1/scripts/marca')
import mc0102_util as M          # noqa: E402
from mc0102_util import V, U, C, D, W, H, FPS   # noqa: E402
from mc01 import amb, cuadro_de, _ease          # noqa: E402  (mismas utilidades de ambiente y conformado)

R = Path('/home/user/1')
T = R / 'TRABAJO/marca/MC-02'
HJ, P, A, MAS, EVID = T / 'hojas', T / 'planos', T / 'audio', T / 'master', T / 'evidencia_v01'
PIEZA = Path('/mnt/project-files/piezas/MARCA_comunidad/MC-02_alto_anuncio')
NF = 495
DUR = NF / FPS                       # 16,500 s
REUSAR = '--rehacer' not in sys.argv
NOMBRES = {'A': 'ROCCE_MC02_ME_COMI_ALTO_ANUNCIO_v01.mp4', 'SINMUSICA': 'ROCCE_MC02_ME_COMI_ALTO_ANUNCIO_SINMUSICA_v01.mp4'}


def etapa_hojas():
    HJ.mkdir(parents=True, exist_ok=True)
    U.hoja_src('IMG_4625', 12, 84, HJ / '4625_0.4-2.8_c3.jpg', cada=3, ancho=180, cols=10)


# =====================================================================================================
# planos
# =====================================================================================================
# Plano 3 · 8008: en los cuadros 5–11 de la fuente (0,167–0,367 s) la R de ROCCÉ pasa por debajo del medidor
# (y 365–415) y de la burbuja (236–350) → texto sobre el estampado en c72–c77. Se arranca en el cuadro 12 (la R ya
# está debajo de y 435) y los 6 cuadros que faltan se ganan con una rampa SOLO en el tramo casi quieto 18–27 (la mano
# sostiene la remera): 12–18 a 1,0 · 18→27 a 0,5625 · 28–40 a 1,0. La cámara se mueve 20–40 px por cuadro en ese tramo
# (correlación de fase, control): la mezcla lineal dejaba letras dobles en ROCCÉ (revisado a tamaño real en c84–c89),
# así que los 16 cuadros intermedios salen de minterpolate con compensación de movimiento (mci); los enteros son reales.
RAMPA3 = list(range(0, 7)) + [6 + 9 * k / 16 for k in range(1, 17)] + list(range(16, 29))
assert len(RAMPA3) == 36


# Blanca por plano (criterio común de la tanda, 25/11): caja de la remera a mano (mitad de cada plano, rev/mids_grid.jpg);
# neutralizar_blanca la mide en la tela lisa (L > 170, sat < 0,15) y la lleva a B−R ≤ +8 solo si pasa de +12.
BLANCA = {'02': ((150, 790, 710, 1110), '7887: la Blanca en la roca'),
          '03': ((0, 380, 1080, 1920), '8008: espalda en arena mojada'),
          '04': ((0, 690, 830, 1610), '7999: la remera en el aire, movida'),
          '05': ((180, 830, 1075, 1545), '8002: en la baranda, cielo azul'),
          '06': ((240, 980, 850, 1430), '7884: en la roca, el chico saca la foto'),
          '07': ((0, 690, 1080, 1920), '4530: espalda sostenida'),
          '08': ((0, 710, 950, 1570), '4625: en la roca'),
          '09': ((0, 710, 1010, 1720), '4625: acercamiento 1,00 → 1,10'),
          '10': ((260, 690, 810, 1090), '7885: en la roca, el chico de espaldas'),
          '11': ((0, 760, 1080, 1900), '4531: de frente al viento')}


def plan():
    bc = lambda k: BLANCA[k][0]
    n7 = cuadro_de('IMG_4530', 1.50); n8 = cuadro_de('IMG_4625', 0.40); n11 = cuadro_de('IMG_4531', 3.50)
    return [
        dict(id='01', m0=0, tipo='n', toma='IMG_7824', n0=cuadro_de('IMG_7824', 0.0), nf=54),
        dict(id='02', m0=54, tipo='n', toma='IMG_7887', n0=60, nf=18, blanca=bc('02')),
        dict(id='03', m0=72, tipo='pos', toma='IMG_8008', n0=12, n_src=29, pos=RAMPA3, mci=(6, 15, 16),
             blanca=bc('03')),
        dict(id='04', m0=108, tipo='n', toma='IMG_7999', n0=45, nf=36, blanca=bc('04')),
        # 8002 cambia de B−R +29 a +22 en dos cuadros (fuente 12–14): ganancias con suavizado corto (sigma 1)
        dict(id='05', m0=144, tipo='n', toma='IMG_8002', n0=0, nf=36, blanca=bc('05'), sigma=1.0),
        dict(id='06', m0=180, tipo='n', toma='IMG_7884', n0=30, nf=36, blanca=bc('06')),
        dict(id='07', m0=216, tipo='n', toma='IMG_4530', n0=n7, nf=36, blanca=bc('07')),
        dict(id='08', m0=252, tipo='n', toma='IMG_4625', n0=n8, nf=36, blanca=bc('08')),
        # «la cámara se acerca a vender»: acercamiento real 1,00 → 1,10 centrado en el estampado (x 480, y 900)
        dict(id='09', m0=288, tipo='z', toma='IMG_4625', n0=n8 + 36, zs=[1.0 + 0.10 * k / 35 for k in range(36)],
             cx=480, cy=900, blanca=bc('09')),
        dict(id='10', m0=324, tipo='n', toma='IMG_7885', n0=30, nf=54, blanca=bc('10')),
        dict(id='11', m0=378, tipo='n', toma='IMG_4531', n0=n11, nf=117, blanca=bc('11')),
    ]


def etapa_planos():
    P.mkdir(parents=True, exist_ok=True)
    reg, colores = [], {}
    for p in plan():
        out = P / f"{p['id']}.mp4"
        crudo = P / f"{p['id']}_sin_neutralizar.mp4"
        hecho = crudo if p.get('blanca') else out
        reusar = hecho.exists() and hecho.with_suffix('.json').exists() and REUSAR
        if reusar:
            r = json.load(open(hecho.with_suffix('.json')))
        elif p['tipo'] == 'n':
            r = M.plano(p['toma'], p['n0'], p['nf'], out)
        elif p['tipo'] == 'z':
            r = M.plano_z(p['toma'], p['n0'], p['zs'], p['cx'], p['cy'], out)
        else:
            r = M.plano_pos(p['toma'], p['n0'], p['n_src'], p['pos'], out, tramo_mci=p.get('mci'))
        if not reusar:
            r = {k: v for k, v in r.items() if k != 'ventanas'}
            if p.get('blanca'):
                shutil.move(out, crudo); r['salida'] = str(crudo)
            M.jdump(r, hecho.with_suffix('.json'))
        if p.get('blanca'):
            colores[p['id']] = M.neutralizar_blanca(crudo, out, p['blanca'], sigma=p.get('sigma', 3.0))
            r = dict(r, salida=str(out))
        r.update(id=p['id'], m0=p['m0'])
        assert M.contar(out) == r['cuadros'], (p['id'], M.contar(out), r['cuadros'])
        reg.append(r); print(p['id'], p['toma'], r['cuadros'], flush=True)
    n = M.unir(reg, T / 'mc02_base.mp4')
    assert n == NF, n
    M.jdump(dict(cuadros=n, planos=reg, blanca=colores), T / 'planos.json')
    print('total', n)


# =====================================================================================================
# interfaz
# =====================================================================================================
CORTES = [54, 72, 108, 144, 180, 216, 252, 288, 324, 378]
# medidor ANUNCIO %: (cuadro, valor) — serie exacta del guion / Roma
MEDIDOR = [(0, 0), (30, 10), (60, 0), (78, 40), (114, 20), (150, 60), (186, 35), (222, 75), (258, 95), (300, 99)]
CUENTA = {324: 83, 325: 66, 326: 50, 327: 33, 328: 17, 329: 0}      # giro: 99 → 0 % en c324–c329
MED = (120, 365, 820, 50)                                          # x, y, ancho, alto (barra 820×50, x 120–940)
BURBUJA_Y = 236
TIPEO = ('Y ahora, lo que', 'estabas esperando:')                  # 15 + espacio + 18 = 34 caracteres, c288–c321
TIPEO_C0, TIPEO_X, TIPEO_Y = 288, 140, 430

TEXTOS = [
    (54, 71, 'placa', 'EL MODELO: YO.', 430, {}),
    (54, 71, 'datoC', 'Gianluca, fundador de Roccé', 540, {}),
    # caja negra de 105 px dentro de y ≤ 1540: placa 1380 → 1350 y dato 1480 → 1432 (bordes visibles 1366–1422 y 1432–1537)
    (72, 107, 'placa', 'MIRÁ ESTE DETALLE:', 1350, dict(size=76, x=60)),
    (72, 107, 'datoC', 'Founders Privée, en celeste', 1432, dict(x=60)),
    (108, 143, 'placa', '…Y LA TIRAMOS\nA LA ARENA.', 430, dict(halo=0.75)),
    (144, 179, 'placa', 'PLANO DE CATÁLOGO.', 430, dict(size=80)),
    (144, 179, 'datoC', 'cielo azul y todo', 540, {}),
    (180, 215, 'placa', 'FILMADO CON\nCELULARES.', 430, dict(halo=0.75)),
    (216, 251, 'placa', 'Y LA ESPALDA…', 430, dict(halo=0.75)),
    (216, 251, 'datoC', 'ROCCÉ + Founders Privée', 540, {}),
    (252, 287, 'serif', 'Founders Privée', 430, dict(size=96, halo=0.75)),
    (324, 377, 'cajaN', 'SIN LINK. SIN PRECIO.\nSIN “COMPRÁ YA”.', 430, dict(pop=True)),
    (378, 419, 'placa', 'Aquel video sí era\nun anuncio.', 430, dict(size=80, halo=0.75)),
    (390, 419, 'placa', 'Tenías razón.', 650, dict(pop=True, halo=0.75)),
    (420, 494, 'caja', 'Preguntame lo que\nquieras de Roccé:\nte respondo con video.', 430, dict(pop=True)),
]
HOOK = ('Si esto llega a 100 %,\ntenés razón.', 430, 9, 53)          # texto, y, pop c9, hasta c53


def medidor_en(n):
    """(valor del número, valor del relleno, cuadro del último cambio, relleno blanco)."""
    if n >= 329:
        return 0, 0.0, 329 if n < 333 else None, False
    if n >= 324:
        return CUENTA[n], float(CUENTA[n]), None, False
    v0 = v = 0; c_ult = 0
    for c, val in MEDIDOR:
        if n >= c:
            v0, v, c_ult = v, val, c
    k = _ease((n - c_ult + 1) / 4) if c_ult > 0 else 1.0
    fill = v0 + (v - v0) * k
    blanco = 258 <= n <= 323 and ((n - 258) // 4) % 2 == 1
    return v, round(fill, 2), c_ult if c_ult > 0 else None, blanco


def burbuja_img():
    """tarjeta de comentario con el estilo de comun.burbuja (radio 28, sombra, SemiBold 52 #141414, rótulo Medium gris
    0,62 × 52 px), con el alto ajustado a la tinta para entrar en y 236–350 del guion (comun.burbuja mide 181 px)."""
    f1, f2 = C.fuente('semibold', 52), C.fuente('medium', 32)
    com, et = 'me comí alto anuncio', 'Comentario en TikTok'
    padx, pady, gap = 34, 18, 14
    b1, b2 = f1.getbbox(com), f2.getbbox(et)
    Wc = int(round(max(f1.getlength(com), f2.getlength(et)) + 2 * padx))
    Hc = pady + (b2[3] - b2[1]) + gap + (b1[3] - b1[1]) + pady
    im = Image.new('RGBA', (Wc + 24, Hc + 24), (0, 0, 0, 0))
    sh = Image.new('L', im.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle([12, 16, 12 + Wc, 16 + Hc], radius=28, fill=110)
    im.putalpha(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([12, 12, 12 + Wc, 12 + Hc], radius=28, fill=C.BLANCO + (255,))
    d.text((12 + padx, 12 + pady - b2[1]), et, font=f2, fill=(120, 120, 124, 255))
    d.text((12 + padx, 12 + pady + (b2[3] - b2[1]) + gap - b1[1]), com, font=f1, fill=C.TINTA + (255,))
    return im


def medidor_img(fill, num, blanco=False, pulso=1.0):
    """barra 820×50 #141414 al 85 % (radio 25), relleno celeste de marca (blanco al titilar), «ANUNCIO» SemiBold 46 a la
    izquierda y «NN %» ExtraBold 46 a la derecha; el texto va blanco sobre lo oscuro y #141414 sobre el relleno."""
    _, _, w, h = MED
    forma = Image.new('L', (w, h), 0); ImageDraw.Draw(forma).rounded_rectangle([0, 0, w - 1, h - 1], radius=25, fill=255)
    im = Image.new('RGBA', (w, h), C.TINTA + (0,)); im.putalpha(forma.point(lambda v: v * 217 // 255))
    corte = Image.new('L', (w, h), 0)
    fw = w * fill / 100
    if fw > 0.5:
        ImageDraw.Draw(corte).rectangle([0, 0, fw, h], fill=255)
    rel = ImageChops.multiply(forma, corte)
    capa = Image.new('RGBA', (w, h), (C.BLANCO if blanco else C.CELESTE) + (255,)); capa.putalpha(rel)
    im = Image.alpha_composite(im, capa)
    txt = Image.new('L', (w, h), 0); dt = ImageDraw.Draw(txt)
    dt.text((24, h / 2 + 1), 'ANUNCIO', font=C.fuente('semibold', 46), fill=255, anchor='lm')
    dt.text((w - 24, h / 2 + 1), f'{num} %', font=C.fuente('extrabold', int(round(46 * pulso))), fill=255, anchor='rm')
    bl = Image.new('RGBA', (w, h), C.BLANCO + (255,)); bl.putalpha(ImageChops.multiply(txt, ImageChops.invert(rel)))
    os_ = Image.new('RGBA', (w, h), C.TINTA + (255,)); os_.putalpha(ImageChops.multiply(txt, rel))
    return Image.alpha_composite(Image.alpha_composite(im, bl), os_)


def flecha_img():
    """flecha blanca con halo (estilo placa) desde el costado derecho de la caja del hook hasta el porcentaje."""
    L = Image.new('L', (W, H), 0); d = ImageDraw.Draw(L)
    p0, p1, p2 = np.array([1004., 662.]), np.array([1014., 474.]), np.array([950., 426.])
    pts = [tuple((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2) for t in np.linspace(0, 1, 40)]
    d.line(pts, fill=255, width=8, joint='curve')
    tg = p2 - p1; tg /= np.linalg.norm(tg)
    for s in (1, -1):
        a = math.radians(28 * s); rot = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
        q = p2 - 34 * (rot @ tg)
        d.line([tuple(p2), tuple(q)], fill=255, width=8)
    for q in (p0, p2):
        d.ellipse([q[0] - 4, q[1] - 4, q[0] + 4, q[1] + 4], fill=255)
    halo = L.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.6))
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); im.putalpha(halo)
    capa = Image.new('RGBA', (W, H), C.BLANCO + (0,)); capa.putalpha(L)
    return Image.alpha_composite(im, capa)


def tipeo_img(k, cursor=True):
    """caja tipeada (estilo comun.caja: SemiBold 76, caja blanca por renglón, radio 20, pad 30/18, interlineado 1,12),
    alineada a la izquierda en x 140, con k caracteres de «Y ahora, lo que estabas esperando:» y cursor #141414."""
    fnt = C.fuente('semibold', 76); pad = (30, 18); radio = 20
    asc, desc = fnt.getmetrics(); alto_r = int(round((asc + desc) * 1.12))
    l1, l2 = TIPEO
    if k <= len(l1):
        rs = [l1[:k]]
    else:
        rs = [l1, l2[:max(0, k - len(l1) - 1)]]
    cur_w, cur_gap = 6, 6
    anchos = [fnt.getlength(r) for r in rs]
    Wc = int(max(fnt.getlength(l1), fnt.getlength(l2)) + 2 * pad[0] + cur_w + cur_gap + 4)
    Hc = alto_r * 2 + 2 * pad[1]
    im = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, a in enumerate(anchos):
        extra = (cur_w + cur_gap) if (cursor and i == len(rs) - 1) else 0
        d.rounded_rectangle([0, i * alto_r, a + 2 * pad[0] + extra, i * alto_r + alto_r + 2 * pad[1]], radius=radio,
                            fill=C.BLANCO + (255,))
    for i, r in enumerate(rs):
        d.text((pad[0], i * alto_r + pad[1] + (alto_r - (asc + desc)) / 2), r, font=fnt, fill=C.TINTA + (255,))
    if cursor:
        i = len(rs) - 1; x = pad[0] + anchos[i] + cur_gap
        y0 = i * alto_r + pad[1] + (alto_r - (asc + desc)) / 2 + asc * 0.18; y1 = i * alto_r + pad[1] + (alto_r - (asc + desc)) / 2 + asc + desc * 0.15
        d.rectangle([x, y0, x + cur_w - 1, y1], fill=C.TINTA + (255,))
    return im


def dibujos(n):
    ds = []
    # burbuja (todo el video; pop c0)
    ds.append(D(('burbuja',), M.img(('burbuja',), burbuja_img), BURBUJA_Y - 12, escala=M.escala_pop(n, 0)))
    # medidor
    num, fill, c_ult, blanco = medidor_en(n)
    pul = 1.0
    if c_ult is not None and 0 <= n - c_ult < 4:
        pul = [1.20, 1.12, 1.06, 1.02][n - c_ult]
    clave = ('medidor', num, fill, blanco, pul)
    ds.append(D(clave, M.img(clave, lambda: medidor_img(fill, num, blanco, pul)), MED[1], x=MED[0]))
    # hook A + flecha al medidor
    txt, y, c_pop, c_fin = HOOK
    if c_pop <= n <= c_fin:
        ds.append(M.caja_en(txt, y, 76, 'blanca', escala=M.escala_pop(n, c_pop)))
        if n >= c_pop + 2:
            ds.append(D(('flecha',), M.img(('flecha',), flecha_img), 0, x=0))
    # caja tipeada
    if TIPEO_C0 <= n <= 323:
        k = min(34, n - TIPEO_C0 + 1)
        cur = True if k < 34 else ((n - TIPEO_C0 - 33) // 4) % 2 == 0
        clave = ('tipeo', k, cur)
        ds.append(D(clave, M.img(clave, lambda: tipeo_img(k, cur)), TIPEO_Y, x=TIPEO_X))
    for n0, n1, tipo, t, y, op in TEXTOS:
        if not (n0 <= n <= n1):
            continue
        esc = M.escala_pop(n, n0) if op.get('pop') else 1.0
        if tipo == 'placa':
            ds.append(M.placa_en(t, y, size=op.get('size', 88), halo=op.get('halo', 0.55), x=op.get('x'), escala=esc))
        elif tipo == 'dato':
            ds.append(M.dato_en(t, y, size=op.get('size', 48), halo=op.get('halo', 0.6), x=op.get('x')))
        elif tipo == 'datoC':                         # dato sobre fondo claro: caja negra 50 (criterio de la tanda)
            ds.append(M.dato_caja_en(t, y, x=op.get('x')))
        elif tipo == 'serif':
            ds.append(M.serif_en(t, y, size=op.get('size', 96), halo=op.get('halo', 0.6)))
        elif tipo == 'caja':
            ds.append(M.caja_en(t, y, 76, 'blanca', escala=esc))
        elif tipo == 'cajaN':
            ds.append(M.caja_en(t, y, 76, 'negra', escala=esc))
    return ds


def etapa_capa():
    reg, unicos = M.escribir_capa(NF, dibujos, T / 'capa_A')
    zona = M.zona_visible(T / 'capa_A')
    M.jdump(dict(unicos=unicos, registro=reg, fuera_de_zona=zona), T / 'capa.json')
    print('cuadros únicos', unicos, '· fuera de zona (píxeles visibles):', len(zona), zona[:3])


# =====================================================================================================
# audio (§MC-02 Sonido; música TEMP propia 100 BPM Re menor → Re mayor en el giro; foley PROVISORIO; ambiente real)
# =====================================================================================================
from sonido import Mezcla      # noqa: E402


def ambientes(m):
    amb(m, 'IMG_7824', 0.0, 0.0, 1.8, -8, hp=150, fi=0.0)                 # 1 (balcón, viento)
    amb(m, 'IMG_7887', 2.00, 1.8, 2.4, -6)                                # 2
    amb(m, 'IMG_8008', 0.167, 2.4, 3.6, -8, hp=200)                       # 3 (sonido continuo; la imagen tiene rampa)
    amb(m, 'IMG_7999', 1.50, 3.6, 4.8, -6, hp=200)                        # 4
    amb(m, 'IMG_8002', 0.00, 4.8, 6.0, -6)                                # 5
    amb(m, 'IMG_7884', 1.00, 6.0, 7.2, -6)                                # 6
    amb(m, 'IMG_4530', 1.50, 7.2, 8.4, -8)                                # 7
    amb(m, 'IMG_4625', 0.40, 8.4, 9.6, -10)                               # 8
    amb(m, 'IMG_4625', 1.60, 9.6, 10.8, -12)                              # 9 (solo tecleo y ambiente)
    amb(m, 'IMG_7885', 1.00, 10.8, 12.6, -8, fi=0.02)                     # 10
    amb(m, 'IMG_4531', 3.50, 12.6, DUR, -8, ff=0.5)                       # 11 (nada antes de 3,50: sin la conversación)


def campana_fx(m, t, nota, g):
    """campana de alarma como interfaz (pista fx: queda también en la mezcla sin música)."""
    tmp = Mezcla(1.6); tmp.campana(0.0, nota, g)
    m.put('fx', tmp.pistas['mus'], t); m.log(t, f'alarma campana {nota}')


def foley_interfaz(m):
    m.toque(0.0, .22, 1900); m.toque(0.01, .10, 3800); m.log(0.0, 'pop burbuja c0')
    m.toque(0.30, .16, 2600); m.log(0.30, 'pop hook c9')
    prev = 0
    for c, v in MEDIDOR[1:]:
        t = c / FPS - 0.2
        if v > prev:
            m.subida(t, t + .25, .10); m.toque(t + .2, .18, 2600); m.log(t + .2, f'medidor sube a {v} % (c{c})')
        else:
            m.barrido(t, .25, .14, sube=False); m.toque(t + .2, .18, 600); m.log(t + .2, f'medidor baja a {v} % (c{c})')
        prev = v
    m.tela(4.05, .30, .18); m.tela(4.40, .25, .12); m.log(4.05, 'tela del tiro / caída (7999 c60, c70)')
    m.obturador(6.40, .40)
    for t in (8.60, 8.80, 9.00):
        campana_fx(m, t, 88, .06)
    for c in range(TIPEO_C0, TIPEO_C0 + 34):
        m.toque(c / FPS, .05, 4200)
    m.log(TIPEO_C0 / FPS, 'tecleo: 34 toques c288–c321')
    m.barrido(10.80 + .15, .25, .16, sube=False); m.impacto(10.80, .55); m.toque(329 / FPS, .18, 600)
    m.log(10.80, 'giro: impacto + barrido de bajada; 0 % en c329')
    m.toque(390 / FPS, .14, 2400); m.log(390 / FPS, 'pop «Tenías razón.» c390')


def musica(m):
    m.pad(0.0, [50, 53, 57], 9.6, .045, 1200)
    for t in np.arange(0.0, 9.6 - 1e-6, 0.3):
        m.charles(round(float(t), 3), .09 if round(t / 0.3) % 2 else .11)
    for t in (1.8, 2.4, 3.6, 4.8, 6.0, 7.2, 8.4):
        m.bombo(t, .7); m.ocho08(t, 38, .5)
    m.silenciar('mus', 9.6, 10.8)
    # giro / drop en Re mayor
    m.bombo(10.8, 1.0); m.ocho08(10.8, 38, 1.0, .6, glide_desde=45)
    m.pad(10.8, [50, 54, 57, 62], 1.8, .07)
    for t in np.arange(10.8, 16.5 - 1e-6, 0.3):
        m.charles(round(float(t), 3), .07)
    for t in np.arange(11.4, 16.3, 0.6):
        m.bombo(round(float(t), 3), .55)
    for t in (11.4, 12.6, 13.8, 15.0, 16.2):
        m.palma(t, .24)
    m.pad(12.6, [43, 47, 50, 55], 1.2, .06); m.ocho08(12.6, 31, .9, .5)
    m.pad(13.8, [45, 49, 52, 57], 1.2, .06); m.ocho08(13.8, 33, .9, .5)
    m.pad(15.0, [50, 54, 57, 62], 1.5, .06); m.ocho08(15.0, 38, 1.2, .5)
    m.campana(14.00, 74, .07); m.log(14.0, 'campana CTA c420')
    m.fundido('mus', 16.0, DUR); m.fundido('bombo', 16.0, DUR)


def etapa_audio():
    A.mkdir(parents=True, exist_ok=True)
    niveles = {k: round(M.rms_fuente(*v), 1) for k, v in {
        '7824_0.0': ('IMG_7824', 0.0, 1.8, 150), '7887_2.0': ('IMG_7887', 2.0, 0.6), '8008_0.17': ('IMG_8008', 0.167, 1.2, 200),
        '7999_1.5': ('IMG_7999', 1.5, 1.2, 200), '8002_0.0': ('IMG_8002', 0.0, 1.2), '7884_1.0': ('IMG_7884', 1.0, 1.2),
        '4530_1.5': ('IMG_4530', 1.5, 1.2), '4625_0.4': ('IMG_4625', 0.4, 2.4), '7885_1.0': ('IMG_7885', 1.0, 1.8),
        '4531_0.0-3.4 (fuera)': ('IMG_4531', 0.0, 3.4), '4531_3.5': ('IMG_4531', 3.5, 3.9)}.items()}
    print('RMS fuente (dBFS):', niveles, flush=True)
    m = Mezcla(DUR); ambientes(m); foley_interfaz(m); musica(m)
    r1 = M.exportar(m, A / 'mc02_completa.wav')
    s = Mezcla(DUR); ambientes(s); foley_interfaz(s)
    s.fundido('amb', 16.0, DUR)
    r2 = M.exportar(s, A / 'mc02_sinmusica.wav', g_pistas={'fx': -3}, comp=M.COMP_SM)
    r1['limitador'] = M.reduccion_limitador(A / 'mc02_completa.wav', r1)
    r2['limitador'] = M.reduccion_limitador(A / 'mc02_sinmusica.wav', r2)
    M.jdump(dict(rms_fuente=niveles, completa=r1, sinmusica=r2), A / 'audio.json')
    print('completa', r1, '\nsin música', r2)


# =====================================================================================================
# máster
# =====================================================================================================
def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    out = MAS / NOMBRES['A']
    if out.exists():
        out.unlink()
    print(M.master_ui(T / 'mc02_base.mp4', T / 'capa_A', A / 'mc02_completa.wav', out, NF, video_cache=MAS / '_video_A.mp4'))
    print('->', out, flush=True)
    out = MAS / NOMBRES['SINMUSICA']
    if out.exists():
        out.unlink()
    M.sin_musica(MAS / NOMBRES['A'], A / 'mc02_sinmusica.wav', out)
    print('->', out)


# =====================================================================================================
# control
# =====================================================================================================
TRAMOS = [('1 apuesta 7824', 0.0, 1.8), ('2 el modelo: yo', 1.8, 2.4), ('3 mirá este detalle', 2.4, 3.6),
          ('4 la tiramos', 3.6, 4.8), ('5 catálogo', 4.8, 6.0), ('6 celulares', 6.0, 7.2), ('7 la espalda', 7.2, 8.4),
          ('8 Founders Privée', 8.4, 9.6), ('9 tecleo (sin música)', 9.6, 10.8), ('10 giro', 10.8, 12.6),
          ('11 reenganche + CTA', 12.6, DUR), ('último 0,5 s', DUR - 0.5, DUR)]
PRUEBA_ROPA = {'03': range(72, 108), '07': range(216, 252), '08': range(252, 288)}
# zona de las prendas por plano (a mano, sobre las hojas de reglas y los cuadros de la base): (c0, c1, caja c0, caja c1)
ROI_PRENDAS = [
    (0, 53, (0, 600, 1080, 1800), (0, 600, 1080, 1800)),
    (54, 71, (0, 750, 1080, 1500), (0, 750, 1080, 1500)),
    (72, 107, (0, 380, 1080, 1920), (0, 380, 1080, 1920)),
    (108, 143, (0, 600, 1080, 1920), (0, 600, 1080, 1920)),
    (144, 179, (0, 820, 1080, 1920), (0, 820, 1080, 1920)),
    (180, 215, (0, 900, 1080, 1700), (0, 900, 1080, 1700)),
    (216, 251, (0, 600, 1080, 1920), (0, 600, 1080, 1920)),
    (252, 323, (0, 650, 1080, 1700), (0, 650, 1080, 1700)),
    (324, 377, (0, 650, 1080, 1500), (0, 650, 1080, 1500)),
    (378, 494, (0, 620, 1080, 1920), (0, 620, 1080, 1920)),
]
FALSOS_POSITIVOS = {
    **{n: 'falso positivo: sombra del borde de la manga y granos de arena en el hombro de la Blanca (8008) bajo el '
          'medidor; la R de ROCCÉ empieza unos 60 px más abajo' for n in range(72, 75)},
    **{n: 'falso positivo: borde de la sombra proyectada de quien graba sobre la Blanca (8008); «Founders Privée» '
          'queda arriba a la derecha, fuera del texto' for n in range(75, 93)},
    103: 'falso positivo: grano de arena oscuro en la tela, debajo del dato; el trazo de «Privée» queda a más de 30 px',
    **{n: 'falso positivo: sombra azulada de un pliegue y de quien graba sobre la tela lisa de la Blanca (8008), bajo '
          'la placa y la caja negra; «Privée» y su rúbrica quedan a la derecha, a más de 60 px (revisado a tamaño real '
          'en rev/contactos_v01d)' for n in (102, 106, 107)},
    **{n: 'falso positivo: kiosco celeste de la playa al fondo (4530), detrás del borde inferior de la caja «ROCCÉ + '
          'Founders Privée»; la prenda empieza en y ≈ 690 y su estampado más abajo (revisado a tamaño real en '
          'rev/contactos_v01d)' for n in range(216, 237)},
    **{n: 'falso positivo: kiosco celeste de la playa al fondo (4531), detrás de la mano; la prenda y su estampado '
          'quedan más abajo' for n in range(420, 495)},
}


def desplazamiento(a, b):
    """traslación (px) entre dos cuadros por correlación de fase sobre la luminancia a 1/4."""
    ga = a[::4, ::4].astype(np.float32) @ np.float32([.2126, .7152, .0722]); gb = b[::4, ::4].astype(np.float32) @ np.float32([.2126, .7152, .0722])
    ga -= ga.mean(); gb -= gb.mean()
    Fa, Fb = np.fft.fft2(ga), np.fft.fft2(gb)
    r = np.fft.ifft2(Fa * np.conj(Fb) / (np.abs(Fa * np.conj(Fb)) + 1e-6)).real
    y, x = np.unravel_index(np.argmax(r), r.shape)
    y = y - r.shape[0] if y > r.shape[0] // 2 else y; x = x - r.shape[1] if x > r.shape[1] // 2 else x
    return round(float(math.hypot(x, y) * 4), 1)


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
    for k in NOMBRES:
        M.jdump(M.momentanea(MAS / NOMBRES[k]), EVID / f'sonoridad_momentanea_{k}.json')
    fA = MAS / NOMBRES['A']
    ns = {0, 9, 11, 30, 33, 300, 321, 323, 324, 325, 326, 327, 328, 329, 390, 392, 420, 422, NF - 1} | \
         {c + d for c in CORTES for d in (-1, 0)}
    M.cuadros(fA, ns, EVID / 'cuadros_A')
    for c in CORTES:
        M.tira([EVID / 'cuadros_A' / f'c{c - 1:03d}.jpg', EVID / 'cuadros_A' / f'c{c:03d}.jpg'], [f'c{c - 1}', f'c{c}'],
               EVID / 'cuadros_A' / f'corte_c{c:03d}.jpg')
    M.tira([EVID / 'cuadros_A' / f'c{c:03d}.jpg' for c in range(323, 330)], [f'c{c}' for c in range(323, 330)],
           EVID / 'cuadros_A' / 'giro_c323-c329.jpg', ancho=300)
    M.hoja_cada(fA, EVID / 'hoja_A_cada_0.5s.jpg', cada=15)
    M.vista_360(fA, [0, 12, 40, 60, 90, 125, 160, 195, 230, 270, 300, 320, 330, 360, 400, 440, 494], EVID / 'vista_360_A.jpg')
    # medidor: valor por cuadro en los cuadros del guion (y su vecino anterior)
    capa = json.load(open(T / 'capa.json'))
    med = {}
    for c in [0, 29, 30, 59, 60, 77, 78, 113, 114, 149, 150, 185, 186, 221, 222, 257, 258, 299, 300, 323, 324, 325, 326,
              327, 328, 329, 494]:
        num, fill, _, bl = medidor_en(c)
        med[c] = dict(numero=num, relleno=fill, relleno_blanco=bl)
    rep['medidor'] = dict(serie_guion=MEDIDOR, cuenta_giro=CUENTA, por_cuadro=med)
    M.cuadros(fA, [29, 30, 59, 60, 77, 78, 113, 114, 149, 150, 185, 186, 221, 222, 257, 258, 299, 300], EVID / 'medidor')
    rep['burbuja_en_todos_los_cuadros'] = all('burbuja' in ' '.join(r['elementos']) for r in capa['registro'])
    # texto vs estampado: TODOS los cuadros, estampado detectado dentro de la zona de prendas de cada plano
    # (ROI_PRENDAS); contactos revisados uno por uno a tamaño real (FALSOS_POSITIVOS)
    ch = M.choque_roi(T / 'mc02_base.mp4', T / 'capa_A', list(range(NF)), ROI_PRENDAS)
    malos = {n: dict(v, revision=FALSOS_POSITIVOS.get(n, 'SIN REVISAR')) for n, v in ch.items() if v['pix'] > 0}
    dist = sorted((v['dist_px'], n) for n, v in ch.items() if v['dist_px'] is not None and v['pix'] == 0)[:8]
    rep['texto_vs_estampado'] = dict(metodo='mc0102_util.estampado_roi + choque_roi (contacto = interfaz alfa > 60 a '
                                            'menos de 12 px del estampado)', cuadros_revisados=len(ch), contactos=malos,
                                     distancia_minima_sin_contacto_px=dist,
                                     contactos_reales=[n for n, v in malos.items() if v['revision'] == 'SIN REVISAR'])
    rep['zona_segura_pixeles_visibles'] = M.zona_visible(T / 'capa_A')
    base = M.leer_rgb(T / 'mc02_base.mp4', 0, NF - 1)
    (EVID / 'estampado').mkdir(exist_ok=True)
    for n in (9, 30, 60, 72, 75, 78, 90, 106, 125, 160, 175, 200, 230, 270, 300, 322, 330, 360, 395, 425, 480):
        M.vista_roi(base[n], T / 'capa_A', n, M.roi_en(ROI_PRENDAS, n), EVID / 'estampado' / f'c{n:03d}.jpg', 'MC-02')
    # plano 3: rampa en el tramo casi quieto (desplazamiento entre cuadros de la fuente 18–27 = máster c78–c95)
    src = M._decode_1080('IMG_8008', 12, 29)
    rgb = [M.yuv_rgb(s[0], s[1], s[2]).clip(0, 255) for s in src]
    rep['plano3_rampa'] = dict(
        posiciones_fuente=[round(12 + p, 4) for p in RAMPA3],
        origen=json.load(open(P / '03_sin_neutralizar.json')).get('origen'),
        desplazamiento_px_fuente=[dict(de=12 + i, a=13 + i, px=desplazamiento(rgb[i], rgb[i + 1])) for i in range(28)],
        dif_media_consecutivos_master=[round(float(np.abs(base[n].astype(np.int16) - base[n - 1].astype(np.int16)).mean()), 2)
                                       for n in range(73, 108)])
    M.cuadros(T / 'mc02_base.mp4', [84, 85, 86, 87, 89], EVID / 'plano3_interpolado_tamano_real', prefijo='base_c')
    ims = [Image.fromarray(base[n]).crop((480, 380, 980, 1080)) for n in (78, 84, 86, 89, 94)]
    tira = Image.new('RGB', (2500, 700))
    for i, im in enumerate(ims):
        tira.paste(im, (500 * i, 0))
    tira.save(EVID / 'plano3_ROCCE_tamano_real_c78_84_86_89_94.jpg', quality=92)
    # color de la Blanca y la Negra (base, sin interfaz)
    col = {}
    # Blanca: tabla por plano en la tela lisa (L > 170, sat < 0,15), antes/después, con el celeste de «Founders Privée»
    rep['blanca_tabla'] = M.tabla_blanca(BLANCA, T / 'mc02_base.mp4', T / 'planos.json',
                                         EVID / 'blanca_medicion_por_plano.jpg', 'MC-02')
    for nom, n, caja in (('negra_7824_c30', 30, (100, 500, 1000, 1500)), ('negra_7887_c60', 60, (500, 1000, 1000, 1500))):
        x0, y0, x1, y1 = caja; q = base[n][y0:y1, x0:x1].reshape(-1, 3).astype(float)
        Lq = q @ [.2126, .7152, .0722]; q = q[Lq <= np.percentile(Lq, 30)]; md = q.mean(0)
        col[nom] = dict(rgb=[round(x, 1) for x in md], r_menos_b=round(md[0] - md[2], 1), nota='marrón si R − B > +6')
    rep['color'] = col
    pj = json.load(open(T / 'planos.json'))
    rep['blanca_neutralizada'] = {k: dict({kk: vv for kk, vv in v.items() if kk != 'control'}, control=v.get('control', [])[:4])
                                  for k, v in pj['blanca'].items()}
    for f in HJ.glob('*.jpg'):
        shutil.copy2(f, EVID / f'hoja_fuente_{f.name}')
    shutil.copy2(A / 'audio.json', EVID / 'audio.json')
    for k in ('completa', 'sinmusica'):
        shutil.copy2(A / f'mc02_{k}_eventos.json', EVID / f'audio_eventos_{k}.json')
    shutil.copy2(T / 'planos.json', EVID / 'planos.json')
    if (T / 'rev' / 'contactos_v01d').exists():          # vistas a tamaño real de los contactos revisados
        shutil.copytree(T / 'rev' / 'contactos_v01d', EVID / 'estampado' / 'contactos_revisados', dirs_exist_ok=True)
    M.jdump(rep, EVID / 'control.json')
    print(json.dumps({k: v for k, v in rep.items() if k not in ('archivos',)}, ensure_ascii=False, default=str)[:4000])


def etapa_revision():
    """vuelve a rotular los contactos de control.json con FALSOS_POSITIVOS (sin recalcular nada) y suma a la evidencia
    las vistas a tamaño real de esa revisión."""
    rep = json.load(open(EVID / 'control.json'))
    t = rep['texto_vs_estampado']
    for n, v in t['contactos'].items():
        v['revision'] = FALSOS_POSITIVOS.get(int(n), 'SIN REVISAR')
    t['contactos_reales'] = [int(n) for n, v in t['contactos'].items() if v['revision'] == 'SIN REVISAR']
    rep['blanca_tabla'] = M.tabla_blanca(BLANCA, T / 'mc02_base.mp4', T / 'planos.json',
                                         EVID / 'blanca_medicion_por_plano.jpg', 'MC-02')
    rv = T / 'rev' / 'contactos_v01d'
    if rv.exists():
        shutil.copytree(rv, EVID / 'estampado' / 'contactos_revisados', dirs_exist_ok=True)
    M.jdump(rep, EVID / 'control.json')
    print('contactos sin revisar:', t['contactos_reales'])


def etapa_entregar():
    r = M.entregar(list(NOMBRES.values()), PIEZA, EVID, MAS)
    M.jdump(r, T / 'entrega.json')
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    {'hojas': etapa_hojas, 'planos': etapa_planos, 'capa': etapa_capa, 'audio': etapa_audio, 'master': etapa_master,
     'control': etapa_control, 'revision': etapa_revision, 'entregar': etapa_entregar}[sys.argv[1]]()
