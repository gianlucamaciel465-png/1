#!/bin/bash
# Arma ROCCE_01_HIELO_REVELACION v02 (30 fps, 1080×1920):
#   0,000–5,133  hielo REAL de la referencia con la remera negra compuesta (acabado.py → FINAL_DIR, 154 cuadros):
#                golpes (ref 305–402) · levantar (440–469) · caída, choque y rotura (472–497) + "Remera roccé>"
#   5,133–7,333  IMG_7793 2,40–4,60 s  de espaldas, parado en el balcón: arranca cerca del estampado y abre hasta la
#                remera entera (hombros, mangas, largo): el calce
#   7,333–9,100  IMG_7887 1,90–3,667 s  sentado en las rocas frente al mar, "Founders Privée" en la espalda
# Audio: efectos sintetizados sincronizados con el metraje (sonido.py) hasta el corte; después el sonido real de
# cada toma (viento/ciudad del balcón realzado, mar). ≈ −14 LUFS, pico < −1 dBTP. Sin GPS ni metadatos.
# Uso: montar.sh TRABAJO_DIR FINAL_DIR SALIDA.mp4
set -euo pipefail
T="$1"; FD="$2"; OUT="$3"
O=/home/user/1/ORIGINALES
PY=${PY:-python3}
AQUI="$(cd "$(dirname "$0")" && pwd)"
NA=154; NB=66; NC=53
ffmpeg -v error -y \
  -framerate 30 -start_number 1 -i "$FD/%04d.png" \
  -ss 2.4 -t 2.3 -i "$O/IMG_7793.mov" -ss 1.9 -t 1.85 -i "$O/IMG_7887.mov" \
  -filter_complex "\
[0:v]trim=end_frame=$NA,setpts=N/30/TB,format=yuv444p,setsar=1[A];\
[1:v]scale=1080:1920:flags=lanczos:in_range=tv:out_range=tv:in_color_matrix=bt709:out_color_matrix=bt709,fps=30,trim=end_frame=$NB,setpts=N/30/TB,format=yuv444p,setsar=1[B];\
[2:v]scale=1080:1920:flags=lanczos:in_range=tv:out_range=tv:in_color_matrix=bt709:out_color_matrix=bt709,fps=30,trim=end_frame=$NC,setpts=N/30/TB,format=yuv444p,setsar=1[C];\
[A][B][C]concat=n=3:v=1:a=0,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -profile:v high -preset slow -crf 18 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -an "$T/v1b_video.mp4" </dev/null
N=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$T/v1b_video.mp4")
DUR=$($PY -c "print(f'{$N/30:.4f}')")
echo "video: $N cuadros ($DUR s)"
TC=$($PY -c "print(f'{$NA/30:.4f}')"); DB=$($PY -c "print(f'{$NB/30:.4f}')"); DC=$($PY -c "print(f'{$NC/30:.4f}')")
$PY "$AQUI/sonido.py" "$T/v1b_sfx.wav" "$DUR"
ffmpeg -v error -y -i "$T/v1b_sfx.wav" \
  -ss 2.4 -t "$DB" -i "$O/IMG_7793.mov" -ss 1.9 -t "$DC" -i "$O/IMG_7887.mov" \
  -filter_complex "\
[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,highpass=f=60,volume=16dB,afade=t=in:d=0.10,afade=t=out:st=$($PY -c "print($DB-0.06)"):d=0.06[b];\
[2:a]aresample=48000,pan=stereo|c0=c0|c1=c0,afade=t=in:d=0.06,afade=t=out:st=$($PY -c "print($DC-0.35)"):d=0.35[c];\
[b][c]concat=n=2:v=0:a=1,adelay=$($PY -c "print(int(round($TC*1000)))")|$($PY -c "print(int(round($TC*1000)))"),apad=whole_dur=$DUR[real];\
[0:a]apad=whole_dur=$DUR[fx];\
[fx][real]amix=inputs=2:normalize=0:duration=first[m]" -map "[m]" -ar 48000 -c:a pcm_s24le "$T/v1b_audio_bruto.wav" </dev/null
medir() { ffmpeg -v info -i "$1" -af ebur128=peak=true -f null - 2>&1 | $PY -c "import sys,re; t=sys.stdin.read(); print(re.findall(r'I:\s+(-?[0-9.]+) LUFS', t)[-1])"; }
I=$(medir "$T/v1b_audio_bruto.wav")
NS=$((N*1600))
G=$($PY -c "print(f'{-14.0-($I):.2f}')")
for pasada in 1 2; do
  ffmpeg -v error -y -i "$T/v1b_audio_bruto.wav" -af "volume=${G}dB,alimiter=limit=0.70:level=false:attack=1:release=50,apad=whole_len=$NS,atrim=end_sample=$NS" -ar 48000 -c:a pcm_s24le "$T/v1b_audio.wav" </dev/null
  I2=$(medir "$T/v1b_audio.wav"); G=$($PY -c "print(f'{$G+(-14.0-($I2)):.2f}')")
done
ffmpeg -v error -y -i "$T/v1b_video.mp4" -i "$T/v1b_audio.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -map_metadata -1 -movflags +faststart "$OUT" </dev/null
echo "listo: $OUT ($DUR s; ganancia ${G} dB desde ${I} LUFS)"
