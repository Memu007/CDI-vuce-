# Reproducción de PA-1 y D3 — 2026-10-24

PM principal. Entrega de la Dev técnica: informe `31719c3` (rama
`claude/dev-tecnica`), puertas sobre `a114465`. Base: `c402bcb` (PA-1) y
`bdd5fb3` (D3). Producto: `git diff c402bcb 31719c3 -- . ':!docs'`.

**Veredicto: aceptada**, incluido el supuesto de la fecha a medias
(`d8e084c`). Integrada a la rama de la PM con `merge` de `913d282` (`fe41228`); lo que sigue a
`31719c3` son sólo notas de su canal.

## Lo corrido

Worktrees descartables en `31719c3`, API con SQLite nueva, sin terceros.

| Qué | Resultado |
|---|---|
| Focales `tests/test_pa1_textos.py` y `tests/test_clientes_crud.py` | `65 passed` |
| Suite completa, `--no-cov --timeout=120` | `1782 passed, 102 skipped, 2 xfailed`, exit 0 (igual que la Dev) |
| Sabotajes `pa1.sh 31719c3` | 27 `ROJO`, `sabotajes sin rojo: 0` |
| Sabotajes `cliente1.sh 31719c3` | 22 `ROJO` y 1 `ROJO?`: «lo recordado de una edición pasa al alta» dio rojo por otro motivo («el aviso dice que falta el CUIT, y se cargó») |
| Lo mismo, con la prueba esperando el foco en `#cfNombre` antes de llenar | 23 `ROJO`, `sabotajes sin rojo: 0`, exit 0: el sabotaje da su propio rojo |
| Adversario Sonnet alto, contexto nuevo, sobre D3 en navegador | núcleo de D3 sin hallazgo; 3 puntos fuera de D3 (abajo) |
| e2e de la CI | **no corrida por la PM**; la Dev vio un rojo intermitente en `#validatingRerun` (abajo) |

## El `ROJO?` de `cliente1.sh`

No es de D3: es la carrera del foco que ya está en PRUEBAS-1 (a).
`openForm()` enfoca `#cfNombre` con `setTimeout(..., 80)`; si cae entre el
foco y la escritura de `page.fill('#cfCuit', …)`, el CUIT se escribe en el
nombre. Con la espera de la condición observable
(`document.activeElement.id === 'cfNombre'`) en las cinco aperturas del
formulario, la corrida completa da cada rojo por su motivo.

## Del adversario

| # | Hallazgo | Reproducido | Qué se hace |
|---|---|---|---|
| 1 | Un año de 5 cifras (`20150`) se guarda cortado a 10 caracteres (`20150-01-0`): `update_cliente` hace `[:10]` sin validar. El campo lo muestra vacío y, con D3, se conserva sin aviso | por el adversario en navegador; la PM leyó el `[:10]` en `main.py` | anterior a D3; va a CLIENTE-1b (validar en el alta **y** en la edición) |
| 2 | Una fecha conservada que no sirve (`2015-02-30`, `20150-01-0`) no se avisa | por el adversario | es lo pedido en D3; CLIENTE-1b corta la entrada y lista lo ya guardado |
| 3 | La respuesta de un guardado en vuelo cierra el formulario de otro cliente abierto después (sin mandar nada de uno al otro) | por el adversario, con la red demorada | anterior a D3; riesgo anotado, no se pide |

## e2e: el rojo intermitente de `#validatingRerun`

La Dev lo vio una vez sobre `d1f7833` (`Node is either not clickable or not
an Element` en `config/e2e_maria.js:202`) y dio OK en las demás corridas.
PA-1 no toca ese botón ni la pantalla Validar más allá de un texto. Sin
causa todavía: va a PRUEBAS-1 (c).
