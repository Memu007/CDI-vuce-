# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D278 (b): la lista de usuarios con el cobro efectivo, sobre `05ca7f71` (2026-11-21 04:23 UTC)

**Resultado.** Se cumple en `05ca7f71`, contra tu rama integrada en `a17011d1`. Después integré
`5af7e43d` (sólo `docs/pm/`).
- La lista de usuarios del panel muestra el cobro con el que decide el acceso. Una prueba vencida, una
  suscripción vencida hace más de 7 días o un integrante con el estudio vencido se ven `past_due`,
  aunque nadie haya entrado desde que vencieron.
- El acceso (`_vencer_si_corresponde`) y la lista usan la misma función,
  `billing_service.cobro_efectivo`, que no escribe; no hay copia en la lista. El plan no se tocó.
- Mirar sigue sin escribir: la lista calcula sobre las columnas leídas, no sobre objetos del ORM.
- `producto +28/−26`, chequeo-6 sin avisos. Revisión fuerte porque toqué `_vencer_si_corresponde`:
  `cobro_corte1.sh` con Postgres y Opus alto, además de lo pedido.
- **Para decidir: D279** (las otras copias de la regla). Nada más.

| SHA | qué |
|---|---|
| `4149d3fa` | fix: `cobro_efectivo` y la gracia en `billing_service`; `_vencer_si_corresponde` la usa; la lista también; CHANGELOG |
| `f70703cc` | test: los dos casos nuevos; cuatro sabotajes en `admin_usuarios1.sh`; tres anclas de `cobro_corte1.sh` siguen a la regla |
| `843a9e0e` | fix: la anotación `str \| None` de `cobro_efectivo` (sale de `/code-review`) |
| `b218105b` | test: la lectura por otra conexión espera el lock 30 s, como la suite (sale de `/code-review`) |
| `82b2f641` | test: las cuentas de borde a una hora de cada lado de los 7 días (sale del adversario Sonnet) |
| `05ca7f71` | test: las fechas de la familia se cuentan desde que se siembra (sale de `/code-review`) |

Archivos de producto: `main.py`, `routers/admin_router.py`, `services/billing_service.py`.

## D279 — las otras copias de la regla de vencido

Quedan tres lugares que deciden «¿venció?» por su cuenta. Ninguno hace que la lista contradiga al
acceso, porque usan los mismos umbrales y sólo pasan cuentas a `past_due`:
- `_check_expired_trials` (`main.py:786-807`), el SQL del arranque, sólo sobre `users`;
- `get_current_user` (`auth/dependencies.py:142-155`), sólo `trial` y sobre la fila del usuario;
- el checkout (`main.py:~11878`), sin gracia, sólo para elegir el texto del 409.

Además, el perfil de facturación del usuario (`main.py:3669`) muestra el estado guardado. Una cuenta
`active` vencida hace más de 7 días que no pasó por una ruta con cobro se ve `past_due` para el admin y
`active` en su propio perfil hasta su primer pedido con cobro, que da 402.
- **(a)** Una pieza chica: el perfil muestra `cobro_efectivo` y las tres copias pasan por ella. Toca
  `get_current_user`: revisión fuerte.
- **(b) Recomiendo:** a la cola de limpieza las tres copias; el perfil, como riesgo escrito. Hoy no
  hay camino que dé o niegue acceso mal, y lo que pide ADMIN-CREDITOS-1 es la lista, que ya está.

## Qué cambió

- **`billing_service.cobro_efectivo(cuenta, ahora=None)`** devuelve el estado con el que decide el acceso:
  `trial` con el fin pasado da `past_due`; `active` con el fin pasado hace más de
  `BILLING_GRACE_DAYS_ACTIVE` (7) días, también; sin fecha, lo guardado. Lee la fecha con `como_utc`.
  No escribe.
- **`_vencer_si_corresponde`** (`main.py:2204`) llama a esa función y asigna sólo si cambia. Ahora
  devuelve verdadero o falso. Antes devolvía `"trial"`, `"active"` o `None`, pero sus dos llamadores
  sólo lo usaban como verdadero o falso. Opus comparó la vieja y la nueva en 260 combinaciones de
  estado, fecha y zona: mismo veredicto y mismo estado guardado en todas.
- **`BILLING_GRACE_DAYS_ACTIVE`** se mudó a `billing_service`. `main.py` lo importa, así que
  `m.BILLING_GRACE_DAYS_ACTIVE` sigue andando (lo usa `conexiones1_renovacion.py`, de la Técnica).
- **La lista** (`admin_router.py:430`) aplica `cobro_efectivo` al saldo de quien paga (el estudio, si
  es integrante), sobre un `SimpleNamespace` hecho de las columnas leídas.

## La prueba

