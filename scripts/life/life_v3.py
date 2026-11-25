#!/usr/bin/env python3
"""Roccé Life · V3 «5 domingos» · receta de los másteres v01 y v02 (Pedro, 25/11/2026).

v02 (dictamen de Roma TANDA2/V3_5_domingos/04_roma_dictamen_master_v01.md): solo cambian dos planos. Paso 10 (CTA,
10,70–13,10) = 4627 8,933–11,333 (c268–c339) con la placa en tres capas (degradé reforzado, frase, firma) y control de
contraste ≥ 3:1 en ≥ 95 % del trazo por cuadro; paso 2 (1,80–2,70) = 4627 c363–c389 (12,10–13,00, fuera de 8,93–11,33,
remera entera con ≥ 53 px de margen), en gris como en v01. Los otros ocho planos son los intermedios de v01 (mismos
archivos). Se elige con la variable de entorno V3_VERSION=v02 (sin ella, la receta es la de v01 tal cual); los
intermedios de v02 van a TRABAJO/life2/v3/v02/ y la evidencia a evidencia_v02/.

Guion: piezas/LIFE_rocce_life/TANDA2/V3_5_domingos/01_fede_guion_G1_v1.md (G1 v1) + condiciones de Roma en
TANDA2/07_roma_aprobacion_guiones_t2.md (mandan sobre el guion).

Reutiliza sin modificarlos: scripts/fmt/video.py (color/HDR→SDR, plano, unir, ass, foto_srgb), fmt03.py (plano_n, leer,
hoja_src, md5_stream, ebur, audio_np, niveles_tramos, control), fmt03_v02.py (momentanea), sonido.py (Mezcla) y las
funciones de scripts/life/life_v2.py (neutralización de la Blanca, master_v2 con el overlay corregido, medición de
textos, limitar_tp, átomos, hojas). life_v2 se importa como módulo: al importarlo envuelve video.sh con nice y 2 hilos
(máquina compartida con los Pedros de V4 y V5). La placa usa el CSS de scripts/life/pines.py como V1 (render con
scripts/life/life_v1_render.js, fondo transparente).
Prueba de lugar de la foto (condición 2): scripts/life/life_v3_lugar.py (OpenCV, entorno TRABAJO/life2/v3/cvenv).

Etapas (python de TRABAJO/venv, con nice -n 10):
  hojas → planos → color → textos → placa → audio → master → control → entregar
  (numeros: rehace solo la comparación de los cinco números y la guarda en evidencia_v01/control.json)
Intermedios en TRABAJO/life2/v3/. Nada se publica; sin servicios externos ni créditos.
"""
import json, math, os, subprocess, sys, hashlib, shutil, time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/home/user/1/scripts/fmt')
sys.path.insert(0, '/home/user/1/scripts/life')
import video as V          # noqa: E402
import fmt03 as U          # noqa: E402
import life_v2 as L2       # noqa: E402  (envuelve V.sh: ffmpeg con nice y 2 hilos)

VERSION = os.environ.get('V3_VERSION', 'v01')
assert VERSION in ('v01', 'v02'), VERSION
V02 = VERSION == 'v02'
R = Path('/home/user/1')
T = R / 'TRABAJO/life2/v3'
TV = T / 'v02' if V02 else T        # intermedios de la versión (v01: los de siempre, sin mover nada)
HJ = T / 'hojas'
MED = T / 'med'                     # mediciones comunes (lugar de la foto, bordes de 4627)
MEDV = TV / 'med'                   # mediciones de la versión (color.json, márgenes, contraste)
P = TV / 'planos'
A = TV / 'audio'
MAS = TV / 'master'
PL = TV / 'placa'
TX = T / 'textos'                   # los textos no cambian en v02: mismos .ass
BASE0 = TV / 'v3_base0.mp4'
BASE = TV / 'v3_base.mp4'
EVID = T / f'evidencia_{VERSION}'
EXP = R / 'EXPORTACIONES'
PIEZA = Path('/mnt/project-files/piezas/LIFE_rocce_life/TANDA2/V3_5_domingos')
FPS, W, H = 30, 1080, 1920
NF = 393
DUR = NF / FPS                      # 13,100 s
SR = 48000
FONT = U.FONT
NUMEROS = (37, 36, 35, 34, 33)      # 25, 26, 27, 28 y 29/11 (condición 3 de Roma); revisión = 36
REVISION = 36


def nombre(n, k, version=None):
    v = version or VERSION
    return f'ROCCE_LIFE_V3_5_DOMINGOS_{n}_{v}.mp4' if k == 'completa' else f'ROCCE_LIFE_V3_5_DOMINGOS_{n}_SINMUSICA_{v}.mp4'


def nice(cmd):
    return ['nice', '-n', '10'] + list(cmd)


jdump = L2.jdump


# =====================================================================================================
# etapa hojas · cuadro a cuadro de los tramos críticos (cara de 7884 0,0–2,8 s: condición 1 de Roma)
# =====================================================================================================
def etapa_hojas():
    HJ.mkdir(parents=True, exist_ok=True)
    U.hoja_src('IMG_7884', 0, 89, HJ / '7884_c0-c89_c1.jpg', cada=1, ancho=200, cols=15)
    # cabeza: cajas (x, y, w, h) en 4K alrededor de la cabeza, que sigue a la cámara
    U.hoja_src('IMG_7884', 0, 29, HJ / '7884_cabeza_c0-c29_c1.jpg', cada=1, ancho=300, cols=10, caja=(1000, 1200, 1100, 1100))
    U.hoja_src('IMG_7884', 30, 59, HJ / '7884_cabeza_c30-c59_c1.jpg', cada=1, ancho=300, cols=10, caja=(1160, 900, 1000, 1200))
    U.hoja_src('IMG_7884', 60, 89, HJ / '7884_cabeza_c60-c89_c1.jpg', cada=1, ancho=300, cols=10, caja=(1160, 700, 1000, 1200))
    U.hoja_src('IMG_7884', 84, 156, HJ / '7884_c84-c156_c3.jpg', cada=3, ancho=240, cols=13)
    U.hoja_src('IMG_7885', 0, 59, HJ / '7885_c0-c59_c1.jpg', cada=1, ancho=200, cols=15)
    U.hoja_src('IMG_7885', 0, 59, HJ / '7885_cabeza_c0-c59_c1.jpg', cada=1, ancho=220, cols=12, caja=(1050, 1050, 800, 800))
    U.hoja_src('IMG_4627', 180, 207, HJ / '4627_c180-c207_c1.jpg', cada=1, ancho=200, cols=14)
    U.hoja_src('IMG_4627', 0, 72, HJ / '4627_c0-c72_c3.jpg', cada=3, ancho=200, cols=13)
    U.hoja_src('IMG_7896', 0, 81, HJ / '7896_c0-c81_c3.jpg', cada=3, ancho=200, cols=14)
    # detalle a tamaño real del costado de la cara (donde estarían ojo y nariz) en 8 cuadros
    from PIL import Image, ImageDraw
    src = V._src('IMG_7884'); tiles = []
    for n, (x0, y0, x1, y1) in [(0, (1000, 1250, 1700, 1950)), (13, (1000, 1250, 1700, 1950)), (26, (1000, 1250, 1700, 1950)),
                                (33, (1100, 1100, 1900, 1900)), (40, (1300, 1100, 2100, 1900)), (45, (1400, 1000, 2160, 1760)),
                                (60, (1500, 800, 2160, 1500)), (66, (1500, 800, 2160, 1500))]:
        f = U.leer(src, 2160, 3840, n0=n, n1=n, vf_pre=V.color('IMG_7884'))[0]
        im = Image.fromarray(f[y0:y1, x0:x1]).resize((500, round(500 * (y1 - y0) / (x1 - x0))))
        d = ImageDraw.Draw(im); d.rectangle([0, 0, 60, 24], fill=(0, 0, 0)); d.text((4, 4), f'c{n}', fill=(255, 255, 0))
        tiles.append(im)
    hh = max(t.height for t in tiles)
    Wd = Image.new('RGB', (4 * 502, 2 * hh + 4), (30, 30, 30))
    for i, t in enumerate(tiles):
        Wd.paste(t, ((i % 4) * 502, (i // 4) * (hh + 4)))
    Wd.save(HJ / '7884_cara_detalle_1a1.jpg', quality=90)


# =====================================================================================================
# etapa planos · tabla del guion (pasos 1–10). Cuadros del máster inclusive; n0 = cuadro de la fuente.
# =====================================================================================================
FULL4K = (0, 0, 2160, 3840)
FULLHD = (0, 0, 1080, 1920)
FOTO = R / 'PRODUCTO' / 'blanca_espalda_roca_ola.jpg'
# paso 8: 9:16 a alto completo de la foto 1512×2016 (x 60–1194, guion), empuje 1,00 → 1,04 lineal, centrado
FOTO_CAJA = (60, 0, 1134, 2016)
FOTO_Z = (1.00, 1.04)
# barrido (paso 9 → 10): desenfoque de movimiento SOLO horizontal (avgblur con sizeY=1; sin sizeY, avgblur usa el mismo
# tamaño en vertical y queda un desenfoque de foco, no un barrido: primer render del 25/11, no entregado) en los 3 últimos
# cuadros de 7885 y los 3 primeros de 4627, creciendo hacia el corte
BARRIDO_SALIDA = ("avgblur=sizeX=16:sizeY=1:enable='eq(n\\,39)',avgblur=sizeX=48:sizeY=1:enable='eq(n\\,40)',"
                  "avgblur=sizeX=110:sizeY=1:enable='eq(n\\,41)'")
BARRIDO_ENTRADA = ("avgblur=sizeX=110:sizeY=1:enable='eq(n\\,0)',avgblur=sizeX=48:sizeY=1:enable='eq(n\\,1)',"
                   "avgblur=sizeX=16:sizeY=1:enable='eq(n\\,2)'")
PLANOS = [
    # id, m0 (cuadro del máster), toma, n0 (cuadro de la fuente), nf, caja, post, función
    dict(id='01', m0=0, toma='IMG_7885', n0=0, nf=54, caja=FULL4K, f='APUESTA + GRAN PREGUNTA + PISTA 1'),
    dict(id='02', m0=54, toma='IMG_4627', n0=180, nf=27, caja=FULLHD, f='E− 1'),
    dict(id='03', m0=81, toma='IMG_7896', n0=0, nf=27, caja=FULL4K, f='E− 2'),
    dict(id='04', m0=108, toma='IMG_7896', n0=48, nf=33, caja=FULL4K, f='E+ 1'),
    dict(id='05', m0=141, toma='IMG_7884', n0=0, nf=27, caja=FULL4K, f='E+ 2 + PISTA 2'),
    dict(id='06', m0=168, toma='IMG_7884', n0=60, nf=24, caja=FULL4K, f='SUBE'),
    dict(id='07', m0=192, toma='IMG_7884', n0=84, nf=48, caja=FULL4K, f='GIRO'),
    dict(id='08', m0=240, toma='foto', n0=None, nf=39, caja=FOTO_CAJA, f='RESOLUCIÓN + plano de ropa'),
    dict(id='09', m0=279, toma='IMG_7885', n0=0, nf=42, caja=FULL4K, post=BARRIDO_SALIDA, f='REENGANCHE'),
    dict(id='10', m0=321, toma='IMG_4627', n0=0, nf=72, caja=FULLHD, post=BARRIDO_ENTRADA, f='CTA'),
]
if V02:
    # dictamen de Roma sobre v01: paso 10 = 4627 8,93–11,33 (c268–c339, 72 cuadros, mismo barrido de entrada); paso 2 =
    # otro tramo de 4627 fuera de 8,93–11,33 con la remera entera: c363–c389 (12,10–13,00 s), el de mayor margen mínimo
    # de los tramos de 27 cuadros (53 px a la izquierda; med/4627_margenes_completo.json). En gris, como en v01.
    PLANOS[1] = dict(PLANOS[1], n0=363)
    PLANOS[9] = dict(PLANOS[9], n0=268)
CAMBIADOS = ('02', '10') if V02 else ()
CORTES = [p['m0'] for p in PLANOS[1:]]          # 54 81 108 141 168 192 240 279 321
GRIS_HASTA = 191                                 # c0–c191 sin color (0,000–6,400 s)
RAMPA = {192: 0.2, 193: 0.4, 194: 0.6, 195: 0.8}  # el color vuelve en 4 cuadros; pleno desde c196 (6,533 s)
FLASH = {240: 0.90, 241: 0.45}                   # flash blanco de 2 cuadros sobre la foto (mezcla hacia blanco)


def plano_foto(path, nf, caja, z0, z1, salida):
    """foto de PRODUCTO/ (Display P3 → sRGB con video.foto_srgb) como plano de nf cuadros con empuje lineal z0 → z1
    centrado en la caja (x, y, w, h). Recorte subpíxel por cuadro con Lanczos (PIL) y codificación RGB → YUV con la
    matriz BT.709 explícita (scale=out_color_matrix=bt709, rango tv), intermedio x264 crf 12 como video.py."""
    from PIL import Image
    png = Path(str(salida) + '.png')
    V.foto_srgb(path, png)
    im = Image.open(png).convert('RGB')
    x, y, w, h = caja
    cx, cy = x + w / 2, y + h / 2
    enc = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                 '-r', str(FPS), '-i', '-', '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
                                 '-threads', '2', *V.ENC_INT, str(salida)]), stdin=subprocess.PIPE)
    ventanas = []
    for k in range(nf):
        z = z0 + (z1 - z0) * k / max(nf - 1, 1)
        ww, hh = w / z, h / z
        box = (cx - ww / 2, cy - hh / 2, cx + ww / 2, cy + hh / 2)
        ventanas.append([round(z, 5)] + [round(v, 2) for v in box])
        enc.stdin.write(np.asarray(im.resize((W, H), Image.LANCZOS, box=box), np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    assert enc.returncode == 0
    return dict(foto=str(path), cuadros=nf, salida=str(salida), caja=caja, z0=z0, z1=z1, ventanas=ventanas,
                tam_foto=im.size)


def etapa_planos():
    P.mkdir(parents=True, exist_ok=True)
    reg = []
    v01 = {r['id']: r for r in json.load(open(T / 'planos.json'))['planos']} if V02 else {}
    for p in PLANOS:
        out = P / f"{p['id']}.mp4"
        if V02 and p['id'] not in CAMBIADOS:
            r = dict(v01[p['id']], reutilizado_de_v01=True)          # mismo intermedio de v01 (no se recodifica)
            r['md5_archivo'] = hashlib.md5(Path(r['salida']).read_bytes()).hexdigest()
            reg.append(r); print(p['id'], 'v01', r['cuadros'], flush=True); continue
        if p['toma'] == 'foto':
            r = plano_foto(FOTO, p['nf'], p['caja'], *FOTO_Z, out)
        else:
            r = U.plano_n(p['toma'], p['n0'], p['nf'], out, caja=p['caja'], post=p.get('post'))
        r.update(id=p['id'], m0=p['m0'], funcion=p['f'], post=p.get('post'))
        reg.append(r); print(p['id'], r['cuadros'], flush=True)
    n = V.unir(reg, BASE0)
    assert n == NF, n
    jdump(dict(cuadros=n, planos=reg), TV / 'planos.json')
    print('total', n)


# =====================================================================================================
# etapa color · código visual del guion: gris mientras la pregunta está abierta (c0–c191), el color vuelve en 4
# cuadros (c192–c195) y es pleno desde c196; flash blanco de 2 cuadros sobre la foto (c240–c241).
# Se trabaja sobre los planos Y/Cb/Cr del intermedio (yuv420p, BT.709, rango tv): gris = Cb = Cr = 128 exactos
# (saturación 0 medible), rampa = croma escalada hacia 128, flash = mezcla hacia el blanco de video (Y 235, croma 128).
# La luma de c0–c239 no se toca salvo en el flash. Sin neutralización de la Blanca: los tramos de color miden B−R dentro
# del rango de PRODUCTO (control) y la foto es de PRODUCTO (se usa tal cual, como en el pin 3).
# =====================================================================================================
def etapa_color():
    base0, base = BASE0, BASE
    ny = W * H; nc = ny // 4
    dec = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(base0), '-f', 'rawvideo',
                                 '-pix_fmt', 'yuv420p', '-']), stdout=subprocess.PIPE)
    enc = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{W}x{H}',
                                 '-r', str(FPS), '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                                 '-color_trc', 'bt709', '-i', '-', '-c:v', 'libx264', '-threads', '2', '-qp', '0',
                                 '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries',
                                 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', str(base)]), stdin=subprocess.PIPE)
    reg = {}; k = 0
    while True:
        b = dec.stdout.read(ny + 2 * nc)
        if len(b) < ny + 2 * nc:
            break
        Y, Cb, Cr = [x.copy() for x in L2.partir(b)]
        if k <= GRIS_HASTA:
            Cb[:] = 128; Cr[:] = 128; reg[k] = 'gris'
        elif k in RAMPA:
            s = RAMPA[k]
            Cb = np.clip(np.round(128 + s * (Cb.astype(np.float32) - 128)), 0, 255).astype(np.uint8)
            Cr = np.clip(np.round(128 + s * (Cr.astype(np.float32) - 128)), 0, 255).astype(np.uint8)
            reg[k] = f'croma ×{s}'
        if k in FLASH:
            a = FLASH[k]
            Y = np.clip(np.round(Y + a * (235 - Y.astype(np.float32))), 0, 255).astype(np.uint8)
            Cb = np.clip(np.round(128 + (1 - a) * (Cb.astype(np.float32) - 128)), 0, 255).astype(np.uint8)
            Cr = np.clip(np.round(128 + (1 - a) * (Cr.astype(np.float32) - 128)), 0, 255).astype(np.uint8)
            reg[k] = f'flash {a}'
        enc.stdin.write(Y.tobytes() + Cb.tobytes() + Cr.tobytes()); k += 1
    dec.stdout.close(); dec.wait(); enc.stdin.close(); enc.wait()
    assert k == NF and enc.returncode == 0, (k, enc.returncode)
    MEDV.mkdir(parents=True, exist_ok=True)
    jdump(dict(gris=f'c0–c{GRIS_HASTA}', rampa=RAMPA, flash=FLASH, por_cuadro=reg), MEDV / 'color.json')
    print('color', k, 'cuadros')


