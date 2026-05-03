# Plan 02 · Clientes drawer polish (v2)

> Ejecutar segundo. Mejora la pantalla de Clientes con features que ya existen en v1.
> No depende de los planes 03 ni 04.

## Objetivo

Paridad funcional con v1 para la gestión de clientes desde la lente del despachante. Seis mejoras concretas al drawer de clientes sin sumar ventanas nuevas.

## Alcance

1. Cinco KPIs completos en el detalle del cliente.
2. Orden de la lista por último movimiento descendente (en vez de solo "favoritos primero").
3. Badge de operaciones por fila en la lista.
4. Exportar CSV del historial del cliente.
5. Expand "Ver todas las operaciones" (hoy corta en 5).
6. Filtro "solo favoritos" con checkbox.

## Files clave

- `proyecto_maria/services/client_service.py` → asegurar que `get_metricas` retorne los 5 campos + `origen_frecuente`.
- `proyecto_maria/main.py` → portar endpoint `GET /api/clientes/{id}/export.csv` (hoy vive en `routers/_deprecated/client_router.py`).
- `proyecto_maria/static/v2/screens/clientes.js` → UI para los 6 items.
- `proyecto_maria/static/v2/app_v2.css` → estilos KPIs + badge + filtro.

## Comportamiento

### 1. Cinco KPIs (final: operaciones, última op, items totales, promedio items/op, origen más frecuente)

- Header del detalle del cliente muestra grilla de 5 tarjetas pequeñas.
- Backend: `ClientService.get_metricas(client_id)` calcula `origen_frecuente` agrupando `items.origen` por todas las operaciones del cliente (desempate por `veces_usado DESC, fecha_ultima DESC`).
- Si no hay datos aún, muestra `—` (dash) y no rompe el layout.

### 2. Orden de la lista

- `GET /api/clientes` retorna array sorted por:
  1. `favorito=true` primero (sigue siendo prioridad visual).
  2. Dentro de cada grupo, `ultimo_movimiento DESC`.
  3. Fallback: `nombre ASC`.
- Implementado server-side en la query SQL (no client-side) para consistency con paginación futura.

### 3. Badge de operaciones por fila

- Cada fila de cliente en la lista muestra badge pequeño a la derecha del nombre: `· 23 ops` (con punto separador).
- Si 0 ops → no muestra badge.
- Dato viene en el mismo `GET /api/clientes` (sumar `total_operaciones` al payload si no está).
- Evitar N+1: no fetch individual por cliente como hace v1.

### 4. Exportar CSV

- Portar endpoint `/api/clientes/{id}/export.csv` desde `routers/_deprecated/client_router.py` a `main.py`, multi-tenant safe (`owner_username` filter).
- Columnas: `fecha, op_id, total_items, valor_total, ncms, origenes` (CSV UTF-8 con BOM para Excel).
- Botón "Exportar CSV" en el detalle del cliente, al lado de "Cerrar detalle".
- Click → navega a la URL con `?t={jwt}` en query para auth, o usa link con cookie (preferir cookie si ya hay sesión).

### 5. Expand "Ver todas las operaciones"

- Hoy lista últimas 5 en el detalle.
- Si `total_operaciones > 5`, mostrar botón "Ver todas ({n})" debajo de la lista.
- Click → expande inline a todas las operaciones (scrollable si son muchas).
- Botón se transforma a "Mostrar menos" cuando está expandido.
- Nada de paginación server-side por ahora (asumimos < 200 ops/cliente).

### 6. Filtro "solo favoritos"

- Checkbox "⭐ Solo favoritos" arriba de la lista, al lado del input de búsqueda.
- Filtrado client-side (no request nuevo): mostrar solo `cliente.favorito === true`.
- Estado persistido en `localStorage.cdi_v2_clientes_only_favs`.

## Acceptance criteria

- Abrir detalle de un cliente con 3+ ops muestra los 5 KPIs con valores reales.
- Al crear una op con cliente activo y volver al drawer, el cliente sube al tope de la lista (por último movimiento).
- Cada fila muestra `· N ops` cuando tiene historial.
- Click en "Exportar CSV" descarga archivo con datos reales del cliente.
- Click en "Ver todas" expande operaciones 6, 7, 8... inline.
- Checkbox "Solo favoritos" filtra la lista y persiste al recargar.

## Tareas (todos)

- [ ] `p02_metricas_origen` — agregar `origen_frecuente` a `get_metricas`.
- [ ] `p02_kpis_render` — 5 KPI cards en el detalle.
- [ ] `p02_sort_backend` — orden SQL por último movimiento.
- [ ] `p02_badge_ops` — agregar `total_operaciones` al payload de lista + render badge.
- [ ] `p02_csv_endpoint` — portar endpoint + multi-tenant.
- [ ] `p02_csv_button` — botón en detalle.
- [ ] `p02_expand_ops` — ver todas/mostrar menos inline.
- [ ] `p02_filter_favs` — checkbox + filtro client-side + persist.
- [ ] `p02_smoke` — crear cliente, crear op, verificar badge, KPIs, CSV, expand, filtro.

## Estimación

~2h de implementación, 20 min de smoke. Puede paralelizarse (KPIs + CSV + filtro son independientes).
