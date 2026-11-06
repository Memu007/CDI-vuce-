# DESPACHO-1d: reproducción de la PM (2026-11-05)

**Veredicto: aceptada, sin integrar**, sobre `528961b` (base `38e743c`).
Se integra con `ca87d82`: debajo vienen SESION-1, ABUSO-1, OBSERVABILIDAD-1,
SUFIJOS-2 y ORG-1 sin aceptar.

## Lo que corrí sobre `528961b`

| Qué | Salida |
|---|---|
| `pytest tests/test_despacho1c.py` | `83 passed, 3 warnings in 5.92s` |
| `despacho1d.sh` | 9 sabotajes, `fallas: 0` |
| `despacho1c.sh` | 15 sabotajes, `fallas: 0` |
| `chequeo-6.py 38e743c 528961b` | `producto +64/−45`, historia vacía, `avisos: 2` |

Los dos AVISOs son el envoltorio del módulo de `finalize.js` y `ncm.js` (la
función anónima que encierra el archivo); partir `finalize.js` ya está en la
cola de limpieza.

## Mi ejemplo, distinto de los del pedido

El id de proveedor armado en el navegador, con la misma expresión de
`finalize.js:1337`, contra la regla del servidor `^[a-z0-9_]{1,60}$`: 200
«é», 59 «a» más « ñb», «😀😀😀», «東京商事 株式会社», «Ñandú » más 80 «x» y
un emoji, «ǅ» ×70, «İstanbul Ltd » más 60 «z». Los siete dan `OK` (largo 60
o `proveedor`).

## Adversario (Sonnet medio, contexto nuevo)

Nada que frene. 83 casos verdes y las 15 combinaciones de orden invertido
bien. Hallazgos, todos de antes de la pieza salvo el 6:

1. Operación colgada y catálogo con falla: sólo queda el aviso del catálogo
   (`finalize.js:765`).
2. El servidor recalcula el id de proveedor desde el nombre
   (`catalog_service.py:343`): es la propuesta CR8 de la Dev.
3. `saveNcmUsage` corre en cada salida del campo (`ncm.js:1369`).
4. Dos ventanas de 402 seguidas.
5. Cliente duplicado sin CUIT si se pierde la respuesta (`finalize.js:1144`).
6. Nuevo, informativo: la pista de memoria aparece tarde (`ncm.js:1764`).

## D69

(a), reusar el cliente creado en el panel, decidido por la PM.

## No corrido

- Suite completa: no; el cambio es de pantalla y lo cubren los 83 casos y
  los 24 sabotajes. La Dev informa la suya en el informe.
