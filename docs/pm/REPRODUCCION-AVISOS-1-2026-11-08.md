# Reproducción de AVISOS-1, 2026-11-08

Entrega de la Dev MARIA: producto y pruebas en `0aed334` (producto `7a2961f`,
`d7345fa`, `efb9c07`, `cec3564`), informe en `3deff12`, base `e6adea1`.
Corrido por la PM desde un worktree de `0aed334`, venv Python 3.12 primero en
el `PATH`, sin red y con `GEMINI_API_KEY` vacía.

## Resultado

**Aceptada sobre `0aed334`, sin integrar.** Igual al informe salvo el número
de casos, que es mayor (abajo).

| Qué | Salida |
|---|---|
| `chequeo-6.py e6adea1 0aed334` | `producto +54/−16`, arnés `+331/−8`, historia vacía, 3 avisos, los tres explicados en el informe (igual) |
| pytest de las seis suites del informe | `256 passed`, salida 0 |
| `sabotajes/avisos1.sh 0aed334` | `BASE 149 passed`, 22 `ROJO`, «sabotajes sin rojo: 0», salida 0 |
| `sabotajes/seguro2.sh 0aed334` | `BASE 78 passed`, 19 `ROJO`, «sabotajes sin rojo: 0», salida 0 |

El informe dice `199 passed` para las seis suites; en `0aed334` se juntan
256 casos (72 + 60 + 17 + 25 + 52 + 30, con `--collect-only` por archivo) y
pasan todos. El número del informe quedó de una corrida anterior; no cambia
el veredicto.

La suite completa no la repetí: la Dev la corrió dos veces (5345 passed, la
segunda como la CI).

Los avisos de chequeo-6 quedan como los explica la Dev: 38 netas por el
predicado, el texto y la marca; el comentario de 3 líneas reescribe uno de 4;
la función de más de 150 es la IIFE del módulo y lo nuevo va aparte.

## Adversario Sonnet alto

Sin altos ni medios.

- Ninguna importación legítima frenada: `IC04` en cualquier caja y con
  espacios, `IC01`, `IC03`, `IC05`, `IT01`, `TR01`, `ZFI1`, `TRAN`, vacío,
  `None`.
- Ninguna exportación que todavía genere: 400 con espacio, guion, nulo,
  U+200B, U+00AD, U+FEFF, U+3164, U+2028, U+0085, U+202E, U+034F, U+E0045,
  ancho completo, `ⓔⓒ01`, `𝐄𝐂01`. Una sola llamada a `generate_maria_txt`;
  el Excel no lee la destinación.
- `seguro_borrado: true` del cliente sólo elige el texto; no cambia el TXT
  ni salta un freno.
- Ningún 500: tipos raros dan 422.

Bajas:

1. `es_exportacion` normaliza el texto entero: 2 millones de caracteres
   tardan unos 5 s y traban el proceso (con sesión). Antes eran 8 ms.
   Recortar antes de normalizar.
2. Con el seguro borrado y de vuelta a FOB, el 400 dice «al pasar a un
   incoterm que ya lo lleva en el precio»; la nota de la pantalla sí lo
   distingue. Leído del código, no reproducido.
3. Fuera de alcance: `/generate_maria_export` acepta `IC04` o `TRAN` y los
   pone en un TXT de exportación.

`ᴇC01` (versalita) pasa como importación con `ISTA=ᴇC01`: es de la familia
de homoglifos que la Dev ya declaró y que cierra la D130.

No corrido: navegador real (`marcarEnLaRevision`), Postgres, producción.
