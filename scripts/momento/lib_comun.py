#!/usr/bin/env python3
"""MARCA_momento · LIB-1 y LIB-2 · herramientas comunes (Pedro, 25/11/2026).

Imagen: planos de los clips de @libertadores (clips/tt, fuera de git) con conversión exacta de cuadros:
  '1:1'      fuente de 30 o 29,97: cuadro por cuadro, mismo tiempo
  'cuadro'   fuente de 23,976 cuadro a cuadro a 30 (acelera 1,25 ×)
  'real'     fuente de 23,976 a velocidad real con fps=30 (repite 1 de cada 4 cuadros); se usa con la voz de Muslera
  'descarte' fuente de 59,94: uno de cada dos cuadros (velocidad real)
Tomas propias (ORIGINALES/IMG_*) con scripts/fmt/video.py (cadena de color aprobada).
Texto: capas RGBA de scripts/marca/comun.py (caja, placa) rasterizadas por cuadro: una PNG por cuadro del máster.
Sonido: numpy a 48 kHz estéreo; música TEMP original sintetizada acá (sin material de terceros); golpes grave/seco.
Máster: H.264 High 4.0 yuv420p BT.709 rango limitado, 30 fps, AAC-LC 48 kHz estéreo, faststart, sin metadatos.
"""
import json, math, os, subprocess, sys, shutil, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/marca')
import video as V      # noqa: E402
import comun as C      # noqa: E402

R = Path('/home/user/1')
CLIPS = R / 'TRABAJO/momento/clips/tt'
W, H, FPS, SR = 1080, 1920, 30, 48000
TT = {'T1': '7699689076894518535', 'T2': '7699720550272339221', 'T3': '7699707634881973512',
      'T4': '7699692272857681173', 'T6': '7700024221778382100', 'T7': '7699694551849504007',
      'T8': '7700704056871816469', 'T10': '7699681462412446977', 'T13': '7704348186437029140'}
FPS_SRC = {'T1': 24000 / 1001, 'T2': 24000 / 1001, 'T3': 24000 / 1001, 'T4': 30.0, 'T6': 30000 / 1001,
           'T7': 24000 / 1001, 'T8': 30.0, 'T10': 24000 / 1001, 'T13': 60000 / 1001}
ENC_INT = V.ENC_INT
# IMG_7896 viene en rango completo (yuvj420p, color_range=pc según ffprobe): pasa a limitado. IMG_7895 ya es tv.
V.TOMAS['IMG_7896']['full'] = True


def sh(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True)
    if r.returncode:
        raise RuntimeError(' '.join(map(str, cmd))[:400] + '\n' + r.stderr.decode()[-2500:])
    return r.stdout


def clip(t):
    return CLIPS / f'tt_{TT[t]}.mp4'


def nframes(mp4):
    return int(sh(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                   'stream=nb_read_frames', '-of', 'csv=p=0', mp4]).decode().strip())


# ---------------------------------------------------------------------------------------------- imagen
def plano_tt(t, modo, t0, n, salida, post=None):
    """n cuadros de salida a 30 fps desde el segundo t0 del clip t. Devuelve la ficha del plano."""
    f = FPS_SRC[t]
    if modo in ('1:1', 'cuadro'):
        s = round(t0 * f)
        vf = [f'trim=start_frame={s}:end_frame={s + n}', 'setpts=N/(30*TB)']
        fuente = (s, s + n - 1)
    elif modo == 'descarte':
        s = round(t0 * f)
        vf = [f'trim=start_frame={s}:end_frame={s + 2 * n}', "select='not(mod(n\\,2))'", 'setpts=N/(30*TB)']
        fuente = (s, s + 2 * n - 2)
    elif modo == 'real':
        vf = [f'trim=start={t0:.4f}:end={t0 + n / 30 + 0.2:.4f}', 'setpts=PTS-STARTPTS', 'fps=30']
        fuente = (round(t0 * f), round((t0 + n / 30) * f))
    else:
        raise ValueError(modo)
    vf += ['scale=1080:1920:flags=lanczos', 'setsar=1', 'format=yuv420p']
    if post:
        vf.append(post)
    sh(['ffmpeg', '-v', 'error', '-y', '-i', clip(t), '-an', '-vf', ','.join(vf), '-frames:v', n, '-r', 30,
        *ENC_INT, salida])
    k = nframes(salida)
    if k != n:
        raise RuntimeError(f'{salida}: {k} cuadros, esperaba {n}')
    return dict(clip=t, id=TT[t], modo=modo, t0=t0, t1=round(fuente[1] / f, 3), cuadros_fuente=fuente, cuadros=n,
                salida=str(salida))