En `tests/test_admin_usuarios1.py`, dos casos nuevos:
- **`test_la_lista_muestra_el_cobro_con_el_que_decide_el_acceso`.** La familia va como datos en
  `COBROS`: prueba vencida y vigente, `active` una hora dentro y una hora fuera de los 7 días,
  `past_due`, cancelada terminada, integrante con el estudio vencido y con el estudio vigente (y la
  cuenta propia vencida). Siembra las cuentas con la app ya arrancada, porque el arranque vence las que
  encuentra vencidas y taparía el defecto. Pide la lista, después decide el acceso de cada cuenta con
  `_billing_vigente`, y compara las dos cosas entre sí y con lo esperado.
- **`test_mirar_no_cambia_la_base`.** Siembra también esa familia y lista. Después lee `users`,
  `organizations`, `password_reset_tokens` e `invitations` con `sqlite3` propio, fuera del pool de la
  app, y las encuentra iguales a la foto de antes.

**Rojo con el arreglo revertido, en el mismo SHA.** Con `admin_router.py` de `a17011d1` en un
worktree de `05ca7f71` (`rojo_final.log`):
```
E     {'adco5d5b54d2_prueba_vencida': 'trial'} != {'adco5d5b54d2_prueba_vencida': 'past_due'}
E     {'adco5d5b54d2_fuera_de_la_gracia': 'active'} != {'adco5d5b54d2_fuera_de_la_gracia': 'past_due'}
E     {'adco5d5b54d2_de_estudio_vencido': 'trial'} != {'adco5d5b54d2_de_estudio_vencido': 'past_due'}
=================== 1 failed, 8 passed, 5 warnings in 2.11s ====================
```
Son las tres vencidas, y nada más. Con el arreglo, en un worktree de `05ca7f71`: `134 passed, 19
warnings in 58.57s` (`test_admin_usuarios1.py`, `test_admin_solo_admin.py`, `test_cobro_corte1.py`;
`verde_final.log`).

**La gracia está fijada.** Con `BILLING_GRACE_DAYS_ACTIVE` en 6, 7 y 8, en un worktree de `05ca7f71`
(`gracia_final.log`):
```
gracia 6: E     {'adcof365d70f_en_la_gracia': 'past_due'} != {'adcof365d70f_en_la_gracia': 'active'} =================== 1 failed, 8 passed, 3 warnings in 2.17s ==================== 
gracia 7: ======================== 9 passed, 3 warnings in 2.13s ========================= 
gracia 8: E     {'adco1074bfab_fuera_de_la_gracia': 'active'} != {'adco1074bfab_fuera_de_la_gracia': 'past_due'} =================== 1 failed, 8 passed, 3 warnings in 2.33s ==================== 
```

**Sabotajes nuevos en `admin_usuarios1.sh`:**
- «mirar vence las cuentas y guarda», que rompe `test_mirar_no_cambia_la_base`;
- «la lista muestra el cobro guardado»;
- «el cobro se mira en la cuenta y no en quien paga»;
- «la suscripción vence sin gracia en la lista y en el acceso», que rompe la regla en
  `billing_service` y por eso agarra una copia de la regla dentro de la lista.

Los tres últimos rompen el caso de la lista. En `cobro_corte1.sh` se movieron a `billing_service` las
tres anclas de la regla: el vencimiento de `trial`, la gracia y la zona. El sabotaje «el pedido que
vence la cuenta da otra razón» ahora mira el booleano. Antes cambiaba el mensaje sólo al vencer un
`active`; ahora, ante cualquier vencimiento. Sigue exigiendo el rojo en `[suscripcion_vencida]`.

## Puertas sobre `05ca7f71`

| puerta | resultado |
|---|---|
| chequeo-6 `a17011d1 05ca7f71` | `producto +28/−26`, `avisos: 0` (salida entera abajo) |
| grep de historia de §6 | vacío |
| `anclas_perdidas.py 05ca7f71` | perdidas `0`, `0` y `0`; `no medido 5` en 2 guiones (`limpieza1.sh`, el cambio lo hace «nuevo»), igual que antes |
| `admin_usuarios1.sh 05ca7f71` | 31 `ROJO` de 31, `sabotajes sin rojo: 0` |
| `cobro_corte1.sh 05ca7f71` con Postgres 16 | 87 `ROJO`, 0 ROTO/PATRÓN/MAL, «BASE \| en verde», «BASE \| la pantalla en verde», «BASE \| el lock en verde», «sabotajes con falla: 0», rc=0, 03:18 a 04:22 UTC (`cobro_corte1_final.log`). Una primera corrida no midió el lock: le pasé `PG` con `/postgres` al final y el guion le suma otro (81 `ROJO` en servidor y pantalla, después «no se pudo crear la base»); la relancé entera |
| suite completa desde worktree limpio sobre `05ca7f71` | `6242 passed, 110 skipped, 3 xfailed, 112 warnings in 1153.04s (0:19:13)`, rc=0, 0 cambios en el árbol (`suite_final.log`) |
| `/code-review` alto | sobre `a17011d1..f70703cc`, `f70703cc..82b2f641` y `82b2f641..05ca7f71` (hallazgos abajo) |
| adversario Sonnet alto | sobre `a17011d1..f70703cc`; otra vuelta sobre `f70703cc..82b2f641` y otra sobre `82b2f641..05ca7f71` |
| adversario Opus alto | sobre `a17011d1..f70703cc`. Lo de después (una anotación y tres commits de pruebas) lo vieron Sonnet y `/code-review` |

