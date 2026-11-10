# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PRESUPUESTO-CLIENTE-1 (D141 a) entregada en eeba405 (base de176b1~1 = 2fbfea9)

Los commits de la pieza están intercalados con los de CATALOGO-3. Para verla
sola, cherry-pick de los ocho sobre `de176b1~1` (comando abajo). El producto
cambia sólo en `proyecto_maria/main.py` (y `CHANGELOG.md`).

| SHA | Qué |
|---|---|
| de176b1 | fix: pasar una operación compartida a otro cliente da de baja su link |
| f9d4c76 | test: el link compartido se va al pasar la operación a otro cliente |
| db0f25a | refactor: el borrado del link al cambiar de cliente va en su función |
| 1345ca7 | test: los sabotajes del link siguen al borrado en su función |
| 4d30e9c | refactor: el cliente de `_soltar_link_de_otro_cliente` es texto (hallazgo 8) |
| c3cca11 | test: en Postgres, la operación pasada a otro cliente pierde su link |
| a9fb87f | docs: el docstring dice qué hay en el link que se suelta |
| eeba405 | test: al pasar la operación de cliente no se van los links de otras operaciones |
| (siguiente) | docs: este informe |

**Resultado.** Cuando `save_client_operation` guarda en otro cliente una
operación que ya tenía cliente, borra sus PublicQuote en la misma
transacción. Desde ese momento el link da 404. Hay tres casos en que el link
sigue:
- la operación se guarda en el mismo cliente;
- la operación no tenía cliente y recibe uno;
- el guardado falla: el rollback deja el link como estaba.

Los links de las demás operaciones, del mismo dueño o de otro, no se tocan.
Funciona igual en SQLite y en PG 16. Con el arreglo revertido falla en los
dos motores (rojos abajo).

`main.py:6341`, función aparte de 8 líneas. `save_client_operation` sólo suma
la llamada. Producto +10/−0 (chequeo-6 abajo).

## Decisiones

**D163. Un link que se comparte mientras la operación pasa a otro cliente.**
`share_quote` lee la operación, después calcula los aranceles (llama a
Tarifar) y recién ahí inserta el link. Puede pasar que, mientras tanto, el
mismo usuario guarde la operación en otro cliente desde otra pestaña. En ese
caso el link nuevo se inserta después del borrado y queda andando con el
presupuesto armado para el cliente anterior (CR1 de /code-review).
`get_public_quote` no compara el cliente del link (CR2).
- (a) Queda como riesgo bajo, sin código.
- (b) En `share_quote`, bloquear la operación y volver a leer
  `op.client_id` antes del insert.
- (c) Guardar `client_id` en el snapshot y que `get_public_quote` dé 404 si
  ya no coincide con el de la operación.

**Recomiendo (a).** Para que pase, el mismo dueño tiene que compartir y
cambiar de cliente a la vez, en dos pestañas. No cruza ninguna frontera de
permisos: el link lo arma y lo reparte ese mismo usuario, y puede volver a
compartirlo cuando quiera. (b) agrega un bloqueo en un endpoint que espera a
un servicio externo. (c) cambia el formato del snapshot y deja sin cubrir los
links ya emitidos, que no tienen el campo. Si preferís cerrarlo, (c) es la
más barata y no bloquea nada.

## Hallazgo 8

- **`client_id: int`:** corregido en 4d30e9c. La columna y el valor de la
  ruta son texto; la anotación decía `int` e invitaba a convertirlo, y eso
  rompería la comparación. No tiene prueba porque no cambia el
  comportamiento: la comparación ya era entre textos.
- **La función de 161 líneas:** es el AVISO de chequeo-6. La rama nueva va en
  la función aparte, como pide §6. La función larga sólo suma la llamada
  (160 → 161). Partirla va a la cola de limpieza; no la toqué.

## Comandos copiables

Desde un worktree con su venv y las variables de las pruebas
(`DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares`):

