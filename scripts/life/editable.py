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
    for f in ['InstrumentSerif-Regular.ttf', 'InstrumentSerif-Italic.ttf', 'InstrumentSerif-OFL.txt']:
        shutil.copy(R / 'scripts' / 'fuentes' / f, tmp / 'fuentes' / f)
    shutil.copy(INTER, tmp / 'fuentes' / 'Inter-Medium.otf')
    shutil.copy(INTER_LIC, tmp / 'fuentes' / 'Inter-LICENCIA.txt')
    shutil.copy(R / 'LOGO' / 'rocce_logo.png', tmp / 'logo' / 'rocce_logo.png')
    trabajos = []
    for h in sorted(src.glob('p*.html')):
        doc = h.read_text(encoding='utf-8')
        fondo = re.search(r"file://([^']*_fondo_[^']*\.png)", doc).group(1)
        shutil.copy(fondo, tmp / 'fondos' / Path(fondo).name)
        doc = doc.replace(f'file://{fondo}', f'fondos/{Path(fondo).name}')
        doc = doc.replace(f"file://{R}/scripts/fuentes/", 'fuentes/')
        doc = doc.replace(f'file://{R}/LOGO/rocce_logo.png', 'logo/rocce_logo.png')
        doc = doc.replace("@font-face{font-family:'ISI'",
                          "@font-face{font-family:'Inter';font-weight:500;src:url('fuentes/Inter-Medium.otf')}\n"
                          "@font-face{font-family:'ISI'")
        assert 'file://' not in doc, h
        (tmp / f'pin_{h.stem}.html').write_text(doc, encoding='utf-8')
        trabajos.append(dict(html=f'pin_{h.stem}.html', out=f'pin_{h.stem}.png', w=1000, h=1500))
    import json
    (tmp / 'trabajos.json').write_text(json.dumps(trabajos, indent=1))
    shutil.copy(R / 'scripts' / 'life' / 'render.js', tmp / 'render.js')
    (tmp / 'LEEME.txt').write_text(
        'Roccé Life · pines editables\n'
        '- Cada pin_*.html es un pin de 1000×1500: abrilo en Chrome; la frase está en <div class="frase">.\n'
        '- Fondos: recortes 2:3 de material real (ver registro_recortes en la entrega).\n'
        '- Fuentes: Instrument Serif y Inter (licencia OFL, incluidas). Logo: archivo original de Roccé, sin cambios.\n'
        '- Para exportar PNG: node render.js trabajos.json (necesita Node + Playwright), o pines.py en el repo.\n',
        encoding='utf-8')
    with zipfile.ZipFile(zip_out, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(tmp.rglob('*')):
            if f.is_file():
                z.write(f, Path('ROCCE_LIFE_pines_editable_' + version) / f.relative_to(tmp))
    return tmp


if __name__ == '__main__':
    print(armar(sys.argv[1], sys.argv[2]))
