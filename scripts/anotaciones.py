# Anotaciones "de ficha técnica" que siguen un detalle real de la prenda en movimiento (seguimiento por plantilla).
# Por cada anotación: anillo en el detalle → línea → etiqueta (número celeste + palabra blanca) sobre placa oscura.
# Salida: una secuencia PNG RGBA (1080×1920), un cuadro por cuadro del clip, para superponer con FFmpeg.
# Uso (con Python que tenga OpenCV, p. ej. demucs-env):
#   python anotaciones.py CLIP.mp4 SALIDA_DIR SPEC.json
# SPEC.json: {"tracker": {"frame": 36, "x": 680, "y": 1065, "size": 130, "search": 70},
#             "notas": [{"num": "01", "texto": "DENIM", "desde": 8, "hasta": 59, "ancla": [0, 0], "etiqueta": [-260, -230]}, ...]}
#   ancla = desplazamiento del punto respecto del centro seguido; etiqueta = posición de la placa respecto del ancla.
import sys, os, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

clip, out, spec_path = sys.argv[1:4]
spec = json.load(open(spec_path)); os.makedirs(out, exist_ok=True)
W, H = 1080, 1920
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W)
n = len(frames)

# --- seguimiento: desde el cuadro de referencia hacia adelante y hacia atrás ---
t = spec["tracker"]; s = t["size"] // 2; srch = t.get("search", 70)
def track(order):
    x, y = t["x"], t["y"]; tmpl = frames[t["frame"]][y - s:y + s, x - s:x + s].astype(np.float32); pos = {}
    for i in order:
        g = frames[i].astype(np.float32)
        x0, y0 = max(0, x - s - srch), max(0, y - s - srch); x1, y1 = min(W, x + s + srch), min(H, y + s + srch)
        r = cv2.matchTemplate(g[y0:y1, x0:x1], tmpl, cv2.TM_CCOEFF_NORMED)
        _, sc, _, loc = cv2.minMaxLoc(r)
        nx, ny = loc[0] + x0 + s, loc[1] + y0 + s
        if sc > 0.4:
            x, y = nx, ny
            new = g[y - s:y + s, x - s:x + s]
            if new.shape == tmpl.shape: tmpl = 0.85 * tmpl + 0.15 * new   # tolera escala y desenfoque
        pos[i] = (x, y, sc)
    return pos
pos = {**track(range(t["frame"], n)), **track(range(t["frame"], -1, -1))}
xs = np.array([pos[i][0] for i in range(n)], float); ys = np.array([pos[i][1] for i in range(n)], float)
k = 5; ker = np.ones(k) / k
xs = np.convolve(np.pad(xs, k // 2, mode="edge"), ker, "valid"); ys = np.convolve(np.pad(ys, k // 2, mode="edge"), ker, "valid")
print("seguimiento: x %.0f→%.0f, y %.0f→%.0f, coincidencia mínima %.2f" % (xs[0], xs[-1], ys[0], ys[-1], min(p[2] for p in pos.values())))

# --- dibujo ---
SS = 2
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf"
ft = ImageFont.truetype(MONO, 42 * SS)
CEL, BLANCO = (169, 200, 232), (255, 255, 255)
ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3

def nota(draw, shadow, ax, ay, lx, ly, num, texto, f):
    a_ring, a_line, a_tag = ease(f / 4), ease((f - 2) / 6), ease((f - 6) / 5)
    t1 = num + "  "; w1, w2 = ft.getlength(t1), ft.getlength(texto)
    pad, hgt = 16 * SS, 62 * SS; tw = w1 + w2 + 2 * pad
    x0 = lx * SS - tw / 2                                         # placa centrada en el punto de etiqueta
    x0 = min(max(x0, 28 * SS), (W - 28) * SS - tw)                # sin salirse del cuadro
    y0 = ly * SS - hgt / 2
    # la línea termina en el borde de la placa más cercano al anillo
    tx = min(max(ax * SS, x0 + 12 * SS), x0 + tw - 12 * SS); ty = y0 + hgt if ay * SS > y0 + hgt else y0
    if a_ring > 0:
        r = 16 * a_ring * SS
        shadow.ellipse([ax * SS - r, ay * SS - r, ax * SS + r, ay * SS + r], outline=(0, 0, 0, 130), width=9 * SS)
        draw.ellipse([ax * SS - r, ay * SS - r, ax * SS + r, ay * SS + r], outline=BLANCO + (255,), width=4 * SS)
        d = 5 * SS * a_ring; draw.ellipse([ax * SS - d, ay * SS - d, ax * SS + d, ay * SS + d], fill=BLANCO + (255,))
    if a_line > 0:
        L = max(1.0, np.hypot(tx - ax * SS, ty - ay * SS)); ux, uy = (tx - ax * SS) / L, (ty - ay * SS) / L
        sx, sy = ax * SS + ux * 20 * SS, ay * SS + uy * 20 * SS
        ex, ey = sx + (tx - sx) * a_line, sy + (ty - sy) * a_line
        shadow.line([sx, sy, ex, ey], fill=(0, 0, 0, 130), width=9 * SS)
        draw.line([sx, sy, ex, ey], fill=BLANCO + (255,), width=4 * SS)
    if a_tag > 0:
        k = max(1, int(round(len(texto) * ease((f - 6) / 7))))
        draw.rounded_rectangle([x0, y0, x0 + tw, y0 + hgt], radius=10 * SS, fill=(10, 18, 28, int(165 * a_tag)))
        hb = ft.getbbox("H"); tyy = y0 + (hgt - (hb[3] - hb[1])) / 2 - hb[1]
        draw.text((x0 + pad, tyy), t1, font=ft, fill=CEL + (int(255 * a_tag),))
        draw.text((x0 + pad + w1, tyy), texto[:k], font=ft, fill=BLANCO + (int(255 * a_tag),))

for i in range(n):
    sh = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    ds, di = ImageDraw.Draw(sh), ImageDraw.Draw(im)
    for nt in spec["notas"]:
        if nt["desde"] <= i <= nt["hasta"]:
            f = i - nt["desde"]; ax, ay = xs[i] + nt["ancla"][0], ys[i] + nt["ancla"][1]
            lx, ly = ax + nt["etiqueta"][0], ay + nt["etiqueta"][1]
            nota(di, ds, ax, ay, lx, ly, nt["num"], nt["texto"], f)
            fin = nt["hasta"] - i
            if fin < 5:   # salida: se apaga en 5 cuadros
                for layer in (im, sh):
                    a = np.asarray(layer).copy(); a[..., 3] = (a[..., 3] * (fin / 5)).astype(np.uint8); layer.paste(Image.fromarray(a), (0, 0))
    sh = sh.filter(ImageFilter.GaussianBlur(3 * SS))
    frame = Image.alpha_composite(sh, im).resize((W, H), Image.LANCZOS)
    frame.save(os.path.join(out, "%04d.png" % i))
print("listo:", n, "cuadros en", out)
