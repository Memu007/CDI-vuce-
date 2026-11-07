# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

> **RESET-2** ya la aceptaste (99d3f69, D93 a); gracias. D91/D92 quedan como
> ENTORNO-1, que arranco ahora. ABUSO-1 va encima, sobre la devolución de
> `43916a7`.

## ABUSO-1: **entregada**. Producto `1880c98`, `9ef6c73`, `55bf408`; pruebas `1119901`, `3f0eeab`, `cf45cd4`, `8a363eb`, `1b48774`; informe en el commit siguiente. SHA entregado `55bf408` (2026-11-07)

**Resultado.** Los cuatro puntos de la devolución tienen prueba que distingue
el defecto y sabotaje con rojo:

- **D44 (una sola conexión en el login).** Ya lo había arreglado `ce7cd9d`
  (SESION-1 v2), que está entre `43916a7` y mi base `1f48bb5`. No toqué
  producto para esto: sumé la prueba en PG que pediste. En
  `abuso1_motores.py`, 120 logins malos y 120 buenos a la vez contra PG
  local (55432) con `/health` consultado en paralelo:

  | Código | 120 malos | 120 buenos | `/health` |
  |---|---|---|---|
  | `55bf408` | `[401]` (500: 0) | `[200]` (500: 0) | 200 en 4.116 s y 5.896 s |
  | `ce7cd9d^` (2ª conexión) | `[401, 500]` (500: 93) | — | 200 en 0.06 s |
  | mutante: `limpiar` con conexión propia | `[401]` (500: 0) | `[200, 500]` (500: 96) | `HTTP Error 503` a 31.46 s |

  El mutante muestra por qué hacen falta los dos casos: el login malo pasa
  por `registrar`, el bueno por `limpiar`.
- **Punto 1 (duración).** Casos «a los 14 min sigue 429, a los 16 pasa» para
  el bloqueo por IP del login, el corte por IP de recuperar usuario y la
  ventana por email de recuperar (3600 s, «a los 59 min sigue, a los 61
  no»). Los mutantes «el bloqueo dura un minuto», «recuperar usuario: el
  corte por IP dura un minuto» y «la ventana por email es de un minuto» dan
  rojo.
- **Punto 2 (claves de 121 a 300 en PG).** Una IP de 100, 200, 287 y 332
  caracteres no rompe ninguna ruta con contador y se bloquea al quinto fallo
  en PG («una IP de N caracteres también se bloquea al quinto fallo», todas
  OK). En SQLite, `test_tabla_una_ip_larga_entra_en_la_clave`. El mutante
  «una clave de hasta 300 entra tal cual» (el `len(clave) <= 300`) da rojo.
- **Punto 3 (surrogate).** Un surrogate suelto o un NUL ya no dan 500 en
  `/auth/recover-username`, `/auth/request-password-reset`, `/auth/login`
  ni `/auth/reset-password`. Tampoco en el 422, que antes repetía lo que
  llegó y se caía al codificarlo. Lo cubre `test_un_surrogate_suelto_no_da_500`,
  con 12 entradas como datos de un solo caso.

**Producto +35/−20**, sólo en `main.py`:

- `TextoCodificable` valida con el `_guardable_en_pg` que ya existía, que
  subí de lugar en el archivo. Lo usan `LoginRequest.username`,
  `PasswordResetRequest.email`, `PasswordResetConfirm.token` y
  `RecoverUsernameRequest.email`.
- Un manejador de `RequestValidationError` arma el 422 en JSON ASCII.

Suma +15 netas, así que no hace falta la línea de §6 por pasar de 20.

### Supuestos (reversibles; rechazalos si no van)

1. **Más allá del correo.** La devolución nombraba el correo de recuperar
   usuario. Extendí lo mismo al usuario del login, al correo de reset y al
   token de reset-password, porque los cuatro daban el mismo 500 (rojo en
   `1119901` y `8a363eb`).
2. **El NUL también.** Se trata como el surrogate, porque PG lo rechaza
   igual.
3. **El 422 ASCII vale para todas las rutas**, no sólo las de auth. El JSON
   es equivalente, pero un carácter no ASCII sale como `\uXXXX`. Ninguna
   prueba de la suite dependía de eso (ver la fila de la suite en Puertas).

## Decisiones

