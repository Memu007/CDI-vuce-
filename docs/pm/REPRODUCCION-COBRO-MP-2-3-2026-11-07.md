# Reproducción de COBRO-MP-2 vuelta + COBRO-MP-3 (2026-11-07)

PM principal. Rama `claude/dev-tecnica`, entrega `cb740f3`, producto
`4f1822f..6ecfe06` (sin cambios de cobro hasta `cb740f3`), informe `a06c0c8`.

**Veredicto: devolución de pruebas.** El producto se comporta como dice el
informe, pero cinco cambios del producto que rompen la seguridad de la firma,
quién toca a quién o el plazo único dejan todas las pruebas en verde.

## Lo que coincide con el informe

| Qué | Salida |
|---|---|
| `chequeo-6.py 4f1822f 6ecfe06` | `producto +157/−101`, `AVISO producto suma 56 líneas netas` (explicado en el informe), historia vacía, `avisos: 1` |
| `chequeo-6.py db31e0e cb740f3` | `producto +0/−0`, `arnés +12/−6`, `avisos: 0` |
| pruebas de cobro (mp1, mp1_cde, mp1_h, mp1_i, mp1_vuelta2, mp2, mp3, corte1, g7) | `420 passed, 3 warnings in 233.68s` |
| `cobro_mp2_postgres.py`, base propia `pm_mp3_esc` | salida 0, 16 OK, `fallas: 0` |
| `cobro_mp3.sh cb740f3` | 13 ROJO, `sabotajes con falla: 0`, `salida 0` |
| `cobro_mp2.sh cb740f3` | en curso al escribir esto (21 ROJO de 66, ninguna falla hasta ahí) |

Negativos propios, con MP simulado:

| Caso | Resultado |
|---|---|
| aviso firmado de pago aprobado | 200, la cuenta queda activa |
| el mismo aviso firmado otra vez | 200 «payment_id ya procesado», sin cambios |
| `data.id` con un «0» adelante | 200 «ya procesado» |
| `v1=…, ts=…` en otro orden, `data.id` entero | 200 «ya procesado» |
| `v1` en mayúsculas | 401 |
| cuerpo que no es UTF-8 | 401 |

## Mutaciones que ninguna prueba ve (reproducidas por la PM)

Árbol `/tmp/cdi-pm/rev-mut` en `cb740f3`, un cambio por vez. Pruebas:
`test_cobro_mp1/mp2/mp3`, `test_org1`, `test_g7_cobro`,
`test_mp_webhook_signature`, `test_webhook_ipn`, más `test_admin2` y
`test_prelaunch_block2/3` en a, b y c.

| | Cambio en `proyecto_maria/main.py` | Salida |
|---|---|---|
| a | borrar `if not MP_WEBHOOK_SECRET: return False` | `199 passed` y `119 passed` |
| b | comparar sólo `expected[:8]` con `received_v1[:8]` | `199 passed` y `119 passed` |
| c | sacar `User.organization_id == org.id` al buscar a quién sacar | `199 passed` y `119 passed` |
| d | `fail_after(_TOPE_MP)` por llamada, en vez del plazo único `hasta` | `211 passed` |
| e | reactivar con `con_sid` vacío | `211 passed` |

Qué deja pasar cada una (PoC del adversario Sonnet alto; a, b, c y e
también con el código real dan el rechazo correcto):
- a: sin secreto, un aviso firmado con clave vacía pasa y se consulta MP.
- b: una firma con los 8 primeros caracteres reales pasa (32 bits).
- c: la dueña del estudio A saca a un usuario del estudio B y le cancela en
  MP su suscripción pendiente (con el código real, 404).
- d: cancelar con dos pendientes y MP lento contesta 200 a los 2,4 s en vez
  de 503 al tope; con candado tomado, el peor caso pasa de 15 s a varios
  topes.
- e: quien abrió la que paga no puede reactivar si el estudio quedó
  cancelado y su suscripción sigue anotada (403 en vez de 200).

## Adversarios

**Opus alto** (producto, Postgres propio): seis hallazgos. Los cinco
reproducidos ya estaban como riesgos en el informe (hilos abandonados que
sueltan su lugar, PUT abandonado, preapproval huérfana, 8 lugares
compartidos con los avisos, X-Forwarded-For = D66). Nuevo y bajo, por
código: «Próximo cobro» con la pendiente de otro miembro (`main.py:3236`).
Nuevo y con camino de hoy: con el PUT abandonado, cancelar contesta «tu plan
sigue igual» y MP sí cancela (`main.py:2100`, lo mismo al sacar en `10085` y
en el checkout); el perfil muestra «Próximo cobro» y no habrá cobro.

**Sonnet alto** (mutaciones de prueba): 19 mutaciones, 8 en rojo. De las 11
verdes, las cinco de arriba son devolución. `_TOPE_MP = 900`, `60/hour`,
`CapacityLimiter(39)`, `.match` en vez de `.fullmatch`, clave global del
límite y `cancelar_corta_acceso(db_user)` quedan como riesgos.

## No corrido

- Suite completa sobre `cb740f3`: no hace falta para una devolución; se corre
  sobre la vuelta.
- `cobro_mp2.sh` todavía corriendo al escribir esto.
