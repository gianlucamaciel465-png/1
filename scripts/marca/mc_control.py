#!/usr/bin/env python3
"""MARCA · control y entrega de los másteres v01 de MC-03 y MC-04 (Pedro B, 25/11/2026).

python mc_control.py control MC-03|MC-04   → evidencia_v01/ (ffprobe, decodificación, GPS, md5 de flujos, sonoridad,
                                             niveles por plano, cuadros de cada corte, hoja cada 0,5 s, vista a 360 px,
                                             estados de la gráfica por cuadro, choques texto/estampado, color, cámara lenta)
python mc_control.py control|hoja|entregar MC-04 v02 → lo mismo para la v02 de MC-04 (dictamen 02 de Roma): master_v02/,
                                             evidencia_v02/, 03_pedro_hoja_master_v02.md (solo lo que cambió)
python mc_control.py entregar MC-03|MC-04  → copia a EXPORTACIONES/ y a la carpeta de la pieza (sin sobrescribir) y verifica
                                             las copias por md5 de flujos (la carpeta de la pieza agrega una caja C2PA).
"""
import json, math, subprocess, sys, hashlib, shutil, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, '/home/user/1/scripts/marca')
import mc03 as M          # noqa: E402
import mc04 as M4         # noqa: E402
U, V = M.U, M.V
FONT = M.FONT_HOJA


def pieza(pid, ver='v01'):
    """rutas por pieza y versión. v01: master/, evidencia_v01/, hoja 01. MC-04 v02: master_v02/, evidencia_v02/, hoja 03."""
    if pid == 'MC-03':
        d = dict(T=M.T, NF=M.NF, nombres=M.NOMBRES, ref='A', cortes=M.CORTES, base=M.T / 'mc03_base.mp4',
                 carpeta=M.PIEZA, audio={'A': M.A / 'mc03_completa.wav', 'B': M.A / 'mc03_completa.wav',
                                         'A_sinmusica': M.A / 'mc03_sinmusica.wav'},
                 giro=[310, 325, 340], cta=[370, 380, 429], ui=lambda: M.ui_mc03('A')[0])
    else:
        d = dict(T=M4.T, NF=M4.NF, nombres=M4.NOMBRES, ref='completa', cortes=M4.CORTES, base=M4.T / 'mc04_base.mp4',
                 carpeta=M4.PIEZA, audio={'completa': M4.A / 'mc04_completa.wav', 'sinmusica': M4.A / 'mc04_sinmusica.wav'},
                 giro=[262, 268, 285], cta=[330, 340, 419], ui=lambda: M4.ui_mc04()[0])
    d.update(ver=ver, mas=d['T'] / 'master', ev=d['T'] / 'evidencia_v01', hoja='01_pedro_hoja_master_v01.md',
             entrega='entrega.json')
    if ver == 'v02' and pid == 'MC-03':
        d.update(nombres=M.NOMBRES_V02, mas=M.T / 'master_v02', ev=M.T / 'evidencia_v02', hoja='03_pedro_hoja_master_v02.md',
                 entrega='entrega_v02.json', ui=lambda: M.ui_mc03('A', 'v02')[0],
                 muestra={'01': 30, '03': 90, '04': 110, '06': 180, '07': 205, '10': 295})
    elif ver == 'v02':
        d.update(nombres=M4.NOMBRES_V02, mas=M4.T / 'master_v02', ev=M4.T / 'evidencia_v02',
                 hoja='03_pedro_hoja_master_v02.md', entrega='entrega_v02.json', ui=lambda: M4.ui_mc04('v02')[0])
    return d


def ficha(f):
    err = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(f), '-f', 'null', '-'],
                         capture_output=True, text=True).stderr.strip()
    pj = json.loads(U.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(f)]))
    cuerpo = f.read_bytes()
    gps = [m.decode() for m in (b'ISO6709', b'location', b'com.apple.quicktime', b'\xa9xyz') if m in cuerpo]
    vs = [s for s in pj['streams'] if s['codec_type'] == 'video'][0]
    au = [s for s in pj['streams'] if s['codec_type'] == 'audio'][0]
    nb = int(U.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                    'stream=nb_read_frames', '-of', 'csv=p=0', str(f)]).decode().strip())
    # faststart: el átomo moov va antes que mdat
    i_moov, i_mdat = cuerpo.find(b'moov'), cuerpo.find(b'mdat')
    return pj, dict(
        archivo=str(f), bytes=f.stat().st_size, sha256=hashlib.sha256(cuerpo).hexdigest(),
        md5_video=U.md5_stream(f, 'v'), md5_audio=U.md5_stream(f, 'a'),
        decodifica_completo=(err == ''), errores=err[:400], faststart=bool(0 <= i_moov < i_mdat),
        video=dict(codec=vs['codec_name'], perfil=vs.get('profile'), nivel=vs.get('level'), pix_fmt=vs['pix_fmt'],
                   ancho=vs['width'], alto=vs['height'], fps=vs['r_frame_rate'], cuadros_decodificados=nb,
                   duracion=float(vs['duration']),
                   color=[vs.get('color_range'), vs.get('color_space'), vs.get('color_transfer'), vs.get('color_primaries')]),
        audio=dict(codec=au['codec_name'], perfil=au.get('profile'), hz=int(au['sample_rate']), canales=au['channels'],
                   duracion=float(au['duration'])),
        duracion_formato=float(pj['format']['duration']), etiquetas_formato=pj['format'].get('tags', {}),
        marcas_gps_o_ubicacion=gps, sonoridad=U.ebur(f))


def vista_360(mp4, cuadros, salida, cols=6, rotulos=None):
    fr = M.leer_cuadros(mp4, cuadros, 360, 640)
    fnt = ImageFont.truetype(FONT, 18)
    filas = math.ceil(len(cuadros) / cols)
    Wd = Image.new('RGB', (cols * 364, filas * 668), (24, 24, 24))
    for i, (k, f) in enumerate(zip(cuadros, fr)):
        im = Image.fromarray(f)
        x, y = (i % cols) * 364, (i // cols) * 668
        Wd.paste(im, (x, y + 26))
        d = ImageDraw.Draw(Wd)
        d.text((x + 4, y + 4), f'c{k}  {k / 30:.2f} s' + (f'  {rotulos[i]}' if rotulos else ''), font=fnt, fill=(255, 255, 0))
    Wd.save(salida, quality=92)


def tira(mp4, cuadros, caja, salida, cols=6):
    """recortes a tamaño real (caja x0, y0, x1, y1) de varios cuadros, uno al lado del otro, con su número."""
    fr = M.leer_cuadros(mp4, cuadros)
    x0, y0, x1, y1 = caja; w, h = x1 - x0, y1 - y0
    fnt = ImageFont.truetype(FONT, 30)
    filas = math.ceil(len(cuadros) / cols)
    Wd = Image.new('RGB', (cols * (w + 4), filas * (h + 44)), (24, 24, 24)); d = ImageDraw.Draw(Wd)
    for i, (k, f) in enumerate(zip(cuadros, fr)):
        x, y = (i % cols) * (w + 4), (i // cols) * (h + 44)
        Wd.paste(Image.fromarray(f).crop(caja), (x, y + 44))
        d.text((x + 6, y + 6), f'c{k}  {k / 30:.3f} s', font=fnt, fill=(255, 255, 0))
    Wd.save(salida, quality=93)


def niveles_planos(mp4, planos, nf):
    a = U.audio_np(mp4)
    tramos = [(f"plano {p['id']}", p['m0'] / 30, (p['m0'] + p['nf']) / 30) for p in planos] + [('último 0,5 s', nf / 30 - 0.5, nf / 30)]
    niv, v100, sil = U.niveles_tramos(a, tramos)
    return niv, sil, v100


def forma_onda(wavs, salida, dur, cortes):
    """forma de onda (envolvente RMS de 10 ms) de cada mezcla con los cortes marcados."""
    import soundfile as sf
    Wd = Image.new('RGB', (1600, 260 * len(wavs)), (20, 20, 20)); d = ImageDraw.Draw(Wd)
    fnt = ImageFont.truetype(FONT, 18)
    for j, (nom, f) in enumerate(wavs):
        x = U.audio_np(f) if str(f).endswith('.mp4') else sf.read(f)[0]
        x = x.mean(1) if x.ndim == 2 else x
        hop = 480; n = len(x) // hop
        rms = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1))
        db_ = 20 * np.log10(np.maximum(rms, 1e-6))
        y0 = j * 260
        for c in cortes:
            xx = int(c / 30 / dur * 1580) + 10; d.line([xx, y0 + 20, xx, y0 + 250], fill=(70, 70, 120))
        for i in range(n):
            xx = int(i / n * 1580) + 10; h = int(np.clip((db_[i] + 60) / 60, 0, 1) * 110)
            d.line([xx, y0 + 135 - h, xx, y0 + 135 + h], fill=(120, 200, 255))
        d.text((12, y0 + 2), f'{nom} · RMS 10 ms (−60…0 dBFS) · líneas = cortes', font=fnt, fill=(255, 255, 0))
    Wd.save(salida)


def margen_texto_estampado(ui, est_json, nf):
    """por cuadro: distancia vertical mínima entre la caja visible de cada texto o gráfica y la caja del estampado
    (cuando se superponen en x). Negativa = se pisan las cajas (no necesariamente los píxeles: eso lo mide el choque)."""
    est = json.load(open(est_json))
    peor = None
    por_el = {}
    for k in range(nf):
        e = est.get(str(k))
        if not e or not e['caja']:
            continue
        ex0, ey0, ex1, ey1 = e['caja']
        for it in ui(k)[1]:
            x0, y0, x1, y1 = it[0].caja
            if x1 <= ex0 or x0 >= ex1:
                continue
            gap = ey0 - y1 if y1 <= ey0 else (y0 - ey1 if y0 >= ey1 else -min(y1 - ey0, ey1 - y0))
            r = dict(cuadro=k, elemento=it[0].nombre, texto=it[0].texto, margen_px=int(gap), caja_el=list(it[0].caja), caja_estampado=e['caja'])
            if it[0].nombre not in por_el or gap < por_el[it[0].nombre]['margen_px']:
                por_el[it[0].nombre] = r
            if peor is None or gap < peor['margen_px']:
                peor = r
    return dict(minimo=peor, por_elemento=por_el)


def estados_grafica(ui, nf):
    """cambios de estado de la gráfica (marcador o barra) por cuadro, leídos de la misma función que arma la capa."""
    prev, out = None, []
    for k in range(nf):
        clave, items = ui(k)
        g = [it[0].texto for it in items if it[0].nombre in ('marcador', 'barra')]
        e = [it[0].texto for it in items if it[0].nombre.startswith('etq')]
        s = (tuple(g), tuple(e))
        if s != prev:
            out.append(dict(cuadro=k, t=round(k / 30, 3), grafica=g, etiqueta=e))
            prev = s
    return out


def textos_por_cuadro(ui, nf):
    prev, out = None, []
    for k in range(nf):
        clave, items = ui(k)
        t = tuple((it[0].nombre, it[0].texto, list(it[0].caja)) for it in items if it[0].nombre not in ('marcador', 'barra'))
        if t != prev:
            out.append(dict(cuadro=k, t=round(k / 30, 3), textos=[dict(nombre=a, texto=b, caja_visible=c) for a, b, c in t]))
            prev = t
    return out


