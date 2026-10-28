# Pose del escalador (figura blanca de Neuron Visuals) por cuadro, para vestirlo con la remera.
# Parte de la cabeza de pose_heroe.py (punto más grueso del blanco, muy confiable) y agrega continuidad en el tiempo:
#   torso  = segmento de largo fijo por plano que sale del borde de la cabeza y mejor cae dentro del blanco, buscando
#            cerca del ángulo del cuadro anterior (cambia despacio, también cuando pasa por encima del borde);
#   brazos = dirección con más masa blanca (cercano) o gris (lejano) en un anillo alrededor del hombro, sin contar
#            cabeza ni torso, también con preferencia por el ángulo anterior.
# Después suaviza cada serie dentro del plano. Salida: JSON por cuadro (1-based) con H, r, N, P, brazos.
# Uso (Python con OpenCV): python pose_escalador.py SEQ_DIR POSE_HEROE.json SALIDA.json f0 f1   (f 1-based)
import sys, json, math
import numpy as np, cv2
from PIL import Image

seq, pin, out, f0, f1 = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
raw = json.load(open(pin))           # claves 0-based (pose_heroe)

def masks(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    L = (r + g + b) / 3; sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    blanco = (L > 200) & (sat < 40)
    gris = (L > 105) & (L <= 200) & (sat < 40)
    # solo trazos gruesos (las letras de la pared y el mástil son finos)
    k = np.ones((5, 5), np.uint8)
    blanco = cv2.morphologyEx(blanco.astype(np.uint8), cv2.MORPH_OPEN, k).astype(bool)
    gris = cv2.morphologyEx(gris.astype(np.uint8), cv2.MORPH_OPEN, k).astype(bool)
    return blanco, gris

def cobertura(m, p, q, n=40):
    t = np.linspace(0, 1, n)[:, None]; pts = p[None, :] + (q - p)[None, :] * t
    x = np.clip(np.round(pts[:, 0]).astype(int), 0, m.shape[1] - 1); y = np.clip(np.round(pts[:, 1]).astype(int), 0, m.shape[0] - 1)
    return m[y, x].mean()

fs = list(range(f0, f1 + 1))
H = np.array([raw[str(f - 1)]["H"] if raw.get(str(f - 1)) else [np.nan, np.nan] for f in fs], float)
r = np.array([raw[str(f - 1)]["r"] if raw.get(str(f - 1)) else np.nan for f in fs], float)
Ls = np.array([raw[str(f - 1)]["L"] if raw.get(str(f - 1)) else np.nan for f in fs], float)
rr = float(np.nanmedian(r)); Lt = float(np.nanpercentile(Ls, 70))
# ángulo inicial del torso: mediana de los primeros cuadros de pose_heroe
ang0 = []
for f in fs[:6]:
    p = raw.get(str(f - 1))
    if p: d = np.array(p["P"]) - np.array(p["N"]); ang0.append(math.atan2(d[1], d[0]))
th = float(np.median(ang0)) if ang0 else math.pi / 2
res = {}
a_cer, a_lej = None, None
for i, f in enumerate(fs):
    a = np.asarray(Image.open(f"{seq}/{f:04d}.png").convert("RGB"))
    bl, gr = masks(a)
    Hc = H[i]
    if not np.all(np.isfinite(Hc)): continue
    inner = cv2.erode(bl.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    mejor = (-9, th)
    for d in np.radians(np.arange(-30, 30.1, 1.5)):
        t_ = th + d; u = np.array([math.cos(t_), math.sin(t_)])
        N = Hc + u * (rr + 0.25 * rr); P = Hc + u * (rr + 0.25 * rr + Lt)
        c = cobertura(inner, N, P) - 0.0025 * abs(math.degrees(d))
        if c > mejor[0]: mejor = (c, t_)
    th = mejor[1]; u = np.array([math.cos(th), math.sin(th)]); nrm = np.array([-u[1], u[0]])
    N = Hc + u * rr * 0.95; P = N + u * (Lt + 0.3 * rr)
    S = N + u * 0.14 * Lt
    # brazos: masa por dirección en un anillo alrededor del hombro
    yy, xx = np.mgrid[int(S[1] - 2.6 * rr):int(S[1] + 2.6 * rr), int(S[0] - 2.6 * rr):int(S[0] + 2.6 * rr)]
    ok = (yy >= 0) & (yy < a.shape[0]) & (xx >= 0) & (xx < a.shape[1])
    yy, xx = yy[ok], xx[ok]
    dx, dy = xx - S[0], yy - S[1]; rad = np.hypot(dx, dy)
    v2x, v2y = xx - N[0], yy - N[1]; tt = np.clip((v2x * u[0] + v2y * u[1]) / Lt, 0, 1)
    dax = np.hypot(v2x - tt * Lt * u[0], v2y - tt * Lt * u[1])
    sel = (rad > 0.9 * rr) & (rad < 2.3 * rr) & (np.hypot(xx - Hc[0], yy - Hc[1]) > 1.12 * rr) & (dax > 0.55 * rr)
    ang = np.arctan2(dy, dx)
    brazos = {}
    for nombre, m, prev in (("cerca", bl, a_cer), ("lejos", gr, a_lej)):
        w_ = m[yy, xx] & sel
        if w_.sum() < 15: brazos[nombre] = None; continue
        bins = np.radians(np.arange(-180, 180, 5))
        hist = np.array([np.sum(w_ & (np.abs(np.angle(np.exp(1j * (ang - b)))) < math.radians(12))) for b in bins], float)
        if prev is not None:
            hist = hist * (1.0 - 0.45 * np.clip(np.abs(np.angle(np.exp(1j * (bins - prev)))) / math.pi, 0, 1))
        k = int(np.argmax(hist)); aa = float(bins[k])
        # refinar: media circular de los píxeles de ese lóbulo
        lob = w_ & (np.abs(np.angle(np.exp(1j * (ang - aa)))) < math.radians(18))
        aa = float(np.angle(np.mean(np.exp(1j * ang[lob])))) if lob.sum() > 5 else aa
        brazos[nombre] = aa
    a_cer = brazos["cerca"] if brazos["cerca"] is not None else a_cer
    a_lej = brazos["lejos"] if brazos["lejos"] is not None else a_lej
    res[f] = {"H": Hc.tolist(), "r": rr, "th": th, "Lt": Lt, "cerca": brazos["cerca"], "lejos": brazos["lejos"]}

# cadera: a 0,80 del largo del torso medido (≈ 3,5 radios de cabeza bajo el cuello, medido en la figura parada
# del cuadro 301: la mano del brazo colgando llega a ~6 radios y la rodilla está más abajo). La detección por
# ensanchamiento se confundía con los brazos pegados al cuerpo.
CADERA = 0.80 * Lt

# suavizado (media móvil de 5 en ángulos desenvueltos y en la cabeza)
def suav(v, k=5):
    v = np.asarray(v, float); x = np.arange(len(v)); m = np.isfinite(v)
    if m.sum() < 2: return v
    v = np.interp(x, x[m], v[m]); pad = np.pad(v, (k // 2, k // 2), mode="edge"); return np.convolve(pad, np.ones(k) / k, "valid")
ks = sorted(res)
Hs = np.array([res[f]["H"] for f in ks]); th_ = np.unwrap([res[f]["th"] for f in ks])
ac = [res[f]["cerca"] if res[f]["cerca"] is not None else np.nan for f in ks]
al = [res[f]["lejos"] if res[f]["lejos"] is not None else np.nan for f in ks]
def unw(v):
    v = np.array(v, float); m = np.isfinite(v); v2 = v.copy(); v2[m] = np.unwrap(v[m]); return v2
Hx, Hy, th_s, ac_s, al_s = suav(Hs[:, 0], 3), suav(Hs[:, 1], 3), suav(th_, 5), suav(unw(ac), 5), suav(unw(al), 5)
fin = {}
for i, f in enumerate(ks):
    u = np.array([math.cos(th_s[i]), math.sin(th_s[i])]); Hc = np.array([Hx[i], Hy[i]])
    N = Hc + u * rr * 0.95; P = N + u * CADERA
    fin[f] = {"H": Hc.tolist(), "r": rr, "N": N.tolist(), "P": P.tolist(), "S": (N + u * 0.14 * Lt).tolist(),
              "cerca": float(ac_s[i]), "lejos": float(al_s[i])}
json.dump(fin, open(out, "w"), indent=0)
print("pose:", len(fin), "cuadros; r", round(rr, 1), "torso", round(Lt, 1), "cadera", round(CADERA, 1))
