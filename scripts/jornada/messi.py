# Reel «Messi: ¿lo evita esta noche?» (27/11/2026). Guion de Fede v01 (12_fede_guiones_tarde.md), voz natural.
# Apuesta en el cuadro 0: su cara (clip oficial de Inter Miami CF) + «SI PIERDE HOY, MESSI QUEDA AFUERA.» → atajada del juego 1
# (@mls) → «Columbus 3, Miami 0» (gol de Columbus, @mls) → en contra a toda velocidad (8 de 9; le tiró la pelota a la cara a
# Tapia; con roja se perdía el juego 2: la tarjeta aparece en blanco, sin color) → tramo calmo (el plantel en la previa) →
# giro: la tarjeta se llena de amarillo, «AMARILLA.» (único grito, con volumen y no con tono) → para los dos, llega →
# a favor (Bota de Oro) → reenganche: hoy 22:00, penales si empatan, juego 3 el miércoles → CTA sobre la espalda real de la
# remera (IMG_5327): «¿Perdiste el primero? Volvé.» El famoso nunca aparece junto a la prenda; descargo en la placa.
# Clips: TRABAJO/jornada2/messi/ (© MLS / Inter Miami CF, marca de agua intacta, sin su audio; los de 59,94 y 23,976 fps
# se leen a tiempo real, sin cámara lenta). Voz: scripts/jornada/voz_messi.tsv (modo natural).
# Uso: python3 scripts/jornada/messi.py SALIDA.mp4
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reel import *

MX = os.path.join(RAIZ, "TRABAJO/jornada2/messi")
FEED = os.path.join(RAIZ, "TRABAJO/feed")
VOZ = os.path.join(RAIZ, "TRABAJO/jornada2/voz_x")
VOZ_R = os.path.join(RAIZ, "TRABAJO/jornada2/voz_x_rap")   # x1 ×1,08 · x2, x4, x5 ×1,15 · x3 ×1,2 (cola recortada) · x8–x10 ×1,1 (atempo)
RAP = ("x1", "x2", "x3", "x4", "x5", "x8", "x9", "x10")
CARA = os.path.join(MX, "tt_7710039332676996365.mp4")      # @intermiamicf, primer plano (plano único 5,47–7,87 s)
ATAJA = os.path.join(MX, "tt_7710827690126855454.mp4")     # @mls, atajada a Messi en el juego 1
GOL = os.path.join(MX, "tt_7710863273897250078.mp4")       # @mls, gol de Columbus («How it ended», tapado)
PREVIA = os.path.join(MX, "tt_7712874915082276110.mp4")    # @intermiamicf, previa de hoy
BOTA = os.path.join(MX, "tt_7710769166743112991.mp4")      # @mls, Bota de Oro (desde 6,3 s: el rótulo en inglés ya salió)
ENTRENO = os.path.join(MX, "tt_7709985084794899725.mp4")   # @intermiamicf, entrenamiento
salida = sys.argv[1]

TV = dict(x1=0.05, x2=2.35, x3=3.95, x4=5.45, x5=7.0, x6=8.65, x7=10.8, x8=12.2, x9=14.0, x10=16.72, x11=18.9)
N = cs(22.4)
C_GIRO = cs(TV["x6"] + 1.41)   # «¡Amarilla!»

estado = {}


def clip(nombre, src, t0, osc=None, congelar_en=None):
    def f(c, k):
        if k == 0 or nombre not in estado:
            if nombre in estado: estado[nombre].cerrar()
            estado[nombre] = Lector(src, t0, W, H, uno_a_uno=False)
        a = estado[nombre].ult if (congelar_en is not None and k >= congelar_en) else estado[nombre].cuadro()
        a = a.copy()
        if osc: a = oscurecer(a, *osc)
        return a
    return f


def cerrar(nombre):
    return lambda: estado.pop(nombre).cerrar() if nombre in estado else None


AMARILLO = (246, 206, 32)


def tarjeta_arbitro(modo):
    """fondo de tarjeta + tarjeta de árbitro: 'vacia' (contorno blanco), 'amarilla' (se llena con un golpe), 'dos'."""
    def f(c, k):
        img = Image.fromarray(fondo_tarjeta(c))
        d = ImageDraw.Draw(img)
        cw, ch, y0 = 230, 320, 1050
        if modo == "vacia":
            d.rounded_rectangle([W / 2 - cw / 2, y0, W / 2 + cw / 2, y0 + ch], radius=18, outline=(235, 235, 235), width=6)
        elif modo == "amarilla":
            e = pop(k, 5, 1.18); w2, h2 = cw * e / 2, ch * e / 2; cy = y0 + ch / 2
            d.rounded_rectangle([W / 2 - w2, cy - h2, W / 2 + w2, cy + h2], radius=18, fill=AMARILLO)
        else:
            for dx, ang in ((-150, -8), (150, 8)):
                t = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0))
                ImageDraw.Draw(t).rounded_rectangle([20, 20, 20 + cw, 20 + ch], radius=18, fill=AMARILLO + (255,))
                t = t.rotate(ang, resample=Image.BICUBIC, expand=True)
                img.paste(t, (int(W / 2 + dx - t.width / 2), int(y0 + ch / 2 - t.height / 2)), t)
        return np.asarray(img)
    return f


