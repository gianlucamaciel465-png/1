#!/usr/bin/env python3
"""BOC-25 P2 «La copa sale seguro» · receta v01 (25/11/2026, Pedro).

Guion: guiones/P2_G1_fede.md con los cambios de Roma (guiones/P2_G1_roma.md): CTA «Etiquetá al que dice que hoy no está.».
30 fps, 723 cuadros (24,1 s). Clips oficiales de terceros (TikTok @bocajuniors, @sudamericana, @ligaprofesional): ver
material/inventario_clips.md. Motor: scripts/bocsud/comun.py (C) + scripts/fmt/video.py (V).

Cambios de tramo respecto del guion (todos medidos con fotogramas ampliados de la fuente, ver 06_pedro_P2.md):
  B5  …021013 empieza en 14,00 (el guion cruzaba el corte de la fuente en 13,733 s).
  B6/R el clip …205396 del guion es un entrenamiento de juveniles (no aparece Paredes, «betsson» en carteles y pecheras):
      se reemplaza por el primer plano real de Paredes en la Bombonera (…252680, 07/11): B6 3,00–4,20 (besa el escudo),
      R 0,30–3,00 (camina hacia la gente con el brazo en alto; la «5» en el pantalón).
  B7/B8 …217426 23,45–24,95 y 24,95–26,95 (desde 27,1 entra el 19 con «betsson» en el pecho).
  F1  …415476 10,30 (la copa más grande que en 8,42) · F2 …021013 13,30 (la copa en la mano, antes del corte de 13,733).
  G   …252680 10,90–12,47 a media velocidad (60 → 30 fps, cuadro por cuadro): en 6,27 hay un cartel vertical «betsson»
      legible y la cinta LED pasa por detrás de la cabeza hasta ≈10,9. Barra del título opaca que sigue la cinta LED
      (detectada por cuadro), marca de agua LPF repuesta encima de la barra (máscara estática por varianza temporal) y
      desenfoque localizado de la cinta LED inferior a la derecha del torso.

Etapas: python3 p2.py planos | trans | audio | master | control | todo
"""
import sys, json, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, '/home/user/1/scripts/bocsud')
import comun as C
V = C.V

R = Path('/home/user/1')
T = R / 'TRABAJO' / 'boc25' / 'p2'
PIEZA = Path('/mnt/project-files/piezas/BOC-25_octavos_hoy')
CONTROL = PIEZA / 'control'
SALIDA = T / 'p2_master_v01.mp4'
ENTREGA = PIEZA / 'ROCCE_BOC25_P2_LA_COPA_SALE_SEGURO_v01.mp4'
FPS, NF = 30, 723
W, H = 1080, 1920
NAVY = (11, 26, 58)
F_BOLD = '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
LOGO = R / 'LOGO' / 'rocce_logo.png'

# clips (id6 = últimos dígitos del id de TikTok)
VIAJE = '897415476'      # 7711204482897415476 @bocajuniors 23/11 «Llegó papá a Argentina»
ARCO = '344363568392'    # 7710800344363568392 @sudamericana 21/11 levanta el trofeo
PISTA = '547532021013'   # 7711083547532021013 @bocajuniors 22/11 llevando la copa
VASCO = '604023217426'   # 7710823604023217426 @sudamericana 21/11 pitazo final, el Vasco
BOMBO = '403848252680'   # 7705576403848252680 @ligaprofesional 07/11 Paredes, el emblema (60 fps)
OVACION = '908210425095'  # 7705572908210425095 @ligaprofesional 07/11 ovación de la Bombonera (sonido)

G_T0 = 10.90             # segundo de la fuente del primer cuadro de G (60 fps, uno a uno)
G_N = 94


