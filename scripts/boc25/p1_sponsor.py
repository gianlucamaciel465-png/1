"""P1 · vuelve ilegible el sponsor del pecho (letras oscuras sobre la franja amarilla de la camiseta de Boca) sin
seguimiento: máscara de amarillo a media resolución, cierre morfológico (las letras quedan rodeadas de amarillo),
y desenfoque gaussiano de toda la franja cerrada (letras, números y rayas incluidos).
Se aplica a los planos de 140245 (camisetas de frente). No toca marcas de agua ni el resto de la imagen."""
import numpy as np
from PIL import Image, ImageFilter


def mascara_amarillo(a):
    """amarillo de la franja por tono (HSV de PIL: H 0–255): 28–50 ≈ 40°–70°, saturación y brillo mínimos
    (la franja con luz fuerte queda pálida y un umbral por canales no la tomaba: «etsson» legible en 140245 @21,8)"""
    hsv = np.asarray(Image.fromarray(a).convert('HSV')).astype(np.int16)
    h, s_, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    m = (h >= 26) & (h <= 52) & (s_ > 55) & (v > 105)
    return Image.fromarray((m * 255).astype(np.uint8))


def tapar(f, cierre=13, sigma=6.0, pluma=2):
    """f: Image RGB. cierre: lado del cierre morfológico a media resolución (px, impar)."""
    a = np.asarray(f)
    w, h = f.size
    am = mascara_amarillo(np.asarray(f.resize((w // 2, h // 2), Image.BILINEAR)))
    ce = am.filter(ImageFilter.MaxFilter(cierre)).filter(ImageFilter.MinFilter(cierre))
    # toda la franja cerrada (con sus letras) se desenfoca: a media resolución las letras se mezclan con el amarillo y
    # «solo los huecos» las dejaba pasar (v01). El amarillo liso desenfocado no cambia; letras, números y rayas sí.
    m = ce.filter(ImageFilter.MaxFilter(3))
    m = m.resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(pluma))
    mm = np.asarray(m, np.float32)[..., None] / 255
    bl = np.asarray(f.filter(ImageFilter.GaussianBlur(sigma)), np.float32)
    o = a.astype(np.float32) * (1 - mm) + bl * mm
    return Image.fromarray(o.round().clip(0, 255).astype(np.uint8))
