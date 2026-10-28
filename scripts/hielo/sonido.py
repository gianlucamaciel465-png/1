# Sonido de la parte 3D de ROCCE_01_HIELO_REVELACION, sintetizado y sincronizado con la escena (escena.json):
#   - cada golpe: barrido del hacha, golpe grave, chasquido de la grieta, "tin" del filo y crujido que se propaga;
#   - la rotura: golpe más grande, estallido de hielo y tintineo/arrastre de los pedazos al caer y deslizarse;
#   - el acercamiento final: barrido de aire que sube hasta el corte y un impacto suave que abre al mar.
# Sin material de terceros. Uso (Python con numpy + scipy): python sonido.py escena.json SALIDA.wav DURACION CORTE_s
import sys, json, wave
import numpy as np
from scipy.signal import butter, sosfilt

esc = json.load(open(sys.argv[1])); out = sys.argv[2]; DUR = float(sys.argv[3]); CORTE = float(sys.argv[4])
sr = 48000; N = int(DUR * sr); L = np.zeros(N); R = np.zeros(N); rng = np.random.default_rng(11)
FPS = 30.0

def bp(x, f0, f1, o=2): return sosfilt(butter(o, [f0, f1], "bandpass", fs=sr, output="sos"), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, "lowpass", fs=sr, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "highpass", fs=sr, output="sos"), x)
def db(v): return 10 ** (v / 20)

def put(sig, t, g=0.0, pan=0.0):
    i = int(round(t * sr)); j = min(N, i + len(sig))
    if j <= max(0, i): return
    s = sig[max(0, -i):j - i] * db(g)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[max(0, i):j] += s * l * 1.41; R[max(0, i):j] += s * r * 1.41

def env(n, ata, dec):
    t = np.arange(n) / sr; return np.minimum(1, t / max(ata, 1e-4)) * np.exp(-t / dec)

def barrido(dur, f0=300, f1=2500, g=-14):
    n = int(dur * sr); t = np.arange(n) / sr; x = rng.standard_normal(n)
    # banda que sube con la velocidad del hacha; envolvente que crece hasta el golpe
    y = np.zeros(n); seg = 256
    for k in range(0, n, seg):
        fc = f0 + (f1 - f0) * (k / n) ** 2
        y[k:k + seg] = bp(x[k:k + seg + 512], fc * 0.6, min(sr / 2 - 100, fc * 1.6))[:len(y[k:k + seg])]
    e = (t / dur) ** 2.2
    return y * e / (np.abs(y * e).max() + 1e-9) * db(g)

def golpe_grave(g=-6, f0=85, f1=42, dec=0.16):
    n = int(0.6 * sr); t = np.arange(n) / sr
    f = f1 + (f0 - f1) * np.exp(-t / 0.03); s = np.sin(2 * np.pi * np.cumsum(f) / sr) * env(n, 0.002, dec)
    s += 0.6 * lp(rng.standard_normal(n), 900) * env(n, 0.001, 0.025)
    return s / np.abs(s).max() * db(g)

def chasquido(g=-8, f0=1800, f1=9000, dec=0.012):
    n = int(0.08 * sr); s = bp(rng.standard_normal(n), f0, f1) * env(n, 0.0003, dec)
    return s / np.abs(s).max() * db(g)

def tin(g=-20):
    n = int(0.35 * sr); t = np.arange(n) / sr
    s = sum(a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / d) for f, a, d in ((2140, 1, 0.09), (3420, 0.7, 0.06), (5230, 0.4, 0.04)))
    return s / np.abs(s).max() * db(g)

def crujido(dur=0.32, n_cl=34, g=-14):
    n = int(dur * sr); s = np.zeros(n)
    for k in range(n_cl):
        tk = (rng.random() ** 1.8) * dur; a = np.exp(-tk / (dur * 0.5)) * rng.uniform(0.3, 1.0)
        c = chasquido(0, rng.uniform(900, 2500), rng.uniform(5000, 11000), rng.uniform(0.002, 0.006))
        i = int(tk * sr); j = min(n, i + len(c)); s[i:j] += c[:j - i] * a
    return s / (np.abs(s).max() + 1e-9) * db(g)

