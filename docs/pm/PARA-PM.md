# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ADMIN-CREDITOS-1 vuelve, sobre la devolución de las 12:08

**El diff de la vuelta no toca el servidor.** El único cambio de producto es
`dev_dashboard.html` +6/−6 (`acf9bd3d`); ningún `.py` de `proyecto_maria/` cambió desde `39d4dd8b`.
Por lo que dijiste, no hace falta volver a correr la suite ni los de cobro. `cobro_corte1.sh` lo corrí
igual, sobre un solo SHA (punto 4).

| | SHA |
|---|---|
| Base | `0208ea9d` |
| Producto | `acf9bd3d` (vuelta), sobre los de antes: `795f10b3` … `dad0139c` |
| Pruebas | `87785b1e`, `8d6829ea`, `51638c07`, `ba9fca8d`, `0f5ee58d` |
| CHANGELOG | `612f5124` |
| Este informe | el commit `docs:` encima de `0f5ee58d` |

**Resultado.** Los cuatro puntos están hechos, cada uno con su rojo. Nada nuevo para decidir: D238
(a) ya está decidida y D237 va a Emi, como dijiste. No hay D239.

### Los puntos de la devolución

| # | Pide | Qué hice y dónde se ve |
|---|---|---|
| 1a | Caso 8: el orden tarde no puede salir «ok» | Abajo, «La condición de armado». Sabotaje «sin atrapar el choque de la clave»: 20 de 20 en rojo sobre `0f5ee58d` |
| 1b | Caso 10: cada fila de guardado con un sabotaje que la ponga en rojo | El guardado corre al tope y gasta uno extra. Tabla de abajo |
| 2 | `sinConfirmar` para toda la familia de claves heredadas | Es un `Map` (`acf9bd3d`), que no mira `Object.prototype`, así que vale para cualquier clave. La pantalla prueba `__proto__`, `constructor`, `toString`, `hasOwnProperty` y `valueOf` (`pantalla_admin_creditos1.js:147`); `valueOf` queda fuera de las cuatro que nombraste. El sabotaje que vuelve al objeto común da «FALLA: abrir __proto__» |
| 3 | El bit +x de `admin_creditos1.sh` | `100755` desde `87785b1e` (`git ls-files -s`) |
| 4 | Un solo SHA para `cobro_corte1.sh` y el SHA de `/security-review` | Los dos corrieron sobre `8d6829ea`. De ahí a `0f5ee58d` cambiaron sólo los arneses de esta pieza (`admin_creditos1_postgres.py`, sus dos guiones de sabotaje, el nuevo `_veces.sh` y `admin_creditos1.sh`); `cobro_corte1.sh` no usa ninguno |

#### La condición de armado (caso 8)

`mismo_pedido_dos_cuentas`, `scripts/testing/admin_creditos1_postgres.py:69-97`:

1. La conexión `candado` del arnés inserta el pedido en `creditos_admin` y no commitea.
2. Lanza las dos cargas, una por cuenta, con ese pedido.
3. La ronda se da por armada sólo si, antes de soltar, `h.esperando(mio)` muestra **dos** consultas
   `INSERT INTO creditos_admin` esperando la clave que retiene el arnés. Si las dos están en el
   INSERT, las dos buscaron el pedido (`db.get`) y no lo vieron.
4. En `finally`, el arnés hace `rollback`: una carga commitea y la otra choca con la clave.

**Por qué el orden tarde no puede salir «ok»:** mientras el arnés retiene la clave, ninguna carga
puede commitear. Si una de las dos todavía no llegó al INSERT cuando se agota la espera, `consultas`
queda en `None`. Entonces `fila()` (líneas 54-58) imprime «SIN ARMAR … | NO SE ARMÓ», y `main` sale
4 (`return 1 if malas else 4 if sin_armar else 0`). Para salir «ok», la ronda tiene que estar armada:
las dos tienen que haber buscado el pedido antes de que hubiera un commit.

El sabotaje «el pedido sin clave en la tabla» acepta «1|4», porque sin clave nada espera detrás
del arnés: la ronda no se arma y, según quién commitee primero, las dos cargan (1) o la segunda ve
el pedido (4). Exige «NO SE ARMÓ».

#### Caso 10, cada fila con su rojo

Con créditos al día, el guardado va con `ops_used_this_period = 15`, o sea, al tope del plan: gasta
un crédito extra, y se espera `5 + N − 1` (la etiqueta dice «, al tope»). Con vencidos y debajo del
tope, se espera `0 + N`.

Lo que dio `sabotajes/admin_creditos1_postgres.sh` sobre `51638c07`; de ahí a `0f5ee58d` ni ese
guion ni el arnés cambiaron:

