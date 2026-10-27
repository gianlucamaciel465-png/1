# Acceso a Instagram desde el entorno (prueba del 27/10/2026)

Herramientas: Chromium headless con Playwright (Node, preinstalado), `yt-dlp` 2026.10.21 y `curl`.
Scripts: `scripts/instagram_acceso.js`, `scripts/instagram_reels.js`. Capturas: `instagram_2026-10-27/`.

| Prueba | Resultado | Evidencia |
|---|---|---|
| Sesión autenticada | **No hay.** El navegador arranca sin cookies; al final solo tiene cookies anónimas (`csrftoken`, `mid`, `ig_did`, `datr`…), ninguna de sesión. No hay credenciales de Instagram en el entorno. | `instagram_acceso.js` |
| Feed (`instagram.com/`) | HTTP 200, portada sin sesión: "Iniciar sesión o registrarte". No se ve ningún feed. | `feed.jpg` |
| Perfil `@rocce.ar` (y `/reels/`) | **HTTP 429** (límite de solicitudes anónimas) y redirección a `accounts/login`. Página vacía. | `perfil_rocce.jpg` |
| API web del perfil (`web_profile_info`) | HTTP 401 `require_login` ("Please wait a few minutes…"). | — |
| Reel 1: https://www.instagram.com/reel/De9bn1GqBYQ/ | Página HTTP 200 con cartel de registro encima; **sin reproductor** (no hay `<video>`). Se lee el texto: "TOPARADI en Instagram: Join The Waitlist ➡️ LINK IN BIO #clothingbrand". `yt-dlp` (metadatos): cuenta toparadi, 1080×1920, publicado 26/10/2026. | `reel_1.jpg` |
| Reel 2: https://www.instagram.com/reel/DeSZWn3RYFG/ | Igual: cartel de registro, sin reproductor. Texto del posteo de Neuron Visuals ("You can spend forever getting the first brick right…"). `yt-dlp`: cuenta neuronvisuals, 1080×1920, publicado 09/10/2026. | `reel_2.jpg` |

- Lo observado son **texto del posteo, metadatos y capturas**. No se escuchó audio. Con `yt-dlp` se pueden bajar reels públicos sueltos si se conoce la URL (así se obtuvieron R11–R14), pero no hay forma de listar el perfil ni de ver el feed.
- Para acceder al feed o al perfil haría falta iniciar sesión con una cuenta (credenciales que no deben pasarse por el chat) o un conector oficial con permiso; no existe ninguno en esta organización.
