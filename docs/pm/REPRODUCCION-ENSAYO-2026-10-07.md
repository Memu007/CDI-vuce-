# Ataque al candidato del ensayo — 2026-10-07

**Veredicto: se puede publicar si Emi hace antes la lista de Railway de
`NOW.md`** («Para Emi», punto 1).

Subagente de la PM, Opus alto, sólo en local: Postgres 16, una base armada con
el código de julio (`a771693`: 6 usuarios, clientes y operaciones) y el
candidato arrancado encima con `ENVIRONMENT=production`. Primero sobre
`81bcaba` y después sobre `7f1dd2c` (con ADMIN-2): **mismo resultado en todo.**
De `7f1dd2c` a la cabeza de la rama sólo cambian documentos.

## Hallazgos reproducidos

| # | Qué pasa | Qué se hace |
|---|---|---|
| 1 | Al arrancar, toda cuenta `active` con `trial_ends_at` vencido hace más de 7 días pasa a `past_due` (`✅ Billing cron: 2 usuario(s) pasados a past_due`). La de Emi sigue generando el TXT y descargando (200), pero no guarda operaciones nuevas (`402 TRIAL_EXPIRED`). Volver a julio no lo deshace. El esquema queda igual (`pg_dump`: 112 filas antes y después) | Emi, antes: su fila con `billing_status` = `active` **y** `trial_ends_at` futura. Probado: `emi active 2027-10-31` → no se corta, guardar = 200. Con `past_due` y fecha futura → 402: la fecha sola no alcanza |
| 2 | Si `demo`, `premium` o `basico` ya están en la base, entran; `demo` tiene el rol admin guardado y entra al panel (200 en `/api/admin/stats/summary` y `/api/dev/stats`) | Emi los borra. Probado: sin datos propios, `DELETE 3` limpio. Si tienen aunque sea un cliente, falla (`clients_owner_username_fkey`): las 10 claves foráneas a `users` no borran en cascada. Si pasa, Emi avisa |
| 3 | `ADMIN_USERNAMES` ausente, vacía o con un usuario inexistente: arranca sin admin y sin aviso. Con un nombre inexistente, el primero que se registre con ese nombre es admin (reproducido con el registro público) | Emi pone su usuario exacto. El mecanismo es de julio; ADMIN-1 lo hizo la única llave del panel |
| 4 | `ENVIRONMENT=Production` (con mayúscula) no aplica nada de producción: crea los tres demo en la base Postgres, `demo` entra al panel, `/docs` abierto, sin los chequeos de JWT, CORS ni `DATABASE_URL` | Emi pone `production` exacto, en minúsculas |
| 5 | Con `ENVIRONMENT=production`, el arranque exige `DATABASE_URL` (nuevo), `ALLOWED_ORIGINS` y un JWT fuerte (ya en julio). Sin base que responda, no arranca: Railway no da por buena una versión rota | Emi confirma que existan |
| 6 | Menor: a una cuenta que fue `active` sin pago de Mercado Pago se le responde «prueba vencida» | COBRO-CORTE-1 |

Las organizaciones `active` vencidas no se cortan al arrancar sino en el primer
pedido (402). Las cuentas con `trial_ends_at` vacío no se tocan.

## Leído, sin verificar

- Al reiniciar se pierden los archivos del disco del contenedor: los TXT y
  Excel generados, `data/generated/`, el historial de NCM por usuario,
  `localStorage_backup.json`, `error_notes.json`; en memoria, la cuota diaria
  de Gemini y los intentos de login. Ya pasaba en julio. Si el servicio
  tuviera un volumen, los TXT de julio quedarían donde `/download` ya no los
  busca (DISCO-1).
- El webhook de Mercado Pago sólo procesa `type == "payment"`: si las
  renovaciones llegan con otro tipo, el período no se extiende (COBRO-MP-1).

## Fuera de alcance

Con el mismo pedido FOB, el TXT cambia entre julio y el candidato: desaparece
el bloque `CCPL=GTOS-POS-FOB` / `MCPL=0.00` y el `IEXT` pasa de `/25` a `/26`.
Son cambios aceptados; se le dijo a Emi.

## No corrido

Railway, Mercado Pago y renovaciones reales; si el servicio tiene volumen; el
estado real de la cuenta de Emi. La suite sobre el SHA exacto se corre a la
mañana, antes del «dale».
