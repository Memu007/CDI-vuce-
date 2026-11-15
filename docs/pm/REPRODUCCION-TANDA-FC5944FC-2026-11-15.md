# Tanda de sabotajes sobre `fc5944fc` (candidato a publicar), 2026-11-15

Escrita por la PM principal a las 16:11 UTC.

## Qué se corrió

- **Candidato:** `fc5944fc`. Frente a lo publicado (`7436c6e5`; `main` = `f734fbb3`, que sólo
  suma documentos), el producto cambia en `maria_generator.py`, `main.py`, `paises_maria.js` y
  `finalize.js`: SUFIJO-BORRADOR, PAIS-NL y CUIT-GENERAR. No hay migración de esquema.
  `git merge-tree` de `origin/main` con `fc5944fc` no da conflictos.
- **Ya corrido antes sobre `fc5944fc`:** la suite (6151 passed, 110 skipped, 3 xfailed) y
  `e2e_maria.sh` en verde.
- **La tanda:** 87 guiones de sabotaje, los que tocan lo que cambió desde `7436c6e5`. Corrieron
  en segundo plano entre el 14/11 14:21 y el 15/11 14:03 UTC, en un worktree con 0 cambios.
  La máquina se reinició dos veces y la tanda se retomó desde el guion que había quedado a
  medias. El registro está en el scratchpad de la PM (`tanda2/resumen.txt`).
- La cabeza de la rama de PM sólo agrega pruebas y arnés de MARIA-8 sobre `fc5944fc`.
  `git diff fc5944fc HEAD` fuera de `docs/pm`, `.claude` y `AGENTS.md` toca sólo
  `tests/test_maria8_subitems_por_posicion.py` y `scripts/testing/sabotaje_maria8.sh`.

## Resultado

83 de 87 guiones dieron `rc=0`. Los cuatro que no:

| Guion | En la tanda | Solo, sin carga | Causa |
|---|---|---|---|
| `sabotajes/despacho1b.sh` | `rc=124` al tope de 3600 s, con 67 de 132 en `ROJO` | `rc=0` en 7080 s: 136 `ROJO` (Postgres incluido), «sabotajes sin rojo: 0» | Es largo: 132 sabotajes a unos 53 s cada uno. No se trabó. |
| `sabotajes/aislamiento2.sh` | `rc=5` | sin vigía, `rc=16`; con vigía que mata el Postgres suelto, `rc=0` en 249 s: 28 `ROJO`, 2 controles `VERDE`, 18 Postgres sueltos muertos | Defecto del arnés, ya en la cola de limpieza: `limpiar()` corre `pg_ctl stop` como root, no lo apaga, y el siguiente ataque no levanta el suyo en 5434. |
| `sabotaje_org1.sh` | `rc=1`: `contar_antes` quedó verde una vez | la prueba sola, 8 de 8 en rojo; el archivo, 4 de 4 | Carrera del arnés, por lectura del código (el verde no se volvió a ver: 12 de 12 en rojo): la barrera de `_carrera` (`tests/test_org1.py:404`) alinea los dos registros después del hash. Si uno cuenta, gasta y confirma antes de que el otro cuente, el sabotaje queda verde. En esa zona el producto es igual a `7436c6e5`, donde dio `rc=0`. Va a la cola de limpieza. |
| `sabotajes/rendimiento1b.sh` | `rc=1`: un `ROJO?` por salida 137 (sin memoria) en «el vendedor vuelve a leer con pdfminer» | sobre `7436c6e5` dio la misma salida 137, también solo | Hallazgo conocido del guion: la pieza para la Técnica espera a Emi. Los otros seis sabotajes del guion dan `ROJO`. |

`cobro_corte1` (3897 s), `cobro_mp1` (3617 s) y `cobro_mp2` (8934 s, 87 `ROJO`, 0 `FALLA`)
dieron `rc=0`.

## Las demás puertas (16:20 UTC)

- `anclas_perdidas.py fc5944fc`: 103 guiones, 2509 anclas presentes, 0 perdidas. Hay 5 sin
  medir (en 2 guiones) y 6 sin ancla (en 1), los mismos tipos ya conocidos.
- **Paso 2 de «Publicar»:** `main` fusionado sobre `fc5944fc` en una copia local da `e42f0084`,
  con árbol idéntico al de `fc5944fc` (`git diff fc5944fc e42f0084` vacío).
- Frente a `7436c6e5` no hay migración de esquema, variables nuevas, `.env` ni claves.
- La CI corre en el pull request.

## Conclusión de la PM

Ningún sabotaje sobrevivió por el producto: ninguna protección de lo que cambió quedó sin
prueba. Los cuatro rojos son del arnés o del tope de tiempo de la tanda:
`despacho1b` y `aislamiento2` dieron verde solos, y el verde de `org1` no se volvió a ver. Por la tanda, `fc5944fc` queda listo para pedir el «dale» de Emi.
