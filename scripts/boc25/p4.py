#!/usr/bin/env python3
"""BOC-25 P4 «La balanza» · valor: disciplina · receta v02 (25/11/2026; v01 en TRABAJO/boc25/p4/p4_receta_v01.py). Guion G1 (Fede) aprobado por Roma 08:32.

Pieza solo con texto (sin locución). Una balanza blanca (viga, triángulo, pesas, etiquetas BOCA / RIVADAVIA) se dibuja
por cuadro con Pillow (supermuestreo ×3) en una pasada propia sobre el video armado, antes del .ass.
Clips oficiales de terceros (TikTok @bocajuniors, @ligaprofesional, @tycsports; sin licencia), tomas propias 7887 y 7894.

Cambios respecto del guion (ver 06_pedro_P4.md):
  T1  326869 1,00–3,40 (no 0,00–2,40): 0,00–0,90 tiene hinchas en primer plano y un barrido; desde 3,1 s entra una cara
      por el borde derecho: acercamiento lento 1,00→1,38 hacia la izquierda que la deja afuera.
  T2  001281 26,95–28,65 (no 27,86–29,56): desde 28,6 s una bengala/humo blanco tapa a los jugadores.
  T3  425095 10,15–12,15 (no 9,38–11,38): 9,38–9,6 muestra el anillo superior con «betsson» legible.
  T5  297108 («Qué DT», @bocajuniors 07/11) 0,50–2,60, el Vasco de espaldas saluda a la Bombonera (blanco y negro):
      en 425095 3,10–5,20 «betsson» se lee en tres bandas del estadio. El sonido sigue siendo la ovación real de 425095.
  T10 326869 13,70–14,77 y T11 326869 14,77–16,77 (no 425095 11,38–12,45 ni 326869 2,40–4,40): 425095 ya no alcanza
      después de mover T3 y en 326869 3,0–4,5 hay una cara en primer plano.
  T12 7887 1,40–3,60 (66 cuadros) y T13 7894 0,00–2,37 (71 cuadros): la biblioteca de 7894 tiene 71 cuadros; el CTA
      entra en c767 (no c766).
  CTA nuevo (Roma, 25/11): «¿Para dónde la inclinás vos?» + «Comentalo antes de las 21:00.»
  Horizontales: recorte 470,0 1450×890 (fuera el zócalo «ÚLTIMA NOTICIA» desde y≈897 y el rótulo «VIVO · …» de arriba a
      la izquierda; la marca de agua de TyC queda entera), ventana de 960 px en y=500.

Etapas: python3 p4.py planos | barra | audio | master | control | entregar | todo
"""
import sys, json, math, subprocess, shutil, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, '/home/user/1/scripts/bocsud')
import comun as C
V = C.V

T = Path('/home/user/1/TRABAJO/boc25/p4')
PIEZA = Path('/mnt/project-files/piezas/BOC-25_octavos_hoy')
CONTROL = PIEZA / 'control'
VERSION = 'v02'
SALIDA = PIEZA / f'ROCCE_BOC25_P4_LA_BALANZA_{VERSION}.mp4'
MASTER_T = T / f'p4_master_{VERSION}.mp4'
VID = T / f'p4_video_{VERSION}.mp4'          # montaje
VID_B = T / f'p4_video_b_{VERSION}.mp4'      # montaje + balanza
FPS, W, H = 30, 1080, 1920
NF = 838
REC = (470, 0, 1450, 890)          # recorte de los horizontales de TyC (x, y, w, h)
FG_W, FG_Y = 960, 500              # ventana de los horizontales
CEL = (126, 178, 222)              # celeste del estilo Celeste (&H00DEB27E)
OSC = (22, 22, 24)
LOGO = Path('/home/user/1/LOGO/rocce_logo.png')

# planos: (nombre, cuadro de entrada, cuadros, vertical)
CORTES = [0, 72, 123, 183, 273, 336, 423, 474, 531, 609, 641, 701, 767]
VERT = [(0, 72), (123, 183), (273, 336), (609, 707)]      # pantalla completa: banda oscura detrás de la barra (v02: T6 es ventana)


def t(c):
    return c / FPS


def tx(c):
    return max(c / FPS - 0.004, 0.0)


