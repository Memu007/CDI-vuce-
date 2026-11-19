# Reproducción CATALOGO-PAIS (MARIA), 2026-11-19

Entrega `4904e5a1` (informe `997e3dd8`), base `695a5377`. Producto `+8/−12`, sólo CSS y JS de
pantalla (`app_v2.css`, `paises_maria.js`, `catalogo.js`, `clientes.js`). La rama de PM, desde la
base de la entrega, sólo tocó `docs/pm`: la unión tiene el mismo producto que `4904e5a1`.

**Borrador: el veredicto espera a `catalogo3.sh`.** Hasta acá, los seis criterios se cumplen y cada
cambio de producto tiene su rojo.

## Lo que corrí, sobre `4904e5a1`, en un worktree limpio

| qué | resultado |
|---|---|
| `chequeo-6.py 695a5377 4904e5a1` | «producto +8/−12», «arnés +185/−80», historia vacía, «avisos: 0» |
| vecinos (`test_catalogo3`, `test_catalogo4`, `test_catalogo_largo1/2`, `test_guardar1/2`) | «218 passed» |
| `holanda423.sh` | BASE casos «113 passed», BASE pantalla «OK: pantalla Holanda→423», 28 ROJO, «sabotajes sin rojo: 0» |
| `paises_nombres.sh` | 9 ROJO, «OK: todos los sabotajes en rojo» |
| `catalogo3.sh` | PENDIENTE |
| `e2e_maria.sh` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| negativos PM (abajo) | «2 passed»; con el PUT del cliente saboteado, «1 failed, 3 passed» |
| capturas de los dos catálogos, 1280 y 800 px | el texto largo se corta dentro del campo; la fila no se rompe ni se pisa |
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
- lo que no es un país se ve como vino, sin blancos de los bordes;
- volver a mandar la etiqueta que se ve deja el mismo país.

Otro caso escribe en el cliente «paises bajos», «Holanda», «Países Bajos», «423 · PAISES BAJOS»,
«china» y «Estados Unidos»: cada uno queda en su código, los cuatro primeros en 423.

Los dos son guardas del servidor (pasarían también en la base). Con un sabotaje en el PUT del cliente
que normaliza `origen_frecuente` en cualquier guardado, el mío falla y el de MARIA
(`test_cada_pais_del_catalogo_vuelve_a_su_codigo`) pasa, porque sólo siembra códigos. Va a la cola de
limpieza; no es devolución.

## Adversario (sonnet alto, sin red)

Nada rompe los criterios 1 a 5. Notas, ninguna causada por este diff:
- «XX» escrito a mano da 400 en el cliente y 200 en el proveedor. Ya estaba.
- `calculadora.js:112` no precarga un origen guardado como etiqueta o nombre. Va junto al riesgo de la
  calculadora de ORIGEN-2.
- No pudo mirar el CSS sin navegador: lo miré yo con las capturas.

## Lo decidido por la PM

- **Riesgo 1, etiquetas largas** (unas cuarenta de 308): aceptado. En las capturas, «670 · ISLAS DEL
  CANAL (GUERNESEY…» se corta dentro del campo en los dos catálogos, a 1280 y a 800 px, y la fila queda
  entera.
- **Mayúsculas en el cliente**: el campo ya tenía `text-transform: uppercase`. «Narnia» se ve «NARNIA»,
  pero lo guardado y lo que se manda queda como vino. Riesgo escrito, sin código.
- **Riesgo 7, `catalogo3.sh` tarda ~80 min**: a la cola de limpieza.
