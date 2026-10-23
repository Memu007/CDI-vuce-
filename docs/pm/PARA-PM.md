# Dev → PM

## EXCEL-2 integrada sobre release 648cd2f — devolución de 23 de octubre

**Resultado: no aceptar aún. El mensaje de subítems de CI está corregido; queda un rojo de concurrencia con cobertura en diagnóstico PM.** Rama local `codex/excel2-integration-648`, clone `/private/tmp/cdi-excel2-integration-648`. Base publicada `648cd2f`; producto inicial `7e9c4e0`; integración inicial de pruebas `d448033`. Devolución de los dos bloqueantes: producto `3906130`, pruebas `b073ba4`, prueba durable de concurrencia `0666881360962c3501b863ffbcd6a7518eacf25c`. La entrega original terminó con documentación `0389f0c`; después se corrige el mensaje específico de subítems en producto `be17e1b` (ver devolución siguiente).

### Alcance y preservación

Se aplicó sólo el diff EXCEL-2 `1cdfe49..04e1d0` con tres vías sobre `648cd2f`; ningún conflicto de producto. No se incorporó su historia, GUARDAR-2 ni cobro. No se trajeron los documentos PM antiguos: se preservaron los actuales y se reemplaza únicamente este canal Dev. El CHANGELOG sucio previo (11 líneas de EXCEL-2/XML) se conservó y se agrega esta devolución.

Las funciones de peso `_dice_de_una_unidad`, `_bruto_de_una_unidad`, `_clase_de_peso`, `_peso_por_unidad` y la guarda EC permanecieron idénticas al release. Continúan la clasificación DOC-1, el estado/undo por operación y `use_mapping` omitido=True/false explícito/422 inválido. Sin cambios de dependencias, topes, esquema ni despliegue.

### Dos bloqueantes corregidos

1. La lectura de `mergeCell` tenía otra regex literal de atributos y perdía el origen de la segunda línea con XML válido. Ahora Expat estándar lee los atributos de la primera hoja sin construir un árbol, reconoce comillas/espacios/entidades y sólo cuenta elementos del namespace de la planilla.
2. Ocho hojas de 10282491 bytes, dentro de 10 MiB, ocupaban la lectura de pandas antes de aplicar el límite de 5000 filas; la carga normal vencía a los 30 s. La misma pasada XML rechaza antes de pandas sólo cuando encuentra más de 5000+31 filas con valores numéricos reales. Es una cota conservadora: se descuentan hasta 31 filas para localizar el encabezado, no se cuentan huecos, estilos, sharedStrings, fórmulas sin valor ni NaN. No se usa nrows ni se truncan filas. El control completo posterior sigue vigente.

### Evidencia sobre esta devolución

- Rojo previo, nuevos fixtures sobre `d448033`: **4 failed, 1 passed**. Tres variantes XML pierden origen y la falta de guarda llega a pandas. Archivo aislado `/private/tmp/cdi-excel2-before-new-fixtures`.
- Focales de las seis propiedades nuevas: **6 passed, 113 deselected**. Incluyen encabezado desplazado, huecos e índices físicos, namespace ajeno, rechazo previo a pandas y referencias XML equivalentes.
- Sobre producto `b073ba4`: **362 passed, 3 warnings in 39.93s**, archivo EXCEL-2 más EXCEL-1, DOC-1 y seis focales MARIA. Log `/private/tmp/cdi-excel2-b073-focals.log`.
- La prueba durable de ocho entradas fue corregida en `0666881`: mide el tamaño XML real dentro de 9.5–10 MiB y espera una barrera de ocho entradas al validador, sin sleep. **1 passed, 118 deselected in 23.21s**; XML **10282491 bytes**, zip **796162 bytes**, ocho entradas y carga normal **200 en 22.6 s**. Log `/private/tmp/cdi-excel2-durable8.log`.
- Harness acotado independiente sobre mismo producto `b073ba4`: `concurrent_border` exit0 sin corte, normal **200 en 23.292 s**, ocho libros rechazados por el límite de filas, pico de familia RSS **254394368 bytes**. Ambas comillas en `merged_quote` conservan CN/CN y exit0. Scripts y logs `/private/tmp/cdi-excel2-independent/measurements/`. Hubo una medición previa de 25.138 s también verde; no se cuenta como otro criterio.
- Estos tiempos cumplen el 200 pedido, pero quedan cerca del timeout de 30 s. No se afirma fluidez ni garantía universal de memoria o concurrencia.

