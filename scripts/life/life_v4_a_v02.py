#!/usr/bin/env python3
"""Roccé Life · V4 «¿Vuelve?» versión A · máster A v02 (Pedro, 25/11/2026).

Corrección dirigida de Roma sobre A v01 (aprobada salvo dos cambios; nada más se toca):
  1. reenganche (paso 13, c384–c422): «¿Y vos, qué prometés?» → «¿Y la tuya,» / «cuál es?». Misma caja (chip), posición
     (y 300), tiempos (c384–c422; renglón 1 completo en c387 y última palabra en c393, como B), pop y sonido (acento en
     c393, la sacudida de B). Hace eco de «la única victoria que nadie puede quitarte». Placa, firma y audio desde c384
     siguen iguales a B.
  2. la sílaba «te» de «quitarte»: el fondo (mar y colchón: pistas amb y mus) baja 6 dB más solo entre 11,50 y 11,90 s,
     con fundidos de 30 ms dentro del tramo. La voz no se toca.

Importa life_v4_a (que importa life_v4_v02 y life_v4) sin modificarlos. La base de imagen es la de A v01
(TRABAJO/life2/v4a/v4_base.mp4) sin rehacerla; textos c0–c383 copiados de A v01. Intermedios en TRABAJO/life2/v4a/v02/.
Etapas (nice -n 10): textos → resto (audio, master, control, entregar en un mismo proceso).
Sin servicios externos ni créditos; nada se publica.
"""
import copy, hashlib, json, math, shutil, subprocess, sys, time
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/life')
import life_v4_a as A        # noqa: E402

M, B2, U, V, L2 = A.M, A.B2, A.U, A.V, A.L2
R, TA, TB, PIEZA = A.R, A.TA, A.TB, A.PIEZA
W, H, FPS = A.W, A.H, A.FPS
TA2 = TA / 'v02'
TX1, AU1, MAS1 = TA / 'textos', TA / 'audio', TA / 'master'
NOMBRES_A1 = {'completa': 'ROCCE_LIFE_V4_VUELVE_A_v01.mp4', 'sinmusica': 'ROCCE_LIFE_V4_VUELVE_A_SINMUSICA_v01.mp4'}

# M.T sigue en TA (base graduada de A v01); el resto de los intermedios, propios de v02
M.A, M.MAS, M.TX, M.MED = TA2 / 'audio', TA2 / 'master', TA2 / 'textos', TA2 / 'med'
M.EVID = TA2 / 'evidencia_A_v02'
M.NOMBRES = {'completa': 'ROCCE_LIFE_V4_VUELVE_A_v02.mp4', 'sinmusica': 'ROCCE_LIFE_V4_VUELVE_A_SINMUSICA_v02.mp4'}

# =====================================================================================================================
# 1 · reenganche
# =====================================================================================================================
REENG_N = (384, 422)
REENG_LINEAS = [['¿Y', 'la', 'tuya,'], ['cuál', 'es?']]
REENG_APARECE = [384, 385, 387, 390, 393]     # B: ¿Y 384 · vos, 387 · qué 390 · prometés? 393 (renglón 1 en c387, pop en c393)
REENG_GOLPE = 393
TEXTO_V02 = '¿Y la tuya, cuál es?'

_FR_A1 = copy.deepcopy(M.FRASES)


def frases_v02():
    fr = copy.deepcopy(M.FRASES)
    f = [x for x in fr if x['id'] == 'reeng'][0]
    antes = [a for _, a, *_ in M.palabras(f)]
    assert tuple(f['n']) == REENG_N and antes == [384, 387, 390, 393] and M.golpe_de(f) == REENG_GOLPE, (f['n'], antes)
    f.update(lineas=REENG_LINEAS, aparece=REENG_APARECE, golpe_n=REENG_GOLPE, guion=TEXTO_V02)
    return fr


M.FRASES = frases_v02()
_r = [x for x in M.FRASES if x['id'] == 'reeng'][0]
assert [a for _, a, *_ in M.palabras(_r)] == REENG_APARECE and M.golpe_de(_r) == REENG_GOLPE


def _eventos_con(fr):
    keep = M.FRASES
    M.FRASES = fr
    try:
        return M.eventos_texto()
    finally:
        M.FRASES = keep


assert _eventos_con(_FR_A1) == M.eventos_texto(), 'los golpes y toques tienen que ser los mismos de A v01 (y de B desde c384)'


def jdump(o, f):
    M.jdump(o, f)


