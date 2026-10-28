# Banco vocal de Roccé (registro; las grabaciones NO están en este repo)

**El repo `gianlucamaciel465-png/1` es público.** Las grabaciones (voz de marca, voz real de Gianluca y locuciones producidas) viven en una página **privada** de claude.ai que solo abre la cuenta de Gianluca:

**https://claude.ai/artifact/AQSWzDitj143yjJdqkoXQk** — "Banco vocal Roccé" (creada el 28/10/2026)

## Prioridad de uso
1. **Roccé — Firme 04** (voz sintética de marca aprobada): `originales/Rocce_Voz_Firme.mp3`, sha256 `a39ef18a97fc9a79353c342534233ca96c70d902843542b7f41607ca25cb148e`, 9,384 s.
2. **Gianluca, voz real** (alternativa autorizada): `originales/ROCCE_Voz_Gianluca_Referencia_Original.wav`, sha256 `42dffea0112160ee6c01ef2f501da3f6aea16654c140ed95225726b43c2617f1`, 24,639 s (dos notas de voz del 23/10/2026 unidas con 0,30 s de pausa, sin procesar).
- La voz guía de `ROCCE_lo_que_te_frena_v02` (Chatterbox, voz incorporada) **no es referencia** y no se vuelve a usar como voz de marca.
- Registro completo (procedencia, parámetros, motor, receta, sha256 de cada archivo): `REGISTRO_BANCO_VOCAL.json` en la página. JSON original de Gianluca: `originales/ROCCE_Perfiles_Vocales_Verificados.json` (sha256 `df5cc802…c465`).

## Firme 04: configuración y cómo se genera
- Documentado en el MP3 aprobado: base `es-AR-ElenaNeural`, rate `+11%`, pitch `-20Hz`; tratamiento formants 0,94 · pitch_factor 0,93 · tempo 1,0 · saturation_mix 0,055 · max_internal_pause_ms 180; pronunciación **"Royé"** (en pantalla siempre Roccé).
- **No documentado:** transporte y código originales; orden y operadores exactos del tratamiento. No inventar proveedor, credenciales ni voice_id.
- Motor usado desde el 28/10/2026:
  1. `scripts/voz/edge_firme.py`: síntesis con edge-tts 7.3.1 (servicio en línea de lectura en voz alta de Microsoft Edge, sin cuenta). edge-tts arma su TLS con certifi: el script apunta certifi al CA del proxy del contenedor (`/root/.ccr/ca-bundle.crt`); nunca desactivar la verificación.
  2. `scripts/voz/tratamiento_firme.py`: reconstrucción del tratamiento con Praat (parselmouth). Pausas ≤ 180 ms → "Change gender" (formantes ×0,94, mediana de tono ×0,93) → saturación suave 5,5 % → pico −1 dBFS.
  3. `scripts/voz/comparar_voz.py`: compara contra la referencia. Con el mismo texto que el MP3 aprobado da tono 166,0 vs 167,2 Hz, F1 387 vs 386 Hz y diferencia de espectro 1,26 dB (sin tratamiento: 2,62 dB). Son medidas; no reemplazan escuchar.
- Locución de una pieza: `scripts/proxima/locucion.py GUION.tsv SALIDA` (una frase por línea, "Royé" y "fáunders" escritos así) + `scripts/proxima/palabras.py SALIDA` (marcas por palabra). **Probar primero una frase corta con Roccé.**
- No se clonó ninguna voz. Si algún día se clona desde el MP3 ya tratado, no volver a aplicarle el tratamiento.
- Gianluca: grabación real. Para frases nuevas, que las grabe él; una síntesis basada en su referencia se informa como tal.

## Recuperación en una sesión nueva (probada el 28/10/2026)
1. Entornos: `S=<scratchpad> scripts/instalar_entorno.sh "$S" voz whisper` (voz-env: `scripts/requisitos/voz.txt`).
2. Bajar el banco con la herramienta Artifact: `action: "read"`, `url: https://claude.ai/artifact/AQSWzDitj143yjJdqkoXQk`, `paths: [...]` (rutas de la tabla de `REGISTRO_BANCO_VOCAL.json`), `out_dir: <scratchpad>/banco_vocal`.
3. Comparar el sha256 de cada archivo con el registro. Prueba del 28/10: Firme, Gianluca, JSON, `L5.wav` y `tratamiento_firme.py` bajaron con el mismo sha256 que los originales.
4. Para rehacer exactamente `ROCCE_proxima_v01`: copiar `locuciones/proxima_v01/*` a `TRABAJO/proxima/voz/` y correr `scripts/proxima_v01.sh`.
- Si la página no se puede leer (otra cuenta, permisos), pedirle a Gianluca los archivos o que la abra; no reemplazar la voz en silencio.
- Una carpeta temporal del contenedor o un modelo en caché no son almacenamiento: el contenedor se borra.
