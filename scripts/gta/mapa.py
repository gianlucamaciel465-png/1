#!/usr/bin/env python3
"""GTA6 «La misión» · mapa del cambio de personaje, 15,00–16,00 (Pedro, 19/11/2026). Guion §3 plano 7 y §6.

  15,00–15,30 (c450–c458)  el cuadro (último de G7) se achica dentro del mapa sobre Florida y se desatura
  15,30–15,70 (c459–c470)  el mapa baja de Florida a la costa bonaerense (se aleja a mitad de camino para que se lea
                           el continente), con ruta punteada celeste y marcador
  15,70–16,00 (c471–c479)  dos picadas sobre el marcador; la segunda entra al marcador, cuyo interior es el negro
                           medido de la espalda de 7887 a z 2,5 (TRABAJO/gta/negro_7887.json, promedio del recorte):
                           c479 queda lleno de ese color y en D (c480) abre 7887.
Costas: Natural Earth 1:50m «land» (dominio público), raw.githubusercontent.com/nvkelso/natural-earth-vector,
descargado el 19/11/2026 a TRABAJO/gta/ne/. Proyección Mercator. Sin rótulos. El marcador es esquemático: un punto de
la costa atlántica bonaerense tomado del propio mapa, no la ubicación GPS de ninguna toma.
Paleta: mar azul noche, tierra blanco humo con borde celeste humo, ruta celeste con borde azul noche.
El vuelo (180°, 24 muestras) y las picadas (90°, 12 muestras) llevan desenfoque de movimiento por supermuestreo temporal.
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, '/home/user/1/scripts/gta')
from comun import T, W, H, FPS, CELESTE, clamp, ease_in_out, ease_out, lerp, guardar_json   # noqa

NE = T / 'ne/ne_50m_land.geojson'
MAR = (9, 20, 44)                  # azul noche
TIERRA = (230, 236, 241)           # blanco humo
COSTA = (163, 190, 212)            # celeste humo
GRILLA = (255, 255, 255, 14)
RUTA_BORDE = (9, 20, 44)

N0, N_ACHICA, N_VUELO, N_PICADA1, N_PICADA2, N_FIN = 450, 459, 471, 471, 476, 480
FLORIDA = (-80.35, 25.95)          # Florida (sur de la península)
DEST_LAT = -37.6                   # costa atlántica bonaerense: vértice de costa más cercano a esta latitud con lon > −58,5
S_F, S_MED, S_B = 105.0, 16.0, 105.0   # px por grado de Mercator: Florida / mitad del vuelo / llegada
SS = 2                             # supermuestreo espacial del dibujo


def merc(lon, lat):
    lat = np.clip(lat, -85, 85)
    return lon, np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))


class Mapa:
    def __init__(self):
        g = json.loads(NE.read_text())
        self.anillos = []                # (array Nx2 mercator, es_hueco)
        for f in g['features']:
            geo = f['geometry']
            polys = geo['coordinates'] if geo['type'] == 'MultiPolygon' else [geo['coordinates']]
            for poly in polys:
                for i, ring in enumerate(poly):
                    a = np.asarray(ring, np.float64)
                    x, y = merc(a[:, 0], a[:, 1])
                    self.anillos.append((np.stack([x, y], 1), i > 0))
        self.bb = [(r[:, 0].min(), r[:, 1].min(), r[:, 0].max(), r[:, 1].max()) for r, _ in self.anillos]
        self.dest = self._destino()
        self.orig = np.array(merc(*FLORIDA), np.float64)
        try:
            nj = json.loads((T / 'negro_7887.json').read_text())
            # v01: tela sola (03 de Roma, corrección 2); v00 usaba la media del recorte (con estampado y roca)
            self.negro = tuple(int(round(v)) for v in nj.get('v01_tela_remera', {}).get('rgb', nj['media_recorte_rgb']))
        except FileNotFoundError:
            self.negro = (48, 43, 41)
        # ruta: Bézier cuadrática que se abre sobre el Atlántico
        p0, p2 = self.orig, self.dest
        p1 = np.array([-38.0, (p0[1] + p2[1]) / 2 + 4.0])
        u = np.linspace(0, 1, 400)[:, None]
        self.ruta = (1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u ** 2 * p2

    def _destino(self):
        best = None
        _, y0 = merc(0, DEST_LAT)
        for (r, hueco), bb in zip(self.anillos, self.bb):
            if hueco or bb[2] < -66 or bb[0] > -50 or bb[3] < -48 or bb[1] > -30:
                continue
            m = (r[:, 0] > -58.5) & (r[:, 0] < -56.0)
            if not m.any():
                continue
            d = np.abs(r[m, 1] - y0)
            i = int(np.argmin(d))
            if best is None or d[i] < best[0]:
                best = (d[i], r[m][i])
        return np.array(best[1], np.float64)

    # ---------------------------------------------------------------------------------------------
    def camara(self, n_f):
        """(centro mercator, escala px/grado) para un cuadro fraccional."""
        if n_f < N_ACHICA:          # sobre Florida; leve alejamiento mientras el cuadro se achica
            u = (n_f - N0) / (N_ACHICA - N0)
            return self.orig.copy(), S_F * lerp(1.45, 1.0, ease_out(u, 2))
        if n_f < N_VUELO:           # vuelo Florida → costa bonaerense
            u = ease_in_out((n_f - N_ACHICA) / (N_VUELO - N_ACHICA))
            cen = self.orig + (self.dest - self.orig) * u
            # escala en log: baja a S_MED en el medio
            ls = math.log(S_F) * (1 - u) + math.log(S_B) * u
            ls = ls - (math.log(S_F) - math.log(S_MED)) * math.sin(math.pi * u) ** 1.2
            return cen, math.exp(ls)
        if n_f < N_PICADA2:         # picada 1: ×3 con salida suave
            u = ease_out((n_f - N_PICADA1) / (N_PICADA2 - N_PICADA1 - 1), 3)
            return self.dest.copy(), S_B * lerp(1.0, 3.0, u)
        # picada 2: se acerca al marcador hasta que su interior llena la pantalla en c479
        u = clamp((n_f - N_PICADA2) / (N_FIN - 1 - N_PICADA2))
        return self.dest.copy(), S_B * 3.0 * math.exp(math.log(16.0) * u ** 1.6)

    def a_pantalla(self, pts, cen, s):
        x = W / 2 + (pts[:, 0] - cen[0]) * s
        y = H / 2 - (pts[:, 1] - cen[1]) * s
        return np.stack([x, y], 1)

    def dibujar(self, n_f, contenido=None):
        """RGB uint8 del mapa para un cuadro fraccional (sin el cuadro achicado)."""
        cen, s = self.camara(n_f)
        im = Image.new('RGB', (W * SS, H * SS), MAR)
        d = ImageDraw.Draw(im, 'RGBA')
        vx0 = cen[0] - W / 2 / s; vx1 = cen[0] + W / 2 / s; vy0 = cen[1] - H / 2 / s; vy1 = cen[1] + H / 2 / s
        # grilla cada 10° (lat/lon) muy tenue
        for lon in range(-180, 181, 10):
            if vx0 <= lon <= vx1:
                x = (W / 2 + (lon - cen[0]) * s) * SS; d.line([(x, 0), (x, H * SS)], fill=GRILLA, width=SS)
        for lat in range(-80, 81, 10):
            _, yy = merc(0, lat)
            if vy0 <= yy <= vy1:
                y = (H / 2 - (yy - cen[1]) * s) * SS; d.line([(0, y), (W * SS, y)], fill=GRILLA, width=SS)
        for (r, hueco), bb in zip(self.anillos, self.bb):
            if bb[2] < vx0 or bb[0] > vx1 or bb[3] < vy0 or bb[1] > vy1:
                continue
            p = self.a_pantalla(r, cen, s) * SS
            # simplificación por distancia en pantalla (≥ 1,5 px)
            keep = np.ones(len(p), bool)
            if len(p) > 50:
                dd = np.r_[np.inf, np.hypot(*np.diff(p, axis=0).T)]
                acc = 0.0
                for i in range(len(p)):
                    acc += dd[i] if np.isfinite(dd[i]) else 1e9
                    if acc < 1.5 * SS:
                        keep[i] = False
                    else:
                        acc = 0.0
            q = [tuple(v) for v in p[keep]]
            if len(q) < 3:
                continue
            d.polygon(q, fill=MAR if hueco else TIERRA, outline=COSTA if not hueco else None, width=max(1, int(1.6 * SS)))
        return im, cen, s

    def ruta_y_marcador(self, im, n_f, cen, s):
        d = ImageDraw.Draw(im, 'RGBA')
        # ruta punteada: se dibuja hasta la fracción p (va un poco delante de la cámara)
        if n_f >= N_ACHICA - 1:
            p = clamp((n_f - (N_ACHICA - 1)) / (N_VUELO - N_ACHICA - 2))
            p = ease_in_out(p)
            k = max(2, int(len(self.ruta) * p))
            q = self.a_pantalla(self.ruta[:k], cen, s)
            # puntos cada 22 px de pantalla
            seg = np.hypot(*np.diff(q, axis=0).T); acum = np.r_[0, np.cumsum(seg)]
            paso = 22.0
            for t in np.arange(0, acum[-1], paso):
                i = min(np.searchsorted(acum, t), len(q) - 1)
                x, y = q[i]
                if -20 < x < W + 20 and -20 < y < H + 20:
                    r = 7
                    d.ellipse([(x - r - 2.5) * SS, (y - r - 2.5) * SS, (x + r + 2.5) * SS, (y + r + 2.5) * SS], fill=RUTA_BORDE + (255,))
                    d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=CELESTE + (255,))
        # marcador de destino: aparece al 55 % del vuelo; anillo celeste, borde blanco, interior = negro medido
        if n_f >= N_ACHICA + 0.55 * (N_VUELO - N_ACHICA):
            x, y = self.a_pantalla(self.dest[None], cen, s)[0]
            ap = clamp((n_f - (N_ACHICA + 0.55 * (N_VUELO - N_ACHICA))) / 3)
            base = 30 * ease_out(ap, 2) if n_f < N_PICADA2 else 30
            # en la picada 2 el marcador crece con la cámara: su interior llena la pantalla en c479
            if n_f >= N_PICADA2:
                u = clamp((n_f - N_PICADA2) / (N_FIN - 1 - N_PICADA2))
                base = 30 * math.exp(math.log(1300 / 30) * u ** 1.6)
            r_in = base; r_cel = base * 1.32; r_bl = base * 1.45
            for rr, col in ((r_bl, (255, 255, 255, 255)), (r_cel, CELESTE + (255,)), (r_in, self.negro + (255,))):
                d.ellipse([(x - rr) * SS, (y - rr) * SS, (x + rr) * SS, (y + rr) * SS], fill=col)
            return (x, y, r_in)
        return None

    def cuadro(self, n, contenido=None, sub=3):
        """RGB uint8 1080×1920 del cuadro n (450–479). contenido = último cuadro de G7 (RGB uint8) que se achica."""
        movil = n >= N_ACHICA            # vuelo y picadas: desenfoque de movimiento por supermuestreo temporal
        # v00b: con 5 muestras el vuelo dejaba copias escalonadas (c461–c470). Vuelo: obturador de 180°, 24 muestras;
        # picadas: 90°, 12 muestras (≈0,4 s de render por muestra).
        if not (movil and sub > 1):
            offs = [0.0]
        elif n < N_VUELO:
            offs = list(np.linspace(-0.25, 0.25, 24))
        else:
            offs = list(np.linspace(-0.125, 0.125, 12))
        acc = np.zeros((H, W, 3), np.float32)
        for o in offs:
            n_f = n + o
            im, cen, s = self.dibujar(n_f)
            info = self.ruta_y_marcador(im, n_f, cen, s)
            im = im.resize((W, H), Image.LANCZOS)
            if contenido is not None and n_f < N_VUELO + 2:
                im = self.poner_cuadro(im, contenido, n_f, cen, s)
            acc += np.asarray(im, np.float32)
        out = np.clip(acc / len(offs) + 0.5, 0, 255).astype(np.uint8)
        if n == N_FIN - 1:
            out[...] = self.negro           # c479: lleno del negro medido (la última picada termina en la tela)
        return out

    def poner_cuadro(self, im, contenido, n_f, cen, s):
        """el cuadro de G7 se achica hasta una tarjeta de 20 % anclada en Florida y se desatura (15,00–15,30)."""
        u = ease_in_out((n_f - N0) / (N_ACHICA - N0))
        esc = lerp(1.0, 0.20, u)
        sat = 1 - u
        x, y = self.a_pantalla(self.orig[None], cen, s)[0]
        # centro: del centro de la pantalla a Florida (la tarjeta queda arriba del punto, como una ficha)
        cx = lerp(W / 2, x, u); cy = lerp(H / 2, y - 0.5 * H * 0.20 - 18, u)
        w, h = max(2, int(W * esc)), max(2, int(H * esc))
        c = Image.fromarray(contenido).resize((w, h), Image.LANCZOS)
        a = np.asarray(c, np.float32)
        gris = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        a = a * sat + gris[..., None] * (1 - sat)
        a = a * lerp(1.0, 0.85, u)
        c = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        # borde blanco y esquinas redondeadas cuando ya es tarjeta
        rad = int(lerp(0, 22, u)); bw = int(round(lerp(0, 5, u)))
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=rad, fill=255)
        x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
        if bw:
            b = Image.new('L', (w + 2 * bw, h + 2 * bw), 0)
            ImageDraw.Draw(b).rounded_rectangle([0, 0, w + 2 * bw - 1, h + 2 * bw - 1], radius=rad + bw, fill=255)
            im.paste((255, 255, 255), (x0 - bw, y0 - bw), b)
        im.paste(c, (x0, y0), m)
        return im


def render(contenido, salida_dir):
    """renderiza c450–c479 a PNG (para la animática) y devuelve la lista de rutas."""
    M = Mapa()
    out = []
    Path(salida_dir).mkdir(parents=True, exist_ok=True)
    for n in range(N0, N_FIN):
        f = M.cuadro(n, contenido)
        p = Path(salida_dir) / f'mapa_c{n}.png'
        Image.fromarray(f).save(p); out.append(p)
    info = dict(destino_mercator=[round(float(v), 3) for v in M.dest], origen=FLORIDA, negro_rgb=M.negro,
                escalas=dict(florida=S_F, medio=S_MED, llegada=S_B), cuadros=[N0, N_FIN - 1])
    guardar_json(info, Path(salida_dir) / 'mapa.json')
    return out, M


if __name__ == '__main__':
    # prueba: render con un cuadro gris de contenido
    cont = np.full((H, W, 3), 110, np.uint8)
    out, M = render(cont, T / 'mapa_prueba')
    print(len(out), M.dest, M.negro)
