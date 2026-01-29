from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api

app_name = 'notifications'

# API Router
router = DefaultRouter()
router.register(r'preferences', views_api.NotificationPreferenceViewSet, basename='preference')
router.register(r'notifications', views_api.NotificationViewSet, basename='notification')
router.register(r'sms-logs', views_api.SMSLogViewSet, basename='sms-log')
router.register(r'email-logs', views_api.EmailLogViewSet, basename='email-log')
router.register(r'templates', views_api.NotificationTemplateViewSet, basename='template')

urlpatterns = [
    path('api/', include(router.urls)),
]
