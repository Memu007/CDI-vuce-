# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D243 (b): entregada en `0dff850`. Las cuatro anclas vuelven a encontrar su línea; los tres guiones corridos enteros dan todos sus sabotajes en rojo y `anclas_perdidas.py` vuelve a 6. Sólo arnés. Nada para decidir

| qué | SHA |
|---|---|
| base (informe de SABOTAJE-SUBITEMS1) | `2a0b8e8` |
| arnés: las cuatro anclas. **Lo que se entrega** | `0dff850` |
| unión con tu rama (hasta `036e294`, sólo `docs/pm`) | `ff3eea2` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +8/−8`: cuatro pares de líneas (ancla y sabotaje) en
`sabotajes/estudio1.sh`, `sabotajes/estudio1b.sh` y `sabotajes/excel2.sh`.
Fuera de esas ocho líneas no toqué nada de esos archivos.

Leí tu veredicto de SABOTAJE-SUBITEMS1 y el orden nuevo: sigo con
`sabotaje_sufijos1.sh` y después D245 (a).

## Decisiones

Ninguna. Próxima D: D246.

## Lo que cambió

Son las líneas de la tabla de mi informe de CUIT-GENERAR, sin cambios.

| guion | sabotaje | ancla nueva | lo que pone |
|---|---|---|---|
| `estudio1.sh:78` | el cuit_agr que manda la pantalla gana al estudio | `crudo = (estudio.cuit if estudio is not None else cuit_agr) or del_perfil` | `crudo = cuit_agr or (estudio.cuit if estudio is not None else "") or del_perfil` |
| `estudio1b.sh:71` | el uso del perfil cuenta sólo con cuit_agr vacío | `es_el_del_perfil = estudio is None and bool(cuit) and cuit == del_perfil` | `es_el_del_perfil = estudio is None and not cuit_agr and bool(cuit)` |
| `estudio1b.sh:75` | un cuit_agr ajeno cuenta como uso del perfil | la misma | `es_el_del_perfil = estudio is None and bool(cuit)` |
| `excel2.sh:168` | el CUIT del despachante vuelve a aceptar cualquier cosa | `    if crudo and not cuit_valido(cuit):` | `    if False:` |

## Resultado

Los tres guiones enteros sobre `0dff850`, cada uno en su worktree:

| guion | `ROJO` | `VERDE`, `ROTO` o `ROJO?` | última línea | `rc` |
|---|---|---|---|---|
| `sabotajes/estudio1.sh` | 37 | 0 | `sabotajes sin rojo: 0` | 0 |
| `sabotajes/estudio1b.sh` | 20 | 0 | `sabotajes sin rojo: 0` | 0 |
| `sabotajes/excel2.sh` | 42 | 0 | `sabotajes con falla: 0` | 0 |

Los cuatro que cambié, copiados de la salida:

```
ROJO  | el cuit_agr que manda la pantalla gana al estudio: dice «FAILED tests/test_estudio1.py::test_el_estudio_elegido_va_al_cddtagr_aunque_haya_perfil_y_cuit_agr»
ROJO  | el uso del perfil cuenta sólo con cuit_agr vacío (la pantalla siempre lo manda): dice «FAILED tests/test_estudio1b.py::test_el_cuit_del_perfil_en_cuit_agr_cuenta_como_uso_del_perfil»
ROJO  | un cuit_agr ajeno cuenta como uso del perfil: dice «FAILED tests/test_estudio1b.py::test_un_cuit_agr_propio_no_cuenta_como_uso_del_perfil»
ROJO  | el CUIT del despachante vuelve a aceptar cualquier cosa: dice «FAILED tests/test_excel2.py::test_el_cuit_del_despachante_va_solo_con_11_digitos» (4 s)
```

`anclas_perdidas.py`:

| | base `2a0b8e8` | `0dff850` |
|---|---|---|
| perdida, una línea | 10 (guiones: 8) | 6 (guiones: 5) |
| perdidas de una línea sin repetir | 9 | 6 |
| perdida, varias líneas | 3 | 3 |
| está | 2475 | 2479 |

Las 6 que quedan son de mis vencidos: `sabotaje_maria5.sh` (2),
`sabotaje_maria1d.sh`, `sabotaje_maria7.sh`, `sabotaje_maria8.sh` y
`sabotajes/guardar2.sh` (1 cada uno).

## Notas (ninguna pide decisión)

- **El rojo de `excel2.sh:168` es el mismo, el control no.** El viejo era
  `[0-9]{11}`; el de ahora es `cuit_valido`, que además mira el verificador.
  El nombre del sabotaje y el de su prueba siguen diciendo «11 dígitos» y el
  sabotaje sigue dando su rojo. El verificador tiene sabotaje propio en
  `cuit_generar.sh:99` y `estudio1.sh:109`.
- **Comentario viejo en `excel2.sh:171`** («El control de los sub-ítems de ese
  mismo bucle…»): el control del CUIT ya no está en ese bucle. Es de la
  Técnica y queda fuera de las cuatro anclas: no lo toqué.
- **`estudio is None` en `es_el_del_perfil` no tiene sabotaje** en estos tres
  guiones ni en `cuit_generar.sh`. Lo medí: sin esa condición,
  `test_estudio1.py`, `test_estudio1b.py` y `test_cuit_generar.py` dan
  `85 passed`. Es lo que ya escribiste en CUIT-GENERAR: los dos usos de la
  marca miran antes si hay estudio (dentro de `_cuit_del_despachante`,
  `main.py:4750` y `:4752`, y en el endpoint, `:5234` y `:5241`). No es un hueco.

## Revisión adversarial

| quién | modelo y esfuerzo | qué encontró |
|---|---|---|
| `adversario-sonnet-medio` | Sonnet, medio | Sin bloqueantes. Aplicó a mano los cuatro: son equivalentes a los viejos y dan rojo por el motivo que dice el nombre (`assert ['20111111112'] == ['30222222229']`; `assert '<uuid>' is None`; `assert None == '<uuid>'`; `assert 200 == 400` con `CDDTAGR=2O111111112` en el TXT). Trajo la primera y la tercera nota de arriba. |

## `/code-review high`

Sobre `2a0b8e8..0dff850`: `[]`, sin hallazgos. Los revisores aplicaron los
cuatro sabotajes por su cuenta, contaron que cada ancla aparece una vez en
`main.py` y buscaron en `scripts/` y `tests/` alguna otra línea que apunte a lo
que sacó CUIT-GENERAR: no hay. No corrieron las secciones de pantalla ni los
sabotajes que no cambié (eso lo corrí yo, arriba).

`/security-review`: no corrido. La pieza no toca producto.

## Comandos

```bash
VENV=/ruta/a/tu/venv
PY=$VENV/bin/python scripts/testing/sabotajes/estudio1.sh 0dff850 | tail -1    # sabotajes sin rojo: 0   (10 min)
PY=$VENV/bin/python scripts/testing/sabotajes/estudio1b.sh 0dff850 | tail -1   # sabotajes sin rojo: 0   (10 min)
PY=$VENV/bin/python scripts/testing/sabotajes/excel2.sh 0dff850 | tail -1      # sabotajes con falla: 0  (4,5 min)
$VENV/bin/python scripts/testing/anclas_perdidas.py 0dff850 | sed -n 2p        # perdida, una línea          6   guiones: 5
$VENV/bin/python docs/pm/herramientas/chequeo-6.py 2a0b8e8 0dff850             # producto +0/−0, arnés +8/−8, avisos: 0
git diff 2a0b8e8 0dff850 --stat | tail -1                                      # 3 files changed, 8 insertions(+), 8 deletions(-)
```

## Puertas

Sobre `0dff850`, árbol limpio.

| puerta | salida |
|---|---|
| `sabotajes/estudio1.sh 0dff850` | 37 `ROJO`, `sabotajes sin rojo: 0`, `rc=0` |
| `sabotajes/estudio1b.sh 0dff850` | 20 `ROJO`, `sabotajes sin rojo: 0`, `rc=0` |
| `sabotajes/excel2.sh 0dff850` | 42 `ROJO`, `sabotajes con falla: 0`, `rc=0` |
| `anclas_perdidas.py 0dff850` | `perdida, una línea          6   guiones: 5` |
| `pytest tests/test_anclas_perdidas.py tests/test_limpieza1.py` | `32 passed` |
| `chequeo-6.py 2a0b8e8 0dff850` | abajo, `avisos: 0` |

**No corrido:** la suite entera (no cambió ningún archivo que pytest junte ni
producto; corrí las dos pruebas que leen `sabotajes/`), `compileall`, las
pantallas fuera de las que corren esos dos guiones, `e2e_maria.sh`,
`smoke_friccion.sh`, `ataque_aislamiento.sh`, Postgres, los demás guiones de
sabotaje y `/security-review`. Sobre `ff3eea2` (la unión) no corrí nada: trae
sólo `docs/pm`.

## `chequeo-6`

```
chequeo-6 2a0b8e8..0dff850: avisos para mirar, no un veredicto
producto +0/−0
arnés +8/−8
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

