# Tratamiento del perfil "Roccé — Firme 04" sobre la voz base (es-AR-ElenaNeural, rate +11 %, pitch −20 Hz).
# Parámetros documentados en el comentario del MP3 aprobado: formants 0.94, pitch_factor 0.93, tempo 1.0,
# saturation_mix 0.055, max_internal_pause_ms 180. El orden y los operadores exactos no están documentados;
# esta es la reconstrucción usada (comparada contra el MP3 con comparar_voz.py):
#   1. pausas internas más largas que max_internal_pause_ms se acortan a ese valor (bordes intactos);
#   2. Praat "Change gender": formant shift ratio = formants, nueva mediana de tono = mediana × pitch_factor,
#      rango de tono ×1, duración ×tempo (parselmouth);
#   3. saturación suave en paralelo: (1 − mix)·x + mix·tanh(DRIVE·x)/tanh(DRIVE);
#   4. normalización de pico a −1 dBFS (la sonoridad final se ajusta en la mezcla).
# Uso: python tratamiento_firme.py ENTRADA SALIDA.wav [formants pitch_factor tempo sat_mix max_pausa_ms drive]
import sys, subprocess
import numpy as np
import parselmouth
from parselmouth.praat import call

ent, sal = sys.argv[1], sys.argv[2]
P = dict(formants=0.94, pitch_factor=0.93, tempo=1.0, saturation_mix=0.055, max_internal_pause_ms=180, drive=3.0)
for k, v in zip(["formants", "pitch_factor", "tempo", "saturation_mix", "max_internal_pause_ms", "drive"], sys.argv[3:]):
    P[k] = float(v)
SR = 48000

def leer(p):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"])
    return np.frombuffer(raw, np.float32).astype(np.float64)

def acortar_pausas(x, max_ms, umbral_db=-42, ventana_ms=10):
    w = int(SR * ventana_ms / 1000); n = len(x) // w
    e = np.array([np.sqrt(np.mean(x[i * w:(i + 1) * w] ** 2)) + 1e-12 for i in range(n)])
    db = 20 * np.log10(e / e.max())
    voz = db > umbral_db
    idx = np.where(voz)[0]
    if len(idx) == 0: return x
    a, b = idx[0], idx[-1] + 1                      # silencio inicial/final: se respeta afuera de este tramo
    partes = [x[:a * w]]; i = a; maxv = int(max_ms / ventana_ms)
    while i < b:
        j = i
        if not voz[i]:
            while j < b and not voz[j]: j += 1
            largo = j - i
            if largo > maxv:                      # se conserva la mitad de max a cada lado del corte, con fundido
                keep = maxv // 2; f = int(0.004 * SR)
                s1 = x[i * w:(i + keep) * w].copy(); s2 = x[(j - keep) * w:j * w].copy()
                s1[-f:] *= np.linspace(1, 0, f); s2[:f] *= np.linspace(0, 1, f)
                partes += [s1, s2]
            else:
                partes.append(x[i * w:j * w])
            i = j
        else:
            while j < b and voz[j]: j += 1
            partes.append(x[i * w:j * w]); i = j
    partes.append(x[b * w:])
    return np.concatenate(partes)

x = leer(ent)
if P["max_internal_pause_ms"] > 0:
    x = acortar_pausas(x, P["max_internal_pause_ms"])
snd = parselmouth.Sound(x, sampling_frequency=SR)
pitch = snd.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=500)
f0 = pitch.selected_array["frequency"]; f0 = f0[f0 > 0]
mediana = float(np.median(f0)) if len(f0) else 0.0
nueva = mediana * P["pitch_factor"] if mediana else 0.0
snd2 = call(snd, "Change gender", 75, 500, P["formants"], nueva, 1.0, P["tempo"])
y = snd2.values[0].astype(np.float64)
m = P["saturation_mix"]; d = P["drive"]
if m > 0:
    pk = np.abs(y).max() + 1e-9; yn = y / pk
    y = ((1 - m) * yn + m * np.tanh(d * yn) / np.tanh(d)) * pk
y = y / (np.abs(y).max() + 1e-9) * 10 ** (-1 / 20)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s24le", sal],
               input=y.astype(np.float64).tobytes(), check=True)
print(f"{sal}: mediana de tono {mediana:.1f} Hz → {nueva:.1f} Hz, duración {len(y) / SR:.2f} s, parámetros {P}")
