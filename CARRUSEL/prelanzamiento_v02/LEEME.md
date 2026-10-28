# Roccé — carrusel de prelanzamiento v02 (mixto)

Ocho piezas de 1080 × 1350 px (4:5) para un único carrusel de Instagram. Cinco son MP4 con video real de las remeras dentro de recuadros fijos y tres son PNG.

| # | Archivo | Qué se mueve |
|---|---|---|
| 01 | `ROCCE_PRELAUNCH_01_v02.mp4` (8 s) | Ventana: la blanca y después la negra, sostenidas frente a la playa |
| 02 | `ROCCE_PRELAUNCH_02_v02.mp4` (8 s) | Ventana grande: la blanca (espalda, frente, puesta). Ventana chica: la negra (sostenida, puesta) |
| 03 | `ROCCE_PRELAUNCH_03_v02.mp4` (7 s) | Banda: recorrido por el denim y el celeste, la blanca cayendo en la arena, la negra tono sobre tono |
| 04 | `ROCCE_PRELAUNCH_04_v02.png` | Fija: Mar del Plata, mar y médano |
| 05 | `ROCCE_PRELAUNCH_05_v02.mp4` (6,7 s) | Ventana: dedos sobre la frase de la negra; la frase de la blanca |
| 06 | `ROCCE_PRELAUNCH_06_v02.png` | Fija: 001—100 |
| 07 | `ROCCE_PRELAUNCH_07_v02.mp4` (9 s) | Ventana: la blanca puesta frente al mar, con el mar picado, y la negra puesta |
| 08 | `ROCCE_PRELAUNCH_08_v02.png` | Fija: cierre con el logo original y la fecha |

En cada MP4 el fondo, los textos, los marcos y las fotos fijas no se mueven. Dentro de cada ventana corren tramos reales de las tomas, sin cámara lenta, reversa ni zoom agregado; los cambios de toma quedan dentro del recuadro. No llevan audio: se entienden en silencio.

## Cómo está hecho
- **`proyecto.py`:** las fotos fijas (archivo, zona) y los clips de cada ventana (toma, desde, hasta, encuadre).
- **`pagina.html` + `estilos.css`:** el diseño de las ocho láminas. En las ventanas se ve el primer cuadro del clip.
- **`construir.py`:** arma todo.
  1. Recorta las fotos fijas (Display P3 → sRGB).
  2. Saca las capas fijas con Chromium (`capas.js`).
  3. Recorta cada clip a la proporción de su ventana; las tomas HDR pasan a SDR BT.709.
  4. Compone cada MP4 con FFmpeg: base fija, ventanas con video y capa superior. Salida H.264 yuv420p, 30 fps, sin audio.
- **`verificar.py`:** sobre el MP4 final, mide que dentro de las ventanas haya movimiento y que afuera no cambie nada. Arma una hoja con varios instantes y el mapa de movimiento.
- **`revisar_recortes.py`:** muestra el encuadre de cada clip al principio, al medio y al final.
- **`ficha.py` → `FUENTES.md`:** la ficha de fuentes (lámina, archivo, tramo, función).

Para rehacer los MP4 hacen falta las tomas de `ORIGINALES/` y las fotos de `PRODUCTO/` del repo.
Comando: `python3 construir.py SALIDA v03`, después `python3 entregar.py SALIDA v03`.

Fuentes tipográficas: Inter Display (licencia OFL en `fuentes/`). La tipografía de marca no está disponible.

## Descripción del post
Todavía no salió. Ya tiene historia.

El mar, Mar del Plata y una idea propia que fue tomando forma en cada detalle.

Founders Privée 2026.
01.11 — Guardá la fecha.

GIVE HISTORY YOUR NAME.
