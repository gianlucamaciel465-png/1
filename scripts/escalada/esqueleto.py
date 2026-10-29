# Esqueleto del escalador (figura de palitos de Neuron Visuals) por cuadro, para vestirlo con la remera v02.
# El personaje tiene proporciones fijas (medidas en cuadros claros): grosor de trazo t = 0,82·r (r = radio de la
# cabeza), torso cuello→pelvis = 5,1·r, brazo (hombro→codo) = 2,2·r, hombro a 0,6·r bajo el cuello.
# Por cuadro solo se buscan ángulos, partiendo de la cabeza (pose_heroe: centro y radio, muy confiable):
#   torso  = ángulo cuyo segmento de largo fijo, pegado al borde de la cabeza, cae más adentro del blanco;
#   brazos = ángulo del brazo cercano (blanco) y del lejano (gris) desde el hombro, sin contar cabeza ni torso;
# con preferencia por el ángulo del cuadro anterior (continuidad) y suavizado dentro del plano.
# Salida JSON por cuadro: H, r, N (cuello), P (pelvis), S (hombro), tor, cer, lej (ángulos, rad), conf.
# Uso: python esqueleto.py SEQ_DIR POSE_V01_DIR SALIDA.json
import sys, json, math
import numpy as np, cv2

seq, pdir, out = sys.argv[1:4]
PLANOS = {"A": (1, 72), "C": (124, 186), "D": (187, 222), "E": (223, 302), "F": (303, 372)}
LT, LS, LU = 5.1, 0.6, 2.2
# Claves manuales (grados; 0 = derecha, 90 = abajo), revisadas sobre los cuadros: donde el brazo cercano doblado
# pasa por delante del torso (forma de V), el ajuste automático se va hacia el brazo. Entre claves, interpolación.
MANUAL = {"tor": [(139, 157, 85.0, 86.0), (211, 222, 88.0, 93.0), (223, 234, 94.0, 91.0), (315, 372, 81.0, 81.0, -0.25)],
          "cer": [(216, 222, 74.0, 76.0), (223, 232, 74.0, 74.0), (315, 372, 68.0, 68.0)]}
# (tor C 139–157: el muslo doblado tira del ajuste; D/E 211–234: brazo en V delante; F: de perfil, el brazo cuelga
#  delante y tapa casi todo el torso — torso medido a mano sobre el cuadro 330, con su corrimiento lateral en r)

def manual(nombre, f, desplazamiento=False):
    for k in MANUAL[nombre]:
        a, b, va, vb = k[:4]
        if a <= f <= b:
            if desplazamiento: return k[4] if len(k) > 4 else 0.0
            return math.radians(va + (vb - va) * (f - a) / max(1, b - a))
    return None

def mascaras(im, r):
    L = im.mean(2); sat = im.max(2) - im.min(2)
    k = max(3, int(round(0.35 * r)) | 1); ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    bl = cv2.morphologyEx(((L > 190) & (sat < 45)).astype(np.uint8), cv2.MORPH_OPEN, ker)
    gr = cv2.morphologyEx(((L > 95) & (L <= 190) & (sat < 45)).astype(np.uint8), cv2.MORPH_OPEN, ker)
    # "núcleo": más de 0,2·r adentro del trazo (el centro de un trazo de 0,82·r está a 0,41·r del borde)
    dbl = cv2.distanceTransform(bl, cv2.DIST_L2, 5); dgr = cv2.distanceTransform(gr | bl, cv2.DIST_L2, 5)
    return (dbl > 0.2 * r).astype(np.float32), ((dgr > 0.2 * r) & (gr > 0)).astype(np.float32)

def muestras(m, pts):
    x = np.clip(np.round(pts[:, 0]).astype(int), 0, m.shape[1] - 1)
    y = np.clip(np.round(pts[:, 1]).astype(int), 0, m.shape[0] - 1)
    dentro = (pts[:, 0] >= 0) & (pts[:, 0] < m.shape[1]) & (pts[:, 1] >= 0) & (pts[:, 1] < m.shape[0])
    return m[y, x] * dentro

def u(a): return np.array([math.cos(a), math.sin(a)])

def ajustar_torso(core, H, r, prev):
    rango = np.radians(np.arange(-28, 28.1, 1.0)) + prev if prev is not None else np.radians(np.arange(0, 360, 2.0))
    t = np.linspace(0.08, 0.72, 26)[:, None]          # parte alta: cerca de la pelvis se confunde con el muslo
    mejor = None
    for a in rango:
        d = u(a); N = H + 1.0 * r * d; P = N + LT * r * d
        pts = N + (P - N) * t
        # también los costados del trazo (±0,2·r) para que no se pegue a un borde
        nrm = np.array([-d[1], d[0]])
        c = (muestras(core, pts).mean() * 2 + muestras(core, pts + 0.2 * r * nrm).mean()
             + muestras(core, pts - 0.2 * r * nrm).mean()) / 4
        pen = 0.0 if prev is None else 0.0025 * abs(math.degrees((a - prev + math.pi) % (2 * math.pi) - math.pi))
        sc = c - pen
        if mejor is None or sc > mejor[0]: mejor = (sc, a, c)
    return mejor[1], mejor[2]

