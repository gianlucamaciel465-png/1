# Roccé — carrusel de prelanzamiento (v01, 28/10/2026)

8 placas de 1080 × 1350 px (4:5) para Instagram, antes del Drop Founders Privée del 01/11/2026.
Concepto: **TODAVÍA NO SALIÓ. YA TIENE HISTORIA.**
Recorrido: curiosidad → producto → detalles → origen → la frase → Founders → participación → fecha.

## Cómo editar y exportar
- **Textos y orden:** `index.html` (una `<section class="placa">` por imagen).
- **Diseño:** `estilos.css` (colores, tamaños, posiciones; márgenes de 72 px).
- **Fotos:** `recortes.py` recorta las fotos originales de `PRODUCTO/` (y un fotograma de `ORIGINALES/IMG_7824.mov`), las pasa de Display P3 a sRGB y las deja en `recursos/`. Cada recorte anota de qué archivo y qué zona sale (`recursos/recortes.json`).
- **Exportar:**
  1. `node render.js SALIDA v02` (Chromium/Playwright);
  2. `python3 finalizar.py SALIDA v02` (perfil sRGB, controles, vista conjunta y ZIP).
- **Ver en una computadora:** abrir `index.html` en Chrome. Las fuentes están en `fuentes/` (Inter Display, licencia OFL: `fuentes/LICENCIA_Inter.txt`).

## Material usado (todo existente)
| Placa | Recurso | Uso |
|---|---|---|
| 01 | `blanca_negra_espalda_playa_2.jpg` | Franja de las dos espaldas: pista visual bajo el titular |
| 02 | la misma foto, completa | Las dos remeras (blanca adelante, negra atrás) |
| 03 | `blanca_espalda_rocas_espuma.jpg` | ROCCÉ en denim con pespunte, Founders Privée celeste y la É de cerca |
| 04 | — | Pausa tipográfica |
| 05 | `blanca_frente_detalle_estampado.jpg` | so f★cking close. tal como está estampada en el pecho |
| 06 | fotograma de `IMG_7824.mov` (6,8 s) | La negra sostenida: ROCCÉ en denim negro y Founders Privée gris |
| 07 | `blanca_puesta_espalda_balcon_playa.jpg` | La blanca puesta, de espaldas (sin cara) |
| 08 | `LOGO/rocce_logo.png` | Logo original sin cambios, sobre su mismo fondo (#FEFEFE) |

Solo se recortó y se escaló conservando la proporción. No hay retoques, espejados ni imágenes generadas.

## Tipografía
La tipografía de marca no está disponible: se usa **Inter Display** (Medium, SemiBold y Bold). ROCCÉ como texto aparece solo dentro de frases; el logo es el archivo original.

## Descripción del post
Todavía no salió. Ya tiene historia.

El denim, el celeste y una idea que fue tomando forma hasta convertirse en Roccé.

Founders Privée 2026.
01.11 — Guardá la fecha.

GIVE HISTORY YOUR NAME.