def cuadro_tt(t, n_src, png):
    """Un cuadro exacto (número de cuadro de la fuente) a PNG RGB, con matriz BT.709 rango limitado explícita."""
    sh(['ffmpeg', '-v', 'error', '-y', '-i', clip(t), '-vf',
        f"select='eq(n\\,{n_src})',scale=in_color_matrix=bt709:in_range=tv,format=rgb24", '-frames:v', 1,
        '-fps_mode', 'vfr', png])
    return png


def png_a_plano(png, n, salida, zoom=None, post=None):
    """Congelado de una imagen RGB 1080x1920 durante n cuadros (zoom=(z0, z1) empuje centrado con zoompan)."""
    vf = []
    if zoom:
        z0, z1 = zoom
        vf += ['scale=2160:3840:flags=lanczos',
               f"zoompan=z='{z0}+({z1}-{z0})*on/{max(1, n - 1)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps=30"]
    vf += ['scale=out_color_matrix=bt709:out_range=tv', 'format=yuv420p', 'setsar=1']
    if post:
        vf.append(post)
    sh(['ffmpeg', '-v', 'error', '-y', '-loop', 1, '-framerate', 30, '-i', png, '-vf', ','.join(vf), '-frames:v', n,
        '-r', 30, *ENC_INT, salida])
    return dict(png=str(png), cuadros=n, salida=str(salida), zoom=zoom)


def foco_placa(png_in, png_out, caja, marca, sigma=14, oscuro=0.50, pluma=14):
    """Deja nítida solo `caja` (x0,y0,x1,y1): el resto se desenfoca y oscurece para que no se lea ningún otro año.
    `marca` (x0,y0,x1,y1) = marca de agua CONMEBOL, que vuelve nítida e intacta encima."""
    im = Image.open(png_in).convert('RGB')
    bl = im.filter(ImageFilter.GaussianBlur(sigma))
    bl = Image.eval(bl, lambda v: int(v * oscuro))
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle(caja, radius=10, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(pluma / 2))
    out = Image.composite(im, bl, m)
    # marca de agua: solo sus letras (píxeles claros del recorte, dilatados y con borde suave) vuelven nítidas;
    # el fondo del recorte queda desenfocado como el resto (sin «calcomanía» rectangular)
    mm = mascara_marca(marca)
    out.paste(im.crop(marca), marca[:2], mm)
    out.save(png_out)
    return png_out


def mascara_marca(marca, t='T13', cada=60, hasta_s=43.0):
    """Máscara de la marca de agua CONMEBOL: mínimo temporal de la zona en un cuadro de cada `cada` (la marca es lo
    único que queda claro en todos los cuadros). Rampa 50→120 de gris, dilatada 1 px."""
    x0, y0, x1, y1 = marca
    raw = sh(['ffmpeg', '-v', 'error', '-i', clip(t), '-vf',
              f"select='not(mod(n\\,{cada}))',crop={x1 - x0}:{y1 - y0}:{x0}:{y0},format=gray", '-fps_mode', 'vfr',
              '-f', 'rawvideo', '-'])
    a = np.frombuffer(raw, np.uint8).reshape(-1, y1 - y0, x1 - x0)
    k = int(hasta_s * FPS_SRC[t] / cada)
    mn = a[:k].min(0).astype(np.float32)
    m = np.clip((mn - 50) / 70, 0, 1)
    return Image.fromarray((m * 255).astype('uint8')).filter(ImageFilter.MaxFilter(3))


