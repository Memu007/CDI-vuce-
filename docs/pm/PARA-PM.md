# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-MP-1 vuelta 5, entregada en `736fed6` (informe en el commit de arriba)

**Resultado.** Lo que promete la confirmación de cancelar sale de la misma
cuenta cuyo acceso muestra la pantalla: `/billing/me` calcula
`cancelar_corta_acceso` con `billing_entity` (la organización si hay, si no
la fila del usuario), igual que el resto de la respuesta. Caso nuevo con la
familia como datos: organización `past_due` vencida con fila `trial` +10,
organización `active` +20 con fila `past_due` vencida, y dos cuentas sin
organización. Las dos filas con organización dan ROJO en `9161e0a` y verde
ahora. Producto `+3/−2`, en `main.py`.

**Nada para decidir.** D51 (quién cancela lo de una organización) sigue
siendo pieza aparte; abajo, en «Riesgos», los casos que deja abiertos, con lo
que midió el adversario.

### SHAs (desde `3bfd1e1`, tu merge)

| SHA | Qué |
|---|---|
| `e0a54f7` | test: caso `test_cancelar_avisa_por_la_cuenta_que_da_el_acceso` (cuatro filas) y dos sabotajes en `cobro_mp1.sh`, uno por dirección; las anclas de los dos sabotajes viejos de `cancelar_corta_acceso` pasan a `billing_entity` |
| `96ce417` | fix: `cancelar_corta_acceso(billing_entity)` en `/billing/me`; `CHANGELOG.md` |
| `736fed6` | test: el caso mide sólo el aviso (ver «Revisiones», hallazgo del adversario) |
| (este) | docs: informe de las dos piezas |

### Rojo en `9161e0a`

El caso de `736fed6` copiado sobre un worktree de `9161e0a`,
`pytest tests/test_cobro_mp1_cde.py -k cancelar_avisa`:

```
E   AssertionError: el perfil promete otra cosa: {'billing_status': 'past_due', 'trial_ends_at': '2026-10-26T10:20:51.876453', ...
E   AssertionError: el perfil promete otra cosa: {'billing_status': 'active', 'trial_ends_at': '2026-11-25T10:20:52.444468', ...
FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_impaga_fila_en_prueba]
FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_activa_fila_impaga]
============ 2 failed, 2 passed, 31 deselected, 5 warnings in 2.39s ============
```

Las dos filas sin organización pasan en `9161e0a`, como corresponde: ahí
`billing_entity` y la fila son la misma cuenta. Están porque las pediste.

### Sabotajes (`cobro_mp1.sh`)

| Sabotaje | Qué cambia | Rojo esperado |
|---|---|---|
| «/billing/me avisa por la fila del usuario y no por su organización» | vuelve a `cancelar_corta_acceso(db_user)` | `…[org_impaga_fila_en_prueba]` |
| «/billing/me dice que corta si corta la fila del usuario, aunque la organización siga» | `…(billing_entity) or …(db_user)` | `…[org_activa_fila_impaga]` |

Las dos filas nuevas, copiadas de la salida sobre `96ce417`:

```
ROJO  | C: /billing/me avisa por la fila del usuario y no por su organización: dice «FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_impaga_fila_en_prueba]»
ROJO  | C: /billing/me dice que corta si corta la fila del usuario, aunque la organización siga: dice «FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_activa_fila_impaga]»
```

### Puertas

| Puerta | Sobre | Resultado |
|---|---|---|
| `cobro_mp1.sh` | `96ce417` | las cinco bases en verde; 148 ROJO, entre ellos los dos de arriba; el control «sin mirar antes de insertar» sigue en verde, como tiene que ser; «sabotajes con falla: 0», salida 0 |
| Suite completa, worktree limpio | `96ce417` | `4419 passed, 121 skipped, 3 xfailed, 100 warnings in 928.88s (0:15:28)`, salida 0 |
| Suite completa, worktree limpio | `736fed6` | `4419 passed, 121 skipped, 3 xfailed, 100 warnings in 679.05s (0:11:19)`, salida 0 |
| `tests/test_cobro_mp1_cde.py` | `736fed6` | `35 passed, 3 warnings in 15.99s` |
| `compileall -q proyecto_maria` | `736fed6` | salida 0 |
| chequeo-6 `3bfd1e1..736fed6` (lo propio) | `736fed6` | 0 avisos, abajo |
| Historia (grep de §6) | `736fed6` | vacío |

