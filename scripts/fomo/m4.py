# M4 «¿En qué intento lo logra?» · FOMO de la placa + Black Friday (26/11/2026).
# Apuesta desde el cuadro 0 (un skater se cae: INTENTO 1 ✗), evidencia a toda velocidad (caídas, se levanta, se sienta,
# vuelve a agarrar la tabla, contador que se acelera), congelado en el aire, giro (✓ INTENTO 23, vuelve el color),
# reenganche con la placa real de Gianluca (IMG_5361 acercamiento, IMG_5359 foco = «seguir hasta lograrlo»),
# qué es (metal, viene con cada remera: IMG_5325), «¿Y vos, en qué intento vas?» y CTA sobre IMG_8002 con la placa sumada.
# Clips de skate de Mixkit (licencia libre): 6719, 6495, 34383, 34389, 34384. Voz Firme 04 (voz_m4.tsv).
# Uso: python3 scripts/fomo/m4.py SALIDA.mp4
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
sys.path.insert(0, os.path.dirname(__file__))
from comun import *

SK = os.path.join(RAIZ, "TRABAJO/fomo/sk")
GL = os.path.join(RAIZ, "TRABAJO/fomo/gl")  # tomas de Gianluca del 26/11 pasadas a SDR (ver m1.py, TONEMAP)
VOZ = os.path.join(RAIZ, "TRABAJO/fomo/voz_m4")
VOZ56 = os.path.join(RAIZ, "TRABAJO/fomo/voz_m4b/w56.wav")  # «Significa una sola cosa: seguir hasta lograrlo.» («seguir» a 1,66 s)
PLACA = os.path.join(RAIZ, "TRABAJO/fomo/rcs-placa.jpg")
FOTO_CTA = os.path.join(RAIZ, "TRABAJO/fomo/f8002.png")
salida = sys.argv[1]
N = 736


def sk(i):
    return os.path.join(SK, f"h_{i}.mp4")


# ---------- planos: (desde, hasta, fuente, t0, centros {t_src: x}, espejo, bn) ----------
C6719 = {1.4: 1056, 1.7: 864, 1.9: 800, 2.2: 672, 2.4: 608, 2.7: 512, 2.8: 448, 2.9: 480, 3.0: 416, 3.2: 352, 3.4: 288}
C34384 = {2.5: 420, 4.0: 450, 5.5: 560, 7.0: 650}
C6495 = {1.5: 714, 1.75: 644, 2.0: 556, 2.25: 501, 2.5: 476, 2.75: 464, 3.5: 480, 4.5: 480}
PLAN = [
    (0, 50, sk(6719), 1.60, C6719, False),
    (50, 84, sk(6495), 1.60, C6495, False),
    (84, 102, sk(6495), 3.70, C6495, False),
    (102, 125, sk(6719), 2.30, C6719, True),
    (125, 142, sk(6495), 2.10, C6495, True),
    (142, 180, sk(34383), 0.80, {0: 860}, False),
    (180, 199, "REV", 0, None, False),  # 34383 al revés: vuelve a agarrar la tabla
    (199, 227, "RAFAGA", 0, None, False),
    (227, 249, sk(34389), 4.40, {0: 960}, False),
    (249, 275, sk(34384), 2.60, C34384, False),
    (275, 285, "CONGELA", 0, None, False),
    (285, 335, sk(34384), 5.45, C34384, False),
]
# contador: (cuadro, número, marca) — marca: None, "x" o "v"
CONT = [(0, 1, None), (40, 1, "x"), (50, 2, None), (82, 2, "x"), (102, 5, None), (121, 5, "x"), (125, 9, None),
        (135, 9, "x"), (142, 14, None), (180, 15, None)]
for j in range(7):
    CONT.append((199 + 4 * j, 16 + j, "x"))
CONT += [(227, 23, None), (302, 23, "v")]
C_COLOR = 302  # vuelve el color con el ✓


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


def leer_n(src, t0, n):
    w0, h0, fps = tamano(src)
    L = Lector(src, t0, w0, h0)
    out = [L.cuadro().copy() for _ in range(n)]
    L.cerrar()
    return out, fps