def unir(planos, salida):
    lst = Path(str(salida) + '.txt')
    lst.write_text(''.join(f"file '{Path(p['salida']).resolve()}'\n" for p in planos))
    sh(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', 0, '-i', lst, '-c', 'copy', salida])
    n = nframes(salida); esp = sum(p['cuadros'] for p in planos)
    if n != esp:
        raise RuntimeError(f'unir: {n} != {esp}')
    return n


# ---------------------------------------------------------------------------------------------- texto
def _ancho(texto, peso, size):
    f = C.fuente(peso, size)
    return max(f.getlength(r) for r in texto.split('\n'))


def envolver(texto, peso, size, maxw):
    """Parte cada renglón en el espacio más cercano al medio si no entra en maxw (no cambia palabras ni signos)."""
    out = []
    pend = texto.split('\n')
    while pend:
        r = pend.pop(0)
        if C.fuente(peso, size).getlength(r) <= maxw or ' ' not in r:
            out.append(r); continue
        esp = [i for i, ch in enumerate(r) if ch == ' ']
        i = min(esp, key=lambda k: abs(k - len(r) / 2))
        pend[0:0] = [r[:i], r[i + 1:]]
    return '\n'.join(out)


def ajustar(texto, peso, smax, smin, maxw, pad=0):
    """Mayor tamaño entre smax y smin que entra en maxw; si ni smin entra, envuelve a smin."""
    for s in range(smax, smin - 1, -2):
        if _ancho(texto, peso, s) + 2 * pad <= maxw:
            return texto, s
    return envolver(texto, peso, smin, maxw - 2 * pad), smin


def caja_fit(texto, smax=76, smin=64, maxw=980, tema='blanca', peso='semibold'):
    t, s = ajustar(texto, peso, smax, smin, maxw, pad=30)
    return C.caja(t, s, tema=tema, peso=peso)


def placa_fit(texto, smax=96, smin=76, maxw=980):
    t, s = ajustar(texto, 'extrabold', smax, smin, maxw)
    return C.placa(t, s)


def dato(texto, maxw=880):
    """Dato chico: caja negra SemiBold 50 (condición 4 del 09)."""
    t, s = ajustar(texto, 'semibold', 50, 50, maxw, pad=30)
    return C.caja(t, 50, tema='negra', peso='semibold')


def capa(img, f0, f1, y, cx=W // 2, x=None, pop=False, nombre=''):
    """f1 exclusivo. y = borde superior (a escala 1). cx = centro horizontal."""
    x0 = x if x is not None else round(cx - img.width / 2)
    return dict(img=img, f0=f0, f1=f1, x0=int(x0), y0=int(y), pop=pop, nombre=nombre,
                caja=(int(x0), int(y), int(x0 + img.width), int(y + img.height)))


def rotulo(img, f0, f1, y, cx, punta, pop=True, nombre=''):
    """Caja + raya desde el borde inferior de la caja hasta `punta` (x, y) sobre la remera, con un punto."""
    x0 = round(cx - img.width / 2)
    base = (cx, y + img.height)
    xs = [x0, punta[0] - 8, base[0]]; ys = [y, punta[1] - 8]
    X0, Y0 = min(xs + [punta[0] - 8]), y
    X1 = max(x0 + img.width, punta[0] + 8); Y1 = max(y + img.height, punta[1] + 8)
    L = Image.new('RGBA', (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    for wdt, col in ((7, (20, 20, 20, 150)), (4, (255, 255, 255, 255))):
        d.line([(base[0] - X0, base[1] - Y0 - 2), (punta[0] - X0, punta[1] - Y0)], fill=col, width=wdt)
    d.ellipse([punta[0] - X0 - 8, punta[1] - Y0 - 8, punta[0] - X0 + 8, punta[1] - Y0 + 8], fill=(255, 255, 255, 255),
              outline=(20, 20, 20, 200), width=2)
    L.alpha_composite(img, (x0 - X0, 0))
    return dict(img=L, f0=f0, f1=f1, x0=X0, y0=Y0, pop=pop, nombre=nombre, caja=(x0, y, x0 + img.width, y + img.height),
                punta=punta)


ESCALAS_POP = [1.18, 1.09]


def rasterizar(capas, nf, carpeta):
    """Una PNG RGBA por cuadro (carpeta/c%04d.png). Estados repetidos se enlazan (mismo archivo)."""
    carpeta = Path(carpeta)
    if carpeta.exists():
        shutil.rmtree(carpeta)
    carpeta.mkdir(parents=True)
    prev_key, prev_path = None, None
    for f in range(nf):
        act = []
        for i, c in enumerate(capas):
            if c['f0'] <= f < c['f1']:
                k = f - c['f0']
                e = ESCALAS_POP[k] if (c['pop'] and k < len(ESCALAS_POP)) else 1.0
                act.append((i, e))
        key = tuple(act)
        p = carpeta / f'c{f:04d}.png'
        if key == prev_key:
            os.link(prev_path, p); continue
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        for i, e in act:
            c = capas[i]; im = c['img']
            if e != 1.0:
                im2 = im.resize((round(im.width * e), round(im.height * e)), Image.LANCZOS)
                x = round(c['x0'] + im.width / 2 - im2.width / 2); y = round(c['y0'] + im.height / 2 - im2.height / 2)
            else:
                im2, x, y = im, c['x0'], c['y0']
            L.alpha_composite(im2, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))
        L.save(p, compress_level=1)
        prev_key, prev_path = key, p
    return carpeta


def master(video, wav, capas_dir, salida):
    """Imagen + capa de texto (una PNG por cuadro) + audio. Mismos parámetros de codificación que fmt/video.master."""
    sh(['ffmpeg', '-v', 'error', '-y', '-i', video, '-i', wav, '-framerate', 30, '-i', Path(capas_dir) / 'c%04d.png',
        '-filter_complex', '[0:v]setsar=1[b];[b][2:v]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[v]',
        '-map', '[v]', '-map', '1:a:0',
        '-c:v', 'libx264', '-profile:v', 'high', '-level:v', '4.0', '-preset', 'slow', '-crf', '17',
        '-maxrate', '20M', '-bufsize', '25M', '-pix_fmt', 'yuv420p', '-r', 30, '-g', 30,
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
        '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', SR, '-ac', 2,
        '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
        '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
        '-shortest', '-movflags', '+faststart', salida])
    return salida


# ---------------------------------------------------------------------------------------------- sonido
def leer_audio(src, t0, dur, tempo=1.0):
    """Audio estéreo 48 kHz de src desde t0. tempo > 1 acelera sin cambiar el tono (atempo), para los planos
    cuadro a cuadro (así el sonido de la jugada queda en sincronía con la imagen acelerada)."""
    af = f'atempo={tempo:.6f}' if abs(tempo - 1) > 1e-6 else 'anull'
    raw = sh(['ffmpeg', '-v', 'error', '-ss', f'{t0:.4f}', '-t', f'{dur * tempo + 0.3:.4f}', '-i', src, '-vn', '-af', af,
              '-ac', 2, '-ar', SR, '-f', 'f32le', '-'])
    a = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    n = int(round(dur * SR))
    if len(a) < n:
        a = np.vstack([a, np.zeros((n - len(a), 2), np.float32)])
    return a[:n]


def rms_db(a):
    return 20 * np.log10(np.sqrt((a.astype(np.float64) ** 2).mean()) + 1e-12)


def fades(a, fi=0.008, fo=0.008):
    a = a.copy(); ni, no = int(fi * SR), int(fo * SR)
    if ni:
        a[:ni] *= np.linspace(0, 1, ni)[:, None]
    if no:
        a[-no:] *= np.linspace(1, 0, no)[:, None]
    return a


def put(buf, sig, t0, g=1.0):
    i = int(round(t0 * SR))
    if sig.ndim == 1:
        sig = np.stack([sig, sig], 1)
    j = min(len(buf), i + len(sig))
    if j > max(0, i):
        buf[max(0, i):j] += g * sig[max(0, -i):j - i]


_rng = np.random.default_rng(7)


def lp(x, fc):
    """pasa bajos de un polo (vectorizado por bloques con lfilter equivalente)."""
    a = math.exp(-2 * math.pi * fc / SR)
    y = np.empty_like(x); s = 0.0
    # implementación por recursión en numpy puro es lenta: se usa scipy si está
    try:
        from scipy.signal import lfilter
        return lfilter([1 - a], [1, -a], x).astype(np.float32)
    except Exception:
        for k in range(len(x)):
            s = (1 - a) * x[k] + a * s; y[k] = s
        return y


def hp(x, fc):
    return (x - lp(x, fc)).astype(np.float32)


def grave(db=-8.0, dec=0.32):
    """Golpe GRAVE (a favor): bombo profundo con sub y un ataque corto."""
    L = int(0.9 * SR); t = np.arange(L) / SR
    f = 42 + (120 - 42) * np.exp(-t / 0.045)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dec)
    s += 0.35 * np.sin(2 * np.pi * 38 * t) * np.exp(-t / (dec * 1.4))
    s += 0.18 * lp(_rng.standard_normal(L).astype(np.float32), 1800) * np.exp(-t / 0.012)
    s *= np.minimum(1, t / 0.0015)
    return (s / np.abs(s).max() * 10 ** (db / 20)).astype(np.float32)


def seco(db=-10.0):
    """Golpe SECO (en contra): clic metálico corto (ruido agudo + resonancias de 2,4 y 3,7 kHz)."""
    L = int(0.25 * SR); t = np.arange(L) / SR
    n = hp(_rng.standard_normal(L).astype(np.float32), 2500) * np.exp(-t / 0.006)
    r = (np.sin(2 * np.pi * 2400 * t) + 0.6 * np.sin(2 * np.pi * 3710 * t)) * np.exp(-t / 0.035)
    lo = np.sin(2 * np.pi * (180 + 300 * np.exp(-t / 0.01)) * t) * np.exp(-t / 0.03)
    s = 0.9 * n + 0.45 * r + 0.5 * lo
    s *= np.minimum(1, t / 0.0005)
    return (s / np.abs(s).max() * 10 ** (db / 20)).astype(np.float32)


def subida(dur, db=-16.0):
    L = int(dur * SR); t = np.arange(L) / SR
    n = _rng.standard_normal(L).astype(np.float32)
    x = lp(n, 900) * 0.6 + hp(n, 3000) * 0.4
    s = x * (t / dur) ** 2
    return (s / (np.abs(s).max() + 1e-9) * 10 ** (db / 20)).astype(np.float32)


def aire(dur, db=-42.0):
    """Aire de estadio vacío: ruido marrón filtrado, estéreo descorrelacionado."""
    L = int(dur * SR)
    ch = []
    for _ in range(2):
        b = np.cumsum(_rng.standard_normal(L)).astype(np.float32)
        b = hp(b, 60); b = lp(b, 1400)
        b = b / (np.sqrt((b ** 2).mean()) + 1e-9) * 10 ** (db / 20)
        ch.append(b)
    return np.stack(ch, 1).astype(np.float32)


def roce(dur, db=-24.0):
    """Roce de dedos sobre tela (foley sintetizado)."""
    L = int(dur * SR); t = np.arange(L) / SR
    n = _rng.standard_normal(L).astype(np.float32)
    x = lp(hp(n, 1200), 6000)
    e = 0.5 - 0.5 * np.cos(2 * np.pi * np.minimum(t / dur, 1))
    s = x * e * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * t))
    return (s / (np.sqrt((s ** 2).mean()) + 1e-9) * 10 ** (db / 20)).astype(np.float32)


