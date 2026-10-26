#!/usr/bin/env bash
# Extrae fotogramas cada N segundos con la marca de tiempo impresa y en el nombre.
# Uso: fotogramas.sh video.mp4 carpeta_salida [cada_seg=1]
set -euo pipefail
in="$1"; out="$2"; step="${3:-1}"; mkdir -p "$out"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
t=0
while awk "BEGIN{exit !($t < $dur)}"; do
  name=$(printf "%s/t%07.2f.jpg" "$out" "$t")
  ffmpeg -v error -y -ss "$t" -i "$in" -frames:v 1 -vf "scale=-2:720,drawtext=text='t=${t}s':x=10:y=10:fontsize=28:fontcolor=yellow:box=1:boxcolor=black@0.6" "$name"
  t=$(awk "BEGIN{print $t+$step}")
done
echo "Fotogramas en $out"
