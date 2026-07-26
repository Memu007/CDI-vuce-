# Estado de deploy — revisión del 2026-07-26

> Revisión de PM sobre si el proyecto está listo para salir a producción.
> Escrito para el dueño del producto, no para un programador.

---

## Conclusión

**Todavía no está listo para deploy, pero falta poco y lo que falta es corto.**

La aplicación en sí anda bien: arranca en modo producción, el `/health`
responde, las protecciones de seguridad están puestas y el flujo principal
(subir factura → revisar → generar MARIA.TXT) tiene pruebas automáticas que
pasan.

Lo que frena el deploy son cuatro cosas, ninguna del producto en sí:

1. Una clave de Gemini real quedó escrita en un documento del repo. Hay que
   **rotarla**.
2. Los scripts de deploy a Google Cloud **no pasaban las variables críticas**:
   el servicio arrancaba mal o directamente no arrancaba. **Ya está arreglado.**
3. Hay **tres destinos de deploy** configurados a la vez (Railway, Cloud Run y
   Firebase). Hay que elegir uno.
4. La suite de pruebas completa **no termina**: se cuelga en dos archivos y
   hay pruebas en rojo que CI no mira. No frena el deploy, pero significa que
   "las pruebas pasan" hoy es una afirmación parcial.

---

## 1. Lo que se verificó (y funciona)

| Qué | Resultado |
|---|---|
| Arranque real con `ENVIRONMENT=production` | ✅ Arranca y sirve |
| `/health` | ✅ `{"status":"ok","database":"ok"}` |
| `/docs` (Swagger) cerrado en producción | ✅ 404 |
| Usuarios demo NO se crean en producción | ✅ Verificado en la base |
| Cabeceras de seguridad (CSP, HSTS, X-Frame-Options…) | ✅ Todas presentes |
| Cookies con flag `Secure` en producción | ✅ |
| CORS: la app se niega a arrancar con `*` | ✅ Corta con mensaje claro |
| `JWT_SECRET_KEY` débil: la app se niega a arrancar | ✅ Corta con mensaje claro |
| Smoke test (`smoke_friccion.sh`) | ✅ Pasa |
| Pruebas críticas de CI (4 archivos) | ✅ 87 pasadas, 1 salteada |

Las dos negativas ("se niega a arrancar") son buenas: es la app defendiéndose
de una mala configuración en vez de salir a producción insegura.

---

## 2. Lo que hay que hacer antes de deployar

### 🔴 Rotar la clave de Gemini — lo tenés que hacer vos

En `docs/audits/AUDITORIA_PRE_TESTING_5_USUARIOS.md` estaba escrita una clave
real de Gemini. La dejé tachada en el archivo, pero **sigue en el historial de
git**: cualquiera con acceso al repo la puede leer.

Qué hacer:

1. Entrar a Google AI Studio → API keys.
2. Borrar la clave vieja y crear una nueva.
3. Cargar la nueva en las variables del servidor (`GEMINI_API_KEY`), nunca en
   un archivo del repo.

También había un fragmento del DSN de Sentry en el checklist de deploy. Ya lo
saqué. El DSN de Sentry es menos grave (sirve para mandar errores, no para
leerlos), pero conviene rotarlo también si es fácil.

### ✅ Destino de deploy: Railway — decidido el 2026-07-26

| Destino | Archivos | Estado |
|---|---|---|
| **Railway** | `railway.json`, `Dockerfile` | **El camino oficial.** Guía: `RAILWAY_SETUP.md`. |
| Google Cloud Run | `cloudbuild.yaml`, `scripts/deployment/deploy-cloud-run.sh` | Se deja como alternativa, arreglada y con un solo script. No es el camino actual. |
| ~~Firebase Hosting~~ | ~~`firebase.json`~~ | **Borrado.** Apuntaba a una función `api` que no existe en este repo. Si algún día hace falta, está en el historial de git. |

También se borró `deploy_cloudrun.sh` de la raíz, que deployaba un servicio
distinto (`cdi-maria`) al del otro script (`cdi-backend`): correr los dos
dejaba dos apps vivas con bases separadas.

> Nota: se dejó **una** vía de Cloud Run en vez de borrar las dos. Cuesta cero
> mantenerla y evita rehacer todo desde cero si Railway no convence. La
> confusión venía de tener dos scripts peleados, no de que exista la opción.

### 🟡 Cargar las variables de producción

Sin estas la app no arranca (y es a propósito):

- `ENVIRONMENT=production`
- `JWT_SECRET_KEY` — 32+ caracteres al azar
- `ALLOWED_ORIGINS` — la URL real, ej. `https://cdi.tu-dominio.com`

Sin esta, se pierden los datos en cada deploy:

