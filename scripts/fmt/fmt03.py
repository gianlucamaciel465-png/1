#!/usr/bin/env python3
"""FMT-03 · «¿Blanca o Negra?» · receta del máster v01 (Pedro, 17/11/2026).

Guion: piezas/FMT_tanda_formatos/FMT-03_blanca_o_negra/01_fede_guion_G1.md (G1) + 02_roma_aprobacion_G1.md.
Usa scripts/fmt/video.py y scripts/fmt/sonido.py sin modificarlos. Lo nuevo (hojas con cuadro de fuente, medición
de estampados con numpy) vive acá; fmt01.py lo importa.

Etapas (cada una se corre por separado, con nice):
  python fmt03.py hojas     -> hojas cada 0,1 s de los tramos estimados (cuadro y tiempo de la FUENTE impresos)
  python fmt03.py medir     -> mediciones con numpy (tapado del lente, primera tela de 7793, márgenes de ventanas)
  python fmt03.py planos    -> sub-planos + composición de la pantalla dividida + unión
  python fmt03.py audio     -> mezcla completa y mezcla sin música (−14 LUFS, pico ≤ −1 dBTP)
  python fmt03.py master    -> textos + codificación de los dos MP4 en EXPORTACIONES/
  python fmt03.py control   -> evidencia (hoja de contacto, cortes, ffprobe, niveles, md5)
"""
import json, math, os, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V  # noqa: E402

R = Path('/home/user/1')
T = R / 'TRABAJO/fmt/fmt03'
FONT = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
FPS = 30


# =====================================================================================================
# utilidades nuevas (no están en video.py)
# =====================================================================================================
def run(cmd):
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode:
        raise RuntimeError(' '.join(map(str, cmd)) + '\n' + r.stderr.decode(errors='replace')[-3000:])
    return r.stdout


def hoja_src(toma, n0, n1, salida, cada=3, ancho=270, cols=8, caja=None, rot=''):
    """Hoja de los cuadros n0..n1 (índice real del cuadro decodificado de la FUENTE) cada `cada` cuadros.
    Imprime «c<n> <ms>» de la fuente. caja=(x,y,w,h) en coordenadas naturales para ver un recorte."""
    src = V._src(toma)
    pre = V.color(toma)
    if caja:
        x, y, w, h = caja
        pre += f',crop={w}:{h}:{x}:{y}'
    tot = (n1 - n0) // cada + 1
    filas = math.ceil(tot / cols)
    txt = f"{rot}c%{{eif\\:n\\:d}} %{{eif\\:t*1000\\:d}}ms"
    vf = (f"{pre},scale={ancho}:-2,drawtext=fontfile={FONT}:text='{txt}':x=4:y=4:fontsize={max(13, ancho // 14)}:"
          f"fontcolor=yellow:box=1:boxcolor=black@0.7,select='between(n\\,{n0}\\,{n1})*not(mod(n-{n0}\\,{cada}))',"
          f"tile={cols}x{filas}:padding=2:color=0x202020")
    run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', str(src), '-an', '-vf', vf, '-frames:v', '1',
         '-fps_mode', 'vfr', str(salida)])
    return salida


def leer(src, w, h, n0=None, n1=None, vf_pre='', ss=None, t=None):
    """Cuadros RGB (N×h×w×3, uint8) de un archivo. Con n0/n1: índices reales de cuadro de la fuente."""
    vf = (vf_pre + ',' if vf_pre else '')
    if n0 is not None:
        vf += f"select='between(n\\,{n0}\\,{n1})',"
    vf += f'scale={w}:{h}:flags=area,format=rgb24'
    cmd = ['nice', '-n', '10', 'ffmpeg', '-v', 'error']
    if ss is not None:
        cmd += ['-ss', f'{ss:.4f}']
    cmd += ['-i', str(src)]
    if t is not None:
        cmd += ['-t', f'{t:.4f}']
    cmd += ['-an', '-vf', vf, '-fps_mode', 'passthrough', '-f', 'rawvideo', '-']
    a = np.frombuffer(run(cmd), np.uint8)
    return a.reshape(-1, h, w, 3)


def tiempos_src(toma):
    """pts (s) de cada cuadro de video de la fuente."""
    out = run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=pts_time', '-of', 'csv=p=0',
               str(V._src(toma))]).decode().split()
    return [float(x.strip(',')) for x in out if x.strip(',')]


_PTS = {}


def desde_cuadro(toma, n):
    """segundo de búsqueda que hace que el primer cuadro del plano sea EXACTAMENTE el cuadro n de la fuente
    (-ss descarta los cuadros con pts < ss: se busca 0,5 ms antes del pts del cuadro)."""
    if toma not in _PTS:
        _PTS[toma] = tiempos_src(toma)
    return _PTS[toma][n] - 0.0005


def plano_n(toma, n0, nf, salida, caja=None, post=None):
    """video.plano sin acercamiento, definido por cuadro de fuente (n0) y cantidad de cuadros (nf)."""
    d = desde_cuadro(toma, n0)
    p = V.plano(toma, d, d + nf / FPS, salida, caja=caja, post=post)
    assert p['cuadros'] == nf, (p, nf)
    p.update(n0=n0)
    return p


