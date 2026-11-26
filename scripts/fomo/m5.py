# M5 «¿La mete antes de que suene?» · FOMO de la placa + Black Friday (26/11/2026). Misma línea que M4.
# Apuesta desde el cuadro 0 (reloj de posesión 0:10 y un jugador que encara: ¿la mete antes de que suene?), evidencia en
# contra a toda velocidad (erra, vuelve a errar, le tapan el tiro, ráfaga de ✗ mientras el reloj baja), último tiro,
# congelado, la bocina suena con la pelota en el aire y entra (✓, vuelve el color). Reenganche: «el último tiro lo ve todo
# el mundo; los mil de antes, nadie» → la placa real de Gianluca (IMG_5359, IMG_5361) «es por esos mil», viene con cada
# remera (IMG_5333) → «¿Cuántos tiros te faltan a vos?» → CTA sobre la foto real de la placa con las dos remeras (IMG_5361).
# Clips de básquet de Mixkit (licencia libre): 44455, 44448, 44458, 44468, 44454, 44446, 13733, 2278.
# Voz dirigida: scripts/fomo/voz_m5.tsv + scripts/voz/voz_dirigida.py.
# Uso: python3 scripts/fomo/m5.py SALIDA.mp4   (SOLO_AUDIO=1 mide voz/fondo sin renderizar el video)
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from comun import *

BK = os.path.join(RAIZ, "TRABAJO/fomo/bk")
GL = os.path.join(RAIZ, "TRABAJO/fomo/gl")  # tomas de Gianluca del 26/11 pasadas a SDR (ver m1.py, TONEMAP)
VOZ = os.path.join(RAIZ, "TRABAJO/fomo/voz_m5")
FOTO_CTA = os.path.join(GL, "f5361_0.png")  # primer cuadro de IMG_5361: la placa con las dos remeras en el deck
salida = sys.argv[1]
N = 743
SOLO_AUDIO = bool(os.environ.get("SOLO_AUDIO"))


def bk(i):
    return os.path.join(BK, f"h_{i}.mp4")


# ---------- planos de básquet: (desde, hasta, fuente, t0, centros {t_src: x}, espejo, velocidad) ----------
# velocidad "real" = tiempo real (FFmpeg pasa a 30 fps); "nativa" = un cuadro de la fuente por cuadro (cámara lenta suave)
C55 = {3.4: 1300, 3.8: 1230, 4.2: 1080, 4.6: 960, 4.97: 860}
C48 = {2.95: 1000, 3.4: 900, 3.9: 740}
C33 = {1.0: 700, 1.8: 620, 2.6: 620, 4.0: 560, 7.0: 560}
PLAN = [
    (0, 47, bk(44455), 3.40, C55, False, "real"),  # encara y tira: se corta justo antes del aro (golpe de aro + ✗)
    (47, 76, bk(44448), 2.95, C48, False, "real"),  # tiro en suspensión: ✗
    (76, 100, bk(44458), 0.60, {0: 860}, False, "real"),  # levanta la pelota, la hace girar
    (100, 130, bk(44468), 2.65, {0: 480}, False, "real"),  # se la tapan: ✗
    (130, 150, bk(44455), 4.30, C55, True, "real"),  # vuelve a encarar: ✗
    (150, 178, "RAFAGA", 0, None, False, ""),
    (178, 214, bk(44446), 10.60, {0: 1000}, False, "real"),  # último tiro
    (214, 232, "CONGELA", 0, None, False, ""),
    (232, 278, bk(13733), 1.00, C33, False, "nativa"),  # la pelota baja al aro; bocina en el aire; entra
    (278, 344, bk(44458), 4.60, {0: 870}, False, "real"),  # el jugador, en color: «el último tiro lo ve todo el mundo»
    (344, 390, "MONTAJE", 0, None, False, ""),  # «los mil de antes…»
    (390, 422, bk(2278), 4.70, {0: 900}, False, "real"),  # sola en la cancha, después del tiro: «nadie»
]
RAFAGA = [(bk(44454), 0.72, 860, False), (bk(44448), 3.72, 760, True), (bk(44468), 3.25, 480, False),
          (bk(44455), 4.83, 880, True), (bk(44454), 0.80, 860, True), (bk(44448), 3.80, 760, False),
          (bk(44468), 3.40, 480, True)]  # 4 cuadros cada uno, justo antes de que la pelota llegue al aro
