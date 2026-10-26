#!/usr/bin/env bash
# Reel v01 — DROP FOUNDERS PRIVÉE. Sin música: sonido ambiente de las tomas.
# Toma 1: IMG_7793 (negra, balcón) 1.5–5.3 s, vertical nativa.
# Toma 2: IMG_7859 (blanca, mar) 2.0–7.6 s, horizontal: ventana del 48 % del ancho
#         para no cortar la remera; arriba/abajo, la misma toma desenfocada.
# Cierre: placa con el logo original (sin modificar, fondo #FEFEFE igual al del PNG) + texto.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-EXPORTACIONES/ROCCE_reel_founders_v01.mp4}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe"; exit 1; }
mkdir -p TRABAJO
for f in IMG_7793.mov IMG_7859.mov; do [ -e TRABAJO/$f ] || cp ORIGINALES/$f TRABAJO/; done
FONT=/usr/share/fonts/opentype/inter/Inter-SemiBold.otf
TXT=$(mktemp); printf '%s' "1/11 — DROP FOUNDERS PRIVÉE" > "$TXT"
D1=3.8; D2=5.6; D3=2.6
ffmpeg -v error -stats -n \
  -ss 1.5 -t $D1 -i TRABAJO/IMG_7793.mov \
  -ss 2.0 -t 6.33 -i TRABAJO/IMG_7859.mov \
  -loop 1 -framerate 30 -t $D3 -i LOGO/rocce_logo.png \
  -f lavfi -t $D3 -i "color=c=0xFEFEFE:s=1080x1920:r=30" \
  -filter_complex "
  [0:v]scale=1080:1920:flags=lanczos,setsar=1,fps=30,format=yuv420p,setpts=PTS-STARTPTS[v1];
  [1:v]trim=0:$D2,setpts=PTS-STARTPTS,fps=30,split[f][b];
  [b]scale=-2:1920,crop=1080:1920:(iw*0.495-540):0,boxblur=40:2,eq=brightness=-0.04[bg];
  [f]scale=2250:-2:flags=lanczos,crop=1080:ih:(iw*0.495-540):0[fg];
  [bg][fg]overlay=0:(H-h)/2,setsar=1,format=yuv420p[v2];
  [2:v]scale=1000:1000:flags=lanczos,format=rgba,fade=t=in:st=0:d=0.35:alpha=1[logo];
  [3:v][logo]overlay=40:330:shortest=1,
     drawtext=fontfile=$FONT:textfile=$TXT:fontsize=56:fontcolor=0x111111:x=(w-text_w)/2:y=1330:alpha='min(1,max(0,(t-0.5)/0.35))',
     setsar=1,format=yuv420p[v3];
  [v1][v2][v3]concat=n=3:v=1:a=0[v];
  [0:a]volume=12dB,afade=t=in:d=0.05,afade=t=out:st=$(awk "BEGIN{print $D1-0.03}"):d=0.03,apad,atrim=0:$D1[a1];
  [1:a]afade=t=in:d=0.03,afade=t=out:st=$D2:d=0.7,apad,atrim=0:$(awk "BEGIN{print $D2+$D3}")[a2];
  [a1][a2]concat=n=2:v=0:a=1,alimiter=limit=0.89,aresample=48000,aformat=channel_layouts=stereo[a]" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -r 30 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
rm -f "$TXT"; echo "Exportado: $OUT (cortes en ${D1}s y $(awk "BEGIN{print $D1+$D2}")s)"
