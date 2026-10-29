# Seguimiento del bloque de hielo (rígido) en cada plano de la referencia: homografía de cada cuadro respecto de un
# cuadro clave, con puntos de Lucas-Kanade sobre la prenda y el hielo (comprobación ida y vuelta + RANSAC). Si quedan
# pocos puntos se detectan nuevos y se llevan al cuadro clave con la homografía vigente.
# Control: IoU entre la máscara de tela de cada cuadro y la del cuadro clave llevada con la homografía.
# Uso: python seguir.py CUADROS_DIR SALIDA.json   (planos y cuadros clave en PLANOS)
import sys, json
import numpy as np, cv2
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from reemplazo import mascara_tela

PLANOS = {"A": (305, 402, 345), "C": (440, 469, 452), "D": (470, 497, 490)}
src, out = sys.argv[1], sys.argv[2]
EROSION = len(sys.argv) > 3 and sys.argv[3] == "tela"     # puntos solo sobre la tela (plano de la cara superior)

def leer(f):
    im = cv2.imread(f"{src}/{f:04d}.png")
    return im, cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

def region(im_bgr):
    m = mascara_tela(im_bgr[..., ::-1].astype(np.float32))
    return (cv2.erode(m, np.ones((9, 9), np.uint8)) if EROSION else cv2.dilate(m, np.ones((31, 31), np.uint8))), m

def detectar(g, reg, n=500):
    p = cv2.goodFeaturesToTrack(g, n, 0.005, 5, mask=reg, blockSize=7)
    return p.reshape(-1, 2).astype(np.float32) if p is not None else np.zeros((0, 2), np.float32)

LK = dict(winSize=(25, 25), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.01))

def recorrer(orden, k, gk, regk):
    pk = detectar(gk, regk); cur = pk.copy(); gp = gk
    Hs = {}; Hprev = np.eye(3)
    for f in orden:
        im, g = leer(f)
        if len(cur) < 8: raise RuntimeError(f"sin puntos en {f}")
        # predicción con la homografía anterior para movimientos grandes
        p1, st, _ = cv2.calcOpticalFlowPyrLK(gp, g, cur.reshape(-1, 1, 2), None, **LK)
        p0r, st2, _ = cv2.calcOpticalFlowPyrLK(g, gp, p1, None, **LK)
        p1 = p1.reshape(-1, 2); fb = np.linalg.norm(p0r.reshape(-1, 2) - cur, axis=1)
        ok = (st.ravel() == 1) & (st2.ravel() == 1) & (fb < 1.0)
        H, inl = cv2.findHomography(pk[ok], p1[ok], cv2.RANSAC, 2.0, maxIters=4000, confidence=0.999)
        if H is None: raise RuntimeError(f"homografía fallida en {f}")
        inl = inl.ravel().astype(bool)
        keep = np.flatnonzero(ok)[inl]
        pk, cur = pk[keep], p1[keep]
        if len(cur) < 150:                                   # renovar puntos
            reg = cv2.warpPerspective(regk, H, (g.shape[1], g.shape[0]), flags=cv2.INTER_NEAREST)
            nuevos = detectar(g, reg, 400)
            if len(nuevos):
                d = np.min(np.linalg.norm(nuevos[:, None] - cur[None], axis=2), axis=1) if len(cur) else np.full(len(nuevos), 99.)
                nuevos = nuevos[d > 4]
                pkn = cv2.perspectiveTransform(nuevos.reshape(-1, 1, 2), np.linalg.inv(H)).reshape(-1, 2)
                pk = np.concatenate([pk, pkn]); cur = np.concatenate([cur, nuevos])
        Hs[f] = (H, int(inl.sum()))
        gp = g
    return Hs

res = {}
for nombre, (a, b, k) in PLANOS.items():
    imk, gk = leer(k); regk, mk = region(imk)
    Hs = {k: (np.eye(3), -1)}
    Hs.update(recorrer(range(k + 1, b + 1), k, gk, regk))
    Hs.update(recorrer(range(k - 1, a - 1, -1), k, gk, regk))
    for f in range(a, b + 1):
        H, n = Hs[f]
        im, _ = leer(f); _, m = region(im)
        mw = cv2.warpPerspective(mk, H, (m.shape[1], m.shape[0]), flags=cv2.INTER_NEAREST)
        iou = float((m & mw).sum() / max(1, (m | mw).sum()))
        res[f] = {"plano": nombre, "clave": k, "H": np.asarray(H).tolist(), "puntos": n, "iou": round(iou, 3)}
    ious = [res[f]["iou"] for f in range(a, b + 1)]
    print(nombre, a, b, "clave", k, "IoU mín", min(ious), "en", a + int(np.argmin(ious)), "media", round(float(np.mean(ious)), 3))
json.dump(res, open(out, "w"))
