# Referencias de estilo — piezas propias de Roccé

Guardadas el 26/10/2026 a pedido de Gianluca: "Estos son videos que hacemos… tené en cuenta este estilo".
Son piezas de la marca: guían estructura, ritmo, texto y audio. Las reglas que se desprenden están resumidas en `CLAUDE.md` → "Estilo de la casa". Material de análisis (fotogramas, transcripciones) en `REFERENCIAS/analisis/`.

**Qué se verificó:** formato con ffprobe; fotogramas a 2 cuadros/s y cuadro a cuadro en cada giro; cortes por detección de escena; nivel por tramo de 0,5 s y sonoridad integrada (EBU R128); transcripción con faster-whisper (modelo small) contrastada con los subtítulos quemados; tempo estimado por análisis espectral; colores medidos en píxeles.
**No verificado:** escucha real (no identifiqué ninguna canción ni juzgué la mezcla de oído) y el movimiento continuo entre los fotogramas revisados. Los tempos son estimaciones automáticas.

## Archivos
| Ref | Archivo | Nombre original (fecha) | Duración | Formato | Sonoridad |
|---|---|---|---|---|---|
| R1 | `REF_01_hyperspeed_cameraman.mov` | `9d889018-66641d7896ae40e69110dd7b66da7b1c.mov` (25/10/2026) | 10,0 s | 1080×1920, 30 fps, H.264, AAC 44,1 kHz estéreo | −14,9 LUFS |
| R2 | `REF_02_plata_facil.mov` | `Rocce_Plata_Facil_Founders_1-11.mov` (26/10/2026, exportado con FFmpeg) | 9,1 s | 1080×1920, 30 fps, H.264, AAC 44,1 kHz estéreo | −14,7 LUFS |
| R3 | `REF_03_escalera_animacion.mov` | `Rocce_Escalera_Audio.mov` (26/10/2026, exportado con FFmpeg) | 17,4 s | 1080×1920, 30 fps, H.264, AAC 48 kHz estéreo | −16,1 LUFS |
| R4 | `REF_04_bala_tubo_curvo.mov` | `717eaa6d746b4fa49bbaceb41b8f77a6.mov` (25/10/2026) | 27,5 s | 1080×1920, 30 fps, H.264, AAC 48 kHz estéreo | −13,5 LUFS |

---

## R1 — "Hyperspeed Cameraman": gancho prestado + montaje a ritmo
| Tiempo (s) | Imagen | Texto | Audio |
|---|---|---|---|
| 0,00–1,67 | Camarógrafo de F1 en el corral de prensa (clip ajeno, marca de agua F1) | "Hyperspeed Cameraman", blanco con contorno, arriba (~16 % de la altura) | bajo (≈ −30/−24 dBFS) |
| 1,67–3,03 | Su punto de vista: el auto se acerca y pasa en barrido | sigue el texto | bajo |
| **3,03** | **Giro:** corte en el desenfoque del barrido → blanca de espaldas sobre rocas con espuma (`clip_a592f367`) | — | sube a ≈ −12/−13 dBFS (entra la música) |
| 4,17 | Negra sobre rocas con olas, cenital | — | |
| 4,77 | Chico de espaldas caminando con la blanca, jardín | — | |
| 5,53 | Macro del frente blanco "ROCCÉ so f★cking close." | — | |
| 5,97 | Mano que sostiene la negra de frente | — | |
| 6,47 | Espalda blanca en diagonal sobre arena húmeda (`IMG_8008`) | — | |
| 6,90 | Chico de espaldas con la negra, balcón (`IMG_7793`) | — | |
| 7,63–10,00 | Placa: ambas remeras sobre rocas frente al mar, leve acercamiento | "DROP" (chico, espaciado) / "FOUNDERS PRIVÉE" / "1/11" (grande); blanco, centrado, tercio superior | silencio en los últimos 0,5 s |

- Montaje: 7 planos en 4,6 s (0,43–1,14 s cada uno). Tempo estimado ≈ 131 BPM; los cortes mantienen un desfase casi constante con el golpe → cortados a ritmo (estimación automática).
- Voz: no hay. Sin el filtro de voz, Whisper solo devuelve una alucinación típica sobre música ("Thanks for watching guys!", confianza muy baja).

## R2 — "Como hacer plata fácil": gancho de humor + bajada a silencio + montaje
| Tiempo (s) | Imagen | Texto | Audio |
|---|---|---|---|
| 0,00–4,90 | Clip ajeno de recital: fans en la valla, alguien junta celulares; desde 4,17 s, punto de vista de un celular grabando | Barra estilo Snapchat "Como hacer plata fácil 🤫😅" (blanco sobre negro translúcido, a lo ancho, ~68 % de la altura) | multitud fuerte (≈ −13 dBFS) que baja desde 3,0 s hasta casi silencio (−44 dBFS a los 5,0 s) |
| **4,93** | **Giro:** corte seco a la negra sostenida de frente (jardín) | — | casi silencio |
| 5,83 | Espalda blanca en diagonal (`IMG_8008`) | — | |
| 6,63 | Chico con la negra, balcón (`IMG_7793`) | — | entra música a los 6,5 s (≈ −18 dBFS) |
| 7,33 | Chico caminando con la blanca, jardín | — | |
| 7,93–9,13 | Placa: ambas remeras en rocas | "DROP FOUNDERS PRIVÉE" (una línea) + "1/11" grande | |

