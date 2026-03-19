# Gunicorn config for E-Learning Backend
# Used by deploy_production.sh

bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
timeout = 120
keepalive = 2

# Use production settings on server
raw_env = [
    "DJANGO_SETTINGS_MODULE=config.settings.prod",
]

accesslog = "config/logs/gunicorn_access.log"
errorlog = "config/logs/gunicorn.log"
loglevel = "info"
capture_output = True
proc_name = "elearning_backend"
max_requests = 1000
max_requests_jitter = 50
