# Reproducción de SEPARADORES-1b — 2026-10-25

Sobre `db39de0` (informe `8974daf`; base de comparación `a2fdabd`). La PM
corrió las pruebas, el sabotaje y dos negativos propios en worktrees limpios
(`/tmp/rev-sep1b` y `/tmp/rev-sep1b-base`). Un revisor adversarial con
contexto nuevo (Opus alto) trabajó con árboles propios. Todo local, con
sintéticos y sin Gemini.

**Veredicto:** SEPARADORES-1b, **aceptada**. Ningún 500; con un número JSON
el TXT sale idéntico al de la base; la familia «cuatro cifras o más,
separador y tres decimales» ya no sale por mil ni en la factura ni en la
pantalla. Lo que queda abierto es de antes o necesita saltearse la revisión,
y va a una pieza chica, **SEPARADORES-1c**.

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| `pytest tests/test_separadores1b.py tests/test_separadores1.py tests/test_valor1.py tests/test_valor1c.py` | `295 passed, 3 warnings in 79.84s` |
| `bash scripts/testing/sabotaje_separadores1b.sh db39de0 /tmp/cdi-pm/venv` | «OK: los 12 sabotajes dan rojo por la razón esperada», rc=0 |
| Suite completa sobre `db39de0` | ver «Suite» abajo |
| `MariaExportRequest` (`main.py`) | sigue con `flete: float` y `seguro: float`: la exportación no cambia |

El script de sabotaje usa por defecto el venv de la máquina de la Dev
(`/tmp/cdi-dev2/venv`); en otra máquina hay que pasarle el venv como segundo
argumento (sin él sale con `rc=127`).

### Negativo propio, servidor

Cinco campos (flete, seguro, gastos, ajustes a incluir y a deducir) por 14
textos raros contra `/generate_maria` y `/generate_maria/avisos`, más una
prueba de igualdad: `71 passed`, ningún 500. Los textos: «1_000», «nan»,
«inf», «-0», «12.345», «+5», cifras árabes, «1e3», «0x10», «99999999999999999999»,
« 12.50 », «   », «12.», «.5».

- Flete, seguro o gastos ilegibles: 400 con el campo nombrado (por ejemplo
  «Gastos (gastos_fob): «+5» no es un importe.»).
- «-0», « 12.50 » y blanco: 200. « 12.50 » como texto da un TXT idéntico
  byte a byte al de 12.5 como número.
- Un ajuste ilegible: 200 en las dos rutas, no entra al TXT (D12) y se dice
  en las cuentas.

### Negativo propio, pantalla (`montos_ar.js`, `leer`)

| Escrito | `db39de0` | `a2fdabd` |
|---|---|---|
| «7654.321» | pregunta «¿7.654.321 o 7.654,321?…» | 7654.321 |
| «123456,789», «1000.000», «9999,999» | pregunta | no corrido |
| «1234.56», «12345.6» | 1234.56, 12345.6 | no corrido |
| «1.234», «12.345», «123.456» | 1234, 12345, 123456 | no corrido |
| «1.234.567,891», «10.000.000», «4.500.000», «1,000,000.50» | 1234567.891, 10000000, 4500000, 1000000.5 | no corrido |
| «0001.500» | 1.5 | 1.5 |
| «1 000.000» | «Debe ser un numero.» | igual |
| «4500.000,00» | «Los puntos y comas no cierran…» | no corrido |

## Lo que probó el revisor (Opus alto)

- **Punto 1 (D19 b):** unas 60 variantes de flete, seguro, gastos, seguro
  calculado y ajustes en las dos rutas, en base y entrega: cero 500; con
  número JSON, TXT idéntico; «7925», «7925.00», « 7925 », «007925»,
  «7925\n», «-0» como texto, TXT idéntico a la base. Todo lo que lee esos
  campos antes de convertirlos pasa por `importe_valido`; ningún otro
  endpoint usa `MariaRequest`.
- **Punto 2, pantalla:** `leer` en 1157 entradas, base contra entrega: las 72
  diferencias son todas de la familia nueva y pasan de leerse a preguntarse;
  ninguna cambia de magnitud. 5 millones de cifras con «.123», 0,7 s; 20
  millones de caracteres «1.123.123…», 2 s.
- **Punto 2, factura:** las 25 diferencias de `_monto_factura` entre las tres
  pistas son las buscadas (antes por mil, ahora sin leer). Dos más pasan de
  un número a sin leer: «1 234.567» con «,» y «1 234 567,000» con «.»
  (mezclan espacios con otro separador de miles): más seguro, queda marcado.

## Hallazgos

| # | Qué | Gravedad | Qué se hace |
|---|---|---|---|
| H1 | **Cero adelante en la factura.** `_monto_factura` da «0500.000» con «,» → 500000 y «01500.000» con «,» → 1500000 (reproducido por la PM). Es la D21 de la Dev: de antes, la regla nueva exige 1-9 adelante. También «01,500» con «.» → 1500: **la PM se equivocó en la tarea** al decir que con el cero adelante no puede ser miles. | plata, baja (entrada improbable) | SEPARADORES-1c |
| H2 | **Un monto ilegible puede llegar al TXT como 0.** `trim()` de JS no saca `\x85` ni `\x1c`-`\x1f`; `strip()` de Python sí. `leer("\x85")` da error, `montoDelPedido` manda «\x85», `importe_valido` lo deja en blanco, None, y el TXT sale `MDDTFLE=0.00` (la base daba 422). La revisión lo frena (por código, no probado en navegador): sólo se llega salteándola, que es justo el camino que D19 quería cubrir. | plata, baja | SEPARADORES-1c |
| H3 | **La pregunta sugiere tres decimales.** Para «2500.125» propone «2.500,125», que `leer` acepta y el TXT redondea a 2500.13 sin aviso; para «4500.000» propone «4.500,000» en vez de «4.500»; para «-1234.500» pierde el signo. | plata muy baja (un centavo), mensaje | SEPARADORES-1c |
| H4 | Por API, «» y «   » en flete, seguro o gastos daban 422 y ahora 200 con 0 o None. Lo dice el docstring de `importe_valido` y la pantalla manda 0 para el campo vacío. | cambio buscado | no se toca |
| H5 | Por API, textos como «+7925», «7_925», «1e3», «7.925» ahora dan 400 (antes 200, y «7.925» salía 7,93). La pantalla nunca los manda como texto. | cambio buscado (D19) | no se toca |
| H6 | El mismo campo se nombra «Gastos (gastos_anteriores_fob)» y «Gastos (gastos anteriores a FOB)» según el control. Una cifra gigante arma un mensaje de varios MB (no traba). | cosmético | no se toca |

## Suite

Desde base limpia sobre `db39de0` (`rm -f test.db`, entorno de prueba con
los modos simulados):

```
FAILED tests/test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal
= 1 failed, 2384 passed, 102 skipped, 2 xfailed, 92 warnings in 499.23s (0:08:19) =
rc=1
```

El rojo es el conocido de EXCEL-2 (`NOW.md`): la subida normal espera detrás
de ocho libros grandes y pasa el tope de 30 s en esta máquina; la Dev lo
informó también sobre la base `a2fdabd`. No lo toca este diff. Al cerrar
quedan 32 líneas «Task was destroyed but it is pending!» de asyncio, ruido
del cierre.

## Limpieza

Sin `uvicorn`, `chromium` ni `pytest` andando al terminar (`ps`). Worktrees
`/tmp/rev-sep1b` y `/tmp/rev-sep1b-base` borrados; el sabotaje borra el suyo.
