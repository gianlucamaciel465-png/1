#!/bin/bash
# Receta completa de IGLIB-1 «La tercera tarjeta» v01 (se puede volver a correr; cada etapa reutiliza lo hecho).
#   1. preparar_iglib1.py  tramos de video (7859 con blanco corregido y seguimiento del estampado; Mixkit cuadro a cuadro)
#   2. render.js           compositor en Chromium (hoja.js + iglib1.js), canvas al doble
#   3. sonido.py           efectos sintetizados, ambiente real de 7859, música propia
#   4. montar.sh           másteres con y sin música
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd); T=/home/user/1/TRABAJO/iglib/reels/iglib1; PYE=/home/user/1/TRABAJO/iglib/env/bin/python
OUT=${OUT:-/mnt/project-files/piezas/IGLIB_funcion_libertadores}
$PYE "$D/preparar_iglib1.py" "$T"
$PYE -c "import json; t=json.load(open('$T/src/7859_estampado.json')); json.dump({'src':'$T/src','logo':'/home/user/1/LOGO/rocce_logo.png','track':t}, open('$T/datos.json','w'))"
rm -rf "$T/cuadros"; NODE_PATH=$(npm root -g) node "$D/render.js" iglib1 "$T/datos.json" "$T/cuadros"
$PYE "$D/sonido.py" iglib1 "$T/audio"
PY=$PYE bash "$D/montar.sh" "$T/cuadros" "$T/audio" "$OUT" IGLIB-1 v01
