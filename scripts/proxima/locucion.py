# Locución de ROCCE_proxima con el perfil de marca "Roccé — Firme 04" (banco vocal: ver scripts/voz/BANCO_VOCAL.md).
# Cada frase se sintetiza por separado con la voz base documentada (es-AR-ElenaNeural, rate +11 %, pitch −20 Hz) y
# recibe el tratamiento documentado (scripts/voz/tratamiento_firme.py: formants 0,94 · pitch ×0,93 · saturación 0,055 ·
# pausas internas ≤ 180 ms). El factor de tono es relativo, así que todas las frases quedan con la misma identidad.
# Después se recorta el silencio de cada punta (umbral −45 dB, 30 ms antes y 90 ms después de la voz).
# En el texto que se sintetiza, la marca se escribe "Royé" y "founders" se escribe "fáunders" (pronunciación);
# en pantalla siempre es Roccé / FOUNDERS.
#
# Uso: VOZ_PY=.../voz-env/bin/python python3 locucion.py GUION.tsv SALIDA_DIR
#   GUION.tsv: id<TAB>texto a sintetizar (una frase por línea)
#   Sale: SALIDA_DIR/<id>_base.mp3 (síntesis sin tratar), <id>_tratada.wav, <id>.wav (recortada, la que se usa)
#         y SALIDA_DIR/locucion.json (texto, duración, recorte).
import os, sys, json, subprocess
import numpy as np

guion, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
AQUI = os.path.dirname(os.path.abspath(__file__)); VOZ = os.path.join(AQUI, "..", "voz")
PY = os.environ.get("VOZ_PY", sys.executable)
SR = 48000

def leer(p):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], stdin=subprocess.DEVNULL)
    return np.frombuffer(raw, np.float32).astype(np.float64)

def recortar(x, umbral=-45, antes=0.03, despues=0.09):
    w = int(0.01 * SR); n = len(x) // w
    e = np.array([np.sqrt(np.mean(x[i * w:(i + 1) * w] ** 2)) + 1e-12 for i in range(n)])
    v = np.where(20 * np.log10(e / e.max()) > umbral)[0]
    a = max(0, v[0] * w - int(antes * SR)); b = min(len(x), (v[-1] + 1) * w + int(despues * SR))
    y = x[a:b].copy(); fi, fo = int(0.005 * SR), int(0.03 * SR)
    y[:fi] *= np.linspace(0, 1, fi); y[-fo:] *= np.linspace(1, 0, fo)
    return y, a / SR, b / SR

info = []
for linea in open(guion, encoding="utf-8"):
    if not linea.strip() or linea.startswith("#"): continue
    fid, texto = linea.rstrip("\n").split("\t", 1)
    base, trat, fin = (os.path.join(out, f"{fid}{s}") for s in ("_base.mp3", "_tratada.wav", ".wav"))
    if not os.path.exists(base):
        subprocess.run([PY, "-I", os.path.join(VOZ, "edge_firme.py"), texto, base], check=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    subprocess.run([PY, "-I", os.path.join(VOZ, "tratamiento_firme.py"), base, trat], check=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    y, a, b = recortar(leer(trat))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s24le", fin],
                   input=y.tobytes(), check=True)
    info.append(dict(id=fid, texto_sintetizado=texto, duracion=round(len(y) / SR, 3), recorte=[round(a, 3), round(b, 3)]))
    print(f"{fid}: {len(y) / SR:5.2f} s  {texto}")
json.dump(dict(perfil="Roccé — Firme 04", motor="edge-tts 7.3.1 (servicio de lectura en voz alta de Microsoft Edge) + tratamiento_firme.py",
               frases=info), open(os.path.join(out, "locucion.json"), "w"), indent=1, ensure_ascii=False)
