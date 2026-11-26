# Utilidades comunes de la tanda FOMO de la placa (26/11/2026).
# Lectura de clips cuadro a cuadro por tubería de FFmpeg, grado B/N, textos con Pillow,
# sonido sintetizado (golpes, tics, barridos, colchones), mezcla con la voz y codificación final.
import os, subprocess, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, SR = 1080, 1920, 30, 48000
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FUENTES = dict(
    disp_b="/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
    disp_xb="/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf",
    disp_m="/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf",
    inter_b="/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    inter_sb="/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
    inter_m="/usr/share/fonts/opentype/inter/Inter-Medium.otf",
    serif=os.path.join(RAIZ, "scripts/fuentes/InstrumentSerif-Regular.ttf"),
    serif_i=os.path.join(RAIZ, "scripts/fuentes/InstrumentSerif-Italic.ttf"),
)
CELESTE = (170, 208, 240)
_fcache = {}


def fuente(k, s):
    if (k, s) not in _fcache:
        _fcache[(k, s)] = ImageFont.truetype(FUENTES[k], s)
    return _fcache[(k, s)]


class Lector:
    """Lee cuadros de un video en orden. uno_a_uno=True: cada cuadro de la fuente es un cuadro a 30 fps."""

    def __init__(self, src, t0, w, h, crop=None, uno_a_uno=True, vf_pre="", vf_post=""):
        vf = []
        if vf_pre:
            vf.append(vf_pre)
        if uno_a_uno:
            vf.append("setpts=N/(30*TB)")
        vf.append("fps=30")
        if crop:
            vf.append(f"crop={crop}")
        vf.append(f"scale={w}:{h}:flags=lanczos")
        if vf_post:
            vf.append(vf_post)
        self.w, self.h = w, h
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-i", src, "-vf", ",".join(vf),
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stdin=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
        self.ult = None

    def cuadro(self):
        n = self.w * self.h * 3
        b = self.p.stdout.read(n)
        if len(b) == n:
            self.ult = np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3)
        return self.ult  # si se terminó, repite el último (se registra en el control)

    def cerrar(self):
        self.p.stdout.close(); self.p.kill()


def bn(a, contraste=1.18, gamma=1.0, ganancia=1.0):
    """B/N: luma BT.709 en lineal aproximado, ganancia, curva S suave."""
    x = a.astype(np.float32) / 255.0
    y = 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]
    y = np.clip(y * ganancia, 0, 1) ** gamma
    y = 0.5 + (y - 0.5) * contraste
    y = np.clip(y, 0, 1)
    y = y * y * (3 - 2 * y) * 0.35 + y * 0.65
    return np.repeat((y[..., None] * 255).astype(np.uint8), 3, axis=2)


_rng = np.random.default_rng(7)
_grano = [(_rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)) for _ in range(6)]


def grano(a, fuerza=5.0, i=0):
    g = _grano[i % len(_grano)]
    g = np.kron(g, np.ones((2, 2), np.float32))[: a.shape[0], : a.shape[1]]
    return np.clip(a.astype(np.float32) + g[..., None] * fuerza, 0, 255).astype(np.uint8)


