# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PRESUPUESTO-CLIENTE-1 reentregada sobre la unión: `f45243a`

| qué | SHA |
|---|---|
| base (tu cabeza, ya traída con `merge` en `be52392`) | `64c39e9` |
| **entregado** | **`f45243aa6f7f29531571c376a1bdd084f04be416`** |
| producto, commits originales | `de176b1`, `db0f25a`, `4d30e9c`, `a9fb87f` |
| el merge que puso la llamada en el camino por `operacion_id` | `2b59f39` |
| pruebas sobre la unión | `2f3f51f`, `e937116`, `3936c24`, `f45243a` |
| pruebas originales | `f9d4c76`, `1345ca7`, `c3cca11`, `eeba405` |
| PRUEBA-LIMPIAR-1 (D164 a), entra con ésta | `5dd9a6e` |
| informe | el commit siguiente a `f45243a` |

**Resultado.** Pasar una operación a otro cliente suelta su link, también
cuando el guardado la encuentra por `operacion_id`. En la unión hay un solo
camino que encuentra una operación existente (`_operacion_del_usuario`), y la
llamada está ahí, una sola vez (`main.py:8171`; la función, `main.py:6336`).

- Tus cuatro pasos dan 404 en el GET público, en SQLite y en PG 16.
- El control sin pase sigue igual: borrar A deja los presupuestos en 0.
- Con el arreglo revertido, rojo en los dos motores (abajo).
- El link sigue si la operación se guarda en el mismo cliente, si recibe
  cliente por primera vez, o si el guardado falla (rollback).
- Los links de otras operaciones, del mismo dueño o de otro, no se tocan.

Producto de la pieza: **+10/−0**, sólo `proyecto_maria/main.py` (y la entrada
de `CHANGELOG.md`).

**Tres diferencias con lo que pediste, para que no las descubras vos:**

1. En `tests/test_datos1.py` y en el arnés PG el link se crea con el
   `share_quote` real (Tarifar en modo fake, sin red), no con una fila por
   SQL.
2. Tus cuatro pasos literales, con la fila por SQL, los corrí con un guion
   descartable que no está en el repositorio. Sólo en SQLite; su salida está
   en «Rojos y salidas copiadas». En PG no corrió: Emi cortó esa corrida.
   En PG la cubre el paso 6 del arnés.
3. El control sin pase del repositorio
   (`test_borrar_cliente_borra_sus_presupuestos_y_no_los_ajenos`, y el paso 1
   del arnés PG) parte de una operación guardada a mano, no de un MARIA
   generado. El guion descartable sí parte de un MARIA generado.

## Decisiones

**D163. Un link que se comparte mientras la operación pasa a otro cliente, o
mientras se borra su cliente.** La repito porque dijiste que la contestabas
sobre este SHA. Ahora tiene dos variantes.

`share_quote` lee la operación, después calcula los aranceles (llama a
Tarifar) y recién ahí inserta el link, sin bloqueo.

- **Variante 1 (la de antes):** mientras tanto, el mismo usuario guarda la
  operación en otro cliente desde otra pestaña. El link nuevo se inserta
  después del borrado y queda andando con el presupuesto armado para el
  cliente anterior.
- **Variante 2 (nueva, del adversario, reproducida en PG 16):** mientras
  tanto, el mismo usuario borra el cliente. `delete_cliente` borra los links
  y deja la operación sin cliente; el link nuevo se inserta después. Si más
  tarde guarda esa operación en B, el link sigue, porque «recibir cliente por
  primera vez» no lo suelta. Salida, con el `share` detenido a mano:
  «delete A (con share detenido): 200», «share: 200», «GET público tras
  borrar A: 200», «guardar en B: 200 True», «GET público tras pasar a B: 200
  ['TABLETA SINTETICA']». Control sin la carrera: 404 y 404.

Ninguna la introdujo este arreglo. `get_public_quote` no compara el cliente
del link.

