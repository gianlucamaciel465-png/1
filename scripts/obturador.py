# Sonido de obturador sintetizado (sin material de terceros): dos chasquidos cortos filtrados + golpe grave.
# Uso: python3 obturador.py SALIDA.wav [ganancia_dB=-8]
import sys, wave
import numpy as np

out = sys.argv[1]; g = float(sys.argv[2]) if len(sys.argv) > 2 else -8.0
sr = 48000; L = int(0.25 * sr); a = np.zeros(L, np.float32)
rng = np.random.default_rng(7)

def burst(t0, dur, decay, amp):
    n = int(dur * sr); tt = np.arange(n) / sr
    s = rng.standard_normal(n) * np.exp(-tt / decay)
    s = np.convolve(s, [1, -0.85], "same")          # quita graves: chasquido metálico
    i = int(t0 * sr); a[i:i + n] += amp * s[:L - i]

def thump(t0, f, dur, amp):
    n = int(dur * sr); tt = np.arange(n) / sr
    i = int(t0 * sr); a[i:i + n] += amp * np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dur / 4))

burst(0.000, 0.012, 0.0025, 0.9); thump(0.000, 140, 0.05, 0.5)
burst(0.055, 0.016, 0.0035, 0.7); thump(0.055, 110, 0.06, 0.35)
a = a / np.abs(a).max() * 10 ** (g / 20)
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((a * 32767).astype(np.int16).tobytes())
print(f"{out}: obturador {L / sr:.2f} s, pico {g} dBFS")
