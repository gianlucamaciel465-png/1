#!/usr/bin/env python3
"""REAL-02 v1.1 · controles sobre el MP4 entregado (la copia de /mnt/project-files) y contra v1 (dictamen de Roma 08).
uso: venv/bin/python evidencia_v1_1.py V1_1.mp4 V1.mp4 DIR_TRABAJO_v01_1 DIR_EVIDENCIA"""
import sys, os, json, subprocess, hashlib, re
os.environ['REAL02_VER'] = 'v1_1'
sys.path.insert(0, '/home/user/1/scripts/real02')
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
import textos
from superponer import superponer, mascara, tinta_en_cuadro, borde

MP4, V1, T, E = sys.argv[1:5]
W, H, NF, SR = 1080, 1920, 307, 48000
FONT = ImageFont.truetype('/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf', 22)
for d in ('cuadros', 'cambio1', 'cambio2', 'audio', 'identidad'): os.makedirs(f'{E}/{d}', exist_ok=True)
run = lambda c: subprocess.run(c, capture_output=True, text=True, check=True)
R = {'archivo': MP4, 'comparado_con': V1}
lum_lin = lambda rgb: (lambda c: 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2])(
    np.where(rgb / 255.0 <= 0.04045, rgb / 255.0 / 12.92, ((rgb / 255.0 + 0.055) / 1.055) ** 2.4))
contraste = lambda la, lb: round((max(la, lb) + 0.05) / (min(la, lb) + 0.05), 2)

# ---------------- contenedor ----------------
p = subprocess.run(['ffmpeg', '-v', 'error', '-i', MP4, '-f', 'null', '-'], capture_output=True, text=True)
R['decodificacion'] = {'codigo': p.returncode, 'errores': p.stderr.strip()}
pr = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', MP4]).stdout)
v = next(s for s in pr['streams'] if s['codec_type'] == 'video'); a = next(s for s in pr['streams'] if s['codec_type'] == 'audio')
R['ffprobe'] = {'video': {k: v.get(k) for k in ('codec_name', 'profile', 'level', 'width', 'height', 'pix_fmt', 'r_frame_rate', 'nb_frames',
                                               'duration', 'bit_rate', 'color_space', 'color_primaries', 'color_transfer', 'color_range')},
                'audio': {k: a.get(k) for k in ('codec_name', 'profile', 'sample_rate', 'channels', 'channel_layout', 'nb_frames', 'duration', 'bit_rate')},
                'formato': {k: pr['format'].get(k) for k in ('duration', 'size', 'bit_rate')}, 'etiquetas_formato': pr['format'].get('tags', {})}
R['duracion_video_menos_audio_ms'] = round((float(v['duration']) - float(a['duration'])) * 1000, 3)
data = open(MP4, 'rb').read(); cajas, i = [], 0
while i < len(data):
    n = int.from_bytes(data[i:i + 4], 'big'); t = data[i + 4:i + 8].decode('latin1')
    if n == 1: n = int.from_bytes(data[i + 8:i + 16], 'big')
    cajas.append((t, n)); i += n if n else len(data)
meta, i = b'', 0
for t, n in cajas:
    if t != 'mdat': meta += data[i:i + n]
    i += n
R['cajas_nivel_superior'] = cajas
R['faststart_moov_antes_de_mdat'] = [c[0] for c in cajas].index('moov') < [c[0] for c in cajas].index('mdat')
R['busqueda_ubicacion_fuera_de_mdat'] = {k: meta.count(k.encode()) for k in ('©xyz', 'xyz', 'location', 'GPS', 'ISO6709', 'com.apple.quicktime', 'make', 'model')}
R['sha256_archivo'] = hashlib.sha256(data).hexdigest(); R['bytes'] = len(data); del data, meta
R['md5_paquetes'] = {s: run(['ffmpeg', '-v', 'error', '-i', MP4, '-map', f'0:{s[0]}', '-c', 'copy', '-f', 'md5', '-']).stdout.strip() for s in ('video', 'audio')}
R['cuadros_clave'] = [i for i, q in enumerate(json.loads(run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_frames', '-show_entries',
                                                              'frame=key_frame', '-of', 'json', MP4]).stdout)['frames']) if q['key_frame'] == 1]


