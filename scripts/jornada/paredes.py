# Reel Roccé Life «Paredes: 11 días» (28/11/2026). Guion de Fede v01 (04_fede_guiones.md, pieza 2) con los cambios de Roma
# (06_roma_revision_guiones.md): sin imagen de P3 (betsson a lo ancho), banda con el nombre en el cuadro 0, rótulo
# «PREVISTO: 21 A 25 DÍAS» + «DÍA 11», sin las filas 5 y 13, descargo con «sus rivales».
# Cambios de Pedro por control de marcas (betsson legible a 1080 en el frente de Boca):
#   - fila 8 «BOCA, A LA FINAL.»: P4 16,4–18,2 (abrazo, #5 de espaldas) en lugar de P4 10,6–12,4 (festejo de frente);
#   - fila 1: P1 recortado a la izquierda (el #6 que sale, con betsson en el pecho, queda fuera de cuadro);
#   - fila 2: P1 3,6–5,1 (el cuarto árbitro con el cartel), recortado a la izquierda;
#   - fila 12: P5 5,8–8,5 sin ampliar; la banda baja del descargo tapa el pecho (betsson en y 1300–1460).
#   - fila 3: la cita es la frase literal del audio de P2 (14,10–17,38): «Sabíamos que era asumir un riesgo muy grande.».
# v03 (Roma doc 14): el giro 2 se ve. Fila 12 = P5 8,30–10,50: «ELLA» entra en 9,40, el cuadro en que el parche toca el
#   pecho; fila 12b nueva = P5 13,55–15,00, el abrazo y el beso (misma toma continua, sin corte entre 5,5 y 16,0: es la
#   misma mujer del top a rayas con «PAREDES 5»), sin texto y sin banda (el pecho queda tapado por ella: betsson no se ve),
#   recortada 1,3× a la derecha para dejar afuera la cartera con el monograma de Louis Vuitton (x 0–250 de la fuente).
# v04 (Roma doc 17, pruebas): fila 6 = P4 2,60–4,50 (en 4,5–4,8 el pecho gira a cámara y se insinúan letras del
#   sponsor); fila 12b recortada 1,42× desde x 320 (la cartera llega hasta x 303 de la fuente en 14,2–14,4, medido por
#   cuadro: con 1,3× desde 248 se veía el monograma en la esquina de abajo a la izquierda).
# Audio: sin voz en off; la voz de Paredes (P2 y P3) baja el fondo. No se usa el audio de P1 (canción «Yellow»), P4, P5 ni
# P6 (música de la edición): la tribuna sale de A y C (Maracaná, clips de Cetré) y el resto es diseño sintetizado.
# Uso: python3 scripts/jornada/paredes.py SALIDA.mp4   (SOLO_AUDIO=1 mide la mezcla sin renderizar)
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from historia import *

CL = os.path.join(RAIZ, "TRABAJO/jornada3/clips")
P1 = os.path.join(CL, "sud_7702939397037083924.mp4")   # entrada: el #5 espera el cambio (rótulo y 909–1014)
P2 = os.path.join(CL, "sud_7698978508042685703.mp4")   # zona mixta (subtítulos en y ≈1360–1480)
P3 = os.path.join(CL, "sud_7706714837585382708.mp4")   # entrevista: solo audio
P4 = os.path.join(CL, "sud_7698963654401740040.mp4")   # el gol a Vasco
P5 = os.path.join(CL, "sud_7710801996952997127.mp4")   # el parche de campeón
P6 = os.path.join(CL, "sud_7710800344363568392.mp4")   # festejo de la final
A = os.path.join(CL, "lib_7699705925208198407.mp4")    # tribuna del Maracaná (ambiente)
C = os.path.join(CL, "lib_7699708477442100488.mp4")    # tribuna festejando (ambiente)
salida = sys.argv[1]

ROT_P1 = (126, 897, 952, 1026)    # rótulo de P1 + 12 px de margen
BANDA_BAJA = (1185, 1480)         # banda opaca con el descargo: tapa subtítulos de P2 y el pecho en P5

