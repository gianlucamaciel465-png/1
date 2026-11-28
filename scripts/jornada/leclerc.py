# Reel Roccé Life «Leclerc: ¿le echa la culpa?» (28/11/2026). Guion de Fede v01 (04_fede_guiones.md, pieza 3) con los cambios
# de Roma (06_roma_revision_guiones.md): giro en «I'll accept the blame», L3 a tamaño nativo, sin «desde 2019», reenganche con
# L1 9,1–10,9 (sin Louis Vuitton) y sin «HOY». Cambios de edición (Pedro), por tiempo y por redundancia:
#   - sale la fila 9 («Lo único que no me gusta es que cuestionen mi integridad…», 5,6 s): decía lo mismo que el giro 2 y lo
#     adelantaba; su encabezado «SEMANA DE QATAR · LE CUESTIONAN LA LEALTAD» pasa a la fila 10;
#   - giro 2 = «the question mark» (L4 34,28–35,08, pantalla dividida) + «that hurts me more than anything else» (37,50–39,50,
#     primer plano): el corte de audio cae en el cambio de plano de la fuente (36,92); la tarjeta lleva puntos suspensivos;
#   - fila 8 termina en 57,92 (v02, Roma doc 14): desde 57,93 la mitad de arriba pierde color (saturación −2 % a 57,93,
#     −7 % a 57,97, −10 % a 58,00), funde a Hamilton;
#   - v02 (Roma doc 14): la fila 7 termina en «team» (37,16, hueco antes de «Again»): «Otra vez» era una muletilla de la
#     frase siguiente; en r5–r8 el descargo va en 2 renglones sin placa ARRIBA de las tarjetas (sobre el pecho de Leclerc):
#     debajo tapaba la cara de Hamilton, y en r5 no entra debajo (la tarjeta termina en 1122 y las cejas están en 1215).
# Tiempos por envolvente de voz (huecos entre palabras) y transcripción por ventanas; cortes de imagen por diferencia de cuadros.
# Audio: voces originales (radio de L1, relator de L2, Leclerc en L3 y L4) normalizadas a −20 dBFS RMS; el resto es diseño
# sintetizado. Sin voz en off.
# Uso: python3 scripts/jornada/leclerc.py SALIDA.mp4   (SOLO_AUDIO=1 mide la mezcla sin renderizar)
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from historia import *

CL = os.path.join(RAIZ, "TRABAJO/jornada3/clips")
L1 = os.path.join(CL, "f1_7710491362512096534.mp4")   # radio de la Q2 (casco) + las dos Ferrari en pista
L2 = os.path.join(CL, "f1_7710891950127238422.mp4")   # el choque (aérea y dos cámaras a bordo)
L3 = os.path.join(CL, "f1_7711027707898826006.mp4")   # Leclerc después de la carrera (pantalla dividida con Hamilton)
L4 = os.path.join(CL, "f1_7712582746299747606.mp4")   # semana de Qatar: responde a las críticas
salida = sys.argv[1]

# rótulos incrustados de la fuente (medidos a resolución completa, con margen en las tarjetas que los tapan)
VISOR_L1 = (269, 678, 809, 999)      # «Are we through or not?» / «No, we are out.» (rojo y blanco) 0,6–3,45
BOTH_L1 = (250, 1190, 830, 1385)     # «BOTH Ferraris out in Q2 🤯» 0–3,8
CRASH_L2 = (110, 490, 970, 556)      # «The Ferraris crash again 😱» 0–7,6
SUB_L3 = (160, 928, 920, 988)        # subtítulo rojo en la división (L3 y L4 dividida 940–986)
DEBRIEF_L3 = (160, 1044, 920, 1108)  # «Ferrari debrief post-race» 0–3,5
SUB_L4_PP = (150, 1410, 930, 1464)   # subtítulo rojo del primer plano de L4

FILAS = [("r1", 1.98), ("r2", 1.37), ("r3", 2.50), ("r4", 1.40), ("r5", 3.78), ("r6", 4.04), ("r7", 1.76), ("r8", 1.20),
         ("r10", 2.96), ("r11a", 0.80), ("r11b", 2.00), ("r12", 1.80), ("r13", 1.30)]
T0 = {}
t = 0.0
for k, d in FILAS:
    T0[k] = round(t, 3); t += d
DUR = round(t, 3)
N = cs(DUR)
D = dict(FILAS)

