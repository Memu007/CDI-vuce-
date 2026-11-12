# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1 C (sólo arnés): el rojo con otra cuenta está. Mientras otra cuenta satura, quien sólo consulta espera 30 s en `/api/ncm/sugerir`, y en la subida pública 30 s (6,5 s con la cuota de producción). El arreglo propuesto, sin commitear, lo baja a 0,45 s o menos. Decide Emi: D182

| Qué | SHA |
|---|---|
| Base | `8d61bb09` |
| Arnés: el medidor mide a otra cuenta y separa pool lleno de fuga | `33c61162` |
| Arnés: pool lleno sale con 4, no con 3 (el 3 es de `con_pg16.sh`) | `76b50666` |
| Informe | el commit `docs:` encima de `76b50666` |
| Corridas de hoy | `76b50666`, código de producto igual a la base |
| Corridas del arreglo | `76b50666` más el diff de abajo, sin commitear |

**Producto tocado: ninguno.** `chequeo-6` da `producto +0/−0` y `arnés +58/−27`.

## Decisiones

**D182. ¿Entra el arreglo que suelta la conexión antes de esperar?** Decide Emi: la fila del roadmap dice «arreglar sólo si las deja», y no las deja.
- (a) Entra tal como está abajo: un `commit` al final de `require_billing_vigente` y otro en `sugerir_ncm` antes de esperar a Gemini. Lo acompaña el ajuste de una línea al inyector de fallas de `test_cobro_corte1.py`.
- (b) Igual que (a), y además lo mismo en `require_active_billing`, que tiene el mismo patrón y no medí.
- (c) No entra, y queda la espera de 30 s para la otra cuenta mientras alguien satura.

**Recomiendo (a).** Cumple el criterio en las dos configuraciones, y (b) sumaría una ruta que no medí. Si entra, va como pieza con `/entregar`: subagentes, `/code-review`, `/security-review` (toca sesión de base y cobro) y la suite completa.

**Supuesto reversible: el criterio.** Lo propongo así:
- la otra cuenta recibe 0 × 500 y espera como máximo 5 s (`--espera-otra 5`, el valor por defecto del medidor);
- la cuenta que satura recibe sólo 422, 429 o 504.

## Resultado, para la otra cuenta

Todas las corridas son `--pico 60 --lento 30`, en gunicorn más Postgres 16 descartable (`con_pg16.sh`).
- Pool: 20 + 30 = 50 conexiones, con `pool_timeout` de 30 s.
- La otra cuenta hace 12 pedidos rápidos por pico.
- «máxT / máxPG» es el máximo de conexiones tomadas según el pool y según `pg_stat_activity`.

### Código de hoy (`76b50666`)

| Corrida | Pico | Otra cuenta: 500 | Otra cuenta: espera máx. | Códigos de la cuenta que satura | máxT / máxPG |
|---|---|---|---|---|---|
| sin cuota | login (bcrypt) | 0 | 3.38 s | 401 × 60 | 50 / 50 |
| sin cuota | sugerir (Gemini) | 0 | **30.08 s** | 200 × 60 | 50 / 50 |
| sin cuota | subida pública de PDF | 0 | **30.01 s** | 422 × 16 · 500 × 10 · 504 × 34 | 50 / 50 |
| cuota de producción | login (bcrypt) | 0 | 3.85 s | 401 × 60 | 50 / 50 |
| cuota de producción | sugerir (Gemini) | 0 | **30.06 s** | 200 × 60 | 50 / 50 |
| cuota de producción | subida pública de PDF | 0 | **6.51 s** | 422 × 16 · 429 × 25 · 504 × 19 | 50 / 50 |

- **Las dos corridas salen con rc 4:** «POOL LLENO: ninguna conexión quedó tomada, pero la otra cuenta o el log sufrieron».
- **No es una fuga.** Al final quedan `tomadas` 0, `close_empezados` = `close_terminados` y `apilog_creados` = `log_tareas_fin` = 667.
- **Sin cuota, los 10 × 500 son de la cuenta que satura**, no de la otra. Son `TimeoutError` del pool. El log tiene `QueuePool limit` 50, `Exception in ASGI application` 10 y `Traceback` 60.
- **Con la cuota de producción el log queda limpio:** `QueuePool limit` 0, `Exception in ASGI application` 0 y `Traceback` 0. Igual, la otra cuenta espera 30.06 s en sugerir y 6.51 s en la subida.
- **El login no empeora:** 3.38 s y 3.85 s, dentro de los 3,1 a 3,7 s de antes salvo el 3.85. El margen contra los 5 s es fino (riesgos).

**La causa, leída en el código.**
- `require_billing_vigente` lee la entidad de cobro y deja abierta la transacción de lectura. La conexión queda tomada hasta que la sesión cierra al final del pedido.
- `sugerir_ncm` además lee el catálogo y el historial y después espera hasta 30 s a Gemini con esa conexión tomada.
- Con 50 pedidos lentos en vuelo, el pool se llena, y el pedido rápido de la otra cuenta espera a que se libere una.

### Con el arreglo propuesto (mismo medidor congelado, worktree descartable)

