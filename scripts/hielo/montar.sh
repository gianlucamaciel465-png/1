#!/bin/bash
# Arma ROCCE_01_HIELO_REVELACION (30 fps, 1080×1920):
#   A  0,000–4,667  escena 3D (render a 720×1280 → 1080×1920, contraste suave, nitidez leve) + "Remera roccé>"
#   B  4,667–6,133  IMG_7887 2,20–3,67 s  Gianluca de espaldas con la negra (ROCCÉ + Founders Privée), corte directo
#                    desde el acercamiento al mismo estampado
#   C  6,133–8,533  IMG_7885 0,00–2,40 s  sentado en las rocas, ola detrás, la remera en movimiento natural
#   D  8,533–9,933  IMG_7884 0,00–1,40 s  agachado sacando la foto de la blanca (caída de la tela al agacharse)
# Audio: efectos sintetizados (sonido.py) en A y su golpe de corte; desde B el sonido real de cada toma (mar),
# con fundidos cortos entre tomas. Sonoridad ≈ −14 LUFS, pico < −1 dBTP. Sin GPS ni metadatos de las tomas.
# Uso: montar.sh TRABAJO_DIR RENDER_DIR SALIDA.mp4
set -euo pipefail
T="$1"; RD="$2"; OUT="$3"
O=/home/user/1/ORIGINALES
PY=${PY:-python3}
NA=140                                              # cuadros de la escena 3D (0–139)
# --- video
ffmpeg -v error -y \
  -framerate 30 -start_number 0 -i "$RD/%04d.png" -i "$T/hielo/etiqueta.png" \
  -ss 2.2 -t 1.4667 -i "$O/IMG_7887.mov" -ss 0 -t 2.4 -i "$O/IMG_7885.mov" -ss 0 -t 1.4 -i "$O/IMG_7884.mov" \
  -filter_complex "\
[0:v]trim=end_frame=$NA,setpts=N/30/TB,scale=1080:1920:flags=lanczos,curves=master='0/0 0.22/0.18 0.6/0.62 1/1',unsharp=5:5:0.45,format=rgba[a0];\
[a0][1:v]overlay=0:0:format=auto,format=yuv444p,setsar=1[A];\
[2:v]scale=1080:1920:flags=lanczos:in_range=tv:out_range=tv:in_color_matrix=bt709:out_color_matrix=bt709,fps=30,trim=end_frame=44,setpts=N/30/TB,format=yuv444p,setsar=1[B];\
[3:v]scale=1080:1920:flags=lanczos:in_range=tv:out_range=tv:in_color_matrix=bt709:out_color_matrix=bt709,fps=30,trim=end_frame=72,setpts=N/30/TB,format=yuv444p,setsar=1[C];\
[4:v]scale=1080:1920:flags=lanczos:in_range=tv:out_range=tv:in_color_matrix=bt709:out_color_matrix=bt709,fps=30,trim=end_frame=42,setpts=N/30/TB,format=yuv444p,setsar=1[D];\
[A][B][C][D]concat=n=4:v=1:a=0,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -profile:v high -preset slow -crf 17 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -an "$T/v1_video.mp4" </dev/null
N=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$T/v1_video.mp4")
DUR=$($PY -c "print(f'{$N/30:.4f}')")
echo "video: $N cuadros ($DUR s)"
# --- audio
TA=$($PY -c "print(f'{$NA/30:.4f}')")
$PY /home/user/1/scripts/hielo/sonido.py "$T/hielo/v01/escena.json" "$T/v1_sfx.wav" "$DUR" "$TA" >/dev/null
ffmpeg -v error -y -i "$T/v1_sfx.wav" \
  -ss 2.2 -t 1.4667 -i "$O/IMG_7887.mov" -ss 0 -t 2.4 -i "$O/IMG_7885.mov" -ss 0 -t 1.4 -i "$O/IMG_7884.mov" \
  -filter_complex "\
[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,afade=t=in:d=0.12,afade=t=out:st=1.40:d=0.06,volume=1.0[b];\
[2:a]aresample=48000,pan=stereo|c0=c0|c1=c0,afade=t=in:d=0.06,afade=t=out:st=2.34:d=0.06[c];\
[3:a]aresample=48000,pan=stereo|c0=c0|c1=c0,volume=4dB,afade=t=in:d=0.06,afade=t=out:st=1.10:d=0.30[d];\
[b][c][d]concat=n=3:v=0:a=1,adelay=$($PY -c "print(int(round($NA/30*1000)))")|$($PY -c "print(int(round($NA/30*1000)))"),apad=whole_dur=$DUR[real];\
[0:a]apad=whole_dur=$DUR[fx];\
[fx][real]amix=inputs=2:normalize=0:duration=first[m]" -map "[m]" -ar 48000 -c:a pcm_s24le "$T/v1_audio_bruto.wav" </dev/null
I=$(ffmpeg -v info -i "$T/v1_audio_bruto.wav" -af ebur128=peak=true -f null - 2>&1 | $PY -c "import sys,re; t=sys.stdin.read(); print(re.findall(r'I:\s+(-?[0-9.]+) LUFS', t)[-1])")
# dos pasadas: ganancia + limitador (techo −3 dB de muestra, para que el pico real quede < −1 dBTP después del AAC);
# la segunda corrige lo que bajó el limitador. El audio dura exactamente lo mismo que el video (N × 1600 muestras).
NS=$((N*1600))
medir() { ffmpeg -v info -i "$1" -af ebur128=peak=true -f null - 2>&1 | $PY -c "import sys,re; t=sys.stdin.read(); print(re.findall(r'I:\s+(-?[0-9.]+) LUFS', t)[-1])"; }
G=$($PY -c "print(f'{-14.0-($I):.2f}')")
for pasada in 1 2; do
  ffmpeg -v error -y -i "$T/v1_audio_bruto.wav" -af "volume=${G}dB,alimiter=limit=0.70:level=false:attack=1:release=50,apad=whole_len=$NS,atrim=end_sample=$NS" -ar 48000 -c:a pcm_s24le "$T/v1_audio.wav" </dev/null
  I2=$(medir "$T/v1_audio.wav"); G=$($PY -c "print(f'{$G+(-14.0-($I2)):.2f}')")
done
ffmpeg -v error -y -i "$T/v1_video.mp4" -i "$T/v1_audio.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -map_metadata -1 -movflags +faststart "$OUT" </dev/null
echo "listo: $OUT ($DUR s; ganancia ${G} dB desde ${I} LUFS)"
