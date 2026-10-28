# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORDEN-1, vuelta 2: tu devolución del 2026-10-28 20:08 UTC sobre `973a1ed`

Entrego cerrada sólo esta pieza, porque Emi pidió frenar a las 22:00 UTC.
**COBRO-MP-1 no está entregado.** Sus arreglos están en la rama, pero le
faltan `/code-review high`, `/security-review` y el informe. Como pediste no
lanzar subagentes nuevos, esas dos revisiones no las corrí. El estado está
al final.

### Decisiones

Nada para decidir. Hice lo de la devolución con D1 = (a), con tus dos
condiciones: si el mismo usuario vuelve a entrar, la pestaña sigue
guardando, y cuando deja de guardar, lo avisa a la vista. Los supuestos y
los riesgos están abajo.

| Qué | SHA |
|---|---|
| Rojo: casos l a y (sesión revisada, aviso, recuperación tardía) | `4c0ccef` |
| **Producto:** la pestaña revisa la sesión antes de guardar, recupera tarde y avisa | `d24c1d8` |
| Rojo: k, z, z2, z3, z4 (y m2 como guarda) | `671a16f` |
| **Producto:** la recuperación tardía no pisa la pantalla ni una subida; tope de 10 s | `92890b6` |
| Rojo: z6 y z7 (y z5 y z8, que distinguen sus mutantes) | `3961a53` |
| **Producto:** no pisa una pestaña tocada; sin usuario a los 4 s avisa que no guarda; la primera consulta se corta | `ad87f78` |
| Sabotajes de z6 y z7 | `e4e8ad2` |
| z7 deja colgada la consulta en camino; un sabotaje que había quedado sin su patrón | `86c9d84` |
| Informe | este commit |

En el medio van también commits de COBRO-MP-1 (`5c12041`…`3761589`,
`1e67ba6`…`84d8062`). No son parte de esta entrega.

Archivos de producto tocados en esta vuelta:
`proyecto_maria/static/v2/app_v2.js`, `proyecto_maria/static/v2/screens/upload.js`
(el contador `subiendo`), `proyecto_maria/templates/dashboard_v2.html`
(`#avisoBorrador`) y `CHANGELOG.md`.

### Qué hace ahora, punto por punto

1. **La sesión se revisa antes de guardar y antes de recuperar.**
   - La sesión se reconoce por la cookie CSRF. Si cambió desde que se
     confirmó al dueño, la pestaña no guarda ni borra hasta volver a
     preguntar quién es.
   - **Mismo usuario:** sigue guardando, sin aviso (m y m2).
   - **Otro usuario o sesión cerrada:** deja de guardar y avisa (l, n, o e y).
   - **Otro usuario que entra con la primera consulta en camino** (z8): no
     guarda a su nombre y avisa «Entró otro usuario».
2. **La recarga con el usuario lento o caído recupera o avisa.**
   - **Si el usuario llega tarde,** la operación de antes vuelve (p, z y
     z5), pero sólo con la pestaña sin tocar: vacía, en la carga y sin
     subida en curso. Un clic, una tecla o soltar un archivo cuentan como
     tocarla (z6: el diálogo de archivos abierto). Si se tocó o hay algo
     cargado, la operación de antes queda guardada y se avisa, sin mover
     la pantalla (z, z2 y z6).
   - **Si el usuario no llega en 4 s,** avisa «No se pudo comprobar la
     sesión: esta pestaña no guarda la operación por ahora.» (z7, con la
     consulta en error o colgada). Cuando llega, el aviso se va y la
     operación vuelve.
   - **La primera consulta** se corta a los 10 s y se reintenta (z4 y z7
     colgada).
3. **Cuando la pestaña corta, lo dice a la vista** en `#avisoBorrador`, con
   un aviso por motivo: otro usuario, sesión cerrada, sin red, sin lugar
   para guardar o recuperar (z3) y operación pendiente.
4. **El `CHANGELOG`** ya no dice que deja de autoguardar en el caso de la
   devolución. Las tres líneas de «ORDEN-1, vuelta 2» dicen lo que hace
   ahora.