SEG = [
    seg(T0["r1"], T0["r3"], clip("r1", L1, 0.10), "r1"),           # radio: toma continua 0,10–3,45
    seg(T0["r3"], T0["r4"], clip("r3", L2, 3.85), "r3"),
    seg(T0["r4"], T0["r5"], clip("r4", L2, 15.00), "r4"),
    seg(T0["r5"], T0["r6"], clip("r5", L3, 0.00), "r5"),
    seg(T0["r6"], T0["r7"], clip("r6", L3, 21.56), "r6"),
    seg(T0["r7"], T0["r8"], clip("r7", L3, 35.40), "r7"),
    seg(T0["r8"], T0["r10"], clip("r8", L3, 56.72), "r8"),
    seg(T0["r10"], T0["r11a"], clip("r10", L4, 17.70), "r10"),
    seg(T0["r11a"], T0["r11b"], clip("r11a", L4, 34.28), "r11a"),
    seg(T0["r11b"], T0["r12"], clip("r11b", L4, 37.50), "r11b"),
    seg(T0["r12"], T0["r13"], clip("r12", L1, 9.10), "r12"),
    seg(T0["r13"], N, negro),
]

T = []


def txt(a, b, capa, y=0, x=None, pop=1.0, entra=0, sale=True):
    d = dict(c0=cs(a) if isinstance(a, float) else a, c1=cs(b) if isinstance(b, float) else b, capa=capa, y=y, pop=pop,
             entra=entra, sale=sale)
    if x is not None: d["x"] = x
    T.append(d)


def chico(s, color=CEL, size=40):
    while fuente("disp_b", size).getlength(s) > 840: size -= 1
    return capa_texto([s], "disp_b", size, color=color, sombra=0.85, radio_sombra=10)


def caja_ok(lineas, size=84, **kw):
    f = fuente("disp_xb", size)
    while max(f.getlength(s) for s in lineas) > 800: size -= 2; f = fuente("disp_xb", size)
    return caja(lineas, size, **kw)


def tarjeta(lineas, tapa, clave=None, encabezado=None, size=56, ancho=880, fk="serif_i"):
    """tarjeta azul noche opaca (radio 18) que tapa el rectángulo `tapa` (x0, y0, x1, y1) con ≥ 14 px de margen;
    texto centrado (serif cursiva blanca, `clave` en celeste). Devuelve (capa a todo el ancho, y de la capa)."""
    fi = fuente(fk, size)
    while max(fi.getlength(l) for l in lineas) > ancho - 80: size -= 2; fi = fuente(fk, size)
    fe = fuente("inter_sb", 30)
    lh = int(size * 1.14)
    alto_txt = (52 if encabezado else 0) + lh * len(lineas)
    x0t, y0t, x1t, y1t = tapa
    bw = max(ancho, int(max(fi.getlength(l) for l in lineas)) + 80)
    bh = max(alto_txt + 64, (y1t - y0t) + 28)
    bx = (W - bw) // 2
    by = int((y0t + y1t) / 2 - bh / 2)
    assert bx <= x0t - 14 and bx + bw >= x1t + 14 and by <= y0t - 14 and by + bh >= y1t + 14, (lineas, bx, by, bw, bh, tapa)
    assert by >= 250 and by + bh <= 1350, (lineas, by, bh)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([bx, by + 8, bx + bw, by + bh + 8], radius=18, fill=(0, 0, 0, 120))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=18, fill=NOCHE + (255,))
    y = by + (bh - alto_txt) / 2 - size * 0.12
    if encabezado:
        x = (W - (fe.getlength(encabezado) + 2 * (len(encabezado) - 1))) / 2
        assert x >= 60, encabezado
        for ch in encabezado:
            d.text((x, y), ch, font=fe, fill=CEL + (255,)); x += fe.getlength(ch) + 2
        y += 52
    for l in lineas:
        x = (W - fi.getlength(l)) / 2
        if clave and clave in l:
            a, b = l.split(clave, 1)
            d.text((x, y), a, font=fi, fill=(255, 255, 255, 255)); x += fi.getlength(a)
            d.text((x, y), clave, font=fi, fill=CEL + (255,)); x += fi.getlength(clave)
            d.text((x, y), b, font=fi, fill=(255, 255, 255, 255))
        else:
            d.text((x, y), l, font=fi, fill=(255, 255, 255, 255))
        y += lh
    return img


