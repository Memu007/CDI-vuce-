# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## BORRADOR-1 (D143 a): el arranque ya no saca a la usuaria de Clientes. Si no fue a ninguna pantalla, o si el tour la llevó a la carga, recupera la operación de antes. D170 a D173 las decidís vos

| Qué | SHA |
|---|---|
| Entrega (este informe) | el commit de este informe, encima de `1732cd72` (el merge de tu rama, que toca sólo `docs/pm`) |
| Producto | `524a8f00` y `cc8b834b`: `app_v2.js` y `CHANGELOG.md` |
| Pruebas y sabotaje | `d3dfc2e4`, `42f0ed9b` y `b0d6c274`: `scripts/testing/pantalla_borrador1.js` y `scripts/testing/sabotajes/borrador1.sh` |
| Comentarios | `6c2b3383`: sólo comentarios de `app_v2.js` |
| Base | `4555f7c4` |

`git diff b0d6c274 HEAD -- proyecto_maria tests scripts` da vacío: las puertas sobre `b0d6c274` valen para la entrega.

**Resultado**
- El arranque cambia de pantalla sólo si la usuaria todavía no fue a ninguna, o si está en la carga.
  - A la carga la puede haber llevado el tour, y el tour no es una elección de ella.
- Si ya está en otra pantalla, la operación de antes queda guardada y aparece el aviso «Quedó guardada la operación».
- Si el usuario no llega a tiempo, tampoco la saca de donde está.
- La base de `cliente1` era roja (`locator.click: Timeout`) y ahora da verde.
- Los sabotajes de `cliente1` que dan ROJO? a partir del 6.º registro son el límite de registro (D145), no esta pieza. Está más abajo, con evidencia.

**Archivo de producto tocado:** `proyecto_maria/static/v2/app_v2.js`.

## Decisiones

Las D de esta entrega van de D170 en adelante. El rango lo elegí yo: D150 a D163 están tomadas, y comprobé con `git grep -E '\bD17[0-9]\b'` que D170 a D179 no aparecen en `docs/pm` de `claude/dev-tecnica`, `claude/practical-shannon-szpwkn` ni `claude/dev-maria`.

- **D170. El aviso «pendiente» no se borra y no se vuelve a ofrecer** (severidad baja).
  - Pasa si la operación de antes llega mientras la usuaria está ocupada en otra pantalla.
  - El texto dice «antes de recargar», nunca se borra y puede pisar el aviso de «lleno».
  - La pestaña no vuelve a ofrecer la operación; aparece recién al recargar.
  - (a) Pieza chica: al volver a una pantalla libre, ofrecerla de nuevo y borrar el aviso.
  - (b) Dejarlo así; recargar la recupera.
  - **Recomiendo (b) por ahora:** no se pierde nada y la salida existe.
- **D171. Se pierde la operación con el tour después de recuperarla** (media; ya estaba antes de esta pieza, la reprodujo el adversario).
  - Una usuaria nueva recupera una operación con ítems.
  - El tour hace `goTo('upload')`.
  - El guardado automático (`app_v2.js`, el intervalo cerca de la línea 1190) borra el borrador al estar en la carga.
  - Si recarga, la operación ya no está.
  - (a) Pieza nueva: el tour no lleva a la carga si hay una operación en curso.
  - (b) A la cola.
  - **Recomiendo (a):** pierde datos de la usuaria. Es chica, pero no entra en D143 (a), que era sólo no sacarla de Clientes.
- **D172. La adopción está escrita de dos formas** (limpieza).
  - `b && adoptarTarde(b)` aparece dos veces, y el arranque elige con un ternario: tres lugares, dos estilos.
  - **Propongo** un `recuperar(b)` para `COLA-LIMPIEZA.md`. No lo hice dentro del arreglo (§6).
- **D173. `pantalla_cliente1.js` sigue aunque el registro falle** (no es mía; lo propongo).
  - La línea 38 hace `page.request.post(base + '/auth/register', …)` y no mira el status.
  - Con el límite de 5 por hora (D145), a partir del 6.º registro sigue sin usuario, y cada sabotaje cae por timeout de click y no por su falla.
  - El arnés se vuelve ROJO? en vez de decir «429».
  - (a) Que falle con «no se pudo registrar: 429», como `pantalla_borrador1.js:47`, y que el arnés levante una base nueva por sabotaje, como `borrador1.sh`.
  - (b) Dejarlo.
  - **Recomiendo (a),** para MARIA o para quien tenga el arnés. Yo no lo toqué.

## Rojo antes, verde después