# --- música TEMP original (pulso grave ≈ 100 lpm, bajo, pad oscuro, hats) ---
BPM = 100.0
BEAT = 60.0 / BPM


def _kick(g=1.0):
    L = int(0.42 * SR); t = np.arange(L) / SR
    f = 46 + (105 - 46) * np.exp(-t / 0.04)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22) * np.minimum(1, t / 0.002)
    return (g * s).astype(np.float32)


def _hat(g=1.0):
    L = int(0.06 * SR); t = np.arange(L) / SR
    return (g * hp(_rng.standard_normal(L).astype(np.float32), 7000) * np.exp(-t / 0.015)).astype(np.float32)


def _clap(g=1.0):
    L = int(0.25 * SR); t = np.arange(L) / SR
    n = lp(hp(_rng.standard_normal(L).astype(np.float32), 900), 5000)
    e = np.exp(-t / 0.05) * (1 + 0.6 * (np.sin(2 * np.pi * 90 * t) > 0) * (t < 0.03))
    return (g * n * e).astype(np.float32)


def _saw(f, L):
    t = np.arange(L) / SR
    return (2 * ((f * t) % 1.0) - 1).astype(np.float32)


def _pad(notas, L, brillo=900):
    x = sum(_saw(f * d, L) for f in notas for d in (0.997, 1.003)) / (2 * len(notas))
    x = lp(lp(x, brillo), brillo)
    t = np.arange(L) / SR
    a = np.minimum(1, t / 0.25) * np.minimum(1, (L / SR - t) / 0.25)
    return (x * a).astype(np.float32)


