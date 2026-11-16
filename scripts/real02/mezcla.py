#!/usr/bin/env python3
"""REAL-02 v01 · mezcla (48 kHz estéreo, float) según el guion G1 §6. Tres capas:
A) ambiente real de las tomas en mono al centro, recortado a los mismos cuadros que la imagen (fundidos de 5 ms en cada corte);
B) efectos sintetizados: golpe (seno 58→42 Hz, 160 ms), pulso (62 Hz, 90 ms, saturación suave para que tenga armónicos
   audibles en un teléfono), ráfaga de ruido 250 ms (f94), clic (f244);
C) música propia sintetizada 120 BPM (1 tiempo = 15 cuadros, primer tiempo f94): bombo 1 y 3, palma 2 y 4, bajo,
   acorde por compás Am (f94) – F (f154) – G (f214) – C (f274), charles en corcheas desde f124, charles abierto y arpegio
   desde f184, acorde C sostenido desde f274, fundido f295–f306. Instrumentos adaptados de scripts/proxima/musica.py.
Sin voces ni material de terceros. uso: venv/bin/python mezcla.py DIR_AUD ATENUACION_SILENCIO_dB
Escribe DIR_AUD/mezcla_pre.wav, pistas separadas y mezcla_eventos.json."""
import sys, os, json, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

D = sys.argv[1]; ATT = float(sys.argv[2]) if len(sys.argv) > 2 else 18.0
SR = 48000; NF = 307; N = NF * SR // 30            # 491200 muestras = 10,2333 s
O = '/home/user/1/ORIGINALES'
C = lambda f: f / 30
rng = np.random.default_rng(2)
V11 = os.environ.get('REAL02_VER', 'v1') == 'v1_1'   # v1.1 (dictamen 08): P6 hasta f258 y clic en f229
FIN_P6, F_CLIC = (259, 229) if V11 else (229, 244)
t = np.arange(N) / SR
hz = lambda n: 440 * 2 ** ((n - 69) / 12)
ev = {'eventos': []}


def leer(toma):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{O}/{toma}.mov', '-vn', '-map', '0:a:0', '-f', 'f32le', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    ch = int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=channels', '-of', 'csv=p=0',
                             f'{O}/{toma}.mov'], capture_output=True, text=True).stdout)
    a = np.frombuffer(raw, np.float32).reshape(-1, ch).astype(np.float64)
    m = a.mean(1, keepdims=True)                     # guion §6: ambiente en mono, al centro
    return np.repeat(m, 2, 1)


def filt(x, tipo, f, orden=2):
    return sosfilt(butter(orden, f, btype=tipo, fs=SR, output='sos'), x, axis=0)


def tramo(a, src0, f0, f1, fade=0.005):
    """audio de la fuente desde src0 (s) colocado en el máster de f0 a f1 (exclusivo), fundidos de 5 ms."""
    i0, i1 = int(round(C(f0) * SR)), int(round(C(f1) * SR)); n = i1 - i0
    s0 = int(round(src0 * SR)); seg = a[s0:s0 + n].copy()
    if len(seg) < n: seg = np.vstack([seg, np.zeros((n - len(seg), 2))])
    k = int(fade * SR); r = np.ones(n); r[:k] = np.linspace(0, 1, k); r[-k:] = np.linspace(1, 0, k)
    out = np.zeros((N, 2)); out[i0:i1] = seg * r[:, None]; return out


def put(buf, sig, t0, g=1.0, pan=0.0):
    if sig.ndim == 1: sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1)
    i = int(round(t0 * SR)); j = min(N, i + len(sig))
    if j > max(i, 0): buf[max(i, 0):j] += g * sig[max(0, -i):j - i]


def db(x): return 10 ** (x / 20)
def pico_a(sig, dbfs): return sig / (np.abs(sig).max() + 1e-12) * db(dbfs)