def tarjeta(c, k):
    return fondo_tarjeta(c)


SEG = [
    dict(c0=0, c1=cs(1.3), fuente=clip("cara", CARA, 5.5, osc=(560, 0.45)), cerrar=cerrar("cara")),
    dict(c0=cs(1.3), c1=cs(2.35), fuente=clip("ataja", ATAJA, 4.0, osc=(700, 0.4)), cerrar=cerrar("ataja")),
    dict(c0=cs(2.35), c1=cs(3.95), fuente=clip("gol", GOL, 11.5, osc=(600, 0.3)), cerrar=cerrar("gol")),
    dict(c0=cs(3.95), c1=cs(7.0), fuente=tarjeta),
    dict(c0=cs(7.0), c1=cs(8.65), fuente=tarjeta_arbitro("vacia")),
    dict(c0=cs(8.65), c1=C_GIRO, fuente=clip("previa", PREVIA, 8.1, osc=(700, 0.3)), cerrar=cerrar("previa")),
    dict(c0=C_GIRO, c1=cs(10.8), fuente=tarjeta_arbitro("amarilla")),
    dict(c0=cs(10.8), c1=cs(12.2), fuente=tarjeta_arbitro("dos")),
    dict(c0=cs(12.2), c1=cs(14.0), fuente=clip("bota", BOTA, 6.3, osc=(700, 0.45)), cerrar=cerrar("bota")),
    dict(c0=cs(14.0), c1=cs(16.72), fuente=clip("entreno", ENTRENO, 7.0, osc=(720, 0.4)), cerrar=cerrar("entreno")),
    dict(c0=cs(16.72), c1=cs(18.9), fuente=tarjeta),
    dict(c0=cs(18.9), c1=N, fuente=clip("cta", os.path.join(FEED, "sdr_5327.mp4"), 4.3, osc=(640, 0.6, 1120, 0.62),
                                      congelar_en=cs(0.6)), cerrar=cerrar("cta")),
]


# ---------- textos ----------
def ajustar(lineas, fk, size, ancho=960):
    while max(fuente(fk, size).getlength(l) for l in lineas) > ancho: size -= 2
    return size


def tarj(g, ch=None, size=104):
    s = ajustar(g, "disp_xb", size)
    return capa_texto(g, "disp_xb", s), (capa_texto([ch], "disp_b", 58, color=CEL) if ch else None), s


T = []
CRED = 1330   # crédito chico abajo a la izquierda (el cuadro 0 tiene la cara arriba), por encima de la interfaz de Reels


def credito(a, b, txt, y=CRED):
    T.append(dict(c0=cs(a) if a else 0, c1=cs(b) if isinstance(b, float) else b, capa=rotulo_fuente(txt), x=40, y=y,
                  entra=0))


T.append(dict(c0=0, c1=cs(1.3), capa=caja(["SI PIERDE HOY,", "MESSI QUEDA AFUERA."], 72), y=150, pop=1, entra=0))
credito(0, 1.3, "Video: @intermiamicf")
T.append(dict(c0=cs(1.3), c1=cs(2.35), capa=caja(["¿LO EVITA", "ESTA NOCHE?"], 80), y=150, pop=1.1, entra=0))
credito(1.3, 2.35, "Video: @mls")
T.append(dict(c0=cs(2.35), c1=cs(3.95), capa=caja(["JUEGO 1:", "COLUMBUS 3, MIAMI 0."], 70, chico="Dos goles de Tapia.",
                                                size_chico=46), y=1060, entra=0))   # tapa «How it ended…» (filas 1250–1309)
credito(2.35, 3.95, "Video: @mls", y=150)

for (a, b, g, ch) in [(3.95, 5.45, ["COLUMBUS LLEGÓ CON", "8 DE SUS ÚLTIMOS 9."], "Y ganó el juego 1."),
                      (5.45, 7.0, ["MESSI LE TIRÓ", "LA PELOTA A LA", "CARA A TAPIA."], "Al de los dos goles.")]:
    cg, cc, s = tarj(g, ch)
    lh = int(s * 1.08)
    y = 760 - lh * (len(g) - 1) // 2
    T.append(dict(c0=cs(a), c1=cs(b), capa=cg, y=y, pop=1.2, sale=False))
    T.append(dict(c0=cs(a) + 3, c1=cs(b), capa=cc, y=y + lh * len(g) + 30, pop=1, sale=False))

