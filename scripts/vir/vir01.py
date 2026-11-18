#!/usr/bin/env python3
"""VIR-01 «A nada» · receta del máster v01 (Pedro, 18/11/2026).

Guion: piezas/VIR_marcas_nuevas_virales/VIR-01_a_nada/01_fede_guion_G1.md (G1 v1) + 02_roma_aprobacion_G1.md.
Reutiliza sin modificarlos scripts/fmt/video.py (color, ass, master), sonido.py (Mezcla), fmt03.py (plano_z, leer,
control, entregar, md5_stream, ebur), fmt03_v02.py (perfil, contraste_blanco, mascara_texto, textos_limites,
momentanea) y fmt04_util.py (hoja_c). Lo nuevo de esta pieza vive acá:
  - planos por TOMA CONTINUA: cada toma se decodifica una sola vez (fmt03.plano_z con zoom y centro por cuadro), así
    los cortes internos del guion (1a/1b, 2a/2b, 3a/3b, 4a/4b/4c, 5a/5b/5c, 6a/6b/6c) no pueden duplicar ni saltear
    cuadros;
  - una pasada de efectos por cuadro sobre el video unido (fundidos a blanco y a negro, desenfoque horizontal de los
    barridos, degradé de 6b–6c), con mezcla en YUV de rango limitado, sin overlay;
  - mediciones de «sin resultado antes de tiempo» (gotas sobre la Negra de 4631, salida de la Blanca de 7884).

Etapas (python vir01.py <etapa>, con nice -n 10):
  medir → planos → efectos → audio → master → control → entregar
"""
import json, math, subprocess, sys, hashlib, shutil, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V          # noqa: E402
import fmt03 as U          # noqa: E402
import fmt03_v02 as U2     # noqa: E402
import fmt04_util as F4    # noqa: E402

R = Path('/home/user/1')
T = R / 'TRABAJO/vir/vir01'
EXP = R / 'EXPORTACIONES'
PIEZA = Path('/mnt/project-files/piezas/VIR_marcas_nuevas_virales/VIR-01_a_nada/')
FPS = 30
NF = 318
DUR = NF / FPS                 # 10,600 s
W, H = 1080, 1920


def lin(a, b, n):
    """n valores lineales de a a b (incluidos los dos extremos): el acercamiento «lineal por cuadro» del guion."""
    return [a + (b - a) * k / (n - 1) for k in range(n)] if n > 1 else [a]


# =====================================================================================================
# tabla §2 del guion, agrupada por toma continua (cuadro de fuente n0; zoom y centro por cuadro, coordenadas de la
# toma rotada: 4631 y 3453 1080×1920; 7887, 7884 y 7857 2160×3840)
# =====================================================================================================
CY1B_DELTA = 472   # 1b: recorrido vertical del centro (ver tomas(), S1)


def tomas():
    return [
        # 1a c0–c37 (fuente 2,433–3,700, z 1) + 1b c38–c44 (3,700–3,900, z 1→2,5, cx 540→650)
        # DESVÍO medido (etapa medir, gotas_4631_c110-c118_ventana_1a1.jpg): con cy 960→560 lineal, en c42 (fuente
        # 3,833 s) quedan 146 px de las remeras en cuadro y una gota nueva sobre la Negra (864, 1099) cae DENTRO de la
        # ventana. Criterio del guion: «las remeras salen por abajo antes de que caiga la espuma». z y cx siguen
        # lineales; cy baja con salida suave 960 → 488 (u = k/6, cy = 960 − 472·(1 − (1 − u)²)): borde inferior de la
        # ventana 1920 / 1583 / 1338 / 1155 / 1020 / 928 / 872 → las remeras (tope 1027) salen enteras en c42.
        dict(id='S1', toma='IMG_4631', n0=73, nf=45, m0=0,
             zs=[1.0] * 38 + lin(1.0, 2.5, 7), cxs=[540] * 38 + lin(540, 650, 7),
             cys=[960] * 38 + [960 - CY1B_DELTA * (1 - (1 - k / 6) ** 2) for k in range(7)],
             sub=[('1a', 0, 37), ('1b', 38, 44)]),
        # 2a c45–c53 (0,000–0,267, z 2,5→1, cx 700→1080, cy 900→1920) + 2b c54–c104 (0,300–1,967, z 1)
        dict(id='S2', toma='IMG_7887', n0=0, nf=60, m0=45,
             zs=lin(2.5, 1.0, 9) + [1.0] * 51, cxs=lin(700, 1080, 9) + [1080] * 51, cys=lin(900, 1920, 9) + [1920] * 51,
             sub=[('2a', 45, 53), ('2b', 54, 104)]),
        # 3a c105–c141 (2,300–3,500, z 1) + 3b c142–c149 (3,533–3,767, z 1→2,5, cx 1080→1300, cy 1920→768)
        dict(id='S3', toma='IMG_7884', n0=69, nf=45, m0=105,
             zs=[1.0] * 37 + lin(1.0, 2.5, 8), cxs=[1080] * 37 + lin(1080, 1300, 8), cys=[1920] * 37 + lin(1920, 768, 8),
             sub=[('3a', 105, 141), ('3b', 142, 149)]),
        # 4a c150–c158 (0,000–0,267, z 2,5→1, cx 1080, cy 768→1920) + 4b c159–c206 (0,300–1,867, z 1)
        # + 4c c207–c209 (1,900–1,967, z 1→1,25, cx 1080→1500, desenfoque horizontal en la pasada de efectos)
        dict(id='S4', toma='IMG_7857', n0=0, nf=60, m0=150,
             zs=lin(2.5, 1.0, 9) + [1.0] * 48 + lin(1.0, 1.25, 3), cxs=[1080] * 57 + lin(1080, 1500, 3),
             cys=lin(768, 1920, 9) + [1920] * 51, sub=[('4a', 150, 158), ('4b', 159, 206), ('4c', 207, 209)]),
        # 5a c210–c211 (2,200–2,233, z 1,25→1, cx 330→540, desenfoque) + 5b c212–c235 (2,267–3,033, z 1)
        # + 5c c236–c239 (3,067–3,167, z 1→2,5, cx 540→260, cy 960→384; negro en la pasada de efectos)
        dict(id='S5', toma='IMG_3453', n0=66, nf=30, m0=210,
             zs=lin(1.25, 1.0, 2) + [1.0] * 24 + lin(1.0, 2.5, 4), cxs=lin(330, 540, 2) + [540] * 24 + lin(540, 260, 4),
             cys=[960] * 26 + lin(960, 384, 4), sub=[('5a', 210, 211), ('5b', 212, 235), ('5c', 236, 239)]),
        # 6a c240–c254 (3,500–3,967) + 6b c255–c284 (4,000–4,967, degradé) + 6c c285–c317 (5,000–6,067, degradé)
        dict(id='S6', toma='IMG_4631', n0=105, nf=78, m0=240,
             zs=[1.0] * 78, cxs=[540] * 78, cys=[960] * 78, sub=[('6a', 240, 254), ('6b', 255, 284), ('6c', 285, 317)]),
    ]


def ventana(toma, Z, cx, cy):
    """la misma ventana que fmt03.plano_z: (x, y, w, h) en coordenadas de la toma, limitada al cuadro."""
    nw, nh = V.TOMAS[toma]['nat']
    Z = max(1.0, round(Z, 6)); w, h = nw / Z, nh / Z
    x = min(max(cx - w / 2, 0), nw - w); y = min(max(cy - h / 2, 0), nh - h)
    return x, y, w, h


# =====================================================================================================
# etapa 1 · mediciones sobre las fuentes (antes del render)
# =====================================================================================================
CLARO_GOTA = 150   # L de una gota (el ROCCÉ tono sobre tono de la Negra llega a L ≈ 110–140: con 110 contaba como gota)


def gotas_4631(n0=105, n1=125):
    """Gotas sobre la Negra de 4631 por cuadro de fuente: componentes claros (L > CLARO_GOTA) chicos (4–400 px) dentro de la
    silueta de la remera negra (L < 60, componente mayor, huecos rellenos) y a más de 8 px de las letras de «Founders
    Privée» (componentes claros > 400 px). Devuelve también el tope de la Negra y de la Blanca (coordenadas 1080×1920)."""
    from scipy import ndimage as nd
    fr = U.leer(V._src('IMG_4631'), W, H, n0=n0, n1=n1, vf_pre=V.color('IMG_4631'))
    out = []
    for k, f in enumerate(fr):
        L = U.luma(f); sat = (f.max(-1).astype(np.float32) - f.min(-1)) / (f.max(-1).astype(np.float32) + 1)
        zona = np.zeros_like(L, bool); zona[950:1750, 380:1080] = True
        lab, n = nd.label((L < 60) & zona)
        s = nd.sum(np.ones_like(L), lab, range(1, n + 1)); negra = lab == (int(np.argmax(s)) + 1)
        silueta = nd.binary_fill_holes(nd.binary_closing(negra, iterations=6))
        claro = (L > CLARO_GOTA) & silueta & ~negra
        lab2, n2 = nd.label(claro)
        s2 = nd.sum(np.ones_like(L), lab2, range(1, n2 + 1))
        letras = np.isin(lab2, [i + 1 for i, v in enumerate(s2) if v > 400])
        cerca = nd.binary_dilation(letras, iterations=8)
        gotas = []
        for i, v in enumerate(s2):
            if 4 <= v <= 400:
                m = lab2 == i + 1
                if not (m & cerca).any():
                    ys, xs = np.nonzero(m); gotas.append((int(xs.mean()), int(ys.mean()), int(v)))
        zb = np.zeros_like(L, bool); zb[950:1750, 0:700] = True
        lb, nb = nd.label((L > 185) & (sat < 0.15) & zb)
        sb = nd.sum(np.ones_like(L), lb, range(1, nb + 1)) if nb else []
        blanca = lb == (int(np.argmax(sb)) + 1) if nb else np.zeros_like(L, bool)
        ys_n = np.nonzero(silueta.any(1))[0]; ys_b = np.nonzero(blanca.any(1))[0]
        out.append(dict(cuadro_fuente=n0 + k, t_fuente=round((n0 + k) / FPS, 4), gotas=len(gotas),
                        gotas_y_min=min((g[1] for g in gotas), default=None), gotas_xy=gotas[:40],
                        tope_negra=int(ys_n.min()) if len(ys_n) else None, tope_blanca=int(ys_b.min()) if len(ys_b) else None,
                        x_negra=[int(np.nonzero(silueta.any(0))[0].min()), int(np.nonzero(silueta.any(0))[0].max())]))
    return out


