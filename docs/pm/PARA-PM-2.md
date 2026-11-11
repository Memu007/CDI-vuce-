# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## El armado para la PR: `d2f7f9c`

| qué | SHA |
|---|---|
| base (tu cabeza al arrancar, la de D166) | `db8f607` |
| **armado** | **`d2f7f9c7d7c3c8c15f693eb467766e469151dd3a`** |
| merge del armado en `claude/dev-maria` | `fcee205` (padres `5067149` y `d2f7f9c`) |

Está subido dentro de mi rama: `d2f7f9c` es el segundo padre de `fcee205`.
No subí ninguna rama aparte.

**Nada para decidir.**

`git log --oneline db8f607..d2f7f9c`:

```
d2f7f9c test: la memoria de la pantalla corre node en un fixture con tope, y tab/NBSP antes de la letra siguen rechazados
df3e26f test: el caso de la memoria junta las cuatro entradas antes de comparar
c6a8de6 test: la posición como la arma la pantalla aprende por guardar-uso, la operación, learn y el PUT
faf2b5f fix: la posición SIM con la letra separada por un espacio alimenta la memoria del cliente
```

## Lo único hecho a mano

`git cherry-pick d497551` chocó en `CHANGELOG.md` y sólo ahí. Dejé tu
`CHANGELOG.md` y sumé las 4 líneas de `d497551` arriba de NOMBRES-1. Los
otros tres commits entraron solos.

En el merge a mi rama chocó el mismo archivo: dejé el mío. El árbol no cambió.

## Las dos salidas, sobre `d2f7f9c` ya commiteado

Checkout aparte en `d2f7f9c`, sin cambios sin commit antes ni después.

| qué | salida |
|---|---|
| `tests/test_memoria_pantalla.py tests/test_guardar1.py` | `======================== 32 passed, 5 warnings in 5.92s ========================`, `exit=0` |
| `scripts/testing/e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.`, `exit=0` |

## Lo que dijiste que ibas a comprobar

`git diff db8f607 d2f7f9c -- proyecto_maria/` (las mismas líneas `+`/`−` que
`git show d497551 -- proyecto_maria/`, comparadas con `diff`):

```
-# de la posición SIM al final.
-_NCM = re.compile(r"[0-9]+(?:[.\- ][0-9]+)*[A-Z]?")
+# de la posición SIM al final; la pantalla la separa con un espacio.
+_NCM = re.compile(r"[0-9]+(?:[.\- ][0-9]+)*(?: ?[A-Z])?")
```

`chequeo-6`, corrido en el checkout del armado (`HEAD` es `d2f7f9c`):

```
chequeo-6 db8f607..HEAD: avisos para mirar, no un veredicto
producto +2/−2
arnés +87/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/services/client_memory.py: 305 → 305
avisos: 0
```

`git diff --stat db8f607 d2f7f9c`:

```
 CHANGELOG.md                             |  4 +++
 proyecto_maria/services/client_memory.py |  4 +--
 tests/memoria_pantalla.js                | 24 ++++++++++++++
 tests/test_guardar1.py                   |  7 ++++
 tests/test_memoria_pantalla.py           | 56 ++++++++++++++++++++++++++++++++
 5 files changed, 93 insertions(+), 2 deletions(-)
```

`CHANGELOG.md`: `1 file changed, 4 insertions(+)`. Las 4 líneas son las de
`d497551` (comparadas con `diff`).

## Comandos

```bash
git fetch origin claude/dev-maria
git log --oneline db8f607..d2f7f9c | wc -l                 # 4
git diff db8f607 d2f7f9c -- proyecto_maria/                # sólo la regex _NCM y su comentario
python docs/pm/herramientas/chequeo-6.py db8f607 d2f7f9c   # producto +2/−2, avisos: 0
git diff --shortstat db8f607 d2f7f9c -- CHANGELOG.md       # 1 file changed, 4 insertions(+)
git diff --stat db8f607 d2f7f9c                            # los 5 archivos de arriba
git rev-parse 'fcee205^{tree}' '5067149^{tree}'            # eb441dcc4fb39452df944a7b578fc3556cec9ee9 dos veces
git rev-parse d2f7f9c:proyecto_maria/services/client_memory.py f186ecf:proyecto_maria/services/client_memory.py
                                                           # 19348f5f… y 9d65c665…: no es el de f186ecf
```

## No corrido y riesgos

- **No corrido sobre `d2f7f9c`:** suite completa, `compileall`, smoke,
  `ataque_aislamiento.sh`, sabotajes. Pediste las dos salidas de arriba.
- El `client_memory.py` del armado no es el de `f186ecf`: lleva la regex
  sobre tu versión, sin CATALOGO-3. Las dos salidas pasan sobre esa
  combinación; nada más la cubre.
- Corrí las dos salidas con el adversario de PRESUPUESTO-CLIENTE-1 vivo en
  otro checkout. Antes de cada una miré que no hubiera `pytest`, `uvicorn` ni
  `node` corriendo. Las dos dieron verde a la primera.

## PRESUPUESTO-CLIENTE-1

No entregada. Sigue en `3936c24` (casos y arnés PG al día con la unión).
Sobre `3936c24`: `tests/test_datos1.py` 11 passed y, con el arreglo
revertido, `2 failed, 9 passed`; arnés PG16 `fallas: 0` y revertido
`fallas: 2`; `datos1.sh` 21 rojos, `sabotajes sin rojo: 0`. El adversario
está corriendo. Faltan su resultado, `/code-review`, `/security-review` y las
puertas sobre el SHA que entregue. Es lo que sigue.
