"""
Utility to check and verify CSRF and ngrok configuration
"""
from django.conf import settings
from django.http import JsonResponse

def check_csrf_config(request):
    """Debug view to check CSRF configuration"""
    host = request.get_host()
    origin = request.META.get('HTTP_ORIGIN', 'Not provided')
    referer = request.META.get('HTTP_REFERER', 'Not provided')
    
    config = {
        'host': host,
        'origin': origin,
        'referer': referer,
        'csrf_cookie_secure': settings.CSRF_COOKIE_SECURE,
        'csrf_cookie_samesite': settings.CSRF_COOKIE_SAMESITE,
        'csrf_trusted_origins': settings.CSRF_TRUSTED_ORIGINS,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'debug': settings.DEBUG,
    }
    
    return JsonResponse(config, indent=2)