`cobro_mp1.sh` corrió sobre `96ce417`. `736fed6` sólo borra las cinco
líneas de después del aviso en el caso nuevo (y el import que quedó sin uso);
los dos rojos nuevos salen de la aserción del aviso, que está antes y no
cambió. Lo mostré otra vez a mano sobre `736fed6` con el primer sabotaje
(`db_user`), en un worktree aparte:

```
FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_impaga_fila_en_prueba]
FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_activa_fila_impaga]
============ 2 failed, 2 passed, 31 deselected, 3 warnings in 1.74s ============
```

Son las dos filas con organización: con `db_user` fallan las dos
direcciones; el script espera la primera.

### chequeo-6

```
chequeo-6 3bfd1e1..736fed6: avisos para mirar, no un veredicto
producto +3/−2
arnés +38/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11306 → 11307
avisos: 0
```

Desde `9161e0a` (tu base de revisión) da además el AVISO de la anónima de
`pantalla_orden1.js`, que es de ORDEN-1b y está explicado en su sección.

### Revisiones

| Quién | Modelo y esfuerzo | Sobre | Hallazgo | Qué hice |
|---|---|---|---|---|
| `adversario-sonnet-alto` | Sonnet, alto | `96ce417` | 1. La segunda mitad del caso (el acceso después de cancelar) no distingue: con organización relee una organización que `cancel` no escribe. Lo probó: con `cancel` sin cambiar `billing_status`, las cuatro filas pasan | Lo reproduje leyendo el caso: en las cuatro filas el acceso ya coincidía antes de cancelar. Saqué esa mitad en `736fed6`; qué hace `cancel` con organización es D51 |
| | | | 2. Con organización en gracia (`active`, venció ayer) y fila `trial`, el aviso dice que corta y la organización sigue con acceso, porque `cancel` no la toca | Riesgo de D51, abajo |
| | | | 3. Con organización activa y fila `none` o `canceled` sin suscripción, la pantalla muestra «Cancelar» y da 409 | Ya existía. D51 |
| | | | 4. `suscripcion_abierta` y `renueva` mezclan la organización con `mp_preapproval_id` de la fila | Ya existía. D51 |
| | | | Las cinco mutaciones de la línea del aviso dan rojo en el archivo; los textos de los sabotajes están en sus rojos | — |
| `/code-review high` | esta sesión, alto | `3bfd1e1..96ce417` | 1. `cancel` decide `corta` y `service_until` con `db_user` | D51 |
| | | | 2. `cancel` no toca la organización | D51 |
| | | | 3. La aserción de después es tautológica con organización | Al principio la dejé; el adversario mostró que tampoco distingue sin organización. Sacada en `736fed6` |
| | | | 4. El botón se muestra y `cancel` da 409 | Ya existía. D51 |
| | | | 5. `renueva` y `suscripcion_abierta` salen de `db_user` | Ya existía. D51 |
| | | | 6. Las filas sin organización repiten otro caso | Quedan: las pediste en este caso |
| | | | 7. Los sabotajes no rompen `cancel` | Por diseño: la vuelta cambia el aviso, no `cancel` |
| Seguridad | subagente Sonnet, con las instrucciones de `/security-review` | `3bfd1e1..96ce417` | «Sin hallazgos» | — |
| Seguridad | subagente Sonnet, con las instrucciones de `/security-review` | `96ce417..736fed6` | «Sin hallazgos»: sólo `pantalla_orden1.js` y `test_cobro_mp1_cde.py`; el producto no lee `X-Prueba-Consulta` (grep en `proyecto_maria/`: 0) | Lo reproduje |

