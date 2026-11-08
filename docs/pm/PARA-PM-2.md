# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## RESET-3 (D132 a): **entregada** en `8fda3d2` (2026-11-08), base `2fba5c9`

| SHA | qué |
|---|---|
| `3d0083a` | fix: tope de 3 pedidos de reset por hora por cuenta; CHANGELOG |
| `4458020` | test: casos, arnés de Postgres y `reset3.sh` |
| `1a02fc2` | refactor: reset y recuperar usan un solo `_tope_por_cuenta` (hallazgo de `/code-review`) |
| `d07c004` | test: el login correcto no toca la clave de reset por cuenta; anclas del arnés al helper |
| `0c0b541` | test: una IP inventada con forma de clave de cuenta no gasta el tope (rojo sobre `d07c004`) |
| `e187466` | fix: la clave pasa a `reset-cuenta:<usuario>`, fuera de las `reset:` de la IP; CHANGELOG |
| `8fda3d2` | test: arnés y casos con la clave nueva y el sabotaje de la colisión |
| este commit | docs: el informe |

**Producto +14/−7** (7 netas).

AVISOS-2b (`ffd1b95..aa115f4`, aceptada) está arriba de RESET-3 en la rama;
la base de esta pieza es `2fba5c9` y su punta `8fda3d2`.

Qué hace:

1. `request_password_reset` (`main.py`) cuenta los pedidos de la cuenta con
   `limites_auth.contar(db, "reset-cuenta:<usuario>", 3600)`, antes de trabar
   la cuenta. Desde el cuarto de la hora contesta el mismo
   `{"message": "Si el email existe, se envió un link."}`, pero no crea el
   link ni manda el mail. Los pedidos pueden llegar de IPs distintas.
2. El tope se cuenta antes del `with_for_update`: `contar` hace commit y
   soltaría la traba de RESET-1. Lo cubre el sabotaje de Postgres.
3. Reset y recuperar usuario usan el mismo `_tope_por_cuenta`. El chequeo
   estaba escrito dos veces.
4. La clave es `reset-cuenta:` y no `reset:cuenta:`. Sin un proxy que
   agregue su entrada, la IP la escribe el cliente en `X-Forwarded-For`.
   Con `reset:cuenta:` como clave, una IP inventada `cuenta:<usuario>` caía
   en el contador de esa cuenta. Además, un bloqueo de 24 h por IP en esa
   misma clave dejaba sin links a la cuenta. Lo reprodujo un adversario:
   «COLISION 200 mails: 0 links: 0». Arreglado en `e187466`, con el rojo
   antes en `0c0b541`.

## Decisiones

**D138. Quien conoce el email de una cuenta la deja sin links.** Cuatro
pedidos por hora alcanzan, desde cualquier IP, y se puede sostener. La
persona recibe la misma respuesta y no le llega nada. Es lo mismo que ya
pasa con recuperar usuario desde ABUSO-2.

- (a) Se acepta como en recuperar: el tope es lo que pidió D132 (a).
- (b) Se sube el tope (por ejemplo, a 10 por hora). Hace falta más trabajo
  para sostener el bloqueo, pero deja pasar más links por hora.
- (c) Al llegar al tope se le manda a la cuenta un único aviso por hora, sin
  link, que diga que se pidieron muchos cambios de clave.

Recomiendo **(a)**:

- (b) sólo corre el número;
- (c) es un mail nuevo, con su texto y su propio tope, y conviene que lo
  pida Emi.

Si decís (c), es una pieza aparte.

Siguen abiertas:

- **D131**, de EMAIL-1: va a Emi.
- **D136**: no traigo tu rama hasta que me avises que INTEGRAR-1 está
  aceptada.

Supuestos que podés rechazar:

- El tope por cuenta depende de `limiter.enabled`, igual que el de
  recuperar. El de la IP no depende.
- Un pedido para un email que no existe no cuenta en ninguna clave de
  cuenta: no hay cuenta.

## Comandos

