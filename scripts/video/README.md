# Video de presentación

`./scripts/video/build.sh` genera en `proyecto_maria/static/v2/media/` dos versiones
(1920x1080, 30 fps, sin audio) y el póster `cdi-presentacion-poster.png`:

- `cdi-presentacion.mp4` (~40 s): los 5 pasos y, después, el tablero de operaciones,
  la ficha del cliente (historial, CSV, plantilla Excel), el catálogo de columnas,
  «Mi catálogo aprendido» con una NCM corregida y «Traer mis clientes».
- `cdi-presentacion-corto.mp4` (~22 s): sólo los 5 pasos.

Qué hace: levanta la app con base SQLite y datos descartables en `/tmp`, da de
alta un usuario y dos clientes ficticios (CUIT `30-00000000-7`, `30-00000001-5`),
graba con Playwright el recorrido real Excel → Revisar → NCM → Validar → MARIA.TXT
y las pantallas de después (`capture.js`), corta los tramos con `cut_clips.py` y compone tarjetas + ventana con
`composer.html` + `render.js` (cuadro por cuadro en Chromium, codificado con ffmpeg).
No toca Gemini, VUCE, MercadoPago ni producción. Por eso no se graba la lectura de
PDF: en la app pasa por Gemini y acá no hay clave; con `GEMINI_API_KEY` en el entorno
se podría agregar una escena con un PDF de factura ficticio.

Los textos del video están en `render.js` (`scenes`); los estilos, en `composer.html`.
Para embeberlo en la landing: `<video src="/static/v2/media/cdi-presentacion.mp4"
poster="/static/v2/media/cdi-presentacion-poster.png" autoplay muted loop playsinline>`.
