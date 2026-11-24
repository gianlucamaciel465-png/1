#!/usr/bin/env python3
"""BOC-SUD (24/11/2026) · herramientas comunes para las 3 piezas de Boca campeón de la Sudamericana.

Material: tomas propias (biblioteca SDR en TRABAJO/bocsud/lib, hecha con scripts/fmt/video.plano) y archivos de
Wikimedia Commons (TRABAJO/bocsud/commons/arch, con su ficha de licencia en fichas.json).
Todo sale a 1080x1920, 30 fps, BT.709 rango limitado, intermedios x264 crf 12.
"""
import subprocess, json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageDraw
sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V

W, H, FPS = 1080, 1920, 30
T = Path('/home/user/1/TRABAJO/bocsud')
LIB = T / 'lib'
ARCH = T / 'commons' / 'arch'
ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709',
       '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(' '.join(map(str, cmd))[:400] + '\n' + r.stderr[-2500:])
    return r.stdout


def encoder(salida):
    """recibe cuadros RGB24 1080x1920 por stdin (sRGB) y escribe yuv420p BT.709 rango limitado."""
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                             '-r', str(FPS), '-i', '-', '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
                             *ENC, str(salida)], stdin=subprocess.PIPE)


def nf(dur):
    return int(round(dur * FPS))


def suave(x):
    """curva de aceleración suave 0..1"""
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ventana_de(img_w, img_h, cx, cy, z, aspecto=W / H):
    """ventana (x0,y0,x1,y1) de aspecto 9:16 que cubre, centrada en (cx,cy) (0..1), acercamiento z>=1"""
    if img_w / img_h > aspecto:
        h = img_h / z; w = h * aspecto
    else:
        w = img_w / z; h = w / aspecto
    x0 = min(max(cx * img_w - w / 2, 0), img_w - w); y0 = min(max(cy * img_h - h / 2, 0), img_h - h)
    return (x0, y0, x0 + w, y0 + h)


def cubrir(img, cx, cy, z, size=(W, H)):
    box = ventana_de(img.width, img.height, cx, cy, z, size[0] / size[1])
    return img.resize(size, Image.LANCZOS, box=box)


