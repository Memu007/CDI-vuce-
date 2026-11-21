# ADMIN-CREDITOS-1, tramos 1 y 2: `39d4dd8b` (informe `010e0dae`), 2026-11-21, PM

**Aceptada a la vuelta sobre `0f5ee58d`** (informe `c4cb73e4`), integrada con el merge de `54a533c1`
(`2c60ef94`): abajo, «La vuelta». Sin publicar y fuera de la candidata `0d7401ed`.

**Primer veredicto (12:08): vuelve.** No hay defecto de plata en el servidor. Vuelve por dos rondas de Postgres que
dicen «ok» sin comprobar lo que afirman, un error del panel con nombres de usuario que hoy se
pueden registrar, y dos detalles del informe. Base `0208ea9d`. Revisión fuerte (plata, permisos,
migración). Sin integrar.

## Diff

`git diff 39d4dd8b 010e0dae -- . ':!docs/pm'` vacío. La unión con mi rama no suma nada fuera de
`docs/pm`, `.claude` y `AGENTS.md`. `chequeo-6.py 0208ea9d 39d4dd8b` igual al informe: «producto
+195/−52», AVISO de 143 netas (explicación suficiente), «arnés +959/−54», historia vacía, «avisos: 1».
El tramo 1 (`247d6440..0208ea9d`, `billing_service.py`) sólo agrega `acreditar_extra` y un parámetro
con valor por defecto a `recarga_entra`: los llamadores de antes no cambian.

## Lo que corrí (worktrees en `39d4dd8b`)

| Qué | Resultado |
|---|---|
| `anclas_perdidas.py` | rc=0, 0 perdidas, los mismos 6 «SIN ANCLA» de `limpieza1.sh` |
| `admin_creditos1_postgres.py` (PG16 descartable) | «filas MAL: 0; rondas sin armar: 0»; migración «creditos_admin con 0 filas; 21 tablas más, cambios: ninguno», rc=0 |
| `admin_usuarios1_postgres.py` | 9 casos, «fallas: 0», rc=0 |
| `sabotajes/admin_creditos1.sh` | **rc=126 «Permission denied»** tal como está en el informe (modo 100644). Con `bash`: 26 ROJO, BASE «35 passed, 5 warnings», «sabotajes sin rojo: 0», rc=0 |
| `sabotajes/admin_creditos1_postgres.sh` | **«sabotajes sin rojo: 1»**, rc=1: abajo |
| suite completa, worktree limpio | `6276 passed, 110 skipped, 3 xfailed, 112 warnings in 1226.22s`, rc=0. Las 2 de más: «Event loop is closed» en hilos de aiosqlite, en `test_datos1` y `test_sesion1` (fuera de la pieza, máquina con carga 6) |
| `cobro_mp1.sh` entero | 145 ROJO, 0 ROTO/PATRÓN/MAL, BASE en verde, el VERDE de D31 sigue verde, «sabotajes con falla: 0», rc=0, 3618 s |
| `cobro_corte1.sh` entero | 87 ROJO, BASE en verde (también la pantalla y el lock), «sabotajes con falla: 0», rc=0, 4011 s (la primera corrida la cortó el tope de 2 h en 63 ROJO; repetida sola) |
| mis negativos en SQLite | sin negativo 35 passed; registro con `cuenta=username`: 2 failed; `vigentes_antes` mal: 5 failed |

## Por qué vuelve

1. **El choque de la clave entre dos cuentas (caso 8) se arma a veces sin choque.** El sabotaje
   «sin atrapar el choque de la clave» dio verde 3 de 26 veces: 1 en su guion de sabotajes, 0 en 5 y
   2 en 20 corridas mías (en rojo: `[200, 500]`; en verde: `[200, 409]`). La ronda espera a que los dos pedidos estén frenados en el candado de las
   cuentas, no a que los dos hayan buscado el pedido. A veces el segundo busca después del commit
   del primero, ve la fila y va por el 409 sin pasar por el choque. Lo mismo pasa sin sabotaje, y
   «rondas sin armar: 0» lo cuenta como armada. El producto está bien por los dos caminos.
