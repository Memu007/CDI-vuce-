# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ENTORNO-2 (D98): **entregada** en `bf92bf9` (2026-11-08)

| Qué | SHAs |
|---|---|
| Rojo antes del arreglo | `4183666` |
| Producto y CHANGELOG | `c8afa6f`, `fb91f5c` (refactor: un solo import de `config` en `main.py`) |
| Pruebas y sabotajes | `cac8924`, `65a689d`, `1b44897`, `633551d` |
| Merge de tu rama (sólo `docs/pm/`) | `bf92bf9` = `0855bee` traído con merge |
| Informe | el commit `docs:` que sigue a `bf92bf9` |
| Base | `1e1f60d` |

**Resultado.** Con `ENVIRONMENT` ausente o con un valor desconocido, los seis controles que pediste se portan como en producción:
- el CSRF bloquea;
- las cookies de sesión y la de CSRF van `Secure`;
- `/docs`, `/redoc` y `/openapi.json` dan 404;
- sin `DATABASE_URL`, la app no arranca en vez de caer a SQLite;
- el VUCE simulado no responde;
- el cobro simulado da 404 aunque esté `ENABLE_SIMULATE_CHARGE=true`.

Todos preguntan a `config.es_desarrollo()`, que vale `True` sólo para `development`, `test` y `testing`, escritos exactos. Esa es tu sugerencia, y además deja una sola definición en lugar de dos. Las suites completas desde base limpia están verdes (abajo).

## Decisiones

**D107. `IS_PRODUCTION` y lo que cuelga de él.** Hay controles que todavía preguntan «¿es `production`?» en vez de «¿no es desarrollo?»:
- `main.py:105`: `IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"`.
- De él cuelgan dos cosas:
  - el fallo por falta de `FRONTEND_URL` (`main.py:223`);
  - el fallo por `ALLOWED_ORIGINS` vacío o `*` (`main.py:406`).
- En `security/security_middleware.py` pasa lo mismo con HSTS (`:62`) y con el pase libre del rate-limit para `127.0.0.1` (`:211`).

Con `ENVIRONMENT` ausente, CORS y FRONTEND_URL caen a localhost en vez de fallar, no se manda HSTS, y desde 127.0.0.1 no hay rate-limit.
- (a) **Recomendada.** Pieza aparte, ENTORNO-3, después de ENTRADAS-2: esos cuatro lugares preguntan a `es_desarrollo()`, con su caso en `test_entorno1` y su sabotaje.
  - Costo: sin `ENVIRONMENT`, la app no arranca hasta que estén `ALLOWED_ORIGINS` y `FRONTEND_URL`. Es lo que pide el criterio de esta pieza, aplicado a dos controles más.
  - Por qué aparte: no estaban en la lista de esta tarea, y el arranque con CORS es una puerta más que hay que probar.
- (b) Dejarlo así, como riesgo. Ninguno de los cuatro abre una puerta de desarrollo: todos dejan menos protegido un despliegue mal configurado.

Próxima D libre: D108.

**Supuesto reversible.** `ENABLE_SIMULATE_CHARGE` ya no se lee en ningún lugar del producto (`grep` en `proyecto_maria/` da vacío). Un despliegue de demostración fuera de desarrollo ya no puede simular el cobro con la bandera. Si hace falta, se vuelve a leer, pero sólo dentro de `es_desarrollo()`.

## Archivos de producto que toqué

- `proyecto_maria/config.py` (+6/−0): `es_desarrollo()`.
- `proyecto_maria/main.py` (+10/−17): docs/redoc/openapi, el valor por omisión de CSRF, `secure=` de las dos cookies y el cobro simulado.
- `proyecto_maria/database/connection.py` (+4/−6): sin `DATABASE_URL`, `RuntimeError` fuera de desarrollo.
- `proyecto_maria/core/vuce_connector.py` (+4/−3): el VUCE simulado, sólo en desarrollo.
- `CHANGELOG.md`: una entrada.

`producto +24/−26`.

## Casos

Siguen el patrón de `test_entorno1`: la sonda (`tests/entorno_sonda.py`) arranca la app en otro proceso con cada `ENVIRONMENT`. Las puertas nuevas se suman como datos al dict `PUERTAS`:
- `csrf_que_solo_avisa`;
- `cookies_sin_secure`;
- `docs_y_openapi`;
- `sqlite_sin_database_url`;
- `vuce_simulado`;
- `cobro_simulado`, que ahora arranca con la bandera puesta.

Los mismos dos casos de siempre las recorren:
- `test_puerta_cerrada_fuera_de_desarrollo`, con los valores `None`, `""`, `production`, `prod`, `staging`, `Development`, `" development"` y `TESTING`;
- `test_puerta_abierta_en_desarrollo`, con `development`, `test` y `testing`.

