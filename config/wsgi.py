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
    
    # Initialize Google OAuth provider
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
            print("Google OAuth provider initialized")
        except Exception as oauth_err:
            print(f"OAuth initialization warning: {oauth_err}")
except Exception as e:
    print(f"Startup warning: {e}")