| Corrida | Pico | Otra cuenta: 500 | Otra cuenta: espera máx. | Códigos de la cuenta que satura | máxT / máxPG |
|---|---|---|---|---|---|
| sin cuota | login (bcrypt) | 0 | 3.48 s | 401 × 60 | 50 / 50 |
| sin cuota | sugerir (Gemini) | 0 | **0.45 s** | 200 × 60 | **24 / 27** |
| sin cuota | subida pública de PDF | 0 | **0.05 s** | 422 × 16 · 504 × 44 | 50 / 50 |
| cuota de producción | login (bcrypt) | 0 | 3.13 s | 401 × 60 | 50 / 50 |
| cuota de producción | sugerir (Gemini) | 0 | **0.38 s** | 200 × 60 | **26 / 27** |
| cuota de producción | subida pública de PDF | 0 | **0.05 s** | 422 × 16 · 429 × 25 · 504 × 19 | 50 / 50 |

- **Las dos corridas salen con rc 0:** «sin conexiones tomadas».
- **En total hay 0 × 500**, y el log da 0 en cada contador: QueuePool, ASGI y Traceback.
- **`close_con_transaccion` baja de 280 a 105.** Son los cierres de sesión que encontraron una transacción abierta.
- **Al final, en las dos:** `tomadas` 0, `close_empezados` = `close_terminados` = 2992 y `apilog_creados` 667.
- **Los cortes de 30 s siguen.** `corte_gemini` (30.02 s y 30.01 s) y `corte_pdf` (30.04 s y 30.01 s) son la duración de los pedidos cortados, no la espera de la otra cuenta.

### El diff propuesto, sin commitear

```diff
--- a/proyecto_maria/main.py
+++ b/proyecto_maria/main.py
@@ -2303,6 +2303,9 @@ async def require_billing_vigente(
     await _vencer_y_guardar(db, entidad)
     if not billing_service.tiene_acceso(entidad):
         raise HTTPException(status_code=402, detail=_detalle_402(entidad))
+    # Termina la transacción de lectura: si no, la conexión queda tomada
+    # mientras el endpoint espera a la IA o a la lectura del PDF.
+    await db.commit()
     return db_user
 
 
@@ -10448,6 +10451,7 @@ async def sugerir_ncm(
         # (RENDIMIENTO-1). Si no contesta a tiempo, se sigue sin sus sugerencias.
         import asyncio
         limite = _segundos_de_entorno("NCM_GEMINI_TIMEOUT_S", 30.0)
+        await db.commit()
         try:
             de_gemini = await asyncio.wait_for(
```

Y el ajuste que necesita el inyector de fallas de `test_cobro_corte1.py`, también sin commitear:

```diff
--- a/tests/test_cobro_corte1.py
+++ b/tests/test_cobro_corte1.py
@@ -828,7 +828,8 @@ _confirmar = main.AsyncSession.commit
 
 async def _commit_que_falla(self):
     # La autenticación confirma antes de la ruta: falla sólo el de main.py.
-    if sys._getframe(1).f_code.co_filename != main.__file__:
+    quien = sys._getframe(1).f_code
+    if quien.co_filename != main.__file__ or quien.co_name == "require_billing_vigente":
         return await _confirmar(self)
     raise RuntimeError("la base se cayó al confirmar")
```

**Por qué el ajuste.**
- El inyector hace fallar cualquier `commit` llamado desde `main.py`, para simular que se cae el `commit` de la ruta.
- Con el arreglo, el primer `commit` desde `main.py` es el de la dependencia, que corre antes de la ruta. La falla salta ahí y el caso ya no prueba lo que dice.
- Sin el ajuste fallan 4 casos, con `RuntimeError: la base se cayó al confirmar`:
  - `test_lo_no_entregado_no_queda_cobrado[importacion_al_confirmar]`;
  - `test_regenerar_con_una_falla_deja_entero_lo_ya_entregado`, con `[al_confirmar]`, `[al_confirmar_y_deshacer]` y `[al_confirmar_sin_enlaces]`.
- Con el ajuste pasan.
- Si la base se cae en ese `commit` nuevo, pasa lo mismo que si se cae el `commit` con que ya termina `get_current_user`: un 500 sin escribir nada.

**Qué se confirma en cada punto nuevo.** Lo leí en el código. Ninguna de estas funciones deja algo pendiente de escribir al llegar al `commit` nuevo:
- `get_current_user` ya termina con su propio `commit`.
- `_vencer_y_guardar` confirma sólo si cambió algo y, si falla, deshace.
- `_get_billing_entity`, `lookup_client_memory`, `match_items` y `load_ncm_historial` sólo leen: no tienen `db.add`, `flush` ni `commit`.
- Con `expire_on_commit=False`, el usuario y la entidad leídos siguen usables después del `commit`.

**Los 8 endpoints que pasan por `require_billing_vigente`:**
- `/process_operation/`;
- `/upload_pdf/public`;
- `/generate_maria` y `/generate_maria_export`;
- `/api/migrations/analyze` y `/api/migrations/{batch_id}/confirm`;
- `/api/clientes/{client_id}/operaciones`;
- `/api/ncm/sugerir`.

