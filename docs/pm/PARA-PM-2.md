# Candidato local Fase 1 — informes preservados

Integración sin cambios nuevos de producto. Informes de las dos entregas, con sus límites originales:

# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## DOC-1 — implementación entregada a revisión PM (2026-10-20)

Backend, subida y protección de deshacer NCM implementados y probados.
**El bloqueante `lastSnapshot` quedó corregido**: cada borrador de deshacer
pertenece a su estado de operación y no puede reemplazar otra operación.
Sin bloqueante conocido de implementación; la aceptación independiente,
integración y publicación siguen en manos de PM/Emi.

| Pieza | SHA |
|---|---|
| Base PM autorizada | `1469102` |
| Producto: lector, guardas y estado de subida | `b5b6dec` |
| Casos y actualización de mocks válidos | `917594e` |
| Negativos DOC-1 aislados | `674379d` |
| Caso de rechazo levantado en worker | `378288e` |
| Adaptación de dos negativos MARIA-2b al retorno clasificado | `10bbe35` |
| Informe provisional previo | `e148343` |
| Protección de deshacer NCM (origen revisado `565b6aa`) | `c2d41b4` |
| Casos NCM undo (origen revisado `e45e80e`) | `637758c` |
| Registro del cambio de NCM en changelog | `380bb95` |

Rama local `codex/doc1-block-invalid-pdf`, clon `/private/tmp/cdi-doc1-dev`.
No push, merge a main ni publicación. Después de `378288e` sólo cambiaron scripts/documentación y la protección JS
de NCM. `git diff 378288e..380bb95 -- "*.py"` no muestra diferencias. Por eso
no se repitió la suite Python completa; sí los 38 focales y los 15 escenarios JS
sobre la integración final.

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
- Deshacer las cuatro acciones NCM masivas conserva la operación dueña: una
  nueva subida, carga manual o simulada invalida el borrador previo, mientras
  que deshacer dentro de la misma operación continúa funcionando.
- UI fue construida por el subagente `dev_doc1_ui` con modelo/esfuerzo heredado;
  su arnés JS usa DOM/API falsos. Es autorrevisión, no aceptación independiente.

## Evidencia ejecutada

| Puerta | Resultado exacto / alcance |
|---|---|
| Rojo previo DOC-1 | `26 failed, 3 warnings in 2.90s` sobre producto base; falta conservación, rechazo y EC HTTP |
| Rojo previo generador puro | `3 failed, 26 deselected, 3 warnings in 0.23s` antes de la guarda EC del core |
| Focales lector, pesos, devolución, Gemini fallido, rendimiento, punta a punta, TXT y subítems | `352 passed, 2 xfailed, 10 warnings in 30.21s` |
| DOC-1 final, incluye excepción worker | `38 passed, 3 warnings in 0.36s` sobre `378288e`; tras integrar JS: `38 passed, 3 warnings in 0.73s` sobre `637758c` |
| UI sintética integrada | `DOC-1 upload: 11 synthetic scenarios OK (state, rejection, races, client, catalog, draft, Excel).`; `DOC-1 NCM undo: 4 synthetic scenarios OK.` sobre `637758c` |
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

