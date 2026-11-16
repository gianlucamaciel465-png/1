#!/usr/bin/env python3
"""REAL-02 v01 · controles sobre el MP4 final (la copia de /mnt/project-files). Todo se mide sobre el archivo entregado:
cuadros pedidos y pares de corte, máscara de la remera contra cada número, área de espuma en los picos, pecho de P4 a 1:1,
audio (ebur128, RMS cada 0,1 s, casi silencio, entrada de la música, espectrograma), contenedor (ffprobe, orden de cajas,
metadatos, huellas de paquetes).
uso: venv/bin/python evidencia.py MASTER.mp4 DIR_TRABAJO DIR_EVIDENCIA"""
import sys, os, json, subprocess, hashlib, re
sys.path.insert(0, '/home/user/1/scripts/real02')
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
from superponer import superponer, mascara, tinta_en_cuadro, borde
from textos import TEXTOS

MP4, T, E = sys.argv[1:4]
W, H, NF, SR = 1080, 1920, 307, 48000
FONT = ImageFont.truetype('/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf', 22)
for d in ('cuadros', 'mascaras', 'espuma', 'p4', 'audio'): os.makedirs(f'{E}/{d}', exist_ok=True)
run = lambda c: subprocess.run(c, capture_output=True, text=True, check=True)
R = {'archivo': MP4}

# ---------------- decodificación completa ----------------
p = subprocess.run(['ffmpeg', '-v', 'error', '-i', MP4, '-f', 'null', '-'], capture_output=True, text=True)
R['decodificacion'] = {'codigo': p.returncode, 'errores': p.stderr.strip()}
raw = f'{T}/salida.rgb'
if not os.path.exists(raw) or os.path.getsize(raw) != NF * W * H * 3:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', MP4, '-map', '0:v', '-vf',
                    'scale=in_color_matrix=bt709:in_range=tv:flags=lanczos+accurate_rnd+full_chroma_int,format=rgb24',
                    '-f', 'rawvideo', raw], check=True)
V = np.memmap(raw, np.uint8, 'r', shape=(NF, H, W, 3))
M = np.load(f'{T}/mascaras.npz')

# ---------------- contenedor ----------------
pr = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', MP4]).stdout)
v = next(s for s in pr['streams'] if s['codec_type'] == 'video'); a = next(s for s in pr['streams'] if s['codec_type'] == 'audio')
R['ffprobe'] = {'video': {k: v.get(k) for k in ('codec_name', 'profile', 'level', 'width', 'height', 'pix_fmt', 'r_frame_rate', 'avg_frame_rate',
                                               'nb_frames', 'duration', 'bit_rate', 'color_space', 'color_primaries', 'color_transfer', 'color_range')},
                'audio': {k: a.get(k) for k in ('codec_name', 'profile', 'sample_rate', 'channels', 'channel_layout', 'nb_frames', 'duration', 'bit_rate')},
                'formato': {k: pr['format'].get(k) for k in ('format_name', 'duration', 'size', 'bit_rate')},
                'etiquetas_formato': pr['format'].get('tags', {}),
                'etiquetas_video': v.get('tags', {}), 'etiquetas_audio': a.get('tags', {})}
R['duracion_video_menos_audio_ms'] = round((float(v['duration']) - float(a['duration'])) * 1000, 3)
cajas = []
with open(MP4, 'rb') as fh:
    data = fh.read()
i = 0
while i < len(data):
    n = int.from_bytes(data[i:i + 4], 'big'); t = data[i + 4:i + 8].decode('latin1')
    if n == 1: n = int.from_bytes(data[i + 8:i + 16], 'big')
    cajas.append((t, n)); i += n if n else len(data)
R['cajas_nivel_superior'] = cajas
R['faststart_moov_antes_de_mdat'] = [c[0] for c in cajas].index('moov') < [c[0] for c in cajas].index('mdat')
meta, i = b'', 0                               # todas las cajas menos mdat (los datos comprimidos dan coincidencias al azar)
for t, n in cajas:
    if t != 'mdat': meta += data[i:i + n]
    i += n
