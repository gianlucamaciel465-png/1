# IGLIB-1 «La tercera tarjeta» · etapa 1: prepara las imágenes de cada tramo de video para el compositor (canvas).
# Uso: env/bin/python preparar_iglib1.py TRABAJO_DIR
#   TRABAJO_DIR/src/7859/NNNN.png      IMG_7859 (SDR, rango completo BT.709) a 3840×2160, cuadros 15–119 y 180–248 (v01;
#                                      v02 agrega 120–128 y 139–249),
#                                      con corrección de blanco fija para toda la toma (rr=1.035, bb=0.955 → B−R ≤ +8)
#   TRABAJO_DIR/src/7859fill/NNNN.png  relleno desenfocado de la MISMA toma (franja derecha sin persona) a 1080×1920
#   TRABAJO_DIR/src/7859_estampado.json  centro y ancho de «ROCCÉ» por cuadro (plantilla multiescala, suavizado)
#   TRABAJO_DIR/src/879/NNNN.png + 879fill/   Mixkit 879 cuadros 134–172 (1920×1080) y relleno 1080×1920 desenfocado
#   TRABAJO_DIR/src/32807/NNNN.png     Mixkit 32807 cuadros 50–88 (1080×1920), escudo del edificio del fondo desenfocado
#   TRABAJO_DIR/src/40971/NNNN.png     Mixkit 40971 cuadros 0–35 (1080×1920)
# Los Mixkit de 23,976/24 fps se usan cuadro a cuadro a 30 fps (un cuadro de origen por cuadro de salida, sin repetir).
import sys, os, json, subprocess
import numpy as np, cv2

R = '/home/user/1'; MK = f'{R}/TRABAJO/iglib/mixkit'
out = sys.argv[1]; S = f'{out}/src'; os.makedirs(S, exist_ok=True)

def ff(*a):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True, stdin=subprocess.DEVNULL)

def extraer(src, a, b, carpeta, vf, rango='tv'):
    d = f'{S}/{carpeta}'; os.makedirs(d, exist_ok=True)
    if all(os.path.exists(f'{d}/{n:04d}.png') for n in range(a, b + 1)): return d
    ff('-i', src, '-vf', f"select='between(n\\,{a}\\,{b})',scale=in_color_matrix=bt709:in_range={rango}:out_range=pc"
       + (',' + vf if vf else '') + ',format=rgb24', '-fps_mode', 'passthrough', '-start_number', str(a),
       '-compression_level', '1', f'{d}/%04d.png')
    return d

WB = 'colorchannelmixer=rr=1.035:bb=0.955'
# --- IMG_7859 (rango completo): cuadros 15–119 (tramos 9 y 10) y 180–248 (tramo 14)
# v02 (con voz, línea de tiempo más larga): además 120–128 (tramo 10 sostenido) y 139–249 (CTA de 3,7 s)
for a, b in [(15, 119), (180, 248), (120, 128), (139, 179), (249, 249)]:
    extraer(f'{R}/ORIGINALES/IMG_7859.mov', a, b, '7859', WB, 'pc')
# relleno: franja derecha x 2850–3840 (sin persona en estos tramos), alto proporcional 9:16, ampliada y desenfocada
d7 = f'{S}/7859'; df = f'{S}/7859fill'; os.makedirs(df, exist_ok=True)
for f in sorted(os.listdir(d7)):
    if os.path.exists(f'{df}/{f}'): continue
    im = cv2.imread(f'{d7}/{f}'); crop = im[200:200 + 1760, 2850:3840]
    big = cv2.resize(crop, (1080, 1920), interpolation=cv2.INTER_AREA)
    big = cv2.GaussianBlur(big, (0, 0), 28)
    cv2.imwrite(f'{df}/{f}', (big * 0.78).astype(np.uint8), [cv2.IMWRITE_PNG_COMPRESSION, 1])

