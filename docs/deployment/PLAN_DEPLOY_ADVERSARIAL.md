# Plan adversarial para llegar a deploy

> Escrito para el dueño del producto. Complementa `ESTADO_DEPLOY.md`, que dice
> **en qué estado está**. Este dice **cómo salir**, y con qué método.

---

## La idea en una frase

En vez de que alguien construya y después alguien "revise", cada pieza tiene
**dos agentes enfrentados**: uno que la deja andando (Azul) y otro cuyo único
trabajo es **romperla y demostrarlo** (Rojo). Nada pasa a la ronda siguiente
sin que el Rojo se quede sin ataques.

Por qué así y no una revisión normal: la revisión normal ya falló. El script
`deploy-cloud-run.sh` estuvo roto meses — habría deployado con usuarios demo y
la API documentada al público — y nadie lo vio, porque nadie intentó usarlo de
verdad. Leer código no encuentra eso. Atacarlo sí.

---

## Las 3 reglas del juego

1. **El Rojo gana los empates.** Si no hay evidencia de que algo está
   arreglado, está roto. "Yo lo probé y andaba" no es evidencia.
2. **Evidencia = comando + salida + veredicto.** Cualquiera lo tiene que poder
   repetir. Un hallazgo sin comando para reproducirlo no cuenta, y un arreglo
   sin comando que lo demuestre tampoco.
3. **El Rojo no toca código de producción.** Escribe ataques, pruebas y
   evidencia. Si el Rojo arregla lo que él mismo rompió, se pierde el control
   cruzado y volvemos a una persona sola revisándose a sí misma.

Y una regla mía como PM: **corto por over-engineering.** Si una ronda se
convierte en investigación académica, la cierro con lo que haya y anoto la
deuda. El objetivo es deployar, no ganar un premio.

---

## Los agentes

| Agente | Qué hace | Cuándo entra |
|---|---|---|
| **PM / Árbitro** (yo) | Decide qué hallazgo se arregla y cuál se anota como deuda. Corta empates y ceremonial. | Todas las rondas |
| **Azul-Secretos** | Rota claves, limpia el repo. | Ronda 0 |
| **Rojo-Secretos** | Busca claves vivas en **todo el historial de git**, no en la foto actual. | Ronda 0 |
| **Azul-Deploy** | Deja un solo destino funcionando de punta a punta. | Ronda 1 |
| **Rojo-Config** | Intenta deployar mal a propósito, de diez formas distintas. | Ronda 1 |
| **Azul-Backend** | Arregla lo que el intruso encuentre. | Rondas 2-3 |
| **Rojo-Intruso** | Ataca la app corriendo: sesiones, datos de otros usuarios, endpoints de admin. | Rondas 2-3 |
| **Rojo-Aduana** | Ataca **el producto**: intenta que salga un MARIA.TXT inválido o que el sistema invente una NCM sin que el despachante confirme. | Ronda 4 |
| **Azul-QA / Rojo-QA** | Arreglan y verifican el cuelgue de la suite. | Ronda 5 |

Los "agentes" pueden ser sesiones separadas de IA, o vos y yo en momentos
distintos. Lo que importa es que **el que construye no sea el que valida**.

---

## Las rondas

Cada ronda tiene una **puerta**: no se avanza sin pasarla. Están ordenadas por
riesgo, no por comodidad.

---

### Ronda 0 · Secretos 🔴 *bloqueante*

**Azul-Secretos**
- Rotar la `GEMINI_API_KEY` en Google AI Studio (borrar la vieja, no solo
  crear una nueva).
- Rotar el DSN de Sentry si es barato hacerlo.
- Confirmar que `.env` y `.env.afip` siguen fuera de git.

**Rojo-Secretos**
- Escanear **el historial completo**, no el árbol actual:
  `git log -p --all` contra patrones de clave (`AIza…`, `sk-…`, `APP_USR-…`,
  `postgres://usuario:clave@`).
- Probar que la clave vieja de Gemini **ya no funciona**: una llamada a la API
  con esa clave tiene que dar 400/403.
- Revisar `docs/` completo, no solo `docs/audits/`.

**Puerta G0:** cero claves vivas en el historial. La clave vieja, muerta y
comprobado que está muerta.