# ---------- textos ----------
def capa_contador(n, marca):
    f = fuente("disp_xb", 124)
    txt = f"INTENTO {n}"
    tw = f.getlength(txt)
    mk = 100 if marca else 0
    gap = 34 if marca else 0
    img = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    x = (W - tw - gap - mk) / 2
    col = CELESTE if marca == "v" else (255, 255, 255)
    sm = Image.new("L", img.size, 0); ds = ImageDraw.Draw(sm)
    ds.text((x, 30 + 4), txt, font=f, fill=255)
    d = ImageDraw.Draw(img)
    mx, my = x + tw + gap, 52
    if marca == "x":
        for dd in (ds,):
            dd.line([(mx, my + 4), (mx + mk, my + mk + 4)], fill=255, width=22)
            dd.line([(mx + mk, my + 4), (mx, my + mk + 4)], fill=255, width=22)
    elif marca == "v":
        ds.line([(mx, my + 55), (mx + 35, my + 92), (mx + mk, my + 8)], fill=255, width=22, joint="curve")
    sm = sm.filter(ImageFilter.GaussianBlur(12))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(sm.point(lambda v: int(v * 0.6)))
    img = Image.alpha_composite(img, sh); d = ImageDraw.Draw(img)
    d.text((x, 30), txt, font=f, fill=col + (255,))
    if marca == "x":
        d.line([(mx, my), (mx + mk, my + mk)], fill=(255, 255, 255, 255), width=20)
        d.line([(mx + mk, my), (mx, my + mk)], fill=(255, 255, 255, 255), width=20)
    elif marca == "v":
        d.line([(mx, my + 51), (mx + 35, my + 88), (mx + mk, my + 4)], fill=CELESTE + (255,), width=20, joint="curve")
    return img


_cc = {}


def contador(n, marca):
    if (n, marca) not in _cc:
        _cc[(n, marca)] = capa_contador(n, marca)
    return _cc[(n, marca)]


T_PREG = capa_texto(["¿EN QUÉ INTENTO", "LO LOGRA?"], "disp_b", 80)
T_RINDE = capa_texto(["¿SE RINDE?"], "disp_xb", 84, color=CELESTE)
T_POR = capa_texto(["POR ESO EXISTE", "ESTA PLACA"], "disp_xb", 84)
T_SIGN = capa_texto(["SIGNIFICA", "UNA SOLA COSA:"], "disp_b", 70)
T_SEGUIR = capa_texto(["SEGUIR HASTA", "LOGRARLO."], "disp_xb", 112)
T_METAL = capa_texto(["PLACA DE METAL"], "disp_xb", 84)
T_VIENE = capa_texto(["VIENE CON", "CADA REMERA"], "disp_xb", 96)
T_VOS = capa_texto(["¿Y VOS, EN QUÉ", "INTENTO VAS?"], "disp_xb", 96)
# CTA
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
    """escala de entrada (1 = normal)."""
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


# ---------- CTA: foto IMG_8002 + la placa real sumada, flotando sobre la arena ----------
foto = Image.open(FOTO_CTA).convert("RGB")
pl = Image.open(PLACA).convert("RGB")
PW = 640; PH = int(PW * pl.height / pl.width)
pl = pl.resize((PW, PH), Image.LANCZOS)
pl = Image.fromarray(np.clip(np.asarray(pl).astype(np.float32) * 1.05 + 4, 0, 255).astype(np.uint8))
mask = Image.new("L", (PW, PH), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, PW - 1, PH - 1], 9, fill=255)
PLACA_RGBA = pl.convert("RGBA"); PLACA_RGBA.putalpha(mask)


def placa_cta(k):
    a = np.asarray(PLACA_RGBA).astype(np.float32).copy()
    # brillo que recorre el metal al entrar
    xx, yy = np.meshgrid(np.arange(PW), np.arange(PH))
    c = -0.3 + 1.7 * suave((k - 3) / 16)
    d = (xx / PW + yy / PH * 0.4) - c
    a[..., :3] = 255 - (255 - a[..., :3]) * (1 - 0.4 * np.exp(-(d / 0.07) ** 2)[..., None])
    im = Image.fromarray(a.astype(np.uint8), "RGBA").rotate(-3, resample=Image.BICUBIC, expand=True)
    return im


def cuadro_cta(k):
    im = fill_cover(foto, W, H, cx=0.5, cy=0.5, zoom=1.0 + 0.04 * k / 96)
    a = oscurecer_arriba(np.asarray(im), hasta=900, g=0.42)
    t = k / FPS
    bob = 7 * np.sin(2 * np.pi * t / 2.4)
    ent = suave(k / 9)
    cy = 1612 + bob + (1 - ent) * 90
    # sombra en la arena
    sh = Image.new("L", (W, 240), 0)
    ImageDraw.Draw(sh).ellipse([300, 90, 780, 150], fill=255)
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    s = np.asarray(sh).astype(np.float32) / 255 * 0.42 * ent * (1 - bob / 40)
    y0 = 1690
    a = a.astype(np.float32)
    a[y0:y0 + 240] *= (1 - s[: H - y0])[..., None]
    a = a.astype(np.uint8)
    p = placa_cta(k)
    esc = 0.92 + 0.08 * ent
    p = p.resize((int(p.size[0] * esc), int(p.size[1] * esc)), Image.LANCZOS)
    pegar(a, p, (W - p.size[0]) / 2, cy - p.size[1] / 2, alfa=ent)
    pegar(a, T_BF, 0, 112, alfa=suave(k / 4))
    pegar_esc(a, T_PCT, 222, esc=pop(k - 3, 5, 1.3), alfa=suave((k - 3) / 3))
    pegar(a, T_PRE, 0, 488, alfa=suave((k - 12) / 4))
    pegar(a, T_ANT, 0, 618, alfa=suave((k - 12) / 4))
    pegar(a, T_INC, 0, 692, alfa=suave((k - 20) / 4))
    pegar(a, T_WEB, 0, 1806, alfa=suave((k - 24) / 4))
    return a


