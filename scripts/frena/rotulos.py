# Rótulos en el estilo de Neuron Visuals (mayúsculas cuadradas redondeadas, espaciadas) para R1 "lo que te frena".
# Misma técnica que scripts/rotulos_r14.py, como función, con Saira (OFL; la más parecida al original entre las
# probadas: D de lado recto, O redondeada, A con vértice angosto) ajustada en ancho (≈ 0,75 del alto), I con remates
# como el original, tildes de la fuente. Medido en R1: alto de mayúscula 26 px, hueco entre letras ≈ 0,43 del alto,
# gris claro ≈ 182. Orbitron (la de R14) se descartó acá: su D y su O se confunden y su A es plana.
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fuentes", "Saira-Variable.ttf")
SS = 4

class Estilo:
    def __init__(self, cap=26.0, gap=0.43, wght=600, dil=0.02, fuente=None, ancho=0.75):
        self.cap, self.gap, self.dil = cap, gap, dil
        fuente = fuente or FONT
        def abrir(px):
            f = ImageFont.truetype(fuente, px)
            if wght is not None:
                try:
                    ejes = f.get_variation_axes()
                    f.set_variation_by_axes([wght if b"eight" in e["name"] else e["default"] for e in ejes])
                except Exception: pass
            return f
        probe = abrir(400)
        bb = probe.getbbox("H"); size = 400 * cap * SS / (bb[3] - bb[1])
        self.ft = abrir(int(size))
        hb = self.ft.getbbox("H"); self.capH = hb[3] - hb[1]
        ref_w = np.median([self.ft.getbbox(c)[2] - self.ft.getbbox(c)[0] for c in "ACEKNORST"])
        self.sx = ancho * self.capH / ref_w
        self.stems = self._stems()

    def _raw(self, c):
        ft, capH = self.ft, self.capH
        bb = ft.getbbox(c); gw = bb[2] - bb[0]
        im = Image.new("L", (gw + 8 * SS, int(capH * 1.7)), 0)
        ImageDraw.Draw(im).text((4 * SS - bb[0], int(capH * 0.4) - ft.getbbox("H")[1]), c, font=ft, fill=255)
        cols = np.where(np.asarray(im).max(0) > 0)[0]; im = im.crop((cols.min(), 0, cols.max() + 1, im.height))
        im = im.resize((max(1, round(im.width * self.sx)), im.height), Image.LANCZOS)
        d = int(round(self.dil * capH))
        if d > 0:
            a = np.pad(np.asarray(im), ((0, 0), (d, d)))
            a = np.max(np.stack([a[:, k:k + a.shape[1] - 2 * d] for k in range(2 * d + 1)]), 0)
            im = Image.fromarray(a.astype(np.uint8), "L")
        return im

    def _stems(self):
        h = np.asarray(self._raw("H")) > 128; ys = np.where(h.any(1))[0]; row = h[ys.min() + (ys.max() - ys.min()) // 4]
        sv = int(np.argmax(~row[np.argmax(row):]))
        e = np.asarray(self._raw("E")) > 128; col = e[:, e.shape[1] // 2]; top = np.argmax(col)
        return sv, int(np.argmax(~col[top:]))

    def glifo(self, c):
        if c == " ": return None
        if c == "I":
            ref = np.asarray(self._raw("H")); rows = np.where(ref.max(1) > 128)[0]; y0, y1 = rows.min(), rows.max() + 1
            sv, sh = self.stems; wI = int(round(0.44 * self.capH)); a = np.zeros((ref.shape[0], wI), np.uint8)
            a[y0:y0 + sh, :] = 255; a[y1 - sh:y1, :] = 255; x0 = (wI - sv) // 2; a[y0:y1, x0:x0 + sv] = 255
            return Image.fromarray(a, "L")
        return self._raw(c)

    def linea(self, texto):
        """Máscara L (sobremuestreada → tamaño final) del texto; devuelve (máscara, y de la línea de base superior)."""
        gl = [self.glifo(c) for c in texto]; gap = self.gap * self.capH; space = max(0.0, 1.0 * self.capH - 2 * gap)
        widths = [g.width if g else space for g in gl]
        total = sum(widths) + gap * (len(gl) - 1)
        line = Image.new("L", (int(total) + 2, int(self.capH * 1.7)), 0); x = 0.0
        for g, w in zip(gl, widths):
            if g: line.paste(g, (int(round(x)), 0), g)
            x += w + gap
        line = line.resize((max(1, round(line.width / SS)), max(1, round(line.height / SS))), Image.LANCZOS)
        a = np.asarray(line)
        top_cap = int(round(self.capH * 0.4 / SS))          # fila donde empieza la mayúscula (sin tilde)
        return a, top_cap

def capa_rgba(mask, color=(182, 182, 182), halo=0.06):
    """RGBA float (0–1) del texto con un halo muy suave como el original."""
    a = mask.astype(np.float32) / 255
    h = np.asarray(Image.fromarray(mask).filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255
    alpha = np.clip(a + halo * h / max(h.max(), 1e-6), 0, 1)
    out = np.zeros(mask.shape + (4,), np.float32); out[..., :3] = np.array(color, np.float32) / 255; out[..., 3] = alpha
    return out
