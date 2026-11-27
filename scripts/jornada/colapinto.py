# Reel «Colapinto: ¿lo pasa el domingo?» (27/11/2026). Guion de Fede v01 con corrección de Roma (video oficial donde existe).
# Apuesta en el cuadro 0: su cara (entrevista de Alpine, antes del rótulo P6) + «a 3 puntos de Lindblad, ¿lo pasa el domingo en
# Qatar?» → erra el tiro (@f1). En contra a toda velocidad (tarjetas: Las Vegas 2024 choque, 2025 15.º, 6 carreras sin puntos),
# a favor y en contra en la carrera (largada oficial de Las Vegas 2026), tramo calmo y giro: mete el segundo tiro → P6 real
# (Alpine; la cara del cuadro 0 era esa misma entrevista). Reenganche: Qatar, domingo 13:00, queda abierta. Significado:
# «Errar el primero no define nada.» → CTA con la placa real (IMG_5359).
# v02 (auditoría de Roma): cara en el cuadro 0, tarjetas de 6,8 s a 5,5 s (voz c2–c4 ×1,2 con atempo, c1 ×1,08, c8 ×1,1:
# voz_c_rap/), duración 23,6 → 21,8 s, descargo en dos renglones de 40 px por encima de la interfaz de Reels (placa subida
# con zoom 1,1). La largada arranca en 8,1 s de la fuente: antes pasan los McLaren y parecería que muestra el sobrepaso.
# Clips: TRABAJO/colapinto/ (© Formula 1 / Alpine, marca de agua intacta, sin su audio). Voz: scripts/jornada/voz_colapinto.tsv.
# Uso: python3 scripts/jornada/colapinto.py SALIDA.mp4
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reel import *

CL = os.path.join(RAIZ, "TRABAJO/colapinto")
FEED = os.path.join(RAIZ, "TRABAJO/feed")
GL = os.path.join(RAIZ, "TRABAJO/fomo/gl")
VOZ = os.path.join(RAIZ, "TRABAJO/jornada/voz_c")
VOZ_R = os.path.join(RAIZ, "TRABAJO/jornada/voz_c_rap")   # c1 ×1,08 · c2–c4 ×1,2 · c8 ×1,1 (ffmpeg atempo)
RAP = ("c1", "c2", "c3", "c4", "c8")
BASKET = os.path.join(CL, "tt_7712543529678949654.mp4")
LARGADA = os.path.join(CL, "tt_7711352916942130454.mp4")
P6 = os.path.join(CL, "tt_7710975293321760022.mp4")
OOPS = os.path.join(CL, "tt_7712595829265042727.mp4")
salida = sys.argv[1]

# voces (s)
TV = dict(c1=0.05, c2=2.60, c3=4.90, c4=6.49, c5=8.03, c6=10.97, c7=12.17, c8=14.67, c9=16.88, c10=19.43)
N = cs(21.8)
C_GRITO = cs(TV["c7"] + 1.358)   # «¡Y termina sexto!»

# ---------- segmentos ----------
estado = {}


def clip(nombre, src, t0, zoom=1.0, cx=0.5, cy=0.5, osc=None, congelar_en=None):
    def f(c, k):
        if k == 0 or nombre not in estado:
            if nombre in estado: estado[nombre].cerrar()
            estado[nombre] = lector_clip(src, t0, zoom, cx, cy)
        if congelar_en is not None and k >= congelar_en:
            a = estado[nombre].ult
        else:
            a = estado[nombre].cuadro()
        a = a.copy()
        if osc: a = oscurecer(a, *osc)
        return a
    return f


def cerrar(nombre):
    return lambda: estado.pop(nombre).cerrar() if nombre in estado else None


def tarjeta(c, k):
    return fondo_tarjeta(c)