# ---------- tomas reales de Gianluca ----------
def lector_gl(nombre, t0):
    return Lector(os.path.join(GL, nombre), t0, W, H)


# ---------- render ----------
rev, _ = leer_n(sk(34383), 1.60, 19)
rev = [a916(f, 860) for f in rev[::-1]]
raf = []
for j in range(7):
    if j % 2 == 0:
        fr, _ = leer_n(sk(6719), 2.90, 4); cs, t0 = C6719, 2.90
    else:
        fr, _ = leer_n(sk(6495), 2.40, 4); cs, t0 = C6495, 2.40
    raf += [a916(f, centro(cs, t0 + i / 30), espejo=(j % 4 >= 2)) for i, f in enumerate(fr)]

cod = Codificador(salida + ".tmp.mp4")
lect = None; actual = None; ultimo = None; control = []
for c in range(N):
    if c < 335:
        for a, b, src, t0, cs, esp in PLAN:
            if a <= c < b:
                break
        k = c - a
        if src == "REV":
            img = rev[min(k, len(rev) - 1)].copy()
        elif src == "RAFAGA":
            img = raf[min(k, len(raf) - 1)].copy()
        elif src == "CONGELA":
            im = Image.fromarray(ultimo)
            z = 1.0 + 0.05 * suave(k / 10)
            img = np.asarray(fill_cover(im, W, H, zoom=z)).copy()
        else:
            if actual != a:
                if lect: lect.cerrar()
                w0, h0, fps = tamano(src)
                lect = Lector(src, t0, w0, h0); actual = a; fps_act = fps
            fr = lect.cuadro()
            img = a916(fr, centro(cs, t0 + k / fps_act), esp).copy()
            ultimo = img.copy()
        # grado: B/N hasta el ✓, después vuelve el color
        g = bn(img, contraste=1.28)
        if c >= C_COLOR:
            m = suave((c - C_COLOR) / 6)
            img = (g * (1 - m) + img * m).astype(np.uint8)
        else:
            img = g
        img = oscurecer_arriba(img, 640, 0.42)
        img = grano(img, 5, c)
        # textos
        if c < C_COLOR + 28:
            pegar(img, T_PREG, 0, 112, alfa=1.0 if c < C_COLOR else 1 - suave((c - C_COLOR) / 6))
        ev = [e for e in CONT if e[0] <= c][-1]
        kk = c - ev[0]
        sacude = (12 * np.sin(kk * 2.4) * (1 - kk / 5)) if (ev[2] == "x" and kk < 5) else 0
        if c < 335:
            pegar_esc(img, contador(ev[1], ev[2]), 322, esc=pop(kk, 4, 1.22 if ev[2] else 1.12), dx=sacude)
        if 142 <= c < 199:
            pegar_esc(img, T_RINDE, 1500, esc=pop(c - 146, 4, 1.3), alfa=suave((c - 146) / 3))
    elif c < 409:  # IMG_5361: acercamiento a la placa junto a las dos remeras
        if c == 335:
            if lect: lect.cerrar()
            lect = lector_gl("sdr_5361.mp4", 0.0)
        img = lect.cuadro().copy()
        img = oscurecer_arriba(img, 720, 0.55)
        img = grano(img, 3, c)
        if c >= 339:
            pegar_esc(img, T_POR, 170, esc=pop(c - 339, 4, 1.15), alfa=suave((c - 339) / 3) * (1 - suave((c - 387) / 4)))
        if c >= 392:
            pegar(img, T_SIGN, 0, 190, alfa=suave((c - 392) / 3))
    elif c < 496:  # IMG_5359: la placa en su mano, el foco llega con «seguir»
        if c == 409:
            lect.cerrar(); lect = lector_gl("sdr_5359.mp4", 6.1)
        img = lect.cuadro().copy()
        img = grano(img, 3, c)
        if c < 442:
            pegar(img, T_SIGN, 0, 190)
        else:
            pegar_esc(img, T_SEGUIR, 330, esc=pop(c - 442, 5, 1.18), alfa=suave((c - 442) / 3))
    elif c < 508:  # IMG_5361 final: la placa de cerca
        if c == 496:
            lect.cerrar(); lect = lector_gl("sdr_5361.mp4", 74 / 30)
        img = lect.cuadro().copy()
        img = oscurecer_arriba(img, 720, 0.6)
        pegar_esc(img, T_METAL, 200, esc=pop(c - 498, 4, 1.2), alfa=suave((c - 498) / 2))
    elif c < 586:  # IMG_5325: la Founders blanca
        if c == 508:
            lect.cerrar(); lect = lector_gl("sdr_5325.mp4", 1.2)
        img = lect.cuadro().copy()
        img = oscurecer_arriba(img, 640, 0.45)
        img = grano(img, 3, c)
        if c < 516:
            pegar(img, T_METAL, 0, 200, alfa=1 - suave((c - 510) / 5))
        if c >= 541:
            pegar_esc(img, T_VIENE, 190, esc=pop(c - 541, 4, 1.2), alfa=suave((c - 541) / 3))
    elif c < 640:  # vuelve el skater en el piso: «¿Y vos, en qué intento vas?»
        if c == 586:
            lect.cerrar(); lect = Lector(sk(6495), 3.0, 1280, 720)
        fr = lect.cuadro()
        img = a916(fr, 476).copy()
        img = grano(bn(img, contraste=1.28), 5, c)
        if c >= 589:
            pegar_esc(img, T_VOS, 300, esc=pop(c - 589, 5, 1.2), alfa=suave((c - 589) / 3))
    else:
        if lect: lect.cerrar(); lect = None
        img = cuadro_cta(c - 640)
    cod.poner(img)
