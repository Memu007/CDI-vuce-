# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CATALOGO-3 (devolución 973c489) entregada en e81b961 (base b7c4c85)

Para ver sólo esta vuelta: `git diff b7c4c85..e81b961`. El producto cambia
sólo en `proyecto_maria/services/client_memory.py` (y `CHANGELOG.md`).

| SHA | Qué |
|---|---|
| 53ac893 | fix: ante un empate gana el texto idéntico y después el último confirmado |
| a2f77ee | test: empates en SQLite, Postgres y sabotajes |
| 3f68668 | fix: el texto idéntico no distingue mayúsculas y la misma hora no la decide el id |
| 1e81a30 | test: mayúsculas, el mismo texto con dos NCM y la misma hora |
| 1dca33e | fix: el texto idéntico se compara contra la clave guardada |
| e81b961 | test: la fila vieja con otro espaciado, los dos órdenes y cada guardado comprobado |
| (siguiente) | docs: este informe |

**Resultado.** Las tres reglas quedan cumplidas, en SQLite y en PG; con el
arreglo revertido falla alguna siempre, en los dos motores (rojos abajo).
Nada para decidir: no hay D nuevas. Próxima D libre: **D163**.

- **Regla 1, texto idéntico.** Ante un empate de parecido gana la fila cuya
  clave guardada (`row.clave`) es la clave del texto buscado con el NCM de esa
  fila (`identidad_del_producto`, la misma función que la escribe). Es lo que
  pediste: NFC y sin distinguir mayúsculas. Se compara contra la clave
  guardada y no contra la descripción, porque una fila escrita por una
  versión anterior con otro espaciado («Cable  2,5mm2») tiene la misma clave
  y otra descripción: comparando descripciones perdía (es el rojo de 1e81a30).
- **Regla 1 con varias filas idénticas y regla 2.** Gana la de `ultima_vez`
  mayor; una fila sin fecha pierde contra una con fecha.
- **Regla 3, determinismo.** Si además coinciden en la hora, decide el
  contenido de la fila (NCM, descripción) y recién después el id. El
  resultado ya no depende del orden en que la base devuelve las filas.
- `client_memory.py:283-295`. Se sacó el bucle de «la primera de mayor
  puntaje»; producto +12/−9 (chequeo-6 abajo).

## Lo demás de la devolución

- **D160, D161, D162:** (a) aplicadas; no requieren código nuevo, el
  comportamiento entregado en ec0092a ya era (a).
- **Corrijo:** SUR→SR es **Surinam (232)**, no Sudáfrica. El supuesto
  reversible de la entrega anterior estaba mal escrito; el código no cambia.
- **Choque de la migración:** a la lista de publicar. Si el primer arranque
  dice que N filas quedan por un choque y N > 0, se frena antes de que
  alguien confirme: con el choque, el texto exacto lee la otra fila y al
  confirmarlo pisa su NCM, origen y descripción.
- **Salteados, 335 contra 101.** De mis 335, **234 son de
  `tests/test_excel3*`**, que se saltean porque en mi venv no está `xlwt`
  (`pytest.importorskip`); 335 − 234 = 101, que es lo tuyo. Otros 19 son de
  backup1a (sin binarios de PG 16 en el PATH de la suite) y el resto son
  saltos fijos del código. El total coincide porque los tests salteados
  igual se cuentan.
- **Riesgos que no pedís arreglar**, quedan anotados tal cual: «1½» contra
  «1 1/2» (0,67); orígenes de cifras («212» da US, D158); dos versiones
  escribiendo claves a la vez; recorte de espacios cuadrático en JS y avisos
  sin tope; `main.py:8244` y `8844` guardan el origen crudo (ORIGEN-2);
  descripciones largas que difieren en potencia y modelo sugieren el mismo NCM.

## Comandos copiables

Desde un worktree en e81b961, con su venv y las variables de las pruebas
(`DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares`):

```bash
python -m pytest -q --no-cov tests/test_catalogo3.py -k empate        # 14 passed
git worktree add /tmp/rev b7c4c85 && cp tests/test_catalogo3.py /tmp/rev/tests/ && (cd /tmp/rev && python -m pytest -q --no-cov tests/test_catalogo3.py -k empate)   # 13 failed, 1 passed
(unset DATABASE_URL; python scripts/testing/catalogo3_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/postgres)            # «todo OK»
(unset DATABASE_URL; python scripts/testing/catalogo3_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/postgres b7c4c85)    # FALLA en los tres empates
PY=$(which python) scripts/testing/sabotajes/catalogo3.sh e81b961     # 50 de 50 ROJO, «fallas: 0»
```

## Rojos copiados (con el arreglo revertido)

