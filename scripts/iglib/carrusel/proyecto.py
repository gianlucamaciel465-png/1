# IGLIB-3 «Ambos permanecen» v01 · carrusel mixto 4:5 (1080×1350) · fuente única de verdad.
# Guion: /mnt/project-files/piezas/IGLIB_funcion_libertadores/05_fede_guiones_G1.md (IGLIB-3)
# Correcciones que mandan: 06_roma_aprobacion_G1.md (L6: «Ambos» → «Ambas» después de tachar) + aviso del
# coordinador del 25/11: en L5 la Negra va con otra foto de PRODUCTO (no negra_frente_detalle_estampado.jpg).
#
# Coordenadas de video: píxeles del cuadro ya rotado y llevado a 1080×1920 (las 4K se bajan a la mitad en video.py).
# Coordenadas de foto: píxeles del archivo original de PRODUCTO/.

FPS = 30
W, H = 1080, 1350
PROD = "/home/user/1/PRODUCTO"
LOGO = "/home/user/1/LOGO/rocce_logo.png"
TRAB = "/home/user/1/TRABAJO/iglib/carrusel"
DOCS = "/mnt/project-files/piezas/IGLIB_funcion_libertadores"
SALIDA = DOCS + "/IGLIB-3_v01"
EVID = DOCS + "/evidencia_carrusel_v01"
VER = "v01"

# ---------- blanco neutro (regla Roma 06 §5: en tela, B−R ≤ +8; misma toma = mismo color) ----------
# Ganancias por canal medidas sobre la tela blanca (mediana de una zona sin estampado) para llevarla a gris neutro.
# Se aplican en RGB con una rampa: plenas si el canal mínimo ≤ 230 y nulas desde 250 (la espuma y el cielo
# quemados no se amarillean). IMG_4530 usa la corrección ffmpeg ya probada en encargos anteriores.
NEUTRO = {
    "IMG_7857": (1.047, 1.021, 0.938),   # medido: tela (155,159,173) B−R +18
    "IMG_4631": (1.062, 1.024, 0.925),   # medido tras mobius: tela (216,224,248) B−R +32
    "blanca_puesta_espalda_balcon_playa.jpg": (1.035, 1.016, 0.952),  # medido en sRGB: (161,164,175) B−R +14
}
CORR_FFMPEG = {"IMG_4530": "colorchannelmixer=rr=1.05:gg=1.03:bb=0.92"}   # medido: B−R +31 → +3

# ---------- ventanas de video ----------
# Cada ventana: toma, desde (s), cuadros, caja en la lámina (x, y, w, h), recorte y máscara.
#   recorte "fijo": (cx, cy, ancho) en la toma
#   recorte "claves": lista de (cuadro, cx, cy) + ancho; se interpola y se suaviza (σ en cuadros)
#   recorte "completo": toda la toma escalada a la caja, con relleno desenfocado de la misma toma (L3 izquierda)
#   recorte "seguir_y": ancho completo, y0 base + desplazamiento vertical medido por correlación de fase
LAMINAS = {
    "L1": dict(tipo="mp4", cuadros=72, ventanas=[
        dict(id="v1a", toma="IMG_7857", desde=1.00, caja=(160, 646, 250, 250), mascara="circulo",
             recorte="claves", ancho=820, sigma=3,
             claves=[(0, 410, 1030), (10, 440, 1030), (20, 370, 1030), (30, 330, 990), (40, 400, 970),
                     (50, 375, 930), (60, 290, 870), (70, 330, 850), (71, 335, 848)],
             nota="Blanca puesta de espaldas frente al mar: círculo de hombros a cintura que sigue el estampado"),
        dict(id="v1b", toma="IMG_7793", desde=2.40, caja=(670, 646, 250, 250), mascara="circulo",
             recorte="claves", ancho=900, sigma=3,
             claves=[(0, 540, 940), (18, 510, 980), (36, 502, 1020), (54, 522, 1030), (71, 540, 980)],
             nota="Negra puesta de espaldas en el balcón: círculo de hombros a cintura"),
    ]),
    "L2": dict(tipo="mp4", cuadros=63, ventanas=[
        dict(id="v2", toma="IMG_4530", desde=0.80, caja=(540, 0, 540, 1350), mascara=None,
             recorte="fijo", centro=(548, 960), ancho=768,
             nota="DE CERCA: la Blanca sostenida, recorte 0,4 (768×1920, toda la altura) con ROCCÉ completo"),
    ]),
    "L3": dict(tipo="mp4", cuadros=45, ventanas=[
        dict(id="v3a", toma="IMG_7793", desde=92 / 30,   # 3,067 s: sobre la grilla de cuadros de la toma (3,05 duplicaba el primero)
             caja=(0, 0, 540, 1350), mascara=None,
             recorte="completo", nitido=(0, 240, 540, 960), desenfoque=22,
             relleno_arriba=(0, 0, 270, 120), relleno_abajo=(0, 1845, 270, 1920),
             nota="PUESTA: la Negra de manga a manga (3,07–4,57 s: único tramo de la toma con las dos mangas adentro)"),
        dict(id="v3b", toma="IMG_7824", desde=5.80, caja=(540, 0, 540, 1350), mascara=None,
             recorte="claves", ancho=768, sigma=4, cy=960,
             claves=[(0, 492, 960), (6, 495, 960), (16, 510, 960), (26, 540, 960), (36, 560, 960), (44, 560, 960)],
             nota="DE CERCA: ROCCÉ tono sobre tono completo, recorte 0,4 que sigue el centro de ROCCÉ"),
    ]),
    "L4": dict(tipo="png"),
    "L5": dict(tipo="png"),
    "L6": dict(tipo="mp4", cuadros=132, animada=True, ventanas=[
        dict(id="v6", toma="IMG_4631", desde=1.60, caja=(0, 0, 1080, 1350), mascara=None,
             recorte="seguir_y", y0=430, zona=(650, 600, 950, 1800), umbral=75, sigma=3,
             nota="Las dos remeras sobre las rocas; la ola rompe a los 3,0–3,5 s de la toma (cuadros 42–57 de la lámina)"),
    ]),
}

