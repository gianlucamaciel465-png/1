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

## Material guardado (fuente de verdad permanente — no borrar ni modificar)

### Prendas
- **Remera blanca**: frente con logo chico "ROCCÉ / so f★cking close." a la altura del pecho izquierdo, en gris. Etiqueta en el cuello "ROCCÉ" con monograma. Espalda: "ROCCÉ" en letras universitarias negras con borde y pespunte gris + "Founders Privée" en cursiva celeste con subrayado de trazo.
- **Remera negra**: frente "ROCCÉ / so f★cking close." en gris claro. Espalda: "ROCCÉ" universitario negro sobre negro (tono sobre tono, apenas visible) + "Founders Privée" en cursiva gris. Cuello alto acanalado.
- Las grafías exactas son "ROCCÉ" (con É) y "Founders Privée". La estrella en "f★cking" es parte del estampado.

### `PRODUCTO/` (fotos)
| Archivo | Contenido |
|---|---|
| `blanca_frente_estudio.jpg` | Blanca, frente, sobre piso blanco (1170×1988) |
| `blanca_espalda_estudio.jpg` | Blanca, espalda, piso blanco (1170×2036) |
| `negra_espalda_estudio.jpg` | Negra, espalda, piso blanco (1170×1613) |
| `negra_frente_playa.jpg` | Negra, frente (detalle logo), en arena (1200×1600) |
| `blanca_negra_espalda_playa.jpg` | Ambas, espalda, en arena (1200×1600) |

### `ORIGINALES/` (videos, todos 30 fps)
| Archivo | Formato | Dur. | Contenido |
|---|---|---|---|
| `IMG_7793.mov` | HEVC 4K, vertical (rotación −90) | 5.3 s | 0–1.2 s paneo desde la playa/ciudad; desde ~1.5 s chico de espaldas con la **negra** en balcón frente a la playa, cielo nublado. Audio mono, bajo (ambiente). |
| `IMG_7859.mov` | HEVC 4K, **horizontal** 16:9 | 8.3 s | Chico de espaldas con la **blanca**, mar picado y rocas. Para 9:16 hay que recortar al centro (la persona está centrada). Audio mono fuerte (olas, pico −0.6 dB). |
| `IMG_8008.mov` | HEVC 4K, vertical | 2.2 s | Primer plano de la espalda de la **blanca** sostenida y apoyada en arena húmeda, sol fuerte. Movimiento rápido. |
| `clip_a592f367.mov` | H.264 1024×576, vertical (576×1024 efectivo) | 4.3 s | **Blanca** apoyada sobre rocas con espuma de mar; acercamiento al estampado. Baja resolución (se ve más blanda al escalar a 1080×1920). |
| `clip_f2a34e51.mov` | H.264 1024×576, vertical | 7.9 s | Paneo playa → arena → **negra y blanca** de espaldas en la arena, termina en la blanca. Baja resolución. |

### `LOGO/`
- `rocce_logo.png` — **logo oficial**: "1" negro estilizado con "ROCCÉ" en blanco, inclinado, dentro del trazo. PNG 1254×1254, RGB sin transparencia, fondo casi blanco #FEFEFE.
- Usarlo tal cual: solo escalar/posicionar. No recolorear, no invertir, no recortar el trazo, no quitar el fondo sin pedir permiso. Para placas, usar fondo #FEFEFE para que el borde del PNG no se note.

### Audio
- **Sin música** (indicación del usuario). Usar solo el sonido ambiente de las tomas (viento/olas), nivelado entre cortes.

## Encuadre vertical
- El estampado tiene que verse completo y legible en todo momento.
- Tomas horizontales (p. ej. `IMG_7859`): no recortar a 9:16 a pantalla completa si corta la prenda. Usar una ventana más ancha y rellenar arriba y abajo con el mar de la misma toma, ampliado y desenfocado (no repetir la persona desenfocada: queda una "cabeza fantasma").
- `IMG_7793`: estampado completo solo entre 2.4 s y 4.8 s; antes y después la cámara se acerca y corta "Privée".

## Historial de exportaciones
- `ROCCE_reel_founders_v01.mp4` — descartada: estampado cortado al final de la toma negra y fondo desenfocado con cabeza duplicada.
- `ROCCE_reel_founders_v02.mp4` — 11.0 s, 30 fps. IMG_7793 2.4–4.8 s → IMG_7859 2.0–8.0 s → placa con logo + texto (2.6 s). Script: `scripts/reel_v02.sh`.

## Primera prueba
Reel vertical 10–15 s, dos tomas reales de la prenda, audio indicado por el usuario. Cierre con el texto exacto:
`1/11 — DROP FOUNDERS PRIVÉE` (raya —, É con tilde).
