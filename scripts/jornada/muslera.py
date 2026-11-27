# Reel «Muslera: ¿gana la Libertadores el sábado?» (27/11/2026). Guion de Fede v01 (12_fede_guiones_tarde.md), voz natural.
# Apuesta en el cuadro 0: su cara (entrevista de CONMEBOL Libertadores sobre el Mundial, ampliada para que no entren los
# subtítulos quemados) + «MUSLERA, 40 AÑOS: ¿GANA LA LIBERTADORES EL SÁBADO?» → en contra: el remate sin fuerza del
# Mundial (tarjeta), lo sacaron en el entretiempo (su cara), semifinal en el Maracaná con 10, penales, patea Jorginho
# (12 de 12) → tramo calmo (la carrera) → giro: «¡Se lo ataja!» (único grito, con volumen y no con tono) → y a Paquetá, y a
# Bruno Henrique → su frase → reenganche: sábado 17:00 en el Centenario, Palmeiras también va por su revancha →
# CTA sobre la espalda real de la remera (IMG_5325): «Quedate en el arco.» El famoso nunca aparece junto a la prenda.
# Clips: TRABAJO/jornada2/muslera/ (© CONMEBOL, marca de agua intacta, sin su audio). Voz: scripts/jornada/voz_muslera.tsv.
# Uso: python3 scripts/jornada/muslera.py SALIDA.mp4
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reel import *

MU = os.path.join(RAIZ, "TRABAJO/jornada2/muslera")
GL = os.path.join(RAIZ, "TRABAJO/fomo/gl")
VOZ = os.path.join(RAIZ, "TRABAJO/jornada2/voz_u")
VOZ_R = os.path.join(RAIZ, "TRABAJO/jornada2/voz_u_rap")   # u1 ×1,1 · u2 ×1,15 · u3 ×1,1 · u4 ×1,15 · u5 ×1,1 · u7 ×1,05 · u8 ×1,1
RAP = ("u1", "u2", "u3", "u4", "u5", "u7", "u8")
CARA = os.path.join(MU, "tt_7699716590002081025.mp4")      # entrevista sobre el Mundial (subtítulos en y 1311–1404)
JORGINHO = os.path.join(MU, "tt_7702591620943777044.mp4")  # carrera 0–4,0 · atajada 4,0 (rótulos en y≈1200–1305)
PAQUETA = os.path.join(MU, "tt_7699707634881973512.mp4")   # «le atajó el penal a Paquetá»: reacción 10,5–12
BRUNO = os.path.join(MU, "tt_7699700296234159367.mp4")     # «le atajó el penal a Bruno Henrique»: en el piso con la pelota
SENALA = os.path.join(MU, "tt_7699841588662406420.mp4")    # «héroe de la noche en el Maracaná»: de pie, señala
PROMO = os.path.join(MU, "tt_7712840382895164692.mp4")     # promo de la final: jugadores de Estudiantes 0–3,6
salida = sys.argv[1]

TV = dict(u1=0.05, u2=3.2, u3=5.1, u4=6.9, u5=9.25, u6=11.3, u7=13.0, u8=16.2, u9=19.6)
N = cs(21.9)
C_GIRO = cs(TV["u6"] + 0.83)   # «¡Se lo ataja!»
estado = {}


def clip(nombre, src, t0, zoom=1.0, cx=0.5, cy=0.5, osc=None, congelar_en=None):
    def f(c, k):
        if k == 0 or nombre not in estado:
            if nombre in estado: estado[nombre].cerrar()
            if zoom == 1.0:
                estado[nombre] = Lector(src, t0, W, H, uno_a_uno=False)
            else:
                cw, ch = int(W / zoom) // 2 * 2, int(H / zoom) // 2 * 2
                x = int(max(0, min(W - cw, cx * W - cw / 2))); y = int(max(0, min(H - ch, cy * H - ch / 2)))
                estado[nombre] = Lector(src, t0, W, H, crop=f"{cw}:{ch}:{x}:{y}", uno_a_uno=False,
                                        vf_pre=f"scale={W}:{H}")
        a = estado[nombre].ult if (congelar_en is not None and k >= congelar_en) else estado[nombre].cuadro()
        a = a.copy()
        if osc: a = oscurecer(a, *osc)
        return a
    return f


def cerrar(nombre):
    return lambda: estado.pop(nombre).cerrar() if nombre in estado else None