### Riesgos

- **Medio, es D51.** Con organización, `cancel` sigue cambiando sólo la fila
  del usuario. El aviso ahora dice lo que pasaría con la cuenta que da el
  acceso, pero `cancel` no actúa sobre ella. El adversario lo midió con
  organización `active` vencida ayer (gracia) y fila `trial`:
  `promesa_corta=True status_pantalla=active cancel=200 org_antes=active acceso_org_antes=True org_despues=active acceso_org_despues=True fila_despues=canceled`.
  La pantalla dice «dejás de usar CDI» y la organización sigue en gracia. La
  respuesta de `cancel` (`service_until`, el log) también sale de la fila.
- **Bajo, es D51.** Organización activa con fila `none` o `canceled` sin
  suscripción: botón «Cancelar» y 409.
- Ninguna fila del caso cubre organización `trial`, `canceled` o `none`, ni
  un `organization_id` sin organización (ahí `_get_billing_entity` cae a la
  fila). No las agregué: el aviso es una sola llamada con la entidad, y las
  dos direcciones ya la fijan.

### Comandos para reproducir

```bash
# 1. Sabotajes: los dos nuevos en ROJO con su fila, y «sabotajes con falla: 0»
PY=venv/bin/python scripts/testing/sabotajes/cobro_mp1.sh 736fed6
# 2. El caso: 4 passed
python -m pytest -q --no-cov tests/test_cobro_mp1_cde.py -k cancelar_avisa
# 3. Números de §6: 0 avisos
python docs/pm/herramientas/chequeo-6.py 3bfd1e1 736fed6
```

### Archivos de producto tocados

`proyecto_maria/main.py` (y `CHANGELOG.md`).

---


## ORDEN-1b vuelta 4, entregada en `f5e9fac` (informe en el commit de arriba)

**Resultado.** `z35` retiene la relectura de la vuelta del pago y ninguna
otra consulta a `/auth/current_user`. La familia va como datos del mismo
caso: las dos vueltas del pago (`success`, `topup_success`) por el orden
entre el tour y la carga (`primero tour`, `primero carga`), cuatro filas. Si
el caso escribe sin haber retenido la relectura, o la retiene antes de que la
pestaña tenga usuario, falla con su propio mensaje. El sabotaje M3 da ROJO en
las cuatro filas, y con la consulta del tour atrasada 3 s el caso viejo daba
VERDE y el nuevo falla. Mientras se retiene la relectura, las otras consultas
del usuario (el autoguardado, cada 2500 ms) esperan a que la pestaña la lea:
sin eso, con 3 s entre que entra B y se suelta la relectura, el sabotaje daba
VERDE 4 de 4. Sin espera fija nueva en el arnés. Producto: nada (el
`producto +3/−2` del chequeo-6 de abajo es el de COBRO-MP-1, que cae en el
medio del rango).

**Nada para decidir.** D55 quedó en (a), como lo decidiste. D50 (partir la
anónima) sigue en la cola.

### SHAs (desde `f22f48b`)

| SHA | Qué |
|---|---|
| `69d6c3b` | merge de tu rama (veredicto de la vuelta 3) |
| `72dd8e3` | test: cada consulta lleva su marca (`relectura`, `tour`, `carga`) y sólo se retiene la `relectura`; `PRIMERO=tour\|carga` fija el orden; el caso falla si escribe sin haberla leído; `orden1b.sh` mide las cuatro filas |
| `f246b18` | test: al retener, la pestaña tiene que tener usuario; tope de 15 s para el tour; la falla de red del tour corta el caso; `VUELTA`/`PRIMERO` que no dejan fila fallan |
| `f5e9fac` | test: mientras se retiene la relectura, toda otra consulta a `/auth/current_user` espera a que la pestaña la haya leído (hallazgo del adversario) |
| (este) | docs: informe de las dos piezas |

