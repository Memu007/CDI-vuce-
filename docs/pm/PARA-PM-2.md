# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORG-1: lista, **sin entregar** (2026-10-27)

**Estado:** los cinco puntos están hechos. Tienen casos en SQLite, un script
contra Postgres, sabotajes y suite completa. **No la entrego todavía.** Tu
canal dice «`/entregar` espera a que vuelva el cupo», y el cupo de
subagentes y `/code-review` vuelve el 28/10 a las 18:00 UTC. Ahí corro la
autorrevisión independiente y `/security-review`, reproduzco lo que
encuentren y entrego con el timbre. Subo ahora para que el trabajo no se
pierda si el contenedor muere. **No hace falta que la revises todavía.**

**Nada para decidir ahora.** Abajo van los supuestos y dos candidatas a D
(D26 y D27) que no frenan ORG-1.

| Pieza | SHA |
|---|---|
| Casos en rojo antes del producto | `9d727e7` |
| Producto y `CHANGELOG.md` | `e43810b` |
| Sabotajes (9, uno por motivo) | `18f7f25` |
| Carrera de dos invitaciones a la vez, en Postgres | `ddfc798` |
| **SHA probado:** suite, compileall, smoke, aislamiento | **`18f7f25`** |

Entre `18f7f25` y `ddfc798` sólo cambia `scripts/testing/org1_postgres.py`,
que pytest no junta. Tu diff de revisión parte de `ea64a9c`, la punta de tu
rama.

Toqué estos archivos de producto:
- `proyecto_maria/main.py`
- `CHANGELOG.md`

## 1. La premisa: confirmada

Corrí `org1_postgres.py` contra un Postgres 16 local con el código de
`ea64a9c`. El resultado fue `fallas: 15`. Cada 500 trae en el log
`TypeError: can't compare offset-naive and offset-aware datetimes` (15
veces). Es tu sospecha: asyncpg devuelve `expires_at` con zona, y se compara
con `datetime.utcnow()`, que no tiene zona. Validar, registrarse, una
vencida y una usada daban 500 en Postgres. Invitar no daba 500, porque no
compara fechas.

## 2. Qué cambió, por punto

Todo está en `proyecto_maria/main.py`.

1. **Sin 500 en las dos bases.** El registro y `validate_invitation`
   comparan `_utc(expires_at) < datetime.now(timezone.utc)`. `_utc` ya
   existía y toma una fecha sin zona como UTC. Así entran los registros
   viejos de SQLite y los de Postgres, que vienen con zona.
2. **Atada al email.** Al registrarse con `invite_token`, el email del
   registro, ya con `strip().lower()`, tiene que ser el de la invitación. Si
   no, responde 400 «Esta invitación es para otro email. Registrate con el
   email al que te invitaron.». La invitación sigue pendiente y no se crea el
   usuario. Una invitación sin email no deja entrar a nadie. El otro camino
   que pone `organization_id` es `/api/organizations/create`, que es el
   dueño creando su estudio. Sacar un miembro lo vuelve a `None`. No hay
   camino para que una cuenta existente se sume.
3. **Tope del plan.** El tope sale de
   `billing_service.get_plan(org.plan or "premium")["users"]`. Un helper
   nuevo, `_emails_de_miembros`, cuenta los usuarios del estudio, dueño
   incluido.
   - Al invitar: responde 400 «El estudio ya ocupa los {tope} usuarios de
     su plan, contando las invitaciones pendientes.» si miembros más
     pendientes sin vencer llegan al tope.
   - Al registrarse: responde 400 «El estudio ya tiene los {tope} usuarios
     de su plan.» si los miembros ya llegaron. Hace rollback y la invitación
     queda pendiente.
4. **Un solo uso.** Pasos del registro:
   - Gasta la invitación con
     `UPDATE invitations SET status='accepted' WHERE id=… AND status='pending'`.
   - Comprueba `rowcount == 1`; si no, hace rollback y responde 400 «Esta
     invitación ya fue usada».
   - Recién después cuenta el tope.
   - Hace un solo commit con el usuario.

   El estudio se lee con `FOR UPDATE` al invitar y al registrarse.

## 3. Qué deja una carrera

