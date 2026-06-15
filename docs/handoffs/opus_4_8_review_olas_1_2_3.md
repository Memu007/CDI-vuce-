# Handoff Opus 4.8 — Revisión Olas 1, 2 y 3

> Fecha: 2026-06-15  
> Tarea: revisar Olas 1, 2 y 3 (FUNCIONAMIENTO, no MP) y dejar anotaciones de mejoras/errores/riesgos.  
> Objetivo final del repo: producto comercial listo.

---

## Ola 1 — Cockpit + S1/S3

Archivos: `main.py` cockpit endpoints, `routers/_deprecated/history_router.py`, auth.

Dudas concretas:
1. ¿El panel `/dev/dashboard` con `/api/dev/wave1-kpis` sigue siendo útil o debería migrarse al dashboard principal?
2. `routers/_deprecated/history_router.py` tiene `require_plan` hardcodeado a premium — ¿está realmente desenchufado y seguro de borrar?
3. CSRF double-submit cookie está en report-only. ¿Listo para pasar a enforce?

## Ola 2 — Planes 02 y 03 (Clientes drawer + alta desde review)

Archivos: `static/v2/screens/clientes.js`, `main.py` `/api/clientes/*`, `models.py` `Client`.

Dudas concretas:
1. Drawer de clientes: al cargar muchas operaciones, ¿hay paginación o envía todo?
2. Búsqueda server-side `/api/clientes/search`: ¿protegida contra inyección / caracteres especiales?
3. Export CSV: ¿ filtra bien por `owner_username`?

## Ola 3 — Plan 04 (Catálogo unificado)

Archivos: `main.py` `/api/clientes/{id}/catalogo/*`, `static/v2/screens/clientes.js` pestaña Catálogo, `core/excel_parser.py`.

Dudas concretas:
1. `Client.column_mapping` es JSON. ¿Hay límite de tamaño / validación estructural?
2. Autofill desde catálogo del cliente: ¿qué pasa si dos clientes tienen la misma descripción y NCM distinto? ¿Prioriza cliente activo?
3. Botón "Olvidar" tiene confirmación, pero ¿elimina lógicamente o físicamente del historial?

## Riesgo transversal

- `viejo/` está en `.gitignore` pero existen en local algunos scripts con secretos viejos (`test_reset_flow.py` consulta?). Verificar que nada de prod quede en tests o docs.
- `pytest 8.4.2` vulnerable (dev-only). ¿Actualizamos ahora o esperamos a post-Ola4?

## Formato de respuesta esperado

Para cada Ola, devolver:
1. Errores encontrados.
2. Mejoras sugeridas (con justificación).
3. Riesgos al tocar MP/Ola4.

Sin diff largo. Conclusión arriba.
