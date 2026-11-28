# 3 historias de IG para comunidad (28/11/2026; guion de Fede, doc 04 §7, con la revisión de Roma, doc 06 §7):
# H1 encuesta «¿cuál pateás vos?» antes de la final de la Libertadores (hoy 17:00 ART): cancha dibujada en perspectiva
#    real (punto penal, línea del área y medialuna en blanco sobre azul noche), sin camisetas, escudos ni prenda;
# H2 pregunta «¿cuál fue tu "casi" de este año?» sobre los dedos que recorren «so f★cking close.» (IMG_3453, la negra);
# H3 revelación «¿Terminó el Black Friday? No. Sigue hasta el lunes 30/11.» sobre el recorrido real hasta la placa
#    (IMG_5361) + datos verificados + zona de link. Sin hora de cierre ni escasez.
# Mismo sistema visual que las del 26 y 27/11 (Instrument Serif + Inter espaciada, grado «lujo silencioso»).
# Uso: python3 scripts/ig/historias_28.py SALIDA_DIR
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fomo"))
from comun import Lector, Codificador, fuente, suave, fill_cover, grano, RAIZ

OUT = sys.argv[1]
for d in ("historias", "guia"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
SW, SH = 1080, 1920
BLANCO = (255, 255, 255)
CEL = (170, 208, 240)
NOCHE = (14, 24, 44)
V = "v01"
SOLO = os.environ.get("SOLO", "123")                                # qué historias renderizar
S3453 = os.path.join(RAIZ, "TRABAJO/jornada3/h28/sdr_3453.mp4")  # HLG→SDR + corrección de CAMPANA (negra carbón), 30 fps
S5361 = os.path.join(RAIZ, "TRABAJO/feed/sdr_5361.mp4")
LOGO = os.path.join(RAIZ, "LOGO/rocce_logo.png")


def neutro_oscuros(a, umbral=0.42, ancho_=0.22):
    """quita el tinte cálido de los oscuros (en 3453 la negra seguía marrón: R−B 8–12 en la tela, Roma doc 17)."""
    x = a.astype(np.float32) / 255.0
    lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    w = np.clip((umbral - lum) / ancho_, 0, 1)
    x = x + (lum - x) * w
    return np.clip(x * 255, 0, 255).astype(np.uint8)


def grado(a):
    x = a.astype(np.float32) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b)[..., None]
    celeste = np.clip((b - np.maximum(r, g)) * 8, 0, 1)[..., None]
    x = lum + (x - lum) * (0.86 + 0.14 * celeste)
    x = 0.022 + 0.958 * np.power(np.clip(x, 0, 1), 1.04)
    x = np.where(x > 0.84, 0.84 + (x - 0.84) * 0.72, x)
    return np.clip(x * 255, 0, 255).astype(np.uint8)


def degrade(a, y0, y1, g, arriba=True):
    yy = np.arange(a.shape[0], dtype=np.float32)
    t = np.clip((yy - y0) / max(1.0, y1 - y0), 0, 1)
    t = t * t * (3 - 2 * t)
    m = (1 - t) if arriba else t
    return (a.astype(np.float32) * (1 - g * m)[:, None, None]).astype(np.uint8)


def capa():
    return Image.new("RGBA", (SW, SH), (0, 0, 0, 0))


def renglon(img, y, tramos, track=0, sombra=0.5, radio=16):
    """renglón centrado con tramos de distinta fuente o color: [(texto, fuente, tamaño, color), ...]. Devuelve el ancho."""
    def ancho(s, f):
        return sum(f.getlength(c) for c in s) + track * (len(s) - 1) if track else f.getlength(s)
    fs = [(s, fuente(fk, sz), col) for s, fk, sz, col in tramos]
    w = sum(ancho(s, f) for s, f, _ in fs)
    sm = Image.new("L", img.size, 0); dm = ImageDraw.Draw(sm); d = ImageDraw.Draw(img)
    for paso in ("sombra", "texto"):
        x = SW / 2 - w / 2
        for s, f, col in fs:
            if track:
                for ch in s:
                    (dm.text((x, y + 3), ch, font=f, fill=255) if paso == "sombra" else d.text((x, y), ch, font=f, fill=col + (255,)))
                    x += f.getlength(ch) + track
            else:
                (dm.text((x, y + 3), s, font=f, fill=255) if paso == "sombra" else d.text((x, y), s, font=f, fill=col + (255,)))
                x += f.getlength(s)
        if paso == "sombra" and sombra:
            sh = capa(); sh.putalpha(sm.filter(ImageFilter.GaussianBlur(radio)).point(lambda v: int(v * sombra)))
            img.alpha_composite(sh)
    return w


