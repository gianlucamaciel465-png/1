#!/usr/bin/env python3
"""MARCA · Historias para Destacadas H1 «ROCCÉ», H2 «FOUNDERS», H3 «TU CASI» · receta de los másteres v01 (Pedro C,
25/11/2026).

Guion: piezas/MARCA_comunidad/04_fede_guiones_G1.md §«Historias para Destacadas» + 06_roma_aprobacion_G1.md
+ 05_especificacion_comun.md. 1080×1920, 30 fps, 12,000 s (360 cuadros), H.264 High 4.0 / AAC-LC, −14 LUFS, música TEMP
baja en el pulso (120 BPM: todos los cortes en 2,0 / 5,5 / 7,0 / 8,5 / 9,5 s caen en el pulso). La zona y 1150–1450 del
último plano queda limpia para el sticker (se agrega al publicar; acá solo la guía en PNG). Sin fechas, sin link.

Reutiliza (importa, no modifica) scripts/marca/mc05.py: Capa (rasterizado por cuadro), placa_serif, neutralización de la
Blanca, Negra carbón de 3453, mezcla, máster con capa, ficha y entrega; y scripts/marca/comun.py tal cual.

Etapas (python historias.py <etapa> [H1,H2,H3]):  planos → capas → audio → master → control → guias → entregar
Intermedios en TRABAJO/marca/HIST/<H>/.
"""
import json, math, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, '/home/user/1/scripts/marca')
import mc05 as M           # noqa: E402
from mc05 import V, U, C, F4, nice, jdump   # noqa: E402

R = Path('/home/user/1')
T = R / 'TRABAJO/marca/HIST'
EXP = R / 'EXPORTACIONES'
PIEZA = Path('/mnt/project-files/piezas/MARCA_comunidad/HISTORIAS')
W, H, FPS, SR = 1080, 1920, 30, 48000
NF = 360
DUR = NF / FPS
EVID = T / 'evidencia_v02'
VERSION = 'v02'      # v02 = dictamen de Roma 02_roma_dictamen_v01.md (receta exacta de v01: historias_v01.py)
# Blanca de H3 (v02): regiones de tela blanca medidas sobre la remera (fracciones del cuadro)
M.REG_BLANCA.update({'IMG_7884': (0.40, 0.70, 0.15, 0.75), 'IMG_4627': (0.55, 0.90, 0.05, 0.70)})

# (id, toma, desde, hasta, modo, cuadros congelados al final, función)
HIST = {
    'H1': dict(
        nombre='ROCCE_H01_ROCCE_v02.mp4', guia='ROCCE_H01_ROCCE_guia_sticker_v02.png',
        sticker=('Sticker de pregunta', ['Preguntame lo que quieras de Roccé'], None),
        planos=[('P1', 'IMG_4530', 0.50, 2.50, 'color', 0, 'APUESTA'),
                # 3453 decodifica 140 cuadros (0–4,633 s): 0,00–4,667 + 10 congelados (0,333 s) en vez de 4,70 + 0,30
                ('P2', 'IMG_3453', 0.00, 140 / 30, 'negra', 10, 'PISTAS'),
                ('P3', 'IMG_7887', 0.00, 2.50, 'neutra', 0, 'RESOLUCIÓN'),
                # 7894 tiene 74 cuadros (2,467 s): 0,00–2,467 + 1 cuadro clonado (0,033 s) para cerrar en 12,000 s
                ('P4', 'IMG_7894', 0.00, 74 / 30, 'neutra', 1, 'CTA')],
        cortes=[60, 210, 285]),
    'H2': dict(
        nombre='ROCCE_H02_FOUNDERS_v02.mp4', guia='ROCCE_H02_FOUNDERS_guia_sticker_v02.png',
        sticker=('Sticker de encuesta', ['¿Qué preferís ser?'], ['001', '100']),
        planos=[('P1', 'IMG_7824', 0.00, 2.00, 'color', 0, 'APUESTA'),
                ('P2', 'IMG_8004', 1.50, 5.00, 'neutra', 0, 'EVIDENCIA'),
                ('P3', 'IMG_7824', 5.80, 8.80, 'color', 0, 'GIRO'),
                ('P4', 'IMG_7896', 1.00, 4.50, 'neutra_z', 0, 'CTA')],
        cortes=[60, 165, 255]),
    'H3': dict(
        nombre='ROCCE_H03_TU_CASI_v02.mp4', guia='ROCCE_H03_TU_CASI_guia_sticker_v02.png',
        sticker=('Sticker de pregunta', ['Contame tu casi en una línea'], None),
        # v02: Blanca neutralizada (v01 medía B−R +10,4…+12,0 en 7884 y +8,9…+11,9 en 4627; dictamen: ≤ +8)
        planos=[('P1', 'IMG_7884', 3.00, 5.00, 'neutra_a', 0, 'APUESTA'),
                ('P2', 'IMG_4627', 2.50, 7.50, 'neutra_a', 0, 'EJEMPLOS'),
                ('P3', 'IMG_3453', 2.00, 4.50, 'negra', 0, 'RESOLUCIÓN'),
                # 7895 tiene 69 cuadros (0–2,267 s): 0,00–2,30 + 0,2 s congelado = 69 + 6 cuadros
                ('P4', 'IMG_7895', 0.00, 69 / 30, 'neutra', 6, 'CTA')],
        cortes=[60, 210, 285]),
}
ZONA_STICKER = (1150, 1450)


