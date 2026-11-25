"""P1 · revisión de sonido sin escucha: por ventana de 1 s, nivel RMS (dBFS) y tonalidad (pico de la media espectral
sobre su versión suavizada, dB, 100–4000 Hz). Hinchada/ambiente: espectro liso (tonalidad baja); música o relator:
líneas estables (tonalidad alta) y energía de voz 300–3000 Hz modulada. Uso: p1_tonal.py id6 [id6 ...]"""
import sys, subprocess, glob, numpy as np
SR = 24000
def leer(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-vn', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)
def analizar(x, win=1.0):
    N = 4096; hop = 1024; w = np.hanning(N)
    f = np.fft.rfftfreq(N, 1 / SR); b = (f > 100) & (f < 4000)
    out = []
    for s in range(0, len(x) - int(win * SR), int(win * SR)):
        seg = x[s:s + int(win * SR)]
        rms = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
        S = np.array([np.abs(np.fft.rfft(seg[i:i + N] * w)) ** 2 for i in range(0, len(seg) - N, hop)])
        L = 10 * np.log10(S.mean(0) + 1e-12)
        k = 25; sm = np.convolve(L, np.ones(k) / k, mode='same')
        ton = np.percentile((L - sm)[b], 99.5)
        out.append((s / SR, rms, ton))
    return out
for id6 in sys.argv[1:]:
    p = glob.glob(f'/home/user/1/TRABAJO/boc25/clips/*{id6}.mp4')[0]
    r = analizar(leer(p))
    print(id6, ' '.join(f'{t:.0f}:{rms:.0f}/{ton:.1f}' for t, rms, ton in r))