- (a) Queda como riesgo bajo, sin código.
- (b) En `share_quote`, bloquear la operación y volver a leer
  `op.client_id` antes del insert.
- (c) Guardar `client_id` en el snapshot y que `get_public_quote` dé 404 si
  ya no coincide con el de la operación.

**Recomiendo (a).** Para que pase, el mismo dueño tiene que compartir y
mover o borrar a la vez, en dos pestañas. No cruza ninguna frontera de
permisos: el link lo arma y lo reparte ese mismo usuario. (b) agrega un
bloqueo en un endpoint que espera a un servicio externo. (c) cierra las dos
variantes y no bloquea nada, pero cambia el formato del snapshot y no cubre
los links ya emitidos. Si preferís cerrarlo, (c).

**D167. `/autocompact 200k` deja a esta sesión compactando cada 3 minutos.**
Medido en el registro de la sesión: hoy 33 compactaciones desde las 18:42
UTC, 14 entre las 20:21 y las 21:05. Con 200k la compactación salta a
~145k, y esta sesión arranca en 135k–140k después de compactar (~36k de
resumen y ~100k de carga fija, sin desglosar). Quedan ~5k por ciclo, y cada
compactación tarda 145 a 201 s. Ayer el arranque era 109k–122k. A las 21:06
UTC Emi puso 250k en esta sesión; desde entonces llegó a ~160k sin compactar.

- (a) «Eficiencia de chats» de `AGENTS.md` pasa a 250k.
- (b) Queda en 200k y Dev 2 sigue en una sesión nueva.
- (c) Queda como está.

**Recomiendo (a).** (b) ahorra sólo el resumen: una sesión nueva carga la
misma parte fija (esto lo calculo, no lo medí). Mi parte la corrijo igual:
los resúmenes venían copiando logs enteros; desde ahora citan este informe.

## Comandos copiables

Desde un worktree con su venv y las variables de las pruebas
(`DATABASE_URL=… DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares`):

```bash
python -m pytest -q --no-cov tests/test_datos1.py                 # 11 passed
PY=$(which python) scripts/testing/sabotajes/datos1.sh f45243a    # 20 ROJO, «sabotajes sin rojo: 0»
(unset DATABASE_URL; python scripts/testing/datos1_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/<base vacía>)   # «fallas: 0»

# el arreglo revertido: 2 failed, 9 passed (y «fallas: 2» en el arnés PG)
sed -i 's/^\(\s*\)await _soltar_link_de_otro_cliente(db, operation, client_id)$/\1pass/' proyecto_maria/main.py
python -m pytest -q --no-cov tests/test_datos1.py; git checkout -- proyecto_maria/main.py
```

La pieza sola sobre tu cabeza, para chequeo-6 (corrido tal cual: `producto
+10/−0`, `arnés +200/−24`, `avisos: 1`):

```bash
git worktree add -q --detach /tmp/pc1 64c39e9 && cd /tmp/pc1
git checkout -q f45243a -- tests/test_datos1.py scripts/testing/sabotajes/datos1.sh scripts/testing/datos1_postgres.py
git apply <<'DIFF'
diff --git a/proyecto_maria/main.py b/proyecto_maria/main.py
index fbf25f3..bf6115d 100644
--- a/proyecto_maria/main.py
+++ b/proyecto_maria/main.py
@@ -6297,6 +6297,15 @@ async def _operacion_del_usuario(db: AsyncSession, username: str, operacion_id:
     return result.scalars().first()
 
 
+async def _soltar_link_de_otro_cliente(db: AsyncSession, operation, client_id: str) -> None:
+    """Si la operación pasa a otro cliente, su link compartido se va, como al borrar el
+    cliente: es el presupuesto armado para el anterior. Sin commit: cae con el resto si falla."""
+    if operation.client_id not in (None, client_id):
+        await db.execute(
+            sa_delete(PublicQuoteModel).where(PublicQuoteModel.operation_id == operation.id)
+        )
+
+
 def _del_periodo(operacion, cuenta) -> bool:
     """Las regeneraciones que le quedaban a una operación de un período anterior no pasan a éste."""
     inicio, creada = cuenta.billing_period_started_at, operacion.created_at
@@ -8123,6 +8132,7 @@ async def save_client_operation(
             currency=str(data.get("currency") or "USD")[:3],
         )
         if operation is not None:
+            await _soltar_link_de_otro_cliente(db, operation, client_id)
             for campo, valor in campos.items():
                 setattr(operation, campo, valor)
             operation.extra = {**(operation.extra or {}), "resumen": resumen}
DIFF
git commit -qam pieza && python docs/pm/herramientas/chequeo-6.py 64c39e9 HEAD
```