# ---------------- G: barra sobre la cinta LED, marca de agua encima, desenfoque de la cinta inferior ----------------
def cinta_superior(cuadros):
    """borde inferior (y) de las letras blancas de la cinta LED superior en cada cuadro (x 0–700, y 360–640)"""
    out = []
    for a in cuadros:
        reg = a[360:640, 0:700].astype(np.int16)
        mn, mx = reg.min(2), reg.max(2)
        blanco = (mn > 165) & ((mx - mn) < 80)
        filas = blanco.sum(1)
        ok = np.nonzero(filas >= 10)[0]
        if len(ok) == 0:
            out.append(None); continue
        # grupo contiguo más poblado (las letras), con huecos de hasta 4 filas
        grupos, ini, prev = [], ok[0], ok[0]
        for y in ok[1:]:
            if y - prev > 4:
                grupos.append((ini, prev)); ini = y
            prev = y
        grupos.append((ini, prev))
        g = max(grupos, key=lambda p: filas[p[0]:p[1] + 1].sum())
        out.append((360 + g[0], 360 + g[1]))
    return out


def mascara_marca(id6):
    """marca de agua fija de la cuenta (LPF + TORNEO CLAUSURA + mercado libre): píxeles casi quietos en todo el clip
    (la cámara se mueve todo el tiempo). Caja x 860–1070, y 200–540."""
    x0, y0, w, h = 860, 200, 210, 340
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(C.clip(id6)), '-vf', f'fps=12,crop={w}:{h}:{x0}:{y0}',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32)
    sd = a.std(0).mean(2)
    m = (sd < 9).astype(np.uint8) * 255
    mi = Image.fromarray(m).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
    full = np.zeros((H, W), np.float32)
    full[y0:y0 + h, x0:x0 + w] = np.asarray(mi, np.float32) / 255
    Image.fromarray((full * 255).astype(np.uint8)).save(T / 'g_mascara_marca.png')
    return full


def limite_cinta_inferior(ts):
    """x desde donde se desenfoca la cinta LED inferior (a la derecha del torso), por segundo de la fuente"""
    kf = [(10.90, 760), (11.05, 740), (11.30, 860), (11.55, 890), (11.80, 905), (12.00, 980), (12.12, 1080), (12.50, 1080)]
    xs = [k[0] for k in kf]; ys = [k[1] for k in kf]
    return float(np.interp(ts, xs, ys))


def plano_g(salida):
    src = C.clip(BOMBO)
    vf = f'setpts=N/({FPS}*TB)'
    cuadros = C.leer_video(src, G_T0, G_N / FPS, W, H, vf)
    det = cinta_superior(cuadros)
    fondo = [d[1] if d else None for d in det]
    # relleno de huecos y margen: el borde de la barra cubre el máximo de ±2 cuadros + 12 px
    ys = np.array([f if f is not None else np.nan for f in fondo], np.float64)
    idx = np.arange(len(ys)); ok = ~np.isnan(ys)
    ys = np.interp(idx, idx[ok], ys[ok])
    borde = np.array([ys[max(0, k - 2):k + 3].max() for k in range(len(ys))]) + 12
    borde = np.convolve(np.pad(borde, 2, mode='edge'), np.ones(5) / 5, 'valid')
    borde = np.maximum(borde, np.array([ys[max(0, k - 2):k + 3].max() + 8 for k in range(len(ys))]))
    marca = mascara_marca(BOMBO)[..., None]
    alto = 150
    # 88 px centrado en x 450: termina antes de la marca de agua de la cuenta (x ≥ 900), que queda encima de la barra
    fnt = ImageFont.truetype(F_BOLD, 88)
    txt = 'La copa sale seguro.'
    tw = fnt.getlength(txt)
    X_TIT = 450
    enc = C.encoder(salida)
    reg = []
    for k, a in enumerate(cuadros):
        ts = G_T0 + k / 60
        orig = a.astype(np.float32)
        im = Image.fromarray(a)
        # cinta LED inferior: desenfoque fuerte a la derecha del torso
        xl = int(round(limite_cinta_inferior(ts)))
        if xl < W:
            y1, y2 = 840, 995
            caja = (max(xl - 30, 0), y1 - 20, W, y2 + 20)
            parte = im.crop(caja)
            bl = parte.filter(ImageFilter.GaussianBlur(11))
            mk = Image.new('L', parte.size, 0)
            ImageDraw.Draw(mk).rectangle([30, 20, parte.size[0], 20 + (y2 - y1)], fill=255)
            mk = mk.filter(ImageFilter.GaussianBlur(9))
            im.paste(Image.composite(bl, parte, mk), caja[:2])
        b = int(round(borde[k])); t = b - alto
        d = ImageDraw.Draw(im)
        d.rectangle([0, t, W, b], fill=NAVY)
        d.text((X_TIT - tw / 2, t + alto / 2), txt, font=fnt, fill=(255, 255, 255), anchor='lm')
        arr = np.asarray(im, np.float32)
        arr = arr * (1 - marca) + orig * marca          # la marca de agua de la cuenta queda entera, encima
        enc.stdin.write(arr.round().clip(0, 255).astype(np.uint8).tobytes())
        reg.append(dict(k=k, fuente=round(ts, 3), letras=det[k], barra=(t, b), desenfoque_x=xl))
    enc.stdin.close(); enc.wait()
    json.dump(reg, open(T / 'g_barra.json', 'w'), indent=0, default=str)
    return dict(clip=BOMBO, desde=G_T0, cuadros=len(cuadros), salida=str(salida), uno_a_uno=True,
                barra='opaca navy, sigue la cinta LED', marca='repuesta encima')


