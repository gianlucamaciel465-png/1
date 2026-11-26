# M3 «Lo mejor de esta remera no es la remera.» · publicación seria con fotos reales que se mueven apenas.
# Sale en dos formatos con el mismo guion:
#   reel 9:16 (fotos con empuje lento y flash de obturador entre fotos, sonido real del mar de IMG_7896)
#   carrusel 4:5: una lámina por foto, en MP4 (foto que se mueve, sin sonido) y en PNG fija.
# La pregunta abre en la lámina 1 («lo mejor…») y se resuelve en la 5 (la placa); la 6 es el Black Friday.
# Uso: python3 scripts/fomo/m3.py CARPETA_SALIDA
import sys, os, json, io, zipfile
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageCms
sys.path.insert(0, os.path.dirname(__file__))
from comun import *

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
P = lambda r: os.path.join(RAIZ, r)
SLIDES = [
    dict(foto="PRODUCTO/blanca_puesta_espalda_balcon_playa.jpg", cx=0.5, cy=0.55, l1="Lo mejor de esta remera", l2="no es la remera.", lugar="arriba"),
    dict(foto="PRODUCTO/blanca_frente_detalle_estampado.jpg", cx=0.5, cy=0.42, l1="Adelante:", l2="estuviste cerca.", lugar="abajo", oscuro=True, contener=0.5),
    dict(foto="PRODUCTO/blanca_espalda_rocas_espuma.jpg", cx=0.5, cy=0.55, l1="Atrás:", l2="llegaste primero.", lugar="arriba"),
    dict(foto="TRABAJO/fomo/shop/rc-negra-rambla.webp", cx=0.5, cy=0.55, l1="Corte V.", l2="Ensancha hombros, reduce cintura.", lugar="arriba", chico=True, contener=1.0, lugar45="abajo"),
    dict(placa=True, l1="Y lo mejor: la placa.", l2="Seguir hasta lograrlo."),
    dict(cta=True, foto="PRODUCTO/blanca_negra_espalda_playa_2.jpg", cx=0.5, cy=0.52, contener=1.0, y_cont=640),
]


def abrir(r):
    im = Image.open(P(r)); im = ImageOps.exif_transpose(im)
    icc = im.info.get("icc_profile")
    im = im.convert("RGB")
    if icc:  # fotos de iPhone en Display P3 → sRGB
        try:
            im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile("sRGB"))
        except Exception:
            pass
    return im


FOTOS = {k: abrir(s["foto"]) for k, s in enumerate(SLIDES) if "foto" in s}
PLACA = Image.open(P("TRABAJO/fomo/rcs-placa.jpg")).convert("RGB")
LOGO = Image.open(P("LOGO/rocce_logo.png")).convert("RGB")


def chip_logo(lado=150, radio=0.12):
    lg = LOGO.resize((lado, lado), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (lado, lado), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, lado - 1, lado - 1], int(lado * radio), fill=255)
    lg.putalpha(m); return lg


def textos_slide(s, h):
    """Capas de texto de una lámina para un alto dado (1920 reel, 1350 carrusel)."""
    k = 1.0 if h == 1920 else 0.9
    color = (17, 17, 17) if s.get("oscuro") else (255, 255, 255)
    sombra = 0 if s.get("oscuro") else 0.5
    capas = []
    if s.get("cta"):
        capas.append(("BF", capa_texto(["BLACK FRIDAY"], "disp_xb", int(118 * k))))
        capas.append(("PCT", capa_texto(["−25%"], "disp_xb", int(230 * k), color=CELESTE)))
        capas.append(("PRE", capa_texto(["$48.750"], "disp_b", int(112 * k))))
        f = fuente("inter_m", int(44 * k)); t = "antes $65.000"
        a = capa_texto([t], "inter_m", int(44 * k), color=(222, 222, 222))
        x0 = (W - f.getlength(t)) / 2 + f.getlength("antes "); x1 = (W + f.getlength(t)) / 2; y = 10 + f.getmetrics()[0] * 0.64
        ImageDraw.Draw(a).line([(x0 - 3, y), (x1 + 3, y)], fill=(222, 222, 222, 255), width=4)
        capas.append(("ANT", a))
        capas.append(("INC", capa_texto(["Remera + placa · Envío gratis"], "inter_sb", int(40 * k))))
        capas.append(("WEB", capa_texto(["rocce.shop"], "inter_b", int(48 * k), color=CELESTE)))
        return capas
    if s.get("placa"):
        capas.append(("L1", capa_texto([s["l1"]], "serif", int(92 * k))))
        capas.append(("L2", capa_texto([s["l2"]], "serif_i", int(104 * k), color=CELESTE)))
        capas.append(("SUB", capa_texto(["VIENE CON CADA REMERA FOUNDERS PRIVÉE"], "inter_sb", int(28 * k), track=4)))
        return capas
    t1 = int((88 if not s.get("chico") else 88) * k); t2 = int((88 if not s.get("chico") else 64) * k)
    capas.append(("L1", capa_texto([s["l1"]], "serif", t1, color=color, sombra=sombra)))
    capas.append(("L2", capa_texto([s["l2"]], "serif_i", t2, color=color, sombra=sombra)))
    return capas


