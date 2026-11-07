# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ABUSO-2: **entregada**. Pruebas y sabotajes en `8ad47ee`, más este informe (2026-11-07)

| Qué | SHAs |
|---|---|
| Rojos | `273c9a7`, `f99f48e`, `972567f` |
| Producto | `1f0bfb0`, `42d024c`, `979a83a`, `e6372e7`, `59778f9` |
| Sabotajes y script de Postgres | `e725f0e`, `ced8431`, `e77fc16`, `8ad47ee` |
| CHANGELOG | `db6ecea` (la entrada de ABUSO-2 ya estaba) |
| Informe | el commit `docs:` que sigue a `8ad47ee` |
| Base de la pieza | `ccf0f65` |

**Resultado.**
- Un login correcto resta de la IP **sólo** lo que esa cuenta falló desde esa IP. No borra los fallos contra otras cuentas o usuarios inexistentes, tampoco después de un bloqueo vencido, y nunca baja de cero.
- El tope de recuperar usuario (3 por hora) va por cuenta encontrada. Así, cinco formas del mismo email que Postgres toma por igual mandan como máximo tres mails.

**Para decidir: D105.** Hoy, cualquiera que conozca el email de otra persona puede gastarle el tope de recuperar usuario de esa hora; ese pedido vuelve con el mismo `mensaje` y no manda mail. Antes pasaba lo mismo por texto y ahora pasa por cuenta.
- (a) Queda así y lo anotamos como riesgo.
- (b) Pieza aparte: el tope por cuenta se cuenta además por IP de origen, o un tope alto por cuenta sumado a uno bajo por IP.

Recomiendo **(a)**:
- el daño es que llega un mail menos por hora a quien lo pidió;
- (b) vuelve a abrir el salto del tope con muchas IPs, que es justo lo que esta pieza cierra.

D99 sigue con Emi. D100–D104 ya las decidiste. Próxima D libre: D106.

## Cómo quedó

- **Contadores del login.** Tienen dos claves, `login:{ip}` y `cuenta:{username}:login:{ip}`. Las dos usan `sumar_fallo(exacta=True)`: cuentan cada fallo, y la ventana se corre a 24 h desde el último fallo. Lo de la cuenta olvida con la misma regla que la IP, así el perdón no queda corto ni largo.
- **Login correcto.** Llama a `descontar(clave_ip, clave_cuenta)`. Esa función borra la fila de la cuenta con `DELETE … RETURNING` y resta ese número de la IP, con piso 0. El bloqueo ya puesto no se toca.
- **Recuperar usuario.** Primero mira el tope por IP y después busca la cuenta. Cuenta en `recuperar:cuenta:{username}`. Pasado el tope, contesta el mismo `mensaje` que cuando el email no existe.

## Autorrevisión

| Quién (modelo, esfuerzo) | Hallazgo | Qué hice |
|---|---|---|
| adversario-opus-alto | 1. Después de un bloqueo vencido, `sumar_fallo` volvía la cuenta de la IP a `tope`: el login correcto restaba lo propio de una cuenta más chica y borraba fallos ajenos | Arreglado en `979a83a`: la IP se cuenta con `exacta`. Fila `ajeno_tras_el_bloqueo`, en rojo con su sabotaje |
| | 2. Una IP compartida (NAT) queda bloqueada por los fallos de otro | Queda. Es lo que pide la pieza: los fallos ajenos no se perdonan. Riesgo R1 |
| | No encontró otra forma de que el login correcto perdone fallos ajenos, ni regresión en reset | — |
| `/code-review high` | #1, #3, #7, #10 | Arreglados con rojo previo: `e6372e7` (descontar resta sólo lo propio), `59778f9` (la cuenta olvida como la IP; la IP no queda en negativo) y los comentarios en `42d024c` |
| | #2. Dos fallos a la vez pueden pasar el chequeo del bloqueo | Queda, R2. Cada uno igual suma su fallo |
| | #4. Los dos `sumar_fallo` son dos commits y no uno | Queda, R3 |
| | #5. Pasado el tope, recuperar contesta sin mandar mail y por eso más rápido | Queda, R4 |
| | #6. El perdón se hace antes de `abrir_sesion` (viene de antes) | Queda, R5 |
| | #8 (altitud), #9 (eficiencia) | Fuera de alcance: no son defectos |
| `/security-review` (subagente general) | Sin hallazgos. Miró choques de claves (`:` en el usuario, `_clave` cortada a 120 con sha256), inyección SQL, enumeración en login y en recuperar, y si el perdón puede pasarse de lo propio | — |

No pude reconstruir del registro, palabra por palabra, el texto de cada número de `/code-review`. La tabla trae lo que anoté en su momento.

## Sabotajes (`scripts/testing/sabotajes/abuso2.sh 8ad47ee`, con `PG_URL` en 55432)

