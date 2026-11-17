#!/usr/bin/env python3
"""FMT-03 · «¿Blanca o Negra?» · receta del máster v02 (Pedro, 17/11/2026).

Dictamen: piezas/FMT_tanda_formatos/FMT-03_blanca_o_negra/04_roma_dictamen_master_v01.md. Se conserva el montaje
(TRABAJO/fmt/fmt03/fmt03_video.mp4 de v01, sin re-render). Cambia texto, sonido y nada más:
  1. degradé oscuro suave detrás de «Decidí antes del final.» (c0–c53), por cuadro, terminando ≥ 20 px por encima
     de la prenda y de las manos medidas en cada cuadro;
  2. +8 dB en 0–1,7 s y +6 dB en 4,8–6,5 s a los elementos de la propuesta de la hoja v01 (pad, charles, campana,
     redoble y subida), manteniendo los huecos 1,70–1,80 y 6,50–6,60 antes de los drops;
  3. ambiente de 1,80–4,80: 7793 → alternativa del guion (7824 6,00, −6 dB, pasa-altos 150, pasa-bajos 8000), porque los
     sonidos tonales de 7793 no corresponden a nada que se vea (etapa «tonales»).
Las utilidades genéricas (degradé por cuadro, contraste, límites de texto, sonoridad momentánea, tonales) viven acá;
fmt01_v02.py las importa.

Etapas (python fmt03_v02.py <etapa>, con nice -n 10):  tonales → degrade → audio → master → control → entregar
"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V  # noqa: E402
import fmt03 as U  # noqa: E402  (utilidades y receta v01; no ejecuta nada al importarse)

R = U.R
T = U.T                       # TRABAJO/fmt/fmt03 (montaje v01)
T2 = T / 'v02'
FPS = 30
NF = 306
DUR = NF / FPS
VID0 = T / 'fmt03_video.mp4'  # montaje v01 sin textos (se conserva)
VID = T2 / 'fmt03_video_degrade.mp4'


# =====================================================================================================
# utilidades genéricas (las usa también fmt01_v02.py)
# =====================================================================================================
def perfil(alfa, y_plano, y_cero, H=1920):
    """alfa por fila: `alfa` hasta y_plano y fundido coseno a 0 en y_cero (el mismo perfil del degradé de FMT-01 v01).
    Si y_cero ≤ 0 no hay degradé. Si y_plano < 0, el coseno empieza fuera del cuadro (sigue siendo continuo)."""
    y = np.arange(H, dtype=np.float32)
    a = np.zeros(H, np.float32)
    if y_cero <= 0:
        return a
    a[y <= y_plano] = alfa
    m = (y > y_plano) & (y < y_cero)
    t = (y[m] - y_plano) / (y_cero - y_plano)
    a[m] = alfa * 0.5 * (1 + np.cos(np.pi * t))
    return a


def top_producto(f, x0=0, x1=None, min_area=3000):
    """fila más alta de la prenda o de las manos (1080×1920 RGB): tela oscura (L < 60) o piel (R > 120, R−G > 25,
    R−B > 35), apertura 2, componentes de más de `min_area` px. Devuelve None si no hay."""
    from scipy import ndimage as nd
    g = f[:, x0:x1].astype(np.int16); r, gg, b = g[..., 0], g[..., 1], g[..., 2]
    L = U.luma(f[:, x0:x1])
    m = nd.binary_opening(((r > 120) & (r - gg > 25) & (r - b > 35)) | (L < 60), iterations=2)
    lab, k = nd.label(m)
    if not k:
        return None
    s = nd.sum(m, lab, range(1, k + 1))
    big = [i + 1 for i, v in enumerate(s) if v > min_area]
    if not big:
        return None
    return int(np.nonzero(np.isin(lab, big))[0].min())


def aplicar_degrade(src, dst, nf, alfas, W=1080, H=1920):
    """alfas: {cuadro: alfa por fila (H,)}. Mezcla con negro sobre los planos YUV decodificados (rango limitado):
    Y' = 16 + (Y − 16)(1 − a), U' = 128 + (U − 128)(1 − a) con el alfa de croma promediado por pares de filas.
    Sin overlay ni conversión de color: los cuadros sin alfa pasan con el mismo contenido (recodificados con ENC_INT)."""
    ny = W * H; nc = ny // 4
    dec = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(src), '-f', 'rawvideo',
                            '-pix_fmt', 'yuv420p', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p',
                            '-s', f'{W}x{H}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-i', '-', *V.ENC_INT, str(dst)],
                           stdin=subprocess.PIPE)
    k = 0
    while True:
        b = dec.stdout.read(ny + 2 * nc)
        if len(b) < ny + 2 * nc:
            break
        a = alfas.get(k)
        if a is not None and a.max() > 0:
            fy = (1 - a)[:, None]; fc = (1 - 0.5 * (a[0::2] + a[1::2]))[:, None]
            f = np.frombuffer(b, np.uint8).astype(np.float32)
            Y = f[:ny].reshape(H, W); U_ = f[ny:ny + nc].reshape(H // 2, W // 2); V_ = f[ny + nc:].reshape(H // 2, W // 2)
            Y = 16 + (Y - 16) * fy; U_ = 128 + (U_ - 128) * fc; V_ = 128 + (V_ - 128) * fc
            b = np.concatenate([Y.ravel(), U_.ravel(), V_.ravel()]).round().clip(0, 255).astype(np.uint8).tobytes()
        enc.stdin.write(b); k += 1
    dec.stdout.close(); dec.wait(); enc.stdin.close(); enc.wait()
    assert k == nf and enc.returncode == 0, (k, nf, enc.returncode)


def lin(v):
    v = np.asarray(v, np.float64) / 255
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def contraste_blanco(img, mask):
    """contraste (WCAG) de un relleno blanco contra cada píxel de fondo de `mask` (imagen SIN texto, sRGB):
    1,05 / (Y_lin + 0,05). Devuelve la mediana, el p10 (el 10 % de fondo más claro) y la luma mediana."""
    p = img[mask].astype(np.float64)
    Y = lin(p) @ np.array([0.2126, 0.7152, 0.0722])
    r = 1.05 / (Y + 0.05)
    return dict(contraste_mediana=round(float(np.median(r)), 2), contraste_p10=round(float(np.percentile(r, 10)), 2),
                luma_mediana=round(float(np.median(U.luma(img)[mask])), 1))


def mascara_texto(texto, t, carpeta, nombre, dil=8):
    """máscara (1920×1080, bool) de UN texto renderizado por libass en el instante t, dilatada `dil` px: el fondo que
    lo rodea. Se usa para medir el contraste en el video sin textos."""
    from scipy import ndimage as nd
    p = carpeta / f'{nombre}.ass'; V.ass([texto], p)
    r = U.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=black:s=1080x1920:r=30:d=16', '-vf',
               f"subtitles={p}:fontsdir=/usr/share/fonts/opentype/inter,trim=start={t:.4f},setpts=PTS-STARTPTS,"
               f"format=gray", '-frames:v', '1', '-f', 'rawvideo', '-'])
    g = np.frombuffer(r, np.uint8).reshape(1920, 1080) > 8
    return nd.binary_dilation(g, iterations=dil) if dil else g, g


def textos_limites(master, vid_ref, textos, limites, nf, carpeta):
    """En el máster, cada texto se ve en sus cuadros pedidos [a, b] y no en a−1 ni b+1. Se mide |máster − video sin
    textos| dentro de la máscara de ese texto (sin los píxeles de otros textos visibles en ese cuadro)."""
    from scipy import ndimage as nd
    mascaras = [mascara_texto(textos[i], (a + b) / 2 / FPS, carpeta, f'texto_{i}')[0] for i, (a, b) in enumerate(limites)]
    filas = []
    for i, (a, b) in enumerate(limites):
        for n in (a - 1, a, b, b + 1):
            if n < 0 or n >= nf:
                continue
            otros = [j for j, (aa, bb) in enumerate(limites) if j != i and aa <= n <= bb]
            mk = mascaras[i].copy()
            for j in otros:
                mk &= ~nd.binary_dilation(mascaras[j], iterations=8)
            m_ = U.leer(master, 1080, 1920, n0=n, n1=n)[0].astype(np.float32)
            v_ = U.leer(vid_ref, 1080, 1920, n0=n, n1=n)[0].astype(np.float32)
            d = float(np.abs(m_ - v_)[mk].mean()) if mk.any() else None
            filas.append(dict(texto=textos[i]['txt'], pedido=f'c{a}–c{b}', cuadro=n, pixeles_medidos=int(mk.sum()),
                              dif_media=None if d is None else round(d, 2), visible=(d or 0) > 4,
                              debe_verse=a <= n <= b))
    return filas, all(f['visible'] == f['debe_verse'] for f in filas)


def momentanea(f):
    """sonoridad momentánea (400 ms) y de corto plazo (3 s) cada 100 ms, ebur128 sobre el archivo."""
    r = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-nostats', '-v', 'verbose', '-i', str(f), '-vn', '-af', 'ebur128',
                        '-f', 'null', '-'], capture_output=True, text=True).stderr
    return [dict(t=float(a), M=float(b), S=float(c)) for a, b, c in
            re.findall(r't:\s*([\d.]+)\s+TARGET:.*?M:\s*([-\d.]+)\s+S:\s*([-\d.]+)', r)]


def momentanea_tramos(mom, tramos):
    """por tramo (nombre, t0, t1): M (ventana de 400 ms que termina en t, con t − 0,4 ≥ t0 y t ≤ t1) mín/mediana/máx."""
    out = []
    for nom, t0, t1 in tramos:
        v = [x['M'] for x in mom if x['t'] - 0.4 >= t0 - 1e-6 and x['t'] <= t1 + 1e-6]
        out.append(dict(tramo=nom, t0=t0, t1=t1, M_min=min(v) if v else None,
                        M_mediana=round(float(np.median(v)), 1) if v else None, M_max=max(v) if v else None, n=len(v)))
    return out


def curva(N, tramos, sr=48000):
    """ganancia lineal por muestra: tramos = [(t0, t1, dB, rampa_entrada, rampa_salida)]; las rampas (en s) son
    lineales en dB y van DESPUÉS de t0 y DESPUÉS de t1 (la salida baja dentro del hueco)."""
    gdb = np.zeros(N)
    t = np.arange(N) / sr
    for t0, t1, d, ri, ro in tramos:
        m = (t >= t0) & (t < t1)
        w = np.ones(m.sum())
        if ri:
            w = np.minimum(w, (t[m] - t0) / ri)
        gdb[m] = np.maximum(gdb[m], d * w)
        if ro:
            m2 = (t >= t1) & (t < t1 + ro)
            gdb[m2] = np.maximum(gdb[m2], d * (1 - (t[m2] - t1) / ro))
    return 10 ** (gdb / 20)


def tonales(x, sr, t_ini, banda=(500, 4500), umbral_db=15, voz=True):
    """sonidos tonales en un tramo de audio (mono). STFT de 2048 muestras (42,7 ms) cada 10 ms; el espectro en dB se
    «blanquea» restando su envolvente (mediana móvil de 17 bandas = 400 Hz), así la caída natural del viento no cuenta.
    - evento tonal: el pico blanqueado más alto de `banda` supera `umbral_db` durante ≥ 30 ms (frecuencias al inicio,
      al final, mínima y máxima);
    - tonos estacionarios: bandas con ≥ 8 dB blanqueados en ≥ 80 % de las ventanas (zumbidos, no eventos);
    - voz: pila armónica (f0 80–300 Hz con ≥ 4 de los 6 primeros armónicos ≥ 8 dB blanqueados). Una pila con la misma
      f0 en ≥ 80 % de las ventanas es un zumbido estacionario, no voz."""
    from scipy.signal import stft
    from scipy.ndimage import median_filter
    f, t, Z = stft(x, sr, nperseg=2048, noverlap=2048 - 480)
    A = 20 * np.log10(np.abs(Z) + 1e-9)
    Wb = A - median_filter(A, size=(17, 1), mode='nearest')
    b = (f >= banda[0]) & (f <= banda[1])
    pico = Wb[b].max(0); fpk = f[b][Wb[b].argmax(0)]
    ton = pico >= umbral_db
    ev = []
    k = 0
    while k < len(t):
        if ton[k]:
            j = k
            while j + 1 < len(t) and ton[j + 1]:
                j += 1
            if t[j] - t[k] >= 0.03:
                seg = slice(k, j + 1)
                ev.append(dict(t0=round(t_ini + float(t[k]), 3), t1=round(t_ini + float(t[j]), 3),
                               f_ini_hz=int(fpk[k]), f_fin_hz=int(fpk[j]), f_min_hz=int(fpk[seg].min()),
                               f_max_hz=int(fpk[seg].max()), sobre_envolvente_db=round(float(pico[seg].max()), 1)))
            k = j + 1
        else:
            k += 1
    est = (Wb >= 8).mean(1)
    estacionarios = [int(f[i]) for i in np.nonzero((est >= 0.8) & (f >= 40) & (f <= 8000))[0]]
    rep = dict(eventos=ev, ventanas_tonales_pct=round(float(ton.mean() * 100), 1),
               tonos_estacionarios_hz=estacionarios)
    if voz:
        df = f[1] - f[0]
        f0s = np.arange(80, 300.1, 2.5)
        hallados = []
        for i in range(len(t)):
            col = Wb[:, i]; mejor = None
            for f0 in f0s:
                cnt = 0
                for n in range(1, 7):
                    c = int(round(n * f0 / df))
                    if col[max(0, c - 1):c + 2].max() >= 8:
                        cnt += 1
                if cnt >= 4:
                    mejor = float(f0); break
            if mejor:
                hallados.append((round(t_ini + float(t[i]), 2), mejor))
        f0_moda = None; frac = 0.0
        if hallados:
            vals = np.array([h[1] for h in hallados]); u, c = np.unique(np.round(vals / 5) * 5, return_counts=True)
            f0_moda = float(u[c.argmax()]); frac = float(c.max() / len(t))
        rep.update(ventanas_con_pila_armonica=len(hallados), ventanas_total=len(t), pila_f0_moda_hz=f0_moda,
                   pila_misma_f0_fraccion=round(frac, 2), pila_tiempos=[h[0] for h in hallados][:60],
                   voz_probable=bool(len(hallados) >= 0.1 * len(t) and frac < 0.8))
    return rep


def espectrograma(wav_mono, sr, salida, t_ini, titulo, fmax=6000, marcas=()):
    """PNG del espectrograma (dB) con eje de tiempo de la FUENTE y marcas verticales (t)."""
    from scipy.signal import stft
    from PIL import Image, ImageDraw, ImageFont
    f, t, Z = stft(wav_mono, sr, nperseg=2048, noverlap=2048 - 240)
    A = 20 * np.log10(np.abs(Z) + 1e-9); b = f <= fmax; A = A[b][::-1]
    lo, hi = np.percentile(A, 5), A.max()
    g = np.clip((A - lo) / (hi - lo), 0, 1)
    img = (np.stack([g ** 0.6, g ** 1.4, 0.4 * g + 0.6 * g ** 3], -1) * 255).astype(np.uint8)
    im = Image.fromarray(img).resize((1400, 520)); d = ImageDraw.Draw(im)
    fnt = ImageFont.truetype(U.FONT, 16)
    W_ = im.width; dur = len(wav_mono) / sr
    for k in range(int(np.ceil(dur * 10)) + 1):
        x = int(k / 10 / dur * W_)
        d.line([x, 510, x, 520], fill=(255, 255, 255))
        if k % 5 == 0:
            d.text((x + 2, 490), f'{t_ini + k / 10:.1f}', font=fnt, fill=(255, 255, 0))
    for hz in range(1000, fmax, 1000):
        y = int((1 - hz / fmax) * 520); d.line([0, y, 8, y], fill=(255, 255, 255)); d.text((10, y - 9), f'{hz} Hz', font=fnt, fill=(255, 255, 255))
    for m in marcas:
        x = int((m - t_ini) / dur * W_); d.line([x, 0, x, 480], fill=(0, 255, 0))
    d.text((80, 4), titulo, font=fnt, fill=(255, 255, 0))
    im.save(salida)


def wav_np(f, t0=None, t1=None, sr=48000, canal=None):
    cmd = ['ffmpeg', '-v', 'error']
    if t0 is not None:
        cmd += ['-ss', f'{t0:.4f}']
    cmd += ['-i', str(f)]
    if t1 is not None:
        cmd += ['-t', f'{t1 - (t0 or 0):.4f}']
    cmd += ['-vn', '-f', 'f32le', '-ac', '1', '-ar', str(sr), '-']
    return np.frombuffer(U.run(cmd), np.float32).astype(np.float64)


# =====================================================================================================
# etapa 1 · sonidos tonales de 7793 (indicación 3): espectrograma, eventos y pila armónica de voz
# =====================================================================================================
def etapa_tonales():
    T2.mkdir(parents=True, exist_ok=True)
    O = R / 'ORIGINALES'
    rep = {}
    # la fuente de 7793 que usaba v01 en 1,80–4,80 es 1,167–4,167 (pasa-altos 150, pasa-bajos 8000)
    from scipy.signal import butter, sosfilt
    sos = butter(2, [150, 8000], btype='band', fs=48000, output='sos')
    for toma, t0, t1, nom in (('IMG_7793', 1.167, 4.167, '7793_usado_v01'), ('IMG_7824', 6.00, 9.00, '7824_alternativa')):
        x = sosfilt(sos, wav_np(O / f'{toma}.mov', t0, t1))
        rep[nom] = dict(toma=toma, fuente=[t0, t1], **tonales(x, 48000, t0))
        espectrograma(x, 48000, T2 / f'espectro_{nom}_{t0:.2f}-{t1:.2f}.png', t0,
                      f'{toma} fuente {t0:.3f}–{t1:.3f} s (pasa-banda 150–8000) · marcas: tramos de Roma',
                      marcas=(1.17, 1.37, 1.67, 1.87) if toma == 'IMG_7793' else ())
        print(nom, {k: v for k, v in rep[nom].items() if k not in ('eventos', 'pila_tiempos')}, flush=True)
        for e in rep[nom]['eventos']:
            print('   ', e)
    # detalle 0,8–2,3 s de 7793 (los dos tramos de Roma con margen)
    x = sosfilt(sos, wav_np(O / 'IMG_7793.mov', 0.8, 2.3))
    espectrograma(x, 48000, T2 / 'espectro_7793_0.80-2.30_detalle.png', 0.8,
                  'IMG_7793 fuente 0,80–2,30 s (detalle) · verde: 1,17 / 1,37 / 1,67 / 1,87', fmax=5000,
                  marcas=(1.17, 1.37, 1.67, 1.87))
    rep['transcripcion'] = ('no disponible: faster-whisper está instalado (TRABAJO/whisper-env) pero la descarga del '
                            'modelo desde huggingface.co la rechaza el proxy del entorno (403 por política); no se reintentó')
    json.dump(rep, open(T2 / 'tonales.json', 'w'), ensure_ascii=False, indent=1)


# =====================================================================================================
# etapa 2 · degradé detrás de «Decidí antes del final.» (indicación 1)
# =====================================================================================================
# Medido en el video sin textos (etapa degrade, tops.json): la prenda o las manos empiezan en y 484–566 en c0–c45
# (1a + primer cuadro de 1b); en c46 la remera ya llega a y 150 (acercamiento de 1b) y desde c47 llena el cuadro.
# Perfil de FMT-01 v01 (negro alfa 0,38 y fundido coseno de 150 px), con y_cero = min(480, tope − 20) por cuadro:
# siempre termina ≥ 20 px por encima de la prenda y de las manos; donde la remera tapa el texto (c47–c53) no hay degradé.
DEG = dict(alfa=0.38, fundido_px=150, y_cero_max=480, separacion_px=20, cuadros=(0, 53))


def alfas_fmt03():
    tops = {}
    fr = U.leer(VID0, 1080, 1920, n0=DEG['cuadros'][0], n1=DEG['cuadros'][1])
    alfas, filas = {}, []
    for k, f in enumerate(fr):
        n = DEG['cuadros'][0] + k
        top = top_producto(f)
        yc = min(DEG['y_cero_max'], (top if top is not None else 1920) - DEG['separacion_px'])
        a = perfil(DEG['alfa'], yc - DEG['fundido_px'], yc)
        alfas[n] = a; tops[n] = top
        filas.append(dict(cuadro=n, tope_prenda_o_manos=top, y_cero=yc if yc > 0 else None,
                          y_plano=(yc - DEG['fundido_px']) if yc > 0 else None, alfa_max=round(float(a.max()), 3)))
    return alfas, filas


def etapa_degrade():
    T2.mkdir(parents=True, exist_ok=True)
    alfas, filas = alfas_fmt03()
    aplicar_degrade(VID0, VID, NF, alfas)
    # comprobación sobre el video codificado: filas oscurecidas (> 1,5 niveles de media en filas de 2 px) por cuadro,
    # contra el tope de la prenda; oscurecimiento dentro de la prenda; nada cambia fuera de c0–c53
    n0, n1 = DEG['cuadros']
    a0 = U.leer(VID0, 1080, 1920, n0=n0, n1=n1 + 1)
    a1 = U.leer(VID, 1080, 1920, n0=n0, n1=n1 + 1)
    for k, fi in enumerate(filas):
        x0, x1 = a0[k].astype(np.float32), a1[k].astype(np.float32)
        d = (x0 - x1).mean(axis=(1, 2)).reshape(-1, 2).mean(1)
        r = np.nonzero(d > 1.5)[0]
        fi['y_max_oscurecida'] = int(r.max()) * 2 + 1 if len(r) else None
        top = fi['tope_prenda_o_manos']
        fi['separacion_px'] = (top - fi['y_max_oscurecida']) if (top is not None and fi['y_max_oscurecida'] is not None) else None
        if top is not None:
            fi['oscurecimiento_medio_desde_tope'] = round(float((x0[top:] - x1[top:]).mean()), 3)
    c54 = float(np.abs(a0[-1].astype(np.float32) - a1[-1].astype(np.float32)).mean())
    del a0, a1
    b0 = U.leer(VID0, 270, 480, n0=54, n1=NF - 1).astype(np.float32); b1 = U.leer(VID, 270, 480, n0=54, n1=NF - 1).astype(np.float32)
    osc_resto = (b0 - b1).mean(axis=(2, 3))
    rep = dict(parametros=DEG, por_cuadro=filas,
               separacion_min_px=min(f['separacion_px'] for f in filas if f['separacion_px'] is not None),
               oscurecimiento_max_desde_tope=max(f.get('oscurecimiento_medio_desde_tope', 0) for f in filas),
               c54_dif_abs_media=round(c54, 3), c54_c305_osc_max_fila=round(float(osc_resto.max()), 2),
               c54_c305_dif_abs_media=round(float(np.abs(b0 - b1).mean()), 3))
    json.dump(rep, open(T2 / 'degrade.json', 'w'), ensure_ascii=False, indent=1)
    for f in filas[::5] + filas[44:48]:
        print(f)
    print({k: v for k, v in rep.items() if k not in ('por_cuadro', 'parametros')})
    # imagen del alfa (c0 y c30) y comparación antes/después de c0, c30 y c45 con el texto quemado
    contraste_texto(guardar=True)


def contraste_texto(guardar=False):
    """contraste de «Decidí antes del final.» antes (v01) y después (v02) del degradé, en c0–c53 (cada 3 cuadros y el
    resumen), medido en los videos sin textos dentro de la máscara del texto dilatada 8 px."""
    t = U.TEXTOS[1]
    mk, glifos = mascara_texto(t, 0.9, T2, 'texto_decidi')
    filas = []
    ns = list(range(0, 54, 3)) + [45, 46, 47, 53]
    for n in sorted(set(ns)):
        f0 = U.leer(VID0, 1080, 1920, n0=n, n1=n)[0]; f1 = U.leer(VID, 1080, 1920, n0=n, n1=n)[0]
        filas.append(dict(cuadro=n, v01=contraste_blanco(f0, mk), v02=contraste_blanco(f1, mk)))
    ys, xs = np.nonzero(glifos)
    rep = dict(texto=t['txt'], glifos_caja=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
               metodo='WCAG 1,05/(Y_lin+0,05) de relleno blanco contra cada píxel de fondo (máscara del texto dilatada '
                      '8 px, video sin textos); mediana y p10 (el 10 % de fondo más claro)', por_cuadro=filas,
               v02_mediana_min_c0_c45=min(f['v02']['contraste_mediana'] for f in filas if f['cuadro'] <= 45),
               v02_p10_min_c0_c45=min(f['v02']['contraste_p10'] for f in filas if f['cuadro'] <= 45),
               v01_mediana_max_c0_c45=max(f['v01']['contraste_mediana'] for f in filas if f['cuadro'] <= 45))
    if guardar:
        json.dump(rep, open(T2 / 'contraste_decidi.json', 'w'), ensure_ascii=False, indent=1)
    for f in filas:
        print(f['cuadro'], 'v01', f['v01'], 'v02', f['v02'])
    print('glifos', rep['glifos_caja'], 'v02 mediana mín c0–c45', rep['v02_mediana_min_c0_c45'], 'p10 mín',
          rep['v02_p10_min_c0_c45'])
    return rep


# =====================================================================================================
# etapa 3 · sonido (indicaciones 2 y 3)
# =====================================================================================================
def ambientes(m):
    m.ambiente('IMG_7824', 3.70, 0.0, 1.80, -10, hp=200)
    # v02: alternativa del guion (§5) en vez de 7793 1,167 +8 dB: 7793 tiene sonidos tonales que no corresponden a nada
    # de la imagen (tonales.json); 7824 6,00–9,00 es el mismo balcón y no tiene eventos tonales
    m.ambiente('IMG_7824', 6.00, 1.80, 4.80, -6, hp=150, lp=8000)
    m.ambiente('IMG_7996', 0.80, 4.80, 6.60, -4, hp=200)
    m.ambiente('IMG_7857', 1.70, 6.60, 7.80, -6)
    m.ambiente('IMG_7857', 2.90, 7.80, 9.20, -10, fin_fade=.3)
    m.ambiente('IMG_7857', 1.70, 9.20, 10.20, -12, ini_fade=.3, fin_fade=.25)


GANANCIA = [(0.0, 1.70, 8.0, 0.0, 0.10),      # entrada: +8 dB; vuelve a 0 dentro del hueco 1,70–1,80
            (4.80, 6.50, 6.0, 0.03, 0.10)]    # tensión: +6 dB desde el corte c144; vuelve a 0 en el hueco 6,50–6,60


def musica(m, g):
    """igual que v01 (fmt03.musica); los elementos de la propuesta (pad, charles, campana, redoble y subida de la entrada
    y de la tensión) van a la mezcla `g`, que recibe la curva GANANCIA antes de sumarse."""
    ch = lambda mz, t0, t1, gg=.08: [mz.charles(round(t, 3), gg) for t in np.arange(t0, t1 - 1e-6, 0.3)]
    # entrada c0–c53 → g
    g.pad(0.0, [45, 48, 52], 1.7, .05, 1000, a=.15)
    for i, t in enumerate((0.0, 0.3, 0.6, 0.9, 1.2, 1.5)):
        g.charles(t, .06 + .03 * i / 5)
    g.campana(0.0, 76, .05)
    g.subida(0.90, 1.70, .16)
    # drop 1 (c54)
    m.bombo(1.8, .9); m.ocho08(1.8, 33, 1.0, .55, glide_desde=40); m.impacto(1.8, .40)
    m.pad(1.8, [45, 48, 52], 2.3, .06, 1400)
    m.bombo(3.0); m.bombo(3.3, .5); m.palma(2.4); m.palma(3.6); ch(m, 1.8, 4.2)
    m.ocho08(3.0, 33, .5); m.ocho08(3.6, 36, .5)
    # compás 3 (tensión): pad, charles, redoble y subida → g (la curva sube desde 4,80)
    m.bombo(4.2, .8)
    g.pad(4.2, [41, 45, 48], 1.15, .06, 1200); g.pad(5.4, [40, 44, 47], 1.15, .06, 1200)
    ch(g, 4.2, 5.4); g.redoble(5.4, 6.4, .12); g.subida(5.6, 6.5, .14)
    # drop 2 (c198) en adelante, igual que v01
    m.bombo(6.6, 1.0); m.impacto(6.6, .55); m.ocho08(6.6, 33, 1.1, .6, glide_desde=40)
    m.pad(6.6, [45, 48, 52, 57], 1.15, .07); ch(m, 6.6, 7.8); m.palma(7.2)
    m.bombo(7.8, .75); m.pad(7.8, [48, 52, 55], 1.15, .06); m.ocho08(7.8, 36, .5); m.ocho08(8.4, 40, .5)
    m.palma(8.4); ch(m, 7.8, 9.0)
    m.bombo(9.0, .9); m.ocho08(9.0, 33, 1.1, .5); m.pad(9.0, [45, 48, 52, 57], .9, .06, r=.5)
    m.campana(9.0, 76, .07, .9); m.palma(9.6, .25)
    # curva a la mezcla g y suma
    c = curva(m.N, GANANCIA)[:, None]
    for k in ('mus', 'fx'):
        m.pistas[k] += g.pistas[k] * c
    m.ev += [dict(e, evento=e['evento'] + ' (con curva v02)') for e in g.ev]
    m.log(0.0, 'curva v02: +8 dB 0,00–1,70 (rampa de salida 1,70–1,80) a pad/charles/campana/subida de la entrada')
    m.log(4.80, 'curva v02: +6 dB 4,80–6,50 (rampas 4,80–4,83 y 6,50–6,60) a pad/charles/redoble/subida de la tensión')
    # huecos y final, después de sumar todo
    m.silenciar('mus', 1.70, 1.80); m.silenciar('mus', 6.50, 6.60)
    m.fundido('mus', 9.70, 10.20)
    m.fundido('fx', 9.85, 10.20)


def etapa_audio():
    from sonido import Mezcla
    A = T2 / 'audio'; A.mkdir(parents=True, exist_ok=True)
    m = Mezcla(DUR); g = Mezcla(DUR)
    ambientes(m); U.foley(m); musica(m, g)
    r1 = m.exportar(str(A / 'fmt03_completa.wav'), lufs=-14)
    s = Mezcla(DUR); ambientes(s); U.foley(s)            # sin música: ambiente, tela, barrido y toque (sin curva)
    r2 = s.exportar(str(A / 'fmt03_sinmusica.wav'), lufs=-14)
    print('completa', r1, 'sin música', r2)
    # sonidos tonales en la mezcla final 1,80–4,80 (sin música): comprobar que no quedó nada de 7793
    x = wav_np(A / 'fmt03_sinmusica.wav', 1.80, 4.80)
    json.dump(tonales(x, 48000, 1.80, voz=False), open(A / 'tonales_sinmusica_1.80-4.80.json', 'w'), indent=1)


# =====================================================================================================
# etapa 4 · máster (mismos textos exactos de v01; el .ass se vuelve a escribir y se compara con el de v01)
# =====================================================================================================
NOMBRES = {'completa': 'ROCCE_FMT03_BLANCA_O_NEGRA_v02.mp4', 'sinmusica': 'ROCCE_FMT03_BLANCA_O_NEGRA_SINMUSICA_v02.mp4'}
MAS = T2 / 'master'
ASS = T2 / 'fmt03_textos.ass'
LIMITES_TEXTO = [(0, 53), (0, 53), (144, 182), (234, 305), (246, 305)]


def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    a = V.ass(U.TEXTOS, ASS)
    assert Path(a).read_bytes() == (T / 'fmt03_textos.ass').read_bytes(), 'el .ass cambió respecto de v01'
    for k, nombre in NOMBRES.items():
        if (MAS / nombre).exists():
            raise RuntimeError(f'{MAS / nombre} ya existe')
        V.master(VID, T2 / 'audio' / f'fmt03_{k}.wav', MAS / nombre, ass_path=a)
        print('->', MAS / nombre)


# =====================================================================================================
# etapa 5 · control y evidencia
# =====================================================================================================
EVID = T2 / 'evidencia_v02'
TRAMOS = [('1 gancho: Negra sostenida + tapa el lente', 0.0, 1.8), ('2 Negra puesta (7793; ambiente 7824)', 1.8, 4.8),
          ('3 ¿Y la Blanca? tiro (7996)', 4.8, 6.6), ('4 Blanca puesta (7857)', 6.6, 7.8),
          ('5 pantalla dividida + CTA', 7.8, 10.2), ('último 0,5 s', 9.7, 10.2)]
TRAMOS_M = [('gancho 0,0–1,7', 0.0, 1.7), ('hueco + drop 1 1,7–2,2', 1.7, 2.2), ('Negra puesta 1,8–4,2', 1.8, 4.2),
            ('4,2–4,8', 4.2, 4.8), ('tensión 4,8–6,5', 4.8, 6.5), ('drop 2 6,6–7,8', 6.6, 7.8),
            ('pantalla dividida 7,8–10,2', 7.8, 10.2)]


def extra_v02():
    import shutil
    # comprobaciones de v01 sobre el máster v02 (§8.1 tapado del lente, §8.3 textos fuera de las ventanas, color)
    U.MAS, U.NOMBRES = MAS, NOMBRES
    out = U.extra_fmt03()
    S = T2 / 'ctrl'; S.mkdir(exist_ok=True)
    f0 = MAS / NOMBRES['completa']
    out['textos_limites'], out['textos_ok'] = textos_limites(f0, VID, U.TEXTOS, LIMITES_TEXTO, NF, S)
    # contraste de todos los textos (en su cuadro medio, v02 sin textos) + «Decidí» antes/después
    out['contraste_decidi'] = contraste_texto(guardar=True)
    cont = {}
    for i, (a, b) in enumerate(LIMITES_TEXTO):
        n = (a + b) // 2; t = U.TEXTOS[i]
        mk, _ = mascara_texto(t, n / FPS, S, f'cont_{i}')
        f = U.leer(VID, 1080, 1920, n0=n, n1=n)[0]
        c = contraste_blanco(f, mk)
        if t['estilo'] in ('Caja', 'CajaN'):
            c['nota'] = ('caja opaca: ' + ('texto #141414 sobre caja blanca' if t['estilo'] == 'Caja'
                                           else 'texto blanco sobre caja #141414') +
                         f" → {1.05 / (lin(20) + 0.05):.1f}:1 (el fondo medido queda fuera de la caja)")
        cont[f"{t['txt']} (c{a}–c{b}, medido en c{n})"] = c
    out['contraste_textos'] = cont
    # degradé
    out['degrade'] = {k: v for k, v in json.load(open(T2 / 'degrade.json')).items() if k != 'por_cuadro'}
    # sonoridad momentánea cada 100 ms y por tramo (las dos versiones; y v01 completa para comparar)
    mom = {}
    for k, nombre in NOMBRES.items():
        mm = momentanea(MAS / nombre)
        json.dump(mm, open(EVID / f'sonoridad_momentanea_100ms_{k}.json', 'w'), indent=0)
        mom[k] = momentanea_tramos(mm, TRAMOS_M)
    v1 = momentanea(U.EXP / U.NOMBRES_V01['completa']) if hasattr(U, 'NOMBRES_V01') else None
    if v1:
        mom['completa_v01'] = momentanea_tramos(v1, TRAMOS_M)
    out['sonoridad_momentanea_por_tramo'] = mom
    # huecos antes de los drops: RMS por 20 ms en 1,60–1,85 y 6,40–6,65 (completa)
    a = U.audio_np(f0).mean(1)
    hue = {}
    for t0, t1 in ((1.60, 1.85), (6.40, 6.65)):
        v = [round(float(20 * np.log10(np.sqrt((a[int(t * 48000):int((t + .02) * 48000)] ** 2).mean()) + 1e-9)), 1)
             for t in np.arange(t0, t1 - 1e-6, 0.02)]
        hue[f'{t0:.2f}–{t1:.2f}'] = dict(zip([f'{t:.2f}' for t in np.arange(t0, t1 - 1e-6, 0.02)], v))
    out['huecos_rms_20ms_dbfs'] = hue
    out['tonales'] = json.load(open(T2 / 'tonales.json'))
    out['tonales_mezcla_sinmusica_1.80-4.80'] = json.load(open(T2 / 'audio' / 'tonales_sinmusica_1.80-4.80.json'))
    return out


def etapa_control():
    import shutil
    U.NOMBRES_V01 = dict(completa='ROCCE_FMT03_BLANCA_O_NEGRA_v01.mp4')
    EVID.mkdir(parents=True, exist_ok=True)
    rep = U.control(NOMBRES, EVID, [54, 144, 198, 234], NF - 1, TRAMOS, ASS, U.TEXTOS, [0.5, 1.0, 5.0, 8.0, 9.0],
                    extra=extra_v02, carpeta=MAS)
    for f in ('degrade.json', 'contraste_decidi.json', 'tonales.json', 'espectro_7793_usado_v01_1.17-4.17.png',
              'espectro_7824_alternativa_6.00-9.00.png', 'espectro_7793_0.80-2.30_detalle.png'):
        shutil.copy2(T2 / f, EVID / f)
    for k in ('completa', 'sinmusica'):
        shutil.copy2(T2 / 'audio' / f'fmt03_{k}_eventos.json', EVID / f'audio_eventos_{k}.json')
    shutil.copy2(T / 'planos.json', EVID / 'planos.json')
    # tiras: «Decidí…» con el máster v01 y v02 en c0, c30 y c45 (texto quemado), al ancho del teléfono y 1:1
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(U.FONT, 24)
    m1 = U.EXP / 'ROCCE_FMT03_BLANCA_O_NEGRA_v01.mp4'; m2 = MAS / NOMBRES['completa']
    filas = []
    for n in (0, 30, 45):
        a1 = U.leer(m1, 1080, 1920, n0=n, n1=n)[0]; a2 = U.leer(m2, 1080, 1920, n0=n, n1=n)[0]
        filas.append((n, a1, a2))
    W_ = Image.new('RGB', (2 * 1082, 3 * 422), (30, 30, 30)); d = ImageDraw.Draw(W_)
    for i, (n, a1, a2) in enumerate(filas):
        for j, a_ in enumerate((a1, a2)):
            W_.paste(Image.fromarray(a_[180:600]), (j * 1082, i * 422))
            d.rectangle([j * 1082, i * 422, j * 1082 + 210, i * 422 + 32], fill=(0, 0, 0))
            d.text((j * 1082 + 6, i * 422 + 3), f"{'v01' if j == 0 else 'v02'} c{n} 1:1", font=fnt, fill=(255, 255, 0))
    W_.save(EVID / 'decidi_v01_v02_c0_c30_c45_1a1.jpg', quality=92)
    t3 = Image.new('RGB', (2 * 362, 3 * 642), (30, 30, 30)); d = ImageDraw.Draw(t3)
    for i, (n, a1, a2) in enumerate(filas):
        for j, a_ in enumerate((a1, a2)):
            t3.paste(Image.fromarray(a_).resize((360, 640), Image.LANCZOS), (j * 362, i * 642))
            d.text((j * 362 + 6, i * 642 + 600), f"{'v01' if j == 0 else 'v02'} c{n} 360 px", font=fnt, fill=(255, 255, 0))
    t3.save(EVID / 'decidi_v01_v02_ancho_telefono_360px.jpg', quality=92)
    # el degradé se retira cuando la remera sube hacia el lente (c44–c49 del máster)
    U.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', str(m2), '-vf',
           f"scale=300:-2,drawtext=fontfile={U.FONT}:text='c%{{eif\\:n\\:d}}':x=4:y=4:fontsize=20:fontcolor=yellow:"
           f"box=1:boxcolor=black,select='between(n\\,44\\,49)',tile=6x1:padding=2", '-fps_mode', 'vfr', '-frames:v', '1',
           str(EVID / 'master_c44-c49_degrade_se_retira.jpg')])
    json.dump(rep, open(EVID / 'control.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k not in ('archivos', 'tonales', 'color', 'mediciones')},
                     ensure_ascii=False)[:5000])
    for k, v in rep['archivos'].items():
        print(k, v['bytes'], v['sha256'], v['md5_video'], v['md5_audio'], v['sonoridad'], v['video']['cuadros'],
              v['video']['duracion'], v['audio']['duracion'], v['decodifica_completo'], v['marcas_gps_o_ubicacion'])


# =====================================================================================================
# etapa 6 · entrega (fmt03.entregar: no sobrescribe; verifica bytes, sha256 y md5 de flujos de las copias)
# =====================================================================================================
def etapa_entregar():
    r = U.entregar(NOMBRES, MAS, EVID, U.PIEZA)
    json.dump(r, open(T2 / 'entrega.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    {'tonales': etapa_tonales, 'degrade': etapa_degrade, 'contraste': contraste_texto, 'audio': etapa_audio,
     'master': etapa_master, 'control': etapa_control, 'entregar': etapa_entregar}[etapa]()
