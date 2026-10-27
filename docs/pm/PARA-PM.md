# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Vuelta de CLIENTE-1c y ESTUDIO-1b: entregadas en `3aba9c2`

| Qué | SHA |
|---|---|
| ESTUDIO-1b, producto | `e226ac3`, `975d627` |
| ESTUDIO-1b, pruebas, pantalla y sabotajes | `009ad58`, `8359e53` |
| Vuelta de CLIENTE-1c, producto | `7e43604`, `eda3755` (import sin uso), `2a21835` (refactor) |
| Vuelta de CLIENTE-1c, pruebas y sabotajes | `d0dcf04`, `f1cb25e` |
| Merge de tu rama (`ce70729`), sólo `docs/pm/` | `3aba9c2` (lo que se entrega) |
| Informe | este commit |

Tu diff de revisión: `git diff 4452b22..3aba9c2`. Los merges de tu rama
traen sólo `docs/pm/`; mi canal `PARA-DEV.md` no cambió con `ce70729`.

**Nada para decidir.** Lo que elegí sin que se pidiera va en «Supuestos»,
para que lo puedas rechazar. Próxima D: D26.

## 1. Vuelta de CLIENTE-1c

- **H1, la clave de `--base`.** El script ya no lee la URL dos veces:
  conecta con la de `make_url` y tapa con esa misma (sin `urlsplit`). El
  lugar del error sale de `url.host`, `url.port` y `url.database`, y pasa
  igual por `_tapar`. Lo que no entiende `make_url` (por ejemplo el puerto
  «:abc») da el mensaje de uso con rc 2, nunca un traceback. Si tapar falla,
  sale «(sin detalle)» y el nombre del error: tampoco hay traceback.
  - Casos: claves con «/», «?», «#», «[», «]», «;», espacio, «%2F» y «@», y
    esos signos en ancho completo («／», «＠», «？», «＃»). Cada una corre el
    script como proceso, y otra vez con un error que repite la URL entera.
    Ninguna muestra la clave ni un traceback; todas dan rc 2.
- **H2, el usuario que rompía palabras.** Se tapa sólo el secreto entero
  (no pegado a letras o dígitos). Un usuario «u» ya no deja
  «ConnectionRef***sedError». Los pedazos del host que no son secretos
  quedan: una clave «1» no borra «127.0.0.1».
- **H3, el año `0001`:** anotado, no lo toqué.
- **D25 (b):** la regla vive en un solo módulo,
  `proyecto_maria/services/fecha_inic_activ.py` (`fecha_del_alta`). La usan
  el alta y la edición (`main.py`) y la importación
  (`migration_service.py`). En la importación, «15/03/15», «01/01/50»,
  DD-MM-AAAA y los dígitos de ancho completo quedan vacíos con el aviso de
  su fila.
- **Saqué código mío que no hacía nada (`2a21835`).** Tapar el lugar del
  error pedazo por pedazo sólo cambiaba la salida en URLs absurdas (la clave
  repetida dentro del host), y ahí no tapaba más. Lo encontré porque su
  sabotaje quedaba verde. Ahora es una línea:
  `donde = _tapar(_donde(url), secretos, visibles)`.
- **Sabotajes arreglados (`f1cb25e`).** En `cliente1c.sh` los textos
  esperados siguen los ids que escribe pytest (escapa lo que no es ASCII,
  `[２０１５-03-15]`). En `cliente1b.sh` tres sabotajes
  apuntaban a `main.py`: ahora apuntan al módulo de la regla.

## 2. ESTUDIO-1b

- **D23 (b):** generar con el CUIT del perfil se anota (tabla nueva
  `usos_cuit_perfil`, por cuenta) y compite con los estudios. La operación
  siguiente trae elegido lo último usado, estudio o perfil. Cuenta tanto
  `estudio_id: ""` como la falta del campo, y también el CUIT del perfil
  mandado en `cuit_agr` (la pantalla lo hace así). Los avisos y un TXT que
  no sale no cuentan.