def ajustar(tramos, maximo=920):
    """baja el tamaño de todos los tramos por igual hasta que el renglón entra en `maximo` px."""
    k = 1.0
    while sum(fuente(fk, int(sz * k)).getlength(s) for s, fk, sz, _ in tramos) > maximo: k -= 0.02
    return [(s, fk, int(sz * k), c) for s, fk, sz, c in tramos]


def ficha_logo(lado):
    lg = Image.open(LOGO).convert("RGB").resize((lado, lado), Image.LANCZOS)
    m = Image.new("L", (lado, lado), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, lado - 1, lado - 1], radius=int(lado * 0.12), fill=255)
    return lg, m


def frames(src, t0, n):
    L = Lector(src, t0, SW, SH); out = [L.cuadro().copy() for _ in range(n)]; L.cerrar(); return out


control, GUIA = {}, {}


def historia(nombre, fr, capas, zonas):
    """capas: (desde_cuadro, hasta_cuadro o None, capa RGBA, fundido en cuadros). Guarda MP4, último cuadro y guía."""
    cod = Codificador(os.path.join(OUT, "historias", nombre + ".mp4"), w=SW, h=SH)
    ult = None
    for k, f in enumerate(fr):
        b = Image.fromarray(f).convert("RGBA")
        for k0, k1, cp, fd in capas:
            if k >= k0 and (k1 is None or k < k1):
                al = suave((k - k0) / fd) if fd else 1.0
                if al < 1:
                    c2 = np.asarray(cp).astype(np.float32); c2[..., 3] *= al
                    b.alpha_composite(Image.fromarray(c2.astype(np.uint8), "RGBA"))
                else:
                    b.alpha_composite(cp)
        ult = grano(np.asarray(b.convert("RGB")), 2.5, k)
        cod.poner(ult)
    cod.cerrar()
    control[nombre] = dict(cuadros=cod.n, segundos=round(cod.n / 30, 2))
    Image.fromarray(ult).save(os.path.join(OUT, "historias", nombre + "_cuadro_final.png"), optimize=True)
    g = Image.fromarray(ult).convert("RGBA"); d = ImageDraw.Draw(g)
    for (x0, y0, x1, y1), t in zonas:
        for xx in range(int(x0), int(x1), 28):
            d.line([(xx, y0), (min(xx + 14, x1), y0)], fill=(255, 230, 0, 255), width=4)
            d.line([(xx, y1), (min(xx + 14, x1), y1)], fill=(255, 230, 0, 255), width=4)
        for yy in range(int(y0), int(y1), 28):
            d.line([(x0, yy), (x0, min(yy + 14, y1))], fill=(255, 230, 0, 255), width=4)
            d.line([(x1, yy), (x1, min(yy + 14, y1))], fill=(255, 230, 0, 255), width=4)
        renglon(g, (y0 + y1) / 2 - 18, [(t, "inter_sb", 28, (255, 230, 0))], sombra=0.8)
    for y in (220, SH - 300):  # zona segura: perfil arriba, respuesta abajo
        d.line([(0, y), (SW, y)], fill=(255, 80, 80, 200), width=2)
    g.convert("RGB").save(os.path.join(OUT, "guia", nombre + "_GUIA.jpg"), quality=88)
    GUIA[nombre] = [dict(zona=z, sticker=t) for z, t in zonas]


# ---------------- H1 · encuesta: la cancha en perspectiva real ----------------
# Plano de la cancha visto desde arriba (metros → píxeles) y proyección de cámara estenopeica detrás de la medialuna.
PX = 60                                    # px por metro en el plano
FX0, FY0, FW, FH = -26.0, -2.0, 52.0, 44.0  # x a lo ancho, y = distancia a la línea de meta
PL_W, PL_H = int(FW * PX), int(FH * PX)


def a_plano(x, y):
    return ((x - FX0) * PX, (y - FY0) * PX)


