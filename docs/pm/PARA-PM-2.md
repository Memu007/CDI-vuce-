# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORG-1 + D40, devolución sobre `b358827`: **entregada** en `bf9583b` (2026-11-09; el informe va en el commit siguiente), base `db9f11f`

Los seis puntos de la devolución están atendidos. El producto cambió en dos
lugares de `main.py` (+8/−3): el tope ya no cuenta las pendientes de emails
con cuenta, y al registrarse una vencida por fecha no queda usada. Decidís
D151 (cuándo traigo tu rama). Lo demás de las decisiones sigue como estaba.

| SHA | qué |
|---|---|
| `1095f5c` | fix: una pendiente a un email con cuenta no ocupa lugar en el tope |
| `ef022b3` | test: un caso por guarda de invitar, sacar, validar y listar, con su sabotaje |
| `e9e6153` | fix: una vencida por fecha no queda usada; el tope compara la cuenta como el registro (lower, sin trim). Suma CHANGELOG |
| `bf9583b` | test: los rojos de `e9e6153` y tres sabotajes |
| este commit | docs: el informe |

**Producto +8/−3. Arnés +406/−58** (`test_org1.py` +173, `sabotajes/org1.sh`
+174/−57, `org1_postgres.py` +59/−1).

### Los seis puntos

1. **El «Sumá» 4, un caso por guarda.** Casos nuevos en `tests/test_org1.py`,
   cada uno con su sabotaje en `org1.sh`:
   - `test_invitar_o_sacar_sin_estudio_400` ← «invitar sin estudio», «sacar sin estudio»;
   - `test_un_miembro_no_puede_invitar_403` ← «invita quien no es dueño» (tu `if False`);
   - `test_la_invitacion_vence_a_los_7_dias` ← «la invitación vence a los 8 días»;
   - `test_validar_con_el_estudio_borrado_404` ← «validar con el estudio borrado»;
   - `test_sacar_a_alguien_de_otro_estudio_404_y_sigue_en_el_suyo` ← «sacar busca en todos los estudios» (tu filtro por estudio);
   - `test_sacar_no_borra_al_usuario` ← «sacar borra al usuario»;
   - `test_mine_lista_sólo_los_miembros_del_estudio_y_quién_es_dueño` ← los tres de `/mine`.
   El de validar con el estudio borrado corre sólo en SQLite: en Postgres la
   FK de `models.py:571` no deja borrar el estudio con la invitación adentro.
2. **Una vencida queda vencida.** `test_una_invitacion_vencida_sigue_vencida_cuando_entra_con_otra`,
   por zona (SQLite sin zona, Postgres con zona) × estado (`expired`, y
   `pending` con la fecha pasada). El `pending` vencido por fecha estaba **en
   rojo** (`'accepted' == 'pending'`): el `UPDATE` del registro lo marcaba
   usado. Lo arregla `e9e6153`. El filtro `status == "pending"` sólo lo
   distingue Postgres: en SQLite la marcada `expired` no vuelve a `pending`
   por otro lado. Sabotajes: «la regla 2 despierta a las marcadas vencidas
   (sólo en PG)» y «la regla 2 usa las vencidas por fecha».
3. **El orden de los mensajes.** `test_con_el_estudio_lleno_un_email_con_cuenta_dice_que_ya_tiene_cuenta`,
   también en `org1_postgres.py`. Ya estaba verde; lo distingue «con el
   estudio lleno, el tope habla antes que la cuenta».
4. **El `UPDATE` en la misma transacción.** `test_si_falla_usar_las_otras_invitaciones_no_se_crea_la_cuenta`:
   secuencial, hace fallar el `UPDATE` y comprueba que no queda la cuenta ni
   cambia la invitación. Ya estaba verde; lo distingue «la regla 2 en otra
   transacción».
5. **Lugar muerto.** `test_una_pendiente_cuyo_email_ya_tiene_cuenta_no_ocupa_lugar`,
   con la familia como datos: `sin link` (tu A), `con la invitacion de otro
   estudio` (tu C), `perfil` (se pone ese email en el perfil) y `vieja en
   mayusculas` (cuenta guardada con mayúsculas). Los cuatro **en rojo** sobre
   `db9f11f` (`4 failed, 79 passed`); los arregla `1095f5c`. El caso de la
   cuenta guardada con espacios (`test_una_pendiente_a_una_cuenta_con_espacios_ocupa_lugar`)
   va al revés: esa cuenta no frena el registro, así que la invitación sí se
   puede usar y sigue ocupando lugar. Estaba **en rojo** con `1095f5c`
   (`200 == 400`); lo arregla `e9e6153`. Sabotajes: «el tope cuenta las
   pendientes de emails con cuenta», «el tope compara la cuenta sin
   mayúsculas», «el tope compara la cuenta sin espacios».
