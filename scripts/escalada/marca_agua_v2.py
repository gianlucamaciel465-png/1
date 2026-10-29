# Quita la marca de agua NEURONVISUALS (capa fija semitransparente: letras blancas + sombra oscura) de cada cuadro,
# sin parches ni desenfoque: se resta la capa (modelo I = B·(1 − αb − αs) + 255·αb) con su transparencia medida
# en 474 cuadros (marca_agua_v4.npz) y alineada por cuadro (la grabación de pantalla la mueve ±0,5 px).
# Lo que queda (compresión en los bordes de las letras) se completa solo dentro del trazo fino, con el grano del
# fondo. Uso: from marca_agua_v2 import quitar; quitar(img_rgb_uint8, semilla)
import os
import numpy as np, cv2
_ma = np.load(os.path.join(os.environ.get("ESCALADA_TRABAJO", "."), "an", "marca_agua_v4.npz"))
AW, AK = _ma["alpha"][..., ::-1].copy(), _ma["sombra"][..., ::-1].copy()      # el archivo está en BGR
X0, Y0, X1, Y1 = map(int, _ma["caja"])
LET = (AW.mean(2) > 0.02)
TRAZO = cv2.dilate(((AW.mean(2) > 0.03) | (AK.mean(2) > 0.05)).astype(np.uint8), np.ones((2, 2), np.uint8))

def _resta(I, aw, ak):
    return (I - 255 * aw) / np.maximum(1 - aw - ak, 0.3)

def _resid(q):
    return float(np.abs(q - cv2.GaussianBlur(q, (0, 0), 2.0))[LET].mean())

def quitar(img, semilla=0):
    I = img[Y0:Y1, X0:X1].astype(np.float32)
    h, w = AW.shape[:2]
    mejor = None
    for dx in np.arange(-1.0, 1.01, 0.25):
        for dy in np.arange(-1.0, 1.01, 0.25):
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            aw = cv2.warpAffine(AW, M, (w, h), flags=cv2.INTER_LINEAR)
            ak = cv2.warpAffine(AK, M, (w, h), flags=cv2.INTER_LINEAR)
            for g in (0.95, 1.05, 1.15):
                r = _resid(_resta(I, aw * g, ak * g))
                if mejor is None or r < mejor[0]: mejor = (r, aw * g, ak * g)
    q = np.clip(_resta(I, mejor[1], mejor[2]), 0, 255)
    # donde el fondo es liso (cielo negro, pared gris), lo que deja la compresión en los bordes de las letras se
    # completa desde alrededor (trazo + halo); cerca de bordes reales del dibujo (torre, risco, rótulos) se deja la
    # resta, que conserva esos bordes
    zona = cv2.dilate(TRAZO, np.ones((5, 5), np.uint8))
    inp = cv2.inpaint(np.clip(q + 0.5, 0, 255).astype(np.uint8), zona, 4, cv2.INPAINT_TELEA).astype(np.float32)
    gq = cv2.morphologyEx(cv2.cvtColor(inp.astype(np.uint8), cv2.COLOR_RGB2GRAY), cv2.MORPH_GRADIENT,
                          np.ones((3, 3), np.uint8)).astype(np.float32)
    liso = np.clip((26 - cv2.dilate(gq, np.ones((3, 3), np.uint8))) / 10, 0, 1)    # solo se respeta un borde fuerte (torre, rótulos)
    hp = q - cv2.GaussianBlur(q, (0, 0), 1.5)
    anillo = cv2.dilate(zona, np.ones((9, 9), np.uint8)) > zona
    v = hp[anillo]; sd = float(min(1.2, 1.4826 * np.median(np.abs(v - np.median(v)))))   # grano del fondo (robusto)
    inp += np.random.default_rng(semilla).normal(0, sd, inp.shape[:2])[..., None]
    m = (cv2.GaussianBlur(zona.astype(np.float32), (0, 0), 1.0) * liso)[..., None]
    img[Y0:Y1, X0:X1] = np.clip(q * (1 - m) + inp * m + 0.5, 0, 255).astype(np.uint8)
    return mejor[0]
