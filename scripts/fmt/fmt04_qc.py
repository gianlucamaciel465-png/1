#!/usr/bin/env python3
"""FMT-04 · control del máster v01/v02 (Pedro, 17/11/2026). Genera la evidencia en <carpeta de la versión>/qc/.

    FMT04_VERSION=v02 nice -n 10 /home/user/1/TRABAJO/venv/bin/python /home/user/1/scripts/fmt/fmt04_qc.py

Mide sobre el MP4 entregado (no sobre los intermedios): decodificación, ffprobe, metadatos, sonoridad, huellas,
cuadros de control, márgenes del estampado contra los bordes y contra los textos, color contra las fotos de producto,
cuadros repetidos y niveles de audio por tramo.
"""
import sys, json, subprocess
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, '/home/user/1/scripts/fmt')
import video as V
import fmt04_util as U
import fmt04 as R

D = R.D; Q = D / 'qc'; Q.mkdir(exist_ok=True)
MP4 = D / f'{R.NOMBRE}_{R.VERSION}.mp4'; MP4_SM = D / f'{R.NOMBRE}_SINMUSICA_{R.VERSION}.mp4'
PLANOS = R.PLANOS_QC
RANGO = {n: (a, b) for n, _, a, b in PLANOS}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def tecnico():
    out = {}
    for f in (MP4, MP4_SM):
        k = f.name
        dec = run(['ffmpeg', '-v', 'error', '-i', str(f), '-f', 'null', '-'])
        pr = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-count_frames', '-of', 'json', str(f)]).stdout)
        json.dump(pr, open(Q / f'ffprobe_{f.stem}.json', 'w'), indent=1, ensure_ascii=False)
        tags = {'format': pr['format'].get('tags', {}), **{f"stream{s['index']}": s.get('tags', {}) for s in pr['streams']}}
        crudo = f.read_bytes()
        ub = any(x in crudo for x in (b'\xa9xyz', b'com.apple.quicktime.location', b'ISO6709'))
        e = run(['ffmpeg', '-nostats', '-i', str(f), '-vn', '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-']).stderr
        g = lambda key: float([l for l in e.splitlines() if l.strip().startswith(key)][-1].split()[1])
        # muestras de audio decodificadas vs cuadros de video
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(f), '-vn', '-f', 's16le', '-ac', '1', '-ar', '48000', '-'],
                             capture_output=True).stdout
        v = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]; a = [s for s in pr['streams'] if s['codec_type'] == 'audio'][0]
        out[k] = dict(decodifica_sin_errores=dec.stdout + dec.stderr == '', errores=(dec.stderr or '')[:500],
                      video=dict(codec=v['codec_name'], perfil=v.get('profile'), nivel=v.get('level'), pix_fmt=v['pix_fmt'],
                                 ancho=v['width'], alto=v['height'], fps=v['avg_frame_rate'], cuadros=int(v['nb_read_frames']),
                                 duracion=float(v['duration']), color=[v.get('color_range'), v.get('color_space'),
                                                                        v.get('color_transfer'), v.get('color_primaries')]),
                      audio=dict(codec=a['codec_name'], perfil=a.get('profile'), hz=int(a['sample_rate']), canales=a['channels'],
                                 duracion=float(a['duration']), muestras_decodificadas=len(raw) // 2,
                                 duracion_decodificada=round(len(raw) / 2 / 48000, 4)),
                      formato=dict(duracion=float(pr['format']['duration']), bytes=int(pr['format']['size']),
                                   bit_rate=int(pr['format']['bit_rate'])),
                      etiquetas=tags, ubicacion_en_bytes=ub,
                      ebur128=dict(I_LUFS=g('I:'), LRA=g('LRA:'), pico_dBTP=g('Peak:')),
                      faststart=crudo.find(b'moov') < crudo.find(b'mdat'),
                      huella=R.huella(f))
    out['misma_imagen'] = out[MP4.name]['huella']['md5_video'] == out[MP4_SM.name]['huella']['md5_video']
    json.dump(out, open(Q / 'tecnico.json', 'w'), indent=1, ensure_ascii=False)
    return out


