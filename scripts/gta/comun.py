#!/usr/bin/env python3
"""GTA6 «La misión» · preproducción (Pedro, 19/11/2026) · constantes y utilidades comunes.

Guion: /mnt/project-files/piezas/GTA6_casi/01_fede_guion_G1.md + correcciones de 02_roma_aprobacion_G1.md (mandan).
D nominal = 16,00 s (Legacy todavía no llegó). 1080×1920, 30 fps. Convención del guion: `y` = borde superior del texto
(tinta de las letras, sin contorno), centrado en x 540 salvo indicación.
"""
import json, math, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

R = Path('/home/user/1')
T = R / 'TRABAJO/gta'
EVID = Path('/mnt/project-files/piezas/GTA6_casi/evidencia_pre/')
W, H, FPS = 1080, 1920, 30
D = 16.00
ND = round(D * FPS)                      # 480: primer cuadro del drop

# ---------------------------------------------------------------- colores (RGB 0–255)
CELESTE = (126, 178, 222)                # celeste de marca usado en las placas previas (escalada, frena)
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
CAJA_A = 0.55                            # caja negra de HUD/Tarjeta/Etiqueta (guion §4)
CAJA_R = 10

# ---------------------------------------------------------------- fuentes
SAIRA = str(R / 'scripts/fuentes/Saira-Variable.ttf')
INTER = '/usr/share/fonts/opentype/inter/'
_FC = {}


def saira(px, wght=800, wdth=100):
    """Saira variable (ejes wght 100–900, wdth 50–125). Saira no tiene ★: la estrella sale de Inter Display."""
    k = ('saira', px, wght, wdth)
    if k not in _FC:
        f = ImageFont.truetype(SAIRA, px)
        f.set_variation_by_axes([wght, wdth])
        _FC[k] = f
    return _FC[k]


def inter(px, peso='ExtraBold'):
    k = ('inter', px, peso)
    if k not in _FC:
        _FC[k] = ImageFont.truetype(f'{INTER}InterDisplay-{peso}.otf', px)
    return _FC[k]


# ---------------------------------------------------------------- línea de tiempo del guion (D = 16,00)
# (id, máster t0, t1, fuente, qué se ve)
PLANOS = [
    ('H', 0.00, 1.50, 'G2 · cuadro del contacto congelado', 'Pantalla de carga: pelota sobre la faja, Jason al fondo '
     'con la Negra. Contraste +15 %, viñeta, empuje 1,00→1,04'),
    ('G3', 1.50, 3.90, 'G3 0,10–2,50', 'Jason de espaldas en la línea de fondo; guarda una 2.ª pelota en el bolsillo y '
     'pica dos veces. ESPALDA COMPUESTA'),
    ('G2', 3.90, 6.30, 'G2 llegada → caída · rampa 100→30→100 %', 'La pelota pega en la faja (4,60), sube, queda colgada '
     'y cae del lado de Jason (5,60). Desaturado 40 % en la tarjeta'),
    ('G4', 6.30, 8.30, 'G4 0,80–2,80', 'Al ras del hoyo: la pelota rueda y frena en el borde (7,50); Jason al fondo se '
     'agarra la cabeza'),
    ('G6', 8.30, 10.00, 'G6 1,00–2,70', 'De perfil en la barra de la playa: sube temblando, el mentón queda a 2 cm y cae'),
    ('G5', 10.00, 12.60, 'G5 0,40–3,00', 'Auto negro sin insignias frena hacia el lente, queda a centímetros de la '
     'barrera, cabecea y la toca (11,85). Jason apoya la frente en el volante'),
    ('G7', 12.60, 15.00, 'G7 0,20–2,60', 'Misma cancha y encuadre que G3, sol en el horizonte. Cabizbajo; saca la 2.ª '
     'pelota (≈13,30), pica y levanta la cabeza (13,80–14,80). ESPALDA COMPUESTA'),
    ('MAPA', 15.00, 16.00, 'último cuadro de G7 + mapa dibujado', 'Cambio de personaje: el cuadro se achica en el mapa, '
     'Florida → costa bonaerense, dos picadas al negro de la tela'),
    ('7887', 16.00, 17.77, 'IMG_7887 1,90–3,67', 'DROP · abre desde el negro de la espalda (z 2,5→1,0 en 0,30 s)'),
    ('7884', 17.77, 19.17, 'IMG_7884 3,10–4,50', 'La Blanca de espaldas, completa; la ola revienta detrás'),
    ('4631', 19.17, 21.57, 'IMG_4631 2,50–4,90 (HLG→SDR mobius)', 'Las dos en la roca; la ola sube y revienta detrás'),
]


