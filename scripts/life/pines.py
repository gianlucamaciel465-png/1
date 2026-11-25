#!/usr/bin/env python3
"""Roccé Life · pines de Pinterest con frase (1000×1500, PNG sRGB).

Cada pin = foto o cuadro real de Roccé (recorte 2:3 documentado) + degradé suave donde va el texto + frase propia
(Instrument Serif, cursiva en la palabra clave) + firma chica «ROCCÉ LIFE» + logo original en ficha #FEFEFE
(radio ≤ 12 %: solo se recorta fondo, el dibujo empieza a 182 px del borde de 1254).

Uso:  python3 pines.py [version]      → TRABAJO/life/pines/<version>/
Fondos: fotos de PRODUCTO/ (Display P3 → sRGB con ImageCms) o cuadros de ORIGINALES/ extraídos con la cadena de
scripts/fmt/video.py (BT.709, HLG → SDR con mobius y ganancias por toma).
"""
import io, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageOps, ImageCms

R = Path('/home/user/1')
F = R / 'scripts' / 'fuentes'
W, H = 1000, 1500
sys.path.insert(0, str(R / 'scripts' / 'fmt'))


def srgb(path):
    im = ImageOps.exif_transpose(Image.open(path))
    icc = im.info.get('icc_profile')
    if icc:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc)); dst = ImageCms.createProfile('sRGB')
        im = ImageCms.profileToProfile(im.convert('RGB'), src, dst, renderingIntent=1, outputMode='RGB')
    return im.convert('RGB')


def cuadro(toma, seg, out):
    import video as V
    vf = V.color(toma).replace('format=yuv420p', 'format=rgb24')
    V.sh(['ffmpeg', '-v', 'error', '-y', '-ss', f'{seg:.3f}', '-i', str(V._src(toma)), '-frames:v', '1', '-vf', vf, str(out)])
    return Image.open(out).convert('RGB')


def neutralizar(im, caja):
    """Blanca neutra (la toma de iPhone sale fría: B−R +13…+21). Mide la tela blanca lisa dentro de `caja` (L > 150,
    sat < 0,12) por franja de luminancia, interpola la ganancia por L y la aplica solo a neutros claros (sat < 0,10 entera,
    se apaga hasta 0,15; L desde 120, entera desde 150) solo sobre la Blanca (mayor componente conexo de tela clara dentro de
    la caja, +8 px, borde de 3 px): el estampado de la Negra queda igual (dictamen de Roma 24/11), el celeste del estampado
    (sat 0,17–0,26), las rocas, la piel y el negro no cambian. Mismo criterio que scripts/vir/vir01_v02.py (COLOR)."""
    import numpy as np
    from PIL import ImageFilter
    a = np.asarray(im, np.float32)
    L = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    mx, mn = a.max(-1), a.min(-1); sat = (mx - mn) / (mx + 1)
    x0, y0, x1, y1 = caja
    dentro = np.zeros(L.shape, bool); dentro[y0:y1, x0:x1] = True
    # solo la Blanca: el mayor componente conexo de tela clara y neutra dentro de la caja (el estampado gris claro de la
    # Negra cumple la misma condición pero está separado por tela negra: queda afuera), ensanchado 8 px para los bordes
    from scipy import ndimage as ndi
    lab, n = ndi.label(dentro & (L > 150) & (sat < 0.12), structure=np.ones((3, 3)))
    tam = ndi.sum(np.ones(L.shape), lab, index=np.arange(1, n + 1))
    blob = lab == (1 + int(np.argmax(tam)))
    dentro = ndi.binary_dilation(blob, iterations=8)
    tela = blob
    cent, gan, med = [], [], []
    for lo, hi in [(150, 190), (190, 215), (215, 256)]:
        m = tela & (L >= lo) & (L < hi)
        if m.sum() < 3000:
            continue
        md = np.median(a[m], 0); y = float(md @ np.array([0.2126, 0.7152, 0.0722]))
        cent.append(float(np.median(L[m]))); gan.append(y / np.maximum(md, 1e-3)); med.append(md.round(1).tolist())
    cent = np.array(cent); gan = np.array(gan)
    g = np.stack([np.interp(L, cent, gan[:, k]) for k in range(3)], -1)
    ss = lambda x: (lambda c: c * c * (3 - 2 * c))(np.clip(x, 0, 1))
    w = np.clip((0.15 - sat) / 0.05, 0, 1) * ss((L - 120) / 30)
    borde = Image.fromarray((dentro * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
    w = w * (np.asarray(borde, np.float32) / 255)
    out = a * (1 + w[..., None] * (g - 1))
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)), dict(caja=caja, mediana_por_franja=med,
                                                                             ganancias=gan.round(4).tolist())


