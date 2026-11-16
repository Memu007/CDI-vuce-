# Holanda→423: reproducción de la PM

Entrega `a910c5f` (informe `c6cb661` y `df935f5`, canal `PARA-PM-2.md`). Base `8d2cacc`. Producto:
`paises_maria.js` (sale `434 · HOLANDA`, `HOLANDA` → 423, `REEMPLAZOS = {"434":"423"}`),
`maria_generator.py` (`_reemplazos` y `codigo_de_pais`) y `despacho_lector.py` (pasa por
`codigo_de_pais`). Veredicto: **devolución sobre `a910c5f`**: el criterio 5 no se cumple (abajo).

## Corrido por la PM (2026-11-16, de 22:42:47 a 23:30:31 UTC)

| Qué | Resultado |
|---|---|
| `git diff --stat a910c5f origin/claude/dev-maria -- . ':!docs/pm'` | vacío |
| `chequeo-6.py 8d2cacc a910c5f` | producto +23/−18, arnés +117/−26, historia vacía, `avisos: 0`, como en el informe |
| grep de historia de §6 sobre `proyecto_maria/` | vacío |
| `anclas_perdidas.py a910c5f` | 103 guiones, 2553 anclas; perdidas 0, 0 y 0 |
| las tres pruebas del informe sobre `a910c5f` | `247 passed` |
| las mismas con el producto de `8d2cacc` | `4 failed, 243 passed`, los cuatro del informe |
| `test_despacho1b.py` | `285 passed` |
| `e2e_maria.sh` sobre el SHA (22:43:09) y sobre la unión con mi rama (22:43:26) | «E2E MARIA OK» los dos |
| `sabotaje_maria3.sh` (guion igual en mi rama y en la entrega) | 32 OK (22:46:51) |
| `sabotaje_maria1a.sh` desde un worktree de `a910c5f` | «OK: los 10 sabotajes dan rojo por la razón esperada» (22:58) |
| `sabotajes/catalogo3.sh` desde un worktree de `a910c5f` | `rc=0`, 65 `ROJO`, 0 «ROJO?» ni sin rojo, «fallas: 0» (23:30:31) |
| suite completa (sqlite, `ENVIRONMENT=test`, sin red) | `6197 passed, 110 skipped, 3 xfailed` en 18:15 (23:05:15); 0 líneas `FAILED` |
| `codigo_de_pais` sobre 4019 formas (000–999 con y sin 0, `0NNN`, nombres, alias, INDEC, en mayúscula, minúscula y título, y los números 434, 423, 310 y 434.0), producto de `8d2cacc` contra `a910c5f` | 6 distintas, todas Holanda: «0434», «434», «HOLANDA», «Holanda», «holanda» y el número 434, de 434 a 423 |

Error mío, corregido: la primera corrida de `sabotaje_maria1a.sh` salió de mi rama (`b2a53410`),
con el ancla vieja, y dio `rc=1` «PATRON NO ENCONTRADO»; la de `catalogo3.sh` también salió de mi
rama y la corté. Las dos se volvieron a correr desde un worktree de `a910c5f`. Regla que ya estaba:
un guion de sabotaje se corre con la copia del SHA que se revisa.

Negativos míos, en un archivo descartable: siete formas que no estaban en la familia de la Dev
pasan sobre `a910c5f` y cuatro dan rojo con el producto de `8d2cacc`. Sabotajes míos fuera del
guion: S1 `1 failed`, S2 `4 failed`.

Adversario de la PM (Opus, esfuerzo alto, contexto nuevo, sin red, `GEMINI_API_KEY` vacía,
lanzado a las 22:46): ningún TXT da 434 y pantalla y servidor coinciden. Encontró lo del
criterio 5 y el «4340» (D263).

## Criterio 5: lo que se muestra y lo que sale

Medido por la PM con la API del catálogo (`PUT /api/catalog/{vid}/productos/{key}` con un
`origen`, después `GET /api/catalog/{vid}` y la base):

| escrito | guardado y devuelto (la pantalla lo pone tal cual, `catalogo.js:270`) | TXT |
|---|---|---|
| `434` | 434 | 423 |
| `0434` | 0434 | 423 |
| `HOLANDA` | HOLANDA | 423 |
| `310` | 310 | 310 |
| `CHINA` | CHINA | 310 |

Que la pantalla repita lo escrito vale para todos los países, y un nombre («HOLANDA», como
«CHINA») muestra un nombre y saca un código: eso no es nuevo. Lo nuevo es una forma que lleva el
código reemplazado (434, 0434, «434 · HOLANDA»): se ve un código y el TXT dice otro. En la base,
434 se mostraba y salía 434. La diferencia la crea esta pieza, tiene camino hoy en el catálogo
(escribirlo, o un 434 ya guardado que el lookup trae a la grilla de ítems) y el informe dice que el
criterio 5 no se cumple. Es devolución, no una lectura más angosta del criterio. Los demás lugares
(`default_origin`, el «Origen frecuente») no vuelven a la generación según el informe: la vuelta
dice, lugar por lugar, si lo que muestra llega a un TXT. Relabelar todos los países (D261 (a)) es
otra cosa y la decide Emi.

## Las D

- **D261**, decidido por la PM: la parte de 434 (ningún lugar muestra un código reemplazado) es
  la devolución; mostrar todos los países con su etiqueta va a Emi con recomendación, aparte.
- **D262 (a)**, decidido por la PM: `_reemplazos` es la tercera lectura de una constante de
  `paises_maria.js`; a la cola de limpieza.
- **D263**, de la PM: `validate_items_for_maria` mira `origen` y el generador usa `pais_origen`
  primero. Medido en el generador: `pais_origen="4340"` con `origen="CN"` valida sin errores y
  sale `CARTPAYORI=4340`. Camino hoy: la API (`MariaRequest.items` es una lista libre); la
  pantalla no manda `pais_origen`. Ya estaba en la base. Pieza chica, después de D239 (a).

## Supuestos y riesgos

- **Supuestos 1 a 3:** aceptados.
- **La premisa del criterio 4 no se cumplía:** verificado; en `8d2cacc` el único caso de «mismo
  origen» era el de CN y US. Bien que lo dijera en lugar de inventar algo que re-apuntar.
- **`/security-review`** cubrió `8d2cacc..a910c5f`, el producto entregado.

**No corrido por la PM:** `/security-review` propio; lo nuevo mirado en el navegador.
