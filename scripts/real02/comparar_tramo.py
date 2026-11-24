#!/usr/bin/env python3
"""Compara cuadro a cuadro dos MP4 en un tramo (decodificados en yuv420p) y cada uno contra la entrada compuesta del
codificador (componer.cuadro sobre la base). Da PSNR en luma (Y) y diferencia máxima.
uso: REAL02_VER=... venv/bin/python comparar_tramo.py A.mp4 B.mp4 base.rgb DESDE HASTA SALIDA.json"""
import sys, json, subprocess
sys.path.insert(0, '/home/user/1/scripts/real02')
import numpy as np
import componer
W, H = 1080, 1920
A, B, base, f0, f1, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
n = f1 - f0 + 1


def yuv(mp4):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', mp4, '-map', '0:v', '-vf', f'trim=start_frame={f0}:end_frame={f1 + 1}',
                          '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'], capture_output=True, check=True).stdout
    assert len(raw) == n * W * H * 3 // 2, (mp4, len(raw))
    return np.frombuffer(raw, np.uint8).reshape(n, -1)[:, :W * H].reshape(n, H, W)   # solo luma


def entrada_y(b, f):
    rgb = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-i', '-', '-vf',
                          'scale=out_color_matrix=bt709:out_range=tv:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p',
                          '-f', 'rawvideo', '-'], input=componer.cuadro(b, f).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(rgb, np.uint8)[:W * H].reshape(H, W)


def psnr(x, y):
    m = np.mean((x.astype(np.float64) - y) ** 2); return 99.0 if m == 0 else round(10 * np.log10(255 ** 2 / m), 2)


ya, yb = yuv(A), yuv(B)
b = np.memmap(base, np.uint8, 'r').reshape(-1, H, W, 3)
filas = []
for k in range(n):
    e = entrada_y(b, f0 + k); d = np.abs(ya[k].astype(np.int16) - yb[k])
    filas.append({'cuadro': f0 + k, 'psnr_Y_A_vs_B': psnr(ya[k], yb[k]), 'dif_max_Y': int(d.max()), 'px_distintos_%': round(100 * (d > 0).mean(), 2),
                  'px_dif>4_%': round(100 * (d > 4).mean(), 3), 'psnr_Y_A_vs_entrada': psnr(ya[k], e), 'psnr_Y_B_vs_entrada': psnr(yb[k], e)})
json.dump(filas, open(out, 'w'), indent=1)
for r in filas: print(r)
