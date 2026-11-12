# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D190: las seis pantallas de la Técnica toman la IP de `_ip_nueva.js`

| SHA | qué |
|---|---|
| `c8247e95` | tu base (avance rápido, sin merge) |
| `6f50e17a` | `test:` `tests/test_conexiones1.py` guardado como `scripts/testing/conexiones1_tests.diff` |
| `0b92e6d8` | `refactor(test):` las seis pantallas usan `require('./_ip_nueva')` |
| este commit | `docs:` informe |

**Nada para decidir.** Sin supuestos agregados. `producto +0/−0`.
`tests/test_conexiones1.py` sigue sin seguimiento; su copia está en el parche.

### A. Parche

En un worktree limpio sobre `6f50e17a`: `git apply --check scripts/testing/conexiones1_tests.diff` → `check=0`; después de aplicarlo, `cmp` contra mi `tests/test_conexiones1.py` → `cmp=0` (iguales).

### B. D190

En `pantalla_cliente1.js`, `_despacho1a`, `_destino1`, `_estudio1`, `_estudio1b` y `_orden1` el comentario y `const ipNueva = () => '10.' + ...` pasan a `const ipNueva = require('./_ip_nueva');`. Las seis pasan `node --check`. Arnés +6/−12.

**Grep** (`grep -rnE "'10\.' *\+|X-Forwarded-For': *'|192\.0\.2" scripts/testing/ --include=*.js --include=*.sh --include=*.py`) da sólo dos líneas: `_ip_nueva.js:3` y `pantalla_orden1.js:1343`.

**Por qué queda el `192.0.2` de `pantalla_orden1.js:1343`:**
- Es para el login (`@limiter.limit("5/minute")` en `/auth/login`), no para el registro, que es lo que D190 cubre.
- Es una secuencia (`'192.0.2.' + (++miradas % 250 + 1)`) y no un azar: dentro de una corrida no se repite hasta la mirada 251, y `enElServidor` se llama en dos lugares (1398 y 1489). No puede chocar consigo misma como la IP fija del rojo.
- El comentario de 1338–1340 ya dice el porqué. Cambiarla a `_ip_nueva` no arregla nada y sumaría azar donde hoy no hay.

**Los 9 guiones sobre `0b92e6d8`**, todos `rc=0`; ningún «BASE» ni «no se puede medir» en los logs:

| guion | ROJO | resultado |
|---|---|---|
| cliente1 | 34 | sabotajes sin rojo: 0 |
| despacho1a | 14 | sabotajes sin rojo: 0 |
| destino1 | 19 | sabotajes sin rojo: 0 |
| estudio1 | 37 | sabotajes sin rojo: 0 |
| estudio1b | 20 | sabotajes sin rojo: 0 |
| orden1 | 76 | sabotajes sin rojo: 0 |
| orden1b | 29 | sabotajes sin rojo: 0 |
| foco_cliente1 | — | «con espera, 80 ms: 100 bien, 0 fallas de 100»; «con espera, en el peor momento: 5 bien, 0 fallas de 5»; control «sin espera, en el peor momento: 0 bien, 5 fallas de 5 (5 con lo de otro campo en la razón social)»; «mediciones con falla: 0»; «tardó 1828 s» |
| foco_perfil | — | NO PIERDE en las tres filas (`#pfEstudioNombre` 3000/3000/3001 ms; `#pfEstudioCuit` y `#pfEmail` 3000/3000/3000 ms) |

**El rojo con IP fija.** Una API (`ENVIRONMENT=development`, limitador activo, el de siempre), una sola base SQLite y 7 corridas seguidas de `pantalla_estudio1b.js`, que registra una vez por corrida. Dos worktrees descartables: uno con `const ipNueva = () => '10.0.0.1';` y otro limpio en `0b92e6d8`.
- IP fija: corridas 1–5 `rc=0` «PANTALLA ESTUDIO-1b OK»; corridas 6 y 7 `rc=1`:
  `FALLA: registro: 429 {"detail":"Demasiados registros desde esta conexión. Intente más tarde."}`. En el log de la API, 2 respuestas 429.
- `_ip_nueva`: corridas 1–7 `rc=0` y OK; 0 respuestas 429.

Es el límite de 5 registros por hora por IP (`main.py`, registro), no una espera vencida. Los guiones normales no lo ven porque cada corrida empieza con base vacía; por eso el rojo usa una sola base.

**chequeo-6**, entero:

```
chequeo-6 c8247e95..0b92e6d8: avisos para mirar, no un veredicto
producto +0/−0
arnés +272/−12
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

El +272 incluye el parche. `6f50e17a..0b92e6d8` sólo: arnés +6/−12, avisos 0.

### Comandos

```bash
git diff c8247e95..0b92e6d8 --stat                       # el parche y las seis pantallas; nada en proyecto_maria/
grep -rnE "'10\.' *\+|X-Forwarded-For': *'|192\.0\.2" scripts/testing/ --include=*.js --include=*.sh --include=*.py
                                                          # sólo _ip_nueva.js:3 y pantalla_orden1.js:1343
git apply --check scripts/testing/conexiones1_tests.diff  # sin salida, rc 0 (en un árbol sin tests/test_conexiones1.py)
python3 docs/pm/herramientas/chequeo-6.py c8247e95 0b92e6d8   # producto +0/−0, avisos: 0
```

### No corrido

- La suite pytest: no hay cambio de producto ni de `tests/` fuera del parche.
- Los armados de `X-Forwarded-For` en Python (`conexiones1_medir`/`cuerpo`, `sesion1_motores`, `email1_motores`, `abuso1_motores`, `abuso2_postgres`): no son pantallas, quedan fuera de D190.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué D190 (6f50e17a + 0b92e6d8 + informe); nada para decidir; tests/test_conexiones1.py sin seguimiento (su copia está en el parche); espero veredicto.