def fondo(p, carpeta):
    """p['fuente'] = ('foto', 'archivo.jpg') o ('toma', 'IMG_7887', segundo). p['caja'] = (x, y, w) con h = 1,5·w."""
    if p['fuente'][0] == 'color':
        # fondo liso con degradé vertical (arriba → abajo) y grano de ±1,5 niveles para que no haga bandas en 8 bits
        import numpy as np
        a = np.array(Image.new('RGB', (1, 1), p['fuente'][1]).getpixel((0, 0)), float)
        b = np.array(Image.new('RGB', (1, 1), p['fuente'][2]).getpixel((0, 0)), float)
        t = np.linspace(0, 1, H)[:, None, None]
        arr = a + (b - a) * t + np.zeros((H, W, 3))
        arr += np.random.default_rng(7).normal(0, 1.5, arr.shape)
        bg = Image.fromarray(np.clip(arr.round(), 0, 255).astype('uint8'))
        out = carpeta / f"_fondo_{p['id']}.png"
        bg.save(out)
        return out, (W, H)
    if p['fuente'][0] == 'foto':
        im = srgb(R / 'PRODUCTO' / p['fuente'][1])
    elif p['fuente'][0] == 'externa':   # foto de banco con licencia (fuera de git: TRABAJO/life2/pines_v06/fotos/)
        im = srgb(R / p['fuente'][1])
    else:
        im = cuadro(p['fuente'][1], p['fuente'][2], carpeta / f"_cuadro_{p['id']}.png")
    if p.get('neutro'):
        im, p['_neutro'] = neutralizar(im, p['neutro'])
    x, y, w = p['caja']; h = round(w * 1.5)
    assert x >= 0 and y >= 0 and x + w <= im.width and y + h <= im.height, (p['id'], im.size, p['caja'])
    bg = im.crop((x, y, x + w, y + h)).resize((W, H), Image.LANCZOS)
    if p.get('ajuste'):
        from PIL import ImageEnhance
        a = p['ajuste']
        if 'brillo' in a: bg = ImageEnhance.Brightness(bg).enhance(a['brillo'])
        if 'contraste' in a: bg = ImageEnhance.Contrast(bg).enhance(a['contraste'])
    out = carpeta / f"_fondo_{p['id']}.png"
    bg.save(out)
    return out, im.size


CSS = """
@font-face{font-family:'IS';src:url('file://%(F)s/InstrumentSerif-Regular.ttf')}
@font-face{font-family:'ISI';src:url('file://%(F)s/InstrumentSerif-Italic.ttf')}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:%(W)dpx;height:%(H)dpx;overflow:hidden;background:#15191D}
.bg{position:absolute;inset:0;background-size:cover}
.grad{position:absolute;left:0;right:0}
.frase{position:absolute;left:%(mx)dpx;right:%(mx)dpx;font-family:'IS';font-weight:400;color:%(color)s;
  font-size:%(fs)dpx;line-height:%(lh)s;letter-spacing:-0.012em;text-shadow:%(sombra)s;
  font-feature-settings:'kern','liga'}
.frase em{font-family:'ISI';font-style:normal}
.frase .c{color:%(acento)s}
.firma{position:absolute;display:flex;align-items:center;gap:16px}
.firma img{width:%(logo)dpx;height:%(logo)dpx;border-radius:%(radio)dpx;display:block}
.firma span{font-family:'Inter';font-weight:500;font-size:%(ffs)dpx;letter-spacing:.34em;color:%(fcolor)s;
  text-shadow:%(sombra_f)s}
"""


