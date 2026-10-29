# Sonido de ROCCE_ANTES_DEL_APLAUSO, sintetizado (sin material de terceros) y ubicado con la línea de tiempo de la
# escena (eventos.json, que exporta render.js):
#   - aplauso breve: un golpe por cada contacto de las manos dibujadas (cuadro 1 incluido) y se apaga a los ~2 s;
#   - el trabajo de abajo: lápiz (roce que sigue el trazo, con cortes en los vértices de la estrella), tirón y vuelo
#     de la hoja, caída sobre la pila, firma, subrayado, pasos, despegue de la hoja firmada;
#   - acentos: chispa que llega a la etiqueta de Roccé, entrada del CTA, tarjeta que sube, paso al cierre;
#   - música original contenida: pulso grave + pulsación de piano suave (Re menor, 100 BPM) desde que empieza el
#     proceso; se abre en el CTA y resuelve en el cierre (sin silencio final).
# Salidas (48 kHz estéreo): musica.wav, fx.wav, voz.wav (frases en sus tiempos), y las mezclas
#   mezcla_voz.wav (con locución Firme 04, música y efectos bajan con la voz) y mezcla_sin_voz.wav.
# Uso: python sonido.py EVENTOS.json VOZ_DIR SALIDA_DIR
import sys, json, os
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

ev, vozdir, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
TL = ev["TL"]; SR = 48000; DUR = TL["dur"]; N = int(round(DUR * SR))
rng = np.random.default_rng(17)
mus, fx = np.zeros((N, 2)), np.zeros((N, 2))

def put(buf, sig, t0, g=1.0, pan=0.0):
    if sig.ndim == 1: sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1)
    i = int(round(t0 * SR)); j = min(N, i + len(sig))
    if j > max(i, 0): buf[max(i, 0):j] += g * sig[max(0, -i):j - i]
def filt(x, tipo, f, o=2): return sosfilt(butter(o, f, btype=tipo, fs=SR, output="sos"), x, axis=0)
def db(v): return 10 ** (v / 20)
def norm(x): return x / (np.abs(x).max() + 1e-9)
def env(L, a, d):
    t = np.arange(L) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def ruido(L): return rng.standard_normal(L)
def sala(x, seg=0.9, mezcla=0.18):
    L = int(seg * SR); t = np.arange(L) / SR
    ir = rng.standard_normal(L) * np.exp(-t / (seg / 5)); ir = filt(ir, "lowpass", 5000)
    y = fftconvolve(x, ir)[:len(x)] if x.ndim == 1 else np.stack([fftconvolve(x[:, c], ir)[:len(x)] for c in range(2)], 1)
    return x * (1 - mezcla) + norm(y) * np.abs(x).max() * mezcla

# ---------------- efectos
def palmada():
    L = int(0.16 * SR); x = np.zeros(L)
    for k in range(rng.integers(2, 4)):                 # varias capas: la palmada real tiene micro-golpes
        o = int(rng.uniform(0, 0.006) * SR); n = filt(ruido(L - o), "bandpass", [rng.uniform(700, 1100), rng.uniform(3200, 5200)])
        x[o:] += n * env(L - o, 0.0006, rng.uniform(0.012, 0.03))
    x += 0.35 * filt(ruido(L), "bandpass", [180, 500]) * env(L, 0.001, 0.02)
    return norm(x)
for g in ev["golpes"]:
    t = g["t"]; ap = db(-3) * (1 - 0.85 * min(1, max(0, (t - 1.3) / 1.0)))
    put(fx, palmada(), t, 0.9 * ap * db(rng.uniform(-2, 0)), pan=(-0.45 if g["par"] == 0 else 0.45) + rng.uniform(-0.1, 0.1))
    # algún aplauso más lejano (pocas personas fuera de cuadro), muy bajo
    if rng.random() < 0.6: put(fx, palmada(), t + rng.uniform(0.04, 0.12), 0.25 * ap, pan=rng.uniform(-0.8, 0.8))

