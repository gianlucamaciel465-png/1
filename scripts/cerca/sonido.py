# Sonido de "ESTUVISTE CERCA" (44 s, 48 kHz estéreo):
#  - voces (edge-tts) en sus tiempos de linea.py, con un respiro suave del chico entre ideas;
#  - mar real de fondo: IMG_7896 (mar parejo) en bucle con fundidos, una ola de IMG_4641 y la ola grande de
#    IMG_4631 en el corte al agua (25,8–27,0 s), más el agua de la propia toma S5;
#  - roce de tela sintetizado en la entrega (32,2–35,6 s);
#  - motivo musical muy bajo sintetizado que entra después de la pregunta (≈30,4 s) y resuelve en la placa.
# Salida: mezcla_voz.wav (sin normalizar; montar.sh lleva a −14 LUFS). Uso: python sonido.py VOZ_DIR TOMAS_DIR SALIDA_DIR
import sys, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
sys.path.insert(0, __file__.rsplit("/", 1)[0]); from linea import VOZ
vd, td, out = sys.argv[1:4]
SR, DUR = 48000, 44.0; N = int(SR * DUR)
def leer(path, t0=0, t1=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(t0)] + (["-to", str(t1)] if t1 else []) + ["-i", path, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
def filt(x, kind, f, order=4):
    return sosfilt(butter(order, f, kind, fs=SR, output="sos"), x, axis=0)
def db(x): return 10 ** (x / 20)
def poner(buf, x, t, g=1.0):
    i = int(round(t * SR)); x = x[:max(0, N - i)]; buf[i:i + len(x)] += x * g
def env(n, a, r):
    e = np.ones(n); a, r = int(a * SR), int(r * SR)
    e[:a] = np.linspace(0, 1, a); e[n - r:] = np.linspace(1, 0, r); return e
rng = np.random.default_rng(11)

# --- voces
voz = np.zeros((N, 2))
for k, t in VOZ.items():
    x, sr = sf.read(f"{vd}/{k}.wav"); x = filt(x, "highpass", 90, 2)
    poner(voz, np.stack([x, x], 1), t, db(-1.0) if k.startswith("a") else 1.0)
def respiro(t, g):  # inhalación corta por la nariz: ruido filtrado con envolvente suave
    n = int(0.42 * SR); x = filt(rng.normal(0, 1, n), "bandpass", [500, 2600], 2) * np.hanning(n) ** 1.5
    poner(voz, np.stack([x, x], 1) / np.abs(x).max(), t, db(g))
for t in (8.05, 21.45, 23.05): respiro(t, -40)

# --- mar real de fondo
O = "ORIGINALES/"
base = filt(leer(O + "IMG_7896.mov"), "highpass", 70, 2); base /= np.sqrt((base ** 2).mean()); L = len(base)
mar = np.zeros((N, 2)); x = int(0.8 * SR); t = 0; i = 0
while t < N:
    seg = base if i % 2 == 0 else base[::-1]           # alterna sentido para que el bucle no se note
    seg = seg * env(L, 0.8, 0.8)[:, None]; mar[t:t + L] += seg[:N - t]; t += L - x; i += 1
mar *= db(-30)
ola = filt(leer(O + "IMG_4641.mov", 0.5, 4.0), "highpass", 70, 2); ola = ola * env(len(ola), 0.5, 0.8)[:, None]
poner(mar, ola, 9.0, db(-12)); poner(mar, ola, 21.5, db(-14))
grande = filt(leer(O + "IMG_4631.mov", 2.0, 5.6), "highpass", 60, 2); grande *= env(len(grande), 0.3, 1.0)[:, None]
poner(mar, grande, 25.3, db(-11))
s5 = leer(f"{td}/S5.mp4", 0.4, 1.8); poner(mar, s5 * env(len(s5), 0.1, 0.2)[:, None], 25.8, db(-2))
# el mar baja un poco con la voz (que se entienda) y se va en la placa
vl = np.convolve(np.abs(voz[:, 0]), np.ones(int(0.25 * SR)) / (0.25 * SR), "same")
duck = db(-5 * np.clip(vl / (vl.max() * 0.25), 0, 1))
mar *= duck[:, None]
fade = np.ones(N); a, b = int(40.0 * SR), int(43.2 * SR); fade[a:b] = np.linspace(1, 0.15, b - a); fade[b:] = np.linspace(0.15, 0, N - b)
mar *= fade[:, None]

# --- roce de tela en la entrega
tela = np.zeros((N, 2))
for t0, d, g in ((32.55, 0.55, -30), (33.3, 0.7, -28), (34.2, 0.45, -31), (35.0, 0.35, -34), (38.9, 0.5, -30)):
    n = int(d * SR); x = filt(rng.normal(0, 1, (n, 2)), "bandpass", [900, 7000], 2)
    e = np.abs(filt(rng.normal(0, 1, n), "lowpass", 18, 2)); e = e / e.max() * np.hanning(n)
    poner(tela, x * e[:, None] / np.abs(x).max(), t0, db(g))

# --- motivo musical muy bajo (entra después de la pregunta)
def nota(f, d, g):
    n = int(d * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * h * t) * a for h, a in ((1, 1), (2, .25), (3, .08))) * np.exp(-t * 1.1)
    x *= env(n, 0.02, min(1.0, d * 0.5)); return np.stack([x, x], 1)
def pad(fs, d):
    n = int(d * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in fs) / len(fs)
    x = filt(x, "lowpass", 1800, 2) * env(n, 1.5, 1.8); return np.stack([x, x * 0.96], 1)
mus = np.zeros((N, 2))
A3, C4, E4, G4, F3, A4, D4, B3, G3 = 220.0, 261.63, 329.63, 392.0, 174.61, 440.0, 293.66, 246.94, 196.0
for t, f in ((30.6, E4), (31.6, G4), (32.6, A4), (34.6, E4), (36.0, C4), (37.4, D4), (38.8, E4), (40.2, C4), (40.9, G4), (41.6, E4)):
    poner(mus, nota(f, 2.2, 0), t, db(-6))
poner(mus, pad((A3, C4, E4), 6.0), 30.4, db(-10)); poner(mus, pad((F3, A3, C4, E4), 4.6), 35.6, db(-10))
poner(mus, pad((C4 / 2, G3, C4, E4), 4.2), 39.8, db(-8))
mus *= db(-24)

mezcla = voz + mar + tela + mus
sf.write(f"{out}/mezcla_voz.wav", mezcla.astype(np.float32), SR, subtype="FLOAT")
for n, x in (("voz", voz), ("mar", mar), ("tela", tela), ("musica", mus)):
    sf.write(f"{out}/capa_{n}.wav", x.astype(np.float32), SR, subtype="FLOAT")
print("mezcla", mezcla.shape, "pico", np.abs(mezcla).max().round(3))