5. **Tus mutantes.** Cada uno tiene su sabotaje en
   `scripts/testing/sabotajes/orden1.sh`:

   | Mutante | Sabotaje |
   |---|---|
   | La rama del dueño distinto | «otro usuario recupera la operación» |
   | `sinSesion`, las dos líneas | «un 401 no marca la sesión vencida» y «el reintento no corta con la sesión vencida» |
   | `return !!currentUser` → `true` | «un corte de red da por cargado al usuario» |
   | El tope de 30 s | «la espera crece sin tope» |
   | El crecimiento de la espera | «la espera no crece» |
   | `ESPERA_PESTANA_MS` | «una pestaña muerta sin avisar no se da por muerta nunca» |
   | `pageshow` | «al volver de la caché…», dos sabotajes |
   | El `borrarBorrador()` de `pagehide` | «al cerrar no se borra la operación terminada» |
   | El `borrarBorrador()` del intervalo | «con la pestaña abierta no se borra la operación terminada» |
   | El barrido de vencidos de otro usuario | «el vencido se borra sólo si es del usuario» |
   | `parsed.v !== 1` | «se acepta un sobre de otra versión» |

### Puertas

| Puerta | SHA | Resultado |
|---|---|---|
| Pantalla de ORDEN-1, los 36 casos (`pantalla_orden1.js`) | árbol = `ad87f78` | «OK: ORDEN-1 en el navegador», «salida 0» |
| Pantalla, z7 y z con la prueba de `86c9d84` | producto de `e4e8ad2` | «OK: ORDEN-1 en el navegador», «salida 0» |
| Sabotajes (`scripts/testing/sabotajes/orden1.sh`) | `e4e8ad2` | 62 en ROJO, «sabotajes sin rojo: 2» (ver abajo) |
| Sabotajes, de nuevo | `86c9d84` | 64 en ROJO, «sabotajes sin rojo: 0», salida 0 |
| `tests/test_orden1.py` | `e4e8ad2` | «24 passed, 1 xfailed, 3 warnings in 0.27s» |
| Suite completa | — | **no corrida** |
| `/code-review high` y `/security-review` | — | **no corridos**: en una vuelta corre sólo el adversario Sonnet alto |

Sobre `e4e8ad2`, los sabotajes encontraron dos huecos, los dos en las
pruebas y no en el producto. Los arreglé en `86c9d84`:

- «VERDE | la primera consulta colgada no se corta: la prueba no lo vio».
  z7 sacaba la ruta que colgaba la consulta y la consulta en camino
  contestaba igual, así que no probaba el corte. Ahora las consultas que
  salieron antes siguen colgadas hasta después de mirar, y sólo las nuevas
  contestan. Con ese mutante da «FALLA: al recargar la consulta del usuario
  no contesta y cuando vuelve a contestar la pestaña no se entera en 30 s»,
  y sobre el producto, OK.
- «ROTO | el usuario tarde recupera aunque la pestaña esté fuera de la
  carga: el sabotaje no encontró su patrón». `ad87f78` cambió esa línea.
  Ahora muta sólo la condición de la pantalla y da «FALLA: el usuario llegó
  tarde y la pestaña se fue de la pantalla en que estaba a review».

Los rojos de esta vuelta, copiados de la salida, antes del arreglo:

- **z6, sobre `84d8062`:** «FALLA: se abrió el diálogo de archivos antes
  de que llegara el usuario y la operación de antes de recargar se perdió:
  ["DEL-PDF"]».
- **z7, sobre `84d8062`:** «FALLA: al recargar la consulta del usuario da
  error y en 8 s la pestaña no avisa que no guarda».
- **z8, con el mutante que saca `|| getCsrfToken() !== sesionAlAbrir`:**
  «FALLA: entró otro usuario con la primera consulta del usuario en camino
  y lo cargado se guardó a nombre de él: [{"user":"ord1z8b_…","closed":false,…}]».
  Sobre el producto, z8 da OK.

### Adversario (Sonnet, esfuerzo alto, sobre `92890b6`)

