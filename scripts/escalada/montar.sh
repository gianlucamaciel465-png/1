#!/bin/bash
# Arma ROCCE_02_HACETE_FOUNDER: animación intervenida (cuadros 1–473 = 0–15,77 s) + placa (127 cuadros) = 20,0 s.
# Audio: el de la referencia hasta el final de la animación (con su caída) y, bajo la placa, la misma canción desde
# 0,81 s del reel (el reel vuelve a empezar ahí al repetirse; 0,81 s deja los golpes en la misma grilla, 80 BPM),
# con entrada de 0,25 s y salida de 0,9 s. Sonoridad ≈ −14 LUFS, pico < −1 dBTP.
# Uso: montar.sh TRABAJO_DIR SALIDA.mp4 AUDIO_REFERENCIA.wav
set -euo pipefail
T="$1"; OUT="$2"; AUD="$3"
FR="$T/v2_frames"; rm -rf "$FR"; mkdir -p "$FR"
n=0
for i in $(seq 1 473); do n=$((n+1)); ln -s "$T/comp_v2/$(printf %04d $i).png" "$FR/$(printf %04d $n).png"; done
for i in $(seq 1 127); do n=$((n+1)); ln -s "$T/placa/$(printf %04d $i).png" "$FR/$(printf %04d $n).png"; done
DUR=$(python3 -c "print(f'{$n/30:.4f}')")
A1=$(python3 -c "print(f'{473/30:.4f}')"); A2=$(python3 -c "print(f'{127/30:.4f}')")
ffmpeg -v error -y -i "$AUD" -filter_complex "\
[0:a]atrim=0:$A1,asetpts=N/SR/TB[a1];\
[0:a]atrim=0.81:$(python3 -c "print(f'{0.81+127/30:.4f}')"),asetpts=N/SR/TB,afade=t=in:d=0.25,afade=t=out:st=$(python3 -c "print(f'{127/30-0.9:.4f}')"):d=0.9[a2];\
[a1][a2]concat=n=2:v=0:a=1[a]" -map "[a]" -ar 48000 -ac 2 -c:a pcm_s24le "$T/v2_audio_bruto.wav" </dev/null
# sonoridad: medir y llevar a −14 LUFS (ganancia fija) + limitador sin nivelar
I=$(ffmpeg -v info -i "$T/v2_audio_bruto.wav" -af ebur128=peak=true -f null - 2>&1 | python3 -c "import sys,re; t=sys.stdin.read(); print(re.findall(r'I:\s+(-?[0-9.]+) LUFS', t)[-1])")
G=$(python3 -c "print(f'{-14.0-($I):.2f}')")
ffmpeg -v error -y -i "$T/v2_audio_bruto.wav" -af "volume=${G}dB,alimiter=limit=0.84:level=false:attack=2:release=60" -ar 48000 -c:a pcm_s24le "$T/v2_audio.wav" </dev/null
ffmpeg -v error -y -framerate 30 -i "$FR/%04d.png" -i "$T/v2_audio.wav" \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" -c:v libx264 -profile:v high -preset slow -crf 17 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -map_metadata -1 -movflags +faststart -shortest "$OUT" </dev/null
echo "listo: $OUT ($DUR s; ganancia ${G} dB desde ${I} LUFS)"
