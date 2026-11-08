# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-MP-2+3 (vuelta 3), PERMISOS-1 y BACKUP-1a, entregadas en `ca84c5f` (informe en el commit de arriba)

Bases:
- COBRO-MP-2+3 y PERMISOS-1: `ac52d6f`, el merge de tu rama antes de empezar.
- BACKUP-1a: `b831905`, la punta de LIMPIEZA-1, sobre la que arrancó.

Encima de `ca84c5f` hay merges de tu rama, que traen `docs/pm` (el último trae tu `6f9d0c1`, con EXCEL-2c aceptada), los commits de EXCEL-2c y los de EXCEL-2d (`ac11cd8` a `e02dd76`). EXCEL-2d está subida pero no entregada: su informe va aparte. Ninguna de las dos toca los archivos de estas tres piezas, salvo `CHANGELOG.md`. El producto y las pruebas que se entregan acá son los de `ca84c5f`.

### Resultado

1. **COBRO-MP-2+3: el reintento de cancelar concilia.**
   - Si quien abrió la suscripción, o la dueña, recibe el 503 y Mercado Pago sí la canceló, al reintentar recibe 200.
   - El estudio queda `canceled`, el sid se borra y `/billing/me` da `renueva: False`.
   - Si otra suscripción del estudio sigue pagando, el reintento da 403 y no cambia nada.
   - Cancelar deja la suscripción que paga para el final. Un corte a mitad deja canceladas las demás, y el reintento legítimo concilia igual.
   - Los cuatro puntos de pruebas tienen su caso y su rojo (abajo).
   - La regla para reintentar es «todas las suscripciones anotadas del estudio están canceladas». No es «quien recibió el 503»: ver **D119**.
2. **PERMISOS-1: el arranque da admin por `ADMIN_USERNAMES` sólo por username.**
   - Un email que puso el usuario no da admin, con o sin mayúsculas, con espacios o igual al de una cuenta borrada.
   - Un nombre tampoco da admin.
   - Hay un problema de antes que sigue: **D120**.
3. **BACKUP-1a:** `scripts/datos/copia_base.py` tiene tres órdenes: `copiar`, `verificar` y `enviar`.
   - **Qué hace:**
     - saca la copia con `pg_dump -Fc`;
     - la restaura en una base descartable;
     - compara filas y contenido por tabla, y si no coinciden sale con error.
   - **Qué no compara:** índices, restricciones, secuencias ni objetos grandes. Así figura también en `CHANGELOG.md`.
   - **Cuándo falla:**
     - con 0 tablas o 0 filas en total, y lo dice;
     - si la verificación falla, `copiar` sale con 1.
   - **Archivos:** quedan en 0600 y la carpeta en 0700.
   - **Ante `COPIA_PLAZO_S` o una señal:** borra la base descartable, corta `pg_dump` o `pg_restore` y sale con error.
   - **`enviar`:** es un paso aparte, que lleva a una carpeta local sólo una copia verificada, con su huella y sin cambios.
   - Los siete puntos del adversario están atendidos, en el producto o en riesgos (abajo).

**producto +19/−15** en `proyecto_maria/main.py` contra `ac52d6f` (chequeo-6 entero, abajo).

| Archivo | Contra la base de su pieza | Por qué tanto |
|---|---|---|
| `scripts/datos/copia_base.py` | +525/−0 contra `b831905` (archivo nuevo); +113/−26 en esta vuelta contra `ac52d6f` | chequeo-6 no lo cuenta porque mira `proyecto_maria/`. Las 113 líneas de esta vuelta son el borrado con tope ante un corte, la señal y el aviso de la base que quedó: cada una tiene su caso y su sabotaje |
| `CHANGELOG.md` | +18/−1 contra `ac52d6f` | — |

Los archivos de producto abiertos para `NOW.md` son `proyecto_maria/main.py`, `scripts/datos/copia_base.py` y `CHANGELOG.md`.

### Decisiones

**Numeración.** D118 queda salteada:
- mi canal decía «Próxima D libre: D117»;
- MARIA usó D117;
- D118 es de la Dev 2.

Arranco en D119. El mensaje de `495e601` dice «va como D117»; vale lo de acá.

**D119. El reintento de cancelar lo puede hacer cualquier miembro del estudio con una suscripción anotada, si todas las anotadas del estudio están canceladas en Mercado Pago.**

Esto no es exactamente lo que pediste. Pediste que el reintento lo haga «quien recibió el 503», y CDI no anota quién lo recibió.

Cuando no hay ninguna suscripción que pague, un miembro puede pasar el estudio a `canceled` en estos casos:
- con una suscripción vieja suya cancelada, o una que Mercado Pago contesta con 404;
- en gracia;
- en un estudio `active` sin suscripciones que paguen.

