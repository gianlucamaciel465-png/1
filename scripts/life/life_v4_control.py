#!/usr/bin/env python3
"""Roccé Life · V4 «¿Vuelve?» B · control del máster v01 y entrega (Pedro, 25/11/2026).

Se llama desde life_v4.py (`python life_v4.py control` / `entregar`). Lee los dos MP4 de TRABAJO/life2/v4/master y deja
la evidencia en TRABAJO/life2/v4/evidencia_v01:
  · técnica: ffprobe, decodificación completa, sha256, md5 de flujos (ID inmutable), átomos (faststart), GPS,
    ebur128 (integrada, pico real, LRA) + momentánea y niveles por tramo, duración de audio = video;
  · imagen: hoja cada 0,5 s, cuadros de cada corte, cuadros críticos, exposición por paso, continuidad;
  · separación 0–12,50 s (condición 4 de Roma): por cada cuadro del máster, ventana real usada (planos.json) contra las
    remeras seguidas (med/seguimiento.json) con la tolerancia medida a mano; hojas cuadro a cuadro de cada caja sobre
    la toma original; hoja de todos los cuadros 0–377 del máster; detector del logo (ficha de la firma) en cada cuadro;
    croma fuera del texto (B/N);
  · textos: lo visible por cuadro (volcado del DOM del render) contra el guion y las citas contra 02b carácter por
    carácter; distancia texto–remeras en 12,60–15,90;
  · audio: golpes del texto contra el inicio medido en la pista de efectos, tramos sin música, silencio final.
"""
import json, math, hashlib, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/life')
import video as V           # noqa: E402
import fmt03 as U           # noqa: E402
import fmt03_v02 as U2      # noqa: E402
import life_v2 as L2        # noqa: E402
import life_v4 as M         # noqa: E402

T, MAS, EVID, PL, TX, A, MED = M.T, M.MAS, M.EVID, M.PL, M.TX, M.A, M.MED
W, H, FPS, NF, DUR = M.W, M.H, M.FPS, M.NF, M.DUR
FONT = U.FONT
GUION = M.PIEZA / '01_fede_guion_G1_v1.md'
ROMA = M.PIEZA.parent / '07_roma_aprobacion_guiones_t2.md'
FIN_SEP = 374                   # último cuadro que debe estar libre de remera, logo y firma (12,50 s = c375)


def jdump(o, f):
    M.jdump(o, f)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, check=True).stdout


def nice(cmd):
    return ['nice', '-n', '10'] + list(cmd)


def tramos():
    out = []
    for paso, a, b, fn in M.PASOS:
        out.append((f'paso {paso} · {fn}', round(a / FPS, 3), round((b + 1) / FPS, 3)))
    out += [('solo mar (música cortada)', 8.10, 9.50), ('negro', 12.50, 12.60), ('último 0,5 s', DUR - 0.5, DUR)]
    return out


