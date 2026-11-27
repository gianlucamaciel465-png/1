# Reel «Palermo: ¿le gana a Boca por primera vez?» (27/11/2026). Guion de Fede v01 (12_fede_guiones_tarde.md), voz natural.
# Apuesta en el cuadro 0: su cara (presentación en Platense TV, ampliada para que no entren los subtítulos quemados) +
# «COMO DT, PALERMO NUNCA LE GANÓ A BOCA.» → ¿le gana en la final del miércoles? → en contra: 10 partidos, 0 victorias;
# casi: el 1-1 del 16/08 (festejo de Platense) → pista: 1999, 3 penales errados (travesaño, arriba, atajado: siguió
# pateando) → tramo calmo (camina) → giro: «¡Máximo goleador de Boca!» (único grito, con volumen y no con tono) → primera
# final entre los dos → reenganche: miércoles 02/12 (hora y sede sin confirmar: no se ponen) → CTA sobre la remera negra
# real (IMG_5333): «Seguí pateando.» El famoso nunca aparece junto a la prenda; descargo en la placa.
# Clips: TRABAJO/jornada2/palermo/ (canal oficial de Platense, marca de agua «PLATENSE TV», sin su audio).
# Voz: scripts/jornada/voz_palermo.tsv. Uso: python3 scripts/jornada/palermo.py SALIDA.mp4
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reel import *

PA = os.path.join(RAIZ, "TRABAJO/jornada2/palermo")
GL = os.path.join(RAIZ, "TRABAJO/fomo/gl")
VOZ = os.path.join(RAIZ, "TRABAJO/jornada2/voz_p")
VOZ_R = os.path.join(RAIZ, "TRABAJO/jornada2/voz_p_rap")   # p1 ×1,1 · p2 ×1,15 · p3 ×1,1 · p4 ×1,1 · p8 ×1,05
RAP = ("p1", "p2", "p3", "p4", "p8")
PRESENTA = os.path.join(PA, "tt_7671113870957661448.mp4")  # 720×1280: sentado 2,0 · habla 9–44 (subtítulos en y≈1480)
CAMINA = os.path.join(PA, "tt_7676298185282686226.mp4")    # 720×1280 con franjas: imagen en y 420–1089 (meme arriba, fuera)
EMPATE = os.path.join(PA, "tt_7674464032115412232.mp4")    # gol de Retamar en el 1-1 con Boca: festejo 6,0–9,5
VESTUARIO = os.path.join(PA, "tt_7701923223528688903.mp4") # vestuario festejando el pase a la final
salida = sys.argv[1]

TV = dict(p1=0.05, p2=3.1, p3=5.9, p4=7.4, p5=9.35, p6=11.2, p7=14.2, p8=15.8, p9=18.1)
N = cs(20.4)
C_GIRO = cs(TV["p6"] + 1.45)   # «¡Máximo goleador de Boca!»
estado = {}


