# Reproducción CATALOGO-PAIS (MARIA), 2026-11-19

Entrega `4904e5a1` (informe `997e3dd8`), base `695a5377`. Producto `+8/−12`, sólo CSS y JS de
pantalla (`app_v2.css`, `paises_maria.js`, `catalogo.js`, `clientes.js`). La rama de PM, desde la
base de la entrega, sólo tocó `docs/pm`: la unión tiene el mismo producto que `4904e5a1`.

**Devolución sobre `4904e5a1`.** Las puertas y los rojos están bien, pero la fila del catálogo del
cliente se rompe en dos renglones entre 850 y 1010 px de ancho de ventana (y crece de 82 a 87 px de
alto entre 1020 y 1040, con 1024 adentro). Con el ancho de la base (36 px) queda en un renglón y 82 px
de 700 a 1600. Camino de hoy: una ventana en media pantalla de 1920 (960 px) o con zoom. Además el
campo del cliente muestra en mayúsculas lo que no es un país («Narnia» se ve «NARNIA»), y `learn`
guarda «Narnia» así: falla el criterio 4 («se ve como se escribió»).

## Lo que corrí, sobre `4904e5a1`, en un worktree limpio

| qué | resultado |
|---|---|
| `chequeo-6.py 695a5377 4904e5a1` | «producto +8/−12», «arnés +185/−80», historia vacía, «avisos: 0» |
| vecinos (`test_catalogo3`, `test_catalogo4`, `test_catalogo_largo1/2`, `test_guardar1/2`) | «218 passed» |
| `holanda423.sh` | BASE casos «113 passed», BASE pantalla «OK: pantalla Holanda→423», 28 ROJO, «sabotajes sin rojo: 0» |
| `paises_nombres.sh` | 9 ROJO, «OK: todos los sabotajes en rojo» |
| `catalogo3.sh` | 65 ROJO, «fallas: 0», de 21:47 a 22:55 UTC |
| `e2e_maria.sh` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| negativos PM (abajo) | «2 passed»; con el PUT del cliente saboteado, «1 failed, 3 passed» |
| capturas de los dos catálogos, 1280 y 800 px | el texto largo se corta dentro del campo; a esos dos anchos la fila no se rompe |
| barrido de 1600 a 700 px cada 10, fila del cliente | 850–1010: dos renglones (alto 93, y 114 a 850); 1020–1040: alto 87; el resto, 82 y un renglón. Con etiqueta corta («310 · CHINA») también: a 1024 baja «kg», a 960 baja el peso |
| el mismo barrido con el campo en 36 px (ancho de la base) | un renglón y alto 82 en todos los anchos |
| barrido del proveedor | 340 px de cajón fijo, un renglón y alto 156 en todos los anchos |
| `git status` del worktree al final | limpio |
| suite completa | no la corrí: la de MARIA dio «6228 passed, 110 skipped, 3 xfailed» y no hay rojo que la contradiga |

## Cada cambio de producto tiene su rojo

De los 28 ROJO de `holanda423.sh`:
- `catalogo.js:250` (la etiqueta en el proveedor): «el catálogo del proveedor muestra lo guardado» y su
  variante HTML.
- `clientes.js:1427` (la etiqueta en el cliente, sin `maxlength`): «el catálogo del cliente muestra lo
  guardado», su variante HTML y «corta el origen en 3».
- `clientes.js:1468` (la etiqueta después de guardar): «muestra el código de lo escrito» y «pisa lo que
  se sigue escribiendo».
- CSS: «el origen del catálogo del cliente no llega a Emiratos», «del proveedor en el ancho de un
  código» y «del proveedor con su ancho propio».
- El −80 del arnés son los sabotajes de `mostrar`, que salió del producto; el de `etiqueta` se reescribió.
  Los sabotajes pasaron de 24 a 28 y sus anclas son código.

## Negativos PM: orígenes viejos guardados como nombre

`tests/test_pm_cpais.py` (fuera del repo), en los dos catálogos, siembra por SQL «Holanda», «paises
bajos», «CHINA», «CHN», «0423», « 423 », «Hong Kong», «Türkiye», «Narnia», «<b>Z</b>», «XX» y «cn»:
- guardar otro campo los deja byte a byte;
- lo que no es un país vuelve como vino, sin blancos de los bordes (mira el valor del campo, no lo que
  se pinta: las mayúsculas del CSS no las ve);
- volver a mandar la etiqueta que se ve deja el mismo país.

Otro caso escribe en el cliente «paises bajos», «Holanda», «Países Bajos», «423 · PAISES BAJOS»,
«china» y «Estados Unidos»: cada uno queda en su código, los cuatro primeros en 423.

Los dos son guardas del servidor (pasarían también en la base). Con un sabotaje en el PUT del cliente
que normaliza `origen_frecuente` en cualquier guardado, el mío falla y el de MARIA
(`test_cada_pais_del_catalogo_vuelve_a_su_codigo`) pasa, porque sólo siembra códigos. Va a la cola de
limpieza; no es devolución.

