# Reemplaza el estampado que dibujó la IA por el arte real (arte_estampado.py) en una toma, con seguimiento
# por homografía (Lucas-Kanade sobre la tela y las letras, RANSAC, suavizado temporal).
# Pasos por cuadro: (1) borrar las letras de la IA (máscara de tinta del cuadro 0 seguida + inpaint de la tela),
# (2) multiplicar el arte real sobre la tela limpia (hereda luz y pliegues), (3) dedos vóxel por delante
# (tono naranja), (4) desenfoque y grano parecidos a la toma.
# Variables: DEDOS=0 (sin manos delante), LIMPIAR=0 (no hay letras que borrar), OPAC=0.85 (tinta más liviana).
# Uso: python estampado_toma.py TOMA.mp4 ARTE.png SALIDA_DIR ROI(x0,y0,x1,y1) CENTRO(x,y) ANCHO [desde_cuadro] [hasta_cuadro]
import sys, os, cv2, numpy as np
toma, arte_p, out = sys.argv[1], sys.argv[2], sys.argv[3]
x0, y0, x1, y1 = map(int, sys.argv[4].split(",")); cx, cy = map(float, sys.argv[5].split(",")); ancho = float(sys.argv[6])
desde = int(sys.argv[7]) if len(sys.argv) > 7 else 0; hasta = int(sys.argv[8]) if len(sys.argv) > 8 else 10**9
os.makedirs(out, exist_ok=True)
LIMPIAR = os.environ.get("LIMPIAR", "1") == "1"   # 0: la prenda no trae letras de la IA (solo se suma el arte)
DEDOS = os.environ.get("DEDOS", "1") == "1"     # 0: no hay manos delante (y la prenda tiene tono cálido)
OPAC = float(os.environ.get("OPAC", "1"))          # <1: tinta menos cargada (prenda chica, luz dura)
cap = cv2.VideoCapture(toma); fr = []
while True:
    ok, f = cap.read()
    if not ok: break
    fr.append(f)
fr = fr[desde:min(hasta, len(fr))]
H, W = fr[0].shape[:2]

def dedos(f):  # piel vóxel naranja (manos), siempre por delante del estampado
    if not DEDOS: return np.zeros(f.shape[:2], np.float32)
    f = f.astype(np.float32) / 255
    m = ((f[..., 2] - f[..., 0]) > 0.16) & (f[..., 2] > 0.35)
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(cv2.dilate(m, np.ones((3, 3), np.uint8)).astype(np.float32), (0, 0), 1.0)

def tinta_ia(f):  # letras de la IA: más oscuras que la tela vecina o celestes
    r = f.astype(np.float32) / 255
    bg = cv2.GaussianBlur(cv2.dilate(r, np.ones((25, 25), np.uint8)), (0, 0), 8)
    m = ((bg.mean(2) - r.mean(2)) > 0.10) | ((r[..., 0] - r[..., 2]) > 0.08)
    roi = np.zeros_like(m); roi[y0:y1, x0:x1] = True
    m = m & roi & (dedos(f) < 0.3)
    return cv2.dilate(m.astype(np.uint8), np.ones((7, 7), np.uint8))

# seguimiento: cuadro 0 -> cuadro t
g0 = cv2.cvtColor(fr[0], cv2.COLOR_BGR2GRAY)
mroi = np.zeros_like(g0); mroi[y0 - 60:y1 + 60, x0 - 60:x1 + 60] = 255
mroi[dedos(fr[0]) > 0.2] = 0
p0 = cv2.goodFeaturesToTrack(g0, 400, 0.005, 6, mask=mroi)
Hs = []
for f in fr:
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g, p0, None, winSize=(31, 31), maxLevel=3)
    ok = st.ravel() == 1
    Hm, inl = cv2.findHomography(p0[ok], p1[ok], cv2.RANSAC, 1.5)
    Hs.append(Hm / Hm[2, 2])
Hs = np.array(Hs)
k = 5; Hsm = np.array([Hs[max(0, i - k):i + k + 1].mean(0) for i in range(len(Hs))])  # suaviza el temblor del seguimiento

# arte real ubicado sobre el cuadro 0
arte = cv2.imread(arte_p, cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
esc = ancho / arte.shape[1]
arte_s = cv2.resize(arte, None, fx=esc, fy=esc, interpolation=cv2.INTER_AREA)
ah, aw = arte_s.shape[:2]
T = np.array([[1, 0, cx - aw / 2], [0, 1, cy - ah / 2], [0, 0, 1]], np.float64)
m0 = tinta_ia(fr[0]) if LIMPIAR else None
rng = np.random.default_rng(7)
for i, f in enumerate(fr):
    Hm = Hsm[i]
    if LIMPIAR:
        m = cv2.warpPerspective(m0, Hm, (W, H), flags=cv2.INTER_NEAREST) | tinta_ia(f)
        limpio = cv2.inpaint(f, m, 6, cv2.INPAINT_TELEA).astype(np.float32) / 255
    else:
        limpio = f.astype(np.float32) / 255
    A = cv2.warpPerspective(arte_s, Hm @ T, (W, H), flags=cv2.INTER_LINEAR, borderValue=(1, 1, 1, 0))
    A = cv2.GaussianBlur(A, (0, 0), 0.55)
    a = A[..., 3:4] * OPAC; alb = A[..., :3]
    o = limpio * (1 - a + a * alb)
    d = dedos(f)[..., None]
    o = o * (1 - d) + (f.astype(np.float32) / 255) * d
    grano = rng.normal(0, 0.008, o.shape[:2])[..., None] * a
    o = np.clip(o + grano, 0, 1)
    cv2.imwrite(f"{out}/{i + 1:04d}.png", (o * 255 + .5).astype(np.uint8))
print("cuadros", len(fr), "escala arte", round(esc, 4))