def md5f(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def etapa_textos():
    """renderiza c378–c422 con la receta de B/A (mismo HTML, CSS, JS y renderizador); c378–c383 sirven de control de que el
    render es el mismo que en A v01; la capa final = A v01 en c0–c383 + reenganche nuevo en c384–c422."""
    M.TX.mkdir(parents=True, exist_ok=True)
    sp = M.spec_texto()
    css = M.CSS_TEXTO % dict(F=L2.FUENTES, CEL=M.CELESTE, LHC=A.LH_CITA)
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body><div id="raiz"></div>'
            f'<script>{M.JS_TEXTO.replace("__SPEC__", json.dumps(sp, ensure_ascii=False))}</script></body></html>')
    (M.TX / 'texto_v4a_v02.html').write_text(html, encoding='utf-8')
    jdump(sp, M.TX / 'spec_texto.json')
    ren = M.TX / 'render'
    if ren.exists():
        shutil.rmtree(ren)
    trabajo = dict(html=str(M.TX / 'texto_v4a_v02.html'), outdir=str(ren), n0=378, n1=M.TEXTO_ULTIMO, w=W, h=H,
                   dump=str(M.TX / 'visible_378_422.json'))
    (M.TX / '_trabajo.json').write_text(json.dumps(trabajo, indent=1))
    subprocess.run(A.nice(['node', str(R / 'scripts/life/life_v4_render.js'), str(M.TX / '_trabajo.json')]), check=True)
    control = {n: md5f(ren / f'f_{n:04d}.png') == md5f(TX1 / 'cuadros' / f'f_{n:04d}.png') for n in range(378, 384)}
    sec = M.TX / 'cuadros'
    if sec.exists():
        shutil.rmtree(sec)
    sec.mkdir()
    for n in range(0, 384):
        shutil.copyfile(TX1 / 'cuadros' / f'f_{n:04d}.png', sec / f'f_{n:04d}.png')
    for n in range(384, M.TEXTO_ULTIMO + 1):
        shutil.copyfile(ren / f'f_{n:04d}.png', sec / f'f_{n:04d}.png')
    vis = json.load(open(M.TX / 'visible_378_422.json'))['cuadros']
    reeng = {n: [x for x in vis[str(n)] if x['id'] == 'reeng'] for n in range(384, M.TEXTO_ULTIMO + 1)}
    jdump(dict(render_c378_c383_igual_a_A_v01=control, reenganche_visible=reeng), M.TX / 'control_textos.json')
    print('control c378–c383 igual a A v01:', control)
    print('c384', reeng[384]); print('c393', reeng[393]); print('c422', reeng[422])
    assert all(control.values())


# =====================================================================================================================
# 2 · fondo −6 dB entre 11,50 y 11,90 s (mar y colchón), voz intacta
# =====================================================================================================================
DIP_T0, DIP_T1, DIP_DB, DIP_FUNDIDO = 11.50, 11.90, 6.0, 0.030
_mezcla_a1 = A.mezcla_a


def curva_dip(n, sr):
    g = np.ones(n)
    i0, i1, nf = int(round(DIP_T0 * sr)), int(round(DIP_T1 * sr)), int(round(DIP_FUNDIDO * sr))
    lo = 10 ** (-DIP_DB / 20)
    g[i0:i1] = lo
    g[i0:i0 + nf] = np.linspace(1.0, lo, nf)
    g[i1 - nf:i1] = np.linspace(lo, 1.0, nf)
    return g


def mezcla_v02(con_musica, k):
    m, voz, e = _mezcla_a1(con_musica, k)
    g = curva_dip(m.N, M.SR)
    for p in ('amb', 'mus'):
        m.pistas[p] *= g[:, None]
    m.log(DIP_T0, f'fondo (mar y colchón) −{DIP_DB:.0f} dB entre {DIP_T0} y {DIP_T1} s, fundidos de {DIP_FUNDIDO * 1000:.0f} ms '
                  'dentro del tramo (la «te» de «quitarte»); la voz no se toca')
    return m, voz, e


A.mezcla_a = mezcla_v02


