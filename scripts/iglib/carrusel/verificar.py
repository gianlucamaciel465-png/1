# IGLIB-3 v01 · control de las láminas exportadas (los archivos finales, no el editor) y paquete de entrega.
#   - ffprobe resumido, decodificación completa (ffmpeg -v error … -f null -), md5 del flujo de video, sha256
#   - movimiento: cambio entre cuadros DENTRO de cada ventana (debe haber) y FUERA (debe quedar quieto: solo ruido
#     de compresión); también debajo de la capa de texto opaca (alfa ≥ 0,99) que cae sobre una ventana
#   - blanco neutro medido en el archivo final (B−R en tela de la Blanca)
#   - evidencia: cuadros a resolución completa, vistas a 360 px, hoja de cajas de medición
#   - vista conjunta (6 láminas) y ZIP
# Uso: python3 verificar.py
import os, sys, io, json, hashlib, zipfile, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
from proyecto import *

CAP = os.path.join(TRAB, "capas"); os.makedirs(EVID, exist_ok=True)
vent = json.load(open(os.path.join(CAP, "ventanas.json")))
FONT = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 22)
arch = lambda nl: os.path.join(SALIDA, f"IGLIB-3_{nl}_{VER}." + ("png" if LAMINAS[nl]["tipo"] == "png" else "mp4"))

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def cuadros_rgb(f, w=W, h=H):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)

# cajas de tela blanca sin estampado (coordenadas de la lámina), para medir B−R en el archivo final
TELA_BLANCA = {
    "L1": [("círculo IMG_7857 (cuadro 36)", (250, 850, 330, 880), 36)],
    "L2": [("PUESTA foto balcón", (150, 900, 400, 1040), 31), ("DE CERCA IMG_4530 (cuadro 31)", (640, 960, 1000, 1150), 31)],
    "L4": [("Blanca estudio", (150, 1010, 380, 1060), 0)],
    "L5": [("Blanca detalle", (20, 540, 120, 620), 0)],
    "L6": [("remera blanca IMG_4631 (cuadro 0)", (220, 950, 420, 1060), 0), ("remera blanca IMG_4631 (cuadro 110)", (220, 950, 420, 1060), 110)],
}
REPRESENTATIVO = {"L1": 36, "L2": 31, "L3": 22, "L6": 110}
EVID_L6 = [0, 41, 44, 48, 52, 57, 60, 63, 66, 67, 68, 69, 70, 71, 76, 80, 94, 98, 131]