MONTAJE = [(bk(44455), 4.40, 1000, False, 7), (bk(2278), 3.20, 900, False, 7), (bk(44448), 3.40, 900, True, 7),
           (bk(44468), 3.00, 480, False, 7), (bk(2278), 7.60, 900, True, 7), (bk(44454), 0.70, 860, False, 6),
           (bk(44446), 11.20, 1000, False, 5)]
# reloj: (cuadro, segundos, marca) — marca None, "x" o "v"
CONT = [(0, 10, None), (30, 9, None), (46, 9, "x"), (58, 8, None), (75, 8, "x"), (86, 7, None), (100, 6, None),
        (121, 6, "x"), (132, 5, None), (149, 5, "x")]
for j in range(7):
    CONT.append((150 + 4 * j, 3 if j < 3 else 2, "x"))
CONT += [(178, 1, None), (238, 0, None), (254, 0, "v")]
C_BOCINA, C_SWISH, C_COLOR = 238, 249, 254  # el ✓ cuando la pelota ya pasó el aro


def centro(cs, t):
    ks = sorted(cs)
    if t <= ks[0]: return cs[ks[0]]
    if t >= ks[-1]: return cs[ks[-1]]
    for a, b in zip(ks, ks[1:]):
        if a <= t <= b:
            return cs[a] + (cs[b] - cs[a]) * (t - a) / (b - a)


def a916(fr, cx, espejo=False):
    h0, w0 = fr.shape[:2]
    ww = int(round(h0 * 9 / 16))
    x0 = int(round(min(max(cx - ww / 2, 0), w0 - ww)))
    sub = fr[:, x0:x0 + ww]
    if espejo:
        sub = sub[:, ::-1]
    return np.asarray(Image.fromarray(np.ascontiguousarray(sub)).resize((W, H), Image.BICUBIC))


def tamano(src):
    import subprocess as sp
    o = sp.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                         "-of", "csv=p=0", src]).decode().strip().split(",")
    a, b = o[2].split("/")
    return int(o[0]), int(o[1]), float(a) / float(b)


def leer_n(src, t0, n, cx, espejo):
    w0, h0, _ = tamano(src)
    L = Lector(src, t0, w0, h0, uno_a_uno=False)
    out = [a916(L.cuadro(), cx, espejo).copy() for _ in range(n)]
    L.cerrar()
    return out


# ---------- textos ----------
def capa_reloj(n, marca):
    f = fuente("disp_xb", 150)
    txt = f"0:{n:02d}"
    tw = f.getlength(txt)
    mk = 104 if marca else 0
    gap = 38 if marca else 0
    img = Image.new("RGBA", (W, 230), (0, 0, 0, 0))
    x = (W - tw - gap - mk) / 2
    col = CELESTE if marca == "v" else (255, 255, 255)
    sm = Image.new("L", img.size, 0); ds = ImageDraw.Draw(sm)
    ds.text((x, 30 + 4), txt, font=f, fill=255)
    mx, my = x + tw + gap, 66
    if marca == "x":
        ds.line([(mx, my + 4), (mx + mk, my + mk + 4)], fill=255, width=22)
        ds.line([(mx + mk, my + 4), (mx, my + mk + 4)], fill=255, width=22)
    elif marca == "v":
        ds.line([(mx, my + 55), (mx + 36, my + 94), (mx + mk, my + 8)], fill=255, width=22, joint="curve")
    sm = sm.filter(ImageFilter.GaussianBlur(12))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(sm.point(lambda v: int(v * 0.6)))
    img = Image.alpha_composite(img, sh); d = ImageDraw.Draw(img)
    d.text((x, 30), txt, font=f, fill=col + (255,))
    if marca == "x":
        d.line([(mx, my), (mx + mk, my + mk)], fill=(255, 255, 255, 255), width=20)
        d.line([(mx + mk, my), (mx, my + mk)], fill=(255, 255, 255, 255), width=20)
    elif marca == "v":
        d.line([(mx, my + 51), (mx + 36, my + 90), (mx + mk, my + 4)], fill=CELESTE + (255,), width=20, joint="curve")
    return img


_cr = {}


def reloj(n, marca):
    if (n, marca) not in _cr:
        _cr[(n, marca)] = capa_reloj(n, marca)
    return _cr[(n, marca)]


