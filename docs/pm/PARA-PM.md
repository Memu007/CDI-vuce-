# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## INTEGRAR-1 vuelta 2: todo lo que no se había corrido ya está corrido. Ningún rojo viene del merge; D145 a D149 las decidís vos

| Qué | SHA |
|---|---|
| Entrega (este informe) | el commit de este informe, encima de `f9ec94e0` |
| Merge de INTEGRAR-1 | `b9db0ad3` (^1 `0d829b8a` dev-tecnica, ^2 `4db641b0` dev-maria, base `30533fe4`) |
| Producto de esta vuelta | `d26d477b`: `main.py` −2. `register` ya no importa `re` |
| Pruebas y sabotajes de esta vuelta | `e2f923fe` y `2e775aa4` (D140 a), `56756f84`, `f614bafb`, `9b639146`, `6d6efb86`, `ed8d9769`, `1c36ef2a` |
| Suite completa | `f7a45660`: `git diff f7a45660 HEAD -- proyecto_maria tests scripts` da vacío |

**Resultado**
- Ningún rojo nuevo viene del merge. Los únicos que tocan el merge son tres patrones de arnés que quedaron viejos, y el comportamiento es el mismo:
  - `despacho1c`;
  - `despacho1d`;
  - uno de `estudio1`.
- Los demás rojos se reparten así:
  - previos de MARIA: patrones viejos, 429 del límite de registro y el smoke;
  - de la base: los arneses de navegador y un patrón mío de `cobro_mp1`;
  - de entorno: pypdf.

**Puertas en verde**
- Suite completa: 5907 passed.
- Ataques sobre Postgres real: 47 OK, 0 FUGA.
- D140 (a) hecha.

**Mi pedido**
- Necesito un rango de D nuevo. Usé de D144 a D149. Revisé que ninguna de esas aparece en `docs/pm` fuera de este canal y de la línea «Próxima D tuya: D144».

`0231eee` de dev-maria sigue fuera del merge, como dice la tarea.

## Decisiones

**D144. `despacho1a` da rojo en la BASE**
- Es la misma causa que D143 (`36aba873`): la llamada a `goTo` que hace el arranque llega tarde y pisa la navegación de la pantalla.
- Ya tenés tu respuesta en D143 (a) / BORRADOR-1. No hay nada nuevo que decidir. La numero sólo para que quede contestada.

**D145. Los arneses de MARIA chocan con el límite de registro (429)**
- **Qué pasa:**
  - `orden1` y `orden1b` dan 429 en la BASE;
  - `org1b` tiene 2 ROJO?, `validacion1` 3 y `estudio1` 9 de 9;
  - en todos aparece `registro: 429 {"detail":"Demasiados registros desde esta conexión. Intente más tarde."}`.
- **Por qué:**
  - el límite es `registro:h:{ip}` (más de 5 por hora) o `registro:d:{ip}` (más de 20 por día), en `main.py:3385`;
  - todos los sabotajes registran desde 127.0.0.1;
  - dentro del proceso, conftest y datos1 apagan el limitador; con uvicorn aparte, el arnés no puede hacerlo sin un interruptor en el producto, y ese interruptor no va.
- **Opciones:**
  - (a) Que cada sabotaje del arnés mande su propio `X-Forwarded-For`. `get_client_ip` (`core/rate_limit.py:47`) toma la última entrada cuando `TRUSTED_PROXY_HOPS` es 1, que es el valor por defecto. No hay cambio de producto.
  - (b) Que el arnés reuse una cuenta que ya registró.
  - (c) Dejar esos 429 como ROJO?.
- **Recomiendo (a):** es lo más chico, deja el control de producción igual y cada sabotaje vuelve a mostrar su rojo propio.
- Los arneses son de MARIA: la decisión es a quién se la das.

**D146. El límite de login cuenta después de bcrypt**
- Viene del code-review de esta vuelta, fila 1.
- El login entra en `main.py:3197` y `verify_password` corre en `:3238`, antes de sumar al límite.
- Con una clave mala, cada intento paga bcrypt antes de que el límite lo frene. El costo es de CPU, no de acceso: el límite sigue cortando.
- **Opciones:**
  - (a) contar antes de verificar, en una pieza propia con su rojo;
  - (b) dejarlo y anotarlo en la cola de limpieza.
- **Recomiendo (b)** hasta que CONEXIONES-1 mida bcrypt bajo carga. Si la medida muestra que pesa, (a).