# =====================================================================================================
# textos · grafía exacta del guion (base común: hook CajaN \fs120, pasos \fs104, palabra fuerte Grande \fs124).
# Únicos agregados: saltos de renglón (\N) donde el texto no entra en una línea a ese tamaño (WrapStyle 2 no corta solo)
# y el color de «también» (celeste de la prenda: «Founders Privée» en la foto de la roca, percentil 90 = #B0CAEB).
# Un texto por vez, arriba al centro; las anclas se calibran para que la caja empiece en y 270 (zona 270–1130).
# =====================================================================================================
CELESTE = '&HEBCAB0&'          # ASS &HBBGGRR& = #B0CAEB
F_HOOK, F_PASO, F_GRANDE = r'\fs120\xbord33\ybord10', r'\fs104\xbord29\ybord9', r'\fs124'


def textos(n_dias):
    return [  # c = cuadros del máster inclusive
        dict(id='hook1', c=(0, 23), txt=f'Quedan {n_dias} días.', estilo='CajaN', extra=F_HOOK, pop=True),
        dict(id='hook2', c=(24, 53), txt='¿Arrancás o\\Nesperás a enero?', estilo='CajaN', extra=F_HOOK, pop=False),
        dict(id='em1', c=(54, 80), txt='Diciembre: fiestas.', estilo='CajaN', extra=F_PASO, pop=False),
        dict(id='em2', c=(81, 107), txt='“Arranco en enero.”', estilo='CajaN', extra=F_PASO, pop=False),
        dict(id='ep1', c=(108, 140), txt=f'Enero {{\\c{CELESTE}}}también{{\\c&HFFFFFF&}}\\Nva a tener excusas.',
             estilo='CajaN', extra=F_PASO, pop=False),
        dict(id='ep2', c=(141, 167), txt=f'{n_dias} días.\\N5 domingos.', estilo='CajaN', extra=F_PASO, pop=False),
        dict(id='sube', c=(168, 191), txt='¿Qué entra en uno?', estilo='CajaN', extra=F_PASO, pop=False),
        dict(id='giro1', c=(192, 209), txt='Un domingo.', estilo='CajaN', extra=F_PASO, pop=True),
        dict(id='giro2', c=(210, 239), txt='Un celular.', estilo='CajaN', extra=F_PASO, pop=False),
        dict(id='esto', c=(240, 278), txt='Esto.', estilo='Grande', extra=F_GRANDE, pop=True),
        dict(id='reenganche', c=(279, 320), txt='Te quedan 5.', estilo='CajaN', extra=F_PASO, pop=False),
    ]


def texto_plano(t):
    """texto tal como se lee en pantalla (sin etiquetas ASS; \\N = salto de renglón)."""
    import re
    return re.sub(r'\{[^}]*\}', '', t['txt']).replace('\\N', ' ')


Y_ZONA = (270, 1130)
Y_ESTO = 860            # «Esto.»: sobre la roca, encima de la Blanca (etapa textos: ver anclas.json)


def ass_numero(n_dias, anclas, salida):
    ev = []
    for t in textos(n_dias):
        n0, n1 = t['c']
        ev.append(dict(t0=max(0.0, (n0 - 0.5) / FPS), t1=(n1 + 0.5) / FPS, txt=t['txt'], estilo=t['estilo'], x=540,
                       y=anclas[t['id']], pop=t['pop'], extra=t['extra']))
    return V.ass(ev, salida)


def render_ass_gris(ass_path, n):
    """como life_v2.render_ass_gris, con la duración de V3 (13,1 s)."""
    r = U.run(nice(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}:d={DUR + 1}', '-vf',
                    f"subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter,select='eq(n\\,{n})',format=gray",
                    '-frames:v', '1', '-fps_mode', 'passthrough', '-f', 'rawvideo', '-']))
    return np.frombuffer(r, np.uint8).reshape(H, W)


def etapa_textos():
    """calibra las anclas (caja desde y 270 para los textos en caja; «Esto.» en Y_ESTO) y escribe un .ass por número."""
    TX.mkdir(parents=True, exist_ok=True)
    prueba = {t['id']: 400 for t in textos(REVISION)}
    a0 = ass_numero(REVISION, prueba, TX / '_calibrar.ass')
    anclas, cajas = {}, {}
    for t in textos(REVISION):
        n = t['c'][0] + 6                         # después del pop (90 ms)
        c = L2._caja(render_ass_gris(a0, n) > 8)
        anclas[t['id']] = (400 - (c[1] - Y_ZONA[0])) if t['estilo'] == 'CajaN' else Y_ESTO
    for N in NUMEROS:
        ass_numero(N, anclas, TX / f'v3_textos_{N}.ass')
    for t in textos(REVISION):
        n = t['c'][0] + 6
        cajas[t['id']] = L2._caja(render_ass_gris(TX / f'v3_textos_{REVISION}.ass', n) > 8)
    jdump(dict(anclas=anclas, cajas_36=cajas), TX / 'anclas.json')
    print(json.dumps(dict(anclas=anclas, cajas=cajas), ensure_ascii=False))


# =====================================================================================================
# etapa placa · cierre del sistema Roccé Life (V1: CSS de pines.py, Instrument Serif con la palabra en cursiva, firma
# centrada con el logo original en ficha #FEFEFE de 96 px, radio 11 %; degradé arriba rgb(12,18,26) α 0,62 → 0)
# =====================================================================================================
FRASE_HTML = 'Guardalo para el<br><em>domingo</em>.'      # «Guardalo para el *domingo*.» (cursiva solo de estilo)
FRASE_TXT = 'Guardalo para el domingo.'
FIRMA_TXT = 'ROCCÉ LIFE'
PLACA = dict(fs=92, lh='1.03', top_frase=290, logo=96, ffs=30, top_firma=520, grad=(820, 0.62, (12, 18, 26)))
OV_FRASE = (327, 392)        # entra 6 cuadros después del corte (el barrido termina en c323)
OV_FIRMA = (333, 392)
# v02 · placa en tres capas: degradé (numpy: perfil exacto y medible), frase y firma (mismo CSS y mismos textos que v01).
# El degradé entra en el corte (c321, debajo del barrido de entrada) para no aparecer de golpe con la frase sobre la
# espuma; frase y firma entran como en v01. Perfil: op_arriba en y 0 → op_meseta en y_meseta (lineal), después curva
# suave (smoothstep) hasta 0 en y_fin. y_fin queda por encima del borde superior de la remera en todos los cuadros del
# paso 10 (mínimo 746 px en 4627 c312 = máster c365); el control lo comprueba cuadro a cuadro.
DEGRADE_V02 = dict(color=(12, 18, 26), op_arriba=0.74, op_meseta=0.70, y_meseta=585, y_fin=705)
OV_DEGRADE = (321, 392) if V02 else OV_FRASE


def degrade_alfa(d=None):
    d = d or DEGRADE_V02
    y = np.arange(H, dtype=np.float64)
    a = d['op_arriba'] + (d['op_meseta'] - d['op_arriba']) * np.clip(y / d['y_meseta'], 0, 1)
    u = np.clip((y - d['y_meseta']) / (d['y_fin'] - d['y_meseta']), 0, 1)
    return np.where(y <= d['y_meseta'], a, d['op_meseta'] * (1 - u * u * (3 - 2 * u)))


def degrade_png(salida, d=None):
    from PIL import Image
    d = d or DEGRADE_V02
    a8 = np.round(degrade_alfa(d) * 255).astype(np.uint8)
    im = np.zeros((H, W, 4), np.uint8); im[..., :3] = d['color']; im[..., 3] = a8[:, None]
    Image.fromarray(im, 'RGBA').save(salida)
    return dict(perfil=d, alfa_8bit_por_fila_cada_50px={int(y): int(a8[y]) for y in range(0, H, 50) if y <= d['y_fin'] + 50},
                ultima_fila_alfa_mayor_8=int(np.nonzero(a8 > 8)[0].max()), ultima_fila_alfa_mayor_0=int(np.nonzero(a8 > 0)[0].max()))