def plano_z(toma, n0, zs, cxs, cys, salida, caja=None, post=None, grano=0.0):
    """Acercamiento real cuadro a cuadro. Motivo: el filtro crop de FFmpeg 6.1 evalúa w/h una sola vez, así que
    video.plano(z0 != z1) no cambia el tamaño de la ventana (también lo detectó el Pedro de FMT-04). Se decodifica con la
    MISMA cadena de color de video.py (V.color) y fps=30, se recorta con caja subpíxel y Lanczos (PIL) sobre los planos
    Y, U y V en yuv444p (sin conversión de matriz) y se codifica con ENC_INT, igual que los intermedios de video.py.
    zs, cxs, cys: zoom y centro (coordenadas naturales) por cuadro; la ventana se limita a la caja.
    grano: sigma (niveles de 8 bits) de un grano fino en luma, proporcional a (Z−1)/(Zmáx−1), para que los bloques
    del HEVC original no se vean al ampliar tela negra."""
    rng = np.random.default_rng(7)
    zmax = max(zs)
    from PIL import Image
    nw, nh = V.TOMAS[toma]['nat']
    x0, y0, cw, ch = caja or (0, 0, nw, nh)
    nf = len(zs)
    cxs = cxs if isinstance(cxs, (list, tuple)) else [cxs] * nf
    cys = cys if isinstance(cys, (list, tuple)) else [cys] * nf
    d = desde_cuadro(toma, n0)
    dec = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-ss', f'{d:.4f}', '-i', str(V._src(toma)),
                            '-t', f'{nf / FPS + 0.2:.4f}', '-an', '-vf', V.color(toma) + f',fps={FPS},format=yuv444p',
                            '-frames:v', str(nf), '-f', 'rawvideo', '-pix_fmt', 'yuv444p', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv444p',
                            '-s', f'{V.W}x{V.H}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-i', '-',
                            *(['-vf', post] if post else []), *V.ENC_INT, str(salida)], stdin=subprocess.PIPE)
    fs = nw * nh * 3
    ventanas = []
    for k in range(nf):
        b = dec.stdout.read(fs)
        if len(b) < fs:
            break
        fr = np.frombuffer(b, np.uint8).reshape(3, nh, nw)
        Z = max(1.0, round(zs[k], 6)); w, h = cw / Z, ch / Z
        x = min(max(cxs[k] - w / 2, x0), x0 + cw - w); y = min(max(cys[k] - h / 2, y0), y0 + ch - h)
        ventanas.append([round(Z, 4), round(x, 1), round(y, 1), round(w, 1), round(h, 1)])
        out = np.empty((3, V.H, V.W), np.uint8)
        for c in range(3):
            out[c] = np.asarray(Image.fromarray(fr[c]).resize((V.W, V.H), Image.LANCZOS, box=(x, y, x + w, y + h)))
        if grano and zmax > 1:
            sg = grano * (Z - 1) / (zmax - 1)
            if sg > 0.05:
                out[0] = np.clip(out[0] + rng.normal(0, sg, out[0].shape), 16, 235).astype(np.uint8)
        enc.stdin.write(out.tobytes())
    dec.stdout.close(); dec.wait()
    enc.stdin.close(); enc.wait()
    if len(ventanas) != nf or enc.returncode:
        raise RuntimeError(f'plano_z {toma}: {len(ventanas)} cuadros de {nf}')
    return dict(toma=toma, n0=n0, cuadros=nf, salida=str(salida), caja=caja, ventanas=ventanas, post=post)


def seguir_estampado(frames, tipo, roi0, margen=24):
    """Mide el estampado cuadro a cuadro dentro de una ventana (frames: N×h×w×3 RGB a escala de la ventana).
    Founders Privée (el elemento más ancho: da los bordes izquierdo y derecho y el inferior con la raya) se detecta por
    color: celeste en la Blanca (B−R > 20, B−G > 4, L > 105) y gris claro en la Negra (L > 95, sat < 0,2). Se busca
    dentro del recuadro del cuadro anterior agrandado `margen` px (el primero, dentro de roi0 fijado a mano), así el
    cielo y el mar no entran. ROCCÉ (borde superior) se busca en la franja de arriba de Founders: oscuro (L < 85) en
    la Blanca; tono sobre tono en la Negra (L entre la mediana de la tela + 9 y 95).
    Devuelve una lista de dicts con bbox (x0, y0, x1, y1), márgenes y las máscaras."""
    from scipy import ndimage as nd
    res = []
    roi = roi0
    for img in frames:
        H, W = img.shape[:2]
        f = img.astype(np.float32); r, g, b = f[..., 0], f[..., 1], f[..., 2]
        L = 0.2126 * r + 0.7152 * g + 0.0722 * b
        sat = (f.max(-1) - f.min(-1)) / (f.max(-1) + 1)
        if tipo == 'blanca':
            c = (b - r > 20) & (b - g > 4) & (L > 105) & (L < 240)
        else:
            c = (L > 95) & (sat < 0.2)
        x0, y0, x1, y1 = [int(v) for v in roi]
        m = np.zeros_like(c); m[max(0, y0):min(H, y1 + 1), max(0, x0):min(W, x1 + 1)] = True
        c &= m
        c = nd.binary_opening(c, iterations=1)
        lab, n = nd.label(nd.binary_dilation(c, iterations=4))
        s = nd.sum(c, lab, range(1, n + 1))
        c &= np.isin(lab, [i + 1 for i, v in enumerate(s) if v >= 0.10 * s.max()])
        ys, xs = np.nonzero(c)
        bx0, bx1, by0, by1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()); bw = bx1 - bx0
        ya = int(max(0, by0 - 0.40 * bw)); yb = int(by0 + 0.05 * bw)
        band = L[ya:yb, bx0:bx1]
        if tipo == 'blanca':
            d = nd.binary_opening(band < 85, iterations=1)
            ys2, xs2 = np.nonzero(d)
            top = ya + int(np.percentile(ys2, 0.5)) if len(ys2) else by0
        else:
            # ROCCÉ tono sobre tono no se separa bien de los pliegues por umbral: borde superior CONSERVADOR = toda la
            # franja de 0,40 × ancho de Founders por encima (en las hojas ROCCÉ siempre queda adentro de esa franja)
            d = np.zeros_like(band, bool)
            top = ya
        bb = (bx0, min(top, by0), bx1, by1)
        res.append(dict(bbox=bb, founders=(bx0, by0, bx1, by1), izq=bb[0], der=W - 1 - bb[2], arr=bb[1],
                        abj=H - 1 - bb[3], mask=c, banda=(bx0, ya, bx1, yb), roc=d))
        roi = (bx0 - margen, by0 - margen, bx1 + margen, by1 + margen)
    return res


