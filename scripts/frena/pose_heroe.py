# Pose del protagonista de R1 (figura de palitos blanca de Neuron Visuals) cuadro a cuadro, para vestirlo con la remera.
# Estima por cuadro: cabeza (centro y radio), cuello N, pelvis P, hombro S y dirección del brazo cercano (blanco)
# y del lejano (gris). Método:
#   cabeza = punto más grueso del blanco (transformada de distancia) cerca de la posición prevista;
#   torso  = segmento recto más largo (3,0–4,6 radios) que arranca en el borde de la cabeza y queda dentro del blanco;
#   brazos = segmento de ~1,8 radios desde el hombro que queda dentro del blanco (cercano) o del gris (lejano).
# Uso (Python con OpenCV, p. ej. demucs-env):
#   python pose_heroe.py SEQ_DIR SALIDA.json f0 f1 x y     (SEQ_DIR con 0001.png…; x, y = cabeza aproximada en f0)
import sys, json
import numpy as np, cv2
from PIL import Image

seq, out, f0, f1, hx, hy = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])
R = 380

def masks(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    L = (r + g + b) / 3
    red = (r - np.maximum(g, b)) > 50
    return (L > 200) & ~red, (L > 115) & ~red

def cover(mask, p, q, n=40):
    """Fracción de puntos del segmento p→q (arrays N×2) dentro de la máscara."""
    t = np.linspace(0, 1, n)[None, :, None]
    pts = p[:, None, :] + (q - p)[:, None, :] * t
    x = np.clip(np.round(pts[..., 0]).astype(int), 0, mask.shape[1] - 1)
    y = np.clip(np.round(pts[..., 1]).astype(int), 0, mask.shape[0] - 1)
    inside = (pts[..., 0] >= 0) & (pts[..., 0] < mask.shape[1]) & (pts[..., 1] >= 0) & (pts[..., 1] < mask.shape[0])
    return (mask[y, x] & inside).mean(1)

ang = np.radians(np.arange(0, 360, 3)); U = np.stack([np.cos(ang), np.sin(ang)], 1)
res = {}; px, py = float(hx), float(hy); vx, vy = 0.0, 0.0
for f in range(f0, f1 + 1):
    a = np.asarray(Image.open(f"{seq}/{f + 1:04d}.png").convert("RGB"))
    Hh, Ww = a.shape[:2]
    ex, ey = px + vx, py + vy                                   # posición prevista
    x0, y0 = int(max(0, ex - R)), int(max(0, ey - R)); x1, y1 = int(min(Ww, ex + R)), int(min(Hh, ey + R))
    white, body = masks(a[y0:y1, x0:x1])
    wb = white.astype(np.uint8)
    dt = cv2.distanceTransform(wb, cv2.DIST_L2, 5)
    yy, xx = np.mgrid[0:dt.shape[0], 0:dt.shape[1]]
    score = dt - 0.008 * np.hypot(xx - (ex - x0), yy - (ey - y0))
    hy_, hx_ = np.unravel_index(np.argmax(score), dt.shape); rh = float(dt[hy_, hx_])
    if rh < 8: res[f] = None; continue
    Hc = np.array([hx_, hy_], float)
    inner = cv2.erode(wb, np.ones((3, 3), np.uint8)).astype(bool)
    # torso: arranca a rh+7 del centro (después del contorno oscuro entre cabeza y cuello), dirección cercana a la radial
    best = (-1, None)
    A1 = np.repeat(np.arange(len(U)), 27); dA = np.tile(np.arange(-13, 14), len(U))
    A2 = (A1 + dA) % len(U)
    p0 = Hc[None, :] + U[A1] * (rh + 7)
    for L in np.linspace(4.4, 2.6, 10) * rh:
        q = p0 + U[A2] * L
        c = cover(inner, p0, q)
        k = int(np.argmax(c))
        if c[k] >= 0.90:
            best = (L, (Hc + U[A2[k]] * rh * 0.95, q[k])); break
    if best[1] is None: res[f] = None; continue
    N, P = best[1]; ut = (P - N) / np.linalg.norm(P - N); Lt = float(best[0])
    S = N + ut * 0.12 * Lt
    # brazos: desde una raíz cerca del hombro, contando solo las muestras fuera de la cabeza y del torso
    grey = body & ~cv2.dilate(wb, np.ones((5, 5), np.uint8)).astype(bool)
    t = np.linspace(1.0, 3.0, 28) * rh
    nt = np.array([-ut[1], ut[0]])
    arms = {}
    for nombre, m in (("cerca", inner), ("lejos", grey)):
        best = (0, None, None)
        for d_off in (-24, -16, -8, 0, 8, 16, 24):
            for d_up in (-6, 0, 8, 16, 24):
                S0 = S + nt * d_off + ut * d_up
                pts = S0[None, None, :] + U[:, None, :] * t[None, :, None]
                dH = np.hypot(pts[..., 0] - Hc[0], pts[..., 1] - Hc[1])
                v = pts - N[None, None, :]; tt = np.clip((v @ ut) / Lt, 0, 1)
                dT = np.linalg.norm(v - tt[..., None] * Lt * ut[None, None, :], axis=-1)
                valid = (dH > rh + 3) & (dT > 11)
                xi = np.clip(np.round(pts[..., 0]).astype(int), 0, wb.shape[1] - 1); yi = np.clip(np.round(pts[..., 1]).astype(int), 0, wb.shape[0] - 1)
                hit = m[yi, xi] & valid
                nv = valid.sum(1); c = np.where(nv >= 10, hit.sum(1) / np.maximum(nv, 1), 0) * (U @ ut < 0.85)
                c = c - 0.002 * abs(d_off)                      # a igual cobertura, raíz más cerca del eje
                k = int(np.argmax(c))
                if c[k] > best[0]: best = (c[k], U[k], S0)
        arms[nombre] = None if best[0] < 0.7 else [float(best[1][0]), float(best[1][1]), float(best[0]),
                                                   float(best[2][0] + x0), float(best[2][1] + y0)]
    off = np.array([x0, y0], float)
    Hn = Hc + off
    res[f] = {"H": Hn.tolist(), "r": rh, "N": (N + off).tolist(), "P": (P + off).tolist(), "S": (S + off).tolist(),
              "L": Lt, "brazos": arms}
    vx, vy = Hn[0] - px, Hn[1] - py
    px, py = Hn[0], Hn[1]
json.dump(res, open(out, "w"), indent=0)
print("pose:", len([v for v in res.values() if v]), "de", len(res), "cuadros")
