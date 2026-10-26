#!/usr/bin/env bash
# Ficha técnica + hoja de fotogramas (2 por segundo) de material de video.
# Uso: scripts/catalogar.sh ORIGINALES/IMG_xxxx.mov [...]
# Las hojas quedan en ORIGINALES/analisis/<nombre>_fotogramas_2fps.jpg.
# Avisa si la toma es HDR (hay que convertirla a SDR) o si trae ubicación GPS.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p ORIGINALES/analisis
# Conversión HDR (HLG/PQ) → SDR BT.709 probada el 26/10/2026 con IMG_4675.
TONEMAP="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
for f in "$@"; do
  n=$(basename "${f%.*}")
  echo "== $n"
  ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,profile,width,height,r_frame_rate,avg_frame_rate,pix_fmt,color_transfer:stream_side_data=rotation -of default=nw=1 "$f" | tr '\n' ' '; echo
  ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of default=nw=1 "$f" | tr '\n' ' '; echo
  ffprobe -v error -show_entries format=duration:format_tags=creation_time,com.apple.quicktime.model -of default=nw=1 "$f" | tr '\n' ' '; echo
  trc=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of default=nw=1:nk=1 "$f" | head -1)
  pre=""
  case "$trc" in
    arib-std-b67|smpte2084) echo "   AVISO: HDR ($trc). Convertir a SDR antes de mezclar: $TONEMAP"; pre="$TONEMAP," ;;
  esac
  ffprobe -v error -show_entries format_tags -of default=nw=1 "$f" | grep -qi "location" && echo "   AVISO: trae ubicación GPS en los metadatos (no debe pasar a las exportaciones)"
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  cnt=$(awk "BEGIN{print int($d*2)+1}"); rows=$(( (cnt+7)/8 ))
  ffmpeg -v error -y -i "$f" -vf "${pre}fps=2,scale=240:-2,drawtext=text='$n %{pts\:hms}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.7,tile=8x${rows}" -frames:v 1 "ORIGINALES/analisis/${n}_fotogramas_2fps.jpg"
  echo "   hoja: ORIGINALES/analisis/${n}_fotogramas_2fps.jpg"
done
