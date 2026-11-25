#!/usr/bin/env python3
"""BOC-25 P1 «Dos copas» · máster v01 (25/11/2026) · guion G1 de Fede con los cambios de Roma (P1_G1_roma.md).

Apuesta en c0 («Hoy Boca se juega 2 copas. / Y no es una final.»), pistas a favor y en contra hasta c443, giro en c552
(«Si pierde hoy, se apagan 2.»), reenganche «¿Diciembre con 1 copa o con 3?», placa «PARA GUARDAR» y CTA único
«Guardalo para ese día.» con IMG_8002. 30 fps, 888 cuadros = 29,60 s (el tramo 12 queda en 3,0 s: la placa se lee a 360 px).

Material: clips oficiales de TikTok (terceros, sin licencia; ver material/inventario_clips.md) y la toma propia IMG_8002
(biblioteca SDR TRABAJO/bocsud/lib). Cambios de tramo respecto del guion (fotogramas ampliados de la fuente):
  1  140245 @15,092 → @19,80–22,40: en 15–17,7 «betsson» se lee en varios pechos a 1080 px; además la copa con papel
     picado y jugadores chicos está en 19,6–26. En todo 140245 el sponsor sigue apareciendo: p1_sponsor.tapar lo vuelve
     ilegible (desenfoque solo de lo oscuro rodeado por la franja amarilla de la camiseta).
  2  750535 @7,137 → @4,05–5,55: el gol (la pelota pasa a los defensores y entra junto al palo derecho) está en 5,183 s
     (cuadro k 34 → c112); en 7,1–8,6 ya es el festejo (Valencia se tira, el defensor se agarra la cabeza). La
     hinchada estalla en 5,8 s de la fuente (nivel −22 → −10 dBFS).
  3  831508 @4,380 → @4,96–6,56: el remate sale en 4,96 y la pelota pasa al arquero en 6,34–6,37 s (k 42 → c165).
  8  425095 @9,376 → @10,05–11,65: 9,4–9,9 es un paneo barrido con personas cerca; 10,05–11,65 es tribuna con banderas
     (incluye el corte propio de la fuente en 11,12 = c429).
  9–10  140245 @18,865–22,465 → @22,40–26,00 (sigue donde terminó el gancho; el congelado gris es el plano más abierto).
  11 021013 @10,194 → @11,40–13,60: en 10,2–10,9 hay una cara de frente con anteojos; 11,4–13,6 es de espaldas con la copa
     en una mano y el bolso en la otra.
  14–15 IMG_8002 dura 3,567 s y la biblioteca llega a 3,467 (104 cuadros): el tramo 14 usa 1,800–3,467 (50 cuadros) y el
     congelado buscado empieza en c848 (no c852) con el último cuadro (3,433 s), espalda completa legible.
Fila del calendario 12/12: «12/12 · Final del Clausura · si llega» (Roma).

Etapas: python3 p1.py planos | trans | capa | audio | master | control | todo
"""
import sys, json, subprocess, hashlib, shutil, math
from pathlib import Path
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, '/home/user/1/scripts/bocsud')
sys.path.insert(0, '/home/user/1/scripts/boc25')
import comun as C
import p1_sponsor as SP
V = C.V

T = Path('/home/user/1/TRABAJO/boc25/p1')
FPS, W, H = 30, 1080, 1920
NF = 888
PIEZA = Path('/mnt/project-files/piezas/BOC-25_octavos_hoy')
VERSION = 'v02'          # v01 (11:02 UTC): CTA en rojo (estilo Sello). v02: CTA blanco con degradé oscuro detrás (Roma)
SALIDA = T / f'ROCCE_BOC25_P1_DOS_COPAS_{VERSION}.mp4'
ENTREGA = PIEZA / f'ROCCE_BOC25_P1_DOS_COPAS_{VERSION}.mp4'
CTRL = PIEZA / 'control'
LOGO = Path('/home/user/1/LOGO/rocce_logo.png')
FD = '/usr/share/fonts/opentype/inter/'
CELESTE = (126, 178, 222)
NOCHE = (10, 18, 42)

G1, G2 = 112, 165          # cuadro del gol de la Tabla Anual (750535 @5,183) y de la Sudamericana (831508 @6,37)
CORTES = [0, 78, 123, 171, 210, 282, 342, 396, 444, 486, 588, 654, 744, 798, 848]


def tapar(k, f):
    return SP.tapar(f)


