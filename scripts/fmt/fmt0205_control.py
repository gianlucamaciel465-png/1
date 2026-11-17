#!/usr/bin/env python3
"""FMT-02 y FMT-05 · control del máster y copia a la carpeta de la pieza (Pedro, 17/11/2026).

control_pieza(): decodificación completa, ffprobe, metadatos, sonoridad EBU R128 (integrada, pico verdadero), niveles
por tramo, sonoridad momentánea, huellas md5 (archivo y streams), hoja de contacto cada 0,5 s, cuadros c0 / último /
antes-en-después de cada corte a tamaño real, cuadros negros / congelados / duplicados, textos del .ass contra la
receta, color de la tela blanca y negra contra PRODUCTO/, y los puntos comprobables de cada pieza (función `puntos`).
copiar_pieza(): copia MP4 y evidencia al montaje de red, espera y verifica tamaño y md5 de streams.
"""
import json, shutil, subprocess, time
from pathlib import Path
import numpy as np

import fmt0205_util as U
import video as V

PRODUCTO = Path('/home/user/1/PRODUCTO')
REF_TELA = {  # zonas de tela lisa en las fotos de producto (sRGB, píxeles de la foto orientada)
    'blanca': [('blanca_frente_detalle_estampado.jpg', (150, 80, 1350, 650)),
               ('blanca_espalda_estudio.jpg', (480, 1150, 920, 1600))],
    'negra': [('negra_frente_detalle_estampado.jpg', (380, 1400, 1300, 1950)),
              ('negra_espalda_estudio.jpg', (240, 1080, 900, 1450))],
}


def _tela(rgb, tipo):
    """mediana RGB de los píxeles de tela lisa (sin estampado) dentro de un recorte."""
    a = rgb.reshape(-1, 3).astype(float)
    R, G, B = a[:, 0], a[:, 1], a[:, 2]
    Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
    if tipo == 'blanca':
        m = (Y > 150) & (np.abs(B - R) < 32) & (np.abs(G - R) < 22)
    else:
        m = (Y < 70) & (np.abs(B - R) < 25) & (np.abs(G - R) < 20)
    if m.sum() < 200:
        return None
    med = np.median(a[m], 0)
    y = 0.2126 * med[0] + 0.7152 * med[1] + 0.0722 * med[2]
    return {'rgb_mediana': [round(float(x), 1) for x in med], 'luma': round(float(y), 1),
            'B-R': round(float(med[2] - med[0]), 1), 'G-R': round(float(med[1] - med[0]), 1), 'pixeles': int(m.sum())}


def color_telas(mp4, telas, tmpdir):
    from PIL import Image
    res = {'producto': {}, 'master': {}}
    for tipo, lst in REF_TELA.items():
        for f, (x0, y0, x1, y1) in lst:
            png = Path(tmpdir) / (Path(f).stem + '_srgb.png')
            if not png.exists():
                V.foto_srgb(PRODUCTO / f, png)
            im = np.asarray(Image.open(png).convert('RGB'))[y0:y1, x0:x1]
            res['producto'][f'{tipo} · {f}'] = _tela(im, tipo)
    for tipo, lst in telas.items():
        for c, (x0, y0, x1, y1) in lst:
            im = U.leer_mp4(mp4, c0=c, c1=c)[0][y0:y1, x0:x1]
            res['master'][f'{tipo} · c{c} · ({x0},{y0},{x1},{y1})'] = _tela(im, tipo)
    return res


def cuadros_por_cuadro(mp4):
    """luma media por cuadro y diferencia media absoluta con el anterior (270×480): negros, congelados, saltos."""
    fr = U.leer_mp4(mp4, 270, 480).astype(np.float32)
    Y = fr.mean(3)
    luma = Y.mean((1, 2))
    dif = np.r_[np.nan, np.abs(np.diff(Y, axis=0)).mean((1, 2))]
    return [{'c': i, 'luma': round(float(l), 1), 'dif_prev': None if np.isnan(d) else round(float(d), 2)}
            for i, (l, d) in enumerate(zip(luma, dif))]


def gps_bruto(mp4):
    """busca en los bytes del contenedor (fuera de mdat no hay forma de que aparezcan) cadenas ISO 6709 o 'location'."""
    import re
    b = Path(mp4).read_bytes()
    pos = b.find(b'moov')
    zona = b[:200000] + b[pos - 4: pos + 400000] if pos > 0 else b[:200000]
    hall = re.findall(rb'[+-]\d{1,3}\.\d{3,}[+-]\d{1,3}\.\d{3,}', zona)
    return {'iso6709': [h.decode() for h in hall][:5], 'palabra_location': b'location' in zona.lower()}