def cuadros():
    cortes = R.CORTES
    for c in cortes:
        for n in (c - 1, c, c + 1):
            V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(MP4), '-vf', f"select='eq(n\\,{n})'", '-frames:v', '1', '-fps_mode',
                  'vfr', '-q:v', '2', str(Q / f'corte_c{c}_cuadro_c{n:03d}.jpg')])
        # tira antes / en / después a media resolución
        V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(MP4), '-vf',
              f"drawtext=fontfile={U.FONT}:text='c%{{n}}':x=16:y=16:fontsize=56:fontcolor=yellow:box=1:boxcolor=black@0.6,"
              f"select='between(n\\,{c - 1}\\,{c + 1})',scale=540:-2,tile=3x1:padding=4", '-frames:v', '1', '-fps_mode', 'vfr',
              str(Q / f'corte_c{c}_tira.jpg')])
    for n in (0, 60, 150, 195, 260, 299):
        V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(MP4), '-vf', f"select='eq(n\\,{n})'", '-frames:v', '1', '-fps_mode', 'vfr',
              '-q:v', '2', str(Q / f'cuadro_c{n:03d}.jpg')])
    U.hoja_c(MP4, Q / 'hoja_contacto_05s.jpg', cada=0.5, ancho=216, cols=10)
    U.hoja_c(MP4, Q / 'hoja_contacto_01s.jpg', cada=0.1, ancho=135, cols=20)


# ---------------------------------------------------------------- estampado: detección por plano (media resolución)
def leer_master(w=540, h=960):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(MP4), '-vf', f'scale={w}:{h}:flags=area,format=rgb24', '-f', 'rawvideo', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def rodeado(lab, i, s, lum, lo=None, hi=None, pad=5):
    y0, y1 = max(0, s[0].start - pad), min(lum.shape[0], s[0].stop + pad); x0, x1 = max(0, s[1].start - pad), min(lum.shape[1], s[1].stop + pad)
    m = np.median(lum[y0:y1, x0:x1][lab[y0:y1, x0:x1] != i + 1])
    return (lo is None or m >= lo) and (hi is None or m <= hi)


def estampado(plano, f):
    """máscara del estampado (media resolución) para el plano dado."""
    a = f.astype(np.float32); lum = a.mean(2); R_, G_, B_ = a[..., 0], a[..., 1], a[..., 2]
    if plano == 'B1':          # gris claro sobre negro; se excluye la piel
        m = (lum > 130) & (np.abs(R_ - B_) < 35) & ~((R_ - B_ > 30) & (R_ > 90))
        return ndi.binary_opening(m, iterations=1)
    if plano in ('B2', 'B3') or (plano == 'B5' and R.B5_MODO.startswith('compuesto')):  # letras oscuras en remera blanca + celeste
        lab, k = ndi.label(lum < 95); sl = ndi.find_objects(lab); ok = []
        for i, s in enumerate(sl):
            hh = s[0].stop - s[0].start; ww = s[1].stop - s[1].start
            if 6 <= hh <= 120 and ww <= 120 and rodeado(lab, i, s, lum, lo=150):
                ok.append(i + 1)
        m = np.isin(lab, ok)
        cel = (B_ - R_ > 30) & (lum > 110) if plano in ('B3', 'B5') else ((B_ - R_ > 35) & (B_ - G_ > 12))
        return m | ndi.binary_opening(cel, iterations=1)
    # B4 / B5 (7824): remera negra = mayor componente oscura neutra; ROCCÉ tono sobre tono + Founders claro adentro
    neutro = (lum < 62) & (np.abs(R_ - G_) < 18) & (np.abs(G_ - B_) < 18)
    neutro = ndi.binary_closing(neutro, iterations=3)
    lab, k = ndi.label(neutro)
    if k == 0:
        return np.zeros(lum.shape, bool)
    big = lab == (1 + np.argmax(ndi.sum(neutro, lab, range(1, k + 1))))
    remera = ndi.binary_fill_holes(big)
    s = ndi.uniform_filter(lum, 7)
    roc = ndi.binary_opening((s > 46) & (s < 115) & remera, iterations=2)
    fo = (lum > 130) & remera
    return roc | fo


def agrupar(m, radio=14):
    """se queda con el grupo principal del estampado: componentes a ≤ radio px (media resolución) del grupo de más píxeles."""
    if m.sum() == 0:
        return m
    g = ndi.binary_dilation(m, iterations=radio)
    lab, k = ndi.label(g)
    tam = ndi.sum(m, lab, range(1, k + 1))
    return m & (lab == 1 + int(np.argmax(tam)))


def caja(m, minimo=6):
    ys = np.nonzero(m.sum(1) >= 2)[0]; xs = np.nonzero(m.sum(0) >= 2)[0]
    if len(ys) == 0 or m.sum() < minimo:
        return None
    return int(xs.min() * 2), int(ys.min() * 2), int(xs.max() * 2 + 1), int(ys.max() * 2 + 1)


