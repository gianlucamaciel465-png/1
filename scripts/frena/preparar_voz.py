# Prepara las seis frases de la locución de ROCCE_lo_que_te_frena_v02 como p1.wav … p6.wav (48 kHz mono, recortadas).
#   Modo nota:  python preparar_voz.py nota GRABACION.(wav|m4a|ogg|mp4) SALIDA_DIR
#               Una sola grabación (la nota de voz de Gianluca): se transcribe con marcas por palabra, se alinea con
#               el texto esperado y se corta cada frase por sus palabras de inicio y fin (con un margen que no come
#               las colas). Si una frase se dijo varias veces, queda la que alinea primero: para elegir otra
#               toma, recortar la nota antes o pasar las frases sueltas con el modo tomas.
#   Modo tomas: python preparar_voz.py tomas DIR_TOMAS SALIDA_DIR
#               Tomas sueltas f{i}_*.wav (voz guía de voz_chatterbox.py): por frase, la toma cuya transcripción más se
#               parece al texto (a igual parecido, la más corta), recortando silencios.
# Usa faster-whisper (modelo small, en caché). Escribe SALIDA_DIR/preparacion.json con lo elegido y lo transcripto.
# La transcripción no equivale a escuchar: "Roccé", "founder" y el voseo se revisan de oído.
import sys, os, json, glob, re, subprocess, unicodedata, difflib
import numpy as np

FRASES = ["Fracasé.", "Me incomodé.", "Y acá estoy.", "Ahora te toca a vos.",
          "El primero de noviembre, hacete founder de Roccé y creá lo que viene con nosotros.",
          "Mandanos FOUNDERS y pedí acceso."]
modo, entrada, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)

def norm(s):
    s = unicodedata.normalize("NFD", s.lower()); s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z ]", " ", s).split()

def leer(p, sr=48000):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"])
    return np.frombuffer(raw, np.float32).copy(), sr

def escribir(p, x, sr=48000):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le", p],
                   input=x.astype(np.float32).tobytes(), check=True)

def recortar(x, sr, umbral_db=-38, margen=(0.05, 0.10)):
    """Quita silencio adelante y atrás (umbral relativo al pico, ventanas de 10 ms) y aplica fundidos de 12 ms."""
    w = int(0.01 * sr); n = len(x) // w
    e = np.array([np.sqrt(np.mean(x[i * w:(i + 1) * w] ** 2)) + 1e-9 for i in range(n)])
    db = 20 * np.log10(e / e.max())
    on = np.where(db > umbral_db)[0]
    if len(on) == 0: return x, 0.0
    a = max(0, on[0] * w - int(margen[0] * sr)); b = min(len(x), (on[-1] + 1) * w + int(margen[1] * sr))
    y = x[a:b].copy(); f = int(0.012 * sr)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y, a / sr

from faster_whisper import WhisperModel
modelo = WhisperModel("small", device="cpu", compute_type="int8")
def transcribir(p):
    audio, _ = leer(p, 16000)                     # audio ya decodificado (la versión de av instalada no abre rutas)
    segs, _ = modelo.transcribe(audio, language="es", word_timestamps=True, beam_size=5,
                                initial_prompt="Roccé, founder, FOUNDERS.")   # solo vocabulario: con el guion completo inventa el texto
    pal = [(w.word, w.start, w.end) for s in segs for w in s.words]
    return pal

info = {"modo": modo, "frases": []}
if modo == "tomas":
    for i, fr in enumerate(FRASES, 1):
        mejores = []
        for p in sorted(glob.glob(os.path.join(entrada, f"f{i}_*.wav"))):
            pal = transcribir(p); txt = "".join(w[0] for w in pal).strip()
            sim = difflib.SequenceMatcher(None, " ".join(norm(fr)), " ".join(norm(txt))).ratio()
            x, sr = leer(p); a = 0.0
            # recorte por palabras reconocidas (la voz sintética a veces agrega ruido después de terminar)
            if pal:
                a, b = max(0, pal[0][1] - 0.06), pal[-1][2] + 0.15
                x = x[int(a * sr):int(b * sr)]
            y, a2 = recortar(x, sr)
            pals = [(w.strip(), round(ws - a - a2, 3), round(we - a - a2, 3)) for w, ws, we in pal]
            mejores.append((round(sim, 3), -len(y) / sr, p, txt, y, pals))
        mejores.sort(key=lambda m: (m[0], m[1]), reverse=True)
        sim, nd, p, txt, y, pals = mejores[0]
        escribir(os.path.join(out, f"p{i}.wav"), y)
        info["frases"].append({"frase": fr, "toma": os.path.basename(p), "transcripcion": txt, "parecido": sim,
                               "duracion": round(-nd, 3), "palabras": pals,
                               "otras": [(os.path.basename(m[2]), m[0], m[3]) for m in mejores[1:]]})
        print(f"p{i}: {os.path.basename(p)}  {-nd:.2f} s  parecido {sim}  «{txt}»", flush=True)
else:
    x, sr = leer(entrada)
    tmp = os.path.join(out, "_nota.wav"); escribir(tmp, x)
    pal = transcribir(tmp)
    rec = [(norm(w)[0] if norm(w) else "", a, b) for w, a, b in pal]
    esperadas = []; frase_de = []
    for i, fr in enumerate(FRASES):
        for w in norm(fr): esperadas.append(w); frase_de.append(i)
    # alineación por palabras entre el texto esperado y lo transcripto
    sm = difflib.SequenceMatcher(None, esperadas, [r[0] for r in rec], autojunk=False)
    mapa = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): mapa[blk.a + k] = blk.b + k
    for i, fr in enumerate(FRASES):
        idx = [j for j, f in enumerate(frase_de) if f == i]
        ok = [mapa[j] for j in idx if j in mapa]
        if not ok:
            print(f"p{i + 1}: NO ENCONTRADA en la nota ({fr})"); info["frases"].append({"frase": fr, "error": "no encontrada"}); continue
        a, b = max(0.0, rec[min(ok)][1] - 0.08), rec[max(ok)][2] + 0.14
        y, a2 = recortar(x[int(a * sr):int(b * sr)], sr)
        escribir(os.path.join(out, f"p{i + 1}.wav"), y)
        txt = "".join(pal[k][0] for k in range(min(ok), max(ok) + 1)).strip()
        pals = [(pal[k][0].strip(), round(pal[k][1] - a - a2, 3), round(pal[k][2] - a - a2, 3)) for k in range(min(ok), max(ok) + 1)]
        info["frases"].append({"frase": fr, "desde": round(a, 3), "hasta": round(b, 3), "transcripcion": txt, "palabras": pals,
                               "palabras_alineadas": f"{len(ok)}/{len(idx)}", "duracion": round(len(y) / sr, 3)})
        print(f"p{i + 1}: {a:.2f}–{b:.2f} s  ({len(ok)}/{len(idx)} palabras)  «{txt}»", flush=True)
    os.remove(tmp)
json.dump(info, open(os.path.join(out, "preparacion.json"), "w"), indent=1, ensure_ascii=False)
