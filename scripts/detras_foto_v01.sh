#!/usr/bin/env bash
# ROCCE_detras_foto_v01 — "Así se hace una foto Roccé": la sesión real (Gianluca fotografiando las remeras en las
# rocas, 11/10/2026) → el disparo → la foto. Material propio; sin música (no hay pista con uso permitido), sin voz.
# Texto exacto; cierre de campaña "Drop Founders Privée — 01/11/2026".
#
# Montaje (30 fps, 322 cuadros = 10,73 s):
#   A  0,000–3,733  IMG_7884 0,00–3,73: Gianluca agachado apunta con el celular a la blanca; la cámara pasa por
#                   encima de su hombro y llega a la remera cuando empieza a romper una ola detrás.
#                   Texto "Así se hace una foto Roccé." (0,25–3,3 s, arriba, sobre el mar oscurecido).
#   F1 3,733–5,733  disparo (destello blanco 0,2 s + obturador sintetizado) → foto PRODUCTO/blanca_espalda_roca_ola.jpg
#                   como copia con borde blanco sobre la misma foto desenfocada, acercamiento lento 1,00→1,04.
#   B  5,733–7,233  IMG_7887 1,90–3,40: Gianluca sentado con la negra puesta fotografía la blanca.
#   F2 7,233–8,733  segundo disparo → PRODUCTO/detras_escena_negra_puesta_fotografia_blanca_rocas.jpg.
#   Z  8,733–10,733 IMG_7896 4,15–6,15 acercada 1,16× + "Drop Founders Privée —" / "01/11/2026".
# La foto F1 es de la misma sesión (misma roca, luz y ola); las fotos no traen fecha en sus metadatos, así que
# el montaje no afirma con texto que salió de ese disparo exacto.
# Uso: scripts/detras_foto_v01.sh [SALIDA]
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-EXPORTACIONES/ROCCE_detras_foto_v01.mp4}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe"; exit 1; }
T=TRABAJO/detras_foto; C=$T/clips; X=$T/textos; mkdir -p $C $X
ENC="-c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -an"

# 1) tomas de video (4K SDR) y copias de las fotos (2 s / 1,5 s con acercamiento)
ffmpeg -v error -y -ss 0.00 -i ORIGINALES/IMG_7884.mov -vf "scale=1080:1920:flags=lanczos:out_range=tv,format=yuv420p,fps=30,setsar=1" -frames:v 112 $ENC $C/A_7884.mp4
ffmpeg -v error -y -ss 1.90 -i ORIGINALES/IMG_7887.mov -vf "scale=1080:1920:flags=lanczos:out_range=tv,format=yuv420p,fps=30,setsar=1" -frames:v 45 $ENC $C/B_7887.mp4
ffmpeg -v error -y -ss 4.15 -i ORIGINALES/IMG_7896.mov -vf "crop=w=iw/1.16:h=ih/1.16:x=iw*0.024:y=ih*0.07,scale=1080:1920:flags=lanczos:in_range=pc:out_range=tv,format=yuv420p,fps=30,setsar=1" -frames:v 60 $ENC $C/Z_7896.mp4
copia() {  # foto 3:4 entera como copia impresa (borde blanco 14 px) sobre la misma foto desenfocada
  local src=$1 n=$2 out=$3
  ffmpeg -v error -y -loop 1 -framerate 30 -i "$src" -filter_complex "
    [0:v]split[a][b];
    [a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:3,eq=brightness=-0.18:saturation=0.85[fondo];
    [b]scale=880:-2:flags=lanczos,pad=iw+28:ih+28:14:14:white[foto];
    [fondo][foto]overlay=(W-w)/2:(H-h)/2,format=yuv420p,
    zoompan=z='1+0.04*on/$n':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,setsar=1" \
    -frames:v $n $ENC "$out"
}
copia PRODUCTO/blanca_espalda_roca_ola.jpg 60 $C/F1.mp4
copia PRODUCTO/detras_escena_negra_puesta_fotografia_blanca_rocas.jpg 45 $C/F2.mp4

# 2) textos y obturador
python3 scripts/texto_png.py $X/titulo.png 66 330 "Así se hace una foto Roccé.|#FFFFFF"
python3 scripts/texto_png.py $X/cierre1.png 56 330 "Drop Founders Privée —|#FFFFFF"
python3 scripts/texto_png.py $X/cierre2.png 124 460 "01/11/2026|#FFFFFF"
python3 scripts/obturador.py $T/obturador.wav -6

# 3) montaje
OSCURO="geq=lum='lum(X,Y)*(1-0.5*max(0,1-Y/850))':cb='cb(X,Y)':cr='cr(X,Y)'"
ffmpeg -v error -stats -n \
  -i $C/A_7884.mp4 -i $C/F1.mp4 -i $C/B_7887.mp4 -i $C/F2.mp4 -i $C/Z_7896.mp4 \
  -framerate 30 -loop 1 -t 3.7333 -i $X/titulo.png \
  -framerate 30 -loop 1 -t 2.0 -i $X/cierre1.png -framerate 30 -loop 1 -t 2.0 -i $X/cierre2.png \
  -i ORIGINALES/IMG_7884.mov -i ORIGINALES/IMG_7887.mov -i ORIGINALES/IMG_7896.mov -i $T/obturador.wav \
  -filter_complex "
  [0:v]$OSCURO,setpts=PTS-STARTPTS[a0];
  [5:v]format=rgba,fade=t=in:st=0.25:d=0.2:alpha=1,fade=t=out:st=3.15:d=0.2:alpha=1[ta];
  [a0][ta]overlay=0:0:shortest=1,format=yuv420p[a];
  [1:v]fade=t=in:st=0:d=0.22:color=white,setpts=PTS-STARTPTS[f1];
  [2:v]setpts=PTS-STARTPTS[b];
  [3:v]fade=t=in:st=0:d=0.22:color=white,setpts=PTS-STARTPTS[f2];
  [4:v]$OSCURO,setpts=PTS-STARTPTS[z0];
  [6:v]format=rgba,fade=t=in:st=0.12:d=0.15:alpha=1[c1];[7:v]format=rgba,fade=t=in:st=0.30:d=0.15:alpha=1[c2];
  [z0][c1]overlay=0:0:shortest=1[z1];[z1][c2]overlay=0:0:shortest=1[z];
  [a][f1][b][f2][z]concat=n=5:v=1:a=0,setsar=1,format=yuv420p[v];
  [8:a]aresample=48000,atrim=0:5.233,asetpts=PTS-STARTPTS,afade=t=out:st=4.83:d=0.4[s1];
  [9:a]aresample=48000,atrim=1.4:4.9,asetpts=PTS-STARTPTS,afade=t=in:d=0.4,afade=t=out:st=3.1:d=0.4,adelay=5233|5233[s2];
  [10:a]aresample=48000,atrim=2.6:6.15,asetpts=PTS-STARTPTS,volume=6dB,afade=t=in:d=0.4,afade=t=out:st=3.05:d=0.5,adelay=7183|7183[s3];
  [11:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[o1][o2];
  [o1]adelay=3733|3733[ob1];[o2]adelay=7233|7233[ob2];
  [s1][s2][s3][ob1][ob2]amix=inputs=5:normalize=0:duration=longest,atrim=0:10.7333,volume=${GAN:-9}dB,alimiter=limit=0.78:level=false,aformat=channel_layouts=stereo[au]" \
  -map "[v]" -map "[au]" -t 10.7333 \
  -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -r 30 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
echo "Exportado: $OUT"
