# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SEPARADORES-1b-LIMPIEZA: el caso de la pista en contra distingue la regla sin_grupo

| SHA | qué |
|---|---|
| `d8383df2` | base (tu merge, AUTOREMOVE-PG aceptada) |
| `bb0d3347` | `test:` el caso unido y las dos anclas de `sabotaje_separadores1b.sh` |
| este commit | `docs:` informe |

**Nada para decidir.** Producto +0/−0. Sin adversarios ni `/code-review`, como pedía la tarea.

### Qué hice: unir los dos casos, con la familia como datos

- `FAMILIA` pasó a pares `(texto, pista en contra)`. Tiene las 4 entradas de antes, sin espacios, y las 5 del caso de grupos de espacio.
- `test_en_la_factura_con_la_pista_en_contra_queda_sin_leer` recorre esa familia con sus dos aserciones de antes: con la pista en contra da None, y con la pista None también.
- `test_en_la_factura_con_grupos_de_espacio_tambien` se retiró: sus entradas son ahora datos del caso unido.
- Mantuve las 4 entradas sin espacios, aunque no distinguen la regla, para no perder cobertura del resultado de `_monto_factura`. Hoy, en otro caso, sólo están cubiertas en `_numero_factura` o de punta a punta. El comentario de `FAMILIA` dice cuáles frena cada cosa. **Supuesto reversible:** si preferís sacarlas, son 4 tuplas.

### El rojo, una vez

Con la regla apagada (`if sin_grupo and decimal != sin_grupo.group(1):` → `if False:`) en un worktree descartable de `bb0d3347`, `tests/test_separadores1b.py` da:

```
FAILED tests/test_separadores1b.py::test_en_la_factura_con_la_pista_en_contra_queda_sin_leer[4 500.000-,]
FAILED tests/test_separadores1b.py::test_en_la_factura_con_la_pista_en_contra_queda_sin_leer[4'500.000-,]
FAILED tests/test_separadores1b.py::test_en_la_factura_con_la_pista_en_contra_queda_sin_leer[4 500.000-,]
FAILED tests/test_separadores1b.py::test_en_la_factura_con_la_pista_en_contra_queda_sin_leer[4\xa0500.000-,]
FAILED tests/test_separadores1b.py::test_en_la_factura_con_la_pista_en_contra_queda_sin_leer[12 345,250-.]
================== 5 failed, 100 passed, 5 warnings in 32.89s ==================
```

Con la regla da 105 passed. Las 4 entradas sin espacios siguen verdes con la regla apagada, como medías vos.

### Puertas, sobre `bb0d3347`

| puerta | salida |
|---|---|
| `tests/test_separadores1b.py` entero | `105 passed, 3 warnings in 32.23s` |
| `sabotaje_separadores1b.sh bb0d3347 <venv>` | `BASE en verde: 265 passed`; `factura_multiplica: 5 failed, 260 passed`; `factura_grupo_con_espacio: 5 failed, 260 passed`; `OK: los 12 sabotajes dan rojo por la razón esperada`; salida 0 |
| `anclas_perdidas.py HEAD` filtrado por `separadores1b` | nada (grep salió 1) |
| `chequeo-6.py d8383df2 HEAD` | entero abajo |

```
chequeo-6 d8383df2..HEAD: avisos para mirar, no un veredicto
producto +0/−0
arnés +11/−18
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

Las dos anclas del guion (1 y 2b) apuntan ahora al id del caso unido. Van en el mismo commit que el cambio de id.

### Comandos para reproducir

```bash
python -m pytest -q --no-cov tests/test_separadores1b.py                # 105 passed
bash scripts/testing/sabotaje_separadores1b.sh bb0d3347 <venv>          # termina en «OK: los 12 sabotajes dan rojo…», salida 0
python scripts/testing/anclas_perdidas.py HEAD | grep separadores1b     # nada
python docs/pm/herramientas/chequeo-6.py d8383df2 bb0d3347              # producto +0/−0, avisos: 0
```

- No corrí la suite completa: la tarea pide este archivo, el guion y chequeo-6.
- Archivos de producto tocados: ninguno.
- Riesgos: ninguno nuevo.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué SEPARADORES-1b-LIMPIEZA (bb0d3347 + informe); nada para decidir; tests/test_conexiones1.py sin seguimiento (su copia está en el parche); espero veredicto.