No mueve plata, porque no hay nada que cobre. Pero corta el acceso del estudio.

Lo encontraron el adversario (media) y `/security-review` (confianza 4-5).

Además, si entre el 503 y el reintento aparece una pendiente que abrió otra persona del estudio, el reintento da 403, y sólo la dueña lo destraba.

Opciones:
- **(a)** Dejarlo así, como riesgo.
- **(b)** Anotar en la cuenta que recibió el 503 de cancelar. Sólo esa cuenta, o la dueña, reconcilian, y la marca se borra al conciliar. Es un campo nuevo, así que lleva migración.
- **(c)** Que el reintento de un miembro sólo concilie si el estudio tenía una suscripción que pagaba y era la suya. Esto exige guardar cuál pagaba antes del corte, que es casi lo mismo que (b).

**Recomiendo (b) como pieza aparte.** Es lo que pediste y toca plata y migración. Meterlo acá agranda el producto sin que lo decidieras.

**D120. Un username de `ADMIN_USERNAMES` sin cuenta se puede registrar y queda admin.** Esto es de antes de PERMISOS-1.

`_es_admin` da admin en cada pedido por username (`main.py:1744`), no sólo al arrancar. Quien registre primero ese nombre es admin.

PERMISOS-1 cierra el camino por email, que es lo que pediste. Este otro camino sigue abierto.

Opciones:
- **(a)** Riesgo, que lo cuide Emi: que cada nombre de `ADMIN_USERNAMES` tenga su cuenta creada antes de publicar.
- **(b)** Pieza chica: `_es_admin` mira sólo los roles guardados, y el registro rechaza un nombre de `ADMIN_USERNAMES`.

**Recomiendo (b).** Es el mismo tipo de arreglo chico de seguridad que D116. Antes de cambiarlo hay que confirmar con Emi cómo entra hoy su admin.

**D121. Restos de la vieja regla por email.**
- Un usuario que ya ganó admin por email lo conserva, porque el arranque no saca roles.
- Una entrada con forma de email en `ADMIN_USERNAMES` ya no hace nada.
- El bucle se podría borrar si D120 va por (b).

Opciones:
- **(a)** A la cola de limpieza, y que Emi revise los roles admin guardados en producción.
- **(b)** Una pieza que quite el admin a quien no está por username.

**Recomiendo (a).** Sacar roles guardados en producción es un cambio de datos que decide Emi.

**D8 (BACKUP-1a). Nada chocó.** En el punto 4 elegí manejar la señal y poner un tope, en vez de limpiar al empezar las `cdi_restauracion_*` viejas:
- limpiar al empezar podría borrar la base de otra corrida en curso;
- con la señal y el tope, la corrida que la creó la borra.

Lo que queda tras un `SIGKILL` está en riesgos.

### SHAs

| SHA | Qué |
|---|---|
| `b831905` | base de BACKUP-1a (LIMPIEZA-1) |
| `9459754` | producto: la copia no da por buena una base vacía ni deja restos al cortarse |
| `1154be3` | arnés: copia vacía, corte por plazo o señal, permisos, enviar sin huella; `con_pg16.sh` usa `PG_PUERTO` |
| `fb7b73c` | producto: el corte mata a `pg_dump`, limpia aunque falle el CREATE y respeta nohup; el plazo «²» se rechaza |
| `f7086a9` | arnés: corte con `pg_restore` colgado, SIGHUP ignorado, plazo «²» |
| `8410cf6` | merge de tu rama |
| `ac52d6f` | base de COBRO-MP-2+3 y PERMISOS-1 |
| `495e601` | producto: el reintento de cancelar concilia y una firma con una clave repetida da 401 |
| `a0b34ac` | arnés: reintento, firma carácter por carácter y `v1` repetido, textos 503, plazo único con dos lecturas, reactivar con una propia que no paga |
| `a7dd38b` | arnés: sabotajes de cobro |
| `756fed2` | producto: el arranque da admin por `ADMIN_USERNAMES` sólo por username |
| `7baaeae` | arnés: PERMISOS-1 y `permisos1.sh` |
| `22eecd8` | merge de tu rama |
| `171c6d7` | producto: el reintento concilia sólo con todas las suscripciones del estudio canceladas |
| `8174f01` | arnés: un miembro con una cancelada no toca el plan |
| `6d2eee3` | arnés: un nombre tampoco da admin |
| `28a826b` | producto: copiar no deja una copia vacía, y el borrado de la restauración aguanta un corte (tope de 60 s) |
| `767c689` | arnés: copia vacía sin restos, borrado ante un corte y con tope, SIGHUP sin carrera |
| `5dc946b` | arnés: el sabotaje «sin plazo» espera el rojo real (~8 min la corrida) |
| `622bcf7` | producto: la base que no se pudo borrar se avisa también al cortarse y no deja marcar la copia |
| `ca84c5f` | arnés de BACKUP-1a; **SHA que se entrega** |
| `a87b4f7` | merge de tu rama, sólo `docs/pm` |

