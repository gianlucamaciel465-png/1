#!/usr/bin/env python3
"""GTA6 «La misión» · animática v00 (Pedro, 19/11/2026). Línea de tiempo completa del guion G1 con D = 16,00.

  c0–c449    marcador por plano (H, G3, G2, G4, G6, G5, G7: fondo neutro con nombre, lo que se ve y el tramo) en lugar
             de los clips generados, con el empuje del hook (1,00→1,04) y la sacudida de 11,85 (3 cuadros, 6 px)
  c450–c479  mapa del cambio de personaje (mapa.py) con el último cuadro de G7 (marcador) achicándose
  encima     toda la gráfica (grafica.py, variante A o B) hasta 15,70
  c480–c646  tramo real (real.py): 7887 → 7884 → 4631 (o 7895 con --alt)
Audio: efectos + ambiente real + clic TEMP 100 BPM (sonido_gta.py), sin música.
Salida: TRABAJO/gta/ROCCE_GTA6_animatica_v00.mp4 (H.264 High 4.0, yuv420p, 30 fps, AAC 48 kHz), copia en evidencia_pre/.

Uso (venv): python animatica.py render [A|B] [--alt]  ·  python animatica.py control
"""
import hashlib, json, math, shutil, subprocess, sys, textwrap, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, '/home/user/1/scripts/gta')
from comun import T, EVID, W, H, FPS, D, ND, PLANOS, inter, sobre, run, guardar_json   # noqa
from grafica import Grafica, c as cuadro                                                  # noqa
import mapa as MP                                                                          # noqa

A = T / 'audio'
TR = T / 'real'
VER = next((a.split('=')[1] for a in sys.argv if a.startswith('--ver=')), 'v00')   # v01: --ver=v01
NOMBRE = {('A', False): 'ROCCE_GTA6_animatica_v00.mp4', ('B', False): 'ROCCE_GTA6_animatica_B_v00.mp4',
          ('A', True): 'ROCCE_GTA6_animatica_ALT7895_v00.mp4'}
NEUTRO = (62, 66, 72)


def plano_de(n):
    t = n / FPS
    for p in PLANOS:
        if p[1] - 1e-9 <= t < p[2] - 1e-9:
            return p
    return PLANOS[-1]


_cache = {}


def marcador(pid):
    """fondo neutro del plano: id grande y tenue al centro, y abajo (y 1480–1830, libre de gráfica) nombre, qué se ve y
    tramo. El marcador no es gráfica de la pieza."""
    if pid in _cache:
        return _cache[pid]
    p = [x for x in PLANOS if x[0] == pid][0]
    im = Image.new('RGB', (W, H), NEUTRO); d = ImageDraw.Draw(im)
    # rayado diagonal tenue (se lee como «falta el clip»)
    for x in range(-H, W, 60):
        d.line([(x, H), (x + H, 0)], fill=(68, 72, 78), width=14)
    big = inter(360, 'Black')
    tw = big.getlength(pid)
    d.text(((W - tw) / 2, 760), pid, font=big, fill=(84, 89, 96))
    y = 1480
    d.rectangle([40, y - 20, W - 40, 1840], fill=(30, 32, 36))
    d.text((64, y), f'{pid} · MARCADOR (clip generado pendiente)', font=inter(40, 'Bold'), fill=(255, 214, 90))
    y += 60
    for linea in textwrap.wrap(p[4], 52):
        d.text((64, y), linea, font=inter(32, 'Medium'), fill=(225, 228, 232)); y += 42
    y += 8
    d.text((64, y), f'Fuente: {p[3]}', font=inter(30, 'Medium'), fill=(170, 200, 230)); y += 40
    d.text((64, y), f'Máster {p[1]:.2f}–{p[2]:.2f} s'.replace('.', ','), font=inter(30, 'Medium'), fill=(170, 200, 230))
    _cache[pid] = np.asarray(im)
    return _cache[pid]


def fondo(n):
    p = plano_de(n); pid = p[0]
    bg = marcador(pid).copy()
    d = Image.fromarray(bg); dr = ImageDraw.Draw(d)
    t = n / FPS
    dr.text((W - 330, 1790), f't {t:05.2f} · c{n} · D{t - D:+.2f}'.replace('.', ','), font=inter(26, 'Medium'), fill=(200, 200, 200))
    dr.text((64, 1790), 'AUDIO: efectos + clic TEMP 100 BPM · sin Legacy', font=inter(26, 'Medium'), fill=(255, 140, 120))
    bg = np.asarray(d)
    if pid == 'H':      # empuje 1,00→1,04 + viñeta (el contraste +15 % es del clip)
        z = 1 + 0.04 * n / (cuadro(1.50) - 1)
        im = Image.fromarray(bg); w2, h2 = W / z, H / z
        im = im.resize((W, H), Image.LANCZOS, box=((W - w2) / 2, (H - h2) / 2, (W + w2) / 2, (H + h2) / 2))
        yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
        vig = 1 - 0.35 * np.clip((r - 0.6) / 0.8, 0, 1) ** 1.5
        bg = (np.asarray(im, np.float32) * vig[..., None]).astype(np.uint8)
    if pid == 'G5':     # «toc» 11,85 + sacudida 3 cuadros (6 px)
        k = n - cuadro(11.85)
        if 0 <= k < 3:
            dx, dy = [(6, -4), (-6, 3), (3, -2)][k]
            bg = np.roll(np.roll(bg, dy, 0), dx, 1)
    return bg