# =====================================================================================================
# etapa 1 · hojas cada 0,1 s de los tramos estimados
# =====================================================================================================
def etapa_hojas():
    H = T / 'hojas'
    # 7824 3,6–4,5 s (fuente ≈ 29,97 cps: c108–c135) y 5,1–5,6 (tapado del lente)
    hoja_src('IMG_7824', 105, 138, H / '7824_3.5-4.6.jpg', cada=3)
    hoja_src('IMG_7824', 150, 168, H / '7824_5.0-5.6_c1.jpg', cada=1, ancho=216, cols=10)
    # 7793 1,0–1,7 (c30–c51), cada cuadro
    hoja_src('IMG_7793', 30, 52, H / '7793_1.0-1.7_c1.jpg', cada=1, ancho=216, cols=12)
    # 7996 c60–c85, cada cuadro; y 0,8–2,6 cada 0,1 s para la revisión de quién tira
    hoja_src('IMG_7996', 60, 85, H / '7996_c60-c85_c1.jpg', cada=1, ancho=216, cols=13)
    hoja_src('IMG_7996', 24, 78, H / '7996_0.8-2.6.jpg', cada=3, ancho=270, cols=10)
    # 7857 c9–c30, cada cuadro
    hoja_src('IMG_7857', 9, 30, H / '7857_c9-c30_c1.jpg', cada=1, ancho=216, cols=11)
    # 7857 1,7–4,1 (ventana izquierda) y 7793 2,4–4,8 (ventana derecha) cada 0,1 s, recortadas como en el máster
    hoja_src('IMG_7857', 51, 123, H / '7857_ventana_1.7-4.1.jpg', cada=3, ancho=180, cols=13, caja=(0, 240, 1800, 3200))
    hoja_src('IMG_7793', 72, 144, H / '7793_ventana_2.4-4.8.jpg', cada=3, ancho=180, cols=13)


# =====================================================================================================
# etapa 3 · planos (tabla §2 del guion, con los cuadros fijados en las hojas cada 0,1 s)
# =====================================================================================================
P = T / 'planos'
FULL = (0, 0, 2160, 3840)
VENT = 'scale=540:960:flags=lanczos,setsar=1'
# 2a+2b1 (7793 c35–c50, 16 cuadros, un solo plano continuo): DESVÍO medido. Con z 3,0 en (1760, 2760) los cuadros
# c54–c56 muestran «Foun» completo arriba y el brazo y la baranda a la izquierda (gris 7,6 %, claro 6,4 %). Con umbral
# L < 35 la ventana 9:16 más grande que es solo tela negra pide z ≥ 4,2 / 3,8 / 3,5 en c35 / c36 / c37, pegada al borde
# derecho de la toma (etapa medir). Con z 4,3 quedaba además una astilla clara de 31×76 px en el borde izquierdo de c54
# (mano/baranda): se sube a z 4,6. Apertura a velocidad percibida constante, Z_k = 4,6^(1 − k/15) (4,60 → 1,00), con la
# ventana anclada al borde derecho de la toma y el borde inferior bajando con suavidad (3407 → 3840) hasta el cuadro entero.
Z2 = [4.6 ** (1 - k / 15) for k in range(16)]
C2Y = [3840 - (3840 - 3407) * (1 - k / 15) ** 3.34 - 3840 / z / 2 for k, z in enumerate(Z2)]
# ventana izquierda de la pantalla dividida: DESVÍO medido. 7857 c51–c122 deja la «F» a 8–18 px del borde izquierdo de la
# ventana en c53–c65 (la «F» está a ≈27 px del borde de la toma: ninguna caja lo arregla). Ningún tramo de 72 cuadros de
# 7857 con caja fija da ≥ 20 px. Se usa c66–c137 (2,200–4,567) con un empuje lento dentro de la ventana: ancho de caja
# 1620 → 1300 px (anclado al borde izquierdo de la toma, z 1,111 → 1,385 sobre la caja del guion).
CW_IZQ = [1620 + (1300 - 1620) * k / 71 for k in range(72)]
# 4a/4b1: DESVÍO medido (ver hoja de máster): en 7857 c15–c17 el chico ocupa solo el ≈35–40 % izquierdo del cuadro;
# con z 1,3 centrado no «llena el cuadro». Se aplica la misma técnica aprobada para 7793 (§0.2): entrar adentro de la
# espalda blanca y abrir a 1,0, siguiendo la espalda (ventana anclada a la izquierda).
Z4A = [2.6, 2.4, 2.2]
Z4B1 = [1.9, 1.7, 1.5, 1.35, 1.22, 1.12, 1.05, 1.01]


def lista_planos():
    return [
        # id, función, args
        ('1a', 'n', dict(toma='IMG_7824', n0=111, nf=45, caja=FULL)),                       # 3,702–5,168
        ('1b', 'z', dict(toma='IMG_7824', n0=156, zs=[1 + 2.14 * k / 9 for k in range(9)], cxs=1080, cys=3140,
                         post='fade=t=out:st=0.2333:d=0.0333')),                          # 5,202–5,469
        ('2a', 'z', dict(toma='IMG_7793', n0=35, zs=Z2, cxs=2160, cys=C2Y,
                         grano=1.6)),                                                      # 1,167–1,667
        ('2b2', 'n', dict(toma='IMG_7793', n0=51, nf=74, caja=FULL)),                       # 1,700–4,133
        ('3a', 'n', dict(toma='IMG_7996', n0=24, nf=50, caja=FULL)),                        # 0,800–2,433
        ('3b', 'z', dict(toma='IMG_7996', n0=74, zs=[1 + 0.35 * k / 4 for k in range(4)], cxs=1400, cys=3300,
                         post='avgblur=sizeX=1:sizeY=36')),                                # 2,467–2,567
        ('4a', 'z', dict(toma='IMG_7857', n0=15, zs=Z4A, cxs=420, cys=2200, post='avgblur=sizeX=1:sizeY=24')),
        ('4b1', 'z', dict(toma='IMG_7857', n0=18, zs=Z4B1, cxs=420, cys=2200)),
        ('4b2', 'n', dict(toma='IMG_7857', n0=26, nf=25, caja=FULL)),                       # 0,867–1,667
    ]


