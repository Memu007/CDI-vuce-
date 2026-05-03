# Plan 04 · Catálogo unificado (v2)

> Ejecutar cuarto. El más grande. Cierra el ciclo: alta → aprende → reconoce.
> Depende idealmente de Plan 03 (para que exista cliente al que aprender), pero puede ejecutarse sin él.

## Objetivo

Eliminar el concepto "Mapeo de columnas" y reemplazarlo por un **Catálogo por cliente** que se llena solo. El catálogo tiene dos dimensiones:
1. **Columnas** que el cliente usa en sus Excel (aprendidas en el primer upload).
2. **Productos** que el cliente importa habitualmente (aprendidos al generar MARIA).

La UI no tiene formulario manual. Solo muestra lo aprendido y permite editar/olvidar.

## Principios

- **Zero setup**. El usuario nunca configura mapping a mano en condiciones normales.
- **Aprendizaje silencioso**. La primera op enseña, las siguientes reconocen. Sin ceremonias.
- **Tolerancia a catálogo parcial**. Si la heurística detectó 4/6 columnas, se guarda lo detectado con badge "Parcial 4/6" y sigue aprendiendo en próximas ops.
- **Editable pero no obligatorio**. El usuario puede corregir/olvidar en cualquier momento, pero nunca es requerido.

## Alcance

### Fase 4.1 — Rename "Mapeo" → "Catálogo"

- UI: la pestaña/sub-panel "Mapeo" del drawer se renombra a "Catálogo".
- API interna: endpoints y campos se renombran a `catalogo`:
  - `GET /api/clientes/{id}/column_mapping` → `GET /api/clientes/{id}/catalogo/columnas`
  - `POST /api/clientes/{id}/column_mapping` → `PUT /api/clientes/{id}/catalogo/columnas`
  - `DELETE /api/clientes/{id}/column_mapping` → `DELETE /api/clientes/{id}/catalogo/columnas`
- DB: el campo `Client.column_mapping` se mantiene (interno), no se renombra en DB para evitar migración innecesaria. Solo la API/UI usan el término "catálogo".
- Deprecation: los endpoints viejos se mantienen con `@deprecated` y logging por un release, para no romper nada.

### Fase 4.2 — Auto-inferencia de columnas al primer upload

- Al subir Excel con `cliente_id` presente, si el cliente no tiene `column_mapping` (o tiene parcial), el backend:
  1. Detecta headers con la heurística existente (`detect_columns_heuristic`).
  2. Guarda lo detectado en `Client.column_mapping` (mergea con lo previo si había parcial).
  3. Devuelve en la respuesta del upload: `{ catalogo: { columnas_detectadas: 4, columnas_faltantes: ['peso_unitario','valor_unitario'] } }`.
- Frontend muestra toast sutil: "Catálogo aprendido: 4 de 6 columnas reconocidas."

### Fase 4.3 — Sub-vista Catálogo en el drawer

Reemplaza la actual sección "Mapeo" con una sección "Catálogo" que tiene 2 sub-secciones:

#### 4.3a — Columnas reconocidas

- Tabla simple de 6 filas (una por campo canónico: pieza, descripcion, origen, cantidad, valor_unitario, peso_unitario).
- Cada fila muestra el header detectado (editable inline) o placeholder "— Sin reconocer —" con estilo grisado.
- Badge arriba: `6/6 ✓` (verde), `4/6 ⚠️ Parcial` (amarillo), `0/6 · Sin catálogo aún` (gris).
- Botón "Olvidar columnas" → DELETE endpoint, confirma con toast.

#### 4.3b — Productos aprendidos

- Tabla de productos del cliente (`ClientProductHistory`).
- Columnas: descripción, NCM, origen, peso, veces usado, última op.
- Editable inline (NCM/origen/peso).
- Botón "Olvidar producto" por fila → DELETE `/api/clientes/{id}/catalogo/productos/{id}`.
- Empty state: "Todavía no aprendí productos. Se van a guardar cuando generes tu primera MARIA con este cliente."

### Fase 4.4 — Learn al generar MARIA

- Ya parcialmente implementado en `finalize.js` (F3 + F4e).
- Verificar que `saveOperationToHistory` también actualice `ClientProductHistory` vía `POST /api/clientes/{id}/catalogo/productos/learn`.
- Endpoint recibe items de la op y upsert-ea cada uno (match por descripción normalizada).