def capa_texto(lineas, fk, size, color=(255, 255, 255), ancho=W, interlinea=1.08, alinear="c", sombra=0.55,
               radio_sombra=10, track=0, tachar=None):
    """Devuelve un RGBA del ancho dado con las líneas centradas (o a la izquierda) y sombra suave."""
    f = fuente(fk, size)
    asc, desc = f.getmetrics()
    lh = int(size * interlinea)
    alto = lh * len(lineas) + desc + 2 * radio_sombra + 10
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pos = []
    for k, ln in enumerate(lineas):
        if track:
            wln = sum(f.getlength(ch) for ch in ln) + track * (len(ln) - 1)
        else:
            wln = f.getlength(ln)
        x = (ancho - wln) / 2 if alinear == "c" else radio_sombra
        y = radio_sombra + k * lh
        pos.append((x, y, ln, wln))
    if sombra:
        sm = Image.new("L", img.size, 0)
        ds = ImageDraw.Draw(sm)
        for x, y, ln, wln in pos:
            _dibujar(ds, x, y + 3, ln, f, 255, track)
        sm = sm.filter(ImageFilter.GaussianBlur(radio_sombra))
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.putalpha(sm.point(lambda v: int(v * sombra)))
        img = Image.alpha_composite(img, sh)
        d = ImageDraw.Draw(img)
    for k, (x, y, ln, wln) in enumerate(pos):
        _dibujar(d, x, y, ln, f, color + (255,), track)
        if tachar is not None and k in tachar:
            yy = y + asc * 0.62
            d.line([(x - 4, yy), (x + wln + 4, yy)], fill=color + (255,), width=max(3, size // 14))
    return img


def _dibujar(d, x, y, ln, f, fill, track):
    if not track:
        d.text((x, y), ln, font=f, fill=fill)
        return
    for ch in ln:
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + track


def pegar(base, rgba, x, y, alfa=1.0):
    """Compone un RGBA de Pillow (o arreglo) sobre un arreglo RGB uint8, con opacidad global."""
    if alfa <= 0:
        return base
    a = np.asarray(rgba).astype(np.float32)
    h, w = a.shape[:2]
    x0, y0 = int(round(x)), int(round(y))
    xa, ya = max(0, x0), max(0, y0)
    xb, yb = min(base.shape[1], x0 + w), min(base.shape[0], y0 + h)
    if xb <= xa or yb <= ya:
        return base
    sub = a[ya - y0: yb - y0, xa - x0: xb - x0]
    m = sub[..., 3:4] / 255.0 * alfa
    r = base[ya:yb, xa:xb].astype(np.float32)
    base[ya:yb, xa:xb] = (r * (1 - m) + sub[..., :3] * m).astype(np.uint8)
    return base


def suave(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def fill_cover(img, w, h, cx=0.5, cy=0.5, zoom=1.0):
    """Recorta una imagen PIL para cubrir w×h con zoom y centro relativos."""
    iw, ih = img.size
    s = max(w / iw, h / ih) * zoom
    cw, ch = min(w / s, iw), min(h / s, ih)
    x0 = max(0.0, min(max(cx * iw - cw / 2, 0), iw - cw))
    y0 = max(0.0, min(max(cy * ih - ch / 2, 0), ih - ch))
    return img.resize((w, h), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))


# ---------------- sonido ----------------

def lienzo(dur):
    return np.zeros(int(dur * SR) + SR, np.float64)


def _env(n, ataque, caida):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(ataque, 1e-4)) * np.exp(-t / max(caida, 1e-4))
    return e


def golpe(x, t, g=1.0, f0=52, caida=0.45):
    n = int(1.2 * SR); i = int(t * SR); tt = np.arange(n) / SR
    f = f0 * (1 + 1.5 * np.exp(-tt / 0.03))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, caida)
    ruido = np.random.default_rng(int(t * 1000)).normal(0, 1, n) * _env(n, 0.001, 0.05)
    ruido = np.convolve(ruido, np.ones(12) / 12, "same")
    seg = (s * 0.9 + ruido * 0.35) * g
    x[i:i + n] += seg[: len(x) - i]


def tic(x, t, g=0.25, f=1900):
    n = int(0.05 * SR); i = int(t * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.008) * g
    x[i:i + n] += s[: len(x) - i]


def barrido(x, t, dur=0.35, g=0.3, f1=300, f2=4000):
    n = int(dur * SR); i = int(t * SR)
    r = np.random.default_rng(int(t * 997)).normal(0, 1, n)
    F = np.fft.rfft(r); fr = np.fft.rfftfreq(n, 1 / SR)
    fc = np.sqrt(f1 * f2)
    F *= np.exp(-0.5 * (np.log(np.maximum(fr, 1) / fc) / 0.9) ** 2)
    s = np.fft.irfft(F, n)
    s /= np.abs(s).max() + 1e-9
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    x[i:i + n] += (s * e * g)[: len(x) - i]


def brillo(x, t, g=0.18, dur=1.6):
    n = int(dur * SR); i = int(t * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * tt + k) * a for k, (f, a) in enumerate([(2093, 1), (3136, .7), (4186, .5), (5274, .3)]))
    s *= _env(n, 0.004, 0.45) * g
    x[i:i + n] += s[: len(x) - i]


