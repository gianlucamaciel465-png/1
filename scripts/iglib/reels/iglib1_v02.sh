#!/bin/bash
# Receta completa de IGLIB-1 «La tercera tarjeta» v02 (con locución «Roccé — Firme 04», 10_roma_locucion_G1.1.md).
# Se puede volver a correr; cada etapa reutiliza lo hecho. La v01 (iglib1.sh) queda intacta.
#   0. locución: voz/iglib1_locucion.tsv → scripts/proxima/locucion.py (edge-tts 7.3.1 es-AR-ElenaNeural +11 % −20 Hz +
#      scripts/voz/tratamiento_firme.py). Necesita voz-env (scripts/instalar_entorno.sh DIR voz) y salida al servicio de Edge.
#   1. preparar_iglib1.py  tramos de video (7859 15–128 y 139–249 con blanco corregido y seguimiento; Mixkit cuadro a cuadro)
#   2. render.js           compositor en Chromium (hoja.js + iglib1_v02.js), canvas al doble
#   3. sonido.py iglib1v2  voz + efectos + ambiente real de 7859 + música propia; fondo atenuado en cada frase; voz/fondo medido
#   4. montar.sh           másteres con y sin música (−14 LUFS, pico ≤ −1 dBTP)
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd); T=/home/user/1/TRABAJO/iglib/reels/iglib1; PYE=/home/user/1/TRABAJO/iglib/env/bin/python
VOZ=/home/user/1/TRABAJO/iglib/voz/iglib1; VOZ_PY=${VOZ_PY:-/home/user/1/TRABAJO/iglib/voz-env/bin/python}
OUT=${OUT:-/mnt/project-files/piezas/IGLIB_funcion_libertadores}
[ -f "$VOZ/v14.wav" ] || VOZ_PY=$VOZ_PY python3 /home/user/1/scripts/proxima/locucion.py "$D/voz/iglib1_locucion.tsv" "$VOZ"
$PYE "$D/preparar_iglib1.py" "$T"
$PYE -c "import json; t=json.load(open('$T/src/7859_estampado.json')); c=json.load(open('$T/src/7859_cta.json')); json.dump({'src':'$T/src','logo':'/home/user/1/LOGO/rocce_logo.png','track':t,'cta':c}, open('$T/datos_v02.json','w'))"
rm -rf "$T/cuadros_v02"; NODE_PATH=$(npm root -g) node "$D/render.js" iglib1_v02 "$T/datos_v02.json" "$T/cuadros_v02"
$PYE "$D/sonido.py" iglib1v2 "$T/audio_v02" "$VOZ"
PY=$PYE bash "$D/montar.sh" "$T/cuadros_v02" "$T/audio_v02" "$OUT" IGLIB-1 v02