def html(p, fondo_png, carpeta):
    t = dict(F=F, W=W, H=H, mx=p.get('mx', 76), color=p.get('color', '#FFFFFF'), fs=p.get('fs', 104),
             lh=p.get('lh', '1.0'), acento=p.get('acento', '#CDDDE5'), logo=p.get('logo', 72), ffs=p.get('ffs', 21),
             radio=round(p.get('logo', 72) * 0.11), fcolor=p.get('fcolor', 'rgba(255,255,255,.92)'),
             sombra=p.get('sombra', '0 2px 24px rgba(0,0,0,.28)'), sombra_f=p.get('sombra_f', '0 1px 8px rgba(0,0,0,.35)'))
    grad = ''
    for g in (p.get('grad'), p.get('grad2')):  # (lado, alto_px, opacidad_max, color); grad2 = segundo degradé (v03)
        if not g:
            continue
        lado, alto, op, col = g
        r, gg, b = col
        d = 'to top' if lado == 'bottom' else 'to bottom'
        grad += (f'<div class="grad" style="{lado}:0;height:{alto}px;background:linear-gradient({d},'
                 f'rgba({r},{gg},{b},{op}) 0%,rgba({r},{gg},{b},{op * 0.55:.3f}) 45%,rgba({r},{gg},{b},0) 100%)"></div>')
    pos_f = p['pos_frase']  # css (p. ej. 'top:120px' o 'bottom:210px')
    pos_s = p['pos_firma']
    logo = R / 'LOGO' / 'rocce_logo.png'
    firma = (f'<div class="firma" style="{pos_s}"><img src="file://{logo}"><span>ROCCÉ LIFE</span></div>'
             if p.get('firma', True) else '')
    doc = (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS % t}</style></head><body>'
           f'<div class="bg" style="background-image:url(\'file://{fondo_png}\')"></div>{grad}'
           f'<div class="frase" style="{pos_f};text-align:{p.get("alinear", "left")}">{p["frase_html"]}</div>{firma}'
           f'</body></html>')
    out = carpeta / f"{p['id']}.html"
    out.write_text(doc, encoding='utf-8')
    return out


# ---------------------------------------------------------------------------------------------------------------------
# v05 · estilo de los pines del perfil de Gianluca (capturas IMG_5539–5541, 25/11/2026): frase en MAYÚSCULAS en Anton,
# centrada en el tercio superior, relleno con degradé vertical por renglón (blanco → gris claro; acento celeste), sombra
# oscura marcada debajo (una dura corta + un halo blando), logo «1» recortado (LOGO/ROCCE_logo_sin_fondo.png, sin tocar:
# solo escala y posición) centrado justo debajo de la frase; borde blanco fino solo sobre fondo oscuro. Sin firma ni ficha.
# El texto va en SVG: la línea de base y los degradés quedan en píxeles exactos (no dependen de las métricas de CSS).
# Medidas de Anton (Pillow, 1000 px): mayúscula 0,860 em, ascendente 1,177 em, tilde de mayúscula 0,241 em sobre la H.
ANTON_CAP = 0.860
LOGO_SF = R / 'LOGO' / 'ROCCE_logo_sin_fondo.png'
LOGO_BBOX = (356, 179, 870, 1056)          # caja del dibujo (alfa > 0) en el PNG de 1254×1254
BLANCO = ('#FFFFFF', '#D4D4D2')            # arriba → abajo de cada renglón (sus pines: 249–253 → 207–222)
ACENTO = ('#E1EBEF', '#CDDDE5')            # celeste del acento de v04 abajo, «un poco más claro» arriba (pedido de Roma)

CSS_ANTON = """
@font-face{font-family:'Anton';src:url('file://%(F)s/Anton-Regular.ttf')}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:%(W)dpx;height:%(H)dpx;overflow:hidden;background:%(fondo_body)s}
.bg{position:absolute;inset:0;background-size:cover}
.grad{position:absolute;left:0;right:0}
svg{position:absolute;left:0;top:0}
.logo{position:absolute;display:block}
"""