# =====================================================================================================
# lector del máster cuadro a cuadro (yuv420p crudo)
# =====================================================================================================
def cuadros_yuv(mp4):
    ys, cs = W * H, (W // 2) * (H // 2)
    p = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(mp4), '-f', 'rawvideo', '-pix_fmt',
                               'yuv420p', '-']), stdout=subprocess.PIPE)
    n = 0
    while True:
        b = p.stdout.read(ys + 2 * cs)
        if len(b) < ys + 2 * cs:
            break
        Y = np.frombuffer(b[:ys], np.uint8).reshape(H, W)
        Cb = np.frombuffer(b[ys:ys + cs], np.uint8).reshape(H // 2, W // 2)
        Cr = np.frombuffer(b[ys + cs:], np.uint8).reshape(H // 2, W // 2)
        yield n, Y, Cb, Cr
        n += 1
    p.stdout.close(); p.wait()


def _ncc(img, tpl, sd_min=3.0):
    """NCC de la plantilla; donde la imagen es casi plana (desvío < sd_min niveles) la NCC no está definida y se pone 0
    (si no, la división por una varianza ≈ 0 da valores > 1 en cielo liso o negro)."""
    from scipy.signal import fftconvolve
    t = tpl - tpl.mean(); tn = math.sqrt(float((t * t).sum())) + 1e-9
    k = np.ones(tpl.shape)
    num = fftconvolve(img, t[::-1, ::-1], mode='valid')
    s1 = fftconvolve(img, k, mode='valid'); s2 = fftconvolve(img * img, k, mode='valid')
    var = s2 - s1 * s1 / tpl.size
    ok = var > (sd_min ** 2) * tpl.size
    out = np.zeros_like(num)
    out[ok] = num[ok] / (np.sqrt(var[ok]) * tn)
    return np.clip(out, -1, 1)


def plantilla_logo(q=2):
    """luma de la ficha del logo tal como entra en la firma (cierre_firma.png, opaca), reducida 1/q."""
    from PIL import Image
    pj = json.load(open(PL / 'placa.json'))
    x0, y0, x1, y1 = pj['ficha_logo']
    a = np.asarray(Image.open(PL / 'cierre_firma.png').convert('RGBA')).astype(np.float32)
    rgb = a[y0:y1 + 1, x0:x1 + 1, :3]
    Y = rgb @ np.array([.2126, .7152, .0722], np.float32)
    im = Image.fromarray(Y.astype(np.uint8)).resize(((x1 + 1 - x0) // q, (y1 + 1 - y0) // q), Image.BOX)
    return np.asarray(im).astype(np.float32), (x0, y0, x1, y1)


def alfa_texto(n):
    """alfa (0–255) de todo lo que se superpone en el cuadro n: capa de texto (0–416) + placa (419–476)."""
    from PIL import Image
    a = np.zeros((H, W), np.uint8)
    f = TX / 'cuadros' / f'f_{n:04d}.png'
    if n <= M.TEXTO_ULTIMO and f.exists():
        a = np.maximum(a, np.asarray(Image.open(f))[..., 3])
    for nombre, (n0, n1) in M.PLACA_CUADROS.items():
        if n0 <= n <= n1:
            a = np.maximum(a, np.asarray(Image.open(PL / f'cierre_{nombre}.png'))[..., 3])
    return a


def analisis_cuadros(mp4):
    """una pasada por el máster: luma media, diferencia con el anterior, croma fuera del texto, logo (NCC máx.)."""
    from scipy import ndimage as nd
    tpl, ficha = plantilla_logo()
    filas = []
    prev = None
    for n, Y, Cb, Cr in cuadros_yuv(mp4):
        y2 = Y[::2, ::2].astype(np.float32)
        c = _ncc(y2, tpl)
        iy, ix = np.unravel_index(int(np.argmax(c)), c.shape)
        al = alfa_texto(n)
        m = nd.binary_dilation(al[::2, ::2] > 0, iterations=6)          # texto + 12 px (submuestreo y sangrado x264)
        dcb = np.abs(Cb.astype(np.int16) - 128); dcr = np.abs(Cr.astype(np.int16) - 128)
        dc = np.maximum(dcb, dcr)
        fuera = dc[~m]
        fila = dict(cuadro=n, t=round(n / FPS, 3), luma_media=round(float(Y.mean()), 2),
                    dif_anterior=None if prev is None else round(float(np.abs(y2 - prev).mean()), 3),
                    croma_fuera_texto_max=int(fuera.max()) if fuera.size else None,
                    croma_fuera_texto_p999=float(np.percentile(fuera, 99.9)) if fuera.size else None,
                    croma_media=round(float(dc.mean()), 3),
                    logo_ncc_max=round(float(c[iy, ix]), 4), logo_pos=[int(ix * 2), int(iy * 2)],
                    texto_px=int((al > 8).sum()))
        filas.append(fila)
        prev = y2
        if n % 60 == 0:
            print('análisis', n, fila['logo_ncc_max'], fila['croma_fuera_texto_max'], flush=True)
    return filas, ficha


# =====================================================================================================
# separación 0–12,50 s
# =====================================================================================================
def mapa_cuadros():
    """cuadro del máster → (plano, toma, cuadro de fuente, ventana [x, y, w, h] en píxeles nativos rotados)."""
    pj = json.load(open(T / 'planos.json'))
    out = {}
    for r in pj['planos']:
        m0 = r['m0']
        for k in range(r['cuadros']):
            n = m0 + k
            if r.get('ventanas'):
                Z, x, y, w, h = r['ventanas'][k]
                out[n] = dict(plano=r['id'], toma=r['toma'], fuente=r['n0'] + k, ventana=[x, y, w, h])
            elif r['toma']:
                x, y, w, h = r['caja']
                out[n] = dict(plano=r['id'], toma=r['toma'], fuente=r['n0'] + k, ventana=[x, y, w, h])
            else:
                out[n] = dict(plano=r['id'], toma=None, fuente=None, ventana=None)
    return out


def blanca_8002(n0=0, n1=20):
    """caja de la Blanca en cada cuadro de 8002 por detección directa (1/2 resolución): mín(R, G, B) > 185 y saturación
    < 0,15, componente más grande. El cielo es azul saturado y la arena es beige: no entran. Coordenadas nativas."""
    from scipy import ndimage as nd
    fr = U.leer(V._src('IMG_8002'), 1080, 1920, n0=n0, n1=n1, vf_pre=V.color('IMG_8002')).astype(np.float32)
    out = {}
    for k, a in enumerate(fr):
        mx, mn = a.max(-1), a.min(-1)
        m = (mn > 185) & ((mx - mn) / np.maximum(mx, 1) < 0.15)
        m = nd.binary_opening(m, iterations=2)
        lab, nl = nd.label(m)
        if nl == 0:
            out[n0 + k] = None; continue
        tam = nd.sum(m, lab, range(1, nl + 1)); big = lab == (1 + int(np.argmax(tam)))
        ys, xs = np.nonzero(big)
        out[n0 + k] = dict(caja=[int(xs.min()) * 2, int(ys.min()) * 2, int(xs.max()) * 2 + 1, int(ys.max()) * 2 + 1],
                           pixeles=int(big.sum()))
    return out


def separacion(seg, mapa, directo=None):
    """por cuadro 0–374: hueco (px nativos y px del máster) entre cada objeto seguido y la ventana; el eje que separa y
    la tolerancia medida a mano en ese borde (|seguido − a mano| del control); peor caso = hueco − tolerancia."""
    filas = []
    for n in range(0, FIN_SEP + 1):
        mp = mapa[n]
        if mp['toma'] is None:
            filas.append(dict(cuadro=n, plano=mp['plano'], negro=True)); continue
        toma, s = mp['toma'], mp['fuente']
        x, y, w, h = mp['ventana']; wx0, wy0, wx1, wy1 = x, y, x + w, y + h
        esc = W / w
        dif = seg[toma]['control_manual']['dif_px']
        objs = dict(seg[toma]['por_cuadro'][str(s)]['cajas'])
        tols = {k: dif for k in objs}
        if directo and toma in directo and directo[toma].get(s):
            # detección directa (más precisa que la caja seguida, que lleva margen): tolerancia ±2 px nativos (1/2 res.)
            objs['blanca_deteccion_directa'] = directo[toma][s]['caja']; tols['blanca_deteccion_directa'] = [2, 2, 2, 2]
        res = {}
        for nombre, (ox0, oy0, ox1, oy1) in objs.items():
            d_ = tols[nombre]
            ejes = {'abajo': (oy0 - wy1, abs(d_[1])), 'derecha': (ox0 - wx1, abs(d_[0])),
                    'arriba': (wy0 - oy1, abs(d_[3])), 'izquierda': (wx0 - ox1, abs(d_[2]))}
            eje = max(ejes, key=lambda k: ejes[k][0])
            hueco, tol = ejes[eje]
            res[nombre] = dict(eje=eje, hueco_nativo=round(hueco, 1), tolerancia_nativa=round(tol, 1),
                               peor_caso_nativo=round(hueco - tol, 1), peor_caso_px_master=round((hueco - tol) * esc, 1),
                               caja_objeto=[round(v, 1) for v in (ox0, oy0, ox1, oy1)])
        decide = {k: v for k, v in res.items() if not (k == 'blanca' and 'blanca_deteccion_directa' in res)}
        filas.append(dict(cuadro=n, plano=mp['plano'], toma=toma, fuente=s, ventana=[round(v, 1) for v in (wx0, wy0, wx1, wy1)],
                          objetos=res, minimo_peor_caso_px_master=min(v['peor_caso_px_master'] for v in decide.values()),
                          minimo_solo_seguimiento_px_master=min(v['peor_caso_px_master'] for k, v in res.items()
                                                                if k != 'blanca_deteccion_directa')))
    return filas


def hojas_separacion(seg, mapa, carpeta, directo=None):
    """hoja cuadro a cuadro de cada caja: cada cuadro del máster 0–374 sobre su cuadro de fuente a color, ventana en rojo,
    remeras/persona seguidas en verde, hueco peor caso en px del máster."""
    from PIL import Image, ImageDraw, ImageFont
    carpeta.mkdir(parents=True, exist_ok=True)
    fnt = ImageFont.truetype(FONT, 15)
    por_plano = {}
    for n in range(0, FIN_SEP + 1):
        if mapa[n]['toma']:
            por_plano.setdefault(mapa[n]['plano'], []).append(n)
    sep = {f['cuadro']: f for f in separacion(seg, mapa, directo)}
    hojas = []
    for plano, ns in por_plano.items():
        toma = mapa[ns[0]]['toma']
        nw, nh = V.TOMAS[toma]['nat']
        ancho = 216; alto = round(ancho * nh / nw); s = ancho / nw
        fs = sorted({mapa[n]['fuente'] for n in ns})
        fr = U.leer(V._src(toma), ancho, alto, n0=fs[0], n1=fs[-1], vf_pre=V.color(toma))
        tiles = []
        for n in ns:
            mp = mapa[n]
            im = Image.fromarray(fr[mp['fuente'] - fs[0]]); d = ImageDraw.Draw(im)
            x, y, w, h = mp['ventana']
            d.rectangle([x * s, y * s, (x + w) * s, (y + h) * s], outline=(255, 40, 40), width=2)
            for nombre, c in seg[toma]['por_cuadro'][str(mp['fuente'])]['cajas'].items():
                d.rectangle([c[0] * s, c[1] * s, c[2] * s, c[3] * s], outline=(0, 255, 0), width=2)
            if directo and toma in directo and directo[toma].get(mp['fuente']):
                c = directo[toma][mp['fuente']]['caja']
                d.rectangle([c[0] * s, c[1] * s, c[2] * s, c[3] * s], outline=(0, 230, 255), width=2)
            d.rectangle([0, 0, ancho, 38], fill=(0, 0, 0))
            d.text((3, 1), f'm c{n} ← {toma[4:]} c{mp["fuente"]}', font=fnt, fill=(255, 255, 0))
            d.text((3, 19), f'hueco mín. {sep[n]["minimo_peor_caso_px_master"]:.0f} px', font=fnt, fill=(120, 255, 120))
            tiles.append(im)
        cols = 12; filas = math.ceil(len(tiles) / cols)
        Wd = Image.new('RGB', (cols * (ancho + 2), filas * (alto + 2)), (30, 30, 30))
        for i, t in enumerate(tiles):
            Wd.paste(t, ((i % cols) * (ancho + 2), (i // cols) * (alto + 2)))
        f = carpeta / f'caja_{plano}.jpg'
        Wd.save(f, quality=86)
        hojas.append(dict(plano=plano, toma=toma, cuadros_master=[ns[0], ns[-1]], archivo=f.name))
        print('hoja', f.name, len(ns), flush=True)
    return hojas


def hoja_master_todos(mp4, salida, n0=0, n1=377, cols=20, ancho=120):
    """todos los cuadros n0..n1 del máster, en orden, con su número (lo que ve el espectador hasta 12,60 s)."""
    nf = n1 - n0 + 1; filas = math.ceil(nf / cols)
    U.run(nice(['ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-vf',
                f"select='between(n\\,{n0}\\,{n1})',scale={ancho}:-2,drawtext=fontfile={FONT}:text='c%{{eif\\:n+{n0}\\:d}}':"
                f"x=3:y=3:fontsize=14:fontcolor=yellow:box=1:boxcolor=black@0.75,tile={cols}x{filas}:padding=2",
                '-frames:v', '1', '-fps_mode', 'vfr', '-q:v', '3', str(salida)]))


# =====================================================================================================
# textos
# =====================================================================================================
def norm(s):
    return ' '.join(s.replace('\\N', ' ').split())


def control_textos():
    vis = json.load(open(TX / 'visible.json'))
    guion = GUION.read_text(encoding='utf-8'); roma = ROMA.read_text(encoding='utf-8')
    ensayo = M.ENSAYO.read_text(encoding='utf-8')
    filas = []
    for f in M.FRASES:
        completo = [int(n) for n, fr in vis['cuadros'].items() for x in fr if x['id'] == f['id'] and x['completa']]
        primero = min(completo) if completo else None
        mostrado = None
        if primero is not None:
            x = [x for x in vis['cuadros'][str(primero)] if x['id'] == f['id']][0]
            mostrado = x['lineas']
        fuente = 'roma_07 (paso 9)' if f['id'] == 'p3' else 'guion_G1_v1'
        doc = roma if f['id'] == 'p3' else guion
        filas.append(dict(id=f['id'], texto_guion=f['guion'], en_documento=f['guion'] in doc, documento=fuente,
                          renglones_mostrados=mostrado, igual_al_guion=(mostrado is not None and norm(' '.join(mostrado)) == norm(f['guion'])),
                          renglones_guion=f['guion'].split('\\N'), cambia_corte_de_renglon=(mostrado != f['guion'].split('\\N')),
                          visible_cuadros=list(f['n']), completo_desde=primero,
                          completo_hasta=max(completo) if completo else None))
    # placa (CTA): texto del guion con *cursiva* → <em>
    filas.append(dict(id='placa', texto_guion='Seguí al *equipo*.', en_documento='Seguí al *equipo*.' in guion,
                      documento='guion_G1_v1', html=M.PLACA['frase_html'],
                      igual_al_guion=M.PLACA['frase_html'].replace('<em>', '*').replace('</em>', '*') == 'Seguí al *equipo*.',
                      visible_cuadros=list(M.PLACA_CUADROS['frase'])))
    # citas contra 02b, carácter por carácter
    linea_02b = [l for l in ensayo.splitlines() if 'no puedo prometer ningún resultado' in l][0]
    original = linea_02b[linea_02b.index('«') + 1:linea_02b.rindex('»')]
    citas = []
    for cid in M.CITAS:
        f = [x for x in M.FRASES if x['id'] == cid][0]
        t = norm(f['guion'])
        interior = t.strip('“”').lstrip('…')
        pos = original.find(interior)
        citas.append(dict(id=cid, en_pantalla=t, sin_comillas_ni_elipsis=interior, posicion_en_02b=pos,
                          identica=pos >= 0, caracteres=len(interior),
                          comparacion=[dict(i=i, pantalla=a, original=b) for i, (a, b) in
                                       enumerate(zip(interior, original[pos:pos + len(interior)])) if a != b] if pos >= 0 else 'no encontrada'))
    union = norm(' '.join(x['sin_comillas_ni_elipsis'] for x in citas[1:]))
    citas_rep = dict(original_02b=original, linea_02b=linea_02b, citas=citas,
                     c2_mas_c3_es_continuo=(union in original), voseo_en_citas=any(w in union for w in ('podés', 'vas a', 'tenés')))
    # nada de la marca ni de apuestas en la capa de texto 0–12,50
    palabras = ' '.join(norm(f['guion']) for f in M.FRASES).lower()
    prohibidas = ['roccé', 'rocce', 'apuesta', 'apostá', 'cuota', 'momio', 'bet', 'casino', 'pronóstico', 'odds']
    marca = dict(palabras_prohibidas_encontradas=[p for p in prohibidas if p in palabras])
    return filas, citas_rep, marca


def texto_vs_remeras():
    """12,60–15,90: borde inferior de lo superpuesto (alfa > 8) contra el borde superior de las remeras seguidas."""
    from PIL import Image
    seg = json.load(open(MED / 'seguimiento.json'))
    filas = []
    for n in range(378, NF):
        if n <= 416:
            toma, s, esc = 'IMG_7895', n - 378, W / 2160          # plano 09: cuadro completo 2160 → 1080
        else:
            toma, s, esc = 'IMG_4631', 129 + n - 417, 1.0          # plano 10: caja (0, 0, 1080, 1920)
        c = seg[toma]['por_cuadro'][str(s)]['cajas']['remeras']
        dif = seg[toma]['control_manual']['dif_px']
        al = alfa_texto(n)
        filas_txt = np.nonzero((al > 8).any(1))[0]
        if n >= 417:
            # la placa lleva un degradé de 760 px (opacidad que baja a 0): se mide solo frase + firma (letras y logo)
            a1 = np.asarray(Image.open(PL / 'cierre_frase.png')).astype(int)
            letras = (a1[..., 3] > 200) & (a1[..., :3].min(-1) > 200)
            if n >= M.PLACA_CUADROS['firma'][0]:
                letras |= np.asarray(Image.open(PL / 'cierre_firma.png'))[..., 3] > 8
            filas_txt = np.nonzero(letras.any(1))[0]
        y_txt = int(filas_txt.max()) if len(filas_txt) else None
        y_rem = c[1] * esc; tol = abs(dif[1]) * esc
        filas.append(dict(cuadro=n, toma=toma, fuente=s, texto_borde_inferior=y_txt, remeras_borde_superior=round(y_rem, 1),
                          tolerancia=round(tol, 1), hueco_peor_caso=None if y_txt is None else round(y_rem - tol - y_txt, 1)))
    return filas


# =====================================================================================================
# audio
# =====================================================================================================
def _salto(x, sr, t, tipo):
    """dónde cae el evento cerca de t. Golpes: salto de nivel (dB) entre los 20 ms siguientes y los 20 ms anteriores,
    en una grilla de 2 ms entre t − 66 y t + 66 ms (±2 cuadros); devuelve el desvío del salto máximo y el salto en t.
    Barridos (suben de a poco): desvío del pico de la envolvente de 10 ms en [t − 150, t + 66 ms]."""
    m = np.abs(x).mean(1) if x.ndim == 2 else np.abs(x)
    if tipo in ('barrido CTA', 'slam'):
        k = int(0.01 * sr); e = np.convolve(m, np.ones(k) / k, 'same')
        i0, i1 = max(0, int((t - 0.15) * sr)), int((t + 0.066) * sr)
        return dict(desvio_ms=round(((i0 + int(np.argmax(e[i0:i1]))) / sr - t) * 1000, 1), salto_db_en_t=None)
    w = int(0.02 * sr)
    def j(tt):
        i = int(round(tt * sr))
        a = np.sqrt((m[max(0, i - w):i] ** 2).mean() + 1e-14); b = np.sqrt((m[i:i + w] ** 2).mean() + 1e-14)
        return 20 * np.log10(b / a)
    grid = np.arange(-0.066, 0.0661, 0.002)
    v = [j(t + g) for g in grid]
    return dict(desvio_ms=round(float(grid[int(np.argmax(v))]) * 1000, 1), salto_db_en_t=round(j(t), 1),
                salto_db_max=round(float(max(v)), 1))


def inicios_golpes():
    """cada golpe del texto (y los del gancho, el drop y el CTA) contra lo que suena: en la pista de efectos (antes del
    limitador) y en el audio decodificado del MP4 entregado."""
    import soundfile as sf
    fx, sr = sf.read(str(A / 'v4_completa_fx.wav'))
    au = json.load(open(A / 'audio.json'))
    evs = [dict(cuadro=g['cuadro'], t=g['t'], tipo=g['tipo'], frase=g['frase']) for g in au['golpes_texto']]
    evs += [dict(cuadro=0, t=0.0, tipo='impacto + campana', frase='gancho'), dict(cuadro=378, t=12.6, tipo='drop', frase='reeng'),
            dict(cuadro=417, t=13.9, tipo='barrido CTA', frase='placa')]
    mp4 = U.audio_np(MAS / M.NOMBRES['completa']).astype(np.float64)
    out = []
    for ev in sorted(evs, key=lambda x: x['t']):
        if ev['t'] < 0.03:
            a1 = dict(desvio_ms=0.0, salto_db_en_t=None, nota='arranca en la muestra 0'); a2 = dict(a1)
        else:
            a1 = _salto(fx, sr, ev['t'], ev['tipo']); a2 = _salto(mp4, 48000, ev['t'], ev['tipo'])
        out.append(dict(ev, pista_fx=a1, mp4=a2, desvio_ms=a1['desvio_ms'], mp4_en_banda=_banda(mp4, ev)))
    return out


BANDAS = {'grave': (35, 200), 'agudo': (1500, 9000), 'impacto': (30, 150), 'sub': (50, 140), 'acento': (1800, 3500),
          'drop': (30, 150)}


def _banda(x, ev, sr=48000):
    """salto (dB) de los 30 ms siguientes contra los 30 ms anteriores en la banda donde vive el golpe, en el audio del
    MP4 (lo que llega al espectador; la medida de banda ancha la dominan el mar y el colchón graves)."""
    if ev['tipo'] not in BANDAS or ev['t'] < 0.03:
        return None
    from scipy.signal import butter, sosfiltfilt
    lo, hi = BANDAS[ev['tipo']]
    i = int(ev['t'] * sr); w = int(0.03 * sr)
    seg = x[max(0, i - sr // 2):i + sr // 2].mean(1)
    b = sosfiltfilt(butter(4, [lo, hi], btype='band', fs=sr, output='sos'), seg)
    c = min(i, sr // 2)
    pre = np.sqrt((b[c - w:c] ** 2).mean()) + 1e-12; post = np.sqrt((b[c:c + w] ** 2).mean()) + 1e-12
    return dict(banda_hz=[lo, hi], salto_db=round(float(20 * np.log10(post / pre)), 1))


def pistas_en_tramos():
    import soundfile as sf
    out = {}
    for mezcla in ('completa', 'sinmusica'):
        r = {}
        for p in ('amb', 'fx', 'mus', 'bombo'):
            f = A / f'v4_{mezcla}_{p}.wav'
            if not f.exists():
                r[p] = 'no existe (pista vacía en esta mezcla)'; continue
            x, sr = sf.read(str(f))
            d = {}
            for nom, t0, t1 in (('solo mar 8,10–9,50', 8.10, 9.50), ('negro 12,50–12,60', 12.50, 12.60)):
                s = x[int(t0 * sr):int(t1 * sr)]
                d[nom] = round(float(20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-12)), 1)
            r[p] = d
        out[mezcla] = r
    return out


# =====================================================================================================
# etapa control
# =====================================================================================================
CRITICOS = {0: 'c0 · apuesta (portada)', 18: '¿Vuelve? entra', 24: '¿Vuelve? asentado', 54: 'golpe E− 1', 78: 'golpe E− 2',
            108: 'golpe E− 3', 123: 'golpe E+ 1a', 138: 'golpe E+ 1b (pista)', 162: 'Nocaut (impacto)', 165: 'Nocaut asentado',
            189: 'golpe E− 4', 210: 'golpe E+ 3 (paso 9 nuevo)', 228: 'golpe E− 5 (pista)', 242: 'fin de la cadena',
            246: 'giro: oscuro', 262: 'cita 1', 284: 'cita 1 completa', 300: 'cita 2', 330: 'cita 3 entra', 348: 'sub-golpe «intentarlo»',
            374: 'último cuadro de la resolución', 375: 'negro', 378: 'color: revela las remeras', 387: 'acento «prometés?»',
            416: 'barrido', 419: 'placa', 429: 'firma', 450: 'CTA', 476: 'último cuadro'}
PNG_CRITICOS = (0, 108, 162, 262, 348, 378, 387, 450)


def etapa_control():
    EVID.mkdir(parents=True, exist_ok=True)
    rep = dict(fecha='2026-11-25', pieza='Roccé Life · V4 «¿Vuelve?» versión B · máster v01', archivos={})
    tr = tramos()
    for k, nombre in M.NOMBRES.items():
        f = MAS / nombre
        err = subprocess.run(nice(['ffmpeg', '-v', 'error', '-i', str(f), '-f', 'null', '-']), capture_output=True, text=True).stderr.strip()
        pj = json.loads(U.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(f)]))
        json.dump(pj, open(EVID / f'ffprobe_{k}.json', 'w'), indent=1)
        cuerpo = f.read_bytes()
        gps = [m.decode() for m in (b'ISO6709', b'\xa9xyz', b'com.apple.quicktime.location', b'location') if m in cuerpo]
        a = U.audio_np(f)
        niv, v100, sil = U.niveles_tramos(a, tr)
        mom = U2.momentanea(f)
        vs = [s for s in pj['streams'] if s['codec_type'] == 'video'][0]
        au = [s for s in pj['streams'] if s['codec_type'] == 'audio'][0]
        ncuad = int(U.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                           'stream=nb_read_frames', '-of', 'csv=p=0', str(f)]).decode().strip())
        I, Pk, LRA = L2.medir_ebur(f)
        rep['archivos'][k] = dict(
            archivo=str(f), bytes=f.stat().st_size, sha256=hashlib.sha256(cuerpo).hexdigest(),
            md5_flujo_video=U.md5_stream(f, 'v'), md5_flujo_audio=U.md5_stream(f, 'a'),
            decodifica_completo=(err == ''), errores_decodificacion=err[:500], cuadros_decodificados=ncuad,
            video=dict(codec=vs['codec_name'], perfil=vs.get('profile'), nivel=vs.get('level'), pix_fmt=vs['pix_fmt'],
                       ancho=vs['width'], alto=vs['height'], fps=vs['r_frame_rate'], cuadros=int(vs['nb_frames']),
                       duracion=float(vs['duration']), rango=vs.get('color_range'), matriz=vs.get('color_space'),
                       transferencia=vs.get('color_transfer'), primarios=vs.get('color_primaries'),
                       bitrate=int(vs.get('bit_rate', 0))),
            audio=dict(codec=au['codec_name'], perfil=au.get('profile'), hz=int(au['sample_rate']), canales=au['channels'],
                       duracion=float(au['duration']), bitrate=int(au.get('bit_rate', 0))),
            duracion_formato=float(pj['format']['duration']), etiquetas_formato=pj['format'].get('tags', {}),
            atomos=L2.atomos(f), faststart=L2.atomos(f).index('moov') < L2.atomos(f).index('mdat'),
            marcas_gps_o_ubicacion=gps,
            sonoridad=dict(lufs_integrado=I, pico_real_dbtp=Pk, lra=LRA),
            momentanea_por_tramo=U2.momentanea_tramos(mom, tr), niveles_por_tramo=niv,
            ventanas_100ms_bajo_menos50dbfs=sil, silencio_final_s=L2.silencio_final(a),
            audio_igual_video=abs(float(au['duration']) - float(vs['duration'])) < 1 / FPS)
        jdump(mom, EVID / 'audio' / f'momentanea_{k}.json')
        print(k, rep['archivos'][k]['sonoridad'], rep['archivos'][k]['md5_flujo_video'], rep['archivos'][k]['md5_flujo_audio'],
              'gps', gps, flush=True)
    rep['video_identico_en_las_dos'] = rep['archivos']['completa']['md5_flujo_video'] == rep['archivos']['sinmusica']['md5_flujo_video']
    f0 = MAS / M.NOMBRES['completa']

    # imagen: hoja cada 0,5 s, cortes, críticos
    U.hoja_contacto(f0, EVID / 'hoja_contacto_cada_0.5s.jpg', cada=15, cols=8, ancho=240)
    U.cuadros_corte(f0, M.CORTES_IMG, EVID / 'cortes', NF - 1)
    crit = EVID / 'criticos'; crit.mkdir(parents=True, exist_ok=True)
    ns = sorted(CRITICOS)
    sel = '+'.join(f'eq(n\\,{k})' for k in ns)
    U.run(nice(['ffmpeg', '-v', 'error', '-y', '-i', str(f0), '-vf', f"select='{sel}'", '-fps_mode', 'vfr', str(crit / 'tmp_%03d.png')]))
    from PIL import Image
    for i, n in enumerate(ns):
        src = crit / f'tmp_{i + 1:03d}.png'
        if n in PNG_CRITICOS:
            src.rename(crit / f'c{n:03d}.png')
        else:
            Image.open(src).convert('RGB').save(crit / f'c{n:03d}.jpg', quality=95); src.unlink()
    rep['criticos'] = {f'c{n:03d}': v for n, v in CRITICOS.items()}

    # una pasada cuadro a cuadro
    filas, ficha = analisis_cuadros(f0)
    jdump(filas, EVID / 'imagen' / 'por_cuadro.json')
    logo_sep = max(filas[n]['logo_ncc_max'] for n in range(0, FIN_SEP + 1))
    logo_firma = [filas[n]['logo_ncc_max'] for n in range(M.PLACA_CUADROS['firma'][0], NF)]
    croma_bn = [filas[n]['croma_fuera_texto_max'] for n in range(0, FIN_SEP + 1)]
    exp = []
    for paso, a, b, fn in M.PASOS:
        v = [filas[n]['luma_media'] for n in range(a, b + 1)]
        exp.append(dict(paso=paso, funcion=fn, cuadros=[a, b], luma_media=round(float(np.mean(v)), 1),
                        grado=M.grado_de(a)[0], k=M.grado_de(a)[1] and round(M.grado_de(a)[1], 3)))
    cortes = set(M.CORTES_IMG) | {65, 66, 67, 90, 201, 243}
    difs = [(f['cuadro'], f['dif_anterior']) for f in filas[1:]]
    rep['imagen'] = dict(
        logo=dict(metodo='NCC de la ficha del logo (luma, 1/2) en cada cuadro del máster; control positivo: cuadros con firma',
                  ficha_px=ficha, ncc_max_0_374=logo_sep, ncc_firma_min=min(logo_firma), ncc_firma_max=max(logo_firma),
                  cuadros_0_374_con_ncc_mayor_0_6=[f['cuadro'] for f in filas[:FIN_SEP + 1] if f['logo_ncc_max'] > 0.6]),
        bn=dict(metodo='|Cb−128|, |Cr−128| del máster fuera del texto (alfa dilatada 12 px), cuadros 0–374',
                maximo=max(croma_bn), cuadros_con_maximo_mayor_3=[n for n, v in enumerate(croma_bn) if v > 3],
                p999_max=max(filas[n]['croma_fuera_texto_p999'] for n in range(0, FIN_SEP + 1)),
                croma_media_color_378_476=round(float(np.mean([filas[n]['croma_media'] for n in range(378, NF)])), 2)),
        exposicion_por_paso=exp,
        continuidad=dict(duplicados_dif_menor_0_2=[n for n, d in difs if d is not None and d < 0.2],
                         saltos_fuera_de_corte_dif_mayor_25=[n for n, d in difs if d is not None and d > 25 and n not in cortes],
                         dif_max=max(d for _, d in difs)))
    print('logo 0–374', logo_sep, 'firma', min(logo_firma), 'croma', max(croma_bn), flush=True)

    # separación
    seg = json.load(open(MED / 'seguimiento.json'))
    mapa = mapa_cuadros()
    sp = EVID / 'separacion'; sp.mkdir(parents=True, exist_ok=True)
    directo = {'IMG_8002': blanca_8002()}
    jdump(directo, sp / 'deteccion_directa_blanca_8002.json')
    sep = separacion(seg, mapa, directo)
    jdump(sep, sp / 'separacion_por_cuadro.json')
    hojas = hojas_separacion(seg, mapa, sp, directo)
    hoja_master_todos(f0, sp / 'master_todos_los_cuadros_c0-c377.jpg')
    for toma in M.OBJETOS:
        shutil.copy2(MED / f'seguimiento_{toma}.jpg', sp / f'seguimiento_{toma}.jpg')
    por_plano = {}
    for f in sep:
        if f.get('negro'):
            continue
        p = por_plano.setdefault(f['plano'], dict(toma=f['toma'], cuadros=[f['cuadro'], f['cuadro']], min_px_master=1e9,
                                                  min_solo_seguimiento_px_master=1e9))
        p['cuadros'][1] = f['cuadro']
        p['min_solo_seguimiento_px_master'] = min(p['min_solo_seguimiento_px_master'], f['minimo_solo_seguimiento_px_master'])
        if f['minimo_peor_caso_px_master'] < p['min_px_master']:
            p.update(min_px_master=f['minimo_peor_caso_px_master'], cuadro_min=f['cuadro'],
                     objeto_eje={k: v['eje'] for k, v in f['objetos'].items()})
    rep['separacion'] = dict(
        regla='0–12,50 s (c0–c374): sin remera, logo ni firma (condición 4 de Roma)',
        metodo=('ventana real de cada cuadro (planos.json, la que usó plano_z) contra las cajas seguidas de remeras y persona '
                '(semejanza anclada a un cuadro de referencia medido a mano; validada con una segunda medición a mano); peor caso '
                '= hueco − |seguido − a mano| en el borde que separa; hojas cuadro a cuadro de cada caja y de todo el máster 0–377'),
        control_manual={t: seg[t]['control_manual'] for t in seg}, ncc_min_seguimiento={t: seg[t]['ncc_min'] for t in seg},
        por_plano=por_plano, todos_positivos=all(f.get('negro') or f['minimo_peor_caso_px_master'] > 0 for f in sep),
        negro=[375, 376, 377], hojas=hojas)
    print('separación', json.dumps(por_plano, ensure_ascii=False), flush=True)

    # textos
    tx, citas, marca = control_textos()
    tv = texto_vs_remeras()
    te = EVID / 'textos'; te.mkdir(parents=True, exist_ok=True)
    jdump(dict(frases=tx, marca_y_apuestas=marca), te / 'textos_vs_guion.json')
    jdump(citas, te / 'citas_vs_02b.json')
    with open(te / 'citas_vs_02b.txt', 'w', encoding='utf-8') as h:
        h.write('02b (texto exacto del original, cap. 9):\n' + citas['original_02b'] + '\n\n')
        for c in citas['citas']:
            h.write(f"{c['id']} en pantalla: {c['en_pantalla']}\n   comparado: {c['sin_comillas_ni_elipsis']}\n"
                    f"   posición en 02b: {c['posicion_en_02b']} · {c['caracteres']} caracteres · idéntica: {c['identica']} · "
                    f"diferencias: {c['comparacion']}\n\n")
        h.write(f"c2 + c3 seguidas = un tramo continuo del original: {citas['c2_mas_c3_es_continuo']}\n")
    jdump(tv, te / 'texto_vs_remeras_c378-c476.json')
    shutil.copy2(TX / 'visible.json', te / 'visible_por_cuadro.json')
    shutil.copy2(TX / 'spec_texto.json', te / 'spec_texto.json')
    shutil.copy2(TX / 'texto_v4.html', te / 'texto_v4.html')
    rep['textos'] = dict(todas_iguales_al_guion=all(f['igual_al_guion'] for f in tx), todas_en_documento=all(f['en_documento'] for f in tx),
                         cambios_de_renglon=[f['id'] for f in tx if f.get('cambia_corte_de_renglon')],
                         citas_identicas=all(c['identica'] for c in citas['citas']), c2_mas_c3_continuo=citas['c2_mas_c3_es_continuo'],
                         marca=marca, texto_vs_remeras_min=min(f['hueco_peor_caso'] for f in tv if f['hueco_peor_caso'] is not None),
                         texto_vs_remeras_cuadro_min=min((f for f in tv if f['hueco_peor_caso'] is not None),
                                                         key=lambda f: f['hueco_peor_caso'])['cuadro'])
    print('textos', json.dumps(rep['textos'], ensure_ascii=False), flush=True)

    # audio
    au = EVID / 'audio'; au.mkdir(parents=True, exist_ok=True)
    ig = inicios_golpes(); pt = pistas_en_tramos()
    jdump(ig, au / 'golpes_vs_texto.json'); jdump(pt, au / 'pistas_en_tramos.json')
    for k in ('completa', 'sinmusica'):
        shutil.copy2(A / f'v4_{k}_eventos.json', au / f'eventos_{k}.json')
    shutil.copy2(A / 'audio.json', au / 'audio.json')
    rep['audio'] = dict(golpes_desvio_max_ms=max(abs(g['desvio_ms']) for g in ig), golpes=ig, pistas_en_tramos=pt)
    print('golpes', [(g['cuadro'], g['tipo'], g['pista_fx']['desvio_ms'], g['mp4_en_banda']) for g in ig], flush=True)

    # grado y planos (registro)
    shutil.copy2(MED / 'grado.json', EVID / 'imagen' / 'grado.json')
    shutil.copy2(T / 'planos.json', EVID / 'imagen' / 'planos.json')
    shutil.copy2(PL / 'placa.json', EVID / 'imagen' / 'placa.json')
    jdump(rep, EVID / 'control.json')
    print('control ok')


# =====================================================================================================
# etapa entregar
# =====================================================================================================
def etapa_entregar():
    res = {}
    for k, nombre in M.NOMBRES.items():
        for dst in (M.EXP / nombre, M.PIEZA / nombre):
            if dst.exists():
                raise RuntimeError(f'{dst} ya existe: no se sobrescribe')
    ev = M.PIEZA / EVID.name
    if ev.exists():
        raise RuntimeError(f'{ev} ya existe')
    for k, nombre in M.NOMBRES.items():
        for dst in (M.EXP / nombre, M.PIEZA / nombre):
            shutil.copyfile(MAS / nombre, dst)
    shutil.copytree(EVID, ev)
    time.sleep(8)                                    # montaje de red: esperar antes de verificar
    for k, nombre in M.NOMBRES.items():
        src = MAS / nombre
        ref = dict(bytes=src.stat().st_size, sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                   md5_flujo_video=U.md5_stream(src, 'v'), md5_flujo_audio=U.md5_stream(src, 'a'))
        for dst in (M.EXP / nombre, M.PIEZA / nombre):
            err = subprocess.run(nice(['ffmpeg', '-v', 'error', '-i', str(dst), '-f', 'null', '-']), capture_output=True, text=True).stderr.strip()
            got = dict(bytes=dst.stat().st_size, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
                       md5_flujo_video=U.md5_stream(dst, 'v'), md5_flujo_audio=U.md5_stream(dst, 'a'))
            flujos = (got['md5_flujo_video'], got['md5_flujo_audio']) == (ref['md5_flujo_video'], ref['md5_flujo_audio'])
            res[str(dst)] = dict(got, flujos_iguales_al_original=flujos, archivo_identico=(got == ref),
                                 bytes_agregados=got['bytes'] - ref['bytes'], decodifica_completo=(err == ''), atomos=L2.atomos(dst))
            print(dst, got, 'flujos OK' if flujos else 'FLUJOS DISTINTOS', 'archivo idéntico' if got == ref else
                  f"+{got['bytes'] - ref['bytes']} bytes", 'decodifica' if err == '' else err[:200], flush=True)
    n_local = sum(1 for _ in EVID.rglob('*') if _.is_file()); n_red = sum(1 for _ in ev.rglob('*') if _.is_file())
    dif = []
    for f in EVID.rglob('*'):
        if f.is_file():
            g = ev / f.relative_to(EVID)
            if not g.exists() or hashlib.md5(f.read_bytes()).hexdigest() != hashlib.md5(g.read_bytes()).hexdigest():
                dif.append(str(f.relative_to(EVID)))
    res['evidencia'] = dict(carpeta=str(ev), archivos_local=n_local, archivos_red=n_red, distintos=dif)
    print('evidencia', n_local, n_red, 'distintos', dif)
    jdump(res, T / 'entrega.json')
