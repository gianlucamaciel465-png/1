# Sigue los rótulos en inglés de R1 cuadro a cuadro (60 fps): posición (traslación) y opacidad.
# Plantilla = recorte del rótulo en un cuadro de referencia; búsqueda en una ventana alrededor de la posición prevista
# (posición anterior + velocidad), con correlación normalizada (no depende del brillo, sirve mientras se apaga).
# Opacidad = (brillo del texto − fondo) / (lo mismo en la referencia).
# Uso (Python con OpenCV): python seguir_rotulos.py SEQ_DIR SALIDA.json f0 f1
import sys, json
import numpy as np, cv2
from PIL import Image

seq, out, f0, f1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
REF = 30
# cajas ajustadas a las letras en el cuadro REF (x0, y0, x1, y1), medidas a mano y por perfil de columnas
CAJAS = {"FEAR": (80, 1072, 185, 1096), "OPINIONS": (122, 982, 343, 1007), "DOUBT": (271, 926, 414, 951),
         "LAZINESS": (357, 880, 575, 905), "EXCUSES": (492, 750, 689, 775)}
M = 6

PAD = 320   # margen negro: permite seguir un rótulo que sale de cuadro (coordenadas guardadas sin el margen)
def gris(f, pad=True):
    a = np.asarray(Image.open(f"{seq}/{f + 1:04d}.png").convert("RGB")).astype(np.float32)
    if pad: a = np.pad(a, ((PAD, PAD), (PAD, PAD), (0, 0)))
    return a.mean(2), a

g0, a0 = gris(REF, pad=False)
tpl, mask_t = {}, {}
for k, (x0, y0, x1, y1) in CAJAS.items():
    t = g0[y0 - M:y1 + 1 + M, x0 - M:x1 + 1 + M].copy()
    sat = a0[y0 - M:y1 + 1 + M, x0 - M:x1 + 1 + M].max(2) - a0[y0 - M:y1 + 1 + M, x0 - M:x1 + 1 + M].min(2)
    m = (t > 120) & (sat < 30)
    m[:M, :] = m[-M:, :] = False; m[:, :M] = m[:, -M:] = False
    if k == "OPINIONS":                      # sin la cabeza que toca la S
        yy, xx = np.mgrid[0:t.shape[0], 0:t.shape[1]]
        m &= np.hypot(xx - (362 - (x0 - M)), yy - (996 - (y0 - M))) > 22
    tpl[k], mask_t[k] = t, m

def opac(g, k, x, y):
    t, m = tpl[k], mask_t[k]
    h, w = t.shape
    if x < 0 or y < 0 or x + w > g.shape[1] or y + h > g.shape[0]:
        x0c, y0c = max(0, x), max(0, y); x1c, y1c = min(g.shape[1], x + w), min(g.shape[0], y + h)
        if x1c - x0c < 10 or y1c - y0c < 10: return 0.0
        sub = np.zeros_like(t); sub[y0c - y:y1c - y, x0c - x:x1c - x] = g[y0c:y1c, x0c:x1c]
        valid = np.zeros_like(m); valid[y0c - y:y1c - y, x0c - x:x1c - x] = True
    else:
        sub = g[y:y + h, x:x + w]; valid = np.ones_like(m)
    # solo cuenta lo que cae dentro del cuadro real (no el margen negro agregado)
    yy, xx = np.mgrid[y:y + h, x:x + w]
    valid = valid & (xx >= PAD) & (xx < g.shape[1] - PAD) & (yy >= PAD) & (yy < g.shape[0] - PAD)
    ring = (~cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)) & valid
    mm = m & valid
    if mm.sum() < 20: return 0.0
    ref = t[m].mean() - np.median(t[~cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)])
    return float(np.clip((sub[mm].mean() - np.median(sub[ring])) / ref, 0, 1.3))

res = {k: {} for k in CAJAS}
for k, (x0, y0, x1, y1) in CAJAS.items():
    for order in (range(REF, f1 + 1), range(REF, f0 - 1, -1)):
        x, y = x0 - M + PAD, y0 - M + PAD; vx, vy = 0.0, 0.0; perdido = 0
        for f in order:
            g, _ = gris(f)
            ex, ey = x + vx, y + vy
            S = 26 if abs(vx) + abs(vy) < 6 else 40
            h, w = tpl[k].shape
            X0, Y0 = int(max(0, ex - S)), int(max(0, ey - S)); X1, Y1 = int(min(g.shape[1], ex + w + S)), int(min(g.shape[0], ey + h + S))
            sc, nx, ny = -1, ex, ey
            if X1 - X0 > w and Y1 - Y0 > h:
                r = cv2.matchTemplate(g[Y0:Y1, X0:X1], tpl[k], cv2.TM_CCOEFF_NORMED)
                # premio a la cercanía con la posición prevista (evita saltar a otro rótulo superpuesto)
                yy, xx = np.mgrid[0:r.shape[0], 0:r.shape[1]]
                rr = r - 0.004 * np.hypot(xx + X0 - ex, yy + Y0 - ey)
                iy, ix = np.unravel_index(np.argmax(rr), r.shape); sc = float(r[iy, ix]); nx, ny = ix + X0, iy + Y0
            if sc > 0.45:
                vx, vy = 0.6 * vx + 0.4 * (nx - x), 0.6 * vy + 0.4 * (ny - y); x, y = nx, ny; perdido = 0
            else:
                x, y = ex, ey; perdido += 1           # sin coincidencia: sigue con la velocidad
            op = opac(g, k, int(round(x)), int(round(y))) if perdido < 12 else 0.0
            res[k][f] = {"x": float(x + M - PAD), "y": float(y + M - PAD), "score": sc, "op": op}
        print(k, "ok")
json.dump(res, open(out, "w"))
