# AJUSTE-BORRADOR — reproducción de la PM (2026-11-13)

Pieza de MARIA: un ajuste mal escrito, después de recargar y recuperar la
operación, se ve en el campo que nombra el aviso. Base `a647bee`, rojo
`a57b584`, entregado `d094c24`, informe `fdaa2da`. Producto +4/−4
(`finalize.js`, dos guardas menos) y `CHANGELOG.md`.

**Veredicto: aceptada sobre `d094c24` e integrada (`fdaa2da`).** D227 (a) y
D234 (a), decididas por la PM.

## Lo que corrí

Worktree en `d094c24`, venv de la PM, sin red.

| qué | resultado |
|---|---|
| `pantalla_ajuste1.js` sobre `a57b584` | `ROJA ajuste1 rc=1`, `FALLA: el aviso dice «Ajustes a incluir: no es un número. …` |
| `pantalla_ajuste1.js` sobre `d094c24` | `verde ajuste1 rc=0`, `PANTALLA AJUSTE-1 OK` |
| `tests/test_valor1.py` | `76 passed` |
| lo mismo con el `finalize.js` de `a647bee` | `1 failed, 75 passed`: `test_un_ajuste_mal_escrito_se_ve_en_el_campo_que_llega_vacio` |
| mi negativo: la guarda vuelta a poner sólo en Ajustes a deducir | `1 failed, 75 passed`, el mismo caso |
| mi negativo: sin `document.activeElement !== incluir` (`:451`) | `76 passed`: hueco de valor1, va a SUFIJO-BORRADOR |
| lo mismo con `deducir` (`:454`) | `1 failed`: `test_lo_que_se_esta_escribiendo_no_se_pisa` |
| `e2e_maria.sh` sobre `d094c24` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| `chequeo-6.py a647bee d094c240` | producto +4/−4, arnés +116/−11, historia vacía, 0 avisos: igual al informe |

El primer negativo es el espejo del que informó la Dev sobre `a7511e0`; el
segundo ataca otro borde (no pisar lo que se escribe) y encontró que la
prueba mira un solo campo. No es de este diff: lo dejó valor1.

## D227

Leído, no corrido: `sbtInput` (`finalize.js:16`, `:60`) sólo se lee
(`:671`) y se enfoca (`:683`); ninguna línea de `static/v2` le asigna valor.
`despachante.js:256` prefiere el campo a la operación. Pieza aparte,
SUFIJO-BORRADOR, con el rojo primero.

## D234

Reproducido con el comando 4 de la Dev: la prueba sola `7 passed` (3,59 s);
con 1075 hilos dormidos, `1 failed` 2 de 2 (1,47 y 1,13 s de CPU). Escape en
EXCEL2D-RELOJ (commit propio); vuelve a la Técnica.

## No corrido por mí

`pytest` entero (la Dev lo corrió: `1 failed, 6110 passed`, el rojo es D234),
`sabotaje_valor1.sh` (sus 29 `ROJO`), `compileall` y las 31 pantallas. Si la
CI de la PR sale roja en `test_la_subida_cara_no_frena_a_nadie` después de
este push, es D234 y no esta pieza.
