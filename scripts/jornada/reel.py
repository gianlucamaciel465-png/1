# Motor común de los reels de la jornada 27/11/2026 (Colapinto, Merentiel): segmentos de video real, tarjetas,
# textos en caja (tapan rótulos quemados en inglés de los clips oficiales), rótulo de fuente y mezcla con la voz dirigida.
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fomo"))
from comun import (W, H, FPS, SR, RAIZ, CELESTE, Lector, Codificador, fuente, capa_texto, pegar, suave, fill_cover, grano,
                   lienzo, golpe, tic, barrido, brillo, colchon, dron, leer_wav, mezclar)

NOCHE = (14, 24, 44)
CEL = (170, 208, 240)


def cs(s):
    return int(round(s * FPS))


# ---------- capas de texto ----------
def caja(lineas, size=74, chico=None, size_chico=40, color=(255, 255, 255), color_chico=CEL, alfa=0.9, rotulo=None,
         ancho_min=0, pad=34):
    """texto bold blanco dentro de una caja azul noche redondeada (estilo barra de plataforma), centrada en W."""
    f = fuente("disp_xb", size)
    fc = fuente("disp_b", size_chico)
    fr = fuente("inter_sb", 26)
    lh = int(size * 1.1)
    wmax = max([f.getlength(l) for l in lineas] + [fc.getlength(chico) if chico else 0] +
               [fr.getlength(rotulo) + 3 * len(rotulo) if rotulo else 0])
    bw = int(max(wmax + 2 * pad, ancho_min))
    bh = pad + (40 if rotulo else 0) + lh * len(lineas) + (int(size_chico * 1.35) if chico else 0) + pad - 8
    img = Image.new("RGBA", (W, bh + 40), (0, 0, 0, 0))
    x0 = (W - bw) // 2
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0, 14, x0 + bw, 14 + bh], radius=22, fill=(0, 0, 0, 110))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, 6, x0 + bw, 6 + bh], radius=22, fill=NOCHE + (int(255 * alfa),))
    y = 6 + pad - 6
    if rotulo:
        x = (W - (fr.getlength(rotulo) + 3 * (len(rotulo) - 1))) / 2
        for ch in rotulo:
            d.text((x, y), ch, font=fr, fill=CEL + (255,)); x += fr.getlength(ch) + 3
        y += 40
    for l in lineas:
        d.text(((W - f.getlength(l)) / 2, y), l, font=f, fill=color + (255,)); y += lh
    if chico:
        d.text(((W - fc.getlength(chico)) / 2, y + 4), chico, font=fc, fill=color_chico + (255,))
    return img