FILAS = [("r1", 1.45), ("r2", 1.50), ("r3", 3.80), ("r4", 2.75), ("r6", 1.90), ("r7", 1.30), ("r8", 1.80), ("r9", 3.25),
         ("r10", 1.60), ("r11", 1.30), ("r12", 2.20), ("r12b", 1.45), ("r14", 2.80), ("r15", 1.40)]
T0 = {}
t = 0.0
for k, d in FILAS:
    T0[k] = round(t, 3); t += d
DUR = round(t, 3)
N = cs(DUR)
D = dict(FILAS)


def recorte(z, x0, y0):
    cw, ch = int(W / z) // 2 * 2, int(H / z) // 2 * 2
    assert 0 <= x0 <= W - cw and 0 <= y0 <= H - ch, (z, x0, y0)
    return dict(zoom=z, cx=(x0 + cw / 2) / W, cy=(y0 + ch / 2) / H), (z, x0, y0)


R1, RC1 = recorte(1.5, 0, 400)
R2, RC2 = recorte(1.5, 0, 250)
R14, RC14 = recorte(1.25, 0, 230)
R3, RC3 = recorte(1.2, 180, 320)
R12B, RC12B = recorte(1.42, 320, 60)


def banda_rotulo(rc, lineas, size=72, sup=None, size_sup=36):
    """banda azul noche opaca a todo el ancho que tapa el rótulo de P1 en el recorte rc; texto centrado (x ≤ 950)."""
    z, x0, y0 = rc
    tp, b = (ROT_P1[1] - y0) * z, (ROT_P1[3] - y0) * z
    f = fuente("disp_xb", size)
    while max(f.getlength(s) for s in lineas) > 800: size -= 2; f = fuente("disp_xb", size)
    fs = fuente("disp_b", size_sup)
    if sup:
        while fs.getlength(sup) > 800: size_sup -= 1; fs = fuente("disp_b", size_sup)
    lh = int(size * 1.1)
    alto_txt = lh * len(lineas) + (int(size_sup * 1.5) if sup else 0) + 34
    alto = max(b - tp + 20, alto_txt)
    y_box = int((tp + b) / 2 - alto / 2)
    assert y_box <= tp - 6 and y_box + alto >= b + 6 and y_box >= 250 and y_box + alto <= 1235, (lineas, y_box, alto, tp, b)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([0, y_box + 6, W, y_box + alto + 10], fill=(0, 0, 0, 110))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    d.rectangle([0, y_box, W, y_box + alto], fill=NOCHE + (255,))
    y = y_box + (alto - alto_txt + 34) / 2 - size * 0.05
    if sup:
        d.text(((W - fs.getlength(sup)) / 2, y), sup, font=fs, fill=CEL + (255,)); y += int(size_sup * 1.5)
    for s in lineas:
        assert (W + f.getlength(s)) / 2 <= 950, s
        d.text(((W - f.getlength(s)) / 2, y), s, font=f, fill=(255, 255, 255, 255)); y += lh
    return img


def banda_baja():
    y0, y1 = BANDA_BAJA
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = np.zeros((H, W, 4), np.uint8)
    a[..., :3] = NOCHE
    yy = np.arange(H)
    alfa = np.where((yy >= y0) & (yy <= y1), 255, 0).astype(np.float32)
    g = (yy >= y0 - 36) & (yy < y0); alfa[g] = 255 * (yy[g] - (y0 - 36)) / 36          # borde superior suave (fuera de lo que tapa)
    g = (yy > y1) & (yy <= y1 + 24); alfa[g] = 255 * (1 - (yy[g] - y1) / 24)
    a[..., 3] = alfa[:, None].astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def caja_ok(lineas, size=84, **kw):
    f = fuente("disp_xb", size)
    while max(f.getlength(s) for s in lineas) > 800: size -= 2; f = fuente("disp_xb", size)
    return caja(lineas, size, **kw)


