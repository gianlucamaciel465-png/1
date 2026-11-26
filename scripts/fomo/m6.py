# M6 «¿Llega a 200?» · FOMO de la placa + Black Friday (26/11/2026). Misma línea que M4 y M5, ahora con tenis.
# Apuesta desde el cuadro 0: «¿Llega a 200 km/h con 50 pelotas?» y un saque. Evidencia en contra a toda velocidad: cada saque
# marca su velocidad en un radar (183 ✗, 191 ✗, ráfaga de ✗) mientras las pelotas se acaban. Última pelota: congelado, el radar
# sube cada vez más lento y frena en 199 ✗ («so f★cking close.»). Giro: no era la última pelota; vuelve a llenar la canasta y la
# primera pelota marca 201 ✓ (vuelve el color). Reenganche: «no llegó en la última; llegó porque volvió a llenar la canasta» →
# la placa real de Gianluca (IMG_5359, IMG_5361) «eso significa: seguir hasta lograrlo», viene con cada remera (IMG_5333) →
# «¿Cuántas veces volviste a llenar la tuya?» → CTA sobre la foto real de la placa con las dos remeras (IMG_5361).
# Clips de tenis de Mixkit (licencia libre, solo hay 720p): 45496 (saque), 23025 (saque en cámara lenta, contraluz),
# 23946 (canasta de pelotas), 23639 (golpe en cámara lenta), 14057 (pelota en el piso). Las velocidades son ficción del relato.
# Voz dirigida: scripts/fomo/voz_m6.tsv + scripts/voz/voz_dirigida.py.
# Uso: python3 scripts/fomo/m6.py SALIDA.mp4   (SOLO_AUDIO=1 mide voz/fondo sin renderizar el video)
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from comun import *

TN = os.path.join(RAIZ, "TRABAJO/fomo/tenis")
GL = os.path.join(RAIZ, "TRABAJO/fomo/gl")
VOZ = os.path.join(RAIZ, "TRABAJO/fomo/voz_m6")
FOTO_CTA = os.path.join(GL, "f5361_0.png")
salida = sys.argv[1]
N = 822
SOLO_AUDIO = bool(os.environ.get("SOLO_AUDIO"))


def tn(i):
    return os.path.join(TN, f"h_{i}.mp4")


# ---------- planos: (desde, hasta, fuente, t0, cx, espejo, modo, zoom) ----------
# modo "real" = tiempo real; "x2" = fuente en cámara lenta acelerada al doble; "nativa" = un cuadro de la fuente por cuadro
C_H1, C_H2 = 50, 86  # golpes de los saques 1 y 2
PLAN = [
    (0, 54, tn(45496), 13.2 - 50 / 30, 690, False, "real", 1.0),  # saque 1
    (54, 92, tn(23025), 8.28 - 2 * 32 / 30, 600, True, "x2", 1.0),  # saque 2 (espejado)
    (92, 108, tn(23946), 4.0, 820, False, "real", 1.0),  # la canasta: las pelotas se van
    (108, 136, "RAFAGA", 0, 0, False, "", 1.0),
    (136, 160, tn(45496), 4.2, 780, False, "real", 1.0),  # pica la pelota: última
    (160, 188, tn(23025), 8.25 - 28 / 30, 640, False, "real", 1.25),  # último saque, cámara lenta, más cerca
    (188, 248, "CONGELA", 0, 0, False, "", 1.0),
    (248, 272, tn(14057), 3.0, 1000, False, "real", 1.0),  # la pelota en el piso: quedan 0
    (272, 322, tn(23946), 0.4, 820, False, "real", 1.0),  # la mano en la canasta: vuelve a llenarla
    (322, 392, tn(23639), 4.2 - 33 / 25, 700, False, "nativa", 1.0),  # primera pelota: golpe en cámara lenta
    (392, 436, tn(45496), 13.4, 720, False, "real", 1.0),  # el jugador, en color
    (436, 510, "MONTAJE", 0, 0, False, "", 1.0),  # las cincuenta de antes, en B/N
]
RAFAGA = [(tn(45496), 13.14, 700, False, 1.0), (tn(23025), 8.22, 620, True, 1.1), (tn(45496), 13.12, 660, True, 1.15),
          (tn(23025), 8.20, 660, False, 1.0), (tn(45496), 13.16, 720, False, 1.25), (tn(23025), 8.24, 600, True, 1.25),
          (tn(45496), 13.12, 690, True, 1.0)]  # 4 cuadros cada uno, en el golpe
