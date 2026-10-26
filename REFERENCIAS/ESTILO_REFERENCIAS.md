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
| Macro del frente blanco "so f★cking close." | R1, R4 | `ORIGINALES/IMG_3375.mov` (HDR) y `PRODUCTO/blanca_frente_detalle_estampado.jpg`; negra: `IMG_3453.mov` |
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

---

# Segunda tanda de piezas publicadas (R5–R10, recibidas el 26/10/2026)
Gianluca: "videos que subimos". **Mejor resultado: R7 (la lata), ~2.000 vistas en TikTok e Instagram** (dato informado por Gianluca; no tengo acceso a las métricas ni a las vistas de las otras piezas). Es un solo dato: sirve como pista, no como regla.

| Ref | Archivo (nombre original) | Dur. | Formato | Sonoridad | Fórmula |
|---|---|---|---|---|---|
| R5 | `REF_05_5a53c8e6.mov` (`5a53c8e6ebc34016b0687d576457c209.mov`, 24/10) | 17,8 s | 1080×1920, ~30 fps | −13,8 LUFS | Globo 3D celeste con el estampado del pecho y una aguja que baja; contador "FRAMES TO IMPACT" 195 → 001; corte justo antes del pinchazo → montaje de producto → placa azul marino |
| R6 | `REF_06_176cdbef.mov` (23/10) | 8,0 s | **540×960** | −19,1 LUFS | Cenital: chico acostado en una alfombra; un brazo mecánico pasa y cambia el outfit (negra/blanca); "1/11" fijo arriba |
| **R7** | `REF_07_c9e02636.mov` (23/10) | 9,5 s | **720×1280** | −17,8 LUFS | **La lata (mejor resultado).** Fondo crema; lata 3D con el estampado del pecho; una bala se acerca y un contador baja 162 → 001 (cambia de negro a rojo cerca del final); la bala se frena a milímetros sin tocarla; cierre "ROCCÉ / Founders Privée / 1/11" en serif |
| R8 | `REF_08_13d13282.mov` (23/10) | 23,7 s | **540×960** | −13,9 LUFS | Voz en off + textos grandes sobre montaje de producto ("TE DICEN CASI…"); cierre blanco con CTA "ESCRIBINOS FOUNDERS" |
| R9 | `REF_09_1-11_sin_logo_final.mov` (`ROCCE_1-11_Sin_Logo_Final.mov`, 26/10, FFmpeg) | 12,2 s | **720×1280** | −13,7 LUFS | Blanco y negro: abre con clip ajeno de una serie (personaje fumando, diálogo en inglés) → tomas de las remeras en las rocas con "so f★cking close." encima (serif, estrella azul) → "1/11 DISPONIBLE" |
| R10 | `REF_10_color_identidad.mov` (`ROCCE_COLOR_IDENTIDAD.mov`, 26/10, FFmpeg) | 7,1 s | 1080×1920, 30 fps | −20,6 LUFS | Dos interruptores tipo iPhone, "COLOR" e "IDENTIDAD": arranca en blanco y negro con las remeras lisas; al activar COLOR entra el color; al activar IDENTIDAD aparecen los estampados. Material: `IMG_7884/7887` |

## R7 — la lata (detalle)
- 0,0–8,0 s: plano fijo, fondo crema limpio, la lata se acerca/agranda, la bala avanza en línea recta desde la izquierda. Contador grande debajo (162 → 001) que se desacelera: los números bajan cada vez más lento → **tensión creciente**. Desde ~022 el número pasa a rojo.
- ~8,0 s: la bala queda a milímetros de la lata; **no hay impacto** = "so f★cking close." hecho imagen. Aparece "ROCCÉ / Founders Privée / 1/11" en serif negra, abajo.
- Audio: música sin voz clara (Whisper no detecta letra confiable); sube de ≈ −21 a −15 dBFS hacia el final y baja en el último segundo.
- Producto: no aparece la remera; aparece el **estampado del pecho** en la lata. Ojo: la lata es un objeto generado; el arte del estampado debe respetarse exacto.