def enc_rgb(salida):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                             '-r', str(FPS), '-i', '-', '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
                             '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-colorspace', 'bt709',
                             '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', str(salida)],
                            stdin=subprocess.PIPE)


def render(variante='A', alt=False):
    g = Grafica(variante)
    pre = T / f'animatica_pre_{variante}{"" if VER == "v00" else "_" + VER}.mp4'
    if not (alt and pre.exists()):
        M = MP.Mapa()
        contenido = fondo(cuadro(15.00) - 1)          # último cuadro de G7 (marcador), sin gráfica
        e = enc_rgb(pre)
        t0 = time.time()
        for n in range(ND):
            bg = M.cuadro(n, contenido) if n >= MP.N0 else fondo(n)
            lz, vis = g.capa(n)
            e.stdin.write(sobre(bg, lz.p).tobytes())
            if n % 60 == 0:
                print(n, round(time.time() - t0, 1), vis, flush=True)
        e.stdin.close(); e.wait()
    segs = [TR / '7887.mp4', TR / '7884.mp4', TR / ('7895.mp4' if alt else '4631.mp4')]
    lst = T / f'animatica_{variante}{"_alt" if alt else ""}.txt'
    lst.write_text(''.join(f"file '{p}'\n" for p in [pre] + segs))
    out = T / NOMBRE[(variante, alt)].replace('_v00', f'_{VER}')
    nf = ND + sum(int(run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                           'stream=nb_read_frames', '-of', 'csv=p=0', str(s)]).decode()) for s in segs)
    wav = (T / 'audio_alt7895' if alt else A) / 'mezcla_animatica.wav'      # ALT: ambiente de 7895 bajo 7895
    dur = nf / FPS
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-i', str(wav),
         '-map', '0:v:0', '-map', '1:a:0', '-vf', 'setsar=1,format=yuv420p', '-frames:v', str(nf),
         '-c:v', 'libx264', '-profile:v', 'high', '-level:v', '4.0', '-preset', 'slow', '-crf', '18',
         '-maxrate', '20M', '-bufsize', '25M', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-g', '30',
         '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
         '-af', f'apad=whole_dur={dur:.4f},atrim=0:{dur:.4f}',
         '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
         '-map_metadata', '-1', '-metadata:s:v:0', 'handler_name=VideoHandler',
         '-metadata:s:a:0', 'handler_name=SoundHandler', '-metadata:s:a:0', 'title=efectos + ambiente + clic TEMP 100 BPM (sin musica)',
         '-movflags', '+faststart', str(out)])
    print('salida', out, nf)
    return out


# ===================================================================================================== control
def md5_stream(mp4, sel):
    return run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-map', f'0:{sel}', '-c', 'copy', '-f', 'md5', '-']).decode().strip().split('=')[-1]


def ebur(mp4, t0=None, t1=None):
    cmd = ['ffmpeg', '-nostats']
    if t0 is not None:
        cmd += ['-ss', str(t0), '-t', str(t1 - t0)]
    cmd += ['-i', str(mp4), '-map', '0:a:0', '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-']
    r = subprocess.run(cmd, capture_output=True, text=True).stderr
    g = lambda k: float([l for l in r.splitlines() if l.strip().startswith(k)][-1].split()[1])
    return dict(I=g('I:'), LRA=g('LRA:'), pico_dbtp=g('Peak:'))


def cuadros_rgb(mp4, ns, ancho=None):
    out = {}
    for n in ns:
        vf = f"select='eq(n\\,{n})'" + (f',scale={ancho}:-2:flags=lanczos' if ancho else '')
        raw = run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-vf', vf + ',format=rgb24', '-fps_mode', 'passthrough',
                   '-frames:v', '1', '-f', 'rawvideo', '-'])
        w = ancho or W; h = len(raw) // (3 * w)
        out[n] = np.frombuffer(raw, np.uint8).reshape(h, w, 3)
    return out