def banda(y0, y1, lineas=None, size=62):
    """banda azul noche opaca a todo el ancho de y0 a y1, con borde suave fuera de ese tramo; texto centrado opcional."""
    a = np.zeros((H, W, 4), np.uint8)
    a[..., :3] = NOCHE
    yy = np.arange(H)
    alfa = np.where((yy >= y0) & (yy <= y1), 255, 0).astype(np.float32)
    g = (yy >= y0 - 30) & (yy < y0); alfa[g] = 255 * (yy[g] - (y0 - 30)) / 30
    g = (yy > y1) & (yy <= y1 + 24); alfa[g] = 255 * (1 - (yy[g] - y1) / 24)
    a[..., 3] = alfa[:, None].astype(np.uint8)
    img = Image.fromarray(a, "RGBA")
    if lineas:
        f = fuente("disp_xb", size)
        while max(f.getlength(s) for s in lineas) > 800: size -= 2; f = fuente("disp_xb", size)
        lh = int(size * 1.1)
        y = (y0 + y1) / 2 - lh * len(lineas) / 2 - size * 0.08
        d = ImageDraw.Draw(img)
        for s in lineas:
            d.text(((W - f.getlength(s)) / 2, y), s, font=f, fill=(255, 255, 255, 255)); y += lh
    return img


# descargo (40 px, x 52–≤950) todo el video
DESC = capa_texto(["Roccé no tiene relación con Charles", "Leclerc, Lewis Hamilton, Ferrari ni la",
                   "Fórmula 1."], "inter_m", 40, color=(236, 236, 236), sombra=0.9, radio_sombra=8,
                  alinear="l", ancho=W, interlinea=1.15)
DESC = fondo_suave(DESC)          # placa oscura difusa: se lee también sobre medias, camisetas y cielo blancos
assert max(fuente("inter_m", 40).getlength(s) for s in ["Roccé no tiene relación con Charles",
                                                         "Leclerc, Lewis Hamilton, Ferrari ni la"]) + 52 <= 950
Y_DESC = 1244

# bandas bajas opacas (debajo del descargo): «BOTH Ferraris out in Q2» en L1 y el subtítulo del primer plano de L4
BB_L1 = banda(BOTH_L1[1] - 40, BOTH_L1[3] + 30)
assert BOTH_L1[1] - 40 <= Y_DESC - 28
txt(T0["r1"], T0["r3"], BB_L1, y=0, x=0, sale=False)
BB_L4 = banda(1185, 1480)
assert 1185 <= SUB_L4_PP[1] - 14 and 1480 >= SUB_L4_PP[3] + 14
txt(T0["r11b"], T0["r12"], BB_L4, y=0, x=0, sale=False)

txt(0, T0["r5"], DESC, y=Y_DESC, x=52, sale=False)
txt(T0["r10"], T0["r13"], DESC, y=Y_DESC, x=52, sale=False)
# r5–r8 (pantalla dividida): 2 renglones sin placa, arriba de las tarjetas, para dejar libre la cara de Hamilton
DESC2 = capa_texto(["Roccé no tiene relación con Charles Leclerc,", "Lewis Hamilton, Ferrari ni la Fórmula 1."], "inter_m", 40,
                   color=(240, 240, 240), sombra=0.9, radio_sombra=8, alinear="l", ancho=W, interlinea=1.15)
assert fuente("inter_m", 40).getlength("Roccé no tiene relación con Charles Leclerc,") + 52 <= 950
DESC2 = fondo_suave(DESC2, alfa=0.38)      # placa suave: sobre el logo azul y blanco del pecho de Leclerc «no tiene» se cortaba a 360 px
_a = np.array(DESC2)[..., 3]; _ys = np.nonzero((_a > 200).any(axis=1))[0]
TOPE_TARJETAS = 867                        # la tarjeta más alta de r5–r8 (r6) arranca en y 867
Y_DESC2 = TOPE_TARJETAS - 16 - int(_ys.max())
txt(T0["r5"], T0["r10"], DESC2, y=Y_DESC2, x=52, sale=False)
# crédito a la derecha: a la izquierda, en y≈245–280, está el logo de F1 de la fuente
CRED = rotulo_fuente("Video: F1")
txt(0, T0["r13"], CRED, y=252, x=int(940 - fuente("inter_sb", 28).getlength("Video: F1")), sale=False)

# 1 · apuesta: la radio en la Q2
G_NO = T0["r2"] + 0.02
txt(0, T0["r2"], caja_ok(["LECLERC"], 64, chico="CLASIFICACIÓN DE LAS VEGAS", size_chico=34), y=300)
txt(0, T0["r2"], tarjeta(["—¿Pasamos o no?"], VISOR_L1, encabezado="RADIO DE FERRARI", size=74, ancho=700), sale=False)
# 2 · giro corto
txt(T0["r2"], T0["r3"], tarjeta(["—No. Estamos afuera."], VISOR_L1, encabezado="RADIO DE FERRARI", size=74, ancho=700),
    sale=False)
