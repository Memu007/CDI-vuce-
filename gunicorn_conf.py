import multiprocessing
import os

# Gunicorn config variables
loglevel = "info"
errorlog = "-"  # stderr
accesslog = "-"  # stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# Workers configuration
# Recommended: (2 x num_cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1 if 'RAILWAY_ENVIRONMENT_NAME' not in os.environ else 4
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts
timeout = 120
keepalive = 5

# Reload for development (optional, disable in prod)
reload = True