def _bajo(f, L, g=1.0):
    t = np.arange(L) / SR
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    e = np.minimum(1, t / 0.01) * np.exp(-t / 0.5)
    return (g * s * e).astype(np.float32)


A1, F1, C2, G1 = 55.0, 43.65, 65.41, 49.0
ACORDES = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (196.0, 246.94, 293.66), (164.81, 196.0, 246.94)]
BAJOS = [A1, F1, G1, 41.2]


def musica(dur, tramos, sr=SR):
    """tramos: lista de (t0, t1, modo) con modo en {'pulso', 'pleno', 'lento', 'silencio'}.
    pulso = bombo en cada tiempo + bajo + pad bajo · pleno = + hats, palmas en 2 y 4, pad más brillante
    lento = bombo cada dos tiempos, pad muy bajo · silencio = nada. La grilla nace en t=0."""
    N = int(dur * sr); m = np.zeros((N, 2), np.float32)
    nb = int(dur / BEAT) + 1
    for b in range(nb):
        t = b * BEAT
        modo = next((md for (a, z, md) in tramos if a <= t < z), 'silencio')
        if modo == 'silencio':
            continue
        compas = (b // 4) % 4
        if modo in ('pulso', 'pleno') or (modo == 'lento' and b % 2 == 0):
            put(m, _kick(0.9 if modo != 'lento' else 0.55), t)
        if modo in ('pulso', 'pleno') and b % 4 == 0:
            put(m, _bajo(BAJOS[compas], int(4 * BEAT * sr), 0.55), t)
        if modo == 'pleno':
            put(m, _hat(0.18), t + BEAT / 2)
            if b % 2 == 1:
                put(m, _clap(0.35), t)
        if b % 4 == 0 and modo in ('pulso', 'pleno', 'lento'):
            g = {'pulso': 0.10, 'pleno': 0.16, 'lento': 0.05}[modo]
            br = {'pulso': 700, 'pleno': 1500, 'lento': 500}[modo]
            pd = _pad(ACORDES[compas], int(4 * BEAT * sr), br) * g
            put(m, np.stack([pd, np.roll(pd, 240)], 1), t)
    # cortes exactos a silencio en los tramos 'silencio' (las colas no cruzan el hueco)
    for (a, z, md) in tramos:
        if md == 'silencio':
            i, j = int(a * sr), int(z * sr)
            m[i:j] = 0
            k = min(int(0.006 * sr), i)
            if k:
                m[i - k:i] *= np.linspace(1, 0, k)[:, None]
    return m


def envolvente_duck(N, zonas, db=-12.0, rampa=0.06):
    """Ganancia por muestra: baja `db` en las zonas (t0, t1) con rampas (ducking de la música bajo la voz)."""
    g = np.ones(N, np.float32); r = int(rampa * SR); low = 10 ** (db / 20)
    for (a, z) in zonas:
        i, j = int(a * SR), int(z * SR)
        g[i:j] = np.minimum(g[i:j], low)
        if r:
            i0 = max(0, i - r); g[i0:i] = np.minimum(g[i0:i], np.linspace(1, low, i - i0))
            j1 = min(N, j + r); g[j:j1] = np.minimum(g[j:j1], np.linspace(low, 1, j1 - j))
    return g


def escribir_wav(a, f):
    a = np.clip(a, -1, 1)
    sh_in = (a * 32767).astype('<i2').tobytes()
    import wave
    with wave.open(str(f), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(sh_in)
    return f


def ebur(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-vn', '-af', 'ebur128=peak=true:framelog=quiet', '-f',
                        'null', '-'], capture_output=True, text=True).stderr
    g = lambda k: float([l for l in r.splitlines() if l.strip().startswith(k)][-1].split()[1])
    return dict(lufs_integrado=g('I:'), lra=g('LRA:'), pico_dbtp=g('Peak:'))


def a_menos14(a, tmp, objetivo=-14.0, techo_dbtp=-1.6):
    """Ganancia a ≈ −14 LUFS + limitador de picos (alimiter level=false) y control con ebur128. Devuelve (a, medida)."""
    tmp = Path(tmp); tmp.parent.mkdir(parents=True, exist_ok=True)
    g_db = 0.0
    for it in range(4):
        b = a * 10 ** (g_db / 20)
        escribir_wav_f32(b, tmp.with_suffix('.pre.wav'))
        lim = 10 ** (techo_dbtp / 20)
        sh(['ffmpeg', '-v', 'error', '-y', '-i', tmp.with_suffix('.pre.wav'), '-af',
            f'alimiter=limit={lim:.4f}:attack=3:release=60:level=false:asc=1', '-c:a', 'pcm_f32le', tmp])
        m = ebur(tmp)
        if abs(m['lufs_integrado'] - objetivo) <= 0.3 and m['pico_dbtp'] <= -1.0:
            break
        g_db += objetivo - m['lufs_integrado']
    raw = sh(['ffmpeg', '-v', 'error', '-i', tmp, '-f', 'f32le', '-ac', 2, '-ar', SR, '-'])
    out = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    return out[:len(a)], m, g_db


def escribir_wav_f32(a, f):
    sh_in = np.ascontiguousarray(a.astype('<f4'))
    p = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a',
                        'pcm_f32le', str(f)], input=sh_in.tobytes(), capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode()[-1500:])
    return f