MARCA = {h: capa_texto(["ROCCÉ"], "inter_sb", 26 if h == 1920 else 24, track=9, sombra=0.4) for h in (1920, 1350)}
MARCA_OSC = {h: capa_texto(["ROCCÉ"], "inter_sb", 26 if h == 1920 else 24, track=9, sombra=0, color=(17, 17, 17)) for h in (1920, 1350)}
CAPAS = {(i, h): textos_slide(s, h) for i, s in enumerate(SLIDES) for h in (1920, 1350)}
CHIP = chip_logo(96)


def linea_bf(size=88):
    a = capa_texto(["BLACK FRIDAY"], "disp_xb", size); b = capa_texto(["−25%"], "disp_xb", size, color=CELESTE)
    ba, bb = a.getbbox(), b.getbbox()
    a = a.crop((ba[0], 0, ba[2], a.height)); b = b.crop((bb[0], 0, bb[2], b.height))
    gap = int(size * 0.35); ancho = a.width + gap + b.width
    o = Image.new("RGBA", (W, max(a.height, b.height)), (0, 0, 0, 0))
    x0 = (W - ancho) // 2; o.alpha_composite(a, (x0, 0)); o.alpha_composite(b, (x0 + a.width + gap, 0))
    return o


LINEA_BF = linea_bf()


