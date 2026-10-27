# Viste al protagonista de R1 con la remera blanca de Roccé, dibujada con el estilo de la animación
# (relleno claro, contorno oscuro como las extremidades, sombreado suave y halo), sobre la pose de pose_heroe.py.
#   - cuerpo: caja a lo largo del torso (cuello → cadera), más ancha de frente que de perfil;
#   - mangas cortas que siguen la dirección de cada brazo (la del brazo lejano, más oscura y detrás del cuerpo);
#   - oclusiones: la cabeza, la soga roja (atada a la cintura) y el antebrazo cercano quedan delante de la remera;
#   - desenfoque de movimiento según la velocidad del torso;
#   - de frente (arriba de la escalera), el estampado del pecho: "ROCCÉ" + "so f★cking close." chicos, del lado
#     izquierdo de quien la usa, en negro con la estrella celeste (como la remera real).
import json, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SS = 3                                       # sobremuestreo del dibujo
CEL = (126, 178, 222)
FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

def cargar_pose(path, f0, f1, manual=None):
    """Pose suavizada por cuadro (60 fps). Rellena huecos/saltos interpolando y suaviza con media de 5 cuadros."""
    raw = json.load(open(path)); manual = manual or {}
    fs = list(range(f0, f1 + 1))
    def serie(get):
        v = np.array([get(raw.get(str(f))) if raw.get(str(f)) else [np.nan, np.nan] for f in fs], float)
        return v
    H = serie(lambda p: p["H"]); N = serie(lambda p: p["N"]); P = serie(lambda p: p["P"])
    r = np.array([raw[str(f)]["r"] if raw.get(str(f)) else np.nan for f in fs])
    A1 = serie(lambda p: p["brazos"]["cerca"][:2] if p["brazos"]["cerca"] else [np.nan, np.nan])
    R1 = serie(lambda p: p["brazos"]["cerca"][3:5] if p["brazos"]["cerca"] and len(p["brazos"]["cerca"]) > 3 else [np.nan, np.nan])
    # saltos de cabeza (detección en otra parte del cuerpo) → hueco
    for i in range(len(fs)):
        lo, hi = max(0, i - 4), min(len(fs), i + 5)
        med = np.nanmedian(H[lo:hi], 0)
        if np.all(np.isfinite(H[i])) and np.hypot(*(H[i] - med)) > 30: H[i] = N[i] = P[i] = np.nan; r[i] = np.nan
    for k, v in manual.items():                      # correcciones a mano: {"f": {"N": [...], ...}}
        i = int(k) - f0
        if 0 <= i < len(fs):
            if "N" in v: N[i] = v["N"]
            if "P" in v: P[i] = v["P"]
            if "H" in v: H[i] = v["H"]
            if "r" in v: r[i] = v["r"]
    def fill(a):
        a = a.copy(); x = np.arange(len(a))
        if a.ndim == 1: a = a[:, None]
        for c in range(a.shape[1]):
            m = np.isfinite(a[:, c])
            if m.sum() >= 2: a[:, c] = np.interp(x, x[m], a[m, c])
        return a
    def smooth(a, k=5):
        pad = np.pad(a, ((k // 2, k // 2), (0, 0)), mode="edge"); ker = np.ones(k) / k
        return np.stack([np.convolve(pad[:, c], ker, "valid") for c in range(a.shape[1])], 1)
    H, N, P, r = smooth(fill(H)), smooth(fill(N)), smooth(fill(P)), smooth(fill(r), 7)[:, 0]
    R1 = smooth(fill(R1), 5)
    ang1 = np.arctan2(A1[:, 1], A1[:, 0]); ang1 = np.where(np.isfinite(ang1), ang1, np.nan)
    m = np.isfinite(ang1); x = np.arange(len(fs))
    if m.sum() >= 2:
        un = np.unwrap(ang1[m]); ang1 = np.interp(x, x[m], un)
    ang1 = smooth(ang1[:, None], 5)[:, 0]
    out = {}
    for i, f in enumerate(fs):
        out[f] = {"H": H[i], "N": N[i], "P": P[i], "r": r[i], "a1": ang1[i], "raiz1": R1[i]}
    return out

def _mask_poly(shape, pts, off):
    m = Image.new("L", shape, 0)
    ImageDraw.Draw(m).polygon([((q[0] - off[0]) * SS, (q[1] - off[1]) * SS) for q in pts], fill=255)
    return np.asarray(m, np.float32) / 255

def _mask_disk(shape, c, rad, off):
    m = Image.new("L", shape, 0); x, y = (c[0] - off[0]) * SS, (c[1] - off[1]) * SS; rr = rad * SS
    ImageDraw.Draw(m).ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
    return np.asarray(m, np.float32) / 255

def _suave(m, sig):
    return (cv2.GaussianBlur(m, (0, 0), max(0.5, sig)) > 0.5).astype(np.float32)

def _borde(m, ol):
    k = max(3, int(round(ol)) | 1)
    return np.clip(cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) - m, 0, 1)

def _capa(rgb, m):
    """RGBA float desde color y máscara (con borde suavizado)."""
    a = cv2.GaussianBlur(m, (0, 0), 0.7)
    out = np.zeros(m.shape + (4,), np.float32); out[..., :3] = rgb; out[..., 3] = a
    return out

def _over(dst, src):
    a = src[..., 3:4]
    dst[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a)
    dst[..., 3:4] = a + dst[..., 3:4] * (1 - a)
    return dst

def dibujar(frame, p, frente=0.0, brazos=None, vel=(0.0, 0.0), estampado=0.0, alpha=1.0):
    """frame: RGB uint8. p: pose del cuadro. frente: 0 perfil → 1 de frente.
    brazos: {"cerca": (raíz, dir), "lejos": (raíz, dir)} (dir unitario, coordenadas de imagen)."""
    Hc, N, P, r = np.array(p["H"], float), np.array(p["N"], float), np.array(p["P"], float), float(p["r"])
    u = (P - N) / (np.linalg.norm(P - N) + 1e-6); n = np.array([-u[1], u[0]]); L = np.linalg.norm(P - N)
    hw = r * (0.98 + 0.30 * frente)                       # medio ancho del cuerpo
    Hh, Ww = frame.shape[:2]
    x0 = int(max(0, min(Hc[0], N[0], P[0]) - 4.5 * r)); x1 = int(min(Ww, max(Hc[0], N[0], P[0]) + 4.5 * r))
    y0 = int(max(0, min(Hc[1], N[1], P[1]) - 4.5 * r)); y1 = int(min(Hh, max(Hc[1], N[1], P[1]) + 4.5 * r))
    if x1 - x0 < 10 or y1 - y0 < 10: return frame
    off = np.array([x0, y0], float); w, h = x1 - x0, y1 - y0; shp = (w * SS, h * SS)
    q = lambda s_, t_: N + u * s_ * L + n * t_ * hw        # coordenadas locales del torso
    # cuerpo: cuello, hombros caídos, sisa, ruedo (apenas curvo)
    body = [q(0.00, -0.42), q(0.05, -0.92), q(0.14, -1.00), q(0.40, -1.00), q(1.06, -0.98), q(1.10, -0.40),
            q(1.10, 0.40), q(1.06, 0.98), q(0.40, 1.00), q(0.14, 1.00), q(0.05, 0.92), q(0.00, 0.42)]
    mb = _suave(_mask_poly(shp, body, off), 0.12 * r * SS)
    sl_len, sl_r = 1.75 * r, 0.56 * r
    bpoly = np.array(body, np.float32)
    def dentro(pt):
        return cv2.pointPolygonTest(bpoly.reshape(-1, 1, 2), (float(pt[0]), float(pt[1])), False) >= 0
    def manga(raiz, dirv):
        raiz, dirv = np.array(raiz, float), np.array(dirv, float); dirv = dirv / (np.linalg.norm(dirv) + 1e-9)
        nd = np.array([-dirv[1], dirv[0]])
        a0 = raiz; e = raiz + dirv * sl_len
        if frente > 0.5:
            # de frente el brazo va al costado del cuerpo: la manga nace donde el brazo sale de la remera
            k = 0.0
            while k < 4 * r and dentro(raiz + dirv * k): k += 1.0
            a0 = raiz + dirv * max(0.0, k - 0.55 * r); e = raiz + dirv * (k + 1.15 * r)
        tube = [a0 + nd * sl_r, e + nd * sl_r * 1.06, e - nd * sl_r * 1.06, a0 - nd * sl_r]   # boca apenas más ancha
        m = np.maximum(_mask_poly(shp, tube, off), _mask_disk(shp, a0, sl_r, off))
        return _suave(m, 0.10 * r * SS), e, nd
    brazos = brazos or {}
    ol = max(2.0, 0.20 * r) * SS
    OUT = np.array([16, 18, 20], np.float32) / 255
    lay = np.zeros((shp[1], shp[0], 4), np.float32)
    if brazos.get("lejos"):
        ml, _, _ = manga(*brazos["lejos"])
        ml = np.clip(ml - mb, 0, 1)                         # detrás del cuerpo: solo lo que asoma
        ml = _suave(ml, 0.06 * r * SS)
        lay = _over(lay, _capa(OUT, np.clip(ml + _borde(ml, ol), 0, 1)))
        lay = _over(lay, _capa(np.array([196, 201, 207], np.float32) / 255, ml))
    lay = _over(lay, _capa(OUT, np.clip(mb + _borde(mb, ol), 0, 1)))
    lay = _over(lay, _capa(np.array([244, 246, 248], np.float32) / 255, mb))
    # volumen: lado de atrás apenas más oscuro (de perfil); costados (de frente)
    yy, xx = np.mgrid[0:shp[1], 0:shp[0]].astype(np.float32)
    px = (xx / SS + x0 - N[0]); py = (yy / SS + y0 - N[1])
    tcoord = (px * n[0] + py * n[1]) / hw
    sombra = np.clip((np.abs(tcoord) - 0.45) / 0.55, 0, 1) if frente > 0.5 else np.clip((-tcoord * (1 if n[0] >= 0 else -1) - 0.1) / 0.9, 0, 1)
    sombra = (sombra * mb * (0.10 + 0.04 * (1 - frente)))[..., None]
    lay[..., :3] = lay[..., :3] * (1 - sombra) + (np.array([70, 82, 96], np.float32) / 255) * sombra
    # cuello acanalado
    col = Image.new("L", shp, 0); dc = ImageDraw.Draw(col); cr = 0.40 * r * SS; c = (N + u * 0.015 * L - off) * SS
    dc.ellipse([c[0] - cr, c[1] - cr * (0.45 + 0.35 * frente), c[0] + cr, c[1] + cr * (0.45 + 0.35 * frente)], outline=255, width=max(1, int(ol * 0.7)))
    lay = _over(lay, _capa(OUT, np.asarray(col, np.float32) / 255 * mb))
    if brazos.get("cerca"):
        mn, e, nd = manga(*brazos["cerca"])
        dv = np.array(brazos["cerca"][1], float); dv /= np.linalg.norm(dv) + 1e-9
        if abs(float(dv @ u)) > 0.72:
            # brazo pegado al cuerpo: la manga se funde con la remera (sin contorno encima, que parecería un bolsillo)
            mn = np.clip(mn - mb, 0, 1); mn = _suave(mn, 0.06 * r * SS)
        lay = _over(lay, _capa(OUT, np.clip(mn + _borde(mn, ol), 0, 1)))
        lay = _over(lay, _capa(np.array([248, 250, 251], np.float32) / 255, mn))
    # estampado del pecho (de frente, del lado izquierdo de quien la usa = derecha de la imagen)
    if estampado > 0.02:
        im = Image.new("RGBA", shp, (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        side = 1 if n[0] > 0 else -1
        ex = (N + u * 0.20 * L + n * side * hw * 0.42 - off) * SS
        sz = max(3.0, 0.22 * r) * SS
        ft = ImageFont.truetype(FONT_SERIF, int(sz * 1.25)); a = int(235 * estampado)
        d.text((ex[0], ex[1]), "ROCCÉ", font=ft, fill=(22, 22, 24, a), anchor="mm")
        lw = ft.getlength("ROCCÉ"); ly = ex[1] + sz * 1.05
        d.line([ex[0] - lw * 0.48, ly, ex[0] + lw * 0.48, ly], fill=(60, 60, 64, int(a * 0.75)), width=max(1, int(sz * 0.22)))
        sx = ex[0] - lw * 0.20; rr = sz * 0.20
        d.ellipse([sx - rr, ly - rr, sx + rr, ly + rr], fill=CEL + (a,))
        pr = np.asarray(im, np.float32) / 255; pr[..., 3] *= mb
        lay = _over(lay, pr)
    # halo suave como el de las figuras
    al = lay[..., 3]
    glow = cv2.GaussianBlur(al, (0, 0), 0.45 * r * SS) * 0.22
    halo = np.zeros_like(lay); halo[..., :3] = 1; halo[..., 3] = glow
    lay = _over(halo, lay)
    lay = cv2.resize(lay, (w, h), interpolation=cv2.INTER_AREA)
    # desenfoque de movimiento (premultiplicado)
    vx, vy = vel; sp = math.hypot(vx, vy)
    if sp > 3.0:
        k = int(min(15, round(sp))) | 1
        ker = np.zeros((k, k), np.float32); c0 = k // 2; ux, uy = vx / sp, vy / sp
        cv2.line(ker, (int(round(c0 - ux * c0)), int(round(c0 - uy * c0))), (int(round(c0 + ux * c0)), int(round(c0 + uy * c0))), 1.0, 1)
        ker /= ker.sum()
        prem = lay.copy(); prem[..., :3] *= prem[..., 3:4]
        prem = cv2.filter2D(prem, -1, ker)
        a_ = prem[..., 3:4]; lay = np.concatenate([np.where(a_ > 1e-3, prem[..., :3] / np.maximum(a_, 1e-3), 0), a_], -1)
    A = lay[..., 3:4] * alpha
    reg = frame[y0:y1, x0:x1].astype(np.float32)
    comp = reg * (1 - A) + lay[..., :3] * 255 * A
    # oclusiones: cabeza, soga/chispas y antebrazo cercano quedan delante
    R_, G_, B_ = reg[..., 0], reg[..., 1], reg[..., 2]; lum = reg.mean(-1)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    keep = np.hypot(xx - Hc[0], yy - Hc[1]) < r * 1.12
    # soga y chispas delante solo en el borde de atrás, donde está atada (en el resto del cuerpo pasa por detrás)
    sx_ = ((xx - N[0]) * u[0] + (yy - N[1]) * u[1]) / L; tx_ = ((xx - N[0]) * n[0] + (yy - N[1]) * n[1]) / hw
    keep |= ((R_ - np.maximum(G_, B_)) > 45) & (np.abs(tx_) > 0.65)
    if brazos.get("cerca"):
        raiz, dv = np.array(brazos["cerca"][0], float), np.array(brazos["cerca"][1], float); dv /= np.linalg.norm(dv) + 1e-9
        along = (xx - raiz[0]) * dv[0] + (yy - raiz[1]) * dv[1]
        v2x, v2y = xx - N[0], yy - N[1]; tt = np.clip((v2x * u[0] + v2y * u[1]) / L, 0, 1)
        dax = np.hypot(v2x - tt * L * u[0], v2y - tt * L * u[1])
        keep |= (lum > 200) & (dax > 0.75 * r) & (along > sl_len * 1.02) & (np.hypot(xx - P[0], yy - P[1]) > 1.3 * r)
    keep = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 0.8)[..., None]
    comp = comp * (1 - keep) + reg * keep
    out = frame.copy(); out[y0:y1, x0:x1] = np.clip(comp, 0, 255).astype(np.uint8)
    return out
