# Reproducción de ESTUDIO-1 (2026-10-25)

Entrega de la Dev técnica en `claude/dev-tecnica`, informe `c820c74`:
- base `273c153`;
- producto `609ec52` y `8bbfbe6`;
- pruebas `6d4cc89` y `c992715`.

Veredicto en `PARA-DEV.md`: **aceptada sobre `5468581`**, con una pieza que
se suma, **ESTUDIO-1b** (D23). ESTUDIO-1b tiene que estar antes de publicar.

Lo que hace la pieza:
- tabla nueva `estudios`, de la cuenta, con `UNIQUE(owner_username, cuit)`;
- `GET`, `POST` y `DELETE /api/estudios`;
- `estudio_id` en `/generate_maria` y en `/generate_maria/avisos`;
- el CUIT del estudio va al CDDTAGR y manda sobre `cuit_agr` y el perfil;
- selector en la pantalla final y en «Mi perfil».

## Lo que corrió la Dev (informe)

- Suite sobre `7de44b7`: 2469 passed, 102 skipped, 2 xfailed. También
  compileall, humo y ataque G3 (22 bloqueados, 0 fugas).
- `test_estudio1.py`: 26 passed.
- `estudio1.sh`: 37 ROJO, 0 sin rojo.

No corrió: el ataque de aislamiento con estudios, Postgres de punta a punta
(sólo su adversario, sobre `6d4cc89`) ni el e2e con un TXT real.

## Lo que corrí yo, sobre `5468581`

- `tests/test_estudio1.py`: **26 passed, 3 warnings in 20.86s**, rc=0.
- `scripts/testing/sabotajes/estudio1.sh` en `/tmp/rev-3d` (también
  `5468581`): **37 ROJO, «sabotajes sin rojo: 0»**.
  - Una segunda corrida mía, en otra carpeta y con el mismo puerto 8873, dio
    «BASE | la pantalla ya está en rojo» («borrar no pide confirmación»). La
    causa fue mía: su API no pudo tomar el puerto, y la prueba de pantalla le
    habló a la API de la primera corrida justo con ese sabotaje puesto.
  - Sola y en limpio, `pantalla_estudio1.js` dio «PANTALLA ESTUDIO-1 OK» dos
    veces seguidas (puerto 8874). No es un rojo del producto.
- Suite completa: **no corrida** por mí. La pieza no toca lo que la suite
  cubre fuera de `test_estudio1.py`, y la Dev la corrió sobre `7de44b7`.

### Mis negativos (8 passed)

Archivo `tests/test_pm_negativos_estudio1.py`, fuera del repositorio:

| Caso | Resultado |
|---|---|
| TXT con el estudio contra TXT con ese CUIT en `cuit_agr` | iguales: el estudio sólo cambia el CDDTAGR |
| `estudio_id` propio con espacios alrededor | usa el estudio |
| `estudio_id` propio en mayúsculas | 400 «no está en tu cuenta», no cae al perfil |
| `estudio_id` `5`, `[1]`, `{"id":1}`, `true` | 422 |
| `estudio_id` `null`, `"null"`, `"N/A"` | 200 con el CUIT del perfil (hallazgo 2) |
| usar X y después Y | Y pasa a ser el preseleccionado |
| generar con el perfil después de Y | Y sigue preseleccionado (D23) |
| B borra el de A, con el id exacto o con `%20` | 404; A lo sigue usando |
| borrar el preseleccionado | preselección vacía; sin perfil no se genera (400) |
| sin sesión | `GET` y `POST /api/estudios` dan 401 o 403 |

## Adversario (Opus, alto, sobre `c992715`)

No encontró cómo entrar a lo ajeno ni cómo perder datos.

Comprobado corriendo:

1. **Media, es D23.** Con un solo estudio, aunque nunca se haya usado, ese
   estudio queda preseleccionado por encima del CUIT del perfil. Elegir «CUIT
   de mi perfil» en una operación no cuenta como uso: en la siguiente vuelve
   el estudio.
   - En Chromium, la operación 2 sin tocar el selector sale con el CDDTAGR
     del estudio.
   - El selector muestra nombre y CUIT, y la vista previa trae la línea
     `CDDTAGR=`, pero no hay aviso.
2. **Baja.** `estudio_id` `null`, `"null"`, `"None"`, `"N/A"` o `"  "` cae al
   perfil en silencio. El validador `_vacio_escrito` lo trata como vacío, y
   eso contradice el docstring de `_estudio_elegido`. La pantalla nunca lo
   manda: sólo se llega por la API.
3. **Baja.** El alta acepta un nombre invisible (espacio de ancho cero) o
   invertido (U+202E). No es XSS (se pinta con `textContent`) y el nombre no
   va al TXT.
4. **Baja, ya estaba en la base.** `cuit_valido` acepta `00000000000`.

Revisado sin hallazgos, corriendo:
- Aislamiento por `GET`, `DELETE`, `/generate_maria` y `/generate_maria/avisos`,
  con el id exacto, con espacios y en mayúsculas.
- `owner_username` o `id` en el alta no tienen efecto.
- El único camino que escribe el CDDTAGR es `/generate_maria`;
  `/generate_maria_export` no lo tiene.
- La tabla de CUIT: estudio, `cuit_agr`, perfil, y un estudio borrado da 400.
- Duplicado 409 y rollback.
- Las carreras del front: `listo()`, `avisosSeq`, y el selector oculto si
  falla la API.

Sólo razonado, no corrido:
- **Postgres.** `create_all(checkfirst=True)` crea `estudios` en una base
  existente. El FK a `users.username` es válido porque es la clave primaria.
  No hay Alembic.
- **Equipos.** Los estudios no se comparten dentro de un equipo, igual que
  `Client`.
- **Borrado a la vez que se genera.** El TXT sale con el CUIT del estudio
  recién borrado. Hacen falta dos sesiones intercaladas; impacto mínimo.

## Decisión de integración

Acepto, pero **no integro todavía**. `5468581` trae EXCEL-3d, y su H1 (plata
sin aviso) sigue abierta en EXCEL-3e. Si integrara ahora, la rama de la PM
dejaría de poder publicarse.

ESTUDIO-1, CLIENTE-1b y EXCEL-3d entran juntas cuando acepte EXCEL-3e.
ESTUDIO-1 no se publica sin ESTUDIO-1b.

## Cómo repetirlo

```bash
git fetch origin claude/dev-tecnica && git worktree add /tmp/est1 5468581 && cd /tmp/est1
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov --timeout=120 tests/test_estudio1.py          # 26 passed
PY=$(command -v python) PUERTO=8873 scripts/testing/sabotajes/estudio1.sh   # 37 ROJO, 0 sin rojo
```

Mis negativos y la prueba del adversario quedan en el scratchpad de la PM.