| Carrera | Antes (`ea64a9c`) | Ahora |
|---|---|---|
| Dos registros con la misma invitación, SQLite | `[(200, ''), (500, 'No pudimos procesar tu solicitud…')]` | `[200, 400 «ya fue usada»]`, un usuario, invitación `accepted` |
| Lo mismo, Postgres | dos 500 (el `TypeError`) | `[(200, ''), (400, 'Esta invitación ya fue usada')]` |
| Dos registros con invitaciones distintas por el último lugar, SQLite | `[(200, ''), (200, '')]`: entran los dos | `[200, 400 «los 2 usuarios»]`, miembros 2, `['accepted', 'pending']` |
| Lo mismo, Postgres | dos 500 | `[(200, ''), (400, 'El estudio ya tiene los 2 usuarios de su plan.')], miembros 2, ['accepted', 'pending']` |
| Dos invitaciones enviadas a la vez por el último lugar, Postgres | `[(200, ''), (200, '')], pendientes 2` | `[(200, ''), (400, 'El estudio ya ocupa los 2 usuarios de su plan, contando las invitaciones pendientes.')], pendientes 1` |
| Lo mismo, SQLite | — | **No está protegido** (riesgo abajo) |

Cómo se serializa cada base:
- **SQLite:** el primer `UPDATE` del registro toma el candado de escritura
  de la base. Por eso el tope se cuenta después de gastar la invitación: el
  otro registro espera y cuenta con el primero ya adentro.
- **Postgres:** el `FOR UPDATE` sobre el estudio serializa los registros y
  las invitaciones del mismo estudio.

Las carreras son reales, no secuenciales. En SQLite, dos hilos esperan
juntos en una barrera después del hash de la clave. En Postgres, cada
invitación espera en su commit, ya pasado el control del tope. Espera a que
la otra también llegue al commit o quede frenada en el candado, mirado en
`pg_stat_activity`. No hay esperas fijas: el plazo de 20 s sólo corre si no
pasa ninguna de las dos.

## Supuestos reversibles

- **Las pendientes cuentan por email distinto.** Una pendiente de alguien
  que ya es miembro no cuenta. Reinvitar a un email pendiente no ocupa otro
  lugar y responde 200, como hoy.
- **El `FOR UPDATE` sobre el estudio**, al invitar y al registrarse. Es una
  fila por estudio y por pedido, no un candado global.
- **Los tres textos de error nuevos** (arriba).
- **Una invitación «expired» con fecha futura** responde «ya fue usada»,
  porque no está pendiente. Hoy sólo `validate_invitation` marca «expired»,
  y lo hace con la fecha vencida, así que no debería existir.

## Candidatas a D (no frenan ORG-1)

- **D26. No hay forma de cancelar una invitación pendiente.** Con el tope
  nuevo, una invitación a un email equivocado ocupa un lugar hasta que vence
  a los 7 días.
  - (a) Dejarlo así.
  - (b) Un endpoint chico para que el dueño cancele una pendiente.

  Recomiendo (b) como pieza aparte, porque es funcionalidad nueva y no entra
  en ORG-1.
- **D27. La pantalla de registro no completa el email invitado.**
  `proyecto_maria/templates/landing.html` (~774-794) valida el token pero deja el email vacío. Con el
  punto 3, si el invitado escribe otro email recibe el 400.
  - (a) Dejarlo así.
  - (b) Completar el email con el que devuelve `/api/invitations/{token}`,
    sólo lectura.

  Recomiendo (b), aparte: es pantalla y no entra en ORG-1.

## Puertas

| Puerta | Resultado |
|---|---|
| `tests/test_org1.py` sobre `ddfc798` | `46 passed, 3 warnings in 31.56s` |
| Los mismos casos contra `ea64a9c` | `36 failed, 10 passed, 39 warnings in 45.26s` |
| `org1_postgres.py`, Postgres 16 local, sobre `ddfc798` | `fallas: 0`, 3 de 3 corridas |
| Lo mismo contra `ea64a9c` | `fallas: 15` |
| `sabotaje_org1.sh 18f7f25` | `OK: los 9 sabotajes dan rojo por la razón esperada`, salida 0 |
| Suite completa, worktree limpio en `18f7f25` | `1 failed, 3323 passed, 302 skipped, 2 xfailed, 94 warnings in 505.43s (0:08:25)` |
| `compileall -q proyecto_maria` | rc 0 |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `ataque_aislamiento.sh` | `Bloqueado: 22 · Fugas: 0`, «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.» |

Los casos corren cada uno dos veces, `sqlite_sin_zona` y
`postgres_con_zona`. El segundo inyecta un `expires_at` con zona al cargar
la fila, que es lo que hace asyncpg.

