#!/usr/bin/env python3
"""GTA6 «La misión» · tramo real después del drop (Pedro, 19/11/2026). Guion §3 planos 8–10 y §7.

  8   IMG_7887 1,90–3,67 (c57–c109, 53 cuadros): abre desde el negro de la tela, z 2,5→1,0 en 0,30 s (9 cuadros)
  9   IMG_7884 3,10–4,50 (c93–c134, 42 cuadros)
  10  IMG_4631 2,50–4,90 (c75–c146, 72 cuadros), HLG→SDR con mobius (cadena de CLAUDE.md vía video.color)
  10b IMG_7895 0,00–2,30 (c0–c68, 69 cuadros): alternativa para no repetir VIR-01

Color: «Blanca» neutra por toma contra PRODUCTO/blanca_espalda_estudio.jpg con el mapa de ganancias por zona de VIR-01 v02
(vir01_v02.MapaBlanco: solo toca neutros claros; la Negra, las rocas, la piel y el celeste quedan con peso 0). Se mide la
Negra antes/después para que no se vaya a marrón (lección de VIR-01) y, si se va, se corrige solo su croma.
Reutiliza sin modificar: fmt/video.py (color, ENC_INT), fmt/fmt03.py (plano_z, plano_n, leer), vir/vir01_v02.py.

Etapas (venv: /home/user/1/TRABAJO/venv/bin/python real.py <etapa>):
  planos → color → control
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/gta'); sys.path.insert(0, '/home/user/1/scripts/fmt'); sys.path.insert(0, '/home/user/1/scripts/vir')
from comun import T, EVID, W, H, FPS, run, guardar_json   # noqa
import video as V          # noqa: E402
import fmt03 as U          # noqa: E402

TR = T / 'real'
PROD = Path('/home/user/1/PRODUCTO')


def lin(a, b, n):
    return [a + (b - a) * k / (n - 1) for k in range(n)] if n > 1 else [a]


# ventana de z 2,5 sobre la espalda de 7887 c57 elegida por medición (etapa planos): la de 432×768 px de salida con más
# tela negra (L < 55, sat < 0,35): 67 % de tela, centro (840, 1348) de salida = (1680, 2696) de la toma 2160×3840.
CX0, CY0 = 1680, 2696
TOMAS = {
    'IMG_7887': dict(n0=57, nf=53, zs=lin(2.5, 1.0, 9) + [1.0] * 44, cxs=lin(CX0, 1080, 9) + [1080] * 44,
                     cys=lin(CY0, 1920, 9) + [1920] * 44),
    'IMG_7884': dict(n0=93, nf=42),
    'IMG_4631': dict(n0=75, nf=72),
    'IMG_7895': dict(n0=0, nf=69),
}
# cajas de la Blanca (salida 1080×1920, a z 1) para medir el mapa de ganancias; la de 7887 se lleva a cada ventana del
# acercamiento. La de la Negra, para medir que no se vaya a marrón.
CAJA_BLANCA = {'IMG_7887': (120, 760, 720, 1220), 'IMG_7884': (40, 800, 1060, 1720), 'IMG_4631': (0, 1000, 620, 1660),
               'IMG_7895': (300, 760, 720, 1060)}
CAJA_NEGRA = {'IMG_7887': (600, 930, 1080, 1500), 'IMG_7884': None, 'IMG_4631': (560, 980, 1080, 1700),
              'IMG_7895': (560, 760, 900, 1060)}


def seg(toma, sufijo=''):
    return TR / f'{toma[4:]}{sufijo}.mp4'


def etapa_planos():
    TR.mkdir(parents=True, exist_ok=True)
    rep = {}
    for toma, d in TOMAS.items():
        if 'zs' in d:
            p = U.plano_z(toma, d['n0'], d['zs'], d['cxs'], d['cys'], seg(toma, '_pre'))
        else:
            p = U.plano_n(toma, d['n0'], d['nf'], seg(toma, '_pre'))
        n = int(run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                     'stream=nb_read_frames', '-of', 'csv=p=0', str(seg(toma, '_pre'))]).decode().strip())
        assert n == d['nf'], (toma, n)
        rep[toma] = dict(n0=d['n0'], cuadros=n, fuente_s=[round(U.desde_cuadro(toma, d['n0']) + 0.0005, 4),
                                                           round(U.desde_cuadro(toma, d['n0'] + d['nf'] - 1) + 0.0005, 4)],
                         color=V.color(toma), ventanas=p.get('ventanas', [])[:10])
        print(toma, n, flush=True)
    guardar_json(rep, TR / 'planos.json')


# ------------------------------------------------------------------------------------------------ color
def leer_rgb(src):
    """todos los cuadros RGB float (BT.709 desde YUV de rango limitado, como vir01_v02.yuv_rgb)."""
    import vir01_v02 as C
    ny = W * H; nc = ny // 4
    raw = run(['ffmpeg', '-v', 'error', '-i', str(src), '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'])
    nf = len(raw) // (ny + 2 * nc)
    out = []
    for k in range(nf):
        b = raw[k * (ny + 2 * nc):(k + 1) * (ny + 2 * nc)]
        f = np.frombuffer(b, np.uint8).astype(np.float32)
        Y = f[:ny].reshape(H, W); Cb = f[ny:ny + nc].reshape(H // 2, W // 2); Cr = f[ny + nc:].reshape(H // 2, W // 2)
        out.append((Y, Cb, Cr))
    return out


def medir(rgb, caja, tipo):
    """mediana de la tela: blanca = L > 150 y sat < 0,12; negra = L < 70 y sat < 0,35 (dentro de la caja)."""
    import vir01_v02 as C
    L, sat = C.lum_sat(rgb)
    m = np.zeros(L.shape, bool); x0, y0, x1, y1 = caja; m[y0:y1, x0:x1] = True
    m &= ((L > 150) & (sat < 0.12)) if tipo == 'blanca' else ((L < 70) & (sat < 0.35) & (L > 8))
    if m.sum() < 500:
        return None
    x = np.median(np.clip(rgb[m], 0, 255), 0)
    return dict(rgb=[round(float(v), 1) for v in x], b_menos_r=round(float(x[2] - x[0]), 1),
                g_menos_r=round(float(x[1] - x[0]), 1), n=int(m.sum()))


def medir_celeste(rgb, caja):
    import vir01_v02 as C
    L, sat = C.lum_sat(rgb)
    m = np.zeros(L.shape, bool); x0, y0, x1, y1 = caja; m[y0:y1, x0:x1] = True
    m &= (rgb[..., 2] - rgb[..., 0] > 25) & (L > 90) & (sat > 0.15)
    if m.sum() < 300:
        return None
    x = np.median(rgb[m], 0)
    return dict(rgb=[round(float(v), 1) for v in x], b_sobre_r=round(float(x[2] / max(x[0], 1)), 3), n=int(m.sum()))


def producto():
    """PRODUCTO/blanca_espalda_estudio.jpg y negra_espalda_estudio.jpg (sin perfil ICC: se toman como sRGB)."""
    from PIL import Image
    import vir01_v02 as C
    out = {}
    for nom, tipo, caja in (('blanca_espalda_estudio', 'blanca', (292, 1316, 877, 1755)),
                            ('negra_espalda_estudio', 'negra', (292, 1228, 877, 1462))):
        im = Image.open(PROD / f'{nom}.jpg'); icc = 'icc_profile' in im.info
        a = np.asarray(im.convert('RGB'), np.float32)
        out[nom] = dict(icc=icc, caja=caja, tela=medir(a, caja, tipo))
    return out


def etapa_color():
    import vir01_v02 as C
    rep = dict(metodo='vir01_v02.MapaBlanco por toma (caja de la Blanca; en 7887 la caja sigue la ventana del acercamiento). '
                      'Peso 0 para L < 120 y para lo saturado: la Negra, las rocas, la piel y el celeste no se tocan.',
               producto=producto(), tomas={})
    planos = json.load(open(TR / 'planos.json'))
    for toma in TOMAS:
        src = seg(toma, '_pre'); dst = seg(toma)
        fr = leer_rgb(src)
        mb = C.MapaBlanco(CAJA_BLANCA[toma])
        ventanas = None
        if toma == 'IMG_7887':
            d = TOMAS[toma]
            # ventana de cada cuadro (misma cuenta que fmt03.plano_z) → caja de la Blanca en coordenadas de salida
            ventanas = []
            for k in range(d['nf']):
                Z = max(1.0, d['zs'][k]); w, h = 2160 / Z, 3840 / Z
                x = min(max(d['cxs'][k] - w / 2, 0), 2160 - w); y = min(max(d['cys'][k] - h / 2, 0), 3840 - h)
                ventanas.append((x, y, w, h))
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{W}x{H}',
                                '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                                '-color_trc', 'bt709', '-i', '-', *V.ENC_INT, str(dst)], stdin=subprocess.PIPE)
        filas = []
        for k, (Y, Cb, Cr) in enumerate(fr):
            rgb = C.yuv_rgb(Y, Cb, Cr)
            caja = CAJA_BLANCA[toma]
            if ventanas:
                x, y, w, h = ventanas[k]
                sx = 1080 / w; x0, y0, x1, y1 = caja
                # caja definida a z 1 (salida = toma/2) → coordenadas de la toma → ventana → salida
                X0, Y0, X1, Y1 = [v * 2 for v in caja]
                cb = (int(max(0, (X0 - x) * sx)), int(max(0, (Y0 - y) * sx)), int(min(1080, (X1 - x) * sx)), int(min(1920, (Y1 - y) * sx)))
                mb.box = np.zeros((H, W), bool)
                if cb[2] > cb[0] and cb[3] > cb[1]:
                    mb.box[cb[1]:cb[3], cb[0]:cb[2]] = True
                caja = cb
            rgb2, w_, g = mb(rgb)
            Y2, Cb2, Cr2 = C.rgb_yuv(rgb2)
            if k in (0, len(fr) // 2, len(fr) - 1) or k % 10 == 0:
                cajan = CAJA_NEGRA[toma]
                filas.append(dict(cuadro=k, blanca_antes=medir(rgb, caja, 'blanca') if caja[2] > caja[0] else None,
                                  blanca_despues=medir(rgb2, caja, 'blanca') if caja[2] > caja[0] else None,
                                  celeste_antes=medir_celeste(rgb, caja) if caja[2] > caja[0] else None,
                                  celeste_despues=medir_celeste(rgb2, caja) if caja[2] > caja[0] else None,
                                  negra_antes=medir(rgb, cajan, 'negra') if cajan and k >= 9 else None,
                                  negra_despues=medir(rgb2, cajan, 'negra') if cajan and k >= 9 else None,
                                  pct_tocado=round(float((w_ > 0.01).mean() * 100), 1)))
            enc.stdin.write(np.concatenate([Y2.ravel(), Cb2.ravel(), Cr2.ravel()]).round().clip(0, 255).astype(np.uint8).tobytes())
        enc.stdin.close(); enc.wait()
        rep['tomas'][toma] = dict(caja_blanca=CAJA_BLANCA[toma], caja_negra=CAJA_NEGRA[toma], medidas=filas)
        print(toma, json.dumps([(f['cuadro'], (f['blanca_antes'] or {}).get('b_menos_r'), (f['blanca_despues'] or {}).get('b_menos_r'),
                                 (f['blanca_antes'] or {}).get('g_menos_r'), (f['blanca_despues'] or {}).get('g_menos_r'),
                                 (f['negra_antes'] or {}).get('b_menos_r'), (f['negra_despues'] or {}).get('b_menos_r'),
                                 (f['negra_antes'] or {}).get('g_menos_r')) for f in filas]), flush=True)
    guardar_json(rep, TR / 'color.json')
    negro()


def negro():
    """negro medido de la espalda de 7887 a z 2,5: media del primer cuadro del plano (el que se ve en D)."""
    import vir01_v02 as C
    Y, Cb, Cr = leer_rgb(seg('IMG_7887'))[0]
    rgb = np.clip(C.yuv_rgb(Y, Cb, Cr), 0, 255)
    L, sat = C.lum_sat(rgb)
    tela = (L < 55) & (sat < 0.35)
    m = rgb.reshape(-1, 3).mean(0)
    rep = dict(fuente='IMG_7887 c57 a z 2,5 (ventana 864×1536 de la toma, centro (1680, 2696)) = primer cuadro del drop',
               media_recorte_rgb=[round(float(v), 2) for v in m], media_recorte_hex='#%02X%02X%02X' % tuple(int(round(v)) for v in m),
               media_solo_tela_rgb=[round(float(v), 2) for v in rgb[tela].mean(0)], fraccion_tela=round(float(tela.mean()), 3))
    guardar_json(rep, T / 'negro_7887.json')
    print(rep)


if __name__ == '__main__':
    {'planos': etapa_planos, 'color': etapa_color, 'negro': negro}[sys.argv[1]]()
