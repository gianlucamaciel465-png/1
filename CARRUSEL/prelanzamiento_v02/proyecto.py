# Carrusel de prelanzamiento v02 (mixto): fuente única de verdad del proyecto.
# Define las fotos fijas (recortes de originales) y los clips reales que se reproducen dentro de cada ventana.
# Lo usan recortes.py (fotos y pósters), componer.py (MP4/PNG) y ficha.py (FUENTES.md).
#
# Coordenadas: píxeles del cuadro ya rotado como se ve en el teléfono (los videos de iPhone vienen girados -90°).
# Videos: "centro" (cx, cy) y "ancho" del recorte dentro de la toma; el alto sale de la proporción de la ventana.
# Color: "sdr_tv" / "sdr_pc" (rango del archivo) o "hdr" (HLG → SDR BT.709 con tonemap mobius) + corrección opcional.

FPS = 30
ORIG = "ORIGINALES"
PROD = "PRODUCTO"
TM = "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"

# Correcciones medidas en encargos anteriores (ver CAMPANA_ACTUAL.md)
CORR = {
    "IMG_4530": "colorchannelmixer=rr=1.05:gg=1.03:bb=0.92",                              # HDR: blanco neutro
    "IMG_4531": "colorchannelmixer=rr=1.05:gg=1.03:bb=0.92",
    "IMG_3453": "colorchannelmixer=rr=0.84:gg=0.98:bb=1.16,eq=gamma=0.66:saturation=0.5",  # negra carbón bajo luz cálida
    "IMG_3375": "colorchannelmixer=rr=0.88:gg=1.0:bb=1.12",                               # blanca neutra
}
COLOR = {  # rango/transferencia de cada toma (ffprobe)
    "IMG_4530": "hdr", "IMG_4531": "hdr", "IMG_3453": "hdr", "IMG_3375": "hdr",
    "IMG_7824": "sdr_tv", "IMG_7857": "sdr_tv", "IMG_7793": "sdr_tv",
    "IMG_7859": "sdr_pc", "IMG_8004": "sdr_pc", "IMG_8008": "sdr_pc", "IMG_8002": "sdr_pc",
}

# ---------- fotos fijas: nombre → (origen, caja x, y, w, h en px del original, salida w×h) ----------
# origen: "PRODUCTO/x.jpg" o "ORIGINALES/X.mov@segundo" (un fotograma de una toma real, como foto fija)
FIJAS = {
    "f01_fondo_mar":    ("ORIGINALES/IMG_7857.mov@0.05", (0, 450, 2160, 2700), (1080, 1350),
                         "Fondo de la portada: mar, rocas y cielo (costa de Mar del Plata según el GPS de la toma, 11/10/2026)."),
    "f01_denim":        ("PRODUCTO/blanca_espalda_rocas_espuma.jpg", (395, 760, 1140, 950), (360, 300),
                         "Portada: espalda de la blanca de cerca (ROCCÉ en denim, Founders Privée celeste)."),
    "f02_ambas":        ("PRODUCTO/blanca_negra_espalda_playa_2.jpg", (0, 650, 1932, 1096), (372, 211),
                         "Placa 02: las dos remeras de espaldas sobre la arena."),
    "f03_denim":        ("PRODUCTO/blanca_espalda_rocas_espuma.jpg", (520, 860, 400, 400), (276, 276),
                         "Placa 03: letras de denim con pespunte claro (R y O de ROCCÉ)."),
    "f03_celeste":      ("PRODUCTO/blanca_espalda_rocas_espuma.jpg", (1080, 1040, 400, 400), (276, 276),
                         "Placa 03: Founders Privée en celeste, con relieve."),
    "f03_e":            ("PRODUCTO/blanca_espalda_rocas_espuma.jpg", (1048, 812, 220, 220), (276, 276),
                         "Placa 03: la É con su acento, en denim."),
    "f04_ciudad":       ("ORIGINALES/IMG_7793.mov@0.2", (0, 1100, 2160, 1292), (936, 560),
                         "Placa 04: Mar del Plata desde el balcón: edificios, playa y rambla (Mar del Plata según el GPS de la toma, 11/10/2026)."),
    "f04_mar":          ("ORIGINALES/IMG_7857.mov@0.05", (0, 1480, 2160, 1213), (456, 256),
                         "Placa 04: mar y rocas (Mar del Plata, 11/10/2026)."),
    "f04_medano":       ("ORIGINALES/IMG_8002.mov@0.0", (0, 1150, 2160, 1213), (456, 256),
                         "Placa 04: médano, troncos y cielo azul, con la blanca colgada (costa sur de Mar del Plata según el GPS de la toma, 12/10/2026)."),
    "f05_frase":        ("PRODUCTO/blanca_frente_detalle_estampado.jpg", (110, 1200, 1395, 280), (936, 188),
                         "Placa 05: so f★cking close., tal como está estampada en el pecho de la blanca."),
    "f06_negra":        ("ORIGINALES/IMG_7824.mov@6.8", (0, 960, 2160, 1600), (400, 296),
                         "Placa 06: la negra sostenida de espaldas (ROCCÉ en denim negro, Founders Privée gris)."),
    "f07_fondo":        ("PRODUCTO/blanca_puesta_espalda_balcon_playa.jpg", (0, 0, 1932, 2415), (1080, 1350),
                         "Fondo de la placa 07: la blanca puesta frente a la playa y la ciudad (mismo balcón que IMG_7793/IMG_7824)."),
    "f08_franja":       ("ORIGINALES/IMG_7857.mov@0.05", (0, 1700, 2160, 360), (1080, 180),
                         "Placa 08: franja de mar (Mar del Plata)."),
}