def tarjeta_fondo(k, semilla=0):
    """fondo de tarjeta: azul noche con viñeta y grano, leve respiración."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
    v = np.clip(1.15 - r * 1.1, 0.55, 1.15)[..., None]
    a = np.array(NOCHE, np.float32)[None, None] * v
    return grano(np.clip(a, 0, 255).astype(np.uint8), 4.0, k + semilla)


_TF = None


def fondo_tarjeta(k):
    global _TF
    if _TF is None:
        _TF = tarjeta_fondo(0)
    return grano(_TF.copy(), 3.0, k)


def rotulo_fuente(txt):
    return capa_texto([txt], "inter_sb", 28, color=(235, 235, 235), sombra=0.7, radio_sombra=6, alinear="l", ancho=600)


def pop(k, dur=4, desde=1.18):
    if k >= dur: return 1.0
    return desde + (1 - desde) * suave(max(k, 0) / dur)


def pegar_esc(img, capa, y, esc=1.0, alfa=1.0):
    if alfa <= 0: return
    if esc != 1.0:
        w, h = capa.size
        c2 = capa.resize((int(w * esc), int(h * esc)), Image.LANCZOS)
        pegar(img, c2, (W - c2.size[0]) / 2, y - (c2.size[1] - h) / 2, alfa)
    else:
        pegar(img, capa, 0, y, alfa)


def oscurecer(a, arriba=0, g_arr=0.0, abajo=H, g_ab=0.0):
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    m = np.ones((H, 1, 1), np.float32)
    if g_arr:
        m *= 1 - np.clip((arriba - yy) / max(1, arriba), 0, 1) * g_arr
    if g_ab:
        m *= 1 - np.clip((yy - abajo) / max(1, H - abajo), 0, 1) * g_ab
    return (a.astype(np.float32) * m).astype(np.uint8)


# ---------- lectores ----------
def lector_clip(src, t0, zoom=1.0, cx=0.5, cy=0.5):
    if zoom == 1.0:
        return Lector(src, t0, W, H)
    cw, ch = int(W / zoom) // 2 * 2, int(H / zoom) // 2 * 2
    x = int(max(0, min(W - cw, cx * W - cw / 2))); y = int(max(0, min(H - ch, cy * H - ch / 2)))
    return Lector(src, t0, W, H, crop=f"{cw}:{ch}:{x}:{y}")


class Ventana:
    """franja horizontal de un video (p. ej. la imagen de un reel con banda de título) en 9:16: fondo desenfocado de la
    misma toma + la franja ampliada al centro."""

    def __init__(self, src, t0, y0, alto, zoom=1.3, cy=0.5, cx=0.5):
        self.L = Lector(src, t0, W, alto, crop=f"{W}:{alto}:0:{y0}")
        self.alto, self.zoom, self.cy, self.cx = alto, zoom, cy, cx

    def cuadro(self):
        f = self.L.cuadro()
        im = Image.fromarray(f)
        fondo = fill_cover(im, W // 6, H // 6).filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
        a = (np.asarray(fondo).astype(np.float32) * 0.42).astype(np.uint8)
        fw, fh = int(W * self.zoom), int(self.alto * self.zoom)
        g = im.resize((fw, fh), Image.LANCZOS)
        xo = int((fw - W) * self.cx)
        g = np.asarray(g)[:, xo:xo + W]
        y = int(H * self.cy - fh / 2)
        a[y:y + fh] = g
        return a

    def cerrar(self):
        self.L.cerrar()


# ---------- render ----------
def render(salida, N, segmentos, textos, sonido, voces, techo=0.8, extra_audio=None):
    """segmentos: lista de dict(c0, c1, fuente=callable(c, k) -> RGB) ; textos: lista de dict(c0, c1, capa, y, pop, sale, rotulo)
    sonido: callable(x, dur) que agrega efectos; voces: lista (t, arreglo); extra_audio: lista (t, arreglo) sin ducking."""
    cod = Codificador(salida + ".tmp.mp4")
    seg_i = 0
    for c in range(N):
        while segmentos[seg_i]["c1"] <= c:
            if "cerrar" in segmentos[seg_i]: segmentos[seg_i]["cerrar"]()
            seg_i += 1
        s = segmentos[seg_i]
        img = np.ascontiguousarray(s["fuente"](c, c - s["c0"]), np.uint8).copy()
        for t in textos:
            if t["c0"] <= c < t["c1"]:
                k = c - t["c0"]
                al = suave(k / t.get("entra", 3)) if t.get("entra", 3) else 1.0
                if t.get("sale", True) and t["c1"] < N:
                    al *= 1 - suave((c - (t["c1"] - 3)) / 3)
                if t.get("x") is not None:
                    pegar(img, t["capa"], t["x"], t["y"], al)
                else:
                    pegar_esc(img, t["capa"], t["y"], pop(k, 4, t.get("pop", 1.12)) if t.get("pop", 1.12) != 1 else 1.0, al)
        cod.poner(grano(img, 2.0, c))
    if "cerrar" in segmentos[-1]: segmentos[-1]["cerrar"]()
    dur = N / FPS
    x = lienzo(dur)
    sonido(x, dur)
    if extra_audio:
        for t, a in extra_audio:
            i = int(t * SR); m = min(len(a), len(x) - i)
            x[i:i + m] += a[:m]
    wav = salida + ".wav"
    nivel, (vv, ff) = mezclar(x, voces, dur, wav, techo=techo)
    rel = []
    for tv, av in voces:
        i0, i1 = int(tv * SR), int(tv * SR) + len(av)
        rv = np.sqrt((vv[i0:i1] ** 2).mean()) + 1e-12; rf = np.sqrt((ff[i0:i1] ** 2).mean()) + 1e-12
        rel.append(round(20 * np.log10(rv / rf), 1))
    cod.cerrar(audio=wav)
    os.replace(salida + ".tmp.mp4", salida); os.remove(wav)
    ctrl = dict(cuadros=cod.n, duracion=round(dur, 3), sonoridad=nivel, voz_fondo_db=rel,
                fin_voz=round(max([t + len(a) / SR for t, a in voces] or [0.0]), 2))
    json.dump(ctrl, open(salida + ".control.json", "w"), indent=1)
    print(json.dumps(ctrl))
    return ctrl


def audio_clip(src, t0, dur, gan=1.0, fade=0.08):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0}", "-t", f"{dur}", "-i", src, "-f", "f32le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32).astype(np.float64) * gan
    n = int(fade * SR)
    if len(a) > 2 * n:
        a[:n] *= np.linspace(0, 1, n); a[-n:] *= np.linspace(1, 0, n)
    return a