## Rojos y salidas copiadas

- **Arreglo revertido, SQLite:** «FAILED
  tests/test_datos1.py::test_pasar_la_operacion_a_otro_cliente_borra_su_presupuesto»
  («AssertionError: (True, 200)», «assert 200 == 404»), «FAILED
  tests/test_datos1.py::test_borrar_el_cliente_anterior_no_deja_el_link_de_la_operacion_pasada»
  («AssertionError: assert 200 == 404»), «2 failed, 9 passed, 3 warnings in
  9.01s», `exit=1`.
- **Arreglo revertido, PG 16:** nueve `OK` y «FALLA | guardada en otro
  cliente, la operación pierde su link (200)», «FALLA | borrar el cliente
  anterior no la toca ni devuelve el link (200)», «fallas: 2», `exit=1`.
- **PG 16 sobre `f45243a`:** once `OK`, entre ellos «OK    | guardada en otro
  cliente, la operación pierde su link (200)» y «OK    | borrar el cliente
  anterior no la toca ni devuelve el link (200)»; «fallas: 0», `exit=0`.
- **Tus cuatro pasos literales, guion descartable, SQLite, sobre `f45243a`:**

```
== sqlite con pase
link antes: 200
pase a B: 200 True
borrar A: 200
GET publico sin login: 404
presupuestos, (cliente es B, sin cliente): (0, (True, False))
== sqlite sin_pase
link antes: 200
borrar A: 200
GET publico sin login: 404
presupuestos, (cliente es B, sin cliente): (0, (False, True))
```

## Sabotajes (`scripts/testing/sabotajes/datos1.sh`)

El script tiene 20 sabotajes y corrí los 20 sobre `f45243a`: **20 de 20
ROJO**, «sabotajes sin rojo: 0», `exit=0`. Los 12 primeros son de DATOS-1.
Éstos son los 8 de esta pieza, con el texto del log; todos anclan en código:

| Sabotaje | Dice |
|---|---|
| pasada a otro cliente, el link sigue andando, también al borrar el anterior | los dos `FAILED` de arriba, «AssertionError: (True, 200)», «assert 200 == 404» |
| pasada a otro cliente, sólo se borra uno de sus links | `test_pasar_…`, «AssertionError: (True, 200)», «assert 200 == 404» |
| borrar el cliente anterior suelta también la operación que ya pasó | `test_borrar_el_cliente_anterior_…`, «assert None ==» |
| se borra aunque siga en el mismo cliente | `test_pasar_…`, «AssertionError: (False, 200)», «assert 404 == 200» |
| se borra al recibir cliente por primera vez | `test_pasar_…`, «AssertionError: sin cliente antes», «assert 404 == 200» |
| el borrado queda aunque el guardado falle | `test_pasar_…`, «AssertionError: (True, 400)», «assert 404 == 200» |
| se borran también los links de otras operaciones | `test_pasar_…`, «AssertionError: otra operación del mismo cliente», «assert 404 == 200» |
| el guardado encuentra la operación de otro dueño | `test_pasar_…`, «AssertionError: assert '» «' != '» |

