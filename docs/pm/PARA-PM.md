# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1-NOKEY: el bloqueo de la cuenta toma FOR NO KEY UPDATE

| | SHA |
|---|---|
| base (tu rama, traída con merge) | `3874a1d2` |
| fix: `_cuenta_bloqueada` con `key_share=True` y `of=`, `CHANGELOG` | `298e5fee` |
| test: el caso 6 mira el SQL que llega a Postgres y su sabotaje | `936f6010` |
| test: filas MAL de los pares objetivo, `PY` absoluto, `trap` | `33d00cd4` |
| merge de tu rama (`35de2344`) | `8bc3db7f` |
| test: ancla de `limpieza1.sh` en el nombre del job | `ac4993b7` |
| informe | el commit `docs:` que trae este archivo |

**Resultado.** Con créditos vencidos, la recarga junto a un guardado o a MARIA
ya no da deadlock, 500 ni recarga sin acreditar: 0/30 en cada uno de los cuatro
pares objetivo, contra 8–10 de 10 sin el arreglo. Los choques del alta, cancelar
y reactivar siguen: son la pieza siguiente.

Archivo de producto tocado: `proyecto_maria/main.py` (sólo `_cuenta_bloqueada`).

### Decisiones

- **D231. El pin de SQLAlchemy (`requirements.txt:92`, `2.0.25`).** En esa
  versión, la clave de cache de `with_for_update` no incluye `key_share`: por
  eso, sin `of=`, se reusa el `FOR UPDATE` que compiló la consulta igual del
  aviso. El `of=` lo esquiva y el caso 6 lo prueba mirando el SQL real.
  - a) Dejar el pin y el `of=` (recomiendo: el arreglo ya está probado y
    subir el ORM toca todo el producto).
  - b) Una tarea aparte para subir SQLAlchemy a una 2.0 que tenga la clave
    completa, con suite completa.

- **Objeción al criterio de la pieza chica.** Pediste que
  `anclas_perdidas.py <SHA>` no nombre `limpieza1.sh`. Ya no lo nombra como
  PERDIDA, pero sigue nombrándolo en 6 líneas SIN ANCLA (175, 177, 179, 181,
  183, 187): «el cambio lo hace «git»/«nuevo», que no reemplaza texto». Esos
  sabotajes crean o borran archivos, no reemplazan texto, así que no tienen
  ancla por diseño y ya estaban así antes. Propongo leer el criterio como «no
  lo nombra como PERDIDA». Si querés el literal, hay que cambiar
  `scripts/testing/anclas_perdidas.py`: decime y lo hago como pieza aparte.

### Comandos

```bash
PY=$PWD/<venv>/bin/python
git diff 3874a1d2 ac4993b7 -- proyecto_maria/
# tiene que mostrar sólo _cuenta_bloqueada: dos with_for_update(key_share=True, of=…) y dos líneas del docstring
PY=$PY scripts/testing/sabotajes/conexiones1_nokey.sh ac4993b7
# tiene que dar tres BIEN y salir 0; la primera dice «FOR NO KEY UPDATE OF users | FOR NO KEY UPDATE OF organizations»
PY=$PY scripts/testing/sabotajes/limpieza1.sh ac4993b7
# tiene que tener «ROJO  | el job con continue-on-error» y «sabotajes con falla: 0»
$PY scripts/testing/anclas_perdidas.py ac4993b7 | grep limpieza1
# fila «0 | 0 | 0 | 0 | 6 | 33» y ninguna PERDIDA de limpieza1.sh
```

### Lo que ya corrí

| Puerta | SHA | Resultado |
|---|---|---|
| suite completa (`pytest -q --no-cov --timeout=120`) | `936f6010` | rc=0: «6231 passed, 110 skipped, 3 xfailed, 110 warnings in 1415.31s (0:23:35)», 0 failed |
| `conexiones1_nokey.sh` | `33d00cd4` | rc=0 en 134 s, tres BIEN (abajo) |
| carrera natural, N=30 | `33d00cd4` | pares objetivo 0/30 (abajo) |
| la misma carrera sin el arreglo, N=10 | HEAD sin `298e5fee` | recarga + guardado 10/10 y 8/10; recarga + maria 9/10 y 9/10 |
| `limpieza1.sh` | `ac4993b7` | rc=0 en 94 s, 40 filas, «sabotajes con falla: 0» |
| `e2e_maria.sh` | `ac4993b7` | rc=0 en 32 s, «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| `anclas_perdidas.py` | `8bc3db7f` / `ac4993b7` | `limpieza1.sh: 1 \| 0 \| 0 \| 0 \| 6 \| 32` → `0 \| 0 \| 0 \| 0 \| 6 \| 33` |
| `/security-review` (Sonnet alto) | `33d00cd4` | 0 hallazgos con confianza ≥ 8 |

`conexiones1_nokey.sh` sobre `33d00cd4`:

```
BIEN  | sin sabotaje: salida 1, dice «_cuenta_bloqueada después del aviso: FOR NO KEY UPDATE OF users | FOR NO KEY UPDATE OF organizations»
        deadlocks: 3; rondas sin armar: 0; filas MAL: 0
BIEN  | sin key_share ni of=: salida 1, dice «FOR UPDATE | FOR UPDATE | MAL DEADLOCK | recarga + guardado DEADLOCK | recarga + maria»
        deadlocks: 5; rondas sin armar: 0; filas MAL: 2
BIEN  | key_share sin of=: salida 1, dice «FOR NO KEY UPDATE | FOR UPDATE | MAL»
        deadlocks: 3; rondas sin armar: 0; filas MAL: 0
```

El caso sale 1 también con el arreglo: los 3 deadlocks son de los pares del
alta, que no entran en esta pieza. Lo que discrimina es el texto.

Carrera natural sobre `33d00cd4`, N=30:

```
recarga + guardado, créditos vencidos: 0/30 rondas con deadlock, 0/30 mal
recarga + guardado, créditos al día: 0/30 rondas con deadlock, 0/30 mal
recarga + maria, créditos vencidos: 0/30 rondas con deadlock, 0/30 mal
recarga + maria, créditos al día: 0/30 rondas con deadlock, 0/30 mal
recarga + alta, créditos vencidos: 0/30 rondas con deadlock, 30/30 mal
...
rondas con deadlock: 42, recargas perdidas: 30, cuentas mal: 36
sale 1 en 285 s
```

Los totales vienen de los pares del alta y de la renovación, que siguen abiertos.

Sabotaje de `limpieza1.sh` sobre `ac4993b7`:

```
ROJO  | el job con continue-on-error: dice «la CI puede esconder el resultado de la suite: ['continue-on-error: true']»
sabotajes con falla: 0
rc=0 en 94s
```

`chequeo-6` 3874a1d2..ac4993b7, entero:

```
chequeo-6 3874a1d2..ac4993b7: avisos para mirar, no un veredicto
producto +5/−3
arnés +123/−14
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12287 → 12289
avisos: 0
```

### Hallazgos

| Revisor | Modelo y esfuerzo | Hallazgo | Qué pasó |
|---|---|---|---|
| adversario | Sonnet alto | ninguno de la pieza; stress 64/64 sin 500, contra 5 filas 500 en la base | — |
| adversario | Opus alto | producto limpio | — |
| adversario | Opus alto | A–D del arnés: una ronda sin armar o con 500 daba BIEN por los deadlocks de otros pares; el control exigía un deadlock que se va a arreglar; `PY` relativo; `trap` después de `worktree add` | arreglados en `33d00cd4` |
| adversario | Opus alto | la cache de `users` (`main.py:11724`) no tiene caso | queda como riesgo |
| `/security-review` | Sonnet alto | 0 con confianza ≥ 8 | — |
| propio | — | nit 1: SQLAlchemy 2.0.25 no tiene `key_share` en la clave de cache | D231 |

### Qué no se corrió

- **La suite sobre el SHA final.** Corrió sobre `936f6010`. Después sólo
  cambiaron scripts y docs (`33d00cd4`, `8bc3db7f`, `ac4993b7`), nada que corra
  pytest.
- **El rojo del `PY` relativo.** El guion viejo con `PY` relativo dio BIEN por
  coincidencia, así que el arreglo de esa línea no tiene rojo mostrado.
- **El rojo del ancla vieja de `limpieza1.sh`.** Lo muestra `anclas_perdidas`
  sobre `8bc3db7f` («PERDIDA, UNA LÍNEA scripts/testing/sabotajes/limpieza1.sh:135
  .github/workflows/ci.yml (está 0, se esperaba 1)»); no corrí el guion viejo.
- **La cache de `users`.** Sin caso.

### Riesgos

- «key_share sin of=» sólo lo discrimina la línea del SQL: los deadlocks y las
  filas MAL dan igual que sin sabotaje, porque Postgres recibe un candado
  NO KEY en `users` y uno FOR UPDATE en `organizations`.
- Con el pin actual, quien escriba otra `with_for_update(key_share=True)` sin
  `of=` sobre una consulta que ya está en cache recibe en silencio un FOR
  UPDATE (D231).

### Observación, no es mía

`anclas_perdidas.py ac4993b7` da PERDIDA en `catalogo_largo2.sh` (224, 263) y en
`cobro_corte1.sh` (430, 434, 438), las cinco contra `proyecto_maria/main.py`.

Ahora sigo con CONEXIONES-1-PRODUCTO (D182, D183, D188). **Próxima D: D232.**

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, base 3874a1d2. CONEXIONES-1-NOKEY entregada (fix 298e5fee, tests 936f6010/33d00cd4/ac4993b7, merge 8bc3db7f, informe en el docs siguiente). Pieza activa: CONEXIONES-1-PRODUCTO (D182, D183, D188) sobre ella; plan b60c30d4 como sugerencia; D205 no entra. Revisión fuerte: /security-review, adversarios con Postgres 16 sin red y GEMINI_API_KEY vacía, suite completa, e2e_maria.sh, sabotaje propio. Próxima D: D232. Sin advisor, nunca main, sin secretos, test_conexiones1.py no se sube.
