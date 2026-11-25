# IGLIB-2 «Nadie cambia» · etapa 1: imágenes de cada tramo de video para el compositor (canvas).
# v02 (con locución): tramos más largos para que entre cada frase; los rangos se eligieron para que cada «No.» caiga
# en la acción (44451: suelta la pelota en 272; 876: impacto en 50). Revisado a 1080 que no aparezcan marcas nuevas.
# Uso: env/bin/python preparar_iglib2.py TRABAJO_DIR
#   src/8744/  Mixkit 8744 cuadros 148–202 (gesto de frustración con el celular y se inclina; la pantalla no se ve)
#   src/44451/ Mixkit 44451 cuadros 235–288; la marca impresa en la pelota (legible a 1080 en 235–246) se desenfoca
#              con una elipse que sigue la pelota (plantilla). «MVP 7» de la camiseta queda: es texto genérico, no marca.
#   src/876/   Mixkit 876 cuadros 6–66 (6–42 de perfil, sin logo a la vista); el logo de la remera rosa (rombo + texto, visible en 50–66) se borra con
#              seguimiento y relleno (inpaint) sobre la tela lisa.
#   src/608/   Mixkit 608 cuadros 60–123 (30 fps nativos).
#   src/4627/  IMG_4627 cuadros 287–412 (v02 usa 287–348 en el tramo 7 y 349–404 en el CTA) (HLG → SDR con la cadena mobius de CLAUDE.md, rotación aplicada) + blanco fijo
#              para toda la toma (rr=1,05 gg=1,02 bb=0,945 → B−R de la tela entre −1 y +5, medido con medir_tela.py).
#   src/3375/  IMG_3375 cuadros 15–68 (HLG → SDR) + blanco fijo (rr=0,873 bb=1,123: la luz de interior es cálida y
#              cambia con el giro de la prenda; tela entre ≈ +5 al principio y ≈ −8 al final, medido con medir_tela.py).
import sys, os, subprocess
import numpy as np, cv2

R = '/home/user/1'; MK = f'{R}/TRABAJO/iglib/mixkit'
out = sys.argv[1]; S = f'{out}/src'; os.makedirs(S, exist_ok=True)
HDR = 'zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p'

def extraer(src, a, b, carpeta, pre=None, post=None):
    d = f'{S}/{carpeta}'; os.makedirs(d, exist_ok=True)
    if all(os.path.exists(f'{d}/{n:04d}.png') for n in range(a, b + 1)): return d
    vf = f"select='between(n\\,{a}\\,{b})'" + (',' + pre if pre else '') + ',scale=in_color_matrix=bt709:in_range=tv:out_range=pc' + (',' + post if post else '') + ',format=rgb24'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', vf, '-fps_mode', 'passthrough', '-start_number', str(a),
                    '-compression_level', '1', f'{d}/%04d.png'], check=True, stdin=subprocess.DEVNULL)
    return d

def seguir(d, ns, ref_n, caja, margen=120):
    """Sigue una plantilla (caja x0,y0,x1,y1 en el cuadro ref_n) por los cuadros ns; devuelve {n: (dx, dy)}."""
    ref = cv2.imread(f'{d}/{ref_n:04d}.png', cv2.IMREAD_GRAYSCALE); x0, y0, x1, y1 = caja; tpl = ref[y0:y1, x0:x1]
    pos = {ref_n: (0, 0)}; prev = (x0, y0)
    orden = sorted(ns, key=lambda n: abs(n - ref_n))
    for n in orden:
        if n == ref_n: continue
        g = cv2.imread(f'{d}/{n:04d}.png', cv2.IMREAD_GRAYSCALE)
        vecino = min(pos, key=lambda k: abs(k - n)); px, py = x0 + pos[vecino][0], y0 + pos[vecino][1]
        sx0, sy0 = max(0, px - margen), max(0, py - margen); sx1, sy1 = min(g.shape[1], px + (x1 - x0) + margen), min(g.shape[0], py + (y1 - y0) + margen)
        r = cv2.matchTemplate(g[sy0:sy1, sx0:sx1], tpl, cv2.TM_CCOEFF_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
        pos[n] = (sx0 + ml[0] - x0, sy0 + ml[1] - y0)
    return pos

extraer(f'{MK}/8744-1080.mp4', 148, 202, '8744')
extraer(f'{MK}/608-1080.mp4', 60, 123, '608')

# 44451: pelota con marca impresa (235–246)
d = extraer(f'{MK}/44451-1080.mp4', 235, 288, '44451')
if not os.path.exists(f'{d}/.pelota_ok'):
    pos = seguir(d, range(235, 248), 241, (960, 740, 1220, 940), margen=160)
    for n, (dx, dy) in pos.items():
        im = cv2.imread(f'{d}/{n:04d}.png').astype(np.float32); h, w = im.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]; cx, cy = 1110 + dx, 855 + dy
        m = np.clip(1.25 - np.hypot((xx - cx) / 98, (yy - cy) / 62), 0, 1)[..., None]
        bl = cv2.GaussianBlur(im, (0, 0), 7)
        cv2.imwrite(f'{d}/{n:04d}.png', np.clip(im * (1 - m) + bl * m, 0, 255).astype(np.uint8), [cv2.IMWRITE_PNG_COMPRESSION, 1])
    open(f'{d}/.pelota_ok', 'w').write(str(pos))

