# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## DESPACHO-1d: **entregada** en `528961b` (2026-11-05)

| Punto | Resultado | Qué decidís |
|---|---|---|
| 1. La operación nunca espera al catálogo | Guardar la operación y aprender el catálogo van a la vez. Con el catálogo colgado o fallando (500, 409, 402, red, `historial_guardado: false`), la operación queda guardada y lo último a la vista es su resultado | Nada |
| 2. Red caída y 402 avisan (D65) | Confirmar NCM y aprender el catálogo avisan con la red caída y con 402, en la misma familia que 500 y 400 | Nada |
| 3. El id de proveedor nunca pasa de 60 (D67) | `.slice(0, 60)`; el caso mira la regla del servidor (`is_valid_vendor_id`), no un número copiado | Nada |
| 4. Sin segundo cliente | Crear A (falla), asignar B (falla), crear otra vez guarda en A. Abrir el panel para la operación siguiente olvida A: el caso `crear-y-otra` da rojo si se saca el reinicio de `clienteCreadoAca` | **D69** |
| 5. «Guardamos este NCM» sólo si se guardó | Con 400, 402, red, `historial_guardado: false` y también `{"success": false}` con 200 (lo encontró la revisión) | Nada |

**Una decisión: D69** (abajo). No te frena: lo entregado hace (a).

**Ojo para publicar, sigue igual:** la rama tiene `e0b8626` (COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a, sin aceptar). Ningún SHA mío sirve para publicar hasta que esas cinco estén ✅.

**Archivos de producto:** `proyecto_maria/static/v2/screens/finalize.js` (`generate`, `saveOperationToHistory`, `saveCatalogLearn`, `renderOrphanPanel`, `orphanCreateSubmit`, el slug del proveedor) y `proyecto_maria/static/v2/screens/ncm.js` (`saveNcmUsage`), más `CHANGELOG.md`. **Producto +64/−45** (neto +19).

### Decisiones

- **D67 (id a 60)** es la D67 que contestaste para esta pieza. La otra D67 (504 SinLugar) sigue siendo pieza aparte después de SESION-1.
- **D69. Reintentar crear después de cambiar el formulario reusa el cliente ya creado, sin aplicarle el cambio.** Caso: creo A «Acme SA», el guardado de la operación falla, corrijo el nombre a «Acme S.A.» y aprieto crear otra vez. La operación se guarda en A, que queda con el nombre viejo. Lo encontró el adversario (hallazgo 2) y `/code-review` (CR2).
  - (a) Reusar siempre el cliente creado en este panel, como está entregado.
  - (b) Reusar sólo si el formulario no cambió; si cambió, crear otro.
  - **Recomiendo (a).** Con (b), corregir un error de tipeo, que es lo más probable al reintentar, deja dos clientes, y uno sin operaciones. Con (a) queda uno, y el nombre se corrige en la ficha del cliente. Si preferís (b), es una pieza chica con su caso.

### SHAs (base `38e743c`)

| SHA | Qué |
|---|---|
| `887ee84` | test: rojos de los cinco puntos. Sobre `fbbb2ad`: `21 failed, 59 passed` (lista abajo) |
| `fc1fc5b` | fix: la operación no espera al catálogo y ninguna falla deja un éxito a la vista |
| `b40fd0d` | test: un sabotaje por punto y los de DESPACHO-1c al día con los patrones nuevos |
| `24b14ec` | refactor: la operación se arma al llamar a guardarla (sin la espera, el tercer parámetro sobraba) |
| `76b6cab` | test: sale el sabotaje 1c «la operación armada tarde» (ver abajo) |
| `629c69a` | docs: CHANGELOG |
| `eeb09c3` | test: rojos de guardar-uso con `{"success": false}` y de la operación que no se arma |
| `0073292` | fix: esos dos |
| `2ce5bd3` | test: sus sabotajes |
| `f714e64` | refactor: guardar-uso cuenta como guardado sólo con `success === true` (sale `res.ok`, que no distinguía nada) |
| `528961b` | test: los sabotajes de guardar-uso apuntan a la línea nueva |

**Rojo sobre `fbbb2ad`** (`tests/test_despacho1c.py`, salida copiada):

