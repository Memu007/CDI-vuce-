# Routers deprecados (NO ENGANCHADOS)

Estos routers **no estan incluidos en `main.py`** (solo se registra
`admin_router`). Quedaron como codigo legado de iteraciones anteriores.

**IMPORTANTE — si alguien en el futuro los quiere resucitar:**

Ninguno de estos endpoints tiene auth (`Depends(get_current_user)`) ni
filtrado multi-tenant (`owner_username`). Incluirlos directamente con
`app.include_router(...)` abre un hueco de seguridad instantaneo porque
permite leer/modificar datos de *cualquier* usuario.

Antes de reactivarlos:

1. Agregar `user=Depends(get_current_user)` a cada endpoint.
2. Filtrar queries por `owner_username == user["username"]`.
3. Hacer 404 en cross-tenant (ver patron en `/api/clientes/{id}` en
   `main.py`).
4. Agregar test de aislamiento en
   `proyecto_maria/scripts/test_multitenant.py`.

Routers aqui:

- `calculator_router.py` — calculadora de aranceles/impuestos.
- `client_router.py` — legacy CRUD de clientes (reemplazado por
  endpoints en `main.py` con auth + owner_username).
- `history_router.py` — historial por cliente.
- `items_router.py` — update/delete/duplicate de items.
- `pdf_router.py` — extraccion PDF (la version viva esta en
  `/upload_pdf/public` en `main.py`, ya con auth).
- `templates_router.py` — plantillas guardadas.
- `validation_router.py` — validaciones pre-MARIA.

Auditado el 2026-04-19 como parte de D5b.
