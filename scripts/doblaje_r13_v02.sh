#!/usr/bin/env bash
# ROCCE_doblaje_v02 — R13 (Instagram De2oes9oLFO, isaiahrosslabs, video hecho con IA):
# video original intacto hasta 11,417 s (cuadro 274, cuando el personaje abre la boca para hablar en el original;
# se conserva su sonrisa de los cuadros 256–272). Desde ahí dice
# "Demostrá que valés más. Primero de noviembre. Drop Founders Privée." con sincronización labial
# (MuseTalk 1.5, CPU; entrada gradual de la boca en 3 cuadros) y voz sintética en español
# (Chatterbox Multilingual, timbre tomado de su línea original). El plano final se extiende con sus propios
# cuadros en ida y vuelta. Formato vertical con el cuadro 4:3 completo sobre fondo desenfocado.
# Cambios frente a v01: empalme en 274 (antes 267, cortaba la sonrisa), ambiente extendido completo
# (en v01 quedaba mudo el último medio segundo), voz al nivel de la original (v01: −6 dB por el eco) y techo −1,5 dB.
# Uso: scripts/doblaje_r13_v02.sh VOZ.wav [SALIDA]  (voz armada, 48 kHz mono, empieza en la primera palabra)
#      SKIP_LIPSYNC=1 reutiliza $W/dub_out si ya tiene los cuadros de esta receta.
set -euo pipefail
cd "$(dirname "$0")/.."
VOZ="$1"; OUT="${2:-EXPORTACIONES/ROCCE_doblaje_v02.mp4}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe"; exit 1; }
REF=REFERENCIAS/REF_13_isaiahrosslabs_domino_De2oes9oLFO.mp4
BED=AUDIO/R13_base_sin_voz_demucs.flac
S=${S:-/tmp/claude-0/-home-user-1/bd43937f-7b34-55cc-a48c-8ac864032e15/scratchpad}
W=$S/dub; MODELS=$S/mt_models; PY=$S/demucs-env/bin/python
FPS=24; START=274                      # 11,417 s: termina la sonrisa y empieza a abrir la boca (voz original en 11,53 s)
T0=$(awk "BEGIN{print $START/$FPS}")
DV=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VOZ")
N=$(awk "BEGIN{print int(($DV+0.5)*$FPS+0.999)}")
END=$(awk "BEGIN{print ($START+$N)/$FPS}")
echo "voz ${DV}s → plano doblado de $N cuadros desde ${T0}s, fin ${END}s"
if [ "${SKIP_LIPSYNC:-0}" = 1 ] && [ "$(ls $W/dub_out/*.png 2>/dev/null | wc -l)" = "$N" ]; then
  echo "reutilizando $W/dub_out"
else
  # 1) cuadros fuente (cara derecha = girados 90° antihorario), ida y vuelta desde el último cuadro (346)
  rm -rf $W/dub_in $W/dub_out; mkdir -p $W/dub_in
  python3 -I - "$W" "$START" "$N" <<'PYEOF'
import sys, os
W, start, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
last = 346; idx = []; i = start; step = 1
while len(idx) < n:
    idx.append(i)
    if i == last: step = -1
    i += step
for k, j in enumerate(idx):
    os.symlink(f"{W}/rot_all/{j:04d}.png", f"{W}/dub_in/{k:04d}.png")
print("cuadros fuente:", idx[0], "…", idx[-1], "(vuelve desde 346)" if max(idx) == last and idx[-1] != last else "")
PYEOF
  # 2) audio para la sincronización (16 kHz, misma duración que el plano)
  ffmpeg -v error -y -i "$VOZ" -af "apad,atrim=0:$(awk "BEGIN{print $N/$FPS}")" -ac 1 -ar 16000 $W/voz16k.wav
  # 3) sincronización labial (recorte y elipses medidos en el cuadro 267; el seguimiento corrige el desplazamiento)
  $PY -I scripts/lipsync_musetalk.py $W/dub_in $W/voz16k.wav $W/dub_out $MODELS 310 160 845 910 690 745 205 155 $FPS 712 712 150 70 648 3