```bash
python -m pytest -q --no-cov tests/test_datos1.py          # 10 passed
PY=$(which python) scripts/testing/sabotajes/datos1.sh eeba405   # 18 ROJO, «sabotajes sin rojo: 0»
(unset DATABASE_URL; python scripts/testing/datos1_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/<base vacía>)   # «fallas: 0»
# la pieza sola, para chequeo-6:
git worktree add /tmp/pc1 de176b1~1 && cd /tmp/pc1 && git cherry-pick de176b1 f9d4c76 db0f25a 1345ca7 4d30e9c c3cca11 a9fb87f eeba405 && python docs/pm/herramientas/chequeo-6.py de176b1~1 HEAD
```

## Rojos copiados

- **Arreglo revertido, SQLite** (sabotaje «pasada a otro cliente, el link
  sigue andando»): «FAILED tests/test_datos1.py::test_pasar_la_operacion_a_otro_cliente_borra_su_presupuesto»
  «AssertionError: (True, 200)» «assert 200 == 404».
- **Arreglo revertido, PG 16** (`pg_pc1_antes.log`): «FALLA | guardada en
  otro cliente, la operación pierde su link (200)», «fallas: 1». El chequeo
  anterior, «si el guardado en otro cliente falla, el link sigue (400)», da
  OK también sin el arreglo, como corresponde.
- **PG 16 sobre eeba405** (`pg_pc1_v2.log`): «OK | si el guardado en otro
  cliente falla, el link sigue (400)», «OK | guardada en otro cliente, la
  operación pierde su link (200)», «fallas: 0», salida=0.

## Sabotajes (`scripts/testing/sabotajes/datos1.sh`)

El script tiene 18 sabotajes y corrí los 18 sobre eeba405: **18 de 18 ROJO**,
«sabotajes sin rojo: 0», salida=0. Estos son los de esta pieza, con el texto
del log (todos en `test_pasar_la_operacion_a_otro_cliente_borra_su_presupuesto`):

| Sabotaje | Dice |
|---|---|
| pasada a otro cliente, el link sigue andando | «AssertionError: (True, 200)» «assert 200 == 404» |
| se borra aunque siga en el mismo cliente | «AssertionError: (False, 200)» «assert 404 == 200» |
| se borra al recibir cliente por primera vez | «AssertionError: sin cliente antes» «assert 404 == 200» |
| el borrado queda aunque el guardado falle | «AssertionError: (True, 400)» «assert 404 == 200» |
| se borran también los links de otras operaciones | «AssertionError: otra operación del mismo cliente» «assert 404 == 200» |
| el guardado encuentra la operación de otro dueño | «AssertionError: otro dueño» «assert 404 == 200» |

## Puertas

Todo sobre eeba405, desde base limpia (`rm -f test.db`), una puerta por vez.

| Puerta | Salida |
|---|---|
| suite completa (`--timeout=120`) | «5562 passed, 335 skipped, 3 xfailed, 110 warnings in 1123.64s (0:18:43)»; sin FAILED ni ERROR. Los 335 salteados son la misma cuenta que en CATALOGO-3 (234 de `test_excel3` sin xlwt, 19 de `test_backup1a` «sin Postgres 16 local» y 82 viejos con motivo escrito) |
| `compileall -q proyecto_maria` | rc=0, sin salida |
| golden (5 archivos) | «115 passed, 2 xfailed in 17.33s» |
| `tests/test_datos1.py` | «10 passed» |
| arnés PG 16 (`datos1_postgres.py`) | «fallas: 0», salida=0 |
| sabotajes `datos1.sh` | 18 de 18 ROJO, «sabotajes sin rojo: 0» |
| `smoke_friccion.sh` (app en ENVIRONMENT=test, SQLite) | «OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido», salida=0 |
| `ataque_aislamiento.sh` | sobre Postgres descartable: «Bloqueado: 47 · Fugas: 0 · Sin probar: 0», «PUERTA G3 PASADA», salida=0 |

### chequeo-6 (la pieza sola: los 8 commits sobre `de176b1~1`)

