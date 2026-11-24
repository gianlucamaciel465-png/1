#!/usr/bin/env bash
# REAL-02 v1.1 — «¿Cuál se la lleva?» con los 2 cambios del dictamen de Roma (08_roma_dictamen_master_v1.md, 16/11/2026):
#   1) «3» a 240 px en x 860 / y 770, sobre la roca (f63–f73);
#   2) cierre en movimiento: P6 = 4625 c15–c89 (f184–f258) con «rocce.shop» desde f229 y el clic en f229;
#      P7 = foto de la ficha f259–f306 con acercamiento ×1,00 → ×1,06 sobre azul noche liso; «Con placa y número» / «del 001 al 100.».
# Lo demás sale de v1 tal cual: el video se EMPALMA por GOP cerrado (cuadros clave de v1 en f0, 46, 63, 94, 124, 184, 229, 289):
#   se copian sin recodificar los GOP de v1 f0–f45, f46–f62, f94–f123, f124–f183 y f184–f228 y se codifican solo f63–f93 y f229–f306,
#   con los mismos parámetros (mismo SPS/PPS). f74–f93 se recodifica porque en v1 comparte GOP con f63–f73 (ver hoja 09).
# Audio: misma mezcla con REAL02_VER=v1_1 (ambiente de 4625 hasta f258, clic en f229) y la MISMA ganancia que v1 (+2,0 dB),
#   así la mezcla es idéntica a v1 hasta f228.
# La receta de v1 (scripts/real02_v01.sh) no cambia: sin REAL02_VER, todos los scripts hacen v1.
#
# Uso: scripts/real02_v01_1.sh            Variables: T (carpeta de trabajo), PRUEBA=1 (no entrega ni escribe evidencia)
set -euo pipefail
cd "$(dirname "$0")/.."
R=scripts/real02
T1=TRABAJO/real02/v01                    # trabajo de v1 (base de v1; si falta, se rehace con scripts/real02/base.py)
T=${T:-TRABAJO/real02/v01_1}
PF=/mnt/project-files/piezas/REAL-02
V1="$PF/REAL-02_v1.mp4"                  # máster v1 aprobado en todo lo demás (huella de video 24b3aa7d…a410)
OUT=EXPORTACIONES/ROCCE_REAL02_cual_se_la_lleva_v01_1.mp4
PY=TRABAJO/real02/venv/bin/python
export REAL02_VER=v1_1
mkdir -p "$T/aud" "$T/tramos_v1"
if ! "$PY" -c "import scipy, numpy, PIL" 2>/dev/null; then
  python3 -m venv --system-site-packages TRABAJO/real02/venv
  TRABAJO/real02/venv/bin/pip install -q numpy==2.5.3 scipy==1.18.1 pillow==12.3.0
fi
[ "$(ffmpeg -v error -i "$V1" -map 0:v -c copy -f md5 -)" = "MD5=24b3aa7da7feae66d0d22013522fa410" ] || { echo "ERROR: $V1 no es el v1 aprobado"; exit 1; }

# 1) base v1.1: f0–f183 copiados de la base de v1 (md5 por plano comprobado), P6 largo y P7 nuevo
[ -s "$T1/base.rgb" ] || env -u REAL02_VER nice "$PY" $R/base.py "$T1/base.rgb" "$T1/base_info.json"
nice "$PY" $R/base_v1_1.py "$T/base.rgb" "$T/base_info.json" "$T1/base.rgb" "$T1/base_info.json"

# 2) máscaras y márgenes (P6 hasta f258)
nice "$PY" $R/mascaras.py "$T/base.rgb" "$T/mascaras.npz"
nice "$PY" $R/margenes.py "$T/mascaras.npz" "$T/margenes_v01_1.tsv"

# 3) md5 de cada cuadro compuesto (entrada del codificador), v1 contra v1.1
env -u REAL02_VER nice "$PY" $R/componer.py "$T1/base.rgb" --md5 "$T/entrada_md5_v1.txt"
nice "$PY" $R/componer.py "$T/base.rgb" --md5 "$T/entrada_md5_v1_1.txt"

