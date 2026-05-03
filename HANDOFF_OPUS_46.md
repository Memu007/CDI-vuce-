# Handoff para Opus 4.6 — CDI / MARIA (VUCE)

> Este archivo es el punto de entrada. Leelo entero **antes** de tocar nada.
> Fecha del handoff: 2026-04-22. Sesion previa: Opus 4.7.

---

## 1. TL;DR en 30 segundos

- Backend FastAPI + SQLAlchemy async que arma una factura AVG con NCM, origen,
  FOB, flete, seguro y la exporta a TXT (para importar en MARIA / VUCE).
- Frontend HTML + JS vanilla, dos pantallas principales:
  - `landing.html` → auth (login / registro con pago simulado).
  - `dashboard_v2.html` → app logueada (clientes, nueva operacion, NCM, etc.).
- Despliegue: **Railway** (`Memu007/CDI` on `main`) + **Postgres managed**.
- Estado: **beta cerrada lista para un despachante amigo**. No apto para
  publico general.
- Lo critico: hay un “modo pago simulado” (no cobra de verdad), email
  verification desactivado por env, todo corre detras de login.

## 2. Identidad del proyecto

- Producto: **CDI (Custom Data Interchange)** para despachantes.
- Marca: **Ynera** (logo + footer).
- Dominio de produccion: subdominio de Railway (`*.up.railway.app`). El
  dominio propio esta pendiente de conectar (owner lo tiene comprado).
- Tono de copy: espanol rioplatense, cercano, sin jerga tecnica (ver
  regla `.cursor/rules/explicar-sin-asumir-tecnico.mdc`).

## 3. Estructura del codigo (lo importante)

```
proyecto_maria/
  main.py                     # TODO. 3.500+ lineas. Endpoints y lifecycle.
  database/
    models.py                 # SQLAlchemy: User, Client, Operation, ...
    connection.py             # init_db + create_all + detect sqlite/postgres
  core/
    catalog_service.py        # Catalogo vendor-aware (async, Postgres)
    dolar_service.py          # Scraper de USD oficial/blue con cache
    vuce_tarifar.py           # Scrape NCM -> alicuotas, licencias, regimen
  services/
    billing_sim.py            # Pago simulado (Luhn + brand + 3 ultimos)
    client_memory.py          # Memoria NCM por cliente (ClientProductHistory)
  security/
    passwords.py              # bcrypt
    jwt_utils.py              # cookies HttpOnly, samesite=strict
  static/v2/
    app_v2.js / app_v2.css    # shell del dashboard
    topbar_financials.js      # dolar + AFIP en la topbar
    screens/
      upload.js               # PDF upload
      ncm.js                  # edicion linea por linea (core de la UX)
      clientes.js             # CRUD clientes + empty state
      review.js               # resumen final + export TXT
      semaforo.js             # semaforo de intervenciones
  templates/
    landing.html              # auth + pago simulado + copy de Ynera
    dashboard_v2.html         # app logueada
  data/
    ncm_cache.json            # fallback local. La tabla NCMCache en DB lo cachea real.
```

## 4. Deploy / infra

### Railway
- Repo conectado: `Memu007/CDI` rama `main`.
- Auto-deploy on push.
- Servicios:
  - **web** (FastAPI): uvicorn, buildpack Python auto.
  - **postgres**: managed, conectado via `DATABASE_URL`.
- Env vars criticas (ver `RAILWAY_SETUP.md`):
  - `JWT_SECRET_KEY` — 64+ chars random. NO `SECRET_KEY`, el chequeo es por JWT_.
  - `GEMINI_API_KEY` — opcional, sin ella el parser cae en regex.
  - `DATABASE_URL` — la provee Railway al linkear Postgres.
  - `FRONTEND_URL` / `ALLOWED_ORIGINS` — URL publica de la app.
  - `PYTHON_ENV=production` — dispara chequeo de JWT seguro.
  - `EMAIL_VERIFICATION_REQUIRED=false` — beta pasa por encima.
  - `ENABLE_PAYMENT_SIMULATION=true` — pago simulado en alta.

### Migraciones de DB
- No hay Alembic. Usamos `Base.metadata.create_all(checkfirst=True)` + un
  par de ALTERs manuales en `main.py` (`_migrate_add_user_cuit_column`,
  `_migrate_add_user_billing_columns`, etc.). Si agregas **columna**, tenes
  que agregar un ALTER helper similar. Si agregas **tabla**, con create_all
  alcanza.
