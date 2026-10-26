#!/usr/bin/env bash
# Verifica un export: decodificación completa, specs, fotogramas en cortes y final.
# Uso: verificar.sh salida.mp4 carpeta_fotogramas [tiempos_de_corte...]
set -uo pipefail
f="$1"; out="$2"; shift 2; mkdir -p "$out"
echo "== Decodificación completa =="; errs=$(ffmpeg -v error -i "$f" -f null - 2>&1); [ -z "$errs" ] && echo OK || echo "$errs"
echo "== Specs =="; ffprobe -v error -show_entries stream=codec_type,codec_name,profile,width,height,r_frame_rate,pix_fmt,sample_rate,channels,duration,nb_frames -show_entries format=duration -of compact "$f"
echo "== Audio (niveles) =="; ffmpeg -v info -i "$f" -af volumedetect -vn -f null - 2>&1 | grep -E "mean_volume|max_volume"
echo "== Audio (sonoridad EBU R128; objetivo ≈ −14 LUFS, pico ≤ −1 dBTP) =="; ffmpeg -nostats -i "$f" -vn -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):" | tr -s ' '
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
for c in "$@"; do for d in -0.10 -0.04 0 0.04 0.10; do
  t=$(awk "BEGIN{print $c+$d}"); ffmpeg -v error -y -ss "$t" -i "$f" -frames:v 1 -vf scale=360:-2 "$out/corte_${c}_$(printf %+.2f $d).jpg"; done; done
for t in 0.2 $(awk "BEGIN{print $dur-1.5; print $dur-0.5}"); do ffmpeg -v error -y -ss "$t" -i "$f" -frames:v 1 "$out/t${t}.jpg"; done
echo "Fotogramas en $out"
