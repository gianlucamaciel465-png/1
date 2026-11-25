#!/bin/bash
# Receta completa de IGLIB-2 «Nadie cambia» v02 (con locución «Roccé — Firme 04», 10_roma_locucion_G1.1.md), en loop.
# Se puede volver a correr; cada etapa reutiliza lo hecho.
#   0. locución: voz/iglib2_locucion.tsv → scripts/proxima/locucion.py (edge-tts 7.3.1 + tratamiento_firme.py; voz-env)
#   1. preparar_iglib2.py  tramos de video (8744, 44451 con la marca de la pelota desenfocada, 876 con el logo borrado,
#                          608; IMG_4627 e IMG_3375 HLG → SDR con blanco fijo por toma)
#   2. render.js           compositor en Chromium (hoja.js + iglib2_v02.js), canvas al doble
#   3. sonido.py iglib2v2  voz + efectos + mar real de 4627 + música propia; fondo atenuado en cada frase; voz/fondo medido
#   4. montar.sh           másteres con y sin música (−14 LUFS, pico ≤ −1 dBTP)
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd); T=/home/user/1/TRABAJO/iglib/reels/iglib2; PYE=/home/user/1/TRABAJO/iglib/env/bin/python
VOZ=/home/user/1/TRABAJO/iglib/voz/iglib2; VOZ_PY=${VOZ_PY:-/home/user/1/TRABAJO/iglib/voz-env/bin/python}
OUT=${OUT:-/mnt/project-files/piezas/IGLIB_funcion_libertadores}
[ -f "$VOZ/w12.wav" ] || VOZ_PY=$VOZ_PY python3 /home/user/1/scripts/proxima/locucion.py "$D/voz/iglib2_locucion.tsv" "$VOZ"
$PYE "$D/preparar_iglib2.py" "$T"
echo "{\"src\":\"$T/src\",\"logo\":\"/home/user/1/LOGO/rocce_logo.png\"}" > "$T/datos_v02.json"
rm -rf "$T/cuadros_v02"; NODE_PATH=$(npm root -g) node "$D/render.js" iglib2_v02 "$T/datos_v02.json" "$T/cuadros_v02"
$PYE "$D/sonido.py" iglib2v2 "$T/audio_v02" "$VOZ"
PY=$PYE bash "$D/montar.sh" "$T/cuadros_v02" "$T/audio_v02" "$OUT" IGLIB-2 v02
