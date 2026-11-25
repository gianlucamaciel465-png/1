#!/usr/bin/env python3
"""MARCA · MC-03 «0-40» · receta del máster v01 (Pedro B, 25/11/2026).

Guion: piezas/MARCA_comunidad/04_fede_guiones_G1.md §0, §MC-03 y §8 (G1 v1) + 06_roma_aprobacion_G1.md (condiciones)
+ 05_especificacion_comun.md. Usa sin modificarlos scripts/fmt/video.py (color, plano, unir, ENC_INT, TOMAS),
scripts/fmt/fmt03.py (hoja_src, leer, plano_n, desde_cuadro, md5_stream, ebur, audio_np, niveles_tramos, cuadros_corte,
hoja_contacto), scripts/fmt/fmt04_util.py (_decode_yuv444, _encoder), scripts/fmt/sonido.py (Mezcla) y
scripts/marca/comun.py (caja, placa, burbuja, fuente, fuera_de_zona, CELESTE, TINTA).

Lo que no está en esos módulos vive acá y lo reutiliza mc04.py:
  · interfaz por cuadro: cada cuadro del máster recibe UNA capa RGBA armada con Pillow (textos de comun.py, marcador de
    transmisión, etiquetas, «pop» de 3 cuadros, titileo). Se mezcla en Python sobre el YUV de la base con la matriz
    BT.709 de rango limitado y se codifica con los mismos parámetros que video.master (H.264 High 4.0, crf 17, AAC-LC
    192k 48 kHz, faststart, sin metadatos). Motivo: con ~40 PNG en bucle el filtro overlay de FFmpeg decodifica cada PNG
    430 veces y convierte RGB→YUV con la matriz BT.601 por defecto; acá el estado de cada cuadro es exacto.
  · burbuja con emoji (Noto Color Emoji, tamaño 109 escalado) con la misma geometría que comun.burbuja;
  · cámara lenta ×0,5 de 3375 con mezcla de cuadros compensada por flujo óptico denso (Lucas–Kanade piramidal en
    numpy/scipy, sin OpenCV como pide la especificación 05): sin tartamudeo y sin doble contorno en «ROCCÉ / so f★cking
    close.» (condiciones 1 y 2 de Roma). La primera versión (una sola traslación por correlación de fase) dejaba 5–13 %
    de píxeles con doble contorno durante la revelación: med/fantasmas_3375.json;
  · cuadro congelado con acercamiento real por cuadro (recorte subpíxel Lanczos), balance de blancos por cuadro de 3375;
  · detección del estampado por cuadro para comprobar que ningún texto lo toca (condición 4 de Roma).

Etapas (python mc03.py <etapa>, con el python de TRABAJO/venv):
  hojas → planos → medir → ui → audio → master → control → entregar
Intermedios en TRABAJO/marca/MC-03/. Sin servicios externos ni créditos. Sin commit ni push (lo hace Roma).
"""
import json, math, subprocess, sys, shlex, hashlib, shutil, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/marca')
import video as V            # noqa: E402
import fmt03 as U            # noqa: E402
import fmt04_util as F4      # noqa: E402
import comun as C            # noqa: E402
from sonido import Mezcla, filt, ruido, satur, SR   # noqa: E402

R = Path('/home/user/1')
EXP = R / 'EXPORTACIONES'
W, H, FPS = 1080, 1920, 30
FONT_HOJA = U.FONT
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
NAVY = (15, 28, 46)            # #0F1C2E (guion: caja azul noche)
HILOS = '2'                    # máquina compartida con otros dos Pedros

# ffmpeg de video.py con nice y 2 hilos (video.py no se toca: se envuelve V.sh en este proceso)
_SH0 = V.sh


def _sh_hilos(cmd, **kw):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    cmd = list(cmd)
    if cmd and cmd[0] == 'ffmpeg':
        cmd = ['nice', '-n', '10', 'ffmpeg', '-threads', HILOS, '-filter_threads', HILOS] + cmd[1:-1] + ['-threads', HILOS, cmd[-1]]
    return _SH0(cmd, **kw)


V.sh = _sh_hilos


def jdump(obj, f):
    Path(f).parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(f, 'w'), ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))


# =====================================================================================================
# color: BT.709 rango limitado (igual que life_v2.yuv_rgb / rgb_yuv)
# =====================================================================================================
def yuv444_rgb(Y, Cb, Cr):
    y = (Y.astype(np.float32) - 16) / 219; u = (Cb.astype(np.float32) - 128) / 224; v = (Cr.astype(np.float32) - 128) / 224
    Rr = y + 1.5748 * v; Bb = y + 1.8556 * u; Gg = (y - 0.2126 * Rr - 0.0722 * Bb) / 0.7152
    return np.stack([Rr, Gg, Bb], -1) * 255.0


def rgb_yuv444(rgb):
    r, g, b = rgb[..., 0] / 255, rgb[..., 1] / 255, rgb[..., 2] / 255
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return 16 + 219 * y, 128 + 224 * (b - y) / 1.8556, 128 + 224 * (r - y) / 1.5748


def u8(x):
    return np.clip(np.round(x), 0, 255).astype(np.uint8)


# =====================================================================================================
# textos (comun.py) posicionados por el borde superior VISIBLE (guion: «y es el borde superior del texto»)
# =====================================================================================================
class El:
    """Elemento de interfaz: imagen RGBA + posición. caja = recuadro visible (glifos o tarjeta) para zona y choques."""
    def __init__(self, img, x, y, caja, nombre, texto=''):
        self.img, self.x, self.y, self.caja, self.nombre, self.texto = img, x, y, caja, nombre, texto

    def escalado(self, e):
        if e == 1.0:
            return self.img, self.x, self.y
        im = self.img.resize((max(1, round(self.img.width * e)), max(1, round(self.img.height * e))), Image.LANCZOS)
        cx = self.x + self.img.width / 2
        if getattr(self, 'ancla', 'centro') == 'abajo':    # el borde inferior no se mueve: el «pop» crece hacia arriba
            yb = self.y + self.img.height
            return im, round(cx - im.width / 2), round(yb - im.height)
        if getattr(self, 'ancla', 'centro') == 'arriba':   # el borde superior no se mueve: el «pop» crece hacia abajo
            return im, round(cx - im.width / 2), self.y
        cy = self.y + self.img.height / 2
        return im, round(cx - im.width / 2), round(cy - im.height / 2)


