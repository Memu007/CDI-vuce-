# Reproducción de DESTINO-1 (2026-10-28)

Entrega de la Dev MARIA: producto en `f887b4a` (informe `eacf591`), y la
devolución de pruebas en `b9881fb` (informe `3d001a6`), sin producto.

## Suite

Sobre `f887b4a`, copia limpia, SQLite: `1 failed, 3930 passed, 102 skipped,
2 xfailed`. El rojo es
`test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`,
el de tiempos que arregla EXCEL-2b. Preexistente, no de esta pieza.

## Adversario (Sonnet alto, contexto nuevo), sobre `f887b4a`

No sacó un par mezclado ni un destino distinto del elegido. Lo que encontró
fueron pruebas que faltaban: la PM agregó `item.pop('iva_adicional', None)`
y `combined.pop('iva_adicional', None)` en `maria_generator.py`, y las
pruebas daban `182 passed` con el TXT en `COMERC`/`NO_VALIDA` donde debía
salir `BDEUSO`/`IVAAD2`. Devolución por la causa: ninguna prueba miraba el
par de un ítem armado con varias entradas.

## La vuelta, sobre `b9881fb`

- `git show --stat b9881fb`: sólo `tests/test_destino1.py` y
  `scripts/testing/sabotajes/destino1.sh`.
- `tests/test_destino1.py`, corrida de la PM: `32 passed`.
- `destino1.sh b9881fb`, corrida de la PM desde la raíz: 19 sabotajes, los
  19 en `ROJO`, «sabotajes sin rojo: 0», `rc=0`. Los cuatro nuevos:
  «los renglones juntados pierden su destino» y «el grupo pierde su
  destino» (los dos mutantes de la devolución, `('COMERC', 'NO_VALIDA')`),
  «el grupo sale como bien de uso de una persona» (`('USOPAR', 'IVAAD1')`)
  y «el ítem con sub-ítems toma el destino de la operación».

## Punto 2(b): decidido por la PM

La devolución pedía como válido un grupo con el primero explícito y el resto
vacío. La Dev mostró que en el producto vacío es «el de la operación», así
que ese grupo tiene dos destinos y no se genera; su prueba lo fija. Tenía
razón: queda así. Heredar el del primero en silencio podría declarar mal un
ítem que el usuario dejó en «igual que la operación».

## Riesgos que quedan

- Un `iva_adicional` falso por ítem (`false`, `0`, `[]`) se toma como
  «igual que la operación».
- El 400 por destino inválido devuelve el valor entero.
- `/generate_maria/avisos` no valida el destino; el error aparece al
  generar.
- Premisa: el golden de 2025 trae `COMERC` con `IVAAD1`. Si la pregunta 7
  al despachante dice otra cosa, se reabre la tabla (D28).

## Veredicto

Aceptada sobre `f887b4a` con las pruebas de `b9881fb`. Debajo sólo tiene
ORG-1, ya integrada: la PM integró `f887b4a` en su rama (conflicto sólo en
`CHANGELOG.md`, quedan las dos entradas). Sobre el merge, `test_destino1`,
las suites de MARIA, `test_guardar2` y `test_org1`: `384 passed, 2
xfailed`. `b9881fb` entra cuando se integre lo que tiene debajo
(DESPACHO-1b tiene devolución). Nada se publica sin el «dale» de Emi.
