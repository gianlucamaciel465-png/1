# Video de marca A para @rocce.ar «¿Cómo está hecho este nombre?» (28/11/2026). Guion de Fede (04_fede_guiones.md, pieza 4)
# con la versión de Roma (06_roma_revision_guiones.md, Marca A): frío o caliente sobre la técnica del nombre de la espalda;
# giro «no está estampado: es jean» (CAMPANA_ACTUAL, línea 41: ROCCÉ en parche de denim azul con borde/pespunte claro).
# Material real: IMG_5325 (26/11, tramos nuevos: 13,30–15,59 macro a 1/1,4 de velocidad y 4,60–5,80 entera; FOMO usó el comienzo, «Esto no se
# compra» 10,0–13,3, las historias del 27/11 0,5–4,5 y Muslera 15,6–), IMG_8004 (4K: recorte nativo del parche), IMG_7857,
# IMG_4530 y IMG_3375 (HLG → SDR, blanco neutro), IMG_5361 (placa sin número) e IMG_7896 ×1,16 para el cierre.
# Cambios de edición (Pedro): filas 2–5 de 1,0 s (más ritmo); grilla de 100 BPM desde el giro (cortes cada 2 tiempos); el fit
# check queda en 4 planos de 1,2 s (sale IMG_7859: horizontal, la ventana del 52 % achica la prenda).
# Sonido: diseño sintetizado + mar real (IMG_7859, IMG_7896). MUSICA=0 exporta la versión sin música (para un sonido de IG).
# Uso: python3 scripts/jornada/marca_a.py SALIDA.mp4
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from historia import *

GL = os.path.join(RAIZ, "TRABAJO/fomo/gl")
OR = os.path.join(RAIZ, "ORIGINALES")
S5325 = os.path.join(GL, "sdr_5325_full.mp4")       # IMG_5325 ya en SDR (receta de CLAUDE.md), 1080×1920
S5361 = os.path.join(GL, "sdr_5361.mp4")
V8004 = os.path.join(OR, "IMG_8004.mov")             # 4K vertical (2160×3840 tras la rotación)
V7857 = os.path.join(OR, "IMG_7857.mov")
V7859 = os.path.join(OR, "IMG_7859.mov")
V7896 = os.path.join(OR, "IMG_7896.mov")
V4530 = os.path.join(OR, "IMG_4530.mov")             # HLG
V3375 = os.path.join(OR, "IMG_3375.mov")             # HLG
LOGO = os.path.join(RAIZ, "LOGO/rocce_logo.png")
salida = sys.argv[1]
MUSICA = os.environ.get("MUSICA", "1") != "0"

TM = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
      "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
NEUTRO = "colorchannelmixer=rr=1.05:gg=1.03:bb=0.92"   # CAMPANA: la blanca de 4530 queda fría tras el tonemap
NEUTRO_3375 = "colorchannelmixer=rr=0.95:gg=1.03:bb=1.14"  # 3375 (luz cálida de interior) sale crema: blanco medido 224/220/221

BEAT = 0.6
G = 5.40                                             # giro: arranca la grilla de 100 BPM
FILAS = [("r1", 1.20), ("r2", 1.00), ("r3", 1.00), ("r4", 1.00), ("r5", 1.20),
         ("r6", 2 * BEAT), ("r7", 2 * BEAT), ("f1", 2 * BEAT), ("f2", 2 * BEAT), ("f3", 2 * BEAT), ("f4", 2 * BEAT),
         ("cta", 4 * BEAT + 0.3)]
T0 = {}
t = 0.0
for k, d in FILAS:
    T0[k] = round(t, 3); t += d
assert abs(T0["r6"] - G) < 1e-6
DUR = round(t, 3)
N = cs(DUR)
D = dict(FILAS)


def clip_src(nombre, src, t0, crop=None, vf="", lento=1.0, osc=None):
    """como historia.clip, pero el recorte va en píxeles de la fuente (aprovecha el 4K) y admite filtros previos."""
    def f(c, k):
        if k == 0 or nombre not in estado:
            if nombre in estado: estado[nombre].cerrar()
            pre = vf
            if lento != 1.0:
                pre = (pre + "," if pre else "") + f"setpts={lento}*PTS,framerate=fps=30"
            cr = f"{crop[0]}:{crop[1]}:{crop[2]}:{crop[3]}" if crop else None
            estado[nombre] = Lector(src, t0, W, H, crop=cr, uno_a_uno=False, vf_pre=pre)
        a = estado[nombre].cuadro().copy()
        if osc: a = oscurecer(a, *osc)
        return a
    return f


