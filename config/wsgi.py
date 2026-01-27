"""
WSGI config for School Management System
Production-ready with robust static file handling
"""
import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get paths
BASE_DIR = Path(__file__).resolve().parent.parent
STATICFILES_DIR = BASE_DIR / 'staticfiles'

print("\n" + "="*60)
print("[MUNTECH] WSGI Application Startup")
print("="*60)

# Step 1: Ensure static files directory exists with proper permissions
print("[MUNTECH] Step 1: Preparing static files directory...")
try:
    STATICFILES_DIR.mkdir(parents=True, exist_ok=True, mode=0o755)
    # Create a marker file to verify directory is writable
    marker_file = STATICFILES_DIR / '.muntech_writable'
    marker_file.touch()
    marker_file.unlink()  # Clean up marker
    print(f"[MUNTECH] ✓ Staticfiles directory ready: {STATICFILES_DIR}")
except Exception as dir_err:
    print(f"[MUNTECH] ⚠ WARNING: Could not create staticfiles directory: {dir_err}", file=sys.stderr)

# Step 2: Initialize Django application
print("[MUNTECH] Step 2: Initializing Django WSGI application...")
try:
    application = get_wsgi_application()
    print("[MUNTECH] ✓ Django WSGI application initialized")
except Exception as app_err:
    print(f"[MUNTECH] ✗ ERROR initializing WSGI: {app_err}", file=sys.stderr)
    raise

# Step 3: Run database migrations
print("[MUNTECH] Step 3: Running database migrations...")
try:
    call_command('migrate', verbosity=0, interactive=False, run_syncdb=False)
    print("[MUNTECH] ✓ Database migrations completed")
except Exception as migrate_err:
    print(f"[MUNTECH] ⚠ Migration warning: {migrate_err}", file=sys.stderr)

# Step 4: Collect static files with proper error handling
print("[MUNTECH] Step 4: Collecting static files...")
try:
    # First try with clear=False to preserve existing files
    call_command('collectstatic', verbosity=2, interactive=False, clear=False)
    
    # Verify static files were collected
    css_files = list(STATICFILES_DIR.rglob('*.css'))
    js_files = list(STATICFILES_DIR.rglob('*.js'))
    
    print(f"[MUNTECH] ✓ Static files collected:")
    print(f"[MUNTECH]   - CSS files: {len(css_files)}")
    print(f"[MUNTECH]   - JS files: {len(js_files)}")
    
    if len(css_files) > 0 or len(js_files) > 0:
        print(f"[MUNTECH] ✓ Static files collected to {STATICFILES_DIR}")
    else:
        print(f"[MUNTECH] ⚠ WARNING: No static files found after collection", file=sys.stderr)
        
except Exception as collect_err:
    print(f"[MUNTECH] ⚠ Collectstatic error: {collect_err}", file=sys.stderr)

# Step 5: Initialize OAuth provider
print("[MUNTECH] Step 5: Initializing OAuth providers...")
try:
    from allauth.socialaccount.models import SocialApp
    from django.contrib.sites.models import Site
    
    if not SocialApp.objects.filter(provider='google').exists():
        try:
            site = Site.objects.get_current()
            google_app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
                secret=os.getenv('GOOGLE_CLIENT_SECRET', '')
            )
            google_app.sites.add(site)
            print("[MUNTECH] ✓ Google OAuth provider created")
        except Exception as create_oauth_err:
            print(f"[MUNTECH] ⚠ Could not create OAuth: {create_oauth_err}", file=sys.stderr)
    else:
        print("[MUNTECH] ✓ OAuth providers already configured")
        
except Exception as oauth_err:
    print(f"[MUNTECH] ⚠ OAuth initialization: {oauth_err}", file=sys.stderr)

print("[MUNTECH] ✓ Application startup completed successfully!")
print("="*60 + "\n")



