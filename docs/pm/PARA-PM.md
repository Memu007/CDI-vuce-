# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1: plan de la pieza de producto (sin producto)

| SHA | Qué |
|---|---|
| este commit | `docs:` este plan |

Producto +0/−0. **Emi no dijo que sí a D182**: según tu tarea, no arranco la
pieza de producto. Pasame la siguiente de la cola.

### Resultado

1. **(b), tal como la medí, arma un deadlock que tu negativo no ve.** Con (b)
   (`require_billing_vigente` + `commit` en la manual) y sin tocar
   `_cuenta_bloqueada`, `conexiones1_creditos.py` da rc=2 en 3 de 3 corridas.
   La fila es «NO VALE | organización, carrera: Invalida: alta 500 …», con
   `asyncpg.exceptions.DeadlockDetectedError: deadlock detected`. El par que
   choca es alta + recarga de la org, no alta + guardado. Tu negativo
   (alta + guardado) sobre el mismo árbol da «carrera: alta 200, guardado 200,
   deadlocks +0» en 3 de 3, igual que a vos.
2. **Causa medida.** Es la FK `organizations.owner_username → users`. El
   webhook hace un segundo `UPDATE` de la org en la misma transacción, y ese
   `UPDATE` corre el trigger de la FK, que pide `FOR KEY SHARE` sobre la
   dueña. Pero el alta tiene a la dueña con `FOR UPDATE` y espera a la org:
   cada una espera a la otra. Postgres lo dice así: «Process 8692 waits for
   ShareLock on transaction 785; blocked by process 8694». El 8692 es el
   alta, en `SELECT organizations … FOR UPDATE`. Lo reproduje mínimo, sin la
   app: con 2 `UPDATE` y el alta en `FOR UPDATE` hay deadlock; con
   `FOR NO KEY UPDATE`, ok.
3. **Arreglo medido:** `_cuenta_bloqueada` pasa a tomar los candados con
   `FOR NO KEY UPDATE`, que no choca con `FOR KEY SHARE`.
   - Créditos: rc=0 en 3 de 3, «pierden: 0; no valen: 0; sin carrera: 0», con
     las 4 fases en «quedan 10 de 10 pagos».
   - Tu negativo sobre el mismo árbol: 200/200 y deadlocks +0.
4. **Trampa de SQLAlchemy 2.0.25** (`requirements.txt:92`). Para la cache,
   `with_for_update()` y `with_for_update(key_share=True)` son la misma
   consulta, porque a `ForUpdateArg` le falta `key_share` en la clave. El
   alta reutiliza entonces el `FOR UPDATE` que ya compiló el webhook.
   - `key_share=True` solo: el log de Postgres muestra 0 «FOR NO KEY UPDATE»
     y los créditos siguen en rc=2.
   - Con `of=User` / `of=Organization` la clave cambia: 6 «FOR NO KEY UPDATE
     OF users…» y rc=0.
   - La 2.0.57 lo arregla (D200).

## Decisiones

Para Emi siguen abiertas D182, D183, D186 y D188; D184 ya está decidida. Las
mías:

- **D200. Cómo se pide `FOR NO KEY UPDATE`.**
  - (a) Con `of=` en las dos consultas de `_cuenta_bloqueada` (2 líneas), más
    el caso 6, que mira el SQL que llega a Postgres después de que el webhook
    compiló el suyo. **Recomendada.**
  - (b) Subir SQLAlchemy de 2.0.25 a 2.0.57 y usar `key_share` sin `of`, con
    suite completa.
  - Por qué (a): (b) cambia una dependencia de toda la app dentro de una pieza
    de plata. La subida va a la cola, con su propia suite.
