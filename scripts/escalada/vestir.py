# Viste al escalador con la remera negra de Roccé, dibujada con el estilo de la animación:
#   - cuerpo: caja redondeada a lo largo del torso (pose_escalador.py), negra, con contorno gris claro y un brillo
#     de borde suave para que se separe del fondo oscuro, cuello acanalado;
#   - mangas: salen de los brazos reales de la figura cerca del hombro (píxeles blancos = brazo cercano, grises =
#     lejano), recorridos a lo largo del brazo hasta un largo fijo, con el ruedo recto y perpendicular al brazo;
#     la lejana queda detrás del cuerpo y más oscura;
#   - estampado real (recortado de las fotos de producto, sin redibujar): de espaldas mientras trepa (ROCCÉ tono
#     sobre tono + Founders Privée), y del pecho (ROCCÉ / so f★cking close.) cuando queda de frente arriba;
#   - delante de la remera quedan la cabeza y el antebrazo cercano cuando cruza el cuerpo.
# La llama componer.py con el cuadro (coordenadas originales) y el nombre del plano.
import os, json, math
import numpy as np, cv2
from PIL import Image

TRAB = os.environ.get("ESCALADA_TRABAJO", ".")
SS = 3
POSES = {}
for k in "ACDEF":
    p = os.path.join(TRAB, "pose", f"p2_{k}.json")
    if os.path.exists(p):
        for f, v in json.load(open(p)).items(): POSES[int(f)] = v

def _cargar_estampa(nombre, umbral, ancho_umbral):
    """Estampa real recortada de la foto: diferencia con el fondo local de la tela (la foto tiene luz despareja),
    alfa por umbral suave y desvanecida en los bordes del recorte. Devuelve (valor a sumar al negro, alfa)."""
    im = np.asarray(Image.open(os.path.join(TRAB, "escalada_tex", nombre)).convert("L"))
    # fondo de la tela: apertura con un disco más ancho que los trazos (saca el estampado) y suavizado
    bg = cv2.morphologyEx(im, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (71, 71)))
    bg = cv2.GaussianBlur(bg.astype(np.float32), (0, 0), 15)
    hp = np.clip(im.astype(np.float32) - bg, 0, None)
    a = np.clip((hp - umbral) / ancho_umbral, 0, 1)
    h, w = a.shape; yy, xx = np.mgrid[0:h, 0:w]
    ven = np.clip(np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]) / (0.05 * min(h, w)), 0, 1)
    a = cv2.GaussianBlur(a * ven, (0, 0), 0.8)
    return hp, a
EST_ESP = _cargar_estampa("estampa_espalda.png", 6.0, 10.0)      # también el ROCCÉ tono sobre tono (muy sutil, como en la remera)
EST_FRE = _cargar_estampa("estampa_frente.png", 20.0, 25.0)

NEGRO = np.array([13, 13, 15], np.float32)
CONTORNO = np.array([150, 152, 157], np.float32)
LEJANA = np.array([25, 25, 28], np.float32)

def frente(f):
    if f < 283: return 0.0
    if f >= 291: return 1.0
    return (f - 283) / 8.0

def _poly(shape, pts):
    m = np.zeros(shape, np.uint8); cv2.fillPoly(m, [np.round(np.array(pts) * 8).astype(np.int32)], 1, lineType=cv2.LINE_AA, shift=3)
    return m.astype(bool)

def _geodesica(mask, semilla, pasos):
    """Distancia (en pasos de dilatación) desde la semilla, sin salir de la máscara."""
    d = np.full(mask.shape, np.inf, np.float32); cur = semilla & mask; d[cur] = 0
    k = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    for i in range(1, pasos + 1):
        nxt = cv2.dilate(cur.astype(np.uint8), k).astype(bool) & mask
        nuevo = nxt & ~cur
        if not nuevo.any(): break
        d[nuevo] = i; cur = nxt
    return d

