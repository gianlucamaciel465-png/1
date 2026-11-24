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
    if p['fuente'][0] == 'foto':
        im = srgb(R / 'PRODUCTO' / p['fuente'][1])
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
    g = p.get('grad')  # (lado, alto_px, opacidad_max, color)
    grad = ''
    if g:
        lado, alto, op, col = g
        r, gg, b = col
        d = 'to top' if lado == 'bottom' else 'to bottom'
        grad = (f'<div class="grad" style="{lado}:0;height:{alto}px;background:linear-gradient({d},'
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


def construir(pines, version):
    carpeta = R / 'TRABAJO' / 'life' / 'pines' / version
    carpeta.mkdir(parents=True, exist_ok=True)
    trabajos, registro = [], []
    for p in pines:
        fpng, tam = fondo(p, carpeta)
        h = html(p, fpng, carpeta)
        out = carpeta / f"{p['nombre']}.png"
        trabajos.append(dict(html=str(h), out=str(out), w=W, h=H))
        registro.append(dict(id=p['id'], nombre=p['nombre'], fuente=p['fuente'], tam_fuente=tam,
                             caja_xywh=[*p['caja'], round(p['caja'][2] * 1.5)], frase=p['frase_txt'],
                             neutro=p.get('_neutro'), ajuste=p.get('ajuste')))
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
    return carpeta


if __name__ == '__main__':
    from pines_config import PINES
    v = sys.argv[1] if len(sys.argv) > 1 else 'v00'
    print(construir(PINES[v], v))