| Sabotaje | Salida | Filas MAL | Qué pone en rojo |
|---|---|---|---|
| sin sabotaje | 0 | 0 | — |
| sin atrapar el choque de la clave | 1 | 1 | dos cuentas, `[5, 12]`, `[200, 500]` |
| el pedido sin clave en la tabla | 4 | 0 | la ronda no se arma |
| la carga sin candado | 1 | 6 | las 4 de recarga + carga; guardado + carga al tope, usuario y org: «quedan 12, esperaba 11» |
| la cuenta sin candado | 1 | 10 | las 4 de recarga + carga; carga + guardado, usuario y org: con vencidos «quedan 0, esperaba 7» y al tope «quedan 4, esperaba 11»; guardado + carga al tope, usuario y org |
| la recarga sin candado | 1 | 4 | las 4 de carga + recarga |
| la ruta no reconoce el pedido repetido | 1 | 3 | el mismo pedido dos veces (usuario y org) y dos cuentas, `[200, 500]` |
| el arranque crea tablas que ya existen | 1 | 1 | el primer arranque falla |
| la tabla de cargas se crea sin mirar si existe | 1 | 1 | el segundo arranque falla |
| el arranque cambia otra tabla | 1 | 1 | `public.users: el contenido no coincide` |
| el arranque deja cargas | 1 | 1 | `creditos_admin con 2 filas` |

«sabotajes sin rojo: 0», rc=0. El mapa sabotaje → fila está en
`scripts/testing/sabotajes/admin_creditos1_postgres.sh:57-114`.

**La ronda que no se corre:** guardado y después carga, con créditos vencidos. Da 7 aun sin
candado, porque la carga vence lo viejo igual; ningún sabotaje la distingue. Está excluida y
explicada en `admin_creditos1_postgres.py:148-149`. Las otras tres de guardado sí tienen rojo.

#### Las 20 corridas

`scripts/testing/sabotajes/admin_creditos1_postgres_veces.sh` (nuevo en `0f5ee58d`, `100755`):

- arma un worktree del SHA;
- quita el `try/except IntegrityError` de `admin_router.py`;
- corre N veces el arnés;
- cuenta como ROJO sólo la corrida que sale 1 con la fila «MAL | el mismo pedido para dos cuentas»
  en `[200, 500]`; una ronda sin armar sale 4 y no cuenta;
- termina con «rojas: N de VECES» y sale 0 sólo si todas son rojas.

Sobre `0f5ee58d`: «rojas: 20 de 20», rc=0. Cada corrida dice
«salida 1 ROJO | MAL | el mismo pedido para dos cuentas | créditos [5, 12] | [200, 500] | deadlocks +0 | filas MAL: 1; rondas sin armar: 0».

### Puertas

| Puerta | SHA | Salida exacta |
|---|---|---|
| Suite completa | `6249a66d` | `6276 passed, 110 skipped, 3 xfailed, 110 warnings in 1229.68s (0:20:29)`, rc=0 |
| `sabotajes/admin_creditos1.sh` (27) | `ba9fca8d` | BASE «35 passed, 5 warnings in 4.14s» y «OK: ADMIN-CREDITOS-1 en el navegador»; 27 ROJO; «sabotajes sin rojo: 0», rc=0 |
| `sabotajes/admin_creditos1_postgres.sh` | `51638c07` | la tabla de arriba; «sabotajes sin rojo: 0», rc=0 |
| `sabotajes/admin_creditos1_postgres_veces.sh` | `0f5ee58d` | «rojas: 20 de 20», rc=0 |
| `sabotajes/cobro_corte1.sh` entero | `8d6829ea` | BASE «en verde», «la pantalla en verde» y «el lock en verde»; 87 ROJO; «sabotajes con falla: 0», rc=0 |
| `/security-review` | `8d6829ea` | sin vulnerabilidades de alta confianza; sugiere `Depends(require_admin)` en la ruta como defensa extra, que no sumé (la ruta ya exige admin y lo prueban los casos sin sesión y no admin) |
| `anclas_perdidas.py` | `0f5ee58d` | rc=0, ninguna PERDIDA |
| `chequeo-6.py 0208ea9d 0f5ee58d` | `0f5ee58d` | abajo, entera |

**Corrijo el informe anterior.** Decía que los únicos `SIN ANCLA` eran `limpieza1.sh:183` y `:187`.
Son seis: `limpieza1.sh:175`, `177`, `179`, `181`, `183` y `187`. Ya estaban así sobre `39d4dd8b`, y
siguen igual sobre `0f5ee58d`.

**Qué no corrí sobre `0f5ee58d` y por qué vale igual:**
- **La suite** corrió sobre `6249a66d`. Desde ahí no cambió ningún `.py` de producto.
- **`cobro_mp1.sh`**: no lo volví a correr, porque el servidor no cambió. Sabotea también el HTML,
  pero `anclas_perdidas` sobre `0f5ee58d` no da ninguna PERDIDA.
- **`admin_creditos1.sh`** corrió sobre `ba9fca8d`; después sólo se sumó `_veces.sh`.
- **`admin_creditos1_postgres.sh`** corrió sobre `51638c07`; después cambiaron
  `admin_creditos1.sh` (+2/−2, anclas del Map) y se sumó `_veces.sh`. Ninguno de los dos lo usa.