class Franja:
    """franja de imagen de un video con franjas negras: fondo desenfocado de la misma toma + la franja ampliada."""

    def __init__(self, src, t0, y0, alto, ancho_src=720, zoom=1.35):
        self.L = Lector(src, t0, ancho_src, alto, crop=f"{ancho_src}:{alto}:0:{y0}", uno_a_uno=False)
        self.w0, self.alto, self.zoom = ancho_src, alto, zoom
        self.ult = None

    def cuadro(self):
        im = Image.fromarray(self.L.cuadro())
        fondo = fill_cover(im, W // 6, H // 6).filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
        a = (np.asarray(fondo).astype(np.float32) * 0.4).astype(np.uint8)
        fw = int(W * self.zoom); fh = int(self.alto * fw / self.w0)
        g = np.asarray(im.resize((fw, fh), Image.LANCZOS))[:, (fw - W) // 2:(fw - W) // 2 + W]
        y = int(H * 0.5 - fh / 2)
        a[max(0, y):y + fh] = g[max(0, -y):max(0, -y) + min(fh, H - max(0, y))]
        self.ult = a
        return a

    def cerrar(self):
        self.L.cerrar()


def clip(nombre, src, t0, zoom=1.0, cx=0.5, cy=0.5, osc=None, congelar_en=None, franja=None):
    def f(c, k):
        if k == 0 or nombre not in estado:
            if nombre in estado: estado[nombre].cerrar()
            if franja:
                estado[nombre] = Franja(src, t0, *franja)
            elif zoom == 1.0:
                estado[nombre] = Lector(src, t0, W, H, uno_a_uno=False)
            else:
                cw, ch = int(W / zoom) // 2 * 2, int(H / zoom) // 2 * 2
                x = int(max(0, min(W - cw, cx * W - cw / 2))); y = int(max(0, min(H - ch, cy * H - ch / 2)))
                estado[nombre] = Lector(src, t0, W, H, crop=f"{cw}:{ch}:{x}:{y}", uno_a_uno=False, vf_pre=f"scale={W}:{H}")
        a = estado[nombre].ult if (congelar_en is not None and k >= congelar_en) else estado[nombre].cuadro()
        a = a.copy()
        if osc: a = oscurecer(a, *osc)
        return a
    return f


def cerrar(nombre):
    return lambda: estado.pop(nombre).cerrar() if nombre in estado else None


def tarjeta(c, k):
    return fondo_tarjeta(c)


SEG = [
    dict(c0=0, c1=cs(1.5), fuente=clip("cara", PRESENTA, 2.0, zoom=1.4, cy=0.35, osc=(560, 0.4)), cerrar=cerrar("cara")),
    dict(c0=cs(1.5), c1=cs(3.1), fuente=clip("camina", CAMINA, 1.0, franja=(420, 668), osc=(560, 0.3)), cerrar=cerrar("camina")),
    dict(c0=cs(3.1), c1=cs(5.9), fuente=tarjeta),
    dict(c0=cs(5.9), c1=cs(7.4), fuente=clip("empate", EMPATE, 6.0, osc=(700, 0.4)), cerrar=cerrar("empate")),
    dict(c0=cs(7.4), c1=cs(11.2), fuente=tarjeta),
    dict(c0=cs(11.2), c1=C_GIRO, fuente=clip("camina2", CAMINA, 9.0, franja=(420, 668)), cerrar=cerrar("camina2")),
    dict(c0=C_GIRO, c1=cs(14.2), fuente=clip("habla", PRESENTA, 12.0, zoom=1.4, cy=0.35, osc=(560, 0.4)), cerrar=cerrar("habla")),
    dict(c0=cs(14.2), c1=cs(15.8), fuente=clip("vest", VESTUARIO, 0.7, osc=(700, 0.4)), cerrar=cerrar("vest")),
    dict(c0=cs(15.8), c1=cs(18.1), fuente=tarjeta),
    dict(c0=cs(18.1), c1=N, fuente=clip("cta", os.path.join(GL, "sdr_5333.mp4"), 2.5, osc=(640, 0.55, 1120, 0.62),
                                      congelar_en=cs(0.5)), cerrar=cerrar("cta")),
]


def ajustar(lineas, fk, size, ancho=960):
    while max(fuente(fk, size).getlength(l) for l in lineas) > ancho: size -= 2
    return size


T = []


def credito(a, b, y=1330):
    T.append(dict(c0=cs(a) if a else 0, c1=cs(b) if isinstance(b, float) else b, capa=rotulo_fuente("Video: @caplatense"),
                  x=40, y=y, entra=0))


def tarjeta_txt(a, b, g, ch=None, size=104, pop_=1.2):
    s = ajustar(g, "disp_xb", size)
    lh = int(s * 1.08)
    y = 760 - lh * (len(g) - 1) // 2
    T.append(dict(c0=cs(a), c1=cs(b), capa=capa_texto(g, "disp_xb", s), y=y, pop=pop_, sale=False))
    if ch:
        T.append(dict(c0=cs(a) + 3, c1=cs(b), capa=capa_texto([ch], "disp_b", 56, color=CEL), y=y + lh * len(g) + 30, pop=1,
                      sale=False))


T.append(dict(c0=0, c1=cs(1.5), capa=caja(["COMO DT, PALERMO", "NUNCA LE GANÓ A BOCA."], 70), y=150, pop=1, entra=0))
credito(0, 1.5)
T.append(dict(c0=cs(1.5), c1=cs(3.1), capa=caja(["¿LE GANA EN LA", "FINAL DEL MIÉRCOLES?"], 72), y=150, pop=1.1, entra=0))
credito(1.5, 3.1)
tarjeta_txt(3.1, 5.9, ["10 PARTIDOS.", "0 VICTORIAS."], "6 derrotas y 4 empates.")
T.append(dict(c0=cs(5.9), c1=cs(7.4), capa=caja(["16/08/2026: 1-1."], 84, chico="Platense–Boca.", size_chico=44), y=232,
              pop=1.1, entra=0))
credito(5.9, 7.4)
tarjeta_txt(7.4, 9.35, ["1999: ERRÓ 3 PENALES", "EN UN PARTIDO."], "Récord Guinness.")
for a, b, w in ((9.35, 9.99, "TRAVESAÑO."), (9.99, 10.51, "ARRIBA."), (10.51, 11.2, "ATAJADO.")):
    tarjeta_txt(a, b, [w], size=140, pop_=1.25)
credito(11.2, C_GIRO)
T.append(dict(c0=C_GIRO, c1=cs(14.2), capa=caja(["MÁXIMO GOLEADOR DE", "LA HISTORIA DE BOCA."], 74), y=150, pop=1.2, entra=0))
credito(12.65, 15.8)
T.append(dict(c0=cs(14.2), c1=cs(15.8), capa=caja(["PRIMERA FINAL ENTRE", "PLATENSE Y BOCA."], 72), y=232, entra=0))
tarjeta_txt(15.8, 18.1, ["MIÉRCOLES 02/12"], "Final de la Copa Argentina.")
T.append(dict(c0=cs(18.45), c1=N, capa=capa_texto(["SEGUÍ", "PATEANDO."], "disp_xb", 120), y=110, pop=1.15))
T.append(dict(c0=cs(18.8), c1=N, capa=capa_texto(["Para los que vuelven a patear:", "Founders Privée."], "disp_b", 50,
                                                 sombra=0.85), y=390, pop=1))
T.append(dict(c0=cs(18.8), c1=N, capa=capa_texto(["Roccé no tiene relación con Martín Palermo,", "Platense ni Boca Juniors."],
                                                 "inter_m", 40, color=(236, 236, 236), sombra=0.85), y=1290, pop=1))


def sonido(x, dur):
    rng = np.random.default_rng(29)
    x += np.convolve(rng.normal(0, 1, len(x)), np.ones(80) / 80, "same") * 0.02
    golpe(x, 1.5, 0.28, f0=50, caida=0.25)
    for t in (3.1, 7.4):
        tic(x, t, 0.22, 1800); golpe(x, t, 0.3, f0=48, caida=0.3)
    golpe(x, 5.9, 0.35, f0=52, caida=0.3)
    dron(x, 3.1, 11.2, f=46, g=0.045)
    for t in (9.35, 9.99, 10.51):                        # travesaño · arriba · atajado
        tic(x, t, 0.25, 2000); golpe(x, t, 0.3, f0=60, caida=0.15)
    barrido(x, 11.6, 0.9, 0.12, 200, 7000)
    g = C_GIRO / FPS
    golpe(x, g - 0.05, 0.4, f0=42, caida=0.6); brillo(x, g, 0.07)
    colchon(x, g, 15.7, [146.8, 220.0, 293.7, 370.0], 0.035, ataque=0.25, suelta=0.5)
    for t in np.arange(15.8, 18.0, 0.42):
        golpe(x, t, 0.13, f0=50, caida=0.15)
    i0, i1 = int(18.02 * SR), int(18.4 * SR)
    x[i0:i1] *= 0.15
    golpe(x, 18.1, 0.3, f0=52, caida=0.35); brillo(x, 18.45, 0.08)
    colchon(x, 18.1, dur, [110.0, 164.8, 220.0, 277.2], 0.045, ataque=0.15, suelta=0.4)


v = {k: leer_wav(os.path.join(VOZ_R if k in RAP else VOZ, f"{k}.wav")) for k in TV}
for k, db in (("p2", 2.0), ("p3", 2.0), ("p5", 1.0), ("p6", 1.5), ("p8", 1.0), ("p9", 1.0)):
    v[k] = v[k] * 10 ** (db / 20)
voces = [(TV[k], v[k]) for k in TV]
for (a, va), (b, _) in zip(voces, voces[1:]):
    assert a + len(va) / SR <= b + 1e-3, f"voces superpuestas en {a:.2f}–{b:.2f}"
render(salida, N, SEG, T, sonido, voces, techo=0.8)