def plano():
    img = Image.new("RGB", (PL_W, PL_H), NOCHE)
    d = ImageDraw.Draw(img)
    for i, y in enumerate(np.arange(FY0, FY0 + FH, 4.0)):          # franjas del corte del pasto, cada 4 m
        if i % 2:
            d.rectangle([0, a_plano(0, y)[1], PL_W, a_plano(0, y + 4.0)[1]], fill=(18, 30, 54))
    lin = Image.new("L", (PL_W, PL_H), 0); dl = ImageDraw.Draw(lin)
    g = int(0.12 * PX)                                               # línea de 12 cm
    def seg(p, q):
        dl.line([a_plano(*p), a_plano(*q)], fill=255, width=g)
    seg((-20.16, 0), (20.16, 0)); seg((-20.16, 16.5), (20.16, 16.5)); seg((-20.16, 0), (-20.16, 16.5)); seg((20.16, 0), (20.16, 16.5))
    seg((-9.16, 0), (-9.16, 5.5)); seg((9.16, 0), (9.16, 5.5)); seg((-9.16, 5.5), (9.16, 5.5))
    c = a_plano(0, 11.0); r = 9.15 * PX                               # medialuna: arco de 9,15 m desde el punto, fuera del área
    ang = np.degrees(np.arccos(5.5 / 9.15))
    dl.arc([c[0] - r, c[1] - r, c[0] + r, c[1] + r], 90 - ang, 90 + ang, fill=255, width=g)
    rp = 0.22 * PX                                                    # punto penal
    dl.ellipse([c[0] - rp, c[1] - rp, c[0] + rp, c[1] + rp], fill=255)
    lin = lin.filter(ImageFilter.GaussianBlur(1.6))
    tiza = Image.new("RGB", (PL_W, PL_H), (232, 238, 244))
    img.paste(tiza, (0, 0), lin.point(lambda v: int(v * 0.92)))
    return img


def proyectar(x, y, cam_y, h=11.0, pitch=26.0, f=1250.0, cx=SW / 2, cy=1100.0):
    d = cam_y - y                                                     # distancia hacia adelante (hacia el arco)
    t = np.radians(pitch)
    fw = d * np.cos(t) + h * np.sin(t)
    up = -h * np.cos(t) + d * np.sin(t)
    return (cx + f * x / fw, cy - f * up / fw)


def coef_perspectiva(dst, src):
    """coeficientes de PIL (salida → entrada) a partir de 4 pares de puntos."""
    A, B = [], []
    for (u, v), (x, y) in zip(dst, src):
        A.append([u, v, 1, 0, 0, 0, -x * u, -x * v]); B.append(x)
        A.append([0, 0, 0, u, v, 1, -y * u, -y * v]); B.append(y)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


PLANO = plano() if "1" in SOLO else None
N1 = 150 if "1" in SOLO else 0
fr = []
for k in range(N1):
    cam = 31.0 - 1.2 * suave(k / (N1 - 1))                            # avance lento de la cámara (1,2 m en 5 s)
    pts = [(-14.0, 2.0), (14.0, 2.0), (14.0, 24.0), (-14.0, 24.0)]
    dst = [proyectar(x, y, cam) for x, y in pts]
    src = [a_plano(x, y) for x, y in pts]
    im = PLANO.transform((SW, SH), Image.PERSPECTIVE, coef_perspectiva(dst, src), Image.BICUBIC, fillcolor=NOCHE)
    a = np.asarray(im).astype(np.float32)
    px, py = proyectar(0.0, 11.0, cam)                                # luz suave sobre el punto penal
    yy, xx = np.mgrid[0:SH, 0:SW]
    luz = np.exp(-(((xx - px) / 420.0) ** 2 + ((yy - py) / 300.0) ** 2))
    a = a * (0.62 + 0.55 * luz[..., None])
    vin = np.clip(1 - 0.35 * ((xx - SW / 2) / (SW / 2)) ** 2 - 0.25 * ((yy - SH * 0.55) / (SH * 0.55)) ** 2, 0, 1)
    fr.append(np.clip(a * vin[..., None], 0, 255).astype(np.uint8))
PUNTO_Y = [round(proyectar(0.0, 11.0, 31.0 - 1.2 * suave(k / (N1 - 1)))[1]) for k in (0, N1 - 1)]

