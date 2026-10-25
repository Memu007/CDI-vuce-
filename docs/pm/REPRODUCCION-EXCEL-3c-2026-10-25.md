# Reproducción de EXCEL-3c y CLIENTE-1b — 2026-10-25

Sobre `273c153` (informe `69347ff`, puertas sobre `d527f33`). Base de
comparación: `e08b4c4` (la entrega anterior, EXCEL-3b). Revisor adversarial
Opus, esfuerzo alto, con árboles propios de la base y de la entrega. La PM
re-corrió sus propios casos en los dos árboles. Todo local y con sintéticos.

**Veredicto:** EXCEL-3c vuelve como **EXCEL-3d**. CLIENTE-1b, **aceptada con
nota**; se integra junto con EXCEL-3d porque la rama no se separa limpia (el
corte `23936d5` ya trae `test_excel3.py` y `excel3.sh` de EXCEL-3b/3c).

## Lo que se corrió

| Qué | Resultado |
|---|---|
| `pytest tests/test_excel3.py tests/test_cliente1b.py tests/test_cliente1b_script.py` sobre `273c153` | `160 passed, 3 warnings in 11.50s` |
| una corrida anterior con otra selección, que no anoté | `162 passed, 5 warnings in 5.46s` |
| `scripts/testing/sabotajes/excel3.sh` | todos ROJO, `sabotajes sin rojo: 0`, rc=0 |
| `scripts/testing/sabotajes/cliente1b.sh` | todos ROJO, `sabotajes sin rojo: 0` |
| `ataque_aislamiento.sh` | rc=1, `Bloqueado: 19 · Fugas: 0`, «❌ PUERTA G3 SIN PROBAR: Ana no llegó a generar su MARIA.TXT.» (el sufijo «01» que la API rechaza desde MARIA-7: D17) |
| `test_excel2 -k ocho_libros`, solo, con la máquina quieta (carga 0.14) | `2 passed, 117 deselected, 3 warnings in 42.16s` |
| casos de la PM y del adversario por `/upload_excel_v2/`, base contra entrega | abajo |
| fuzz del adversario, base contra entrega | abajo |

El rojo de «ocho libros» (31 s) en una corrida con carga es la medición de
tiempo sensible a la carga; solo y quieta pasa. No es un hallazgo.

## Hallazgos

### 1. Un cargo con una palabra que la lista no conoce entra al FOB sin aviso (regresión)

Con el origen combinado (`C2:C4`), la fila 4 lleva un rótulo de cargo en la
columna de la descripción. `273c153` decide si es cargo con una lista de
palabras (`_es_solo_un_cargo`, `_CARGOS` / `_PALABRAS_DE_CARGO`,
`main.py:4600-4637`; se usa en `main.py:4877-4878` y `4968-4969`). Si el
rótulo trae una palabra que no está en la lista, la fila entra como producto
en silencio.

| Caso (fila 4: `[3, <rótulo>, None, 1, 1200, 1200]`, `C2:C4`) | `273c153` | base `e08b4c4` |
|---|---|---|
| «Flete int.» | 3 ítems, FOB 4750.0, flete None, avisos `[]` | 2 ítems, FOB 3550.0, flete 1200.0, aviso «Flete: se leyó 1.200,00 de la fila 4…» |
| «Gastos administrativos» | 3 ítems, FOB 4750, avisos `[]` | 2 ítems, FOB 3550 |
| «Insurance 40 GBP» | 3 ítems, FOB 4750, avisos `[]` | 2 ítems, FOB 3550 |
| «Flete maritimo» | 2 ítems, FOB 3550, flete 1200 | igual |
| los cuatro sin combinadas | 3 ítems, FOB 4750 | igual |

Lo que pasa: 1200 USD de flete, gastos o seguro suben el FOB de 3550 a 4750
sin un solo aviso. La base leía «Flete int.» como flete y lo avisaba con su
fila. Una lista de palabras no cierra la familia: cualquier palabra nueva
vuelve a abrirla.

### 2. Una cabecera de grupo con rótulo de cargo queda afuera y su hijo entra con ese rótulo (regresión, sin combinadas)

Sin combinadas. La fila 3 es una cabecera con código y medidas; la fila 4,
su hijo, sin código ni descripción. El hijo hereda el rótulo, pero el
filtro de cargos no lo mira (`rotulo_propio = ""` si `del_grupo`,
`main.py:4958`).

| Caso | `273c153` | base `e08b4c4` |
|---|---|---|
| `f3_insurance`: `["H-1","Insurance",1,2,5,10,50]`, `[None,None,1,1,4,10,40]` | entra «H-1 Insurance, ancho 1 m x largo 1 m», 4 × 10; FOB 41.5; sin leer `[3]` | FOB 1.5; sin leer `[3, 4]` |
| `f3_handling`: igual con «Handling trolley DEMO» | entra «H-1 Handling trolley DEMO, ancho 1 m x largo 3 m», 4 × 10; FOB 41.5; sin leer `[3]` | FOB 1.5; sin leer `[3, 4]` |

Los dos dan, en los dos árboles, sólo estos avisos: «El Excel no tiene una
columna de país de origen…» y «1 renglón(es) sin descripción tomaron la del
renglón de arriba (como agrupa la proforma), desde la fila 4. Revisalos.».
Con «Insurance», 40 USD de seguro entran al FOB como producto y el aviso no
dice que es un cargo. La cabecera y su hijo, con el mismo rótulo, se deciden
distinto.

### 3. D12 (a) avisa sólo en el grupo con medidas

El aviso de «sin precio» está sólo en la rama del grupo con medidas
(`main.py:4921`). Con la descripción combinada (`B2:B4`), sin medidas y el
precio sólo arriba:

`d12_hijos_sin_precio`: `[1,"LAPTOP DEMO","China",10,350,3500]`,
`[2,None,"China",5,None,None]`, `[3,None,"China",5,None,None]` →
3 ítems, FOB 3500, avisos `[]`, en la entrega y en la base.

Dos renglones entran sin precio y nadie avisa al subir. Es lo que pedía el
punto 3 de EXCEL-3c, en un miembro de la familia que la prueba no cubre.

### Lo que cambió y trae aviso (riesgo, no se devuelve)

En el fuzz del adversario cambian tres proformas de la base a la entrega,
las tres con el aviso «renglón(es) sin descripción tomaron la del renglón de
arriba…»: `fz47_SO` (FOB 50 → 60), `fz187_R` (0 → 500) y `fz236_R`
(0 → 100). Es la herencia de R2, que ahora entra con aviso.

### Lo que ya estaba en la base (no es de esta pieza)

«Ins.», «Commission» y rótulos parecidos entran al FOB como producto también
en la base.

## CLIENTE-1b: notas (no frenan)

- Se acepta el día con una cifra (`5/03/2015`).
- Los años 0001 y 9999 pasan.
- Con un `--base` mal escrito, el script muestra la clave de la base en el
  error de Python.
- Un dígito de ancho completo («２０１５») se lee distinto en la pantalla y
  en el generador.

Las dos últimas van a CLIENTE-1c, con D15 y D16.

## Lo que no se corrió

- La suite completa sobre `273c153`.
- `ataque_aislamiento.sh` con G3: no llega a generar el TXT (D17).
- El script de fechas contra una base que no sea local.
- Nada contra producción.