def estallido(g=-7):
    n = int(0.6 * sr); t = np.arange(n) / sr
    s = bp(rng.standard_normal(n), 900, 11000) * env(n, 0.002, 0.11)
    c = crujido(0.5, 90, 0); s[:len(c)] += 0.5 * c[:n]
    return s / np.abs(s).max() * db(g)

def tintineo(t0, dur, n_ev, g=-18):
    for k in range(n_ev):
        tk = t0 + (rng.random() ** 1.4) * dur; a = rng.uniform(-8, 0) - 6 * (tk - t0) / dur
        nn = int(0.12 * sr); tt = np.arange(nn) / sr; f = rng.uniform(1600, 5200)
        s = np.sin(2 * np.pi * f * tt) * np.exp(-tt / rng.uniform(0.015, 0.05))
        c = chasquido(0, 2000, 9000, 0.004); s[:len(c)] += 0.5 * c[:nn]
        put(s / np.abs(s).max(), tk, g + a, rng.uniform(-0.6, 0.6))

def arrastre(t0, dur, g=-22):
    n = int(dur * sr); t = np.arange(n) / sr
    s = bp(rng.standard_normal(n), 250, 1800) * np.exp(-t / (dur * 0.35)) * np.minimum(1, t / 0.02)
    put(s / np.abs(s).max(), t0, g)

golpes = esc["golpes"]; f_rot = esc["rotura"]
# fondo exterior muy bajo (que no haya silencio digital)
amb = lp(rng.standard_normal(N), 700) * db(-40); L += amb; R += amb * 0.95
for k, (f, x, y, rc, rm) in enumerate(golpes):
    th = f / FPS; fuerte = (f == f_rot); pan = float(np.clip(x * 1.2, -0.5, 0.5))
    pre = 0.2 if k == 0 else 0.3
    put(barrido(pre, 250, 3000 if fuerte else 2400, -16 if not fuerte else -13), th - pre, 0, pan)
    put(golpe_grave(-4 if fuerte else -7, 95 if fuerte else 85, 40, 0.22 if fuerte else 0.15), th, 0, pan * 0.5)
    put(chasquido(-6 if fuerte else -9), th, 0, pan)
    put(tin(-22 if fuerte else -19), th + 0.003, 0, pan)
    put(crujido(0.45 if fuerte else 0.3, 60 if fuerte else 34, -11 if fuerte else -14), th + 0.01, 0, pan)
    if fuerte:
        put(estallido(-6), th + 0.005, 0, 0.0)
        tintineo(th + 0.12, 1.3, 52, -17)
        arrastre(th + 0.18, 0.75, -21)
# el hielo se asienta: crujidos sueltos y bajos mientras la cámara se acerca
for k in range(26):
    tk = golpes[-1][0] / FPS + 0.9 + rng.random() * (CORTE - golpes[-1][0] / FPS - 1.2)
    put(chasquido(0, 1500, 8000, rng.uniform(0.002, 0.005)), tk, rng.uniform(-30, -22), rng.uniform(-0.7, 0.7))
# acercamiento final: aire que sube hasta el corte + impacto suave
put(barrido(1.0, 150, 1800, -12), CORTE - 1.0, 0, 0.0)
put(golpe_grave(-9, 70, 32, 0.35), CORTE, 0, 0.0)
mix = np.stack([L, R], 1)
mix = hp(mix.T, 25).T
pk = np.abs(mix).max(); mix = mix / pk * db(-3)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
print("sonido:", out, f"{DUR:.2f} s; golpes en", [round(g[0] / FPS, 3) for g in golpes], "corte", CORTE)
