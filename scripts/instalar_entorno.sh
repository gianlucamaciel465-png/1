#!/usr/bin/env bash
# Reinstala los entornos de Python usados por las recetas, con las versiones exactas que funcionaron
# (congeladas el 27/10/2026 en scripts/requisitos/*.txt). No persisten entre sesiones: cada sesión nueva
# arranca en una máquina limpia; lo que persiste es este repo.
#   whisper-env  faster-whisper 1.2.1 (transcripción; el modelo "small" se baja solo la primera vez, ~460 MB)
#   demucs-env   demucs 4.1 + torch CPU (+ diffusers/transformers/opencv/librosa para MuseTalk)
#   tts-env      Chatterbox Multilingual 0.1.7 (Python 3.11; pesos t3_mtl23ls_v2 ~3 GB se bajan al primer uso)
#   ytdlp-env    yt-dlp 2026.10.21 (descarga de referencias públicas)
#   voz-env      edge-tts 7.3.1 + praat-parselmouth 0.4.7 + scipy/soundfile (voz de marca Firme 04 y música sintetizada;
#                edge-tts necesita salida a speech.platform.bing.com — ver scripts/voz/BANCO_VOCAL.md)
#   bpy-env      Blender 5.0.1 como módulo de Python (Python 3.11; ~375 MB): escenas 3D con Cycles en CPU
#                (scripts/hielo/escena.py). No se instala por defecto: pedirlo con "bpy".
# Modelos de sincronización labial: scripts/instalar_doblaje.sh (reutiliza los entornos si ya existen).
# Uso: scripts/instalar_entorno.sh [CARPETA] [whisper demucs tts ytdlp voz]   (por defecto: todos, en $S o ./.entornos)
# Las recetas buscan los entornos en $S (variable de entorno): exportar S=CARPETA antes de usarlas.
set -euo pipefail
cd "$(dirname "$0")/.."
D=${1:-${S:-$PWD/.entornos}}; shift || true
QUE=${*:-whisper demucs tts ytdlp voz}
CPU=https://download.pytorch.org/whl/cpu
mkdir -p "$D"
for e in $QUE; do
  [ -x "$D/$e-env/bin/python" ] && { echo "$e-env ya existe"; continue; }
  py=python3; { [ "$e" = tts ] || [ "$e" = bpy ]; } && py=/usr/bin/python3.11
  $py -m venv "$D/$e-env"
  "$D/$e-env/bin/pip" install -q --default-timeout 60 --extra-index-url $CPU -r scripts/requisitos/$e.txt
  echo "$e-env instalado en $D"
done