def geometria(p):
    """Renglones: línea de base de cada uno a partir de la altura de mayúscula del primero (p['top']), el cuerpo (fs) y la
    interlínea (paso / mayúscula). Logo: alto del dibujo p['logo_h'], a p['logo_gap'] px debajo de la última base."""
    fs = p['fs']; cap = ANTON_CAP * fs; paso = cap * p.get('inter', 1.14)
    ex = p.get('extra', {})   # px extra encima del renglón i (p. ej. una Ñ cuya virgulilla toca el renglón de arriba)
    bases = [p['top'] + cap + i * paso + sum(v for k, v in ex.items() if k <= i) for i in range(len(p['lineas']))]
    s = p['logo_h'] / (LOGO_BBOX[3] - LOGO_BBOX[1])
    logo_top = bases[-1] + p['logo_gap']
    cx = W / 2 + p.get('dx', 0)
    lx = cx - (LOGO_BBOX[0] + LOGO_BBOX[2]) / 2 * s
    ly = logo_top - LOGO_BBOX[1] * s
    return dict(fs=fs, cap=cap, paso=paso, bases=bases, cx=cx, logo_escala=s, logo_img=(lx, ly, 1254 * s),
                logo_caja=(cx - (LOGO_BBOX[2] - LOGO_BBOX[0]) / 2 * s, logo_top,
                           cx + (LOGO_BBOX[2] - LOGO_BBOX[0]) / 2 * s, logo_top + p['logo_h']))


def html_anton(p, fondo_png, carpeta, modo='final'):
    """modo: 'final' · 'sin' (sin frase ni logo, con los degradés: base del contraste, mismo método que v04) ·
    'mascara' (frase blanca sólida sin sombra sobre negro: píxeles del trazo) · 'logo' (solo el logo sobre blanco)."""
    g = geometria(p)
    t = dict(F=F, W=W, H=H, fondo_body='#000' if modo == 'mascara' else ('#FFF' if modo == 'logo' else '#15191D'))
    capas = ''
    if modo in ('final', 'sin'):
        capas += f'<div class="bg" style="background-image:url(\'file://{fondo_png}\')"></div>'
        for gr in p.get('grads', []):  # dict(lado, alto, color, stops=[(pct, opacidad), ...])
            r, gg, b = gr['color']
            d = 'to top' if gr['lado'] == 'bottom' else 'to bottom'
            st = ','.join(f'rgba({r},{gg},{b},{o}) {pc}%' for pc, o in gr['stops'])
            capas += f'<div class="grad" style="{gr["lado"]}:0;height:{gr["alto"]}px;background:linear-gradient({d},{st})"></div>'
    svg = ''
    if modo in ('final', 'mascara'):
        cap, fs = g['cap'], g['fs']
        sm = p.get('sombra', dict(dura=(0.05, 0.012, 0.80), halo=(0.03, 0.10, 0.62)))  # (dy, desenfoque, alfa) × mayúscula
        defs, textos = '', ''
        for i, (linea, base) in enumerate(zip(p['lineas'], g['bases'])):
            for k, cols in (('b', BLANCO), ('c', p.get('acento', ACENTO))):
                defs += (f'<linearGradient id="g{i}{k}" gradientUnits="userSpaceOnUse" x1="0" x2="0" '
                         f'y1="{base - cap:.2f}" y2="{base:.2f}"><stop offset="0" stop-color="{cols[0]}"/>'
                         f'<stop offset="0.38" stop-color="{cols[0]}"/><stop offset="1" stop-color="{cols[1]}"/>'
                         f'</linearGradient>')
            tsp = ''.join(f'<tspan fill="{"#FFFFFF" if modo == "mascara" else f"url(#g{i}{k or "b"})"}">{txt}</tspan>'
                          for txt, k in linea)
            ob = (f' transform="translate({g["cx"]:.2f} {base:.2f}) skewX({-p["oblicua"]}) '
                  f'translate({-g["cx"]:.2f} {-base:.2f})"') if p.get('oblicua') else ''
            textos += (f'<text x="{g["cx"]:.2f}" y="{base:.2f}" text-anchor="middle" font-family="Anton" '
                       f'font-size="{fs}" style="white-space:pre"{ob}>{tsp}</text>')
        if modo == 'final':
            (d1, s1, a1), (d2, s2, a2) = sm['dura'], sm['halo']
            defs += (f'<filter id="sombra" x="-20%" y="-30%" width="140%" height="170%" '
                     f'color-interpolation-filters="sRGB">'
                     f'<feGaussianBlur in="SourceAlpha" stdDeviation="{s2 * cap:.2f}"/>'
                     f'<feOffset dy="{d2 * cap:.2f}"/><feComponentTransfer result="h2"><feFuncA type="linear" '
                     f'slope="{a2}"/></feComponentTransfer>'
                     f'<feGaussianBlur in="SourceAlpha" stdDeviation="{s1 * cap:.2f}"/>'
                     f'<feOffset dy="{d1 * cap:.2f}"/><feComponentTransfer result="h1"><feFuncA type="linear" '
                     f'slope="{a1}"/></feComponentTransfer>'
                     f'<feMerge><feMergeNode in="h2"/><feMergeNode in="h1"/><feMergeNode in="SourceGraphic"/></feMerge>'
                     f'</filter>')
            textos = f'<g filter="url(#sombra)">{textos}</g>'
        svg = f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{defs}</defs>{textos}</svg>'
    logo = ''
    if modo in ('final', 'logo'):
        lx, ly, lw = g['logo_img']
        borde = ''
        if modo == 'final' and p.get('logo_borde'):
            b = p.get('logo_borde_px', 1.5)
            borde = ('filter:' + ' '.join(f'drop-shadow({x}px {y}px 0 #FFFFFF)'
                                          for x, y in ((b, 0), (-b, 0), (0, b), (0, -b))) + ';')
        logo = (f'<img class="logo" src="file://{LOGO_SF}" style="left:{lx:.2f}px;top:{ly:.2f}px;'
                f'width:{lw:.2f}px;height:{lw:.2f}px;{borde}">')
    doc = (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS_ANTON % t}</style></head><body>'
           f'{capas}{svg}{logo}</body></html>')
    suf = '' if modo == 'final' else f'_{modo}'
    out = carpeta / f"{p['id']}{suf}.html"
    out.write_text(doc, encoding='utf-8')
    return out


