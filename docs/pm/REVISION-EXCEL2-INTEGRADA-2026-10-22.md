# EXCEL-2 integrada — vuelve, 2026-10-22

## Candidata revisada

`d44803379ce1ddcdc6f0b7cd3e56bd0c76188c83`, rama local
`codex/excel2-integration-648`, preservada en el repo de trabajo. Base
`648cd2f`, producto `7e9c4e0`. Se aplicó sólo la pieza EXCEL-2 y devolución
XML, sin GUARDAR-2 ni cobro. Clone `/private/tmp/cdi-excel2-integration-648`.
Dev informó 356 focales y 15 escenarios JS verdes; no sustituyen esta revisión.
Quedó un CHANGELOG no commiteado, conservado además en
`/private/tmp/cdi-excel2-integration-changelog.patch`; no había producto sucio.

## Veredicto PM

**No aceptar ni publicar.** Dos incumplimientos reproducidos en la integración:

1. Ocho libros de primera hoja dentro del tope (10282491 bytes, menos de
   10 MiB) entran a la validación antes de la carga normal. La normal devuelve
   **400 a los 30.26 s**; incumple el criterio 200. Seis pesados se rechazan
   por 6660 filas frente a 5000; otros dos por tiempo. No se usó libro masivo
   ni producción. Pico RSS de la familia 261390336 bytes, por debajo del
   presupuesto de corte 900000000; el harness no activó su corte por memoria.
2. Una combinada de origen C2:C3, con XML `ref="C2:C3"`, produce CN/CN;
   cambiar sólo las comillas a `ref='C2:C3'` produce CN/vacío. Ambas respuestas
   son 200. La regex de `_xlsx_solo_primera_hoja` omite XML válido y pierde el
   origen del segundo producto. La corrección previa de `_ultima_columna`
   no corrige este otro lector de atributos.

El test de concurrencia existente calcula filas desde una estimación de 1500
bytes por fila: su fixture termina fuera del tope real y puede dar verde
porque rechaza rápido los pesados. La primera corrida del harness repitió
ese error y NO se cuenta como aceptación. La medición válida comprueba el
tamaño XML real, entre 9.5 y 10 MiB, y registra ocho entradas al validador
antes de enviar la normal.

## Lo que sí se verificó

| Caso sintético | Resultado | Pico RSS familia |
|---|---|---|
| 2000 combinadas gigantes | 200, origen CN/CN, 0.166 s de respuesta: cumple <1 s | 156581888 bytes |
| Nueve libros normales propios, base contra candidata | nueve respuestas JSON idénticas, todos 200 | ~153 MB en cada proceso |
| 250000 estilos xf | 200, 4.59 s | 304914432 bytes |
| 250000 estilos font | 200, 5.18 s | 279060480 bytes |
| 250000 estilos dxf | 200, 1.48 s | 257421312 bytes |
| Ocho libros con hoja secundaria de 25162973 bytes y relación rara | normal 200, 1.00 s; ocho pesados 400 sin productos | 261500928 bytes |

Los nueve libros son nuevos fixtures sintéticos comparables, **no** los nueve
históricos cuya lista no se recuperó. Los picos incluyen importación,
construcción de fixtures y petición, sumando RSS del proceso y sus hijos
muestreado cada 50 ms; no son un límite universal de memoria. No se midieron
todos los libros posibles ni el extremo de estilos permitido. No afirmar
que todo libro admitido usa menos de 1 GB.

## Harness y límites

Scripts y logs en `/private/tmp/cdi-excel2-independent/`: `bounded_runner.py`,
`acceptance_worker.py`, directorio `measurements/`. Cada muestra comprueba
SHA, usa subprocess propio, corte RSS de 900 MB y timeout de 90 s; mata sólo
su grupo de procesos. SQLite temporal del conftest, usuario inventado,
test-key, conectores falsos y URLs loopback. Sin archivos ni servicios reales.
La lectura de métricas requirió escalación local porque el sandbox bloqueaba
psutil; no se desactivaron controles del producto.

Los intentos iniciales normal9 con TestClient individual se bloquearon en
el cierre del portal AnyIO de la base. Se diagnosticó con traceback y se
cambió el harness a un único bucle ASGI para las peticiones secuenciales.
La comparación válida usa ese mismo transporte en base y candidata; no se
atribuyó aquel bloqueo a EXCEL-2 ni se contó como prueba aprobada.

Reproducción (todos los datos son generados en memoria):

```sh
rtk proxy /private/tmp/cdi-clean-requirements-20261020/bin/python /private/tmp/cdi-excel2-independent/bounded_runner.py /private/tmp/cdi-excel2-integration-648 d44803379ce1ddcdc6f0b7cd3e56bd0c76188c83 concurrent_border
rtk proxy /private/tmp/cdi-clean-requirements-20261020/bin/python /private/tmp/cdi-excel2-independent/bounded_runner.py /private/tmp/cdi-excel2-integration-648 d44803379ce1ddcdc6f0b7cd3e56bd0c76188c83 merged_quote
```

El wrapper imprime el exit del hijo en JSON; el primero da exit 1 por
status normal 400, el segundo exit 1 por origen perdido. No confundir exit
del wrapper con aceptación del caso; leer `exit` y `stopped` del resumen.

## Próxima entrega

Corregir ambos casos sobre la integración, con rojo previo y discriminantes.
No bajar el tope de 10 MiB decidido en D27 sin elevar decisión con lo medido.
No mover trabajo a ABUSO-1 para esquivar el criterio de EXCEL-2 ya aprobado.
Después repetir sólo las mediciones afectadas y ejecutar suite completa y
CI/e2e sobre el nuevo producto exacto. No se corrió la suite larga sobre esta
candidata porque los rojos ya impiden aceptarla. Negativos 42/43 pendientes:
la sesión Dev se interrumpió por límite de uso, no se inventan resultados.

Railway sigue pendiente para la publicación ANTERIOR autorizada, main648cd2f;
no mezclar esta devolución ni publicar automáticamente una candidata nueva.