- `DATABASE_URL` — Postgres. Si falta, la app usa un archivo dentro del
  contenedor, y ese contenedor se borra entero en cada reinicio.

Para chequearlas sin deployar nada:

```bash
./scripts/deployment/preflight_env.sh
```

---

## 3. Lo que se arregló en esta revisión

| Arreglo | Por qué importaba |
|---|---|
| `deploy_cloudrun.sh` y `scripts/deployment/deploy-cloud-run.sh` ahora pasan `JWT_SECRET_KEY`, `ALLOWED_ORIGINS` y `DATABASE_URL` | Antes no las pasaban: el primero dejaba el servicio reiniciándose en loop; el segundo **ni siquiera ponía `ENVIRONMENT=production`**, así que habría deployado con usuarios demo, `/docs` abierto y cookies sin `Secure`. |
| Nuevo `scripts/deployment/preflight_env.sh`, que corre antes de buildear | Te dice qué falta en castellano, antes de gastar 10 minutos de build. |
| `cloudbuild.yaml` ahora manda `ALLOWED_ORIGINS` | Sin eso el deploy automático buildeaba bien y después no arrancaba. |
| `gunicorn_conf.py`: se apagó el auto-reload en producción y se fijó 1 worker | El auto-reload en producción reinicia procesos en medio de una request. Y con más de un worker el límite de peticiones (rate limit) se multiplica, porque cada proceso lleva su propia cuenta. |
| `railway.json`: healthcheck `/health` codificado | Antes había que acordarse de configurarlo a mano en el panel. |
| Clave de Gemini y DSN de Sentry tachados de los docs | Estaban en texto plano. |
| `PRE_DEPLOYMENT_CHECKLIST.md` actualizado | Listaba mal las variables obligatorias (faltaban las tres que frenan el arranque), el nombre del script y la cantidad de workers. |

---

## 4. Deuda que queda abierta (no frena el deploy)

### Las pruebas completas no terminan

`pytest` sobre todo el repo **se cuelga**, no falla: se queda esperando para
siempre. Al sacar un test que cuelga aparece el siguiente, así que **hoy no se
puede sacar un número de "cuántas pruebas pasan"**. Los que se identificaron:

- `tests/test_billing_autoservicio.py::test_change_password_wrong_current_returns_401`
- `tests/test_prelaunch_block2.py::test_trial_vencido_bloquea_operaciones_con_402`
- `tests/test_prelaunch_block3.py::test_past_due_rechaza_operacion_con_402`
- y al menos uno más en `test_billing_autoservicio.py`, después de esos tres.

Todos son de la misma familia (facturación / trial vencido / rechazo con 402),
así que lo más probable es que sea **un solo problema de base**, no cuatro.

`HANDOFF.md` §11 lo describe como "flaky". Es más que eso: es un cuelgue
reproducible, y el `--timeout` configurado no lo mata porque usa el método
`thread` (no puede interrumpir un hilo bloqueado).

Además, sacando esos tests, **quedan pruebas en rojo** en
`test_prelaunch_block1.py`, `test_prelaunch_block3.py`, `test_pilar_b_quotes.py`
y `test_pdf_avg_functional.py`.

Por qué esto no lo vio nadie: CI no corre la suite completa, corre 4 archivos
elegidos a mano (`ci.yml`) más el E2E. Esos 4 pasan. El resto no lo mira nadie.

Qué conviene hacer (no urgente, pero sí antes de tocar billing o trials):
arreglar el cuelgue, poner `--timeout-method=signal`, y recién ahí ampliar CI
para que corra la suite entera.

### Otros puntos menores

- **Catálogo de proveedor en disco**: vive en un archivo dentro del
  contenedor, así que se reinicia en cada deploy. Ya está avisado en
  `RAILWAY_SETUP.md` §6. La memoria por cliente (que es la importante) sí
  persiste en la base.
- **Rate limiting en memoria**: para escalar a más de un worker hay que
  agregar Redis (`REDIS_URL`) primero.
- **MercadoPago**: si el token empieza con `TEST-`, los pagos son simulados.
  El preflight te avisa.

---

## 5. Orden sugerido para salir

> Versión detallada, con equipos enfrentados y puertas de control:
> `docs/deployment/PLAN_DEPLOY_ADVERSARIAL.md`.


1. Rotar la clave de Gemini.
2. Elegir destino (recomendado: Railway) y archivar los otros.
3. Cargar las variables y correr `./scripts/deployment/preflight_env.sh`.
4. Deployar.
5. Verificar: `curl https://TU-URL/health` → tiene que decir `"status":"ok"`.
6. Abrir la app, registrarte con un usuario nuevo y hacer un flujo completo
   hasta descargar el MARIA.TXT.
7. Recién después, agendar el arreglo de las pruebas colgadas.