VEL_RAF = [176, 188, 181, 194, 190, 197, 195]
BOL_RAF = [17, 14, 11, 8, 5, 3, 1]
MONTAJE = [(tn(45496), 4.6, 640, False, 1.0), (tn(23025), 7.9, 620, True, 1.0), (tn(23946), 2.2, 820, False, 1.0),
           (tn(45496), 9.8, 680, True, 1.0), (tn(14057), 6.0, 1000, False, 1.0), (tn(23025), 8.2, 640, False, 1.2),
           (tn(45496), 12.9, 700, False, 1.15)]  # ~10 cuadros cada uno, B/N
N_MON = 74
C_FIN_SUBE, C_X199, C_FRASE = 226, 230, 234
C_IMPACTO, C_COLOR = 355, 361


def vel_congelado(c):
    u = min(max((c - 190) / (C_FIN_SUBE - 190), 0), 1)
    return int(120 + 79 * (1 - (1 - u) ** 3))


# radar: lista de (cuadro, valor, marca)
RADAR = []
for ch, v in ((C_H1, 183), (C_H2, 191)):
    for k in range(6):
        RADAR.append((ch + k, int(v - (v - 100) * (1 - k / 6) ** 2), None))
    RADAR.append((ch + 6, v, "x"))
for j, v in enumerate(VEL_RAF):
    RADAR.append((108 + 4 * j, v, "x"))
for c in range(190, C_X199):
    RADAR.append((c, vel_congelado(c), None))
RADAR.append((C_X199, 199, "x"))
for k in range(6):
    RADAR.append((C_IMPACTO + k, int(201 - 101 * (1 - k / 6) ** 2), None))
RADAR.append((C_IMPACTO + 6, 201, "v"))
RADAR.sort()
# pelotas que quedan: (cuadro, n)
BOLAS = [(0, 50), (C_H1 + 6, 49), (C_H2 + 6, 48)]
for c in range(94, 106, 2):
    BOLAS.append((c, 48 - (c - 92) * 2))  # 46 … 36
BOLAS.append((106, 20))
for j, n in enumerate(BOL_RAF):
    BOLAS.append((108 + 4 * j, n))
BOLAS.append((C_X199, 0))
for k, c in enumerate(range(288, 305)):
    BOLAS.append((c, min(50, int(50 * (k / 16) ** 0.8))))


def radar_en(c):
    if not (C_H1 <= c < 136 or 190 <= c < 268 or C_IMPACTO <= c < 392):
        return None
    ev = [e for e in RADAR if e[0] <= c]
    return ev[-1] if ev else None


def bolas_en(c):
    if not (c < 136 or 160 <= c < 322):
        return None if not (136 <= c < 160) else (136, 1)
    return [e for e in BOLAS if e[0] <= c][-1]


# ---------- lectura ----------
def recorte(fr, cx, espejo=False, zoom=1.0, cy=None):
    h0, w0 = fr.shape[:2]
    hh = int(round(h0 / zoom)); ww = int(round(hh * 9 / 16))
    cy = h0 / 2 if cy is None else cy
    x0 = int(round(min(max(cx - ww / 2, 0), w0 - ww)))
    y0 = int(round(min(max(cy - hh / 2, 0), h0 - hh)))
    sub = fr[y0:y0 + hh, x0:x0 + ww]
    if espejo:
        sub = sub[:, ::-1]
    im = Image.fromarray(np.ascontiguousarray(sub)).resize((W, H), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=55, threshold=3))  # 720p: un poco de nitidez
    return np.asarray(im)


def lector(src, t0, modo):
    if modo == "x2":
        return Lector(src, t0, 1280, 720, uno_a_uno=False, vf_pre="setpts=0.5*PTS")
    return Lector(src, t0, 1280, 720, uno_a_uno=(modo == "nativa"))


def leer_n(src, t0, n, cx, espejo, zoom, modo="real"):
    L = lector(src, t0, modo)
    out = [recorte(L.cuadro(), cx, espejo, zoom).copy() for _ in range(n)]
    L.cerrar()
    return out