### Comandos y pendientes

```sh
rtk proxy env ENVIRONMENT=testing GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x /private/tmp/cdi-clean-requirements-20261020/bin/python -m pytest -q --no-cov tests/test_excel2.py
rtk proxy /private/tmp/cdi-clean-requirements-20261020/bin/python /private/tmp/cdi-excel2-new-negatives.py
```

El segundo comando contiene dos mutaciones nuevas en archivos temporales, no toca el checkout. **Resultado: 2/2 mutaciones dan rojo por la causa esperada**, con exit de pytest 1 verificado: guarda de filas desactivada llega a pandas; lectura de combinadas desactivada pierde CN. Logs `/private/tmp/cdi-excel2-new-negative-filas.log` y `/private/tmp/cdi-excel2-new-negative-combinadas.log`. Las **42 mutaciones históricas de `scripts/testing/sabotajes/excel2.sh` NO se corrieron** sobre esta integración: no afirmar 42/42 ni heredar verdes de otra versión. El harness temporal de selección focal quedó preparado pero no se ejecutó; el rojo previo y los negativos nuevos cubren los dos bloqueantes de esta devolución.

Suite completa limpia y CI/e2e: **no corridas por esta Dev**, PM coordina sobre `0666881` (documentación posterior no cambia producto). Las mediciones y revisiones de QA se reportan con su alcance; no sustituyen importación real en Kit MARIA. CSV malformado queda como observación menor separada; no se amplió alcance.

Sin push, main ni publicación. PM decide aceptación.

Última vuelta: 2026-10-23.
Contexto: ~60 %.
/compact conservar: EXCEL-2 integrada local sobre648cd2f, producto3906130, pruebas b073ba4+0666881; dos rojos corregidos, 362 focales y durable8 verdes; logs en/private/tmp; 42negativos históricos no corridos, suite/CI independientes pendientes; sin publicar, preservar límites10MiB/5000 y DOC1/pesos/Form.


## Devolución CI y suite — 23 de octubre

CI de PR5 `39943030809` dio cuatro fallos: los subítems escalares se rechazaban con el mensaje genérico de producto. La guarda temprana añadida por EXCEL-2 estaba en `main.py`, no en `controles_maria`: ahora distingue producto no-dict y subítems mal formados, conserva el mensaje específico anterior y todas las guardas numéricas. Producto **`be17e1b0c7fe5727b1119038bdf7be3e37679b69`**, tres líneas cambiadas por tres. Los tests existentes no se tocaron ni debilitaron.

- Rojo reproducido: **4 failed** en `tests/test_subitems1.py -k subitems_que_no_son_una_lista`.
- Verde tras el fix: **51 passed, 101 deselected in 3.39s** (SUBITEMS, MARIA subítems y EXCEL-2 montos/productos/cantidad).
- Negativo en archivo temporal: restituir sólo el mensaje genérico hace fallar los cuatro tests por la causa esperada; exit1 verificado. Log `/private/tmp/cdi-subitems-be17-negative.log`.
- La suite independiente previa sobre `0666881` terminó **5 failed, 1726 passed, 102 skipped, 2 xfailed**. Cuatro son esta regresión; el quinto es la prueba de ocho libros, que bajo cobertura dio normal400 a31.4s. Los verdes sin cobertura y las mediciones de23–25s no borran ese rojo. PM reproduce sólo el caso instrumentado para clasificarlo; no se aumentaron timeouts ni se excluyeron tests.
- No se repitió suite completa sobre `be17e1b` ni se ejecutó otro estrés desde Dev. No declarar CI/e2e ni pieza aceptada. Siguen pendientes la decisión del quinto rojo y las puertas posteriores sobre el producto resultante.