# VBV (bufsize 25 Mbit, maxrate 20 Mb/s, llenado inicial 90 % como x264) sobre los paquetes de video en orden de decodificación
def vbv(mp4):
    pk = json.loads(run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'packet=size,dts_time', '-of', 'json', mp4]).stdout)['packets']
    buf, cap, rate, mn, t_prev, peor = 0.9 * 25e6, 25e6, 20e6, 1e18, None, 0
    for k, (sz, dts) in enumerate((int(q['size']), float(q['dts_time'])) for q in pk):
        if t_prev is not None: buf = min(cap, buf + rate * (dts - t_prev))
        buf -= 8 * sz; t_prev = dts
        if buf < mn: mn, peor = buf, k
    return {'llenado_min_%': round(100 * mn / cap, 1), 'paquete_mas_bajo': peor, 'paquetes': len(pk)}


R['vbv'] = {'v1_1': vbv(MP4), 'v1': vbv(V1)}

# ---------------- identidad con v1 ----------------
fmd5 = lambda mp4: [l.split(',')[-1].strip() for l in run(['ffmpeg', '-v', 'error', '-i', mp4, '-map', '0:v', '-fps_mode', 'passthrough',
                                                            '-f', 'framemd5', '-c:v', 'rawvideo', '-']).stdout.splitlines() if not l.startswith('#')]
m1, m11 = fmd5(V1), fmd5(MP4)
with open(f'{E}/identidad/md5_cuadros_decodificados_v1_vs_v1_1.tsv', 'w') as fh:
    fh.write('cuadro\tmd5_v1\tmd5_v1_1\tigual\n')
    for f in range(NF): fh.write(f'{f}\t{m1[f]}\t{m11[f]}\t{int(m1[f] == m11[f])}\n')


def tramos(iguales):
    out, a_ = [], 0
    for f in range(1, NF + 1):
        if f == NF or iguales[f] != iguales[a_]:
            out.append(f'f{a_}-f{f - 1} {"igual" if iguales[a_] else "distinto"}'); a_ = f
    return out


R['cuadros_decodificados_v1_vs_v1_1'] = tramos([m1[f] == m11[f] for f in range(NF)])
e1 = [l.split('\t')[1].strip() for l in open(f'{T}/entrada_md5_v1.txt')]; e11 = [l.split('\t')[1].strip() for l in open(f'{T}/entrada_md5_v1_1.txt')]
R['entrada_del_codificador_v1_vs_v1_1'] = tramos([e1[f] == e11[f] for f in range(NF)])
cmp = json.load(open(f'{T}/comparacion_f74-f93.json'))
R['f74_f93_decodificado'] = {'psnr_Y_v1_vs_v1_1_min_dB': min(r['psnr_Y_A_vs_B'] for r in cmp), 'psnr_Y_v1_vs_v1_1_max_dB': max(r['psnr_Y_A_vs_B'] for r in cmp),
                             'dif_max_Y': max(r['dif_max_Y'] for r in cmp), 'px_con_dif>4_%_max': max(r['px_dif>4_%'] for r in cmp),
                             'psnr_Y_v1_vs_entrada': [min(r['psnr_Y_A_vs_entrada'] for r in cmp), max(r['psnr_Y_A_vs_entrada'] for r in cmp)],
                             'psnr_Y_v1_1_vs_entrada': [min(r['psnr_Y_B_vs_entrada'] for r in cmp), max(r['psnr_Y_B_vs_entrada'] for r in cmp)]}

# ---------------- cuadros decodificados ----------------
raw = f'{T}/salida.rgb'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', MP4, '-map', '0:v', '-fps_mode', 'passthrough', '-vf',
                'scale=in_color_matrix=bt709:in_range=tv:flags=lanczos+accurate_rnd+full_chroma_int,format=rgb24', '-f', 'rawvideo', raw], check=True)
V = np.memmap(raw, np.uint8, 'r', shape=(NF, H, W, 3))
M = np.load(f'{T}/mascaras.npz')
PEDIDOS = [0, 39, 46, 56, 63, 70, 74, 93, 94, 110, 124, 150, 184, 229, 250, 258, 259, 280, 306]
CORTES = [(45, 46), (62, 63), (93, 94), (123, 124), (183, 184), (258, 259)]
for f in sorted(set(PEDIDOS) | {x for c in CORTES for x in c}):
    Image.fromarray(np.asarray(V[f])).save(f'{E}/cuadros/f{f:03d}.jpg', quality=92)