`cobro_mp2.sh` corrió en dos tramos:
- los primeros 43 sabotajes sobre `8174f01`; ahí corté la corrida;
- el resto sobre `ca84c5f`, con una copia del script que saltea los primeros 43. La copia suma una sola línea (cuenta los sabotajes y saltea hasta `SALTEAR`) y no está en el repo.

Entre `8174f01` y `ca84c5f`, `git diff --stat` sobre `proyecto_maria/`, `tests/test_cobro*`, `conftest.py`, `mp_firma.py`, `cobro_mp2.sh` y `cobro_mp2_postgres.py` da vacío. El diff entero son 7 archivos, ninguno de cobro (`7 files changed, 195 insertions(+), 22 deletions(-)`). Los 87 rojos de los dos tramos no se repiten.

`permisos1.sh` corrió sobre `ca84c5f`.

### COBRO-MP-2+3: cada punto con su rojo

**El reintento concilia.** Casos en `tests/test_cobro_mp2.py`:

- **`test_si_mp_cancelo_sin_confirmar_el_reintento_concilia`.** El PUT cancela en Mercado Pago pero contesta 500, y la relectura falla. Hay tres filas:
  - `abrio-False-200` y `duena-False-200`: el reintento concilia;
  - `abrio-True-403`: otra suscripción paga, y no cambia nada.
- **`test_un_miembro_con_una_cancelada_no_toca_el_plan_del_estudio`.** Da 403 y no cambia nada. Hay tres filas:
  - `cancela_la_pendiente_de_otro`;
  - `cancela_con_la_suya_pendiente`;
  - `reactiva_con_la_suya_cancelada`.

```
ROJO  | el reintento no concilia: dice «FAILED tests/test_cobro_mp2.py::test_si_mp_cancelo_sin_confirmar_el_reintento_concilia[abrio-False-200]»
ROJO  | cancelar no avisa que es un reintento: dice «FAILED tests/test_cobro_mp2.py::test_si_mp_cancelo_sin_confirmar_el_reintento_concilia[abrio-False-200]»
ROJO  | el reintento concilia aunque otra suscripción pague: dice «FAILED tests/test_cobro_mp2.py::test_si_mp_cancelo_sin_confirmar_el_reintento_concilia[abrio-True-403]»
ROJO  | con la suya cancelada, un miembro cancela la pendiente de otro: dice «FAILED tests/test_cobro_mp2.py::test_un_miembro_con_una_cancelada_no_toca_el_plan_del_estudio[cancela_la_pendiente_de_otro]»
ROJO  | con otra cancelada, un miembro cancela la suya pendiente: dice «FAILED tests/test_cobro_mp2.py::test_un_miembro_con_una_cancelada_no_toca_el_plan_del_estudio[cancela_con_la_suya_pendiente]»
ROJO  | reactivar acepta una suscripción propia ya cancelada: dice «FAILED tests/test_cobro_mp2.py::test_un_miembro_con_una_cancelada_no_toca_el_plan_del_estudio[reactiva_con_la_suya_cancelada]»
```

**1. Firma** (`tests/test_cobro_mp3.py`):
- cada una de las 64 posiciones cambiada, una por vez, como datos;
- dos `v1=`, con la buena primero y con la buena al final.

Todas dan 401 y no consultan a Mercado Pago (`LLAMADAS == []`). En el producto, un encabezado con una clave repetida da 401.

```
ROJO  | se atiende un IPN por la URL, sin firma: dice «('ipn', 200»
ROJO  | un cuerpo que no es un objeto rompe la verificación: dice «'cuerpo que no es un objeto'»
ROJO  | un data que no es un objeto rompe la verificación: dice «'data que no es un objeto'»
ROJO  | la firma se compara como texto: dice «'firma con letras no ascii'»
ROJO  | sin clave configurada, se verifica con la clave vacía: dice «('firmado con clave vacía', 200»
ROJO  | la firma se compara a medias (sólo los primeros caracteres): dice «('sólo los primeros caracteres', 200»
ROJO  | la firma se compara a medias (firma más corta): dice «('firma más corta', 200»
ROJO  | la firma se compara a medias (firma más larga): dice «('firma más larga', 200»
ROJO  | la firma se compara a medias (el carácter 0 cambiado): dice «('el carácter 0 cambiado', 200»
ROJO  | la firma se compara a medias (el carácter 8 cambiado): dice «('el carácter 8 cambiado', 200»
ROJO  | la firma se compara a medias (el carácter 30 cambiado): dice «('el carácter 30 cambiado', 200»
ROJO  | la firma se compara a medias (el carácter 63 cambiado): dice «('el carácter 63 cambiado', 200»
ROJO  | con dos v1 vale el último: dice «('dos v1, la buena al final', 200»
```

