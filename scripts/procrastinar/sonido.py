# Sonido de "Dejá de procrastinar" (15,0 s, 48 kHz estéreo), todo sintetizado salvo el mar real de IMG_7857 en el CTA.
# Sigue la línea de tiempo de eventos.json (render.js):
#  cuenta regresiva: pulso a 120 bpm + tic por cada día (sube de tono) + ladrillo del constructor + deslizar del celular
#  1 DÍA: alarma, latido, lluvia y ladrillos a toda velocidad · HOY: golpe y silencio · MISMA PARED: dos "ding" + acorde
#  DISTINTO MES: caída de cinta (todo baja de tono), golpe sordo, ladrillo que cae · vuelve a 30: hoja + tic otra vez
#  CTA (11,6 s): impacto + groove completo + mar real; golpes en cada renglón del texto.
# Uso: python sonido.py EVENTOS.json SALIDA.wav
import sys, json, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
ev = json.load(open(sys.argv[1])); TL = ev["TL"]; out = sys.argv[2]
SR, DUR, CTA = 48000, 15.0, 11.6; N = int(SR * DUR); rng = np.random.default_rng(5)
mix = np.zeros((N, 2))
def put(x, t, g=1.0, pan=0.0):
    if x.ndim == 1: x = np.stack([x * (1 - max(0, pan)), x * (1 + min(0, pan))], 1)
    i = int(round(t * SR)); j = min(N, i + len(x))
    if i < N and j > i: mix[i:j] += x[:j - i] * g
def filt(x, k, f, o=2): return sosfilt(butter(o, f, k, fs=SR, output="sos"), x, axis=0)
def env(L, a, d): t = np.arange(L) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def db(x): return 10 ** (x / 20)
def tono(f, L, d, armon=((1, 1),)):
    t = np.arange(L) / SR; return sum(a * np.sin(2 * np.pi * f * h * t) for h, a in armon) * env(L, 0.002, d)
def kick(g=1.0):
    L = int(0.4 * SR); t = np.arange(L) / SR; f = 45 + 75 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22) * g
def hat(g=1.0, d=0.03):
    L = int(0.12 * SR); return filt(rng.normal(0, 1, L), "highpass", 7000) * env(L, 0.001, d) * 0.35 * g
def clap(g=1.0):
    L = int(0.3 * SR); x = filt(rng.normal(0, 1, L), "bandpass", [900, 4000]); e = np.zeros(L)
    for k in (0, 0.011, 0.022): i = int(k * SR); e[i:] += np.exp(-np.arange(L - i) / SR / 0.012)
    return x * (e * 0.4 + env(L, 0.001, 0.09)) * 0.5 * g
def ladrillo(g=1.0, f=900):     # clac seco de ladrillo
    L = int(0.12 * SR); x = filt(rng.normal(0, 1, L), "bandpass", [f * 0.6, f * 2.2]) * env(L, 0.0005, 0.018)
    return (x + tono(f * 0.35, L, 0.03) * 0.25) * g
def golpe(g=1.0):
    L = int(1.6 * SR); t = np.arange(L) / SR; f = 32 + 90 * np.exp(-t / 0.06)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55) + filt(rng.normal(0, 1, L), "lowpass", 900) * env(L, 0.001, 0.12) * 0.6
    return s * g
def ding(f, g=1.0): L = int(1.2 * SR); return tono(f, L, 0.45, ((1, 1), (2.01, 0.35), (3.02, 0.12))) * g
def pop(g=1.0): L = int(0.09 * SR); t = np.arange(L) / SR; return np.sin(2 * np.pi * (300 + 900 * t / 0.09) * t) * env(L, 0.001, 0.025) * g
def roce(d, g=1.0): L = int(d * SR); return filt(rng.normal(0, 1, L), "bandpass", [1500, 7000]) * np.sin(np.pi * np.arange(L) / L) ** 2 * 0.3 * g
def subida(d, g=1.0):
    L = int(d * SR); u = np.arange(L) / L; x = filt(rng.normal(0, 1, L), "bandpass", [400, 6000]) * u ** 2
    return (x + np.sin(2 * np.pi * np.cumsum(120 + 900 * u ** 2) / SR) * u ** 2 * 0.3) * 0.5 * g
def bajo(f, d, g=1.0):
    L = int(d * SR); t = np.arange(L) / SR; x = np.sign(np.sin(2 * np.pi * f * t)) * 0.4 + np.sin(2 * np.pi * f * t)
    return filt(x, "lowpass", 260) * env(L, 0.005, d * 0.6) * g
def pad(fs, d, g=1.0, brillo=1600):
    L = int(d * SR); t = np.arange(L) / SR
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t) for f in fs) / len(fs)
    e = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.4); return filt(x, "lowpass", brillo) * e * g

