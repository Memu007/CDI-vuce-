# Reproducción de CLIENTE-1c — 2026-10-27

Sobre `4452b22` (informe `dbe7c4a`, merge `df07dda` sólo de documentos;
diff de revisión desde `c820c74`). La PM corrió la suite, el sabotaje y sus
negativos en un worktree limpio (`/tmp/cdi-pm/wt-4452b22`). Un revisor
adversarial con contexto nuevo (Opus alto) trabajó con una base propia.
Todo local, con sintéticos, sin Gemini ni servidor Postgres.

**Veredicto:** CLIENTE-1c, **con devolución**. D15 (b), D16 (b), la regla
única de la fecha y los 12 rojos de la suite están bien. Falla la nota de
CLIENTE-1b que venía en la pieza: con un `--base` que SQLAlchemy acepta, el
script todavía muestra la clave, o se cae con un traceback en vez del
mensaje limpio.

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| Suite completa sobre `4452b22`, desde base limpia | `3135 passed, 102 skipped, 2 xfailed, 92 warnings in 325.87s`, rc=0 |
| `PY=… bash scripts/testing/sabotajes/cliente1c.sh 4452b22` | 25 ROJO, «sabotajes sin rojo: 0», rc=0 |

La suite da 0 rojos: los 11 de presupuesto los cierra `2ff3262` (las
pruebas de CLIENTE-1c devuelven las operaciones que gastan del usuario de
prueba) y `test_guardar1` ahora espera la ficha vacía para la fecha con
hora, que es lo que dice D15 (b).

### Negativos propios (el script de fechas con `--base`)

Claves inventadas, puerto 1 cerrado en local. Todas rc=2.

| `--base` | Lo que muestra |
|---|---|
| `postgresql://u:pa/ss@127.0.0.1:1/db` | «No se pudo revisar la base u:pa/ss@127.0.0.1:1/db: ConnectionRefusedError…»: **la clave entera** |
| la clave con `?` o `#` en vez de `/` | «…la base u:pa: …»: una parte de la clave |
| `u:s3cr@t`, `u:clave%2Fok` | sin la clave, pero «Name or service no*** known», «ConnectionRef***sedError»: el usuario «u» tapado dentro del texto |

## Lo que probó el revisor (Opus alto)

- **Reproducido por la PM:** una clave con un carácter de ancho completo
  que la normalización convierte en un delimitador de URL hace que la
  segunda lectura del texto lance un `ValueError` con el usuario, la clave
  y el host, desde dentro del manejador que debía taparla: traceback, rc=1.
  Con `[` en la clave, traceback (`Invalid IPv6 URL`), rc=1, sin la clave.
- **Sin hallazgo:** clave con `%40` o espacio, `?password=`, `[::1]`,
  puerto 99999, host que no resuelve, `?sslmode=`, `?ssl=`,
  `?connect_timeout=`, drivers `mysql` y `psycopg2`, acentos, `%ZZ`, `%00`,
  sqlite con un archivo que no es base.
- **Fecha:** 29 cadenas raras contra el alta y el generador: el alta nunca
  acepta algo que el generador rechace, y `fecha_inic_activ_sirve` coincide
  con el generador. La operación con tipos raros devuelve 200 y rellena el
  domicilio igual. La importación deja vacías y listadas `15.03.2015`,
  `March 15 2015`, `42073` y otras. El conflicto no pisa la ficha; el
  deshacer devuelve `deleted 1, restored 1`. El valor
  `<img src=x onerror=…>` sale en JSON y la pantalla lo pone con
  `textContent` (lectura de código, no en navegador).
- **Decidido, no hallazgo:** la fecha de la operación con hora ya no se
  copia (antes se cortaba a 10 caracteres). Es D15 (b) y la pantalla sólo
  manda `type=date`.

## Hallazgos

| # | Qué | Gravedad | Qué se hace |
|---|---|---|---|
| H1 | **La clave de `--base` en el error.** El dónde y los secretos salen de una segunda lectura del texto (`urlsplit` en `_donde_y_secretos`), no de lo mismo que conecta (`make_url`). Cuando las dos lecturas no coinciden, sale la clave o un traceback. | seguridad, alta | devolución |
| H2 | **El enmascarado rompe el texto.** Se reemplaza cada aparición del usuario en todo el mensaje («ConnectionRef***sedError»). Misma causa: lo que se tapa no es lo que leyó la conexión. | cosmético | en la misma devolución |
| H3 | Año `0001` aceptado por el alta, la operación y el generador. Consistente entre los tres. | baja | se anota |

