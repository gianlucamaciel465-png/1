#!/usr/bin/env python3
"""Roccé Life · V2 «Fichate vos» · receta del máster v01, solo hook A (Pedro, 24/11/2026).

Guion: piezas/LIFE_rocce_life/V2_fichate_vos/01_fede_guion_G1.md (G1 v1) + 02_roma_aprobacion_G1.md (condiciones).
Usa sin modificarlos scripts/fmt/video.py (color, plano, unir, ass, master), fmt03.py (plano_n, plano_z, desde_cuadro,
leer, hoja_src, md5_stream, ebur, audio_np, niveles_tramos, cuadros_corte, hoja_contacto, cajas_texto) y sonido.py
(Mezcla). Lo que hace falta y no está ahí (medición de «Founders Privée» copiada de scripts/vir/vir02n_v02.py, control
de muñeca en 7824, neutralización de la Blanca solo sobre la Blanca, placa PNG transparente) vive acá o en
life_v2_render.js (copia de scripts/life/render.js con fondo transparente).

Etapas (con nice -n 10 y el python de TRABAJO/venv):
  hojas → medir → planos → color → placa → audio → master → control → entregar
Intermedios en TRABAJO/life/v2/. Nada se publica; sin servicios externos ni créditos.
"""
import json, math, subprocess, sys, hashlib, shutil, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V          # noqa: E402
import fmt03 as U          # noqa: E402

R = Path('/home/user/1')
T = R / 'TRABAJO/life/v2'
HJ = T / 'hojas'
MED = T / 'med'
P = T / 'planos'
A = T / 'audio'
MAS = T / 'master'
EVID = T / 'evidencia_v01'
EXP = R / 'EXPORTACIONES'
PIEZA = Path('/mnt/project-files/piezas/LIFE_rocce_life/V2_fichate_vos')
FPS, W, H = 30, 1080, 1920
NF = 281
DUR = NF / FPS                      # 9,3667 s
FONT = U.FONT
SR = 48000
NOMBRES = {'completa': 'ROCCE_LIFE_V2_FICHATE_VOS_v01.mp4', 'sinmusica': 'ROCCE_LIFE_V2_FICHATE_VOS_SINMUSICA_v01.mp4'}


def nice(cmd):
    return ['nice', '-n', '10'] + list(cmd)


# Máquina compartida con V1: los ffmpeg que lanza video.py (plano, unir, master) pasan por acá con nice y 2 hilos
# (decodificador, filtros y codificador). video.py no se modifica: se envuelve V.sh en este proceso.
import shlex as _shlex
_SH0 = V.sh


def _sh_hilos(cmd, **kw):
    if isinstance(cmd, str):
        cmd = _shlex.split(cmd)
    cmd = list(cmd)
    if cmd and cmd[0] == 'ffmpeg':
        cmd = ['nice', '-n', '10', 'ffmpeg', '-threads', '2', '-filter_threads', '2'] + cmd[1:-1] + ['-threads', '2', cmd[-1]]
    return _SH0(cmd, **kw)


V.sh = _sh_hilos


def jdump(obj, f):
    Path(f).parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(f, 'w'), ensure_ascii=False, indent=1)


# =====================================================================================================
# etapa hojas · cuadro a cuadro de los tramos críticos (§6 del guion: «hojas cada 0,1 s»; acá cada cuadro)
# =====================================================================================================
def etapa_hojas():
    HJ.mkdir(parents=True, exist_ok=True)
    U.hoja_src('IMG_7824', 24, 59, HJ / '7824_c24-c59_c1.jpg', cada=1, ancho=216, cols=12)            # 0,8–1,97
    U.hoja_src('IMG_7887', 27, 45, HJ / '7887_c27-c45_c1.jpg', cada=1, ancho=216, cols=10)            # 0,9–1,5
    U.hoja_src('IMG_7885', 84, 96, HJ / '7885_c84-c96_c1.jpg', cada=1, ancho=216, cols=13)            # 2,8–3,2
    U.hoja_src('IMG_7885', 60, 132, HJ / '7885_c60-c132_c3.jpg', cada=3, ancho=216, cols=13)          # plano 3
    U.hoja_src('IMG_7896', 108, 183, HJ / '7896_caja_c108-c183_c3.jpg', cada=3, ancho=180, cols=13,
               caja=(100, 300, 1800, 3200))                                                          # 3,6–6,1


# =====================================================================================================
# medición de «Founders Privée» (copiado de scripts/vir/vir02n_v02.py: estampado/seguir, sin cambios de criterio)
# =====================================================================================================
def estampado(img, tipo, roi, tam=41, lf_max=70, dl_min=55, media_max=110, min_frac=0.0, excluir=()):
    """«Founders Privée» en un cuadro 1080×1920 RGB (uint8); ver vir02n_v02.estampado. Blanca: celeste contra el fondo
    local (cierre en gris); Negra: letra = L − Lf > dl_min con Lf (apertura en gris) < lf_max, sat < 0,25 y media local
    < media_max. Agrupa trazos (dilatación 8), queda el grupo mayor y los vecinos ≥ 3 %. Devuelve caja y máscara."""
    from scipy import ndimage as nd
    f = img.astype(np.float32)
    x0, y0, x1, y1 = [int(round(v)) for v in roi]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W - 1, x1), min(H - 1, y1)
    pad = tam
    ya, yb, xa, xb = max(0, y0 - pad), min(H, y1 + pad + 1), max(0, x0 - pad), min(W, x1 + pad + 1)
    sub = f[ya:yb, xa:xb]
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    L = 0.2126 * r + 0.7152 * g + 0.0722 * b
    sat = (sub.max(-1) - sub.min(-1)) / (sub.max(-1) + 1)
    if tipo == 'blanca':
        bg = [nd.grey_closing(c, size=(tam, tam)) + 1 for c in (r, g, b)]
        Lf = 0.2126 * bg[0] + 0.7152 * bg[1] + 0.0722 * bg[2]
        d = b / bg[2] - r / bg[0]
        d = d - nd.grey_opening(d, size=(61, 61))
        dentro = np.zeros_like(d, bool); dentro[y0 - ya:y1 - ya + 1, x0 - xa:x1 - xa + 1] = True
        thr = max(0.06, 0.45 * float(np.percentile(d[dentro & (Lf > 140)], 99.5))) if (dentro & (Lf > 140)).any() else 0.06
        m = (d > thr) & (L / Lf > 0.72) & (Lf > 140)
    else:
        Lf = nd.grey_opening(L, size=(tam, tam))
        m = ((L - Lf) > dl_min) & (Lf < lf_max) & (sat < 0.25) & (nd.uniform_filter(L, size=tam) < media_max)
    m = nd.binary_opening(m, iterations=1)
    full = np.zeros((H, W), bool); full[ya:yb, xa:xb] = m
    lim = np.zeros((H, W), bool); lim[y0:y1 + 1, x0:x1 + 1] = True
    full &= lim
    for ex0, ey0, ex1, ey1 in excluir:
        full[ey0:ey1 + 1, ex0:ex1 + 1] = False
    if min_frac > 0 and full.any():
        lab0, n0_ = nd.label(full)
        s0 = nd.sum(full, lab0, np.arange(1, n0_ + 1))
        full &= np.isin(lab0, 1 + np.nonzero(s0 >= min_frac * full.sum())[0])
    lab, n = nd.label(nd.binary_dilation(full, iterations=8))
    if n == 0:
        return None, full
    idx = np.arange(1, n + 1)
    s_ = nd.sum(full, lab, idx)
    k = int(np.argmax(s_)) + 1
    sl = nd.find_objects(lab)
    gy0, gy1, gx0, gx1 = sl[k - 1][0].start, sl[k - 1][0].stop, sl[k - 1][1].start, sl[k - 1][1].stop
    gw, gh = gx1 - gx0, gy1 - gy0
    cm = nd.center_of_mass(full, lab, idx)
    keep = [i + 1 for i in range(n) if i + 1 == k or (s_[i] >= 0.03 * s_[k - 1] and
            gx0 - 0.15 * gw <= cm[i][1] <= gx1 + 0.15 * gw and gy0 - 0.6 * gh <= cm[i][0] <= gy1 + 0.6 * gh)]
    full &= np.isin(lab, keep)
    rows = full.sum(1); ok = np.nonzero(rows >= 0.08 * rows.max())[0]
    full[:ok.min()] = False; full[ok.max() + 1:] = False
    ys, xs = np.nonzero(full)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), full


def inclinacion(mask):
    """ángulo (grados, positivo = sube hacia la derecha) del eje principal de los píxeles de la máscara."""
    ys, xs = np.nonzero(mask)
    if len(xs) < 50:
        return None
    x = xs - xs.mean(); y = ys - ys.mean()
    c = np.cov(np.stack([x, y]))
    w, v = np.linalg.eigh(c)
    ax = v[:, np.argmax(w)]
    if ax[0] < 0:
        ax = -ax
    return round(float(-math.degrees(math.atan2(ax[1], ax[0]))), 2)


# clave: (toma, tipo, cuadro inicial, cuadro final, zona inicial en 1080×1920, seguir, parámetros)
MEDIR = {
    'IMG_7824': ('IMG_7824', 'negra', 36, 56, (0, 760, 1079, 1260), True, {}),
    'IMG_7887': ('IMG_7887', 'negra', 27, 48, (420, 880, 1079, 1260), True, dict(lf_max=115, dl_min=60, media_max=150)),
}


def medir_founders(clave, vf_extra=''):
    toma, tipo, n0, n1, roi, seguir, par = MEDIR[clave]
    fr = U.leer(V._src(toma), W, H, n0=n0, n1=n1, vf_pre=V.color(toma))
    s = V.TOMAS[toma]['nat'][0] / W
    filas, masks = [], []
    for k, img in enumerate(fr):
        bb, m = estampado(img, tipo, roi, **par)
        masks.append(m)
        if bb is None:
            filas.append(dict(cuadro_fuente=n0 + k, bbox_1080=None)); continue
        x0, y0, x1, y1 = bb
        filas.append(dict(cuadro_fuente=n0 + k, bbox_1080=[x0, y0, x1, y1],
                          bbox_nat=[x0 * s, y0 * s, (x1 + 1) * s, (y1 + 1) * s],
                          cx_nat=round((x0 + x1 + 1) / 2 * s, 1), cy_nat=round((y0 + y1 + 1) / 2 * s, 1),
                          w_nat=(x1 + 1 - x0) * s, h_nat=(y1 + 1 - y0) * s,
                          centroide_nat=[round(float(np.nonzero(m)[1].mean() * s), 1), round(float(np.nonzero(m)[0].mean() * s), 1)],
                          inclinacion_grados=inclinacion(m), toca_borde_der=bool(x1 >= W - 2), toca_borde_izq=bool(x0 <= 1)))
        if seguir:
            roi = (x0 - 30, y0 - 30, x1 + 30, y1 + 30)
    return fr, masks, filas


