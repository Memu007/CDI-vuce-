# Video de presentación

`./scripts/video/build.sh` genera `proyecto_maria/static/v2/media/cdi-presentacion.mp4`
(1920x1080, 30 fps, ~21 s, sin audio) y `cdi-presentacion-poster.png`.

Qué hace: levanta la app con base SQLite y datos descartables en `/tmp`, da de
alta un usuario y dos clientes ficticios (CUIT `30-00000000-7`, `30-00000001-5`),
graba con Playwright el recorrido real Excel → Revisar → NCM → Validar → MARIA.TXT
(`capture.js`), corta los tramos con `cut_clips.py` y compone tarjetas + ventana con
`composer.html` + `render.js` (cuadro por cuadro en Chromium, codificado con ffmpeg).
No toca Gemini, VUCE, MercadoPago ni producción.

Los textos del video están en `render.js` (`scenes`); los estilos, en `composer.html`.
Para embeberlo en la landing: `<video src="/static/v2/media/cdi-presentacion.mp4"
poster="/static/v2/media/cdi-presentacion-poster.png" autoplay muted loop playsinline>`.