# ---------------- A) ambiente real ----------------
a41, a84, a27, a57, a25 = leer('IMG_4641'), leer('IMG_7884'), leer('IMG_4627'), leer('IMG_7857'), leer('IMG_4625')
amb = np.zeros((N, 2))
amb += tramo(a41, 18 / 30, 0, 46)                        # P1: 4641 c18-c63 (crece solo)
amb += tramo(a84, 105 / 30, 46, 63)                      # P2: 7884 c105-c121 (golpe real 3,53 s -> f46,9)
p3 = tramo(a27, 333 / 30, 63, 94)                        # P3: 4627 c333-c363 (pico real 11,35 s -> f70,5)
g3 = np.ones(N); u = np.clip((t - C(74)) / (C(78) - C(74)), 0, 1); g3 *= 1 - (1 - db(-ATT)) * (0.5 - 0.5 * np.cos(np.pi * u))
p3 *= g3[:, None]; amb += p3                             # f74-f78: baja ATT dB -> casi silencio hasta f93
a57f = filt(a57, 'high', 150)                            # P5: 7857 2,0-4,0 s, -20 dB, pasaaltos 150 Hz (viento)
p5 = tramo(a57f, 60 / 30, 124, 184) * db(-20)
u1 = np.clip(np.minimum((t - 5.20) / 0.04, (5.42 - t) / 0.04), 0, 1); p5 *= (1 - (1 - db(-6)) * u1)[:, None]  # ráfaga 3,07-3,29 s fuente
amb += p5
amb += tramo(a25, 15 / 30, 184, FIN_P6) * db(-6)         # P6: 4625 c15-c59 (v1.1: c15-c89), bajo
ev['ambiente'] = {'P1': '4641 fuente 0,600-2,133 s -> f0-f45', 'P2': '7884 fuente 3,500-4,067 s -> f46-f62',
                  'P3': f'4627 fuente 11,100-12,133 s -> f63-f93; baja {ATT:.1f} dB entre f74 y f78 (coseno) y queda así hasta f93',
                  'P4': 'sin ambiente', 'P5': '7857 fuente 2,000-4,000 s -> f124-f183, pasaaltos 150 Hz, -20 dB, ráfaga 3,07-3,29 s fuente -6 dB',
                  'P6': f'4625 fuente 0,500-{0.5 + (FIN_P6 - 184) / 30:.3f} s -> f184-f{FIN_P6 - 1}, -6 dB'.replace('.', ','), 'P7': 'sin ambiente', 'fundidos_corte_ms': 5}

# ---------------- B) efectos ----------------
fx = np.zeros((N, 2))
def golpe():
    L = int(0.160 * SR); tt = np.arange(L) / SR; f = 58 - 16 * tt / tt[-1]
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.07) * np.minimum(1, tt / 0.003)
    s[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR)); return np.tanh(2.2 * s) / np.tanh(2.2)
def pulso():
    L = int(0.090 * SR); tt = np.arange(L) / SR
    s = np.sin(2 * np.pi * 62 * tt) * np.exp(-tt / 0.035) * np.minimum(1, tt / 0.002)
    s[-int(0.008 * SR):] *= np.linspace(1, 0, int(0.008 * SR)); return np.tanh(2.0 * s) / np.tanh(2.0)
for f, lvl in ((0, -16), (46, -13), (63, -10)):
    put(fx, pico_a(golpe(), lvl), C(f)); ev['eventos'].append({'cuadro': f, 'evento': 'golpe seno 58→42 Hz 160 ms', 'pico_pre_dBFS': lvl})
for f, lvl in ((0, -24), (15, -24), (30, -24), (54, -22), (68, -20), (72, -20)):   # f0: el guion pide golpe 1 «y pulso»
    put(fx, pico_a(pulso(), lvl), C(f)); ev['eventos'].append({'cuadro': f, 'evento': 'pulso 62 Hz 90 ms', 'pico_pre_dBFS': lvl})
L = int(0.25 * SR); tt = np.arange(L) / SR
raf = filt(rng.standard_normal((L, 2)), 'band', [400, 7000]) * np.exp(-tt / 0.07)[:, None] * np.minimum(1, tt / 0.002)[:, None]
put(fx, pico_a(raf, -14), C(94)); ev['eventos'].append({'cuadro': 94, 'evento': 'ráfaga de ruido 250 ms (400-7000 Hz)', 'pico_pre_dBFS': -14})
def clic():
    L = int(0.06 * SR); tt = np.arange(L) / SR
    return (np.sin(2 * np.pi * 1500 * tt) + 0.5 * np.sin(2 * np.pi * 120 * tt)) * np.exp(-tt / 0.012) * np.minimum(1, tt / 0.001)
