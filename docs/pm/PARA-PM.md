# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## FOCO-PERFIL (sólo arnés): la reproducción da el rojo siempre en la base y verde con el arreglo. El paso 2 pierde el nombre (confirmado) y el paso 9 pierde su propio CUIT. Nada para decidir

| Qué | SHA |
|---|---|
| Base | `5f78311a` |
| `pantalla_estudio1.js` espera el foco del perfil antes de escribir; reproducción `foco_perfil.sh` | `639b7262` |
| La reproducción lista cada apertura que perdió lo escrito | `78d4188e` |
| La reproducción no deja la API viva, rechaza un puerto ocupado, corre en modo fake y saca `cobro_mp1` | `dc4cf077` |
| Informe | el commit `docs:` encima de `dc4cf077` |

`producto +0/−0`. No toqué `profile.js`.

### Resultado

Salida de `foco_perfil.sh` sobre la base `5f78311a` (rc=1), copiada del log:

```
PIERDE      | scripts/testing/pantalla_estudio1.js·#pfEstudioNombre: lo escrito cayó en «Mi CUIT» (robado=%23pfEstudioNombre&valor=20-11111111-2Estudio+Inventado) · focos: foco=campo&ms=202
FALLA: error del CUIT corto: El nombre del estudio no puede quedar vacío, pasar de 200 caracteres ni tener saltos de línea ni caracteres invisibles.
PIERDE      | scripts/testing/pantalla_estudio1.js·#pfEstudioCuit: lo escrito cayó en «Mi CUIT» (robado=%23pfEstudioCuit&valor=20-11111111-230-2222 robado=%23pfEstudioCuit&valor=30222222229) · focos: foco=campo&ms=182 foco=campo&ms=286
FALLA: sin perfil, el estudio no aparece en la lista
```

- **Paso 2:** el nombre del estudio llega vacío porque «Estudio Inventado» cayó en «Mi CUIT».
- **Paso 9:** la segunda señal (`valor=30222222229`) es el CUIT que escribe el paso 9. Lo pierde él mismo; no arrastra lo del paso 2.

Sobre `dc4cf077` (rc=0):

```
NO PIERDE   | scripts/testing/pantalla_estudio1.js·#pfEstudioNombre · focos: foco=reloj&ms=3000 foco=reloj&ms=3000 foco=reloj&ms=3000
NO PIERDE   | scripts/testing/pantalla_estudio1.js·#pfEstudioCuit · focos: foco=reloj&ms=3000 foco=reloj&ms=3000 foco=reloj&ms=3000
```

Corrí la base tres veces (`5f78311a` con las tres versiones del script): las tres PIERDE en los dos casos. El arreglo dio verde en `639b7262`, `78d4188e` y `dc4cf077`.

### Cómo da el rojo siempre, sin espera fija

- **Tu palanca sugerida no mueve la carrera.** `open()` espera `Promise.all` de las tres cargas y recién después programa el foco a 150 ms; `CDI.openProfileModal` es ese `open`, así que el `evaluate` del arnés vuelve después de las cargas. Demorar la carga corre las dos cosas juntas.
- **Lo que hace la reproducción.** En un worktree descartable cambia, con reemplazo exacto de una sola vez, el `setTimeout(...focus, 150)` de `profile.js` por un reloj que pone el foco en `#pfCuit` una vez por apertura, en lo primero que pase:
  - que el arnés entre al campo del caso: el foco salta en una microtarea del `focusin`, antes de que Playwright inserte el texto;
  - o que pasen 3000 ms.
- Un arnés que escribe sin esperar el foco lo pierde siempre. Uno que espera el foco lo recibe a los 3000 ms y sigue. La página avisa por `GET /health?foco=…` y `?robado=…`, y el script lo lee del log de la API. Nada de esto entra al producto.
- **Margen:** en las bases el arnés entró al campo entre 80 y 286 ms después de cargar; el reloj recién dispara a 3000.

### Alcance

- `openProfileModal` aparece en tres pantallas: `pantalla_estudio1.js` (mía, la arreglé), `pantalla_cobro_mp1.js` (mía) y `pantalla_sesion1.js` (de MARIA, no la toqué).
- `pantalla_cobro_mp1.js` no escribe en el perfil: no tiene ningún `fill`, `type` ni `press`, sólo abre secciones. El foco no le saca nada. Lo tenía como tercer caso y daba verde siempre, así que no distinguía: lo saqué en `dc4cf077`.
- Costo: cada apertura del perfil en `estudio1` espera ahora el foco real (~150 ms después de cargar).

