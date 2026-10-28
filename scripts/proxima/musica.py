# Música original de ROCCE_proxima, sintetizada (sin material de terceros), armada sobre la línea de tiempo del montaje.
# Re menor, ~104 BPM, grilla con origen en el primer corte (la ola). Progresión emocional por tramos:
#   intro   (gancho)          colchón grave casi quieto: tensión, deja la pregunta sola
#   pulso   (historia)        latido de bombo en 1 y 3, bajo en la tónica, acordes Rem–Sib; tic de charles desde C
#   respiro (tesis "con vos") se va la batería; acorde de Sib mayor abierto: alivio; subida hacia la oferta
#   subida  (oferta)          golpe; bombo en negras, bajo en contratiempo, palmas en 2 y 4, filtro que se abre
#                             (Rem–Sib–Fa–Do por compás); subida de 1 compás hacia la placa
#   pleno   (invitación)      golpe; mismo ritmo con todo abierto, charles en semicorcheas, acento en "FOUNDERS"
#   cola                      se corta la batería en un tiempo fuerte y queda el acorde (sin silencio final largo)
# Efectos (fx.wav, aparte para que no los aplaste la voz): roce de tela, golpes en los cortes clave, clics de los
# detalles, barrido al tachar "ALGÚN DÍA", subidas.
# Uso: python musica.py LINEA_DE_TIEMPO.json SALIDA_DIR   → SALIDA_DIR/musica.wav y SALIDA_DIR/fx.wav (48 kHz estéreo)
import sys, json, os
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
import soundfile as sf

tl, out = json.load(open(sys.argv[1])), sys.argv[2]; os.makedirs(out, exist_ok=True)
SR = 48000; DUR = tl["duracion"]; N = int(DUR * SR) + SR
M = tl["musica"]; BEAT = 60 / M["bpm"]; G0 = M["origen"]; SEC = M["tramos"]
rng = np.random.default_rng(7)
mus = np.zeros((N, 2)); fx = np.zeros((N, 2))
hz = lambda nota: 440 * 2 ** ((nota - 69) / 12)

def put(buf, sig, t0, g=1.0, pan=0.0):
    if sig.ndim == 1: sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1)
    i = int(round(t0 * SR)); j = min(N, i + len(sig))
    if j > max(i, 0): buf[max(i, 0):j] += g * sig[max(0, -i):j - i]

def filt(x, tipo, f, orden=2):
    return sosfilt(butter(orden, f, btype=tipo, fs=SR, output="sos"), x, axis=0)

def env(L, a, r, s=1.0):
    t = np.arange(L) / SR; e = np.minimum(1, t / max(a, 1e-4)) * s
    k = min(L, int(r * SR))
    if k > 0: e[-k:] *= np.linspace(1, 0, k) ** 1.5
    return e

def saw(f, L, det=0.0):
    t = np.arange(L) / SR; y = np.zeros(L); nh = int(min(40, 9000 / f))
    for k in range(1, nh + 1): y += np.sin(2 * np.pi * k * f * (1 + det) * t + rng.uniform(0, 6.28)) / k
    return y * 0.55

def pad(notas, L, brillo=1400):
    izq = sum(saw(hz(n), L, -0.004) + saw(hz(n), L, 0.003) for n in notas)
    der = sum(saw(hz(n), L, 0.004) + saw(hz(n), L, -0.002) for n in notas)
    st = np.stack([izq, der], 1) / (2 * len(notas)); return filt(st, "low", brillo)

def kick(g=1.0):
    L = int(0.42 * SR); t = np.arange(L) / SR
    f = 46 + 74 * np.exp(-t / 0.032); s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)
    s += 0.18 * rng.standard_normal(L) * np.exp(-t / 0.003); return g * s * np.minimum(1, t / 0.0015)

def hat(g=1.0, dec=0.028):
    L = int(0.12 * SR); t = np.arange(L) / SR
    return g * filt(rng.standard_normal(L), "high", 7000) * np.exp(-t / dec) * 0.6