**D147. `_LIMITE_AVISOS_MP` vive en cada worker**
- Está en `main.py:11520`, `parse_limite("60/minute")`, y se usa en `:11529` con `limiter.limiter.hit`.
- Sin `REDIS_URL`, `core/rate_limit.py` usa `MemoryStorage`, uno por worker: con N workers el tope real es N×60.
- **Opciones:**
  - (a) dejarlo así y anotar que el tope es por worker;
  - (b) exigir `REDIS_URL` en producción para este límite.
- **Recomiendo (a):** el webhook sin firma ya no cambia nada (COBRO-MP-3), así que el tope sólo protege CPU. Si Railway corre con Redis, ni hace falta.

**D148. `sesion1` es previo de MARIA**
- Es un arnés de MARIA (SESION-1: `539b55b9`, `ce7cd9dd`, `2e62761c`; los tres están sólo en `4db641b0`). En lab3 sobre `56756f84` dio rc=1 en 1845 s.
- **Los dos ROTO y el ROJO? son patrones viejos; los controles siguen en el producto:**
  - ROTO «resetear la clave vuelve a poner active_jti en NULL»: RESET-1 `816eab90` cambió `revocar_sesiones(user)` por `guardar_si_la_clave_sigue(..., active_jti=uuid.uuid4().hex)`.
  - ROJO? «revocar escribe NULL y resucita las viejas»: es la misma causa.
  - ROTO «un email mal escrito»: ENTRADAS-1 `5001831f` llevó el chequeo a `_email_valido(raw_email)`.
- **El VERDE es un hueco del arnés:**
  - «limpiar abre su propia conexión» da VERDE porque ABUSO-2 `1f0bfb04` cambió `limpiar` por `descontar` en el login, así que el sabotaje apunta a un camino por el que ningún caso pasa.
  - No medí si otro caso lo ve.
- Sólo te pido que confirmes la clasificación. Arreglar el arnés le toca a MARIA.

**D149. Patrones de sabotaje que quedaron viejos**
- **Qué abarca.** Son dos grupos:
  - patrones de arneses de MARIA que su propia rama ya había movido;
  - patrones que el merge dejó equivalentes.
- **Causa.** En todos los casos el control sigue en el producto y lo que quedó viejo es la línea que busca el sabotaje. La lista está en la tabla de arneses, con la marca «D149».
- **Opciones:**
  - (a) que cada dueña ponga al día sus patrones: MARIA los suyos, y yo `cobro_mp1` (g) y los tres que el merge dejó equivalentes;
  - (b) que se anoten en la cola de limpieza.
- **Recomiendo (a) para los míos:** son 4 líneas de arnés, y las hago apenas me lo digas.

## D140 (a): hecha

- `e2f923fe` (prueba): el webhook sin `MP_WEBHOOK_SECRET` queda cerrado también en desarrollo.
- `2e775aa4` (sabotajes): los sabotajes del webhook siguen al rechazo en cualquier entorno.
- El producto ya rechazaba así en el merge. En esta pieza no hubo commit de producto.

## Arneses

Están los 57 nombres de la lista «No corrido» de la vuelta 1 (decía «56», pero son 57) más `cobro_mp1` y `cobro_corte1` enteros.

**Dónde corrió cada tanda**

| Tanda | SHA |
|---|---|
| lab3 | `56756f84` |
| lab5 y lab5rep | `c9e9a69c` |
| sab_lab | `80c1afbc` |
| lab15 | `4899fc51` |

**Por qué valen sobre el SHA final**
- De `56756f84` a `c9e9a69c`, en scripts y tests sólo cambiaron excel1, observabilidad1 y punta_a_punta1, y los tres se volvieron a correr.
- En el producto sólo cambió `d26d477b`.
- Ninguno de esos arneses cambió después.

**Cómo leer las marcas**
- «ROTO»: el sabotaje no encontró su patrón.
- «ROJO?»: dio rojo, pero no con el texto esperado.

**Limpios (rc=0, ningún sabotaje con falla)**

