#!/usr/bin/env bash
# Instala faster-whisper en un entorno aislado (no toca el Python del sistema).
# No persiste entre sesiones en la nube: correrlo cuando haga falta transcribir (~5–10 min).
# Uso: scripts/instalar_transcripcion.sh [carpeta_entorno]   (por defecto ~/.whisper-env)
# Después: ~/.whisper-env/bin/python -I scripts/transcribir.py small ARCHIVO es
#          (el modelo "small", ~460 MB, se descarga solo la primera vez)
set -euo pipefail
ENV="${1:-$HOME/.whisper-env}"
python3 -m venv "$ENV"
WH=$(mktemp -d)
# PyAV desde pip llegó a bajar a pocos KB/s; con curl tarda ~1 min. Se baja primero.
U=$(curl -sS https://pypi.org/simple/av/ | grep -oE 'https://files.pythonhosted.org[^"#]*/av-[0-9.]+-cp3[0-9]+-abi3-manylinux_2_28_x86_64\.whl' | tail -1 || true)
if [ -n "$U" ]; then curl -sS --retry 3 -o "$WH/$(basename "$U")" "$U"; fi
"$ENV/bin/pip" install -q --find-links "$WH" --default-timeout 60 faster-whisper
"$ENV/bin/python" -c "import faster_whisper; print('faster-whisper', faster_whisper.__version__, 'instalado en', '$ENV')"
