# M2 «¿Cuál de los tres se rinde?» · FOMO de la placa por el valor (seguir hasta lograrlo) + Black Friday.
# Tres franjas en paralelo (estudio, gimnasio, ring; clips de Mixkit, licencia libre) → «Ninguno.» →
# la placa real en color → la frase FOMO sobre IMG_7896 (tomas reales) → cierre Black Friday con el precio de la web.
# Uso: python3 scripts/fomo/m2.py SALIDA.mp4 [--sin-musica]
import sys, os, json
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from comun import *

MX = os.path.join(RAIZ, "TRABAJO/fomo/mixkit")
VOZ = os.path.join(RAIZ, "TRABAJO/fomo/voz_m2")
PLACA = os.path.join(RAIZ, "TRABAJO/fomo/rcs-placa.jpg")
TOMA = os.path.join(RAIZ, "ORIGINALES/IMG_7896.mov")
salida = sys.argv[1]
SIN_MUSICA = "--sin-musica" in sys.argv
N = 650
BANDAS_Y = [370, 785, 1200]; BH = 400

def mx(i):
    return os.path.join(MX, f"h_{i}.mp4")

def crop_band(i, y):
    w, h = (1920, 1080) if i in (25575, 50112, 28321, 50133, 40250) else (1280, 720)
    ch = int(round(w * BH / W))
    return f"{w}:{ch}:0:{y}"

# (cuadro inicio, cuadro fin, clip, t0 en la fuente, recorte y, rótulo)
PLAN = {
    0: [(0, 90, 25575, 1.0, 120, "DESAPROBÓ EL FINAL"), (90, 170, 50112, 0.5, 180, "SE VUELVE A ANOTAR"),
        (170, 235, 25575, 8.0, 120, "OTRA VEZ: UN 2"), (235, 300, 50112, 3.9, 200, "TERCER INTENTO"),
        (330, 390, 46416, 3.7, 0, "SE RECIBIÓ")],
    1: [(0, 70, 23938, 1.4, 40, "NO LLEGA A LOS 100 KG"), (70, 150, 23653, 0.4, 110, "VUELVE A ENTRENAR"),
        (150, 220, 23923, 12.2, 110, "TAMPOCO"), (220, 300, 23653, 9.8, 110, "UNA SEMANA MÁS"),
        (330, 390, 48541, 0.25, 0, "LEVANTÓ LOS 100")],
    2: [(0, 60, 23926, 0.8, 200, "AL PISO EN EL PRIMER ROUND"), (60, 140, 23926, 4.2, 200, "CUENTA: 6, 7…"),
        (140, 300, 23634, 0.0, 120, "NADIE ESPERA QUE SE LEVANTE"), (330, 390, 23634, 6.9, 120, "SE LEVANTÓ")],
}
TIC_CORTES = sorted({a for b in PLAN.values() for a, *_ in b if 0 < a < 300})

# ---------- capas de texto (se renderizan una vez) ----------
T_PREG = capa_texto(["¿Cuál de los tres", "se rinde?"], "disp_b", 84)
T_NING = capa_texto(["Ninguno."], "disp_b", 132)
T_NING_S = capa_texto(["Ninguno."], "disp_b", 96)
ROT = {}
for b in PLAN.values():
    for *_, r in b:
        if r not in ROT:
            t = capa_texto([r], "inter_b", 30, sombra=0, track=2, radio_sombra=0, alinear="l")
            bb = t.getbbox(); t = t.crop((0, 0, bb[2] + 2, bb[3] + 4))
            chip = Image.new("RGBA", (t.width + 36, t.height + 22), (0, 0, 0, 150))
            chip.alpha_composite(t, (18, 9)); ROT[r] = chip
