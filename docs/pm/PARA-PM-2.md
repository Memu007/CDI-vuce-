# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PYPDF-1: **entregada**. Producto `f3bd528`, pruebas `2471da2`+`9204e26`+`db384f1`+`974263e`, informe en el commit siguiente. SHA entregado `974263e` (incluye el merge `9c2ded8` de la limpieza de la PM) (2026-11-06)

**Resultado.** pypdf 6.21.4 es un arreglo de seguridad: suma topes propios
(array 100 000, dict 100 000, árbol de hojas 2 000 000, trabajo de parseo
2 000 000) que cortan solos la mayoría de los PDF armados. No se fija una
versión vieja: se adapta hacia adelante. El producto cambia en un solo lugar
(trata el tope propio de pypdf como «demasiado pesado»); el resto es prueba.

## Decisiones

- **D89 (seguridad/datos): ¿se deja el tope de memoria del hijo (256 MB) como
  red de respaldo, sin prueba que lo dispare?** Hoy ninguna entrada sintética
  llega a 256 MB: pypdf corta antes con sus topes. El tope sigue siendo
  defensa en profundidad (caro nada: ya está puesto) por si una versión futura
  de pypdf afloja un tope. **Recomiendo (a): dejarlo y no fabricar una bomba
  más grande** para dispararlo (sería una carrera contra los topes de pypdf,
  fuera de alcance). Opción (b): invertir en buscar un vector residual.

- **D90 (reversible): toda `LimitReachedError` se trata como «demasiado
  pesado», incluso topes que no son de tamaño** (profundidad de árbol,
  recuperación del objeto raíz: PDFs rotos o chicos). Es un 400 seguro con un
  mensaje razonable en castellano. **Recomiendo (a): dejarlo así.** Distinguir
  «roto» de «pesado» obliga a leer el texto en inglés de la excepción, frágil
  entre versiones. Opción (b): mapear algunos mensajes a «PDF inválido».

## Qué cambió en 6.21.4 y las 5 fallas (D73)

Las 5 rojas de D73 (rojas también en la base con 6.21.4):

- `test_rendimiento1c.py` ×2 (la bomba que se infla). El árbol de hojas
  repetido ahora pasa el tope propio de pypdf (`LimitReachedError: Maximum
  page tree page entry limit exceeded!`) a ~170 MB, no «más de 1 GB».
  `validar_pdf` lo trataba como PDF roto y devolvía el mensaje en inglés
  («Invalid PDF file…») en vez de «demasiado pesado».
- `test_despacho1b.py` ×3 (el corte por CPU). pypdf 6.21.4 juntó las matrices
  de texto seguidas y `T*`/extracción dejó de ser cuadrático: una hoja de
  80 KB costaba ~0,13 s y ya no gastaba el tope, así que el corte no se veía.

**Arreglo, partido:**
- Producto (`f3bd528`): `validar_pdf` suma `LimitReachedError` al `except` que
  levanta `MemoryError` → el hijo sale con 3 → la app devuelve 400 «El PDF es
  demasiado pesado para abrirlo». `requirements.txt`: `pypdf>=6.21.2` →
  `>=6.21.4`.
- Pruebas (`2471da2`): la hoja cara pasa a 500 KB de renglones (debajo del
  tope de 512 KB por hoja, >1 s de CPU), que cuesta por sus operaciones de
  texto y no porque pypdf sea lento. Sabotaje nuevo en `rendimiento1c.sh`.
- Pruebas (`9204e26`): el sabotaje del tope de RunLength vuelve a encontrar su
  línea (D87).
- Pruebas (`db384f1`): las docstrings decían «ocupa más de 1 GB»; ahora dicen
  la verdad (pypdf corta en su tope de árbol, muy por debajo del tope de
  memoria del proceso aparte).

## Por qué no se fija una versión vieja

- `requirements.txt` ya era `>=`, así que Railway instalaba 6.21.4 igual: las
  pruebas tienen que andar con el pypdf vigente, no con uno clavado.
- 6.21.3/6.21.4 son versiones de seguridad (topes de recursos + arreglos
  puntuales). Clavar 6.21.2 reabriría el vector que RENDIMIENTO-1c vino a
  tapar (un PDF chico que inflaba la app a >1 GB).