- **`estudio_id`:** sólo `""` o la falta del campo es «sin estudio».
  «null», «None», «N/A», espacios, un null de JSON, un número o una lista
  dan 400, en `/generate_maria` y en `/generate_maria/avisos`.
- **Nombre del estudio:** rechaza los caracteres de formato invisibles
  (Unicode Cf: ancho cero, controles de dirección, BOM). Acepta acentos y
  otros alfabetos.
- **Pantalla (`scripts/testing/pantalla_estudio1b.js`):** estudio único
  elegido, perfil elegido a mano, la operación siguiente sin tocar el
  selector viene con el perfil, y sigue así al recargar.
- **Arreglo propio de `/code-review` (`975d627`):** con el CUIT del perfil
  borrado, su uso viejo dejaba elegida la opción sin CUIT. Ahora no cuenta.
- **`estudio1.sh`:** VALOR-1c (`3df999c`) movió el código y un sabotaje
  perdió su patrón; lo actualicé en `8359e53`.

## Supuestos (los podés rechazar)

CLIENTE-1c:
- La importación acepta la celda de fecha de Excel («2015-03-15 00:00:00»):
  sólo se le saca la hora `00:00:00`. Con otra hora (14:30) queda vacía y
  con aviso, como en la operación (D15 b). Antes de esta vuelta se
  importaba la fecha sin la hora.
- Se tapa de más, a propósito: el usuario, cada pedazo de lo de antes del
  «@», los valores de la consulta (`sslmode=require` sale `***`) y una clave
  corta igual al puerto. Si la base se llama igual que un pedazo, el lugar
  sale `host/***`.
- No se tapa un secreto pegado a letras o dígitos (`%40127.0.0.1`). Es lo
  que permite no romper palabras.
- Si el texto de la clave también es parte del host, el host puede
  mostrarlo: no se puede tapar uno sin el otro.

ESTUDIO-1b:
- El rechazo del nombre es por la categoría Cf entera, más amplio que la
  lista de la tarea. Otros caracteres en blanco que no son Cf (`U+3164`,
  `U+2800`) pasan.
- A la misma hora gana el perfil.
- Un estudio único cargado después de usar el perfil no gana: cargar no es
  usar.
- Un `estudio_id` con espacios alrededor da 400, no se recorta.
- Sin CUIT en el perfil, su uso viejo no cuenta.

## Riesgos

| Riesgo | Severidad | Detalle |
|---|---|---|
| `test_excel2` con la máquina cargada | baja, de entorno | Corrida junto a 4 sabotajes, `test_ocho_libros_con_la_primera_hoja_al_borde_del_tope…` dio rojo una vez. Sola: «2 passed», subida en 15.1 s contra un tope de 30 s. En la suite final, 0 rojos. No es de mi pieza. |
| `cuit_valido` acepta `00000000000` | baja | De ESTUDIO-1, no lo toqué. |
| Estudio borrado mientras se genera | baja | De ESTUDIO-1, no lo toqué. |
| Dos generaciones a la vez con el perfil, sin uso anterior | baja | Las dos insertan; la segunda da IntegrityError, se deshace y sólo se pierde esa anotación de uso. El TXT sale igual. |
| Un CUIT del perfil mal armado preseleccionado | muy baja | Sólo se mira que no esté vacío. No encontré camino: el perfil guarda sólo dígitos y el uso se anota recién después de un TXT con ese CUIT. |
| La URL de `--base` queda en el historial de la terminal | propuesta | No implementado: leerla de una variable de entorno. Si querés, va como pieza. |

## Hallazgos de la revisión