SEG = [
    dict(c0=0, c1=cs(0.6), fuente=clip("p0", P6, 0.0, zoom=1.5, cx=0.6, cy=0.0, osc=(520, 0.35)), cerrar=cerrar("p0")),  # su cara
    dict(c0=cs(0.6), c1=cs(2.5), fuente=clip("b1", BASKET, 2.45, osc=(760, 0.5)), cerrar=cerrar("b1")),  # tira y erra
    dict(c0=cs(2.5), c1=cs(8.0), fuente=tarjeta),
    dict(c0=cs(8.0), c1=cs(12.14), fuente=clip("lg", LARGADA, 8.1, osc=(700, 0.35)), cerrar=cerrar("lg")),
    dict(c0=cs(12.14), c1=cs(13.62), fuente=clip("b2", BASKET, 5.61, osc=(700, 0.3)), cerrar=cerrar("b2")),
    dict(c0=cs(13.62), c1=cs(14.67), fuente=clip("p6", P6, 1.95, osc=(0, 0, 1350, 0.6)), cerrar=cerrar("p6")),
    dict(c0=cs(14.67), c1=cs(16.83), fuente=clip("oo", OOPS, 0.0, osc=(720, 0.35)), cerrar=cerrar("oo")),
    dict(c0=cs(16.83), c1=cs(19.43), fuente=clip("g26", os.path.join(FEED, "sdr_5326.mp4"), 0.6, osc=(720, 0.55)),
         cerrar=cerrar("g26")),
    dict(c0=cs(19.43), c1=N, fuente=clip("g59", os.path.join(GL, "sdr_5359.mp4"), 6.9, zoom=1.1, cy=0.58,
                                         osc=(900, 0.5, 1250, 0.55), congelar_en=cs(1.4)), cerrar=cerrar("g59")),
]

# ---------- textos ----------
T = []
gancho = caja(["COLAPINTO, A 3 PUNTOS", "DE LINDBLAD."], 78, chico="¿LO PASA EL DOMINGO?", size_chico=64)
T.append(dict(c0=0, c1=cs(2.5), capa=gancho, y=232, pop=1, entra=0))
T.append(dict(c0=0, c1=cs(0.6), capa=rotulo_fuente("Video: @alpinef1team"), x=40, y=150, entra=0))
T.append(dict(c0=cs(0.6), c1=cs(2.5), capa=rotulo_fuente("Video: @f1"), x=40, y=150, entra=0))


def tarj(g, ch, size=104):
    return capa_texto(g, "disp_xb", size), capa_texto([ch], "disp_b", 58, color=CEL)


for (a, b, g, ch) in [(2.5, 4.88, ["LAS VEGAS 2024"], "Choque en la Q2."),
                      (4.88, 6.47, ["LAS VEGAS 2025", "15.º"], "“El auto fue un desastre.”"),
                      (6.47, 8.0, ["6 CARRERAS", "SIN PUNTOS"], "Así llegó a Las Vegas 2026.")]:
    cg, cc = tarj(g, ch)
    T.append(dict(c0=cs(a), c1=cs(b), capa=cg, y=760 - 60 * (len(g) - 1), pop=1.2, sale=False))
    T.append(dict(c0=cs(a) + 3, c1=cs(b), capa=cc, y=760 + 120 * len(g) - 40 + 20, pop=1, sale=False))

T.append(dict(c0=cs(8.0), c1=cs(10.94), capa=caja(["VUELTA 12: PASÓ A", "LOS DOS McLAREN"], 76, rotulo="LAS VEGAS 2026"), y=330))
T.append(dict(c0=cs(10.94), c1=cs(12.14), capa=caja(["SE LOS DEVOLVIERON."], 76, rotulo="LAS VEGAS 2026",
                                                    chico="Además: gomas traseras recalentadas.", size_chico=40), y=330,
              entra=2))
T.append(dict(c0=cs(8.0), c1=cs(12.14), capa=rotulo_fuente("Video: @f1"), x=40, y=150, entra=0))
T.append(dict(c0=cs(12.14), c1=cs(13.62), capa=rotulo_fuente("Video: @f1"), x=40, y=150, entra=0))
T.append(dict(c0=cs(13.99), c1=cs(14.67), capa=caja(["8 PUNTOS."], 84, chico="CORTÓ LA RACHA.", size_chico=56),
              y=1380, pop=1.2, entra=2))