def tarjeta(c, k):
    return fondo_tarjeta(c)


# el tramo de Jorginho es continuo: 9,25 s del reel = 1,12 s de la fuente, así la atajada (4,0) cae en el giro
T_JOR = 4.0 - (C_GIRO / FPS - TV["u5"])
SEG = [
    dict(c0=0, c1=cs(3.2), fuente=clip("cara", CARA, 0.3, zoom=1.5, cy=0.0, osc=(560, 0.4)), cerrar=cerrar("cara")),
    dict(c0=cs(3.2), c1=cs(5.1), fuente=tarjeta),
    dict(c0=cs(5.1), c1=cs(6.9), fuente=clip("cara2", CARA, 15.5, zoom=1.5, cy=0.0, osc=(560, 0.4)), cerrar=cerrar("cara2")),
    dict(c0=cs(6.9), c1=cs(9.25), fuente=tarjeta),
    dict(c0=cs(9.25), c1=cs(13.0), fuente=clip("jor", JORGINHO, T_JOR, osc=(600, 0.3)), cerrar=cerrar("jor")),
    dict(c0=cs(13.0), c1=cs(13.8), fuente=clip("paq", PAQUETA, 10.6, osc=(600, 0.3)), cerrar=cerrar("paq")),
    dict(c0=cs(13.8), c1=cs(14.6), fuente=clip("bru", BRUNO, 5.2, osc=(600, 0.3)), cerrar=cerrar("bru")),
    dict(c0=cs(14.6), c1=cs(16.2), fuente=clip("sen", SENALA, 36.5, osc=(760, 0.5)), cerrar=cerrar("sen")),
    dict(c0=cs(16.2), c1=cs(19.6), fuente=clip("promo", PROMO, 0.2, osc=(700, 0.4)), cerrar=cerrar("promo")),
    dict(c0=cs(19.6), c1=N, fuente=clip("cta", os.path.join(GL, "sdr_5325_full.mp4"), 15.6, osc=(640, 0.6, 1120, 0.62),
                                      congelar_en=cs(1.2)), cerrar=cerrar("cta")),
]


def ajustar(lineas, fk, size, ancho=960):
    while max(fuente(fk, size).getlength(l) for l in lineas) > ancho: size -= 2
    return size


def tarj(g, ch=None, size=104):
    s = ajustar(g, "disp_xb", size)
    return capa_texto(g, "disp_xb", s), (capa_texto([ch], "disp_b", 54, color=CEL) if ch else None), s


T = []


def credito(a, b, y=1330):
    T.append(dict(c0=cs(a) if a else 0, c1=cs(b) if isinstance(b, float) else b, capa=rotulo_fuente("Video: @libertadores"),
                  x=40, y=y, entra=0))


def tarjeta_txt(a, b, g, ch):
    cg, cc, s = tarj(g, ch)
    lh = int(s * 1.08)
    y = 760 - lh * (len(g) - 1) // 2
    T.append(dict(c0=cs(a), c1=cs(b), capa=cg, y=y, pop=1.2, sale=False))
    if cc: T.append(dict(c0=cs(a) + 3, c1=cs(b), capa=cc, y=y + lh * len(g) + 30, pop=1, sale=False))


T.append(dict(c0=0, c1=cs(3.2), capa=caja(["MUSLERA, 40 AÑOS:", "¿GANA LA LIBERTADORES", "EL SÁBADO?"], 64), y=120, pop=1,
              entra=0))
credito(0, 3.2)
tarjeta_txt(3.2, 5.1, ["MUNDIAL 2026:", "NO RETUVO UN", "REMATE SIN FUERZA."], "España 1-0. Uruguay, afuera.")
T.append(dict(c0=cs(5.1), c1=cs(6.9), capa=caja(["LO SACARON EN", "EL ENTRETIEMPO."], 70, chico="Pidió disculpas.",
                                                size_chico=46), y=150, entra=0))
