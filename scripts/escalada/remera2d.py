# Remera negra de Roccé como prenda del personaje (v02): se arma cada cuadro sobre el esqueleto (esqueleto.py),
# en el lenguaje de la animación (formas planas, contorno, brillo suave), en vez de una caja pegada.
#   - cuerpo: cuello redondo, hombros caídos, costados apenas entallados y ruedo con curva, a lo largo del torso;
#     ancho y largo fijos en radios de cabeza (el personaje no cambia de proporciones);
#   - mangas: tubo sobre el brazo desde el hombro, con ruedo acanalado; la cercana delante del cuerpo, la lejana
#     detrás (solo se ve lo que sale del cuerpo) y se esconde si el brazo lejano no se ve;
#   - capas: brazo lejano → manga lejana → cuerpo → brazo y pierna cercanos (píxeles originales) → manga cercana →
#     cabeza. El brazo que pasa por delante del torso con contorno (parado, agachado) queda entero delante;
#   - estampado REAL de la espalda (Founders Privée y ROCCÉ tono sobre tono, recortados de la foto, sin redibujar)
#     en plano, pegado al cuerpo: rota y se mueve con el torso. Personaje de perfil mirando a la derecha, visto un
#     poco de atrás: se ve la espalda (nunca el diseño de la espalda en el pecho);
#   - desenfoque de movimiento por sub-cuadros (esqueleto interpolado) cuando la figura se mueve rápido.
# Uso desde componer: import remera2d; remera2d.vestir(img, f)  (img RGB uint8 1080×1920, coordenadas originales)
import os, json, math
import numpy as np, cv2
from PIL import Image

TRAB = os.environ.get("ESCALADA_TRABAJO", ".")
ESQ = {int(k): v for k, v in json.load(open(os.path.join(TRAB, "an", "esqueleto.json"))).items()}
SS = 3
NEGRO = np.array([15, 15, 17], np.float32)
CONTORNO = np.array([168, 170, 176], np.float32)
CONT_LEJ = np.array([98, 99, 104], np.float32)
COSTURA = np.array([44, 44, 48], np.float32)
RIB = np.array([38, 38, 42], np.float32)
ESTAMPA = np.array([196, 198, 204], np.float32)
TONO = np.array([40, 40, 44], np.float32)
# forma (en radios de cabeza): x = hacia el pecho, y = a lo largo del torso desde el cuello
LT = 5.1                             # cuello → pelvis (esqueleto.py)
ANCHO, LARGO = 0.86, 5.30            # medio ancho en los hombros; largo del cuello al ruedo (apenas bajo la pelvis)
MANGA_L, MANGA_R0, MANGA_R1 = 1.62, 0.56, 0.64
# tramos donde un brazo o una pierna cercanos pasan por delante del cuerpo (brazo en V, trepar el borde, agachado,
# parado con el brazo colgando); en el resto solo la manga cercana va delante
FRENTE = [(212, 236), (263, 302), (303, 372)]
OL = 0.075

