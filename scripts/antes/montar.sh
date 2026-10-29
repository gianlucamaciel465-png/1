#!/bin/bash
# Arma ROCCE_04_ANTES_DEL_APLAUSO (con locución Firme 04) y ROCCE_04B_ANTES_DEL_APLAUSO_SIN_VOZ (misma imagen, solo
# tipografía + diseño sonoro): 450 cuadros a 30 fps (15,0 s), 1080×1920, H.264 High yuv420p BT.709, AAC 48 kHz.
# Sonoridad ≈ −14 LUFS en dos pasadas, limitador sin nivelar (pico < −1 dBTP), audio de exactamente N × 1600 muestras.
# Uso: montar.sh CUADROS_DIR AUDIO_DIR SALIDA_DIR VERSION(vNN)
set -euo pipefail
FR="$1"; AU="$2"; OUT="$3"; V="$4"; PY=${PY:-python3}
N=$(ls "$FR"/[0-9]*.png | wc -l); NS=$((N*1600))
ffmpeg -v error -y -framerate 30 -i "$FR/%04d.png" \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" -c:v libx264 -profile:v high -preset slow -crf 16 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -an "$AU/video.mp4" </dev/null
medir() { ffmpeg -v info -i "$1" -af ebur128=peak=true -f null - 2>&1 | $PY -c "import sys,re; t=sys.stdin.read(); print(re.findall(r'I:\s+(-?[0-9.]+) LUFS', t)[-1])"; }
for par in "mezcla_voz:ROCCE_04_ANTES_DEL_APLAUSO_${V}" "mezcla_sin_voz:ROCCE_04B_ANTES_DEL_APLAUSO_SIN_VOZ_${V}"; do
  M="${par%%:*}"; NOMBRE="${par##*:}"
  I=$(medir "$AU/$M.wav"); G=$($PY -c "print(f'{-14.0-($I):.2f}')")
  for pasada in 1 2; do
    ffmpeg -v error -y -i "$AU/$M.wav" -af "volume=${G}dB,alimiter=limit=0.70:level=false:attack=1:release=50,apad=whole_len=$NS,atrim=end_sample=$NS" -ar 48000 -ac 2 -c:a pcm_s24le "$AU/${M}_final.wav" </dev/null
    I2=$(medir "$AU/${M}_final.wav"); G=$($PY -c "print(f'{$G+(-14.0-($I2)):.2f}')")
  done
  ffmpeg -v error -y -i "$AU/video.mp4" -i "$AU/${M}_final.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 \
    -map_metadata -1 -movflags +faststart "$OUT/$NOMBRE.mp4" </dev/null
  echo "listo: $OUT/$NOMBRE.mp4 ($N cuadros; ganancia ${G} dB desde ${I} LUFS)"
done
