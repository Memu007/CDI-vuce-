# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## AVISOS-2 (D130 (a) y las tres bajas): **entregada** en `4db641b` (2026-11-08)

| SHA | qué |
|---|---|
| `217c7cd` | fix: sólo un código de 4 letras o números ASCII llega como destinación al TXT; las tres bajas; CHANGELOG |
| `e51d54f` | test: la forma de la destinación, la exportación, el texto enorme y el lector; arnés `avisos2.sh` |
| `c10462a` | test: el arnés espera los ids no ASCII como los escribe pytest |
| `cfd03a5` | fix: los blancos delante de la destinación se sacan antes del corte (regresión mía, ver abajo) |
| `bd6330d` | test: 70 blancos y 70 tabs delante de EC, y el generador directo con lo que no es código |
| `4db641b` | fix: el comentario de `es_exportacion` en dos líneas (el AVISO de chequeo-6) |
| este commit | docs: el informe |

**Producto +29/−16** (13 netas).

Qué hace:

1. **D130 (a).** `destinacion_del_txt` (`maria_generator.py`) es el único
   lugar que decide qué destinación va al ISTA: cuatro letras o números
   ASCII después de `strip()`, en mayúsculas; si no, `ValueError` con el
   ejemplo («como IC04» o «como EC01»). Lo usan el generador, los dos
   endpoints de importación y el de exportación (vía `_destinacion_o_400`,
   que lo vuelve 400). Antes, `IC041` salía como `IC04` y `ＩＣ０４` o
   `ıc04` llegaban al TXT.
2. **Baja 1, texto enorme.** `es_exportacion` corta a 64 caracteres después
   del `strip()` y antes de normalizar. 5 millones de caracteres: 0,022 s.
3. **Baja 2, seguro borrado de vuelta a FOB.** El 400 dice «el que calculó
   el sistema se borró al cambiar el incoterm», sin «en el precio». Vale
   para ir y volver.
4. **Baja 3.** `/generate_maria_export` da 400 con `IC04`, `TRAN` o
   cualquier destinación que no sea EC*, y escribe la normalizada
   (` ec01 ` → `EC01`).
5. El lector (`validar_documento_importacion`) usa el mismo `es_exportacion`
   para los tres lugares donde puede venir la destinación.

**Contradigo la propuesta con evidencia.** La regex `^[A-Z]{2}\d{2}$` que
estaba en D130 rechaza `ZFI1` y `TRAN`, que hoy están en el select de la
revisión. Por eso la regla es «cuatro letras o números ASCII», no «dos
letras y dos números». Si querés la más estricta, es una D aparte con su
lista de destinaciones.

**Lo admito: metí una regresión y la encontré antes de entregar.** En
`217c7cd` el corte a 64 iba antes del `strip()`. Con 64 blancos o más
delante de `EC01`, un TXT de **importación** salía con `ISTA=EC01`, en el
endpoint, el generador y el lector. La base no lo dejaba pasar. La
encontraron `/code-review high` y el adversario Sonnet alto, los dos. La
prueba del texto enorme que yo había escrito no la veía: usaba `\u200b`,
que `strip()` no saca, y esperaba `ValueError`, que da igual el chequeo de
forma. Arreglo en `cfd03a5`; las pruebas que la distinguen, en `bd6330d`
(70 blancos y 70 tabs, en los dos endpoints, el lector y exportación).
Rojo con `cfd03a5` revertido: «9 failed, 122 passed»; en el arnés es el
sabotaje «corta antes de sacar los blancos».

## Decisiones

La D134 ya la usaste vos en `PARA-DEV.md`; por eso la segunda mía es la D135.

**D133. El lector deja pasar una destinación que no es código.**
`pdf_extractor.py:2576` guarda `documento["destinacion"]` sólo con
`strip()`/`upper()`. Si el modelo devuelve `IC-04`, `IC04 (consumo)` o
`\u200bIC04`, la operación la lleva, el select de la revisión queda en
blanco (no es una opción) y cada generación da 400 «Destinación: va un
código de 4 letras o números». La persona no ve qué está mal hasta que
abre el select. Antes se cortaba a 4 y generaba.

