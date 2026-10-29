# ROCCE_01_HIELO_REVELACION v02 — paso 1: la remera negra adentro del hielo REAL de la referencia.
# Para cada cuadro de los planos A (golpes), C (levantar) y D (caída y rotura):
#   1. modelo por píxel  observado = s·c_b + w   (reemplazo.resolver): s = tela visible, w = luz que suma el hielo;
#   2. el logo blanco del jogger se borra rellenando s y w desde la tela de alrededor (máscara del cuadro clave
#      llevada con la homografía del seguimiento, barrida con el movimiento del cuadro);
#   3. la tela bordó pasa a ser la remera negra: nuevo = s·remera(x) + w, con el estampado REAL de la espalda
#      (textura_plegada.py) ubicado con la homografía textura → cuadro clave → cuadro, con el mismo desenfoque
#      óptico que el logo original (σ ≈ 1 px medido) y el desenfoque de movimiento del cuadro (sub-cuadros);
#   4. solo dentro del bloque (polígono del cuadro clave seguido con la homografía) y nunca en las manos
#      (polígonos de exclusión seguidos + piel por color fuera de la tela).
# Todo lo que el hielo pone delante (escarcha, burbujas, brillos, esquirlas, la herramienta, las manos) queda igual.
# Uso: python componer_hielo.py CUADROS_DIR SEGUIMIENTO.json TEXTURA.png SALIDA_DIR DESENFOQUE.json [cuadros,...]
#   (DESENFOQUE.json = desenfoque.py: desenfoque extra de cada cuadro medido sobre el logo del jogger)
import os, sys, json
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reemplazo import resolver

src, seg, texp, out, desf = sys.argv[1:6]
solo = set(int(x) for x in sys.argv[6].split(",")) if len(sys.argv) > 6 else None
os.makedirs(out, exist_ok=True)
TONO = 0.40          # algodón negro ≈ 0,4 × la luminancia (lineal) del bordó con la misma luz (comparado a ojo con 0,3)
CONTRASTE_ESTAMPA = 1.0   # contraste del estampado como en la foto (0,3 y 0,6 lo dejaban ilegible dentro del hielo)
SIGMA = 1.0          # desenfoque óptico medido en el logo del jogger (px a 512 de ancho)
OBTURADOR = 0.5      # fracción del intervalo entre cuadros con el obturador abierto (se comprueba en la caída)
TELA = 30.0
# Cuadro clave de cada plano (coordenadas de ese cuadro, 512×1108):
#   quad = cara visible de la prenda (cuello arriba); logo = caja del logo del jogger;
#   bloque = donde puede verse tela (cara, franja superior, caras laterales); manos = exclusión;
#   franja = tela vista a través del canto o de una cara lateral del hielo: el hielo le corre el tono (rojo con
#            poco azul, parecido a la piel), así que ahí vale un criterio de rojo amplio y no el control de piel;
#            "anillo" = banda de 18 px alrededor de la cara de la prenda (planos sin manos).
CLAVES = {
    345: dict(quad=[[52, 356], [500, 326], [502, 598], [50, 622]], logo=(360, 446, 410, 458),
              bloque=[[-60, 280], [600, 260], [600, 690], [-60, 700]], manos=[], franja="anillo", piel=False),
    452: dict(quad=[[100, 400], [440, 388], [446, 645], [98, 636]], logo=(295, 380, 435, 488),
              bloque=[[96, 392], [150, 366], [300, 349], [430, 336], [490, 338], [498, 380], [496, 515], [478, 536],
                      [466, 600], [455, 646], [370, 652], [250, 652], [110, 650], [58, 648], [50, 620],
                      [56, 560], [76, 515], [84, 470], [92, 420]],
              manos=[[[0, 420], [70, 430], [80, 470], [76, 515], [56, 560], [48, 620], [56, 660], [0, 700]],
                     [[480, 538], [500, 522], [512, 515], [512, 800], [360, 800], [366, 654], [458, 650], [468, 600]]],
              franja=[[[96, 392], [150, 366], [300, 349], [430, 336], [470, 340], [470, 392], [100, 404]],
                      [[438, 338], [498, 345], [498, 515], [478, 536], [466, 600], [450, 646], [438, 600]]],
              piel=True),
    490: dict(quad=[[277, 335], [482, 447], [400, 585], [165, 442]], logo=(370, 430, 452, 482),
              bloque=[[-300, -300], [812, -300], [812, 1400], [-300, 1400]], manos=[], franja="anillo", piel=False),
}
S = json.load(open(seg))
_d = {int(k): v for k, v in json.load(open(desf)).items()}
EXTRA = {}
for f in _d:                                                   # mediana de 3 cuadros del mismo plano: sin saltos
    vec = [_d[g] for g in (f - 1, f, f + 1) if g in _d and S[str(g)]["plano"] == S[str(f)]["plano"]]
    EXTRA[f] = float(np.median(vec))
