"""Pin v06 P7: saca los cuernos rojos del gorro (disfraz) de la foto de Burst «hooded-figure-sits-on-city-street-hill».
Licencia Burst: se permite modificar. Máscara = rojo oscuro (G < 0,52·R) en dos cajas; fuera del domo del gorro se
rellena con asfalto corrido en horizontal (y corrección de nivel local); dentro, con tela del mismo borde rotada hacia
abajo alrededor del centro del domo. Borde del domo con 1 px de transición."""
import sys
import numpy as np
from PIL import Image, ImageFilter

src, out = sys.argv[1], sys.argv[2]
im = Image.open(src)
icc = im.info.get('icc_profile')
a = np.asarray(im.convert('RGB')).astype(float)
R, G = a[..., 0], a[..., 1]
m = np.zeros(R.shape, bool)
CAJAS = [(1700, 4230, 1830, 4330, -1), (1930, 4220, 2060, 4320, +1)]   # x0, y0, x1, y1, lado
for x0, y0, x1, y1, _ in CAJAS:
    m[y0:y1, x0:x1] |= G[y0:y1, x0:x1] < 0.52 * R[y0:y1, x0:x1] + 3
mi = Image.fromarray((m * 255).astype('uint8')).filter(ImageFilter.MaxFilter(7))   # +3 px: el borde suavizado
m = np.asarray(mi) > 0
CX, CY, RAD = 1871.0, 4357.0, 133.0
yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
o = a.copy()
for x0, y0, x1, y1, lado in CAJAS:
    X0, Y0, X1, Y1 = x0 - 8, y0 - 8, x1 + 8, y1 + 8
    sm = m[Y0:Y1, X0:X1]
    ys, xs = np.where(sm); ys = ys + Y0; xs = xs + X0
    d = np.hypot(xs - CX, ys - CY)
    # asfalto: corrido 150 px hacia afuera, nivelado con el anillo conocido alrededor de la máscara
    sx = xs + lado * 150
    asf = a[ys, sx]
    anillo = np.asarray(Image.fromarray((sm * 255).astype('uint8')).filter(ImageFilter.MaxFilter(15))) > 0
    anillo &= ~sm
    ry, rx = np.where(anillo); ry += Y0; rx += X0
    fuera = np.hypot(rx - CX, ry - CY) > RAD + 4
    corr = a[ry[fuera], rx[fuera]].mean(0) - a[ry[fuera], rx[fuera] + lado * 150].mean(0)
    asf = asf + corr
    # tela: relleno armónico (Laplace) desde la tela conocida del domo + grano de la tela del mismo radio rotada 32° hacia abajo
    ang = np.arctan2(ys - CY, xs - CX) + np.deg2rad(32 if lado < 0 else -32)
    tx = np.clip(np.round(CX + d * np.cos(ang)).astype(int), 0, a.shape[1] - 1)
    ty = np.clip(np.round(CY + d * np.sin(ang)).astype(int), 0, a.shape[0] - 1)
    bl = np.asarray(Image.fromarray(a.astype('uint8')).filter(ImageFilter.GaussianBlur(4))).astype(float)
    grano = a[ty, tx] - bl[ty, tx]
    reg = a[Y0:Y1, X0:X1].copy()
    dreg = np.hypot(xx[Y0:Y1, X0:X1] - CX, yy[Y0:Y1, X0:X1] - CY)
    dentro = dreg < RAD + 0.5
    U = sm & dentro
    K = dentro & ~sm
    reg[U] = reg[K].mean(0)
    for _ in range(3000):
        acc = np.zeros_like(reg); n = np.zeros(reg.shape[:2])
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sh = np.roll(np.roll(reg, dy, 0), dx, 1); dn = np.roll(np.roll(dentro, dy, 0), dx, 1)
            acc += sh * dn[..., None]; n += dn
        nuevo = acc / np.maximum(n, 1)[..., None]
        reg[U] = nuevo[U]
    tela = reg[ys - Y0, xs - X0] + grano
    al = np.clip(RAD - d + 0.5, 0, 1)[:, None]
    o[ys, xs] = al * tela + (1 - al) * asf
Image.fromarray(np.clip(o.round(), 0, 255).astype('uint8')).save(out, quality=97, icc_profile=icc)
print('px retocados', int(m.sum()))