# ---------- termómetro (dibujado sobre el cuadro, debajo de los textos) ----------
FRIO, CALOR = np.array(CEL, float), np.array((255, 122, 89), float)
NIVELES = [(0.0, 0.10), (T0["r2"] + 0.40, 0.14), (T0["r3"] + 0.40, 0.10), (T0["r4"] + 0.40, 0.62),
           (T0["r5"] + 0.40, 0.86), (G, 1.0)]
TX, TY0, TY1, TW = 70, 560, 1180, 34                 # tubo a la izquierda (x 70–104), lejos del parche


def nivel(tt):
    v = NIVELES[0][1]
    for (ta, va), (tb, vb) in zip(NIVELES, NIVELES[1:]):
        if tt >= tb: v = vb; continue
        if tt >= ta: v = va
    # transición de 0,2 s hacia cada valor nuevo
    for (ta, va), (tb, vb) in zip(NIVELES, NIVELES[1:]):
        if tb <= tt < tb + 0.2:
            return va + (vb - va) * suave((tt - tb) / 0.2)
    return v


def termo(img, c):
    tt = c / FPS
    if tt >= T0["r7"] + 0.15: return img
    al = 1.0 if tt < T0["r7"] else 1 - (tt - T0["r7"]) / 0.15
    v = nivel(tt)
    col = tuple(int(x) for x in FRIO + (CALOR - FRIO) * min(1.0, v / 0.9))
    if tt >= G:                                      # hierve: late con el golpe
        col = tuple(CALOR.astype(int))
    im = Image.fromarray(img).convert("RGBA")
    capa = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    d.rounded_rectangle([TX - 6, TY0 - 6, TX + TW + 6, TY1 + 30], radius=(TW + 12) // 2, fill=(0, 0, 0, int(110 * al)))
    d.rounded_rectangle([TX, TY0, TX + TW, TY1], radius=TW // 2, outline=(255, 255, 255, int(235 * al)), width=4)
    d.ellipse([TX - 14, TY1 - 10, TX + TW + 14, TY1 + 52], fill=col + (int(255 * al),), outline=(255, 255, 255, int(235 * al)), width=4)
    top = TY1 - (TY1 - TY0 - 14) * v
    d.rounded_rectangle([TX + 8, top, TX + TW - 8, TY1 + 10], radius=(TW - 16) // 2, fill=col + (int(255 * al),))
    im.alpha_composite(capa)
    return np.array(im.convert("RGB"))


def con_termo(f):
    return lambda c, k: termo(f(c, k), c)


OSC = (760, 0.6)                                     # degradé oscuro arriba (texto blanco sobre la remera blanca)
SEG = [
    seg(T0["r1"], T0["r4"], con_termo(clip_src("mac", S5325, 13.30, lento=1.4)), "mac"),
    seg(T0["r4"], T0["r5"], con_termo(clip_src("r4", V8004, 2.40, crop=(1080, 1920, 200, 1600))), "r4"),
    seg(T0["r5"], T0["r6"], con_termo(clip_src("r5", V8004, 3.40, crop=(720, 1280, 900, 1720))), "r5"),
    seg(T0["r6"], T0["r7"], con_termo(clip_src("r6", S5325, 4.60, osc=OSC)), "r6"),
    seg(T0["r7"], T0["f1"], con_termo(clip_src("r7", V7857, 0.90, osc=(700, 0.55))), "r7"),
    seg(T0["f1"], T0["f2"], clip_src("f1", V7857, 3.00), "f1"),
    seg(T0["f2"], T0["f3"], clip_src("f2", V4530, 1.00, vf=TM + "," + NEUTRO), "f2"),
    seg(T0["f3"], T0["f4"], clip_src("f3", V3375, 0.60, vf=TM + "," + NEUTRO_3375), "f3"),
    seg(T0["f4"], T0["cta"], clip_src("f4", S5361, 0.10), "f4"),
    seg(T0["cta"], N, clip_src("cta", V7896, 4.20, crop=(1862, 3310, 52, 269), osc=(820, 0.62)), "cta"),
]

T = []


def txt(a, b, capa, y=0, x=None, pop=1.0, entra=0, sale=True):
    d = dict(c0=cs(a) if isinstance(a, float) else a, c1=cs(b) if isinstance(b, float) else b, capa=capa, y=y, pop=pop,
             entra=entra, sale=sale)
    if x is not None: d["x"] = x
    T.append(d)


def caja_ok(lineas, size=84, **kw):
    f = fuente("disp_xb", size)
    while max(f.getlength(s) for s in lineas) > 800: size -= 2; f = fuente("disp_xb", size)
    return caja(lineas, size, **kw)


def pastilla(s, fondo, tinta, size=60):
    f = fuente("disp_xb", size)
    tw = sum(f.getlength(ch) + 4 for ch in s) - 4
    bw, bh = int(tw + 56), int(size * 1.6)
    img = Image.new("RGBA", (W, bh + 24), (0, 0, 0, 0))
    x0 = (W - bw) // 2
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0, 10, x0 + bw, 10 + bh], radius=bh // 2, fill=(0, 0, 0, 110))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, 4, x0 + bw, 4 + bh], radius=bh // 2, fill=fondo + (255,))
    x = x0 + 28
    for ch in s:
        d.text((x, 4 + (bh - size * 1.22) / 2), ch, font=f, fill=tinta + (255,)); x += f.getlength(ch) + 4
    return img


FRIO_T, CAL_T, MUY_T = tuple(CEL), (255, 150, 110), (255, 104, 72)

# la gran pregunta va en una tarjeta de juego DEBAJO de las letras (arriba tapaba el nombre que se pregunta):
# en el macro las letras quedan entre y 0 y 905 y en los recortes de 8004 entre 377 y 765.
PANEL_Y0, PANEL_Y1, PANEL_X0, PANEL_X1 = 925, 1345, 150, 930


def panel():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([PANEL_X0, PANEL_Y0 + 8, PANEL_X1, PANEL_Y1 + 8], radius=34, fill=(0, 0, 0, 90))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(img).rounded_rectangle([PANEL_X0, PANEL_Y0, PANEL_X1, PANEL_Y1], radius=34, fill=NOCHE + (212,))
    return img


txt(T0["r1"], T0["r6"], panel(), y=0, x=0, sale=False)
txt(T0["r1"], T0["r6"], titular(["¿CÓMO ESTÁ HECHO", "ESTE NOMBRE?"], size=64, ancho=700), y=932, pop=1.08, sale=False)
txt(T0["r1"] + 0.35, T0["r2"], pastilla("FRÍO", FRIO_T, NOCHE, size=56), y=1215, pop=1.15)
JUEGO = [("r2", "¿ESTAMPADO?", "FRÍO", FRIO_T, NOCHE), ("r3", "¿VINILO?", "FRÍO", FRIO_T, NOCHE),
         ("r4", "¿TELA?", "CALIENTE", CAL_T, NOCHE), ("r5", "¿JEAN?", "MUY CALIENTE", MUY_T, (255, 255, 255))]
for k, preg, resp, fo, ti in JUEGO:
    fin = T0[k] + D[k]
    txt(T0[k], fin, titular([preg], size=70, clave=0, ancho=700), y=1085, pop=1.12, sale=False)
    txt(T0[k] + 0.40, fin, pastilla(resp, fo, ti, size=56), y=1215, pop=1.2, sale=(k != "r5"))
# giro
txt(G, T0["r7"], titular(["¡TE QUEMASTE!"], size=118), y=300, pop=1.25)
txt(G + 0.30, T0["r7"], caja_ok(["ROCCÉ: PARCHE DE JEAN", "CON PESPUNTE."], 64), y=460, pop=1.1)
# reenganche
txt(T0["r7"], T0["f1"], titular(["¿Y PUESTA?"], size=110), y=300, pop=1.15)

# cierre: ficha del logo + producto + llamada
lg = Image.open(LOGO).convert("RGB")
LS = 168
lg = lg.resize((LS, LS), Image.LANCZOS)
ficha = Image.new("RGBA", (W, LS + 30), (0, 0, 0, 0))
m = Image.new("L", (LS, LS), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, LS - 1, LS - 1], radius=int(LS * 0.12), fill=255)
sh = Image.new("RGBA", ficha.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle([(W - LS) // 2, 12, (W + LS) // 2, 12 + LS], radius=int(LS * 0.12), fill=(0, 0, 0, 120))
ficha = Image.alpha_composite(ficha, sh.filter(ImageFilter.GaussianBlur(10)))
ficha.paste(lg, ((W - LS) // 2, 4), m)
txt(T0["cta"], N, ficha, y=270, x=0, entra=4, sale=False)
txt(T0["cta"] + 0.15, N, titular(["FOUNDERS PRIVÉE"], size=78), y=470, entra=4, sale=False)
fs = fuente("serif_i", 50)
sub = capa_texto(["Blanca · ROCCÉ en parche de jean"], "serif_i", 50, color=(235, 242, 250), sombra=0.85, radio_sombra=10)
txt(T0["cta"] + 0.30, N, sub, y=570, entra=4, sale=False)
lk = Image.new("RGBA", (W, 60), (0, 0, 0, 0))
fl = fuente("inter_sb", 34); s_ = "LINK EN LA BIO · rocce.shop"
x = (W - (fl.getlength(s_) + 3 * (len(s_) - 1))) / 2
d_ = ImageDraw.Draw(lk)
for ch in s_:
    d_.text((x + 2, 12), ch, font=fl, fill=(0, 0, 0, 150)); d_.text((x, 10), ch, font=fl, fill=CEL + (255,)); x += fl.getlength(ch) + 3
txt(T0["cta"] + 0.45, N, lk, y=660, x=0, entra=4, sale=False)


# ---------- audio ----------
def sonido(x, dur):
    rng = np.random.default_rng(28)
    x += np.convolve(rng.normal(0, 1, len(x)), np.ones(80) / 80, "same") * 0.006
    # juego: tic en cada pregunta, respuesta fría (grave) o caliente (sube)
    dron(x, 0.0, G, f=49, g=0.03)
    tic(x, 0.02, 0.14, 1500)
    golpe(x, T0["r1"] + 0.35, 0.16, f0=60, caida=0.15)
    for k, _, resp, _, _ in JUEGO:
        tic(x, T0[k], 0.16, 1900)
        if resp == "FRÍO":
            golpe(x, T0[k] + 0.40, 0.18, f0=58, caida=0.15); tic(x, T0[k] + 0.40, 0.06, 900)
        else:
            barrido(x, T0[k] + 0.18, 0.24, 0.07 if resp == "CALIENTE" else 0.10, 400, 3200)
            golpe(x, T0[k] + 0.40, 0.24, f0=52, caida=0.25); brillo(x, T0[k] + 0.41, 0.04 if resp == "CALIENTE" else 0.07, 0.8)
    for t_ in np.arange(T0["r5"] + 0.5, G - 0.25, 0.125): tic(x, t_, 0.05, 2400)       # se acelera antes del giro
    i0, i1 = int((G - 0.2) * SR), int((G - 0.005) * SR); x[i0:i1] *= 0.08                # casi silencio
    golpe(x, G, 0.55, f0=42, caida=0.6); brillo(x, G + 0.02, 0.09, 1.6)
    if MUSICA:
        acordes = [[220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [130.8, 196.0, 261.6], [196.0, 246.9, 293.7]]
        t_ = G; i = 0
        while t_ < T0["cta"] + 4 * BEAT - 1e-6:
            colchon(x, t_, t_ + 2 * BEAT, acordes[i % 4], 0.05, ataque=0.03, suelta=0.25); i += 1; t_ += 2 * BEAT
        for b in np.arange(G, T0["cta"] + 4 * BEAT - 1e-6, BEAT):
            golpe(x, b, 0.32, f0=50, caida=0.22)
            tic(x, b + BEAT / 2, 0.06, 6000)
        for b in [T0["f1"], T0["f2"], T0["f3"], T0["f4"], T0["cta"]]:
            barrido(x, b - 0.18, 0.18, 0.05, 2500, 500)
    else:
        for b in [T0["f1"], T0["f2"], T0["f3"], T0["f4"], T0["cta"]]:
            golpe(x, b, 0.25, f0=50, caida=0.25)
    golpe(x, T0["cta"], 0.35, f0=46, caida=0.5); brillo(x, T0["cta"] + 0.05, 0.06, 1.2)
    i0 = int((DUR - 0.45) * SR); x[i0:] *= np.linspace(1, 0, len(x) - i0)               # fundido final ≤ 0,5 s


MAR = [(T0["r7"], audio_clip(V7859, 1.0, T0["cta"] - T0["r7"], gan=0.9, fade=0.3)),
       (T0["cta"], audio_clip(V7896, 4.20, DUR - T0["cta"], gan=1.6, fade=0.2))]

print("duración", DUR, T0, "música" if MUSICA else "sin música")
render(salida, N, SEG, T, sonido, [], techo=0.8, extra_audio=MAR)
