# Reel Roccé Life «Cetré: lo metió y no valió» (28/11/2026). Guion de Fede v01 (04_fede_guiones.md) con los cambios de Roma
# (06_roma_revision_guiones.md) y los tiempos medidos por Pedro (05_pedro_tiempos_medidos.md). Voz oficial en modo natural.
# Apuesta: patea Cetré en la tanda del Maracaná → la mete → el arquero reclama → «¡No vale!» (resbaló y la tocó dos veces) →
# se repite → por arriba del travesaño → ¿quedan afuera por él? → Muslera ataja dos más, una atrás de la otra → Estudiantes a la
# final → reenganche: hoy 17:00 contra Palmeiras, si hay penales ¿le das la pelota? → placa «so f★cking close.».
# Clips (© CONMEBOL, marca de agua intacta): A = tribuna (rótulo «Los penales fallidos de Cetré.» fijo en y 1216–1311,
# x 325–754: se tapa con la caja de cada texto, calculada después del zoom), B = transmisión (rótulo hasta 8,7 s; se usa
# desde 9,7), C = tribuna de Estudiantes (rótulo hasta 8,7 s; se usa desde 9,7).
# Uso: python3 scripts/jornada/cetre.py SALIDA.mp4
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from historia import *

CL = os.path.join(RAIZ, "TRABAJO/jornada3/clips")
A = os.path.join(CL, "lib_7699705925208198407.mp4")
B = os.path.join(CL, "lib_7699841588662406420.mp4")
C = os.path.join(CL, "lib_7699708477442100488.mp4")
VOZ = os.path.join(RAIZ, "TRABAJO/jornada3/voz_c2")
salida = sys.argv[1]

ROT_A = (313, 1204, 766, 1323)   # rótulo de A + 12 px de margen (unión de píxeles en todos los cuadros)

# filas: (dur, voz, desfase de la voz)
FILAS = [
    ("r1", 2.20, "c1", 0.06), ("r2", 1.45, "c2", 0.08), ("r3", 2.50, "c3", 0.06), ("r4", 0.85, "c4", 0.08),
    ("r5", 2.05, "c5", 0.05), ("r6", 2.00, "c6", 0.08), ("r7", 1.10, "c7", 0.10), ("r8", 1.90, "c8", 0.10),
    ("r9", 1.65, "c9", 0.08), ("r10", 1.75, "c10", 0.06), ("r11", 2.05, "c11", 0.08), ("r12", 2.30, "c12", 0.15),
    ("r13", 1.70, "c13", 0.10), ("r14", 4.75, "c14", 0.10), ("r15", 1.50, None, 0),
]
T0 = {}
t = 0.0
for k, d, _, _ in FILAS:
    T0[k] = round(t, 3); t += d
DUR = round(t, 3)
N = cs(DUR)
TF = lambda k: T0[k] + dict((f[0], f[1]) for f in FILAS)[k]


def recorte(z, x0, y0):
    """devuelve (zoom, cx, cy) para clip() a partir del origen del recorte en la fuente."""
    cw, ch = int(W / z) // 2 * 2, int(H / z) // 2 * 2
    return dict(zoom=z, cx=(x0 + cw / 2) / W, cy=(y0 + ch / 2) / H), (z, x0, y0)


def caja_rotulo(lineas, rc, size=64, rotulo=None):
    """caja azul noche opaca con el texto, que cubre el rótulo de A en el recorte rc = (z, x0, y0)."""
    z, x0, y0 = rc
    l, tp, r, b = [(v - o) * z for v, o in zip(ROT_A, (x0, y0, x0, y0))]
    f = fuente("disp_xb", size)
    while max(f.getlength(s) for s in lineas) > 860: size -= 2; f = fuente("disp_xb", size)
    lh = int(size * 1.1)
    bw = int(max(r - l + 16, max(f.getlength(s) for s in lineas) + 60))
    bh_txt = lh * len(lineas) + 30
    bh = int(max(b - tp + 16, bh_txt))
    cxo = (l + r) / 2
    x_box = int(min(max(cxo - bw / 2, 20), W - 20 - bw))
    y_box = int((tp + b) / 2 - bh / 2)
    assert x_box <= l - 4 and x_box + bw >= r + 4 and y_box <= tp - 4 and y_box + bh >= b + 4, (lineas, x_box, bw, y_box, bh, l, r, tp, b)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x_box, y_box + 8, x_box + bw, y_box + bh + 8], radius=20, fill=(0, 0, 0, 120))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x_box, y_box, x_box + bw, y_box + bh], radius=20, fill=NOCHE + (255,))
    util = min(x_box + bw, 950) - x_box - 40          # el texto termina antes de x 950 (íconos de Reels)
    while max(f.getlength(s) for s in lineas) > util:
        size -= 2; f = fuente("disp_xb", size); lh = int(size * 1.1)
    y = y_box + (bh - lh * len(lineas)) / 2 - size * 0.06
    xc = (x_box + min(x_box + bw, 950)) / 2
    for s in lineas:
        assert xc + f.getlength(s) / 2 <= 950, s
        d.text((xc - f.getlength(s) / 2, y), s, font=f, fill=(255, 255, 255, 255)); y += lh
    return img