### Fase 4.5 — Autofill silencioso en review

- Cuando hay cliente activo y se entra a review:
  - Por cada item cuya `descripcion` no tiene NCM asignado, buscar en catálogo del cliente.
  - Si hay match exacto o fuzzy ≥ 0.90 → pre-fill NCM + origen + peso.
  - Mostrar mini-icono "📚" al lado del NCM para indicar "vino del catálogo del cliente".
- Fallback al catálogo vendor-scoped (F4e existente) si no matchea en el del cliente.
- Zero UX adicional — debe pasar desapercibido en el happy path.

## Files clave

- `proyecto_maria/database/models.py` → revisar `ClientProductHistory` (ya existe).
- `proyecto_maria/services/client_service.py` → `get_catalogo_columnas`, `update_catalogo_columnas`, `get_catalogo_productos`, `update_producto`, `delete_producto`, `learn_productos_from_items`.
- `proyecto_maria/main.py` → endpoints `/api/clientes/{id}/catalogo/*` + mantener antiguos deprecated.
- `proyecto_maria/static/v2/screens/clientes.js` → sub-vista Catálogo con ambas secciones.
- `proyecto_maria/static/v2/screens/upload.js` → manejar respuesta con info de catálogo y mostrar toast.
- `proyecto_maria/static/v2/screens/review.js` → autofill silencioso.
- `proyecto_maria/static/v2/screens/finalize.js` → verificar learn productos.
- `proyecto_maria/templates/dashboard_v2.html` → markup nueva sub-vista.
- `proyecto_maria/static/v2/app_v2.css` → estilos catálogo.

## Matching de productos (fuzzy)

- Normalización: upper, sin acentos, colapsar espacios/puntuación.
- Match exacto: prioridad 1.
- Match prefijo: prioridad 2 (ej: "TORNILLO HEX M6" matchea "TORNILLO HEX M6 12MM").
- Match fuzzy (Levenshtein): prioridad 3, threshold ≥ 0.90.
- En Python: usar `difflib.SequenceMatcher` o `rapidfuzz` si ya está instalado.

## Acceptance criteria

- Cliente nuevo sin catálogo + subir Excel → backend aprende columnas, toast aparece.
- Subir segundo Excel del mismo cliente → usa el catálogo guardado para mapear, sin reprocesar headers.
- Drawer → cliente → "Catálogo" muestra las 2 secciones con datos reales.
- Generar MARIA con cliente → productos quedan en `ClientProductHistory`.
- Segunda op del mismo cliente con items similares → NCMs auto-llenados en review, icono 📚 visible.
- "Olvidar columnas" resetea el catálogo.
- Endpoints antiguos (`column_mapping`) siguen respondiendo con deprecation warning.

## Tareas (todos)

### Backend

- [ ] `p04_endpoints_catalogo_columnas` — 3 endpoints nuevos + deprecations.
- [ ] `p04_endpoints_catalogo_productos` — GET/PUT/DELETE/learn + multi-tenant.
- [ ] `p04_service_columnas` — refactor ClientService con nuevas funciones.
- [ ] `p04_service_productos_matcher` — fuzzy match function.
- [ ] `p04_upload_aprende` — al subir Excel con cliente_id, guardar columnas detectadas.
- [ ] `p04_upload_response` — incluir info de catálogo en response.

### Frontend

- [ ] `p04_drawer_rename` — UI "Mapeo" → "Catálogo".
- [ ] `p04_drawer_columnas` — sección columnas reconocidas editable.
- [ ] `p04_drawer_productos` — sección productos aprendidos editable.
- [ ] `p04_drawer_empty_states` — mensajes cuando no hay catálogo.
- [ ] `p04_upload_toast` — toast al aprender columnas.
- [ ] `p04_review_autofill` — prefill silencioso en review con catálogo del cliente.
- [ ] `p04_finalize_learn` — verificar que productos se aprendan en generate MARIA.

### Smoke

- [ ] `p04_smoke_nuevo` — cliente nuevo: upload → aprende → segunda op → reconoce.
- [ ] `p04_smoke_parcial` — upload con headers raros → catálogo parcial → segundo upload completa.
- [ ] `p04_smoke_edit` — editar y olvidar funcionando.

## Estimación

~4-5h de implementación (es el plan más grande), 45 min de smoke. Backend antes que frontend.
