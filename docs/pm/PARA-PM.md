# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## INTEGRAR-1 vuelta 2: todo lo que no se había corrido ya está corrido. Tres ROTO son del merge, con el mismo comportamiento; D145 a D149 las decidís vos

| Qué | SHA |
|---|---|
| Entrega (este informe) | el commit de este informe, encima de `f9ec94e0` |
| Merge de INTEGRAR-1 | `b9db0ad3` (^1 `0d829b8a` dev-tecnica, ^2 `4db641b0` dev-maria, base `30533fe4`) |
| Producto de esta vuelta | `d26d477b`: `main.py` −2. `register` ya no importa `re` |
| Pruebas y sabotajes de esta vuelta | `e2f923fe` y `2e775aa4` (D140 a), `56756f84`, `f614bafb`, `9b639146`, `6d6efb86`, `ed8d9769`, `1c36ef2a` |
| Suite completa | `f7a45660`: `git diff f7a45660 HEAD -- proyecto_maria tests scripts` da vacío |

**Resultado**
- Del merge vienen tres ROTO: patrones de arnés que quedaron viejos, con el comportamiento igual. Ningún control se perdió:
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

Están los 56 nombres de la lista «No corrido» de la vuelta 1, más `cobro_mp1` y `cobro_corte1` enteros. Además corrí abuso1, catalogolargo1 y nombres1.

**Dónde corrió cada tanda**

| Tanda | SHA |
|---|---|
| lab2 | `2e775aa4`: primera tanda. Todo lo que corrió ahí se volvió a correr en otra tanda |
| lab3 | `56756f84` |
| lab5, lab5rep, lab6 y lab14 | `c9e9a69c` |
| lab8 | `6d6efb86` (excel1 y observabilidad1, después de arreglar sus arneses) |
| lab10 | `ed8d9769` (punta_a_punta1, después de arreglar su arnés) |
| sab_lab | `80c1afbc`: commit de laboratorio fuera de la rama, padre `50682549`. Su producto es el de `c9e9a69c` con el `import re` que saca `d26d477b`; abuso1, catalogolargo1 y cliente1 no cambian entre los dos |
| lab15 | `4899fc51` |
| lab4, lab6, lab7, lab9, lab11, lab13 | `0d829b8a` y `4db641b0` por separado, y la bisección de `30533fe4..ebe7b97a`: sirven para clasificar, no son la corrida del SHA final |

**Por qué valen sobre el SHA final**
- De `56756f84` a `c9e9a69c`, en scripts y tests sólo cambiaron excel1, observabilidad1 y punta_a_punta1, y los tres se volvieron a correr (lab8 y lab10).
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
| nombres1 | lab14 | «sabotajes con falla: 0» |
| conexiones1 | lab6 | close_cancelado y close_cancelado_suelto: 1 cada uno |
| observabilidad1, excel1 | lab8 | «sabotajes sin rojo: 0; no corridos: 0» y «sabotajes con falla: 0» |
| punta_a_punta1 | lab10 | «sabotajes con falla: 0» |
| guardar1 | lab6 | «sabotajes con falla: 0» después de arreglar el arnés en `1c36ef2a` (ver merge) |

**Merge: el patrón del arnés quedó viejo y el comportamiento es el mismo**

| Arnés | Tanda | Qué dio | Causa |
|---|---|---|---|
| despacho1c | lab5 | 1 ROTO «el plan vencido no avisa que no se guardó» | MARIA tiraba `Error('payment_required')` con `err.motivo`. El merge quedó con la forma de dev-tecnica, `err.code='payment_required'`, y `finalize.js:1338-1341` y `upload.js:438` la leen igual. D149 |
| despacho1d | lab5 | 1 ROTO «la operación vuelve a esperar al catálogo» | Es la misma llamada con más argumentos: `saveOperationToHistory(items, data, carga, foto).then(r => {` en `finalize.js:779`. D149 |
| estudio1 | lab5 | 1 de sus 2 ROTO «generar no espera la lista de estudios» | El patrón incluye el comentario `// ESTUDIO-1`, que el merge sacó (§6). La línea `if (CDI.estudios) await CDI.estudios.listo();` es igual. D149 |
| guardar1 | lab5; arreglado, lab6 | 1 ROTO «el NUL vuelve a llegar a la base» | Es un arnés mío: ENTRADAS-2 (`a91c7b8f`) cambió `data = _sin_nul(await request.json())` por `data = _sin_nul(data)`. Ya lo arreglé en `1c36ef2a` y quedó limpio |