def _manga(limb, S, r, rho, rel):
    """Manga a partir de los píxeles del brazo (limb, bool) cerca del hombro S. Devuelve (máscara, geodésica) o None."""
    h, w = limb.shape
    yy, xx = np.mgrid[0:h, 0:w]
    semilla = limb & (np.hypot(xx - S[0], yy - S[1]) < 1.05 * r)
    if semilla.sum() < 6: return None
    geo = _geodesica(limb, semilla, int(rho + 2 * r))
    brazo = geo <= rho
    if brazo.sum() < 10: return None
    frente_px = (geo > rho - 0.35 * r) & brazo
    c0 = np.array([xx[semilla].mean(), yy[semilla].mean()])
    if frente_px.sum() >= 3:
        E = np.array([xx[frente_px].mean(), yy[frente_px].mean()])
    else:
        E = np.array([xx[brazo].mean(), yy[brazo].mean()])
    dA = E - c0; nA = np.linalg.norm(dA)
    if nA < 0.3 * r: return None
    dA /= nA
    k = int(round(2 * rel)) | 1
    sl = cv2.dilate(brazo.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))).astype(bool)
    sl &= ((xx - E[0]) * dA[0] + (yy - E[1]) * dA[1]) <= 0.0           # ruedo recto
    return sl, geo, E, dA