## Hallazgos de los adversarios (autorrevisión)

| # | Modelo/esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| 1 | Sonnet alto | Ninguna prueba dispara ya el tope de memoria del hijo en modo validar (sabotaje `_MAX_MEMORIA_HIJO = 1<<40` → `15 passed`). | Reproducido. Es que pypdf corta antes con sus topes (misma salida con y sin el tope de 256 MB). Va como **D89**. |
| 2 | Sonnet alto | Toda `LimitReachedError` da «demasiado pesado», también PDFs rotos/chicos. | Reproducido. Supuesto reversible: **D90**. |
| 3 | Sonnet alto | El caso del corte por CPU (`test_las_hojas_leidas_antes_del_corte`) queda con margen 1,75× (0,8 s vs 1,4 s) y sugiere bajar el tope a 0,5. | **Probado y rechazado con evidencia**: a 0,5 falló 1 de 5 (el corte cae antes de leer las 2 hojas reales); a 1,0, 10 de 10. La hoja no puede pesar más (tope 512 KB). Queda en 1,0. |
| 4 | Sonnet alto | Otros mensajes en inglés de pypdf siguen llegando al usuario («Stream has ended unexpectedly»). | Preexistente, informativo. No es de esta pieza. |
| 5 | Sonnet alto | Comentarios que dicen «más que lineal» para la extracción (`despacho_lector.py:43`, `test_rendimiento1b.py:151`, `test_rendimiento1d.py:6`). | Medido: con 6.21.4 `'` y `TJ` son lineales y `TJ` queda topeado a 100 000 elementos. Los comentarios quedaron imprecisos; van a `COLA-LIMPIEZA.md` (no se tocan dentro del arreglo, §6). |

## Riesgos

- **D89 vigente**: el tope de memoria del hijo no tiene prueba que lo dispare.
- **Margen del corte por CPU**: 1,75× en `test_las_hojas_leidas…`; estable en
  10 corridas, pero depende del reloj de la máquina. No hay palanca para
  ampliarlo (la hoja ya está en el tope de 512 KB).
- **Railway instala `>=6.21.4`**: una versión futura de pypdf puede mover sus
  topes y cambiar qué mensaje da (de ahí D90).
- **`LimitReachedError` en PDFs rotos**: mensaje «demasiado pesado» impreciso
  pero seguro (D90).