- Voz: nada claro. Sin filtro, Whisper devuelve "I don't know what happened to me!" sobre los gritos del gancho con confianza baja: puede ser un grito del público o una alucinación. No verificado.
- Rango dinámico alto (LRA 14,2 LU): el contraste ruido → silencio → música es parte del efecto.

## R3 — "Escalera": animación propia de marca
Motion graphics 2D: siluetas negras sobre fondo azul pizarra con brillo celeste.
| Tiempo (s) | Imagen |
|---|---|
| 0,0–0,9 | Multitud de siluetas "dormidas" (ojos cerrados); el protagonista, con los ojos abiertos, lleva la remera blanca con el estampado del pecho |
| 0,9–3,0 | Plano general de la escalera con rótulos EMPEZÁ → APRENDÉ → so f★cking close. → CONSTRUÍ → TU META (bandera roja); el protagonista sube |
| 3,0–6,3 | Acercamiento: se sienta agotado justo en el escalón "so f★cking close." |
| 6,3–8,0 | Vuelve la multitud |
| 8,0–11,3 | Se levanta y sigue: CONSTRUÍ → TU META; llega a la bandera |
| 11,3–15,0 | La multitud abajo; desde arriba cae un chorro amarillo sobre ella (remate de humor) |
| 15,0–17,4 | Placa de marca |

- Rótulos de la escalera: monoespaciada en mayúscula chica con una raya de marca. La frase de la colección va en serif con la estrella en azul, igual que en la prenda.
- Placa (medida en píxeles): fondo azul marino degradado `#0f1929` → `#0a1522`; logo en **versión blanca**; "ROCCÉ" en serif grande, blanco roto `#efefe9`; "BANCAMOS A LOS QUE SIGUEN." en mayúsculas chicas espaciadas, celeste `#a2bfda`; línea divisoria celeste `#b3cae1`; "DROP" mini espaciado; "Founders Privée" en serif; "01/11/2026"; "SEGUINOS" mini en celeste. Todo centrado.
- Audio: música continua, sin voz detectable; nivel parejo (LRA 1,9 LU) con bajadas cada ~4 s; fundido final de 15,0 a 17,4 s. Tempo estimado ≈ 80 BPM (poco confiable).

## R4 — "Bala por un tubo curvo": gancho de curiosidad + voz en off de venta
Transcripción (faster-whisper small, corregida con los subtítulos quemados; entre corchetes, lo que Whisper entendió mal):
- 0,08–7,14 — "Si disparas una bala por un tubo curvo que apunta hacia ti, casi todo el mundo cree que te acabaría dando a ti, pero no."
- 7,50–11,12 — "Lo que sucede es que la bala durante el recorrido sale y se va directa…"
- 11,62–15,54 — "…al 1 de noviembre, que sale el drop Founders Privée [«foundo es privé»]. ¿Querés verte mejor que los demás?"
- 15,78–20,62 — "Nuestra remera [«primera»] tiene un corte en V [«en B»] que te hace más estético, agrandándote la espalda y reduciéndote la cintura."
- 20,82–24,70 — "Ni hablar de que pesa 305 gramos y tiene bordados en tela de jean [«tela de chin»]."
- 24,98–27,16 — "No dudes más, que tenemos envío gratis y entrá ya."

| Tiempo (s) | Imagen | Subtítulo |
|---|---|---|
| 0,00–11,00 | Clip ajeno 3D (pistola, tubo curvo, cuadrícula azul); 0–0,46 s en silencio | subtítulos bold blancos con sombra, del clip |
| **11,00** | **Giro** en el remate "y se va directa…": ambas remeras en rocas | "y se va directa…" → "1/11" grande (11,4 s) |
| 12,77 | Blanca sobre rocas con espuma | "que sale el drop" / "Founders Privée" |
| 14,33 | Mano que sostiene la negra | "¿Querés verte mejor" / "que los demás?" |
| 15,73 | Macro del frente blanco | "Nuestra remera tiene" |
| 16,40 | Chico con la negra, balcón | "CORTE EN V" / "que te hace más estético" / "agrandándote la espalda" |
| 19,27 | Chico caminando con la blanca | "y reduciéndote la cintura" |
| 20,73 | Blanca de frente sobre rocas con espuma | "Ni hablar de que pesa" |
| 21,80 | Macro del frente | "305 gramos" |
| 23,10 | Espalda blanca en diagonal | "y tiene bordados" / "TELA DE JEAN" |
| 24,83–27,47 | Placa "DROP FOUNDERS PRIVÉE / 1/11" | "No dudes más" / "ENVÍO GRATIS" / "ENTRA YA" |

