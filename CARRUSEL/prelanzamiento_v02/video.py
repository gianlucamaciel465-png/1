# Funciones de video compartidas: tamaño real (rotado) de una toma y cadena de filtros de un clip dentro de una ventana.
import os, json, subprocess
from proyecto import FPS, TM, CORR, COLOR, ORIG
RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

def tam(toma):
    """Tamaño del cuadro ya rotado (como se ve)."""
    r = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=width,height:stream_side_data=rotation", "-of", "json", os.path.join(RAIZ, ORIG, toma + ".mov")]))["streams"][0]
    w, h = r["width"], r["height"]; rot = abs(int(next((s["rotation"] for s in r.get("side_data_list", []) if "rotation" in s), 0)))   # las HDR traen antes un bloque Dolby Vision
    return (h, w) if rot in (90, 270) else (w, h)

def cadena(toma, centro, ancho, W, H):
    """Filtro de un clip: color → recorte con la proporción de la ventana → escala exacta."""
    sw, sh = tam(toma); cx, cy = centro
    h = ancho * H / W
    if h > sh: h = sh; ancho = h * W / H
    ancho = min(ancho, sw)
    x = min(max(cx - ancho / 2, 0), sw - ancho); y = min(max(cy - h / 2, 0), sh - h)
    ev = lambda v: int(round(v / 2) * 2)
    crop = f"crop={ev(ancho)}:{ev(h)}:{ev(x)}:{ev(y)}"
    c = COLOR[toma]
    if c == "hdr":
        pre = TM + ("," + CORR[toma] if toma in CORR else "")
        esc = f"scale={W}:{H}:flags=lanczos:out_range=tv:out_color_matrix=bt709"
        return f"{pre},{crop},{esc},setsar=1,fps={FPS},format=yuv444p"
    rng = "pc" if c == "sdr_pc" else "tv"
    return f"{crop},scale={W}:{H}:flags=lanczos:in_range={rng}:out_range=tv:in_color_matrix=bt709:out_color_matrix=bt709,setsar=1,fps={FPS},format=yuv444p"