**2. Textos de los 503** (`test_con_mp_sin_contestar_se_contesta_503_dentro_del_tope`). Cada texto se compara exacto. Ninguno afirma algo que no se confirmó.

| Dónde | Texto |
|---|---|
| cancelar | «No se pudo confirmar la cancelación en Mercado Pago. Probá de nuevo en unos minutos.» |
| checkout, lectura o PUT de la vieja | «No pudimos confirmar tu suscripción actual con Mercado Pago. Probá de nuevo en unos minutos.» |
| checkout, al crear la nueva | «Mercado Pago no contestó. Probá de nuevo en unos minutos.» |
| sacar a un miembro | «No se pudo confirmar en Mercado Pago la suscripción de {username}; sigue en el estudio. Probá de nuevo en unos minutos.» |

```
ROJO  | si Mercado Pago no contesta, cancelar dice que el plan sigue igual: dice «FAILED tests/test_cobro_mp2.py::test_con_mp_sin_contestar_se_contesta_503_dentro_del_tope[cancelar_lee]»
ROJO  | si Mercado Pago no contesta, sacar dice que el miembro ya salió: dice «FAILED tests/test_cobro_mp2.py::test_con_mp_sin_contestar_se_contesta_503_dentro_del_tope[sacar_lee]»
ROJO  | si Mercado Pago no crea la nueva, el checkout dice que el plan sigue igual: dice «FAILED tests/test_cobro_mp2.py::test_con_mp_sin_contestar_se_contesta_503_dentro_del_tope[checkout_crea]»
```

**3. Plazo único.** Nueva fila `checkout_lee_dos` en `test_el_tope_es_uno_para_todos_los_pedidos_a_mp`. El checkout lee dos suscripciones anotadas, la de la dueña y la de quien la abrió. Cada lectura queda por debajo del tope y la suma por encima, y da 503 dentro del tope.

```
ROJO  | las lecturas iniciales del checkout tienen su propio plazo: dice «FAILED tests/test_cobro_mp2.py::test_el_tope_es_uno_para_todos_los_pedidos_a_mp[checkout_lee_dos]»
```

**4. Quién toca.** Nueva fila `reactivar_con_una_propia_que_no_paga`: un miembro con un sid propio pendiente, en un estudio cancelado, intenta reactivar. Da 403.

```
ROJO  | reactivar acepta a quien abrió una suscripción que no paga: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[reactivar_con_una_propia_que_no_paga-abrio]»
```

**R1** («No podés removerte a vos mismo» sin caso) queda en la cola, como decidiste.

### PERMISOS-1: el caso y su rojo

**`tests/test_admin_bootstrap.py::test_lo_que_puso_el_usuario_en_su_perfil_no_da_admin`.** El caso:
1. un usuario común cambia por `PUT /api/user/profile` su email y su nombre a `jefe@estudio.test`, que está en `ADMIN_USERNAMES` y no tiene cuenta;
2. se reinicia;
3. `admin` no está en sus roles.

La familia va como datos:
- `tal_cual`;
- `mayusculas` (`Jefe@Estudio.TEST`);
- `espacios`;
- `de_una_cuenta_borrada`.

Saqué `test_bootstrap_admin_promotes_by_email`, que pedía lo contrario. `test_bootstrap_admin_promotes_by_username` sigue verde.

Sabotaje propio, `scripts/testing/sabotajes/permisos1.sh`, corrido sobre `ca84c5f`:

```
ROJO  | el arranque busca también por email: dice «FAILED tests/test_admin_bootstrap.py::test_lo_que_puso_el_usuario_en_su_perfil_no_da_admin[tal_cual]»
ROJO  | el arranque busca el email sin mirar mayúsculas: dice «FAILED tests/test_admin_bootstrap.py::test_lo_que_puso_el_usuario_en_su_perfil_no_da_admin[mayusculas]»
ROJO  | el arranque busca también por nombre: dice «FAILED tests/test_admin_bootstrap.py::test_lo_que_puso_el_usuario_en_su_perfil_no_da_admin[tal_cual]»
ROJO  | el arranque no da admin a nadie: dice «FAILED tests/test_admin_bootstrap.py::test_bootstrap_admin_promotes_by_username»
sabotajes con falla: 0
```

