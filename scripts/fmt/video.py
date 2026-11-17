#!/usr/bin/env python3
"""Tanda FMT (17/11/2026) · herramientas comunes de imagen para los 5 videos de formatos.

Cada pieza define una lista de planos (receta) y usa estas funciones:
  plano(...)   -> recorta un tramo de un original, lo pasa a SDR BT.709 rango limitado, lo encuadra a 1080x1920 30 fps
  foto(...)    -> una foto de PRODUCTO/ como plano (con empuje suave opcional)
  unir(...)    -> concatena los planos (sin recomprimir de más: intermedios x264 crf 12)
  ass(...)     -> escribe un .ass con los textos (libass; Inter / Inter Display del sistema)
  master(...)  -> quema textos, mezcla audio, codifica H.264 High nivel 4.0 + AAC-LC 48 kHz, faststart, sin metadatos
  hoja(...)    -> hoja de contacto con tiempo impreso

Ganancias de 4530, 4531 y 4631 medidas por Roma el 17/11 sobre tela sin estampado (objetivo B−R ≈ +8, G−R ≈ +1,5,
igual que las tomas de roca de REAL-02).
Color: las tomas HLG del iPhone 13 pasan por la cadena probada (CLAUDE.md) y después por ganancias por toma medidas
sobre la tela blanca (fe de erratas de Pedro, REAL-02 03_pedro_inventario.md). Las de rango completo del iPhone 15
pasan a rango limitado. Las fotos de iPhone (Display P3) se convierten a sRGB con ImageCms.
"""
import json, os, subprocess, shlex
from pathlib import Path

R = Path('/home/user/1')
O = R / 'ORIGINALES'
P = R / 'PRODUCTO'
W, H, FPS = 1080, 1920, 30

# --- datos por toma (natural = ya rotada). hdr: HLG; full: rango completo; g: ganancias R/G/B sobre gbrp ---
TOMAS = {
    'IMG_3375': dict(hdr=True, nat=(1080, 1920), g=(0.910, 1.017, 1.139)),
    'IMG_3453': dict(hdr=True, nat=(1080, 1920), extra='colorchannelmixer=rr=0.90:gg=0.98:bb=1.10,eq=gamma=0.70:saturation=0.85'),
    'IMG_4530': dict(hdr=True, nat=(1080, 1920), g=(1.012, 1.005, 0.918)),
    'IMG_4531': dict(hdr=True, nat=(1080, 1920), g=(1.000, 1.012, 0.940)),
    'IMG_4625': dict(hdr=True, nat=(1080, 1920), g=(0.988, 1.006, 0.975)),
    'IMG_4627': dict(hdr=True, nat=(1080, 1920), g=(0.997, 1.005, 0.965)),
    'IMG_4631': dict(hdr=True, nat=(1080, 1920), g=(1.015, 1.000, 0.930)),
    'IMG_4641': dict(hdr=True, nat=(1080, 1920), g=(1.035, 1.004, 0.878)),
    'IMG_4675': dict(hdr=True, nat=(1080, 1920), g=None),
    'IMG_7793': dict(nat=(2160, 3840)), 'IMG_7824': dict(nat=(2160, 3840)),
    'IMG_7857': dict(nat=(2160, 3840), g=(1.029, 0.996, 0.960)), 'IMG_7859': dict(nat=(3840, 2160), full=True),
    'IMG_7884': dict(nat=(2160, 3840)), 'IMG_7885': dict(nat=(2160, 3840)), 'IMG_7887': dict(nat=(2160, 3840)),
    'IMG_7894': dict(nat=(2160, 3840)), 'IMG_7895': dict(nat=(2160, 3840)), 'IMG_7896': dict(nat=(2160, 3840)),
    'IMG_7901': dict(nat=(2160, 3840)), 'IMG_7947': dict(nat=(2160, 3840)),
    'IMG_7996': dict(nat=(2160, 3840), full=True), 'IMG_7999': dict(nat=(2160, 3840), full=True),
    'IMG_8002': dict(nat=(2160, 3840)), 'IMG_8004': dict(nat=(2160, 3840)), 'IMG_8008': dict(nat=(2160, 3840), full=True),
    'clip_a2c1cbe8': dict(nat=(576, 1024)), 'clip_a592f367': dict(nat=(576, 1024)), 'clip_f2a34e51': dict(nat=(576, 1024)),
}
HLG = ('zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,'
       'zscale=t=bt709:m=bt709:r=tv,format=gbrp')
ENC_INT = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p',
           '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']