# ---------- fotos fijas (recursos para las capas de Chromium) ----------
# nombre: (archivo, caja x, y, w, h en el original, salida w×h)
FOTOS = {
    "L2_puesta": ("blanca_puesta_espalda_balcon_playa.jpg", (454, 0, 1030, 2576), (540, 1350)),
    "L5_blanca": ("blanca_frente_detalle_estampado.jpg", (0, 690, 1512, 945), (1080, 675)),
    # L5 Negra: negra_frente_arena_F266ACD9.png es la única de las tres candidatas con «ROCCÉ / so f★cking close.»
    # entero (en negra_frente_playa y _playa_2 un pliegue tapa «so»). El estampado mide 218×99 px en el original:
    # se amplía ×1,8 (recorte 600×375) para que se lea; no hay más detalle en la fuente.
    "L5_negra": ("negra_frente_arena_F266ACD9.png", (1090, 646, 600, 375), (1080, 675)),
}
# L4: las dos espaldas de estudio a 540 px de ancho, sobre el gris del piso medido arriba y abajo, fundido de 60 px.
L4 = {
    "blanca": dict(archivo="blanca_espalda_estudio.jpg", top=225),
    "negra": dict(archivo="negra_espalda_estudio.jpg", top=327),
    "fundido": 60,
}

# ---------- textos exactos (guion 05 + correcciones 06) ----------
TEXTOS = {
    "L1": ["Instagram te deja elegir equipo para la final.", "ROCCÉ", "¿Cuál ponés en tu foto de perfil?",
           "Ambos permanecen hasta que finaliza el evento.", "\"BLANCA\"", "\"NEGRA\"", "Elegir este equipo"],
    "L2": ["La Blanca: ROCCÉ en denim y cursiva celeste.", "PUESTA", "DE CERCA"],
    "L3": ["La Negra: ROCCÉ en denim, tono sobre tono.", "PUESTA", "DE CERCA"],
    "L4": ["¿Que te vean de lejos o que te descubran de cerca?", "\"BLANCA\"", "\"NEGRA\""],
    "L5": ["Adelante, las dos dicen lo mismo.", "\"BLANCA\"", "\"NEGRA\""],
    "L6": ["Ambos permanecen hasta que finaliza el evento.", "Ambas permanecen.",
           "La insignia se va cuando termina el evento. Lo que elegís ponerte, no.", "Etiquetá al que es de la otra."],
}

# ---------- línea de tiempo de L6 (cuadros a 30 fps) ----------
L6_TL = dict(tachar=(42, 57), desvanecer=(57, 66), letra=(66, 71), bajada=(72, 80), cta=(90, 98))

# Esquina de la numeración de Instagram (arriba a la derecha): debe quedar libre de texto y elementos.
ESQUINA_IG = (900, 0, 1080, 110)