# ---------------------------------------------------------------------------------------------- control
def md5_stream(mp4, sel):
    out = sh(['ffmpeg', '-v', 'error', '-i', mp4, '-map', f'0:{sel}', '-c', 'copy', '-f', 'md5', '-']).decode()
    return out.strip().split('=')[-1]


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def ficha(mp4):
    j = json.loads(sh(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', mp4]))
    v = next(s for s in j['streams'] if s['codec_type'] == 'video'); a = next(s for s in j['streams'] if s['codec_type'] == 'audio')
    return dict(video=dict(codec=v['codec_name'], perfil=v.get('profile'), nivel=v.get('level'), w=v['width'], h=v['height'],
                           fps=v['r_frame_rate'], pix=v['pix_fmt'], espacio=v.get('color_space'), trc=v.get('color_transfer'),
                           primarios=v.get('color_primaries'), rango=v.get('color_range'), cuadros=v.get('nb_frames'),
                           dur=v.get('duration')),
                audio=dict(codec=a['codec_name'], perfil=a.get('profile'), sr=a['sample_rate'], canales=a['channels'],
                           dur=a.get('duration')),
                formato=dict(dur=j['format']['duration'], bytes=j['format']['size'], tags=j['format'].get('tags', {})))


def decodifica(mp4):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-f', 'null', '-'], capture_output=True, text=True)
    return r.stderr.strip() == '', r.stderr.strip()[:500]


def faststart(mp4):
    with open(mp4, 'rb') as f:
        data = f.read(1 << 16)
    i_moov, i_mdat = data.find(b'moov'), data.find(b'mdat')
    return i_moov != -1 and (i_mdat == -1 or i_moov < i_mdat)


def vista_360(mp4, salida, cuadros, cols=8, rot=None):
    """Cuadros elegidos escalados a 360 px de ancho (tamaño de teléfono), 1:1, con número de cuadro."""
    from PIL import ImageFont
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 18)
    tmp = Path(str(salida) + '_tmp'); tmp.mkdir(parents=True, exist_ok=True)
    sel = '+'.join(f'eq(n\\,{k})' for k in cuadros)
    sh(['ffmpeg', '-v', 'error', '-y', '-i', mp4, '-vf', f"select='{sel}',scale=360:640:flags=area", '-fps_mode', 'vfr',
        '-q:v', 2, tmp / 'x_%04d.jpg'])
    ims = []
    for k, n in enumerate(cuadros):
        im = Image.open(tmp / f'x_{k + 1:04d}.jpg').convert('RGB'); d = ImageDraw.Draw(im)
        lab = f'c{n} {n / 30:.2f}s' + (f' {rot[k]}' if rot else '')
        d.rectangle([0, 620, 8 + fnt.getlength(lab), 640], fill=(0, 0, 0)); d.text((4, 620), lab, font=fnt, fill=(255, 255, 0))
        ims.append(im)
    rows = math.ceil(len(ims) / cols)
    S = Image.new('RGB', (cols * 362, rows * 642), (40, 40, 40))
    for k, im in enumerate(ims):
        S.paste(im, ((k % cols) * 362, (k // cols) * 642))
    S.save(salida, quality=88)
    shutil.rmtree(tmp)
    return salida


def franja(mp4, salida, cuadros, caja, cols=4, escala=1.0):
    """Recorte a resolución completa de la misma zona en varios cuadros del máster (control de carteles y pechos)."""
    from PIL import ImageFont
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 16)
    tmp = Path(str(salida) + '_tmp'); tmp.mkdir(parents=True, exist_ok=True)
    sel = '+'.join(f'eq(n\\,{k})' for k in cuadros)
    x0, y0, x1, y1 = caja
    sh(['ffmpeg', '-v', 'error', '-y', '-i', mp4, '-vf', f"select='{sel}',crop={x1 - x0}:{y1 - y0}:{x0}:{y0}",
        '-fps_mode', 'vfr', '-q:v', 2, tmp / 'x_%04d.png'])
    ims = []
    for k, n in enumerate(cuadros):
        im = Image.open(tmp / f'x_{k + 1:04d}.png').convert('RGB')
        if escala != 1.0:
            im = im.resize((round(im.width * escala), round(im.height * escala)), Image.LANCZOS)
        d = ImageDraw.Draw(im); d.rectangle([0, 0, 70, 18], fill=(0, 0, 0)); d.text((3, 0), f'c{n}', font=fnt, fill=(255, 255, 0))
        ims.append(im)
    rows = math.ceil(len(ims) / cols); iw, ih = ims[0].size
    S = Image.new('RGB', (cols * (iw + 3), rows * (ih + 3)), (40, 40, 40))
    for k, im in enumerate(ims):
        S.paste(im, ((k % cols) * (iw + 3), (k // cols) * (ih + 3)))
    S.save(salida, quality=90)
    shutil.rmtree(tmp)
    return salida
