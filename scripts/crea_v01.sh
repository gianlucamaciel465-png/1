#!/usr/bin/env bash
# ROCCE_crea_v01 — "¿Y si la próxima Roccé la creás vos?" (Founders Privée: el 001 diseña la próxima prenda).
# Rehace la pieza "Detrás de la foto" desde los originales. Sin fotos con marco, sin música de terceros, sin voz.
#
# Estructura (30 fps, 339 cuadros = 11,30 s):
#   S1 0,00–1,10  IMG_8002 0,00–1,10  blanca en el tronco bajo cielo azul, la cámara avanza. Pregunta en barra (0,10–2,40).
#   S2 1,10–3,10  IMG_8004 1,60–3,60  travelling que revela ROCCÉ en denim + cursiva; anotaciones 01 DENIM, 02 PESPUNTE.
#   S3 3,10–4,60  IMG_7857 1,30–2,80  la blanca puesta frente al mar (presencia, movimiento).
#   S4 4,60–5,60  IMG_7824 4,60–5,60  la negra avanza hacia cámara; anotación 03 TONO SOBRE TONO.
#   S5 5,60–8,30  IMG_3453 1,92–4,62  macro de la negra (corrección de color); el pulso se corta → "Los primeros 100 /
#                                     son Founders." (5,72) → "El 001 diseña / la próxima." (6,85) mientras la mano
#                                     vuelve a recorrer "so f★cking close.".
#   S6 8,30–11,30 IMG_8002 cuadro 0   la imagen del principio, quieta con acercamiento 1,00→1,035 (cierra el loop):
#                                     "FOUNDERS PRIVÉE" · "01/11/2026" · botón "Sé uno de los primeros 100.".
# Sonido: ambiente real de cada toma + efectos sintetizados (scripts/sfx.py, scripts/crea/cues_v01.json).
# Uso: scripts/crea_v01.sh [SALIDA]
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-EXPORTACIONES/ROCCE_crea_v01.mp4}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe"; exit 1; }
S=${S:-/tmp/claude-0/-home-user-1/bd43937f-7b34-55cc-a48c-8ac864032e15/scratchpad}; CV=$S/demucs-env/bin/python   # Python con OpenCV
T=TRABAJO/crea; C=$T/clips; X=$T/textos; mkdir -p $C $X $T/notas
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
SC="scale=1080:1920:flags=lanczos:out_range=tv,format=yuv420p,fps=30,setsar=1"
ENC="-c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -an"

# 1) tomas
ffmpeg -v error -y -ss 0.00 -i ORIGINALES/IMG_8002.mov -vf "$SC" -frames:v 33 $ENC $C/S1_8002.mp4
ffmpeg -v error -y -ss 1.60 -i ORIGINALES/IMG_8004.mov -vf "$SC" -frames:v 60 $ENC $C/S2_8004.mp4
ffmpeg -v error -y -ss 1.30 -i ORIGINALES/IMG_7857.mov -vf "$SC" -frames:v 45 $ENC $C/S3_7857.mp4
ffmpeg -v error -y -ss 4.60 -i ORIGINALES/IMG_7824.mov -vf "$SC" -frames:v 30 $ENC $C/S4_7824.mp4
ffmpeg -v error -y -ss 1.92 -i ORIGINALES/IMG_3453.mov -vf "$TM,fps=30,scale=1080:1920:flags=lanczos,setsar=1" -frames:v 81 $ENC $C/S5_3453.mp4
ffmpeg -v error -y -ss 0.00 -i ORIGINALES/IMG_8002.mov -vf "$SC" -frames:v 1 -update 1 $T/placa_8002_f0.png
ffmpeg -v error -y -loop 1 -framerate 30 -i $T/placa_8002_f0.png -vf "zoompan=z='1+0.035*on/90':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,setsar=1" -frames:v 90 $ENC $C/S6_placa.mp4

# 2) anotaciones con seguimiento, textos y efectos
rm -rf $T/notas/s2 $T/notas/s4
$CV -I scripts/anotaciones.py $C/S2_8004.mp4 $T/notas/s2 scripts/crea/notas_s2.json
$CV -I scripts/anotaciones.py $C/S4_7824.mp4 $T/notas/s4 scripts/crea/notas_s4.json
python3 scripts/textos_crea.py $X
python3 scripts/sfx.py $T/fx.wav 11.3 scripts/crea/cues_v01.json

