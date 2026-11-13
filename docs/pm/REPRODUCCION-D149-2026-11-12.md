# Reproducción de D149 (a) + CR8 + ids de pytest (2026-11-12, PM principal)

Entrega de MARIA: arnés `48195cfe`, informe `46959d76` (rama
`claude/dev-maria`). Sólo pruebas: producto **+0/−0**.

**Estado: aceptada sobre `48195cfe` e integrada** con `merge` de `46959d76`,
no de la cabeza de la rama. D168 (b), decidida por la PM. D169 (a): la suma
la Técnica, con su caso dando `PIERDE` en `832bf74` y `NO PIERDE` en
`48195cfe`. Los cuatro guiones cortos de `f2709a2`, que estaban integrados
sin aceptar, quedan aceptados con esta pieza.

Corrido con el venv de la PM, sin red y con `GEMINI_API_KEY` vacía. Los
guiones toman el repositorio del directorio actual, así que corrí copias de
los suyos sobre el SHA (cada uno arma su propio worktree).

## Lo corrido

| Qué | SHA | Resultado |
|---|---|---|
| `chequeo-6` | `b558b66..48195cfe` | igual al informe: producto +0/−0, historia vacía |
| `catalogolargo1.sh` | `48195cfe` | 11 `ROJO`, `fallas: 0`, rc=0, 88 s |
| `datos1.sh` (los tres de CR8, ahora en código) | `48195cfe` | 20 `ROJO`, `sabotajes sin rojo: 0`, rc=0, 231 s |
| `disco1.sh` (ids explícitos) | `48195cfe` | 46 `ROJO`, `sabotajes sin rojo: 0`, rc=0, 395 s |
| `maria1b.sh` | `48195cfe` | 34 `ROJO`, `sabotajes con falla: 0`, rc=0, 522 s |
| `foco_perfil.sh` con el caso `pantalla_sesion1.js·#pfEmail` (copia fuera del repo) | `832bf74` | `PIERDE`: «lo escrito cayó en «Mi CUIT»» |
| lo mismo | `48195cfe` | `NO PIERDE` |
| `tests/test_despacho1b.py` natural | `48195cfe` | `285 passed`, tres veces |
| Sabotaje de `4292e0f` (`_DemasiadoTrabajo(Exception)`), sólo los dos casos de la hoja cara | `48195cfe` | `2 failed` en 15 de 15 corridas |

## Negativos de la PM

- **Todos los `no_debe` de `despacho1b.sh` nombran un caso real.** Un script
  mío expande las variables del guion (la más larga primero) y compara cada
  argumento con los 285 ids que junta pytest (`--collect-only -qq`):
  «argumentos de `no_debe`: 29; sin caso real: 0», rc=0. Control: con un
  argumento inventado (`[CERO]`) da 1 sin caso y rc=1.
- **El `no_debe` nuevo distingue los dos lados.** Con una salida guardada que
  nombra un caso que pasa sólo dentro de la advertencia de pytest
  («Event loop is closed», de aiosqlite), el viejo (`c4a1ecb`) da `ANCHO` y el
  nuevo calla. Con un `FAILED` real de ese caso, el nuevo da `ANCHO`.
- **La familia de `no_debe` suelto existe sólo en `despacho1b.sh`** (grep en
  `scripts/testing/sabotajes/` y `sabotaje_*.sh`).
- **«Valen igual»:** `app_v2.js` en `cc8b834b` es ancestro de `54ba001`, y
  `maria1b`, `entradas1`, `abuso1` y `cobro_mp2` no tocan `static/v2` ni el
  arnés de pantalla. Por eso sus corridas sobre `ab5b08c` valen para la
  entrega.

## Supuestos de ella (8)

Aceptados los ocho. El 6 lo cubre mi `catalogolargo1`, el 7 mi
`foco_perfil.sh` y el 8 mis 285 `passed` y el sabotaje de `4292e0f`. Los 3 y
4 cambian `sesion1.sh`, que no corrí: se apoyan en la corrida de ella sobre
`54ba001` (39 `ROJO`, `sabotajes sin rojo: 0`). El 5 se apoya en su
`despacho1b` entero. El 1 y el 2 son de forma.

## D168: fuera de CR8

CR8 era «tres sabotajes viejos anclan en comentarios: va con D149»
(`REPRODUCCION-PRESUPUESTO-CLIENTE-1-2026-11-11.md`), y los tres eran de
`datos1`; quedaron en código. Las siete anclas que marcó `/code-review`
(`sesion1.sh`, `despacho1b.sh`, `cobro_mp2.sh`) no las tocó esta pieza y son
parte de una familia de los dos Devs. Va a `COLA-LIMPIEZA.md` como una sola
entrada, con el grep para encontrarla y no con la lista: la paga cada Dev
cuando vuelve a tocar el guion.

## No corrido por la PM

- `despacho1b.sh`, `sesion1.sh` (supuestos 3 y 4), `entradas1.sh` y
  `abuso1.sh` enteros. Vale
  la corrida entera limpia de despacho1b de ella (136 `ROJO`, sale 0,
  8202 s), que es una sola.
- `cobro_mp2.sh` entero: ni ella (corrió una copia reducida) ni yo.
- El rojo viejo de `disco1` sobre la base (el de los ids con pytest 9.2.0).
- La suite completa (la última de ella, sobre `f36cc83` con pytest 9.1.1).
- `e2e_maria.sh`: producto +0/−0, no corresponde.
- Ella no corrió `/code-review` de nuevo sobre `4292e0f` ni `48195cf`.

## Riesgos que quedan

- Los ids de otros cuatro casos largos suyos todavía dependen de la versión
  de pytest; hoy ningún patrón los nombra.
- `pantalla_sesion1.js` depende de que el foco caiga en «Mi CUIT»: si se
  arregla `profile.js` (cola), ese arnés cambia en el mismo commit.
- La advertencia de aiosqlite ensucia la salida de pytest; no rompe nada hoy.
- Hipótesis de la revisión sobre el `finally` de `_tope_de_cpu`: es producto
  y sería una pieza aparte; no reproducida.

## D169 (la Técnica, 2026-11-12 13:47 UTC)

`foco_perfil.sh` de `117c1d16` (informe `027f5257`), con el caso
`pantalla_sesion1.js·#pfEmail`: `832bf74` `PIERDE` («lo escrito cayó en «Mi
CUIT»», rc=1); `48195cfe` y `57faa844` (mi rama con D149 y K) `NO PIERDE`,
rc=0. Los dos casos de `pantalla_estudio1` dan `NO PIERDE` en los tres. La
Técnica marcó que mi puerta original («`NO PIERDE` sobre HEAD») no se podía
cumplir antes de integrar D149: tenía razón.