tex = np.asarray(Image.open(texp).convert("RGB")).astype(np.float32)
th, tw = tex.shape[:2]
ESQ_TEX = np.float32([[0, 0], [tw - 1, 0], [tw - 1, th - 1], [0, th - 1]])
W, H = 512, 1108

def leer(f):
    return np.asarray(Image.open(f"{src}/{f:04d}.png").convert("RGB")).astype(np.float32)

def poligono(p):
    m = np.zeros((H, W), np.float32)
    if len(p): cv2.fillPoly(m, [np.int32(p)], 1.0)
    return m

claves = {}
for k, c in CLAVES.items():
    im = leer(k)
    x0, x1, y0, y1 = c["logo"]
    G = im[y0:y1, x0:x1, 1]
    m = (G > np.percentile(G, 50) + 35).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    i = 1 + int(np.argmax(st[1:, 4]))
    logo = np.zeros((H, W), np.uint8); logo[y0:y1, x0:x1] = (lab == i)
    logo = cv2.dilate(logo, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(np.float32)
    Hq = cv2.getPerspectiveTransform(ESQ_TEX, np.float32(c["quad"]))
    manos = np.zeros((H, W), np.float32)
    for p in c["manos"]: manos = np.maximum(manos, poligono(p))
    if c["franja"] == "anillo":
        franja = cv2.dilate(poligono(c["quad"]), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (37, 37)))
    else:
        franja = np.zeros((H, W), np.float32)
        for p in c["franja"]: franja = np.maximum(franja, poligono(p))
    claves[k] = dict(logo=logo, Hq=Hq, bloque=poligono(c["bloque"]), manos=manos, franja=franja,
                     quad=poligono(c["quad"]), piel=c["piel"])

def homografia(f):
    return np.array(S[str(f)]["H"]) if str(f) in S else None

# color de la tela por plano (solo importa su tono; la escala la absorbe s): dentro de la cara de la prenda, tono
# bordó, mitad más iluminada, el 40 % más saturado (sin escarcha); mediana del plano
planos = {}
for f, e in S.items(): planos.setdefault(e["plano"], []).append(int(f))
cbs = {}
for p, fs in planos.items():
    vals = []
    for f in sorted(fs)[::3]:
        e = S[str(f)]; Hf = homografia(f); obs = leer(f)
        q = cv2.warpPerspective(claves[e["clave"]]["quad"], Hf, (W, H), flags=cv2.INTER_NEAREST) > 0.5
        R, G, B = obs[..., 0], obs[..., 1], obs[..., 2]; rg, bg = R - G, B - G
        m = q & (rg > 8) & (bg > 0.35 * rg) & (bg < rg)
        if m.sum() < 300: continue
        px = obs[m]; lum = px.mean(1)
        px = px[(lum > np.percentile(lum, 50)) & (lum < np.percentile(lum, 95))]   # sin sombras aplastadas
        sat = (px[:, 0] - px[:, 1]) / (px.mean(1) + 5)      # tela sin escarcha = la más saturada
        vals.append(np.median(px[sat > np.percentile(sat, 60)], 0))
    cbs[p] = np.median(np.array(vals), 0).astype(np.float32)
    print("plano", p, "c_b", cbs[p].round(1), "(", len(vals), "muestras )")