> Por qué primero: mientras la clave siga viva, todo lo demás es decoración.
> Y si al final se decide reescribir el historial de git, conviene saberlo
> antes de acumular commits encima.

---

### Ronda 1 · Configuración de deploy 🔴 *bloqueante*

**Azul-Deploy**
- Elegir **un** destino (recomiendo Railway) y archivar el resto: el
  `firebase.json` muerto y el script de Cloud Run que sobra.
- Dejar el camino elegido documentado en un solo lugar.

**Rojo-Config** — intenta deployar mal, a propósito, y anota qué pasa:

| Ataque | Qué tiene que pasar |
|---|---|
| Sin `ALLOWED_ORIGINS` | El preflight corta **antes** de buildear |
| `ALLOWED_ORIGINS=*` | Corta |
| `JWT_SECRET_KEY` corta o con `secret` adentro | Corta |
| Sin `DATABASE_URL` | Corta (si no, se pierden los datos en cada deploy) |
| `ENVIRONMENT` sin poner | Corta |
| `ALLOWED_ORIGINS` con **dos** URLs separadas por coma | **Llega entera**, no truncada |
| Token de MercadoPago `TEST-` en producción | Avisa, no corta |
| Correr los dos scripts de Cloud Run seguidos | No deberían existir los dos |

**Puerta G1:** toda mala configuración falla **ruidosa y temprano**. Ninguna
llega a producir un servicio vivo y mal configurado.

> El caso de las dos URLs con coma no es teórico: es exactamente el tipo de
> error silencioso que dejaría el CORS roto en producción sin que nadie se dé
> cuenta hasta que un usuario no puede entrar.

---

### Ronda 2 · La imagen real, atacada 🔴 *bloqueante*

⚠️ **Esta ronda necesita Docker o un entorno de staging.** En el entorno donde
hice la revisión no había Docker: todo lo que verifiqué fue con la app corriendo
directo, **no con la imagen que realmente se deploya**. Es un hueco real.

**Azul-Deploy** buildea la imagen y la levanta con variables de producción.

**Rojo-Intruso** ataca el contenedor:

- `/docs`, `/redoc`, `/openapi.json` → tienen que dar 404
- Login con `demo`/`demo123`, `premium`/`premium123` → tiene que fallar
- Cookie de sesión → tiene que traer `Secure` y `HttpOnly`
- Petición desde un origen no autorizado → CORS la tiene que rechazar
- `/api/admin/*` sin login → 401
- `/dev/dashboard` con un usuario común → 403
- Pedir un archivo sensible por la ruta de estáticos (`.env`, `.db`, logs)
- Golpear un endpoint hasta pasar el rate limit → tiene que cortar
- Matar el contenedor y levantarlo → los datos tienen que seguir ahí
  (si no siguen, `DATABASE_URL` está mal y lo vas a descubrir acá y no con
  clientes adentro)

**Puerta G2:** los diez ataques, todos rechazados, con la salida pegada como
evidencia.

---

### Ronda 3 · Datos de un cliente contra otro 🔴 *bloqueante*

Este es **el riesgo más grande del negocio**. No es un bug técnico: son datos
de importación de despachantes. Que el despachante A vea las operaciones del
despachante B es el tipo de cosa que termina el producto.

**Rojo-Intruso**, con dos usuarios creados de cero:
- Pedir el cliente de otro usuario por ID
- Pedir un cliente ajeno por CUIT
- Descargar el MARIA.TXT de una operación ajena
- Ver el historial de productos y las notas NCM de otro
- Repetir con el usuario B borrado a mitad de camino
- Repetir todo apuntando al importador de clientes (CSV/XLSX)

**Azul-Backend** arregla lo que aparezca. Cada arreglo va con una prueba
automática nueva, para que no vuelva.

**Puerta G3:** cero fugas entre usuarios. Cada intento cerrado con una prueba
en `tests/`.

---

### Ronda 4 · El producto, atacado 🟡 *importante*

Las rondas anteriores cuidan el servidor. Esta cuida **la promesa del
producto**: *"la IA recomienda, el humano confirma; el TXT es trazable a lo que
el usuario aprobó en pantalla"*.

