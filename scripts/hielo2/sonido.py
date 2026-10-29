# Sonido de la parte del hielo de ROCCE_01_HIELO_REVELACION v02, sintetizado (sin material de terceros: el audio de
# la grabación de referencia tiene voz y música ajenas) y sincronizado con los contactos REALES del metraje:
#   - golpes: contactos de la herramienta encontrados cuadro a cuadro (sacudón de cámara + esquirlas nuevas);
#     golpe grave + chasquido + "tin" + crujido; los fuertes (sacudón grande o estallido de esquirlas) más llenos;
#   - levantar: crujidos bajos del hielo en las manos;
#   - caída: aire, impacto contra el piso y estallido del hielo en el cuadro del choque, tintineo y arrastre de los
#     pedazos; al corte, un golpe grave suave que abre a las tomas reales.
# Uso: python sonido.py SALIDA.wav DURACION_s
import sys, wave
import numpy as np
from scipy.signal import butter, sosfilt

out = sys.argv[1]; DUR = float(sys.argv[2])
sr = 48000; N = int(round(DUR * sr)); L = np.zeros(N); R = np.zeros(N); rng = np.random.default_rng(23)
FPS = 30.0
# línea de tiempo del montaje (cuadros de salida): A = ref 305–402 → 0–97 · C = 440–469 → 98–127 · D = 472–497 → 128–153
def tA(f): return (f - 305) / FPS
def tD(f): return (128 + f - 472) / FPS
GOLPES = [306, 313, 319, 327, 333, 342, 346, 349, 355, 362, 369, 376, 382, 387, 393, 398, 400]
FUERTES = {319, 349, 355, 376, 393}
T_C = 98 / FPS; T_D = 128 / FPS; T_CHOQUE = tD(477); T_CORTE = 154 / FPS

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

def norm(s): return s / (np.abs(s).max() + 1e-9)

def barrido(dur, f0=300, f1=2500):
    n = int(dur * sr); t = np.arange(n) / sr; x = rng.standard_normal(n + 1024); y = np.zeros(n); seg = 256
    for k in range(0, n, seg):
        fc = f0 + (f1 - f0) * (k / n) ** 2
        y[k:k + seg] = bp(x[k:k + seg + 512], fc * 0.6, min(sr / 2 - 100, fc * 1.6))[:len(y[k:k + seg])]
    return norm(y * (t / dur) ** 2.2)

def golpe_grave(f0=85, f1=42, dec=0.16):
    n = int(0.6 * sr); t = np.arange(n) / sr
    f = f1 + (f0 - f1) * np.exp(-t / 0.03); s = np.sin(2 * np.pi * np.cumsum(f) / sr) * env(n, 0.002, dec)
    s += 0.6 * lp(rng.standard_normal(n), 900) * env(n, 0.001, 0.025)
    return norm(s)

def chasquido(f0=1800, f1=9000, dec=0.012):
    n = int(0.08 * sr); return norm(bp(rng.standard_normal(n), f0, f1) * env(n, 0.0003, dec))

def tin():
    n = int(0.35 * sr); t = np.arange(n) / sr
    return norm(sum(a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / d)
                    for f, a, d in ((2140, 1, 0.09), (3420, 0.7, 0.06), (5230, 0.4, 0.04))))

def crujido(dur=0.32, n_cl=34):
    n = int(dur * sr); s = np.zeros(n)
    for _ in range(n_cl):
        tk = (rng.random() ** 1.8) * dur; a = np.exp(-tk / (dur * 0.5)) * rng.uniform(0.3, 1.0)
        c = chasquido(rng.uniform(900, 2500), rng.uniform(5000, 11000), rng.uniform(0.002, 0.006))
        i = int(tk * sr); j = min(n, i + len(c)); s[i:j] += c[:j - i] * a
    return norm(s)

