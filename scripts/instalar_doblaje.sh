#!/usr/bin/env bash
# Instala lo necesario para doblaje en CPU (probado 26/10/2026): no persiste entre sesiones.
#  - demucs-env: torch CPU + demucs (separación voz/música) + diffusers/transformers/opencv/librosa (MuseTalk)
#  - tts-env (Python 3.11): Chatterbox Multilingual 0.1.7 (voz en español con timbre de referencia)
#  - mt_models: MuseTalk 1.5 (UNet), VAE sd-vae-ft-mse y whisper-tiny (~3,7 GB desde Hugging Face)
# Licencias de uso comercial permitido: MuseTalk MIT, sd-vae-ft-mse MIT, whisper-tiny Apache-2.0, Chatterbox MIT.
# Uso: scripts/instalar_doblaje.sh [CARPETA]   (por defecto $S o el directorio actual)
#      Después: S=CARPETA scripts/doblaje_r13_v02.sh ...   (~25 min de instalación + ~6,5 s por cuadro doblado)
set -euo pipefail
D=${1:-${S:-$PWD}}; mkdir -p "$D"; cd "$D"
CPU=https://download.pytorch.org/whl/cpu
if [ ! -x demucs-env/bin/python ]; then
  python3 -m venv demucs-env
  demucs-env/bin/pip install -q --default-timeout 60 torch torchaudio --index-url $CPU
  demucs-env/bin/pip install -q --default-timeout 60 demucs soundfile diffusers transformers opencv-python-headless librosa
fi
if [ ! -x tts-env/bin/python ]; then
  /usr/bin/python3.11 -m venv tts-env
  tts-env/bin/pip install -q --default-timeout 60 torch==2.6.0 torchaudio==2.6.0 --index-url $CPU
  tts-env/bin/pip install -q --default-timeout 60 chatterbox-tts==0.1.7
fi
M=mt_models; mkdir -p $M/musetalkV15 $M/sd-vae $M/whisper
while read -r repo file dest; do
  [ -s "$M/$dest" ] || curl -sSfL --retry 4 "https://huggingface.co/$repo/resolve/main/$file" -o "$M/$dest"
  echo "ok $dest"
done <<'EOF'
TMElyralab/MuseTalk musetalkV15/musetalk.json musetalkV15/musetalk.json
TMElyralab/MuseTalk musetalkV15/unet.pth musetalkV15/unet.pth
stabilityai/sd-vae-ft-mse config.json sd-vae/config.json
stabilityai/sd-vae-ft-mse diffusion_pytorch_model.safetensors sd-vae/diffusion_pytorch_model.safetensors
openai/whisper-tiny config.json whisper/config.json
openai/whisper-tiny model.safetensors whisper/model.safetensors
openai/whisper-tiny preprocessor_config.json whisper/preprocessor_config.json
openai/whisper-tiny generation_config.json whisper/generation_config.json
EOF
demucs-env/bin/python -c "import diffusers, transformers, cv2, librosa; print('MuseTalk deps ok')"
tts-env/bin/python -c "from chatterbox.mtl_tts import ChatterboxMultilingualTTS; print('chatterbox ok')"