def _bbox_alpha(im, umbral):
    a = np.asarray(im)[..., 3]
    ys, xs = np.nonzero(a > umbral)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def placa(txt, size, y, cx=W // 2, peso='extrabold', halo=0.55, nombre='placa', sombra_px=None):
    """Placa con halo (comun.placa). y = borde superior de los glifos."""
    im = C.placa(txt, size, peso=peso, halo=halo, sombra_px=sombra_px)
    gx0, gy0, gx1, gy1 = _bbox_alpha(im, 200)            # glifos (el halo llega a 0,55 × 255 = 140)
    x = round(cx - im.width / 2); yy = y - gy0
    return El(im, x, yy, (x + gx0, y, x + gx1, yy + gy1), nombre, txt)


def dato(txt, size, y, cx=W // 2, nombre='dato', halo=0.6, sombra_px=None):
    return placa(txt, size, y, cx, peso='medium', halo=halo, nombre=nombre, sombra_px=sombra_px)


def caja(txt, size, y, cx=W // 2, tema='blanca', nombre='caja', interlineado=1.12, pad=(30, 18)):
    im = C.caja(txt, size, tema=tema, interlineado=interlineado, pad=pad)
    x0, y0, x1, y1 = _bbox_alpha(im, 10)
    x = round(cx - im.width / 2)
    return El(im, x, y - y0, (x + x0, y, x + x1, y - y0 + y1), nombre, txt)


def _emoji_img(ch, alto):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((round(im.width * alto / im.height), alto), Image.LANCZOS)


def burbuja_emoji(renglones, etiqueta='Comentario en TikTok', size=52, y=620, cx=W // 2, nombre='burbuja', pad=34,
                  interlineado=1.08):
    """Misma tarjeta que comun.burbuja (blanca, radio 28, sombra 12 px, etiqueta gris 0,62 × size, pad 34), con varios
    renglones y emoji en color (Noto Color Emoji, OFL). renglones: lista de listas de tramos ('t', texto) o ('e', emoji).
    y = borde superior de la tarjeta."""
    f1, f2 = C.fuente('semibold', size), C.fuente('medium', int(size * 0.62))
    a1, d1 = f1.getmetrics(); a2, d2 = f2.getmetrics()
    alto_e = round(size * 1.0)
    esp = round(size * 0.12)

    def ancho(r):
        w = 0
        for i, (k, s) in enumerate(r):
            w += f1.getlength(s) if k == 't' else len(s) * (alto_e + esp)
        return w
    inter = round((a1 + d1) * interlineado)
    w_txt = max(max(ancho(r) for r in renglones), f2.getlength(etiqueta))
    Wc = int(w_txt + 2 * pad); Hc = int(pad * 2 + (a2 + d2) + 10 + inter * len(renglones))
    im = Image.new('RGBA', (Wc + 24, Hc + 24), (0, 0, 0, 0))
    sh = Image.new('L', im.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle([12, 16, 12 + Wc, 16 + Hc], radius=28, fill=110)
    im.putalpha(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([12, 12, 12 + Wc, 12 + Hc], radius=28, fill=C.BLANCO + (255,))
    d.text((12 + pad, 12 + pad), etiqueta, font=f2, fill=(120, 120, 124, 255))
    y0 = 12 + pad + a2 + d2 + 10
    for i, r in enumerate(renglones):
        x = 12 + pad; yy = y0 + i * inter
        for k, s in r:
            if k == 't':
                d.text((x, yy), s, font=f1, fill=C.TINTA + (255,)); x += f1.getlength(s)
            else:
                for ch in s:
                    e = _emoji_img(ch, alto_e)
                    im.alpha_composite(e, (int(round(x + esp / 2)), int(round(yy + (a1 - size * 0.80)))))
                    x += alto_e + esp
    x = round(cx - im.width / 2)
    return El(im, x, y - 12, (x + 12, y, x + 12 + Wc, y + Hc), nombre,
              ' / '.join(''.join(s for _, s in r) for r in renglones) + ' + ' + etiqueta)


def pastilla(txt, size=40, fondo=NAVY + (235,), tinta=C.BLANCO, cx=780, y=270, nombre='etiqueta', pad=(22, 10), radio=14):
    f = C.fuente('extrabold', size)
    a, dsc = f.getmetrics()
    w = f.getlength(txt); x0, y0, x1, y1 = f.getbbox(txt)
    Wc = int(w + 2 * pad[0]); Hc = int((y1 - y0) + 2 * pad[1] + 8)
    im = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, Wc - 1, Hc - 1], radius=radio, fill=fondo)
    d.text((pad[0], (Hc - (y1 - y0)) / 2 - y0), txt, font=f, fill=tinta + (255,))
    x = round(cx - Wc / 2)
    return El(im, x, y, (x, y, x + Wc, y + Hc), nombre, txt)


# =====================================================================================================
# capa por cuadro y composición final (mismos parámetros de codificación que video.master)
# =====================================================================================================
def capa_rgba(items):
    """items: lista de (El, escala, alfa). Devuelve np.uint8 H×W×4 o None."""
    if not items:
        return None
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for el, e, alfa in items:
        im, x, y = el.escalado(e)
        if alfa < 1.0:
            im = im.copy(); a = np.asarray(im)[..., 3].astype(np.float32) * alfa
            im.putalpha(Image.fromarray(u8(a)))
        L.alpha_composite(im, (int(x), int(y)))
    return np.asarray(L)


def _ui_yuv(rgba):
    a = rgba[..., 3].astype(np.float32) / 255.0
    Y, Cb, Cr = rgb_yuv444(rgba[..., :3].astype(np.float32))
    a2 = a.reshape(H // 2, 2, W // 2, 2).mean((1, 3))
    pc = lambda P: (P * a).reshape(H // 2, 2, W // 2, 2).mean((1, 3)) / np.maximum(a2, 1e-6)
    return a, Y, a2, pc(Cb), pc(Cr)


ENC_MASTER = ['-c:v', 'libx264', '-profile:v', 'high', '-level:v', '4.0', '-preset', 'slow', '-crf', '17',
              '-maxrate', '20M', '-bufsize', '25M', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-g', '30',
              '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']
ENC_AUDIO = ['-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2']
META = ['-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
        '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler']


def componer(base, ui_fn, audio_wav, salida, nf, choque_fn=None, pre_fn=None):
    """base: mp4 yuv420p 1080×1920; ui_fn(k) -> (clave, items); audio_wav: mezcla final. Devuelve registro por cuadro.
    choque_fn(k, alfa) -> dict opcional (medición de choques texto/estampado sobre la capa de ese cuadro).
    pre_fn(k, Y, Cb, Cr) -> (Cb, Cr) opcional: corrección de croma de la base antes de la capa (MC-04 v02, Blanca
    neutra); sin pre_fn el resultado es idéntico al de antes."""
    dec = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', HILOS, '-i', str(base), '-f', 'rawvideo',
                            '-pix_fmt', 'yuv420p', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p',
                            '-s', f'{W}x{H}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-i', '-', '-i', str(audio_wav),
                            '-map', '0:v', '-map', '1:a', '-threads', HILOS, *ENC_MASTER, *ENC_AUDIO, *META,
                            '-shortest', '-movflags', '+faststart', str(salida)], stdin=subprocess.PIPE)
    fs = W * H * 3 // 2
    cache_k, cache_v = None, None
    reg = []
    for k in range(nf):
        b = dec.stdout.read(fs)
        if len(b) < fs:
            raise RuntimeError(f'componer: base corta en el cuadro {k}')
        Y = np.frombuffer(b, np.uint8, W * H).reshape(H, W)
        Cb = np.frombuffer(b, np.uint8, W * H // 4, W * H).reshape(H // 2, W // 2)
        Cr = np.frombuffer(b, np.uint8, W * H // 4, W * H * 5 // 4).reshape(H // 2, W // 2)
        if pre_fn is not None:
            Cb, Cr = pre_fn(k, Y, Cb, Cr)
            b = Y.tobytes() + Cb.tobytes() + Cr.tobytes()
        clave, items = ui_fn(k)
        if clave != cache_k:
            rgba = capa_rgba(items)
            cache_v = None if rgba is None else _ui_yuv(rgba)
            cache_k = clave
        if cache_v is None:
            out = b
            alfa = None
        else:
            a, Yu, a2, Cbu, Cru = cache_v
            Yo = u8(Y * (1 - a) + Yu * a); Cbo = u8(Cb * (1 - a2) + Cbu * a2); Cro = u8(Cr * (1 - a2) + Cru * a2)
            out = Yo.tobytes() + Cbo.tobytes() + Cro.tobytes()
            alfa = a
        enc.stdin.write(out)
        r = dict(cuadro=k, capa=str(clave)[:200])
        if choque_fn is not None:
            r.update(choque_fn(k, alfa))
        reg.append(r)
    dec.stdout.close(); dec.wait(); enc.stdin.close(); enc.wait()
    if enc.returncode:
        raise RuntimeError('componer: falló la codificación')
    return reg


def copiar_video(master, audio_wav, salida):
    """mismo flujo de video (copia sin recodificar) + otra mezcla (spec 05: _SINMUSICA)."""
    U.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', str(master), '-i', str(audio_wav), '-map', '0:v',
           '-map', '1:a', '-c:v', 'copy', *ENC_AUDIO, *META, '-shortest', '-movflags', '+faststart', str(salida)])


# =====================================================================================================
# planos especiales
# =====================================================================================================
def leer_fuente_yuv444(toma, n0, nf):
    nw, nh = V.TOMAS[toma]['nat']
    d = U.desde_cuadro(toma, n0)
    return [fr.copy() for fr in F4._decode_yuv444(V._src(toma), d, nf / FPS, V.color(toma) + f',fps={FPS}', nw, nh, nf)]


def recorte(fr, x, y, w, h):
    out = np.empty((3, H, W), np.uint8)
    for c in range(3):
        out[c] = np.asarray(Image.fromarray(fr[c]).resize((W, H), Image.LANCZOS, box=(x, y, x + w, y + h)))
    return out


def congelado_zoom(toma, n, salida, z0, z1, cx, cy, nf):
    """cuadro n de la toma congelado nf cuadros con acercamiento lineal real z0→z1 centrado en (cx, cy) (coordenadas
    naturales). video.foto solo admite z fijo; acá se recorta por cuadro con caja subpíxel (Lanczos) sobre Y, U, V."""
    nw, nh = V.TOMAS[toma]['nat']
    fr = leer_fuente_yuv444(toma, n, 1)[0]
    enc = F4._encoder(salida)
    vent = []
    for k in range(nf):
        Z = z0 + (z1 - z0) * k / max(nf - 1, 1); w, h = nw / Z, nh / Z
        x = min(max(cx - w / 2, 0), nw - w); y = min(max(cy - h / 2, 0), nh - h)
        vent.append([round(Z, 4), round(x, 1), round(y, 1), round(w, 1), round(h, 1)])
        enc.stdin.write(recorte(fr, x, y, w, h).tobytes())
    enc.stdin.close(); enc.wait()
    return dict(toma=toma, n_congelado=n, cuadros=nf, salida=str(salida), z0=z0, z1=z1, centro_nat=[cx, cy], ventanas=vent)


def blanco_medido(rgb_small):
    """media RGB de la tela blanca lisa (mayor componente con L > 170 y sat < 0,15) en un cuadro reducido."""
    from scipy import ndimage as nd
    f = rgb_small.astype(np.float32)
    L = f @ np.array([.2126, .7152, .0722], np.float32); sat = (f.max(-1) - f.min(-1)) / (f.max(-1) + 1)
    m = (L > 170) & (sat < 0.15)
    lab, n = nd.label(m)
    if n == 0:
        return None
    s = nd.sum(m, lab, range(1, n + 1)); big = lab == (1 + int(np.argmax(s)))
    return f[big].mean(0)


def fase(a, b):
    """desplazamiento d (dx, dy) con b(x) ≈ a(x − d), correlación de fase con ventana de Hann y ajuste parabólico."""
    a = a - a.mean(); b = b - b.mean()
    w = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1])).astype(np.float32)
    Fa = np.fft.fft2(a * w); Fb = np.fft.fft2(b * w)
    Rr = Fb * np.conj(Fa); Rr /= np.abs(Rr) + 1e-9
    r = np.real(np.fft.ifft2(Rr))
    iy, ix = np.unravel_index(np.argmax(r), r.shape)

    def sub(v, i, n):
        vm, v0, vp = v[(i - 1) % n], v[i], v[(i + 1) % n]
        den = vm - 2 * v0 + vp
        return i + (0.5 * (vm - vp) / den if abs(den) > 1e-9 else 0.0)
    sy = sub(r[:, ix], iy, r.shape[0]); sx = sub(r[iy, :], ix, r.shape[1])
    if sy > r.shape[0] / 2: sy -= r.shape[0]
    if sx > r.shape[1] / 2: sx -= r.shape[1]
    return float(sx), float(sy), float(r.max())


