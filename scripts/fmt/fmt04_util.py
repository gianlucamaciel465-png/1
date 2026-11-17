#!/usr/bin/env python3
"""FMT-04 · utilidades propias de Pedro (no reemplazan video.py / sonido.py).
hoja_c: hoja de contacto con el número de cuadro real (c = round(t*30) + desfase) y solo las filas necesarias.
leer_cuadros: cuadros RGB reducidos de un tramo de un original (para medir con numpy).
"""
import subprocess, math
import numpy as np
FPS = 30
FONT = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'


def hoja_c(video, salida, cada=0.1, ancho=216, cols=10, desfase=0, t0=0.0, t1=None, rotulo=''):
    """Hoja con el cuadro del máster impreso: c = n_en_el_archivo + desfase (n real, no el contador de select)."""
    n = max(1, round(cada * FPS))
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(video)],
                               capture_output=True, text=True).stdout.strip())
    t1 = dur if t1 is None else min(t1, dur)
    total = len(range(round(t0 * FPS), min(round(t1 * FPS), round(dur * FPS) - 1) + 1, n))
    filas = math.ceil(total / cols)
    a0 = round(t0 * FPS); a1 = round(t1 * FPS)
    txt = f"{rotulo}c%{{eif\\:n+{desfase}\\:d}}" if True else ''
    vf = (f"drawtext=fontfile={FONT}:text='{txt}':x=4:y=4:fontsize={max(12, ancho // 12)}:fontcolor=yellow:box=1:boxcolor=black@0.65,"
          f"select='between(n\\,{a0}\\,{a1})*not(mod(n-{a0}\\,{n}))',scale={ancho}:-2,tile={cols}x{filas}:padding=2:color=0x202020")
    # drawtext antes del select: n es el cuadro real del archivo
    vf = (f"scale={ancho}:-2,drawtext=fontfile={FONT}:text='{txt}':x=4:y=4:fontsize={max(12, ancho // 12)}:fontcolor=yellow:"
          f"box=1:boxcolor=black@0.65,select='between(n\\,{a0}\\,{a1})*not(mod(n-{a0}\\,{n}))',"
          f"tile={cols}x{filas}:padding=2:color=0x202020")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vf', vf, '-frames:v', '1', '-fps_mode', 'vfr',
                    str(salida)], check=True)
    return salida


def leer_cuadros(src, t0, t1, w, h, vf_pre='', fps=None):
    """Devuelve (tiempos, array N×h×w×3 uint8) del archivo src entre t0 y t1 (segundos de la fuente),
    escalado a w×h. vf_pre: filtros antes del escalado (p. ej. rango)."""
    vf = (vf_pre + ',' if vf_pre else '') + (f'fps={fps},' if fps else '') + f'scale={w}:{h}:flags=area,format=rgb24'
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t0:.4f}', '-i', str(src), '-t', f'{t1 - t0:.4f}', '-an',
                        '-vf', vf, '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(r, np.uint8).reshape(-1, h, w, 3)
    return a


# ---------------------------------------------------------------------------------------------------------------
# Acercamiento suave propio. Motivo: en FFmpeg 6.1 el filtro crop evalúa w/h UNA sola vez (al configurar, con t=NAN),
# así que video.plano(z0 != z1) deja la ventana fija en z1 y solo mueve x/y (probado el 17/11/2026 con IMG_7824:
# showinfo da 2700x4800 constantes). Acá se recorta con PIL cuadro a cuadro con caja subpíxel sobre los planos Y, U, V
# (yuv444p, sin conversión de matriz) y se codifica igual que los intermedios de video.py.
# ---------------------------------------------------------------------------------------------------------------
def _decode_yuv444(src, desde, dur, vf, w, h, nf):
    """generador de cuadros yuv444p (3, h, w) uint8 ya rotados."""
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{desde:.4f}', '-i', str(src), '-t', f'{dur + 0.2:.4f}', '-an',
                          '-vf', vf + ',format=yuv444p', '-frames:v', str(nf), '-f', 'rawvideo', '-pix_fmt', 'yuv444p', '-'],
                         stdout=subprocess.PIPE)
    fs = w * h * 3
    for _ in range(nf):
        b = p.stdout.read(fs)
        if len(b) < fs:
            break
        yield np.frombuffer(b, np.uint8).reshape(3, h, w)
    p.stdout.close(); p.wait()


def _encoder(salida, W=1080, H=1920):
    import video as V
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv444p', '-s', f'{W}x{H}',
                             '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                             '-color_trc', 'bt709', '-i', '-', *V.ENC_INT, str(salida)], stdin=subprocess.PIPE)


