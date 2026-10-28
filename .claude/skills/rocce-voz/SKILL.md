---
name: rocce-voz
description: Voz de Roccé para reels y locuciones. Usar cuando un encargo pida voz en off, locución, narración o voz de marca de Roccé, o mencione Firme 04, "Royé", el banco vocal o la voz de Gianluca. Indica qué voz usar primero, dónde está el banco privado, cómo recuperarlo y la receta para generar y mezclar la voz.
---

# Voz de Roccé

1. **Qué voz:** primero la voz de marca aprobada **"Roccé — Firme 04"**; como alternativa, la **voz real de Gianluca**. La voz guía de `lo_que_te_frena_v02` no es referencia.
2. **Dónde están las grabaciones:** página privada https://claude.ai/artifact/AQSWzDitj143yjJdqkoXQk (no en el repo: el repo es público). Registro, hashes y recuperación: `scripts/voz/BANCO_VOCAL.md`.
3. **Recuperar:** instalar entornos (`scripts/instalar_entorno.sh "$S" voz whisper`), bajar con la herramienta Artifact (`read` + `paths`) y comparar sha256 con `REGISTRO_BANCO_VOCAL.json`. Si no se puede leer, pedirle los archivos a Gianluca.
4. **Generar con Firme 04:**
   - escribir el guion como TSV (`id<TAB>texto`), con "Royé" por Roccé y "fáunders" por founders (en pantalla: Roccé / FOUNDERS);
   - **probar primero una frase corta con Royé**;
   - `VOZ_PY=$S/voz-env/bin/python python3 scripts/proxima/locucion.py GUION.tsv SALIDA` (edge-tts es-AR-ElenaNeural +11 % / −20 Hz + `tratamiento_firme.py`);
   - `$S/whisper-env/bin/python -I scripts/proxima/palabras.py SALIDA`;
   - medir con `scripts/voz/comparar_voz.py`.
5. **No afirmar** que se escuchó, se clonó o que la reconstrucción es idéntica: decir que se midió (tono, formantes, espectro, transcripción) y que falta la escucha.
6. **Mezcla:**
   - la música, el ambiente y los efectos bajan con la voz (`sidechaincompress`); la voz queda 10–15 dB arriba del fondo, medido frase por frase;
   - poner `apad=whole_dur=DURACIÓN` en la señal que maneja el sidechain, porque el compresor termina cuando termina la voz;
   - entrega a ≈ −14 LUFS, con picos por debajo de −1 dBTP.
7. **Nunca** subir grabaciones de voz al repo mientras sea público, ni compartir la página del banco con enlace público.