def plano_b8():
    """B8 c321–380: acercamiento 1,00→1,12 en 6 cuadros y deriva vertical. La ventana queda pegada al borde izquierdo
    (cx ≤ 0,446 con 1,12) para que la marca de agua CONMEBOL de arriba a la izquierda quede entera; la «5» entra a la derecha."""
    def v_b8(k):
        if k < 6:
            u = C.suave((k + 1) / 6); return (0.5 - 0.06 * u, 0.5 - 0.05 * u, 1.0 + 0.12 * u)
        u = (k - 6) / 53
        return (0.44, 0.45 - 0.05 * u, 1.12)
    return C.real(VASCO, 24.95, 60, T / 's08_b8.mp4', ventana=v_b8)


# ---------------- planos ----------------
def planos():
    T.mkdir(parents=True, exist_ok=True)
    P = []
    # B1 c0–71 APUESTA: Paredes baja la escalera con la copa (ventana anclada arriba: el cielo queda para el gancho)
    P.append(C.real(VIAJE, 6.73, 72, T / 's01_b1.mp4', ventana=lambda k: C.anclada(90, 0, 1.10 + 0.05 * k / 71)))
    # B2 c72–113 la copa en el arco (sin acercar: la marca de agua CONMEBOL queda entera y fuera del encabezado)
    P.append(C.real(ARCO, 4.60, 42, T / 's02_b2.mp4'))
    # B3 c114–161 placa azul noche plana, sin imagen ni efecto
    P.append(C.negro(48 / FPS, T / 's03_b3.mp4', color=NAVY))
    # B4 c162–200 abajo de la escalera, la copa a la derecha
    P.append(C.real(VIAJE, 10.10, 39, T / 's04_b4.mp4', c0=(0.55, 0.40), z0=1.06, z1=1.10))
    # B5 c201–239 el plantel en la pista (después del corte de la fuente en 13,733 s)
    P.append(C.real(PISTA, 14.00, 39, T / 's05_b5.mp4', c0=(0.52, 0.47), z0=1.25, z1=1.30))
    # B6 c240–275 primer plano: besa el escudo (Bombonera 07/11); ventana anclada a la izquierda y arriba
    P.append(C.real(BOMBO, 3.00, 36, T / 's06_b6.mp4', ventana=lambda k: C.anclada(0, 0, 1.22 + 0.04 * k / 35)))
    # B7 c276–320 el Vasco abraza al 5
    P.append(C.real(VASCO, 23.45, 45, T / 's07_b7.mp4', c0=(0.45, 0.50), z0=1.08, z1=1.12))
    P.append(plano_b8())
    # F1 c381–390 la copa en su mano (acercamiento rápido)
    P.append(C.real(VIAJE, 10.30, 10, T / 's09_f1.mp4', ventana=lambda k: (0.86, 0.215, 1.7 + 0.8 * C.suave((k + 1) / 10))))
    # F2 c391–400 la copa en la mano, pista de Barranquilla
    P.append(C.real(PISTA, 13.30, 10, T / 's10_f2.mp4', ventana=lambda k: (0.25, 0.36, 1.5 + 0.7 * C.suave((k + 1) / 10))))
    # G c401–494 GIRO
    P.append(plano_g(T / 's11_g.mp4'))
    # R c495–575 REENGANCHE: camina hacia la gente, brazo en alto (sin acercar: la marca de agua queda entera)
    P.append(C.real(BOMBO, 0.30, 81, T / 's12_r.mp4'))
    # C1 c576–647 la Negra de espaldas (IMG_7793) · C2 c648–722 la Blanca en la roca (IMG_4627, ya en SDR)
    P.append(C.propia('IMG_7793', 2.40, 4.80, T / 's13_c1.mp4', z0=1.0, z1=1.03))
    P.append(C.propia('IMG_4627', 2.00, 4.50, T / 's14_c2.mp4', z0=1.0, z1=1.03))
    n = C.armar(P, T / 'p2_video.mp4')
    assert n == NF, n
    json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('cuadros', n)


