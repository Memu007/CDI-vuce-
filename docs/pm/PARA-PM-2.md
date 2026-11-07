# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ENTRADAS-1, devolución: **entregada**. Sólo pruebas sobre `589fd0b`. SHA `c839197` más el informe (2026-11-07)

| Qué | SHAs |
|---|---|
| Pruebas y sabotajes de la devolución | `30b8b78`, `c839197` |
| Merge de tu rama (sólo `docs/pm/`) | `32cad6e` |
| Producto de ENTRADAS-1 | sin cambios desde `589fd0b` |
| **Ojo: en la rama, no en esta entrega** | `273c9a7`, `1f0bfb0`, `e725f0e` son ABUSO-2 **en curso, sin entregar**. `1f0bfb0` toca `main.py` y `core/limites_auth.py` (login y recuperar usuario, nada de entradas). Revisalos cuando entregue ABUSO-2 |
| Informe | el commit `docs:` que sigue a `c839197` |

**Resultado.** Cada mutación de tu devolución, y las que encontró el adversario
de esta vuelta, ahora da rojo en el caso que tiene que caer.
`sabotajes/entradas1.sh c839197` da `BASE  | en verde`, 32 `ROJO` y
`sabotajes con falla: 0`. En `589fd0b` eran 22.

**Nada para decidir.** D99 sigue con Emi. D100–D104 ya las decidiste. Próxima
D libre: D105.

## Tus cuatro puntos

1. **La clave no vuelve en ninguna respuesta.** Cada vía (reset, cambio,
   registro, alta de estudio) exige `clave not in r.text` en dos casos:
   - en el 422 de una clave mala;
   - en un caso nuevo, el 422 de un **campo obligatorio que falta**. Ahí el
     `input` de pydantic es el cuerpo entero, con la clave adentro.

   Los sabotajes «el rechazo de la clave la repite» (mete la clave en `msg`),
   «el 422 repite la clave que llegó» y «el 422 repite el cuerpo de un campo
   que falta» dan rojo. El último deja pasar `input` cuando es un dict.
2. **73 bytes justos.** Hay dos filas:
   - `73_bytes`: 73 ASCII;
   - `multibyte_en_el_borde`: 71 ASCII + «ñ», que son 73 bytes en 72
     caracteres.

   «El tope deja pasar 73 bytes» (`> 73`) y «el tope cuenta caracteres y no
   bytes» (`len(v)`) dan rojo en su fila. El de 72 justos sigue entrando.
3. **Lo guardado y no sólo el código.** El caso de los textos lee la fila en
   la base y exige que no tenga NUL ni surrogate y que tenga «�». Pasa con el
   nombre del registro, el nombre del estudio y el nombre del perfil, para
   NUL, surrogate alto y surrogate bajo. Con eso, «el NUL no cuenta como no
   guardable» da rojo en SQLite
   (`…queda_con_reemplazo[registro_nombre-nul]`).
4. **`JSONResponse` contra `allow_nan=True`.** El caso del manejador trae dos
   errores como datos, cada uno con lo que puede pasar:
   - surrogate en `msg`: nunca puede cortar. Tiene que salir JSON estricto
     que contenga «Xx»;
   - `NaN` en `ctx`: puede cortar con un `ValueError` que no sea
     `UnicodeError`. Si responde, tiene que ser JSON estricto.

   Antes, el `except ValueError` se tragaba el `UnicodeEncodeError` de
   `JSONResponse`, y por eso ese sabotaje daba VERDE. Ahora «el 422 sale con
   la respuesta común» da rojo en `[surrogate_en_msg]` y «el 422 escribe NaN»
   da rojo en `[nan_en_ctx]`.

## Lo que sumé por el adversario de esta vuelta

- **Surrogate bajo.** Una fila `\udfff` en claves y en textos. El sabotaje «el
  surrogate bajo cuenta como guardable» acorta la regex a `\ud800-\udbff` y
  da rojo en `[reset-surrogate_bajo]`.
- **Ítems de agrupar.** Una fila `agrupar_surrogate`. El sabotaje «los ítems
  de agrupar sin validar» pasa `list[TextoCodificable]` a `list[str]` y da
  rojo en `[agrupar_surrogate]`.
- **Campo que falta.** El caso nuevo del punto 1.

## Autorrevisión

| Quién (modelo, esfuerzo) | Rango | Hallazgo | Qué hice |
|---|---|---|---|
| adversario-sonnet-alto | `589fd0b..30b8b78` | 1. El sabotaje `JSONResponse` seguía VERDE: el `except ValueError` se tragaba el `UnicodeEncodeError` | Arreglado en `c839197`, ahora rojo |
| | | 2. Un campo obligatorio que falta repite el cuerpo, clave incluida, en `input` | Caso nuevo en `c839197`, rojo con su sabotaje |
| | | 3. Sin fila de surrogate bajo | Fila y sabotaje en `c839197` |
| | | 4. `item_ids` sin caso; login y la rama dict de `_guardable_en_pg` sin caso | `item_ids`: fila y sabotaje. Login (`LoginRequest.username` ya existía) y la rama dict (de la Dev 1): no son de esta pieza, no los probé |
| | | 5. Las filas NUL de `CAMPOS` (el caso de 400 de usuario, email e invitación) no discriminan en SQLite | Queda. Las mira `entradas1_postgres.py`, y el NUL de lo guardado lo distingue el caso del punto 3 |
| | | 6. Sin caso de emoji (4 bytes) en el borde de 72 | Queda. El borde ya lo distingue la «ñ» de 2 bytes, y la regla mide `len(v.encode())` igual para cualquier ancho |
| | | 7. El caso de la clave mira que el login con `"Clave-1!"` siga andando. Es un prefijo fijo y frágil si cambia la clave de prueba | Queda, como riesgo de mantenimiento bajo |