# ---------- textos ----------
def capa_radar(n, marca):
    f = fuente("disp_xb", 150); fk = fuente("disp_b", 50)
    txt = f"{n}"
    tw = f.getlength(txt); kw = fk.getlength("KM/H")
    mk = 104 if marca else 0
    gap = 38 if marca else 0
    img = Image.new("RGBA", (W, 230), (0, 0, 0, 0))
    x = (W - tw - 16 - kw - gap - mk) / 2
    col = CELESTE if marca == "v" else (255, 255, 255)
    xk, yk = x + tw + 16, 30 + 88
    mx, my = xk + kw + gap, 66
    sm = Image.new("L", img.size, 0); ds = ImageDraw.Draw(sm)
    ds.text((x, 34), txt, font=f, fill=255); ds.text((xk, yk + 4), "KM/H", font=fk, fill=255)
    if marca == "x":
        ds.line([(mx, my + 4), (mx + mk, my + mk + 4)], fill=255, width=22)
        ds.line([(mx + mk, my + 4), (mx, my + mk + 4)], fill=255, width=22)
    elif marca == "v":
        ds.line([(mx, my + 55), (mx + 36, my + 94), (mx + mk, my + 8)], fill=255, width=22, joint="curve")
    sm = sm.filter(ImageFilter.GaussianBlur(12))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(sm.point(lambda v: int(v * 0.6)))
    img = Image.alpha_composite(img, sh); d = ImageDraw.Draw(img)
    d.text((x, 30), txt, font=f, fill=col + (255,))
    d.text((xk, yk), "KM/H", font=fk, fill=col + (255,))
    if marca == "x":
        d.line([(mx, my), (mx + mk, my + mk)], fill=(255, 255, 255, 255), width=20)
        d.line([(mx + mk, my), (mx, my + mk)], fill=(255, 255, 255, 255), width=20)
    elif marca == "v":
        d.line([(mx, my + 51), (mx + 36, my + 90), (mx + mk, my + 4)], fill=CELESTE + (255,), width=20, joint="curve")
    return img


_cache = {}


def radar(n, marca):
    if ("r", n, marca) not in _cache:
        _cache[("r", n, marca)] = capa_radar(n, marca)
    return _cache[("r", n, marca)]


def bolas(n):
    if ("b", n) not in _cache:
        t = "QUEDA 1 PELOTA" if n == 1 else ("QUEDAN 0" if n == 0 else f"QUEDAN {n} PELOTAS")
        _cache[("b", n)] = capa_texto([t], "inter_sb", 50 if n > 1 else 60, track=4, sombra=0.95, radio_sombra=8)
    return _cache[("b", n)]


T_PREG = capa_texto(["¿LLEGA A 200 KM/H", "CON 50 PELOTAS?"], "disp_b", 80)
T_ULT = capa_texto(["ÚLTIMA PELOTA"], "disp_xb", 84, color=CELESTE)
T_CLOSE = capa_texto(["so f★cking close."], "disp_xb", 104)
T_PRIM = capa_texto(["PRIMERA PELOTA"], "disp_xb", 84, color=CELESTE)
T_LLEGO = capa_texto(["¡LLEGÓ!"], "disp_xb", 150, color=CELESTE)
T_NOULT = capa_texto(["NO LLEGÓ", "EN LA ÚLTIMA."], "disp_xb", 100)
T_PORQUE = capa_texto(["LLEGÓ PORQUE VOLVIÓ", "A LLENAR LA CANASTA."], "disp_xb", 84)
T_SIGNIF = capa_texto(["ESO SIGNIFICA", "ESTA PLACA"], "disp_xb", 96)
T_SEGUIR = capa_texto(["SEGUIR HASTA", "LOGRARLO."], "disp_xb", 112)
T_VIENE = capa_texto(["VIENE CON", "CADA REMERA"], "disp_xb", 96)
T_VOS = capa_texto(["¿CUÁNTAS VECES", "VOLVISTE A LLENAR", "LA TUYA?"], "disp_xb", 90)
# CTA (mismos datos verificados que M4 y M5)
T_BF = capa_texto(["BLACK FRIDAY"], "disp_xb", 112)
T_PCT = capa_texto(["−25%"], "disp_xb", 236)
T_PRE = capa_texto(["$48.750"], "disp_b", 112)
f46 = fuente("inter_m", 46)
T_ANT = capa_texto(["antes $65.000"], "inter_m", 46, color=(225, 225, 225))
x0_ = (W - f46.getlength("antes $65.000")) / 2 + f46.getlength("antes "); x1_ = (W + f46.getlength("antes $65.000")) / 2
ImageDraw.Draw(T_ANT).line([(x0_ - 3, 10 + f46.getmetrics()[0] * 0.64), (x1_ + 3, 10 + f46.getmetrics()[0] * 0.64)],
                           fill=(225, 225, 225, 255), width=4)
