# v02 — Compone la animación de escalada intervenida, cuadro por cuadro (30 fps, 1080×1920):
#   1. borra los restos de la interfaz de Instagram de la grabación (cabecera "Reels · Amigos" que se apaga en los
#      primeros cuadros y su fantasma tenue que queda arriba);
#   2. quita la marca de agua NEURONVISUALS en TODOS los cuadros (marca_agua_v2.py) y no se vuelve a poner;
#   3. plano C (escalador de cerca): lo reencuadra 150 px a la derecha (la pared se extiende) para que la bandera
#      entre con el mismo tamaño relativo que en los otros planos;
#   4. rótulos en español y bandera celeste (rotulos_bandera.py), siguiendo la torre (seguir_torre.py);
#   5. remera negra del escalador como prenda articulada (remera2d.py, sobre esqueleto.py).
# Uso (Python con OpenCV): python componer.py SEQ_DIR TORRE.json AN_DIR SALIDA_DIR f0 f1
import os, sys, json, math
import numpy as np, cv2
from PIL import Image
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
from planos import PLANOS, FIN_ANIM
from rotulos_bandera import Plano, aplicar_rotulos, borrar_roja, dibujar_bandera
import remera2d
from marca_agua_v2 import quitar as quitar_marca_v2

seq, torre_js, an, outdir, f0, f1 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6])
os.makedirs(outdir, exist_ok=True)
torre = {int(k): v for k, v in json.load(open(torre_js)).items()}
# mástil en el cuadro de referencia de cada plano: (x centro, y punta, largo, ancho)
POSTES = {"A_general": (880.0, 202, 172, 3), "C_escalador": (896.5, 177, 311, 6), "D_general": (873.0, 278, 189, 3),
          "E_cima": (739.5, 597, 265, 4), "F_general_cima": (885.0, 373, 170, 3)}
DX_C = 150                                  # reencuadre del plano C
MARGEN = 14

def plano_de(f):
    for n, P in PLANOS.items():
        if P["cuadros"][0] <= f <= P["cuadros"][1]: return n, P
    return None, None

def leer(f): return np.asarray(Image.open(f"{seq}/{f:04d}.png").convert("RGB")).copy()

# fantasma de la cabecera (mínimo de muchos cuadros en las filas de arriba) y cuadro limpio para los primeros
fant = None
fp = os.path.join(an, "fantasma_ui.npy")
if os.path.exists(fp): fant = np.load(fp)
else:
    st = np.stack([np.asarray(Image.open(f"{seq}/{f:04d}.png").convert("RGB"))[:70].astype(np.float32) for f in range(7, 470, 6)])
    fant = np.clip(st.min(0) - 1.2, 0, None); np.save(fp, fant)
limpio7 = None

ma = np.load(os.path.join(an, "marca_agua.npz")); MA_AL = ma["alpha"]; MX0, MY0, MX1, MY1 = map(int, ma["caja"])
def quitar_marca(img):
    w = img[MY0:MY1, MX0:MX1].astype(np.float32); a = MA_AL[..., None]
    img[MY0:MY1, MX0:MX1] = np.clip((w - 255 * a) / np.maximum(1 - a, 0.2), 0, 255).astype(np.uint8)
def poner_marca(img):
    w = img[MY0:MY1, MX0:MX1].astype(np.float32); a = MA_AL[..., None]
    img[MY0:MY1, MX0:MX1] = np.clip(w * (1 - a) + 255 * a, 0, 255).astype(np.uint8)

def extender(img, dx, rng):
    """Agrega dx columnas a la derecha repitiendo la última por fila (pared, borde y cielo) con grano suave."""
    col = img[:, -6:].astype(np.float32).mean(1, keepdims=True)
    ext = np.repeat(col, dx, 1) + rng.normal(0, 1.2, (img.shape[0], dx, 1))
    return np.concatenate([img, np.clip(ext, 0, 255).astype(np.uint8)], 1)

# planos con torre
planos = {n: Plano(n, P, seq, POSTES[n], torre) for n, P in PLANOS.items() if P.get("rotulos")}

def tam_bandera(n):
    """Ancho y alto de la bandera (coordenadas de referencia del plano): ancho = largo del mástil, salvo que no entre."""
    xc, yt, Lp, wp = POSTES[n]; P = PLANOS[n]
    borde_der = 1080 + (DX_C if n == "C_escalador" else 0) - MARGEN
    room = 1e9
    for f in range(P["cuadros"][0], P["cuadros"][1] + 1):
        T = torre[f]; room = min(room, (borde_der - T["tx"]) / T["s"] - (xc + wp / 2))
    W = min(1.0 * Lp, room); return W, 0.62 * W
BANDERA = {n: tam_bandera(n) for n in planos}
json.dump({n: [round(w, 1), round(h, 1)] for n, (w, h) in BANDERA.items()}, open(os.path.join(an, "bandera_tam.json"), "w"))

for f in range(f0, f1 + 1):
    if f > FIN_ANIM: break
    rng = np.random.default_rng(f)
    img = leer(f)
    # 1. interfaz
    if f <= 6:
        global_lim = np.asarray(Image.open(f"{seq}/0007.png").convert("RGB"))[:70].astype(np.float32)
        img[:70] = np.clip(global_lim - fant, 0, 255).astype(np.uint8)
    else:
        img[:70] = np.clip(img[:70].astype(np.float32) - fant, 0, 255).astype(np.uint8)
    quitar_marca_v2(img, f)
    n, P = plano_de(f)
    pan = (n == "C_escalador")
    if pan:
        img = extender(img, DX_C, rng)
    if n in planos:
        T = torre[f]; s, tx, ty = T["s"], T["tx"], T["ty"]
        pl = planos[n]
        aplicar_rotulos(img, pl, (s, tx, ty), rng)
        xc, yt, Lp, wp = POSTES[n]
        # borrar la roja (caja amplia alrededor de la punta del mástil, con su resplandor)
        bx0, by0 = s * (xc - 6) + tx, s * (yt - 0.2 * Lp) + ty
        bx1, by1 = s * (xc + 0.75 * Lp) + tx, s * (yt + 0.55 * Lp) + ty
        borrar_roja(img, int(bx0), int(by0), int(bx1), int(by1))
        Wb, Hb = BANDERA[n]
        dibujar_bandera(img, s * (xc + wp / 2) + tx, s * (yt + 0.01 * Lp) + ty, s * Wb, s * Hb, (f - 1) / 30.0)
    remera2d.vestir(img, f, n)
    if pan:
        img = img[:, DX_C:DX_C + 1080].copy()
    Image.fromarray(img).save(os.path.join(outdir, f"{f:04d}.png"), compress_level=1)
print("listo", f0, f1)
