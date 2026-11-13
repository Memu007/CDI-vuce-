# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D223 + D224: entregada en `32f09ba` (el trabajo es de `77cb691`; sólo arnés). Nada para decidir

Traje tu rama (`72c297c`) con `merge` y leí el veredicto: PANTALLAS-MARIA
aceptada, D225 (a), D226 (a), el orden nuevo y el aviso de que
`pantalla_orden1.js` ya es mía para CUIT-PERFIL. Sigo con el lugar 2,
**D226 (a)**.

| qué | SHA |
|---|---|
| base (mi informe anterior) | `8f84886` |
| los dos datos del tope, sus dos sabotajes y el sabotaje del candado | `d4c6ea0` |
| de la autorrevisión: el dato de 60 mide la clave y no el nombre | `77cb691` |
| tu rama `72c297c` integrada: **el que se entrega** | `32f09ba` |
| informe | el commit siguiente |

Las puertas corrieron sobre `77cb691`. Entre `77cb691` y `32f09ba`, fuera de
`docs/`, sólo cambian ocho archivos de pantallas de la Técnica
(`correr_pantallas.sh`, `forzar_arranque.js`, `forzar_orden1.js`,
`pantalla_maria1c.js`, `pantalla_maria7.js`, `pantalla_orden1.js`,
`pantalla_sesion1.js` y `sabotajes/orden1b.sh`): ni el producto, ni `tests/`,
ni mis dos guiones, ni `catalogo3_postgres.py`, ni `con_pg16.sh`. Sobre
`32f09ba` corrí sólo la prueba corta: `10 passed, 97 deselected`.

**Resultado.**

- **D224.** `test_un_proveedor_latino_conserva_su_id` tiene dos datos más:
  una clave de 60 entra entera (`60-entra`) y una de 61 se corta
  (`61-se-corta`). Tu mutación `<=`→`<`, que daba 186 passed, ahora da
  `FAILED tests/test_catalogo3.py::test_un_proveedor_latino_conserva_su_id[60-entra]`.
- **D223.** `catalogo_largo2.sh` tiene un sabotaje más, el 39: la línea que
  pide el candado (`main.py:1354`) cambiada por `pass` da
  `FALLA | dos workers esperan juntos la migración y arrancan los dos: juntos False`.
  El `lock_timeout` (`main.py:1352`) queda sin sabotaje, como riesgo anotado.
- Los dos guiones, enteros, sobre `77cb691`: `catalogo3.sh` 53 `ROJO`, `fallas: 0`, sale 0 (1736 s);
  `catalogo_largo2.sh` con PG16 39 `ROJO`, `fallas: 0`, sale 0 (1539 s).
- Producto **+0/−0**; arnés +18/−2.

## Decisiones

Ninguna.

## Supuestos (reversibles)

1. **Dos sabotajes en `catalogo3.sh` que no pediste** (pediste los dos
   datos): `<=`→`<` y `_MAX_VENDOR_ID = 60`→`70`. Sin ellos, los datos nuevos
   no tenían negativo propio. El guion pasa de 51 a 53 sabotajes.
2. **El dato de 60 es un nombre de 61 caracteres** (`"x"*30 + ", " + "x"*29`)
   cuya clave mide 60 (`"x"*30 + "_" + "x"*29`). Con `"x"*60`, que fue mi
   primera versión (`d4c6ea0`), el nombre y la clave medían lo mismo y medir
   el nombre en vez de la clave pasaba en verde (hallazgo 1).
3. **Una frase en la cabecera de `catalogo3.sh`** que dice dónde están los
   sabotajes que corren el arnés de Postgres (hallazgo 5).
4. **El sabotaje del candado va dentro del bloque `PRUEBA_PG_ITEMS`** de
   `catalogo_largo2.sh`, con el otro que corre `catalogo3_postgres.py`: no
   levanta un Postgres más.

## Para reproducir

