# Reproducción de PERMISOS-2, 2026-11-08

Entrega de la Dev técnica: código en `a1db966` (producto `0d65cc3` y
`2082647`), informe en `1f9e9ea`, base `bc5d6b4`. Corrido por la PM desde un
worktree de `a1db966`, venv Python 3.12, sin red y con `GEMINI_API_KEY` vacía.

## Resultado

**Aceptada sobre `a1db966`, sin integrar.** Igual al informe.

| Qué | Salida |
|---|---|
| `chequeo-6.py bc5d6b4 a1db966` | `producto +15/−15`, arnés `+227/−28`, historia vacía, avisos 0 (igual al informe) |
| `sabotajes/permisos2.sh a1db966` | 7 `ROJO`, `sabotajes con falla: 0`, salida 0 |
| `sabotajes/cobro_mp4.sh a1db966` | `BASE  | en verde`, 9 `ROJO`, `sabotajes con falla: 0`, salida 0 |
| `pytest tests/test_permisos2.py tests/test_admin_solo_admin.py` + el caso de cobro nuevo | `35 passed, 17 warnings in 8.86s` (salida 1 sólo por el mínimo de cobertura, que no aplica a una corrida parcial sin `--no-cov`) |
| `PUERTO=8790 ataque_aislamiento.sh` | `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`, «PUERTA G3 PASADA», salida 0 |

La primera corrida del ataque dio salida 1 por `No module named 'fastapi'`:
el script levantó uvicorn con el Python del sistema porque el venv no estaba
primero en el `PATH`. Es del entorno de la PM; con el venv primero dio lo de
arriba.

Mirado a mano: fuera de `_exigir_username_libre` y el arranque, ningún otro
lugar de `proyecto_maria/` usa `_admin_usernames()` ni `ADMIN_USERNAMES`.

La suite completa no la repetí: la Dev la corrió (4702 passed) y el producto
son 15 líneas en `main.py`.

## Adversario Opus alto

No encontró camino a admin sin el rol guardado, ni para quedarse con el rol
registrando un nombre reservado. Revisó: el JWT (los roles del token no se
usan; `get_current_user` lee la base), otros usos de la lista (sólo arranque
y reserva), otras altas o renombres (sólo register, que incluye invitación, y
alta de estudio), unicode y espacios (la regex ASCII los frena), el recorte
de `ADMIN_USERNAMES`, roles con formato raro. Sus pruebas: `54 passed`.

Bajas, sin permisos (van a PERMISOS-3, decidido por la PM):

1. **`\n` al final.** La regex de usuario de `/auth/register` y
   `/api/organizations/create` usa `re.match(r'^…$')`, y `$` acepta un `\n`
   final: `'emi\n'` da 200 y se guarda con el `\n`. No es admin al reiniciar
   (el arranque compara exacto), pero se ve como `emi`.
2. **Mayúsculas.** Con `jefe` en la lista, `Jefe` y `JEFE` se registran;
   sin admin al reiniciar. Misma suplantación visual.

Bajas que quedan como riesgo, sin pieza:

3. Un nombre de la lista sin cuenta no lo puede registrar nadie; el alta de
   una admin nueva es «registrarse y después agregar a la lista» (CHANGELOG).
   Si un nombre ajeno ya existía, el arranque le da el rol y queda guardado.
   Ya pasaba antes.
4. Si el arranque falla, saltea los nombres que faltan y sólo imprime
   «Error creando usuarios demo». No le quita el rol a una cuenta que ya lo
   tenía guardado.

Previo y fuera del diff:

5. La cuenta `demo`/`demo123` se siembra con `roles=["admin"]` en cualquier
   entorno que no sea `ENVIRONMENT=production` exacto (reproducido con
   `development`: login 200, `/api/dev/stats` 200). Es la D99 que espera a
   Emi: confirmar `ENVIRONMENT=production` en Railway antes de publicar.

No corrido: Postgres (el `\n` y las mayúsculas en `=` sobre varchar) ni nada
de producción.