| Arnés | Dónde | Nota |
|---|---|---|
| datos1, csrf1, csrf2, csrf3, org1, pa1, permisos1, permisos2, reset1, seguro1, seguro2, sufijos2, excel2, excel2b, excel2c, excel2d, excel3 | lab3 | 17 de 17 |
| front422, guardar2, limpieza1, disco1, email1, entorno1, entorno2, entorno3, entorno4, entradas2, entradas3, entradas4, cobro_mp3, cobro_mp4 | lab5 | entorno2 se volvió a lanzar después de un reinicio del contenedor |
| cobro_corte1 entero | lab5rep | 5271 s, 88 ROJO, BASE, pantalla y lock en verde |
| rendimiento1, rendimiento1d | lab5rep | 11 y 12 ROJO |
| rendimiento1c | lab6 | 18 ROJO con pypdf 6.21.4 (ver Entorno) |
| conexiones1 | `c9e9a69c` | close_cancelado y close_cancelado_suelto: 1 cada uno |
| observabilidad1, excel1 | `6d6efb86` | «sabotajes sin rojo: 0; no corridos: 0» y «sabotajes con falla: 0» |
| punta_a_punta1 | `ed8d9769` o posterior | «sabotajes con falla: 0» |
| guardar1 | `c9e9a69c` | «sabotajes con falla: 0» después de arreglar el arnés en `1c36ef2a` (ver merge) |

**Merge: el patrón del arnés quedó viejo y el comportamiento es el mismo**

| Arnés | Qué dio | Causa |
|---|---|---|
| despacho1c | 1 ROTO «el plan vencido no avisa que no se guardó» | MARIA tiraba `Error('payment_required')` con `err.motivo`. El merge quedó con la forma de dev-tecnica, `err.code='payment_required'`, y `finalize.js:1338-1341` y `upload.js:438` la leen igual. D149 |
| despacho1d | 1 ROTO «la operación vuelve a esperar al catálogo» | Es la misma llamada con más argumentos: `saveOperationToHistory(items, data, carga, foto).then(r => {` en `finalize.js:779`. D149 |
| estudio1 | 1 de sus 2 ROTO «generar no espera la lista de estudios» | El patrón incluye el comentario `// ESTUDIO-1`, que el merge sacó (§6). La línea `if (CDI.estudios) await CDI.estudios.listo();` es igual. D149 |
| guardar1 | 1 ROTO «el NUL vuelve a llegar a la base» | Es un arnés mío: ENTRADAS-2 (`a91c7b8f`) cambió `data = _sin_nul(await request.json())` por `data = _sin_nul(data)`. Ya lo arreglé en `1c36ef2a` y quedó limpio |

**Previos de MARIA: el arnés o el comportamiento ya estaban así en `4db641b0`**

| Arnés | Qué dio | Causa |
|---|---|---|
| maria1b | rc=4, 4 ROTO | SEGURO-1 `4e4a58ba` pasó el saneo a una función. ENTRADAS-2 `28c72f84` pasó los números a `_numero_de_afuera`. D149 |
| despacho1b | rc=1, 6815 s: 8 ROTO + 2 VACÍO + 3 ROJO? | Los 8 patrones tampoco están en `4db641b0` (ENTRADAS-2: `_entero_de_afuera`, `_cuerpo_guardable`). Los 2 VACÍO vienen detrás de su ROTO. D149. Los 3 ROJO? de CPU están en «No corrido» |
| entradas1 | 1 ROTO «los ítems de agrupar sin validar» | En `4db641b0` ya es `Field(default=[], max_length=10000)`, en `main.py:8216`. D149 |
| estudio1 | 26 ROJO, 1 ROTO, 9 ROJO? | Los 9 ROJO? son 429 del registro (D145). El ROTO «los avisos anotan el uso» espera `_items_con_procedencia`, que en `4db641b0` ya es `_textos_como_van_al_txt` (`main.py:4910`). D149 |
| estudio1b | 19 ROJO + 1 ROTO | Es la misma causa que el ROTO de estudio1. D149 |
| cobro_mp2 entero | rc=1, 11791 s, 86 ROJO + 1 ROTO | ROTO «sin la variable de entorno hay demo»: ENTORNO-2 `c8afa6ff` llevó el chequeo a `config.py:15`. BASE y cruces de Postgres en verde. D149 |
| orden1, orden1b, org1b, validacion1 | 429 del registro | D145. orden1b da verde en `0d829b8a` y 429 en la BASE de `4db641b0` |
| sesion1 | 2 ROTO + 1 ROJO? + 1 VERDE | D148 |
| abuso1 | 1 ROTO «vencido el bloqueo…» | ABUSO-2 `59778f92` cambió la línea de `case(...)`. El arnés y el código son iguales en `4db641b0` y en el merge |
| catalogolargo1 | 4 ROTO + 1 ROJO? | CATALOGO-LARGO-2 `1ecab6f1` partió las líneas. El arnés y el código son iguales en `4db641b0` y en el merge |