```bash
git checkout 8fda3d2
# negativos de RESET-3: «BASE | ... 74 passed», 7 ROJO en SQLite, «BASE | Postgres: fallas: 0», 1 ROJO en Postgres, «sabotajes sin rojo: 0»
PY=python scripts/testing/sabotajes/reset3.sh 8fda3d2
# negativos de ABUSO-2, que comparten limites_auth y recuperar: «BASE | en verde», 20 ROJO, «fallas: 0»
PY=python scripts/testing/sabotajes/abuso2.sh 8fda3d2
# producto +14/−7, «avisos: 0»
python docs/pm/herramientas/chequeo-6.py 2fba5c9 8fda3d2
# los casos de la pieza solos: 0 failed
python -m pytest -q --no-cov tests/test_abuso1.py -k reset
```

Los sabotajes de `reset3.sh`, cada uno con lo que dice su rojo:

| sabotaje | dice |
|---|---|
| sin el tope por cuenta | `FAILED tests/test_abuso1.py::test_reset_tres_por_hora_por_cuenta_aunque_cambie_la_ip`, «el cuarto pedido de la hora mandó el mail» |
| el tope cuenta la IP | ídem |
| la clave de la cuenta cae dentro de las de la IP | `FAILED tests/test_abuso1.py::test_reset_una_ip_inventada_no_gasta_el_tope_de_la_cuenta`, «una IP inventada gastó el tope de la cuenta» |
| el tope deja pasar cuatro | `…test_reset_tres_por_hora…`, «el cuarto pedido de la hora mandó el mail» |
| el tope corta después de crear el link | ídem, «el cuarto pedido de la hora creó un link» |
| la ventana dura menos de una hora | ídem, «a los 59 minutos ya mandó otro» |
| la ventana dura dos horas | ídem, «pasada la hora no volvió a mandar» |
| (Postgres) el tope se cuenta con la cuenta trabada | «FALLA \| el tope por cuenta no suelta la traba» |

## Puertas

Todo sobre `8fda3d2`, desde un worktree limpio.

| puerta | salida exacta |
|---|---|
| `pytest -q --no-cov --timeout=120` | `5408 passed, 335 skipped, 3 xfailed, 102 warnings in 1059.97s (0:17:39)`, salida 0 (AVISOS-2b da más casos porque suma los suyos arriba) |
| `compileall -q proyecto_maria` | sin salida, salida 0 |
| `smoke_friccion.sh` contra uvicorn | `[FAIL] POST /api/ui/event`, salida 1: el rojo conocido desde ABUSO-1 que arregla SMOKE-1 (D137 a). Como se corta en el primer evento, el resto del smoke **no corrió** |
| `ataque_aislamiento.sh` (`PUERTO=18799`) | `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`, `✅ PUERTA G3 PASADA`, salida 0 |
| `reset3.sh 8fda3d2` | `BASE  \| ... 74 passed, 5 warnings in 29.33s`, 7 ROJO en SQLite, `BASE  \| Postgres: fallas: 0`, 1 ROJO en Postgres, `sabotajes sin rojo: 0` |
| `abuso2.sh 8fda3d2` | `BASE  \| en verde`, 20 ROJO, `fallas: 0` |
| `reset1_postgres.py` (PG 16 descartable) | `BASE  \| en verde`, `fallas: 0`, salida 0 |