def composicion(izq, der, salida, nf=72):
    """§6 del guion: fondo #0E0E10, ventanas 540×960 en (0,330) y (540,330), línea blanca de 4 px en x 538."""
    V.sh(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
          f'color=c=0x0E0E10:s=1080x1920:r=30:d={nf / FPS}', '-i', str(izq), '-i', str(der), '-filter_complex',
          '[0][1]overlay=0:330[a];[a][2]overlay=540:330,drawbox=x=538:y=330:w=4:h=960:color=white:t=fill,'
          'format=yuv420p,setsar=1', '-frames:v', str(nf), *V.ENC_INT, str(salida)])
    return dict(toma='composición', cuadros=nf, salida=str(salida))


def etapa_planos():
    P.mkdir(parents=True, exist_ok=True)
    reg = []
    for pid, tipo, a in lista_planos():
        out = P / f'{pid}.mp4'
        if tipo == 'n':
            p = plano_n(a['toma'], a['n0'], a['nf'], out, caja=a.get('caja'), post=a.get('post'))
        else:
            p = plano_z(a['toma'], a['n0'], a['zs'], a['cxs'], a['cys'], out, caja=a.get('caja'), post=a.get('post'),
                        grano=a.get('grano', 0.0))
        p['id'] = pid; reg.append(p); print(pid, p['cuadros'], flush=True)
    izq = plano_z('IMG_7857', 66, [1800 / cw for cw in CW_IZQ], 0, 1840, P / '5_izq.mp4', caja=(0, 240, 1800, 3200),
                  post=VENT)                                                                  # 2,200–4,567
    der = plano_n('IMG_7793', 72, 72, P / '5_der.mp4', caja=FULL, post=VENT)                   # 2,400–4,767
    c = composicion(izq['salida'], der['salida'], P / '5.mp4'); c['id'] = '5'
    reg += [dict(izq, id='5_izq'), dict(der, id='5_der')]
    n = V.unir([p for p in reg if p['id'] not in ('5_izq', '5_der')] + [c], T / 'fmt03_video.mp4')
    reg.append(dict(c))
    json.dump(dict(cuadros=n, planos=reg), open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1)
    print('total', n)


