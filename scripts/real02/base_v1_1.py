#!/usr/bin/env python3
"""REAL-02 v1.1 · imagen base sin textos (dictamen de Roma 08, cambio 2). 307 cuadros 1080x1920 RGB24.
f0–f183: P1–P5 exactamente como v1 (mismas funciones y parámetros de base.py).
P6 f184–f258: IMG_4625 c15–c89 (75 cuadros, antes c15–c59), tonemap + las mismas ganancias de v1.
P7 f259–f306: foto de la ficha con acercamiento continuo ×1,00 → ×1,06 (48 cuadros) alrededor del centro de la foto
(540, 1055); a ×1,00 ocupa 1080×1350 en y 380–1730, como en v1. Fondo: azul noche liso medido en la propia foto
(mediana de la franja superior, filas 0–40), sin desenfoque; la foto entra con borde suave (30 px de la foto ≈ 40 px del
máster) arriba y abajo.
uso: base_v1_1.py SALIDA.rgb SALIDA_info.json [BASE_V1.rgb BASE_V1_info.json]
     con la base de v1, copia f0–f183 de ella y comprueba el md5 de cada plano contra su info; si no, los rehace."""
import sys, io, json, hashlib
import numpy as np
from PIL import Image, ImageCms
sys.path.insert(0, '/home/user/1/scripts/real02')
from base import plano, a8, PLANOS, FOTO, W, H

P6 = ('P6', 'IMG_4625', 15, 75, True, (0.988, 1.006, 0.975), None)
N_P7, ZOOM, CX, CY, ESC0, BORDE = 48, 0.06, 540.0, 1055.0, 1.35, 30


def foto_srgb():
    im = Image.open(FOTO)
    icc = im.info.get('icc_profile')
    if icc:
        im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), outputMode='RGB')
    return im.convert('RGB')


def p7():
    im = foto_srgb(); w, h = im.size
    a = np.asarray(im, np.float32)
    azul = tuple(int(v) for v in np.median(a[0:40].reshape(-1, 3), 0))          # azul noche de la franja superior de la foto
    v = np.arange(h, dtype=np.float32)
    r = np.clip(np.minimum(v, h - 1 - v) / BORDE, 0, 1); r = r * r * (3 - 2 * r)    # borde suave arriba y abajo
    alfa = Image.fromarray(np.repeat((r * 255)[:, None], w, 1).astype(np.uint8), 'L')
    fondo = np.empty((H, W, 3), np.float32); fondo[:] = azul
    cuadros = []
    for k in range(N_P7):
        s = ESC0 * (1 + ZOOM * k / (N_P7 - 1))                                       # px del máster por px de la foto
        data = (1 / s, 0, w / 2 - CX / s, 0, 1 / s, h / 2 - CY / s)
        rgb = np.asarray(im.transform((W, H), Image.AFFINE, data, resample=Image.BICUBIC, fillcolor=azul), np.float32)
        al = np.asarray(alfa.transform((W, H), Image.AFFINE, data, resample=Image.BICUBIC, fillcolor=0), np.float32)[..., None] / 255
        cuadros.append(np.clip(np.rint(fondo * (1 - al) + rgb * al), 0, 255).astype(np.uint8))
    return cuadros, azul, (w, h)


if __name__ == '__main__':
    out, info_path = sys.argv[1], sys.argv[2]
    v1 = sys.argv[3] if len(sys.argv) > 3 else None
    info = {'version': 'v1.1', 'planos': []}
    f0 = 0
    with open(out, 'wb') as fh:
        if v1:
            ref = {p['plano']: p for p in json.load(open(sys.argv[4]))['planos']}
            b = np.memmap(v1, np.uint8, 'r').reshape(-1, H, W, 3)
        for pid, toma, c0, n, hdr, g, rec in PLANOS[:5] + [P6]:
            if v1 and pid != 'P6':
                a = np.asarray(b[f0:f0 + n])
                assert hashlib.md5(a.tobytes()).hexdigest() == ref[pid]['md5_base'], pid
            else:
                a = a8(plano(toma, c0, n, hdr, rec), g)
            fh.write(a.tobytes())
            info['planos'].append(dict(plano=pid, toma=toma, cuadros_fuente=[c0, c0 + n - 1], master=[f0, f0 + n - 1], hdr=hdr,
                                       ganancias=g, recorte=rec, md5_base=hashlib.md5(a.tobytes()).hexdigest()))
            print(pid, toma, f'c{c0}-c{c0 + n - 1} -> f{f0}-f{f0 + n - 1}', flush=True)
            f0 += n
        cuadros, azul, tam = p7()
        for c in cuadros:
            fh.write(c.tobytes())
        info['planos'].append(dict(plano='P7', toma='rc-blanca-placas.jpg (ficha Shopify)', tam_original=tam, master=[f0, f0 + N_P7 - 1],
                                   fondo=f'azul noche liso {azul} (mediana de las filas 0-40 de la foto), sin desenfoque',
                                   frente=f'acercamiento continuo x1,00 -> x{1 + ZOOM:.2f} alrededor de ({CX:.0f}, {CY:.0f}); a x1,00 1080x1350 en y 380-1730; borde suave {BORDE} px de la foto arriba y abajo',
                                   md5_base=hashlib.md5(b''.join(c.tobytes() for c in cuadros)).hexdigest()))
        f0 += N_P7
    assert f0 == 307
    info['cuadros'] = f0
    json.dump(info, open(info_path, 'w'), indent=1, ensure_ascii=False)
    print('cuadros', f0, 'azul', azul)