def c(t):
    """segundo del máster → cuadro (round)."""
    return int(round(t * FPS))


def rango(t0, t1):
    """cuadros visibles de un elemento [t0, t1)."""
    return range(c(t0), c(t1))


NF_PRE = ND                              # 480 cuadros antes del drop
NF_REAL = {'IMG_7887': 53, 'IMG_7884': 42, 'IMG_4631': 72, 'IMG_7895': 69}


# ---------------------------------------------------------------- curvas
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(u, p=3):
    u = clamp(u); return 1 - (1 - u) ** p


def ease_in_out(u):
    u = clamp(u); return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


# ---------------------------------------------------------------- sprites RGBA (numpy float32, alfa recta 0–1)
class Sprite:
    """imagen RGBA float32 (h, w, 4), alfa recta en [0, 1]; (ox, oy) = posición del punto de referencia dentro del
    sprite (para ubicar con la tinta del texto, no con el contorno)."""
    def __init__(self, rgba, ox=0.0, oy=0.0):
        self.a = rgba; self.ox = ox; self.oy = oy

    @property
    def w(self):
        return self.a.shape[1]

    @property
    def h(self):
        return self.a.shape[0]

    @staticmethod
    def de_pil(im, ox=0.0, oy=0.0):
        a = np.asarray(im.convert('RGBA'), np.float32) / 255.0
        return Sprite(a, ox, oy)

    def escalado(self, s, centro=None):
        """sprite escalado por s alrededor de `centro` (coordenadas del sprite; por defecto el centro)."""
        if abs(s - 1) < 1e-4:
            return self
        cx, cy = centro if centro else (self.w / 2, self.h / 2)
        nw, nh = max(1, round(self.w * s)), max(1, round(self.h * s))
        # premultiplicar para no oscurecer bordes al remuestrear
        p = self.a.copy(); p[..., :3] *= p[..., 3:4]
        im = [Image.fromarray(p[..., k]).resize((nw, nh), Image.BICUBIC) for k in range(4)]
        q = np.stack([np.asarray(x, np.float32) for x in im], -1)
        q[..., 3] = np.clip(q[..., 3], 0, 1)
        q[..., :3] = np.where(q[..., 3:4] > 1e-4, q[..., :3] / np.maximum(q[..., 3:4], 1e-4), 0)
        q[..., :3] = np.clip(q[..., :3], 0, 1)
        sx, sy = nw / self.w, nh / self.h
        return Sprite(q, self.ox * sx + (cx * (1 - sx) if False else 0), self.oy * sy)


class Lienzo:
    """capa RGBA 1080×1920 (premultiplicada mientras se compone)."""
    def __init__(self):
        self.p = np.zeros((H, W, 4), np.float32)

    def poner(self, sp, x, y, alfa=1.0, escala=1.0, ancla=None):
        """pone el sprite con su punto de referencia (ox, oy) en (x, y). escala alrededor de `ancla` (coordenadas del
        lienzo; por defecto el centro del sprite ubicado)."""
        if alfa <= 0.001:
            return
        if abs(escala - 1) > 1e-4:
            # ubicación del sprite sin escalar
            x0, y0 = x - sp.ox, y - sp.oy
            ax, ay = ancla if ancla else (x0 + sp.w / 2, y0 + sp.h / 2)
            s2 = sp.escalado(escala)
            x0 = ax + (x0 - ax) * escala; y0 = ay + (y0 - ay) * escala
            sp = s2; x, y = x0, y0
        else:
            x, y = x - sp.ox, y - sp.oy
        xi, yi = int(round(x)), int(round(y))
        a = sp.a
        x1, y1 = max(0, xi), max(0, yi)
        x2, y2 = min(W, xi + a.shape[1]), min(H, yi + a.shape[0])
        if x2 <= x1 or y2 <= y1:
            return
        s = a[y1 - yi:y2 - yi, x1 - xi:x2 - xi]
        al = s[..., 3:4] * alfa
        d = self.p[y1:y2, x1:x2]
        d[..., :3] = s[..., :3] * al + d[..., :3] * (1 - al)
        d[..., 3:4] = al + d[..., 3:4] * (1 - al)

    def poner_premult(self, rgba_p, x=0, y=0):
        """capa ya premultiplicada (h, w, 4) en (x, y)."""
        h, w = rgba_p.shape[:2]
        d = self.p[y:y + h, x:x + w]
        al = rgba_p[..., 3:4]
        d[..., :3] = rgba_p[..., :3] + d[..., :3] * (1 - al)
        d[..., 3:4] = al + d[..., 3:4] * (1 - al)

    def rgba8(self):
        """RGBA uint8 con alfa recta."""
        a = self.p[..., 3:4]
        rgb = np.where(a > 1e-4, self.p[..., :3] / np.maximum(a, 1e-4), 0)
        return np.concatenate([np.clip(rgb, 0, 1), np.clip(a, 0, 1)], -1).__mul__(255).round().astype(np.uint8)


