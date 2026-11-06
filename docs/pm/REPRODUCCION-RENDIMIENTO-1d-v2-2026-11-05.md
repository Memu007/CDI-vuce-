# RENDIMIENTO-1d, vuelta de la devolución: `558c941` (2026-11-05, PM)

**Veredicto: aceptada, sin integrar.** Base `724484c`. Debajo vienen los mismos
commits sin aceptar que en `ca87d82` (SESION-1, ABUSO-1, OBSERVABILIDAD-1,
SUFIJOS-2, ORG-1) y `e0b8626` de técnica: se integra con ellos.

## Diff de producto

Sólo `proyecto_maria/core/despacho_lector.py`, `_main`: la salida del hijo pasa
por `_MEDIO_PAR.sub("�", …)` y se escribe en bytes UTF-8. `chequeo-6`:
`producto +4/−1`, `arnés +81/−1`, historia vacía, `avisos: 0`.

## Lo que corrí sobre `558c941`

| Qué | Salida |
|---|---|
| `pytest tests/test_rendimiento1d.py tests/test_rendimiento1c.py` | `27 passed, 5 warnings in 74.42s` |
| `rendimiento1d.sh 558c941` | 12 `ROJO`, `fallas: 0` |
| `chequeo-6.py 724484c 558c941` | `avisos: 0` |
| grep de historia de §6 | vacío |

## Mi ejemplo, distinto del de la devolución

Otro par de glifos en el mismo renglón: `DBFF` + `€`, `DFFF` + un par válido
`D83DDE00` (😀), `D83D` + `é`; y el hijo con `PYTHONIOENCODING` en `ascii` y en
`cp1252` (la Dev probó `latin-1`).

- `558c941`: `texto` y `leer` devuelven `COSA � € INVENTADA`,
  `COSA � 😀 INVENTADA`, `COSA � é INVENTADA`; con `ascii` y `cp1252`, `rc 0` y
  el texto completo. El par válido vuelve entero.
- `724484c`: `UnicodeEncodeError: 'utf-8' codec can't encode character '\udbff'
  … surrogates not allowed`; se pierde la lectura.

## Evidencia extra sobre `aaed661` (la versión devuelta)

`rendimiento1d.sh aaed661`: `VERDE | el texto vuelve a la app sin tope: la
prueba no lo vio`, `fallas: 1`. Confirma el punto 2 de la devolución. Esa
corrida se cortó después (el proceso murió); la suite sobre `aaed661` no se
corrió, y ya no hace falta.

## Qué no corrí

- Suite completa: no. La Dev informa `4903 passed, 355 skipped, 3 xfailed` en
  un worktree limpio en `558c941`. El cambio es de 4 líneas, en la salida del
  proceso aparte, y lo cubren los 27 casos y los 12 sabotajes de arriba.
- Subagentes adversariales: no, por el tamaño; la causa ya la habían atacado
  en la devolución.
- `rendimiento1c.sh` y `rendimiento1.sh` sobre `558c941`, corridos después:
  `rendimiento1c` 17 sabotajes, `sabotajes con falla: 0`; `rendimiento1` 11
  sabotajes, `sabotajes con falla: 0`.

## Hallazgo 2 del `/code-review` de la Dev

Un par válido partido en dos glifos vuelve como «��». Lo dejo así: hace falta
un PDF armado de esa manera, y `leer` ya hacía lo mismo.
