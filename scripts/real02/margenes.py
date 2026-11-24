#!/usr/bin/env python3
"""Distancia mínima (px, euclídea) entre la tinta de cada texto (contorno incluido, alfa > 0,1, con el pop) y la máscara
real de la remera y de la espuma, cuadro por cuadro. uso: venv/bin/python margenes.py mascaras.npz SALIDA.tsv"""
import sys
sys.path.insert(0, '/home/user/1/scripts/real02')
import numpy as np
from scipy import ndimage as ndi
from textos import capas
M = np.load(sys.argv[1]); filas = []
def mask(k):
    return np.unpackbits(M[k])[:1920 * 1080].reshape(1920, 1080).astype(bool) if k in M else None
import os
FIN_P6 = 259 if os.environ.get('REAL02_VER', 'v1') == 'v1_1' else 229      # v1.1: P6 hasta f258
for f in list(range(0, 94)) + list(range(184, FIN_P6)):
    rem, esp = mask(f'rem_{f}'), mask(f'esp_{f}')
    dr = ndi.distance_transform_edt(~rem) if rem is not None else None
    de = ndi.distance_transform_edt(~esp) if esp is not None else None
    for tid, im, tinta, x, y in capas(f):
        a = np.asarray(tinta) > 25
        ys, xs = np.nonzero(a); ys = ys + y; xs = xs + x
        ok = (ys >= 0) & (ys < 1920) & (xs >= 0) & (xs < 1080); ys, xs = ys[ok], xs[ok]
        mr = float(dr[ys, xs].min()) if dr is not None else float('nan')
        me = float(de[ys, xs].min()) if de is not None else float('nan')
        filas.append((f, tid, xs.min(), ys.min(), xs.max(), ys.max(), mr, me))
with open(sys.argv[2], 'w') as fh:
    fh.write('cuadro\ttexto\tx0\ty0\tx1\ty1\tdist_min_remera_px\tdist_min_espuma_px\n')
    for r in filas: fh.write('\t'.join(str(round(v, 1)) if isinstance(v, float) else str(v) for v in r) + '\n')
import collections
g = collections.defaultdict(list)
for r in filas: g[r[1]].append(r)
for tid, rs in g.items():
    mr = min(rs, key=lambda r: r[6]); me = min(rs, key=lambda r: (r[7] if r[7] == r[7] else 1e9))
    print(f'{tid}: f{rs[0][0]}-f{rs[-1][0]}  dist. mín. a la remera {mr[6]:.1f} px (f{mr[0]})  a la espuma {me[7]:.1f} px (f{me[0]})  caja máx x{min(r[2] for r in rs)}-{max(r[4] for r in rs)} y{min(r[3] for r in rs)}-{max(r[5] for r in rs)}')
