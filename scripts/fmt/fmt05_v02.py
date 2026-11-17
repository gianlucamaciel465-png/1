#!/usr/bin/env python3
"""FMT-05 · «Tres movimientos de celular» · receta del máster v02 · Pedro · 17/11/2026

Corrección de Roma (04_roma_dictamen_master_v01.md): el resultado del movimiento 2 (C3, c180–c209) tiene que mostrar
«ROCCÉ» entero y nítido. C2/C3 vuelven a los tramos del guion con su regla: «si en 2,5 la R todavía toca el borde,
arrancar C3 en el primer cuadro con ROCCÉ entero y terminar C2 donde corresponda para que el corte siga en c180».
Todo lo demás es v01 sin cambios (textos, sonido, loop, versión sin música): esta receta reusa fmt05.py (v01) y solo
cambia C2, C3, las carpetas y el nombre de versión. v01 queda intacta y reproducible con fmt05.py.

Medido (etapa medir_rocce, an_v02/rocce_8004.json): en 8004 la «R» está fuera de cuadro hasta c82, entra cortada
desde c83 y queda entera desde c95 (3,167 s); la «É» toca el borde derecho desde c111 (3,700 s). «ROCCÉ» entero:
solo 8004 c95–c110 (16 cuadros, 0,53 s). Con 30 cuadros reales a velocidad 1 no se puede tener el nombre entero en
todo C3: C3 arranca en c95 (regla de Roma) y la «É» sale por la derecha en los últimos 14 cuadros (c196–c209).

C1 = 8004 0,0–1,0 (c0–c29) · C2 = 8004 1,0–3,1667 (c30–c94) a 65/30 = 2,1667× con mezcla de cuadros (contigua:
sin saltos entre C1, C2 y C3) · C3 = 8004 3,1667–4,1667 (c95–c124) a velocidad 1.

Uso:  nice -n 10 /home/user/1/TRABAJO/venv/bin/python /home/user/1/scripts/fmt/fmt05_v02.py
      [medir_rocce] [planos] [alinear] [mezclas] [masters] [control] [puntos_v02] [textos_cuadros] [extra] [copiar]
(mezclas = la misma de v01; si ya existe en TRABAJO/fmt/fmt05/mez no hace falta correrla.)
"""
import json, shutil, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
import fmt05 as B  # noqa: E402
import fmt0205_util as U  # noqa: E402
import video as V  # noqa: E402

B.VERSION = 'v02'
B.PL = B.T / 'planos_v02'
B.EVI = B.T / 'evidencia_v02'
AN2 = B.T / 'an_v02'
HOJA = B.T / '05_pedro_hoja_master_v02.md'

C3_INI = 95                       # primer cuadro de 8004 con «ROCCÉ» entero (medir_rocce lo comprueba)
VEL_C2 = (C3_INI - 30) / 30       # C2 contiguo de 8004 c30 a c94 en 30 cuadros → 2,1667×
B.PLANOS = [p if p[0] not in ('c2', 'c3') else
            (('c2', 'IMG_8004', 1.0, C3_INI / 30, {'vel': VEL_C2}) if p[0] == 'c2' else
             ('c3', 'IMG_8004', C3_INI / 30, (C3_INI + 30) / 30, {}))
            for p in B.PLANOS]


# ---------------- medición: dónde está «ROCCÉ» entero en 8004 ----------------
def letras_rocce(f):
    """Componentes oscuros con forma de letra en la franja de «ROCCÉ» (y 800–1400 del cuadro 1080×1920), de
    izquierda a derecha: [(x0, x1, y0, y1)]. Las letras son parches de denim oscuro sobre la tela blanca."""
    from scipy import ndimage as nd
    Y = f.astype(float).mean(2)[800:1400]
    m = nd.binary_opening(Y < 90, iterations=2)
    lab, n = nd.label(m)
    out = []
    for k, sl in enumerate(nd.find_objects(lab)):
        area = int((lab[sl] == k + 1).sum()); h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
        if area > 1500 and 50 < h < 300 and w < 350 and sl[0].start + 800 > 940:
            out.append((sl[1].start, sl[1].stop, sl[0].start + 800, sl[0].stop + 800))
    return sorted(out)