## Puertas

Todo sobre `f45243a`, desde base limpia (`rm -f test.db`), una puerta por vez.

| Puerta | Salida |
|---|---|
| suite completa (`--timeout=120`) | `5832 passed, 355 skipped, 3 xfailed, 104 warnings in 1086.03s (0:18:06)`, `exit=0` |
| `compileall -q proyecto_maria` | sin salida, rc=0 |
| golden (5 archivos) | `115 passed, 2 xfailed in 14.33s`, `exit=0`; `git status --short` vacío |
| `tests/test_datos1.py` | `11 passed, 3 warnings in 9.28s`, `exit=0` |
| arnés PG 16 (`datos1_postgres.py`) | `fallas: 0`, `exit=0` |
| sabotajes `datos1.sh` | 20 ROJO, `sabotajes sin rojo: 0`, `exit=0` |
| `smoke_friccion.sh` (app en ENVIRONMENT=test, SQLite) | `==> OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido`, `exit=0` |
| `ataque_aislamiento.sh` | `Bloqueado: 47   ·   Fugas: 0   ·   Sin probar: 0`, `✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.`, `exit=0` |
| `e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.`, `exit=0` |

Los 355 salteados: 234 de `test_excel3` y 11 de `test_excel2d` (sin `xlwt`
en este entorno), 28 de `test_backup1a` («sin Postgres 16 local: correr con
scripts/testing/con_pg16.sh») y 82 viejos en otros siete archivos. Son 20 más
que en `eeba405` (335): 11 de `test_excel2d` y 9 de `test_backup1a`, que
vinieron con la unión. El motivo de esos 39 lo leí con `-rs`; el de los 234
de `test_excel3` no lo releí en esta corrida.

### chequeo-6, la pieza sola (la receta de arriba)

```
chequeo-6 64c39e9..HEAD: avisos para mirar, no un veredicto
producto +10/−0
arnés +200/−24
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12211 → 12221
  AVISO creció una función de más de 150: proyecto_maria/main.py:8091 save_client_operation 152 → 153, 1 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 1
```

AVISO de `save_client_operation`: la rama nueva va en la función aparte. La
función larga sólo suma la llamada. Partirla va a la cola de limpieza.

### chequeo-6, la unión entera (`64c39e9..f45243a`)

Es la suma de las piezas aceptadas sin integrar que entran con ésta (110
commits propios), no esta pieza. Por eso las 200 netas y el AVISO de
`register`, que no es de esta pieza: ésta toca sólo los dos trozos de arriba.

```
chequeo-6 64c39e9..f45243a: avisos para mirar, no un veredicto
producto +400/−200
  AVISO producto suma 200 líneas netas: el informe dice por qué (§6: más de 20)
arnés +2559/−183
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/catalog_service.py: 636 → 732
  proyecto_maria/core/despacho_lector.py: 902 → 900
  proyecto_maria/core/maria_generator.py: 2341 → 2391
  proyecto_maria/core/maria_generator_export.py: 320 → 298
  proyecto_maria/core/tarifar_connector.py: 525 → 526
  proyecto_maria/database/models.py: 617 → 617
  proyecto_maria/main.py: 12211 → 12270
  AVISO creció una función de más de 150: proyecto_maria/main.py:3404 register 209 → 210, 1 en su propio cuerpo (§6: lo nuevo va aparte)
  AVISO creció una función de más de 150: proyecto_maria/main.py:8127 save_client_operation 152 → 153, 1 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/pdf_extractor.py: 2893 → 2890
  proyecto_maria/services/client_memory.py: 305 → 308
  proyecto_maria/static/v2/paises_maria.js: 33 → 47
  proyecto_maria/static/v2/screens/catalogo.js: 402 → 403
  proyecto_maria/static/v2/screens/finalize.js: 1477 → 1484
  proyecto_maria/static/v2/screens/ncm.js: 2350 → 2351
avisos: 3
```