`pantalla_borrador1.js` sobre la base `4555f7c4`:
```
FALLA: el usuario no llega a tiempo: el arranque la sacó de Clientes y la llevó a upload
FALLA: hay una operación de antes: el arranque la sacó de Clientes y la llevó a review
FALLA: hay una operación de antes: no apareció el aviso «Quedó guardada la operación»
rc=1
```
Esos textos son de la primera versión de la prueba. Los casos «sin ir a ninguna pantalla» y «el tour la lleva a la carga» los sumé en `b0d6c274`. Su rojo con el arreglo revertido son los sabotajes `siempre_tarde`, `tour_ocupa` y `queda_carga`, de abajo.

## Sabotaje: `scripts/testing/sabotajes/borrador1.sh b0d6c274`

Cada parte del arreglo se revierte en un worktree descartable, con una base nueva por corrida (el registro tiene límite por hora). Salida entera:
```
OK    | producto: ok: el arranque no saca de Clientes y recupera si no fue a ninguna pantalla
ROJO bien | decide_tarde:
        FALLA: hay una operación de antes: el arranque tenía que dejarla en clientes y la llevó a review
        FALLA: hay una operación de antes: no apareció el aviso «Quedó guardada la operación»
        FALLA: hay una operación de antes: la operación de antes se cargó en la pestaña
        FALLA: hay una operación de antes: la operación de antes ya no está guardada
ROJO bien | sin_freno:
        FALLA: el usuario no llega a tiempo: el arranque tenía que dejarla en clientes y la llevó a upload
        FALLA: hay una operación de antes: el arranque tenía que dejarla en clientes y la llevó a upload
ROJO bien | siempre_tarde:
        FALLA: sin ir a ninguna pantalla: el arranque tenía que dejarla en review y la llevó a upload
        FALLA: sin ir a ninguna pantalla: la operación de antes no se recuperó
        FALLA: el tour la lleva a la carga: el arranque tenía que dejarla en review y la llevó a upload
        FALLA: el tour la lleva a la carga: la operación de antes no se recuperó
ROJO bien | tour_ocupa:
        FALLA: el tour la lleva a la carga: el arranque tenía que dejarla en review y la llevó a upload
        FALLA: el tour la lleva a la carga: la operación de antes no se recuperó
ROJO bien | queda_carga:
        FALLA: el tour la lleva a la carga: el arranque tenía que dejarla en review y la llevó a upload
corridas que no dieron lo esperado: 0
rc=0
```
El sabotaje es propio porque la pieza toca el borrador guardado de la usuaria, que es dato (§3).

## Puertas

| Puerta | SHA | Resultado |
|---|---|---|
| Suite completa | `d3dfc2e4` (producto igual al de `524a8f00`) | 5907 passed, 110 skipped, 3 xfailed, rc=0 |
| compileall | `d3dfc2e4` | rc=0 |
| Los 6 archivos de pytest que leen `app_v2.js` | `b0d6c274` | 103 passed, 1 skipped, 2 xfailed |
| `borrador1.sh` | `b0d6c274` | 5 ROJO bien, 0 inesperadas |
| `cliente1.sh` | `b0d6c274` | rc=1: 4 ROJO correcto, 30 ROJO? por 429 (D145, abajo) |
| `foco_cliente1.sh` | `b0d6c274` | cortado por mí (rc=143): su API dio 5 registros con 200 y 42 con 429, D145 |
| `destino1.sh` | `b0d6c274` | PENDIENTE_DESTINO |
| `despacho1a.sh` | `b0d6c274` | PENDIENTE_DESPACHO |
| `orden1.sh` | `b0d6c274` | «FALLA: no se pudo registrar el usuario de prueba: 429»: es D145 |

Los 6 archivos son `test_sufijos1`, `test_ncm_batch_frontend`, `test_punta_a_punta1`, `test_regression_phase0`, `test_static_endpoints` y `test_tour_onboarding`.

**Los ROJO? de `cliente1` son 429, no esta pieza**
- El arnés usa una sola API y una sola base. Cada corrida de `pantalla_cliente1.js` registra un usuario nuevo y no mira el status (D173).
- El log de la API a mitad de la corrida, contando los `POST /auth/register`:
  ```
        5 "POST /auth/register HTTP/1.1" 200
        6 "POST /auth/register HTTP/1.1" 429
  ```
- Los 5 con 200 son la base y los 4 primeros sabotajes, que dieron ROJO correcto:
  - «el CUIT no se marca»;
  - «el domicilio no se marca»;
  - «el inicio de actividad no se marca»;
  - «el inicio de actividad vuelve a esconderse».
- Desde el 5.º sabotaje («no avisa lo que falta»), cada uno cae por `locator.click` o `page.waitForFunction: Timeout 30000ms` y no por su falla.
- Los mismos sabotajes dieron ROJO correcto en corridas anteriores a D145.