chequeo-6, salida entera:
```
chequeo-6 a17011d1..05ca7f71: avisos para mirar, no un veredicto
producto +28/−26
arnés +122/−22
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12294 → 12276
  proyecto_maria/routers/admin_router.py: 465 → 466
  proyecto_maria/services/billing_service.py: 420 → 439
avisos: 0
```

## Hallazgos

| de | sobre | qué | qué hice |
|---|---|---|---|
| `/code-review` alto | `f70703cc..82b2f641` | importante: `AHORA` se fija al importar; si entre la recolección y el caso pasa más de una hora, `en_la_gracia` vence sola | arreglado en `05ca7f71`: cada cuenta lleva un desfase desde que se siembra. Sonnet lo revisó: nada |
| Sonnet alto | `a17011d1..f70703cc` | la gracia no estaba fijada: una de 4 a 6 días daba verde | arreglado en `82b2f641`; 6 y 8 dan rojo (arriba) |
| `/code-review` alto | `a17011d1..f70703cc` | detalles: la anotación de tipo y el timeout de la lectura | arreglados en `843a9e0e` y `b218105b` |
| Sonnet y Opus alto | `a17011d1..f70703cc` | menor: el borde exacto (`<` contra `<=`) no lo distingue ninguna prueba; la diferencia es de un microsegundo | riesgo 1 |
| Opus alto | `a17011d1..f70703cc` | menor: las otras copias de la regla y el perfil con lo guardado | D279 |
| Sonnet alto | `a17011d1..f70703cc` | menor: una cancelada con el período terminado se ve `canceled`, aunque ya no tiene acceso | riesgo 2 |
| Sonnet alto | `a17011d1..f70703cc` | menor: la prueba decide el acceso con `_billing_vigente`, no con `get_current_user` | riesgo 3 |
| `/code-review` alto | `a17011d1..f70703cc` | ya estaba: `cohort-retention` usa el estado guardado; el panel dice «past_due hasta <fecha pasada>» | riesgos 4 y 5 |
| `/code-review` alto | `82b2f641..05ca7f71` | detalle: `_cobro` arma cada cuenta sólo con estado y fin; un campo que se sume a `COBROS` se perdería | no lo cambio: hoy no hay otro campo |

Opus, además, comparó la regla vieja y la nueva (260 casos) y miró los llamadores del valor devuelto,
el integrante con el estudio borrado y las fechas sin zona: nada.

## Riesgos

1. **El borde exacto.** `fin == ahora` y `fin == ahora − 7 días` no tienen caso: cambiar `<` por `<=`
   queda en verde. Bajo: es un microsegundo.
2. **Una cancelada terminada se ve `canceled`**, no `past_due`. Es lo que guarda y lo que decide el
   acceso (`tiene_acceso`), que la deja pasar sólo hasta el fin del período. Bajo.
3. **El acceso en la prueba** se decide con `_billing_vigente`, que es lo que usan las rutas con cobro;
   `get_current_user` vence aparte (D279). Bajo.
4. **`cohort-retention`** (`admin_router.py:342`) sigue con el estado guardado. Ya estaba; no es acceso.
5. **El panel** muestra «past_due hasta <fecha pasada>» para una vencida (`dev_dashboard.html:422`).
   Se entiende, pero el «hasta» de una vencida es el fin que pasó. Bajo; cambiarlo es pantalla.
6. **`billing_service.py` lo toca también la Técnica ahora** (ADMIN-CREDITOS-1, primer tramo, según
   `NOW.md`). Lo mío ahí: `BILLING_GRACE_DAYS_ACTIVE` y `cobro_efectivo`, juntos antes de `vigente`
   (`billing_service.py:145-163`). Si su tramo cambia esa zona, el merge choca; la regla no cambia.

## No corrido

- `e2e_maria.sh`: no toqué `static/v2`.
- Los sabotajes de otras piezas, salvo `cobro_corte1.sh` (lo pide la revisión fuerte).
- Un reloj simulado para la deriva de `AHORA`: el arreglo se sostiene leyendo el código y con la vuelta de
  Sonnet.

