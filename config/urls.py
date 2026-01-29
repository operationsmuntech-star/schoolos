from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.csrf_utils import check_csrf_config

# Customize admin site branding
admin.site.site_header = "MunTech Administration"
admin.site.site_title = "MunTech Admin Portal"
admin.site.index_title = "Welcome to MunTech Admin"

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),  # Grappelli admin interface
    path('admin/', admin.site.urls),
    path('', include('core.dashboard.urls')),
    
    # Allauth handles /accounts/login/, /accounts/logout/
    path('accounts/', include('allauth.urls')),
    
    # Our custom users app handles /accounts/register-school/
    path('accounts/', include('core.users.urls')),
    
    path('admissions/', include('core.admissions.urls')),
    path('attendance/', include('core.attendance.urls')),
    path('exams/', include('core.examinations.urls')),
    path('fees/', include('core.fees.urls')),
    path('payments/', include('core.payments.urls')),
    path('notifications/', include('core.notifications.urls')),
    path('admin-panel/', include('core.adminpanel.urls')),
    
    # Parent Portal API
    path('api/parent/', include('core.payments.parent_urls')),
    
    # Debug endpoint for CSRF configuration (only in DEBUG mode)
    path('debug/csrf-config/', check_csrf_config, name='csrf_config'),
]

if settings.DEBUG:
    # Serve media files (uploads)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files from STATICFILES_DIRS (development)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])