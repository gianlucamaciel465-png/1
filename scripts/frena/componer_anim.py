# Compone la parte animada de ROCCE_lo_que_te_frena sobre R1 (Neuron Visuals), cuadro a cuadro (60 fps → 30 fps):
#   1. borra los rótulos en inglés (máscara del rótulo seguido + relleno desde el entorno) y escribe los nuevos en
#      español con la misma letra, alineados al mismo borde derecho, con la opacidad y el movimiento del original;
#   2. viste al protagonista con la remera blanca de Roccé (remera_heroe.py);
#   3. cambia SUCCESS por "GIVE HISTORY / YOUR NAME." con el mismo brillo y la misma aparición desde el centro;
#   4. agrega el gancho "Lo que te frena / no está adelante." hasta que se corta la soga.
# Uso (Python con OpenCV): python componer_anim.py SEQ60_DIR pose60_fix.json rot60.json TEXTOS_DIR SALIDA_DIR
#   (pose60_fix.json = pose_heroe.py + pose_salto.py)
import sys, os, json, math
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from remera_heroe import cargar_pose, dibujar
from rotulos import Estilo, capa_rgba

seq, pose_json, rot_json, textos, outdir = sys.argv[1:6]
os.makedirs(outdir, exist_ok=True)
F_INI, F_FIN = 12, 436                 # 0,20 s → 7,27 s del original (cuadros de 60 fps; se toma uno de cada dos)
F_SOGA = 240                           # la soga se corta (4,0 s)
F_EXITO = 334                          # empieza a aparecer SUCCESS
REF, M = 30, 6
CAJAS = {"FEAR": (80, 1072, 185, 1096), "OPINIONS": (122, 982, 343, 1007), "DOUBT": (271, 926, 414, 951),
         "LAZINESS": (357, 880, 575, 905), "EXCUSES": (492, 750, 689, 775)}
NUEVOS = {"FEAR": "MIEDO", "OPINIONS": "QUÉ DIRÁN", "DOUBT": "DUDAS", "LAZINESS": "FIACA", "EXCUSES": "EXCUSAS"}
# v02: el villano definido por Gianluca es comodidad, fiaca, excusas, miedo y qué dirán → ROTULO_DOUBT=COMODIDAD
NUEVOS["DOUBT"] = os.environ.get("ROTULO_DOUBT", NUEVOS["DOUBT"])

def leer(f): return np.asarray(Image.open(f"{seq}/{f + 1:04d}.png").convert("RGB"))

# máscaras de las letras originales (cuadro de referencia), igual que en seguir_rotulos.py
a0 = leer(REF).astype(np.float32); g0 = a0.mean(2)
mask_t = {}
for k, (x0, y0, x1, y1) in CAJAS.items():
    t = g0[y0 - M:y1 + 1 + M, x0 - M:x1 + 1 + M]
    sub = a0[y0 - M:y1 + 1 + M, x0 - M:x1 + 1 + M]; sat = sub.max(2) - sub.min(2)
    m = (t > 100) & (sat < 30); m[:M - 2, :] = m[-(M - 2):, :] = False; m[:, :M - 2] = m[:, -(M - 2):] = False
    if k == "OPINIONS":
        yy, xx = np.mgrid[0:t.shape[0], 0:t.shape[1]]
        m &= np.hypot(xx - (362 - (x0 - M)), yy - (996 - (y0 - M))) > 22
    mask_t[k] = cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))   # incluye el halo

rot = json.load(open(rot_json))
def rot_at(k, f):
    e = rot[k].get(str(f))
    return (e["x"], e["y"], e["op"], e["score"]) if e else None
def op_suave(k, f):
    v = [rot_at(k, g)[2] for g in range(f - 2, f + 3) if rot_at(k, g)]
    return float(np.median(v)) if v else 0.0

est_rot = Estilo(cap=26, gap=0.43)
nuevo = {k: est_rot.linea(t) for k, t in NUEVOS.items()}
est_exito = Estilo(cap=46, gap=0.45)
lemas = [est_exito.linea("GIVE HISTORY"), est_exito.linea("YOUR NAME.")]

pose = cargar_pose(pose_json, F_INI, 464)
def rotv(v, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a); return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])
def brazos_de(f, p):
    N, P, r = np.array(p["N"]), np.array(p["P"]), p["r"]
    u = (P - N) / np.linalg.norm(P - N)
    if f >= 334:      # brazos en alto (medido en el cuadro 396, relativo al torso; ya arriba desde el 334)
        return {"cerca": (N + np.array([-0.68 * r, 0]) + 1.16 * r * u, rotv(-u, -31)),
                "lejos": (N + np.array([0.92 * r, 0]) + 0.76 * r * u, rotv(-u, 35))}
    d1 = np.array([math.cos(p["a1"]), math.sin(p["a1"])]); r1 = np.array(p["raiz1"])
    return {"cerca": (r1, d1), "lejos": (r1 + rotv(d1, -90) * 0.25 * r, rotv(d1, -10))}

def pegar(dst, rgba, x, y):
    """Compone una capa RGBA float (0–1) en dst (float 0–255) con esquina (x, y), recortando al cuadro."""
    h, w = rgba.shape[:2]; H, W = dst.shape[:2]
    xa, ya, xb, yb = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if xb <= xa or yb <= ya: return
    s = rgba[ya - y:yb - y, xa - x:xb - x]; al = s[..., 3:4]
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - al) + s[..., :3] * 255 * al