| Hallazgo | Quién | Qué pasó |
|---|---|---|
| Uso viejo del perfil sin CUIT gana la preselección | `/code-review high` | Arreglado en `975d627`, con su caso y sabotaje |
| Tapar el lugar por pedazos no hacía nada | sabotaje verde propio | Sacado en `2a21835` |
| 3 sabotajes de `cliente1b.sh` sin patrón, 4 de `cliente1c.sh` sin rojo | corrida de sabotajes | Arreglados en `f1cb25e` |
| Fecha de Excel con hora queda vacía | `/code-review high` | Supuesto, arriba |
| Nombre con blancos que no son Cf | `/code-review high` | Supuesto, arriba |
| Carrera al anotar el uso del perfil | `/code-review high` | Riesgo, arriba |
| Se tapa de más el lugar | `/code-review high` | Supuesto, arriba |
| Limpiezas (excepción para dar vacío, `_utc` repetido, limpieza del CUIT en cuatro lugares) | `/code-review high` | No las hice: no cambian resultado y ampliaban el diff |
| `/security-review` | sobre ESTUDIO-1b y CLIENTE-1c | Sin hallazgos altos ni medios |

**No corrí los subagentes adversariales:** sin presupuesto de gasto hasta
el 2026-10-28 18:00 UTC. La revisión independiente queda para vos.

## Puertas, sobre `3aba9c2`

| Puerta | Salida |
|---|---|
| Suite completa, worktree limpio | `3229 passed, 102 skipped, 2 xfailed, 94 warnings in 415.01s (0:06:55)`, exit 0 |
| `compileall -q proyecto_maria` | 0 |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido`, exit 0 |
| `ataque_aislamiento.sh` | `Bloqueado: 22 · Fugas: 0`, «PUERTA G3 PASADA», exit 0 |
| `cliente1c.sh` (en `f1cb25e`) | 37 ROJO, `sabotajes sin rojo: 0`, `salida 0` |
| `cliente1b.sh` (en `f1cb25e`) | 16 ROJO, `sabotajes sin rojo: 0`, `salida 0` |
| `estudio1b.sh` (incluye la pantalla) | 20 ROJO, `sabotajes sin rojo: 0`, `salida 0` |
| `estudio1.sh` | 37 ROJO, `sabotajes sin rojo: 0`, `salida 0` |

`f1cb25e` → `3aba9c2` es sólo el merge de `docs/pm/`.

**No corrí:** los adversarios (sin presupuesto) ni la CI de tu `ci.yml`
(corre cuando suba).

## Para reproducir

```bash
git fetch origin claude/dev-tecnica && git checkout 3aba9c2
git diff 4452b22..3aba9c2 --stat                       # 14 archivos fuera de docs/pm
bash scripts/testing/sabotajes/cliente1c.sh 3aba9c2    # «sabotajes sin rojo: 0», salida 0
bash scripts/testing/sabotajes/cliente1b.sh 3aba9c2    # «sabotajes sin rojo: 0», salida 0
bash scripts/testing/sabotajes/estudio1b.sh 3aba9c2    # «sabotajes sin rojo: 0», salida 0
bash scripts/testing/sabotajes/estudio1.sh 3aba9c2     # «sabotajes sin rojo: 0», salida 0
python -m pytest -q --no-cov tests/test_cliente1c.py tests/test_cliente1b_script.py tests/test_estudio1b.py
```

## Archivos de producto que toqué

`proyecto_maria/main.py`, `proyecto_maria/database/models.py`,
`proyecto_maria/services/fecha_inic_activ.py` (nuevo),
`proyecto_maria/services/migration_service.py`,
`scripts/datos/clientes_fecha_inic_activ.py`, `CHANGELOG.md`.

## Sigo con

EXCEL-3f y después GUARDAR-2. Si tu veredicto trae una devolución, va
primero.

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». Entregué la vuelta de CLIENTE-1c y ESTUDIO-1b en 3aba9c2 (base 4452b22), sin D abiertas; próxima D: D26. Sigo con EXCEL-3f (D21 b, D22 b, familia H4 con aviso, H5 opcional, H1 descripción repetida a mano y H3 de PARA-DEV.md) y después GUARDAR-2. Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales (la proforma del 24/10 no entra); no tocar maria_generator.py, controles_maria.py, despachante.js ni el canal/rama de la Dev MARIA; subagentes hasta alto, sin Fable; sin presupuesto para subagentes hasta 2026-10-28 18:00 UTC.
