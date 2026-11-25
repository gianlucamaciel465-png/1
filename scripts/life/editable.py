#!/usr/bin/env python3
"""Roccé Life · paquete editable de los pines: HTML con rutas relativas + fondos + fuentes (OFL) + logo original.

Uso:  python3 editable.py v01 /ruta/de/salida.zip
Abrir cualquier `pin_*.html` en Chrome a 1000×1500 muestra el pin; el texto se edita en el HTML. Para exportar igual que
la entrega: `node render.js trabajos.json` (incluido) o `python3 pines.py` en el repo.
"""
import re, shutil, sys, zipfile
from pathlib import Path

R = Path('/home/user/1')
INTER = Path('/usr/share/fonts/opentype/inter/Inter-Medium.otf')
INTER_LIC = Path('/usr/share/doc/fonts-inter/copyright')


def armar(version, zip_out):
    src = R / 'TRABAJO' / 'life' / 'pines' / version
    tmp = src / '_editable'
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / 'fondos').mkdir(parents=True); (tmp / 'fuentes').mkdir(); (tmp / 'logo').mkdir()
    # v05 (estilo Anton): otra fuente y el logo recortado; los v01–v04 siguen igual que antes
    anton = "font-family:'Anton'" in (src / 'p4.html' if (src / 'p4.html').exists() else next(src.glob('p*.html'))).read_text()
    fuentes = ['Anton-Regular.ttf', 'Anton-OFL.txt'] if anton else \
        ['InstrumentSerif-Regular.ttf', 'InstrumentSerif-Italic.ttf', 'InstrumentSerif-OFL.txt']
    for f in fuentes:
        shutil.copy(R / 'scripts' / 'fuentes' / f, tmp / 'fuentes' / f)
    if not anton:
        shutil.copy(INTER, tmp / 'fuentes' / 'Inter-Medium.otf')
        shutil.copy(INTER_LIC, tmp / 'fuentes' / 'Inter-LICENCIA.txt')
    logo_arch = 'ROCCE_logo_sin_fondo.png' if anton else 'rocce_logo.png'
    shutil.copy(R / 'LOGO' / logo_arch, tmp / 'logo' / logo_arch)
    trabajos = []
    for h in sorted(src.glob('p*.html')):
        if h.stem.count('_'):          # p4_sin.html, p4_mascara.html…: controles, no van en el editable
            continue
        doc = h.read_text(encoding='utf-8')
        fondo = re.search(r"file://([^']*_fondo_[^']*\.png)", doc).group(1)
        shutil.copy(fondo, tmp / 'fondos' / Path(fondo).name)
        doc = doc.replace(f'file://{fondo}', f'fondos/{Path(fondo).name}')
        doc = doc.replace(f"file://{R}/scripts/fuentes/", 'fuentes/')
        doc = doc.replace(f'file://{R}/LOGO/{logo_arch}', f'logo/{logo_arch}')
        doc = doc.replace("@font-face{font-family:'ISI'",
                          "@font-face{font-family:'Inter';font-weight:500;src:url('fuentes/Inter-Medium.otf')}\n"
                          "@font-face{font-family:'ISI'")
        assert 'file://' not in doc, h
        (tmp / f'pin_{h.stem}.html').write_text(doc, encoding='utf-8')
        trabajos.append(dict(html=f'pin_{h.stem}.html', out=f'pin_{h.stem}.png', w=1000, h=1500))
    import json
    (tmp / 'trabajos.json').write_text(json.dumps(trabajos, indent=1))
    shutil.copy(R / 'scripts' / 'life' / 'render.js', tmp / 'render.js')
    if anton:
        leeme = ('Roccé Life · pines editables (v05: Anton + logo recortado)\n'
                 '- Cada pin_*.html es un pin de 1000×1500: abrilo en Chrome. La frase está en el <svg>: un <text> por renglón;\n'
                 '  el acento es el <tspan> con fill url(#g…c). Posiciones, degradés y sombra salen de scripts/life/pines.py\n'
                 "  (html_anton) y pines_config.py (PINES['v05']) en el repo.\n"
                 '- Fondos: recortes 2:3 de tomas reales de Roccé (ver registro_recortes_v05.json en la entrega).\n'
                 '- Fuente: Anton (licencia OFL, incluida). Logo: LOGO/ROCCE_logo_sin_fondo.png sin cambios (solo escala y posición).\n'
                 '- Para exportar PNG: node render.js trabajos.json (necesita Node + Playwright), o pines.py v05 en el repo.\n')
    else:
        leeme = ('Roccé Life · pines editables\n'
                 '- Cada pin_*.html es un pin de 1000×1500: abrilo en Chrome; la frase está en <div class="frase">.\n'
                 '- Fondos: recortes 2:3 de material real (ver registro_recortes en la entrega).\n'
                 '- Fuentes: Instrument Serif y Inter (licencia OFL, incluidas). Logo: archivo original de Roccé, sin cambios.\n'
                 '- Para exportar PNG: node render.js trabajos.json (necesita Node + Playwright), o pines.py en el repo.\n')
    (tmp / 'LEEME.txt').write_text(leeme, encoding='utf-8')
    with zipfile.ZipFile(zip_out, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(tmp.rglob('*')):
            if f.is_file():
                z.write(f, Path('ROCCE_LIFE_pines_editable_' + version) / f.relative_to(tmp))
    return tmp


if __name__ == '__main__':
    print(armar(sys.argv[1], sys.argv[2]))
