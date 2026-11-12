# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D149 (a) con el ataque sin Postgres, D145 (a) en siete arneses y D173 (a). Salida de navegación de BORRADOR-1. Nada para decidir; un desvío: dos commits de arnés en vez de uno

| Qué | SHA |
|---|---|
| Entrega (este informe) | el commit de este informe, encima de `30b9fea6` (merge de tu rama en `6cabcf65`, que trae MARIA integrada en `8669b434`) |
| Donde corrieron el ataque y la navegación | `bb1bc1df` (merge anterior de tu rama). Los rojos de los patrones, en sus SHAs (abajo) |
| Arnés, D149 y ataque sin Postgres | `b7db6f65`: `ataque_aislamiento.sh`, `sabotajes/cobro_mp1.sh`, `sabotajes/despacho1d.sh`, `sabotajes/estudio1.sh` |
| Arnés, D145 (a), D173 (a) y `estudio1b` | `4e7da21f`: `pantalla_{cliente1,despacho1a,destino1,estudio1,estudio1b,orden1}.js`, `sabotajes/estudio1b.sh` |
| Base | `e7633862` (padre de `b7db6f65`) |

**Producto tocado: ninguno.** `git rev-list --no-merges 22163cec..30b9fea6 --not origin/claude/practical-shannon-szpwkn -- proyecto_maria` da vacío. Los merges de tu rama (`6809a846` y `30b9fea6`) no tuvieron conflictos, así que no hay `--remerge-diff` mío. Recorriendo todos los merges de `22163cec..30b9fea6`, `git show --remerge-diff` limitado a `proyecto_maria` da 0 líneas en cada uno, salvo `2b59f396` (97 líneas). Ese es el merge de MARIA que integra tu rama en `claude/dev-maria`, y ya es ancestro de tu rama.

**Resultado**
- Los cuatro patrones viejos (`cobro_mp1` g, `despacho1d`, `estudio1`, `estudio1b`) vuelven a encontrar su texto y cada sabotaje da ROJO. Ningún ROTO.
- `ataque_aislamiento.sh` ya no cae a SQLite: si Postgres 16 no levanta, sale con `rc=1` y el log de Postgres. Con Postgres, el control sigue en 47 bloqueados y 0 fugas.
- Cada llamada a `/auth/register` de los siete arneses manda su propia `X-Forwarded-For`. Va por registro y no por sabotaje: `foco_cliente1` registra unas cien veces dentro de un mismo sabotaje, así que una IP por sabotaje igual llegaría al límite.
- `pantalla_cliente1.js:41` falla con el status y el texto del registro si no es 2xx (D173 a). `foco_cliente1` usa ese mismo archivo, así que también lo hereda.
- Navegación de BORRADOR-1 sobre `bb1bc1df`: los cinco arneses con rc=0, ningún ROTO y ningún 429 (tabla abajo).

**Desvío que tenés que saber:** pediste un commit de arnés y son dos (`b7db6f65` y `4e7da21f`). Los dos ya estaban subidos cuando lo noté; sin `push --force` no se pueden unir. Ninguno toca producto.

**Puerta e2e de MARIA:** no aplica. La pieza no toca el recorrido MARIA ni `static/v2`; sólo `scripts/testing`.

## Decisiones

Nada para decidir. No uso ninguna D de mi rango (D180 a D189).

Supuesto reversible: `pantalla_destino1.js` manda la `X-Forwarded-For` pero no mira el status del registro. D173 (a) pedía el chequeo sólo en `cliente1`, y no lo sumé donde no se pidió. Si lo querés en los demás, es una línea por arnés.

## Rojos de los patrones nuevos (cada uno, una vez)

Corrieron sobre `54ddb500` (`despacho1d`, `estudio1`), `542c1860` (`cobro_mp1`) y `4e7da21f` (`estudio1b`). Los tres son ancestros de `bb1bc1df`, y `git diff <cada uno> bb1bc1df -- scripts/testing tests proyecto_maria` da sólo `client_memory.py`, `tests/memoria_pantalla.js`, `tests/test_guardar1.py` y `tests/test_memoria_pantalla.py` (MARIA). Ningún script de sabotaje ni pantalla cambió.

