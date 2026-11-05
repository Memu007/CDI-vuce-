# CDI

App web para despachantes de aduana argentinos. Lee la factura del proveedor
(Excel o PDF), ayuda a clasificar cada ítem (NCM) y genera el archivo que se
pega en el sistema MARIA de ARCA. El despachante revisa y confirma en pantalla;
el archivo es trazable a lo que aprobó.

**Si sos un asistente de IA, empezá por `AGENTS.md`.** Si vas a tocar código,
leé también `CLAUDE.md`. El estado vigente del proyecto (qué está hecho, qué
sigue, qué espera decisión) está en `docs/pm/NOW.md`.

## Stack

| Capa | Qué se usa |
|------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy async |
| Base de datos | SQLite local; PostgreSQL en producción (`DATABASE_URL`) |
| Frontend | HTML + JavaScript sin framework (`proyecto_maria/static/v2/`) |
| Lectura de PDF | Gemini, con fallback a texto y OCR |
| Pagos | Mercado Pago |
| Producción | Railway construye el `Dockerfile` y publica cada push a `main` |

## Correr en local

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # mínimo: JWT_SECRET_KEY (32+ caracteres), ENVIRONMENT=development
PYTHONPATH=. uvicorn proyecto_maria.main:app --host 127.0.0.1 --port 8000 --reload
```

Abrí <http://127.0.0.1:8000/>. Sin `GEMINI_API_KEY` todo funciona salvo la
lectura de PDF. Las tablas se crean solas al arrancar y los cambios de esquema
corren en ese mismo arranque, dentro de `main.py` (funciones `_migrate_*`,
cada una verifica si ya está aplicada); no hay herramienta de migraciones
aparte. `start_server.sh` arranca con Gunicorn, como en producción.

## Pruebas

```bash
ENVIRONMENT=testing EMAIL_VERIFICATION_REQUIRED=false \
  JWT_SECRET_KEY=clave-de-prueba-con-mas-de-32-caracteres \
  python -m pytest --no-cov          # suite completa
./scripts/testing/e2e_maria.sh       # recorrido real en navegador (necesita Node 22)
```

La CI (`.github/workflows/ci.yml`) corre las dos cosas, pero deselecciona
algunos tests con falla vieja: no es una red de seguridad completa y Railway
no la espera para publicar.

## Producción

`main` es de Emi. Railway publica cada push a `main` sin esperar los tests, así
que empujar a `main` es publicar: se hace sólo con su «dale» para un SHA
concreto. Todo trabajo va a una rama. La configuración está en
`docs/deployment/RAILWAY_SETUP.md`; las puertas de publicación, en
`docs/deployment/PLAN_DEPLOY_ADVERSARIAL.md`.

## Dónde está cada cosa

```
proyecto_maria/     la aplicación
  main.py           FastAPI, rutas y lógica (un solo módulo, grande)
  core/             generación del archivo MARIA, conectores (VUCE, Tarifar), dólar
  database/         modelos y conexión
  templates/        landing, dashboard v2 (default) y v1 (cookie ui=v1)
  static/v2/        frontend vigente
tests/              pytest; conftest con base y usuario de prueba
scripts/testing/    e2e, smokes, sabotajes y capturas de pantalla
scripts/datos/      generadores de datos de referencia
config/             Puppeteer para el e2e (package.json)
docs/pm/            el canal de trabajo: NOW, ROADMAP, DECISIONS, PARA-DEV, PARA-PM
docs/deployment/    Railway y puertas de publicación
docs/negocio/       planes de valuación y venta
docs/archive/       historia, sólo lectura
```

`HANDOFF.md` describe cómo funciona el producto, pero está desactualizado
desde julio: ante una contradicción mandan Git y `docs/pm/NOW.md`.
`CHANGELOG.md` tiene una a tres líneas por cambio, con fecha.
