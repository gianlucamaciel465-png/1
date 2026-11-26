# Voz dirigida de Roccé (26/11/2026): reemplaza a Firme 04 (Gianluca: «cambiá a una voz más agradable… que tenga momentos
# en los que grita, desafina, habla despacio… dopamínica hasta la voz, pero bien medido en el momento justo y sin pasarse»).
# Motor: edge-tts (servicio de lectura en voz alta de Microsoft Edge), voz es-AR-TomasNeural por defecto, sin el tratamiento Firme.
# La interpretación se marca por tramo en el guion y se resuelve con prosodia de edge-tts + Praat (parselmouth) + FFmpeg.
#
# Guion TSV: id<TAB>texto dirigido. Tramos separados por « | », cada uno con su marca al principio:
#   [normal] [rapido] [lento] [bajo] (cerca y despacio) [firme] [energico] [grito] [pausa 0.3]
#   ^palabra = se le quiebra la voz en esa palabra (sube ~7 semitonos 90 ms y vuelve: «desafina»). Usar 1 por pieza.
#   Ej.: w3<TAB>[grito] ¡En el veinti^trés!
#        w56<TAB>[lento] Significa una sola cosa: | [pausa 0.3] | [firme] seguir hasta lograrlo.
# En el texto que se sintetiza: «Royé» por Roccé, «Fáunders Privé» por Founders Privée, «Blac Fraidei» por Black Friday,
# números en palabras. En pantalla, siempre la grafía real.
# Uso (en voz-env): python -I voz_dirigida.py GUION.tsv SALIDA_DIR [VOZ]
# Salida: <id>.wav (48 kHz mono) + voz.json con duración de cada frase y el comienzo de cada tramo.
import sys, os, re, json, subprocess, asyncio
import numpy as np
import certifi
CA = "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):
    certifi.where = lambda: CA
import edge_tts
import parselmouth
from parselmouth.praat import call

SR = 48000
guion, out = sys.argv[1], sys.argv[2]
VOZ = sys.argv[3] if len(sys.argv) > 3 else "es-AR-TomasNeural"
os.makedirs(out, exist_ok=True)

# estilo: (rate, pitch, ganancia dB, filtros FFmpeg)
ESTILOS = {
    "normal": ("+4%", "+0Hz", 0.0, ""),
    "rapido": ("+13%", "+2Hz", 0.0, ""),
    "lento": ("-14%", "-4Hz", -0.5, ""),
    "bajo": ("-12%", "-7Hz", -2.5, "bass=g=3:f=180,treble=g=-2.5:f=6000"),
    "firme": ("-6%", "-3Hz", 1.0, "acompressor=threshold=0.12:ratio=3:attack=5:release=80"),
    "energico": ("+9%", "+16Hz", 1.0, ""),
    "grito": ("+10%", "+30Hz", 0.0, ""),
}


async def sintetizar(texto, rate, pitch, mp3):
    c = edge_tts.Communicate(texto, VOZ, rate=rate, pitch=pitch, boundary="WordBoundary")
    pal = []
    with open(mp3, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                pal.append((ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]))
    return pal


def leer(p):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f64le", "-"])
    return np.frombuffer(raw, np.float64).copy()


def escribir(p, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s24le", p],
                   input=x.astype(np.float64).tobytes(), check=True)


def filtrar(x, af):
    if not af:
        return x
    raw = subprocess.run(["ffmpeg", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", af,
                          "-f", "f64le", "-"], input=x.tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float64).copy()


def recortar(x, pal, umbral=-45):
    env = np.convolve(np.abs(x), np.ones(480) / 480, "same")
    lim = 10 ** (umbral / 20) * max(env.max(), 1e-9)
    idx = np.where(env > lim)[0]
    if len(idx) == 0:
        return x, pal
    a = max(0, idx[0] - int(0.02 * SR)); b = min(len(x), idx[-1] + int(0.08 * SR))
    return x[a:b], [(o - a / SR, d, w) for o, d, w in pal]


