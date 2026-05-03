# Plan 03 · Alta de cliente desde operación (v2)

> Ejecutar tercero. Cambia el flujo principal: los clientes nacen desde la primera op, no antes.
> Depende de que la extracción de PDF ya devuelva CUIT y razón social (confirmar en paso 0).

## Objetivo

Eliminar la fricción de pre-registrar clientes. Cuando se carga una operación de un importador no reconocido, la v2 ofrece alta rápida en review con datos pre-filled del PDF, dedupe por CUIT, y aviso si hay nombre similar.

## Principios

- **Nunca bloquear el flujo**. El alta es opcional (dismissable). El usuario siempre puede "seguir sin cliente".
- **Cero fricción en el happy path**. Si el CUIT ya matchea → auto-selecciona cliente sin preguntar.
- **Dedupe confiable**. Por CUIT (canónico), fallback por nombre normalizado (warning, no auto-merge).

## Alcance

1. Backend: búsqueda `GET /api/clientes/search?cuit=...&nombre_similar=...` con match exacto CUIT + fuzzy nombre.
2. Backend: asegurar que el extractor de PDF expone `cuit`, `razon_social`, `domicilio` del importador.
3. Frontend: al entrar a review, detectar si hay CUIT extraído y consultar el search.
4. Frontend: tres caminos según resultado — match CUIT (silent), match nombre (warning banner), sin match (offer banner).
5. Frontend: mini-form lateral para alta rápida prefilled.
6. Telemetría de los tres caminos.

## Files clave

- `proyecto_maria/services/client_service.py` → `search_by_cuit(cuit)`, `search_by_nombre_similar(nombre)` (Levenshtein o trigram).
- `proyecto_maria/main.py` → `GET /api/clientes/search`.
- `proyecto_maria/pdf_extractor.py` → verificar campos extraídos; ajustar si falta `cuit` limpio.
- `proyecto_maria/static/v2/screens/review.js` → lookup + render banner.
- `proyecto_maria/templates/dashboard_v2.html` → markup banner + mini-form overlay.
- `proyecto_maria/static/v2/app_v2.css` → estilos banner + mini-form.

## Comportamiento por caso

### Caso A — CUIT extraído match exacto

- Al cargar review, fetch `/api/clientes/search?cuit=XXX`.
- Si 1 match → `CDI.state.clienteActivo = {...}`, emit `cdi:cliente-activo-cambio`.
- UI: pill del cliente arriba aparece ya seleccionado, sin banner.
- Telemetría: `ui_alta_cliente_auto_match`.

### Caso B — CUIT sin match, nombre similar encontrado (Levenshtein distance ≤ 3 sobre nombre normalizado)

- Banner amarillo arriba del review:
  > ⚠️ Importador "ACME S.A." no está en tu cartera. ¿Es el mismo que "Acme SA" (existente)?
  > **[Usar existente]** **[Crear nuevo igual]** **[Ignorar]**
- "Usar existente" → selecciona el cliente existente como activo.
- "Crear nuevo igual" → abre mini-form prefilled con datos del PDF.
- "Ignorar" → dismissa banner (no vuelve a aparecer para esta sesión).
- Telemetría: `ui_alta_cliente_fuzzy_match` con acción.

### Caso C — Sin match alguno, datos de importador presentes

- Banner azul (neutral) arriba del review:
  > Nuevo importador detectado: **ACME S.A.** (CUIT 30-12345678-9). ¿Guardar en tu cartera?
  > **[Crear cliente]** **[Seguir sin guardar]**
- "Crear cliente" → mini-form prefilled.
- "Seguir sin guardar" → dismiss, op continúa sin cliente activo.
- Telemetría: `ui_alta_cliente_offer` con acción.

### Mini-form de alta rápida

- Panel lateral pequeño (no drawer completo), 3 campos:
  - **Nombre** (razón social, required)
  - **CUIT** (required si se extrajo, optional si fue entrada manual)
  - **Domicilio** (optional, prefilled si existe)
- Campos prefilled con datos del PDF, editables.
- Botón "Crear y usar". Cierra panel, setea cliente activo, toast "Cliente creado: ACME S.A.".
- Si el POST falla (ej: CUIT duplicado detectado server-side), muestra error inline y ofrece "Usar el existente".

### Backend: endpoint search

```
GET /api/clientes/search?cuit=30123456789&nombre=ACME
```

Respuesta:
```json
{
  "match_cuit": { "id": "...", "nombre": "...", ... } | null,
  "matches_nombre": [ { "id": "...", "nombre": "...", "similitud": 0.92 }, ... ]
}
```

- Multi-tenant (filtrado por `owner_username`).
- CUIT normalizado (sin guiones) antes de comparar.
- Nombre normalizado: upper, sin acentos, colapsar espacios.
- `matches_nombre` devuelve top 3 con similitud > 0.80.

## Acceptance criteria

- PDF con CUIT conocido → cliente se auto-asigna silenciosamente en review. Sin banner.
- PDF con CUIT nuevo pero nombre parecido a existente → banner amarillo con 3 opciones funcionando.
- PDF con importador 100% nuevo → banner azul con offer.
- Crear cliente desde mini-form lo deja como activo y funcionando en el resto del flujo.
- En finalize, el cliente creado recibe la operación en su historial.
- "Seguir sin guardar" persiste: recargar review no vuelve a mostrar el banner.

## Tareas (todos)

- [ ] `p03_pdf_cuit` — validar/ajustar que el extractor devuelva CUIT limpio y razón social.
- [ ] `p03_search_backend` — endpoint `/api/clientes/search` + normalización + fuzzy match.
- [ ] `p03_review_lookup` — llamar search al entrar a review con CUIT presente.
- [ ] `p03_banner_markup` — markup + estilos de banners (A/B/C).
- [ ] `p03_banner_logic` — lógica de qué banner mostrar según respuesta.
- [ ] `p03_miniform` — panel lateral prefilled + POST cliente + setear activo.
- [ ] `p03_dedup_error` — manejo de CUIT duplicado en POST (raro pero posible).
- [ ] `p03_dismiss_session` — persistir dismiss en sessionStorage por op_key.
- [ ] `p03_telemetry` — los 3 eventos + acciones.
- [ ] `p03_smoke` — 3 casos end-to-end.

## Estimación

~3h de implementación, 30 min de smoke. El fuzzy match en backend es lo más delicado.