6. **A riesgos**, abajo: R1 a R3.

## Decisiones

- **D151. Cuándo traigo tu rama.** `DECISIONS.md:557` (D136) dice que no la
  traigo hasta que INTEGRAR-1 esté aceptada, y tu rama trae producto de la
  técnica (`main.py`, `models.py`, billing).
  - (a) Espero a INTEGRAR-1.
  - (b) La traigo ahora y resuelvo los choques en `main.py`.

  **Recomiendo (a):** es lo decidido en D136, y traerla ahora mezcla en esta
  entrega producto que no es de la pieza.

Siguen abiertas D131 (a Emi) y D142 (a Emi; mientras, c). D150 la decidiste
(b), D139 (a). La próxima D libre es la D152.

Supuestos reversibles:

1. **«Tiene cuenta» compara `lower(email)` sin `trim`, igual que el registro.**
   Si la cuenta quedó guardada con espacios, el registro no la ve, así que la
   invitación se puede usar y ocupa lugar.
2. **El tope descuenta con una consulta más bajo el lock del estudio.** Son
   tres consultas bajo `with_for_update`; no medí el costo, es un estudio con
   pocas pendientes.

## Comandos

```bash
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
# casos de la pieza: «86 passed»
python -m pytest -q --no-cov tests/test_org1.py
# arnés de Postgres, en una base nueva: termina en «fallas: 0»
psql postgresql://cdi@127.0.0.1:55432/postgres -qc "create database org1pm" && python scripts/testing/org1_postgres.py postgresql://cdi@127.0.0.1:55432/org1pm; psql postgresql://cdi@127.0.0.1:55432/postgres -qc "drop database org1pm"
# sabotajes: 35 «ROJO», «sabotajes sin rojo: 0», salida 0
PY=python PG=postgresql://cdi@127.0.0.1:55432 ./scripts/testing/sabotajes/org1.sh bf9583b
# rojo del lugar muerto: los cuatro de la familia, «4 failed»
git checkout db9f11f -- proyecto_maria/main.py && python -m pytest -q --no-cov tests/test_org1.py -k no_ocupa_lugar; git checkout HEAD -- proyecto_maria/main.py
```

## Puertas

| corrida | SHA | salida exacta |
|---|---|---|
| `sabotajes/org1.sh bf9583b` con `PG=` | `bf9583b` | `BASE  | verde sin sabotaje en bf9583b… (SQLite y Postgres)`, 35 líneas `ROJO` (25 sabotajes; los que el arnés de Postgres no distingue corren sólo en SQLite, y «despierta a las marcadas vencidas» sólo en Postgres), `sabotajes sin rojo: 0`, `salida 0` |
| suite completa (`pytest -q --no-cov --timeout=120`) | `bf9583b` | `5452 passed, 335 skipped, 3 xfailed, 106 warnings in 1045.19s (0:17:25)`, `salida 0` |
| `compileall -q proyecto_maria` | `bf9583b` | sin salida, `salida 0` |
| smoke_friccion, servidor local en el 8097 | `bf9583b` | `OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido`, `salida 0` |
| `ataque_aislamiento.sh` (`PUERTO=8098`) | `bf9583b` | `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`, `✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.`, `salida 0` |
| rojo de `test_org1.py` con el producto de `ef022b3` | `bf9583b` | `3 failed, 83 passed, 5 warnings in 55.39s`: `[sqlite_sin_zona-pending]`, `[postgres_con_zona-pending]`, `test_una_pendiente_a_una_cuenta_con_espacios_ocupa_lugar` |
| rojo de `test_org1.py` sobre `db9f11f` | `ef022b3` | `4 failed, 79 passed`, los cuatro de `test_una_pendiente_cuyo_email_ya_tiene_cuenta_no_ocupa_lugar` |

