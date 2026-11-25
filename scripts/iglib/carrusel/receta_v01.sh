#!/usr/bin/env bash
# IGLIB-3 «Ambos permanecen» v01 · receta completa (≈ 4 min en CPU).
# Necesita: ORIGINALES/IMG_7857, IMG_7793, IMG_4530, IMG_7824, IMG_4631 (.mov); PRODUCTO/ (fotos del proyecto.py);
# LOGO/rocce_logo.png; Chromium + Playwright en /opt/node-tools; Python 3 con numpy y Pillow; FFmpeg 6.
# Salida: /mnt/project-files/piezas/IGLIB_funcion_libertadores/IGLIB-3_v01/ (láminas, vista conjunta, ZIP)
#         …/evidencia_carrusel_v01/ (cuadros y vistas a 360 px) · intermedios en TRABAJO/iglib/carrusel/
set -euo pipefail
cd "$(dirname "$0")"
python3 construir.py          # recursos → capas (Chromium) → ventanas → MP4/PNG
python3 verificar.py          # ffprobe, decodificación, md5/sha256, movimiento dentro/fuera, blanco neutro, evidencia, vista, ZIP