- **D94 (seguridad media, fuera de ABUSO-1, te lo propongo como pieza).**
  Una contraseña de más de 72 bytes da **500** en reset (`main.py:1874`),
  cambio (`2458`), registro (`3414`) y `10515`. La causa: `hash_password`
  (`3151`) llama a `bcrypt.hashpw`, y bcrypt 5.0.0 levanta `ValueError:
  password cannot be longer than 72 bytes`. Esas validaciones tienen mínimo
  de 8 pero no máximo. Opciones:
  - (a) Tope de 72 bytes en UTF-8 en un solo validador que usen las cuatro
    rutas, con 400 y un mensaje claro.
  - (b) Prehash (sha256 → base64) antes de bcrypt. Cambia el formato y pide
    migración.
  - (c) Dejarlo.

  **Recomiendo (a)**: resta una rama a cada ruta y no toca los hashes ya
  guardados.
- **D95 (entorno de prueba, baja).** En SQLite, 120 logins a la vez dan
  «database is locked»: 12 de 120 malos y 7 de 120 buenos. En PG no pasa
  (cuadro de arriba), y producción es PG. Opciones:
  - (a) Dejarlo y anotarlo.
  - (b) Darle un `busy_timeout` al motor de prueba.

  **Recomiendo (a).**
- **D96 (robustez, baja).** El mismo surrogate en otros campos JSON
  (registro, `new_password`, otros formularios) todavía puede dar 500 al
  guardarlo, aunque el 422 ya no se cae. Opciones:
  - (a) Pieza chica que aplique `TextoCodificable` a los modelos de entrada
    que guardan texto.
  - (b) Dejarlo.

  **Recomiendo (a)**, después de ENTORNO-1.

Próxima D libre: D97.

## Rojo antes del arreglo

| Commit | Sobre | Salida |
|---|---|---|
| `1119901` (pruebas) | base `1f48bb5` | «6 failed, 60 passed»; los 6 son 500 con `UnicodeEncodeError` |
| `8a363eb` (pruebas) | `1880c98` | «6 failed, 6 passed, 60 deselected, 3 warnings in 1.13s», en el token de reset-password y en el 422 |
| `9ef6c73` (arreglo) | — | «72 passed, 3 warnings in 21.59s» |

Último rojo copiado de `rojo_cr.log`:
`FAILED tests/test_abuso1.py::test_un_surrogate_suelto_no_da_500[False-/auth/login-{"username": "a\ud800"}-422]`.

Los casos de duración (punto 1) y la clave larga (punto 2) no tenían rojo en
la base: el producto ya era correcto, y lo que faltaba era una prueba que
distinguiera el defecto. Sus rojos son los de los sabotajes.

## Autorrevisión

| Revisor | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| Adversario | Sonnet, alto | #1 el token de reset-password con surrogate da 500 | Arreglado (`8a363eb` → `9ef6c73`) |
| | | #2 el 422 repite la entrada y se cae | Arreglado (handler ASCII) |
| | | #3 otros campos JSON con surrogate | Va como D96 |
| | | #4 el mutante de `limpiar` sobrevive en SQLite | Muerto en PG (120 logins buenos) |
| | | #5 XFF y `TRUSTED_PROXY_HOPS`, #6 IPv6 | A riesgos, como pediste |
| `/code-review high` | — | #5 movida de un comentario de Mercado Pago | Comentario devuelto a su lugar (`55bf408`) |
| | | #6 largo de la IP de prueba | Uso 100 caracteres, que sí cruza el corte de 120 en la clave compuesta |
| | | #7 el hilo de `/health` usaba una espera fija | Ahora un `Event` |
| | | #9 la fórmula de la IP | Queda: la clave es `ruta:IP` y el corte se calcula sobre el total |
| `/security-review` | — | Ninguno de confianza alta | — |

En el diff completo `1f48bb5..55bf408` no hay nada fuera de la tarea, aparte
de los supuestos 1–3. El grep de historia de §6 da vacío.

## Riesgos / límites (sin tocar producto, como pediste)

- **XFF y `TRUSTED_PROXY_HOPS`.** El conteo por IP depende de que
  `TRUSTED_PROXY_HOPS` coincida con los saltos reales de Railway. Mal puesto,
  o todos comparten una IP o cada uno elige la suya.
- **IPv6 y puerto sin normalizar.** Un mismo cliente IPv6 rota dentro de su
  /64 y saca contadores nuevos.
- **Bordes de la duración.** Las pruebas miran los minutos 14 y 16 (y 59 y
  61), así que un mutante con un bloqueo de 14.5 min sobrevive. Tampoco hay
  caso para el rebloqueo después de que vence un bloqueo viejo.