def dibujar(frames, masks, filas, salida, rot, ancho=216, cols=7):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 30)
    tiles = []
    for img, m, f in zip(frames, masks, filas):
        ov = img.copy(); ov[m] = [255, 0, 0]
        im = Image.fromarray(ov); d = ImageDraw.Draw(im)
        if f.get('bbox_1080'):
            d.rectangle(f['bbox_1080'], outline=(255, 255, 0), width=4)
        d.rectangle([0, 0, 1079, 44], fill=(0, 0, 0))
        d.text((8, 6), f"{rot} c{f['cuadro_fuente']} {f.get('bbox_1080')} {f.get('inclinacion_grados')}°", font=fnt,
               fill=(255, 255, 0))
        tiles.append(im.resize((ancho, round(ancho * im.height / im.width))))
    th = tiles[0].height; filas_ = math.ceil(len(tiles) / cols)
    Wd = Image.new('RGB', (cols * (ancho + 2), filas_ * (th + 2)), (32, 32, 32))
    for i, t in enumerate(tiles):
        Wd.paste(t, ((i % cols) * (ancho + 2), (i // cols) * (th + 2)))
    Wd.save(salida, quality=90)


# muñeca tatuada de la mano izquierda en 7824 (condición 1 de Roma: «solo dedos, ningún antebrazo» en c0–c53).
# Medido en 4K (coordenadas naturales) en la zona x 0–400, y 1200–1600: piel (r > 120, r − b > 25, r ≥ g, cerrada 8 px);
# tatuaje = trazo gris dentro de la piel, más oscuro que su entorno (L < cierre(L, 25 px) − 15, sat < 0,30), en x < 260 y
# y 1270–1520 (arriba quedan los pliegues de los nudillos). Grupos < 40 px afuera. Se informa el borde derecho por cuadro.
MUNECA = dict(zona=(0, 1200, 400, 1600), x_max=260, y=(1270, 1520), margen=60)


def tatuaje_7824(n0=0, n1=56):
    from scipy import ndimage as nd
    x0, y0, x1, y1 = MUNECA['zona']
    fr = U.leer(V._src('IMG_7824'), x1 - x0, y1 - y0, n0=n0, n1=n1,
                vf_pre=V.color('IMG_7824') + f',crop={x1 - x0}:{y1 - y0}:{x0}:{y0}')
    out, vis = [], []
    for k, img in enumerate(fr):
        f = np.asarray(img, np.float32)
        r, g, b = f[..., 0], f[..., 1], f[..., 2]; L = .2126 * r + .7152 * g + .0722 * b
        sat = (f.max(-1) - f.min(-1)) / (f.max(-1) + 1)
        piel = nd.binary_closing((r > 120) & (r - b > 25) & (r >= g), iterations=8)
        Lc = nd.grey_closing(L, size=(25, 25))
        t = piel & (L < Lc - 15) & (sat < 0.30)
        lim = np.zeros_like(t); lim[MUNECA['y'][0] - y0:MUNECA['y'][1] - y0, :MUNECA['x_max']] = True
        t &= lim
        t = nd.binary_opening(t, iterations=1)
        lab, n = nd.label(nd.binary_dilation(t, iterations=3))
        if n:
            s = nd.sum(t, lab, range(1, n + 1)); t &= np.isin(lab, 1 + np.nonzero(s >= 40)[0])
        ys, xs = np.nonzero(t)
        out.append(dict(cuadro_fuente=n0 + k, px=int(t.sum()), x_der_nat=(int(xs.max()) + x0) if len(xs) else None,
                        y_nat=[int(ys.min()) + y0, int(ys.max()) + y0] if len(ys) else None))
        ov = f.astype(np.uint8).copy(); ov[t] = [255, 0, 0]
        vis.append(ov)
    return out, vis


def etapa_medir():
    MED.mkdir(parents=True, exist_ok=True)
    rep = {}
    tat, vis = tatuaje_7824()
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 22)
    Wd = Image.new('RGB', (10 * 202, math.ceil(len(vis) / 10) * 202), (30, 30, 30))
    for i, (v, t) in enumerate(zip(vis, tat)):
        im = Image.fromarray(v).resize((200, 200)); d = ImageDraw.Draw(im)
        d.text((4, 4), f"c{t['cuadro_fuente']} x≤{t['x_der_nat']}", font=fnt, fill=(255, 255, 0))
        Wd.paste(im, ((i % 10) * 202, (i // 10) * 202))
    Wd.save(MED / 'muneca_7824_c0-c56.jpg', quality=90)
    rep['tatuaje_7824'] = tat
    print('tatuaje', [(t['cuadro_fuente'], t['x_der_nat']) for t in tat], flush=True)
    for clave in MEDIR:
        fr, masks, filas = medir_founders(clave)
        dibujar(fr, masks, filas, MED / f'founders_{clave}.jpg', clave[4:])
        rep[clave] = filas
        for f in filas:
            print(clave, f['cuadro_fuente'], f.get('bbox_nat'), 'w', f.get('w_nat'), 'c', f.get('cx_nat'), f.get('cy_nat'),
                  'incl', f.get('inclinacion_grados'), 'borde', f.get('toca_borde_izq'), f.get('toca_borde_der'), flush=True)
    jdump(rep, MED / 'founders.json')


# =====================================================================================================
# etapa planos · tabla §2 del guion con las mediciones (corte por coincidencia de letras c53 → c54)
# =====================================================================================================
FULL = (0, 0, 2160, 3840)
NW, NH = 2160, 3840
ANCHO_OBJ = 1.02          # «Founders Privée» = 102 % del ancho del cuadro en c53 y c54 (validación: 95–110 %)
# 1a · DESVÍO medido: la muñeca tatuada de la mano izquierda entra por el borde izquierdo en c43 (≈ 7 px de 4K; hoja
# 7824_muneca_c30-c53_1a1.jpg) y crece desde c46. Con z 1,0 en c43 se vería. 1a va a z 1,03 anclado a la derecha
# (recorte de 63 px a la izquierda y 56 arriba y abajo, en 4K): nada de la imagen cambia salvo ese borde.
Z1A = 1.03
X1A, Y1A = NW - NW / Z1A, (NH - NH / Z1A) / 2
# medición de «Founders Privée» (etapa medir; caja = letras + rúbrica, coordenadas 4K): 7824 c53 y 7887 c30
F7824_C53 = dict(bbox=[366, 1910, 1716, 2294])
F7887_C30 = dict(bbox=[1244, 2124, 1790, 2284])


def ventana_founders(bb, ancho=ANCHO_OBJ):
    """ventana 9:16 (x, y, w, h) en 4K que deja la caja `bb` con `ancho` × 1080 px y centrada en el cuadro."""
    x0, y0, x1, y1 = bb
    w = (x1 - x0) / ancho; h = w * NH / NW
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return cx - w / 2, cy - h / 2, w, h


def interp_ventanas(va, vb, s_log):
    """ventanas intermedias: log Z interpolado con s_log (lista 0..1) y la ventana anclada al punto fijo entre va y vb
    (acercamiento recto, sin deriva lateral)."""
    za, zb = NW / va[2], NW / vb[2]
    out = []
    for s in s_log:
        z = math.exp(math.log(za) + (math.log(zb) - math.log(za)) * s); w = NW / z; h = NH / z
        sr = (w - va[2]) / (vb[2] - va[2]) if vb[2] != va[2] else s
        out.append((va[0] + (vb[0] - va[0]) * sr, va[1] + (vb[1] - va[1]) * sr, w, h))
    return out


def plan_planos():
    v1a = (X1A, Y1A, NW / Z1A, NH / Z1A)
    v53 = ventana_founders(F7824_C53['bbox'])
    v1b = interp_ventanas(v1a, v53, [((k + 1) / 10) ** 2 for k in range(10)])          # ease-in, c44–c53
    v54 = ventana_founders(F7887_C30['bbox'])
    v2a = interp_ventanas(v54, (0, 0, NW, NH), [1 - (1 - k / 11) ** 2 for k in range(12)])  # ease-out, c54–c65
    zc = lambda vs: ([NW / v[2] for v in vs], [v[0] + v[2] / 2 for v in vs], [v[1] + v[3] / 2 for v in vs])
    z1b, x1b, y1b = zc(v1b); z2a, x2a, y2a = zc(v2a)
    blur1b = ("avgblur=sizeX=8:enable='eq(n\\,7)',avgblur=sizeX=16:enable='eq(n\\,8)',"
              "avgblur=sizeX=24:enable='eq(n\\,9)'")
    blur2a = "avgblur=sizeX=16:enable='lte(n\\,1)'"
    return [
        dict(id='1a', m0=0, tipo='n', toma='IMG_7824', n0=0, nf=44,
             caja=(round(X1A), round(Y1A), round(NW / Z1A), round(NW / Z1A * 16 / 9))),
        dict(id='1b', m0=44, tipo='z', toma='IMG_7824', n0=44, zs=z1b, cxs=x1b, cys=y1b, post=blur1b),
        dict(id='2a', m0=54, tipo='z', toma='IMG_7887', n0=30, zs=z2a, cxs=x2a, cys=y2a, post=blur2a),
        dict(id='2b', m0=66, tipo='n', toma='IMG_7887', n0=42, nf=68, caja=FULL),
        dict(id='3', m0=134, tipo='n', toma='IMG_7885', n0=60, nf=72, caja=FULL),
        dict(id='4', m0=206, tipo='n', toma='IMG_7896', n0=108, nf=75, caja=(100, 300, 1800, 3200)),
    ]


def etapa_planos():
    P.mkdir(parents=True, exist_ok=True)
    reg = []
    for p in plan_planos():
        out = P / f"{p['id']}.mp4"
        if p['tipo'] == 'n':
            r = U.plano_n(p['toma'], p['n0'], p['nf'], out, caja=p['caja'])
        else:
            r = U.plano_z(p['toma'], p['n0'], p['zs'], p['cxs'], p['cys'], out, caja=FULL, post=p.get('post'))
            # versión sin desenfoque (solo evidencia: medir «Founders Privée» en c53/c54 sobre la imagen nítida)
            U.plano_z(p['toma'], p['n0'], p['zs'], p['cxs'], p['cys'], P / f"{p['id']}_nitido.mp4", caja=FULL)
        r.update(id=p['id'], m0=p['m0'], post=p.get('post'))
        reg.append(r); print(p['id'], r['cuadros'], flush=True)
    n = V.unir(reg, T / 'v2_base0.mp4')
    assert n == NF, n
    jdump(dict(cuadros=n, planos=reg), T / 'planos.json')
    print('total', n)


# =====================================================================================================
# etapa color · Blanca neutra solo sobre la Blanca (condición 3 de Roma); la Negra no se toca
# =====================================================================================================
# Criterio de scripts/life/pines.py: neutralizar (pines v02, aprobado): ganancias R/G/B por franja de luminancia medidas
# sobre la tela blanca lisa (L > 150, sat < 0,12) del mayor componente conexo de tela clara y neutra dentro de una caja,
# aplicadas solo a neutros claros (sat < 0,10 entera, se apaga hasta 0,15; L desde 120, entera desde 150) y solo sobre ese
# componente (+8 px, borde suavizado 3 px). Acá en video: las ganancias son UNA por toma (mediana de 4 cuadros de
# medición, sin parpadeo) y la máscara de la Blanca se recalcula en cada cuadro. Se reescriben solo los píxeles con peso
# > 0 (luma) y los bloques de croma 2×2 que tocan uno: el resto del cuadro (la Negra, la piel, el mar) queda idéntico.
COLOR = {   # toma: (cuadros del máster, cuadros de medición, caja de búsqueda de la Blanca x0, y0, x1, y1 en 1080×1920)
    'IMG_7887': ((54, 133), (70, 90, 110, 130), (0, 380, 760, 1350)),
    'IMG_7885': ((134, 205), (140, 160, 180, 200), (0, 450, 1080, 1500)),
    'IMG_7896': ((206, 280), (210, 235, 260, 280), (60, 700, 700, 1400)),
}
FRANJAS = [(150, 190), (190, 215), (215, 256)]
KY = np.array([0.2126, 0.7152, 0.0722])


def yuv_rgb(Y, Cb, Cr):
    cb = np.repeat(np.repeat(Cb, 2, 0), 2, 1).astype(np.float32); cr = np.repeat(np.repeat(Cr, 2, 0), 2, 1).astype(np.float32)
    y = (Y.astype(np.float32) - 16) / 219; u = (cb - 128) / 224; v = (cr - 128) / 224
    Rr = y + 1.5748 * v; Bb = y + 1.8556 * u; Gg = (y - 0.2126 * Rr - 0.0722 * Bb) / 0.7152
    return np.stack([Rr, Gg, Bb], -1) * 255.0


def rgb_yuv(rgb):
    r, g, b = rgb[..., 0] / 255, rgb[..., 1] / 255, rgb[..., 2] / 255
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Cb = 128 + 224 * (b - y) / 1.8556; Cr = 128 + 224 * (r - y) / 1.5748
    Cb = Cb.reshape(H // 2, 2, W // 2, 2).mean((1, 3)); Cr = Cr.reshape(H // 2, 2, W // 2, 2).mean((1, 3))
    return 16 + 219 * y, Cb, Cr


def lum_sat(rgb):
    c = np.clip(rgb, 0, 255)
    L = c @ KY.astype(np.float32)
    mx = c.max(-1); mn = c.min(-1)
    return L, (mx - mn) / (mx + 1)


SOLIDEZ_MIN, AREA_MIN = 0.40, 2000


def blanca(rgb, caja):
    """máscara de la Blanca: mayor componente conexo de tela clara y neutra (L > 150, sat < 0,12) dentro de la caja,
    entre los que tienen ≥ 2000 px y solidez (área / área de su recuadro) ≥ 0,40. La solidez deja afuera las letras grises
    de «Founders Privée» de la Negra (trazos finos: en 2a, con el acercamiento de 4×, cada letra es más grande que el
    pedazo de Blanca que entra por el borde) y la espuma suelta."""
    from scipy import ndimage as nd
    L, sat = lum_sat(rgb)
    x0, y0, x1, y1 = caja
    dentro = np.zeros(L.shape, bool); dentro[y0:y1, x0:x1] = True
    lab, n = nd.label(dentro & (L > 150) & (sat < 0.12), structure=np.ones((3, 3)))
    if n == 0:
        return np.zeros(L.shape, bool), L, sat
    idx = np.arange(1, n + 1)
    tam = nd.sum(np.ones(L.shape), lab, index=idx)
    mejor, area = None, 0
    for i, sl in enumerate(nd.find_objects(lab)):
        if tam[i] < AREA_MIN:
            continue
        caja_area = (sl[0].stop - sl[0].start) * (sl[1].stop - sl[1].start)
        if tam[i] / caja_area >= SOLIDEZ_MIN and tam[i] > area:
            mejor, area = i + 1, tam[i]
    if mejor is None:
        return np.zeros(L.shape, bool), L, sat
    return lab == mejor, L, sat


def ganancias_toma(rgbs, caja):
    acc = {k: [] for k in range(len(FRANJAS))}
    for rgb in rgbs:
        bl, L, sat = blanca(rgb, caja)
        for k, (lo, hi) in enumerate(FRANJAS):
            m = bl & (L >= lo) & (L < hi)
            acc[k].append(np.concatenate([rgb[m], L[m][:, None]], 1))
    cent, gan, med = [], [], []
    for k, v in acc.items():
        p = np.concatenate(v, 0)
        if len(p) < 3000:
            continue
        md = np.median(p[:, :3], 0); y = float(md @ KY)
        cent.append(float(np.median(p[:, 3]))); gan.append(y / np.maximum(md, 1e-3))
        med.append(dict(franja=FRANJAS[k], L_centro=round(cent[-1], 1), n=int(len(p)), rgb_mediana=[round(float(x), 1) for x in md],
                        b_menos_r=round(float(md[2] - md[0]), 1), ganancia=[round(float(x), 4) for x in gan[-1]]))
    return np.array(cent), np.array(gan), med


def corregir(rgb, caja, cent, gan):
    from scipy import ndimage as nd
    from PIL import Image, ImageFilter
    bl, L, sat = blanca(rgb, caja)
    zona = nd.binary_dilation(bl, iterations=8)
    borde = np.asarray(Image.fromarray((zona * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    g = np.stack([np.interp(L, cent, gan[:, k]) for k in range(3)], -1)
    ss = lambda x: (lambda c: c * c * (3 - 2 * c))(np.clip(x, 0, 1))
    w = np.clip((0.15 - sat) / 0.05, 0, 1) * ss((L - 120) / 30) * borde
    return rgb * (1 + w[..., None] * (g - 1)), w, bl


def tela_br(rgb, bl):
    """B−R y G−R de la tela lisa de la Blanca: L > 150, sat < 0,12, mitad más clara (la cara iluminada)."""
    L, sat = lum_sat(rgb)
    m = bl & (L > 150) & (sat < 0.12)
    if m.sum() < 500:
        return None
    q = rgb[m]; Lq = L[m]; q = q[Lq >= np.median(Lq)]
    md = np.median(q, 0)
    return dict(rgb=[round(float(x), 1) for x in md], b_menos_r=round(float(md[2] - md[0]), 1),
                g_menos_r=round(float(md[1] - md[0]), 1), pixeles=int(len(q)))


def celeste(rgb, bl):
    """celeste de «Founders Privée» de la Blanca: píxeles saturados azulados dentro del contorno relleno de la Blanca."""
    from scipy import ndimage as nd
    L, sat = lum_sat(rgb)
    fill = nd.binary_fill_holes(nd.binary_closing(bl, iterations=4))
    m = fill & (rgb[..., 2] - rgb[..., 0] > 25) & (L > 90) & (sat > 0.15)
    if m.sum() < 200:
        return None
    md = np.median(rgb[m], 0)
    return dict(rgb=[round(float(x), 1) for x in md], b_sobre_r=round(float(md[2] / max(md[0], 1)), 3), pixeles=int(m.sum()))


def leer_yuv(src, n):
    r = U.run(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(src), '-vf', f"select='eq(n\\,{n})'",
                    '-fps_mode', 'passthrough', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-']))
    return partir(r)


def partir(b):
    ny = W * H; nc = ny // 4
    a = np.frombuffer(b, np.uint8)
    return a[:ny].reshape(H, W), a[ny:ny + nc].reshape(H // 2, W // 2), a[ny + nc:].reshape(H // 2, W // 2)


# tramos de suavizado: 2a (acercamiento 4× → 1×: la parte visible de la Blanca cambia de la sombra al sol en 12 cuadros)
# con mediana de 3 y media de 3; 2b, 3 y 4 con mediana de 5 y media de 7
TRAMOS_COLOR = [(54, 65, 3, 3), (66, 133, 5, 7), (134, 205, 5, 7), (206, 280, 5, 7)]


def residuo(rgb, bl, cent, gan):
    """ganancia residual del cuadro: después de las ganancias por franja de la toma, la que deja neutra la mediana de la
    tela lisa de la Blanca visible en ESE cuadro (en 2a, con el acercamiento, se ve el lado en sombra: B−R +10…+20)."""
    L, sat = lum_sat(rgb)
    m = bl & (L > 150) & (sat < 0.12)
    if m.sum() < 300:
        return None
    m &= L >= np.median(L[m])            # la cara iluminada (misma definición que tela_br, la medida que se informa)
    g = np.stack([np.interp(L[m], cent, gan[:, k]) for k in range(3)], -1)
    md = np.median(rgb[m] * g, 0)
    return float(md @ KY) / np.maximum(md, 1e-3)


def suavizar(serie, med=5, media=7):
    """mediana móvil y media móvil (bordes repetidos); los cuadros sin medida toman el vecino."""
    from scipy.ndimage import median_filter, uniform_filter1d
    a = np.array([np.nan * np.ones(3) if v is None else v for v in serie], float)
    ok = ~np.isnan(a[:, 0])
    if not ok.any():
        return np.ones_like(a)
    idx = np.arange(len(a))
    for c in range(3):
        a[:, c] = np.interp(idx, idx[ok], a[ok, c])
    a = median_filter(a, size=(med, 1), mode='nearest')
    return uniform_filter1d(a, media, axis=0, mode='nearest')


def etapa_color():
    base0, base = T / 'v2_base0.mp4', T / 'v2_base.mp4'
    rep = dict(metodo=('pines.neutralizar en video. (1) Ganancias por franja de L (150–190, 190–215, 215–256) por toma: '
                       'mediana de la tela lisa (L > 150, sat < 0,12) de la Blanca en 4 cuadros. (2) Residuo por cuadro: '
                       'la ganancia que deja neutra la mediana de la cara iluminada (mitad más clara) de la tela visible en ese cuadro, suavizada en el tiempo '
                       '(mediana de 5 + media de 7 cuadros por plano; en 2a, mediana de 3 + media de 3) para que no parpadee. '
                       'Máscara de la Blanca por cuadro: mayor componente conexo de tela clara y neutra con ≥ 2000 px y '
                       'solidez ≥ 0,40 dentro de la caja de la toma, +8 px, borde de 3 px. Peso = clip((0,15 − sat)/0,05) '
                       '· suave((L − 120)/30): el celeste (sat 0,17–0,26), el ROCCÉ de denim (L < 120), la piel, las '
                       'rocas y la Negra quedan con peso 0. Solo se reescriben los píxeles con peso > 0,002 (y los '
                       'bloques de croma 2×2 que los tocan); el resto del cuadro queda idéntico al de la base.'), tomas={})
    G = {}
    for toma, (rango, medir, caja) in COLOR.items():
        rgbs = [yuv_rgb(*leer_yuv(base0, n)) for n in medir]
        cent, gan, med = ganancias_toma(rgbs, caja)
        G[toma] = (cent, gan)
        rep['tomas'][toma] = dict(cuadros_master=list(rango), medicion=list(medir), caja=list(caja), franjas=med)
        print(toma, json.dumps(med, ensure_ascii=False), flush=True)
    rango = {n: t for t, (r, _, _) in COLOR.items() for n in range(r[0], r[1] + 1)}
    ny = W * H; nc = ny // 4

    def cuadros():
        dec = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(base0), '-f', 'rawvideo',
                                     '-pix_fmt', 'yuv420p', '-']), stdout=subprocess.PIPE)
        k = 0
        while True:
            b = dec.stdout.read(ny + 2 * nc)
            if len(b) < ny + 2 * nc:
                break
            yield k, b
            k += 1
        dec.stdout.close(); dec.wait()

    # pasada 1: residuo por cuadro (a media resolución: alcanza para la mediana de la tela)
    # (media resolución: se arma con la luma promediada 2×2 y la croma nativa 540×960)
    res = {}
    for k, b in cuadros():
        if k not in rango:
            continue
        toma = rango[k]; x0, y0, x1, y1 = COLOR[toma][2]
        Y, Cb, Cr = partir(b)
        Yh = Y.reshape(H // 2, 2, W // 2, 2).mean((1, 3))
        y = (Yh - 16) / 219; u = (Cb.astype(np.float32) - 128) / 224; v = (Cr.astype(np.float32) - 128) / 224
        Rr = y + 1.5748 * v; Bb = y + 1.8556 * u; Gg = (y - 0.2126 * Rr - 0.0722 * Bb) / 0.7152
        rgb = np.stack([Rr, Gg, Bb], -1) * 255.0
        global AREA_MIN
        a0 = AREA_MIN; AREA_MIN = a0 // 4
        try:
            bl, _, _ = blanca(rgb, (x0 // 2, y0 // 2, x1 // 2, y1 // 2))
        finally:
            AREA_MIN = a0
        res[k] = residuo(rgb, bl, *G[toma])
    RES = {}
    for a, b_, md_, mm_ in TRAMOS_COLOR:
        sm = suavizar([res.get(n) for n in range(a, b_ + 1)], md_, mm_)
        for i, n in enumerate(range(a, b_ + 1)):
            RES[n] = sm[i]
    rep['residuo_por_cuadro'] = {n: dict(medido=None if res.get(n) is None else [round(float(x), 4) for x in res[n]],
                                         suavizado=[round(float(x), 4) for x in RES[n]]) for n in sorted(RES)}
    # pasada 2: aplicar
    enc = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{W}x{H}',
                                 '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                                 '-color_trc', 'bt709', '-i', '-', '-c:v', 'libx264', '-threads', '2', '-qp', '0',
                                 '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries',
                                 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', str(base)]), stdin=subprocess.PIPE)
    por_cuadro = {}; n_out = 0
    for k, b in cuadros():
        if k in rango:
            toma = rango[k]; caja = COLOR[toma][2]
            cent, gan = G[toma]
            Y, Cb, Cr = partir(b)
            rgb = yuv_rgb(Y, Cb, Cr)
            rgb2, w, bl = corregir(rgb, caja, cent, gan * RES[k][None, :])
            Y2, Cb2, Cr2 = rgb_yuv(rgb2)
            mw = w > 0.002
            mc = mw.reshape(H // 2, 2, W // 2, 2).any((1, 3))
            Yo = np.where(mw, np.clip(np.round(Y2), 0, 255), Y).astype(np.uint8)
            Cbo = np.where(mc, np.clip(np.round(Cb2), 0, 255), Cb).astype(np.uint8)
            Cro = np.where(mc, np.clip(np.round(Cr2), 0, 255), Cr).astype(np.uint8)
            b = Yo.tobytes() + Cbo.tobytes() + Cro.tobytes()
            rgb_d = yuv_rgb(Yo, Cbo, Cro)
            fuera = ~np.repeat(np.repeat(mc, 2, 0), 2, 1)
            por_cuadro[k] = dict(toma=toma, pct_luma_tocada=round(float(mw.mean() * 100), 2),
                                 blanca_px=int(bl.sum()), tela_antes=tela_br(rgb, bl), tela_despues=tela_br(rgb_d, bl),
                                 celeste_antes=celeste(rgb, bl), celeste_despues=celeste(rgb_d, bl),
                                 fuera_de_la_zona_dif_max=int(max(np.abs(Yo.astype(int) - Y)[fuera].max(initial=0), 0)))
        enc.stdin.write(b); n_out += 1
    enc.stdin.close(); enc.wait()
    assert n_out == NF and enc.returncode == 0, (n_out, enc.returncode)
    rep['por_cuadro'] = por_cuadro
    jdump(rep, MED / 'color_blanca.json')
    for toma, (r, medir, caja) in COLOR.items():
        a = [por_cuadro[n]['tela_antes']['b_menos_r'] for n in range(r[0], r[1] + 1) if por_cuadro[n]['tela_antes']]
        d = [por_cuadro[n]['tela_despues']['b_menos_r'] for n in range(r[0], r[1] + 1) if por_cuadro[n]['tela_despues']]
        print(toma, 'B−R antes mediana', np.median(a), 'rango', min(a), max(a), '· después mediana', np.median(d),
              'rango', min(d), max(d), flush=True)


# =====================================================================================================
# etapa placa · cierre del sistema Roccé Life (pines v02): degradé + frase en Instrument Serif + firma con logo original
# =====================================================================================================
FUENTES = R / 'scripts' / 'fuentes'
LOGO = R / 'LOGO' / 'rocce_logo.png'
PLACA = dict(frase_html='Seguí al <em>equipo</em>.', frase_txt='Seguí al equipo.', fs=100, top_frase=300,
             grad=(760, 0.62, (12, 18, 26)), logo=96, ffs=30, top_firma=450)
CSS_PLACA = """
@font-face{font-family:'IS';src:url('file://%(F)s/InstrumentSerif-Regular.ttf')}
@font-face{font-family:'ISI';src:url('file://%(F)s/InstrumentSerif-Italic.ttf')}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:transparent}
.grad{position:absolute;left:0;right:0;top:0}
.frase{position:absolute;left:72px;right:72px;font-family:'IS';font-weight:400;color:#FFFFFF;text-align:center;
  font-size:%(fs)dpx;line-height:1.0;letter-spacing:-0.012em;text-shadow:0 2px 24px rgba(0,0,0,.28);
  font-feature-settings:'kern','liga'}
.frase em{font-family:'ISI';font-style:normal}
.firma{position:absolute;left:50%%;transform:translateX(-50%%);display:flex;align-items:center;gap:16px}
.firma img{width:%(logo)dpx;height:%(logo)dpx;border-radius:%(radio)dpx;display:block}
.firma span{font-family:'Inter';font-weight:500;font-size:%(ffs)dpx;letter-spacing:.34em;margin-right:-.34em;
  color:rgba(255,255,255,.92);text-shadow:0 1px 8px rgba(0,0,0,.35)}
"""


def etapa_placa():
    """dos PNG RGBA 1080×1920: cierre_frase (degradé + frase, c206–c280) y cierre_firma (c216–c280). CSS de
    scripts/life/pines.py (frase, em, firma) con fondo transparente; logo original escalado a 96 px, ficha #FEFEFE con
    radio 11 px (11 %, ≤ 12 %: solo se recorta fondo). La firma va centrada (guion, notas comunes)."""
    C = T / 'placa'; C.mkdir(parents=True, exist_ok=True)
    t = dict(F=FUENTES, fs=PLACA['fs'], logo=PLACA['logo'], radio=round(PLACA['logo'] * 0.11), ffs=PLACA['ffs'])
    alto, op, (r, g, b) = PLACA['grad']
    grad = (f'<div class="grad" style="height:{alto}px;background:linear-gradient(to bottom,rgba({r},{g},{b},{op}) 0%,'
            f'rgba({r},{g},{b},{op * 0.55:.3f}) 45%,rgba({r},{g},{b},0) 100%)"></div>')
    docs = {
        'cierre_frase': f'{grad}<div class="frase" style="top:{PLACA["top_frase"]}px">{PLACA["frase_html"]}</div>',
        'cierre_firma': (f'<div class="firma" style="top:{PLACA["top_firma"]}px"><img src="file://{LOGO}">'
                         f'<span>ROCCÉ LIFE</span></div>'),
    }
    trabajos = []
    for nombre, cuerpo in docs.items():
        h = C / f'{nombre}.html'
        h.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS_PLACA % t}</style></head>'
                     f'<body>{cuerpo}</body></html>', encoding='utf-8')
        trabajos.append(dict(html=str(h), out=str(C / f'{nombre}.png'), w=W, h=H))
    (C / '_trabajos.json').write_text(json.dumps(trabajos, indent=1))
    subprocess.run(nice(['node', str(R / 'scripts' / 'life' / 'life_v2_render.js'), str(C / '_trabajos.json')]), check=True)
    from PIL import Image
    rep = {}
    for tr in trabajos:
        im = Image.open(tr['out']); a = np.asarray(im)
        assert im.size == (W, H) and im.mode == 'RGBA', (im.size, im.mode)
        al = a[..., 3]
        filas = np.nonzero((al > 8).any(1))[0]; cols = np.nonzero((al > 8).any(0))[0]
        rep[Path(tr['out']).name] = dict(tam=im.size, modo=im.mode, md5_pixeles=hashlib.md5(a.tobytes()).hexdigest(),
                                         caja_alfa_gt8=[int(cols.min()), int(filas.min()), int(cols.max()), int(filas.max())])
    # caja de la frase y de la firma sin el degradé: píxeles casi blancos y opacos
    a = np.asarray(Image.open(C / 'cierre_frase.png')).astype(int)
    m = (a[..., 3] > 200) & (a[..., :3].min(-1) > 200)
    ys, xs = np.nonzero(m)
    rep['frase_letras'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    a = np.asarray(Image.open(C / 'cierre_firma.png')).astype(int)
    ys, xs = np.nonzero(a[..., 3] > 8)
    rep['firma'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    # el logo de la ficha: la esquina (fondo #FEFEFE) y el dibujo, sin deformar (proporción 1:1)
    jdump(rep, C / 'placa.json')
    print(json.dumps(rep, ensure_ascii=False))


# =====================================================================================================
# textos (§4 del guion, hook A) · tamaños de §notas comunes
# =====================================================================================================
def tt(n):
    """segundo para libass que cae entre el cuadro n−1 y el n (el .ass redondea a centésimas: 134/30 = 4,4667 → 4,47
    entraría un cuadro tarde)."""
    return max(0.0, (n - 0.4) / FPS)


TEXTOS = [
    dict(n=(0, 53), txt='No esperes\\Nque te fichen.', estilo='CajaN', y=270, pop=True, extra='\\fs120\\xbord33\\ybord10'),
    dict(n=(60, 89), txt='Es su marca.', estilo='CajaN', y=270, pop=True, extra='\\fs104\\xbord29\\ybord9'),
    dict(n=(90, 133), txt='Se fichó solo.', estilo='CajaN', y=270, extra='\\fs104\\xbord29\\ybord9'),
    dict(n=(134, 161), txt='¿Y vos?', estilo='CajaN', y=270, extra='\\fs104\\xbord29\\ybord9'),
    dict(n=(162, 205), txt='Fichate vos.', estilo='Grande', y=300, pop=True, extra='\\fs124'),
]


def textos_ass():
    ev = [dict(t0=tt(d['n'][0]), t1=tt(d['n'][1] + 1), txt=d['txt'], estilo=d['estilo'], y=d['y'], pop=d.get('pop', False),
               extra=d.get('extra')) for d in TEXTOS]
    return V.ass(ev, T / 'v2_textos.ass')


# =====================================================================================================
# etapa audio · §5 del guion (música TEMP propia 100 BPM Mi menor; foley de tela PROVISORIO; ambiente real)
# =====================================================================================================
RAFAGAS_7887 = [(2.25, 2.40), (3.68, 3.85)]     # máster (fuente 1,45–1,60 y 2,88–3,05: medido, ver audio.json)
XF = 0.03


def rms_hp(toma, src0, dur, hp):
    from sonido import Mezcla, filt, SR as _SR
    a = Mezcla(1.0).leer(toma)
    seg = filt(a[int(src0 * _SR):int((src0 + dur) * _SR)], 'high', hp)
    return float(np.sqrt((seg ** 2).mean()))


def ganancia_parche():
    """el guion pone el parche de 7885 a −8 dB, pero 7885 (olas rompiendo) mide ≈ 14 dB más que el ambiente de 7887:
    con −8 el parche sonaría tan fuerte como la ráfaga. Se iguala su RMS (pasa-altos 150 Hz) al de 7887 alrededor de cada
    ráfaga, con la misma ganancia de 7887 (−6 dB)."""
    r87 = np.mean([rms_hp('IMG_7887', a, 0.15, 150) for a in (1.30, 1.62, 2.73, 3.08)])
    r85 = rms_hp('IMG_7885', 0.60, 0.23, 150)
    return round(-6 + 20 * math.log10(r87 / r85), 2), dict(rms_7887_dbfs=round(20 * math.log10(r87), 1),
                                                          rms_7885_0_6_dbfs=round(20 * math.log10(r85), 1))


def ambientes(m, g_parche):
    m.ambiente('IMG_7824', 0.000, 0.000, 1.800, -10, hp=200)
    # 7887 (fuente 1,000 → máster 1,800) en tres tramos, con las ráfagas reemplazadas por 7885 0,6 (fundidos de 30 ms
    # fuera de la ráfaga)
    (a1, b1), (a2, b2) = RAFAGAS_7887
    s = lambda t: 1.000 + (t - 1.800)
    m.ambiente('IMG_7887', s(1.800), 1.800, a1, -6, hp=150, fin_fade=XF)
    m.ambiente('IMG_7885', 0.60, a1 - XF, b1 + XF, g_parche, hp=150, fade=XF)
    m.ambiente('IMG_7887', s(b1), b1, a2, -6, hp=150, fade=XF)
    m.ambiente('IMG_7885', 0.60, a2 - XF, b2 + XF, g_parche, hp=150, fade=XF)
    m.ambiente('IMG_7887', s(b2), b2, 4.467, -6, hp=150, ini_fade=XF)
    m.ambiente('IMG_7885', 2.000, 4.467, 6.867, -4, hp=60)
    m.ambiente('IMG_7896', 3.600, 6.867, DUR, -4, fin_fade=.25)


def foley(m):
    m.obturador(0.10, .30); m.obturador(0.37, .24); m.obturador(0.87, .30)     # flashes de la presentación (pista 1)
    m.tela(1.47, .30, .14)                                                       # empuje
    m.barrido(1.65, .30, .12)                                                    # barrido del empuje: suena 1,47–1,77
    m.obturador(2.20, .45)                                                       # c66: el obturador de su celular
    m.tela(2.50, .40, .08)                                                       # baja el celular
    m.barrido(6.80, .25, .16); m.toque(6.867, .16, 2400)                         # corte al equipo (c206)


def musica(m):
    ch = lambda t0, t1, g=.08: [m.charles(round(float(t), 3), g) for t in np.arange(t0, t1 - 1e-6, 0.3)]
    # entrada
    m.pad(0.0, [52, 55, 59], 1.75, .05, 1000, a=.1)
    m.campana(0.0, 76, .05)
    m.bombo(0.0, .5, f0=100); m.bombo(0.6, .45, f0=100); m.bombo(1.2, .5, f0=100)
    for i, t in enumerate((0.0, 0.3, 0.6, 0.9, 1.2)):
        m.charles(t, .06 + .03 * i / 4)
    m.subida(1.00, 1.70, .16)
    # drop 1 (c54)
    m.bombo(1.8, .95); m.impacto(1.8, .40)
    m.ocho08(1.8, 40, 1.0, .55, glide_desde=47)
    m.pad(1.8, [52, 55, 59, 64], 1.15, .06, 1400)
    m.campana(1.8, 83, .06)
    for t, g in ((2.4, .8), (3.0, .85), (3.6, .8), (4.2, .85)):
        m.bombo(t, g)
    m.palma(3.0); m.palma(4.2)
    m.pad(3.0, [48, 52, 55], 1.15, .06, 1200); m.pad(4.2, [50, 54, 57], .3, .06, 1200)
    m.ocho08(3.0, 36, .5); m.ocho08(3.6, 36, .5)
    ch(1.8, 4.4)
    # tensión
    m.pad(4.467, [47, 50, 54], .9, .05, 800)
    m.redoble(4.8, 5.35, .12); m.subida(4.70, 5.35, .15)
    # drop 2 (c162)
    m.bombo(5.4, 1.0); m.impacto(5.4, .5)
    m.ocho08(5.4, 40, 1.1, .6, glide_desde=35)
    m.pad(5.4, [52, 55, 59, 64], 1.45, .07)
    m.campana(5.4, 76, .07)
    m.bombo(6.0, .8); m.palma(6.0); m.palma(6.3, .22)
    ch(5.4, 6.8)
    # cierre
    m.bombo(7.2, .9); m.pad(7.2, [48, 52, 55, 59], .6, .06); m.ocho08(7.2, 36, .5)
    m.bombo(7.8, .8); m.palma(7.8); m.pad(7.8, [50, 54, 57], .6, .06); m.ocho08(7.8, 38, .5)
    m.bombo(8.4, .9); m.pad(8.4, [52, 55, 59, 64], .9, .06, r=.5); m.campana(8.4, 76, .07, .9); m.ocho08(8.4, 40, .8, .5)
    # huecos y final (después de colocar todo lo de 'mus')
    m.silenciar('mus', 1.70, 1.80); m.silenciar('mus', 5.33, 5.40)
    m.fundido('mus', 8.90, DUR)
    m.fundido('fx', 9.05, DUR)        # colas de reverberación de la música (van en 'fx'): sin corte seco al final


def medir_ebur(f):
    r = subprocess.run(nice(['ffmpeg', '-nostats', '-threads', '2', '-i', str(f), '-af', 'ebur128=peak=true:framelog=quiet',
                             '-f', 'null', '-']), capture_output=True, text=True).stderr
    g = lambda k: float([l for l in r.splitlines() if l.strip().startswith(k)][-1].split()[1])
    return g('I:'), g('Peak:'), g('LRA:')


def limitar_tp(salida, lufs=-14.0, tp_max=-1.5):
    """sonido.Mezcla.exportar limita a 0,83 de muestra (−1,6 dBFS) y no mira el pico real: con transitorios secos (los
    obturadores sobre el ambiente normalizado de la versión sin música) el pico real pasa de −1 dBTP. Se rehace la última
    etapa desde el _pre.wav con el mismo alimiter (level=false) y un techo que baja 0,5 dB por vuelta hasta que el pico
    real queda ≤ tp_max, corrigiendo la ganancia para −14 LUFS en cada vuelta."""
    pre = str(salida).replace('.wav', '_pre.wav')
    I0, _, _ = medir_ebur(pre)
    gan = lufs - I0; lim_db = -1.6; hist = []
    for _ in range(12):
        lim = 10 ** (lim_db / 20)
        subprocess.run(nice(['ffmpeg', '-v', 'error', '-y', '-i', pre, '-af',
                             f'volume={gan:.2f}dB,alimiter=limit={lim:.4f}:level=false:attack=3:release=60:latency=1',
                             '-c:a', 'pcm_f32le', str(salida)]), check=True)
        I, Pk, LRA = medir_ebur(salida); hist.append(dict(techo_db=lim_db, ganancia_db=round(gan, 2), lufs=I, pico_dbtp=Pk))
        if abs(I - lufs) < 0.3 and Pk <= tp_max:
            break
        if Pk > tp_max:
            lim_db -= 0.5
        gan += (lufs - I)
    return dict(lufs=I, pico_dbtp=Pk, lra=LRA, vueltas=hist)


def etapa_audio():
    from sonido import Mezcla
    A.mkdir(parents=True, exist_ok=True)
    gp, med = ganancia_parche()
    print('parche 7885', gp, med, flush=True)
    m = Mezcla(DUR); ambientes(m, gp); foley(m); musica(m)
    r1 = m.exportar(str(A / 'v2_completa.wav'), lufs=-14)
    s = Mezcla(DUR); ambientes(s, gp); foley(s)
    r2 = s.exportar(str(A / 'v2_sinmusica.wav'), lufs=-14)
    out = dict(parche_7885_db=gp, medicion_parche=med, rafagas_master=RAFAGAS_7887, exportar_completa=r1,
               exportar_sinmusica=r2)
    for k, r in (('completa', r1), ('sinmusica', r2)):
        if r[1] > -1.5:
            out[f'limitado_{k}'] = limitar_tp(A / f'v2_{k}.wav')
            print(k, out[f'limitado_{k}'], flush=True)
        out[k] = dict(zip(('lufs', 'pico_dbtp', 'lra'), medir_ebur(A / f'v2_{k}.wav')))
    jdump(out, A / 'audio.json')
    print('completa', out['completa'], 'sin música', out['sinmusica'])


# =====================================================================================================
# etapa master · textos + placa + mezcla → H.264 High 4.0 / AAC-LC (video.master)
# =====================================================================================================
def master_v2(video, audio_wav, salida, ass_path=None, overlays=None):
    """copia de video.master con un arreglo en los overlays. Con `-loop 1 -i png` el PNG entra a 25 fps y
    `enable='between(n,…)'` no sigue los cuadros del video de 30 fps: en la primera corrida (v01 sin entregar) la placa
    aparecía solo en c210, c216, c222… y fija desde c246. Acá el PNG entra a 30 fps y la ventana va por tiempo con medio
    cuadro de margen: between(t, (n0 − 0,5)/30, (n1 + 0,5)/30). overlays = [(png, x, y, n0, n1)] con cuadros inclusivos.
    El resto (códecs, nivel, tasa, metadatos, faststart) es idéntico a video.master."""
    inputs = ['-i', str(video), '-i', str(audio_wav)]
    fc = ['[0:v]setsar=1[v0]']
    lab = 'v0'
    for i, (png, x, y, n0, n1) in enumerate(overlays or []):
        inputs += ['-framerate', str(FPS), '-loop', '1', '-i', str(png)]
        nl = f'v{i + 1}'
        fc.append(f"[{lab}][{i + 2}:v]overlay={x}:{y}:enable='between(t,{(n0 - 0.5) / FPS:.5f},{(n1 + 0.5) / FPS:.5f})':shortest=1[{nl}]")
        lab = nl
    if ass_path:
        fc.append(f"[{lab}]subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter[vs]"); lab = 'vs'
    fc.append(f'[{lab}]format=yuv420p[vout]')
    V.sh(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '1:a:0',
          '-c:v', 'libx264', '-profile:v', 'high', '-level:v', '4.0', '-preset', 'slow', '-crf', '17',
          '-maxrate', '20M', '-bufsize', '25M', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-g', '30',
          '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
          '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
          '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
          '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
          '-shortest', '-movflags', '+faststart', str(salida)])
    return salida


PLACA_CUADROS = dict(frase=(206, 280), firma=(216, 280))


def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    a = textos_ass()
    C = T / 'placa'
    ov = [(C / 'cierre_frase.png', 0, 0, *PLACA_CUADROS['frase']), (C / 'cierre_firma.png', 0, 0, *PLACA_CUADROS['firma'])]
    for k, nombre in NOMBRES.items():
        if (MAS / nombre).exists():
            (MAS / nombre).unlink()          # intermedio de trabajo (nunca entregado): se rehace
        master_v2(T / 'v2_base.mp4', A / f'v2_{k}.wav', MAS / nombre, ass_path=a, overlays=ov)
        print('->', MAS / nombre, flush=True)


# =====================================================================================================
# etapa control · evidencia (evidencia_v01/): formato, huellas, sonido, validaciones §8, color, textos, hojas
# =====================================================================================================
CORTES = [44, 54, 66, 134, 162, 206]          # 44 y 66: cambio de plano dentro de la misma toma (empuje / apertura)
TRAMOS = [('1a apuesta 7824', 0.0, 44 / FPS), ('1b empuje + hueco', 44 / FPS, 1.8), ('2a giro 1 7887', 1.8, 66 / FPS),
          ('2b se fichó solo 7887', 66 / FPS, 134 / FPS), ('3 ¿Y vos? 7885', 134 / FPS, 162 / FPS),
          ('3 Fichate vos. 7885', 162 / FPS, 206 / FPS), ('4 CTA 7896', 206 / FPS, DUR), ('último 0,5 s', DUR - 0.5, DUR)]


def _img(a):
    from PIL import Image
    return Image.fromarray(np.ascontiguousarray(a))


def tira(imgs, rotulos, salida, ancho=360):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 22)
    ims = []
    for a, r in zip(imgs, rotulos):
        im = _img(a); im = im.resize((ancho, round(ancho * im.height / im.width)), Image.LANCZOS)
        d = ImageDraw.Draw(im); tw = d.textlength(r, font=fnt); d.rectangle([0, 0, tw + 12, 30], fill=(0, 0, 0))
        d.text((6, 3), r, font=fnt, fill=(255, 255, 0)); ims.append(im)
    Wd = Image.new('RGB', (sum(i.width + 2 for i in ims), max(i.height for i in ims)), (30, 30, 30))
    x = 0
    for i in ims:
        Wd.paste(i, (x, 0)); x += i.width + 2
    Wd.save(salida, quality=92)


def render_ass_gris(ass_path, n):
    r = U.run(nice(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}:d={DUR + 1}', '-vf',
                    f"subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter,select='eq(n\\,{n})',format=gray",
                    '-frames:v', '1', '-fps_mode', 'passthrough', '-f', 'rawvideo', '-']))
    return np.frombuffer(r, np.uint8).reshape(H, W)


def altura_mayuscula(ass_path, n):
    """altura (px) de la primera letra del primer renglón del texto visible en el cuadro n (mayúscula: N, E, S, F, ¿)."""
    from scipy import ndimage as nd
    g = render_ass_gris(ass_path, n)
    m = g > 160                       # letras blancas (la caja #141414 queda afuera)
    lab, k = nd.label(m)
    objs = nd.find_objects(lab)
    if not objs:
        return None
    y0 = min(o[0].start for o in objs)
    primer = [o for o in objs if o[0].start < y0 + 40]
    hmax = max(o[0].stop - o[0].start for o in primer)
    primer = [o for o in primer if o[0].stop - o[0].start >= 0.8 * hmax]     # salta el «¿» (más bajo que la Y)
    o = min(primer, key=lambda s: s[1].start)
    return dict(cuadro=n, alto_px=o[0].stop - o[0].start, ancho_px=o[1].stop - o[1].start,
                caja_texto=[int(np.nonzero(m.any(0))[0].min()), int(np.nonzero(m.any(1))[0].min()),
                            int(np.nonzero(m.any(0))[0].max()), int(np.nonzero(m.any(1))[0].max())],
                caja_con_fondo=_caja(g > 8))


def _caja(m):
    ys, xs = np.nonzero(m)
    return None if len(ys) == 0 else [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def founders_en(img, toma):
    _, tipo, _, _, _, _, par = MEDIR[toma]
    bb, m = estampado(img, tipo, (0, 500, W - 1, 1500), **par)
    if bb is None:
        return None, m
    x0, y0, x1, y1 = bb
    return dict(bbox=[x0, y0, x1, y1], ancho_px=x1 + 1 - x0, ancho_pct=round((x1 + 1 - x0) / W * 100, 1),
                centro=[round((x0 + x1 + 1) / 2, 1), round((y0 + y1 + 1) / 2, 1)], toca_bordes=[x0 <= 1, x1 >= W - 2],
                inclinacion_grados=inclinacion(m)), m


def letras_tophat(img, banda=(760, 1180), umbral=30, x_min=0):
    """«Founders Privée» en un cuadro ampliado: trazos claros y neutros sobre la Negra (sombrero de copa blanco de 91 px
    sobre la luma, sat < 0,15, 60 < L < 200), componentes ≥ 400 px dentro de la banda. El detector `estampado` está
    afinado para la escala natural y a 1,6× / 4× pierde trazos (primera corrida del control: 83,7 % y 37,5 %)."""
    from scipy import ndimage as nd
    a = img.astype(np.float32)
    Lm = a @ KY; mx = a.max(-1); mn = a.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
    th = Lm - nd.grey_opening(Lm, size=(91, 91))
    m = (th > umbral) & (sat < 0.15) & (Lm > 60) & (Lm < 200)
    m[:banda[0]] = False; m[banda[1]:] = False; m[:, :x_min] = False
    m = nd.binary_opening(m, iterations=2)
    lab, k = nd.label(m); s = nd.sum(m, lab, range(1, k + 1)); m = np.isin(lab, 1 + np.nonzero(s >= 400)[0])
    ys, xs = np.nonzero(m)
    v = np.linalg.eigh(np.cov(np.stack([xs, ys])))[1][:, 1]
    ang = float(np.degrees(np.arctan2(-v[1], v[0]))); ang = ang - 180 if ang > 90 else (ang + 180 if ang < -90 else ang)
    return dict(bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                ancho_visible_pct=round((xs.max() + 1 - xs.min()) / W * 100, 1),
                centro=[round((xs.min() + xs.max() + 1) / 2, 1), round((ys.min() + ys.max() + 1) / 2, 1)],
                centroide=[round(float(xs.mean()), 1), round(float(ys.mean()), 1)],
                toca_bordes=[bool(xs.min() <= 2), bool(xs.max() >= W - 3)],
                inclinacion_eje_principal_grados=round(ang, 2), pixeles=int(m.sum())), m


def ventana_predicha(bb_nat, v):
    x, y, w, h = v; s = W / w
    x0, y0, x1, y1 = bb_nat
    b = [(x0 - x) * s, (y0 - y) * s, (x1 - x) * s, (y1 - y) * s]
    return dict(bbox=[round(c, 1) for c in b], ancho_pct=round((b[2] - b[0]) / W * 100, 1),
                centro=[round((b[0] + b[2]) / 2, 1), round((b[1] + b[3]) / 2, 1)])


def remeras_7896(img):
    """Blanca (blanca()) + Negra (tela oscura y neutra: L < 75, sat < 0,30, componente que toca la Blanca dilatada 25 px)
    en un cuadro del plano 4; devuelve cajas y márgenes al borde del cuadro."""
    from scipy import ndimage as nd
    rgb = img.astype(np.float32)
    bl, L, sat = blanca(rgb, (60, 700, 760, 1500))
    fill = nd.binary_fill_holes(nd.binary_closing(bl, iterations=6))
    cerca = nd.binary_dilation(fill, iterations=25)
    zona = np.zeros(L.shape, bool); zona[700:1500, 60:1060] = True
    # B − R ≥ 1: la Negra es neutra-fría (mediana +5 en c206); las sombras de la roca son cálidas (mediana −6). Sin este
    # filtro la máscara se fugaba a las grietas oscuras debajo de la Negra (primera corrida del control)
    osc = zona & (L < 75) & (sat < 0.30) & (rgb[..., 2] - rgb[..., 0] >= 1)
    osc = nd.binary_opening(osc, iterations=3)
    lab, n = nd.label(osc)
    toca = np.unique(lab[cerca & osc]); toca = toca[toca > 0]
    if len(toca):
        tam = nd.sum(osc, lab, toca); neg = lab == toca[int(np.argmax(tam))]
        neg = nd.binary_fill_holes(nd.binary_closing(neg, iterations=6))
        # mangas y hombro (negro puro, B − R ruidoso): se crece la Negra sin límite por todo lo oscuro (L < 55, abierto
        # 2 px) que la toca. Es conservador: si se pega una sombra de la roca, la caja crece y el margen medido baja.
        neg = nd.binary_dilation(neg, iterations=0, mask=nd.binary_opening(L < 55, iterations=2) | neg)
        neg = nd.binary_fill_holes(nd.binary_closing(neg, iterations=4))
    else:
        neg = np.zeros_like(osc)
    cb, cn = _caja(fill), _caja(neg)
    u = [min(cb[0], cn[0]), min(cb[1], cn[1]), max(cb[2], cn[2]), max(cb[3], cn[3])] if cn else cb
    return dict(blanca=cb, negra=cn, union=u, margen=dict(izq=u[0], der=W - 1 - u[2], arr=u[1], abj=H - 1 - u[3])), fill, neg


def etapa_control():
    from PIL import Image
    import fmt03_v02 as U2
    EVID.mkdir(parents=True, exist_ok=True)
    (EVID / 'validaciones').mkdir(exist_ok=True)
    ass_path = T / 'v2_textos.ass'
    rep = U.control(NOMBRES, EVID, CORTES, NF - 1, TRAMOS, ass_path,
                    [dict(txt=d['txt']) for d in TEXTOS], [tt(n) + 0.5 / FPS for n in (10, 70, 100, 140, 170)], carpeta=MAS)
    rep['fecha'] = '2026-11-24'
    f0 = MAS / NOMBRES['completa']
    for k, nombre in NOMBRES.items():
        f = MAS / nombre
        a = U.audio_np(f)
        mom = U2.momentanea(f)
        rep['archivos'][k].update(
            sonoridad_momentanea_tramos=U2.momentanea_tramos(mom, [(n, a_, b_) for n, a_, b_ in TRAMOS]),
            silencio_final_s=silencio_final(a), rms_ultimo_05s_dbfs=round(float(20 * np.log10(np.sqrt((a[-SR // 2:] ** 2).mean()) + 1e-12)), 1))
        rep['archivos'][k]['atomos'] = atomos(f)
        jdump(mom, EVID / f'sonoridad_momentanea_{k}.json')
        print(k, rep['archivos'][k]['sonoridad'], rep['archivos'][k]['atomos'], 'silencio final', rep['archivos'][k]['silencio_final_s'], flush=True)
    # ---- duración de video y audio iguales
    for k in NOMBRES:
        r = rep['archivos'][k]
        r['duracion_video_igual_audio'] = abs(r['video']['duracion'] - r['audio']['duracion']) < 0.5 / FPS
    # ---- cuadros del máster (RGB 1080×1920) usados abajo
    N_ = sorted({0, 10, 43, 44, 50, 52, 53, 54, 55, 56, 60, 66, 90, 133, 134, 140, 161, 162, 163, 164, 180, 205, 206, 216,
                 240, 260, 280})
    MF = {n: U.leer(f0, W, H, n0=n, n1=n)[0] for n in N_}
    # ---- §8.1 · solo dedos en c0–c53 (muñeca tatuada fuera de la ventana)
    med = json.load(open(MED / 'founders.json'))
    tat = {t['cuadro_fuente']: t['x_der_nat'] for t in med['tatuaje_7824']}
    pl = plan_planos()
    v1a = (X1A, Y1A, NW / Z1A, NH / Z1A)
    p1b = pl[1]
    filas = []
    for n in range(0, 54):
        if n < 44:
            x_izq = v1a[0]
        else:
            k = n - 44; w = NW / p1b['zs'][k]; x_izq = min(max(p1b['cxs'][k] - w / 2, 0), NW - w)
        t = tat.get(n)
        filas.append(dict(cuadro=n, borde_izq_ventana_4k=round(x_izq, 1), tatuaje_x_der_4k=t,
                          margen_4k=None if t is None else round(x_izq - t, 1),
                          tatuaje_dentro=bool(t is not None and t >= x_izq)))
    val = dict(solo_dedos=dict(
        criterio=('la muñeca tatuada de la mano izquierda es el primer pedazo de antebrazo que entra (c43, borde '
                  'izquierdo, x ≤ ≈8 px de 4K a ojo; detector desde c46). Se exige que el borde izquierdo de la ventana '
                  'quede a la derecha del tatuaje en todos los cuadros. La mano derecha (uñas largas) entra con dedos y '
                  'parte del dorso por el borde derecho, sin muñeca a la vista (hojas 7824_der_c0-c53.jpg).'),
        tatuaje_visible_en_ventana=[f['cuadro'] for f in filas if f['tatuaje_dentro']], por_cuadro=filas))
    # recortes del borde izquierdo del MÁSTER c36–c53 (donde estaría la muñeca) y del borde derecho
    izq = U.leer(f0, W, H, n0=36, n1=53)
    tira([fr[560:860, 0:300] for fr in izq[::1]], [f'c{36 + i}' for i in range(len(izq))],
         EVID / 'validaciones' / '1_solo_dedos_borde_izq_master_c36-c53_1a1.jpg', ancho=150)
    tira([fr[300:900, 780:1080] for fr in izq[::3]], [f'c{36 + 3 * i}' for i in range(len(izq[::3]))],
         EVID / 'validaciones' / '1_solo_dedos_borde_der_master_c36-c53.jpg', ancho=200)
    for f_ in ('muneca_7824_c0-c56.jpg',):
        shutil.copy2(MED / f_, EVID / 'validaciones' / f'1_fuente_{f_}')
    for f_ in ('7824_muneca_c30-c53_1a1.jpg', '7824_der_c0-c53.jpg', '7824_izq_c20-c53.jpg'):
        shutil.copy2(HJ / f_, EVID / 'validaciones' / f'1_fuente_{f_}')
    # ---- §8.2 · coincidencia de «Founders Privée» en c53/c54
    nit53 = U.leer(P / '1b_nitido.mp4', W, H, n0=9, n1=9)[0]
    nit54 = U.leer(P / '2a_nitido.mp4', W, H, n0=0, n1=0)[0]
    # medición sobre los cuadros renderizados sin desenfoque (letras_tophat). En c54 se descartan x < 40: ahí entra el
    # borde de la Blanca (fondo claro) y el sombrero de copa lo toma como trazo.
    f53, m53 = letras_tophat(nit53); f54, m54 = letras_tophat(nit54, x_min=40)
    pred53 = ventana_predicha(F7824_C53['bbox'], ventana_founders(F7824_C53['bbox']))
    pred54 = ventana_predicha(F7887_C30['bbox'], ventana_founders(F7887_C30['bbox']))
    det53, _ = founders_en(nit53, 'IMG_7824'); det54, _ = founders_en(nit54, 'IMG_7887')
    val['coincidencia_letras'] = dict(
        pedido='ancho de «Founders Privée» 95–110 % en c53 y c54; centro vertical con diferencia ≤ 120 px',
        lectura=('c53 (7824 1,767 s, z 1,632): «Founders Privée» completo, de la rúbrica de la F a la última e, toca los dos '
                 'bordes (≥ 100 % medido; 102 % por la ventana). c54 (7887 1,000 s, z 4,035): en la fuente la palabra '
                 '«Privée» dobla con la espalda (brazos arriba) y «ée» no se ve en ningún cuadro; lo visible es «Founders '
                 'Priv», que va del borde izquierdo (x ≥ 40 medido; la F empieza ≈ x 50) al borde derecho. La ventana se '
                 'calculó para que lo visible mida 102 %.'),
        medido_sin_desenfoque=dict(c53=f53, c54=f54,
                                   dif_centro_vertical_px=round(abs(f53['centro'][1] - f54['centro'][1]), 1),
                                   dif_centroide_vertical_px=round(abs(f53['centroide'][1] - f54['centroide'][1]), 1),
                                   dif_inclinacion_grados=round(abs(f53['inclinacion_eje_principal_grados'] -
                                                                    f54['inclinacion_eje_principal_grados']), 2)),
        predicho_por_la_ventana=dict(c53=pred53, c54=pred54,
                                     nota='caja medida en la fuente a escala natural (etapa medir) llevada por la ventana exacta'),
        detector_estampado_descartado=dict(c53=det53, c54=det54,
                                           nota='afinado para escala 1:1; a 1,6× y 4× pierde «Privée» (no se usa)'),
        cumple=bool(f53['ancho_visible_pct'] >= 95 and f54['ancho_visible_pct'] >= 95 and pred53['ancho_pct'] <= 110 and
                    pred54['ancho_pct'] <= 110 and abs(f53['centro'][1] - f54['centro'][1]) <= 120))
    from PIL import ImageDraw
    vis = []
    for img, f_, m_ in ((nit53, f53, m53), (nit54, f54, m54)):
        ov = img.copy(); ov[m_] = (0.5 * ov[m_] + 0.5 * np.array([255, 0, 0])).astype(np.uint8)
        im = _img(ov); d = ImageDraw.Draw(im)
        d.rectangle(f_['bbox'], outline=(255, 255, 0), width=5)
        d.line([0, f_['centro'][1], W, f_['centro'][1]], fill=(0, 255, 255), width=3)
        d.line([f_['centro'][0], 0, f_['centro'][0], H], fill=(0, 255, 255), width=3)
        vis.append(np.asarray(im))
    tira(vis + [MF[53], MF[54]], [f"c53 nítido · visible {f53['ancho_visible_pct']} % · centro y {f53['centro'][1]}",
                                  f"c54 nítido · visible {f54['ancho_visible_pct']} % · centro y {f54['centro'][1]}",
                                  'c53 máster', 'c54 máster'],
         EVID / 'validaciones' / '2_coincidencia_founders_c53_c54.jpg', ancho=540)
    # franja de letras c53 arriba / c54 abajo a tamaño real, y la fuente a 4K con la caja medida
    fr_ = np.concatenate([nit53[600:1300], np.full((4, W, 3), (255, 0, 0), np.uint8), nit54[600:1300]])
    _img(fr_).save(EVID / 'validaciones' / '2_letras_c53_arriba_c54_abajo_1a1.jpg', quality=92)
    for toma, n_, bb, recorte, nombre in (('IMG_7824', 53, F7824_C53['bbox'], (250, 1750, 1900, 2450), '2_fuente_7824_c53_4K_caja.jpg'),
                                          ('IMG_7887', 30, F7887_C30['bbox'], (1100, 1950, 2000, 2450), '2_fuente_7887_c30_4K_caja.jpg')):
        src = U.leer(V._src(toma), NW, NH, n0=n_, n1=n_, vf_pre=V.color(toma))[0]
        im = _img(src).crop(recorte); d = ImageDraw.Draw(im)
        d.rectangle([bb[0] - recorte[0], bb[1] - recorte[1], bb[2] - recorte[0], bb[3] - recorte[1]], outline=(255, 255, 0), width=4)
        im.save(EVID / 'validaciones' / nombre, quality=92)
    _img(MF[53]).save(EVID / 'validaciones' / '2_master_c53.png'); _img(MF[54]).save(EVID / 'validaciones' / '2_master_c54.png')
    _img(nit53).save(EVID / 'validaciones' / '2_c53_sin_desenfoque.png'); _img(nit54).save(EVID / 'validaciones' / '2_c54_sin_desenfoque.png')
    shutil.copy2(MED / 'founders_IMG_7824.jpg', EVID / 'validaciones' / '2_fuente_founders_7824_c36-c56.jpg')
    shutil.copy2(MED / 'founders_IMG_7887.jpg', EVID / 'validaciones' / '2_fuente_founders_7887_c27-c48.jpg')
    print('coincidencia', json.dumps(val['coincidencia_letras']['medido_sin_desenfoque'], ensure_ascii=False), flush=True)
    # ---- placa cuadro a cuadro: cada cuadro c196–c280 del máster se compara con base, base + frase y base + frase + firma
    # (composición alfa de los PNG en numpy); gana la de menor error medio. Zona de la frase: y 0–280 (degradé, sin textos
    # ASS); zona de la firma: su caja.
    from PIL import Image as _I
    pf = np.asarray(_I.open(T / 'placa' / 'cierre_frase.png')).astype(np.float32)
    pg = np.asarray(_I.open(T / 'placa' / 'cierre_firma.png')).astype(np.float32)
    comp = lambda b, p: b * (1 - p[..., 3:] / 255) + p[..., :3] * (p[..., 3:] / 255)
    fx0, fy0, fx1, fy1 = json.load(open(T / 'placa' / 'placa.json'))['firma']
    placa = {}
    for k, nombre in NOMBRES.items():
        mm = U.leer(MAS / nombre, W, H, n0=196, n1=280).astype(np.float32)
        bb = U.leer(T / 'v2_base.mp4', W, H, n0=196, n1=280).astype(np.float32)
        fila = []
        for i, (m_, b_) in enumerate(zip(mm, bb)):
            e_fr = [float(np.abs(m_[:280] - x[:280]).mean()) for x in (b_[:280], comp(b_[:280], pf[:280]))]
            zb = b_[fy0:fy1 + 1, fx0:fx1 + 1]; zf = comp(zb, pf[fy0:fy1 + 1, fx0:fx1 + 1])
            zg = comp(zf, pg[fy0:fy1 + 1, fx0:fx1 + 1]); zm = m_[fy0:fy1 + 1, fx0:fx1 + 1]
            e_fi = [float(np.abs(zm - zf).mean()), float(np.abs(zm - zg).mean())]
            fila.append(dict(cuadro=196 + i, frase=bool(e_fr[1] < e_fr[0]), firma=bool(e_fi[1] < e_fi[0]),
                             err_frase=[round(x, 2) for x in e_fr], err_firma=[round(x, 2) for x in e_fi]))
        fr_on = [f['cuadro'] for f in fila if f['frase']]; fi_on = [f['cuadro'] for f in fila if f['firma']]
        placa[k] = dict(frase_cuadros=f'c{min(fr_on)}–c{max(fr_on)} ({len(fr_on)} cuadros)' if fr_on else 'nunca',
                        firma_cuadros=f'c{min(fi_on)}–c{max(fi_on)} ({len(fi_on)} cuadros)' if fi_on else 'nunca',
                        frase_ok=fr_on == list(range(206, 281)), firma_ok=fi_on == list(range(216, 281)), por_cuadro=fila)
        print('placa', k, placa[k]['frase_cuadros'], placa[k]['firma_cuadros'], placa[k]['frase_ok'], placa[k]['firma_ok'], flush=True)
    val['placa_por_cuadro'] = placa
    hoja_cuadros(f0, list(range(202, 220)), EVID / 'hoja_master_c202-c219_entrada_placa.jpg', ancho=200, cols=9)
    # ---- §8.3a · «Fichate vos.» (c162–c205) no pisa el estampado de la Blanca
    from scipy import ndimage as nd
    base = U.leer(T / 'v2_base.mp4', W, H, n0=162, n1=205)
    txt_cajas = {n: _caja(render_ass_gris(ass_path, n) > 8) for n in (162, 163, 164, 165, 180, 205)}
    txt_bajo = max(c[3] for c in txt_cajas.values())
    filas = []
    for i, img in enumerate(base):
        rgb = img.astype(np.float32)
        bl, L, sat = blanca(rgb, COLOR['IMG_7885'][2])
        fill = nd.binary_fill_holes(nd.binary_closing(bl, iterations=3))
        est = nd.binary_opening(fill & ~bl & ((L < 120) | ((rgb[..., 2] - rgb[..., 0] > 20) & (sat > 0.12))), iterations=1)
        lab, k = nd.label(est)
        if k:
            s = nd.sum(est, lab, range(1, k + 1)); est &= np.isin(lab, 1 + np.nonzero(s >= 150)[0])
        c = _caja(est)
        filas.append(dict(cuadro=162 + i, estampado_caja=c, blanca_caja=_caja(bl),
                          separacion_px=None if c is None else c[1] - txt_bajo))
    sep = [f['separacion_px'] for f in filas if f['separacion_px'] is not None]
    val['fichate_vos_sin_pisar_estampado'] = dict(texto_cajas_por_cuadro=txt_cajas, texto_borde_inferior_max=txt_bajo,
                                                  separacion_min_px=min(sep), cuadro_min=filas[int(np.argmin(sep))]['cuadro'],
                                                  cumple=min(sep) > 0, por_cuadro=filas)
    tira([MF[162], MF[164], MF[180], MF[205]], ['c162', 'c164', 'c180', 'c205'],
         EVID / 'validaciones' / '3_fichate_vos_c162-c205.jpg', ancho=360)
    print('fichate vos separación mínima', min(sep), flush=True)
    # ---- §8.3b · cierre c206–c280: remeras completas (≥ 20 px), frase y firma en y 270–1130 sin tocar las remeras
    b4 = U.leer(T / 'v2_base.mp4', W, H, n0=206, n1=280)
    pj = json.load(open(T / 'placa' / 'placa.json'))
    filas = []; vis = []
    for i, img in enumerate(b4):
        r, fb, fn = remeras_7896(img)
        r['cuadro'] = 206 + i; filas.append(r)
        if i in (0, 37, 74):
            ov = img.copy(); ov[fb] = (0.6 * ov[fb] + 0.4 * np.array([255, 0, 0])).astype(np.uint8)
            ov[fn] = (0.6 * ov[fn] + 0.4 * np.array([0, 0, 255])).astype(np.uint8)
            im = _img(ov); d = ImageDraw.Draw(im); d.rectangle(r['union'], outline=(255, 255, 0), width=4)
            d.rectangle(pj['frase_letras'], outline=(0, 255, 0), width=3); d.rectangle(pj['firma'], outline=(0, 255, 0), width=3)
            vis.append(np.asarray(im))
    mins = {k: min(f['margen'][k] for f in filas) for k in ('izq', 'der', 'arr', 'abj')}
    arriba_remeras = min(f['union'][1] for f in filas)
    textos_y = [pj['frase_letras'][1], pj['firma'][3]]
    val['cierre'] = dict(margenes_min_px=mins, remeras_completas_20px=all(v >= 20 for v in mins.values()),
                         frase_letras=pj['frase_letras'], firma=pj['firma'],
                         textos_dentro_270_1130=bool(270 <= textos_y[0] and textos_y[1] <= 1130),
                         borde_superior_remeras_min=arriba_remeras, separacion_firma_remeras_px=arriba_remeras - pj['firma'][3],
                         no_tocan=bool(arriba_remeras > pj['firma'][3]), por_cuadro=filas)
    tira(vis + [MF[216], MF[280]], ['c206 máscaras', 'c243 máscaras', 'c280 máscaras', 'c216 máster', 'c280 máster'],
         EVID / 'validaciones' / '4_cierre_remeras_y_placa.jpg', ancho=360)
    print('cierre', mins, 'remeras desde y', arriba_remeras, flush=True)
    # ---- textos: altura de mayúscula y presencia por cuadro
    alt = {d['txt']: altura_mayuscula(ass_path, d['n'][0] + 6) for d in TEXTOS}
    pres = {}
    for d in TEXTOS:
        a_, b_ = d['n']
        for n in (a_ - 1, a_, b_, b_ + 1):
            if 0 <= n < NF:
                pres[f"{d['txt']} c{n}"] = bool((render_ass_gris(ass_path, n) > 8).any())
    rep['textos'].update(altura_mayuscula=alt, presencia_en_bordes=pres,
                         pop_hook_c0=_caja(render_ass_gris(ass_path, 0) > 8))
    print('mayúsculas', {k: v['alto_px'] for k, v in alt.items()}, flush=True)
    # ---- color: resumen por toma + referencia de producto + mapa de cambios
    col = json.load(open(MED / 'color_blanca.json'))
    resumen = {}
    for toma, (rg, _, _) in COLOR.items():
        pc = [col['por_cuadro'][str(n)] for n in range(rg[0], rg[1] + 1)]
        a_ = [p['tela_antes']['b_menos_r'] for p in pc if p['tela_antes']]
        d_ = [p['tela_despues']['b_menos_r'] for p in pc if p['tela_despues']]
        ga = [p['tela_despues']['g_menos_r'] for p in pc if p['tela_despues']]
        ce = [(p['celeste_antes']['b_sobre_r'], p['celeste_despues']['b_sobre_r']) for p in pc if p['celeste_antes'] and p['celeste_despues']]
        resumen[toma] = dict(cuadros=f'c{rg[0]}–c{rg[1]}', b_menos_r_antes=dict(mediana=float(np.median(a_)), min=min(a_), max=max(a_)),
                             b_menos_r_despues=dict(mediana=float(np.median(d_)), min=min(d_), max=max(d_)),
                             g_menos_r_despues_mediana=float(np.median(ga)),
                             celeste_b_sobre_r_cambio_max=round(max(abs(x - y) for x, y in ce), 4) if ce else None,
                             fuera_de_la_blanca_dif_max=max(p['fuera_de_la_zona_dif_max'] for p in pc))
    V.foto_srgb(R / 'PRODUCTO' / 'blanca_espalda_estudio.jpg', T / 'blanca_espalda_estudio_srgb.png')
    prod = np.asarray(Image.open(T / 'blanca_espalda_estudio_srgb.png').convert('RGB'))
    resumen['PRODUCTO_blanca_espalda_estudio'] = U.color_parche(prod, (292, 1316, 877, 1755))
    # Negra intacta: diferencia base sin corregir vs corregida en la tela oscura y en todo lo que no es la Blanca
    negra = {}
    for n in (60, 90, 120, 150, 200, 240, 270):
        a0 = yuv_rgb(*leer_yuv(T / 'v2_base0.mp4', n)); a1 = yuv_rgb(*leer_yuv(T / 'v2_base.mp4', n))
        L0, s0 = lum_sat(a0)
        dif = np.abs(a1 - a0).max(-1)
        negra[f'c{n}'] = dict(dif_max_tela_oscura_L_menor_100=round(float(dif[L0 < 100].max()), 2),
                              pct_pixeles_cambiados=round(float((dif > 0.5).mean() * 100), 2),
                              dif_max_pixeles_saturados_sat_mayor_015=round(float(dif[s0 > 0.15].max()), 2))
        if n in (90, 150, 240):
            ov = np.clip(a0, 0, 255).astype(np.uint8).copy(); ov[dif > 0.5] = [255, 0, 0]
            _img(ov).resize((540, 960)).save(EVID / 'validaciones' / f'5_color_pixeles_cambiados_c{n}.jpg', quality=88)
            tira([np.clip(a0, 0, 255).astype(np.uint8), np.clip(a1, 0, 255).astype(np.uint8)], [f'c{n} antes', f'c{n} después'],
                 EVID / 'validaciones' / f'5_color_antes_despues_c{n}.jpg', ancho=540)
    jdump(dict(resumen=resumen, negra_intacta=negra, metodo=col['metodo'], tomas=col['tomas'],
               residuo_por_cuadro=col['residuo_por_cuadro'], por_cuadro=col['por_cuadro']), EVID / 'color_blanca.json')
    rep['color_resumen'] = resumen; rep['negra_intacta'] = negra
    print('color', json.dumps(resumen, ensure_ascii=False), flush=True)
    # ---- 7896 (rango completo en la fuente): luma del plano 4 dentro de 16–235
    ys = [leer_yuv(f0, n)[0] for n in (220, 270)]
    rep['rango_luma_plano4'] = [int(min(y.min() for y in ys)), int(max(y.max() for y in ys))]
    # ---- continuidad: diferencia media entre cuadros consecutivos (congelados o saltos)
    a = U.leer(f0, 270, 480).astype(np.float32)
    dif = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2, 3))
    rep['diferencia_consecutiva'] = [round(float(x), 2) for x in dif]
    rep['cuadros_casi_iguales_al_anterior'] = [(i + 1, round(float(x), 2)) for i, x in enumerate(dif) if x < 0.6]
    # ---- hojas
    hoja_cuadros(f0, [0, 1, 2, 3, 43, 44, 45, 52, 53, 54, 55, 59, 60, 65, 66, 67, 89, 90, 133, 134, 135, 140, 161, 162,
                      163, 205, 206, 207, 215, 216, 240, 279, 280], EVID / 'hoja_master_cortes_inicio_medio_final.jpg')
    hoja_cuadros(f0, list(range(40, 70)), EVID / 'hoja_master_c40-c69_cada_cuadro.jpg', ancho=200, cols=10)
    for n in (100, 170):
        MF[n] = U.leer(f0, W, H, n0=n, n1=n)[0]
    tira([MF[n] for n in (0, 60, 100, 140, 170, 240)], ['c0', 'c60', 'c100', 'c140', 'c170', 'c240'],
         EVID / 'textos_ancho_telefono_360px.jpg', ancho=360)
    for n in (0, 140, 240, 280):
        _img(MF.get(n, U.leer(f0, W, H, n0=n, n1=n)[0])).save(EVID / f'master_c{n:03d}.png')
    # ---- copias de insumos de evidencia
    for f_ in ('founders.json',):
        shutil.copy2(MED / f_, EVID / f_)
    shutil.copy2(T / 'planos.json', EVID / 'planos.json')
    shutil.copy2(A / 'audio.json', EVID / 'audio.json')
    for k in NOMBRES:
        shutil.copy2(A / f'v2_{k}_eventos.json', EVID / f'audio_eventos_{k}.json')
    for f_ in ('cierre_frase.png', 'cierre_firma.png', 'placa.json'):
        shutil.copy2(T / 'placa' / f_, EVID / f'placa_{f_}')
    for f_ in HJ.glob('*.jpg'):
        shutil.copy2(f_, EVID / f'hoja_fuente_{f_.name}')
    rep['validaciones'] = {k: {kk: vv for kk, vv in v.items() if kk != 'por_cuadro'} for k, v in val.items()}
    jdump(val, EVID / 'validaciones.json')
    jdump(rep, EVID / 'control.json')
    print(json.dumps({k: rep['archivos'][k]['sonoridad'] for k in NOMBRES}), 'casi iguales', rep['cuadros_casi_iguales_al_anterior'])


def atomos(f):
    """átomos de primer nivel del MP4 en orden (faststart = moov antes de mdat)."""
    import struct
    out = []
    with open(f, 'rb') as h:
        while True:
            hd = h.read(8)
            if len(hd) < 8:
                break
            n, k = struct.unpack('>I4s', hd)
            if n == 1:
                n = struct.unpack('>Q', h.read(8))[0]; h.seek(n - 16, 1)
            else:
                h.seek(n - 8, 1)
            out.append(k.decode('latin1'))
            if n == 0:
                break
    return out


def silencio_final(a, sr=SR, umbral=-60.0):
    """segundos al final del archivo con RMS de 10 ms por debajo de `umbral` dBFS."""
    w = sr // 100; m = a.mean(1); n = len(m) // w
    v = 20 * np.log10(np.sqrt(np.square(m[:n * w].reshape(n, w)).mean(1)) + 1e-12)
    k = 0
    while k < n and v[n - 1 - k] < umbral:
        k += 1
    return round(k * 0.01, 2)


def hoja_cuadros(mp4, cuadros, salida, ancho=240, cols=9):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 20)
    tiles = []
    for n in cuadros:
        im = _img(U.leer(mp4, ancho, round(ancho * 16 / 9), n0=n, n1=n)[0]); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 70, 26], fill=(0, 0, 0)); d.text((4, 2), f'c{n}', font=fnt, fill=(255, 255, 0)); tiles.append(im)
    filas = math.ceil(len(tiles) / cols)
    Wd = Image.new('RGB', (cols * (ancho + 2), filas * (tiles[0].height + 2)), (30, 30, 30))
    for i, t in enumerate(tiles):
        Wd.paste(t, ((i % cols) * (ancho + 2), (i // cols) * (tiles[0].height + 2)))
    Wd.save(salida, quality=90)


# =====================================================================================================
# etapa entregar · EXPORTACIONES/ + carpeta de la pieza + evidencia; verificación de las copias (md5 de flujos)
# =====================================================================================================
def etapa_entregar():
    res = {}
    for k, nombre in NOMBRES.items():
        for dst in (EXP / nombre, PIEZA / nombre):
            if dst.exists():
                raise RuntimeError(f'{dst} ya existe: no se sobrescribe')
    ev = PIEZA / EVID.name
    if ev.exists():
        raise RuntimeError(f'{ev} ya existe')
    for k, nombre in NOMBRES.items():
        for dst in (EXP / nombre, PIEZA / nombre):
            shutil.copyfile(MAS / nombre, dst)
    shutil.copytree(EVID, ev)
    time.sleep(12)                                  # montaje de red: esperar antes de verificar
    for k, nombre in NOMBRES.items():
        src = MAS / nombre
        ref = dict(bytes=src.stat().st_size, sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                   md5_video=U.md5_stream(src, 'v'), md5_audio=U.md5_stream(src, 'a'))
        res[str(src)] = ref
        for dst in (EXP / nombre, PIEZA / nombre):
            got = dict(bytes=dst.stat().st_size, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
                       md5_video=U.md5_stream(dst, 'v'), md5_audio=U.md5_stream(dst, 'a'))
            err = subprocess.run(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(dst), '-f', 'null', '-']),
                                 capture_output=True, text=True).stderr.strip()
            cuerpo = dst.read_bytes()
            res[str(dst)] = dict(got, flujos_iguales=(got['md5_video'] == ref['md5_video'] and got['md5_audio'] == ref['md5_audio']),
                                 byte_a_byte=(got == ref), decodifica_sin_errores=(err == ''), atomos=atomos(dst),
                                 marcas_ubicacion=[m.decode() for m in (b'ISO6709', b'location', b'com.apple.quicktime') if m in cuerpo],
                                 etiquetas=json.loads(U.run(['ffprobe', '-v', 'error', '-show_entries', 'format_tags', '-of', 'json', str(dst)]))
                                 .get('format', {}).get('tags', {}))
            print(dst, res[str(dst)], flush=True)
    n_local = sum(1 for _ in EVID.rglob('*') if _.is_file()); n_red = sum(1 for _ in ev.rglob('*') if _.is_file())
    res['evidencia'] = dict(carpeta=str(ev), archivos_local=n_local, archivos_red=n_red)
    jdump(res, T / 'entrega.json')
    print('evidencia', n_local, n_red)


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    globals()['etapa_' + etapa]()
