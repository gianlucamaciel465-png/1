#!/bin/bash
# Arma ROCCE_05_ESTUVISTE_CERCA: 1320 cuadros a 30 fps (44,0 s), 1080×1920, H.264 High yuv420p BT.709, AAC 48 kHz.
# Tomas (Higgsfield, Wan 2.7) recortadas según linea.py; estampado real ya compuesto en S1/S3/S6 (pecho de la abuela)
# G3 (pecho de la abuela, cuadros 42–78 de la toma) y G2 (frente); subtítulos .ass; placa 4 s. Sonoridad ≈ −14 LUFS en dos pasadas, limitador sin nivelar.
# Uso: montar.sh TRABAJO_DIR SALIDA.mp4
set -euo pipefail
T="$1"; OUT="$2"; PY=${PY:-python3}; NS=$((1320*1600))
F="scale=-2:1920:flags=lanczos,crop=1080:1920,setsar=1,fps=30,format=yuv420p"
seg() { echo "[$1:v]trim=start_frame=$2:end_frame=$3,setpts=PTS-STARTPTS,$F[v$1]"; }
ffmpeg -v error -y \
  -framerate 30 -i "$T/post/ab/S1/%04d.png" -i "$T/tomas/S2.mp4" -framerate 30 -i "$T/post/ab/S3/%04d.png" \
  -i "$T/tomas/S4.mp4" -i "$T/tomas/S5.mp4" -framerate 30 -i "$T/post/ab/S6/%04d.png" -i "$T/tomas/S7.mp4" \
  -i "$T/tomas/G1.mp4" -framerate 30 -i "$T/post/g2/zoom/%04d.png" -framerate 30 -i "$T/post/ab/G3/%04d.png" \
  -loop 1 -framerate 30 -t 4 -i "$T/post/placa.png" \
  -filter_complex "$(seg 0 0 150);$(seg 1 0 360);$(seg 2 0 84);$(seg 3 0 180);$(seg 4 12 48);$(seg 5 0 102);$(seg 6 0 54);\
$(seg 7 18 96);$(seg 8 0 120);$(seg 9 0 36);[10:v]trim=end_frame=120,setpts=PTS-STARTPTS,$F[v10];\
[v0][v1][v2][v3][v4][v5][v6][v7][v8][v9]concat=n=10:v=1:a=0,ass=$T/post/subs.ass[cuento];[cuento][v10]concat=n=2:v=1:a=0[v]" \
  -map "[v]" -c:v libx264 -profile:v high -preset slow -crf 16 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -an "$T/video.mp4" </dev/null
medir() { ffmpeg -v info -i "$1" -af ebur128=peak=true -f null - 2>&1 | $PY -c "import sys,re; t=sys.stdin.read(); print(re.findall(r'I:\s+(-?[0-9.]+) LUFS', t)[-1])"; }
M="$T/audio/mezcla_voz"; I=$(medir "$M.wav"); G=$($PY -c "print(f'{-14.0-($I):.2f}')")
for pasada in 1 2; do
  ffmpeg -v error -y -i "$M.wav" -af "volume=${G}dB,alimiter=limit=0.70:level=false:attack=1:release=50,apad=whole_len=$NS,atrim=end_sample=$NS" -ar 48000 -ac 2 -c:a pcm_s24le "${M}_final.wav" </dev/null
  I2=$(medir "${M}_final.wav"); G=$($PY -c "print(f'{$G+(-14.0-($I2)):.2f}')")
done
ffmpeg -v error -y -i "$T/video.mp4" -i "${M}_final.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -map_metadata -1 -movflags +faststart "$OUT" </dev/null
echo "listo: $OUT (ganancia ${G} dB desde ${I} LUFS)"
