# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Vencido `sabotaje_valor1b.sh`: entregado en `70eb5dc`. Vuelve a encontrar sus dos anclas; 22 `ROJO`, `rc=0`; anclas perdidas en 2 y 0, «otra cantidad» en 0

| qué | SHA |
|---|---|
| base (informe de maria5) | `9153d23` |
| pruebas: dos anclas reescritas, el `23` del último `echo` pasa a `22` y mi línea fuera de `sabotajes-conocidos.txt`. **Lo que se entrega** | `70eb5dc` |
| tu rama, traída hasta `607272c` | `6aad893` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +10/−6`: `scripts/testing/sabotaje_valor1b.sh` y una
línea menos en `docs/pm/herramientas/sabotajes-conocidos.txt`.

El SHA que entrego pasó por un adversario (abajo, «Revisión adversarial»).

## Nada para decidir

Antes de reescribir comprobé que las dos protecciones siguen existiendo
(D195 (a)): no hay sabotaje para retirar ni D nueva. Un supuesto reversible:

1. **Corregí el número del último `echo`: decía 23 y el guion tiene 22
   casos.** No lo rompió este arreglo: `efa2e08` (2026-10-25) sumó cuatro
   casos a los 18 que había y escribió 23 (`grep -c '^caso '` da 18 en
   `9546fa7` y 22 en `efa2e08` y en `9153d23`). Tu acta
   `REPRODUCCION-VALOR-1b-MARIA-9-2026-10-25.md` copia ese «23»: ese día
   corrieron 22. Lo cambié porque el guion afirmaba algo falso en la línea que
   se lee para aceptarlo. Sigue escrito a mano (línea para la cola, abajo). Si
   preferís que no lo toque, es volver ese renglón a `23`.

## Lo que cambió

```diff
 # 8. después de calcular, el botón sigue con las cuentas de antes
-reemplazar $JS '        cuentasViejas();
-        refrescarAvisos();
-        if (CDI.semaforo' '        refrescarAvisos();
-        if (CDI.semaforo'
+reemplazar $JS '            op.campos_completados = Array.from(completados);
+        }
+        cuentasViejas();
+' '            op.campos_completados = Array.from(completados);
+        }
+'
…
 # 10. el semáforo no se entera del seguro calculado
 reemplazar $JS '        if (CDI.semaforo && CDI.semaforo.refresh) CDI.semaforo.refresh();
