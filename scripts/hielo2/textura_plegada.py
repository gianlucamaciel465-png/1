# Textura de la remera negra plegada con la espalda hacia arriba (como queda congelada en el bloque).
# Dos capas: tela negra pareja (la luz, las arrugas y el hielo los pone el metraje real) + el estampado REAL de la
# foto de espalda (ROCCÉ tono sobre tono y Founders Privée), extraído con apertura morfológica (la foto tiene una
# viñeta editada muy fuerte y luz despareja: así el estampado sale sin esa mancha). Sin redibujar nada.
# Uso: python textura_plegada.py FOTO_ESPALDA SALIDA.png   (FOTO = PRODUCTO/negra_espalda_arena_DFDC5DED.png)
import sys
import numpy as np, cv2
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
X0, Y0, X1, Y1 = 440, 380, 1880, 1280                 # panel de la espalda: de sisa a sisa, del cuello a media espalda
c = im[Y0:Y1, X0:X1]
L = c.mean(2).astype(np.uint8)
base = cv2.morphologyEx(L, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (71, 71)))
base = cv2.GaussianBlur(base.astype(np.float32), (0, 0), 12)
hp = np.clip(L.astype(np.float32) - base, 0, None)          # lo que el estampado suma sobre la tela
# solo dentro de la remera (arriba de los hombros el recorte toca arena): máscara de tela con huecos rellenos
tela = (cv2.GaussianBlur(L, (0, 0), 3) < 110).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(tela, 8)
tela = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
inv = 1 - tela; n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
bordes = set(np.unique(np.concatenate([lab2[0], lab2[-1], lab2[:, 0], lab2[:, -1]])))
for i in range(1, n2):
    if i not in bordes: tela[lab2 == i] = 1
tela = cv2.erode(tela, np.ones((25, 25), np.uint8)).astype(np.float32)
hp *= cv2.GaussianBlur(tela, (0, 0), 6)
TELA = 30.0
tex = TELA + hp * 0.92                                      # mismo contraste que en la foto (gris ≈ 150–160 sobre negro)
tex = cv2.GaussianBlur(tex, (0, 0), 0.8)
rgb = np.dstack([tex, tex, tex * 1.03])                     # negro apenas frío, como en la foto
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(out)
print(out, rgb.shape[1], "×", rgb.shape[0], "estampado máx", round(float(tex.max()), 1))