**Rojo-Aduana** intenta romper esa promesa:
- Generar un MARIA.TXT con peso, cantidad o valor en cero o negativo
- Generar con una NCM de 8 dígitos, sin la posición SIM completa ni el DC
- Que la memoria del cliente **autocomplete un peso** de una factura anterior
  (eso ya se cerró en julio — hay que verificar que siga cerrado)
- Agrupar ítems que mezclan NCM, origen o unidad
- Que una sugerencia de Gemini con una NCM inventada llegue a la pantalla sin
  validarse contra el catálogo ARCA
- Con Gemini apagado o caído: que el sistema invente algo en vez de decir
  "sin coincidencia segura"
- Subir un PDF corrupto, vacío, gigante, o que no sea un PDF

**Puerta G4:** ningún camino produce un TXT que el despachante no aprobó
explícitamente. Con Gemini caído, el sistema dice que no sabe — no adivina.

> Esta ronda es la que un equipo normal se saltea, porque "no es un bug de
> seguridad". Es la que más te puede costar: un TXT mal generado lo rebota
> aduana con el nombre de tu cliente encima.

---

### Ronda 5 · Las pruebas 🟢 *después del deploy*

**Rojo-QA** deja el cuelgue reproducible en un comando y demuestra que **CI
hoy no lo detectaría** (corre 4 archivos elegidos a mano, no la suite).

**Azul-QA**:
- Cambiar `pytest.ini` a `--timeout-method=signal`, para que un test colgado
  muera en vez de trabar todo.
- Arreglar la causa (los cuelgues son todos de billing / trial / respuestas
  402 — probablemente una sola causa).
- Ampliar `ci.yml` para que corra la suite entera.

**Rojo-QA** verifica: rompe un test a propósito y confirma que ahora CI lo
agarra.

**Puerta G5:** la suite termina, y un test roto hace fallar CI.

> Va después del deploy a propósito. Es deuda real, pero no frena salir: el
> flujo principal ya tiene E2E y las 4 suites críticas pasan.

---

### Ronda 6 · Salir, y probar la vuelta atrás

- Deployar.
- Verificar `/health`.
- **Hacer un flujo completo de verdad**: usuario nuevo → cliente → factura →
  revisar → SIM 11 + DC → validar → descargar MARIA.TXT.
- **Probar el rollback antes de necesitarlo.** Volver a la versión anterior a
  propósito, confirmar que la app sigue viva y los datos siguen ahí, y volver
  a la nueva.

**Puerta G6:** rollback probado. Si no se probó, no existe.

---

## Resumen de puertas

| Puerta | Qué asegura | ¿Frena el deploy? |
|---|---|---|
| G0 · Secretos | Ninguna clave viva dando vueltas | 🔴 Sí |
| G1 · Configuración | Una mala config falla temprano, no en producción | 🔴 Sí |
| G2 · Imagen real | El contenedor que se deploya está cerrado | 🔴 Sí |
| G3 · Aislamiento | Un despachante no ve datos de otro | 🔴 Sí |
| G4 · Producto | El TXT sale de lo que el humano aprobó | 🟡 Muy recomendable |
| G5 · Pruebas | La suite termina y CI la mira | 🟢 No |
| G6 · Rollback | Se puede volver atrás | 🔴 Sí |

---

## Dónde este método no vale la pena

Para ser honesto sobre el costo:

- **Frontend y textos**: no necesitan adversarial. Se mira y se arregla.
- **Ronda 5**: podría hacerla una sola persona. La puse enfrentada solo porque
  el enunciado del `HANDOFF` ("flaky") ya subestimó una vez el problema.
- **Rondas 0 a 4**: acá sí. Son exactamente las áreas donde revisar sin atacar
  ya demostró que no alcanza.

Si querés una versión corta: **G0, G1 y G3**. Son las tres donde un error se
paga con datos de clientes o con el servicio caído, y las tres se resuelven en
una tarde.

---

## Para empezar

Decime dos cosas y arranco:

1. ¿Railway o Cloud Run? (recomiendo Railway)
2. ¿Tenés dónde correr Docker, o vamos directo a un staging para la Ronda 2?
