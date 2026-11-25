#!/usr/bin/env python3
"""MARCA · MC-04 «¿Founder 001 o Founder 100?» · receta del máster v01 (Pedro B, 25/11/2026).

Guion: piezas/MARCA_comunidad/04_fede_guiones_G1.md §0, §MC-04 y §8 + 06_roma_aprobacion_G1.md + 05_especificacion_comun.md.
Reutiliza de mc03.py (misma carpeta) la interfaz por cuadro (componer, copiar_video, placa/dato/caja con borde superior
visible, El, capa_rgba), la detección del estampado y los choques, sin cambiarlos. Lo propio de MC-04: la barra de cuota
sin números (pista de 760×20, fichas de 100 px, disco blanco de 40 px), el rodillo de números, la corrección de la Negra
en 3453 y la mezcla.

Etapas: planos → medir → audio → master  (control y entrega: mc_control.py)

v02 (dictamen de Roma 02_roma_dictamen_master_v01.md): mismo montaje, base, tramos, barra y audio. Cambian dos cosas:
  1. Blanca neutra en los planos 3, 4, 7 y 8: corrimiento de croma (misma luma) hasta B−R +8 / G−R +1,5 solo en los
     neutros claros de la tela, con el criterio de Pedro C en 8004 (mc05.delta_neutra / neutralizar: peso por luma y por
     cercanía al croma del blanco medido) más una máscara de la remera (componente mayor dentro de una caja por plano)
     para que no entren cielo, espuma ni arena. Se aplica al componer (sin generación extra de video).
  2. Datos de c12 y c330 en caja negra SemiBold 50 (comun.caja, tema 'negra'), misma y y mismo cuadro de entrada.
Etapa: master_v02  (control: mc_control.py control MC-04 v02; hoja: hoja_v02 MC-04; entrega: entregar MC-04 v02)
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, '/home/user/1/scripts/marca')
import mc03 as M                  # noqa: E402  (también envuelve video.sh con nice y 2 hilos)
V, U, F4, C = M.V, M.U, M.F4, M.C
from sonido import Mezcla, filt, ruido, SR   # noqa: E402

R, W, H, FPS = M.R, M.W, M.H, M.FPS
T = R / 'TRABAJO/marca/MC-04'
P, A, MAS, MED = T / 'planos', T / 'audio', T / 'master', T / 'med'
EVID = T / 'evidencia_v01'
PIEZA = Path('/mnt/project-files/piezas/MARCA_comunidad/MC-04_001_o_100')
NF = 420
DUR = NF / FPS                    # 14,000 s
NOMBRES = {'completa': 'ROCCE_MC04_FOUNDER_001_O_100_v01.mp4', 'sinmusica': 'ROCCE_MC04_FOUNDER_001_O_100_SINMUSICA_v01.mp4'}
NOMBRES_V02 = {'completa': 'ROCCE_MC04_FOUNDER_001_O_100_v02.mp4', 'sinmusica': 'ROCCE_MC04_FOUNDER_001_O_100_SINMUSICA_v02.mp4'}
MAS2 = T / 'master_v02'
CORTES = [45, 75, 120, 150, 195, 240, 285, 330]

# 4631 z 1,15 fijo sobre las remeras: ventana 939×1670 anclada abajo a la derecha (la Negra ya toca el borde derecho:
# así no se corta más de lo que corta la toma)
Z4631 = (141, 250, 939, 1670)
# 7824 z 1,06 anclado arriba (DESVÍO medido: ROCCÉ tono sobre tono empieza en y ≈ 615 en c180 y la barra ocupa y 520–620)
Z7824 = (61, 0, 2038, 3623)
PLANOS = [
    dict(id='1', m0=0, nf=45, tipo='n', toma='IMG_4530', n0=0, caja=None, fuente='0,000–1,468 (29,97 → 30)', funcion='APUESTA + PISTA'),
    dict(id='2', m0=45, nf=30, tipo='negra', toma='IMG_3453', n0=48, fuente='1,600–2,567', funcion='A FAVOR 001'),
    dict(id='3', m0=75, nf=45, tipo='n', toma='IMG_8004', n0=102, caja=None, fuente='3,400–4,867', funcion='A FAVOR 001 · goleada'),
    dict(id='4', m0=120, nf=30, tipo='n', toma='IMG_7996', n0=90, caja=None, fuente='3,000–3,967', funcion='GRAN PREGUNTA'),
    dict(id='5', m0=150, nf=45, tipo='n', toma='IMG_4631', n0=0, caja=Z4631, fuente='0,000–1,467 · z 1,15', funcion='GIRO 1'),
    dict(id='6', m0=195, nf=45, tipo='n', toma='IMG_7824', n0=180, caja=Z7824, fuente='6,001–7,469 (29,97 → 30) · z 1,06', funcion='GIRO 2'),
    dict(id='7', m0=240, nf=45, tipo='n', toma='IMG_7999', n0=0, caja=None, fuente='0,000–1,467', funcion='GIRO 3 · vuelta de tuerca'),
    dict(id='8', m0=285, nf=45, tipo='n', toma='clip_a592f367', n0=0, caja=None, fuente='0,000–1,467', funcion='RESOLUCIÓN'),
    dict(id='9', m0=330, nf=90, tipo='n', toma='IMG_4627', n0=300, caja=None, fuente='10,000–12,967', funcion='REENGANCHE + CTA'),
]


# =====================================================================================================
# 3453 · Negra carbón (condición 5 de Roma: «la Negra nunca marrón»)
# =====================================================================================================
LN0, LN1 = 70.0, 130.0            # el corrimiento de croma se aplica entero en L < 70 y se apaga hasta L 130


def _ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def plano_negra(toma, n0, nf, salida):
    """video.color (HLG + corrección de TOMAS de 3453) y después, solo en los oscuros, se resta la croma media de la tela
    negra lisa (L < 60, mediana de los nf cuadros): la Negra queda neutra (carbón), el relieve gris claro y la piel no se
    tocan (peso 0 desde L 130). Una sola corrección para todo el plano (sin parpadeo)."""
    src = M.leer_fuente_yuv444(toma, n0, nf)
    cbs, crs = [], []
    for fr in src[::3]:
        L = (fr[0].astype(np.float32) - 16) * 255 / 219
        m = (L < 60) & (L > 8)
        cbs.append(np.median(fr[1][m].astype(np.float32) - 128)); crs.append(np.median(fr[2][m].astype(np.float32) - 128))
    dcb, dcr = float(np.median(cbs)), float(np.median(crs))
    enc = F4._encoder(salida)
    antes, despues = [], []
    for k, fr in enumerate(src):
        L = (fr[0].astype(np.float32) - 16) * 255 / 219
        w = 1 - _ss((L - LN0) / (LN1 - LN0))
        out = fr.copy()
        out[1] = M.u8(fr[1] - w * dcb); out[2] = M.u8(fr[2] - w * dcr)
        if k % 10 == 0:
            for lista, f_ in ((antes, fr), (despues, out)):
                rgb = M.yuv444_rgb(f_[0][::4, ::4], f_[1][::4, ::4], f_[2][::4, ::4])
                Lr = rgb @ np.array([.2126, .7152, .0722], np.float32); m = (Lr < 55) & (Lr > 10)
                q = np.median(rgb[m], 0)
                lista.append(dict(cuadro=n0 + k, rgb=[round(float(v), 1) for v in q], b_menos_r=round(float(q[2] - q[0]), 1),
                                  g_menos_r=round(float(q[1] - q[0]), 1)))
        enc.stdin.write(out.tobytes())
    enc.stdin.close(); enc.wait()
    return dict(toma=toma, n0=n0, cuadros=nf, salida=str(salida), croma_restada=dict(d_cb=round(dcb, 2), d_cr=round(dcr, 2)),
                negra_antes=antes, negra_despues=despues)


def etapa_planos():
    P.mkdir(parents=True, exist_ok=True)
    reg = []
    for p in PLANOS:
        out = P / f"p{p['id']}.mp4"
        if p['tipo'] == 'negra':
            r = plano_negra(p['toma'], p['n0'], p['nf'], out)
        else:
            r = U.plano_n(p['toma'], p['n0'], p['nf'], out, caja=p['caja'])
        r.update({k: v for k, v in p.items() if k not in r})
        assert r['cuadros'] == p['nf'], (p['id'], r['cuadros'])
        reg.append(r); print(p['id'], r['cuadros'], flush=True)
    n = V.unir(reg, T / 'mc04_base.mp4')
    assert n == NF, n
    M.jdump(dict(cuadros=n, planos=reg), T / 'planos.json')


# =====================================================================================================
# barra de cuota (sin números de votos) · §MC-04 «Gráfica»
# =====================================================================================================
X_IZQ, X_DER, R_FICHA, STEP = 160, 920, 50, 100        # fichas de 100 px en los extremos de la pista 760×20; −3 → x 240


def barra(y0, v, izq='001', der='100', est_izq='celeste', est_der='blanca', brillo_izq=0.0, centro_celeste=False):
    """capa de 1080 × 140 con la barra; y0 = borde superior de las fichas. v: posición del disco (−3 … 0)."""
    Hb = 140
    im = Image.new('RGBA', (W, Hb), (0, 0, 0, 0))
    cy = 20 + R_FICHA
    # sombra suave general (legible sobre cielo y espuma)
    sh = Image.new('L', (W, Hb), 0); ds = ImageDraw.Draw(sh)
    ds.rounded_rectangle([X_IZQ, cy - 10, X_DER, cy + 10], radius=10, fill=120)
    for x in (X_IZQ, X_DER):
        ds.ellipse([x - R_FICHA, cy - R_FICHA, x + R_FICHA, cy + R_FICHA], fill=120)
    im.putalpha(sh.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([X_IZQ, cy - 10, X_DER, cy + 10], radius=10, fill=(20, 20, 20, 170), outline=(255, 255, 255, 110), width=2)
    d.rounded_rectangle([538, cy - 20, 542, cy + 20], radius=2, fill=(C.CELESTE if centro_celeste else C.BLANCO) + (255,))
    if brillo_izq > 0:
        g = Image.new('L', (W, Hb), 0)
        ImageDraw.Draw(g).ellipse([X_IZQ - R_FICHA - 10, cy - R_FICHA - 10, X_IZQ + R_FICHA + 10, cy + R_FICHA + 10], fill=255)
        g = g.filter(ImageFilter.GaussianBlur(10)).point(lambda a: int(a * 0.85 * brillo_izq))
        capa = Image.new('RGBA', (W, Hb), C.CELESTE + (0,)); capa.putalpha(g)
        im = Image.alpha_composite(im, capa); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(C.FUENTES / 'InterDisplay-Bold.otf'), 46)
    estilos = {'celeste': (C.CELESTE, C.TINTA), 'blanca': (C.BLANCO, C.TINTA), 'gris': ((112, 116, 122), (205, 205, 205))}
    for x, txt, est in ((X_IZQ, izq, est_izq), (X_DER, der, est_der)):
        fondo, tinta = estilos[est]
        d.ellipse([x - R_FICHA, cy - R_FICHA, x + R_FICHA, cy + R_FICHA], fill=fondo + (255,))
        bx0, by0, bx1, by1 = f.getbbox(txt)
        d.text((x - (bx1 - bx0) / 2 - bx0, cy - (by1 - by0) / 2 - by0), txt, font=f, fill=tinta + (255,))
    xd = 540 + v * STEP
    sd = Image.new('L', (W, Hb), 0)
    ImageDraw.Draw(sd).ellipse([xd - 20, cy - 18, xd + 20, cy + 22], fill=150)
    sdc = Image.new('RGBA', (W, Hb), (0, 0, 0, 0)); sdc.putalpha(sd.filter(ImageFilter.GaussianBlur(4)))
    im = Image.alpha_composite(im, sdc); d = ImageDraw.Draw(im)
    d.ellipse([xd - 20, cy - 20, xd + 20, cy + 20], fill=C.BLANCO + (255,))
    return im, y0 - 20


# valores de la barra (guion): llega a cada valor en el cuadro indicado; el cuadro anterior muestra el 60 % del recorrido
VALORES = [(0, 0.0), (51, -1.0), (81, -3.0), (156, -2.0), (201, -1.0), (268, 0.0)]


def valor_barra(k):
    v = 0.0
    for i, (c, val) in enumerate(VALORES):
        if k >= c:
            v = val
        elif k == c - 1 and i > 0:
            prev = VALORES[i - 1][1]
            return prev + 0.6 * (val - prev)
    return v


def rodillo_der(k):
    """c0–c20: la ficha derecha rueda 001 → 100 (un número por cuadro, con aceleración y frenado)."""
    if k > 20:
        return '100'
    return f'{round(1 + 99 * _ss(k / 20)):03d}'


def rodillo_izq(k):
    """c262–c284: la ficha «001» rueda 002 → 003 → … (igual que la placa «PASA AL 002. AL 003…»); desde c285, 001."""
    if 262 <= k < 266:
        return '002'
    if 266 <= k < 270:
        return '003'
    if 270 <= k < 285:
        return '…'
    return '001'


def estado_barra(k):
    y0 = 600 if k < 45 else 520
    v = valor_barra(k)
    est_der = 'gris' if 126 <= k < 156 else 'blanca'
    est_izq = 'blanca' if k >= 336 else 'celeste'       # plano 9: fichas iguales (c336 = corte + 6)
    brillo = 1.0 if 81 <= k < 156 else 0.0              # c81: la ficha «001» brilla
    if 81 <= k < 84:
        brillo = (k - 80) / 3
    return (y0, round(v, 3), rodillo_izq(k), rodillo_der(k), est_izq, est_der, round(brillo, 2), k >= 291)


_CB = {}


def el_barra(k):
    e = estado_barra(k)
    if e not in _CB:
        y0, v, izq, der, ei, ed, br, cc = e
        im, _ = barra(y0, v, izq, der, ei, ed, br, cc)
        _CB[e] = M.El(im, 0, y0 - 20, (X_IZQ - R_FICHA, y0, X_DER + R_FICHA, y0 + 2 * R_FICHA), 'barra',
                      f'barra v={v} fichas {izq}/{der}')
    return _CB[e], e


def armar_textos(ver='v01'):
    L = []

    def add(el, c0, c1, pop=False):
        L.append(dict(el=el, c0=c0, c1=c1, pop=pop))
    Y = 236
    # mismo halo que MC-03 (más denso que comun.placa por defecto): el cielo de 4530/7824 y la espuma de 4627 dejaban el
    # Dato blanco casi ilegible a 360 px (evidencia_v01/halo_prueba_360px.png)
    HP = dict(halo=0.95, sombra_px=16)
    HD = dict(halo=0.9, sombra_px=12)
    add(M.caja('¿Founder 001\no Founder 100?', 76, Y, interlineado=1.0, pad=(28, 14), nombre='hook_caja'), 0, 44, True)
    if ver == 'v01':
        add(M.dato('Los primeros 100 compradores de Roccé,\nnumerados 001–100.', 46, 470, nombre='hook_dato', **HD), 12, 44)
    else:
        # v02 (dictamen 02, corrección 2): caja negra SemiBold 50, misma y (470) y mismo cuadro de entrada (c12). Relleno
        # compacto 28/14 e interlineado 1,0 (los de la caja del hook): con los de comun.caja (30/18, 1,12) el segundo
        # renglón terminaba en y 644 y tapaba la pista y el disco de la barra (y 630–670)
        add(M.caja('Los primeros 100 compradores de Roccé,\nnumerados 001–100.', 50, 470, tema='negra', interlineado=1.0,
                   pad=(28, 14), nombre='hook_dato'), 12, 44)
    add(M.placa('EL 001 DISEÑA\nUNA PRENDA A SU GUSTO.', 74, Y, **HP), 45, 74)
    add(M.placa('Y SE LLEVA UN PORCENTAJE\nDE LA GANANCIA DE ESA PRENDA.', 57, Y, **HP), 75, 119)
    add(M.caja('¿Y EL 100?', 76, Y, nombre='caja_y_el_100'), 120, 149, True)
    add(M.placa('ATRÁS DICEN LO MISMO.', 78, Y, **HP), 150, 194)
    add(M.placa('LOS 100, EN UN GRUPO PRIVADO\nDE WHATSAPP CON GIANLUCA.', 61, Y, **HP), 195, 239)
    add(M.placa('¿Y SI EL 001 NO\nQUIERE DISEÑAR?', 80, Y, **HP), 240, 261)
    add(M.placa('PASA AL 002. AL 003…', 86, Y, **HP), 262, 284)
    add(M.placa('EL NÚMERO ES EL ORDEN.', 76, Y, **HP), 285, 329)
    add(M.dato('¿QUIÉN ES MÁS FOUNDER?', 48, 450, nombre='rotulo', **HD), 45, 299)
    add(M.dato('Founders son los 100.', 50, 450, nombre='dato_founders', **HD), 300, 329)
    add(M.caja('¿001 o 100?', 76, Y, nombre='cta_caja'), 330, 419, True)
    if ver == 'v01':
        add(M.dato('Comentá cuál y por qué.', 52, 440, nombre='cta_dato', **HD), 330, 419)
    else:
        add(M.caja('Comentá cuál y por qué.', 50, 440, tema='negra', interlineado=1.0, pad=(28, 14), nombre='cta_dato'), 330, 419)
    return L


def ui_mc04(ver='v01'):
    textos = armar_textos(ver)

    def fn(k):
        items, clave = [], []
        b, cb = el_barra(k)
        items.append((b, 1.0, 1.0)); clave.append(('b',) + cb)
        for t in textos:
            if t['c0'] <= k <= t['c1']:
                e = M.POP[k - t['c0']] if t['pop'] and k - t['c0'] < 2 else 1.0
                items.append((t['el'], e, 1.0)); clave.append((t['el'].nombre, t['el'].texto, e))
        return tuple(clave), items
    return fn, textos


ROI_04 = {
    '1': ('blanca', (0, 640, 1080, 1500)), '2': ('negra', (250, 560, 1080, 1920)), '3': ('blanca', (0, 560, 1080, 1700)),
    '4': ('blanca', (0, 700, 1080, 1800)), '5': ('ambas', (0, 850, 1080, 1700)),
    # 6: el ROCCÉ tono sobre tono de la Negra no entra en la máscara de letras claras: caja medida a mano en c195
    # (rejilla de 50 px: tilde de la É en y ≈ 650, «Founders Privée» hasta y ≈ 1206, x 22–950) y seguida por correlación
    # de fase; la Negra se aleja (se achica), así que la caja seguida queda más alta que el estampado real (conservadora)
    '6': ('seguir', dict(k_ref=195, caja=(20, 645, 960, 1210))),
    '7': None, '8': ('blanca', (0, 600, 1080, 1500)), '9': ('blanca', (0, 700, 1080, 1700)),
}


def etapa_medir():
    MED.mkdir(parents=True, exist_ok=True)
    planos = json.load(open(T / 'planos.json'))['planos']
    est = M.medir_estampado(T / 'mc04_base.mp4', planos, ROI_04, NF)
    res = {k: dict(plano=v['plano'], caja=v['caja'], px=v['px']) for k, v in est.items()}
    M.jdump(res, MED / 'estampado.json')
    por = {}
    for k, v in res.items():
        if v['caja']:
            por.setdefault(v['plano'], []).append((k, v['caja'][1]))
    resumen = {p: dict(y_sup_min=min(y for _, y in l), cuadro=min(l, key=lambda t: t[1])[0]) for p, l in por.items()}
    M.jdump(resumen, MED / 'estampado_resumen.json')
    print(json.dumps(resumen, ensure_ascii=False))
    fn, _ = ui_mc04()
    M.dibujar_estampado(T / 'mc04_base.mp4', est, list(range(0, NF, 6)), MED / 'estampado_c0-c419_c6.jpg', ui_fn=fn)


# =====================================================================================================
# sonido
# =====================================================================================================
def barrido_pan(m, t, dur=0.30, g=0.20, sube=True, pan=0.0):
    """Mezcla.barrido con paneo (hacia el 001 = izquierda, hacia el 100 = derecha)."""
    L = int(dur * SR); tt = np.arange(L) / SR; u = tt / tt[-1]
    n = ruido(L); out = np.zeros(L); B = 16
    for b in range(B):
        i0, i1 = b * L // B, (b + 1) * L // B
        x = b / B if sube else 1 - b / B
        fc = 500 * (9000 / 500) ** x
        out[i0:i1] = filt(n, 'band', [fc * 0.6, min(fc * 1.6, 20000)])[i0:i1]
    out *= np.sin(np.pi * u) ** 1.5
    m.put('fx', out / (np.abs(out).max() + 1e-9), t - dur * 0.6, g, pan=pan)
    m.log(t, f'barrido pan {pan:+.1f}')


def mezcla_mc04(salida, musica=True):
    m = Mezcla(DUR)
    am = [('IMG_4530', 0.000, 0.0, 1.5, -8, None, None), ('IMG_4530', 1.500, 1.5, 2.5, -16, None, 3000),
          ('IMG_8004', 3.400, 2.5, 4.0, -8, None, None), ('IMG_7996', 3.000, 4.0, 5.0, -6, 200, None),
          ('IMG_4631', 0.000, 5.0, 6.5, -6, None, None), ('IMG_7824', 6.000, 6.5, 8.0, -8, None, None),
          ('IMG_7999', 0.000, 8.0, 9.5, -6, None, None), ('clip_a592f367', 0.000, 9.5, 11.0, -10, 150, None),
          ('IMG_4627', 10.000, 11.0, DUR, -6, None, None)]
    for toma, s0, t0, t1, g, hp, lp in am:
        m.ambiente(toma, s0, t0, t1, g, hp=hp, lp=lp, fade=0.012, fin_fade=(0.3 if t1 >= DUR - 0.01 else None))
    # interfaz (las dos mezclas): rodillo, barra, fichas
    prev = None
    for k in range(0, 21):
        n = rodillo_der(k)
        if n != prev:
            m.toque(k / FPS, .06, 3000); prev = n
    m.log(0.0, 'rodillo 001 → 100 (un clic por número)')
    for c, val, pan in ((51, -1, -0.5), (81, -3, -0.6), (156, -2, 0.5), (201, -1, 0.5), (268, 0, 0.4)):
        t = c / FPS
        barrido_pan(m, t, .26, .20, sube=(val > -3 and c > 100), pan=pan)
        m.toque(t, .18, 2400 if c > 100 else 1800); m.log(t, f'barra → {val}')
    m.toque(81 / FPS + .05, .12, 3400)                    # brillo de la ficha 001
    m.toque(126 / FPS, .20, 600); m.log(126 / FPS, 'ficha 100 a gris')
    m.toque(156 / FPS + .04, .12, 3000)
    for c in (262, 266, 270):
        m.toque(c / FPS, .10, 3000); m.log(c / FPS, 'rodillo ficha 001')
    m.toque(291 / FPS, .16, 2600); m.log(291 / FPS, 'marca central celeste')
    m.toque(336 / FPS, .14, 2200); m.log(336 / FPS, 'fichas iguales')
    m.subida(8.0, 9.5, .14)
    # sin música, el impacto a la mitad: con −14 LUFS sobre ambiente y foley quedaba 18 dB por encima del resto
    m.impacto(9.5, .6 if musica else .3)
    if musica:
        b = 0.5
        m.pad(0.0, [45, 48, 52], 4.4, .09, 1000)                          # La menor (0,05 → 0,09: c21–c44 medía
        t = 0.0                                                            #  −36 dB RMS, un hueco dentro del hook)
        while t < 4.4 - 1e-6:
            m.charles(t, .11 if int(round(t / .25)) % 2 else .07); t += .25
        for tc in (0.0, 1.5, 2.5, 4.0):
            m.bombo(tc, .7); m.ocho08(tc, 33, .45, .45)
        for tc, g in ((0.5, .3), (1.0, .35)):                              # pulso de la apuesta a 120 BPM
            m.bombo(tc, g)
        m.campana(2.7, 76, .06)
        m.silenciar('mus', 4.4, 5.0)
        m.pad(5.0, [48, 52, 55], 4.5, .05, 1300)                          # Do mayor
        t = 5.0
        while t < 9.5 - 1e-6:
            m.charles(t, .09 if int(round(t / .25)) % 2 else .06); t += .25
        for tc, n_ in ((5.0, 36), (6.5, 41), (8.0, 43)):
            m.bombo(tc, .7); m.ocho08(tc, n_, .45, .45)
        m.bombo(9.5, 1.0); m.ocho08(9.5, 36, 1.2, .6, glide_desde=43)
        m.campana(9.5, 76, .06); m.pad(9.5, [48, 52, 55, 60], 1.5, .07, 1800)
        m.pad(11.0, [48, 52, 55, 60], 2.6, .06, 1800); m.campana(11.0, 79, .07)
        t = 11.0
        while t < DUR - 0.05:
            m.charles(t, .08 if int(round(t / .25)) % 2 else .05); t += .25
        for tc in np.arange(11.0, 13.6, b):
            if int(round((tc - 11.0) / b)) % 2 == 0:
                m.bombo(float(tc), .6)
            else:
                m.palma(float(tc), .22)
        for tc, n_ in ((11.0, 36), (12.0, 43), (13.0, 41)):
            m.ocho08(tc, n_, .9, .45)
        m.fundido('mus', 13.5, DUR)
    return m.exportar(str(salida), lufs=-14)


def etapa_audio():
    A.mkdir(parents=True, exist_ok=True)
    r1, r2 = mezcla_mc04(A / 'mc04_completa.wav', True), mezcla_mc04(A / 'mc04_sinmusica.wav', False)
    q1, q2 = M.asegurar_pico(A / 'mc04_completa.wav'), M.asegurar_pico(A / 'mc04_sinmusica.wav')   # pico verdadero ≤ −1,5
    M.jdump(dict(completa=dict(exportar=r1, final=q1), sinmusica=dict(exportar=r2, final=q2)), A / 'sonoridad_wav.json')
    print('completa', r1, q1, 'sin música', r2, q2)


def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    planos = json.load(open(T / 'planos.json'))['planos']
    est = M.medir_estampado(T / 'mc04_base.mp4', planos, ROI_04, NF)
    fn, textos = ui_mc04()
    reg = M.componer(T / 'mc04_base.mp4', fn, A / 'mc04_completa.wav', MAS / NOMBRES['completa'], NF, choque_fn=M.choques(est))
    print('choques', sum(1 for r in reg if r.get('choque_px', 0) > 0), flush=True)
    M.copiar_video(MAS / NOMBRES['completa'], A / 'mc04_sinmusica.wav', MAS / NOMBRES['sinmusica'])
    M.jdump(reg, MAS / 'registro_cuadros.json')


# =====================================================================================================
# v02 · Blanca neutra en los planos 3, 4, 7 y 8 (dictamen de Roma 02, corrección 1)
# =====================================================================================================
# Cajas de búsqueda de la remera por plano (cuadro del máster: caja x0, y0, x1, y1; interpoladas entre claves). Dejan
# afuera el cielo y las olas (plano 7, y < 900) y la espuma de arriba y de abajo (plano 8). Adentro, la remera es la
# componente mayor de «tela clara cercana al croma del blanco»: la espuma suelta, la arena y la roca quedan afuera.
# Criterio de Pedro C (mc05.neutralizar): peso por luma × cercanía a la croma del blanco medido, corrimiento de Cb/Cr con
# la misma luma hasta el objetivo (B−R +7 / G−R +1,5; Roma pide ≤ +8). Agregados, medidos sobre el v01:
#   - la croma de la tela blanca depende de la luma: un modelo por cuadro (punto iluminado + punto de sombra si la sombra
#     es más azul que la proporción) da la croma esperada a cada luma, y la rampa de luma baja a 70 → 100 dentro de la
#     máscara de la remera. Con la rampa de Pedro C (140 → 180) la parte al sol quedaba neutra y la sombra seguía celeste
#     (c285, lo que vio Roma), y en el plano 7 (la Blanca en la mano, a la sombra, Y ≈ 131) no se corregía nada;
#   - cada píxel va hasta el objetivo y nunca más allá (lo ya neutro no se toca; nunca se empuja hacia el azul);
#   - el celeste de «Founders Privée» y los costados de su relieve se protegen (resguardo_estampado);
#   - un corrimiento por cuadro: en 7996 la remera cae y pasa de B−R +15 a +20, y en 7999 de +20 a +35.
NEUTRO = {
    '3': dict(cajas={75: (0, 600, 1080, 1920)}),
    '4': dict(cajas={120: (0, 0, 1080, 1920)}),
    '7': dict(cajas={240: (0, 900, 560, 1920)}),
    '8': dict(cajas={285: (220, 740, 1080, 1650), 300: (0, 730, 1080, 1700), 315: (0, 720, 1080, 1780),
                     329: (0, 650, 1080, 1920)}),
}
RAMPA_Y = (70.0, 100.0)
OBJ_BR, OBJ_GR = 7.0, 1.5          # Roma pide ≤ +8: objetivo +7 (G−R +1,5 de Pedro C) para que la medición quede debajo
D0, D1 = 5.0, 11.0                 # ventana de croma de Pedro C (mc05.neutralizar)
SUAVE = 1                          # sin media móvil: el corrimiento sigue la medición de cada cuadro, así el resultado queda quieto
# contexto de la neutralización: los valores por defecto son los de MC-04 v02. MC-03 v02 (mc03.etapa_master_v02) usa
# las mismas funciones con sus planos, cajas, base y rampa (L > 170, sin punto de sombra: la sombra proyectada no se toca)
CTX = dict(planos=None, neutro=NEUTRO, rampa=RAMPA_Y, base=None, med=None, sombra=True, mask_y=None, componentes='mayor',
           excluir_estampado=False, resguardo_relativo=None, rampas={}, _pid=None)
# excluir_estampado / resguardo_relativo (MC-03): en clip_f2a34e51 la tela está en B−R +46 y la regla absoluta del
# estampado marcaba media remera; rampas: rampa de luma por plano


def _rampa():
    """rampa de luma del plano en curso (CTX['rampas'][pid]) o la general (CTX['rampa'])."""
    return CTX['rampas'].get(CTX['_pid'], CTX['rampa'])


def _plano_de(k):
    for p in (CTX['planos'] or PLANOS):
        if p['m0'] <= k < p['m0'] + p['nf']:
            return p
    return None


def _half(Y):
    return Y.astype(np.float32).reshape(H // 2, 2, W // 2, 2).mean((1, 3))


def _rgb(Yh, Cb, Cr):
    return M.yuv444_rgb(Yh, Cb.astype(np.float32), Cr.astype(np.float32))


def delta_neutra(rgb, br=OBJ_BR, gr=OBJ_GR):
    """(dCb, dCr) que lleva el blanco medido a B−R = br, G−R = gr con la misma luma (mc05.delta_neutra)."""
    r, g, b = rgb
    yf = 0.2126 * r + 0.7152 * g + 0.0722 * b
    rt = yf - 0.7152 * gr - 0.0722 * br
    _, cbm, crm = M.rgb_yuv444(np.array([[r, g, b]], np.float32))
    _, cbt, crt = M.rgb_yuv444(np.array([[rt, rt + gr, rt + br]], np.float32))
    return float(cbm[0] - cbt[0]), float(crm[0] - crt[0])


def _caja_half(pid, k):
    x0, y0, x1, y1 = M.interp_caja(CTX['neutro'][pid]['cajas'], k)
    return int(x0) // 2, int(y0) // 2, int(x1) // 2, int(y1) // 2


def _oc(Yh, mo):
    """croma esperada de la Blanca a cada luma (desvío de 128). Sin punto de sombra: proporcional a (Y − 16) desde el
    punto iluminado (yl, cbl, crl). Con punto de sombra (ys, cbs, crs): recta entre sombra e iluminada (la sombra bajo el
    cielo es más azul que la proporción: en clip_a592f367, B−R +28 contra +20 a pleno sol) y proporcional fuera de ese
    tramo. Devuelve (desvío Cb, desvío Cr, escala de luma)."""
    yl = mo['yl']; olb, olr = mo['cbl'] - 128.0, mo['crl'] - 128.0
    sc = np.clip((Yh - 16.0) / (yl - 16.0), 0.0, 1.3)
    ocb, ocr = olb * sc, olr * sc
    if mo.get('ys'):
        ys = mo['ys']; osb, osr = mo['cbs'] - 128.0, mo['crs'] - 128.0
        t = np.clip((Yh - ys) / (yl - ys), 0, 1)
        scs = np.clip((Yh - 16.0) / (ys - 16.0), 0, 1)
        ocb = np.where(Yh >= yl, ocb, np.where(Yh < ys, osb * scs, osb + (olb - osb) * t))
        ocr = np.where(Yh >= yl, ocr, np.where(Yh < ys, osr * scs, osr + (olr - osr) * t))
    return ocb, ocr, sc


def _dist(Yh, Cb, Cr, mo):
    ocb, ocr, sc = _oc(Yh, mo)
    return np.hypot(Cb.astype(np.float32) - 128 - ocb, Cr.astype(np.float32) - 128 - ocr), sc


def _sat(Yh, Cb, Cr):
    rgb = _rgb(Yh, Cb, Cr)
    return (rgb.max(-1) - rgb.min(-1)) / (np.maximum(rgb.max(-1), 0) + 1)


def mascara_tela(Yh, Cb, Cr, pid, k, mo, ancho=1.0):
    """máscara suave (0–1, media resolución) de la remera: dentro de la caja del plano, tela clara cercana a la croma
    esperada de la Blanca; apertura (corta puentes finos con la espuma), componente mayor, agujeros rellenos (estampado),
    dilatación 4 px y desenfoque σ 3. ancho: multiplica la ventana de croma (medición de la sombra)."""
    from scipy import ndimage as nd
    x0, y0, x1, y1 = _caja_half(pid, k)
    dist, _ = _dist(Yh, Cb, Cr, mo)
    cand = np.zeros(Yh.shape, bool)
    cand[y0:y1, x0:x1] = True
    cand &= (Yh > (_rampa()[0] if CTX['mask_y'] is None else min(CTX['mask_y'], _rampa()[0]))) & (dist < D1 * ancho)
    cand = nd.binary_opening(cand, iterations=2)
    lab, n = nd.label(cand)
    if n == 0:
        return np.zeros(Yh.shape, np.float32)
    sz = nd.sum(cand, lab, range(1, n + 1))
    m = lab == (1 + int(np.argmax(sz)))
    if CTX['componentes'] == 'grandes':              # MC-03: la sombra proyectada parte la remera en varios pedazos claros
        m = np.isin(lab, 1 + np.nonzero(sz >= 0.10 * sz.max())[0])
    m = nd.binary_dilation(nd.binary_fill_holes(m), iterations=4)
    return np.clip(nd.gaussian_filter(m.astype(np.float32), 3.0), 0, 1)


def resguardo_estampado(Yh, Cb, Cr, caja=None, mo=None):
    """0–1: el celeste de «Founders Privée» (caras iluminadas del relieve: B−R > 35, saturación > 0,22, L > 155; a la
    sombra, B−R > 50 y saturación > 0,3) y 6 px
    alrededor (los costados del relieve, a la sombra). La sombra que el relieve proyecta sobre la tela, más lejos, sí se
    corrige: sin eso quedaban manchas azules sobre la tela ya neutra."""
    from scipy import ndimage as nd
    rgb = _rgb(Yh, Cb, Cr)
    L = rgb @ np.array([.2126, .7152, .0722], np.float32)
    sat = _sat(Yh, Cb, Cr); br = rgb[..., 2] - rgb[..., 0]
    if CTX['resguardo_relativo'] is not None and mo is not None:
        # MC-03 v02: en clip_f2a34e51 la tela misma está en B−R +46 con saturación 0,20–0,27, así que la regla absoluta
        # marcaba media remera como estampado (manchas celestes). Estampado = B−R que supera al de la tela esperada a esa
        # luma por más de resguardo_relativo (tela: p99 +19; «Founders Privée»: p90 +45 en c205)
        ocb, ocr, _ = _oc(Yh, mo)
        rm = _rgb(Yh, (ocb + 128).astype(np.float32), (ocr + 128).astype(np.float32))
        m = ((br - (rm[..., 2] - rm[..., 0])) > CTX['resguardo_relativo']) & (L > 150)
        m = nd.binary_opening(m, iterations=1)
        m = nd.binary_dilation(m, iterations=3)
        return np.clip(nd.gaussian_filter(m.astype(np.float32), 1.5), 0, 1)
    m = (br > 35) & (sat > 0.22) & (L > 155)
    # el estampado a la sombra (7996, sombra de quien filma): B−R ≈ +64 y saturación > 0,3; la tela a la sombra llega a
    # +24 (7996) y +32 (a592f367). (Por tono no sirve: el estampado a la sombra tiene G−R/B−R 0,34, como la tela.)
    # Solo si en la caja de la remera hay estampado iluminado (≥ 200 px): en 7999 (plano 7, c273–c279) el estampado no se
    # ve y la tela a la sombra llega a B−R +46 a +50 con saturación 0,30–0,34; sin esta condición quedaban manchas
    # celestes sobre la tela ya neutra (control del máster v02, primera pasada)
    if caja is None or (m & caja).sum() >= 200:
        m |= (br > 50) & (sat > 0.30) & (Yh > _rampa()[0])
    m = nd.binary_opening(m, iterations=1)
    m = nd.binary_dilation(m, iterations=3)
    return np.clip(nd.gaussian_filter(m.astype(np.float32), 1.5), 0, 1)


def peso_neutro(Yh, Cb, Cr, mo):
    """peso = rampa de luma × ventana de croma de Pedro C (alrededor de la croma esperada) × resguardo de saturación (el
    celeste de «Founders Privée» a la sombra queda cerca en croma de la tela a la sombra, pero es el doble de saturado).
    Devuelve (peso, escala de luma). v02 no define sat_lo: el resguardo por saturación dejaba manchas azules en las
    sombras profundas de la tela; el estampado se protege con resguardo_estampado()."""
    dist, sc = _dist(Yh, Cb, Cr, mo)
    w = _ss((Yh - _rampa()[0]) / (_rampa()[1] - _rampa()[0])) * (1 - _ss((dist - D0) / (D1 - D0)))
    if mo.get('sat_lo') is not None:
        w = w * (1 - _ss((_sat(Yh, Cb, Cr) - mo['sat_lo']) / 0.06))
    return w, sc


def _centro_inicial(Yh, Cb, Cr, pid, k):
    """croma y luma de partida: píxeles de la caja claros, poco saturados y de tinte entre neutro y celeste pálido (deja
    afuera arena, piel y el celeste de «Founders Privée»); luma de referencia = percentil 75."""
    x0, y0, x1, y1 = _caja_half(pid, k)
    sl = (slice(y0, y1), slice(x0, x1))
    rgb = _rgb(Yh[sl], Cb[sl], Cr[sl])
    br = rgb[..., 2] - rgb[..., 0]; gr = rgb[..., 1] - rgb[..., 0]
    sat = (rgb.max(-1) - rgb.min(-1)) / (rgb.max(-1) + 1)
    m = (Yh[sl] > 110) & (br > -5) & (br < 50) & (gr > -12) & (gr < 20) & (sat < 0.3)
    if CTX['excluir_estampado']:
        m &= resguardo_estampado(Yh, Cb, Cr)[sl] < 0.5
    return float(np.median(Cb[sl][m])), float(np.median(Cr[sl][m])), float(np.percentile(Yh[sl][m], 75))


def _leer_base_420(ks):
    sel = '+'.join(f'eq(n\\,{k})' for k in ks)
    a = np.frombuffer(U.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(CTX['base'] or T / 'mc04_base.mp4'), '-vf',
                             f"select='{sel}'", '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-']), np.uint8)
    fs = W * H * 3 // 2
    out = []
    for i in range(len(a) // fs):
        b = a[i * fs:(i + 1) * fs]
        out.append((b[:W * H].reshape(H, W), b[W * H:W * H * 5 // 4].reshape(H // 2, W // 2),
                    b[W * H * 5 // 4:].reshape(H // 2, W // 2)))
    return out


def _medir_blanco(Yh, Cb, Cr, pid, k, mo):
    """tela clara iluminada: peso × máscara > 0,8 y escala de luma > 0,85. Devuelve dict o None."""
    w, sc = peso_neutro(Yh, Cb, Cr, mo)
    g = mascara_tela(Yh, Cb, Cr, pid, k, mo)
    sel = (w * g > 0.8) & (sc > 0.85)
    if CTX['excluir_estampado']:
        sel &= resguardo_estampado(Yh, Cb, Cr, mo=mo) < 0.5
    if sel.sum() < 300:
        return None
    rgb = _rgb(Yh, Cb, Cr)[sel].mean(0)
    return dict(rgb=rgb, cb=float(Cb[sel].mean()), cr=float(Cr[sel].mean()), y=float(Yh[sel].mean()),
                w=float((w * g)[sel].mean()), sat=float(np.median(_sat(Yh, Cb, Cr)[sel])), px=int(sel.sum()))


def _medir_sombra(Yh, Cb, Cr, pid, k, mo, sat_l, br_l):
    """tela a la sombra (escala de luma 0,40–0,78) conectada a la remera, con una ventana de croma 2,2 veces más ancha,
    saturación < la de la tela iluminada + 0,12 (deja afuera el celeste del estampado) y más azul que la mitad de la
    proporción de la iluminada (deja afuera la arena y la roca a la sombra). Solo se usa si la sombra es más azul que la
    proporción: el modelo nunca empuja un píxel hacia el azul. None si no hay 800 píxeles o si no es más azul."""
    dist, sc = _dist(Yh, Cb, Cr, mo)
    rgb = _rgb(Yh, Cb, Cr); br = rgb[..., 2] - rgb[..., 0]
    g = mascara_tela(Yh, Cb, Cr, pid, k, mo, ancho=2.2)
    sel = ((g > 0.8) & (sc > 0.40) & (sc < 0.78) & (dist < 2.2 * D1) & (Yh > _rampa()[0]) & (br > 0.5 * br_l * sc))
    if sel.sum() < 800:
        return None
    br_s, sc_s = float(np.median(br[sel])), float(sc[sel].mean())
    if br_s <= br_l * sc_s + 2:
        return None
    return dict(ys=float(Yh[sel].mean()), cbs=float(np.median(Cb[sel])), crs=float(np.median(Cr[sel])),
                sat=float(np.median(_sat(Yh, Cb, Cr)[sel])), px=int(sel.sum()), b_menos_r=round(br_s, 1))


def medir_neutro():
    """por cuadro: (1) blanco de la tela iluminada, 3 pasadas (la croma medida pasa a ser el centro); (2) punto de sombra;
    (3) objetivo: B−R +7 / G−R +1,5 en la iluminada, proporcional a la luma en la sombra; el corrimiento se divide por el
    peso medio de la medición (el peso < 1 corrige de menos). Sin media móvil (SUAVE = 1)."""
    res = {}
    for pid in CTX['neutro']:
        CTX['_pid'] = pid
        p = [q for q in (CTX['planos'] or PLANOS) if q['id'] == pid][0]
        ks = list(range(p['m0'], p['m0'] + p['nf']))
        frs = _leer_base_420(ks)
        por = []
        for k, (Y, Cb, Cr) in zip(ks, frs):
            Yh = _half(Y)
            cb0, cr0, y0 = _centro_inicial(Yh, Cb, Cr, pid, k)
            mo = dict(yl=y0, cbl=cb0, crl=cr0)
            m = None
            for it in range(3):                    # el centro final es el que se usó en la última medición
                m2 = _medir_blanco(Yh, Cb, Cr, pid, k, mo)
                if m2 is None:
                    break
                m = m2
                if it < 2:
                    mo = dict(yl=m['y'], cbl=m['cb'], crl=m['cr'])
            if m is None:
                continue
            som = _medir_sombra(Yh, Cb, Cr, pid, k, mo, m['sat'], float(m['rgb'][2] - m['rgb'][0])) if CTX['sombra'] else None
            if som is not None and som['ys'] < mo['yl'] - 15:
                mo.update(ys=som['ys'], cbs=som['cbs'], crs=som['crs'])
            dcb, dcr = delta_neutra(m['rgb'])
            por.append(dict(k=k, modelo={a: round(float(b), 3) for a, b in mo.items()},
                            objetivo_cb_cr=[round(mo['cbl'] - dcb, 3), round(mo['crl'] - dcr, 3)], peso_medio=round(m['w'], 3),
                            antes=dict(b_menos_r=round(float(m['rgb'][2] - m['rgb'][0]), 1), g_menos_r=round(float(m['rgb'][1] - m['rgb'][0]), 1)),
                            px=m['px'], px_sombra=som['px'] if som else 0, sombra_b_menos_r=som['b_menos_r'] if som else None))
        res[pid] = dict(toma=p['toma'], cuadros_medidos=len(por), cuadros_del_plano=p['nf'], por_cuadro=por,
                        cajas=CTX['neutro'][pid]['cajas'], rampa_luma=_rampa(), ventana_croma=[D0, D1], objetivo=[OBJ_BR, OBJ_GR])
        brs = [q['antes']['b_menos_r'] for q in por]
        print(pid, p['toma'], 'cuadros', len(por), '/', p['nf'], 'B−R antes', min(brs), '…', max(brs),
              'con sombra', sum(1 for q in por if q['px_sombra']), flush=True)
    M.jdump(res, CTX['med'] or MED / 'neutro_v02.json')
    return res


def pre_neutro(med, log=None):
    """pre_fn de componer: en los planos de NEUTRO corre Cb/Cr hacia el objetivo con peso × máscara; el resto pasa
    igual. Un cuadro sin medición toma el modelo del cuadro medido más cercano."""
    idx = {pid: {q['k']: q for q in r['por_cuadro']} for pid, r in med.items()}

    def f(k, Y, Cb, Cr):
        p = _plano_de(k)
        if p is None or p['id'] not in med:
            return Cb, Cr
        CTX['_pid'] = p['id']
        tab = idx[p['id']]
        q = tab[min(tab, key=lambda j: abs(j - k))]
        mo = q['modelo']
        Yh = _half(Y)
        w, sc = peso_neutro(Yh, Cb, Cr, mo)
        x0, y0, x1, y1 = _caja_half(p['id'], k)
        caja = np.zeros(w.shape, bool); caja[y0:y1, x0:x1] = True
        w = w * mascara_tela(Yh, Cb, Cr, p['id'], k, mo) * (1 - resguardo_estampado(Yh, Cb, Cr, caja, mo))
        ocb, ocr, _ = _oc(Yh, mo)
        tcb, tcr = (q['objetivo_cb_cr'][0] - 128) * sc, (q['objetivo_cb_cr'][1] - 128) * sc
        sb, sr = ocb - tcb, ocr - tcr                         # corrimiento del modelo a esta luma
        n2 = sb * sb + sr * sr + 1e-6
        # cada píxel va hasta el objetivo y nunca más allá: el corrimiento es lo que el píxel se aparta del objetivo en la
        # dirección del modelo (uno ya neutro no se toca; uno hasta 1,6 veces más azul que el modelo llega justo al
        # objetivo). La luma no cambia, así que la textura de la tela queda igual
        fac = np.clip(((Cb.astype(np.float32) - 128 - tcb) * sb + (Cr.astype(np.float32) - 128 - tcr) * sr) / n2, 0, 1.6)
        g = w * fac
        Cb2 = M.u8(Cb.astype(np.float32) - g * sb); Cr2 = M.u8(Cr.astype(np.float32) - g * sr)
        if log is not None:
            lit = (w > 0.8) & (sc > 0.85)
            som = (w > 0.5) & (sc > 0.45) & (sc < 0.75)
            x0, y0, x1, y1 = _caja_half(p['id'], k)
            fuera = np.ones(w.shape, bool); fuera[y0:y1, x0:x1] = False
            r = dict(k=k, plano=p['id'], px_tela_iluminada=int(lit.sum()), px_tela_sombra=int(som.sum()),
                     max_cambio_fuera_de_la_caja=int(max(np.abs(Cb2.astype(int) - Cb)[fuera].max(initial=0),
                                                         np.abs(Cr2.astype(int) - Cr)[fuera].max(initial=0))))
            for nombre, sel in (('iluminada', lit), ('sombra', som)):
                if sel.sum() > 200:
                    a, b = _rgb(Yh, Cb, Cr)[sel].mean(0), _rgb(Yh, Cb2, Cr2)[sel].mean(0)
                    r[nombre] = dict(antes=[round(float(a[2] - a[0]), 1), round(float(a[1] - a[0]), 1)],
                                     despues=[round(float(b[2] - b[0]), 1), round(float(b[1] - b[0]), 1)])
            log.append(r)
        return Cb2, Cr2
    return f


def etapa_master_v02():
    MAS2.mkdir(parents=True, exist_ok=True)
    for n in NOMBRES_V02.values():
        assert not (MAS2 / n).exists() or '--rehacer' in sys.argv, f'{MAS2 / n} ya existe'
    planos = json.load(open(T / 'planos.json'))['planos']
    est = M.medir_estampado(T / 'mc04_base.mp4', planos, ROI_04, NF)
    # la medición no depende del resguardo del estampado: se reutiliza si ya está (--remedir la rehace)
    med = json.load(open(MED / 'neutro_v02.json')) if (MED / 'neutro_v02.json').exists() and '--remedir' not in sys.argv \
        else medir_neutro()
    log = []
    fn, textos = ui_mc04('v02')
    reg = M.componer(T / 'mc04_base.mp4', fn, A / 'mc04_completa.wav', MAS2 / NOMBRES_V02['completa'], NF,
                     choque_fn=M.choques(est), pre_fn=pre_neutro(med, log))
    print('choques', sum(1 for r in reg if r.get('choque_px', 0) > 0), flush=True)
    M.copiar_video(MAS2 / NOMBRES_V02['completa'], A / 'mc04_sinmusica.wav', MAS2 / NOMBRES_V02['sinmusica'])
    M.jdump(reg, MAS2 / 'registro_cuadros.json')
    M.jdump(log, MED / 'neutro_v02_por_cuadro.json')


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    {'planos': etapa_planos, 'medir': etapa_medir, 'audio': etapa_audio, 'master': etapa_master,
     'medir_neutro': medir_neutro, 'master_v02': etapa_master_v02}[etapa]()
