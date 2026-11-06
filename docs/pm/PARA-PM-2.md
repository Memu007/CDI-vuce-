# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## RESET-1: **entregada** en `02a21e7` (el informe va en el commit siguiente) (2026-11-06)

| Punto de la tarea | Resultado | Qué decidís |
|---|---|---|
| Un link pedido antes de que el dueño cambie la clave o el email ya no sirve | Cambiar la clave (`/api/user/change-password`), el email (`PUT /api/user/profile`) o restablecerla con otro link marca como usados todos los links sin usar de esa cuenta. Caso `test_el_link_no_sirve_despues_de_un_cambio`, con los cambios como datos | D82 (¿pedir un link nuevo mata los de antes?) |
| Un link usado no sirve una segunda vez, tampoco con dos usos a la vez | El reset guarda la clave con compare-and-swap sobre el hash que leyó y consume el link en la misma transacción, sólo si sigue sin usar y sin vencer. En Postgres: dos usos a la vez dan un 200 y un 400 y la clave es la del primero | Nada |
| Los cambios como datos | `CAMBIOS`: cambio de clave, cambio de email, otro reset y el mismo link dos veces; un solo caso | Nada |
| (encontrado al atacarla) Un link pedido a la vez que un cambio de email | El pedido traba la fila de la cuenta filtrando por el email que leyó: si el email cambió, no sale link; si el cambio llega después, lo barre. Rojo en Postgres sobre el producto de antes | Nada |
| (encontrado al atacarla) Un link que vence entre validarlo y guardar | El consumo pide `expires_at > ahora`; si venció, no se guarda. Caso `test_un_link_que_vence_antes_de_guardar_no_cambia_la_clave` | Nada |

**Dos decisiones nuevas: D82 y D83.** Las de la devolución de CATALOGO-LARGO-2 empiezan en D84: tu canal dice «siguen en D82», pero RESET-1 ya las había tomado.

**Orden al revés del que pediste.** Escribiste «esta devolución primero, después RESET-1». Cuando llegó la devolución, RESET-1 ya tenía los rojos, el arreglo y los sabotajes hechos (`7b039aa` a `82130a8`); la cerré para no dejar un arreglo de seguridad a medio entregar. Sigo ahora con la devolución de CATALOGO-LARGO-2.

**Ojo para publicar, sigue igual:** la rama tiene `e0b8626` (COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a, sin aceptar). Ningún SHA mío sirve para publicar hasta que esas cinco estén ✅. El último limpio es `9018d77`.

**Archivos de producto:**
- `proyecto_maria/main.py`: `request_password_reset`, `reset_password` y `guardar_si_la_clave_sigue` (por donde ya pasaban el cambio de clave y el de perfil: barre los links ahí, una vez).
- `CHANGELOG.md`.

`producto +23/−15` (8 netas).

### Decisiones

**D82. ¿Pedir un link nuevo deja sin uso los de antes?** Hoy no: los barre usar un link, cambiar la clave o cambiar el email, no pedir otro.
- (a) Queda así. **Recomiendo esta.** Los mails llegan fuera de orden; el que pide dos veces y abre el primero no se encuentra con «Token inválido». Cada link vence solo y sólo llega al email del dueño.
- (b) Pedir uno nuevo mata los anteriores: menos links vivos a la vez, a cambio de ese tropiezo.

**D83. El alta de prueba que libera un email (`_archived_test_email`, detrás de `REGISTER_TEST_EMAIL_REPLACE`, apagado por defecto) cambia el email de una cuenta vieja sin barrer sus links.** Es la única escritura de `User.email` que no pasa por el perfil.
- (a) Queda así. **Recomiendo esta.** Sólo corre con la variable prendida y con emails de la lista de prueba; el que recibe esos links es el mismo dueño del buzón, que ya podía pedir uno. No hay ganancia de seguridad.
- (b) Barrer los links también ahí: una línea más, para que la regla no tenga excepciones.

### SHAs

| SHA | Qué |
|---|---|
| `5b0ca2b` | base |
| `7b039aa` | test: rojos de RESET-1 |
| `6e8109f` | test: Postgres, dos usos a la vez y cambio de email a la vez |
| `816eab9` | fix: el reset consume su link atómico y los cambios de cuenta lo matan |
| `82130a8` | test: sabotajes |
| `28d0422` | (tu devolución de CATALOGO-LARGO-2, por merge) |
| `fc2a066` | fix: el pedido traba la cuenta y el consumo mira el vencimiento |
| `b85016d`, `1227e10`, `02a21e7` | test: casos y sabotajes de lo anterior; docstring |
| `7181ca8` | merge de tu rama; difiere de `02a21e7` sólo en `docs/pm/` |

### Para reproducir

```bash
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
# 1. los casos: «6 passed»
python -m pytest -q --no-cov tests/test_reset1.py
# 2. Postgres local y descartable: tres «OK» y «fallas: 0»
python scripts/testing/reset1_postgres.py postgresql://cdi@127.0.0.1:55462/postgres
# 3. lo mismo en 82130a8 (sin fc2a066): «FALLA | el link pedido a la vez que el cambio de email no sirve»
# 4. sabotajes: 8 «ROJO», «fallas: 0»
PY=$(command -v python) PG_URL=postgresql://cdi@127.0.0.1:55462/postgres scripts/testing/sabotajes/reset1.sh 02a21e7
# 5. chequeo-6: «avisos: 0»
python docs/pm/herramientas/chequeo-6.py 5b0ca2b 02a21e7
```

### Puertas, sobre `02a21e7`

