#!/usr/bin/env python3
"""GTA6 «La misión» · efectos propios y ambiente real (Pedro, 19/11/2026). Guion §3 (columna Sonido) y §8, D = 16,00.

Todo sintetizado acá o con scripts/fmt/sonido.py (Mezcla, sin modificarlo): ningún sonido de Rockstar, ninguna voz.
Sin música: Legacy no llegó. En la animática va un clic de tempo PROVISORIO a 100 BPM (pista «clic_TEMP»), anclado a D
(D cae en tiempo fuerte; compás de 4 = 2,4 s), que NO es la grilla de Legacy.
Los tiempos de los efectos atados a planos generados (piques, faja, rodar, barra, motor) son los OBJETIVO del guion: se
vuelven a medir sobre cada clip cuando exista (están marcados «a medir» en la línea de tiempo).
Ambiente real después de D a −12 dB: se interpreta como 12 LU debajo del objetivo de la mezcla (−14 LUFS, donde va a ir
Legacy): el ambiente 16,00–21,57 sale con −26 LUFS integrados medidos sobre esa pista sola.

Salidas en TRABAJO/gta/audio/: fx.wav, amb.wav, clic_TEMP.wav, mezcla_animatica.wav (+ eventos.json, niveles.json).
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/gta'); sys.path.insert(0, '/home/user/1/scripts/fmt')
from comun import T, D, FPS, guardar_json      # noqa
import sonido as S                             # noqa: E402  (Mezcla, filt, env, satur, ruido, SR)

SR = S.SR
ALT = '--alt' in sys.argv                      # variante con 7895 0,00–2,30 en lugar de 4631 (644 cuadros)
DUR = (644 if ALT else 647) / FPS              # 21,4667 / 21,5667 s (= video)
A = T / ('audio_alt7895' if ALT else 'audio')
rng = np.random.default_rng(19)


def n(x):
    return x / (np.abs(x).max() + 1e-9)


# ------------------------------------------------------------------------------------------------ sintetizadores
def ping(f=1760.0, dec=0.55):
    L = int(1.6 * SR); t = np.arange(L) / SR
    mod = np.sin(2 * np.pi * f * 2.0 * t) * 1.4 * np.exp(-t / 0.15)
    s = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / dec) + 0.35 * np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-t / (dec * 0.6))
    return n(s * np.minimum(1, t / 0.002))


def tic(f=2600.0, dec=0.006, L=0.03):
    L = int(L * SR); t = np.arange(L) / SR
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / dec) + 0.3 * S.ruido(L) * np.exp(-t / 0.0015)
    return n(s)


def pique(tono=230.0):
    """pelota de tenis contra cancha dura: golpe sordo con «pok» afinado + chasquido."""
    L = int(0.25 * SR); t = np.arange(L) / SR
    f = tono * (1 + 0.6 * np.exp(-t / 0.004))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.035)
    s += 0.6 * S.filt(S.ruido(L), 'band', [1200, 5000]) * np.exp(-t / 0.004)
    s += 0.5 * np.sin(2 * np.pi * 85 * t) * np.exp(-t / 0.05)
    return n(S.satur(s, 1.5))


def faja():
    """pelota contra la faja de la red: chasquido seco + vibración de la cuerda (buzz 140 Hz que se apaga)."""
    L = int(0.9 * SR); t = np.arange(L) / SR
    chas = S.filt(S.ruido(L), 'band', [1500, 7000]) * np.exp(-t / 0.006)
    golpe = np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.03)
    vib = np.sign(np.sin(2 * np.pi * 140 * t + 0.3 * np.sin(2 * np.pi * 6 * t))) * np.exp(-t / 0.25) * 0.25
    vib = S.filt(vib, 'band', [120, 2400])
    return n(chas + 0.8 * golpe + vib)


def rodar(dur=1.2):
    """pelota que rueda en el pasto y se frena: ruido grave con modulación que se hace lenta."""
    L = int(dur * SR); t = np.arange(L) / SR; u = t / dur
    fmod = 18 * (1 - u) + 3
    am = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(fmod) / SR)
    s = S.filt(S.ruido(L), 'band', [180, 1400]) * am * (1 - u) ** 1.5 * np.minimum(1, t / 0.05)
    return n(s)


def tk():
    """la pelota toca el borde del hoyo: clic plástico corto."""
    L = int(0.12 * SR); t = np.arange(L) / SR
    s = np.sin(2 * np.pi * 1450 * t) * np.exp(-t / 0.012) + 0.6 * np.sin(2 * np.pi * 3100 * t) * np.exp(-t / 0.006)
    s += 0.4 * S.filt(S.ruido(L), 'high', 3000) * np.exp(-t / 0.002)
    return n(s)


def crujido(dur=1.0):
    """barra de dominadas: crujido metálico por fricción (micro-golpes con resonancia)."""
    L = int(dur * SR); s = np.zeros(L); t = np.arange(L) / SR
    k = 0.0
    while k < dur - 0.05:
        i = int(k * SR); m = min(L - i, int(0.04 * SR)); tt = np.arange(m) / SR
        s[i:i + m] += np.sin(2 * np.pi * rng.uniform(260, 420) * tt) * np.exp(-tt / 0.012) * rng.uniform(0.4, 1)
        k += rng.uniform(0.02, 0.07)
    s = S.filt(s, 'band', [180, 3000]) * (0.5 + 0.5 * np.sin(np.pi * t / dur))
    return n(s)


def golpe_sordo(f0=95, dec=0.18):
    L = int(0.5 * SR); t = np.arange(L) / SR
    f = 48 + (f0 - 48) * np.exp(-t / 0.03)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dec) + 0.35 * S.filt(S.ruido(L), 'low', 900) * np.exp(-t / 0.03)
    return n(S.satur(s, 1.4))


def golpe_tarjeta():
    """golpe grave de tarjeta: sub corto con armónicos (se oye en el parlante del teléfono) + aire."""
    L = int(0.9 * SR); t = np.arange(L) / SR
    f = 42 + 70 * np.exp(-t / 0.04)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.28)
    s += 0.25 * S.filt(S.ruido(L), 'band', [200, 2500]) * np.exp(-t / 0.05)
    return n(S.satur(1.3 * s, 1.8))


def motor(dur=1.85, frena=0.45):
    """auto que llega y frena: motor armónico con RPM que cae + chirrido de gomas desde `frena` s."""
    L = int(dur * SR); t = np.arange(L) / SR; u = t / dur
    rpm = 95 - 50 * np.clip((t - frena) / (dur - frena), 0, 1) ** 0.7
    ph = 2 * np.pi * np.cumsum(rpm) / SR
    s = sum(np.sin(k * ph) / k ** 0.8 for k in range(1, 12))
    s = S.filt(S.satur(0.6 * s, 2.0), 'low', 2200) * (0.4 + 0.6 * np.clip(t / 0.4, 0, 1)) * (1 - 0.6 * np.clip((t - frena) / (dur - frena), 0, 1))
    ch = S.filt(S.ruido(L), 'band', [2300, 3600]) * (0.7 + 0.3 * np.sin(2 * np.pi * 23 * t))
    env_ch = np.clip((t - frena) / 0.08, 0, 1) * np.clip((dur - 0.12 - t) / 0.25, 0, 1)
    return n(0.7 * n(s) + 0.45 * n(ch) * env_ch)


def toc():
    """el auto toca apenas la barrera: golpe sordo de plástico/hormigón."""
    L = int(0.4 * SR); t = np.arange(L) / SR
    s = np.sin(2 * np.pi * 170 * t) * np.exp(-t / 0.05) + 0.5 * np.sin(2 * np.pi * 420 * t) * np.exp(-t / 0.02)
    s += 0.5 * S.filt(S.ruido(L), 'band', [400, 3500]) * np.exp(-t / 0.01)
    return n(S.satur(s, 1.3))


def chirp_dig(f0, f1, dur=0.035):
    L = int(dur * SR); t = np.arange(L) / SR
    f = f0 + (f1 - f0) * t / dur
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / (dur * 0.5))
    return n(S.filt(s, 'band', [600, 7000]))


def clic_temp(acento):
    L = int(0.03 * SR); t = np.arange(L) / SR
    f = 2500 if acento else 1500
    return n(np.sin(2 * np.pi * f * t) * np.exp(-t / 0.005))


# ------------------------------------------------------------------------------------------------ línea de tiempo
def linea():
    """lista de (t, nombre, función que pone el sonido en la Mezcla, nota). Tiempos del guion con D = 16,00."""
    sys.path.insert(0, '/home/user/1/scripts/gta')
    from grafica import valor_contador, c as cuadro
    ev = []
    E = lambda t, nom, nota='': ev.append(dict(t=round(t, 3), cuadro=cuadro(t), efecto=nom, nota=nota))
    m = S.Mezcla(DUR)
    # H: tics de carga (siguen el anillo: 0,10 → 1,30, se aceleran) · ping 1,40 · barrido 1,45
    t = 0.10; k = 0
    while t < 1.32:
        m.put('fx', tic(1900 + 40 * k, 0.005), t, 0.10 + 0.012 * k); E(t, 'tic de carga'); t += max(0.07, 0.14 - 0.008 * k); k += 1
    m.put('fx', ping(), 1.40, 0.32); m.rev(ping() * 0.10, 1.40, seg=1.8); E(1.40, 'ping (anillo lleno)')
    m.barrido(1.45, dur=0.30, g=0.22); E(1.45, 'barrido hacia el corte 1,50')
    # G3: 2 piques (objetivo: G3 fuente ≈1,0 y ≈1,8 → máster 2,40 y 3,20, a medir) · swish en el corte 3,90
    for tt in (2.40, 3.20):
        m.put('fx', pique(), tt, 0.40); E(tt, 'pique (G3, a medir)')
    m.barrido(3.90, dur=0.22, g=0.20); E(3.90, 'swish en el corte G3→G2')
    # G2: faja 4,60 (+ vibración) · cae y pica 5,60 · golpe grave de tarjeta 5,70
    m.put('fx', faja(), 4.60, 0.45); E(4.60, 'tic de faja + vibración de red (a medir)')
    m.put('fx', pique(260), 5.60, 0.32); E(5.60, 'pique de la pelota del lado de Jason (a medir)')
    m.put('fx', golpe_tarjeta(), 5.70, 0.55); E(5.70, 'golpe grave de tarjeta «CASI.» te faltó 1 cm')
    # G4: rodar 6,30–7,50 · tk 7,50 · tarjeta 7,70
    m.put('fx', rodar(1.2), 6.30, 0.22); E(6.30, 'rodar en el pasto (a medir)')
    m.put('fx', tk(), 7.50, 0.30); E(7.50, '«tk» en el borde (a medir)')
    m.put('fx', golpe_tarjeta(), 7.70, 0.55); E(7.70, 'golpe grave de tarjeta «CASI.» te faltó 1 mm')
    # G6: crujido de barra 8,40–9,40 · tarjeta 9,40 · golpe al soltar 9,70
    m.put('fx', crujido(1.0), 8.40, 0.16); E(8.40, 'crujido de barra (a medir)')
    m.put('fx', golpe_tarjeta(), 9.40, 0.55); E(9.40, 'golpe grave de tarjeta «CASI.» te faltó una')
    m.put('fx', golpe_sordo(), 9.70, 0.30); E(9.70, 'golpe al soltar la barra (a medir)')
    # G5: motor y frenada 10,00–11,85 · tics del contador (cambios de número) · toc 11,85 · tarjeta 12,00
    m.put('fx', motor(1.85, 0.45), 10.00, 0.24); E(10.00, 'motor y frenada (a medir)')
    ult = -1.0; prev = None; nt = 0
    for f in range(cuadro(10.10), cuadro(11.70)):
        txt, cm = valor_contador(f)
        if txt != prev:
            tt = f / FPS
            final = cm == 1
            if final or tt - ult >= 0.06:
                prog = (tt - 10.10) / 1.35
                m.put('fx', tic(1100 if final else 2400, 0.008 if final else 0.005), tt, 0.30 if final else 0.07 + 0.12 * min(1, prog))
                ult = tt; nt += 1
            prev = txt
    E(10.10, f'tics del contador ({nt}, uno por cambio de número con separación ≥ 0,06 s; el de «0,01 m» más grave)')
    m.put('fx', toc(), 11.85, 0.50); E(11.85, '«toc» contra la barrera + sacudida 3 cuadros')
    m.put('fx', golpe_tarjeta(), 12.00, 0.55); E(12.00, 'golpe grave de tarjeta «CASI.» te faltó nada')
    # G7: descifrado ×8 (13,20–13,52) · 2 piques (objetivo 14,20 y 14,65, a medir) · subida hacia el cambio
    for k in range(8):
        tt = 13.20 + k * 0.045
        m.put('fx', chirp_dig(1800 + 260 * k, 2600 + 300 * k), tt, 0.13); E(tt, f'tic de descifrado {k + 1}/8')
    for tt in (14.20, 14.65):
        m.put('fx', pique(), tt, 0.36); E(tt, 'pique (G7, a medir)')
    m.subida(14.30, 15.00, g=0.16); E(14.30, 'subida hacia el cambio (termina 15,00)')
    # cambio de personaje: barridos 15,00 · 15,70 · 15,85 · golpe grave en D
    m.barrido(15.00, dur=0.32, g=0.24); E(15.00, 'barrido: el cuadro se achica en el mapa')
    m.barrido(15.70, dur=0.20, g=0.24); E(15.70, 'barrido: picada 1')
    m.barrido(15.85, dur=0.16, g=0.26); E(15.85, 'barrido: picada 2')
    m.impacto(D, g=0.75); E(D, 'golpe grave en D (drop)')
    return m, ev


def ambiente():
    """ambiente real después de D (planos 8–10), sin efectos. La ráfaga de viento de 7887 (fuente 2,88–3,05, medida en
    FMT-02) se reemplaza por audio limpio de la misma toma (2,55–2,72), como en FMT-02."""
    m = S.Mezcla(DUR)
    m.ambiente('IMG_7887', 1.90, 16.00, 16.98, ini_fade=0.02, fin_fade=0.02)
    m.ambiente('IMG_7887', 2.55, 16.98, 17.15, fade=0.02)
    m.ambiente('IMG_7887', 3.05, 17.15, 17.77, ini_fade=0.02, fin_fade=0.01)
    m.ambiente('IMG_7884', 3.10, 17.77, 19.17, ini_fade=0.01, fin_fade=0.01)
    ult, t_ult = ('IMG_7895', 0.00) if ALT else ('IMG_4631', 2.50)
    m.ambiente(ult, t_ult, 19.17, DUR, ini_fade=0.01, fin_fade=0.30)              # fundido final 0,30 s
    return m


def clic():
    m = S.Mezcla(DUR); ev = []
    b = 60 / 100
    k0 = -int(D // b)
    for k in range(k0, int((DUR - D) // b) + 1):
        t = D + k * b
        if 0 <= t < DUR - 0.05:
            ac = (k % 4 == 0)
            m.put('mus', clic_temp(ac), t, 0.16 if ac else 0.09); ev.append(round(t, 3))
    return m, ev


def lufs(path, t0=None, t1=None):
    cmd = ['ffmpeg', '-nostats']
    if t0 is not None:
        cmd += ['-ss', str(t0), '-t', str(t1 - t0)]
    cmd += ['-i', str(path), '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-']
    r = subprocess.run(cmd, capture_output=True, text=True).stderr
    I = float([l for l in r.splitlines() if l.strip().startswith('I:')][-1].split()[1])
    P = float([l for l in r.splitlines() if l.strip().startswith('Peak:')][-1].split()[1])
    return I, P


def escribir(path, x):
    import soundfile as sf
    sf.write(str(path), x.astype(np.float32), SR, subtype='FLOAT')


def etapa():
    A.mkdir(parents=True, exist_ok=True)
    m, ev = linea()
    fx = m.pistas['fx']
    am = ambiente().pistas['amb']
    mc, beats = clic(); ck = mc.pistas['mus']
    for nom, x in (('fx_crudo', fx), ('amb_crudo', am), ('clic_TEMP_crudo', ck)):
        escribir(A / f'{nom}.wav', x)
    # 1) fx + clic a −14 LUFS integrados (lo que suena antes de D define la sonoridad)
    I0, _ = lufs(A / 'fx_crudo.wav')
    g_fx = 10 ** ((-14.0 - I0) / 20)
    # 2) ambiente: −26 LUFS integrados medidos sobre 16,00–21,57 (12 LU debajo del objetivo, donde va Legacy)
    Ia, _ = lufs(A / 'amb_crudo.wav', D, DUR)
    g_am = 10 ** ((-26.0 - Ia) / 20)
    # 3) clic TEMP: 6 dB debajo de los efectos en su pico
    fxn = fx * g_fx; amn = am * g_am
    ckn = ck * (np.abs(fxn).max() * 10 ** (-12 / 20) / (np.abs(ck).max() + 1e-9))
    for nom, x in (('fx', fxn), ('amb', amn), ('clic_TEMP', ckn)):
        escribir(A / f'{nom}.wav', x)
    pre = fxn + amn + ckn
    escribir(A / 'mezcla_pre.wav', pre)
    # limitador sin autonivelado (CLAUDE.md: alimiter level=false) y ajuste fino a −14 LUFS / pico ≤ −1 dBTP
    gan = 0.0
    for _ in range(4):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(A / 'mezcla_pre.wav'), '-af',
                        f'volume={gan:.2f}dB,alimiter=limit=0.83:level=false:attack=3:release=60:latency=1',
                        '-c:a', 'pcm_f32le', str(A / 'mezcla_animatica.wav')], check=True)
        I, P = lufs(A / 'mezcla_animatica.wav')
        if abs(I + 14) < 0.4 and P <= -1.0:
            break
        gan += (-14 - I)
    niveles = dict(mezcla=dict(lufs=I, pico_dbtp=P, ganancia_db=round(gan, 2)),
                   fx_lufs=lufs(A / 'fx.wav')[0], amb_lufs_tramo_D=lufs(A / 'amb.wav', D, DUR)[0],
                   clic_lufs=lufs(A / 'clic_TEMP.wav')[0],
                   tramos={nom: lufs(A / 'mezcla_animatica.wav', a, b)[0] for nom, a, b in
                           (('H 0–1,5', 0, 1.5), ('G3 1,5–3,9', 1.5, 3.9), ('G2 3,9–6,3', 3.9, 6.3), ('G4 6,3–8,3', 6.3, 8.3),
                            ('G6 8,3–10', 8.3, 10.0), ('G5 10–12,6', 10.0, 12.6), ('G7 12,6–15', 12.6, 15.0),
                            ('mapa 15–16', 15.0, 16.0), (f'real 16–{DUR:.2f}'.replace('.', ','), 16.0, DUR))})
    guardar_json(dict(eventos=ev, clic_TEMP_100BPM=beats, niveles=niveles,
                      nota='clic TEMP: grilla de 100 BPM anclada a D (tiempo fuerte en 1,60, 4,00 … 16,00 …); no es Legacy.'),
                 A / 'eventos.json')
    print(json.dumps(niveles, ensure_ascii=False))


if __name__ == '__main__':
    etapa()