## Comandos para vos

Desde la raíz del repo, con el venv del proyecto en `PY`:
```bash
PY=/ruta/al/venv/bin/python
T="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $PY -m pytest -q --no-cov -p no:cacheprovider"
# 1. chequeo-6: «producto +28/−26» y «avisos: 0»
python3 docs/pm/herramientas/chequeo-6.py a17011d1 05ca7f71
# 2. verde: «134 passed»
git worktree add -q --detach /tmp/d278-verde 05ca7f71 && (cd /tmp/d278-verde && $T tests/test_admin_usuarios1.py tests/test_admin_solo_admin.py tests/test_cobro_corte1.py | tail -1); git worktree remove --force /tmp/d278-verde
# 3. rojo con la lista de antes: «1 failed, 8 passed», y difieren prueba_vencida, fuera_de_la_gracia y de_estudio_vencido
git worktree add -q --detach /tmp/d278-rojo 05ca7f71 && (cd /tmp/d278-rojo && git checkout a17011d1 -- proyecto_maria/routers/admin_router.py && $T tests/test_admin_usuarios1.py | grep -E "^E     \{|passed|failed" | tail -4); git worktree remove --force /tmp/d278-rojo
# 4. guion propio: «sabotajes sin rojo: 0»
PY=$PY bash scripts/testing/sabotajes/admin_usuarios1.sh 05ca7f71 | tail -1
```
Ya corridos por mí, con esta salida: el 1, `producto +28/−26` · `avisos: 0`; el 2, `134 passed, 19
warnings in 58.57s`; el 3, las tres líneas `E` y `1 failed, 8 passed, 5 warnings in 2.15s`; el 4,
`sabotajes sin rojo: 0`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U (/respondio), prendida por la PM al asignar D278 (b). PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `5af7e43d` (plan de ADMIN-CREDITOS-1 aceptado: la Técnica toca `billing_service.py` y `models.py` ya, `main.py` y `admin_router.py` después de D278 (b)); timbre con send_message, priority next. Aceptadas: las de antes (… CATALOGO-PAIS-2 sobre `9459a0d4`; ADMIN-USUARIOS-1 sobre `b06b47fa`, D278 (b); los dos `/security-review` sin hallazgos, leídos). Entregada: D278 (b) sobre `05ca7f71` (base `a17011d1`), informe en este archivo, esperando veredicto; D279 abierta (las otras copias de la regla de vencido y el perfil con lo guardado: recomiendo (b), cola de limpieza y riesgo escrito). Lo pedido en D278 (b) (sí de Emi 20/11): la lista de usuarios del panel muestra el cobro efectivo, misma regla que el acceso y no una copia de `_vencer_si_corresponde`; el plan no se toca; mirar no escribe; prueba con la familia como datos que compara lista y acceso, y otra que lee la base por otra conexión; rojo una vez con el arreglo revertido; puertas chequeo-6, anclas_perdidas, suite completa desde worktree limpio, /code-review, Sonnet alto, y por tocar `_vencer_si_corresponde` revisión fuerte: `cobro_corte1.sh` y Opus alto. Después: la Técnica hace ADMIN-CREDITOS-1 sobre lo mío; hasta el veredicto, `admin_router.py` es mío. No hay pieza «apenas entregues». Próxima D: D280. Lecciones (además de las del historial de este archivo): el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; cada número del informe sale de un log, también las cuentas de líneas («25 ROJO» eran 24); `anclas_perdidas.py <SHA>` después de tocar líneas que anclan sabotajes, también de guiones ajenos, y antes de lanzar la suite (los tests leen los guiones); el `LIKE` de SQLite no distingue mayúsculas: `PRAGMA case_sensitive_like` en el caso; un adversario revisó un SHA: lo cambiado después se dice; un ancho en `ch` depende de la fuente: medir con Inter y con Liberation Sans (`fuente/arial.conf`); una regla de pantalla se mide en cada ancho de disposición; un sabotaje que falla en el primer elemento de una lista no prueba los de atrás; no editar `scripts/` mientras corre un guion de sabotaje: cortar las puertas y relanzarlas sobre el SHA nuevo; un valor puesto por código no dispara `input`; un campo de texto pierde los saltos de línea; puertas con `setsid nohup`; horas, sólo de `date -u`; los comandos para la PM se prueban antes de escribirlos; un borrador con huecos no se sube; el `TestClient` arranca la app y el arranque vence lo vencido: sembrar después de entrar; una fecha de prueba fijada al importar se gasta mientras corre la suite: contarla desde que se siembra; un commit que sale de un hallazgo pasa otra vez por adversario y `/code-review`. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe. Letra ancha: tabla U+FF01..FF5E, no NFKC («№» da Noruega).