def estallido():
    n = int(0.6 * sr); s = bp(rng.standard_normal(n), 900, 11000) * env(n, 0.002, 0.11)
    c = crujido(0.5, 90); s[:len(c)] += 0.5 * c[:n]
    return norm(s)

def tintineo(t0, dur, n_ev, g=-18):
    for _ in range(n_ev):
        tk = t0 + (rng.random() ** 1.4) * dur; a = rng.uniform(-8, 0) - 6 * (tk - t0) / dur
        nn = int(0.12 * sr); tt = np.arange(nn) / sr; f = rng.uniform(1600, 5200)
        s = np.sin(2 * np.pi * f * tt) * np.exp(-tt / rng.uniform(0.015, 0.05))
        c = chasquido(2000, 9000, 0.004); s[:len(c)] += 0.5 * c[:nn]
        put(norm(s), tk, g + a, rng.uniform(-0.6, 0.6))

def arrastre(t0, dur, g=-22):
    n = int(dur * sr); t = np.arange(n) / sr
    put(norm(bp(rng.standard_normal(n), 250, 1800) * np.exp(-t / (dur * 0.35)) * np.minimum(1, t / 0.02)), t0, g)

# piso de ruido muy bajo (sin silencio digital) hasta el corte
amb = lp(rng.standard_normal(N), 700) * db(-42); amb[int(T_CORTE * sr):] = 0
L += amb; R += amb * 0.95
# A: golpes reales
for f in GOLPES:
    t = tA(f); fuerte = f in FUERTES; pan = rng.uniform(-0.25, 0.35)
    put(barrido(0.10, 300, 2600), t - 0.10, -20 if not fuerte else -16, pan)
    put(golpe_grave(95 if fuerte else 80, 40, 0.2 if fuerte else 0.12), t, -4 if fuerte else -9, pan * 0.5)
    put(chasquido(), t, -6 if fuerte else -10, pan)
    put(tin(), t + 0.003, -21 if fuerte else -24, pan)
    put(crujido(0.35 if fuerte else 0.22, 50 if fuerte else 26), t + 0.008, -11 if fuerte else -16, pan)
    if f == 376:                                            # estallido de esquirlas visible
        put(estallido(), t + 0.01, -10, 0.2); tintineo(t + 0.08, 0.45, 18, -22)
# C: hielo en las manos
put(golpe_grave(70, 38, 0.10), T_C, -10, 0.0)                    # manos que agarran el bloque
arrastre(T_C + 0.0, 0.9, -12)                                      # hielo que roza las palmas
put(crujido(0.55, 40), T_C + 0.06, -8, -0.3); put(crujido(0.5, 34), T_C + 0.42, -10, 0.3)
put(crujido(0.4, 26), T_C + 0.74, -11, 0.0)
tintineo(T_C + 0.05, 0.85, 10, -22)                                # esquirlas sueltas que caen del bloque
# D: caída, choque y rotura del hielo
put(barrido(T_CHOQUE - T_D + 0.02, 150, 1400), T_D - 0.02, -15, 0.0)
put(golpe_grave(90, 36, 0.26), T_CHOQUE, -3, 0.0)
put(estallido(), T_CHOQUE + 0.004, -5, 0.0)
put(crujido(0.5, 70), T_CHOQUE + 0.01, -10, 0.1)
tintineo(T_CHOQUE + 0.06, 0.6, 40, -16)
arrastre(T_CHOQUE + 0.08, 0.55, -21)
# corte a las tomas reales: golpe grave suave
put(golpe_grave(64, 30, 0.32), T_CORTE, -11, 0.0)
mix = np.stack([L, R], 1)
mix = hp(mix.T, 25).T
mix = mix / np.abs(mix).max() * db(-3)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
print("sonido:", out, f"{DUR:.3f} s; golpes", [round(tA(f), 3) for f in GOLPES], "choque", round(T_CHOQUE, 3),
      "corte", round(T_CORTE, 3))
