# Compara una voz candidata con la referencia aprobada (Rocce_Voz_Firme.mp3) con medidas objetivas.
# No reemplaza escuchar: mide tono, formantes, espectro promedio, duración y pausas.
# Uso: python comparar_voz.py REFERENCIA CANDIDATA [CANDIDATA ...]
import sys, subprocess
import numpy as np
import parselmouth

SR = 48000
def leer(p):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"])
    return np.frombuffer(raw, np.float32).astype(np.float64)

def medir(p):
    x = leer(p); snd = parselmouth.Sound(x, sampling_frequency=SR)
    pi = snd.to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=500).selected_array["frequency"]; v = pi[pi > 0]
    fo = snd.to_formant_burg(time_step=0.01, max_number_of_formants=5, maximum_formant=5000)
    ts = np.arange(0.02, snd.duration - 0.02, 0.01)
    f1 = np.array([fo.get_value_at_time(1, t) for t in ts]); f2 = np.array([fo.get_value_at_time(2, t) for t in ts])
    pt = snd.to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=500)
    voiced = np.array([pt.get_value_at_time(t) > 0 if not np.isnan(pt.get_value_at_time(t)) else False for t in ts])
    f1v, f2v = f1[voiced & ~np.isnan(f1)], f2[voiced & ~np.isnan(f2)]
    # espectro promedio (LTAS) en bandas de tercio de octava, normalizado
    n = 4096; win = np.hanning(n); specs = []
    for i in range(0, len(x) - n, n // 2):
        seg = x[i:i + n]
        if np.sqrt(np.mean(seg ** 2)) > 1e-3: specs.append(np.abs(np.fft.rfft(seg * win)) ** 2)
    S = np.mean(specs, 0); fr = np.fft.rfftfreq(n, 1 / SR)
    bandas = [100 * 2 ** (k / 3) for k in range(0, 22)]
    ltas = np.array([10 * np.log10(S[(fr >= b / 2 ** (1 / 6)) & (fr < b * 2 ** (1 / 6))].mean() + 1e-20) for b in bandas])
    ltas -= ltas.mean()
    # pausas
    w = int(0.01 * SR); e = np.array([np.sqrt(np.mean(x[i:i + w] ** 2)) + 1e-12 for i in range(0, len(x) - w, w)])
    db = 20 * np.log10(e / e.max()); voz = db > -42; idx = np.where(voz)[0]
    pausas = []; i = idx[0]
    while i < idx[-1]:
        if not voz[i]:
            j = i
            while not voz[j]: j += 1
            if j - i >= 8: pausas.append((j - i) * 10)
            i = j
        else: i += 1
    hablado = (idx[-1] - idx[0]) * 0.01
    return dict(dur=len(x) / SR, hablado=hablado, f0_med=np.median(v), f0_iqr=np.subtract(*np.percentile(v, [75, 25])),
                f1=np.median(f1v), f2=np.median(f2v), ltas=ltas, pausas=pausas)

ref = medir(sys.argv[1])
print("%-34s %6s %7s %7s %6s %6s %6s %6s  %s" % ("archivo", "dur", "hablado", "f0 med", "f0 iqr", "F1", "F2", "ΔLTAS", "pausas ms"))
def fila(nom, m, r):
    d = np.sqrt(np.mean((m["ltas"] - r["ltas"]) ** 2))
    print("%-34s %6.2f %7.2f %7.1f %6.1f %6.0f %6.0f %6.2f  %s" % (nom[-34:], m["dur"], m["hablado"], m["f0_med"], m["f0_iqr"], m["f1"], m["f2"], d, m["pausas"]))
fila(sys.argv[1], ref, ref)
for p in sys.argv[2:]:
    fila(p, medir(p), ref)
