# Plan 01 · UX polish screens (v2)

> Ejecutar primero. Wins visibles y rápidos que no dependen de nada más.

## Objetivo

Pulir tres detalles UX sueltos de la v2 que el usuario pidió: fechas con máscara automática, lookup VUCE dentro del spotlight al tipear un NCM manual, y botón "Clientes" explícito en la topbar.

## Alcance

1. Helper `CDI.maskDate` y cableado en los dos inputs de fecha.
2. Panel VUCE (descripción oficial + alícuotas) dentro del spotlight "Cambiar" cuando el usuario tipea un código NCM válido.
3. Botón "Clientes" visible en la topbar-nav (hoy solo accesible por el pill del cliente activo).

## Files clave

- `proyecto_maria/static/v2/app_v2.js` → definir `CDI.maskDate(input)`.
- `proyecto_maria/static/v2/screens/review.js` → aplicar mask a `f_fecha_emision`, `f_fecha_embarque`.
- `proyecto_maria/static/v2/screens/ncm.js` → al tipear en el spotlight, si match regex `^\d{4,8}$`, consultar `GET /api/ncm/{ncm}/completo` y renderizar preview.
- `proyecto_maria/templates/dashboard_v2.html` → agregar `<button data-action="go-clientes">Clientes</button>` en topbar-nav.
- `proyecto_maria/static/v2/app_v2.css` → estilos `.vuce-preview` dentro del spotlight.

## Comportamiento

### 1. Dates mask

- Al tipear dígitos en el input se insertan `/` automáticamente en las posiciones 2 y 5 → `DDMMYYYY` se ve como `DD/MM/YYYY`.
- Backspace respeta los `/` (los salta).
- Aceptar pegado: si el usuario pega `19/04/2026` o `19042026`, se normaliza a `DD/MM/YYYY`.
- Validación existente en review.js no cambia (sigue pidiendo regex `DD/MM/AAAA`).

### 2. VUCE preview en spotlight

- Cuando el input del spotlight tiene `length >= 6` y matchea dígitos NCM, debounce 300ms.
- Fetch `GET /api/ncm/{ncm}/completo`. Renderizar en un bloque nuevo abajo de resultados:
  - Código + descripción oficial VUCE.
  - Alícuotas (DI, TE, IVA, ingresos brutos si vienen).
  - Nota si hay intervenciones.
- Si 404 o timeout, sin ruido (el input sigue funcionando normal).
- Cuando el usuario confirma (enter) con el código manual, se usa `source: 'manual'` (ya existe).

### 3. Botón Clientes en topbar

- Agregar `<button class="topbar-nav-btn" data-action="go-clientes">Clientes</button>` en el `.topbar-nav` del template.
- El handler `data-action="go-clientes"` ya existe y llama `CDI.openClientesDrawer()`, no hay lógica nueva.
- Estilo consistente con los otros botones de la topbar (Perfil, Ayuda).

## Telemetría

- Evento `ui_date_mask_applied` (opcional, debounced 5s).
- Evento `ui_vuce_preview_hit` con payload `{ ncm, fuente: 'spotlight' }`.
- Evento `ui_topbar_clientes_click`.

## Acceptance criteria

- Tipeando en `f_fecha_emision` con dígitos, el `/` aparece solo y la validación pasa.
- En NCM screen → botón "Cambiar" → tipeando `8471` muestra sugerencias como hoy; tipeando `84713010` muestra además panel VUCE con descripción oficial.
- Botón "Clientes" en topbar abre el drawer.
- Sin regresiones en `review.js` ni `ncm.js`.

## Tareas (todos)

- [ ] `p01_mask_helper` — `CDI.maskDate` en `app_v2.js`.
- [ ] `p01_mask_wire` — aplicar mask en review.js a los dos inputs de fecha.
- [ ] `p01_vuce_preview` — panel VUCE en spotlight (debounce + fetch + render).
- [ ] `p01_topbar_btn` — botón Clientes en topbar.
- [ ] `p01_smoke` — manual: fechas + NCM manual + topbar.

## Estimación

~45-60 min de implementación, 10 min de smoke.