T_SIG1 = capa_texto(["ESTA PLACA SIGNIFICA"], "inter_sb", 38, track=6)
T_SIG2 = capa_texto(["seguir hasta lograrlo."], "serif", 128)
T_F1 = capa_texto(["Algunos la van a tener."], "disp_b", 74)
T_F2 = capa_texto(["El resto la va a ver en otros."], "disp_b", 74)
T_BF = capa_texto(["BLACK FRIDAY"], "disp_xb", 132)
T_PCT = capa_texto(["−25%"], "disp_xb", 250, color=CELESTE)
T_PRE = capa_texto(["$48.750"], "disp_b", 128)
T_ANT = capa_texto(["antes $65.000"], "inter_m", 46, color=(215, 215, 215), tachar=None)
T_INC = capa_texto(["Remera + placa · Envío gratis"], "inter_sb", 42)
T_WEB = capa_texto(["rocce.shop"], "inter_b", 50, color=CELESTE)

# «antes $65.000» con el precio tachado (solo el número)
def antes():
    img = T_ANT.copy(); from PIL import ImageDraw
    f = fuente("inter_m", 46); txt = "antes $65.000"
    x0 = (img.width - f.getlength(txt)) / 2 + f.getlength("antes ")
    x1 = (img.width - f.getlength(txt)) / 2 + f.getlength(txt)
    y = 10 + f.getmetrics()[0] * 0.64
    ImageDraw.Draw(img).line([(x0 - 3, y), (x1 + 3, y)], fill=(215, 215, 215, 255), width=4)
    return img
T_ANT = antes()

# ---------- placa ----------
placa = Image.open(PLACA).convert("RGB")  # 1800×920, foto real de la web
fondo_placa = np.asarray(fill_cover(placa, W, H, zoom=1.0).filter(ImageFilter.GaussianBlur(40))).astype(np.float32) * 0.28

def cuadro_placa(k):
    """k: cuadro desde c390. Pedazos (borde/letras, año) y después la placa entera con empuje y barrido de luz."""
    if k < 8:
        img = fill_cover(placa, W, H, cx=0.30, cy=0.33, zoom=1.0 + 0.02 * k)
        return np.asarray(img).copy()
    if k < 16:
        img = fill_cover(placa, W, H, cx=0.51, cy=0.80, zoom=1.0 + 0.02 * (k - 8))
        return np.asarray(img).copy()
    p = (k - 16) / 64
    esc = 1.0 + 0.07 * suave(p)
    pw = int(W * 0.90 * esc); ph = int(pw * placa.height / placa.width)
    im = np.asarray(placa.resize((pw, ph), Image.LANCZOS)).astype(np.float32)
    # barrido de luz diagonal sobre el metal
    xx, yy = np.meshgrid(np.arange(pw), np.arange(ph))
    c = -0.3 + 1.6 * suave(min(1, p * 1.4))
    d = (xx / pw + yy / ph * 0.35) - c
    im = 255 - (255 - im) * (1 - 0.35 * np.exp(-(d / 0.08) ** 2)[..., None])
    base = fondo_placa.copy()
    x0 = (W - pw) // 2; y0 = (H - ph) // 2 - 30
    base[y0:y0 + ph, x0:x0 + pw] = im
    return np.clip(base, 0, 255).astype(np.uint8)

# ---------- render ----------
cod = Codificador(salida + ".tmp.mp4")
lect = {}
control = dict(repetidos=[], textos=[])

def franja(bi, c):
    for (a, b_, clip, t0, cy, rot) in PLAN[bi]:
        if a <= c < b_:
            key = (bi, a)
            if key not in lect:
                for k in [k for k in lect if k[0] == bi]:
                    lect.pop(k).cerrar()
                lect[key] = Lector(mx(clip), t0, W, BH, crop=crop_band(clip, cy))
            fr = lect[key].cuadro()
            return bn(fr, contraste=1.22, ganancia=2.3 if clip == 23653 else 1.0), rot, c - a
    return None, None, None