def etapa_placa():
    import pines
    PL.mkdir(parents=True, exist_ok=True)
    t = dict(F=pines.F, W=W, H=H, mx=72, color='#FFFFFF', fs=PLACA['fs'], lh=PLACA['lh'], acento='#CDDDE5',
             logo=PLACA['logo'], ffs=PLACA['ffs'], radio=round(PLACA['logo'] * 0.11), fcolor='rgba(255,255,255,.92)',
             sombra='0 2px 24px rgba(0,0,0,.28)', sombra_f='0 1px 8px rgba(0,0,0,.35)')
    css = pines.CSS % t + 'html,body{background:transparent !important}' \
        '.firma{left:0;right:0;justify-content:center}.firma span{margin-right:-.34em}'
    alto, op, (r, g, b) = PLACA['grad']
    grad = (f'<div class="grad" style="top:0;height:{alto}px;background:linear-gradient(to bottom,'
            f'rgba({r},{g},{b},{op}) 0%,rgba({r},{g},{b},{op * 0.55:.3f}) 45%,rgba({r},{g},{b},0) 100%)"></div>')
    logo = R / 'LOGO' / 'rocce_logo.png'
    docs = {
        'cierre_frase': f'{grad}<div class="frase" style="top:{PLACA["top_frase"]}px;text-align:center">{FRASE_HTML}</div>',
        'cierre_firma': (f'<div class="firma" style="top:{PLACA["top_firma"]}px"><img src="file://{logo}">'
                         f'<span>{FIRMA_TXT}</span></div>'),
    }
    if V02:
        # sin el degradé CSS (va en su propia capa) + máscaras del trazo sin sombra para medir el contraste
        docs['cierre_frase'] = f'<div class="frase" style="top:{PLACA["top_frase"]}px;text-align:center">{FRASE_HTML}</div>'
        docs['mascara_frase'] = (f'<div class="frase" style="top:{PLACA["top_frase"]}px;text-align:center;text-shadow:none">'
                                 f'{FRASE_HTML}</div>')
        docs['mascara_firma'] = (f'<div class="firma" style="top:{PLACA["top_firma"]}px"><img src="file://{logo}" '
                                 f'style="visibility:hidden"><span style="text-shadow:none">{FIRMA_TXT}</span></div>')
    trabajos = []
    for nom, body in docs.items():
        h = PL / f'{nom}.html'
        h.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>',
                     encoding='utf-8')
        trabajos.append(dict(html=str(h), out=str(PL / f'{nom}.png'), w=W, h=H))
    j = PL / '_trabajos.json'; j.write_text(json.dumps(trabajos, indent=1))
    subprocess.run(nice(['node', str(R / 'scripts/life/life_v1_render.js'), str(j)]), check=True)
    from PIL import Image
    rep = {}
    for tr in trabajos:
        im = Image.open(tr['out']); a = np.asarray(im)
        assert im.size == (W, H) and im.mode == 'RGBA', (im.size, im.mode)
        ys, xs = np.nonzero(a[..., 3] > 8)
        rep[Path(tr['out']).name] = dict(modo=im.mode, tam=im.size, md5_pixeles=hashlib.md5(a.tobytes()).hexdigest(),
                                         bbox_alfa_mayor_8=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())])
    a = np.asarray(Image.open(PL / 'cierre_frase.png').convert('RGBA')).astype(np.float32)
    ys, xs = np.nonzero((a[..., 3] > 200) & (a[..., :3].min(-1) > 200))
    rep['frase_letras_bbox'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    f = np.asarray(Image.open(PL / 'cierre_firma.png').convert('RGBA')).astype(np.float32)
    ys, xs = np.nonzero(f[..., 3] > 200)
    rep['firma_bbox_opaco'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    ys, xs = np.nonzero((f[..., 3] > 250) & (f[..., :3].min(-1) > 250))
    rep['ficha_logo_bbox'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    rep['radio_px'] = t['radio']; rep['radio_pct'] = round(t['radio'] / PLACA['logo'] * 100, 1)
    if V02:
        rep['degrade'] = degrade_png(PL / 'cierre_degrade.png')
        for nom in ('mascara_frase', 'mascara_firma'):
            m_ = np.asarray(Image.open(PL / f'{nom}.png').convert('RGBA'))[..., 3] >= 128
            ys, xs = np.nonzero(m_)
            rep[nom] = dict(criterio='trazo = alfa ≥ 128 (cobertura ≥ 50 %), sin sombra', pixeles=int(m_.sum()),
                            bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())])
    # logo: la ficha escalada contra el PNG original reducido con el mismo tamaño (sin recolorear ni deformar)
    lg = np.asarray(Image.open(logo).convert('RGB').resize((PLACA['logo'], PLACA['logo']), Image.LANCZOS)).astype(np.float32)
    x0, y0 = rep['ficha_logo_bbox'][:2]
    fx = f[y0:y0 + PLACA['logo'], x0:x0 + PLACA['logo'], :3]
    cen = slice(12, PLACA['logo'] - 12)
    rep['logo_dif_media_contra_original_reducido'] = round(float(np.abs(fx[cen, cen] - lg[cen, cen]).mean()), 2)
    jdump(rep, PL / 'placa.json')
    print(json.dumps(rep, ensure_ascii=False))


# =====================================================================================================
# etapa audio · columna «Sonido» del guion. Ambiente real de cada toma, foley PROVISORIO (obturador, barrido) y música
# TEMP propia sintetizada con sonido.py (100 BPM: pulso cada 0,6 s, La menor). Sin voz. Versión SINMUSICA = ambiente +
# foley, con el foley idéntico muestra por muestra (misma semilla).
# =====================================================================================================
WAV = {'completa': A / 'v3_completa.wav', 'sinmusica': A / 'v3_sinmusica.wav'}
XF = 0.03
LP_HZ = 450                   # pasabajos de la música hasta el drop
LP_ABRE = (6.40, 6.64)        # el filtro se abre (fundido cruzado pasabajos → completa, curva suave)
HUECO = (6.33, 6.40)


# v02: la rompiente real del paso 10 (4627 8,933–11,333) se midió en el audio de la toma (envolvente > 1,5 kHz de la
# espuma, ventanas de 20 ms): sube desde 10,52 s de la fuente y llega al máximo en 10,94 s = 12,707 s del máster (c381),
# donde también abre la salpicadura arriba a la derecha (hoja v02/hojas/4627_c268-c339_c3.jpg). La campana queda en 12,50
# (cadencia 0,6 s) y el fundido del ambiente arranca en la rompiente (12,70 → 13,10); música, bombo y efectos siguen
# fundiendo desde 12,60 como en v01.
AMB_FUNDIDO = 12.70 if V02 else 12.60


def _ambiente(m):
    # (toma, fuente desde, máster desde, máster hasta, dB, pasa-altos)
    t2 = PLANOS[1]['n0'] / FPS                     # v01: 6,000 · v02: 12,100
    m.ambiente('IMG_7885', 0.000, 0.000, 1.800, 0, hp=80, ini_fade=.01, fin_fade=XF)          # ola real (paso 1)
    m.ambiente('IMG_4627', t2 - XF, 1.800 - XF, 2.700, 2, hp=80, fade=XF)                      # paso 2
    m.ambiente('IMG_7896', 0.000, 2.700 - XF, 3.600, 8, hp=120, fade=XF)                        # paso 3
    m.ambiente('IMG_7896', 1.600 - XF, 3.600 - XF, 4.700, 8, hp=120, fade=XF)                   # paso 4
    m.ambiente('IMG_7884', 0.000, 4.700 - XF, 5.600, 6, hp=120, fade=XF)                        # paso 5
    m.ambiente('IMG_7884', 2.000 - XF, 5.600 - XF, 6.400, 5, hp=120, fade=XF)                   # paso 6
    m.ambiente('IMG_7884', 2.800 - XF, 6.400 - XF, 8.000, 6, hp=80, fade=XF)                    # paso 7: ola real 7,0–7,8
    m.ambiente('IMG_7884', 4.400 - XF, 8.000 - XF, 8.800, 4, hp=80, fade=XF)                    # paso 8 (la ola sigue)
    m.ambiente('IMG_4627', 3.500, 8.800 - 0.05, 9.300, 4, hp=80, ini_fade=.05, fin_fade=XF)     # paso 8, misma roca
    m.ambiente('IMG_7885', 0.000, 9.300 - XF, 10.700, 0, hp=80, fade=XF)                       # paso 9 (cuadro 0 otra vez)
    if V02:                                         # paso 10: 4627 desde c268 (8,933 s), en sincronía con la imagen
        m.ambiente('IMG_4627', PLANOS[9]['n0'] / FPS - XF, 10.700 - XF, DUR, 3, hp=80, ini_fade=XF)
    else:
        m.ambiente('IMG_4627', 0.000, 10.700 - XF, DUR, 3, hp=80, ini_fade=XF)                  # paso 10: rompiente ≈ 12,7
    m.fundido('amb', AMB_FUNDIDO, DUR)


def _foley(m, S):
    S.rng = np.random.default_rng(31)
    m.obturador(7.985, .50)          # la foto: el segundo clic del obturador cae en el flash (c240)
    m.barrido(10.70, .32, .20)       # barrido al cierre


def _musica(m, S):
    S.rng = np.random.default_rng(47)
    pulso = lambda t, g=.42: m.bombo(t, g, f0=72, f1=40, dec=.24)
    sordo = lambda t: (m.bombo(t, .95, f0=85, f1=40, dec=.32), m.impacto(t, .22))
    agudo = lambda t: (m.bombo(t, .70, f0=150, f1=55, dec=.16), m.palma(t, .30), m.toque(t, .14, 3200))
    ch = lambda t0, t1, g=.09: [m.charles(round(float(t), 3), g) for t in np.arange(t0, t1 - 1e-6, 0.3)]
    # 0–6,40 · apuesta y evidencia: pulso grave cada 0,6 s (la cuenta regresiva), pad con pasabajos, golpes en los cortes
    for k in range(11):
        pulso(round(0.6 * k, 3))
    m.pad(0.0, [45, 48, 52], 3.4, .05, 600, a=.15)
    m.pad(3.6, [41, 45, 48], 2.7, .05, 600, a=.10)
    m.ocho08(0.0, 33, 1.7, .22); m.ocho08(1.8, 33, .8, .22); m.ocho08(3.6, 29, 1.6, .22)
    sordo(1.80); sordo(2.70); agudo(3.60); agudo(4.70)
    # 5,60–6,33 · sube (redoble + subida) · hueco 6,33–6,40
    m.redoble(5.60, 6.33, .14); m.subida(5.60, 6.33, .18)
    m.pad(5.6, [43, 47, 50], .73, .06, 700, a=.05)
    # 6,40 · DROP (el color vuelve, el filtro se abre)
    m.bombo(6.40, 1.0); m.impacto(6.40, .5)
    m.ocho08(6.40, 45, 1.1, .6, glide_desde=52)
    m.pad(6.40, [57, 60, 64, 69], 1.5, .07)
    m.campana(6.40, 81, .06)
    m.bombo(7.00, .60); m.bombo(7.60, .65); m.palma(7.60, .26)        # más bajo: deja oír la ola real 7,0–7,8
    m.ocho08(7.60, 45, .35, .5)
    ch(6.40, 8.00)
    # 8,00 · «Esto.»: golpe con la foto
    m.bombo(8.00, 1.0); m.impacto(8.00, .45); m.campana(8.00, 88, .06, .9)
    m.ocho08(8.00, 41, 1.2, .55, glide_desde=48)
    m.pad(8.00, [53, 57, 60, 65], 1.3, .07)
    m.palma(8.60, .22); ch(8.30, 9.30, .07)
    # 9,30 · reenganche: vuelve el pulso (ahora sin filtro)
    for t in (9.30, 9.90, 10.50):
        pulso(t, .55)
    m.pad(9.30, [57, 60, 64], 1.4, .055, 1100)
    m.ocho08(9.30, 45, .5, .45); m.ocho08(9.90, 45, .5, .45); m.ocho08(10.50, 43, .2, .45)
    # 10,70 · cierre: cadencia (Fa → Sol → La menor), campana final; fundido 12,6–13,1
    m.bombo(10.70, .9); m.pad(10.70, [53, 57, 60, 65], .6, .06); m.ocho08(10.70, 41, .5, .5)
    m.bombo(11.30, .8); m.palma(11.30); m.pad(11.30, [55, 59, 62, 67], .6, .06); m.ocho08(11.30, 43, .5, .5)
    m.bombo(11.90, .85); m.pad(11.90, [57, 60, 64, 69], 1.2, .06, r=.6); m.ocho08(11.90, 45, .9, .5)
    m.bombo(12.50, .7); m.campana(12.50, 81, .06, .9)
    ch(10.70, 12.50, .07)


def _pasabajos_y_hueco(m):
    """música con pasabajos hasta el drop: fundido cruzado de la pista 'mus' filtrada (Butterworth 2.º orden, 450 Hz)
    a la completa en 6,40–6,64 (suave). Después, el hueco 6,33–6,40 en música, bombo y efectos."""
    import sonido as S
    mus = m.pistas['mus']; lp = S.filt(mus, 'low', LP_HZ)
    t = np.arange(m.N) / SR
    c = np.clip((t - LP_ABRE[0]) / (LP_ABRE[1] - LP_ABRE[0]), 0, 1); c = c * c * (3 - 2 * c)
    m.pistas['mus'] = lp * (1 - c)[:, None] + mus * c[:, None]
    for p in ('mus', 'bombo', 'fx'):
        m.silenciar(p, *HUECO, rampa=0.02)


def etapa_audio():
    import sonido as S
    A.mkdir(parents=True, exist_ok=True)
    rep = {}
    for k in ('completa', 'sinmusica'):
        m = S.Mezcla(DUR)
        _ambiente(m); _foley(m, S)
        if k == 'completa':
            _musica(m, S); _pasabajos_y_hueco(m)
            m.fundido('mus', 12.60, DUR); m.fundido('bombo', 12.60, DUR)
            m.fundido('fx', 12.60, DUR)       # colas de reverberación de la música (van en 'fx')
        I, Pk = m.exportar(str(WAV[k]), lufs=-14.0)
        rep[k] = dict(exportar=dict(lufs=I, pico_dbtp=Pk))
        if Pk > -1.5:
            rep[k]['limitado'] = L2.limitar_tp(WAV[k])
        rep[k]['final'] = dict(zip(('lufs', 'pico_dbtp', 'lra'), L2.medir_ebur(WAV[k])))
        print(k, rep[k], flush=True)
    jdump(rep, A / 'audio.json')


# =====================================================================================================
# etapa master · por número: textos + placa + mezcla completa → H.264 High 4.0 / AAC-LC (life_v2.master_v2: PNG a
# 30 fps y ventana por tiempo). La versión SINMUSICA lleva el MISMO flujo de video (copia, sin recodificar) y su mezcla.
# =====================================================================================================
def sinmusica_de(completa, wav, salida):
    V.sh(['ffmpeg', '-v', 'error', '-y', '-i', str(completa), '-i', str(wav), '-map', '0:v:0', '-map', '1:a:0',
          '-c:v', 'copy', '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
          '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
          '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
          '-shortest', '-movflags', '+faststart', str(salida)])
    return salida


CAMBIO_V02 = set(range(54, 81)) | set(range(321, NF))      # cuadros del máster que cambian en v02 (pasos 2 y 10)


def _claves(mp4):
    out = U.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=key_frame', '-of', 'csv=p=0',
                 str(mp4)]).decode().split()
    return [i for i, k in enumerate(out) if k.strip().startswith('1')]


def _fmd5(mp4):
    out = U.run(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(mp4), '-map', '0:v', '-f', 'framemd5', '-'])).decode()
    return [l.split(',')[-1].strip() for l in out.splitlines() if l and not l.startswith('#')]


def empalme_v02(N, completo, salida):
    """v02 = los GOP de v01 que no tocan los pasos 2 y 10, copiados sin recodificar (mismos paquetes H.264 que el máster
    aprobado), + los GOP de la codificación completa de v02 que contienen algún cuadro de esos pasos. Las dos
    codificaciones salen de la misma receta (master_v2: x264 High 4.0, crf 17, GOP 30, mismo SPS/PPS) y tienen los cuadros
    clave en los mismos lugares (se comprueba); los GOP son cerrados (cada uno empieza en un IDR). Corte con el muxer
    segment en esos IDR y unión con el demuxer concat (copia de flujo); el audio es el AAC de la codificación completa.
    Comprobación: cada cuadro decodificado del empalme es idéntico (framemd5) al de v01 o al de la codificación completa,
    según el tramo, y los tiempos de presentación quedan en la grilla de 30 fps."""
    v01 = T / 'master' / nombre(N, 'completa', 'v01')
    k1, k2 = _claves(v01), _claves(completo)
    assert k1 == k2, (k1, k2)
    gops = [(a, b - 1) for a, b in zip(k1, k1[1:] + [NF])]
    fuente = ['v02' if any(n in CAMBIO_V02 for n in range(a, b + 1)) else 'v01' for a, b in gops]
    tramos, ini = [], 0                                    # tramos consecutivos de la misma fuente
    for i in range(1, len(gops) + 1):
        if i == len(gops) or fuente[i] != fuente[ini]:
            tramos.append((gops[ini][0], gops[i - 1][1], fuente[ini])); ini = i
    cortes = ','.join(str(a) for a, _, _ in tramos[1:])
    tmp = MAS / f'_empalme_{N}'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    for nom, src in (('v01', v01), ('v02', completo)):
        V.sh(['ffmpeg', '-v', 'error', '-i', str(src), '-map', '0:v', '-c', 'copy', '-f', 'segment', '-segment_frames', cortes,
              '-reset_timestamps', '1', '-segment_format', 'mp4', str(tmp / f'{nom}_%02d.mp4')])
    (tmp / 'lista.txt').write_text(''.join(f"file '{tmp / f'{f}_{i:02d}.mp4'}'\n" for i, (_, _, f) in enumerate(tramos)))
    V.sh(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(tmp / 'lista.txt'), '-i', str(completo),
          '-map', '0:v:0', '-map', '1:a:0', '-c', 'copy', '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
          '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
          '-movflags', '+faststart', str(salida)])
    # comprobaciones
    fa, fb, fe = _fmd5(v01), _fmd5(completo), _fmd5(salida)
    assert len(fe) == NF, len(fe)
    origen = ['v01' if e == a else ('v02' if e == b else 'NINGUNO') for a, b, e in zip(fa, fb, fe)]
    esperado = [f for a, b, f in tramos for _ in range(a, b + 1)]
    pts = U.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=pts_time', '-of', 'csv=p=0',
                 str(salida)]).decode().split()
    fuera = [i for i, t in enumerate(pts) if abs(float(t.strip(',')) - i / FPS) > 0.002]
    # cuadros con fuente ambigua (idénticos en v01 y en la codificación completa) cuentan para los dos
    ok = all(o == e or (fa[i] == fb[i] and o in ('v01', 'v02')) for i, (o, e) in enumerate(zip(origen, esperado)))
    tam = [int(x) for x in U.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'packet=size',
                                  '-of', 'csv=p=0', str(salida)]).decode().split()]
    pico = max(sum(tam[i:i + FPS]) for i in range(len(tam) - FPS + 1)) * 8 / 1e6
    buf, vmin = 25e6 * 0.9, 25e6 * 0.9           # búfer de decodificación con los valores del máster (20 Mbit/s, 25 Mbit)
    for b in tam:
        buf = min(25e6, buf + 20e6 / FPS) - b * 8; vmin = min(vmin, buf)
    r = dict(metodo=empalme_v02.__doc__, v01=str(v01), codificacion_completa=str(completo), claves=k1,
             tramos=[dict(cuadros=f'c{a}–c{b}', fuente=f) for a, b, f in tramos],
             cuadros_identicos_a_su_fuente=ok, cuadros_decodificados=len(fe), pts_fuera_de_grilla=fuera,
             cuadros_v02_que_no_cambian=[n for n in range(NF) if esperado[n] == 'v02' and n not in CAMBIO_V02],
             pico_mbit_por_segundo_ventana_30_cuadros=round(pico, 2),
             vbv_20M_25M_minimo_mbit=round(vmin / 1e6, 2), vbv_sin_vaciarse=vmin > 0)
    assert ok and not fuera, r
    shutil.rmtree(tmp)
    jdump(r, MAS / f'empalme_{N}.json')
    return r


def etapa_empalmar():
    """v02: rehace solo el empalme y la versión SINMUSICA desde las codificaciones completas ya hechas."""
    for N in [int(x) for x in sys.argv[2:]] or list(NUMEROS):
        r = empalme_v02(N, MAS / 'codificacion_completa' / nombre(N, 'completa'), MAS / nombre(N, 'completa'))
        sinmusica_de(MAS / nombre(N, 'completa'), WAV['sinmusica'], MAS / nombre(N, 'sinmusica'))
        print('empalme', N, r['tramos'], r['vbv_20M_25M_minimo_mbit'], flush=True)