| Arnés | Resultado | El rojo del patrón nuevo |
|---|---|---|
| `cobro_mp1` | 145 ROJO, «sabotajes con falla: 0», rc=0 | «ROJO  · g: Listo guarda la operación sin el archivo del MARIA: dice «FALLA: import: la pantalla hizo»» |
| `despacho1d` | 9 ROJO, «fallas: 0», rc=0 | «ROJO  · la operación vuelve a esperar al catálogo: dice «FAILED tests/test_despacho1c.py::test_la_operacion_no_espera_al_catalogo[colgado-guardado]»» |
| `estudio1` | 37 ROJO, «sabotajes sin rojo: 0», rc=0 | «ROJO  · generar no espera la lista de estudios: dice «FALLA: generar antes de la lista manda estudio_id»» y «ROJO  · los avisos anotan el uso: dice «FAILED tests/test_estudio1.py::test_los_avisos_y_un_txt_que_no_se_genera_no_cuentan_como_uso»» |
| `estudio1b` | 20 ROJO, «sabotajes sin rojo: 0», rc=0 | ancla nueva `_textos_como_van_al_txt(request)`: «ROJO  · el uso del perfil no se anota: dice «FAILED tests/test_estudio1b.py::test_generar_con_el_perfil_despues_de_un_estudio_preselecciona_el_perfil»» |

En las celdas cambié la barra vertical del log por `·`.

## El ataque sin Postgres: rojo y control

Corrió sobre `bb1bc1df` sin `TMPDIR`. El ataque arma `$TMP` con `mktemp -d` y levanta Postgres con `su` como otro usuario. Con mi `TMPDIR` (un directorio de root sin permiso para otros) Postgres no podía entrar y daba un rojo falso; por eso el rojo de abajo ocupa el puerto a propósito.

- **Rojo (puerto 5434 ocupado a propósito, 21:03:51 UTC):** rc=1.
  - «❌ No levantó Postgres 16: sin él no se mide.»
  - Del log de Postgres: «could not bind IPv4 address "127.0.0.1": Address already in use» y «FATAL:  could not create any TCP/IP sockets».
  - Antes de `b7db6f65`, en ese caso seguía sobre SQLite.
- **Control (puerto libre, 21:03:59 UTC):** rc=0.
  - «✅ Postgres listo», «Bloqueado: 47   ·   Fugas: 0   ·   Sin probar: 0», «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.».

## Navegación de BORRADOR-1 sobre `bb1bc1df`

| Arnés | Resultado | 429 | Inicio → fin (UTC) |
|---|---|---|---|
| `cliente1` | 34 ROJO, «sabotajes sin rojo: 0», rc=0 | 0 | 21:04:31 → 21:09:15 |
| `foco_cliente1` | «con espera, 80 ms: 100 bien, 0 fallas de 100», «con espera, en el peor momento: 5 bien, 0 fallas de 5», «sin espera, en el peor momento: 0 bien, 5 fallas de 5 (5 con lo de otro campo en la razón social)», «mediciones con falla: 0», rc=0 | 0 | 21:09:15 → 21:39:23 |
| `destino1` | 19 ROJO, «sabotajes sin rojo: 0», rc=0 | 0 | 21:39:23 → 21:46:15 |
| `despacho1a` | 14 ROJO, «sabotajes sin rojo: 0», rc=0 | 0 | 21:46:15 → 21:47:16 |
| `orden1` | 76 ROJO, «sabotajes sin rojo: 0», rc=0 | 0 | 21:47:16 → 22:17:58 |

`foco_cliente1` no imprime líneas ROJO: mide corridas. El rojo es la fila «sin espera». «429» es la cantidad de líneas del log que contienen «429».

