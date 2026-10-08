import os

# Railway dynamically assigns the PORT environment variable (default: 8000)
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

workers = 2
threads = 4
worker_class = "gthread"
timeout = 60
accesslog = "-"
errorlog = "-"
loglevel = "info"