res = {}
for nl, pag in LAMINAS.items():
    f = arch(nl); r = res.setdefault(nl, {}); r["archivo"] = f; r["bytes"] = os.path.getsize(f); r["sha256"] = sha256(f)
    if pag["tipo"] == "png":
        im = Image.open(f); r.update(tam=list(im.size), modo=im.mode, icc=bool(im.info.get("icc_profile")),
                                     icc_desc=__import__("PIL.ImageCms", fromlist=["x"]).getProfileDescription(
                                         __import__("PIL.ImageCms", fromlist=["x"]).ImageCmsProfile(io.BytesIO(im.info["icc_profile"]))).strip())
        fr = np.array(im.convert("RGB"))[None]
    else:
        pr = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
             "stream=index,codec_type,codec_name,profile,level,width,height,pix_fmt,r_frame_rate,avg_frame_rate,nb_frames,duration,color_range,color_space,color_transfer,color_primaries,bit_rate"
             ":format=duration,size,bit_rate,format_name:format_tags:stream_tags", "-of", "json", f]))
        r["ffprobe"] = pr
        r["errores_decodificacion"] = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "null", "-"], capture_output=True, text=True).stderr.strip() or "ninguno"
        r["md5_flujo_video"] = subprocess.check_output(["ffmpeg", "-v", "error", "-i", f, "-map", "0:v:0", "-c", "copy", "-f", "md5", "-"]).decode().strip()
        r["faststart_moov_antes_de_mdat"] = (lambda b: b.find(b"moov") < b.find(b"mdat"))(open(f, "rb").read(4096 * 64))
        fr = cuadros_rgb(f); r["cuadros_decodificados"] = int(fr.shape[0])
        g = fr.astype(np.float32).mean(axis=3); d = np.abs(np.diff(g, axis=0))
        dentro = np.zeros((H, W), bool); borde = np.zeros((H, W), bool)
        for v in vent[nl]:
            dentro[v["y"]:v["y"] + v["h"], v["x"]:v["x"] + v["w"]] = True
            borde[max(0, v["y"] - 8):v["y"] + v["h"] + 8, max(0, v["x"] - 8):v["x"] + v["w"] + 8] = True
        fuera = ~borde
        mov = {}
        for v in vent[nl]:
            z = d[:, v["y"]:v["y"] + v["h"], v["x"]:v["x"] + v["w"]].mean(axis=(1, 2))
            mov[v["id"]] = dict(cambio_medio=round(float(z.mean()), 2), cambio_min=round(float(z.min()), 2),
                                cuadros_con_movimiento=int((z > 0.3).sum()), de=int(len(z)))
        r["movimiento_dentro"] = mov
        if fuera.any():
            r["fuera"] = dict(px=int(fuera.sum()), cambio_medio=round(float(d[:, fuera].mean()), 4), cambio_max=float(d[:, fuera].max()),
                              px_cuadro_con_cambio_mayor_a_4=int((d[:, fuera] > 4).sum()))
        else:
            r["fuera"] = "la ventana ocupa toda la lámina"
        if not pag.get("animada"):
            a = np.array(Image.open(os.path.join(CAP, f"arriba_{nl}.png")))[..., 3] >= 252
            op = a & dentro
            if op.any():
                r["texto_opaco_sobre_video"] = dict(px=int(op.sum()), cambio_medio=round(float(d[:, op].mean()), 4), cambio_max=float(d[:, op].max()))
    # blanco neutro
    for nombre, (x0, y0, x1, y1), k in TELA_BLANCA.get(nl, []):
        z = fr[k, y0:y1, x0:x1].reshape(-1, 3).astype(float); m = np.median(z, axis=0)
        r.setdefault("blanco_neutro", []).append(dict(zona=nombre, caja=[x0, y0, x1, y1], cuadro=k, rgb_mediana=[round(c, 1) for c in m], B_menos_R=round(m[2] - m[0], 1)))
    # evidencia
    if pag["tipo"] == "png":
        shutil.copyfile(f, os.path.join(EVID, f"IGLIB-3_{nl}_completa.png"))
        rep = fr[0]
    else:
        n = fr.shape[0]; ks = sorted(set([0, n // 2, n - 1] + (EVID_L6 if nl == "L6" else [])))
        for k in ks: Image.fromarray(fr[k]).save(os.path.join(EVID, f"IGLIB-3_{nl}_c{k:03d}_{k / FPS:.2f}s.png"))
        rep = fr[REPRESENTATIVO[nl]]; r["cuadros_evidencia"] = ks
    r["cuadro_representativo"] = REPRESENTATIVO.get(nl, 0)
    Image.fromarray(rep).save(os.path.join(TRAB, f"rep_{nl}.png"))
    Image.fromarray(rep).resize((360, 450), Image.LANCZOS).save(os.path.join(EVID, f"IGLIB-3_{nl}_vista_360px.png"))
    # cajas de medición dibujadas (para comprobar que miden tela y no estampado)
    if nl in TELA_BLANCA:
        im = Image.fromarray(fr[TELA_BLANCA[nl][0][2]]).copy(); dr = ImageDraw.Draw(im)
        for nombre, c, k in TELA_BLANCA[nl]: dr.rectangle(c, outline=(255, 0, 255), width=4)
        im.resize((540, 675)).save(os.path.join(TRAB, f"cajas_blanco_{nl}.jpg"), quality=88)
    print(nl, "ok")

# vista conjunta: 3 × 2, cada lámina a 540 × 675 con su número debajo (fuera de la lámina)
G = 24; tw, th = 540, 675
vc = Image.new("RGB", (3 * tw + 4 * G, 2 * (th + 44) + G), (18, 18, 18)); dr = ImageDraw.Draw(vc)
for i, nl in enumerate(LAMINAS):
    x = G + (i % 3) * (tw + G); y = G + (i // 3) * (th + 44)
    vc.paste(Image.open(os.path.join(TRAB, f"rep_{nl}.png")).resize((tw, th), Image.LANCZOS), (x, y))
    t = f"{nl} · " + ("PNG" if LAMINAS[nl]["tipo"] == "png" else f"MP4 {LAMINAS[nl]['cuadros'] / FPS:.1f} s · cuadro {REPRESENTATIVO[nl]}")
    dr.text((x, y + th + 8), t, fill=(220, 220, 220), font=FONT)
vista = os.path.join(SALIDA, f"IGLIB-3_vista_conjunta_{VER}.jpg"); vc.save(vista, quality=92)
res["vista_conjunta"] = dict(archivo=vista, sha256=sha256(vista), tam=list(vc.size))

# ZIP con las 6 láminas y la vista conjunta (sin comprimir los MP4/PNG: ya están comprimidos)
zp = os.path.join(SALIDA, f"IGLIB-3_{VER}.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
    for nl in LAMINAS: z.write(arch(nl), os.path.basename(arch(nl)))
    z.write(vista, os.path.basename(vista))
with zipfile.ZipFile(zp) as z: assert z.testzip() is None; res["zip"] = dict(archivo=zp, sha256=sha256(zp), contenido=z.namelist(), bytes=os.path.getsize(zp))
json.dump(res, open(os.path.join(TRAB, "control_v01.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("ffprobe",)} for k, v in res.items()}, ensure_ascii=False, indent=1))
