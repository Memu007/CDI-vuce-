# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-MP-4 (con D124), entregada en `0fb991c` (informe en el commit de arriba)

Base: `3be86b7`. El código está en `0fb991c`, un merge de tu rama que trae `9eef8a2` y sólo toca `docs/pm`. El informe va en el commit de arriba.

| Commit | Qué |
|---|---|
| `f152a7a` | producto: la marca del 503 y quién concilia |
| `674da8f` | casos, `cobro_mp4.sh` y `cobro_mp4_postgres.py` |
| `83a2957` | producto: conciliar borra las marcas de todo el estudio; en el CHANGELOG, la vuelta atrás va después del código |
| `31da854` | casos de la marca de otra cuenta y del borrado |
| `b5c9dc0` | merge de tu rama (`docs/pm`) |
| `162468e` | D124: la CI instala `xlwt` |
| `7cb4918` | dos casos de tiempo de `test_cobro_mp2.py` esperan la marca nueva (abajo, «Un BASE en rojo») |
| `0fb991c` | merge de tu rama (`docs/pm`) |

COBRO-MP-2+3 vuelta 3, PERMISOS-1 y BACKUP-1a: leí que las aceptaste sobre `ca84c5f`, sin integrar. EXCEL-2d, aceptada sobre `84fd9f2`.

### Resultado

- **La marca.** Cuando cancelar recibe un 503, la cuenta que pidió queda anotada en `users.cancelar_sin_confirmar` con la suscripción que Mercado Pago no confirmó. La columna es nueva, de 100 caracteres y puede quedar vacía; la agrega el arranque.
- **Quién concilia.** Al reintentar, con todas las suscripciones canceladas, concilian sólo la dueña o quien tenga una marca igual a una suscripción del estudio que sigue anotada. Un miembro sin la marca recibe 403 y no cambia nada. El caso cubre que su suscripción venga cancelada, con 404 en MP o sin sid, y además que la marca sea de una suscripción que ya no está.
- **Se borra al conciliar.** Se borra la marca de quien pide y la de cada cuenta del estudio cuya suscripción se cancela.
- **El orden de cancelar.** Ahora cancela primero las de otras cuentas, después la de quien pide y al final la que paga. Así, si falla una de otra cuenta, quien pide sigue teniendo su suscripción anotada y puede volver a conciliar (`test_el_reintento_que_falla_en_otra_deja_la_suya_para_volver_a_conciliar`).
- **La migración** se probó en un Postgres 16 descartable (`cobro_mp4_postgres.py`): el arranque agrega la columna a una base con datos, el 503 guarda la marca, el reintento concilia y la borra, y un segundo arranque no cambia nada. La vuelta atrás se corrió dos veces.
- **Vuelta atrás.** Primero el código anterior y después `alter table users drop column if exists cancelar_sin_confirmar`. Se pierden las marcas pendientes: después de volver atrás, el reintento de un miembro vuelve a la regla anterior. Está en el CHANGELOG.
- **D124.** La CI instala `xlwt==1.3.0` en un paso aparte, después de `requirements.txt` (`162468e`). Producción no lo instala.
- **Archivos de producto:**
  - `proyecto_maria/main.py`: `cancel_billing`, `_quien_toca_el_plan` y la lista de `_migrate_add_user_billing_columns`;
  - `proyecto_maria/database/models.py`;
  - `CHANGELOG.md`;
  - `.github/workflows/ci.yml` (D124).

**producto +14/−6**.

### Decisiones

Nada para decidir. Supuestos que se pueden revertir:

- **El orden de cancelar** cambió (arriba, «El orden de cancelar»). La tarea no lo pedía. Sin él, cuando falla la suscripción de otra cuenta, la de quien pide ya se canceló y su marca no coincide con ninguna anotada: no podría volver a conciliar. Si preferís el orden de antes, ese caso pasa a esperar 403.
- **Conciliar borra las marcas de todo el estudio**, no sólo la de quien pide (`83a2957`). Una marca que queda apunta a una suscripción que ya no está anotada, así que no sirve para nada; borrarla deja la fila limpia.
- **Un segundo 503 pisa la marca** con la suscripción que falló esta vez. Es la que sigue anotada, así que la marca sigue sirviendo.

### Un BASE en rojo, arreglado en las pruebas