```bash
# raíz del repo en 32f09ba (o en 77cb691: para estos comandos es lo mismo); PY = python de un venv con requirements.txt; hace falta node.
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares

# 1) Los datos nuevos, un segundo:
env -u DATABASE_URL -u ENVIRONMENT $PY -m pytest -q --no-cov -p no:cacheprovider tests/test_catalogo3.py -k proveedor_latino
#   → `10 passed, 97 deselected`

# 2) catalogo3.sh entero, unos 29 minutos:
env -u DATABASE_URL -u ENVIRONMENT PY=$PY bash scripts/testing/sabotajes/catalogo3.sh 77cb691 | tee /tmp/c3.out
grep -c '^ROJO' /tmp/c3.out; tail -1 /tmp/c3.out      # → 53 y «fallas: 0»; sale 0
grep 'clave de proveedor de 6' /tmp/c3.out
#   → ROJO  | una clave de proveedor de 60 se corta: dice «FAILED tests/test_catalogo3.py::test_un_proveedor_latino_conserva_su_id[60-entra]»
#   → ROJO  | una clave de proveedor de 61 se guarda entera: dice «FAILED tests/test_catalogo3.py::test_un_proveedor_latino_conserva_su_id[61-se-corta]»

# 3) catalogo_largo2.sh entero con PG16, unos 24 minutos:
env -u DATABASE_URL -u ENVIRONMENT PY=$PY scripts/testing/con_pg16.sh bash -c 'PG_URL="$BACKUP1A_PG_URL" bash scripts/testing/sabotajes/catalogo_largo2.sh 77cb691' | tee /tmp/cl2.out
grep -c '^ROJO' /tmp/cl2.out; tail -2 /tmp/cl2.out    # → 39; la última ROJO es la del candado; «fallas: 0»; sale 0
#   → ROJO  | dos workers migran las claves sin esperarse: dice «FALLA | dos workers esperan juntos la migración y arrancan los dos: juntos False»

# 4) El rojo que motivó el cambio de la autorrevisión (a mano, en una copia descartable):
#    en proyecto_maria/core/catalog_service.py, «if len(clave) <= _MAX_VENDOR_ID:» → «if len(nombre) <= _MAX_VENDOR_ID:»
#    y el comando de 1):
#   → FAILED tests/test_catalogo3.py::test_un_proveedor_latino_conserva_su_id[60-entra]
#   → 1 failed, 9 passed, 97 deselected
#    Con el dato de d4c6ea0 ("x"*60) esa misma mutación daba 188 passed en los cuatro archivos de catálogo
#    (lo corrió el adversario; yo corrí el rojo de arriba, no su verde).
```

## Puertas (sobre `77cb691`)

| puerta | salida |
|---|---|
| `tests/test_catalogo3.py`, `test_catalogo_largo1.py`, `test_catalogo_largo2.py`, `test_catalogo_ncm1.py` (corridos sobre el árbol que después fue `77cb691`, antes de commitear) | `188 passed, 3 warnings in 104.68s` |
| `tests/test_catalogo3.py -k proveedor_latino` | `10 passed, 97 deselected` |
| `catalogo3.sh 77cb691`, entero | 53 `ROJO`, `fallas: 0`, sale 0 (1736 s) |
| `catalogo_largo2.sh 77cb691`, entero, PG16 | 39 `ROJO`, `fallas: 0`, sale 0 (1539 s) |
| la mutación `len(nombre)` sobre `77cb691` | `FAILED tests/test_catalogo3.py::test_un_proveedor_latino_conserva_su_id[60-entra]`; `1 failed, 9 passed, 97 deselected` |
| `tests/test_catalogo3.py -k proveedor_latino`, sobre `32f09ba` | `10 passed, 97 deselected` |
| `anclas_perdidas.py 77cb691` | sale 0; ninguna fila de `catalogo3.sh` ni de `catalogo_largo2.sh` |