toma = None
for c in range(N):
    img = np.zeros((H, W, 3), np.uint8)
    if c < 390:
        for bi in range(3):
            fr, rot, kk = franja(bi, c)
            y = BANDAS_Y[bi]
            if fr is not None:
                img[y:y + BH] = fr
                pegar(img, ROT[rot], 22, y + 20, alfa=suave(kk / 4))
        img = grano(img, 6, c)
        if c < 300:
            pegar(img, T_PREG, 0, 150)
        elif 310 <= c < 330:
            pegar(img, T_NING, 0, (H - T_NING.height) // 2, alfa=suave((c - 310) / 3))
        elif c >= 330:
            pegar(img, T_NING_S, 0, 200)
    elif c < 470:
        k = c - 390
        img = cuadro_placa(k)
        if c >= 406:
            pegar(img, T_SIG1, 0, 560, alfa=suave((c - 406) / 5))
        if c >= 433:
            pegar(img, T_SIG2, 0, 1290, alfa=suave((c - 433) / 6))
    else:
        if toma is None:
            toma = Lector(TOMA, 0.15, W, H, uno_a_uno=True)
        fr = toma.cuadro().astype(np.float32)
        # degradés para leer el texto sin tapar las remeras (están entre y≈860 y 1150)
        yy = np.arange(H)[:, None, None]
        osc = np.clip((820 - yy) / 560, 0, 1) * 0.80 + np.clip((yy - 1180) / 420, 0, 1) * 0.78
        img = (fr * (1 - osc)).astype(np.uint8)
        if c < 555:
            pegar(img, T_F1, 0, 1300, alfa=suave((c - 472) / 5))
            if c >= 512:
                pegar(img, T_F2, 0, 1400, alfa=suave((c - 512) / 5))
        else:
            k = c - 555
            pegar(img, T_BF, 0, 190, alfa=suave(k / 4))
            pegar(img, T_PCT, 0, 330, alfa=suave((k - 4) / 4))
            pegar(img, T_PRE, 0, 1215, alfa=suave((k - 10) / 4))
            pegar(img, T_ANT, 0, 1355, alfa=suave((k - 10) / 4))
            pegar(img, T_INC, 0, 1430, alfa=suave((k - 16) / 4))
            pegar(img, T_WEB, 0, 1495, alfa=suave((k - 16) / 4))
    cod.poner(img)
for l in lect.values():
    l.cerrar()
toma.cerrar()

# ---------- sonido ----------
dur = N / FPS
x = lienzo(dur)
v = {k: leer_wav(os.path.join(VOZ, f"{k}.wav")) for k in ("v1", "v2b", "v3", "v4", "v5")}
golpe(x, 0.0, 0.9)
if not SIN_MUSICA:
    dron(x, 0.0, 10.0, 55, 0.10)
# reloj que se acelera (el tiempo importa): 2 → 4 tics por segundo hasta el corte a negro
t = 0.25
while t < 10.0:
    tic(x, t, 0.10 if not SIN_MUSICA else 0.14, 1500)
    t += 0.5 - 0.25 * (t / 10.0)
for a in TIC_CORTES:
    barrido(x, a / FPS - 0.12, 0.22, 0.10)
golpe(x, 310 / FPS, 1.0, f0=44, caida=0.8)
barrido(x, 328 / FPS, 0.35, 0.18)
if not SIN_MUSICA:
    colchon(x, 11.0, 13.2, [110.0, 138.6, 164.8], 0.09)
    colchon(x, 13.0, dur, [146.8, 185.0, 220.0, 293.7], 0.08, ataque=0.4, suelta=0.5)
brillo(x, 390 / FPS, 0.16)
brillo(x, 406 / FPS, 0.12)
golpe(x, 555 / FPS, 0.55, f0=60, caida=0.35)
brillo(x, 555 / FPS, 0.10)
voces = [(4 / FPS, v["v1"]), (314 / FPS, v["v2b"]), (400 / FPS, v["v3"]), (472 / FPS, v["v4"]), (558 / FPS, v["v5"])]
wav = salida + ".wav"
nivel, _ = mezclar(x, voces, dur, wav)
cod.cerrar(audio=wav)
os.replace(salida + ".tmp.mp4", salida)
os.remove(wav)
control.update(cuadros=cod.n, duracion=dur, sonoridad=nivel)
json.dump(control, open(salida + ".control.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(control, ensure_ascii=False))