| Puerta | Salida |
|---|---|
| Suite completa | `4956 passed, 355 skipped, 3 xfailed, 97 warnings in 869.40s (0:14:29)` |
| `compileall -q proyecto_maria` | sin salida, código 0 |
| `smoke_friccion.sh` | `[FAIL] POST /api/ui/event`: el rojo de entorno conocido (manda `smoke_wave1` y `smoke_session_state_alias`, que no están en la lista de eventos: «Evento sin sesión no admitido»). La misma corrida con `hero_cta_clicked` da `SMOKE_EXIT=0` |
| `ataque_aislamiento.sh` (PUERTO=8133) | `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`, `✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.`, código 0 |
| `reset1_postgres.py` (Postgres 16 en 55432) | tres `OK`, `fallas: 0` |
| Lo mismo en `82130a8` | `FALLA | el link pedido a la vez que el cambio de email no sirve: … reset 200, clave sin cambiar False`; en pytest, `assert True is False` en el caso del vencimiento |
| Revisión de seguridad | **inline sobre el diff de `fc2a066` y `816eab9`, no con `/security-review`**: el comando revisa la rama entera contra `main` (411 KB de diff, piezas ajenas). Sin hallazgos de confianza alta. Nota menor: con la fila trabada, el pedido tarda más para una cuenta que existe; no se puede explotar más allá de lo que ya da el 200 genérico |

### Sabotajes (`scripts/testing/sabotajes/reset1.sh` sobre `1227e10`, con Postgres)

```
ROJO  | cambiar la clave o el email no mata los links de antes: dice «FAILED tests/test_reset1.py::test_el_link_no_sirve_despues_de_un_cambio[cambio de clave] FAILED tests/test_reset1.py::test_el_link_no_sirve_despues_de_un_cambio[cambio de email] FAILED tests/test_reset1.py::test_el_link_no_sirve_despues_de_un_cambio[otro reset] el link viejo sigue sirviendo»
ROJO  | cambiar el email no mata los links de antes: dice «FAILED tests/test_reset1.py::test_el_link_no_sirve_despues_de_un_cambio[cambio de email] el link viejo sigue sirviendo»
ROJO  | el reset guarda sin compare-and-swap ni consumo: dice «FAILED tests/test_reset1.py::test_el_link_no_sirve_despues_de_un_cambio[otro reset] el link viejo sigue sirviendo»
ROJO  | el consumo no mira el vencimiento: dice «FAILED tests/test_reset1.py::test_un_link_que_vence_antes_de_guardar_no_cambia_la_clave»
ROJO  | el reset no consume su link: dice «FALLA | el cambio de email que llega primero mata el link»
ROJO  | el reset que pierde la carrera dice que guardó: dice «FALLA | el mismo link dos veces a la vez FALLA | el cambio de email que llega primero mata el link»
ROJO  | el reset guarda sin compare-and-swap ni consumo: dice «FALLA | el mismo link dos veces a la vez FALLA | el cambio de email que llega primero mata el link»
ROJO  | pedir un link no traba la cuenta: dice «FALLA | el link pedido a la vez que el cambio de email no sirve»
fallas: 0
salida 0
```

`02a21e7` sólo cambia un docstring respecto de `1227e10`.

### chequeo-6

```
chequeo-6 5b0ca2b..02a21e7: avisos para mirar, no un veredicto
producto +23/−15
arnés +373/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11939 → 11947
avisos: 0
```

### Hallazgos

| # | Quién (modelo, esfuerzo) | Hallazgo | Qué hice |
|---|---|---|---|
| 1 | adversario Opus, alto | MEDIA: un link pedido a la vez que un cambio de email lee el email viejo y se guarda después del cambio: sirve | Reproducido en Postgres (rojo en `82130a8`); arreglado en `fc2a066` |
| 2 | adversario Opus, alto | BAJA: un link que vence entre validarlo y guardar cambia la clave igual | Reproducido; arreglado en `fc2a066` |
| 3 | adversario Opus, alto | INFORMATIVO: el chequeo 1 de Postgres (mismo link dos veces) lo decide el compare-and-swap de la clave; el consumo atómico lo mide el chequeo 2 | Queda dicho en «Riesgos» |
| 4 | adversario Opus, alto | Sin deadlock entre el pedido, el reset y los cambios de cuenta | Nada |
| 5 | `/code-review high` | Puntos 1, 3, 7, 8 y 10 | Aplicados |
| 6 | `/code-review high` | 4: bcrypt corre en el loop de eventos (de antes); 5: la firma con `consumir`/`password` por nombre, se deja; 6: el SELECT previo al compare-and-swap, se deja; 9: el script abre una conexión por sondeo | Riesgos, sin cambio |

### Riesgos

- bcrypt en el loop de eventos (anterior a la pieza): `reset_password` llama a `hash_password` sin threadpool y ocupa el proceso mientras calcula.
- El rehash de claves planas de usuarios demo (`main.py:3166`, sólo fuera de producción) escribe la clave sin pasar por `guardar_si_la_clave_sigue`: no barre links. El hash es de la misma clave, así que no cambia quién entra.
- Si se sacara sólo el consumo atómico y quedara el compare-and-swap, el chequeo 1 de Postgres seguiría verde; lo pone rojo el chequeo 2.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797WNM. RESET-1 entregada en 02a21e7 (informe en el commit siguiente); D82 y D83 nuevas; sigo con la devolución de CATALOGO-LARGO-2, cuyas D empiezan en D84; después PYPDF-1. Nada se publica sin el «dale» de Emi para el SHA, nunca main, sin secretos ni datos reales.
