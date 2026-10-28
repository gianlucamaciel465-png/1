# Detecta los rótulos de la pared (letras gris claro finas) en el cuadro de referencia de cada plano.
# Agrupa las componentes claras en renglones y dibuja las cajas para revisarlas.
# Uso: python detectar_rotulos.py SEQ_DIR SALIDA_DIR f1 f2 ...
import sys, os, json
import numpy as np, cv2
from PIL import Image, ImageDraw
seq, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
res = {}
for f in map(int, sys.argv[3:]):
    a = np.asarray(Image.open(f"{seq}/{f:04d}.png").convert("RGB")).astype(np.int16)
    g = a.mean(2); sat = a.max(2) - a.min(2)
    m = ((g > 120) & (sat < 40)).astype(np.uint8)
    # descarta lo grueso (cuerpo de las figuras): distancia al borde > 4 px
    dt = cv2.distanceTransform(m, cv2.DIST_L2, 3)
    gruesa = cv2.dilate((dt > 4.5).astype(np.uint8), np.ones((25, 25), np.uint8))
    m = m & (1 - gruesa)
    lineas = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((1, 61), np.uint8))   # borde superior de la torre
    m = m & (1 - cv2.dilate(lineas, np.ones((3, 3), np.uint8)))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    comps = [(x, y, w, h) for (x, y, w, h, A) in st[1:] if 8 <= h <= 60 and w <= 60 and A >= 15]
    # agrupar por renglón (misma altura y cercanía horizontal)
    comps.sort(key=lambda c: (c[1], c[0])); lines = []
    for c in comps:
        for L in lines:
            if abs((L[1] + L[3] / 2) - (c[1] + c[3] / 2)) < 0.5 * max(L[3], c[3]) and c[0] - (L[0] + L[2]) < 2.5 * c[3] and c[0] + c[2] > L[0] - 2.5 * c[3]:
                x0, y0 = min(L[0], c[0]), min(L[1], c[1]); x1, y1 = max(L[0] + L[2], c[0] + c[2]), max(L[1] + L[3], c[1] + c[3])
                L[:] = [x0, y0, x1 - x0, y1 - y0, L[4] + 1]; break
        else: lines.append([*c, 1])
    lines = [L for L in lines if L[4] >= 3]
    lines = [[int(v) for v in L] for L in lines]; res[f] = lines
    im = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(im)
    for x, y, w, h, k in lines: d.rectangle([x - 2, y - 2, x + w + 2, y + h + 2], outline=(0, 255, 0)); d.text((x, y + h + 3), f"{x},{y},{w},{h}", fill=(255, 255, 0))
    im.save(f"{out}/rot_{f:04d}.png")
json.dump(res, open(f"{out}/rotulos_detectados.json", "w"), indent=1)
for f, L in res.items(): print(f, L)