cg, _, s = tarj(["CON ROJA, SE PERDÍA", "EL JUEGO 2."])
T.append(dict(c0=cs(7.0), c1=cs(8.65), capa=cg, y=700, pop=1.15, sale=False))
credito(8.65, C_GIRO, "Video: @intermiamicf")
T.append(dict(c0=C_GIRO, c1=cs(10.8), capa=capa_texto(["AMARILLA."], "disp_xb", 150), y=720, pop=1.25, entra=0, sale=False))
cg, _, s = tarj(["PARA LOS DOS.", "LLEGA AL JUEGO 2."])
T.append(dict(c0=cs(10.8), c1=cs(12.2), capa=cg, y=700, pop=1.12, sale=False))
T.append(dict(c0=cs(12.2), c1=cs(14.0), capa=caja(["BOTA DE ORO,", "2 AÑOS SEGUIDOS."], 74), y=232, entra=2))
credito(12.2, 14.0, "Video: @mls")
T.append(dict(c0=cs(14.0), c1=cs(16.72), capa=caja(["HOY · 22:00"], 84, chico="Si empatan a los 90’, penales. Sin alargue.",
                                                 size_chico=40, ancho_min=780), y=232, entra=0))
credito(14.0, 16.72, "Video: @intermiamicf")
cg, cc, s = tarj(["SI GANA: JUEGO 3."], "Miércoles 02/12 · 21:30 · en Miami.")
T.append(dict(c0=cs(16.72), c1=cs(18.9), capa=cg, y=760, pop=1.2, sale=False))
T.append(dict(c0=cs(16.72) + 3, c1=cs(18.9), capa=cc, y=760 + int(s * 1.08) + 30, pop=1, sale=False))
T.append(dict(c0=cs(19.25), c1=N, capa=capa_texto(["SEGUIR HASTA", "LOGRARLO."], "disp_xb", 120), y=130, pop=1.15))
T.append(dict(c0=cs(19.6), c1=N, capa=capa_texto(["¿Perdiste el primero? Volvé:", "Founders Privée."], "disp_b", 52,
                                                 sombra=0.85), y=420, pop=1))
T.append(dict(c0=cs(19.6), c1=N, capa=capa_texto(["Roccé no tiene relación con Lionel Messi,",
                                                  "Inter Miami, Columbus Crew ni la MLS."],
                                                 "inter_m", 40, color=(236, 236, 236), sombra=0.85), y=1290, pop=1))


# ---------- sonido ----------
def sonido(x, dur):
    rng = np.random.default_rng(27)
    x += np.convolve(rng.normal(0, 1, len(x)), np.ones(80) / 80, "same") * 0.02
    golpe(x, 1.3, 0.3, f0=50, caida=0.22)                # corte a la atajada
    golpe(x, 1.62, 0.35, f0=110, caida=0.06)             # la pelota contra el arquero
    golpe(x, 2.35, 0.32, f0=46, caida=0.3)
    for t in (3.95, 5.45, 7.0):                          # tarjetas
        tic(x, t, 0.22, 1800); golpe(x, t, 0.3, f0=48, caida=0.3)
    dron(x, 3.95, 8.65, f=46, g=0.05)
    barrido(x, 9.0, 1.0, 0.12, 200, 7000)                # subida hacia el giro (tramo calmo)
    g = C_GIRO / FPS
    golpe(x, g - 0.05, 0.4, f0=42, caida=0.6); brillo(x, g, 0.07)
    colchon(x, g, 14.0, [146.8, 220.0, 293.7, 370.0], 0.035, ataque=0.25, suelta=0.5)
    tic(x, 10.8, 0.2, 1800); golpe(x, 10.8, 0.28, f0=50, caida=0.25)
    barrido(x, 12.12, 0.3, 0.12, 300, 5000)
    for t in np.arange(14.0, 18.85, 0.42):               # pulso: queda abierta
        golpe(x, t, 0.13, f0=50, caida=0.15)
    golpe(x, 14.98, 0.3, f0=120, caida=0.05)             # la pelota en la red
    i0, i1 = int(18.82 * SR), int(19.2 * SR)
    x[i0:i1] *= 0.15                                     # casi silencio antes del CTA
    golpe(x, 18.9, 0.3, f0=52, caida=0.35); brillo(x, 19.25, 0.08)
    colchon(x, 18.9, dur, [110.0, 164.8, 220.0, 277.2], 0.045, ataque=0.15, suelta=0.4)


v = {k: leer_wav(os.path.join(VOZ_R if k in RAP else VOZ, f"{k}.wav")) for k in TV}
for k, db in (("x2", 2.0), ("x3", 2.0), ("x5", 2.0), ("x6", 1.5), ("x9", 1.0), ("x10", 1.0), ("x11", 1.0)):
    v[k] = v[k] * 10 ** (db / 20)
voces = [(TV[k], v[k]) for k in TV]
for (a, va), (b, _) in zip(voces, voces[1:]):
    assert a + len(va) / SR <= b + 1e-3, f"voces superpuestas en {a:.2f}–{b:.2f}"
render(salida, N, SEG, T, sonido, voces, techo=0.8)
