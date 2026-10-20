# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## DOC-1 — entrega provisional, no aceptada (2026-10-20)

Backend y subida implementados y probados; **sigue bloqueando la aceptación el
borrador de deshacer NCM (`lastSnapshot`)**, que puede restaurar productos de
otra operación al volver a esa pantalla. PM encargó su corrección a UI en un
clon aislado. No integrar ni publicar esta entrega como cierre de DOC-1.

| Pieza | SHA |
|---|---|
| Base PM autorizada | `1469102` |
| Producto: lector, guardas y estado de subida | `b5b6dec` |
| Casos y actualización de mocks válidos | `917594e` |
| Negativos DOC-1 aislados | `674379d` |
| Caso de rechazo levantado en worker | `378288e` |
| Adaptación de dos negativos MARIA-2b al retorno clasificado | `10bbe35` |

Rama local `codex/doc1-block-invalid-pdf`, clon `/private/tmp/cdi-doc1-dev`.
No push, merge a main ni publicación. Los cambios posteriores a `378288e`
son sólo el script de negativos: `git diff 378288e..10bbe35 -- proyecto_maria`
no muestra diferencias.

## Alcance real

- Ambas copias Gemini piden clasificación en la misma llamada, la conservan y
  rechazan clase ausente, desconocida, despacho, exportación y metadatos
  contradictorios. El rechazo dedicado no se traga, reintenta ni cae en el
  fallback. Una factura válida sin productos conserva clasificación y sigue
  dando el 400 existente de tabla vacía.
- La subida valida antes de intentar heurísticas opcionales; devuelve 422 con
  `code=documento_no_admitido`, sin ítems. Se cubre tanto respuesta inválida
  como excepción levantada dentro del worker.
- EC* explícita no pasa por generación de importación, sus avisos ni la
  función pura `generate_maria_txt`. No se cambió un campo del TXT válido ni
  el exportador.
- Subir B invalida datos/borrador local de A inmediatamente. Respuestas viejas
  de subida, autoasignación, catálogo y confirmaciones Excel no pisan B.
  Se conserva historial y preferencias; el rechazo ofrece elegir otra factura.
- UI fue construida por el subagente `dev_doc1_ui` con modelo/esfuerzo heredado;
  su arnés JS usa DOM/API falsos. Es autorrevisión, no aceptación independiente.

## Evidencia ejecutada

| Puerta | Resultado exacto / alcance |
|---|---|
| Rojo previo DOC-1 | `26 failed, 3 warnings in 2.90s` sobre producto base; falta conservación, rechazo y EC HTTP |
| Rojo previo generador puro | `3 failed, 26 deselected, 3 warnings in 0.23s` antes de la guarda EC del core |
| Focales lector, pesos, devolución, Gemini fallido, rendimiento, punta a punta, TXT y subítems | `352 passed, 2 xfailed, 10 warnings in 30.21s` |
| DOC-1 final, incluye excepción worker | `38 passed, 3 warnings in 0.36s` sobre `378288e` |
| UI sintética | `DOC-1 upload: 11 synthetic scenarios OK (state, rejection, races, client, catalog, draft, Excel).` |
| Negativos DOC-1 aislados | 3/3 rojos esperados: clasificación, servidor HTTP y generador puro; cada mutante corre en snapshot temporal |
| `compileall` y diff check | OK |
| Preflight aislado `378288e` | OK: checkout limpio, Python 3.12 heredado, sin `.env`, claves inventadas, servicios fake/loopback9, API única `127.0.0.1:19001`, `/health` y frontend 200, tablas SQLite temporales |
| Suite completa normal, cobertura por defecto, sobre `378288e` | `1564 passed, 102 skipped, 2 xfailed, 28 warnings in 393.02s (0:06:33)`; cobertura `50.53%` (mínimo 38%); `FIN SUITE exit=0` |
| Smoke backend local | `OK · telemetría + alias session/state + by-cuit protegido` |
| Negativos vigentes completos sobre `10bbe35` | MARIA-1a 10/10; MARIA-1c 4/4; MARIA-1d 8/8; MARIA-2 8/8; MARIA-3 30/30; MARIA-2b 6/6 |

