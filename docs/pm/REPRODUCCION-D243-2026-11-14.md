# D243 (b): reproducción de la PM

Entrega `0dff850` (merge `ff3eea2`, informe `4474108`, canal `PARA-PM-2.md`). Base
`2a0b8e8`. Veredicto: **aceptada sobre `0dff850`**. Sólo arnés.

## Corrido por la PM (2026-11-14, worktrees descartables)

- `chequeo-6.py 2a0b8e80 0dff8503`: igual al informe (producto +0/−0, arnés +8/−8,
  historia vacía, avisos: 0). Diff: 3 archivos, las cuatro anclas de la tabla de D243.
- Unión: integro `4474108` (no la cabeza de su rama, que ya trae SABOTAJE-SUFIJOS1
  sin revisar). `git diff --stat 036e294e 4474108 -- . ':!docs/pm'` da sólo esos tres
  guiones. `git diff --stat 29327d2 4474108 -- proyecto_maria/` vacío: el producto
  es el de CUIT-GENERAR, y su suite entera (`6143 passed`) sigue valiendo.

| corrida | resultado |
|---|---|
| `anclas_perdidas.py 0dff8503` | «perdida, una línea 6 guiones: 5» (de vuelta a la base) |
| `estudio1.sh 0dff8503`, copia del SHA, 04:25–04:48 UTC | `rc=0`, 37 `ROJO`, `sabotajes sin rojo: 0` |
| `estudio1b.sh 0dff8503` | `rc=0`, 20 `ROJO`, `sabotajes sin rojo: 0` |
| `excel2.sh 0dff8503` | `rc=0`, 42 `ROJO`, `sabotajes con falla: 0` |
| sabotaje mío `crudo = cuit_agr or del_perfil` (sin el estudio) | `5 failed, 199 passed` |
| sabotaje mío `es_el_del_perfil = … and False` | `9 failed, 195 passed` |
| sin sabotaje (`test_estudio1`, `1b`, `cuit_generar`, `excel2`) | `204 passed` |

Los cuatro sabotajes cambiados, cada uno en `ROJO` por la prueba que lo nombra:
`test_el_estudio_elegido_va_al_cddtagr_aunque_haya_perfil_y_cuit_agr`,
`test_el_cuit_del_perfil_en_cuit_agr_cuenta_como_uso_del_perfil`,
`test_un_cuit_agr_propio_no_cuenta_como_uso_del_perfil` y
`test_el_cuit_del_despachante_va_solo_con_11_digitos`.

## Error mío en la primera corrida

La primera vez (terminó a las 04:24) corrí los guiones desde mi checkout
(`036e294e`), o sea la copia vieja con las anclas viejas contra el `main.py` nuevo:
`rc=1` en los tres, con 1, 2 y 1 `ROTO` «el sabotaje no encontró su patrón»,
justo en los cuatro sabotajes cambiados. No dice nada de la entrega. Un guion de
sabotaje se corre con la copia del SHA que se revisa.

## Notas de la Dev

Ninguna pide decisión. El comentario viejo de `excel2.sh:171` (de la Técnica) va a
`COLA-LIMPIEZA.md`.

## No corrido por la PM

La suite (sólo arnés; el producto es el de `29327d2`), pantallas, `e2e_maria.sh`,
adversario y `/security-review`. La corrida se superpuso con la tanda de fondo
(`run6`, sobre `7436c6e5`) y, desde las 04:46, con el guion de SABOTAJE-SUFIJOS1.
