# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ABUSO-2, devolución: **entregada**. Sólo pruebas y sabotajes, en `22a2c4b`, `b6ad266` y `1f79a8e`, más este informe (2026-11-07)

| Qué | SHAs |
|---|---|
| Pruebas y sabotajes | `22a2c4b`, `b6ad266`, `1f79a8e` (sólo `tests/test_abuso2.py` y `scripts/testing/sabotajes/abuso2.sh`) |
| Producto | ninguno: `producto +0/−0` |
| Informe | el commit `docs:` que sigue a `1f79a8e` |
| Base | `0c4893b` |

**Resultado.** Las cinco mutaciones que pediste dan rojo, cada una en el caso de su causa, y `abuso2.sh` termina con `fallas: 0` (salida abajo).

**Cómo quedaron los casos**, un caso por causa, con la familia como datos:
- `test_login_correcto_perdona_solo_los_fallos_de_su_cuenta`: 16 filas. Cada fila es una lista de pasos y cuántos 401 quedan antes del 429. Las filas nuevas:
  - `dos_logins_seguidos`: dos logins correctos perdonan una sola vez.
  - `propios_vencidos_con_la_ip_viva`: lo propio vencido no se resta.
  - `los_dos_olvidan_al_dia`, `la_cuenta_recuerda_un_dia` y `la_ip_recuerda_un_dia`: la cuenta y la IP olvidan juntas, a las 24 h y no antes.
  - `fallos_con_el_email`: los fallos tipeando el email se perdonan al entrar con el usuario.
- `test_un_login_correcto_no_cambia_otras_claves` lee la tabla entera antes y después del login correcto. Sólo cambia la fila de la IP, y de ella sólo `cuenta`, que baja en lo propio. No cambian `bloqueado_hasta` ni `vence`, ni las otras claves: otra IP, otra cuenta, recuperar (cuenta e IP), registro (hora y día), reset y cambio de clave.

Nada para decidir. D105 y D106 ya están decididas (a). Próxima D libre: D107.

## Tus mutaciones, en rojo

Copiado de la salida de `abuso2.sh 1f79a8e`:

| Tu mutación | Sabotaje | Rojo |
|---|---|---|
| M2, `update` sin `where clave == clave` | «descontar resta en todas las claves» | `ROJO`, `test_un_login_correcto_no_cambia_otras_claves` |
| M5, `select` en vez de `delete … returning` | «descontar lee lo propio y no lo borra» | `ROJO`, `test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[dos_logins_seguidos]` |
| M1, sin purga | «descontar resta lo propio vencido» | `ROJO`, `test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[propios_vencidos_con_la_ip_viva]` |
| M8b, la cuenta olvida a las 48 h | «la cuenta olvida a las 48 h» | `ROJO`, `test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[propios_vencidos_con_la_ip_viva]` |
| M15, la IP tiene otra ventana | «la IP olvida a las 48 h» | `ROJO`, `test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[los_dos_olvidan_al_dia]` |

Salida entera:

```
Preparing worktree (detached HEAD 1f79a8e)
BASE  | en verde
ROJO  | el login correcto borra todos los fallos de la IP: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[otra_cuenta]»
ROJO  | los fallos de la cuenta no se cuentan aparte: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[solo_propios]»
ROJO  | la cuenta se cuenta sin la IP: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[fallos_propios_desde_otra_ip]»
ROJO  | la cuenta se cuenta por el texto tipeado: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[fallos_con_el_email]»
ROJO  | la cuenta se cuenta en una ventana fija: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[fallos_propios_de_mas_de_un_dia]»
ROJO  | descontar borra lo propio pero no lo resta de la IP: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[mitad_y_mitad]»
ROJO  | descontar deja la IP en negativo: dice «FAILED tests/test_abuso2.py::test_descontar_no_deja_la_ip_en_negativo»
ROJO  | el login cuenta los fallos de la IP con el tope de recuperar: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[ajeno_tras_el_bloqueo]»
ROJO  | descontar resta en todas las claves: dice «FAILED tests/test_abuso2.py::test_un_login_correcto_no_cambia_otras_claves»
ROJO  | descontar resta también en reset: dice «FAILED tests/test_abuso2.py::test_un_login_correcto_no_cambia_otras_claves»
ROJO  | descontar resta también en el tope diario de registro: dice «FAILED tests/test_abuso2.py::test_un_login_correcto_no_cambia_otras_claves»
ROJO  | descontar alarga el olvido de la IP: dice «FAILED tests/test_abuso2.py::test_un_login_correcto_no_cambia_otras_claves»
ROJO  | descontar lee lo propio y no lo borra: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[dos_logins_seguidos]»
ROJO  | descontar resta lo propio vencido: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[propios_vencidos_con_la_ip_viva]»
ROJO  | la cuenta olvida a las 48 h: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[propios_vencidos_con_la_ip_viva]»
ROJO  | la cuenta olvida a las 23,5 h: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[la_cuenta_recuerda_un_dia]»
ROJO  | la IP olvida a las 48 h: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[los_dos_olvidan_al_dia]»
ROJO  | la IP olvida a las 23,5 h: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[la_ip_recuerda_un_dia]»
ROJO  | el tope de recuperar va por el texto pedido: dice «FAILED tests/test_abuso1.py::test_s6_recuperar_usuario_corta_en_silencio_por_email»
ROJO  | Postgres: el tope de recuperar va por el texto en minúsculas de Python: dice «FALLA | cinco variantes del mismo email mandan tres mails»
fallas: 0
```

