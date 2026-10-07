import os

# Render dynamically assigns the PORT environment variable (default: 10000)
port = os.environ.get("PORT", "10000")
bind = f"0.0.0.0:{port}"

workers = 2
threads = 2
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