# 876: logo de la remera (50–66), seguimiento desde el cuadro 62 (53–66) y desde el 53 (50–52), y relleno
d = extraer(f'{MK}/876-1080.mp4', 6, 66, '876')
if not os.path.exists(f'{d}/.logo_ok'):
    pos = seguir(d, range(53, 67), 62, (330, 778, 392, 832), margen=60)
    # 50–52: el logo gira y se achica; la plantilla de 62 se pierde (revisado a 1080). En 48–49 quedan dos rayas
    # ilegibles sobre el borde de la tela: no se tocan (el relleno ahí ensuciaba el borde). Se sigue con la plantilla del
    # cuadro 53 en su posición, buscando cerca de la posición extrapolada (≈ +41 px/cuadro en x).
    vx, vy = (pos[53][0] - pos[55][0]) / 2, (pos[53][1] - pos[55][1]) / 2
    g53 = cv2.imread(f'{d}/0053.png', cv2.IMREAD_GRAYSCALE); bx, by = 330 + pos[53][0], 778 + pos[53][1]
    tpl = g53[by:by + 54, bx:bx + 62]; prev = pos[53]
    for n in (52, 51, 50):
        ex, ey = prev[0] + vx, prev[1] + vy; px, py = int(330 + ex), int(778 + ey)
        g = cv2.imread(f'{d}/{n:04d}.png', cv2.IMREAD_GRAYSCALE); m = 28
        r = cv2.matchTemplate(g[py - m:py + 54 + m, px - m:px + 62 + m], tpl, cv2.TM_CCOEFF_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
        pos[n] = prev = (px - m + ml[0] - 330, py - m + ml[1] - 778)
    for n, (dx, dy) in pos.items():
        im = cv2.imread(f'{d}/{n:04d}.png'); h, w = im.shape[:2]
        m = np.zeros((h, w), np.uint8); cv2.ellipse(m, (int(361 + dx), int(804 + dy)), (36, 31), 0, 0, 360, 255, -1)
        fill = cv2.inpaint(im, m, 9, cv2.INPAINT_TELEA)
        # textura: se suma el grano de la tela de alrededor (desplazado) para que el parche no quede liso
        alfa = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 4)[..., None]
        grano = im.astype(np.float32) - cv2.GaussianBlur(im.astype(np.float32), (0, 0), 3)
        grano = np.roll(grano, 80, axis=1)
        res = im * (1 - alfa) + (fill.astype(np.float32) + grano * 0.8) * alfa
        cv2.imwrite(f'{d}/{n:04d}.png', np.clip(res, 0, 255).astype(np.uint8), [cv2.IMWRITE_PNG_COMPRESSION, 1])
    open(f'{d}/.logo_ok', 'w').write(str(pos))

# tomas propias HLG → SDR + blanco fijo por toma
extraer(f'{R}/ORIGINALES/IMG_4627.mov', 287, 412, '4627', pre=HDR, post='colorchannelmixer=rr=1.05:gg=1.02:bb=0.945')
extraer(f'{R}/ORIGINALES/IMG_3375.mov', 15, 68, '3375', pre=HDR, post='colorchannelmixer=rr=0.873:bb=1.123')
print('listo', S)
