"""
Django settings for campus_marketplace project.
Campus Marketplace - Student-to-Student Commerce Platform.
"""

from pathlib import Path
import os
import sys
import json
import logging
import dj_database_url
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env', override=True)


# Security settings
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-campus-marketplace-local-dev-key-2026-very-secure'
)

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

allowed_hosts_raw = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,testserver,.vercel.app,.onrender.com,.railway.app,.up.railway.app')
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_raw.split(',') if h.strip()]
for host in ['testserver', '.vercel.app', '.onrender.com', '.railway.app', '.up.railway.app', '127.0.0.1', 'localhost']:
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

# Automatically support Render's and Railway's dynamically assigned external hostnames
render_external_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_external_hostname and render_external_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_external_hostname)

railway_public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
if railway_public_domain and railway_public_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(railway_public_domain)

railway_static_url = os.environ.get('RAILWAY_STATIC_URL')
if railway_static_url and railway_static_url not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(railway_static_url)

if '*' in ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*']

# CSRF Trusted Origins for deployed domain(s)
csrf_origins_raw = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://*.vercel.app,https://*.onrender.com,https://*.railway.app,https://*.up.railway.app')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins_raw.split(',') if o.strip()]
for origin in ['https://*.vercel.app', 'https://*.onrender.com', 'https://*.railway.app', 'https://*.up.railway.app']:
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

if render_external_hostname:
    render_origin = f'https://{render_external_hostname}'
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

if railway_public_domain:
    railway_origin = f'https://{railway_public_domain}'
    if railway_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(railway_origin)

if railway_static_url:
    railway_static_origin = f'https://{railway_static_url}'
    if railway_static_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(railway_static_origin)

# Trust reverse proxy header from Railway / cloud providers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'storages',
    # Project apps
    'accounts.apps.AccountsConfig',
    'marketplace.apps.MarketplaceConfig',
]


# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'campus_marketplace.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'marketplace.context_processors.marketplace_counts',
            ],
        },
    },
]

WSGI_APPLICATION = 'campus_marketplace.wsgi.application'

# Database configuration:
# Defaults to in-memory SQLite for test suite runs, Supabase PostgreSQL in production, or local SQLite fallback
DATABASE_URL = os.environ.get('DATABASE_URL')
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
elif DATABASE_URL:
    # Supabase Transaction Pooler (port 6543) uses PgBouncer in transaction mode.
    # When using transaction pooling, disable server-side cursors and set conn_max_age=0.
    is_transaction_pooler = ':6543' in DATABASE_URL or os.environ.get('DISABLE_SERVER_SIDE_CURSORS', '').lower() in ('true', '1')
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=0 if is_transaction_pooler else int(os.environ.get('CONN_MAX_AGE', 600)),
            conn_health_checks=not is_transaction_pooler,
            ssl_require=True,
        )
    }
    if is_transaction_pooler:
        DATABASES['default'].setdefault('OPTIONS', {})
        DATABASES['default']['OPTIONS']['disable_server_side_cursors'] = True
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Production static files compression with WhiteNoise and security hardening
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    if os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1'):
        SECURE_SSL_REDIRECT = True


# Media files & Storage Configuration
# Primary: Supabase Object Storage via S3 Protocol (django-storages[s3] + boto3)
SUPABASE_S3_ACCESS_KEY = os.environ.get('SUPABASE_S3_ACCESS_KEY')
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')

if SUPABASE_S3_ACCESS_KEY:
    # Supabase S3 Storage Configuration
    AWS_ACCESS_KEY_ID = SUPABASE_S3_ACCESS_KEY
    AWS_SECRET_ACCESS_KEY = os.environ.get('SUPABASE_S3_SECRET_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('SUPABASE_S3_BUCKET_NAME', 'listing_images')
    AWS_S3_ENDPOINT_URL = os.environ.get('SUPABASE_S3_ENDPOINT_URL', 'https://xlcmrhqhvulypglyxtov.supabase.co/storage/v1/s3')
    AWS_S3_REGION_NAME = os.environ.get('SUPABASE_S3_REGION_NAME', 'ap-southeast-2')
    AWS_S3_ADDRESSING_STYLE = 'path'
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False

    # Supabase serves public object CDN URLs at:
    # https://<project-ref>.supabase.co/storage/v1/object/public/<bucket>/<key>
    custom_domain_env = os.environ.get('AWS_S3_CUSTOM_DOMAIN')
    if custom_domain_env:
        AWS_S3_CUSTOM_DOMAIN = custom_domain_env
    else:
        endpoint_clean = AWS_S3_ENDPOINT_URL.replace('https://', '').replace('http://', '').rstrip('/')
        base_host = endpoint_clean.split('/storage')[0] if '/storage' in endpoint_clean else endpoint_clean
        AWS_S3_CUSTOM_DOMAIN = f"{base_host}/storage/v1/object/public/{AWS_STORAGE_BUCKET_NAME}"

    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if not DEBUG else "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }


elif CLOUDINARY_CLOUD_NAME and os.environ.get('CLOUDINARY_API_KEY') and os.environ.get('CLOUDINARY_API_SECRET'):
    INSTALLED_APPS.insert(0, 'cloudinary_storage')
    INSTALLED_APPS.insert(1, 'cloudinary')
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    }
    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if not DEBUG else "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Authentication URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'marketplace:listing_list'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Email Configuration (Gmail SMTP with local fallback)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '').strip()
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '').strip()  # 16-character Google App Password
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', 10))

# Secure TLS (port 587) vs SSL (port 465) mutual exclusivity handling
if EMAIL_PORT == 465 or os.environ.get('EMAIL_USE_SSL', 'False').lower() in ('true', '1'):
    EMAIL_USE_SSL = True
    EMAIL_USE_TLS = False
else:
    EMAIL_USE_SSL = False
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1')

DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    f"Campus Marketplace <{EMAIL_HOST_USER}>" if EMAIL_HOST_USER else "Campus Marketplace <no-reply@campusmarketplace.local>"
)

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    logger.warning("EMAIL_HOST_USER/PASSWORD not set. Falling back to console.EmailBackend for local dev.")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