def lin(v): return (np.clip(v, 0, 255) / 255.0) ** 2.2
def gam(l): return 255.0 * np.clip(l, 0, 1) ** (1 / 2.2)
def luminancia(c): return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])
# textura en luz lineal relativa a la tela (tela = 1), con el contraste del estampado de la foto (≈ 150 sobre 30).
tex_rel = lin(tex) / lin(TELA)
tex_rel = 1.0 + (tex_rel - 1.0) * CONTRASTE_ESTAMPA

def tapar(x, m8, esc):
    x8 = np.clip(x * esc, 0, 255).astype(np.uint8)
    return cv2.inpaint(x8, m8, 6, cv2.INPAINT_TELEA).astype(np.float32) / esc

def subcuadros(f):
    """Homografías de cuadro clave → cuadro en instantes dentro del obturador (interpolando esquinas)."""
    e = S[str(f)]; Hf = homografia(f)
    Ha, Hb = homografia(f - 1), homografia(f + 1)
    if Ha is None or S[str(f - 1)]["clave"] != e["clave"]: Ha = None
    if Hb is None or S[str(f + 1)]["clave"] != e["clave"]: Hb = None
    ref = np.float32([[0, 0], [W, 0], [W, H], [0, H]]).reshape(-1, 1, 2)
    cf = cv2.perspectiveTransform(ref, Hf)
    ca = cv2.perspectiveTransform(ref, Ha) if Ha is not None else None
    cb_ = cv2.perspectiveTransform(ref, Hb) if Hb is not None else None
    if ca is None and cb_ is not None: ca = 2 * cf - cb_
    if cb_ is None and ca is not None: cb_ = 2 * cf - ca
    if ca is None: return [Hf]
    out = []
    for t in np.linspace(-OBTURADOR / 2, OBTURADOR / 2, 9):
        c = cf + t * (cb_ - cf) if t >= 0 else cf + t * (cf - ca)
        out.append(cv2.getPerspectiveTransform(ref.reshape(-1, 2), np.float32(c.reshape(-1, 2))))
    return out