credito(5.1, 6.9)
tarjeta_txt(6.9, 9.25, ["SEMIFINAL EN EL", "MARACANÁ: PENALES."], "Con 10, casi todo el segundo tiempo.")
T.append(dict(c0=cs(9.25), c1=C_GIRO, capa=caja(["JORGINHO:", "12 DE 12 EN FLAMENGO."], 72), y=1100, entra=0))  # tapa el rótulo (dura hasta 3,9 s de la fuente)
credito(9.25, C_GIRO, y=150)
T.append(dict(c0=C_GIRO, c1=cs(13.0), capa=caja(["SE LO ATAJA."], 92), y=1150, pop=1.2, entra=0))      # tapa «No es problema…»
credito(13.0, 16.2, y=150)
T.append(dict(c0=cs(13.0), c1=cs(13.8), capa=caja(["Y A PAQUETÁ."], 84), y=232, pop=1.15, entra=0))
T.append(dict(c0=cs(13.8), c1=cs(14.6), capa=caja(["Y A BRUNO HENRIQUE."], 80), y=232, pop=1.15, entra=0))
T.append(dict(c0=cs(14.6), c1=cs(16.2), capa=capa_texto(["“El fútbol siempre", "te da otra oportunidad.”"], "disp_xb", 72),
              y=250, pop=1.08))
T.append(dict(c0=cs(14.6) + 4, c1=cs(16.2), capa=capa_texto(["Muslera, después de la semi."], "disp_b", 44, color=CEL,
                                                            sombra=0.8), y=430, pop=1))
T.append(dict(c0=cs(16.2), c1=cs(19.6), capa=caja(["SÁBADO · 17:00 · CENTENARIO"], 70,
                                                chico="Palmeiras también va por su revancha.", size_chico=44), y=232, entra=0))
credito(16.2, 19.6)
T.append(dict(c0=cs(19.95), c1=N, capa=capa_texto(["QUEDATE", "EN EL ARCO."], "disp_xb", 120), y=110, pop=1.15))
T.append(dict(c0=cs(20.3), c1=N, capa=capa_texto(["Lo que importa es la próxima:", "Founders Privée."], "disp_b", 50,
                                                 sombra=0.85), y=390, pop=1))
T.append(dict(c0=cs(20.3), c1=N, capa=capa_texto(["Roccé no tiene relación con Fernando Muslera,",
                                                  "Estudiantes, Flamengo, Palmeiras ni la CONMEBOL."],
                                                 "inter_m", 38, color=(236, 236, 236), sombra=0.85), y=1290, pop=1))


def sonido(x, dur):
    rng = np.random.default_rng(28)
    x += np.convolve(rng.normal(0, 1, len(x)), np.ones(80) / 80, "same") * 0.02
    for t in (3.2, 6.9):
        tic(x, t, 0.22, 1800); golpe(x, t, 0.3, f0=48, caida=0.3)
    golpe(x, 5.1, 0.28, f0=50, caida=0.25)
    dron(x, 3.2, 9.25, f=46, g=0.045)
    golpe(x, 9.25, 0.3, f0=46, caida=0.3)
    barrido(x, 11.3, 0.8, 0.12, 200, 7000)               # subida en la carrera
    g = C_GIRO / FPS
    golpe(x, g - 0.05, 0.4, f0=42, caida=0.6); brillo(x, g, 0.07)
    golpe(x, 13.0, 0.35, f0=52, caida=0.3); golpe(x, 13.8, 0.35, f0=52, caida=0.3)
    colchon(x, g, 16.1, [146.8, 220.0, 293.7, 370.0], 0.035, ataque=0.25, suelta=0.5)
    for t in np.arange(16.2, 19.5, 0.42):
        golpe(x, t, 0.13, f0=50, caida=0.15)
    i0, i1 = int(19.52 * SR), int(19.9 * SR)
    x[i0:i1] *= 0.15
    golpe(x, 19.6, 0.3, f0=52, caida=0.35); brillo(x, 19.95, 0.08)
    colchon(x, 19.6, dur, [110.0, 164.8, 220.0, 277.2], 0.045, ataque=0.15, suelta=0.4)


v = {k: leer_wav(os.path.join(VOZ_R if k in RAP else VOZ, f"{k}.wav")) for k in TV}
for k, db in (("u2", 2.0), ("u3", 2.0), ("u5", 2.0), ("u6", 1.5), ("u8", 1.0), ("u9", 1.0)):
    v[k] = v[k] * 10 ** (db / 20)
voces = [(TV[k], v[k]) for k in TV]
for (a, va), (b, _) in zip(voces, voces[1:]):
    assert a + len(va) / SR <= b + 1e-3, f"voces superpuestas en {a:.2f}–{b:.2f}"
render(salida, N, SEG, T, sonido, voces, techo=0.8)