# recortes de A
P1, R_P1 = recorte(1.5, 90, 560)     # primer intento: punto penal y arco
PK, R_PK = recorte(1.35, 280, 450)   # arquero que reclama / árbitro
P2, R_P2 = recorte(1.5, 180, 560)    # carrera de la repetición
P3, R_P3 = recorte(1.35, 280, 410)   # la pelota por arriba del travesaño (sale por la derecha)
PC, R_PC = recorte(1.35, 140, 450)   # Cetré frente a la pelota (cuadro 0 y reenganche)
PW, R_PW = recorte(1.2, 90, 320)     # plano abierto de A (árbitro, arquero y Cetré de lejos)

C_NOVALE = cs(T0["r5"] + 0.05 + 1.05)

# pelota de la repetición, detectada por diferencia de cuadros en A (x, y de la fuente; 23,70 y 23,733 extrapolados)
BOLA = [(23.533, 559, 980), (23.567, 630, 944), (23.600, 705, 905), (23.633, 786, 865), (23.667, 870, 823),
        (23.700, 950, 783), (23.733, 1030, 743)]


def con_aro(fuente_, t_fuente0, lento, rc):
    z, x0, y0 = rc
    ts = np.array([b[0] for b in BOLA]); xs = np.array([b[1] for b in BOLA]); ys = np.array([b[2] for b in BOLA])
    def f(c, k):
        a = fuente_(c, k)
        s_ = t_fuente0 + (k / FPS) / lento
        if ts[0] - 0.01 <= s_ <= ts[-1] + 0.01:
            x = (np.interp(s_, ts, xs) - x0) * z; y = (np.interp(s_, ts, ys) - y0) * z
            im = Image.fromarray(a); d = ImageDraw.Draw(im)
            for r_, w_, col in ((34, 7, (0, 0, 0)), (32, 4, (255, 255, 255))):
                d.ellipse([x - r_, y - r_, x + r_, y + r_], outline=col, width=w_)
            a = np.asarray(im)
        return a
    return f   # corte al árbitro cuando arranca «¡No vale!»

