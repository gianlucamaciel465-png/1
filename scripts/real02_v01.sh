#!/usr/bin/env bash
# REAL-02 v01 — «¿Cuál se la lleva?» (guion G1 de Fede aprobado por Roma el 16/11/2026, con 6 condiciones).
# Solo tomas reales (IMG_4641, IMG_7884, IMG_4627, IMG_3375, IMG_7857, IMG_4625) + la foto de la ficha rc-blanca-placas.jpg.
# Sin voz. Música propia sintetizada (sin material de terceros). Máster 1080x1920, 30 fps, 307 cuadros (10,233 s).
#
# Uso: scripts/real02_v01.sh            (rehace todo desde ORIGINALES/ y deja el máster + la evidencia)
# Intermedios en TRABAJO/real02/v01/ (fuera de git). El MP4 queda fuera del repo público (.gitignore: EXPORTACIONES/ROCCE_REAL02_*).
# Entorno: Python 3.13 con numpy 2.5.3, scipy 1.18.1, Pillow 12.3.0; FFmpeg 6.1.1 (libx264, aac, zscale).
set -euo pipefail
cd "$(dirname "$0")/.."
R=scripts/real02
T=TRABAJO/real02/v01
PF=/mnt/project-files/piezas/REAL-02
OUT=EXPORTACIONES/ROCCE_REAL02_cual_se_la_lleva_v01.mp4
ATT=25          # dB que baja el ambiente de 4627 entre f74 y f78 (con 18 dB, el guion, f78–f93 quedaba en ≈ −37 dBFS RMS, no en ≈ −45)
mkdir -p "$T/aud"

# 0) entorno aislado (venv con los paquetes del sistema + scipy)
PY=TRABAJO/real02/venv/bin/python
if ! "$PY" -c "import scipy, numpy, PIL" 2>/dev/null; then
  python3 -m venv --system-site-packages TRABAJO/real02/venv
  TRABAJO/real02/venv/bin/pip install -q numpy==2.5.3 scipy==1.18.1 pillow==12.3.0
fi

# 1) base de imagen: 7 planos al cuadro (tonemap HLG->SDR del CLAUDE.md + ganancias medidas sobre la tela), 307 cuadros rgb24
nice "$PY" $R/base.py "$T/base.rgb" "$T/base_info.json"

# 2) máscara real de la remera y de la espuma por cuadro; 3) distancia de cada texto a la remera y a la espuma
nice "$PY" $R/mascaras.py "$T/base.rgb" "$T/mascaras.npz"
nice "$PY" $R/margenes.py "$T/mascaras.npz" "$T/margenes_v01.tsv"

# 4) imagen final: base + degradé superior (P1, P3, P6) + textos T1–T8 -> H.264 High 4.0, BT.709, 30 fps
nice "$PY" $R/componer.py "$T/base.rgb" "$T/video_v01.mp4"

# 5) mezcla: ambiente real + efectos + música propia; −14 LUFS con limitador sin autonivelado; AAC-LC 48 kHz estéreo
nice "$PY" $R/mezcla.py "$T/aud" "$ATT"
I=$(ffmpeg -hide_banner -nostats -i "$T/aud/mezcla_pre.wav" -af ebur128=framelog=verbose -f null - 2>&1 | sed -n '/Summary/,$p' | awk '/I:/{print $2; exit}')
G=$(python3 -c "print(round(-14 - ($I), 2))")
echo "sonoridad previa $I LUFS -> ganancia $G dB"
ffmpeg -v error -y -i "$T/aud/mezcla_pre.wav" -af "volume=${G}dB,alimiter=limit=0.84:level=false:latency=1" -c:a pcm_f32le "$T/aud/mezcla_m14.wav"
ffmpeg -v error -y -i "$T/aud/mezcla_m14.wav" -c:a aac -profile:a aac_low -b:a 192k -ar 48000 -ac 2 "$T/aud/audio_final.m4a"

# 6) máster: streams copiados, sin metadatos de las tomas (sin GPS), faststart
ffmpeg -v error -i "$T/video_v01.mp4" -i "$T/aud/audio_final.m4a" -map 0:v:0 -map 1:a:0 -c copy \
  -map_metadata -1 -map_metadata:s:v -1 -map_metadata:s:a -1 \
  -metadata:s:v:0 handler_name=VideoHandler -metadata:s:a:0 handler_name=SoundHandler \
  -movflags +faststart -y "$T/REAL-02_v1.mp4"
ffmpeg -v error -i "$T/REAL-02_v1.mp4" -f null - && echo "decodifica completo"

# 7) entrega (nunca sobrescribir): exportación local y copia de revisión en /mnt/project-files (el montaje agrega una caja C2PA:
#    se compara por md5 de paquetes, no por sha256 del archivo)
[ -e "$OUT" ] && echo "AVISO: $OUT ya existe; no se sobrescribe" || cp "$T/REAL-02_v1.mp4" "$OUT"
[ -e "$PF/REAL-02_v1.mp4" ] && echo "AVISO: $PF/REAL-02_v1.mp4 ya existe; no se sobrescribe" || cp "$T/REAL-02_v1.mp4" "$PF/REAL-02_v1.mp4"
for f in "$OUT" "$PF/REAL-02_v1.mp4"; do
  echo "$f"; ffmpeg -v error -i "$f" -map 0:v -c copy -f md5 -; ffmpeg -v error -i "$f" -map 0:a -c copy -f md5 -
done

# 8) evidencia sobre la copia entregada (cuadros, máscaras, espuma, P4 1:1, audio, contenedor) + vista de la propuesta del «3»
E="$PF/evidencia_v1"
nice "$PY" $R/evidencia.py "$PF/REAL-02_v1.mp4" "$T" "$E"
nice "$PY" $R/propuesta_t4.py "$T/base.rgb" "$T/salida.rgb" "$E/mascaras/propuesta_T4_roca_f063_f070.jpg"
cp "$T/margenes_v01.tsv" "$T/base_info.json" "$T/aud/mezcla_eventos.json" "$E/"