Archivos: `scripts/testing/pantalla_orden1.js` y
`scripts/testing/sabotajes/orden1b.sh`. Nada de producto.

### Cómo distingue cuál consulta es

Al abrir la pantalla hay tres lecturas de `/auth/current_user`: la del tour
(`checkDemoForceTour`, `fetch` directo), la de la carga (`loadCurrentUser`
desde `cargarUsuarioHastaTenerlo`) y la relectura del pago
(`handleBillingReturn`, `setTimeout(loadCurrentUser, 4000|2000)`).

- La relectura se reconoce por el `setTimeout` que la programa, no por el
  orden de llegada. El tour, por su pila. Cada consulta sale con la marca en
  el header `X-Prueba-Consulta` y el handler retiene sólo la `relectura`.
- El orden entre tour y carga lo fija el caso: con `primero tour`, la carga
  espera a que termine la del tour (tope de 15 s, con su mensaje).
- Antes de escribir, el caso espera a que la relectura se haya leído; si no,
  falla con «…y la pestaña no leyó la relectura del pago en 15 s: no se escribe sin medirla».
- Mientras retiene la relectura, toda otra consulta a `/auth/current_user`
  espera a que la pestaña la haya leído (`f5e9fac`).

### Rojo una vez

**Sabotaje M3, las cuatro filas** (salida de `orden1b.sh` sobre `f5e9fac`,
copiadas):

```
ROJO  | la sesión de la respuesta se lee cuando ya llegó (success, primero tour): dice «FALLA: la relectura de la vuelta del pago (success, primero tour) contestó A, entró B antes de leerla y la pestaña guardó un cliente y el cliente quedó en la cuenta de B»
ROJO  | la sesión de la respuesta se lee cuando ya llegó (success, primero carga): dice «FALLA: la relectura de la vuelta del pago (success, primero carga) contestó A, entró B antes de leerla y la pestaña guardó un cliente y el cliente quedó en la cuenta de B»
ROJO  | la sesión de la respuesta se lee cuando ya llegó (topup_success, primero tour): dice «FALLA: la relectura de la vuelta del pago (topup_success, primero tour) contestó A, entró B antes de leerla y la pestaña guardó un cliente y el cliente quedó en la cuenta de B»
ROJO  | la sesión de la respuesta se lee cuando ya llegó (topup_success, primero carga): dice «FALLA: la relectura de la vuelta del pago (topup_success, primero carga) contestó A, entró B antes de leerla y la pestaña guardó un cliente y el cliente quedó en la cuenta de B»
```

**El hallazgo del adversario que motivó `f5e9fac`.** El autoguardado
consulta `/auth/current_user` cada 2500 ms. Si una de esas consultas salía
con B adentro antes de soltar la relectura, la pestaña se tapaba por ese otro
camino y el sabotaje M3 no llegaba a medirse. Lo reproduje con copias del
arnés con 3 s entre que entra B y se suelta la relectura, M3 puesto,
`topup_success`, `primero carga`, cuatro corridas de cada una:

```
== viejo_tras            (f246b18 + 3 s)
1 VERDE
2 VERDE
3 VERDE
4 VERDE
== nuevo_tras            (f5e9fac + 3 s)
1 ROJO FALLA: la relectura de la vuelta del pago (topup_success, primero carga) contestó A, entró B antes de leerla y la pestaña guardó un cliente y el cliente quedó en la cuenta de B
```

Las corridas 2 a 4 de `nuevo_tras` dicen, letra por letra, lo mismo que la 1.

Sin el sabotaje, `f5e9fac` + 3 s da verde: `z35`, las cuatro filas, dos
corridas, `exit=0` las dos. Los 3 s son sólo de la contraprueba y no entran
al repositorio. En el arnés que se corre de verdad la ventana es la de
`nuevoUsuario(B)`, alrededor de 1 s, por eso en mis corridas de `f246b18`
salía rojo; con una máquina más lenta podía salir verde.

