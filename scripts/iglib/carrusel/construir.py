# IGLIB-3 «Ambos permanecen» v01 · construye las 6 láminas desde los originales.
#   1. recursos: fotos de PRODUCTO/ (Display P3 → sRGB con ImageCms), recortes, blanco neutro; base de L4 con el gris del piso
#   2. capas de Chromium (node capas.js): base, capa superior, L6 cuadro a cuadro, ventanas medidas
#   3. ventanas: cuadros reales de cada toma (HDR → SDR mobius en video.py), recorte fijo / con claves / completo / seguimiento
#   4. composición en RGB (base + ventanas + capa superior) y codificación H.264 High 4.0, yuv420p, BT.709, 30 fps, sin audio
#      PNG: base con perfil sRGB incrustado
# Uso: python3 construir.py [L1 L2 …]   (sin argumentos: todas). Salida en proyecto.SALIDA.
import io, os, sys, json, subprocess
import numpy as np
from PIL import Image, ImageCms, ImageFilter
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
from proyecto import *
from video import cuadros, info

REC, CAP = os.path.join(TRAB, "recursos"), os.path.join(TRAB, "capas")
for d in (REC, CAP, SALIDA): os.makedirs(d, exist_ok=True)
SRGB = ImageCms.createProfile("sRGB"); SRGB_B = ImageCms.ImageCmsProfile(SRGB).tobytes()
solo = sys.argv[1:] or list(LAMINAS)

def a_srgb(ruta):
    im = Image.open(ruta)
    p = im.info.get("icc_profile")
    if p:   # las fotos de iPhone vienen en Display P3
        im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(p)), SRGB, outputMode="RGB",
                                       renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC)
    return im.convert("RGB")

def neutro(rgb, g):
    """Ganancias por canal con rampa: plenas si min(R,G,B) ≤ 230, nulas desde 250 (lo quemado no se toca)."""
    a = rgb.astype(np.float32)
    w = np.clip((250.0 - a.min(axis=2)) / 20.0, 0, 1)[..., None]
    b = a * (1 + w * (np.array(g, np.float32) - 1))
    return np.clip(b + 0.5, 0, 255).astype(np.uint8)