def sel(argv):
    return argv[2].split(',') if len(argv) > 2 else list(HIST)


def reg_salida(toma, modo):
    """región de tela blanca en el cuadro de salida: con z 1,30 apoyado abajo (7896) se pasa de la toma a la ventana."""
    y0, y1, x0, x1 = M.REG_BLANCA[toma]
    if modo != 'neutra_z':
        return (y0, y1, x0, x1)
    nw, nh = V.TOMAS[toma]['nat']; z = 1.30; wy, wx = nh / z, nw / z; oy, ox = nh - wy, nw / 2 - wx / 2
    return ((y0 * nh - oy) / wy, (y1 * nh - oy) / wy, (x0 * nw - ox) / wx, (x1 * nw - ox) / wx)


def pad_plano(src, pad, salida, nf):
    V.sh(nice(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', f'tpad=stop_mode=clone:stop={pad}', '-frames:v', str(nf + pad),
               *V.ENC_INT, salida]))


def ts_med(d, h):
    return [d + 0.25 * (h - d), d + 0.5 * (h - d), d + 0.75 * (h - d)]


def neutralizar_adapt(reg, br=5.6, gr=1.5, alfa=0.3, y0=140.0, y1=180.0, d0=5.0, d1=11.0, registro=None):
    """por_cuadro (v02, H3 7884 y 4627): mide el blanco de la remera EN CADA CUADRO (región reg, L > 150, sat < 0,15,
    como medir_blanca), calcula el corrimiento de croma que lo lleva a B−R = br, G−R = gr (mc05.delta_neutra), lo divide
    por el peso medio de esos píxeles (para que la MEDIA de la tela llegue al objetivo aunque los pliegues en sombra
    reciban menos corrección) y lo suaviza con media móvil (alfa). La corrección es la misma de mc05.neutralizar: solo
    claros (Y 140→180) y cercanos al croma del blanco (distancia 5→11): arena, rocas, piel y celeste quedan fuera.
    Se aplica con mc05.neutralizar_fino (redondeo con tramado fijo): con el redondeo simple, cada vez que el corrimiento
    cruzaba x,5 toda la tela saltaba 1 nivel de croma entre dos cuadros (primera pasada de v02, descartada).
    Objetivo 5,6 (no 8): el 4:2:0 del máster corre el celeste del estampado hacia el blanco vecino y la medición del
    control (rgb_plano, sobre el MP4) da hasta ≈ +2 más que la medición por cuadro en yuv444 (con 7,0 quedaban cuadros en +8,7; con 6,2, en +8,1)."""
    est = {}

    def ss(x):
        x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

    def f(k, o):
        h_, w_ = o.shape[1:]
        r0, r1, c0, c1 = int(reg[0] * h_), int(reg[1] * h_), int(reg[2] * w_), int(reg[3] * w_)
        Y = o[0, r0:r1:2, c0:c1:2].astype(np.float32); Cb = o[1, r0:r1:2, c0:c1:2].astype(np.float32)
        Cr = o[2, r0:r1:2, c0:c1:2].astype(np.float32)
        R = 1.164 * (Y - 16) + 1.793 * (Cr - 128); G = 1.164 * (Y - 16) - 0.213 * (Cb - 128) - 0.533 * (Cr - 128)
        B = 1.164 * (Y - 16) + 2.112 * (Cb - 128)
        rgb = np.clip(np.stack([R, G, B], -1), 0, 255)
        L = rgb.mean(-1); sat = (rgb.max(-1) - rgb.min(-1)) / (rgb.max(-1) + 1)
        m = (L > 150) & (sat < 0.15)
        if m.sum() >= 500:
            med = rgb[m].mean(0)
            (dcb, dcr), (cbm, crm) = M.delta_neutra(med, br, gr)
            wt = ss((Y - y0) / (y1 - y0)) * (1 - ss((np.hypot(Cb - cbm, Cr - crm) - d0) / (d1 - d0)))
            mw = float(max(wt[m].mean(), 0.5))
            v = np.array([dcb / mw, dcr / mw, cbm, crm])
            est['v'] = v if 'v' not in est else (1 - alfa) * est['v'] + alfa * v
            if registro is not None:
                registro.append(dict(k=k, medido_rgb=[round(float(x), 1) for x in med], b_r=round(float(med[2] - med[0]), 1),
                                     peso_medio=round(mw, 3), delta=[round(float(x), 2) for x in est['v'][:2]]))
        if 'v' not in est:
            return o
        dcb, dcr, cbm, crm = est['v']
        return M.neutralizar_fino((dcb, dcr), (cbm, crm), y0, y1, d0, d1)(k, o)
    return f