- **D201. `require_active_billing` queda sin rutas con (b).** Hoy la usa sólo
  la manual (`main.py:3755`).
  - (a) Borrarla (~20 líneas), junto con lo que la nombra:
    - el reemplazo en `tests/test_maria1b_controles.py:40/44`, que ya hoy no
      hace nada, porque `/generate_maria` usa `require_billing_vigente`;
    - el paso de `tests/test_cobro_corte1.py:598`;
    - los docstrings de `tests/test_prelaunch_block2.py` (11, 499, 524) y
      `tests/test_prelaunch_block3.py` (12, 555, 561, 581). Sus casos le pegan
      a la ruta y siguen valiendo.

    **Recomendada:** §6 pide restar.
  - (b) Dejarla.
- **D202. Si la base se cae en el `commit` que suelta la conexión.** Los tres
  `commit` (vigente, analyze y NCM) cierran una transacción de sólo lectura.
  - (a) Uno solo, `_soltar_conexion(db)`, en los tres puntos: lo anota en el
    log y la ruta sigue con lo ya leído. **Recomendada.**
  - (b) Que el error suba en vigente y en analyze (500), como cualquier
    caída.
  - No medí en qué estado queda la sesión después de un `commit` fallido; lo
    mide el caso 4. Si la ruta escribe después y esa escritura no queda, el
    caso da rojo y paso a (b).
- **D203. Hasta dónde llega `FOR NO KEY UPDATE`.**
  - (a) Sólo en `_cuenta_bloqueada`. El caso 6 corre el par alta + aviso de
    suscripción. **Recomendada.**
  - (b) También en el candado del webhook (`main.py:11705`) y en
    `_cuenta_con_suscripciones` (11804/11816).
  - Si el caso 6 da rojo en algún par con (a), (b) entra en la pieza con ese
    rojo. El caso espejo (webhook contra alta) no está medido.
- **D204. `past_due` pisado por una renovación** (tu «leído, no medido»).
  También lo leí, sin medirlo.
  - El orden que temo: `require_billing_vigente` lee la cuenta sin candado;
    `_vencer_si_corresponde` ve `active` vencida más allá de la gracia; en
    el medio, el webhook renueva y confirma. Después `_vencer_y_guardar`
    escribe `billing_status=past_due` sobre la cuenta ya renovada. Quedaría
    pagada y bloqueada.
  - Pasa lo mismo hoy y con (b): (b) no toca esa lectura.
  - El caso 7 lo mide primero sobre HEAD. Si no reproduce, lo digo así y no
    toco nada. Si reproduce:
    - (a) Arreglarlo en la pieza: vencer con un `UPDATE` condicional
      (`WHERE billing_status=… AND trial_ends_at < …`), o vencer bajo
      `_cuenta_bloqueada`. Es la misma familia y la misma función.
      **Recomendada.**
    - (b) Pieza aparte.

## La forma: (b) más `FOR NO KEY UPDATE`

`main.py` +22/−5 (con D201 (a), unas 20 líneas menos). Es el árbol que medí;
cada parte con su caso:

| Cambio | Por qué | Caso |
|---|---|---|
| `_cuenta_bloqueada`: `.with_for_update(key_share=True, of=User)` y `(key_share=True, of=Organization)` | el deadlock con la FK; `of=` por la cache de 2.0.25 | 5 y 6 |
| `require_billing_vigente`: `_soltar_conexion(db)` después del 402 | la conexión no queda tomada mientras la ruta espera a la IA o al PDF | 1 y 4 |
| `create_manual_operation`: `_cobro=Depends(require_billing_vigente)` en lugar de `require_active_billing` | el tope se cuenta una vez, bajo candado, en `_contar_operacion_bloqueada` (eso es (b)) | 2, 3, 5, 6 y 8 |
| `analyze_client_migration`: `_soltar_conexion(db)` después de cargar los clientes; sin `db.refresh(batch)` | no retener la conexión mientras se lee el archivo; el `refresh` no se usaba | 1 y 4 |
| `sugerir_ncm`: `_soltar_conexion(db)` antes de esperar a Gemini | igual | 1 y 4 |
| `require_active_billing`: borrada (D201 a) | sin rutas | suite |

## Casos (uno por causa; las familias van como datos)