def resumen_ffprobe(pj):
    v = [s for s in pj['streams'] if s['codec_type'] == 'video'][0]
    a = [s for s in pj['streams'] if s['codec_type'] == 'audio'][0]
    return {
        'video': {k: v.get(k) for k in ('codec_name', 'profile', 'level', 'pix_fmt', 'width', 'height', 'r_frame_rate',
                                        'avg_frame_rate', 'nb_read_frames', 'duration', 'color_space', 'color_primaries',
                                        'color_transfer', 'color_range', 'sample_aspect_ratio')},
        'audio': {k: a.get(k) for k in ('codec_name', 'profile', 'sample_rate', 'channels', 'channel_layout', 'duration',
                                        'nb_read_frames')},
        'formato': {k: pj['format'].get(k) for k in ('format_name', 'duration', 'size', 'bit_rate')},
        'tags_formato': pj['format'].get('tags', {}),
        'tags_streams': [s.get('tags', {}) for s in pj['streams']],
        'cantidad_streams': len(pj['streams']),
    }


def faststart(mp4):
    """True si el átomo moov está antes que mdat."""
    with open(mp4, 'rb') as f:
        pos = 0
        orden = []
        while True:
            h = f.read(8)
            if len(h) < 8:
                break
            n = int.from_bytes(h[:4], 'big'); t = h[4:8].decode('latin1')
            if n == 1:
                n = int.from_bytes(f.read(8), 'big'); f.seek(pos + n)
            else:
                f.seek(pos + n)
            orden.append(t); pos += n
            if n == 0:
                break
    return {'atomos': orden, 'faststart': orden.index('moov') < orden.index('mdat') if 'moov' in orden and 'mdat' in orden else None}


