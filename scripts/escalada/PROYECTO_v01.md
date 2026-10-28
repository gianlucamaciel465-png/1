# ROCCE_02_HACETE_FOUNDER_v01 — escalada (Neuron Visuals) intervenida + placa Founders

Receta: `scripts/escalada_v01.sh` · 20,0 s · 1080×1920 · 30 fps · H.264 High yuv420p BT.709 · AAC 48 kHz estéreo · −14,0 LUFS, pico −1,5 dBTP.

## Referencia (observado)
Grabación de pantalla de un reel de **Neuron Visuals** (`REFERENCIAS/REF_21_…`, solo local): 1170×2532, HEVC con cuadros variables (máx. 60), 17,06 s. El reel ocupa 1170×2080 desde y=203; arriba la cabecera "Reels · Amigos" se apaga en 0,17 s pero deja un fantasma tenue (≈ 4/255) todo el video; debajo, la barra de comentarios. Desde 15,9 s el reel vuelve a empezar y aparece la interfaz: no se usa.
Planos (cortes medidos por diferencia entre cuadros, a 30 fps):

| Plano | Cuadros | Tiempo | Qué pasa |
|---|---|---|---|
| A | 1–72 | 0,00–2,40 | general: el grupo en el acantilado, el escalador en la torre con WORK · DREAM · START A BUSINESS · BUILD AN EMPIRE · SUCCESS, bandera roja arriba |
| B | 73–123 | 2,40–4,10 | el grupo mira (de cerca) |
| C | 124–186 | 4,10–6,20 | el escalador de cerca, mano sobre mano |
| D | 187–222 | 6,20–7,40 | general: ya cerca de la cima |
| E | 223–302 | 7,40–10,07 | llega a SUCCESS, pasa por encima del borde, se agacha y se para junto a la bandera |
| F | 303–372 | 10,07–12,40 | general: él arriba, el grupo abajo |
| G | 373–477 | 12,40–15,90 | el grupo; cae la chispa sobre el primero ("la idea") y se agarra la cabeza; fundido a negro (15,3–15,77 s) |

Música: la de la grabación (≈ 80 BPM, primer golpe 0,48 s), cae con el fundido a −28/−33 dB. En la interfaz figura "The Weeknd · Timeless": **música comercial de terceros**.

## Qué se conservó y qué se cambió
- Conservado: toda la animación 0–15,77 s (historia completa, cámara, cortes, la reacción del grupo y la "idea"), su música y la marca de agua de Neuron Visuals (en su lugar fijo de pantalla).
- Rótulos de la pared traducidos en el mismo orden y lugar, con la misma letra (Saira, ya usada para Neuron Visuals), mismo alto y color (209,205,209), detrás del escalador cuando pasa por delante: **TRABAJO · SUEÑO · INICIAR / UN NEGOCIO · CONSTRUIR / UN IMPERIO · ÉXITO**. ÉXITO baja unos píxeles para que entre la tilde bajo el borde de la torre y su rayita guía baja con él. Los ingleses se borran con su leve resplandor (no quedan letras fantasma; revisado con la imagen aclarada ×1,8–2,2).
- Seguimiento: cada renglón por correlación normalizada con escala; por cuadro, semejanza (escala + traslación) con los renglones firmes (los 7 encontrados en todos los cuadros con torre).
- Bandera: la roja se borra (con su resplandor) y se dibuja una **celeste** rectangular que flamea, atada a la punta del mástil (mismo punto de la torre), con **GIVE / HISTORY / YOUR NAME.** en azul oscuro (Inter Display Bold). Ancho = largo del mástil (alto 0,62 del ancho) en todos los planos.
- Plano C reencuadrado 150 px (la pared se extiende a la derecha) para que la bandera entre con el mismo tamaño relativo que en los otros planos; el escalador queda más centrado. La marca de agua se quita antes y se vuelve a poner en su lugar fijo.
- Escalador vestido con la **remera negra** (`vestir.py`): cuerpo negro con contorno gris claro y brillo de borde para separarlo del fondo, cuello acanalado, mangas que salen de los brazos reales de la figura (recorrido a lo largo del brazo, ruedo recto), manga lejana detrás. Estampado real recortado de las fotos (sin redibujar): espalda (ROCCÉ tono sobre tono + Founders Privée) mientras trepa; pecho (ROCCÉ / so f★cking close.) cuando queda de frente arriba (transición 9,4–9,7 s). Cabeza y antebrazo cercano quedan delante. Desenfoque de movimiento según la velocidad del torso.
- Placa final (15,77–20,0 s, 4,23 s): **SI TAMBIÉN / PASASTE POR ESO, / HACETE FOUNDER** (blanco; el último renglón en celeste) · **Lista privada de Roccé para vos / y creás prendas con nosotros.** (celeste) · logo original sobre su fondo #FEFEFE en una ficha de esquinas redondeadas (las esquinas solo recortan fondo: el dibujo empieza a 182 px del borde). Entrada escalonada 0,1–1,35 s y después quieta.
- Audio bajo la placa: la misma canción desde 0,81 s del reel (como cuando el reel se repite), elegido para que los golpes sigan la grilla de 80 BPM; entrada 0,25 s, salida 0,9 s.

## Línea de tiempo
| Salida | Archivo | Entrada | Acción | Texto | Sonido |
|---|---|---|---|---|---|
| 0,00–15,77 | REF_21 (recorte del reel) | 0,00–15,77 | animación completa intervenida | rótulos en español; bandera GIVE HISTORY YOUR NAME. | música original |
| 15,77–20,00 | placa (`placa.py`) | — | entrada del título, subtítulo y logo | título + subtítulo exactos | misma canción desde 0,81 s, con salida |

## Revisión
- Verificado técnicamente: decodifica completo; 600 cuadros; video y audio 20,000 s; 1080×1920, 30 fps, High, yuv420p, BT.709; −14,0 LUFS integrado, pico −1,5 dBTP; sin GPS.
- Revisado visualmente (fotogramas): cada plano con torre a 4 fps, alrededor de cada corte (±0,04 y ±0,10 s), rótulos aclarados para buscar restos, la remera en 60 cuadros de todos los planos y la placa.
- Limitaciones: sin reproducción ni escucha; en el paso por encima del borde (8,9–9,5 s) la remera tapa parte del antebrazo doblado; la bandera en los planos generales queda con letra chica (≈ 20 px de mayúscula) — se lee grande en los planos C y E (4,1–6,2 s y 7,4–10,1 s).
- Derechos: animación y música son de terceros (Neuron Visuals; "Timeless"). Publicarla puede generar reclamo o audio silenciado.
