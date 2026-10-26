#!/usr/bin/env bash
# ROCCE_construi_historia_v02 — R14 (Instagram DeSZWn3RYFG, Neuron Visuals: perfeccionista vs. accionista)
# con rótulos en español + 7 s de Roccé ("CONSTRUÍ TU HISTORIA.").
# Total = 13,8 s del original + 7,0 s = 20,8 s (624 cuadros a 30 fps; las tomas propias son de 30 fps).
#
# Montaje del bloque Roccé (tiempos relativos a 13,8 s; cortes en la grilla de la música, golpe = 0,3483 s):
#   A 0,000–1,233  IMG_3453 (HDR) 0,00–1,23: dedos que recorren el estampado de la negra (la mano que construye)
#                  + "CONSTRUÍ TU HISTORIA." en el estilo de los rótulos de la animación.
#   B 1,233–3,333  IMG_4530 (HDR) 0,80–2,90: manos sostienen la espalda de la blanca, ROCCÉ en denim + Founders Privée.
#                  Entra con la batería (compás de 15,06 s).
#   C 3,333–5,100  IMG_7887 1,90–3,67: chico con la negra puesta fotografía la blanca en las rocas (presencia).
#   D 5,100–7,000  IMG_7896 4,20–6,10 acercada 1,16× (4K): ambas remeras completas y una ola que rompe detrás
#                  + "1/11 — DROP FOUNDERS PRIVÉE". (v01 usaba IMG_7894: la manga de la blanca tocaba el borde.)
# Audio: original intacto hasta 13,8 s; la canción del original vuelve a empezar en 13,932 s (alineada a sus
# compases: el 1,126 s de la canción cae en el compás de 15,058 s), con eco de la última sílaba como puente.
# Uso: scripts/construi_historia_v02.sh [SALIDA]
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-EXPORTACIONES/ROCCE_construi_historia_v02.mp4}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe"; exit 1; }
REF=REFERENCIAS/REF_14_neuronvisuals_ladrillo_DeSZWn3RYFG.mp4
T=TRABAJO/construi; mkdir -p $T/clips
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
ENC="-c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -an"
GA=null; GB=null; GC=null; GD=null   # la corrección de color se aplica en el montaje (paso 4)

# 1) animación con rótulos en español (60 fps, intermedio)
python3 scripts/rotulos_r14.py $T/rotulos >/dev/null
ffmpeg -v error -y -i $REF -framerate 60 -loop 1 -i $T/rotulos/rotulos.png -filter_complex "
  [0:v]drawbox=x=554:y=583:w=366:h=58:color=0x020202:t=fill,drawbox=x=130:y=781:w=396:h=58:color=0x020202:t=fill[c];
  [1:v]format=rgba,fade=t=out:st=13.40:d=0.33:alpha=1[l];
  [c][l]overlay=0:0:shortest=1,format=yuv420p[v]" -map "[v]" $ENC $T/animacion_es_60fps_v.mp4