2. **El guardado y la carga a la vez (caso 10) no distingue la falta de candado.** Ninguno de los
   tres sabotajes de Postgres pone en rojo una fila «carga + guardado» o «guardado + carga». El alta
   de la ronda (`items: []`) no gasta créditos, así que no escribe lo que el candado protege.
   Negativo mío con la ronda de Opus, donde el alta gasta un extra, en PG16 descartable:
   - sin sabotaje, 3 de 3 «filas MAL: 0»;
   - con «la carga sin candado», 3 de 3 «filas MAL: 2», `alta primero`, usuario y org: «extra 12
     (esperaba 11)». El crédito gastado se pierde.
3. **El panel usa un objeto común con el nombre de usuario como clave.** `const sinConfirmar = {}`
   (`dev_dashboard.html`). En el SHA, `/auth/register` acepta `constructor`, `__proto__`,
   `toString` y `hasOwnProperty` (200 los cuatro). Con la ronda de Opus sobre el HTML del SHA, al
   abrir el diálogo de `constructor` dice «La carga de undefined no se confirmó: si la enviás de
   nuevo, no se carga dos veces.». Corrí sólo abrir el diálogo; el envío no lo corrí. La familia es toda
   clave heredada de `Object.prototype`.
4. `sabotajes/admin_creditos1.sh` entró sin permiso de ejecución: el comando copiable del informe
   falla.
5. El informe pone `cobro_corte1.sh` sobre `39d4dd8b` en la tabla y sobre `87985bba` en el texto, y
   no dice sobre qué SHA corrió `/security-review`.

## Adversarios (sin red, `GEMINI_API_KEY` vacía, PG16 descartable)

- **Sonnet alto:** nada serio. Matriz del webhook de 220 escenarios, base contra cabeza, sin
  diferencias. Entradas raras dan 422/404, sin 500. Bajo, nuevo: cargar a una cuenta `past_due` o
  `canceled` da 200 sin aviso. Bajo, ya en la base: `/api/billing/me` muestra extras vencidos.
- **Opus alto:** ningún defecto del servidor.
  - Medio: el mecanismo de D237. Ya existe en la base con dos recargas; la carga del admin es otra
    forma de dispararlo.
  - Bajo: el punto 3 de arriba.
  - Nota de diseño: reabrir con la carga en vuelo y mandar otra cantidad aplica las dos. Es lo que
    dice el panel («otra cantidad es otra carga»).

## Lo que queda escrito

- **D237** (plata) va a Emi, con la recomendación (a). El pago rechazado queda a la vista en el panel
  de admin («Pagos de Mercado Pago rechazados», `/api/dev/pagos-mp-rechazados`). No frena la vuelta: lo entregado es (a).
- **D238 (a), decidido por la PM.** `last_topup_at` sólo se lee en el panel de admin
  (`admin_router.py:401`, `:415` y `:438`, «ultima_recarga»). Ninguna regla lo usa.
- **Cargar a una cuenta `past_due`:** riesgo bajo, escrito. Avisarlo en el panel es propuesta para
  Emi; no entra.
- Sus supuestos (sin claves foráneas en `creditos_admin`, `pedido` en mayúsculas da 422) y sus
  riesgos se sostienen como los escribe.
- No corrido por la PM: `/code-review` (lo cubren Opus y Sonnet alto y su `/security-review`), y
  `e2e_maria.sh` (la pieza no toca el recorrido MARIA).

## La vuelta: `0f5ee58d` (informe `c4cb73e4`), 14:09 UTC, aceptada