Pruebas de e81b961 sobre el producto de b7c4c85 (sin ningún arreglo) y de
1e81a30 (sin el último).

- **SQLite, b7c4c85:** «13 failed, 1 passed, 90 deselected in 7.55s».
  Los 8 de texto idéntico dicen «assert ['84714900', '84714900'] ==
  ['73181500', '84714900']»; los 5 de última confirmada «At index 2 diff:
  '84714900' != '73181500'». El que pasa es el de la misma hora: con la base
  vieja depende del orden en que SQLite devuelve las filas, y en 3 corridas
  pasó 1. Por eso el rojo «siempre» lo dan los otros 13, que no dependen del
  orden.
- **SQLite, 1e81a30:** «1 failed, 13 passed, 90 deselected in 7.36s»:
  «FAILED tests/test_catalogo3.py::test_ante_un_empate_gana_el_texto_identico[Cable 2,5mm2-Cable 2,5mm\xb2-None-Cable  2,5mm2-False]»,
  «assert ['84714900', '84714900'] == ['73181500', '84714900']».
- **PG 16, b7c4c85:** salida=1, FALLA en los tres chequeos de empate:
  identico alterna `['73181500','73181500']` y `['84714900','84714900']`;
  ultima da 5 × `['73181500','73181500','73181500','73181500']`;
  misma_hora `['73181500','73181500','84714900','84714900']`.
- **PG 16, 1e81a30:** salida=1, «FALLA | ante un empate gana el texto
  idéntico, en los dos órdenes de guardado»: el 7.º par da
  `['84714900', '84714900']` (la fila vieja con otro espaciado). Los otros
  dos chequeos de empate dan OK.
- **PG 16, e81b961:** «todo OK», salida=0. identico 8 × `['73181500','84714900']`;
  ultima 5 × `['73181500','84714900','73181500','84714900']`; misma_hora 4 ×
  `'84714900'`. Cada confirmación devuelve `historial_guardado: true` y va en
  su propio pedido.

## Sabotajes nuevos (`scripts/testing/sabotajes/catalogo3.sh`)

50 sabotajes en el script; corrí los 50 sobre e81b961: **50 de 50 ROJO**,
«fallas: 0», salida=0 (`sab_c3_v3.log`). Los de esta vuelta, con el texto del
log:

| Sabotaje | Dice |
|---|---|
| ante un empate vuelve a no preferir el texto idéntico | «FAILED tests/test_catalogo3.py::test_ante_un_empate_gana_el_texto_identico» |
| el texto idéntico vuelve a distinguir mayúsculas y espacios | «FAILED tests/test_catalogo3.py::test_ante_un_empate_gana_el_texto_identico[Cable 2,5mm\xb2-Cable 2,5mm2-buscados2-» |
| ante un empate vuelve a ganar una fila fija | «FAILED tests/test_catalogo3.py::test_ante_un_empate_gana_la_ultima_confirmada» |
| a la misma hora vuelve a decidir el id de la fila | «FAILED tests/test_catalogo3.py::test_un_empate_a_la_misma_hora_no_depende_del_orden» |
| ante un empate vuelve a quedarse la primera fila que trae la base | «FAILED tests/test_catalogo3.py::test_ante_un_empate_gana» |
| la memoria del cliente compara sin las letras no latinas (existente, ahora apunta a `client_memory.py`) | «FAILED tests/test_catalogo3.py::test_la_memoria_del_cliente_usa_la_misma_clave» |

## Puertas

Todo sobre e81b961, desde base limpia (`rm -f test.db`), una puerta por vez.

| Puerta | Salida |
|---|---|
| suite completa (`--timeout=120`) | «5562 passed, 335 skipped, 3 xfailed, 107 warnings in 1138.69s (0:18:58)», salida=0 |
| salteados por archivo | 234 `test_excel3.py` (sin `xlwt`), 31 `security/test_security.py`, 19 `test_backup1a.py`, 15 `integration/test_workflows.py`, 12 `test_user_registration.py`, 10 `test_recent_changes_validation.py`, 7 `test_pdf_avg_functional.py`, 6 `unit/test_validations.py`, 1 `test_regression_phase0.py` |
| `compileall -q proyecto_maria` | salida=0 |
| golden (5 archivos) | «115 passed, 2 xfailed, 15 warnings in 16.83s» |
| `tests/test_catalogo3.py` | «104 passed, 3 warnings in 30.61s» |
| arnés PG 16 (`catalogo3_postgres.py`) | «todo OK», salida=0 |
| sabotajes `catalogo3.sh` | 50 de 50 ROJO, «fallas: 0» |

Al cerrar el proceso, la suite y test_catalogo3 imprimen «Task was destroyed but
it is pending!». Es el cierre del loop de asyncio, después del resumen (775 veces en el log de la suite), y no
cambia la salida.

### chequeo-6

```
chequeo-6 b7c4c85..e81b961: avisos para mirar, no un veredicto
producto +12/−9
arnés +166/−4
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/services/client_memory.py: 305 → 308
avisos: 0
```

## Hallazgos

| Quién | # | Sev. | Hallazgo | Qué hice |
|---|---|---|---|---|
| adversario-sonnet-alto (Sonnet, alto), sobre a2f77ee | A1 | Baja | Una fila escrita antes de que se normalizara la descripción («Cable  2,5mm2») nunca era «idéntica» | Arreglado en 1dca33e (compara contra la clave guardada); caso en e81b961, rojo con 1e81a30 arriba |
| ídem | A2 | Baja | Dentro de una misma operación o archivo, la «última» la decide el orden de escritura (hash de la clave), no el de la factura | Queda como riesgo: es determinista y la regla pedida se cumple |
| ídem | A3 | Baja | El PATCH manual pone `ultima_vez` con `func.now()` (segundos en SQLite, reloj de la base en PG) y cuenta como confirmación | Queda como riesgo; no lo reproduje |
| ídem | A4 | Baja | Sin prueba: `ultima_vez` nula, desempate por id, consulta que no normaliza | El desempate por id se reemplazó (3f68668) y lo cubre el caso de la misma hora; `ultima_vez` nula y la consulta que no normaliza siguen sin caso (abajo) |
| /code-review high (Opus, alto), sobre 1e81a30 | C1 | Media | El caso de la misma hora guardaba siempre en el mismo orden: no distinguía el defecto | Arreglado en e81b961: los dos órdenes, en SQLite y PG |
| ídem | C2 | Media | El texto idéntico se rearmaba con una función propia, no con la clave guardada | Arreglado en 1dca33e; de paso, el desempate se calcula sólo entre las filas empatadas (resuelve los dos hallazgos de rendimiento) |
| ídem | C3 | Baja | El arnés PG no comprobaba que cada confirmación se guardara | Arreglado en e81b961 (`historial_guardado: true` en cada pedido) |
| ídem | C4 | Baja | Fechas con y sin zona horaria mezcladas | Descartado: dentro de un motor no se mezclan; lookup y upsert van en pedidos distintos |
| ídem | C5 | Baja | Dos definiciones de «la más reciente» (lookup y migración) | Descartado: la migración desempata dentro de la misma clave, no entre filas que empatan en parecido |
| ídem | C6 | Baja | Relojes desparejos entre réplicas | Riesgo, abajo |
| ídem | C7 | Baja | Filas sin clave nunca son «idénticas» | Riesgo, abajo (era así antes) |

La severidad de C1 a C7 es mi lectura: no conservé la que dio /code-review.

## Riesgos y lo no corrido

- `catalog_service.py:381-402` (catálogo del proveedor) tiene el mismo patrón
  de «la primera de mayor puntaje»; la devolución pide la memoria del cliente,
  así que no lo toqué. Va como pieza aparte si lo querés.
- Con relojes de réplicas distintas, o con la misma hora, «la última
  confirmada» puede no ser la última real: a la misma hora gana el NCM mayor.
  Es determinista, no cronológico.
- µ/μ dan la misma clave (NFKC), así que para la memoria son el mismo texto:
  van en el caso de última confirmada, no en el de texto idéntico.
- Una fila con `clave` NULL (sin migrar) nunca cuenta como texto idéntico y
  cae a la última confirmada. Era así antes.
- Fechas con y sin zona horaria mezcladas romperían la comparación; lookup y
  upsert escriben con el mismo criterio, por eso lo descarté (C4).
- **No corrido:** `smoke_friccion.sh` y `ataque_aislamiento.sh`. El cambio
  es sólo cuál fila gana un empate dentro de `lookup_client_memory`: no cambia
  rutas, sesión, permisos ni la forma de la respuesta. El camino HTTP lo
  recorren el arnés PG y los casos de SQLite.
- **Sin caso:** una fila con `ultima_vez` nula en un empate, y una búsqueda que
  no normaliza (más de 2000 caracteres o un medio par). Las dos ramas se leen
  correctas (A4), pero ninguna prueba las distingue.

## Sigue

PRESUPUESTO-CLIENTE-1 (D141 a): faltan sus puertas, sabotajes, informe y el
hallazgo 8.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797WNM (rama claude/practical-shannon-szpwkn), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. CATALOGO-3 (devolución 973c489) entregada en e81b961 (informe en el commit siguiente), esperando veredicto. Sigue PRESUPUESTO-CLIENTE-1. Próxima D libre: D163. D151 sigue. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos.