SEG = [
    seg(T0["r1"], T0["r2"], clip("r1", P1, 0.10, **R1), "r1"),
    seg(T0["r2"], T0["r3"], clip("r2", P1, 3.60, **R2), "r2"),
    seg(T0["r3"], T0["r4"], clip("r3", P2, 14.00, **R3), "r3"),
    seg(T0["r4"], T0["r6"], clip("r4", P2, 19.52, **R3), "r4"),
    seg(T0["r6"], T0["r7"], clip("r6", P4, 2.60), "r6"),
    seg(T0["r7"], T0["r8"], clip("r7", P4, 6.45), "r7"),
    seg(T0["r8"], T0["r9"], clip("r8", P4, 16.40), "r8"),
    seg(T0["r9"], T0["r10"], clip("r9", P4, 35.95), "r9"),
    seg(T0["r10"], T0["r11"], clip("r10", P6, 4.40), "r10"),
    seg(T0["r11"], T0["r12"], clip("r11", P5, 0.10), "r11"),
    seg(T0["r12"], T0["r12b"], clip("r12", P5, 8.30), "r12"),
    seg(T0["r12b"], T0["r14"], clip("r12b", P5, 13.55, **R12B), "r12b"),
    seg(T0["r14"], T0["r15"], clip("r14", P1, 18.10, **R14), "r14"),
    seg(T0["r15"], N, negro),
]

T = []


def txt(a, b, capa, y=0, x=None, pop=1.0, entra=0, sale=True):
    d = dict(c0=cs(a) if isinstance(a, float) else a, c1=cs(b) if isinstance(b, float) else b, capa=capa, y=y, pop=pop,
             entra=entra, sale=sale)
    if x is not None: d["x"] = x
    T.append(d)


def chico(s, color=CEL, size=40):
    return capa_texto([s], "disp_b", size, color=color, sombra=0.85, radio_sombra=10)


# banda baja opaca (antes del descargo, que va encima): P2 (subtítulos) y P5 (pecho)
BB = banda_baja()
txt(T0["r3"], T0["r6"], BB, y=0, x=0, sale=False)
txt(T0["r12"], T0["r12b"], BB, y=0, x=0, sale=False)

# descargo (3 renglones de 40 px, x 52–≤950, y 1244–1390) todo el video, también sobre la placa (se agrega al final)
DESC = capa_texto(["Roccé no tiene relación con Leandro", "Paredes, Boca Juniors, sus rivales ni",
                   "la CONMEBOL."], "inter_m", 40, color=(236, 236, 236), sombra=0.9, radio_sombra=8,
                  alinear="l", ancho=W, interlinea=1.15)
DESC = fondo_suave(DESC)          # placa oscura difusa: se lee también sobre medias, camisetas y cielo blancos
txt(0, T0["r15"], DESC, y=1244, x=52, sale=False)
CRED = rotulo_fuente("Video: CONMEBOL Sudamericana")
# a la derecha: a la izquierda, entre y 250 y 400, está la marca de agua de la fuente en los planos sin recorte
CRED_X = int(940 - fuente("inter_sb", 28).getlength("Video: CONMEBOL Sudamericana"))
txt(0, T0["r14"], CRED, y=252, x=CRED_X, sale=False)
# r14: sin crédito (a la izquierda o a la derecha cae sobre la camiseta); la marca de agua CONMEBOL SUDAMERICANA de la fuente queda entera arriba a la izquierda

# 1 · apuesta: Paredes, lesionado hace 11 días, espera el cambio
txt(0, T0["r2"], chico("SEMIFINAL · MARACANÁ"), y=318)
txt(0, T0["r2"], banda_rotulo(RC1, ["PAREDES, LESIONADO", "HACE 11 DÍAS."], 76), sale=False)
# 2 · gran pregunta
txt(T0["r2"], T0["r3"], banda_rotulo(RC2, ["¿SE VUELVE A ROMPER", "O LA DEFINE?"], 76), sale=False)
# 3 · evidencia en contra: el riesgo, con su voz
CITA3 = cita(["“Sabíamos que era asumir", "un riesgo muy grande.”"], clave="riesgo muy grande", encabezado="LA CHARLA CON EL DT:",
             size=58)
