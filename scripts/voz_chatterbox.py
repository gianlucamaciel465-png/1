# Genera tomas de voz en español con Chatterbox Multilingual (MIT), frase por frase.
# Uso: python voz_chatterbox.py REFERENCIA.wav SALIDA_DIR "frase 1" "frase 2" ...
#   REFERENCIA "-" = voz incorporada del modelo (sin clonar a nadie; sirve como voz guía provisoria).
#   TOMAS=2 limita las tomas por frase (por defecto 3).
# Hace 3 tomas por frase con distintas semillas y niveles de expresividad; la elección se hace después
# (transcripción con Whisper + duración).
import sys, os, torch, torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

ref, out = sys.argv[1], sys.argv[2]
ref = None if ref == "-" else ref
frases = sys.argv[3:]
os.makedirs(out, exist_ok=True)
torch.set_num_threads(os.cpu_count())
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
ajustes = [(0.5, 0.5, 1), (0.6, 0.4, 2), (0.45, 0.6, 3)][:int(os.environ.get("TOMAS", 3))]  # (exaggeration, cfg_weight, semilla)
if os.environ.get("AJUSTES"):   # p. ej. AJUSTES="0.5,0.5,1;0.7,0.3,4" (más expresiva y pausada)
    ajustes = [tuple(float(v) if i < 2 else int(v) for i, v in enumerate(a.split(","))) for a in os.environ["AJUSTES"].split(";")]
PREFIJO = os.environ.get("PREFIJO", "f")
for i, f in enumerate(frases):
    for ex, cfg, seed in ajustes:
        torch.manual_seed(seed)
        wav = m.generate(f, language_id="es", audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg)
        p = os.path.join(out, f"{PREFIJO}{i+1}_ex{ex}_cfg{cfg}_s{seed}.wav")
        torchaudio.save(p, wav, m.sr)
        print(p, round(wav.shape[-1] / m.sr, 2), "s", flush=True)