def blur_mov(rgba, vx, vy, k=1.0):
    sp = math.hypot(vx, vy) * k
    if sp < 2: return rgba
    n = int(min(41, round(sp))) | 1; ker = np.zeros((n, n), np.float32); c = n // 2; ux, uy = vx / math.hypot(vx, vy), vy / math.hypot(vx, vy)
    cv2.line(ker, (int(round(c - ux * c)), int(round(c - uy * c))), (int(round(c + ux * c)), int(round(c + uy * c))), 1.0, 1)
    ker /= ker.sum(); pad = n
    big = np.pad(rgba, ((pad, pad), (pad, pad), (0, 0)))
    prem = big.copy(); prem[..., :3] *= prem[..., 3:4]; prem = cv2.filter2D(prem, -1, ker)
    a = prem[..., 3:4]
    return np.concatenate([np.where(a > 1e-4, prem[..., :3] / np.maximum(a, 1e-4), 0), a], -1), pad

gancho = np.asarray(Image.open(os.path.join(textos, "gancho.png")), np.float32) / 255

k_out = 0
for f in range(F_INI, F_FIN + 1, 2):
    fr = leer(f).copy()
    # 1) borrar rótulos en inglés
    borrar = np.zeros(fr.shape[:2], np.uint8); dibujos = []
    for k in CAJAS:
        e = rot_at(k, f)
        if not e: continue
        x, y, op, sc = e; op = op_suave(k, f)
        if op < 0.02: continue
        m = mask_t[k]; X, Y = int(round(x)) - M, int(round(y)) - M
        h, w = m.shape; xa, ya, xb, yb = max(0, X), max(0, Y), min(fr.shape[1], X + w), min(fr.shape[0], Y + h)
        if xb > xa and yb > ya: borrar[ya:yb, xa:xb] |= m[ya - Y:yb - Y, xa - X:xb - X]
        pa, pb = rot_at(k, f - 1), rot_at(k, f + 1)
        vx, vy = ((pb[0] - pa[0]) / 2, (pb[1] - pa[1]) / 2) if pa and pb else (0, 0)
        dibujos.append((k, x, y, min(1.0, op), vx, vy))
    if borrar.any():
        fr = cv2.inpaint(fr, borrar * 255, 4, cv2.INPAINT_TELEA)
    # 2) remera
    p = pose.get(f)
    if p is not None:
        pa, pb = pose.get(f - 1, p), pose.get(f + 1, p)
        vel = ((pb["H"][0] - pa["H"][0]) * 0.5, (pb["H"][1] - pa["H"][1]) * 0.5)   # desplazamiento por cuadro de 60 fps (cabeza: estable)
        fre = float(np.clip((f - 312) / 28, 0, 1)); est = float(np.clip((f - 340) / 14, 0, 1))
        fr = dibujar(fr, p, frente=fre, brazos=brazos_de(f, p), vel=vel, estampado=est)
    out = fr.astype(np.float32)
    # 3) rótulos nuevos (mismo borde derecho y misma línea de mayúsculas que el original)
    for k, x, y, op, vx, vy in dibujos:
        m, top = nuevo[k]; x1 = x + (CAJAS[k][2] - CAJAS[k][0]) + 1
        rgba = capa_rgba(m); rgba[..., 3] *= op
        X, Y = int(round(x1 - m.shape[1])), int(round(y - top))
        b = blur_mov(rgba, vx, vy)
        if isinstance(b, tuple): rgba, pad = b; X -= pad; Y -= pad
        pegar(out, rgba, X, Y)
    # 4) SUCCESS → GIVE HISTORY / YOUR NAME.
    if f >= F_EXITO:
        y0, y1, x0, x1 = 400, 572, 270, 760
        top, bot = out[y0 - 1, x0:x1], out[y1, x0:x1]
        t = np.linspace(0, 1, y1 - y0)[:, None, None]
        out[y0:y1, x0:x1] = top[None] * (1 - t) + bot[None] * t
        prog = (f - F_EXITO) / 10.0
        capa = np.zeros(out.shape[:2], np.float32)
        cx = 513.5
        for (m, top_), ytop in zip(lemas, (424, 494)):
            X = int(round(cx - m.shape[1] / 2)); Y = int(round(ytop - top_))
            mm = m.astype(np.float32) / 255
            d = np.abs(np.arange(m.shape[1]) + X - cx) / 300.0
            rev = np.clip((prog * 1.15 - d) / 0.18, 0, 1)[None, :] * np.clip((f - F_EXITO + 1) / 4, 0, 1)
            hh, ww = mm.shape; capa[Y:Y + hh, X:X + ww] = np.maximum(capa[Y:Y + hh, X:X + ww], mm * rev)
        glow = cv2.GaussianBlur(capa, (0, 0), 7) * 0.85 + cv2.GaussianBlur(capa, (0, 0), 18) * 0.35
        bg = out / 255
        bg = 1 - (1 - bg) * (1 - np.clip(glow, 0, 1)[..., None])
        out = (bg * (1 - capa[..., None]) + capa[..., None]) * 255
    # 5) gancho hasta que se corta la soga
    ag = 1.0 if f < F_SOGA - 4 else max(0.0, 1 - (f - (F_SOGA - 4)) / 6)
    if ag > 0:
        al = gancho[..., 3:4] * ag
        out = out * (1 - al) + gancho[..., :3] * 255 * al
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(outdir, "%04d.png" % k_out))
    k_out += 1
    if k_out % 20 == 0: print("cuadro", k_out, "(original", f, ")", flush=True)
print("listo:", k_out, "cuadros")
