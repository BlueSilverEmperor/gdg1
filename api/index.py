"""
Serverless entry point for Vercel.
Exposes the Django WSGI application as `app`.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_marketplace.settings')

app = get_wsgi_application()
