#!/usr/bin/env bash
# ROCCE_lo_que_te_frena_v01 — adaptación de R1 (Neuron Visuals, "escalera y obstáculos", REF_15) para Roccé.
# Se conserva la animación, su música y su ritmo (tirones, corte de la soga, llegada arriba); se interviene:
#   - gancho "Lo que te frena / no está adelante." desde el primer cuadro hasta que se corta la soga;
#   - rótulos en español con la letra del original (Saira, OFL): MIEDO · QUÉ DIRÁN · DUDAS · FIACA · EXCUSAS,
#     borrando los ingleses con seguimiento y máscara (no quedan debajo);
#   - el protagonista lleva la remera blanca de Roccé: sigue su pose cuadro a cuadro, con la cabeza y la soga por
#     delante, desenfoque de movimiento y, de frente, el estampado real del pecho;
#   - SUCCESS → "GIVE HISTORY / YOUR NAME." con el mismo brillo y aparición;
#   - giro a lo real: la misma remera puesta frente al mar (IMG_7857) y placa de la casa (IMG_7896) con
#     "Drop Founders Privée —" / "01/11/2026" y una sola llamada: "Sé uno de los primeros 100.".
# Línea de tiempo (30 fps, 11,50 s):
#   0,00–7,10  R1 0,20–7,30 (animación intervenida). Soga: 3,80. Lema: 5,40 (aparece) → 7,10.
#   7,10–9,50  IMG_7857 2,90–5,30 (corte sobre el golpe de la música).
#   9,50–11,50 IMG_7896 4,15–6,15 acercada 1,16× + cierre (la toma termina en 6,17).
# Audio: música original de R1 (0,20–8,06) con fundido 7,36–7,86 + mar real de IMG_7857 (+3 dB; crece hasta una ola)
#        y de IMG_7896 (+10 dB, es más baja).
# Uso: scripts/lo_que_te_frena_v01.sh [SALIDA]     (S=scratchpad con demucs-env: Python con OpenCV y SciPy)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-EXPORTACIONES/ROCCE_lo_que_te_frena_v01.mp4}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe"; exit 1; }
S=${S:-/tmp/claude-0/-home-user-1/bd43937f-7b34-55cc-a48c-8ac864032e15/scratchpad}; CV=$S/demucs-env/bin/python
R1=REFERENCIAS/REF_15_neuronvisuals_soga_DeUC8-gxNIn.mp4
T=TRABAJO/frena; C=$T/clips; mkdir -p $C $T/seq60
ENC="-c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -an"

# 1) animación: cuadros, pose, rótulos, composición
[ -f $T/seq60/0483.png ] || ffmpeg -v error -y -i $R1 $T/seq60/%04d.png
[ -f $T/pose60.json ] || $CV -I scripts/frena/pose_heroe.py $T/seq60 $T/pose60.json 12 470 907 652
$CV -I scripts/frena/pose_salto.py $T/seq60 $T/pose60.json $T/pose60_fix.json > /dev/null
[ -f $T/rot60.json ] || $CV -I scripts/frena/seguir_rotulos.py $T/seq60 $T/rot60.json 6 310
python3 scripts/frena/textos_frena.py $T/textos > /dev/null
rm -rf $T/anim; $CV -I scripts/frena/componer_anim.py $T/seq60 $T/pose60_fix.json $T/rot60.json $T/textos $T/anim
ffmpeg -v error -y -framerate 30 -i $T/anim/%04d.png -vf "scale=out_range=tv:out_color_matrix=bt709,format=yuv420p,setsar=1" -frames:v 213 $ENC $C/A_anim.mp4

# 2) tomas reales
ffmpeg -v error -y -ss 2.90 -i ORIGINALES/IMG_7857.mov -vf "scale=1080:1920:flags=lanczos:out_range=tv,format=yuv420p,fps=30,setsar=1" -frames:v 72 $ENC $C/B_7857.mp4
ffmpeg -v error -y -ss 4.15 -i ORIGINALES/IMG_7896.mov -vf "crop=w=iw/1.16:h=ih/1.16:x=iw*0.024:y=ih*0.07,scale=1080:1920:flags=lanczos:in_range=pc:out_range=tv,format=yuv420p,fps=30,setsar=1" -frames:v 60 $ENC $C/C_7896.mp4

# 3) montaje
X=$T/textos
ov() { echo "[$1]format=rgba,fade=t=in:st=$2:d=${4:-0.15}:alpha=1[$3]"; }
ffmpeg -v error -stats -n \
  -i $C/A_anim.mp4 -i $C/B_7857.mp4 -i $C/C_7896.mp4 \
  -framerate 30 -loop 1 -t 11.5 -i $X/placa_fondo.png -framerate 30 -loop 1 -t 11.5 -i $X/placa1.png \
  -framerate 30 -loop 1 -t 11.5 -i $X/placa2.png -framerate 30 -loop 1 -t 11.5 -i $X/placa3.png \
  -i $R1 -i ORIGINALES/IMG_7857.mov -i ORIGINALES/IMG_7896.mov \
  -filter_complex "
  [0:v][1:v][2:v]concat=n=3:v=1:a=0,setsar=1,format=yuv420p[base];
  $(ov 3:v 9.50 g 0.25); $(ov 4:v 9.62 c1); $(ov 5:v 9.76 c2); $(ov 6:v 10.20 c3 0.18);
  [base][g]overlay=0:0:enable='gte(t,9.5)'[v1]; [v1][c1]overlay=0:0:enable='gte(t,9.62)'[v2];
  [v2][c2]overlay=0:0:enable='gte(t,9.76)'[v3]; [v3][c3]overlay=0:0:enable='gte(t,10.20)',format=yuv420p[v];
  [7:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0.2:8.06,asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st=7.36:d=0.5[m];
  [8:a]aresample=48000,aformat=channel_layouts=stereo,atrim=2.9:5.3,asetpts=PTS-STARTPTS,volume=${MAR1:-3}dB,afade=t=in:d=0.25,afade=t=out:st=2.3:d=0.1,adelay=7100|7100[a1];
  [9:a]aresample=48000,aformat=channel_layouts=stereo,atrim=4.15:6.15,asetpts=PTS-STARTPTS,volume=${MAR2:-10}dB,afade=t=in:d=0.08,afade=t=out:st=1.7:d=0.3,adelay=9500|9500[a2];
  [m][a1][a2]amix=inputs=3:normalize=0:duration=longest,atrim=0:11.5,volume=${GAN:-1}dB,alimiter=limit=${LIM:-0.76}:level=false[au]" \
  -map "[v]" -map "[au]" -t 11.5 \
  -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -r 30 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
echo "Exportado: $OUT"