T_PREG = capa_texto(["¿LA METE ANTES", "DE QUE SUENE?"], "disp_b", 80)
T_ULT = capa_texto(["ÚLTIMO TIRO"], "disp_xb", 84, color=CELESTE)
T_ADENTRO = capa_texto(["¡ADENTRO!"], "disp_xb", 146, color=CELESTE)
T_MUNDO = capa_texto(["EL ÚLTIMO TIRO", "LO VE TODO EL MUNDO"], "disp_xb", 84)
T_MIL = capa_texto(["LOS MIL", "DE ANTES…"], "disp_xb", 124)
T_NADIE = capa_texto(["NADIE."], "disp_xb", 190)
T_ESOS = capa_texto(["ESTA PLACA", "ES POR ESOS MIL"], "disp_xb", 92)
T_SEGUIR = capa_texto(["SEGUIR HASTA", "LOGRARLO."], "disp_xb", 112)
T_VIENE = capa_texto(["VIENE CON", "CADA REMERA"], "disp_xb", 96)
T_VOS = capa_texto(["¿CUÁNTOS TIROS", "TE FALTAN A VOS?"], "disp_xb", 96)
# CTA (mismos datos verificados que M4)
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
    return desde + (1 - desde) * suave(k / dur)


def pegar_esc(img, capa, y, esc=1.0, alfa=1.0, dx=0):
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
    im = fill_cover(foto, W, H, cx=0.5, cy=0.55, zoom=1.0 + 0.05 * k / 85)
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


# ---------- render ----------
cod = None; control = []
if not SOLO_AUDIO:
    raf = []
    for src, t0, cx, esp in RAFAGA:
        raf += leer_n(src, t0, 4, cx, esp)
    mon = []
    for src, t0, cx, esp, n in MONTAJE:
        mon += leer_n(src, t0, n, cx, esp)
    cod = Codificador(salida + ".tmp.mp4")