def ajustar_brazo(core, H, r, N, P, S, prev, excl_torso=True):
    rango = np.radians(np.arange(-40, 40.1, 2.0)) + prev if prev is not None else np.radians(np.arange(0, 360, 3.0))
    t = np.linspace(0.45, 1.0, 16)[:, None]
    mejor = None
    seg = P - N; Ls = float(np.linalg.norm(seg)); us = seg / Ls
    for a in rango:
        d = u(a); pts = S + LU * r * d * t
        v = pts - N; s = np.clip(v @ us, 0, Ls); dist_t = np.linalg.norm(v - s[:, None] * us, axis=1)
        dist_h = np.linalg.norm(pts - H, axis=1)
        valido = (dist_h > 1.15 * r) & ((dist_t > 0.6 * r) if excl_torso else True)
        m = muestras(core, pts)
        c = m[valido].mean() if valido.sum() >= 5 else 0.25
        pen = 0.0 if prev is None else 0.004 * abs(math.degrees((a - prev + math.pi) % (2 * math.pi) - math.pi))
        sc = c - pen
        if mejor is None or sc > mejor[0]: mejor = (sc, a, c)
    return mejor[1], mejor[2]

def refinar(bl, H, r, a):
    """Centra el eje del torso en el trazo real: en cortes transversales limpios (un solo trazo de ancho ≈ t)
    mide el centro del blanco y ajusta desplazamiento lateral c y giro δ (o(y) = c + y·δ)."""
    d = u(a); n = np.array([-d[1], d[0]]); N = H + r * d; t = 0.82 * r
    ys, os_ = [], []
    off = np.arange(-1.1 * r, 1.1 * r + 0.5, 1.0)
    for y in np.linspace(1.0, 4.6, 28):
        c = N + d * y * r
        pts = c[None, :] + off[:, None] * n[None, :]
        v = muestras(bl, pts) > 0
        if not v.any(): continue
        # tramo blanco más cercano al eje
        idx = np.flatnonzero(v); grupos = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
        g = min(grupos, key=lambda g_: abs(off[g_].mean()))
        ancho = off[g[-1]] - off[g[0]] + 1
        if 0.6 * t <= ancho <= 1.3 * t + 10 and abs(off[g].mean()) < 0.7 * r and g[0] > 0 and g[-1] < len(off) - 1:
            ys.append(y * r); os_.append(off[g].mean())
    if len(ys) < 8: return a, 0.0, len(ys)
    A = np.stack([np.ones(len(ys)), np.array(ys)], 1); c0, k = np.linalg.lstsq(A, np.array(os_), rcond=None)[0]
    dl = float(np.clip(math.atan(k), -math.radians(16), math.radians(16)))
    return a + dl, float(np.clip(c0, -0.6 * r, 0.6 * r)), len(ys)

def suavizar(angs, sig=0.9):
    a = np.unwrap(np.array(angs))
    if len(a) < 3: return a
    from scipy.ndimage import gaussian_filter1d, median_filter
    return gaussian_filter1d(median_filter(a, 3, mode="nearest"), sig, mode="nearest")

res = {}
for nombre, (f0, f1) in PLANOS.items():
    pose = json.load(open(f"{pdir}/p2_{nombre}.json"))
    fs = [f for f in range(f0, f1 + 1) if str(f) in pose]
    tor, cer, lej, conf, Hs, rs, ofl = [], [], [], [], [], [], []
    pt = pc = pl = None
    r_pl = float(np.median([pose[str(f)]["r"] for f in fs]))
    for f in fs:
        p = pose[str(f)]; H = np.array(p["H"], float); r = r_pl
        im = cv2.imread(f"{seq}/{f:04d}.png")[..., ::-1].astype(np.float32)
        cb, cg = mascaras(im, r)
        a_t, c_t = ajustar_torso(cb, H, r, pt)
        if manual("tor", f) is not None: a_t = manual("tor", f); ofs = manual("tor", f, True) * r
        else:
            L_ = im.mean(2); sat_ = im.max(2) - im.min(2)
            a_t, ofs, _ = refinar(((L_ > 200) & (sat_ < 45)).astype(np.float32), H, r, a_t)
        pt = a_t; ofl.append(ofs)
        d = u(a_t); N = H + r * d + ofs * np.array([-d[1], d[0]]); P = N + LT * r * d; S = N + LS * r * d
        a_c, c_c = ajustar_brazo(cb, H, r, N, P, S, pc)
        if manual("cer", f) is not None: a_c = manual("cer", f)
        pc = a_c
        a_l, c_l = ajustar_brazo(cg, H, r, N, P, S, pl); pl = a_l
        tor.append(a_t); cer.append(a_c); lej.append(a_l); conf.append((c_t, c_c, c_l)); Hs.append(H); rs.append(r)
    tor, cer, lej = suavizar(tor), suavizar(cer, 0.7), suavizar(lej, 0.7)
    from scipy.ndimage import gaussian_filter1d as _g
    ofl = _g(np.array(ofl, float), 1.0, mode="nearest")
    # brazo lejano: visible solo si el gris lo sostiene; si no, queda detrás del torso (ángulo del torso)
    from scipy.ndimage import gaussian_filter1d
    vis = gaussian_filter1d(np.clip((np.array([c[2] for c in conf]) - 0.3) / 0.15, 0, 1), 1.5, mode="nearest")
    dl = (lej - tor + np.pi) % (2 * np.pi) - np.pi
    lej = tor + dl * vis
    for i, f in enumerate(fs):
        H, r = Hs[i], rs[i]; d = u(tor[i]); N = H + r * d + ofl[i] * np.array([-d[1], d[0]])
        P = N + LT * r * d; S = N + LS * r * d
        res[f] = dict(H=H.tolist(), r=r, N=N.tolist(), P=P.tolist(), S=S.tolist(), tor=float(tor[i]), off=float(ofl[i]),
                      cer=float(cer[i]), lej=float(lej[i]), vis_lej=round(float(vis[i]), 2),
                      conf=[round(float(c), 2) for c in conf[i]], plano=nombre)
    cf = np.array(conf)
    print(nombre, len(fs), "cuadros; cobertura media torso %.2f brazo %.2f lejano %.2f" % tuple(cf.mean(0)),
          "mín torso %.2f" % cf[:, 0].min())
json.dump(res, open(out, "w"))