def fondo_en_tramo():
    """nivel del fondo (amb + mus, promedio de canales) en v01 y v02, por tramo y cada 20 ms; voz v01 = v02."""
    import soundfile as sf
    out = {}
    for k in ('completa', 'sinmusica'):
        st = {}
        for ver, d in (('v01', AU1), ('v02', M.A)):
            fx = {}
            for p in ('amb', 'mus', 'voz', 'fx'):
                f = d / f'v4_{k}_{p}.wav'
                fx[p] = sf.read(str(f))[0].mean(1) if f.exists() else None
            st[ver] = fx
        sr = M.SR

        def rms(x, a, b):
            seg = x[int(round(a * sr)):int(round(b * sr))]
            return round(20 * math.log10(np.sqrt((seg ** 2).mean()) + 1e-12), 2)

        def fondo(v):
            f = st[v]['amb'].copy()
            if st[v]['mus'] is not None:
                f = f + st[v]['mus']
            return f
        f1, f2 = fondo('v01'), fondo('v02')
        fila = dict(
            tramo_11_50_11_90=dict(v01_db=rms(f1, 11.50, 11.90), v02_db=rms(f2, 11.50, 11.90)),
            meseta_11_53_11_87=dict(v01_db=rms(f1, 11.53, 11.87), v02_db=rms(f2, 11.53, 11.87)),
            silaba_te_11_62_11_72=dict(v01_db=rms(f1, 11.62, 11.72), v02_db=rms(f2, 11.62, 11.72),
                                       voz_db=rms(st['v02']['voz'], 11.62, 11.72)),
            fondo_igual_fuera_del_tramo=bool(np.array_equal(f1[:int(round(DIP_T0 * sr))], f2[:int(round(DIP_T0 * sr))])
                                             and np.array_equal(f1[int(round(DIP_T1 * sr)):], f2[int(round(DIP_T1 * sr)):])),
            voz_v01_igual_v02=bool(np.array_equal(st['v01']['voz'], st['v02']['voz'])),
            fx_v01_igual_v02=bool(np.array_equal(st['v01']['fx'], st['v02']['fx'])),
            cada_20ms=[dict(t=round(t, 2), v01_db=rms(f1, t, t + 0.02), v02_db=rms(f2, t, t + 0.02))
                       for t in np.arange(11.44, 11.96, 0.02)])
        for kk in ('tramo_11_50_11_90', 'meseta_11_53_11_87', 'silaba_te_11_62_11_72'):
            fila[kk]['dif_db'] = round(fila[kk]['v02_db'] - fila[kk]['v01_db'], 2)
        out[k] = fila
    return out


def audio_vs(ref_dir, nombre_ref, tramos_iguales):
    """WAV previo y final de v02 contra una referencia, en los tramos que deben ser idénticos."""
    import soundfile as sf
    out = {}
    for k in ('completa', 'sinmusica'):
        fila = {}
        for etapa, suf in (('previa', '_pre'), ('final', '')):
            x2, sr = sf.read(str(M.A / f'v4_{k}{suf}.wav'))
            x1, _ = sf.read(str(ref_dir / nombre_ref(k, suf)))
            for a, b in tramos_iguales:
                i, j = int(round(a * sr)), (int(round(b * sr)) if b else min(len(x1), len(x2)))
                d = np.abs(x2[i:j] - x1[i:j])
                fila[f'{etapa}_{a}-{b or "fin"}s'] = dict(identico_bit_a_bit=bool(d.max() == 0), dif_max=float(d.max()))
        out[k] = fila
    return out


def psnr_vs_v01():
    """máster v02 contra v01 decodificados, cuadro a cuadro (luma), separando el tramo cambiado (c384–c422)."""
    ys = W * H
    filas = []
    for n, (a, b) in enumerate(zip(A.frames_yuv(M.MAS / M.NOMBRES['completa']), A.frames_yuv(MAS1 / NOMBRES_A1['completa']))):
        ya = np.frombuffer(a[:ys], np.uint8).astype(np.float32); yb = np.frombuffer(b[:ys], np.uint8).astype(np.float32)
        mse = float(((ya - yb) ** 2).mean())
        filas.append(dict(cuadro=n, psnr_db=round(99.0 if mse == 0 else 10 * math.log10(255 ** 2 / mse), 2)))
    fuera = [f['psnr_db'] for f in filas if not (REENG_N[0] <= f['cuadro'] <= REENG_N[1])]
    dentro = [f['psnr_db'] for f in filas if REENG_N[0] <= f['cuadro'] <= REENG_N[1]]
    return dict(fuera_c384_c422=dict(cuadros=len(fuera), psnr_min=min(fuera), psnr_mediana=float(np.median(fuera)),
                                     iguales_99=sum(p == 99.0 for p in fuera)),
                dentro_c384_c422=dict(cuadros=len(dentro), psnr_min=min(dentro), psnr_mediana=float(np.median(dentro))),
                por_cuadro=filas)


def textos_vs_v01():
    dif = [n for n in range(0, M.TEXTO_ULTIMO + 1)
           if md5f(M.TX / 'cuadros' / f'f_{n:04d}.png') != md5f(TX1 / 'cuadros' / f'f_{n:04d}.png')]
    return dict(cuadros_distintos=[dif[0], dif[-1]] if dif else [], n_distintos=len(dif),
                solo_c384_c422=(dif == list(range(REENG_N[0], REENG_N[1] + 1))))