def overlays_placa():
    ov = [(PL / 'cierre_frase.png', 0, 0, *OV_FRASE), (PL / 'cierre_firma.png', 0, 0, *OV_FIRMA)]
    return ([(PL / 'cierre_degrade.png', 0, 0, *OV_DEGRADE)] + ov) if V02 else ov


def etapa_master():
    MAS.mkdir(parents=True, exist_ok=True)
    ov = overlays_placa()
    solo = [int(x) for x in sys.argv[2:]] or list(NUMEROS)
    for N in solo:
        for k in ('completa', 'sinmusica'):
            if (MAS / nombre(N, k)).exists():
                (MAS / nombre(N, k)).unlink()          # intermedio de trabajo (nunca entregado): se rehace
        if V02:
            completo = MAS / 'codificacion_completa' / nombre(N, 'completa'); completo.parent.mkdir(exist_ok=True)
            L2.master_v2(BASE, WAV['completa'], completo, ass_path=TX / f'v3_textos_{N}.ass', overlays=ov)
            r = empalme_v02(N, completo, MAS / nombre(N, 'completa'))
            print('empalme', N, r['tramos'], r['vbv_20M_25M_minimo_mbit'], flush=True)
        else:
            L2.master_v2(BASE, WAV['completa'], MAS / nombre(N, 'completa'), ass_path=TX / f'v3_textos_{N}.ass',
                         overlays=ov)
        sinmusica_de(MAS / nombre(N, 'completa'), WAV['sinmusica'], MAS / nombre(N, 'sinmusica'))
        print('->', N, flush=True)
    if V02 and REVISION in solo:
        # referencia «el mismo cuadro sin texto» para el contraste de la placa: la base con el degradé solo, codificada
        # con los mismos ajustes que el máster (intermedio de control, no se entrega)
        L2.master_v2(BASE, WAV['completa'], MAS / 'ref_sin_texto_36.mp4', ass_path=None, overlays=[ov[0]])
        print('-> ref_sin_texto_36', flush=True)



# =====================================================================================================
# detectores de prenda para el control (sobre v3_base0.mp4: en color en todos los cuadros, misma geometría que el máster)
# =====================================================================================================
KY = np.array([0.2126, 0.7152, 0.0722], np.float32)


def _ls(rgb):
    mx = rgb.max(-1); mn = rgb.min(-1)
    return rgb @ KY, (mx - mn) / (mx + 1)


def _zona(shape, caja):
    z = np.zeros(shape, bool); x0, y0, x1, y1 = caja; z[y0:y1, x0:x1] = True
    return z


def estampado_blanca(rgb, caja):
    """Blanca y su estampado de espalda («ROCCÉ» + «Founders Privée»).
    remera = mayor componente de tela clara y neutra (L > 140, sat < 0,35) dentro de la caja, cerrada y rellena;
    «Founders Privée» = celeste (B − R > 25, sat > 0,15, L > 100) dentro de la remera: el grupo más grande (dilatado 12 px)
    y los grupos que comparten sus filas (las sombras azuladas del cuerpo, más abajo, quedan afuera);
    «ROCCÉ» = trazos oscuros y neutros (L < 120, B ≥ R − 4, ≥ 60 px) en la banda de 1,2 alturas del celeste por encima.
    Devuelve (remera, estampado, caja del estampado, caja de la remera)."""
    from scipy import ndimage as nd
    L, sat = _ls(rgb)
    br = nd.binary_opening(_zona(L.shape, caja) & (L > 140) & (sat < 0.35), iterations=2)
    lab, k = nd.label(br)
    if not k:
        return None, None, None, None
    s = nd.sum(br, lab, range(1, k + 1)); sh = lab == (1 + int(np.argmax(s)))
    fill = nd.binary_fill_holes(nd.binary_closing(sh, iterations=8))
    # celeste RELATIVO a la tela que lo rodea: la Blanca a la sombra ya es fría (B − R ≈ 40 a L 200, medido en c60/c260/
    # c360), así que un umbral absoluto toma las sombras del cuerpo. Los trazos del celeste son finos (≤ 13 px) y se
    # separan del promedio local de la tela (ventana de 61 px) en B − R y en G − R.
    br, gr = rgb[..., 2] - rgb[..., 0], rgb[..., 1] - rgb[..., 0]
    f = fill.astype(np.float32); den = np.maximum(nd.uniform_filter(f, 61), 1e-3)
    dbr = br - nd.uniform_filter(br * f, 61) / den; dgr = gr - nd.uniform_filter(gr * f, 61) / den
    cel = nd.binary_opening(fill & (L > 100) & (br > 25) & (dbr > 10) & (dgr > 5), iterations=1)
    lab, k = nd.label(nd.binary_dilation(cel, iterations=12))
    if not k:
        return fill, None, None, L2._caja(fill)
    s = nd.sum(cel, lab, range(1, k + 1)); g = 1 + int(np.argmax(s))
    gy = np.nonzero((lab == g).any(1))[0]
    keep = [i for i in range(1, k + 1) if s[i - 1] >= 0.05 * s.max() and
            (lambda ys: ys.min() <= gy.max() and ys.max() >= gy.min())(np.nonzero((lab == i).any(1))[0])]
    cel &= np.isin(lab, keep)
    ys, xs = np.nonzero(cel); F = [xs.min(), ys.min(), xs.max(), ys.max()]; fh = F[3] - F[1]
    band = np.zeros(L.shape, bool); band[max(0, int(F[1] - 1.2 * fh)):F[1] + int(0.3 * fh), F[0]:F[2] + 1] = True
    roc = nd.binary_opening(fill & band & (L < 120) & (rgb[..., 2] >= rgb[..., 0] - 4), iterations=1)
    lab, k = nd.label(roc)
    if k:
        s = nd.sum(roc, lab, range(1, k + 1)); roc &= np.isin(lab, 1 + np.nonzero(s >= 60)[0])
    est = cel | roc
    return fill, est, L2._caja(est), L2._caja(fill)


def estampado_negra(rgb, caja):
    """letras claras y neutras (L > 105, sat < 0,16, ≥ 40 px) sobre tela negra (fracción de L < 70 en 61 px > 0,45)."""
    from scipy import ndimage as nd
    L, sat = _ls(rgb)
    tela = nd.uniform_filter((L < 70).astype(np.float32), 61) > 0.45
    let = nd.binary_opening(_zona(L.shape, caja) & tela & (L > 105) & (sat < 0.16), iterations=1)
    lab, k = nd.label(let)
    if not k:
        return None, None
    s = nd.sum(let, lab, range(1, k + 1)); let &= np.isin(lab, 1 + np.nonzero(s >= 40)[0])
    return (let, L2._caja(let)) if let.any() else (None, None)


# cajas de búsqueda por plano (x0, y0, x1, y1 en el cuadro 1080×1920); None = esa prenda no está en el plano
CAJAS_PRENDA = {
    '01': ((100, 620, 800, 1150), (250, 450, 1080, 1600)),
    '02': ((0, 700, 1080, 1850), None),
    '03': ((60, 950, 700, 1350), None),
    '04': ((60, 950, 700, 1350), None),
    '05': ((150, 1000, 800, 1300), (450, 650, 1080, 1500)),
    '06': ((0, 700, 1080, 1500), (650, 600, 1080, 1700)),
    '07': ((0, 600, 1080, 1500), None),
    '08': ((100, 950, 1000, 1850), None),
    '09': ((100, 620, 800, 1150), (250, 450, 1080, 1600)),
    '10': ((0, 700, 1080, 1850), None),
}
if V02:
    # tramos nuevos de 4627: la remera arranca en y ≥ 746 y termina en y ≤ 1667; caja abierta abajo y a los costados para
    # no recortar la remera (la medición de márgenes no puede quedar limitada por la caja)
    CAJAS_PRENDA['02'] = CAJAS_PRENDA['10'] = ((0, 450, 1080, 1920), None)


def plano_de(n):
    return [p for p in PLANOS if p['m0'] <= n][-1]['id']



# =====================================================================================================
# etapa control · evidencia en evidencia_v01/ (técnica de los 10 archivos; visual sobre el máster de revisión 36)
# =====================================================================================================
TRAMOS = [('1 apuesta · 7885', 0.0, 1.8), ('2 Diciembre · 4627', 1.8, 2.7), ('3 Arranco en enero · 7896', 2.7, 3.6),
          ('4 Enero también · 7896', 3.6, 4.7), ('5 días/domingos · 7884', 4.7, 5.6), ('6 sube · 7884', 5.6, 6.33),
          ('hueco 6,33–6,40', 6.33, 6.40), ('7 giro/drop · 7884', 6.4, 8.0), ('8 Esto. · foto', 8.0, 9.3),
          ('9 Te quedan 5. · 7885', 9.3, 10.7), ('10 CTA · 4627', 10.7, DUR), ('último 0,5 s', DUR - 0.5, DUR)]
MARCAS_UBICACION = (b'ISO6709', b'location', b'com.apple.quicktime', b'\xa9xyz')
BARRIDO = set(range(318, 324))          # cuadros con desenfoque de barrido: sin medición de prenda
CRITICOS = {0: 'hook_quedan_N_dias', 24: 'hook_arrancas_o_esperas', 53: 'fin_paso1', 54: 'diciembre_fiestas',
            81: 'arranco_en_enero', 108: 'enero_tambien', 141: 'N_dias_5_domingos', 168: 'que_entra_en_uno',
            191: 'ultimo_gris', 192: 'giro_color_0.2', 193: 'color_0.4', 194: 'color_0.6', 195: 'color_0.8',
            196: 'color_pleno', 210: 'un_celular', 239: 'ultimo_7884', 240: 'esto_flash_0.90', 241: 'esto_flash_0.45',
            242: 'esto_foto', 260: 'esto', 278: 'fin_foto', 279: 'te_quedan_5', 321: 'cta_barrido', 327: 'entra_frase',
            333: 'entra_firma', 360: 'placa', 392: 'ultimo'}


def ebur_texto(f):
    r = subprocess.run(nice(['ffmpeg', '-nostats', '-i', str(f), '-vn', '-af', 'ebur128=peak=true:framelog=quiet',
                             '-f', 'null', '-']), capture_output=True, text=True).stderr
    resumen = r[r.rfind('Summary:'):]
    g = lambda k: float([l for l in resumen.splitlines() if l.strip().startswith(k)][-1].split()[1])
    return dict(lufs_integrado=g('I:'), lra=g('LRA:'), pico_dbtp=g('Peak:')), resumen


def tecnico(f, ev=None):
    import fmt03_v02 as U2
    ev = ev or EVID
    err = subprocess.run(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(f), '-f', 'null', '-']),
                         capture_output=True, text=True).stderr.strip()
    pj = json.loads(U.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(f)]))
    (ev / 'ffprobe').mkdir(parents=True, exist_ok=True); (ev / 'ebur128').mkdir(exist_ok=True)
    jdump(pj, ev / 'ffprobe' / f'{f.stem}.json')
    son, resumen = ebur_texto(f)
    (ev / 'ebur128' / f'{f.stem}.txt').write_text(resumen, encoding='utf-8')
    cuerpo = f.read_bytes()
    vs = [x for x in pj['streams'] if x['codec_type'] == 'video'][0]
    au = [x for x in pj['streams'] if x['codec_type'] == 'audio'][0]
    a = U.audio_np(f)
    niv, v100, sil = U.niveles_tramos(a, TRAMOS)
    mom = U2.momentanea(f)
    r = dict(archivo=f.name, bytes=f.stat().st_size, sha256=hashlib.sha256(cuerpo).hexdigest(),
             md5_video=U.md5_stream(f, 'v'), md5_audio=U.md5_stream(f, 'a'),
             decodifica_completo=(err == ''), errores_decodificacion=err[:500],
             video=dict(codec=vs['codec_name'], perfil=vs.get('profile'), nivel=vs.get('level'), pix_fmt=vs['pix_fmt'],
                        ancho=vs['width'], alto=vs['height'], fps=vs['r_frame_rate'], cuadros=int(vs['nb_frames']),
                        duracion=float(vs['duration']), color=[vs.get('color_range'), vs.get('color_space'),
                                                               vs.get('color_transfer'), vs.get('color_primaries')]),
             audio=dict(codec=au['codec_name'], perfil=au.get('profile'), hz=int(au['sample_rate']), canales=au['channels'],
                        duracion=float(au['duration'])),
             duracion_formato=float(pj['format']['duration']), etiquetas_formato=pj['format'].get('tags', {}),
             marcas_gps_o_ubicacion=[m.decode('latin1') for m in MARCAS_UBICACION if m in cuerpo], atomos=L2.atomos(f),
             sonoridad=son, sonoridad_momentanea_tramos=U2.momentanea_tramos(mom, TRAMOS),
             niveles_por_tramo=niv, ventanas_100ms_bajo_menos50dbfs=sil,
             silencio_final_s=L2.silencio_final(a),
             rms_ultimo_05s_dbfs=round(float(20 * np.log10(np.sqrt((a[-SR // 2:] ** 2).mean()) + 1e-12)), 1))
    r['duracion_video_igual_audio'] = abs(r['video']['duracion'] - r['audio']['duracion']) < 0.5 / FPS
    r['faststart'] = r['atomos'].index('moov') < r['atomos'].index('mdat')
    return r, mom


def _yuv_lector(path):
    return subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(path), '-f', 'rawvideo',
                                  '-pix_fmt', 'yuv420p', '-']), stdout=subprocess.PIPE)


def _ass_lector(ass_path):
    return subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}:d={DUR}',
                                  '-vf', f'subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter,format=gray',
                                  '-f', 'rawvideo', '-']), stdout=subprocess.PIPE)


def _croma(Cb, Cr, m):
    c = np.sqrt((Cb.astype(np.float32) - 128) ** 2 + (Cr.astype(np.float32) - 128) ** 2)[m]
    if c.size == 0:
        return None
    return dict(media=round(float(c.mean()), 3), p99=round(float(np.percentile(c, 99)), 2), max=round(float(c.max()), 2),
                pct_mayor_4=round(float((c > 4).mean() * 100), 3))


Y_PLACA = 708 if V02 else 780         # v01: alfa > 8 hasta y 775 · v02: alfa > 0 hasta y 701 (degradé numpy)


