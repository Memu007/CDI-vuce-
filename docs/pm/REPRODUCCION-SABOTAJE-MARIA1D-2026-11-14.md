# Vencido `sabotaje_maria1d.sh`: reproducción de la PM

Entrega `6e4e658` (informe `38a7ed2`, canal `PARA-PM-2.md`). Base `8f50af3`. Sólo
arnés: `scripts/testing/sabotaje_maria1d.sh` +4/−4 y una línea menos en
`docs/pm/herramientas/sabotajes-conocidos.txt`. Las anclas de los casos 4 y 8 de
`main.py` vuelven a encontrarse, cada una sin contexto de más. Veredicto: **aceptado
sobre `6e4e658`**.

## Corrido por la PM (2026-11-14, entre 08:12 y 08:18 UTC, worktrees descartables)

SQLite, `ENVIRONMENT=test` y los modos falsos. El guion exporta `GEMINI_API_KEY=test-key`
y pisa lo que se le pase (previo, no del diff). Corrió superpuesto con `run6` y `d1b`.

| Qué | Resultado |
|---|---|
| `chequeo-6.py 8f50af39 6e4e6583` | producto +0/−0, arnés +4/−4, historia vacía, `avisos: 0` |
| unión `6e4e6583..38a7ed2b`: fuera de `docs/pm` y en `docs/pm/herramientas` | vacía las dos |
| copia del guion de `6e4e6583` | `48 passed` sin sabotaje; 8 `ROJO`, 0 `FALLA`, `rc=0`; caso 4 `2 failed`, caso 8 `8 failed` |
| `anclas_perdidas` sobre `6e4e6583` | de una línea 4 (guiones 3), de varias 0; antes 5 y 1. `maria1d` no aparece en el detalle; «otra cantidad 2» es `valor1b` (vencido conocido) |
| `sabotajes-conocidos.txt` de `6e4e6583` | 5 `vencido`, ninguno `maria1d` |
| ancla vieja del caso 8 en `main.py` de `6e4e6583` | 0 veces; la nueva, 1 (`main.py:5008`) |
| caso 4 | cae en `_supuestos_maria` (`main.py:4883`), que llaman `4992` y `5223` |

Negativos de la PM, con copias del guion:

| Copia | Resultado |
|---|---|
| el guion de `8f50af3` sobre `6e4e6583` | `PATRON NO ENCONTRADO (0 veces)` en el caso 4, `rc=1` (corta ahí por `set -e`; el 8 lo mide la fila de arriba) |
| el caso 8 sacando `kit_warnings` en vez de la procedencia | `FALLA procedencia_rara_sin_aviso: quedó verde`, `rc=1` |

El segundo probó sólo `kit_warnings`; no dice nada de `avisos_ncm` ni `avisos_valor`.

## Decisiones

- Supuesto 1 (anclas achicadas a lo que el sabotaje saca): aceptado.
- El SHA final pasó por un adversario: la línea de D248 quedó cumplida.
- No hay D nueva: la próxima sigue siendo D250. Subpieza: `ROADMAP.md` no cambia.

## Riesgos (todos previos, ninguno del diff)

1. La prueba del caso 4 también cae con los casos 1 y 3.
2. `caso` mira el nombre de la prueba en `FAILED`, no el motivo.
3. El caso 4 no ve el camino de los avisos previos; lo ven `test_maria3` y `test_maria5`
   (medido por la Dev: `4 failed, 1169 passed`).

## No corrido

- Suite entera y e2e_maria.sh: sin cambio de producto.
- Subagentes adversariales de la PM: arnés sin dinero, sesión ni datos.
- Un negativo propio sobre el caso 4.