TRANS = {381: 'zoom', 391: 'zoom', 401: 'destello'}


def trans():
    C.transiciones(T / 'p2_video.mp4', T / 'p2_video_t.mp4', TRANS, NF)
    print('transiciones', TRANS)


# ---------------- textos ----------------
V.ESTILOS.update({
    # familia «Inter Display» con negrita (-1): fontconfig elige InterDisplay-Bold.otf (por nombre completo salía Regular)
    'P2_hook': ('Inter Display', 104, '&H00FFFFFF', '&H66000000', '&H99000000', -1, 3, 4, 1, 8, 0),
    'P2_main': ('Inter Display', 88, '&H00FFFFFF', '&H66000000', '&H99000000', -1, 2.6, 4, 1, 8, 0),
    'P2_src': ('Inter Display', 34, '&H4CFFFFFF', '&H80000000', '&HA0000000', -1, 1.6, 2, 1, 8, 0),
    'P2_chico': ('Inter Display', 40, '&H00FFFFFF', '&H66000000', '&H99000000', -1, 2, 3, 1, 8, 0),
    'P2_head': ('Inter', 40, '&H00FFFFFF', '&H4C3A1A0B', '&H4C3A1A0B', -1, 14, 0, 3, 8, 0),
    'P2_esq': ('Inter Display', 34, '&H1AFFFFFF', '&H80000000', '&HA0000000', -1, 1.6, 2, 1, 7, 0),
})
_F88 = ImageFont.truetype(F_BOLD, 88)


def partir(txt, fs=88, maximo=800):
    """un renglón si entra en `maximo` px; si no, dos renglones lo más parejos posible"""
    f = _F88 if fs == 88 else ImageFont.truetype(F_BOLD, fs)
    if f.getlength(txt) <= maximo:
        return txt, 1
    pal = txt.split(' ')
    mejor = min(range(1, len(pal)), key=lambda i: max(f.getlength(' '.join(pal[:i])), f.getlength(' '.join(pal[i:]))))
    return ' '.join(pal[:mejor]) + '\\N' + ' '.join(pal[mejor:]), 2


def tx(c):
    return max(c / FPS - 0.004, 0.0)