T.append(dict(c0=cs(13.62), c1=cs(14.67), capa=rotulo_fuente("Video: @alpinef1team"), x=40, y=150, entra=0))
T.append(dict(c0=cs(14.67), c1=cs(16.83), capa=caja(["QATAR · DOMINGO 13:00"], 76, chico="Sábado 15:00 clasifica.",
                                                    size_chico=46, alfa=0.94, ancho_min=760), y=232, entra=0))
T.append(dict(c0=cs(14.67), c1=cs(16.83), capa=rotulo_fuente("Video: @alpinef1team"), x=40, y=150, entra=0))
T.append(dict(c0=cs(17.18), c1=cs(19.43), capa=capa_texto(["ERRAR EL PRIMERO", "NO DEFINE NADA."], "disp_xb", 96), y=150,
              pop=1.15))
T.append(dict(c0=cs(19.88), c1=N, capa=capa_texto(["SEGUIR HASTA", "LOGRARLO."], "disp_xb", 120), y=250, pop=1.15))
T.append(dict(c0=cs(20.23), c1=N, capa=capa_texto(["Lo tuyo, hoy: Founders Privée."], "disp_b", 54, sombra=0.8), y=545,
              pop=1))
T.append(dict(c0=cs(20.23), c1=N, capa=capa_texto(["Roccé no tiene relación con", "Franco Colapinto, Alpine ni la F1."],
                                                 "inter_m", 40, color=(232, 232, 232), sombra=0.8), y=1300, pop=1))


# ---------- sonido ----------
def sonido(x, dur):
    rng = np.random.default_rng(27)
    x += np.convolve(rng.normal(0, 1, len(x)), np.ones(80) / 80, "same") * 0.02
    golpe(x, 0.6, 0.25, f0=50, caida=0.2)
    golpe(x, 1.43, 0.45, f0=120, caida=0.06)            # la pelota pega en el aro
    golpe(x, 1.50, 0.3, f0=50, caida=0.25)
    for t in (2.5, 4.88, 6.47):                        # tarjetas
        tic(x, t, 0.22, 1800); golpe(x, t, 0.32, f0=48, caida=0.3)
    dron(x, 2.5, 8.0, f=46, g=0.05)
    barrido(x, 7.92, 0.35, 0.16, 300, 5000)
    for t in np.arange(8.07, 12.07, 0.5):               # pulso de carrera, bajo la voz
        golpe(x, t, 0.12, f0=52, caida=0.12)
    golpe(x, 10.94, 0.3, f0=44, caida=0.35)
    barrido(x, 12.22, 1.35, 0.12, 200, 7000)           # subida hacia el giro
    golpe(x, C_GRITO / FPS, 0.6, f0=42, caida=0.7); brillo(x, C_GRITO / FPS, 0.1)
    colchon(x, C_GRITO / FPS, 16.73, [146.8, 220.0, 293.7, 370.0], 0.05, ataque=0.2, suelta=0.5)
    for t in np.arange(14.67, 16.73, 0.42):             # pulso: queda abierta
        golpe(x, t, 0.14, f0=50, caida=0.15)
    i0, i1 = int(16.78 * SR), int(17.23 * SR)
    x[i0:i1] *= 0.15                                    # casi silencio antes del significado
    golpe(x, 19.43, 0.4, f0=52, caida=0.4); brillo(x, 19.88, 0.12)
    colchon(x, 19.43, dur, [110.0, 164.8, 220.0, 277.2], 0.06, ataque=0.15, suelta=0.4)


v = {k: leer_wav(os.path.join(VOZ_R if k in RAP else VOZ, f"{k}.wav")) for k in TV}
for k, db in (("c2", 2.0), ("c3", 2.0), ("c4", 2.0), ("c6", 2.0), ("c8", 1.0), ("c9", 2.0), ("c10", 1.0)):
    v[k] = v[k] * 10 ** (db / 20)
voces = [(TV[k], v[k]) for k in TV]
for (a, va), (b, _) in zip(voces, voces[1:]):
    assert a + len(va) / SR <= b + 1e-3, f"voces superpuestas en {a:.2f}–{b:.2f}"
render(salida, N, SEG, T, sonido, voces, techo=0.8)