```
FAILED tests/test_despacho1c.py::test_lo_que_no_quedo_en_la_memoria_se_avisa[no-guardado-asignar-ncm]
FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[aprender-402]
FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[aprender-red]
FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[confirmar-ncm-402]
FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[confirmar-ncm-red]
FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[asignar-ncm-400]
FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[asignar-ncm-402]
FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[asignar-ncm-red]
FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[asignar-ncm-no-guardado]
FAILED tests/test_despacho1c.py::test_la_operacion_no_espera_al_catalogo[colgado-guardado]
FAILED tests/test_despacho1c.py::test_la_operacion_no_espera_al_catalogo[colgado-500]
FAILED tests/test_despacho1c.py::test_la_operacion_no_espera_al_catalogo[colgado-409]
FAILED tests/test_despacho1c.py::test_la_operacion_no_espera_al_catalogo[colgado-402]
FAILED tests/test_despacho1c.py::test_la_operacion_no_espera_al_catalogo[colgado-red]
FAILED tests/test_despacho1c.py::test_la_operacion_no_espera_al_catalogo[colgado-no-guardado]
FAILED tests/test_despacho1c.py::test_la_operacion_no_espera_al_catalogo[402-guardado]
FAILED tests/test_despacho1c.py::test_la_operacion_no_espera_al_catalogo[red-guardado]
FAILED tests/test_despacho1c.py::test_el_proveedor_cumple_la_regla_del_servidor[acentos-largo]
FAILED tests/test_despacho1c.py::test_el_proveedor_cumple_la_regla_del_servidor[61]
FAILED tests/test_despacho1c.py::test_el_proveedor_cumple_la_regla_del_servidor[corte-en-espacio]
FAILED tests/test_despacho1c.py::test_cada_cliente_nuevo_se_crea_una_vez[crear-asignar-crear-respuesta0-1]
21 failed, 59 passed, 3 warnings in 4.75s
```

`crear-y-otra` (el reinicio de `clienteCreadoAca`) ya pasaba en `fbbb2ad`: el reinicio estaba. Su rojo es el sabotaje «el panel nuevo no olvida el cliente creado».

**Rojo sobre `eeb09c3`** (los casos que trajo la revisión, sin el arreglo de `0073292`; guardar-uso rechazado da rojo al confirmar y al asignar NCM; salida copiada):

```
FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[confirmar-ncm-rechazado]
FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[asignar-ncm-rechazado]
FAILED tests/test_despacho1c.py::test_si_la_operacion_no_se_arma_se_avisa - A...
=================== 3 failed, 80 passed, 3 warnings in 4.61s ===================
```

### Revisión

| Hallazgo | Quién (modelo, esfuerzo) | Qué hice |
|---|---|---|
| guardar-uso contesta 200 con `{"success": false}` y salía «Guardamos este NCM» | `/code-review high` (CR1) y adversario Sonnet alto (hallazgo 3) | Reproducido y arreglado (`eeb09c3`, `0073292`) |
| Si armar la operación lanza, la pantalla queda callada | `/code-review high` (CR3) | Regresión de la pieza: reproducida y arreglada, avisa «No se guardó al cliente» |
| Carrera entre el aviso del catálogo y el de la operación | adversario (hallazgo 1), CR7 | No reproducible: los toasts se reemplazan y el de la operación siempre queda último. Saqué el caso de ticks que había escrito, porque no distinguía nada |
| Reusar A después de cambiar el formulario | adversario (hallazgo 2), CR2 | **D69** |
| El aviso «cliente activo» sin cliente | CR4 | Ya estaba antes de la pieza: riesgo bajo, no lo toqué |
| `armarOperacion` lee la operación viva | CR5 | Descartado: nada la cambia en el lugar |
| Sin `.catch` en el catálogo | CR6 | Descartado: todo lo que puede lanzar en `saveCatalogLearn` está dentro de su `try`, que devuelve false |
| Comentario de `armarOperacion` desactualizado | CR9 | Corregido: «Lee el cliente y la operación en el momento en que se llama.» |
| El slug del proveedor se arma distinto en el navegador y en el servidor | CR8 | Propuesta: que el navegador no lo arme y use el que devuelve el servidor. Fuera de alcance |
| La pista de NCM sólo sale en el destacado | CR10 | Propuesta, fuera de alcance |

`/security-review` no se corrió: la pieza cambia avisos de pantalla y el orden en que el navegador llama a endpoints que ya existían. No toca permisos, sesión ni lo que guarda el servidor.

