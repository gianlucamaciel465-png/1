#!/bin/bash
# Receta completa de ROCCE_01_HIELO_REVELACION_v01 (bloque de hielo 3D con la remera negra real + tomas de Gianluca).
# Necesita: bpy-env (scripts/instalar_entorno.sh "" bpy), $S/demucs-env (OpenCV, scipy), PRODUCTO/negra_espalda_arena_*.png,
# ORIGINALES/IMG_7884/7885/7887.mov. El render 3D tarda ≈ 2,5 h en 4 CPU (141 cuadros a 720×1280, 28 muestras).
# Uso: S=CARPETA_ENTORNOS scripts/hielo_v01.sh TRABAJO_DIR
set -euo pipefail
cd "$(dirname "$0")/.."
R=$PWD; T=${1:-$R/TRABAJO/hielo}; PY=$S/demucs-env/bin/python; H=$R/scripts/hielo
mkdir -p "$T/hielo"; cd "$T"
$PY $H/textura_remera.py $R/PRODUCTO/negra_espalda_arena_DFDC5DED.png hielo/remera_espalda.png
$S/bpy-env/bin/python $H/escena.py hielo/remera_espalda.png hielo/v01            # arma la escena (escena.blend + escena.json)
nice -n 15 $S/bpy-env/bin/python $H/render.py hielo/v01/escena.blend hielo/v01/r67 0 140 67 28
$PY $H/suavizar_marcas.py hielo/v01/r67 hielo/v01/r67_post             # marcas de impacto: de estrella a escarcha
python3 $H/etiqueta.py hielo/etiqueta.png
PY=$PY $H/montar.sh "$T" hielo/v01/r67_post "$R/EXPORTACIONES/ROCCE_01_HIELO_REVELACION_v01.mp4"