BEAT = 0.5   # 120 bpm
A2, C3, E3, G3, F2 = 110.0, 130.81, 164.81, 196.0, 87.31
# ---- 1) cuenta regresiva (0 → 1 DÍA): pulso que se va apurando con los días
for k in range(int(TL["unDia"] / BEAT) + 1):
    t = k * BEAT
    if t < TL["unDia"]: put(kick(0.55 + 0.25 * t / TL["unDia"]), t); put(bajo(A2 if (k // 4) % 2 == 0 else F2, 0.45, 0.35), t)
    for h in (0.25,): put(hat(0.5), t + h)
for i, t in enumerate(ev["tC"]):
    put(ladrillo(0.28, 820 + 40 * (i % 3)), t + 0.16, pan=0.35)                      # constructor (derecha)
dias = [TL["d0"] + k * TL["paso"] for k in range(28)]
for k, t in enumerate(dias): put(tono(1800 + 22 * k, int(0.05 * SR), 0.012), t, 0.16)  # tic de cada día (sube)
for t in np.arange(0.3, TL["unDia"], 0.62): put(roce(0.09, 0.35), t, pan=-0.4)         # deslizar del celular (izquierda)
for a, b in TL["manana"]: put(pop(0.5), a, pan=-0.3)
put(subida(TL["unDia"] - 2.0, 0.22), 2.0)                                              # tensión que crece
# ---- 2) 1 DÍA: alarma, latido, lluvia, ladrillos a toda velocidad
for k in range(3): put(tono(1320, int(0.11 * SR), 0.05, ((1, 1), (3, 0.3))), TL["unDia"] + k * 0.14, 0.32)
for t in np.arange(TL["unDia"] + 0.1, TL["hoy"], 0.30): put(kick(0.5), t); put(kick(0.35), t + 0.13)       # latido
L = int((TL["hoy"] - TL["unDia"]) * SR); put(filt(rng.normal(0, 1, (L, 2)), "bandpass", [1200, 8000]) * 0.05 * np.sin(np.pi * np.arange(L) / L)[:, None] ** 0.3, TL["unDia"])
for t in np.arange(TL["unDia"], TL["hoy"], 0.0625): put(hat(0.6, 0.02), t)
for i, t in enumerate(ev["tP"]): put(ladrillo(0.30, 700 + 60 * (i % 4)), t + 0.13, pan=-0.35)
# ---- 3) HOY: golpe y respiro; MISMA PARED: dos ding + acorde mayor
put(golpe(0.9), TL["hoy"])
put(ding(1046.5, 0.22), TL["hoy"] + 0.10, pan=-0.3); put(ding(1318.5, 0.22), TL["hoy"] + 0.18, pan=0.3)
for k, ch in enumerate("MISMA PARED."): put(pop(0.10), TL["misma"] + k * 0.028)
put(pad((C3, E3, G3, 2 * C3), TL["distinto"] - TL["misma"] + 0.2, 0.18, 2200), TL["misma"])
for t in np.arange(TL["hoy"] + 0.5, TL["distinto"], BEAT): put(kick(0.45), t); put(hat(0.45), t + 0.25); put(bajo(C3 / 2, 0.45, 0.3), t)   # festejo con pulso
# ---- 4) DISTINTO MES: caída de cinta + golpe sordo + ladrillo que cae
L = int(0.9 * SR); t = np.arange(L) / SR; f = 220 * np.exp(-t * 2.2)
put(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(L, 0.005, 0.5) * 0.35, TL["distinto"])
for k, ch in enumerate("DISTINTO MES."): put(pop(0.08), TL["distinto"] + k * 0.028)
put(golpe(0.45), TL["distinto"] + 0.40)                                                   # se desploma
put(ladrillo(0.5, 600), TL["cae"] + 0.45, pan=-0.3); put(golpe(0.35), TL["cae"] + 0.55)    # ladrillo al piso
put(pad((A2, C3, E3), TL["reset"] - TL["distinto"] + 0.3, 0.12, 700), TL["distinto"])
# ---- 5) vuelve a 30: hoja, pilas nuevas, el tic otra vez, "mañana…"
put(roce(0.25, 0.8), TL["reset"] - 0.05)
for i in range(6): put(ladrillo(0.25, 760), TL["reset"] + i * 0.035 + 0.22)
for i in range(6): put(ladrillo(0.22, 840), TL["reset"] + 0.45 + i * TL["paso"] + 0.16, pan=0.35)
for k in range(8): put(tono(1800 + 22 * k, int(0.05 * SR), 0.012), TL["reset"] + 0.2 + k * TL["paso"], 0.14)
for k in range(4): put(kick(0.45), TL["reset"] + 0.1 + k * BEAT)
put(subida(1.0, 0.35), CTA - 1.0)
# ---- 6) CTA: impacto + groove + mar real
put(golpe(1.0), CTA); put(clap(0.6), CTA)
for k in range(int((DUR - CTA) / (BEAT / 2))):
    t = CTA + k * BEAT / 2
    if k % 2 == 0: put(kick(0.8), t); put(bajo(A2 if (k // 8) % 2 == 0 else F2, 0.45, 0.45), t)
    if k % 4 == 2: put(clap(0.45), t)
    put(hat(0.45), t + BEAT / 4)
for t, g in ((CTA + 0.10, 0.35), (CTA + 0.45, 0.6), (CTA + 0.85, 0.35)): put(golpe(g * 0.6), t); put(pop(0.3), t)
put(pad((A2, C3, E3, G3), DUR - CTA, 0.10, 1800), CTA)
mar = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-ss", "3.55", "-t", str(DUR - CTA), "-i", "ORIGINALES/IMG_7857.mov", "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, np.float32).reshape(-1, 2)
put(filt(mar, "highpass", 80) * 0.6, CTA)
# fundido final corto (sin silencio largo)
mix[-int(0.45 * SR):] *= np.linspace(1, 0, int(0.45 * SR))[:, None]
sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT"); print("mezcla", out, "pico", round(float(np.abs(mix).max()), 3))