def pasada_cuadros(master, base, ass_path):
    """recorre los 393 cuadros del máster, la base (después del color, antes de textos y placa) y el .ass solo (sobre
    negro) a la vez. Por cuadro: caja del texto renderizado, croma (|Cb − 128|, |Cr − 128| → módulo, niveles de 8 bits)
    fuera del texto y dentro del texto, en el máster y en la base, y diferencia de luma máster − base dentro del texto y
    fuera de textos y placa (lo que no es texto ni placa tiene que ser la base)."""
    ny = W * H; nc = ny // 4
    pm, pb, pa = _yuv_lector(master), _yuv_lector(base), _ass_lector(ass_path)
    filas = []
    for n in range(NF):
        bm = pm.stdout.read(ny + 2 * nc); bb_ = pb.stdout.read(ny + 2 * nc); ba = pa.stdout.read(ny)
        assert len(bm) == len(bb_) == ny + 2 * nc and len(ba) == ny, n
        Ym, Cbm, Crm = L2.partir(bm); Yb, Cbb, Crb = L2.partir(bb_)
        A = np.frombuffer(ba, np.uint8).reshape(H, W)
        tm = A > 8; caja = L2._caja(tm)
        excl = np.zeros((H, W), bool)
        if caja:
            x0, y0, x1, y1 = caja; excl[max(0, y0 - 16):y1 + 17, max(0, x0 - 16):x1 + 17] = True
        if n >= OV_DEGRADE[0]:
            excl[:Y_PLACA] = True             # degradé + frase + firma
        ec = excl[::2, ::2]
        dentro_c = np.zeros_like(ec)
        if caja:
            dentro_c[y0 // 2:y1 // 2 + 1, x0 // 2:x1 // 2 + 1] = True
        dY = np.abs(Ym.astype(np.int16) - Yb.astype(np.int16))
        filas.append(dict(
            cuadro=n, t=round(n / FPS, 3), texto_caja=caja,
            croma_master_fuera=_croma(Cbm, Crm, ~ec), croma_base_fuera=_croma(Cbb, Crb, ~ec),
            croma_master_texto=_croma(Cbm, Crm, dentro_c) if caja else None,
            luma_dif_dentro_texto=round(float(dY[tm].mean()), 2) if caja else None,
            luma_dif_fuera=round(float(dY[~excl].mean()), 3), luma_dif_fuera_p999=int(np.percentile(dY[~excl], 99.9))))
    for p in (pm, pb, pa):
        p.stdout.close(); p.wait()
    return filas


def grafico_croma(filas, salida, n1=NF - 1):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT, 22); fch = ImageFont.truetype(FONT, 17)
    Wd, Hd, ml, mb, mt = 1500, 560, 80, 60, 50
    im = Image.new('RGB', (Wd, Hd), (250, 250, 250)); d = ImageDraw.Draw(im)
    vmax = max(f['croma_master_fuera']['p99'] for f in filas[:n1 + 1]) * 1.1
    X_ = lambda n: ml + (Wd - ml - 30) * n / n1
    Y_ = lambda v: Hd - mb - (Hd - mb - mt) * v / vmax
    for v in range(0, int(vmax) + 1, 5):
        d.line([ml, Y_(v), Wd - 30, Y_(v)], fill=(225, 225, 225)); d.text((ml - 40, Y_(v) - 10), str(v), font=fch, fill=(90, 90, 90))
    for n, rot in ((192, 'c192 vuelve el color'), (196, 'c196 pleno'), (240, 'c240 foto')):
        if n <= n1:
            d.line([X_(n), mt, X_(n), Hd - mb], fill=(200, 120, 120), width=2); d.text((X_(n) + 4, mt + (0 if n != 196 else 24)), rot, font=fch, fill=(160, 60, 60))
    for k, col in (('p99', (60, 110, 200)), ('media', (20, 20, 20))):
        pts = [(X_(f['cuadro']), Y_(f['croma_master_fuera'][k])) for f in filas[:n1 + 1]]
        d.line(pts, fill=col, width=3)
    for n in range(0, n1 + 1, 30):
        d.text((X_(n) - 10, Hd - mb + 8), f'c{n}', font=fch, fill=(90, 90, 90))
    d.text((ml, 10), 'Croma del máster 36 fuera de los textos (módulo |Cb−128|,|Cr−128|, 8 bits) · negro = media · azul = p99',
           font=fnt, fill=(20, 20, 20))
    im.save(salida)


def hoja_rango(mp4, n0, n1, salida, ancho=200, cols=10, recorte=None):
    """todos los cuadros n0–n1 en una hoja (un solo decodificado). recorte = (x, y, w, h) en el cuadro 1080×1920."""
    k = n1 - n0 + 1; filas = math.ceil(k / cols)
    cr = f'crop={recorte[2]}:{recorte[3]}:{recorte[0]}:{recorte[1]},' if recorte else ''
    U.run(nice(['ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-vf',
                f"select='between(n\\,{n0}\\,{n1})',{cr}scale={ancho}:-2,drawtext=fontfile={FONT}:text='c%{{eif\\:n+{n0}\\:d}}':"
                f"x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.7,tile={cols}x{filas}:padding=2",
                '-frames:v', '1', '-fps_mode', 'vfr', '-q:v', '3', str(salida)]))


def etapa_control():
    from PIL import Image, ImageDraw
    EVID.mkdir(parents=True, exist_ok=True)
    VAL = EVID / 'validaciones'; VAL.mkdir(exist_ok=True)
    f36 = MAS / nombre(REVISION, 'completa')
    solo = [int(x) for x in sys.argv[2:]] or list(NUMEROS)          # v02: primero solo el 36 (orden de entrega de Roma)
    rep = dict(fecha='2026-11-25', pieza=f'V3 «5 domingos» {VERSION}', master_revision=nombre(REVISION, 'completa'),
               numeros_en_este_control=solo, archivos={})
    # ---- 1 · técnica de los archivos
    for N in solo:
        for k in ('completa', 'sinmusica'):
            f = MAS / nombre(N, k)
            r, mom = tecnico(f)
            rep['archivos'][f.name] = r
            if N == REVISION:
                jdump(mom, EVID / f'sonoridad_momentanea_{N}_{k}.json')
            print(f.name, r['sonoridad'], 'v', r['md5_video'], 'a', r['md5_audio'], 'err', r['decodifica_completo'],
                  'gps', r['marcas_gps_o_ubicacion'], r['atomos'], flush=True)
    A_ = rep['archivos']
    rep['cruces'] = cruces(A_, solo)
    print('cruces', rep['cruces'], flush=True)
    # ---- 2 · hojas, cortes y cuadros críticos del máster 36
    U.hoja_contacto(f36, EVID / f'hoja_contacto_cada_0.5s_{REVISION}.jpg', cada=15, cols=9, ancho=240)
    U.cuadros_corte(f36, CORTES, EVID / 'cortes', NF - 1)
    CC = EVID / 'cuadros_criticos'; CC.mkdir(exist_ok=True)
    ns = sorted(CRITICOS)
    sel = '+'.join(f'eq(n\\,{k})' for k in ns)
    U.run(nice(['ffmpeg', '-v', 'error', '-y', '-i', str(f36), '-vf', f"select='{sel}'", '-fps_mode', 'vfr', '-q:v', '2',
                str(CC / 'tmp_%03d.jpg')]))
    for i, n in enumerate(ns):
        (CC / f'tmp_{i + 1:03d}.jpg').rename(CC / f'c{n:03d}_{CRITICOS[n]}.jpg')
    hoja_rango(f36, 186, 200, EVID / 'hoja_master_c186-c200_vuelve_el_color.jpg', ancho=216, cols=15)
    hoja_rango(f36, 236, 246, EVID / 'hoja_master_c236-c246_flash_esto.jpg', ancho=216, cols=11)
    hoja_rango(f36, 315, 340, EVID / 'hoja_master_c315-c340_barrido_y_placa.jpg', ancho=200, cols=13)
    if V02:     # los dos planos nuevos, cuadro a cuadro, con los cortes de entrada y salida
        hoja_rango(f36, 48, 86, EVID / 'hoja_master_c48-c86_paso2_y_cortes.jpg', ancho=200, cols=13)
        hoja_rango(f36, 315, 392, EVID / 'hoja_master_c315-c392_paso10_cada_cuadro.jpg', ancho=160, cols=13)
    # ---- 3 · cara de 7884 (condición 1) y cabeza de 7885: hojas de la fuente cuadro a cuadro + el máster cuadro a cuadro
    for f_ in ('7884_c0-c89_c1.jpg', '7884_cabeza_c0-c29_c1.jpg', '7884_cabeza_c30-c59_c1.jpg', '7884_cabeza_c60-c89_c1.jpg',
               '7884_cara_detalle_1a1.jpg', '7884_c84-c156_c3.jpg', '7885_c0-c59_c1.jpg', '7885_cabeza_c0-c59_c1.jpg'):
        shutil.copy2(HJ / f_, VAL / f'1_fuente_{f_}')
    hoja_rango(f36, 141, 239, VAL / '1_cara_master_c141-c239_mitad_derecha_cada_cuadro.jpg', ancho=216, cols=11,
               recorte=(432, 400, 648, 1200))
    hoja_rango(f36, 0, 53, VAL / '1_cabeza_7885_master_c0-c53_cada_cuadro.jpg', ancho=200, cols=11, recorte=(300, 300, 780, 900))
    hoja_rango(f36, 279, 320, VAL / '1_cabeza_7885_master_c279-c320_cada_cuadro.jpg', ancho=200, cols=11, recorte=(300, 300, 780, 900))
    # ---- 4 · lugar de la foto (condición 2)
    for f_ in sorted((MED / 'lugar').glob('lugar_foto_vs_*.jpg')) + [MED / 'lugar' / 'mascaras_foto.jpg', MED / 'lugar' / 'lugar.json']:
        shutil.copy2(f_, VAL / f'2_{f_.name}')
    # ---- 5 · pasada por cuadro (máster 36 + base + .ass): croma, textos, todo lo demás igual a la base
    ass36 = TX / f'v3_textos_{REVISION}.ass'
    filas = pasada_cuadros(f36, BASE, ass36)
    grafico_croma(filas, EVID / 'saturacion_por_cuadro_c0-c392.png')
    grafico_croma(filas, EVID / 'saturacion_por_cuadro_c0-c210.png', n1=210)
    gris = [f for f in filas if f['cuadro'] <= GRIS_HASTA]
    pleno = [f for f in filas if 196 <= f['cuadro'] <= 210]
    sat = dict(
        criterio=('módulo de croma (|Cb−128|, |Cr−128|) en niveles de 8 bits, en todo el cuadro salvo la caja del texto '
                  f'(+16 px) y, desde c{OV_DEGRADE[0]}, salvo y < {Y_PLACA} (degradé de la placa). Gris = Cb = Cr = 128 en la base (exacto) y '
                  '≈ 128 en el máster (H.264 crf 17).'),
        gris_c0_c191=dict(media_max=max(f['croma_master_fuera']['media'] for f in gris),
                          p99_max=max(f['croma_master_fuera']['p99'] for f in gris),
                          max_max=max(f['croma_master_fuera']['max'] for f in gris),
                          pct_mayor_4_max=max(f['croma_master_fuera']['pct_mayor_4'] for f in gris),
                          base_max=max(f['croma_base_fuera']['max'] for f in gris)),
        rampa={f['cuadro']: f['croma_master_fuera'] for f in filas if 190 <= f['cuadro'] <= 197},
        pleno_c196_c210=dict(media_min=min(f['croma_master_fuera']['media'] for f in pleno),
                             p99_min=min(f['croma_master_fuera']['p99'] for f in pleno)),
        dentro_de_textos_c0_c191=dict(
            tambien_c108_c140_max=max(f['croma_master_texto']['max'] for f in filas if 108 <= f['cuadro'] <= 140),
            otros_textos_max=max(f['croma_master_texto']['max'] for f in gris if f['croma_master_texto'] and not 108 <= f['cuadro'] <= 140)))
    rep['saturacion'] = sat
    print('saturación', json.dumps(sat, ensure_ascii=False)[:800], flush=True)
    # textos: identidad por cuadro (caja renderizada = caja de referencia del texto que corresponde) y presencia en el máster
    ref = json.load(open(TX / 'anclas.json'))['cajas_36']
    tx = []
    for t in textos(REVISION):
        n0, n1 = t['c']; malos = []; pres = []
        for n in range(n0, n1 + 1):
            c = filas[n]['texto_caja']; r_ = ref[t['id']]
            if t['pop'] and n < n0 + 3:
                ok = c is not None and c[0] <= r_[0] + 2 and c[2] >= r_[2] - 2      # pop 118 % → 100 % en 90 ms: contiene la caja final
            else:
                ok = c is not None and max(abs(a - b) for a, b in zip(c, r_)) <= 3
            if not ok:
                malos.append((n, c))
            pres.append(filas[n]['luma_dif_dentro_texto'])
        tx.append(dict(id=t['id'], texto=texto_plano(t), cuadros=f'c{n0}–c{n1}', segundos=f'{n0 / FPS:.2f}–{(n1 + 1) / FPS:.2f}',
                       caja_ref=ref[t['id']], cuadros_que_no_coinciden=malos,
                       luma_dif_master_vs_base_dentro_min=min(pres)))
    sin_texto = [f['cuadro'] for f in filas if f['texto_caja'] is None]
    fuera = [f['luma_dif_fuera'] for f in filas]
    rep['textos'] = dict(por_texto=tx, cuadros_sin_texto_ass=f"c{min(sin_texto)}–c{max(sin_texto)} ({len(sin_texto)})",
                         todo_lo_demas_igual_a_la_base=dict(luma_dif_media_max=max(fuera),
                                                            cuadro=int(np.argmax(fuera)),
                                                            p999_max=max(f['luma_dif_fuera_p999'] for f in filas)))
    print('textos', [(x['id'], len(x['cuadros_que_no_coinciden']), x['luma_dif_master_vs_base_dentro_min']) for x in tx], flush=True)
    # grafía exacta: lo que dice cada .ass contra textos(N)
    import re
    graf = {}
    for N in NUMEROS:
        dl = [l.split(',', 9)[9] for l in (TX / f'v3_textos_{N}.ass').read_text(encoding='utf-8').splitlines() if l.startswith('Dialogue:')]
        limpio = [re.sub(r'\{[^}]*\}', '', x) for x in dl]
        esperado = [re.sub(r'\{[^}]*\}', '', t['txt']) for t in textos(N)]
        graf[N] = dict(en_pantalla=[x.replace('\\N', ' ⏎ ') for x in limpio], igual_al_guion=(limpio == esperado))
    rep['textos']['grafia_por_numero'] = graf
    placa, rep['placa'] = placa_por_cuadro(f36)
    print('placa', rep['placa']['frase_cuadros'], rep['placa']['firma_cuadros'], rep['placa']['frase_ok'], rep['placa']['firma_ok'], flush=True)
    # ---- 6 · números: cada máster contra el 36 (solo deben cambiar c0–c23 y c141–c167, en la zona de textos)
    if len(solo) == len(NUMEROS):          # v02: va en control_variantes, cuando están los cinco
        rep['numeros'] = comparar_numeros()
        tira_numeros(EVID / 'numeros_37-33_c10_c150.jpg')
    # ---- 7 · prenda: estampados contra textos y placa; márgenes del estampado en los pasos 8 y 10; remera en los bordes
    pj = json.load(open(PL / 'placa.json'))
    zonas_placa = dict(frase_letras=pj['frase_letras_bbox'], firma=pj['firma_bbox_opaco'],
                       degrade_hasta_y=(pj['degrade']['ultima_fila_alfa_mayor_0'] if V02 else pj['cierre_frase.png']['bbox_alfa_mayor_8'][3]))
    dec = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(BASE0), '-f', 'rawvideo',
                                 '-pix_fmt', 'rgb24', '-']), stdout=subprocess.PIPE)
    prenda = []; vis = []
    VIS = {0, 40, 60, 120, 150, 180, 200, 245, 270, 290, 330, 392}
    for n in range(NF):
        rgb8 = np.frombuffer(dec.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3)
        if n in BARRIDO:
            prenda.append(dict(cuadro=n, nota='barrido (desenfoque): sin medición')); continue
        pid = plano_de(n); cb, cn = CAJAS_PRENDA[pid]
        rgb = rgb8.astype(np.float32)
        fill, est, bb, fb = estampado_blanca(rgb, cb)
        mneg, nb = estampado_negra(rgb, cn) if cn else (None, None)
        # tela de la remera que toca el borde izquierdo (filas en x = 0, sobre la tela clara crecida desde la remera)
        filas_x0 = None
        if fill is not None:
            from scipy import ndimage as nd
            Lr, sr_ = _ls(rgb)
            m = (Lr > 140) & (sr_ < 0.35) & nd.binary_dilation(fill, iterations=12)
            lab, k = nd.label(m)
            if k:
                s_ = nd.sum(m, lab, range(1, k + 1)); m = lab == (1 + int(np.argmax(s_)))
                filas_x0 = int(m[:, 0].sum()); fb = L2._caja(m)
        tc = filas[n]['texto_caja']
        cajas_txt = ([('texto', tc)] if tc else []) + ([('frase', zonas_placa['frase_letras']), ('firma', zonas_placa['firma'])]
                                                       if n >= OV_FIRMA[0] else ([('frase', zonas_placa['frase_letras'])] if n >= OV_FRASE[0] else []))
        def sep(e):
            if e is None or not cajas_txt:
                return None
            return min(e[1] - c[3] for _, c in cajas_txt)          # > 0: el estampado empieza debajo del texto
        def cruza(e):
            return bool(e and any(not (c[2] < e[0] or c[0] > e[2] or c[3] < e[1] or c[1] > e[3]) for _, c in cajas_txt))
        prenda.append(dict(cuadro=n, plano=pid, blanca_estampado=bb, blanca_remera=fb, remera_filas_en_x0=filas_x0,
                           negra_estampado=nb, textos=cajas_txt,
                           sep_texto_estampado_blanca=sep(bb), sep_texto_estampado_negra=sep(nb),
                           texto_cruza_estampado=cruza(bb) or cruza(nb),
                           margenes_estampado_blanca=None if bb is None else dict(izq=bb[0], der=W - 1 - bb[2], arr=bb[1], abj=H - 1 - bb[3]),
                           margenes_remera=None if fb is None else dict(izq=fb[0], der=W - 1 - fb[2], arr=fb[1], abj=H - 1 - fb[3])))
        if n in VIS:
            ov = rgb8.copy()
            if fill is not None:
                ov[fill] = (0.65 * ov[fill] + 0.35 * np.array([0, 255, 0])).astype(np.uint8)
            if est is not None:
                ov[est] = [255, 0, 0]
            if mneg is not None:
                ov[mneg] = [0, 255, 255]
            im = Image.fromarray(ov); d = ImageDraw.Draw(im)
            for nom_, c in cajas_txt:
                d.rectangle(c, outline=(255, 255, 0), width=5)
            if n >= OV_DEGRADE[0]:
                d.line([0, zonas_placa['degrade_hasta_y'], W, zonas_placa['degrade_hasta_y']], fill=(255, 255, 0), width=2)
            for e in (bb, nb):
                if e:
                    d.rectangle(e, outline=(255, 0, 255), width=4)
            vis.append((np.asarray(im), f'c{n} p{pid} sep {prenda[-1]["sep_texto_estampado_blanca"]}'))
    dec.stdout.close(); dec.wait()
    L2.tira([v[0] for v in vis[:6]], [v[1] for v in vis[:6]], VAL / '3_estampados_vs_textos_a.jpg', ancho=360)
    L2.tira([v[0] for v in vis[6:]], [v[1] for v in vis[6:]], VAL / '3_estampados_vs_textos_b.jpg', ancho=360)
    med = [p for p in prenda if 'plano' in p]
    def resumen_plano(ids):
        ps = [p for p in med if p['plano'] in ids]
        sb = [p['sep_texto_estampado_blanca'] for p in ps if p['sep_texto_estampado_blanca'] is not None]
        sn = [p['sep_texto_estampado_negra'] for p in ps if p['sep_texto_estampado_negra'] is not None]
        mb = [p['margenes_estampado_blanca'] for p in ps if p['margenes_estampado_blanca']]
        mr = [p['margenes_remera'] for p in ps if p['margenes_remera']]
        x0 = [p['cuadro'] for p in ps if p['remera_filas_en_x0']]
        return dict(cuadros=f"c{ps[0]['cuadro']}–c{ps[-1]['cuadro']}" if ps else None, medidos=len(ps),
                    estampado_blanca_detectado=sum(1 for p in ps if p['blanca_estampado']),
                    sep_min_texto_estampado_blanca=min(sb) if sb else None,
                    sep_min_texto_estampado_negra=min(sn) if sn else None,
                    algun_texto_cruza_un_estampado=any(p['texto_cruza_estampado'] for p in ps),
                    margen_min_estampado_blanca={k: min(m[k] for m in mb) for k in ('izq', 'der', 'arr', 'abj')} if mb else None,
                    margen_min_remera_blanca={k: min(m[k] for m in mr) for k in ('izq', 'der', 'arr', 'abj')} if mr else None,
                    cuadros_con_la_remera_en_el_borde_izq=(f'{len(x0)} cuadros: c{min(x0)}–c{max(x0)}' if x0 else 'ninguno'),
                    remera_filas_en_x0_max=max((p['remera_filas_en_x0'] or 0) for p in ps) if ps else None)
    rep['prenda'] = {f'paso {p["id"]}': resumen_plano({p['id']}) for p in PLANOS}
    p8 = [p for p in med if p['plano'] == '08']
    rep['prenda']['esto_contra_remera_foto'] = dict(
        caja_esto=ref['esto'], borde_sup_remera_min=min(p['blanca_remera'][1] for p in p8),
        borde_sup_estampado_min=min(p['blanca_estampado'][1] for p in p8),
        sep_esto_remera_px=min(p['blanca_remera'][1] for p in p8) - ref['esto'][3],
        sep_esto_estampado_px=min(p['blanca_estampado'][1] for p in p8) - ref['esto'][3])
    p10 = [p for p in med if p['plano'] == '10' and p['cuadro'] >= OV_DEGRADE[0]]
    rep['prenda']['placa_contra_remera'] = dict(
        zonas_placa=zonas_placa, cuadros=f"c{p10[0]['cuadro']}–c{p10[-1]['cuadro']} ({len(p10)}, sin los del barrido)",
        borde_sup_remera_min=min(p['blanca_remera'][1] for p in p10),
        cuadro_borde_sup_min=min(p10, key=lambda p: p['blanca_remera'][1])['cuadro'],
        sep_firma_remera_px=min(p['blanca_remera'][1] for p in p10) - zonas_placa['firma'][3],
        sep_degrade_remera_px=min(p['blanca_remera'][1] for p in p10) - zonas_placa['degrade_hasta_y'],
        cuadros_con_el_degrade_sobre_la_remera=[p['cuadro'] for p in p10 if p['blanca_remera'][1] <= zonas_placa['degrade_hasta_y']])
    if V02:
        rep['margenes_v02'] = margenes_pasos_2_y_10(med)
        print('márgenes', json.dumps(rep['margenes_v02'], ensure_ascii=False)[:1500], flush=True)
    jdump(prenda, VAL / '3_prenda_por_cuadro.json')
    print('prenda', json.dumps(rep['prenda'], ensure_ascii=False)[:3000], flush=True)
    # ---- 7b · blanco de la Blanca por toma contra PRODUCTO (V3 no neutraliza: se mide y se informa)
    rep['color_blanca'] = color_blanca(f36)
    print('color', json.dumps(rep['color_blanca']['tela_entera_mitad_clara'], ensure_ascii=False), flush=True)
    # ---- 8 · continuidad: diferencia media entre cuadros consecutivos (congelados, saltos)
    a = U.leer(f36, 270, 480).astype(np.float32)
    dif = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2, 3))
    rep['diferencia_consecutiva'] = [round(float(x), 2) for x in dif]
    rep['cuadros_casi_iguales_al_anterior'] = [(i + 1, round(float(x), 2)) for i, x in enumerate(dif) if x < 0.6]
    L2.tira([a.astype(np.uint8)[n] for n in (0, 60, 108, 150, 200, 260, 300, 360)], ['c0', 'c60', 'c108', 'c150', 'c200', 'c260', 'c300', 'c360'],
            EVID / 'ancho_telefono_360px.jpg', ancho=270)
    # ---- 10 · v02: PSNR contra v01 fuera de los pasos 2 y 10, y contraste del trazo de la placa por cuadro
    if V02:
        rep['empalme'] = {N: json.load(open(MAS / f'empalme_{N}.json')) for N in solo}
        for N in solo:
            shutil.copy2(MAS / f'empalme_{N}.json', EVID / f'empalme_{N}.json')
        ps = psnr_contra(f36, T / 'master' / nombre(REVISION, 'completa', 'v01'), EVID / f'psnr_{REVISION}_v02_contra_v01.log')
        rep['psnr_contra_v01'] = psnr_resumen(ps)
        jdump(ps, EVID / f'psnr_por_cuadro_{REVISION}_v02_contra_v01.json')
        print('psnr', rep['psnr_contra_v01'], flush=True)
        cres, cfilas = contraste_placa(f36, MAS / 'ref_sin_texto_36.mp4', EVID / f'contraste_peor_cuadro_{REVISION}.jpg')
        rep['contraste_placa'] = cres
        jdump(cfilas, EVID / f'contraste_por_cuadro_{REVISION}.json')
        print('contraste', {k: v for k, v in cres.items() if k != 'criterio'}, flush=True)
    # ---- 9 · copias de insumos
    for f_ in (TV / 'planos.json', MEDV / 'color.json', TX / 'anclas.json', A / 'audio.json', MED / '4627_borde_izq.json'):
        shutil.copy2(f_, EVID / f_.name)
    if V02:
        shutil.copy2(MED / '4627_margenes_completo.json', EVID / '4627_margenes_por_cuadro_fuente.json')
        for f_ in sorted((TV / 'hojas').glob('4627_*.jpg')):
            shutil.copy2(f_, EVID / f'hoja_fuente_{f_.name}')
    for N in NUMEROS:
        shutil.copy2(TX / f'v3_textos_{N}.ass', EVID / f'v3_textos_{N}.ass')
    for k in ('completa', 'sinmusica'):
        shutil.copy2(A / f'v3_{k}_eventos.json', EVID / f'audio_eventos_{k}.json')
    for f_ in ('cierre_frase.png', 'cierre_firma.png', 'placa.json') + (('cierre_degrade.png', 'mascara_frase.png', 'mascara_firma.png') if V02 else ()):
        shutil.copy2(PL / f_, EVID / f'placa_{f_}')
    for f_ in ('4627_c180-c207_c1.jpg', '4627_c0-c72_c3.jpg', '4627_c255-c405_c6.jpg', '7896_c0-c81_c3.jpg'):
        if V02 and f_.startswith('4627_c'):
            continue                                  # tramos de v01 que ya no se usan
        shutil.copy2(HJ / f_, EVID / f'hoja_fuente_{f_}')
    jdump(dict(por_cuadro=filas), EVID / 'pasada_por_cuadro_36.json')
    jdump(placa, EVID / 'placa_por_cuadro_36.json')
    jdump(rep, EVID / 'control.json')
    if V02:
        jdump(rep['margenes_v02'], EVID / 'margenes_pasos_2_y_10_por_cuadro.json')
    print('listo', {k: v['sonoridad'] for k, v in rep['archivos'].items()}, 'casi iguales', rep['cuadros_casi_iguales_al_anterior'])