| # | Causa | Datos | Verde | Rojo mostrado una vez |
|---|---|---|---|---|
| 1 | La ruta espera sin retener conexión | las 9 rutas de `require_billing_vigente`, analyze incluida (`conexiones1_medir.py`) | ninguna conexión retenida mientras espera | sin el `_soltar_conexion` de vigente (su sabotaje, anclado en código) |
| 2 | El corte de una cuenta al día da 400 | `test_cobro_corte1.py` como está | pasa | el de su script |
| 3 | La impaga da 402 sin leer el cuerpo | cortado · JSON roto completo · 1×100 MB · 4×100 MB (`conexiones1_cuerpo.py`) | 402 y 0 retenidas; JSON roto completo sigue en 402 | leyendo el cuerpo antes del 402 (lo que hacía (a)) |
| 4 | La base se cae en el `commit` que suelta | vigente (`/process_operation/`) · analyze · NCM | la ruta contesta como sin caída y nunca da 200 con datos perdidos; el pedido siguiente funciona. Lo que el caso le cambia al motor o a la sesión vuelve en `try/finally` | `_soltar_conexion` sin `try` da 500 |
| 5 | Una recarga y un alta a la vez no pierden la recarga | `conexiones1_creditos.py`: usuario y org · control y carrera | rc=0, «quedan 10 de 10 pagos» | el arreglo revertido (hoy): rc=1, «quedan 0 de 10 pagos» |
| 6 | Dos rutas a la vez sobre la misma cuenta no se trancan | pares: alta + guardado · alta + recarga · alta + aviso de suscripción · generar MARIA + recarga; cuentas: usuario y org; créditos vencidos y no vencidos | 200/200, deadlocks +0 (`pg_stat_database`) y el SQL de `_cuenta_bloqueada` en «FOR NO KEY UPDATE OF» | (i) verde sobre un árbol sin `commit` antes de contar (hoy o (a)): guardado 500 y deadlock, como tu negativo; (ii) (b) sin `key_share`/`of`: alta 500 en alta + recarga de org |
| 7 | Una renovación no queda pisada por `past_due` | usuario y org; trial vencido y `active` fuera de gracia | se mide primero sobre HEAD (D204) | si reproduce, el rojo es HEAD |
| 8 | El tope de 10 sigue con (b) | `test_prelaunch_block2.py` y el conteo bloqueado de la manual | pasa | contar sin `_contar_operacion_bloqueada` |

El caso 6 es un script nuevo de ≤80 líneas sobre las funciones de
`conexiones1_creditos.py`, sin esperas fijas: espera a ver las consultas
esperando en `pg_stat_activity`. Captura el SQL con el evento
`before_cursor_execute`. No va en SQLite, porque SQLite no emite
`FOR UPDATE`.

`sabotajes_f.py` entra al repo con `SUELTA` y `COBRO` anclados en código.

## Los demás caminos de `require_active_billing` y `can_create_operation`

| Camino | Qué usa | Caso o razón |
|---|---|---|
| `/api/operations/manual` | hoy `require_active_billing`; con (b), vigente + `_contar_operacion_bloqueada` | 2, 3, 5, 6, 8 |
| `/api/clientes/{id}/operaciones` (guardar) | vigente + `_contar_operacion_bloqueada` | 6 (alta + guardado), 8 |
| `/generate_maria` y `/generate_maria_export` → `_contar_maria` | vigente + `_cuenta_bloqueada` + `_contar_en_la_cuenta` (`can_create_operation`) | cuentan bajo el mismo candado que el alta: la línea de `of=` los cubre. Van al caso 6 como dato: el par generar MARIA + recarga de la org, con su rojo sobre (b) sin `of=`. El conteo y el tope los cubren los casos existentes de `test_cobro_corte1.py` (370 a 530) |
| `DELETE /api/clientes/public/{id}` (`_cliente_con_cuenta_bloqueada`) | toma `_cuenta_bloqueada` y no cuenta | no lleva caso propio: el candado es el mismo y lo cubre `of=`. El caso 6 mira el SQL de esa función |
| `/process_operation/` (análisis de PDF), `/upload_pdf/public`, `/api/migrations/analyze`, `/api/migrations/{id}/confirm`, `/api/ncm/sugerir` | sólo `require_billing_vigente`; no cuentan | 1 (no retienen) y 4 (base caída, con `/process_operation/` como dato de vigente). No llaman a `can_create_operation` |
| Webhook de pagos (`main.py:11705`; recarga y suscripción) | su propio `with_for_update()` | 5 y 6 (pares con el alta); D203 |
| `/billing/topup` (`recarga_entra`, 11779) | lee `_expire_extra_ops` sin escribir | sin caso: no escribe la cuenta; la recarga la aplica el webhook |
| `cancel_billing`, `reactivate_billing`, `billing_checkout` (`_cuenta_con_suscripciones`) | `with_for_update()` sin `of` | no cuentan operaciones. Quedan como están por D203 (a); el caso espejo no está medido (riesgo) |
| «Otros planes» | `can_create_operation` mira `plan` dentro de la misma función | el plan es un dato de la cuenta, no otro camino: lo cubren los casos 2 y 8 |

