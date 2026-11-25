#!/usr/bin/env python3
"""OCR cuadro a cuadro de un MP4 a resolución completa (control de casas de apuestas y frases en carteles).

Uso: ocr-env/bin/python -I ocr_cuadros.py <mp4> <salida.json> [paso=1] [desde=0] [hasta=fin]
Decodifica con ffmpeg (rgb24, sin escalar) y pasa cada cuadro por RapidOCR (onnxruntime, CPU).
Guarda por cuadro: texto, puntaje y caja. Es un filtro automático: no reemplaza la revisión visual.
"""
import json, subprocess, sys
import numpy as np
from rapidocr_onnxruntime import RapidOCR

mp4, salida = sys.argv[1], sys.argv[2]
paso = int(sys.argv[3]) if len(sys.argv) > 3 else 1
desde = int(sys.argv[4]) if len(sys.argv) > 4 else 0
hasta = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 9
pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                '-of', 'json', mp4], capture_output=True, text=True).stdout)['streams'][0]
w, h = pr['width'], pr['height']
ocr = RapidOCR()
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', mp4, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
res = {}
n = 0
while True:
    buf = p.stdout.read(w * h * 3)
    if len(buf) < w * h * 3:
        break
    if desde <= n < hasta and (n - desde) % paso == 0:
        im = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        r, _ = ocr(im)
        res[n] = [dict(t=t, s=round(float(s), 3), caja=[[int(x), int(y)] for x, y in b]) for b, t, s in (r or [])]
        if n % 30 == 0:
            print(n, len(res[n]), flush=True)
    n += 1
p.wait()
json.dump(res, open(salida, 'w'), ensure_ascii=False)
print('cuadros', len(res))