En todos, el cuerpo arranca con una transacción nueva.

**Subida de PDF: es zona de MARIA (D74).** El arreglo no toca su código, pero cambia la transacción con la que entra a `/upload_pdf/public`. ¿Se lo pasás?

## Comandos

```bash
# 1. Rojo de hoy: rc=4 y «POOL LLENO…»; «pico_gemini: la otra cuenta recibió 0 × 500 y esperó hasta 30.xx s».
scripts/testing/con_pg16.sh python scripts/testing/conexiones1_medir.py --pico 60 --lento 30; echo rc=$?

# 2. Lo mismo con la cuota de producción: rc=4; pico_pdf de la otra cuenta en ~6.5 s y pico_gemini en ~30 s.
scripts/testing/con_pg16.sh python scripts/testing/conexiones1_medir.py --pico 60 --lento 30 --cuota-de-produccion; echo rc=$?

# 3. El arreglo: guardá los dos diffs de arriba en /tmp/arreglo.diff y corré el 1 en un worktree.
#    Tiene que dar rc=0, «sin conexiones tomadas» y la otra cuenta por debajo de 0.5 s en pico_gemini y pico_pdf.
git worktree add --detach /tmp/wt-c 76b50666 && cd /tmp/wt-c && git apply /tmp/arreglo.diff
scripts/testing/con_pg16.sh python scripts/testing/conexiones1_medir.py --pico 60 --lento 30; echo rc=$?

# 4. Control del medidor: cinco BIEN y rc=0.
PY=python scripts/testing/sabotajes/conexiones1.sh 76b50666; echo rc=$?
```

## Puertas

| Puerta | Salida |
|---|---|
| Medidor, hoy, `--pico 60 --lento 30` | rc=4 · POOL LLENO · otra cuenta 30.08 s en sugerir y 30.01 s en subida |
| Medidor, hoy, con `--cuota-de-produccion` | rc=4 · POOL LLENO · otra cuenta 30.06 s en sugerir y 6.51 s en subida |
| Medidor, arreglo, `--pico 60 --lento 30` | rc=0 · sin conexiones tomadas · otra cuenta 0.45 s y 0.05 s |
| Medidor, arreglo, con `--cuota-de-produccion` | rc=0 · sin conexiones tomadas · otra cuenta 0.38 s y 0.05 s |
| `sabotajes/conexiones1.sh` sobre `76b50666` | 5 BIEN · rc=0 |
| pytest en el arreglo, sin el ajuste del inyector: billing, cobro, sugerir, catálogo, CSRF y rendimiento (11 archivos) | 4 failed · 341 passed (los 4 de arriba) |
| pytest en el arreglo con el ajuste: `test_cobro_corte1.py` y `test_excel2b.py` | 201 passed |
| Los 4 casos en `76b50666`, sin arreglo | 9 passed (los dos casos completos) |
| `chequeo-6 8d61bb09 76b50666` | avisos: 0 |

Las 5 líneas del control del medidor:

```
BIEN  | sin sabotaje: salida 0, dice «sin conexiones tomadas»
BIEN  | close_cancelado: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | close_cancelado_suelto: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto guarda la sesión sin cerrar: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto suelta la sesión sin cerrar: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
```

<details><summary>chequeo-6, salida entera</summary>

```
chequeo-6 8d61bb0909d18ccd7f773d41743241f75ebe0af0..76b50666: avisos para mirar, no un veredicto
producto +0/−0
arnés +58/−27
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

</details>

**Qué no corrí**
- La suite completa con el arreglo: sólo los 11 archivos de la tabla y, con el ajuste, los dos de cobro y Excel. Si entra, va completa.
- Subagentes, `/code-review` y `/security-review`: lo commiteado es arnés, y el arreglo es una propuesta. Si Emi dice que sí, el arreglo pasa por los tres.
- `require_active_billing` en el medidor.

**Riesgos**
- **El arreglo es general.** Cambia la transacción de 8 endpoints, no sólo de los dos medidos. Ninguno deja algo pendiente al llegar al `commit` nuevo, según lo que leí en el código. Una dependencia futura que escriba sin confirmar antes de `require_billing_vigente` quedaría confirmada ahí, antes de la ruta. Hoy no hay ninguna.
- **La subida es zona de MARIA:** su cuerpo empieza con la conexión ya suelta. No leí su código más allá de lo que toca la sesión.
- **`require_active_billing` tiene el mismo patrón** y no lo medí.
- **Sin explicar: en la subida y el login, máxT / máxPG sigue en 50 / 50 con el arreglo.** Aun así, la otra cuenta no espera (0.05 s y ≤3.48 s). No sé qué retiene esas conexiones. En el login, bcrypt corre con la conexión tomada.
- **El login tiene poco margen:** 3.13 a 3.85 s contra los 5 s del criterio.

**Archivos de producto tocados:** ninguno. Si D182 dice (a): `proyecto_maria/main.py` y `tests/test_cobro_corte1.py`.
