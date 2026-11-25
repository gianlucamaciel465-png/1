#!/usr/bin/env python3
"""BOC-25 P5 «Antes del parche» · receta v01 (25/11/2026) · máster para revisión privada de Gianluca (no se publica).

Guion: piezas/BOC-25_octavos_hoy/guiones/P5_G1_fede.md con la aprobación de Roma (P5_G1_roma.md: hook, tomas de cierre y CTA).
Mecánica de casa de apuestas: la apuesta (Boca puede quedar afuera hoy) abre en c0, pistas a favor y en contra hasta c294,
giro en c294–c384 (el parche «se despega» en reversa: «Todo parche tiene un antes.» / «Hoy es ese antes.»), la prenda
cobra la palabra «parche» (ROCCÉ en denim de la espalda) y el partido queda abierto hasta las 21:00.

Tiempos de los clips de terceros: los segundos del guion salieron de las tiras de 8 cuadros, que tienen el tiempo impreso
corrido (la tira se hizo con -ss = paso/2 y el sello de tiempo arranca en 0). Acá cada tramo se ubicó por su contenido en
la fuente, cuadro a cuadro (ver 06_pedro_P5.md, tabla de correcciones).

Clips (TikTok @sudamericana, © CONMEBOL, material de terceros sin licencia; marca de agua sin tocar):
  227090 = 7710811901336227090 (parches, sombrero)   629831 = 7710815379563629831 (chapa y bocha de la copa)
  622854 = 7711539134128622854 (tribuna)              293202 = 7710804759703293202 (hincha con el parche)
  767624 = 7710808462346767624 (parche en el pecho blanco, en reversa)
Tomas propias: IMG_3453, IMG_4625, IMG_7824 (biblioteca SDR TRABAJO/bocsud/lib) e IMG_4530 rehecha desde el original con
el mezclador de Roma después del tonemap (colorchannelmixer=rr=1.05:gg=1.03:bb=0.92).

Etapas: python p5.py planos | audio | master | control | todo     (python = TRABAJO/boc25/p5/py/bin/python: necesita scipy)
"""
import sys, json, subprocess, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, '/home/user/1/scripts/bocsud')
import comun as C
V = C.V

T = Path('/home/user/1/TRABAJO/boc25/p5')
CLIPS = Path('/home/user/1/TRABAJO/boc25/clips')
FPS, W, H = 30, 1080, 1920
NF = 680                                   # 22,667 s (tramo 13 ajustado: ver informe)
AZUL = (11, 22, 38)                        # #0B1626 azul noche
WY, WW, WH = 640, 1080, 810                # ventana 4:3 de los tramos 1–8 (y 640–1450)
PIEZA = Path('/mnt/project-files/piezas/BOC-25_octavos_hoy')
SALIDA = PIEZA / 'ROCCE_BOC25_P5_ANTES_DEL_PARCHE_v01.mp4'

ID = dict(sombrero='7710811901336227090', chapa='7710815379563629831', tribuna='7711539134128622854',
          hincha='7710804759703293202', pecho='7710808462346767624')


def clip(nombre):
    return sorted(CLIPS.glob(f'*_{ID[nombre]}.mp4'))[0]


def tam(src):
    return [int(v) for v in C.sh(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                  '-of', 'csv=p=0', str(src)]).strip().split(',')[:2]]


# ---------------- tramo 7: recorrido de la ventana sobre el pecho blanco (medido cuadro a cuadro en la fuente) ----------------
# borde izquierdo L (px de la fuente) por tiempo de la fuente: siempre a la derecha de la pipa de Nike (borde derecho
# medido + ≥ 12 px) y a la izquierda del parche cuando ya está pegado. Borde de arriba T: y 995 mientras el parche está en
# el pecho (mentón ≤ 990, camisetas con «betsson» del fondo en y ≤ 980) y baja a y 1066 entre 20,0 y 19,5 s, cuando se
# agacha (anteojos y mentón hasta y 1044 en 18,9–19,5 s; la cara del chico de negro termina en y ≈ 1020).
# Ancho 520 (alto 390): L + 520 ≤ 1080 en todo el recorrido.
L7 = [(18.90, 455), (19.10, 475), (19.30, 478), (19.70, 492), (20.10, 506), (20.30, 510), (20.50, 518), (20.90, 535),
      (21.10, 542), (21.30, 556), (21.50, 559), (21.70, 560), (22.10, 560)]