Dos filas no distinguen nada por sí mismas, así que las dejo dicho:
- `espacios` da lo mismo que `tal_cual`, porque `_admin_usernames()` recorta los espacios;
- `de_una_cuenta_borrada` casi no prueba nada, porque una cuenta borrada no deja rastro que el arranque pueda leer.

Quedan como datos porque los pediste.

### BACKUP-1a: los puntos del adversario

| Punto | Qué quedó | Caso |
|---|---|---|
| 1. Copia vacía | `copiar` y `verificar` fallan con 0 tablas o 0 filas, y lo dicen. `copiar` no deja la copia ni su huella | `test_una_copia_vacia_da_error`, `test_una_huella_sin_filas_no_llega_a_la_base` |
| 2. El código de salida | `copiar` sale con 1 si la verificación falla | `test_copiar_sale_con_error_si_la_verificacion_falla` |
| 3. Permisos | archivos en 0600 y carpeta en 0700, también en `enviar` | en `test_la_copia_de_todas_las_tablas_se_restaura_igual` y `test_enviar_lleva_la_copia_verificada_al_destino` |
| 4. Señal y tope | `COPIA_PLAZO_S` (3600 por defecto) o una señal no ignorada borran la base descartable, cortan al hijo y salen con error. El borrado aguanta otro corte y tiene un tope de 60 s. Si no se pudo borrar, avisa y no marca la copia | `test_un_corte_no_deja_la_base_ni_el_pg_restore`, `test_un_plazo_que_no_se_entiende_no_copia`, `test_un_corte_durante_el_borrado_no_lo_deja_a_medias`, `test_un_borrado_colgado_tiene_tope_y_avisa`, `test_una_restauracion_que_quedo_no_marca_la_copia` |
| 5. Lo que se promete | compara filas y contenido por tabla; no índices, restricciones, secuencias ni objetos grandes | `CHANGELOG.md` y este informe |
| 6. Mutantes | la huella mira todos los esquemas; `enviar` no lleva una copia sin su huella | `test_otro_esquema_entra_en_la_huella`, `test_enviar_no_lleva_una_copia_sin_su_huella` |
| 7. Restos que traban el reintento | a riesgos | — |

El rename de `PUERTO` a `PG_PUERTO` en `con_pg16.sh`, que estaba en la cola, quedó hecho en `1154be3`.

**Lo que tiene que cargar Emi para activarlo:**

- `COPIA_ORIGEN_URL`: la base de producción. Idealmente con un usuario de sólo lectura.
- `COPIA_PRUEBA_URL`: un Postgres descartable donde se restaura. El usuario necesita `CREATEDB`.
- `COPIA_DESTINO`: hoy sólo acepta una carpeta local, absoluta y que ya exista. Un servicio externo (S3 u otro) es otra pieza.
- `COPIA_PG_BIN`: la carpeta de un `pg_dump` y un `pg_restore` de la misma versión del servidor o más nueva.
- `COPIA_PLAZO_S`: opcional. Por defecto, 3600 s.
- Dónde se programa (cron u otro) y quién recibe la alerta cuando sale distinto de 0.
- Cuántas copias se guardan. Hoy `copiar` no pisa una que ya existe, y no borra copias viejas.

### Sabotajes

| Script | Sobre | ROJO | Fallas | Salida |
|---|---|---|---|---|
| `cobro_mp2.sh`, primer tramo | `8174f01` | 43 | la corté ahí | — |
| `cobro_mp2.sh`, el resto | `ca84c5f` | 44 | `sabotajes con falla: 0` | `salida 0` |
| `cobro_mp3.sh` | `ca84c5f` | 22 | `sabotajes con falla: 0` | `salida 0` |
| `permisos1.sh` | `ca84c5f` | 4 de 4 | `sabotajes con falla: 0` | `salida 0` |
| `backup1a.sh` | `ca84c5f` | 48 de 48 | `sabotajes con falla: 0` | `salida 0` |

Las líneas de base, copiadas:

```
BASE  | en verde                                (cobro_mp2.sh, primer tramo)
BASE  | en verde                                (cobro_mp2.sh, el resto)
BASE  | los cruces en Postgres, en verde        (cobro_mp2.sh, el resto)
BASE  | tests/test_cobro_mp3.py en verde        (cobro_mp3.sh)
VERDE | base: 47 passed, 5 warnings in 45.78s
```

La última es la base de `backup1a.sh`: las pruebas sin sabotear, en verde. No es un sabotaje verde.

En las salidas de los cinco scripts no hay ninguna línea `VERDE`, `ROTO` ni `ROJO?`, salvo esa base de `backup1a.sh`. El primer tramo de `cobro_mp2.sh` no tiene línea final porque lo corté.