- Tablas que se crean automaticamente via `create_all`:
  `users, password_reset_tokens, clients, operations, operation_items,
   ncm_notes, system_backups, api_logs, client_product_history,
   vendor_catalog_products, ncm_cache`.

## 5. Lo que se cambio en esta sesion (opus 4.7 → 4.6)

Las 3 cosas importantes:

1. **Catalogo en DB (antes JSON)**
   - Nueva tabla `vendor_catalog_products` con unique `(owner, vendor_id, product_key)`.
   - `core/catalog_service.py` reescrito a async contra DB. El JSON
     `data/product_catalog.json` **ya no se usa** (queda de referencia
     historica, no lo leas).
   - Endpoints `/api/catalog/*` aceptan `db: AsyncSession` y son `async`.
   - Data que estaba en el JSON local **NO** se migro. Para la beta empieza
     vacio; el catalogo se va llenando al guardar operaciones.
2. **Errores amigables**
   - Global handler para `StarletteHTTPException` 5xx y `Exception` que
     devuelve `{"detail": "No pudimos procesar...", "code": "internal_error"}`
     y logea el stacktrace en server.
3. **Beta polish**
   - Banner global amarillo en landing + dashboard (`#betaBanner`) dismiss
     por session.
   - Empty states con CTA en clientes y operaciones del cliente.
   - Boton "usar tarjeta de prueba" (4242 4242 4242 4242) en registro.
   - Copy de pago: "modo demo · beta" explicito.

## 6. Lo que funciona (verificado)

- Alta + login con pago simulado (`4242 4242 4242 4242` pasa Luhn).
- Upload de PDF -> extraccion con Gemini si `GEMINI_API_KEY` esta seteada,
  regex fallback si no.
- Sugerencias NCM combinadas (memoria cliente + catalogo proveedor) via
  `POST /api/catalog/lookup`.
- Autoguardado post-operacion: `save_client_operation` alimenta
  `client_product_history` + `vendor_catalog_products`.
- Export TXT compatible con MARIA.
- Semaforo de intervenciones (VUCE + licencias).
- Dolar + AFIP en topbar.

## 7. Lo que NO funciona / trampas conocidas

- **Pago real**: esta 100% simulado. MercadoPago esta parcialmente
  integrado (`routers/mercadopago.py`) pero **no conectado al flow** de
  alta. Stripe no esta.
- **Email**: hay codigo para enviar confirmacion por SMTP, pero en beta
  corre en **mock mode** (link mostrado en consola). No llegan mails reales.
- **Rate limiting**: solo en `/api/auth/login` y uploads. El resto esta
  abierto.
- **Tests**: hay `tests/` pero la mayoria estan desactualizados respecto al
  modelo actual. No correr en CI todavia.
- **Legacy files**: `landing_legacy.html`, `viejo/`, `routers/_deprecated/`,
  `templates/landing_legacy.html` siguen en disco. Se pueden borrar con
  confianza, pero esta sesion no lo hizo para no arriesgar.
- **Divergencia de folders**: hubo un folder `/Users/Emi/Desktop/CDI (vuce)`
  trabajado fuera de git y luego sincronizado con rsync al repo
  `/Users/Emi/CDI`. Ahora ya estan alineados; si volves a tocar,
  **hacelo en `/Users/Emi/CDI`** para no repetir el lio. Ver
  `SYNC_TO_RAILWAY.md`.

## 8. Rutas / endpoints criticos

| Metodo | Path                                    | Auth | Proposito                                |
|-------:|-----------------------------------------|:----:|------------------------------------------|
| GET    | `/health`                               |  no  | Health check para Railway                |
| POST   | `/api/auth/register`                    |  no  | Alta con pago simulado                   |
| POST   | `/api/auth/login`                       |  no  | Login (rate-limited)                     |
| POST   | `/api/auth/logout`                      | yes  | Borra cookie                             |
| GET    | `/api/clients`                          | yes  | Lista clientes del despachante           |
| POST   | `/api/clients`                          | yes  | Crea cliente                             |
| POST   | `/api/upload/pdf`                       | yes  | Extrae items del PDF                     |
| POST   | `/api/catalog/lookup`                   | yes  | Sugerencias combinadas (memoria + catalogo) |
| POST   | `/api/catalog/match`                    | yes  | Match solo contra catalogo del vendor    |
| GET    | `/api/catalog/proveedores`              | yes  | Lista vendors con totales                |
| POST   | `/api/catalog/{vendor_id}/productos`    | yes  | Guarda/actualiza productos del vendor    |
| GET    | `/api/operations`                       | yes  | Operaciones del cliente                  |
| POST   | `/api/clients/{id}/operations`          | yes  | Guarda operacion + alimenta memoria/catalogo |
| GET    | `/api/system/connectors`                | yes  | Estado de VUCE/Tarifar/etc               |

