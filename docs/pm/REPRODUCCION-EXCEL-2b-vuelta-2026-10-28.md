# Reproducción de EXCEL-2b, vuelta (2026-10-28)

Entrega de la Dev técnica: informe `a81bb1f`, puertas sobre `606dda5`
(producto `ce3ac05` y `cedb3ff`; pruebas y sabotajes `271c0db`, `f5f8f75`,
`f567adb`, `83871a5`, `43fd20d`, `606dda5`). Es la vuelta de la revisión
sobre `b3ac325` más el agregado de GUARDAR-2.

## Lo que corrió la PM

- `excel2b.sh` sobre `606dda5`: 25 ROJO, «sabotajes sin rojo: 0», salida 0,
  worktree limpio después.
- El tope en cero, sobre `606dda5`:

  ```
  EXCEL_MAX_DESCOMPRIMIDO_MB=1e-9      -> _mb_de_entorno = 0
  EXCEL_MAX_DESCOMPRIMIDO_MB=0.0000009 -> 0
  EXCEL_MAX_DESCOMPRIMIDO_MB=0.000001  -> 1
  EXCEL_MAX_ELEMENTOS_ESTILOS=0.5      -> _elementos_de_entorno = 0
  ```

  Un valor positivo que en bytes (o en elementos) da 0 pasa como tope 0, y
  ninguna subida de Excel entra. Es la misma familia que el `1e308` de la
  revisión anterior: se arregló el ejemplo, no la causa. El informe lo
  lista como BAJA, a riesgos.
- Mutantes de la PM contra todas las pruebas de Excel y GUARDAR-2
  (`test_excel1_lectura`, `test_excel1_txt`, `test_excel2`, `test_excel2b`,
  `test_excel3`, `test_maria5_peso_excel`, `test_guardar2`), cada uno
  restaurado después:

  | Mutante | Resultado |
  |---|---|
  | M02: `valor <= 0` pasa a `valor < 0` en `_mb_de_entorno` | 1201 passed, sobrevive |
  | M08: la cabeza se descomprime sin `max_length` | 1201 passed, sobrevive |
  | M13: `continue` pasa a `break` en el presupuesto de imágenes | 1201 passed, sobrevive |
  | M14: las imágenes se ordenan de menor a mayor (`reverse=False`) | 1201 passed, sobrevive |
  | M15: no se excluyen las entradas cifradas | 1201 passed, sobrevive |
  | M19: no se mira la firma del encabezado local | 1201 passed, sobrevive |

- GUARDAR-2, `/api/ncm/sugerir` con dos clientes iguales del mismo
  despachante (prueba del adversario, corrida por la PM sobre `606dda5`):

  ```
  GUARDAR-USO 200 {"success":true}          (cliente A)
  SUGERIR-OTRO 200 [{'ncm': '84714900', 'desc': 'COMPUTADORA PORTATIL', 'source': 'historial', 'count': 1}]
  SUGERIR-SIN-CLIENTE 200 [{... 'source': 'historial' ...}]
  LOOKUP-OTRO ninguno
  ```

  El historial liviano (`load_ncm_historial`, `main.py` cerca de la 9517)
  es por despachante y existía antes de GUARDAR-2. No hay fuga entre
  despachantes. Pero el informe dice que los dos clientes «no comparten
  historial ni en `/api/catalog/lookup` ni en `/api/ncm/sugerir`», y en
  `sugerir` sí lo comparten: la prueba de `f567adb` no lo ve porque la
  descripción no pasa por `guardar-uso`.

## Adversario (Sonnet alto, contexto nuevo)

1. Media: el historial liviano de `sugerir`, reproducido arriba.
2. Media: el tope en cero, reproducido arriba.
3. Baja, preexistente: `MAX_UPLOAD_MB` con `inf`, `nan`, `1e309` o `1e308`
   da 500 en `/upload_excel_v2/`. La Dev lo tiene en riesgos.
4. Baja: hasta `1e302` se acepta como tope enorme; desde `1e303`, el
   defecto.
5. Sus mutantes, contra `test_excel2b` y `test_guardar2` solamente:
   sobreviven M08 a M15 y M19 (los bordes M09 a M12 no los corrió la PM
   contra el resto de las pruebas). Los de carril (M21 a M28) mueren: no
   encontró camino de `/upload_excel_v2/` que lea en el carril equivocado.
6. Con M08, un zip de 415 KB tarda 0,497 s y llega a 45 MiB.

No corrido por la PM: la suite completa (la Dev informa 4178 passed, 121
skipped, 3 xfailed sobre `606dda5`), Postgres, `ataque_aislamiento.sh`.

## Veredicto

Devolución sobre `606dda5`. Causa: el arreglo del tope tapó el ejemplo
(`1e308`) y no la familia (un número de entorno que no da un tope usable), y
varias guardas del carril liviano no tienen un caso que las distinga. El
detalle y la D32 están en `PARA-DEV.md`.
