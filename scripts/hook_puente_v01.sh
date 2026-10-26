#!/usr/bin/env bash
# ROCCE_hook_puente_v01 — hook original de la referencia (R11, Instagram De9bn1GqBYQ, cuenta toparadi)
# + montaje de remeras Roccé en los mismos cortes de la referencia + cierre "1/11 — DROP FOUNDERS PRIVÉE".
# Audio: pista completa de la referencia (sincronía intacta). 30 fps, 312 cuadros = duración de la referencia (10,4 s).
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-EXPORTACIONES/ROCCE_hook_puente_v01.mp4}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe"; exit 1; }
REF=REFERENCIAS/REF_11_toparadi_hook_puente_De9bn1GqBYQ.mp4
mkdir -p TRABAJO; for f in IMG_4530 IMG_7824 IMG_3375 IMG_3453 IMG_7857 IMG_7793 IMG_7894; do [ -e TRABAJO/$f.mov ] || cp ORIGINALES/$f.mov TRABAJO/; done
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
TXT=$(mktemp); printf '%s' "1/11 — DROP FOUNDERS PRIVÉE" > "$TXT"
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
N="scale=1080:1920:flags=lanczos,setsar=1,fps=30,format=yuv420p"
# plano: entrada inicio(s) cuadros [hdr]
ffmpeg -v error -stats -n \
  -i "$REF" \
  -ss 0.10 -i TRABAJO/IMG_4530.mov \
  -ss 4.90 -i TRABAJO/IMG_7824.mov \
  -ss 0.40 -i TRABAJO/IMG_3375.mov \
  -ss 0.10 -i TRABAJO/IMG_3453.mov \
  -ss 3.10 -i TRABAJO/IMG_7857.mov \
  -ss 2.60 -i TRABAJO/IMG_7793.mov \
  -ss 0.00 -i TRABAJO/IMG_7894.mov \
  -filter_complex "
  [0:v]$N,trim=end_frame=110,setpts=PTS-STARTPTS[h];
  [1:v]$TM,$N,trim=end_frame=18,setpts=PTS-STARTPTS[a];
  [2:v]$N,trim=end_frame=35,setpts=PTS-STARTPTS[b];
  [3:v]$TM,$N,trim=end_frame=14,setpts=PTS-STARTPTS[c];
  [4:v]$TM,$N,trim=end_frame=42,setpts=PTS-STARTPTS[d];
  [5:v]$N,trim=end_frame=30,setpts=PTS-STARTPTS[e];
  [6:v]$N,trim=end_frame=27,setpts=PTS-STARTPTS[f];
  [7:v]$N,trim=end_frame=36,setpts=PTS-STARTPTS[g];
  [h][a][b][c][d][e][f][g]concat=n=8:v=1:a=0,
    drawtext=fontfile=$FONT:textfile=$TXT:fontsize=56:fontcolor=white:x=(w-text_w)/2:y=h*0.17:shadowcolor=black@0.55:shadowx=2:shadowy=3:enable='gte(t,9.4)'[v];
  [0:a]atrim=0:10.4,asetpts=PTS-STARTPTS,aresample=48000,afade=t=out:st=10.34:d=0.06[au]" \
  -map "[v]" -map "[au]" -t 10.4 \
  -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -r 30 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
rm -f "$TXT"; echo "Exportado: $OUT"