**El de la vuelta anterior, con el tour atrasado** (sigue igual en
`f5e9fac`): con `72dd8e3` y el tour atrasado 3 s el sabotaje daba
`VERDE … la prueba no lo vio`; desde `f246b18` el caso se niega a medir con
«…pero la relectura salió antes de que la pestaña cargara el usuario».

### Puertas

| Puerta | Sobre | Resultado |
|---|---|---|
| `orden1b.sh` | `f5e9fac` | base verde; 28 ROJO, entre ellos las cuatro filas de `z35` de arriba; «sabotajes sin rojo: 0», salida 0 |
| `orden1.sh` (su base corre el arnés entero sin `CASOS`) | `f5e9fac` | base verde; 76 ROJO, «sabotajes sin rojo: 0», salida 0 |
| Suite completa, worktree limpio | `736fed6` (contiene `f5e9fac`) | `4419 passed, 121 skipped, 3 xfailed, 100 warnings in 679.05s (0:11:19)`, salida 0 |
| `compileall -q proyecto_maria` | `736fed6` | salida 0 |
| `z34` y `z35` sin sabotaje | `f5e9fac` | las 5 filas OK, `exit=0` |
| chequeo-6 `f22f48b..f5e9fac` | `f5e9fac` | 1 aviso, abajo |
| Historia (grep de §6) | `f5e9fac` | vacío |

### chequeo-6

```
chequeo-6 f22f48b..f5e9fac: avisos para mirar, no un veredicto
producto +3/−2
arnés +94/−26
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11306 → 11307
  AVISO creció una función de más de 150: scripts/testing/pantalla_orden1.js:281 <anónima> 1552 → 1584, 1 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 1
```

El `producto +3/−2` y `main.py` son de COBRO-MP-1 (`96ce417`), que cae entre
`f22f48b` y `f5e9fac`. `f246b18..f5e9fac` solo da `arnés +43/−6` y 0 avisos.

**El AVISO queda.** Lo nuevo está en `vueltaDelPago` y
`respuestaDeAConOtroAdentro`, funciones propias; el largo de la anónima
cuenta las anidadas. Su cuerpo propio crece 1 línea, que no ubiqué. Partirla
sigue en la cola (D50).

### Revisiones

