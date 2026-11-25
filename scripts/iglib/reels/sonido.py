# Sonido de IGLIB-1 / IGLIB-2: efectos sintetizados (pulso, clics, barridos, golpes, impactos), ambiente real de
# las tomas propias y música propia sintetizada (sin material de terceros). v02: + locución Firme 04 (voz/locucion.json)
# con el fondo atenuado durante cada frase (ducking por frase con rampas de 60/120 ms, equivalente al sidechain) y
# medición voz/fondo por frase con ponderación K (voz_fondo.json). Uso:
#   env/bin/python sonido.py iglib1|iglib2 SALIDA_DIR                (v01, sin voz)
#   env/bin/python sonido.py iglib1v2|iglib2v2 SALIDA_DIR VOZ_DIR     (v02, con voz: VOZ_DIR/<id>.wav de locucion.py)
#   → SALIDA_DIR/fx.wav, amb.wav, musica.wav, [voz.wav], mezcla.wav (voz + fx+amb+música) y mezcla_sinmusica.wav
#     (voz + fx+amb), 48 kHz estéreo, largo exacto = cuadros × 1600 muestras. eventos.json documenta cada sonido.
import sys, os, json, subprocess
import numpy as np
from scipy.signal import butter, sosfilt
import soundfile as sf

pieza, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
SR = 48000; FPS = 30
NF = {'iglib1': 633, 'iglib2': 408, 'iglib1v2': 885, 'iglib2v2': 528}[pieza]; N = NF * 1600
VOZD = sys.argv[3] if len(sys.argv) > 3 else None; VOCES = []        # (id, cuadro de entrada)
rng = np.random.default_rng(11)
fx = np.zeros((N, 2)); amb = np.zeros((N, 2)); mus = np.zeros((N, 2)); EV = []

def filt(x, tipo, f, orden=2): return sosfilt(butter(orden, f, btype=tipo, fs=SR, output='sos'), x, axis=0)
def db(v): return 10 ** (v / 20)
def put(buf, sig, t0, g=1.0, pan=0.0):
    if sig.ndim == 1: sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1) * np.sqrt(2)
    i = int(round(t0 * SR)); j = min(N, i + len(sig))
    if j > max(i, 0): buf[max(i, 0):j] += g * sig[max(0, -i):j - i]
def norm(s): return s / (np.abs(s).max() + 1e-9)
def ev(tipo, f, **k): EV.append(dict(tipo=tipo, cuadro=f, t=round(f / FPS, 3), **k))

# ---------- efectos
def pulso():
    L = int(0.42 * SR); t = np.arange(L) / SR; f = 44 + 66 * np.exp(-t / 0.03)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.20) * np.minimum(1, t / 0.002)
    s += 0.10 * filt(rng.standard_normal(L), 'low', 900) * np.exp(-t / 0.006); return norm(s)
def golpe(cola=0.9):
    L = int((0.5 + cola) * SR); t = np.arange(L) / SR; f = 32 + 70 * np.exp(-t / 0.05)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.35 * cola + 0.2)) * np.minimum(1, t / 0.002)
    s += 0.45 * filt(rng.standard_normal(L), 'low', 1500) * np.exp(-t / 0.08); return norm(s)
def clic(f0=1900):
    L = int(0.035 * SR); t = np.arange(L) / SR
    s = (np.sin(2 * np.pi * f0 * t) + 0.4 * np.sin(2 * np.pi * 2 * f0 * t)) * np.exp(-t / 0.005) * np.minimum(1, t / 0.0012)
    s += 0.3 * filt(rng.standard_normal(L), 'high', 3000) * np.exp(-t / 0.002); return norm(s)