- Los tres guiones son de la Técnica. Su rama no los tocó desde mi base (lo
  miré con `git log` sobre `claude/dev-tecnica` antes de cambiar). Si los toca
  ahora, la unión puede chocar en esas líneas.
- Con esto `29327d2` deja de tener sabotajes sin ancla por CUIT-GENERAR. Las 6
  anclas perdidas que quedan son anteriores y están en mis vencidos.

## Líneas para COLA-LIMPIEZA

- `sabotajes/excel2.sh:171`: el comentario habla de «ese mismo bucle», donde ya
  no está el control del CUIT del despachante (Técnica).

## Archivos de producto que toqué

Ninguno.

## Sigo con

`sabotaje_sufijos1.sh`, con el dato de `sufijo_otra1` que pediste. Después
D245 (a).

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `036e294`). CUIT-GENERAR aceptada sobre `29327d2`; SABOTAJE-SUBITEMS1 aceptada sobre `bf6778e`. D243 (b) entregada sobre `0dff850` (base `2a0b8e8`; sólo arnés, +8/−8 en `sabotajes/estudio1.sh`, `estudio1b.sh` y `excel2.sh`; los tres guiones enteros 37, 20 y 42 `ROJO`; `anclas_perdidas.py` 6), sin decisiones. Si vuelve con devolución, va primero. Orden de la PM: 1) **`sabotaje_sufijos1.sh`, pieza activa** (vencido de `sabotajes-conocidos.txt`: queda verde `codigo_vacio_cargado`, que espera una prueba que ya no existe), y lleva como dato de `sufijo_otra1` la siguiente operación con su propio sufijo guardado: entra sin el aviso de la anterior y con su sufijo en el campo (su rojo: `pintarSufijo` que esconde el aviso sólo cuando el campo entra vacío). 2) **D245 (a)**, sólo pruebas: sumar la afirmación de `success` del semáforo en `test_punta_a_punta1.py`, `test_generar_maria_txt.py` y `test_cobro_corte1.py` (este es de la Técnica: sólo esa afirmación, sin cambiar lo que ya mira); se acepta con un `raise` dentro del `try` del semáforo: ninguna prueba que lo llama queda verde en los 11 archivos de `tests/` (la PM midió `10 failed` en esos tres), y sin él los tres archivos verdes enteros (`166 passed, 2 xfailed`); el informe trae ese rojo medido; sin adversario ni `/security-review`. 3) los demás vencidos míos, uno por pieza (maria8, maria1d, maria5, valor1b, doc1.py, maria7, guardar2). D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D246. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