def rocce_entero(letras, ancho_r=(205, 225), margen=2):
    """«ROCCÉ» entero: 5 letras, la primera (R) con su ancho completo y sin tocar el borde izquierdo, y la última (É)
    sin tocar el borde derecho. Ancho de la R medido cuando está entera: 211–212 px."""
    if len(letras) < 5:
        return False
    L = letras[-5:]
    r0, r1 = L[0][0], L[0][1]
    return r0 >= margen and ancho_r[0] <= (r1 - r0) <= ancho_r[1] and L[-1][1] <= 1079 - margen


def medir_rocce():
    AN2.mkdir(parents=True, exist_ok=True)
    from PIL import Image, ImageDraw
    fr = U.leer_src('IMG_8004', 60, 135, 1080, 1920)
    filas, tiles = [], []
    for i, f in enumerate(fr):
        c = 60 + i
        L = letras_rocce(f)
        g = np.hypot(*np.gradient(f.astype(float).mean(2)[900:1300]))
        ent = rocce_entero(L)
        filas.append({'c_8004': c, 't_s': round(c / 30, 3), 'letras_x0_x1': [[a, b] for a, b, _, _ in L],
                      'rocce_entero': ent, 'nitidez_grad_p99': round(float(np.percentile(g, 99)), 1)})
        if 74 <= c <= 125:
            im = Image.fromarray(f).crop((0, 860, 1080, 1460)); d = ImageDraw.Draw(im)
            for a, b, y0, y1 in L:
                d.rectangle([a, y0 - 860, b - 1, y1 - 860], outline='lime' if ent else 'red', width=4)
            im = im.resize((270, 150)); d = ImageDraw.Draw(im)
            d.text((3, 3), f'8004 c{c} {c / 30:.3f}s {"ENTERO" if ent else ""}', fill='yellow')
            tiles.append(im)
    (AN2 / 'rocce_8004.json').write_text(json.dumps(filas, indent=0))
    cols = 8; rows = (len(tiles) + cols - 1) // cols
    lien = Image.new('RGB', (270 * cols, 150 * rows))
    for k, t in enumerate(tiles):
        lien.paste(t, (270 * (k % cols), 150 * (k // cols)))
    lien.save(AN2 / 'rocce_8004_c74-125.jpg', quality=90)
    ent = [x['c_8004'] for x in filas if x['rocce_entero']]
    print('ROCCÉ entero en 8004:', ent[0], '…', ent[-1], f'({len(ent)} cuadros)')
    assert ent[0] == C3_INI, f'el primer cuadro con ROCCÉ entero es {ent[0]}, no {C3_INI}'


# ---------------- planos ----------------
def planos():
    B.planos()
    # referencia para el control del 2,1667×: el mismo tramo saltando cuadros (setpts + fps de video.plano)
    V.plano('IMG_8004', 1.0, C3_INI / 30, B.PL / 'ref_c2_salto.mp4', vel=VEL_C2)


def alinear():
    """igual que v01, pero el resultado va a an_v02/ (no pisa la alineación de v01)."""
    an = B.AN; B.AN = AN2
    try:
        B.alinear()
    finally:
        B.AN = an


def puntos_v02():
    """Condición de Roma para v02 sobre el máster sin textos (unido) y el máster: «ROCCÉ» entero y nítido en c180–c209;
    más el 2,1667× de C2 sin tartamudeo (mezcla contra salto)."""
    unido = B.PL / 'unido.mp4'
    fr = U.leer_mp4(unido, c0=150, c1=215)
    filas = []
    for i, f in enumerate(fr):
        c = 150 + i
        L = letras_rocce(f)
        g = np.hypot(*np.gradient(f.astype(float).mean(2)[900:1300]))
        filas.append({'c_master': c, 'letras_x0_x1': [[a, b] for a, b, _, _ in L], 'rocce_entero': rocce_entero(L),
                      'nitidez_grad_p99': round(float(np.percentile(g, 99)), 1)})
    c3 = [x for x in filas if 180 <= x['c_master'] <= 209]
    ent = [x['c_master'] for x in c3 if x['rocce_entero']]
    r = {'c3_rocce_entero_cuadros': ent, 'c3_rocce_cortado_cuadros': [x['c_master'] for x in c3 if not x['rocce_entero']],
         'c3_nitidez_min_max': [min(x['nitidez_grad_p99'] for x in c3), max(x['nitidez_grad_p99'] for x in c3)],
         'por_cuadro_c150-c215': filas}

    def alterna(path, c0=None, c1=None):
        x = U.leer_mp4(path, 270, 480, c0=c0, c1=c1).astype(np.float32).mean(3)
        d = np.abs(np.diff(x, axis=0)).mean((1, 2))
        return d, float(np.abs(np.diff(d)).mean() / d.mean())
    d_m, a_m = alterna(unido, 149, 180)
    d_s, a_s = alterna(B.PL / 'ref_c2_salto.mp4')
    r['c2_vel'] = round(VEL_C2, 4)
    r['c2_diferencias_mezcla_c149-c180'] = [round(float(x), 2) for x in d_m]
    r['c2_diferencias_salto_referencia'] = [round(float(x), 2) for x in d_s]
    r['c2_indice_alternancia(media|Δd|/media d)'] = {'mezcla': round(a_m, 3), 'salto': round(a_s, 3)}
    # cuadros a tamaño real de C3 para la revisión visual
    from PIL import Image, ImageDraw
    m = U.leer_mp4(B.salidas()[0], c0=178, c1=211)
    tiles = []
    for c in (178, 179, 180, 181, 185, 190, 195, 196, 200, 205, 209, 210):
        im = Image.fromarray(m[c - 178]).crop((0, 800, 1080, 1600)).resize((360, 267)); d = ImageDraw.Draw(im)
        d.text((4, 4), f'c{c}', fill='yellow'); tiles.append(im)
    lien = Image.new('RGB', (360 * 6, 267 * 2))
    for k, t in enumerate(tiles):
        lien.paste(t, (360 * (k % 6), 267 * (k // 6)))
    lien.save(B.EVI / 'p_v02_rocce_c178-c210.jpg', quality=92)
    (B.EVI / 'puntos_v02.json').write_text(json.dumps(r, indent=1))
    print('ROCCÉ entero en C3:', ent[:1], '…', ent[-1:], len(ent), 'de 30 · nitidez', r['c3_nitidez_min_max'],
          '· alternancia C2', r['c2_indice_alternancia(media|Δd|/media d)'])


def extra():
    B.extra()
    mv = B.EVI / 'medicion_v02'; mv.mkdir(parents=True, exist_ok=True)
    for f in sorted(AN2.glob('*')):
        if f.suffix in ('.json', '.jpg', '.png'):
            shutil.copy2(f, mv / f.name)
    shutil.copy2(B.PL / 'c2.mp4.pesos.json', B.EVI / 'c2_pesos_mezcla_2.1667x.json')
    # el sonido es el de v01: se deja la huella de los WAV usados
    (B.EVI / 'mezcla' / 'wav_usados_md5.json').write_text(json.dumps(
        {f.name: U.md5_archivo(f) for f in (B.MZ / 'fmt05_completa.wav', B.MZ / 'fmt05_sinmusica.wav')}, indent=1))


def copiar():
    import fmt0205_control as C
    C.copiar_pieza(B.salidas(), B.EVI, B.DEST / f'evidencia_{B.VERSION}', extra=[HOJA])


ETAPAS = {'medir_rocce': medir_rocce, 'planos': planos, 'alinear': alinear, 'mezclas': B.mezclas,
          'masters': B.masters, 'control': B.control, 'puntos_v02': puntos_v02, 'textos_cuadros': B.textos_cuadros,
          'extra': extra, 'copiar': copiar}

if __name__ == '__main__':
    etapas = sys.argv[1:] or ['medir_rocce', 'planos', 'alinear', 'masters', 'control', 'puntos_v02',
                              'textos_cuadros', 'extra', 'copiar']
    for e in etapas:
        t0 = time.time(); ETAPAS[e](); print(f'== {e}: {time.time() - t0:.0f} s')
