# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ABUSO1-LIMPIEZA: los dos topes por cuenta de `test_abuso1.py` en un caso

| SHA | qué |
|---|---|
| `00ac6b29` | base |
| `c193af5d` | `test:` un caso con las dos rutas como datos, y las anclas de `reset3.sh`, `abuso1.sh` y `abuso2.sh` |
| este commit | `docs:` informe |

**Nada para decidir.** Producto +0/−0. No hubo adversarios, como pedía la tarea. El nombre de la pieza lo puse yo, porque la tarea no traía uno.

**Supuesto reversible: la rama de reset ahora controla más.** El caso de reset de antes mandaba 4 pedidos seguidos con la misma variante. No veía este caso: que una variante del email (por ejemplo, en mayúsculas) no encontrara la cuenta y aun así llegaran 3 mails. El caso unido toma la forma del de recuperar. Primero pide con `EMAIL`, `Email` y `email`, y comprueba que llegaron 3 mails a la dirección guardada. Recién después hace el cuarto pedido. Así, la rama de reset controla eso también.

### La premisa: es la misma causa

Medí sobre `00ac6b29`, en un worktree descartable, apagando el tope de una ruta por vez: `return mensaje` → `pass` después de `_tope_por_cuenta`.

| tope apagado | `tests/test_abuso1.py` |
|---|---|
| reset | `FAILED tests/test_abuso1.py::test_reset_tres_por_hora_por_cuenta_aunque_cambie_la_ip` · `1 failed, 73 passed, 5 warnings in 28.33s` |
| recuperar | `FAILED tests/test_abuso1.py::test_s6_recuperar_usuario_corta_en_silencio_por_email` · `1 failed, 73 passed, 3 warnings in 28.81s` |
| ninguno | `74 passed, 3 warnings in 28.80s` |

Los dos topes salen del mismo `_tope_por_cuenta`, y cada caso era el único que cuidaba su ruta. Por eso armé un solo caso, `test_tres_por_hora_por_cuenta_aunque_cambie_la_ip[recuperar|reset]`. Recibe la ruta, el mensaje y los links que crea cada mail (0 en recuperar, 1 en reset).

El chequeo de links del reset sigue. Con el cuarto pedido, a los 59 minutos y pasada la hora, se compara `_links_de_reset(u)` con `n × links_por_mail`. En recuperar ese número es 0, así que la misma línea comprueba que recuperar nunca crea un link.

### Los dos rojos, sobre `c193af5d`

Con el mismo sabotaje, en un worktree descartable que ya retiré:

```
== tope por cuenta apagado sólo en: reset
FAILED tests/test_abuso1.py::test_tres_por_hora_por_cuenta_aunque_cambie_la_ip[reset]
================== 1 failed, 73 passed, 3 warnings in 29.87s ===================
== tope por cuenta apagado sólo en: recuperar
FAILED tests/test_abuso1.py::test_tres_por_hora_por_cuenta_aunque_cambie_la_ip[recuperar]
================== 1 failed, 73 passed, 3 warnings in 30.56s ===================
== sin sabotaje
======================= 74 passed, 3 warnings in 29.79s ========================
```

### Puertas, sobre `c193af5d`

| puerta | salida |
|---|---|
| `tests/test_abuso1.py` entero | `74 passed, 3 warnings in 29.79s` |
| `reset3.sh c193af5d` | `BASE \| 74 passed, 5 warnings in 30.73s`; 7 `ROJO`; `SALTO \| sin PG_URL: que contar no suelte la traba no se midió`; `sabotajes sin rojo: 0`; `rc=0` |
| `abuso1.sh c193af5d` | 34 `ROJO`; `sabotajes sin rojo: 0`; `rc=0` |
| `abuso2.sh c193af5d` | `BASE  \| en verde`; 19 `ROJO`; `SIN PG\| el sabotaje de la İ necesita PG_URL: no se corrió`; `fallas: 0`; `rc=0` |
| `ROTO`, `VERDE \|` o `ROJO?` en los tres logs | 0 |
| `anclas_perdidas.py c193af5d` | nada de `test_abuso1.py`. Lo que lista es ajeno a esta pieza: `guardar2.sh:74` (PERDIDA) y seis `SIN ANCLA` de `limpieza1.sh` |
| `chequeo-6.py 00ac6b29 c193af5d` | entero abajo |

```
chequeo-6 00ac6b2954f4c842cf3961360a60893689a8ea8c..c193af5dd50d2e7b8e1576a1e9814c8430e7df79: avisos para mirar, no un veredicto
producto +0/−0
arnés +27/−41
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

Las anclas re-apuntadas están en el mismo commit que el cambio de id:

- `reset3.sh:25` apunta a `[reset]`.
- `abuso1.sh` (en tres lugares) y `abuso2.sh:120` apuntan a `[recuperar]`.

Cada uno de esos sabotajes da su rojo con el texto esperado: por ejemplo, «el cuarto pedido de la hora mandó el mail», «creó un link», «a los 59 minutos ya mandó otro» y «pasada la hora no volvió a mandar».

### Comandos para reproducir

```bash
python -m pytest -q --no-cov tests/test_abuso1.py                        # 74 passed
PY=python bash scripts/testing/sabotajes/reset3.sh c193af5d              # sabotajes sin rojo: 0, sin ROTO
PY=python bash scripts/testing/sabotajes/abuso1.sh c193af5d              # sabotajes sin rojo: 0, sin ROTO
PY=python bash scripts/testing/sabotajes/abuso2.sh c193af5d              # fallas: 0, sin ROTO
python scripts/testing/anclas_perdidas.py c193af5d | grep test_abuso1    # nada
python docs/pm/herramientas/chequeo-6.py 00ac6b29 c193af5d               # producto +0/−0, avisos: 0
```

- **No corrido:**
  - Sin `PG_URL`: el sabotaje de Postgres de `reset3.sh` y el de la İ de `abuso2.sh`.
  - La suite completa: la tarea pide este archivo, los guiones y chequeo-6.
- **Archivos de producto tocados:** ninguno.
- **Riesgos:** ninguno nuevo. Que la rama de reset ahora controle más es el supuesto de arriba.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué ABUSO1-LIMPIEZA (c193af5d + informe); nada para decidir; tests/test_conexiones1.py sin seguimiento (su copia está en el parche); espero veredicto.
