# ROCCE_01_HIELO_REVELACION_v01 — la remera negra congelada, el hacha y Gianluca con la remera puesta

Receta: `scripts/hielo_v01.sh` · 9,93 s · 1080×1920 · 30 fps · H.264 High yuv420p BT.709 · AAC 48 kHz estéreo · −14,7 LUFS, pico −2,0 dBTP.

## Referencia (observado, `REFERENCIAS/REF_20_hacha_hielo_grabacion.mp4`, 512×1108, 18,8 s)
- 0–1 s: vista cenital sobre cemento gris; una mano con un hacha negra golpea un bloque de hielo blanco con un jogger adentro (se ve el logo). Etiqueta "Baggy Nike Jogger>" (blanca, negrita itálica, sombra oscura).
- 1,5–5,5 s: soplete, sopladora, levantan el bloque. 6–8 s: el modelo con el jogger puesto ("THIS IS THE RECREATED"). 8,5–9,5 s: promoción "20.9 MILLION". 10–17,5 s: segunda versión con hielo transparente y la etiqueta arriba del bloque; "AND THIS IS THE ORIGINAL". Después, interfaz.
- Se toma: el gancho (prenda reconocible dentro del hielo desde el cuadro 1, golpe inmediato), la etiqueta y su estilo, el ritmo, y el paso a la prenda puesta. Se deja: promociones, interfaz, otros productos y el modelo de la referencia.

## Qué se hizo
- **Escena 3D real** (Blender 5.0 como módulo, Cycles en CPU, `escena.py`): bloque de hielo de 0,80 × 0,76 × 0,19 m con bordes redondeados y escarcha en los bordes, sobre cemento (con la mancha húmeda del deshielo); adentro, la **remera negra real** (textura recortada de `PRODUCTO/negra_espalda_arena_DFDC5DED.png`, sin redibujar: Founders Privée + ROCCÉ tono sobre tono), con relieve leve. Cámara cenital como la referencia.
- **Golpes** (cuadros 6, 26, 45 y 66): hacha negra con filo de acero que entra desde abajo a la derecha (la mano queda fuera de cuadro). Cada golpe: sacudón de cámara, marca blanca de hielo molido con rayos, grietas (planos de fractura que aparecen alrededor del impacto), esquirlas y polvo.
- **Rotura** (cuadro 66): fractura de Voronoi calculada para la escena (36 pedazos, más chicos cerca del último golpe); los pedazos saltan, caen y se deslizan hasta quedar alrededor de la remera, que queda libre e intacta. El hacha sale de cuadro.
- **Revelación** (3,3–4,67 s): la cámara se acerca a la espalda de la remera y entra rápido en "Founders Privée"; **corte directo** a la misma inscripción en la espalda de Gianluca (`IMG_7887`).
- Etiqueta **"Remera roccé>"** (texto exacto, Inter ExtraBold Italic blanca con sombra suave), arriba del bloque, en toda la parte del hielo.
- Sonido sintetizado (`sonido.py`, sin material de terceros) sincronizado con los cuadros de la escena: barrido del hacha, golpe, chasquido, "tin" del filo, crujido de la grieta; estallido, tintineo y arrastre de los pedazos; crujidos sueltos al asentarse; aire del acercamiento y golpe suave en el corte. Después, el sonido real del mar de cada toma.

## Línea de tiempo
| Salida | Archivo | Entrada | Acción | Texto | Sonido |
|---|---|---|---|---|---|
| 0,00–4,67 | escena 3D (`hielo/v01/r67/0000–0139`) | cuadros 0–139 | hacha: 4 golpes (0,20 · 0,87 · 1,50 · 2,20 s), rotura, pedazos alrededor, acercamiento a la espalda | Remera roccé> | efectos sintetizados |
| 4,67–6,13 | `IMG_7887.mov` | 2,20–3,67 s | Gianluca de espaldas: ROCCÉ y Founders Privée en primer plano, ola atrás | — | mar real (entrada 0,12 s) + cola del golpe de corte |
| 6,13–8,53 | `IMG_7885.mov` | 0,00–2,40 s | sentado en las rocas, rompe la ola, la remera se mueve con él | — | mar real |
| 8,53–9,93 | `IMG_7884.mov` | 0,00–1,40 s | agachado sacando la foto de la blanca (la tela al agacharse) | — | mar real (+4 dB), salida 0,3 s |

## Revisión
- Verificado técnicamente: decodifica completo; 298 cuadros; video 9,933 s y audio 9,933 s; 1080×1920, 30 fps, High, yuv420p, BT.709; −14,7 LUFS integrado, pico −2,0 dBTP (limitador a −3 dB de muestra, dos pasadas); sin GPS ni metadatos de las tomas.
- Corregido en la revisión: (1) el primer montaje perdía el último cuadro al unir audio y video (el audio duraba 0,04 ms menos): ahora el audio se ajusta a N × 1600 muestras; (2) el pico real superaba −1 dBTP después del AAC (−0,2): limitador más bajo; (3) las marcas de impacto salían como estrellas blancas de rayos finos: se suavizan en 2D en su posición exacta, calculada desde la escena 3D (`marcas_2d.py` + `suavizar_marcas.py`), y quedan como manchas de escarcha.
- Revisado visualmente (fotogramas): la secuencia completa a 4 cuadros por segundo, el primer cuadro y la rotura a resolución completa, ±0,04 y ±0,10 s alrededor de cada corte.
- Sin reproducción ni escucha: el sonido se revisó por niveles por tramo (3,0–3,9 s queda bajo a propósito, antes del acercamiento).

## Limitaciones conocidas
- Render a 720×1280 escalado a 1080×1920 (Cycles en CPU, ≈ 70 s por cuadro): un poco menos de detalle fino que un render nativo.
- No hay toma de Gianluca con la negra **de frente** ni parado mostrando calce: el final usa las tres tomas de espaldas que existen.
- La mano del hacha no se ve (queda fuera de cuadro): una mano generada no habría sido creíble con las herramientas disponibles.