def clap(g=1.0):
    L = int(0.35 * SR); t = np.arange(L) / SR; n = filt(rng.standard_normal(L), "band", [900, 2600])
    e = np.exp(-t / 0.09) * 0.6
    for d in (0.0, 0.011, 0.022): e += np.exp(-np.maximum(0, t - d) / 0.006) * (t >= d) * 0.5
    return g * n * e

def bajo(nota, L, g=1.0):
    t = np.arange(L) / SR; f = hz(nota); s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return g * np.tanh(1.6 * s) * env(L, 0.004, min(0.08, L / SR / 2))

def golpe(g=1.0):
    L = int(2.2 * SR); t = np.arange(L) / SR
    s = np.sin(2 * np.pi * np.cumsum(32 + 60 * np.exp(-t / 0.05)) / SR) * np.exp(-t / 0.55)
    s += filt(rng.standard_normal(L), "low", 1600) * np.exp(-t / 0.25) * 0.6; return g * s

def subida(d, g=1.0):
    L = int(d * SR); u = np.linspace(0, 1, L)
    n = rng.standard_normal(L); y = np.zeros(L); blk = 2048
    for i in range(0, L, blk):
        fc = 400 + 7000 * u[i] ** 2; y[i:i + blk] = filt(n[i:i + blk], "band", [fc * 0.7, min(fc * 1.4, 20000)])
    tono = np.sin(2 * np.pi * np.cumsum(180 + 700 * u ** 2) / SR) * 0.25
    return g * (y + tono) * u ** 2.2

def roce(d, g=1.0):
    L = int(d * SR); u = np.linspace(0, 1, L)
    return g * filt(rng.standard_normal(L), "band", [1800, 5200]) * np.sin(np.pi * u) ** 2

def barrido(g=1.0):
    L = int(0.22 * SR); u = np.linspace(0, 1, L); n = rng.standard_normal(L); y = np.zeros(L); blk = 512
    for i in range(0, L, blk):
        fc = 1500 + 7000 * u[i]; y[i:i + blk] = filt(n[i:i + blk], "band", [fc * 0.8, min(fc * 1.25, 20000)])
    return g * y * np.sin(np.pi * u) ** 1.5

def clic(g=1.0):
    L = int(0.06 * SR); t = np.arange(L) / SR
    s = (np.sin(2 * np.pi * 1500 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)) * np.exp(-t / 0.012)
    return g * s * np.minimum(1, t / 0.001)

def reverb(st, seg=1.8, mezcla=0.25):
    L = int(seg * SR); t = np.arange(L) / SR
    ir = [filt(rng.standard_normal(L), "low", 6000) * np.exp(-t / (seg / 6)) for _ in range(2)]
    w = np.stack([fftconvolve(st[:, c], ir[c])[:len(st)] for c in range(2)], 1)
    w *= np.sqrt(np.mean(st ** 2) / (np.mean(w ** 2) + 1e-12)); return st * (1 - mezcla) + w * mezcla

def tramo(nombre): return next(s for s in SEC if s["tipo"] == nombre)
def beats(a, b, paso=1.0):
    k0 = int(np.ceil((a - G0) / (BEAT * paso) - 1e-6)); out = []
    while G0 + k0 * BEAT * paso < b - 1e-6: out.append((k0, G0 + k0 * BEAT * paso)); k0 += 1
    return out

