#!/bin/bash
# Arma los másteres de una pieza IGLIB: cuadros JPEG al doble → 1080×1920 (lanczos), H.264 High nivel 4.0
# (maxrate 20M, bufsize 25M), yuv420p, BT.709 rango TV, 30 fps; audio AAC 48 kHz estéreo a −14 LUFS integrados
# (dos pasadas de ganancia + alimiter level=false, pico ≤ −1 dBTP), largo exacto = cuadros × 1600 muestras,
# sin metadatos (-map_metadata -1: sin GPS), +faststart.
# Uso: montar.sh CUADROS_DIR AUDIO_DIR SALIDA_DIR NOMBRE(IGLIB-1) VERSION(v01)
set -euo pipefail
FR="$1"; AU="$2"; OUT="$3"; NOM="$4"; V="$5"; PY=${PY:-python3}
N=$(ls "$FR"/[0-9]*.jpg | wc -l); NS=$((N*1600))
ffmpeg -v error -y -framerate 30 -start_number 0 -i "$FR/%04d.jpg" \
  -vf "scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int:in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p" \
  -c:v libx264 -profile:v high -level:v 4.0 -preset slow -crf 16 -maxrate 20M -bufsize 25M \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -an "$AU/video.mp4" </dev/null
medir() { ffmpeg -nostats -i "$1" -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | $PY -c "import sys,re; t=sys.stdin.read(); print(re.findall(r'I:\s+(-?[0-9.]+) LUFS', t)[-1])"; }
for par in "mezcla:${NOM}_${V}" "mezcla_sinmusica:${NOM}_${V}_SINMUSICA"; do
  M="${par%%:*}"; NOMBRE="${par##*:}"
  I=$(medir "$AU/$M.wav"); G=$($PY -c "print(f'{-14.0-($I):.2f}')")
  for pasada in 1 2 3; do
    ffmpeg -v error -y -i "$AU/$M.wav" -af "volume=${G}dB,alimiter=limit=0.72:level=false:attack=1:release=60,apad=whole_len=$NS,atrim=end_sample=$NS" -ar 48000 -ac 2 -c:a pcm_s24le "$AU/${M}_final.wav" </dev/null
    I2=$(medir "$AU/${M}_final.wav"); G=$($PY -c "print(f'{$G+(-14.0-($I2)):.2f}')")
  done
  ffmpeg -v error -y -i "$AU/video.mp4" -i "$AU/${M}_final.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 -ac 2 \
    -map_metadata -1 -map_chapters -1 -movflags +faststart "$OUT/$NOMBRE.mp4" </dev/null
  echo "listo: $OUT/$NOMBRE.mp4 ($N cuadros; ganancia final ${G} dB desde ${I} LUFS)"
done