## R8 — voz en off (transcripción corregida con los textos en pantalla; entre corchetes lo dudoso)
"Te dicen casi, como si fuera tu nombre. Casi quedás, casi ganás, casi te sale. Y todo lo que hiciste parece no contar. Pero vos sabés lo que te costó llegar hasta ahí. [Con el lema so f★cking close] llevás la historia puesta, la de quienes estuvieron cerca y siguen. Que un resultado no te ponga nombre: dáselo vos. Founders Privée. Primero de noviembre. Escribí FOUNDERS y sumate a la lista privada."
- Textos en pantalla: condensada bold en mayúsculas, blanco con palabras clave en rojo o amarillo, arriba a la izquierda ("TE DICEN / CASI.", "¿ESO TE DEFINE?", "ESA HISTORIA. / PUESTA.", "TU HISTORIA. / TU NOMBRE.").
- Cierre: fondo blanco, "ROCCÉ so f★cking close." + "FOUNDERS PRIVÉE" + "01.11" en rojo, video en recuadro, "ESCRIBINOS / FOUNDERS / Y SUMATE A LA LISTA PRIVADA."

## Lo que aportan R5–R10 al estilo
1. **Concepto "casi impacto" (R5 globo, R7 lata):** la frase de la colección convertida en imagen — algo que está a punto de pasar y no pasa. Contador descendente como motor de retención (obliga a mirar hasta el final). Es la fórmula del mejor resultado.
2. **Producto como objeto gráfico** (estampado sobre una lata o un globo) además de la prenda real.
3. **Interruptores / interfaz** (R10) y **brazo que cambia el outfit** (R6): transformaciones visuales simples y legibles.
4. **Narrativa "casi"** (R8): la historia de estar cerca, con voz y texto; CTA a escribir "FOUNDERS".
5. Tipografías vistas: serif para "ROCCÉ / Founders Privée" (R7, R9); condensada bold para textos de impacto (R8); números grandes celestes en placas azul marino (R5: "01 / 11").

## Riesgos detectados
- **Calidad:** R6, R8 (540×960) y R7, R9 (720×1280) están por debajo de 1080×1920; R6, R7 y R10 suenan bajo (−17,8 a −20,6 LUFS).
- **Derechos:** R9 abre con una escena de una serie de TV (material de terceros con diálogo).
- **Producto:** R6 muestra otras prendas (shorts y jeans) que no son del drop; en R10 la versión "sin identidad" quita los estampados (es el concepto, pero implica edición de la prenda).
- R9 dice "1/11 DISPONIBLE" y R8 promete una "lista privada": confirmar que eso está vigente antes de repetirlo.


---

# R11 — referencia externa del encargo "hook puente" (no es pieza de Roccé)
`REF_11_toparadi_hook_puente_De9bn1GqBYQ.mp4` (Instagram `De9bn1GqBYQ`, cuenta toparadi, 10,4 s).
- 0–3,667 s: toma en primera persona (gran angular) con piernas que saltan sobre una estructura metálica encima del agua, a pleno sol.
- 3,667 s: **corte seco en pleno salto** a una remera negra en una percha (estudio oscuro); una mano con guante blanco sale de cuadro. El audio cae casi a silencio entre 3,75 y 4,0 s y la música vuelve fuerte a los 4,2 s.
- 4,267–10,4 s: detalles con guante (logo, etiqueta del cuello, textura, gestos), cortes cada 0,5–1,4 s al ritmo (≈ 128 BPM; cortes en 4,267 · 5,433 · 5,9 · 7,3 · 7,8 · 8,3 · 9,2 · 9,9). Sin placa final.
- Material de terceros (imagen y música): riesgo de reclamo de derechos al publicar.


# R12 — referencia externa del encargo "salto" (no es pieza de Roccé)
`REF_12_macrobodega_salto_DdRfmrgDLIk.mp4` (Instagram `DdRfmrgDLIk`, cuenta macrobodega, 54,9 s, 30 fps). Transcripción en `analisis/R12_transcripcion_whisper.txt`.
- 0–39 s: explicación en 3D ("Reemplaza los huesos de tus piernas con un marco de titanio…") con voz masculina continua, música de fondo (~107 BPM, ≈ −30 dBFS bajo la voz) y subtítulos de 1–3 palabras: Montserrat Bold blanca, sombra oscura, sobre franja translúcida desenfocada a ~77 % de la altura.
- 38,9–39,5 s: transición de **explosión de píxeles** con golpe sonoro → 39,5–50 s local y productos de Macrobodega → 50–54,9 s logo y "COTIZA TU PEDIDO".
- Gancho narrativo reutilizable: la explicación termina en "…lanzándote lo suficientemente alto para llegar a [marca]".