def tramos_txt(cuadros):
    """[321, 322, 323, 327] → 'c321–c323 (10,700–10,800 s), c327 (10,900 s)' (segundos del máster, inicio del cuadro)."""
    out, ini = [], None
    for i, n in enumerate(sorted(cuadros)):
        if ini is None:
            ini = n
        if i + 1 == len(cuadros) or sorted(cuadros)[i + 1] != n + 1:
            out.append(f'c{ini}–c{n} ({ini / FPS:.3f}–{(n + 1) / FPS:.3f} s)'.replace('.', ',') if n > ini
                       else f'c{n} ({n / FPS:.3f}–{(n + 1) / FPS:.3f} s)'.replace('.', ','))
            ini = None
    return ', '.join(out) if out else 'ninguno'


def margenes_pasos_2_y_10(med):
    """remera entera con ≥ 20 px de margen en cada cuadro de los pasos 2 y 10 (condición de Roma para v02).
    Remera = tela clara crecida desde la remera detectada (dilatación 12 px, la mayor componente), sobre v3_base0 (color,
    misma geometría que el máster); margen = distancia de su caja a cada borde del cuadro 1080×1920. Los 3 cuadros del
    barrido (c321–c323, desenfoque horizontal de 110/48/16 px) no se miden en el máster: se informan con la misma medición
    sobre la fuente sin desenfoque (med/4627_margenes_completo.json, 4627 decodificada con la misma cadena de color; el
    plano usa la toma nativa 1080×1920 sin recorte, así que las coordenadas son las mismas)."""
    fuente = {r['n']: r for r in json.load(open(MED / '4627_margenes_completo.json'))}
    fino = {r['n']: r for r in json.load(open(MED / '4627_margenes_fino.json'))}
    out = dict(criterio=margenes_pasos_2_y_10.__doc__, criterio_fino=MARGEN_FINO_DOC)
    for pid in ('02', '10'):
        pl = [p for p in PLANOS if p['id'] == pid][0]
        filas = []
        for n in range(pl['m0'], pl['m0'] + pl['nf']):
            src = pl['n0'] + n - pl['m0']
            p = next((q for q in med if q['cuadro'] == n), None)
            fs = fuente[src]
            if p and p.get('margenes_remera'):
                mr = p['margenes_remera']; x0 = p['remera_filas_en_x0']; origen = 'máster (base0)'
            else:
                mr = fs['margen']; x0 = fs['filas_x0']; origen = 'fuente (barrido)'
            ff = fino[src]
            filas.append(dict(cuadro=n, t=round(n / FPS, 3), fuente=f'4627 c{src}', origen=origen, margen=mr,
                              minimo=min(mr.values()), lado=min(mr, key=mr.get), filas_en_x0=x0,
                              fuente_margen_min=min(fs['margen'].values()),
                              margen_fino=ff['margen_fino'], minimo_fino=min(ff['margen_fino'].values()),
                              filas_en_x0_fino=ff['filas_x0_fino']))
        bajo = [f['cuadro'] for f in filas if f['minimo'] < 20]
        tocan = [f['cuadro'] for f in filas if f['minimo'] <= 0 or (f['filas_en_x0'] or 0) > 0]
        bajo_f = [f['cuadro'] for f in filas if f['minimo_fino'] < 20]
        tocan_f = [f['cuadro'] for f in filas if f['minimo_fino'] <= 0 or f['filas_en_x0_fino'] > 0]
        peor = min(filas, key=lambda f: f['minimo']); peor_f = min(filas, key=lambda f: f['minimo_fino'])
        out[f'paso_{pid}'] = dict(cuadros=f"c{pl['m0']}–c{pl['m0'] + pl['nf'] - 1}",
                                  fuente=f"4627 c{pl['n0']}–c{pl['n0'] + pl['nf'] - 1} ({pl['n0'] / FPS:.3f}–{(pl['n0'] + pl['nf']) / FPS:.3f} s)",
                                  margen_min=peor['minimo'], cuadro_min=peor['cuadro'], lado_min=peor['lado'],
                                  cuadros_bajo_20=bajo, cuadros_bajo_20_txt=tramos_txt(bajo),
                                  cuadros_que_tocan_el_borde=tocan, cuadros_que_tocan_el_borde_txt=tramos_txt(tocan),
                                  cumple=not bajo,
                                  fino=dict(margen_min=peor_f['minimo_fino'], cuadro_min=peor_f['cuadro'],
                                            cuadros_bajo_20=bajo_f, cuadros_bajo_20_txt=tramos_txt(bajo_f),
                                            cuadros_que_tocan_el_borde=tocan_f, cumple=not bajo_f),
                                  por_cuadro=filas)
    out['cumplen_los_dos'] = out['paso_02']['cumple'] and out['paso_10']['cumple']
    out['cumplen_los_dos_fino'] = out['paso_02']['fino']['cumple'] and out['paso_10']['fino']['cumple']
    return out


