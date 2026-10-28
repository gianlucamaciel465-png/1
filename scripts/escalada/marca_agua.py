# Estima la marca de agua "NEURONVISUALS" (capa fija en pantalla, blanca semitransparente) para poder reencuadrar
# un plano sin moverla: alfa = (I - fondo) / (255 - fondo), con el fondo estimado por apertura morfológica
# (las letras son finas). Promedia muchos cuadros de planos donde el fondo es oscuro y liso.
# Uso: python marca_agua.py SEQ_DIR SALIDA.npz
import sys
import numpy as np, cv2
from PIL import Image
seq, out = sys.argv[1], sys.argv[2]
X0, Y0, X1, Y1 = 360, 1545, 720, 1615
acc = []; 
for f in list(range(2, 72, 2)) + list(range(305, 372, 3)):
    a = np.asarray(Image.open(f"{seq}/{f:04d}.png").convert("L"), np.float32)[Y0:Y1, X0:X1]
    bg = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    bg = cv2.GaussianBlur(bg, (0, 0), 2)
    al = np.clip((a - bg) / np.maximum(1, 255 - bg), 0, 1)
    acc.append(al)
al = np.median(np.stack(acc), 0)
al[al < 0.02] = 0
np.savez(out, alpha=al.astype(np.float32), caja=np.array([X0, Y0, X1, Y1]))
ys, xs = np.where(al > 0.05)
print("alfa máx %.3f" % al.max(), "caja letras", xs.min() + X0, ys.min() + Y0, xs.max() + X0, ys.max() + Y0)
Image.fromarray((np.clip(al * 4, 0, 1) * 255).astype(np.uint8)).save(out.replace(".npz", ".png"))