**Corrido y no corrido:** todo lo de la tabla, una corrida a la vez, sobre `bf9583b`. La suite completa corre sólo en SQLite; en Postgres 16 corrieron `org1_postgres.py` (dentro de los sabotajes, que arrancan con la base en verde) y los sabotajes marcados PG. No corrí los sabotajes de otras piezas: son tuyos al publicar.

## Hallazgos de la autorrevisión

| quién | hallazgo | qué hice |
|---|---|---|
| `/code-review high` | Una pendiente vuelve a ocupar lugar si la cuenta suelta el email (lo cambia en el perfil) | Es correcto: la invitación vuelve a poder usarse. A riesgos (R4) |
| `/code-review high` | El tope comparaba la cuenta con `trim` y el registro sin | Arreglado en `e9e6153`, con su rojo |
| `/code-review high` | El `UPDATE` del registro marcaba usada una pendiente vencida por fecha | Arreglado en `e9e6153`, con su rojo |
| `/code-review high` | Marcar las pendientes al momento en que alguien toma el email | Propuesta, no la hice: suma escrituras en el perfil. A riesgos (R4) |
| `/code-review high` | `archivo` se pisaba entre sabotajes en `org1.sh` | Arreglado en `bf9583b` |
| `/code-review high` | Tres consultas bajo el lock del estudio | Queda: supuesto 2 |
| `/code-review high` | Dos hallazgos más | Descartados al verificarlos; no guardé su texto, así que no te los puedo citar |
| `/code-review high` | Dos opcionales de estilo | No los hice |
| `adversario-sonnet-alto` (Sonnet, alto) | La vencida por fecha queda usada | El mismo de arriba: arreglado en `e9e6153` |
| `adversario-sonnet-alto` (Sonnet, alto) | Una pendiente revive si la cuenta suelta el email | Lo reprodujo; R4 |
| `adversario-sonnet-alto` (Sonnet, alto) | Variantes del tope que ningún caso distinguía | Cerrado con los tres sabotajes del tope |
| `adversario-sonnet-alto` (Sonnet, alto) | El bloque de Postgres no se había corrido | Corrido: puertas |
| `/security-review` | Sin hallazgos con confianza ≥ 8: consultas parametrizadas, el tope no se saltea porque el registro vuelve a contar bajo lock | Nada |

## Riesgos

1. **`REGISTER_TEST_EMAIL_REPLACE`** (`main.py:235`): con esa variable en
   `true`, el registro reemplaza el email. Es un modo de prueba que vive en
   el producto.
2. **Invitar dice si un email tiene cuenta, sin límite de pedidos.** Un dueño
   puede preguntar por cualquier email. Es anterior a la pieza.
3. **Cambiar el email del perfil no pide verificarlo.** Con eso se puede
   tomar un email ajeno y liberar el lugar de su invitación pendiente.
4. **Una pendiente vuelve a ocupar lugar si la cuenta suelta el email.** Es
   correcto (la invitación vuelve a poder usarse), pero el dueño puede ver
   que el estudio pasa a estar lleno sin haber invitado a nadie.

## chequeo-6

```
chequeo-6 db9f11f..bf9583b: avisos para mirar, no un veredicto
producto +8/−3
arnés +406/−58
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12106 → 12111
  AVISO creció una función de más de 150: proyecto_maria/main.py:3391 register 218 → 219, 1 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 1
```

El `AVISO` queda: es un filtro más (`expires_at > ahora`) en el `UPDATE` que `register` ya tenía; sacarlo aparte partiría esa transacción. Partir `register` no está en `COLA-LIMPIEZA.md`: te lo propongo para ahí.

## Archivos de producto

`proyecto_maria/main.py`: `register` (el `UPDATE` de las otras invitaciones)
e `invite_to_organization` (el tope). `CHANGELOG.md`.

## Lo que sigue

D139 (escapar el panel), después D102.

/compact conservar: Dev MARIA (Dev 2), rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP (/respondio), aviso a la PM principal session_01B7FVQspcEHF7PqNv797WNM. ORG-1+D40 entregada en bf9583b (informe en el commit siguiente), base db9f11f; espera veredicto y D151. Sigue D139 (escapar el panel), después D102. Próxima D libre: D152. Nada se publica sin el «dale» de Emi; nunca main; sin secretos; sin datos reales.
