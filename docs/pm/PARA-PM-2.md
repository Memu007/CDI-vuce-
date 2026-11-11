# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PRUEBA-LIMPIAR-1 entregada en 5dd9a6e (base c033db7), sólo pruebas

| commit | qué |
|---|---|
| `5dd9a6e` | test: dos datos más en `test_contar_intentos_usa_la_conexion_del_pedido` |
| (este) | docs: informe |

**Resultado:** los datos «perfil con la clave buena» y «cambiar la clave con
la clave buena» entran en el mismo caso parametrizado. Cada uno hace antes un
intento fallido para que `limpiar` tenga qué borrar, y después exige 200 y una
sola conexión a la vez. Producto sin tocar: `git diff c033db7 5dd9a6e -- proyecto_maria/` da vacío.

**El rojo de aceptación pedido no sale, y no es un defecto de la prueba.**
Con `limpiar` usando su propia conexión (`async with _conn.engine.begin()`),
los 9 datos dan verde (`9 passed, 35 deselected`). La causa es que cada
función de `limites_auth` hace commit antes de volver, y cuando corre
`limpiar` el pedido no tiene ninguna conexión tomada. La de `limpiar` es la
única en uso (sonda: pool `NullPool`, máximo 1). Lo que el caso mide, y lo que
traba el pool, es pedir una conexión mientras se tiene otra; ese sabotaje no
lo hace.

## Decisiones

**D164. Con qué rojo se acepta PRUEBA-LIMPIAR-1.**
- (a) Con un sabotaje que es el defecto que mide el caso: `limpiar` toca la
  sesión del pedido sin commit y, con esa conexión tomada, abre otra. Da rojo
  sólo en los dos datos nuevos (salida abajo).
- (b) Retirar los dos datos: frente al sabotaje de la tarea no distinguen
  nada.
- (c) Pedir otra forma de medir «no usa otra conexión», por ejemplo que
  ninguna conexión salga del engine por fuera de la sesión del pedido. Es más
  código de prueba y lo propondría aparte.

Recomiendo **(a)**. Hoy, con la clave buena, ningún dato pasa por `limpiar`.
Con (a), una versión de `limpiar` que retenga la conexión del pedido mientras
pide otra (el riesgo real de trabar el pool) queda en rojo. Lo que (a) no
cubre lo dice arriba: una conexión aparte en un momento en que el pedido no
tiene ninguna no se ve, y no traba nada.

## Lo que no coincide con tu tarea

Escribiste que, con `descontar` saboteado, el caso «sí da rojo en los siete
casos». No lo reproduzco. Con `descontar` abriendo `engine.begin()` para su
primer DELETE da rojo sólo «login»: `1 failed, 8 passed`. Con `_escribir`
(`sumar_fallo` y `contar`) abriendo su propia conexión, dan rojo sólo «login
sin usuario» y «login con clave mala»: `2 failed, 7 passed`. Perfil y cambiar
la clave con la clave mala siguen verdes. Sin tu cambio exacto no sé qué
sabotaje probaste.

**Riesgo:** por lo mismo, en las rutas que verifican la clave actual el caso
no ve una conexión aparte en `segundos_bloqueado`, `sumar_fallo` ni `limpiar`.
Sólo ve una que se pida mientras el pedido tiene otra. Es la propiedad que
importa para el pool, pero no es «nunca usa otra conexión».

## Comandos

```bash
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov -p no:warnings tests/test_sesion1.py -k contar_intentos   # 9 passed, 35 deselected
```

Rojo de (a), con `limpiar` cambiado a mano y revertido:

```python
async def limpiar(db, clave):
    await db.execute(select(_T.c.clave).where(_T.c.clave == _clave(clave)))
    async with _conn.engine.begin() as c:
        await c.execute(delete(_T).where(_T.c.clave == _clave(clave)))
    await db.commit()
```
```
E   AssertionError: perfil con la clave buena: 2 conexiones a la vez
E   AssertionError: cambiar la clave con la clave buena: 2 conexiones a la vez
FAILED tests/test_sesion1.py::test_contar_intentos_usa_la_conexion_del_pedido[perfil con la clave buena]
FAILED tests/test_sesion1.py::test_contar_intentos_usa_la_conexion_del_pedido[cambiar la clave con la clave buena]
================== 2 failed, 7 passed, 35 deselected in 9.62s ==================
```

Sabotaje de la tarea: `======================= 9 passed, 35 deselected in 9.32s =======================`.

## Puertas sobre 5dd9a6e

| puerta | resultado |
|---|---|
| `tests/test_sesion1.py tests/test_abuso1.py tests/test_abuso2.py` | `136 passed in 121.26s` |
| suite completa, compileall, smoke, aislamiento, golden | no corridos: la pieza sólo toca una prueba |
| subagentes y `/code-review` | no corridos: diff de prueba de 11 líneas, sin producto |

Archivos de producto tocados: ninguno.

## chequeo-6 c033db7 5dd9a6e

```
chequeo-6 c033db7..5dd9a6e: avisos para mirar, no un veredicto
producto +0/−0
arnés +11/−3
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## En curso, sin entregar (corte por límite, 2026-11-11)

MEMORIA-E2E a medias en 195af11 (arreglo d497551, casos 9be52ef y 195af11; e2e_maria.sh dio «E2E MARIA OK» en 195af11). Faltan las puertas completas, la revisión adversarial, `/code-review` y el informe; la reentrega de PRESUPUESTO-CLIENTE-1 no empezó. No es una entrega.