def estampado_blanca_frente(Y, caja=None):
    """máscara de letras oscuras sobre tela clara (frente de la Blanca) en luma de rango limitado (1080×1920)."""
    from scipy import ndimage as nd
    L = (Y.astype(np.float32) - 16) * 255 / 219
    s = L[::2, ::2]
    bg = nd.grey_closing(s, size=(21, 21))
    m = (s < bg - 60) & (bg > 165)
    m = nd.binary_opening(m, iterations=1)
    lab, n = nd.label(nd.binary_dilation(m, iterations=6))
    if n == 0:
        return np.zeros(Y.shape, bool)
    sz = nd.sum(m, lab, range(1, n + 1)); i = int(np.argmax(sz))
    m &= np.isin(lab, [j + 1 for j in range(n) if sz[j] > 0.15 * sz[i]])
    full = np.repeat(np.repeat(m, 2, 0), 2, 1)
    if caja is not None:
        x0, y0, x1, y1 = caja; lim = np.zeros_like(full); lim[y0:y1, x0:x1] = True; full &= lim
    return full


_MALLAS = {}


def _malla(h, w):
    if (h, w) not in _MALLAS:
        _MALLAS[(h, w)] = np.mgrid[0:h, 0:w].astype(np.float32)
    return _MALLAS[(h, w)]


def deformar1(img, F, order=1):
    """img(x + F(x)) para una imagen 2D float32 (F: h×w×2, dx y dy en píxeles)."""
    from scipy import ndimage as nd
    gy, gx = _malla(*img.shape)
    return nd.map_coordinates(img, [gy + F[..., 1], gx + F[..., 0]], order=order, mode='nearest')


def flujo_lk(A, B, d0=(0.0, 0.0), niveles=5, iters=3, sigma=6.0):
    """flujo óptico denso A→B (B(x + F(x)) ≈ A(x)) por Lucas–Kanade piramidal con numpy/scipy (la especificación 05
    excluye OpenCV). Pirámide gaussiana de 5 niveles, arranca en la traslación global d0 (correlación de fase), 3
    iteraciones por nivel con tensor de estructura suavizado (σ 6 px), regularización suave y mediana 5×5 del flujo."""
    from scipy import ndimage as nd

    def pir(img):
        P = [img.astype(np.float32)]
        for _ in range(niveles - 1):
            P.append(nd.gaussian_filter(P[-1], 1.0)[::2, ::2])
        return P
    PA, PB = pir(A), pir(B)
    F = None
    g = lambda x: nd.gaussian_filter(x, sigma)
    for lv in range(niveles - 1, -1, -1):
        a, b = PA[lv], PB[lv]; h, w = a.shape
        if F is None:
            F = np.zeros((h, w, 2), np.float32); F[..., 0] = d0[0] / 2 ** lv; F[..., 1] = d0[1] / 2 ** lv
        else:
            F = np.stack([nd.zoom(F[..., c], (h / F.shape[0], w / F.shape[1]), order=1)[:h, :w] for c in range(2)], -1) * 2
        gy_a, gx_a = np.gradient(a)
        for _ in range(iters):
            bw = deformar1(b, F)
            gy_b, gx_b = np.gradient(bw)
            Ix = 0.5 * (gx_a + gx_b); Iy = 0.5 * (gy_a + gy_b); It = bw - a
            Ixx, Iyy, Ixy, Ixt, Iyt = g(Ix * Ix), g(Iy * Iy), g(Ix * Iy), g(Ix * It), g(Iy * It)
            reg = 6.5 + 1e-3 * (Ixx + Iyy)
            a11, a22 = Ixx + reg, Iyy + reg
            det = a11 * a22 - Ixy * Ixy
            F[..., 0] -= (a22 * Ixt - Ixy * Iyt) / det
            F[..., 1] -= (a11 * Iyt - Ixy * Ixt) / det
            F = np.stack([nd.median_filter(F[..., c], 5) for c in range(2)], -1)
    return F


