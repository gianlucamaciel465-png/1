#!/bin/bash
# Arma ROCCE_06_DEJA_DE_PROCRASTINAR: animación 3D (348 cuadros, render.js) + CTA sobre IMG_7857 (102 cuadros, cta.py)
# = 450 cuadros a 30 fps (15,0 s), 1080×1920, H.264 High yuv420p BT.709, AAC 48 kHz; ≈ −14 LUFS en dos pasadas,
# limitador sin nivelar, audio de exactamente 450 × 1600 muestras.
# Uso: montar.sh TRABAJO_DIR SALIDA.mp4   (TRABAJO_DIR con cuadros/, cta/cuadros/ y mezcla.wav)
set -euo pipefail
T="$1"; OUT="$2"; PY=${PY:-python3}; NS=$((450*1600))
ffmpeg -v error -y -framerate 30 -i "$T/cuadros/%04d.png" -framerate 30 -i "$T/cta/cuadros/%04d.png" \
  -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]" -map "[v]" \
  -c:v libx264 -profile:v high -preset slow -crf 17 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -an "$T/video.mp4" </dev/null
medir() { ffmpeg -v info -i "$1" -af ebur128=peak=true -f null - 2>&1 | $PY -c "import sys,re; t=sys.stdin.read(); print(re.findall(r'I:\s+(-?[0-9.]+) LUFS', t)[-1])"; }
I=$(medir "$T/mezcla.wav"); G=$($PY -c "print(f'{-14.0-($I):.2f}')")
for pasada in 1 2; do
  ffmpeg -v error -y -i "$T/mezcla.wav" -af "volume=${G}dB,alimiter=limit=0.70:level=false:attack=1:release=50,apad=whole_len=$NS,atrim=end_sample=$NS" -ar 48000 -ac 2 -c:a pcm_s24le "$T/mezcla_final.wav" </dev/null
  I2=$(medir "$T/mezcla_final.wav"); G=$($PY -c "print(f'{$G+(-14.0-($I2)):.2f}')")
done
ffmpeg -v error -y -i "$T/video.mp4" -i "$T/mezcla_final.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -map_metadata -1 -movflags +faststart "$OUT" </dev/null
echo "listo: $OUT (ganancia ${G} dB desde ${I} LUFS)"