W7 = 520
T7_0, T7_N = 18.90, 97                     # se leen 97 cuadros desde 18,90 s; la reversa toma 96, 94, …, 2


def l7(ts):
    xs, ys = zip(*L7)
    return float(np.interp(ts, xs, ys))


def t7(ts):
    return 995 + 71 * C.suave((20.0 - ts) / 0.5)


def ventana(nombre, t0, n_leer, salida, rect, orden=None, por_cuadro=None, cuadros=None):
    """Plano de ventana: fondo azul noche y, en y=WY, el recorte 4:3 rect(k, i) -> (x, y, w) (px de la fuente) del cuadro i
    de la fuente (leída desde t0 a 30 fps), escalado a 1080×810. orden: cuadro de la fuente para cada cuadro de salida."""
    src = clip(nombre)
    sw, sh_ = tam(src)
    if cuadros is None:
        cuadros = C.leer_video(src, t0, n_leer / FPS, sw, sh_)
    orden = list(range(n_leer)) if orden is None else orden
    enc = C.encoder(salida)
    rects = []
    for k, i in enumerate(orden):
        x, y, w = rect(k, i); h = w * 3 / 4
        assert x >= 0 and y >= 0 and x + w <= sw + 1e-6 and y + h <= sh_ + 1e-6, (nombre, k, x, y, w)
        im = Image.fromarray(cuadros[i]).resize((WW, WH), Image.LANCZOS, box=(x, y, x + w, y + h))
        fr = Image.new('RGB', (W, H), AZUL); fr.paste(im, (0, WY))
        if por_cuadro:
            fr = por_cuadro(k, fr)
        enc.stdin.write(np.asarray(fr, np.uint8).tobytes())
        rects.append([round(x, 1), round(y, 1), round(w, 1), round(h, 1)])
    enc.stdin.close(); enc.wait()
    return dict(clip=ID[nombre], desde=t0, cuadros=len(orden), orden=orden, salida=str(salida), ventanas=rects)


_GRAD = {}


def degrade(yc, s=240, k=0.45):
    """oscurece suave una franja horizontal centrada en yc: apoyo para texto blanco sobre cielo, espuma o mar"""
    if (yc, s, k) not in _GRAD:
        y = np.arange(H, dtype=np.float32)
        _GRAD[(yc, s, k)] = (1 - k * np.exp(-((y - yc) / s) ** 2))[:, None, None]
    g = _GRAD[(yc, s, k)]
    return lambda kk, f: Image.fromarray((np.asarray(f, np.float32) * g).round().clip(0, 255).astype(np.uint8))


