# Gunicorn configuration file
import multiprocessing

max_requests = 1000
max_requests_jitter = 50
timeout = 600

log_file = "-"

bind = "0.0.0.0:8086"

worker_class = "uvicorn.workers.UvicornWorker"
workers = 2