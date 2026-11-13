# Reproducción de CUIT-PERFIL (2026-11-13)

Entrega de MARIA: base `fdaa2da`, casos `0dd23d7`, arreglo `31d14cf`,
entregado en `af396041` (su merge de mi rama), informe `9ed8b9a9`. Producto:
`PUT /api/user/profile` usa `cuit_valido` y contesta 400 si el verificador
no cierra. Revisado por la PM principal en un worktree en `af396041`.
Veredicto: **aceptada e integrada**.

| qué | salida |
|---|---|
| `chequeo-6.py fdaa2da af39604` | producto +4/−3, arnés +375/−25, historia vacía, 0 AVISO: igual que el informe |
| `git diff --stat b99ca0c af396041` (sus puertas corrieron sobre `b99ca0c`) | sólo `docs/pm/` y `tests/test_excel2d.py` de la Técnica, ya aceptado |
| pytest de la pieza y `test_excel2d.py` | `114 passed` |
| rojo: los casos de `af39604` con el `main.py` de `fdaa2da` | `5 failed`, los mismos cinco del informe |
| `sabotajes/cuit_perfil.sh` | 11 `ROJO`, `sabotajes sin rojo: 0`, rc=0 |
| los que mandan un CUIT al perfil en `tests/`: `test_estudio1`, `test_estudio1b`, `test_generar_maria_txt`, `test_maria7_rechazos_24_10`, `test_punta_a_punta1` | `201 passed, 2 xfailed` |
| `e2e_maria.sh` sobre `af396041` (carga `20111111112` por la API; `af396041` ya contiene mi rama `1de18f9d`) | `E2E MARIA OK`, rc=0 |
| pantallas sobre `af396041`: `cuit_perfil1`, `validacion1`, `cobro_corte1`, `cobro_mp1_v2`, `sesion1`, `orden1` | todas OK. `orden1` dio primero rc=124: saltó mi tope de 300 s (el del repo es 900) con 31 OK de 71; el texto «FALLA» de z4 salió al cortarse. Con 300 s nunca terminaba (un caso solo tarda 200 s). Sola con 900 s y la suite al lado: rc=0, 71 OK, z4 incluido, ~10 min |
| pytest entero sobre la unión `f1403811` (mi rama `1de18f9d` + `9ed8b9a9` + la Técnica `d9dd73bc`) | `6126 passed, 110 skipped, 3 xfailed`, rc=0, 19 min |

**Negativos de la PM** (archivo propio, fuera del repositorio, borrado):
`PUT` con dígitos arábigos orientales, `{"a":1}`, `true` y `20999999998`:
400 y queda el CUIT anterior. Con un nulo al final, letras, «CUIT 20-…», un
entero y una lista: 200 y queda `20111111112` limpio.

**Adversario** (Sonnet alto, contexto nuevo): el único camino que escribe
`User.cuit` es `main.py:2440`; ante el 400 hay rollback sin commit parcial;
un `PUT` sin la clave `cuit` guarda el resto. Encontró que `00000000000` da
200: `cuit_valido('00000000000')` da `True` (corrido por la PM; el `PUT` lo
corrió el adversario). El estudio y `review.js:36` lo aceptan igual: es de
`cuit_valido`, no de esta pieza. Riesgo anotado, sin código.

**z8 de `orden1` (`b99ca0c`, sólo arnés, no pedido).** Leído: quita las rutas
antes de cerrar el contexto, 4 líneas fuera de la función larga. Su forzado
(3/3 rojo antes, 3/3 verde después) **no lo reproduje**: el guion no quedó en
el repositorio. Aceptado por ser arnés y por la causa que describe.

**Supuestos de la Dev, aceptados.** Un perfil con un CUIT malo guardado no
guarda nada desde «Mi perfil» hasta corregirlo; el mensaje del 400; los datos
`20111111120` y `20111111189`.

**D235: (a), decidido por la PM.** El mismo TXT ya frena el CUIT del
importador con el verificador malo (`controles_maria.py:264`) y ESTUDIO-1 (✅)
lo rechaza al guardar el CUIT del estudio; `/generate_maria` (`main.py:5161`) sólo
cuenta 11 dígitos para el del perfil y para `cuit_agr`. Es la regla del
verificador que el TXT ya aplica, en el CUIT del `CDDTAGR` (obligatorio por
MARIA-7), que la saltea: pieza aparte,
después de SUFIJO-BORRADOR, que arranca con dos rojos (un TXT con el CUIT
malo guardado en el perfil y otro con `cuit_agr`). Cuántos perfiles tienen
hoy uno malo va en la nota del «dale»: quien lo tenga queda frenado al
generar.

No corrido: Postgres, y el forzado de z8.