No los volví a correr sobre `30b9fea6`. Lo que ese merge suma sobre `bb1bc1df` es lo tuyo y lo de MARIA que aceptaste (`main.py`, `catalog_service.py`, `finalize.js`, entre otros), no código mío. De mis arneses, sólo cambió `despacho1d.sh`: MARIA reescribió el patrón de «aprender el catálogo con la red caída no avisa», que no es el de D149. Lo volví a correr sobre `30b9fea6`: 9 ROJO, «fallas: 0», rc=0, ningún ROTO.

El merge también cambia `main.py`. `git diff bb1bc1df 30b9fea6 -- proyecto_maria/main.py` toca límites sólo en la recuperación de contraseña (`_tope_por_cuenta`, `recuperar:cuenta:`), no en `register` ni en `get_client_ip`. Para comprobar el registro desde el navegador sobre lo que entrego, volví a correr `despacho1a` sobre `30b9fea6`: 14 ROJO, «sabotajes sin rojo: 0», rc=0, 0 líneas con «429».

Los patrones de D149 aparecen una vez cada uno en `30b9fea6`, con la sangría exacta del `.sh` (`grep -cF` da 1 en cada caso):
- `cobro_mp1` g: `saveOperationToHistory(...)`, con 12 espacios, en `finalize.js`.
- `estudio1`: `if (CDI.estudios) await CDI.estudios.listo();`, con 8 espacios, en `finalize.js`.
- `estudio1b`: el par `_estudio_elegido` / `_textos_como_van_al_txt(request)` en `main.py`.

De los cuatro arneses, sólo `despacho1d` volvió a correr.

## Riesgos

- **Versión de Postgres:** el mensaje dice «Postgres 16», pero el script no mira el número de versión; usa el `initdb` del PATH. En este contenedor el log dice 16.15. En una máquina con otra versión mediría sobre esa sin avisar. Severidad baja; si querés el chequeo, es una pieza aparte.
- **IP inventada:** `ipNueva()` arma `10.x.x.x` al azar (unos 16 millones). El 429 llega con más de 5 registros por hora desde una IP (`main.py`, `register`). Que seis de unos cientos caigan en la misma es despreciable.
- **No corrí:** la suite completa (no se tocó producto ni `tests/`) ni `e2e_maria.sh` (la puerta no aplica).

## Para reproducir

```bash
git fetch origin claude/practical-shannon-szpwkn
git rev-list --no-merges 22163cec..30b9fea6 --not origin/claude/practical-shannon-szpwkn -- proyecto_maria   # vacío
git show --remerge-diff --format= 30b9fea6 -- proyecto_maria | wc -l    # 0 (igual con 6809a846)
bash scripts/testing/sabotajes/estudio1b.sh bb1bc1df          # 20 ROJO, «sabotajes sin rojo: 0»
bash scripts/testing/ataque_aislamiento.sh                    # sin Postgres 16: rc=1 y «❌ No levantó Postgres 16»; con él: 47 / 0 / 0
grep -ln "X-Forwarded-For" scripts/testing/pantalla_*.js      # seis archivos; foco_cliente1 usa pantalla_cliente1.js
```

## chequeo-6

Corrió sobre `bb1bc1df`, no sobre `30b9fea6`: medido ahí, sumaría como míos los cambios de MARIA que trae tu rama. El único AVISO es `pantalla_cliente1.js:27`: la función anónima del arnés pasa de 296 a 297 líneas por el chequeo de D173 (a), que es una línea. Queda porque D173 pedía el chequeo ahí, donde está el registro. Partir esa función va a la cola de limpieza; no lo hago dentro de esta pieza.

<details><summary>Salida de <code>docs/pm/herramientas/chequeo-6.py e7633862 bb1bc1df</code></summary>

```
chequeo-6 e7633862..bb1bc1dff1b92d8954857f60264be10f7b285c29: avisos para mirar, no un veredicto
producto +2/−2
arnés +121/−26
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/services/client_memory.py: 305 → 305
  AVISO creció una función de más de 150: scripts/testing/pantalla_cliente1.js:27 <anónima> 296 → 297, 1 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 1
```

</details>
