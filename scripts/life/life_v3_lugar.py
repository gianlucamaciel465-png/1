#!/usr/bin/env python3
"""Roccé Life · V3 «5 domingos» · prueba de lugar de la foto del paso 8 (Pedro, 25/11/2026).

Condición 2 de Roma (07_roma_aprobacion_guiones_t2.md): «Esto.» con PRODUCTO/blanca_espalda_roca_ola.jpg solo si se
demuestra que es el mismo lugar que IMG_7884 (comparar la roca y la ubicación de la Blanca; la foto no tiene EXIF).

Método (OpenCV 4.10 headless, entorno aislado TRABAJO/life2/v3/cvenv; se corre con ese python):
  1. Puntos SIFT de la foto (sRGB) y de cada cuadro de prueba, a 1400 px de lado mayor; razón de Lowe 0,8.
  2. Solo cuentan los pares que caen en ROCA en las dos imágenes (marrón saturado o roca mojada oscura, erosionado 15 px,
     fuera de la remera ensanchada 31 px): el estampado es el mismo en todas las tomas y el mar se mueve.
  3. Geometría: matriz fundamental por RANSAC (umbral 2 px). Muchos pares de roca consistentes con UNA geometría de
     dos vistas = la misma roca. Controles negativos: rocas de otras tomas de la misma costa (7887, 7894, 7896).
  4. Ubicación de la Blanca: homografía con los pares de roca a menos de 250 px de la remera en la foto (la losa donde
     apoya); se lleva el contorno de la remera de la foto al cuadro y se mide la superposición (IoU) con la remera del
     cuadro, y la distancia entre los centros de «ROCCÉ» proyectado y medido.
Salida: TRABAJO/life2/v3/med/lugar/lugar.json + imágenes.
"""
import json, sys, subprocess
from pathlib import Path
import cv2, numpy as np

R = Path('/home/user/1')
OUT = R / 'TRABAJO/life2/v3/med/lugar'
FOTO = OUT / 'foto_srgb.png'           # PRODUCTO/blanca_espalda_roca_ola.jpg en sRGB (video.foto_srgb, etapa lugar0)
HLG = ('zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,'
       'zscale=t=bt709:m=bt709:r=tv,format=gbrp')
PRUEBAS = [  # (toma, segundo, hdr, rol)
    ('IMG_7884', 2.8, False, 'paso 7 (inicio)'), ('IMG_7884', 3.3, False, 'paso 7'), ('IMG_7884', 3.9, False, 'paso 7 (ola)'),
    ('IMG_7884', 4.367, False, 'paso 7 (último cuadro)'),
    ('IMG_4627', 0.0, True, 'paso 10 (misma Blanca, iPhone 13)'), ('IMG_7885', 0.5, False, 'paso 1'),
    ('IMG_7887', 2.0, False, 'control: otra roca de la sesión'), ('IMG_7894', 1.0, False, 'control: otra roca'),
    ('IMG_7896', 2.0, False, 'control: otra roca'),
]
# caja de búsqueda de la remera (fracción del cuadro x0, y0, x1, y1)
CAJA_FOTO = (0.12, 0.52, 0.68, 0.96)
CAJA_CUADRO = (0.0, 0.30, 1.0, 1.0)


def extraer(toma, seg, hdr, out):
    vf = (HLG + ',' if hdr else '') + 'scale=1080:1920'
    subprocess.run(['nice', '-n', '10', 'ffmpeg', '-v', 'error', '-y', '-ss', f'{seg:.3f}', '-i', str(R / 'ORIGINALES' / f'{toma}.mov'),
                    '-frames:v', '1', '-vf', vf, str(out)], check=True)


def kp(img, maxw=1400):
    s = maxw / max(img.shape[:2]); im = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    k, d = cv2.SIFT_create(nfeatures=12000).detectAndCompute(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), None)
    return im, k, d