c = capa()
lg, m = ficha_logo(96)
c.paste(lg, (SW // 2 - 48, 246), m)
renglon(c, 384, [("HOY 17:00 · FINAL DE LA LIBERTADORES", "inter_sb", 34, CEL)], track=5, sombra=0.6)
renglon(c, 446, ajustar([("SI SE DEFINE POR PENALES,", "serif", 84, BLANCO)], 900), sombra=0.5, radio=18)
renglon(c, 540, ajustar([("¿CUÁL PATEÁS VOS?", "serif", 118, BLANCO)], 900), sombra=0.5, radio=18)
if "1" in SOLO: historia(f"ROCCE_IG_28_HISTORIA_1_ENCUESTA_{V}", fr, [(0, None, c, 0)],
         [((170, 730, 910, 950), "ENCUESTA: «EL PRIMERO» / «EL ÚLTIMO»")])

# ---------------- H2 · pregunta: los dedos sobre «so f★cking close.» (IMG_3453, 0,4–4,4 s) ----------------
fr = [degrade(grado(neutro_oscuros(a)), 0, 820, 0.45) for a in frames(S3453, 0.4, 120)] if "2" in SOLO else []
c = capa()
renglon(c, 254, ajustar([("¿CUÁL FUE TU ", "serif", 124, BLANCO), ("«CASI»", "serif_i", 124, CEL)], 930), sombra=0.55, radio=18)
renglon(c, 378, ajustar([("DE ESTE AÑO?", "serif", 124, BLANCO)], 930), sombra=0.55, radio=18)
if "2" in SOLO: historia(f"ROCCE_IG_28_HISTORIA_2_PREGUNTA_{V}", fr, [(0, None, c, 0)],
         [((170, 510, 910, 700), "PREGUNTA: «MI CASI FUE…»")])

# ---------------- H3 · revelación: el recorrido llega a la placa (IMG_5361) y se queda con un zoom lento ----------------
f = frames(S5361, 0.0, 87)
ult = Image.fromarray(f[-1])
f += [np.asarray(fill_cover(ult, SW, SH, cy=0.7, zoom=1.0 + 0.035 * suave(k / 63))) for k in range(63)]
fr = [degrade(degrade(grado(x), 0, 1000, 0.55), 0, 700, 0.45) for x in f]   # la manga blanca queda detrás de los textos
CAMBIO = 45                                                           # 1,5 s: la placa ya llena el cuadro
c1 = capa()
renglon(c1, 268, [("¿TERMINÓ EL", "serif", 118, BLANCO)], sombra=0.5, radio=18)
renglon(c1, 390, [("BLACK FRIDAY?", "serif", 118, BLANCO)], sombra=0.5, radio=18)
c2 = capa()
renglon(c2, 250, [("NO.", "serif_i", 150, BLANCO)], sombra=0.5, radio=18)
renglon(c2, 412, ajustar([("SIGUE HASTA EL LUNES 30/11.", "serif", 72, BLANCO)], 900), sombra=0.55, radio=16)
c3 = capa()
pl = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))                     # placa difusa: los datos van sobre la manga blanca
ImageDraw.Draw(pl).rounded_rectangle([170, 514, 910, 660], radius=30, fill=(8, 14, 26, 150))
c3.alpha_composite(pl.filter(ImageFilter.GaussianBlur(12)))
renglon(c3, 532, [("$48.750 (antes $65.000) · −25 %", "inter_sb", 44, BLANCO)], sombra=0.7)
renglon(c3, 592, [("Envío gratis · Placa incluida", "inter_m", 42, CEL)], sombra=0.7)
if "3" in SOLO: historia(f"ROCCE_IG_28_HISTORIA_3_REVELACION_{V}", fr, [(0, CAMBIO, c1, 0), (CAMBIO, None, c2, 6), (CAMBIO + 9, None, c3, 8)],
         [((290, 680, 790, 780), "LINK: rocce.shop")])

json.dump(dict(control=control, guia=GUIA, punto_penal_y=PUNTO_Y), open(os.path.join(OUT, "guia", "control.json"), "w"),
          indent=1, ensure_ascii=False)
print(json.dumps(dict(control=control, punto_penal_y=PUNTO_Y)))
