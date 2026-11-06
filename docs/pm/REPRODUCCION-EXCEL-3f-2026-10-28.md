# Reproducción de EXCEL-3f (con H1-bis) — 2026-10-28

Sobre `8c63c37` (informe `0557f03`; lo de la Dev solo: `89a0fde..8c63c37`,
7 archivos, +539 −39). La PM corrió la suite, los sabotajes y trece
negativos propios en worktrees limpios (`/tmp/cdi-pm/wt-3f` y
`/tmp/cdi-pm/wt-3f-base` en `89a0fde`). Todo local, con sintéticos y sin
Gemini. **No corrió un adversario con contexto nuevo:** sin presupuesto de
subagentes hasta el 2026-10-28 18:00 UTC.

Veredicto: EXCEL-3f, **aceptada**. Lo único que cambia el FOB es el
plural, y se comporta igual que su singular en la base. Todo lo demás sólo
suma un aviso que nombra la fila. H1-bis tapa la clave de `--base` en todas
las formas de escribirla que probé. Con esto **EXCEL-3 queda cerrada**: lo
que sigue abierto son riesgos anotados, no tareas.

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| Suite completa sobre `8c63c37`, worktree limpio | `1 failed, 3844 passed, 102 skipped, 2 xfailed, 94 warnings in 494.34s`. El rojo es el de `test_excel2` (observación 3), no de 3f |
| `cliente1c.sh 8c63c37` (H1-bis) | 44 ROJO, `sabotajes sin rojo: 0`, `rc=0` (con el script de `8c63c37`; una primera corrida con el script viejo de la rama de PM se descartó) |
| `excel3.sh 8c63c37`, sólo los 39 sabotajes de 3f y los reapuntados (3d, 3c R1, 3b-3#1) | 3b-3#1, 3c R1 y 3d: 23 ROJO; 3f: 16 ROJO; `sabotajes sin rojo: 0`, `rc=0` en los tres tramos (39 de 39) |
| Trece negativos propios × `.xlsx` y `.xls`, en la base y en la entrega | 26 passed en cada SHA; tabla abajo |

El `excel3.sh` entero (112) lo corrió la Dev en dos tramos; la PM corrió una
copia que sólo agrega, al principio de `sabotaje()`, un filtro por nombre:
el resto del script es igual byte a byte. En tres tramos, porque el primero
(`^(3f|3d|3c R1|3b-3#1)`) se cortó por el límite de 30 min de la tarea en
segundo plano a los 13: después `^(3f)` (16) y `^(3d)` (12, dos repetidos).

## Negativos propios

Distintos de los ejemplos de la tarea. Un producto «LAPTOP DEMO» de 3500 y
una segunda fila con el rótulo. FOB = suma de lo que entra como producto.
`.xls` dio lo mismo que `.xlsx` en todos.

| Rótulo de la fila 3 | `89a0fde` (base) | `8c63c37` | Lectura |
|---|---|---|---|
| «Fletes y seguros» 500, sin origen | producto, FOB 4000 | flete 500 con aviso, FOB 3500 | igual que el singular «Flete y seguro» en la base (flete 500) |
| «SEGUROS» 80, sin origen | producto, FOB 3580 | fila 3 sin leer, FOB 3500 | plural como el singular (D21 b) |
| «Seguros para puerta DEMO» 50, sin origen | producto, FOB 3550 | fila 3 sin leer, FOB 3500 | igual que «Seguro para puerta DEMO» en la base; ver observación 1 |
| «Seguros para puerta DEMO», con origen | producto, sin aviso | producto, con aviso «parecen un cargo» | aviso de más, sin plata |
| «Fee meter», con origen | producto, sin aviso | producto, con aviso | aviso de más, sin plata |
| «Air freights», sin origen | producto, sin aviso | producto, con aviso | lo pedido (H4 + plural) |
| «FedEx charges», con origen | producto, sin aviso | producto, con aviso | lo pedido |
| «Transporte interno», con origen | producto, sin aviso | igual | sin aviso; observación 2 |
| «DHL» solo | producto, sin aviso | igual | sin aviso; observación 2 |
| «Container 20GP», «Transport case», «Express charger» | producto, sin aviso | igual | bien: productos que comparten una palabra |
| Ocho filas de flete | «de la fila 3, 4, 5, 6, 7» | «de las filas 3, 4, 5, 6, 7 y 3 más» | H5, bien |

La fila sin leer va a `operacion.filas_excel_sin_leer`, que el semáforo
muestra (`semaforo.js`): no se pierde en silencio.

## Observaciones (no frenan)

1. **«Seguros para puerta» es un producto en castellano** (cerrojos). Sin
   origen ni NCM sale del FOB, con su fila nombrada en el semáforo. Ya
   pasaba con el singular; el plural lo extiende. Es la D21 (b) tal cual.
2. **Aviso de menos:** «Transporte interno» con origen y «DHL» solo no
   llevan aviso. No cambian el FOB; queda anotado.
3. **`test_excel2::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope…`**
   da rojo en este contenedor (4 núcleos, carga ~0,9 sin nada más
   corriendo): en la suite y 6 de 6 corrido solo, alternando base y
   entrega. La subida normal tardó 32,71 / 31,36 / 30,83 s en `89a0fde` y
   30,71 / 30,91 / 31,50 s en `8c63c37`, contra el corte de 30 s de
   `file_security.py`. Igual en la base: **no es de 3f**. La Dev lo vio 1
   de 5. Va como seguimiento después de ORDEN-1 (diagnóstico y D, sin
   subir el corte ni aflojar la prueba): en producción una subida normal
   puede esperar ~30 s detrás de ocho pesadas.

## Riesgos de la Dev

Aceptados como los anotó: `rotulo_aparte` lee Part No. o Transporte,
«Shipping container 20GP», el plural amplía el descarte, «THC-200», y el
sabotaje M de H1-bis verde sin fuga (`url.password` ya viene decodificada).
Sus supuestos (H3 con aviso sin tocar `_es_una_medida`, `not pieza`,
«parecen un cargo», plurales también como rótulo) quedan aceptados.
