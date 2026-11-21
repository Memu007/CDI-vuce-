# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ADMIN-CREDITOS-1: tramos 1 y 2, entregados juntos

| | SHA |
|---|---|
| Base | `0208ea9d` |
| Producto | `795f10b3`, `ee643799`, `ecdeaf17`, `36f74147`, `38c62843`, `2c03ae3a`, `dad0139c` |
| Pruebas | los `test:` de `0208ea9d..39d4dd8b`; el último es `39d4dd8b` |
| Este informe | el commit `docs:` encima de `39d4dd8b` |

**Resultado.** El admin carga de 1 a 100 créditos extra a una cuenta desde el panel. Los cinco
ajustes se cumplen, cada uno con su caso y su sabotaje. Las puertas están en verde, salvo lo que se
declara en «Qué no corrí sobre el SHA final».

### Decisiones

| D | Pregunta | Opciones | Recomiendo |
|---|---|---|---|
| D237 | El admin llena el tope a 100 y después se paga un link de recarga que se creó antes | (a) queda como hoy: el webhook rechaza esa recarga a la vista (estado «rechazado», 200 a MP), la plata se cobró sin créditos y la devolución es manual; (b) la ruta del admin no deja llenar el tope mientras haya un link de recarga pendiente para esa cuenta | **(a)**. El rechazo de una recarga que no entra ya existe y lo cubre `test_una_recarga_que_no_entra_queda_rechazada_y_no_suma` (`tests/test_cobro_mp1_vuelta2.py:460`). (b) suma una consulta de links pendientes y otro 409 para un caso que hoy sólo puede producir Emi |
| D238 | Si la carga del admin toca `last_topup_at` | (a) sí, como la recarga pagada; (b) no, y sólo la recarga pagada lo toca | **(a)**. Es lo que dice D234 (a): una sola regla para acreditar. `last_topup_at` sólo lo escribe `billing_service.py:142` y sólo lo lee el panel de admin, en la columna «ultima_recarga» (`admin_router.py:401,415,438`): con (a), esa columna muestra también la carga del admin. Si querés distinguirla, eso es otra pieza |

**Supuestos que podés rechazar:**
- El registro de la carga (`creditos_admin`) no tiene claves foráneas, a propósito: una cuenta
  borrada no borra el registro, y la inserción no toma KEY SHARE sobre `users`, que chocaría con
  el candado de la cuenta. Lo fija `test_la_tabla_no_tiene_claves_foraneas`.
- `pedido` en mayúsculas da 422: el panel lo manda en minúsculas (`crypto.randomUUID()`), y así un
  mismo UUID no puede entrar como dos claves.

### Los ajustes

| # | Pide | Dónde se ve |
|---|---|---|
| 1 | La misma clave en dos cuentas a la vez, en Postgres | Caso 8 de `admin_creditos1_postgres.py`, «dos cuentas»: una carga 200 y la otra 409 «ese pedido ya se usó para otra carga», y la segunda cuenta queda sin créditos. Sabotaje 2 de `admin_creditos1_postgres.sh` |
| 2 | Llenar a 100 y reintentar con la misma clave da 200 `ya_aplicado` | `test_carga[llena_el_tope]` y `test_carga[vencidos_y_cien]`. La ruta busca el pedido (`db.get(CreditoAdmin, pedido)`) antes del tope. Sabotaje «el pedido no se busca antes del tope»: «assert 409 == 200» |
| 3 | El caso 9 como familia: usuario solo e integrante de un estudio que recibe la recarga pagada | Casos 9 y 10 en Postgres, con usuario solo y con integrante, con créditos vencidos y al día, y en los dos órdenes. En SQLite, `test_carga[solo]` y `test_carga[estudio]` |
| 4 | `pedido` que no es UUID o de más de 36 caracteres da 422 | `test_cuerpo_invalido[cuerpo7]` («no-es-un-uuid»), `[cuerpo8]` (UUID + «0», 37 caracteres), `[cuerpo9]` (mayúsculas), `[cuerpo10]` (sin pedido) |
| 5 | Puertas | La tabla de abajo |

### Puertas