## Hallazgos

| Quién | # | Sev. | Hallazgo | Qué hice |
|---|---|---|---|---|
| adversario-sonnet-alto (Sonnet, alto) | A1 | Media | Un `share_quote` en vuelo durante `delete_cliente` deja un link vivo; un guardado posterior en B no lo suelta | Reproducido en PG 16. No lo introduce el arreglo. Es la variante 2 de D163 |
| ídem | A2 | Baja | Cambiar el borrado de `delete_cliente` para que borre sólo los links de la primera operación deja `tests/test_datos1.py` en 11 passed | Reproducido. Hueco de prueba de DATOS-1, no de esta pieza: propuesta para la cola |
| ídem | — | — | «No encontré un camino que haga fallar la aceptación como la pediste» | — |
| `/code-review high` (revisores con el modelo de la sesión) | CR1 | Baja | `share_quote` sin bloqueo frente a un pase o un borrado | D163 |
| ídem | CR2 | Media | Guardar una operación existente con un cuerpo mínimo pisa `source`, `currency`, `total_value` y `extra.resumen` | Vino con la unión, no con esta pieza. Leído, no corrido. Riesgo |
| ídem | CR3 | Baja | Dos sabotajes idénticos | Arreglado en `f45243a` |
| ídem | CR4 | Baja | Arnés PG: clientes creados sin mirar el status; un `[0][0]` que podía dar IndexError | Arreglado en `f45243a` |
| ídem | CR5 | Baja | El caso nuevo deja un TXT en `data/descargas` | Lo hacen 45 archivos de `tests/` que generan un MARIA. Riesgo, propuesta para la cola |
| ídem | CR6 | Baja | Ayudantes y un ítem repetidos en el arnés | Arreglado en `f45243a` |
| ídem | CR7 | Baja | El arnés PG importa `_pedido`, privado de un módulo de pruebas | Queda. Riesgo |
| ídem | CR8 | Baja | Tres sabotajes viejos de DATOS-1 anclan en comentarios | Es de D149: va con esa pieza |
| revisión de seguridad (a mano, yo) | — | — | Sin hallazgos con confianza ≥ 0,8. Ningún camino deja que un usuario borre o conserve el link de otro | — |

Las severidades de CR son mi lectura; los revisores no reprodujeron ninguno.
La revisión de seguridad no fue independiente: `/security-review` arma el
diff de toda la rama (1,5 MB), así que leí los dos trozos y quién los llama.

## Riesgos y lo no corrido

- A2, CR2, CR5, CR7 y CR8 de la tabla.
- Los links que ya hubieran quedado vivos antes del arreglo no se limpian
  solos. No sé si hay alguno en producción: no la miré.
- El GET público no manda `Cache-Control` (nota del adversario, sin
  reproducir).
- El arranque del PG 16 local para la corrida que Emi cortó tardó más de lo
  habitual. No diagnosticado; el servidor quedó apagado.
- `f45243a` quedó subido a las 21:07 UTC, antes de este informe: lo pidió el
  aviso automático de commits sin subir.
- **No corrido:** tus cuatro pasos literales en PG (corte de Emi; ver
  arriba); el guion descartable con el arreglo revertido; los sabotajes de
  otras piezas; CR2.

Archivo de producto tocado: `proyecto_maria/main.py`.

## Sigue

Sin esperar el veredicto: el arnés de pantalla del 402
(`tests/despacho1c_pantalla.js`), con sus dos sabotajes y el patrón de
`despacho1c`. Después D149 (a) y D145 (a).

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 64c39e9), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. PRESUPUESTO-CLIENTE-1 reentregada en f45243a (informe en el commit siguiente), esperando veredicto; D163 y D167 abiertas. Sigue el arnés de pantalla del 402, después D149 (a) y D145 (a). Próxima D libre: D168. Los detalles de la entrega están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