**Sale un sabotaje de DESPACHO-1c (`76b6cab`).** «La operación se arma tarde» daba verde: sin la espera por el catálogo, armarla antes o en la llamada pasa en el mismo instante. Lo cubre el sabotaje 1d «la operación vuelve a esperar al catálogo», que pone rojo `colgado-guardado`.

### chequeo-6 38e743c 528961b (salida entera)

```
chequeo-6 38e743c..528961b: avisos para mirar, no un veredicto
producto +64/−45
arnés +281/−61
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/screens/finalize.js: 1426 → 1436
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/finalize.js:9 <anónima> 1418 → 1428, 1 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/ncm.js: 2341 → 2350
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/ncm.js:7 <anónima> 2335 → 2344, 2 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 2
```

Los dos AVISOs son el envoltorio del módulo (la función anónima que encierra todo el archivo), no una función: lo nuevo va en funciones propias. Partir `finalize.js` por pantalla ya está en la cola de limpieza.

### Puertas, sobre `528961b`

| Puerta | Salida |
|---|---|
| Suite completa, worktree limpio | `4895 passed, 355 skipped, 3 xfailed, 102 warnings in 698.41s (0:11:38)`, `pytest 0` |
| `compileall -q proyecto_maria` | `compileall 0` |

El log de la suite trae 447 líneas «Task was destroyed but it is pending!». El log de RENDIMIENTO-1d sobre `558c941` trae las mismas 447: son de antes de esta pieza y no hacen fallar ningún caso.
| `despacho1d.sh 528961b` | 9 ROJO, `fallas: 0` |
| `despacho1c.sh 528961b` | 15 ROJO, `fallas: 0` |
| `smoke_friccion.sh`, `ataque_aislamiento.sh` | No corridos: la pieza no toca backend, datos, sesión ni permisos |

Los sabotajes de 1d (salida copiada):

```
ROJO  | la operación vuelve a esperar al catálogo: dice «FAILED tests/test_despacho1c.py::test_la_operacion_no_espera_al_catalogo[colgado-guardado]»
ROJO  | aprender el catálogo con la red caída no avisa: dice «FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[aprender-red]»
ROJO  | confirmar la posición con la red caída no avisa: dice «FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[confirmar-ncm-red]»
ROJO  | el id de proveedor vuelve a llegar a 64: dice «FAILED tests/test_despacho1c.py::test_el_proveedor_cumple_la_regla_del_servidor»
ROJO  | el panel nuevo no olvida el cliente creado para la operación anterior: dice «FAILED tests/test_despacho1c.py::test_cada_cliente_nuevo_se_crea_una_vez[crear-y-otra-True-2]»
ROJO  | asignar otro entre medio hace que volver a crear cree otro: dice «FAILED tests/test_despacho1c.py::test_cada_cliente_nuevo_se_crea_una_vez[crear-asignar-crear-respuesta0-1]»
ROJO  | «Memoria activada» aparece aunque el guardado falle: dice «FAILED tests/test_despacho1c.py::test_lo_que_no_quedo_en_la_memoria_se_avisa[no-guardado-asignar-ncm]»
ROJO  | guardar-uso rechazado vuelve a contar como guardado: dice «FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[asignar-ncm-rechazado]»
ROJO  | la operación que no se arma vuelve a quedar callada: dice «FAILED tests/test_despacho1c.py::test_si_la_operacion_no_se_arma_se_avisa»
fallas: 0
```

### Riesgos

- El arnés es un DOM falso en `node vm`: comprueba el orden de llamadas y lo último a la vista, no un navegador real.
- CR4 (arriba), ya estaba antes.

### Comandos

```bash
git checkout 528961b
PY=<venv>/bin/python scripts/testing/sabotajes/despacho1d.sh 528961b   # 9 ROJO, «fallas: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/despacho1c.sh 528961b   # 15 ROJO, «fallas: 0»
env GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares \
  python -m pytest -q --no-cov -p no:cacheprovider tests/test_despacho1c.py                        # 83 passed
python docs/pm/herramientas/chequeo-6.py 38e743c 528961b                                           # la salida de arriba
```

**Encima de `528961b`** están RENDIMIENTO-1d (hasta `558c941`), el merge `2a87aca` de tu `343a1b5` (sólo `docs/pm/`), su informe `d71b285` y este informe.
