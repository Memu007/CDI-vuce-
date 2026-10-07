# Ataque al candidato de la segunda publicación — 2026-10-07

**Veredicto: se puede publicar `6ea8ca9`** (la cabeza de la rama de la PM,
`70c416d`, tiene el mismo producto), si antes Emi sabe qué cambia en el TXT y
qué le va a pedir la pantalla. Suite sobre `6ea8ca9`: `1224 passed, 102
skipped, 1 xfailed`. No cambia el esquema; en `requirements.txt`, sólo -PyPDF2,
-python-jose, +pypdf.

Subagente de la PM, Opus alto, sólo en local. Usó Postgres 16, con una base
armada con `5cb03ab` (lo publicado hoy) y el candidato arrancado encima con
`ENVIRONMENT=production`.

| # | Qué pasa | Qué se hace |
|---|---|---|
| 1 | **Ya en producción:** guardar una operación cuyo producto tiene la posición SIM completa (`84714900100D`) da 500 y no se guarda nada: `client_product_history.ncm` es `String(10)` (`database/models.py`), y el error salta en el `commit`. Con una NCM de 8 dígitos guarda (lo que probó Emi en el ensayo). En las pruebas no se ve porque SQLite no controla el largo | **GUARDAR-1**, urgente, después de la publicación. Hasta entonces, el TXT sale y se descarga, pero la operación con SIM completa no queda guardada |
| 2 | Arranque: el esquema no cambia (`pg_dump --schema-only` igual), arranca en ~3 s y `/health` da 200. La línea «Billing cron» sólo se imprime si pasa a alguien a impago: que no aparezca está bien | — |
| 3 | Lo guardado con `5cb03ab` se lee bien con el candidato (clientes, operaciones, exportar, métricas), y volver a `5cb03ab` después funciona | — |
| 4 | Sesiones: `python-jose` no se usaba (todo es PyJWT); un token de una versión vale en la otra | — |
| 5 | Un catálogo de columnas de Excel guardado con dos columnas para el mismo campo da 400 al volver a guardarlo, con un mensaje claro | Emi deja una sola |
| 6 | El Excel lee más que antes (números con coma, «Precio Unitario» contra total) | Mejora |
| 7 | Respuesta vieja de Gemini (`USD`, `peso_kg`, nulos, `CHN`): entra; «USD» queda y la revisión lo marca; «CHN» y «China» salen `CN` (antes `CH`, Suiza). Sin PyMuPDF funciona | Emi cambia USD por DOL en la revisión |
| 8 | Imagen: el `Dockerfile` tal cual no se pudo construir (la red bloquea apt); una variante sin apt arranca con `ENVIRONMENT=production` y da el mismo TXT byte por byte | — |
| 9 | Ya pasaba: un PDF con clave de dueño da 400 «Encrypted PDFs are not allowed» | Se anota |
| 10 | Rutas sacadas sin llamadores (`/upload_excel/`, `/upload_excel/public`, `/api/clientes/import`); una nueva, `/generate_maria/avisos`, con sesión | — |

## El TXT cambia en (pedido FOB normal, 3 productos)

- `CARTUSO` 3 → 2 («Nuevo sin uso importado»; se elige por producto).
- `IVAADICIONAL1` `IVAAD1` → `NO_VALIDA` (reventa, por defecto; se cambia por
  operación o producto).
- La fecha siempre DD/MM/AAAA, y el CUIT del importador sin guiones.
- Líneas opcionales nuevas: banco y empresa de digitalización.

## Ahora pide (antes generaba igual)

- La fecha de emisión válida (antes ponía la de hoy).
- La moneda («USD» se escribe DOL; EUR genera con aviso) y el incoterm.
- El CUIT del importador, con el dígito verificador correcto.
- El estado de la mercadería si el origen es argentino.
- Además, propone el 0 perdido de la NCM, y una procedencia o un banco mal
  escritos dan 400.

## No corrido

El `Dockerfile` tal cual (apt bloqueado), Gemini real, PyMuPDF, OCR,
Railway, `.xls`.