def lapiz(d, ritmo=None, g=1.0, cortes=()):
    L = int(d * SR); t = np.arange(L) / SR
    n = filt(ruido(L), "bandpass", [2200, 7500]) + 0.5 * filt(ruido(L), "bandpass", [700, 1800])
    a = 0.65 + 0.35 * np.abs(filt(ruido(L), "lowpass", 9))  # presión que varía
    a /= a.max()
    if ritmo: a *= 0.55 + 0.45 * np.abs(np.sin(np.pi * ritmo * t))
    for c in cortes:                                       # el lápiz frena en los vértices
        a *= 1 - 0.85 * np.exp(-((t - c) / 0.025) ** 2)
    a *= np.minimum(1, t / 0.02) * np.minimum(1, (d - t) / 0.03)
    return norm(n * a) * g
def tirar_hoja():
    L = int(0.2 * SR); t = np.arange(L) / SR
    x = np.zeros(L)
    for k in range(40):                                    # desgarro: chasquidos de fibras
        o = int(rng.uniform(0, 0.17) * SR); m = min(L - o, int(0.006 * SR))
        x[o:o + m] += filt(ruido(m), "bandpass", [1500, 7000]) * rng.uniform(0.3, 1)
    x += 0.4 * filt(ruido(L), "bandpass", [600, 3000]) * np.exp(-t / 0.08)
    return norm(x)
def aire(d, f0=300, f1=2500, sube=True):
    L = int(d * SR); t = np.arange(L) / SR; n = ruido(L); y = np.zeros(L); s = 512
    for k in range(0, L, s):
        u = k / L; fc = (f0 + (f1 - f0) * u) if sube else (f1 + (f0 - f1) * u)
        y[k:k + s] = filt(n[k:k + s + 256], "bandpass", [fc * 0.6, min(SR / 2 - 100, fc * 1.5)])[:len(y[k:k + s])]
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    return norm(y * e)
def papel_cae():
    L = int(0.18 * SR); return norm(filt(ruido(L), "bandpass", [250, 2200]) * env(L, 0.002, 0.035))
def golpe_suave(f=70, d=0.35):
    L = int(d * 2 * SR); t = np.arange(L) / SR
    fr = f * (1 + 0.6 * np.exp(-t / 0.03)); x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / d)
    return norm(x + 0.2 * filt(ruido(L), "lowpass", 600) * np.exp(-t / 0.02))
def campanita(f=1568, d=0.9):
    L = int(d * 2 * SR); t = np.arange(L) / SR
    x = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / (d / m ** 0.7)) for m, a in ((1, 1), (2.01, 0.35), (3.02, 0.12)))
    return norm(x * np.minimum(1, t / 0.003))
def clic():
    L = int(0.03 * SR); return norm(filt(ruido(L), "bandpass", [2500, 9000]) * env(L, 0.0003, 0.004))
def paso():
    L = int(0.12 * SR); g = np.zeros(L); gs = golpe_suave(90, 0.05)[:L]; g[:len(gs)] = gs
    return norm(filt(ruido(L), "lowpass", 900) * env(L, 0.003, 0.03) + 0.4 * g)

