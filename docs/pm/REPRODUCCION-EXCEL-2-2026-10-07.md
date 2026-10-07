# Reproducción de EXCEL-2 — 2026-10-07

**Veredicto: devuelta** sobre `3e6e63e` (base `3b52bc9`) por seis puntos.
Tres rompen: una combinada gigante traba la lectura, una combinada con texto
duplica el FOB, y el tope de los estilos no protege la memoria. D27: (a).

## Lo que corrió la PM

Worktrees limpios. El venv se armó sólo con el `requirements.txt` de la rama
(es igual al de `6ea8ca9`). Gemini falso y terceros simulados.

| Qué | Salida |
|---|---|
| Rojo antes: `tests/test_excel2.py` con el producto de `3b52bc9` | `43 failed, 8 passed, 5 warnings in 81.01s` |
| Suite | `1277 passed, 102 skipped, 3 xfailed, 25 warnings in 139.46s` (la Dev: 1267 con los 10 que deselecciona la CI) |
| Se junta con la rama de la PM | sin conflictos (`git merge-tree`) |
| La PM, a mano, hallazgos 1 y 2 | `merge_10.xlsx`: `200 5.6s` (en `3b52bc9`, `200 0.1s`); «5 UN» y «USD 100» combinados: la fila B sale `5.0 / 100.0` (sin combinar, `0.0 / 0.0`) |

## Subagente de la PM (Sonnet alto)

**Se sostiene:**
- **Hojas con nombre repetido** y relación normal: la segunda queda fuera.
  Tarda 0,1 s, contra 7,3 s en `3b52bc9`.
- **`sharedStrings` de 19 millones de entradas:** 400 en 0,1 s, con 153 MB.
- **Entidades XML:** expat 2.6.1 corta las dos variantes.
- **Orden de los topes:** el tope de 100 MB descomprimido va antes de contar
  las hojas y antes de reconstruir el libro.
- **Combinadas:** con las filas 1 y 2 vacías de verdad, el relleno cae en la
  fila correcta y el aviso nombra la fila real. También con el encabezado
  más abajo, un título combinado o combinadas hacia el costado. Con números
  puros, el FOB no se duplica.
- **El 400 de `/generate_maria`:** nunca sale vacío. `items=[1]` y
  `subitems=7` dan 400; en `3b52bc9` daban 500.
- **CSV:** coma, punto y coma, tab, comillas y BOM se leen bien.
- **D27:** el mensaje llega a `upload.js` (leído en el código).
- **Regresiones:** nueve libros normales dan el mismo JSON que en
  `3b52bc9`. Los archivos reales: `9 passed, 3 xfailed`.
- **CUIT con guiones:** se normaliza.

| # | Hallazgo | ¿Antes? | Cómo quedó |
|---|---|---|---|
| 1 | Una combinada `C2:C1048576` repetida 2000 veces (libro de 1,8 KB) ocupa un hilo ~1000 s; con dos así, la normal da 504 a los 60 s | Nuevo (en `3b52bc9`, 0,2 s) | **Devolución 1** |
| 2 | Cantidad y precio combinados con texto («5 UN», «USD 100», «$ 1.500,00») se copian a la fila de abajo: FOB duplicado | Nuevo | **Devolución 2** |
| 3 | `styles.xml` de 10 MB de `<xf/>` (17 KB comprimido): pasa la validación, 1,4 GB y 52 s; con dos, la normal da 504 y el proceso llega a 1,9 GB | Parcial (antes daba 400 a los 30 s y 1,3 GB) | **Devolución 3** |
| 4 | CSV cp1252 con un par que parece UTF-8 («é®», «ñ» + 0xA0, «ó¿»): todas las tildes se pierden sin aviso | Distinto (antes se rechazaba) | **Devolución 5** |
| 5 | La D26 se saltea: (a) una hoja extra con un `Type` raro que openpyxl abre igual; (b) una primera hoja de 27 MB sin `<dimension>`. Con 8 delante, la normal da 504. Con el libro de la Dev da 200 en 12,5 s | Ya pasaba (antes, 400 a los 30 s) | **Devolución 4** |
| 6 | Una combinada sobre una fila vacía la marca como «fila sin leer» | Nuevo | **Devolución 6** |
| 7a | Con `cantidad: 10**400`, el 400 trae también «Valor inválido» y «Peso inválido» | Igual que antes | De paso |
| 7b | 92 MB de medios: 359 MB y 1,4 s | Nuevo, acotado por los 100 MB | Se deja |
| 7c | Un perfil con un CUIT que no tiene 11 dígitos da 400 con mensaje | Nuevo, buscado | Se deja |

## No corrido

- `merge_10000.xlsx` de punta a punta: se extrapoló de 2000.
- El camino con el mapeo guardado del cliente, de punta a punta: sólo se
  leyó.
- `upload.js` en un navegador.
- Los sabotajes de la Dev (`excel2.sh`).
- `.xls` con xlrd, Gemini real.

Los archivos de ataque quedaron en `/tmp/cdi-pm/rev/ex2-ataque/` del
contenedor de la PM, no en el repositorio.

Contexto de la Dev 1 en la pieza: ~62 % al entregar (624 mil tokens); Emi la
compactó después (11 %).
