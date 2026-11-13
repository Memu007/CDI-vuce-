# Reproducción de D199 y de `sabotaje_valor1.sh` (2026-11-13)

Entrega de MARIA: arnés `fe0f1b4`, informe `4b5ef688`, base `0609e14`. Sólo
arnés (producto +0/−0). Revisado por la PM principal en un worktree aparte en
`fe0f1b4` (`/tmp/cdi-pm/wt-maria`), con los guiones de esa versión.

## Mi primera corrida no vale

Volví a correr los tres guiones desde mi rama (`08ae9654`) y no desde
`fe0f1b4`: `sabotaje_valor1.sh` cortó con `PATRON NO ENCONTRADO` después de 12
`ROJO`, porque mis anclas eran las viejas. Corté los procesos por PID, aparté
esos registros y repetí todo desde el worktree de `fe0f1b4`. Es el mismo
escape que el 2026-11-12 (`REPRODUCCION-CATALOGO-LARGO2-2026-11-12.md`): el
guion que se reproduce es el del SHA entregado.

## Lo reproducido (guiones de `fe0f1b4`, Postgres 16 local)

| qué | salida |
|---|---|
| `sabotajes/catalogo3.sh fe0f1b4` | 51 `ROJO`, `fallas: 0`, salida 0. El sexto es el de D199: `ROJO` en `test_un_proveedor_latino_conserva_su_id[Industrias Garc` (igual al informe) |
| `sabotajes/catalogo_largo2.sh fe0f1b4` | 37 `ROJO`, `fallas: 0`, salida 0; los «FALLA» que aparecen son texto esperado dentro de líneas `ROJO` (igual) |
| `sabotaje_valor1.sh fe0f1b4` | 30 `ROJO`, `FALLA  mal_escrito_se_borra: quedó verde`, `FALLAN 1 sabotajes`, salida 1 (igual: es D222) |
| `chequeo-6` por tramo | producto +0/−0 y 0 avisos en los dos tramos |
| `anclas_perdidas.py fe0f1b4` | ninguna fila de los tres guiones |
| `git diff --stat fe0f1b4 4b5ef688` | sólo `docs/pm/PARA-PM-2.md` |

**Negativo mío de D199.** Con `NFD`→`NFKC` en `_normalize` (otro borde, no el
del guion), `tests/test_catalogo3.py` da 6 failed: la prueba también ve que se
pierda la descomposición, no sólo la compatibilidad.

**Negativo mío de D222.** Con la mutación del sabotaje 24 aplicada, las
pruebas de `valor1` dan 75 passed, y `separadores1` con las vecinas, 501
passed: ninguna prueba de hoy mira esa guarda. Confirma el verde del informe.

## D221: se retira el sabotaje 13 (b)

Comprobado leyendo y corriendo:

- en `montos_ar.js` todo retorno con error lleva `valor: null`, así que
  `r.error ? null : r.valor` y `r.valor` dejan el producto igual;
- el ancla `        return r.error ? String(v).trim() : r.valor;` aparece una
  sola vez en `finalize.js`;
- `sabotaje_separadores1b.sh` no está en `sabotajes-conocidos.txt`, y su
  sabotaje 5 (líneas 101–102, `return r.valor;`) aplicado a mano da 4 failed,
  entre ellos `[abc-ajusteDelPedido]`;
- en `valor1`, el sabotaje 14 (`pedido_sin_deducir`, líneas 125–128) dio
  `ROJO` y mantiene nombrado
  `test_el_pedido_manda_los_ajustes_y_nunca_algo_que_frene_el_txt`.

El 13 no distingue nada que no distinga `separadores1b`. Se retira.

## D222: se retira el sabotaje 24 (a), pero sacar la guarda no es limpieza

El sabotaje se retira: ninguna prueba de hoy lo ve. Lo que no acepto es la
premisa de que las dos guardas de `pintarValor` «no hacen nada que se vea».
Leyendo el código hay un camino de hoy donde sí actúan, **y lo que muestran
parece un defecto**:

- el campo escribe la operación tal cual (`finalize.js:337–343`,
  `op[campos[id]] = input.value`) y el botón del descuento también
  (`:371–373`);
- la pantalla guarda el borrador en el navegador (`app_v2.js:1082`,
  `guardarBorrador`) y al volver lo recupera (`adoptarBorrador`, `:1124`);
- después de recargar, el campo arranca vacío (`dashboard_v2.html:622`), y al
  entrar se repinta (`finalize.js:90`, `pintarValor(null)`);
- la guarda (`finalize.js:451` y `:454`) no copia el ajuste mal escrito al
  campo, mientras el aviso (`:475–476`) sigue diciendo «Ajustes a incluir: …»
  y el pedido manda ese texto.

Es decir: tras recuperar un borrador con un ajuste mal escrito, el campo se ve
vacío y el aviso nombra un error que no se ve dónde está. Es lectura de
código: **no lo vi en un navegador.** Por eso no va a la cola como limpieza
sin efecto: va como pieza aparte, y empieza por un caso de pantalla que lo
muestre en rojo. Si el caso no lo reproduce, se informa y las dos guardas
recién ahí pasan a la cola.

## Veredicto

Aceptada sobre `fe0f1b4`. Integro el informe `4b5ef688` (no la punta de la
rama, que ya trae trabajo de D218/D219).