def barrido(dur, sube=True):
    L = int(dur * SR); u = np.linspace(0, 1, L); n = rng.standard_normal(L)
    lo = filt(n, 'band', [300, 1200]); hi = filt(n, 'band', [1500, 6000])
    e = np.sin(np.pi * u) ** 1.5 if not sube else u ** 1.8 * np.minimum(1, (1 - u) * 12 + 0.0)
    s = (lo * (1 - u) + hi * u) if sube else (hi * (1 - u) + lo * u)
    return norm(s * e)
def subida(dur):
    L = int(dur * SR); u = np.linspace(0, 1, L); t = np.arange(L) / SR
    tono = np.sin(2 * np.pi * np.cumsum(220 + 660 * u ** 2) / SR) * 0.35
    ruido = filt(rng.standard_normal(L), 'high', 2000) * u ** 2
    return norm((tono + ruido) * u ** 2.2)
def tenis():                                      # impacto de raqueta: golpe seco con cuerpo medio
    L = int(0.12 * SR); t = np.arange(L) / SR
    s = filt(rng.standard_normal(L), 'band', [700, 3200]) * np.exp(-t / 0.012)
    s += 0.8 * np.sin(2 * np.pi * 480 * t) * np.exp(-t / 0.02); return norm(s)
def pisada():
    L = int(0.15 * SR); t = np.arange(L) / SR
    s = np.sin(2 * np.pi * np.cumsum(60 + 80 * np.exp(-t / 0.01)) / SR) * np.exp(-t / 0.045)
    s += 0.5 * filt(rng.standard_normal(L), 'band', [400, 2500]) * np.exp(-t / 0.01); return norm(s)
def punete():
    L = int(0.3 * SR); t = np.arange(L) / SR
    s = np.sin(2 * np.pi * np.cumsum(55 + 120 * np.exp(-t / 0.015)) / SR) * np.exp(-t / 0.09)
    s += 0.9 * filt(rng.standard_normal(L), 'band', [600, 4000]) * np.exp(-t / 0.015); return norm(s)

def ambiente(src, a, b, t0, g, fi=0.05, fo=0.05):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a), '-t', str(b - a), '-i', src, '-vn', '-ac', '2', '-ar', str(SR),
                          '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    L = len(x); e = np.ones(L); k1, k2 = int(fi * SR), int(fo * SR)
    if k1: e[:k1] = np.linspace(0, 1, k1)
    if k2: e[-k2:] *= np.linspace(1, 0, k2)
    put(amb, x * e[:, None], t0, g)

# ---------- música propia (re menor)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
def saw(f, L, det=0.0):
    t = np.arange(L) / SR; y = np.zeros(L); nh = int(min(30, 8000 / f))
    for k in range(1, nh + 1): y += np.sin(2 * np.pi * k * f * (1 + det) * t + rng.uniform(0, 6.28)) / k
    return y * 0.5
def pad(notas, dur, brillo=1100, a=0.25, r=0.4):
    L = int(dur * SR); izq = sum(saw(hz(n), L, -0.003) for n in notas); der = sum(saw(hz(n), L, 0.003) for n in notas)
    st = filt(np.stack([izq, der], 1) / len(notas), 'low', brillo); e = np.ones(L); ka, kr = int(a * SR), int(r * SR)
    e[:ka] = np.linspace(0, 1, ka) ** 1.5; e[-kr:] *= np.linspace(1, 0, kr) ** 1.5; return st * e[:, None]
def bajo(n, dur):
    L = int(dur * SR); t = np.arange(L) / SR; s = np.sin(2 * np.pi * hz(n) * t) + 0.3 * np.sin(4 * np.pi * hz(n) * t)
    e = np.minimum(1, t / 0.01) * np.exp(-t / (dur * 0.9)); return s * e
def bombo():
    L = int(0.4 * SR); t = np.arange(L) / SR; f = 46 + 80 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22) * np.minimum(1, t / 0.0015)
def charles(dec=0.03):
    L = int(0.1 * SR); t = np.arange(L) / SR; return filt(rng.standard_normal(L), 'high', 7000) * np.exp(-t / dec)

