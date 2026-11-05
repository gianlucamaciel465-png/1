# Voces de "ESTUVISTE CERCA": dos voces rioplatenses de edge-tts (es-AR), una toma por frase.
# Chico = es-AR-TomasNeural (más lento y grave, cansado). Abuela = es-AR-ElenaNeural (más lenta y grave, mayor).
# Uso: python voces.py SALIDA_DIR
import sys, os, asyncio, certifi
CA = "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA): certifi.where = lambda: CA
import edge_tts
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
V = {"C": ("es-AR-TomasNeural", "-10%", "-8Hz"), "A": ("es-AR-ElenaNeural", "-16%", "-38Hz")}
FR = [
 ("c1", "C", "Abue, hace un año que no me sale una."),
 ("a1", "A", "¿Qué pasó?"),
 ("c2a", "C", "Antes me sacaba nueves y jugaba de titular."),
 ("c2b", "C", "Ahora estudio el doble y desapruebo igual."),
 ("c2c", "C", "El domingo entré cinco minutos."),
 ("c2d", "C", "La única que tuve"),
 ("c2e", "C", "pegó en el palo."),
 ("a2", "A", "Seguí yendo, mi amor."),
 ("c3a", "C", "Eso hago, abue."),
 ("c3b", "C", "Estoy cansado."),
 ("c3c", "C", "Ya siento que no sirvo para nada."),
 ("a3", "A", "¿Estuviste cerca entonces, muchacho?"),
 ("c4", "C", "Sí."),
 ("a4a", "A", "Acá también lo estuvieron."),
 ("a4b", "A", "Seguí para adelante."),
]
async def una(k, who, txt):
    v, r, p = V[who]
    if k == "c3c": r, p = "-14%", "-14Hz"   # baja la voz en la última
    if k == "a4a": r = "-22%"                # íntimo
    c = edge_tts.Communicate(txt, v, rate=r, pitch=p)
    with open(f"{out}/{k}.mp3", "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])
async def main():
    for k, w, t in FR: await una(k, w, t)
asyncio.run(main())
for k, w, t in FR: print(k, w, t)
