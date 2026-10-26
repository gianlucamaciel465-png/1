# Estima tempo (BPM) y golpes a partir del flujo espectral; compara con tiempos de corte dados.
import sys, subprocess, numpy as np
f = sys.argv[1]; t0 = float(sys.argv[2]); t1 = float(sys.argv[3]); cortes = [float(x) for x in sys.argv[4:]]
sr = 22050
pcm = subprocess.run(['ffmpeg','-v','error','-ss',str(t0),'-to',str(t1),'-i',f,'-vn','-ac','1','-ar',str(sr),'-f','f32le','-'],capture_output=True,check=True).stdout
x = np.frombuffer(pcm, dtype=np.float32)
hop, win = 220, 2048  # 100 cuadros/s
frames = np.lib.stride_tricks.sliding_window_view(np.pad(x,(0,win)), win)[::hop] * np.hanning(win)
mag = np.log1p(np.abs(np.fft.rfft(frames, axis=1)))
flux = np.maximum(0, np.diff(mag, axis=0)).sum(axis=1); flux = (flux - flux.mean())/ (flux.std()+1e-9)
fps = sr/hop
ac = np.correlate(flux, flux, 'full')[len(flux)-1:]
lags = np.arange(len(ac))/fps
ok = (lags >= 60/190) & (lags <= 60/70)
best = lags[ok][np.argmax(ac[ok])]; bpm = 60/best
# fase: elegir desplazamiento que maximiza el flujo en la grilla
period = best*fps
phases = np.arange(0, int(period))
score = [flux[np.arange(p, len(flux), period).astype(int)].sum() for p in phases]
ph = phases[int(np.argmax(score))]/fps
beats = np.arange(ph, (t1-t0), best) + t0
print(f"{f}: tramo {t0}-{t1}s  tempo ≈ {bpm:.1f} BPM (golpe cada {best:.3f}s); primer golpe {beats[0]:.2f}s")
for c in cortes:
    d = beats[np.argmin(abs(beats-c))]-c
    print(f"  corte {c:.2f}s → golpe más cercano a {d*1000:+.0f} ms")