restos = []
for f in sorted(int(x) for x in S):
    if solo and f not in solo: continue
    e = S[str(f)]; k = e["clave"]; Hf = homografia(f); cb = cbs[e["plano"]]; C = claves[k]
    obs = leer(f)
    _, _, res = resolver(obs, cb)                              # residuo del modelo (en valores de pantalla)
    # el reemplazo se hace en luz lineal: la luz de la tela y la del hielo se suman en radiancia, no en gamma
    ol, cbl = lin(obs), lin(cb)
    s, w, _ = resolver(ol, cbl); s = np.clip(s, 0, 12.0); w = np.clip(w, 0, 1.0)
    rec0 = s[..., None] * cbl + w[..., None]
    Hs = subcuadros(f)
    # logo del jogger (barrido con el movimiento)
    lg = np.max([cv2.warpPerspective(C["logo"], h, (W, H), flags=cv2.INTER_LINEAR) for h in Hs], 0)
    m8 = (lg > 0.1).astype(np.uint8)
    s1, w1 = s, w
    if m8.any():
        s1 = np.where(m8 > 0, tapar(s, m8, 21.0), s); w1 = np.where(m8 > 0, tapar(w, m8, 255.0), w)
    lgs = np.clip(cv2.GaussianBlur(m8.astype(np.float32), (0, 0), 1.0) * 1.5, 0, 1)
    # zonas seguidas
    seg_ = lambda m: cv2.warpPerspective(m, Hf, (W, H), flags=cv2.INTER_LINEAR)
    bloque, manos, franja, quad = seg_(C["bloque"]), seg_(C["manos"]), seg_(C["franja"]), seg_(C["quad"])
    R, G, B = obs[..., 0], obs[..., 1], obs[..., 2]
    rg, bg = R - G, B - G; razon = bg / np.maximum(rg, 1.0)
    piel = np.zeros((H, W), np.float32)
    if C["piel"]:
        piel = ((rg > 25) & (razon < 0.33) & (G > 55)).astype(np.float32) * (1 - np.maximum(franja, quad))
        piel = np.clip(cv2.GaussianBlur(cv2.dilate(piel, np.ones((5, 5), np.uint8)), (0, 0), 1.5) * 1.5, 0, 1)
    # fuera de la cara de la prenda solo cuenta lo que tiene tono bordó (B−G ≈ 0,5·(R−G)): así el piso cálido
    # y el hielo que lo deja ver no se tocan; en la cara (y en la franja del canto) entra todo, también bajo escarcha
    tono = np.clip((razon - 0.30) / 0.10, 0, 1) * np.clip((rg - 4) / 6, 0, 1)
    cara = cv2.GaussianBlur(cv2.dilate(quad, np.ones((7, 7), np.uint8)), (0, 0), 2.0)
    tono2 = np.clip((rg - 9) / 8, 0, 1) * np.clip((bg + 3) / 4, 0, 1)        # rojo amplio (canto del hielo)
    franja = cv2.GaussianBlur(franja, (0, 0), 2.0)
    zona = cv2.GaussianBlur(bloque * (1 - manos), (0, 0), 1.5) * np.maximum((1 - piel) * np.maximum(tono, cara),
                                                                          franja * tono2)
    okm = np.clip((44 - res) / 16, 0, 1)
    wgt = np.maximum(zona * okm, lgs * (1 - np.clip(manos, 0, 1)))
    # remera: textura llevada al cuadro con desenfoque de movimiento + óptico
    rem = np.mean([cv2.warpPerspective(tex_rel, h @ C["Hq"], (W, H), flags=cv2.INTER_AREA,
                                       borderMode=cv2.BORDER_CONSTANT, borderValue=(1.0, 1.0, 1.03 ** 2.2))
                   for h in Hs], 0)
    rem = cv2.GaussianBlur(rem, (0, 0), float(np.hypot(SIGMA, EXTRA.get(f, 0.0))))
    rem = rem * (TONO * luminancia(cbl))
    nuevo = s1[..., None] * rem + w1[..., None]
    # lo que el modelo no explica (residuo) se conserva en luminancia; su color (restos del tono bordó con otra
    # tinta, p. ej. la tela vista por el canto del hielo) se neutraliza dentro de la zona de tela
    r = ol - rec0
    neutra = zona * np.clip(s / 0.3, 0, 1)                    # solo donde hay tela (no en piso ni hielo claro)
    r_neutro = r - (r - r.mean(2, keepdims=True)) * neutra[..., None]
    base = ol + wgt[..., None] * (nuevo + r_neutro - ol)
    o = gam(base * (1 - lgs[..., None]) + nuevo * lgs[..., None])          # en el logo, sin residuo
    Ro, Go, Bo = o[..., 0], o[..., 1], o[..., 2]
    resto = ((Ro - Go > 14) & ((Bo - Go) > 0.3 * (Ro - Go)) & (Go < 130) & (bloque > 0.5) & (manos < 0.5)).sum()
    restos.append((f, int(resto)))
    Image.fromarray(np.round(o).astype(np.uint8)).save(f"{out}/{f:04d}.png", compress_level=1)
print("píxeles bordó restantes dentro del bloque (máx 5):", sorted(restos, key=lambda x: -x[1])[:5])