def blanca_7884(n0=100, n1=114):
    """tope de la Blanca de 7884 por cuadro de fuente (coordenadas 2160×3840): componente blanco (L > 190, sat < 0,15)
    más grande por debajo de y 1300 (arriba de esa fila está la espuma)."""
    from scipy import ndimage as nd
    fr = U.leer(V._src('IMG_7884'), W, H, n0=n0, n1=n1, vf_pre=V.color('IMG_7884'))
    out = []
    for k, f in enumerate(fr):
        L = U.luma(f); sat = (f.max(-1).astype(np.float32) - f.min(-1)) / (f.max(-1).astype(np.float32) + 1)
        z = np.zeros_like(L, bool); z[650:1500, 100:1000] = True
        lab, n = nd.label(nd.binary_opening((L > 190) & (sat < 0.15) & z, iterations=2))
        s = nd.sum(np.ones_like(L), lab, range(1, n + 1)); m = lab == (int(np.argmax(s)) + 1)
        ys, xs = np.nonzero(m)
        out.append(dict(cuadro_fuente=n0 + k, t_fuente=round((n0 + k) / FPS, 4), tope=int(ys.min()) * 2,
                        x=[int(xs.min()) * 2, int(xs.max()) * 2], area_px_1080=int(m.sum())))
    return out


def letras_3453(n0=88, n1=96):
    """estampado de 3453 por cuadro de fuente (1080×1920): píxeles grises claros (L > 95, sat < 0,25) = letras."""
    fr = U.leer(V._src('IMG_3453'), W, H, n0=n0, n1=n1, vf_pre=V.color('IMG_3453'))
    out = []
    for k, f in enumerate(fr):
        L = U.luma(f); sat = (f.max(-1).astype(np.float32) - f.min(-1)) / (f.max(-1).astype(np.float32) + 1)
        m = (L > 95) & (sat < 0.25)
        out.append((n0 + k, m))
    return out


