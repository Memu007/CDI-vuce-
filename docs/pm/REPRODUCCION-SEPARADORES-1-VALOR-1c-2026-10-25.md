# Reproducción de SEPARADORES-1 y VALOR-1c — 2026-10-25

Sobre `a099655` (informe `4548644`; base de comparación `a74ee9d`, producto
igual a `efa2e08`). La PM corrió los casos y los dos sabotajes en un
worktree limpio (`/tmp/rev-sep`), sola, uno detrás del otro. Un revisor
adversarial con contexto nuevo (Opus alto) trabajó con árboles propios de la
base y de la entrega. Todo local, con sintéticos y sin Gemini.

**Veredicto:** SEPARADORES-1 y VALOR-1c, **aceptadas**. Ningún TXT con el
flete, el seguro o el valor equivocado sin freno ni aviso; ningún 500 nuevo;
el TXT es idéntico byte a byte salvo los casos pedidos. Lo que queda va a una
pieza chica, **SEPARADORES-1b** (D19 b y la agrupación mal formada).

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| `git diff --stat a099655 origin/claude/dev-maria -- . ':!docs/pm'` | vacío: el merge `d4a3f08` es sólo de `docs/pm` |
| `pytest tests/test_valor1c.py tests/test_valor1.py tests/test_maria9_kilos.py tests/test_separadores1.py tests/test_prelaunch_block1.py tests/test_maria7_rechazos_24_10.py` | `301 passed, 5 warnings in 39.29s` |
| `scripts/testing/sabotaje_valor1c.sh a099655` | «OK: los 26 sabotajes dan rojo por la razón esperada», rc=0 |
| `scripts/testing/sabotaje_separadores1.sh a099655` (incluye los 3 del navegador) | «OK: los 17 sabotajes dan rojo por la razón esperada», rc=0 |
| Suite completa sobre `a099655` | ver «Suite» abajo |
| Negativo propio: `montos_ar.js`, 200.000 montos al azar de 0 a 9 dígitos con centavos, `leer(escribir(n))` y `leer` del formato `es-AR` | `casos 200000 malos 0`, ninguno quedó sin valor |
| Lectura: dónde se borra la marca | sólo `review.js:666`, en `onFieldChange` del campo `seguro` (un evento de la persona), y en «Dejar el seguro como está» (`finalize.js`). Un ajuste o el flete no la borran. Verificado por código; en el navegador sólo se corrió que el flete la conserva |
| `git diff a74ee9d a099655 -- CHANGELOG.md` | dos entradas que dicen sólo lo probado |

## Lo que probó el revisor (Opus alto)

- **Byte a byte**, 56 pedidos contra `/generate_maria` y `/avisos` en la base
  y en la entrega: TXT idénticos en todos los que dan 200 en las dos. Las
  diferencias son las pedidas: el general que nadie usa pasa de 400 a 200 y
  no va al TXT; desaparece su aviso; con la marca y un seguro viejo, 400;
  sin ítems, 400 en vez de un TXT sin productos; si alguien usa el general,
  sigue en 400.
- **Fuzz** de 333 pedidos: ningún 500 nuevo. El único 500 de la base
  (`grupo_id=[1]` con la marca) ahora es 400. Los 17 que pasan de 200 a 400
  son la marca con cuentas en error o con un seguro viejo.
- **La marca en el navegador (Playwright):** calcular da 14,88 y la marca;
  el flete cambiado a «2.000» en revisión la conserva; generar da 400 con
  «…con los de ahora da 33,88 y la operación lleva 14,88…» y aparece
  «Dejar»; después de «Dejar», 200 con `MDDTASS=14.88 MDDTFLE=2000.00`. Al
  recargar, la marca sobrevive y validar ofrece «Recalcular seguro…: 33,88»
  y «Dejar».
- **D19 en el navegador:** con «abc», «1,500» o «-5» en el flete, o «abc» o
  «1,000» en el seguro, la pantalla no sale de revisión. Por código, la
  validación sólo se alcanza desde revisión.
- **`_monto_factura`**: 41 entradas por tres pistas decimales. «3.480»,
  «3.480,00», «1.234.567», «1,234.56», «USD 3.480», «$3.480», «0.500» y
  «12.345.678,90» salen bien; negativos y «(3.480)» quedan sin leer.
- **D18** por lectura: la agrupación y el IVA coinciden entre el endpoint y
  el generador.

## Hallazgos

| # | Qué | Gravedad | Qué se hace |
|---|---|---|---|
| H1 | **Agrupación mal formada en la factura.** «3480.000» con pista decimal `,` da 3480000; «3480,000» con pista `.` da 3480000 (reproducido por la PM llamando a `_monto_factura`). La regex de miles no los toma y caen a `_numero_factura`. Hace falta que la pista contradiga el monto, pero si la pista está mal, el flete sale ×1000 sin preguntar, que es lo que SEPARADORES-1 vino a cerrar. | plata, baja | SEPARADORES-1b, punto 2 |
| H2 | **Lo mismo en la pantalla.** «1234.567» y «1234,567» se toman como 1234,567 sin preguntar; «1.234» bien agrupado es 1234. Una persona que escribe «1234.567» pensando en miles mal puestos queda ×1000 más chica. | plata, baja | SEPARADORES-1b, punto 2 |
| H3 | Lo que la factura deja sin leer termina en flete 0 con el aviso no bloqueante «No pudimos leer flete…» y se puede generar con `MDDTFLE=0.00`. Es el diseño de MARIA-1c, pero SEPARADORES-1 manda más casos ahí (pista igual al separador). | riesgo | anotado; no se toca |
| H4 | «1.234,567» (tres decimales con los dos separadores) se acepta. No es ambiguo. | cosmético | no se toca |
| H5 | `pais_origen` «Narnia» sale `CARTPAYORI=310` sin aviso. No viene de este diff (antes lo tapaba el 400 del general). | fuera de alcance | anotado para M9 |

«01,500» no es hallazgo: con el cero adelante no puede ser miles, así que
1,5 es la única lectura.

## Suite

Desde base limpia sobre `a099655` (`rm -f test.db`, entorno de prueba con
los modos simulados):

```
==== 2280 passed, 102 skipped, 2 xfailed, 23 warnings in 252.78s (0:04:12) =====
rc=0
```

Igual a lo que informó la Dev. Al cerrar quedan 32 líneas «Task was
destroyed but it is pending!» de asyncio: es ruido del cierre, no hace
fallar nada y la suite sale con rc=0.

## Limpieza

Sin `uvicorn`, `chromium` ni `pytest` andando al terminar (`ps`). Worktree
`/tmp/rev-sep` borrado.