def praat(x, f):
    """f(sound) -> sound de parselmouth; mantiene la duración."""
    s = parselmouth.Sound(x, sampling_frequency=SR)
    r = f(s)
    return r.values[0].astype(np.float64)


def subir_tono(s, semitonos, rango):
    med = call(s.to_pitch(), "Get quantile", 0, 0, 0.5, "Hertz")
    if not med or np.isnan(med):
        return s
    return call(s, "Change gender", 75, 600, 1.0, med * 2 ** (semitonos / 12), rango, 1.0)


def quebrar(s, t0, t1, factor=1.5):
    m = call(s, "To Manipulation", 0.01, 75, 700)
    pt = call(m, "Extract pitch tier")
    call(pt, "Multiply frequencies", t0, t1, factor)
    call([pt, m], "Replace pitch tier")
    return call(m, "Get resynthesis (overlap-add)")


def saturar(x, drive):
    p = np.abs(x).max() + 1e-9
    y = np.tanh(drive * x / p) / np.tanh(drive)
    return y * p


def sala(x, mezcla=0.12, dur=0.22):
    n = int(dur * SR)
    rng = np.random.default_rng(5)
    ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / (0.055 * SR))
    ir /= np.sqrt((ir ** 2).sum())
    w = np.convolve(x, ir)[: len(x)]
    return x + mezcla * w


def normalizar(x, pico_db=-3.0):
    return x / (np.abs(x).max() + 1e-9) * 10 ** (pico_db / 20)


def tramo(est, texto, tmp):
    rate, pitch, gan, af = ESTILOS[est]
    quiebre = None
    m = re.search(r"\^(\w+)", texto)
    if m:
        quiebre = m.group(1)
        texto = texto.replace("^", "")
    pal = asyncio.run(sintetizar(texto, rate, pitch, tmp))
    x = leer(tmp)
    x, pal = recortar(x, pal)
    if est == "grito":
        x = praat(x, lambda s: subir_tono(s, 2.5, 1.35))
    if quiebre:
        cand = [p for p in pal if quiebre.lower() in p[2].lower().replace("¡", "").replace("!", "")] or pal[-1:]
        o, d, _ = cand[0]
        t0 = o + d * 0.30; t1 = t0 + 0.09
        x = praat(x, lambda s: quebrar(s, t0, t1, 1.5))
    x = filtrar(x, "highpass=f=80" + ("," + af if af else ""))
    if est == "grito":
        x = sala(saturar(x, 2.0), 0.14)
    elif est == "energico":
        x = saturar(x, 1.3)
    x = normalizar(x) * 10 ** (gan / 20)
    return x, pal


frases = {}
for ln in open(guion, encoding="utf-8"):
    ln = ln.rstrip("\n")
    if not ln.strip() or ln.startswith("#"):
        continue
    fid, txt = ln.split("\t", 1)
    partes = []; t = 0.0; tramos = []
    for i, seg in enumerate([s.strip() for s in txt.split("|")]):
        m = re.match(r"\[(\w+)(?:\s+([\d.]+))?\]\s*(.*)", seg)
        est, num, texto = m.group(1), m.group(2), m.group(3)
        if est == "pausa":
            n = int(float(num) * SR); partes.append(np.zeros(n)); t += n / SR
            continue
        x, pal = tramo(est, texto, os.path.join(out, f"{fid}_{i}.mp3"))
        tramos.append(dict(estilo=est, texto=texto, inicio=round(t, 3), palabras=[(round(t + o, 3), w) for o, d, w in pal]))
        partes.append(x); t += len(x) / SR
    y = np.concatenate(partes)
    escribir(os.path.join(out, f"{fid}.wav"), y)
    frases[fid] = dict(texto=txt, duracion=round(len(y) / SR, 3), tramos=tramos)
    print(f"{fid}: {len(y) / SR:5.2f} s  {txt}")
json.dump(dict(voz=VOZ, motor="edge-tts + Praat (parselmouth) + FFmpeg · scripts/voz/voz_dirigida.py", frases=frases),
          open(os.path.join(out, "voz.json"), "w"), ensure_ascii=False, indent=1)
