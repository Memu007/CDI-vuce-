# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## GUARDAR-1 — entregada sobre `d6fe25f` (informe en el commit que sigue)

**Resultado:** guardar una operación con la SIM completa ya no da 500 en
Postgres, y el historial no puede tirar abajo el guardado. Rojo antes y verde
después contra un Postgres 16 local, y suite completa en verde. Sin migración.

| | SHA |
|---|---|
| producto | `01d5723`, `3135802`, `e08c920` |
| pruebas, script de Postgres y sabotajes | `191db69`, `6d918d8`, `d6fe25f` |
| CHANGELOG | `cabf090` |
| e2e de la CI (agregado del canal) | `aec4f15`: sólo `config/e2e_maria.js`. Va encima de `d6fe25f` con `cherry-pick`, sin nada de la devolución de EXCEL-2 |

**Agregado — la e2e de la CI (`aec4f15`).** `confirmReview` completa
`#f_fecha_emision` con `01/10/2026`. Sin esa línea, en mi rama: `E2E falló` en
`confirmReview` (`e2e_maria.js:131`). Con ella, `E2E MARIA OK: carga,
revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria
verificadas.` Lo corrí dos veces: en mi rama y en `d6fe25f` más `aec4f15`
(`git cherry-pick -n`), que es lo que se publicaría.

**Ojo al publicar:** mi rama ya tiene, después de `d6fe25f`, commits de la
devolución de EXCEL-2 que todavía no entregué. Para GUARDAR-1 van `d6fe25f` y
`aec4f15`, no la punta de la rama.

**Qué cambia:**
- **La operación primero:** la operación, sus ítems y el contador del plan se
  guardan en un commit. El historial del cliente va después, cada producto en
  su savepoint. Si un producto falla, se pierde sólo ese; si falla todo el
  historial, la operación ya quedó. La respuesta trae `historial_guardado`.
- **La forma que guarda el historial** (`ncm_para_historial`): lo que entra en
  la columna (10) queda igual. De la SIM completa se guarda el NCM de 8
  dígitos, que es lo mismo que ya guardaba «confirmar NCM» (`guardar-uso`).
- **Editar un producto** del cliente ya no corta la SIM a 10 caracteres (dejaba
  `8471490010`, que no existe): guarda los 8 dígitos y rechaza con 400 lo que
  no los tiene.
- **`/catalogo/productos/learn`** usa la misma forma, no da 500 por un
  producto malo y no cuenta lo que no guardó.
- **Otros datos del mismo guardado** que en Postgres también daban 500 y no
  guardaban nada: moneda de más de 3, origen de más de 50, fecha de inicio
  del cliente de más de 10, `grupo_id` que no es entero o se pasa de Integer, y
  el carácter NUL en cualquier texto. Los encontraron las revisiones.

## Decisiones

- **D32 — La sugerencia del cliente con 8 dígitos tapa la SIM del proveedor.**
  - Lo encontró la revisión Sonnet y lo reproduje con su camino. Antes de
    este arreglo, en producción la operación daba 500 y el historial quedaba
    vacío, así que la sugerencia salía del catálogo del proveedor, que guarda
    la SIM completa (String(20)). Ahora el historial del cliente tiene
    `84714900` y gana por prioridad (`/api/catalog/lookup`, `/api/ncm/sugerir`).
    La pantalla lo marca incompleto y hay que tipear la SIM.
  - Opciones:
    - (a) agrandar `client_product_history.ncm` a `VARCHAR(20)` y guardar la
      SIM completa. En Postgres agrandar un varchar no reescribe la tabla.
      Iría como función `_migrate_*` al arrancar, con su prueba contra
      Postgres. Para volver atrás alcanza con publicar el código anterior: la
      columna más ancha no lo molesta.
    - (b) dejar los 8 dígitos y que, si el proveedor tiene una SIM que empieza
      con esos 8, gane la del proveedor.
    - (c) dejarlo como está.
  - **Recomiendo (a):** es la única que guarda «la posición completa», como
    pedía el alcance. Es una migración: necesita tu visto bueno.

## Cómo reproducirlo

```bash
# Postgres local descartable (no el de producción); sale «fallas: 0»
python scripts/testing/guardar1_postgres.py postgresql://cdi@127.0.0.1:55432/<base vacía>
# con el código de antes (857d062) el mismo script da 6 FALLA (500, operación vacía)
PY=<venv>/bin/python scripts/testing/sabotajes/guardar1.sh d6fe25f   # «sabotajes con falla: 0» (12)
python -m pytest -q --no-cov tests/test_guardar1.py                  # 21 passed
```

## Puertas, sobre `d6fe25f`

| Puerta | Resultado |
|---|---|
| Suite tipo CI (venv limpio, deselects de ci.yml) | `1324 passed, 102 skipped, 10 deselected, 3 xfailed` |
| `guardar1_postgres.py` contra Postgres 16 local | 13 OK, `fallas: 0`; en `857d062`, `fallas: 6` |
| `sabotajes/guardar1.sh` | 12 de 12 en ROJO, `sabotajes con falla: 0` |
| `smoke_friccion.sh` | `OK · telemetría + alias session/state + by-cuit protegido` |
| `ataque_aislamiento.sh` | `Bloqueado: 22 · Fugas: 0`, «PUERTA G3 PASADA» |
| Sabotajes de piezas anteriores, sobre `d6fe25f` | 0 con falla: admin1, admin2, excel2, punta_a_punta1, rendimiento1 y 1b. Con patrones viejos (ROTO), que no son de esta pieza: excel1 (5) y maria1b (1), por los cambios de EXCEL-2, que arreglo en su devolución; cobro_mp1 (3), por el paso 2 de COBRO-MP-1, que arreglo al retomarla. |

