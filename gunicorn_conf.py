"""Configuración de Gunicorn.

La usa `start_server.sh`. El `Dockerfile` pasa sus flags a mano, pero deja los
mismos valores que este archivo para que los dos caminos se comporten igual.
"""

import multiprocessing
import os

# Gunicorn config variables
loglevel = os.environ.get("LOG_LEVEL", "info").lower()
errorlog = "-"  # stderr
accesslog = "-"  # stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

IS_PRODUCTION = os.environ.get("ENVIRONMENT", "development") == "production"

# Workers.
#
# El rate limiting (`proyecto_maria/core/rate_limit.py`) usa MemoryStorage
# cuando no hay REDIS_URL. Memoria no se comparte entre procesos: con N
# workers cada uno lleva su propio contador y el límite real termina siendo
# N veces el configurado. Por eso, sin Redis, un solo worker.
#
# Con REDIS_URL el contador es compartido y sí conviene escalar.
if os.environ.get("WEB_CONCURRENCY"):
    workers = int(os.environ["WEB_CONCURRENCY"])
elif os.environ.get("REDIS_URL"):
    workers = multiprocessing.cpu_count() * 2 + 1
else:
    workers = 1

worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts
timeout = 120
keepalive = 5

# Recicla workers para acotar fugas de memoria (mismo criterio que el Dockerfile).
max_requests = 1000
max_requests_jitter = 50

# Auto-reload SOLO en desarrollo. En producción vigilar el filesystem gasta CPU
# y puede reiniciar workers en medio de una request.
reload = not IS_PRODUCTION