**Previos de MARIA: el arnés o el comportamiento ya estaban así en `4db641b0`**

| Arnés | Tanda | Qué dio | Causa |
|---|---|---|---|
| maria1b | lab5 | rc=4, 4 ROTO | SEGURO-1 `4e4a58ba` pasó el saneo a una función. ENTRADAS-2 `28c72f84` pasó los números a `_numero_de_afuera`. D149 |
| despacho1b | lab5 | rc=1, 6815 s: 8 ROTO + 2 VACÍO + 3 ROJO? | Los 8 patrones tampoco están en `4db641b0` (ENTRADAS-2: `_entero_de_afuera`, `_cuerpo_guardable`). Los 2 VACÍO vienen detrás de su ROTO. D149. Los 3 ROJO? de CPU están en «No corrido» |
| entradas1 | lab5 | 1 ROTO «los ítems de agrupar sin validar» | En `4db641b0` ya es `Field(default=[], max_length=10000)`, en `main.py:8216`. D149 |
| estudio1 | lab5 | 26 ROJO, 1 ROTO, 9 ROJO? | Los 9 ROJO? son 429 del registro (D145). El ROTO «los avisos anotan el uso» espera `_items_con_procedencia`, que en `4db641b0` ya es `_textos_como_van_al_txt` (`main.py:4910`). D149 |
| estudio1b | lab5 | 19 ROJO + 1 ROTO | Es la misma causa que el ROTO de estudio1. D149 |
| cobro_mp2 entero | lab5rep | rc=1, 11791 s, 86 ROJO + 1 ROTO | ROTO «sin la variable de entorno hay demo»: ENTORNO-2 `c8afa6ff` llevó el chequeo a `config.py:15`. BASE y cruces de Postgres en verde. D149 |
| orden1, orden1b, org1b, validacion1 | lab3 | 429 del registro | D145. orden1b da verde en `0d829b8a` y 429 en la BASE de `4db641b0` |
| sesion1 | lab3 | 2 ROTO + 1 ROJO? + 1 VERDE | D148 |
| abuso1 | sab_lab | 1 ROTO «vencido el bloqueo…» | ABUSO-2 `59778f92` cambió la línea de `case(...)`. El arnés y el código son iguales en `4db641b0` y en el merge |
| catalogolargo1 | sab_lab | 4 ROTO + 1 ROJO? | CATALOGO-LARGO-2 `1ecab6f1` partió las líneas. El arnés y el código son iguales en `4db641b0` y en el merge |

**Base (dev-tecnica, antes del merge)**

| Arnés | Tanda | Qué dio | Causa |
|---|---|---|---|
| destino1, foco_cliente1, despacho1a (y cliente1, de la vuelta 1) | destino1 lab5rep y lab6, foco_cliente1 lab5, despacho1a lab14, cliente1 sab_lab | La BASE da rojo con `page.fill` o `locator.click: Timeout 30000ms exceeded.` | Bisección de destino1: `30533fe4` malo, `ebe7b97a` bueno, primer malo `36aba873` (ORDEN-1, mío). El arranque espera al usuario (`ESPERA_USUARIO_MS` 4000) y después hace `goTo('review'/'upload')`, que pisa el `goTo` de la pantalla. Con 6 s de espera, despacho1a da «OK 1280 px» y «OK 390 px», y destino1 da «OK: pantalla DESTINO-1». BORRADOR-1 los tiene que dejar verdes. D143/D144 |
| cobro_mp1 entero | lab5rep | rc=1, 4718 s: 144 ROJO + 1 VERDE esperado + 1 ROTO | ROTO «g: Listo guarda la operación sin el archivo del MARIA»: el patrón dice `.catch(err => {` y hoy la línea es `.then(r => {`, por COBRO-CORTE-1 `1fea5ba5`. Es un arnés mío. D149 |
| rendimiento1b | lab5rep | rc=1, 6 ROJO + 1 ROJO? | El ROJO? salió con código 137: dmesg dice «Memory cgroup out of memory». El defecto saboteado (memoria) se ve; el texto esperado no llega a imprimirse. El arnés es frágil frente al OOM. No lo repetí |

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

