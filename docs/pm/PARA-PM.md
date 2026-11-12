# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Limpieza de CONEXIONES-1 (sólo arnés)

| SHA | qué |
|---|---|
| `391f5571` | refactor(test): el SQL de «créditos al día» vive sólo en `conexiones1_creditos.py` (`AL_DIA`); natural y pares lo usan |
| `376c8adc` | refactor(test): `_instalar` de la sonda se parte en `_contar_registro`, `_sabotear_close`, `_frenar_lentos` y `_contar_cuerpo`; `_instalar` sólo las llama |
| `e6d938a6` | merge de tu rama (`3ff4e770`), sin choques |
| este commit | informe |

**Resultado:** las dos entradas quedaron hechas, con las puertas en verde. No hay nada para decidir.

**Entradas de `COLA-LIMPIEZA.md` que cerré** (las sacás vos):
- línea 146: `conexiones1_sonda.py` `_instalar` (96 líneas).
- líneas 185-186: el SQL de «créditos al día» en `conexiones1_natural.py` (`CREDITOS`) y en `conexiones1_pares.py`.

**`tests/test_conexiones1.py`:** no es descartable y no lo borré.
- Tiene los 8 casos de la pieza de producto de CONEXIONES-1: «las rutas lentas de RUTAS no retienen una conexión mientras esperan»; por ejemplo, `test_la_espera_no_retiene_conexiones[body-400]` y `test_cuenta_que_no_puede_cargar_y_corta_el_cuerpo`.
- Es la única copia: no está en ninguno de los dos parches guardados.
- Por D184 va en el commit de pruebas de esa pieza, si Emi dice que sí a D182 o a D206 (a). Hasta entonces queda sin seguimiento y nunca entra a `git add`.
- Si preferís no depender de mi contenedor, lo sumo al parche en la próxima pieza: decímelo.

## Puertas

| puerta | resultado |
|---|---|
| `py_compile` de los 4 archivos | compila |
| `chequeo-6.py 618efd8a 376c8adc` | salida entera abajo: producto +0/−0, 0 avisos; `_instalar` pasó de 96 a 9 líneas |
| control de la sonda `sabotajes/conexiones1.sh 618efd8a` (antes de partirla) | 6 BIEN, sale 0 |
| el mismo control sobre `376c8adc` (partida) | 6 BIEN, sale 0; mismas líneas que antes |
| rojo conocido sin la llamada `_sabotear_close(...)` en `_instalar` | `close_cancelado` da salida 0 y «sin conexiones tomadas»: el rojo depende de la función partida |
| natural `N=3` sobre `376c8adc` | filas «al día» con 0/3 mal; `recarga + alta, créditos vencidos` con 3/3 mal y 3 RECARGA PERDIDA (D188) |
| pares sobre `376c8adc` | las 28 filas «créditos al día» dan `ok`; los 5 deadlocks son todos de org con créditos vencidos; sale 1 por esos deadlocks |

**El rojo conocido es `close_cancelado`.** La sonda cancela algunos `AsyncSession.close()` y retiene la sesión; el medidor tiene que salir 1 con «QUEDAN CONEXIONES TOMADAS». Ya daba ese rojo antes de partirla y lo sigue dando.

Además, saqué la llamada a `_sabotear_close` en un worktree descartable: el mismo sabotaje pasó a verde. Así se ve que el rojo sale de la función nueva y no de otra parte.

Salida del control, igual en los dos SHA:
```
BIEN  | sin sabotaje: salida 0, dice «sin conexiones tomadas»
BIEN  | close_cancelado: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | close_cancelado_suelto: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto guarda la sesión sin cerrar: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto suelta la sesión sin cerrar: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto pierde filas de api_logs sin avisar: salida 2, dice «no explican la diferencia»
```

Resumen de natural `N=3` sobre `376c8adc`:
```
recarga + guardado, créditos vencidos: 3/3 rondas con deadlock, 0/3 mal
recarga + guardado, créditos al día: 0/3 rondas con deadlock, 0/3 mal
recarga + maria, créditos vencidos: 3/3 rondas con deadlock, 0/3 mal
recarga + maria, créditos al día: 0/3 rondas con deadlock, 0/3 mal
recarga + alta, créditos vencidos: 0/3 rondas con deadlock, 3/3 mal
recarga + alta, créditos al día: 0/3 rondas con deadlock, 0/3 mal
alta + guardado, créditos vencidos: 1/3 rondas con deadlock, 0/3 mal
alta + cancelar, créditos vencidos: 0/3 rondas con deadlock, 0/3 mal
alta + reactivar, cancelada: 1/3 rondas con deadlock, 0/3 mal
renovación + guardado, prueba vencida: 0/3 rondas con deadlock, 2/3 mal
renovación + guardado, active fuera de gracia: 0/3 rondas con deadlock, 3/3 mal
rondas con deadlock: 8, recargas perdidas: 3, cuentas mal: 5
```
Las filas «al día» quedaron en 0 perdidas y 0 mal, y la cláusula del módulo común se aplica. Lo muestra pares: «al día» da 0 deadlocks, mientras que con créditos vencidos la org da deadlocks en las mismas parejas. Las filas de renovación ya estaban en la entrega K.

`chequeo-6.py 618efd8a 376c8adc`, salida entera:
```
chequeo-6 618efd8a..376c8adc: avisos para mirar, no un veredicto
producto +0/−0
arnés +22/−5
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

**Largos después de partirla:** `_contar_registro` 41, `_sabotear_close` 38, `_frenar_lentos` 32, `_contar_cuerpo` 19 e `_instalar` 9 líneas.

## Comandos para reproducir

```bash
PY=/ruta/venv/bin/python
# 6 BIEN y sale 0 en los dos SHA; la línea de close_cancelado dice «salida 1, dice «QUEDAN CONEXIONES TOMADAS»»
PY=$PY scripts/testing/sabotajes/conexiones1.sh 618efd8a
PY=$PY scripts/testing/sabotajes/conexiones1.sh 376c8adc
# filas «al día» con 0/3 mal; «recarga + alta, créditos vencidos» con 3/3 mal y RECARGA PERDIDA
N=3 PY=$PY scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_natural.py
# todas las filas «créditos al día» en ok
PY=$PY scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_pares.py
# producto +0/−0, avisos: 0
$PY docs/pm/herramientas/chequeo-6.py 618efd8a 376c8adc
# una sola línea, la de conexiones1_creditos.py
grep -n "20 days" scripts/testing/*.py
```

## Qué no corrí y riesgos

- **No corrí** la suite de pytest ni `e2e_maria.sh`: no cambió producto y ningún test importa estos arneses.
- **No corrí** natural con N=10. Con N=3 la puerta pedía otra cosa: que no cambiara qué filas dan mal.
- **No hubo autorrevisión con subagentes ni `/code-review`.** Es un refactor de arnés sin cambio de comportamiento, y lo cubren el control y su versión sin la llamada.
- **Riesgo bajo.** Las listas `marcadas` y `retenidas` del sabotaje siguen vivas en el cierre de `close` dentro de `_sabotear_close`, igual que antes. Si se perdiera `retenidas`, `close_cancelado` dejaría de retener y no daría rojo, y el control sigue dando rojo.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué la limpieza de CONEXIONES-1 (391f5571 + 376c8adc + informe); nada para decidir; tests/test_conexiones1.py sigue sin seguimiento hasta la pieza de producto (D182 / D206 a); espero veredicto, nada «apenas entregues».
