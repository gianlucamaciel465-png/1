# Textos editoriales de ROCCE_proxima: una capa RGBA por cuadro (1080×1920, 30 fps) para superponer al montaje.
# Cada momento tiene una idea dominante: la palabra clave más grande; el resto, en una línea de apoyo.
# Tipografía de la casa: Inter Display (ExtraBold para la idea, SemiBold para el apoyo), blanca con sombra suave.
# Celeste (#A9C8E8) solo sobre fondo oscuro (remera negra); sobre cielo o espuma, blanco con degradé oscuro detrás
# (el celeste queda para la prenda). Entradas: fundido de 0,14 s con subida de 12 px; salidas en el corte, secas.
# Zonas seguras de Instagram: nada importante arriba de y=230, debajo de y=1500 ni a la derecha de x=940 (íconos).
#
# Uso: python3 textos.py LINEA_DE_TIEMPO.json SALIDA_DIR   (la línea de tiempo la escribe montaje.py)
#   LINEA_DE_TIEMPO.json → "textos": [{"id", "t0", "t1", "fi"?, "fo"?, "tachar"?}], "duracion"
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/opentype/inter/InterDisplay-{}.otf"
BLANCO, CELESTE, TINTA = (255, 255, 255), (169, 200, 232), (17, 17, 17)
_f = {}
def F(peso, px):
    if (peso, px) not in _f: _f[(peso, px)] = ImageFont.truetype(FD.format(peso), px)
    return _f[(peso, px)]

# ---------- diseño de cada texto ----------
# línea = (y del centro de las mayúsculas, [(texto, peso, px, color, espaciado_px), ...])
L = lambda y, *tramos: (y, [t if len(t) == 5 else t + (0,) for t in tramos])
TEXTOS = {
    # A — gancho sobre el macro de la negra (fondo oscuro: celeste permitido)
    "A_pregunta": [L(372, ("¿Hace cuánto que guardás", "SemiBold", 62, BLANCO)),
                   L(520, ("ESA IDEA?", "ExtraBold", 158, CELESTE, 2))],
    # B — quién es (rótulo documental)
    "B_nombre":   [L(1268, ("GIANLUCA", "ExtraBold", 104, BLANCO, 8)),
                   L(1352, ("fundador de Roccé", "SemiBold", 50, BLANCO))],
    # C — la lección de su historia
    "C_espera":   [L(330, ("NO ESPERÓ", "ExtraBold", 132, BLANCO, 2)),
                   L(448, ("el momento ideal.", "SemiBold", 66, BLANCO))],
    # D — cada detalle, con el plano que lo muestra
    "D_denim":    [L(318, ("DENIM.", "ExtraBold", 150, BLANCO, 6)),
                   L(424, ("ROCCÉ en parche de jean", "SemiBold", 50, BLANCO))],
    "D_tono":     [L(318, ("TONO SOBRE TONO.", "ExtraBold", 86, BLANCO, 2)),
                   L(424, ("ROCCÉ en denim negro", "SemiBold", 50, BLANCO))],
    "D_frase":    [L(318, ("LA FRASE.", "ExtraBold", 150, BLANCO, 4)),
                   L(424, ("en el pecho", "SemiBold", 50, BLANCO))],
    # E — la tesis: la decisión vuelve al espectador
    "E_tesis":    [L(300, ("La próxima Roccé", "SemiBold", 66, BLANCO)),
                   L(384, ("puede empezar", "SemiBold", 66, BLANCO)),
                   L(520, ("CON VOS.", "ExtraBold", 176, BLANCO, 4))],
    # F1 — el villano ("algún día") tachado por una fecha
    "F1_algun":   [L(318, ("ALGÚN DÍA", "Bold", 104, BLANCO, 6))],
    "F1_fecha":   [L(500, ("01/11", "ExtraBold", 230, BLANCO, 4))],
    "F1_cien":    [L(724, ("LOS PRIMEROS 100", "ExtraBold", 92, BLANCO, 2)),
                   L(820, ("en comprar son ", "SemiBold", 60, BLANCO), ("FOUNDERS.", "ExtraBold", 60, BLANCO, 2))],
    # F2 — el beneficio confirmado (sin cifras ni plazos)
    "F2_001":     [L(330, ("FOUNDER 001", "ExtraBold", 126, BLANCO, 4)),
                   L(448, ("diseña una prenda", "SemiBold", 68, BLANCO))],
    "F2_pct":     [L(292, ("y se lleva", "SemiBold", 64, BLANCO)),
                   L(410, ("UN PORCENTAJE", "ExtraBold", 104, BLANCO, 2)),
                   L(520, ("de la ganancia.", "SemiBold", 64, BLANCO))],
    # G — una sola acción, con la misma palabra que dice la voz
    "G_escribinos": [L(300, ("Escribinos", "SemiBold", 76, BLANCO))],
    "G_ruta":     [L(616, ("hoy, por mensaje a ", "SemiBold", 56, BLANCO), ("@rocce.ar", "ExtraBold", 56, BLANCO))],
    "G_participar": [L(700, ("y conocé cómo participar.", "SemiBold", 56, BLANCO))],
    "G_datos":    [L(1376, ("Drop Founders Privée — 01/11/2026", "Bold", 46, BLANCO)),
                   L(1442, ("Primeros 100 founders · el 001 diseña una prenda", "SemiBold", 38, BLANCO))],
}
BURBUJA = dict(y=446, texto="FOUNDERS", peso="ExtraBold", px=118, esp=4)     # mensaje a escribir (no es un botón)
DEGRADES = {   # nombre: (desde_y, hasta_y, opacidad_máx, arriba=True) — negro suave detrás del texto
    "grad_sup":   (0, 760, 0.60, True),
    "grad_sup_l": (0, 860, 0.62, True),
    "grad_fuerte": (0, 900, 0.74, True),
    "grad_f1":    (0, 1040, 0.78, True),
    "grad_inf":   (1180, 1560, 0.55, False),
}

