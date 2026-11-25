#!/usr/bin/env python3
"""Roccé Life · hojas de control de los pines v05 (25/11/2026).

1. comparación a 180 px (miniatura del feed): v04 · v05 · sus pines (recortes de las capturas IMG_5539–5541);
2. vista a 360 px (ancho de teléfono): v05 al lado de sus pines;
3. feed simulado: grilla negra de 3 columnas a 180 px con esquinas redondeadas, los v05 mezclados con sus pines;
4. prueba de acento (no entregable): el celeste de v04 (#CDDDE5) contra el medido en su pin «GIVE HISTORY» (#B2E2FD).

Uso: python3 pines_hojas_v05.py <carpeta_salida>
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

R = Path('/home/user/1')
V04 = Path('/mnt/project-files/piezas/LIFE_rocce_life/TANDA2/PINES_v04')
V05 = R / 'TRABAJO' / 'life' / 'pines' / 'v05'
ACE = R / 'TRABAJO' / 'life' / 'pines' / 'v05_prueba_acento'
REF = R / 'TRABAJO' / 'life2' / 'ref_pines'
NOMBRES = ['ROCCE_LIFE_PIN_04_agrandado', 'ROCCE_LIFE_PIN_05_quedate_igual', 'ROCCE_LIFE_PIN_06_enero_excusas']
SUYOS = ['giveh', 'hasta', 'noestas', 'sivas', 'disciplina', 'siterindes']   # recortes de sus pines (≈ 2× de la captura)
FONT = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'


def f(tam):
    try:
        return ImageFont.truetype(FONT, tam)
    except OSError:
        return ImageFont.load_default()


def ancho(im, w):
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def redondear(im, r):
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    o = Image.new('RGB', im.size, '#000000'); o.paste(im, (0, 0), m)
    return o


def suyo(k):
    return Image.open(REF / f'{k}.png').convert('RGB')


def main(salida):
    salida = Path(salida); salida.mkdir(parents=True, exist_ok=True)
    v04 = [Image.open(V04 / f'{n}_v04.png').convert('RGB') for n in NOMBRES]
    v05 = [Image.open(V05 / f'{n}_v05.png').convert('RGB') for n in NOMBRES]

    # 1 · comparación a 180 px
    W1 = 12 + 6 * 192
    hoja = Image.new('RGB', (W1, 3 * 330 + 30), '#FFFFFF'); d = ImageDraw.Draw(hoja)
    filas = [('v04 (serif, ficha abajo a la izquierda)', v04), ('v05 (Anton, logo recortado debajo de la frase)', v05),
             ('sus pines (capturas del perfil, 25/11)', [suyo(k) for k in SUYOS])]
    for i, (rot, ims) in enumerate(filas):
        y = 10 + i * 330
        d.text((12, y), rot, fill='#111111', font=f(16))
        for j, im in enumerate(ims):
            t = ancho(im, 180)
            t = t.crop((0, 0, 180, min(t.height, 280)))
            hoja.paste(t, (12 + j * 192, y + 30))
    hoja.save(salida / 'ROCCE_LIFE_PINES_comparacion_180px_v05.png')

    # 2 · vista a 360 px: v05 + sus pines
    W2 = 16 + 6 * 376
    h2 = Image.new('RGB', (W2, 620), '#FFFFFF'); d = ImageDraw.Draw(h2)
    d.text((16, 8), 'a 360 px (ancho de teléfono): v05 · sus pines', fill='#111111', font=f(18))
    for j, im in enumerate(v05 + [suyo(k) for k in ('giveh', 'hasta', 'noestas')]):
        t = ancho(im, 360); t = t.crop((0, 0, 360, min(t.height, 540)))
        h2.paste(t, (16 + j * 376, 40))
    h2.save(salida / 'ROCCE_LIFE_PINES_vista_360px_v05.png')

    # 3 · feed simulado (fondo negro, 3 columnas de 180, esquinas de 10 px, como su perfil)
    col = [[suyo('giveh'), v05[1], suyo('noestas')], [v05[0], suyo('hasta'), suyo('siterindes')],
           [suyo('sivas'), v05[2], suyo('disciplina')]]
    feed = Image.new('RGB', (3 * 180 + 4 * 8, 900), '#000000')
    for c, ims in enumerate(col):
        y = 8
        for im in ims:
            t = redondear(ancho(im, 180), 10)
            if y + t.height > feed.height:
                t = t.crop((0, 0, 180, feed.height - y))
            feed.paste(t, (8 + c * 188, y)); y += t.height + 8
    feed.save(salida / 'ROCCE_LIFE_PINES_feed_simulado_180px_v05.png')

    # 4 · prueba de acento (no entregable)
    ace = [Image.open(ACE / f'{n}_v05.png').convert('RGB') for n in NOMBRES]
    h4 = Image.new('RGB', (12 + 6 * 192, 330), '#FFFFFF'); d = ImageDraw.Draw(h4)
    d.text((12, 6), 'acento #CDDDE5 (v04, entregado)  |  #B2E2FD (medido en su pin GIVE HISTORY) · prueba, no entregable',
           fill='#111111', font=f(14))
    for j, im in enumerate(v05 + ace):
        h4.paste(ancho(im, 180).crop((0, 0, 180, 270)), (12 + j * 192, 34))
    h4.save(salida / 'PRUEBA_acento_180px_v05.png')
    return salida


if __name__ == '__main__':
    print(main(sys.argv[1] if len(sys.argv) > 1 else V05 / '_hojas'))
