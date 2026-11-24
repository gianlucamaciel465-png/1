#!/usr/bin/env python3
"""Vista de la propuesta para Roma (NO está en el máster v1): «3» a 240 px en x0 860 / y0 770, sobre la roca, contra el «3»
del guion (280 px, x0 836 / y0 519) que en v1 se apoya sobre la espuma en f63-f73.
uso: venv/bin/python propuesta_t4.py base.rgb salida.rgb SALIDA.jpg"""
import sys
sys.path.insert(0, '/home/user/1/scripts/real02')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import textos, componer
W, H = 1080, 1920
b = np.memmap(sys.argv[1], np.uint8, 'r').reshape(-1, H, W, 3); s = np.memmap(sys.argv[2], np.uint8, 'r').reshape(-1, H, W, 3)
F = ImageFont.truetype('/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf', 22)
i = [t[0] for t in textos.TEXTOS].index('T4'); t = list(textos.TEXTOS[i]); t[3], t[6], t[7] = 240, 860, 770
paneles = [(f'v1 f{f} (guion)', np.asarray(s[f])) for f in (63, 70)]
textos.TEXTOS[i] = tuple(t); textos.parche.cache_clear()
paneles += [(f'propuesta f{f}', componer.cuadro(b, f)) for f in (63, 70)]
o = Image.new('RGB', (4 * 546, 990), (18, 18, 18)); d = ImageDraw.Draw(o)
for k, (r, im) in enumerate(paneles):
    o.paste(Image.fromarray(im).resize((540, 960), Image.LANCZOS), (k * 546, 30)); d.text((k * 546 + 6, 3), r, fill=(255, 230, 0), font=F)
o.save(sys.argv[3], quality=90); print(sys.argv[3])