def margenes():
    F = leer_master()
    textos = {}
    for d in R.TEXTOS:
        c0, c1 = round(d['t0'] * 30), round(d['t1'] * 30)
        textos[d['txt']] = (c0, c1)
    # caja de cada texto por cuadro (el pop cambia el tamaño en los 3 primeros cuadros)
    tb = {}
    for d in R.TEXTOS:
        c0, c1 = round(d['t0'] * 30), round(d['t1'] * 30)
        for c in sorted({c0, c0 + 1, c0 + 2, c0 + 3, c1 - 1}):
            tb[(d['txt'], c)] = U.medir_textos(D / 'textos.ass', [c / 30])[c / 30]
    filas = []
    deb = []
    for nombre, toma, a, b in PLANOS:
        for c in range(a, b):
            m = estampado(nombre, F[c])
            for d in R.TEXTOS:                     # fuera los textos quemados (con 8 px de borde)
                c0, c1 = round(d['t0'] * 30), round(d['t1'] * 30)
                if c0 <= c < c1:
                    t = tb.get((d['txt'], c)) or tb[(d['txt'], c1 - 1)]
                    m[max(0, t[1] // 2 - 4):t[3] // 2 + 5, max(0, t[0] // 2 - 4):t[2] // 2 + 5] = False
            m = agrupar(m); bx = caja(m)
            fila = dict(cuadro=c, plano=nombre, estampado=bx)
            if bx:
                fila['margen_izq'] = bx[0]; fila['margen_der'] = 1079 - bx[2]; fila['margen_sup'] = bx[1]; fila['margen_inf'] = 1919 - bx[3]
            for d in R.TEXTOS:
                c0, c1 = round(d['t0'] * 30), round(d['t1'] * 30)
                if c0 <= c < c1 and bx:
                    t = tb.get((d['txt'], c)) or tb[(d['txt'], c1 - 1)]
                    solapa_x = not (t[2] < bx[0] or t[0] > bx[2])
                    fila.setdefault('textos', []).append(dict(texto=d['txt'], caja=t, distancia_al_estampado_px=(bx[1] - t[3]) if solapa_x else None))
            filas.append(fila)
            if c in sorted({0, 45, 260, 299} | {x for k in R.CORTES for x in (k - 1, k)}):
                im = F[c].copy(); im[m] = [255, 0, 255]
                deb.append(im)
    from PIL import Image
    Image.fromarray(np.hstack(deb)).resize((len(deb) * 180, 320)).save(Q / 'deteccion_estampado.jpg', quality=88)
    json.dump(filas, open(Q / 'margenes_por_cuadro.json', 'w'), indent=0, ensure_ascii=False)
    # resumen por plano
    res = {}
    for nombre, toma, a, b in PLANOS:
        fs = [f for f in filas if f['plano'] == nombre and f['estampado']]
        r = dict(cuadros=b - a, con_estampado=len(fs))
        for k in ('margen_izq', 'margen_der', 'margen_sup', 'margen_inf'):
            v = [f[k] for f in fs]
            r[k + '_min'] = (min(v), fs[int(np.argmin(v))]['cuadro']) if v else None
        dist = [(t['distancia_al_estampado_px'], f['cuadro'], t['texto']) for f in fs for t in f.get('textos', []) if t['distancia_al_estampado_px'] is not None]
        r['texto_a_estampado_min'] = min(dist) if dist else None
        res[nombre] = r
    # recuadros de R/É en B3: cuadros con la palabra completa y con ≥ 40 px
    json.dump(res, open(Q / 'margenes_resumen.json', 'w'), indent=1, ensure_ascii=False)
    return res


def roc_b3():
    """ROCCÉ en B3 con el detector de letras de 8004 (medido en la toma, convertido a píxeles del máster)."""
    import importlib.util
    from scipy import ndimage as ndi
    a3, b3 = RANGO['B3']
    Fs = U.leer_cuadros('/home/user/1/ORIGINALES/IMG_8004.mov', R.B3_FUENTE[0], R.B3_FUENTE[1], 540, 960, fps=30).astype(np.float32)
    out = []
    for n, f in enumerate(Fs[:b3 - a3]):
        lum = f.mean(2); lab, k = ndi.label(lum < 85); sl = ndi.find_objects(lab); xs = []
        for i, s in enumerate(sl):
            hh = s[0].stop - s[0].start
            if hh < 25 or hh > 130 or s[0].start < 420 or s[0].stop > 680:
                continue
            if not rodeado(lab, i, s, lum, lo=150, pad=6):
                continue
            xs.append((s[1].start, s[1].stop))
        x0 = min(x[0] for x in xs); x1 = max(x[1] for x in xs)
        # «Founders Privée» (celeste) debajo de ROCCÉ: extremos horizontales
        cel = ndi.binary_opening((f[..., 2] - f[..., 0] > 30) & (lum > 110), iterations=1); cel[:440] = False
        cc = np.nonzero(cel.sum(0) >= 2)[0]
        fx0, fx1 = (int(cc.min()), int(cc.max())) if len(cc) else (None, None)
        out.append(dict(cuadro=a3 + n, letras=len(xs), R_al_borde_px=x0 * 2, E_al_borde_px=(540 - x1) * 2,
                        toca_izq=x0 <= 1, toca_der=x1 >= 539,
                        founders_izq_px=None if fx0 is None else fx0 * 2, founders_der_px=None if fx1 is None else (539 - fx1) * 2,
                        founders_cortado=None if fx0 is None else (fx0 <= 1 or fx1 >= 538)))
    json.dump(out, open(Q / 'b3_rocce_bordes.json', 'w'), indent=0)
    completos = [o['cuadro'] for o in out if o['letras'] >= 5 and not o['toca_izq'] and not o['toca_der']]
    con40 = [o['cuadro'] for o in out if o['letras'] >= 5 and o['R_al_borde_px'] >= 40 and o['E_al_borde_px'] >= 40]
    return dict(palabra_entera=(min(completos), max(completos)) if completos else None,
                con_40px=(min(con40), max(con40)) if con40 else None, cuadros_con_40px=len(con40), cuadros=len(out),
                founders_cortado_en=[o['cuadro'] for o in out if o['founders_cortado']], primero=out[0], ultimo=out[-1])


# ---------------------------------------------------------------- color contra las fotos de producto
def color():
    from PIL import Image
    F = leer_master()
    res = {}
    # fotos de detalle (P3 → sRGB con video.foto_srgb)
    fotos = {}
    for k in ('negra_frente_detalle_estampado', 'blanca_frente_detalle_estampado'):
        png = Q / f'{k}_srgb.png'
        V.foto_srgb(V.P / f'{k}.jpg', png)
        fotos[k] = np.asarray(Image.open(png).convert('RGB')).astype(np.float32)

    def stats(px):
        m = px.reshape(-1, 3).mean(0)
        return dict(rgb=[round(float(x), 1) for x in m], B_menos_R=round(float(m[2] - m[0]), 1), G_menos_R=round(float(m[1] - m[0]), 1))

    def tela_y_estampado(img, oscura):
        lum = img.mean(2)
        if oscura:
            est = (lum > 140) & (np.abs(img[..., 0] - img[..., 2]) < 35)
            tela = (lum < 70) & (lum > 8) & (np.abs(img[..., 0] - img[..., 2]) < 40)
        else:
            est = (lum < 90)
            tela = (lum > 170) & (np.abs(img[..., 0] - img[..., 2]) < 40)
        return tela, est

    for k, oscura in (('negra_frente_detalle_estampado', True), ('blanca_frente_detalle_estampado', False)):
        t, e = tela_y_estampado(fotos[k], oscura)
        res[f'foto:{k}'] = dict(tela=stats(fotos[k][t]), estampado=stats(fotos[k][e]))
    # máster: Negra B1 c75 (sin dedos), Blanca B2 c100, Blanca B3 (c142 v01 · c127 v02), Negra B4 c195
    c3 = 142 if R.VERSION == 'v01' else 127
    for nombre, c, oscura in (('B1_negra_c75', 75, True), ('B2_blanca_c100', 100, False), (f'B3_blanca_c{c3}', c3, False),
                              ('B4_negra_c195', 195, True)):
        img = F[c].astype(np.float32)
        piel = (img[..., 0] - img[..., 2] > 30) & (img[..., 0] > 90)
        t, e = tela_y_estampado(img, oscura)
        if nombre.startswith('B3'):   # solo la remera: debajo del renglón de ROCCÉ
            zona = np.zeros(t.shape, bool); zona[560:, :] = True; t &= zona; e &= zona
        if nombre.startswith('B2'):
            zona = np.zeros(t.shape, bool); zona[250:850, 60:500] = True; t &= zona; e &= zona
        res[nombre] = dict(tela=stats(img[t & ~piel]), estampado=stats(img[e & ~piel]))
    # estrella celeste en B2 (c100) y en la foto de la Blanca
    for nombre, img in (('estrella_B2_c100', F[100].astype(np.float32)), ('estrella_foto_blanca', fotos['blanca_frente_detalle_estampado'])):
        m = (img[..., 2] - img[..., 0] > 35) & (img[..., 2] - img[..., 1] > 12)
        res[nombre] = stats(img[m]) if m.sum() > 20 else None
    json.dump(res, open(Q / 'color.json', 'w'), indent=1, ensure_ascii=False)
    return res


# ---------------------------------------------------------------- cuadros repetidos y continuidad
def repetidos():
    F = leer_master(270, 480).astype(np.float32)
    dif = np.abs(np.diff(F, axis=0)).mean((1, 2, 3))
    rep = [int(i + 1) for i, d in enumerate(dif) if d < 0.35]
    json.dump(dict(diferencia_media_por_cuadro=[round(float(x), 2) for x in dif], repetidos=rep), open(Q / 'repetidos.json', 'w'))
    return dict(repetidos=rep, saltos_mayores=[(int(i + 1), round(float(d), 1)) for i, d in enumerate(dif) if d > 25])


# ---------------------------------------------------------------- audio por tramos
def audio_tramos():
    out = {}
    for f in (MP4, MP4_SM):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(f), '-vn', '-f', 'f32le', '-ac', '2', '-ar', '48000', '-'],
                             capture_output=True, check=True).stdout
        a = np.frombuffer(raw, np.float32).reshape(-1, 2)
        filas = []
        for i in range(20):
            seg = a[i * 24000:(i + 1) * 24000]
            rms = np.sqrt((seg ** 2).mean()); pk = np.abs(seg).max()
            filas.append(dict(t=f'{i * 0.5:.1f}–{(i + 1) * 0.5:.1f}', cuadros=f'c{i * 15}–c{(i + 1) * 15 - 1}',
                              rms_dbfs=round(float(20 * np.log10(rms + 1e-12)), 1), pico_dbfs=round(float(20 * np.log10(pk + 1e-12)), 1)))
        # sonoridad de corto plazo (3 s) y momentánea por tramo con ebur128
        e = subprocess.run(['ffmpeg', '-nostats', '-i', str(f), '-vn', '-af', 'ebur128=framelog=verbose', '-f', 'null', '-'],
                           capture_output=True, text=True).stderr
        mom = []
        for l in e.splitlines():
            if 't:' in l and 'M:' in l and 'S:' in l:
                p = l.split()
                try:
                    t = float(p[p.index('t:') + 1]); M = float(p[p.index('M:') + 1]); S_ = float(p[p.index('S:') + 1])
                    mom.append((t, M, S_))
                except (ValueError, IndexError):
                    pass
        cola = a[-int(0.5 * 48000):]
        out[f.name] = dict(tramos_05s=filas, momentanea_cada_05s=[dict(t=round(t, 1), M=M, S=S_) for t, M, S_ in mom if abs((t * 10) % 5) < 1e-6],
                           ultimo_medio_segundo_rms_dbfs=round(float(20 * np.log10(np.sqrt((cola ** 2).mean()) + 1e-12)), 1))
    out['capas_pre_normalizacion'] = json.load(open(R.AU / 'sonoridad.json'))['capas_LUFS_pre_normalizacion']
    json.dump(out, open(Q / 'audio_tramos.json', 'w'), indent=1, ensure_ascii=False)
    return out