def lento_mc(toma, n0, n_fuente, posiciones, salida, wb=None, zoom=None, registro=None):
    """Cámara lenta con mezcla de cuadros compensada en movimiento. posiciones: posición (en cuadros de la fuente,
    relativa a n0) de cada cuadro de salida. Entre dos cuadros A = i y B = i+1 se calcula el flujo óptico denso en los
    dos sentidos (flujo_lk: Lucas–Kanade piramidal a resolución completa sobre la luma, arrancando en la traslación del
    estampado medida por correlación de fase) y el cuadro intermedio con peso f es
    (1−f)·A(x + F_f→A) + f·B(x + F_f→B), con F_f→A = −(1−f)f·F_AB + f²·F_BA y F_f→B = (1−f)²·F_AB − f(1−f)·F_BA.
    Donde las dos imágenes deformadas no coinciden (|ΔY| > 12, suavizado) se toma solo la más cercana en el tiempo, para
    que no aparezca un doble contorno sobre el estampado. Primero se probó una traslación única por correlación de fase:
    el estampado rota y se deforma durante la revelación y dejaba 5–13 % de píxeles con doble contorno (med/fantasmas_3375.json).
    wb: ganancias RGB por cuadro de fuente (lista) o None. zoom(k) -> (x, y, w, h) ventana en 1080×1920 o None."""
    from scipy import ndimage as nd
    src = leer_fuente_yuv444(toma, n0, n_fuente)
    if wb is not None:
        for i, fr in enumerate(src):
            rgb = yuv444_rgb(fr[0], fr[1], fr[2]) * np.array(wb[i], np.float32)
            Y, Cb, Cr = rgb_yuv444(rgb); src[i] = np.stack([u8(Y), u8(Cb), u8(Cr)])
    cajas = []
    for i in range(n_fuente):
        m = estampado_blanca_frente(src[i][0])
        ys, xs = np.nonzero(m)
        cajas.append([int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None)
    desp = []
    for i in range(n_fuente - 1):                     # traslación global del estampado (arranque del flujo)
        x0, y0, x1, y1 = cajas[i] or cajas[i + 1]
        x0, y0, x1, y1 = max(0, x0 - 48), max(0, y0 - 48), min(W, x1 + 48), min(H, y1 + 48)
        desp.append(fase(src[i][0][y0:y1, x0:x1].astype(np.float32), src[i + 1][0][y0:y1, x0:x1].astype(np.float32)))
    cache = {}

    def flujos(i):
        if i not in cache:
            cache.clear()
            dx, dy, _ = desp[i]
            cache[i] = (flujo_lk(src[i][0], src[i + 1][0], (dx, dy)), flujo_lk(src[i + 1][0], src[i][0], (-dx, -dy)))
        return cache[i]

    def deformar(fr, F):
        return np.stack([deformar1(fr[c].astype(np.float32), F, order=3) for c in range(3)])
    enc = F4._encoder(salida)
    log = []
    for k, s in enumerate(posiciones):
        i = int(math.floor(s + 1e-6)); f = s - i
        if i >= n_fuente - 1:
            i, f = n_fuente - 1, 0.0
        med = None
        if f < 1e-4:
            fr = src[i].astype(np.float32); tipo = 'real'
        else:
            F01, F10 = flujos(i)
            wa = deformar(src[i], -(1 - f) * f * F01 + f * f * F10)
            wb_ = deformar(src[i + 1], (1 - f) ** 2 * F01 - f * (1 - f) * F10)
            dif = nd.gaussian_filter(np.abs(wa[0] - wb_[0]), 2.0)
            g = np.clip((dif - 12.0) / 20.0, 0, 1)                  # 0 = coinciden; 1 = se toma solo la más cercana
            fe = f * (1 - g) + (0.0 if f <= 0.5 else 1.0) * g
            fr = wa * (1 - fe) + wb_ * fe
            cj = cajas[i] or cajas[i + 1]
            if cj:
                x0, y0, x1, y1 = cj
                d0 = np.abs(wa[0] - wb_[0])[y0:y1, x0:x1]
                med = dict(desacuerdo_mayor_40_pct=round(100 * float((d0 > 40).mean()), 3),
                           arbitrado_pct=round(100 * float((g[y0:y1, x0:x1] > 0.5).mean()), 3))
            tipo = f'flujo {1 - f:.2f}·c{n0 + i} + {f:.2f}·c{n0 + i + 1}'
        fr = u8(fr)
        vent = None
        if zoom is not None:
            vent = zoom(k)
            if vent is not None:
                fr = recorte(fr, *vent)
        enc.stdin.write(fr.tobytes())
        log.append(dict(k=k, pos_fuente=round(n0 + s, 3), tipo=tipo, estampado=med,
                        ventana=None if vent is None else [round(v, 2) for v in vent]))
    enc.stdin.close(); enc.wait()
    if registro is not None:
        registro.update(metodo='flujo óptico denso Lucas–Kanade piramidal (numpy/scipy, sin OpenCV) en los dos sentidos, '
                               'arranque en la traslación del estampado por correlación de fase',
                        traslacion_estampado=[dict(de=f'c{n0 + i}', a=f'c{n0 + i + 1}', dx=round(d[0], 2), dy=round(d[1], 2),
                                                   pico=round(d[2], 3)) for i, d in enumerate(desp)],
                        cajas_estampado=cajas, cuadros=log)
    return dict(toma=toma, n0=n0, cuadros=len(posiciones), salida=str(salida))


# =====================================================================================================
# MC-03 · datos de la pieza
# =====================================================================================================
T = R / 'TRABAJO/marca/MC-03'
HJ, P, A, MAS, MED = T / 'hojas', T / 'planos', T / 'audio', T / 'master', T / 'med'
EVID = T / 'evidencia_v01'
PIEZA = Path('/mnt/project-files/piezas/MARCA_comunidad/MC-03_0_40')
NF = 430
DUR = NF / FPS                    # 14,333 s
NOMBRES = {'A': 'ROCCE_MC03_0_40_A_v01.mp4', 'B': 'ROCCE_MC03_0_40_B_v01.mp4',
           'A_sinmusica': 'ROCCE_MC03_0_40_SINMUSICA_v01.mp4'}
CORTES = [60, 80, 100, 120, 160, 190, 220, 250, 280, 310, 370]
NOMBRES_V02 = {'A': 'ROCCE_MC03_0_40_A_v02.mp4', 'B': 'ROCCE_MC03_0_40_B_v02.mp4',
               'A_sinmusica': 'ROCCE_MC03_0_40_SINMUSICA_v02.mp4'}

# tabla del guion con los cuadros fijados en las hojas cada 0,1 s (hojas/). n0 = primer cuadro de la fuente.
PLANOS = [
    dict(id='01', m0=0, nf=60, tipo='n', toma='IMG_7999', n0=101, fuente='3,367–5,333', funcion='APUESTA + PISTA'),
    dict(id='02', m0=60, nf=20, tipo='n', toma='clip_f2a34e51', n0=30, fuente='1,000–1,633', funcion='EN CONTRA (repetición)'),
    dict(id='03', m0=80, nf=20, tipo='n', toma='IMG_8002', n0=45, fuente='1,500–2,133', funcion='EN CONTRA (repetición)'),
    dict(id='04', m0=100, nf=20, tipo='n', toma='IMG_7999', n0=81, fuente='2,700–3,333', funcion='EN CONTRA · repite la pista'),
    dict(id='05', m0=120, nf=40, tipo='n', toma='IMG_7884', n0=96, fuente='3,200–4,500', funcion='SUBE LA APUESTA'),
    dict(id='06', m0=160, nf=30, tipo='n', toma='IMG_8002', n0=73, fuente='2,433–3,400', funcion='A FAVOR · cortado → completo'),
    dict(id='07', m0=190, nf=30, tipo='n', toma='clip_f2a34e51', n0=165, fuente='5,500–6,467', funcion='A FAVOR'),
    dict(id='08', m0=220, nf=30, tipo='n', toma='IMG_4627', n0=51, fuente='1,700–2,667', funcion='A FAVOR'),
    dict(id='09', m0=250, nf=30, tipo='n', toma='IMG_7896', n0=30, fuente='1,000–1,967', funcion='A FAVOR'),
    dict(id='10', m0=280, nf=30, tipo='congelado', toma='IMG_7999', n=160, z0=1.30, z1=1.40, cx=860, cy=1720,
         fuente='cuadro 160 (5,333) congelado', funcion='GRAN PREGUNTA'),
    dict(id='11-12', m0=310, nf=120, tipo='lento', toma='IMG_3375', n0=9, n_fuente=60,
         fuente='0,300–1,300 (plano 11) y 1,300–2,267 (plano 12), ×0,5 con mezcla compensada', funcion='GIRO + CTA'),
]
# 3375: plano 11 = 0,30–1,30 a ×0,5 (c310–c369) y plano 12 = 1,30–2,27 a ×0,49 (c370–c429) + acercamiento 1,00→1,06
POS_3375 = [k / 2 for k in range(60)] + [30 + (k * 29 / 59) for k in range(60)]
WB_OBJ = (-3.0, 0.0)          # B−R y G−R objetivo del blanco de 3375 (foto de producto blanca_frente_detalle: −4,4 / +0,5)


def zoom_3375(k):
    """plano 12 (k ≥ 60): acercamiento 1,00→1,06 anclado arriba (el estampado baja y se aleja de la caja del CTA) y
    centrado en x sobre el estampado (x medio medido 705 en c39–c68)."""
    if k < 60:
        return None
    Z = 1.0 + 0.06 * (k - 60) / 59
    w, h = W / Z, H / Z
    x = min(max(705 - w / 2, 0), W - w)
    return (x, 0.0, w, h)


def etapa_hojas():
    HJ.mkdir(parents=True, exist_ok=True)
    U.hoja_src('IMG_8002', 45, 106, HJ / '8002_c45-c106_c3.jpg', cada=3, ancho=216, cols=11)
    U.hoja_src('IMG_7999', 0, 160, HJ / '7999_c0-c160_c3.jpg', cada=3, ancho=180, cols=12)
    U.hoja_src('IMG_7884', 96, 138, HJ / '7884_c96-c138_c3.jpg', cada=3, ancho=216, cols=8)
    U.hoja_src('IMG_3375', 0, 68, HJ / '3375_c0-c68_c3.jpg', cada=3, ancho=216, cols=8)
    U.hoja_src('clip_f2a34e51', 0, 235, HJ / 'f2a3_c0-c235_c3.jpg', cada=3, ancho=160, cols=14)
    U.hoja_src('IMG_4627', 45, 84, HJ / '4627_c45-c84_c3.jpg', cada=3, ancho=216, cols=7)
    U.hoja_src('IMG_7896', 27, 63, HJ / '7896_c27-c63_c3.jpg', cada=3, ancho=216, cols=7)


def wb_3375():
    """ganancias R, G, B por cuadro de 3375 (c9–c68) para llevar el blanco a WB_OBJ conservando su luma; suavizadas con
    una media móvil de 7 cuadros (sin parpadeo). Medición en cuadros 270×480."""
    fr = U.leer(V._src('IMG_3375'), 270, 480, n0=9, n1=68, vf_pre=V.color('IMG_3375'))
    g = []
    med = []
    for f in fr:
        w = blanco_medido(f)
        Lw = float(w @ [.2126, .7152, .0722])
        tr = Lw - 0.0722 * WB_OBJ[0] - 0.7152 * WB_OBJ[1]
        t = np.array([tr, tr + WB_OBJ[1], tr + WB_OBJ[0]])
        g.append(t / w); med.append(w)
    g = np.array(g)
    k = 7; pad = np.pad(g, ((k // 2, k // 2), (0, 0)), mode='edge')
    gs = np.stack([np.convolve(pad[:, c], np.ones(k) / k, 'valid') for c in range(3)], 1)
    return gs.tolist(), [m.tolist() for m in med]


def etapa_planos(solo=None):
    """solo: ids de planos a rehacer (el resto se reutiliza de planos.json si su archivo existe)."""
    P.mkdir(parents=True, exist_ok=True)
    previo = {r['id']: r for r in json.load(open(T / 'planos.json'))['planos']} if (T / 'planos.json').exists() else {}
    reg = []
    for p in PLANOS:
        out = P / f"{p['id']}.mp4"
        if solo and p['id'] not in solo and p['id'] in previo and out.exists():
            reg.append(previo[p['id']]); print(p['id'], 'reutilizado', flush=True)
            continue
        if p['tipo'] == 'n':
            r = U.plano_n(p['toma'], p['n0'], p['nf'], out, caja=None)
        elif p['tipo'] == 'congelado':
            r = congelado_zoom(p['toma'], p['n'], out, p['z0'], p['z1'], p['cx'], p['cy'], p['nf'])
        else:
            gs, med = wb_3375()
            info = {}
            r = lento_mc(p['toma'], p['n0'], p['n_fuente'], POS_3375, out, wb=gs, zoom=zoom_3375, registro=info)
            info.update(wb_ganancias=gs, wb_blanco_medido=med, wb_objetivo=WB_OBJ)
            jdump(info, T / 'lento_3375.json')
        r.update({k: v for k, v in p.items() if k not in r})
        r['cuadros'] = p['nf'] if 'cuadros' not in r else r['cuadros']
        assert r['cuadros'] == p['nf'], (p['id'], r['cuadros'])
        reg.append(r); print(p['id'], r['cuadros'], flush=True)
    n = V.unir(reg, T / 'mc03_base.mp4')
    assert n == NF, n
    jdump(dict(cuadros=n, planos=reg), T / 'planos.json')


# =====================================================================================================
# interfaz MC-03 · marcador de transmisión de tenis (distinto del de MC-01) + etiquetas + textos
# =====================================================================================================
MX, MY, MW = 60, 250, 540           # marcador: x 60–600, y 250 (guion)
FILA, PADM = 66, 10


def marcador_tv(fila1, fila2, destello=None, ad_apagado=False, game=False):
    """Caja azul noche #0F1C2E al 90 %, dos filas (nombres Inter Display Bold 46 px blancos), celdas de puntaje celestes
    con números #141414, punto de saque «●» celeste delante de ROCCÉ. destello: 0/1 fila cuyo puntaje acaba de cambiar
    (celda blanca 3 cuadros). game: la caja pasa a una sola banda «GAME · ROCCÉ» con la misma altura."""
    Hc = 2 * FILA + 2 * PADM
    im = Image.new('RGBA', (MW, Hc), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, MW - 1, Hc - 1], radius=16, fill=NAVY + (230,))
    fb = ImageFont.truetype(str(C.FUENTES / 'InterDisplay-Bold.otf'), 46)
    fn = ImageFont.truetype(str(C.FUENTES / 'InterDisplay-Bold.otf'), 46)
    asc, dsc = fb.getmetrics()
    if game:
        f2 = ImageFont.truetype(str(C.FUENTES / 'InterDisplay-ExtraBold.otf'), 64)
        a2, d2 = f2.getmetrics()
        t1, t2 = 'GAME', ' · ROCCÉ'
        w1, w2 = f2.getlength(t1), f2.getlength(t2)
        x = (MW - (w1 + 36 + w2)) / 2; yb = (Hc - (a2 + d2)) / 2
        x0b, y0b, x1b, y1b = f2.getbbox(t1)
        d.rounded_rectangle([x - 4, PADM + 8, x + w1 + 32, Hc - PADM - 8], radius=10, fill=C.CELESTE + (255,))
        d.text((x + 14, yb), t1, font=f2, fill=C.TINTA + (255,))
        d.text((x + w1 + 36, yb), t2, font=f2, fill=C.BLANCO + (255,))
        return im
    for i, (nombre, pts) in enumerate((fila1, fila2)):
        y0 = PADM + i * FILA
        yt = y0 + (FILA - (asc + dsc)) / 2
        if i == 0:
            d.ellipse([22, y0 + FILA / 2 - 9, 40, y0 + FILA / 2 + 9], fill=C.CELESTE + (255,))
        d.text((58, yt), nombre, font=fn, fill=C.BLANCO + (255,))
        cw = 112; cx0 = MW - PADM - cw
        if i == 0 and ad_apagado:
            d.rounded_rectangle([cx0, y0 + 6, cx0 + cw, y0 + FILA - 6], radius=10, outline=C.CELESTE + (255,), width=3)
            col = C.CELESTE
        else:
            fill = C.BLANCO if destello == i else C.CELESTE
            d.rounded_rectangle([cx0, y0 + 6, cx0 + cw, y0 + FILA - 6], radius=10, fill=fill + (255,))
            col = C.TINTA
        w = fb.getlength(pts)
        d.text((cx0 + (cw - w) / 2, yt), pts, font=fb, fill=col + (255,))
        if i == 0:
            d.line([20, y0 + FILA, MW - 20, y0 + FILA], fill=(255, 255, 255, 40), width=2)
    return im


# estados del marcador por cuadro (guion: 0-40 c0 → 15-40 c166 → 30-40 c196 → 40·40 c226 → AD c256 → GAME c340)
MARCADOR = [(0, '0', '40'), (166, '15', '40'), (196, '30', '40'), (226, '40', '40'), (256, 'AD', '40'), (340, 'GAME', '')]


def estado_marcador(k):
    e = [m for m in MARCADOR if k >= m[0]][-1]
    return e


TEXTOS_03 = []      # se llena en armar_textos(): para el control de grafías exactas


def armar_textos(hook, ver='v01'):
    """Elementos de texto de MC-03 con sus cuadros. Devuelve lista de dict(el, c0, c1, pop). ver='v02': el dato del hook A
    en caja negra (dictamen 02 de Roma, corrección 2)."""
    Y = 420
    L = []
    # halo más denso que el de comun.placa por defecto (0,55): media pieza va sobre tela blanca o espuma, y con 0,55 la
    # placa blanca se lee mal a 360 px (prueba en evidencia_v01/halo_prueba_360px.png). Mismo halo en toda la pieza.
    HP = dict(halo=0.95, sombra_px=16)
    HD = dict(halo=0.9, sombra_px=12)

    def add(el, c0, c1, pop=False):
        L.append(dict(el=el, c0=c0, c1=c1, pop=pop))
    add(caja('0-40. ¿Lo damos vuelta?', 76, Y, pad=(28, 14), nombre='hook_caja'), 0, 59, True)
    if hook == 'A' and ver == 'v01':
        add(dato('La sesión de fotos de Roccé,\npunto por punto.', 48, 620, nombre='hook_A_dato', **HD), 0, 59)
    elif hook == 'A':
        # v02: caja negra SemiBold 50 en la misma y (620), relleno compacto 28/14 e interlineado 1,0 como los datos en caja
        # negra de MC-04 v02; termina en y 771 y el estampado de 7999 empieza en y ≥ 840 en c0–c59 (≥ 40 px, medido)
        add(caja('La sesión de fotos de Roccé,\npunto por punto.', 50, 620, tema='negra', interlineado=1.0, pad=(28, 14),
                 nombre='hook_A_dato'), 0, 59)
    else:
        # texto de la burbuja a 50 px (mínimo de la especificación 05); para que entre entre la caja y «ROCÉ» (y ≈ 840
        # en c59) la caja del hook usa el relleno compacto del CTA y la tarjeta, relleno 28 e interlineado 1,0; corrida
        # 30 px a la derecha (x 252–887) para no tapar la etiqueta interior del cuello, que en c18–c35 sube por x 90–230
        bur = burbuja_emoji([[('t', 'Pasamos de estar cerca a')], [('t', 'hacerlo??? '), ('e', '🤫🤫💎')]], size=50,
                            y=Y_BURBUJA, cx=570, nombre='hook_B_burbuja', pad=28, interlineado=1.0)
        # pop anclado arriba: centrado, a ×1,18 subía 20 px y se montaba sobre la caja del hook en c0 (la portada de B);
        # así crece hacia abajo, donde en c0–c1 no hay estampado (está en y ≥ 1450)
        bur.ancla = 'arriba'
        add(bur, 0, 59, True)
    add(placa('0-15: ARENA.', 88, Y, **HP), 60, 79)
    add(placa('0-30: CORTADA.', 88, Y, **HP), 80, 99)
    add(placa('0-40: LA SOMBRA.', 88, Y, **HP), 100, 119)
    add(placa('TRIPLE BREAK POINT.', 88, Y, **HP), 120, 159)
    add(placa('MISMA TOMA,\nUN SEGUNDO DESPUÉS.', 82, Y, **HP), 160, 189)
    add(placa('LA BLANCA,\nEN LA MISMA ARENA.', 86, Y, **HP), 190, 219)
    add(placa('IGUALES.', 88, Y, **HP), 220, 249)
    add(placa('VENTAJA ROCCÉ.', 88, Y, **HP), 250, 279)
    add(placa('Punto de game.\n¿Qué tapaba la sombra?', 82, Y, **HP), 280, 309)
    add(placa('Estar cerca\ny seguir sacando.', 84, Y, **HP), 325, 369)
    cta = caja('Mandáselo al que\nhoy está 0-40.', 76, Y, interlineado=1.0, pad=(28, 14), nombre='cta_caja')
    # la caja termina en y 634 y el estampado empieza en y 650 en c370: con el «pop» centrado (×1,18) el borde inferior
    # bajaba a y 653 y tocaba «ROCCÉ» en c370. Anclado abajo, el borde inferior queda quieto y el pop crece hacia arriba
    # (en c370 roza 21 px el margen azul del marcador, debajo de la pastilla GAME, sin tapar texto).
    cta.ancla = 'abajo'
    add(cta, 370, 429, True)
    return L


Y_BURBUJA = 562     # 10 px debajo de la caja del hook (y 420–552); la tarjeta termina en y ≈ 790 y «ROCÉ» llega a y ≈ 840 en c59
ETIQUETAS = None


def etiquetas():
    return dict(rep=pastilla('REPETICIÓN', nombre='etq_repeticion'),
                bp=pastilla('BREAK POINT', fondo=C.CELESTE + (255,), tinta=C.TINTA, nombre='etq_break_point'),
                igu=pastilla('IGUALES', nombre='etq_iguales'))


_CACHE_M = {}


def el_marcador(k):
    c0, a, b = estado_marcador(k)
    destello = None
    if c0 > 0 and k - c0 < 3 and a != 'GAME':
        destello = 0                                    # ROCCÉ suma: su celda destella 3 cuadros
    ad_apagado = (a == 'AD' and 280 <= k <= 309 and (k - 280) % 12 >= 6)   # «AD» titila en el plano 10
    game = a == 'GAME'
    clave = (a, b, destello, ad_apagado, game)
    if clave not in _CACHE_M:
        _CACHE_M[clave] = El(marcador_tv(('ROCCÉ', a), ('LA SESIÓN', b), destello, ad_apagado, game), MX, MY,
                             (MX, MY, MX + MW, MY + 2 * FILA + 2 * PADM), 'marcador', f'{a}-{b}' if not game else 'GAME · ROCCÉ')
    return _CACHE_M[clave], clave


POP = [1.18, 1.09]


def pop_e(el, i, margen=40):
    """escala del «pop» en el cuadro i de entrada. Si la caja visible a ×1,18 no entra en el ancho con 40 px por lado
    (la caja del hook mide 917 px: a ×1,18 llegaba a x −1…1081 y cortaba sus esquinas en c0, la portada), el pop se
    reduce en proporción para que entre; el resto de las gráficas conserva 1,18 / 1,09."""
    x0, y0, x1, y1 = el.caja
    emax = (W - 2 * margen) / (x1 - x0)
    return 1 + (POP[i] - 1) * min(1.0, (emax - 1) / (POP[0] - 1))


def ui_mc03(hook, ver='v01'):
    global ETIQUETAS
    ETIQUETAS = etiquetas()
    textos = armar_textos(hook, ver)

    def fn(k):
        items, clave = [], []
        m, cm = el_marcador(k)
        e = 1.0
        if cm[4] and k - 340 < 2:
            e = pop_e(m, k - 340)                 # GAME entra con «pop» (giro)
        items.append((m, e, 1.0)); clave.append(('m',) + cm + (e,))
        et = None
        if 60 <= k <= 119:
            et = 'rep'
        elif 126 <= k <= 159 and (k - 126) % 8 < 5:   # BREAK POINT titila (5 encendido / 3 apagado)
            et = 'bp'
        elif 226 <= k <= 249:
            et = 'igu'
        if et:
            items.append((ETIQUETAS[et], 1.0, 1.0)); clave.append(et)
        for t in textos:
            if t['c0'] <= k <= t['c1']:
                e = pop_e(t['el'], k - t['c0']) if t['pop'] and k - t['c0'] < 2 else 1.0
                items.append((t['el'], e, 1.0)); clave.append((t['el'].nombre, t['el'].texto, e))
        return tuple(clave), items
    return fn, textos


# =====================================================================================================
# medición del estampado por plano (para choques con el texto) · etapa medir
# =====================================================================================================
def mascara_estampado(rgb, tipo, roi):
    """máscara (1080×1920) del estampado visible dentro de roi=(x0, y0, x1, y1).
    blanca: letras oscuras sobre tela clara + celeste de «Founders Privée» / estrella; negra: letras claras sobre tela
    oscura. Se trabaja a 540×960 y se amplía."""
    from scipy import ndimage as nd
    if tipo == 'ambas':
        return mascara_estampado(rgb, 'blanca', roi) | mascara_estampado(rgb, 'negra', roi)
    f = rgb[::2, ::2].astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    L = .2126 * r + .7152 * g + .0722 * b
    if tipo == 'blanca':
        bg = nd.grey_closing(L, size=(21, 21))
        osc = (L < bg - 55) & (bg > 150)
        bgb = nd.grey_closing(b, size=(21, 21)) + 1; bgr = nd.grey_closing(r, size=(21, 21)) + 1
        cel = ((b / bgb - r / bgr) > 0.07) & (bg > 150) & (L > 110) & ((b - r) > 18)
        m = osc | cel
    else:
        bg = nd.grey_opening(L, size=(21, 21))
        sat = (f.max(-1) - f.min(-1)) / (f.max(-1) + 1)
        m = ((L - bg) > 40) & (bg < 75) & (sat < 0.3)
    m = nd.binary_opening(m, iterations=1)
    x0, y0, x1, y1 = [v // 2 for v in roi]
    lim = np.zeros_like(m); lim[y0:y1, x0:x1] = True
    # solo sobre la remera: componentes grandes de tela (clara: L > 185; oscura: L < 60) con agujeros rellenos y
    # dilatados 8 px (sin esto la arena, la roca bajo la espuma y el pasto dan falsos positivos)
    tela = (L > 185) if tipo == 'blanca' else ((L < 60) & (L > 5))
    tela = nd.binary_opening(tela & lim, iterations=2)
    lt, nt = nd.label(tela)
    if nt:
        st = nd.sum(tela, lt, range(1, nt + 1))
        tela = np.isin(lt, [j + 1 for j in range(nt) if st[j] >= max(800, 0.15 * st.max())])
        tela = nd.binary_dilation(nd.binary_fill_holes(nd.binary_closing(tela, iterations=6)), iterations=4)
    m &= lim & tela
    lab, n = nd.label(nd.binary_dilation(m, iterations=5))
    if n:
        sz = nd.sum(m, lab, range(1, n + 1))
        m &= np.isin(lab, [j + 1 for j in range(n) if sz[j] >= max(25, 0.04 * sz.max())])
    return m                                   # 540×960 (mitad de resolución)


# zona de búsqueda del estampado por plano (1080×1920, generosa; medida en las hojas). None = sin estampado a la vista.
ROI_03 = {
    # 01: la Blanca a la sombra de quien filma: la tela sombreada (L 100–150, azulada) no entra en la máscara de «tela
    # clara» y los bordes de la sombra dan falsos positivos. Se sigue la caja del estampado medida a mano en c59
    # (rejilla de 50 px: «ROCÉ» desde y 840, «…ckiclose.» hasta y 990, x 480–700; +60 px a la izquierda por la parte
    # que tapa el pliegue) hacia atrás por correlación de fase cuadro a cuadro.
    '01': ('seguir', dict(k_ref=59, caja=(420, 830, 720, 1000))), '02': ('negra', (0, 900, 1080, 1920)), '03': ('blanca', (0, 700, 1080, 1920)),
    '04': ('blanca', (0, 900, 1080, 1920)), '05': ('blanca', (0, 760, 1080, 1500)), '06': ('blanca', (0, 600, 1080, 1700)),
    '07': ('blanca', (0, 700, 1080, 1800)), '08': ('blanca', (0, 800, 1080, 1800)), '09': ('blanca', (100, 900, 900, 1350)),
    # 10: cuadro congelado con acercamiento lineal: caja medida a mano en c280 y c309 (rejilla de 50 px) e interpolada.
    '10': ('fijo', {280: (560, 905, 905, 1130), 309: (560, 900, 925, 1135)}), '11-12': ('blanca', (0, 560, 1080, 1300)),
}


def leer_cuadros(video, cuadros, w=W, h=H):
    """cuadros RGB de una lista de índices (select por número de cuadro)."""
    sel = '+'.join(f'eq(n\\,{k})' for k in cuadros)
    a = np.frombuffer(U.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-threads', HILOS, '-i', str(video), '-vf',
                             f"select='{sel}',scale={w}:{h}:flags=area,format=rgb24", '-fps_mode', 'passthrough',
                             '-f', 'rawvideo', '-']), np.uint8)
    return a.reshape(-1, h, w, 3)


def interp_caja(claves, k):
    ks = sorted(claves)
    if k <= ks[0]:
        return claves[ks[0]]
    if k >= ks[-1]:
        return claves[ks[-1]]
    a = max(c for c in ks if c <= k); b = min(c for c in ks if c >= k)
    if a == b:
        return claves[a]
    t = (k - a) / (b - a)
    return tuple(round(va + (vb - va) * t) for va, vb in zip(claves[a], claves[b]))


def seguir_caja(base, ks, k_ref, caja, margen=90):
    """caja (x0, y0, x1, y1) medida a mano en k_ref y seguida a los demás cuadros de ks por correlación de fase de la
    luma (media resolución) en la caja + margen; cuadro a cuadro, hacia atrás y hacia adelante desde k_ref."""
    fr = U.leer(base, W // 2, H // 2, n0=ks[0], n1=ks[-1])
    Y = {k: f.astype(np.float32) @ np.array([.2126, .7152, .0722], np.float32) for k, f in zip(ks, fr)}
    cajas = {k_ref: tuple(float(v) for v in caja)}

    def paso(ka, kb):
        x0, y0, x1, y1 = [v / 2 for v in cajas[ka]]
        X0, Y0 = int(max(0, x0 - margen / 2)), int(max(0, y0 - margen / 2))
        X1, Y1 = int(min(W // 2, x1 + margen / 2)), int(min(H // 2, y1 + margen / 2))
        if X1 - X0 < 32 or Y1 - Y0 < 32:
            cajas[kb] = cajas[ka]; return
        dx, dy, _ = fase(Y[ka][Y0:Y1, X0:X1], Y[kb][Y0:Y1, X0:X1])
        cajas[kb] = tuple(v + 2 * d for v, d in zip(cajas[ka], (dx, dy, dx, dy)))
    for k in range(k_ref, ks[0], -1):
        paso(k, k - 1)
    for k in range(k_ref, ks[-1]):
        paso(k, k + 1)
    return {k: tuple(int(round(min(max(v, 0), lim))) for v, lim in zip(c, (W, H, W, H))) for k, c in cajas.items()}


def medir_estampado(base, planos, roi_por_plano, nf, bloque=40):
    """para cada cuadro del máster: máscara del estampado a 540×960 (m) y su caja en 1080×1920."""
    out = {}
    for p in planos:
        pid = p['id']
        if roi_por_plano.get(pid) is None:
            continue
        tipo, roi = roi_por_plano[pid]
        ks = list(range(p['m0'], p['m0'] + p['nf']))
        if tipo in ('seguir', 'fijo'):
            cajas = seguir_caja(base, ks, roi['k_ref'], roi['caja']) if tipo == 'seguir' else \
                {k: interp_caja(roi, k) for k in ks}
            for k in ks:
                x0, y0, x1, y1 = cajas[k]
                m = np.zeros((H // 2, W // 2), bool); m[max(0, y0 // 2):max(0, y1 // 2), max(0, x0 // 2):max(0, x1 // 2)] = True
                out[k] = dict(plano=pid, caja=[int(v) for v in cajas[k]] if m.any() else None, px=int(m.sum()) * 4, m=m,
                              metodo='caja seguida' if tipo == 'seguir' else 'caja medida e interpolada')
            continue
        for i in range(0, len(ks), bloque):
            sub = ks[i:i + bloque]
            fr = U.leer(base, W, H, n0=sub[0], n1=sub[-1])
            for k, f in zip(sub, fr):
                m = mascara_estampado(f, tipo, roi)
                ys, xs = np.nonzero(m)
                out[k] = dict(plano=pid, caja=None if len(xs) == 0 else [int(xs.min()) * 2, int(ys.min()) * 2,
                                                                          int(xs.max()) * 2 + 1, int(ys.max()) * 2 + 1],
                              px=int(m.sum()) * 4, m=m)
    return out


def dibujar_estampado(base, est, cuadros, salida, ancho=270, cols=8, ui_fn=None):
    """evidencia: cuadros del máster con la máscara del estampado en rojo y su caja en amarillo (+ capa de texto)."""
    fr_all = leer_cuadros(base, cuadros)
    fnt = ImageFont.truetype(FONT_HOJA, 34)
    tiles = []
    for j, k in enumerate(cuadros):
        img = fr_all[j].copy()
        if ui_fn is not None:
            clave, items = ui_fn(k)
            rgba = capa_rgba(items)
            if rgba is not None:
                a = rgba[..., 3:4].astype(np.float32) / 255
                img = u8(img * (1 - a) + rgba[..., :3] * a)
        if k in est:
            mm = np.repeat(np.repeat(est[k]['m'], 2, 0), 2, 1)
            img[mm] = (0.4 * img[mm] + 0.6 * np.array([255, 0, 0])).astype(np.uint8)
        im = Image.fromarray(img); d = ImageDraw.Draw(im)
        if k in est and est[k]['caja']:
            d.rectangle(est[k]['caja'], outline=(255, 255, 0), width=5)
        d.rectangle([0, 0, 360, 48], fill=(0, 0, 0)); d.text((8, 6), f'c{k}', font=fnt, fill=(255, 255, 0))
        tiles.append(im.resize((ancho, round(ancho * H / W)), Image.LANCZOS))
    th = tiles[0].height; filas = math.ceil(len(tiles) / cols)
    Wd = Image.new('RGB', (cols * (ancho + 2), filas * (th + 2)), (32, 32, 32))
    for i, t in enumerate(tiles):
        Wd.paste(t, ((i % cols) * (ancho + 2), (i // cols) * (th + 2)))
    Wd.save(salida, quality=88)


def choques(est, margen=8):
    """función para componer(): píxeles de texto/gráfica (alfa > 0,15) sobre el estampado dilatado `margen` px."""
    from scipy import ndimage as nd
    dil = {}

    def fn(k, alfa):
        if alfa is None or k not in est:
            return dict(choque_px=0)
        if k not in dil:
            dil[k] = nd.binary_dilation(est[k]['m'], iterations=max(1, margen // 2))
        a = alfa[::2, ::2] > 0.15
        n = int((a & dil[k]).sum()) * 4
        return dict(choque_px=n, estampado_caja=est[k]['caja'])
    return fn


def etapa_medir():
    MED.mkdir(parents=True, exist_ok=True)
    planos = json.load(open(T / 'planos.json'))['planos']
    est = medir_estampado(T / 'mc03_base.mp4', planos, ROI_03, NF)
    res = {k: dict(plano=v['plano'], caja=v['caja'], px=v['px']) for k, v in est.items()}
    jdump(res, MED / 'estampado.json')
    # resumen por plano: borde superior mínimo del estampado (para ubicar textos)
    por = {}
    for k, v in res.items():
        if v['caja']:
            por.setdefault(v['plano'], []).append((k, v['caja'][1]))
    resumen = {p: dict(y_sup_min=min(y for _, y in l), cuadro=min(l, key=lambda t: t[1])[0]) for p, l in por.items()}
    jdump(resumen, MED / 'estampado_resumen.json')
    print(json.dumps(resumen, ensure_ascii=False))
    fn, _ = ui_mc03('B')
    dibujar_estampado(T / 'mc03_base.mp4', est, list(range(0, NF, 6)), MED / 'estampado_c0-c429_c6.jpg', ui_fn=fn)


# =====================================================================================================
# sonido · ambiente real + foley + música TEMP (§MC-03 «Sonido»)
# =====================================================================================================
def golpe_pelota(m, t):
    m.toque(t, .25, 700); m.bombo(t, .20, f0=300, f1=160, dec=.05, pista='fx'); m.log(t, 'golpe de pelota')


def aplauso(m, t0, dur, g0=.08, g1=.15, n=None, semilla=3):
    """aplauso provisorio: ráfagas de palmas sintetizadas al azar (g .08–.15) en la pista fx (foley, va en las 2 mezclas)."""
    rg = np.random.default_rng(semilla)
    n = n or int(dur * 34)
    for _ in range(n):
        t = t0 + rg.uniform(0, dur) * (1 - 0.35 * rg.uniform())
        L = int(0.12 * SR); tt = np.arange(L) / SR
        s = filt(ruido(L), 'band', [800 + rg.uniform(0, 600), 3600]) * np.exp(-tt / rg.uniform(0.008, 0.02))
        env_ = 1.0 - 0.7 * max(0.0, (t - t0) / dur - 0.4)
        m.put('fx', s / (np.abs(s).max() + 1e-9), t, rg.uniform(g0, g1) * env_, pan=rg.uniform(-0.7, 0.7))
    m.log(t0, f'aplauso {dur:.1f} s')


def latido(m, t, g=1.0):
    m.bombo(t, .55 * g, f0=75, f1=40, dec=.10, pista='fx'); m.bombo(t + .17, .38 * g, f0=68, f1=38, dec=.12, pista='fx')
    m.log(t, 'latido')


def mezcla_mc03(salida, musica=True):
    m = Mezcla(DUR)
    am = [('IMG_7999', 3.367, 0.0, 2.0, -6, 200, None), ('clip_f2a34e51', 1.000, 2.0, 2.667, -10, 150, None),
          ('IMG_8002', 1.500, 2.667, 3.333, -8, 150, None), ('IMG_7999', 2.700, 3.333, 4.0, -6, 200, None),
          ('IMG_7884', 3.200, 4.0, 5.333, -4, None, None), ('IMG_8002', 2.433, 5.333, 6.333, -8, 150, None),
          ('clip_f2a34e51', 5.500, 6.333, 7.333, -10, 150, None), ('IMG_4627', 1.700, 7.333, 8.333, -6, None, None),
          ('IMG_7896', 1.000, 8.333, 9.333, -8, None, None), ('IMG_7999', 4.333, 9.333, 10.333, -20, 200, 2500),
          ('IMG_4627', 6.000, 10.333, DUR, -18, None, None)]
    for toma, s0, t0, t1, g, hp, lp in am:
        m.ambiente(toma, s0, t0, t1, g, hp=hp, lp=lp, fade=0.012, fin_fade=(0.25 if t1 >= DUR - 0.01 else None))
    # foley e interfaz (las dos mezclas)
    for t in (2.0, 2.667, 3.333):
        m.barrido(t, .30, .20, sube=False); m.toque(t + .02, .14, 1500)
    m.toque(4.2, .16, 2600)                                  # c126: entra BREAK POINT
    for t in (5.533, 6.533, 7.533, 8.533):
        golpe_pelota(m, t)
    aplauso(m, 7.60, 0.8, semilla=5)
    # sin música, latidos e impacto a la mitad: con −14 LUFS sobre ambiente y foley quedaban 15 dB por encima del resto
    gl = 1.0 if musica else 0.5
    m.toque(0.0, .16, 1800)                                  # c0: «pop» de la caja del hook
    m.subida(8.333, 9.333, .14)
    latido(m, 9.6, gl); latido(m, 10.0, gl)
    # c310–c339 (revelación en cámara lenta, sin texto): los latidos se aceleran y una subida lleva al GAME; medido en
    # la primera mezcla: −35 dB RMS durante 1 s después de otro segundo de casi silencio (2 s sin energía antes del giro)
    for t in (10.40, 10.733, 10.967, 11.15):
        latido(m, t, gl * 0.8)
    m.subida(10.333, 11.30, .12)
    m.impacto(11.333, .55 * gl)
    aplauso(m, 11.40, 1.6, g0=.10, g1=.17, semilla=9)
    m.toque(12.333, .18, 2200)                               # CTA
    if musica:
        m.pad(0.0, [40, 43, 47], 5.3, .09, 900)              # Mi menor de tensión hasta 5,33 (0,05 → 0,09: el hook
        t = 0.0                                              #  medía −34,6 dB RMS en c0–c59, 22 dB debajo del resto)
        while t < 9.333 - 1e-6:
            m.charles(t, .11 if (round(t / 0.3333) % 2) else .07); t += 1 / 3
        m.campana(0.0, 76, .07)
        for tc, g in ((0.0, .6), (0.667, .3), (1.333, .35)):  # pulso de la apuesta en la grilla de 2/3 s de los cortes
            m.bombo(tc, g)
        for tc in (2.0, 2.667, 3.333, 4.0, 5.333, 6.333, 7.333, 8.333):
            m.bombo(tc, .7)
        m.campana(4.0, 71, .06); m.campana(4.333, 71, .05)   # break point: campana ×2
        for tc, n_ in zip((5.333, 6.333, 7.333, 8.333), (31, 33, 35, 36)):
            m.ocho08(tc, n_, .8, .5)                         # remontada: el bajo sube
        for tc, ch in zip((5.333, 6.333, 7.333, 8.333), ([43, 47, 50], [45, 48, 52], [47, 50, 54], [48, 52, 55])):
            m.pad(tc, ch, 0.95, .035, 1200, a=.05, r=.25)    # DESVÍO de sonido: acordes sobre el bajo (G–Am–Bm–C)
        m.silenciar('mus', 9.333, 10.333)
        m.pad(11.333, [43, 47, 50, 55], 3.0, .07, 1600)      # GAME: Sol mayor hasta el final (fundido)
        m.bombo(11.333, 1.0); m.campana(11.333, 79, .08); m.campana(11.333, 83, .05)
        t = 11.333
        while t < DUR - 0.1:
            m.charles(t, .07); t += 1 / 3
        m.bombo(12.333, .55); m.bombo(13.0, .4); m.bombo(13.667, .35)   # el CTA sostiene el pulso hasta el fundido
        m.fundido('mus', 13.83, DUR)
    return m.exportar(str(salida), lufs=-14)


def medir_ebur(f):
    r = subprocess.run(['ffmpeg', '-nostats', '-i', str(f), '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    I = float([l for l in r.splitlines() if l.strip().startswith('I:')][-1].split()[1])
    Pk = float([l for l in r.splitlines() if l.strip().startswith('Peak:')][-1].split()[1])
    return I, Pk


def asegurar_pico(wav, lufs=-14.0, tp_obj=-1.5):
    """sonido.exportar limita el pico de muestra (alimiter a −1,6 dBFS) pero no el pico verdadero: con foley de
    transitorios agudos el pico entre muestras llegó a −0,2 dBTP (MC-04 sin música). Acá, si hace falta, se repite el
    limitador sobremuestreado a 192 kHz (ve los picos entre muestras) y se reajusta la ganancia a −14 LUFS. Objetivo
    −1,5 dBTP en el WAV para que el AAC quede ≤ −1 dBTP. No toca sonido.py (común)."""
    wav = Path(wav)
    I, Pk = medir_ebur(wav)
    if Pk <= tp_obj and abs(I - lufs) < 0.5:
        return dict(lufs=I, pico_dbtp=Pk, retoque=False)
    src = wav.with_name(wav.stem + '_sin_retoque_tp.wav')
    shutil.copyfile(wav, src)
    gan, lim = lufs - I, 10 ** ((tp_obj - 0.3) / 20)
    for _ in range(5):
        U.run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-af',
               f'volume={gan:.2f}dB,aresample=192000,alimiter=limit={lim:.4f}:level=false:attack=1:release=60:latency=1,'
               f'aresample=48000', '-c:a', 'pcm_f32le', str(wav)])
        I, Pk = medir_ebur(wav)
        if Pk <= tp_obj and abs(I - lufs) < 0.4:
            break
        gan += lufs - I
        if Pk > tp_obj:
            lim *= 10 ** ((tp_obj - Pk - 0.1) / 20)
    return dict(lufs=I, pico_dbtp=Pk, retoque=True, ganancia_db=round(gan, 2), limite=round(lim, 4))


def etapa_audio():
    A.mkdir(parents=True, exist_ok=True)
    r1 = mezcla_mc03(A / 'mc03_completa.wav', True)
    r2 = mezcla_mc03(A / 'mc03_sinmusica.wav', False)
    q1, q2 = asegurar_pico(A / 'mc03_completa.wav'), asegurar_pico(A / 'mc03_sinmusica.wav')
    jdump(dict(completa=dict(exportar=r1, final=q1), sinmusica=dict(exportar=r2, final=q2)), A / 'sonoridad_wav.json')
    print('completa', r1, q1, 'sin música', r2, q2)


# =====================================================================================================
# máster · control · entrega
# =====================================================================================================
def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    est = None
    if (MED / 'estampado.json').exists():
        planos = json.load(open(T / 'planos.json'))['planos']
        est = medir_estampado(T / 'mc03_base.mp4', planos, ROI_03, NF)
    regs = {}
    for hook in ('A', 'B'):
        fn, textos = ui_mc03(hook)
        reg = componer(T / 'mc03_base.mp4', fn, A / 'mc03_completa.wav', MAS / NOMBRES[hook], NF,
                       choque_fn=choques(est) if est else None)
        regs[hook] = reg
        print(hook, 'choques', sum(1 for r in reg if r.get('choque_px', 0) > 0), flush=True)
    copiar_video(MAS / NOMBRES['A'], A / 'mc03_sinmusica.wav', MAS / NOMBRES['A_sinmusica'])
    jdump(regs, MAS / 'registro_cuadros.json')


# =====================================================================================================
# v02 (dictamen 02 de Roma, 25/11/2026): Blanca fría a B−R ≤ +8 solo en los neutros claros de la tela (L > 170), con las
# funciones de MC-04 v02 (mc04.medir_neutro / pre_neutro) y el mismo objetivo (+7 / +1,5); la sombra proyectada (la pista)
# no se toca: la rampa de luma empieza en L 170 y no hay punto de sombra. Dato del hook A en caja negra (armar_textos).
# =====================================================================================================
MAS2 = T / 'master_v02'
NEUTRO_03 = {                      # caja de la remera por plano (la máscara la recorta por croma; la arena queda afuera)
    '01': dict(cajas={0: (0, 0, 1080, 1920)}),
    '03': dict(cajas={80: (0, 520, 1080, 1920)}),       # arriba, cielo y médano
    '04': dict(cajas={100: (0, 0, 1080, 1920)}),
    '06': dict(cajas={160: (0, 380, 1080, 1920)}),
    '07': dict(cajas={190: (0, 450, 1080, 1920)}),
    '10': dict(cajas={280: (0, 0, 1080, 1920)}),
}
# rampa en luminancia L (RGB 0–255) convertida a luma de video: peso 0 hasta L 160 y completo desde L 172, para que todo
# lo que pasa de L 170 quede corregido (con 170 → 185 la medición de Roma, mayor componente con L > 170, daba +8,1 a
# +8,8 por la franja parcial) y la sombra proyectada (L < 150) no cambie nada
RAMPA_03 = (16 + 160 * 219 / 255, 16 + 172 * 219 / 255)
# plano 07 (clip_f2a34e51): la tela entera está en B−R +46; con L > 170 solo, los pliegues quedaban celestes al lado de las
# luces neutras (c205, evidencia_v02/plano07_L170_descartado.jpg). Ahí no hay sombra proyectada (la pista es de 7999):
# usa la rampa de MC-04 v02 (luma 70 → 100). Desvío para Roma.


def ctx_v02():
    import mc04 as M4
    M4.CTX.update(planos=json.load(open(T / 'planos.json'))['planos'], neutro=NEUTRO_03, rampa=RAMPA_03,
                  base=T / 'mc03_base.mp4', med=MED / 'neutro_v02.json', sombra=False, mask_y=100.0, componentes='grandes',
                  excluir_estampado=True, resguardo_relativo=25.0, rampas={'07': M4.RAMPA_Y})
    return M4


def etapa_master_v02():
    MAS2.mkdir(parents=True, exist_ok=True)
    for n in NOMBRES_V02.values():
        assert not (MAS2 / n).exists() or '--rehacer' in sys.argv, f'{MAS2 / n} ya existe'
    M4 = ctx_v02()
    planos = json.load(open(T / 'planos.json'))['planos']
    est = medir_estampado(T / 'mc03_base.mp4', planos, ROI_03, NF)
    med = json.load(open(MED / 'neutro_v02.json')) if (MED / 'neutro_v02.json').exists() and '--remedir' not in sys.argv \
        else M4.medir_neutro()
    regs, logs = {}, {}
    for hook in ('A', 'B'):
        fn, textos = ui_mc03(hook, 'v02')
        log = []
        reg = componer(T / 'mc03_base.mp4', fn, A / 'mc03_completa.wav', MAS2 / NOMBRES_V02[hook], NF,
                       choque_fn=choques(est), pre_fn=M4.pre_neutro(med, log))
        regs[hook], logs[hook] = reg, log
        print(hook, 'choques', sum(1 for r in reg if r.get('choque_px', 0) > 0), flush=True)
    copiar_video(MAS2 / NOMBRES_V02['A'], A / 'mc03_sinmusica.wav', MAS2 / NOMBRES_V02['A_sinmusica'])
    jdump(regs, MAS2 / 'registro_cuadros.json')
    jdump(logs['A'], MED / 'neutro_v02_por_cuadro.json')


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    if etapa == 'planos' and len(sys.argv) > 2:
        etapa_planos(solo=sys.argv[2].split(','))          # p. ej. python mc03.py planos 11-12
    else:
        {'hojas': etapa_hojas, 'planos': etapa_planos, 'medir': etapa_medir, 'audio': etapa_audio,
         'master': etapa_master, 'medir_neutro': lambda: ctx_v02().medir_neutro(), 'master_v02': etapa_master_v02}[etapa]()
