#!/usr/bin/env bash
# ROCCE_lo_que_te_frena_v02 — corrección de v01 pedida por Gianluca (27/10/2026): se conserva el inicio aprobado y su
# resolución; se conecta la animación con su trabajo real, se construye una progresión sonora y se cierra con una
# invitación concreta. Villano: lo que nos hace postergar (MIEDO · QUÉ DIRÁN · COMODIDAD · FIACA · EXCUSAS).
# Héroe: el espectador. Guía: Roccé / Gianluca, que protagoniza este episodio y le devuelve la acción al espectador.
# Locución (texto de Gianluca): "Fracasé. Me incomodé. Y acá estoy. / Ahora te toca a vos. / El primero de noviembre,
# hacete founder de Roccé y creá lo que viene con nosotros. / Mandanos FOUNDERS y pedí acceso."
# Una sola acción en voz, pantalla y descripción: mandar FOUNDERS por mensaje (no hay un enlace activo a la lista).
#
# Uso: scripts/lo_que_te_frena_v02.sh [SALIDA]
#   VOZ=carpeta con p1.wav … p6.wav (scripts/frena/preparar_voz.py). Por defecto, la voz guía provisoria.
#   Para usar la nota de voz de Gianluca:
#     $S/whisper-env/bin/python scripts/frena/preparar_voz.py nota NOTA.m4a TRABAJO/frena2/voz_gianluca
#     VOZ=TRABAJO/frena2/voz_gianluca scripts/lo_que_te_frena_v02.sh EXPORTACIONES/ROCCE_lo_que_te_frena_v03.mp4
#   La duración y los cortes se recalculan con la duración de cada frase (TRABAJO/frena2/linea_de_tiempo.json).
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-EXPORTACIONES/ROCCE_lo_que_te_frena_v02.mp4}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe"; exit 1; }
S=${S:-/tmp/claude-0/-home-user-1/bd43937f-7b34-55cc-a48c-8ac864032e15/scratchpad}; CV=$S/demucs-env/bin/python
VOZ=${VOZ:-AUDIO/frena_v02_voz_guia}   # voz guía provisoria (Chatterbox, voz incorporada; no es la de Gianluca)
R1=REFERENCIAS/REF_15_neuronvisuals_soga_DeUC8-gxNIn.mp4
T=TRABAJO/frena; mkdir -p $T/seq60 TRABAJO/frena2

# 1) animación de v01 con el rótulo COMODIDAD (en lugar de DUDAS)
[ -f $T/seq60/0483.png ] || ffmpeg -v error -y -i $R1 $T/seq60/%04d.png
[ -f $T/pose60.json ] || $CV -I scripts/frena/pose_heroe.py $T/seq60 $T/pose60.json 12 470 907 652
[ -f $T/pose60_fix.json ] || $CV -I scripts/frena/pose_salto.py $T/seq60 $T/pose60.json $T/pose60_fix.json > /dev/null
[ -f $T/rot60.json ] || $CV -I scripts/frena/seguir_rotulos.py $T/seq60 $T/rot60.json 6 310
python3 scripts/frena/textos_frena.py $T/textos > /dev/null
python3 scripts/frena/textos_frena_v02.py TRABAJO/frena2/textos > /dev/null
if [ ! -f TRABAJO/frena2/anim/0212.png ]; then
  ROTULO_DOUBT=COMODIDAD $CV -I scripts/frena/componer_anim.py $T/seq60 $T/pose60_fix.json $T/rot60.json $T/textos TRABAJO/frena2/anim
fi
# 2) capas de la música de R1 (demucs)
if [ ! -f $T/stems/other.wav ]; then
  mkdir -p $T/stems; ffmpeg -v error -y -i $R1 -vn -ac 2 -ar 44100 $T/stems/r1.wav
  $CV -m demucs -n htdemucs -o $T/stems/sep $T/stems/r1.wav && cp $T/stems/sep/htdemucs/r1/{other,bass,drums}.wav $T/stems/
fi
# 3) montaje (la línea de tiempo sale de la voz)
python3 scripts/frena/montaje_v02.py "$VOZ" "$OUT"