def textos_exactos():
    guion = ['Pasale el dedo.', 'Relieve.', 'Dala vuelta.', 'Letras de denim.\\NCostura a la vista.', 'Hacela tuya.', 'link en bio']
    ass = (D / 'textos.ass').read_text(encoding='utf-8')
    usados = [l.split('}', 1)[1] for l in ass.splitlines() if l.startswith('Dialogue:')]
    return dict(iguales=usados == guion, usados=usados)


def roc_b4():
    """ROCCÉ tono sobre tono en B4 (c165–c209), a resolución completa: letras = más claras que la tela vecina (contraste
    local ≥ 4 niveles, ventana 9 contra 41 px) y oscuras en absoluto, en la franja de 330 px por encima de «Founders
    Privée»; componentes de ≥ 60 px de alto (descarta la costura del hombro) que no tocan el borde (manga, mano).
    Si una letra tocara el borde quedaría fuera de la medición: por eso se revisa también la imagen de control."""
    from PIL import Image
    out = []; deb = []
    a4, b4 = RANGO['B4']
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(MP4), '-vf', f"select='between(n\\,{a4}\\,{b4 - 1})',format=rgb24",
                          '-fps_mode', 'vfr', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    Fr = np.frombuffer(raw, np.uint8).reshape(-1, 1920, 1080, 3)
    for j, c in enumerate(range(a4, b4)):
        a_ = Fr[j].astype(np.float32); lum = a_.mean(2)
        m1 = ndi.uniform_filter(lum, 9); big = ndi.uniform_filter(lum, 41)
        let = (m1 - big > 4) & (m1 < 110) & (m1 > 30)
        let &= ~ndi.binary_dilation((a_[..., 0] - a_[..., 2] > 20) & (lum > 40), iterations=12)   # sin piel (manos)
        neutro = ndi.binary_closing((lum < 62) & (np.abs(a_[..., 0] - a_[..., 1]) < 18) & (np.abs(a_[..., 1] - a_[..., 2]) < 18),
                                    iterations=3)
        lb, kb = ndi.label(neutro)
        remera = ndi.binary_fill_holes(lb == (1 + np.argmax(ndi.sum(neutro, lb, range(1, kb + 1)))))
        fo = ndi.binary_opening((lum > 130) & remera, iterations=2)     # «Founders Privée» dentro de la remera
        rows = np.nonzero(fo.sum(1) >= 6)[0]
        ytop = int(np.percentile(rows, 3)) if len(rows) else 1920
        band = np.zeros_like(let); band[max(0, ytop - 330):ytop - 5] = True
        m = ndi.binary_closing(let & band, iterations=4)
        lab, k = ndi.label(m); sl = ndi.find_objects(lab); ok = []
        for i, s_ in enumerate(sl):
            hh = s_[0].stop - s_[0].start
            if hh >= 60 and s_[1].start > 8 and s_[1].stop < 1072:     # fuera la manga / mano que tocan el borde
                ok.append(i + 1)
        m = np.isin(lab, ok)
        ys, xs = np.nonzero(m)
        bx = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(xs) else None
        out.append(dict(cuadro=c, rocce=bx, margen_izq=bx[0] if bx else None, margen_der=1079 - bx[2] if bx else None))
        if c in sorted({a4, b4 - 1} | set(range(a4, b4, 10))):
            im = Fr[j].copy(); im[m] = [255, 0, 255]
            if bx:
                im[bx[1]:bx[3], [bx[0], bx[2]]] = [0, 255, 0]; im[[bx[1], bx[3]], bx[0]:bx[2]] = [0, 255, 0]
            deb.append(im[::4, ::4])
    Image.fromarray(np.hstack(deb)).save(Q / 'b4_rocce_deteccion.jpg', quality=88)
    json.dump(out, open(Q / 'b4_rocce_bordes.json', 'w'), indent=0)
    v = [o for o in out if o['rocce']]
    mi = min(v, key=lambda o: o['margen_izq']); md = min(v, key=lambda o: o['margen_der'])
    return dict(cuadros_medidos=len(v), margen_izq_min=(mi['margen_izq'], mi['cuadro']), margen_der_min=(md['margen_der'], md['cuadro']),
                cuadros_bajo_40=[o['cuadro'] for o in v if min(o['margen_izq'], o['margen_der']) < 40])



