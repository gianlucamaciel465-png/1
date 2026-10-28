# Suaviza en 2D las marcas de impacto del render (estrellas blancas de rayos finos, demasiado gráficas) para que se
# vean como hielo molido: manchas blancas difusas. Solo toca componentes claras con forma de estrella (poco
# "sólidas": área / casco convexo baja) y de tamaño chico; las esquirlas (redondeadas) y los bordes de los pedazos
# (largos y finos) quedan como están.
# Si se pasa MARCAS.json (marcas_2d.py: posición y radio de cada marca en pantalla por cuadro), además se suaviza un
# disco en cada marca, aunque esté pegada a un borde (ahí el detector de forma no la encuentra).
# Uso: python suavizar_marcas.py ENTRADA_DIR SALIDA_DIR [MARCAS.json]
import sys, os
import numpy as np, cv2
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
import json
marcas = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
f0, f1 = 0, 10 ** 6
os.makedirs(dst, exist_ok=True)
tocados = 0
for nombre in sorted(os.listdir(src)):
    if not nombre.endswith(".png"): continue
    f = int(nombre[:4])
    if not (f0 <= f <= f1): continue
    a = np.asarray(Image.open(os.path.join(src, nombre)).convert("RGB")).astype(np.float32)
    L = a.mean(2)
    m = (L > 186).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    sel = np.zeros(L.shape, np.uint8)
    for i in range(1, n):
        x, y, w, h, A = st[i]
        if A < 12 or A > 1500 or max(w, h) > 70: continue
        if max(w, h) / max(1, min(w, h)) > 1.9: continue
        comp = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
        cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        hull = cv2.convexHull(np.concatenate(cnts))
        sol = A / max(1.0, cv2.contourArea(hull))
        if sol < 0.70:                                     # estrella: rayos finos con huecos entre ellos
            sel[y:y + h, x:x + w] |= comp
    for (px, py, rad) in marcas.get(str(f), []):
        cv2.circle(sel, (int(round(px)), int(round(py))), int(round(rad * 0.85)), 1, -1)
    if sel.any():
        tocados += 1
        reg = cv2.dilate(sel, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))).astype(np.float32)
        reg = np.clip(cv2.GaussianBlur(reg, (0, 0), 3.5) * 1.3, 0, 1)
        difuso = cv2.GaussianBlur(a, (0, 0), 5.5)
        # mancha de escarcha: lo difuso, apenas más apagado que el brillo del rayo
        mancha = difuso * 0.97 + 6
        a = a * (1 - reg[..., None]) + mancha * reg[..., None]
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(dst, nombre), compress_level=1)
print("cuadros con marcas suavizadas:", tocados)
