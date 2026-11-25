# Mide el blanco de la tela: mediana de R, G, B (sRGB 8 bits) sobre una máscara de tela dentro de una caja.
# Tela = L > 160, croma < 70 y B−R entre −45 y +45 (excluye roca/piel cálida y el estampado celeste).
# Uso: medir_tela.py CARPETA x0 y0 x1 y1 [paso]   (CARPETA con NNNN.png)  ·  también se importa: medir(im, caja)
import sys, os, numpy as np, cv2
def medir(im, caja):
    x0, y0, x1, y1 = caja; z = im[y0:y1, x0:x1].reshape(-1, 3).astype(np.float32)
    b, g, r = z[:, 0], z[:, 1], z[:, 2]; L = z.mean(1); cr = z.max(1) - z.min(1)
    m = (L > 160) & (cr < 70) & (b - r > -45) & (b - r < 45)
    if m.sum() < 500: return None
    B, G, R = np.median(z[m], 0); return R, G, B, int(m.sum())
if __name__ == '__main__':
    d = sys.argv[1]; caja = tuple(map(int, sys.argv[2:6])); paso = int(sys.argv[6]) if len(sys.argv) > 6 else 1
    fs = sorted(f for f in os.listdir(d) if f.endswith('.png'))[::paso]
    for f in fs:
        v = medir(cv2.imread(f'{d}/{f}'), caja)
        print(f[:-4], 'sin tela' if v is None else f'R{v[0]:.0f} G{v[1]:.0f} B{v[2]:.0f}  B−R {v[2]-v[0]:+.0f}  px {v[3]}')