| # | Severidad | Hallazgo | Qué hice |
|---|---|---|---|
| A1 | MEDIA | Con el diálogo de archivos abierto antes de que llegue el usuario, la operación recuperada se pierde al elegir el archivo | Caso z6, rojo y arreglado en `ad87f78` (`pestanaTocada`) |
| A6 y A11 | MEDIA | Si el usuario nunca llega (500 o consulta colgada), lo cargado no se guarda y no hay aviso | Caso z7, rojo y arreglado: aviso a los 4 s y corte de la primera consulta |
| A10 | MEDIA (prueba) | Ninguna prueba distinguía la mitad «la sesión cambió mientras volvía la consulta» | Caso z8 y su sabotaje |
| — | BAJA (prueba) | Si se saca el `subiendo--`, no da rojo | **No hecho**: riesgo |
| A4 | BAJA | La recuperación tardía pisa el cliente elegido en la carga | Elegirlo con un clic ya marca la pestaña tocada, así que no se pisa. No tiene caso propio |
| A2 | BAJA | El mismo usuario que vuelve a entrar durante la carga inicial ve «Entró otro usuario» y la pestaña deja de guardar hasta recargar | Riesgo: falla del lado seguro |
| A9 | BAJA | `adoptarBorrador` puede escribir `user:null` si la sesión cambia mientras espera el candado. La ventana es de milisegundos y hasta 1,5 s con un candado trabado | Riesgo |
| A3 y A5 | Informativa | El aviso «pendiente» (y el de «sin lugar») se pierde cuando otro aviso lo reemplaza y después se limpia | Riesgo |
| — | Informativa | Dos mutantes de `revisarSesion` y `confirmarSesion` sobreviven, porque las otras guardas cubren el mismo caso | Nada: es redundancia |

### Supuestos (reversibles)

- **Cualquier toque desactiva la adopción tardía,** aunque sea un clic sin
  efecto. En ese caso la operación de antes queda guardada y avisada, no
  se pierde.
- **La espera de 4 s y el tope de 10 s** (`ESPERA_USUARIO_MS` y
  `ESPERA_SESION_MS`) los elegí yo.

### Riesgos

- **`finalize.js:667`:** el TXT generado desde la pestaña cuenta en las
  operaciones de la sesión de ese momento. Ya estaba antes de la pieza;
  sin arreglo acá.
- **localStorage lleno:** al guardar, avisa «sin lugar»; al recuperar,
  también (z3). El aviso se pierde si otro lo reemplaza (A5).
- **`/logout`** no rota a un CSRF nuevo. Un logout y un login del mismo
  usuario entre dos revisiones se ven como «mismo usuario», que es lo
  pedido.
- **bfcache** se probó simulado, con `pageshow` `persisted`, no en un
  navegador real.
- **`pagehide` con una sesión ajena** no marca nada; la pestaña queda
  viva hasta que vence `ESPERA_PESTANA_MS`.
- **El contador `subiendo`:** no encontré fuga, pero no hay caso que pruebe
  que vuelve a 0.
- **z8 simula la consulta tomando las cookies del momento en que sale,**
  como hace el navegador. No es un segundo navegador.
- A2 y A9, en la tabla.

### Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout --detach 86c9d84
PUERTO=8853 PY=<venv>/bin/python bash scripts/testing/sabotajes/orden1.sh 86c9d84
#   tiene que terminar en «sabotajes sin rojo: 0» (64 en ROJO)
#   entre ellas «la recuperación tardía no mira si se tocó la pestaña», «la primera consulta colgada no se corta»,
#   «sin usuario a tiempo no se avisa» y «la primera consulta no mira si la
#   sesión cambió mientras volvía»
CASOS=z6,z7,z8 BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_orden1.js
#   con la API del árbol levantada: tres OK y «OK: ORDEN-1 en el navegador»
```

## COBRO-MP-1: estado, sin entregar

- En la rama están A a E, la cancelación que espera al checkout
  (`472e389` y `87094a1`), su sabotaje (`4115f32`) y la cancelada con un
  checkout nuevo (`1e67ba6`…`84d8062`).
- `scripts/testing/sabotajes/cobro_mp1.sh` sobre `84d8062`: 63 en ROJO,
  «sabotajes con falla: 0», «salida 0».
- **Faltan** `/code-review high`, `/security-review` y el informe con las D.
  Los corro cuando se retome.

/compact conservar: Dev 1 (técnica), sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, rutina trig_011UpBfwEu9TUzoNUrviqoP5 (apagada por la PM), aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM). Emi (28/10 22:00 UTC): todo frenado hasta el sábado; no arrancar piezas ni lanzar subagentes hasta que la PM diga de volver. ORDEN-1 (vuelta 2) entregada en 86c9d84 + informe. COBRO-MP-1 sin entregar: falta /code-review high, /security-review e informe (sabotajes 63 ROJO sobre 84d8062). Después COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1, BACKUP-1a, EXCEL-2c.
