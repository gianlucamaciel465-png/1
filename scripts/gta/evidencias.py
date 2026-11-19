#!/usr/bin/env python3
"""GTA6 «La misión» · hojas de evidencia complementarias (Pedro, 19/11/2026).

  python evidencias.py color   → TRABAJO/gta/evidencia/hoja_color_tramo_real.jpg
      por toma (7887, 7884, 4631, 7895): cuadro ANTES (real/*_pre.mp4, solo HLG→SDR o tal cual) | DESPUÉS (real/*.mp4,
      Blanca neutralizada) + recortes de PRODUCTO (blanca/negra espalda estudio) y la medida B−R de cada caja (color.json).
  python evidencias.py mapa    → TRABAJO/gta/evidencia/hoja_mapa_A.jpg
      cuadros 450–480 de la animática A (transición de mapa y picada al negro medido de 7887).
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).parent))
from comun import T, FPS
from animatica import cuadros_rgb, hoja

E = T / 'evidencia'
TR = T / 'real'
FNT = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'


def _rot(d, xy, txt, px=16, fill=(255, 220, 80)):
    d.text(xy, txt, font=ImageFont.truetype(FNT, px), fill=fill)


def hoja_color():
    col = json.loads((TR / 'color.json').read_text())
    tomas = [('IMG_7887', '7887', 30), ('IMG_7884', '7884', 21), ('IMG_4631', '4631', 36), ('IMG_7895', '7895', 34)]
    A = 300; Hh = round(A * 1920 / 1080)
    filas = []
    for nom, cod, n in tomas:
        pre = cuadros_rgb(TR / f'{cod}_pre.mp4', [n], A)[n]
        pos = cuadros_rgb(TR / f'{cod}.mp4', [n], A)[n]
        med = next((m for m in col['tomas'][nom]['medidas'] if m['cuadro'] == n), None)
        fila = Image.new('RGB', (2 * A + 330, Hh + 30), (20, 20, 20))
        fila.paste(Image.fromarray(pre), (0, 30)); fila.paste(Image.fromarray(pos), (A + 4, 30))
        d = ImageDraw.Draw(fila)
        _rot(d, (4, 6), f'{nom} c{n} ANTES'); _rot(d, (A + 8, 6), 'DESPUÉS (Blanca neutralizada)')
        cb = col['tomas'][nom]['caja_blanca']; cn = col['tomas'][nom]['caja_negra']
        k = A / 1080
        for caja, c in ((cb, (255, 255, 255)), (cn, (126, 178, 222))):
            if caja:
                for x0 in (0, A + 4):
                    d.rectangle([x0 + caja[0] * k, 30 + caja[1] * k, x0 + caja[2] * k, 30 + caja[3] * k], outline=c, width=1)
        y = 40
        if med:
            for et, clave in (('Blanca antes', 'blanca_antes'), ('Blanca después', 'blanca_despues'),
                              ('Negra antes', 'negra_antes'), ('Negra después', 'negra_despues')):
                v = med.get(clave)
                if v:
                    _rot(d, (2 * A + 14, y), et, 15, (230, 230, 230)); y += 19
                    _rot(d, (2 * A + 14, y), f"RGB {v['rgb'][0]:.0f}/{v['rgb'][1]:.0f}/{v['rgb'][2]:.0f}", 14, (200, 200, 200)); y += 18
                    _rot(d, (2 * A + 14, y), f"B−R {v['b_menos_r']:+.1f}  G−R {v['g_menos_r']:+.1f}", 14, (200, 200, 200)); y += 26
            _rot(d, (2 * A + 14, y), f"zona tocada {med['pct_tocado']} %", 14, (200, 200, 200)); y += 26
        _rot(d, (2 * A + 14, y), 'caja blanca = medida Blanca', 13, (255, 255, 255)); y += 18
        _rot(d, (2 * A + 14, y), 'caja celeste = medida Negra', 13, (126, 178, 222))
        filas.append(fila)
    # referencia de estudio
    ref = Image.new('RGB', (2 * A + 330, Hh + 30), (20, 20, 20))
    d = ImageDraw.Draw(ref)
    x = 0
    for clave, archivo in (('blanca_espalda_estudio', 'blanca_espalda_estudio.jpg'), ('negra_espalda_estudio', 'negra_espalda_estudio.jpg')):
        im = ImageOps.exif_transpose(Image.open(f'/home/user/1/PRODUCTO/{archivo}'))
        if 'icc_profile' in im.info:
            from PIL import ImageCms
            import io
            src = ImageCms.ImageCmsProfile(io.BytesIO(im.info['icc_profile']))
            im = ImageCms.profileToProfile(im, src, ImageCms.createProfile('sRGB'), outputMode='RGB')
        im = im.convert('RGB'); im.thumbnail((A, Hh))
        ref.paste(im, (x, 30)); _rot(d, (x + 4, 6), f'PRODUCTO/{archivo}', 13)
        t = col['producto'][clave]['tela']
        _rot(d, (x + 4, 30 + im.height + 6), f"tela RGB {t['rgb'][0]:.0f}/{t['rgb'][1]:.0f}/{t['rgb'][2]:.0f} · B−R {t['b_menos_r']:+.0f}", 13, (230, 230, 230))
        x += A + 4
    _rot(d, (2 * A + 14, 40), 'Referencia de estudio', 15, (230, 230, 230))
    _rot(d, (2 * A + 14, 62), '(sRGB desde su ICC)', 13, (200, 200, 200))
    filas.append(ref)
    hoja_ = Image.new('RGB', (filas[0].width * 2 + 8, (Hh + 34) * 3), (10, 10, 10))
    for i, f in enumerate(filas):
        hoja_.paste(f, ((i % 2) * (f.width + 8), (i // 2) * (Hh + 34)))
    sal = E / 'hoja_color_tramo_real.jpg'
    hoja_.save(sal, quality=88)
    print(sal, hoja_.size)


def hoja_mapa():
    mp4 = T / 'ROCCE_GTA6_animatica_v00.mp4'
    ns = [450, 452, 454, 456, 458, 459, 461, 463, 465, 467, 469, 470, 471, 472, 474, 476, 477, 478, 479, 480]
    print(hoja(mp4, ns, E / 'hoja_mapa_A.jpg', 216, 10))


def hoja_cambios():
    """v01: antes (v00) | después (v01) de las correcciones 1–3 de 03_roma_revision_pre_v00.md."""
    v0 = T / 'ROCCE_GTA6_animatica_v00.mp4'; v1 = T / 'ROCCE_GTA6_animatica_v01.mp4'
    fnt = ImageFont.truetype(FNT, 22)

    def rot(im, t):
        im = Image.fromarray(im) if not isinstance(im, Image.Image) else im
        out = Image.new('RGB', (im.width, im.height + 32), (20, 20, 20)); out.paste(im, (0, 32))
        ImageDraw.Draw(out).text((6, 5), t, font=fnt, fill=(255, 220, 80)); return out

    filas = []
    # 1 · «INSPIRADO EN EL DROP» (c420 = 14,00 s), recorte 1:1 de y 340–660
    a0 = cuadros_rgb(v0, [420])[420][340:660]; a1 = cuadros_rgb(v1, [420])[420][340:660]
    filas.append([rot(a0, 'v00 · c420 · etiqueta Saira 44 · caja 548 px'), rot(a1, 'v01 · c420 · Saira 62 (×1,41) · caja 768 px ≤ frase 814')])
    # 2 · a 360 px de ancho (lectura en teléfono)
    b0 = cuadros_rgb(v0, [420], 360)[420]; b1 = cuadros_rgb(v1, [420], 360)[420]
    filas.append([rot(b0, 'v00 a 360 px'), rot(b1, 'v01 a 360 px')])
    # 3 · puente c478 | c479 | c480
    ns = [478, 479, 480]
    c0 = cuadros_rgb(v0, ns, 216); c1 = cuadros_rgb(v1, ns, 216)
    tira = lambda c: np.concatenate([c[n] for n in ns], 1)
    filas.append([rot(tira(c0), 'v00 · c478 c479 c480 · puente #322D2B (con roca)'),
                  rot(tira(c1), 'v01 · c478 c479 c480 · puente = tela sola')])
    # 4 · 4631 c36 (tramo real): Negra antes/después del croma de oscuros
    d0 = cuadros_rgb(TR / '4631_v00.mp4', [36])[36][900:1800]; d1 = cuadros_rgb(TR / '4631.mp4', [36])[36][900:1800]
    filas.append([rot(d0, 'v00 · 4631 c36 · Negra B−R +17,1'), rot(d1, 'v01 · 4631 c36 · Negra B−R +2,5 · R−G −0,8')])
    ancho = 2 * 1080 + 12
    alto = sum(max(r[0].height, r[1].height) + 12 for r in filas)
    out = Image.new('RGB', (ancho, alto), (10, 10, 10)); y = 0
    for r in filas:
        x = 0
        for t in r:
            out.paste(t, (x, y)); x += 1080 + 12
        y += max(r[0].height, r[1].height) + 12
    sal = E / 'hoja_cambios_v01.jpg'; out.save(sal, quality=88); print(sal, out.size)


if __name__ == '__main__':
    {'color': hoja_color, 'mapa': hoja_mapa, 'cambios': hoja_cambios}[sys.argv[1]]()
