# SUFIJO-BORRADOR, vuelta de la devolución (D236 b): reproducción de la PM

Entrega `52f13ca` (informe `6fbfefd`, canal `PARA-PM-2.md`). Base `0d4cd72`.
Veredicto: **aceptada sobre `52f13ca`; se integra después de publicar `7436c6e5`**
(la PR a `main` publica la cabeza de la rama de PM y el «dale» es para `7436c6e5`).

## Corrido por la PM (2026-11-13, 19:14–19:16 UTC)

- `correr_pantallas.sh` con `SOLO="sufijo_otra1 sufijo_borrador1 pm_trasgenerar"` sobre
  `52f13ca` + sonda mía (commit local descartable `6244c52`): `resumen: 3 verdes, 0 rojas`.
- Rojo: lo mismo con `finalize.js` de `ee2ee3c` (commit descartable `2ef395d`):
  `resumen: 0 verdes, 2 rojas: pm_trasgenerar sufijo_otra1`. Las tres llegadas de su caso dan
  `campo / operación / tarjeta = «AA(000123) /  / lo marca escrito con otro sufijo»; «Generar» siguió a «ready» y salieron 1 POST /generate_maria`.
- Mi ejemplo, no dado a la Dev (`pm_trasgenerar`): A se **genera de verdad** con `AB(000777)`
  (TXT 200 con ese `CSBTSVL`), «Nueva operación» de la barra, B sin sufijo.
  Verde: `OK B tras generar A: campo vacío, frena, 0 POST`. Rojo sobre `ee2ee3c`:
  `campo / operación = «AB(000777) / »; «Generar» siguió a «ready»; POST /generate_maria = 1`.
- `e2e_maria.sh` sobre `52f13ca`: `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.`
  La unión `1163424` difiere de `52f13ca` sólo en `docs/pm/NOW.md` (diff fuera de docs vacío).
- `chequeo-6.py 0d4cd72 52f13ca`: igual al informe (producto +5/−11, historia vacía, avisos: 0).
- Leído, no corrido: el camino real «Nueva operación» + carga. `app_v2.js:890` hace
  `CDI.state = {}` y `upload.js:352`/`:695` reemplazan `operacion` por la que trae la carga,
  así que B no hereda `sbt_sufijo_valor` dentro de la operación.

## No corrido por la PM

Suite entera (la Dev: `6130 passed, 110 skipped, 3 xfailed`), las 34 pantallas, `orden1`
(su rojo en z22 descansa en su diagnóstico: firma de D237), tres de sus cuatro rojos
(`740b38a`, `8a9a8f6`, `8e6b598`), sabotajes valor1/valor1c, `anclas_perdidas.py`.
Sin adversarios: la pieza es sólo de pantalla, no toca dinero, sesión, permisos ni datos.

## Decisiones y riesgos

- **D238: (a), decidido por la PM**, pieza chica aparte después de D237 (a).
- Valor en el campo sin evento `input`: ahora frena en vez de generar (dirección segura). Riesgo bajo.
- `despachante.js:255` lee el sufijo del campo, «Generar» de la operación: a `COLA-LIMPIEZA.md`.
- Mi sonda usa dos esperas fijas (600 ms y 1,5 s): es descartable, no entra al arnés.