T_INC = capa_texto(["REMERA + PLACA · ENVÍO GRATIS"], "inter_sb", 40, track=2)
T_WEB = capa_texto(["rocce.shop"], "inter_sb", 52)


def pop(k, dur=4, desde=1.25):
    if k >= dur: return 1.0
    return desde + (1 - desde) * suave(max(k, 0) / dur)


def pegar_esc(img, capa, y, esc=1.0, alfa=1.0, dx=0):
    if alfa <= 0: return
    if esc != 1.0:
        w, h = capa.size
        capa = capa.resize((int(w * esc), int(h * esc)), Image.LANCZOS)
        pegar(img, capa, (W - capa.size[0]) / 2 + dx, y - (capa.size[1] - h) / 2, alfa)
    else:
        pegar(img, capa, dx, y, alfa)


def oscurecer_arriba(a, hasta=700, g=0.5):
    yy = np.arange(H)[:, None, None]
    osc = np.clip((hasta - yy) / hasta, 0, 1) * g
    return (a.astype(np.float32) * (1 - osc)).astype(np.uint8)


def oscurecer_abajo(a, desde=1500, g=0.5):
    yy = np.arange(H)[:, None, None]
    osc = np.clip((yy - desde) / (H - desde), 0, 1) * g
    return (a.astype(np.float32) * (1 - osc)).astype(np.uint8)


foto = Image.open(FOTO_CTA).convert("RGB")


def cuadro_cta(k):
    im = fill_cover(foto, W, H, cx=0.5, cy=0.55, zoom=1.0 + 0.05 * k / 80)
    a = oscurecer_arriba(np.asarray(im), hasta=900, g=0.45)
    a = oscurecer_abajo(a, 1560, 0.55)
    pegar(a, T_BF, 0, 112, alfa=suave(k / 4))
    pegar_esc(a, T_PCT, 222, esc=pop(k - 3, 5, 1.3), alfa=suave((k - 3) / 3))
    pegar(a, T_PRE, 0, 488, alfa=suave((k - 12) / 4))
    pegar(a, T_ANT, 0, 618, alfa=suave((k - 12) / 4))
    pegar(a, T_INC, 0, 692, alfa=suave((k - 20) / 4))
    pegar(a, T_WEB, 0, 1806, alfa=suave((k - 24) / 4))
    return a


def lector_gl(nombre, t0):
    return Lector(os.path.join(GL, nombre), t0, W, H)


def entra(c, c0, d=3):
    return suave((c - c0) / d)


