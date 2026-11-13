# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CORREDOR-PANTALLAS: un comando corre todas las pantallas sobre un SHA

| | SHA |
|---|---|
| Base | `67c8ff0d` |
| Arnés | `868c0355` (corredor + cabeceras), `bfde5a5a` (cabecera CSRF de csrf2, csrf3 y orden1), `907e1edb63028953e3dfc0756d9ad3433720f89b` (sin colores en la última línea) |
| Informe | el commit `docs:` que trae este archivo |

**Resultado:** `scripts/testing/correr_pantallas.sh [SHA] [carpeta]` corre las 30 `pantalla_*.js` sobre el SHA, cada una con su uvicorn y su sqlite nuevos, esperando `/health` (sin esperas fijas). Sobre 907e1ed: **26 verdes, 4 rojas** (`maria3 maria4 maria5 subitems1`, las de MARIA). Producto +0/−0.

Una puerta no se cumple al pie de la letra: con el sabotaje, el resumen contó **dos** rojas más, no una. Una es la del sabotaje (`borrador1`). La otra es `maria7`, que es intermitente en el corredor (ver «Intermitentes»). Por nombre, el sabotaje hace exactamente lo pedido.

## Decisiones

**D210. `maria7` y `maria1c` son intermitentes: ¿quién las mira?**
- (a) **La Dev MARIA** (recomendada): son pantallas suyas y la causa probable de `maria7` está en el guion (abajo); yo no las toco.
- (b) Yo, en una pieza aparte, cuando MARIA termine con maria3/4/5 y subitems1.
- Mientras tanto, el resumen del corredor puede contar una o dos rojas de más por ellas: se comparan por nombre.

Supuestos reversibles: el corredor también recibe `CDI_DB`, `PY` y `CHROMIUM` en cada pantalla (algunas los usan), y saca los escapes de color de la última línea (commit aparte, 907e1ed).

## Cabecera

Debajo de `// uso:`, la pantalla dice lo que necesita; el corredor lee sólo el bloque `//` de arriba:

```
// corredor: servidor CSRF_ENFORCE=true          csrf1, csrf2, csrf3, orden1
// corredor: argumentos tests/test_facturas.xlsx  excel1, maria1b
// corredor: argumentos tests/test_factura.pdf    maria1c
// corredor: sin servidor                         panel_dev
```

Cada `VAR=valor` de `servidor` se valida; si no tiene esa forma, la pantalla da `FALLA: cabecera` con rc=2. `maria3`, `maria4`, `maria5` y `subitems1` **no necesitan cabecera**: sólo piden `BASE_URL`. No las toqué.

**Hallazgo propio, ya arreglado:** en 868c0355 sólo `csrf1` tenía la cabecera CSRF, y `csrf2` y `csrf3` dieron verde **sin el control que prueban**. Sus guiones (`sabotajes/_csrf_comun.sh`, `orden1.sh`, `orden1b.sh`) levantan con `CSRF_ENFORCE=true`; bfde5a5 se lo agrega a `csrf2`, `csrf3` y `orden1`.

**Diferencia conocida:** `sabotajes/sesion1.sh` levanta con `ENVIRONMENT=testing` y el corredor con `development`. `main.py:109` cambia `IS_TESTING` con eso. `sesion1` da verde igual. No lo agregué a la cabecera porque no hacía falta para correr; si lo querés idéntico al guion, es una línea.

## Pantallas que hoy no corre ningún guion (medido por llamada)

Son 11: `catalogo_ncm1`, `despacho1b`, `excel1`, `maria1b`, `maria1c`, `maria3`, `maria4`, `maria5`, `maria7`, `subitems1`, `sufijos1`.

```bash
for f in scripts/testing/pantalla_*.js; do n=$(basename $f .js); grep -rhE "$n\.js" scripts --include='*.sh' --include='*.py' --exclude=correr_pantallas.sh | grep -qvE '^[[:space:]]*#' || echo ${n#pantalla_}; done
#   → catalogo_ncm1 despacho1b excel1 maria1b maria1c maria3 maria4 maria5 maria7 subitems1 sufijos1
```

Cuenta una línea de un `.sh` o `.py` que no sea comentario. `maria1c`, `maria4`, `maria7`, `subitems1` y `sufijos1` aparecen sólo en comentarios de su `sabotaje_*.sh`; `maria5` no aparece en ninguno.