def etapa_medir():
    T.mkdir(parents=True, exist_ok=True)
    rep = {}
    tm = {t['id']: t for t in tomas()}
    # --- 1b: gotas sobre la Negra contra la ventana de cada cuadro del máster ---
    g = gotas_4631()
    # detecciones fijas (ya están en 3,500–3,667 s, antes de que llegue el agua: una mota en y ≈ 1500 y la tilde del
    # ROCCÉ tono sobre tono en ≈ (861, 1099)) no son gotas: se descartan las que quedan a ≤ 14 px de una de referencia
    ref = [p for d in g if d['cuadro_fuente'] <= 110 for p in d['gotas_xy']]
    for d in g:
        d['gotas_nuevas_xy'] = [p for p in d['gotas_xy'] if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 14 for q in ref)]
        d['gotas_nuevas'] = len(d['gotas_nuevas_xy'])
    rep['gotas_4631'] = g
    rep['gotas_4631_nota'] = ('gotas = componentes con L > %d de 4–400 px dentro de la silueta de la Negra y lejos de '
                              'Founders Privée; «nuevas» = sin una detección de 3,500–3,667 s a ≤ 14 px (mota fija y '
                              'tilde de ROCCÉ). Primera gota nueva: fuente c115 (3,833 s).' % CLARO_GOTA)
    s1 = tm['S1']; fil = []
    for c in range(36, 45):
        k = c - s1['m0']; n = s1['n0'] + k
        x, y, w, h = ventana('IMG_4631', s1['zs'][k], s1['cxs'][k], s1['cys'][k])
        gi = [d for d in g if d['cuadro_fuente'] == n][0]
        dentro = [p for p in gi['gotas_nuevas_xy'] if x <= p[0] <= x + w and y <= p[1] <= y + h]
        tope = min(gi['tope_negra'], gi['tope_blanca'])
        fil.append(dict(cuadro=c, fuente=n, t_fuente=round(n / FPS, 4), ventana=[round(x), round(y), round(x + w), round(y + h)],
                        gotas_nuevas_en_fuente=gi['gotas_nuevas'], gotas_nuevas_xy=gi['gotas_nuevas_xy'],
                        gotas_dentro_de_la_ventana=len(dentro),
                        tope_remeras=tope, remeras_visibles_px=max(0, round(y + h - tope))))
    rep['1b_ventanas'] = fil
    # imagen: Negra a 1:1 en c110–c118 de fuente con la ventana del máster y las gotas nuevas marcadas
    from PIL import Image, ImageDraw, ImageFont
    fr = U.leer(V._src('IMG_4631'), W, H, n0=110, n1=118, vf_pre=V.color('IMG_4631'))
    fnt = ImageFont.truetype(U.FONT, 22); tiles = []
    vent = {f['fuente']: (f['cuadro'], f['ventana']) for f in fil}
    for k, f in enumerate(fr):
        n = 110 + k; gi = [d for d in g if d['cuadro_fuente'] == n][0]
        im = Image.fromarray(f[980:1440, 420:1080].copy()); d = ImageDraw.Draw(im)
        for x_, y_, _ in gi['gotas_nuevas_xy']:
            d.ellipse([x_ - 420 - 10, y_ - 980 - 10, x_ - 420 + 10, y_ - 980 + 10], outline=(255, 0, 0), width=3)
        rot = f'fuente c{n} {n / FPS:.3f}s'
        if n in vent:
            c, (x0, y0, x1, y1) = vent[n]
            d.rectangle([x0 - 420, y0 - 980, x1 - 420, y1 - 980], outline=(0, 255, 0), width=3)
            rot += f' = máster c{c}'
        d.rectangle([0, 0, 380, 30], fill=(0, 0, 0)); d.text((4, 3), rot, font=fnt, fill=(255, 255, 0))
        tiles.append(im)
    tw, th = tiles[0].size
    hoja = Image.new('RGB', (3 * (tw + 2), 3 * (th + 2)), (30, 30, 30))
    for i, t in enumerate(tiles):
        hoja.paste(t, ((i % 3) * (tw + 2), (i // 3) * (th + 2)))
    hoja.save(T / 'gotas_4631_c110-c118_ventana_1a1.jpg', quality=90)
    # --- 3b: la Blanca de 7884 contra la ventana ---
    b = blanca_7884()
    rep['blanca_7884'] = b
    s3 = tm['S3']; fil = []
    for c in range(138, 150):
        k = c - s3['m0']; n = s3['n0'] + k
        x, y, w, h = ventana('IMG_7884', s3['zs'][k], s3['cxs'][k], s3['cys'][k])
        bi = [d for d in b if d['cuadro_fuente'] == n][0]
        fil.append(dict(cuadro=c, fuente=n, t_fuente=round(n / FPS, 4), ventana=[round(x), round(y), round(x + w), round(y + h)],
                        tope_blanca=bi['tope'], blanca_visible_px=max(0, round(y + h - bi['tope']))))
    rep['3b_ventanas'] = fil
    # --- 5c: letras del pecho dentro de la ventana (fracción de la ventana) ---
    s5 = tm['S5']; fil = []
    for n, m in letras_3453():
        k = n - s5['n0']
        if not 0 <= k < s5['nf']:
            continue
        x, y, w, h = ventana('IMG_3453', s5['zs'][k], s5['cxs'][k], s5['cys'][k])
        sub = m[int(y):int(y + h), int(x):int(x + w)]
        fil.append(dict(cuadro=s5['m0'] + k, fuente=n, ventana=[round(x), round(y), round(x + w), round(y + h)],
                        letras_pct_ventana=round(float(sub.mean() * 100), 2)))
    rep['5c_letras'] = fil
    rep['revisado_a_ojo'] = {
        'fuente c113 (791, 1157), 54 px, dentro de la ventana de c40': (
            'punta del trazo de la «d» de «Founders», que en ese cuadro se separa del resto de la letra; aparece un solo '
            'cuadro y no persiste: no es una gota (hojas/4631_c111-c115_791_1157_x4.jpg)'),
        'primera gota real sobre la Negra': 'fuente c115 (3,833 s): (864, 1099), (941, 1310), (653, 1344); en el máster '
                                            'c42 la ventana termina en y 1020, fuera de las tres'}
    json.dump(rep, open(T / 'medir.json', 'w'), ensure_ascii=False, indent=1)
    for d in g:
        print('4631', d['cuadro_fuente'], d['t_fuente'], 'gotas', d['gotas'], 'ymin', d['gotas_y_min'], 'tope N/B',
              d['tope_negra'], d['tope_blanca'], d['x_negra'])
    for f in rep['1b_ventanas'] + rep['3b_ventanas'] + rep['5c_letras']:
        print(f)


# =====================================================================================================
# etapa 2 · planos (una decodificación por toma continua) + unión
# =====================================================================================================
P = T / 'planos'
BASE = T / 'vir01_base.mp4'          # montaje sin efectos ni textos
VID = T / 'vir01_video.mp4'          # montaje con fundidos, desenfoques y degradé (sin textos)


def etapa_planos():
    P.mkdir(parents=True, exist_ok=True)
    reg = []
    for t in tomas():
        assert len(t['zs']) == len(t['cxs']) == len(t['cys']) == t['nf'], t['id']
        p = U.plano_z(t['toma'], t['n0'], t['zs'], t['cxs'], t['cys'], P / f"{t['id']}.mp4")
        p.update(id=t['id'], m0=t['m0'], sub=t['sub'])
        reg.append(p); print(t['id'], t['toma'], 'fuente', t['n0'], '→', t['n0'] + t['nf'] - 1, 'máster c', t['m0'], flush=True)
    n = V.unir(reg, BASE)
    assert n == NF, n
    json.dump(dict(cuadros=n, planos=reg), open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1)
    # control: cuadros consecutivos casi iguales (duplicados) dentro de cada toma
    a = U.leer(BASE, 270, 480).astype(np.float32)
    dif = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2, 3))
    cortes = [t['m0'] for t in tomas()]
    bajos = [(i + 1, round(float(x), 2)) for i, x in enumerate(dif) if x < 0.5 and (i + 1) not in cortes]
    json.dump(dict(dif_consecutiva=[round(float(x), 2) for x in dif], casi_iguales=bajos),
              open(T / 'dif_consecutiva.json', 'w'), indent=0)
    print('total', n, 'cuadros casi iguales al anterior (c, dif):', bajos)


# =====================================================================================================
# etapa 3 · efectos por cuadro sobre el video unido (YUV de rango limitado, sin overlay)
# =====================================================================================================
BLANCO = (235, 128, 128)
NEGRO = (16, 128, 128)
Y_BLANCO_OBJ = 203        # objetivo de Y por píxel al calcular la α mínima (margen de 3 sobre 200 por la compresión)
FRAC_BLANCO_OBJ = 0.925   # fracción de píxeles del cuadro sin textos (≥ 0,90 pedido + ≈ 2 % de la caja del texto)
DESENF = {207: 36, 208: 36, 209: 36, 210: 24, 211: 24}   # radio horizontal de caja (px de 1080), como fmt03 (sizeY=36)
NEGROS = {238: 0.5, 239: 1.0}
DEG = dict(alfa=0.38, fundido_px=150, y_cero_max=480, separacion_px=20, cuadros=(255, 317))


def alfa_min_blanco(Y):
    """α mínima de la mezcla con blanco (Y 235) para que FRAC_BLANCO_OBJ de los píxeles queden con Y ≥ Y_BLANCO_OBJ."""
    Y = Y.astype(np.float32)
    nec = np.clip((Y_BLANCO_OBJ - Y) / (235.0 - Y + 1e-6), 0, 1)
    return float(math.ceil(np.quantile(nec, FRAC_BLANCO_OBJ) * 100) / 100)


def tope_remeras_4631(f):
    """fila más alta de las dos remeras en un cuadro 1080×1920 RGB de 4631 sin acercamiento (Negra: L < 60, componente
    mayor en y 900–1750, x 380–1080; Blanca: L > 185 y sat < 0,15, componente mayor en y 900–1750, x 0–700)."""
    from scipy import ndimage as nd
    L = U.luma(f); sat = (f.max(-1).astype(np.float32) - f.min(-1)) / (f.max(-1).astype(np.float32) + 1)
    tops = {}
    for nom, m, (x0, x1) in (('negra', L < 60, (380, 1080)), ('blanca', (L > 185) & (sat < 0.15), (0, 700))):
        z = np.zeros_like(m); z[900:1750, x0:x1] = True
        lab, n = nd.label(m & z)
        if not n:
            tops[nom] = None; continue
        s = nd.sum(np.ones_like(L), lab, range(1, n + 1))
        tops[nom] = int(np.nonzero((lab == int(np.argmax(s)) + 1).any(1))[0].min())
    return tops


def _yuv(b):
    ny = W * H; nc = ny // 4
    f = np.frombuffer(b, np.uint8).astype(np.float32)
    return f[:ny].reshape(H, W), f[ny:ny + nc].reshape(H // 2, W // 2), f[ny + nc:].reshape(H // 2, W // 2)


def _blur_h(p, r):
    if r < 1:
        return p
    q = np.pad(p, ((0, 0), (r + 1, r)), mode='edge')
    c = np.cumsum(q, axis=1, dtype=np.float64)
    return ((c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)).astype(np.float32)


def aplicar_efectos(src, dst, ops):
    """ops: {cuadro: [(tipo, valor), ...]} con tipo 'blanco'/'negro' (α escalar), 'blur_h' (radio en px de luma) o
    'degrade' (α por fila, negro). Los cuadros sin ops pasan con el mismo contenido (recodificados con ENC_INT)."""
    ny = W * H; nc = ny // 4
    dec = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(src), '-f', 'rawvideo',
                            '-pix_fmt', 'yuv420p', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p',
                            '-s', f'{W}x{H}', '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-i', '-', *V.ENC_INT, str(dst)],
                           stdin=subprocess.PIPE)
    k = 0
    while True:
        b = dec.stdout.read(ny + 2 * nc)
        if len(b) < ny + 2 * nc:
            break
        if k in ops:
            Y, Cb, Cr = _yuv(b)
            for tipo, v in ops[k]:
                if tipo == 'blur_h':
                    Y = _blur_h(Y, int(v)); Cb = _blur_h(Cb, int(v) // 2); Cr = _blur_h(Cr, int(v) // 2)
                elif tipo in ('blanco', 'negro'):
                    y0, u0, v0 = BLANCO if tipo == 'blanco' else NEGRO
                    Y = Y + (y0 - Y) * v; Cb = Cb + (u0 - Cb) * v; Cr = Cr + (v0 - Cr) * v
                elif tipo == 'degrade':
                    a = np.asarray(v, np.float32)
                    fy = (1 - a)[:, None]; fc = (1 - 0.5 * (a[0::2] + a[1::2]))[:, None]
                    Y = 16 + (Y - 16) * fy; Cb = 128 + (Cb - 128) * fc; Cr = 128 + (Cr - 128) * fc
            b = np.concatenate([Y.ravel(), Cb.ravel(), Cr.ravel()]).round().clip(0, 255).astype(np.uint8).tobytes()
        enc.stdin.write(b); k += 1
    dec.stdout.close(); dec.wait(); enc.stdin.close(); enc.wait()
    assert k == NF and enc.returncode == 0, (k, enc.returncode)


def leer_Y(src, n):
    """plano Y (rango limitado, sin conversión) del cuadro n."""
    r = U.run(['ffmpeg', '-v', 'error', '-i', str(src), '-vf', f"select='eq(n\\,{n})'", '-fps_mode', 'passthrough',
               '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'])
    return np.frombuffer(r, np.uint8)[:W * H].reshape(H, W)


def etapa_efectos():
    ops = {}
    rep = dict(blancos={}, negros=NEGROS, desenfoque_h_radio=DESENF, degrade=dict(parametros=DEG, por_cuadro=[]))
    # fundidos a blanco: salida (penúltimo 0,5, último α mín.) y entrada (primero α mín., segundo 0,5)
    # DESVÍO medido: en c44 (espuma ampliada 2,5×) la α mínima da 0,22 y en c150 (cielo de 7857) 0,49, menos que el
    # 0,5 del cuadro vecino: aplicada tal cual, el blanco bajaría justo antes del corte (0,5 → 0,22) y parpadearía.
    # Se usa α = máx(α mínima, 0,5): el fundido nunca retrocede y el cuadro sigue cumpliendo ≥ 90 % con Y ≥ 200.
    rep['alfa_minima_medida'] = {}
    for sal, ent in ((44, 45), (149, 150)):
        m_sal = alfa_min_blanco(leer_Y(BASE, sal)); m_ent = alfa_min_blanco(leer_Y(BASE, ent))
        rep['alfa_minima_medida'][sal] = m_sal; rep['alfa_minima_medida'][ent] = m_ent
        for n, a in ((sal - 1, 0.5), (sal, max(m_sal, 0.5)), (ent, max(m_ent, 0.5)), (ent + 1, 0.5)):
            ops.setdefault(n, []).append(('blanco', a)); rep['blancos'][n] = a
    for n, r in DESENF.items():
        ops.setdefault(n, []).append(('blur_h', r))
    for n, a in NEGROS.items():
        ops.setdefault(n, []).append(('negro', a))
    # degradé 6b–6c: y_cero = min(480, tope de las remeras − 20) por cuadro (perfil de FMT-03 v02)
    n0, n1 = DEG['cuadros']
    fr = U.leer(BASE, W, H, n0=n0, n1=n1)
    for k, f in enumerate(fr):
        n = n0 + k
        tp = tope_remeras_4631(f)
        top = min(v for v in tp.values() if v is not None)
        yc = min(DEG['y_cero_max'], top - DEG['separacion_px'])
        a = U2.perfil(DEG['alfa'], yc - DEG['fundido_px'], yc)
        ops.setdefault(n, []).append(('degrade', a))
        rep['degrade']['por_cuadro'].append(dict(cuadro=n, tope_negra=tp['negra'], tope_blanca=tp['blanca'], y_cero=yc,
                                                 y_plano=yc - DEG['fundido_px']))
    del fr
    aplicar_efectos(BASE, VID, ops)
    # comprobación sobre el video codificado (sin textos)
    chk = {}
    for n in (43, 44, 45, 46, 148, 149, 150, 151):
        Y = leer_Y(VID, n); chk[f'c{n}'] = dict(pct_Y_mayor_igual_200=round(float((Y >= 200).mean() * 100), 2))
    for n in (237, 238, 239, 240):
        Y = leer_Y(VID, n); chk[f'c{n}'] = dict(pct_Y_menor_igual_20=round(float((Y <= 20).mean() * 100), 2))
    rep['comprobacion_video_sin_textos'] = chk
    # el degradé no toca las remeras: oscurecimiento medio por fila base − video en c255–c317
    a0 = U.leer(BASE, W, H, n0=n0, n1=n1).astype(np.float32)[:, :, :, 1]
    a1 = U.leer(VID, W, H, n0=n0, n1=n1).astype(np.float32)[:, :, :, 1]
    osc = (a0 - a1).mean(axis=2)                    # (cuadros, filas)
    filas = []
    for k, d in enumerate(rep['degrade']['por_cuadro']):
        r = np.nonzero(osc[k] > 1.5)[0]
        ymax = int(r.max()) if len(r) else None
        top = min(v for v in (d['tope_negra'], d['tope_blanca']) if v is not None)
        d.update(y_max_oscurecida=ymax, separacion_px=(top - ymax) if ymax is not None else None,
                 osc_medio_desde_tope=round(float(osc[k, top:].mean()), 3))
    rep['degrade']['separacion_min_px'] = min(d['separacion_px'] for d in rep['degrade']['por_cuadro'] if d['separacion_px'] is not None)
    rep['degrade']['osc_max_desde_tope'] = max(d['osc_medio_desde_tope'] for d in rep['degrade']['por_cuadro'])
    del a0, a1
    json.dump(rep, open(T / 'efectos.json', 'w'), ensure_ascii=False, indent=1)
    print('blancos', rep['blancos']); print(chk)
    print('degradé: separación mín', rep['degrade']['separacion_min_px'], 'osc máx desde el tope',
          rep['degrade']['osc_max_desde_tope'], 'y_cero', sorted({d['y_cero'] for d in rep['degrade']['por_cuadro']}))


# =====================================================================================================
# etapa 4 · sonido (§5 del guion; grilla 120 BPM desde 0,0, La menor; música TEMP propia; foley PROVISORIO)
# Se arma en tres mezclas separadas (música, ambiente, foley) que se suman muestra a muestra: la completa es la suma de
# las tres y la sin música es ambiente + foley con los MISMOS sonidos (el ruido de sonido.py sale de un generador
# global: armarlas por separado daría ruidos distintos). Así la tabla de niveles por capa es exacta.
# =====================================================================================================
A = T / 'audio'


def musica(m):
    def charles(t0, t1, g=.08):
        for t in np.arange(t0, t1 - 1e-6, 0.25):
            m.charles(round(float(t), 3), g)
    # intro (c0–c44)
    m.pad(0.0, [45, 48, 52], 0.95, .06, 1000, a=.12, r=.3); m.campana(0.0, 76, .05)
    for t, g in zip((0.0, 0.25, 0.5, 0.75), (.07, .08, .09, .10)):
        m.charles(t, g)
    m.subida(0.40, 0.95, .16)
    # drop 1 (c45), sin impacto: el golpe es el real de 4631 en el hueco
    m.bombo(1.5, .9); m.ocho08(1.5, 33, .9, .55, glide_desde=40); m.pad(1.5, [45, 48, 52], 1.9, .06, 1400)
    # groove (c45–c104)
    charles(1.5, 3.5); m.palma(2.0); m.palma(3.0); m.bombo(2.5, .6); m.ocho08(2.5, 33, .45); m.ocho08(3.0, 36, .45)
    # tensión (c105–c133)
    m.bombo(3.5, .7); m.pad(3.5, [41, 45, 48], .9, .06, 1200, r=.3); charles(3.5, 4.25)
    m.redoble(3.70, 4.45, .12); m.subida(3.85, 4.45, .14)
    # drop 2 (c165)
    m.bombo(5.5, 1.0); m.impacto(5.5, .40); m.ocho08(5.5, 33, 1.0, .6, glide_desde=40)
    m.pad(5.5, [45, 48, 52, 57], 1.3, .07); charles(5.5, 7.0); m.palma(6.0); m.palma(6.5); m.bombo(6.0, .6)
    # pista (c210–c233)
    m.campana(7.0, 76, .06, .9); m.pad(7.0, [48, 52, 55], .8, .05, 900, r=.3); m.subida(7.30, 7.80, .14)
    # drop 3 (c255)
    m.bombo(8.5, 1.0); m.ocho08(8.5, 33, 1.1, .6, glide_desde=40); m.pad(8.5, [45, 48, 52, 57], 1.0, .07)
    m.campana(8.5, 76, .07, .9); charles(8.5, 9.5); m.palma(9.0)
    # CTA (c285)
    m.bombo(9.5, .8); m.ocho08(9.5, 36, .5); m.ocho08(10.0, 33, .6); m.pad(9.5, [45, 48, 52], .8, .06, r=.5)
    m.palma(10.0, .25)
    # huecos y final, después de colocar todo
    for t0, t1 in HUECOS:
        m.silenciar('mus', t0, t1)
    m.fundido('mus', 10.10, 10.60)
    # las colas de reverberación de la música van a la pista 'fx' de ESTA mezcla (sonido.py): se funden con la música
    # para que no corten secas en 10,600 (no es un desvío: son parte de la música; foley y ambiente no se tocan)
    m.fundido('fx', 10.10, 10.60)


HUECOS = [(0.95, 1.50), (4.45, 5.50), (7.80, 8.50)]


def ambientes(m):
    m.ambiente('IMG_4631', 2.433, 0.000, 2.000, 0, hp=40, fin_fade=.45)
    m.ambiente('IMG_7887', 0.000, 1.500, 2.900, -6, hp=150, ini_fade=.3, fin_fade=.1)
    m.ambiente('IMG_7857', 3.500, 2.850, 3.500, -8, ini_fade=.1)
    m.ambiente('IMG_7884', 2.300, 3.500, 5.800, -2, hp=40, fin_fade=.5)
    m.ambiente('IMG_7857', 1.400, 5.400, 7.000, -8, ini_fade=.3, fin_fade=.2)
    m.ambiente('IMG_4631', 3.500, 8.000, 10.600, 0, hp=40, fin_fade=.25)


def foley(m):
    m.tela(5.45, .30, .16); m.tela(5.70, .60, .08)
    m.barrido(7.00, .25, .20)
    m.tela(7.85, .15, .16)
    m.toque(9.50, .16, 2400)
    m.obturador(4.95, .40)        # c148 (4,933–4,967); Roma: aprobado, g ≤ 0,40


def mezclas():
    from sonido import Mezcla
    mus, amb, fol = Mezcla(DUR), Mezcla(DUR), Mezcla(DUR)
    musica(mus); ambientes(amb); foley(fol)
    def suma(*ms):
        t = Mezcla(DUR)
        for k in t.pistas:
            t.pistas[k] = sum(x.pistas[k] for x in ms)
        t.ev = [e for x in ms for e in x.ev]
        return t
    return dict(mus=mus, amb=amb, fol=fol, completa=suma(mus, amb, fol), sinmusica=suma(amb, fol))


def duck(P_bombo, duck_db=6.0, sr=48000):
    """misma envolvente de bombeo que sonido.Mezcla.exportar (para medir la música tal como entra en la suma)."""
    N = len(P_bombo); bk = np.abs(P_bombo).mean(1)
    a = np.exp(-1 / (0.12 * sr)); e = np.zeros(N); acc = 0.0
    pk = np.convolve(bk, np.ones(64) / 64, 'same')
    for i in range(0, N, 64):
        acc = max(pk[i:i + 64].max(), acc * a ** 64); e[i:i + 64] = acc
    e = e / (e.max() + 1e-9)
    return 1 - (1 - 10 ** (-duck_db / 20)) * e


def etapa_audio():
    A.mkdir(parents=True, exist_ok=True)
    M = mezclas()
    res = {}
    for k in ('completa', 'sinmusica'):
        res[k] = M[k].exportar(str(A / f'vir01_{k}.wav'), lufs=-14)
        print(k, res[k], flush=True)
    # capas con la ganancia final de la completa (antes del limitador): para la tabla de niveles
    import soundfile as sf
    gan = json.load(open(A / 'vir01_completa_eventos.json'))['ganancia_db']
    g = 10 ** (gan / 20)
    mu = M['mus'].pistas
    capas = dict(mus=(mu['mus'] * duck(mu['bombo'])[:, None] + mu['bombo']) * g, mus_fx=mu['fx'] * g,
                 fx=M['fol'].pistas['fx'] * g, amb=M['amb'].pistas['amb'] * g)
    for k, v in capas.items():
        sf.write(str(A / f'capa_{k}.wav'), v.astype(np.float32), 48000, subtype='FLOAT')
    gan_s = json.load(open(A / 'vir01_sinmusica_eventos.json'))['ganancia_db']
    json.dump(dict(completa=res['completa'], sinmusica=res['sinmusica'], ganancia_completa_db=gan, ganancia_sinmusica_db=gan_s),
              open(A / 'audio.json', 'w'), indent=1)


# =====================================================================================================
# etapa 5 · textos exactos (§4) + máster de las cuatro versiones
# =====================================================================================================
MAS = T / 'master'
HOOK = {'A': '¿Las alcanza?', 'B': '¿Se las lleva?'}
NOMBRES = {'A': 'ROCCE_VIR01_A_NADA_A_v01.mp4', 'B': 'ROCCE_VIR01_A_NADA_B_v01.mp4',
           'A_sinmusica': 'ROCCE_VIR01_A_NADA_A_SINMUSICA_v01.mp4', 'B_sinmusica': 'ROCCE_VIR01_A_NADA_B_SINMUSICA_v01.mp4'}
FUNDADOR = 'El fundador fue por la foto.'


def textos(hook):
    # DESVÍO medido: con y 236 el pop (118 %) sube la caja a y 217 / 218 / 219 en c0–c2, fuera de la zona 220–480 de la
    # condición 4 de Roma. Con y 239 la caja queda en 220 en c0 y en 223–309 desde c3 (3 px más abajo que el guion).
    t = [dict(t0=0 / FPS, t1=45 / FPS, txt=HOOK[hook], estilo='CajaN', y=239, pop=True),          # c0–c44
         None,                                                                                      # c54–c104
         dict(t0=120 / FPS, t1=142 / FPS, txt='¿Y esta?', estilo='CajaN', y=236),                 # c120–c141
         dict(t0=255 / FPS, t1=285 / FPS, txt='so f★cking close.', estilo='Grande', y=236, pop=True),  # c255–c284
         dict(t0=285 / FPS, t1=318 / FPS, txt='Llevala hasta donde rompe.', estilo='Caja', y=236),     # c285–c317
         dict(t0=285 / FPS, t1=318 / FPS, txt='link en bio', estilo='Chico', y=340)]                   # c285–c317
    w = ancho_texto(dict(t0=0, t1=1, txt=FUNDADOR, estilo='CajaN', y=236))
    if w <= 900:
        t[1] = dict(t0=54 / FPS, t1=105 / FPS, txt=FUNDADOR, estilo='CajaN', y=236)
        return [x for x in t if x]
    # guion §4: si pasa de 900 px, dos renglones «El fundador» / «fue por la foto.» en y 236 / 316
    t[1] = dict(t0=54 / FPS, t1=105 / FPS, txt='El fundador', estilo='CajaN', y=236)
    t.insert(2, dict(t0=54 / FPS, t1=105 / FPS, txt='fue por la foto.', estilo='CajaN', y=316))
    return t


def ancho_texto(texto):
    p = T / 'ctrl'; p.mkdir(parents=True, exist_ok=True)
    _, g = U2.mascara_texto(texto, 0.5, p, 'ancho', dil=0)
    xs = np.nonzero(g.any(0))[0]
    return int(xs.max() - xs.min() + 1)


LIMITES = {'¿Las alcanza?': (0, 44), '¿Se las lleva?': (0, 44), FUNDADOR: (54, 104), 'El fundador': (54, 104),
           'fue por la foto.': (54, 104), '¿Y esta?': (120, 141), 'so f★cking close.': (255, 284),
           'Llevala hasta donde rompe.': (285, 317), 'link en bio': (285, 317)}


def remux_audio(master, wav, out):
    """misma salida de audio y metadatos que video.master, copiando el flujo de video de `master` (sin recodificar).
    Motivo: x264 con VBV y 4 hilos no da el mismo flujo en dos corridas con la misma entrada (medido el 18/11/2026:
    c0–c122 iguales, desde c123 PSNR 42–47 dB); así la versión sin música lleva EXACTAMENTE el video de la completa."""
    V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(master), '-i', str(wav), '-map', '0:v:0', '-map', '1:a:0',
          '-c:v', 'copy', '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
          '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
          '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
          '-shortest', '-movflags', '+faststart', str(out)])
    return out