# ---------- render ----------
cod = None
if not SOLO_AUDIO:
    raf = []
    for src, t0, cx, esp, z in RAFAGA:
        raf += leer_n(src, t0, 4, cx, esp, z, "x2" if "23025" in src else "real")
    mon = []
    por = [N_MON // len(MONTAJE) + (1 if i < N_MON % len(MONTAJE) else 0) for i in range(len(MONTAJE))]
    for (src, t0, cx, esp, z), n in zip(MONTAJE, por):
        mon += leer_n(src, t0, n, cx, esp, z, "x2" if "23025" in src else "real")
    cod = Codificador(salida + ".tmp.mp4")
lect = None; actual = None; ultimo = None
for c in range(0 if SOLO_AUDIO else N):
    if c < 510:
        for a, b, src, t0, cx, esp, modo, z in PLAN:
            if a <= c < b:
                break
        k = c - a
        if src == "RAFAGA":
            img = raf[min(k, len(raf) - 1)].copy()
        elif src == "MONTAJE":
            img = mon[min(k, len(mon) - 1)].copy()
        elif src == "CONGELA":
            zz = 1.0 + 0.07 * suave(k / 40)
            img = np.asarray(fill_cover(Image.fromarray(ultimo), W, H, cy=0.4, zoom=zz)).copy()
        else:
            if actual != a:
                if lect: lect.cerrar()
                lect = lector(src, t0, modo); actual = a
            img = recorte(lect.cuadro(), cx, esp, z).copy()
            ultimo = img.copy()
        g = bn(img, contraste=1.28)
        if C_COLOR <= c < 436:  # vuelve el color con el 201 ✓; las cincuenta de antes, en B/N
            m = suave((c - C_COLOR) / 6)
            img = (g * (1 - m) + img * m).astype(np.uint8)
        else:
            img = g
        img = oscurecer_arriba(img, 720, 0.45) if C_COLOR <= c < 436 else oscurecer_arriba(img, 950, 0.62)  # cielo claro en B/N
        img = grano(img, 5, c)
        # textos
        if c < 136:
            pegar(img, T_PREG, 0, 112, alfa=1.0 if c < 130 else 1 - suave((c - 130) / 6))
        r = radar_en(c)
        if r:
            kk = c - r[0]
            sacude = (12 * np.sin(kk * 2.4) * (1 - kk / 5)) if (r[2] == "x" and kk < 5) else 0
            esc = pop(kk, 4, 1.22) if r[2] else 1.0
            fade = (1 - suave((c - 262) / 6)) if 190 <= c < 268 else (1 - suave((c - 130) / 6)) if c < 136 else 1.0
            pegar_esc(img, radar(r[1], r[2]), 322, esc=esc, dx=sacude, alfa=fade)
        bo = bolas_en(c)
        if bo:
            kk = c - bo[0]
            fade = (1 - suave((c - 130) / 6)) if c < 136 else (1 - suave((c - 316) / 6)) if 300 <= c < 322 else 1.0
            pegar_esc(img, bolas(bo[1]), 560, esc=pop(kk, 3, 1.12), alfa=fade)
        if 138 <= c < 188:
            pegar_esc(img, T_ULT, 1500, esc=pop(c - 138, 4, 1.3), alfa=entra(c, 138) * (1 - suave((c - 182) / 6)))
        if C_FRASE <= c < 272:
            pegar_esc(img, T_CLOSE, 1420, esc=pop(c - C_FRASE, 5, 1.15), alfa=entra(c, C_FRASE, 4) * (1 - suave((c - 266) / 6)))
        if 326 <= c < C_IMPACTO + 2:
            pegar_esc(img, T_PRIM, 1500, esc=pop(c - 326, 4, 1.3), alfa=entra(c, 326) * (1 - suave((c - C_IMPACTO + 2) / 3)))
        if C_COLOR + 2 <= c < 392:
            pegar_esc(img, T_LLEGO, 1380, esc=pop(c - C_COLOR - 2, 5, 1.18), alfa=entra(c, C_COLOR + 2, 2))
        if 396 <= c < 436:
            pegar_esc(img, T_NOULT, 180, esc=pop(c - 396, 4, 1.15), alfa=entra(c, 396) * (1 - suave((c - 431) / 5)))
        if c >= 438:
            pegar_esc(img, T_PORQUE, 190, esc=pop(c - 438, 4, 1.15), alfa=entra(c, 438))
    elif c < 561:  # IMG_5359: la placa en su mano — «Eso significa esta placa»
        if c == 510:
            if lect: lect.cerrar()
            lect = lector_gl("sdr_5359.mp4", 8.0)  # la placa nítida en su mano
        img = grano(oscurecer_arriba(lect.cuadro().copy(), 640, 0.45), 3, c)
        if c >= 514:
            pegar_esc(img, T_SIGNIF, 180, esc=pop(c - 514, 4, 1.15), alfa=entra(c, 514))
    elif c < 604:  # IMG_5361: la placa junto a las dos remeras — «seguir hasta lograrlo»
        if c == 561:
            lect.cerrar(); lect = lector_gl("sdr_5361.mp4", 0.6)
        img = grano(oscurecer_arriba(lect.cuadro().copy(), 720, 0.55), 3, c)
        if c >= 563:
            pegar_esc(img, T_SEGUIR, 170, esc=pop(c - 563, 5, 1.18), alfa=entra(c, 563))
    elif c < 668:  # IMG_5333: espalda de la blanca y de la negra — «viene con cada remera»
        if c == 604:
            lect.cerrar(); lect = lector_gl("sdr_5333.mp4", 0.5)
        img = grano(oscurecer_arriba(lect.cuadro().copy(), 640, 0.45), 3, c)
        if c >= 612:
            pegar_esc(img, T_VIENE, 190, esc=pop(c - 612, 4, 1.2), alfa=entra(c, 612))
    elif c < 742:  # la canasta sola: «¿Cuántas veces volviste a llenar la tuya?»
        if c == 668:
            lect.cerrar(); lect = lector(tn(23946), 7.6, "real")
        img = recorte(lect.cuadro(), 860).copy()
        img = grano(oscurecer_arriba(bn(img, contraste=1.28), 760, 0.5), 5, c)
        if c >= 672:
            pegar_esc(img, T_VOS, 230, esc=pop(c - 672, 5, 1.2), alfa=entra(c, 672))
    else:
        if lect: lect.cerrar(); lect = None
        img = cuadro_cta(c - 742)
    cod.poner(img)
if lect: lect.cerrar()

# ---------- sonido ----------
dur = N / FPS
x = lienzo(dur)
rng = np.random.default_rng(16)
aire = np.convolve(rng.normal(0, 1, len(x)), np.ones(60) / 60, "same") * 0.03  # aire de club, afuera
x += aire


def pique(x, t, g=0.5):
    """golpe de raqueta: «pock» corto con cuerpo + click de cuerdas."""
    n = int(0.12 * SR); i = int(t * SR); tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1150 * tt) * np.exp(-tt / 0.018) * 0.7 + np.sin(2 * np.pi * 520 * tt) * np.exp(-tt / 0.03) * 0.5)
    r = np.random.default_rng(int(t * 1000)).normal(0, 1, n) * np.exp(-tt / 0.004) * 0.6
    x[i:i + n] += ((s + r) * g)[: len(x) - i]
    golpe(x, t, g * 0.4, f0=95, caida=0.06)