def textos():
    X = []

    def apoyo(a, b, x0, y0, w, h):
        """apoyo de lectura: rectángulo negro translúcido muy difuminado detrás del texto (capa 0)"""
        X.append(dict(t0=tx(a), t1=tx(b), estilo='P2_main', x=int(x0), y=int(y0), blur=False, capa=0,
                      extra='\\an7\\p1\\bord0\\shad0\\1c&H000000&\\1a&H78&\\blur22',
                      txt=f'm 0 0 l {int(w)} 0 {int(w)} {int(h)} 0 {int(h)}{{\\p0}}'))

    def linea(a, b, txt, y, fuente=None, fs=88, estilo='P2_main'):
        t, n = partir(txt, fs)
        ancho = max(_F88.getlength(r) for r in t.split('\\N')) + 110
        alto = n * 104 + (44 if fuente else 0) + 44
        apoyo(a, b, 540 - ancho / 2, y - 22, ancho, alto)
        X.append(dict(t0=tx(a), t1=tx(b), txt=t, estilo=estilo, y=y, pop=True, capa=1))
        if fuente:
            X.append(dict(t0=tx(a), t1=tx(b), txt=fuente, estilo='P2_src', y=y + n * 104 + 4, capa=1))
    # B1 APUESTA (gancho en el cielo, sobre Paredes)
    apoyo(0, 72, 540 - 400, 280, 800, 260)
    X.append(dict(t0=tx(0), t1=tx(72), txt='¿Llega Paredes\\Na las 21?', estilo='P2_hook', y=296, pop=True, capa=1))
    X.append(dict(t0=tx(6), t1=tx(72), txt='Hoy · Boca · octavos', estilo='P2_chico', y=228))
    # encabezado fijo c72–c400
    X.append(dict(t0=tx(72), t1=tx(401), txt='¿LLEGA A LAS 21?', estilo='P2_head', y=238))
    linea(72, 114, 'Sábado: levantó la copa.', 600)
    linea(114, 162, 'Después de la final, se descompensó.', 820, 'minutouno · 23/11')
    linea(162, 201, 'Los estudios: bien.', 1150, 'minutouno · 23/11')
    linea(201, 240, 'Entrenó con el grupo.', 560, 'Río Negro · 24/11')
    linea(240, 276, 'Quiere jugar.', 1000, 'minutouno · 23/11')   # tapa el pecho (patrocinio) sin tapar la cara
    linea(276, 321, 'Puede arrancar en el banco.', 560, 'La Gaceta · 24/11')
    linea(321, 381, 'Si no está, entra Belmonte.', 560, 'Río Negro · 24/11')
    # G: el título va dentro de la barra (plano_g); segunda línea, fuente y lugar
    linea(431, 495, 'La saca él, ante la gente.', 1130, 'Diario Hoy · 25/11')
    apoyo(401, 495, 30, 226, 390, 64)
    X.append(dict(t0=tx(401), t1=tx(495), txt='La Bombonera · 07/11', estilo='P2_esq', y=236, x=48, capa=1))
    # R
    linea(495, 576, '¿Y la 5, desde el arranque?', 860)   # sobre el pecho (patrocinio) en el tramo cercano
    linea(527, 576, 'Lo contesta la formación, antes de las 21.', 1132)
    # C1, C2
    linea(582, 648, 'La presencia no depende de la formación.', 1170)
    linea(648, 723, 'Etiquetá al que dice que hoy no está.', 640)
    return X


def ficha_logo(lado=150):
    """logo original escalado (sin deformar) sobre su fondo #FEFEFE, esquinas redondeadas radio 12 %"""
    im = Image.open(LOGO).convert('RGB').resize((lado, lado), Image.LANCZOS)
    S = 4
    m = Image.new('L', (lado * S, lado * S), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, lado * S - 1, lado * S - 1], radius=int(0.12 * lado * S), fill=255)
    m = m.resize((lado, lado), Image.LANCZOS)
    out = Image.new('RGBA', (lado, lado)); out.paste(im, (0, 0)); out.putalpha(m)
    p = T / 'logo_ficha_150.png'; out.save(p)
    return p


