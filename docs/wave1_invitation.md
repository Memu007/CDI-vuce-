# Wave 1 — invitaciones y estudios

Texto vivo para equipo de producto: Loom corto guion, email tipo, FAQ y estudios rápidos.

## Loom (2–4 minutos, guión)

1. Qué probás: nueva operación con PDF real vs simulador.
2. Mostrar: cliente activo, aviso cuando el PDF trae importador nuevo, botón “Crear cliente y usar”.
3. Decir que no pisamos tu cliente elegido si ya lo tenías seleccionado.
4. Pedir una fricción honesta (“qué frenó / qué esperabas”).

## Email de invitación (borrador)

Asunto: Probar nueva carga MARIA · 15 min

Cuerpo: Hola _, estamos midiendo tiempo hasta el primer archivo listo y la claridad del flujo importador/PDF. Si podés cargar una operación real (o usar “Simular”), y responder 4 preguntas al final del form, nos sirve una banda. Link: _

## FAQ corta

- **¿Se guardan mis datos del PDF fuera de mi cuenta?** No; lo que cuenta es estadística agregada y eventos anonimizables con tu usuario sólo después de iniciar sesión.
- **¿Me cambian el cliente sin avisarme si subo otro PDF?** No: si ya tenés cliente activo, ese no se sustituye automáticamente por el que trae otro archivo.
- **¿Qué es “Crear cliente y usar”?** Da de alta rápido al importador del PDF como cliente tuyo y lo deja seleccionado.

## Cinco estudios rápidos (encuesta 5 opciones cada uno)

1. ¿Hallaste rápido dónde subir el PDF? (sí/medio/no)
2. ¿Entendiste qué hacer con importador nuevo? (sí/medio/no)
3. ¿Alcanzaste a generar / ver el siguiente paso? (sí/casi/no)
4. ¿Confiarías en esto con un archivo real urgente? (sí/medio/no)
5. ¿Recomendarías a un par? (ya / con reservas / no)

## Documentación PM relacionada

- **[Definiciones “usuario activado”](./wave1_activation_definitions.md)** (tabla de opciones A–F y métricas en `/api/dev/wave1-kpis`).
- **[Kit entrevistas + contraste con panel](./wave1_interview_kit.md)** — para ejecutar la tanda 3–5 conversaciones sin improvisar métricas.
- **[Puerta Fase 2](./wave1_phase2_gate.md)** — cuando tengamos ventana estable de datos o feedback suficiente.

## Rescore rápido (priorizar backlog)

Cuando lleguen datos del panel Wave 1: si `importador_no_match` y abandono antes de MARIA ↑, subir peso del banner + onboarding importador; si `upload_simulated` domina pero no pasan a PDF real ↓ friction en “subir archivo real”; si tiempo sesión→PDF medio alto revisar errores upload o campos obligatorios en revisión.