def lamina(i, p, h, t_txt):
    """Cuadro de la lámina i con progreso p∈[0,1] (empuje lento) y tiempo de texto t_txt (s desde que aparece)."""
    s = SLIDES[i]
    a_txt = suave(t_txt / 0.35)
    if s.get("placa"):
        fondo = np.asarray(fill_cover(PLACA, W, h).filter(ImageFilter.GaussianBlur(45))).astype(np.float32) * 0.24
        esc = 0.86 + 0.06 * suave(p); pw = int(W * esc); ph = int(pw * PLACA.height / PLACA.width)
        im = np.asarray(PLACA.resize((pw, ph), Image.LANCZOS)).astype(np.float32)
        xx, yy = np.meshgrid(np.arange(pw), np.arange(ph))
        d = (xx / pw + yy / ph * 0.35) - (-0.3 + 1.6 * suave(min(1, p * 1.3)))
        im = 255 - (255 - im) * (1 - 0.3 * np.exp(-(d / 0.08) ** 2)[..., None])
        x0 = (W - pw) // 2; y0 = int(h * 0.47) - ph // 2
        fondo[y0:y0 + ph, x0:x0 + pw] = im
        img = np.clip(fondo, 0, 255).astype(np.uint8)
        c = dict(CAPAS[(i, h)])
        pegar(img, c["L1"], 0, y0 - c["L1"].height - (40 if h == 1920 else 20), a_txt)
        pegar(img, c["L2"], 0, y0 + ph + (40 if h == 1920 else 24), suave((t_txt - 0.5) / 0.35))
        pegar(img, c["SUB"], 0, y0 + ph + (190 if h == 1920 else 150), suave((t_txt - 0.9) / 0.35))
    else:
        foto = FOTOS[i]
        if h == 1920 and "contener" in s:
            fondo = fill_cover(foto, W, h).filter(ImageFilter.GaussianBlur(38))
            base = np.asarray(fondo).astype(np.float32) * (1.0 if s.get("oscuro") else 0.55)
            z = 1.0 + 0.04 * suave(p)
            pw = int(W * z); ph = int(pw * foto.height / foto.width)
            fi = np.asarray(foto.resize((pw, ph), Image.LANCZOS)).astype(np.float32)
            y0 = s.get("y_cont", int((h - ph) * s["contener"])) - (ph - int(W * foto.height / foto.width)) // 2
            x0 = (W - pw) // 2
            # borde superior e inferior fundidos con el fondo
            al = np.ones((ph, 1, 1), np.float32); f_ = 60
            al[:f_, 0, 0] = np.linspace(0, 1, f_); al[-f_:, 0, 0] = np.linspace(1, 0, f_)
            ya, yb = max(0, y0), min(h, y0 + ph)
            seg = fi[ya - y0:yb - y0, max(0, -x0):max(0, -x0) + W]
            a_ = al[ya - y0:yb - y0]
            base[ya:yb] = base[ya:yb] * (1 - a_) + seg * a_
            img = base
        else:
            img = np.asarray(fill_cover(foto, W, h, cx=s["cx"], cy=s["cy"], zoom=1.0 + 0.06 * suave(p))).astype(np.float32)
        yy = np.arange(h)[:, None, None] / h
        if s.get("cta"):
            osc = (np.clip((0.44 - yy) / 0.40, 0, 1) * 0.78 + np.clip((yy - 0.66) / 0.22, 0, 1) * 0.80) if h == 1350 else \
                  (np.clip((0.40 - yy) / 0.30, 0, 1) * 0.70 + np.clip((yy - 0.84) / 0.10, 0, 1) * 0.70)
        elif s.get("oscuro"):
            osc = 0 * yy
        elif (s.get("lugar45", s["lugar"]) if h == 1350 else s["lugar"]) == "arriba":
            osc = np.clip((0.40 - yy) / 0.38, 0, 1) * 0.62
        else:
            osc = np.clip((yy - 0.62) / 0.30, 0, 1) * 0.62
        img = (img * (1 - osc)).astype(np.uint8)
        c = dict(CAPAS[(i, h)])
        if s.get("cta"):
            top = 150 if h == 1920 else 70
            if h == 1920:
                pegar(img, c["BF"], 0, top, a_txt)
                pegar(img, c["PCT"], 0, top + c["BF"].height - 20, suave((t_txt - 0.12) / 0.3))  # precio arriba (sobre el fondo ampliado); envío y web abajo, sobre la arena
                yp = top + c["BF"].height + c["PCT"].height - 50
                pegar(img, c["PRE"], 0, yp, suave((t_txt - 0.35) / 0.3))
                pegar(img, c["ANT"], 0, yp + c["PRE"].height - 22, suave((t_txt - 0.35) / 0.3))
                pegar(img, c["INC"], 0, 1650, suave((t_txt - 0.55) / 0.3))
                pegar(img, c["WEB"], 0, 1712, suave((t_txt - 0.55) / 0.3))
                return img
            yb = int(h * 0.69)
            pegar(img, LINEA_BF, 0, 48, a_txt)
            pegar(img, c["PRE"], 0, yb, suave((t_txt - 0.35) / 0.3))
            pegar(img, c["ANT"], 0, yb + c["PRE"].height - 22, suave((t_txt - 0.35) / 0.3))
            pegar(img, c["INC"], 0, yb + c["PRE"].height + c["ANT"].height - 30, suave((t_txt - 0.55) / 0.3))
            pegar(img, c["WEB"], 0, yb + c["PRE"].height + c["ANT"].height + c["INC"].height - 40, suave((t_txt - 0.55) / 0.3))
        else:
            lugar = s.get("lugar45", s["lugar"]) if h == 1350 else s["lugar"]
            if lugar == "arriba":
                y1 = int(h * (0.105 if h == 1920 else 0.085))
            else:
                y1 = int(h * (0.76 if h == 1920 else 0.80))
            pegar(img, c["L1"], 0, y1, a_txt)
            pegar(img, c["L2"], 0, y1 + int(c["L1"].height * 0.78), suave((t_txt - 0.25) / 0.35))
    marca = MARCA_OSC[h] if s.get("oscuro") else MARCA[h]
    if not s.get("cta"):
        pegar(img, marca, 0, (h - marca.height - (330 if h == 1920 else 50)) if (s.get("lugar45", s.get("lugar")) if h == 1350 else s.get("lugar")) == "arriba" or s.get("placa") else (95 if h == 1920 else 40), 0.9)
    else:
        pegar(img, CHIP, W - CHIP.width - 36, h - CHIP.height - 36, suave((t_txt - 0.7) / 0.3))
    return img