def b5_7859():
    """B5 v02 (7859, ventana 1888×2160 en y 460): por cuadro c210–c299, márgenes de la remera y pelo (seguimiento real del
    torso en la toma, R.medidas_b5_ancha), separación CTA–pelo y borde inferior de «Founders Privée»; sobre el máster,
    caja de ROCCÉ (letras oscuras) y de «Founders Privée» (celeste). Imagen de control con las medidas dibujadas encima."""
    from PIL import Image, ImageDraw
    a5, b5 = RANGO['B5']
    _, _, med = R.medidas_b5_ancha(R.B5_Y, R.B5_VENTANA[0])
    cta = U.medir_textos(D / 'textos.ass', [8.5])[8.5]          # «Hacela tuya.» + «link en bio» juntos
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(MP4), '-vf', f"select='between(n\\,{a5}\\,{b5 - 1})',format=rgb24",
                          '-fps_mode', 'vfr', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    Fr = np.frombuffer(raw, np.uint8).reshape(-1, 1920, 1080, 3)
    filas = []; deb = []
    h_v = round(1080 * R.B5_VENTANA[1] / R.B5_VENTANA[0])
    for k, c in enumerate(range(a5, b5)):
        f = Fr[k].astype(np.float32); lum = f.mean(2)
        md = med[k]
        # solo dentro de la remera según el seguimiento (entre sus bordes, debajo del pelo): fuera quedan rocas y espuma
        xl_, xr_ = int(md['margen_remera_izq_master']), int(1080 - md['margen_remera_der_master'])
        zona = np.zeros(lum.shape, bool); zona[int(md['pelo_y_master'] or R.B5_Y) + 60:R.B5_Y + h_v, xl_:xr_] = True
        let = (lum < 80) & zona
        lab, n = ndi.label(let); sl = ndi.find_objects(lab); ok = []
        for i, s_ in enumerate(sl):
            hh = s_[0].stop - s_[0].start; ww = s_[1].stop - s_[1].start
            if 30 <= hh <= 160 and ww <= 160 and rodeado(lab, i, s_, lum, lo=150, pad=8):
                ok.append(i + 1)
        m = np.isin(lab, ok); ys, xs = np.nonzero(m)
        roc = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None
        cel = ndi.binary_opening((f[..., 2] - f[..., 0] > 30) & (lum > 110) & zona, iterations=2)
        if roc:
            cel[:roc[3]] = False; cel[roc[3] + 350:] = False
        ys2, xs2 = np.nonzero(cel)
        fo = [int(xs2.min()), int(ys2.min()), int(xs2.max()), int(ys2.max())] if len(xs2) else None
        fila = dict(cuadro=c, remera_margen_izq=md['margen_remera_izq_master'], remera_margen_der=md['margen_remera_der_master'],
                    pelo_y=md['pelo_y_master'], founders_y1_seguimiento=md['founders_y1_master'],
                    rocce_maestro=roc, founders_maestro=fo,
                    cta_a_pelo_px=None if (c < 240 or md['pelo_y_master'] is None) else round(md['pelo_y_master'] - cta[3], 1))
        filas.append(fila)
        if c in (210, 225, 239, 240, 255, 270, 285, 299):
            im = Image.fromarray(Fr[k].copy()); dr = ImageDraw.Draw(im)
            xl = md['margen_remera_izq_master']; xr = 1080 - md['margen_remera_der_master']
            dr.line([(xl, R.B5_Y), (xl, R.B5_Y + h_v)], fill=(255, 0, 255), width=3)
            dr.line([(xr, R.B5_Y), (xr, R.B5_Y + h_v)], fill=(255, 0, 255), width=3)
            if md['pelo_y_master']:
                dr.line([(200, md['pelo_y_master']), (880, md['pelo_y_master'])], fill=(0, 255, 0), width=3)
            dr.line([(0, cta[3]), (1080, cta[3])], fill=(255, 255, 0), width=2)
            dr.line([(0, 1380), (1080, 1380)], fill=(255, 0, 0), width=2)
            if roc:
                dr.rectangle(roc, outline=(0, 200, 255), width=3)
            if fo:
                dr.rectangle(fo, outline=(255, 140, 0), width=3)
            dr.text((20, 20), f'c{c}', fill=(255, 255, 0))
            deb.append(np.asarray(im)[::2, ::2])
    Image.fromarray(np.hstack(deb)).save(Q / 'b5_7859_control.jpg', quality=88)
    json.dump(filas, open(Q / 'b5_7859_por_cuadro.json', 'w'), indent=0)
    v = lambda key: [x[key] for x in filas if x[key] is not None]
    fo_y = [x['founders_maestro'][3] for x in filas if x['founders_maestro']]
    roc_l = [x['rocce_maestro'][0] for x in filas if x['rocce_maestro']]; roc_r = [1079 - x['rocce_maestro'][2] for x in filas if x['rocce_maestro']]
    return dict(cuadros=len(filas), remera_margen_izq_min=min(v('remera_margen_izq')), remera_margen_der_min=min(v('remera_margen_der')),
                cta_caja=cta, cta_a_pelo_min=min(v('cta_a_pelo_px')), cta_a_pelo_max=max(v('cta_a_pelo_px')),
                pelo_en_borde_superior_ventana=[x['cuadro'] for x in filas if x['pelo_y'] is not None and x['pelo_y'] <= R.B5_Y + 0.5],
                founders_y1_max_maestro=max(fo_y) if fo_y else None, founders_y1_max_seguimiento=max(v('founders_y1_seguimiento')),
                rocce_margen_izq_min=min(roc_l) if roc_l else None, rocce_margen_der_min=min(roc_r) if roc_r else None,
                cuadros_con_rocce=len(roc_l))