RE, SIB, FA, DO = [50, 53, 57], [46, 50, 53], [45, 48, 53], [43, 48, 52]     # Rem, Sib (1.ª inv. baja), Fa (2.ª), Do
RAIZ = {0: 38, 1: 34, 2: 41, 3: 36}
# ---------- intro: colchón grave ----------
a = tramo("intro"); L = int((a["hasta"] - a["desde"] + 0.6) * SR)
c = pad(RE, L, 700) * env(L, 0.8, 0.6)[:, None] * 0.55 + np.stack([np.sin(2 * np.pi * hz(38) * np.arange(L) / SR)] * 2, 1) * env(L, 1.0, 0.6)[:, None] * 0.25
put(mus, c, a["desde"])
# ---------- pulso ----------
p = tramo("pulso"); compas = 4 * BEAT
for k, t in beats(p["desde"], p["hasta"]):
    if k % 2 == 0: put(mus, kick(0.55), t)
    if k % 4 == 0:
        acorde = RE if (k // 8) % 2 == 0 else SIB; L = int(compas * SR)
        put(mus, pad(acorde, L, 1100) * env(L, 0.25, 0.4)[:, None] * 0.42, t)
        put(mus, bajo(RAIZ[0] if acorde is RE else RAIZ[1], int(compas * 0.9 * SR), 0.30), t)
for k, t in beats(p.get("charles_desde", p["desde"]), p["hasta"], 0.5):
    put(mus, hat(0.10 if k % 2 else 0.16), t, pan=0.25)
# ---------- respiro ----------
r = tramo("respiro"); L = int((r["hasta"] - r["desde"] + 1.2) * SR)
put(mus, pad([46, 53, 57, 60, 62], L, 2200) * env(L, 0.35, 1.0)[:, None] * 0.55, r["desde"] - 0.05)
# ---------- subida y pleno ----------
prog = [RE, SIB, FA, DO]
def groove(a, b, nivel, pleno):
    for k, t in beats(a, b):
        u = (t - a) / max(b - a, 1e-6); kb = k - int(round((a - G0) / BEAT))
        put(mus, kick(0.75 if pleno else 0.55 + 0.2 * u), t)
        if kb % 2 == 1 and (pleno or kb >= 4): put(mus, clap(0.30 if pleno else 0.22), t, pan=-0.1)
        if kb % 4 == 0:
            i = (kb // 4) % 4; L = int(4 * BEAT * SR)
            br = 3200 if pleno else 700 + 2200 * u
            put(mus, pad(prog[i], L, br) * env(L, 0.05, 0.3)[:, None] * nivel, t)
        i = ((kb // 4) % 4); raiz = [38, 34, 41, 36][i]
        put(mus, bajo(raiz, int(BEAT * 0.45 * SR), 0.34), t + BEAT / 2)
    for k, t in beats(a, b, 0.25 if pleno else 0.5):
        put(mus, hat(0.08 + (0.06 if k % 2 == 0 else 0.0)), t, pan=0.3)
s = tramo("subida"); g = tramo("pleno"); cola = tramo("cola")
groove(s["desde"], s["hasta"], 0.36, False)
groove(g["desde"], g["hasta"], 0.40, True)
L = int((cola["hasta"] - cola["desde"] + 0.5) * SR)
put(mus, pad(prog[0] + [62], L, 2600) * env(L, 0.02, max(0.3, L / SR - 0.2))[:, None] * 0.5, cola["desde"])
put(mus, bajo(38, int(1.0 * SR), 0.34), cola["desde"]); put(mus, kick(0.75), cola["desde"])
mus = reverb(mus, 1.6, 0.22)
# ---------- efectos ----------
for e in tl["fx"]:
    t, tp, gn = e["t"], e["tipo"], 10 ** (e.get("db", 0) / 20)
    if tp == "golpe": put(fx, golpe(gn), t)
    elif tp == "subida": put(fx, subida(e["dur"], gn), t - e["dur"])
    elif tp == "roce": put(fx, roce(e["dur"], gn), t)
    elif tp == "barrido": put(fx, barrido(gn), t)
    elif tp == "clic": put(fx, clic(gn), t)
fx = reverb(fx, 1.2, 0.18)
for nombre, buf in (("musica", mus), ("fx", fx)):
    buf = buf[:int(DUR * SR)]; pk = np.abs(buf).max()
    buf = buf / (pk + 1e-9) * 10 ** (-3 / 20)                     # pico −3 dBFS; los niveles se ajustan en la mezcla
    sf.write(os.path.join(out, nombre + ".wav"), buf, SR, subtype="PCM_24")
    print(f"{nombre}.wav: {len(buf) / SR:.2f} s")
