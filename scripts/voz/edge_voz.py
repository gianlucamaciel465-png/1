# Síntesis con cualquier voz de edge-tts (servicio de lectura en voz alta de Microsoft Edge), sin el tratamiento Firme.
# Uso: python edge_voz.py VOZ "texto" salida.mp3 [rate] [pitch]   ·   python edge_voz.py --lista
import sys, os
import certifi
CA = "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):
    certifi.where = lambda: CA
import asyncio, edge_tts

async def lista():
    for v in await edge_tts.list_voices():
        if v["Locale"].startswith("es-") or "Multilingual" in v["ShortName"]:
            print(v["ShortName"], v["Gender"], ",".join(v.get("VoiceTag", {}).get("VoicePersonalities", [])))

async def main(voz, texto, salida, rate, pitch):
    c = edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch)
    subs = []
    with open(salida, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] in ("WordBoundary", "SentenceBoundary"):
                subs.append((ch["type"], ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]))
    with open(salida + ".palabras.tsv", "w") as f:
        for t, o, d, w in subs: f.write(f"{t}\t{o:.3f}\t{d:.3f}\t{w}\n")

if sys.argv[1] == "--lista":
    asyncio.run(lista())
else:
    voz, texto, salida = sys.argv[1], sys.argv[2], sys.argv[3]
    rate = sys.argv[4] if len(sys.argv) > 4 else "+0%"
    pitch = sys.argv[5] if len(sys.argv) > 5 else "+0Hz"
    asyncio.run(main(voz, texto, salida, rate, pitch))
    print(salida)