def ancho(tramos):
    return sum(F(p, px).getlength(t) + esp * max(0, len(t) - 1) for t, p, px, c, esp in tramos)

def dibujar(d, dm, x, y, tramos):
    for t, p, px, c, esp in tramos:
        ft = F(p, px); cap = ft.getbbox("H"); base = y + (cap[3] - cap[1]) / 2
        for ch in (t if esp else [t]):
            d.text((x, base), ch, font=ft, fill=c + (255,), anchor="ls"); dm.text((x, base), ch, font=ft, fill=255, anchor="ls")
            x += ft.getlength(ch) + esp
    return x

def sombra(img, mask, r=6, a=0.55, dy=3):
    s = mask.filter(ImageFilter.GaussianBlur(r)).point(lambda v: int(v * a))
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0)); capa.paste((0, 0, 0, 255), (0, dy), s)
    return Image.alpha_composite(capa, img)

def capa_texto(lineas, nombre=""):
    for y, tramos in lineas:                         # margen lateral mínimo de 70 px (íconos de Instagram a la derecha)
        if ancho(tramos) > W - 140: print(f"AVISO {nombre}: línea de {ancho(tramos):.0f} px, más ancha que {W - 140}")
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); mask = Image.new("L", (W, H), 0)
    d, dm = ImageDraw.Draw(img), ImageDraw.Draw(mask); cajas = []
    for y, tramos in lineas:
        x0 = (W - ancho(tramos)) / 2; x1 = dibujar(d, dm, x0, y, tramos); cajas.append((x0, x1, y))
    return sombra(img, mask), cajas