`cobro_mp2.sh` dio BASE en rojo sobre `31da854`. Dos casos de tiempo, `test_con_mp_sin_contestar_se_contesta_503_dentro_del_tope` y `test_el_tope_es_uno_para_todos_los_pedidos_a_mp`, comparaban la fila de quien pidió antes y después del 503 y veían la marca nueva. La marca es justamente lo que la pieza agrega. `7cb4918` los ajusta para esperarla en el 503 de cancelar y para seguir exigiendo que nada más cambie. El producto no se tocó.

### Sabotajes

`cobro_mp4.sh` sobre `0fb991c`: `BASE  | en verde`, 8 `ROJO`, `sabotajes con falla: 0`, salida 0.

| Sabotaje | El rojo dice |
|---|---|
| el 503 de cancelar no anota quién lo recibió | «FAILED tests/test_cobro_mp2.py::test_si_mp_cancelo_sin_confirmar_el_reintento_concilia[abrio» |
| conciliar no borra la marca de la dueña | «FAILED tests/test_cobro_mp2.py::test_si_mp_cancelo_sin_confirmar_el_reintento_concilia[duena» |
| un miembro sin la marca concilia | «FAILED tests/test_cobro_mp2.py::test_un_miembro_sin_la_marca_no_concilia[cancelada]» |
| una marca de una suscripción que ya no está concilia | «FAILED tests/test_cobro_mp2.py::test_un_miembro_sin_la_marca_no_concilia[marca_de_otra]» |
| conciliar deja las marcas de las otras cuentas | «FAILED tests/test_cobro_mp2.py::test_conciliar_borra_las_marcas_de_todo_el_estudio» |
| la marca de otra cuenta del estudio concilia | «FAILED tests/test_cobro_mp2.py::test_la_marca_de_otra_cuenta_no_concilia[abrio-miembro]» |
| cancelar empieza por la suscripción de quien pide | «FAILED tests/test_cobro_mp2.py::test_el_reintento_que_falla_en_otra_deja_la_suya_para_volver_a_conciliar» |
| el arranque no agrega la columna a una base que ya existe | la línea `FALLA` de «el arranque agrega cancelar_sin_confirmar» |

`cobro_mp2.sh`, en una copia enfocada (el entero tardaba demasiado), sobre `0fb991c`: `BASE  | en verde`, `BASE  | los cruces en Postgres, en verde`, 87 `ROJO`, ninguno sin rojo, `sabotajes con falla: 0`, salida 0. El script entero lo corriste vos sobre `ca84c5f`.

### Pruebas

**El rojo de los casos nuevos.** Los casos de `0fb991c` contra el producto de `3be86b7` (`main.py` y `models.py` de la base): `11 failed, 110 deselected`.

- Cinco fallan por la regla: `assert 200 == 403`, el miembro concilia con `{"success":true,"billing_status":"canceled",...}`. Son `test_un_miembro_sin_la_marca_no_concilia[cancelada]`, `[404_en_mp]` y `[marca_de_otra]`, y `test_la_marca_de_otra_cuenta_no_concilia[abrio-miembro]` y `[duena-abrio]`.
- Seis fallan sólo porque falta la columna (`AttributeError: 'User' object has no attribute 'cancelar_sin_confirmar'`): los tres de `test_si_mp_cancelo_sin_confirmar_el_reintento_concilia`, `[sin_sid]`, `test_conciliar_borra_las_marcas_de_todo_el_estudio` y `test_el_reintento_que_falla_en_otra_deja_la_suya_para_volver_a_conciliar`. Ese rojo no distingue la regla; lo que la distingue son los sabotajes de arriba, que dejan la columna y rompen una línea por vez. `[sin_sid]` no tiene sabotaje propio: con o sin el arreglo da 403.

| Prueba, sobre `0fb991c` | Resultado |
|---|---|
| suites de cobro: `tests/test_cobro_*.py`, `test_billing_checkout`, `test_billing_ola4`, `test_billing_autoservicio`, `test_api_clientes_billing`, `test_g7_cobro`, `test_g7_3_corte_active`, `test_mp_webhook_signature`, `test_webhook_ipn`, `test_migration_import` | `508 passed in 282.70s (0:04:42)` |
| D124, local, con `xlwt 1.3.0`: `-rs tests/test_excel2d.py tests/test_excel3.py` | `984 passed in 32.07s`, ninguna línea `SKIPPED` |
| `cobro_mp4_postgres.py` en un Postgres 16 descartable | 8 `OK`, `fallas: 0` |

### chequeo-6

```
chequeo-6 3be86b7..0fb991c: avisos para mirar, no un veredicto
producto +14/−6
arnés +336/−8
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/database/models.py: 570 → 573
  proyecto_maria/main.py: 11372 → 11377
avisos: 0
```

### Revisiones

| Revisión | Modelo y esfuerzo | Encontró | Qué hice |
|---|---|---|---|
| `adversario-opus-alto` | Opus, alto | No encontró cómo un miembro sin la marca concilie. Riesgos: si el proceso muere o falla el commit entre el 503 y la marca, no queda marca; la migración sin `lock_timeout` y con la excepción tragada (de antes); la vuelta atrás no sirve en SQLite; el texto del 403 confunde; la marca no vence | Van a «Riesgos». Producción es Postgres; el CHANGELOG no aclara que en SQLite la vuelta atrás no corre |
| `/code-review high` | el de la sesión | Baja: un segundo 503 pisa la marca. El caso `sin_sid` no distingue el defecto (con o sin el arreglo da 403). Repetición en el arnés | La marca pisada queda como supuesto. `sin_sid` queda porque la tarea lo pide en la familia; los otros tres sí distinguen (abajo, el rojo) |
| `/security-review` (subagente general) | Opus, alto; sólo leyó código | Nada con confianza 8 o más. Endurecimiento opcional: borrar la marca al sacar a un miembro | A «Riesgos»: la marca de quien salió no coincide con nada, porque al sacarlo se borra su suscripción |

### Riesgos

- **La marca no vence.** Queda hasta que alguien concilie. Sólo sirve mientras su suscripción siga anotada en el estudio.
- **Sin marca si se corta en el medio.** Si el proceso muere o falla el commit entre el 503 y la marca, quien pidió no queda anotado y su reintento recibe 403. La dueña igual puede conciliar.
- **Sacar a un miembro no borra su marca.** Al sacarlo se borra su suscripción, y los sid de MP no se repiten, así que esa marca no coincide con nada.
- **La vuelta atrás pierde las marcas pendientes.** `drop column if exists` es de Postgres; en SQLite da error de sintaxis.
- **La migración** sigue sin `lock_timeout` y traga la excepción, como las columnas de antes en la misma lista.
- **El 403** de un miembro sin la marca dice lo mismo que antes; no explica que puede conciliar quien recibió el 503.

### Lo que no se corrió

- **La CI de GitHub no corrió.** Se dispara con `main` y con PR, y esta rama no tiene PR. Lo de D124 en la CI (los `.xls` corriendo, no salteados) no lo pude mostrar ahí: lo mostré local, con el mismo `xlwt==1.3.0`. Queda para cuando corra la CI.
- **La suite completa** no corrió; sí las suites de cobro (arriba).
- **`cobro_mp2.sh` entero** no corrió: corrí una copia enfocada (arriba). Vos lo corriste entero sobre `ca84c5f`.
- **flake8** no corrió.
- **`smoke_friccion.sh` y `ataque_aislamiento.sh`** no corrieron: la pieza no toca pantallas ni aislamiento de datos.

### Para reproducir

```bash
git fetch origin claude/dev-tecnica && git checkout --detach 0fb991c
export DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares

# Los 8 sabotajes de esta pieza: «sabotajes con falla: 0» y 8 ROJO (el último, la migración en Postgres)
PY=$(command -v python) scripts/testing/sabotajes/cobro_mp4.sh 0fb991c

# La migración contra un Postgres 16 descartable: «fallas: 0»
PY=python scripts/testing/con_pg16.sh bash -c '"$0" scripts/testing/cobro_mp4_postgres.py "$BACKUP1A_PG_URL"' python

# Los casos nuevos: todos passed
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  python -m pytest -q --no-cov tests/test_cobro_mp2.py -k "cancelo_sin_confirmar or sin_la_marca or marca_de_otra or conciliar_borra or reintento_que_falla"

# D124: con xlwt instalado, ningún caso de .xls salteado (sin «SKIPPED ... xlwt»)
pip install xlwt==1.3.0
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  python -m pytest -q --no-cov -rs tests/test_excel2d.py tests/test_excel3.py

# Los números de §6: la salida de abajo
python docs/pm/herramientas/chequeo-6.py 3be86b7 0fb991c
```

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. EXCEL-2d aceptada en 84fd9f2; ca84c5f aceptada. COBRO-MP-4 (con D124) entregada en 0fb991c (informe en el commit de arriba). D119, D120, D121 y D124 contestadas. Sigue PERMISOS-2; frenar 2026-11-08 15:50 UTC. Reglas de Emi: sólo la PM y Emi me piden, nada se publica sin su «dale» para el SHA, nunca main, sin secretos.
