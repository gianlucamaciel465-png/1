#!/usr/bin/env python3
"""Tanda FMT (17/11/2026) · sonido común: ambiente real de las tomas, foley y música propia sintetizada.

Sin material de terceros. La música es una guía propia (TEMP para el destino: en Instagram se puede reemplazar por un
audio de la biblioteca al subir). Instrumentos pensados para que se oigan en el parlante de un teléfono: el bajo y el
bombo llevan armónicos (saturación suave) además de la fundamental.

Uso típico:
    from sonido import Mezcla
    m = Mezcla(dur=12.0)
    m.ambiente('IMG_7884', src0=3.5, t0=2.0, t1=4.0, db=-6)
    m.bombo(1.0); m.palma(1.5) ...
    m.exportar('mezcla.wav', lufs=-14)
"""
import json, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
O = '/home/user/1/ORIGINALES'
rng = np.random.default_rng(11)


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


NOTA = {k: v for v, k in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}


def midi(s):
    """'A2' -> 45 ; 'F#3' -> 54"""
    n, o = (s[:-1], int(s[-1]))
    return 12 * (o + 1) + NOTA[n]


def db(x):
    return 10 ** (x / 20)


def filt(x, tipo, f, orden=2):
    return sosfilt(butter(orden, f, btype=tipo, fs=SR, output='sos'), x, axis=0)


def env(L, a=0.002, d=0.2, s=0.0, r=0.05, hold=None):
    """ADSR simple de L muestras; hold = segundos hasta empezar el release (por defecto, todo)."""
    t = np.arange(L) / SR
    e = np.where(t < a, t / max(a, 1e-5), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-5)))
    if hold is not None:
        k = int(hold * SR)
        if k < L:
            e[k:] *= np.exp(-(t[k:] - t[k]) / max(r, 1e-4))
    return e


def satur(x, k=2.0):
    return np.tanh(k * x) / np.tanh(k)


def ruido(L):
    return rng.standard_normal(L)


