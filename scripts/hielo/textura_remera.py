# Recorta la remera negra de las fotos de producto (fondo de arena) y deja PNG RGBA para usar como textura.
# Máscara: oscuro (L < 105) → componente conexa más grande → huecos rellenos (el estampado gris queda adentro)
# → erosión de 4 px (saca el filete claro del recorte original) → borde suavizado.
# Las fotos vienen en sRGB (sin perfil P3). Uso: python textura_remera.py FOTO.png SALIDA.png
import sys
import numpy as np, cv2
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB"); a = np.asarray(im)
L = a.astype(np.float32).mean(2)
m = (L < 105).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); m = (lab == k).astype(np.uint8)
# rellenar huecos
inv = 1 - m; n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
borde = set(np.unique(np.concatenate([lab2[0], lab2[-1], lab2[:, 0], lab2[:, -1]])))
for i in range(1, n2):
    if i not in borde: m[lab2 == i] = 1
m = cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
alpha = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.5)
ys, xs = np.where(m > 0); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
pad = 8; x0, y0 = max(0, x0 - pad), max(0, y0 - pad); x1, y1 = min(a.shape[1], x1 + pad), min(a.shape[0], y1 + pad)
# si la foto corta la prenda contra el margen izquierdo (la manga de la foto de espalda), redondear esa esquina
# para que no quede un borde recto artificial (solo se quita fondo de la manga, no se inventa tela)
filas = np.where(m[:, 0] > 0)[0]
if len(filas) > 4:
    ra = min(60.0, len(filas) / 2); yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    for cy, sg in ((filas.min() + ra, -1), (filas.max() - ra, 1)):
        reg = (xx < ra) & ((yy - cy) * sg > 0)
        alpha[reg] *= np.clip(ra + 0.5 - np.hypot(xx[reg] - ra, yy[reg] - cy), 0, 1)
    alpha[:, :6] *= np.linspace(0.0, 1.0, 6)[None, :]
rgba = np.dstack([a, (alpha * 255).astype(np.uint8)])[y0:y1, x0:x1]
Image.fromarray(rgba, "RGBA").save(out)
print(out, "caja", (x0, y0, x1 - x0, y1 - y0), "área", int(m.sum()))
