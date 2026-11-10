# Reproducción INTEGRAR-1, vuelta 2 (2026-11-10, PM principal)

**Veredicto: aceptada sobre `4555f7c4`** (merge `b9db0ad3`; producto
idéntico a `cbbd37b2`: `git diff --stat cbbd37b2 4555f7c4 -- . ':!docs/pm'`
vacío). **No es un SHA para publicar:** faltan las condiciones de abajo.

## Lo que corrí, sobre `cbbd37b2`

| Qué | Resultado |
|---|---|
| Suite completa, base limpia | `5907 passed, 110 skipped, 3 xfailed, 93 warnings in 1063.40s`, rc=0. Igual al informe |
| `ataque_aislamiento.sh` en Postgres | 47 bloqueados, 0 fugas, «PUERTA G3 PASADA», rc=0 |
| `aislamiento2.sh` | «sabotajes con falla: 0», rc=0 |
| CHANGELOG | las líneas de las dos ramas están |
| Arranque sobre base vieja (30533fe4 → merge, dos arranques) | 0→1 sólo agrega o ensancha (varchar→text, columnas nuevas de `client_product_history`, `cancelar_sin_confirmar`, tablas `limites_auth` y `ncm_historial` con sus índices y FK). 1→2: esquema igual salvo el token `\restrict` de pg_dump; filas iguales; sin errores en el log. Con foto previa y columnas viejas: `users` y `client_product_history` iguales |
| Mis sabotajes (4) | los 4 en ROJO: sin la variable hay demo (`test_cobro_mp2[sin_variable]`); el reset deja `active_jti` en NULL (`test_resetear_clave_revoca_todas_las_sesiones`); email mal escrito en el perfil (`test_update_user_profile_email_invalido_400`); vencido el bloqueo sigue contando (`test_reset_cinco_y_despues_uno_cada_quince_minutos`, `[429, 429]`) |
| Sabotaje g de `cobro_mp1` (D149), con el patrón al día | sin cambios «OK … guardar MARIA_FAC_V2.TXT», rc=0; con `saveOperationToHistory(items, {}, …)` en `finalize.js:779`: «FALLA … guardar null», rc=1. El ROTO del guion es patrón viejo; la garantía sigue |

### Una afirmación mía que retiro

En `PARA-DEV-2.md` (PRUEBA-LIMPIAR-1) escribí que con `descontar` usando su
propia conexión el caso `test_contar_intentos_usa_la_conexion_del_pedido`
daba rojo en los siete datos. Corrí dato por dato: el rojo es
`sqlite3.OperationalError: database is locked` en
`DELETE FROM limites_auth … RETURNING cuenta`, durante la preparación, no la
condición `maximo == 1`. No distingue el defecto. MARIA tenía razón. El
reemplazo exacto que usé fue, en `limites_auth.py`, la línea
`n = (await db.execute(delete(_T).where(_T.c.clave == propia).returning(_T.c.cuenta))).scalar() or 0`
envuelta en `async with _conn.engine.begin() as conn:` con `conn.execute`.

## Adversarios (sin red, `GEMINI_API_KEY` vacía)

**Opus, base adv_int1_opus. Un hallazgo medio, probado: un link de
presupuesto sobrevive a la baja del cliente.**
Pasos: crear clientes A y B; generar un MARIA; guardarlo en A; poner una
fila en `public_quotes` para esa operación (por SQL: `share_quote` pide red;
el snapshot se arma como `quote_router`); guardar la misma `operacion_id`
en B; borrar A. La fila queda y `GET /api/quotes/public/<token>` da 200 sin
login con los datos de A. Control: sin el paso a B, borrar A lleva los
presupuestos de 1 a 0.
- Es la familia de D141 (PRESUPUESTO-CLIENTE-1, sí de Emi). Pero el camino
  por `operacion_id` sólo existe en la unión: `save_client_operation` busca
  la operación con `_operacion_del_usuario`, que viene de la rama técnica.
  El arreglo de MARIA (`_soltar_link_de_otro_cliente`, en su rama) cuelga del
  camino por nombre de archivo (`_operacion_maria`), que la unión ya no usa.
- Probé la unión de su rama sobre `4555f7c4` en un worktree descartable:
  choca en `main.py`, `finalize.js`, `CHANGELOG.md` y
  `sabotajes/observabilidad1.sh`. La trae MARIA.
- Sin probar: hasta 10 TXT por una operación cobrada (es el diseño de D4 b,
  N = 10); `operationSavedFor` usa el nombre de archivo como clave; un email
  de invitación pendiente puesto en un perfil.

**Sonnet, base adv_int1_sonnet. Un hallazgo bajo, sólo de prueba.**
`tests/despacho1c_pantalla.js:75` simula el 402 con
`new Error('payment_required')` y `.motivo`; el `app_v2.js` unido lanza
`Error(lead)` con `.code = 'payment_required'` (COBRO-CORTE-1, `efaef2b6`) y
`finalize.js:1338` busca `.code`. Con el stub viejo el toast dice «Error de
red al guardar…»; con el real, «Venció tu prueba gratis. Suscribite para
seguir usando CDI.». El arnés está sólo en la rama de MARIA: nace al unir.
Sabotear `err.code === 'payment_required'` → `false`, o `err.message` →
`err.motivo` en ese toast, deja verdes `test_despacho1c.py` y
`test_front422.py` (sólo miran `tipo == "error"`). El producto está bien.
- Sin probar: las rutas nuevas de catálogo (`…/catalogo/despacho/guardar` y
  `leer`) no cortan por plan vencido, como las de catálogo que ya había;
  `_migrate_catalogo_sin_tope` con `lock_timeout` de 5 s bajo carga.
- Atacó sin hallazgo: migraciones con datos viejos, borrar cliente y guardar
  operaciones (20 rondas concurrentes sin 500 ni huérfanas), plan vencido en
  las seis rutas que cuentan, `file_security.py` por las dos subidas,
  registro.

El 409 de regeneraciones de MARIA no está en la unión a propósito:
COBRO-CORTE-1 (aceptada) lo cambió por «la undécima es otra operación»
(`REPRODUCCION-COBRO-CORTE-1-v2-2026-11-05.md`).

## Condiciones antes de publicar (nuevas)

1. PRESUPUESTO-CLIENTE-1 integrada sobre la unión, con este caso de
   aceptación en SQLite y Postgres: pasar por `operacion_id` a otro cliente,
   borrar el original, el GET público da 404; y el control sin pase.
2. El arnés de pantalla del 402 al día, con los dos sabotajes de Sonnet en
   rojo.
3. `_migrate_catalogo_sin_tope` (lock de 5 s) probado con una conexión
   abierta, como D156.

## Chequeo después de integrar

`git diff 4555f7c4 HEAD -- . ':!docs/pm' ':!.claude'` tiene que dar vacío.
