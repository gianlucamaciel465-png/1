# Reemplazo de la prenda congelada en el metraje REAL de la referencia (bloque transparente con un jogger bordó):
# la remera negra plegada (textura_plegada.py) queda adentro del mismo hielo, con la misma luz y lo que el hielo pone
# delante (escarcha, brillos, burbujas, esquirlas, agua).
#
# Modelo por píxel: observado = s · c_b + w · (1,1,1)
#   c_b = color de la tela bordó bien iluminada (medido en cada cuadro), s = cuánta tela se ve (sombra, arrugas,
#   lo que tapa el hielo), w = luz neutra que suma el hielo por delante. Se resuelve s, w por mínimos cuadrados.
#   nuevo = observado − s·c_b + s·remera(x)  → cambia la tela y se conserva todo lo demás tal cual.
# La remera se ubica con una homografía al cuadrilátero de la prenda (máscara de tela por cuadro, suavizada en el
# tiempo dentro de cada plano). El logo blanco del jogger se borra (rellenando s y w desde el entorno) antes.
import os, sys, json, math
import numpy as np, cv2
from PIL import Image

def resolver(obs, cb):
    """s, w y residuo por píxel para observado ≈ s·cb + w·1."""
    A = np.stack([cb, np.ones(3, np.float32)], 1)            # 3×2
    P = np.linalg.pinv(A)                                       # 2×3
    sw = obs @ P.T                                              # H×W×2
    rec = sw @ A.T
    res = np.abs(obs - rec).max(2)
    return sw[..., 0], sw[..., 1], res

def color_tela(obs, y_min=100):
    R, G, B = obs[..., 0], obs[..., 1], obs[..., 2]
    m = (R - G > 30) & (B > G + 3) & (G < 110)
    m[:y_min] = False
    if m.sum() < 200: return None, m
    d = (R - G)[m]; hi = d > np.percentile(d, 80)
    return np.median(obs[m][hi], 0), m

def mascara_prenda(obs, cb=None, y_min=100):
    """Tela bordó: rojo y azul por encima del verde (la piel tiene azul por debajo del verde; piso e hielo, neutros)."""
    R, G, B = obs[..., 0], obs[..., 1], obs[..., 2]
    rg, bg = R - G, B - G
    m = ((rg > 10) & (bg > 4) & (bg < rg) & (G < 150)).astype(np.uint8)
    m[:y_min] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n < 2: return None
    k = 1 + int(np.argmax(st[1:, 4])); m = (lab == k).astype(np.uint8)
    inv = 1 - m; n2, lab2 = cv2.connectedComponents(inv, connectivity=4)
    bordes = set(np.unique(np.concatenate([lab2[0], lab2[-1], lab2[:, 0], lab2[:, -1]])))
    for i in range(1, n2):
        if i not in bordes: m[lab2 == i] = 1
    return m

def peso_tela(obs):
    """0–1: cuánto se parece el tono al bordó del jogger. La tela tiene el azul a ~mitad de camino entre verde y rojo
    (B−G ≈ 0,5·(R−G)), también bajo escarcha; la piel tiene B−G ≈ 0–0,2·(R−G); hielo, piso y herramienta son neutros."""
    R, G, B = obs[..., 0], obs[..., 1], obs[..., 2]
    rg, bg = R - G, B - G
    razon = bg / np.maximum(rg, 1.0)
    return (np.clip((razon - 0.22) / 0.12, 0, 1) * np.clip((rg - 6) / 10, 0, 1) * (razon < 1.1)).astype(np.float32)

def mascara_tela(obs, y_min=60):
    G = obs[..., 1]
    m = ((peso_tela(obs) > 0.5) & (G < 120)).astype(np.uint8)
    m[:y_min] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n < 2: return m
    k = 1 + int(np.argmax(st[1:, 4])); m = (lab == k).astype(np.uint8)
    inv = 1 - m; n2, lab2 = cv2.connectedComponents(inv, connectivity=4)
    bordes = set(np.unique(np.concatenate([lab2[0], lab2[-1], lab2[:, 0], lab2[:, -1]])))
    for i in range(1, n2):
        if i not in bordes: m[lab2 == i] = 1
    return m

def cuadrilatero(m):
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    hull = cv2.convexHull(max(cnts, key=cv2.contourArea))
    per = cv2.arcLength(hull, True)
    for eps in np.linspace(0.01, 0.12, 40):
        ap = cv2.approxPolyDP(hull, eps * per, True)
        if len(ap) == 4: break
    else:
        r = cv2.minAreaRect(hull); ap = cv2.boxPoints(r).reshape(-1, 1, 2)
    q = ap.reshape(-1, 2).astype(np.float32)
    # ordenar: arriba-izq, arriba-der, abajo-der, abajo-izq
    c = q.mean(0); ang = np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0]); q = q[np.argsort(ang)]
    i0 = int(np.argmin(q.sum(1))); q = np.roll(q, -i0, 0)
    return q

def componer(obs, cb, quad, tex, logo_tex=None, tono=0.45):
    """obs: H×W×3 float. quad: 4×2 (orden arriba-izq, arriba-der, abajo-der, abajo-izq). tex: textura float."""
    H, W = obs.shape[:2]; th, tw = tex.shape[:2]
    src = np.float32([[0, 0], [tw - 1, 0], [tw - 1, th - 1], [0, th - 1]])
    Hm = cv2.getPerspectiveTransform(src, quad.astype(np.float32))
    tw_ = cv2.warpPerspective(tex, Hm, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
    s, w, res = resolver(obs, cb)
    s = np.clip(s, 0, 1.8); w = np.clip(w, 0, 255)
    if logo_tex is not None:                                    # logo del jogger: rellenar s y w desde el entorno
        lm = cv2.warpPerspective(logo_tex, Hm, (W, H), flags=cv2.INTER_LINEAR)
        lm = (cv2.dilate((lm > 0.2).astype(np.uint8), np.ones((5, 5), np.uint8)))
        if lm.any():
            def tapar(x, esc):
                x8 = np.clip(x * esc, 0, 255).astype(np.uint8)
                return cv2.inpaint(x8, lm, 5, cv2.INPAINT_TELEA).astype(np.float32) / esc
            s = np.where(lm > 0, tapar(s, 120.0), s); w = np.where(lm > 0, tapar(w, 1.0), w)
    # tela: solo donde el modelo explica bien el color (no piel ni herramienta ni llama)
    ok = np.clip((40 - res) / 16, 0, 1) * np.clip((s - 0.04) / 0.2, 0, 1)
    ok = cv2.GaussianBlur(ok, (0, 0), 0.8)
    lum_cb = float(cb.mean())
    remera = tw_ / 30.0 * (tono * lum_cb)                      # tela negra = tono × luminancia de la tela original
    viejo = s[..., None] * cb[None, None, :]
    nuevo = s[..., None] * remera
    out = obs + ok[..., None] * (nuevo - viejo)
    return np.clip(out, 0, 255), Hm, ok