# ---------------- sonido ----------------
def audio():
    t = lambda c: c / FPS
    DUR = NF / FPS
    m = C.MezclaB(DUR)
    # B1: ambiente bajo de la llegada (clip …415476; tiene un tono estable de motor: va bajo y filtrado)
    m.real(C.clip(VIAJE), 6.73, t(0), t(72), -20, hp=120, lp=2500, ini=0.02, fin=0.05, etiqueta='ambiente llegada')
    # B2: hinchada real de la final (golpe corto 1,4 s; fuente sin picos tonales persistentes)
    m.real(C.clip(ARCO), 4.60, t(72), t(114), 8, hp=100, ini=0.01, fin=0.03, etiqueta='hinchada final (arco)')
    # B3: corte seco a casi silencio (solo el zumbido de la música)
    # B4–B6 aire bajo: B4 llegada, B5 sin sonido de fuente (…021013 trae picos tonales: posible música), B6 Bombonera
    m.real(C.clip(VIAJE), 10.10, t(162), t(201), -22, hp=120, lp=2500, ini=0.01, fin=0.02, etiqueta='ambiente llegada')
    m.real(C.clip(BOMBO), 3.00, t(240), t(276), -16, ini=0.01, fin=0.02, etiqueta='hinchada Bombonera (bajo)')
    # B7–B8 hinchada de la final, baja; c369–380 casi silencio
    m.real(C.clip(VASCO), 23.45, t(276), t(369), -14, hp=100, ini=0.01, fin=0.03, etiqueta='hinchada final (Vasco)')
    # G: hinchada de la Bombonera a pleno (ovación del mismo partido, 07/11)
    m.real(C.clip(OVACION), 3.00, t(401), t(495), -6, ini=0.005, fin=0.05, etiqueta='hinchada Bombonera (ovación) a pleno')
    # R: hinchada −8 dB
    m.real(C.clip(OVACION), 6.13, t(495), t(576), -14, ini=0.05, fin=0.3, etiqueta='hinchada Bombonera −8 dB')
    # C1: la hinchada se funde con el ambiente de la toma; C2: la ola y el mar
    m.real(C.clip(OVACION), 8.83, t(576), t(612), -20, ini=0.05, fin=1.0, etiqueta='hinchada que se funde')
    m.toma('IMG_7793', 2.40, t(576), t(648), -10, ini=0.4, fin=0.1)
    m.toma('IMG_4627', 2.00, t(648), t(723), -6, ini=0.03, fin=0.4)
    # reloj: tic-tac cada 0,5 s de c0 a c400 (se apaga en el giro)
    for i, c in enumerate(range(0, 401, 15)):
        if c in (0,):
            continue
        m.toque(t(c), 0.10 if i % 2 else 0.13, 2600 if i % 2 else 2100)
    m.toque(t(0), 0.35, 1800); m.log(0, 'tic seco')
    for c in (162, 201):
        m.toque(t(c), 0.30, 3400); m.log(t(c), 'clic agudo')
    m.toque(t(240), 0.30, 3400); m.log(t(240), 'clic agudo')
    m.subida(t(242), t(276), 0.07)
    for c in (276, 321):
        m.toque(t(c), 0.45, 650); m.bombo(t(c), 0.25, f0=160, f1=70, dec=0.08); m.log(t(c), 'clic grave')
    m.toque(t(114), 0.2, 900)
    for c in (381, 391):
        m.barrido(t(c), 0.22, 0.16)
    # giro
    m.impacto(t(401), 0.6); m.bombo(t(401), 0.8, f0=90, f1=34, dec=0.7)
    for c in (503, 518):
        m.toque(t(c), 0.12, 2400)
    # música propia (TEMP): zumbido grave que sube; casi silencio c369–380; acorde en el giro; nota sostenida al cierre
    m.pad(t(0), [33, 40], t(114) - 0.05, 0.05, corte=500)
    m.pad(t(114), [33], t(162) - t(114), 0.045, corte=380, a=0.01)
    m.pad(t(162), [33, 40, 45], t(369) - t(162), 0.05, corte=700)
    m.pad(t(401), [33, 45, 52, 57], t(495) - t(401), 0.05, corte=1400, a=0.02)
    m.pad(t(495), [38, 45, 50], t(576) - t(495), 0.04, corte=900)
    m.pad(t(576), [57], t(700) - t(576), 0.045, corte=1800, a=0.3)
    m.silenciar('amb', t(114), t(162), rampa=0.005)
    m.silenciar('amb', t(369), t(381), rampa=0.02)
    m.silenciar('mus', t(369), t(381), rampa=0.02)
    m.toque(t(369), 0.13, 2600); m.toque(t(375), 0.11, 2100)
    m.fundido('mus', t(700), t(723) - 0.25)
    m.fundido('amb', t(723) - 0.45, t(723) - 0.02)
    (T / 'audio').mkdir(exist_ok=True)
    wav = str(T / 'audio' / 'p2_completa.wav')
    r = m.exportar(wav, lufs=-14)
    print('exportar', r)
    # el limitador de exportar (0,83 de muestra) no garantiza el pico verdadero: pasada propia desde la mezcla previa
    pre = wav.replace('.wav', '_pre.wav')

    def medir(f):
        e = subprocess.run(['ffmpeg', '-nostats', '-i', f, '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-'],
                           capture_output=True, text=True).stderr
        I = float([l for l in e.splitlines() if l.strip().startswith('I:')][-1].split()[1])
        P = float([l for l in e.splitlines() if l.strip().startswith('Peak:')][-1].split()[1])
        return I, P
    I0, _ = medir(pre); gan = -14 - I0
    for _ in range(6):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', pre, '-af',
                        f'volume={gan:.2f}dB,alimiter=limit=0.76:level=false:attack=1:release=60:latency=1',
                        '-c:a', 'pcm_f32le', wav], check=True)
        I, P = medir(wav)
        if abs(I + 14) <= 0.2 and P <= -1.2:
            break
        gan += (-14 - I)
    json.dump({'lufs': I, 'pico_dbtp': P, 'ganancia_db': round(gan, 2)}, open(wav.replace('.wav', '_final.json'), 'w'))
    print('audio', I, P)