if pieza == 'iglib1':
    P, G, C, B = pulso(), golpe(), clic(), golpe(0.5)
    # pulso grave cada 0,5 s desde c0; sube en el tramo 3; se acelera en el tramo 6; golpe en 249; corte en 336
    for f in range(0, 204, 15): put(fx, P, f / FPS, db(-15 if f < 87 else -12)); ev('pulso', f)
    for f in [204, 217, 228, 237, 244]: put(fx, P, f / FPS, db(-11)); ev('pulso (acelera)', f)
    put(fx, G, 249 / FPS, db(-6)); ev('golpe grave', 249)
    for f in range(264, 336, 15): put(fx, P, f / FPS, db(-12)); ev('pulso', f)
    ev('pulso cortado / silencio', 336)
    put(fx, C, 53 / FPS, db(-12)); put(fx, clic(3200), 56 / FPS, db(-17)); ev('clic + tic (toca tarjeta 1)', 53)
    for a, b in [(87, 99), (132, 143), (168, 178), (252, 261)]:
        put(fx, barrido((b - a) / FPS + 0.04), a / FPS, db(-20)); put(fx, C, b / FPS, db(-13)); ev('barrido + clic', a, fin=b)
    put(fx, barrido(10 / FPS, sube=False), 309 / FPS, db(-27)); ev('barrido suave (arrastre a medias)', 309)
    put(fx, barrido(10 / FPS + 0.03), 345 / FPS, db(-15)); ev('barrido largo', 345)
    put(fx, G, 355 / FPS, db(-5)); ev('golpe (asienta la tercera tarjeta)', 355)
    put(fx, C, 426 / FPS, db(-10)); put(fx, B, 426 / FPS, db(-8)); ev('clic + golpe (toca GIVE HISTORY YOUR NAME.)', 426)
    put(fx, subida(15 / FPS), 435 / FPS, db(-16)); ev('subida', 435)
    put(fx, B, 450 / FPS, db(-10)); ev('golpe de corte', 450)
    put(fx, tenis(), 479 / FPS, db(-11)); ev('impacto de raqueta (879 cuadro 163)', 479)
    put(fx, B, 489 / FPS, db(-12)); ev('golpe de corte', 489)
    for f in [490, 497, 504, 511, 518, 525]: put(fx, pisada(), f / FPS, db(-15), pan=0.1 * (-1) ** f); ev('pisada', f)
    for f in [534, 554]: put(fx, punete(), f / FPS, db(-9)); ev('puñetazo (40971)', f)
    put(fx, golpe(0.7), 564 / FPS, db(-12)); ev('golpe suave (CTA)', 564)
    # ambiente real de IMG_7859 (mar y viento): tramo 10 (3,50–4,00) bajo; tramo 14 (6,00–8,30)
    ambiente('/home/user/1/ORIGINALES/IMG_7859.mov', 0.50, 3.50, 345 / FPS, db(-17), fi=0.35, fo=0.02); ev('mar real 7859 0,50–3,50 (muy bajo, el video del círculo)', 345)
    ambiente('/home/user/1/ORIGINALES/IMG_7859.mov', 3.50, 4.00, 435 / FPS, db(-12), fi=0.02, fo=0.02); ev('mar real 7859 3,50–4,00 (bajo)', 435)
    ambiente('/home/user/1/ORIGINALES/IMG_7859.mov', 6.00, 8.30, 564 / FPS, db(-6), fi=0.02, fo=0.4); ev('mar real 7859 6,00–8,30', 564)
    # música propia: baja desde el giro (355), arriba en 450–563 (cada corte = cambio de acorde), baja en el CTA
    t0 = 355 / FPS; put(mus, pad([50, 53, 57], 450 / FPS - t0 + 0.2, 800, a=0.6, r=0.3), t0, db(-8)); put(mus, pad([38], 450 / FPS - t0, 300, a=0.6, r=0.3), t0, db(-6))
    ev('música propia entra baja (re menor)', 355)
    beat = 0.65; g0 = 450 / FPS; acordes = [([50, 53, 57], 38), ([46, 50, 53], 34), ([53, 57, 60], 41)]
    cortes = [450, 489, 528, 564]
    for k, (notas, b) in enumerate(acordes):
        ta, tb = cortes[k] / FPS, cortes[k + 1] / FPS
        put(mus, pad(notas, tb - ta + 0.05, 2200, a=0.02, r=0.05), ta, db(-7)); put(mus, bajo(b, tb - ta), ta, db(-6))
    for i in range(6):
        tb_ = g0 + i * beat
        if tb_ < 564 / FPS - 0.05: put(mus, bombo(), tb_, db(-4)); put(mus, charles(), tb_ + beat / 2, db(-17), pan=0.3)
    ev('música arriba (bombo cada 0,65 s, acorde por corte)', 450)
    tc = 564 / FPS; L = N / SR - tc
    put(mus, pad([50, 53, 57, 64], L, 1300, a=0.05, r=0.4), tc, db(-9)); put(mus, bajo(38, L), tc, db(-9)); put(mus, bombo(), tc, db(-6))
    ev('música baja (CTA) y fundido en los últimos 0,4 s', 564)
    fin = np.ones(N); k = int(0.4 * SR); fin[-k:] = np.linspace(1, 0, k) ** 1.4
    mus *= fin[:, None]; amb *= fin[:, None]; fx *= fin[:, None]