### Supuestos reversibles

- `foco_perfil.sh` queda en el repo como reproducción para que la corras vos. §6 dice que fuera de lo de revisión fuerte alcanza con mostrar el rojo una vez; lo dejé porque pediste una reproducción y no corresponde pedirte pasos a mano. Si no lo querés en el repo, se borra sin tocar nada más.
- Si `profile.js` deja de poner el foco en «Mi CUIT» (el arreglo de producto está en la cola), `estudio1` falla con «el perfil no puso el foco en «Mi CUIT»» en vez de esperar sin fin. El arreglo de producto tiene que llevar el cambio del arnés en el mismo commit.

### Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout dc4cf077   # o el SHA del informe
PY=<venv>/bin/python scripts/testing/foco_perfil.sh 5f78311a; echo rc=$?
#  dos líneas PIERDE con robado=…, «El nombre del estudio no puede quedar vacío…» y «sin perfil, el estudio no aparece en la lista»; rc=1
PY=<venv>/bin/python scripts/testing/foco_perfil.sh dc4cf077; echo rc=$?
#  dos líneas NO PIERDE con foco=reloj&ms=3000 tres veces cada una; rc=0
PY=<venv>/bin/python PUERTO=8852 scripts/testing/sabotajes/estudio1.sh dc4cf077; echo rc=$?
#  termina con «sabotajes sin rojo: 0»; rc=0
```

### Puertas

| Puerta | Resultado |
|---|---|
| `foco_perfil.sh 5f78311a` | rc=1, PIERDE en los dos casos (3 de 3 corridas) |
| `foco_perfil.sh dc4cf077` | rc=0, NO PIERDE en los dos casos |
| `sabotajes/estudio1.sh 78d4188e` | 37 ROJO, «sabotajes sin rojo: 0», rc=0 |
| Suite pytest | no corrida: no cambió producto ni tests de Python |

`sabotajes/estudio1.sh` lo corrí sobre `78d4188e`; `dc4cf077` cambia sólo `foco_perfil.sh`, que ese script no usa.

### `/code-review high` sobre `5f78311a..78d4188e`

| # | Hallazgo | Qué hice |
|---|---|---|
| 1 | La API arrancaba dentro de `$(...)`: si se cortaba el script, quedaba viva ocupando el puerto | arreglado en `dc4cf077` |
| 2 | Si el puerto ya respondía, el arnés corría contra otra API | arreglado: rechaza un puerto ocupado |
| 3 | El caso `cobro_mp1` no podía dar PIERDE | arreglado: se sacó (ver Alcance) |
| 4 | La espera del foco podría pasar con un `#pfCuit` enfocado de una apertura anterior | no reproduce: si pasara antes de tiempo, el arnés entraría al campo antes de los 3000 ms y el reloj marcaría `campo`; en el arreglo marcó `reloj` las 6 veces |
| 5 | ILEGIBLE (salida 2) gana a PIERDE (salida 1) | queda: un caso ilegible invalida la corrida; la línea PIERDE se imprime igual |
| 6 | `estudio1` depende de que el producto ponga el foco | riesgo, en Supuestos |
| 7 | La API no iba en modo fake | arreglado: `VUCE_MODE`, `TARIFAR_MODE` y `AFIP_MODE` en fake |
| 8 | Si queda algo extra en el temporal, `rmdir` falla y lo deja | queda: no uso `rm -rf` con variables; lo que puede sobrar es un archivo auxiliar de SQLite tras un corte |
| 9 | Repite código de `_entorno_comun.sh` | queda: ese archivo es para pytest (`test.db`, `juzgar`); no levanta uvicorn ni corre node |
| 10 | §6 sobre guiones de sabotaje propios | en Supuestos |

Subagentes adversariales: ninguno. Es sólo arnés, sin producto ni datos.

<details><summary>chequeo-6 5f78311a..dc4cf077</summary>

```
chequeo-6 5f78311a..dc4cf077: avisos para mirar, no un veredicto
producto +0/−0
arnés +112/−7
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

</details>
