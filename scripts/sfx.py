# Efectos sintetizados (sin material de terceros) ubicados en una línea de tiempo, para diseñar el sonido de un reel.
# Uso: python3 sfx.py SALIDA.wav DURACION CUES.json
# CUES.json: [{"tipo": "kick|golpe|zumbido|clic|subida", "t": segundos, "db": ganancia_pico, ...}]
#   kick     pulso grave corto (latido del ritmo)          t = inicio
#   golpe    golpe grave con cola (giro / revelación)      t = inicio
#   zumbido  barrido de aire que crece hasta t             "dur" = duración antes de t
#   clic     clic corto de interfaz (anotaciones, botones) t = inicio
#   subida   subida suave hacia un corte en t              "dur"
import sys, json, wave
import numpy as np

out, dur, cues = sys.argv[1], float(sys.argv[2]), json.load(open(sys.argv[3]))
sr = 48000; N = int(dur * sr); mix = np.zeros(N, np.float32); rng = np.random.default_rng(3)

def put(sig, t0):
    i = int(round(t0 * sr)); j = min(N, i + len(sig))
    if i < N and j > max(0, i): mix[max(0, i):j] += sig[max(0, -i):j - i]

def norm(sig, db): return sig / (np.abs(sig).max() + 1e-9) * 10 ** (db / 20)

def lowpass(x, fc):   # un polo, fc puede variar por muestra
    fc = np.broadcast_to(np.asarray(fc, np.float32), x.shape); a = np.exp(-2 * np.pi * fc / sr); y = np.zeros_like(x); s = 0.0
    for k in range(len(x)): s = (1 - a[k]) * x[k] + a[k] * s; y[k] = s
    return y

def kick(db, f0=110, f1=46, dec=0.28):
    L = int(0.45 * sr); t = np.arange(L) / sr
    f = f1 + (f0 - f1) * np.exp(-t / 0.035); ph = 2 * np.pi * np.cumsum(f) / sr
    s = np.sin(ph) * np.exp(-t / dec) * np.minimum(1, t / 0.002)
    s += 0.25 * rng.standard_normal(L) * np.exp(-t / 0.004)          # ataque
    return norm(s, db)

def golpe(db):
    s = kick(0, f0=80, f1=34, dec=0.9); L = len(s); t = np.arange(L) / sr
    s = np.concatenate([s, np.zeros(int(0.8 * sr))]); t = np.arange(len(s)) / sr
    aire = lowpass(rng.standard_normal(len(s)).astype(np.float32), 1800) * np.exp(-t / 0.35) * 0.8
    return norm(s + aire, db)

def zumbido(db, d):
    L = int(d * sr); t = np.arange(L) / sr; u = t / d
    n = rng.standard_normal(L).astype(np.float32)
    s = lowpass(n, 300 + 5200 * u ** 2) * (u ** 2.2)
    cola = int(0.09 * sr); s = np.concatenate([s, s[-1] * np.exp(-np.arange(cola) / (0.02 * sr))])
    return norm(s, db)

def clic(db):
    L = int(0.04 * sr); t = np.arange(L) / sr
    s = (np.sin(2 * np.pi * 1900 * t) + 0.4 * np.sin(2 * np.pi * 3800 * t)) * np.exp(-t / 0.006) * np.minimum(1, t / 0.0015)
    return norm(s, db)

def subida(db, d):
    L = int(d * sr); t = np.arange(L) / sr; u = t / d
    s = np.sin(2 * np.pi * np.cumsum(200 + 900 * u ** 2) / sr) * 0.5 + lowpass(rng.standard_normal(L).astype(np.float32), 2500) * 0.5
    return norm(s * u ** 2.5, db)

for c in cues:
    tp, db = c["tipo"], c["db"]
    if tp == "kick": put(kick(db), c["t"])
    elif tp == "golpe": put(golpe(db), c["t"])
    elif tp == "clic": put(clic(db), c["t"])
    elif tp == "zumbido": put(zumbido(db, c["dur"]), c["t"] - c["dur"])
    elif tp == "subida": s = subida(db, c["dur"]); put(s, c["t"] - c["dur"])
st = np.stack([mix, mix], 1)
peak = np.abs(st).max()
if peak > 0.98: st *= 0.98 / peak
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print(f"{out}: {len(cues)} efectos, {dur:.2f} s, pico {20 * np.log10(peak + 1e-9):.1f} dBFS")