def _estampas():
    im = np.asarray(Image.open(os.path.join(TRAB, "escalada_tex", "estampa_espalda.png")).convert("L")).astype(np.float32)
    bg = cv2.GaussianBlur(cv2.morphologyEx(im.astype(np.uint8), cv2.MORPH_OPEN,
                                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (71, 71))).astype(np.float32), (0, 0), 15)
    hp = np.clip(im - bg, 0, None)
    letra = np.clip((hp - 45) / 25, 0, 1)                          # Founders Privée (gris claro)
    tono = np.clip((hp - 7) / 8, 0, 1) * (1 - np.clip((hp - 30) / 10, 0, 1))
    h, w = hp.shape; yy = np.mgrid[0:h, 0:w][0]
    tono *= (yy < 0.42 * h)                                         # ROCCÉ tono sobre tono (arriba)
    tono = cv2.morphologyEx(tono, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return cv2.GaussianBlur(letra, (0, 0), 1.2), cv2.GaussianBlur(tono, (0, 0), 2.0)
LETRA, TONO_A = _estampas()

def u(a): return np.array([math.cos(a), math.sin(a)])

def interp(f, t):
    """Esqueleto en el instante f + t (t en cuadros, |t| ≤ 0,5), interpolando con el vecino del mismo plano."""
    e = ESQ[f]
    g = f + (1 if t > 0 else -1)
    if t == 0 or g not in ESQ or ESQ[g]["plano"] != e["plano"]: return e
    o = ESQ[g]; a = abs(t)
    if np.hypot(*(np.array(o["H"]) - np.array(e["H"]))) > 3 * e["r"]: return e      # corte: no mezclar
    def la(x, y): return x + a * (((y - x) + math.pi) % (2 * math.pi) - math.pi)
    r = dict(e)
    r["H"] = (np.array(e["H"]) * (1 - a) + np.array(o["H"]) * a).tolist()
    for k in ("tor", "cer", "lej"): r[k] = la(e[k], o[k])
    r["vis_lej"] = e["vis_lej"] * (1 - a) + o["vis_lej"] * a
    return r

def geometria(e):
    H = np.array(e["H"], float); r = float(e["r"]); d = u(e["tor"]); fr = np.array([d[1], -d[0]])
    N = H + r * d
    def B(x, y): return N + fr * x * r + d * y * r              # cuerpo → imagen
    # contorno del cuerpo (pecho a la derecha): escote, hombros caídos, costados apenas entallados, ruedo curvo;
    # se suaviza con subdivisión de Chaikin para que no quede una caja
    W = ANCHO
    cuello = [(-0.40, 0.03), (-0.21, 0.12), (0.0, 0.16), (0.23, 0.13), (0.42, 0.03)]
    contorno = cuello + [(0.62, 0.12), (0.78, 0.28), (W, 0.55), (W - 0.03, 0.95),          # hombro caído
                         (0.80, 1.6), (0.72, 2.6), (0.66, 3.5), (0.69, 4.6), (0.74, LARGO - 0.12),  # entallada
                         (0.70, LARGO), (0.3, LARGO + 0.05), (0.0, LARGO + 0.06), (-0.3, LARGO + 0.05),
                         (-0.70, LARGO), (-0.74, LARGO - 0.12), (-0.69, 4.6), (-0.66, 3.5), (-0.72, 2.6),
                         (-0.80, 1.6), (-W + 0.03, 0.95), (-W, 0.55), (-0.78, 0.28), (-0.62, 0.12)]
    c = np.array(contorno, float)
    for _ in range(2):                                           # Chaikin (cerrado)
        q = np.roll(c, -1, 0); c = np.concatenate([0.75 * c + 0.25 * q, 0.25 * c + 0.75 * q], 1).reshape(-1, 2)
    cuerpo = np.array([B(x, y) for x, y in c])
    esc = np.array([B(x, y) for x, y in cuello])
    S = N + 0.6 * r * d
    def manga(a):
        """Tubo de la manga sobre el brazo: raíz redondeada dentro del hombro, costados rectos que abren apenas,
        ruedo perpendicular al brazo (levemente curvo)."""
        m = u(a); q = np.array([-m[1], m[0]])
        raiz = S - m * 0.40 * r; fin = S + m * MANGA_L * r
        poly = [raiz - m * math.cos(k) * MANGA_R0 * r * 0.8 + q * math.sin(k) * MANGA_R0 * r
                for k in np.linspace(-math.pi / 2, math.pi / 2, 11)]
        poly += [fin + q * MANGA_R1 * r] + [fin + m * 0.06 * r * math.cos(k) + q * MANGA_R1 * r * math.sin(k)
                                             for k in np.linspace(math.pi / 2 * 0.8, -math.pi / 2 * 0.8, 7)]
        poly += [fin - q * MANGA_R1 * r]
        return np.array(poly), fin, m, q
    return dict(H=H, r=r, d=d, fr=fr, N=N, S=S, cuerpo=cuerpo, esc=esc, B=B,
                cerca=manga(e["cer"]), lejos=manga(e["lej"]), vis_lej=float(e.get("vis_lej", 1.0)))

def _poly(shape, pts, off):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.round((pts - off) * SS * 16).astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=4)
    return m.astype(np.float32) / 255.0

def _anillo(m, px):
    k = max(3, int(round(2 * px)) | 1)
    return np.clip(cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) - m, 0, 1)

