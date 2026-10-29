# ROCCE_logo_sin_fondo.png a partir del logo ORIGINAL (LOGO/rocce_logo.png, 1254×1254, fondo #FEFEFE ±1).
# Solo se quita el fondo EXTERIOR: la zona clara conectada al borde de la imagen. Las letras blancas de "ROCCÉ"
# quedan adentro del trazo negro y no se tocan. En el contorno (píxeles grises del suavizado entre trazo y fondo)
# el alfa sale de la mezcla: valor = a·trazo + (1−a)·fondo → a = (fondo − valor)/(fondo − trazo), con color de trazo.
# Mismo tamaño y posición que el original (no se redibuja ni se recorta).
# Uso: python logo_sin_fondo.py ORIGINAL.png SALIDA.png
import sys
import numpy as np, cv2
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
rgb = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
L = rgb.mean(2)
FONDO = float(np.median(L[:20, :20]))
claro = (L > 128).astype(np.uint8)
n, lab = cv2.connectedComponents(claro, connectivity=4)
bordes = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
exterior = np.isin(lab, list(bordes))
trazo = (L < 60) & ~exterior
C = np.median(rgb[trazo], 0); Lc = float(C.mean())
a = np.ones(L.shape, np.float32)
ae = np.clip((FONDO - L) / (FONDO - Lc), 0, 1)
ae[L >= FONDO - 2] = 0.0                       # fondo con ruido de ±1: transparente
a[exterior] = ae[exterior]
col = rgb.copy()
col[exterior] = C                              # color de los píxeles de borde: el del trazo (sin blanco mezclado)
rgba = np.dstack([col, a * 255]).round().clip(0, 255).astype(np.uint8)
Image.fromarray(rgba, "RGBA").save(out)
print(out, "fondo", FONDO, "trazo", C.round(1), "píxeles transparentes", int((a == 0).sum()), "semitransparentes", int(((a > 0) & (a < 1)).sum()),
      "letras internas claras conservadas", int((~exterior & (L > 200)).sum()))