lect = None; actual = None; ultimo = None
for c in range(0 if SOLO_AUDIO else N):
    if c < 422:
        for a, b, src, t0, cs, esp, vel in PLAN:
            if a <= c < b:
                break
        k = c - a
        if src == "RAFAGA":
            img = raf[min(k, len(raf) - 1)].copy()
        elif src == "MONTAJE":
            img = mon[min(k, len(mon) - 1)].copy()
        elif src == "CONGELA":
            z = 1.0 + 0.06 * suave(k / 18)
            img = np.asarray(fill_cover(Image.fromarray(ultimo), W, H, cy=0.45, zoom=z)).copy()
        else:
            if actual != a:
                if lect: lect.cerrar()
                w0, h0, fps = tamano(src)
                lect = Lector(src, t0, w0, h0, uno_a_uno=(vel == "nativa")); actual = a
                paso = 1 / fps if vel == "nativa" else 1 / FPS
            img = a916(lect.cuadro(), centro(cs, t0 + k * paso), esp).copy()
            ultimo = img.copy()
        g = bn(img, contraste=1.28)
        if C_COLOR <= c < 344:  # vuelve el color con el ✓ (13733 y el jugador); los mil de antes y «nadie», en B/N
            m = suave((c - C_COLOR) / 6)
            img = (g * (1 - m) + img * m).astype(np.uint8)
        else:
            img = g
        if c < 232 or 278 <= c:
            img = oscurecer_arriba(img, 640, 0.42)
        img = grano(img, 5, c)
        # textos
        if c < 232:
            pegar(img, T_PREG, 0, 112, alfa=1.0 if c < 226 else 1 - suave((c - 226) / 6))
        if c < 272:
            ev = [e for e in CONT if e[0] <= c][-1]
            kk = c - ev[0]
            sacude = (12 * np.sin(kk * 2.4) * (1 - kk / 5)) if (ev[2] == "x" and kk < 5) else 0
            late = 1.0 + (0.06 * max(0.0, np.cos(2 * np.pi * (c - 178) / 15)) if (ev[1] == 1) else 0)
            esc = pop(kk, 4, 1.22 if ev[2] else 1.12) * late
            pegar_esc(img, reloj(ev[1], ev[2]), 322, esc=esc, dx=sacude, alfa=1 - suave((c - 265) / 6))
        if 182 <= c < 232:
            pegar_esc(img, T_ULT, 1500, esc=pop(c - 182, 4, 1.3), alfa=suave((c - 182) / 3))
        if C_COLOR - 1 <= c < 278:
            pegar_esc(img, T_ADENTRO, 1380, esc=pop(c - C_COLOR + 1, 5, 1.18), alfa=suave((c - C_COLOR + 1) / 2))
        if 284 <= c < 344:
            pegar_esc(img, T_MUNDO, 180, esc=pop(c - 284, 4, 1.15), alfa=suave((c - 284) / 3) * (1 - suave((c - 338) / 5)))
        if 350 <= c < 390:
            pegar_esc(img, T_MIL, 300, esc=pop(c - 350, 5, 1.2), alfa=suave((c - 350) / 3))
        if c >= 392:
            pegar_esc(img, T_NADIE, 760, esc=pop(c - 392, 5, 1.3), alfa=suave((c - 392) / 3))
    elif c < 476:  # IMG_5359: la placa en su mano, cae al deck — «Esta placa es por esos mil»
        if c == 422:
            if lect: lect.cerrar()
            lect = lector_gl("sdr_5359.mp4", 9.6)
        img = grano(oscurecer_arriba(lect.cuadro().copy(), 640, 0.45), 3, c)
        if c >= 424:
            pegar_esc(img, T_ESOS, 180, esc=pop(c - 424, 4, 1.15), alfa=suave((c - 424) / 3))
    elif c < 544:  # IMG_5361: la placa junto a las dos remeras — «seguir hasta lograrlo»
        if c == 476:
            lect.cerrar(); lect = lector_gl("sdr_5361.mp4", 0.6)
        img = grano(oscurecer_arriba(lect.cuadro().copy(), 720, 0.55), 3, c)
        if c >= 496:
            pegar_esc(img, T_SEGUIR, 170, esc=pop(c - 496, 5, 1.18), alfa=suave((c - 496) / 3))
    elif c < 596:  # IMG_5333: espalda de la remera blanca y de la negra — «viene con cada remera»
        if c == 544:
            lect.cerrar(); lect = lector_gl("sdr_5333.mp4", 0.5)
        img = grano(oscurecer_arriba(lect.cuadro().copy(), 640, 0.45), 3, c)
        if c >= 554:
            pegar_esc(img, T_VIENE, 190, esc=pop(c - 554, 4, 1.2), alfa=suave((c - 554) / 3))
    elif c < 658:  # el aro vacío: «¿Cuántos tiros te faltan a vos?»
        if c == 596:
            lect.cerrar(); lect = Lector(bk(13733), 4.5, 1280, 720)
        img = a916(lect.cuadro(), 560).copy()
        img = grano(bn(img, contraste=1.28), 5, c)
        if c >= 600:
            pegar_esc(img, T_VOS, 300, esc=pop(c - 600, 5, 1.2), alfa=suave((c - 600) / 3))
    else:
        if lect: lect.cerrar(); lect = None
        img = cuadro_cta(c - 658)
    cod.poner(img)
if lect: lect.cerrar()

# ---------- sonido ----------
dur = N / FPS
x = lienzo(dur)
rng = np.random.default_rng(12)
x += np.convolve(rng.normal(0, 1, len(x)), np.ones(30) / 30, "same") * 0.025  # aire de gimnasio


def aro(x, t, g=0.5):
    """golpe metálico contra el aro: parciales que se apagan + ruido corto + golpe grave del tablero."""
    n = int(0.9 * SR); i = int(t * SR); tt = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * tt + k) * np.exp(-tt / d)
            for k, (f, a, d) in enumerate([(612, 1.0, 0.22), (1227, 0.6, 0.15), (1866, 0.45, 0.10), (2650, 0.3, 0.06)]))
    r = np.random.default_rng(int(t * 1000)).normal(0, 1, n) * np.exp(-tt / 0.012) * 0.6
    seg = (s * 0.5 + r) * g
    x[i:i + n] += seg[: len(x) - i]
    golpe(x, t, g * 0.5, f0=70, caida=0.12)


def bocina(x, t, g=0.3, d=0.75):
    n = int(d * SR); i = int(t * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f0 * h * tt) / h for f0 in (349.0, 352.5) for h in range(1, 16, 2))
    s = np.tanh(1.6 * s / 2) * np.minimum(1, tt / 0.01) * np.minimum(1, (d - tt) / 0.05)
    x[i:i + n] += (s * g)[: len(x) - i]