- **Mapeo asimétrico (code-review #2)**: `validar_pdf` mapea el tope de pypdf a
  «demasiado pesado», pero el otro lugar que abre el PDF (`_leer_hojas` en
  `leer_despacho`) todavía lo agarra en su `except Exception` y avisa «No pude
  abrir el PDF». No llega por la subida (ahí `validar_pdf_aparte` corre
  primero), así que no lo arreglo dentro de esta pieza; lo dejo anotado por si
  querés unificar el trato de los topes de pypdf en una pieza aparte.

## chequeo-6 (`3e6320a` → `db384f1`, mi aporte sin la limpieza de la PM)

```
chequeo-6 3e6320a..db384f1: avisos para mirar, no un veredicto
producto +4/−2
arnés +23/−18
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/despacho_lector.py: 900 → 902
avisos: 0
```
(`requirements.txt` no lo cuenta chequeo-6: sólo mira `proyecto_maria/`.)

## Puertas (SHA entregado `9c2ded8`)

| Puerta | Resultado |
|---|---|
| suite completa (974263e) | `4989 passed, 335 skipped, 3 xfailed, 95 warnings in 877.18s`, salida=0. Las 5 de D73 desaparecieron. |
| `compileall proyecto_maria` | `compileall=0` |
| sabotajes `rendimiento1c.sh` | 18 ROJO, `sabotajes con falla: 0`, salida 0. Incluye «un tope propio de pypdf vuelve a ser un PDF inválido» → `Invalid PDF file: Maximum page tree page entry limit exceeded!` |
| sabotajes de mi pieza en `despacho1b.sh` | Los que toca PYPDF-1, en ROJO: el corte por CPU de la hoja cara (`sin el temporizador de CPU`, `el corte de CPU es una Exception`, `la señal queda puesta`) y el de RunLength de D87 (`sin el tope de RunLength` → `2 failed`: `test_una_hoja_que_se_infla_con_run_length_se_saltea`, `test_los_topes_de_pypdf_cubren_todos_los_filtros`). El script entero (133 sabotajes, de DESPACHO-1b) no entra en una ventana de fondo: a los 30 min iba 36 ROJO, 0 falla, y lo cortó el límite. El set completo es puerta de la PM antes de publicar (§1 de /entregar). |
| `/code-review high` (`3e6320a..db384f1`) | Sin bug de producto. Confirmó la corrección contra pypdf 6.21.4. 4 notas de fragilidad baja: (1) el sabotaje ataba el texto en inglés de pypdf → **arreglado** en `974263e`; (3) el techo de 512 KB de `una_hoja_cara` → comentario en `974263e`; (2) y (4) van a riesgos abajo (fuera de alcance / sin palanca). |

Rojos de entorno conocidos: las 5 de D73 desaparecen (esta pieza las arregla).

## Comandos copiables (lo que cada uno muestra)

```bash
# 1) las docstrings ya no mienten
git -C /home/user/CDI-vuce- show db384f1 -- tests/test_rendimiento1c.py
# 2) el producto: un solo except suma LimitReachedError
git -C /home/user/CDI-vuce- show f3bd528 -- proyecto_maria/core/despacho_lector.py
# 3) la bomba corta en el tope de pypdf (~170 MB), no en 1 GB
#    (venv con pypdf 6.21.4)
# 4) sabotajes (deben dar todo ROJO, salida 0)
PY=<venv>/bin/python bash scripts/testing/sabotajes/rendimiento1c.sh 9c2ded8
PY=<venv>/bin/python bash scripts/testing/sabotajes/despacho1b.sh 9c2ded8
```

## Archivos de producto tocados

- `proyecto_maria/core/despacho_lector.py` (el `except` de `validar_pdf`)
- `requirements.txt`

La limpieza de la PM (tandas 1/2b/2d) vino por merge en `9c2ded8`: verifiqué
que sólo toca comentarios/docstrings (sin código ejecutable) en producto y JS.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con priority next. PYPDF-1 ENTREGADA: producto f3bd528 (suma LimitReachedError al except de validar_pdf → «demasiado pesado»; requirements pypdf>=6.21.4), pruebas 2471da2+9204e26+db384f1+974263e, SHA entregado 974263e (incluye el merge 9c2ded8 de la limpieza de la PM, sólo comentarios en producto/JS, verificado). 6.21.4 es seguridad: topes propios (array/dict 100k, árbol 2M, parseo 2M) cortan antes que el de memoria del hijo (256 MB). Las 5 fallas de D73: rendimiento1c ×2 (la bomba pasa el tope de árbol → mensaje en inglés, ahora «demasiado pesado») y despacho1b ×3 (extracción lineal: una_hoja_cara(80) ya no gastaba el tope de CPU → hoja de 500 KB). No se fija versión vieja: reabriría el inflado de RENDIMIENTO-1c. Decisiones para la PM: D89 (dejar el tope de memoria del hijo sin prueba que lo dispare; recomiendo a) y D90 (toda LimitReachedError = «demasiado pesado», reversible; recomiendo a). Próxima D libre D91. Adversario Sonnet alto y /code-review high: sin bug de producto; la sugerencia de bajar el tope de CPU a 0,5 la probé y da peor (1/5 falla); el margen del corte queda 1,75× estable; comentarios «más que lineal» a COLA-LIMPIEZA (extracción ya es lineal en 6.21.4). Puertas: chequeo-6 producto +4/−2 historia vacía avisos 0; sabotajes rendimiento1c 18 ROJO; D87 RunLength ROJO verificado directo; despacho1b entero (133) es puerta de la PM. Sigue: RESET-2 (el link de reset vuelve en la respuesta sólo con ENVIRONMENT=test, nunca por ENVIRONMENT ausente), después ABUSO-1. Reglas de Emi: nada se publica sin su «dale» para el SHA (no propongo SHA; la rama lleva e0b8626 no aceptada), nunca main, nunca force/amend de lo ya pusheado, sin secretos ni datos reales (TXT/proforma del 24/10 sólo en scratchpad), subagentes hasta alto sin Fable, no uso advisor (es de la PM), Postgres local 55432 (nunca 5432).
