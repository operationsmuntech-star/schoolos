"""
Django settings for MunTech School Infrastructure
Production-ready with Railway support
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Allow everyone (Local LAN + Railway) - can be restricted later
# Tighten ALLOWED_HOSTS: read from env or fallback to sensible defaults
env_allowed = os.environ.get('ALLOWED_HOSTS')
if env_allowed:
    # Allow comma-separated list from environment
    ALLOWED_HOSTS = [h.strip() for h in env_allowed.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
    # Prefer explicit Railway domain if provided in env
    railway_domain = os.environ.get('RAILWAY_DOMAIN')
    if railway_domain:
        ALLOWED_HOSTS.append(railway_domain)
    else:
        # Allow Railway subdomains when not explicitly set (less permissive than '*')
        ALLOWED_HOSTS.append('.railway.app')

# Database configuration - supports both SQLite and PostgreSQL
if os.environ.get('DATABASE_URL'):
    # Railway PostgreSQL connection
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Local SQLite fallback
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'backend.core',
    'backend.people',
    'backend.attendance',
    'backend.users',
    'backend.sync',
    'backend.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add WhiteNoise only in production (Gunicorn/Railway)
if not DEBUG and os.environ.get('DATABASE_URL'):
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'backend.config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files configuration
STATIC_URL = '/'  # Serve static files from root
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Include all frontend subdirectories in static files lookup
STATICFILES_DIRS = [
    BASE_DIR / 'frontend',  # Includes scripts/, styles/, views/, components/, etc.
]

# Production static files handling with WhiteNoise
if not DEBUG and os.environ.get('DATABASE_URL'):
    # Use compression but KEEP original filenames (Required for PWA/Service Worker)
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    # WhiteNoise Root: serve ALL collected files from root URL (not /static/)
    WHITENOISE_ROOT = BASE_DIR / 'staticfiles'
    # WhiteNoise will serve index.html fallback for SPA
    WHITENOISE_AUTOREFRESH = False
    # Explicit MIME types for frontend assets
    WHITENOISE_MIMETYPES = {
        '.json': 'application/json',
        '.js': 'application/javascript',
        '.css': 'text/css',
        '.html': 'text/html',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
    }

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS Configuration for PWA and multi-tenant
cors_env = os.environ.get('CORS_ALLOWED_ORIGINS')
if cors_env:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_env.split(',') if o.strip()]
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    # Add Railway domain if provided explicitly
    if os.environ.get('RAILWAY_DOMAIN'):
        CORS_ALLOWED_ORIGINS.append(f"https://{os.environ.get('RAILWAY_DOMAIN')}")

CORS_ALLOW_CREDENTIALS = True

# Security settings for production
if not DEBUG and os.environ.get('DATABASE_URL'):
    # Trust Railway's Load Balancer
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # DISABLE Internal SSL Redirect (Railway handles this at the edge/domain level)
    # This ensures the HTTP health check passes.
    SECURE_SSL_REDIRECT = False
    
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'"),
        'style-src': ("'self'", "'unsafe-inline'"),
    }

# Allow all hosts in production (Railway handles routing, this prevents 400 errors on health checks)
if not DEBUG:
    ALLOWED_HOSTS = ['*']

# WhiteNoise Root Configuration
# Allows serving files (like service-worker.js, manifest.json, styles/) from the root URL
if not DEBUG and os.environ.get('DATABASE_URL'):
    WHITENOISE_ROOT = BASE_DIR / 'staticfiles'
