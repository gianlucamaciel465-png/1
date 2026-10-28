# Marcas de tiempo por palabra de cada frase de la locución (faster-whisper "small"), para sincronizar textos y cortes
# con palabras concretas ("noviembre", "cien", "fáunders", "porcentaje"…). Solo vocabulario como contexto: con el guion
# entero como initial_prompt Whisper inventa el texto esperado.
# Uso: whisper-env/bin/python -I palabras.py VOZ_DIR   → agrega "palabras" a VOZ_DIR/locucion.json
import sys, os, json, subprocess
import numpy as np
from faster_whisper import WhisperModel

d = sys.argv[1]; J = os.path.join(d, "locucion.json"); loc = json.load(open(J))
m = WhisperModel("small", device="cpu", compute_type="int8")
for f in loc["frases"]:
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(d, f["id"] + ".wav"), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, stdin=subprocess.DEVNULL).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(a, language="es", word_timestamps=True, beam_size=5, initial_prompt="Roccé, founders, Gianluca.")
    f["palabras"] = [[w.word.strip(), round(w.start, 2), round(w.end, 2)] for s in segs for w in s.words]
    print(f["id"], " ".join(f"{w}[{s}]" for w, s, e in f["palabras"]))
json.dump(loc, open(J, "w"), indent=1, ensure_ascii=False)