def master():
    a = V.ass(textos(), T / 'p2.ass')
    logo = ficha_logo(150)
    V.master(T / 'p2_video_t.mp4', T / 'audio' / 'p2_completa.wav', SALIDA, ass_path=a,
             overlays=[(str(logo), (W - 150) // 2, 300, 648 / FPS, NF / FPS)])
    print(SALIDA)


def control():
    CONTROL.mkdir(parents=True, exist_ok=True)
    V.hoja(SALIDA, CONTROL / 'P2_hoja_contacto_0.5s.jpg', cada=0.5, ancho=216, cols=8)
    cortes = [0, 71, 72, 113, 114, 161, 162, 200, 201, 239, 240, 275, 276, 320, 321, 380, 381, 390, 391, 400, 401, 431,
              494, 495, 527, 575, 576, 647, 648, 700, 722]
    for c in cortes:
        V.cuadro(SALIDA, c, CONTROL / f'P2_c{c:03d}.jpg')
    print('control', len(cortes))


if __name__ == '__main__':
    T.mkdir(parents=True, exist_ok=True)
    et = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    if et in ('planos', 'todo'): planos()
    if et == 'b8':                     # rehace solo B8 (marca de agua entera) y vuelve a unir
        P = json.load(open(T / 'planos.json'))
        P[7] = plano_b8()
        assert C.armar(P, T / 'p2_video.mp4') == NF
        json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    if et == 'g':                      # rehace solo G y vuelve a unir con los demás planos ya hechos
        P = json.load(open(T / 'planos.json'))
        P[10] = plano_g(T / 's11_g.mp4')
        assert C.armar(P, T / 'p2_video.mp4') == NF
        json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    if et in ('trans', 'todo'): trans()
    if et in ('audio', 'todo'): audio()
    if et in ('master', 'todo'): master()
    if et in ('control', 'todo'): control()