txt(T0["r2"], T0["r3"], caja_ok(["LAS DOS FERRARI, AFUERA EN Q2."], 64), y=300, pop=1.12)
# 3 · la apuesta sube: el choque, con la banda sobre el rótulo en inglés
txt(T0["r3"], T0["r4"], banda(CRASH_L2[1] - 50, CRASH_L2[3] + 50, ["Y EN LA CARRERA,", "CHOCA CON SU COMPAÑERO."], 62),
    y=0, x=0, sale=False)
# 4 · gran pregunta
txt(T0["r4"], T0["r5"], caja_ok(["¿LE VA A ECHAR LA CULPA", "A HAMILTON?"], 76), y=858, entra=2)
# 5 · evidencia: la sanción, con su voz
txt(T0["r5"], T0["r6"], tarjeta(["“Hoy me consideraron culpable.", "Me dieron 10 segundos de penalización.”"],
                                (DEBRIEF_L3[0], SUB_L3[1], DEBRIEF_L3[2], DEBRIEF_L3[3]), clave="culpable", size=52),
    sale=False)
G_10 = T0["r5"] + 2.55                     # «10 seconds» (L3 2,54)
txt(G_10, T0["r6"], etiqueta("+10 s", 46), y=668, pop=1.25)      # entre el mentón (≈620) y el descargo
# 6 · evidencia a favor de que lo culpa
txt(T0["r6"], T0["r7"], tarjeta(["“No creo que Lewis, con el ángulo de su auto,", "me haya visto en los espejos.”"], SUB_L3,
                                clave="Lewis", size=52), sale=False)
# 7 · pista
txt(T0["r7"], T0["r8"], tarjeta(["“Me siento muy mal por el EQUIPO.”"], SUB_L3, clave="EQUIPO", size=56),
    sale=False)
# 8 · giro
G_CULPA = T0["r8"] + 0.08                  # «I'll» (L3 56,80)
txt(T0["r8"], T0["r10"], tarjeta(["“Acepto la culpa.”"], SUB_L3, clave="culpa", size=84), pop=1.15, sale=False)   # desde el cuadro 0: tapa el subtítulo
# 10 · reenganche: semana de Qatar
txt(T0["r10"], T0["r11a"], tarjeta(["“Voy a hacer todo para volver", "a llevar a Ferrari arriba.”"], SUB_L3,
                                   encabezado="SEMANA DE QATAR · LE CUESTIONAN LA LEALTAD", size=54), sale=False)
# 11 · giro 2
txt(T0["r11a"], T0["r12"], tarjeta(["“Ese signo de pregunta…", "me duele más que cualquier otra cosa.”"], SUB_L3,
                                   clave="me duele más", size=54), sale=False)
# 12 · reenganche
txt(T0["r12"], T0["r13"], chico("GP DE QATAR · CARRERA: DOM 29/11, 13:00 (ARG)", size=36), y=318)
txt(T0["r12"], T0["r13"], titular(["¿LO DEMUESTRA", "EN LA PISTA?"], size=96, clave=1), y=372, pop=1.1)
# 13 · firma
txt(T0["r13"], N, placa_firma(None), y=0, x=0, sale=False, entra=2)
txt(T0["r13"], N, DESC, y=Y_DESC, x=52, sale=False)

# ---------- audio ----------
VOCES = [(T0["r1"], audio_clip(L1, 0.10, T0["r3"] - T0["r1"], fade=0.04)),        # radio + motor
         (T0["r3"], audio_clip(L2, 3.85, D["r3"], fade=0.05)),                      # «The Ferraris make contact»
         (T0["r5"], audio_clip(L3, 0.00, D["r5"], fade=0.04)),
         (T0["r6"], audio_clip(L3, 21.56, D["r6"], fade=0.04)),
         (T0["r7"], audio_clip(L3, 35.40, D["r7"], fade=0.04)),
         (T0["r8"], audio_clip(L3, 56.72, D["r8"], fade=0.04)),
         (T0["r10"], audio_clip(L4, 17.70, D["r10"], fade=0.04)),
         (T0["r11a"], audio_clip(L4, 34.28, D["r11a"], fade=0.03)),
         (T0["r11b"], audio_clip(L4, 37.50, D["r11b"], fade=0.04))]
for i, (tv, a) in enumerate(VOCES):
    r = np.sqrt((a ** 2).mean()) + 1e-12
    VOCES[i] = (tv, a * (10 ** (-20 / 20) / r))