-' ''
+    }
+' '    }
+'
…
-echo "OK: los 23 sabotajes dan rojo por la razón esperada"
+echo "OK: los 22 sabotajes dan rojo por la razón esperada"
```

Por qué se habían perdido: los dos casos sacan un renglón del final de la
función que pone el seguro sugerido, en
`proyecto_maria/static/v2/screens/finalize.js`. `4f75f3d` (SEGURO-1) sumó la
función que borra el seguro, que termina con los mismos tres renglones
(`cuentasViejas();`, `refrescarAvisos();` y el del semáforo). Las dos anclas
pasaron a estar dos veces y el guion cortaba en el caso 8.

Cada ancla lleva ahora el renglón que la ata a la función del sugerido:

- **Caso 8:** el cierre del bloque de arriba
  (`op.campos_completados = Array.from(completados);` y su `}`). La función
  que borra no tiene ese renglón.
- **Caso 10:** el cierre de la función (`    }`). En la que borra, después
  del renglón del semáforo viene `return true;`.

Lo que cada caso saca es lo mismo que sacaba: `cuentasViejas();` el 8 y el
renglón del semáforo el 10. Los nombres y los textos esperados de los 22
casos no cambiaron.

## Resultado

| qué | antes, guion de `9153d23` | ahora, `70eb5dc` |
|---|---|---|
| el guion | 8 `ROJO` y corta: `PATRON NO ENCONTRADO (2 veces) en proyecto_maria/static/v2/screens/finalize.js: '        cuentasViejas();\n        refrescarAvisos();\n        if (CDI.semaforo'`; `rc=1` | 22 `ROJO`, 0 `FALLA`; `OK: los 22 sabotajes dan rojo por la razón esperada`; `rc=0` |
| caso 8 | cortaba ahí | `ROJO   calculado_cuentas_viejas: 1 failed, 75 passed` |
| caso 10 | no llegaba a correr | `ROJO   semaforo_sin_refrescar: 2 failed, 74 passed` |
| anclas perdidas | 2 y 0; «otra cantidad» 2 (`sabotaje_valor1b.sh:102` y `:114`, «está 2, se esperaba 1») | `perdida, una línea 2 guiones: 2`; `perdida, varias líneas 0 guiones: 0`; `otra cantidad 0 guiones: 0` |
| mi línea en `sabotajes-conocidos.txt` | estaba | no está; quedan 3 `vencido` |

Que la protección sigue, medido a mano sobre el producto de `9153d23` (el
mismo de `70eb5dc`) antes de tocar el guion, en un worktree descartable, con
`tests/test_valor1.py`:

| mutación | resultado | pruebas en rojo |
|---|---|---|
| ninguna | `76 passed` | |
| caso 8: sale `cuentasViejas();` de la función del sugerido | `1 failed, 75 passed` | `test_el_boton_del_seguro_pone_el_sugerido_y_pide_las_cuentas_de_nuevo`: `assert False is True` |
| caso 10: sale el renglón del semáforo de la función del sugerido | `2 failed, 74 passed` | la misma (`assert (1 == 1 and 0 == 1)`) y `test_el_seguro_calculado_deja_de_avisarse_como_no_leido` (`assert 0 == 1`) |

## Revisión adversarial

Pieza chica de arnés: un adversario Sonnet, esfuerzo medio, sobre `70eb5dc`,
en un worktree propio que retiró al terminar.

No corrió el guion entero. **Defectos: ninguno.**

| qué probó | resultado | lo reproduje |
|---|---|---|
| las dos anclas en `finalize.js` | cada una, una sola vez y en código: la del 8 en la línea 419 y la del 10 en la 423, las dos dentro de `calcularSeguro`. `borrarSeguroCalculado` sigue con `return true;` y no coincide | sí, contando en el archivo de `70eb5dc`: 1 y 1, líneas 419 y 423, función `calcularSeguro` |
| el JS con cada mutación | `node --check` pasa en las dos | sí; y el `diff` contra el original es un solo renglón menos: el 421 (`cuentasViejas();`) y el 423 (el del semáforo) |
| caso 8 puesto a mano | `1 failed, 75 passed`, por `test_el_boton_del_seguro_pone_el_sugerido_y_pide_las_cuentas_de_nuevo`; ni sintaxis, ni importación, ni timeout | sí, antes que él (tabla de arriba) y en el guion |
| caso 10 puesto a mano | `2 failed, 74 passed`: la esperada y la del botón | sí, ídem |
| ¿saca lo mismo que el guion viejo? | sí: cambió sólo el contexto que ata cada ancla a su lugar | sí, es el `diff` de un renglón |
| el mensaje del commit | cierto: `4f75f3d` suma `borrarSeguroCalculado` con los mismos tres renglones y `return true;`; `efa2e08^` tiene 18 casos, `efa2e08` 22 y su `echo` decía 23 | sí, con `git show` y `grep -c '^caso '` en cada versión |
| la cuenta | 22 llamadas a `caso`, ningún nombre repetido, ningún `exit` entre casos | sí: 22 en el archivo y 22 `ROJO` en la salida |
| quién más espera «los 23 sabotajes» | nadie, fuera de las actas y `docs/archive/` | sí, con `grep -rn` |
| `anclas_perdidas.py 70eb5dc` | ninguna fila de `sabotaje_valor1b.sh`, ni perdida ni «otra cantidad» | sí |

Tres observaciones suyas, las tres previas: que el caso 10 pone roja también
la prueba del 8 (riesgo 2), que el `22` sigue escrito a mano (línea para la
cola) y que mi informe anterior nombraba este guion como vencido (lo
reemplaza este).

No corrí `/code-review`: el SHA que se entrega pasó por el adversario, que es
una de las dos que pediste.

## Comandos

```bash
VENV=/ruta/a/tu/venv
git diff 9153d23 70eb5dc --stat -- scripts docs/pm/herramientas | tail -1    # 2 files changed, 10 insertions(+), 7 deletions(-)
bash scripts/testing/sabotaje_valor1b.sh 70eb5dc $VENV > /tmp/v1b.log; echo $?    # 0   (unos 8 min)
grep -c '^ROJO ' /tmp/v1b.log                       # 22
grep -c 'FALLA' /tmp/v1b.log                        # 0
grep -c '^caso ' scripts/testing/sabotaje_valor1b.sh    # 22
grep -E 'calculado_cuentas_viejas|semaforo_sin_refrescar' /tmp/v1b.log
#   ROJO   calculado_cuentas_viejas: … 1 failed, 75 passed …
#   ROJO   semaforo_sin_refrescar: … 2 failed, 74 passed …
$VENV/bin/python scripts/testing/anclas_perdidas.py 70eb5dc | sed -n 2,4p
#     perdida, una línea          2   guiones: 2
#     perdida, varias líneas      0   guiones: 0
#     otra cantidad               0   guiones: 0
grep -c sabotaje_valor1b docs/pm/herramientas/sabotajes-conocidos.txt    # 0
grep -c '^vencido' docs/pm/herramientas/sabotajes-conocidos.txt          # 3