R['busqueda_ubicacion_fuera_de_mdat'] = {k: meta.count(k.encode()) for k in ('©xyz', 'xyz', 'location', 'GPS', 'ISO6709', 'com.apple.quicktime', 'make', 'model')}
R['bytes_caja_uuid'] = [n for t, n in cajas if t == 'uuid']
R['sha256_archivo'] = hashlib.sha256(data).hexdigest(); R['bytes'] = len(data)
R['md5_paquetes'] = {s: run(['ffmpeg', '-v', 'error', '-i', MP4, '-map', f'0:{s[0]}', '-c', 'copy', '-f', 'md5', '-']).stdout.strip()
                     for s in ('video', 'audio')}
del data

# ---------------- cuadros pedidos y pares de corte ----------------
PEDIDOS = [0, 39, 46, 56, 63, 70, 74, 93, 94, 110, 124, 150, 184, 229, 250, 306]
CORTES = [(45, 46), (62, 63), (93, 94), (123, 124), (183, 184), (228, 229)]
for f in sorted(set(PEDIDOS) | {x for c in CORTES for x in c}):
    Image.fromarray(np.asarray(V[f])).save(f'{E}/cuadros/f{f:03d}.jpg', quality=92)


def hoja(fs, salida, esc=0.25, cols=8, rotulos=None):
    w, h = int(W * esc), int(H * esc); filas = (len(fs) + cols - 1) // cols
    o = Image.new('RGB', (cols * (w + 6), filas * (h + 30)), (18, 18, 18)); d = ImageDraw.Draw(o)
    for k, f in enumerate(fs):
        x0, y0 = (k % cols) * (w + 6), (k // cols) * (h + 30)
        o.paste(Image.fromarray(np.asarray(V[f])).resize((w, h), Image.LANCZOS), (x0, y0 + 28))
        d.text((x0 + 4, y0 + 2), rotulos[k] if rotulos else f'f{f}', fill=(255, 230, 0), font=FONT)
    o.save(salida, quality=88)


hoja(PEDIDOS, f'{E}/cuadros/hoja_cuadros_pedidos.jpg')
hoja([x for c in CORTES for x in c], f'{E}/cuadros/hoja_pares_de_corte.jpg', cols=4,
     rotulos=[f'f{x}' + (' (antes)' if j == 0 else ' (después)') for c in CORTES for j, x in enumerate(c)])
# continuidad en los cortes: diferencia media entre el último cuadro de un plano y el primero del siguiente, y dentro del plano
R['cortes'] = []
for a_, b_ in CORTES:
    dif = lambda x, y: float(np.abs(np.asarray(V[x], np.int16) - np.asarray(V[y], np.int16)).mean())
    R['cortes'].append({'corte': f'f{a_}/f{b_}', 'dif_media_en_el_corte': round(dif(a_, b_), 1),
                        'dif_media_cuadro_previo': round(dif(a_ - 1, a_), 1), 'dif_media_cuadro_siguiente': round(dif(b_, b_ + 1), 1)})
# cuadros repetidos (congelados) fuera de P7, que es foto fija por guion
dprev = [float(np.abs(np.asarray(V[f], np.int16) - np.asarray(V[f - 1], np.int16)).mean()) for f in range(1, NF)]
R['cuadros_casi_iguales_al_anterior_dif<0,5'] = {'fuera_de_P7': [f for f in range(1, 229) if dprev[f - 1] < 0.5],
                                                 'P7_dif_max_entre_cuadros': round(max(dprev[229:]), 3),
                                                 'P7_cuadro_dif_max': 230 + int(np.argmax(dprev[229:]))}
R['cuadros_negros'] = [f for f in range(NF) if np.asarray(V[f]).mean() < 8]

# ---------------- máscara de la remera contra cada número ----------------
CTRL = {'T1': [0, 38, 45], 'T2': [0, 38, 45], 'T3': [46, 56, 62], 'T4': [63, 70, 73], 'T5': [74, 84, 93], 'T6': [184, 222, 228]}
for f in sorted({x for v_ in CTRL.values() for x in v_}):
    Image.fromarray(superponer(np.asarray(V[f]), f, M)).resize((540, 960), Image.LANCZOS).save(f'{E}/mascaras/mascara_f{f:03d}.jpg', quality=90)
mg = [l.rstrip('\n').split('\t') for l in open(f'{T}/margenes_v01.tsv')][1:]
R['margenes'] = {}
for tid in ('T1', 'T2', 'T3', 'T4', 'T5', 'T6'):
    filas = [r for r in mg if r[1] == tid]
    rr = min(filas, key=lambda r: float(r[6])); ee = min(filas, key=lambda r: float(r[7]) if r[7] != 'nan' else 1e9)
    R['margenes'][tid] = {'cuadros': f'f{filas[0][0]}-f{filas[-1][0]}', 'min_a_remera_px': float(rr[6]), 'cuadro_min_remera': int(rr[0]),
                          'min_a_espuma_px': float(ee[7]), 'cuadro_min_espuma': int(ee[0]),
                          'cuadros_con_espuma_a_menos_de_24px': sum(1 for r in filas if r[7] != 'nan' and float(r[7]) < 24)}
# recortes 1:1 de los números en su cuadro más cercano a la remera
for tid in ('T2', 'T3', 'T4'):
    f = R['margenes'][tid]['cuadro_min_remera']
    ys, xs = np.nonzero(tinta_en_cuadro(f, {tid}))
    x0, x1 = max(0, xs.min() - 120), min(W, xs.max() + 120); y0, y1 = max(0, ys.min() - 120), min(H, ys.max() + 160)
    Image.fromarray(superponer(np.asarray(V[f]), f, M)[y0:y1, x0:x1]).save(f'{E}/mascaras/{tid}_f{f:03d}_1a1.png')

# ---------------- espuma en los picos ----------------
yv = np.arange(H, dtype=np.float32)
DEG = np.interp(yv, [0, 40, 200, 400, H], [0, 0, 0.30, 0, 0]).astype(np.float32)[:, None, None]
HZ = {39: 380, 56: 0, 70: 0}
R['espuma'] = {}
paneles = []
for f in (39, 56, 70):
    img = np.asarray(V[f]).astype(np.float32) / (1 - DEG) if f in (39, 70) else np.asarray(V[f]).astype(np.float32)
    lum = img @ np.array([.2126, .7152, .0722], np.float32); sat = img.max(-1) - img.min(-1)
    rem = mascara(M, f'rem_{f}'); txt = ndi.binary_dilation(tinta_en_cuadro(f), iterations=16)
    A = mascara(M, f'esp_{f}') & ~txt
    Bm = (lum > 185) & (sat < 70) & ~ndi.binary_dilation(rem, iterations=6) & ~txt; Bm[:HZ[f]] = False
    Bm = ndi.binary_opening(Bm, iterations=1)
    bb = np.asarray(np.memmap(f'{T}/base.rgb', np.uint8, 'r', shape=(NF, H, W, 3))[f]).astype(np.float32)
    lb = bb @ np.array([.2126, .7152, .0722], np.float32); sb = bb.max(-1) - bb.min(-1)
    Bb = (lb > 185) & (sb < 70) & ~ndi.binary_dilation(rem, iterations=6); Bb[:HZ[f]] = False; Bb = ndi.binary_opening(Bb, iterations=1)
    R['espuma'][f'f{f}'] = {'A_blanca_sat<40_px': int(A.sum()), 'A_%_cuadro': round(100 * A.sum() / (W * H), 2),
                            'B_blanca_o_beige_sat<70_px': int(Bm.sum()), 'B_%_cuadro': round(100 * Bm.sum() / (W * H), 2),
                            'B_en_base_sin_textos_%': round(100 * Bb.sum() / (W * H), 2),
                            'zona_excluida_por_textos_px': int(txt.sum()), 'horizonte_y': HZ[f]}
    o = np.asarray(V[f]).astype(np.float32).copy()
    o[Bm] = o[Bm] * 0.5 + np.array([255, 0, 255]) * 0.5; o[borde(A, 1)] = (0, 230, 255); o[borde(rem)] = (255, 220, 0)
    pan = Image.fromarray(o.clip(0, 255).astype(np.uint8)).resize((432, 768), Image.LANCZOS)
    ImageDraw.Draw(pan).text((8, 6), f'f{f}  B {100 * Bm.sum() / (W * H):.1f} %  A {100 * A.sum() / (W * H):.1f} %', fill=(255, 255, 0), font=FONT)
    paneles.append(pan)
o = Image.new('RGB', (3 * 438, 768), (18, 18, 18))
for k, pan in enumerate(paneles): o.paste(pan, (k * 438, 0))
o.save(f'{E}/espuma/espuma_f39_f56_f70.jpg', quality=90)

# ---------------- P4: pecho completo y estrella celeste ----------------
R['p4'] = []
fil = np.zeros((H, 1), bool); fil[450:1250] = True
for f in range(94, 124):
    im = np.asarray(V[f]).astype(np.int16); lum = im @ np.array([2126, 7152, 722]) / 10000; sat = im.max(-1) - im.min(-1)
    # tela clara (componente mayor) con los huecos rellenos: el estampado queda adentro; baranda y mano quedan afuera
    tela = ndi.binary_closing((lum > 165) & (sat < 50), np.ones((3, 3)), iterations=6)
    lab, n = ndi.label(tela); k = int(np.argmax(ndi.sum(tela, lab, range(1, n + 1)))) + 1
    m = ndi.binary_fill_holes(lab == k)
    tinta = ndi.binary_opening((lum < 130) & m & fil, iterations=1)
    ys, xs = np.nonzero(tinta)
    cel = (im[..., 2] - im[..., 0] > 40) & (im[..., 2] > 180) & m & fil          # estrella celeste
    cy_, cx_ = np.nonzero(cel)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    lap = ndi.laplace(lum[y0:y1 + 1, x0:x1 + 1].astype(np.float32))
    R['p4'].append({'cuadro': f, 'tinta_x': [int(x0), int(x1)], 'tinta_y': [int(y0), int(y1)],
                    'margen_izq_px': int(x0), 'margen_der_px': int(W - 1 - x1), 'nitidez_laplaciano_p99': round(float(np.percentile(np.abs(lap), 99)), 1),
                    'estrella_px': int(cel.sum()), 'estrella_rgb_media': [round(float(x), 1) for x in im[cel].mean(0)] if cel.sum() else None,
                    'estrella_centro': [int(cx_.mean()), int(cy_.mean())] if cel.sum() else None})
R['p4_resumen'] = {'cuadros_con_frase_dentro_del_cuadro': sum(1 for r in R['p4'] if r['margen_izq_px'] > 0 and r['margen_der_px'] > 0),
                   'cuadros_con_estrella_celeste': sum(1 for r in R['p4'] if r['estrella_px'] > 1500),
                   'margen_izq_min_px': min(r['margen_izq_px'] for r in R['p4']), 'margen_der_min_px': min(r['margen_der_px'] for r in R['p4'])}
for f in (94, 110, 123):
    r = next(x for x in R['p4'] if x['cuadro'] == f)
    x0, x1 = max(0, r['tinta_x'][0] - 40), min(W, r['tinta_x'][1] + 40); y0, y1 = max(0, r['tinta_y'][0] - 40), min(H, r['tinta_y'][1] + 40)
    Image.fromarray(np.asarray(V[f])[y0:y1, x0:x1]).save(f'{E}/p4/pecho_f{f:03d}_1a1.png')
    cx, cy = r['estrella_centro']
    Image.fromarray(np.asarray(V[f])[cy - 60:cy + 60, cx - 90:cx + 90]).save(f'{E}/p4/estrella_f{f:03d}_1a1.png')

# ---------------- audio ----------------
aud = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', MP4, '-map', '0:a', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                                    capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)
R['audio_muestras_decodificadas'] = len(aud)
eb = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', MP4, '-map', '0:a', '-af', 'ebur128=peak=true:framelog=verbose', '-f', 'null', '-'],
                    capture_output=True, text=True).stderr