def fondo_ventana(img, k=0.0):
    """fondo para un plano horizontal: la misma imagen ampliada, desenfocada y oscurecida"""
    bg = cubrir(img, 0.5, 0.5, 1.15 + 0.02 * k, (W // 4, H // 4)).filter(ImageFilter.GaussianBlur(9))
    bg = bg.resize((W, H), Image.BICUBIC)
    return Image.eval(bg, lambda v: int(v * 0.42))


def foto_movil(path, dur, salida, modo='cubrir', z0=1.0, z1=1.06, c0=(0.5, 0.5), c1=None, fg_w=W, fg_y=None,
               sacudida=None, por_cuadro=None):
    """Foto como plano con movimiento por cuadro (subpíxel con box de PIL).
    modo 'cubrir': llena 9:16. modo 'ventana': la foto entera a fg_w de ancho sobre su fondo desenfocado.
    sacudida: lista de (k, amplitud_px) para un temblor que decae (impacto). por_cuadro(k, Image) -> Image."""
    c1 = c1 or c0
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    n = nf(dur); enc = encoder(salida)
    for k in range(n):
        a = k / max(n - 1, 1)
        z = z0 + (z1 - z0) * a
        cx = c0[0] + (c1[0] - c0[0]) * a; cy = c0[1] + (c1[1] - c0[1]) * a
        dx = dy = 0.0
        for (k0, amp) in (sacudida or []):
            if k >= k0:
                e = amp * math.exp(-(k - k0) / 3.0)
                dx += e * math.sin(1.7 * (k - k0) + 0.3); dy += e * math.cos(2.3 * (k - k0))
        if modo == 'cubrir':
            box = ventana_de(im.width, im.height, cx, cy, z)
            bw = box[2] - box[0]; s = bw / W
            bw, bh = box[2] - box[0], box[3] - box[1]
            x0 = min(max(box[0] + dx * s, 0.0), im.width - bw); y0 = min(max(box[1] + dy * s, 0.0), im.height - bh)
            box = (x0, y0, min(x0 + bw, im.width), min(y0 + bh, im.height))     # el temblor no sale de la foto
            fr = im.resize((W, H), Image.LANCZOS, box=box)
        else:
            fr = fondo_ventana(im, a)
            fw = int(round(fg_w * z)); fh = int(round(fw * im.height / im.width))
            fg = im.resize((fw, fh), Image.LANCZOS)
            x = int(round((W - fw) / 2 + (cx - 0.5) * -fw * 0.2 + dx)); y = int(round((fg_y if fg_y is not None else (H - fh) / 2) + dy))
            fr.paste(fg, (x, y))
        if por_cuadro:
            fr = por_cuadro(k, fr)
        enc.stdin.write(np.asarray(fr, dtype=np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    return dict(foto=str(path), cuadros=n, salida=str(salida), modo=modo, z=(z0, z1), c=(c0, c1))


def foto_desenfocada(path, zonas, salida):
    """copia de la foto con zonas elípticas desenfocadas (caras de terceros a media distancia).
    zonas: [(cx, cy, rx, ry, sigma, pluma)] en píxeles de la foto. No toca el archivo original."""
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    for (cx, cy, rx, ry, sigma, pluma) in zonas:
        pad = int(max(rx, ry) + 4 * sigma + 3 * pluma)
        b = (cx - pad, cy - pad, cx + pad, cy + pad)
        reg = im.crop(b)
        bl = reg.filter(ImageFilter.GaussianBlur(sigma))
        m = Image.new('L', reg.size, 0)
        ImageDraw.Draw(m).ellipse([pad - rx, pad - ry, pad + rx, pad + ry], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(pluma))
        im.paste(Image.composite(bl, reg, m), b[:2])
    im.save(salida, quality=96)
    return salida


def leer_video(src, t0, dur, w, h, vf=''):
    """cuadros RGB del video src (cualquier tamaño) desde t0 durante dur, a 30 fps, escalados a w x h"""
    n = nf(dur)
    chain = (vf + ',' if vf else '') + f'fps={FPS},scale={w}:{h}:flags=lanczos,format=rgb24'
    p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-i', str(src), '-t', f'{dur + 0.3:.3f}', '-an',
                        '-vf', chain, '-frames:v', str(n), '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(p, np.uint8).reshape(-1, h, w, 3)
    if len(a) < n:
        a = np.concatenate([a, np.repeat(a[-1:], n - len(a), 0)])
    return a[:n]


def video_ventana(src, t0, dur, salida, recorte=None, fg_w=W, fg_y=None, z0=1.0, z1=1.0, vf='', por_cuadro=None):
    """Plano horizontal en vertical: el video a fg_w de ancho (recorte opcional x,y,w,h) sobre su fondo desenfocado."""
    sw, sh_ = [int(x) for x in sh(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                   'stream=width,height', '-of', 'csv=p=0', str(src)]).strip().split(',')[:2]]
    cuadros = leer_video(src, t0, dur, sw, sh_, vf)
    n = len(cuadros); enc = encoder(salida)
    for k, a in enumerate(cuadros):
        im = Image.fromarray(a)
        if recorte:
            x, y, w, h = recorte; im = im.crop((x, y, x + w, y + h))
        z = z0 + (z1 - z0) * k / max(n - 1, 1)
        fr = fondo_ventana(im, k / max(n - 1, 1))
        fw = int(round(fg_w * z)); fh = int(round(fw * im.height / im.width))
        fg = im.resize((fw, fh), Image.LANCZOS)
        fr.paste(fg, ((W - fw) // 2, int(round(fg_y if fg_y is not None else (H - fh) / 2))))
        if por_cuadro:
            fr = por_cuadro(k, fr)
        enc.stdin.write(np.asarray(fr, dtype=np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    return dict(video=str(src), desde=t0, cuadros=n, salida=str(salida))


def video_cubrir(src, t0, dur, salida, cx=0.5, cy=0.5, z0=1.0, z1=1.0, vf='', por_cuadro=None, src_size=None):
    """Video que llena 9:16 (recorte centrado en cx,cy con acercamiento z0->z1 por cuadro)."""
    if src_size is None:
        sw, sh_ = [int(x) for x in sh(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                       'stream=width,height', '-of', 'csv=p=0', str(src)]).strip().split(',')[:2]]
    else:
        sw, sh_ = src_size
    cuadros = leer_video(src, t0, dur, sw, sh_, vf)
    n = len(cuadros); enc = encoder(salida)
    for k, a in enumerate(cuadros):
        im = Image.fromarray(a)
        z = z0 + (z1 - z0) * k / max(n - 1, 1)
        ccx = cx(k) if callable(cx) else cx; ccy = cy(k) if callable(cy) else cy
        fr = im.resize((W, H), Image.LANCZOS, box=ventana_de(im.width, im.height, ccx, ccy, z))
        if por_cuadro:
            fr = por_cuadro(k, fr)
        enc.stdin.write(np.asarray(fr, dtype=np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    return dict(video=str(src), desde=t0, cuadros=n, salida=str(salida))


def lib(toma):
    """ruta del tramo de biblioteca de una toma propia y su inicio en segundos de la fuente"""
    for p in sorted(LIB.glob(f'{toma}_*.mp4')):
        a = float(p.stem.split('_')[2]); return p, a
    raise FileNotFoundError(toma)


def propia(toma, desde, hasta, salida, cx=0.5, cy=0.5, z0=1.0, z1=1.0, por_cuadro=None):
    """tramo [desde,hasta) en segundos de la FUENTE original de una toma propia, desde la biblioteca SDR 1080x1920"""
    p, a = lib(toma)
    return video_cubrir(p, desde - a, hasta - desde, salida, cx, cy, z0, z1, por_cuadro=por_cuadro, src_size=(W, H))


def negro(dur, salida, color=(0, 0, 0)):
    n = nf(dur); enc = encoder(salida)
    fr = np.zeros((H, W, 3), np.uint8); fr[:] = color
    for _ in range(n):
        enc.stdin.write(fr.tobytes())
    enc.stdin.close(); enc.wait()
    return dict(cuadros=n, salida=str(salida))


# ---------------- placa real (rc-blanca-placas.jpg, placa izquierda) ----------------
PLACAS = Path('/mnt/project-files/piezas/BOC-01_ultimo_minuto/material/rc-blanca-placas.jpg')
FONDO_PLACA = (16, 17, 19)


def _primer_cuadro(video):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    return Image.fromarray(np.frombuffer(raw, np.uint8).reshape(H, W, 3))


def placa(dur, salida, ancho=720, cy=880, z_in=1.35, k_in=4, temblor=(3, (3, -2), (-2, 2), (1, -1)),
          brillo=(8, 16), empuje=0.08, foco=None, fondo=None, oscurecer=0.42, desenfoque=26):
    """Placa izquierda de rc-blanca-placas (x 12–234, y 54–212), recortada por su contorno (chapa + marco) y con sombra.
    fondo: video 1080x1920 cuyo primer cuadro, desenfocado y oscurecido, hace de fondo (el plano de cierre que sigue);
    sin fondo, color liso. Entra de z_in a 1,0 en k_in cuadros, tiembla, la cruza un brillo y empuja suave hasta el
    final. foco=(fx, fy) 0..1 sobre la placa: el empuje se centra ahí (p. ej. el «2026»)."""
    src = Image.open(PLACAS).convert('RGB').crop((12, 54, 234, 212))
    sa = np.asarray(src).astype(np.float32)
    # la estrella azul de abajo a la derecha (fuente x 195–230, y 192–212) se tapa con el fondo oscuro vecino
    fondo_local = sa[195 - 54:210 - 54, 150 - 12:180 - 12].reshape(-1, 3).mean(0)
    sa[188 - 54:, 185 - 12:] = fondo_local
    src = Image.fromarray(sa.round().clip(0, 255).astype(np.uint8))
    placa_m = (sa.mean(2) > 110).astype(np.float32)          # la chapa (para enmascarar el brillo)
    # contorno: esquinas por extremos de la zona clara, agrandado para incluir el marco oscuro de la chapa
    ys, xs = np.nonzero(placa_m > 0)
    esq = [(xs[i], ys[i]) for i in (np.argmin(xs + ys), np.argmax(xs - ys), np.argmax(xs + ys), np.argmin(xs - ys))]
    mx = sum(e[0] for e in esq) / 4; my = sum(e[1] for e in esq) / 4
    esq = [(mx + (x - mx) * 1.05, my + (y - my) * 1.07) for x, y in esq]
    S4 = 8
    alfa_src = Image.new('L', (src.width * S4, src.height * S4), 0)
    ImageDraw.Draw(alfa_src).polygon([((x + 0.5) * S4, (y + 0.5) * S4) for x, y in esq], fill=255)
    if fondo is not None:
        fb = _primer_cuadro(fondo).filter(ImageFilter.GaussianBlur(desenfoque))
        base0 = np.asarray(fb, np.float32) * oscurecer
    else:
        base0 = np.zeros((H, W, 3), np.float32); base0[:] = FONDO_PLACA
    n = nf(dur); enc = encoder(salida)
    k_t0 = temblor[0]; desps = temblor[1:]
    for k in range(n):
        if k < k_in:
            z = z_in + (1.0 - z_in) * suave((k + 1) / k_in)
        else:
            z = 1.0 + empuje * suave((k - k_in) / max(n - k_in - 1, 1))
        w = ancho * z; h = w * src.height / src.width
        fx, fy = foco or (0.5, 0.5)
        hA = ancho * src.height / src.width
        if k < k_in:              # entrada: escala centrada en la placa
            x = W / 2 - 0.5 * w; y = cy - 0.5 * h
        else:                     # empuje anclado en el foco: el punto (fx, fy) de la placa queda quieto
            x = W / 2 - 0.5 * ancho - (z - 1) * fx * ancho
            y = cy - 0.5 * hA - (z - 1) * fy * hA
        dx = dy = 0
        if k_t0 <= k < k_t0 + len(desps):
            dx, dy = desps[k - k_t0]
        tam = (int(round(w)), int(round(h)))
        im = src.resize(tam, Image.LANCZOS)
        pm = np.asarray(Image.fromarray((placa_m * 255).astype(np.uint8)).resize(tam, Image.BILINEAR), np.float32) / 255
        al_im = alfa_src.resize(tam, Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2))
        al = np.asarray(al_im, np.float32) / 255
        yy, xx = np.mgrid[0:tam[1], 0:tam[0]]
        a = np.asarray(im, np.float32)
        if brillo and brillo[0] <= k <= brillo[1]:
            u = (k - brillo[0]) / max(brillo[1] - brillo[0], 1)
            xc = -0.2 * tam[0] + u * 1.4 * tam[0]
            band = np.clip(1 - np.abs((xx - 0.35 * yy) - xc) / 60.0, 0, 1)
            a = a + (255 - a) * 0.15 * (band * pm)[..., None]
        base = base0.copy()
        x0 = int(round(x + dx)); y0 = int(round(y + dy))
        # sombra de la chapa sobre el fondo
        sm = Image.new('L', (W, H), 0); sm.paste(al_im, (x0 + 14, y0 + 20))
        sm = np.asarray(sm.filter(ImageFilter.GaussianBlur(22)), np.float32) / 255
        base *= (1 - 0.6 * sm)[..., None]
        h_, w_ = al.shape
        xa, ya = max(x0, 0), max(y0, 0); xb, yb = min(x0 + w_, W), min(y0 + h_, H)
        sub = base[ya:yb, xa:xb]; aa = a[ya - y0:yb - y0, xa - x0:xb - x0]; mm = al[ya - y0:yb - y0, xa - x0:xb - x0, None]
        base[ya:yb, xa:xb] = sub * (1 - mm) + aa * mm
        enc.stdin.write(base.round().clip(0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    return dict(foto=str(PLACAS), recorte=(12, 54, 234, 212), cuadros=n, salida=str(salida), fondo=str(fondo))


# ---------------- sonido: mezcla con audio real de cualquier archivo y efectos de cancha ----------------
import sonido as S
from sonido import SR, filt, ruido, satur, env, db


class MezclaB(S.Mezcla):
    _cache = {}

    def leer_archivo(self, path):
        if path not in self._cache:
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-vn', '-map', '0:a:0', '-f', 'f32le', '-ac', '2',
                                  '-ar', str(SR), '-'], capture_output=True, check=True).stdout
            self._cache[path] = np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, 2)
        return self._cache[path]

    def real(self, path, src0, t0, t1, g_db=0.0, hp=None, lp=None, ini=0.01, fin=0.01, pista='amb', etiqueta=None):
        """audio real (estéreo) de `path` desde src0 s, colocado en [t0, t1) del máster, con fundidos ini/fin (s)."""
        a = self.leer_archivo(path)
        n = int(round((t1 - t0) * SR)); s0 = int(round(src0 * SR))
        seg = a[s0:s0 + n].copy()
        if len(seg) < n:
            seg = np.concatenate([seg, np.zeros((n - len(seg), 2))])
        if hp: seg = filt(seg.T, 'high', hp).T
        if lp: seg = filt(seg.T, 'low', lp).T
        r = np.ones(n); k1 = int(ini * SR); k2 = int(fin * SR)
        if k1: r[:k1] = np.linspace(0, 1, k1)
        if k2: r[-k2:] = np.minimum(r[-k2:], np.linspace(1, 0, k2))
        self.put(pista, seg * r[:, None] * db(g_db), t0)
        self.log(t0, f'audio real {etiqueta or Path(path).name} fuente {src0:.2f}–{src0 + t1 - t0:.2f} s, {g_db:+.1f} dB')

    def toma(self, toma, src0, t0, t1, g_db=0.0, **kw):
        """ambiente real de una toma propia (ORIGINALES/<toma>.mov)"""
        self.real(f'{S.O}/{toma}.mov', src0, t0, t1, g_db, etiqueta=toma, **kw)

    def clang(self, t, g=0.5):
        """golpe metálico de travesaño: parciales inarmónicos de un tubo + golpe grave"""
        L = int(1.6 * SR); tt = np.arange(L) / SR
        s = np.zeros(L)
        for f, a, d in ((523, 1.0, 0.9), (1437, 0.7, 0.6), (2817, 0.45, 0.4), (4655, 0.3, 0.25), (6950, 0.18, 0.15)):
            s += a * np.sin(2 * np.pi * f * tt * (1 + 0.002 * np.sin(2 * np.pi * 5 * tt))) * np.exp(-tt / d)
        s += 0.8 * np.sin(2 * np.pi * (70 + 60 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.12)
        s += 0.5 * filt(ruido(L), 'high', 2000) * np.exp(-tt / 0.004)
        s = satur(s / np.abs(s).max(), 1.3)
        self.put('fx', s, t, g); self.rev(s * g * 0.35, t, seg=1.8)
        self.log(t, 'clang (travesaño)')

    def silbato(self, t, dur=0.55, g=0.22):
        """pitazo: tono de 3,1 kHz con trino (bolita) y soplido"""
        L = int(dur * SR); tt = np.arange(L) / SR
        f = 3100 + 180 * np.sign(np.sin(2 * np.pi * 28 * tt)) * 0.5
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / SR)
        s = s * (0.7 + 0.3 * np.sin(2 * np.pi * 28 * tt)) + 0.15 * filt(ruido(L), 'band', [2000, 6000])
        e = np.minimum(1, tt / 0.015) * np.minimum(1, (tt[-1] - tt) / 0.04)
        self.put('fx', s * e / np.abs(s * e).max(), t, g); self.rev(s * e * g * 0.25, t, seg=1.4)
        self.log(t, 'silbato')

    def latido(self, t, g=0.6):
        for dt, a in ((0, 1.0), (0.17, 0.7)):
            L = int(0.25 * SR); tt = np.arange(L) / SR
            s = np.sin(2 * np.pi * (48 + 30 * np.exp(-tt / 0.02)) * tt) * np.exp(-tt / 0.07)
            self.put('bombo', satur(s, 2.0) * a, t + dt, g)
        self.log(t, 'latido')

    def golpe_sordo(self, t, g=0.6):
        """«No.»: golpe grave que cae (bombo largo + ruido grave)"""
        self.bombo(t, g, f0=90, f1=34, dec=0.6)
        L = int(0.5 * SR); tt = np.arange(L) / SR
        self.put('fx', filt(ruido(L), 'low', 400) * np.exp(-tt / 0.12), t, g * 0.5)
        self.log(t, 'golpe sordo')


# ---------------- textos y armado ----------------
FS_HOOK, BORDE_HOOK = 120, 33          # mayúscula ≈ 72 px (medido en VIR-01 v02)
V.ESTILOS.update({
    'CajaN_hook': ('Inter Display SemiBold', FS_HOOK, '&H00FFFFFF', '&H00141414', '&H00141414', 0, BORDE_HOOK, 0, 3, 8, 0),
    'CajaN_125': ('Inter Display SemiBold', 72, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 20, 0, 3, 8, 0),
    'CajaN_ctx': ('Inter Display SemiBold', 54, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 15, 0, 3, 8, 0),
    'CajaN_link': ('Inter Display SemiBold', 50, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 14, 0, 3, 8, 0),
    # golpe: palabra enorme blanca con contorno negro (GOL., NO., 2-0.)
    'Golpe': ('Inter Display ExtraBold', 210, '&H00FFFFFF', '&H00000000', '&H80000000', 0, 9, 0, 1, 5, 0),
    # sello rojo (ANULADO., NO.)
    'Sello': ('Inter Display ExtraBold', 150, '&H002B2BE0', '&H00FFFFFF', '&H00000000', 0, 7, 0, 1, 5, 0),
    'Celeste': ('Inter Display ExtraBold', 96, '&H00DEB27E', '&H00141414', '&H00141414', 0, 26, 0, 3, 8, 0),
})
Y_HOOK = 259


def armar(planos, salida):
    return V.unir(planos, salida)


def congelar(src, n_desde, n, salida, por_cuadro=None):
    """n cuadros congelados del cuadro n_desde de src (1080x1920), con efecto por cuadro opcional"""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(src), '-vf', f"select='eq(n\\,{n_desde})'", '-frames:v', '1',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    f = Image.fromarray(np.frombuffer(raw, np.uint8).reshape(H, W, 3))
    enc = encoder(salida)
    for k in range(n):
        g = por_cuadro(k, f) if por_cuadro else f
        enc.stdin.write(np.asarray(g, np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    return dict(cuadros=n, salida=str(salida), congelado_de=f'{src}#{n_desde}')


def destenir(f, k=1.0, rojo=0.0):
    """desatura (k=1 gris) y tiñe de rojo"""
    a = np.asarray(f, np.float32); g = a @ np.array([0.299, 0.587, 0.114], np.float32)
    b = a * (1 - k) + g[..., None] * k
    if rojo:
        b = b * (1 - rojo) + (g[..., None] * np.array([1.15, 0.35, 0.35])) * rojo
    return Image.fromarray(b.clip(0, 255).astype(np.uint8))


_SOMBRAS = {}


def sombra(f, cx, cy, rx=430, ry=190, k=0.5):
    """oscurece suave una elipse centrada en (cx, cy): apoyo para texto blanco sobre espuma o cielo"""
    clave = (cx, cy, rx, ry, k)
    if clave not in _SOMBRAS:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        _SOMBRAS[clave] = (1 - k * np.exp(-1.3 * d))[..., None]
    return Image.fromarray((np.asarray(f, np.float32) * _SOMBRAS[clave]).clip(0, 255).astype(np.uint8))


def flash(f, a):
    x = np.asarray(f, np.float32)
    return Image.fromarray((x + (255 - x) * a).clip(0, 255).astype(np.uint8))


# ---------------- tamaño de caja según el ancho del texto ----------------
from PIL import ImageFont
_FUENTE_SB = '/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf'
V.ESTILOS.update({
    'CajaN_96': ('Inter Display SemiBold', 96, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 26, 0, 3, 8, 0),
    'CajaN_84': ('Inter Display SemiBold', 84, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 23, 0, 3, 8, 0),
    'CajaN_108': ('Inter Display SemiBold', 108, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 30, 0, 3, 8, 0),
    'SelloG': ('Inter Display ExtraBold', 250, '&H002B2BE0', '&H00FFFFFF', '&H00000000', 0, 10, 0, 1, 5, 0),
})
_TAM = (('CajaN_hook', 120, 33), ('CajaN_96', 96, 26), ('CajaN_84', 84, 23), ('CajaN_125', 72, 20))


def caja(txt, maximo='CajaN_hook', ancho_max=1000):
    """estilo de caja más grande (hasta `maximo`) cuyo renglón más largo + bordes entra en ancho_max px"""
    empezar = [n for n, _, _ in _TAM].index(maximo)
    for nombre, fs, borde in _TAM[empezar:]:
        f = ImageFont.truetype(_FUENTE_SB, fs)
        w = max(f.getlength(r) for r in txt.split('\\N')) + 2 * borde
        if w <= ancho_max:
            return nombre
    return 'CajaN_125'


# ---------------- transiciones sobre el montaje (barrido, golpe de zoom, destello) ----------------
def _desenfoque_h(a, L):
    """desenfoque de movimiento horizontal (caja de L px) sobre un arreglo HxWx3"""
    if L < 2:
        return a
    r = L // 2
    p = np.pad(a.astype(np.float64), ((0, 0), (r + 1, r), (0, 0)), mode='edge')
    c = np.cumsum(p, axis=1)
    return (c[:, 2 * r + 1:] - c[:, :-(2 * r + 1)]) / (2 * r + 1)


_AVANCE = (0.05, 0.18, 0.40, 0.60, 0.82, 0.95)      # fracción del ancho recorrida en c-3 … c+2
_ESTELA = (60, 200, 420, 420, 200, 60)              # largo del desenfoque de movimiento, px


def transiciones(src, dst, cortes, n_total):
    """cortes: {cuadro_del_corte: 'barrido' | 'barrido_izq' | 'zoom' | 'destello' | 'zoom+destello'}.
    barrido: paneo de látigo de 6 cuadros (3 antes y 3 después del corte): el plano que sale y el que entra se
    desplazan juntos, pegados, con desenfoque de movimiento horizontal (sin bandas ni cuadros estirados);
    zoom: el plano nuevo entra ampliado (1,16 → 1,0 en 4 cuadros); destello: blanco que decae en 4 cuadros."""
    nb = W * H * 3
    plan = {}
    barr = {}
    for c, tipo in cortes.items():
        for parte in tipo.split('+'):
            if parte.startswith('barrido'):
                sg = -1 if parte.endswith('izq') else 1
                barr[c] = sg
                for i in range(6):
                    plan.setdefault(c - 3 + i, []).append(('push', c, sg, _AVANCE[i], _ESTELA[i]))
            elif parte == 'zoom':
                for i, z in enumerate((1.16, 1.09, 1.04, 1.015)):
                    plan.setdefault(c + i, []).append(('zoom', z))
            elif parte == 'destello':
                for i, a in enumerate((0.7, 0.42, 0.2, 0.08)):
                    plan.setdefault(c + i, []).append(('dest', a))
    refs = {}
    if barr:       # último cuadro del plano que sale (c-1) y primero del que entra (c)
        need = sorted({c - 1 for c in barr} | set(barr))
        sel = '+'.join(f'eq(n\\,{k})' for k in need)
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(src), '-vf', f"select='{sel}'", '-vsync', '0',
                              '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
        assert len(raw) == nb * len(need), (len(raw), len(need))
        for i, k in enumerate(need):
            refs[k] = np.frombuffer(raw[i * nb:(i + 1) * nb], np.uint8).reshape(H, W, 3)
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(src), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = encoder(dst)
    k = 0
    while True:
        b = dec.stdout.read(nb)
        if len(b) < nb:
            break
        if k in plan:
            im = Image.frombuffer('RGB', (W, H), b, 'raw', 'RGB', 0, 1)
            for op in plan[k]:
                if op[0] == 'push':
                    _, c, sg, p, L = op
                    cur = np.asarray(im)
                    A = cur if k < c else refs[c - 1]
                    B = refs[c] if k < c else cur
                    d = int(round(p * W))
                    if sg > 0:       # el plano viejo sale por la izquierda, el nuevo entra por la derecha
                        v = np.concatenate([A, B], axis=1)[:, d:d + W]
                    else:
                        v = np.concatenate([B, A], axis=1)[:, W - d:2 * W - d]
                    im = Image.fromarray(_desenfoque_h(v, L).clip(0, 255).astype(np.uint8))
                elif op[0] == 'zoom':
                    z = op[1]; w = W / z; h = H / z
                    im = im.resize((W, H), Image.BICUBIC, box=((W - w) / 2, (H - h) / 2, (W + w) / 2, (H + h) / 2))
                elif op[0] == 'dest':
                    im = flash(im, op[1])
            b = np.asarray(im, np.uint8).tobytes()
        enc.stdin.write(b); k += 1
    dec.stdout.close(); dec.wait(); enc.stdin.close(); enc.wait()
    assert k == n_total, (k, n_total)
    return dict(transiciones=cortes, salida=str(dst))
