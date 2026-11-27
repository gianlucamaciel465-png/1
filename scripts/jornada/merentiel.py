# Reel «Merentiel: ¿revancha en la misma copa?» (27/11/2026). Guion de Fede v01 con el ángulo de Roma.
# Apuesta en el cuadro 0: Sudamericana 2024, Merentiel erra el penal decisivo y Boca queda eliminado (imagen de nuestro reel
# del 02/11, que trae la transmisión de ESPN). Pista plantada: «“Siempre tenés revancha.” · 02/11/2026». La final de la misma
# copa (21/11/2026): travesaño (otro «no») → tramo calmo → giro: el gol (clips oficiales de @sudamericana) → reenganche: la frase
# se la dijimos el 02/11, 19 días antes → CTA con la placa real (IMG_5361).
# v02 (auditoría de Roma): el plano general del penal dura 1,05 s y pasa a Merentiel de rodillas (reel 4,48 s, después del
# fundido de 4,27–4,47); descargo en dos renglones de 40 px entre el CTA y la placa (abajo tapaba el «2026» de la placa o
# quedaba bajo la interfaz de Reels).
# v03 (Gianluca 27/11 15:38 UTC): voz natural, sin subidas de tono en el grito ni en el quiebre (voz_m_nat/).
# «FINAL · 2-0» se mantiene: la final terminó 2-0 con goles de Ascacíbar y Merentiel (TUDN, en 01_pepe_informe.md).
# Uso: python3 scripts/jornada/merentiel.py SALIDA.mp4
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reel import *

MR = os.path.join(RAIZ, "TRABAJO/merentiel")
FEED = os.path.join(RAIZ, "TRABAJO/feed")
VOZ = os.path.join(RAIZ, "TRABAJO/jornada/voz_m_nat")   # v03: voz natural (mismo tono; énfasis por volumen)
REEL = os.path.join(MR, "ig_DfP4jptTOP_.mp4")
TRAV = os.path.join(MR, "tt_7710790012186447124.mp4")
GOL = os.path.join(MR, "tt_7710819635519589650.mp4")
ARRIBA = os.path.join(MR, "tt_7710790069065452807.mp4")
TRIBUNA = os.path.join(MR, "tt_7710785699766652180.mp4")
HUMO = (214, 225, 233)
salida = sys.argv[1]

TV = dict(m1=0.05, m2=3.75, m3=5.75, m4=8.18, m5=10.10, m6=12.95, m7=16.15)
N = cs(19.9)
C_TRAV = cs(TV["m4"] + 0.95)     # «travesaño» = la pelota en el travesaño (3,90 s de la fuente)
C_GOL = cs(TV["m5"] + 1.323)      # «¡Gol…!»
estado = {}


def clip(nombre, src, t0, osc=None, congelar_en=None, zoom=1.0, cx=0.5, cy=0.5):
    def f(c, k):
        if k == 0 or nombre not in estado:
            if nombre in estado: estado[nombre].cerrar()
            estado[nombre] = lector_clip(src, t0, zoom, cx, cy)
        a = estado[nombre].ult if (congelar_en is not None and k >= congelar_en) else estado[nombre].cuadro()
        a = a.copy()
        if osc: a = oscurecer(a, *osc)
        return a
    return f


def ventana(nombre, t0):
    def f(c, k):
        if k == 0 or nombre not in estado:
            if nombre in estado: estado[nombre].cerrar()
            estado[nombre] = Ventana(REEL, t0, 572, 600, zoom=1.35, cy=0.52)
        return estado[nombre].cuadro()
    return f


def cerrar(nombre):
    return lambda: estado.pop(nombre).cerrar() if nombre in estado else None


_humo = None


def humo(c, k):
    global _humo
    if _humo is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
        v = np.clip(1.04 - r * 0.22, 0.9, 1.04)[..., None]
        _humo = np.clip(np.array(HUMO, np.float32)[None, None] * v, 0, 255).astype(np.uint8)
    return grano(_humo.copy(), 2.0, c)


SEG = [
    dict(c0=0, c1=cs(1.05), fuente=ventana("r1", 1.65), cerrar=cerrar("r1")),
    dict(c0=cs(1.05), c1=cs(3.72), fuente=ventana("r2", 4.48), cerrar=cerrar("r2")),
    dict(c0=cs(3.72), c1=cs(5.72), fuente=humo),
    dict(c0=cs(5.72), c1=cs(10.05), fuente=clip("tr", TRAV, 3.90 - (C_TRAV / FPS - 5.72), osc=(760, 0.4)), cerrar=cerrar("tr")),
    dict(c0=cs(10.05), c1=cs(11.75), fuente=clip("go", GOL, 12.0 - (11.45 - 10.05), osc=(760, 0.35)), cerrar=cerrar("go")),
    dict(c0=cs(11.75), c1=cs(12.9), fuente=clip("ar", ARRIBA, 5.4, osc=(760, 0.35)), cerrar=cerrar("ar")),
    dict(c0=cs(12.9), c1=cs(16.1), fuente=humo),
    dict(c0=cs(16.1), c1=N, fuente=clip("g61", os.path.join(FEED, "sdr_5361.mp4"), 0.0, osc=(1050, 0.66, 1500, 0.5),
                                        congelar_en=cs(2.85)), cerrar=cerrar("g61")),
]

