# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ENTRADAS-4 (D117 a): **entregada** en `6baddb5` (2026-11-08)

Base `7f6862b`. El único campo `Form` de texto de la app que va a la base era
`cliente_id` de `/upload_excel_v2/`, y con un NUL daba 500 en Postgres. Ahora
es `TextoCodificable`, como los demás textos: el NUL se cambia por «�», el
cliente no se encuentra y el Excel se lee sin su mapeo (200).

Para que un campo nuevo no vuelva a abrir el hueco, `tests/test_entradas4.py`
(corre en la CI) recorre todas las rutas con la app arrancada y falla si hay
un campo `Form` de texto sin `_guardable_en_pg`. Mira también dependencias,
modelos como `Form`, routers y montajes. La sonda contra Postgres mide el 200
con NUL en cada campo de su tabla, y falla si la app tiene un campo que no
está en la tabla.

| SHA | qué |
|---|---|
| `e285386` | fix: `cliente_id` de `/upload_excel_v2/` pasa por `_guardable_en_pg` + CHANGELOG |
| `609d57f` | test: sonda contra Postgres con la familia de campos como datos, y sabotajes |
| `003acc7` | test: la búsqueda va a un test de pytest, que corre la CI; ve dependencias, modelos y routers |
| `6baddb5` | test: la búsqueda corre con la app arrancada (hay routers que se montan en el lifespan) |

`producto +1/−1`.

**Nada para decidir.** Un supuesto reversible:

- Un `cliente_id` con NUL se limpia y se trata como un cliente que no existe:
  200 sin mapeo, igual que hoy con un id inexistente. `/code-review` propuso
  un 422. No lo hice: un id real es un UUID y nunca trae NUL, y la subida ya
  se comporta así con cualquier id que no es del usuario.

## Riesgos

- `_get_owned_client` no tiene guarda propia: la protección está en el tipo
  del campo. Si otra ruta le pasa un texto sin `TextoCodificable`, vuelve el
  500. Hoy no hay otra ruta con `Form` que lo llame; el test de la CI avisa
  si aparece un `Form` sin guarda, pero no un parámetro de query o de ruta.
- La búsqueda depende de arrancar la app: `admin_router` y `quote_router` se
  montan en el lifespan. Si un router se montara después de arrancar, el
  test no lo vería.
- Un `Form` de lista (`list[str]`) se detecta, pero la sonda mandaría un solo
  valor. Hoy no hay ninguno.
- Para la cola de limpieza (propuesta): el arnés de sabotajes y los helpers
  de `*_postgres.py` (crear y borrar la base, registrar usuario, `chequear`)
  están copiados entre piezas.

## Hallazgos de la autorrevisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| adversario | Sonnet alto | la búsqueda no veía modelos como `Form`, `Form` en `Depends`, routers ni montajes | `003acc7` + sabotajes 3 y 4 |
| adversario | Sonnet alto | los routers del lifespan no existían al buscar | `6baddb5` + sabotaje 5 |
| adversario | Sonnet alto | la sonda es manual, la CI no la corre | `003acc7`: la búsqueda va a `tests/` |
| adversario | Sonnet alto | el sabotaje 2 ejerce un solo caso | sabotajes 3, 4 y 5 |
| adversario | Sonnet alto | `list[str]` se manda con un solo valor | riesgo, arriba |
| `/code-review` | high | la sonda aceptaba cualquier `<500` | `003acc7`: exige 200 |
| `/code-review` | high | `Form` en sub-dependencias de `Depends` | `003acc7`: recursivo |
| `/code-review` | high | `tipo is str` no veía subclases de `str` | `003acc7`: `issubclass`, sin `Enum` |
| `/code-review` | high | la CI no corría la búsqueda | `003acc7` |
| `/code-review` | high | limpiar en silencio el `cliente_id`; propone 422 | no: supuesto, arriba |
| `/code-review` | high | `_get_owned_client` sin guarda propia | riesgo, arriba |
| yo | — | el sabotaje del router salía verde (`sabotajes con falla: 1` en `003acc7`) | `6baddb5` |

