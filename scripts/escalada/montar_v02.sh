#!/bin/bash
# Arma ROCCE_02_HACETE_FOUNDER v02: animación intervenida (cuadros 1–473 = 0–15,77 s, comp_v3) + placa v02
# (135 cuadros = 4,5 s: todo legible desde 0,6 s → ≈ 3,9 s útiles de lectura) = 20,27 s.
# Audio: el de la referencia hasta el final de la animación y, bajo la placa, la misma canción desde 0,81 s del reel
# (como cuando el reel se repite; deja los golpes en la grilla de 80 BPM), entrada 0,25 s, salida 0,9 s.
# Sonoridad ≈ −14 LUFS, pico < −1 dBTP (dos pasadas). Audio de exactamente N × 1600 muestras. Sin metadatos.
# Uso: montar_v02.sh TRABAJO_DIR SALIDA.mp4 AUDIO_REFERENCIA.wav
set -euo pipefail
T="$1"; OUT="$2"; AUD="$3"; PY=${PY:-python3}
NA=473; NP=135
FR="$T/v3_frames"; rm -rf "$FR"; mkdir -p "$FR"
n=0
for i in $(seq 1 $NA); do n=$((n+1)); ln -s "$T/comp_v3/$(printf %04d $i).png" "$FR/$(printf %04d $n).png"; done
for i in $(seq 1 $NP); do n=$((n+1)); ln -s "$T/placa_v02/$(printf %04d $i).png" "$FR/$(printf %04d $n).png"; done
A1=$($PY -c "print(f'{$NA/30:.4f}')"); A2=$($PY -c "print(f'{$NP/30:.4f}')")
ffmpeg -v error -y -i "$AUD" -filter_complex "\
[0:a]atrim=0:$A1,asetpts=N/SR/TB[a1];\
[0:a]atrim=0.81:$($PY -c "print(f'{0.81+$NP/30:.4f}')"),asetpts=N/SR/TB,afade=t=in:d=0.25,afade=t=out:st=$($PY -c "print(f'{$NP/30-0.9:.4f}')"):d=0.9[a2];\
[a1][a2]concat=n=2:v=0:a=1[a]" -map "[a]" -ar 48000 -ac 2 -c:a pcm_s24le "$T/v3_audio_bruto.wav" </dev/null
medir() { ffmpeg -v info -i "$1" -af ebur128=peak=true -f null - 2>&1 | $PY -c "import sys,re; t=sys.stdin.read(); print(re.findall(r'I:\s+(-?[0-9.]+) LUFS', t)[-1])"; }
I=$(medir "$T/v3_audio_bruto.wav"); NS=$((n*1600)); G=$($PY -c "print(f'{-14.0-($I):.2f}')")
for pasada in 1 2; do
  ffmpeg -v error -y -i "$T/v3_audio_bruto.wav" -af "volume=${G}dB,alimiter=limit=0.70:level=false:attack=1:release=50,apad=whole_len=$NS,atrim=end_sample=$NS" -ar 48000 -c:a pcm_s24le "$T/v3_audio.wav" </dev/null
  I2=$(medir "$T/v3_audio.wav"); G=$($PY -c "print(f'{$G+(-14.0-($I2)):.2f}')")
done
ffmpeg -v error -y -framerate 30 -i "$FR/%04d.png" -i "$T/v3_audio.wav" \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" -c:v libx264 -profile:v high -preset slow -crf 17 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -map_metadata -1 -movflags +faststart "$OUT" </dev/null
echo "listo: $OUT ($n cuadros; ganancia ${G} dB desde ${I} LUFS)"
