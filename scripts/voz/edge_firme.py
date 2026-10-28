# Síntesis base del perfil "Roccé — Firme 04": es-AR-ElenaNeural (Microsoft, servicio en línea de lectura de Edge,
# vía edge-tts), rate +11 %, pitch −20 Hz. Después se aplica el tratamiento con tratamiento_firme.py.
# El transporte original de síntesis no está documentado; este es el camino recuperable con la voz base documentada.
# En este entorno el tráfico sale por un proxy con su propia CA: edge-tts usa certifi, así que se le indica esa CA
# (sin desactivar la verificación). Uso: python edge_firme.py "texto" salida.mp3 [rate] [pitch]
import sys, os
import certifi
CA = "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):
    certifi.where = lambda: CA
import asyncio, edge_tts

texto, salida = sys.argv[1], sys.argv[2]
rate = sys.argv[3] if len(sys.argv) > 3 else "+11%"
pitch = sys.argv[4] if len(sys.argv) > 4 else "-20Hz"

async def main():
    c = edge_tts.Communicate(texto, "es-AR-ElenaNeural", rate=rate, pitch=pitch)
    subs = []
    with open(salida, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] in ("WordBoundary", "SentenceBoundary"):
                subs.append((ch["type"], ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]))
    with open(salida + ".palabras.tsv", "w") as f:
        for t, o, d, w in subs: f.write(f"{t}\t{o:.3f}\t{d:.3f}\t{w}\n")
asyncio.run(main())
print(salida)