```
BASE  | en verde
ROJO  | el login correcto borra todos los fallos de la IP: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[otra_cuenta]»
ROJO  | los fallos de la cuenta no se cuentan aparte: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[solo_propios]»
ROJO  | la cuenta se cuenta sin la IP: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[fallos_propios_desde_otra_ip]»
ROJO  | la cuenta se cuenta en una ventana fija: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[fallos_propios_de_mas_de_un_dia]»
ROJO  | descontar borra lo propio pero no lo resta de la IP: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[mitad_y_mitad]»
ROJO  | descontar deja la IP en negativo: dice «FAILED tests/test_abuso2.py::test_descontar_no_deja_la_ip_en_negativo»
ROJO  | el login cuenta los fallos de la IP con el tope de recuperar: dice «FAILED tests/test_abuso2.py::test_login_correcto_perdona_solo_los_fallos_de_su_cuenta[ajeno_tras_el_bloqueo]»
ROJO  | el tope de recuperar va por el texto pedido: dice «FAILED tests/test_abuso1.py::test_s6_recuperar_usuario_corta_en_silencio_por_email»
ROJO  | Postgres: el tope de recuperar va por el texto en minúsculas de Python: dice «FALLA | cinco variantes del mismo email mandan tres mails»
fallas: 0
```

## Puertas (sobre `8ad47ee`; el commit del informe no toca código)

| Puerta | Salida |
|---|---|
| `test_abuso2.py` + `test_abuso1.py` | `83 passed in 46.79s` |
| Suite completa, sola | `5107 passed, 335 skipped, 3 xfailed in 812.43s (0:13:32)`, salida 0. Deja avisos `Task was destroyed but it is pending!` de asyncio al cerrar, que no cambian el resultado |
| `compileall -q proyecto_maria` | salida 0 |
| grep de historia de §6 sobre `ccf0f65..8ad47ee` | vacío |
| `chequeo-6.py ccf0f65 8ad47ee` | abajo, `avisos: 0` |
| `smoke_friccion.sh`, `ataque_aislamiento.sh` | **no corridos**. La pieza toca el login y recuperar usuario, que son autenticación pero no datos de clientes ni descargas, que es lo único que cubre el ataque. El login y la sesión los cubren los casos de arriba |

**Sobre el rojo de `despacho1b`.** En esta corrida de la suite completa,
`test_las_hojas_leidas_antes_del_corte_dan_sus_productos` **pasó**. El rojo es
intermitente o depende del orden, y en esta vuelta no se reprodujo. Es la
próxima pieza: lo diagnostico ahí, no lo doy por resuelto.

## chequeo-6

```
chequeo-6 ccf0f65..8ad47ee: avisos para mirar, no un veredicto
producto +35/−24
arnés +458/−41
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/limites_auth.py: 103 → 117
  proyecto_maria/main.py: 11991 → 11988
avisos: 0
```

`producto +35/−24`, 11 netas: no pasa de 20.

## Riesgos

- **R1, media.** Una IP compartida (oficina con NAT) se bloquea por los fallos de otra persona. Es la regla que pide la pieza.
- **R2, baja.** Pedidos simultáneos pueden pasar el chequeo del bloqueo. Cada uno suma su fallo y desde el quinto la ventana vuelve a bloquear.
- **R3, baja.** Los dos `sumar_fallo` del login hacen commit por separado. Si el proceso se corta entre los dos, la IP queda con un fallo más que la cuenta, y eso nunca perdona de más.
- **R4, baja.** Por el tiempo de respuesta de recuperar usuario se puede saber si el email existe o si pasó el tope: con mail o sin él, la respuesta tarda distinto. Viene de antes. Sale aparte si lo querés.
- **R5, baja.** El perdón se hace antes de `abrir_sesion`, como antes. Si `abrir_sesion` falla, la cuenta ya quedó perdonada.
- **R6, baja.** Un `:` en el username no puede chocar con otra clave, porque la IP no puede traer `login:`. Lo vio `/security-review`.
- D105, arriba.

## Comandos copiables

```bash
# desde la raíz, con el venv del proyecto
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
rm -f test.db; python -m pytest -q --no-cov -p no:cacheprovider tests/test_abuso2.py tests/test_abuso1.py
#   → 83 passed
PY=$(command -v python) PG_URL=postgresql://cdi@127.0.0.1:55462/postgres scripts/testing/sabotajes/abuso2.sh 8ad47ee
#   → BASE  | en verde, 9 ROJO, «fallas: 0»
python3 docs/pm/herramientas/chequeo-6.py ccf0f65 8ad47ee
#   → producto +35/−24, avisos: 0
git diff ccf0f65 8ad47ee --stat -- proyecto_maria
#   → 2 files changed (core/limites_auth.py, main.py)
```

## Archivos de producto tocados

`proyecto_maria/main.py` (login y `recover_username`) y
`proyecto_maria/core/limites_auth.py` (`sumar_fallo` con `exacta`, y `descontar`).

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797wNM priority next. ABUSO-2 ENTREGADA en 8ad47ee + informe (perdón sólo de lo propio con exacta y descontar con piso 0; recuperar por cuenta; 9 ROJO, 0 fallas; suite 5107 passed; D105 recomendación (a)). Sigue: rojo de despacho1b (en esta suite pasó: intermitente u orden, diagnosticar) → ENTORNO-2 (D98, `_es_desarrollo`) → D100 → ENTRADAS-2. Próxima D libre D106. Reglas de Emi: nada se publica sin su «dale» para el SHA (no propongo SHA), nunca main, nunca force/amend de lo pusheado, sin secretos ni datos reales, subagentes hasta alto sin Fable, no uso advisor, Postgres local 55432. Corte de rutinas 2026-11-08 15:50 UTC.
