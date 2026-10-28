# Capa "pared" de la escalada: rótulos en español en lugar de los ingleses y bandera celeste en lugar de la roja.
#
# Rótulos (por plano, en coordenadas del cuadro de referencia; seguir_torre.py da la semejanza ref → cuadro):
#   - máscara de las letras originales (claras, dentro de la caja) → se rellenan con la pared (plano ajustado al
#     entorno inmediato + grano parecido) salvo donde hay algo delante (el escalador): ahí queda el cuadro original;
#   - el texto nuevo se escribe con la misma letra (Saira, como en "lo que te frena"), mismo alto de mayúscula, mismo
#     color y mismo inicio a la izquierda, y también queda detrás del escalador;
#   - ÉXITO: la tilde no entra bajo el borde de la torre, así que el renglón baja lo justo y su rayita guía también.
# Bandera: se borra la roja (y su resplandor) y se dibuja una celeste rectangular que flamea, atada al mástil
# (mismo punto de la torre en cada cuadro), con "GIVE / HISTORY / YOUR NAME." en azul oscuro.
import os, sys, math, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI); sys.path.insert(0, os.path.join(AQUI, "..", "frena"))
from planos import PLANOS
from rotulos import Estilo

NUEVOS = {"SUCCESS": "ÉXITO", "BUILD AN": "CONSTRUIR", "EMPIRE": "UN IMPERIO", "START A": "INICIAR",
          "BUSINESS": "UN NEGOCIO", "DREAM": "SUEÑO", "WORK": "TRABAJO"}
COLOR_LETRA = (209, 205, 209)          # medido en las letras originales
CELESTE = np.array([126, 178, 222], np.float32)
AZUL = np.array([14, 32, 60], np.float32)
FUENTE_BANDERA = os.path.join(AQUI, "..", "..", "CARRUSEL", "prelanzamiento", "fuentes", "InterDisplay-Bold.otf")
LEMA = ["GIVE", "HISTORY", "YOUR NAME."]

def gris(a): return a.astype(np.float32).mean(2)