def hoja(mp4, ns, salida, ancho=360, cols=5, rotulos=None):
    fr = cuadros_rgb(mp4, ns, ancho)
    h = next(iter(fr.values())).shape[0]
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 15)
    rows = math.ceil(len(ns) / cols)
    s = Image.new('RGB', (cols * (ancho + 4), rows * (h + 26)), (20, 20, 20))
    for i, n in enumerate(ns):
        im = Image.fromarray(fr[n]); x = (i % cols) * (ancho + 4); y = (i // cols) * (h + 26)
        s.paste(im, (x, y + 22))
        ImageDraw.Draw(s).text((x + 4, y + 3), (rotulos or {}).get(n, f'c{n} · {n / FPS:.2f} s'.replace('.', ',')), font=fnt, fill=(255, 220, 80))
    s.save(salida, quality=88)
    return salida


def control(variante='A', alt=False):
    mp4 = T / NOMBRE[(variante, alt)].replace('_v00', f'_{VER}')
    sfx = ('_alt' if alt else '') + ('' if VER == 'v00' else f'_{VER}')
    E = T / 'evidencia'; E.mkdir(exist_ok=True)
    rep = {}
    pr = json.loads(run(['ffprobe', '-v', 'error', '-show_entries',
                         'format=duration,size,bit_rate:stream=index,codec_name,profile,level,width,height,pix_fmt,avg_frame_rate,'
                         'r_frame_rate,nb_frames,duration,sample_rate,channels,color_range,color_space,color_transfer,color_primaries',
                         '-of', 'json', str(mp4)]))
    rep['ffprobe'] = pr
    dec = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-f', 'null', '-'], capture_output=True, text=True)
    rep['decodificacion_completa'] = dict(codigo=dec.returncode, errores=dec.stderr.strip()[:2000])
    rep['cuadros_contados'] = int(run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                                       'stream=nb_read_frames', '-of', 'csv=p=0', str(mp4)]).decode())
    rep['md5_streams'] = dict(video=md5_stream(mp4, 'v:0'), audio=md5_stream(mp4, 'a:0'))
    h = hashlib.sha256(); h.update(mp4.read_bytes()); rep['sha256_archivo'] = h.hexdigest()
    rep['sonoridad_total'] = ebur(mp4)
    rep['sonoridad_tramos'] = {nom: ebur(mp4, a, b)['I'] for nom, a, b in
                               (('H', 0, 1.5), ('G3', 1.5, 3.9), ('G2', 3.9, 6.3), ('G4', 6.3, 8.3), ('G6', 8.3, 10.0),
                                ('G5', 10.0, 12.6), ('G7', 12.6, 15.0), ('mapa', 15.0, 16.0), ('real', 16.0, 21.5))}
    # silencio final
    raw = run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-map', '0:a:0', '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'])
    a = np.frombuffer(raw, np.float32)
    win = 480; rms = np.sqrt(np.convolve(a ** 2, np.ones(win) / win, 'same'))
    act = np.nonzero(20 * np.log10(rms + 1e-9) > -50)[0]
    rep['silencio_final_s'] = round((len(a) - act.max()) / 48000, 3) if len(act) else None
    rep['duracion_audio_s'] = round(len(a) / 48000, 4)
    # cuadros: negro medido en c479 y primer cuadro de 7887 en c480
    fr = cuadros_rgb(mp4, [478, 479, 480, 481])
    rep['c479_media_rgb'] = [round(float(v), 1) for v in fr[479].reshape(-1, 3).mean(0)]
    rep['c479_desvio'] = round(float(fr[479].reshape(-1, 3).std(0).max()), 2)
    rep['c480_media_rgb'] = [round(float(v), 1) for v in fr[480].reshape(-1, 3).mean(0)]
    rep['negro_medido_7887'] = json.loads((T / 'negro_7887.json').read_text())
    # hoja 360 de cuadros clave
    claves = [0, 13, 20, 47, 70, 175, 240, 290, 320, 365, 400, 415, 455, 465, 474, 479, 480, 500, 545, 610]
    hoja(mp4, claves, E / f'hoja_360_claves_{variante}{sfx}.jpg', 360, 5)
    # cortes: cuadro antes y después de cada corte
    cortes = [45, 117, 189, 249, 300, 378, 450, 480, 533, 575]
    ns = sorted(set(sum([[c - 1, c] for c in cortes], [])))
    hoja(mp4, ns, E / f'hoja_cortes_{variante}{sfx}.jpg', 216, 10)
    hoja(mp4, list(range(0, rep['cuadros_contados'], 15)), E / f'hoja_contacto_{variante}{sfx}.jpg', 180, 11)
    guardar_json(rep, E / f'control_{variante}{sfx}.json')
    print(json.dumps({k: v for k, v in rep.items() if k != 'ffprobe'}, ensure_ascii=False, indent=1))
    return rep


if __name__ == '__main__':
    et = sys.argv[1]; var = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] in ('A', 'B') else 'A'; alt = '--alt' in sys.argv
    if et == 'render':
        render(var, alt)
    elif et == 'control':
        control(var, alt)
