# D257 (b): reproducción de la PM

Entrega `3c7eb14` (informe `38cb92f`, canal `PARA-PM-2.md`). Base `e1bd17a`. Sólo arnés:
`tests/test_maria8_subitems_por_posicion.py` (de 83 a 85 pruebas: dos datos nuevos en
`SE_LIMPIO`) y `scripts/testing/sabotaje_maria8.sh` (de 63 a 70 sabotajes). Veredicto:
**aceptada sobre `3c7eb14`**.

## Corrido por la PM (2026-11-15, entre 05:46 y 05:56 UTC)

Con `run9c` de fondo (tanda de sabotajes sobre `fc5944fc`).

| Qué | Resultado |
|---|---|
| `chequeo-6.py e1bd17a 3c7eb14` | producto +0/−0, arnés +49/−12, historia vacía, `avisos: 0`, como en el informe |
| `3c7eb14..38cb92f` fuera de `docs/pm` | vacío; adentro, la Dev sólo tocó `PARA-PM-2.md` (lo demás es mi `b71f2e9`, integrado) |
| `grep -c '^caso '` en el guion de `3c7eb14` | 70 |
| copia del guion de `3c7eb14` | `85 passed` sin sabotaje; 70 `ROJO`, 0 `FALLA`, «OK: los 70 sabotajes dan rojo por la razón esperada», `rc=0`; los siete nuevos dan `1 failed, 84 passed`, como en el informe |
| `anclas_perdidas.py 3c7eb14` | 103 guiones, 2541 anclas, 11 sin medir; perdidas 0, 0 y 0 |

Negativos míos, en un worktree de `3c7eb14`, con `python -B` y sin `.pyc`. Cada cambio se
midió con la prueba de `3c7eb14` y con la de `e1bd17a` (`85 passed` y `83 passed` sin cambio):

| Cambio en `proyecto_maria/core/maria_generator.py` | prueba de `3c7eb14` | prueba de `e1bd17a` |
|---|---|---|
| sufijos `:2211`: `grupos.add(gid)` → `grupos.clear(); grupos.add(gid)` | `1 failed, 84 passed` (`[dos_grupos]`) | `83 passed` |
| arancel `:1964`: el `elif` del grupo pide además `item.get("sufijo")` | `1 failed, 84 passed` (`[un_grupo_sin_el_suyo]`) | `83 passed` |

El primero ataca el segundo grupo del lado de los sufijos (un grupo que vuelve a avisar); el
segundo, el grupo sin sufijo propio del lado del arancel (cae como «renglón N»). Ninguno está en
el guion; su M23 (el `grupos.clear()` del arancel) es el espejo del primero.

## La premisa del punto 2

Corrección de la Dev, aceptada (medido por ella, no por la PM): con el sufijo de operación de
siempre (`AA(X.0)-AI(Y)-`, que trae AI) un grupo que lo usa no tiene aviso de arancel, y la fila 55
daba `85 passed`. Por eso `un_grupo_sin_el_suyo` trae su propio sufijo de operación sin AI. El
error era de mi criterio.

## Las D

- **D258 (a)**, decidida por la PM: línea para la cola de limpieza. «Un aviso por grupo» está
  escrito dos veces en el generador (arancel y avisos de sufijo, cada uno con su conjunto
  `grupos`, y el cuidado del `TypeError` sólo en el segundo). Es producto; va después.

## Supuestos y riesgos

- **Supuestos 1 a 4:** aceptados. El 4 (no recortar 59 a 63) era optativo.
- **Riesgo 1** (la falta del código AI modelada sólo para grupos; daría un rojo visible, no un
  verde falso) y **riesgo 3** (el orden del arancel entre grupos sin sabotaje): aceptados.
- **Riesgo 2** (el endpoint, `main.py:5127`, sin caso de un grupo sin sufijo propio): riesgo
  escrito, decidido por la PM. Medido: con el sabotaje 67 puesto,
  `tests/test_maria9_sufijo_operacion.py` da `27 passed` (no corrí más archivos). El endpoint usa
  `usa_el_sufijo_de_la_operacion` para pedir el sufijo general; si fallara para un grupo, el
  generador igual corta con «Falta el sufijo de valor SBT (CSBTSVL)» (`maria_generator.py:1729`,
  independiente de esa función): se pierde un 400 claro, no sale un TXT sin sufijo.
- **Riesgo 4** (el guion tarda unos 10 minutos): aceptado.
- **`test_despacho1b`:** sigue abierto en la PM; no frena D257.

## Lo que se arregla en documentos de la PM

- `docs/pm/COLA-LIMPIEZA.md`: el «hoy `63`» pasa a 70, «44 a 63» a «44 a 70», y entra la línea
  de D258.