| Puerta | SHA | Salida exacta |
|---|---|---|
| Suite completa | `6249a66d` | `6276 passed, 110 skipped, 3 xfailed, 110 warnings in 1229.68s (0:20:29)`, rc=0 |
| Unión: tramo 1 + `tests/test_admin_usuarios1.py` | `6f4c6c29` | `44 passed, 3 warnings in 6.51s`, rc=0 |
| `admin_usuarios1_postgres.py` (tu puerta nueva) | `6f4c6c29` | `fallas: 0`, rc=0 |
| `admin_creditos1_postgres.py` (casos 8 a 11) | `6f4c6c29` | el control «sin sabotaje» de la fila siguiente: «BIEN  | sin sabotaje: salida 0, 0 filas MAL» |
| `sabotajes/admin_creditos1.sh` (26) | `39d4dd8b` | 26 ROJO de 26; BASE «35 passed, 5 warnings» y «OK: ADMIN-CREDITOS-1 en el navegador»; «sabotajes sin rojo: 0», rc=0 |
| `sabotajes/admin_creditos1_postgres.sh` | `bbaf593d` | `sabotajes sin rojo: 0`, rc=0 |
| | `6f4c6c29` | `sabotajes sin rojo: 0`, rc=0; el control da «BIEN  | sin sabotaje: salida 0, 0 filas MAL» |
| `sabotajes/cobro_corte1.sh` entero | `39d4dd8b` | 87 ROJO, «sabotajes con falla: 0», rc=0 (BASE en verde, la pantalla en verde, el lock en verde) |
| `sabotajes/cobro_mp1.sh` entero, con Postgres 16 | `87985bba` | `con falla: 0` |
| | `6f4c6c29` | `sabotajes con falla: 0`, rc=0 |
| `anclas_perdidas.py` | `39d4dd8b` | rc=0, ninguna PERDIDA; los únicos `SIN ANCLA` son `limpieza1.sh:183` y `:187`, que ya estaban |
| `chequeo-6.py 0208ea9d 39d4dd8b` | `39d4dd8b` | abajo, entera |

**Qué no corrí sobre el SHA final y por qué vale igual:**
- **La suite** corrió sobre `6249a66d`. De ahí a `39d4dd8b` cambiaron `dev_dashboard.html`, la
  pantalla y su guion de sabotajes, `tests/test_admin_usuarios1.py` y `admin_usuarios1_postgres.py`
  (que trajiste vos con el merge) y `docs/`. Ningún `.py` de producto.
  Esos dos tests los corrió la unión y tu puerta, sobre `6f4c6c29`.
- **La unión, `admin_usuarios1_postgres.py` y el arnés de Postgres** sobre `6f4c6c29`: después
  cambiaron sólo `dev_dashboard.html` (+4/−3), la pantalla y su guion de sabotajes; ninguno de los
  tres los usa.
- **`cobro_corte1.sh`** sobre `87985bba`: sabotea `candados.py`, `main.py` y `billing_service.py`,
  que no cambiaron hasta `39d4dd8b`; después cambiaron sólo `admin_router.py` y el HTML.
- **`cobro_mp1.sh` y el sabotaje de Postgres** sobre `6f4c6c29`: después cambió sólo el HTML
  (+4/−3). `cobro_mp1.sh` sabotea también el HTML, pero `anclas_perdidas` sobre `39d4dd8b` no da
  ninguna PERDIDA.

### Adversarios y revisiones

| Quién | Hallazgo | Qué hice |
|---|---|---|
| Opus alto | Reabrir el diálogo con la carga en vuelo decía «no se confirmó» y no cómo terminó | Arreglado en `dad0139c`, con el escenario `reabrirEnVuelo` y su sabotaje. El rojo sobre `6f4c6c29`: «FALLA: reabrir en vuelo: el diálogo dice «La carga de 6 no se confirmó: si la enviás de nuevo, no se carga dos veces.», no «Cargada. Ahora tiene 21 vigentes.»» |
| `/code-review high` | El mismo de arriba | Igual |
| Sonnet alto | `last_topup_at` no se probaba en el webhook | Caso en `a5e22604` |
| Sonnet alto | El 409 decía un número negativo con más vigentes que el tope | Arreglado en `38c62843`; sabotaje «el 409 da un número negativo» |
| Sonnet alto | Reabrir perdía la carga sin confirmar | Arreglado en `2c03ae3a`. Los rojos sobre `2c03ae3a`, antes del arreglo de la pantalla: «FALLA: reabrir: el diálogo dice «», no «La carga de 2 no se confirmó…»» y «FALLA: reabrir y enviar: el diálogo dice «Cargada. Ahora tiene 12 vigentes.», no «Ya estaba cargada. Ahora tiene 10 vigentes.»» |
| Sonnet alto | El tope se llena antes de que se pague un link | D237 |
| Sonnet alto | Los parches de `conexiones1_tests.diff` no aplican sobre este árbol | Propuesta de limpieza, abajo |
| `/security-review` | Sin hallazgos | — |
| Mío, descartado | Creí que una recarga pagada que no entra en el tope se perdía sin aviso | No pasa: el control previo del webhook la rechaza a la vista; lo cubre `tests/test_cobro_mp1_vuelta2.py:460`. Corrige lo que anuncié en el chat |