**Una corrida cortada, no un rojo.** La primera corrida de
`catalogo_largo2.sh` sobre `77cb691` quedó en 36 de 39: se reinició el
contenedor (mi espera salió con 137 y `uptime` daba 1 minuto). Lo que llegó a
imprimir son 36 `ROJO`, sin `SIN ROJO` ni línea de `fallas`. La corrí de
nuevo, entera y sola: es la de la tabla.

Los mismos dos guiones, enteros, ya habían corrido sobre `d4c6ea0`:
`catalogo3.sh` 53 `ROJO`, `fallas: 0`, sale 0 (1736 s); `catalogo_largo2.sh`
39 `ROJO`, `fallas: 0`, sale 0 (1450 s).

`chequeo-6`, entero:

```
chequeo-6 8f84886..77cb691: avisos para mirar, no un veredicto
producto +0/−0
arnés +18/−2
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Hallazgos de la autorrevisión

Adversario: `adversario-sonnet-alto` (Sonnet, esfuerzo alto), sobre `d4c6ea0`;
corrió pytest con mutaciones en una copia, no corrió Postgres. `/code-review
high` sobre `8f84886..d4c6ea0`: sus revisores heredan Fable. No corrí
`/security-review`: la pieza no cambia la migración, le suma un sabotaje a un
guion.

| # | quién | hallazgo | qué hice |
|---|---|---|---|
| 1 | adversario | Con el dato `"x"*60`, medir el nombre (`len(nombre)`) en vez de la clave pasaba en verde: `188 passed` | **Confirmado** por lectura: el nombre y la clave medían lo mismo. Arreglado en `77cb691`; el rojo, en «Para reproducir» 4 |
| 2 | adversario | La misma mutación con `len(_normalize(nombre))` también pasaba | Queda. Leído, no corrido: para un nombre sólo latino esa cuenta da lo mismo que `len(clave)` (la clave es eso con `_` por espacio), así que con el dato nuevo sigue verde. Se separan sólo en un nombre con letras no latinas, donde la clave suma `~` y 16 cifras: es otra causa, no el borde de 60/61 |
| 3 | adversario, code-review | Las demás mutaciones del tope dan rojo: `<`, 59, 61, 70, corte en 38 o 40, resumen de otro largo, resumen del nombre | Dos las corrió el adversario (`1 failed, 9 passed` cada una), tres el code-review; el resto es lectura. Nada que hacer |
| 4 | adversario | El resumen esperado de la clave de 61 (`c508e75f24e25db94dff`) está bien calculado | Lo recalculó aparte. Nada que hacer |
| 5 | code-review | La cabecera de `catalogo3.sh` manda al arnés de Postgres y no dice qué guion lo sabotea | Arreglado en `77cb691` |
| 6 | adversario | El nombre «60 justos» del sabotaje | Cambiado en `77cb691` |
| 7 | code-review | El sabotaje del candado tarda unos 2 minutos: con el candado sacado, `esperando_candado(2)` espera sus 120 s enteros. Lo midió el revisor (20 s el arnés sano, 132 s saboteado); yo no | Queda. Acortarlo es cambiar `catalogo3_postgres.py`, fuera de la pieza: línea para la cola |
| 8 | code-review, adversario | `juntos False` también es lo que imprime el arnés sano si los dos workers no llegan a esperar a la vez (máquina lenta). Es de antes; nadie lo reprodujo | Queda como riesgo. Si le pasa a la base, `base_en_verde` corta el guion: no da un `ROJO` falso de los otros 38, pero el del candado no distingue ese caso |
| 9 | code-review | El sabotaje muestra que el candado se pide, no que la migración salga mal sin él: los otros 9 chequeos del arnés siguen en `OK` | Es el límite de D223 (a). Lo digo en riesgos |
| 10 | adversario | Las anclas de los tres sabotajes nuevos son código y aparecen una sola vez | Coincide con `anclas_perdidas.py` |
| 11 | adversario | En la lista de datos conviven tuplas y `pytest.param(id=…)` | Queda: los dos nuevos necesitan un id corto y fijo para que el guion los nombre |

**Líneas que propongo para `COLA-LIMPIEZA.md`** (no lo toco):

- `catalogo3_postgres.py`, `esperando_candado`: cortar la espera cuando los
  dos workers ya terminaron, así el paso 2 sin candado falla en segundos y no
  en 120.
- `tests/conftest.py:15-17`: la base temporal `cdi_pytest_*.db` no se borra
  nunca (el comentario dice que la limpia el sistema). En mi contenedor hay
  12712 archivos, 6,5 GiB: cada proceso de pytest deja uno. Borrarla al terminar la sesión de pytest.

## Qué no corrí y riesgos

- **Ni pytest entero, ni `compileall`, ni `smoke_friccion.sh`, ni
  `ataque_aislamiento.sh`, ni `e2e_maria.sh`**: la pieza no toca producto.
  De pytest corrí los cuatro archivos de catálogo.
- **Los cuatro archivos de catálogo no los corrí sobre el commit `77cb691`**
  sino sobre el mismo árbol antes de commitear. Sobre el commit corrieron los
  dos guiones enteros, que arrancan con la base en verde.
- **Los dos guiones enteros no los corrí sobre `32f09ba`**: corrieron sobre
  `77cb691`, y lo que la unión cambia no lo usan (arriba).
- **`lock_timeout` sin sabotaje** (D223 (a)). Dato de antes: sacado, el arnés
  no da una `FALLA` sino un `Traceback` a los ~610 s, en el paso 5.
- **El candado: se ve que se pide, no lo que evita** (hallazgo 9).
- **Cada corrida de `catalogo_largo2.sh` tarda unos 2 minutos más** (hallazgo
  7).
- **`juntos False` por tiempos y no por el sabotaje** (hallazgo 8): no
  reproducido.
- `len(_normalize(nombre))` (hallazgo 2): sigue sin prueba que lo distinga. Lo
  distinguiría un nombre con letras latinas y no latinas cuya clave pase de 60
  sólo por el resumen. No lo agregué: no es lo que pediste.
- El adversario no corrió Postgres: lo del candado lo razonó. Lo corrieron el
  code-review (a mano) y mis dos corridas enteras.

Archivos de producto tocados: ninguno.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 72c297c, ya integrada en 32f09ba), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. Aceptadas: D218, D219 y PANTALLAS-MARIA. Entregada y esperando veredicto: D223 + D224 en 32f09ba (el trabajo es de 77cb691; sólo arnés, producto +0/−0; catalogo3.sh 53 ROJO y catalogo_largo2.sh 39 ROJO, los dos salen 0). Nada abierto para decidir. Ya decididas: D221 (b), D222 (a), D223 (a), D224 (a), D225 (a), D226 (a). Orden de la PM, una pieza a la vez: la que arranco ahora es D226 (a) (catalogo_ncm1, excel1 y maria1b con chromium.launch() sin ruta fija; puerta: las tres verdes en el corredor de mi contenedor). Después: retirar el 13 y el 24 de sabotaje_valor1.sh y reanclar en código el 10 (comentario, línea 108) y el 28 (comentario al final de la línea 187), puerta: valor1 entero da 29 ROJO y sale 0, y su línea sale de sabotajes-conocidos.txt; AJUSTE-BORRADOR (producto en static/v2: primero un caso de pantalla en rojo; corre e2e_maria.sh); CUIT-PERFIL (D225: producto con datos, revisión fuerte; primero el rojo de hoy; PUT /api/user/profile rechaza un CUIT inválido y la pantalla muestra el error; decir qué pasa con los perfiles ya guardados sin cambiar datos; orden1, validacion1, cobro_corte1 y cobro_mp1_v2 pasan a _cuit_perfil.js; la PM ya avisó que pantalla_orden1.js es mía para esa pieza); y los vencidos de sabotajes-conocidos.txt, uno por pieza. No son míos: maria7, maria1c, correr_pantallas.sh, forzar_arranque.js, forzar_orden1.js. Próxima D libre: D227. Una devolución de la PM o la tarea de comparación van primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
