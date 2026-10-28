# Sigue la torre (los siete renglones de la pared) en cada plano de la referencia de escalada.
# Por renglón: plantilla del cuadro de referencia del plano; búsqueda por correlación normalizada en posición y escala
# alrededor de lo previsto. Por cuadro: ajuste de semejanza (escala + traslación, sin giro) con los renglones bien
# encontrados (puntaje alto), descartando los que no encajan (tapados por el escalador o fuera de cuadro).
# Salida: por cuadro, s, tx, ty tales que punto_en_cuadro = s · punto_en_referencia + t.
# Uso (Python con OpenCV): python seguir_torre.py SEQ_DIR SALIDA.json
import sys, json
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from planos import PLANOS

seq, out = sys.argv[1], sys.argv[2]
M, PAD = 6, 300
def gris(f):
    a = np.asarray(Image.open(f"{seq}/{f:04d}.png").convert("L"), np.float32)
    return np.pad(a, PAD)

res = {}
for nombre, P in PLANOS.items():
    if not P.get("rotulos"): continue
    ref = P["ref"]; g0 = gris(ref)
    tpl = {}
    for k, (x, y, w, h) in P["rotulos"].items():
        tpl[k] = g0[PAD + y - M:PAD + y + h + M, PAD + x - M:PAD + x + w + M].copy()
    cen0 = {k: np.array([x + w / 2, y + h / 2]) for k, (x, y, w, h) in P["rotulos"].items()}
    def seguir(orden):
        st = {"s": 1.0, "t": np.zeros(2), "v": np.zeros(3)}; salida = {}
        for f in orden:
            g = gris(f); pred_s = st["s"] + st["v"][0]; pred_t = st["t"] + st["v"][1:]
            obs = {}
            for k, T in tpl.items():
                c = pred_s * cen0[k] + pred_t
                best = (-1, None, None)
                for s in pred_s * np.array([0.992, 0.996, 1.0, 1.004, 1.008]):
                    Ts = cv2.resize(T, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
                    th, tw = Ts.shape; R = 34
                    x0 = int(round(PAD + c[0] - tw / 2 - R)); y0 = int(round(PAD + c[1] - th / 2 - R))
                    win = g[max(0, y0):y0 + th + 2 * R, max(0, x0):x0 + tw + 2 * R]
                    if win.shape[0] < th + 2 or win.shape[1] < tw + 2: continue
                    r = cv2.matchTemplate(win, Ts, cv2.TM_CCOEFF_NORMED)
                    _, mx, _, loc = cv2.minMaxLoc(r)
                    if mx > best[0]:
                        best = (mx, s, np.array([max(0, x0) + loc[0] + tw / 2 - PAD, max(0, y0) + loc[1] + th / 2 - PAD]))
                if best[1] is not None: obs[k] = best
            buenos = [k for k, o in obs.items() if o[0] > 0.80]
            def ajustar(ks):
                A = []; b = []
                for k in ks:
                    p, q = cen0[k], obs[k][2]
                    A += [[p[0], 1, 0], [p[1], 0, 1]]; b += [q[0], q[1]]
                sol, *_ = np.linalg.lstsq(np.array(A), np.array(b), rcond=None)
                return sol[0], sol[1:]
            if len(buenos) >= 2:
                s_, t_ = ajustar(buenos)
                resid = {k: np.linalg.norm(s_ * cen0[k] + t_ - obs[k][2]) for k in buenos}
                ok = [k for k in buenos if resid[k] < 3.0]
                if len(ok) >= 2 and len(ok) < len(buenos): s_, t_ = ajustar(ok)
            elif len(buenos) == 1:
                k = buenos[0]; s_ = pred_s; t_ = obs[k][2] - s_ * cen0[k]; ok = buenos
            else:
                s_, t_, ok = pred_s, pred_t, []
            if salida: st["v"] = 0.5 * st["v"] + 0.5 * np.array([s_ - st["s"], *(t_ - st["t"])])
            st["s"], st["t"] = float(s_), np.array(t_, float)
            salida[f] = {"s": float(s_), "tx": float(t_[0]), "ty": float(t_[1]), "ok": ok,
                         "punt": {k: round(float(o[0]), 3) for k, o in obs.items()}}
        return salida
    a, b = P["cuadros"]
    ida = seguir(range(ref, b + 1)); vuelta = seguir(range(ref, a - 1, -1))
    seq_f = {**vuelta, **ida}
    # suavizado (la cámara se mueve suave): media móvil de 5 cuadros dentro del plano
    fs = sorted(seq_f); arr = np.array([[seq_f[f]["s"], seq_f[f]["tx"], seq_f[f]["ty"]] for f in fs])
    pad = np.pad(arr, ((2, 2), (0, 0)), mode="edge"); sm = np.stack([np.convolve(pad[:, c], np.ones(5) / 5, "valid") for c in range(3)], 1)
    for i, f in enumerate(fs):
        seq_f[f].update({"s": float(sm[i, 0]), "tx": float(sm[i, 1]), "ty": float(sm[i, 2]), "plano": nombre})
        res[f] = seq_f[f]
    malos = [f for f in fs if len(seq_f[f]["ok"]) < 3]
    print(nombre, f"{a}-{b}", "cuadros con <3 renglones firmes:", malos[:20], len(malos))
json.dump(res, open(out, "w"), indent=0)
