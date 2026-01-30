"""
URL configuration for MunTech School Infrastructure
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from backend.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('backend.api.routers')),
    path('health/', lambda r: __import__('django.http', fromlist=['JsonResponse']).JsonResponse({'status': 'ok'})),
]

# Development: serve frontend assets manually
if settings.DEBUG:
    urlpatterns += [
        path('scripts/<path:path>', serve, {'document_root': settings.BASE_DIR / 'frontend' / 'scripts'}),
        path('styles/<path:path>', serve, {'document_root': settings.BASE_DIR / 'frontend' / 'styles'}),
        path('views/<path:path>', serve, {'document_root': settings.BASE_DIR / 'frontend' / 'views'}),
        path('components/<path:path>', serve, {'document_root': settings.BASE_DIR / 'frontend' / 'components'}),
        path('manifest.json', serve, {'document_root': settings.BASE_DIR / 'frontend', 'path': 'manifest.json'}),
        path('offline.html', serve, {'document_root': settings.BASE_DIR / 'frontend', 'path': 'offline.html'}),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Production: WhiteNoise serves all static files from root
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# SPA routes - LAST (catch-all for everything else)
urlpatterns += [
    path('', core_views.spa_index, name='spa-index'),
    re_path(r'^(?!admin/|api/|health/|media/).*$', core_views.spa_index),
]