### chequeo-6, entero

```
chequeo-6 0208ea9d..39d4dd8b: avisos para mirar, no un veredicto
producto +195/−52
  AVISO producto suma 143 líneas netas: el informe dice por qué (§6: más de 20)
arnés +959/−54
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/database/candados.py: nuevo, 33
  proyecto_maria/main.py: 12276 → 12249
  proyecto_maria/routers/admin_router.py: 466 → 514
  proyecto_maria/services/billing_service.py: 450 → 448
avisos: 1
```

rc=0. **El AVISO:** las 143 netas son la ruta nueva y su cuerpo validado, la tabla `CreditoAdmin`,
`candados.py` (el candado que se movió de `main.py` sin cambiarlo, D233) y `acreditar_extra`, que
ahora usan el webhook y la ruta (D234). El HTML no lo mide `chequeo-6`: `dev_dashboard.html`
+98/−7, con el grep de historia en 0.

### Riesgos que quedan

- Si `previa` desaparece entre el IntegrityError y la relectura, da 500. Para eso alguien tiene
  que borrar la fila en ese instante; no hay ruta que borre.
- `.one()` da 500 si la cuenta se borra entre el 404 y el candado.
- `fetchUsuarios(0)` después de cargar vuelve a la primera página de la tabla.
- `crypto.randomUUID()` sólo existe con HTTPS o en `localhost`; el panel de producción va por HTTPS.
- `con_pg16.sh` escribe su Postgres en `/tmp/cdi-pg16.XXXXXX` aunque `TMPDIR` diga otra cosa.

### Propuesta de limpieza

`scripts/testing/conexiones1_tests.diff` ya no aplica sobre este árbol (lo vio Sonnet). O se
regenera desde `tests/test_conexiones1.py`, o se borra junto con lo que lo usa en
`conexiones1_producto.sh`. Es tuya para la cola.

### Archivos de producto que toqué

- `proyecto_maria/database/candados.py` (nuevo)
- `proyecto_maria/main.py`
- `proyecto_maria/routers/admin_router.py`
- `proyecto_maria/services/billing_service.py`
- `proyecto_maria/templates/dev_dashboard.html`
- `CHANGELOG.md`

### Para reproducir

```bash
export PY=<venv>/bin/python
# Los sabotajes de la pieza: tiene que terminar en «sabotajes sin rojo: 0» y rc=0.
scripts/testing/sabotajes/admin_creditos1.sh 39d4dd8b
# Postgres: «filas MAL: 0; rondas sin armar: 0», y después «fallas: 0».
scripts/testing/con_pg16.sh $PY scripts/testing/admin_creditos1_postgres.py
scripts/testing/con_pg16.sh $PY scripts/testing/admin_usuarios1_postgres.py
# Los sabotajes en Postgres: «sabotajes sin rojo: 0».
scripts/testing/sabotajes/admin_creditos1_postgres.sh 39d4dd8b
# Las anclas: ninguna PERDIDA.
$PY scripts/testing/anclas_perdidas.py 39d4dd8b
# Los números de §6: la salida de arriba.
$PY docs/pm/herramientas/chequeo-6.py 0208ea9d 39d4dd8b
```

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, nunca main; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message priority next; la rutina trig_011UpBfwEu9TUzoNUrviqoP5 me dispara /respondio. Pieza: ADMIN-CREDITOS-1 tramos 1 y 2 entregada; producto hasta dad0139c, pruebas hasta 39d4dd8b, base 0208ea9d. Espero el veredicto y las respuestas a D237 y D238; la próxima D es D239. Si hay devolución, va primero. Sin secretos ni datos reales, nada contra producción ni MP real, nada se publica sin el «dale» de Emi para el SHA. tests/test_conexiones1.py queda sin seguimiento a propósito.