def b3_F():
    """Criterio de Roma para B3 (aclaración del 17/11): «ROCCÉ» entero con ≥ 40 px a los dos lados y la «F» de «Founders»
    adentro («Privée» puede salir por la derecha). A resolución completa sobre el máster: borde izquierdo del remate
    superior de la F (franja de 90 px desde el borde superior del celeste) y filas donde el celeste toca el borde izquierdo
    (cola de la F y subrayado)."""
    a3, b3 = RANGO['B3']
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(MP4), '-vf', f"select='between(n\\,{a3}\\,{b3 - 1})',crop=600:1000:0:900,format=rgb24",
                          '-fps_mode', 'vfr', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    F = np.frombuffer(raw, np.uint8).reshape(-1, 1000, 600, 3).astype(np.float32)
    roc = {o['cuadro']: o for o in json.load(open(Q / 'b3_rocce_bordes.json'))}
    out = []
    for k, f in enumerate(F):
        lum = f.mean(2); cel = ndi.binary_opening((f[..., 2] - f[..., 0] > 30) & (lum > 110), iterations=2)
        rows = np.nonzero(cel.sum(1) >= 3)[0]; ytop = int(rows.min())
        cols = np.nonzero(cel[ytop:ytop + 90, :450].sum(0) >= 1)[0]
        borde = np.nonzero(cel[:, :3].any(1))[0]
        c = a3 + k; r = roc[c]
        out.append(dict(cuadro=c, R_px=r['R_al_borde_px'], E_px=r['E_al_borde_px'], remate_F_px=int(cols.min()),
                        celeste_toca_borde_izq_filas=None if not len(borde) else [900 + int(borde.min()), 900 + int(borde.max())],
                        rocce_40=r['R_al_borde_px'] >= 40 and r['E_al_borde_px'] >= 40,
                        founders_entero_izq=not len(borde)))
    json.dump(out, open(Q / 'b3_criterio_roma.json', 'w'), indent=0)
    return dict(rocce_40=[o['cuadro'] for o in out if o['rocce_40']], remate_F_40=[o['cuadro'] for o in out if o['remate_F_px'] >= 40],
                founders_sin_tocar_borde_izq=[o['cuadro'] for o in out if o['founders_entero_izq']],
                todo_el_criterio=[o['cuadro'] for o in out if o['rocce_40'] and o['remate_F_px'] >= 40])


