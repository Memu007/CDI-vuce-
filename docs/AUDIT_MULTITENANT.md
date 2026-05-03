# Auditoría multi-tenant (D4 del plan integrado)

Fecha: 2026-04-20
Scope: aislar datos por usuario antes de abrir beta a 3-5 despachantes.

## Hallazgos críticos

### 1. Modelos SQLAlchemy sin owner

`proyecto_maria/database/models.py`:

| Modelo                   | Tiene `owner_username`? | Consecuencia                                      |
|--------------------------|-------------------------|---------------------------------------------------|
| `User`                   | n/a                     | OK, el owner en sí.                               |
| `Client`                 | ❌                      | Clientes compartidos entre usuarios.              |
| `Operation`              | ❌ (solo `client_id`)   | Hereda de Client, pero Client no tiene owner.     |
| `OperationItem`          | ❌ (solo `operation_id`)| Idem.                                             |
| `NCMNote`                | ❌ (solo `client_id`)   | Idem.                                             |
| `ClientProductHistory`   | ❌ (solo `client_id`)   | Idem.                                             |
| `SystemBackup`           | ❌                      | Backups sin dueño, expuestos a admins.            |
| `APILog`                 | ❌                      | Logs sin owner. Menor prioridad (auditoría).      |

Problema extra: `Client.email` es `unique=True` globalmente. En multi-tenant
dos despachantes distintos pueden tener el mismo cliente (mismo email);
el constraint debe ser `UNIQUE (owner_username, email)`.

### 2. Endpoints sin autenticación (hueco crítico)

`proyecto_maria/routers/client_router.py`:

- `GET/POST/PUT/DELETE /api/clientes/public` — sin auth, el frontend los usa.
- `POST /api/clientes/demo`
- `POST /api/clientes/{id}/favorito`
- `GET/POST /api/clientes/{id}/operaciones`
- `POST /api/clientes/{id}/operaciones/demo`
- `GET /api/clientes/{id}/metricas`
- `GET /api/clientes/{id}/export.csv`
- `GET/POST/DELETE /api/clientes/{id}/column_mapping`
- `POST /api/clientes/{id}/plantilla`
- `POST /api/clientes/detect`
- `GET /api/clientes/{id}/productos-frecuentes`
- `POST /api/items/autocomplete`
- `POST /api/clientes/{id}/update-history`

Todos estos aceptan requests anónimos y operan sobre datos de todos los
usuarios. Para beta hay que:

1. Requerir `user=Depends(get_current_user)` en todos.
2. Filtrar queries por `owner_username`.
3. Eliminar los endpoints `public` (el frontend ya está logueado).

### 3. DataStore legacy roto + DataStore nuevo mal integrado

`client_router.get_store()` intenta cargar `proyecto_maria/database.py` que
**no existe** en el repo. Fallback: `DummyStore` que no persiste nada.
Resultado actual: los endpoints de clientes responden pero no guardan.

`proyecto_maria/core/datastore.py` tiene `DataStore` con 2 backends
(PostgreSQL e InMemory) que **sí** filtran por `user_id`, pero:

- El `user_id` es un UUID random (dev) o el del usuario fijo `"demo"` (PG).
- Nunca viene del request del usuario logueado.
- No está conectado al `client_router`.

Además, las queries PostgreSQL usan columnas que no existen en los modelos
SQLAlchemy: `clients.favorite`, `clients.notes`, `operations.op_code`,
`operations.source`, `operations.extra`, `ncm_notes.ncm`. Indica que
producción tenía un schema a mano que no matchea los modelos.

### 4. Datos persistidos en JSON sin owner

`proyecto_maria/main.py`:

- `CLIENTS_FILE = data/clientes.json` — hoy vacío, pero lectura/escritura global.
- `NCM_NOTAS_FILE = data/ncm_notas.json` — notas de NCM sin dueño.

`proyecto_maria/core/catalog_service.py`:

- `product_catalog.json` — catálogo de productos por proveedor, sin dueño.

`proyecto_maria/core/error_notes_tracker.py`:

- `error_notes.json` — tracking de errores sin dueño.

### 5. Secret management (fix hecho en D7)

- `SECRET_KEY` default débil → ya se endureció el chequeo (D7).
- `CORS`: `allow_origins=["*"]` + `allow_credentials=True` era inválido por spec;
  ya se arregló (D7).

## Plan de remediación

### D4 (este sprint): modelos + migración

1. Agregar `owner_username: str | None = Column(..., ForeignKey("users.username"))`
   a los 5 modelos (`Client`, `Operation`, `NCMNote`, `ClientProductHistory`,
   `SystemBackup`).
2. Quitar `unique=True` de `Client.email`, agregar `UniqueConstraint("owner_username", "email")`.
3. Agregar columnas faltantes usadas por el DataStore PG: `Client.favorite`,
   `Client.notes`, `Operation.op_code`, `Operation.source`, `Operation.extra`.