## Puertas de la pieza (sobre el SHA que se entregue)

- `pytest -q --no-cov` completo desde base limpia.
- `scripts/testing/e2e_maria.sh`.
- `smoke_friccion.sh` y `ataque_aislamiento.sh`.
- `conexiones1_medir.py` con su sabotaje, `conexiones1_cuerpo.py`,
  `conexiones1_creditos.py` y el caso 6.
- `chequeo-6.py` entero.
- `/code-review high` y `/security-review`.
- Adversarios: Sonnet alto y Opus alto.
- Todo lo que ponen los casos, más sus rojos, se muestra una vez.

## Comandos copiables (probados sobre este SHA)

```bash
# 1. La trampa de la cache: tiene que mostrar «2.0.25 True False»
#    (sin of= comparten clave; con of= no).
DATABASE_URL=sqlite+aiosqlite:///:memory: ENVIRONMENT=test GEMINI_API_KEY=test-key PYTHONPATH=. python -c "
from sqlalchemy import select, __version__ as v
from proyecto_maria.database.models import User
k = lambda s: s._generate_cache_key()
print(v, k(select(User).with_for_update()) == k(select(User).with_for_update(key_share=True)), k(select(User).with_for_update()) == k(select(User).with_for_update(key_share=True, of=User)))"

# 2. Rutas por dependencia: tiene que mostrar 3755 con require_active_billing
#    y 8 líneas con require_billing_vigente.
grep -n -e "Depends(require_active_billing)" -e "Depends(require_billing_vigente)" proyecto_maria/main.py
```

Salida de las dos, corridas acá: `2.0.25 True False`; `3755:    db_user: User
= Depends(require_active_billing),` y 3840, 4611, 5032, 5296, 7147, 7245,
8132 y 10335 con `_cobro=Depends(require_billing_vigente),`.

Lo del resultado 1 a 3 (créditos, negativo y log de Postgres) lo corrí sobre
árboles sin commitear. Se reproduce con los casos 5 y 6 de la pieza: hoy no
hay copiable.

## No corrido

- Los casos 4, 6 (con los pares de recarga y aviso de suscripción, y los
  créditos no vencidos) y 7. Los rojos del caso 6 que no son tu negativo.
- Suite completa, `e2e_maria.sh`, revisiones y adversarios: van con la pieza.
- El caso espejo: webhook o `_cuenta_con_suscripciones` contra el alta con
  `FOR NO KEY UPDATE`.

## Riesgos

- Railway no espera a la CI. La CI deselecciona los presupuestos compartidos.
- D185 sigue como estaba.
- La FK de la dueña: cualquier transacción nueva que haga dos `UPDATE` de
  una org mientras otra tiene a la dueña con `FOR UPDATE` puede trancarse.
  Esa es la razón de D203.
- La cache de 2.0.25: otro `with_for_update(key_share=True)` sin `of` en el
  código no haría lo que dice. Hoy no hay ninguno; el caso 6 mira el SQL.
- D204, si reproduce, es plata en producción hoy, como D188.