if lect: lect.cerrar()

# ---------- sonido ----------
dur = N / FPS
x = lienzo(dur)
rng = np.random.default_rng(11)
amb = np.convolve(rng.normal(0, 1, len(x)), np.ones(30) / 30, "same") * 0.025
x += amb
# pulso que se acelera durante la evidencia
t = 0.0
while t < 199 / FPS:
    golpe(x, t, 0.32, f0=48, caida=0.16); t += 0.5
for j in range(7):
    tt = (199 + 4 * j) / FPS
    golpe(x, tt, 0.45, f0=52, caida=0.12); tic(x, tt, 0.2, 2400)
for tt in np.arange(227 / FPS, 275 / FPS, 0.25):
    golpe(x, tt, 0.3, f0=50, caida=0.1)
barrido(x, 227 / FPS, 48 / FPS, 0.28, 180, 6000)  # subida hasta el congelado
# caídas: golpe seco + tabla
for cc, n, m in CONT:
    tt = cc / FPS
    if m == "x":
        golpe(x, tt, 0.85, f0=62, caida=0.3); tic(x, tt + 0.01, 0.3, 900)
    elif m is None and cc > 0:
        tic(x, tt, 0.16, 2200)
# congelado: casi silencio (se apaga el ambiente) y el giro
i0, i1 = int(275 / FPS * SR), int(302 / FPS * SR)
x[i0:i1] *= 0.15
golpe(x, 302 / FPS, 1.0, f0=44, caida=0.9)
brillo(x, 302 / FPS, 0.14)
colchon(x, 302 / FPS, 586 / FPS, [146.8, 220.0, 293.7, 370.0], 0.05, ataque=0.25, suelta=0.6)
for cc in (335, 409, 496, 508, 586):
    barrido(x, cc / FPS - 0.12, 0.3, 0.16, 400, 5000)
brillo(x, 442 / FPS, 0.2)
golpe(x, 442 / FPS, 0.45, f0=50, caida=0.4)
golpe(x, 586 / FPS, 0.5, f0=50, caida=0.3)
golpe(x, 640 / FPS, 0.75, f0=56, caida=0.5)
brillo(x, 643 / FPS, 0.12)
colchon(x, 640 / FPS, dur, [110.0, 164.8, 220.0, 277.2], 0.07, ataque=0.15, suelta=0.4)

v = {k: leer_wav(os.path.join(VOZ, f"{k}.wav")) for k in ("w1", "w2", "w3", "w4", "w7", "w8", "w9")}
v["w56"] = leer_wav(VOZ56)
voces = [(2 / FPS, v["w1"]), (146 / FPS, v["w2"]), (304 / FPS, v["w3"]), (339 / FPS, v["w4"]), (392 / FPS, v["w56"]),
         (498 / FPS, v["w7"]), (589 / FPS, v["w8"]), (644 / FPS, v["w9"])]
wav = salida + ".wav"
nivel, _ = mezclar(x, voces, dur, wav)
cod.cerrar(audio=wav)
os.replace(salida + ".tmp.mp4", salida); os.remove(wav)
json.dump(dict(cuadros=cod.n, duracion=dur, sonoridad=nivel, voces=[(round(a, 2), k) for (a, _), k in
          zip(voces, ["w1", "w2", "w3", "w4", "w56", "w7", "w8", "w9"])]), open(salida + ".control.json", "w"), indent=1)
print(cod.n, nivel)