La sonda arranca con `ENABLE_SIMULATE_CHARGE=true`. Así, una lectura de la bandera al importar también se ve.

## Puertas (sobre `bf92bf9`)

| Puerta | Salida |
|---|---|
| `tests/test_entorno1.py` | `22 passed, 3 warnings in 13.20s` |
| `entorno1.sh bf92bf9` | 10 `ROJO`, `sabotajes sin rojo: 0` |
| `entorno2.sh bf92bf9` | 8 `ROJO`, `sabotajes sin rojo: 0` |
| Suite completa, la mía (`ENVIRONMENT=test`, SQLite), worktree limpio | `bf92bf9`: `5124 passed, 335 skipped, 3 xfailed, 96 warnings in 819.82s (0:13:39)`, `SALIDA suite_mia 0` |
| Suite completa, la de CI (`env -u DATABASE_URL ENVIRONMENT=testing …`), worktree limpio | `bf92bf9`: `5124 passed, 335 skipped, 3 xfailed, 93 warnings in 806.27s (0:13:26)`, `SALIDA suite_ci 0` |
| `chequeo-6.py 1e1f60d bf92bf9` | abajo, `avisos: 0` |
| grep de historia de §6 | vacío |
| `/code-review high` y `/security-review` | abajo |

```
chequeo-6 1e1f60d..bf92bf9: avisos para mirar, no un veredicto
producto +24/−26
arnés +166/−80
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/config.py: 45 → 51
  proyecto_maria/core/vuce_connector.py: 228 → 229
  proyecto_maria/database/connection.py: 163 → 161
  proyecto_maria/main.py: 11988 → 11981
avisos: 0
```

Sabotajes, salida entera:

```
Preparing worktree (detached HEAD bf92bf9)
ROJO  | usuarios demo salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[demo]» «demo no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}» 
ROJO  | login con la contraseña guardada salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[login_con_lo_guardado]» «login_con_lo_guardado no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}» 
ROJO  | webhook sin secreto acepta salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[webhook_sin_secreto]» «webhook_sin_secreto no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}» 
ROJO  | link de reset por consola salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[link_de_reset_en_stdout]» «link_de_reset_en_stdout no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}» 
ROJO  | cobro simulado salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[cobro_simulado]» «cobro_simulado no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}» 
ROJO  | clave JWT de desarrollo salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[clave_jwt_de_desarrollo]» «clave_jwt_de_desarrollo no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}» 
ROJO  | desarrollo sin mirar mayúsculas ni espacios: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[demo]» «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[cobro_simulado]» «cobro_simulado no queda cerrada: {'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}» 
ROJO  | staging cuenta como desarrollo: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[webhook_sin_secreto]» «webhook_sin_secreto no queda cerrada: {'staging': 'abierta'}» 
ROJO  | variable ausente cuenta como desarrollo: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[login_con_lo_guardado]» «login_con_lo_guardado no queda cerrada: {None: 'abierta'}» 
ROJO  | ninguna puerta abre ni en desarrollo: «FAILED tests/test_entorno1.py::test_puerta_abierta_en_desarrollo[demo]» «FAILED tests/test_entorno1.py::test_puerta_abierta_en_desarrollo[cobro_simulado]» «demo no queda abierta: {'development': 'cerrada', 'test': 'cerrada', 'testing': 'cerrada'}» 
sabotajes sin rojo: 0
Preparing worktree (detached HEAD bf92bf9)
ROJO  | la bandera abre el cobro simulado fuera de desarrollo: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[cobro_simulado]» 
ROJO  | CSRF sólo avisa salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[csrf_que_solo_avisa]» «csrf_que_solo_avisa no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}» 
ROJO  | cookie de sesión sin Secure salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[cookies_sin_secure]» 
ROJO  | cookie CSRF sin Secure salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[cookies_sin_secure]» 
ROJO  | openapi abierto salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[docs_y_openapi]» 
ROJO  | docs, redoc y openapi abiertos salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[docs_y_openapi]» «docs_y_openapi no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}» 
ROJO  | SQLite sin DATABASE_URL salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[sqlite_sin_database_url]» «sqlite_sin_database_url no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}» 
ROJO  | VUCE simulado salvo en producción: «FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[vuce_simulado]» «vuce_simulado no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}» 
sabotajes sin rojo: 0
```

Lo primero es `entorno1.sh` y lo segundo `entorno2.sh`. Las dos cargan el arnés común `scripts/testing/sabotajes/_entorno_comun.sh`.

## Autorrevisión