def color_master(mp4, planos, salida_json):
    """blanco (tela lisa) y negro (tela) medidos en el máster, un cuadro por plano (medio del plano)."""
    ks = [p['m0'] + p['nf'] // 2 for p in planos]
    fr = M.leer_cuadros(mp4, ks, 540, 960)
    out = []
    for p, k, f in zip(planos, ks, fr):
        f32 = f.astype(np.float32)
        w = M.blanco_medido(f)
        L = f32 @ np.array([.2126, .7152, .0722], np.float32)
        dm = (L < 55) & (L > 10)
        q = np.median(f32[dm], 0) if dm.sum() > 2000 else None
        out.append(dict(plano=p['id'], cuadro=k, toma=p['toma'],
                        blanco=None if w is None else dict(rgb=[round(float(v), 1) for v in w], b_menos_r=round(float(w[2] - w[0]), 1),
                                                           g_menos_r=round(float(w[1] - w[0]), 1)),
                        oscuro=None if q is None else dict(rgb=[round(float(v), 1) for v in q], b_menos_r=round(float(q[2] - q[0]), 1),
                                                           g_menos_r=round(float(q[1] - q[0]), 1), px=int(dm.sum()))))
    M.jdump(out, salida_json)
    return out


def _leer_420(mp4, ks):
    """cuadros ks de un MP4 como (Y, Cb, Cr) yuv420p, sin pasar por RGB (la corrección v02 trabaja en Cb/Cr)."""
    Wd, Hd = M.W, M.H
    sel = '+'.join(f'eq(n\\,{k})' for k in ks)
    a = np.frombuffer(U.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(mp4), '-vf', f"select='{sel}'",
                             '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-']), np.uint8)
    fs = Wd * Hd * 3 // 2
    out = []
    for i in range(len(a) // fs):
        b = a[i * fs:(i + 1) * fs]
        out.append((b[:Wd * Hd].reshape(Hd, Wd), b[Wd * Hd:Wd * Hd * 5 // 4].reshape(Hd // 2, Wd // 2),
                    b[Wd * Hd * 5 // 4:].reshape(Hd // 2, Wd // 2)))
    assert len(out) == len(ks), (mp4, len(out), len(ks))
    return out


def color_v02(mp4_v01, mp4_v02, EV, cada=5, muestra=None):
    """tela de la Blanca en los planos corregidos, medida en los dos másteres codificados con los mismos píxeles: la máscara
    sale del v01 con el modelo de neutro_v02.json (tela iluminada: peso > 0,8 y escala de luma > 0,85; sombra: peso > 0,5 y
    escala 0,45–0,75; estampado: resguardo_estampado > 0,5 dentro de la caja). Se mide el
    cambio de Cb/Cr entre v01 y v02 lejos de la remera (> 8 px de todo píxel con peso): solo debería quedar ruido de
    codificación."""
    # MC-04 con el contexto por defecto de mc04; MC-03 con el que fija mc03.ctx_v02() (M4.CTX)
    med = json.load(open(M4.CTX['med'] or M4.MED / 'neutro_v02.json'))
    planos = {p['id']: p for p in (M4.CTX['planos'] or json.load(open(M4.T / 'planos.json'))['planos'])}
    muestra = muestra or {'3': 100, '4': 135, '7': 255, '8': 307}
    mc03 = M4.CTX['sombra'] is False
    res, pares = {}, []
    for pid in M4.CTX['neutro']:
        p = planos[pid]
        ks = sorted(set(list(range(p['m0'], p['m0'] + p['nf'], cada)) + [muestra[pid]]))
        A_, B_ = _leer_420(mp4_v01, ks), _leer_420(mp4_v02, ks)
        tab = {q['k']: q for q in med[pid]['por_cuadro']}
        acc = {n: dict(px=0, a=np.zeros(3), b=np.zeros(3), br_b_min=99.0, br_b_max=-99.0) for n in ('iluminada', 'sombra', 'estampado')}
        amarillo, fuera, bajo, arena = 0, [], [], []
        M4.CTX['_pid'] = pid
        for k, (Ya, Cba, Cra), (Yb, Cbb, Crb) in zip(ks, A_, B_):
            mo = tab[min(tab, key=lambda j: abs(j - k))]['modelo']
            Yha, Yhb = M4._half(Ya), M4._half(Yb)
            w, sc = M4.peso_neutro(Yha, Cba, Cra, mo)
            x0, y0, x1, y1 = M4._caja_half(pid, k)
            caja = np.zeros(w.shape, bool); caja[y0:y1, x0:x1] = True
            res_e = M4.resguardo_estampado(Yha, Cba, Cra, caja, mo)
            w = w * M4.mascara_tela(Yha, Cba, Cra, pid, k, mo) * (1 - res_e)
            ra, rb = M4._rgb(Yha, Cba, Cra), M4._rgb(Yhb, Cbb, Crb)
            La = ra @ np.array([.2126, .7152, .0722], np.float32)
            # la corrección no cambia la luma: donde la luma cambia es la capa de textos (en MC-03 v02, el dato del hook A
            # en c0–c59), y esos píxeles quedan fuera de todas las medidas
            ig = np.abs(Yha - Yhb) < 6
            w = w * ig
            if mc03:
                # MC-03: la corrección empieza en L 170; «sombra» = lo que está a la sombra junto a la remera (L 40–160,
                # a ≤ 40 px de la tela corregida): la sombra proyectada, la pista, que no se tiene que mover
                from scipy import ndimage as nd
                cerca = nd.binary_dilation(w > 0.05, iterations=20)
                sel = {'iluminada': (w > 0.8) & (sc > 0.85), 'sombra': cerca & (La > 40) & (La < 150) & caja & ig,
                       'estampado': (res_e > 0.5) & caja & ig}
            else:
                sel = {'iluminada': (w > 0.8) & (sc > 0.85), 'sombra': (w > 0.5) & (sc > 0.45) & (sc < 0.75),
                       'estampado': (res_e > 0.5) & caja}
            dd = np.maximum(np.abs(Cbb.astype(int) - Cba), np.abs(Crb.astype(int) - Cra))
            bm = (La < 150) & caja & ig
            if bm.sum() > 200:
                bajo.append((float(np.percentile(dd[bm], 99)), float(dd[bm].mean())))
            bra = ra[..., 2] - ra[..., 0]
            am = (bra < -8) & (La > 60) & (w < 0.01) & ig
            if am.sum() > 200:
                arena.append((float(np.percentile(dd[am], 99)), float(dd[am].mean())))
            for n, m in sel.items():
                if m.sum() < 200:
                    continue
                a, b = ra[m].mean(0), rb[m].mean(0)
                c = acc[n]; c['px'] += int(m.sum()); c['a'] += a * m.sum(); c['b'] += b * m.sum()
                c['br_b_min'] = min(c['br_b_min'], float(b[2] - b[0])); c['br_b_max'] = max(c['br_b_max'], float(b[2] - b[0]))
            lit = sel['iluminada']
            if lit.sum() > 200:
                amarillo += int(((rb[..., 2] - rb[..., 0]) < 0)[lit].sum())
            # fuera de la remera: más de 8 px (media resolución) de cualquier píxel con peso > 0 (en el plano 4 la caja es
            # el cuadro entero, así que la caja sola no sirve para esto)
            from scipy import ndimage as nd
            lejos = ~nd.binary_dilation(w > 0.001, iterations=8) & ig
            d = np.maximum(np.abs(Cbb.astype(int) - Cba), np.abs(Crb.astype(int) - Cra))
            fuera.append((float(np.percentile(d[lejos], 99)) if lejos.any() else None,
                          float(np.percentile(d[lit], 50)) if lit.sum() > 200 else None,
                          float(np.abs(d[lejos]).mean()) if lejos.any() else None))
            if k == muestra[pid]:
                m = (w > 0.5)
                ys, xs = np.nonzero(m)
                cx, cy = int(xs.mean()) * 2, int(ys.mean()) * 2
                cw, ch = 600, 700
                bx0 = int(np.clip(cx - cw // 2, 0, M.W - cw)); by0 = int(np.clip(cy - ch // 2, 0, M.H - ch))
                pares.append((pid, k, (bx0, by0, bx0 + cw, by0 + ch)))
        r = dict(toma=p['toma'], cuadros=ks)
        for n, c in acc.items():
            if c['px'] == 0:
                r[n] = None
                continue
            a, b = c['a'] / c['px'], c['b'] / c['px']
            r[n] = dict(v01=dict(b_menos_r=round(float(a[2] - a[0]), 1), g_menos_r=round(float(a[1] - a[0]), 1)),
                        v02=dict(b_menos_r=round(float(b[2] - b[0]), 1), g_menos_r=round(float(b[1] - b[0]), 1)),
                        v02_b_menos_r_por_cuadro_min_max=[round(c['br_b_min'], 1), round(c['br_b_max'], 1)], px=c['px'])
        n_lit = acc['iluminada']['px']
        r['tela_iluminada_con_b_menos_r_negativo_pct'] = round(100 * amarillo / max(1, n_lit), 2)
        r['cambio_cb_cr_fuera_de_la_remera_p99_max'] = max(f[0] for f in fuera if f[0] is not None)
        r['cambio_cb_cr_fuera_de_la_remera_medio'] = round(max(f[2] for f in fuera if f[2] is not None), 2)
        r['cambio_cb_cr_tela_iluminada_mediana'] = [f[1] for f in fuera]
        r['cambio_cb_cr_L_menor_150_p99_medio'] = [max(f[0] for f in bajo), round(max(f[1] for f in bajo), 2)] if bajo else None
        r['cambio_cb_cr_arena_p99_medio'] = [max(f[0] for f in arena), round(max(f[1] for f in arena), 2)] if arena else None
        res[pid] = r
    # antes | después a tamaño real, un cuadro por plano (recorte 600×700 centrado en la tela)
    fnt = ImageFont.truetype(FONT, 28)
    Wd = Image.new('RGB', (2 * 604, len(pares) * 744), (24, 24, 24)); dr = ImageDraw.Draw(Wd)
    for i, (pid, k, caja) in enumerate(pares):
        fa, fb = M.leer_cuadros(mp4_v01, [k])[0], M.leer_cuadros(mp4_v02, [k])[0]
        for j, (f, rot) in enumerate(((fa, 'v01'), (fb, 'v02'))):
            Wd.paste(Image.fromarray(f).crop(caja), (j * 604, i * 744 + 44))
            dr.text((j * 604 + 6, i * 744 + 6), f'plano {pid}  c{k}  {rot}', font=fnt, fill=(255, 255, 0))
    Wd.save(EV / 'color_antes_v01_despues_v02_tamano_real.jpg', quality=93)
    M.jdump(res, EV / 'color_v02.json')
    return res


def control(pid, ver='v01'):
    d = pieza(pid, ver)
    T, NF, MAS = d['T'], d['NF'], d['mas']
    EV = d['ev']
    EV.mkdir(parents=True, exist_ok=True)
    planos = json.load(open(T / 'planos.json'))['planos']
    rep = dict(pieza=pid, version=ver, fecha='2026-11-25', archivos={})
    for k, nombre in d['nombres'].items():
        f = MAS / nombre
        pj, fi = ficha(f)
        M.jdump(pj, EV / f'ffprobe_{k}.json')
        niv, sil, v100 = niveles_planos(f, planos, NF)
        fi.update(niveles_por_plano=niv, ventanas_100ms_bajo_menos50dBFS=sil)
        rep['archivos'][k] = fi
        print(k, fi['md5_video'], fi['md5_audio'], fi['sonoridad'], fi['video']['cuadros_decodificados'], fi['audio']['duracion'],
              'gps', fi['marcas_gps_o_ubicacion'], 'faststart', fi['faststart'], flush=True)
    ref = MAS / d['nombres'][d['ref']]
    U.hoja_contacto(ref, EV / 'hoja_cada_0.5s.jpg', cada=15, cols=8, ancho=216)
    ultimo = NF - 1
    U.cuadros_corte(ref, d['cortes'], EV / 'cortes', ultimo)
    extra = sorted(set(d['giro'] + d['cta']))
    fr = M.leer_cuadros(ref, extra)
    for k, f in zip(extra, fr):
        Image.fromarray(f).save(EV / 'cortes' / f'c{k:03d}_giro_cta.jpg', quality=95)
    # vista a 360 px: un cuadro por plano (después de que responde la gráfica) + giro + CTA + último
    ks = sorted(set([p['m0'] + min(10, p['nf'] - 1) for p in planos] + extra + [0, ultimo] + ([14] if (ver, pid) == ('v02', 'MC-04') else [])))
    vista_360(ref, ks, EV / 'vista_360px.jpg')
    if pid == 'MC-03':
        fB = MAS / d['nombres']['B']
        vista_360(fB, [0, 2, 15, 45, 59], EV / 'vista_360px_hookB.jpg', cols=5)
        fr = M.leer_cuadros(fB, [0, 3, 30, 59])
        for k, f in zip([0, 3, 30, 59], fr):
            Image.fromarray(f).save(EV / 'cortes' / f'B_c{k:03d}.jpg', quality=95)
    # gráfica y textos por cuadro (de la misma función que arma la capa)
    ui = d['ui']()
    rep['grafica_cambios'] = estados_grafica(ui, NF)
    rep['textos_cambios'] = textos_por_cuadro(ui, NF)
    if (T / 'med' / 'estampado.json').exists():
        rep['margen_texto_estampado'] = {h: margen_texto_estampado(M.ui_mc03(h, ver)[0] if pid == 'MC-03' else ui, T / 'med' / 'estampado.json', NF)
                                         for h in (['A', 'B'] if pid == 'MC-03' else ['completa'])}
    # choques texto/estampado (medidos al componer, cuadro por cuadro)
    reg = json.load(open(MAS / 'registro_cuadros.json'))
    regs = reg if isinstance(reg, dict) else {d['ref']: reg}
    rep['choques_texto_estampado'] = {h: dict(cuadros_con_choque=[r['cuadro'] for r in rr if r.get('choque_px', 0) > 0],
                                              px_max=max([r.get('choque_px', 0) for r in rr] + [0]),
                                              cuadros_medidos=sum(1 for r in rr if 'estampado_caja' in r))
                                      for h, rr in regs.items()}
    for f in (T / 'med' / 'fantasmas_3375.json', T / 'med' / 'lento_3375_traslacion_descartado.json', T / 'audio' / 'sonoridad_wav.json'):
        if f.exists():
            shutil.copy2(f, EV / f.name)
    for f in ('estampado.json', 'estampado_resumen.json', 'estampado_c0-c429_c6.jpg', 'estampado_c0-c419_c6.jpg'):
        if (T / 'med' / f).exists():
            shutil.copy2(T / 'med' / f, EV / f)
    if pid == 'MC-03' and ver == 'v01':
        # plano 6: el estampado pasa de cortado a completo dentro del plano (tira a tamaño real, recorte del pecho)
        tira(ref, [160, 166, 170, 175, 182, 189], (0, 560, 1080, 1160), EV / 'plano06_cortado_a_completo.jpg')
        # plano 11: la Blanca entra desde la izquierda (c310–c312 la «s» de «so» toca el borde)
        tira(ref, list(range(310, 319)), (0, 640, 420, 1160), EV / 'plano11_entrada_c310-c318.jpg', cols=9)
        # cámara lenta por flujo óptico: cuadros reales y mezclados alternados, a tamaño real, sobre el estampado
        tira(ref, [320, 321, 322], (150, 600, 1080, 1100), EV / 'lento_tamano_real_c320-c322.jpg', cols=3)
        tira(ref, [331, 332, 333], (150, 600, 1080, 1100), EV / 'lento_tamano_real_c331-c333.jpg', cols=3)
        tira(ref, [362, 363, 364], (150, 600, 1080, 1100), EV / 'lento_tamano_real_c362-c364.jpg', cols=3)
        # c310–c369: «ROCCÉ / so f★cking close.» a 360 px sin texto encima
        vista_360(ref, [310, 318, 325, 340, 355, 369], EV / 'vista_360px_c310-c369.jpg', cols=6)
    rep['color_master'] = color_master(ref, planos, EV / 'color_master.json')
    forma_onda([(k, MAS / n) for k, n in d['nombres'].items() if 'B' != k], EV / 'forma_de_onda.png', NF / 30, d['cortes'])
    for k, f in d['audio'].items():
        ev = Path(str(f).replace('.wav', '_eventos.json'))
        if ev.exists():
            shutil.copy2(ev, EV / f'audio_eventos_{k}.json')
    shutil.copy2(T / 'planos.json', EV / 'planos.json')
    if (T / 'lento_3375.json').exists():
        shutil.copy2(T / 'lento_3375.json', EV / 'lento_3375.json')
    for h in sorted((T / 'hojas').glob('*.jpg')) if (T / 'hojas').exists() else []:
        shutil.copy2(h, EV / f'hoja_fuente_{h.name}')
    if ver == 'v02':
        # corrección 1 (blanca fría): color de la tela antes (v01) y después (v02) medido en los dos másteres codificados
        if pid == 'MC-03':
            M.ctx_v02()                      # fija mc04.CTX con los planos, cajas y rampa de MC-03
        rep['color_v02'] = color_v02(pieza(pid)['mas'] / pieza(pid)['nombres'][d['ref']], ref, EV, muestra=d.get('muestra'))
        for f in ('neutro_v02.json', 'neutro_v02_por_cuadro.json'):
            shutil.copy2(T / 'med' / f, EV / f)
        if pid == 'MC-04':
            # corrección 2 (datos en caja negra): entrada c12–c14 y c330–c332 a tamaño real
            tira(ref, [11, 12, 13, 14], (0, 300, 1080, 560), EV / 'caja_negra_c11-c14.jpg', cols=2)
            tira(ref, [329, 330, 331, 332], (0, 900, 1080, 1120), EV / 'caja_negra_c329-c332.jpg', cols=2)
        else:
            # corrección 2: dato del hook A en caja negra, con el estampado debajo (c0, c1 con pop de la caja del hook, c30, c59)
            tira(ref, [0, 1, 30, 59], (0, 400, 1080, 1000), EV / 'caja_negra_hookA_c0-c59.jpg', cols=2)
            if (T / 'med' / 'plano07_L170_descartado.jpg').exists():
                shutil.copy2(T / 'med' / 'plano07_L170_descartado.jpg', EV / 'plano07_L170_descartado.jpg')
    M.jdump(rep, EV / 'control.json')
    print(json.dumps({k: v for k, v in rep.items() if k in ('choques_texto_estampado',)}, ensure_ascii=False))
    return rep


def entregar(pid, ver='v01'):
    d = pieza(pid, ver)
    T = d['T']; EV = d['ev']; car = d['carpeta']; MAS = d['mas']
    car.mkdir(parents=True, exist_ok=True)
    res = {}
    for k, nombre in d['nombres'].items():
        src = MAS / nombre
        for dst in (M.EXP / nombre, car / nombre):
            if dst.exists():
                raise RuntimeError(f'{dst} ya existe: no se sobrescribe')
            shutil.copyfile(src, dst)
    ev = car / EV.name
    if ev.exists():
        raise RuntimeError(f'{ev} ya existe')
    shutil.copytree(EV, ev)
    hj = car / d['hoja']
    if hj.exists():
        raise RuntimeError(f'{hj} ya existe')
    shutil.copyfile(T / d['hoja'], hj)
    time.sleep(10)                     # releer ~10 s después de escribir en /mnt/project-files
    for k, nombre in d['nombres'].items():
        src = MAS / nombre
        ref = dict(md5_video=U.md5_stream(src, 'v'), md5_audio=U.md5_stream(src, 'a'))
        for dst in (M.EXP / nombre, car / nombre):
            got = dict(md5_video=U.md5_stream(dst, 'v'), md5_audio=U.md5_stream(dst, 'a'))
            res[str(dst)] = dict(got, bytes=dst.stat().st_size, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
                                 flujos_iguales_al_original=(got == ref))
            print(dst, res[str(dst)])
    res['evidencia'] = dict(carpeta=str(ev), archivos_local=sum(1 for _ in EV.rglob('*') if _.is_file()),
                            archivos_red=sum(1 for _ in ev.rglob('*') if _.is_file()))
    res['hoja'] = dict(ruta=str(hj), igual_a_la_local=(hj.read_bytes() == (T / d['hoja']).read_bytes()))
    M.jdump(res, T / d['entrega'])
    print(res['evidencia'])




# =====================================================================================================
# hoja de máster (spec 05 §Control): datos medidos de control.json + desvíos y decisiones de la receta
# =====================================================================================================
def _f(x, n=1):
    return f'{x:.{n}f}'.replace('.', ',')


def hoja(pid):
    d = pieza(pid)
    T = d['T']; EV = T / 'evidencia_v01'
    rep = json.load(open(EV / 'control.json'))
    planos = json.load(open(T / 'planos.json'))['planos']
    st = HOJA_03 if pid == 'MC-03' else HOJA_04
    L = [f"# {st['titulo']} · hoja de máster v01 · Pedro B · 25/11/2026", '',
         f"Guion: `04_fede_guiones_G1.md` §{pid} + condiciones de `06_roma_aprobacion_G1.md` + `05_especificacion_comun.md`. "
         f"Receta: `scripts/marca/{'mc03' if pid == 'MC-03' else 'mc04'}.py` (control: `scripts/marca/mc_control.py`). "
         f"Intermedios: `TRABAJO/marca/{pid}/`. Evidencia: `evidencia_v01/` (al lado de esta hoja).", '',
         '**Estado:** máster v01 para revisión de Roma. No se escuchó el audio (nadie lo reprodujo con parlante o auriculares): '
         'el sonido está controlado con medidores (ebur128, niveles por tramo, forma de onda) y la imagen con cuadros '
         'decodificados del MP4 final. No es una aprobación para publicar: quedan personas por confirmar (abajo).', '',
         '## Archivos e ID inmutable', '',
         '| Versión | Archivo | md5 flujo de video | md5 flujo de audio | Bytes (local) | sha256 (local) |', '|---|---|---|---|---|---|']
    for k, fi in rep['archivos'].items():
        L.append(f"| {k} | `{Path(fi['archivo']).name}` | `{fi['md5_video']}` | `{fi['md5_audio']}` | {fi['bytes']} | `{fi['sha256'][:16]}…` |")
    L += ['', 'El ID inmutable es el **md5 de los flujos** (`ffmpeg -i X -map 0:v -c copy -f md5 -`, ídem audio): la carpeta '
          'compartida agrega una caja C2PA al archivo y cambia su sha256, no sus flujos (comprobado en `entrega.json`).', '',
          '## Formato (ffprobe del MP4 final)', '',
          '| Versión | Video | Perfil · nivel | pix_fmt · color | Tamaño · fps | Cuadros decodificados | Duración video / audio | Audio | faststart | GPS | Errores de decodificación |',
          '|---|---|---|---|---|---|---|---|---|---|---|']
    for k, fi in rep['archivos'].items():
        v, a = fi['video'], fi['audio']
        L.append(f"| {k} | {v['codec']} | {v['perfil']} · {v['nivel'] / 10:.1f} | {v['pix_fmt']} · {'/'.join(str(c) for c in v['color'])} | "
                 f"{v['ancho']}×{v['alto']} · {v['fps']} | {v['cuadros_decodificados']} | {_f(v['duracion'], 3)} s / {_f(a['duracion'], 3)} s | "
                 f"{a['codec']} {a['perfil']} {a['hz']} Hz {a['canales']} can. | {'sí' if fi['faststart'] else 'NO'} | "
                 f"{'ninguna marca' if not fi['marcas_gps_o_ubicacion'] else fi['marcas_gps_o_ubicacion']} | {'ninguno' if fi['decodifica_completo'] else fi['errores']} |")
    L += ['', '## Sonoridad y niveles (medidos, no escuchados)', '',
          '| Versión | Integrada | Pico verdadero | LRA |', '|---|---|---|---|']
    for k, fi in rep['archivos'].items():
        s_ = fi['sonoridad']
        L.append(f"| {k} | {_f(s_['lufs_integrado'])} LUFS | {_f(s_['pico_dbtp'])} dBTP | {_f(s_['lra'])} LU |")
    for k, fi in rep['archivos'].items():
        if k in ('B',):
            continue
        L += ['', f'Niveles por plano · {k} (RMS / pico de muestra, dBFS):', '',
              '| Tramo | s | RMS | Pico |', '|---|---|---|---|']
        for n in fi['niveles_por_plano']:
            L.append(f"| {n['tramo']} | {_f(n['t0'], 3)}–{_f(n['t1'], 3)} | {_f(n['rms_dbfs'])} | {_f(n['pico_dbfs'])} |")
        L.append(f"\nVentanas de 100 ms por debajo de −50 dBFS: {fi['ventanas_100ms_bajo_menos50dBFS'] or 'ninguna'}.")
    L += ['', '## Línea de tiempo real contra el guion', '', st['tabla_cab']]
    for p, fila in zip(planos, st['filas']):
        L.append(fila.format(c0=p['m0'], c1=p['m0'] + p['nf'] - 1, s0=_f(p['m0'] / 30, 3), s1=_f((p['m0'] + p['nf']) / 30, 3)))
    L += ['', '### Cambios de la gráfica (leídos de la misma función que dibuja la capa)', '']
    for g in rep['grafica_cambios']:
        L.append(f"- c{g['cuadro']} ({_f(g['t'], 3)} s): {' · '.join(g['grafica'])}{'  ·  etiqueta ' + ', '.join(g['etiqueta']) if g['etiqueta'] else ''}")
    L += ['', '### Textos en pantalla (texto exacto, cuadros y caja visible x0, y0, x1, y1)', '']
    vis = {}
    for t in rep['textos_cambios']:
        for x in t['textos']:
            vis.setdefault((x['nombre'], x['texto']), []).append(t['cuadro'])
    ui = d['ui']()
    for (nom, txt), ks in vis.items():
        c0 = min(ks); c1 = c0
        while c1 + 1 < d['NF'] and any(it[0].texto == txt for it in ui(c1 + 1)[1]):
            c1 += 1
        caja_ = [x['caja_visible'] for t in rep['textos_cambios'] for x in t['textos'] if x['texto'] == txt][0]
        L.append(f"- c{c0}–c{c1} · {nom} · «{txt}» · caja {caja_}")
    L += ['', '## Desvíos del guion y de las condiciones, con su motivo', ''] + st['desvios']
    L += ['', '## Condiciones de Roma (06) y criterios del encargo', ''] + st['condiciones']
    ch = rep['choques_texto_estampado']
    L += ['', '## Texto y estampado', '',
          'Medido cuadro por cuadro al componer: píxeles de la capa de texto y gráfica con alfa > 0,15 sobre la máscara del '
          'estampado dilatada 8 px. ' + ' · '.join(f"{h}: {v['cuadros_medidos']} cuadros medidos, {len(v['cuadros_con_choque'])} con choque"
                                                   + (f" ({v['cuadros_con_choque'][:12]}…, máx. {v['px_max']} px)" if v['cuadros_con_choque'] else '')
                                                   for h, v in ch.items()) + '.']
    for h, mg in rep.get('margen_texto_estampado', {}).items():
        mn = mg['minimo']
        if mn:
            L.append(f"- Margen mínimo entre cajas ({h}): {mn['margen_px']} px en c{mn['cuadro']} ({mn['elemento']} «{mn['texto']}» "
                     f"{mn['caja_el']} contra el estampado {mn['caja_estampado']}). Por elemento: "
                     + '; '.join(f"{n} {r['margen_px']} px (c{r['cuadro']})" for n, r in mg['por_elemento'].items()) + '.')
    L += st['estampado']
    if pid == 'MC-03' and (EV / 'lento_3375.json').exists():
        lj = json.load(open(EV / 'lento_3375.json'))
        cu = lj['cuadros']; mez = [c for c in cu if c['tipo'] != 'real']
        conm = [c for c in mez if c.get('estampado')]
        dmax = max(conm, key=lambda c: c['estampado']['desacuerdo_mayor_40_pct'])
        altos = [c['k'] + 310 for c in conm if c['estampado']['desacuerdo_mayor_40_pct'] > 1.0]
        pos = [c['pos_fuente'] for c in cu]
        rep_pos = sum(1 for a_, b_ in zip(pos, pos[1:]) if abs(a_ - b_) < 1e-6)
        fan = json.load(open(EV / 'fantasmas_3375.json')) if (EV / 'fantasmas_3375.json').exists() else []
        L += ['', '## Cámara lenta (c310–c429)', '',
              f"- {len(cu)} cuadros: {len(cu) - len(mez)} cuadros reales de 3375 y {len(mez)} interpolados por flujo óptico "
              f"({lj['metodo']}). Posiciones de fuente repetidas entre cuadros seguidos: {rep_pos} (sin tartamudeo).",
              f"- Desacuerdo entre las dos imágenes deformadas sobre el estampado (|ΔY| > 40): máximo "
              f"{_f(dmax['estampado']['desacuerdo_mayor_40_pct'], 2)} % en c{dmax['k'] + 310}; por encima de 1 % en "
              f"{', '.join('c' + str(k) for k in altos) or 'ningún cuadro'}. En esas zonas se toma solo el cuadro más cercano, sin mezclar.",
              (f"- Con la traslación única descartada, el mismo desacuerdo iba de {_f(min(r['comp_frac'] for r in fan[:30]) * 100, 1)} a "
               f"{_f(max(r['comp_frac'] for r in fan[:30]) * 100, 1)} % en la revelación (fuente c9–c39)." if fan else ''),
              '- Revisión a tamaño real (cuadro real, interpolado, real): `lento_tamano_real_*.jpg`. Sin doble contorno visible; el '
              'desenfoque de movimiento que se ve viene de la toma original (aparece igual en los cuadros reales vecinos).']
    L += ['', '## Color medido en el máster (un cuadro por plano)', '', '| Plano | Cuadro | Toma | Blanco B−R / G−R | Oscuro B−R / G−R |', '|---|---|---|---|---|']
    for c in rep['color_master']:
        b = c['blanco']; o = c['oscuro']
        L.append(f"| {c['plano']} | c{c['cuadro']} | {c['toma']} | {'—' if not b else _f(b['b_menos_r']) + ' / ' + _f(b['g_menos_r'])} | "
                 f"{'—' if not o else _f(o['b_menos_r']) + ' / ' + _f(o['g_menos_r'])} |")
    L += st['color']
    L += ['', '## Evidencia (`evidencia_v01/`)', ''] + st['evidencia']
    L += ['', '## Verificado técnicamente', ''] + st['verificado']
    L += ['', '## Revisado visualmente (cuadros decodificados del MP4 final)', ''] + st['visual']
    L += ['', '## Pendiente de revisión humana', ''] + st['pendiente']
    L += ['', '## Personas y frases a confirmar (no frenan el v01; frenan la publicación)', ''] + st['personas']
    (T / '01_pedro_hoja_master_v01.md').write_text('\n'.join(L) + '\n')
    print(T / '01_pedro_hoja_master_v01.md')


CAB = ('| Plano | Máster (cuadros · s) | Archivo · tramo fuente | Encuadre / proceso | Texto en pantalla | Gráfica | Sonido | Función | Desvío |\n'
       '|---|---|---|---|---|---|---|---|---|')
HOJA_03 = dict(
    titulo='MC-03 «0-40»', tabla_cab=CAB,
    filas=[
        '| 1 | c{c0}–c{c1} · {s0}–{s1} | IMG_7999 · c101–c160 (3,367–5,367) | completo; rango completo → limitado | «0-40. ¿Lo damos vuelta?» (Caja 76, pop, y 420) · **A:** «La sesión de fotos de Roccé, / punto por punto.» (Dato 48, y 620) · **B:** burbuja «Pasamos de estar cerca a / hacerlo??? 🤫🤫💎» + «Comentario en TikTok» (50 px, pop, y 562) | marcador «● ROCCÉ 0 / LA SESIÓN 40» (x 60–600, y 250) | amb 7999 −6 (hp 200) · toque del pop c0 · pad Mi menor · charles · campana y bombo c0 · pulso 0,667 y 1,333 | APUESTA + PISTA | caja con relleno compacto; burbuja en y 562 (ver desvíos) |',
        '| 2 | c{c0}–c{c1} · {s0}–{s1} | clip_f2a34e51 · c30–c49 (1,000–1,667) | nativo 576×1024 escalado (lanczos) | «0-15: ARENA.» (Placa 88) · etiqueta «REPETICIÓN» c60–c119 | sigue 0-40 | barrido de bajada + toque 2,000 · bombo · amb −10 (hp 150) | EN CONTRA | — |',
        '| 3 | c{c0}–c{c1} · {s0}–{s1} | IMG_8002 · c45–c64 (1,500–2,167) | completo | «0-30: CORTADA.» (Placa 88) · «REPETICIÓN» | — | barrido + toque 2,667 · bombo · amb −8 | EN CONTRA | — |',
        '| 4 | c{c0}–c{c1} · {s0}–{s1} | IMG_7999 · c81–c100 (2,700–3,367) | completo | «0-40: LA SOMBRA.» (Placa 88) · «REPETICIÓN» | — | barrido + toque 3,333 · bombo · amb −6 | EN CONTRA · repite la pista | — |',
        '| 5 | c{c0}–c{c1} · {s0}–{s1} | IMG_7884 · c96–c135 (3,200–4,533) | completo | «TRIPLE BREAK POINT.» (Placa 88) · etiqueta «BREAK POINT» celeste c126–c159 (titila 5/3 c) | 0-40 | ola real −4 · bombo 4,0 · campana 4,000 y 4,333 · toque 4,2 (entra la etiqueta) | SUBE LA APUESTA | — |',
        '| 6 | c{c0}–c{c1} · {s0}–{s1} | IMG_8002 · c73–c102 (2,433–3,433) | completo | «MISMA TOMA, / UN SEGUNDO DESPUÉS.» (Placa 82) | c166 → 15-40 (la celda destella 3 c) | golpe de pelota 5,533 · bombo 5,333 · bajo + acorde Sol | A FAVOR · estampado cortado c160–c174 → completo desde c175 | tramo 2,433–3,433 en vez de 2,60–3,60 |',
        '| 7 | c{c0}–c{c1} · {s0}–{s1} | clip_f2a34e51 · c165–c194 (5,500–6,500) | nativo escalado (lanczos) | «LA BLANCA, / EN LA MISMA ARENA.» (Placa 86) | c196 → 30-40 | golpe de pelota 6,533 · bombo · bajo + La menor | A FAVOR | — |',
        '| 8 | c{c0}–c{c1} · {s0}–{s1} | IMG_4627 · c51–c80 (1,700–2,700) | nativo HDR → SDR | «IGUALES.» (Placa 88) · etiqueta «IGUALES» c226–c249 | c226 → 40-40 | golpe de pelota 7,533 · ola real −6 · aplauso 7,6 (0,8 s) · bajo + Si menor | A FAVOR | — |',
        '| 9 | c{c0}–c{c1} · {s0}–{s1} | IMG_7896 · c30–c59 (1,000–2,000) | completo | «VENTAJA ROCCÉ.» (Placa 88) | c256 → AD-40 | golpe de pelota 8,533 · subida 8,333–9,333 · bajo + Do | A FAVOR | — |',
        '| 10 | c{c0}–c{c1} · {s0}–{s1} | IMG_7999 · c160 congelado (5,333) | acercamiento real 1,30 → 1,40 (recorte subpíxel lanczos por cuadro, centro natural 860, 1720) | «Punto de game. / ¿Qué tapaba la sombra?» (Placa 82) | «AD» titila (6 c / 6 c) | música fuera · amb 7999 −20 (lp 2500) · latidos 9,6 y 10,0 | GRAN PREGUNTA (cobra la pista) | cuadro 160 (el 5,367 no existe); acercamiento por la condición 1 |',
        '| 11-12 | c{c0}–c{c1} · {s0}–{s1} | IMG_3375 · c9–c68 (0,300–2,300) | HDR → SDR; ×0,5 (c310–c369 = fuente 0,30–1,30) y ×0,49 (c370–c429 = 1,30–2,27) con mezcla compensada por flujo óptico; c370–c429 acercamiento 1,00 → 1,06 anclado arriba; blanco por cuadro → B−R −3 | c310–c324 sin texto · c325–c369 «Estar cerca / y seguir sacando.» (Placa 84) · c370–c429 «Mandáselo al que / hoy está 0-40.» (Caja 76, pop) | c340 → «GAME · ROCCÉ» (pop) | latidos que se aceleran 10,40–11,15 + subida · GAME 11,333: bombo, impacto, campanas, aplauso 1,6 s, pad Sol mayor · toque CTA 12,333 · bombo 13,0 y 13,667 · fundido 13,83–14,333 · amb 4627 −18 (3375 no tiene audio) | GIRO + prueba de ropa (11) · CTA (12) | condición 1 de Roma: el cierre se mueve (ver desvíos) |',
    ],
    desvios=[
        '1. **Plano 6 (c160–c189):** 8002 de 2,433 a 3,433 s en lugar de 2,60–3,60. La toma termina en el cuadro 106 (3,533 s) y desde c104 la R de ROCCÉ toca el borde. El estampado entra cortado (c160–c174) y queda completo desde c175: el pase de cortado a completo ocurre dentro del plano (`evidencia_v01/plano06_cortado_a_completo.jpg`). El 15-40 llega en c166, con el estampado todavía cortado (el marcador anticipa lo que se ve 0,3 s después).',
        '2. **Plano 10 (c280–c309):** congelado del cuadro 160 de 7999 (5,333 s). El 5,367 del guion no existe: la toma termina en el 160. Lleva un acercamiento real de 1,30 a 1,40 (condición 1), no un zoom fijo.',
        '3. **Planos 11-12 (c310–c429), condición 1:** el plano 11 usa 3375 0,30–1,30 a ×0,5. Es la única lectura que llena c310–c369 con ese tramo sin repetir cuadros. El plano 12 usa 1,30–2,27 a ×0,49, porque 3375 termina en el cuadro 68. En el plano 12 hay un acercamiento de 1,00 a 1,06 anclado arriba y centrado en x 705: el estampado baja y se aleja de la caja del CTA.',
        '4. **Mezcla de cuadros por flujo óptico** (Lucas–Kanade piramidal en numpy/scipy) en vez de `minterpolate=mi_mode=blend` o `tblend`. Durante la revelación el estampado se mueve hasta 22 px por cuadro y rota, así que una mezcla simple o una sola traslación deja doble contorno sobre «ROCCÉ / so f★cking close.»:',
        '   - Traslación única (primer intento): 5–13 % de píxeles en desacuerdo > 40 niveles (`fantasmas_3375.json`).',
        '   - Flujo: el desacuerdo cae a lo indicado en «Cámara lenta». Donde las dos imágenes no coinciden se toma solo el cuadro más cercano.',
        '   - Se probó también OpenCV (DIS) y se descartó porque la especificación 05 excluye OpenCV. Se borró su instalación aislada.',
        '5. **Placas de 2 renglones a 82, 86 y 84 px** (guion: 88). A 88 px exceden el ancho útil. Todas quedan dentro de 76–96 px.',
        '6. **Halo de placas y datos más denso** que el de `comun.placa` por defecto: placa 0,95 con 16 px (por defecto 0,55) y dato 0,9 con 12 px. Con 0,55, el texto blanco sobre la tela blanca (planos 10–11) y sobre la espuma se leía mal a 360 px (`halo_prueba_360px.png`). No se modificó `comun.py`.',
        '7. **Hook:** la caja usa el relleno compacto del CTA (28/14 px; termina en y 552). La burbuja del hook B va en y 562 (guion: «en el mismo lugar» del Dato, y 620), con texto de 50 px (el mínimo de la especificación), relleno 28 e interlineado 1,0. Motivo: en c59 el estampado de 7999 llega a y ≈ 840. Así la tarjeta termina en y ≈ 791 y no lo toca.',
        '8. **Marcador en «GAME»:** una sola banda «GAME · ROCCÉ» (celda celeste en GAME) en lugar de las dos filas.',
        '9. **Sonido (TEMP, sintetizado):**',
        '   - **Hook:** la primera mezcla medía −34,6 dB RMS en c0–c59, 22 dB por debajo del resto. Pad 0,05 → 0,09, charles más alto y pulso de bombo en 0 / 0,667 / 1,333 s (grilla de los cortes). Ahora mide −14 / −19 dB.',
        '   - **Remontada:** acordes Sol–Lam–Sim–Do sobre el bajo (5,33–8,33).',
        '   - **c310–c339:** latidos que se aceleran y una subida hasta el GAME. Antes eran 2 s seguidos casi sin energía (−35 dB RMS).',
        '   - **Cierre:** pad de Sol mayor hasta el final, con bombo en 13,0 y 13,667 y fundido 13,83–14,333.',
        '   - **Sin música:** latidos e impacto a la mitad de ganancia (quedaban 15 dB por encima del ambiente).',
        '   - **Aplausos** sintetizados (provisorios).',
        '   - **Pico verdadero:** pasada final con limitador sobremuestreado a 192 kHz. `sonido.exportar` limita el pico de muestra, no el verdadero.',
        '10. **Blanco de 3375 por cuadro:** B−R −3 / G−R 0 con media móvil de 7 cuadros. Medido de −8 a −19, cálido; la foto de producto da −4,4. Las tomas de playa al sol (+15 a +22) quedan como están: coinciden con la foto de producto exterior `blanca_puesta_frente_detalle_mar` (+23). 7884 mide +10,6 (≤ +12), sin neutralizar.',
        '11. **Pop del CTA anclado abajo (c370–c371):** la caja del CTA termina en y 634, y el estampado empieza en y 650 en c370. Con el pop centrado (×1,18) el borde inferior bajaba a y 653 y tocaba «ROCCÉ» en c370: era el único choque del primer máster (608 px, A y B). Ahora el borde inferior queda fijo y el pop crece hacia arriba. En c370 la caja cubre 21 px del margen azul del marcador (y 381–402), por debajo de la pastilla GAME, sin tapar texto (`cortes/c370.jpg`). En reposo, el margen mínimo con el estampado es de 16 px (c370) y después crece.',
        '12. **Entrada de la Blanca en el plano 11 (c310–c312), para decidir:** con 3375 desde 0,30 s (condición 1), la remera entra desde la izquierda. La «s» de «so» sale cortada por el borde en c310 y c311, en c312 apenas lo toca y desde c313 está completa con margen (`evidencia_v01/plano11_entrada_c310-c318.jpg`). «ROCCÉ» se lee completo en todos esos cuadros. Son 0,1 s de movimiento con desenfoque, durante la revelación y sin texto. Propuesta: dejarlo así, como entrada a cuadro. Alternativa: empezar en 0,40 s (fuente c12). Eso obliga a estirar 1,90 s de fuente en 4,0 s (×0,475 en vez de ×0,5) y agrega cuadros interpolados en la revelación.',
        '13. **Pop de la portada (c0–c1):** la caja del hook mide 917 px de ancho. Con el pop estándar (×1,18), en c0 iba de x −1 a 1081 y cortaba sus esquinas contra el borde del cuadro, justo en la portada. El pop se reduce en proporción solo cuando la caja no entra con 40 px por lado: el hook queda en ×1,09 / ×1,045 (x 40–1040). El CTA, la burbuja y GAME conservan ×1,18 / ×1,09. En el hook B, la burbuja ancla su pop arriba: centrada, en c0 se montaba 20 px sobre la caja del hook. Ahora crece hacia abajo (y 564–849), donde en c0 no hay estampado (y ≥ 1450). Ver `cortes/c000.jpg` y `cortes/B_c000.jpg`.',
    ],
    condiciones=[
        '- **1 · Cierre de MC-03 sin congelado:** cumplido. El plano 11 es la revelación de 3375 a ×0,5. El plano 12 es 3375 1,30–2,27 a ×0,49 con mezcla de cuadros y acercamiento de 1,00 a 1,06. El congelado del plano 10 lleva acercamiento de 1,30 a 1,40.',
        '- **2 · Cámara lenta sin tartamudeo ni fantasmas:**',
        '  - Ningún cuadro de salida repite la posición de fuente del anterior (`lento_3375.json`, campo `pos_fuente`).',
        '  - Fantasmas controlados a tamaño real: `lento_tamano_real_*.jpg` (cuadro real, mezclado, real).',
        '- **3 · Hook B:** la burbuja con el comentario real y los emoji de Noto Color Emoji (tamaño 109, escalado), sin usuario. Solo en el máster B.',
        '- **4 · Texto nunca sobre el estampado:** ver «Texto y estampado».',
        '- **5 · Color:** ver la tabla y el punto 10 de los desvíos. La Negra del clip (planos 2 y 7) no tiene corrección: se mide en la tabla.',
        '- **6 · Interfaz con `comun.py`:**',
        '  - Caja, placa, fuentes y colores salen de `comun.py`, sin modificarlo.',
        '  - Marcador propio de transmisión: caja azul noche #0F1C2E al 90 %, distinto del de MC-01.',
        '  - Cada gráfica responde 6 cuadros después del corte, con su golpe: c126 BREAK POINT (corte c120, toque 4,2), c166 (c160, golpe de pelota 5,533), c196 (c190, 6,533), c226 (c220, 7,533), c256 (c250, 8,533).',
        '  - GAME entra en c340, en el giro del guion, con bombo, impacto, campanas y aplauso.',
        '- **7 · Personas:** abajo.',
        '- **8 · Para Gianluca:** de MC-03 solo aplica el permiso para mostrar el comentario sin usuario (hook B).',
        '- **Marcador del encargo:** 0-40 (c0) → 15-40 (c166) → 30-40 (c196) → 40-40 (c226) → AD (c256) → GAME (c340). Comprobado en «Cambios de la gráfica».',
        '- **c310–c369:** «ROCCÉ / so f★cking close.» legible a 360 px y sin texto encima: `vista_360px_c310-c369.jpg` y margen medido.',
    ],
    estampado=[
        '',
        '- **Planos 1 y 10 (7999):** la Blanca está a la sombra de quien filma y la máscara automática de «tela clara» no la ve; los bordes de la sombra daban falsos positivos.',
        '  - Plano 1: caja medida a mano en c59 sobre una rejilla de 50 px y seguida cuadro a cuadro por correlación de fase.',
        '  - Plano 10: caja medida en c280 y c309 e interpolada.',
        '  - Las cajas están dibujadas en `estampado_c0-c429_c6.jpg`.',
        '- **c318 (plano 11-12):** la caja automática sube a y 560 y llega a x 1075 por un falso positivo de borde. Ese cuadro no tiene texto (c310–c324 van sin texto).',
        '- **Etiqueta interior del cuello de 7999:** es tejida, con la marca, y no está en la lista de estampados de Roma. En c18–c35 la toma la sube por x 90–230 e y ≈ 550–720. La burbuja del hook B va corrida 30 px a la derecha (x 252–887) para no taparla. El borde inferior de la caja del hook (y 552) roza su parte de arriba en c26–c35 (A y B): la caja no puede moverse sin salir de y 420 del guion.',
    ],
    color=['', 'La «Blanca» se mide como la tela lisa más grande con L > 170 y saturación < 0,15; el «Oscuro», como la mediana de 10 < L < 55. En los planos sin Negra, el oscuro es sombra o roca.'],
    evidencia=[
        '- `control.json`: todas las mediciones de esta hoja. `ffprobe_*.json`.',
        '- `cortes/`: c0, cada corte (n−1, n, n+1), giro (c310, c325, c340), CTA (c370, c380, c429) y último, a tamaño real. Hook B: `B_c000/003/030/059.jpg`.',
        '- `hoja_cada_0.5s.jpg`.',
        '- Vistas a 360 px de ancho: `vista_360px.jpg`, `vista_360px_hookB.jpg`, `vista_360px_c310-c369.jpg`.',
        '- `plano06_cortado_a_completo.jpg`: el estampado de cortado a completo, a tamaño real.',
        '- `plano11_entrada_c310-c318.jpg`: borde izquierdo del plano 11 (x 0–420, y 640–1160) a tamaño real; la «s» de «so» completa desde c313.',
        '- Cámara lenta a tamaño real: `lento_tamano_real_c320-c322.jpg`, `lento_tamano_real_c331-c333.jpg`, `lento_tamano_real_c362-c364.jpg`. Registro por cuadro en `lento_3375.json`; comparación con la traslación descartada en `fantasmas_3375.json` y `lento_3375_traslacion_descartado.json`.',
        '- Estampado: `estampado_c0-c429_c6.jpg` (máscara roja, caja amarilla y capa de texto del hook B), `estampado.json` y `estampado_resumen.json`.',
        '- `color_master.json`.',
        '- Sonido: `forma_de_onda.png`, `audio_eventos_*.json` (cada golpe con su tiempo) y `sonoridad_wav.json`.',
        '- Hojas de las fuentes cada 0,1 s (tramos dudosos, antes del render): `hoja_fuente_*.jpg`. Prueba de halo: `halo_prueba_360px.png`.',
    ],
    verificado=[
        '- Los tres MP4 decodifican completos sin errores. Los cuadros contados coinciden con 430 y la duración de audio con la de video (tabla de formato).',
        '- H.264 High 4.0, yuv420p, BT.709 de rango limitado, 1080×1920, 30 fps, AAC-LC 48 kHz estéreo, faststart. Sin marcas de ubicación ni GPS.',
        '- `_SINMUSICA` lleva el mismo flujo de video que A: md5 de video idéntico.',
        '- Sonoridad y pico verdadero medidos con ebur128 sobre el MP4 final.',
        '- Estado de la gráfica y texto por cuadro, leídos de la misma función que dibuja la capa. Choques de texto con el estampado medidos píxel a píxel en los 430 cuadros de A y de B.',
    ],
    visual=[
        '- Cuadros de corte, giro, CTA, c0 y último; hoja cada 0,5 s; vistas a 360 px; tiras a tamaño real del plano 6, de la entrada del plano 11 (c310–c318) y de la cámara lenta.',
        '- Textos exactos: ROCCÉ, «so f★cking close.» (en la prenda) y voseo de «Mandáselo».',
        '- La Blanca y la Negra sin dominante marrón ni azul en los cuadros revisados.',
    ],
    pendiente=[
        '- **Escucha del audio:** no se escuchó. Falta confirmar en parlante de teléfono el pop de c0, los golpes de pelota con cada punto, el casi silencio del plano 10, el GAME de c340 y que la música TEMP no tape el ambiente.',
        '- **Reproducción continua a velocidad real:** se revisaron cuadros, no movimiento. Falta mirar la cámara lenta de c310–c429 en un teléfono por si hay saltos o una deformación sutil (sobre todo en c331–c339 y c363, donde el flujo tuvo más desacuerdo), y la fluidez del acercamiento del plano 10.',
        '- **Legibilidad a 360 px en un teléfono real.**',
    ],
    personas=[
        '- **7884** (plano 5, c120–c159): brazo y celular en el borde derecho; ¿Gianluca? (06, condición 7).',
        '- **7999** (planos 1, 4 y 10): sombra de quien filma (silueta, sin cara).',
        '- **Comentario real del hook B** «Pasamos de estar cerca a hacerlo??? 🤫🤫💎»: falta el permiso de Gianluca para mostrar comentarios sin usuario (06, condición 8).',
    ],
)
HOJA_04 = dict(
    titulo='MC-04 «¿Founder 001 o Founder 100?»', tabla_cab=CAB,
    filas=[
        '| 1 | c{c0}–c{c1} · {s0}–{s1} | IMG_4530 · 0,000–1,468 (29,97 → 30) | nativo HDR → SDR | «¿Founder 001 / o Founder 100?» (Caja 76, pop, y 236) · c12 «Los primeros 100 compradores de Roccé, / numerados 001–100.» (Dato 46, y 470) | barra en y 600; ficha «001» celeste, «100» blanca; la ficha derecha rueda 001 → 100 en c0–c20 | amb −8 · un toque por número · pad La menor · bombo c0 + pulso 0,5 y 1,0 | APUESTA + PISTA | Dato en y 470 (guion 440) |',
        '| 2 | c{c0}–c{c1} · {s0}–{s1} | IMG_3453 · 1,600–2,567 | nativo HDR → SDR + corrección de TOMAS + Negra neutralizada | «EL 001 DISEÑA / UNA PRENDA A SU GUSTO.» (Placa 74) · rótulo «¿QUIÉN ES MÁS FOUNDER?» (Dato 48, y 450) c45–c299 | barra en y 520; c51 → −1 | barrido con paneo hacia el 001 + toque · bombo 1,5 · amb 4530 −16 (3453 no tiene audio) | A FAVOR 001 | placa a 74 px |',
        '| 3 | c{c0}–c{c1} · {s0}–{s1} | IMG_8004 · 3,400–4,867 | completo | «Y SE LLEVA UN PORCENTAJE / DE LA GANANCIA DE ESA PRENDA.» (Placa 57) | c81 → −3 (tope); la ficha «001» brilla c81–c155 | barrido + toque · brillo · campana 2,7 · bombo 2,5 · amb −8 | A FAVOR 001 · goleada | placa a 57 px |',
        '| 4 | c{c0}–c{c1} · {s0}–{s1} | IMG_7996 · 3,000–3,967 | completo; rango completo → limitado | «¿Y EL 100?» (Caja 76, pop) | sigue en −3; la ficha «100» pasa a gris en c126 | toque grave c126 · música fuera 4,4–5,0 · amb −6 (hp 200) | GRAN PREGUNTA | — |',
        '| 5 | c{c0}–c{c1} · {s0}–{s1} | IMG_4631 · 0,000–1,467 | z 1,15 fijo sobre las remeras, anclado abajo a la derecha | «ATRÁS DICEN LO MISMO.» (Placa 78) | c156 → −2; la ficha «100» se vuelve a encender | barrido hacia el 100 + toque · Do mayor desde 5,0 · amb −6 | GIRO 1 (cobra la pista) | — |',
        '| 6 | c{c0}–c{c1} · {s0}–{s1} | IMG_7824 · 6,001–7,469 (29,97 → 30) | z 1,06 anclado arriba | «LOS 100, EN UN GRUPO PRIVADO / DE WHATSAPP CON GIANLUCA.» (Placa 61) | c201 → −1 | barrido + toque · bombo 6,5 · amb −8 | GIRO 2 | z 1,06 (guion: completo); placa a 61 px |',
        '| 7 | c{c0}–c{c1} · {s0}–{s1} | IMG_7999 · 0,000–1,467 | completo | c240 «¿Y SI EL 001 NO / QUIERE DISEÑAR?» (Placa 80) · c262 «PASA AL 002. AL 003…» (Placa 86) | la ficha izquierda rueda 002 (c262) → 003 (c266) → «…» (c270–c284); c268 → 0 | toques c262, c266 y c270 · barrido c268 · subida 8,0–9,5 · bombo 8,0 · amb −6 | GIRO 3 · vuelta de tuerca | «¿Y SI EL 001 NO / QUIERE DISEÑAR?» en dos renglones |',
        '| 8 | c{c0}–c{c1} · {s0}–{s1} | clip_a592f367 · 0,000–1,467 | nativo 576×1024 escalado (lanczos) | «EL NÚMERO ES EL ORDEN.» (Placa 76) · c300 «Founders son los 100.» (Dato 50, y 450) | la ficha izquierda vuelve a «001» en c285; marca central celeste desde c291 | drop 9,5: impacto, bombo, bajo con glide, campana y pad · toque c291 · amb −10 (hp 150) | RESOLUCIÓN | — |',
        '| 9 | c{c0}–c{c1} · {s0}–{s1} | IMG_4627 · 10,000–12,967 | nativo HDR → SDR | «¿001 o 100?» (Caja 76, pop) + «Comentá cuál y por qué.» (Dato 52, y 440) | barra al centro; fichas iguales (las dos blancas) desde c336 | campana 11,0 · groove bombo/palma · toque c336 · ola real −6 · fundido 13,5–14,0 | REENGANCHE + CTA | — |',
    ],
    desvios=[
        '1. **Hook (c0–c44):** la caja va en dos renglones, «¿Founder 001 / o Founder 100?», porque a 76 px en uno mide 1082 px y no entra. Por eso el Dato baja a y 470 (guion 440) y la barra del plano 1 va en y 600 (guion: 580–680).',
        '2. **Placas por debajo del rango 76–96 px de la especificación:** «EL 001 DISEÑA / UNA PRENDA A SU GUSTO.» 74 px · «Y SE LLEVA UN PORCENTAJE / DE LA GANANCIA DE ESA PRENDA.» 57 px · «LOS 100, EN UN GRUPO PRIVADO / DE WHATSAPP CON GIANLUCA.» 61 px.',
        '   - A 76 px, sus renglones miden 1059–1264 px: no entran en 2 renglones, y el texto es exacto (no se acorta).',
        '   - Se leen a 360 px (`vista_360px.jpg`).',
        '   - **Para Roma (c75–c119 y c195–c239):** confirmar 57/61 px, o pasar esas dos reglas a 3 renglones de 76 px. Eso rompe el máximo de 2 renglones y baja la barra.',
        '3. **«¿Y SI EL 001 NO / QUIERE DISEÑAR?»** en dos renglones (80 px).',
        '4. **Plano 6 (c195–c239):** 7824 con z 1,06 anclado arriba (guion: completo). En c195 la tilde de ROCCÉ (tono sobre tono) está en y ≈ 650 y la barra ocupa y 520–620: sin el acercamiento se tocaban.',
        '5. **Rodillo de la ficha izquierda:** 002 (c262–c265), 003 (c266–c269) y «…» hasta c284 (guion: c262–c280). Vuelve a «001» en c285, con «EL NÚMERO ES EL ORDEN.».',
        '6. **Negra de 3453 (plano 2):** después de la corrección de TOMAS medía B−R −20 / G−R −16,5 (marrón). Se resta la croma mediana de la tela solo en los oscuros (peso 1 con L < 70, se apaga hasta L 130; la piel y el relieve no cambian) y queda en −1 a −2 / −1,5 a −2,2 (`planos.json`, `negra_antes` y `negra_despues`).',
        '7. **Halo de placas y datos más denso** que `comun.placa` por defecto (0,95 con 16 px y 0,9 con 12 px). El cielo de 4530 y 7824 y la espuma de 4627 dejaban el Dato blanco casi ilegible a 360 px. No se modificó `comun.py`.',
        '8. **Sonido (TEMP, sintetizado):**',
        '   - **Hook:** c21–c44 medía −36 dB RMS, un hueco dentro del hook. Pad 0,05 → 0,09, charles más alto y pulso de bombo en 0,5 y 1,0 s (120 BPM).',
        '   - **Sin música:** impacto a la mitad de ganancia (quedaba 18 dB por encima del resto).',
        '   - **Pico verdadero:** pasada final con limitador sobremuestreado a 192 kHz. La mezcla sin música daba −0,2 dBTP con `sonido.exportar`.',
    ],
    condiciones=[
        '- **Barra sin números de votos:** −1 c51, −3 c81, −2 c156, −1 c201, 0 c268. Comprobado en «Cambios de la gráfica». El cuadro anterior a cada salto muestra el 60 % del recorrido.',
        '- **Reglas de Founders con el texto exacto de la tabla:** sin cifras, fechas, «cada Founder» ni «ganá».',
        '  - «EL 001 DISEÑA UNA PRENDA A SU GUSTO.»',
        '  - «Y SE LLEVA UN PORCENTAJE DE LA GANANCIA DE ESA PRENDA.»',
        '  - «LOS 100, EN UN GRUPO PRIVADO DE WHATSAPP CON GIANLUCA.»',
        '  - «¿Y SI EL 001 NO QUIERE DISEÑAR?» / «PASA AL 002. AL 003…» (regla aprobada por Roma en 06).',
        '- **Sin chat, sin grupo en pantalla y sin una persona presentada como Founder.** Las manos de 4530 y 7824 y la persona de 7999 no se nombran.',
        '- **Interfaz con `comun.py`:** caja, placa, fuentes y colores. Cada cambio de la barra responde 6 cuadros después del corte (c51, c81, c156, c201) o con la placa (c268), con barrido con paneo y toque.',
        '- **Color:** Negra de 3453 corregida (desvío 6); la Negra de 4631 y 7824, en la tabla.',
        '- **Cierre con movimiento:** el plano 9 es video nativo (ola real) hasta el último cuadro.',
    ],
    estampado=[
        '',
        '- **Plano 6:** el ROCCÉ tono sobre tono de la Negra no entra en la máscara de letras claras. Se usa una caja medida a mano en c195 (rejilla de 50 px) y seguida por correlación de fase. La Negra se aleja, así que la caja seguida queda más alta que el estampado real: es conservadora.',
        '- **Plano 7 (7999):** no se mide. La Blanca va colgada de la mano, de costado, sin estampado legible.',
        '- **Plano 9 (4627):** la máscara marca también bordes de la remera a la sombra (rojo fuera de las letras en la hoja), lo que solo agranda la caja.',
    ],
    color=['', 'La «Blanca» se mide como la tela lisa más grande con L > 170 y saturación < 0,15; el «Oscuro», como la mediana de 10 < L < 55 en todo el cuadro (la Negra en los planos 2 y 6; en los demás, sombra, roca o mar). En el plano 5 el «Oscuro» de la tabla (B−R +17) es el mar y la sombra de las rocas: medida solo sobre la Negra (x 560–1060, y 950–1450, c172), da B−R entre −1 y +2 en todos los tramos de L. Es neutra.'],
    evidencia=[
        '- `control.json` y `ffprobe_*.json`.',
        '- `cortes/`: c0, cada corte (n−1, n, n+1), giro (c262, c268, c285), CTA (c330, c340, c419) y último, a tamaño real.',
        '- `hoja_cada_0.5s.jpg` y `vista_360px.jpg`.',
        '- Estampado: `estampado_c0-c419_c6.jpg` (máscara, caja y capa de texto), `estampado.json` y `estampado_resumen.json`.',
        '- `color_master.json`. La Negra antes y después, en `planos.json`.',
        '- Sonido: `forma_de_onda.png`, `audio_eventos_*.json` y `sonoridad_wav.json`.',
        '- Hojas de las fuentes cada 0,1–0,2 s: `hoja_fuente_*.jpg`.',
    ],
    verificado=[
        '- Los dos MP4 decodifican completos sin errores. Los cuadros contados coinciden con 420 y la duración de audio con la de video.',
        '- H.264 High 4.0, yuv420p, BT.709 de rango limitado, 1080×1920, 30 fps, AAC-LC 48 kHz estéreo, faststart. Sin marcas de ubicación.',
        '- `_SINMUSICA` lleva el mismo flujo de video que la completa: md5 idéntico.',
        '- Sonoridad y pico verdadero medidos con ebur128 sobre el MP4 final.',
        '- Estados de la barra y textos por cuadro leídos de la función que dibuja la capa. Choques medidos en los 420 cuadros.',
    ],
    visual=[
        '- Cuadros de corte, giro, CTA, c0 y último; hoja cada 0,5 s; vista a 360 px.',
        '- Textos exactos: Roccé, ROCCÉ, «Founders Privée» (en la prenda), 001–100 con raya, «PASA AL 002. AL 003…» con puntos suspensivos y voseo de «Comentá».',
        '- La Negra neutra (carbón), sin marrón.',
    ],
    pendiente=[
        '- **Escucha del audio:** no se escuchó. Falta confirmar en parlante de teléfono los toques del rodillo, los barridos de la barra, el hueco de 4,4–5,0, el drop de 9,5 y la ola de 4627.',
        '- **Reproducción continua a velocidad real:** se revisaron cuadros, no movimiento.',
        '- **Placas de 57 y 61 px:** decisión de Roma (desvío 2).',
    ],
    personas=[
        '- **7999** (plano 7, c240–c284): persona de pelo largo con campera de cuero, de costado, sin cara; lleva la Blanca en la mano (06, condición 7).',
        '- **7996** (plano 4): sombra con el brazo levantado.',
        '- **7824** (plano 6) y **4530** (plano 1): manos que sostienen la remera. 06 menciona antebrazos tatuados en 7824: en el tramo usado (6,0–7,5 s) se ven las manos; confirmar de quién son.',
    ],
)


def _caja_el(el, e=1.0):
    """caja visible (x0, y0, x1, y1) de un El al escalado e (alfa > 0,15)."""
    im, x, y = el.escalado(e)
    a = np.asarray(im)[..., 3] > 38
    ys, xs = np.nonzero(a)
    return [int(x + xs.min()), int(y + ys.min()), int(x + xs.max()), int(y + ys.max())]


def _luz(el_a, el_b):
    """luz mínima en px entre lo visible (alfa > 0,15) de dos El, por distancia euclídea entre sus máscaras."""
    from scipy import ndimage as nd
    ms = []
    for el in (el_a, el_b):
        im, x, y = el.escalado(1.0)
        m = np.zeros((M.H, M.W), bool)
        a = np.asarray(im)[..., 3] > 38
        x0, y0 = max(0, x), max(0, y)
        m[y0:y + a.shape[0], x0:x + a.shape[1]] = a[y0 - y:M.H - y, x0 - x:M.W - x]
        ms.append(m)
    return int(np.floor(nd.distance_transform_edt(~ms[0])[ms[1]].min())) - 1


def hoja_v02(pid='MC-04'):
    """03_pedro_hoja_master_v02.md: solo lo que cambia contra la v01 (dictamen 02 de Roma)."""
    d = pieza(pid, 'v02'); d1 = pieza(pid)
    T = d['T']
    rep = json.load(open(d['ev'] / 'control.json')); rep1 = json.load(open(d1['ev'] / 'control.json'))
    cv = rep['color_v02']
    cm1 = {c['plano']: c for c in rep1['color_master']}; cm2 = {c['plano']: c for c in rep['color_master']}
    textos = M4.armar_textos('v02')
    el = {t['el'].nombre: t for t in textos if t['el'].nombre in ('hook_caja', 'hook_dato', 'cta_caja', 'cta_dato')}
    b14, b340 = _caja_el(M4.el_barra(14)[0]), _caja_el(M4.el_barra(340)[0])
    hd, cd = _caja_el(el['hook_dato']['el']), _caja_el(el['cta_dato']['el'])
    hc, cc = _caja_el(el['hook_caja']['el']), _caja_el(el['cta_caja']['el'])
    ch = rep['choques_texto_estampado']['completa']
    L = ['# 03 · Pedro B · Hoja de máster MC-04 v02 · 25/11/2026', '',
         'REGLA PERMANENTE · CASA DE APUESTAS (textual): «Todo contenido de Roccé usa la mecánica de retención de una casa de '
         'apuestas. Es mecánica, no estética ni promoción de apuestas: una apuesta abierta desde el primer segundo, evidencia a '
         'favor y en contra a toda velocidad, y la resolución lo más tarde posible.»', '',
         'Responde a `02_roma_dictamen_master_v01.md`. **Solo lo que cambió** contra `01_pedro_hoja_master_v01.md`: las 2 '
         'correcciones. Montaje, tramos, barra, rodillo, textos aprobados, audio y desvíos 1 a 8 quedan como en la v01 (la v01 '
         'se conserva). Receta: `scripts/marca/mc04.py master_v02`; control: `scripts/marca/mc_control.py control MC-04 v02`. '
         'Evidencia: `evidencia_v02/` (al lado de esta hoja).', '',
         '**Estado:** máster v02 para revisión de Roma. No se escuchó el audio; la imagen se controló con cuadros decodificados '
         'del MP4 final, no con reproducción continua.', '',
         '## Archivos e ID inmutable (md5 de flujos)', '',
         '| Versión | Archivo | md5 flujo de video | md5 flujo de audio | Cuadros | Duración video / audio | Sonoridad | Pico verdadero | LRA |',
         '|---|---|---|---|---|---|---|---|---|']
    for k, fi in rep['archivos'].items():
        s_, v, a = fi['sonoridad'], fi['video'], fi['audio']
        L.append(f"| {k} | `{Path(fi['archivo']).name}` | `{fi['md5_video']}` | `{fi['md5_audio']}` | {v['cuadros_decodificados']} | "
                 f"{_f(v['duracion'], 3)} s / {_f(a['duracion'], 3)} s | {_f(s_['lufs_integrado'])} LUFS | {_f(s_['pico_dbtp'])} dBTP | {_f(s_['lra'])} LU |")
    igual_audio = all(rep['archivos'][k]['md5_audio'] == rep1['archivos'][k]['md5_audio'] for k in rep['archivos'])
    v0 = rep['archivos']['completa']['video']
    L += ['', f"Formato sin cambios: {v0['codec']} {v0['perfil']} {v0['nivel'] / 10:.1f}, {v0['pix_fmt']}, "
          f"{v0['ancho']}×{v0['alto']}, {v0['fps']} fps, AAC 48 kHz estéreo, faststart "
          f"{'sí' if all(f['faststart'] for f in rep['archivos'].values()) else 'NO'}, "
          f"{'sin marcas GPS' if not any(f['marcas_gps_o_ubicacion'] for f in rep['archivos'].values()) else 'CON GPS'}, "
          f"decodificación {'completa sin errores' if all(f['decodifica_completo'] for f in rep['archivos'].values()) else 'CON ERRORES'}. "
          + ('El audio sale del mismo WAV que la v01 y su md5 de flujo es **idéntico** al de la v01 en las dos versiones.' if igual_audio else
             'El audio sale del mismo WAV que la v01, pero su md5 de flujo cambió (recodificación AAC): misma sonoridad.'),
          'El ID inmutable es el md5 de los flujos: la carpeta compartida agrega una caja C2PA y cambia el sha256, no los flujos '
          '(`entrega_v02.json`).', '',
          '## Corrección 1 · Blanca fría', '',
          'Medido en los **dos másteres codificados** (v01 y v02) sobre **los mismos píxeles** (`evidencia_v02/color_v02.json`), '
          f"un cuadro de cada {5} del plano. Tela iluminada = peso > 0,8 y luma ≥ 85 % de la del blanco del cuadro; sombra = peso "
          '> 0,5 y luma 45–75 %; estampado = celeste de «Founders Privée» protegido, dentro de la caja del plano.', '',
          '| Plano | Toma | Tabla de Roma (v01) → v02, mismo método | Tela iluminada B−R v01 → v02 (mín–máx por cuadro) | G−R v01 → v02 | Sombra B−R v01 → v02 | Estampado B−R v01 → v02 | Tela con B−R < 0 | Cambio Cb/Cr lejos de la remera (p99 · medio) |',
          '|---|---|---|---|---|---|---|---|---|']
    for pid_, r in cv.items():
        il, so, es = r['iluminada'], r['sombra'], r['estampado']
        b1 = (cm1.get(pid_) or {}).get('blanco') or {}; b2 = (cm2.get(pid_) or {}).get('blanco') or {}
        tab = f"{_f(b1['b_menos_r'])} → {_f(b2['b_menos_r'])}" if b1 and b2 else 'sin medida'
        fmt = lambda x, c='b_menos_r': '—' if x is None else f"{_f(x['v01'][c])} → **{_f(x['v02'][c])}**" if c == 'b_menos_r' else f"{_f(x['v01'][c])} → {_f(x['v02'][c])}"
        mm = '' if il is None else f" ({_f(il['v02_b_menos_r_por_cuadro_min_max'][0])} a {_f(il['v02_b_menos_r_por_cuadro_min_max'][1])})"
        L.append(f"| {pid_} | {r['toma']} | {tab} | {fmt(il)}{mm} | {fmt(il, 'g_menos_r')} | {fmt(so)} | {fmt(es)} | "
                 f"{_f(r['tela_iluminada_con_b_menos_r_negativo_pct'], 2)} % | {_f(r['cambio_cb_cr_fuera_de_la_remera_p99_max'], 0)} · {_f(r['cambio_cb_cr_fuera_de_la_remera_medio'], 2)} niveles |")
    il2 = [r['iluminada']['v02'] for r in cv.values() if r['iluminada']]
    so2 = [r['sombra']['v02'] for r in cv.values() if r['sombra']]
    es2 = [(p_, r['estampado']) for p_, r in cv.items() if r['estampado']]
    mm_il = [x for r in cv.values() if r['iluminada'] for x in r['iluminada']['v02_b_menos_r_por_cuadro_min_max']]
    L += ['', f"- **Objetivo B−R ≤ +8 en la tela:** tela iluminada {_f(min(x['b_menos_r'] for x in il2))} a "
          f"{_f(max(x['b_menos_r'] for x in il2))} de media por plano (por cuadro, {_f(min(mm_il))} a {_f(max(mm_il))}); sombra "
          f"{_f(min(x['b_menos_r'] for x in so2))} a {_f(max(x['b_menos_r'] for x in so2))}. No se vuelve amarillenta: B−R queda "
          f"positivo y G−R entre {_f(min(x['g_menos_r'] for x in il2 + so2))} y {_f(max(x['g_menos_r'] for x in il2 + so2))} "
          '(la 8004 de MC-05 mide B−R +8). La sombra del plano 7 tiene pocos píxeles (la tela está casi toda a la misma luz); su '
          'mínimo y máximo por cuadro están en `color_v02.json`.',
          '- **Plano 7 (7999):** el +18,4 de la tabla de la v01 era el **mar**, no la remera: `color_master` toma el blanco más '
          'claro del cuadro y en 7999 la espuma es más clara que la tela, que está a la sombra de la persona (B−R +29 a +36 en '
          'la v01). Por eso esa columna casi no cambia en el plano 7 (el mar no se toca, como pide el dictamen) y la medida que '
          'vale es la de la tela.',
          '- **«Founders Privée» sigue celeste:** el estampado se protege (B−R > 35 y saturado; a la sombra, B−R > 50, solo si '
          'en el cuadro hay estampado iluminado) y su B−R queda en ' + ', '.join(f"+{_f(e['v02']['b_menos_r'])} (plano {p_})" for p_, e in es2) +
          ' (columna Estampado; en el plano 7 no se ve el estampado). Recortes a tamaño real: '
          '`evidencia_v02/color_antes_v01_despues_v02_tamano_real.jpg`.',
          '- **Nada fuera de la remera:** lejos de la remera (a más de 16 px de todo píxel corregido) Cb/Cr cambian solo por '
          'ruido de codificación (columna final); cielo, espuma, arena, piel y fondo quedan como en la v01. La luma no se toca (la textura de la tela es la misma).', '',
          '**Método** (criterio de Pedro C en 8004 para MC-05, con dos agregados porque estas tomas tienen tela a la sombra):', '',
          '1. Croma esperada de la Blanca por cuadro: punto de tela iluminada y, si es más azul que la proporción, punto de sombra; '
          'entre ambos se interpola por luma (`neutro_v02.json`).',
          '2. Peso = rampa de luma 70→100 × ventana de croma de Pedro C (5 → 11 alrededor de la croma esperada) × máscara de la '
          'remera (caja por plano, tela clara cercana a esa croma, componente mayor, agujeros rellenos) × (1 − resguardo del estampado).',
          '3. Objetivo B−R +7 / G−R +1,5 a la luma del blanco, proporcional en la sombra. Cada píxel se corre hacia el objetivo, '
          'nunca más allá ni hacia el azul; solo Cb/Cr, cuadro por cuadro, dentro de la misma pasada que la capa de textos (sin '
          'una generación de video extra).',
          '- Agregados respecto de 8004: (a) rampa de luma 70→100 en vez de 140→180, porque con la de 8004 la sombra de la tela '
          'quedaba celeste y el plano 7 no se corregía; (b) corrimiento medido por cuadro (sin media móvil), porque con un valor '
          'por plano el plano 4 quedaba en +12; (c) el estampado a la sombra se protege solo si en la caja de la remera hay '
          'estampado iluminado: en la primera pasada del máster v02, la tela de 7999 a la sombra (B−R +46 a +50) quedaba '
          'protegida como si fuera estampado y dejaba manchas celestes en c273–c279. Se corrigió y se volvió a generar el máster '
          'antes de entregarlo.', '',
          '## Corrección 2 · Datos de la tanda en caja negra', '',
          '| Texto (exacto) | Cuadros | Antes (v01) | v02 | Caja visible x0, y0, x1, y1 | Luz con lo de arriba | Luz con la barra |',
          '|---|---|---|---|---|---|---|',
          f"| «Los primeros 100 compradores de Roccé, / numerados 001–100.» | c{el['hook_dato']['c0']}–c{el['hook_dato']['c1']} (igual) | "
          f"blanco con halo, 46 px, y 470 | caja negra SemiBold 50 px, y 470 | {hd} | {_luz(el['hook_caja']['el'], el['hook_dato']['el'])} px con la caja del hook | {_luz(el['hook_dato']['el'], M4.el_barra(14)[0])} px |",
          f"| «Comentá cuál y por qué.» | c{el['cta_dato']['c0']}–c{el['cta_dato']['c1']} (igual) | blanco con halo, 52 px, y 440 | "
          f"caja negra SemiBold 50 px, y 440 | {cd} | {_luz(el['cta_caja']['el'], el['cta_dato']['el'])} px con «¿001 o 100?» | {_luz(el['cta_dato']['el'], M4.el_barra(340)[0])} px |", '',
          f"- `M.caja(..., tema='negra')` de la receta (envuelve `comun.caja`; SemiBold es el peso por defecto). Mismo cuadro de "
          'entrada que en la v01, sin pop (como los datos de la v01).',
          '- **Relleno compacto 28/14 e interlineado 1,0** (los de la caja del hook) en vez de 30/18 y 1,12: con el relleno por '
          'defecto el segundo renglón de c12 bajaba hasta tapar la pista y el disco de la barra, que tiene que quedar quieta. '
          'Con el compacto queda la luz de la tabla. «Comentá cuál y por qué.» usa el mismo para que los dos datos se vean iguales.',
          '- «Founders son los 100.» (c300) y el rótulo de la barra siguen con halo, como autoriza el dictamen.',
          f"- Choques de texto con el estampado: **{len(ch['cuadros_con_choque'])}** en {ch['cuadros_medidos']} cuadros medidos "
          f"(máximo {ch['px_max']} px), medidos al componer cuadro por cuadro.",
          '- Entrada a tamaño real: `evidencia_v02/caja_negra_c11-c14.jpg` y `caja_negra_c329-c332.jpg`.', '',
          '## Vista a 360 px', '',
          '`evidencia_v02/vista_360px.jpg`: un cuadro por plano, **c14** (el dato de c12 ya quieto, después de c12), giro (c262, '
          'c268, c285), CTA (c330, c340, c419) y el último cuadro.', '',
          '## Desvíos nuevos', '',
          '- **D9 · relleno compacto de las cajas negras** (28/14 e interlineado 1,0 en lugar del de `comun.caja`), por la barra. '
          'Texto, tamaño (50 px), tema, y y cuadros como pide el dictamen.',
          '- **D10 · neutralización extendida a la sombra de la tela** (rampa de luma 70→100, modelo con punto de sombra y '
          'resguardo del estampado a la sombra condicionado), por el plano 7, donde la remera está a la sombra. Si Roma prefiere '
          'el criterio de 8004 tal cual (solo tela iluminada), la tela del plano 7 vuelve a +29 a +36.', '',
          '## No verificado', '',
          '- **No se escuchó el audio** (no cambió: mismo WAV que la v01; controlado con medidores).',
          '- Sin reproducción continua: la imagen se revisó por cuadros decodificados del MP4 final y por la vista a 360 px.',
          '- Legibilidad en un teléfono real (solo vista a 360 px).',
          '- Visto a tamaño real y no corregido (para decidir): (a) plano 8, c285–c329: la sombra que el relieve de las letras '
          'proyecta sobre la tela conserva un tinte celeste de 10 a 20 px junto a «Founders Privée» (es el resguardo del '
          'estampado a la sombra; a 360 px no se distingue); (b) plano 4, c145–c149: la sombra de quien filma sobre la remera '
          'queda azulada, pareja y sin bordes, porque ahí la tela a la sombra pasa de B−R +50 y se protege junto con el '
          'estampado. Para sacarlos habría que separar estampado y tela a la sombra por forma, no por color.',
          '- Las personas y permisos pendientes de la v01 siguen igual (persona de 7999, sombra de 7996, manos de 7824 y 4530).', '',
          '## Evidencia (`evidencia_v02/`)', '',
          '- `control.json` (ffprobe, md5, sonoridad, niveles, choques, color), `ffprobe_*.json`, `forma_de_onda.png`, `cortes/`, '
          '`hoja_cada_0.5s.jpg`.',
          '- `color_v02.json`, `color_master.json`, `color_antes_v01_despues_v02_tamano_real.jpg`, `neutro_v02.json` (modelo por '
          'cuadro), `neutro_v02_por_cuadro.json` (B−R / G−R antes y después en cada cuadro, al componer).',
          '- `vista_360px.jpg`, `caja_negra_c11-c14.jpg`, `caja_negra_c329-c332.jpg`.']
    (T / d['hoja']).write_text('\n'.join(L) + '\n')
    print(T / d['hoja'])


def hoja_v02_mc03():
    """03_pedro_hoja_master_v02.md de MC-03: solo lo que cambia contra la v01 (dictamen 02 de Roma)."""
    pid = 'MC-03'
    d = pieza(pid, 'v02'); d1 = pieza(pid)
    T = d['T']
    rep = json.load(open(d['ev'] / 'control.json')); rep1 = json.load(open(d1['ev'] / 'control.json'))
    rep4 = json.load(open(M4.T / 'evidencia_v02' / 'control.json'))
    cv = rep['color_v02']
    cm1 = {c['plano']: c for c in rep1['color_master']}; cm2 = {c['plano']: c for c in rep['color_master']}
    textos = {t['el'].nombre: t for t in M.armar_textos('A', 'v02')}
    hd = _caja_el(textos['hook_A_dato']['el'])
    me = rep['margen_texto_estampado']['A']['por_elemento']['hook_A_dato']
    ch = rep['choques_texto_estampado']
    L = ['# 03 · Pedro B · Hoja de máster MC-03 v02 · 25/11/2026', '',
         'REGLA PERMANENTE · CASA DE APUESTAS (textual): «Todo contenido de Roccé usa la mecánica de retención de una casa de '
         'apuestas. Es mecánica, no estética ni promoción de apuestas: una apuesta abierta desde el primer segundo, evidencia a '
         'favor y en contra a toda velocidad, y la resolución lo más tarde posible.»', '',
         'Responde a `02_roma_dictamen_master_v01.md`. **Solo lo que cambió** contra `01_pedro_hoja_master_v01.md`: las 2 '
         'correcciones. Montaje, tramos, marcador, hook B, audio, condiciones 1 a 3 y los desvíos aceptados (entrada de c310, '
         '3375 en −3) quedan como en la v01. La v01 se conserva y no se volvió a generar después de su entrega (05:24). '
         'Receta: `scripts/marca/mc03.py master_v02` (usa la neutralización de `mc04.py`, la misma de MC-04 v02); control: '
         '`scripts/marca/mc_control.py control MC-03 v02`. Evidencia: `evidencia_v02/` (al lado de esta hoja).', '',
         '**Estado:** máster v02 para revisión de Roma. No se escuchó el audio; la imagen se controló con cuadros decodificados '
         'del MP4 final, no con reproducción continua.', '',
         '## Archivos e ID inmutable (md5 de flujos)', '',
         '| Versión | Archivo | md5 flujo de video | md5 flujo de audio | Cuadros | Duración video / audio | Sonoridad | Pico verdadero | LRA |',
         '|---|---|---|---|---|---|---|---|---|']
    for k, fi in rep['archivos'].items():
        s_, v, a = fi['sonoridad'], fi['video'], fi['audio']
        L.append(f"| {k} | `{Path(fi['archivo']).name}` | `{fi['md5_video']}` | `{fi['md5_audio']}` | {v['cuadros_decodificados']} | "
                 f"{_f(v['duracion'], 3)} s / {_f(a['duracion'], 3)} s | {_f(s_['lufs_integrado'])} LUFS | {_f(s_['pico_dbtp'])} dBTP | {_f(s_['lra'])} LU |")
    igual_audio = all(rep['archivos'][k]['md5_audio'] == rep1['archivos'][k]['md5_audio'] for k in rep['archivos'])
    v0 = rep['archivos']['A']['video']
    L += ['', f"Formato sin cambios: {v0['codec']} {v0['perfil']} {v0['nivel'] / 10:.1f}, {v0['pix_fmt']}, {v0['ancho']}×{v0['alto']}, "
          f"{v0['fps']} fps, AAC 48 kHz estéreo, faststart {'sí' if all(f['faststart'] for f in rep['archivos'].values()) else 'NO'}, "
          f"{'sin marcas GPS' if not any(f['marcas_gps_o_ubicacion'] for f in rep['archivos'].values()) else 'CON GPS'}, "
          f"decodificación {'completa sin errores' if all(f['decodifica_completo'] for f in rep['archivos'].values()) else 'CON ERRORES'}. "
          + ('El audio sale de los mismos WAV que la v01 y su md5 de flujo es **idéntico** al de la v01 en las tres versiones.' if igual_audio else
             'El audio sale de los mismos WAV que la v01, pero su md5 de flujo cambió (recodificación AAC): misma sonoridad.'),
          'A y SINMUSICA comparten el flujo de video. El ID inmutable es el md5 de los flujos: la carpeta compartida agrega una '
          'caja C2PA y cambia el sha256, no los flujos (`entrega_v02.json`).', '',
          '## Corrección 1 · Blanca fría (neutros claros de la tela, L > 170; plano 7, desvío D15)', '',
          'Medido en los **dos másteres A codificados** (v01 y v02) sobre **los mismos píxeles** (`evidencia_v02/color_v02.json`), '
          'un cuadro de cada 5 del plano, sin los píxeles del dato del hook A (en c0–c59 la capa de textos cambió). Tela clara = '
          'peso > 0,8 (L ≥ 172 y croma de la Blanca, dentro de la máscara de la remera; en el plano 7, la rampa de MC-04 v02); '
          'sombra = L 40–150 a ≤ 40 px de la tela corregida (la sombra proyectada y los pliegues); estampado = celeste de '
          '«Founders Privée» protegido (en 7999, el estampado oscuro con la estrella).', '',
          '| Plano | Toma | Tabla de Roma (v01) → v02, mismo método | Tela clara B−R v01 → v02 (mín–máx por cuadro) | G−R v01 → v02 | Sombra B−R v01 → v02 | Estampado B−R v01 → v02 | Cambio Cb/Cr con L < 150 (p99 · medio) | Cambio Cb/Cr en la arena (p99 · medio) |',
          '|---|---|---|---|---|---|---|---|---|']
    fmt = lambda x, c='b_menos_r', neg=True: '—' if x is None else (f"{_f(x['v01'][c])} → **{_f(x['v02'][c])}**" if neg else f"{_f(x['v01'][c])} → {_f(x['v02'][c])}")
    for pid_, r in cv.items():
        il, so, es = r['iluminada'], r['sombra'], r['estampado']
        b1 = (cm1.get(pid_) or {}).get('blanco') or {}; b2 = (cm2.get(pid_) or {}).get('blanco') or {}
        tab = f"{_f(b1['b_menos_r'])} → {_f(b2['b_menos_r'])}" if b1 and b2 else 'sin medida'
        mm = '' if il is None else f" ({_f(il['v02_b_menos_r_por_cuadro_min_max'][0])} a {_f(il['v02_b_menos_r_por_cuadro_min_max'][1])})"
        cb, ca = r.get('cambio_cb_cr_L_menor_150_p99_medio'), r.get('cambio_cb_cr_arena_p99_medio')
        L.append(f"| {pid_} | {r['toma']} | {tab} | {fmt(il)}{mm} | {fmt(il, 'g_menos_r', False)} | {fmt(so, neg=False)} | {fmt(es)} | "
                 f"{'—' if not cb else _f(cb[0], 0) + ' · ' + _f(cb[1], 2)} | {'—' if not ca else _f(ca[0], 0) + ' · ' + _f(ca[1], 2)} |")
    il2 = [r['iluminada']['v02'] for r in cv.values() if r['iluminada']]
    mm_il = [x for r in cv.values() if r['iluminada'] for x in r['iluminada']['v02_b_menos_r_por_cuadro_min_max']]
    t7_4 = rep4['color_v02']['7']['iluminada']['v02']['b_menos_r']
    t7_3 = [cv[p_]['iluminada']['v02']['b_menos_r'] for p_ in ('01', '04', '10') if cv[p_]['iluminada']]
    es2 = [(p_, r['estampado']) for p_, r in cv.items() if r['estampado'] and r['toma'] != 'IMG_7999']
    es7999 = [(p_, r['estampado']) for p_, r in cv.items() if r['estampado'] and r['toma'] == 'IMG_7999']
    L += ['', f"- **Tela clara a B−R ≤ +8:** {_f(min(x['b_menos_r'] for x in il2))} a {_f(max(x['b_menos_r'] for x in il2))} de media "
          f"por plano (por cuadro, {_f(min(mm_il))} a {_f(max(mm_il))}), G−R {_f(min(x['g_menos_r'] for x in il2))} a "
          f"{_f(max(x['g_menos_r'] for x in il2))}: no queda amarillenta.",
          f"- **7999 coincide con MC-04 v02:** la tela de 7999 queda en {', '.join('+' + _f(x) for x in t7_3)} (planos 1, 4 y 10) y en "
          f"+{_f(t7_4)} en MC-04 v02 (plano 7), con el mismo objetivo (+7 / +1,5) y el mismo modelo por cuadro. Son tramos "
          'distintos de la toma (MC-04: 0–1,47 s, la Blanca en la mano; MC-03: 2,70–5,33 s, la Blanca en la arena con la sombra).',
          '- **La sombra proyectada no se toca:** en los planos de 7999 (1, 4, 10) y 8002 (3, 6) no hay punto de sombra y el '
          'peso es 0 hasta L 160 y completo desde L 172 (D16). La columna Sombra (L < 150) muestra el '
          'mismo B−R en v01 y v02, y con L < 150 Cb/Cr solo cambian por ruido de codificación. Se sigue viendo como sombra (la '
          'luma nunca se toca).',
          '- **Plano 7 (clip_f2a34e51, c190–c219, 6,33–7,30 s), desvío D15:** ahí la tela entera mide B−R +46 a +49 (la tabla de '
          'la v01 daba +23,4 porque `color_master` toma el blanco más claro del cuadro). Con L > 170 solo, las luces quedaban '
          'neutras y los pliegues celestes: la remera se veía de dos colores (`evidencia_v02/plano07_L170_descartado.jpg`, c205). '
          'Este plano no tiene sombra proyectada (la pista es de 7999), así que usa la rampa de MC-04 v02 (luma 70 → 100) y se '
          'corrigen también los pliegues: por eso sus columnas Sombra y L < 150 sí cambian. Si Roma prefiere L > 170 también '
          'ahí, es cambiar una línea de la receta (`rampas` en `mc03.ctx_v02`) y volver a generar.',
          '- **La arena no cambia** (columna final: ruido de codificación).',
          '- **«Founders Privée» sigue celeste** (8002 y clip_f2a34e51): ' + ', '.join(f"plano {p_} B−R {_f(e['v01']['b_menos_r'])} → {_f(e['v02']['b_menos_r'])}" for p_, e in es2) +
          '. En 7999 la zona protegida (B−R más de +25 sobre la tela esperada a esa luma: la estrella celeste de «so f★cking '
          'close.» y el borde azulado de la sombra; no separé cuánto es cada uno) queda igual: ' +
          ', '.join(f"plano {p_} {_f(e['v01']['b_menos_r'])} → {_f(e['v02']['b_menos_r'])}" for p_, e in es7999) +
          '. Recortes a tamaño real: `evidencia_v02/color_antes_v01_despues_v02_tamano_real.jpg`.', '',
          '**Método:** el de MC-04 v02 (`mc04.medir_neutro` y `mc04.pre_neutro`, criterio de Pedro C en 8004): croma esperada '
          'de la Blanca por cuadro, ventana de croma 5 → 11, máscara de la remera por plano, resguardo del estampado, objetivo '
          'B−R +7 / G−R +1,5, solo Cb/Cr, cuadro por cuadro, en la misma pasada que la capa de textos. Cambios que pide este '
          'dictamen: rampa de luminancia **L 160 → 172** (peso 0 hasta L 160, completo desde L 172; plano 7, ver D15) y **sin punto de '
          'sombra**. Además: (a) como la sombra parte la remera en varios pedazos claros, la máscara toma todos los pedazos '
          'grandes (≥ 10 % del mayor); (b) el estampado se reconoce por su B−R relativo a la tela esperada a esa luma (> +25) '
          'y se excluye también de la medición: en clip_f2a34e51 la tela misma está en +46 y la regla absoluta de MC-04 '
          '(B−R > 35) marcaba media remera como estampado y dejaba manchas celestes.', '',
          '## Corrección 2 · Dato del hook A en caja negra', '',
          f"- «La sesión de fotos de Roccé, / punto por punto.»: caja negra SemiBold 50 px, y 620 (la misma), c0–c59 (igual), "
          f"caja visible {hd}. Relleno compacto 28/14 e interlineado 1,0, como los datos en caja negra de MC-04 v02.",
          f"- Distancia al estampado en c0–c59: mínimo **{me['margen_px']} px** (c{me['cuadro']}, estampado en {me['caja_estampado']}); "
          f"pedido ≥ 40 px. Luz con la caja del hook: {_luz(textos['hook_caja']['el'], textos['hook_A_dato']['el'])} px.",
          f"- Choques de texto con el estampado: A {len(ch['A']['cuadros_con_choque'])} y B {len(ch['B']['cuadros_con_choque'])} en "
          f"{ch['A']['cuadros_medidos']} cuadros medidos.",
          '- El hook B queda como estaba (burbuja con emoji). Recorte a tamaño real: `evidencia_v02/caja_negra_hookA_c0-c59.jpg`.', '',
          '## Vista a 360 px', '',
          '- A: `evidencia_v02/vista_360px.jpg` (un cuadro por plano, giro, CTA y el último).',
          '- B: `evidencia_v02/vista_360px_hookB.jpg` (c0, c2, c15, c45 y c59).', '',
          '## Desvíos nuevos', '',
          '- **D14 · relleno compacto** de la caja negra del hook A (28/14 e interlineado 1,0 en lugar del de `comun.caja`), el '
          'mismo de MC-04 v02, para que los datos en caja negra de la tanda se vean iguales.',
          '- **D15 · plano 7 con la rampa de MC-04 v02** (luma 70 → 100) en lugar de L > 170, por lo explicado arriba. Para decidir.',
          '- **D16 · franja de transición L 160–172** (planos 1, 3, 4, 6 y 10): con el corte justo en L 170 el borde de la sombra '
          'quedaría como un escalón de color, y con la franja arriba de 170 (170 → 185, primera prueba) la medición de Roma (mayor '
          'componente con L > 170) daba +8,1 a +8,8. Con 160 → 172 lo que pasa de L 170 queda corregido por completo y entre L '
          '150 y 170 el cambio medio es de 0,7 a 1,3 niveles. Con L < 150 (la sombra proyectada) el cambio es 0.', '',
          '## No verificado', '',
          '- **No se escuchó el audio** (no cambió: mismos WAV que la v01; controlado con medidores).',
          '- Sin reproducción continua: la imagen se revisó por cuadros decodificados del MP4 final y por las vistas a 360 px.',
          '- Legibilidad en un teléfono real (solo vista a 360 px).',
          '- Las personas y permisos pendientes de la v01 siguen igual (7884, sombra de 7999, permiso del comentario del hook B).', '',
          '## Evidencia (`evidencia_v02/`)', '',
          '- `control.json`, `ffprobe_*.json`, `forma_de_onda.png`, `cortes/`, `hoja_cada_0.5s.jpg`.',
          '- `color_v02.json`, `color_master.json`, `color_antes_v01_despues_v02_tamano_real.jpg`, `neutro_v02.json`, '
          '`neutro_v02_por_cuadro.json` (A).',
          '- `vista_360px.jpg`, `vista_360px_hookB.jpg`, `caja_negra_hookA_c0-c59.jpg`, `plano07_L170_descartado.jpg`.']
    (T / d['hoja']).write_text('\n'.join(L) + '\n')
    print(T / d['hoja'])


if __name__ == '__main__':
    accion, pid = sys.argv[1], sys.argv[2]
    ver = sys.argv[3] if len(sys.argv) > 3 else 'v01'
    if accion == 'hoja':
        (hoja_v02_mc03() if pid == 'MC-03' else hoja_v02(pid)) if ver == 'v02' else hoja(pid)
    else:
        {'control': control, 'entregar': entregar}[accion](pid, ver)
