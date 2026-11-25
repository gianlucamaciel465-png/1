#!/usr/bin/env python3
"""Roccé Life · hojas de control de los pines v06 (25/11/2026): comparación a 180 px (v05 · v06 · sus pines) y feed
simulado (grilla negra de 3 columnas a 180 px, esquinas redondeadas) con los v06 mezclados con sus pines.
Uso: python3 pines_hojas_v06.py <carpeta_salida>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from pines_hojas_v05 import f, ancho, redondear, suyo, R

V05 = R / 'TRABAJO' / 'life' / 'pines' / 'v05'
V06 = R / 'TRABAJO' / 'life' / 'pines' / 'v06'
N05 = ['ROCCE_LIFE_PIN_04_agrandado_v05', 'ROCCE_LIFE_PIN_05_quedate_igual_v05', 'ROCCE_LIFE_PIN_06_enero_excusas_v05']
N06 = ['ROCCE_LIFE_PIN_07_nadie_lo_ve_v06', 'ROCCE_LIFE_PIN_08_cansado_v06', 'ROCCE_LIFE_PIN_09_caerse_v06']
SUYOS = ['giveh', 'hasta', 'noestas', 'sivas', 'disciplina', 'siterindes']


def main(salida):
    salida = Path(salida); salida.mkdir(parents=True, exist_ok=True)
    v05 = [Image.open(V05 / f'{n}.png').convert('RGB') for n in N05]
    v06 = [Image.open(V06 / f'{n}.png').convert('RGB') for n in N06]
    hoja = Image.new('RGB', (12 + 6 * 192, 3 * 330 + 30), '#FFFFFF'); d = ImageDraw.Draw(hoja)
    for i, (rot, ims) in enumerate([('v05 (rechazados)', v05), ('v06', v06),
                                    ('sus pines (capturas del perfil, 25/11)', [suyo(k) for k in SUYOS])]):
        y = 10 + i * 330
        d.text((12, y), rot, fill='#111111', font=f(16))
        for j, im in enumerate(ims):
            t = ancho(im, 180); t = t.crop((0, 0, 180, min(t.height, 280)))
            hoja.paste(t, (12 + j * 192, y + 30))
    hoja.save(salida / 'ROCCE_LIFE_PINES_comparacion_180px_v06.png')
    col = [[suyo('giveh'), v06[1], suyo('noestas')], [v06[0], suyo('hasta'), suyo('siterindes')],
           [suyo('sivas'), v06[2], suyo('disciplina')]]
    feed = Image.new('RGB', (3 * 180 + 4 * 8, 900), '#000000')
    for c, ims in enumerate(col):
        y = 8
        for im in ims:
            t = redondear(ancho(im, 180), 10)
            if y + t.height > 900: t = t.crop((0, 0, 180, 900 - y))
            feed.paste(t, (8 + c * 188, y)); y += t.height + 8
    feed.save(salida / 'ROCCE_LIFE_PINES_feed_simulado_180px_v06.png')


if __name__ == '__main__':
    main(sys.argv[1])
