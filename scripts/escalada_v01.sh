#!/bin/bash
# Receta completa de ROCCE_02_HACETE_FOUNDER_v01 (escalada de Neuron Visuals intervenida + placa Founders).
# Necesita: REFERENCIAS/REF_21_neuronvisuals_escalada_grabacion.mp4 (grabación de pantalla 1170×2532, solo local),
# PRODUCTO/negra_{frente,espalda}_arena_*.png, LOGO/rocce_logo.png y un Python con OpenCV + scipy ($S/demucs-env).
# Uso: S=CARPETA_ENTORNOS scripts/escalada_v01.sh TRABAJO_DIR
set -euo pipefail
cd "$(dirname "$0")/.."
R=$PWD; T=${1:-$R/TRABAJO/escalada}; PY=$S/demucs-env/bin/python; E=$R/scripts/escalada
mkdir -p "$T/an" "$T/pose" "$T/hielo"
REF=$R/REFERENCIAS/REF_21_neuronvisuals_escalada_grabacion.mp4
# 1. recorte del reel (sin la barra de estado ni la de comentarios) a 1080×1920, 30 fps
mkdir -p "$T/r2seq"
ffmpeg -v error -y -i "$REF" -vf "fps=30,crop=1170:2080:0:203,scale=1080:1920:flags=lanczos:in_range=pc:in_color_matrix=bt709:out_color_matrix=bt709,format=rgb24" "$T/r2seq/%04d.png" </dev/null
ffmpeg -v error -y -i "$REF" -vn -ac 2 -ar 48000 -c:a pcm_s16le "$T/an/r2_audio.wav" </dev/null
cd "$T"
# 2. torre (rótulos) y marca de agua
$PY $E/seguir_torre.py r2seq an/torre.json
$PY $E/marca_agua.py r2seq an/marca_agua.npz
# 3. pose del escalador (pose_heroe da la cabeza; pose_escalador agrega continuidad, torso y cadera)
P=$R/scripts/frena/pose_heroe.py
for a in "A 0 71 677 631" "C 123 185 543 730" "D 186 221 658 561" "E 222 301 449 903" "F 302 371 776 307"; do set -- $a; $PY $P r2seq pose/$1.json $2 $3 $4 $5; done
for a in "A 1 72" "C 124 186" "D 187 222" "E 223 302" "F 303 372"; do set -- $a; $PY $E/pose_escalador.py r2seq pose/$1.json pose/p2_$1.json $2 $3; done
# 4. estampados reales para la remera del escalador
$PY $R/scripts/hielo/textura_remera.py $R/PRODUCTO/negra_espalda_arena_DFDC5DED.png hielo/remera_espalda.png
$PY $R/scripts/hielo/textura_remera.py $R/PRODUCTO/negra_frente_arena_F266ACD9.png hielo/remera_frente.png
$PY $E/estampas.py hielo/remera_espalda.png hielo/remera_frente.png escalada_tex
# 5. composición (rótulos, bandera, remera, reencuadre del plano C)
export ESCALADA_TRABAJO=$T; rm -rf comp_v2; mkdir -p comp_v2
for r in "1 120" "121 240" "241 360" "361 475"; do set -- $r; $PY $E/componer.py r2seq an/torre.json an comp_v2 $1 $2 & done; wait
# 6. placa y montaje final
rm -rf placa; python3 $E/placa.py placa 127
$E/montar.sh "$T" "$R/EXPORTACIONES/ROCCE_02_HACETE_FOUNDER_v01.mp4" an/r2_audio.wav