## Puertas

| Puerta | Resultado |
|---|---|
| Lista medida de pantallas sin guion | 11, arriba |
| Línea del corredor = pantalla sola, sobre el mismo SHA | Coinciden la roja `maria3` y las verdes `csrf2` (con `CSRF_ENFORCE=true`) y `borrador1`. Las solas corrieron sobre bfde5a5; entre bfde5a5 y 907e1ed sólo cambia una línea de `correr_pantallas.sh` (`git diff --stat`: 1 file, 1+/1−), ninguna pantalla |
| Sabotaje: verde → roja, una roja más | `borrador1` pasa a ROJA. El resumen va de 4 a 6 rojas, porque `maria7` también dio roja (intermitente). **No se cumple al pie de la letra** |
| chequeo-6 | producto +0/−0, avisos: 0 |

### Corrida sobre 907e1ed (salida exacta, sin la ruta de los logs)

```
pantallas sobre 907e1edb63028953e3dfc0756d9ad3433720f89b;
verde borrador1      rc=0   borrador1.log | ok: el arranque no saca de Clientes y recupera si no fue a ninguna pantalla
verde catalogo_ncm1  rc=0   catalogo_ncm1.log | OK: pantalla CATALOGO-NCM-1
verde cliente1       rc=0   cliente1.log | PANTALLA CLIENTE-1 OK (con CLIENTE-1b y 1c)
verde cobro_corte1   rc=0   cobro_corte1.log | pantalla COBRO-CORTE-1: OK
verde cobro_mp1      rc=0   cobro_mp1.log | pantalla COBRO-MP-1: OK
verde cobro_mp1_v2   rc=0   cobro_mp1_v2.log | OK | generación rechazada: generar /generate_maria
verde csrf1          rc=0   csrf1.log | OK: CSRF-1 en el navegador
verde csrf2          rc=0   csrf2.log | OK: CSRF-2 en el navegador
verde csrf3          rc=0   csrf3.log | OK: CSRF-3 en el navegador
verde despacho1a     rc=0   despacho1a.log | OK 390 px: «catalogo_cliente_inventado_d1a_390.xlsx» trae ["CABALLO INVENTADO","=1+1 NOTEBOOK INVENTADA
verde despacho1b     rc=0   despacho1b.log | OK 390 px: 3 renglones, faltante marcado [["cxDesp2_kilo_neto",""]], nada guardado antes ni con error, gu
verde destino1       rc=0   destino1.log | OK: pantalla DESTINO-1
verde estudio1       rc=0   estudio1.log | PANTALLA ESTUDIO-1 OK
verde estudio1b      rc=0   estudio1b.log | PANTALLA ESTUDIO-1b OK
verde excel1         rc=0   excel1.log | OK: pantalla EXCEL-1
verde maria1b        rc=0   maria1b.log | OK: pantalla MARIA-1b
verde maria1c        rc=0   maria1c.log | OK: pantalla MARIA-1c
ROJA  maria3         rc=1   maria3.log | Node.js v22.22.0
ROJA  maria4         rc=1   maria4.log |        - waiting 500ms
ROJA  maria5         rc=1   maria5.log | FALLA: no se generó el TXT: {"detail":"Falta el CUIT del despachante (CDDTAGR): elegí el estudio en la oper
verde maria7         rc=0   maria7.log | PANTALLA MARIA-7 OK
verde maria9         rc=0   maria9.log | PANTALLA MARIA-9 OK
verde orden1         rc=0   orden1.log | OK: ORDEN-1 en el navegador
verde org1b          rc=0   org1b.log | OK ORG-1b
verde panel_dev      rc=0   panel_dev.log | fallas: 0
verde separadores1   rc=0   separadores1.log | PANTALLA SEPARADORES-1 OK
verde sesion1        rc=0   sesion1.log | OK: el perfil pide la contraseña sólo al cambiar el email y no saca a nadie al login
ROJA  subitems1      rc=1   subitems1.log | FALLA: no se generó el TXT: {"detail":"Falta el CUIT del despachante (CDDTAGR): elegí el estudio en la o
verde sufijos1       rc=0   sufijos1.log | PANTALLA SUFIJOS-1 OK
verde validacion1    rc=0   validacion1.log | pantalla VALIDACION-1: OK
resumen: 26 verdes, 4 rojas: maria3 maria4 maria5 subitems1
rc=1
```

