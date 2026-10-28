# Reproducción de SEGURO-1 (2026-10-28)

Entrega de MARIA en `5dfaf47`: producto `4f75f3d` y `bf6e1d7`, pruebas
`a08de1f`, `371cde2` y `5dfaf47`. La rama trae debajo SUFIJOS-2, que volvió
con devolución: se integra con la cadena, no antes. Suite de la Dev sobre
`5dfaf47`: 4007 passed, 0 failed. La PM no corrió la suite.

## Corrido por la PM sobre `5dfaf47`

- `tests/test_seguro1.py`: `48 passed`.
- Mutante: sumar `DAT`, `DDU`, `DAF`, `DES` y `DEQ` a
  `INCOTERMS_CON_SEGURO` (`maria_generator.py:952`): `48 passed`. Sumar
  sólo `DAT`: `48 passed`. Ninguna prueba fija que la lista sea esa.
- Lectura: `_seguro_calculado_viejo` (`main.py:4456`) vuelve sin decir nada
  si el pedido no trae `seguro_calculado`. Es lo encargado (el seguro
  «calculado por el sistema» es el que trae la marca); un 1 % mandado sin
  la marca no se distingue de uno escrito a mano.

## Adversario (Sonnet alto, contexto nuevo)

Sin hallazgos graves: con los cinco incoterms el 1 % calculado no sale por
ninguna ruta que arme el sistema. Mutantes: agregar `CFR` a la lista,
quitar el `raise` y que la pantalla no vacíe el seguro dan rojo. Lo demás,
no corrido por la PM:

1. Con `seguro_calculado` en false (u omitido) y CIF, el 1 % entra al TXT.
   En la pantalla: calcular con CFR, «Dejar el seguro», pasar a CIF. Es la
   regla encargada; va a riesgos y a SEGURO-2 (D30 b, para Emi).
2. `/generate_maria/avisos` no normaliza el incoterm como `/generate_maria`
   (`"CIF\x00"` ofrece el botón; generar da 400). No se llega por la
   pantalla.
3. Seguro mayor que el FOB sin aviso. Preexistente.
4. La revisión avisa «no los sumes dos veces» con CIF y seguro > 0, y el
   400 pide «cargá el de la factura en la revisión». Sólo lectura.
5. Parpadeo del aviso viejo en la pantalla. Cosmético.

## Veredicto

Aceptada sobre `5dfaf47`. Se suma a la próxima entrega de MARIA la prueba
que fija la lista y la normalización de los avisos.