### Adversarios y revisiones

| Quién | Hallazgo | Qué hice |
|---|---|---|
| Sonnet alto | El sabotaje «el pedido sin clave en la tabla» no era determinista: sale 1 o 4 según quién commitea primero | Acepta «1\|4» y exige «NO SE ARMÓ» (`51638c07`) |
| Sonnet alto | Nits 2 y 3: el comentario del sabotaje del pedido repetido no decía que el segundo da 500, y la pantalla tenía un chequeo de otra cuenta después de `__proto__` que daba verde con el objeto común | Arreglados en `8d6829ea` |
| Sonnet alto | Nit 4: la pantalla pide una base nueva, porque las cuentas de claves heredadas tienen nombre fijo | Queda así; la cabecera lo dice. El arnés de casos y pantalla ya arranca con base nueva |
| Mío | Dos anclas de `admin_creditos1.sh` se perdieron con el Map | Siguen al Map en `ba9fca8d`; `anclas_perdidas` sobre `0f5ee58d` no da ninguna PERDIDA |
| `/security-review` (`8d6829ea`) | Sin hallazgos de alta confianza | — |

### Lo que contestaste

- **D238 (a)**, decidida: nada que hacer.
- **D237** va a Emi con (a): no sigo en eso.
- **`past_due`/`canceled` dan 200**: anotado como riesgo bajo.
- **La limpieza de `conexiones1_tests.diff`**: pasa a `COLA-LIMPIEZA`, que es tuyo.

### chequeo-6, entero

```
chequeo-6 0208ea9d..0f5ee58d: avisos para mirar, no un veredicto
producto +195/−52
  AVISO producto suma 143 líneas netas: el informe dice por qué (§6: más de 20)
arnés +1080/−54
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/database/candados.py: nuevo, 33
  proyecto_maria/main.py: 12276 → 12249
  proyecto_maria/routers/admin_router.py: 466 → 514
  proyecto_maria/services/billing_service.py: 450 → 448
avisos: 1
```

rc=0. **El AVISO** es el mismo de la entrega anterior: la ruta y su cuerpo, la tabla `CreditoAdmin`,
`candados.py` (D233) y `acreditar_extra` (D234). La vuelta sola:

```
chequeo-6 3ced84af..0f5ee58d: avisos para mirar, no un veredicto
producto +6/−6
arnés +143/−22
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

El HTML no lo mide `chequeo-6`: en la vuelta, `dev_dashboard.html` +6/−6 (`producto +6/−6`), con el
grep de historia vacío.

### Riesgos que quedan

- Los de la entrega anterior siguen: `previa` borrada entre el IntegrityError y la relectura da 500;
  `.one()` da 500 si la cuenta se borra entre el 404 y el candado; `fetchUsuarios(0)` vuelve a la
  primera página; `crypto.randomUUID()` sólo existe con HTTPS o `localhost`; `con_pg16.sh` escribe en
  `/tmp/cdi-pg16.XXXXXX` aunque `TMPDIR` diga otra cosa.
- `past_due`/`canceled` dan 200 (lo calificaste bajo).
- La ronda guardado + carga con vencidos no se corre, porque no distingue el defecto.

### Archivos de producto que toqué en la vuelta

- `proyecto_maria/templates/dev_dashboard.html`
- `CHANGELOG.md`

### Para reproducir

```bash
export PY=<venv>/bin/python
# Los sabotajes de la pieza: 27 ROJO y «sabotajes sin rojo: 0».
scripts/testing/sabotajes/admin_creditos1.sh 0f5ee58d
# Postgres: «filas MAL: 0; rondas sin armar: 0».
scripts/testing/con_pg16.sh $PY scripts/testing/admin_creditos1_postgres.py
# Los sabotajes en Postgres: la tabla de arriba y «sabotajes sin rojo: 0».
scripts/testing/sabotajes/admin_creditos1_postgres.sh 0f5ee58d
# El choque de la clave, 20 veces: «rojas: 20 de 20».
scripts/testing/sabotajes/admin_creditos1_postgres_veces.sh 0f5ee58d
# Las anclas: ninguna PERDIDA.
$PY scripts/testing/anclas_perdidas.py 0f5ee58d
# Los números de §6: la salida de arriba.
$PY docs/pm/herramientas/chequeo-6.py 0208ea9d 0f5ee58d
```

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, nunca main; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message priority next; rutina trig_011UpBfwEu9TUzoNUrviqoP5. Pieza ADMIN-CREDITOS-1 vuelta entregada; producto hasta acf9bd3d; pruebas hasta 0f5ee58d; base 0208ea9d; próxima D D239. Sin secretos ni datos reales, nada contra producción ni MP real, nada se publica sin el «dale» de Emi. tests/test_conexiones1.py queda sin seguimiento a propósito.