if os.environ.get("SOLO_FOTOS"):
    for h in (1920, 1350):
        ims = [Image.fromarray(lamina(i, 0.5, h, 9.0)).resize((270, int(270 * h / W))) for i in range(6)]
        o = Image.new("RGB", (270 * 6, ims[0].height))
        for i, im in enumerate(ims): o.paste(im, (270 * i, 0))
        o.save(os.path.join(out, f"prueba_{h}.jpg"), quality=85)
    sys.exit(0)

# ---------- reel 9:16 ----------
CORTES = [0, 66, 120, 174, 228, 318, 414]
N = CORTES[-1]
cod = Codificador(os.path.join(out, "M3_reel.tmp.mp4"))
for c in range(N):
    i = max(k for k in range(6) if CORTES[k] <= c)
    a, b = CORTES[i], CORTES[i + 1]
    img = lamina(i, (c - a) / (b - a), 1920, (c - a - 5) / FPS)
    if c - a < 3:  # flash de obturador
        fl = [0.85, 0.45, 0.15][c - a]
        img = (img.astype(np.float32) * (1 - fl) + 255 * fl).astype(np.uint8)
    cod.poner(grano(img, 3, c))
dur = N / FPS
x = lienzo(dur)
mar = leer_wav(P("ORIGINALES/IMG_7896.mov"))
mar = mar / (np.abs(mar).max() + 1e-9) * 0.35
L = len(mar); xf = int(0.5 * SR); pos = 0
while pos < len(x):  # bucle del mar real con fundido cruzado
    seg = mar.copy(); seg[:xf] *= np.linspace(0, 1, xf); seg[-xf:] *= np.linspace(1, 0, xf)
    m = min(L, len(x) - pos); x[pos:pos + m] += seg[:m]; pos += L - xf
for k in CORTES[:-1]:
    t = k / FPS
    tic(x, t, 0.30, 3200); barrido(x, t, 0.06, 0.25, 2000, 9000); tic(x, t + 0.045, 0.18, 1400)
colchon(x, 0.0, dur, [110.0, 164.8, 220.0], 0.035, ataque=1.2, suelta=0.6)
colchon(x, 228 / FPS, dur, [146.8, 220.0, 277.2, 370.0], 0.05, ataque=0.5, suelta=0.6)
brillo(x, 228 / FPS, 0.12)
golpe(x, 318 / FPS, 0.45, f0=60, caida=0.35)
wav = os.path.join(out, "M3_reel.wav")
nivel, _ = mezclar(x, [], dur, wav)
cod.cerrar(audio=wav)
os.replace(os.path.join(out, "M3_reel.tmp.mp4"), os.path.join(out, "M3_reel.mp4")); os.remove(wav)

# ---------- carrusel 4:5 ----------
NC = 150  # 5 s por lámina
archivos = []
for i in range(6):
    nom = f"ROCCE_FOMO_CARRUSEL_{i + 1:02d}"
    cod = Codificador(os.path.join(out, nom + ".mp4"), h=1350)
    fin = None
    for c in range(NC):
        img = lamina(i, c / (NC - 1), 1350, (c - 6) / FPS)
        cod.poner(grano(img, 3, c)); fin = img
    cod.cerrar()
    Image.fromarray(lamina(i, 0.5, 1350, 9.0)).save(os.path.join(out, nom + ".png"), icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    archivos += [nom + ".mp4", nom + ".png"]
with zipfile.ZipFile(os.path.join(out, "ROCCE_FOMO_CARRUSEL.zip"), "w", zipfile.ZIP_STORED) as z:
    for a in archivos:
        z.write(os.path.join(out, a), a)
json.dump(dict(reel=dict(cuadros=N, duracion=dur, sonoridad=nivel), carrusel=archivos), open(os.path.join(out, "M3.control.json"), "w"), indent=1)
print(N, nivel)
