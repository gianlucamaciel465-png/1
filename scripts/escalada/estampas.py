# Recorta los estampados reales de las texturas de la remera negra (hielo/textura_remera.py) para vestir al escalador:
#   espalda: ROCCÉ tono sobre tono + Founders Privée (zona 430–1930 × 280–960 de la textura de espalda)
#   frente:  ROCCÉ / so f★cking close. del pecho (zona 1262–1508 × 446–572 de la textura de frente)
# Uso: python estampas.py TEXTURA_ESPALDA.png TEXTURA_FRENTE.png SALIDA_DIR
import sys, os
from PIL import Image
esp, fre, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
Image.open(esp).convert("RGB").crop((430, 280, 1930, 960)).save(os.path.join(out, "estampa_espalda.png"))
Image.open(fre).convert("RGB").crop((1262, 446, 1508, 572)).save(os.path.join(out, "estampa_frente.png"))
print("estampas en", out)
