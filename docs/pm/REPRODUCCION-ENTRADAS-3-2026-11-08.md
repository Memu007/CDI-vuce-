# Reproducción ENTRADAS-3 (Dev MARIA), 2026-11-08

Sobre `cf5309a` (informe `4a6fdcd`), base `0f09bd8`. Veredicto: **aceptada,
sin integrar**.

| Qué | Resultado |
|---|---|
| `chequeo-6.py 0f09bd8 cf5309a` | `producto +48/−21`, 1 AVISO (27 netas, explicado), historia vacío — igual al informe |
| `test_entradas3.py`, `test_entradas2.py` | `47 passed` |
| `entradas3_postgres.py` contra PG16 local | `fallas: 0`; última `OK \| NUL en la consulta: 400` |
| `entradas3.sh cf5309a` (con `PG_URL`) | BASE, 11 ROJO, `sabotajes con falla: 0`, rc 0 |
| `entradas2.sh cf5309a` | BASE, 24 ROJO, `sabotajes con falla: 0`, rc 0 |
| Mío: `/health?%00=1`, `?x=a%00b&y=2` | 400 «La consulta tiene un carácter nulo.» |
| Mío: `/health?x=%2500`, `?x=%E2%82%AC` | 200 (no confunde un `%` escapado ni un no-ASCII) |

Leí el diff de producto entero. La guarda de NUL en la consulta va en el
middleware que ya miraba la ruta; `_cuerpo_guardable` recorre dentro del
`try` y levanta el aviso de medio par afuera; el tope `1e15` va en
`_numero_de_afuera`, único lugar.

No corrí la suite completa: tomo la de la Dev (`5212 passed`, dos formas).
Sin adversario propio: entradas, sin dinero ni permisos; la Dev pasó Sonnet
alto, `/code-review` y `/security-review`.

Nota: el comando de `entradas3.sh` del informe no trae `PG_URL`; sin ella
sale con error al empezar. Con ella, verde.
