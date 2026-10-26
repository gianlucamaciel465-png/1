# Transcripción con marcas de tiempo (faster-whisper). Uso: transcribir.py modelo archivo [idioma|auto] [vad:1/0]
import sys, time, subprocess
import numpy as np
from faster_whisper import WhisperModel
modelo, archivo = sys.argv[1], sys.argv[2]
idioma = None if len(sys.argv) < 4 or sys.argv[3] == "auto" else sys.argv[3]
vad = len(sys.argv) < 5 or sys.argv[4] == "1"
t0 = time.time()
m = WhisperModel(modelo, device="cpu", compute_type="int8")
# Audio decodificado con FFmpeg (16 kHz mono) para no depender de PyAV.
pcm = subprocess.run(['ffmpeg','-v','error','-i',archivo,'-vn','-ac','1','-ar','16000','-f','f32le','-'],capture_output=True,check=True).stdout
audio = np.frombuffer(pcm, dtype=np.float32)
segs, info = m.transcribe(audio, language=idioma, vad_filter=vad, word_timestamps=True, beam_size=5,
                          condition_on_previous_text=False)
print(f"# {archivo}\n# idioma detectado: {info.language} (p={info.language_probability:.2f}); duración audio {info.duration:.2f}s; VAD={'sí' if vad else 'no'}")
for s in segs:
    print(f"[{s.start:6.2f} → {s.end:6.2f}] p_sin_voz={s.no_speech_prob:.2f} logprob={s.avg_logprob:.2f} | {s.text.strip()}")
    print("      palabras: " + " ".join(f"{w.word.strip()}@{w.start:.2f}" for w in (s.words or [])))
print(f"# tiempo de proceso: {time.time()-t0:.1f}s")