# el rojo sin el arreglo: el guion de la base
git show 9153d23:scripts/testing/sabotaje_valor1b.sh > /tmp/v1b_viejo.sh
bash /tmp/v1b_viejo.sh 9153d23 $VENV | tail -1; echo ${PIPESTATUS[0]}
#   PATRON NO ENCONTRADO (2 veces) en proyecto_maria/static/v2/screens/finalize.js: '        cuentasViejas();\n        refrescarAvisos();\n        if (CDI.semaforo'
#   1
```

Corrí cada uno una vez, con la salida a un archivo; esas son sus líneas.

## Puertas

Sobre `70eb5dc`, árbol limpio.

| puerta | salida |
|---|---|
| `sabotaje_valor1b.sh 70eb5dc` | 22 `ROJO`, 0 `FALLA`; `OK: los 22 sabotajes dan rojo por la razón esperada`; `rc=0` |
| `tests/test_valor1.py` sobre `9153d23` (mismo producto y misma prueba) | `76 passed` |
| `tests/test_anclas_perdidas.py` | `27 passed` |
| `anclas_perdidas.py 70eb5dc` | `103 guiones, 2493 anclas medidas y 11 llamadas sin medir`; 2, 0 y 0; ninguna fila de `sabotaje_valor1b.sh`; `rc=0` |
| `chequeo-6.py 9153d23 70eb5dc` | abajo, `avisos: 0` |

**No corrido:** la suite entera (cambió un guion, ningún producto ni prueba),
`compileall`, las pantallas, `e2e_maria.sh`, `smoke_friccion.sh`,
`ataque_aislamiento.sh`, Postgres, los demás guiones de sabotaje,
`/code-review` y `/security-review` (no toca plata, sesión, permisos ni
datos).

## `chequeo-6`

```
chequeo-6 9153d23..70eb5dc: avisos para mirar, no un veredicto
producto +0/−0
arnés +10/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. **El guion no corre la prueba sin sabotaje.** No tiene la línea `VERDE`
   que sí tiene `sabotaje_maria5.sh`: si `tests/test_valor1.py` estuviera en
   rojo por otra causa, un caso podría decir `ROJO` sin que su mutación
   muerda. `caso` mira el nombre en `FAILED`, no la causa. Lo cubrí a mano
   (`76 passed` en la base). Es previo; severidad baja.
2. **Los casos 9 y 10 esperan la misma prueba**
   (`test_el_seguro_calculado_deja_de_avisarse_como_no_leido`), y el 10 pone
   roja también la del 8. Si el 10 dejara de morder y otro cambio pusiera
   roja esa prueba, el guion diría `ROJO`. Es previo y el commit no lo
   empeora; severidad baja.
3. **El ancla del 10 depende de que la función del sugerido termine con el
   renglón del semáforo.** Si alguien suma un renglón después, el guion corta
   con `PATRON NO ENCONTRADO (0 veces)`: falla a la vista, no en silencio.

## Líneas para `COLA-LIMPIEZA.md`

- `scripts/testing/sabotaje_valor1b.sh`: el `22` del último `echo` está
  escrito a mano (estuvo en 23 con 22 casos desde `efa2e08`); el venv por
  defecto es `/tmp/cdi-dev2/venv`, que ya no existe; y no corre la prueba sin
  sabotaje antes de los casos.

## Archivos de producto que toqué

Ninguno.

## Sigo con

El vencido `scripts/testing/sabotaje_doc1.py` (dos anclas que no están:
`main.py` y `maria_generator.py`, `startswith("EC")`). Primero miro si cada
protección sigue existiendo.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `607272c`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`, D248 (c) sobre `3fcc9c4`, el vencido `sabotaje_maria1d.sh` sobre `6e4e658`, el vencido `sabotaje_maria5.sh` sobre `c0505cc`. Entregada sin veredicto: **el vencido `sabotaje_valor1b.sh` sobre `70eb5dc`** (base `9153d23`; sólo `scripts/testing/sabotaje_valor1b.sh` y mi línea fuera de `sabotajes-conocidos.txt`, arnés +10/−6; 22 `ROJO`, 0 `FALLA`; anclas 2, 0 y «otra cantidad» 0; el `echo` final decía 23 con 22 casos desde `efa2e08` y lo pasé a 22 como supuesto reversible; un adversario Sonnet medio revisó `70eb5dc`, sin defectos). Si vuelve con devolución, va primero. **Pieza activa: el vencido `scripts/testing/sabotaje_doc1.py`** (dos anclas `startswith("EC")` que ya no están en `main.py` ni en `maria_generator.py`; el control parece haberse mudado a `es_exportacion`, `maria_generator.py:1120`: falta comprobarlo); después, uno por pieza: maria7 (97), guardar2 (74); al arreglar cada uno saco mi línea de `docs/pm/herramientas/sabotajes-conocidos.txt`. Después **D249 (a)**, decidida por la PM: sólo `tests/test_sufijos2.py` y `scripts/testing/sabotajes/sufijos2.sh`, criterio entero en `docs/pm/PARA-DEV-2.md`, sección D247 (la familia de fragmentos «…» de `limpiar_sufijo`, un sabotaje por cambio, `sufijos2.sh` entero en `ROJO` con la cuenta exacta, `sabotaje_sufijos1.sh` en 46, anclas que no empeoran: el criterio dice 5 y 1 y hoy son 2 y 0). D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D250. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; que «nadie cubría» algo se mide antes de escribirlo; `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; después de un commit nuevo o de corregir uno, las puertas corren otra vez sobre ese SHA; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar; la cuenta escrita a mano en el último `echo` de un guion se compara con sus líneas `ROJO`; regla de la PM: en un vencido de sólo arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice, cualquier otro cambio sí. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