# ---------- 1. recursos ----------
def recursos():
    for nombre, (archivo, (x, y, w, h), (W2, H2)) in FOTOS.items():
        im = a_srgb(os.path.join(PROD, archivo)).crop((x, y, x + w, y + h)).resize((W2, H2), Image.LANCZOS)
        a = np.array(im)
        if archivo in NEUTRO: a = neutro(a, NEUTRO[archivo])
        Image.fromarray(a).save(os.path.join(REC, nombre + ".png"))
    # L4: dos espaldas de estudio a 540 de ancho; arriba y abajo, el gris del piso medido en el borde de cada foto
    base = np.zeros((H, W, 3), np.float32); F = L4["fundido"]; med = {}
    for i, lado in enumerate(("blanca", "negra")):
        im = a_srgb(os.path.join(PROD, L4[lado]["archivo"]))
        im = im.resize((540, round(im.height * 540 / im.width)), Image.LANCZOS); f = np.array(im).astype(np.float32)
        top = L4[lado]["top"]; hh = f.shape[0]
        g_arr = np.median(f[:12].reshape(-1, 3), axis=0); g_ab = np.median(f[-12:].reshape(-1, 3), axis=0)
        med[lado] = dict(gris_arriba=[int(v) for v in g_arr], gris_abajo=[int(v) for v in g_ab], alto=hh, top=top)
        col = np.zeros((H, 540, 3), np.float32)
        col[:top] = g_arr; col[top + hh:] = g_ab
        col[top:top + hh] = f
        rampa = np.linspace(0, 1, F, dtype=np.float32)[:, None, None]       # fundido de 60 px dentro de la foto
        col[top:top + F] = g_arr * (1 - rampa) + f[:F] * rampa
        col[top + hh - F:top + hh] = f[hh - F:] * (1 - rampa) + g_ab * rampa
        base[:, i * 540:(i + 1) * 540] = col
    Image.fromarray(np.clip(base + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(REC, "L4_base.png"))
    json.dump(med, open(os.path.join(REC, "L4_medidas.json"), "w"), indent=1)
    print("recursos listos:", sorted(os.listdir(REC)))

# ---------- 2. capas ----------
def capas():
    subprocess.run(["node", os.path.join(AQUI, "capas.js"), os.path.join(AQUI, "pagina.html"), CAP,
                    str(LAMINAS["L6"]["cuadros"])], check=True, stdin=subprocess.DEVNULL)
    return json.load(open(os.path.join(CAP, "ventanas.json")))

# ---------- 3. ventanas ----------
def suavizar(v, s):
    if s <= 0: return v
    r = int(3 * s); k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum()
    return np.convolve(np.pad(v, r, mode="edge"), k, mode="valid")

def trayectoria(claves, n, s):
    ks = [c[0] for c in claves]
    cx = suavizar(np.interp(np.arange(n), ks, [c[1] for c in claves]), s)
    cy = suavizar(np.interp(np.arange(n), ks, [c[2] for c in claves]), s)
    return cx, cy

def recorte(im, cx, cy, w, h):
    sw, sh = im.size
    w = min(w, sw); h = min(h, sh)
    x0 = min(max(cx - w / 2, 0), sw - w); y0 = min(max(cy - h / 2, 0), sh - h)
    return (x0, y0, x0 + w, y0 + h)

def ventana(v, n, registro):
    """Generador de los cuadros de una ventana (RGB uint8 del tamaño de la caja)."""
    bw, bh = v["caja"][2], v["caja"][3]
    corr = CORR_FFMPEG.get(v["toma"]); g = NEUTRO.get(v["toma"])
    fuente = cuadros(v["toma"], v["desde"], n, corr)
    if v["recorte"] == "seguir_y":
        # seguimiento vertical: borde superior de la remera negra (primer renglón de la zona con más del 60 % de
        # píxeles oscuros). La correlación de fase sobre la zona fallaba con la espuma de la ola.
        frames = [f.copy() for f in fuente]; x0, y0z, x1, y1z = v["zona"]
        bordes = []
        for f in frames:
            osc = f[y0z:y1z, x0:x1].astype(np.float32).mean(axis=2) < v["umbral"]
            filas = np.where(osc.mean(axis=1) > 0.6)[0]; bordes.append(y0z + filas.min())
        bordes = np.array(bordes, np.float32)
        dys_s = suavizar(bordes - bordes[0], v["sigma"])
        registro["borde_remera_negra_y"] = [int(b) for b in bordes]
        registro["desplazamiento_y_px"] = [round(float(d), 1) for d in dys_s]
        fuente = iter(frames)
    for k, f in enumerate(fuente):
        if g: f = neutro(f, g)
        im = Image.fromarray(f)
        if v["recorte"] == "fijo":
            cx, cy = v["centro"]; caja = recorte(im, cx, cy, v["ancho"], v["ancho"] * bh / bw)
            out = im.resize((bw, bh), Image.LANCZOS, box=caja)
        elif v["recorte"] == "claves":
            if k == 0: v["_cx"], v["_cy"] = trayectoria(v["claves"], n, v["sigma"])
            caja = recorte(im, v["_cx"][k], v["_cy"][k], v["ancho"], v["ancho"] * bh / bw)
            out = im.resize((bw, bh), Image.LANCZOS, box=caja)
        elif v["recorte"] == "completo":
            # toma entera en la zona nítida; arriba y abajo, relleno de una zona SIN PERSONA de la misma toma
            # (cielo y baranda del costado izquierdo), ampliada y desenfocada, con fundido de 24 px (sin cabeza fantasma)
            nx, ny, nw, nh = v["nitido"]
            lienzo = np.zeros((bh, bw, 3), np.float32)
            for zona, (y_a, y_b) in ((v["relleno_arriba"], (0, ny)), (v["relleno_abajo"], (ny + nh, bh))):
                r = im.resize((bw, y_b - y_a), Image.LANCZOS, box=zona).filter(ImageFilter.GaussianBlur(v["desenfoque"]))
                lienzo[y_a:y_b] = np.array(r)
            nit = np.array(im.resize((nw, nh), Image.LANCZOS)).astype(np.float32)
            a = np.ones((nh, 1, 1), np.float32); F = 24; rampa = np.linspace(0, 1, F, dtype=np.float32)[:, None, None]
            a[:F] = rampa; a[-F:] = rampa[::-1]
            vieja = lienzo[ny:ny + nh, nx:nx + nw].copy()
            vieja[:F] = lienzo[ny - 1:ny, nx:nx + nw]; vieja[-F:] = lienzo[ny + nh:ny + nh + 1, nx:nx + nw]
            lienzo[ny:ny + nh, nx:nx + nw] = nit * a + vieja * (1 - a)
            out = Image.fromarray(np.clip(lienzo + 0.5, 0, 255).astype(np.uint8))
            caja = (0, 0, im.width, im.height)
        elif v["recorte"] == "seguir_y":
            y0 = v["y0"] + dys_s[k]; y0 = min(max(y0, 0), im.height - bh)
            caja = (0, y0, im.width, y0 + bh * im.width / bw)
            out = im.resize((bw, bh), Image.LANCZOS, box=caja)
        registro.setdefault("recortes", []).append([round(c, 1) for c in caja])
        yield np.array(out)

def mascara_circulo(d, s=4):
    yy, xx = np.mgrid[0:d * s, 0:d * s]; c = (d * s - 1) / 2
    m = ((xx - c) ** 2 + (yy - c) ** 2 <= (d * s / 2) ** 2).astype(np.float32)
    return m.reshape(d, s, d, s).mean(axis=(1, 3))[..., None]

# ---------- 4. composición y codificación ----------
# mbtree=0 + aq-mode=0 + psy-rd=0: sin esto x264 "retoca" las zonas fijas en los primeros cuadros (bordes de texto que
# cambiaban hasta 64 niveles fuera de las ventanas); con esto el cambio máximo afuera baja a ≈ 8 (medido sobre L1).
ENC = ["-c:v", "libx264", "-preset", "slow", "-crf", "16", "-x264-params", "mbtree=0:aq-mode=0:psy-rd=0.0,0.0",
       "-profile:v", "high", "-level:v", "4.0", "-maxrate", "20M",
       "-bufsize", "25M", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
       "-color_range", "tv", "-an", "-map_metadata", "-1", "-movflags", "+faststart"]

def rgba(ruta):
    a = np.array(Image.open(ruta).convert("RGBA")).astype(np.float32)
    return a[..., :3], a[..., 3:4] / 255.0

def lamina_mp4(nl, pag, vent, ficha):
    n = pag["cuadros"]; base = np.array(Image.open(os.path.join(CAP, f"base_{nl}.png")).convert("RGB")).astype(np.float32)
    assert base.shape == (H, W, 3), base.shape
    if not pag.get("animada"): top_rgb, top_a = rgba(os.path.join(CAP, f"arriba_{nl}.png"))
    gens, cajas, masks = [], [], []
    for v in pag["ventanas"]:
        med = next(m for m in vent[nl] if m["id"] == v["id"])
        assert (med["x"], med["y"], med["w"], med["h"]) == tuple(v["caja"]), f"{nl}/{v['id']}: la página mide {med} y el proyecto dice {v['caja']}"
        reg = ficha.setdefault(nl, {}).setdefault(v["id"], dict(toma=f"ORIGINALES/{v['toma']}.mov", desde=v["desde"],
              hasta=round(v["desde"] + n / FPS, 3), cuadros=n, caja=v["caja"], recorte=v["recorte"], nota=v["nota"]))
        gens.append(ventana(v, n, reg)); cajas.append(v["caja"])
        masks.append(mascara_circulo(v["caja"][2]) if v.get("mascara") == "circulo" else None)
    final = os.path.join(SALIDA, f"IGLIB-3_{nl}_{VER}.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p",
                          "-frames:v", str(n), "-r", str(FPS)] + ENC + [final], stdin=subprocess.PIPE)
    for k in range(n):
        fr = base.copy()
        for gen, (x, y, w, h), m in zip(gens, cajas, masks):
            c = next(gen).astype(np.float32)
            if m is None: fr[y:y + h, x:x + w] = c
            else: fr[y:y + h, x:x + w] = c * m + fr[y:y + h, x:x + w] * (1 - m)
        if pag.get("animada"): top_rgb, top_a = rgba(os.path.join(CAP, "L6", f"arriba_{k:03d}.png"))
        fr = top_rgb * top_a + fr * (1 - top_a)
        p.stdin.write(np.clip(fr + 0.5, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); assert p.wait() == 0
    print(final, f"{os.path.getsize(final) / 1e6:.2f} MB")

def lamina_png(nl):
    final = os.path.join(SALIDA, f"IGLIB-3_{nl}_{VER}.png")
    im = Image.open(os.path.join(CAP, f"base_{nl}.png")).convert("RGB"); assert im.size == (W, H)
    im.save(final, icc_profile=SRGB_B, optimize=True); print(final)

if __name__ == "__main__":
    recursos()
    vent = capas()
    ruta_f = os.path.join(CAP, "clips_usados.json")
    ficha = json.load(open(ruta_f)) if os.path.exists(ruta_f) else {}
    for nl in solo:
        pag = LAMINAS[nl]
        if pag["tipo"] == "png": lamina_png(nl)
        else: ficha.pop(nl, None); lamina_mp4(nl, pag, vent, ficha)
    json.dump(ficha, open(ruta_f, "w"), indent=1, ensure_ascii=False)