put(fx, pico_a(clic(), -24), C(F_CLIC)); ev['eventos'].append({'cuadro': F_CLIC, 'evento': 'clic suave', 'pico_pre_dBFS': -24})

# ---------------- C) música 120 BPM ----------------
mus = np.zeros((N, 2)); BEAT = 0.5; T0 = C(94)
def env(L, a, r):
    e = np.minimum(1, np.arange(L) / SR / max(a, 1e-4)); k = min(L, int(r * SR))
    if k > 0: e[-k:] *= np.linspace(1, 0, k) ** 1.5
    return e
def saw(f, L, det=0.0):
    tt = np.arange(L) / SR; y = np.zeros(L)
    for k in range(1, int(min(40, 9000 / f)) + 1): y += np.sin(2 * np.pi * k * f * (1 + det) * tt + rng.uniform(0, 6.28)) / k
    return y * 0.55
def pad(notas, L, brillo):
    iz = sum(saw(hz(n), L, -0.004) + saw(hz(n), L, 0.003) for n in notas); de = sum(saw(hz(n), L, 0.004) + saw(hz(n), L, -0.002) for n in notas)
    return filt(np.stack([iz, de], 1) / (2 * len(notas)), 'low', brillo)
def kick():
    L = int(0.42 * SR); tt = np.arange(L) / SR; f = 46 + 74 * np.exp(-tt / 0.032)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.22) + 0.18 * rng.standard_normal(L) * np.exp(-tt / 0.003)
    return s * np.minimum(1, tt / 0.0015)
def clap():
    L = int(0.35 * SR); tt = np.arange(L) / SR; n = filt(rng.standard_normal(L), 'band', [900, 2600]); e = np.exp(-tt / 0.09) * 0.6
    for d in (0.0, 0.011, 0.022): e += np.exp(-np.maximum(0, tt - d) / 0.006) * (tt >= d) * 0.5
    return n * e
def hat(dec=0.028):
    L = int(0.25 * SR); tt = np.arange(L) / SR; return filt(rng.standard_normal(L), 'high', 7000) * np.exp(-tt / dec) * 0.6
def bajo(nota, L):
    tt = np.arange(L) / SR; f = hz(nota); s = np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt)
    return np.tanh(1.6 * s) * env(L, 0.004, min(0.08, L / SR / 2))
def pluck(nota):
    L = int(0.35 * SR); tt = np.arange(L) / SR
    return filt(saw(hz(nota), L), 'low', 3500) * np.exp(-tt / 0.10) * np.minimum(1, tt / 0.002)
def reverb(st, seg=1.6, mezcla=0.25):
    L = int(seg * SR); tt = np.arange(L) / SR
    ir = [filt(rng.standard_normal(L), 'low', 6000) * np.exp(-tt / (seg / 6)) for _ in range(2)]
    w = np.stack([fftconvolve(st[:, c], ir[c])[:len(st)] for c in range(2)], 1)
    w *= np.sqrt(np.mean(st ** 2) / (np.mean(w ** 2) + 1e-12)); return st * (1 - mezcla) + w * mezcla

ACORDES = [('Am', 94, [57, 60, 64, 69], 33), ('F', 154, [53, 57, 60, 65], 29), ('G', 214, [55, 59, 62, 67], 31), ('C', 274, [60, 64, 67, 72], 36)]
pads = np.zeros((N, 2)); arp = np.zeros((N, 2))
for k, (nom, f0, notas, raiz) in enumerate(ACORDES):
    fin = 307 if nom == 'C' else ACORDES[k + 1][1]
    L = int(round((C(fin) - C(f0)) * SR)) + int(0.05 * SR)
    brillo = 1800 if f0 < 184 else 2600
    put(pads, pad(notas, L, brillo) * env(L, 0.02 if f0 == 94 else 0.06, 0.05)[:, None], C(f0), 0.55)
    ev['eventos'].append({'cuadro': f0, 'evento': f'acorde {nom}' + (' sostenido' if nom == 'C' else '')})
    # bajo en negras (en C: una nota larga)
    if nom != 'C':
        for b in range(4):
            put(mus, bajo(raiz, int(0.45 * SR)), C(f0) + b * BEAT, 0.55)
    else:
        put(mus, bajo(raiz, int((C(307) - C(274)) * SR)), C(274), 0.55)
    # arpegio desde f184 (corcheas) hasta f273
    for e8 in range(8):
        te = C(f0) + e8 * 0.25
        if C(184) - 1e-6 <= te < C(274) - 1e-6:
            put(arp, pluck(notas[[0, 1, 2, 3, 2, 1, 3, 2][e8]] + 12), te, 0.30, pan=(-0.3 if e8 % 2 else 0.3))