- **Deadlock en PG con ventanas cortas.** 38 de 400 pedidos, con las
  ventanas achicadas a propósito. Con las ventanas de producción no lo medí.
- **Filas sin tope.** `limites_auth` crece con cada IP o email distinto
  hasta que vence; no hay purga con tope.
- **Telemetría.** Un token revocado todavía escribe un evento de telemetría.
- **Tiempo del login.** Un usuario existente tarda 0.673 s y uno inexistente
  0.010 s, por bcrypt, así que se puede enumerar usuarios por tiempo.
- **Truncado a 200.** El `StringDataRightTruncationError` con 200 sólo lo
  vi con el mutante. Con el producto, las IPs de 200, 287 y 332 dan OK.
- **`/health` lento bajo carga.** Tarda 4–6 s con 120 logins a la vez en PG
  (bcrypt ocupa los hilos). Está por debajo del tope de 15 s, pero no es
  instantáneo.
- **Choque con la Dev 1.** Subí `_guardable_en_pg` de lugar en `main.py`; si
  COBRO-MP toca esas líneas puede haber conflicto de merge. No cambié su
  cuerpo.
- **Sin prueba de duración ni de concurrencia** para la ventana
  `registro:h` ni para `verificar_clave_actual`.

## chequeo-6 (`1f48bb5` → `55bf408`)

```
chequeo-6 1f48bb5..55bf408: avisos para mirar, no un veredicto
producto +35/−20
arnés +182/−38
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11950 → 11965
avisos: 0
```

La base es `1f48bb5`, el merge de tu rama sobre el que arranqué. Con
`43916a7` como base entrarían 69 archivos (+3742/−24065) de otras piezas.

## Puertas (SHA entregado `55bf408`)

| Puerta | Resultado |
|---|---|
| `compileall -q proyecto_maria` | salida=0 |
| `pytest tests/test_abuso1.py` | 72 passed, 3 warnings in 21.59s |
| Motores PG (`abuso1_motores.py pg`, 55432) | «pg: todo OK» |
| Sabotajes (`abuso1.sh`) | 35 ROJO, «sabotajes sin rojo: 0» |
| Suite completa, worktree limpio en `55bf408` | Corriendo; la línea final va en el commit siguiente, antes del aviso |
| `smoke_friccion.sh`, `ataque_aislamiento.sh` | No corridos: el cambio es de validación de entrada en auth, sin datos ni permisos entre clientes |

## Comandos copiables

```bash
# Desde la raíz, con el entorno de prueba exportado
python -m pytest -q --no-cov tests/test_abuso1.py
#   → 72 passed
python scripts/testing/abuso1_motores.py pg postgresql://cdi@127.0.0.1:<puerto>/postgres
#   → última línea «pg: todo OK»; 120 malos [401] y 120 buenos [200], 500: 0
PY=python bash scripts/testing/sabotajes/abuso1.sh 55bf408
#   → 35 líneas ROJO y «sabotajes sin rojo: 0»
python docs/pm/herramientas/chequeo-6.py 1f48bb5 55bf408
#   → producto +35/−20, historia vacío, avisos: 0
```

## Archivos de producto tocados

- `proyecto_maria/main.py`

Arnés: `tests/test_abuso1.py`, `scripts/testing/abuso1_motores.py` y
`scripts/testing/sabotajes/abuso1.sh`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797WNM priority next. ABUSO-1 ENTREGADA en 55bf408 (producto 1880c98/9ef6c73/55bf408: TextoCodificable con _guardable_en_pg en login/reset/token/recover y 422 ASCII; D44 ya arreglado por ce7cd9d, probado en PG con 120 logins malos y buenos). D abiertas: D94 (bcrypt >72 bytes da 500 en reset/cambio/registro; recomiendo tope de 400), D95 (SQLite locked, dejar), D96 (surrogate en otros campos JSON). Próxima D libre D97. Sigue: ENTORNO-1 (D91/D92: login con ENVIRONMENT ausente, demo admin, hash como contraseña, webhook MP y link de reset en stdout). Corte el 2026-11-08 15:50 UTC. Reglas de Emi: nada se publica sin su «dale» para el SHA (no propongo SHA), nunca main, nunca force/amend de lo pusheado, sin secretos ni datos reales, subagentes hasta alto sin Fable, no uso advisor, Postgres local 55432.