# =====================================================================================================
# etapa 2 · mediciones con numpy (sobre los intermedios reales)
# =====================================================================================================
def luma(a):
    return a.astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def dibujar_margenes(frames, res, salida, cada=3, ancho=180, cols=12, rotulo=''):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 22)
    tiles = []
    for k in range(0, len(frames), cada):
        ov = frames[k].copy(); r = res[k]
        ov[r['mask']] = [255, 0, 0]
        bx0, ya, bx1, yb = r['banda']; sub = ov[ya:yb, bx0:bx1]; sub[r['roc']] = [0, 255, 0]
        im = Image.fromarray(ov); d = ImageDraw.Draw(im)
        d.rectangle(list(r['bbox']), outline=(255, 255, 0), width=3)
        d.rectangle([0, 0, im.width - 1, 64], fill=(0, 0, 0))
        d.text((6, 4), f"{rotulo}k{k} i{r['izq']} d{r['der']}", font=fnt, fill=(255, 255, 0))
        d.text((6, 32), f"a{r['arr']} b{r['abj']}", font=fnt, fill=(255, 255, 0))
        tiles.append(im.resize((ancho, round(ancho * im.height / im.width))))
    th = tiles[0].height; filas = math.ceil(len(tiles) / cols)
    W = Image.new('RGB', (cols * (ancho + 2), filas * (th + 2)), (32, 32, 32))
    for i, t in enumerate(tiles):
        W.paste(t, ((i % cols) * (ancho + 2), (i // cols) * (th + 2)))
    W.save(salida, quality=90)


def etapa_medir():
    M = T / 'med'; M.mkdir(exist_ok=True)
    out = {}
    # --- 1) ventanas de la pantalla dividida (c234–c305): márgenes del estampado en px de la ventana 540×960 ---
    for nombre, tipo, roi0, c0 in (('5_izq', 'blanca', (0, 400, 539, 720), 66), ('5_der', 'negra', (0, 380, 539, 600), 72)):
        fr = leer(P / f'{nombre}.mp4', 540, 960)
        res = seguir_estampado(fr, tipo, roi0)
        dibujar_margenes(fr, res, M / f'margenes_{nombre}.jpg', rotulo=f'{nombre} ')
        filas = [dict(master=234 + k, fuente=c0 + k, bbox=r['bbox'], izq=r['izq'], der=r['der'], arr=r['arr'], abj=r['abj'])
                 for k, r in enumerate(res)]
        mins = {k: min(f[k] for f in filas) for k in ('izq', 'der', 'arr', 'abj')}
        peor = {k: min(filas, key=lambda f: f[k])['master'] for k in mins}
        out[nombre] = dict(minimos_px=mins, cuadro_master_del_minimo=peor, por_cuadro=filas)
        print(nombre, 'mínimos', mins, 'en', peor)
    # --- 2) tapado del lente: 1b (c45–c53) y primera tela de 7793 (c54–c56) en el video unido ---
    v = leer(T / 'fmt03_video.mp4', 540, 960, n0=45, n1=60)
    tap = []
    for k, f in enumerate(v):
        Lm = luma(f); sat = (f.max(-1).astype(np.float32) - f.min(-1)) / (f.max(-1).astype(np.float32) + 1)
        tap.append(dict(cuadro=45 + k, negro_puro_pct=round(float((Lm < 12).mean() * 100), 2),
                        tela_negra_pct=round(float((Lm < 45).mean() * 100), 2),
                        gris_letras_pct=round(float(((Lm > 90) & (sat < 0.2)).mean() * 100), 3),
                        cielo_pct=round(float(((Lm > 150) & (sat < 0.2)).mean() * 100), 3),
                        luma_media=round(float(Lm.mean()), 1)))
        print(tap[-1])
    out['tapado_lente'] = tap
    # --- 3) cuadros repetidos o saltos dentro del video unido (diferencia media entre cuadros consecutivos) ---
    a = leer(T / 'fmt03_video.mp4', 270, 480).astype(np.float32)
    dif = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2, 3))
    out['diferencia_consecutiva'] = [round(float(x), 2) for x in dif]
    bajos = [(i + 1, round(float(x), 2)) for i, x in enumerate(dif) if x < 0.8]
    print('cuadros casi iguales al anterior (c, dif):', bajos)
    json.dump(out, open(M / 'mediciones.json', 'w'), ensure_ascii=False, indent=1)


# =====================================================================================================
# etapa 4 · sonido (§5 del guion; música TEMP propia 100 BPM La menor; foley de tela PROVISORIO)
# =====================================================================================================
DUR = 306 / FPS   # 10,200 s


def ambientes(m):
    # 7824: el espectro de 3,70–5,50 es casi solo viento/retumbo < 400 Hz (espectros_fmt03.png) → alternativa del guion:
    # −10 dB y pasa-altos 200 Hz.
    m.ambiente('IMG_7824', 3.70, 0.0, 1.80, -10, hp=200)
    # 7793 a +8 dB: piso de ruido medido −37 dBFS (astats, hp 150) → −29 dBFS, por debajo del piso de 7824/7996/7857
    # (−24 a −26 dBFS): no aparece ruido nuevo; se usa 7793 (no la alternativa 7824 6,00).
    m.ambiente('IMG_7793', 1.167, 1.80, 4.80, +8, hp=150, lp=8000)
    m.ambiente('IMG_7996', 0.80, 4.80, 6.60, -4, hp=200)
    m.ambiente('IMG_7857', 1.70, 6.60, 7.80, -6)
    m.ambiente('IMG_7857', 2.90, 7.80, 9.20, -10, fin_fade=.3)
    m.ambiente('IMG_7857', 1.70, 9.20, 10.20, -12, ini_fade=.3, fin_fade=.25)


def foley(m):
    m.tela(0.30, .35, .10)                 # balanceo
    m.tela(0.70, .60, .14)                 # viene hacia la cámara
    m.tela(1.40, .30, .18)                 # la tela contra el lente
    m.barrido(1.80, .30, .18)
    m.tela(4.95, .40, .08)                 # el bollo en la mano
    m.tela(6.133, .25, .22)                # el brazo que tira (c184)
    m.barrido(6.60, .30, .24, sube=False)
    m.tela(6.60, .25, .16)                 # cae puesta
    m.tela(6.90, .50, .08)                 # mano en la nuca
    m.toque(7.80, .16, 2400)               # aparecen las ventanas


def musica(m):
    ch = lambda t0, t1, g=.08: [m.charles(round(t, 3), g) for t in np.arange(t0, t1 - 1e-6, 0.3)]
    # entrada c0–c53
    m.pad(0.0, [45, 48, 52], 1.7, .05, 1000, a=.15)
    for i, t in enumerate((0.0, 0.3, 0.6, 0.9, 1.2, 1.5)):
        m.charles(t, .06 + .03 * i / 5)
    m.campana(0.0, 76, .05)
    m.subida(0.90, 1.70, .16)
    # drop 1 (c54)
    m.bombo(1.8, .9); m.ocho08(1.8, 33, 1.0, .55, glide_desde=40); m.impacto(1.8, .40)
    m.pad(1.8, [45, 48, 52], 2.3, .06, 1400)
    # compás 2
    m.bombo(3.0); m.bombo(3.3, .5); m.palma(2.4); m.palma(3.6); ch(1.8, 4.2)
    m.ocho08(3.0, 33, .5); m.ocho08(3.6, 36, .5)
    # compás 3 (tensión)
    m.bombo(4.2, .8)
    m.pad(4.2, [41, 45, 48], 1.15, .06, 1200); m.pad(5.4, [40, 44, 47], 1.15, .06, 1200)
    ch(4.2, 5.4); m.redoble(5.4, 6.4, .12); m.subida(5.6, 6.5, .14)
    # drop 2 (c198)
    m.bombo(6.6, 1.0); m.impacto(6.6, .55); m.ocho08(6.6, 33, 1.1, .6, glide_desde=40)
    m.pad(6.6, [45, 48, 52, 57], 1.15, .07); ch(6.6, 7.8); m.palma(7.2)
    # pantalla dividida (c234)
    m.bombo(7.8, .75); m.pad(7.8, [48, 52, 55], 1.15, .06); m.ocho08(7.8, 36, .5); m.ocho08(8.4, 40, .5)
    m.palma(8.4); ch(7.8, 9.0)
    # final (c270)
    m.bombo(9.0, .9); m.ocho08(9.0, 33, 1.1, .5); m.pad(9.0, [45, 48, 52, 57], .9, .06, r=.5)
    m.campana(9.0, 76, .07, .9); m.palma(9.6, .25)
    # huecos y final (después de colocar todo lo de 'mus')
    m.silenciar('mus', 1.70, 1.80); m.silenciar('mus', 6.50, 6.60)
    m.fundido('mus', 9.70, 10.20)
    m.fundido('fx', 9.85, 10.20)           # colas de reverberación de la música (van en 'fx'): sin corte seco al final


def etapa_audio():
    from sonido import Mezcla
    A = T / 'audio'; A.mkdir(exist_ok=True)
    m = Mezcla(DUR); ambientes(m); foley(m); musica(m)
    r1 = m.exportar(str(A / 'fmt03_completa.wav'), lufs=-14)
    s = Mezcla(DUR); ambientes(s); foley(s)             # sin música: solo ambiente, tela, barrido y toque
    r2 = s.exportar(str(A / 'fmt03_sinmusica.wav'), lufs=-14)
    print('completa', r1, 'sin música', r2)


# =====================================================================================================
# etapa 5 · textos exactos (§4) + máster
# =====================================================================================================
EXP = R / 'EXPORTACIONES'
NOMBRES = {'completa': 'ROCCE_FMT03_BLANCA_O_NEGRA_v01.mp4', 'sinmusica': 'ROCCE_FMT03_BLANCA_O_NEGRA_SINMUSICA_v01.mp4'}
TEXTOS = [
    dict(t0=0 / FPS, t1=54 / FPS, txt='¿Blanca o Negra?', estilo='Caja', y=236, pop=True),          # c0–c53
    dict(t0=0 / FPS, t1=54 / FPS, txt='Decidí antes del final.', estilo='Nativo', y=330, pop=True),  # c0–c53
    dict(t0=144 / FPS, t1=183 / FPS, txt='¿Y la Blanca?', estilo='CajaN', y=236),                   # c144–c182
    dict(t0=234 / FPS, t1=306 / FPS, txt='¿Blanca o Negra?', estilo='Caja', y=236),                 # c234–c305
    dict(t0=246 / FPS, t1=306 / FPS, txt='link en bio', estilo='Chico', y=1312),                    # c246–c305
]


MAS = T / 'master'


def etapa_master():
    MAS.mkdir(exist_ok=True)
    a = V.ass(TEXTOS, T / 'fmt03_textos.ass')
    for k, nombre in NOMBRES.items():
        V.master(T / 'fmt03_video.mp4', T / 'audio' / f'fmt03_{k}.wav', MAS / nombre, ass_path=a)
        print('->', MAS / nombre)


# =====================================================================================================
# etapa 6 · control y evidencia (genérico: fmt01.py lo usa igual)
# =====================================================================================================
def md5_stream(mp4, sel):
    out = run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-map', f'0:{sel}', '-c', 'copy', '-f', 'md5', '-']).decode()
    return out.strip().split('=')[-1]


def ebur(mp4):
    r = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-nostats', '-i', str(mp4), '-vn', '-af',
                        'ebur128=peak=true:framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True).stderr
    g = lambda k: float([l for l in r.splitlines() if l.strip().startswith(k)][-1].split()[1])
    return dict(lufs_integrado=g('I:'), lra=g('LRA:'), pico_dbtp=g('Peak:'))


def audio_np(mp4):
    raw = run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-vn', '-f', 'f32le', '-ac', '2', '-ar', '48000', '-'])
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def niveles_tramos(a, tramos, sr=48000):
    """tramos: lista (nombre, t0, t1). RMS y pico (dBFS) por tramo + ventanas de 100 ms por debajo de −50 dBFS."""
    db = lambda x: round(float(20 * np.log10(max(x, 1e-9))), 1)
    out = []
    for nom, t0, t1 in tramos:
        seg = a[int(t0 * sr):int(t1 * sr)]
        out.append(dict(tramo=nom, t0=t0, t1=t1, rms_dbfs=db(np.sqrt((seg ** 2).mean())), pico_dbfs=db(np.abs(seg).max())))
    w = int(0.1 * sr)
    v = [db(np.sqrt((a[k:k + w] ** 2).mean())) for k in range(0, len(a) - w + 1, w)]
    silencios = [round(k * 0.1, 1) for k, x in enumerate(v) if x < -50]
    return out, v, silencios


def cuadros_corte(mp4, cortes, carpeta, ultimo):
    """cuadros n−1, n, n+1 de cada corte + c0 y el último, a tamaño real (JPG q2) y una tira por corte."""
    carpeta.mkdir(parents=True, exist_ok=True)
    ns = sorted({0, ultimo} | {k for c in cortes for k in (c - 1, c, c + 1)})
    sel = '+'.join(f'eq(n\\,{k})' for k in ns)
    run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-vf', f"select='{sel}'", '-fps_mode', 'vfr',
         '-q:v', '2', str(carpeta / 'tmp_%03d.jpg')])
    for k, n in enumerate(ns):
        (carpeta / f'tmp_{k + 1:03d}.jpg').rename(carpeta / f'c{n:03d}.jpg')
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 26)
    for c in cortes:
        ims = [Image.open(carpeta / f'c{k:03d}.jpg').resize((360, 640)) for k in (c - 1, c, c + 1)]
        W = Image.new('RGB', (3 * 362, 640), (30, 30, 30))
        for j, im in enumerate(ims):
            d = ImageDraw.Draw(im); d.rectangle([0, 0, 120, 34], fill=(0, 0, 0)); d.text((6, 3), f'c{c - 1 + j}', font=fnt, fill=(255, 255, 0))
            W.paste(im, (j * 362, 0))
        W.save(carpeta / f'tira_corte_c{c:03d}.jpg', quality=90)
    return ns