def control_pieza(salidas, evi, unido, textos, cortes, dur, pieza, puntos=None, telas=None, ass_path=None):
    evi = Path(evi); evi.mkdir(parents=True, exist_ok=True)
    tmp = evi.parent / 'tmp_control'; tmp.mkdir(exist_ok=True)
    rep = {'pieza': pieza, 'fecha': time.strftime('%Y-%m-%d %H:%M'), 'archivos': {}}
    for mp4 in salidas:
        mp4 = Path(mp4); nom = mp4.stem
        r = {}
        r['ruta'] = str(mp4)
        r['bytes'] = mp4.stat().st_size
        r['md5_archivo'] = U.md5_archivo(mp4)
        r['md5_streams'] = U.md5_streams(mp4)
        err = U.decodifica(mp4)
        r['decodifica_completo'] = 'OK (sin errores)' if not err else err[-1500:]
        pj = U.ffprobe_json(mp4)
        (evi / f'ffprobe_{nom}.json').write_text(json.dumps(pj, indent=1))
        r['ffprobe'] = resumen_ffprobe(pj)
        vd = float(r['ffprobe']['video']['duration']); ad = float(r['ffprobe']['audio']['duration'])
        r['duracion_video_s'] = vd; r['duracion_audio_s'] = ad; r['dif_audio_video_ms'] = round((ad - vd) * 1000, 1)
        r['faststart'] = faststart(mp4)
        import re
        tags = json.dumps(r['ffprobe']['tags_formato'] | {'s': r['ffprobe']['tags_streams']}).lower()
        r['tags'] = tags
        r['gps_o_ubicacion'] = bool(any(k in tags for k in ('location', 'gps', 'iso6709')) or
                                    re.search(r'[+-]\d{1,3}\.\d+[+-]\d{1,3}\.\d+', tags))
        r['exiftool_o_strings_gps'] = gps_bruto(mp4)
        r['ebur128'] = U.ebur128_archivo(mp4)
        niv = U.niveles_tramos(mp4, paso=0.5)
        mom = U.sonoridad_momentanea(mp4)
        (evi / f'audio_{nom}.json').write_text(json.dumps({'ebur128': r['ebur128'], 'niveles_0.5s': niv,
                                                           'sonoridad_momentanea_0.2s': mom}, indent=1))
        rep['archivos'][nom] = r
    m0 = Path(salidas[0])
    # imagen (la misma en las dos versiones si el md5 de video coincide)
    vids = {n: r['md5_streams']['video'] for n, r in rep['archivos'].items()}
    rep['video_identico_en_las_dos'] = len(set(vids.values())) == 1
    U.hoja_mp4(m0, evi / 'hoja_contacto_0.5s.jpg', cada=0.5, ancho=270, cols=7)
    nf = int(rep['archivos'][m0.stem]['ffprobe']['video']['nb_read_frames'])
    sel = sorted({0, nf - 1} | {c + d for c in cortes for d in (-1, 0, 1)})
    expr = '+'.join(f'eq(n\\,{c})' for c in sel)
    subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-i', str(m0), '-vf', f"select='{expr}'",
                    '-fps_mode', 'vfr', '-q:v', '2', str(tmp / 'k_%03d.jpg')], check=True)
    cdir = evi / 'cuadros'; cdir.mkdir(exist_ok=True)
    for i, c in enumerate(sel):
        shutil.move(tmp / f'k_{i + 1:03d}.jpg', cdir / f'c{c:03d}_{c / 30:.3f}s.jpg')
    # tira de cortes reducida (antes / en / después)
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(U.FONT, 22)
    filas = [[0]] + [[c - 1, c, c + 1] for c in cortes] + [[nf - 1]]
    W_, H_ = 270, 480
    lien = Image.new('RGB', (W_ * 3 + 8, (H_ + 4) * len(filas)), (25, 25, 25))
    for fi, fila in enumerate(filas):
        for ci, c in enumerate(fila):
            im = Image.open(cdir / f'c{c:03d}_{c / 30:.3f}s.jpg').resize((W_, H_))
            d = ImageDraw.Draw(im); d.rectangle([0, 0, 150, 28], fill=(0, 0, 0)); d.text((4, 2), f'c{c} {c / 30:.3f}s', fill='yellow', font=fnt)
            lien.paste(im, (ci * (W_ + 4), fi * (H_ + 4)))
    lien.save(evi / 'cortes_antes_en_despues.jpg', quality=90)
    # negros / congelados / duplicados
    pc = cuadros_por_cuadro(m0)
    (evi / 'cuadros_luma_diferencia.json').write_text(json.dumps(pc))
    dif = [x['dif_prev'] for x in pc[1:]]
    rep['imagen'] = {'cuadros': nf, 'luma_min': min(x['luma'] for x in pc), 'luma_max': max(x['luma'] for x in pc),
                     'cuadros_negros(luma<16)': [x['c'] for x in pc if x['luma'] < 16],
                     'cuadros_identicos_al_anterior(dif<0,05)': [x['c'] for x in pc[1:] if x['dif_prev'] < 0.05],
                     'dif_max_y_cuadro': [max(dif), int(np.argmax(dif)) + 1],
                     'dif_en_cortes': {c: pc[c]['dif_prev'] for c in cortes}}
    # textos: el .ass quemado contra la receta
    if ass_path:
        ev = [l for l in Path(ass_path).read_text(encoding='utf-8').splitlines() if l.startswith('Dialogue:')]
        txt_ass = [l.split('}', 1)[1] for l in ev]
        rep['textos'] = [{'receta': k['txt'], 'ass': t, 'igual': k['txt'] == t, 'desde_c': round(k['t0'] * 30),
                          'hasta_c': round(k['t1'] * 30) - 1, 'estilo': k['estilo'], 'y': k['y']}
                         for k, t in zip(textos, txt_ass)]
    if telas:
        rep['color_telas'] = color_telas(m0, telas, tmp)
    if puntos:
        rep['puntos_comprobables'] = puntos(m0, unido, evi)
    (evi / f"control_{evi.name.replace('evidencia_', '')}.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    shutil.rmtree(tmp, ignore_errors=True)
    return rep


def _render_ass(ass_path, cuadros, w=1080, h=1920):
    """quema el .ass sobre gris 128 y devuelve {c: RGB int} de los cuadros pedidos (misma cadena que mascara_textos)."""
    n = max(cuadros) + 1
    vf = (f"subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter,format=rgb24,"
          f"select='" + '+'.join(f'eq(n\\,{c})' for c in cuadros) + "'")
    r = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=c=0x808080:s={w}x{h}:r={U.FPS}:d={n / U.FPS + 0.1}',
                        '-vf', vf, '-fps_mode', 'vfr', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(r, np.uint8).reshape(-1, h, w, 3).astype(int)
    return {c: f for c, f in zip(sorted(cuadros), a)}


def entradas_textos(master, textos, evi, n_cuadros, margen=3, umbral=0.6):
    """Cuadro real de entrada y de salida de cada texto EN EL MÁSTER, contra el guion (c = round(t·30)).
    Pedido por Roma (17/11): el overlay PNG de video.master aparece un cuadro antes; los .ass hay que comprobarlos.
    Cada texto se quema SOLO sobre gris (su forma exacta, con el pop del cuadro de entrada) y, en c_entrada±margen y
    c_salida±margen, se correlaciona (Pearson, luma) esa forma con el máster dentro de su huella. Las letras de otro
    texto en el mismo lugar, o la imagen sin texto, no correlacionan. Presente = correlación > umbral."""
    tmp = Path(evi) / '_tmp_textos'; tmp.mkdir(exist_ok=True)
    res = []
    for i, t in enumerate(textos):
        c_in = int(round(t['t0'] * U.FPS)); c_out = min(n_cuadros, int(round(t['t1'] * U.FPS))) - 1
        a = V.ass([t], tmp / f't{i}.ass')
        cs = sorted({c for c in list(range(c_in - margen, c_in + margen + 1)) + list(range(c_out - margen, c_out + margen + 1))
                     if 0 <= c < n_cuadros})
        forma = {c: min(max(c, c_in), c_out) for c in cs}           # fuera del horario se usa la forma del borde
        rend = _render_ass(a, sorted(set(forma.values())))
        corr = {}
        for c in cs:
            R = rend[forma[c]]; H = np.abs(R - 128).max(2) > 6
            m = U.leer_mp4(master, c0=c, c1=c)[0].astype(float).mean(2)
            corr[c] = round(float(np.corrcoef(R.mean(2)[H], m[H])[0, 1]), 3)
        pres = [c for c in cs if corr[c] > umbral]
        ent = min((c for c in pres if abs(c - c_in) <= margen), default=None)
        sal = max((c for c in pres if abs(c - c_out) <= margen), default=None)
        res.append({'texto': t['txt'], 't0': t['t0'], 't1': t['t1'], 'guion_c_entrada': c_in, 'guion_c_salida': c_out,
                    'master_c_entrada': ent, 'master_c_salida': sal,
                    'coincide': ent == c_in and sal == c_out, 'correlacion_por_cuadro': corr})
        print(t['txt'].replace('\\N', ' / '), '| guion', c_in, c_out, '| máster', ent, sal, '|', corr)
    shutil.rmtree(tmp)
    (Path(evi) / 'textos_entrada_salida.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return res


def copiar_pieza(salidas, evi, dest_evi, extra=()):
    """Copia los MP4 a la carpeta de la pieza y la evidencia a dest_evi; espera y verifica tamaño y md5 de streams."""
    dest_evi = Path(dest_evi); dest = dest_evi.parent
    dest_evi.mkdir(parents=True, exist_ok=True)
    rep = {}
    for mp4 in salidas:
        mp4 = Path(mp4); d = dest / mp4.name
        if d.exists():
            # el montaje agrega una caja uuid (C2PA) de ~5,9 kB: se compara por streams, no por bytes
            if U.md5_streams(d) != U.md5_streams(mp4):
                raise SystemExit(f'{d} ya existe con otro contenido: no se sobrescribe')
            continue
        shutil.copy2(mp4, d)
    for f in Path(evi).rglob('*'):
        if f.is_file():
            t = dest_evi / f.relative_to(evi); t.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(f, t)
    for f in extra:
        shutil.copy2(f, dest / Path(f).name)
    time.sleep(8)
    for mp4 in salidas:
        mp4 = Path(mp4); d = dest / mp4.name
        rep[mp4.name] = {'bytes_local': mp4.stat().st_size, 'bytes_red': d.stat().st_size,
                         'md5_streams_local': U.md5_streams(mp4), 'md5_streams_red': U.md5_streams(d),
                         'md5_archivo_red': U.md5_archivo(d)}
        rep[mp4.name]['atomos_red'] = faststart(d)['atomos']
        rep[mp4.name]['gps_red'] = gps_bruto(d)
        rep[mp4.name]['dif_bytes'] = rep[mp4.name]['bytes_red'] - rep[mp4.name]['bytes_local']
        rep[mp4.name]['coincide_streams'] = rep[mp4.name]['md5_streams_local'] == rep[mp4.name]['md5_streams_red']
        rep[mp4.name]['nota'] = ('el montaje agrega una caja uuid (C2PA) antes de moov; video y audio idénticos'
                                 if 'uuid' in rep[mp4.name]['atomos_red'] else '')
    n_loc = sum(1 for f in Path(evi).rglob('*') if f.is_file()); n_red = sum(1 for f in dest_evi.rglob('*') if f.is_file())
    rep['evidencia_archivos_local_red'] = [n_loc, n_red]
    (dest_evi / 'copia_verificada.json').write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))
    return rep