`git diff 0f5ee58d 54a533c1 -- . ':!docs/pm' ':!.claude' ':!AGENTS.md'` y lo mismo contra `2c60ef94`:
vacíos. `chequeo-6.py 39d4dd8b 0f5ee58d`: «producto +6/−6», «arnés +143/−22», historia vacía,
«avisos: 0»; desde la base `0208ea9d`, igual a su informe. El producto es sólo `dev_dashboard.html`
(`const sinConfirmar = new Map()`); ningún `.py` de `proyecto_maria/` cambió desde `39d4dd8b`.

| Qué (worktree en `0f5ee58d`, PG16 descartable) | Resultado |
|---|---|
| `anclas_perdidas.py` | rc=0, los mismos 6 «SIN ANCLA» de `limpieza1.sh` |
| `admin_creditos1_postgres.py` | «filas MAL: 0; rondas sin armar: 0», rc=0 (una corrida) |
| `sabotajes/admin_creditos1.sh` (ahora 100755) | 27 ROJO, BASE «35 passed», pantalla OK, «sabotajes sin rojo: 0», rc=0 |
| `sabotajes/admin_creditos1_postgres.sh` | 11 sabotajes en rojo («la carga sin candado» 6, «la cuenta sin candado» 10, «la recarga sin candado» 4), «sabotajes sin rojo: 0», rc=0 |
| `sabotajes/admin_creditos1_postgres_veces.sh` | «rojas: 20 de 20», todas `[200, 500]` armadas |
| casos de cobro que leen el panel, anclas y admin en SQLite | `195 passed`, rc=0 |

**Mis negativos, con ejemplos que no di:**

1. **El orden tarde, forzado.** Parcheé la ronda del caso 8 para que la segunda cuenta mande su
   pedido recién después del rollback del candado: rc=4, «SIN ARMAR | el mismo pedido para dos
   cuentas | … | [200, 409] | NO SE ARMÓ», «rondas sin armar: 1». Ya no sale «ok».
2. **Mi forma del candado sacado:** la carga busca la cuenta sin bloquearla. rc=1, «filas MAL: 6»: las
   cuatro «recarga + carga» y «guardado + carga, créditos al día, al tope: quedan 12, esperaba 11»
   (usuario y org). Coincide con su fila. El caso 10 ahora distingue en las dos direcciones.
3. **Otras claves heredadas.** La pantalla con `isPrototypeOf`, `propertyIsEnumerable`,
   `toLocaleString` y `__lookupGetter__`, y reabrir sobre `isPrototypeOf`: con el HTML nuevo «OK»,
   rc=0; con el de `39d4dd8b`, «FALLA: abrir isPrototypeOf: … La carga de undefined no se
   confirmó…», rc=1.

**Lo que queda escrito:**

- La ronda «guardado y después carga con créditos vencidos» no se corre (`admin_creditos1_postgres.py:148-149`):
  la carga vence lo viejo igual, así que da 7 con candado o sin él. Las otras celdas de la familia sí
  distinguen (mi negativo 2), así que la causa queda cubierta.
- `/security-review` sugirió `Depends(require_admin)` en la ruta. **Decidido por la PM: no hace falta.**
  El router se monta con `require_admin` (`main.py`), el caso `no_admin` da 403 y el sabotaje «las rutas
  de admin no piden admin» da rojo («assert 200 == 403»).
- Sus riesgos, bajos y escritos, sin pieza: `previa` borrada entre el choque y la relectura, y `.one()`
  con la cuenta borrada (500 en una carrera con un borrado que hoy no tiene ruta);
  `fetchUsuarios(0)` vuelve a la primera página; `crypto.randomUUID()` sólo con HTTPS o `localhost`
  (Railway sirve HTTPS); `con_pg16.sh` ignora `TMPDIR` (arnés); `past_due`/`canceled` dan 200.
- No corrido por la PM en la vuelta: la suite, `cobro_mp1.sh` y `cobro_corte1.sh` (el servidor no
  cambió desde `39d4dd8b`, donde los corrí; su `cobro_corte1` sobre `8d6829ea` dio 87 ROJO),
  adversarios y `/code-review`.
- Al publicar: copia de la base antes (tabla nueva `creditos_admin`).
