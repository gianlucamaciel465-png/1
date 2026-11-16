#!/usr/bin/env python3
"""REAL-02 v01 · composición: base + degradé superior (P1, P3, P6) + textos -> H.264 1080x1920 30 fps.
uso: componer.py base.rgb SALIDA_video.mp4 [DESDE HASTA]  (codifica los 307 cuadros o ese tramo, sin audio)
     componer.py base.rgb --md5 SALIDA.txt             (md5 de cada cuadro compuesto)
     componer.py base.rgb --vista DIR f0,f39,...       (PNG de control de esos cuadros)"""
import sys, os, subprocess
sys.path.insert(0, '/home/user/1/scripts/real02')
import numpy as np
from PIL import Image
from textos import capas

W, H = 1080, 1920
# degradé negro vertical: 0 % en y 40, 30 % en y 200, 0 % en y 400 (guion §5)
y = np.arange(H, dtype=np.float32)
DEG = np.interp(y, [0, 40, 200, 400, H], [0, 0, 0.30, 0, 0]).astype(np.float32)[:, None, None]
FIN_P6 = 259 if os.environ.get('REAL02_VER', 'v1') == 'v1_1' else 229      # v1.1: P6 llega a f258
CON_DEG = set(range(0, 46)) | set(range(63, 94)) | set(range(184, FIN_P6))


def cuadro(b, f):
    im = np.asarray(b[f]).astype(np.float32)
    if f in CON_DEG:
        im = im * (1 - DEG)
    out = Image.fromarray(np.clip(np.rint(im), 0, 255).astype(np.uint8))
    for tid, rgba, tinta, x, yy in capas(f):
        out.alpha_composite(rgba, (x, yy)) if out.mode == 'RGBA' else None
        if out.mode != 'RGBA':
            o = out.convert('RGBA'); o.alpha_composite(rgba, (x, yy)); out = o.convert('RGB')
    return np.asarray(out.convert('RGB'))


if __name__ == '__main__':
    b = np.memmap(sys.argv[1], np.uint8, 'r').reshape(-1, H, W, 3)
    if sys.argv[2] == '--vista':
        os.makedirs(sys.argv[3], exist_ok=True)
        for f in map(int, sys.argv[4].split(',')):
            Image.fromarray(cuadro(b, f)).save(f'{sys.argv[3]}/f{f:03d}.png')
        sys.exit()
    if sys.argv[2] == '--md5':                       # md5 de cada cuadro compuesto (entrada del codificador)
        import hashlib
        with open(sys.argv[3], 'w') as fh:
            for f in range(len(b)):
                fh.write(f'{f}\t{hashlib.md5(cuadro(b, f).tobytes()).hexdigest()}\n')
        sys.exit()
    # opcional: DESDE HASTA (inclusive) codifica solo ese tramo, como GOP cerrado propio (v1.1 empalma tramos nuevos con los de v1)
    f_a, f_b = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, len(b) - 1)
    enc = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
           '-vf', 'scale=out_color_matrix=bt709:out_range=tv:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-profile:v', 'high', '-level:v', '4.0', '-maxrate', '20M',
           '-bufsize', '25M', '-g', '60', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709',
           '-color_trc', 'bt709', '-color_range', 'tv', '-movflags', '+faststart', sys.argv[2]]
    p = subprocess.Popen(enc, stdin=subprocess.PIPE)
    for f in range(f_a, f_b + 1):
        p.stdin.write(cuadro(b, f).tobytes())
    p.stdin.close(); assert p.wait() == 0
    print('video', sys.argv[2], f'f{f_a}-f{f_b}', f_b - f_a + 1, 'cuadros')
