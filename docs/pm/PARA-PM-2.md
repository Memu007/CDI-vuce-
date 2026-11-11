# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## El armado para la PR no entra limpio: frené (D166)

No hay SHA de armado. `git cherry-pick d497551` sobre tu cabeza `c9886d2`
choca en `CHANGELOG.md` y sólo ahí. No lo resolví a mano para entregar.

```
Auto-merging CHANGELOG.md
CONFLICT (content): Merge conflict in CHANGELOG.md
Auto-merging proyecto_maria/services/client_memory.py
error: could not apply d497551... fix: la posición SIM con la letra separada por un espacio alimenta la memoria del cliente
exit=1
```

**Por qué choca.** `d497551` suma 4 líneas a `CHANGELOG.md` justo debajo de
`---`, pegadas a 58 líneas de entradas que tu rama no tiene (CATALOGO-3,
PRESUPUESTO-CLIENTE-1, D102, D139, ORG-1, OBSERVABILIDAD-1, AVISOS-2b,
RESET-3). Git no encuentra dónde apoyarlas.

Los otros tres commits y la parte de código de `d497551` entran solos.

## Decisiones

**D166. Cómo armo el SHA.** Probé las dos primeras en un checkout aparte,
con commits locales que ya borré (no subí ninguno).

- (a) Me autorizás a resolver ese conflicto: tu `CHANGELOG.md` más sólo las
  4 líneas de MEMORIA-E2E arriba de NOMBRES-1. Probado: los cuatro commits
  entran, `git diff c9886d2 <SHA> -- CHANGELOG.md` da +4/−0 y el resto del
  árbol es igual al de (b). **Tu paso 3 vuelve a chocar** en `CHANGELOG.md`
  al traerlo a mi rama (corrido con `git merge-tree`: `CONFLICT (content)`,
  sólo ese archivo). Lo resolvería dejando mi `CHANGELOG.md`, que ya tiene la
  entrada. Son dos resoluciones a mano, las dos de texto en ese archivo.
- (b) El armado sin las 4 líneas de `CHANGELOG.md` en el primer commit.
  Probado: ninguna resolución a mano; `git merge-tree` en mi rama da limpio y
  el árbol resultante es idéntico a mi cabeza (`3ee0fba…` los dos). Costo: tu
  PR lleva un cambio de producto sin su línea de CHANGELOG hasta que integres
  el resto de mi rama, que la trae.
- (c) Integrás antes las piezas de MARIA que le faltan a tu rama y rehago el
  armado sobre esa cabeza.

Recomiendo **(a)**: la PR sale con su línea de CHANGELOG (`CLAUDE.md` §5) y
lo que resuelvo a mano se comprueba con un `git diff` de un archivo de texto.
Si preferís cero manos, (b) ya está probada.

En las tres, `git log c9886d2..<SHA>` da cuatro commits con SHAs nuevos, no
`d497551 9be52ef 195af11 f186ecf`: es un cherry-pick.

## Lo que corrí sobre tu cabeza, sin commit

Árbol: `c9886d2` + el código de `d497551` (sin `CHANGELOG.md`) + los tres
commits de pruebas. Es el contenido de (b). No es un SHA.

| qué | salida |
|---|---|
| `tests/test_memoria_pantalla.py tests/test_guardar1.py` | `======================== 32 passed, 5 warnings in 5.95s ========================`, `exit=0` |
| `scripts/testing/e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.`, `exit=0` |

**No corrido:** nada sobre un SHA de armado, porque no existe. Sobre el árbol
de (a) no corrí pruebas: difiere del de (b) sólo en `CHANGELOG.md`.

## Un dato que cambia lo que integrás

A tu rama no le falta sólo PRESUPUESTO-CLIENTE-1.
`git log --oneline --no-merges c9886d2..f186ecf | wc -l` da **105**, y
`git diff --shortstat c9886d2 f186ecf -- proyecto_maria` da
`14 files changed, 402 insertions(+), 202 deletions(-)`. Ahí están RESET-3,
AVISOS-2b, SMOKE-1, OBSERVABILIDAD-1, ORG-1, D139, D102, CATALOGO-3,
PRUEBA-LIMPIAR-1 y PRESUPUESTO-CLIENTE-1. `3d0083a` (RESET-3) no es ancestro
de `c9886d2`. No sé por qué: te lo paso como dato.

Consecuencia para el armado: su `client_memory.py` no es el de `f186ecf`.
Lleva sólo el cambio de la regex sobre tu versión del archivo (sin
CATALOGO-3). Las pruebas de arriba pasan sobre esa combinación.

## Comandos

```bash
git worktree add /tmp/armado c9886d2 && cd /tmp/armado
git cherry-pick d497551                    # CONFLICT (content): Merge conflict in CHANGELOG.md
git status --short                         # UU CHANGELOG.md / M  proyecto_maria/services/client_memory.py
git cherry-pick --abort
git diff --shortstat c9886d2 d497551~1 -- CHANGELOG.md   # 1 file changed, 58 insertions(+)
git show --stat --format= d497551 -- CHANGELOG.md        # CHANGELOG.md | 4 ++++
```

## PRESUPUESTO-CLIENTE-1

No entregada. En mi rama está `3936c24` (casos y arnés PG al día con la
unión) y el merge de tu rama `0f146f2`. Sobre `3936c24`:
`tests/test_datos1.py` 11 passed y, con el arreglo revertido,
`2 failed, 9 passed`; arnés PG16 `fallas: 0` y revertido `fallas: 2`;
`datos1.sh` 21 rojos, `sabotajes sin rojo: 0`. Faltan el adversario,
`/code-review`, `/security-review` y las puertas sobre el SHA que entregue.
Mientras contestás D166 sigo con esas revisiones; el armado va primero
apenas respondas.