def hoja(fs, salida, esc=0.25, cols=8, rot=None):
    w, h = int(W * esc), int(H * esc); o = Image.new('RGB', (cols * (w + 6), ((len(fs) + cols - 1) // cols) * (h + 30)), (18, 18, 18)); d = ImageDraw.Draw(o)
    for k, f in enumerate(fs):
        x0, y0 = (k % cols) * (w + 6), (k // cols) * (h + 30)
        o.paste(Image.fromarray(np.asarray(V[f])).resize((w, h), Image.LANCZOS), (x0, y0 + 28)); d.text((x0 + 4, y0 + 2), rot[k] if rot else f'f{f}', fill=(255, 230, 0), font=FONT)
    o.save(salida, quality=88)


hoja(PEDIDOS, f'{E}/cuadros/hoja_cuadros_pedidos.jpg', cols=10)
hoja([x for c in CORTES for x in c], f'{E}/cuadros/hoja_pares_de_corte.jpg', cols=4, rot=[f'f{x}' + (' (antes)' if j == 0 else ' (después)') for c in CORTES for j, x in enumerate(c)])
dif = lambda x, y: float(np.abs(np.asarray(V[x], np.int16) - np.asarray(V[y], np.int16)).mean())
R['cortes'] = [{'corte': f'f{a_}/f{b_}', 'dif_en_el_corte': round(dif(a_, b_), 1), 'dif_cuadro_previo': round(dif(a_ - 1, a_), 1),
                'dif_cuadro_siguiente': round(dif(b_, b_ + 1), 1)} for a_, b_ in CORTES]
dprev = [dif(f, f - 1) for f in range(1, NF)]
R['cuadros_casi_iguales_al_anterior_dif<0,5'] = [f for f in range(1, NF) if dprev[f - 1] < 0.5]
R['cuadros_negros'] = [f for f in range(NF) if np.asarray(V[f]).mean() < 8]

# ---------------- cambio 1: el «3» sobre la roca ----------------
mg = [l.rstrip('\n').split('\t') for l in open(f'{T}/margenes_v01_1.tsv')][1:]
R['cambio1_T4'] = {'caja_tinta': textos.caja_tinta('T4'), 'por_cuadro': [{'cuadro': int(r[0]), 'remera_px': float(r[6]), 'espuma_px': float(r[7])} for r in mg if r[1] == 'T4']}
R['cambio1_T4']['min_remera_px'] = min(x['remera_px'] for x in R['cambio1_T4']['por_cuadro'])
R['cambio1_T4']['min_espuma_px'] = min(x['espuma_px'] for x in R['cambio1_T4']['por_cuadro'])
for f in (63, 70):
    ys, xs = np.nonzero(tinta_en_cuadro(f, {'T4'}))
    x0, x1, y0, y1 = max(0, xs.min() - 140), min(W, xs.max() + 60), max(0, ys.min() - 140), min(H, ys.max() + 140)
    Image.fromarray(np.asarray(V[f])[y0:y1, x0:x1]).save(f'{E}/cambio1/T4_f{f:03d}_1a1.png')
    Image.fromarray(superponer(np.asarray(V[f]), f, M)[y0:y1, x0:x1]).save(f'{E}/cambio1/T4_f{f:03d}_1a1_mascaras.png')
    Image.fromarray(superponer(np.asarray(V[f]), f, M)).resize((540, 960), Image.LANCZOS).save(f'{E}/cambio1/mascara_f{f:03d}.jpg', quality=90)
R['margenes_todos'] = {}
for tid in ('T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T8'):
    fil = [r for r in mg if r[1] == tid]
    if fil:
        R['margenes_todos'][tid] = {'cuadros': f'f{fil[0][0]}-f{fil[-1][0]}', 'min_remera_px': min(float(r[6]) for r in fil),
                                    'min_espuma_px': min((float(r[7]) for r in fil if r[7] != 'nan'), default=None)}

# ---------------- cambio 2 ----------------
# a) P7 en movimiento: diferencia entre cuadros consecutivos
d7 = [round(dif(f, f - 1), 3) for f in range(260, NF)]
R['cambio2_P7_movimiento'] = {'dif_media_min': min(d7), 'cuadro_min': 260 + int(np.argmin(d7)), 'dif_media_max': max(d7),
                              'cuadros_con_dif_0': [260 + k for k, x in enumerate(d7) if x == 0],
                              'px_que_cambian_min_%': min(round(100 * float((np.asarray(V[f]) != np.asarray(V[f - 1])).any(-1).mean()), 1) for f in range(260, NF))}


# b) contraste de rocce.shop sobre la espuma de P6, con contorno
def capa_T8(f):
    for tid, rgba, tinta, x, y in textos.capas(f):
        if tid == 'T8':
            r = np.asarray(rgba, np.float32) / 255; al = r[..., 3]; bl = r[..., 0]
            relleno = (al > 0.95) & (bl > 0.95); cont = (np.asarray(tinta) > 242) & (bl < 0.05)
            relleno = ndi.binary_erosion(relleno, iterations=2); cont = ndi.binary_erosion(cont, iterations=2)
            out = []
            for m in (relleno, cont, np.asarray(tinta) > 25):
                g = np.zeros((H, W), bool); ys, xs = np.nonzero(m); ok = (ys + y < H) & (xs + x < W); g[ys[ok] + y, xs[ok] + x] = True; out.append(g)
            return out


filas = []
for f in range(229, 259):
    rel, con, ink = capa_T8(f); im = np.asarray(V[f]).astype(np.float64); L = lum_lin(im)
    anillo = ndi.binary_dilation(ink, iterations=30) & ~ndi.binary_dilation(ink, iterations=6)
    l_rel = float(np.percentile(L[rel], 1)); l_con = float(np.percentile(L[con], 99)); l_esp = float(L[anillo].max())
    filas.append({'cuadro': f, 'relleno_p1': round(l_rel, 3), 'contorno_p99': round(l_con, 4), 'fondo_max_alrededor': round(l_esp, 3),
                  'contraste_relleno_vs_contorno': contraste(l_rel, l_con), 'contraste_contorno_vs_fondo_mas_claro': contraste(l_esp, l_con),
                  'contraste_relleno_vs_fondo_mas_claro_sin_contorno': contraste(l_rel, l_esp)})
R['cambio2_contraste_rocce_shop_P6'] = {'min_relleno_vs_contorno': min(r['contraste_relleno_vs_contorno'] for r in filas),
                                        'min_contorno_vs_fondo_mas_claro': min(r['contraste_contorno_vs_fondo_mas_claro'] for r in filas),
                                        'min_relleno_vs_fondo_sin_contorno': min(r['contraste_relleno_vs_fondo_mas_claro_sin_contorno'] for r in filas),
                                        'por_cuadro': filas}
# contraste de T7 y rocce.shop sobre el azul de P7
c7 = []
for f in (259, 282, 306):
    im = np.asarray(V[f]).astype(np.float64); L = lum_lin(im)
    for tid in ('T7', 'T8'):
        ink = tinta_en_cuadro(f, {tid}); fondo = ndi.binary_dilation(ink, iterations=30) & ~ndi.binary_dilation(tinta_en_cuadro(f), iterations=14)
        nucleo = ndi.binary_erosion(ink, iterations=3) & (L > 0.5)
        c7.append({'cuadro': f, 'texto': tid, 'contraste_relleno_vs_fondo_mas_claro': contraste(float(np.percentile(L[nucleo], 1)), float(L[fondo].max()))})
R['cambio2_contraste_P7'] = c7
# c) fondo de P7: azul liso, sin franja gris
azul = np.array([2, 7, 12], np.float64); fondo7 = []
for f in range(259, NF):
    im = np.asarray(V[f]).astype(np.float64); txt = ndi.binary_dilation(tinta_en_cuadro(f), iterations=30)
    for nom, y0, y1 in (('arriba', 0, 330), ('abajo', 1790, H)):
        z = ~txt[y0:y1]; px = im[y0:y1][z]
        fondo7.append({'cuadro': f, 'zona': nom, 'rgb_mediana': [round(float(x), 1) for x in np.median(px, 0)], 'luma_max': round(float((px @ [.2126, .7152, .0722]).max()), 1)})
R['cambio2_fondo_P7'] = {'azul_medido_en_la_foto': [2, 7, 12],
                         'luma_max_fuera_de_textos': max(x['luma_max'] for x in fondo7),
                         'mediana_rgb_rango': [[min(x['rgb_mediana'][c] for x in fondo7) for c in range(3)], [max(x['rgb_mediana'][c] for x in fondo7) for c in range(3)]]}
# d) primera fila con placas o etiqueta debajo de rocce.shop (columnas 150-930) y separación con la tinta de los textos
sep = []
for f in (259, 282, 306):
    im = np.asarray(V[f]).astype(np.float64); l = im @ [.2126, .7152, .0722]; ink = tinta_en_cuadro(f)
    fil = np.nonzero((l[400:900, 150:930] > 90).sum(1) > 20)[0]; y_obj = 400 + int(fil[0])
    sep.append({'cuadro': f, 'primera_fila_de_placas_o_etiqueta': y_obj, 'ultima_fila_de_tinta_de_texto': int(np.nonzero(ink.any(1))[0].max()),
                'separacion_px': y_obj - int(np.nonzero(ink.any(1))[0].max())})
R['cambio2_textos_vs_placas_P7'] = sep
# e) estampado de 4625 completo en f184-f258 (letras oscuras de ROCCÉ + Founders Privée celeste, dentro de la remera)
est = []
for f in range(184, 259):
    im = np.asarray(V[f]).astype(np.int16); l = im @ np.array([2126, 7152, 722]) / 10000
    rem = ndi.binary_erosion(mascara(M, f'rem_{f}'), iterations=10)
    # letras de denim (luma < 110) y Founders Privée celeste (B−R > 60, luma > 100); las sombras azuladas de la tela quedan por debajo de B−R 60
    tinta_e = ((l < 110) | (((im[..., 2] - im[..., 0]) > 60) & (l > 100))) & rem
    tinta_e = ndi.binary_opening(tinta_e, iterations=1)
    lab, n = ndi.label(tinta_e); sz = ndi.sum(tinta_e, lab, range(1, n + 1)); keep = np.isin(lab, 1 + np.nonzero(sz >= 80)[0])
    ys, xs = np.nonzero(keep)
    est.append({'cuadro': f, 'x': [int(xs.min()), int(xs.max())], 'y': [int(ys.min()), int(ys.max())], 'px': int(keep.sum())})
R['cambio2_estampado_P6'] = {'margen_izq_min_px': min(e['x'][0] for e in est), 'cuadro_margen_izq_min': est[int(np.argmin([e['x'][0] for e in est]))]['cuadro'],
                             'margen_der_min_px': min(W - 1 - e['x'][1] for e in est), 'margen_inf_min_px': min(H - 1 - e['y'][1] for e in est),
                             'px_min': min(e['px'] for e in est), 'px_max': max(e['px'] for e in est), 'por_cuadro': est}
for f in (184, 229, 258):
    e_ = next(e for e in est if e['cuadro'] == f)
    x0, x1, y0, y1 = max(0, e_['x'][0] - 60), min(W, e_['x'][1] + 60), max(0, e_['y'][0] - 60), min(H, e_['y'][1] + 60)
    Image.fromarray(np.asarray(V[f])[y0:y1, x0:x1]).save(f'{E}/cambio2/estampado_4625_f{f:03d}_1a1.png')
# f) cuadros 1:1 pedidos
for f in (229, 258, 259, 280, 306):
    Image.fromarray(np.asarray(V[f])).save(f'{E}/cambio2/f{f:03d}_1a1.png')
for f in (229, 258):
    rel, con, ink = capa_T8(f); ys, xs = np.nonzero(ink)
    Image.fromarray(np.asarray(V[f])[max(0, ys.min() - 150):ys.max() + 60, max(0, xs.min() - 40):xs.max() + 40]).save(f'{E}/cambio2/textos_P6_f{f:03d}_1a1.png')

# ---------------- audio ----------------
def pcm(mp4): return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', mp4, '-map', '0:a', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                                                 capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)
aud, aud1 = pcm(MP4), pcm(V1)
dd = np.nonzero(np.any(aud[:min(len(aud), len(aud1))] != aud1[:min(len(aud), len(aud1))], 1))[0]
R['audio_identico_a_v1_hasta'] = {'primera_muestra_distinta': int(dd[0]) if len(dd) else None, 'cuadro': round(dd[0] / 1600, 2) if len(dd) else None}
pk = lambda mp4: [l.split(',')[-1].strip() for l in run(['ffmpeg', '-v', 'error', '-i', mp4, '-map', '0:a', '-c', 'copy', '-f', 'framemd5', '-']).stdout.splitlines() if not l.startswith('#')]
p1, p11 = pk(V1), pk(MP4)
R['audio_paquetes_iguales_a_v1_desde_el_inicio'] = next((k for k in range(len(p1)) if p1[k] != p11[k]), len(p1))
eb = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', MP4, '-map', '0:a', '-af', 'ebur128=peak=true:framelog=verbose', '-f', 'null', '-'],
                    capture_output=True, text=True).stderr
s = eb[eb.rfind('Summary:'):]; num = lambda k: float(re.search(k + r':\s+(-?[\d.]+)', s).group(1))
R['ebur128'] = {'I_LUFS': num('I'), 'LRA_LU': num('LRA'), 'true_peak_dBTP': num('Peak')}
db = lambda x: round(10 * np.log10(np.mean(x ** 2) + 1e-20), 2); fr = lambda f: int(round(f / 30 * SR))
R['rms_cada_0_1_s'] = [(round(k / 10, 1), db(aud[k * 4800:(k + 1) * 4800])) for k in range(int(np.ceil(fr(NF) / 4800)))]
R['rms_tramos_dBFS'] = {'f78-f93 (casi silencio)': db(aud[fr(78):fr(94)]), 'f94-f123': db(aud[fr(94):fr(124)]), 'f184-f228': db(aud[fr(184):fr(229)]),
                        'f229-f258 (rocce.shop sobre P6)': db(aud[fr(229):fr(259)]), 'f259-f306 (P7)': db(aud[fr(259):fr(NF)]), 'ultimos 0,1 s': db(aud[fr(NF) - 4800:fr(NF)])}
seg = aud[fr(74):fr(94)]
R['casi_silencio_f74_f93'] = {'muestras_en_cero': int((seg == 0).sum()), 'rms_min_por_cuadro_dBFS': min(db(aud[fr(f):fr(f + 1)]) for f in range(78, 94))}
R['rms_por_cuadro_f224_f262'] = [(f, db(aud[fr(f):fr(f + 1)]), db(aud1[fr(f):fr(f + 1)])) for f in range(224, 263)]
Wg, Hg = 1600, 520; g = Image.new('RGB', (Wg, Hg), (250, 250, 250)); d = ImageDraw.Draw(g); sm = ImageFont.truetype('/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf', 15)
X = lambda tt: 60 + (Wg - 80) * tt / (NF / 30); Y = lambda v_: 20 + (Hg - 60) * (0 - v_) / 70
for v_ in range(0, -71, 10): d.line([(60, Y(v_)), (Wg - 20, Y(v_))], fill=(220, 220, 220)); d.text((8, Y(v_) - 9), f'{v_}', fill=(90, 90, 90), font=sm)
for f in (46, 63, 74, 94, 124, 184, 229, 259): d.line([(X(f / 30), 20), (X(f / 30), Hg - 40)], fill=(255, 150, 150)); d.text((X(f / 30) + 3, Hg - 38), f'f{f}', fill=(200, 0, 0), font=sm)
d.line([(X(f / 30 + 1 / 60), Y(max(db(aud1[fr(f):fr(f + 1)]), -70))) for f in range(NF)], fill=(170, 170, 170), width=1)
d.line([(X(f / 30 + 1 / 60), Y(max(db(aud[fr(f):fr(f + 1)]), -70))) for f in range(NF)], fill=(30, 90, 200), width=2)
d.text((70, 24), 'RMS dBFS por cuadro · azul: v1.1 · gris: v1 · rojo: cortes, f74 y f229 (rocce.shop + clic)', fill=(0, 0, 0), font=sm)
g.save(f'{E}/audio/rms_por_cuadro_v1_vs_v1_1.png')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', MP4, '-filter_complex', '[0:a]showspectrumpic=s=1400x500:legend=1:scale=log:fscale=lin:stop=12000',
                '-frames:v', '1', f'{E}/audio/espectrograma_completo.png'], check=True)
os.remove(raw)
json.dump(R, open(f'{E}/controles_v1_1.json', 'w'), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
for k, val in R.items():
    if k not in ('rms_cada_0_1_s', 'cajas_nivel_superior', 'ffprobe') and not (isinstance(val, dict) and ('por_cuadro' in val)):
        print(k, json.dumps(val, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, 'item') else str(o))[:700])
print('estampado', {k: v_ for k, v_ in R['cambio2_estampado_P6'].items() if k != 'por_cuadro'})
print('contraste P6', {k: v_ for k, v_ in R['cambio2_contraste_rocce_shop_P6'].items() if k != 'por_cuadro'})
print('T4', {k: v_ for k, v_ in R['cambio1_T4'].items() if k != 'por_cuadro'})