- (a) El lector la pasa por la misma regla y, si no es código, la deja
  vacía (la revisión pone IC04, como hoy con el vacío). Recomiendo esta:
  una línea, y el 400 no aparece.
- (b) La revisión muestra el valor que vino aunque no esté en la lista.
- (c) Queda así: el 400 dice qué falta.

Va con un caso que ahora el lector admite y la base rechazaba:
`"\u200b"*65 + "EC01"`. El endpoint y el generador lo rechazan con 400, así
que **nunca sale un TXT**; con (a) el lector lo deja vacío.

**D135. Un default de perfil puede trabar todas las importaciones.**
`default_tipo_destinacion` se guarda con `_sanitize_op_default`
(`main.py:2425`): letras y números hasta 10. `IC041`, `IC0` o `EC01`
guardados por la API se ponen en cada operación sin destinación, y cada
generación da 400 hasta que la persona la cambie a mano. Antes `IC041`
se cortaba a `IC04`.

- (a) Al guardar el perfil, la misma regla: 400 si no es un código de
  importación. Recomiendo esta.
- (b) Al aplicar el default en la revisión, ignorarlo si no es código.
- (c) Queda así.

**D136. No integré tu rama: trae la de la técnica y choca en producto.**
`origin/claude/practical-shannon-szpwkn` ahora tiene `f95ca5d` (el merge de
`claude/dev-tecnica`): 177 commits que no están en `main`. Mergearla en la
mía da conflicto en `main.py` (7 bloques), `finalize.js` (4),
`clientes.js`, `file_security.py` y `CHANGELOG.md`. No son de forma: las dos
ramas cambiaron distinto el webhook de MP sin secreto (en desarrollo, una lo
deja pasar y otra lo rechaza), qué pasa con las operaciones al borrar un
cliente (se borran sus presupuestos o la operación queda «Sin cliente»), el
registro (de un lado el tope por IP y la regex del username, del otro
`_exigir_username_libre`) y el guardado al historial
en `finalize.js`. Elegir un lado borra trabajo aceptado de una de las dos.
Los tres commits tuyos que trae (`f4f1d8f`, `40bf363`, `740ba3a`) tocan sólo
`docs/pm/`, y los leí: mi cola queda AVISOS-2 → RESET-3 → OBSERVABILIDAD-1
→ ORG-1+D40 → D102.

- (a) Integrás vos las dos ramas (en `main` o en la tuya, con su suite) y
  yo traigo eso. Recomiendo esta: la integración entre Devs es tuya, y
  RESET-3 toca `main.py`, así que conviene antes de que crezca la
  diferencia.
- (b) La resuelvo yo como pieza aparte, con suite y los arneses de las dos
  ramas, y decidís cada bloque de fondo.
- (c) Sigo sin traerla hasta que aceptes AVISOS-2.

Mientras no decidas, sigo con RESET-3 sobre mi rama y no traigo la tuya.

## Comandos

```bash
git checkout 4db641b
# negativos de AVISOS-2: 12 ROJO, «sabotajes sin rojo: 0»
PY=python scripts/testing/sabotajes/avisos2.sh 4db641b
# negativos de AVISOS-1, que comparten es_exportacion: 22 ROJO, «sabotajes sin rojo: 0»
PY=python scripts/testing/sabotajes/avisos1.sh 4db641b
# 13 netas, avisos 0
python docs/pm/herramientas/chequeo-6.py 8504691 4db641b
```

## Puertas

Todo sobre `4db641b`, desde un worktree limpio.

| puerta | salida exacta |
|---|---|
| suite completa (`pytest -q --no-cov --timeout=120`) | `5406 passed, 335 skipped, 3 xfailed, 97 warnings in 1086.06s (0:18:06)`, `pytest=0` |
| `compileall -q proyecto_maria` | `compileall=0` |
| `avisos2.sh 4db641b` | `BASE \| 131 passed`; 12 `ROJO`; `sabotajes sin rojo: 0` |
| `avisos1.sh 4db641b` | `BASE \| 151 passed`; 22 `ROJO`; `sabotajes sin rojo: 0` |
| `chequeo-6.py 8504691 4db641b` | `avisos: 0` (abajo, entera) |
| grep de historia de §6 | vacío |

