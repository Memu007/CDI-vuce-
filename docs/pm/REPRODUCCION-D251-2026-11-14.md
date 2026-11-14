# D251 (a): reproducción de la PM

Entrega `9d580db` (informe `7a3c594`, canal `PARA-PM-2.md`). Base `01bc9df`. Sólo arnés:
`tests/test_maria8_subitems_por_posicion.py` (de 61 a 77 pruebas; `JUNTOS` con 5 datos y
`MISMO_SUFIJO` con 28) y `scripts/testing/sabotaje_maria8.sh` (de 39 a 43 sabotajes).
Veredicto: **aceptada sobre `9d580db`**.

## Corrido por la PM (2026-11-14, entre 17:32 y 17:39 UTC)

Las corridas se superpusieron con `run9c` de fondo (tanda de sabotajes sobre `fc5944fc`).

| Qué | Resultado |
|---|---|
| `chequeo-6.py 01bc9df 9d580db` | producto +0/−0, arnés +78/−14, historia vacía, `avisos: 0` |
| `2fb54d0..9d580db` fuera de `docs` y `.claude` | sólo los dos archivos de arriba |
| `9d580db..origin/claude/dev-maria` fuera de `docs/pm` | vacío; la Dev sólo tocó `PARA-PM-2.md` |
| copia del guion de `9d580db` | `77 passed` sin sabotaje; 43 `ROJO`, 0 `FALLA`, «OK: los 43 sabotajes dan rojo por la razón esperada», `rc=0`; los 40 a 43 dan `3 failed`, `3 failed`, `1 failed` y `14 failed`, como en el informe |
| guion de `01bc9df` sobre `9d580db` | 39 `ROJO`, 0 `FALLA`, «OK: los 39 sabotajes…», `rc=0`: nada de lo viejo se rompió |
| `anclas_perdidas.py 9d580db` | 103 guiones, 2514 anclas, 11 sin medir; 0, 0 y 0 |

Negativos míos, en un worktree de `9d580db`, con `python -B` y sin `.pyc`. Cada cambio se
midió con la prueba de `9d580db` y con la de `01bc9df` (`77 passed` y `61 passed` sin cambio):

| Cambio en `maria_generator.py` | prueba de `9d580db` | prueba de `01bc9df` |
|---|---|---|
| `:2225` los renglones del aviso, al revés (`sorted(ns, reverse=True)`) | `33 failed, 44 passed` | `17 failed, 44 passed` |
| para el mismo sufijo manda el de la operación sobre el propio del renglón | `26 failed, 51 passed` | `9 failed, 52 passed` |
| `:2225` `_enumerar(list(range(ns[0] + 1, ns[0] + 1 + len(ns))))`: el primero y la cantidad | `3 failed, 74 passed` | `61 passed` |

Los dos primeros ya daban rojo con la prueba vieja: cuidan que nada se rompa, no la pieza. El
tercero es de la familia de D251 (salteados), verde con la prueba vieja y rojo con la nueva, y
no está en la tabla del informe (su sabotaje 40 usa `ns[-1] + 2`; su fila 54 cambia `:2230`).

## Las D

- **D252 (a)**, decidida por la PM: pieza chica, con criterio en `PARA-DEV-2.md`. El aviso de
  cada renglón le dice al despachante qué producto corregir: un número equivocado lo manda al
  producto equivocado.
- **D253 (a)**, decidida por la PM: límite escrito. `juntos[:3]`, `ns[:12]` y
  `min(len(ns), 12)` quedan en verde porque los datos están en el tope; a un tope inventado
  siempre se le puede poner otro más alto que la prueba.
- **D254 (a)**, decidida por la PM: límite escrito. Las filas 46 a 51 agregan condiciones
  inventadas; el error que alguien cometería (el aviso adentro del `try` del otro) da rojo.

## Supuestos y riesgos

Supuestos 1 a 7 y riesgos 1 a 5 aceptados. El riesgo 6 (renglón contra ítem en el texto) es
una pregunta para el despachante, no una pieza: queda sólo en esta acta, y va a Emi si
consulta al despachante por otra cosa.

## Lo que se arregla en documentos de la PM

- `.claude/skills/entregar/SKILL.md`: dice que `/code-review` corre otra vez si después hay
  commits.
- `docs/pm/COLA-LIMPIEZA.md`: las líneas de los literales y del `echo` nombran la prueba y
  el número de hoy.
- `docs/pm/NOW.md`: la línea `/compact conservar` deja de decir a la vez «cerradas» y «al FIN».