def hoja_contacto(mp4, salida, cada=15, cols=7, ancho=240):
    n = int(run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                 'stream=nb_read_frames', '-of', 'csv=p=0', str(mp4)]).decode().strip())
    tot = (n - 1) // cada + 1; filas = math.ceil(tot / cols)
    run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-vf',
         f"scale={ancho}:-2,drawtext=fontfile={FONT}:text='c%{{eif\\:n\\:d}} %{{pts\\:flt}}s':x=4:y=4:fontsize=16:"
         f"fontcolor=yellow:box=1:boxcolor=black@0.7,select='not(mod(n\\,{cada}))',tile={cols}x{filas}:padding=2",
         '-frames:v', '1', '-fps_mode', 'vfr', '-q:v', '3', str(salida)])
    return n


def cajas_texto(ass_path, tiempos, W=1080, H=1920):
    """renderiza el .ass sobre negro (libass, mismas fuentes que el máster) y devuelve la caja de lo dibujado."""
    out = {}
    for t in tiempos:
        r = run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}:d=11', '-vf',
                 f"subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter,trim=start={t:.4f},setpts=PTS-STARTPTS,"
                 f"format=gray", '-frames:v', '1', '-f', 'rawvideo', '-'])
        a = np.frombuffer(r, np.uint8).reshape(H, W)
        ys, xs = np.nonzero(a > 8)
        out[f'{t:.3f}'] = None if len(ys) == 0 else [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    return out


def control(nombres, evid, cortes, ultimo, tramos, ass_path, textos, tiempos_texto, extra=None, carpeta=None):
    import shutil
    carpeta = carpeta or MAS
    evid.mkdir(parents=True, exist_ok=True)
    rep = dict(fecha='2026-11-17', archivos={})
    for k, nombre in nombres.items():
        f = carpeta / nombre
        err = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(f), '-f', 'null', '-'],
                             capture_output=True, text=True).stderr.strip()
        pj = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(f)]))
        json.dump(pj, open(evid / f'ffprobe_{k}.json', 'w'), indent=1)
        cuerpo = f.read_bytes()
        gps = [m for m in (b'ISO6709', b'location', b'com.apple.quicktime') if m in cuerpo]
        a = audio_np(f)
        niv, v100, sil = niveles_tramos(a, tramos)
        vs = [s_ for s_ in pj['streams'] if s_['codec_type'] == 'video'][0]
        au = [s_ for s_ in pj['streams'] if s_['codec_type'] == 'audio'][0]
        import hashlib
        rep['archivos'][k] = dict(
            archivo=str(f), bytes=f.stat().st_size, sha256=hashlib.sha256(cuerpo).hexdigest(),
            md5_video=md5_stream(f, 'v'), md5_audio=md5_stream(f, 'a'),
            decodifica_completo=(err == ''), errores_decodificacion=err[:500],
            video=dict(codec=vs['codec_name'], perfil=vs.get('profile'), nivel=vs.get('level'), pix_fmt=vs['pix_fmt'],
                       ancho=vs['width'], alto=vs['height'], fps=vs['r_frame_rate'], cuadros=int(vs['nb_frames']),
                       duracion=float(vs['duration']), color=[vs.get('color_range'), vs.get('color_space'),
                                                              vs.get('color_transfer'), vs.get('color_primaries')]),
            audio=dict(codec=au['codec_name'], perfil=au.get('profile'), hz=int(au['sample_rate']), canales=au['channels'],
                       duracion=float(au['duration'])),
            duracion_formato=float(pj['format']['duration']), etiquetas_formato=pj['format'].get('tags', {}),
            marcas_gps_o_ubicacion=[m.decode() for m in gps],
            sonoridad=ebur(f), niveles_por_tramo=niv, ventanas_100ms_bajo_menos50dbfs=sil,
            rms_100ms=v100)
        print(k, rep['archivos'][k]['sonoridad'], 'video', rep['archivos'][k]['md5_video'], 'audio',
              rep['archivos'][k]['md5_audio'], 'gps', gps, 'silencios', sil, flush=True)
    f0 = carpeta / nombres['completa']
    hoja_contacto(f0, evid / 'hoja_contacto_cada_0.5s.jpg')
    cuadros_corte(f0, cortes, evid / 'cortes', ultimo)
    shutil.copy2(ass_path, evid / Path(ass_path).name)
    rep['textos'] = dict(exactos=[t['txt'] for t in textos], cajas_renderizadas=cajas_texto(ass_path, tiempos_texto))
    if extra:
        rep.update(extra())
    json.dump(rep, open(evid / 'control.json', 'w'), ensure_ascii=False, indent=1)
    return rep