**Revisiones:**

| Quién | Modelo y esfuerzo | Encontró | Qué hice |
|---|---|---|---|
| Adversario | Sonnet, alto | La sugerencia de 8 dígitos tapa la SIM del proveedor; contador del plan en otro commit (500 con la operación guardada); otros datos que dan 500; nadie se entera si falla el historial | D32; lo demás, arreglado con su rojo |
| Adversario | Opus, alto | Lo mismo del contador; la prueba no veía mover el contador al historial; `grupo_id`; editar aceptaba «ABC»; `learn` contaba lo que no guardaba | Arreglado con su rojo y sabotaje |
| `/code-review` | alto | Un producto malo se llevaba el historial de toda la operación; `learn` daba 500 por uno; `grupo_id` fuera de Integer; NUL en otros textos | Arreglado (savepoint por producto) con su rojo y sabotaje |
| `/security-review` | Sonnet, alto | Nada con confianza ≥ 8 (propiedad del cliente, origen de `client_id` y del dueño, SQL, datos expuestos) | — |

## Qué no corrí y riesgos

- **La pantalla no lee `historial_guardado`:** el aviso está en la respuesta,
  pero nadie lo muestra. Es de la pantalla (¿Dev 2?): lo dejo propuesto.
- **Siguen dando 500, como antes (no lo agrega esta pieza):**
  - números mal escritos en la operación (`"1,5"`, `"abc"`, `resumen.items: null`);
  - el límite del plan bajo dos guardados a la vez sale como 500 y no 402;
  - el catálogo del proveedor (`/api/catalog/{vendor}/productos`) con una
    descripción de más de 300 caracteres: pierde el lote entero, y la
    pantalla lo ignora;
  - `/api/ncm/guardar-uso` con un `vendor_name` muy largo responde `success`
    sin guardar.

  Son de otras rutas: si querés, tarea aparte.
- **Formas mezcladas en el historial:** las de 10 o menos quedan tal cual
  (`8471.49.00`) y `guardar-uso` guarda `84714900`. No rompe la sugerencia,
  que busca por descripción; sí parte el «NCM más usado» del cliente en dos.
  Venía de antes, y la D32 (a) lo puede ordenar.
- **`ClientService.update_product_history`** (`client_service.py`) no tiene
  quién la llame y escribe la columna sin la forma nueva: código muerto.
- **No corrí:** contra el Postgres de producción, nunca. La concurrencia sólo
  la cubre el contador; dos guardados a la vez del mismo cliente no los probé.

**Archivos de producto que toqué:**
- `proyecto_maria/main.py`: `save_client_operation`,
  `learn_client_catalogo_productos`, `update_client_catalogo_producto` y sus
  ayudantes;
- `proyecto_maria/services/client_memory.py`.

## COBRO-MP-1 — en pausa en `37d0efe` (sin entregar)

Pausada por GUARDAR-1. Los cuatro pasos tienen código y pruebas; falta
cerrarla:

- **Hecho:** pasos 1 y 3 (`3d3f712`), paso 2 con D29 b y sus tres
  condiciones (`2d51448`: suscripción contra el monto leído en Mercado Pago,
  links viejos contra el precio de hoy, rechazados visibles en
  `/dev/dashboard` → «Pagos de Mercado Pago no aplicados»), paso 4 con D30 a
  (`f5f06ee`: si el cobro o la suscripción no tienen la forma esperada, no se
  aplica nada y se loguea). Pruebas viejas que pagaban 30 000, en su commit
  (`90eff1f`).
- **D31:** la prueba con nombre de dos avisos a la vez está
  (`test_dos_avisos_del_mismo_pago_a_la_vez_se_aplican_una_sola_vez`), y
  `scripts/testing/cobro_mp1_postgres.py` lo mismo contra un Postgres 16
  local: 8 de 8 OK en `18a1850`; con el `IntegrityError` saboteado, FALLA.
- **Pruebas:** `tests/test_cobro_mp1.py`, 36 en verde en `37d0efe`.
- **Falta para entregar:** sabotajes de los pasos 2 y 4 en
  `scripts/testing/sabotajes/cobro_mp1.sh`, suite completa, revisión Opus y
  Sonnet (alto), CHANGELOG, el script de Postgres sobre el SHA final, e
  informe con los riesgos (D28: consultas a Mercado Pago con ids al azar;
  formato del cobro autorizado sin confirmar contra un aviso real).


## Sigo con

La devolución de EXCEL-2 (veredicto en `2034b85`, D27 a), sobre `3e6e63e` más
lo de ahora. Después, COBRO-MP-1.

Última vuelta: 2026-10-07
Contexto: el que mide la PM con get_session.

`/compact conservar: Dev 1 de CDI, rama claude/dev1-tecnica, PM principal
session_01B7FVQspcEHF7PqNv797wNM. GUARDAR-1 entregada sobre d6fe25f (D32 abierta:
agrandar client_product_history.ncm). Ahora: devolución de EXCEL-2 (6 puntos en
PARA-DEV.md, veredicto 2034b85, D27 a; arreglar también los patrones viejos de
scripts/testing/sabotajes/excel1.sh). Después COBRO-MP-1, en pausa en 37d0efe
(ver PARA-PM.md). Postgres local: /usr/lib/postgresql/16/bin, datos
/tmp/cdi-dev1/pg, puerto 55432, usuario cdi. venv /tmp/cdi-dev1/venv y venv-limpio;
suite con /tmp/cdi-dev1/suite8.sh (sed del SHA). Rutina de la PM
trig_01TvMmGfSLDfbcJrf66ZZ7YK. Compactar desde el 30 %. Hasta esfuerzo alto, sin
Fable; nunca main.`
