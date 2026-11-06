# CTA final sobre la toma real IMG_7857 (espalda con "ROCCÉ Founders Privée", frente al mar), 3,4 s a 30 fps:
# acercamiento leve, degradé oscuro abajo y tres renglones que entran a golpes:
# "DEJÁ DE PROCRASTINAR," · "HACETE FOUNDER" · rocce.shop. Texto abajo del estampado (no lo tapa) y por encima
# de la interfaz de Reels. Uso: python cta.py SALIDA_DIR
import sys, os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
W, H, FPS, T0, DUR = 1080, 1920, 30, 3.55, 3.4
n = round(DUR * FPS)
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(T0), "-i", "ORIGINALES/IMG_7857.mov", "-frames:v", str(n),
                      "-vf", "scale=1080:1920:flags=lanczos,format=rgb24", "-f", "rawvideo", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3); assert len(fr) == n, len(fr)
F = "/usr/share/fonts/opentype/inter/"
f1, f2, f3 = ImageFont.truetype(F + "InterDisplay-Bold.otf", 58), ImageFont.truetype(F + "InterDisplay-ExtraBold.otf", 104), ImageFont.truetype(F + "InterDisplay-Bold.otf", 50)
HUMO, AZUL = (0xCD, 0xDD, 0xE5), (0x23, 0x3A, 0x55)
grad = np.zeros((H, 1), np.float32); y = np.arange(H)
grad[:, 0] = np.clip((y - 1050) / 600, 0, 1) ** 1.3 * 0.78        # degradé oscuro abajo para leer
def suave(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def golpe(u):  # entra grande y asienta
    u = min(1, max(0, u)); return 1 + 0.35 * (1 - u) ** 3
def capa_texto(t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def renglon(txt, font, cy, t0, color, escala_ent=0.3, sombra=True):
        if t < t0: return
        u = (t - t0) / 0.20; s = golpe(u) if escala_ent else 1; a = suave(u * 1.5)
        tw = d.textlength(txt, font=font); bb = font.getbbox(txt); th = bb[3] - bb[1]
        cap = Image.new("RGBA", (int(tw) + 40, th + 60), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap)
        cd.text((20, 30 - bb[1]), txt, font=font, fill=color + (255,))
        if sombra:
            sh = cap.copy(); sh = Image.composite(Image.new("RGBA", sh.size, (0, 0, 0, 170)), Image.new("RGBA", sh.size, (0, 0, 0, 0)), sh.split()[3]).filter(ImageFilter.GaussianBlur(10))
            cap = Image.alpha_composite(sh, cap)
        cap = cap.resize((max(1, int(cap.width * s)), max(1, int(cap.height * s))), Image.LANCZOS)
        cap.putalpha(cap.split()[3].point(lambda v: int(v * a)))
        im.alpha_composite(cap, (int(W / 2 - cap.width / 2), int(cy - cap.height / 2)))
    renglon("DEJÁ DE PROCRASTINAR,", f1, 1300, 0.10, (255, 255, 255))
    renglon("HACETE FOUNDER", f2, 1408, 0.45, (255, 255, 255))
    if t >= 0.85:                       # rocce.shop en píldora celeste humo
        u = suave((t - 0.85) / 0.25); txt = "rocce.shop"; tw = d.textlength(txt, font=f3)
        x0, y0 = W / 2 - tw / 2 - 40, 1490 + (1 - u) * 40
        d.rounded_rectangle((x0, y0, x0 + tw + 80, y0 + 84), radius=42, fill=HUMO + (int(255 * u),))
        bb = f3.getbbox(txt); d.text((W / 2 - tw / 2, y0 + 42 - (bb[1] + bb[3]) / 2), txt, font=f3, fill=AZUL + (int(255 * u),))
    return im
for i in range(n):
    t = i / FPS; z = 1 + 0.05 * suave(t / DUR)                  # acercamiento leve
    im = Image.fromarray(fr[i]).resize((round(W * z), round(H * z)), Image.LANCZOS)
    cx, cy = (im.width - W) // 2, int((im.height - H) * 0.35); im = im.crop((cx, cy, cx + W, cy + H))
    a = np.asarray(im).astype(np.float32) * (1 - grad[:, :, None] if False else 1 - grad[..., None])
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    im.alpha_composite(capa_texto(t)); im.convert("RGB").save(f"{out}/{i + 1:04d}.png")
print("cta", n, "cuadros")