for (a_, va), (b_, _) in zip(VOCES, VOCES[1:]):
    assert a_ + len(va) / SR <= b_ + 1e-3


def sonido(x, dur):
    rng = np.random.default_rng(16)
    x += np.convolve(rng.normal(0, 1, len(x)), np.ones(80) / 80, "same") * 0.008
    dron(x, 0.0, T0["r5"], f=44, g=0.035)
    for t_ in np.arange(0.0, T0["r2"], 0.5): golpe(x, t_, 0.14, f0=50, caida=0.16)
    golpe(x, G_NO, 0.35, f0=44, caida=0.45); brillo(x, G_NO + 0.02, 0.05)
    barrido(x, T0["r3"] - 0.30, 0.32, 0.06, 2400, 300)
    golpe(x, T0["r3"], 0.3, f0=46, caida=0.35)
    for t_ in np.arange(T0["r3"] + 0.5, T0["r4"], 0.5): golpe(x, t_, 0.10, f0=50, caida=0.15)
    for t_ in np.arange(T0["r4"], T0["r5"] - 0.1, 0.25):
        golpe(x, t_, 0.10 + 0.08 * (t_ - T0["r4"]) / D["r4"], f0=54, caida=0.10)
    barrido(x, T0["r4"] + 0.5, D["r4"] - 0.55, 0.05, 300, 2400)
    i0, i1 = int((T0["r5"] - 0.08) * SR), int(T0["r5"] * SR); x[i0:i1] *= 0.2
    dron(x, T0["r5"], T0["r8"], f=44, g=0.06)
    dron(x, T0["r6"], T0["r8"], f=55, g=0.07)
    colchon(x, T0["r6"], T0["r7"], [110.0, 130.8, 164.8], 0.09, ataque=0.4, suelta=0.2)
    for t_ in np.arange(T0["r5"], T0["r7"], 0.5): golpe(x, t_, 0.14, f0=48, caida=0.16)       # pulso bajo bajo la voz
    tic(x, G_10, 0.12)
    colchon(x, T0["r7"], T0["r8"], [146.8, 174.6, 220.0, 293.7], 0.16, ataque=0.2, suelta=0.15)
    i0, i1 = int((T0["r8"] - 0.20) * SR), int((G_CULPA - 0.01) * SR); x[i0:i1] *= 0.1          # casi silencio antes del giro
    golpe(x, G_CULPA, float(os.environ.get("G_CULPA", 0.25)), f0=40, caida=0.45); brillo(x, G_CULPA + 0.02, 0.04)
    golpe(x, T0["r10"], 0.3, f0=46, caida=0.4)
    colchon(x, T0["r10"], T0["r11a"], [164.8, 246.9, 329.6, 415.3], 0.05, ataque=0.3, suelta=0.1)
    for t_ in np.arange(T0["r10"], T0["r11a"], 0.5): golpe(x, t_, 0.10, f0=50, caida=0.15)
    i0, i1 = int((T0["r11a"] - 0.05) * SR), int(T0["r12"] * SR); x[i0:i1] *= 0.15               # giro 2: la música cae a casi nada
    dron(x, T0["r11a"], T0["r12"], f=41, g=0.10)
    golpe(x, T0["r12"], 0.32, f0=46, caida=0.35)
    for t_ in np.arange(T0["r12"], T0["r13"], 0.25): golpe(x, t_, 0.11, f0=52, caida=0.10)
    barrido(x, T0["r12"] + 0.6, D["r12"] - 0.65, 0.05, 300, 2400)
    golpe(x, T0["r13"], 0.4, f0=46, caida=0.5); brillo(x, T0["r13"] + 0.05, 0.07)
    colchon(x, T0["r13"], dur, [110.0, 164.8, 220.0, 277.2], 0.04, ataque=0.1, suelta=0.4)


AMB = []

print("duración", DUR, T0)
if os.environ.get("SOLO_AUDIO"):
    dur = N / FPS; x = lienzo(dur); sonido(x, dur)
    nivel, (vv, ff) = mezclar(x, VOCES, dur, salida, techo=0.8)
    rel = [round(20 * np.log10((np.sqrt((vv[int(t_ * SR):int(t_ * SR) + len(a_)] ** 2).mean()) + 1e-12) /
                               (np.sqrt((ff[int(t_ * SR):int(t_ * SR) + len(a_)] ** 2).mean()) + 1e-12)), 1) for t_, a_ in VOCES]
    print("SOLO_AUDIO", nivel, rel); sys.exit()
render(salida, N, SEG, T, sonido, VOCES, techo=0.8, extra_audio=AMB)