def red(x, t, g=0.35, d=0.45):
    """la red: ruido filtrado agudo que crece y se apaga (swish)."""
    n = int(d * SR); i = int(t * SR)
    r = np.random.default_rng(int(t * 991)).normal(0, 1, n)
    F = np.fft.rfft(r); fr = np.fft.rfftfreq(n, 1 / SR)
    F *= np.exp(-0.5 * (np.log(np.maximum(fr, 1) / 4500) / 0.6) ** 2)
    s = np.fft.irfft(F, n); s /= np.abs(s).max() + 1e-9
    e = np.minimum(1, np.arange(n) / (0.08 * SR)) * np.exp(-np.maximum(0, np.arange(n) - 0.08 * SR) / (0.12 * SR))
    x[i:i + n] += (s * e * g)[: len(x) - i]


# pulso que se acelera mientras el reloj baja (más bajo debajo de la voz)
t = 0.0
while t < 150 / FPS:
    golpe(x, t, 0.14 if (44 / FPS <= t < 100 / FPS) else 0.3, f0=48, caida=0.16); t += 0.5 if t < 100 / FPS else 0.36
for cc, n, m in CONT:
    tt = cc / FPS
    if m == "x" and cc < 150:
        aro(x, tt, 0.42); golpe(x, tt + 0.02, 0.5, f0=60, caida=0.25)
    elif m is None and 0 < cc < C_BOCINA:
        tic(x, tt, 0.2, 2000)
for j in range(7):  # ráfaga
    tt = (150 + 4 * j) / FPS
    aro(x, tt, 0.3); golpe(x, tt, 0.4, f0=54, caida=0.1)
barrido(x, 150 / FPS, 28 / FPS, 0.25, 200, 6000)
for tt in np.arange(178 / FPS, 214 / FPS, 0.5):  # latido del último segundo
    golpe(x, tt, 0.35, f0=46, caida=0.2)
# congelado: casi silencio; la pelota baja; bocina en el aire; entra
i0, i1 = int(214 / FPS * SR), int(C_COLOR / FPS * SR)
x[i0:i1] *= 0.15
golpe(x, 222 / FPS, 0.25, f0=44, caida=0.25)
bocina(x, C_BOCINA / FPS, 0.3)
red(x, C_SWISH / FPS, 0.4)
golpe(x, C_COLOR / FPS, 0.5, f0=44, caida=0.7)
brillo(x, C_COLOR / FPS, 0.08)
colchon(x, C_COLOR / FPS, 344 / FPS, [146.8, 220.0, 293.7, 370.0], 0.05, ataque=0.2, suelta=0.5)
# los mil de antes: tics secos por intento, en B/N
cc = 344
for src, t0, cx, esp, n in MONTAJE:
    tic(x, cc / FPS, 0.18, 1500); golpe(x, cc / FPS, 0.18, f0=58, caida=0.08); cc += n
golpe(x, 392 / FPS, 0.4, f0=44, caida=0.5)  # «nadie»
colchon(x, 422 / FPS, 596 / FPS, [146.8, 220.0, 293.7, 370.0], 0.05, ataque=0.3, suelta=0.6)
for cc in (278, 344, 422, 476, 544, 596):
    barrido(x, cc / FPS - 0.12, 0.3, 0.15, 400, 5000)
brillo(x, 496 / FPS, 0.18); golpe(x, 496 / FPS, 0.4, f0=50, caida=0.4)  # «seguir»
golpe(x, 596 / FPS, 0.45, f0=50, caida=0.3)
golpe(x, 658 / FPS, 0.45, f0=56, caida=0.4); brillo(x, 661 / FPS, 0.12)
colchon(x, 658 / FPS, dur, [110.0, 164.8, 220.0, 277.2], 0.07, ataque=0.15, suelta=0.4)

ids = ["x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "x9"]
v = {k: leer_wav(os.path.join(VOZ, f"{k}.wav")) for k in ids}
for k, db in (("x2", 6.0), ("x4", 5.0), ("x5", 2.0), ("x8", 2.0), ("x9", 2.0)):
    v[k] = v[k] * 10 ** (db / 20)
corte = int(0.674 * SR)  # x2: «Erra.» | «Y vuelve a errar.»
v["x2a"], v["x2b"] = v["x2"][:int(0.5 * SR)], v["x2"][corte:]
voces_k = [(2, "x1"), (49, "x2a"), (60, "x2b"), (180, "x3"), (253, "x4"), (282, "x5"), (424, "x6"), (480, "x7"),
           (598, "x8"), (662, "x9")]
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
