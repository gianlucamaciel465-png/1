# Cierra la exportación del carrusel: incrusta el perfil sRGB en cada PNG, controla tamaño y orden,
# arma la vista conjunta (las 8 en orden) y los ZIP (PNG finales y proyecto editable).
# Uso: python3 finalizar.py SALIDA_DIR VERSION   (después de node render.js SALIDA_DIR VERSION)
import sys, os, zipfile, glob
from PIL import Image, ImageCms, ImageDraw, ImageFont

out, ver = sys.argv[1], sys.argv[2]
AQUI = os.path.dirname(os.path.abspath(__file__))
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
pngs = [os.path.join(out, f"ROCCE_PRELAUNCH_{i:02d}_{ver}.png") for i in range(1, 9)]
for p in pngs:
    im = Image.open(p).convert("RGB")
    assert im.size == (1080, 1350), f"{p}: {im.size}"
    im.save(p, icc_profile=SRGB, optimize=True)
    print(f"{os.path.basename(p)}: 1080×1350, sRGB, {os.path.getsize(p) // 1024} KB")

# vista conjunta: 4 × 2, en orden, con número debajo de cada placa
W, H, G, T = 432, 540, 24, 40
hoja = Image.new("RGB", (4 * W + 5 * G, 2 * (H + T) + 3 * G), (138, 143, 148))
ft = ImageFont.truetype(os.path.join(AQUI, "fuentes", "InterDisplay-SemiBold.otf"), 24)
d = ImageDraw.Draw(hoja)
for i, p in enumerate(pngs):
    x = G + (i % 4) * (W + G); y = G + (i // 4) * (H + T + G)
    hoja.paste(Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS), (x, y))
    d.text((x, y + H + 8), f"{i + 1:02d}", font=ft, fill=(255, 255, 255))
vista = os.path.join(out, f"ROCCE_PRELAUNCH_vista_conjunta_{ver}.jpg")
hoja.save(vista, quality=92, icc_profile=SRGB); print(vista)

with zipfile.ZipFile(os.path.join(out, f"ROCCE_PRELAUNCH_{ver}_PNG.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for p in pngs: z.write(p, os.path.basename(p))
with zipfile.ZipFile(os.path.join(out, f"ROCCE_PRELAUNCH_{ver}_editable.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for f in ["index.html", "estilos.css", "render.js", "recortes.py", "finalizar.py", "LEEME.md"] + \
             sorted(glob.glob("fuentes/*", root_dir=AQUI)) + sorted(glob.glob("recursos/*", root_dir=AQUI)):
        z.write(os.path.join(AQUI, f), os.path.join(f"ROCCE_PRELAUNCH_{ver}_editable", f))
print("ZIP listos en", out)
