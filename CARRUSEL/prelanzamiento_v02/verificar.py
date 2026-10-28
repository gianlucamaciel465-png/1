# Control de las láminas MP4 exportadas (no del editor): decodifica el archivo final y mide, cuadro a cuadro,
# cuánto cambia la imagen DENTRO de cada ventana (debe haber movimiento real del clip) y FUERA (debe quedar quieto:
# solo ruido de compresión). Además arma una hoja con varios instantes de la misma lámina y un mapa de movimiento.
# Uso: python3 verificar.py ARCHIVO.mp4 NN SALIDA_DIR
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw

f, n, outd = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(outd, exist_ok=True)
AQUI = os.path.dirname(os.path.abspath(__file__))
vent = json.load(open(os.path.join(AQUI, "capas", "ventanas.json")))[n]
info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,nb_frames,duration,color_primaries,color_transfer,color_space:format=duration,size",
                                          "-of", "json", f]))
s = info["streams"][0]; W, H = s["width"], s["height"]
err = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "null", "-"], capture_output=True, text=True).stderr.strip()
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.int16)
d = np.abs(np.diff(fr, axis=0))                                   # cambio entre cuadros consecutivos
mask = np.zeros((H, W), bool)
for v in vent: mask[v["y"]:v["y"] + v["h"], v["x"]:v["x"] + v["w"]] = True
borde = np.zeros((H, W), bool)                                     # 8 px alrededor de cada ventana (no cuentan como "fuera")
for v in vent: borde[max(0, v["y"] - 8):v["y"] + v["h"] + 8, max(0, v["x"] - 8):v["x"] + v["w"] + 8] = True
fuera = ~borde
res = dict(archivo=os.path.basename(f), errores_decodificacion=err or "ninguno", codec=s["codec_name"], perfil=s.get("profile"),
           tam=f"{W}x{H}", pix_fmt=s["pix_fmt"], fps=s["r_frame_rate"], cuadros=int(fr.shape[0]), duracion=float(info["format"]["duration"]),
           mb=round(int(info["format"]["size"]) / 1e6, 2), color=[s.get("color_primaries"), s.get("color_transfer"), s.get("color_space")],
           fuera_cambio_medio=round(float(d[:, fuera].mean()), 3), fuera_cambio_max_px=int(d[:, fuera].max()),
           fuera_px_que_cambian_mas_de_8=int((d[:, fuera] > 8).sum()))
for v in vent:
    z = d[:, v["y"]:v["y"] + v["h"], v["x"]:v["x"] + v["w"]].mean(axis=(1, 2))
    res[v["id"]] = dict(cambio_medio=round(float(z.mean()), 2), cuadros_con_movimiento=int((z > 0.5).sum()), de=len(z),
                        cortes=[int(i + 1) for i in np.where(z > 25)[0]])
    # primer cuadro: la ventana ya muestra la toma (no negro ni vacío)
    res[v["id"]]["primer_cuadro_brillo"] = round(float(fr[0, v["y"]:v["y"] + v["h"], v["x"]:v["x"] + v["w"]].mean()), 1)
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open(os.path.join(outd, f"control_{n}.json"), "w"), ensure_ascii=False, indent=1)
# hoja: 5 instantes de la misma lámina + mapa de movimiento (blanco = cambió)
ts = np.linspace(0, fr.shape[0] - 1, 5).astype(int)
tw = 216; th = int(H * tw / W)
hoja = Image.new("RGB", (6 * tw + 7 * 8, th + 40), (138, 143, 148)); dr = ImageDraw.Draw(hoja)
for i, t in enumerate(ts):
    im = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vf", f"select=eq(n\\,{t})", "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                        capture_output=True).stdout
    import io
    hoja.paste(Image.open(io.BytesIO(im)).convert("RGB").resize((tw, th)), (8 + i * (tw + 8), 8)); dr.text((8 + i * (tw + 8), th + 14), f"cuadro {t} ({t / 30:.1f} s)", fill="white")
mov = (d.max(axis=0) > 8).astype(np.uint8) * 255
hoja.paste(Image.fromarray(mov).convert("RGB").resize((tw, th)), (8 + 5 * (tw + 8), 8)); dr.text((8 + 5 * (tw + 8), th + 14), "mapa de movimiento", fill="white")
hoja.save(os.path.join(outd, f"instantes_{n}.jpg"), quality=90)
