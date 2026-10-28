# Arma la entrega a partir de las ocho piezas finales:
#   ROCCE_PRELAUNCH_v02_MIXTO.zip           los ocho archivos del carrusel (5 MP4 + 3 PNG), en orden
#   previews/ROCCE_PRELAUNCH_v02_PREVIEW_vista_conjunta.jpg   un cuadro de cada lámina, marcado MP4/PNG (solo para revisar)
#   previews/ROCCE_PRELAUNCH_v02_PREVIEW_recorrido.mp4        las ocho seguidas (los PNG 2,5 s) — preview, no reemplaza los archivos
#   ROCCE_PRELAUNCH_v02_editable.zip        el proyecto (HTML/CSS, scripts, fuentes, fotos fijas, capas, ficha de fuentes)
# Uso: python3 entregar.py SALIDA_DIR VERSION
import os, sys, glob, zipfile, subprocess, io
from PIL import Image, ImageDraw, ImageFont
out, ver = sys.argv[1], sys.argv[2]; AQUI = os.path.dirname(os.path.abspath(__file__))
piezas = []
for n in range(1, 9):
    f = [p for p in (os.path.join(out, f"ROCCE_PRELAUNCH_{n:02d}_{ver}.{e}") for e in ("mp4", "png")) if os.path.exists(p)]
    assert len(f) == 1, f"falta la lámina {n:02d}"; piezas.append(f[0])
with zipfile.ZipFile(os.path.join(out, f"ROCCE_PRELAUNCH_{ver}_MIXTO.zip"), "w", zipfile.ZIP_STORED) as z:
    for p in piezas: z.write(p, os.path.basename(p))
pv = os.path.join(out, "previews"); os.makedirs(pv, exist_ok=True)
ft = ImageFont.truetype(os.path.join(AQUI, "fuentes", "InterDisplay-SemiBold.otf"), 22)
W, H, G = 360, 450, 16; hoja = Image.new("RGB", (4 * W + 5 * G, 2 * (H + 44) + 2 * G), (138, 143, 148)); d = ImageDraw.Draw(hoja)
for i, p in enumerate(piezas):
    if p.endswith(".mp4"):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "2.0", "-i", p, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
        im = Image.open(io.BytesIO(raw)).convert("RGB"); etq = f"{i + 1:02d} · MP4 (video dentro)"
    else: im = Image.open(p).convert("RGB"); etq = f"{i + 1:02d} · PNG (fija)"
    x, y = G + (i % 4) * (W + G), G + (i // 4) * (H + 44 + G)
    hoja.paste(im.resize((W, H), Image.LANCZOS), (x, y)); d.text((x, y + H + 10), etq, font=ft, fill="white")
hoja.save(os.path.join(pv, f"ROCCE_PRELAUNCH_{ver}_PREVIEW_vista_conjunta.jpg"), quality=90)
ins, fc = [], []
for i, p in enumerate(piezas):
    ins += (["-i", p] if p.endswith(".mp4") else ["-loop", "1", "-framerate", "30", "-t", "2.5", "-i", p])
    fc.append(f"[{i}:v]scale=1080:1350,setsar=1,fps=30,format=yuv420p[p{i}]")
fc.append("".join(f"[p{i}]" for i in range(len(piezas))) + f"concat=n={len(piezas)}:v=1:a=0[v]")
subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fc), "-map", "[v]", "-c:v", "libx264", "-crf", "22",
                "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an",
                os.path.join(pv, f"ROCCE_PRELAUNCH_{ver}_PREVIEW_recorrido.mp4")], check=True, stdin=subprocess.DEVNULL)
incluir = ["pagina.html", "estilos.css", "capas.js", "construir.py", "video.py", "proyecto.py", "verificar.py", "revisar_recortes.py",
           "ficha.py", "entregar.py", "FUENTES.md", "LEEME.md"]
with zipfile.ZipFile(os.path.join(out, f"ROCCE_PRELAUNCH_{ver}_editable.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for f in incluir + sorted(glob.glob("fuentes/*", root_dir=AQUI)) + sorted(glob.glob("recursos/*", root_dir=AQUI)) + sorted(glob.glob("capas/*", root_dir=AQUI)):
        z.write(os.path.join(AQUI, f), os.path.join(f"ROCCE_PRELAUNCH_{ver}_editable", f))
print("entrega lista en", out)
