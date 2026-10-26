#!/usr/bin/env bash
# ROCCE_salto_v01 — Referencia R12 (Instagram DdRfmrgDLIk, cuenta macrobodega):
# apertura original 0–39,45 s (imagen, voz, música, subtítulos) + transición de píxeles + Roccé + cierre.
# La voz original se corta en una pausa natural después de "…para llegar a" (39,45 s). NO hay voz sintetizada.
# Desde ahí sigue la base musical original sin voz (separada con demucs → AUDIO/R12_base_sin_voz_demucs.flac).
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-EXPORTACIONES/ROCCE_salto_v01.mp4}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe"; exit 1; }
REF=REFERENCIAS/REF_12_macrobodega_salto_DdRfmrgDLIk.mp4
BED=AUDIO/R12_base_sin_voz_demucs.flac
FONT=scripts/fuentes/Montserrat-Bold.ttf
mkdir -p TRABAJO; for f in IMG_8002 IMG_4627 IMG_3453 IMG_7793 IMG_7894; do [ -e TRABAJO/$f.mov ] || cp ORIGINALES/$f.mov TRABAJO/; done
T1=$(mktemp); printf '%s' "llegar a" > "$T1"
T2=$(mktemp); printf '%s' "Roccé." > "$T2"
T3=$(mktemp); printf '%s' "1/11 — DROP FOUNDERS PRIVÉE" > "$T3"
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
N="scale=1080:1920:flags=lanczos,setsar=1,fps=30,format=yuv420p,settb=AVTB"
# Franja "vidrio" como la de los subtítulos originales (desenfoque más claro con bordes difusos)
GLASS="boxblur=22:3,eq=brightness=0.05:saturation=0.6,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='255*min(1,min(min(X,W-X)/70,min(Y,H-Y)/32))'"
SUB="fontfile=$FONT:fontcolor=white:shadowcolor=black@0.7:shadowx=3:shadowy=3:x=(w-text_w)/2:y=1452"
ffmpeg -v error -stats -n \
  -i "$REF" \
  -ss 0.00 -i TRABAJO/IMG_8002.mov \
  -ss 1.00 -i TRABAJO/IMG_4627.mov \
  -ss 0.00 -i TRABAJO/IMG_3453.mov \
  -ss 2.50 -i TRABAJO/IMG_7793.mov \
  -ss 0.00 -i TRABAJO/IMG_7894.mov \
  -ss 39.45 -i "$BED" \
  -filter_complex "
  [0:v]$N,trim=end_frame=1184,setpts=PTS-STARTPTS[o];
  [1:v]$N,trim=end_frame=43,setpts=PTS-STARTPTS[s1];
  [2:v]$TM,$N,trim=end_frame=34,setpts=PTS-STARTPTS[s2];
  [3:v]$TM,$N,trim=end_frame=33,setpts=PTS-STARTPTS[s3];
  [4:v]$N,trim=end_frame=34,setpts=PTS-STARTPTS[s4];
  [5:v]$N,trim=end_frame=50,setpts=PTS-STARTPTS[s5];
  [o][s1]xfade=transition=pixelize:duration=0.3:offset=39.1667[x];
  [x][s2][s3][s4][s5]concat=n=5:v=1:a=0,format=yuv420p,split=3[c0][c1][c2];
  [c1]crop=760:150:160:1407,$GLASS[ga];
  [c2]crop=980:150:50:1407,$GLASS[gb];
  [c0][ga]overlay=160:1407:enable='between(t,39.0,40.6)'[d0];
  [d0][gb]overlay=50:1407:enable='gte(t,44.5333)',
    drawtext=$SUB:textfile=$T1:fontsize=59:enable='between(t,39.0,39.4666)',
    drawtext=$SUB:textfile=$T2:fontsize=59:enable='between(t,39.4667,40.6)',
    drawtext=$SUB:textfile=$T3:fontsize=50:enable='gte(t,44.5333)',format=yuv420p[v];
  [0:a]atrim=0:39.45,asetpts=PTS-STARTPTS,aresample=48000,afade=t=out:st=39.43:d=0.02[a0];
  [6:a]atrim=0:6.1833,asetpts=PTS-STARTPTS,aresample=48000,afade=t=in:d=0.02,
    volume='if(lt(t,0.85),1,if(lt(t,1.15),1+2.548*(t-0.85)/0.3,3.548))':eval=frame,
    afade=t=out:st=5.83:d=0.35[a1];
  [a0][a1]concat=n=2:v=0:a=1,alimiter=limit=0.84,aformat=channel_layouts=stereo[a]" \
  -map "[v]" -map "[a]" -t 45.6333 \
  -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -r 30 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
rm -f "$T1" "$T2" "$T3"; echo "Exportado: $OUT"
