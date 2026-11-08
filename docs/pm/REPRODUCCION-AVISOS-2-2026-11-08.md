# Reproducción AVISOS-2, 2026-11-08 (PM principal)

Producto `217c7cd`..`4db641b` (rama `claude/dev-maria`), base `8504691`. Worktree limpio, GEMINI_API_KEY vacía.

| qué | resultado |
|---|---|
| `chequeo-6.py 8504691 4db641b` | producto +29/−16, arnés +268/−6, historia vacío, avisos 0 |
| `avisos2.sh 4db641b` | BASE 131 passed, 12 ROJO, «sabotajes sin rojo: 0», salida 0 |
| `avisos1.sh 4db641b` | BASE 151 passed, «sabotajes sin rojo: 0» |
| mi negativo: `[A-Za-z0-9_]{4}` en `destinacion_del_txt` | `test_avisos2.py` 57 passed: `IC_4` llega al ISTA y ningún caso lo ve. Hueco chico de prueba, a AVISOS-2b |

Adversario Sonnet alto, con contexto nuevo, contra la app en proceso:

- Ningún camino lleva una destinación de exportación al TXT de importación ni
  al revés, ninguna que no sean 4 ASCII, ningún 500. Probó prefijos raros,
  homoglifos, control, 20 MB por ruta (peor caso 2,4 s), tipos JSON y todos
  los llamadores.
- **Baja, sin camino de hoy:** `generate_maria_export_txt` no valida: llamado
  directo con `"EC01\nCDDTIMPEXP=I"` mete líneas. Su único llamador de
  producción (`main.py`) valida antes. Va con la línea del doble chequeo a la
  cola de limpieza: el chequeo, una vez, en los dos generadores.
- **Baja, de dominio:** la regla es la forma, no la tabla de ARCA (`ABCD`,
  `ECZZ` pasan). Es lo que pidió la D130.

No corrí la suite completa: el informe trae 5406 passed sobre `4db641b` y la
pieza toca tres archivos con sus casos.

## AVISOS-2b, sobre `aa115f4` (base `8fda3d2`), 20:58 UTC

| qué | resultado |
|---|---|
| `chequeo-6.py 8fda3d2 aa115f4` | producto +14/−7, arnés +57/−10, historia vacío, avisos 0 |
| `avisos2.sh aa115f4` | BASE 155 passed, 16 ROJO, «sabotajes sin rojo: 0», salida 0 |
| mi negativo: el perfil valida y guarda el texto sin normalizar | `test_el_perfil_solo_guarda_un_codigo_de_importacion[ ic04 -200-IC04]` FAILED: lo ve |

Diff de producto leído entero: una regla (`codigo_de_destinacion`) que usan
el TXT, el lector y el perfil. No corrí la suite completa (el informe trae
5432 passed) ni el smoke (D137).
