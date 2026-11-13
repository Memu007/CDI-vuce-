# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL2D-RELOJ vuelta 2: la espera medida no depende de cuántos hilos tenga el proceso

| | SHA |
|---|---|
| base | `806f838c` |
| test | `cc8c7b7d` |
| informe | el commit `docs:` que trae este archivo |

**Resultado: cumple las cinco puertas.** Nada para decidir.

- Con la espera de 0,8 s, el test da rojo con 0, 1000 y 3000 hilos y mide 0,79 s en los tres casos.
- Con 4 s mide 4,00, 3,99 y 3,99 s.
- La suite entera da `6112 passed, 110 skipped, 3 xfailed`, igual que tu referencia.
- No toca el producto: `producto +0/−0`, arnés `+9/−11`.

### Causa
El testigo marcaba `True` el salto en el que recorría `/proc/self/task`, y ese salto no sumaba espera. Con muchos hilos, el recorrido tarda más que el tic de 10 ms, así que buena parte de la espera caía en saltos que no contaban.

### Arreglo (sólo en `tests/test_excel2d.py`)
- **CPU sin el testigo.** La CPU del salto es `process_time - thread_time`, así no entra lo que gasta el propio testigo al recorrer `/proc`.
- **Un veredicto por salto entero.** El veredicto del recorrido vale para todo el salto, recorrido incluido: la marca de tiempo se toma después de recorrer.
- **Gasto con el mismo reloj.** El gasto sale de esas marcas: `pasos[-1][1] - pasos[0][1]`.

### Puertas sobre `cc8c7b7d`

**Puertas 1 a 3 (filtro `no_frena and 2499`):**

| espera inyectada | 0 hilos | 1000 hilos | 3000 hilos |
|---|---|---|---|
| ninguna | `1 passed … in 0.61s` | `in 0.66s` | `in 0.69s` |
| 0,8 s | `la subida esperó 0.79 s sin gastar CPU`, `1 failed` | `0.79 s`, `1 failed` | `0.79 s`, `1 failed` |
| 4 s | `4.00 s`, `1 failed` | `3.99 s`, `1 failed` | `3.99 s`, `1 failed` |

**Puerta 4:** `sabotajes/excel2d.sh cc8c7b7d`.
- Sin hilos: 21 `ROJO`, «sabotajes con falla: 0».
- Con `HILOS=1000` (tu plugin): 21 `ROJO`, «sabotajes con falla: 0».
- En las dos corridas, el último dice: «ROJO  | la subida espera 4 s sin gastar CPU: dice «FAILED tests/test_excel2d.py::test_la_subida_cara_no_frena_a_nadie[2499 combinadas en 4998 filas]» (13 s)».
- El guion tiene 21 sabotajes, no los 6 que nombraste: los corrí todos.

**Puerta 5:** `pytest` entero con `--no-cov --timeout=120 -p no:cacheprovider`.
- Resultado: `6112 passed, 110 skipped, 3 xfailed, 106 warnings in 1092.69s (0:18:12)`, código 0.

### Mediciones fuera de las puertas

**Sabotaje propio: el test viejo (`806f838c`) con 0,8 s.**

| hilos | resultado |
|---|---|
| 0 | `la subida esperó 0.82 s`, `1 failed` |
| 1000 | `1 passed` |
| 3000 | `1 passed` |

Ése es el defecto que la vuelta arregla.

**Hambre: `taskset -c 0` con 8 `yes`, los 7 casos de la subida cara.**

| espera | 0 hilos | 1000 hilos | 3000 hilos |
|---|---|---|---|
| ninguna | `7 passed … 22.62s` | `7 passed … 23.29s` | `7 passed … 25.20s` |
| 4 s | `3.99 s`, `1 failed` | `3.99 s`, `1 failed` | `4.21 s`, `1 failed` |

Con 3000 hilos y la CPU fijada mide de más, cerca de un 5 %. Probablemente sea el tiempo en que el testigo queda desalojado. Mide de más, no de menos: no esconde una espera.

**Carga sin fijar a una CPU (`yes` sueltos).**

| procesos `yes` | hilos | sin espera | con 4 s |
|---|---|---|---|
| 4 | 0 | `7 passed` | `4.00 s` |
| 4 | 3000 | `7 passed` | `3.92 s` |
| 8 | 0 | `7 passed` | `4.00 s` |
| 8 | 3000 | `7 passed` | `3.97 s` |

### chequeo-6 (entero)
```
chequeo-6 806f838c..cc8c7b7d441235c56e43b5ff0361a6abe1726262: avisos para mirar, no un veredicto
producto +0/−0
arnés +9/−11
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### Comandos para reproducir
```bash
git checkout cc8c7b7d
python -m pytest -q --no-cov tests/test_excel2d.py -k 'no_frena and 2499'   # 1 passed
bash scripts/testing/sabotajes/excel2d.sh cc8c7b7d                           # 21 ROJO, «sabotajes con falla: 0»
HILOS=1000 PYTHONPATH=<carpeta de tu hilos_plugin.py> PYTEST_ADDOPTS="-p hilos_plugin" \
  bash scripts/testing/sabotajes/excel2d.sh cc8c7b7d                         # lo mismo
```

### No corrido
- Adversarios y `/code-review`: no los corrí porque esta vuelta es «sin adversarios».
- No toqué los topes de 1 s y 0,5 s: estaban fuera de la pieza.

### Archivos de producto tocados
Ninguno.

### Para FUGA-HILOS (la sigo ahora)
- Hay 18 archivos de `tests/` con `new_event_loop`, no 77: los otros 59 eran `.pyc`.
- La base para la puerta 3 sale de esta misma corrida entera: 1113 «Task was destroyed but it is pending» con `async_generator_athrow`.

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; entregué EXCEL2D-RELOJ (test cc8c7b7d); sigo con FUGA-HILOS (D229 a), base 1113 «Task was destroyed» con async_generator_athrow; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM; nada se publica sin el «dale» de Emi para el SHA, nunca main, sin secretos; próxima D: D230.