txt(T0["r3"], T0["r4"], CITA3, y=292, entra=3)
# 4 · evidencia en contra (sube): previsto 21 a 25 días; es el día 11
txt(T0["r4"], T0["r6"], caja_ok(["PREVISTO: 21 A 25 DÍAS"], 70), y=292, entra=2)
txt(T0["r4"] + 1.35, T0["r6"], etiqueta("DÍA 11", 46), y=430, pop=1.25)
# 6 · la pregunta se sostiene
txt(T0["r6"], T0["r7"], caja_ok(["A 2 MINUTOS DEL FINAL…"], 80), y=420, entra=2)
# 7 · giro 1
G_GOL = T0["r7"] + 0.20
txt(G_GOL, T0["r8"], caja_ok(["GOL."], 140), y=420, pop=1.3)
# 8 · resolución
txt(T0["r8"], T0["r9"], caja_ok(["BOCA, A LA FINAL."], 84, chico="Primera victoria en el Maracaná desde 1998",
                                size_chico=36), y=420, pop=1.1)
# 9 · pista sembrada: «ninguna medalla»
CITA9 = cita(["“Sí, pero yo no me pongo", "ninguna MEDALLA por eso.”"], clave="MEDALLA",
             encabezado="LE PREGUNTAN SI ARRIESGÓ EL FÍSICO:", size=58)
txt(T0["r9"], T0["r10"], CITA9, y=880, entra=3)     # abajo: arriba tapaba a medias la marca de agua o la cabeza
# 10 · la final
txt(T0["r10"], T0["r11"], caja_ok(["21/11 · FINAL:", "BOCA 2-0 ATLÉTICO MINEIRO."], 76), y=420, pop=1.1)
# 11 · pista visual
txt(T0["r11"], T0["r12"], caja_ok(["¿Y ESTO QUIÉN SE LO PONE?"], 76), y=420, entra=2)
# 12 · giro 2
G_ELLA = T0["r12"] + 1.10                   # P5 9,40: el parche toca el pecho
txt(T0["r12"], G_ELLA, caja_ok(["NINGUNA MEDALLA, DIJO."], 80), y=420, entra=2, sale=False)
txt(G_ELLA, T0["r12b"], caja_ok(["EL PARCHE SE LO PUSO ELLA."], 80), y=420, pop=1.12, sale=False)   # sale en el corte: a y 420 taparía las caras del abrazo
# 14 · reenganche
txt(T0["r14"], T0["r15"], banda_rotulo(RC14, ["¿VA POR OTRA?"], 96, sup="MIÉ 02/12 · FINAL DE COPA ARGENTINA VS. PLATENSE",
                                       size_sup=34), sale=False)
# 15 · firma
txt(T0["r15"], N, placa_firma("GIVE HISTORY YOUR NAME.", serif=True), y=0, x=0, sale=False, entra=2)
txt(T0["r15"], N, DESC, y=1244, x=52, sale=False)

# ---------- audio ----------
VOCES = [(T0["r3"] + 0.08, audio_clip(P2, 14.08, 3.72, fade=0.04)),
         (T0["r4"] + 0.06, audio_clip(P2, 19.58, 2.68, fade=0.05)),
         (T0["r9"] + 0.06, audio_clip(P3, 20.26, 3.14, fade=0.05))]
# misma sonoridad para las tres tomas (RMS de habla)
for i, (tv, a) in enumerate(VOCES):
    r = np.sqrt((a ** 2).mean()) + 1e-12
    VOCES[i] = (tv, a * (10 ** (-20 / 20) / r))
for (a_, va), (b_, _) in zip(VOCES, VOCES[1:]):
    assert a_ + len(va) / SR <= b_ + 1e-3


