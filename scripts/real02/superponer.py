#!/usr/bin/env python3
"""Superpone sobre un cuadro la máscara real de la remera (contorno cian), la banda de 24 px alrededor (contorno amarillo),
la espuma (relleno magenta 35 %) y la tinta de cada texto (contorno rojo).
uso: venv/bin/python superponer.py CUADROS.rgb mascaras.npz SALIDA_DIR f,f,...  [escala]"""
import sys, os
sys.path.insert(0, '/home/user/1/scripts/real02')
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
from textos import capas
W, H = 1080, 1920


def mascara(M, k):
    return np.unpackbits(M[k])[:H * W].reshape(H, W).astype(bool) if k in M else None


def tinta_en_cuadro(f, solo=None):
    """máscara booleana 1080x1920 de la tinta (contorno incluido, alfa > 25) de los textos del cuadro f."""
    a = np.zeros((H, W), bool)
    for tid, rgba, tinta, x, y in capas(f):
        if solo and tid not in solo: continue
        t = np.asarray(tinta) > 25
        y0, x0 = max(y, 0), max(x, 0); y1, x1 = min(y + t.shape[0], H), min(x + t.shape[1], W)
        a[y0:y1, x0:x1] |= t[y0 - y:y1 - y, x0 - x:x1 - x]
    return a


def borde(m, g=2): return m & ~ndi.binary_erosion(m, iterations=g)


def superponer(cuadro, f, M):
    im = cuadro.astype(np.float32).copy()
    rem, esp = mascara(M, f'rem_{f}'), mascara(M, f'esp_{f}')
    if esp is not None: im[esp] = im[esp] * 0.65 + np.array([255, 0, 255]) * 0.35
    if rem is not None:
        banda = ndi.distance_transform_edt(~rem) <= 24
        im[borde(banda)] = (255, 220, 0); im[borde(rem)] = (0, 230, 255)
    im[borde(tinta_en_cuadro(f))] = (255, 30, 30)
    return im.clip(0, 255).astype(np.uint8)


if __name__ == '__main__':
    src, M, out, fs = sys.argv[1], np.load(sys.argv[2]), sys.argv[3], [int(x) for x in sys.argv[4].split(',')]
    esc = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
    nf = os.path.getsize(src) // (W * H * 3); V = np.memmap(src, np.uint8, 'r', shape=(nf, H, W, 3))
    os.makedirs(out, exist_ok=True)
    for f in fs:
        Image.fromarray(superponer(V[f], f, M)).resize((round(W * esc), round(H * esc)), Image.LANCZOS).save(
            f'{out}/mascara_f{f:03d}.jpg', quality=90)
        print(f'{out}/mascara_f{f:03d}.jpg')