def _resize_planos(fr, box, W, H):
    from PIL import Image
    out = np.empty((3, H, W), np.uint8)
    for c in range(3):
        out[c] = np.asarray(Image.fromarray(fr[c]).resize((W, H), Image.LANCZOS, box=box))
    return out


def plano_zoom(toma, desde, hasta, salida, caja, z0, z1, cx, cy, por_cuadro=None):
    """Igual que video.plano pero con acercamiento lineal real: Z(k) = z0 + (z1-z0)*k/(nf-1), k = cuadro del plano.
    Ventana (cw/Z × ch/Z) centrada en (cx, cy) y limitada a la caja. Devuelve también la ventana de cada cuadro.
    por_cuadro(k, yuv444) -> yuv444: retoque opcional por cuadro (p. ej. un degradé) ya en 1080x1920.
    cx, cy pueden ser números o funciones del cuadro k (centro que se mueve)."""
    import video as V
    nw, nh = V.TOMAS[toma]['nat']
    dur = hasta - desde; nf = round(dur * FPS)
    x0, y0, cw, ch = caja
    vf = V.color(toma) + f',fps={FPS}'
    enc = _encoder(salida)
    ventanas = []
    for k, fr in enumerate(_decode_yuv444(V._src(toma), desde, dur, vf, nw, nh, nf)):
        Z = z0 + (z1 - z0) * k / max(nf - 1, 1)
        w, h = cw / Z, ch / Z
        cxk = cx(k) if callable(cx) else cx; cyk = cy(k) if callable(cy) else cy
        x = min(max(cxk - w / 2, x0), x0 + cw - w); y = min(max(cyk - h / 2, y0), y0 + ch - h)
        ventanas.append((round(x, 2), round(y, 2), round(w, 2), round(h, 2)))
        o = _resize_planos(fr, (x, y, x + w, y + h), 1080, 1920)
        if por_cuadro is not None:
            o = por_cuadro(k, o)
        enc.stdin.write(o.tobytes())
    enc.stdin.close(); enc.wait()
    if len(ventanas) != nf:
        raise RuntimeError(f'plano_zoom: {len(ventanas)} cuadros, esperaba {nf}')
    return dict(toma=toma, desde=desde, hasta=hasta, cuadros=nf, salida=str(salida), caja=caja, z0=z0, z1=z1,
                cx=cx if not callable(cx) else [round(cx(k), 1) for k in (0, nf - 1)],
                cy=cy if not callable(cy) else [round(cy(k), 1) for k in (0, nf - 1)], ventanas=ventanas)


def compuesto_ventana(toma, desde, hasta, salida, xs, ventana=(1728, 2160), y_dest=420, relleno_vf=None, w_dest=1080,
                      por_cuadro=None):
    """Ventana 4:5 que sigue al sujeto (xs[k] = borde izquierdo en px de la toma, float) escalada a w_dest y pegada en
    y_dest sobre un relleno de la misma toma (relleno_vf: cadena FFmpeg desde la toma rotada hasta 1080x1920)."""
    import video as V
    nw, nh = V.TOMAS[toma]['nat']
    dur = hasta - desde; nf = round(dur * FPS)
    vw, vh = ventana; h_dest = round(w_dest * vh / vw)
    vf = V.color(toma) + f',fps={FPS}'
    rell = _decode_yuv444(V._src(toma), desde, dur, vf + ',' + relleno_vf, 1080, 1920, nf)
    enc = _encoder(salida)
    x_dest = (1080 - w_dest) // 2
    n = 0
    for k, (fr, bg) in enumerate(zip(_decode_yuv444(V._src(toma), desde, dur, vf, nw, nh, nf), rell)):
        x = min(max(xs[k], 0), nw - vw)
        out = bg.copy()
        out[:, y_dest:y_dest + h_dest, x_dest:x_dest + w_dest] = _resize_planos(fr, (x, 0, x + vw, vh), w_dest, h_dest)
        if por_cuadro is not None:
            out = por_cuadro(k, out)
        enc.stdin.write(out.tobytes()); n += 1
    enc.stdin.close(); enc.wait()
    if n != nf:
        raise RuntimeError(f'compuesto_ventana: {n} cuadros, esperaba {nf}')
    return dict(toma=toma, desde=desde, hasta=hasta, cuadros=nf, salida=str(salida), y_dest=y_dest, w_dest=w_dest)