Negativos vigentes adicionales: MARIA-4 empezó con base `41 passed` y cuatro
mutantes rojos, pero el proceso perdió su sesión al interrumpirse el entorno;
no hay cierre del script en el log y **no cuenta completo**. MARIA-5 de esa
cola no consta ejecutado. No se ejecutaron acá todos los sabotajes históricos
ni la e2e oficial con navegador.

PM comunicó revisión independiente de 38 casos DOC-1, 11 casos JS y recorrido
CUA sintético en `19002`: factura A admitida, despacho B rechazado, recarga sin
revivir A. Es evidencia de PM, no una corrida Dev adicional.

## Rojos diagnosticados y límites

- La primera focal amplia dio `4 failed, 337 passed, 2 xfailed`: tres mocks de
  éxito carecían de clasificación y el retorno vacío perdía metadatos. Se
  corrigieron sin debilitar aserciones; focal final arriba.
- Dos sabotajes MARIA-2b quedaron verdes porque mutaban un retorno terminal ya
  no recorrido por una factura vacía clasificada. Se movieron al retorno
  actual; los seis vuelven a fallar por su motivo esperado.
- El primer bind local 19001 y el primer smoke fallaron por restricciones de
  sandbox. Con permiso local escalado, los mismos controles pasaron; no se
  accedió a producción.
- Una suite diagnóstica sin cobertura arrancada antes del preflight fue
  detenida al estar disponible la corrida válida; no se usa como puerta.
- No se usaron PDFs/TXT ni datos privados. Lectura Gemini simulada: esto
  demuestra el contrato y las guardas, **no precisión real del modelo**.
  Falta futura comprobación de Emi con documentos permitidos.
- Entorno heredado Python 3.12: no se probó instalación limpia de dependencias.
- `/code-review` local no estuvo disponible: la herramienta expuesta sólo
  inspecciona checks de PR y no hay PR de esta pieza. La revisión independiente
  de PM sigue siendo necesaria.

## Reproducción acotada

Desde el clon y con Python del entorno indicado, servicios fake y claves
inventadas (nunca ejecutar contra producción):

```bash
rtk proxy /private/tmp/cdi-codex-pm-venv/bin/python -m pytest tests/test_doc1_documentos.py -o addopts= --timeout=120 -q
rtk proxy node tests/test_doc1_upload.js
rtk proxy /private/tmp/cdi-codex-pm-venv/bin/python scripts/testing/sabotaje_doc1.py
rtk proxy bash scripts/testing/sabotaje_maria2b.sh 10bbe35 /private/tmp/cdi-codex-pm-venv
rtk git diff 378288e..10bbe35 -- proyecto_maria
```

Logs externos, sin datos reales: `/private/tmp/doc1-focals2.txt`,
`/private/tmp/doc1-focused-final.txt`, `/private/tmp/cdi-doc1-suite/suite.log`,
`/private/tmp/doc1-smoke.txt`, `/private/tmp/doc1-sabotaje-maria2b-final.txt` y
`/private/tmp/doc1-sabotajes-lector.txt`. El arnés preflight reproducible quedó
fuera del repo en `/private/tmp/cdi-doc1-suite/preflight_and_suite.py`; comprueba
SHA y limpieza antes de correr, no usarlo después de cambiar HEAD sin fijar
explícitamente el SHA a verificar.

## Siguiente

PM decide integración del arreglo aislado de `lastSnapshot` y su revisión.
No hay una decisión comercial/de alcance nueva para Emi. DOC-1 permanece en
revisión, sin autoaceptación y sin publicación.

Última vuelta: 2026-10-20, 13:45 Argentina.
Contexto: ~55 %.
