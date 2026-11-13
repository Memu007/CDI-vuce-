# Reproducción ENTRADAS-4 (Dev MARIA), 2026-11-08

Sobre `6baddb5` (informe `67b38e4`), base `7f6862b`. Veredicto: **aceptada,
sin integrar**.

| Qué | Resultado |
|---|---|
| `chequeo-6.py 7f6862b 6baddb5` | `producto +1/−1`, avisos 0, historia vacío — igual al informe |
| `test_entradas4.py` + `test_entradas3.py` | `12 passed` |
| `entradas4_postgres.py` contra PG16 local | `NUL en cliente_id de /upload_excel_v2/: 200`, `fallas: 0` |
| `entradas4.sh 6baddb5` (con `PG_URL`) | BASE + 5 ROJO, `sabotajes con falla: 0` |
| Mío: que un `cliente_id` real siga mapeando (`test_clientes_plan04`, `test_maria5d`, `test_maria5_peso_excel`, `unit/test_main_upload`) | `55 passed` |

Diff de producto: una línea, `cliente_id` pasa a `TextoCodificable`
(`Annotated[str, AfterValidator(_guardable_en_pg)]`), igual que los demás
textos que van a la base.

No corrí la suite completa: tomo la de la Dev (`5215 passed`, dos formas).
Sin adversario propio: un tipo de campo en una ruta de subida, sin sesión,
permisos ni dinero; la Dev pasó Sonnet alto y `/code-review`.