if pieza == 'iglib1v2':
    # locución (10_roma_locucion_G1.1.md): cuadro de entrada de cada frase = corte del tramo + 1 (v01 en c0). «Vos.» entra
    # 5 cuadros después del golpe con que asienta la tercera tarjeta (605) para no taparlo.
    VOCES = [('v01', 0), ('v02', 102), ('v03', 155), ('v04', 202), ('v05', 249), ('v06', 322), ('v07', 396), ('v08', 565),
             ('v09', 610), ('v10', 638), ('v11', 679), ('v12', 712), ('v13', 738), ('v14', 775)]
    P, G, C, B = pulso(), golpe(), clic(), golpe(0.5)
    for f in range(0, 321, 15): put(fx, P, f / FPS, db(-15 if f < 154 else -12)); ev('pulso', f)
    for f in [321, 338, 352, 363, 372, 379, 385, 390]: put(fx, P, f / FPS, db(-11)); ev('pulso (acelera)', f)
    put(fx, G, 395 / FPS, db(-6)); ev('golpe grave (se suelta el dedo)', 395)
    for f in range(410, 555, 15): put(fx, P, f / FPS, db(-12)); ev('pulso', f)
    ev('pulso cortado / silencio de la gran pregunta', 555)
    put(fx, C, 109 / FPS, db(-12)); put(fx, clic(3200), 112 / FPS, db(-17)); ev('clic + tic (toca tarjeta 1)', 109)
    for a, b in [(154, 166), (201, 212), (248, 258), (398, 407)]:
        put(fx, barrido((b - a) / FPS + 0.04), a / FPS, db(-20)); put(fx, C, b / FPS, db(-13)); ev('barrido + clic', a, fin=b)
    put(fx, barrido(10 / FPS, sube=False), 528 / FPS, db(-27)); ev('barrido suave (arrastre a medias)', 528)
    put(fx, barrido(38 / FPS + 0.03), 564 / FPS, db(-12)); ev('barrido largo (entra la tercera tarjeta)', 564, fin=602)
    put(fx, G, 605 / FPS, db(-7)); ev('golpe (asienta la tercera tarjeta)', 605)
    put(fx, C, 628 / FPS, db(-10)); put(fx, B, 628 / FPS, db(-8)); ev('clic + golpe (toca GIVE HISTORY YOUR NAME.)', 628)
    put(fx, subida(15 / FPS), 637 / FPS, db(-16)); ev('subida', 637)
    put(fx, B, 678 / FPS, db(-13)); ev('golpe de corte', 678)
    put(fx, tenis(), 707 / FPS, db(-11)); ev('impacto de raqueta (879 cuadro 163)', 707)
    put(fx, B, 711 / FPS, db(-12)); ev('golpe de corte', 711)
    for f in [712, 719, 726, 733]: put(fx, pisada(), f / FPS, db(-15), pan=0.1 * (-1) ** f); ev('pisada', f)
    for f in [744, 764]: put(fx, punete(), f / FPS, db(-9)); ev('puñetazo (40971)', f)
    put(fx, golpe(0.7), 774 / FPS, db(-12)); ev('golpe suave (CTA)', 774)
    # ambiente real de IMG_7859, en sincronía con los cuadros que se ven: círculo (cuadros 15–87), tramo 10 (88–128), CTA (139–249)
    M7 = '/home/user/1/ORIGINALES/IMG_7859.mov'
    ambiente(M7, 15 / 30, 88 / 30, 564 / FPS, db(-13), fi=0.35, fo=0.02); ev('mar real 7859 0,50–2,93 (bajo, video del círculo)', 564)
    ambiente(M7, 88 / 30, 129 / 30, 637 / FPS, db(-8), fi=0.02, fo=0.02); ev('mar real 7859 2,93–4,30', 637)
    ambiente(M7, 139 / 30, 250 / 30, 774 / FPS, db(-6), fi=0.02, fo=0.4); ev('mar real 7859 4,63–8,33', 774)
    # música propia: entra baja cuando asienta la tercera (605), arriba en 678–773 (acorde por corte), baja en el CTA
    t0 = 605 / FPS; put(mus, pad([50, 53, 57], 678 / FPS - t0 + 0.2, 800, a=0.6, r=0.3), t0, db(-8)); put(mus, pad([38], 678 / FPS - t0, 300, a=0.6, r=0.3), t0, db(-6))
    ev('música propia entra baja (re menor)', 605)
    beat = 0.65; g0 = 678 / FPS; acordes = [([50, 53, 57], 38), ([46, 50, 53], 34), ([53, 57, 60], 41)]
    cortes = [678, 711, 738, 774]
    for k, (notas, b) in enumerate(acordes):
        ta, tb = cortes[k] / FPS, cortes[k + 1] / FPS
        put(mus, pad(notas, tb - ta + 0.05, 2200, a=0.02, r=0.05), ta, db(-7)); put(mus, bajo(b, tb - ta), ta, db(-6))
    for i in range(6):
        tb_ = g0 + i * beat
        if tb_ < 774 / FPS - 0.05: put(mus, bombo(), tb_, db(-4)); put(mus, charles(), tb_ + beat / 2, db(-17), pan=0.3)
    ev('música arriba (bombo cada 0,65 s, acorde por corte)', 678)
    tc = 774 / FPS; L = N / SR - tc
    put(mus, pad([50, 53, 57, 64], L, 1300, a=0.05, r=0.4), tc, db(-9)); put(mus, bajo(38, L), tc, db(-9)); put(mus, bombo(), tc, db(-6))
    ev('música baja (CTA) y fundido en los últimos 0,4 s', 774)
    fin = np.ones(N); k = int(0.4 * SR); fin[-k:] = np.linspace(1, 0, k) ** 1.4
    mus *= fin[:, None]; amb *= fin[:, None]; fx *= fin[:, None]