<details><summary>chequeo-6 4555f7c4..b0d6c274</summary>

```
chequeo-6 4555f7c4..b0d6c274: avisos para mirar, no un veredicto
producto +7/−9
arnés +183/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/app_v2.js: 1201 → 1199
avisos: 0
rc=0
```
</details>

## Revisiones

**Adversario: Sonnet, esfuerzo alto, sobre `42f0ed9b`**

| # | Hallazgo | Qué hice |
|---|---|---|
| 1 | Con el tour, una usuaria lenta y una tecla, la operación quedaba «pendiente» y no se recuperaba | Arreglado en `cc8b834b`; los casos y el sabotaje en `b0d6c274` |
| 2 | La prueba no distinguía «siempre adoptarTarde» | Casos nuevos y sabotaje `siempre_tarde` |
| 3 | El aviso «pendiente» no se borra y pisa el de «lleno» (baja) | D170 |
| 4 | Pérdida con el tour después de recuperar (media; ya estaba antes) | D171 |

Probó sin hallazgo:
- esperas de 0, 2 y 5,5 s;
- ir a Clientes y volver;
- recargar;
- respuestas 500;
- `recuperada` dos veces.

**`/code-review high` sobre lo que cambió hasta `42f0ed9b`**

| # | Dónde | Hallazgo | Qué hice |
|---|---|---|---|
| 1 | `pantalla_borrador1.js` | «ya no está guardada» no distinguía el defecto: adoptarla copia el estado a la clave de la pestaña | Arreglado: mira la clave de esta pestaña y la de la otra por separado |
| 2 | `pantalla_borrador1.js` | No prueba cambiar de pantalla mientras corre `buscarBorrador` | Queda como riesgo bajo; el freno es el mismo `currentScreen` |
| 3 | `pantalla_borrador1.js` | El caso «tarde» leía la pantalla sin esperar al arranque | Arreglado: espera una condición |
| 4 | `pantalla_borrador1.js` | El cierre con `runBeforeUnload` no tenía tope | Arreglado: tope de 10 s |
| 5 | `borrador1.sh` | `levantar` aceptaba cualquier `/health` del puerto | Arreglado: exige que la API propia siga viva |
| 6 | `app_v2.js` | La carga a la que lleva el tour contaba como elección de ella | Arreglado en `cc8b834b` |
| 7 | `app_v2.js` | Texto «pendiente» y no vuelve a ofrecerse | D170 |
| 8 | `app_v2.js` | Comentarios viejos | Arreglado en `6c2b3383` |
| 9 | `app_v2.js` | La adopción en dos estilos, en tres lugares | D172 |
| 10 | `borrador1.sh` | Sabotaje propio para un arreglo de navegación | Justificado: toca el borrador guardado (§3) |

## Riesgos y lo no corrido

- **`cc8b834b` no pasó por un segundo adversario ni por otro `/code-review`.** Lo cubren los casos nuevos y los sabotajes `tour_ocupa` y `queda_carga`.
- **Queda una ventana tardía:** si el usuario tarda más que el tope de 4 s del arranque y ella, con el tour en la carga, toca otra pantalla, la operación queda «pendiente» como en D170.
- **La suite corrió sobre `d3dfc2e4`, no sobre `b0d6c274`.** Entre los dos cambian sólo `app_v2.js` (+6/−5) y el arnés. Sobre `b0d6c274` corrí los 6 archivos de pytest que leen `app_v2.js`.
- **No corrí otros arneses de navegador** fuera de los cuatro que pide D143 (a) y `orden1`.

## Comandos para reproducir

```bash
git diff --stat 4555f7c4 b0d6c274 -- proyecto_maria/ CHANGELOG.md   # sólo app_v2.js (+7/−9) y CHANGELOG.md (+5)
PY=<venv>/bin/python TMPDIR=/tmp/cdi-s1 scripts/testing/sabotajes/borrador1.sh b0d6c274   # «OK    | producto» y 5 «ROJO bien», «corridas que no dieron lo esperado: 0»
git grep -n -E '\bD17[0-9]\b' origin/claude/dev-maria -- docs/pm   # vacío: el rango D170 en adelante está libre
```

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. BORRADOR-1 entregada con este informe, encima de 1732cd72; D170 a D173 abiertas (mis D siguen en D174). Sigue CONEXIONES-1 parte B: lo que tenía a medio hacer está en el parche conexiones1_b_wip.patch del scratchpad. No integrar 0231eee. Rutina trig_011UpBfwEu9TUzoNUrviqoP5 /respondio cada 2 h, minuto 15.