def medidas(im, caja):
    f = im.astype(np.float32); b, g, r = f[..., 0], f[..., 1], f[..., 2]
    L = .2126 * r + .7152 * g + .0722 * b; mx = f.max(-1); mn = f.min(-1); sat = (mx - mn) / (mx + 1)
    h, w = L.shape
    x0, y0, x1, y1 = int(caja[0] * w), int(caja[1] * h), int(caja[2] * w), int(caja[3] * h)
    br = np.zeros((h, w), np.uint8); br[y0:y1, x0:x1] = ((L > 150) & (sat < 0.15))[y0:y1, x0:x1]
    br = cv2.morphologyEx(br, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(br)
    i = 1 + int(np.argmax(st[1:, 4]))
    sh = cv2.morphologyEx((lab == i).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
    c, _ = cv2.findContours(sh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(c, key=cv2.contourArea)
    shf = np.zeros_like(sh); cv2.drawContours(shf, [c], -1, 1, -1)
    # «ROCCÉ»: letras oscuras (L < 90) dentro de la remera, en su tercio superior
    ys, xs = np.nonzero(shf); yt = ys.min() + 0.45 * (ys.max() - ys.min())
    let = shf.astype(bool) & (L < 90); let[int(yt):] = False
    ly, lx = np.nonzero(let)
    roc = (float(lx.mean()), float(ly.mean())) if len(lx) > 50 else None
    rock = (((sat > 0.22) & (L < 210) & (r > b)) | (L < 60)).astype(np.uint8)
    rock = cv2.morphologyEx(rock, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    rock = cv2.erode(rock, np.ones((15, 15), np.uint8)) & (1 - cv2.dilate(shf, np.ones((31, 31), np.uint8)))
    return shf.astype(bool), rock.astype(bool), c, roc


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    foto = cv2.imread(str(FOTO)); fi, fk, fd = kp(foto); fsh, frk, fc, froc = medidas(fi, CAJA_FOTO)
    dist = cv2.distanceTransform((1 - fsh).astype(np.uint8), cv2.DIST_L2, 5)
    on = lambda M, p: M[np.clip(p[:, 1].astype(int), 0, M.shape[0] - 1), np.clip(p[:, 0].astype(int), 0, M.shape[1] - 1)]
    rep = dict(metodo=__doc__, foto=dict(archivo='PRODUCTO/blanca_espalda_roca_ola.jpg', puntos=len(fk),
                                         pixeles_roca=int(frk.sum()), pixeles_remera=int(fsh.sum())), pruebas=[])
    cv2.imwrite(str(OUT / 'mascaras_foto.jpg'), np.concatenate([fi, np.dstack([frk * 255, fsh * 255, np.zeros_like(frk, np.uint8)]).astype(np.uint8)], 1))
    for toma, seg, hdr, rol in PRUEBAS:
        png = OUT / f'{toma}_{seg:.3f}.png'
        if not png.exists():
            extraer(toma, seg, hdr, png)
        img = cv2.imread(str(png)); ii, ik, idd = kp(img); ish, irk, ic, iroc = medidas(ii, CAJA_CUADRO)
        m = cv2.BFMatcher().knnMatch(fd, idd, k=2); good = [a for a, b in m if a.distance < 0.8 * b.distance]
        p1 = np.float32([fk[g.queryIdx].pt for g in good]); p2 = np.float32([ik[g.trainIdx].pt for g in good])
        sel = on(frk, p1) & on(irk, p2); q1, q2 = p1[sel], p2[sel]
        fila = dict(toma=toma, segundo=seg, rol=rol, pares_razon=len(good), pares_roca=int(sel.sum()))
        mf = np.zeros(len(q1), bool)
        if len(q1) >= 8:
            cv2.setRNGSeed(7)
            F, mf_ = cv2.findFundamentalMat(q1, q2, cv2.FM_RANSAC, 2.0, 0.999, 5000)
            if mf_ is not None:
                mf = mf_.ravel().astype(bool)
        fila['roca_consistentes_F'] = int(mf.sum())
        fila['fraccion_consistente'] = round(float(mf.sum() / max(len(q1), 1)), 3)
        near = on(dist < 250, q1) & mf
        fila['roca_junto_a_la_remera'] = int(near.sum())
        if near.sum() >= 12:
            cv2.setRNGSeed(7)
            Hh, mh = cv2.findHomography(q1[near], q2[near], cv2.RANSAC, 8.0)
            pc = cv2.perspectiveTransform(fc.astype(np.float32).reshape(-1, 1, 2), Hh)
            proj = np.zeros(ii.shape[:2], np.uint8); cv2.drawContours(proj, [pc.astype(np.int32)], -1, 1, -1)
            pb = proj.astype(bool)
            fila['homografia_inliers'] = int(mh.sum())
            fila['iou_remera'] = round(float((pb & ish).sum() / (pb | ish).sum()), 3)
            fila['remera_proyectada_dentro_de_la_medida'] = round(float((pb & ish).sum() / pb.sum()), 3)
            if froc and iroc:
                pr = cv2.perspectiveTransform(np.float32([[froc]]), Hh)[0, 0]
                diag = float(np.hypot(*ii.shape[:2]))
                fila['rocce_proyectado'] = [round(float(pr[0]), 1), round(float(pr[1]), 1)]
                fila['rocce_medido'] = [round(iroc[0], 1), round(iroc[1], 1)]
                fila['rocce_distancia_pct_diagonal'] = round(float(np.hypot(pr[0] - iroc[0], pr[1] - iroc[1]) / diag * 100), 2)
            # imagen
            h = 900; a = cv2.resize(fi, (round(fi.shape[1] * h / fi.shape[0]), h)); sa = h / fi.shape[0]
            b = ii.copy(); cv2.drawContours(b, [ic], -1, (0, 255, 255), 4); cv2.drawContours(b, [pc.astype(np.int32)], -1, (255, 0, 255), 4)
            if froc and iroc:
                cv2.drawMarker(b, (int(iroc[0]), int(iroc[1])), (0, 255, 255), cv2.MARKER_CROSS, 40, 4)
                cv2.drawMarker(b, (int(pr[0]), int(pr[1])), (255, 0, 255), cv2.MARKER_TILTED_CROSS, 40, 4)
            b = cv2.resize(b, (round(ii.shape[1] * h / ii.shape[0]), h)); sb = h / ii.shape[0]
            cv2.drawContours(a, [(fc * sa).astype(np.int32)], -1, (0, 255, 255), 3)
            Vv = np.concatenate([a, b], 1)
            for (x1, y1), (x2, y2), ok in zip(q1, q2, mf):
                if ok:
                    cv2.line(Vv, (int(x1 * sa), int(y1 * sa)), (int(x2 * sb + a.shape[1]), int(y2 * sb)), (0, 255, 0), 1)
            cv2.rectangle(Vv, (0, 0), (Vv.shape[1], 40), (0, 0, 0), -1)
            cv2.putText(Vv, f"foto vs {toma} {seg:.2f}s  roca: {fila['roca_consistentes_F']}/{fila['pares_roca']} pares consistentes  "
                        f"IoU remera {fila['iou_remera']}", (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.imwrite(str(OUT / f'lugar_foto_vs_{toma}_{seg:.3f}.jpg'), Vv, [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(json.dumps(fila, ensure_ascii=False), flush=True)
        rep['pruebas'].append(fila)
    json.dump(rep, open(OUT / 'lugar.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
