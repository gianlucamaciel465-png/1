# Desenfoque de cada cuadro medido sobre el logo del jogger (lo único con bordes netos sobre la tela): el logo del
# cuadro clave se lleva al cuadro con la homografía (y el barrido del obturador) y se busca el desenfoque gaussiano
# extra que mejor lo iguala al logo real. La remera recibe ese mismo desenfoque extra (compresión, foco, movimiento).
# Uso: python desenfoque.py CUADROS_DIR SEGUIMIENTO.json SALIDA.json
import sys, json, os
import numpy as np, cv2
sys.argv += []
src, seg, out = sys.argv[1:4]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(seg))
CAJAS = {345: (360, 446, 410, 458), 452: (295, 380, 435, 488), 490: (370, 430, 452, 482)}
W, H = 512, 1108
OBTURADOR = 0.5

def leer(f): return cv2.imread(f"{src}/{f:04d}.png")[..., 1].astype(np.float32)

def hom(f): return np.array(S[str(f)]["H"]) if str(f) in S else None

def subcuadros(f):
    e = S[str(f)]; Hf = hom(f)
    Ha, Hb = hom(f - 1), hom(f + 1)
    if Ha is not None and S[str(f - 1)]["clave"] != e["clave"]: Ha = None
    if Hb is not None and S[str(f + 1)]["clave"] != e["clave"]: Hb = None
    ref = np.float32([[0, 0], [W, 0], [W, H], [0, H]]).reshape(-1, 1, 2)
    cf = cv2.perspectiveTransform(ref, Hf)
    ca = cv2.perspectiveTransform(ref, Ha) if Ha is not None else None
    cb = cv2.perspectiveTransform(ref, Hb) if Hb is not None else None
    if ca is None and cb is not None: ca = 2 * cf - cb
    if cb is None and ca is not None: cb = 2 * cf - ca
    if ca is None: return [Hf]
    r = []
    for t in np.linspace(-OBTURADOR / 2, OBTURADOR / 2, 9):
        c = cf + t * (cb - cf) if t >= 0 else cf + t * (cf - ca)
        r.append(cv2.getPerspectiveTransform(ref.reshape(-1, 2), np.float32(c.reshape(-1, 2))))
    return r

res = {}
for f in sorted(int(x) for x in S):
    k = S[str(f)]["clave"]; x0, x1, y0, y1 = CAJAS[k]
    gk = leer(k); plantilla = np.zeros_like(gk); plantilla[y0:y1, x0:x1] = gk[y0:y1, x0:x1]
    msk = np.zeros_like(gk); msk[y0 + 3:y1 - 3, x0 + 3:x1 - 3] = 1
    Hs = subcuadros(f)
    pw = np.mean([cv2.warpPerspective(plantilla, h, (W, H), flags=cv2.INTER_LINEAR) for h in Hs], 0)
    mw = cv2.warpPerspective(msk, Hs[len(Hs) // 2], (W, H), flags=cv2.INTER_NEAREST) > 0.5
    mw = cv2.erode(mw.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    g = leer(f)
    if mw.sum() < 60: res[f] = 0.0; continue
    a = g[mw]; a = (a - a.mean()) / (a.std() + 1e-3)
    mejor = None
    for s in [0, 0.5, 0.8, 1.1, 1.4, 1.8, 2.2, 2.7, 3.3, 4.0]:
        b = cv2.GaussianBlur(pw, (0, 0), s) if s > 0 else pw
        b = b[mw]; b = (b - b.mean()) / (b.std() + 1e-3)
        e = float(np.mean((a - b) ** 2))
        if mejor is None or e < mejor[0]: mejor = (e, s)
    res[f] = mejor[1]
json.dump(res, open(out, "w"))
for p, (a, b) in {"A": (305, 402), "C": (440, 469), "D": (470, 497)}.items():
    print(p, [res[f] for f in range(a, b + 1)])
