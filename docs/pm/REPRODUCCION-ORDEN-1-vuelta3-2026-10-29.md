# Reproducción de ORDEN-1, tercera vuelta (2026-10-29)

Entrega de la Dev técnica: producto `92bbaa2` (diff `40e5a63..92bbaa2`,
sólo `app_v2.js`); CHANGELOG `7b20882`; pruebas y sabotajes hasta
`f7fbb72`. Es la vuelta de la devolución del 2026-10-29 01:00 UTC (H1:
la sesión que cambia durante la espera del candado).

## El arreglo, leído

- `adoptarBorrador` toma el usuario con `usuarioActual()` antes de escribir
  y, sin usuario, no escribe ni borra nada. `usuarioActual()` sólo devuelve
  el dueño fijo de la pestaña o `null` (con otro usuario, `sesionAjena`), así
  que nunca puede escribir a nombre de B ni dejar un sobre sin usuario.
- `click` se suma a `pointerdown`, `keydown` y `drop` para marcar la
  pestaña como tocada.

## Lo que corrió la PM

- `orden1.sh` sobre `f7fbb72`: 76 ROJO, «sabotajes sin rojo: 0», «fin rc=0» (igual que el informe; el `ROJO?` intermitente de z8 sobre `92bbaa2` no apareció con la espera por condición).
- **Adversario Opus alto**, con un ejemplo distinto del de la devolución
  (API local en SQLite):
  - recuperación tardía con la pestaña original cerrada y B que entra entre
    buscar y adoptar: la pestaña queda en la carga con «Entró otro
    usuario…» y el sobre sigue intacto con `user` A; A lo recupera después
    en otra pestaña;
  - lo mismo borrando las cookies: «Se cerró la sesión…», sobre intacto;
  - dos pestañas restauradas con el mismo id a la vez: se duplica, no se
    pierde;
  - z9 a z12 en verde en su entorno.
- **Adversario Sonnet alto:**
  - ningún `.click()` del producto se dispara solo al arrancar, así que
    `click` no frena la recuperación tardía sin motivo (por lectura de
    todos los `.click()` y `dispatchEvent` de v2);
  - cuatro mutantes que no están en `orden1.sh` dieron rojo: el usuario
    tomado antes de la espera (z9, z10), no borrar la clave vieja (caso a),
    los listeners en burbuja (z15) y devolver el estado sin escribir (z9);
  - z8 nuevo: sin el arreglo de sesión da rojo; con el aviso visible ya no
    puede haber un guardado a nombre del otro.

## Hallazgos

1. **Media, anterior a ORDEN-1 (la D12 de la Dev), reproducida por el
   adversario Opus.** Con «Entró otro usuario…» en pantalla, la pestaña de
   A sigue mostrando la operación de A y el nombre de A arriba. Si se
   aprieta Generar, `/generate_maria` sale con la cookie de B: la operación
   se crea y se cobra en la cuenta de B, y el TXT con el CUIT del comprador
   y la factura de A queda descargable desde la cuenta de B, desde otro
   dispositivo. A no tiene registro. El camino probable no es malicioso:
   A vuelve a su pestaña y ve su nombre. Salida:
   ```
   generate_maria: 200 filename= MARIA_FAC_FACTURA-DE-A.TXT
   operaciones de B: "total":1 … "generated_file":"MARIA_FAC_FACTURA-DE-A.TXT"
   ops_used_this_period de B: 0 → 1
   operaciones de A: "total":0
   /download/MARIA_FAC_FACTURA-DE-A.TXT 200 (desde otro contexto, sesión de B)
   ```
   Por lectura, las otras escrituras desde esa pestaña (`/api/clientes`,
   productos del catálogo, `guardar-uso` de NCM) tienen el mismo problema.
   Un `estudio_id` de A con la cookie de B lo rechaza `_estudio_elegido`
   (lectura). No es de este diff: ORDEN-1 agregó el aviso; antes ni se
   avisaba.
2. **Baja, reproducida por los dos adversarios.** Cuando `adoptarBorrador`
   no tiene usuario (A sale y vuelve a entrar en la espera), la pestaña
   queda en la carga, vacía y sin aviso, y no reintenta cuando la sesión se
   confirma. La operación sigue guardada y se recupera al recargar o desde
   otra pestaña. Es la D11 de la Dev.
3. **Baja, por lectura.** En la recuperación tardía, `pestanaTocada` se mira
   después de la espera del candado; ninguna prueba toca la pestaña durante
   esa espera. El producto está bien.
4. **Baja, anterior.** `/logout` (el de la v1) no borra `csrf_token`: la
   pestaña v2 sigue guardando a nombre de A, sin aviso. Dueño correcto, sin
   daño de datos. Ya estaba en riesgos.

## No corrido por la PM

La suite completa (la corrió la Dev sobre `92bbaa2`: 4283 passed, rc=0; el
cambio de producto son dos líneas de JS), el ataque de aislamiento y el
smoke.
