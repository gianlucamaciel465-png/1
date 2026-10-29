# Recortes reales de la remera negra para ROCCE_ANTES_DEL_APLAUSO (sin redibujar nada):
#   remera_frente.png — prenda completa de frente (PRODUCTO/negra_frente_arena_F266ACD9.png) sin la arena: alfa por
#     oscuridad (la tela es negra sobre arena clara), huecos rellenos (el estampado claro del pecho queda adentro),
#     borde suavizado y descontaminado (el borde toma el color de la tela, no el de la arena).
#   espalda_detalle.png — detalle de la espalda (Founders Privée + ROCCÉ tono sobre tono) de
#     PRODUCTO/negra_espalda_arena_DFDC5DED.png, recorte rectangular con su luz real (para una tarjeta con marco).
# Uso: python recortes.py SALIDA_DIR
import os, sys
import numpy as np, cv2
from PIL import Image
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
out = sys.argv[1]; os.makedirs(out, exist_ok=True)

im = np.asarray(Image.open(os.path.join(R, "PRODUCTO", "negra_frente_arena_F266ACD9.png")).convert("RGB")).astype(np.float32)
L = im.mean(2)
H, W = L.shape
# la foto trae una barra negra abajo: buscar la primera fila casi negra en todo el ancho
filas = np.where((L < 25).mean(1) > 0.97)[0]
y_barra = int(filas.min()) if len(filas) else H
m = (cv2.GaussianBlur(L, (0, 0), 2) < 95).astype(np.uint8); m[y_barra - 4:] = 0
n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
k = 1 + int(np.argmax(st[1:, 4])); m = (lab == k).astype(np.uint8)
inv = 1 - m; n2, lab2 = cv2.connectedComponents(inv, connectivity=4)
bordes = set(np.unique(np.concatenate([lab2[0], lab2[-1], lab2[:, 0], lab2[:, -1]])))
for i in range(1, n2):
    if i not in bordes: m[lab2 == i] = 1
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
# alfa suave: transición de 2–3 px según la luminancia en el borde
dist_in = cv2.distanceTransform(m, cv2.DIST_L2, 5); dist_out = cv2.distanceTransform(1 - m, cv2.DIST_L2, 5)
sd = np.where(m > 0, dist_in, -dist_out)
a = np.clip((sd + 1.5) / 3.0, 0, 1)
# descontaminar: en el borde, color de la tela cercana (media local dentro de la máscara)
mf = m.astype(np.float32)
num = cv2.GaussianBlur(im * mf[..., None], (0, 0), 4); den = cv2.GaussianBlur(mf, (0, 0), 4)[..., None]
tela = num / np.maximum(den, 1e-3)
borde = ((a > 0) & (a < 1) | (np.abs(sd) < 3))[..., None]
col = np.where(borde, tela, im)
ys, xs = np.nonzero(a > 0.01); x0, x1, y0, y1 = xs.min() - 20, xs.max() + 20, ys.min() - 20, ys.max() + 20
x0, y0 = max(0, x0), max(0, y0)
rgba = np.dstack([np.clip(col, 0, 255), a * 255])[y0:y1, x0:x1].astype(np.uint8)
Image.fromarray(rgba, "RGBA").save(os.path.join(out, "remera_frente.png"))
print("remera_frente.png", rgba.shape[1], "×", rgba.shape[0], "barra en y =", y_barra)

es = Image.open(os.path.join(R, "PRODUCTO", "negra_espalda_arena_DFDC5DED.png")).convert("RGB")
# hombros a media espalda, centrado en el estampado (ROCCÉ arriba, Founders Privée)
det = es.crop((300, 330, 2040, 1620))
det.save(os.path.join(out, "espalda_detalle.png"))
print("espalda_detalle.png", det.size)
