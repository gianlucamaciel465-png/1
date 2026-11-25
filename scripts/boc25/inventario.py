#!/usr/bin/env python3
"""BOC-25 (25/11/2026) · inventario de clips oficiales bajados de TikTok y tiras de fotogramas por clip.
Uso: python3 inventario.py  -> TRABAJO/boc25/tiras/<id>.jpg (8 cuadros con tiempo) + material/inventario_clips.md
"""
import json, subprocess, glob, os
from pathlib import Path
T = Path('/home/user/1/TRABAJO/boc25'); C = T / 'clips'; TI = T / 'tiras'; TI.mkdir(exist_ok=True)
OUT = Path('/mnt/project-files/piezas/BOC-25_octavos_hoy/material'); OUT.mkdir(parents=True, exist_ok=True)
F = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
filas = []
for mp4 in sorted(C.glob('*.mp4')):
    info = json.load(open(mp4.with_suffix('.info.json')))
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(mp4)],
                                   capture_output=True, text=True).stdout)
    v = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]
    dur = float(pr['format']['duration']); fps = v.get('r_frame_rate', '0/1')
    n, d = fps.split('/'); fpsf = float(n) / float(d or 1)
    tira = TI / f"{info['id']}.jpg"
    if not tira.exists():
        paso = dur / 8
        vf = (f"fps=1/{paso:.4f},scale=160:-2,drawtext=fontfile={F}:text='%{{pts\\:hms}}':x=3:y=3:fontsize=14:"
              f"fontcolor=yellow:box=1:boxcolor=black@0.6,tile=8x1:padding=2")
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{paso / 2:.3f}', '-i', str(mp4), '-vf', vf, '-frames:v', '1',
                        str(tira)], check=True)
    desc = (info.get('description') or info.get('title') or '').replace('\n', ' ').replace('|', '/')
    ts = info.get('timestamp')
    import datetime
    fecha = datetime.datetime.fromtimestamp(ts, datetime.timezone(datetime.timedelta(hours=-3))).strftime('%d/%m %H:%M') if ts else '?'
    filas.append((info.get('uploader_id') or info.get('uploader'), info['id'], fecha, f"{v['width']}x{v['height']}",
                  round(fpsf, 2), round(dur, 1), desc[:200], mp4.name))
filas.sort(key=lambda r: (r[0], r[2]))
L = ['# BOC-25 · Inventario de clips oficiales (TikTok) · 25/11/2026',
     '', 'Todos son de terceros, sin licencia: © de cada cuenta (CONMEBOL Sudamericana, Boca Juniors, Liga Profesional, TyC Sports).',
     'Archivo local: `/home/user/1/TRABAJO/boc25/clips/<archivo>`. Tira de 8 fotogramas con tiempo: `/home/user/1/TRABAJO/boc25/tiras/<id>.jpg`.',
     'Hora de publicación en hora argentina. Sonido: sin revisar (puede traer música de la cuenta).', '',
     '| cuenta | id | publicado | tamaño | fps | dur s | texto del posteo | archivo |', '|---|---|---|---|---|---|---|---|']
L += ['| ' + ' | '.join(map(str, r)) + ' |' for r in filas]
(OUT / 'inventario_clips.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print(len(filas))