def hoja_reenganche(carpeta):
    """v01 arriba, v02 abajo, en los cuadros de aparición de cada palabra, el pop y el final del paso 13."""
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(M.FONT, 20)
    ns = [383, 384, 385, 386, 387, 390, 393, 394, 396, 400, 410, 422, 423]
    S = Image.new('RGB', (len(ns) * 272, 2 * 482), (30, 30, 30))
    for r, mp4 in enumerate((MAS1 / NOMBRES_A1['completa'], M.MAS / M.NOMBRES['completa'])):
        for i, n in enumerate(ns):
            im = Image.fromarray(U.leer(mp4, 270, 480, n0=n, n1=n)[0]); d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 120, 26], fill=(0, 0, 0)); d.text((4, 2), f'{"v01" if r == 0 else "v02"} c{n}', font=fnt, fill=(255, 255, 0))
            S.paste(im, (i * 272, r * 482))
    S.save(carpeta / 'reenganche_v01_v02.jpg', quality=88)
    # cuadro completo del pop (c393) y del texto quieto (c405) de v02
    for n in (393, 405):
        Image.fromarray(U.leer(M.MAS / M.NOMBRES['completa'], 540, 960, n0=n, n1=n)[0]).save(carpeta / f'v02_c{n}.jpg', quality=90)


def etapa_resto():
    # audio (primero, con el generador desde cero, mismo orden que A v01 y B v02)
    A.etapa_audio()
    # máster (una sola vez)
    M.etapa_master()
    # control
    ev = M.EVID; ev.mkdir(parents=True, exist_ok=True)
    rep = {}
    for k in ('completa', 'sinmusica'):
        f = M.MAS / M.NOMBRES[k]
        pj, t = B2.tecnico(f, A.tramos_a())
        rep[k] = t
        json.dump(pj, open(ev / f'ffprobe_{k}.json', 'w'), indent=1)
        print(k, t['md5_flujo_video'], t['md5_flujo_audio'], t['sonoridad'], t['decodifica_completo'], t['cuadros_decodificados'], flush=True)
    rep['fondo_11_5_11_9'] = fondo_en_tramo()
    rep['audio_vs_A_v01'] = audio_vs(AU1, lambda k, s: f'v4_{k}{s}.wav', [(0.0, DIP_T0), (DIP_T1, None)])
    rep['audio_vs_B_desde_c384'] = audio_vs(TB / 'audio', lambda k, s: f'v4_{k}{s}.wav', [(12.80, None)])
    rep['psnr_vs_A_v01'] = psnr_vs_v01()
    rep['textos_vs_A_v01'] = textos_vs_v01()
    rep['base'] = dict(archivo=str(M.T / 'v4_base.mp4'), nota='la misma base sin pérdida de A v01 (no se rehízo)',
                       md5_archivo=md5f(M.T / 'v4_base.mp4'))
    rep['placa'] = dict(archivos=[str(M.PL / 'cierre_frase.png'), str(M.PL / 'cierre_firma.png')], cuadros=M.PLACA_CUADROS)
    rep['golpes_texto'] = [dict(cuadro=n, tipo=t_, frase=i) for n, t_, i in M.eventos_texto()[0]]
    hoja_reenganche(ev)
    jdump(rep, ev / 'control_A_v02.json')
    for kk in ('fondo_11_5_11_9', 'audio_vs_A_v01', 'audio_vs_B_desde_c384', 'textos_vs_A_v01'):
        r_ = rep[kk]
        if kk == 'fondo_11_5_11_9':
            r_ = {k: {x: y for x, y in v.items() if x != 'cada_20ms'} for k, v in r_.items()}
        print(kk, r_, flush=True)
    print('psnr', {k: v for k, v in rep['psnr_vs_A_v01'].items() if k != 'por_cuadro'}, flush=True)
    # entrega: sin sobrescribir; relectura a los 10 s
    out = {}
    for k in ('completa', 'sinmusica'):
        src, dst = M.MAS / M.NOMBRES[k], PIEZA / M.NOMBRES[k]
        assert not dst.exists(), f'ya existe {dst}'
        shutil.copyfile(src, dst)
        out[k] = dict(destino=str(dst))
    time.sleep(10)
    for k in ('completa', 'sinmusica'):
        dst = PIEZA / M.NOMBRES[k]
        mv, ma = U.md5_stream(dst, 'v'), U.md5_stream(dst, 'a')
        out[k].update(bytes=dst.stat().st_size, md5_flujo_video=mv, md5_flujo_audio=ma, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
                      flujos_iguales_al_master=(mv == rep[k]['md5_flujo_video'] and ma == rep[k]['md5_flujo_audio']))
        print(k, out[k], flush=True)
    jdump(out, ev / 'entrega_A_v02.json')
    evd = PIEZA / 'evidencia_A_v02'
    evd.mkdir(exist_ok=True)
    for f in sorted(ev.iterdir()):
        if f.is_file() and not (evd / f.name).exists():
            shutil.copyfile(f, evd / f.name)
    for f in (M.A / 'audio.json', M.TX / 'control_textos.json', M.TX / 'spec_texto.json'):
        if not (evd / f.name).exists():
            shutil.copyfile(f, evd / f.name)


if __name__ == '__main__':
    globals()['etapa_' + sys.argv[1]]()
