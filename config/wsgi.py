"""
WSGI config for School Management System
"""
import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()

# Run migrations on startup (Railway release phase may not execute reliably)
try:
    call_command('migrate', verbosity=0, interactive=False)
    call_command('collectstatic', verbosity=0, interactive=False)
except Exception as e:
    print(f"Startup migration warning: {e}")
