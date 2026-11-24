#!/usr/bin/env python3
"""REAL-02 v01 · máscara real de la remera (no la caja) y máscara de espuma por cuadro sobre la base 1080x1920.
Remera: píxeles claros y poco saturados -> cierre morfológico -> componente conexa que contiene la semilla -> relleno de
huecos (estampado, pliegues y sombras internas). Espuma: claros y poco saturados, fuera de la remera, debajo del horizonte.
uso: venv/bin/python mascaras.py base.rgb SALIDA.npz"""
import sys, os
import numpy as np
from scipy import ndimage as ndi

# plano: (cuadros del máster, semilla (x,y), umbral mín. canal remera, umbral saturación, horizonte y (espuma), umbral luma espuma)
PL = {'P1': (range(0, 46), (620, 1350), 135, 38, 380, 200),
      'P2': (range(46, 63), (540, 1250), 150, 40, 0, 205),
      'P3': (range(63, 94), (450, 1250), 165, 40, 0, 215),
      'P6': (range(184, 259 if os.environ.get('REAL02_VER', 'v1') == 'v1_1' else 229), (430, 1150), 160, 40, 0, 215)}  # v1.1: P6 hasta f258


def remera(a, semilla, tmin, sat):
    mx, mn = a.max(-1).astype(np.int16), a.min(-1).astype(np.int16)
    c = (mn > tmin) & ((mx - mn) < sat)
    c = ndi.binary_closing(c, structure=np.ones((3, 3)), iterations=4)
    lab, _ = ndi.label(c)
    x, y = semilla
    v = lab[y, x]
    if v == 0:  # semilla en un hueco del estampado: el componente más grande cerca
        win = lab[y - 60:y + 60, x - 60:x + 60]; vals, cnt = np.unique(win[win > 0], return_counts=True); v = vals[np.argmax(cnt)]
    m = ndi.binary_fill_holes(lab == v)
    return m


def espuma(a, m_rem, horiz, tl):
    a = a.astype(np.float32); lum = a @ np.array([.2126, .7152, .0722], np.float32); sat = a.max(-1) - a.min(-1)
    e = (lum > tl) & (sat < 40) & ~ndi.binary_dilation(m_rem, iterations=6)
    e[:horiz] = False
    return ndi.binary_opening(e, iterations=1)


if __name__ == '__main__':
    b = np.memmap(sys.argv[1], np.uint8, 'r').reshape(-1, 1920, 1080, 3)
    out = {}
    for pid, (rng, sem, tmin, sat, hz, tl) in PL.items():
        for f in rng:
            a = np.asarray(b[f]); m = remera(a, sem, tmin, sat)
            out[f'rem_{f}'] = np.packbits(m)
            if pid in ('P1', 'P2', 'P3'):
                out[f'esp_{f}'] = np.packbits(espuma(a, m, hz, tl))
        print(pid, 'ok', flush=True)
    np.savez_compressed(sys.argv[2], **out)
