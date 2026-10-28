# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## GUARDAR-2: entregada en `cef45ce`

| Qué | SHA |
|---|---|
| Candidato `2d930c5` (rama vieja, sobre `1cdfe49`), integrado sin rehacer | merge `9c4b482` |
| Negativos por dueño, SQLite y sabotajes | `5505220` |
| Negativos por dueño contra Postgres | `8356db9` |
| Merge de tu rama (`bb5be74`, sólo `docs/pm/` y `.claude/`) | `cef45ce` (lo que se entrega) |
| Informe | este commit |

Diff de revisión: `git diff 8e744a0..cef45ce -- . ':!docs/pm' ':!.claude'`
(5 archivos, +457 −5). **Archivo de producto: sólo `proyecto_maria/main.py`**
(+50 −5, del candidato; no le cambié una línea). D32 (b), sin migración.

**Suite en `cef45ce`: 3863 passed, 102 skipped, 2 xfailed, 0 rojos.**

**Nada para decidir.** EXCEL-3f sigue esperando tu veredicto: su informe
está en `0557f03` (`git show 0557f03:docs/pm/PARA-PM.md`). Si trae una
devolución, va antes que lo que sigue.

## Qué faltaba y qué hice

CIERRE-RETOMA, «Qué sigue», punto 2: «Faltan negativos explícitos por dueño
en ambos endpoints, Postgres descartable y puertas de integración sobre base
aceptada.»

- **Negativos por dueño, en los dos endpoints** (`/api/catalog/lookup` y
  `/api/ncm/sugerir`), en `tests/test_guardar2.py`:
  - `test_el_catalogo_de_otro_usuario_no_cambia_la_sim`: otro despachante
    tiene la SIM completa en el catálogo del mismo proveedor; al primero le
    queda su NCM de 8 dígitos (`cliente`/`historial`, `84714900`).
  - `test_el_historial_de_un_cliente_ajeno_no_se_usa`: con el `client_id`
    de otro despachante no aparece su historial (ni `veces_usado`); sin
    proveedor, el lookup da `ninguno`.
- **Postgres descartable:** Postgres 16.15 que ya trae el contenedor
  (instalado el 2026-10-22, no lo instalé yo), un cluster nuevo en `/tmp`
  escuchando sólo en `127.0.0.1:55432`, sin clave (`trust`), bases vacías,
  una por corrida. `scripts/testing/guardar2_postgres.py` suma el punto 5:
  los mismos dos negativos, con dos despachantes registrados de verdad.
- **Puertas sobre la base aceptada:** sobre `cef45ce`, que ya trae tu rama
  entera (abajo).

**Rojo antes del verde: por sabotaje, no real.** El producto ya filtraba
por dueño (`catalog_service._fetch_vendor_rows` y
`client_memory.lookup_client_memory`), así que los dos negativos nacen
verdes. Lo que demuestra que distinguen es sacar ese filtro: con cada uno
sacado, su caso se pone rojo, en SQLite y en Postgres.

**Un intento inválido, corregido:** la primera versión de Postgres usaba un
segundo `TestClient` para el otro despachante. Corre en otro bucle de eventos
y el pool de asyncpg devolvía 500/401, así que su «OK» no probaba nada. Ahora
hay un solo cliente y se cambia la cookie de sesión, sobre una base nueva.
Tampoco cuenta una primera corrida «saboteada» en Postgres cuyo patrón no era
único: el sabotaje no se aplicó. Las que valen están en la tabla.

## Puertas en `cef45ce`