## Hallazgos de la autorrevisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| `adversario-opus-alto` sobre `4458020` | Opus, alto | colisión de `reset:cuenta:<u>` con `reset:{ip}` cuando el cliente escribe `X-Forwarded-For`: un bloqueo de 24 h dejaba sin links a la cuenta (media-baja). Reproducido: «COLISION 200 mails: 0 links: 0» | arreglado en `e187466`; rojo antes en `0c0b541`; sabotaje en `8fda3d2` |
| ídem | ídem | la ventana fija deja pasar hasta 6 links en 3601 s (baja) | riesgo, abajo; igual en recuperar |
| ídem | ídem | el caso no distingue «por cuenta» de «por email normalizado» (baja) | riesgo de cobertura, abajo |
| ídem | ídem | diferencia de tiempo por el SMTP síncrono (baja) | ya existía; no reproducido |
| `adversario-sonnet-alto` sobre `4458020` | Sonnet, alto | quien conoce el email deja a la cuenta sin links (media) | **D138** |
| ídem | ídem | tiempo de cuenta existente frente a inexistente: 71–75 ms contra 17–18 ms con el simulador (baja) | ya existía; riesgo, abajo |
| `/code-review high` sobre `2fba5c9..4458020` | Opus, alto (subagente) | el chequeo del tope estaba dos veces (§6) | arreglado en `1a02fc2` |
| ídem | ídem | `test_abuso2` no listaba la clave nueva entre las que el login no toca | arreglado en `d07c004` |
| ídem | ídem | `response = mensaje` era un alias del dict compartido | sacado en `1a02fc2` |
| ídem | ídem | el tope por cuenta depende de `limiter.enabled` y el de la IP no | supuesto, arriba; igual en recuperar |
| ídem | ídem | contar antes del re-select gasta un cupo si el email cambia en medio (baja) | riesgo, abajo; es la carrera ya aceptada en RESET-1 |
| ídem | ídem | DoS de ventana fija sostenido | igual que el de Sonnet: D138 |
| ídem | ídem | el caso de reset copia casi entero el de recuperar, en vez de un caso con la ruta como dato (§6) | **queda**: unirlos cambia el nombre de `test_s6_recuperar_…`, que anclan `abuso1.sh`, `abuso2.sh` y `email1.sh`. Lo propongo para la cola de limpieza |
| ídem | ídem | `_links_de_reset` repite en SQL lo que `test_email1._tokens_de` lee por el ORM | queda: es de prueba; va con el anterior a la cola |
| ídem | ídem | `reset3.sh` copia el armado de los demás sabotajes en vez de usar `_entorno_comun.sh` | queda: es el mismo armado que el resto de los scripts de sabotaje |
| `/security-review` sobre `2fba5c9..8fda3d2` | Sonnet, alto (subagente) | sin hallazgos. Excluido por alcance: agotar el tope de una cuenta ajena | D138 |

## Riesgos

- **D138:** cuatro pedidos por hora dejan a una cuenta sin links.
- Ventana fija: alrededor del cambio de hora pasan hasta 6 links en poco
  más de una hora. Igual en recuperar.
- El caso no distingue el tope «por cuenta» del tope «por email
  normalizado». Hoy dan lo mismo y sólo divergen si una cuenta cambia de
  email o con D38.
- Si la cuenta cambia de email entre contar y trabar, el pedido gasta un
  cupo y no crea link. Es la carrera de RESET-1.
- El tiempo de respuesta sigue distinguiendo una cuenta que existe de una
  que no: el SMTP es síncrono. Esto ya existía antes.
- Con `limiter.enabled` apagado no hay tope por cuenta (igual que en
  recuperar). En producción está prendido.

## chequeo-6

```
chequeo-6 2fba5c9..8fda3d2: avisos para mirar, no un veredicto
producto +14/−7
arnés +213/−3
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12078 → 12085
avisos: 0
```

## Archivos de producto

`proyecto_maria/main.py` (`request_password_reset`, `recover_username` y el
helper `_tope_por_cuenta`), `CHANGELOG.md`.

## Lo que sigue

SMOKE-1 (D137 a), después OBSERVABILIDAD-1.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (send_message next, «Dev MARIA: …»), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. RESET-3 entregada en 8fda3d2 (informe en este archivo, base 2fba5c9); AVISOS-2b aceptada sobre aa115f4 sin integrar. Abiertas: D131 (de EMAIL-1, va a Emi), D136 (decidida: no traigo tu rama hasta que INTEGRAR-1 esté aceptada), D138 (DoS del tope por cuenta). D137 (a) decidida: SMOKE-1. La próxima D libre es la D139. Sigue SMOKE-1, después OBSERVABILIDAD-1, después ORG-1+D40 y D102. Nunca main, nada se publica sin el «dale» de Emi para el SHA, sin secretos, sólo datos inventados.