**No corrido:** `smoke_friccion.sh`: necesita la app levantada y no la
levanté; lo que cambió (el 400 de generar, avisos y exportación) lo cubren
los casos de la suite contra la app en proceso. `ataque_aislamiento.sh`: la
pieza no toca datos, sesión ni permisos.

## Hallazgos de la autorrevisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| `/code-review high` sobre `8504691..c10462a` | el de la sesión, alto | corte a 64 antes del `strip()`: `ISTA=EC01` en importación (generador, endpoint) | arreglado en `cfd03a5`, rojo antes |
| ídem | ídem | lo mismo en el lector | ídem |
| ídem | ídem | la prueba del texto enorme no distingue el defecto | `bd6330d`: 70 blancos y 70 tabs |
| ídem | ídem | el sabotaje «el generador corta» sólo daba rojo porque también borraba el rechazo de exportación | `bd6330d`: `test_el_generador_tampoco_escribe_lo_que_no_es_un_codigo`; el sabotaje espera `[IC041]` |
| ídem | ídem | el lector guarda la destinación cruda (`pdf_extractor.py:2576`) | D133 |
| ídem | ídem | el default del perfil sin la regla (`main.py:2425`) | D135 |
| ídem | ídem | el chequeo corre dos veces en importación (endpoint y generador), §6 | no lo toqué: ya estaba así en la base (`_rechazar_exportacion_en_importacion` y el generador) y el endpoint tiene que rechazar antes de `_estudio_elegido`. Riesgo, abajo |
| `adversario-sonnet-alto` | Sonnet, alto | la misma regresión de los blancos | ídem que la primera |
| ídem | ídem | 300 000 combinaciones (prefijos, anchos, mayúsculas, largos, los tres endpoints, el lector): ninguna otra falla y ningún 500 | — |

`/security-review` **no se corrió**: la pieza valida un texto antes de
escribir el TXT; no toca dinero, sesión, permisos ni lo que se guarda.

## Riesgos

- D133, D135 y D136, arriba.
- Con CIF y el seguro borrado, el 400 ya no dice «en el precio»: dice «al
  cambiar el incoterm», que es cierto en los dos sentidos.
- En exportación, una destinación vacía da 400 («como EC01»). Antes llegaba
  vacía al generador de exportación.
- `generate_maria_export_txt` no tiene chequeo propio: su único llamador es
  el endpoint, que ya lo hace.
- El doble chequeo de importación (endpoint y generador) queda como en la
  base. Si lo querés una vez, propongo la línea para la cola de limpieza:
  «`/generate_maria` y `/avisos` asignan `request.tipo_destinacion` con
  `_destinacion_o_400` y el generador confía en lo que recibe».

## chequeo-6

```
chequeo-6 8504691..HEAD: avisos para mirar, no un veredicto
producto +29/−16
arnés +268/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/maria_generator.py: 2331 → 2341
  proyecto_maria/main.py: 12075 → 12078
  proyecto_maria/pdf_extractor.py: 2893 → 2893
avisos: 0
```

## Archivos de producto

`proyecto_maria/core/maria_generator.py`, `proyecto_maria/main.py`,
`proyecto_maria/pdf_extractor.py`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (send_message next, «Dev MARIA: …»), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. AVISOS-2 entregada en 4db641b (informe en este archivo); abiertas D131 (de EMAIL-1, va a Emi), D133, D135 y D136 (no traje tu rama: trae la técnica y choca en producto); la próxima D libre es la D137. Sigue RESET-3 (D132 a: tope por cuenta al pedir el reset, rojo con IPs distintas, sabotaje propio), después OBSERVABILIDAD-1, ORG-1+D40 y D102. Nunca main, nada se publica sin el «dale» de Emi para el SHA, sin secretos, sólo datos inventados.
