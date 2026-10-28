# Recortes del carrusel de prelanzamiento, tomados de las fotos originales de PRODUCTO/ (fuente de verdad).
# Solo se recorta y se escala conservando la proporción; se convierte de Display P3 (iPhone) a sRGB para que el
# color de la prenda se vea igual en la web y en Instagram. Sin retoques, sin espejar, sin generar nada.
# Uso: python3 recortes.py   (desde esta carpeta; lee ../../PRODUCTO y ../../LOGO, escribe recursos/)
import io, os, json, shutil
from PIL import Image, ImageCms

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, "..", ".."))
OUT = os.path.join(AQUI, "recursos"); os.makedirs(OUT, exist_ok=True)
SRGB = ImageCms.createProfile("sRGB")
SRGB_BYTES = ImageCms.ImageCmsProfile(SRGB).tobytes()

# nombre: (foto original, caja x0, y0, x1, y1 en píxeles del original, ancho de salida en px, uso)
RECORTES = {
    "p01_franja":   ("blanca_negra_espalda_playa_2.jpg", (0, 905, 1932, 1385), 1080,
                     "Portada: franja de las dos espaldas (ROCCÉ en denim, Founders Privée celeste y gris)."),
    "p02_ambas":    ("blanca_negra_espalda_playa_2.jpg", (0, 395, 1932, 1985), 1080,
                     "Placa 02: las dos remeras de espaldas sobre la arena, completas (la manga izquierda de la blanca toca el borde en el original)."),
    "p03_principal": ("blanca_espalda_rocas_espuma.jpg", (395, 790, 1535, 1420), 936,
                     "Placa 03: ROCCÉ en denim con pespunte claro y Founders Privée celeste (blanca, espalda)."),
    "p03_e":        ("blanca_espalda_rocas_espuma.jpg", (1048, 812, 1268, 1032), 264,
                     "Placa 03: la É con su acento, en denim (detalle del mismo original)."),
    "p05_frase":    ("blanca_frente_detalle_estampado.jpg", (110, 1200, 1505, 1480), 936,
                     "Placa 05: so f★cking close. tal como está estampada en el pecho de la blanca (estrella celeste)."),
    "p06_negra":    ("ORIGINALES/IMG_7824.mov@6.8", (0, 960, 2160, 2560), 400,
                     "Placa 06: la negra sostenida de espaldas (ROCCÉ en denim negro, Founders Privée gris), fotograma de 6,8 s del video real IMG_7824."),
    "p07_puesta":   ("blanca_puesta_espalda_balcon_playa.jpg", (0, 0, 1932, 2415), 1080,
                     "Placa 07: la blanca puesta, de espaldas, frente a la playa (sin cara visible)."),
}

def abrir(foto):
    if "@" in foto:                                    # fotograma de un video real: ORIGINALES/X.mov@segundos
        ruta, t = foto.split("@"); import subprocess
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", t, "-i", os.path.join(RAIZ, ruta), "-frames:v", "1", "-f", "image2pipe",
                              "-vcodec", "png", "-"], capture_output=True, check=True).stdout
        return Image.open(io.BytesIO(raw)).convert("RGB"), ruta + " (fotograma " + t + " s)"
    return Image.open(os.path.join(RAIZ, "PRODUCTO", foto)), "PRODUCTO/" + foto

def a_srgb(im):
    p = im.info.get("icc_profile")
    if p:
        im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(p)), SRGB,
                                       renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC, outputMode="RGB")
    return im.convert("RGB")

registro = {}
for nombre, (foto, caja, ancho, uso) in RECORTES.items():
    im, origen = abrir(foto)
    im = a_srgb(im).crop(caja)
    w, h = im.size; alto = round(ancho * h / w)
    escala = ancho / w
    if escala != 1: im = im.resize((ancho, alto), Image.LANCZOS)
    dst = os.path.join(OUT, nombre + ".jpg")
    im.save(dst, quality=95, subsampling=0, icc_profile=SRGB_BYTES)
    registro[nombre] = dict(original=origen, caja=caja, salida=[ancho, alto], escala=round(escala, 3), uso=uso)
    print(f"{nombre}: {foto} {caja} → {ancho}×{alto} (escala {escala:.2f})")
shutil.copyfile(os.path.join(RAIZ, "LOGO", "rocce_logo.png"), os.path.join(OUT, "rocce_logo.png"))   # logo original, sin cambios
registro["rocce_logo"] = dict(original="LOGO/rocce_logo.png", uso="Placa 08: logo original (copia exacta, fondo #FEFEFE).")
json.dump(registro, open(os.path.join(OUT, "recortes.json"), "w"), indent=1, ensure_ascii=False)
