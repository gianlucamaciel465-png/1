# Corrige la pose del protagonista en el salto final de R1 (cuadros 60 fps 320–350: se agacha, salta y levanta
# los brazos). Ahí el cuerpo está erguido y el brazo tapa la cabeza en 336–338, así que la búsqueda general se confunde.
# Método para este tramo: cabeza (dada a mano donde el brazo la tapa) → se sigue el palo del torso fila por fila hacia
# abajo (centro del tramo blanco más cercano al de la fila anterior) → dirección media → pelvis a 4,4 radios.
# Uso: python pose_salto.py SEQ60_DIR pose60.json SALIDA.json
import sys, json
import numpy as np, cv2
from PIL import Image

seq, src, dst = sys.argv[1:4]
pose = json.load(open(src))
CABEZA_MANUAL = {336: (472, 668, 21.5), 337: (485, 664, 21.0), 338: (497, 661, 20.5), 339: (500, 683, 20.0)}   # medidas sobre la grilla (cuadros con el brazo encima)

for f in range(320, 352, 1):
    a = np.asarray(Image.open(f"{seq}/{f + 1:04d}.png").convert("RGB")).astype(int)
    L = a.mean(2); red = (a[..., 0] - np.maximum(a[..., 1], a[..., 2])) > 50
    white = (L > 200) & ~red
    if f in CABEZA_MANUAL:
        hx, hy, r = CABEZA_MANUAL[f]
    else:
        p = pose.get(str(f))
        if not p: continue
        hx, hy = p["H"]; r = p["r"]
    # seguir el torso hacia abajo
    y = int(hy + r + 6); x = hx; pts = []; primero = True
    while y < hy + r + 6 + 3.6 * r:
        row = white[y, int(x - 34):int(x + 35)]
        if row.any():
            idx = np.where(row)[0] + int(x - 34)
            # tramos contiguos; el más cercano a x (el primero puede estar corrido respecto del centro de la cabeza)
            runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
            c = [0.5 * (rr[0] + rr[-1]) for rr in runs if 5 <= len(rr) <= 46]
            if c:
                cbest = min(c, key=lambda v: abs(v - x))
                if abs(cbest - x) < (30 if primero else 9): x = cbest; pts.append((x, y)); primero = False
        y += 2
    if len(pts) < 8:
        print(f, "sin torso: se interpola"); pose[str(f)] = None; continue
    pts = np.array(pts, float)
    # dirección: ajuste lineal x(y)
    k, b = np.polyfit(pts[:, 1], pts[:, 0], 1)
    u = np.array([k, 1.0]); u /= np.linalg.norm(u)
    y0 = hy + r * 0.95
    N = np.array([k * y0 + b, y0])
    P = N + u * 4.4 * r
    p = pose.get(str(f)) or {"brazos": {"cerca": None, "lejos": None}}
    p.update({"H": [float(hx), float(hy)], "r": float(r), "N": N.tolist(), "P": P.tolist(), "L": 4.4 * r,
              "S": (N + u * 0.12 * 4.4 * r).tolist(), "manual": True})
    pose[str(f)] = p
    print(f, "H=(%.0f,%.0f) N=(%.0f,%.0f) P=(%.0f,%.0f)" % (hx, hy, N[0], N[1], P[0], P[1]))
json.dump(pose, open(dst, "w"), indent=0)