def etapa_planos():
    for hid in sel(sys.argv):
        cfg = HIST[hid]; carpeta = T / hid / 'planos'; carpeta.mkdir(parents=True, exist_ok=True)
        lista = []
        rehacer = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else None     # p. ej. «planos H1,H3 P2,P3»
        for pid, toma, d, h, modo, pad, fn in cfg['planos']:
            out = carpeta / f'{pid}_{toma}.mp4'
            js = out.with_suffix('.json')
            if rehacer is not None and pid not in rehacer and js.exists():
                lista.append(json.load(open(js))); print(hid, pid, 'reutilizado', flush=True); continue
            d0, h0 = d - 0.0005, h - 0.0005
            nw, nh = V.TOMAS[toma]['nat']
            if modo == 'color':
                p = V.plano(toma, d0, h0, out)
            elif modo == 'negra':
                p = M.plano_negra(toma, d0, h0, out, ts_med=[min(x, 4.5) for x in ts_med(d, h)], pad=pad, adapt=True)
                p['control_negra'] = {f'k{k}': M.tela_oscura(out, k, (0.55, 0.95, 0.0, 1.0)) for k in (10, p['cuadros'] - 1)}
                pad = 0
            elif modo == 'neutra_a':       # v02: neutralización adaptativa por cuadro (B−R ≤ +8 en todo el plano)
                ajustes = []
                p = F4.plano_zoom(toma, d0, h0, out, (0, 0, nw, nh), 1.0, 1.0, nw / 2, nh / 2,
                                  por_cuadro=neutralizar_adapt(M.REG_BLANCA[toma], registro=ajustes))
                p.pop('ventanas', None)
                p['neutra_adaptativa'] = dict(objetivo=dict(b_r=5.6, g_r=1.5), alfa=0.3, por_cuadro=ajustes)
                p['control_neutra'] = {f'k{k}': M.rgb_plano(out, k, M.REG_BLANCA[toma]) for k in (5, p['cuadros'] // 2, p['cuadros'] - 3)}
            elif modo in ('neutra', 'neutra_z'):
                tmp = out if not pad else carpeta / f'{pid}_{toma}_sinpad.mp4'
                tm = {'IMG_7887': [0.5, 1.0, 1.5], 'IMG_7896': [1.5, 2.75, 4.0]}.get(toma, ts_med(d, h))
                if modo == 'neutra_z':      # z 1,30 fijo, ventana apoyada abajo (guion)
                    z = 1.30
                    p = M.plano_neutro(toma, d0, h0, tmp, tm, z=z, cx=nw / 2, cy=nh - nh / z / 2)
                    p['ventana'] = dict(z=z, x=round(nw / 2 - nw / z / 2, 1), y=round(nh - nh / z, 1), w=round(nw / z, 1), h=round(nh / z, 1))
                else:
                    p = M.plano_neutro(toma, d0, h0, tmp, tm)
                p['control_neutra'] = {f'k{k}': M.rgb_plano(tmp, k, reg_salida(toma, modo)) for k in (5, p['cuadros'] // 2)}
            if pad:
                src = p['salida']
                if Path(src) == out:
                    shutil.move(out, carpeta / f'{pid}_{toma}_sinpad.mp4'); src = carpeta / f'{pid}_{toma}_sinpad.mp4'
                pad_plano(src, pad, out, p['cuadros'])
                p['cuadros'] += pad; p['salida'] = str(out); p['congelado_final'] = pad
            p.update(id=pid, modo=modo, funcion=fn)
            jdump(p, js)
            lista.append(p)
            print(hid, pid, toma, d, h, p['cuadros'], p.get('control_neutra', p.get('control_negra', '')), flush=True)
        n = V.unir(lista, T / hid / f'{hid}_base.mp4')
        assert n == NF, (hid, n)
        jdump(lista, T / hid / 'planos.json')


# =====================================================================================================
# textos
# =====================================================================================================
def degrade(y0, y1, amax=0.40):
    """franja oscura suave (CLAUDE.md: texto blanco sobre espuma o cielo) entre y0 e y1, máxima en el centro."""
    a = np.zeros((H, W), np.float32)
    yy = np.arange(H)
    c, r = (y0 + y1) / 2, (y1 - y0) / 2
    prof = np.clip(1 - np.abs(yy - c) / r, 0, 1)
    prof = prof * prof * (3 - 2 * prof)
    a[:] = (prof * amax * 255)[:, None]
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


def textos(hid, cp):
    caja = lambda t, s=76, tema='blanca': C.caja(t, s, tema=tema)
    pl = lambda t, s: C.placa(t, s)
    dato = lambda t, s: C.placa(t, s, peso='medium', halo=0.7)
    cneg = lambda t: C.caja(t, 50, tema='negra', peso='semibold')      # v02: datos en caja negra SemiBold 50
    if hid == 'H1':
        cp.texto('hook', '¿Quién está atrás de Roccé?', caja('¿Quién está atrás\nde Roccé?'), 236, 0, 59, pop=True, y_es_caja=True)
        cp.texto('pista1', 'Pista 1: tiene 19.', pl('Pista 1: tiene 19.', 72), 236, 66, 209)
        cp.texto('pista2', 'Pista 2: es de Cañuelas.', pl('Pista 2: es de Cañuelas.', 72), 330, 108, 209)
        cp.texto('pista3', 'Pista 3: labura en la fábrica de ladrillos de su familia.',
                 pl('Pista 3: labura en la fábrica\nde ladrillos de su familia.', 72), 424, 150, 209)
        cp.fondo('deg_p3', degrade(170, 640, 0.36), 210, 284)
        cp.texto('yo', 'Yo. Gianluca.', caja('Yo. Gianluca.'), 236, 210, 284, pop=True, y_es_caja=True)
        cp.texto('dato', 'Armo Roccé en paralelo a la fábrica.', cneg('Armo Roccé en paralelo a la fábrica.'), 420, 228, 284,
                 y_es_caja=True)
        cp.fondo('deg_p4', degrade(180, 640, 0.42), 285, 359)
        cp.texto('cta', 'Que tu historia lleve tu nombre.', M.placa_serif('Que tu historia\nlleve tu nombre.', 88, halo=0.7), 300, 285, 359)
    elif hid == 'H2':
        cp.texto('hook', '¿Qué tiene el Founder 001 que no tiene nadie?', caja('¿Qué tiene el Founder 001\nque no tiene nadie?'),
                 236, 0, 59, pop=True, y_es_caja=True)
        cp.texto('dato', 'Founders: los primeros 100 compradores, numerados 001–100.',
                 cneg('Founders: los primeros 100 compradores,\nnumerados 001–100.'), 506, 24, 59, y_es_caja=True)
        cp.texto('ev1', 'Diseña una prenda a su gusto.', pl('Diseña una prenda\na su gusto.', 76), 236, 60, 107)
        cp.texto('ev2', 'Y se lleva un porcentaje de la ganancia de esa prenda.',
                 pl('Y se lleva un porcentaje\nde la ganancia\nde esa prenda.', 76), 236, 108, 164)
        cp.texto('giro', '¿Y los otros 99?', caja('¿Y los otros 99?'), 236, 165, 197, pop=True, y_es_caja=True)
        cp.texto('ev3', 'Los 100, en un grupo privado de WhatsApp con Gianluca.',
                 pl('Los 100, en un grupo\nprivado de WhatsApp\ncon Gianluca.', 76), 236, 198, 254)
        cp.fondo('deg_p4', degrade(170, 560, 0.38), 255, 359)
        cp.texto('cta', 'Founders Privée', M.placa_serif('Founders Privée', 88, halo=0.7), 300, 255, 359)
    else:
        cp.texto('hook', '¿Cuál fue tu casi?', caja('¿Cuál fue tu casi?'), 236, 0, 59, pop=True, y_es_caja=True)
        cp.texto('ej1', 'El penal en el palo.', pl('El penal en el palo.', 88), 300, 66, 113)
        cp.texto('ej2', 'El 3 cuando se aprobaba con 4.', pl('El 3 cuando\nse aprobaba con 4.', 88), 300, 114, 161)
        cp.texto('ej3', 'El “te llamamos” que nunca llegó.', pl('El “te llamamos”\nque nunca llegó.', 88), 300, 162, 209)
        cp.texto('res', 'Lo llevamos en el pecho.', pl('Lo llevamos\nen el pecho.', 88), 236, 210, 284)
        cp.fondo('deg_p4', degrade(170, 480, 0.40), 285, 359)
        cp.texto('cta', 'Estar cerca y seguir.', pl('Estar cerca y seguir.', 76), 300, 285, 359)     # v02: Placa 76 con halo


class CapaH(M.Capa):
    def fondo(self, nombre, im, n0, n1):
        p = self.base / f'{nombre}.png'; im.save(p)
        self.items.insert(0, (str(p), 0, 0, n0, n1, nombre))      # debajo de los textos


def etapa_capas():
    for hid in sel(sys.argv):
        capa = T / hid / 'capa'
        if capa.exists():
            shutil.rmtree(capa)
        cp = CapaH(T / hid / 'textos')
        textos(hid, cp)
        cp.rasterizar(capa, NF)
        malas = C.fuera_de_zona([tuple(c['caja_visible']) for c in cp.cajas])
        ult = [c for c in cp.cajas if c['n1'] >= NF - 1]
        choque_sticker = [c['nombre'] for c in ult if not (c['caja_visible'][3] < ZONA_STICKER[0] or c['caja_visible'][1] > ZONA_STICKER[1])]
        jdump(dict(textos=cp.cajas, fuera_de_zona=malas, textos_en_zona_sticker=choque_sticker), T / hid / 'capas.json')
        print(hid, 'fuera de zona', malas, 'zona sticker', choque_sticker)
        for c in cp.cajas:
            print('  ', c['nombre'], c['n0'], c['n1'], c['caja_visible'])


# =====================================================================================================
# sonido: ambiente real + música TEMP baja en el pulso (120 BPM) + golpes de interfaz
# =====================================================================================================
AMB = {
    'H1': [('IMG_4530', 0.50, 0.0, 2.0, 0), ('IMG_7887', 0.00, 7.0, 9.5, -2), ('IMG_7894', 0.00, 9.5, DUR, 0)],
    'H2': [('IMG_7824', 0.00, 0.0, 2.0, -3), ('IMG_8004', 1.50, 2.0, 5.5, 4), ('IMG_7824', 5.80, 5.5, 8.5, -3),
           ('IMG_7896', 1.00, 8.5, DUR, 0)],
    'H3': [('IMG_7884', 3.00, 0.0, 2.0, -3), ('IMG_4627', 2.50, 2.0, 7.0, -5), ('IMG_7895', 0.00, 9.5, 11.8, -6)],
}
RAFAGAS_7887 = [(1.45, 1.60), (2.88, 3.05)]          # fuera (especificación 05)


def ambientes(hid, m):
    from sonido import db
    for toma, src0, t0, t1, g in AMB[hid]:
        a = m.leer(toma); n = int(round((t1 - t0) * SR)); s0 = int(round(src0 * SR))
        seg = a[s0:s0 + n].copy()
        if len(seg) < n:
            seg = np.concatenate([seg, np.zeros(n - len(seg))])
        if toma == 'IMG_7887':     # ráfaga 1,45–1,60 → parche de la misma toma (2,30–2,45), fundidos de 15 ms
            for r0, r1 in RAFAGAS_7887:
                i0, i1 = int((r0 - src0 - 0.02) * SR), int((r1 - src0 + 0.02) * SR)
                if 0 <= i0 < n:
                    i1 = min(i1, n); L = i1 - i0
                    par = a[int(2.30 * SR):int(2.30 * SR) + L]
                    k = int(0.015 * SR); env = np.ones(L); env[:k] = np.linspace(0, 1, k); env[-k:] = np.linspace(1, 0, k)
                    seg[i0:i1] = seg[i0:i1] * (1 - env) + par * env
                    m.log(t0 + r0 - src0, f'ráfaga 7887 {r0:.2f}–{r1:.2f} reemplazada por 7887 2,30–{2.30 + L / SR:.2f}')
        k = int(0.012 * SR); r = np.ones(n); r[:k] = np.linspace(0, 1, k); r[-k:] = np.linspace(1, 0, k)
        m.put('amb', seg * r * db(g), t0)
        m.log(t0, f'ambiente {toma} fuente {src0:.3f}–{src0 + t1 - t0:.3f} s, {g:+d} dB')
    if hid == 'H3':                # 7895 termina en 2,30: el congelado lleva el mar de 7894 (misma sesión), cruzado 60 ms
        a = m.leer('IMG_7894'); t0, t1 = 11.74, DUR; n = int(round((t1 - t0) * SR))
        seg = a[int(0.5 * SR):int(0.5 * SR) + n]; k = int(0.06 * SR); r = np.ones(n); r[:k] = np.linspace(0, 1, k)
        r[-int(0.012 * SR):] = np.linspace(1, 0, int(0.012 * SR))
        m.put('amb', seg * r * db(-4), t0); m.log(t0, 'ambiente IMG_7894 fuente 0,50–0,76 s (congelado final)')


def foley(hid, m):
    cfg = HIST[hid]
    for c in cfg['cortes']:
        m.barrido(c / FPS, .22, .10)
    tx = {'H1': [0, 66, 108, 150, 210, 228, 285], 'H2': [0, 24, 60, 108, 165, 198, 255], 'H3': [0, 66, 114, 162, 210, 285]}[hid]
    for c in tx:
        m.toque(c / FPS, .16, 2200); m.log(c / FPS, 'toque de texto')
    if hid in ('H1', 'H3'):        # dedos sobre el relieve del macro
        t0 = 2.0 if hid == 'H1' else 7.0
        m.tela(t0 + 0.3, 1.2, .12); m.tela(t0 + 2.6, 1.0, .1)


def musica(hid, m):
    b = 0.5                                                  # 120 BPM
    acordes = [[45, 48, 52], [41, 45, 48], [48, 52, 55], [43, 47, 50], [45, 48, 52], [41, 45, 48]]
    bajos = [33, 29, 36, 31, 33, 29]
    for i in range(6):                                       # compases de 2 s
        t = 2.0 * i
        m.pad(t, acordes[i], 2.0, .035, 1100, a=.15, r=.4)
        m.ocho08(t, bajos[i], 1.6, .28)
    for k in range(int(DUR / b)):
        t = k * b
        if k % 2 == 0:
            m.bombo(t, .42, f0=100, f1=46, dec=.3)
        m.charles(t + b / 2, .045)
    for c in HIST[hid]['cortes']:
        m.campana(c / FPS, 76, .045)
    res = {'H1': 7.0, 'H2': 5.5, 'H3': 7.0}[hid]            # resolución / giro
    m.bombo(res, .8); m.impacto(res, .22)
    m.fundido('mus', 11.55, DUR); m.fundido('bombo', 11.55, DUR); m.fundido('fx', 11.75, DUR)
    # «música TEMP baja»: por tramo (plano), música + bombo quedan 6 dB debajo del ambiente real del mismo tramo
    # (sonoridad con ponderación K, BS.1770, sin compuerta). En los tramos del macro 3453, sin ambiente (−50 LUFS), la
    # música va a la mediana del ambiente −2 dB para que no quede un hueco. Rampas de 0,12 s en los cortes.
    cortes = [0] + HIST[hid]['cortes'] + [NF]
    secc = [(a / FPS, b / FPS) for a, b in zip(cortes[:-1], cortes[1:])]
    mus = m.pistas['mus'] + m.pistas['bombo']
    la = [kloud(m.pistas['amb'], t0, t1) for t0, t1 in secc]
    lm = [kloud(mus, t0, t1) for t0, t1 in secc]
    con_amb = [x for x in la if x > -60]
    obj = [(x - 6.0) if x > -60 else (float(np.median(con_amb)) - 2.0) for x in la]
    gs = [o - y for o, y in zip(obj, lm)]
    t = np.arange(m.N) / SR; g = np.full(m.N, gs[0])
    for (t0, _), g0, g1 in zip(secc[1:], gs[:-1], gs[1:]):
        r = np.clip((t - (t0 - 0.06)) / 0.12, 0, 1)
        g = g + (g1 - g0) * r
    k = 10 ** (g / 20)
    for pista in ('mus', 'bombo'):
        m.pistas[pista] *= k[:, None]
    m.log(0.0, 'música baja por tramo: ' + '; '.join(f'{a:.1f}–{b:.1f} s amb {x:.1f} → música {o:.1f} LUFS-K ({gg:+.1f} dB)'
                                                     for (a, b), x, o, gg in zip(secc, la, obj, gs)))


def kloud(x, t0, t1):
    """sonoridad (LUFS, sin compuerta) con ponderación K de BS.1770 a 48 kHz del tramo [t0, t1) de una pista estéreo."""
    from scipy.signal import lfilter
    seg = x[int(t0 * SR):int(t1 * SR)]
    z = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585], seg, axis=0)
    z = lfilter([1.0, -2.0, 1.0], [1, -1.99004745483398, 0.99007225036621], z, axis=0)
    e = (z ** 2).mean(0).sum()
    return -0.691 + 10 * np.log10(e + 1e-12)


def etapa_audio():
    out = {}
    for hid in sel(sys.argv):
        out[hid] = M.mezclar(f'{hid}_mezcla', DUR, [lambda m, h=hid: ambientes(h, m), lambda m, h=hid: foley(h, m),
                                                     lambda m, h=hid: musica(h, m)], T / hid / 'audio')
        jdump(out[hid], T / hid / 'audio' / 'audio.json')
        print(hid, out[hid]['final'])


# =====================================================================================================
# máster, control, guías del sticker, entrega
# =====================================================================================================
def etapa_master():
    for hid in sel(sys.argv):
        cfg = HIST[hid]; (T / hid / 'master').mkdir(parents=True, exist_ok=True)
        f = T / hid / 'master' / cfg['nombre']
        M.master_capa(T / hid / f'{hid}_base.mp4', T / hid / 'capa', T / hid / 'audio' / f'{hid}_mezcla.wav', f)
        print(f, U.md5_stream(f, 'v'), U.md5_stream(f, 'a'))


def estatico_final(mp4, umbral=0.15):
    """segundos al final con diferencia de luma entre cuadros < umbral (cuadros congelados)."""
    d = M.movimiento(mp4, NF - 30, NF - 1)
    k = 0
    while k < len(d) and d[len(d) - 1 - k] < umbral:
        k += 1
    return round(k / FPS, 3), d


def etapa_control():
    for hid in sel(sys.argv):
        cfg = HIST[hid]; ev = EVID / hid; ev.mkdir(parents=True, exist_ok=True)
        f = T / hid / 'master' / cfg['nombre']
        rep = dict(fecha='2026-11-25', pieza=hid, archivo=M.ficha(f))
        cortes = cfg['cortes']
        tramos = [(f'{p[0]} {p[1]}', c0 / FPS, c1 / FPS) for p, c0, c1 in zip(cfg['planos'], [0] + cortes, cortes + [NF])]
        rep['niveles'] = M.niveles(f, tramos)
        quieto, d = estatico_final(f)
        rep['ultimo_plano'] = dict(segundos_quietos_al_final=quieto, diferencia_entre_cuadros_ultimo_segundo=d)
        lista = json.load(open(T / hid / 'planos.json'))
        rep['color_prenda'] = {}
        for p, c0, c1 in zip(lista, [0] + cortes, cortes + [NF]):
            if p['modo'] in ('neutra', 'neutra_z', 'neutra_a'):
                rep['color_prenda'][p['id'] + ' Blanca ' + p['toma']] = {f'c{c}': M.rgb_plano(f, c, reg_salida(p['toma'], p['modo'])) for c in (c0 + 5, (c0 + c1) // 2)}
            if p['modo'] == 'negra':
                rep['color_prenda'][p['id'] + ' Negra ' + p['toma']] = {f'c{c}': M.tela_oscura(f, c, (0.55, 0.95, 0.0, 1.0)) for c in (c0 + 10, c1 - 1)}
        U.hoja_contacto(f, ev / 'hoja_cada_0.5s.jpg', cada=15, cols=6, ancho=240)
        U.cuadros_corte(f, cortes, ev / 'cortes', NF - 1)
        cap = json.load(open(T / hid / 'capas.json'))
        sel_c = sorted({0, 59} | {c['n0'] + (2 if c['pop'] else 0) for c in cap['textos']} | {c + 1 for c in cortes} | {NF - 1})
        M.vista_360(f, sel_c, ev / 'vista_360px.jpg', cols=6)
        shutil.copy2(T / hid / 'capas.json', ev / 'capas_textos.json')
        shutil.copy2(T / hid / 'planos.json', ev / 'planos.json')
        shutil.copy2(T / hid / 'audio' / 'audio.json', ev / 'audio.json')
        shutil.copy2(T / hid / 'audio' / f'{hid}_mezcla_eventos.json', ev / 'eventos_audio.json')
        jdump(rep, ev / 'control.json')
        a = rep['archivo']
        print(hid, a['md5_video'], a['md5_audio'], a['sonoridad'], a['video']['cuadros_decodificados'], a['video']['duracion'],
              a['audio']['duracion'], a['decodifica_completo'], a['marcas_ubicacion'], 'quieto', quieto,
              json.dumps(rep['color_prenda'], ensure_ascii=False), flush=True)


def guia(hid):
    """último cuadro + rectángulo gris punteado en la zona del sticker con su texto exacto (solo guía: el sticker se
    agrega en Instagram al publicar)."""
    cfg = HIST[hid]
    f = T / hid / 'master' / cfg['nombre']
    im = Image.fromarray(U.leer(f, W, H, n0=NF - 1, n1=NF - 1)[0]).convert('RGBA')
    tipo, lineas, opciones = cfg['sticker']
    y0, y1 = ZONA_STICKER
    x0, x1 = 150, 930
    capa = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    d.rounded_rectangle([x0, y0, x1, y1], radius=36, fill=(150, 150, 150, 120))
    # borde punteado
    paso, largo = 26, 14
    for x in range(x0 + 36, x1 - 36, paso):
        for y in (y0, y1):
            d.line([x, y, min(x + largo, x1 - 36), y], fill=(235, 235, 235, 255), width=5)
    for y in range(y0 + 36, y1 - 36, paso):
        for x in (x0, x1):
            d.line([x, y, x, min(y + largo, y1 - 36)], fill=(235, 235, 235, 255), width=5)
    f1 = C.fuente('semibold', 50); f2 = C.fuente('extrabold', 54); f3 = C.fuente('medium', 30)
    yy = y0 + 46
    for ln in lineas:
        tam = 50                                          # el texto del sticker no puede salirse del rectángulo
        while d.textlength(ln, font=C.fuente('semibold', tam)) > x1 - x0 - 72:
            tam -= 1
        fl = C.fuente('semibold', tam)
        w = d.textlength(ln, font=fl); d.text(((W - w) / 2, yy), ln, font=fl, fill=(255, 255, 255, 255)); yy += 70
    if opciones:
        bw = (x1 - x0 - 3 * 36) / 2
        for i, o in enumerate(opciones):
            bx = x0 + 36 + i * (bw + 36)
            d.rounded_rectangle([bx, yy + 6, bx + bw, yy + 106], radius=26, fill=(255, 255, 255, 230))
            w = d.textlength(o, font=f2); d.text((bx + (bw - w) / 2, yy + 22), o, font=f2, fill=(20, 20, 20, 255))
    cap = f'GUÍA · {tipo.lower()} (se agrega al publicar) · zona y {y0}–{y1}'
    w = d.textlength(cap, font=f3)                        # rótulo debajo del rectángulo, en una píldora oscura
    d.rounded_rectangle([(W - w) / 2 - 22, y1 + 18, (W + w) / 2 + 22, y1 + 70], radius=26, fill=(0, 0, 0, 150))
    d.text(((W - w) / 2, y1 + 26), cap, font=f3, fill=(245, 245, 245, 255))
    out = Image.alpha_composite(im, capa).convert('RGB')
    p = T / hid / cfg['guia']; out.save(p)
    return p


def etapa_guias():
    for hid in sel(sys.argv):
        p = guia(hid); shutil.copy2(p, EVID / hid / p.name); print(p)


def etapa_cajas():
    for hid in sel(sys.argv):
        print(M.hoja_cajas(T / hid / f'{hid}_base.mp4', T / hid / 'capas.json', EVID / hid / 'textos_vs_estampado_cada6.jpg',
                           cada=6, cols=12, ancho=225))


def etapa_color_h3():
    """v02 · control de la neutralización de H3 (dictamen §3): B−R de la Blanca en CADA cuadro de P1/P2 del máster v02
    (misma medición que rgb_plano) contra v01, y que arena, rocas y piel no cambien (media de color de los píxeles
    cálidos de v01, R > B + 15 y saturación > 0,15, y diferencia suavizada 15 px para no contar el remuestreo)."""
    from scipy.ndimage import uniform_filter
    from PIL import ImageDraw, ImageFont
    def leer(f, n0, n1, w=540, h=960):
        return U.leer(f, w, h, n0=n0, n1=n1, vf_pre='scale=in_color_matrix=bt709:in_range=tv').astype(np.float32)
    v1m = T / 'H3' / 'master' / 'ROCCE_H03_TU_CASI_v01.mp4'; v2m = T / 'H3' / 'master' / HIST['H3']['nombre']
    a, b = leer(v1m, 0, 209), leer(v2m, 0, 209)
    regs = {'P1': M.REG_BLANCA['IMG_7884'], 'P2': M.REG_BLANCA['IMG_4627']}
    def br(x, reg):
        r = x[int(reg[0] * 960):int(reg[1] * 960), int(reg[2] * 540):int(reg[3] * 540)]
        L = r.mean(2); sat = (r.max(2) - r.min(2)) / (r.max(2) + 1); m = (L > 150) & (sat < 0.15)
        rgb = [float(r[..., c][m].mean()) for c in range(3)]
        return round(rgb[2] - rgb[0], 1), round(rgb[1] - rgb[0], 1)
    por, cal = [], []
    for i in range(210):
        reg = regs['P1'] if i < 60 else regs['P2']
        (b1, g1), (b2, g2) = br(a[i], reg), br(b[i], reg)
        por.append(dict(c=i, b_r_v01=b1, b_r_v02=b2, g_r_v02=g2))
        x = a[i]; sat = (x.max(2) - x.min(2)) / (x.max(2) + 1); warm = (x[..., 0] > x[..., 2] + 15) & (sat > 0.15)
        d = (b[i] - a[i])[warm].mean(0)
        sm = np.abs(uniform_filter(b[i], (15, 15, 1)) - uniform_filter(a[i], (15, 15, 1))).max(2)[warm]
        cal.append(dict(c=i, pixeles=int(warm.sum()), dif_media_rgb=[round(float(v), 2) for v in d],
                        dif_suavizada_media=round(float(sm.mean()), 2), dif_suavizada_p99=round(float(np.percentile(sm, 99)), 2)))
    res = dict(criterio=dict(blanca='B−R ≤ +8 (dictamen §3)', calidos='arena, rocas y piel: R > B + 15, sat > 0,15 en v01'),
               resumen=dict(b_r_v01=[min(x['b_r_v01'] for x in por), max(x['b_r_v01'] for x in por)],
                            b_r_v02=[min(x['b_r_v02'] for x in por), max(x['b_r_v02'] for x in por)],
                            g_r_v02=[min(x['g_r_v02'] for x in por), max(x['g_r_v02'] for x in por)],
                            salto_max_entre_cuadros_v01=max(abs(por[i]['b_r_v01'] - por[i - 1]['b_r_v01']) for i in range(1, 210) if i != 60),
                            salto_max_entre_cuadros_v02=max(abs(por[i]['b_r_v02'] - por[i - 1]['b_r_v02']) for i in range(1, 210) if i != 60),
                            calidos_dif_media_max=max(max(abs(v) for v in x['dif_media_rgb']) for x in cal),
                            calidos_dif_suavizada_p99_max=max(x['dif_suavizada_p99'] for x in cal)),
               blanca_por_cuadro=por, calidos_por_cuadro=cal)
    jdump(res, EVID / 'H3' / 'control_color_v02.json')
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
    out = Image.new('RGB', (540 * 3, 960 * 2), (20, 20, 20))
    for r, i in enumerate((12, 120)):
        dd = np.clip(np.abs(b[i] - a[i]) * 8, 0, 255).astype(np.uint8)
        for c, (im, t) in enumerate(((a[i], f'c{i} v01'), (b[i], f'c{i} v02'), (dd, f'c{i} |v02 − v01| × 8'))):
            I = Image.fromarray(im.astype(np.uint8)); D = ImageDraw.Draw(I)
            D.rectangle([0, 0, 330, 32], fill=(0, 0, 0)); D.text((6, 4), t, font=f, fill=(255, 255, 0))
            out.paste(I, (540 * c, 960 * r))
    out.save(EVID / 'H3' / 'blanca_v01_v02.jpg', quality=88)
    print(json.dumps(res['resumen'], ensure_ascii=False))


def etapa_entregar():
    res = {}
    for hid in sel(sys.argv):
        cfg = HIST[hid]
        r = M.entregar([cfg['nombre']], T / hid / 'master', EVID / hid, PIEZA, extras=[T / hid / cfg['guia']],
                       ev_dst=PIEZA / EVID.name / hid)
        res[hid] = r
    # la carpeta de evidencia queda como HISTORIAS/evidencia_v01/<H>/
    jdump(res, T / 'entrega.json')
    print(json.dumps({k: v['evidencia'] for k, v in res.items()}))


if __name__ == '__main__':
    globals()['etapa_' + sys.argv[1]]()