if pieza == 'iglib2v2':
    # IGLIB-2 «Nadie cambia» v02, en loop (528 cuadros). Locución: cada pregunta entra 1 cuadro después del corte; cada
    # «No.» con su sello y su golpe; en el tramo 6 se mantiene el silencio antes del «No.» (pulso cortado en 327, «No.» en 335).
    # Los «No.» entran 2 cuadros después del golpe del sello: el golpe se oye solo y la voz queda arriba del fondo.
    VOCES = [('w01', 0), ('w02', 85), ('w03', 147), ('w04', 174), ('w05', 212), ('w06', 228), ('w07', 273), ('w08', 289),
             ('w09', 337), ('w10', 353), ('w11', 419), ('w12', 455)]
    P, C, B = pulso(), clic(), golpe(0.5)
    # pulso grave cada 0,5 s desde c0 (528 = 35 × 15 + 3: el barrido final termina justo antes del pulso de c0)
    for f in range(0, 316, 15): put(fx, P, f / FPS, db(-14 if f < 84 else -13)); ev('pulso', f)
    ev('pulso cortado / silencio antes del «No.»', 327)
    for a, d in [(84, 0.30), (173, 0.28), (227, 0.28), (288, 0.28)]:
        put(fx, barrido(d), a / FPS - d * 0.6, db(-19)); ev('barrido (corte a la ventana)', a)
    put(fx, barrido(6 / FPS + 0.03, sube=False), 139 / FPS, db(-24)); ev('barrido suave (arrastra la tarjeta)', 139)
    put(fx, golpe(0.45), 145 / FPS, db(-12)); ev('golpe seco (sello «No cambio.»)', 145)
    put(fx, C, 151 / FPS, db(-14)); ev('clic (la tarjeta vuelve)', 151)
    put(fx, golpe(0.45), 210 / FPS, db(-12)); ev('golpe (sello «No.», suelta la pelota)', 210)
    put(fx, tenis(), 271 / FPS, db(-13)); put(fx, golpe(0.45), 271 / FPS, db(-13)); ev('impacto de raqueta + golpe (sello «No.»; 876 cuadro 50)', 271)
    put(fx, golpe(0.6), 335 / FPS, db(-9)); ev('golpe tardío (sello «No.»)', 335)
    M46 = '/home/user/1/ORIGINALES/IMG_4627.mov'
    ambiente(M46, 287 / 30, 349 / 30, 352 / FPS, db(-6), fi=0.03, fo=0.03); ev('mar real 4627 9,57–11,63 (cuadros 287–348)', 352)
    put(fx, golpe(0.8), 395 / FPS, db(-15)); ev('acento grave en la ola (4627 cuadro ≈ 330)', 395)
    put(fx, subida(0.4), 417 / FPS - 0.4, db(-20)); put(fx, golpe(), 417 / FPS, db(-12)); ev('subida + golpe grave (sello «Tampoco.»)', 417)
    ambiente(M46, 349 / 30, 405 / 30, 454 / FPS, db(-6), fi=0.05, fo=0.05); ev('mar real 4627 11,63–13,50 (cuadros 349–404)', 454)
    put(fx, golpe(0.6), 454 / FPS, db(-14)); ev('golpe suave (CTA)', 454)
    d = 18 / FPS; put(fx, barrido(d), (528 - 18) / FPS, db(-17)); ev('barrido que termina en la fase del pulso de c0', 510, fin=528)
    # música propia (re menor) desde «Tampoco.»: colchón + bajo + bombo suave; se apaga en el tramo 10 (c0 no tiene música)
    t0 = 417 / FPS; t1 = 510 / FPS; L = t1 - t0 + 0.25
    put(mus, pad([50, 53, 57, 62], L, 1500, a=0.6, r=0.3), t0, db(-10)); put(mus, bajo(38, t1 - 437 / FPS + 0.25), 437 / FPS, db(-7))   # crece debajo de «Tampoco.»; el bajo entra al terminar la palabra
    for tb_ in [454 / FPS, 454 / FPS + 0.65, 454 / FPS + 1.30]: put(mus, bombo(), tb_, db(-6))
    ev('música propia entra con «Tampoco.» y se apaga en el tramo 10', 417)
    fin = np.ones(N); i0 = int(510 / FPS * SR); fin[i0:] = np.linspace(1, 0, N - i0) ** 2; mus *= fin[:, None]