## Limpieza

Sin `uvicorn` ni `pytest` de la revisión andando al terminar. El sabotaje
borra su worktree. Los ayudantes del revisor quedaron en `/tmp/cdi-pm/adv`,
fuera del repositorio.

---

# Vuelta de CLIENTE-1c — `3aba9c2` (2026-10-27)

Producto `7e43604`, `eda3755`, `2a21835`; pruebas `d0dcf04`, `f1cb25e`,
`009ad58`, `8359e53`; informe `807d562`; base de revisión `4452b22`. Entra
junto con ESTUDIO-1b (`REPRODUCCION-ESTUDIO-1b-2026-10-27.md`).

**Veredicto:** aceptada, con un punto que se suma a EXCEL-3f (H1-bis).

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| Suite completa sobre `3aba9c2`, worktree limpio | `3229 passed, 102 skipped, 2 xfailed, 93 warnings in 364.32s`, rc=0 |
| `sabotajes/cliente1c.sh 3aba9c2` | 37 de 37 en rojo («sabotajes sin rojo: 0») |
| `sabotajes/cliente1b.sh 3aba9c2` | 16 de 16 en rojo («sabotajes sin rojo: 0») |
| `git merge-base --is-ancestor 2ff3262 3aba9c2` | sí: entran los arreglos de los 12 rojos de la CI |

El revisor adversarial **no corrió** (presupuesto semanal). En su lugar, la
PM hizo el fuzz de abajo.

## La clave de `--base` (H1 de la devolución)

Ahora el dónde y los secretos salen de `make_url`, que es lo que conecta.
Fuzz de la PM: 4000 claves por forma, armadas como
`QZXW<sep>KJVB<sep>NMPL`, con separadores ASCII, de ancho completo,
escapados con `%`, espacio y tab. Se mira qué queda sin tapar cuando el
error repite la clave de distintas maneras:

| Lo que repite el error | Claves que se ven |
|---|---|
| la URL tal como se escribió | 0 de 4000 |
| la clave (cruda, `unquote`, `unquote_plus`, NFKC) | 0 de 4000 |
| host y base | 0 de 4000 |
| los valores de la consulta | 0 de 4000 |
| `url.render_as_string(hide_password=False)` | **113 de 4000** |
| `repr(url.query)` | 102 de 4000 (artificial, no cuenta) |

Ninguna excepción: siempre rc 2 y mensaje limpio.

**H1-bis.** SQLAlchemy 2.0.25 escribe la clave como
`quote(clave, safe=" +")`: deja el espacio y escapa lo demás. Una clave
que mezcla un espacio con otro carácter que se escapa no está entre las
formas que se tapan. Reproducido sobre `3aba9c2`:

```
'QZXW KJVB|NMPL' -> fallo: postgresql+asyncpg://***:QZXW KJVB%7CNMPL@db.local:5432/x
'QZXW KJVB"NMPL' -> fallo: postgresql+asyncpg://***:QZXW KJVB%22NMPL@db.local:5432/x
'QZXW KJVB'      -> fallo: postgresql+asyncpg://***@db.local:5432/x
'QZXW|KJVB'      -> fallo: postgresql+asyncpg://***@db.local:5432/x
```

La prueba de la Dev usa justamente `render_as_string`, pero sólo con claves
de un separador. Su afirmación es más ancha que su evidencia. La exposición
real es baja: ni los drivers ni `str(url)` repiten la clave. Por eso no es
devolución, pero el script **no se corre contra producción** hasta que
entre el arreglo en EXCEL-3f.

## D25 (b), la fecha en la importación

Las pruebas de la Dev cubren «15/03/15», «01/01/50», DD-MM-AAAA, dígitos de
ancho completo, ISO con T y la celda de fecha de Excel
(«AAAA-MM-DD 00:00:00»). La PM leyó el merge de la importación: un valor
entrante vacío nunca pisa una fecha que ya está.