MARGEN_FINO_DOC = ('margen fino: tela blanca estricta (L > 180, saturación < 0,22) dentro de la remera detectada dilatada '
                   '4 px, la mayor componente, sobre 4627 decodificada con la cadena de color del plano (misma geometría). '
                   'La máscara crecida 12 px (método de v01) es más conservadora: en c330–c336 de la fuente suma roca clara '
                   'pegada a la punta de la manga y llega a x = 0, cuando a tamaño real la manga queda a 4 px del borde '
                   '(hoja v02/hojas/manga_izq_paso10_1a1.jpg).')


def etapa_margenes4627():
    """márgenes de la remera en todos los cuadros de 4627 (decodificada con la cadena de color del plano): máscara crecida
    12 px (med/4627_margenes_completo.json, método de v01) y fina (med/4627_margenes_fino.json, ver MARGEN_FINO_DOC)."""
    from scipy import ndimage as nd
    p = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(V._src('IMG_4627')), '-vf',
                               V.color('IMG_4627') + ',scale=1080:1920:flags=area,format=rgb24', '-f', 'rawvideo', '-']),
                         stdout=subprocess.PIPE)
    crec, fino, n = [], [], 0
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        rgb = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32)
        fill, est, bb, fb = estampado_blanca(rgb, (0, 450, 1080, 1920))
        r = dict(n=n, t=round(n / FPS, 3))
        if fill is not None:
            L, s_ = _ls(rgb)
            for umbral, dil, lista in (((L > 140) & (s_ < 0.35), 12, crec), ((L > 180) & (s_ < 0.22), 4, fino)):
                m = umbral & nd.binary_dilation(fill, iterations=dil)
                lab, k = nd.label(m); ss = nd.sum(m, lab, range(1, k + 1)); m = lab == (1 + int(np.argmax(ss)))
                c = L2._caja(m)
                mg = dict(izq=c[0], der=W - 1 - c[2], arr=c[1], abj=H - 1 - c[3])
                if dil == 12:
                    lista.append(dict(r, remera=c, margen=mg, filas_x0=int(m[:, 0].sum()), filas_x1=int(m[:, -1].sum()), estampado=bb))
                else:
                    lista.append(dict(r, remera_fina=c, margen_fino=mg, filas_x0_fino=int(m[:, 0].sum()), relleno=fb))
        else:
            crec.append(r); fino.append(r)
        n += 1
    p.wait()
    json.dump(crec, open(MED / '4627_margenes_completo.json', 'w'))
    json.dump(fino, open(MED / '4627_margenes_fino.json', 'w'))
    print('4627', n, 'cuadros')


def etapa_margenes_v02():
    """rehace solo el resumen de márgenes de los pasos 2 y 10 (desde validaciones/3_prenda_por_cuadro.json) y lo
    actualiza en evidencia_v02/control.json."""
    rep = json.load(open(EVID / 'control.json'))
    med = [p for p in json.load(open(EVID / 'validaciones' / '3_prenda_por_cuadro.json')) if 'plano' in p]
    rep['margenes_v02'] = margenes_pasos_2_y_10(med)
    jdump(rep, EVID / 'control.json')
    jdump(rep['margenes_v02'], EVID / 'margenes_pasos_2_y_10_por_cuadro.json')
    shutil.copy2(MED / '4627_margenes_fino.json', EVID / '4627_margenes_fino_por_cuadro_fuente.json')
    for f_ in ('manga_izq_paso10_1a1.jpg', 'mascara_remera_paso10.jpg', 'borde_izq_paso10_c375-c392_1a1.jpg'):
        shutil.copy2(TV / 'hojas' / f_, EVID / 'validaciones' / f'4_{f_}')
    m = rep['margenes_v02']
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'por_cuadro'} if isinstance(v, dict) else v
                      for k, v in m.items() if k.startswith('paso') or k.startswith('cumplen')}, ensure_ascii=False))


def placa_por_cuadro(f36):
    """placa cuadro a cuadro (método V2): en cada zona, el máster contra la base sin la capa y con la capa compuesta
    (alfa); la capa está si el error con ella es menor. v01: frase (con el degradé) y firma. v02: degradé (y 0–280),
    frase (su caja) y firma, cada una sobre lo que tiene debajo (base, o base + degradé si el degradé está)."""
    from PIL import Image
    pj = json.load(open(PL / 'placa.json'))
    pf = np.asarray(Image.open(PL / 'cierre_frase.png')).astype(np.float32)
    pg = np.asarray(Image.open(PL / 'cierre_firma.png')).astype(np.float32)
    pd = np.asarray(Image.open(PL / 'cierre_degrade.png')).astype(np.float32) if V02 else None
    comp = lambda b, p: b * (1 - p[..., 3:] / 255) + p[..., :3] * (p[..., 3:] / 255)
    fx0, fy0, fx1, fy1 = pj['firma_bbox_opaco']
    qx0, qy0, qx1, qy1 = pj['cierre_frase.png']['bbox_alfa_mayor_8']
    placa = []
    c_ini = 315 if V02 else 321
    for c0 in range(c_ini, NF, 26):
        c1 = min(c0 + 25, NF - 1)
        mm = U.leer(f36, W, H, n0=c0, n1=c1); bs = U.leer(BASE, W, H, n0=c0, n1=c1)
        for i in range(len(mm)):
            m_ = mm[i].astype(np.float32); b_ = bs[i].astype(np.float32)
            fila = dict(cuadro=c0 + i)
            if V02:
                e_de = [float(np.abs(m_[:280] - x).mean()) for x in (b_[:280], comp(b_[:280], pd[:280]))]
                deg = e_de[1] < e_de[0]
                bd = comp(b_[:720], pd[:720]) if deg else b_[:720]
                zb = bd[qy0:qy1 + 1, qx0:qx1 + 1]; zm = m_[qy0:qy1 + 1, qx0:qx1 + 1]
                e_fr = [float(np.abs(zm - zb).mean()), float(np.abs(zm - comp(zb, pf[qy0:qy1 + 1, qx0:qx1 + 1])).mean())]
                zb = bd[fy0:fy1 + 1, fx0:fx1 + 1]
                fila.update(degrade=bool(deg), err_degrade=[round(x, 2) for x in e_de])
            else:
                e_fr = [float(np.abs(m_[:280] - x).mean()) for x in (b_[:280], comp(b_[:280], pf[:280]))]
                zb = b_[fy0:fy1 + 1, fx0:fx1 + 1]
            zf = comp(zb, pf[fy0:fy1 + 1, fx0:fx1 + 1])
            zg = comp(zf, pg[fy0:fy1 + 1, fx0:fx1 + 1]); zm = m_[fy0:fy1 + 1, fx0:fx1 + 1]
            e_fi = [float(np.abs(zm - zf).mean()), float(np.abs(zm - zg).mean())]
            fila.update(frase=bool(e_fr[1] < e_fr[0]), firma=bool(e_fi[1] < e_fi[0]),
                        err_frase=[round(x, 2) for x in e_fr], err_firma=[round(x, 2) for x in e_fi])
            placa.append(fila)
    on = lambda k: [f['cuadro'] for f in placa if f.get(k)]
    rng = lambda c: f'c{min(c)}–c{max(c)} ({len(c)})' if c else 'ninguno'
    fr_on, fi_on = on('frase'), on('firma')
    r = dict(frase_cuadros=rng(fr_on), firma_cuadros=rng(fi_on),
             frase_ok=fr_on == list(range(OV_FRASE[0], NF)), firma_ok=fi_on == list(range(OV_FIRMA[0], NF)),
             texto_exacto=dict(frase=FRASE_TXT, firma=FIRMA_TXT), placa_json=pj)
    if V02:
        de_on = on('degrade')
        r.update(degrade_cuadros=rng(de_on), degrade_ok=de_on == list(range(OV_DEGRADE[0], NF)),
                 revisados=f'c{c_ini}–c{NF - 1}')
    return placa, r


def contraste_placa(master, ref, salida_img=None):
    """contraste del trazo de la placa por cuadro (c327–c392; firma desde c333), condición de Roma para v02.
    Lt = luminancia relativa (WCAG 2: sRGB → lineal, 0,2126 R + 0,7152 G + 0,0722 B) del píxel del máster decodificado;
    Lb = la del mismo píxel en «el mismo cuadro sin texto» (ref: la base con el degradé solo, codificada igual que el
    máster). Contraste = (máx + 0,05) / (mín + 0,05). Trazo = máscara de las letras sin sombra con alfa ≥ 128: frase entera
    y solo las letras de «ROCCÉ LIFE» (sin la ficha del logo). Pasa el cuadro si ≥ 95 % del trazo llega a 3:1."""
    from PIL import Image, ImageDraw
    mf = np.asarray(Image.open(PL / 'mascara_frase.png'))[..., 3] >= 128
    mg = np.asarray(Image.open(PL / 'mascara_firma.png'))[..., 3] >= 128
    lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    Y0, Y1 = 280, 600
    filas = []; peor = None
    for c0 in range(OV_FRASE[0], NF, 22):
        c1 = min(c0 + 21, NF - 1)
        mm = U.leer(master, W, H, n0=c0, n1=c1)[:, Y0:Y1].astype(np.float64) / 255
        rr = U.leer(ref, W, H, n0=c0, n1=c1)[:, Y0:Y1].astype(np.float64) / 255
        for i in range(len(mm)):
            n = c0 + i
            Lt = lin(mm[i]) @ KY.astype(np.float64); Lb = lin(rr[i]) @ KY.astype(np.float64)
            cr = (np.maximum(Lt, Lb) + 0.05) / (np.minimum(Lt, Lb) + 0.05)
            fila = dict(cuadro=n, t=round(n / FPS, 3))
            for nom, m_ in (('frase', mf[Y0:Y1]), ('firma', mg[Y0:Y1])):
                if nom == 'firma' and n < OV_FIRMA[0]:
                    continue
                c = cr[m_]
                fila[nom] = dict(pixeles=int(m_.sum()), pct_3a1=round(float((c >= 3).mean() * 100), 2),
                                 pct_4_5a1=round(float((c >= 4.5).mean() * 100), 2), p5=round(float(np.percentile(c, 5)), 2),
                                 mediana=round(float(np.median(c)), 2), min=round(float(c.min()), 2),
                                 fondo_Lb_p95=round(float(np.percentile(Lb[m_], 95)), 3))
            fila['pasa'] = all(fila[k]['pct_3a1'] >= 95 for k in ('frase', 'firma') if k in fila)
            filas.append(fila)
            score = min(fila[k]['pct_3a1'] for k in ('frase', 'firma') if k in fila)
            if peor is None or score < peor[0]:
                peor = (score, n, cr.copy(), mm[i].copy())
    if salida_img and peor:
        score, n, cr, img = peor
        vis = (img * 255).astype(np.uint8).copy()
        malo = (cr < 3) & (mf[Y0:Y1] | (mg[Y0:Y1] if n >= OV_FIRMA[0] else False))
        vis[malo] = [255, 0, 0]
        im = Image.fromarray(vis[:, 200:880]); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 520, 30], fill=(0, 0, 0))
        d.text((6, 6), f'c{n} peor cuadro: {score:.2f} % del trazo >= 3:1 (rojo = trazo < 3:1)', fill=(255, 255, 0))
        im.save(salida_img, quality=92)
    resumen = dict(criterio=contraste_placa.__doc__, cuadros=f'c{OV_FRASE[0]}–c{NF - 1}', medidos=len(filas),
                   cuadros_que_no_pasan=[f['cuadro'] for f in filas if not f['pasa']],
                   frase_pct_3a1_min=min(f['frase']['pct_3a1'] for f in filas),
                   frase_cuadro_min=min(filas, key=lambda f: f['frase']['pct_3a1'])['cuadro'],
                   firma_pct_3a1_min=min(f['firma']['pct_3a1'] for f in filas if 'firma' in f),
                   firma_cuadro_min=min((f for f in filas if 'firma' in f), key=lambda f: f['firma']['pct_3a1'])['cuadro'],
                   frase_p5_min=min(f['frase']['p5'] for f in filas),
                   firma_p5_min=min(f['firma']['p5'] for f in filas if 'firma' in f))
    return resumen, filas


def psnr_contra(a, b, salida_log):
    """PSNR por cuadro (filtro psnr de FFmpeg, 8 bits, Y y promedio de Y/U/V ponderado por tamaño) del archivo a contra b."""
    U.run(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(a), '-i', str(b), '-lavfi',
                f'[0:v][1:v]psnr=stats_file={salida_log}', '-f', 'null', '-']))
    out = []
    for l in Path(salida_log).read_text().splitlines():
        d = dict(kv.split(':', 1) for kv in l.split() if ':' in kv)
        v = lambda k: float('inf') if d[k] == 'inf' else float(d[k])
        out.append(dict(cuadro=int(d['n']) - 1, psnr_y=v('psnr_y'), psnr_avg=v('psnr_avg')))
    return out


def psnr_resumen(filas):
    fuera = [f for f in filas if not (54 <= f['cuadro'] <= 80 or f['cuadro'] >= 321)]
    fin = lambda x: 99.0 if x == float('inf') else round(x, 2)
    peor = min(fuera, key=lambda f: f['psnr_avg'])
    return dict(criterio='fuera de los pasos 2 (c54–c80) y 10 (c321–c392): c0–c53 y c81–c320, PSNR ≥ 38 dB contra v01',
                cuadros=len(fuera), psnr_avg_min=fin(peor['psnr_avg']), cuadro_min=peor['cuadro'],
                psnr_y_min=fin(min(f['psnr_y'] for f in fuera)),
                psnr_avg_mediana=fin(float(np.median([min(f['psnr_avg'], 99) for f in fuera]))),
                cuadros_bajo_38=[f['cuadro'] for f in fuera if f['psnr_avg'] < 38 or f['psnr_y'] < 38],
                pasos_2_y_10_psnr_avg_mediana=fin(float(np.median([f['psnr_avg'] for f in filas if f not in fuera]))))


def cruces(A_, nums):
    c = dict(sinmusica_mismo_video_que_completa={N: A_[nombre(N, 'sinmusica')]['md5_video'] == A_[nombre(N, 'completa')]['md5_video']
                                                 for N in nums})
    if len(nums) > 1:
        c.update(audio_completa_identico_en_todos=len({A_[nombre(N, 'completa')]['md5_audio'] for N in nums}) == 1,
                 audio_sinmusica_identico_en_todos=len({A_[nombre(N, 'sinmusica')]['md5_audio'] for N in nums}) == 1,
                 videos_distintos_entre_numeros=len({A_[nombre(N, 'completa')]['md5_video'] for N in nums}) == len(nums))
    return c


def color_blanca(f36):
    """B − R y G − R de la tela lisa de la Blanca (remera detectada erosionada 10 px, sin el estampado dilatado 15 px,
    media del 50 % más claro) por toma, contra la Blanca de estudio de PRODUCTO/. Los pasos en gris se miden en
    v3_base0 (antes del gris). Guion: «4627 HDR→SDR, comparar blanco con PRODUCTO»."""
    from PIL import Image
    from scipy import ndimage as nd
    V.foto_srgb(R / 'PRODUCTO' / 'blanca_espalda_estudio.jpg', MED / 'blanca_espalda_estudio_srgb.png')
    prod = np.asarray(Image.open(MED / 'blanca_espalda_estudio_srgb.png').convert('RGB'))
    out = dict(metodo=color_blanca.__doc__, PRODUCTO_blanca_espalda_estudio=U.color_parche(prod, (292, 1316, 877, 1755)),
               tela_entera_mitad_clara={})
    b0 = BASE0
    for src, n, rot in ((b0, 10, '7885 paso 1 (antes del gris)'), (b0, 60, '4627 paso 2 (antes del gris)'),
                        (b0, 120, '7896 paso 4 (antes del gris)'), (b0, 150, '7884 paso 5 (antes del gris)'),
                        (f36, 210, '7884 paso 7'), (f36, 260, 'foto paso 8 (PRODUCTO, tal cual)'), (f36, 300, '7885 paso 9'),
                        (f36, 360, '4627 paso 10')):
        rgb = U.leer(src, W, H, n0=n, n1=n)[0].astype(np.float32)
        fill, est, bb, fb = estampado_blanca(rgb, CAJAS_PRENDA[plano_de(n)][0])
        m = nd.binary_erosion(fill, iterations=10)
        if est is not None:
            m &= ~nd.binary_dilation(est, iterations=15)
        p = rgb[m]; L = p @ KY; p = p[L >= np.percentile(L, 50)]; mu = p.mean(0)
        out['tela_entera_mitad_clara'][f'c{n} {rot}'] = dict(pixeles=int(len(p)), rgb=[round(float(x), 1) for x in mu],
                                                           b_menos_r=round(float(mu[2] - mu[0]), 1),
                                                           g_menos_r=round(float(mu[1] - mu[0]), 1))
    out['PRODUCTO_blanca_espalda_estudio'] = {k: (round(float(v), 3) if not isinstance(v, list) else [round(float(x), 1) for x in v])
                                              for k, v in out['PRODUCTO_blanca_espalda_estudio'].items()}
    return out