# ---------- locución + atenuación del fondo durante cada frase + medición voz/fondo (ponderación K, BS.1770)
def kpond(x):
    from scipy.signal import lfilter
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585], x, axis=0)
    return lfilter([1, -2, 1], [1, -1.99004745483398, 0.99007225036621], y, axis=0)
def nivel(x): y = kpond(x); return 10 * np.log10(np.mean(np.sum(y ** 2, axis=1)) + 1e-12) - 0.691
voz = np.zeros((N, 2)); duck = np.ones(N); tramos_voz = []
ATEN = {'fx': -3, 'amb': -4, 'mus': -15}           # dB durante la frase (medido: voz 10–15 dB sobre el fondo)
if VOCES:
    for vid, f0 in VOCES:
        x, sr = sf.read(f'{VOZD}/{vid}.wav'); assert sr == SR
        i = int(round(f0 / FPS * SR)); j = min(N, i + len(x)); voz[i:j] += x[:j - i, None] * np.array([1.0, 1.0])
        tramos_voz.append((vid, i, j)); ev('voz ' + vid, f0, fin=round(j / SR * FPS, 1))
    act = np.zeros(N)
    for vid, i, j in tramos_voz: act[max(0, i - int(0.06 * SR)):min(N, j + int(0.12 * SR))] = 1
    # rampas: baja en 60 ms, vuelve en 120 ms (filtro de un polo en las dos direcciones)
    from scipy.signal import lfilter
    a = np.exp(-1 / (0.03 * SR)); env = lfilter([1 - a], [1, -a], act); env = np.maximum(env, lfilter([1 - a], [1, -a], act[::-1])[::-1])
    env = np.clip(env * 1.05, 0, 1)
    g = {k: db(v * env) for k, v in ATEN.items()}     # 0 dB fuera de las frases, ATEN dentro
    fx_d, amb_d, mus_d = fx * g['fx'][:, None], amb * g['amb'][:, None], mus * g['mus'][:, None]