def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    for hook in ('A', 'B'):
        a = V.ass(textos(hook), T / f'vir01_textos_{hook}.ass')
        out = MAS / NOMBRES[hook]; out_sm = MAS / NOMBRES[f'{hook}_sinmusica']
        for o in (out, out_sm):
            if o.exists():
                raise RuntimeError(f'{o} ya existe: no se sobrescribe')
        V.master(VID, A / 'vir01_completa.wav', out, ass_path=a)
        remux_audio(out, A / 'vir01_sinmusica.wav', out_sm)
        print('->', out, out_sm, flush=True)


# =====================================================================================================
# etapa 6 · control y evidencia (evidencia_v01/)
# =====================================================================================================
EVID = T / 'evidencia_v01'
CORTES = [45, 105, 150, 210, 240]
RANGOS_HOJA = [(0, 12), (36, 48), (100, 110), (140, 160), (205, 215), (236, 260), (280, 317)]
TRAMOS = [('1 apuesta + pregunta (4631)', 0.0, 1.5), ('2 revelación + groove (7887)', 1.5, 3.5),
          ('3 reenganche + pregunta 2 (7884)', 3.5, 5.0), ('4 giro (7857)', 5.0, 7.0), ('5 pista (3453)', 7.0, 8.0),
          ('6 resolución + giro 2 + CTA (4631)', 8.0, 10.6), ('último 0,5 s', 10.1, 10.6)]