def b5_color():
    """Tela blanca de B5 (7859) debajo de «Founders Privée», en c225, c260 y c290."""
    b = {x['cuadro']: x for x in json.load(open(Q / 'b5_7859_por_cuadro.json'))}
    res = {}
    for c in (225, 260, 290):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(MP4), '-vf', f"select='eq(n\\,{c})',format=rgb24", '-frames:v', '1',
                              '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
        f = np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3).astype(float)
        r = b[c]['rocce_maestro']; fo = b[c]['founders_maestro']
        reg = f[fo[3] + 30:fo[3] + 200, r[0]:r[2]].reshape(-1, 3); lum = reg.mean(1)
        m = reg[(lum > 150) & (np.abs(reg[:, 0] - reg[:, 2]) < 40)].mean(0)
        res[f'B5_blanca_c{c}'] = dict(rgb=[round(float(x), 1) for x in m], B_menos_R=round(float(m[2] - m[0]), 1))
    json.dump(res, open(Q / 'b5_color.json', 'w'), indent=1)
    return res

if __name__ == '__main__':
    pasos = sys.argv[1:] or (['tecnico', 'cuadros', 'margenes', 'roc_b3', 'roc_b4', 'color', 'repetidos', 'audio_tramos', 'textos_exactos']
                             + (['b3_F', 'b5_7859', 'b5_color'] if R.B5_MODO == 'compuesto_7859_ancho' else []))
    res = {}
    for p in pasos:
        res[p] = globals()[p]()
        print('==', p); print(json.dumps(res[p], ensure_ascii=False, indent=1, default=str)[:4000])
    json.dump(res, open(Q / f'qc_{"_".join(pasos) if len(pasos) < 3 else "todo"}.json', 'w'), indent=1, ensure_ascii=False, default=str)