fi
# 4) ambiente: base sin voz desde 11,36 s y luego el tramo silencioso 12,8–13,8 s en bucle (fundidos de 0,25 s).
#    Cada tramo es una entrada separada (con asplit+atrim los bucles salían vacíos). Queda afuera el golpe de 14,0–14,3 s.
B0=11.36
ffmpeg -v error -y -ss $B0 -t 2.54 -i "$BED" -ss 12.8 -t 1 -i "$BED" -ss 12.8 -t 1 -i "$BED" -ss 12.8 -t 1 -i "$BED" -ss 12.8 -t 1 -i "$BED" -filter_complex "
  [0:a][1:a]acrossfade=d=0.25[x1]; [x1][2:a]acrossfade=d=0.25[x2]; [x2][3:a]acrossfade=d=0.25[x3]; [x3][4:a]acrossfade=d=0.25,aresample=48000[x4]" -map "[x4]" $W/bed_ext.wav
DB=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $W/bed_ext.wav)
awk "BEGIN{exit !($B0+$DB >= $END)}" || { echo "ERROR: ambiente corto (${DB}s)"; exit 1; }
# 5) montaje
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
T1=$(mktemp); printf '%s' "DEMOSTRÁ QUE VALÉS MÁS." > "$T1"
T2=$(mktemp); printf '%s' "1/11 — DROP FOUNDERS PRIVÉE" > "$T2"
L2=${L2:-1.62}   # segundos desde el inicio de la voz hasta "Primero de noviembre"
DMS=$(awk "BEGIN{print int($T0*1000)}")
ffmpeg -v error -stats -n \
  -i "$REF" \
  -framerate $FPS -i $W/dub_out/%04d.png \
  -i $W/bed_ext.wav -i "$VOZ" \
  -filter_complex "
  [0:v]trim=end_frame=$START,setpts=PTS-STARTPTS,format=yuv420p[a];
  [1:v]transpose=1,setsar=1,format=yuv420p,setpts=PTS-STARTPTS[b];
  [a][b]concat=n=2:v=1:a=0,fps=$FPS,split[f][bgsrc];
  [bgsrc]scale=-2:1920,crop=1080:1920,boxblur=40:4,eq=brightness=-0.12:saturation=0.8[bg];
  [f]scale=1080:810:flags=lanczos[fg];
  [bg][fg]overlay=0:555,
    drawtext=fontfile=$FONT:textfile=$T1:fontsize=66:fontcolor=0xA9C8E8:x=(w-text_w)/2:y=1440:shadowcolor=black@0.6:shadowx=2:shadowy=3:enable='gte(t,$T0)',
    drawtext=fontfile=$FONT:textfile=$T2:fontsize=48:fontcolor=white:x=(w-text_w)/2:y=1535:shadowcolor=black@0.6:shadowx=2:shadowy=3:enable='gte(t,$T0+$L2)',
    setsar=1,format=yuv420p[v];
  [0:a]atrim=0:11.40,asetpts=PTS-STARTPTS,aresample=48000,afade=t=out:st=11.36:d=0.04[o];
  [2:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.04,apad[bd];
  [o][bd]concat=n=2:v=0:a=1,atrim=0:$END,afade=t=out:st=$(awk "BEGIN{print $END-0.3}"):d=0.3[mix];
  [3:a]aresample=48000,highpass=f=90,aecho=1.0:1.0:28|46:0.10|0.06,pan=stereo|c0=c0|c1=c0,adelay=$DMS|$DMS,apad,atrim=0:$END[vz];
  [mix][vz]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.84:level=false,aformat=channel_layouts=stereo[au]" \
  -map "[v]" -map "[au]" -t $END \
  -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -r $FPS -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
rm -f "$T1" "$T2"; echo "Exportado: $OUT (${END}s)"