Los 48 de `backup1a.sh`:

```
ROJO  | no compara el contenido: dice «FAILED» y «copia verificada»
ROJO  | no compara las filas: dice «public.ncm_cache: el contenido no coincide»
ROJO  | sólo mira las tablas de la copia: dice «[CREATE TABLE de_mas» y «copia verificada»
ROJO  | sólo mira las tablas restauradas: dice «[DROP TABLE ncm_cache» y «copia verificada»
ROJO  | ignora que pg_restore falló: dice «falta en la restauración»
ROJO  | no borra la base de restauración: dice «cdi_restauracion_»
ROJO  | pg_dump no usa el instante de la huella: dice «public.ncm_cache: 3 filas al copiar, 2 al restaurar»
ROJO  | la huella usa el orden alfabético de la base: dice «public.orden: el contenido no coincide»
ROJO  | la sesión no fija «SET TimeZone TO 'UTC'»: dice «public.tipos_extra: el contenido no coincide»
ROJO  | la sesión no fija «SET DateStyle TO 'ISO, YMD'»: dice «public.tipos_extra: el contenido no coincide»
ROJO  | la sesión no fija «SET IntervalStyle TO 'postgres'»: dice «public.tipos_extra: el contenido no coincide»
ROJO  | la sesión no fija «SET extra_float_digits TO 3»: dice «public.tipos_extra: el contenido no coincide»
ROJO  | la sesión no fija «SET bytea_output TO 'hex'»: dice «public.tipos_extra: el contenido no coincide»
ROJO  | verificar no borra la marca vieja: dice «quedó marcada como verificada»
ROJO  | una copia vacía queda verificada: dice «copia verificada: 0 tablas, 0 filas» y «copia verificada: 2 tablas, 0 filas»
ROJO  | copiar fija una copia vacía: dice «vuelta 1: quedó algo»
ROJO  | verificar acepta una huella sin filas: dice «falta la variable COPIA_PRUEBA_URL»
ROJO  | copiar sale bien aunque la verificación falle: dice «LA COPIA NO SIRVE» y «pg_restore falló (salida 1)»
ROJO  | la huella sólo mira public: dice «copia verificada»
ROJO  | una huella que no se entiende llega a la base: dice «falta la variable COPIA_PRUEBA_URL»
ROJO  | sin plazo: dice «LA COPIA NO SIRVE» y «falta en la restauración»
ROJO  | un plazo que no se entiende corre igual: dice «no terminó en 0 s» y «no terminó en -5 s»
ROJO  | un plazo con «²» rompe: dice «ValueError: invalid literal for int()»
ROJO  | la señal mata sin limpiar: dice «(-15 == 1»
ROJO  | una señal ignorada corta igual: dice «se cortó por SIGHUP»
ROJO  | cortar no mata al hijo: dice «pg_restore quedó corriendo»
ROJO  | la limpieza no está protegida del corte: dice «close']»
ROJO  | el borrado no tiene tope: dice «Timeout»
ROJO  | al cortar, la base que quedó no se avisa: dice «hay que borrarla a mano' in ''»
ROJO  | la base que quedó no da error: dice «assert 0 == 1»
ROJO  | copiar no avisa antes de copiar: dice «'no se pisa una copia' in 'error: ya existe /»
ROJO  | _fijar pisa: dice «DID NOT RAISE»
ROJO  | sin COPIA_ORIGEN_URL no lo dice: dice «COPIA_ORIGEN_URL no es una dirección postgresql://»
ROJO  | copia antes de saber dónde probarla: dice «copió sin saber dónde probarla»
ROJO  | argparse repite la dirección: dice «el error repite la clave»
ROJO  | la clave va en la URL de pg_dump: dice «la clave va en pg_dump»
ROJO  | tapar no tapa: dice «queda la clave escrita como»
ROJO  | tapar no mira ?password=: dice «en_la_consulta» y «queda la clave escrita como»
ROJO  | los archivos los lee cualquiera: dice «copia.dump: 0o100644»
ROJO  | enviar sin huella: dice «copia.dump.huella.json»
ROJO  | enviar sin marca la da por verificada: dice «destino/copia.dump»
ROJO  | enviar no mira si cambió: dice «la copia llegó distinta»
ROJO  | enviar no mira lo que llegó: dice «DID NOT RAISE»
ROJO  | enviar no mira el destino antes: dice «error: ya existe /»
ROJO  | enviar a un servicio: dice «[s3:» y «tiene que ser una carpeta local»
ROJO  | enviar a una ruta relativa: dice «[relativo» y «enviada a»
ROJO  | enviar a una carpeta que no existe: dice «no_existe» y «FileNotFoundError»
ROJO  | sin COPIA_DESTINO no lo dice: dice «[-falta la variable COPIA_DESTINO]» y «tiene que ser una carpeta local»
```