T = {k: v for k, v in TL.items() if isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)}
d1 = T["dibujo1"]; put(fx, lapiz(d1[1] - d1[0], g=1.0, cortes=(0.42, 0.75)), d1[0], db(-9), 0.15)
put(fx, lapiz(0.3, ritmo=14), d1[1] - 0.3, db(-8), 0.15)                       # la línea que se va: más nerviosa
put(fx, clic(), T["mira"][0] + 0.02, db(-24), 0.1)                               # levanta el lápiz
put(fx, tirar_hoja(), T["vuela1"][0], db(-9), 0.1)
put(fx, aire(T["vuela1"][1] - T["vuela1"][0] - 0.1, 400, 1800), T["vuela1"][0] + 0.12, db(-20), 0.4)
put(fx, papel_cae(), T["vuela1"][1], db(-14), 0.5)
d2 = T["dibujo2"]; L2 = d2[1] - d2[0]
put(fx, lapiz(L2, g=1.0, cortes=[L2 * k / 5 for k in range(1, 5)]), d2[0], db(-8), 0.15)
fi = T["firma"]; put(fx, lapiz(fi[1] - fi[0], ritmo=8.5 / (fi[1] - fi[0]) * 2), fi[0], db(-8), 0.15)
su = T["subraya"]; put(fx, lapiz(su[1] - su[0]), su[0], db(-8), 0.15)
ch = T["chispa"]; put(fx, aire(ch[1] - ch[0], 1500, 6000), ch[0], db(-28), 0.4); put(fx, campanita(1760, 0.7), ch[1], db(-20), 0.5)
c1 = TL["cta1"][0]; put(fx, aire(0.3, 300, 2500), c1 - 0.25, db(-22)); put(fx, clic(), c1 + 0.02, db(-18)); put(fx, golpe_suave(65, 0.3), c1, db(-14))
for a, b in (T["atras"], T["adelante"]):
    put(fx, paso(), a + 0.1, db(-24), -0.2); put(fx, paso(), (a + b) / 2 + 0.08, db(-25), 0.1)
lv = T["levanta"]; put(fx, tirar_hoja() * 0.5, lv[1] - 0.35, db(-17), 0.1)
tj = T["tarjeta"]; put(fx, aire(tj[1] - tj[0], 300, 3000), tj[0], db(-17)); put(fx, papel_cae(), tj[1], db(-15), 0.3); put(fx, campanita(1318, 0.9), tj[1] + 0.02, db(-22), 0.3)
ci = TL["cierre"]; put(fx, aire(ci[1] - ci[0] + 0.05, 200, 4000), ci[0], db(-16)); put(fx, golpe_suave(55, 0.5), ci[1], db(-11))
put(fx, campanita(1175, 1.4), ci[1] + 0.03, db(-24), -0.2); put(fx, campanita(1760, 1.2), ci[1] + 0.33, db(-27), 0.2)
fx = sala(fx, 0.7, 0.14)

# ---------------- música (Re menor, 100 BPM, grilla desde el comienzo del proceso)
BPM = 100; B = 60 / BPM; G0 = 1.86
hz = lambda n: 440 * 2 ** ((n - 69) / 12)
def piano(f, d=1.2, g=1.0):
    L = int(d * SR); t = np.arange(L) / SR
    x = sum(a * np.sin(2 * np.pi * f * m * t + rng.uniform(0, 6)) * np.exp(-t * (2.2 + 1.6 * m)) for m, a in ((1, 1), (2, 0.42), (3, 0.16), (4, 0.07)))
    return norm(x * np.minimum(1, t / 0.004)) * g
def bombo(g=1.0):
    L = int(0.4 * SR); t = np.arange(L) / SR; f = 46 + 70 * np.exp(-t / 0.035)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)) * g
def charles(g=1.0):
    L = int(0.06 * SR); return norm(filt(ruido(L), "highpass", 7000) * env(L, 0.0005, 0.012)) * g
def colchon(notas, d, g=1.0):
    L = int(d * SR); t = np.arange(L) / SR; x = np.zeros(L)
    for n in notas:
        for det in (-0.12, 0.0, 0.12):
            f = hz(n + det / 10); x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) + 0.3 * np.sin(4 * np.pi * f * t)
    x = filt(x, "lowpass", 1400)
    a = np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.6)
    return norm(x * np.clip(a, 0, 1)) * g
