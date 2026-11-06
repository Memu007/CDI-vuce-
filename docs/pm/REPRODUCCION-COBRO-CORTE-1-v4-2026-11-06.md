# COBRO-CORTE-1 (vuelta 4): reproducción de la PM, 2026-11-06

Producto `ca50916`, informe `0c2e805`, rama `claude/dev-tecnica` en `8a1dcdd`.
Base de la vuelta `633c383`; base del chequeo-6 `d26c404`. Entorno: venv
Python 3.12, Postgres 16 local descartable, SQLite para pytest, Chromium. Sin
red; adversarios con `GEMINI_API_KEY` vacía.

**Veredicto: aceptada, sin integrar.** La rama técnica lleva debajo piezas sin
aceptar (desde `e0b8626`); se integra cuando lo estén. Las tres cosas de la
devolución quedan cerradas: la respuesta escribe en la carga que la pidió
(historial, catálogo y cliente), la carga B puede generar cuando vuelve A, y
regenerar ya no depende de `os.link`.

## Puertas

| Puerta | Resultado PM |
|---|---|
| `tests/test_cobro_corte1.py` en `ca50916` | `98 passed` en 59 s |
| `chequeo-6.py d26c404 ca50916` | `avisos: 3`, los tres explicados en el informe (netas acumuladas de la pieza, la función anónima de `finalize.js`, `casosTardios` de 67 líneas como datos) |
| `sabotajes/cobro_corte1.sh ca50916`, con Postgres | 88 `ROJO`, 0 `ROJO?`, 0 VERDE, 0 ROTO; tres bases en verde (pytest, pantalla, lock); `sabotajes con falla: 0`, rc=0 |
| suite completa en `ca50916` | `4284 passed, 335 skipped, 3 xfailed, 99 warnings in 500.59s`, rc=0 |

La primera corrida de la suite guardó sólo las últimas 8 líneas, todas
`Task was destroyed but it is pending!`, y se perdió el resumen: la volví a
correr entera a un archivo. El harness choca con `con_pg16.sh` por la variable
`PUERTO`; corrí los sabotajes con `unset PUERTO` (va a la cola).

## Adversarios (contexto nuevo, sin red)

**Sonnet alto, pantalla.** Las cuatro promesas aguantan, con ejemplos
distintos de los míos. Hallazgos:

1. **Media, de antes (`f9edbc1`, 07/10).** `runValidation`
   (`finalize.js:103-108`) reusa `lastValidation` durante 60 s sin mirar de qué
   carga es: el panel de B muestra totales, errores y avisos de A, el historial
   de B se guarda con los totales de A, y «Generar» se habilita o no por los
   errores de A. Reproducido (`sc7.js`). No entra en esta pieza: va como
   propuesta de pieza nueva a Emi.
2. **Baja, de antes, ya en la cola:** recargar o reintentar con la generación
   en vuelo vuelve a cobrar.
3. **Baja:** una generación colgada deja la carga siguiente en el spinner;
   `CDI.api` no tiene timeout (`finalize.js:654`).
4. **Baja:** Enter repetido en «Generar» manda dos POST; el segundo reusa el
   `operacion_id` y no cobra otra vez.

**Opus alto, servidor y pantalla.** Sin doble cobro ni datos de otra carga.

1. **Baja:** dos Enter de teclado en «Reintentar» dan dos generaciones
   (`finalize.js:1361-1366`, `:653`), sin cobro extra. Es el riesgo que la Dev
   declaró.
2. **Baja, falla doble:** si falla el commit y además falla restaurar
   `.anterior`, se pierde el archivo ya entregado (`main.py:5933-5941`).

## No corrido

`smoke_friccion.sh` y `ataque_aislamiento.sh`: la vuelta no cambia quién ve
qué datos.