```
chequeo-6 de176b1~1..HEAD: avisos para mirar, no un veredicto
producto +10/−0
arnés +141/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12124 → 12134
  AVISO creció una función de más de 150: proyecto_maria/main.py:8098 save_client_operation 160 → 161, 1 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 1
```

AVISO de `save_client_operation`: la rama nueva va en la función aparte, como
pide §6. La función larga sólo suma la llamada. Partirla va a la cola de
limpieza.

## Hallazgos

| Quién | # | Sev. | Hallazgo | Qué hice |
|---|---|---|---|---|
| PM | 8 | Baja | `client_id: int` y función de 161 líneas | Anotación arreglada en 4d30e9c; la función, AVISO justificado arriba |
| adversario-sonnet-alto (Sonnet, alto) | A1 | Baja | El docstring exageraba qué datos guarda el link | Arreglado en a9fb87f |
| /code-review high (Opus, alto) | CR1 | Baja | Carrera: un `share_quote` en vuelo inserta el link después del borrado | D163 |
| ídem | CR2 | Baja | `get_public_quote` no compara el cliente | D163 (c) |
| ídem | CR3 | Media | Ninguna prueba distinguía un borrado de los links de otras operaciones | Arreglado en eeba405 (caso + sabotaje) |
| ídem | CR4 | Baja | El arnés PG no comprobaba el status del guardado ni del share del caso 6 | Arreglado en eeba405 |
| ídem | CR5 | Baja | El historial de productos (ClientProductHistory) del cliente anterior conserva lo aprendido de esa operación | Riesgo, abajo |
| ídem | CR6 | Baja | `ITEM` y `_cliente` del caso duplican a `_cliente_con_presupuesto` | Riesgo, abajo (va a limpieza) |
| ídem | CR7 | Baja | f9d4c76 arrastró una línea de `catalogo3.sh` (la etiqueta Ñ) | Riesgo, abajo: ya está subido, sin amend |
| revisión de seguridad (Sonnet, alto, sólo lectura) | — | — | Sin hallazgos (confianza 9/10) | — |

La severidad de CR1 a CR7 es mi lectura.

## Riesgos y lo no corrido

- **CR5.** Si la operación pasa al cliente B, la memoria de NCM del
  cliente A conserva lo que aprendió de ella. No borra nada ni expone nada
  a otro usuario; queda así.
- **CR6.** El caso nuevo de `test_datos1.py` repite el armado de cliente e
  ítem del helper. Va a la cola de limpieza.
- **CR7.** El cambio de `catalogo3.sh` en f9d4c76 es de CATALOGO-3 y quedó
  en el commit equivocado. Ya está subido, así que no lo corrijo con amend.
- En `datos1_postgres.py`, los POST que crean los clientes x e y encadenan
  `.json()["cliente"]["id"]` sin mirar el status. Si fallaran, el arnés
  cortaría con KeyError en vez de con un FALLA legible. No da un falso
  verde.
- **No corrí `/security-review` sobre la rama entera:** el diff contra
  `main` mide unos 600 KB y casi todo es de otras piezas. En su lugar hice
  una revisión de seguridad acotada a los ocho commits, con un subagente
  Sonnet alto de sólo lectura. Revisó `_get_owned_client`, el filtro por
  dueño de `_operacion_maria`, que el borrado va por `operation.id`, el
  dueño en `share_quote`, los parámetros ligados y el commit y rollback.
  Sin hallazgos.
- **No corrido:** nada de las puertas de `/entregar`.

## Sigue

CATALOGO-3 quedó aceptada sobre e81b961, sin integrar (f2b099a). Nada marcado
en mi canal para después de esta pieza: espero su veredicto.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. CATALOGO-3 aceptada sobre e81b961 (f2b099a); PRESUPUESTO-CLIENTE-1 entregada en eeba405 (informe en el commit siguiente), esperando veredicto. Próxima D libre: D164. D151 sigue. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos.