# 2) tomas (SDR BT.709, 1080×1920, 30 fps constantes, cantidad exacta de cuadros)
ffmpeg -v error -y -ss 0.00 -i ORIGINALES/IMG_3453.mov -vf "$TM,fps=30,scale=1080:1920:flags=lanczos,$GA,setsar=1" -frames:v 37 $ENC $T/clips/A_3453.mp4
ffmpeg -v error -y -ss 0.80 -i ORIGINALES/IMG_4530.mov -vf "$TM,fps=30,scale=1080:1920:flags=lanczos,$GB,setsar=1" -frames:v 63 $ENC $T/clips/B_4530.mp4
ffmpeg -v error -y -ss 1.90 -i ORIGINALES/IMG_7887.mov -vf "scale=1080:1920:flags=lanczos:out_range=tv,format=yuv420p,fps=30,$GC,setsar=1" -frames:v 53 $ENC $T/clips/C_7887.mp4
ffmpeg -v error -y -ss 4.20 -i ORIGINALES/IMG_7896.mov -vf "crop=w=iw/1.16:h=ih/1.16:x=iw*0.024:y=ih*0.07,scale=1080:1920:flags=lanczos:in_range=pc:out_range=tv,format=yuv420p,fps=30,$GD,setsar=1" -frames:v 57 $ENC $T/clips/D_7896.mp4
for f in $T/clips/*.mp4; do echo "$(basename $f): $(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height -of csv=p=0 $f)"; done

# 3) textos (Inter Display Bold; texto exacto)
python3 scripts/texto_png.py $T/textos_entrada.png 76 560 "CONSTRUÍ TU HISTORIA.|#FFFFFF"
python3 scripts/texto_png.py $T/textos_cierre.png 62 380 "1/11 — DROP FOUNDERS PRIVÉE|#FFFFFF"

# 4) montaje: 414 cuadros de animación + A 37 + B 63 + C 53 + D 57 = 624 cuadros (20,8 s)
VOC=AUDIO/R14_voz_cancion_demucs.flac
ffmpeg -v error -stats -n \
  -i $T/animacion_es_60fps_v.mp4 \
  -i $T/clips/A_3453.mp4 -i $T/clips/B_4530.mp4 -i $T/clips/C_7887.mp4 -i $T/clips/D_7896.mp4 \
  -framerate 30 -loop 1 -t 1.2333 -i $T/textos_entrada.png \
  -framerate 30 -loop 1 -t 1.9 -i $T/textos_cierre.png \
  -i $REF -i $VOC \
  -filter_complex "
  [0:v]fps=30,trim=end_frame=414,setpts=PTS-STARTPTS,format=yuv420p[an];
  [1:v]colorchannelmixer=rr=0.90:gg=0.98:bb=1.10,eq=gamma=0.70:saturation=0.85,fade=t=in:st=0:d=0.2,setpts=PTS-STARTPTS[a0];
  [5:v]format=rgba,fade=t=in:st=0.08:d=0.12:alpha=1[ta];
  [a0][ta]overlay=0:0:shortest=1,format=yuv420p[a];
  [2:v]colorchannelmixer=rr=1.05:gg=1.03:bb=0.92,setpts=PTS-STARTPTS,format=yuv420p[b];
  [3:v]setpts=PTS-STARTPTS,format=yuv420p[c];
  [4:v]geq=lum='lum(X,Y)*(1-0.55*max(0,1-Y/900))':cb='cb(X,Y)':cr='cr(X,Y)',setpts=PTS-STARTPTS[d0];
  [6:v]format=rgba,fade=t=in:st=0.10:d=0.15:alpha=1[td];
  [d0][td]overlay=0:0:shortest=1,format=yuv420p[d];
  [an][a][b][c][d]concat=n=5:v=1:a=0,setsar=1,format=yuv420p[v];
  [7:a]aresample=48000,atrim=0:13.8,asetpts=PTS-STARTPTS,afade=t=out:st=13.775:d=0.025[orig];
  [7:a]aresample=48000,atrim=0:6.868,asetpts=PTS-STARTPTS,adelay=13932|13932[song];
  [8:a]aresample=48000,atrim=13.45:13.80,asetpts=PTS-STARTPTS,highpass=f=300,lowpass=f=4000,afade=t=in:d=0.02,afade=t=out:st=0.31:d=0.04,asplit=2[e1][e2];
  [e1]volume=-9dB,adelay=13798|13798[eco1];
  [e2]volume=-16dB,adelay=14146|14146[eco2];
  [orig][song][eco1][eco2]amix=inputs=4:normalize=0:duration=longest,atrim=0:20.8,afade=t=out:st=20.4:d=0.4,alimiter=limit=0.84:level=false,aformat=channel_layouts=stereo[au]" \
  -map "[v]" -map "[au]" -t 20.8 \
  -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -r 30 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
echo "Exportado: $OUT"