La última línea de `maria3` es `Node.js v22.22.0` porque tira un throw sin capturar (`page.waitForResponse: Timeout 15000ms exceeded`); el detalle está en su log. El corredor muestra la última línea, como pide la tarea.

### Solas sobre bfde5a5 (un uvicorn a mano con el mismo entorno, `/health`, la pantalla)

```
sola maria3 rc=1 | Node.js v22.22.0
sola csrf2 rc=0 | OK: CSRF-2 en el navegador
sola borrador1 rc=0 | ok: el arranque no saca de Clientes y recupera si no fue a ninguna pantalla
```

### Sabotaje

Era un commit local, f650d24, en un worktree descartable que ya retiré. Cambia una línea de `pantalla_borrador1.js`: `if (pantalla !== caso.pantalla) mala(` pasa a `===`. La corrida completa del corredor sobre f650d24 dio (líneas relevantes):

```
ROJA  borrador1      rc=1   borrador1.log | FALLA: el tour la lleva a la carga: el arranque tenía que dejarla en review y la llevó a review
ROJA  maria7         rc=1   maria7.log | FALLA: la pregunta por la fecha no aparece al subir
resumen: 24 verdes, 6 rojas: borrador1 maria3 maria4 maria5 maria7 subitems1
rc=1
```

Sin el sabotaje, sobre 907e1ed: `borrador1` verde, `maria7` verde, «26 verdes, 4 rojas».

## Intermitentes (no son de esta pieza; no tapo nada repitiendo)

| Pantalla | En el corredor | Sola |
|---|---|---|
| `maria7` | roja en bfde5a5 y f650d24, verde en 868c0355 y 907e1ed (2 de 4) | 5 de 5 verdes |
| `maria1c` | roja en bfde5a5, verde en 868c0355, 907e1ed y f650d24 (1 de 4) | 5 de 6 verdes |

- `maria7`: «la pregunta por la fecha no aparece al subir». Causa probable, **no verificada**: el guion espera `#uploadFileInput` con `state: 'attached'`. Ese input está en el HTML estático (`dashboard_v2.html:116`), así que la espera se cumple antes de que `upload.js` `init()` enganche el listener. Si `setInputFiles` llega antes, la subida no ocurre.
- `maria1c`: `locator.click: Timeout 30000ms` sobre `#semaforoFAB`, que existe con `hidden`. No lo diagnostiqué más.

## Para copiar

```bash
PY=<python del proyecto> scripts/testing/correr_pantallas.sh 907e1edb63028953e3dfc0756d9ad3433720f89b
#   → 30 líneas y «resumen: 26 verdes, 4 rojas: maria3 maria4 maria5 subitems1» (±maria7/maria1c), rc=1; tarda unos 15 min (medido: 01:31→01:45)
python docs/pm/herramientas/chequeo-6.py 67c8ff0d 907e1edb63028953e3dfc0756d9ad3433720f89b
#   → producto +0/−0, avisos: 0
```

chequeo-6, salida entera:

```
chequeo-6 67c8ff0d..907e1edb63028953e3dfc0756d9ad3433720f89b: avisos para mirar, no un veredicto
producto +0/−0
arnés +92/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## No corrido

- La suite pytest: no hay cambios de producto.
- Subagentes adversariales y `/code-review`: no, porque la tarea dice «sin adversarios».
- La pantalla sola sobre 907e1ed: las solas son de bfde5a5, con las pantallas idénticas.
- Una segunda corrida del sabotaje para tener «una roja más» limpia: no la hice para no buscar el verde repitiendo. Si la querés, es el mismo comando sobre un SHA saboteado.

## Riesgos

- Con `TOPE` en 600 s por pantalla, la corrida completa tardó unos 15 min (medido: 01:31→01:45, 30 pantallas).
- El corredor usa `git worktree add` en el repo desde donde se lo llama, y lo retira al salir (también si se corta con Ctrl-C, por el `trap`).

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué CORREDOR-PANTALLAS (907e1ed + informe); D210 (intermitentes maria7/maria1c, recomiendo Dev MARIA); tests/test_conexiones1.py sin seguimiento (su copia está en el parche); espero veredicto.
