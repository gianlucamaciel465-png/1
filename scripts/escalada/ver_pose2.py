# Hoja de control de pose_escalador.py: cabeza, torso (cuello→cadera) y dirección de brazos.
import sys, json, math
from PIL import Image, ImageDraw
seq, pj, out = sys.argv[1:4]; paso = int(sys.argv[4]); R = int(sys.argv[5])
pose = json.load(open(pj)); fs = sorted(map(int, pose))[::paso]
T = 250; cols = 9; hoja = Image.new("RGB", (cols * T, ((len(fs) + cols - 1) // cols) * (T + 14)), (30, 0, 0)); d0 = ImageDraw.Draw(hoja)
for i, f in enumerate(fs):
    p = pose[str(f)]; im = Image.open(f"{seq}/{f:04d}.png").convert("RGB"); d = ImageDraw.Draw(im)
    H, N, P, r, S = p["H"], p["N"], p["P"], p["r"], p["S"]
    d.ellipse([H[0] - r, H[1] - r, H[0] + r, H[1] + r], outline=(0, 255, 0), width=2)
    d.line([tuple(N), tuple(P)], fill=(255, 0, 255), width=4)
    for k, col in (("cerca", (0, 200, 255)), ("lejos", (255, 200, 0))):
        a = p[k]; d.line([tuple(S), (S[0] + math.cos(a) * 1.8 * r, S[1] + math.sin(a) * 1.8 * r)], fill=col, width=4)
    crop = im.crop((int(H[0] - R), int(H[1] - R * 0.5), int(H[0] + R), int(H[1] + R * 1.5))).resize((T, T))
    x, y = (i % cols) * T, (i // cols) * (T + 14); hoja.paste(crop, (x, y)); d0.text((x + 3, y + T), f"f{f}", fill="yellow")
hoja.save(out, quality=85)