**Base (dev-tecnica, antes del merge)**

| Arnés | Qué dio | Causa |
|---|---|---|
| destino1, foco_cliente1, despacho1a (y cliente1, de la vuelta 1) | La BASE da rojo con `page.fill` o `locator.click: Timeout 30000ms exceeded.` | Bisección de destino1: `30533fe4` malo, `ebe7b97a` bueno, primer malo `36aba873` (ORDEN-1, mío). El arranque espera al usuario (`ESPERA_USUARIO_MS` 4000) y después hace `goTo('review'/'upload')`, que pisa el `goTo` de la pantalla. Con 6 s de espera, despacho1a da «OK 1280 px» y «OK 390 px», y destino1 da «OK: pantalla DESTINO-1». BORRADOR-1 los tiene que dejar verdes. D143/D144 |
| cobro_mp1 entero | rc=1, 4718 s: 144 ROJO + 1 VERDE esperado + 1 ROTO | ROTO «g: Listo guarda la operación sin el archivo del MARIA»: el patrón dice `.catch(err => {` y hoy la línea es `.then(r => {`, por COBRO-CORTE-1 `1fea5ba5`. Es un arnés mío. D149 |
| rendimiento1b | rc=1, 6 ROJO + 1 ROJO? | El ROJO? salió con código 137: dmesg dice «Memory cgroup out of memory». El defecto saboteado (memoria) se ve; el texto esperado no llega a imprimirse. El arnés es frágil frente al OOM. No lo repetí |

**Entorno**
- La primera corrida de rendimiento1c dio VERDE en «un tope propio de pypdf vuelve a ser un PDF inválido».
- **Causa:** la venv del laboratorio tenía pypdf 6.21.2, y `requirements.txt` pide `>=6.21.4`. Con 6.21.2 la bomba la frena el tope de memoria, con el mismo 400.
- **Con 6.21.4:**
  - 18 ROJO y rc=0, tanto en `c9e9a69c` como con el mismo resultado sobre `4db641b0`;
  - el subconjunto de pruebas de PDF da «530 passed in 225.79s».

## Suite, ataques y smoke

| Puerta | Salida |
|---|---|
| Suite completa, worktree limpio, `f7a45660` | `5907 passed, 110 skipped, 3 xfailed in 1446.16s (0:24:06)` |
| `compileall -q proyecto_maria` | rc=0 |
| Pruebas de PDF con pypdf 6.21.4, `4899fc51` | `530 passed in 225.79s` |
| `ataque_aislamiento.sh`, `TMPDIR=/tmp`, Postgres real, `4899fc51` | «✅ Postgres listo», OK=47, FUGA=0, rc=0 |
| `aislamiento2.sh ataque`, Postgres real, `4899fc51` | «sabotajes con falla: 0», 18 ROJO, rc=0 |
| `smoke_friccion.sh`, `4899fc51` | `[FAIL] POST /api/ui/event`, rc=1. Es previo de MARIA (ver abajo) |

**Hallazgo en los ataques**
- Con `TMPDIR=/tmp/cdi-s1` el ataque no encuentra Postgres y pasa a SQLite sin fallar. Lo único que muestra es «⚠️ Sin Postgres: se usa SQLite temporal.».
- El ataque de la vuelta 1 corrió así, sobre SQLite.
- **Propuesta:** que el ataque falle cuando no hay Postgres, en lugar de seguir. No lo hice porque está fuera de la tarea.

**El smoke**
- ABUSO-1, de MARIA, descarta los eventos sin sesión que no están en la lista («Evento sin sesión no admitido» existe en `4db641b0`, no en `0d829b8a`). El smoke manda `smoke_wave1` sin sesión.
- A mano, con `hero_cta_clicked`:
  - `/api/ui/event` da `{"ok":true}`;
  - `/api/session/state` da `{"ok":true}`;
  - by-cuit da 401.
- El smoke quedó viejo.

## Revisiones

**`/code-review` del merge `b9db0ad3`**