**Cómo corrió MP-2:** ~2 min por sabotaje. Una corrida de MP-2 quedó cortada a mitad porque edité el script mientras corría: terminó con un fin de archivo inesperado. No la cuento. Desde entonces corro una copia del script.

### Puertas, sobre `ca84c5f`

| Puerta | Salida |
|---|---|
| suite completa, desde un worktree limpio | `4604 passed, 110 skipped, 3 xfailed in 760.18s (0:12:40)`, salida 0 |
| `python -m compileall -q proyecto_maria` | salida 0, sin texto |
| `con_pg16.sh` con `test_backup1a.py` y `test_backup1a_unidad.py` | `47 passed in 43.81s`, salida 0 |
| chequeo-6 | abajo, entero |
| `/code-review high` y `/security-review` | en «Revisión» |

La suite deja líneas `Task was destroyed but it is pending!` al cerrar. Ya pasaba antes, y no lo diagnostiqué en esta pieza.

### chequeo-6, `ac52d6f ca84c5f`

```
chequeo-6 ac52d6f..ca84c5f: avisos para mirar, no un veredicto
producto +19/−15
arnés +511/−28
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11358 → 11362
avisos: 0
```

Con `ac52d6f a87b4f7` da lo mismo. chequeo-6 no cuenta `scripts/datos/copia_base.py`; está en la tabla de «Resultado».

### Revisión

**Adversarios**, uno por pieza:

| Pieza | Agente (modelo, esfuerzo) | Sobre |
|---|---|---|
| COBRO-MP-2+3 | `adversario-sonnet-alto` (Sonnet, alto) | `8410cf6..a0b34ac` |
| PERMISOS-1 | `adversario-sonnet-alto` (Sonnet, alto) | `756fed2..7baaeae` |
| BACKUP-1a | `adversario-opus-alto` (Opus, alto) | `9459754` |

| Pieza | Hallazgo | Severidad | Reproducido | Qué hice |
|---|---|---|---|---|
| COBRO | Un miembro con un sid viejo cancelado podía cancelar la pendiente de otro miembro, y con ella el plan | Alta | Sí | Arreglado en `171c6d7` y `8174f01`: el reintento exige todas canceladas |
| COBRO | Un sid viejo corta el acceso en gracia o en un estudio sin suscripción que pague | Media | Por código | D119 |
| COBRO | Sobrevivían los mutantes «sin `cancelar and`» y «`"cancelled" in estados.values()`» | Media (pruebas) | Sí | Cubiertos en `8174f01` por `reactiva_con_la_suya_cancelada` y `cancela_con_la_suya_pendiente`, con sus sabotajes |
| COBRO | No encontró cómo saltear la firma. La repetición por ts viene de antes | Info | — | Riesgo 2 |
| PERMISOS | H1: un nombre de `ADMIN_USERNAMES` sin cuenta se registra y es admin | Alta, de antes | Por código | D120 |
| PERMISOS | H2: admin ya guardado; entradas de email que no hacen nada | Media | Por código | D121 |
| PERMISOS | H3: `de_una_cuenta_borrada` casi no prueba nada; `espacios` da igual que `tal_cual` | Baja | Sí | Dicho arriba; quedan como datos |
| PERMISOS | H4: el nombre también daba admin | Alta | Sí | Arreglado: el arranque busca sólo por username. Caso en `6d2eee3` |
| BACKUP | 1: el DROP sin tope después del primer corte | Media | Sí | Arreglado en `28a826b` y `622bcf7` |
| BACKUP | 2, 3, 4: el corte no mataba a `pg_dump`, el CREATE fallido no limpiaba, nohup | Media | Sí | Arreglado en `fb7b73c` |
| BACKUP | 5: la base que quedó no se avisaba al cortarse | Baja | Sí | Arreglado en `622bcf7` |
| BACKUP | Mi corrida de sabotajes sobre `f7086a9` dio «sabotajes con falla: 2»: VERDE en «una señal ignorada corta igual» y ROJO? en «sin plazo» | — | Sí | Arreglados en `767c689` (SIGHUP sin carrera) y `5dc946b` (espera el rojo real) |

Lo que queda abierto en BACKUP: si el DROP no termina dentro de su tope, la base queda. Se avisa y la copia no se marca (riesgo 8).