**El único rojo de la suite** es
`test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`.
Es el de tiempo ya informado en SUFIJOS-1, 1c y 1d: «la subida normal dio
400 a los 30.0 s: … tardó demasiado». ORG-1 no toca la lectura de Excel.

**Sabotajes** (`sabotaje_org1.sh`). Cada uno vuelve a lo de antes o rompe
una guarda:

| Sabotaje | Qué hace | Rojos |
|---|---|---|
| `fecha_sin_zona` | vuelve a comparar con `datetime.utcnow()` | 14 failed |
| `sin_email` | cualquiera con el enlace entra | 10 failed |
| `invitar_sin_tope` | invitar sin tope | 13 failed |
| `tope_fijo` | tope 3 escrito a mano | 10 failed |
| `vencida_ocupa` | guarda: una pendiente vencida ocupa lugar | 2 failed |
| `reinvitar_ocupa` | guarda: reinvitar ocupa otro lugar | 1 failed |
| `registro_sin_tope` | registrarse sin tope | 3 failed |
| `gasto_sin_condicion` | gasta sin mirar si seguía pendiente | 2 failed |
| `contar_antes` | cuenta el tope antes de gastar (la carrera de SQLite) | 1 failed |

Dos sabotajes más se aplicaron a mano en Postgres, porque el candado sólo se
ve ahí:
- Sin `FOR UPDATE` al invitar: `FALLA | dos invitaciones a la vez por el
  último lugar: sale una ([(200, ''), (200, '')], pendientes 2)`, 3 de 3.
- Sin `FOR UPDATE` al registrarse: `FALLA | dos invitaciones por el último
  lugar: entra una ([(200, ''), (200, '')], miembros 3, ['accepted',
  'accepted'])`, 3 de 3.

**Lo que no corrí:**
- Subagentes adversariales, `/code-review` ni `/security-review`. No tengo
  cuota hasta el 28/10 a las 18:00 UTC. La autorrevisión del diff completo
  contra `ea64a9c` es sólo mía, sin independencia. Por eso todavía no
  entrego.
- La pantalla en un navegador: no toqué pantallas.

## Comandos

Este muestra sólo lo de ORG-1:

```bash
git diff ea64a9c..ddfc798
```

Este tiene que dar `46 passed`:

```bash
python -m pytest -q --no-cov -p no:randomly tests/test_org1.py
```

Este tiene que dar «OK: los 9 sabotajes dan rojo por la razón esperada» y
salida 0:

```bash
scripts/testing/sabotaje_org1.sh 18f7f25 <venv>
```

Este tiene que dar `fallas: 0`. Usá un Postgres local y descartable; el
script rechaza cualquier host que no sea local:

```bash
python scripts/testing/org1_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/<base>
```

## Riesgos

- **La carrera de dos invitaciones a la vez no está protegida en SQLite.**
  `FOR UPDATE` no hace nada ahí, y la invitación no escribe antes de
  contar. Puede quedar un lugar de más pendiente. Al registrarse, el tope se
  vuelve a controlar, así que no entra un miembro de más. Producción es
  Postgres, y ahí está cubierta.
- **En Postgres puede faltar el índice único de `users.email`.** El modelo
  lo declara, pero no comprobé la base de producción, y no la toco. Ahora la
  carrera del mismo email la frena la invitación, no el índice.
- **El registro con un email de prueba reemplazable** confirma ese borrado
  antes de los controles de la invitación. Es de antes y ORG-1 no lo cambia.
- **El 400 «es para otro email»** dice que el email escrito no es el
  invitado. No dice cuál es. Hace falta el token para preguntar.

Última vuelta: Tue Oct 27 21:50:44 UTC 2026

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. SEPARADORES-1d aceptada. ORG-1 lista y subida SIN ENTREGAR (producto e43810b, sabotajes 18f7f25, carrera PG ddfc798; suite 18f7f25 1 failed conocido de test_excel2, 3323 passed). Pendiente: el 28/10 después de las 18:00 UTC, /entregar ORG-1 con subagentes (hasta alto), /code-review high y /security-review; reproducir lo que encuentren, actualizar este informe y timbre «Dev MARIA: entregué ORG-1 en <SHA>». D26 (cancelar pendiente) y D27 (precargar email) son candidatas, no frenan. Apenas entregues: DESTINO-1, PESO-NETO-1, PRORRATEO-1 esperan datos del despachante. Nunca main, sin push --force, sin datos reales del 24/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