def error(x, t, g=0.22, d=0.16):
    """✗ del radar: zumbido grave corto."""
    n = int(d * SR); i = int(t * SR); tt = np.arange(n) / SR
    s = np.sign(np.sin(2 * np.pi * 138 * tt)) * 0.6 + np.sin(2 * np.pi * 69 * tt)
    s *= np.minimum(1, tt / 0.005) * np.minimum(1, (d - tt) / 0.03)
    x[i:i + n] += (s * g)[: len(x) - i]


# pulso que se acelera mientras se acaban las pelotas (más bajo debajo de la voz)
t = 0.0
while t < 136 / FPS:
    bajo_voz = (t < 66 / FPS) or (92 / FPS <= t < 122 / FPS)
    golpe(x, t, 0.14 if bajo_voz else 0.3, f0=48, caida=0.16); t += 0.5 if t < 92 / FPS else 0.34
for ch in (C_H1, C_H2):
    pique(x, ch / FPS, 0.5); error(x, (ch + 6) / FPS, 0.16 if ch == C_H1 else 0.2)
for c in range(94, 108, 2):
    tic(x, c / FPS, 0.14, 2200)
for j in range(7):
    tt = (108 + 4 * j) / FPS
    g_ = 0.35 if j < 1 else 0.2  # debajo de «Tampoco.» más bajo
    pique(x, tt, g_); error(x, tt + 0.02, 0.14 if j < 1 else 0.07, 0.09)
barrido(x, 108 / FPS, 28 / FPS, 0.12, 200, 6000)
for tt in np.arange(136 / FPS, 188 / FPS, 0.48):  # latido: última pelota
    golpe(x, tt, 0.35, f0=46, caida=0.2)
for k in range(3):  # pica la pelota
    golpe(x, (142 + 7 * k) / FPS, 0.22, f0=120, caida=0.05)
pique(x, 187 / FPS, 0.55)
# congelado: casi silencio; el radar sube y frena; 199 ✗; silencio
i0, i1 = int(188 / FPS * SR), int(272 / FPS * SR)
x[i0:i1] *= 0.2
prev = None
for c in range(190, C_X199):
    v = vel_congelado(c)
    if v != prev and v >= 170:
        tic(x, c / FPS, 0.12 + 0.1 * (v - 170) / 29, 2400)
    prev = v