PM comunicó revisión independiente de 38 casos DOC-1, 11 casos JS y los
4 casos NCM undo del candidato aislado antes de autorizar la integración, y recorrido
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
rtk proxy node tests/test_doc1_ncm_undo.js
rtk proxy /private/tmp/cdi-codex-pm-venv/bin/python scripts/testing/sabotaje_doc1.py
rtk proxy bash scripts/testing/sabotaje_maria2b.sh 10bbe35 /private/tmp/cdi-codex-pm-venv
rtk git diff 378288e..380bb95 -- "*.py"
```

Logs externos, sin datos reales: `/private/tmp/doc1-focals2.txt`,
`/private/tmp/doc1-focused-final.txt`, `/private/tmp/doc1-integrated-focused.txt`, `/private/tmp/cdi-doc1-suite/suite.log`,
`/private/tmp/doc1-smoke.txt`, `/private/tmp/doc1-sabotaje-maria2b-final.txt` y
`/private/tmp/doc1-sabotajes-lector.txt`. El arnés preflight reproducible quedó
fuera del repo en `/private/tmp/cdi-doc1-suite/preflight_and_suite.py`; comprueba
SHA y limpieza antes de correr, no usarlo después de cambiar HEAD sin fijar
explícitamente el SHA a verificar.

## Siguiente

No quedan decisiones de alcance ni bloqueantes conocidos de implementación.
PM revisa la entrega integrada y prepara la PR hacia su rama; esto no autoriza
fusionar a main ni publicar. No se ejecutó la puerta oficial completa de
navegador; la evidencia JS y CUA sintética descrita no la reemplaza. No se
afirma aceptación ni precisión de Gemini real.

Última vuelta: 2026-10-20, 13:48 Argentina.
Contexto: ~58 %.


---

# Dev 2 → PM

## MARIA-5d — bruto de una unidad con kg y bruto explícito de la línea

**Resultado: producto y focales terminados; aceptación pendiente de las puertas no corridas.** Rama local `codex/maria5d-unit-kg`, base `d22ff1a`. Producto `b3fd518` y `8b8b789`; pruebas `abe05ae`, `67d18a8`, `eff9dea`; changelog `000a74d`. SHA completo probado: `eff9dea`.

- «Peso bruto unit (kg)», «Gross weight unit (kg)» y «Unit gross weight» conservan el bruto unitario: 10 × 3 kg llega por upload y genera `QARTKGRNET=30.000`, con mapeo automático o guardado.
- La devolución PM sobre «Unit gross weight per line» y «Unit gross weight line» se corrigió en la misma guarda: 30 kg / 10 unidades conserva 30 kg en la línea, sin multiplicarlo a 300. Neto conserva prioridad; bruto total/plural conserva división.

## Evidencia y reproducción

```bash
# Desde esta rama; entorno inventado descrito abajo.
/private/tmp/cdi-codex-pm-venv/bin/python -m pytest -q --no-cov tests/test_maria5d.py tests/test_maria5d_unit_kg.py tests/test_maria5_peso_excel.py tests/test_devolucion2_maria5_ncm.py tests/test_generar_maria_txt.py tests/test_maria_subitems.py
bash scripts/testing/sabotaje_maria5d.sh eff9dea /private/tmp/cdi-codex-pm-venv
```

La suite y el preflight quedaron en `/private/tmp/cdi-maria5d-suite/suite.log`. No repetir para cerrar esta entrega.

| Puerta | Resultado |
|---|---|
| Rojo inicial sobre base, informado por la PM | `6 failed, 7 passed` |
| Rojo de devolución inglesa, antes de `8b8b789` | `2 failed, 4 passed, 9 deselected` |
| Focales sobre producto `8b8b789` (148 casos; últimos commits sólo script) | `148 passed, 3 warnings in 10.97s` |
| Sabotaje `eff9dea` | base `80 passed`; `OK: los 11 sabotajes dan rojo por la razón esperada` |
| Suite completa `eff9dea`, preflight OK | `1570 passed, 102 skipped, 2 xfailed, 28 warnings in 378.14s`; cobertura `50.47%` (mínimo `38%`); `FIN SUITE exit=0` |

Focales: `test_maria5d.py`, `test_maria5d_unit_kg.py`, `test_maria5_peso_excel.py`, `test_devolucion2_maria5_ncm.py`, `test_generar_maria_txt.py`, `test_maria_subitems.py`. Incluyen referencias anonimizadas de MARIA; no se usaron documentos privados.

Entorno: Python 3.12.8 y venv heredado `/private/tmp/cdi-codex-pm-venv` (NO instalación limpia de requirements), claves inventadas, conectores fake, endpoints de dólar/ARCA en loopback cerrado, SQLite temporal. Preflight verificó API propia en localhost:18982, health, frontend, tablas y checkout limpio. Primer intento de bind bloqueado por sandbox; reejecutado con permiso local. Corrida de suite anterior en `000a74d` interrumpida al llegar devolución PM: no cuenta como resultado. Corrida de sabotaje anterior invalidada por desajuste de patrón/SHA durante intervención: reemplazada por 11/11 sobre `eff9dea`.

## Pendientes y límites

- E2E y las tres pantallas: **no corridas**. No se operó navegador mediante shell.
- Kit SIM real: **no corrido**. Sin publicación ni push, según instrucción actual PM.
- Sabotaje EXCEL-1 histórico «mapeo guardado deja afuera lo detectado»: mutar `elegido = g or d` a `elegido = g` deja el test señalado verde (`1 passed`) tanto en base `d22ff1a` como en entrega `000a74d`. `_mapeo_efectivo` tiene AST idéntico entre base y `eff9dea`. Es una carencia de prueba anterior, no una regresión de esta pieza; no se amplió alcance para corregirla.

Autorrevisión del diff contra base: helper de bruto, pruebas sintéticas, sabotajes y changelog; sin cambios de exportación ni otros clasificadores.

**D1.** Mantener pendiente aceptación/publicación hasta completar e2e y pantallas. Recomendación: verificar esas puertas en el entorno habilitado, sin tocar producción.

Última vuelta: 2026-10-20 11:42 UTC
Contexto: ~50 %