def control_anton(pines, carpeta):
    """Contraste del trazo de la frase contra el mismo pin sin frase (WCAG, mismo método que v04: la sombra no cuenta)
    y fondo bajo el logo. Devuelve un dict por pin."""
    import numpy as np
    cc = carpeta / '_control'; cc.mkdir(exist_ok=True)
    trabajos = []
    for p in pines:
        fpng = carpeta / f"_fondo_{p['id']}.png"
        for m in ('sin', 'mascara', 'logo'):
            h = html_anton(p, fpng, cc, m)
            trabajos.append(dict(html=str(h), out=str(cc / f"{p['id']}_{m}.png"), w=W, h=H))
    j = cc / '_trabajos.json'; j.write_text(json.dumps(trabajos, indent=1))
    subprocess.run(['node', str(R / 'scripts' / 'life' / 'render.js'), str(j)], check=True, capture_output=True)

    def lum(a):
        c = a.astype(np.float64) / 255
        c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        return c @ np.array([0.2126, 0.7152, 0.0722])
    res = {}
    for p in pines:
        fin = np.asarray(Image.open(carpeta / f"{p['nombre']}.png").convert('RGB'))
        sin = np.asarray(Image.open(cc / f"{p['id']}_sin.png").convert('RGB'))
        mas = np.asarray(Image.open(cc / f"{p['id']}_mascara.png").convert('L'))
        lg = np.asarray(Image.open(cc / f"{p['id']}_logo.png").convert('L'))
        trazo = mas >= 128
        Lf, Ls = lum(fin), lum(sin)
        cr = (np.maximum(Lf, Ls) + 0.05) / (np.minimum(Lf, Ls) + 0.05)
        v = cr[trazo]
        ys, xs = np.where(trazo)
        g = geometria(p)
        x0, y0, x1, y1 = [round(c) for c in g['logo_caja']]
        dib = lg < 128                                    # píxeles del dibujo del logo (negro) sobre blanco
        zona = np.zeros_like(trazo); zona[y0:y1, x0:x1] = True
        fondo_logo = Ls[zona & ~dib]
        crl = (np.median(fondo_logo) + 0.05) / (Lf[dib & (lg < 60)].mean() + 0.05)
        res[p['id']] = dict(
            trazo_px=int(trazo.sum()), contraste_mediana=round(float(np.median(v)), 2),
            pct_ge_3=round(float((v >= 3).mean() * 100), 2), contraste_p1=round(float(np.percentile(v, 1)), 2),
            bloque_xyxy=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            bloque_ancho_pct=round((xs.max() - xs.min() + 1) / W * 100, 1),
            mayuscula_px=round(g['cap'], 1), mayuscula_pct_ancho=round(g['cap'] / W * 100, 2),
            bases_px=[round(b, 1) for b in g['bases']], paso_px=round(g['paso'], 1),
            logo_caja_xyxy=[round(c, 1) for c in g['logo_caja']], logo_alto_pct_ancho=round(p['logo_h'] / W * 100, 1),
            logo_fondo_lum_mediana=round(float(np.median(fondo_logo)), 3),
            logo_contraste_negro_vs_fondo=round(float(crl), 2), logo_borde=bool(p.get('logo_borde')))
    (carpeta / '_control.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return res


def construir(pines, version):
    carpeta = R / 'TRABAJO' / 'life' / 'pines' / version
    carpeta.mkdir(parents=True, exist_ok=True)
    trabajos, registro = [], []
    for p in pines:
        fpng, tam = fondo(p, carpeta)
        h = html_anton(p, fpng, carpeta) if p.get('estilo') == 'anton' else html(p, fpng, carpeta)
        out = carpeta / f"{p['nombre']}.png"
        trabajos.append(dict(html=str(h), out=str(out), w=W, h=H))
        registro.append(dict(id=p['id'], nombre=p['nombre'], fuente=p['fuente'], tam_fuente=tam,
                             caja_xywh=[*p['caja'], round(p['caja'][2] * 1.5)], frase=p['frase_txt'],
                             neutro=p.get('_neutro'), ajuste=p.get('ajuste')))
        if p.get('estilo') == 'anton':
            registro[-1].update(estilo='anton', lineas=[''.join(t for t, _ in l) for l in p['lineas']],
                                acento=[t for l in p['lineas'] for t, k in l if k == 'c'], fs=p['fs'],
                                grads=p.get('grads'), logo=str(LOGO_SF.relative_to(R)), logo_h=p['logo_h'],
                                logo_borde=bool(p.get('logo_borde')), con_remera=p.get('con_remera'),
                                motivo_foto=p.get('motivo_foto'))
    j = carpeta / '_trabajos.json'
    j.write_text(json.dumps(trabajos, indent=1))
    subprocess.run(['node', str(R / 'scripts' / 'life' / 'render.js'), str(j)], check=True)
    # sRGB incrustado + hoja + miniaturas a 180 px (vista de feed en teléfono)
    srgb_icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    ims = []
    for t in trabajos:
        im = Image.open(t['out']).convert('RGB')
        assert im.size == (W, H), im.size
        im.save(t['out'], icc_profile=srgb_icc, optimize=True)
        ims.append(im)
    hoja = Image.new('RGB', (W * len(ims) // 2 + 20 * (len(ims) + 1), H // 2 + 40), '#F7F7F3')
    for i, im in enumerate(ims):
        hoja.paste(im.resize((W // 2, H // 2), Image.LANCZOS), (20 + i * (W // 2 + 20), 20))
    hoja.save(carpeta / '_hoja.jpg', quality=90)
    mini = Image.new('RGB', (180 * len(ims) + 12 * (len(ims) + 1), 270 + 24), '#FFFFFF')
    for i, im in enumerate(ims):
        mini.paste(im.resize((180, 270), Image.LANCZOS), (12 + i * 192, 12))
    mini.save(carpeta / '_miniaturas_180px.png')
    (carpeta / '_registro.json').write_text(json.dumps(registro, indent=1, ensure_ascii=False))
    anton = [p for p in pines if p.get('estilo') == 'anton']
    if anton:
        for k, v in control_anton(anton, carpeta).items():
            print(k, v)
    return carpeta


if __name__ == '__main__':
    from pines_config import PINES
    v = sys.argv[1] if len(sys.argv) > 1 else 'v00'
    print(construir(PINES[v], v))