| Quién (modelo, esfuerzo) | Hallazgo | Qué hice |
|---|---|---|
| `/code-review high` | 1. CORS y `FRONTEND_URL` siguen colgando de `IS_PRODUCTION` (`main.py:223`, `:406`) | Fuera de la lista de la tarea: D107 |
| | 2. HSTS (`security_middleware.py:62`) y el pase libre del rate-limit para 127.0.0.1 (`:211`) preguntan por `production` | Igual: D107 |
| | 3, 5, 6 y 7 | Arreglados dentro de la pieza. Su texto no lo conservé al compactar el chat, así que no los detallo de memoria |
| | 4. La raíz es `IS_PRODUCTION` (`main.py:105`); la opción es `IS_PRODUCTION = not es_desarrollo()` | D107 (a). Costo: sin `ENVIRONMENT`, la app no arranca sin `ALLOWED_ORIGINS` y `FRONTEND_URL` |
| | 8 | Tomé sólo la parte del import, en `fb91f5c`. El resto del hallazgo quedaba fuera de alcance |
| | 9. Costo: cerca de 33 imports de la app por corrida de `test_entorno1` y unos 300 por corrida de `entorno2.sh` | Queda. Es el patrón de ENTORNO-1, una sonda por valor; el caso tarda 13 s |
| | 10. `cobro_mp2` manda un header `None` | Es sólo de prueba y no cambia lo que se mide. Queda |
| adversario-opus-alto | Ningún defecto de producto | — |
| | a. Si la bandera se leyera al importar, el caso no lo veía: la sonda la ponía tarde | La sonda arranca con la bandera puesta, en `1b44897`. El sabotaje que lee la bandera al importar da `1 failed` |
| | b. `import os` sin uso en la sonda | Lo saqué, en `633551d` |
| | c. `CSRF_ENFORCE=false` puesto a mano apaga el CSRF en cualquier entorno | Es un override documentado; no es un valor por omisión. Queda, R1 |
| | d. Tarifar simulado no depende del entorno | Pasa por `get_ncm_data`, que ahora bloquea el VUCE simulado. Queda, R2 |
| `/security-review` (subagente, Opus alto) | Ningún hallazgo con confianza ≥ 8. Con `production`, todo queda igual o más estricto; sin `ENVIRONMENT` o con uno desconocido, lo que estaba abierto ahora está cerrado. No queda ninguna lectura de `ENABLE_SIMULATE_CHARGE` | Nota: que Railway defina `ENVIRONMENT` y `DATABASE_URL`. R3 |

## Riesgos

- **R1, baja.** `CSRF_ENFORCE=false` puesto a mano sigue apagando el CSRF también fuera de desarrollo. Es un override explícito, no un valor por omisión.
- **R2, baja.** El modo simulado de Tarifar no mira el entorno. Hoy llega por `get_ncm_data`, que sí bloquea el VUCE simulado. No lo probé por separado.
- **R3, media, para antes de publicar.** Si Railway no define `ENVIRONMENT` o `DATABASE_URL`, desde esta pieza la app no arranca, en vez de arrancar con controles de desarrollo. Es lo pedido, pero conviene confirmar las dos variables en Railway antes del «dale». Yo no tengo acceso a Railway.
- **R4, baja.** Lo que cubre D107 sigue igual que antes de la pieza.
- **R5, baja.** Lo que mide `test_entorno1` cuesta unos 33 arranques de la app por corrida, porque son subprocesos. Hoy son 13 s.

## Comandos copiables

```bash
# desde la raíz, con el venv del proyecto
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
rm -f test.db; python -m pytest -q --no-cov -p no:cacheprovider tests/test_entorno1.py
#   → 22 passed
PY=$(command -v python) scripts/testing/sabotajes/entorno2.sh bf92bf9
#   → 8 líneas ROJO, «sabotajes sin rojo: 0»
PY=$(command -v python) scripts/testing/sabotajes/entorno1.sh bf92bf9
#   → 10 líneas ROJO, «sabotajes sin rojo: 0»
python3 docs/pm/herramientas/chequeo-6.py 1e1f60d bf92bf9
#   → producto +24/−26, avisos: 0
grep -rn ENABLE_SIMULATE_CHARGE proyecto_maria/
#   → vacío
```

/compact conservar: Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi), rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message next. ENTORNO-2 entregada en bf92bf9 (base 1e1f60d), D107 abierta (recomendé a: ENTORNO-3 después de ENTRADAS-2), próxima D libre D108. Sigue D100 (FRONT-422) y después ENTRADAS-2 (D101, D104). Corte de rutinas 2026-11-08 15:50 UTC. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; TXT y proforma reales nunca en el repo.