s = eb[eb.rfind('Summary:'):]
num = lambda k: float(re.search(k + r':\s+(-?[\d.]+)', s).group(1))
R['ebur128'] = {'I_LUFS': num('I'), 'LRA_LU': num('LRA'), 'true_peak_dBTP': num('Peak')}
db = lambda x: round(10 * np.log10(np.mean(x ** 2) + 1e-20), 2)
fr = lambda f: int(round(f / 30 * SR))
R['rms_cada_0_1_s'] = [(round(k / 10, 1), db(aud[k * 4800:(k + 1) * 4800])) for k in range(int(np.ceil(fr(NF) / 4800)))]
R['rms_tramos_dBFS'] = {'f63-f73 (ola 3)': db(aud[fr(63):fr(74)]), 'f74-f77 (bajada)': db(aud[fr(74):fr(78)]),
                        'f78-f93 (casi silencio)': db(aud[fr(78):fr(94)]), 'f88-f93': db(aud[fr(88):fr(94)]),
                        'f94-f99 (entra la música)': db(aud[fr(94):fr(100)]), 'f94-f123 (P4)': db(aud[fr(94):fr(124)]),
                        'f124-f183 (P5)': db(aud[fr(124):fr(184)]), 'f184-f228 (P6)': db(aud[fr(184):fr(229)]),
                        'f229-f306 (P7)': db(aud[fr(229):fr(NF)]), 'ultimos 0,1 s': db(aud[fr(NF) - 4800:fr(NF)])}
