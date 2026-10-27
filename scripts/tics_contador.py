# Tics de un contador descendente que se desacelera (concepto "casi impacto", R5/R7).
# n(t) = 1 + ceil((N0-1)·(1 - t/T)^K) para t < T; 1 en t ≥ T. Un tic por cambio de número,
# con separación mínima (al principio el número cambia en cada cuadro y sería un zumbido).
# Volumen creciente hacia el final; el último ("001") más grave y fuerte.
# Uso: python3 tics_contador.py SALIDA.wav N0 T K [fps=30] [sep_min=0.1]
import sys, wave, math
import numpy as np

out, N0, T, K = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
fps = float(sys.argv[5]) if len(sys.argv) > 5 else 30.0
sep = float(sys.argv[6]) if len(sys.argv) > 6 else 0.1
sr = 48000
n = lambda t: 1 if t >= T else 1 + math.ceil((N0 - 1) * (1 - t / T) ** K)
dur = T + 1.0
audio = np.zeros(int(dur * sr), np.float32)
rng = np.random.default_rng(1)

def tick(t0, gain_db, freq):
    L = int(0.03 * sr); tt = np.arange(L) / sr
    s = np.sin(2 * np.pi * freq * tt) * np.exp(-tt / 0.006) + 0.35 * rng.standard_normal(L) * np.exp(-tt / 0.002)
    s *= 10 ** (gain_db / 20)
    i = int(t0 * sr); audio[i:i + L] += s[:len(audio) - i]

last_t, last_n, count = -1.0, None, 0
for f in range(int(T * fps) + 1):
    t = f / fps; v = n(t)
    if v != last_n:
        final = v == 1
        if final or t - last_t >= sep:
            prog = min(1.0, t / T)
            tick(t, -10 if final else -26 + 12 * prog, 1100 if final else 2200)
            last_t = t; count += 1
        last_n = v
audio = np.clip(audio, -1, 1)
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((audio * 32767).astype(np.int16).tobytes())
print(f"{out}: {count} tics en {T:.3f} s (N0={N0}, K={K})")