def comparar_numeros():
    """cada máster contra el 36, luma cuadro a cuadro: píxeles con |ΔY| > 60 dentro de la zona de textos (y 250–550,
    x 40–1040) y fuera de ella. Un cambio de cifra mueve miles de píxeles más de 60 niveles; el ruido de codificación
    (cada número es una codificación x264 aparte) no llega a 60. Primer criterio descartado (corrida del 25/11): la
    media de |ΔY| en la zona > 2 marcaba cuadros de espuma por ruido y no veía «35/33 días.» (cambia una sola cifra)."""
    num = {}
    esperado = list(range(0, 24)) + list(range(141, 168))
    z = np.zeros((H, W), bool); z[250:550, 40:1040] = True          # incluye el pop de 118 % del hook (x 71–1013 en c0)
    f36 = MAS / nombre(REVISION, 'completa')
    for N in NUMEROS:
        if N == REVISION:
            continue
        pa_ = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(MAS / nombre(N, 'completa')), '-f', 'rawvideo', '-pix_fmt', 'gray', '-']), stdout=subprocess.PIPE)
        pb_ = subprocess.Popen(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(f36), '-f', 'rawvideo', '-pix_fmt', 'gray', '-']), stdout=subprocess.PIPE)
        pz, pf, dmax = [], [], []
        for n in range(NF):
            a1 = np.frombuffer(pa_.stdout.read(W * H), np.uint8).reshape(H, W).astype(np.int16)
            a2 = np.frombuffer(pb_.stdout.read(W * H), np.uint8).reshape(H, W).astype(np.int16)
            d_ = np.abs(a1 - a2)
            pz.append(int((d_[z] > 60).sum())); pf.append(int((d_[~z] > 60).sum())); dmax.append(int(d_[~z].max()))
        for p in (pa_, pb_):
            p.stdout.close(); p.wait()
        cambian = [n for n, v in enumerate(pz) if v > 200]
        num[N] = dict(criterio='píxeles con |ΔY| > 60 en la zona de textos > 200', cuadros_con_cambio_en_textos=cambian,
                      esperado='c0–c23 y c141–c167', coincide=(cambian == esperado),
                      pixeles_cambiados_min_en_esos=min(pz[n] for n in esperado),
                      pixeles_cambiados_max_resto_de_cuadros_en_zona=max(v for n, v in enumerate(pz) if n not in esperado),
                      pixeles_mayor_60_fuera_de_la_zona_max=max(pf), dif_max_fuera_de_la_zona=max(dmax))
        print('número', N, num[N]['coincide'], num[N]['pixeles_cambiados_min_en_esos'],
              num[N]['pixeles_cambiados_max_resto_de_cuadros_en_zona'], num[N]['pixeles_mayor_60_fuera_de_la_zona_max'], flush=True)
    return num


def tira_numeros(salida):
    tiles, rot = [], []
    for N in NUMEROS:
        fr2 = U.leer(MAS / nombre(N, 'completa'), W, H, n0=10, n1=10)[0], U.leer(MAS / nombre(N, 'completa'), W, H, n0=150, n1=150)[0]
        tiles += [fr2[0][230:560], fr2[1][230:560]]; rot += [f'{N} · c10', f'{N} · c150']
    L2.tira(tiles, rot, salida, ancho=540)


def etapa_numeros():
    """rehace solo la comparación de números y la actualiza en evidencia_v01/control.json."""
    rep = json.load(open(EVID / 'control.json'))
    rep['numeros'] = comparar_numeros()
    jdump(rep, EVID / 'control.json')


# =====================================================================================================
# etapa control_variantes (v02)
# =====================================================================================================
def etapa_rompiente():
    """v02 · dónde cae la rompiente real del paso 10: envolvente de 4627 (fuente, mono) por bandas en ventanas de 20 ms,
    llevada al tiempo del máster (máster = 10,70 + fuente − 8,9333), junto con la envolvente de la pista ambiente de la
    mezcla y las marcas de la campana (12,50), el fundido de la música (12,60) y el del ambiente (AMB_FUNDIDO).
    Escribe evidencia_v02/rompiente_paso10.png y rompiente_paso10.json."""
    from scipy import signal
    from PIL import Image, ImageDraw, ImageFont
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(V._src('IMG_4627')), '-vn', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                       capture_output=True).stdout
    a = np.frombuffer(r, np.float32).astype(np.float64)
    env = lambda x, w=0.02: 20 * np.log10(np.sqrt((x[:len(x) // int(w * SR) * int(w * SR)].reshape(-1, int(w * SR)) ** 2).mean(1)) + 1e-9)
    hf = signal.sosfiltfilt(signal.butter(4, 1500, 'highpass', fs=SR, output='sos'), a)
    lf = signal.sosfiltfilt(signal.butter(4, 150, 'lowpass', fs=SR, output='sos'), a)
    Eh, El, E = env(hf), env(lf), env(a)
    t = np.arange(len(E)) * 0.02
    t0 = PLANOS[9]['n0'] / FPS
    m = (t >= t0) & (t <= t0 + 2.4)
    tm = 10.70 + t[m] - t0
    idx = np.nonzero((t >= t0 + 1.4) & (t <= t0 + 2.4))[0]
    pk = idx[np.argmax(Eh[idx])]
    d = np.convolve(np.diff(Eh), np.ones(3) / 3, 'same'); oi = idx[np.argmax(d[idx[:-1]])]
    res = dict(metodo=etapa_rompiente.__doc__, fuente_paso10=f'4627 {t0:.3f}–{t0 + 2.4:.3f} s',
               espuma_mayor_1_5kHz_max=dict(fuente_s=round(float(t[pk]), 2), master_s=round(float(10.70 + t[pk] - t0), 3),
                                             cuadro_master=int(round((10.70 + t[pk] - t0) * FPS)), dbfs=round(float(Eh[pk]), 1)),
               espuma_subida_mas_rapida=dict(fuente_s=round(float(t[oi]), 2), master_s=round(float(10.70 + t[oi] - t0), 3)),
               campana_s=12.50, fundido_musica_s=12.60, fundido_ambiente_s=AMB_FUNDIDO,
               envolvente_master=[dict(t=round(float(x), 2), hf=round(float(h), 1), lf=round(float(l), 1), total=round(float(e), 1))
                                  for x, h, l, e in zip(tm, Eh[m], El[m], E[m])])
    jdump(res, EVID / 'rompiente_paso10.json')
    Wd, Hd, ml, mb, mt = 1400, 520, 80, 60, 50
    im = Image.new('RGB', (Wd, Hd), (250, 250, 250)); dr = ImageDraw.Draw(im)
    fnt = ImageFont.truetype(FONT, 20); fch = ImageFont.truetype(FONT, 16)
    X_ = lambda x: ml + (Wd - ml - 30) * (x - 10.7) / 2.4
    Y_ = lambda v: mt + (Hd - mb - mt) * (-v) / 50
    for v in range(0, 51, 10):
        dr.line([ml, Y_(-v), Wd - 30, Y_(-v)], fill=(225, 225, 225)); dr.text((ml - 50, Y_(-v) - 9), f'-{v}', font=fch, fill=(90, 90, 90))
    for x, rot, col in ((12.50, 'campana 12,50', (60, 140, 60)), (12.60, 'fundido música 12,60', (120, 120, 120)),
                        (AMB_FUNDIDO, f'rompiente / fundido ambiente {AMB_FUNDIDO:.2f}'.replace('.', ','), (200, 60, 60))):
        dr.line([X_(x), mt, X_(x), Hd - mb], fill=col, width=2)
        ancho = dr.textlength(rot, font=fch)
        dr.text((X_(x) - ancho - 6, mt + {12.50: 0, 12.60: 20, AMB_FUNDIDO: 40}[x]), rot, font=fch, fill=col)
    for serie, col in ((Eh[m], (60, 110, 200)), (El[m], (150, 150, 150)), (E[m], (20, 20, 20))):
        dr.line([(X_(x), Y_(min(0, max(-50, v)))) for x, v in zip(tm, serie)], fill=col, width=2)
    for x in np.arange(10.7, 13.11, 0.3):
        dr.text((X_(x) - 14, Hd - mb + 8), f'{x:.1f}'.replace('.', ','), font=fch, fill=(90, 90, 90))
    dr.text((ml, 10), 'Paso 10 · audio de 4627 en tiempo de máster (dBFS, 20 ms) · azul = espuma > 1,5 kHz · gris = < 150 Hz · negro = total',
            font=fnt, fill=(20, 20, 20))
    im.save(EVID / 'rompiente_paso10.png')
    print(json.dumps({k: v for k, v in res.items() if k not in ('metodo', 'envolvente_master')}, ensure_ascii=False))


def etapa_control_variantes():
    """v02, después de entregar el 36: técnica de las otras 8 piezas, cruces de las 10, números contra el 36, empalme,
    PSNR contra su v01 y contraste de la placa de cada variante. Evidencia en evidencia_v02/variantes/ (no toca nada de lo
    ya entregado con el 36)."""
    ev = EVID / 'variantes'; ev.mkdir(parents=True, exist_ok=True)
    base = json.load(open(EVID / 'control.json'))
    otros = [N for N in NUMEROS if N != REVISION]
    rep = dict(fecha='2026-11-25', pieza=f'V3 «5 domingos» {VERSION} · variantes', numeros=otros, archivos={})
    for N in otros:
        for k in ('completa', 'sinmusica'):
            r, mom = tecnico(MAS / nombre(N, k), ev)
            rep['archivos'][r['archivo']] = r
            print(r['archivo'], r['sonoridad'], 'v', r['md5_video'], 'a', r['md5_audio'], 'err', r['decodifica_completo'],
                  'gps', r['marcas_gps_o_ubicacion'], flush=True)
    A_ = dict(base['archivos']); A_.update(rep['archivos'])
    rep['cruces'] = cruces(A_, list(NUMEROS))
    print('cruces', rep['cruces'], flush=True)
    rep['numeros'] = comparar_numeros()
    tira_numeros(ev / 'numeros_37-33_c10_c150.jpg')
    rep['empalme'], rep['psnr_contra_v01'], rep['contraste_placa'] = {}, {}, {}
    for N in otros:
        rep['empalme'][N] = json.load(open(MAS / f'empalme_{N}.json'))
        shutil.copy2(MAS / f'empalme_{N}.json', ev / f'empalme_{N}.json')
        ps = psnr_contra(MAS / nombre(N, 'completa'), T / 'master' / nombre(N, 'completa', 'v01'), ev / f'psnr_{N}_v02_contra_v01.log')
        rep['psnr_contra_v01'][N] = psnr_resumen(ps)
        cres, cf = contraste_placa(MAS / nombre(N, 'completa'), MAS / 'ref_sin_texto_36.mp4')
        rep['contraste_placa'][N] = {k: v for k, v in cres.items() if k != 'criterio'}
        jdump(cf, ev / f'contraste_por_cuadro_{N}.json')
        print(N, 'psnr', rep['psnr_contra_v01'][N]['psnr_avg_min'], rep['psnr_contra_v01'][N]['psnr_y_min'],
              'contraste', rep['contraste_placa'][N]['cuadros_que_no_pasan'], rep['contraste_placa'][N]['firma_pct_3a1_min'], flush=True)
        U.hoja_contacto(MAS / nombre(N, 'completa'), ev / f'hoja_contacto_cada_0.5s_{N}.jpg', cada=15, cols=9, ancho=240)
    jdump(rep, ev / 'control_variantes.json')
    print('listo variantes')


# =====================================================================================================
# etapa entregar · EXPORTACIONES/ + carpeta de la pieza + evidencia; verificación de las copias (sin sobrescribir)
# v02: «entregar 36» (36 con y sin música + evidencia_v02/) y después «entregar 37 35 34 33» (+ evidencia_v02/variantes/)
# =====================================================================================================
def etapa_entregar():
    solo = [int(x) for x in sys.argv[2:]] or list(NUMEROS)
    nombres = [nombre(N, k) for N in solo for k in ('completa', 'sinmusica')]
    variantes = V02 and REVISION not in solo
    ev_src = EVID / 'variantes' if variantes else EVID
    ev = PIEZA / EVID.name / 'variantes' if variantes else PIEZA / EVID.name
    for nm in nombres:
        for dst in (EXP / nm, PIEZA / nm):
            if dst.exists():
                raise RuntimeError(f'{dst} ya existe: no se sobrescribe')
    if ev.exists():
        raise RuntimeError(f'{ev} ya existe')
    for nm in nombres:
        for dst in (EXP / nm, PIEZA / nm):
            shutil.copyfile(MAS / nm, dst)
    shutil.copytree(ev_src, ev, ignore=None if variantes else shutil.ignore_patterns('variantes'))
    time.sleep(12)                                  # montaje de red: esperar antes de verificar
    res = {}
    for nm in nombres:
        src = MAS / nm
        ref = dict(bytes=src.stat().st_size, sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                   md5_video=U.md5_stream(src, 'v'), md5_audio=U.md5_stream(src, 'a'))
        res[str(src)] = ref
        for dst in (EXP / nm, PIEZA / nm):
            got = dict(bytes=dst.stat().st_size, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
                       md5_video=U.md5_stream(dst, 'v'), md5_audio=U.md5_stream(dst, 'a'))
            err = subprocess.run(nice(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(dst), '-f', 'null', '-']),
                                 capture_output=True, text=True).stderr.strip()
            cuerpo = dst.read_bytes()
            res[str(dst)] = dict(got, byte_a_byte=(got == ref), decodifica_sin_errores=(err == ''), atomos=L2.atomos(dst),
                                 flujos_identicos=(got['md5_video'] == ref['md5_video'] and got['md5_audio'] == ref['md5_audio']),
                                 marcas_ubicacion=[m.decode('latin1') for m in MARCAS_UBICACION if m in cuerpo])
            print(dst.name, dst.parent.name, res[str(dst)]['byte_a_byte'], res[str(dst)]['flujos_identicos'],
                  res[str(dst)]['decodifica_sin_errores'], flush=True)
    n_local = sum(1 for _ in ev_src.rglob('*') if _.is_file()); n_red = sum(1 for _ in ev.rglob('*') if _.is_file())
    res['evidencia'] = dict(carpeta=str(ev), archivos_local=n_local, archivos_red=n_red)
    nom = ('entrega_variantes.json' if variantes else 'entrega.json')
    jdump(res, TV / nom)
    shutil.copy2(TV / nom, ev / nom)
    print('evidencia', n_local, n_red)


if __name__ == '__main__':
    etapa = sys.argv[1] if len(sys.argv) > 1 else ''
    globals()['etapa_' + etapa]()