def sobre(fondo_rgb8, capa_p):
    """compone una capa premultiplicada float (H, W, 4) sobre un RGB uint8 → RGB uint8."""
    f = fondo_rgb8.astype(np.float32) / 255
    out = capa_p[..., :3] + f * (1 - capa_p[..., 3:4])
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- texto
def texto_sprite(tramos, stroke=0, stroke_fill=(0, 0, 0), sombra=None, pad=None):
    """tramos: [(texto, fuente, color)] en la misma línea de base. Devuelve Sprite con (ox, oy) = (borde izquierdo de
    la tinta, borde superior de la tinta) sin contar contorno ni sombra, y el ancho/alto de la tinta en .ink.
    sombra = (dx, dy, radio, opacidad)."""
    asc = max(f.getmetrics()[0] for _, f, _ in tramos)
    desc = max(f.getmetrics()[1] for _, f, _ in tramos)
    adv = sum(f.getlength(t) for t, f, _ in tramos)
    pad = pad if pad is not None else stroke + (sombra[2] * 3 + max(abs(sombra[0]), abs(sombra[1])) if sombra else 0) + 4
    pad = int(math.ceil(pad))
    Wc, Hc = int(adv + 2 * pad + 4), int(asc + desc + 2 * pad + 4)
    base_y = pad + asc
    im = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0))
    mk = Image.new('L', (Wc, Hc), 0)
    d = ImageDraw.Draw(im); dm = ImageDraw.Draw(mk)
    x = pad
    for t, f, col in tramos:
        if stroke:
            d.text((x, base_y), t, font=f, fill=tuple(stroke_fill) + (255,), anchor='ls', stroke_width=stroke,
                   stroke_fill=tuple(stroke_fill) + (255,))
        x += f.getlength(t)
    x = pad
    for t, f, col in tramos:
        d.text((x, base_y), t, font=f, fill=tuple(col) + (255,), anchor='ls')
        dm.text((x, base_y), t, font=f, fill=255, anchor='ls')
        x += f.getlength(t)
    bb = mk.getbbox()
    if sombra:
        dx, dy, rad, op = sombra
        al = np.asarray(im, np.float32)[..., 3] / 255
        sh = Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(rad))
        sh = np.roll(np.roll(np.asarray(sh, np.float32) / 255 * op, dy, 0), dx, 1)
        base = np.zeros((Hc, Wc, 4), np.float32); base[..., 3] = sh
        top = np.asarray(im, np.float32) / 255
        out = np.empty_like(top)
        out[..., 3] = top[..., 3] + base[..., 3] * (1 - top[..., 3])
        out[..., :3] = np.where(out[..., 3:4] > 1e-4, top[..., :3] * top[..., 3:4] / np.maximum(out[..., 3:4], 1e-4), 0)
        sp = Sprite(out, bb[0], bb[1])
    else:
        sp = Sprite.de_pil(im, bb[0], bb[1])
    sp.ink = (bb[2] - bb[0], bb[3] - bb[1])
    sp.ink_box = bb
    return sp


def caja_sprite(w, h, alfa=CAJA_A, radio=CAJA_R, color=(0, 0, 0), escala_aa=4):
    """rectángulo redondeado con antialias."""
    s = escala_aa
    im = Image.new('L', (int(w * s), int(h * s)), 0)
    ImageDraw.Draw(im).rounded_rectangle([0, 0, int(w * s) - 1, int(h * s) - 1], radius=radio * s, fill=255)
    im = im.resize((int(w), int(h)), Image.LANCZOS)
    a = np.zeros((int(h), int(w), 4), np.float32)
    a[..., :3] = np.array(color, np.float32) / 255
    a[..., 3] = np.asarray(im, np.float32) / 255 * alfa
    return Sprite(a, 0, 0)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, **kw)
    if r.returncode:
        raise RuntimeError(' '.join(map(str, cmd)) + '\n' + r.stderr.decode(errors='replace')[-3000:])
    return r.stdout


def guardar_json(obj, p):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    return p