mus += reverb(pads, 1.8, 0.28) + reverb(arp, 1.2, 0.22)
batt = np.zeros((N, 2))
for b in range(13):                                     # tiempos f94 ... f274
    tb = T0 + b * BEAT; fb = 94 + 15 * b
    if fb <= 274 and b % 2 == 0: put(batt, kick(), tb, 0.9)
    if fb < 274 and b % 2 == 1: put(batt, clap(), tb, 0.35, pan=0.05)
for e8 in range(40):                                    # corcheas desde f124 hasta antes de f274
    te = C(124) + e8 * 0.25
    if te >= C(274) - 1e-6: break
    abierto = te >= C(184) - 1e-6 and e8 % 2 == 1
    put(batt, hat(0.11 if abierto else 0.028), te, 0.22 if abierto else 0.16, pan=0.25)
ev['eventos'] += [{'cuadro': 94, 'evento': 'entra la música: bombo + bajo + Am'}, {'cuadro': 124, 'evento': 'charles en corcheas'},
                  {'cuadro': 184, 'evento': 'charles abierto (contratiempos) y arpegio'}, {'cuadro': 274, 'evento': 'último bombo; acorde C sostenido'}]
mus += batt
fade = np.ones(N); u = np.clip((t - C(295)) / (C(307) - C(295)), 0, 1); fade *= np.cos(0.5 * np.pi * u)
mus *= fade[:, None]; mus[:int(C(94) * SR)] = 0
ev['eventos'].append({'cuadro': 295, 'evento': 'fundido final 0,4 s (f295-f306)'})


def sonoridad(x):
    """LUFS sin compuerta (BS.1770, filtro K por FFT)."""
    X = np.fft.rfft(x, axis=0); w = 2 * np.pi * np.fft.rfftfreq(len(x), 1 / SR) / SR; z = np.exp(-1j * w)
    hh = lambda b, a: (b[0] + b[1] * z + b[2] * z ** 2) / (a[0] + a[1] * z + a[2] * z ** 2)
    H = hh([1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585]) * hh([1, -2, 1], [1, -1.99004745483398, 0.99007225036621])
    y = np.fft.irfft(X * H[:, None], len(x), axis=0); return -0.691 + 10 * np.log10(np.sum(np.mean(y ** 2, 0)) + 1e-15)

# nivel de la música: en P5 (f124-f183) 1 LU por encima de la sonoridad del tramo de olas f46-f73 (ambiente + efectos)
olas = amb + fx; i_a, i_b = int(C(46) * SR), int(C(74) * SR); j_a, j_b = int(C(124) * SR), int(C(184) * SR)
gm = db(sonoridad(olas[i_a:i_b]) + 1 - sonoridad(mus[j_a:j_b])); mus *= gm
mezcla = amb + fx + mus
ev['niveles_pre'] = {'LUFS_sin_compuerta_olas_f46-f73': round(sonoridad(olas[i_a:i_b]), 2), 'LUFS_musica_P5': round(sonoridad(mus[j_a:j_b]), 2),
                     'ganancia_musica_dB': round(20 * np.log10(gm), 2), 'atenuacion_casi_silencio_dB': ATT,
                     'rms_f78-f93_pre_dBFS': round(20 * np.log10(np.sqrt(np.mean(mezcla[int(C(78) * SR):int(C(94) * SR)] ** 2)) + 1e-12), 2)}

def escribir(nombre, x):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_f32le', os.path.join(D, nombre)],
                   input=x.astype(np.float32).tobytes(), check=True)
for nom, x in (('mezcla_pre.wav', mezcla), ('pista_ambiente.wav', amb), ('pista_efectos.wav', fx), ('pista_musica.wav', mus)):
    escribir(nom, x)
ev['muestras'] = N; ev['duracion_s'] = N / SR
json.dump(ev, open(os.path.join(D, 'mezcla_eventos.json'), 'w'), indent=1, ensure_ascii=False)
print(json.dumps(ev['niveles_pre'], ensure_ascii=False))