## Puertas

| Puerta | Salida |
|---|---|
| `tests/test_entradas1.py` | `79 passed in 23.40s` (10 casos) |
| `test_entradas1.py` + `test_user_profile_coverage.py` | `93 passed in 23.20s` |
| Sabotajes `entradas1.sh c839197` | `BASE  | en verde`, 32 `ROJO`, `sabotajes con falla: 0`. Bash avisa 4 veces `warning: command substitution: ignored null byte in input`: es la salida de pytest con el NUL dentro de `$(…)`. No cambia el resultado |
| Postgres `entradas1_postgres.py` (55432) | `fallas: 0` |
| `chequeo-6.py 589fd0b c839197` | abajo. Todo el producto y los 3 avisos son de `1f0bfb0` (ABUSO-2, sin entregar) |
| grep de historia de §6 sobre `589fd0b..c839197` | vacío |
| Suite completa | **no corrida** en esta vuelta. Sólo cambian dos archivos de prueba de la pieza, y el producto de ENTRADAS-1 no cambió. La corro sobre el SHA de ABUSO-2, que sí toca producto |
| `compileall`, `smoke_friccion.sh`, `ataque_aislamiento.sh` | **no corridos**: esta vuelta no toca producto |

## chequeo-6

```
chequeo-6 589fd0b..c839197: avisos para mirar, no un veredicto
producto +38/−18
arnés +430/−41
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/limites_auth.py: 103 → 121
  AVISO comentario nuevo de 5 líneas: proyecto_maria/core/limites_auth.py:107 (§6: una o dos)
  proyecto_maria/main.py: 11991 → 11993
  AVISO comentario nuevo de 3 líneas: proyecto_maria/main.py:1844 (§6: una o dos)
  AVISO comentario nuevo de 4 líneas: proyecto_maria/main.py:3215 (§6: una o dos)
avisos: 3
```

`git log 589fd0b..c839197 -- proyecto_maria` da un solo commit, `1f0bfb0`
(ABUSO-2). Los tres comentarios largos los acorto en ABUSO-2, antes de
entregarla. Lo que es de esta vuelta da `producto +0/−0`.

## Riesgos

- **R1, baja.** El hallazgo 7 del adversario: el prefijo `"Clave-1!"` está
  fijo en el caso de la clave.
- **R2, baja.** Las filas NUL de `CAMPOS` sólo distinguen en Postgres. La
  suite no las cubre, las cubre el script de PG.
- Siguen los R de la entrega anterior: D100 (UI), D102 (bcrypt) y D104 (500
  previos, ahora ENTRADAS-2).

## Comandos copiables

```bash
# desde la raíz, con el venv del proyecto
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
rm -f test.db; python -m pytest -q --no-cov -p no:cacheprovider tests/test_entradas1.py
#   → 79 passed
PY=$(command -v python) scripts/testing/sabotajes/entradas1.sh c839197
#   → BASE  | en verde, 32 ROJO, «sabotajes con falla: 0» (tarda más de 10 minutos)
python scripts/testing/entradas1_postgres.py postgresql://cdi@127.0.0.1:55462/postgres
#   → «fallas: 0»
git diff 589fd0b c839197 --stat -- tests/test_entradas1.py scripts/testing/sabotajes/entradas1.sh
#   → 2 files changed, 122 insertions(+), 26 deletions(-)
```

## Archivos de producto tocados

Ninguno en esta vuelta. ABUSO-2 en curso: `proyecto_maria/main.py` y
`proyecto_maria/core/limites_auth.py`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797wNM priority next. ENTRADAS-1 devolución ENTREGADA en c839197 (sólo pruebas: clave fuera de la respuesta incluido el campo que falta, 73 bytes y ñ en el borde, lo guardado sin NUL/surrogate, manejador 422 distingue JSONResponse de allow_nan; 32 ROJO, 0 fallas). Sigue: ABUSO-2 (ya en rama 273c9a7/1f0bfb0/e725f0e; falta acortar 3 comentarios de chequeo-6, adversarios, /code-review high, /security-review, suite completa sola, compileall, D105 «tercero silencia el recuperar de otro») → rojo de despacho1b → ENTORNO-2 → D100 → ENTRADAS-2. Próxima D libre D105. Reglas de Emi: nada se publica sin su «dale» para el SHA (no propongo SHA), nunca main, nunca force/amend de lo pusheado, sin secretos ni datos reales, subagentes hasta alto sin Fable, no uso advisor, Postgres local 55432.
