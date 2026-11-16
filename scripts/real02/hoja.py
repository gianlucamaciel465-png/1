#!/usr/bin/env python3
"""Hoja de cuadros de un raw 1080x1920 RGB24 con grilla cada 100 px (etiquetas en px del máster).
uso: hoja.py ENTRADA.rgb SALIDA.jpg 'f0,f20,...' [escala=0.3] [cols=6]"""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
src, out, fs = sys.argv[1:4]; esc = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3; cols = int(sys.argv[5]) if len(sys.argv) > 5 else 6
b = np.memmap(src, np.uint8, 'r').reshape(-1, 1920, 1080, 3)
F = ImageFont.truetype('/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf', 13)
fr = [int(x) for x in fs.split(',')]
w, h = int(1080 * esc), int(1920 * esc)
o = Image.new('RGB', (cols * (w + 4), ((len(fr) + cols - 1) // cols) * (h + 20)), (20, 20, 20)); d = ImageDraw.Draw(o)
for k, f in enumerate(fr):
    im = Image.fromarray(np.asarray(b[f])).resize((w, h), Image.LANCZOS); dd = ImageDraw.Draw(im)
    for y in range(100, 1920, 100):
        yy = int(y * esc); dd.line([(0, yy), (6 if y % 500 else 14, yy)], fill=(255, 0, 0)); dd.text((8, yy - 7), str(y), fill=(255, 70, 70), font=F) if y % 200 == 0 else None
    for x in range(100, 1080, 100):
        xx = int(x * esc); dd.line([(xx, h - 6), (xx, h)], fill=(255, 0, 0)); dd.text((xx + 1, h - 20), str(x), fill=(255, 70, 70), font=F) if x % 200 == 0 else None
    x0 = (k % cols) * (w + 4); y0 = (k // cols) * (h + 20)
    o.paste(im, (x0, y0 + 18)); d.text((x0 + 2, y0 + 2), f'f{f}', fill=(255, 230, 0), font=F)
o.save(out, quality=88); print(out, o.size)