def medir_textos(ass_path, tiempos, W=1080, H=1920):
    """Renderiza el .ass sobre negro en cada tiempo y devuelve la caja (x0, y0, x1, y1) de lo dibujado (texto + borde + caja)."""
    out = {}
    for t in tiempos:
        r = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}:d=12',
                            '-vf', f"subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter,trim=start_frame={round(t * FPS)}:end_frame={round(t * FPS) + 1},format=gray",
                            '-frames:v', '1', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
        a = np.frombuffer(r, np.uint8).reshape(H, W)
        ys, xs = np.nonzero(a > 8)
        out[t] = None if len(ys) == 0 else (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return out


def seguir_torso_7859(t0=0.0, t1=3.0):
    """Seguimiento del torso en IMG_7859 por las letras ROCCÉ (azul marino rodeado de remera blanca), cuadros 960x540.
    Devuelve por cuadro (30 fps desde t0): ROCCÉ x0/x1/y0/y1, borde inferior de «Founders Privée» (celeste B-R>30) y
    borde superior del pelo (None si no hay). Coordenadas de la toma 3840x2160."""
    from scipy import ndimage as ndi
    F = leer_cuadros('/home/user/1/ORIGINALES/IMG_7859.mov', t0, t1 + 0.001, 960, 540, vf_pre='scale=in_range=full:out_range=tv',
                     fps=FPS).astype(np.float32)
    res = []
    for n, f in enumerate(F):
        lum = f.mean(2); R, B = f[..., 0], f[..., 2]
        lab, k = ndi.label(lum < 70); sl = ndi.find_objects(lab)
        let = []
        for i, s in enumerate(sl):
            h = s[0].stop - s[0].start; w = s[1].stop - s[1].start
            if not (25 <= h <= 90 and 10 <= w <= 90) or s[0].start < 150 or s[0].stop > 420:
                continue
            y0, y1 = max(0, s[0].start - 5), min(540, s[0].stop + 5); x0, x1 = max(0, s[1].start - 5), min(960, s[1].stop + 5)
            if np.median(lum[y0:y1, x0:x1][lab[y0:y1, x0:x1] != i + 1]) < 130:
                continue
            let.append((s[1].start, s[1].stop, s[0].start, s[0].stop))
        d = dict(n=n, t=round(t0 + n / FPS, 4), letras=len(let))
        if let:
            lx0 = min(a[0] for a in let); lx1 = max(a[1] for a in let); ly0 = min(a[2] for a in let); ly1 = max(a[3] for a in let)
            d.update(roc_x0=lx0 * 4, roc_x1=lx1 * 4, roc_y0=ly0 * 4, roc_y1=ly1 * 4)
            cq = (lx0 + lx1) / 2; wq = lx1 - lx0
            xa, xb = int(max(0, cq - 0.75 * wq)), int(min(960, cq + 0.75 * wq))
            m = ((B - R > 30) & (lum > 110))[ly1:ly1 + 140, xa:xb]
            rows = np.nonzero(m.sum(1) >= 2)[0]
            d['founders_y1'] = int((ly1 + rows.max()) * 4 + 3) if len(rows) else None
            hx0, hx1 = int(cq - 0.6 * wq), int(cq + 0.6 * wq)
            rows = np.nonzero((lum[:max(1, ly0 - 20), hx0:hx1] < 60).sum(1) >= 2)[0]
            d['pelo_y0'] = int(rows.min() * 4) if len(rows) else None
        res.append(d)
    return res


def degrade_negro(alfa_por_fila, rampa=None, clave=None):
    """devuelve por_cuadro que mezcla negro de rango limitado (Y 16, U/V 128) con alfa por fila (array de alto 1920 o menos):
    lo mismo que un overlay RGBA negro, sin depender del 'enable' del filtro overlay.
    rampa=(k0, k1): el degradé entra lineal entre los cuadros k0 (nada) y k1 (completo) del plano.
    clave=(y0, y1): solo oscurece lo claro (cielo): peso 0 con Y ≤ y0 y 1 con Y ≥ y1 (Y de rango limitado), así la tela
    negra y las letras tono sobre tono quedan intactas."""
    a0 = np.zeros(1920, np.float32); a0[:len(alfa_por_fila)] = alfa_por_fila
    a0 = a0[:, None]

    def f(k, o):
        fac = 1.0 if rampa is None else float(np.clip((k - rampa[0]) / (rampa[1] - rampa[0]), 0, 1))
        if fac <= 0:
            return o
        a = a0 * fac
        o = o.astype(np.float32)
        if clave is not None:
            w = np.clip((o[0] - clave[0]) / (clave[1] - clave[0]), 0, 1)
            a = a * (w * w * (3 - 2 * w))
        o[0] = 16 + (o[0] - 16) * (1 - a); o[1] = 128 + (o[1] - 128) * (1 - a); o[2] = 128 + (o[2] - 128) * (1 - a)
        return np.clip(np.round(o), 0, 255).astype(np.uint8)
    return f