def _p01():
    return C.real('140245', 19.80, 78, T / 's01_copa.mp4', c0=(0.5, 0.5), z0=1.0, z1=1.04, por_cuadro=tapar)


def _p09():
    return C.real('140245', 22.40, 42, T / 's09_copa.mp4', c0=(0.5, 0.52), z0=1.04, z1=1.0, por_cuadro=tapar)


def _p10():
    def pc(k, f):
        f = SP.tapar(f)
        if k >= 30:      # c516–c551: se destiñe hasta gris
            f = C.destenir(f, min(1.0, (k - 29) / 36))
        return f
    return C.real('140245', 24.00, 66, T / 's10_copa.mp4', c0=(0.5, 0.52), z0=1.0, z1=1.0, por_cuadro=pc)


def _p_resto():
    P = {}
    # 2 · c78–c122 el gol de la Tabla Anual detrás del arco (pelota adentro en k 34 = c112)
    P[2] = C.real('750535', 4.05, 45, T / 's02_gol1.mp4', c0=(0.5, 0.5), z0=1.0, z1=1.03)
    # 3 · c123–c170 el gol de la Sudamericana en plano general (pelota adentro en k 42 = c165)
    P[3] = C.real('831508', 4.96, 48, T / 's03_gol2.mp4', c0=(0.5, 0.5), z0=1.0, z1=1.05)
    # 4 · c171–c209 jugadores chicos junto al arco
    P[4] = C.real('831508', 13.139, 39, T / 's04_festejo.mp4', c0=(0.5, 0.5), z0=1.0)
    # 5 · c210–c281 Ezeiza, de espaldas con el bolso
    P[5] = C.real('021013', 0.0, 72, T / 's05_ezeiza.mp4', c0=(0.5, 0.5), z0=1.0, z1=1.04)
    # 6 · c282–c341 Bombonera
    P[6] = C.real('999061', 3.883, 60, T / 's06_bombonera.mp4', c0=(0.5, 0.5), z0=1.0)
    # 7 · c342–c395 vista cenital (el reloj incrustado «19:48» queda bajo la caja de «Partido único.»)
    P[7] = C.real('690964', 8.847, 54, T / 's07_cenital.mp4', c0=(0.5, 0.5), z0=1.0)
    # 8 · c396–c443 tribuna de la Bombonera
    P[8] = C.real('425095', 10.05, 48, T / 's08_tribuna.mp4', c0=(0.5, 0.5), z0=1.0)
    # 11 · c588–c653 de espaldas con la copa y el bolso
    P[11] = C.real('021013', 11.40, 66, T / 's11_copa_bolso.mp4', c0=(0.5, 0.5), z0=1.0, z1=1.04)
    # 13–14 · IMG_8002 (degradé oscuro suave arriba desde 0,9 s = k 27, para el texto blanco)
    P[13] = C.propia('IMG_8002', 0.0, 1.8, T / 's13_8002.mp4', por_cuadro=lambda k, f: degrade(f, min(1, max(0, (k - 27) / 8))))
    P[14] = _p14()
    return P


_DEG = {}


def degrade(f, a):
    """oscurece suave el tercio superior (texto blanco sobre cielo o arena)"""
    if a <= 0:
        return f
    if 'm' not in _DEG:
        y = np.arange(H, dtype=np.float32)
        m = np.clip(1 - y / 1050, 0, 1) ** 1.6
        _DEG['m'] = m[:, None, None]
    x = np.asarray(f, np.float32)
    return Image.fromarray((x * (1 - 0.5 * a * _DEG['m'])).clip(0, 255).astype(np.uint8))


# ---------------- placa del calendario (tramo 12, c654–c743) ----------------
FILAS = [('HOY 25/11', ' · 21:00 · Octavos vs. Independiente Rivadavia'),
         ('29/11', ' · Cuartos vs. Gimnasia LP · si gana hoy'),
         ('2/12', ' · Final Copa Argentina vs. Platense'),
         ('12/12', ' · Final del Clausura · si llega'),
         ('19/12', ' · Trofeo de Campeones vs. Belgrano · si gana el Clausura')]


def _f(nombre, tam):
    return ImageFont.truetype(FD + nombre, tam)