def ventana(id_, t0, n, salida, por_cuadro=None):
    return dict(C.video_ventana(C.clip(id_), t0, n / FPS, salida, recorte=REC, fg_w=FG_W, fg_y=FG_Y,
                                por_cuadro=por_cuadro), cuadros=n)


def planos():
    P = []
    # T1 c0–71 apuesta: la multitud de noche en Ezeiza. Acercamiento 1,00→1,38 hacia la izquierda (la cara que entra por
    # el borde derecho desde 3,1 s queda afuera).
    def v1(k):
        a = k / 71
        return 0.5 + (0.30 - 0.5) * a, 0.5, 1.0 + 0.38 * a
    P.append(C.real('326869', 1.00, 72, T / 's01.mp4', ventana=v1))
    P.append(ventana('001281', 26.95, 51, T / 's02.mp4'))                                     # T2 c72–122
    # T3 c123–182 (v02): 085940 = 7708188983750085940 @bocajuniors 14/11, tribuna con humo y el plantel de espaldas,
    # encuadre más cerrado que en T10/T11 (mismo clip, otro tramo). v01 usaba 425095 10,15–12,15, la misma tribuna que P1.
    # ventana anclada arriba (cielo con humo y tribuna; el plantel queda abajo, fuera de la balanza), empuje 1,50→1,56
    P.append(C.real('085940', 0.00, 60, T / 's03_v02.mp4', ventana=lambda k: C.anclada(180, 0, 1.50 + 0.06 * k / 59)))
    P.append(ventana('864385', 10.77, 90, T / 's04.mp4'))                                     # T4 c183–272
    P.append(C.real('297108', 0.50, 63, T / 's05.mp4', z0=1.0, z1=1.04))                      # T5 c273–335
    # T6 c336–422 giro (v02): 145556 = 7711207545922145556 @tycsports, el plantel en el micro antes de salir al predio.
    # v01 usaba 021013 12,40–15,30 (el aeropuerto), que también usa P1.
    P.append(ventana('145556', 14.00, 87, T / 's06_v02.mp4'))
    P.append(ventana('001281', 34.83, 51, T / 's07.mp4'))                                     # T7 c423–473
    P.append(ventana('821972', 22.51, 57, T / 's08.mp4'))                                     # T8 c474–530
    P.append(ventana('853972', 10.14, 78, T / 's09.mp4', por_cuadro=lambda k, f: C.destenir(f, 0.4)))   # T9 c531–608
    # T10 c609–640 y T11 c641–700 (v02): 085940 2,40–5,47 plano general (hinchas lejos). v01 usaba 326869 13,70–16,77:
    # caras de hinchas reconocibles a resolución completa.
    # ventana 1,25 anclada arriba: la tribuna queda detrás de la balanza y el plantel debajo (y > 1375), sin cruzar etiquetas
    P.append(C.real('085940', 2.40, 32, T / 's10_v02.mp4', ventana=lambda k: C.anclada(108, 0, 1.25)))
    P.append(C.real('085940', 3.47, 60, T / 's11_v02.mp4', ventana=lambda k: C.anclada(108, 0, 1.25)))
    P.append(C.propia('IMG_7887', 1.40, 3.60, T / 's12.mp4'))                                 # T12 c701–766
    P.append(C.propia('IMG_7894', 0.0, 71 / FPS, T / 's13.mp4', z0=1.03, z1=1.03))            # T13 c767–837
    n = C.armar(P, VID)
    assert n == NF, n
    json.dump(P, open(T / f'planos_{VERSION}.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('cuadros', n)


# ---------------------------------------------------------------- la balanza ----------------------------------------
PIV = (540.0, 1250.0)
S = 3                                   # supermuestreo
BX0, BY0, BW, BH = 60, 900, 960, 520    # zona de dibujo (x 60–1020, y 900–1420)
F_ET = '/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf'
_FUENTES = {}


def fuente(px):
    px = int(round(px))
    if px not in _FUENTES:
        _FUENTES[px] = ImageFont.truetype(F_ET, px)
    return _FUENTES[px]


def resorte(k, g, a0, a1, dur=12):
    """viga al ángulo nuevo con un rebote de ~30 % que se asienta en `dur` cuadros desde el golpe g"""
    u = (k - g) / dur
    if u >= 1:
        return a1
    s = 1 - (1 - u) ** 2 * math.cos(2 * math.pi * u)
    return a0 + (a1 - a0) * s


def angulo(k):
    """grados; negativo = baja Rivadavia (derecha), positivo = baja Boca (izquierda)"""
    if k < 84: a = 0.0
    elif k < 135: a = resorte(k, 84, 0, -4.5)
    elif k < 195: a = resorte(k, 135, -4.5, -9)
    elif k < 240: a = resorte(k, 195, -9, -4.5)
    elif k < 285: a = resorte(k, 240, -4.5, 0)
    elif k < 342: a = resorte(k, 285, 0, -4.5)
    elif k < 355: a = -4.5 + 2.5 * C.suave((k - 342) / 13)                  # la pesa celeste se levanta: alivia
    elif k < 361: a = -2.0 + 11.0 * (1 - (1 - (k - 355) / 6) ** 2)          # golpe fuerte: +9° en c361
    elif k < 373:
        u = (k - 361) / 12; a = 4.5 + 4.5 * (1 - u) ** 2 * math.cos(1.5 * math.pi * u)   # se asienta en +4,5° (c373)
    elif k < 486: a = 4.5
    else: a = resorte(k, 486, 4.5, 0)
    for s0 in (543, 558, 573):                                                 # los tres sellos: tiembla ±2°
        if s0 <= k < s0 + 8:
            j = k - s0; a += 2.0 * math.sin(math.pi * j / 2) * (1 - j / 8)
    amp = 1.5 if k < 84 else (0.6 if k < 609 else (0.6 * (615 - k) / 6 if k < 615 else 0.0))
    return a + amp * math.sin(2 * math.pi * k / 30)                           # vaivén (ciclo 1 s); se traba en c615


# pesas: lado, lugar en la pila, golpe (aparece 6 cuadros antes)
PESAS = [('R', 0, 84), ('R', 1, 135), ('B', 0, 195), ('B', 1, 240), ('R', 2, 285, 'celeste'), ('R', 2, 486)]


def base(theta):
    u = np.array([math.cos(theta), math.sin(theta)]); nrm = np.array([math.sin(theta), -math.cos(theta)])
    return u, nrm


def reposo(theta, lado, idx):
    u, nrm = base(theta)
    d = -280 if lado == 'B' else 280
    return np.array(PIV) + u * d + nrm * (6 + 13 + idx * 30)


def rr_poly(cx, cy, w, h, r, theta, pasos=6):
    pts = []
    for (qx, qy, a0) in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                         (-w / 2 + r, -h / 2 + r, 180)):
        for i in range(pasos + 1):
            a = math.radians(a0 + 90 * i / pasos)
            pts.append((qx + r * math.cos(a), qy + r * math.sin(a)))
    c, s = math.cos(theta), math.sin(theta)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def P_(x, y):
    return ((x - BX0) * S, (y - BY0) * S)


def dibujar(k):
    """capa RGBA (BW×BH) de la balanza en el cuadro k y alfa global"""
    a = angulo(k); th = math.radians(-a)
    u, nrm = base(th)
    im = Image.new('RGBA', (BW * S, BH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # triángulo (punta en el centro, debajo de la viga); brilla en celeste c659–671
    g = math.sin(math.pi * (k - 659) / 12) if 659 <= k <= 671 else 0.0
    tri = [P_(540, 1256), P_(510, 1306), P_(570, 1306)]
    col_tri = tuple(int(round(255 * (1 - g) + c * g)) for c in CEL)
    if g > 0:
        halo = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(halo).polygon(tri, fill=CEL + (int(255 * g),))
        halo = halo.filter(ImageFilter.GaussianBlur(14 * S))
        im = Image.alpha_composite(im, halo); d = ImageDraw.Draw(im)
    d.polygon(tri, fill=col_tri + (255,))
    # viga 640×12 con puntas redondeadas
    p0 = np.array(PIV) - u * 314; p1 = np.array(PIV) + u * 314
    d.line([P_(*p0), P_(*p1)], fill=(255, 255, 255, 255), width=12 * S)
    for p in (p0, p1):
        x, y = P_(*p); d.ellipse([x - 6 * S, y - 6 * S, x + 6 * S, y + 6 * S], fill=(255, 255, 255, 255))
    # pesas
    for pz in PESAS:
        lado, idx, gol = pz[:3]; cel = len(pz) > 3
        if k < gol - 6:
            continue
        if cel and k >= 342:
            if k < 345:                                  # sube
                c = reposo(th, 'R', 2) + nrm * (30 * (k - 341) / 4)
            elif k < 355:                                # salta en arco de Rivadavia a Boca (techo 140 px)
                uu = C.suave((k - 345) / 10)
                s0 = reposo(th, 'R', 2) + nrm * 30; e0 = reposo(th, 'B', 2)
                c = s0 + (e0 - s0) * uu - np.array([0, 140 * 4 * uu * (1 - uu)])
            else:
                c = reposo(th, 'B', 2)
        elif k < gol:                                    # cae con aceleración
            j = k - (gol - 6)
            c = reposo(th, lado, idx) - np.array([0, 230 * (1 - (j / 6) ** 2)])
        else:
            c = reposo(th, lado, idx)
        relleno = CEL if (cel and k >= 342) else (255, 255, 255)
        borde, ancho = (CEL, 4) if (cel and k >= gol) else (OSC, 2)
        poly = [P_(x, y) for x, y in rr_poly(c[0], c[1], 72, 26, 6, th)]
        al = 255 if k >= gol - 4 else 170
        d.polygon(poly, fill=relleno + (al,), outline=borde + (al,), width=ancho * S)
    # etiquetas derechas: siguen la altura de cada punta, 30 px por debajo
    # la etiqueta queda 30 px por debajo de la viga en todo su ancho (con la viga inclinada, el tramo interior de la
    # viga puede quedar más bajo que la punta)
    yv = lambda x: PIV[1] + (x - PIV[0]) * math.tan(th)
    wb = fuente(50).getlength('BOCA'); w1 = fuente(50 * S).getlength('RIVADAVIA')
    yb = max(yv(PIV[0] - 320 * math.cos(th)), yv(150 + wb))
    yr = max(yv(PIV[0] + 320 * math.cos(th)), yv(930 - w1 / S))
    d.text(P_(150, yb + 36), 'BOCA', font=fuente(50 * S), fill=(255, 255, 255, 255), anchor='lt')
    sc = 1 + 0.12 * math.sin(math.pi * (k - 440) / 12) if 440 <= k <= 452 else 1.0
    f = fuente(50 * S * sc)
    wr = f.getlength('RIVADAVIA')
    xr, yr0 = P_(930, yr + 36)
    d.text((xr + (wr - w1) / 2, yr0 - (sc - 1) * 25 * S), 'RIVADAVIA', font=f, fill=(255, 255, 255, 255), anchor='rt')
    capa = im.resize((BW, BH), Image.LANCZOS)
    alfa = 1.0 if k < 701 else max(0.0, 1 - (k - 701) / 6)
    return capa, alfa


_BANDA = None


def banda():
    global _BANDA
    if _BANDA is None:
        y = np.arange(H, dtype=np.float32)
        b = np.where((y >= 1120) & (y <= 1400), np.sin(np.pi * (y - 1120) / 280) ** 2, 0.0)   # sin²: sin borde visible
        _BANDA = b[:, None, None]
    return _BANDA


def barra():
    nb = W * H * 3
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(VID), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = C.encoder(VID_B)
    k = 0
    while True:
        b = dec.stdout.read(nb)
        if len(b) < nb:
            break
        fr = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32)
        capa, alfa = dibujar(k) if k < 707 else (None, 0.0)
        if alfa > 0:
            if any(a0 <= k < a1 for a0, a1 in VERT):
                fr *= 1 - 0.5 * alfa * banda()
            ca = np.asarray(capa, np.float32) / 255
            A = ca[..., 3:4] * alfa
            sh = Image.fromarray((ca[..., 3] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))
            sha = np.zeros_like(A[..., 0]); sha[2:] = (np.asarray(sh, np.float32) / 255)[:-2]
            sub = fr[BY0:BY0 + BH, BX0:BX0 + BW]
            sub *= (1 - 0.6 * alfa * sha)[..., None]
            sub[:] = sub * (1 - A) + ca[..., :3] * 255 * A
        enc.stdin.write(fr.round().clip(0, 255).astype(np.uint8).tobytes())
        k += 1
    dec.stdout.close(); dec.wait(); enc.stdin.close(); enc.wait()
    assert k == NF, k
    print('barra', k)


# ---------------------------------------------------------------- textos --------------------------------------------
V.ESTILOS.update({
    'CajaN_ctx40': ('Inter Display SemiBold', 40, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 11, 0, 3, 8, 0),
    # sellos de T9: 44 px (el guion pedía 56): a 56 px «Por penales con Atlético Tucumán.» tapaba la marca de TyC
    'Sello56': ('Inter Display ExtraBold', 44, '&H00FFFFFF', '&H00000000', '&H80000000', 0, 4, 0, 1, 8, 0),
})
ALTO = {'CajaN_hook': (120, 33), 'CajaN_96': (96, 26), 'CajaN_84': (84, 23), 'CajaN_125': (72, 20), 'CajaN_ctx': (54, 15),
        'CajaN_ctx40': (40, 11)}


def alto(estilo, txt):
    fs, b = ALTO[estilo]
    return (txt.count('\\N') + 1) * fs * 1.21 + 2 * b


def textos():
    X = []

    def caja(a, b, txt, y, estilo=None, maximo='CajaN_hook', **kw):
        est = estilo or C.caja(txt, maximo)
        kw.setdefault('pop', True)
        X.append(dict(t0=tx(a), t1=tx(b), txt=txt, estilo=est, y=y, **kw))
        return y + alto(est, txt)

    y = caja(0, 72, 'Boca festejó\\Nhasta el lunes.', C.Y_HOOK, 'CajaN_hook')                       # APUESTA
    caja(30, 72, '¿Llega con todo hoy?', y + 18, 'CajaN_84')
    caja(72, 123, 'Copa en andas\\Nhasta la madrugada.', 245)                                        # pista en contra
    y = caja(123, 183, 'Partido único:\\Nsi pierde, afuera.', 245)                                   # sube
    caja(147, 183, 'Empate: alargue y penales.', y + 14, maximo='CajaN_84')
    # pista a favor ×2. Las dos frases van en el mismo lugar, una después de la otra: apiladas, la segunda tapaba a
    # medias la marca de agua de TyC (arriba a la derecha de la ventana, x 907–1007, y 513–563) y no entra centrada
    # en menos de 734 px.
    caja(183, 228, 'Boca: 2.º de su zona,\\N33 puntos.', 245, 'CajaN_84')
    caja(228, 273, 'Independiente Rivadavia:\\N7.º de la suya.', 245, 'CajaN_84')
    caja(273, 336, 'El plan del Vasco\\Nera rotar.', 245)                                            # pista en contra
    # GIRO. v02: T6 es ventana: la caja sube a y=225 para terminar antes de la marca de TyC (y≈515)
    y = caja(336, 423, 'Los titulares le dijeron\\Nque quieren estar.', 225, 'CajaN_96')
    caja(336, 423, 'minutouno, 23/11', y + 14, 'CajaN_ctx40', pop=False)
    # T7 y T9: columna centrada en x=440 (no 540): la marca de agua de TyC ocupa x≈850–1010, y≈515–570 del cuadro
    y = caja(423, 474, '¿Ya está?', C.Y_HOOK, 'CajaN_hook', x=440)                                   # REENGANCHE
    caja(440, 474, 'Rivadavia también\\Nestuvo arriba.', y + 14, 'CajaN_125', x=440)
    caja(474, 531, 'Fue puntero de la tabla anual\\Nbuena parte del año.', 245, maximo='CajaN_96')   # pista en contra
    y = caja(531, 609, 'Y se cayó:', 245, 'CajaN_96', x=430)                                         # la caída
    for i, (c0, s) in enumerate(((543, 'Afuera con Fluminense.'), (558, 'Por penales con Atlético Tucumán.'),
                                 (573, 'Derrota con Estudiantes.'))):
        X.append(dict(t0=tx(c0), t1=tx(609), txt=s, estilo='Sello56', x=430, y=int(y + 18 + i * 64), pop=True))
    caja(609, 641, 'Estar arriba\\Nno alcanza.', 245, 'CajaN_96')                                    # traba
    y = caja(641, 701, 'Queda en el medio.', 245, 'CajaN_96')                                        # resolución en suspenso
    caja(659, 701, 'Se define hoy a las 21:00.', y + 14, 'CajaN_84')
    caja(701, 767, 'La disciplina empieza\\Nel día después.', 300, 'CajaN_84')                       # VALOR
    y = caja(767, NF, '¿Para dónde la inclinás vos?', 235, 'CajaN_ctx', pop=False)                   # CTA (Roma 25/11)
    caja(767, NF, 'Comentalo antes\\Nde las 21:00.', y + 12, 'CajaN_96')
    return X


def ficha_logo(lado=120):
    """logo original escalado sin deformar, sobre su fondo #FEFEFE, esquinas redondeadas (radio 12 %)"""
    lg = Image.open(LOGO).convert('RGB')
    assert lg.size == (1254, 1254), lg.size
    base_ = Image.new('RGB', lg.size, (254, 254, 254)); base_.paste(lg, (0, 0))
    sm = base_.resize((lado, lado), Image.LANCZOS)
    m = Image.new('L', (lado * 4, lado * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, lado * 4 - 1, lado * 4 - 1], radius=int(0.12 * lado * 4), fill=255)
    m = m.resize((lado, lado), Image.LANCZOS)
    out = sm.convert('RGBA'); out.putalpha(m)
    p = T / 'logo_ficha_120.png'; out.save(p)
    return p


# ---------------------------------------------------------------- sonido --------------------------------------------
def audio():
    DUR = NF / FPS
    m = C.MezclaB(DUR)
    OV = C.clip('425095')          # ovación real de la Bombonera para el Vasco (07/11): ruido de multitud, sin música medida
    # hinchada real (sin escuchar: elegida por nivel y espectro; ver informe)
    m.real(OV, 0.00, t(0), t(72), -9, hp=80, ini=0.02, fin=0.02, etiqueta='hinchada 425095')
    m.real(OV, 2.40, t(72), t(123), -16, hp=150, lp=6000, ini=0.02, fin=0.02, etiqueta='hinchada lejana 425095')
    m.real(OV, 4.10, t(123), t(183), -8, hp=80, ini=0.02, fin=0.02, etiqueta='hinchada 425095')
    m.real(OV, 6.10, t(183), t(273), -14, hp=120, ini=0.02, fin=0.02, etiqueta='hinchada 425095')
    m.real(OV, 9.10, t(273), t(336), -6, hp=80, ini=0.02, fin=0.03, etiqueta='ovación para el Vasco 425095')
    m.real(OV, 0.50, t(336), t(609), -20, hp=150, ini=0.05, fin=0.2, etiqueta='hinchada baja bajo la música')
    m.real(OV, 9.40, t(609), t(701), -18, hp=120, ini=0.1, fin=0.3, etiqueta='hinchada baja 425095')
    m.toma('IMG_7887', 1.40, t(701), t(767), -8, ini=0.15, fin=0.04)
    m.toma('IMG_7894', 0.00, t(767), t(NF), -8, ini=0.04, fin=0.05)
    # efectos
    m.latido(t(0), 0.5); m.latido(t(30), 0.55)
    for c, g in ((84, 0.5), (135, 0.55), (195, 0.5), (240, 0.5), (285, 0.55)):
        m.golpe_sordo(t(c), g)
    m.subida(t(147), t(183), 0.14)
    m.toque(t(252), 0.25, 2600); m.log(t(252), 'clic')
    m.latido(t(329), 0.55)
    m.impacto(t(336), 0.6)
    m.barrido(t(350), 0.33, 0.22)
    m.golpe_sordo(t(355), 1.0); m.impacto(t(355), 0.45)          # v02: +1,5 dB (golpe/fondo era +7 dB)
    m.latido(t(440), 0.5)
    m.golpe_sordo(t(486), 1.1)                                    # v02: pesado (golpe/fondo era +8 dB)
    for c in (543, 558, 573):
        m.bombo(t(c), 1.15, f0=150, f1=55, dec=0.12, pista='fx'); m.toque(t(c), 0.25, 1800); m.log(t(c), 'golpe seco')
    m.toque(t(615), 0.32, 2600); m.log(t(615), 'clic (traba)')
    m.latido(t(659), 0.5)
    # música propia sintetizada (TEMP)
    m.pad(t(0), [33, 45, 52], t(336), 0.045, corte=700)                     # pad grave de la apuesta
    b = 0.5                                                                   # 120 BPM: un tiempo = 15 cuadros
    k = 0; t0 = t(336)
    while t0 + k * b < t(609) - 0.05:
        tt = t0 + k * b
        lleno = tt < t(531)
        if k % 4 == 0:
            if lleno: m.bombo(tt, 0.8)
            m.ocho08(tt, [33, 33, 36, 31][(k // 4) % 4], b * 3.6, 0.45 if lleno else 0.25)
        if k % 4 == 2 and lleno:
            m.palma(tt, 0.26); m.bombo(tt + b * 0.5, 0.45)
        m.charles(tt, 0.08 if lleno else 0.05); m.charles(tt + b / 2, 0.05 if lleno else 0.03)
        k += 1
    m.pad(t(336), [45, 52, 57, 60], t(609) - t(336), 0.04, corte=1500)
    m.silenciar('mus', t(609), t(611), rampa=0.01)                           # la música se corta en c609
    m.silenciar('bombo', t(609), t(NF), rampa=0.01)
    m.pad(t(609), [33, 45, 48, 52], t(701) - t(609), 0.05, corte=800)       # queda el pad
    m.pad(t(701), [33, 45, 52, 57, 61], t(826) - t(701), 0.05, corte=1200)  # el pad resuelve
    # v02: en T9 la música se adelgaza −6 dB para que se oigan los tres golpes secos (en v01 quedaban +2/+3 dB)
    i0, i1 = int(t(531) * C.SR), int(t(609) * C.SR)
    m.pistas['mus'][i0:i1] *= C.db(-6)
    # c327–336: casi silencio (todo −30 dB menos el latido)
    for p in ('amb', 'mus', 'fx'):
        i0, i1 = int(t(327) * C.SR), int(t(336) * C.SR)
        m.pistas[p][i0:i1] *= C.db(-30)
    for p in ('amb', 'mus', 'fx', 'bombo'):
        m.fundido(p, t(812), t(826))                                         # fundido que termina en c826
    (T / 'audio').mkdir(exist_ok=True)
    r = m.exportar(str(T / 'audio' / f'p4_completa_{VERSION}.wav'), lufs=-14)
    print('audio', r)


def master():
    a = V.ass(textos(), T / f'p4_{VERSION}.ass')
    logo = ficha_logo(120)
    V.master(VID_B, T / 'audio' / f'p4_completa_{VERSION}.wav', MASTER_T, ass_path=a,
             overlays=[(logo, 480, 1270, t(767), t(NF))])
    print(MASTER_T)


def control():
    CONTROL.mkdir(parents=True, exist_ok=True)
    # hoja de contacto cada 0,5 s (15 cuadros): 56 cuadros en 8×7, con tiempo y número de cuadro
    C.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(MASTER_T), '-vf',
          "select='not(mod(n\\,15))',scale=216:-2,drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-Bold.otf:"
          "text='%{pts\\:hms} c%{n}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=8x7:padding=2",
          '-frames:v', '1', '-fps_mode', 'vfr', str(CONTROL / f'P4_{VERSION}_hoja_0.5s.jpg')])
    for c in sorted(set([0, 30, 84, 96, 147, 252, 297, 342, 350, 355, 361, 373, 440, 498, 545, 560, 575, 615, 665,
                         705, 770, 837] + [x for c0 in CORTES[1:] for x in (c0 - 1, c0)])):
        V.cuadro(MASTER_T, c, CONTROL / f'P4_{VERSION}_c{c:03d}.jpg')
    for c in (40, 300, 380, 450, 600, 690, 800):
        V.cuadro(MASTER_T, c, CONTROL / f'P4_{VERSION}_360_c{c:03d}.png', escala=360)


def entregar():
    """copia el máster a la carpeta de la pieza sin pisar una versión existente"""
    if SALIDA.exists():
        raise FileExistsError(f'{SALIDA} ya existe: subir la versión')
    shutil.copy2(MASTER_T, SALIDA)
    print(SALIDA)


if __name__ == '__main__':
    T.mkdir(parents=True, exist_ok=True)
    et = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    if et in ('planos', 'todo'): planos()
    if et in ('barra', 'todo'): barra()
    if et in ('audio', 'todo'): audio()
    if et in ('master', 'todo'): master()
    if et in ('control', 'todo'): control()
    if et in ('entregar', 'todo'): entregar()