def plano_4530(salida):
    """IMG_4530 0,50–3,10 desde el original: cadena HLG→SDR de CLAUDE.md + mezclador de Roma (en lugar de las ganancias
    de la biblioteca). Blanco medido: B−R +2,7, G−R −1,1 (biblioteca: +10,6 / +2,2; foto de producto en el mismo balcón:
    +6,2 / −1,9; estudio: +1,0 / +0,9)."""
    V.TOMAS['IMG_4530'] = dict(hdr=True, nat=(1080, 1920), g=None, extra='colorchannelmixer=rr=1.05:gg=1.03:bb=0.92')
    tmp = T / 'tmp_4530.mp4'
    V.plano('IMG_4530', 0.50, 3.10, tmp)
    # degradé del CTA sobre el cielo, por cuadro
    g = degrade(400, 230, 0.42)
    n = int(C.sh(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames',
                  '-of', 'csv=p=0', str(tmp)]).strip())
    a = C.leer_video(tmp, 0, n / FPS, W, H)
    enc = C.encoder(salida)
    for k, f in enumerate(a):
        enc.stdin.write(np.asarray(g(k, Image.fromarray(f)), np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    return dict(toma='IMG_4530', desde=0.50, hasta=3.10, cuadros=len(a), salida=str(salida),
                color='HLG→SDR (zscale+mobius) + colorchannelmixer=rr=1.05:gg=1.03:bb=0.92')


def planos():
    P = []
    # T1 c0–c65 APUESTA: el dedo presiona el parche dorado (sombrero). Ventana x 300–900, y 1005–1455: debajo del mentón
    # (y ≤ 960 cuando mira para abajo; la cara levantada en 67,45 s queda en y 600–900) y ≥ 45 px arriba de las letras
    # de «betsson» (empiezan en y ≈ 1500). La marca de agua (x 60–285, y 240–400) queda afuera: crédito.
    P.append(ventana('sombrero', 65.40, 66, T / 't01.mp4', lambda k, i: (300, 1005, 600)))
    # T2 c66–c113 PISTA a favor: las manos llevan la chapa «2026 Club Atlético Boca Juniors» a la base (plano general de
    # 5,57–8,60 s); asienta en ≈ 8,40 s (c111). Fuente 720×1280: ventana de ancho completo, y 620–1160.
    P.append(ventana('chapa', 6.95, 48, T / 't02.mp4', lambda k, i: (0, 620, 720)))
    # T3 c114–c155 PISTA en contra: tribuna alta. Ventana 1:1 (sin ampliar) en y 225–1035 con la marca de agua adentro
    # (sin crédito); afuera quedan los carteles de arriba (y < 60) y las vallas y carteles LED de abajo (y > 1650).
    P.append(ventana('tribuna', 0.00, 42, T / 't03.mp4', lambda k, i: (0, 225, 1080)))
    # T4 c156–c202 SUBE: el mismo plano continuo (1,40 s en adelante) con salto de escala a 1,25 sobre la hinchada (sin
    # marca de agua: crédito). +5 cuadros respecto del guion (la bocha de T5 dura 1,33 s en la fuente).
    P.append(ventana('tribuna', 1.40, 47, T / 't04.mp4', lambda k, i: (108, 430, 864)))
    # T5 c203–c242: la bocha de la copa con el anillo SUDAMERICANA: el plano entero (cuadros 336–375 de la fuente a 29,97 fps,
    # 11,211–12,513 s; cortes medidos por diferencia entre cuadros), y 430–970.
    P.append(ventana('chapa', 11.205, 40, T / 't05.mp4', lambda k, i: (0, 430, 720)))
    # T6 c243–c293: un hincha recibe el parche y lo sostiene entre los dedos, todavía fuera del pecho (10,15–11,85 s).
    # Ventana x 60–1020, y 960–1680: debajo de la barba (baja hasta y 932 en 11,83 s, cuando mira el parche) y de las
    # camisetas con «betsson» de atrás (y < 500, y la franja de la izquierda en y 700–800).
    P.append(ventana('hincha', 10.15, 51, T / 't06.mp4', lambda k, i: (60, 960, 960)))
    # T7 c294–c341 GIRO 1/2: 22,10 → 18,97 s en reversa, un cuadro de cada dos (sin interpolar): el parche se despega del
    # pecho y vuelve a la mano. La ventana acompaña el pecho (ver L7).
    src7 = clip('pecho'); sw, sh_ = tam(src7)
    cu7 = C.leer_video(src7, T7_0, T7_N / FPS, sw, sh_)
    orden7 = [96 - 2 * k for k in range(48)]
    r7 = lambda k, i: (l7(T7_0 + i / FPS), t7(T7_0 + i / FPS), W7)
    P.append(ventana('pecho', T7_0, T7_N, T / 't07.mp4', r7, orden=orden7, cuadros=cu7))
    # T8 c342–c383 GIRO 2/2: el último cuadro de T7 (18,967 s, pecho sin parche: el parche está en la mano) retenido, con
    # acercamiento 1,00 → 1,08 anclado en el pecho vacío, entre el escudo y la mano con el parche (x 610, y 1215 de la
    # fuente): ese punto queda quieto en pantalla y los bordes de la ventana solo se cierran (la pipa y la cara siguen afuera).
    x0, y0, w0 = r7(47, 2); ax, ay = 610.0, 1215.0
    def r8(k, i):
        z = 1 + 0.08 * C.suave(k / 41)
        return (ax - (ax - x0) / z, ay - (ay - y0) / z, w0 / z)
    P.append(ventana('pecho', T7_0, T7_N, T / 't08.mp4', r8, orden=[2] * 42, cuadros=cu7))
    del cu7
    # T9–T10 c384–c467: IMG_3453 0,20–3,00 continuo (los dedos recorren el estampado; desde ≈ 2,3 s ya sin dedos).
    P.append(C.propia('IMG_3453', 0.20, 3.00, T / 't09.mp4'))
    # T11 c468–c521: IMG_4625 1,50–3,30 (Blanca de espaldas sobre la roca, entera en cuadro) con acercamiento 1,00 → 1,20
    # hacia ROCCÉ en denim (centro x 0,43, y 0,44): el borde claro del parche de denim se ve (pespunte: ver informe).
    p, a = C.lib('IMG_4625')
    P.append(dict(C.video_cubrir(p, 1.50 - a, 1.80, T / 't11.mp4', cx=0.43, cy=0.44, src_size=(W, H),
                                 zf=lambda k: 1 + 0.20 * C.suave(k / 53), por_cuadro=degrade(470, 230, 0.42)),
                  toma='IMG_4625', desde=1.50, hasta=3.30, z=(1.0, 1.2)))
    # T12 c522–c601: IMG_7824. La Negra está entera, quieta y cerca solo en 6,15–7,35 s (antes de 6,1 la «F» de Founders
    # se sale por la izquierda; después de 7,4 se aleja y «Privée» se dobla con la manga): 6,15–7,15 (30 cuadros) con
    # «Founders Privée: del 001 al 100.» y, en el cambio de texto, 2,00–3,67 (50 cuadros, entera, con la playa detrás).
    P.append(dict(C.propia('IMG_7824', 6.15, 7.15, T / 't12a.mp4', por_cuadro=degrade(300, 170, 0.45)), toma='IMG_7824'))
    P.append(dict(C.propia('IMG_7824', 2.00, 3.6667, T / 't12b.mp4', por_cuadro=degrade(420, 220, 0.42)), toma='IMG_7824'))
    # T13 c602–c679 CTA: IMG_4530 0,50–3,10 (estampado completo y grande en todo el tramo; 7824 no tiene otro tramo
    # completo que no se haya usado: ver informe).
    P.append(plano_4530(T / 't13.mp4'))
    n = C.armar(P, T / 'p5_video.mp4')
    assert n == NF, n
    for p_ in P:
        p_.pop('orden', None)
    json.dump(P, open(T / 'planos.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print('cuadros', n)


# ---------------- textos ----------------
def tx(c):
    """tiempo de un cuadro para los textos: 4 ms antes, así el redondeo a centésimas del .ass no lo corre un cuadro"""
    return max(c / FPS - 0.004, 0.0)


CEL = '{\\c&H00E8C8A9&}'                   # celeste #A9C8E8 (solo sobre azul noche)
BLA = '{\\c&H00FFFFFF&}'
# Tamaños. En libass el Fontsize del .ass no es el cuerpo de la letra: con Inter Display el cuerpo (em) sale a 0,822 del
# Fontsize (medido el 25/11: Fontsize 100 → mayúscula de 60 px; Pillow a 100 px → 73 px; 60/73 = 0,822). v01 usaba
# Fontsize 72–80 (cuerpo ≈ 59–66 px). v02 (corrección de Roma): cuerpo 82 px el hook, 76 px el resto, CTA 72 + 84 px.
EM = 0.822
def fs(em):
    """Fontsize del .ass para un cuerpo de `em` px"""
    return round(em / EM)


def _est(fsz, sombra):
    return ('Inter Display ExtraBold', fsz, '&H00FFFFFF', '&H00000000', '&H78000000' if sombra else '&H00000000',
            0, 0, 3 if sombra else 0, 1, 2, 0)


V.ESTILOS.update({
    # v01 (Fontsize del .ass)
    'P5': _est(76, False), 'P5h': _est(72, False), 'P5s': _est(76, True), 'P5s68': _est(68, True),
    'P5cta': _est(80, True), 'P5cta2': _est(70, True),
    # v02 (cuerpo en px → Fontsize): misma sombra que en v01
    'P5h2': _est(fs(82), False),          # hook: 100
    'P5b2': _est(fs(76), False),          # pistas y giro sobre azul noche: 92
    'P5s2': _est(fs(76), True),           # tramos 9–12 sobre la imagen: 92
    'P5c1': _est(fs(72), True),           # «¿Hoy jugás tu octavo?»: 88
    'P5c2': _est(fs(84), True),           # «Seguinos antes del parche.»: 102 (la acción es lo más grande)
    'P5rot': ('Inter Display SemiBold', 34, '&H33FFFFFF', '&H00000000', '&H00000000', 0, 0, 0, 1, 8, 0),
    'P5cred': ('Inter Display Medium', 24, '&H30FFFFFF', '&H00000000', '&H90000000', 0, 0, 1.5, 1, 1, 0),
})
YB = 605                                    # base de los textos sobre la ventana (v01)
VERSION = 'v02'


def textos(version=VERSION):
    """capa de textos. y = borde de abajo de la caja (alineación 2). En v02 todo renglón entra en 1080 − 2×70 = 940 px
    (medido con Pillow al cuerpo pedido); el único que no entra es «Seguinos antes del parche.» (1069 px a 84): va en dos.
    Tramos 1–8: todo queda por encima de la ventana (y 640) con ≥ 30 px de aire."""
    X = []
    def t(a, b, txt, y=YB, est='P5', **kw):
        X.append(dict(t0=tx(a), t1=tx(b), txt=txt, estilo=est, y=y, blur=False, **kw))
    v2 = version == 'v02'
    H, B, S = ('P5h2', 'P5b2', 'P5s2') if v2 else ('P5h', 'P5', 'P5s')
    # T1 apuesta
    t(0, 66, 'Hoy Boca puede\\Nquedar afuera.', y=381 if v2 else 402, est=H)
    t(33, 66, f'Y el {CEL}parche{BLA} del sábado\\Nno juega.', y=608 if v2 else YB, est=H)
    # pistas
    t(66, 114, 'Hace 4 días ganó\\Nla Sudamericana.', est=B)
    t(114, 156, 'Hoy: partido único.', est=B)
    t(156, 203, 'Empate: alargue\\Ny penales.', est=B)
    t(203, 243, 'Si gana, no le dan nada.', est=B)
    t(243, 270, 'Domingo: cuartos\\Ncon Gimnasia.', est=B)
    t(270, 294, 'Tampoco hay parche.', est=B)
    # giro
    t(294, 342, f'Todo {CEL}parche{BLA} tiene\\Nun {CEL}antes{BLA}.', est=B)
    t(342, 384, f'Hoy es ese {CEL}antes{BLA}.', est=B)
    # rótulo fijo y créditos (ventana sin la marca de agua: todos menos T3): sin cambios en v02
    X.append(dict(t0=tx(0), t1=tx(384), txt='Boca vs. Independiente Rivadavia · hoy 21:00', estilo='P5rot', y=1474, blur=False))
    for a, b in ((0, 114), (156, 384)):
        X.append(dict(t0=tx(a), t1=tx(b), txt='Video: @sudamericana', estilo='P5cred', x=22, y=WY + WH - 14, blur=False))
    # Roccé
    t(384, 438, 'El pecho del antes:', y=470, est=S)
    t(468, 522, 'Este parche\\Nse lleva antes.', y=575, est=S)
    t(522, 552, 'Founders Privée:\\Ndel 001 al 100.', y=385, est=S if v2 else 'P5s68')
    t(552, 602, 'Los de antes\\Ndel parche.', y=535, est=S)
    # CTA
    if v2:
        t(602, NF, '¿Hoy jugás tu octavo?', y=357, est='P5c1')
        t(617, NF, 'Seguinos antes\\Ndel parche.', y=570, est='P5c2')
    else:
        t(602, NF, '¿Hoy jugás tu octavo?', y=420, est='P5cta')
        t(617, NF, 'Seguinos antes del parche.', y=530, est='P5cta2')
    return X


# ---------------- sonido ----------------
class Mezcla(C.MezclaB):
    def real(self, path, src0, t0, t1, g_db=0.0, hp=None, lp=None, ini=0.01, fin=0.01, pista='amb', etiqueta=None):
        """igual que MezclaB.real, pero filtra a lo largo del tiempo. En comun.py `filt(seg.T, …).T` filtra con axis=0
        sobre (2, n), es decir entre los dos canales, y deja el tramo en −65 a −95 dB (medido el 25/11 en p5)."""
        a = self.leer_archivo(path)
        n = int(round((t1 - t0) * C.SR)); s0 = int(round(src0 * C.SR))
        seg = a[s0:s0 + n].copy()
        if len(seg) < n:
            seg = np.concatenate([seg, np.zeros((n - len(seg), 2))])
        if hp: seg = C.filt(seg, 'high', hp)          # (n, 2), axis=0 = tiempo
        if lp: seg = C.filt(seg, 'low', lp)
        r = np.ones(n); k1 = int(ini * C.SR); k2 = int(fin * C.SR)
        if k1: r[:k1] = np.linspace(0, 1, k1)
        if k2: r[-k2:] = np.minimum(r[-k2:], np.linspace(1, 0, k2))
        self.put(pista, seg * r[:, None] * C.db(g_db), t0)
        self.log(t0, f'audio real {etiqueta or Path(path).name} fuente {src0:.2f}–{src0 + t1 - t0:.2f} s, {g_db:+.1f} dB'
                     + (f', pasaaltos {hp} Hz' if hp else '') + (f', pasabajos {lp} Hz' if lp else ''))

    def toque(self, t, g=0.2, f=2400):
        """tic de sonido.py a 0,6 de la ganancia pedida: a ganancia plena el limitador lo recortaba 3–5 dB"""
        super().toque(t, g * 0.6, f)

    def clic_metal(self, t, g=0.3):
        """clic metálico chico (la chapa que asienta): parciales agudos inarmónicos con caída de 25–60 ms"""
        L = int(0.25 * C.SR); tt = np.arange(L) / C.SR
        s = np.zeros(L)
        for f, a, d in ((2730, 1.0, 0.06), (4110, 0.7, 0.04), (5930, 0.5, 0.03), (7420, 0.3, 0.02)):
            s += a * np.sin(2 * np.pi * f * tt) * np.exp(-tt / d)
        s += 0.6 * C.filt(C.ruido(L), 'high', 3000) * np.exp(-tt / 0.003)
        self.put('fx', s / np.abs(s).max(), t, g); self.rev(s / np.abs(s).max() * g * 0.15, t, seg=0.8)
        self.log(t, 'clic metálico')

    def rebobinado(self, path, src0, src1, t0, g_db):
        """audio real de src0–src1 al revés y al doble de velocidad (rebobinado): las palabras no se entienden"""
        from scipy.signal import resample_poly
        a = self.leer_archivo(path)
        seg = a[int(src0 * C.SR):int(src1 * C.SR)][::-1]
        seg = resample_poly(seg, 1, 2, axis=0)
        n = len(seg); r = np.ones(n); k = int(0.02 * C.SR); r[:k] = np.linspace(0, 1, k); r[-k:] = np.linspace(1, 0, k)
        self.put('amb', seg * r[:, None] * C.db(g_db), t0)
        self.log(t0, f'rebobinado {Path(path).name} {src1:.2f}→{src0:.2f} s a 2×, {g_db:+.1f} dB')


def s(c):
    return c / FPS


def audio():
    DUR = NF / FPS
    m = Mezcla(DUR)
    TRIB, PECHO = clip('tribuna'), clip('pecho')
    # tribuna real (clip 622854, «sonido original»): energía en 400–1000 Hz, sin graves de música (50–150 Hz 15–25 dB debajo),
    # planitud 0,5–0,7, sin picos tonales sostenidos. No se escuchó: para que ninguna palabra del canto se entienda, pasa
    # siempre por un pasabajos (≤ 700 Hz: quita consonantes y segundo formante).
    m.real(TRIB, 9.00, s(0), s(114), -11, hp=90, lp=500, ini=0.04, fin=0.25, etiqueta='tribuna lejana (pasabajos 500 Hz)')
    m.golpe_sordo(s(0), 0.32)                                   # c0 golpe seco grave (a 0,65 el limitador lo recortaba 7,6 dB)
    m.toque(s(33), 0.22, 2000); m.log(s(33), 'tic')              # c33 tic
    m.toque(s(66), 0.22, 2000); m.log(s(66), 'tic')
    m.clic_metal(s(108), 0.32)                                   # la chapa toca la base en c108 (8,37 s de la fuente)
    # c114–c202: el canto de la tribuna sincronizado con su imagen (misma fuente, mismos segundos)
    m.real(TRIB, 0.00, s(114), s(156), -7, hp=110, lp=700, ini=0.12, fin=0.02, etiqueta='canto de tribuna (pasabajos 700 Hz)')
    m.real(TRIB, 1.40, s(156), s(203), -4, hp=110, lp=700, ini=0.02, fin=0.02, etiqueta='canto de tribuna +3 dB')
    m.real(TRIB, 2.97, s(203), s(243), -10, hp=110, lp=700, ini=0.02, fin=0.08, etiqueta='canto de tribuna −6 dB')
    # c243–c294: la misma tribuna sigue, lejana (pasabajos 500 Hz, −6 dB más), debajo de los tics y la subida; sin ella el
    # tramo 6 caía a −40 dB RMS (un hueco antes del giro). Se apaga al entrar el rebobinado.
    m.real(TRIB, 4.30, s(243), s(294), -16, hp=90, lp=500, ini=0.08, fin=0.12, etiqueta='tribuna lejana bajo la subida')
    m.toque(s(114), 0.18, 2000); m.toque(s(156), 0.22, 2000); m.toque(s(203), 0.2, 2000)
    m.subida(s(203), s(342), 0.2)                                 # subida hasta el giro
    m.toque(s(243), 0.22, 2000); m.toque(s(270), 0.24, 2000)
    m.log(s(243), 'tic'); m.log(s(270), 'tic')
    # c294 rebobinado: barrido invertido + el audio real del clip del pecho al revés (22,10 → 18,90 s a 2×)
    m.barrido(s(294) + 0.2, 0.4, 0.28, sube=False)
    m.rebobinado(PECHO, 18.90, 22.10, s(294), -9)
    # c342 corte a casi silencio + golpe grave; silencio hasta c384
    for p in ('amb', 'fx', 'mus', 'bombo'):
        m.silenciar(p, s(342) - 0.004, DUR + 1, rampa=0.004)
    m.impacto(s(342), 0.25)                                       # a 0,6 el limitador lo recortaba 10 dB
    # Roccé
    m.tela(s(386), 0.55, 0.30); m.tela(s(402), 0.45, 0.22)     # roce de los dedos sobre el estampado
    # c416–c468 «ambiente suave» (tramo 10): el mar de 4625 entra bajo la macro y anticipa la ola del tramo 11
    m.toma('IMG_4625', 0.00, s(416), s(468), -13, ini=0.45, fin=0.10)
    m.toque(s(468), 0.14, 2000)
    m.toma('IMG_4625', 1.50, s(468), s(522), -2, ini=0.10, fin=0.04)            # mar real de la toma
    m.toma('IMG_7824', 6.15, s(522), s(552), -9, hp=150, ini=0.03, fin=0.02)     # viento real del balcón
    m.toma('IMG_7824', 2.00, s(552), s(602), -9, hp=150, ini=0.02, fin=0.04)
    m.toque(s(522), 0.14, 2000); m.toque(s(552), 0.14, 2000)
    m.toma('IMG_4530', 0.50, s(602), DUR, 3, hp=150, ini=0.04, fin=0.02)         # balcón frente a la playa (ráfaga de viento
    #                                                                     en 1,13–1,33 s de la fuente, 60–150 Hz: pasaaltos 150)
    m.toque(s(602), 0.18, 2000); m.toque(s(617), 0.16, 2000)
    for p in ('amb', 'fx', 'mus', 'bombo'):
        m.fundido(p, DUR - 12 / FPS, DUR)                         # fundido en los últimos 12 cuadros
    (T / 'audio').mkdir(exist_ok=True)
    r = m.exportar(str(T / 'audio' / 'p5.wav'), lufs=-14)
    print('audio', r)


def master_path(version=VERSION):
    return T / 'borrador' / ('p5_master.mp4' if version == 'v01' else f'p5_master_{version}.mp4')


def master(version=VERSION):
    a = V.ass(textos(version), T / ('p5.ass' if version == 'v01' else f'p5_{version}.ass'))
    T.joinpath('borrador').mkdir(exist_ok=True)
    V.master(T / 'p5_video.mp4', T / 'audio' / 'p5.wav', master_path(version), ass_path=a)
    print(master_path(version))


CORTES = [66, 114, 156, 203, 243, 294, 342, 384, 468, 522, 552, 602]


def control(version=VERSION):
    """cuadros de control del máster en TRABAJO/boc25/p5/control (después se copian a PIEZA/control):
    inicio, final, los dos lados de cada corte, giro (c342), CTA (c640) y hoja cada 0,5 s con el cuadro impreso."""
    import subprocess as sp
    M = master_path(version); D = T / ('control' if version == 'v01' else f'control_{version}'); D.mkdir(exist_ok=True)
    pre = 'P5_' if version == 'v01' else f'P5_{version}_'
    ns = sorted({0, NF - 1} | {c for k in CORTES for c in (k - 1, k)})
    sel = '+'.join(f'eq(n\\,{n})' for n in ns)
    sp.run(['ffmpeg', '-v', 'error', '-y', '-i', str(M), '-vf', f"select='{sel}'", '-fps_mode', 'vfr', '-q:v', '2',
            str(D / 'tmp_%03d.jpg')], check=True)
    for i, n in enumerate(ns):
        (D / f'tmp_{i + 1:03d}.jpg').rename(D / f'{pre}c{n:03d}.jpg')
    for n, nombre in ((342, f'{pre}giro_c342.jpg'), (640, f'{pre}cta_c640.jpg')):
        sp.run(['ffmpeg', '-v', 'error', '-y', '-i', str(M), '-vf', f"select='eq(n\\,{n})'", '-frames:v', '1',
                '-fps_mode', 'vfr', '-q:v', '2', str(D / nombre)], check=True)
    sp.run(['ffmpeg', '-v', 'error', '-y', '-i', str(M), '-vf',
            "select='not(mod(n\\,15))',scale=270:-2,drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-Bold.otf:"
            "text='%{pts\\:hms} c%{eif\\:t*30\\:d}':x=4:y=4:fontsize=17:fontcolor=yellow:box=1:boxcolor=black@0.6,"
            "tile=8x6:padding=3", '-frames:v', '1', '-fps_mode', 'vfr', '-q:v', '2', str(D / f'{pre}hoja_contacto_0.5s.jpg')],
           check=True)
    print(len(list(D.glob(f'{pre}*.jpg'))), 'archivos en', D)


if __name__ == '__main__':
    T.mkdir(parents=True, exist_ok=True)
    et = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    if et in ('planos', 'todo'): planos()
    if et in ('audio', 'todo'): audio()
    if et in ('master', 'todo'): master()
    if et in ('control', 'todo'): control()