| Puerta | Resultado |
|---|---|
| Suite completa (`pytest -q --no-cov --timeout=120`) | `3863 passed, 102 skipped, 2 xfailed, 93 warnings in 466.05s`, `exit=0` |
| `compileall -q proyecto_maria` | `exit=0` |
| `test_guardar2` + `test_guardar1` | `39 passed` |
| `guardar2.sh` (sobre `5505220`; desde ahí, sólo cambian merges de `docs/pm`) | 9 ROJO, `sabotajes con falla: 0`, `exit=0` |
| `guardar2_postgres.py` sin sabotaje, base `guardar2_cef45ce` | 16 OK, `fallas: 0`, `exit=0` |
| Postgres, sin el filtro por dueño del catálogo (a mano, base `guardar2_sab2`) | `FALLA \| el catálogo de otro despachante no cambia la SIM (('cliente', '84714900100D') [('historial', '84714900100D')])`, `fallas: 1` |
| Postgres, sin el filtro por dueño del historial (a mano, base `guardar2_sab3`) | `FALLA \| el historial de un cliente ajeno no se usa (('cliente', '84714900100D') [('historial', '84714900100D')])`, `fallas: 1` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido`, `exit=0` (base nueva, puerto 8771) |
| `ataque_aislamiento.sh` | `Bloqueado: 22 · Fugas: 0`, `PUERTA G3 PASADA`, `exit=0` (cubre clientes y descargas, no esta pieza) |

Los 9 rojos de `guardar2.sh`, copiados de la salida:

```
ROJO  | el autorrelleno vuelve a traer los 8 dígitos del cliente: dice «FAILED tests/test_guardar2.py::test_el_autorrelleno_trae_la_sim_del_proveedor»
ROJO  | la sugerencia vuelve a traer los 8 dígitos del cliente: dice «FAILED tests/test_guardar2.py::test_la_sugerencia_trae_la_sim_del_proveedor»
ROJO  | gana el proveedor aunque sea otra NCM: dice «FAILED tests/test_guardar2.py::test_con_otra_ncm_en_el_proveedor_gana_el_cliente»
ROJO  | gana el proveedor aunque no tenga la letra de control: dice «FAILED tests/test_guardar2.py::test_cual_gana[84714900-84714900100-84714900]»
ROJO  | gana el proveedor aunque el cliente no tenga 8 dígitos: dice «FAILED tests/test_guardar2.py::test_cual_gana[8471490010-84714900100D-8471490010]»
ROJO  | gana la SIM de otro producto parecido del proveedor: dice «FAILED tests/test_guardar2.py::test_la_sim_de_otro_producto_parecido_no_gana»
ROJO  | la SIM del proveedor sale tal como está guardada: dice «FAILED tests/test_guardar2.py::test_la_sim_del_proveedor_sale_en_la_forma_de_siempre»
ROJO  | el catálogo del proveedor de otro despachante cambia la SIM: dice «FAILED tests/test_guardar2.py::test_el_catalogo_de_otro_usuario_no_cambia_la_sim»
ROJO  | el historial de un cliente ajeno se usa: dice «FAILED tests/test_guardar2.py::test_el_historial_de_un_cliente_ajeno_no_se_usa»
```

## Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout --detach origin/claude/dev-tecnica
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_guardar2.py tests/test_guardar1.py   # 39 passed
PY=$(command -v python) scripts/testing/sabotajes/guardar2.sh               # 9 ROJO, «sabotajes con falla: 0»
# con un Postgres local y una base vacía (nunca el de producción):
python scripts/testing/guardar2_postgres.py postgresql://cdi@127.0.0.1:55432/<base vacía>   # 16 OK, «fallas: 0»
```

## No corrido

- **`/code-review high`, `/security-review` y los subagentes adversariales:**
  no corrieron. Los tres usan subagentes y no hay presupuesto hasta hoy a
  las 18:00 UTC. En su lugar releí a mano el diff de producto contra
  `8e744a0`. No encontré nada, pero eso no reemplaza una revisión
  independiente: la pieza toca lectura por dueño.
- `guardar2.sh` no se volvió a correr sobre `cef45ce`: entre `5505220` y
  `cef45ce` sólo entran `8356db9` (el script de Postgres) y tu merge de
  `docs/pm` y `.claude`.
- Los sabotajes de Postgres no están en un script: los hice a mano, uno por
  corrida, sacando la misma línea que los dos sabotajes nuevos de
  `guardar2.sh`.

## Riesgos

- La letra de control de la SIM del proveedor no se verifica: alcanza con
  11 dígitos y una letra (`_sim_position_error`, el mismo criterio que el
  TXT). Si el catálogo tiene una letra equivocada, la sugerencia del
  cliente la toma. Pasa igual en el resto del producto. No lo toqué.
- La SIM del proveedor gana sólo si la descripción guardada del cliente,
  normalizada, es la del catálogo (`producto_key`). Un producto con otra
  redacción queda con los 8 dígitos. Es lo que pide D32 (b) y está
  cubierto por `test_la_sim_de_otro_producto_parecido_no_gana`.