SEG = [
    seg(T0["r1"], T0["r2"], clip("r1", A, 28.6, **PC), "r1"),
    seg(T0["r2"], T0["r3"], clip("r2", B, 9.7), "r2"),
    seg(T0["r3"], T0["r4"], clip("r3", A, 0.0, lento=2.50 / 1.36, **P1), "r3"),
    seg(T0["r4"], T0["r5"], clip("r4", A, 1.36, **P1), "r4"),
    seg(T0["r5"], C_NOVALE, clip("r5a", A, 4.3, **PK), "r5a"),
    seg(C_NOVALE, T0["r6"], clip("r5b", A, 13.9, **PK), "r5b"),
    seg(T0["r6"], T0["r7"], clip("r6", A, 0.3, lento=2.0, **P1), "r6"),
    seg(T0["r7"], T0["r8"], clip("r7", A, 16.0, **PW), "r7"),
    seg(T0["r8"], T0["r9"], clip("r8", A, 21.45, **P2), "r8"),
    seg(T0["r9"], T0["r10"], con_aro(clip("r9", A, 23.35, lento=2.0, **P3), 23.35, 2.0, R_P3), "r9"),
    seg(T0["r10"], T0["r11"], clip("r10", B, 13.3), "r10"),
    seg(T0["r11"], T0["r12"], clip("r11", B, 15.15), "r11"),
    seg(T0["r12"], T0["r13"], clip("r12", B, 32.4), "r12"),
    seg(T0["r13"], T0["r14"], clip("r13", C, 9.7), "r13"),
    seg(T0["r14"], T0["r15"], clip("r14", A, 26.5, congelar_en=cs(4.15), **PC), "r14"),
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


# descargo fijo (3 renglones de 40 px, x 60–≤950, y 1246–1390) hasta la placa
DESC = capa_texto(["Roccé no tiene relación con Edwuin Cetré,", "Fernando Muslera, Estudiantes, Flamengo,",
                   "Palmeiras ni la CONMEBOL."], "inter_m", 40, color=(236, 236, 236), sombra=0.9, radio_sombra=8,
                  alinear="l", ancho=W, interlinea=1.15)
txt(0, T0["r15"], DESC, y=1244, x=52, sale=False)
CRED = rotulo_fuente("Video: CONMEBOL Libertadores")
txt(0, T0["r15"], CRED, y=252, x=60, sale=False)

# 1 · apuesta: Cetré y su nombre
txt(0, T0["r2"], chico("SEMIFINAL DE LIBERTADORES · MARACANÁ"), y=300)
txt(0, T0["r2"], caja_rotulo(["PATEA CETRÉ."], R_PC, 84))
# 2 · Muslera ya atajó uno
txt(T0["r2"], T0["r3"], etiqueta("ATAJADA 1"), y=300)
txt(T0["r2"], T0["r3"], caja(["MUSLERA YA", "ATAJÓ UNO."], 84), y=380, pop=1.1, entra=2)
# 3 · ¿adentro?
txt(T0["r3"], T0["r4"], caja_rotulo(["¿ADENTRO?"], R_P1, 96))
# 4 · adentro
txt(T0["r4"], T0["r5"], caja_rotulo(["ADENTRO."], R_P1, 96))
# 5 · el arquero reclama → no vale
txt(T0["r5"], C_NOVALE, caja_rotulo(["EL ARQUERO RECLAMA."], R_PK, 70))
txt(C_NOVALE, T0["r6"], caja_rotulo(["NO VALE."], R_PK, 110), pop=1.15)
# 6 · se resbala y la toca dos veces (cámara lenta)
txt(T0["r6"], T0["r7"], caja_rotulo(["SE RESBALA Y", "LA TOCA DOS VECES."], R_P1, 70))
txt(T0["r6"], T0["r7"], chico("CÁMARA LENTA", (235, 235, 235), 34), y=300)
# 7 · se repite
txt(T0["r7"], T0["r8"], etiqueta("INTENTO 2"), y=300)
txt(T0["r7"], T0["r8"], caja_rotulo(["SE REPITE."], R_PW, 96))
# 8 · ¿otra vez adentro?
txt(T0["r8"], T0["r9"], caja_rotulo(["¿OTRA VEZ ADENTRO?"], R_P2, 80))
# 9 · arriba del travesaño
txt(T0["r9"], T0["r10"], caja_rotulo(["ARRIBA DEL TRAVESAÑO."], R_P3, 76), pop=1.1)
txt(T0["r9"], T0["r10"], chico("CÁMARA LENTA", (235, 235, 235), 34), y=300)
# 10 · ¿quedan afuera por él?
txt(T0["r10"], T0["r11"], caja(["¿QUEDAN AFUERA", "POR ÉL?"], 88), y=330, pop=1.1)
# 11–12 · las atajadas, una atrás de la otra
txt(T0["r11"], T0["r12"], etiqueta("ATAJADA 2"), y=330)
txt(T0["r12"], T0["r13"], etiqueta("ATAJADA 3"), y=330)
# 13 · a la final
txt(T0["r13"], T0["r14"], caja(["ESTUDIANTES,", "A LA FINAL."], 92), y=330, pop=1.12)
# 14 · reenganche
txt(T0["r14"], T0["r15"], chico("HOY 17:00 · FINAL VS. PALMEIRAS · CENTENARIO"), y=300)
txt(T0["r14"] + 2.30, T0["r15"], caja_rotulo(["SI HAY PENALES,", "¿LE DAS LA PELOTA?"], R_PC, 72), pop=1.08)
txt(T0["r14"], T0["r14"] + 2.30, caja_rotulo(["HOY, LA FINAL."], R_PC, 84), sale=False)
# 15 · placa
PL = placa_firma("so f★cking close.")
d_ = ImageDraw.Draw(PL)
fc = fuente("disp_b", 44)
s_ = "Comentá: sí o no."
d_.text(((W - fc.getlength(s_)) / 2, 1080), s_, font=fc, fill=(255, 255, 255, 255))
txt(T0["r15"], N, PL, y=0, x=0, sale=False, entra=2)


def sonido(x, dur):
    rng = np.random.default_rng(11)
    x += np.convolve(rng.normal(0, 1, len(x)), np.ones(80) / 80, "same") * 0.012
    # pulso: cada 0,5 s en la apuesta, cada 0,25 s en las preguntas
    for t in np.arange(0.0, T0["r3"], 0.5): golpe(x, t, 0.16, f0=50, caida=0.18)
    for t in np.arange(T0["r3"], T0["r4"], 0.25): golpe(x, t, 0.12, f0=54, caida=0.12)
    golpe(x, T0["r4"] + 0.35, 0.25, f0=60, caida=0.2)                      # adentro
    g = C_NOVALE / FPS
    i0, i1 = int((g - 0.25) * SR), int((g - 0.02) * SR); x[i0:i1] *= 0.12   # casi silencio antes del giro
    golpe(x, g, 0.45, f0=40, caida=0.6); brillo(x, g + 0.02, 0.06)
    barrido(x, T0["r6"], 0.5, 0.1, 3000, 300)
    for t in np.arange(T0["r7"], T0["r8"], 0.5): golpe(x, t, 0.14, f0=50, caida=0.15)
    for t in np.arange(T0["r8"], T0["r9"], 0.25): golpe(x, t, 0.1 + 0.08 * (t - T0["r8"]) / 1.9, f0=54, caida=0.12)
    i0, i1 = int((T0["r9"] - 0.2) * SR), int((T0["r9"] - 0.01) * SR); x[i0:i1] *= 0.15
    golpe(x, T0["r9"] + 0.55, 0.4, f0=44, caida=0.5)                       # la pelota se va
    dron(x, T0["r9"], T0["r13"], f=46, g=0.04)
    for t in np.arange(T0["r10"], T0["r11"], 0.5): golpe(x, t, 0.14, f0=50, caida=0.15)
    golpe(x, T0["r11"] + 1.35, 0.4, f0=48, caida=0.4); golpe(x, T0["r12"] + 1.75, 0.45, f0=46, caida=0.45)
    colchon(x, T0["r13"], T0["r14"] + 0.6, [146.8, 220.0, 293.7, 370.0], 0.05, ataque=0.15, suelta=0.6)
    for t in np.arange(T0["r14"], T0["r15"], 0.5): golpe(x, t, 0.12, f0=50, caida=0.15)
    golpe(x, T0["r15"], 0.4, f0=46, caida=0.5); brillo(x, T0["r15"] + 0.05, 0.07)
    colchon(x, T0["r15"], dur, [110.0, 164.8, 220.0, 277.2], 0.04, ataque=0.1, suelta=0.4)


# ambiente real de la tribuna (A y C), bajo
amb = []
for k, src, t0 in (("r1", A, 28.6), ("r3", A, 0.0), ("r4", A, 1.36), ("r5", A, 4.3), ("r7", A, 16.0), ("r8", A, 21.45),
                   ("r14", A, 26.5)):
    d = dict((f[0], f[1]) for f in FILAS)[k]
    d = min(d, 30.7 - t0) if src == A else d
    amb.append((T0[k], audio_clip(src, t0, d, gan=0.6)))
amb.append((T0["r13"], audio_clip(C, 9.7, 1.9, gan=1.1)))
amb.append((T0["r2"], audio_clip(A, 5.0, 1.45, gan=0.6)))     # tribuna bajo la atajada 1 (sin el relato de B)
amb.append((T0["r6"], audio_clip(A, 6.4, 2.0, gan=0.6)))      # tribuna bajo la cámara lenta
amb.append((T0["r14"], audio_clip(A, 8.0, 4.75, gan=0.5)))    # refuerzo de tribuna en el reenganche
amb.append((T0["r10"], audio_clip(A, 5.0, T0["r13"] - T0["r10"], gan=0.4)))   # tribuna bajo las atajadas (sin relato)

voces = [(T0[k] + o, leer_wav(os.path.join(VOZ, f"{v}.wav"))) for k, _, v, o in FILAS if v]
for (a, va), (b, _) in zip(voces, voces[1:]):
    assert a + len(va) / SR <= b + 1e-3, f"voces superpuestas en {a:.2f}–{b:.2f}"
print("duración", DUR, {k: T0[k] for k in T0})
render(salida, N, SEG, T, sonido, voces, techo=0.8, extra_audio=amb)
