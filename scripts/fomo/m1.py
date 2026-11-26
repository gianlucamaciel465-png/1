# M1 «POV: el amigo que tiene la placa» · FOMO social con texto estilo Snapchat + Black Friday.
# Amigo que estudia (clips de Mixkit, licencia libre) → giro de cabeza (barrido) → la placa real (foto de la web) →
# «y yo todavía sin la mía» → cierre Black Friday sobre una foto real de las dos remeras.
# v02 (26/11): el plano de la placa es el video de Gianluca (IMG_5359, su mano con la placa en el deck; HLG → SDR BT.709).
# Si no está ese video, vuelve a la foto de la web (v01).
# Uso: python3 scripts/fomo/m1.py SALIDA.mp4
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
sys.path.insert(0, os.path.dirname(__file__))
from comun import *

MX = os.path.join(RAIZ, "TRABAJO/fomo/mixkit")
PLACA = os.path.join(RAIZ, "TRABAJO/fomo/rcs-placa.jpg")
FOTO_CTA = os.path.join(RAIZ, "TRABAJO/fomo/f8002.png")  # IMG_8002 a 0,30 s (cuadro real)
CUARTO = os.path.join(RAIZ, "TRABAJO/fomo/f50126.png")  # 50126 a 6,9 s: el cuarto del amigo, desenfocado
# IMG_5359 de 6,1 a 9,0 s: placa fuera de foco → foco a los 7,2 s (k=33) → nítida con el reflejo del metal
ORIG_5359 = "/mnt/project-files/material_gianluca/2026-11-26/IMG_5359.mov"
PLACA_VIDEO = os.path.join(RAIZ, "TRABAJO/fomo/gl/sdr_5359.mp4")
T0_PLACA, K_FOCO = 6.1, 33
TONEMAP = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
if not os.path.exists(PLACA_VIDEO) and os.path.exists(ORIG_5359):
    os.makedirs(os.path.dirname(PLACA_VIDEO), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", ORIG_5359, "-map", "0:v:0", "-vf", TONEMAP + ",scale=1080:1920:flags=lanczos",
                    "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", PLACA_VIDEO], check=True)
USAR_VIDEO = os.path.exists(PLACA_VIDEO)
C_CAP2 = 156 if USAR_VIDEO else 168  # con el video, el texto entra con la placa todavía borrosa y el foco la resuelve
Y_CAP2 = 560 if USAR_VIDEO else 1330  # arriba de la placa (en el video ocupa y≈800–1440)
salida = sys.argv[1]
N = 300
CAP1 = "POV: vas a la casa de ese amigo que se mata estudiando, siempre aprueba y tiene la placa"
CAP2 = "y yo todavía sin la mía"


def barra_snap(texto, size=44, ancho_txt=960):
    """Barra de texto estilo Snapchat: franja negra translúcida de lado a lado, texto blanco centrado."""
    f = fuente("inter_m", size)
    pal = texto.split(); lineas = []; cur = ""
    for p in pal:
        prueba = (cur + " " + p).strip()
        if f.getlength(prueba) <= ancho_txt:
            cur = prueba
        else:
            lineas.append(cur); cur = p
    lineas.append(cur)
    lh = int(size * 1.22); pad = 16
    img = Image.new("RGBA", (W, lh * len(lineas) + 2 * pad), (0, 0, 0, 140))
    d = ImageDraw.Draw(img)
    for k, ln in enumerate(lineas):
        d.text(((W - f.getlength(ln)) / 2, pad + k * lh + 2), ln, font=f, fill=(255, 255, 255, 255))
    return img


B1, B2 = barra_snap(CAP1), barra_snap(CAP2)

# planos de Mixkit en 9:16 (fuente 1920×1080 → ventana 607×1080)
PLANOS = [(0, 60, 50133, 1.0, 730), (60, 105, 50112, 1.2, 760), (105, 138, 50126, 6.0, 470)]

placa = Image.open(PLACA).convert("RGB")
fondo = np.asarray(fill_cover(Image.open(CUARTO).convert("RGB"), W, H, cx=0.62).filter(ImageFilter.GaussianBlur(28))).astype(np.float32) * 0.42


