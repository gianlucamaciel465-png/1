#!/usr/bin/env python3
"""GTA6 «La misión» · capa del «ROCCÉ» tono sobre tono extraída de IMG_7887 4K (Pedro, 19/11/2026, v01).

Corrección 4 de 03_roma_revision_pre_v00.md: en la foto de estudio el ROCCÉ casi no se ve (6 niveles de exceso de luz)
y su alfa sale rota. En 7887 2,0–3,6 s (4K, sol rasante) se lee: es una aplicación tipo «varsity» (relleno de fieltro
con borde cosido en zigzag). Se extrae como CAPA DE RAZÓN respecto de la tela, en coordenadas de la foto de estudio:

    R(u, v) = observado_lineal / sombreado_de_la_tela          (por canal; R = 1 es tela lisa)

  1. Registro por cuadro (homografía + malla) de compuesto.py (TRABAJO/gta/compuesto/registro_7887.npz), hecho contra
     el «Founders Privée» de estudio: el ROCCÉ queda ubicado por la misma transformación (está en la misma plantilla).
  2. Para cada celda de una grilla en la zona del ROCCÉ (coordenadas de la foto de estudio × 1,5) se calcula su punto
     en el cuadro (homografía + malla), se lee el 4K (bilineal) y el sombreado de la tela del cuadro a 1080 (convolución
     normalizada multiescala, sin estampado, sin la zona del ROCCÉ, sin piel ni roca).
  3. Mediana temporal por celda en 2,0–3,6 s (c60–c108, 49 cuadros). También por separado cuadros pares e impares, para
     medir cuán limpia y estable es la capa (y para probar el compuesto sin usar el mismo cuadro para extraer y medir).
  4. Limpieza: alfa suave por |R_luma − 1| (0,05 → 0,15), componentes chicos afuera; fuera de las letras R = 1.

Uso (venv): python rocce_capa.py   → TRABAJO/gta/compuesto/rocce_capa.npz, rocce_capa.json, rocce_capa_hoja.jpg
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from scipy import ndimage as nd
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, '/home/user/1/scripts/gta'); sys.path.insert(0, '/home/user/1/scripts/fmt')
import compuesto as C                     # noqa: E402
from comun import guardar_json            # noqa: E402
import fmt03 as U                         # noqa: E402

TC = C.TC
K0, K1 = 3, 51                            # c60–c108 = 2,00–3,60 s de la toma (k = cuadro del tramo c57–c109)
G = 1.5                                   # celdas de grilla por píxel de la foto de estudio
CROP4K = (880, 1440, 2160, 2400)          # x0, y0, x1, y1 en la toma 2160×3840 (cubre la zona del ROCCÉ en c60–c108)
FONT = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'


def zona_rocce(M, margen=26):
    """caja de la zona del ROCCÉ en coordenadas del recorte de la foto de estudio (680×370): de la caja de la alfa de
    estudio (incompleta) con margen, y hasta 6 px arriba del Founders."""
    x0, y0, x1, y1 = M['bbR']
    yF = M['bbF'][1]
    h, w = M['aF'].shape
    # hasta 40 px debajo del borde superior del Founders: la R y la É (el arco baja en las puntas) llegan más abajo;
    # lo que es Founders se excluye celda por celda (huella de su alfa de estudio dilatada)
    return (max(0, x0 - margen), max(0, y0 - margen), min(w, x1 + margen), min(h, yF + 40))


def cuadros_4k():
    """cuadros 4K (RGB uint8) recortados a CROP4K, misma cadena de color que el 1080 (format=yuv420p) y fps 30."""
    x0, y0, x1, y1 = CROP4K
    d = U.desde_cuadro('IMG_7887', C.N0 + K0)
    n = K1 - K0 + 1
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{d:.4f}', '-i', '/home/user/1/ORIGINALES/IMG_7887.mov',
                          '-t', f'{n / 30 + 0.2:.4f}', '-an', '-vf', f'format=yuv420p,fps=30,crop={x1 - x0}:{y1 - y0}:{x0}:{y0}',
                          '-frames:v', str(n), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(n, y1 - y0, x1 - x0, 3)


def adelante(Hp, malla, d, tx, ty):
    """plantilla (px a escala S0) → cuadro 1080: homografía + desplazamiento de la malla."""
    q = Hp @ np.stack([tx, ty, np.ones_like(tx)])
    du, dv = malla.desp(tx, ty, d)
    return q[0] / q[2] + du, q[1] / q[2] + dv


def main():
    M = C.modelo_estudio(); Tm = C.plantilla(M)
    lk = C.LK(Tm); th, tw = Tm.shape; malla = C.Malla(lk, tw, th)
    R = dict(np.load(C.REG))
    F = C.cuadros_7887()
    F4 = cuadros_4k()
    assert len(F4) == K1 - K0 + 1, len(F4)
    zx0, zy0, zx1, zy1 = zona_rocce(M)
    gw, gh = int((zx1 - zx0) * G), int((zy1 - zy0) * G)
    gv, gu = np.mgrid[0:gh, 0:gw].astype(np.float64)
    u = zx0 + (gu + 0.5) / G - 0.5; v = zy0 + (gv + 0.5) / G - 0.5          # px de la foto (recorte)
    tx, ty = u.ravel() * C.S0, v.ravel() * C.S0                            # px de la plantilla
    huellaF = nd.map_coordinates(nd.binary_dilation(M['aF'] > 0.05, iterations=6).astype(np.float32),
                                 [v.ravel(), u.ravel()], order=0, mode='constant') > 0.5
    pilas = []; validos = []; alinea = []
    for j, k in enumerate(range(K0, K1 + 1)):
        f = F[k]; ff = f.astype(np.float32)
        B, L, sat = C.espalda(f, C.ROI0)
        P, _ = C.exceso(L, B)
        Hp, d = R['Hp'][k], R['d'][k]
        xf, yf = adelante(Hp, malla, d, tx, ty)
        # sombreado de la tela a 1080 sin estampado ni zona del ROCCÉ (huella de la grilla dilatada)
        zona = np.zeros((C.H, C.W), bool)
        xi = np.clip(np.round(xf).astype(int), 0, C.W - 1); yi = np.clip(np.round(yf).astype(int), 0, C.H - 1)
        zona[yi, xi] = True
        zona = nd.binary_dilation(nd.binary_closing(zona, iterations=3), iterations=10)
        dentro = B | (nd.binary_dilation(B, iterations=25) & (sat < 0.22))
        occ = C.oclusion(ff, dentro)
        tela = B & ~(P > 0.12) & ~occ & ~zona
        x0b, y0b = max(0, int(xf.min()) - 200), max(0, int(yf.min()) - 200)
        x1b, y1b = min(C.W, int(xf.max()) + 200), min(C.H, int(yf.max()) + 200)
        S = C.sombreado_multi(C.lin(ff), tela, (x0b + 160, y0b + 160, x1b - 160, y1b - 160))
        s_ = np.stack([nd.map_coordinates(S[..., c], [yf, xf], order=1, mode='nearest') for c in range(3)], -1)
        # 4K: coordenadas de la toma = 2·(x + 0,5) − 0,5, menos el recorte
        X = 2 * (xf + 0.5) - 0.5 - CROP4K[0]; Y = 2 * (yf + 0.5) - 0.5 - CROP4K[1]
        f4 = C.lin(F4[j].astype(np.float32))
        o_ = np.stack([nd.map_coordinates(f4[..., c], [Y, X], order=1, mode='constant', cval=np.nan) for c in range(3)], -1)
        ok = (np.isfinite(o_).all(-1) & (X >= 0) & (Y >= 0) & (X <= F4.shape[2] - 1) & (Y <= F4.shape[1] - 1)
              & (xf >= 0) & (xf <= C.W - 1) & (yf >= 0) & (yf <= C.H - 1))
        # solo la espalda (no el borde gris claro de «dentro», que en este tramo agarra la Blanca y el cielo)
        ok &= nd.map_coordinates(nd.binary_erosion(B, iterations=3).astype(np.float32), [yf, xf], order=0, mode='constant') > 0.5
        ok &= nd.map_coordinates(occ.astype(np.float32), [yf, xf], order=0, mode='constant') < 0.5
        ok &= ~huellaF
        r = np.where(ok[:, None], o_ / np.maximum(s_, 1e-4), np.nan)
        pilas.append(r.reshape(gh, gw, 3).astype(np.float32)); validos.append(ok.reshape(gh, gw))
        alinea.append((float(np.median(xf)), float(np.median(yf))))
        print(k, 'válidas', round(float(ok.mean()), 3), flush=True)
    Pz = np.stack(pilas)                                                  # n × gh × gw × 3
    with np.errstate(all='ignore'):
        med = np.nanmedian(Pz, 0); par = np.nanmedian(Pz[0::2], 0); imp = np.nanmedian(Pz[1::2], 0)
    cobertura = np.stack(validos).mean(0)
    lum = lambda x: C.luma(np.nan_to_num(x, nan=1.0))
    rl = lum(med)
    hay = cobertura > 0.2

    # fondo de tela local (el sombreado del cuadro no ve bien adentro de la zona, que se excluyó entera): convolución
    # normalizada σ 20 celdas sobre lo que no es letra, en dos vueltas; las letras (relleno de fieltro) son más claras
    def fondo(excl):
        w = (hay & ~excl).astype(np.float32)
        return nd.gaussian_filter(rl * w, 20) / np.maximum(nd.gaussian_filter(w, 20), 1e-4)
    bg = fondo(rl > 1.3)
    let = (rl / bg > 1.15) & hay
    bg = fondo(nd.binary_dilation(let, iterations=6))
    rn = rl / bg
    # histéresis: núcleo del relleno (rn suavizado σ 2 > 1,35) y después se crece hasta 4 celdas dentro de rn > 1,12 (así no se pegan
    # brillos de pliegues ni el halo del Founders, que quedan por debajo de 1,30)
    let = nd.binary_opening((nd.gaussian_filter(rn, 2.0) > 1.35) & hay, iterations=2)
    lab, n = nd.label(let); s = nd.sum(let, lab, range(1, n + 1))
    hF = huellaF.reshape(gh, gw)
    borde = nd.binary_dilation(~(hay | hF), iterations=4); borde[:, :4] = True; borde[:, -4:] = True
    toca = set(np.unique(lab[borde & (lab > 0)]).tolist())
    # las letras: componentes grandes que no tocan el borde de la cobertura (ahí hay pliegues y el canto de la espalda)
    cand = [i + 1 for i, v in enumerate(s) if v > 0.002 * let.size and (i + 1) not in toca]
    # «ROCCÉ»: las 5 letras son los 5 componentes más grandes; la tilde es un componente chico que cae arriba de una
    # de ellas (centro x dentro de su ancho y centro y por encima de su borde superior). El resto (pliegues) afuera.
    cand.sort(key=lambda i: -s[i - 1]); let5 = cand[:5]
    sl = nd.find_objects(lab)
    tilde = [i for i in cand[5:] if any(sl[l - 1][1].start <= nd.center_of_mass(lab == i)[1] <= sl[l - 1][1].stop
                                       and nd.center_of_mass(lab == i)[0] < sl[l - 1][0].start for l in let5)]
    let = np.isin(lab, let5 + tilde)
    let = let | ((rn > 1.12) & hay & nd.binary_dilation(let, iterations=4))
    # alfa: relleno + 5 celdas (borde cosido, más oscuro que la tela), borde suave
    a = nd.gaussian_filter(nd.binary_dilation(nd.binary_fill_holes(let) & let | let, iterations=5).astype(np.float32), 1.2) * hay

    bgs = np.where(np.isfinite(bg) & (bg > 1e-3), bg, 1.0)              # sin cobertura: fondo 1 (no divide por 0)

    def limpia(x):
        xn = np.nan_to_num(x, nan=1.0) / bgs[..., None]                   # tela local = 1
        return np.nan_to_num(1 + a[..., None] * (xn - 1), nan=1.0, posinf=1.0, neginf=1.0)
    capa, capa_par, capa_imp = limpia(med), limpia(par), limpia(imp)
    letras = a > 0.5
    dif = lum(capa_par) - lum(capa_imp); con = lum(capa) - 1
    rl = lum(capa)
    rep = dict(
        fuente='IMG_7887 4K (2160×3840), c60–c108 = 2,00–3,60 s, misma cadena de color que el tramo (format=yuv420p)',
        grilla=dict(zona_foto_recorte=[zx0, zy0, zx1, zy1], celdas_por_px_foto=G, tamano=[gw, gh]),
        cuadros=len(Pz), cobertura_media_en_letras=round(float(cobertura[letras].mean()), 3),
        celdas_letras=int(letras.sum()), fraccion_zona_letras=round(float(letras.mean()), 3), componentes_letras=int(nd.label(let)[1]),
        tilde_encontrada=bool(tilde),
        razon_luma_letras=dict(mediana=round(float(np.median(rl[letras])), 3), p10=round(float(np.percentile(rl[letras], 10)), 3),
                               p90=round(float(np.percentile(rl[letras], 90)), 3)),
        limpieza=dict(
            contraste_rms_letras=round(float(np.sqrt(np.mean(con[letras] ** 2))), 4),
            dif_rms_pares_vs_impares_letras=round(float(np.sqrt(np.mean(dif[letras] ** 2))), 4),
            relacion=round(float(np.sqrt(np.mean(dif[letras] ** 2)) / max(1e-6, np.sqrt(np.mean(con[letras] ** 2)))), 3),
            nota='diferencia entre la capa de cuadros pares y la de impares, relativa al contraste de las letras '
                 '(0 = idénticas; mide ruido + error de registro en la zona del ROCCÉ)'),
        posicion_media_en_1080=[round(float(np.mean([p[0] for p in alinea])), 1), round(float(np.mean([p[1] for p in alinea])), 1)])
    np.savez_compressed(TC / 'rocce_capa.npz', capa=capa.astype(np.float32), capa_par=capa_par.astype(np.float32),
                        capa_impar=capa_imp.astype(np.float32), alfa=a.astype(np.float32), cobertura=cobertura.astype(np.float32),
                        zona=np.array([zx0, zy0, zx1, zy1], np.float64), G=np.array(G), rn=rn.astype(np.float32),
                        hay=hay, huellaF=hF)
    guardar_json(rep, TC / 'rocce_capa.json')
    hoja(M, capa, capa_par, capa_imp, a, F4, rep)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


def _vis(capa, base=0.035):
    """capa de razón vista sobre una tela lisa de luminancia lineal «base» (≈ la Negra al sol), en sRGB."""
    return np.clip(C.srgb(base * capa) + 0.5, 0, 255).astype(np.uint8)


def hoja(M, capa, par, imp, a, F4, rep):
    fnt = ImageFont.truetype(FONT, 20)
    zx0, zy0, zx1, zy1 = rep['grilla']['zona_foto_recorte']
    est = np.asarray(Image.open(C.PROD).convert('RGB'))[C.CROP[1] + zy0:C.CROP[1] + zy1, C.CROP[0] + zx0:C.CROP[0] + zx1]
    gw, gh = rep['grilla']['tamano']
    est = np.asarray(Image.fromarray(est).resize((gw, gh), Image.LANCZOS))
    estc = np.clip((est.astype(np.float32) - est.mean()) * 4 + 60, 0, 255).astype(np.uint8)     # contraste ×4 para ver algo
    v4 = F4[(K1 - K0) // 2]
    dif = np.clip(128 + (C.luma(par) - C.luma(imp)) * 400, 0, 255).astype(np.uint8)
    tiles = [(estc, 'foto de estudio, misma zona (contraste ×4)'),
             (_vis(capa), f"capa extraída (mediana {rep['cuadros']} cuadros) sobre tela lisa"),
             ((np.clip(a, 0, 1) * 255).astype(np.uint8), 'alfa de las letras (limpieza)'),
             (np.stack([dif] * 3, -1), f"pares − impares ×400 (relación {rep['limpieza']['relacion']})"),
             (np.asarray(Image.fromarray(v4).resize((gw, int(v4.shape[0] * gw / v4.shape[1])), Image.LANCZOS)), 'IMG_7887 4K c84 (recorte, reducido)')]
    filas = []
    for im, t in tiles:
        im = im if im.ndim == 3 else np.stack([im] * 3, -1)
        tt = Image.new('RGB', (im.shape[1], im.shape[0] + 30), (20, 20, 20)); tt.paste(Image.fromarray(im), (0, 30))
        ImageDraw.Draw(tt).text((6, 4), t, font=fnt, fill=(255, 220, 80)); filas.append(tt)
    W_ = max(t.width for t in filas); H_ = sum(t.height + 8 for t in filas)
    out = Image.new('RGB', (W_, H_), (20, 20, 20)); y = 0
    for t in filas:
        out.paste(t, (0, y)); y += t.height + 8
    out.save(TC / 'rocce_capa_hoja.jpg', quality=90)


if __name__ == '__main__':
    main()