# (nombre, primer y último cuadro del golpe según el guion, primer y último cuadro mostrados en la tabla por cuadro)
GOLPES = [('c32–c44 (4631, hueco 1)', 32, 44, 28, 48), ('c138–c144 (7884, hueco 2)', 138, 144, 134, 150),
          ('c240–c252 (4631, hueco 3)', 240, 252, 234, 256)]
PRODUCTO_PARCHES = dict(blanca_espalda_estudio=(292, 1316, 877, 1755), negra_espalda_estudio=(292, 1228, 877, 1462),
                        negra_frente_detalle_estampado=(378, 1550, 1134, 1950))
# parches de tela lisa (sin estampado) en el máster; «sol» y «sombra» por separado: la sombra refleja el cielo
MASTER_PARCHES = {'blanca_4631_c20_sol': (20, (90, 1360, 270, 1500)), 'negra_4631_c20': (20, (640, 1420, 940, 1560)),
                  'blanca_7887_c90_sol': (90, (330, 940, 520, 1020)),
                  'blanca_7884_c125_sol': (125, (230, 1000, 420, 1080)), 'blanca_7884_c125_sombra': (125, (300, 1250, 800, 1420)),
                  'blanca_7884_c140_media': (140, (400, 1250, 700, 1400)),
                  'blanca_7857_c190_nublado': (190, (360, 1360, 700, 1560)),
                  'negra_7887_c95': (95, (650, 1250, 950, 1400)), 'negra_3453_c225': (225, (60, 120, 480, 560)),
                  'negra_4631_c270': (270, (640, 1420, 940, 1560)), 'blanca_4631_c270': (270, (260, 1350, 460, 1500))}


def db_(x):
    return round(float(20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-12)), 1)


def tabla_niveles(mp4_c, mp4_s):
    """RMS cada 0,1 s (dBFS, mezcla mono de los dos canales) de las capas con la ganancia final de la completa (antes del
    limitador) y del total decodificado de los MP4 (completa y sin música)."""
    import soundfile as sf
    cap = {k: sf.read(str(A / f'capa_{k}.wav'))[0].mean(1) for k in ('mus', 'mus_fx', 'fx', 'amb')}
    tc = U.audio_np(mp4_c).mean(1); ts = U.audio_np(mp4_s).mean(1)
    w = 4800; fil = []
    for i in range(106):
        sl = slice(i * w, (i + 1) * w); t0 = i / 10
        nota = []
        for h0, h1 in HUECOS:
            if h0 - 1e-6 <= t0 < h1 - 1e-6 or (t0 < h0 < t0 + 0.1):
                nota.append(f'hueco {h0:.2f}–{h1:.2f}')
        for nom, a, b, _, _ in GOLPES:
            if a / FPS - 1e-6 < t0 + 0.1 and t0 < (b + 1) / FPS - 1e-6:
                nota.append('golpe ' + nom.split(' ')[0])
        fil.append(dict(t=f'{t0:.1f}–{t0 + 0.1:.1f}', cuadros=f'c{round(t0 * FPS)}–c{round((t0 + 0.1) * FPS) - 1}',
                        mus=db_(cap['mus'][sl]), mus_reverb=db_(cap['mus_fx'][sl]),
                        musica_total=db_(cap['mus'][sl] + cap['mus_fx'][sl]), fx_foley=db_(cap['fx'][sl]),
                        amb=db_(cap['amb'][sl]), total_completa_mp4=db_(tc[sl]), total_sinmusica_mp4=db_(ts[sl]),
                        nota=', '.join(nota)))
    return fil