def _capas(e, off, shape):
    """Capas de la remera a resolución SS: devuelve [(color HxWx3, alfa HxW), ...] de atrás hacia adelante,
    separadas en 'detras' (manga lejana + cuerpo) y 'delante' (manga cercana)."""
    g = geometria(e); r = g["r"]; ol = max(1.2, OL * r) * SS
    hs, ws = shape
    yy, xx = np.mgrid[0:hs, 0:ws].astype(np.float32)
    P = lambda p: (p - off) * SS
    cuerpo = _poly(shape, g["cuerpo"], off)
    detras, delante = [], []
    # manga lejana (detrás del cuerpo)
    if g["vis_lej"] > 0.02:
        pl, fin, m, q = g["lejos"]; ml = _poly(shape, pl, off)
        rib = ml * np.clip((((xx - P(fin)[0]) * m[0] + (yy - P(fin)[1]) * m[1]) + 0.16 * r * SS) / 1.5, 0, 1)
        col = np.zeros(shape + (3,), np.float32) + NEGRO
        col = col * (1 - rib[..., None]) + RIB * rib[..., None]
        detras.append((CONT_LEJ, np.clip(_anillo(ml, ol), 0, 1) * g["vis_lej"]))
        detras.append((col, ml * g["vis_lej"]))
    # cuerpo
    col = np.zeros(shape + (3,), np.float32) + NEGRO
    dist_in = cv2.distanceTransform((cuerpo > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    rim = np.clip(1 - dist_in / (0.28 * r * SS), 0, 1) * cuerpo
    col += np.array([20, 20, 23], np.float32) * rim[..., None]
    # ruedo y cuello acanalados
    B = g["B"]
    v = np.stack([xx / SS + off[0] - g["N"][0], yy / SS + off[1] - g["N"][1]], -1)
    yb = (v @ g["d"]) / r; xb = (v @ g["fr"]) / r
    hem = np.clip((yb - (LARGO - 0.16)) / 0.04, 0, 1) * cuerpo
    col = col * (1 - hem[..., None]) + RIB * hem[..., None]
    esc_y = np.interp(xb, [-0.40, -0.20, 0.0, 0.22, 0.42], [-0.02, 0.10, 0.14, 0.12, 0.0])
    cuello = np.clip(1 - np.abs(yb - esc_y - 0.08) / 0.08, 0, 1) * (np.abs(xb) < 0.5) * cuerpo
    col = col * (1 - cuello[..., None]) + RIB * cuello[..., None]
    # estampado de la espalda: plano sobre el cuerpo (medio corrido hacia la espalda), rota con el torso
    hL, wL = LETRA.shape
    ancho = 1.30 * r * SS; alto = ancho * hL / wL
    c = P(B(-0.06, 1.55))
    # vista de 3/4 de atrás con el personaje mirando a la derecha: la estampa se lee de izquierda a derecha en
    # pantalla (hacia el pecho) y hacia abajo a lo largo del torso
    ex, ey = g["fr"], g["d"]
    M = np.float32([[ex[0] * ancho / wL, ey[0] * alto / hL, 0], [ex[1] * ancho / wL, ey[1] * alto / hL, 0]])
    M[:, 2] = c - M[:, 0] * wL / 2 - M[:, 1] * hL / 2
    a_l = cv2.warpAffine(LETRA, M, (ws, hs), flags=cv2.INTER_AREA) * cuerpo
    a_t = cv2.warpAffine(TONO_A, M, (ws, hs), flags=cv2.INTER_AREA) * cuerpo
    col = col * (1 - 0.55 * a_t[..., None]) + TONO * 0.55 * a_t[..., None]
    col = col * (1 - a_l[..., None]) + ESTAMPA * a_l[..., None]
    detras.append((CONTORNO, _anillo(cuerpo, ol)))
    detras.append((col, cuerpo))
    # manga cercana (delante): contorno claro afuera del cuerpo, costura oscura adentro
    pc, fin, m, q = g["cerca"]; mc = _poly(shape, pc, off)
    rib = mc * np.clip((((xx - P(fin)[0]) * m[0] + (yy - P(fin)[1]) * m[1]) + 0.16 * r * SS) / 1.5, 0, 1)
    col = np.zeros(shape + (3,), np.float32) + NEGRO
    dist_in = cv2.distanceTransform((mc > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    col += np.array([18, 18, 21], np.float32) * (np.clip(1 - dist_in / (0.22 * r * SS), 0, 1) * mc)[..., None]
    col = col * (1 - rib[..., None]) + RIB * rib[..., None]
    an = _anillo(mc, ol)
    an_col = CONTORNO[None, None, :] * (1 - cuerpo[..., None]) + COSTURA[None, None, :] * cuerpo[..., None]
    delante.append((an_col, an))
    delante.append((col, mc))
    return detras, delante, cuerpo, g

def _componer(base, capas):
    out = base.copy(); al = np.zeros(base.shape[:2], np.float32)
    for col, a in capas:
        a3 = a[..., None]
        out = out * (1 - a3) + (col if col.ndim == 3 else col[None, None, :]) * a3
        al = al + a * (1 - al)
    return out, al

def vestir(img, f, plano=None):
    if f not in ESQ: return
    e = ESQ[f]; r = float(e["r"]); H = np.array(e["H"])
    R = int(8.5 * r)
    x0, y0 = int(max(0, H[0] - R)), int(max(0, H[1] - R))
    x1, y1 = int(min(img.shape[1], H[0] + R)), int(min(img.shape[0], H[1] + R))
    if x1 - x0 < 10 or y1 - y0 < 10: return
    off = np.array([x0, y0], float)
    reg = img[y0:y1, x0:x1].astype(np.float32)
    h, w = reg.shape[:2]; shape = (h * SS, w * SS)
    # sub-cuadros si se mueve rápido (obturador de medio cuadro)
    vel = 0.0
    for g in (f - 1, f + 1):
        if g in ESQ and ESQ[g]["plano"] == e["plano"]:
            vel = max(vel, float(np.hypot(*(np.array(ESQ[g]["N"]) - np.array(e["N"])))))
    ts = [0.0] if vel < 2.5 else list(np.linspace(-0.25, 0.25, 5))
    acc_d = None; acc_f = None
    for t in ts:
        ee = interp(f, t)
        detras, delante, cuerpo, g = _capas(ee, off, shape)
        cd, ad = _componer(np.zeros(shape + (3,), np.float32), detras)
        cf, af = _componer(np.zeros(shape + (3,), np.float32), delante)
        if acc_d is None: acc_d = [cd * 0, ad * 0, cf * 0, af * 0, cuerpo * 0]
        acc_d[0] += cd; acc_d[1] += ad; acc_d[2] += cf; acc_d[3] += af; acc_d[4] += cuerpo
    n = len(ts)
    cd, ad, cf, af, cuerpo = [x / n for x in acc_d]
    # premultiplicado → a resolución del cuadro
    down = lambda x: cv2.resize(x, (w, h), interpolation=cv2.INTER_AREA)
    cd, ad, cf, af, cuerpo = down(cd), down(ad), down(cf), down(af), down(cuerpo)
    # capa de atrás (manga lejana + cuerpo)
    out = reg * (1 - ad[..., None]) + cd
    # delante del cuerpo: brazo y pierna cercanos (píxeles originales)
    g = geometria(e)
    lum = reg.mean(2); sat = reg.max(2) - reg.min(2)
    blanco = ((lum > 185) & (sat < 45)).astype(np.uint8)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    Hl, Nl = H - off, g["N"] - off; Pl = Nl + g["d"] * LT * r
    v = np.stack([xx - Nl[0], yy - Nl[1]], -1); s = np.clip(v @ g["d"], 0, LT * r)
    dax = np.linalg.norm(v - s[..., None] * g["d"], axis=-1)
    cabeza = (np.hypot(xx - Hl[0], yy - Hl[1]) < 1.04 * r)
    nucleo = dax < 0.62 * r
    fuera = cv2.dilate((ad < 0.05).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    en_frente = any(a <= f <= b for a, b in FRENTE)
    nucleo = dax < (0.72 * r)
    cand = blanco.astype(bool) & ~cabeza & ~nucleo
    n_, lab = cv2.connectedComponents(cand.astype(np.uint8), connectivity=8)
    delante_m = np.zeros((h, w), bool)
    for i in range(1, n_ if en_frente else 1):
        comp = lab == i
        if (comp & fuera).any(): delante_m |= comp
    # brazo con contorno delante del torso (pieza blanca separada que llega al codo)
    codo = g["S"] - off + u(e["cer"]) * 2.2 * r
    n2, lab2 = cv2.connectedComponents(blanco, connectivity=4)
    yc, xc = int(round(codo[1])), int(round(codo[0]))
    ids = set()
    for dy in range(-int(0.3 * r), int(0.3 * r) + 1, 2):
        for dx in range(-int(0.3 * r), int(0.3 * r) + 1, 2):
            yq, xq = yc + dy, xc + dx
            if 0 <= yq < h and 0 <= xq < w and lab2[yq, xq] > 0: ids.add(int(lab2[yq, xq]))
    eje = [(int(round(Nl[1] + g["d"][1] * k * r)), int(round(Nl[0] + g["d"][0] * k * r))) for k in np.linspace(0.8, 4.6, 14)]
    torso_ids = [lab2[y, x] for y, x in eje if 0 <= y < h and 0 <= x < w and lab2[y, x] > 0]
    tid = max(set(torso_ids), key=torso_ids.count) if torso_ids else -1
    for i in (ids if en_frente else []):
        if i != tid:
            comp = (lab2 == i) & ~cabeza
            if comp.sum() < 0.6 * (2 * r) ** 2 * 4: delante_m |= comp
    # cerca de la pelvis las piernas entran por debajo del ruedo (detrás de la remera)
    delante_m &= np.hypot(xx - Pl[0], yy - Pl[1]) > 1.3 * r
    dm = cv2.dilate(delante_m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))).astype(np.float32)
    dm = cv2.GaussianBlur(dm, (0, 0), 0.6)[..., None]
    out = out * (1 - dm) + reg * dm
    # manga cercana y cabeza
    out = out * (1 - af[..., None]) + cf
    cab = cv2.GaussianBlur(cabeza.astype(np.float32), (0, 0), 0.8)[..., None]
    out = out * (1 - cab) + reg * cab
    # brillo suave alrededor de la remera, como el de las figuras
    al = np.clip(ad + af, 0, 1)
    glow = cv2.GaussianBlur(al, (0, 0), 0.30 * r) * 0.10 * (1 - al)
    out = out * (1 - glow[..., None]) + 255 * glow[..., None]
    img[y0:y1, x0:x1] = np.clip(out + 0.5, 0, 255).astype(np.uint8)