def reverb_ir(seg=1.6, pre=0.012, brillo=6000):
    L = int(seg * SR); t = np.arange(L) / SR
    ir = np.zeros((L, 2))
    for c in range(2):
        n = filt(ruido(L), 'low', brillo) * np.exp(-t / (seg / 6.9))
        ir[:, c] = n
    ir[:int(pre * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum(0, keepdims=True))
    return ir


class Mezcla:
    def __init__(self, dur):
        self.dur = dur; self.N = int(round(dur * SR))
        self.pistas = {k: np.zeros((self.N, 2)) for k in ('amb', 'fx', 'mus', 'bombo', 'voz')}
        self.ev = []
        self._ir = {}

    # ---------- utilidades ----------
    def put(self, pista, sig, t0, g=1.0, pan=0.0):
        if sig.ndim == 1:
            sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1)
        i = int(round(t0 * SR)); j = min(self.N, i + len(sig))
        if j > max(i, 0):
            self.pistas[pista][max(i, 0):j] += g * sig[max(0, -i):j - i]

    def log(self, t, que):
        self.ev.append({'t': round(t, 3), 'cuadro': round(t * 30), 'evento': que})

    # ---------- ambiente real ----------
    def leer(self, toma):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{O}/{toma}.mov', '-vn', '-map', '0:a:0', '-f', 'f32le',
                              '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.float32).astype(np.float64)

    def ambiente(self, toma, src0, t0, t1, g_db=0.0, hp=None, lp=None, fade=0.008, fin_fade=None, ini_fade=None):
        """audio real de la toma desde src0 (s de la fuente), colocado en [t0, t1) del máster, mono al centro."""
        a = self.leer(toma)
        n = int(round((t1 - t0) * SR)); s0 = int(round(src0 * SR))
        seg = a[s0:s0 + n].copy()
        if len(seg) < n:
            seg = np.concatenate([seg, np.zeros(n - len(seg))])
        if hp: seg = filt(seg, 'high', hp)
        if lp: seg = filt(seg, 'low', lp)
        r = np.ones(n)
        k1 = int((ini_fade or fade) * SR); k2 = int((fin_fade or fade) * SR)
        if k1: r[:k1] = np.linspace(0, 1, k1)
        if k2: r[-k2:] = np.minimum(r[-k2:], np.linspace(1, 0, k2))
        self.put('amb', seg * r * db(g_db), t0)
        self.log(t0, f'ambiente {toma} fuente {src0:.3f}–{src0 + (t1 - t0):.3f} s, {g_db:+.1f} dB')

    # ---------- batería ----------
    def bombo(self, t, g=0.9, f0=120, f1=46, dec=0.42, pista='bombo'):
        L = int(0.6 * SR); tt = np.arange(L) / SR
        f = f1 + (f0 - f1) * np.exp(-tt / 0.035)
        ph = 2 * np.pi * np.cumsum(f) / SR
        s = np.sin(ph) * np.exp(-tt / dec)
        s += 0.35 * filt(ruido(L), 'band', [1500, 6000]) * np.exp(-tt / 0.004)   # clic de ataque
        s = satur(s, 1.8)
        self.put(pista, s, t, g)

    def ocho08(self, t, nota, dur=0.8, g=0.55, glide_desde=None):
        L = int((dur + 0.1) * SR); tt = np.arange(L) / SR
        f = np.full(L, hz(nota))
        if glide_desde is not None:
            f = hz(nota) + (hz(glide_desde) - hz(nota)) * np.exp(-tt / 0.06)
        ph = 2 * np.pi * np.cumsum(f) / SR
        s = np.sin(ph) * env(L, 0.003, dur * 0.9, 0.0, 0.05, hold=dur)
        s = satur(1.4 * s, 2.5) * 0.8                                           # armónicos para el parlante del teléfono
        self.put('mus', s, t, g)

    def palma(self, t, g=0.32, pan=0.0):
        L = int(0.35 * SR); tt = np.arange(L) / SR
        s = np.zeros(L)
        for k, dt in enumerate((0.0, 0.009, 0.019)):
            i = int(dt * SR); n = L - i
            s[i:] += filt(ruido(n), 'band', [900, 3200]) * np.exp(-np.arange(n) / SR / (0.006 if k < 2 else 0.08))
        s += 0.4 * np.sin(2 * np.pi * 210 * tt) * np.exp(-tt / 0.03)
        self.put('mus', s / np.abs(s).max(), t, g, pan)
        self.rev(s / np.abs(s).max() * g * 0.35, t, seg=1.1)

    def charles(self, t, g=0.10, abierto=False, pan=0.25):
        L = int((0.25 if abierto else 0.06) * SR); tt = np.arange(L) / SR
        s = filt(ruido(L), 'high', 7000, 4) * np.exp(-tt / (0.09 if abierto else 0.012))
        self.put('mus', s / (np.abs(s).max() + 1e-9), t, g, pan)

    def redoble(self, t0, t1, g=0.12):
        """subida de charles/palmas acelerando hasta t1"""
        t = t0; paso = 0.12
        while t < t1 - 0.01:
            self.charles(t, g * (0.5 + 0.5 * (t - t0) / (t1 - t0)), pan=0.0)
            t += paso; paso = max(0.03, paso * 0.86)

    # ---------- armonía ----------
    def pad(self, t, notas, dur, g=0.06, corte=1400, a=0.25, r=0.6):
        L = int((dur + r) * SR); tt = np.arange(L) / SR
        s = np.zeros((L, 2))
        for n in notas:
            for c, det in enumerate((-0.07, 0.07)):
                f = hz(n) * (1 + det / 12)
                y = np.zeros(L)
                for k in range(1, int(min(30, 8000 / f))):                     # sierra limitada en banda
                    y += np.sin(2 * np.pi * f * k * tt + rng.uniform(0, 6.28)) / k
                s[:, c] += y
        s = filt(s, 'low', corte)
        e = env(L, a, 10, 1.0, r, hold=dur)
        s *= e[:, None]
        s /= np.abs(s).max() + 1e-9
        self.put('mus', s, t, g)
        self.rev(s * g * 0.5, t, seg=2.2)

    def campana(self, t, nota, g=0.07, dec=0.9, pan=0.0):
        L = int((dec * 3) * SR); tt = np.arange(L) / SR
        f = hz(nota)
        mod = np.sin(2 * np.pi * f * 3.5 * tt) * 2.2 * np.exp(-tt / 0.25)
        s = np.sin(2 * np.pi * f * tt + mod) * np.exp(-tt / dec)
        self.put('mus', s, t, g, pan)
        self.rev(s * g * 0.6, t, seg=2.0)

    # ---------- efectos ----------
    def rev(self, sig, t, seg=1.6):
        key = round(seg, 2)
        if key not in self._ir:
            self._ir[key] = reverb_ir(seg)
        ir = self._ir[key]
        if sig.ndim == 1:
            sig = np.stack([sig, sig], 1)
        w = np.stack([fftconvolve(sig[:, c], ir[:, c]) for c in range(2)], 1)
        self.put('fx', w, t)

    def subida(self, t0, t1, g=0.25):
        """ruido que se abre + tono que sube, termina en t1"""
        L = int((t1 - t0) * SR); tt = np.arange(L) / SR; u = tt / tt[-1]
        n = ruido(L)
        out = np.zeros(L)
        bloques = 24
        for b in range(bloques):
            i0, i1 = b * L // bloques, (b + 1) * L // bloques
            fc = 400 * (12000 / 400) ** (b / bloques)
            out[i0:i1] = filt(n, 'band', [fc * 0.7, min(fc * 1.4, 20000)])[i0:i1]
        f = 180 * (4 ** u)
        out = out * u ** 2 + 0.25 * np.sin(2 * np.pi * np.cumsum(f) / SR) * u ** 2
        self.put('fx', out / (np.abs(out).max() + 1e-9), t0, g)
        self.log(t0, f'subida hasta {t1:.2f}')

    def barrido(self, t, dur=0.35, g=0.22, sube=True):
        L = int(dur * SR); tt = np.arange(L) / SR; u = tt / tt[-1]
        n = ruido(L); out = np.zeros(L); B = 16
        for b in range(B):
            i0, i1 = b * L // B, (b + 1) * L // B
            x = b / B if sube else 1 - b / B
            fc = 500 * (9000 / 500) ** x
            out[i0:i1] = filt(n, 'band', [fc * 0.6, min(fc * 1.6, 20000)])[i0:i1]
        out *= np.sin(np.pi * u) ** 1.5
        self.put('fx', out / (np.abs(out).max() + 1e-9), t - dur * 0.6, g)
        self.log(t, 'barrido')

    def impacto(self, t, g=0.7):
        L = int(1.4 * SR); tt = np.arange(L) / SR
        f = 38 + 70 * np.exp(-tt / 0.05)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.5)
        s += 0.5 * filt(ruido(L), 'low', 3000) * np.exp(-tt / 0.06)
        s = satur(s, 1.6)
        self.put('fx', s, t, g)
        self.rev(s * g * 0.3, t, seg=2.4)
        self.log(t, 'impacto')

    def obturador(self, t, g=0.45):
        L = int(0.12 * SR); s = np.zeros(L)
        for t0, dur, dec, amp, f in ((0.0, 0.012, 0.0025, 0.9, 140), (0.055, 0.016, 0.0035, 0.7, 110)):
            n = int(dur * SR); tt = np.arange(n) / SR; i = int(t0 * SR)
            b = np.convolve(ruido(n) * np.exp(-tt / dec), [1, -0.85], 'same')
            m = min(n, L - i)
            s[i:i + m] += amp * b[:m] + 0.5 * amp * np.sin(2 * np.pi * f * tt[:m]) * np.exp(-tt[:m] / (dur / 2))
        self.put('fx', s / np.abs(s).max(), t, g)
        self.log(t, 'obturador')

    def tela(self, t, dur=0.35, g=0.18):
        """roce de tela: ruido rosado filtrado con envolvente irregular"""
        L = int(dur * SR); tt = np.arange(L) / SR
        n = np.cumsum(ruido(L)); n -= np.convolve(n, np.ones(400) / 400, 'same')
        n = filt(n, 'band', [700, 6000])
        e = np.sin(np.pi * tt / tt[-1]) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 7 * tt + 1)))
        s = n * e
        self.put('fx', s / (np.abs(s).max() + 1e-9), t, g)
        self.log(t, 'tela')

    def toque(self, t, g=0.2, f=2400):
        L = int(0.05 * SR); tt = np.arange(L) / SR
        s = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.008) + 0.5 * filt(ruido(L), 'high', 3000) * np.exp(-tt / 0.003)
        self.put('fx', s, t, g)

    def silenciar(self, pista, t0, t1, rampa=0.03):
        i0, i1 = int(t0 * SR), int(t1 * SR); k = int(rampa * SR)
        g = np.ones(self.N)
        g[i0:i1] = 0
        if k:
            g[max(0, i0 - k):i0] = np.linspace(1, 0, min(k, i0))
            g[i1:i1 + k] = np.linspace(0, 1, len(g[i1:i1 + k]))
        self.pistas[pista] *= g[:, None]

    def fundido(self, pista, t0, t1):
        i0, i1 = int(t0 * SR), int(t1 * SR)
        g = np.ones(self.N); g[i0:i1] = np.linspace(1, 0, i1 - i0); g[i1:] = 0
        self.pistas[pista] *= g[:, None]

    # ---------- salida ----------
    def exportar(self, salida, lufs=-14.0, g_pistas=None, duck_db=6.0):
        gp = {'amb': 0, 'fx': 0, 'mus': 0, 'bombo': 0, 'voz': 0}; gp.update(g_pistas or {})
        P = {k: v * db(gp[k]) for k, v in self.pistas.items()}
        # bombeo: la música baja con el bombo (sidechain casero)
        bk = np.abs(P['bombo']).mean(1)
        envb = np.maximum.accumulate(np.zeros(1)) if False else None
        a = np.exp(-1 / (0.12 * SR))
        e = np.zeros(self.N); acc = 0.0
        # envolvente rápida (ataque instantáneo, liberación 120 ms) vectorizada por bloques
        pk = np.convolve(bk, np.ones(64) / 64, 'same')
        for i in range(0, self.N, 64):
            v = pk[i:i + 64].max() if i < self.N else 0
            acc = max(v, acc * a ** 64); e[i:i + 64] = acc
        e = e / (e.max() + 1e-9)
        duck = 1 - (1 - db(-duck_db)) * e
        mix = P['amb'] + P['fx'] + P['mus'] * duck[:, None] + P['bombo'] + P['voz']
        import soundfile as sf
        pre = salida.replace('.wav', '_pre.wav')
        sf.write(pre, mix.astype(np.float32), SR, subtype='FLOAT')
        for k, v in P.items():
            if np.abs(v).max() > 0:
                sf.write(salida.replace('.wav', f'_{k}.wav'), v.astype(np.float32), SR, subtype='FLOAT')
        # limitador sin autonivelado + ganancia a la sonoridad objetivo (2 pasadas)
        def medir(f):
            r = subprocess.run(['ffmpeg', '-nostats', '-i', f, '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-'],
                               capture_output=True, text=True).stderr
            I = float([l for l in r.splitlines() if l.strip().startswith('I:')][-1].split()[1])
            Pk = float([l for l in r.splitlines() if l.strip().startswith('Peak:')][-1].split()[1])
            return I, Pk
        I0, _ = medir(pre)
        gan = lufs - I0
        for _ in range(3):
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', pre, '-af',
                            f'volume={gan:.2f}dB,alimiter=limit=0.83:level=false:attack=3:release=60:latency=1',
                            '-c:a', 'pcm_f32le', salida], check=True)
            I, Pk = medir(salida)
            if abs(I - lufs) < 0.4 and Pk <= -1.0:
                break
            gan += (lufs - I)
        json.dump({'lufs': I, 'pico_dbtp': Pk, 'ganancia_db': round(gan, 2), 'eventos': self.ev},
                  open(salida.replace('.wav', '_eventos.json'), 'w'), ensure_ascii=False, indent=1)
        return I, Pk


def grilla(bpm, origen):
    b = 60 / bpm
    return lambda k: origen + k * b