else:
    fx_d, amb_d, mus_d = fx, amb, mus
fondo = fx_d + amb_d + mus_d * db(-3); fondo_sm = fx_d + amb_d
med = []
for vid, i, j in tramos_voz:
    med.append(dict(id=vid, desde=round(i / SR, 3), hasta=round(j / SR, 3), voz_LKFS=round(nivel(voz[i:j]), 1),
                    fondo_LKFS=round(nivel(fondo[i:j]), 1), voz_sobre_fondo_dB=round(nivel(voz[i:j]) - nivel(fondo[i:j]), 1),
                    voz_sobre_fondo_sinmusica_dB=round(nivel(voz[i:j]) - nivel(fondo_sm[i:j]), 1)))
if med:
    json.dump(med, open(f'{out}/voz_fondo.json', 'w'), indent=1, ensure_ascii=False)
    for m in med: print(f"{m['id']}  voz/fondo {m['voz_sobre_fondo_dB']:5.1f} dB   sin música {m['voz_sobre_fondo_sinmusica_dB']:5.1f} dB")
    sf.write(f'{out}/voz.wav', voz.astype(np.float32), SR, subtype='FLOAT')
for nom, buf in [('fx', fx), ('amb', amb), ('musica', mus)]: sf.write(f'{out}/{nom}.wav', buf.astype(np.float32), SR, subtype='FLOAT')
sf.write(f'{out}/mezcla.wav', (voz + fondo).astype(np.float32), SR, subtype='FLOAT')
sf.write(f'{out}/mezcla_sinmusica.wav', (voz + fondo_sm).astype(np.float32), SR, subtype='FLOAT')
json.dump(EV, open(f'{out}/eventos.json', 'w'), indent=1, ensure_ascii=False)
print('sonido listo', out, N, 'muestras')
