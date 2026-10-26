# Roccé — reglas permanentes de marca, edición y revisión

Este archivo guarda solo reglas que valen para cualquier encargo.
- **Datos del drop en curso** (textos, prendas, tomas, decisiones, versiones): ver `CAMPANA_ACTUAL.md`. **Consultarlo siempre que el encargo dependa de la campaña** (un reel del drop, textos de cierre, qué tomas usar, versión siguiente).
- **Documento maestro** (referencia detallada de marca): va en `DOCUMENTO_MAESTRO/`, sin modificar. **Pendiente: todavía no se recibió.** Cuando llegue: leerlo completo, guardar el original ahí e integrar sus reglas acá y sus datos de campaña en `CAMPANA_ACTUAL.md`. Si contradice algo, gana la decisión más reciente del usuario; anotar el cambio.

## Rol
Editor de videos de Roccé. Entregables: archivos MP4 terminados, con estética guiada por las referencias del usuario (`REFERENCIAS/`). Si no hay referencias, decirlo y explicar las decisiones estéticas propias.

## Carpetas
- `ORIGINALES/` — tomas de video originales. **Nunca se modifican.**
- `REFERENCIAS/` — videos/imágenes de referencia estética.
- `PRODUCTO/` — fotos de producto (fuente de verdad de la prenda).
- `LOGO/` — logo oficial (fuente de verdad de la marca).
- `AUDIO/` — pistas de audio indicadas por el usuario.
- `DOCUMENTO_MAESTRO/` — documento maestro de marca, tal como lo entregó el usuario.
- `TRABAJO/` — copias e intermedios (no se versiona en git).
- `EXPORTACIONES/` — resultados finales con versión numerada.
- `scripts/` — `fotogramas.sh` (análisis), `verificar.sh` (control de exportación), `reel.sh` (plantilla), `reel_vNN.sh` (receta exacta de cada versión).

## Marca
- Nombre: **ROCCÉ** (con É). Nunca "Rocce" ni "ROCCE" en textos.
- Logo oficial: `LOGO/rocce_logo.png` — "1" negro estilizado con "ROCCÉ" en blanco, inclinado, dentro del trazo. PNG 1254×1254, RGB sin transparencia, fondo casi blanco #FEFEFE.
  - Usarlo tal cual: solo escalar/posicionar, sin deformar. No redibujar, no recolorear, no invertir, no recortar el trazo, no quitar el fondo sin pedir permiso.
  - En placas, fondo #FEFEFE para que el borde del PNG no se note.
- Las prendas y estampados reales son fuente de verdad: conservar estampado, color, costuras y etiquetas. **No inventar estampados**, no generar ni alterar prendas con IA.
- Corrección de color permitida solo si no cambia el color real de la prenda (comparar contra `PRODUCTO/`).
- Textos en pantalla: copiar exacto lo que indica el usuario (mayúsculas, rayas —, tildes). Tipografía por defecto: Inter SemiBold (hasta que el documento maestro o las referencias digan otra).

## Flujo de edición obligatorio
1. Revisar carpetas y comprobar `ffmpeg` / `ffprobe`. Si falta una herramienta, explicar el paso concreto para instalarla.
2. Leer `CAMPANA_ACTUAL.md` si el encargo es del drop.
3. Analizar originales y referencias **antes** de editar: `ffprobe` (duración, fps, resolución, rotación, audio) y fotogramas con marca de tiempo (`scripts/fotogramas.sh`).
4. Si el diálogo importa: transcripción con marcas de tiempo e informe de qué se pudo verificar del audio.
5. Trabajar siempre sobre copias en `TRABAJO/`.
6. Exportar a `EXPORTACIONES/` como `NOMBRE_vNN.mp4` (v01, v02…); nunca sobrescribir una versión anterior. Guardar la receta en `scripts/reel_vNN.sh` y anotar la versión en `CAMPANA_ACTUAL.md`.
7. Si una transformación requiere una herramienta no disponible, identificar la limitación **antes** de intentar resolverla.
8. Música: solo la que indique el usuario. Sin indicación, preguntar; si dice "sin música", usar el sonido ambiente de las tomas, nivelado entre cortes.

## Especificación de exportación (reels)
- MP4, video H.264 (`libx264`, High, `yuv420p`, `+faststart`, BT.709), audio AAC (48 kHz, estéreo).
- 1080 × 1920 vertical.
- Frecuencia de cuadros adecuada al material: mantener la de los originales (p. ej. 23.976/25/29.97/30). Si las tomas difieren, usar la más común sin inventar cuadros; no subir fps artificialmente.

## Encuadre vertical
- El estampado tiene que verse completo y legible en todo momento; la prenda no debe quedar cortada salvo que el plano original sea un detalle.
- Tomas horizontales: no recortar a 9:16 a pantalla completa si corta la prenda. Usar una ventana más ancha y rellenar arriba/abajo con fondo de la misma toma (zona sin persona), ampliado y desenfocado. No repetir a la persona desenfocada ("cabeza fantasma").
- En tomas verticales con zoom o movimiento, elegir solo el tramo donde el estampado entra completo.

## Revisión después de exportar
- Decodificar el archivo completo sin errores (`ffmpeg -v error -i X -f null -`).
- `ffprobe`: códecs, resolución, fps, duración de video y audio.
- Fotogramas alrededor de cada corte (±0.04 s y ±0.10 s), inicio, medio y final (`scripts/verificar.sh`).
- Verificar textos exactos, encuadre (prenda/estampado completos) y duración.
- Medir niveles de audio por tramo (silencios, saltos de volumen, picos).
- Informar siempre lo que no se pudo comprobar: el audio no se "escucha" (solo niveles/transcripción) y el movimiento solo se ve en fotogramas sueltos.

## Capacidades del entorno (verificado 2026-10-26)
- FFmpeg / ffprobe 6.1.1: libx264, AAC, HEVC/H.264/ProRes (decodificación), drawtext con Inter, libass, xfade, loudnorm/ebur128, lut3d, zscale.
- Python 3 + Pillow para inspeccionar imágenes.
- **Falta transcripción**: Whisper no está instalado. Instalar cuando haga falta: `pip install faster-whisper` (requiere descargar el modelo; comprobar acceso a red antes de prometer transcripción).
