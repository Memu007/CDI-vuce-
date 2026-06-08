# Railway — Setup para beta cerrada (24h MVP)

Guia paso a paso para dejar el proyecto corriendo en Railway con Postgres
managed y sin verificacion de email. Pensado para mandarselo a un despachante
amigo y que pruebe end-to-end.

---

## 1) Adjuntar Postgres al servicio

En el panel de Railway, dentro de tu proyecto:

1. Click en **"+ New"** -> **"Database"** -> **"Add PostgreSQL"**
2. Una vez creado el servicio Postgres, ir al servicio del **backend** (el que
   corre tu Dockerfile).
3. Solapa **"Variables"** -> **"+ New Variable"** -> **"Add Reference"**
4. Elegir el servicio Postgres y la variable `DATABASE_URL`.

Esto inyecta `DATABASE_URL=postgres://...` automaticamente en cada deploy.
El codigo en `proyecto_maria/database/connection.py` ya convierte
`postgres://` -> `postgresql+asyncpg://` solo, no hay que tocar nada.

---

## 2) Variables de entorno (copy/paste en panel Railway)

Pegar en el servicio del **backend**, NO en el de Postgres. Variables marcadas
con * son criticas para esta beta.

```
ENVIRONMENT=production
EMAIL_VERIFICATION_REQUIRED=false
JWT_SECRET_KEY=<GENERAR_CON_secrets.token_urlsafe(64)>
GEMINI_API_KEY=<TU_API_KEY_DE_GEMINI>
GEMINI_MODEL=gemini-3.1-flash-lite-preview
```

> **Tip**: el JWT_SECRET_KEY de arriba lo generamos fresco para esta beta. Si
> queres rotarlo, en tu mac corres: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
> y reemplazas el valor. Importante: si lo cambias despues, las sesiones
> activas se invalidan (los users tienen que loguearse de nuevo).

### URL publica (FRONTEND_URL y CORS)

Estas dependen del dominio que te asigne Railway. Despues del primer deploy,
fijate en la solapa **"Settings"** -> **"Networking"** -> **"Generate Domain"**.
Te va a dar algo tipo `cdi-backend-production-xxxx.up.railway.app`.

Una vez tengas la URL, agregar:

```
FRONTEND_URL=https://TU-SUBDOMINIO.up.railway.app
ALLOWED_ORIGINS=https://TU-SUBDOMINIO.up.railway.app
```

(Reemplazar `TU-SUBDOMINIO` por lo que te asigno Railway.)

### Variables que NO hace falta setear

- `PORT`: Railway lo inyecta solo, el Dockerfile ya lo respeta.
- `DATABASE_URL`: viene del Postgres adjunto (ver paso 1).
- `SMTP_*`: no hace falta porque el email esta deshabilitado para la beta.

---

## 3) Build settings

En el servicio del backend, solapa **"Settings"**:

- **Builder**: Dockerfile (auto-detectado por presencia de `Dockerfile`)
- **Root Directory**: `/` (raiz del repo)
- **Start Command**: dejar vacio (el `CMD` del Dockerfile ya levanta gunicorn)
- **Health Check Path**: `/health`
- **Health Check Timeout**: 60s

---

## 4) Verificar que arranco bien

Despues del primer deploy:

1. **Logs**: en la solapa "Deployments" -> click en el ultimo -> "View Logs".
   Buscar:
   - `"Application startup complete."` -> backend arrancado
   - `"Migracion: agregada columna users.X"` -> ok, primera vez
   - Cualquier `Traceback` o `ERROR` -> hay que arreglar
2. **Healthcheck**: `curl https://TU-SUBDOMINIO.up.railway.app/health` -> 200
3. **Landing**: abrir la URL en el navegador, deberia cargar la pagina de
   bienvenida.

---

## 5) Cuando algo se rompe

| Sintoma | Donde mirar |
|---|---|
| Build falla | Logs del build en Railway, suele ser `requirements.txt` o falta de modulo |
| Container arranca y muere | Logs del runtime, suele ser `DATABASE_URL` mal o migracion rota |
| 500 al registrar usuario | Logs runtime + revisar `EMAIL_VERIFICATION_REQUIRED` esta en `false` |
| 502 / no responde | El healthcheck path es `/health`, asegurate que este configurado |

---

## 6) Que NO funciona en esta beta (avisar al amigo)

- **Mails de confirmacion**: no llegan (email verification esta off, entra directo).
- **Pagos reales**: el formulario de tarjeta es simulado, no se cobra nada.
- **Catalogo de proveedor**: vive en un archivo en disco, se reinicia cada deploy.
  La memoria por cliente (en DB) si persiste.
- **Reportes avanzados / billing real**: aun no estan.