def huecos_resumen():
    import soundfile as sf
    MU = sf.read(str(A / 'capa_mus.wav'))[0]; MF = sf.read(str(A / 'capa_mus_fx.wav'))[0]
    mu = MU.mean(1); mf = MF.mean(1)          # mono (L+R)/2, como las mediciones de Roma (archivo 06)
    est = MU + MF                              # potencia estéreo (promedio de L y R): las colas decorrelacionadas dan hasta 3 dB más
    out = []
    for h0, h1 in HUECOS:
        a, b = int(h0 * 48000), int(h1 * 48000); p = int((h0 - 0.3) * 48000)
        v = [db_((mu + mf)[k:k + 4800]) for k in range(a, b - 2400, 4800)]
        out.append(dict(hueco=f'{h0:.2f}–{h1:.2f}', mus_pista_rms=db_(mu[a:b]), mus_pista_pico=round(float(20 * np.log10(np.abs(mu[a:b]).max() + 1e-12)), 1),
                        musica_con_reverb_rms=db_((mu + mf)[a:b]), musica_con_reverb_peor_100ms=max(v),
                        musica_300ms_antes=db_((mu + mf)[p:a]), bajada_media_db=round(db_((mu + mf)[p:a]) - db_((mu + mf)[a:b]), 1),
                        estereo_musica_con_reverb_rms=db_(est[a:b]),
                        estereo_musica_con_reverb_peor_100ms=max(db_(est[k:k + 4800]) for k in range(a, b - 2400, 4800))))
    return out


def golpes_por_cuadro():
    """RMS y pico por cuadro (33,3 ms) del ambiente y del total en los tramos de golpe, y la correlación entre el ambiente
    de c32–c44 y el de c240–c252 (mismo segmento de 4631)."""
    import soundfile as sf
    amb = sf.read(str(A / 'capa_amb.wav'))[0].mean(1)
    tot = U.audio_np(MAS / NOMBRES['A']).mean(1)
    sp = 1600; out = {}
    for nom, g0, g1, a, b in GOLPES:
        out[nom] = [dict(cuadro=c, en_el_golpe=(g0 <= c <= g1), amb_rms=db_(amb[c * sp:(c + 1) * sp]),
                         amb_pico=round(float(20 * np.log10(np.abs(amb[c * sp:(c + 1) * sp]).max() + 1e-12)), 1),
                         total_rms=db_(tot[c * sp:(c + 1) * sp])) for c in range(a, b + 1)]
    x = amb[32 * sp:45 * sp]; y_ = amb[240 * sp - 200:253 * sp + 200]
    best = (-1, 0)
    for lag in range(0, 401):
        yy = y_[lag:lag + len(x)]
        r = float(np.dot(x, yy) / (np.linalg.norm(x) * np.linalg.norm(yy) + 1e-12))
        if r > best[0]:
            best = (r, lag - 200)
    out['c32_vs_c240'] = dict(correlacion_max=round(best[0], 4), desfase_muestras=best[1],
                              nota='ambiente 4631: c32 = fuente 2,433 + 1,0667 = 3,4997 s; c240 = fuente 3,500 s')
    return out


def ass_textos(path):
    import re
    return [re.sub(r'\{[^}]*\}', '', l.split(',,0,0,0,,', 1)[1]) for l in Path(path).read_text(encoding='utf-8').splitlines()
            if l.startswith('Dialogue:')]


