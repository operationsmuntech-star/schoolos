"""
WSGI config for School Management System
"""
import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django application
application = get_wsgi_application()

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent.parent
STATICFILES_DIR = BASE_DIR / 'staticfiles'

# Ensure staticfiles directory exists
STATICFILES_DIR.mkdir(parents=True, exist_ok=True)
print(f"[MUNTECH] ✓ Staticfiles directory ready: {STATICFILES_DIR}")

# Run migrations and initialization on startup
try:
    # Run database migrations
    print("[MUNTECH] Running database migrations...")
    call_command('migrate', verbosity=0, interactive=False)
    print("[MUNTECH] ✓ Migrations completed successfully")
    
    # Collect static files
    print("[MUNTECH] Collecting static files...")
    try:
        call_command('collectstatic', verbosity=0, interactive=False, clear=True)
        print(f"[MUNTECH] ✓ Static files collected to {STATICFILES_DIR}")
    except Exception as collect_err:
        print(f"[MUNTECH] ⚠ Collectstatic notice: {collect_err}", file=sys.stderr)
    
    # Initialize Google OAuth provider
    from allauth.socialaccount.models import SocialApp
    from django.contrib.sites.models import Site
    
    print("[MUNTECH] Initializing OAuth providers...")
    try:
        if not SocialApp.objects.filter(provider='google').exists():
            site = Site.objects.get_current()
            google_app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
                secret=os.getenv('GOOGLE_CLIENT_SECRET', '')
            )
            google_app.sites.add(site)
            print("[MUNTECH] ✓ Google OAuth provider created")
        else:
            print("[MUNTECH] ✓ OAuth providers already configured")
    except Exception as oauth_err:
        print(f"[MUNTECH] OAuth setup: {oauth_err}", file=sys.stderr)
        
    print("[MUNTECH] ✓ Application startup completed successfully")
    
except Exception as e:
    print(f"[MUNTECH] ⚠ Startup warning: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)