def cuadro_placa(k, n=87):
    p = k / n
    esc = 0.86 + 0.08 * suave(p)
    pw = int(W * esc); ph = int(pw * placa.height / placa.width)
    im = np.asarray(placa.resize((pw, ph), Image.LANCZOS)).astype(np.float32)
    xx, yy = np.meshgrid(np.arange(pw), np.arange(ph))
    c = -0.3 + 1.6 * suave(min(1, p * 1.3))
    d = (xx / pw + yy / ph * 0.35) - c
    im = 255 - (255 - im) * (1 - 0.33 * np.exp(-(d / 0.08) ** 2)[..., None])
    base = fondo.copy()
    # pulso de cámara en mano (POV)
    dx = 6 * np.sin(k * 0.21) + 3 * np.sin(k * 0.53); dy = 5 * np.sin(k * 0.17 + 1) + 2 * np.sin(k * 0.61)
    x0 = int((W - pw) / 2 + dx); y0 = int((H - ph) / 2 - 80 + dy)
    sm = np.zeros((H, W), np.float32); sm[y0 + 18:y0 + ph + 30, x0 + 10:x0 + pw + 10] = 1
    sm = np.asarray(Image.fromarray((sm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(26))).astype(np.float32) / 255
    base *= (1 - 0.65 * sm)[..., None]
    base[y0:y0 + ph, x0:x0 + pw] = im
    return np.clip(base, 0, 255).astype(np.uint8)


foto = ImageOps.exif_transpose(Image.open(FOTO_CTA)).convert("RGB")
try:
    from PIL import ImageCms
    icc = foto.info.get("icc_profile")
    if icc:
        import io
        foto = ImageCms.profileToProfile(foto, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile("sRGB"))
except Exception:
    pass

T_BF = capa_texto(["BLACK FRIDAY"], "disp_xb", 120)
T_PCT = capa_texto(["−25%"], "disp_xb", 240)
T_LA = capa_texto(["La tuya viene con la remera."], "serif_i", 78)
T_PRE = capa_texto(["$48.750"], "disp_b", 120)
f46 = fuente("inter_m", 46)
T_ANT = capa_texto(["antes $65.000"], "inter_m", 46, color=(220, 220, 220))
x0 = (W - f46.getlength("antes $65.000")) / 2 + f46.getlength("antes "); x1 = (W + f46.getlength("antes $65.000")) / 2
ImageDraw.Draw(T_ANT).line([(x0 - 3, 10 + f46.getmetrics()[0] * 0.64), (x1 + 3, 10 + f46.getmetrics()[0] * 0.64)],
                           fill=(220, 220, 220, 255), width=4)
T_WEB = capa_texto(["Envío gratis · rocce.shop"], "inter_sb", 44)

cod = Codificador(salida + ".tmp.mp4")
lect = None; actual = None
for c in range(N):
    if c < 138:
        for a, b, clip, t0, cx in PLANOS:
            if a <= c < b:
                if actual != a:
                    if lect: lect.cerrar()
                    lect = Lector(os.path.join(MX, f"h_{clip}.mp4"), t0, W, H, crop=f"607:1080:{cx}:0"); actual = a
                img = lect.cuadro().copy()
        if c >= 132:  # barrido: giro de cabeza hacia la placa
            k = c - 131
            sh = int(90 * k * k / 2)
            img = np.roll(img, -sh, axis=1)
            img = np.asarray(Image.fromarray(img).filter(ImageFilter.BoxBlur(6 + 6 * k))).copy()
        img = grano(img, 4, c)
        pegar(img, B1, 0, 700, alfa=1.0 if c < 132 else 0)
    elif c < 225:
        k = c - 138
        if USAR_VIDEO:
            if k == 0:
                if lect: lect.cerrar()
                lect = Lector(PLACA_VIDEO, T0_PLACA, W, H); actual = None
            img = lect.cuadro().copy()
        else:
            img = cuadro_placa(k)
        if k < 5:  # llega del barrido
            img = np.roll(img, int(160 * (5 - k) ** 2 / 5), axis=1)
            img = np.asarray(Image.fromarray(img).filter(ImageFilter.BoxBlur(3 * (5 - k)))).copy()
        img = grano(img, 3, c)
        if c >= C_CAP2:
            pegar(img, B2, 0, Y_CAP2)
    else:
        k = c - 225
        im = fill_cover(foto, W, H, cx=0.5, cy=0.5, zoom=1.0 + 0.045 * k / 75)
        a = np.asarray(im).astype(np.float32)
        yy = np.arange(H)[:, None, None]
        osc = np.clip((860 - yy) / 700, 0, 1) * 0.55 + np.clip((yy - 1380) / 300, 0, 1) * 0.55
        img = (a * (1 - osc)).astype(np.uint8)
        pegar(img, T_BF, 0, 150, alfa=suave(k / 4))
        pegar(img, T_PCT, 0, 270, alfa=suave((k - 3) / 4))
        pegar(img, T_PRE, 0, 560, alfa=suave((k - 10) / 4))
        pegar(img, T_ANT, 0, 700, alfa=suave((k - 10) / 4))
        pegar(img, T_LA, 0, 1440, alfa=suave((k - 14) / 5))
        pegar(img, T_WEB, 0, 1540, alfa=suave((k - 18) / 4))
    cod.poner(img)
if lect: lect.cerrar()

# sonido: ambiente de cuarto, papel y lápiz, el «pop» del texto, barrido, brillo del metal y cierre
dur = N / FPS
x = lienzo(dur)
rng = np.random.default_rng(3)
amb = rng.normal(0, 1, len(x)); amb = np.convolve(amb, np.ones(40) / 40, "same") * 0.03
x += amb
for t in np.arange(0.4, 3.4, 0.23):  # lápiz/papel
    barrido(x, t + rng.uniform(-0.05, 0.05), 0.12, 0.035, 2500, 7000)
tic(x, 0.0, 0.22, 1200); tic(x, 0.03, 0.15, 1800)
barrido(x, 4.25, 0.4, 0.35, 400, 6000)
brillo(x, 4.6 + (K_FOCO / FPS if USAR_VIDEO else 0), 0.16)  # el brillo del metal cae cuando entra el foco
colchon(x, 4.6, 7.6, [146.8, 220.0, 277.2], 0.05, ataque=0.5, suelta=0.6)
tic(x, C_CAP2 / FPS, 0.22, 1200); tic(x, C_CAP2 / FPS + 0.03, 0.15, 1800)
golpe(x, 7.5, 0.6, f0=58, caida=0.4)
colchon(x, 7.5, dur, [110.0, 164.8, 220.0, 277.2], 0.07, ataque=0.15, suelta=0.4)
brillo(x, 7.5, 0.08)
wav = salida + ".wav"
nivel, _ = mezclar(x, [], dur, wav)
cod.cerrar(audio=wav)
os.replace(salida + ".tmp.mp4", salida); os.remove(wav)
json.dump(dict(cuadros=cod.n, duracion=dur, sonoridad=nivel), open(salida + ".control.json", "w"), indent=1)
print(cod.n, nivel)