# ---------- páginas ----------
# tipo "mp4": ventanas con clips; "png": lámina fija. Cada clip: (toma, desde, hasta, (cx, cy), ancho)
PAGINAS = {
    "01": dict(tipo="mp4", dur=8.0, ventanas={
        "v01": [("IMG_4530", 0.45, 3.15, (540, 1060), 1080),      # blanca sostenida de espaldas, balcón
                ("IMG_7824", 3.30, 8.60, (1080, 2100), 2160)]}),   # negra sostenida que se acerca
    "02": dict(tipo="mp4", dur=8.0, ventanas={
        "v02a": [("IMG_4530", 0.45, 3.15, (540, 1060), 1080),     # blanca: espalda
                 ("IMG_4531", 3.60, 6.90, (540, 1150), 1080),     # blanca: frente
                 ("IMG_7857", 1.00, 3.00, (1080, 1950), 2160)],   # blanca: puesta
        "v02b": [("IMG_7824", 3.00, 9.00, (1080, 2100), 2160),    # negra: sostenida
                 ("IMG_7793", 2.40, 4.40, (1080, 1750), 2160)]}), # negra: puesta
    "03": dict(tipo="mp4", dur=7.0, ventanas={
        "v03": [("IMG_8004", 1.60, 4.50, (1080, 2450), 2160),     # recorrido lateral: denim y celeste
                ("IMG_8008", 0.00, 1.60, (1080, 1600), 2160),     # la blanca cae sobre la arena mojada
                ("IMG_7824", 4.80, 7.00, (1080, 1920), 2160)]}),  # la negra se acerca: tono sobre tono
    "04": dict(tipo="png"),
    "05": dict(tipo="mp4", dur=6.7, ventanas={
        "v05": [("IMG_3453", 0.20, 4.60, (540, 1100), 1080),      # dedos sobre la frase de la negra
                ("IMG_3375", 0.00, 2.30, (540, 900), 1080)]}),    # la frase de la blanca, sostenida
    "06": dict(tipo="png"),
    "07": dict(tipo="mp4", dur=9.0, ventanas={
        "v07": [("IMG_7857", 1.10, 5.10, (1080, 1950), 2160),     # blanca puesta, frente al mar
                ("IMG_7859", 2.00, 4.50, (1920, 1080), 1728),     # blanca puesta, mar picado (toma horizontal)
                ("IMG_7793", 2.35, 4.85, (1080, 1750), 2160)]}),  # negra puesta, balcón
    "08": dict(tipo="png"),
}
FUNCION = {"IMG_4530": "video principal", "IMG_4531": "video principal", "IMG_7824": "video principal / detalle",
           "IMG_7857": "video de ropa puesta", "IMG_7859": "video de ropa puesta", "IMG_7793": "video de ropa puesta",
           "IMG_8004": "video de detalle", "IMG_8008": "video de detalle", "IMG_3453": "video de detalle (frase)",
           "IMG_3375": "video de detalle (frase)"}