def sh(cmd, **kw):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise RuntimeError(f"falló: {' '.join(map(str, cmd))}\n{r.stderr[-3000:]}")
    return r.stdout


def _src(toma):
    for ext in ('.mov', '.MOV', '.mp4'):
        p = O / f'{toma}{ext}'
        if p.exists():
            return p
    raise FileNotFoundError(toma)


def color(toma):
    """cadena de color hasta gbrp/yuv SDR rango limitado"""
    d = TOMAS.get(toma, {})
    f = []
    if d.get('hdr'):
        f.append(HLG)
        if d.get('g'):
            r, g, b = d['g']; f.append(f'colorchannelmixer=rr={r}:gg={g}:bb={b}')
        if d.get('extra'):
            f.append(d['extra'])
        f.append('format=yuv420p')
    else:
        if d.get('full'):
            f.append('scale=in_range=full:out_range=tv')
        if d.get('g'):
            r, g, b = d['g']; f += ['format=gbrp', f'colorchannelmixer=rr={r}:gg={g}:bb={b}']
        f.append('format=yuv420p')
    return ','.join(f)


def encuadre(toma, caja=None, z0=1.0, z1=None, dur=1.0, cx=None, cy=None, espejo=False):
    """caja = (x, y, w, h) en coordenadas naturales (ya rotadas). Si no hay caja, se usa la ventana 9:16 más grande
    centrada. z0->z1: acercamiento lineal sobre la caja (centrado en cx, cy de la caja, por defecto el centro)."""
    nw, nh = TOMAS.get(toma, {}).get('nat', (1080, 1920))
    if caja is None:
        if nw / nh > W / H:
            ch = nh; cw = round(nh * W / H)
        else:
            cw = nw; ch = round(nw * H / W)
        caja = ((nw - cw) // 2, (nh - ch) // 2, cw, ch)
    x, y, w, h = caja
    z1 = z0 if z1 is None else z1
    if z0 == 1.0 and z1 == 1.0:
        f = [f'crop={w}:{h}:{x}:{y}']
    else:
        # zoom = z0 + (z1-z0)*t/dur ; ventana w/zoom centrada en (cx, cy)
        cx = x + w / 2 if cx is None else cx; cy = y + h / 2 if cy is None else cy
        Z = f'({z0}+({z1}-{z0})*min(t/{dur},1))'
        ww = f'{w}/{Z}'; hh = f'{h}/{Z}'
        xx = f'max({x},min({x}+{w}-{w}/{Z},{cx}-{w}/{Z}/2))'
        yy = f'max({y},min({y}+{h}-{h}/{Z},{cy}-{h}/{Z}/2))'
        # crop con dimensiones variables no está permitido: se escala primero 2x para que el redondeo no tiemble
        f = [f"scale=iw*2:ih*2:flags=bicubic", f"crop=w='2*{ww}':h='2*{hh}':x='2*{xx}':y='2*{yy}':exact=1"]
    f.append(f'scale={W}:{H}:flags=lanczos')
    if espejo:
        f.append('hflip')
    f.append('setsar=1')
    return ','.join(f)


def plano(toma, desde, hasta, salida, caja=None, z0=1.0, z1=None, vel=1.0, cx=None, cy=None, post=None, espejo=False):
    """Tramo [desde, hasta) del original (segundos de la fuente). vel>1 acelera. Salida a 30 fps exactos."""
    dur_src = hasta - desde
    dur = dur_src / vel
    vf = [color(toma), encuadre(toma, caja, z0, z1, dur_src, cx, cy, espejo)]
    if vel != 1.0:
        vf.append(f'setpts=PTS/{vel}')
    vf.append(f'fps={FPS}')
    if post:
        vf.append(post)
    nf = round(dur * FPS)
    sh(['ffmpeg', '-v', 'error', '-y', '-ss', f'{desde:.4f}', '-i', str(_src(toma)), '-t', f'{dur_src + 0.2:.4f}',
        '-an', '-vf', ','.join(vf), '-frames:v', str(nf), *ENC_INT, str(salida)])
    return dict(toma=toma, desde=desde, hasta=hasta, cuadros=nf, salida=str(salida), caja=caja, z0=z0, z1=z1, vel=vel)


def foto_srgb(path, out_png):
    """Convierte una foto de PRODUCTO/ a sRGB (Display P3 -> sRGB) y aplica la orientación EXIF."""
    from PIL import Image, ImageOps, ImageCms
    import io
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    icc = im.info.get('icc_profile')
    if icc:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        dst = ImageCms.createProfile('sRGB')
        im = ImageCms.profileToProfile(im.convert('RGB'), src, dst, renderingIntent=1, outputMode='RGB')
    im.convert('RGB').save(out_png)
    return out_png


def foto(path, dur, salida, caja=None, z0=1.0, z1=1.0, cx=None, cy=None, tmp=None):
    """Foto como plano de `dur` s. caja en píxeles de la foto (orientada). Empuje z0->z1."""
    from PIL import Image
    tmp = tmp or str(salida) + '.png'
    foto_srgb(path, tmp)
    iw, ih = Image.open(tmp).size
    if caja is None:
        if iw / ih > W / H:
            ch = ih; cw = round(ih * W / H)
        else:
            cw = iw; ch = round(iw * H / W)
        caja = ((iw - cw) // 2, (ih - ch) // 2, cw, ch)
    x, y, w, h = caja
    nf = round(dur * FPS)
    cx = x + w / 2 if cx is None else cx; cy = y + h / 2 if cy is None else cy
    # zoompan por cuadro con precisión subpíxel: escalar la foto 4x antes (suave) y recortar
    Z = f'({z0}+({z1}-{z0})*on/{max(nf - 1, 1)})'
    vf = (f"scale=iw*4:ih*4:flags=bicubic,zoompan=z='1':d=1:s={W}x{H}:fps={FPS}:"
          f"x='4*max({x},min({x}+{w}-{w}/{Z},{cx}-{w}/{Z}/2))':y='4*max({y},min({y}+{h}-{h}/{Z},{cy}-{h}/{Z}/2))'")
    # zoompan no admite ventana variable con z=1; se usa crop+scale por cuadro mediante loop + crop con 'n'
    vf = (f"loop=loop={nf - 1}:size=1:start=0,setpts=N/{FPS}/TB,scale=iw*2:ih*2:flags=bicubic,"
          f"crop=w='2*{w}/{Z.replace('on', 'n')}':h='2*{h}/{Z.replace('on', 'n')}':"
          f"x='2*max({x},min({x}+{w}-{w}/{Z.replace('on', 'n')},{cx}-{w}/{Z.replace('on', 'n')}/2))':"
          f"y='2*max({y},min({y}+{h}-{h}/{Z.replace('on', 'n')},{cy}-{h}/{Z.replace('on', 'n')}/2))':exact=1,"
          f"scale={W}:{H}:flags=lanczos,setsar=1,format=yuv420p")
    sh(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-vf', vf, '-frames:v', str(nf), '-r', str(FPS), *ENC_INT, str(salida)])
    return dict(foto=str(path), cuadros=nf, salida=str(salida), caja=caja, z0=z0, z1=z1)


def unir(planos, salida):
    lst = Path(str(salida) + '.txt')
    lst.write_text(''.join(f"file '{Path(p['salida']).resolve()}'\n" for p in planos))
    sh(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(salida)])
    n = int(sh(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                'stream=nb_read_frames', '-of', 'csv=p=0', str(salida)]).strip())
    esperado = sum(p['cuadros'] for p in planos)
    if n != esperado:
        raise RuntimeError(f'unir: {n} cuadros, esperaba {esperado}')
    return n


# ---------------- textos (ASS / libass) ----------------
def _t(seg):
    seg = max(0, seg); h = int(seg // 3600); m = int(seg % 3600 // 60); s = seg % 60
    return f'{h}:{m:02d}:{s:05.2f}'


ESTILOS = {
    # nombre: (fuente, tamaño, primario, contorno, fondo, negrita, borde, sombra, estilo_borde, alineación, margenV)
    # colores ASS &HAABBGGRR
    'Nativo':  ('Inter Display SemiBold', 64, '&H00FFFFFF', '&H90000000', '&H90000000', 0, 2.2, 0, 1, 8, 0),
    'Grande':  ('Inter Display ExtraBold', 104, '&H00FFFFFF', '&H00000000', '&H80000000', 0, 6, 0, 1, 8, 0),
    'Caja':    ('Inter Display SemiBold', 58, '&H00141414', '&H00FFFFFF', '&H00FFFFFF', 0, 16, 0, 3, 8, 0),
    'CajaN':   ('Inter Display SemiBold', 58, '&H00FFFFFF', '&H00141414', '&H00141414', 0, 16, 0, 3, 8, 0),
    'Chico':   ('Inter Display Medium', 44, '&H00FFFFFF', '&H90000000', '&H90000000', 0, 1.6, 0, 1, 8, 0),
    'Serif':   ('Inter Display Bold', 70, '&H00FFFFFF', '&H90000000', '&H90000000', 0, 2, 0, 1, 8, 0),
}


def ass(textos, salida, estilos=None):
    """textos: lista de dicts {t0, t1, txt, estilo, x, y, pop(bool), fad(ms_in, ms_out), extra(tags)}.
    x, y = punto de anclaje (alineación del estilo; 8 = arriba al centro). txt admite \\N y tags ASS."""
    est = dict(ESTILOS); est.update(estilos or {})
    L = ['[Script Info]', 'ScriptType: v4.00+', f'PlayResX: {W}', f'PlayResY: {H}', 'WrapStyle: 2',
         'ScaledBorderAndShadow: yes', 'YCbCr Matrix: TV.709', '', '[V4+ Styles]',
         'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, '
         'Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, '
         'MarginV, Encoding']
    for n, (fn, fs, pc, oc, bc, b, bo, shd, bs, al, mv) in est.items():
        L.append(f'Style: {n},{fn},{fs},{pc},&H000000FF,{oc},{bc},{b},0,0,0,100,100,0,0,{bs},{bo},{shd},{al},40,40,{mv},1')
    L += ['', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
    for k in textos:
        tags = [f"\\pos({k.get('x', W // 2)},{k['y']})"]
        if k.get('pop'):
            tags.append('\\fscx118\\fscy118\\t(0,90,\\fscx100\\fscy100)')
        if k.get('fad'):
            a, b = k['fad']; tags.append(f'\\fad({a},{b})')
        if k.get('blur', True) and est[k.get('estilo', 'Nativo')][8] == 1:
            tags.append('\\blur3')
        if k.get('extra'):
            tags.append(k['extra'])
        L.append(f"Dialogue: {k.get('capa', 0)},{_t(k['t0'])},{_t(k['t1'])},{k.get('estilo', 'Nativo')},,0,0,0,,"
                 f"{{{''.join(tags)}}}{k['txt']}")
    Path(salida).write_text('\n'.join(L) + '\n', encoding='utf-8')
    return salida


def master(video, audio_wav, salida, ass_path=None, overlays=None):
    """Quema el .ass (si hay) y overlays PNG [(png, x, y, t0, t1)], codifica para iPhone (H.264 High 4.0)."""
    inputs = ['-i', str(video), '-i', str(audio_wav)]
    chain = '[0:v]'
    fc = []
    lab = 'v0'
    fc.append(f'[0:v]setsar=1[{lab}]')
    for i, (png, x, y, t0, t1) in enumerate(overlays or []):
        inputs += ['-loop', '1', '-i', str(png)]
        nl = f'v{i + 1}'
        fc.append(f"[{lab}][{i + 2}:v]overlay={x}:{y}:enable='between(t,{t0},{t1})':shortest=1[{nl}]")
        lab = nl
    if ass_path:
        fc.append(f"[{lab}]subtitles={ass_path}:fontsdir=/usr/share/fonts/opentype/inter[vs]"); lab = 'vs'
    fc.append(f'[{lab}]format=yuv420p[vout]')
    sh(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '1:a:0',
        '-c:v', 'libx264', '-profile:v', 'high', '-level:v', '4.0', '-preset', 'slow', '-crf', '17',
        '-maxrate', '20M', '-bufsize', '25M', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-g', '30',
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
        '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '192k', '-ar', '48000', '-ac', '2',
        '-map_metadata', '-1', '-map_metadata:s:v', '-1', '-map_metadata:s:a', '-1',
        '-metadata:s:v:0', 'handler_name=VideoHandler', '-metadata:s:a:0', 'handler_name=SoundHandler',
        '-shortest', '-movflags', '+faststart', str(salida)])
    return salida


def hoja(video, salida, cada=0.5, ancho=216, cols=8):
    """hoja de contacto con el tiempo impreso (cuadros exactos: select por número de cuadro)."""
    n = round(cada * FPS)
    sh(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vf',
        f"select='not(mod(n\\,{n}))',scale={ancho}:-2,drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-Bold.otf:"
        f"text='%{{pts\\:hms}} c%{{n}}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6,"
        f"tile={cols}x{20}:padding=2", '-frames:v', '1', '-fps_mode', 'vfr', str(salida)])
    return salida


def cuadro(video, n, salida, escala=None):
    vf = f"select='eq(n\\,{n})'" + (f',scale={escala}:-2' if escala else '')
    sh(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vf', vf, '-frames:v', '1', '-fps_mode', 'vfr', str(salida)])
    return salida
