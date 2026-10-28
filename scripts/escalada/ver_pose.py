# Hoja de control de la pose: cabeza, cuello→cadera y brazos sobre los cuadros (cada N).
# Uso: python ver_pose.py SEQ_DIR pose.json SALIDA.jpg [paso] [recorte_px]
import sys, json
import numpy as np
from PIL import Image, ImageDraw
seq, pj, out = sys.argv[1:4]; paso = int(sys.argv[4]) if len(sys.argv) > 4 else 4; R = int(sys.argv[5]) if len(sys.argv) > 5 else 220
pose = json.load(open(pj)); fs = sorted(map(int, pose))[::paso]
T = 260; cols = 8; hoja = Image.new("RGB", (cols * T, ((len(fs) + cols - 1) // cols) * (T + 14)), (30, 0, 0)); d0 = ImageDraw.Draw(hoja)
for i, f in enumerate(fs):
    p = pose[str(f)]; im = Image.open(f"{seq}/{f + 1:04d}.png").convert("RGB"); d = ImageDraw.Draw(im)
    if p:
        H, N, P, r = p["H"], p["N"], p["P"], p["r"]
        d.ellipse([H[0] - r, H[1] - r, H[0] + r, H[1] + r], outline=(0, 255, 0), width=2)
        d.line([tuple(N), tuple(P)], fill=(255, 0, 255), width=3)
        for k, col in (("cerca", (0, 200, 255)), ("lejos", (255, 200, 0))):
            b = p["brazos"].get(k)
            if b: d.line([(b[3], b[4]), (b[3] + b[0] * 2.5 * r, b[4] + b[1] * 2.5 * r)], fill=col, width=3)
        c = H
    else: c = (540, 960)
    crop = im.crop((int(c[0] - R), int(c[1] - R * 0.6), int(c[0] + R), int(c[1] + R * 1.4))).resize((T, T))
    x, y = (i % cols) * T, (i // cols) * (T + 14); hoja.paste(crop, (x, y)); d0.text((x + 3, y + T), f"f{f + 1}", fill="yellow")
hoja.save(out, quality=85)