# ------------------------------------------------------------------------------------------------ preparación
class Plano:
    def __init__(self, nombre, P, seq, poste, torre=None):
        self.nombre, self.P = nombre, P
        self.seq, self.torre = seq, torre
        ref = np.asarray(Image.open(f"{seq}/{P['ref']:04d}.png").convert("RGB"))
        self.ref = ref; self.gref = gris(ref)
        self.rot = {}
        for k, (x, y, w, h) in P["rotulos"].items():
            self.rot[k] = self._preparar(k, x, y, w, h)
        self.poste = poste      # (x centro, y punta, largo, ancho) en coordenadas de referencia

    def _preparar(self, k, x, y, w, h):
        g = self.gref
        M = 4
        XL, XR = 4, 34              # ventana: un poco antes de la caja (la rayita termina antes) y bastante después
        sub = (g[y - M:y + h + M, x - XL:x + w + XR] > 80).astype(np.uint8)
        # líneas largas (borde superior de la torre) fuera: así las letras que lo tocan quedan sueltas
        lineas = cv2.morphologyEx(sub, cv2.MORPH_OPEN, np.ones((1, 41), np.uint8))
        sub = sub & (1 - cv2.dilate(lineas, np.ones((3, 1), np.uint8)))
        # solo las letras: componentes que no se salen de la caja (el borde de la torre y el mástil sí se salen)
        n, lab, st, _ = cv2.connectedComponentsWithStats(sub, 8)
        let = np.zeros_like(sub)
        for i in range(1, n):
            cx, cy, cw, ch, A = st[i]
            if cx >= 1 and cx + cw <= sub.shape[1] - 1 and cy >= 1 and cy + ch <= sub.shape[0] - 1 and ch >= 0.5 * h: let[lab == i] = 1
        m = np.zeros_like(g, np.uint8)
        m[y - M:y + h + M, x - XL:x + w + XR] = let
        r_ = int(round(0.2 * h)) | 1                      # cubre el leve resplandor alrededor de cada letra
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (r_, r_)))
        # proteger el borde de la torre y el mástil (líneas largas): no se borran aunque las letras los toquen
        zona = (g[y - 20:y + h + 20, x - 40:x + w + 60] > 80).astype(np.uint8)
        est = cv2.morphologyEx(zona, cv2.MORPH_OPEN, np.ones((1, 41), np.uint8)) | cv2.morphologyEx(zona, cv2.MORPH_OPEN, np.ones((41, 1), np.uint8))
        est_full = np.zeros_like(m); est_full[y - 20:y + h + 20, x - 40:x + w + 60] = cv2.dilate(est, np.ones((3, 3), np.uint8))
        m = m & (1 - est_full)
        # resplandor: más allá del núcleo, peso que baja hasta 0 a ~0,55 del alto de letra
        dist = cv2.distanceTransform((1 - m).astype(np.uint8), cv2.DIST_L2, 5)
        peso = np.clip(1.0 - dist / max(2.0, 0.42 * h), 0, 1).astype(np.float32)
        peso[est_full.astype(bool)] = 0
        est = Estilo(cap=float(h), gap=0.38, wght=500, ancho=0.9)
        txt, top = est.linea(NUEVOS[k])
        dy = 0; raya = None
        if k == "SUCCESS":
            # alto de la tilde: filas con tinta por encima de la mayúscula
            filas = np.where(txt.max(1) > 60)[0]; acento = max(0, top - filas.min())
            # borde de la torre: última fila clara por encima de la caja
            seg = g[y - 25:y + 2, x:x + w].mean(1); claras = [y - 25 + i for i, v in enumerate(seg) if v > 90]
            borde = max(claras) if claras else y - 10
            libre = y - (borde + 1)
            dy = max(0, acento + 3 - libre)
            # rayita guía: componente clara fina a la izquierda de la caja, a media altura
            mejor = None
            a_, b_ = self.P["cuadros"]
            for fr in sorted({self.P["ref"], a_, (a_ + b_) // 2, b_, a_ + (b_ - a_) // 4, a_ + 3 * (b_ - a_) // 4}):
                if fr == self.P["ref"] or not self.torre: gg, ss_, tx_, ty_ = g, 1.0, 0.0, 0.0
                else:
                    T_ = self.torre[fr]; ss_, tx_, ty_ = T_["s"], T_["tx"], T_["ty"]
                    gg = gris(np.asarray(Image.open(f"{self.seq}/{fr:04d}.png").convert("RGB")))
                # zona de la rayita en ese cuadro
                X0_, Y0_ = int(ss_ * (x - 70) + tx_), int(ss_ * (y + 2) + ty_)
                X1_, Y1_ = int(ss_ * (x - 3) + tx_), int(ss_ * (y + h - 2) + ty_)
                t = gg[max(0, Y0_):Y1_, max(0, X0_):X1_]
                if t.size == 0: continue
                cc = (t > 70).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(cc, 8)
                for i in range(1, n):
                    cx, cy, cw, ch, A = st[i]
                    if cw >= 6 and ch <= 6:
                        # a coordenadas de la referencia
                        rx = (max(0, X0_) + cx - tx_) / ss_; ry = (max(0, Y0_) + cy - ty_) / ss_
                        cand = (int(round(rx)), int(round(ry)), int(round(cw / ss_)), max(2, int(round(ch / ss_))))
                        if mejor is None or cand[2] > mejor[2]: mejor = cand
            if mejor is not None and dy > 0:
                rx0, ry0, cw, ch = mejor
                raya = (rx0, ry0, cw, ch)
                # borrar la vieja (en la máscara de borrado) y guardar su aspecto para redibujarla abajo
                m[ry0 - 2:ry0 + ch + 2, rx0:rx0 + cw + 1] = 1
        if raya is not None:
            bx, by, bw, bh = raya; peso[by - 2:by + bh + 2, bx:bx + bw + 1] = 1.0
        return {"caja": (x, y, w, h), "borrar": m, "peso": peso, "txt": txt, "top": top, "dy": dy, "raya": raya}

def ajuste_plano(img, sel):
    """Plano a + b·x + c·y por canal, ajustado a los píxeles sel (bool) de img (h×w×3)."""
    ys, xs = np.nonzero(sel)
    if len(xs) < 20: return None
    A = np.stack([np.ones_like(xs), xs, ys], 1).astype(np.float32)
    coef = [np.linalg.lstsq(A, img[ys, xs, c].astype(np.float32), rcond=None)[0] for c in range(3)]
    res = np.concatenate([img[ys, xs, c].astype(np.float32) - A @ coef[c] for c in range(3)])
    return coef, float(np.std(res))

# ------------------------------------------------------------------------------------------------ rótulos por cuadro
def aplicar_rotulos(out, plano, T, rng, extra_fg=None):
    """out: cuadro RGB uint8 (se modifica). T = (s, tx, ty). extra_fg: máscara opcional de cosas delante."""
    s, tx, ty = T
    Hh, Ww = out.shape[:2]
    g = gris(out)
    for k, R in plano.rot.items():
        x, y, w, h = R["caja"]
        tw = R["txt"].shape[1]
        rx0 = min(x, R["raya"][0] if R["raya"] else x) - 14; ry0 = y - 16
        rx1 = max(x + w, x + tw) + 16; ry1 = y + h + 16 + R["dy"]
        fx0, fy0 = int(math.floor(s * rx0 + tx)), int(math.floor(s * ry0 + ty))
        fx1, fy1 = int(math.ceil(s * rx1 + tx)), int(math.ceil(s * ry1 + ty))
        cx0, cy0, cx1, cy1 = max(0, fx0), max(0, fy0), min(Ww, fx1), min(Hh, fy1)
        if cx1 - cx0 < 4 or cy1 - cy0 < 4: continue
        W_, H_ = cx1 - cx0, cy1 - cy0
        Mw = np.array([[s, 0, tx - cx0], [0, s, ty - cy0]], np.float32)
        borrar = cv2.warpAffine(R["borrar"].astype(np.float32), Mw, (W_, H_), flags=cv2.INTER_LINEAR) > 0.3
        peso = cv2.warpAffine(R["peso"], Mw, (W_, H_), flags=cv2.INTER_LINEAR)
        esperado = cv2.warpAffine(plano.gref, Mw, (W_, H_), flags=cv2.INTER_LINEAR)
        win = out[cy0:cy1, cx0:cx1]; gw = g[cy0:cy1, cx0:cx1]
        # algo delante (el escalador): trazo claro GRUESO (las letras son finas), reconstruido a su ancho completo,
        # más lo que difiere de la referencia fuera de las letras viejas
        capf = s * h
        claro = (gw > 100).astype(np.uint8)
        dt = cv2.distanceTransform(claro, cv2.DIST_L2, 3)
        umbral = max(3.0, 0.12 * capf)
        letras_dil = cv2.dilate(borrar.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
        nucleo = (((dt > umbral) & ~letras_dil) | (dt > 2.2 * umbral)).astype(np.uint8)
        k = int(2 * umbral + 5) | 1
        fg = cv2.dilate(nucleo, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) & cv2.dilate(claro, np.ones((3, 3), np.uint8))
        dif = (np.abs(cv2.GaussianBlur(gw, (0, 0), 1.0) - cv2.GaussianBlur(esperado, (0, 0), 1.0)) > 35) & ~letras_dil
        dif = cv2.morphologyEx(dif.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        fg = cv2.dilate((fg | dif).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        if extra_fg is not None: fg |= extra_fg[cy0:cy1, cx0:cx1]
        # relleno de pared
        anillo = (peso < 0.02) & (~fg) & (gw < 80) & (gw > 22)
        aj = ajuste_plano(win, anillo)
        if aj is not None:
            coef, sd = aj
            yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
            fill = np.stack([coef[c][0] + coef[c][1] * xx + coef[c][2] * yy for c in range(3)], 2)
            fill += cv2.GaussianBlur(rng.normal(0, 1.0, fill.shape[:2]).astype(np.float32), (0, 0), 0.6)[..., None] * min(sd, 1.2)
            # mezcla con borde suave (sin cortes duros contra la pared original)
            suave = peso * (~fg)
            win[:] = np.clip(win.astype(np.float32) * (1 - suave[..., None]) + fill * suave[..., None], 0, 255).astype(np.uint8)
        # texto nuevo (en coordenadas de referencia, sobremuestreado → cuadro)
        txt = R["txt"].astype(np.float32) / 255.0
        capa = np.zeros((int(ry1 - ry0) + 2, int(rx1 - rx0) + 2), np.float32)
        ox, oy = x - rx0, y + R["dy"] - R["top"] - ry0
        hh, ww = txt.shape
        y0c, x0c = max(0, oy), max(0, ox)
        capa[y0c:oy + hh, x0c:ox + ww] = np.maximum(capa[y0c:oy + hh, x0c:ox + ww], txt[y0c - oy:capa.shape[0] - oy, x0c - ox:capa.shape[1] - ox][:capa[y0c:oy + hh, x0c:ox + ww].shape[0], :capa[y0c:oy + hh, x0c:ox + ww].shape[1]])
        if R["raya"] and R["dy"] > 0:
            bx, by, bw, bh = R["raya"]
            capa[by - ry0 + R["dy"]:by - ry0 + R["dy"] + bh, bx - rx0:bx - rx0 + bw] = 1.0
        Mc = np.array([[s, 0, s * rx0 + tx - cx0], [0, s, s * ry0 + ty - cy0]], np.float32)
        a = cv2.warpAffine(capa, Mc, (W_, H_), flags=cv2.INTER_LINEAR)
        halo = cv2.GaussianBlur(a, (0, 0), 3.0 * s) * 0.06
        a = np.clip(a + halo, 0, 1) * (~fg)
        col = np.array(COLOR_LETRA, np.float32)
        win[:] = np.clip(win.astype(np.float32) * (1 - a[..., None]) + col * a[..., None], 0, 255).astype(np.uint8)
    return out

# ------------------------------------------------------------------------------------------------ bandera
def borrar_roja(out, x0, y0, x1, y1):
    Hh, Ww = out.shape[:2]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(Ww, x1), min(Hh, y1)
    if x1 <= x0 or y1 <= y0: return
    win = out[y0:y1, x0:x1].astype(np.float32)
    r, g_, b = win[..., 0], win[..., 1], win[..., 2]
    exc = r - np.maximum(g_, b)
    roja = exc > 6
    if not roja.any(): return
    # fondo: cielo oscuro alrededor (mediana de lo que no es rojo ni claro)
    bgsel = (~cv2.dilate(roja.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)) & (win.mean(2) < 40)
    bgc = np.median(win[bgsel], 0) if bgsel.sum() > 30 else np.array([3, 3, 5], np.float32)
    k = np.clip(exc / 70.0, 0, 1)[..., None]
    neutro = np.minimum(g_, b)[..., None].repeat(3, 2)       # lo que quede del mástil o de una estrella, sin rojo
    nuevo = bgc * k + neutro * (1 - k)
    win = np.where(roja[..., None], nuevo, win)
    out[y0:y1, x0:x1] = np.clip(win, 0, 255).astype(np.uint8)

_FT = {}
def textura_bandera(Wp, Hp):
    """Paño celeste Wp×Hp (px) con el lema en tres renglones centrados. Devuelve RGB float."""
    tex = np.zeros((Hp, Wp, 3), np.float32) + CELESTE
    im = Image.new("L", (Wp, Hp), 0); d = ImageDraw.Draw(im)
    pad_x, pad_y = 0.09 * Wp, 0.12 * Hp
    # tamaño: que el renglón más ancho entre en el ancho útil y los tres en el alto útil
    def medir(px):
        f = _FT.get(px) or ImageFont.truetype(FUENTE_BANDERA, px); _FT[px] = f
        bbs = [f.getbbox(t) for t in LEMA]; return f, bbs
    px = 10
    while True:
        f, bbs = medir(px + 1)
        capH = f.getbbox("H")[3] - f.getbbox("H")[1]
        ancho = max(b[2] - b[0] for b in bbs); alto = 3 * capH + 2 * 0.42 * capH
        if ancho > Wp - 2 * pad_x or alto > Hp - 2 * pad_y: break
        px += 1
    f, bbs = medir(px); capH = f.getbbox("H")[3] - f.getbbox("H")[1]
    alto = 3 * capH + 2 * 0.42 * capH; y = (Hp - alto) / 2
    for t, bb in zip(LEMA, bbs):
        w = bb[2] - bb[0]; d.text(((Wp - w) / 2 - bb[0], y - f.getbbox("H")[1]), t, font=f, fill=255)
        y += capH * 1.42
    a = np.asarray(im, np.float32)[..., None] / 255
    tex = tex * (1 - a) + AZUL * a
    # costura en el lado del mástil (vaina) un poco más oscura
    vaina = int(max(2, 0.035 * Wp)); tex[:, :vaina] *= 0.86
    return tex

def dibujar_bandera(out, xp, yp, Wf, Hf, t, ss=3, glow=True):
    """Bandera atada en (xp, yp) (borde del mástil, punta) en coordenadas del cuadro, Wf×Hf px, flameando en t (s)."""
    Hh, Ww = out.shape[:2]
    amp = 0.075 * Hf
    W2, H2 = int(round(Wf * ss)), int(round(Hf * ss))
    if W2 < 6 or H2 < 6: return
    tex = textura_bandera(W2, H2)
    # malla inversa: para cada píxel de salida, (u, v) del paño. Desplazamiento vertical que crece hacia la punta.
    X0, Y0 = xp, yp - amp * 1.2
    OW, OH = Wf + 2, Hf + 2 * amp * 1.2 + 2
    ow, oh = int(math.ceil(OW * ss)), int(math.ceil(OH * ss))
    xs = (np.arange(ow) + 0.5) / ss; ys = (np.arange(oh) + 0.5) / ss
    u = np.clip(xs / Wf, 0, 1)
    fase = 2 * math.pi * (1.15 * u - 1.35 * t)
    dy = amp * (u ** 1.15) * np.sin(fase) + 0.25 * amp * (u ** 2) * np.sin(2.3 * fase + 1.0)
    compres = 1.0 - 0.035 * (1 - np.cos(fase)) * u               # el paño se acorta un poco en las ondas
    v = (ys[:, None] - amp * 1.2 - dy[None, :]) / Hf
    uu = (xs / (Wf * np.maximum(compres, 0.5)))[None, :].repeat(oh, 0)
    vv = v
    dentro = (uu >= 0) & (uu <= 1) & (vv >= 0) & (vv <= 1)
    mapx = (uu * (W2 - 1)).astype(np.float32); mapy = (vv * (H2 - 1)).astype(np.float32)
    col = cv2.remap(tex, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    # sombreado por la pendiente de la onda (luz desde arriba a la izquierda)
    pend = np.gradient(dy) * ss
    luz = 1.0 + np.clip(-0.9 * pend, -0.28, 0.22)
    col *= luz[None, :, None]
    a = dentro.astype(np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 0.6 * ss / 3)
    col = cv2.resize(col, (int(round(ow / ss)), int(round(oh / ss))), interpolation=cv2.INTER_AREA)
    a = cv2.resize(a, (col.shape[1], col.shape[0]), interpolation=cv2.INTER_AREA)
    ox, oy = int(round(X0)), int(round(Y0))
    h_, w_ = a.shape
    x0, y0 = max(0, ox), max(0, oy); x1, y1 = min(Ww, ox + w_), min(Hh, oy + h_)
    if x1 <= x0 or y1 <= y0: return
    sa = a[y0 - oy:y1 - oy, x0 - ox:x1 - ox][..., None]; sc = col[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    base = out[y0:y1, x0:x1].astype(np.float32)
    if glow:
        hal = cv2.GaussianBlur(sa[..., 0], (0, 0), max(2.0, 0.06 * Hf))[..., None] * 0.22
        base = base * (1 - hal) + CELESTE * hal
    out[y0:y1, x0:x1] = np.clip(base * (1 - sa) + sc * sa, 0, 255).astype(np.uint8)