# 4) video: tramos nuevos con los parámetros de v1 + GOP de v1 copiados -> empalme
nice "$PY" $R/componer.py "$T/base.rgb" "$T/tramo_f063-f093.mp4" 63 93
nice "$PY" $R/componer.py "$T/base.rgb" "$T/tramo_f229-f306.mp4" 229 306
ffmpeg -v error -y -i "$V1" -map 0:v -c copy -f segment -segment_frames 46,63,94,124,184,229,289 -reset_timestamps 1 -segment_format mp4 "$T/tramos_v1/seg%02d.mp4"
for f in "$T/tramo_f063-f093.mp4" "$T/tramo_f229-f306.mp4"; do      # el empalme exige el mismo SPS/PPS que v1
  [ "$(ffprobe -v error -select_streams v -show_entries stream=extradata -show_data -of csv=p=0 "$f")" = \
    "$(ffprobe -v error -select_streams v -show_entries stream=extradata -show_data -of csv=p=0 "$V1")" ] || { echo "ERROR: SPS/PPS distinto en $f"; exit 1; }
done
A=$(realpath "$T")
printf "file '%s'\n" "$A/tramos_v1/seg00.mp4" "$A/tramos_v1/seg01.mp4" "$A/tramo_f063-f093.mp4" "$A/tramos_v1/seg03.mp4" \
  "$A/tramos_v1/seg04.mp4" "$A/tramos_v1/seg05.mp4" "$A/tramo_f229-f306.mp4" > "$T/empalme.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$T/empalme.txt" -c copy -movflags +faststart "$T/video_v01_1.mp4"

# 5) audio: mezcla v1.1 con la ganancia de v1 (+2,0 dB) -> limitador sin autonivelado -> AAC-LC 48 kHz estéreo
nice "$PY" $R/mezcla.py "$T/aud" 25
ffmpeg -v error -y -i "$T/aud/mezcla_pre.wav" -af "volume=2.0dB,alimiter=limit=0.84:level=false:latency=1" -c:a pcm_f32le "$T/aud/mezcla_m14.wav"
ffmpeg -v error -y -i "$T/aud/mezcla_m14.wav" -c:a aac -profile:a aac_low -b:a 192k -ar 48000 -ac 2 "$T/aud/audio_final.m4a"

# 6) máster: streams copiados, sin metadatos (sin ubicación), faststart
ffmpeg -v error -i "$T/video_v01_1.mp4" -i "$T/aud/audio_final.m4a" -map 0:v:0 -map 1:a:0 -c copy \
  -map_metadata -1 -map_metadata:s:v -1 -map_metadata:s:a -1 \
  -metadata:s:v:0 handler_name=VideoHandler -metadata:s:a:0 handler_name=SoundHandler \
  -movflags +faststart -y "$T/REAL-02_v1_1.mp4"
ffmpeg -v error -i "$T/REAL-02_v1_1.mp4" -f null - && echo "decodifica completo"
ffmpeg -v error -i "$T/REAL-02_v1_1.mp4" -map 0:v -c copy -f md5 -; ffmpeg -v error -i "$T/REAL-02_v1_1.mp4" -map 0:a -c copy -f md5 -
[ "${PRUEBA:-0}" = 1 ] && exit 0

# 7) entrega sin sobrescribir (v1 se conserva) y evidencia sobre la copia de /mnt/project-files
[ -e "$OUT" ] && echo "AVISO: $OUT ya existe; no se sobrescribe" || cp "$T/REAL-02_v1_1.mp4" "$OUT"
[ -e "$PF/REAL-02_v1_1.mp4" ] && echo "AVISO: $PF/REAL-02_v1_1.mp4 ya existe; no se sobrescribe" || cp "$T/REAL-02_v1_1.mp4" "$PF/REAL-02_v1_1.mp4"
REAL02_VER=v1_1 nice "$PY" $R/comparar_tramo.py "$V1" "$PF/REAL-02_v1_1.mp4" "$T/base.rgb" 74 93 "$T/comparacion_f74-f93.json"
E="$PF/evidencia_v1_1"
nice "$PY" $R/evidencia_v1_1.py "$PF/REAL-02_v1_1.mp4" "$V1" "$T" "$E"
cp "$T/margenes_v01_1.tsv" "$T/base_info.json" "$T/aud/mezcla_eventos.json" "$T/entrada_md5_v1.txt" "$T/entrada_md5_v1_1.txt" \
   "$T/comparacion_f74-f93.json" "$T/empalme.txt" "$E/"