**`/code-review high`**, en dos corridas:
- **BACKUP-1a:**
  - **Arreglados:** 1, 2, 3, 5, 6, 7 y 8.
  - **4:** el sabotaje de SIGHUP podía dar verde a veces. Arreglado en `767c689`.
  - **9:** la segunda vuelta de `test_una_copia_vacia_da_error` es redundante. Queda: no cambia lo que se prueba.
  - **10:** `copiar` mira `_filas` después de `pg_dump`. Es a propósito: la huella se toma con el mismo instante que la copia.
- **Cobro y permisos:**
  - **1, 5 y 8 (el parámetro `cancelar`):** D119.
  - **2, 3 y 4:** D121.
  - **6:** `v1` repetido y rotación de clave. Una clave repetida da 401. Rotar la clave con dos firmas válidas a la vez no está soportado.
  - **7:** la repetición, de antes. Riesgo 2.
  - **9:** `cancel_billing` vuelve a mandar el PUT a suscripciones ya canceladas. Para la cola.
  - **10:** el arranque de admin está dentro del `try` de los usuarios demo. Es de antes: si falla la creación de demos, no se da admin.

**`/security-review`:** subagente `general-purpose` (Sonnet, alto), sobre `171c6d7` y `756fed2`. Sin hallazgos con confianza 8 o más. Anotó con confianza 4-5 que un estudio `active` sin sids puede pasar a `canceled`. Va en D119.

### Error propio

- Edité `cobro_mp2.sh` mientras corría, y esa corrida se cortó (arriba). No cambió ningún resultado entregado.
- Mi primera corrida de `backup1a.sh` sobre `f7086a9` tuvo dos sabotajes que no distinguían. Están en la tabla de revisión y quedaron arreglados antes de este SHA.

### Riesgos

1. **Firma:** hay dos variantes sin rojo: sin el `x-request-id`, y con `compare_digest` cambiado por `==`. La segunda filtra tiempo, pero no acepta firmas falsas.
2. **Firma:** no se mira la frescura del ts, así que un aviso firmado se puede repetir. Hoy repetir un pago ya anotado no cambia nada.
3. **El hilo abandonado sigue hasta 20 s** con un tope de 15 s, y ocupa uno de los 8 cupos mientras tanto.
4. **La firma usa el `data.id` del cuerpo.** Es de antes.
5. **`copiar` cortado entre `_fijar` y la escritura de la huella** deja la copia sin huella. El reintento con el mismo nombre dice «ya existe».
6. **`copiar` que falla al verificar** deja la copia y su huella, y el reintento dice «ya existe». Es a propósito: se puede volver a correr `verificar` sobre esa copia.
7. **`enviar` cortado** deja el destino a medio escribir, y el reintento da «ya existe en el destino».
8. **Un `SIGKILL`**, o un DROP que no termina en 60 s, deja `.parcial-*` y `cdi_restauracion_*`. En el caso del DROP lo avisa. Las `cdi_restauracion_*` viejas no se limpian al empezar (D8).
9. **La huella no está cubierta por el `.sha256`.**
10. **D119, D120 y D121.**

### Lo que no se corrió

- Los sabotajes de piezas anteriores: los corrés vos antes de publicar.
- Nada contra Mercado Pago real ni contra una base de producción.
- `backup1a.sh` con un `pg_dump` de versión distinta a la del servidor: sólo Postgres 16 local.
- El ataque de aislamiento: estas piezas no tocan clientes ni descargas.

### Para reproducir

```bash
scripts/testing/sabotajes/cobro_mp2.sh ca84c5f    # cada línea «ROJO …», «sabotajes con falla: 0», «salida 0» (~2 min por sabotaje)
scripts/testing/sabotajes/cobro_mp3.sh ca84c5f    # lo mismo
scripts/testing/sabotajes/permisos1.sh ca84c5f    # 4 ROJO, «sabotajes con falla: 0»
scripts/testing/sabotajes/backup1a.sh ca84c5f     # 48 ROJO, «sabotajes con falla: 0» (~8 min por «sin plazo»)
DATABASE_URL=sqlite+aiosqlite:///./rep.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  python -m pytest -q --no-cov tests/test_cobro_mp2.py -k "reintento or cancelada or lee_dos"   # «18 passed, 95 deselected»
docs/pm/herramientas/chequeo-6.py ac52d6f ca84c5f # «producto +19/−15», «avisos: 0»
```

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. COBRO-MP-2+3 vuelta 3, PERMISOS-1 y BACKUP-1a entregadas en ca84c5f (informe en el commit de arriba). Abiertas D119 (recomiendo b, pieza aparte), D120 (b), D121 (a); D8 contestada. Sigue EXCEL-2d; frenar 2026-11-08 15:50 UTC. Reglas de Emi: sólo la PM y Emi me piden, nada se publica sin su «dale» para el SHA, nunca main, sin secretos.