4. Script `scripts/migrate_add_owner.py` para SQLite:
   - `ALTER TABLE ... ADD COLUMN owner_username TEXT`.
   - Backfill con usuario `demo` para datos existentes (hoy casi vacío).
   - Drop y recreate `UNIQUE(email)` → `UNIQUE(owner_username, email)`.

### D5: JSON → DB y filtros

1. Eliminar `CLIENTS_FILE` y `NCM_NOTAS_FILE` como source of truth. Usar DB.
2. `product_catalog.json` → tabla `product_catalog` con `owner_username`.
3. Refactor `DataStore` para aceptar `owner_username` por request en vez
   de global.
4. En **cada** endpoint de `client_router`, `items_router`, `history_router`,
   `validation_router`, `templates_router`, `calculator_router`:
   - Agregar `user=Depends(get_current_user)`.
   - Pasar `user["username"]` al datastore.
   - Filtrar queries por `owner_username=user["username"]`.
5. Eliminar endpoints `/api/clientes/public*` o forzar auth.

### D6: test end-to-end

Script manual `scripts/test_multitenant.py`:

1. Crear 2 users demo (`alice`, `bob`) vía la API de registro.
2. Login como alice → crear cliente "Importadora Alice".
3. Login como bob → listar clientes → debe devolver 0 (no ver a Alice).
4. Login como bob → crear cliente "Importadora Bob".
5. Subir PDF como alice → verificar que la operación queda asociada.
6. Login como bob → listar operaciones → no debe ver la de Alice.

## Métricas de salida

- 0 endpoints sin auth en los routers listados.
- 100% de queries SQL con filtro por `owner_username`.
- Test end-to-end pasa (0 leaks entre alice y bob).
- `grep -rn "CLIENTS_FILE\|NCM_NOTAS_FILE" proyecto_maria/` → 0 matches en código de producción (solo historia en git).

## D5b — Cierre (2026-04-19)

Auditado el resto de `main.py` (69 endpoints `@app.*`). Hallazgos y
acciones:

### Endpoints protegidos en esta pasada

| Endpoint | Riesgo previo | Fix |
| --- | --- | --- |
| `GET /api/dev/stats` | exponia logs de API publicamente | auth obligatoria |
| `POST /api/backup/localStorage` | backup shared entre users | auth + `owner_username` |
| `GET /api/restore/localStorage` | cualquiera recuperaba el ultimo backup | auth + filtro por owner |
| `POST /process_operation/` | generar Excel sin sesion | auth obligatoria |
| `POST /upload_excel/` | subir y procesar Excel sin sesion | auth obligatoria |
| `POST /upload_excel/public` | alias legacy sin auth | auth (alias compat frontend) |
| `POST /upload_pdf/public` | subir PDF y quemar cuota Gemini sin auth | auth obligatoria |
| `POST /api/validate/smart` | validacion sin auth | auth obligatoria |
| `POST /generate_maria` | generar TXT MARIA sin auth | auth obligatoria |
| `POST /generate_maria_export` | idem export | auth obligatoria |
| `POST /api/ncm/sugerir` | quemar cuota Gemini sin auth | auth obligatoria |
| `POST /api/ncm/guardar-uso` | escribir historial compartido sin auth | auth obligatoria |

Refactor colateral: `get_current_user` se movio arriba del archivo para
que los endpoints anteriores pudieran usarla como `Depends()`.

### Endpoints que quedan publicos (intencional)

- `GET /`, `/web`, `/landing*`, `/login`, `/recover*`, `/dashboard` — UI.
- `GET /app.js`, `/app_fixed.js`, `/app.css`, `/features_integration.js` — assets.
- `GET /api/health` — healthcheck.
- `GET /api/financials` — solo cotizaciones USD publicas (cache compartido).
- `POST /auth/register`, `/auth/login`, `/auth/request-reset`, `/auth/reset-password`, `/auth/verify-email`, `/auth/resend-verification`, `/logout` — flow de auth.
- `POST /api/payments/*` — checkout y webhooks (flow propio).

### Routers huerfanos → `_deprecated/`

Los 5 routers que pedia el plan (`items_router`, `templates_router`,
`calculator_router`, `history_router`, `validation_router`) **nunca
estaban incluidos** en `main.py`. Tambien estaban huerfanos
`client_router` y `pdf_router`. Los 7 se movieron a
`proyecto_maria/routers/_deprecated/` con README explicando que hay
que hacer antes de reactivarlos.

Esto elimina ambiguedad (no mas duda de si estan o no expuestos) y
previene reintroduccion accidental del hueco.

### Resultado

- Antes de D5b: 28 endpoints `@app.*` sin auth (muchos criticos).
- Despues de D5b: 0 endpoints criticos sin auth.
- Test `scripts/test_multitenant.py` sigue pasando (12/12 pasos).
- Smoke manual: `POST /process_operation/` sin cookie → 401; con cookie valida → 200 (validado via curl).
