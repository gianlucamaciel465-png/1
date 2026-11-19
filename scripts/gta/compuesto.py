#!/usr/bin/env python3
"""GTA6 «La misión» · prueba del compuesto del estampado de la espalda (Pedro, 19/11/2026). Guion §5 «Compuesto G3/G7».

Método (pensado para G3 y G7, que se van a generar; se valida acá sobre IMG_7887 1,90–3,67, donde hay estampado real):
  1. Modelo del estampado desde PRODUCTO/negra_espalda_estudio.jpg, en luz lineal: fondo de tela por apertura
     morfológica (la foto tiene luz despareja) y, por elemento, alfa y relación de albedo con la tela:
        ρ(x) = 1 + αF(x)·(ρF − 1) + αR(x)·(ρR − 1)        (F = «Founders Privée», R = «ROCCÉ» tono sobre tono)
  2. Registro por cuadro: homografía plantilla → cuadro por Lucas-Kanade (Gauss-Newton con ganancia y sesgo, pirámide de
     desenfoques 4 → 2 → 1 px, pesos de Huber) entre la forma del estampado de estudio y el «exceso de luz» del cuadro
     (L − apertura gris 25 px dentro de la espalda). Arranca en el cuadro anterior. Encima, una MALLA (8×4 nodos,
     base bilineal, regularización laplaciana) que sigue la curvatura de la espalda que la homografía no sigue.
     La ubicación del cuadro 0 parte de un recuadro marcado a mano (ROI0), como haría el editor.
  3. Seguimiento SIN el estampado (lo que vale para un plano generado, cuyo estampado no sirve de guía): homografía
     cuadro a cuadro por LK sobre la luminancia de la espalda (pliegues, cuello, silueta) con el estampado tapado,
     encadenada desde la ubicación del cuadro 0 (T2), y cada cuadro contra el cuadro 0 sin cadena (T3, v2). Se mide su
     deriva contra el registro del paso 2.
  v2 (19/11): borrado limitado a la huella del Founders ubicado; sombreado multiescala σ 5/15/40; razón ρF calibrada en
     c57 (la de estudio da −19,5 % de luminancia al sol); «ROCCÉ» real conservado (la foto no trae su alfa).
  4. Compuesto: se borra el estampado real (sombreado estimado por convolución normalizada σ 5 px sobre la tela + grano
     medido) y se pone el de estudio: salida_lin = borrado_lin + (ρ_warp − 1)·S, con S = sombreado de la tela (luz y
     pliegues del plano). Oclusión: piel, pelo y lo que no es tela quedan con el cuadro original.
Se mide por cuadro: posición, escala y giro del estampado (registro vs seguimiento), IoU y distancia media de bordes
entre el estampado de estudio ubicado y el real, y la diferencia de luminancia del estampado compuesto contra el real.

Uso (venv): python compuesto.py   → TRABAJO/gta/compuesto/ (medidas.json, compuesto_7887.mp4, lado_a_lado_7887.mp4,
            hoja_lado_a_lado_1a1.jpg, grafico_compuesto.png)
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from scipy import ndimage as nd
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, '/home/user/1/scripts/gta'); sys.path.insert(0, '/home/user/1/scripts/fmt')
from comun import T, W, H, FPS, run, guardar_json   # noqa
import video as V, fmt03 as U                       # noqa: E402

TC = T / 'compuesto'
PROD = Path('/home/user/1/PRODUCTO/negra_espalda_estudio.jpg')
CROP = (260, 610, 940, 980)          # zona del estampado en la foto de estudio (1170×2036)
S0 = 0.6                             # escala de la plantilla (≈ tamaño del estampado en 7887 a 1080 de ancho)
N0, NF = 57, 53                      # IMG_7887 c57–c109 (1,90–3,67), a z 1
FONT = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'


def lin(x):
    x = np.asarray(x, np.float32) / 255
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055) * 255


def luma(rgb):
    return rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)


# ==================================================================================================== 1 · estudio
def modelo_estudio():
    a = np.asarray(Image.open(PROD).convert('RGB'), np.float32)
    x0, y0, x1, y1 = CROP
    c = a[y0:y1, x0:x1]; L = luma(c)
    op = nd.grey_opening(L, size=(41, 41))
    ex = L - op
    exs = nd.gaussian_filter(ex, 1.2)
    # «Founders Privée»: exceso alto; «ROCCÉ»: exceso bajo (tono sobre tono) por encima de Founders
    mF = nd.binary_opening(exs > 22, iterations=1)
    lab, k = nd.label(nd.binary_dilation(mF, iterations=3)); s = nd.sum(mF, lab, range(1, k + 1))
    mF &= np.isin(lab, [i + 1 for i, v in enumerate(s) if v > 400])
    ysF = np.nonzero(mF.any(1))[0]; topF = ysF.min()
    aF = np.clip((exs - 10) / (50 - 10), 0, 1) * nd.binary_dilation(mF, iterations=4)
    zona_r = np.zeros_like(mF); zona_r[:max(0, topF - 4), :] = True
    exr = nd.gaussian_filter(ex, 2.0)
    mR = nd.binary_opening((exr > 3.2) & zona_r, iterations=2)
    lab, k = nd.label(mR); s = nd.sum(mR, lab, range(1, k + 1))
    mR &= np.isin(lab, [i + 1 for i, v in enumerate(s) if v > 150])
    aR = np.clip((exr - 1.5) / (5.5 - 1.5), 0, 1) * nd.binary_dilation(mR, iterations=3)
    cl = lin(c)
    base = np.stack([nd.gaussian_filter(nd.grey_opening(cl[..., j], size=(41, 41)), 6) for j in range(3)], -1)
    tela = (aF < 0.02) & (aR < 0.02)
    fuerte_F = aF > 0.9; fuerte_R = aR > 0.8
    rhoF = np.median(cl[fuerte_F] / np.maximum(base[fuerte_F], 1e-4), 0)
    rhoR = np.median(cl[fuerte_R] / np.maximum(base[fuerte_R], 1e-4), 0)
    return dict(aF=aF.astype(np.float32), aR=aR.astype(np.float32), rhoF=rhoF, rhoR=rhoR, crop=CROP,
                bbF=_bb(aF > 0.5), bbR=_bb(aR > 0.5), exceso_F_med=float(np.median(ex[fuerte_F])),
                exceso_R_med=float(np.median(ex[fuerte_R])), tela_L_med=float(np.median(L[tela])))


def _bb(m):
    ys, xs = np.nonzero(m)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def plantilla(M, wR=0.6):
    """forma del estampado para registrar (F = 1, R = wR) a escala S0 con antialias."""
    t = np.clip(M['aF'] + wR * M['aR'], 0, 1)
    t = nd.gaussian_filter(t, 0.5 / S0)
    h, w = t.shape
    ts = np.asarray(Image.fromarray(t).resize((int(w * S0), int(h * S0)), Image.BILINEAR), np.float32)
    return ts


# ==================================================================================================== 2 · video
def cuadros_7887():
    src = TC / '7887_z1.mp4'
    if not src.exists():
        TC.mkdir(parents=True, exist_ok=True)
        U.plano_n('IMG_7887', N0, NF, src)
    raw = run(['ffmpeg', '-v', 'error', '-i', str(src), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def espalda(f, roi):
    """región de la espalda dentro del recuadro roi = (x0, y0, x1, y1): tela oscura poco saturada, cerrada y con
    agujeros llenos (el estampado queda adentro); componente más grande del recuadro."""
    ff = f.astype(np.float32); L = luma(ff); sat = (ff.max(-1) - ff.min(-1)) / (ff.max(-1) + 1)
    x0, y0, x1, y1 = [int(v) for v in roi]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
    m = np.zeros((H, W), bool)
    m[y0:y1, x0:x1] = (L[y0:y1, x0:x1] < 62) & (sat[y0:y1, x0:x1] < 0.32)
    m = nd.binary_opening(m, iterations=2)
    m = nd.binary_closing(m, iterations=8)
    m = nd.binary_fill_holes(m)
    lab, k = nd.label(m)
    if k == 0:
        return m, L, sat
    s_ = nd.sum(m, lab, range(1, k + 1))
    B = lab == (int(np.argmax(s_)) + 1)
    return B, L, sat


def exceso(L, B):
    # el estampado toca el borde de la espalda (no queda como agujero de la tela): se acepta hasta 25 px afuera de B
    P = np.clip(L - nd.grey_opening(L, size=(25, 25)), 0, None) * nd.binary_dilation(B, iterations=25)
    lvl = np.percentile(P[B], 99.3) if B.sum() > 1000 else 1.0
    return np.clip(P / max(lvl, 1e-3), 0, 1.2), float(lvl)


# ==================================================================================================== LK homografía
class LK:
    """registro plantilla → imagen con homografía (8 parámetros) + ganancia y sesgo, Gauss-Newton amortiguado."""
    def __init__(self, Tm, paso=1):
        h, w = Tm.shape
        ys, xs = np.mgrid[0:h:paso, 0:w:paso]
        self.x = xs.ravel().astype(np.float64); self.y = ys.ravel().astype(np.float64)
        self.t = Tm[::paso, ::paso].ravel().astype(np.float64)
        self.cx, self.cy, self.sc = w / 2, h / 2, max(w, h) / 2
        self.xn = (self.x - self.cx) / self.sc; self.yn = (self.y - self.cy) / self.sc

    def aplicar(self, Hn, xn, yn):
        w = Hn[2, 0] * xn + Hn[2, 1] * yn + 1.0
        u = (Hn[0, 0] * xn + Hn[0, 1] * yn + Hn[0, 2]) / w
        v = (Hn[1, 0] * xn + Hn[1, 1] * yn + Hn[1, 2]) / w
        return u, v, w

    def ajustar(self, I, Hn, sigmas=(4, 2, 1), iters=25, mascara=None, ab=(1.0, 0.0), modelo='h', foto=True):
        """foto=False: ganancia y sesgo fijos (registro de formas normalizadas; con ganancia libre hay una solución
        degenerada: a → 0 y la plantilla se va a una zona plana)."""
        a, b = ab
        for sg in sigmas:
            Is = nd.gaussian_filter(I, sg) if sg > 0 else I
            gy, gx = np.gradient(Is)
            Ms = mascara if mascara is None else mascara.astype(np.float64)
            for it in range(iters):
                u, v, w = self.aplicar(Hn, self.xn, self.yn)
                ok = (u > 1) & (u < I.shape[1] - 2) & (v > 1) & (v < I.shape[0] - 2)
                if Ms is not None:
                    mv = nd.map_coordinates(Ms, [v, u], order=0, mode='constant')
                    ok &= mv > 0.5
                if ok.sum() < 500:
                    break
                xn, yn, uu, vv, ww, tt = self.xn[ok], self.yn[ok], u[ok], v[ok], w[ok], self.t[ok]
                Iv = nd.map_coordinates(Is, [vv, uu], order=1)
                Gx = nd.map_coordinates(gx, [vv, uu], order=1); Gy = nd.map_coordinates(gy, [vv, uu], order=1)
                r = Iv - (a * tt + b)
                # pesos de Huber
                s_r = max(1.4826 * np.median(np.abs(r)), 0.05 * max(1e-6, float(np.abs(tt).max()) if foto is False else float(np.std(tt)) + 1e-6))
                k = 1.5 * s_r
                wt = np.where(np.abs(r) <= k, 1.0, k / np.maximum(np.abs(r), 1e-9))
                if modelo == 'sim':    # similitud (escala, giro, traslación): arranque robusto
                    Js = np.stack([Gx * xn + Gy * yn, -Gx * yn + Gy * xn, Gx, Gy], 1)
                    A = Js.T @ (Js * wt[:, None]); g = Js.T @ (wt * r)
                    A += np.diag(np.diag(A)) * 1e-3 + np.eye(4) * 1e-9
                    d = -np.linalg.solve(A, g)
                    Hn = Hn + np.array([[d[0], -d[1], d[2]], [d[1], d[0], d[3]], [0, 0, 0]])
                    if np.abs(d).max() < 1e-4:
                        break
                    continue
                J = np.stack([Gx * xn / ww, Gx * yn / ww, Gx / ww, Gy * xn / ww, Gy * yn / ww, Gy / ww,
                              -(Gx * uu + Gy * vv) * xn / ww, -(Gx * uu + Gy * vv) * yn / ww, -tt, -np.ones_like(tt)], 1)
                if modelo == 's':      # sin perspectiva (afín) en el arranque grueso
                    J[:, 6:8] = 0
                if not foto:
                    J[:, 8:10] = 0
                A = J.T @ (J * wt[:, None]); g = J.T @ (wt * r)
                A += np.diag(np.diag(A)) * 1e-3 + np.eye(10) * 1e-9
                d = -np.linalg.solve(A, g)
                Hn = Hn + np.array([[d[0], d[1], d[2]], [d[3], d[4], d[5]], [d[6], d[7], 0]])
                a += d[8]; b += d[9]
                if np.abs(d[:8]).max() < 1e-4:
                    break
        return Hn, (a, b)

    def a_pixeles(self, Hn):
        """homografía en coordenadas de plantilla en píxeles (sin normalizar)."""
        Nrm = np.array([[1 / self.sc, 0, -self.cx / self.sc], [0, 1 / self.sc, -self.cy / self.sc], [0, 0, 1]])
        return Hn @ Nrm


def descomponer(Hp, cx, cy):
    """posición del centro, escala (raíz del jacobiano) y giro (°) de una homografía en (cx, cy)."""
    def ap(x, y):
        p = Hp @ np.array([x, y, 1.0]); return p[:2] / p[2]
    c0 = ap(cx, cy); e = 1.0
    Jx = (ap(cx + e, cy) - ap(cx - e, cy)) / (2 * e); Jy = (ap(cx, cy + e) - ap(cx, cy - e)) / (2 * e)
    J = np.stack([Jx, Jy], 1)
    esc = math.sqrt(abs(np.linalg.det(J)))
    giro = math.degrees(math.atan2(J[1, 0] - J[0, 1], J[0, 0] + J[1, 1]))
    return c0, esc, giro


def esquinas(Hp, bb):
    x0, y0, x1, y1 = bb
    P = np.array([[x0, y0, 1], [x1, y0, 1], [x1, y1, 1], [x0, y1, 1]], np.float64).T
    q = Hp @ P
    return (q[:2] / q[2]).T


# ==================================================================================================== 3 · seguimiento sin estampado
def flujo_cuadro(L0, L1, mask0, Hguess, sigmas=(6, 3, 1.5)):
    """homografía cuadro k−1 → k sobre la luminancia de la espalda (mask0), con LK + ganancia/sesgo."""
    ys, xs = np.nonzero(mask0)
    sel = slice(None, None, 3)
    x0, x1_, y0, y1_ = xs.min(), xs.max(), ys.min(), ys.max()
    sub = L0[y0:y1_ + 1, x0:x1_ + 1]
    lk = LK(sub, paso=1)
    mk = mask0[y0:y1_ + 1, x0:x1_ + 1].ravel()
    keep = mk.copy(); keep[::1] &= True
    idx = np.nonzero(keep)[0][::3]
    lk.x, lk.y, lk.t = lk.x[idx], lk.y[idx], lk.t[idx]
    lk.xn, lk.yn = (lk.x - lk.cx) / lk.sc, (lk.y - lk.cy) / lk.sc
    # Hguess está en píxeles del cuadro (k−1 → k); pasarlo a coordenadas normalizadas del recorte
    Off = np.array([[1, 0, x0], [0, 1, y0], [0, 0, 1]], np.float64)
    Nrm = np.array([[1 / lk.sc, 0, -lk.cx / lk.sc], [0, 1 / lk.sc, -lk.cy / lk.sc], [0, 0, 1]])
    Hn0 = Hguess @ Off @ np.linalg.inv(Nrm); Hn0 = Hn0 / Hn0[2, 2]
    Hn, _ = lk.ajustar(L1, Hn0, sigmas=sigmas, iters=30)
    Hp = Hn @ Nrm @ np.linalg.inv(Off)
    return Hp / Hp[2, 2]


# ==================================================================================================== 3b · malla (no rígido)
class Malla:
    """desplazamiento suave sobre la homografía: grilla nx×ny en la plantilla con base bilineal, resuelto por
    Gauss-Newton con regularización de suavidad (laplaciano) y de tamaño. Sigue la curvatura de la espalda que una
    homografía no puede seguir."""
    def __init__(self, lk, w, h, nx=8, ny=4, lam=0.6):
        self.lk, self.w, self.h, self.nx, self.ny, self.lam = lk, w, h, nx, ny, lam
        self.Phi = self.base(lk.x, lk.y)
        n = nx * ny
        Lp = np.zeros((n, n))
        for j in range(ny):
            for i in range(nx):
                a = j * nx + i; vec = [(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= i + di < nx and 0 <= j + dj < ny]
                Lp[a, a] = len(vec)
                for (ii, jj) in vec:
                    Lp[a, jj * nx + ii] = -1
        self.Lp = Lp
        self.d = np.zeros(2 * n)

    def base(self, x, y):
        gx = np.clip(x / self.w * (self.nx - 1), 0, self.nx - 1 - 1e-6); gy = np.clip(y / self.h * (self.ny - 1), 0, self.ny - 1 - 1e-6)
        i = np.floor(gx).astype(int); j = np.floor(gy).astype(int); fx = gx - i; fy = gy - j
        P = np.zeros((len(x), self.nx * self.ny))
        r = np.arange(len(x))
        for (di, dj, wt) in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            P[r, (j + dj) * self.nx + (i + di)] += wt
        return P

    def desp(self, x, y, d=None):
        d = self.d if d is None else d
        P = self.base(x, y); n = self.nx * self.ny
        return P @ d[:n], P @ d[n:]

    def ajustar(self, I, Hn, sigmas=(2, 1), iters=15):
        lk = self.lk; n = self.nx * self.ny
        u0, v0, _ = lk.aplicar(Hn, lk.xn, lk.yn)
        R = np.zeros((2 * n, 2 * n)); R[:n, :n] = self.Lp.T @ self.Lp; R[n:, n:] = self.Lp.T @ self.Lp
        for sg in sigmas:
            Is = nd.gaussian_filter(I, sg); gy, gx = np.gradient(Is)
            for it in range(iters):
                du = self.Phi @ self.d[:n]; dv = self.Phi @ self.d[n:]
                u, v = u0 + du, v0 + dv
                ok = (u > 1) & (u < I.shape[1] - 2) & (v > 1) & (v < I.shape[0] - 2)
                uu, vv, tt, Ph = u[ok], v[ok], lk.t[ok], self.Phi[ok]
                Iv = nd.map_coordinates(Is, [vv, uu], order=1)
                Gx = nd.map_coordinates(gx, [vv, uu], order=1); Gy = nd.map_coordinates(gy, [vv, uu], order=1)
                r = Iv - tt
                s_r = max(1.4826 * np.median(np.abs(r)), 0.05); k = 1.5 * s_r
                wt = np.where(np.abs(r) <= k, 1.0, k / np.maximum(np.abs(r), 1e-9))
                J = np.concatenate([Ph * Gx[:, None], Ph * Gy[:, None]], 1)
                A = J.T @ (J * wt[:, None]); g = J.T @ (wt * r)
                esc = np.trace(A) / (2 * n)
                A2 = A + self.lam * esc * R + 1e-3 * esc * np.eye(2 * n)
                dd = -np.linalg.solve(A2, g + self.lam * esc * R @ self.d + 1e-3 * esc * self.d)
                self.d = self.d + dd
                if np.abs(dd).max() < 0.02:
                    break
        return self.d.copy()


def inversa(Hp_tpl, malla, d, xs, ys):
    """píxeles del cuadro → coordenadas de plantilla (homografía + malla), por punto fijo."""
    Hi = np.linalg.inv(Hp_tpl)
    def hinv(px, py):
        q = Hi @ np.stack([px, py, np.ones_like(px)]); return q[0] / q[2], q[1] / q[2]
    tx, ty = hinv(xs, ys)
    if malla is None or d is None:
        return tx, ty
    for _ in range(4):
        du, dv = malla.desp(tx, ty, d)
        tx, ty = hinv(xs - du, ys - dv)
    return tx, ty


def warp_alfa2(M, Hp_tpl, bb, malla=None, d=None):
    x0, y0, x1, y1 = bb
    ys, xs = np.mgrid[y0:y1, x0:x1]
    tx, ty = inversa(Hp_tpl, malla, d, xs.ravel().astype(np.float64), ys.ravel().astype(np.float64))
    u = tx / S0; v = ty / S0
    esc = descomponer(Hp_tpl, 200, 100)[1] * S0          # px de video por px de foto
    out = []
    for a in (M['aF'], M['aR']):
        aa = nd.gaussian_filter(a, 0.5 / max(esc, 1e-3))
        out.append(nd.map_coordinates(aa, [v, u], order=1, mode='constant').reshape(xs.shape))
    return out


def forma(aF, Pc, Bc_ext):
    """compara el Founders de estudio ubicado (aF > 0,5) con el real (P > 0,5) en la zona del Founders:
    centroide (px), ancho y alto (percentiles 2–98 %), IoU y distancia media de bordes (simétrica)."""
    zona = nd.binary_dilation(aF > 0.05, iterations=10) & Bc_ext
    tm = (aF > 0.5) & zona; rm = (Pc > 0.5) & zona
    if tm.sum() < 50 or rm.sum() < 50:
        return None
    def geo(m):
        ys, xs = np.nonzero(m)
        return np.array([xs.mean(), ys.mean()]), np.percentile(xs, 98) - np.percentile(xs, 2), np.percentile(ys, 98) - np.percentile(ys, 2)
    ct, wt_, ht = geo(tm); cr, wr, hr = geo(rm)
    et, er = bordes(tm), bordes(rm)
    dr = nd.distance_transform_edt(~er); dt = nd.distance_transform_edt(~et)
    cham = (dr[et].mean() + dt[er].mean()) / 2
    dentro2 = float((dt[rm] <= 2).mean())
    return dict(dx=round(float(ct[0] - cr[0]), 2), dy=round(float(ct[1] - cr[1]), 2),
                d_centro=round(float(np.hypot(*(ct - cr))), 2), ancho_pct=round(float(wt_ / wr - 1) * 100, 2),
                alto_pct=round(float(ht / hr - 1) * 100, 2), iou=round(float((tm & rm).sum() / (tm | rm).sum()), 3),
                bordes_px=round(float(cham), 2), real_a_2px=round(dentro2, 3))


def sombreado(cl, m, sigma=5.0):
    """sombreado de la tela por convolución normalizada (solo píxeles de tela lisa)."""
    w = nd.gaussian_filter(m.astype(np.float32), sigma)
    return np.stack([nd.gaussian_filter(cl[..., j] * m, sigma) for j in range(3)], -1) / np.maximum(w[..., None], 1e-4), w


def oclusion(ff, B):
    """lo que no es tela ni estampado dentro de la espalda: piel (cálida y saturada), pelo y lo de afuera de la espalda."""
    r, g, b = ff[..., 0], ff[..., 1], ff[..., 2]
    piel = (r > 70) & (r - b > 22) & (r - g > 6)
    return piel | ~B


def bordes(m):
    return m & ~nd.binary_erosion(m, iterations=1)


def sombreado_multi(cl, tela, bb, margen=160):
    """sombreado de la tela en un recorte alrededor del estampado: σ 5 donde hay tela cerca, si no σ 15 y σ 40
    (v1 usaba solo σ 5 y dejaba S = 0, manchas negras, en el centro de letras anchas)."""
    x0, y0 = max(0, bb[0] - margen), max(0, bb[1] - margen); x1, y1 = min(W, bb[2] + margen), min(H, bb[3] + margen)
    c = cl[y0:y1, x0:x1]; m = tela[y0:y1, x0:x1]
    S5, w5 = sombreado(c, m, 5.0); S15, w15 = sombreado(c, m, 15.0); S40, w40 = sombreado(c, m, 40.0)
    a5 = np.clip(w5 / 0.25, 0, 1)[..., None]; a15 = np.clip(w15 / 0.25, 0, 1)[..., None]
    S = np.zeros_like(cl); S[y0:y1, x0:x1] = a5 * S5 + (1 - a5) * (a15 * S15 + (1 - a15) * S40)
    return S


# ==================================================================================================== principal
ROI0 = (520, 880, 1080, 1480)      # ubicación inicial MANUAL del cuadro 0 (en producción la marca el editor)


def inicial(P, M, lk):
    """similitud inicial por la caja de los componentes grandes del Founders real (banda de la fila del mayor)."""
    mF = nd.binary_opening(P > 0.45, iterations=1)
    lab, n = nd.label(mF); s = nd.sum(mF, lab, range(1, n + 1))
    big = [i + 1 for i, v in enumerate(s) if v > 0.15 * s.max()]
    i0 = big[int(np.argmax([s[i - 1] for i in big]))]; y0 = nd.center_of_mass(mF, lab, i0)[0]
    sel = [i for i in big if abs(nd.center_of_mass(mF, lab, i)[0] - y0) < 60]
    bbv = _bb(mF & np.isin(lab, sel))
    bbF_t = tuple(v * S0 for v in M['bbF'])
    sc = math.sqrt((bbv[2] - bbv[0]) / (bbF_t[2] - bbF_t[0]) * (bbv[3] - bbv[1]) / (bbF_t[3] - bbF_t[1]))
    tx = (bbv[0] + bbv[2]) / 2 - sc * (bbF_t[0] + bbF_t[2]) / 2; ty = (bbv[1] + bbv[3]) / 2 - sc * (bbF_t[1] + bbF_t[3]) / 2
    Nrm = np.array([[1 / lk.sc, 0, -lk.cx / lk.sc], [0, 1 / lk.sc, -lk.cy / lk.sc], [0, 0, 1]])
    return np.array([[sc, 0, tx], [0, sc, ty], [0, 0, 1.0]]) @ np.linalg.inv(Nrm)


def encoder(salida, w, h, crf=14, extra=()):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
                             '-r', str(FPS), '-i', '-', '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
                             '-c:v', 'libx264', '-crf', str(crf), '-preset', 'medium', '-colorspace', 'bt709',
                             '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', *extra, str(salida)],
                            stdin=subprocess.PIPE)


def main():
    TC.mkdir(parents=True, exist_ok=True)
    M = modelo_estudio(); Tm = plantilla(M)
    F = cuadros_7887(); assert len(F) == NF, len(F)
    lk = LK(Tm); th, tw = Tm.shape
    malla = Malla(lk, tw, th)
    bbA = (0, 0, tw, th); ccx, ccy = tw / 2, th / 2
    filas = []; hojas = {}
    sal = encoder(TC / 'compuesto_7887.mp4', W, H)
    lado = encoder(TC / 'lado_a_lado_7887.mp4', 1080, 960, 20, ('-profile:v', 'high', '-level:v', '4.0', '-movflags', '+faststart'))
    roi = ROI0; Hn = None; Htr = Htr1 = None; vel = vel1 = np.eye(3)
    prev = None; rhoR_cal = rhoF_vid = None; ref0 = None; Hrel = np.eye(3)
    for k in range(NF):
        f = F[k]; ff = f.astype(np.float32)
        B, L, sat = espalda(f, roi)
        P, lvl = exceso(L, B)
        if k == 0:
            Hn = inicial(P, M, lk)
            Hn, _ = lk.ajustar(P, Hn, sigmas=(8, 4, 2), iters=40, modelo='sim', foto=False)
            Hn, _ = lk.ajustar(P, Hn, sigmas=(4, 2, 1), iters=40, modelo='s', foto=False)
        Hn, _ = lk.ajustar(P, Hn, sigmas=(2, 1), iters=30, foto=False)
        Hp = lk.a_pixeles(Hn); Hp = Hp / Hp[2, 2]
        d = malla.ajustar(P, Hn)
        # --- seguimiento cuadro a cuadro desde el registro del cuadro 0 (sin estampado = T2; con estampado = T1)
        Pm = nd.binary_dilation(P > 0.2, iterations=6)
        # T2 = encadenado k−1 → k (acumula deriva); T3 = cada cuadro contra el cuadro 0 (sin estampado, sin cadena)
        if k == 0:
            Htr = Hp.copy(); Htr1 = Hp.copy()
            m0r = (nd.binary_dilation(B, iterations=8) & ~nd.binary_erosion(B, iterations=40)) | B
            ref0 = (L.copy(), m0r & ~Pm, Hp.copy())
        else:
            Lp, Bp, Pp = prev
            m0 = (nd.binary_dilation(Bp, iterations=8) & ~nd.binary_erosion(Bp, iterations=40)) | Bp
            m_sin = m0 & ~Pp
            Hff = flujo_cuadro(Lp, L, m_sin, vel); vel = Hff
            Htr = Hff @ Htr; Htr /= Htr[2, 2]
            Hrel = flujo_cuadro(ref0[0], L, ref0[1], Hrel)
            Htr1 = Hrel @ ref0[2]; Htr1 /= Htr1[2, 2]
        prev = (L, B, Pm)
        # --- recuadro de trabajo
        q = esquinas(Hp, bbA)
        bb = (max(0, int(q[:, 0].min()) - 30), max(0, int(q[:, 1].min()) - 30), min(W, int(q[:, 0].max()) + 30), min(H, int(q[:, 1].max()) + 30))
        Bc = nd.binary_dilation(B, iterations=25)[bb[1]:bb[3], bb[0]:bb[2]]
        Pc = P[bb[1]:bb[3], bb[0]:bb[2]]
        medidas = {}
        for nom, (HH, mm, dd) in {'homografia': (Hp, None, None), 'homografia_malla': (Hp, malla, d),
                                  'seguimiento_sin_estampado': (Htr, None, None), 'seguimiento_ref0_sin_estampado': (Htr1, None, None)}.items():
            aF_, aR_ = warp_alfa2(M, HH, bb, mm, dd)
            medidas[nom] = forma(aF_, Pc, Bc)
            if nom == 'homografia_malla':
                aF, aR = aF_, aR_
        c_r, e_r, g_r = descomponer(Hp, ccx, ccy)
        c_t, e_t, g_t = descomponer(Htr, ccx, ccy)
        c_t3, e_t3, g_t3 = descomponer(Htr1, ccx, ccy)
        # --- compuesto con homografía + malla
        cl = lin(ff)
        # v2: se borra solo el «Founders Privée» real, dentro de la huella del de estudio ubicado (8 px), sobre la tela
        # o sobre gris poco saturado al borde de cuadro (no la roca). «ROCCÉ» se conserva real (ver resumen).
        foot = np.zeros((H, W), bool); foot[bb[1]:bb[3], bb[0]:bb[2]] = nd.binary_dilation(aF > 0.05, iterations=8)
        dentro = B | (nd.binary_dilation(B, iterations=25) & (sat < 0.22))
        occ = oclusion(ff, dentro)
        borrar = nd.binary_dilation((P > 0.12) & foot, iterations=3) & dentro & ~occ
        tela = B & ~borrar & ~occ & ~(P > 0.12)
        S = sombreado_multi(cl, tela, bb)
        tm_ = tela & (S.max(-1) > 0)
        res = (cl - S)[tm_]; sd = res.std(0) if len(res) > 100 else np.zeros(3)
        rng = np.random.default_rng(k)
        borr = cl.copy()
        borr[borrar] = np.clip(S[borrar] + rng.normal(0, 1, (borrar.sum(), 1)) * sd[None, :] * 0.8, 0, 1)
        Sc = S[bb[1]:bb[3], bb[0]:bb[2]]; clc = cl[bb[1]:bb[3], bb[0]:bb[2]]
        oc = occ[bb[1]:bb[3], bb[0]:bb[2]]
        if k == 0:
            mR_ = (aR > 0.7) & ~oc & (Pc > 0.15)
            rhoR_cal = np.median(clc[mR_] / np.maximum(Sc[mR_], 1e-4), 0) if mR_.sum() > 50 else M['rhoR']
            mF_ = (aF > 0.9) & (Pc > 0.5)
            rhoF_vid = np.median(clc[mF_] / np.maximum(Sc[mF_], 1e-4), 0)
        rho = 1 + aF[..., None] * (rhoF_vid[None, None] - 1)            # razón calibrada en c57 (luz de 7887)
        rho_est = 1 + aF[..., None] * (M['rhoF'][None, None] - 1)        # razón de la foto de estudio (para medir)
        blk = borr[bb[1]:bb[3], bb[0]:bb[2]] + (rho - 1) * Sc
        blk_est = np.where(oc[..., None], clc, borr[bb[1]:bb[3], bb[0]:bb[2]] + (rho_est - 1) * Sc)
        blk = np.where(oc[..., None], clc, blk)
        out = borr.copy(); out[bb[1]:bb[3], bb[0]:bb[2]] = blk
        comp = np.clip(srgb(out) + 0.5, 0, 255).astype(np.uint8)
        fuera = ~nd.binary_dilation(B, iterations=25); comp[fuera] = f[fuera]
        Lc = luma(comp.astype(np.float32))[bb[1]:bb[3], bb[0]:bb[2]]; Lr = L[bb[1]:bb[3], bb[0]:bb[2]]
        mFr = (Pc > 0.7) & (aF > 0.7)
        Le = luma(np.clip(srgb(blk_est) + 0.5, 0, 255))
        fot = dict(L_real=round(float(np.median(Lr[mFr])), 1), L_comp=round(float(np.median(Lc[mFr])), 1),
                   L_comp_razon_estudio=round(float(np.median(Le[mFr])), 1)) if mFr.sum() > 50 else None
        sal.stdin.write(comp.tobytes())
        izq = np.asarray(Image.fromarray(f).resize((540, 960), Image.LANCZOS)); der = np.asarray(Image.fromarray(comp).resize((540, 960), Image.LANCZOS))
        lado.stdin.write(np.concatenate([izq, der], 1).tobytes())
        fila = dict(cuadro=k, fuente_c=N0 + k,
                    registro=dict(centro=[round(float(v), 2) for v in c_r], escala_px_video_por_px_foto=round(e_r * S0, 4),
                                  giro=round(g_r, 2), malla_desp_max_px=round(float(np.abs(d).max()), 2)),
                    compuesto_vs_real=medidas, fotometria_founders=fot,
                    deriva_seguimiento_ref0=dict(centro_px=round(float(np.hypot(*(c_t3 - c_r))), 2),
                                                 escala_pct=round((e_t3 / e_r - 1) * 100, 2), giro=round(g_t3 - g_r, 2)),
                    deriva_seguimiento_sin_estampado=dict(centro_px=round(float(np.hypot(*(c_t - c_r))), 2),
                                                           escala_pct=round((e_t / e_r - 1) * 100, 2), giro=round(g_t - g_r, 2)),
                    pct_oclusion_en_estampado=round(float((oc & (aF + aR > 0.3)).sum() / max(1, (aF + aR > 0.3).sum()) * 100), 2),
                    nivel_exceso=round(lvl, 1))
        filas.append(fila)
        if k in (0, 13, 26, 39, 52):
            hojas[k] = (f.copy(), comp.copy(), q.copy(), bb, aF.copy(), Pc.copy())
        # recuadro del cuadro siguiente: el estampado ubicado + 140 px (la espalda entera queda adentro)
        roi = (q[:, 0].min() - 140, q[:, 1].min() - 160, q[:, 0].max() + 140, q[:, 1].max() + 360)
        hm = medidas['homografia_malla'] or {}; ho = medidas['homografia'] or {}; t2 = medidas['seguimiento_sin_estampado'] or {}
        print(k, 'H', ho.get('d_centro'), ho.get('bordes_px'), ho.get('iou'), '| H+malla', hm.get('d_centro'), hm.get('bordes_px'),
              hm.get('iou'), hm.get('ancho_pct'), '| T2', t2.get('d_centro'), t2.get('bordes_px'), '| T3', (medidas['seguimiento_ref0_sin_estampado'] or {}).get('d_centro'),
              '| L', fot, flush=True)
    sal.stdin.close(); sal.wait(); lado.stdin.close(); lado.wait()
    resumen = resumir(filas, M, rhoR_cal, rhoF_vid)
    guardar_json(dict(metodo=__doc__, resumen=resumen, por_cuadro=filas), TC / 'medidas.json')
    hoja(hojas, filas)
    print(json.dumps(resumen, ensure_ascii=False, indent=1))


def resumir(filas, M, rhoR_cal, rhoF_vid):
    def st(v):
        v = [x for x in v if x is not None]
        if not v:
            return None
        return dict(mediana=round(float(np.median(v)), 3), p90=round(float(np.percentile(v, 90)), 3),
                    max=round(float(np.max(v)), 3), min=round(float(np.min(v)), 3), n=len(v))
    out = dict(cuadros=len(filas))
    for nom in ('homografia', 'homografia_malla', 'seguimiento_sin_estampado', 'seguimiento_ref0_sin_estampado'):
        g = lambda key, ab=False: st([(abs(f['compuesto_vs_real'][nom][key]) if ab else f['compuesto_vs_real'][nom][key])
                                       for f in filas if f['compuesto_vs_real'][nom]])
        out[nom] = dict(d_centro_px=g('d_centro'), ancho_pct_abs=g('ancho_pct', True), alto_pct_abs=g('alto_pct', True),
                        iou=g('iou'), bordes_px=g('bordes_px'), real_a_2px=g('real_a_2px'))
    cen = np.array([f['registro']['centro'] for f in filas]); esc = np.array([f['registro']['escala_px_video_por_px_foto'] for f in filas])
    out['movimiento_del_estampado_real'] = dict(desplazamiento_px=[round(float(v), 1) for v in cen[-1] - cen[0]],
                                                escala_ini_fin=[round(float(esc[0]), 4), round(float(esc[-1]), 4)],
                                                cambio_escala_pct=round(float(esc[-1] / esc[0] - 1) * 100, 1))
    out['deriva_seguimiento_ref0'] = dict(centro_px=st([f['deriva_seguimiento_ref0']['centro_px'] for f in filas]),
                                          escala_pct_abs=st([abs(f['deriva_seguimiento_ref0']['escala_pct']) for f in filas]))
    out['deriva_seguimiento_sin_estampado'] = dict(centro_px=st([f['deriva_seguimiento_sin_estampado']['centro_px'] for f in filas]),
                                                   escala_pct_abs=st([abs(f['deriva_seguimiento_sin_estampado']['escala_pct']) for f in filas]))
    out['fotometria_founders'] = dict(L_real=st([f['fotometria_founders']['L_real'] for f in filas if f['fotometria_founders']]),
                                      L_comp=st([f['fotometria_founders']['L_comp'] for f in filas if f['fotometria_founders']]),
                                      L_comp_razon_estudio=st([f['fotometria_founders']['L_comp_razon_estudio'] for f in filas if f['fotometria_founders']]))
    out['rocce'] = ('se conserva el «ROCCÉ» real: en la foto de estudio el tono sobre tono tiene un exceso de luz de '
                    f"{M['exceso_R_med']:.1f} niveles (Founders {M['exceso_F_med']:.1f}) y su alfa sale incompleta; "
                    'con esa alfa el ROCCÉ compuesto se rompía (v1). Hace falta otra fuente (archivo de arte o foto con luz rasante).')
    out['estudio'] = dict(rhoF=[round(float(v), 2) for v in M['rhoF']], rhoR=[round(float(v), 3) for v in M['rhoR']],
                          exceso_L_founders=round(M['exceso_F_med'], 1), exceso_L_rocce=round(M['exceso_R_med'], 1), tela_L=round(M['tela_L_med'], 1))
    out['video_7887_c57'] = dict(rhoF=[round(float(v), 2) for v in rhoF_vid], rhoR_calibrado=[round(float(v), 3) for v in rhoR_cal])
    return out


def hoja(hojas, filas):
    """hoja 1:1 por cuadro: original | compuesto | bordes (rojo = real, cian = estudio ubicado, blanco = coinciden)."""
    fnt = ImageFont.truetype(FONT, 22)
    filas_img = []
    for k, (f, comp, q, bb, aF, Pc) in hojas.items():
        x0, y0, x1, y1 = bb[0], bb[1], bb[2], min(H, bb[3] + 120)
        a = f[y0:y1, x0:x1]; b = comp[y0:y1, x0:x1]
        ov = (a.astype(np.float32) * 0.4).astype(np.uint8)
        hh = bb[3] - bb[1]
        er = bordes(Pc > 0.5); et = bordes(aF > 0.5)
        sub = ov[:hh]
        sub[er] = (255, 60, 60); sub[et] = (60, 230, 255); sub[er & et] = (255, 255, 255)
        m = filas[k]['compuesto_vs_real']['homografia_malla'] or {}
        tiles = []
        for im, rot in ((a, f'original IMG_7887 c{N0 + k}'), (b, 'compuesto (estampado de estudio)'),
                        (ov, f"rojo real · cian estudio · bordes {m.get('bordes_px')} px · centro {m.get('d_centro')} px")):
            t = Image.fromarray(np.ascontiguousarray(im)); dr = ImageDraw.Draw(t)
            dr.rectangle([0, 0, t.width, 30], fill=(0, 0, 0)); dr.text((6, 3), rot, font=fnt, fill=(255, 255, 0))
            tiles.append(t)
        wsum = sum(t.width for t in tiles) + 20; hmax = max(t.height for t in tiles)
        row = Image.new('RGB', (wsum, hmax), (25, 25, 25)); x = 0
        for t in tiles:
            row.paste(t, (x, 0)); x += t.width + 10
        filas_img.append(row)
    ww = max(r.width for r in filas_img); hh = sum(r.height + 10 for r in filas_img)
    out = Image.new('RGB', (ww, hh), (25, 25, 25)); y = 0
    for r in filas_img:
        out.paste(r, (0, y)); y += r.height + 10
    out.save(TC / 'hoja_lado_a_lado_1a1.jpg', quality=90)
    # gráfico por cuadro
    g = Image.new('RGB', (1080, 560), (18, 18, 22)); d = ImageDraw.Draw(g); fnt2 = ImageFont.truetype(FONT, 19)
    d.text((20, 10), 'Compuesto vs estampado real · IMG_7887 c57–c109 (px a 1080×1920)', font=fnt2, fill=(230, 230, 230))
    get = lambda nom, key: [((f['compuesto_vs_real'][nom] or {}).get(key) or 0) for f in filas]
    ser = [('H+malla bordes px', get('homografia_malla', 'bordes_px'), (140, 255, 140)),
           ('H sola bordes px', get('homografia', 'bordes_px'), (90, 200, 255)),
           ('seguim. encadenado centro px', get('seguimiento_sin_estampado', 'd_centro'), (255, 120, 90)),
           ('seguim. contra c57 centro px', get('seguimiento_ref0_sin_estampado', 'd_centro'), (220, 140, 255)),
           ('H+malla centro px', get('homografia_malla', 'd_centro'), (255, 220, 80))]
    x0, y0, x1, y1 = 60, 50, 1050, 450; ymax = 20.0
    d.rectangle([x0, y0, x1, y1], outline=(80, 80, 80))
    for v in (5, 10, 15):
        yy = y1 - (y1 - y0) * v / ymax; d.line([(x0, yy), (x1, yy)], fill=(50, 50, 50)); d.text((20, yy - 10), str(v), font=fnt2, fill=(150, 150, 150))
    for i, (nom, v, col) in enumerate(ser):
        pts = [(x0 + (x1 - x0) * k / (len(v) - 1), y1 - (y1 - y0) * min(1, vv / ymax)) for k, vv in enumerate(v)]
        d.line(pts, fill=col, width=3)
        d.text((x0 + (i % 2) * 480, y1 + 18 + (i // 2) * 28), nom, font=fnt2, fill=col)
    g.save(TC / 'grafico_compuesto.png')


if __name__ == '__main__':
    main()