def capa_burbuja():
    b = BURBUJA; ft = F(b["peso"], b["px"]); t = b["texto"]
    tw = ft.getlength(t) + b["esp"] * (len(t) - 1); cap = ft.getbbox("H"); ch = cap[3] - cap[1]
    pw, ph = 46, 34; x0 = (W - tw) / 2 - pw; x1 = (W + tw) / 2 + pw; y0 = b["y"] - ch / 2 - ph; y1 = b["y"] + ch / 2 + ph
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) / 2.6, fill=BLANCO + (255,))
    d.polygon([(x0 + 70, y1 - 8), (x0 + 38, y1 + 30), (x0 + 118, y1 - 8)], fill=BLANCO + (255,))   # colita de mensaje
    sh = img.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.45))
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0)); base.paste((0, 0, 0, 255), (0, 6), sh)
    img = Image.alpha_composite(base, img); d = ImageDraw.Draw(img); dm = ImageDraw.Draw(Image.new("L", (W, H)))
    dibujar(d, dm, (W - tw) / 2, b["y"], [(t, b["peso"], b["px"], TINTA, b["esp"])])
    return img

def capa_degrade(y0, y1, a, arriba):
    yy = np.arange(H, dtype=np.float32)[:, None]
    u = np.clip((y1 - yy) / (y1 - y0), 0, 1) if arriba else np.clip((yy - y0) / (y1 - y0), 0, 1)
    al = (u ** 1.4 * a * 255).astype(np.uint8)
    g = np.zeros((H, W, 4), np.uint8); g[..., 3] = np.broadcast_to(al, (H, W)); return Image.fromarray(g, "RGBA")

def preparar():
    capas, cajas = {}, {}
    for k, lin in TEXTOS.items(): capas[k], cajas[k] = capa_texto(lin, k)
    capas["G_burbuja"] = capa_burbuja()
    for k, v in DEGRADES.items(): capas[k] = capa_degrade(*v)
    return {k: np.asarray(v, np.float32) / 255 for k, v in capas.items()}, cajas

def ease(u): return 1 - (1 - u) ** 3

if __name__ == "__main__":
    tl, out = json.load(open(sys.argv[1])), sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".png"): os.remove(os.path.join(out, f))
    capas, cajas = preparar()
    n = int(round(tl["duracion"] * FPS)); ev = tl["textos"]; prev = None
    for i in range(n):
        t = (i + 0.5) / FPS; estado = []
        for e in ev:
            if not (e["t0"] <= t < e["t1"]): continue
            fi, fo = e.get("fi", 0.14), e.get("fo", 0.0)
            a = ease(min(1, (t - e["t0"]) / fi)) if fi > 0 else 1.0
            if fo > 0: a *= min(1, (e["t1"] - t) / fo)
            dy = int(round(12 * (1 - a))) if (fi > 0 and not e["id"].startswith("grad")) else 0
            p = ease(min(1, (t - e["tachar"]) / 0.18)) if ("tachar" in e and t >= e["tachar"]) else None
            estado.append((e["id"], round(a, 3), dy, None if p is None else round(p, 3)))
        if estado == prev:                                               # cuadro igual al anterior: se copia
            os.link(f"{out}/{i - 1:04d}.png", f"{out}/{i:04d}.png"); continue
        prev = estado; acc = np.zeros((H, W, 4), np.float32)            # color premultiplicado + alfa
        for k, a, dy, p in estado:
            c = capas[k].copy()
            if p is not None:                                           # raya que tacha "ALGÚN DÍA", de izquierda a derecha
                x0, x1, y = cajas[k][0]; y = int(y); xs = int(x0 - 14); xe = int(x0 - 14 + p * (x1 - x0 + 28))
                c[y - 6:y + 6, xs:xe, :] = 1.0
            if dy: c = np.roll(c, dy, axis=0)
            al = c[..., 3:4] * a
            acc[..., :3] = c[..., :3] * al + acc[..., :3] * (1 - al); acc[..., 3:4] = al + acc[..., 3:4] * (1 - al)
        rgb = acc[..., :3] / np.maximum(acc[..., 3:4], 1e-6)
        Image.fromarray((np.clip(np.dstack([rgb, acc[..., 3:4]]), 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(f"{out}/{i:04d}.png", compress_level=1)
    print(f"{out}: {n} cuadros")
