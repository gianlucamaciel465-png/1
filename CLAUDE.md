# Roccé — reglas de edición de video

## Rol
Editor de videos de Roccé. Entregables: archivos MP4 terminados, con estética guiada por las referencias del usuario.

## Carpetas
- `ORIGINALES/` — tomas de video originales. **Nunca se modifican.**
- `REFERENCIAS/` — videos/imágenes de referencia estética.
- `PRODUCTO/` — fotos de producto (fuente de verdad de la prenda).
- `LOGO/` — logo oficial (fuente de verdad de la marca).
- `AUDIO/` — pistas de audio indicadas por el usuario.
- `TRABAJO/` — copias e intermedios (no se versiona en git).
- `EXPORTACIONES/` — resultados finales con versión numerada.

## Reglas de fuente de verdad
- Usar las fotos de producto y el logo del usuario tal cual. Conservar los detalles de la remera (estampado, color, costuras, etiquetas).
- **No redibujar el logo, no inventar estampados**, no generar ni alterar la prenda con IA. Solo se permite escalar/posicionar el logo sin deformarlo.
- Corrección de color permitida solo si no cambia el color real de la prenda (comparar contra `PRODUCTO/`).

## Flujo obligatorio
1. Revisar carpetas y comprobar `ffmpeg` / `ffprobe`. Si falta una herramienta, explicar cómo instalarla.
2. Analizar originales y referencias **antes** de editar: `ffprobe` (duración, fps, resolución, rotación, audio) y fotogramas extraídos con su marca de tiempo (`scripts/fotogramas.sh`).
3. Si el diálogo importa: transcripción con marcas de tiempo e informe de qué se pudo verificar del audio.
4. Trabajar siempre sobre copias en `TRABAJO/`.
5. Exportar a `EXPORTACIONES/` con nombre `NOMBRE_vNN.mp4` (v01, v02…); nunca sobrescribir una versión anterior.
6. Si una transformación requiere una herramienta que no está disponible, identificar la limitación **antes** de intentar resolverla.

## Especificación de exportación (reels)
- MP4, video H.264 (`libx264`, `yuv420p`, `+faststart`), audio AAC (48 kHz, estéreo).
- 1080 × 1920 vertical.
- Frecuencia de cuadros adecuada al material: mantener la de los originales (p. ej. 23.976/25/29.97/30). Si las tomas difieren, usar la más común sin inventar cuadros; no subir fps artificialmente.

## Verificación después de exportar
- Decodificar el archivo completo sin errores (`ffmpeg -v error -i X -f null -`).
- Comprobar con `ffprobe`: códecs, resolución, fps, duración de video y audio.
- Extraer y revisar fotogramas, especialmente alrededor de cada corte, y el texto final.
- Verificar textos exactos, encuadre (que la prenda no quede cortada) y duración.
- Informar cualquier parte del audio o del movimiento que no se haya podido comprobar (solo se ven fotogramas sueltos; el audio se mide con niveles/transcripción, no se "escucha").

## Primera prueba (pendiente de material)
Reel vertical 10–15 s, dos tomas reales de la prenda, audio indicado por el usuario. Cierre con el texto exacto:
`1/11 — DROP FOUNDERS PRIVÉE` (raya —, É con tilde).