def vestir(img, f, plano=None):
    p = POSES.get(f)
    if p is None: return
    H, r, N, P = np.array(p["H"]), float(p["r"]), np.array(p["N"]), np.array(p["P"])
    u = (P - N) / (np.linalg.norm(P - N) + 1e-9); L = float(np.linalg.norm(P - N))
    a_ = np.array([u[1], -u[0]])                         # eje transversal (hacia la derecha de la imagen si el torso es vertical)
    hw = 1.12 * r
    S = N + u * 0.14 * L
    Hh, Ww = img.shape[:2]
    R = 1.6 * L + 2 * r
    x0, y0 = int(max(0, min(H[0], P[0]) - R)), int(max(0, min(H[1], P[1]) - R))
    x1, y1 = int(min(Ww, max(H[0], P[0]) + R)), int(min(Hh, max(H[1], P[1]) + R))
    if x1 - x0 < 20 or y1 - y0 < 20: return
    reg = img[y0:y1, x0:x1].astype(np.float32)
    off = np.array([x0, y0], float)
    Hl, Nl, Pl, Sl = H - off, N - off, P - off, S - off
    lum = reg.mean(2); sat = reg.max(2) - reg.min(2)
    k5 = np.ones((5, 5), np.uint8)
    blanco = cv2.morphologyEx(((lum > 200) & (sat < 40)).astype(np.uint8), cv2.MORPH_OPEN, k5).astype(bool)
    gris = cv2.morphologyEx(((lum > 100) & (lum <= 200) & (sat < 40)).astype(np.uint8), cv2.MORPH_OPEN, k5).astype(bool)
    h, w = lum.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # torso: núcleo (para separar brazos del cuerpo) y caja de la remera
    v2x, v2y = xx - Nl[0], yy - Nl[1]; s_ = (v2x * u[0] + v2y * u[1]) / L; t_ = (v2x * a_[0] + v2y * a_[1]) / hw
    dax = np.hypot(v2x - np.clip(s_, 0, 1) * L * u[0], v2y - np.clip(s_, 0, 1) * L * u[1])
    cabeza = np.hypot(xx - Hl[0], yy - Hl[1]) < 1.06 * r
    q = lambda s, t: Nl + u * s * L + a_ * t * hw
    cuerpo_pts = [q(-0.02, -0.40), q(0.04, -0.90), q(0.13, -1.0), q(0.45, -0.98), q(1.00, -0.97), q(1.04, -0.5),
                  q(1.045, 0.0), q(1.04, 0.5), q(1.00, 0.97), q(0.45, 0.98), q(0.13, 1.0), q(0.04, 0.90), q(-0.02, 0.40)]
    cuerpo = _poly((h, w), cuerpo_pts)
    nucleo = dax < 0.45 * r
    rho, rel = 1.45 * r, 0.25 * r
    cerca = _manga(blanco & ~cabeza & ~nucleo, Sl, r, rho, rel)
    lejos = _manga(gris & ~cabeza & ~nucleo, Sl, r, rho * 0.95, rel * 0.9)
    # capas (a resolución del cuadro; bordes suavizados después)
    def borde(m, ol):
        k = max(3, int(round(2 * ol)) | 1)
        return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))).astype(bool) & ~m
    ol = max(1.5, 0.075 * r)
    col = reg.copy(); al = np.zeros((h, w), np.float32)
    def pintar(m, c, a=1.0):
        nonlocal col, al
        mm = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.6) * a
        col = col * (1 - mm[..., None]) + c * mm[..., None]; al = np.maximum(al, mm)
    sombra_total = cuerpo.copy()
    if lejos is not None:
        ml = lejos[0] & ~cuerpo
        pintar(borde(ml, ol * 0.8) & ~cuerpo, CONTORNO * 0.65); pintar(ml, LEJANA)
    forma = cuerpo.copy()
    if cerca is not None: forma |= cerca[0]
    pintar(borde(forma, ol), CONTORNO)
    pintar(forma, NEGRO)
    # volumen: brillo de borde suave adentro
    dist_in = cv2.distanceTransform(forma.astype(np.uint8), cv2.DIST_L2, 5)
    rim = np.clip(1 - dist_in / (0.30 * r), 0, 1) * forma
    col = col + (np.array([30, 30, 34], np.float32) * rim[..., None]) * 0.9
    # ruedo de las mangas y cuello acanalado
    for m in (cerca, lejos):
        if m is None: continue
        sl, geo, E, dA = m
        banda = sl & ((((xx - E[0]) * dA[0] + (yy - E[1]) * dA[1])) > -0.14 * r) & ~cuerpo
        pintar(banda, np.array([44, 44, 48], np.float32))
    cuello = (np.abs(np.hypot((xx - Nl[0]) * 1.0, (yy - Nl[1]) * 1.0) - 0.48 * r) < 0.07 * r + 0.6) & cuerpo
    pintar(cuello, np.array([40, 40, 44], np.float32))
    # estampados reales
    fr = frente(f)
    def estampa(E_, ancho, s_centro, t_centro, peso):
        if peso <= 0.01: return
        im_, a0 = E_
        hh_, ww_ = im_.shape
        alto = ancho * hh_ / ww_
        c = Nl + u * s_centro * L + a_ * t_centro * hw
        # transformación: (columna, fila) de la estampa → cuadro (eje x = a_, eje y = u)
        M = np.float32([[a_[0] * ancho / ww_, u[0] * alto / hh_, 0], [a_[1] * ancho / ww_, u[1] * alto / hh_, 0]])
        M[:, 2] = c - M[:, 0] * ww_ / 2 - M[:, 1] * hh_ / 2
        big = cv2.warpAffine(im_, M, (w, h), flags=cv2.INTER_LINEAR)
        ab = cv2.warpAffine(a0, M, (w, h), flags=cv2.INTER_LINEAR) * cuerpo * peso
        nonlocal col
        col = col * (1 - ab[..., None]) + (NEGRO + big[..., None]) * ab[..., None]
    estampa(EST_ESP, 1.74 * hw, 0.27, 0.0, 1.0 - fr)
    estampa(EST_FRE, 0.62 * hw, 0.24, 0.40, fr)
    # halo suave como el de las figuras (afuera)
    glow = cv2.GaussianBlur(al, (0, 0), 0.35 * r) * 0.16 * (1 - al)
    col = col * (1 - glow[..., None]) + 255 * glow[..., None]
    # delante de la remera: cabeza y antebrazo cercano cuando cruza el cuerpo
    keep = cabeza.copy()
    if cerca is not None:
        geo = cerca[1]
        keep |= blanco & (geo > rho + 0.2 * r) & np.isfinite(geo) & (dax > 0.6 * r) & (np.hypot(xx - Pl[0], yy - Pl[1]) > 1.2 * r)
    # desenfoque de movimiento de la capa (como la figura en los movimientos rápidos)
    pa, pb = POSES.get(f - 1), POSES.get(f + 1)
    if pa is not None and pb is not None:
        v = (np.array(pb["N"]) - np.array(pa["N"])) / 2.0
        sp = float(np.hypot(*v)) * 0.5            # obturador de medio cuadro
        if 1.5 < sp < 20:                           # más de 40 px por cuadro = corte de plano, no movimiento
            k = int(min(25, round(sp))) | 1; ker = np.zeros((k, k), np.float32); c0 = k // 2; ux, uy = v / (np.hypot(*v) + 1e-9)
            cv2.line(ker, (int(round(c0 - ux * c0)), int(round(c0 - uy * c0))), (int(round(c0 + ux * c0)), int(round(c0 + uy * c0))), 1.0, 1)
            ker /= ker.sum()
            col = reg + cv2.filter2D(col - reg, -1, ker)
    keep = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 0.7)[..., None]
    out = col * (1 - keep) + reg * keep
    img[y0:y1, x0:x1] = np.clip(out, 0, 255).astype(np.uint8)