def color_parche(img, caja):
    x0, y0, x1, y1 = caja
    p = img[y0:y1, x0:x1].reshape(-1, 3).astype(np.float64)
    L = p @ [0.2126, 0.7152, 0.0722]
    p = p[L >= np.percentile(L, 50)] if L.mean() > 100 else p[L <= np.percentile(L, 50)]   # tela lisa: sin sombras/brillos
    m = p.mean(0)
    return dict(rgb=[round(x, 1) for x in m], b_menos_r=round(m[2] - m[0], 1), g_menos_r=round(m[1] - m[0], 1),
                b_sobre_r=round(m[2] / max(m[0], 1), 3))


def extra_fmt03():
    from PIL import Image
    S = T / 'ctrl'; S.mkdir(exist_ok=True)
    f0 = MAS / NOMBRES['completa']
    fr = {n: leer(f0, 1080, 1920, n0=n, n1=n)[0] for n in (30, 100, 165, 220)}
    prod = {}
    for nom in ('blanca_frente_detalle_estampado', 'negra_frente_detalle_estampado', 'blanca_espalda_estudio',
                'negra_espalda_estudio'):
        V.foto_srgb(R / 'PRODUCTO' / f'{nom}.jpg', S / f'{nom}_srgb.png')
        prod[nom] = np.asarray(Image.open(S / f'{nom}_srgb.png').convert('RGB'))
    col = dict(
        producto_blanca_frente=color_parche(prod['blanca_frente_detalle_estampado'], (400, 150, 1100, 500)),
        producto_blanca_espalda=color_parche(prod['blanca_espalda_estudio'], (292, 1316, 877, 1755)),
        master_blanca_7857_c220=color_parche(fr[220], (180, 1290, 660, 1650)),
        master_blanca_7996_c165_bollo_sol=color_parche(fr[165], (270, 990, 330, 1080)),
        master_blanca_7996_c165_bollo_sombra=color_parche(fr[165], (100, 1150, 320, 1290)),
        producto_negra_frente=color_parche(prod['negra_frente_detalle_estampado'], (378, 1550, 1134, 1950)),
        producto_negra_espalda=color_parche(prod['negra_espalda_estudio'], (292, 1228, 877, 1462)),
        master_negra_7824_c30=color_parche(fr[30], (240, 1230, 600, 1440)),
        master_negra_7793_c100=color_parche(fr[100], (360, 1200, 900, 1560)))
    # celeste de Founders Privée (tono): producto (espalda de estudio) contra el máster (7857 c220)
    def celeste(img, caja):
        x0, y0, x1, y1 = caja; p = img[y0:y1, x0:x1].reshape(-1, 3).astype(np.float64)
        m = (p[:, 2] - p[:, 0] > 20) & (p[:, 2] - p[:, 1] > 4)
        q = p[m].mean(0); import colorsys
        h, l_, s_ = colorsys.rgb_to_hls(*(q / 255))
        return dict(pixeles=int(m.sum()), rgb=[round(x, 1) for x in q], tono_grados=round(h * 360, 1))
    col['celeste_producto_espalda'] = celeste(prod['blanca_espalda_estudio'], (100, 800, 1100, 1300))
    col['celeste_master_7857_c220'] = celeste(fr[220], (0, 900, 1080, 1250))
    med = json.load(open(T / 'med' / 'mediciones.json'))
    # §8.1 sobre el MÁSTER (con textos): c53 negro y c54–c56 solo tela negra
    m = leer(f0, 540, 960, n0=52, n1=57)
    master_tapado = []
    for k, f in enumerate(m):
        Lm = luma(f); sat = (f.max(-1).astype(np.float32) - f.min(-1)) / (f.max(-1).astype(np.float32) + 1)
        sin_texto = Lm[110:200]   # franja de textos del gancho (y 220–400 en 1080×1920) aparte
        master_tapado.append(dict(cuadro=52 + k, negro_pct_cuadro_entero=round(float((Lm < 20).mean() * 100), 2),
                                  tela_negra_pct_cuadro_entero=round(float((Lm < 45).mean() * 100), 2),
                                  gris_o_claro_pct_fuera_de_textos=round(float(((np.r_[Lm[:110], Lm[200:]] > 90)).mean() * 100), 3)))
    # §8.3: ningún texto adentro de las ventanas (y 330–1290) en c234–c305
    t9 = T / 'ctrl' / 'textos_t9.raw'
    r = run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=black:s=1080x1920:r=30:d=11', '-vf',
             f"subtitles={T / 'fmt03_textos.ass'}:fontsdir=/usr/share/fonts/opentype/inter,trim=start=9.0,setpts=PTS-STARTPTS,format=gray",
             '-frames:v', '1', '-f', 'rawvideo', '-'])
    a = np.frombuffer(r, np.uint8).reshape(1920, 1080)
    filas = np.nonzero((a > 8).any(1))[0]
    bloques = np.split(filas, np.nonzero(np.diff(filas) > 1)[0] + 1)
    return dict(color=col, master_tapado_lente=master_tapado,
                textos_cierre_filas_y=[[int(b[0]), int(b[-1])] for b in bloques],
                textos_cierre_pixeles_en_ventanas=int((a[330:1291] > 8).sum()), mediciones=dict(
        tapado_lente=med['tapado_lente'],
        ventanas_minimos_px={k: med[k]['minimos_px'] for k in ('5_izq', '5_der')},
        ventanas_cuadro_del_minimo={k: med[k]['cuadro_master_del_minimo'] for k in ('5_izq', '5_der')}))


