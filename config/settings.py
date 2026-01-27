"""
Django settings for School Management System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Allow all hosts in development (DEBUG=True)
# In production, set DEBUG=False and specify allowed hosts
if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    # Base allowed hosts
    ALLOWED_HOSTS = [
        'localhost',
        '127.0.0.1',
        'muntechschoolsys.up.railway.app',  # Explicit Railway domain
        '*.railway.app',
        '*.up.railway.app',
        'yourdomain.com',
        'www.yourdomain.com',
    ]
    
    # Add RAILWAY_DOMAIN env var if set
    railway_domain = os.getenv('RAILWAY_DOMAIN', '').strip()
    if railway_domain and railway_domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(railway_domain)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third-party apps
    'grappelli',  # Modern admin interface
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'crispy_forms',
    'crispy_bootstrap5',
    
    # Local apps
    'core.users',
    'core.dashboard',
    'core.adminpanel',
    'core.admissions',
    'core.attendance',
    'core.examinations',
    'core.fees',
    'core.payments',
]

SITE_ID = 1

# CACHING CONFIGURATION (For faster page loads)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files serving
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'core.ngrok_middleware.NgrokMiddleware',  # Custom middleware for ngrok support
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database - Auto-detect PostgreSQL on Railway, SQLite locally
import dj_database_url

if os.getenv('DATABASE_URL'):
    # Production: Use Railway's PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Development: Use SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'CONN_MAX_AGE': 0,
            'AUTOCOMMIT': True,
        }
    }

# Only log actual errors, not every database query
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# In development (DEBUG=True), Django serves static files directly
# In production, run: python manage.py collectstatic
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Used for production with collectstatic
STATICFILES_DIRS = [BASE_DIR / 'static']  # Development: served by Django directly

# WhiteNoise compression for faster static file serving on Railway
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' if not DEBUG else 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth settings
AUTH_USER_MODEL = 'users.CustomUser'
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'account_login'

# Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Google OAuth Configuration
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'key': ''
        }
    }
}

# Allauth Settings
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_ADAPTER = 'core.adapters.CustomSocialAccountAdapter'

# Session & Cookie Optimization
SESSION_COOKIE_AGE = 86400 * 7  # 7 days
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_CACHE_ALIAS = 'default'  # Use cache for sessions
CSRF_COOKIE_HTTPONLY = True
LANGUAGE_COOKIE_SECURE = not DEBUG

# CSRF Configuration - Critical for ngrok and remote access
CSRF_COOKIE_SECURE = not DEBUG  # HTTPS only in production
CSRF_COOKIE_SAMESITE = 'Lax' if DEBUG else 'Strict'
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://localhost:3000',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:3000',
    'http://0.0.0.0:8000',
    'https://*.ngrok-free.dev',
    'https://*.ngrok.io',
    'https://*.ngrok.app',
    'https://*.railway.app',
]
# Add Railway domain if provided
railway_domain = os.getenv('RAILWAY_DOMAIN', '').strip()
if railway_domain:
    if not railway_domain.startswith('https://'):
        railway_domain = 'https://' + railway_domain
    CSRF_TRUSTED_ORIGINS.append(railway_domain)

# CORS Configuration - Allow ngrok and localhost
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://localhost:3000',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:3000',
    'http://0.0.0.0:8000',
]

# Security Headers - Relaxed for development
if DEBUG:
    X_FRAME_OPTIONS = 'ALLOW'
    SECURE_HSTS_SECONDS = 0
    SECURE_SSL_REDIRECT = False
else:
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_SSL_REDIRECT = True
