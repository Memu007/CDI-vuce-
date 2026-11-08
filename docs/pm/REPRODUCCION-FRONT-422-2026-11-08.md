# FRONT-422: reproducción de la PM (2026-11-08)

Entrega `4dbdb0b`, base `19b7764`, rama `claude/dev-maria` (`41d36a9`). Producto
`37ceeed`, `9ee40b8`, `8decbfc`; pruebas `ca54f74`, `1b93976`, `4dbdb0b`.

## Corrido por la PM

- `chequeo-6.py 19b7764 4dbdb0b`: producto `+73/−31`, `avisos: 1` (las +42 netas; la explicación alcanza: `errores.js` reemplaza dos traductores y cubre tres entradas que no tenían).
- `tests/test_front422.py`: `33 passed`.
- `front422.sh 4dbdb0b`: `BASE | en verde`, 17 ROJO, `sabotajes con falla: 0` (igual al informe).
- Negativos míos, `textoDeError` en node con entradas que el arnés no tiene:
  `[]`, `"   "`, `null` → genérico; `{message}` → el mensaje; `string_too_short` → «Revisá el usuario.»;
  `loc` anidado `items/0/cantidad` → «Falta el campo «cantidad» (ítem 1).»; `value_error` sin prefijo → «Email inválido.»;
  `loc` de query → «Falta el campo «page».».
- Ningún otro JS del front lee `detail` como lista (`grep` de `detail[0]`, `isArray(detail)`, `.loc`): el cambio de `CDI.api` no rompe a nadie.
- Los tres formularios de la landing comparten un solo submit: la única llamada cubre login, registro y recuperar.

## No corrido por la PM

Suite completa (la Dev la corrió dos veces, `5157 passed`), adversario (no es pieza de §3; la Dev corrió Opus alto), navegador real.

## Veredicto

Aceptada sobre `4dbdb0b`, sin integrar. D108: (a), decidido por la PM. Riesgos aceptados: R1 a R5 del informe; R1 (tres llamadas de `review.js`/`finalize.js` sin prueba que las corra) se cubre con la mirada en el navegador antes de publicar.