seg = aud[fr(74):fr(94)]
R['casi_silencio_f74_f93'] = {'muestras_exactamente_cero': int((seg == 0).sum()), 'total_muestras': int(seg.size),
                              'pico_abs_dBFS': round(20 * np.log10(np.abs(seg).max()), 2),
                              'rms_min_por_cuadro_dBFS': min(db(aud[fr(f):fr(f + 1)]) for f in range(78, 94))}
# entrada de la música: primer cuadro desde f80 cuyo RMS sube más de 20 dB sobre el casi silencio
base_s = R['rms_tramos_dBFS']['f78-f93 (casi silencio)']
R['primer_cuadro_mas_de_20dB_sobre_el_silencio'] = next(f for f in range(80, 130) if db(aud[fr(f):fr(f + 1)]) > base_s + 20)
R['rms_por_cuadro_f70_f100'] = [(f, db(aud[fr(f):fr(f + 1)])) for f in range(70, 101)]
# gráfico de RMS cada 0,1 s y por cuadro con los cortes
Wg, Hg = 1600, 520; g = Image.new('RGB', (Wg, Hg), (250, 250, 250)); d = ImageDraw.Draw(g); sm = ImageFont.truetype('/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf', 15)
X = lambda tt: 60 + (Wg - 80) * tt / (NF / 30); Y = lambda v_: 20 + (Hg - 60) * (0 - v_) / 70
for v_ in range(0, -71, 10): d.line([(60, Y(v_)), (Wg - 20, Y(v_))], fill=(220, 220, 220)); d.text((8, Y(v_) - 9), f'{v_}', fill=(90, 90, 90), font=sm)
for f in (46, 63, 74, 94, 124, 184, 229): d.line([(X(f / 30), 20), (X(f / 30), Hg - 40)], fill=(255, 150, 150)); d.text((X(f / 30) + 3, Hg - 38), f'f{f}', fill=(200, 0, 0), font=sm)
pf = [(f / 30 + 1 / 60, db(aud[fr(f):fr(f + 1)])) for f in range(NF)]
d.line([(X(tt), Y(max(v_, -70))) for tt, v_ in pf], fill=(30, 90, 200), width=2)
d.line([(X(tt + 0.05), Y(max(v_, -70))) for tt, v_ in R['rms_cada_0_1_s']], fill=(0, 0, 0), width=1)
d.line([(60, Y(-45)), (Wg - 20, Y(-45))], fill=(0, 160, 0)); d.text((Wg - 330, Y(-45) - 20), '−45 dBFS (casi silencio, guion)', fill=(0, 130, 0), font=sm)
d.text((70, 24), 'RMS dBFS · azul: por cuadro · negro: cada 0,1 s · rojo: cortes y f74 («Ninguna.»)', fill=(0, 0, 0), font=sm)
g.save(f'{E}/audio/rms_por_cuadro.png')
for nombre, extra in (('espectrograma_completo.png', []), ('espectrograma_f60-f110.png', ['-ss', str(60 / 30), '-t', str(50 / 30)])):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *extra, '-i', MP4, '-filter_complex',
                    '[0:a]showspectrumpic=s=1400x500:legend=1:scale=log:fscale=lin:stop=12000', '-frames:v', '1', f'{E}/audio/{nombre}'], check=True)

json.dump(R, open(f'{E}/controles_v1.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: R[k] for k in ('decodificacion', 'duracion_video_menos_audio_ms', 'faststart_moov_antes_de_mdat', 'busqueda_ubicacion_fuera_de_mdat', 'bytes_caja_uuid',
                                    'md5_paquetes', 'ebur128', 'rms_tramos_dBFS', 'casi_silencio_f74_f93', 'primer_cuadro_mas_de_20dB_sobre_el_silencio',
                                    'espuma', 'margenes', 'cortes', 'cuadros_casi_iguales_al_anterior_dif<0,5', 'cuadros_negros', 'p4_resumen')}, ensure_ascii=False, indent=1))
print('P4', [(r['cuadro'], r['tinta_x'], r['nitidez_laplaciano_p99'], r['estrella_px']) for r in R['p4']])
