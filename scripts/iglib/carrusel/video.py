# IGLIB-3 · lectura de tomas reales cuadro a cuadro (como se ven en el teléfono, ya rotadas).
# - HDR (HLG/BT.2020) → SDR BT.709 con la cadena mobius probada (CLAUDE.md) + corrección de blanco opcional.
# - SDR BT.709 rango TV → RGB.
# - Las tomas 4K se bajan a 1080×1920 (las ventanas más grandes son de 540 px de ancho, salvo L6, que ya es 1080).
# - Las de 29,97 fps se llevan a 30 con fps=30 (cuadro más cercano, sin mezclar).
# Devuelve cuadros RGB uint8 (numpy) a 30 fps, empezando en `desde` (s) y con `n` cuadros.
import os, json, subprocess
import numpy as np

RAIZ = "/home/user/1"
ORIG = os.path.join(RAIZ, "ORIGINALES")
TM = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
      "zscale=t=bt709:m=bt709:r=tv,format=yuv444p")
FPS = 30

def info(toma):
    r = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=width,height,r_frame_rate,color_transfer,duration:stream_side_data=rotation", "-of", "json",
        os.path.join(ORIG, toma + ".mov")]))["streams"][0]
    # las HDR de iPhone traen antes un bloque Dolby Vision: buscar la entrada que tiene la rotación
    rot = abs(int(next((s["rotation"] for s in r.get("side_data_list", []) if "rotation" in s), 0)))
    w, h = (r["height"], r["width"]) if rot in (90, 270) else (r["width"], r["height"])
    return dict(w=w, h=h, rot=rot, hdr=r.get("color_transfer") in ("arib-std-b67", "smpte2084"),
                fps=r["r_frame_rate"], dur=float(r["duration"]))

def filtro(toma, corr=None):
    i = info(toma)
    f = []
    if i["hdr"]:
        f.append(TM)
        if corr: f.append(corr)
    elif corr:
        f.append(corr)
    if i["w"] > 1080:
        f.append("scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int")
    f.append(f"fps={FPS}")
    f.append("scale=in_range=tv:in_color_matrix=bt709:flags=lanczos+accurate_rnd+full_chroma_int,format=rgb24")
    return ",".join(f), i

def cuadros(toma, desde, n, corr=None):
    """Generador de n cuadros RGB (H×W×3) desde `desde` segundos (búsqueda exacta, autorrotación de ffmpeg)."""
    vf, i = filtro(toma, corr)
    W, H = (1080, 1920) if i["w"] > 1080 else (i["w"], i["h"])
    assert desde + n / FPS <= i["dur"] + 0.02, f"{toma}: {desde}+{n / FPS:.2f} s pasa el final ({i['dur']:.2f} s)"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{desde:.4f}", "-i", os.path.join(ORIG, toma + ".mov"),
                          "-an", "-vf", vf, "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE, stdin=subprocess.DEVNULL)
    tam = W * H * 3; k = 0
    while k < n:
        b = p.stdout.read(tam)
        if len(b) < tam: break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3); k += 1
    p.stdout.close(); p.wait()
    assert k == n, f"{toma}: se leyeron {k} de {n} cuadros"