| Fila | Clase | Nota |
|---|---|---|
| 1 | falso positivo | `efaef2b6` sacó `message` a propósito. El `detail` como dict está sólo en el 403 del login y en el 402 de clientes |
| 2 | falso positivo | quien lo usa compara `err.code` |
| 3, 4 | míos, anteriores (`efaef2b6`) | ya estaban antes del merge |
| 5 | anterior en los dos padres | — |
| 6 | mío, después del merge (`68e77ed6`) | es fragilidad, no un verde falso |
| 7, 8, 9 | de MARIA (`a3abd929`, `ce7cd9dd`) | — |
| 10 | del merge, `b9db0ad3` | menor: la lista se arma dos veces |

**`/code-review` de esta vuelta**

| Fila | Hallazgo | Estado |
|---|---|---|
| 1 | el login cuenta después de bcrypt | D146 |
| 2 | `_commit_que_falla` | no es un defecto |
| 3 | `_LIMITE_AVISOS_MP` es por worker | D147 |
| 4 | `finalize.js` | riesgo bajo |
| 5 | `import re` sin uso | arreglado en `d26d477b` |

**`/security-review`**
- Ningún hallazgo con confianza ≥ 8.
- Lo que señaló lo verifiqué en el código: `main.py:11479`, `:2138` y `:2142`.

## chequeo-6

- **Esta vuelta (`19036a2..4899fc51`):** producto +0/−2, 0 avisos.
- **Contra MARIA (`4db641b0..4899fc51`):** da 7 AVISOs. Los siete vienen de piezas de dev-tecnica que ya entregué antes de esta vuelta:
  - el producto suma 286 líneas netas;
  - `try_extract_with_mapping` pasa de 309 a 312;
  - hay dos comentarios de 4 líneas;
  - la función anónima de `finalize.js:9` pasa de 1436 a 1469;
  - `_instalar` tiene 96 líneas;
  - `casosTardios` tiene 67 líneas.
- Ninguno es de esta vuelta.

<details><summary>Salida entera, esta vuelta</summary>

```
chequeo-6 19036a2..4899fc51: avisos para mirar, no un veredicto
producto +0/−2
arnés +49/−26
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12213 → 12211
avisos: 0
```

</details>

**Archivo de producto que toqué en esta vuelta:** `proyecto_maria/main.py`, en `d26d477b`.

## Comandos para reproducir

```bash
git diff f7a45660 HEAD -- proyecto_maria tests scripts        # vacío: la suite vale para el SHA final
git diff 19036a2 HEAD --stat -- proyecto_maria/               # sólo main.py, 2 líneas menos
git show d26d477b -- proyecto_maria/main.py                   # se va el import re de register
git log --oneline 30533fe4..4db641b0 -- proyecto_maria/config.py   # c8afa6ff: el chequeo de entorno de cobro_mp2 se mudó en MARIA
grep -n "_textos_como_van_al_txt(request)" proyecto_maria/main.py  # el patrón nuevo de estudio1 y estudio1b
TMPDIR=/tmp PUERTO=8791 ./scripts/testing/ataque_aislamiento.sh   # «✅ Postgres listo» y FUGA=0; con otro TMPDIR mirar que no diga «Sin Postgres»
```

## No corrido o sin cerrar

- **despacho1b:** los 3 ROJO? de CPU no los reproduje. El arnés borra su tmp y no deja un log por sabotaje, y esa corrida fue en paralelo con cobro_mp2.
- **sesion1:** no lo corrí sobre `4db641b0` solo. La clasificación sale de comparar el código, no de una corrida.
- **rendimiento1b:** no repetí la corrida que murió por OOM.
- **El código que el merge juntó solo** (sin conflicto) no lo leí línea por línea. Lo cubren la suite y los arneses.
- **cobro_mp1:** no verifiqué si otro sabotaje cubre lo mismo que el ROTO (g).
- **pypdf:** la suite completa no la repetí con 6.21.4; sólo el subconjunto de pruebas de PDF.

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. INTEGRAR-1 vuelta 2 entregada con este informe, encima de f9ec94e0; D144-D149 abiertas; pedí un rango de D nuevo. Sigue BORRADOR-1 (D143 a: el goTo tardío del arranque, 36aba873, pisa la navegación; tienen que quedar verdes cliente1, foco_cliente1, destino1 y despacho1a) y después CONEXIONES-1 parte B (lo que tenía a medio hacer está en el parche conexiones1_b_wip.patch del scratchpad). No integrar 0231eee. Rutina trig_011UpBfwEu9TUzoNUrviqoP5 /respondio cada 2 h, minuto 15.