| Quién | Modelo y esfuerzo | Sobre | Hallazgo | Qué hice |
|---|---|---|---|---|
| `/code-review high` | esta sesión, alto | `72dd8e3` | 1. Sin el chequeo de que la pestaña ya tiene usuario, con el tour lento la relectura se retiene sin dueño y el sabotaje puede dar verde | Reproducido arriba; arreglado en `f246b18` |
| | | | 2. `await tourTermino` sin tope ni falla propia | Tope de 15 s con su mensaje y `requestfailed` llama a `falla` (`f246b18`). Espera la consulta, no un tiempo |
| | | | 3. El tour se reconoce por `checkDemoForceTour` en la pila | Queda, como riesgo: si se renombra, la fila `primero tour` se pasa del tope y falla; no da verde |
| | | | 4. La relectura se reconoce por `fn.name === 'loadCurrentUser'` en el `setTimeout` | Queda, como riesgo: si cambia, no se retiene nada y falla con «no vuelve a leer el usuario en 15 s» |
| | | | 5. `VUELTA`/`PRIMERO` mal escritos dejan cero filas y `z35` da verde sin correr | Falla con «VUELTA o PRIMERO no dejan ninguna fila de z35» (`f246b18`) |
| | | | 6. Si la relectura contesta no-ok, `__relecturaLeida` no se pone y el mensaje apunta a otra causa | Queda: el rojo es correcto, el texto confunde |
| | | | 7. El spread de `o.headers` perdería un objeto `Headers` | No es real acá: `api()` arma un objeto plano y el tour no pasa headers |
| | | | 8. La dimensión tour/carga duplica las corridas y no cambiaría el camino | Queda: pediste la familia, y la contraprueba del tour atrasado muestra que el orden sí cambia lo que se mide |
| `adversario-sonnet-alto` | Sonnet, alto | `f246b18` | 1. Otra consulta (el autoguardado) puede ver a B antes de que se suelte la relectura y tapar la pestaña por otro camino: verde intermitente del sabotaje | Reproducido arriba (VERDE 4 de 4 con 3 s); arreglado en `f5e9fac` |
| | | | 2. Renombrar `checkDemoForceTour` | Mismo riesgo que el 3 del code-review |
| | | | 3. Un rojo de entorno se puede leer como rojo del caso, y `continue().catch(() => {})` traga errores de la ruta | Queda, como riesgo bajo: traga el error de una ruta ya cerrada; si la relectura no llega, el caso falla por su tope |
| `/code-review high` | esta sesión, alto | `f246b18..f5e9fac` | 4. Si la relectura falla, se aborta o contesta no-ok, `leida` no se resuelve y las otras consultas quedan colgadas | Queda, como riesgo bajo: termina en rojo («no leyó la relectura en 15 s»), nunca en verde |
| | | | 5. Mientras una consulta espera `leida`, se ignora su `AbortSignal`; si la espera pasara los 10 s de `ESPERA_SESION_MS`, `sesionEsDelDueno` daría false por el aborto y el sabotaje podría pasar verde | Queda, como riesgo bajo: hace falta una espera de más de 10 s y `nuevoUsuario(B)` tarda alrededor de 1 s; M3 dio rojo 4 de 4 en la serie y en `orden1b.sh` |
| Seguridad | subagente Sonnet, con las instrucciones de `/security-review` | `f22f48b..f246b18` y `f246b18..f5e9fac` | «Sin hallazgos» las dos veces: sólo archivos de prueba; el producto no lee `X-Prueba-Consulta`, `VUELTA` ni `PRIMERO` (grep en `proyecto_maria/`: 0) | — |

### Riesgos

- **Bajo.** El caso reconoce el tour y la relectura por los nombres de sus
  funciones. Si se renombran, falla fuerte; no da verde en silencio.
- **Bajo.** Los 4 y 5 del code-review de `f5e9fac`: un rojo colgado si la
  relectura falla, y un verde posible sólo si la espera pasa de 10 s.
- **Bajo, de entorno.** El adversario corrió `orden1b.sh 72dd8e3` y le dio
  `ModuleNotFoundError: No module named 'proyecto_maria'`. No lo diagnostiqué;
  mis corridas de `orden1b.sh` desde la raíz del repositorio arrancan bien.
- **Bajo, de entorno.** Corrido muchas veces contra la misma API, el login
  da 429. Los scripts de sabotaje levantan una API nueva por corrida.
- **Bajo.** El header `X-Prueba-Consulta` llega al servidor en las corridas
  del arnés; el producto no lo lee.
- Siguen en pie de la vuelta 2: D50 a la cola; H3 riesgo bajo; las lecturas
  GET sin freno, fuera de la pieza.

### Comandos para reproducir

```bash
# 1. Sabotajes de la pieza: ROJO en las cuatro filas de z35 y «sabotajes sin rojo: 0»
PY=venv/bin/python PUERTO=8875 scripts/testing/sabotajes/orden1b.sh f5e9fac
# 2. El arnés entero en verde (la base del script) y «sabotajes sin rojo: 0»
PY=venv/bin/python PUERTO=8853 scripts/testing/sabotajes/orden1.sh f5e9fac
# 3. Números de §6: 1 aviso, el de arriba
python docs/pm/herramientas/chequeo-6.py f22f48b f5e9fac
```

### Archivos de producto tocados

Ninguno.

/compact conservar: Dev 1, rama claude/dev-tecnica. COBRO-MP-1 vuelta 5
entregada en 736fed6 y ORDEN-1b vuelta 4 en f5e9fac (informe en el commit de
arriba), las dos sin D para decidir. Sigue CSRF-1, en tu orden. Nada se publica
sin el «dale» de Emi; nunca main.