def colchon(x, t0, t1, notas, g=0.06, ataque=0.6, suelta=0.8, brillo_=0.25):
    i0, i1 = int(t0 * SR), int(t1 * SR); n = i1 - i0; tt = np.arange(n) / SR
    s = np.zeros(n)
    for k, f in enumerate(notas):
        for h, a in ((1, 1), (2, brillo_), (3, brillo_ * 0.4)):
            s += a * np.sin(2 * np.pi * f * h * tt * (1 + 0.0015 * np.sin(2 * np.pi * 0.2 * tt + k)))
    e = np.minimum(1, tt / ataque) * np.minimum(1, (tt[-1] - tt) / suelta)
    s = s / max(1, len(notas)) * e * g
    x[i0:i1] += s[: len(x) - i0]


def dron(x, t0, t1, f=55, g=0.08):
    i0, i1 = int(t0 * SR), int(t1 * SR); n = i1 - i0; tt = np.arange(n) / SR
    s = np.zeros(n)
    for d in (-0.6, 0, 0.7):
        ph = 2 * np.pi * (f + d) * tt
        s += sum(np.sin(ph * h) / h for h in range(1, 8))
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.35 * tt)
    e = np.minimum(1, tt / 0.15) * np.minimum(1, (tt[-1] - tt) / 0.05)
    s = np.convolve(s, np.ones(24) / 24, "same") * lfo * e * g / 3
    x[i0:i1] += s[: len(x) - i0]


def leer_wav(p):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f64le", "-"],
                                  stdin=subprocess.DEVNULL)
    return np.frombuffer(raw, np.float64).copy()


def mezclar(fondo, voces, dur, salida, lufs=-14.0, duck_db=12.0, gan_voz=1.0):
    """fondo: arreglo mono; voces: lista (t, arreglo). Baja el fondo con la voz y nivela a −14 LUFS, pico < −1 dBTP."""
    n = int(dur * SR)
    fondo = fondo[:n].copy()
    v = np.zeros(n)
    for t, a in voces:
        i = int(t * SR); m = min(len(a), n - i)
        v[i:i + m] += a[:m] * gan_voz
    env = np.abs(v)
    w = int(0.02 * SR)
    env = np.convolve(env, np.ones(w) / w, "same")
    act = (env > 0.01).astype(np.float64)
    # ataque 15 ms, suelta 250 ms
    g = np.zeros(n); a_, r_ = np.exp(-1 / (0.015 * SR)), np.exp(-1 / (0.25 * SR)); s = 0.0
    for k in range(0, n, 48):
        tgt = act[k]
        s = tgt + (s - tgt) * (a_ ** 48 if tgt > s else r_ ** 48)
        g[k:k + 48] = s
    fondo *= 10 ** (-duck_db * g / 20)
    mix = fondo + v
    est = np.stack([mix, mix], 1).astype(np.float32)
    tmp = salida + ".pre.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", tmp],
                   input=est.tobytes(), check=True)
    m = medir(tmp)
    gan = lufs - m["I"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                    f"volume={gan:.2f}dB,alimiter=limit=0.84:level=false:attack=1:release=60", "-ar", str(SR),
                    "-c:a", "pcm_s24le", salida], check=True)
    os.remove(tmp)
    return medir(salida), (v, fondo)


def medir(p):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    blk = r[r.rfind("Summary:"):]
    I = float(blk.split("I:")[1].split("LUFS")[0])
    pk = float(blk.split("Peak:")[1].split("dBFS")[0])
    return dict(I=I, TP=pk)


class Codificador:
    def __init__(self, salida, w=W, h=H, crf=17):
        self.salida = salida
        self.tmp = salida + ".video.mp4"
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                                   "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.0",
                                   "-maxrate", "20M", "-bufsize", "25M", "-crf", str(crf), "-preset", "slow",
                                   "-pix_fmt", "yuv420p", "-vf", "scale=out_color_matrix=bt709:out_range=tv",
                                   "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                                   "-color_range", "tv", self.tmp], stdin=subprocess.PIPE)
        self.n = 0

    def poner(self, a):
        self.p.stdin.write(np.ascontiguousarray(a, np.uint8).tobytes()); self.n += 1

    def cerrar(self, audio=None):
        self.p.stdin.close(); self.p.wait()
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", self.tmp]
        if audio:
            cmd += ["-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2",
                    "-shortest"]
        cmd += ["-c:v", "copy", "-movflags", "+faststart", "-map_metadata", "-1", self.salida]
        subprocess.run(cmd, check=True)
        os.remove(self.tmp)
