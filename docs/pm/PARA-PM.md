# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## AUTOREMOVE-PG: el caso del dueño, también en Postgres

| SHA | qué |
|---|---|
| `24788cf0` | base (tu merge, AUTOREMOVE aceptada) |
| `6d370864` | `test:` el caso en `org1_postgres.py` y el rojo de Postgres en `org1.sh` |
| este commit | `docs:` informe (y el merge de tu rama, sólo `NOW.md`) |

**Nada para decidir.** Producto +0/−0. Postgres da lo mismo que SQLite:
- el nombre exacto da 400;
- las tres variantes dan 404;
- la base queda igual;
- Mercado Pago no se llama.

No corrí adversarios ni `/code-review`, como pedía la tarea.

### A. El caso, en `org1_postgres.py`, sección 6

- **Estudio:** es el mismo de la guarda anterior: el dueño y un miembro que entró con invitación.
- **Suscripción:** con `sql()`, el dueño recibe `mp_preapproval_id = pend-<dueño>`.
- **Mercado Pago:** `main_mod._leer_suscripcion_mp` y `main_mod._cancelar_suscripcion_mp` se reemplazan por funciones que sólo anotan en `a_mp`. La de leer contesta «pending». Las dos originales se restauran en un `finally`.
- **Pedidos:** con la sesión del dueño, `DELETE /api/organizations/members/<nombre>` va una vez por variante:
  - el nombre exacto;
  - en mayúsculas;
  - con un espacio adelante;
  - con un espacio atrás.
- **Un solo `chequear`:** «el dueño no se saca a sí mismo». Pasa sólo si se cumplen las cuatro condiciones:
  - el nombre exacto da `(400, "No podés removerte a vos mismo del estudio")`;
  - cada variante da esa misma respuesta o `(404, "Ese usuario no es miembro del estudio")`;
  - la base queda igual que antes (lo de abajo);
  - `a_mp == []`.
- **Lo que se mira en la base, antes y después, con `sql()`:**
  - `owner_username` del estudio, junto con el `mp_preapproval_id` del dueño;
  - los usernames de los miembros del estudio, ordenados.

Salida en verde:
```
OK    | el dueño no se saca a sí mismo ([(400, 'No podés removerte a vos mismo del estudio'), (404, 'Ese usuario no es miembro del estudio'), (404, 'Ese usuario no es miembro del estudio'), (404, 'Ese usuario no es miembro del estudio')], True, [])
```

### B. El rojo, una vez

Sobre `6d370864`, en un worktree descartable, borré las dos líneas de la guarda y corrí `org1_postgres.py` contra un Postgres 16 local. Los nombres van tapados:
```
FALLA | el dueño no se saca a sí mismo ([(200, ''), (400, 'No pertenecés a un estudio'), (400, 'No pertenecés a un estudio'), (400, 'No pertenecés a un estudio')], False, [('leer', 'pend-o1d_…'), ('cancelar', 'pend-o1d_…')])
```
Qué muestra:
- El dueño sale con 200.
- La base cambia (`False`).
- Mercado Pago se leyó y se canceló.
- Las variantes ya ven al dueño fuera del estudio.

En `org1.sh` con `PG=`, el mismo sabotaje da:
```
ROJO  | el dueño se saca a sí mismo (SQLite): «FAILED tests/test_org1.py::test_el_duenio_no_se_saca_a_si_mismo_y_el_estudio_queda_igual» 
ROJO  | el dueño se saca a sí mismo (Postgres): «FALLA | el dueño no se saca a sí mismo» 
```

### C. Puertas, sobre `6d370864`

| puerta | resultado |
|---|---|
| `org1.sh` entero con `PG=` (Postgres 16 local, vía `con_pg16.sh`) | `BASE  \| verde sin sabotaje en 6d370864… (SQLite y Postgres)`; 40 ROJO, 28 de SQLite y 12 de Postgres; `sabotajes sin rojo: 0`; `salida 0` |
| `chequeo-6.py 24788cf0 6d370864` | completo abajo |

Los conteos de `org1.sh`:
- Tiene 29 sabotajes.
- Uno, «la regla 2 despierta a las marcadas vencidas», sólo tiene rojo en Postgres; por eso SQLite da 28.
- En Postgres hay 12: los 11 que ya estaban más el nuevo.
- Vos habías contado 29 + 10 sobre `1368dff8`. No sé de dónde sale la diferencia: en la base, el guion ya tenía 11 sabotajes con rojo de Postgres.

```
chequeo-6 24788cf0..6d370864e8a17136611ebb1bf3a77cec9d409dfd: avisos para mirar, no un veredicto
producto +0/−0
arnés +27/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### D. Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout <SHA de este informe>
PY=<venv>/bin/python scripts/testing/con_pg16.sh bash -c \
  'PG="${BACKUP1A_PG_URL%/postgres}" scripts/testing/sabotajes/org1.sh 6d370864'
#   → BASE verde (SQLite y Postgres), «ROJO  | el dueño se saca a sí mismo (Postgres)», «sabotajes sin rojo: 0», salida 0
python docs/pm/herramientas/chequeo-6.py 24788cf0 6d370864
#   → producto +0/−0, avisos: 0
```

### E. No corrido y riesgos

- Los otros tres sabotajes del dueño siguen sin rojo de Postgres: «la guarda va después de Mercado Pago», «sacar busca sin mayúsculas» y «sacar busca sin espacios». La tarea pedía sólo el primero. El caso nuevo los cubriría, pero eso no lo corrí.
- No corrí la suite completa porque no hay cambios de producto.
- Archivos de producto tocados: ninguno.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué AUTOREMOVE-PG (6d370864 + informe); nada para decidir; tests/test_conexiones1.py sin seguimiento (su copia está en el parche); espero veredicto.
