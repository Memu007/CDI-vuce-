# OBSERVABILIDAD-1, vuelta: reproducción de PM (2026-11-08)

Entrega de la Dev MARIA en `694f183` (informe `e2dd1e2`), base `0231eee`.
Veredicto: **devolución** (el arnés de ENTRADAS-3 queda en rojo).

| qué | informe | PM |
|---|---|---|
| `chequeo-6.py 0231eee 694f183` | +35/−15, avisos 0, historia vacía | igual |
| `pytest tests/test_observabilidad1.py` | 10 passed | `10 passed, 5 warnings in 1.47s` |
| arranque SQLite | `fallas 0` | `fallas 0` |
| arranque Postgres 16 | 60 OK, `fallas 0` | 60 OK, `fallas 0` (puerto 55462) |
| sabotajes con PG | 24 ROJO, sin rojo 0 | 24 ROJO, `sabotajes sin rojo: 0; no corridos: 0`, salida 0 |
| negativo PM: `or str(request.url.path)` en vez de `or "<sin ruta>"` | — | `AssertionError: la métrica guardó otra cosa que el molde: ['/no-existe-zq9']`, `1 failed` |
| negativo PM: `/static/20123456786-secreto.js`, `/api/quotes/public/abc123hash?token=zzz`, `/api/invitations/TOKENSECRETO999` | — | grabado `['/api/quotes/public/{hash}', '/api/invitations/{token}']` (static no se registra); nada crudo |
| `entradas3_postgres.py` con PG (ENTRADAS-3 aceptada) | no corrido | **`FALLA \| NUL en la ruta: 404; en api_logs: 0`, `FALLA \| ruta de 300 caracteres: 404; en api_logs: 0`, `fallas: 2`** |

## Adversario (Opus, alto, contexto nuevo)

- **Media, confirmada por la PM:** `scripts/testing/entradas3_postgres.py:60`
  busca la métrica por el camino crudo; con 694f183 da `fallas: 2`, con el
  `main.py` de `0231eee` da `fallas: 0`. `sabotajes/entradas3.sh` corta en la
  base y no mide sabotajes. Es la devolución.
- Baja: `error_message = str(e)` (main.py:1953) puede traer `[parameters: (...)]`
  de SQLAlchemy con valores ligados. No cambia con la pieza: riesgo.
- Baja: un índice llamado `ix_api_logs_owner_username` sobre otra columna
  hace que `CREATE INDEX IF NOT EXISTS` no cree nada y el log diga
  «agregado indice». Riesgo.
- Sin hallazgo: 404, 405, 307, OPTIONS, routers incluidos con prefijo,
  `/download/{filename}`, by-cuit: todos con molde o `<sin ruta>`; sin
  NameError posible en `agrega_columna`/`tiene_indice`; `--workers 1`.

## Decisiones

- D139 (a), decidida por la PM: escapar el panel, pieza chica después de ORG-1+D40.
- D140 de MARIA renumerada D142 (choca con la de la técnica): va a Emi; hasta
  entonces (c).