def sonido(x, dur):
    rng = np.random.default_rng(7)
    x += np.convolve(rng.normal(0, 1, len(x)), np.ones(80) / 80, "same") * 0.010
    for t_ in np.arange(0.0, T0["r2"], 0.5): golpe(x, t_, 0.16, f0=50, caida=0.18)
    for t_ in np.arange(T0["r2"], T0["r3"], 0.25): golpe(x, t_, 0.12, f0=54, caida=0.12)
    dron(x, 0.0, T0["r6"], f=44, g=0.035)
    for t_ in np.arange(T0["r3"], T0["r6"], 0.5): golpe(x, t_, 0.12, f0=48, caida=0.14)       # pulso bajo bajo la voz
    tic(x, T0["r4"] + 1.35, 0.10)                                                            # DÍA 11
    for t_ in np.arange(T0["r6"], G_GOL - 0.2, 0.125):
        golpe(x, t_, 0.08 + 0.10 * (t_ - T0["r6"]) / 2.0, f0=54, caida=0.09)
    barrido(x, T0["r6"] + 0.6, G_GOL - 0.2 - (T0["r6"] + 0.6), 0.06, 300, 2400)
    i0, i1 = int((G_GOL - 0.2) * SR), int((G_GOL - 0.01) * SR); x[i0:i1] *= 0.1               # casi silencio antes del gol
    golpe(x, G_GOL, 0.5, f0=42, caida=0.6); brillo(x, G_GOL + 0.02, 0.07)
    colchon(x, T0["r8"], T0["r9"] + 0.5, [146.8, 220.0, 293.7, 370.0], 0.05, ataque=0.12, suelta=0.6)
    dron(x, T0["r9"], T0["r10"], f=46, g=0.03)
    golpe(x, T0["r10"], 0.35, f0=46, caida=0.4); brillo(x, T0["r10"] + 0.03, 0.05)
    colchon(x, T0["r10"], T0["r11"] + 0.3, [164.8, 246.9, 329.6, 415.3], 0.05, ataque=0.1, suelta=0.4)
    tic(x, T0["r11"] + 0.05, 0.12); tic(x, T0["r11"] + 0.65, 0.08)
    i0, i1 = int((T0["r12"] - 0.15) * SR), int((T0["r12"] + 0.05) * SR); x[i0:i1] *= 0.15
    golpe(x, G_ELLA, 0.3, f0=48, caida=0.45); brillo(x, G_ELLA + 0.02, 0.05)
    colchon(x, G_ELLA, T0["r14"] + 0.4, [110.0, 164.8, 220.0, 277.2], 0.045, ataque=0.15, suelta=0.5)
    brillo(x, T0["r12b"] + 0.02, 0.035, 1.0)                                                  # el abrazo
    for t_ in np.arange(T0["r14"], T0["r15"], 0.5): golpe(x, t_, 0.13, f0=50, caida=0.15)
    golpe(x, T0["r15"], 0.4, f0=46, caida=0.5); brillo(x, T0["r15"] + 0.05, 0.07)
    colchon(x, T0["r15"], dur, [110.0, 164.8, 220.0, 277.2], 0.04, ataque=0.1, suelta=0.4)


AMB = [(T0["r1"], audio_clip(A, 1.0, D["r1"] + D["r2"], gan=0.55)),
       (T0["r3"], audio_clip(A, 9.0, D["r3"], gan=1.5)),            # tribuna bajo la voz: voz/fondo entre 10 y 15 dB
       (T0["r4"], audio_clip(A, 9.0 + D["r3"], D["r4"], gan=1.0)),
       (T0["r6"], audio_clip(A, 16.0, D["r6"] + 0.2, gan=0.6)),
       (G_GOL, audio_clip(C, 9.7, T0["r9"] - G_GOL, gan=1.1)),
       (T0["r9"], audio_clip(A, 12.0, D["r9"], gan=1.0)),
       (T0["r10"], audio_clip(C, 11.4, D["r10"], gan=0.9)),
       (T0["r11"], audio_clip(A, 5.0, D["r11"] + D["r12"] + D["r12b"], gan=0.3)),
       (T0["r14"], audio_clip(A, 20.0, D["r14"], gan=0.5))]

print("duración", DUR, T0)
if os.environ.get("SOLO_AUDIO"):
    dur = N / FPS; x = lienzo(dur); sonido(x, dur)
    for t_, a_ in AMB:
        i = int(t_ * SR); m = min(len(a_), len(x) - i); x[i:i + m] += a_[:m]
    nivel, (vv, ff) = mezclar(x, VOCES, dur, salida, techo=0.8)
    rel = [round(20 * np.log10((np.sqrt((vv[int(t_ * SR):int(t_ * SR) + len(a_)] ** 2).mean()) + 1e-12) /
                               (np.sqrt((ff[int(t_ * SR):int(t_ * SR) + len(a_)] ** 2).mean()) + 1e-12)), 1) for t_, a_ in VOCES]
    print("SOLO_AUDIO", nivel, rel); sys.exit()
render(salida, N, SEG, T, sonido, VOCES, techo=0.8, extra_audio=AMB)
