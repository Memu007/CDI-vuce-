# Reproducción de EXCEL-2b, vuelta 2 (2026-10-28)

Entrega de la Dev técnica: informe `5a6ef01`, puertas sobre `03336f1`
(rojos `9fa4b2d`, producto `315b6e6`, casos de guardas y de `sugerir`
`b054ee1`, sabotajes `03336f1`). En la rama van intercalados commits de
COBRO-MP-1 (`472e389`, `87094a1`), que no son parte de esta revisión.

## Lo que corrió la PM

- `excel2b.sh` sobre `03336f1`: 37 ROJO, «sabotajes sin rojo: 0», FIN rc=0.
- Los topes leídos del entorno, sobre `03336f1`
  (`EXCEL_MAX_DESCOMPRIMIDO_MB`, `EXCEL_MAX_ELEMENTOS_ESTILOS`,
  `MAX_UPLOAD_MB`):

  | Valor | Resultado |
  |---|---|
  | `1e-9`, `0.0000009`, `inf`, `nan`, `-0`, `0`, `-3`, `abc` | el defecto en los tres (209715200, 500000, 10485760) |
  | `0.5` MB | 524288 |
  | `0.5` elementos | el defecto |
  | `1e308` MB | el defecto |
  | `EXCEL_MAX_ELEMENTOS_ESTILOS=1e308` | un entero enorme (riesgo «topes enormes», ya anotado) |
  | `1e-6` MB | 1 byte (riesgo que la Dev declara) |

  Son ejemplos distintos de los que pidió la devolución (`0`, `-3`, `abc`,
  `0.0000009`, `0.5` MB), y todos dan un tope usable salvo los dos riesgos
  declarados.

- Mutantes de la PM contra `test_excel1_lectura`, `test_excel1_txt`,
  `test_excel2`, `test_excel2b`, `test_excel3`, `test_maria5_peso_excel`,
  `test_guardar2` y `tests/unit/test_main_upload.py` (1282 pruebas), cada
  uno restaurado después:

  | Mutante | Resultado |
  |---|---|
  | N01: `tope <= 0` → `tope < 0` en `tope_de_entorno` | muere, 52 failed |
  | N02: la escala después del `int` | muere, 11 failed |
  | U1: el lector viejo de `MAX_UPLOAD_MB` | muere, 9 failed |
  | M08: la cabeza sin `max_length` | muere, 1 |
  | M13: `continue` → `break` en el presupuesto de imágenes | muere, 1 |
  | M14: `reverse=False` | muere, 1 |
  | M15: no se excluyen las cifradas | muere, 1 |
  | B1: `resto <= umbral` → `<` | muere, 1 |
  | B2: `.xls` `<=` → `<` | muere, 1 |
  | B3: `resto - descontado <=` → `<` | muere, 2 |
  | B4: `> _LIVIANO_IMAGENES_MAX` → `>=` | muere, 1 |
  | M19: `!= b"PK\x03\x04"` → `== b"NOPE"` | 1282 passed |

  M19 sobrevive porque el mutante de la PM estaba mal elegido: rechaza sólo
  `NOPE`, que es justo el encabezado falso de la prueba. Con
  `== b"XXXX"` (cualquier otra firma pasa) la prueba
  `test_una_cabeza_sin_la_firma_del_encabezado_local_no_cuenta_como_imagen`
  da rojo (1 failed), igual que el sabotaje de la Dev (`if False:`). No es
  un hueco.

- `sugerir` con otro cliente: la Dev corrigió el informe y sumó el caso en
  `test_guardar2` (`b054ee1`).

## Supuesto aceptado

`MAX_UPLOAD_MB` inválido ahora da 10 MB también al PDF (antes 50 MB), y un
negativo da 10 MB en vez de 413. `docker-compose` fija `MAX_UPLOAD_MB=10`,
válido: ahí no cambia nada.

## No corrido por la PM

- La suite completa (la Dev informa 1309 passed en sus pruebas sobre
  `87094a1`; la suite completa tampoco la corrió ella), Postgres,
  `/code-review` y `/security-review`.
- Adversario de la PM: no se corrió. Es lectura de números de entorno, sin
  dinero, sesión ni datos; la Dev corrió Sonnet alto.

## Veredicto

Aceptada sobre `03336f1`, sin integrar: la rama de la técnica intercala
ORDEN-1 y COBRO sin aceptar. Riesgos: topes hasta `1e302` se aceptan; un
tope de 1 a 10 bytes (`1e-6` MB) traba toda subida con mensaje claro; D32
hasta EXCEL-2c.