def etapa_control():
    import shutil
    evid = T / 'evidencia_v01'
    tramos = [('1 Negra sostenida + tapa el lente', 0.0, 1.8), ('2 Negra puesta (7793)', 1.8, 4.8),
              ('3 ¿Y la Blanca? tiro (7996)', 4.8, 6.6), ('4 Blanca puesta (7857)', 6.6, 7.8),
              ('5 pantalla dividida + CTA', 7.8, 10.2), ('último 0,5 s', 9.7, 10.2)]
    rep = control(NOMBRES, evid, [54, 144, 198, 234], 305, tramos, T / 'fmt03_textos.ass', TEXTOS,
                  [0.5, 1.0, 5.0, 8.0, 9.0], extra=extra_fmt03)
    M = T / 'med'
    for f in ('margenes_5_izq.jpg', 'margenes_5_der.jpg', 'mediciones.json'):
        shutil.copy2(M / f, evid / f)
    for f in ('7996_arriba_izq_c24-c78.jpg', '7996_0.8-2.6.jpg', '7857_c9-c30_c1.jpg', '7793_1.0-1.7_c1.jpg',
              '7824_5.0-5.6_c1.jpg'):
        shutil.copy2(T / 'hojas' / f, evid / f'hoja_fuente_{f}')
    shutil.copy2(T / 'audio' / 'espectros_fmt03.png', evid / 'espectros_ambientes.png')
    for k in ('completa', 'sinmusica'):
        shutil.copy2(T / 'audio' / f'fmt03_{k}_eventos.json', evid / f'audio_eventos_{k}.json')
    shutil.copy2(T / 'planos.json', evid / 'planos.json')
    print(json.dumps({k: v for k, v in rep.items() if k != 'archivos'}, ensure_ascii=False)[:3000])


# =====================================================================================================
# etapa 7 · entrega: EXPORTACIONES/ + carpeta de la pieza (montaje de red) + evidencia; verificación de copias
# =====================================================================================================
PIEZA = Path('/mnt/project-files/piezas/FMT_tanda_formatos/FMT-03_blanca_o_negra')


def entregar(nombres, carpeta, evid_local, pieza):
    import shutil, time, hashlib
    res = {}
    for k, nombre in nombres.items():
        src = carpeta / nombre
        for dst in (EXP / nombre, pieza / nombre):
            if dst.exists():
                raise RuntimeError(f'{dst} ya existe: no se sobrescribe')
            shutil.copyfile(src, dst)
    ev = pieza / evid_local.name
    if ev.exists():
        raise RuntimeError(f'{ev} ya existe')
    shutil.copytree(evid_local, ev)
    time.sleep(8)                                   # montaje de red: esperar antes de verificar
    for k, nombre in nombres.items():
        src = carpeta / nombre
        ref = dict(bytes=src.stat().st_size, sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                   md5_video=md5_stream(src, 'v'), md5_audio=md5_stream(src, 'a'))
        for dst in (EXP / nombre, pieza / nombre):
            got = dict(bytes=dst.stat().st_size, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
                       md5_video=md5_stream(dst, 'v'), md5_audio=md5_stream(dst, 'a'))
            res[str(dst)] = dict(got, igual_al_original=(got == ref))
            print(dst, got, 'OK' if got == ref else 'DISTINTO')
    n_local = sum(1 for _ in evid_local.rglob('*') if _.is_file()); n_red = sum(1 for _ in ev.rglob('*') if _.is_file())
    res['evidencia'] = dict(carpeta=str(ev), archivos_local=n_local, archivos_red=n_red)
    print('evidencia', n_local, n_red)
    return res


def etapa_entregar():
    r = entregar(NOMBRES, MAS, T / 'evidencia_v01', PIEZA)
    json.dump(r, open(T / 'entrega.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    {'hojas': etapa_hojas, 'planos': etapa_planos, 'medir': etapa_medir, 'audio': etapa_audio, 'master': etapa_master, 'control': etapa_control, 'entregar': etapa_entregar}[etapa]()