ACORDES = [[50, 57, 62, 65], [46, 53, 58, 62], [41, 48, 53, 57], [48, 55, 60, 64]]     # Rem – Sib – Fa – Do
ARPEGIO = [0, 2, 1, 3, 2, 1, 3, 2]                                                       # índices de nota por corchea
fin_proceso = TL["cierre"][1]
n_beats = int((DUR - G0) / B) + 1
for b in range(n_beats):
    tb = G0 + b * B
    if tb >= DUR - 0.05: break
    compas, tiempo = divmod(b, 4)
    ac = ACORDES[compas % 4]
    abre = tb >= TL["cta1"][0] - 0.05
    cierre_ = tb >= fin_proceso - 0.05
    if not cierre_:
        put(mus, bombo(), tb, db(-12 if tiempo in (0, 2) else -17) * (1.0 if abre else 0.8))
        for k in range(2):                              # corcheas de piano suave
            n = ac[ARPEGIO[(tiempo * 2 + k) % 8]] + 12
            put(mus, piano(hz(n), 0.9), tb + k * B / 2, db(-22 if not abre else -20), pan=(-0.25 if k else 0.25))
        if abre: put(mus, charles(), tb + B / 2, db(-26), 0.3)
    if tiempo == 0 and not cierre_:
        put(mus, colchon(ac, min(4 * B, DUR - tb), db(-19)), tb, 1.0)
# resolución en el cierre: Fa mayor abierto que se sostiene hasta el final (sin silencio)
t_res = fin_proceso
put(mus, colchon([41, 53, 57, 60, 65], DUR - t_res + 0.2, db(-14)), t_res - 0.05, 1.0)
for k, n in enumerate([65, 69, 72, 77]): put(mus, piano(hz(n), 1.8), t_res + k * 0.09, db(-16), pan=0.15 * (k - 1.5))
# entrada del pulso: un respiro antes de arrancar (el aplauso queda solo)
mus *= np.minimum(1, np.maximum(0, (np.arange(N) / SR - (G0 - 0.25)) / 0.25))[:, None]
mus = sala(mus, 1.4, 0.22)
# final: sin corte en seco
fade = np.ones(N); k = int(0.5 * SR); fade[-k:] = np.linspace(1, 0.25, k) ** 1.2
mus *= fade[:, None]; fx *= fade[:, None]

# ---------------- voz (Firme 04) en sus tiempos
voz = np.zeros((N, 2)); info = json.load(open(os.path.join(vozdir, "locucion.json")))
fr = info if isinstance(info, list) else info.get("frases", info)
for fid, t0 in TL["voz"].items():
    y, sr = sf.read(os.path.join(vozdir, f"{fid}.wav"), always_2d=True)
    assert sr == SR, sr
    y = y.mean(1); put(voz, y, t0, 1.0)

def sidechain(x, clave, prof_db=-9, ata=0.03, sol=0.25):
    e = np.abs(clave).max(1); w = int(0.02 * SR)
    e = np.convolve(e, np.ones(w) / w, "same"); on = (e > db(-40)).astype(float)
    g = np.zeros(N); a_at, a_sol = np.exp(-1 / (ata * SR)), np.exp(-1 / (sol * SR)); s = 0.0
    for i in range(N):
        tgt = on[i]; s = a_at * s + (1 - a_at) * tgt if tgt > s else a_sol * s + (1 - a_sol) * tgt; g[i] = s
    return x * (1 - (1 - db(prof_db)) * g)[:, None]
sf.write(os.path.join(out, "musica.wav"), mus, SR, subtype="FLOAT")
sf.write(os.path.join(out, "fx.wav"), fx, SR, subtype="FLOAT")
sf.write(os.path.join(out, "voz.wav"), voz, SR, subtype="FLOAT")
con = voz * db(0) + sidechain(mus, voz, -9) + sidechain(fx, voz, -7)
sin = mus * db(1.5) + fx
sf.write(os.path.join(out, "mezcla_voz.wav"), con, SR, subtype="FLOAT")
sf.write(os.path.join(out, "mezcla_sin_voz.wav"), sin, SR, subtype="FLOAT")
# medición voz contra fondo, frase por frase
fondo = sidechain(mus, voz, -9) + sidechain(fx, voz, -7)
for fid, t0 in TL["voz"].items():
    a, b = int(t0 * SR), int((t0 + 1.2) * SR)
    rv = np.sqrt(np.mean(voz[a:b] ** 2)) + 1e-9; rf = np.sqrt(np.mean(fondo[a:b] ** 2)) + 1e-9
    print(f"{fid}: voz sobre fondo {20 * np.log10(rv / rf):+.1f} dB")
print("listo", out, f"{DUR:.2f} s")