golpe(x, C_X199 / FPS, 0.55, f0=40, caida=0.6); error(x, C_X199 / FPS, 0.2, 0.3)
# vuelve a llenar la canasta: tics que suben
for k, c in enumerate(range(288, 305)):
    tic(x, c / FPS, 0.1 + 0.006 * k, 1500 + 60 * k)
barrido(x, 272 / FPS - 0.1, 0.3, 0.15, 400, 5000)
# primera pelota: suspenso, golpe, color
golpe(x, 326 / FPS, 0.3, f0=46, caida=0.3)
pique(x, C_IMPACTO / FPS, 0.75)
golpe(x, C_COLOR / FPS, 0.5, f0=44, caida=0.7)
brillo(x, C_COLOR / FPS, 0.08)
colchon(x, C_COLOR / FPS, 436 / FPS, [146.8, 220.0, 293.7, 370.0], 0.05, ataque=0.2, suelta=0.5)
# las cincuenta de antes: tics secos por plano
cc = 436
for n in [N_MON // len(MONTAJE) + (1 if i < N_MON % len(MONTAJE) else 0) for i in range(len(MONTAJE))]:
    tic(x, cc / FPS, 0.16, 1500); golpe(x, cc / FPS, 0.16, f0=58, caida=0.08); cc += n
colchon(x, 510 / FPS, 668 / FPS, [146.8, 220.0, 293.7, 370.0], 0.05, ataque=0.3, suelta=0.6)
for cc in (392, 436, 510, 561, 604, 668):
    barrido(x, cc / FPS - 0.12, 0.3, 0.15, 400, 5000)
brillo(x, 563 / FPS, 0.18); golpe(x, 563 / FPS, 0.4, f0=50, caida=0.4)  # «seguir»
golpe(x, 668 / FPS, 0.45, f0=50, caida=0.3)
golpe(x, 742 / FPS, 0.45, f0=56, caida=0.4); brillo(x, 745 / FPS, 0.12)
colchon(x, 742 / FPS, dur, [110.0, 164.8, 220.0, 277.2], 0.07, ataque=0.15, suelta=0.4)

ids = ["x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "x9", "x10"]
v = {k: leer_wav(os.path.join(VOZ, f"{k}.wav")) for k in ids}
for k, db in (("x2", 8.0), ("x3", 2.0), ("x4", 2.0), ("x5", 3.0), ("x6", 2.0), ("x9", 2.0), ("x10", 2.0)):
    v[k] = v[k] * 10 ** (db / 20)
corte = int(0.72 * SR)  # x2: «No llega.» | «Tampoco.»
v["x2a"], v["x2b"] = v["x2"][:corte], v["x2"][corte:]
voces_k = [(2, "x1"), (93, "x2a"), (113, "x2b"), (140, "x3"), (274, "x4"), (325, "x5"), (394, "x6"), (512, "x7"),
           (606, "x8"), (670, "x9"), (746, "x10")]
voces = [(cc / FPS, v[k]) for cc, k in voces_k]
wav = salida + ".wav"
nivel, (vv, ff) = mezclar(x, voces, dur, wav, techo=0.78)
relacion = {}
for (tv, av), (_, k) in zip(voces, voces_k):
    i0, i1 = int(tv * SR), int(tv * SR) + len(av)
    rv = np.sqrt((vv[i0:i1] ** 2).mean()) + 1e-12; rf = np.sqrt((ff[i0:i1] ** 2).mean()) + 1e-12
    relacion[k] = round(20 * np.log10(rv / rf), 1)
print("voz/fondo dB", relacion, "fin voz", round(max(t + len(a) / SR for t, a in voces), 2), "dur", round(dur, 2))
if SOLO_AUDIO:
    os.remove(wav); sys.exit(0)
cod.cerrar(audio=wav)
os.replace(salida + ".tmp.mp4", salida); os.remove(wav)
json.dump(dict(cuadros=cod.n, duracion=dur, sonoridad=nivel, voz_fondo_db=relacion, voces=[(round(cc / FPS, 2), k) for cc, k
          in voces_k]), open(salida + ".control.json", "w"), indent=1)
print(cod.n, nivel)