def cajas_por_texto(textos_, carpeta):
    """caja dibujada (texto + borde/caja) de cada texto renderizado solo, en su cuadro medio."""
    out = {}
    for i, t in enumerate(textos_):
        a, b = round(t['t0'] * FPS), round(t['t1'] * FPS) - 1
        _, g = U2.mascara_texto(t, max(0.0, ((a + b) // 2) / FPS - 0.004), carpeta, f'caja_{i}', dil=0)
        ys, xs = np.nonzero(g)
        out[t['txt']] = dict(cuadros=f'c{a}–c{b}', caja=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                             dentro_y_220_480=bool(ys.min() >= 220 and ys.max() <= 480))
    return out


def pop_hook(t, carpeta):
    """caja del hook en c0..c6 y c10 (render del .ass solo): el pop tiene que haber terminado a más tardar en c6."""
    p = carpeta / 'pop.ass'; V.ass([t], p)
    out = {}
    for n in list(range(0, 7)) + [10]:
        r = U.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=black:s=1080x1920:r=30:d=2', '-vf',
                   f"subtitles={p}:fontsdir=/usr/share/fonts/opentype/inter,trim=start_frame={n}:end_frame={n + 1},format=gray",
                   '-frames:v', '1', '-f', 'rawvideo', '-'])
        g = np.frombuffer(r, np.uint8).reshape(1920, 1080) > 8
        ys, xs = np.nonzero(g)
        out[f'c{n}'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    fin = out['c10']
    out['primer_cuadro_igual_a_c10'] = next((f'c{n}' for n in range(7) if out[f'c{n}'] == fin), None)
    return out


def contraste_caja(img, mask_caja, color_caja):
    """contraste WCAG entre una caja opaca (color sRGB) y el fondo que la rodea (anillo de 4–16 px afuera de la caja)."""
    from scipy import ndimage as nd
    anillo = nd.binary_dilation(mask_caja, iterations=16) & ~nd.binary_dilation(mask_caja, iterations=4)
    p = img[anillo].astype(np.float64)
    Yb = U2.lin(p) @ np.array([0.2126, 0.7152, 0.0722])
    Yc = float(U2.lin(np.array(color_caja, np.float64)) @ np.array([0.2126, 0.7152, 0.0722]))
    r = (np.maximum(Yb, Yc) + 0.05) / (np.minimum(Yb, Yc) + 0.05)
    return dict(caja_fondo_mediana=round(float(np.median(r)), 2), caja_fondo_p10=round(float(np.percentile(r, 10)), 2))


def contrastes(textos_, carpeta):
    out = {}
    t_caja = round(1.05 / (float(U2.lin(20)) + 0.05), 1)
    for i, t in enumerate(textos_):
        a, b = round(t['t0'] * FPS), round(t['t1'] * FPS) - 1
        filas = []
        for n in sorted(set(list(range(a, b + 1, 3)) + [b])):
            mk, g = U2.mascara_texto(t, max(0.0, n / FPS - 0.004), carpeta, f'cont_{i}', dil=8)   # instante exacto del cuadro n
            f = U.leer(VID, W, H, n0=n, n1=n)[0]
            if t['estilo'] in ('Caja', 'CajaN'):
                c = contraste_caja(f, g, (255, 255, 255) if t['estilo'] == 'Caja' else (20, 20, 20))
            else:
                c = U2.contraste_blanco(f, mk)
            filas.append(dict(cuadro=n, **c))
        if t['estilo'] in ('Caja', 'CajaN'):
            res = dict(texto_sobre_caja=f'{t_caja}:1 (' + ('#141414 sobre blanco' if t['estilo'] == 'Caja' else 'blanco sobre #141414') + ')',
                       caja_fondo_mediana_min=min(x['caja_fondo_mediana'] for x in filas),
                       caja_fondo_p10_min=min(x['caja_fondo_p10'] for x in filas))
        else:
            res = dict(blanco_fondo_mediana_min=min(x['contraste_mediana'] for x in filas),
                       blanco_fondo_p10_min=min(x['contraste_p10'] for x in filas),
                       borde=('contorno negro opaco de 6 px (estilo Grande)' if t['estilo'] == 'Grande'
                              else 'contorno negro al 44 % de 1,6 px (estilo Chico)'))
        out[f"{t['txt']} ({t['estilo']}, c{a}–c{b})"] = dict(resumen=res, por_cuadro=filas)
    return out


def blancos_negros(mp4):
    out = {}
    for n in (43, 44, 45, 46, 148, 149, 150, 151):
        Y = leer_Y(mp4, n); out[f'c{n}'] = dict(pct_Y_mayor_igual_200=round(float((Y >= 200).mean() * 100), 2))
    for n in (237, 238, 239, 240):
        Y = leer_Y(mp4, n); out[f'c{n}'] = dict(pct_Y_menor_igual_20=round(float((Y <= 20).mean() * 100), 2))
    out['cumple'] = all(out[f'c{n}']['pct_Y_mayor_igual_200'] >= 90 for n in (44, 45, 149, 150)) and \
        out['c239']['pct_Y_menor_igual_20'] >= 95
    return out


def prendas_y_color(carpeta):
    from PIL import Image, ImageDraw, ImageFont
    m = MAS / NOMBRES['A']
    fr = {n: U.leer(m, W, H, n0=n, n1=n)[0] for n in {v[0] for v in MASTER_PARCHES.values()} | {95, 190, 225, 270}}
    col = {}
    for nom, caja in PRODUCTO_PARCHES.items():
        V.foto_srgb(R / 'PRODUCTO' / f'{nom}.jpg', carpeta / f'{nom}_srgb.png')
        col['producto_' + nom] = U.color_parche(np.asarray(Image.open(carpeta / f'{nom}_srgb.png').convert('RGB')), caja)
    for nom, (n, caja) in MASTER_PARCHES.items():
        col['master_' + nom] = U.color_parche(fr[n], caja)
    # recortes 1:1 de las prendas (Negra en Gianluca, Blanca puesta, relieve, las dos espaldas) con los parches marcados
    fnt = ImageFont.truetype(U.FONT, 26)
    rec = [(95, (480, 860, 1080, 1560), 'c95 Negra en Gianluca (7887)'), (190, (180, 700, 900, 1500), 'c190 Blanca puesta (7857)'),
           (225, (0, 500, 1080, 1700), 'c225 relieve del pecho (3453)'), (270, (0, 950, 1080, 1700), 'c270 las dos espaldas (4631)')]
    ims = []
    for n, (x0, y0, x1, y1), rot in rec:
        im = Image.fromarray(fr[n][y0:y1, x0:x1].copy()); d = ImageDraw.Draw(im)
        for nom, (nn, (a, b, c, e)) in MASTER_PARCHES.items():
            if nn == n:
                d.rectangle([a - x0, b - y0, c - x0, e - y0], outline=(255, 0, 255), width=3)
        d.rectangle([0, 0, 560, 36], fill=(0, 0, 0)); d.text((6, 4), rot + ' · 1:1', font=fnt, fill=(255, 255, 0))
        ims.append(im)
    hh = max(i.height for i in ims); ww = sum(i.width for i in ims) + 6 * len(ims)
    hoja = Image.new('RGB', (ww, hh), (30, 30, 30)); x = 0
    for i in ims:
        hoja.paste(i, (x, 0)); x += i.width + 6
    hoja.save(EVID / 'prendas_c95_c190_c225_c270_1a1.jpg', quality=90)
    return col


def estampados_vs_textos(textos_):
    """fila más alta de prenda o persona en los cuadros de cada texto (máster sin textos) contra el borde inferior del
    texto: 4631 (remeras), 7887 (pelo/espalda de Gianluca: L < 45, componente mayor), 7884 (tope de la Blanca medido)."""
    from scipy import ndimage as nd
    med = json.load(open(T / 'medir.json')); efe = json.load(open(T / 'efectos.json'))
    out = {}
    def tope_oscuro(f, y0=500):
        L = U.luma(f); m = L < 45; m[:y0] = False
        lab, n = nd.label(m)
        if not n:
            return None
        s = nd.sum(m, lab, range(1, n + 1)); return int(np.nonzero((lab == int(np.argmax(s)) + 1).any(1))[0].min())
    tops = {}
    fr = U.leer(VID, W, H, n0=0, n1=38)
    tops['c0–c38 (4631, z 1)'] = min(min(v for v in tope_remeras_4631(f).values() if v) for f in fr)
    v1b = [d for d in med['1b_ventanas'] if d['cuadro'] >= 39]
    tops['c39–c44 (4631, empuje)'] = min(((d['tope_remeras'] - d['ventana'][1]) * H / (d['ventana'][3] - d['ventana'][1]))
                                         for d in v1b if d['remeras_visibles_px'] > 0)
    fr = U.leer(VID, W, H, n0=54, n1=104)
    tops['c54–c104 (7887, pelo de Gianluca)'] = min(tope_oscuro(f) for f in fr)
    tops['c120–c141 (7884, tope de la Blanca)'] = min(d['tope'] for d in med['blanca_7884'] if 3.0 <= d['t_fuente'] <= 3.5) / 2
    tops['c255–c317 (4631, remeras)'] = min(min(v for v in (d['tope_negra'], d['tope_blanca']) if v) for d in efe['degrade']['por_cuadro'])
    out['tope_prenda_o_persona'] = {k: round(v) for k, v in tops.items()}
    return out


def etapa_control():
    import soundfile as sf
    EVID.mkdir(parents=True, exist_ok=True)
    rep = dict(fecha='2026-11-18', pieza='VIR-01 «A nada»', guion='G1 v1', archivos={})
    # --- 1. archivos: decodificación, ffprobe, huellas, sonoridad, niveles por tramo, GPS ---
    for k, nombre in NOMBRES.items():
        f = MAS / nombre
        err = subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-i', str(f), '-f', 'null', '-'],
                             capture_output=True, text=True).stderr.strip()
        pj = json.loads(U.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(f)]))
        json.dump(pj, open(EVID / f'ffprobe_{k}.json', 'w'), indent=1)
        cuerpo = f.read_bytes()
        vs = [x for x in pj['streams'] if x['codec_type'] == 'video'][0]; au = [x for x in pj['streams'] if x['codec_type'] == 'audio'][0]
        niv, v100, sil = U.niveles_tramos(U.audio_np(f), TRAMOS)
        rep['archivos'][k] = dict(
            archivo=nombre, bytes=f.stat().st_size, sha256=hashlib.sha256(cuerpo).hexdigest(),
            md5_video=U.md5_stream(f, 'v'), md5_audio=U.md5_stream(f, 'a'),
            decodifica_completo=(err == ''), errores_decodificacion=err[:500],
            video=dict(codec=vs['codec_name'], perfil=vs.get('profile'), nivel=vs.get('level'), pix_fmt=vs['pix_fmt'],
                       ancho=vs['width'], alto=vs['height'], fps=vs['r_frame_rate'], cuadros=int(vs['nb_frames']),
                       duracion=float(vs['duration']), bitrate=int(vs['bit_rate']),
                       color=[vs.get('color_range'), vs.get('color_space'), vs.get('color_transfer'), vs.get('color_primaries')]),
            audio=dict(codec=au['codec_name'], perfil=au.get('profile'), hz=int(au['sample_rate']), canales=au['channels'],
                       duracion=float(au['duration'])),
            faststart=cuerpo.find(b'moov') < cuerpo.find(b'mdat'),
            etiquetas_formato=pj['format'].get('tags', {}),
            marcas_gps_o_ubicacion=[m.decode() for m in (b'ISO6709', b'location', b'com.apple.quicktime') if m in cuerpo],
            sonoridad=U.ebur(f), niveles_por_tramo=niv, ventanas_100ms_bajo_menos50dbfs=sil)
        r = rep['archivos'][k]
        print(k, r['bytes'], r['md5_video'], r['md5_audio'], r['sonoridad'], r['video']['cuadros'], r['video']['duracion'],
              r['audio']['duracion'], 'dec', r['decodifica_completo'], 'gps', r['marcas_gps_o_ubicacion'], 'fs', r['faststart'],
              'sil', sil, flush=True)
    (EVID / 'decodificacion_completa.txt').write_text(''.join(
        f"{v['archivo']}: ffmpeg -v error -i … -f null - → {'sin errores' if v['decodifica_completo'] else v['errores_decodificacion']} "
        f"({v['video']['cuadros']} cuadros, video {v['video']['duracion']:.3f} s, audio {v['audio']['duracion']:.3f} s)\n"
        for v in rep['archivos'].values()), encoding='utf-8')
    (EVID / 'ebur128.txt').write_text(''.join(
        f"{v['archivo']}: integrado {v['sonoridad']['lufs_integrado']} LUFS · pico real {v['sonoridad']['pico_dbtp']} dBTP · "
        f"LRA {v['sonoridad']['lra']} LU\n" for v in rep['archivos'].values()), encoding='utf-8')
    # --- 2. hojas por cuadro, hoja cada 0,5 s y cortes ---
    mA = MAS / NOMBRES['A']; mB = MAS / NOMBRES['B']
    for a, b in RANGOS_HOJA:
        F4.hoja_c(mA, EVID / f'hoja_A_c{a}-c{b}.jpg', cada=1 / FPS, ancho=216 if b - a < 30 else 180, cols=10 if b - a < 30 else 13,
                  t0=a / FPS, t1=b / FPS)
    F4.hoja_c(mB, EVID / 'hoja_B_c0-c12.jpg', cada=1 / FPS, ancho=216, cols=10, t0=0, t1=12 / FPS)
    U.hoja_contacto(mA, EVID / 'hoja_A_cada_0.5s.jpg', cada=15, cols=8, ancho=240)
    U.hoja_contacto(mB, EVID / 'hoja_B_cada_0.5s.jpg', cada=15, cols=8, ancho=240)
    U.cuadros_corte(mA, CORTES, EVID / 'cortes', NF - 1)
    # --- 3. sonido: tabla de niveles cada 0,1 s, huecos, golpes ---
    tn = tabla_niveles(mA, MAS / NOMBRES['A_sinmusica'])
    json.dump(tn, open(EVID / 'niveles_0.1s.json', 'w'), ensure_ascii=False, indent=0)
    cols = ['t', 'cuadros', 'mus', 'mus_reverb', 'musica_total', 'fx_foley', 'amb', 'total_completa_mp4', 'total_sinmusica_mp4', 'nota']
    fmt = lambda v: ('silencio' if isinstance(v, float) and v < -200 else (f'{v:.1f}'.replace('.', ',') if isinstance(v, float) else str(v)))
    md = ['# VIR-01 · niveles cada 0,1 s (RMS, dBFS) · medido, no escuchado', '',
          '`mus` = pista de música (sintes, 808, palmas, charles) con el bombo y el bombeo, con la ganancia final de la '
          'completa, antes del limitador. `mus_reverb` = colas de reverberación de la música y subidas (pista fx de la '
          'mezcla musical). `fx_foley` = tela, barrido, obturador y toque. `amb` = ambiente real de las tomas. Los dos '
          'totales se decodificaron de los MP4 entregados (A y A sin música). «silencio» = silencio digital.', '',
          '| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    md += ['| ' + ' | '.join(fmt(r[c]) for c in cols) + ' |' for r in tn]
    (EVID / 'niveles_0.1s.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    with open(EVID / 'niveles_0.1s.csv', 'w', encoding='utf-8') as fh:
        fh.write(';'.join(cols) + '\n')
        for r in tn:
            fh.write(';'.join(str(r[c]) for c in cols) + '\n')
    rep['huecos'] = huecos_resumen()
    rep['golpes'] = golpes_por_cuadro()
    json.dump(rep['golpes'], open(EVID / 'golpes_por_cuadro.json', 'w'), ensure_ascii=False, indent=1)
    mom = {k: U2.momentanea(MAS / NOMBRES[k]) for k in ('A', 'A_sinmusica')}
    tramos_m = [('apuesta 0,0–0,95', 0.0, 0.95), ('hueco 1 + golpe 0,95–1,5', 0.95, 1.5), ('groove 1,5–3,5', 1.5, 3.5),
                ('tensión 3,5–4,45', 3.5, 4.45), ('hueco 2 + golpe 4,45–5,5', 4.45, 5.5), ('drop 2 5,5–7,0', 5.5, 7.0),
                ('pista 7,0–7,8', 7.0, 7.8), ('hueco 3 + golpe 7,8–8,5', 7.8, 8.5), ('drop 3 8,5–9,5', 8.5, 9.5),
                ('CTA 9,5–10,6', 9.5, 10.6)]
    rep['sonoridad_momentanea_por_tramo'] = {k: U2.momentanea_tramos(v, tramos_m) for k, v in mom.items()}
    # --- 4. blancos y negros (en los cuatro másteres) ---
    rep['blancos_negros'] = {k: blancos_negros(MAS / n) for k, n in NOMBRES.items()}
    # --- 5. textos: exactos, posición, cuadros, pop, contraste, estampados ---
    S = T / 'ctrl'; S.mkdir(exist_ok=True)
    tx = {}
    for hook in ('A', 'B'):
        ts = textos(hook); ap = T / f'vir01_textos_{hook}.ass'
        shutil.copy2(ap, EVID / ap.name)
        enc = ass_textos(ap)
        esperado = [t['txt'] for t in ts]
        lim, ok = U2.textos_limites(MAS / NOMBRES[hook], VID, ts, [LIMITES[t['txt']] for t in ts], NF, S)
        tx[hook] = dict(textos_en_ass=enc, iguales_a_los_del_guion=(enc == esperado),
                        estrella=[f'U+{ord(c):04X}' for t in enc for c in t if ord(c) > 0x2000],
                        cajas=cajas_por_texto(ts, S), textos_limites=lim, cuadros_ok=ok, pop=pop_hook(ts[0], S))
        print(hook, enc, 'cuadros_ok', ok, 'pop', tx[hook]['pop']['primer_cuadro_igual_a_c10'], flush=True)
    tx['contraste'] = {'A': contrastes(textos('A'), S), 'B_hook': contrastes(textos('B')[:1], S)}
    tx['estampados'] = estampados_vs_textos(textos('A'))
    rep['textos'] = tx
    # --- 6. prendas y color ---
    rep['color'] = prendas_y_color(S)
    # --- 7. copias de las mediciones previas ---
    for f in ('medir.json', 'efectos.json', 'planos.json', 'dif_consecutiva.json', 'gotas_4631_c110-c118_ventana_1a1.jpg'):
        shutil.copy2(T / f, EVID / f)
    for f in ('4631_c111-c115_791_1157_x4.jpg', '4631_c109-c120_3.63-4.0.jpg', '7884_c105-c114_3.5-3.8.jpg',
              '3453_c90-c99_3.0-3.3.jpg', '7857_c0-c12_0.0-0.4.jpg', '4631_c180-c186_6.0-6.2.jpg'):
        shutil.copy2(T / 'hojas' / f, EVID / f'hoja_fuente_{f}')
    for k in ('completa', 'sinmusica'):
        shutil.copy2(A / f'vir01_{k}_eventos.json', EVID / f'audio_eventos_{k}.json')
    shutil.copy2(A / 'audio.json', EVID / 'audio.json')
    json.dump(rep, open(EVID / 'control.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: rep[k] for k in ('huecos', 'blancos_negros')}, ensure_ascii=False))
    print(json.dumps(rep['golpes']['c32_vs_c240'], ensure_ascii=False))
    print(json.dumps({h: {k: v for k, v in tx[h].items() if k in ('cajas', 'pop', 'estrella', 'iguales_a_los_del_guion')} for h in ('A', 'B')}, ensure_ascii=False))
    print(json.dumps({k: v['resumen'] for k, v in tx['contraste']['A'].items()}, ensure_ascii=False))
    print(json.dumps({k: v['resumen'] for k, v in tx['contraste']['B_hook'].items()}, ensure_ascii=False))
    print(json.dumps(tx['estampados'], ensure_ascii=False))
    print(json.dumps(rep['color'], ensure_ascii=False))
    print(json.dumps(rep['sonoridad_momentanea_por_tramo'], ensure_ascii=False))


# ------------------------------------------------------------------------------------------------------------------
# Entrega: EXPORTACIONES/ (copia exacta: bytes + sha256 + md5 de flujos) y carpeta de la pieza (montaje de red que
# agrega una caja C2PA: bytes y sha256 cambian; se verifican md5 de los flujos v/a y la decodificación completa).
# ------------------------------------------------------------------------------------------------------------------
def _huella(p, sha=True):
    d = dict(bytes=p.stat().st_size, md5_video=U.md5_stream(p, 'v'), md5_audio=U.md5_stream(p, 'a'))
    if sha:
        d['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
    return d


def _decodifica(p):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'null', '-'], capture_output=True, text=True)
    return r.returncode == 0 and r.stderr.strip() == ''


def etapa_entregar():
    destinos = []
    for k, nombre in NOMBRES.items():
        for d in (EXP / nombre, PIEZA / nombre):
            if d.exists():
                raise RuntimeError(f'{d} ya existe: no se sobrescribe')
            destinos.append((MAS / nombre, d))
    ev_red = PIEZA / 'evidencia_v01'
    if ev_red.exists():
        raise RuntimeError(f'{ev_red} ya existe')
    for src, d in destinos:
        shutil.copyfile(src, d)
    shutil.copytree(EVID, str(ev_red) + '/')
    time.sleep(12)                                   # montaje de red: esperar antes de verificar
    res = dict(local={}, exportaciones={}, pieza={})
    for k, nombre in NOMBRES.items():
        ref = _huella(MAS / nombre)
        res['local'][nombre] = ref
        e = _huella(EXP / nombre)
        res['exportaciones'][nombre] = dict(e, igual=(e == ref), decodifica=_decodifica(EXP / nombre))
        p = _huella(PIEZA / nombre)
        res['pieza'][nombre] = dict(p, flujos_iguales=(p['md5_video'] == ref['md5_video'] and
                                                         p['md5_audio'] == ref['md5_audio']),
                                    bytes_extra_c2pa=p['bytes'] - ref['bytes'], decodifica=_decodifica(PIEZA / nombre))
        print(nombre, 'EXP', res['exportaciones'][nombre]['igual'], res['exportaciones'][nombre]['decodifica'],
              '| PIEZA flujos', res['pieza'][nombre]['flujos_iguales'], '+', res['pieza'][nombre]['bytes_extra_c2pa'],
              'B', res['pieza'][nombre]['decodifica'])
    loc = sorted(str(f.relative_to(EVID)) for f in EVID.rglob('*') if f.is_file())
    red = sorted(str(f.relative_to(ev_red)) for f in ev_red.rglob('*') if f.is_file())
    tam = {f: ((EVID / f).stat().st_size, (ev_red / f).stat().st_size) for f in loc if (ev_red / f).exists()}
    res['evidencia'] = dict(carpeta=str(ev_red) + '/', archivos_local=len(loc), archivos_red=len(red),
                            faltan=[f for f in loc if f not in red],
                            tamanos_distintos={f: v for f, v in tam.items() if v[0] != v[1]})
    print('evidencia', len(loc), len(red), res['evidencia']['faltan'], list(res['evidencia']['tamanos_distintos']))
    json.dump(res, open(T / 'entrega.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    {'medir': etapa_medir, 'planos': etapa_planos, 'efectos': etapa_efectos, 'audio': etapa_audio, 'master': etapa_master,
     'control': etapa_control, 'entregar': etapa_entregar}[etapa]()
