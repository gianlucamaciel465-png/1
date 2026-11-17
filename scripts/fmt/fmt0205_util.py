#!/usr/bin/env python3
"""FMT-02 y FMT-05 · utilidades propias de Pedro (17/11/2026). No reemplazan video.py / sonido.py: los usan.

- hoja_src: hoja de contacto de un tramo de un ORIGINAL con el número de cuadro de la fuente impreso
  (color y rotación como video.plano).
- cuadro_src: un cuadro de la fuente a tamaño natural (4K rotado) en PNG.
- leer_src / leer_mp4: cuadros RGB reducidos para medir con numpy.
- audio_tramos: RMS por 0,1 s, energía por bandas, planitud espectral y periodicidad de tono (indicador de voz),
  más espectrograma PNG. No es escucha: es medición.
- vel_mezcla: tramo acelerado con mezcla de cuadros (núcleo triangular) en lugar de saltar cuadros (Roma, FMT-05 a).
- md5_streams, ffprobe_json, ebur128, decodifica: control del máster.
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V  # noqa: E402

FPS = 30
FONT = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
PY = '/home/user/1/TRABAJO/venv/bin/python'


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise RuntimeError(f"falló: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r.stdout


def src(toma):
    return str(V._src(toma))


# ---------------- imagen ----------------
def hoja_src(toma, c0, c1, salida, cada=3, ancho=216, cols=10, caja=None, marcas=None):
    """Hoja de la fuente entre los cuadros c0 y c1 (incluidos), uno cada `cada`, con 'cN' de la fuente.
    caja: dibuja un rectángulo (x,y,w,h) en coordenadas naturales. marcas: lista de (y, color) líneas horizontales."""
    nw, nh = V.TOMAS[toma]['nat']
    esc = ancho / nw
    vf = [V.color(toma)]
    vf.append(f'scale={ancho}:-2:flags=area')
    if caja:
        x, y, w, h = caja
        vf.append(f'drawbox=x={x*esc:.0f}:y={y*esc:.0f}:w={w*esc:.0f}:h={h*esc:.0f}:color=red@0.9:t=2')
    for (yy, col) in (marcas or []):
        vf.append(f'drawbox=x=0:y={yy:.0f}:w=iw:h=1:color={col}:t=1')
    vf.append(f"drawtext=fontfile={FONT}:text='{toma[4:]} c%{{n}}':x=3:y=3:fontsize={max(11, ancho // 14)}:"
              f"fontcolor=yellow:box=1:boxcolor=black@0.65")
    vf.append(f"select='between(n\\,{c0}\\,{c1})*not(mod(n-{c0}\\,{cada}))'")
    total = (c1 - c0) // cada + 1
    filas = math.ceil(total / cols)
    vf.append(f'tile={cols}x{filas}:padding=2:color=0x202020')
    run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', src(toma), '-an', '-vf', ','.join(vf),
         '-frames:v', '1', '-fps_mode', 'vfr', str(salida)])
    return salida


def cuadro_src(toma, n, salida, escala=None, caja=None):
    vf = [V.color(toma)]
    vf.append(f"select='eq(n\\,{n})'")
    if caja:
        x, y, w, h = caja
        vf.append(f'crop={w}:{h}:{x}:{y}')
    if escala:
        vf.append(f'scale={escala}:-2:flags=area')
    run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', src(toma), '-an', '-vf', ','.join(vf),
         '-frames:v', '1', '-fps_mode', 'vfr', str(salida)])
    return salida


def leer_src(toma, c0, c1, w, h, caja=None):
    """cuadros c0..c1 (incluidos) de la fuente, RGB uint8, escalados a w×h (después de la caja)."""
    vf = [V.color(toma)]
    if caja:
        x, y, cw, ch = caja
        vf.append(f'crop={cw}:{ch}:{x}:{y}')
    vf += [f"select='between(n\\,{c0}\\,{c1})'", f'scale={w}:{h}:flags=area', 'format=rgb24']
    r = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', src(toma), '-an', '-vf', ','.join(vf),
                        '-fps_mode', 'vfr', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(r, np.uint8).reshape(-1, h, w, 3)


def leer_mp4(path, w=None, h=None, c0=None, c1=None):
    w = w or V.W; h = h or V.H
    vf = []
    if c0 is not None:
        vf.append(f"select='between(n\\,{c0}\\,{c1})'")
    vf += [f'scale={w}:{h}:flags=area', 'format=rgb24']
    r = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(path), '-an', '-vf', ','.join(vf),
                        '-fps_mode', 'vfr', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(r, np.uint8).reshape(-1, h, w, 3)


def leer_yuv(path):
    """cuadros yuv420p crudos de un MP4 1080×1920: lista de (Y, U, V) uint8."""
    r = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(path), '-an', '-f', 'rawvideo',
                        '-pix_fmt', 'yuv420p', '-'], capture_output=True, check=True).stdout
    W_, H_ = V.W, V.H; n = W_ * H_ * 3 // 2
    a = np.frombuffer(r, np.uint8).reshape(-1, n)
    return [(f[:W_ * H_].reshape(H_, W_), f[W_ * H_:W_ * H_ * 5 // 4].reshape(H_ // 2, W_ // 2),
             f[W_ * H_ * 5 // 4:].reshape(H_ // 2, W_ // 2)) for f in a]


def vel_mezcla(toma, desde, hasta, vel, salida, caja=None, z0=1.0, z1=None, cx=None, cy=None, tmp=None):
    """Tramo [desde, hasta) acelerado `vel` veces SIN saltar cuadros de forma irregular (Roma, FMT-05 a): cada cuadro
    de salida k es el promedio ponderado (núcleo triangular de semiancho = vel cuadros) de los cuadros de la fuente
    alrededor de la posición desde*30 + vel*k. Equivale a un obturador de 360° a la velocidad acelerada: el paso se lee
    como movimiento rápido con desenfoque. Primero se hace el tramo a velocidad 1 con video.plano (mismo color y
    encuadre que los demás planos); la mezcla se hace sobre los planos Y, U, V (sin pasar por RGB, así un cuadro con
    peso 1 sale idéntico) y se codifica igual que los intermedios."""
    tmp = tmp or str(salida).replace('.mp4', '_v1.mp4')
    margen = math.ceil(vel)
    d0 = max(0.0, desde - margen / FPS)
    V.plano(toma, d0, hasta + margen / FPS, tmp, caja=caja, z0=z0, z1=z1, cx=cx, cy=cy)
    off = round((desde - d0) * FPS)
    fr = leer_yuv(tmp)
    n_out = round((hasta - desde) * FPS / vel)
    enc = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p',
                            '-s', f'{V.W}x{V.H}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709',
                            '-i', '-', '-frames:v', str(n_out), *V.ENC_INT, str(salida)], stdin=subprocess.PIPE)
    pesos_log = []
    c_src0 = round(desde * FPS)
    for k in range(n_out):
        c = off + vel * k
        lo, hi = math.floor(c - vel) + 1, math.ceil(c + vel) - 1
        idx = [i for i in range(lo, hi + 1) if 0 <= i < len(fr)]
        w = np.array([max(0.0, 1 - abs(i - c) / vel) for i in idx]); w /= w.sum()
        planos = []
        for p in range(3):
            acc = np.zeros(fr[0][p].shape, np.float32)
            for i, wi in zip(idx, w):
                acc += wi * fr[i][p].astype(np.float32)
            planos.append(np.clip(acc + 0.5, 0, 255).astype(np.uint8))
        enc.stdin.write(b''.join(x.tobytes() for x in planos))
        pesos_log.append({'k': k, 'centro_fuente': round(c_src0 + vel * k, 2),
                          'cuadros': [int(i - off + c_src0) for i in idx], 'pesos': [round(float(x), 3) for x in w]})
    enc.stdin.close(); enc.wait()
    if enc.returncode:
        raise RuntimeError('vel_mezcla: falló el codificador')
    Path(str(salida) + '.pesos.json').write_text(json.dumps(pesos_log, indent=0))
    return dict(toma=toma, desde=desde, hasta=hasta, cuadros=n_out, salida=str(salida), caja=caja, z0=z0, z1=z1,
                vel=vel, metodo='mezcla de cuadros, núcleo triangular de semiancho vel (planos YUV)')


# ---------------- audio ----------------
def audio_tramos(toma, salida_json, salida_png=None, paso=0.1):
    """Medición del audio de una toma (mono 48 kHz). Por tramo de `paso` s: RMS dBFS, pico, energía por bandas
    (<150 Hz viento/golpe, 150–300, 300–3400 voz, >3400 aire/espuma), planitud espectral 300–3400 (ruido ≈ 1,
    tonal ≈ 0) y periodicidad de tono 80–400 Hz (autocorrelación normalizada de 300–3400 Hz; voz sostenida ≳ 0,5)."""
    import soundfile  # noqa
    from scipy.signal import butter, sosfilt, spectrogram
    SR = 48000
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src(toma), '-vn', '-map', '0:a:0', '-f', 'f32le', '-ac', '1',
                          '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).astype(np.float64)
    bp = sosfilt(butter(4, [300, 3400], 'band', fs=SR, output='sos'), a)
    L = int(paso * SR)
    filas = []
    for i in range(0, len(a) - L + 1, L):
        x = a[i:i + L]; xb = bp[i:i + L]
        rms = 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)
        pk = 20 * np.log10(np.abs(x).max() + 1e-12)
        X = np.abs(np.fft.rfft(x * np.hanning(L))) ** 2
        f = np.fft.rfftfreq(L, 1 / SR)
        tot = X.sum() + 1e-20
        bandas = {'<150': X[f < 150].sum() / tot, '150-300': X[(f >= 150) & (f < 300)].sum() / tot,
                  '300-3400': X[(f >= 300) & (f < 3400)].sum() / tot, '>3400': X[f >= 3400].sum() / tot}
        Xv = X[(f >= 300) & (f < 3400)] + 1e-20
        plan = float(np.exp(np.log(Xv).mean()) / Xv.mean())
        # periodicidad: autocorrelación de la señal de banda vocal en desfases de 2,5–12,5 ms
        xb0 = xb - xb.mean()
        ac = np.correlate(xb0, xb0, 'full')[L - 1:]
        ac /= ac[0] + 1e-20
        lo, hi = int(SR / 400), int(SR / 80)
        per = float(ac[lo:hi].max())
        filas.append({'t0': round(i / SR, 2), 'rms_dbfs': round(rms, 1), 'pico_dbfs': round(pk, 1),
                      **{f'b{k}': round(float(v), 3) for k, v in bandas.items()},
                      'planitud_voz': round(plan, 3), 'periodicidad': round(per, 3)})
    I = ebur128_archivo(src(toma))
    res = {'toma': toma, 'dur_s': round(len(a) / SR, 3), 'ebur128': I, 'tramos': filas}
    Path(salida_json).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    if salida_png:
        espectrograma_png(a, SR, filas, toma, salida_png)
    return res


def espectrograma_png(a, SR, filas, titulo, salida_png, fmax=8000, px_s=200, alto=400):
    """Espectrograma 0–fmax Hz (lineal) + curva RMS (blanco) y periodicidad (verde) por tramo, con PIL."""
    from scipy.signal import spectrogram
    from PIL import Image, ImageDraw, ImageFont
    f, t, S = spectrogram(a, SR, nperseg=2048, noverlap=2048 - SR // px_s)
    S = 10 * np.log10(S[f <= fmax] + 1e-14)
    v = np.clip((S + 130) / 90, 0, 1)[::-1]                      # -130..-40 dB
    img = (np.stack([v ** 0.8, v ** 2.2, (1 - v) * v * 2.5], -1) * 255).astype(np.uint8)
    im = Image.fromarray(img).resize((max(1, int(len(a) / SR * px_s)), alto))
    W_, H_ = im.size
    lienzo = Image.new('RGB', (W_ + 60, H_ + 170), (20, 20, 20)); lienzo.paste(im, (50, 20))
    d = ImageDraw.Draw(lienzo)
    fnt = ImageFont.truetype(FONT, 12)
    d.text((50, 2), f'{titulo} · espectrograma 0–{fmax} Hz (medición, no escucha)', fill='yellow', font=fnt)
    for hz_ in range(0, fmax + 1, 1000):
        y = 20 + H_ - hz_ / fmax * H_; d.line([(45, y), (50, y)], fill='white'); d.text((2, y - 7), f'{hz_}', fill='white', font=fnt)
    y0 = H_ + 30; hh = 120
    for s in range(0, int(len(a) / SR) + 1):
        x = 50 + s * px_s; d.line([(x, 20), (x, y0 + hh)], fill=(90, 90, 90)); d.text((x + 2, y0 + hh + 2), f'{s} s', fill='white', font=fnt)
    def curva(vals, lo, hi, col):
        pts = [(50 + r['t0'] * px_s + px_s * 0.05, y0 + hh - (min(max(vv, lo), hi) - lo) / (hi - lo) * hh) for r, vv in zip(filas, vals)]
        d.line(pts, fill=col, width=2)
    curva([r['rms_dbfs'] for r in filas], -70, 0, 'white')
    curva([r['periodicidad'] for r in filas], 0, 1, (80, 255, 80))
    d.text((50, y0 - 14), 'blanco: RMS dBFS (−70…0) · verde: periodicidad 80–400 Hz (0…1)', fill='white', font=fnt)
    lienzo.save(salida_png)


def ebur128_archivo(path, extra=()):
    r = subprocess.run(['ffmpeg', '-nostats', *extra, '-i', str(path), '-vn', '-af', 'ebur128=peak=true:framelog=quiet',
                        '-f', 'null', '-'], capture_output=True, text=True).stderr
    out = {}
    for l in r.splitlines():
        s = l.strip()
        for k in ('I:', 'LRA:', 'Peak:'):
            if s.startswith(k):
                out[k[:-1]] = float(s.split()[1])
    return out


def niveles_tramos(path, paso=0.5, stream='0:a:0'):
    """RMS y pico por tramo de una pista (máster o wav)."""
    SR = 48000
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-vn', '-map', stream, '-f', 'f32le', '-ac', '2',
                          '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    L = int(paso * SR); fil = []
    for i in range(0, len(a), L):
        x = a[i:i + L]
        if len(x) < L // 4:
            break
        fil.append({'t0': round(i / SR, 2), 't1': round(min(len(a), i + L) / SR, 3),
                    'rms_dbfs': round(20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12), 1),
                    'pico_dbfs': round(20 * np.log10(np.abs(x).max() + 1e-12), 1)})
    return {'dur_s': round(len(a) / SR, 4), 'tramos': fil}


# ---------------- control ----------------
def md5_streams(path):
    v = run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:v', '-c', 'copy', '-f', 'md5', '-']).strip()
    a = run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a', '-c', 'copy', '-f', 'md5', '-']).strip()
    return {'video': v.replace('MD5=', ''), 'audio': a.replace('MD5=', '')}


def md5_archivo(path):
    import hashlib
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def ffprobe_json(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-count_frames', '-of', 'json',
                           str(path)]))


def decodifica(path):
    r = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(path), '-f', 'null', '-'],
                       capture_output=True, text=True)
    return r.stderr.strip()


def sonoridad_momentanea(path, paso=0.2, ventana=0.4, stream='0:a:0'):
    """Sonoridad momentánea (BS.1770, ponderación K, ventana 400 ms) cada `paso` s. Medición, no escucha."""
    from scipy.signal import lfilter
    SR = 48000
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-vn', '-map', stream, '-f', 'f32le', '-ac', '2',
                          '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]; a1 = [1, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]; a2 = [1, -1.99004745483398, 0.99007225036621]
    k = lfilter(b2, a2, lfilter(b1, a1, a, axis=0), axis=0)
    W = int(ventana * SR); P = int(paso * SR); out = []
    for i in range(0, max(1, len(k) - W + 1), P):
        ms = (k[i:i + W] ** 2).mean(0).sum()
        out.append({'t_centro': round((i + W / 2) / SR, 2), 'lufs_M': round(-0.691 + 10 * np.log10(ms + 1e-12), 1)})
    return out


def alinear_plano(plano_mp4, toma, c_esperado, k=0, caja=None, buscar=2):
    """Comprueba que el cuadro k del plano sea el cuadro c_esperado de la fuente: compara (error medio absoluto)
    contra c_esperado±buscar de la fuente procesada con el mismo color/caja. Devuelve {c: error} y el mejor."""
    w, h = 270, 480
    p = leer_mp4(plano_mp4, w, h, c0=k, c1=k)[0].astype(float)
    c0 = max(0, c_esperado - buscar)
    fr = leer_src(toma, c0, c_esperado + buscar, w, h, caja=caja)
    err = {c0 + i: round(float(np.abs(f.astype(float) - p).mean()), 2) for i, f in enumerate(fr)}
    mejor = min(err, key=err.get)
    return {'esperado': c_esperado, 'mejor': mejor, 'errores': err}


def hoja_mp4(video, salida, cada=0.5, ancho=216, cols=7, c0=0, c1=None, rotulo=''):
    """Hoja de contacto de un MP4 con 't s · cN' del cuadro real del archivo (filas justas)."""
    n = max(1, round(cada * FPS))
    nf = int(run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                  'stream=nb_read_frames', '-of', 'csv=p=0', str(video)]).strip())
    c1 = nf - 1 if c1 is None else min(c1, nf - 1)
    total = (c1 - c0) // n + 1
    filas = math.ceil(total / cols)
    vf = (f"scale={ancho}:-2:flags=area,drawtext=fontfile={FONT}:text='{rotulo}%{{pts\\:hms}} c%{{n}}':x=3:y=3:"
          f"fontsize={max(11, ancho // 15)}:fontcolor=yellow:box=1:boxcolor=black@0.65,"
          f"select='between(n\\,{c0}\\,{c1})*not(mod(n-{c0}\\,{n}))',tile={cols}x{filas}:padding=2:color=0x202020")
    run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', str(video), '-an', '-vf', vf, '-frames:v', '1',
         '-fps_mode', 'vfr', '-q:v', '3', str(salida)])
    return salida


def remux_audio(video_mp4, wav, salida):
    """Misma imagen (stream de video copiado, bit a bit) con otra mezcla: AAC-LC 48 kHz estéreo 192k como video.master,
    sin metadatos, faststart. Se usa para la versión sin música."""
    run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', str(video_mp4), '-i', str(wav), '-map', '0:v:0',
         '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
         '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
         '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
         '-shortest', '-movflags', '+faststart', str(salida)])
    return salida


def mascara_textos(ass_path, cuadros, w=1080, h=1920):
    """Huella exacta de los textos (letras + caja + halo) por cuadro: se queman sobre un fondo gris 128 y se marca
    todo píxel que se aparta del gris. Devuelve {c: máscara bool h×w}."""
    n = max(cuadros) + 1
    vf = (f"subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter,format=rgb24,"
          f"select='" + '+'.join(f'eq(n\\,{c})' for c in cuadros) + "'")
    r = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=c=0x808080:s={w}x{h}:r={FPS}:d={n / FPS + 0.1}',
                        '-vf', vf, '-fps_mode', 'vfr', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(r, np.uint8).reshape(-1, h, w, 3).astype(int)
    return {c: (np.abs(f - 128).max(2) > 6) for c, f in zip(sorted(cuadros), a)}
