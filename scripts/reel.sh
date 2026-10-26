#!/usr/bin/env bash
# Reel vertical 1080x1920: toma A + toma B + audio + texto de cierre.
# Uso: reel.sh tomaA inicioA durA tomaB inicioB durB audio inicioAudio salida.mp4 [fps] [texto]
# El recorte vertical es centrado; ajustar CROP_X_A / CROP_X_B (0..1) si la prenda no está centrada.
set -euo pipefail
A="$1"; SA="$2"; DA="$3"; B="$4"; SB="$5"; DB="$6"; AUD="$7"; SAUD="$8"; OUT="$9"
FPS="${10:-$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$A")}"
TEXT="${11:-1/11 — DROP FOUNDERS PRIVÉE}"
CXA="${CROP_X_A:-0.5}"; CXB="${CROP_X_B:-0.5}"
FONT="${FONT:-/usr/share/fonts/opentype/inter/Inter-SemiBold.otf}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe; usar nueva versión"; exit 1; }
TOTAL=$(awk "BEGIN{print $DA+$DB}")
TXT_IN=$(awk "BEGIN{print $TOTAL-2.5}")
tf=$(mktemp); printf '%s' "$TEXT" > "$tf"
# cubre a 9:16 sin deformar (escala para llenar y recorta)
fill() { echo "scale=w='if(gt(a,9/16),-2,1080)':h='if(gt(a,9/16),1920,-2)':flags=lanczos,crop=1080:1920:(iw-1080)*$1:(ih-1920)/2,setsar=1,fps=$FPS,format=yuv420p"; }
ffmpeg -v error -stats -n \
  -ss "$SA" -t "$DA" -i "$A" \
  -ss "$SB" -t "$DB" -i "$B" \
  -ss "$SAUD" -t "$TOTAL" -i "$AUD" \
  -filter_complex "
    [0:v]$(fill $CXA),setpts=PTS-STARTPTS[a];
    [1:v]$(fill $CXB),setpts=PTS-STARTPTS[b];
    [a][b]concat=n=2:v=1:a=0[cat];
    [cat]drawtext=fontfile=$FONT:textfile=$tf:fontsize=64:fontcolor=white:x=(w-text_w)/2:y=h*0.80:shadowcolor=black@0.6:shadowx=2:shadowy=2:alpha='if(lt(t,$TXT_IN),0,min(1,(t-$TXT_IN)/0.4))'[v];
    [2:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.15,afade=t=out:st=$(awk "BEGIN{print $TOTAL-0.8}"):d=0.8[au]" \
  -map "[v]" -map "[au]" -t "$TOTAL" \
  -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -r "$FPS" \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
rm -f "$tf"; echo "Exportado: $OUT (corte en ${DA}s, texto desde ${TXT_IN}s)"