## Autorrevisión

| Quién (modelo, esfuerzo) | Hallazgo | Qué hice |
|---|---|---|
| `/code-review high` | 1. Una ventana de 23,5 h no se veía | Filas `la_cuenta_recuerda_un_dia` y `la_ip_recuerda_un_dia`, con su sabotaje para cada una |
| | 2. Un `select` seguido de un `delete` aparte no es atómico | No se prueba: haría falta concurrencia en Postgres. Queda como R1 |
| | 3. `descontar` podía cambiar otras columnas de la fila de la IP | El caso compara la fila entera. Sabotaje «descontar alarga el olvido de la IP» |
| | 4. `la_cuenta` repetía una fila | La hice más estricta |
| | 5. El paso `bien` no tenía mensaje en el assert | Arreglado |
| | 6. `_filas` repite el lector de `test_abuso1.py` | Queda: son 5 líneas, y unificarlo toca otro archivo |
| | 7. El docstring no nombraba el cambio de clave | Arreglado |
| | 8. El encabezado del script estaba viejo | Arreglado |
| adversario-sonnet-alto (sobre `22a2c4b`) | Base 17 passed. Vio las cinco mutaciones tuyas, ventanas de 25 h y 23 h, el olvido por omisión en 48 h y 12 h, n ± 1, la purga con margen y un `update` que también toca cambio de clave, recuperar, login y cuenta | — |
| | a. Las claves ajenas no tenían `reset:{ip}` (`main.py:1777`) ni `registro:d:{ip}` (`main.py:3381`). Un `update` que también tocara esas claves quedaba verde | Las sumé como datos en `1f79a8e`, con un sabotaje para cada una |
| | b. Que `descontar` alargue `vence` quedaba verde | Ya lo veía `b6ad266`, que salió después de su corrida: sabotaje «descontar alarga el olvido de la IP», en rojo. Que `descontar` ponga `bloqueado_hasta` en 0 es casi equivalente, porque una IP bloqueada no llega a `descontar` |
| | c. Armar la clave de cuenta con lo tipeado en vez de `user.username` quedaba verde, porque nadie entraba con el email. Fallaría para el lado seguro, no abriría nada | Fila `fallos_con_el_email` y sabotaje «la cuenta se cuenta por el texto tipeado», en `1f79a8e` |
| | d. Mover `descontar` antes de la verificación de email quedaba verde, porque el módulo la apaga | Queda, R4 |
| | Equivalentes: `>= n` en vez de `> n`, y poner 0 en vez de borrar | — |

## Puertas (sobre `1f79a8e`)

| Puerta | Salida |
|---|---|
| `tests/test_abuso2.py` | `18 passed in 37.01s`, sobre el árbol antes de cortar una línea del docstring. Sobre `1f79a8e` mismo lo corrió la `BASE` de `abuso2.sh`, en verde |
| `abuso2.sh 1f79a8e` con `PG_URL` | `BASE  \| en verde`, 20 `ROJO`, `fallas: 0` |
| `chequeo-6.py 0c4893b 1f79a8e` | abajo, `avisos: 0` |
| grep de historia de §6 | vacío |
| Suite completa | **no corrida**. Sólo cambian dos archivos de prueba; el producto no cambia |

```
chequeo-6 0c4893b..1f79a8e: avisos para mirar, no un veredicto
producto +0/−0
arnés +86/−9
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

`producto +0/−0`.

## Riesgos

- **R1, baja.** La atomicidad de `delete … returning` frente a dos logins correctos simultáneos no tiene prueba: necesita concurrencia en Postgres. Lo que sí está probado es que dos logins seguidos perdonan una vez.
- **R2, baja (de antes de esta pieza, lo marcaste vos).** Con cuentas duplicadas por mayúsculas en el email, recuperar manda 3 mails por cuenta.
- **R3, baja (de antes, lo marcaste vos).** El tope de recuperar usa una ventana fija.
- **R4, baja.** Ningún caso de este módulo ve el orden entre `descontar` y la verificación de email, porque la apaga para medir sólo el bloqueo.
- **Proceso.** La primera corrida de `abuso2.sh` sobre `b6ad266` coincidió con las pruebas del subagente: fueron dos suites a la vez. La corrida que vale es la de `1f79a8e`, sola.

## Comandos copiables

```bash
# desde la raíz, con el venv del proyecto y el Postgres local en 55432
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
rm -f test.db; python -m pytest -q --no-cov -p no:cacheprovider -W ignore tests/test_abuso2.py
#   → 18 passed
PY=$(command -v python) PG_URL=postgresql://cdi@127.0.0.1:55432/postgres scripts/testing/sabotajes/abuso2.sh 1f79a8e
#   → BASE en verde, todas las líneas ROJO, «fallas: 0»
python3 docs/pm/herramientas/chequeo-6.py 0c4893b 1f79a8e
#   → producto +0/−0, avisos: 0
```