# 3) montaje
GA="colorchannelmixer=rr=0.90:gg=0.98:bb=1.10,eq=gamma=0.70:saturation=0.85"
ov() { echo "[$1]format=rgba,fade=t=in:st=$2:d=${4:-0.12}:alpha=1${5:+,fade=t=out:st=$5:d=0.15:alpha=1}[$3]"; }
ffmpeg -v error -stats -n \
  -i $C/S1_8002.mp4 -i $C/S2_8004.mp4 -i $C/S3_7857.mp4 -i $C/S4_7824.mp4 -i $C/S5_3453.mp4 -i $C/S6_placa.mp4 \
  -framerate 30 -i $T/notas/s2/%04d.png -framerate 30 -i $T/notas/s4/%04d.png \
  -framerate 30 -loop 1 -t 11.3 -i $X/pregunta.png \
  -framerate 30 -loop 1 -t 11.3 -i $X/resp1.png -framerate 30 -loop 1 -t 11.3 -i $X/resp2.png \
  -framerate 30 -loop 1 -t 11.3 -i $X/cta1.png -framerate 30 -loop 1 -t 11.3 -i $X/cta2.png -framerate 30 -loop 1 -t 11.3 -i $X/cta3.png \
  -i ORIGINALES/IMG_8002.mov -i ORIGINALES/IMG_8004.mov -i ORIGINALES/IMG_7857.mov -i ORIGINALES/IMG_7824.mov -i ORIGINALES/IMG_3453.mov -i $T/fx.wav \
  -filter_complex "
  [1:v][6:v]overlay=0:0[s2];
  [3:v][7:v]overlay=0:0[s4];
  [4:v]$GA[s5];
  [0:v][s2][2:v][s4][s5][5:v]concat=n=6:v=1:a=0,setsar=1,format=yuv420p[base];
  $(ov 8:v 0.10 q 0.10 2.40);
  $(ov 9:v 5.72 r1);
  $(ov 10:v 6.85 r2);
  $(ov 11:v 8.45 c1 0.18);
  $(ov 12:v 8.60 c2 0.18);
  $(ov 13:v 9.20 c3 0.15);
  [base][q]overlay=0:0:enable='between(t,0.1,2.56)'[v1];
  [v1][r1]overlay=0:0:enable='between(t,5.72,8.2999)'[v2];
  [v2][r2]overlay=0:0:enable='between(t,6.85,8.2999)'[v3];
  [v3][c1]overlay=0:0:enable='gte(t,8.45)'[v4];
  [v4][c2]overlay=0:0:enable='gte(t,8.60)'[v5];
  [v5][c3]overlay=0:0:enable='gte(t,9.20)',format=yuv420p[v];
  [14:a]aresample=48000,atrim=0:1.1,asetpts=PTS-STARTPTS,volume=4dB,afade=t=out:st=1.07:d=0.03[a1];
  [15:a]aresample=48000,atrim=1.6:3.6,asetpts=PTS-STARTPTS,volume=4dB,afade=t=in:d=0.03,afade=t=out:st=1.97:d=0.03,adelay=1100|1100[a2];
  [16:a]aresample=48000,atrim=1.3:2.8,asetpts=PTS-STARTPTS,volume=2dB,afade=t=in:d=0.03,afade=t=out:st=1.47:d=0.03,adelay=3100|3100[a3];
  [17:a]aresample=48000,atrim=4.6:5.6,asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st=0.94:d=0.06,adelay=4600|4600[a4];
  [18:a]aresample=48000,aformat=channel_layouts=stereo,atrim=1.92:4.62,asetpts=PTS-STARTPTS,volume=12dB,afade=t=in:d=0.05,afade=t=out:st=2.65:d=0.05,adelay=5600|5600[a5];
  [14:a]aresample=48000,atrim=0:3.0,asetpts=PTS-STARTPTS,volume=4dB,afade=t=in:d=0.15,afade=t=out:st=2.6:d=0.4,adelay=8300|8300[a6];
  [19:a]aresample=48000[fx];
  [a1][a2][a3][a4][a5][a6][fx]amix=inputs=7:normalize=0:duration=longest,atrim=0:11.3,volume=${GAN:-12}dB,alimiter=limit=0.74:level=false,aformat=channel_layouts=stereo[au]" \
  -map "[v]" -map "[au]" -t 11.3 \
  -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -r 30 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
echo "Exportado: $OUT"
