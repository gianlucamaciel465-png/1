#!/usr/bin/env bash
# ROCCE_proxima_v01 — "La próxima empieza con vos" (27–28/10/2026). Reel nuevo desde cero (concepto: creación compartida).
# Voz: perfil de marca "Roccé — Firme 04" (banco vocal: scripts/voz/BANCO_VOCAL.md). Música original sintetizada.
# CTA único en voz, pantalla y descripción: escribir FOUNDERS por mensaje a @rocce.ar.
#
# Uso: scripts/proxima_v01.sh [SALIDA]
#   VOZ=carpeta con L1.wav … L8.wav + locucion.json. Si no existe, se genera con scripts/proxima/locucion.py
#   (síntesis en línea con edge-tts + tratamiento Firme 04). Para rehacer EXACTAMENTE v01, bajar la locución usada
#   del banco vocal privado (ver BANCO_VOCAL.md, carpeta locuciones/proxima_v01/) a TRABAJO/proxima/voz.
#   Para usar la voz real de Gianluca: grabar las 8 frases de scripts/proxima/guion_v01.tsv, recortarlas como L1…L8.wav,
#   correr palabras.py y volver a correr esta receta (la línea de tiempo sale de la duración de cada frase).
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-EXPORTACIONES/ROCCE_proxima_v01.mp4}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe"; exit 1; }
S=${S:-/tmp/claude-0/-home-user-1/bd43937f-7b34-55cc-a48c-8ac864032e15/scratchpad}
VOZ=${VOZ:-TRABAJO/proxima/voz}
if [ ! -f "$VOZ/L8.wav" ]; then
  VOZ_PY=$S/voz-env/bin/python python3 scripts/proxima/locucion.py scripts/proxima/guion_v01.tsv "$VOZ"
  $S/whisper-env/bin/python -I scripts/proxima/palabras.py "$VOZ"
fi
S=$S VOZ_PY=$S/voz-env/bin/python MEDIR=1 python3 scripts/proxima/montaje.py "$VOZ" "$OUT"