- Cortes: cada uno cae al empezar una frase de la voz (10–150 ms antes de la primera palabra), no sobre el golpe musical. Cada dato tiene el plano que lo muestra: "305" sobre el macro, "corte en V" sobre la remera puesta, "tela de jean" sobre el parche de denim.
- Subtítulos: 1–4 palabras por vez, blanco con sombra, centrados a ~76–78 % de la altura; las palabras de venta van en MAYÚSCULAS y más grandes.
- La voz pasa de tuteo en el gancho ("hacia ti") a voseo en la venta ("Querés", "entrá"). No pude verificar si es la misma voz ni si es humana o sintética.
- **Datos comerciales dichos** (corte en V, 305 g, bordados en tela de jean, envío gratis): **no reutilizar sin confirmar que siguen vigentes** (regla de producto de `CLAUDE.md`).

---

## Patrones comunes
1. **Gancho → giro → producto → placa** (R1, R2, R4). El gancho es un clip de alto impacto ajeno a la moda (F1, recital, explicación 3D) con texto nativo de plataforma. Acción desde el primer cuadro, sin logo ni introducción.
2. **El giro es un corte seco** en el pico de movimiento (R1), en un momento de expectativa (R2) o en el remate de la frase (R4). El texto o la voz del gancho pueden cruzar el corte para unir las dos partes.
3. **Montaje de producto corto:** 0,4–1,5 s por plano con música; hasta ~3 s con voz. Alterna blanca y negra, detalle (macro del estampado, denim) y contexto (persona de espaldas, rocas y mar, jardín).
4. **Cambio de energía de audio en el giro:** la música entra o sube (R1), o el gancho se apaga hasta casi silencio antes del producto (R2).
5. **Placa de drop:** foto de las dos remeras en rocas frente al mar; texto blanco, sans grotesca bold, centrado en el tercio superior sobre el mar oscuro, sin tapar la prenda; "1/11" es el elemento más grande (≈ 145 px de altura de mayúscula en 1080×1920). Dura 1,2–2,6 s.
6. **Cierre de marca (R3):** azul marino, logo blanco, serif y mayúsculas chicas espaciadas en celeste.
7. **Sonoridad alta y pareja:** −13,5 a −16,1 LUFS integrados.

## Planos recurrentes y originales disponibles
| Plano | Usado en | Original en el repo |
|---|---|---|
| Ambas remeras sobre rocas frente al mar (placa) | R1, R2, R4 | `ORIGINALES/IMG_7894.mov` (fuente confirmada); variantes `IMG_7895`, `IMG_7896`, `IMG_4631` |
| Blanca de espaldas sobre rocas con espuma | R1, R4 | `ORIGINALES/clip_a592f367.mov` (baja resolución) |
| Blanca de frente sobre rocas con espuma | R4 | **falta** |
| Negra sobre rocas con olas, cenital | R1 | **falta** |
| Chico caminando de espaldas con la blanca, jardín | R1, R2, R4 | **falta** |
| Macro del frente blanco "so f★cking close." | R1, R4 | **falta** |
| Mano que sostiene la negra de frente | R1, R2, R4 | **falta** |
| Espalda blanca en diagonal, arena húmeda | R1, R2, R4 | `ORIGINALES/IMG_8008.mov` |
| Chico de espaldas con la negra, balcón | R1, R2, R4 | `ORIGINALES/IMG_7793.mov` |
| Chico de espaldas con la blanca frente al mar | — | `ORIGINALES/IMG_7859.mov` (sin usar en las referencias) |
| Paneo playa → ambas en arena | — | `ORIGINALES/clip_f2a34e51.mov` (sin usar) |

Material real de final y cierre recibido después (26/10/2026), que no aparece en R1–R4:
- blanca colgada en la baranda de troncos (`IMG_8002`, `IMG_8004`);
- blanca tirada a la arena, de espaldas y de frente (`IMG_7996`, `IMG_7999`);
- detrás de escena de la foto de producto (`IMG_4675`, HDR);
- foto `PRODUCTO/blanca_negra_espalda_playa_2.jpg`.

Detalle y tramos útiles en `CAMPANA_ACTUAL.md`.

## Diferencias con mi reel de prueba v02
- No tiene gancho: abre con un plano tranquilo y audio bajo (≈ −29 dBFS). Las referencias abren con acción y texto.
- Suena más bajo: −19,2 LUFS contra −13,5 a −16,1.
- El cierre (placa blanca, logo negro, texto chico gris) no es el de la casa: foto de las remeras con texto blanco bold, o placa de marca azul marino.
- Termina con 1,9 s de silencio; R1 tiene 0,5 s.