| Fila | Hallazgo | Clase | Nota |
|---|---|---|---|
| 1 | `finalize.js:766`: se fue el respaldo de `detail.message`, y un `detail` objeto da `new Error(obj)` | falso positivo | `efaef2b6` sacó `message` a propósito. El `detail` como dict está sólo en el 403 del login y en el 402 de clientes |
| 2 | `app_v2.js:83`: el 402 deja 'payment_required' sólo en `err.code` | falso positivo | quien lo usa compara `err.code` |
| 3 | `main.py:8114`: `save_client_operation` confía en un `operacion_id` propio y le pisa `client_id` e ítems | mío, anterior (`efaef2b6`) | ya estaba antes del merge |
| 4 | `main.py:7733`: `delete_cliente` deja `generated_file` y el TXT se sigue bajando | mío, anterior (`efaef2b6`) | ya estaba antes del merge |
| 5 | `finalize.js:1210`: el reintento guarda sin carga ni foto | anterior en los dos padres | — |
| 6 | `test_cobro_corte1.py:830`: comparar `co_filename` con `main.__file__` es frágil | mío, después del merge (`68e77ed6`) | es fragilidad, no un verde falso |
| 7 | `main.py:3385`: el `or` corta antes y no suma al contador diario | de MARIA (`a3abd929`) | — |
| 8 | `main.py:3397`: `if request.email:` siempre es verdadero | de MARIA (`dea64a7c`, ENTRADAS-1) | `_email_valido` ya devuelve el email o da 400, así que la guarda quedó de más |
| 9 | `main.py:3381`: el comentario «ABUSO-1, C9» rompe §6 | de MARIA (`a3abd929`) | — |
| 10 | `main.py:7737`: la lista de ids se arma dos veces | del merge, `b9db0ad3` | menor |

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

- **Esta vuelta (`19036a2..cbbd37b2`):** producto +0/−2, 0 avisos.
- **Contra MARIA (`4db641b0..cbbd37b2`):** da 7 AVISOs. Los siete vienen de piezas de dev-tecnica que ya entregué antes de esta vuelta (el `git blame` de la línea de cada aviso y el `git log -L` de las dos funciones que crecieron caen en commits de `0d829b8a`):
  - el producto suma 286 líneas netas;
  - `try_extract_with_mapping` pasa de 309 a 312;
  - hay dos comentarios de 4 líneas;
  - la función anónima de `finalize.js:9` pasa de 1436 a 1469;
  - `_instalar` tiene 96 líneas;
  - `casosTardios` tiene 67 líneas.
- Ninguno es de esta vuelta. Quedan porque partir o achicar código ya entregado va a `COLA-LIMPIEZA.md`, no dentro de una integración (§6).
- Después de `cbbd37b2` sólo va el commit de este informe, que toca sólo `PARA-PM.md`.

<details><summary>Salida entera, esta vuelta</summary>

```
chequeo-6 19036a2..cbbd37b2: avisos para mirar, no un veredicto
producto +0/−2
arnés +49/−26
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12213 → 12211
avisos: 0
```

</details>

<details><summary>Salida entera, contra MARIA</summary>

```
chequeo-6 4db641b0..cbbd37b2: avisos para mirar, no un veredicto
producto +727/−441
  AVISO producto suma 286 líneas netas: el informe dice por qué (§6: más de 20)
arnés +5814/−1044
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/auth/roles.py: 27 → 26
  proyecto_maria/database/models.py: 614 → 617
  proyecto_maria/main.py: 12078 → 12211
  AVISO creció una función de más de 150: proyecto_maria/main.py:5588 try_extract_with_mapping 309 → 312, 3 en su propio cuerpo (§6: lo nuevo va aparte)
  AVISO comentario nuevo de 4 líneas: proyecto_maria/main.py:2143 (§6: una o dos)
  proyecto_maria/security/file_security.py: 693 → 798
  AVISO comentario nuevo de 4 líneas: proyecto_maria/security/file_security.py:363 (§6: una o dos)
  proyecto_maria/services/billing_service.py: 407 → 418
  proyecto_maria/static/v2/app_v2.js: 1199 → 1201
  proyecto_maria/static/v2/screens/clientes.js: 2211 → 2211
  proyecto_maria/static/v2/screens/finalize.js: 1444 → 1477
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/finalize.js:9 <anónima> 1436 → 1469, 6 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/profile.js: 613 → 613
  proyecto_maria/static/v2/screens/upload.js: 718 → 718
  AVISO función nueva de 96 líneas: scripts/testing/conexiones1_sonda.py:59 _instalar (§6: ~60)
  AVISO función nueva de 67 líneas: scripts/testing/pantalla_cobro_corte1.js:33 casosTardios (§6: ~60)
avisos: 7
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