## Adversario (sonnet alto, sin red)

Sin navegador, no encontró nada que rompa los criterios 1 a 5 en el código (lo de la pantalla lo
encontré yo, arriba). Notas, ninguna causada por este diff:
- «XX» escrito a mano da 400 en el cliente y 200 en el proveedor. Ya estaba.
- `calculadora.js:112` no precarga un origen guardado como etiqueta o nombre. Va junto al riesgo de la
  calculadora de ORIGEN-2.
- No pudo mirar el CSS sin navegador: lo miré yo con las capturas.

## Lo decidido por la PM

- **Devolución, por la causa:** la fila del cliente no deja achicarse al campo del origen (ancho fijo
  de `30ch`) y el chequeo de pantalla mide el ancho sólo a 1280. Va en `PARA-DEV-2.md`.
- **Mayúsculas en el cliente:** entran en la devolución por el criterio 4 de esta pieza; `learn`
  guarda «Narnia» así (camino de hoy). Medido en el catálogo del cliente; el del proveedor, no.
- **Riesgo 1, etiquetas largas** (unas cuarenta de 308): aceptado aparte. El texto largo se corta
  dentro del campo; eso no es lo que se devuelve.
- **Riesgo 7, `catalogo3.sh` tarda ~70–80 min**: a la cola de limpieza.
- **Hueco del caso de MARIA** (sólo siembra códigos; con el PUT del cliente saboteado su caso pasa y
  el mío falla): a la cola de limpieza, las formas viejas como datos en su caso.

## Vuelta sobre `8140f496` (informe `d2169ef0`) (2026-11-20)

Sólo cambia `app_v2.css` (+2/−2 contra `4904e5a1`): el bloque del producto del cliente puede achicarse
(`flex: 1; min-width: 0`) y el campo del origen pasa de ancho fijo a `flex: 1 1 36px; min-width: 36px;
max-width: 30ch`, sin `text-transform: uppercase`. El catálogo del proveedor no cambia.

**Puertas, corridas por la PM sobre `8140f496`:**
- `chequeo-6.py 4904e5a1 8140f496`: «producto +2/−2», «avisos: 0». La pieza entera
  (`695a5377..8140f496`): «producto +9/−13», historia vacía, «avisos: 0».
- `holanda423.sh`: «113 passed», «OK: pantalla Holanda→423», 34 ROJO iguales mensaje a mensaje a los del
  informe, «sabotajes sin rojo: 0».
- `paises_nombres.sh`: «22 passed», 9 ROJO, «OK: todos los sabotajes en rojo».
- `e2e_maria.sh`: «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y
  memoria verificadas.»
- Capturas del informe (cliente 1280, 960 y 841; proveedor 1280 y 960): sólo datos inventados.

**Ejes míos, no dados en la devolución** (chequeo propio en navegador, fuera del repo, con Inter; con
Arial no lo corrí):
- Fila recién guardada y Enter: a 850 px escribo «emiratos arabes» y Enter; queda «331 · EMIRATOS
  ARABES,UNID» en el campo, con el comienzo a la vista (`scrollLeft` 0, también al salir del campo).
- Lo que no es un país, con formas mezcladas («Narnia», «tierra Média»): se ve con sus letras en los
  dos catálogos. En la base se veía en mayúsculas y el campo del cliente no guardaba («pai», por el
  `maxlength` de 3).
- El código del país entero en el campo a 460, 521, 641, 721, 841, 850, 960, 1040 y 1280 px (el ancho
  libre más chico, 30 px a 460, alcanza para «331»).
- Catálogo del proveedor de 320 a 1440 px: un renglón y el mismo alto.
- Zoom: sin fallas en la corrida extendida.
- El desborde horizontal de la página (641–1140 y 460–521 px) da el mismo ancho de documento en la
  base: no lo trae esta pieza.

**No corrido en la vuelta:** `catalogo3.sh` y la suite completa (sólo cambió CSS; los corrí sobre
`4904e5a1`), `/security-review` (sin servidor ni datos nuevos) y navegadores reales de Windows y macOS.

**Decidido por la PM, con el consejero:**
- Aceptada sobre `8140f496` e integrada con `merge` de `d2169ef0`.
- D275 (a): el texto largo que no entra en el campo, aceptado como riesgo. Según su tabla con Inter, no
  entran 36 etiquetas a ancho completo, 61 a 960 px, 301 a 841 px y 308 a 460 px. La base mostraba sólo
  el código, y el código queda entero en todos esos anchos. La (b), la etiqueta entera en `title`, va a
  Emi como propuesta.
- Los riesgos 2 a 7 de su informe quedan escritos; los siete sabotajes de CSS se quedan.
