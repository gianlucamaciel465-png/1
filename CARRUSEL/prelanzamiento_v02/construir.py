# Construye el carrusel mixto v02 desde los originales:
#   1. fotos fijas (recortes de PRODUCTO/ o fotogramas de tomas reales), Display P3 → sRGB
#   2. primer cuadro de cada ventana (póster) para la maqueta
#   3. capas fijas con Chromium (node capas.js): base, capa superior y posición de las ventanas
#   4. cada ventana: sus clips reales recortados a la proporción del recuadro, a 30 fps, uno detrás del otro
#   5. MP4 = base fija + ventanas con video + capa superior (H.264, yuv420p, 1080×1350, 30 fps, sin audio)
#      PNG = base fija con perfil sRGB
# Uso: python3 construir.py SALIDA_DIR VERSION [PAGINAS…]   (p. ej.: python3 construir.py ../../EXPORTACIONES/x v02 01)
import io, os, sys, json, subprocess
from PIL import Image, ImageCms
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proyecto import FPS, TM, CORR, COLOR, FIJAS, PAGINAS, ORIG
from video import tam, cadena

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.normpath(os.path.join(AQUI, "..", ".."))
REC, CAP = os.path.join(AQUI, "recursos"), os.path.join(AQUI, "capas")
SRGB = ImageCms.createProfile("sRGB"); SRGB_B = ImageCms.ImageCmsProfile(SRGB).tobytes()
out, ver = sys.argv[1], sys.argv[2]; solo = sys.argv[3:] or list(PAGINAS)
os.makedirs(out, exist_ok=True); os.makedirs(REC, exist_ok=True); os.makedirs(CAP, exist_ok=True)
TMP = os.path.join(RAIZ, "TRABAJO", "carrusel2", "ventanas"); os.makedirs(TMP, exist_ok=True)
run = lambda c: subprocess.run(c, check=True, stdin=subprocess.DEVNULL)

def fotograma(ruta_t):
    ruta, t = ruta_t.split("@")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", t, "-i", os.path.join(RAIZ, ruta), "-frames:v", "1", "-f", "image2pipe",
                          "-vcodec", "png", "-"], capture_output=True, check=True, stdin=subprocess.DEVNULL).stdout
    return Image.open(io.BytesIO(raw)).convert("RGB")

def a_srgb(im):
    p = im.info.get("icc_profile")
    if p: im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(p)), SRGB, outputMode="RGB",
                                         renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC)
    return im.convert("RGB")

# 1. fotos fijas
for nombre, (orig, (x, y, w, h), (W, H), _) in FIJAS.items():
    im = fotograma(orig) if "@" in orig else a_srgb(Image.open(os.path.join(RAIZ, orig)))
    im.crop((x, y, x + w, y + h)).resize((W, H), Image.LANCZOS).save(os.path.join(REC, nombre + ".jpg"), quality=95, subsampling=0, icc_profile=SRGB_B)
import shutil; shutil.copyfile(os.path.join(RAIZ, "LOGO", "rocce_logo.png"), os.path.join(REC, "rocce_logo.png"))
print("fotos fijas:", len(FIJAS))

def capas():
    run(["node", os.path.join(AQUI, "capas.js")])
    return json.load(open(os.path.join(CAP, "ventanas.json")))

# 2–3. capas (primera pasada para conocer las ventanas), pósters y capas definitivas
vent = capas()
for n, pag in PAGINAS.items():
    for v in vent.get(n, []):
        toma, a, b, centro, ancho = pag["ventanas"][v["id"]][0]
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", os.path.join(RAIZ, ORIG, toma + ".mov"), "-frames:v", "1",
             "-vf", cadena(toma, centro, ancho, v["w"], v["h"]).replace("format=yuv444p", "format=rgb24") , os.path.join(CAP, f"poster_{v['id']}.jpg")])
vent = capas()

# 4–5. láminas
ficha = {}
for n in solo:
    pag = PAGINAS[n]; base = os.path.join(CAP, f"base_{n}.png"); final = os.path.join(out, f"ROCCE_PRELAUNCH_{n}_{ver}")
    if pag["tipo"] == "png":
        Image.open(base).convert("RGB").save(final + ".png", icc_profile=SRGB_B, optimize=True); print(final + ".png"); continue
    N = int(round(pag["dur"] * FPS)); ins = ["-loop", "1", "-framerate", str(FPS), "-t", f"{pag['dur']:.3f}", "-i", base]
    fc = [f"[0:v]scale=out_color_matrix=bt709:out_range=tv,format=yuv444p,setsar=1[l0]"]; k = 1; ult = "l0"
    for j, v in enumerate(vent[n]):
        clips = pag["ventanas"][v["id"]]; frames = [int(round((b - a) * FPS)) for _, a, b, _, _ in clips]
        frames[-1] += N - sum(frames)                                            # la ventana dura exactamente la lámina
        assert frames[-1] > 0, f"{n}/{v['id']}: los clips no alcanzan"
        segs = []
        for (toma, a, b, centro, ancho), nf in zip(clips, frames):
            dur_disp = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                                      os.path.join(RAIZ, ORIG, toma + ".mov")]).decode())
            assert a + nf / FPS <= dur_disp + 0.02, f"{toma}: {a}+{nf / FPS:.2f} s pasa el final ({dur_disp:.2f} s)"
            ins += ["-ss", f"{a:.3f}", "-i", os.path.join(RAIZ, ORIG, toma + ".mov")]
            fc.append(f"[{k}:v]{cadena(toma, centro, ancho, v['w'], v['h'])},trim=end_frame={nf},setpts=PTS-STARTPTS[s{k}]"); segs.append(f"[s{k}]"); k += 1
            ficha.setdefault(n, []).append(dict(ventana=v["id"], toma=f"{ORIG}/{toma}.mov", desde=a, hasta=round(a + nf / FPS, 3), cuadros=nf))
        fc.append(f"{''.join(segs)}concat=n={len(segs)}:v=1:a=0,setpts=N/{FPS}/TB[w{j}]")
        fc.append(f"[{ult}][w{j}]overlay=x={v['x']}:y={v['y']}:format=yuv444:eof_action=repeat[l{j + 1}]"); ult = f"l{j + 1}"
    ins += ["-loop", "1", "-framerate", str(FPS), "-t", f"{pag['dur']:.3f}", "-i", os.path.join(CAP, f"arriba_{n}.png")]
    fc.append(f"[{k}:v]scale=out_color_matrix=bt709:out_range=tv,format=yuva444p[top]")
    fc.append(f"[{ult}][top]overlay=format=yuv444,format=yuv420p[v]")
    run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fc), "-map", "[v]", "-frames:v", str(N), "-r", str(FPS),
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
         "-an", "-map_metadata", "-1", "-movflags", "+faststart", final + ".mp4"])
    print(final + ".mp4", f"{os.path.getsize(final + '.mp4') / 1e6:.1f} MB")
json.dump(ficha, open(os.path.join(CAP, "clips_usados.json"), "w"), indent=1, ensure_ascii=False)