# --- seguimiento de «ROCCÉ» (cuadros 15–119): plantilla del cuadro 15, multiescala, sobre la imagen a 1/4
seg = f'{S}/7859_estampado.json'
if not os.path.exists(seg):
    g = lambda n: cv2.cvtColor(cv2.resize(cv2.imread(f'{d7}/{n:04d}.png'), (960, 540), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    ref = g(15)
    # caja de «ROCCÉ» en el cuadro 15 (a 960×540): se busca la zona oscura de letras dentro de la remera
    x0, y0, x1, y1 = 445, 200, 672, 290
    tpl = ref[y0:y1, x0:x1]; res = {}
    prev = None
    for n in range(15, 120):
        im = g(n); best = None
        for sc in np.arange(0.80, 1.60, 0.02):
            t = cv2.resize(tpl, None, fx=sc, fy=sc)
            if t.shape[0] >= im.shape[0] or t.shape[1] >= im.shape[1]: continue
            r = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
            if best is None or mv > best[0]: best = (mv, sc, ml, t.shape)
        mv, sc, ml, sh = best
        res[n] = dict(score=float(mv), sc=float(sc), cx=(ml[0] + sh[1] / 2) * 4, cy=(ml[1] + sh[0] / 2) * 4, w=sh[1] * 4)
    # suavizado (media móvil de 7 cuadros) para que el círculo no tiemble
    ks = sorted(res); arr = np.array([[res[k]['cx'], res[k]['cy'], res[k]['w']] for k in ks])
    pad = np.pad(arr, ((3, 3), (0, 0)), mode='edge'); sm = np.stack([pad[i:i + 7].mean(0) for i in range(len(ks))])
    for k, v in zip(ks, sm): res[k].update(cxs=float(v[0]), cys=float(v[1]), ws=float(v[2]))
    json.dump(res, open(seg, 'w'), indent=1)
    print('seguimiento: puntaje mínimo', min(v['score'] for v in res.values()))

# --- v02: centro y ancho de «ROCCÉ» en el CTA (139–249: la cámara se acerca en 140–176 y se aleja en 176–188), para
# que la ventana siga el estampado y no lo corte. Plantilla del cuadro 15, multiescala 0,55–1,6, suavizado de 9 cuadros.
seg2 = f'{S}/7859_cta.json'
if not os.path.exists(seg2):
    g = lambda n: cv2.cvtColor(cv2.resize(cv2.imread(f'{d7}/{n:04d}.png'), (960, 540), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    tpl = g(15)[200:290, 445:672]; res = {}
    for n in range(139, 250):
        im = g(n); best = None
        for sc in np.arange(0.55, 1.60, 0.02):
            t = cv2.resize(tpl, None, fx=sc, fy=sc)
            r = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
            if best is None or mv > best[0]: best = (mv, sc, ml, t.shape)
        mv, sc, ml, sh = best
        res[n] = dict(score=float(mv), sc=float(sc), cx=(ml[0] + sh[1] / 2) * 4, cy=(ml[1] + sh[0] / 2) * 4, w=sh[1] * 4)
    ks = sorted(res); arr = np.array([[res[k]['cx'], res[k]['cy'], res[k]['w']] for k in ks])
    pad = np.pad(arr, ((4, 4), (0, 0)), mode='edge'); sm = np.stack([pad[i:i + 9].mean(0) for i in range(len(ks))])
    for k, v in zip(ks, sm): res[k].update(cxs=float(v[0]), cys=float(v[1]), ws=float(v[2]))
    json.dump(res, open(seg2, 'w'), indent=1)
    print('seguimiento CTA: puntaje mínimo', min(v['score'] for v in res.values()))

# --- Mixkit 879 (saque aéreo): 134–172 + relleno de la misma toma
d = extraer(f'{MK}/879-1080.mp4', 134, 172, '879', None)
df = f'{S}/879fill'; os.makedirs(df, exist_ok=True)
for f in sorted(os.listdir(d)):
    if os.path.exists(f'{df}/{f}'): continue
    im = cv2.imread(f'{d}/{f}'); h, w = im.shape[:2]; cw = int(h * 1080 / 1920); x = (w - cw) // 2 + 300
    big = cv2.GaussianBlur(cv2.resize(im[:, x:x + cw], (1080, 1920), interpolation=cv2.INTER_CUBIC), (0, 0), 28)
    cv2.imwrite(f'{df}/{f}', (big * 0.78).astype(np.uint8), [cv2.IMWRITE_PNG_COMPRESSION, 1])

# --- Mixkit 32807 (corredora): 50–88 (antes de que se lea la marca dorada de las zapatillas, que aparece desde ~100)
d = extraer(f'{MK}/32807-1080.mp4', 50, 88, '32807', None)
# escudo del edificio del fondo (cámara fija): se reemplaza la zona por la placa de fondo desenfocada, solo donde
# el píxel coincide con el fondo (si pasa una pierna por delante, queda la pierna)
marca = f'{d}/.escudo_ok'
if not os.path.exists(marca):
    fr = [cv2.imread(f'{d}/{n:04d}.png').astype(np.float32) for n in range(50, 89)]
    x0, y0, x1, y1 = 360, 1360, 520, 1520
    pila = np.stack([f[y0:y1, x0:x1] for f in fr]); placa = np.median(pila, 0)
    borr = cv2.GaussianBlur(placa, (0, 0), 9)
    yy, xx = np.mgrid[y0:y1, x0:x1]; cx, cy = 432, 1440
    caja = np.clip(1.6 - np.hypot((xx - cx) / 52, (yy - cy) / 60), 0, 1)[..., None]
    for n, f in zip(range(50, 89), fr):
        z = f[y0:y1, x0:x1]; fondo = (np.abs(z - placa).sum(2, keepdims=True) < 36).astype(np.float32)
        fondo = cv2.GaussianBlur(fondo, (0, 0), 2)[..., None] if fondo.ndim == 3 else fondo
        a = caja * fondo.reshape(caja.shape)
        f[y0:y1, x0:x1] = z * (1 - a) + borr * a
        cv2.imwrite(f'{d}/{n:04d}.png', np.clip(f, 0, 255).astype(np.uint8), [cv2.IMWRITE_PNG_COMPRESSION, 1])
    open(marca, 'w').write('ok')

# --- Mixkit 40971 (boxeador): 0–35. El parche del guante (marca) pasa barrido e ilegible en 14–22 (revisado a 1080).
extraer(f'{MK}/40971-1080.mp4', 0, 35, '40971', None)
print('listo', S)