## 9. Como desarrollar local

```bash
cd /Users/Emi/CDI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# con SQLite local (default si no seteas DATABASE_URL):
uvicorn proyecto_maria.main:app --reload --port 8000
```

Opcional para probar con Postgres igual a prod:

```bash
brew services start postgresql@14
createdb maria_local
export DATABASE_URL=postgresql+asyncpg://$USER@localhost:5432/maria_local
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
uvicorn proyecto_maria.main:app --reload --port 8000
```

Abrir `http://localhost:8000/`.

## 10. Como desplegar a Railway (post-push)

1. `git push origin main` — Railway buildea solo, tarda 3-5 min.
2. Mirar logs en Railway dashboard hasta ver "Application startup complete".
3. Smoke:
   ```bash
   curl -i https://TU-SUBDOMINIO.up.railway.app/health
   ```
4. Abrir en incognito, crear usuario de prueba con `4242 4242 4242 4242`,
   subir un PDF, crear un cliente, ver que la operacion quede.

Si algo explota:
- Env var faltante: Settings → Variables.
- `create_all` fallando: revisar que `DATABASE_URL` use `postgresql+asyncpg://`
  y que el servicio Postgres este linkeado.

## 11. Roadmap prioritizado para vos, Opus 4.6

En orden:

1. **Smoke post-deploy** que quedo pendiente (revisar logs Railway y
   `/health` apenas pushee, probar flow completo con cuenta nueva).
2. **Conectar dominio propio** (Settings → Networking → Custom Domain).
3. **Mercadopago real al alta** — la logica ya existe en `routers/`, hay
   que switch del simulado al real, detras de una env var.
4. **Email real**: probar con SMTP del proveedor del usuario (no Gmail,
   usar Resend o similar). Hoy el mock imprime el link en consola.
5. **Alembic** — para poder agregar columnas sin helpers manuales.
6. **Tests de regresion** sobre el flow de alta + catalogo (los 2 mas
   criticos para beta).
7. **Migrar datos del JSON historico** (`data/product_catalog.json`) a
   la nueva tabla `vendor_catalog_products` si el usuario los quiere.
   Script one-shot, no es critico.
8. **Limpieza grande**: despues de la primera semana de beta, borrar
   `viejo/`, `routers/_deprecated/`, `landing_legacy.html`, `templates/landing_legacy.html`.

## 12. Convenciones de codigo

- **Logging**: `logging.exception(...)` para 500s (incluye stacktrace).
  Nunca `print(e)` en prod path.
- **Errores al usuario**: jamas devolver `str(e)` en HTTP 500; usar el
  handler global. Para 4xx si es OK un mensaje especifico.
- **DB sessions**: siempre via `db: AsyncSession = Depends(get_db)`. Nunca
  abrir sessions manuales en handlers.
- **Tenant**: casi toda tabla tiene `owner_username`. Filtrar SIEMPRE por
  `user["username"]` en handlers autenticados.
- **Async**: handlers nuevos son `async def`. Si necesitas DB, pedila.
- **Copy**: evitar tecnicismos. El usuario final es despachante, no dev.
- **Nuevas reglas de proyecto** en `.cursor/rules/`:
  - `explicar-sin-asumir-tecnico.mdc` — como comunicar decisiones.
  - (resto en `.cursor/rules/` del repo).

## 13. Links utiles

- `RAILWAY_SETUP.md` — pasos infra Railway.
- `MENSAJE_AMIGO.md` — template para invitar al despachante a probar.
- `SYNC_TO_RAILWAY.md` — historia de la divergencia de folders (ya resuelta).
- `docs/AUDIT_MULTITENANT.md` — auditoria multi-tenant previa (pre-hoy).
- `docs/SPRINT_*` — notas de sprints anteriores.

## 14. Preguntas que vas a querer hacerle al usuario

- ¿Ya conectaste Postgres y seteaste las env vars en Railway?
- ¿Cual es el subdominio real (`xxx.up.railway.app`)? Para `FRONTEND_URL`.
- ¿Queres que migremos el JSON historico o arrancamos con catalogo vacio?
- ¿Cual es el SMTP que te da tu proveedor, para email real?
- ¿Queres probar con cuenta demo vos antes de pasarselo al despachante?

## 15. Ultima cosa

El usuario esta en modo “quiero mostrarlo esta semana”. Priorizar
**lo que se ve** > deuda tecnica. La deuda queda documentada aca.
