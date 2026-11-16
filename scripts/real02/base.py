#!/usr/bin/env python3
"""REAL-02 v01 · imagen base sin textos: 307 cuadros 1080x1920 RGB24 (raw) según el guion G1 de Fede (§3).
Cada plano se recorta por índice de cuadro (trim=start_frame), HDR→SDR con la cadena del CLAUDE.md (mobius),
conversión a RGB 16 bits y ganancias R/G/B en coma flotante antes de cuantizar a 8 bits.
uso: base.py SALIDA.rgb SALIDA_info.json"""
import sys, io, json, subprocess, hashlib
import numpy as np
from PIL import Image, ImageCms, ImageFilter, ImageEnhance

O = '/home/user/1/ORIGINALES'
FOTO = '/mnt/project-files/piezas/BOC-01_ultimo_minuto/material/rc-blanca-placas.jpg'
W, H = 1080, 1920
TM = "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
# Ganancias medidas el 16/11 sobre la tela real (componente conexa, 30 % más claro) hacia la tela lisa de
# PRODUCTO/blanca_espalda_estudio.jpg (1 : 1,009 : 1,018). Sustituyen las del inventario (máscara con saturación < 30 que
# excluía la tela azulada de 4641): ver TRABAJO/real02/v01/ganancias_v01_medidas.json.
PLANOS = [  # id, toma, cuadro inicial, cuadros, HDR, ganancias R/G/B, recorte (x,y,w,h) en la salida natural o None
    ('P1', 'IMG_4641', 18, 46, True, (1.035, 1.004, 0.878), (50, 0, 1012, 1800)),
    ('P2', 'IMG_7884', 105, 17, False, None, None),
    ('P3', 'IMG_4627', 333, 31, True, (0.997, 1.005, 0.965), None),
    ('P4', 'IMG_3375', 11, 30, True, (0.910, 1.017, 1.139), None),
    ('P5', 'IMG_7857', 60, 60, False, (1.029, 0.996, 0.960), None),
    ('P6', 'IMG_4625', 15, 45, True, (0.988, 1.006, 0.975), None),
]
N_P7 = 78


def plano(toma, c0, n, hdr, recorte):
    vf = f"trim=start_frame={c0}:end_frame={c0 + n},setpts=PTS-STARTPTS"
    if hdr:
        vf += "," + TM
    vf += ",scale=in_color_matrix=bt709:in_range=tv:flags=lanczos,format=rgb48le"
    if recorte:
        x, y, w, h = recorte
        vf += f",crop={w}:{h}:{x}:{y}"
    vf += f",scale={W}:{H}:flags=lanczos"
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{O}/{toma}.mov', '-vf', vf, '-fps_mode', 'passthrough',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb48le', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint16).reshape(-1, H, W, 3)
    assert len(a) == n, (toma, len(a), n)
    return a


def a8(a16, g):
    x = a16.astype(np.float32) * (255.0 / 65535.0)
    if g:
        x *= np.array(g, np.float32)
    return np.clip(np.rint(x), 0, 255).astype(np.uint8)


def foto_p7():
    im = Image.open(FOTO)
    icc = im.info.get('icc_profile')
    if icc:
        im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), outputMode='RGB')
    im = im.convert('RGB')
    # fondo: la misma foto cubriendo 1080x1920, desenfoque gaussiano sigma 40, brillo -30 %
    k = max(W / im.width, H / im.height)
    bg = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x0, y0 = (bg.width - W) // 2, (bg.height - H) // 2
    bg = bg.crop((x0, y0, x0 + W, y0 + H)).filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.70)
    fg = im.resize((1080, 1350), Image.LANCZOS)
    bg.paste(fg, (0, 380))
    return np.asarray(bg, np.uint8), im.size


if __name__ == '__main__':
    out, info_path = sys.argv[1], sys.argv[2]
    info = {'planos': []}
    f0 = 0
    with open(out, 'wb') as fh:
        for pid, toma, c0, n, hdr, g, rec in PLANOS:
            a = a8(plano(toma, c0, n, hdr, rec), g)
            fh.write(a.tobytes())
            info['planos'].append(dict(plano=pid, toma=toma, cuadros_fuente=[c0, c0 + n - 1], master=[f0, f0 + n - 1], hdr=hdr,
                                       ganancias=g, recorte=rec, md5_base=hashlib.md5(a.tobytes()).hexdigest()))
            print(pid, toma, f'c{c0}-c{c0 + n - 1} -> f{f0}-f{f0 + n - 1}', flush=True)
            f0 += n
        img, tam = foto_p7()
        for _ in range(N_P7):
            fh.write(img.tobytes())
        info['planos'].append(dict(plano='P7', toma='rc-blanca-placas.jpg (ficha Shopify)', tam_original=tam, master=[f0, f0 + N_P7 - 1],
                                   fondo='cubre 1080x1920, desenfoque sigma 40, brillo -30 %', frente='1080x1350 en x 0, y 380-1730'))
        f0 += N_P7
    assert f0 == 307
    info['cuadros'] = f0
    json.dump(info, open(info_path, 'w'), indent=1, ensure_ascii=False)
    print('cuadros', f0)
