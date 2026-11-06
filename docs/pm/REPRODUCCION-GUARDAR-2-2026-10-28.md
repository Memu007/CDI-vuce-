# Reproducción de GUARDAR-2 (2026-10-28)

Entrega de la Dev técnica en `cef45ce` (informe `cb42e8f`). Diff de
producto `8e744a0..cef45ce`: sólo `proyecto_maria/main.py` (+50 −5), sin
migración (D32 b).

## Suite

Sobre `0d89c20` (ORDEN-1, que trae `cef45ce` entero), desde copia limpia,
SQLite: `1 failed, 3886 passed, 102 skipped, 3 xfailed`. El rojo es
`test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`
(«la subida normal dio 400 a los 30.0 s»): el mismo que daba la suite de la
PM en `8c63c37` (base aceptada de EXCEL-3f), la cola detrás de los libros
pesados que arregla EXCEL-2b (D4 a). Preexistente, no de esta pieza.

## Adversario (Sonnet alto, contexto nuevo)

Atacó dueño, cliente, proveedor, formas del NCM, vacíos y Postgres 16
(`guardar2_postgres.py` en un cluster propio: 16 OK, 0 fallas). No encontró
fuga entre despachantes ni SIM equivocada para otro producto. Cuatro
hallazgos; ninguno es del código de esta pieza:

1. **Reproducido por la PM.** Las pruebas no distinguen que se saque el
   filtro por `client_id` de `lookup_client_memory`
   (`services/client_memory.py`, de GUARDAR-1): sin esa línea,
   `test_guardar2.py` + `test_guardar1.py` dan `39 passed`; la prueba del
   adversario (dos clientes del mismo despachante, mismo nombre y CUIT,
   historial sólo en el primero) pasa con el código real y da
   `AssertionError: assert 'cliente' != 'cliente'` con el sabotaje. El
   código filtra bien; falta la prueba. Se suma a la próxima entrega de la
   técnica.
2. **Reproducido por la PM.** Con el catálogo caído, `POST /api/catalog/lookup`
   da 500 y se pierde también la sugerencia del cliente (`main.py:10288`,
   `match_items` fuera de un `try` propio). Igual en la base: preexistente.
   «Si falla el catálogo queda la del cliente» vale sólo en
   `/api/ncm/sugerir`. A riesgos.
3. **Reproducido por la PM.** `_vendor_key` da `""` para nombres sin letras
   latinas: dos proveedores así comparten catálogo dentro del mismo dueño, y
   ahora la SIM de uno completa la del cliente en el otro (misma
   descripción y mismos 8 dígitos). Preexistente (`catalog_service.py`),
   más visible con esta pieza. A riesgos.
4. Mismos 8 dígitos, otra SIM: si el cliente confirmó `…200X` y el catálogo
   tiene `…100D`, se sugiere `…100D`. Es lo que decidió D32 b (el historial
   guarda 8 dígitos); va a riesgos para que se sepa.

## Veredicto

Aceptada sobre `cef45ce`.