El adversario revisó hasta `609d57f`. Descartó, probándolos: filename con
NUL real en el multipart (200, 200, 200 y 400 por extensión en las cuatro
rutas de subida), `use_mapping` con NUL (422) y NUL dentro de CSV o XLSX (no
llega a `column_mapping`). No probó `.xls` con NUL en un encabezado.

## Puertas

Todas sobre `6baddb5`, desde worktree limpio, una a la vez; logs en el scratchpad.

| puerta | salida exacta |
|---|---|
| `compileall -q proyecto_maria` | `compileall 0` |
| suite, SQLite (`ENVIRONMENT=test`, `--timeout=300`) | `5215 passed, 335 skipped, 3 xfailed, 94 warnings in 1035.09s`, `SALIDA suite_mia 0` |
| suite como la CI (`ENVIRONMENT=testing`, sin `DATABASE_URL`) | `5215 passed, 335 skipped, 3 xfailed, 94 warnings in 1014.35s`, `SALIDA suite_ci 0` |
| `tests/test_entradas4.py` | `1 passed` |
| sonda contra Postgres local | `OK    \| campos Form de texto: [('/upload_excel_v2/', 'cliente_id')]`, `OK    \| NUL en cliente_id de /upload_excel_v2/: 200 …`, `fallas: 0` |
| sabotajes `entradas4.sh` | 5 `ROJO`, `sabotajes con falla: 0`, `salida 0` |
| grep de historia de §6 | vacío |

Sabotajes, copiado del log:

```
BASE  | en verde
ROJO  | el cliente del Excel llega con su NUL a la base: «campos Form de texto sin _guardable_en_pg: [('/upload_excel_v2/', 'cliente_id')]» «FALLA | NUL en cliente_id de /upload_excel_v2/: 500»
ROJO  | un campo Form de texto nuevo en la ruta: «campos Form de texto sin _guardable_en_pg: [('/upload_excel_v2/', 'nota')]» «FALLA | campos Form de texto:»
ROJO  | un campo Form de texto en una dependencia: «campos Form de texto sin _guardable_en_pg: [('/upload_excel_v2/', 'nota')]»
ROJO  | un modelo de texto como Form: «campos Form de texto sin _guardable_en_pg: [('/sabotaje/', 'datos')]»
ROJO  | un campo Form de texto en un router: «campos Form de texto sin _guardable_en_pg: [('/api/quotes/sabotaje', 'nota')]»
sabotajes con falla: 0
salida 0
```

El primero es el rojo sin el arreglo: `cliente_id` vuelto a `str` da 500
contra Postgres y el test de la CI lo nombra.

No corrí `smoke_friccion.sh` ni `ataque_aislamiento.sh`. La pieza cambia el
tipo de un campo de una ruta, y lo que hace esa ruta con el NUL lo mide la
sonda contra Postgres. No toca sesión ni permisos.

chequeo-6, entero:

```
chequeo-6 7f6862b..6baddb5: avisos para mirar, no un veredicto
producto +1/−1
arnés +266/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12060 → 12060
avisos: 0
```

## Comandos

```bash
git fetch origin claude/dev-maria && git checkout 6baddb5
<venv>/bin/python -m pytest -q --no-cov tests/test_entradas4.py   # 1 passed
# las dos siguientes necesitan un Postgres local que deje crear bases:
env -u DATABASE_URL <venv>/bin/python scripts/testing/entradas4_postgres.py postgresql://cdi@127.0.0.1:55432/postgres   # «fallas: 0»
PY=<venv>/bin/python PG_URL=postgresql://cdi@127.0.0.1:55432/postgres scripts/testing/sabotajes/entradas4.sh 6baddb5   # 5 ROJO, «sabotajes con falla: 0»
```

## Archivos de producto tocados

`proyecto_maria/main.py`, `CHANGELOG.md`.

Sigo con SUFIJOS-2+SEGURO-1.

/compact conservar: Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi), rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message next. ENTRADAS-4 entregada en 6baddb5 (base 7f6862b). Próxima D libre D118. Sigue SUFIJOS-2+SEGURO-1, después SEGURO-2, EMAIL-1, CONEXIONES-1, OBSERVABILIDAD-1, ORG-1+D40 y D102. Corte de rutinas 2026-11-08 15:50 UTC. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; TXT y proforma reales nunca en el repo.