def _capa_texto(segmentos, ancho, interl, x0=0):
    """segmentos [(texto, fuente, color)] con ajuste por palabra a `ancho` px → RGBA (supermuestreo ×2)"""
    S = 2
    palabras = []
    for txt, fu, col in segmentos:
        fS = ImageFont.truetype(fu.path, fu.size * S)
        for i, p in enumerate(txt.split(' ')):
            palabras.append((('' if i == 0 else ' ') + p, fS, col))
    lineas, cur, w = [], [], 0
    for p, fS, col in palabras:
        pw = fS.getlength(p)
        if cur and w + pw > ancho * S:
            lineas.append(cur); cur = [(p.lstrip(), fS, col)]; w = fS.getlength(p.lstrip())
        else:
            cur.append((p, fS, col)); w += pw
    lineas.append(cur)
    alto = int(len(lineas) * interl * S + 20 * S)
    im = Image.new('RGBA', (ancho * S + 40 * S, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lineas):
        x = 0
        for p, fS, col in ln:
            d.text((x, i * interl * S), p, font=fS, fill=col + (255,))
            x += fS.getlength(p)
    return im.resize((im.width // S, im.height // S), Image.LANCZOS), len(lineas)


def placa_calendario(salida):
    n = 90
    base = Image.new('RGB', (W, H), NOCHE)
    # viñeta muy suave hacia los bordes
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.25 * (((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2) * 2
    base = Image.fromarray((np.asarray(base, np.float32) * v[..., None]).clip(0, 255).astype(np.uint8))
    M = 72
    capas = []        # (cuadro de entrada, imagen RGBA, x, y)
    # etiqueta PARA GUARDAR (píldora celeste) y título
    S = 4
    fe = _f('InterDisplay-SemiBold.otf', 34 * S)
    et = 'PARA GUARDAR'
    esp = 6 * S
    wtxt = sum(fe.getlength(c) for c in et) + esp * (len(et) - 1)
    pill = Image.new('RGBA', (int(wtxt + 56 * S), 66 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(pill)
    d.rounded_rectangle([0, 0, pill.width - 1, pill.height - 1], radius=33 * S, outline=CELESTE + (255,), width=3 * S)
    x = 28 * S
    for c in et:
        d.text((x, 12 * S), c, font=fe, fill=CELESTE + (255,)); x += fe.getlength(c) + esp
    pill = pill.resize((pill.width // S, pill.height // S), Image.LANCZOS)
    capas.append((0, pill, M, 270))
    tit, _ = _capa_texto([('EL CALENDARIO DE BOCA', _f('InterDisplay-ExtraBold.otf', 70), (255, 255, 255))], W - 2 * M + 30, 80)
    capas.append((0, tit, M, 362))
    lin = Image.new('RGBA', (W - 2 * M, 4), CELESTE + (255,))
    capas.append((2, lin, M, 470))
    y = 515
    fd_ = _f('InterDisplay-ExtraBold.otf', 56); ft_ = _f('InterDisplay-SemiBold.otf', 52)
    for i, (fecha, resto) in enumerate(FILAS):
        im, nl = _capa_texto([(fecha, fd_, CELESTE), (resto, ft_, (255, 255, 255))], W - 2 * M - 24, 66)
        capas.append((6 + 8 * i, im, M + 24, y))
        if i == 0:      # hoy: barra celeste a la izquierda
            capas.append((6, Image.new('RGBA', (8, nl * 66 - 8), CELESTE + (255,)), M, y + 8))
        y += nl * 66 + 36
        if i < len(FILAS) - 1:
            capas.append((6 + 8 * i, Image.new('RGBA', (W - 2 * M, 2), CELESTE + (90,)), M, y - 18))
    y += 26
    msg, nl = _capa_texto([('Esta noche: se tachan 2', _f('InterDisplay-Bold.otf', 62), (255, 255, 255))], W - 2 * M, 74)
    msg2, _ = _capa_texto([('o siguen las 3.', _f('InterDisplay-Bold.otf', 62), (255, 255, 255))], W - 2 * M, 74)
    capas.append((42, msg, M, y)); capas.append((42, msg2, M, y + 74))
    y += 2 * 74 + 46
    # fila celeste «__/__ · Tu próxima fecha» dentro de un recuadro celeste
    fila, _ = _capa_texto([('__/__ · Tu próxima fecha', _f('InterDisplay-ExtraBold.otf', 60), CELESTE)], W - 2 * M - 60, 70)
    caja = Image.new('RGBA', (W - 2 * M, 116), (0, 0, 0, 0))
    cS = Image.new('RGBA', (caja.width * S, caja.height * S), (0, 0, 0, 0))
    ImageDraw.Draw(cS).rounded_rectangle([0, 0, cS.width - 1, cS.height - 1], radius=18 * S, fill=CELESTE + (34,), outline=CELESTE + (255,), width=4 * S)
    caja = cS.resize(caja.size, Image.LANCZOS)
    caja.alpha_composite(fila, (30, 22))
    capas.append((72, caja, M, y))
    enc = C.encoder(salida)
    for k in range(n):
        fr = base.convert('RGBA')
        for (k0, im, x, yy_) in capas:
            if k < k0:
                continue
            a = min(1.0, (k - k0 + 1) / 4)
            dy = int(round((1 - C.suave(a)) * 18))
            if a < 1:
                im2 = im.copy(); al = np.asarray(im2.getchannel('A'), np.float32) * a
                im2.putalpha(Image.fromarray(al.astype(np.uint8)))
            else:
                im2 = im
            fr.alpha_composite(im2, (x, yy_ + dy))
        enc.stdin.write(np.asarray(fr.convert('RGB'), np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    return dict(placa='calendario', cuadros=n, salida=str(salida), alto_final=y + 112)


def placa():
    """rehace solo la placa del calendario y vuelve a armar el montaje con los demás planos ya hechos"""
    P = json.load(open(T / 'planos.json'))
    i = [k for k, p in enumerate(P) if p.get('placa') == 'calendario'][0]
    P[i] = placa_calendario(T / 's12_calendario.mp4')
    n = C.armar(P, T / 'p1_video.mp4')
    assert n == NF, n
    json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('placa', P[i])


def _p14():
    """tramo 14 (c798–c847): degradé superior + degradé oscuro suave detrás del CTA blanco (v02), que entra en 6 cuadros"""
    def pc(k, f):
        f = degrade(f, 1.0)
        a = min(1.0, (k + 1) / 6)
        return C.sombra(f, 540, 400, rx=600, ry=260, k=0.42 * a)
    return C.propia('IMG_8002', 1.8, 1.8 + 50 / FPS, T / 's14_8002.mp4', por_cuadro=pc)


def cierre():
    """v02: rehace los tramos 14–15 (degradé detrás del CTA) y vuelve a armar con los demás planos ya hechos"""
    P = json.load(open(T / 'planos.json'))
    i14 = [k for k, p in enumerate(P) if str(p.get('salida', '')).endswith('s14_8002.mp4')][0]
    P[i14] = _p14()
    P[i14 + 1] = C.congelar(T / 's14_8002.mp4', 49, 40, T / 's15_congelado.mp4')
    n = C.armar(P, T / 'p1_video.mp4')
    assert n == NF, n
    json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('cierre', P[i14]['salida'], P[i14 + 1]['salida'])


def copa():
    """rehace los tramos de 140245 (1, 9, 10 y su congelado) con p1_sponsor actual y vuelve a armar"""
    P = json.load(open(T / 'planos.json'))
    idx = {Path(p['salida']).name: k for k, p in enumerate(P)}
    with Pool(3) as pool:
        r = [pool.apply_async(f) for f in (_p01, _p09, _p10)]
        nuevos = [x.get() for x in r]
    for q in nuevos:
        P[idx[Path(q['salida']).name]] = q
    P[idx['s10b_congelado.mp4']] = C.congelar(T / 's10_copa.mp4', 65, 36, T / 's10b_congelado.mp4', por_cuadro=lambda k, f: C.destenir(f, 1.0))
    n = C.armar(P, T / 'p1_video.mp4')
    assert n == NF, n
    json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('copa', n)


def planos():
    with Pool(4) as pool:
        r1 = pool.apply_async(_p01); r9 = pool.apply_async(_p09); r10 = pool.apply_async(_p10)
        rr = pool.apply_async(_p_resto)
        P1, P9, P10, R = r1.get(), r9.get(), r10.get(), rr.get()
    P12 = placa_calendario(T / 's12_calendario.mp4')
    P10c = C.congelar(T / 's10_copa.mp4', 65, 36, T / 's10b_congelado.mp4', por_cuadro=lambda k, f: C.destenir(f, 1.0))
    P15 = C.congelar(T / 's14_8002.mp4', 49, 40, T / 's15_congelado.mp4')
    P = [P1, R[2], R[3], R[4], R[5], R[6], R[7], R[8], P9, P10, P10c, R[11], P12, R[13], R[14], P15]
    n = C.armar(P, T / 'p1_video.mp4')
    assert n == NF, n
    json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('cuadros', n)


TRANS = {444: 'barrido', 744: 'barrido'}


def trans():
    C.transiciones(T / 'p1_video.mp4', T / 'p1_video_t.mp4', TRANS, NF)
    print('transiciones', TRANS)


# ---------------- capa gráfica por cuadro: contador de 5 círculos y logo ----------------
CX = [368, 454, 540, 626, 712]
CY = 326
R0 = 23            # Ø46
X0, Y0, PW, PH = 300, 268, 480, 140      # parche del contador en el cuadro
BEATS11 = [588, 603, 618, 633, 648]


def estado(c):
    """lista de 5 (modo, escala, brillo) con modo 'vacio' | 'lleno' | 'gris'; línea 4–5; rótulo 2/12"""
    st = []
    for i in range(5):
        modo, esc, br = 'vacio', 1.0, 0.0
        if i == 0 and c >= G1:
            modo = 'lleno'; esc = 1 + 0.35 * max(0, 1 - (c - G1) / 5); br = max(0, 1 - (c - G1) / 6)
        if i == 1 and c >= G2:
            modo = 'lleno'; esc = 1 + 0.35 * max(0, 1 - (c - G2) / 5); br = max(0, 1 - (c - G2) / 6)
        for (j, c0) in ((2, 222), (3, 234), (4, 246)):
            if i == j and c0 <= c < c0 + 8:
                esc = 1 + 0.32 * (1 - (c - c0) / 8); br = 0.8 * (1 - (c - c0) / 8)
        if i in (3, 4) and 552 <= c < 588:
            modo = 'gris'
            if c < 556:
                esc = 1 + 0.2 * (1 - (c - 552) / 4)
        if i in (3, 4) and 588 <= c < 654:
            b = max(b0 for b0 in BEATS11 if b0 <= c)
            modo = 'gris' if BEATS11.index(b) % 2 == 0 else 'vacio'
            esc = 1 + 0.18 * max(0, 1 - (c - b) / 5)
        st.append((modo, esc, br))
    return st, (552 <= c < 654), (c >= 444)


def dibujar_contador(c):
    S = 4
    im = Image.new('RGBA', (PW * S, PH * S), (0, 0, 0, 0))
    sh = Image.new('L', (PW * S, PH * S), 0)
    d = ImageDraw.Draw(im); ds = ImageDraw.Draw(sh)
    st, linea, rot = estado(c)
    cx = [(x - X0) * S for x in CX]; cy = (CY - Y0) * S
    if linea:
        x1 = cx[3] + R0 * S; x2 = cx[4] - R0 * S
        ds.rectangle([x1, cy - 6 * S, x2, cy + 6 * S], fill=170)
        d.rectangle([x1, cy - 2 * S, x2, cy + 2 * S], fill=(205, 205, 205, 255))
    for i, (modo, esc, br) in enumerate(st):
        r = R0 * esc * S
        ds.ellipse([cx[i] - r - 5 * S, cy - r - 5 * S, cx[i] + r + 5 * S, cy + r + 5 * S], fill=150)
        if modo == 'lleno':
            col = tuple(int(v + (255 - v) * 0.6 * br) for v in CELESTE)
            d.ellipse([cx[i] - r, cy - r, cx[i] + r, cy + r], fill=col + (255,), outline=(255, 255, 255, 255), width=4 * S)
        elif modo == 'gris':
            d.ellipse([cx[i] - r, cy - r, cx[i] + r, cy + r], fill=(128, 128, 128, 153), outline=(150, 150, 150, 255), width=4 * S)
        else:
            a = int(255 * min(1, 0.85 + br))
            d.ellipse([cx[i] - r, cy - r, cx[i] + r, cy + r], fill=(0, 0, 0, 90), outline=(255, 255, 255, a), width=4 * S)
        if br > 0 and modo == 'lleno':      # anillo que se abre en el gol
            rr = r + (1 - br) * 22 * S
            d.ellipse([cx[i] - rr, cy - rr, cx[i] + rr, cy + rr], outline=CELESTE + (int(255 * br),), width=3 * S)
    if rot:
        f = ImageFont.truetype(FD + 'InterDisplay-Bold.otf', 32 * S)
        t = '2/12'; tw = f.getlength(t)
        ds.text((cx[2] - tw / 2, cy + (R0 + 8) * S), t, font=f, fill=255, stroke_width=3 * S, stroke_fill=255)
        d.text((cx[2] - tw / 2, cy + (R0 + 8) * S), t, font=f, fill=(255, 255, 255, 255))
    sh = sh.resize((PW, PH), Image.LANCZOS).filter(ImageFilter.GaussianBlur(5))
    im = im.resize((PW, PH), Image.LANCZOS)
    return im, sh


def ficha_logo(lado=132, radio=0.10):
    lg = Image.open(LOGO).convert('RGB').resize((lado, lado), Image.LANCZOS)
    S = 4
    m = Image.new('L', (lado * S, lado * S), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, lado * S - 1, lado * S - 1], radius=radio * lado * S, fill=255)
    lg.putalpha(m.resize((lado, lado), Image.LANCZOS))
    return lg


LOGO_XY = (540 - 66, 545)


def capa():
    src, dst = T / 'p1_video_t.mp4', T / 'p1_video_g.mp4'
    nb = W * H * 3
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(src), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = C.encoder(dst)
    lg = ficha_logo()
    c = 0
    while True:
        b = dec.stdout.read(nb)
        if len(b) < nb:
            break
        if 78 <= c < 654 or c >= 852:
            fr = Image.frombuffer('RGB', (W, H), b, 'raw', 'RGB', 0, 1).copy()
            if 78 <= c < 654:
                im, sh = dibujar_contador(c)
                parche = np.asarray(fr.crop((X0, Y0, X0 + PW, Y0 + PH)), np.float32)
                parche *= (1 - 0.55 * np.asarray(sh, np.float32)[..., None] / 255)
                p = Image.fromarray(parche.clip(0, 255).astype(np.uint8)).convert('RGBA')
                p.alpha_composite(im)
                fr.paste(p.convert('RGB'), (X0, Y0))
            if c >= 852:
                a = min(1.0, (c - 851) / 4)
                l2 = lg.copy(); l2.putalpha(Image.fromarray((np.asarray(lg.getchannel('A'), np.float32) * a).astype(np.uint8)))
                fr.paste(l2, LOGO_XY, l2)
            b = np.asarray(fr, np.uint8).tobytes()
        enc.stdin.write(b); c += 1
    dec.stdout.close(); dec.wait(); enc.stdin.close(); enc.wait()
    assert c == NF, c
    print('capa gráfica', c)


# ---------------- textos (ASS) ----------------
V.ESTILOS.update({
    'BlancoG': ('Inter Display ExtraBold', 92, '&H00FFFFFF', '&H70000000', '&H90000000', 0, 2.5, 3, 1, 8, 0),
})
AST = '{\\c&H00DEB27E&}*{\\c&H00FFFFFF&}'


def t(c):
    return c / FPS


def tx(c):
    """tiempo de entrada/salida de un texto en el cuadro c. El .ass se escribe en centésimas (redondeadas): c/30 − 4 ms
    redondeaba otra vez a c/30 y libass, que compara en ms, lo mostraba un cuadro tarde (c798 en v01). Centésima
    entre el cuadro c−1 y el c (c/30 − 10 ms, hacia abajo)."""
    return max(math.floor((c / FPS - 0.01) * 100 + 1e-9) / 100, 0.0)


def textos():
    X = []

    def caja(a, b, txt, y, maximo='CajaN_96', plano=None, pop=True):
        est = C.caja((plano or txt), maximo)
        X.append(dict(t0=tx(a), t1=tx(b), txt=txt, estilo=est, y=y, pop=pop))
    # 1 · APUESTA (debajo de la marca de agua de la cuenta, x 70–260 y 245–395)
    X.append(dict(t0=tx(0), t1=tx(78), txt='21:00 · BOMBONERA', estilo='CajaN_ctx', y=410))
    caja(0, 78, 'Hoy Boca se juega\\N2 copas.', 520, 'CajaN_96', plano='Hoy Boca se juega')
    caja(27, 78, 'Y no es una final.', 835, 'CajaN_96')
    # 2–4 · pistas a favor (en 750535 la marca LPF ocupa x 905–1025 y 240–500: texto desde y 540)
    caja(78, 123, '07/11 · Tabla Anual', 540)
    caja(123, 171, '21/11 · Sudamericana', 440)
    caja(171, 210, 'Van 2 en 14 días.', 440)
    # 5 · lista
    caja(210, 282, 'Le quedan 3 copas por jugar:', 440)
    caja(222, 282, 'Copa Argentina · final 2/12', 628, 'CajaN_84')
    caja(234, 282, 'Clausura', 782, 'CajaN_84')
    caja(246, 282, 'Trofeo de Campeones ' + AST, 936, 'CajaN_84', plano='Trofeo de Campeones *')
    # 6
    caja(282, 342, 'Antes de diciembre: hoy.', 440)
    caja(297, 342, 'Octavos del Clausura · 21:00', 625, 'CajaN_84')
    # 7 · la caja de «Partido único.» tapa el reloj incrustado (x 480–598, y 940–977)
    caja(342, 396, 'Partido único.', 905)
    caja(357, 396, 'Si empata: alargue y penales.', 1090, 'CajaN_84')
    # 8 · GRAN PREGUNTA (425095 también lleva la marca LPF)
    caja(396, 444, 'Una es el Clausura.', 540)
    caja(414, 444, '¿La otra, la Copa Argentina?', 722)
    # 9 · GIRO 1
    caja(444, 486, 'No. Esa final\\Nse juega igual: 2/12.', 440, plano='se juega igual: 2/12.')
    # 10 · GIRO (B)
    caja(486, 516, 'Es la del asterisco.', 440)
    caja(516, 552, 'Trofeo de Campeones ' + AST + ':\\Nsolo si gana el Clausura.', 440, 'CajaN_84', plano='solo si gana el Clausura.')
    X.append(dict(t0=tx(552), t1=tx(588), txt='{\\fs118}Si pierde hoy,\\Nse apagan 2.', estilo='Golpe', y=840, pop=True))
    # 11 · REENGANCHE
    caja(588, 654, '¿Diciembre con\\N1 copa o con 3?', 440, plano='¿Diciembre con')
    caja(624, 654, 'Se contesta hoy, 21:00.', 720, 'CajaN_84')
    # 13–15 · consecuencia y CTA sobre IMG_8002
    X.append(dict(t0=tx(744), t1=tx(798), txt='Tu próxima fecha\\Nno es una final.', estilo='BlancoG', y=300, pop=True))
    X.append(dict(t0=tx(771), t1=tx(798), txt='Puede valer 2.', estilo='BlancoG', y=560, pop=True))
    # v02: blanco Inter Display ExtraBold (BlancoG) en el mismo lugar (centro en y 400) y tiempos que el Sello rojo de v01
    X.append(dict(t0=tx(798), t1=tx(NF) + 0.05, txt='{\\an5\\fs120}Guardalo\\Npara ese día.', estilo='BlancoG', y=400, pop=True))
    return X


# ---------------- sonido ----------------
def audio(con_musica=True):
    DUR = NF / FPS
    m = C.MezclaB(DUR)
    GOL1, OVA = C.clip('750535'), C.clip('425095')
    # hinchada real (750535 y 425095: espectro liso, tonalidad 3–5 dB: sin música ni relator detectados; sin escuchar)
    m.real(OVA, 0.5, t(0), t(78), -14, hp=120, ini=0.02, fin=0.05, etiqueta='hinchada real 425095 (baja)')
    m.real(GOL1, 3.70, t(78), t(G1 + 4), -9, ini=0.03, fin=0.02, etiqueta='hinchada real 750535 (antes del gol)')
    m.real(GOL1, 5.75, t(G1 + 2), t(171), -4, ini=0.02, fin=0.4, etiqueta='hinchada real 750535: estallido del gol (5,8 s)')
    m.real(OVA, 6.8, t(G2 - 4), t(212), -5, ini=0.15, fin=0.3, etiqueta='hinchada real 425095: subida en el gol 2')
    m.real(OVA, 3.0, t(205), t(282), -12, hp=120, ini=0.2, fin=0.2, etiqueta='hinchada real 425095 (−6 dB bajo la lista)')
    m.real(OVA, 4.5, t(280), t(342), -9, ini=0.1, fin=0.1, etiqueta='hinchada real 425095')
    m.real(GOL1, 9.0, t(340), t(396), -10, ini=0.1, fin=0.1, etiqueta='hinchada real 750535 (partido)')
    m.real(OVA, 9.9, t(394), t(444), -14, hp=150, ini=0.1, fin=0.05, etiqueta='hinchada real 425095 (baja)')
    m.real(OVA, 7.0, t(444), t(552), -7, ini=0.08, fin=0.04, etiqueta='hinchada real 425095 (sube en el giro)')
    m.real(OVA, 1.0, t(552), t(588), -30, hp=200, ini=0.02, fin=0.2, etiqueta='hinchada real casi en silencio (−30 dB)')
    m.real(OVA, 2.0, t(586), t(654), -15, hp=150, ini=0.25, fin=0.15, etiqueta='hinchada real 425095 (−12 dB)')
    # efectos
    m.toque(t(0), 0.30); m.toque(t(27), 0.30)
    m.latido(t(40), 0.35)
    m.impacto(t(G1), 0.55)
    m.subida(t(140), t(G2), 0.12)
    m.impacto(t(G2), 0.5)
    for c in (210, 222, 234, 246):
        m.charles(t(c), 0.22, abierto=True)
    m.latido(t(300), 0.35); m.latido(t(325), 0.35)
    m.silbato(t(342), 0.35, 0.22)
    m.latido(t(360), 0.45); m.latido(t(380), 0.45)
    for c in (398, 412, 424, 433, 440):        # el latido acelera hacia la pregunta
        m.latido(t(c), 0.5)
    m.barrido(t(444), 0.35, 0.2)
    m.redoble(t(516), t(552), 0.12); m.subida(t(516), t(552), 0.12)
    m.golpe_sordo(t(552), 0.7)
    for c in BEATS11:
        m.latido(t(c), 0.45)
    for c in (660, 668, 676, 684, 692):
        m.charles(t(c), 0.16)
    m.toque(t(726), 0.22, f=1800)
    m.barrido(t(744), 0.35, 0.2)
    if con_musica:
        # música propia sintetizada (TEMP): entra con la placa (pad + 808 suave), sube en el cierre
        b = 60 / 120
        m.pad(t(654), [45, 52, 57, 61], t(234), 0.05, corte=1500)
        k = 0; t0 = t(654)
        while t0 + k * b < t(NF) - 0.1:
            tt = t0 + k * b
            if k % 4 == 0:
                m.ocho08(tt, [33, 33, 36, 31][(k // 4) % 4], b * 3.6, 0.38 if tt < t(744) else 0.5)
                if tt >= t(744): m.bombo(tt, 0.6)
            if k % 4 == 2 and tt >= t(744):
                m.palma(tt, 0.22)
            m.charles(tt + b / 2, 0.05)
            k += 1
        m.pad(t(744), [45, 52, 57, 64], t(NF) - t(744), 0.06, corte=2200)
        m.fundido('mus', t(876), t(NF))
        m.fundido('bombo', t(876), t(NF))
        m.fundido('fx', t(876), t(NF))
    (T / 'audio').mkdir(exist_ok=True)
    nombre = 'p1_completa.wav' if con_musica else 'p1_sinmusica.wav'
    r = m.exportar(str(T / 'audio' / nombre), lufs=-14)
    json.dump(getattr(m, 'registro', []), open(T / 'audio' / 'registro.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print(nombre, r)


def master():
    a = V.ass(textos(), T / 'p1.ass')
    V.master(T / 'p1_video_g.mp4', T / 'audio' / 'p1_completa.wav', SALIDA, ass_path=a)
    print(SALIDA)


def control():
    CTRL.mkdir(parents=True, exist_ok=True)
    pre = 'P1_' if VERSION == 'v01' else f'P1_{VERSION}_'
    V.hoja(SALIDA, CTRL / f'{pre}hoja_0-5s.jpg')
    clave = sorted(set(CORTES + [c - 1 for c in CORTES if c] + [G1, G2, 246, 552, 560, 696, 726, 740, 852, NF - 1]))
    for c in clave:
        V.cuadro(SALIDA, c, CTRL / f'{pre}c{c:03d}.jpg')
    if not ENTREGA.exists():
        shutil.copy2(SALIDA, ENTREGA)
    print('control', len(clave), ENTREGA)


if __name__ == '__main__':
    T.mkdir(parents=True, exist_ok=True)
    et = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    if et in ('planos', 'todo'): planos()
    if et == 'placa': placa()
    if et == 'cierre': cierre()
    if et == 'copa': copa()
    if et in ('trans', 'todo', 'placa', 'cierre', 'copa'): trans()
    if et in ('capa', 'todo', 'placa', 'cierre', 'copa'): capa()
    if et in ('audio', 'todo'): audio(True)
    if et in ('master', 'todo'): master()
    if et in ('control', 'todo'): control()