T = []
T.append(dict(c0=0, c1=cs(2.55), capa=caja(["MERENTIEL: ¿REVANCHA", "EN LA MISMA COPA?"], 76, rotulo="SUDAMERICANA 2024"),
              y=200, pop=1, entra=0))
T.append(dict(c0=cs(2.55), c1=cs(3.72), capa=caja(["ERRÓ EL PENAL DECISIVO."], 72, rotulo="SUDAMERICANA 2024",
                                                  chico="Boca, eliminado.", size_chico=46), y=200, entra=0))
T.append(dict(c0=0, c1=cs(3.72), capa=rotulo_fuente("Imagen: transmisión ESPN"), x=40, y=1420, entra=0))
frase = capa_texto(["“Siempre tenés", "revancha.”"], "serif", 132, color=NOCHE, sombra=0)
T.append(dict(c0=cs(3.72), c1=cs(5.72), capa=frase, y=700, pop=1.08, sale=False))
T.append(dict(c0=cs(3.72) + 6, c1=cs(5.72), capa=capa_texto(["02/11/2026"], "inter_sb", 40, color=NOCHE, sombra=0, track=6),
              y=1030, pop=1, sale=False))
T.append(dict(c0=cs(5.72), c1=C_TRAV, capa=caja(["21/11/2026 · LA FINAL"], 76, chico="La misma copa.", size_chico=48),
              y=1240))
T.append(dict(c0=C_TRAV, c1=cs(10.05), capa=caja(["TRAVESAÑO."], 110), y=1240, pop=1.25, entra=1))
T.append(dict(c0=C_GOL, c1=cs(12.9), capa=caja(["GOL DE MERENTIEL."], 92, chico="FINAL · 2-0", size_chico=52), y=1240,
              pop=1.25, entra=1))
T.append(dict(c0=cs(5.72), c1=cs(12.9), capa=rotulo_fuente("Video: @sudamericana"), x=40, y=150, entra=0))
T.append(dict(c0=cs(12.9), c1=cs(16.1), capa=frase, y=640, pop=1, sale=False, entra=2))
T.append(dict(c0=cs(13.25), c1=cs(16.1), capa=capa_texto(["Se lo dijimos el 02/11.", "19 días antes de la final."], "disp_b",
                                                        56, color=NOCHE, sombra=0), y=990, pop=1, sale=False))
T.append(dict(c0=cs(17.2), c1=N, capa=capa_texto(["SEGUIR HASTA", "LOGRARLO."], "disp_xb", 120), y=250, pop=1.15))
T.append(dict(c0=cs(17.5), c1=N, capa=capa_texto(["Tampoco es tu final: Founders Privée."], "disp_b", 52, sombra=0.8), y=545,
              pop=1))
T.append(dict(c0=cs(17.5), c1=N, capa=capa_texto(["Roccé no tiene relación con", "Miguel Merentiel ni con Boca Juniors."],
                                                 "inter_m", 40, color=(232, 232, 232), sombra=0.8), y=780, pop=1))


def sonido(x, dur):
    rng = np.random.default_rng(11)
    x += np.convolve(rng.normal(0, 1, len(x)), np.ones(80) / 80, "same") * 0.02
    dron(x, 0.0, 3.72, f=44, g=0.05)
    golpe(x, 2.55, 0.35, f0=46, caida=0.4)
    tic(x, 3.72, 0.2, 1800); brillo(x, 3.72, 0.08)
    barrido(x, 5.62, 0.3, 0.14, 300, 5000)
    for t in np.arange(5.8, C_TRAV / FPS - 0.5, 0.45):
        golpe(x, t, 0.09, f0=52, caida=0.1)
    golpe(x, C_TRAV / FPS - 0.06, 0.32, f0=110, caida=0.06); golpe(x, C_TRAV / FPS - 0.06, 0.22, f0=44, caida=0.4)  # travesaño
    i0, i1 = int(10.05 * SR), int((C_GOL / FPS - 0.05) * SR)
    x[i0:i1] *= 0.2                                                                                  # tramo calmo
    barrido(x, C_GOL / FPS - 0.9, 0.85, 0.06, 200, 7000)
    golpe(x, C_GOL / FPS, 0.35, f0=42, caida=0.6)
    colchon(x, C_GOL / FPS + 0.3, 16.0, [146.8, 220.0, 293.7, 370.0], 0.03, ataque=0.3, suelta=0.5)
    tic(x, 12.9, 0.18, 1800)
    golpe(x, 16.1, 0.4, f0=52, caida=0.4); brillo(x, 17.2, 0.12)
    colchon(x, 16.1, dur, [110.0, 164.8, 220.0, 277.2], 0.06, ataque=0.15, suelta=0.4)


v = {k: leer_wav(os.path.join(VOZ, f"{k}.wav")) for k in TV}
for k, db in (("m2", 2.0), ("m4", 2.0), ("m6", 2.0), ("m7", 1.0)):
    v[k] = v[k] * 10 ** (db / 20)
voces = [(TV[k], v[k]) for k in TV]
tribuna = audio_clip(TRIBUNA, 0.0, 1.55, gan=0.9, fade=0.05)
n_ = int(0.5 * SR); tribuna[-n_:] *= np.linspace(1, 0, n_) ** 2
render(salida, N, SEG, T, sonido, voces, techo=0.8, extra_audio=[(C_GOL / FPS + 0.12, tribuna)])
