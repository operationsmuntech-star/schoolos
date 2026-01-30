"""
API router configuration - Phase 1
"""
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view
from backend.attendance.api import (
    AttendanceViewSet,
    AttendanceSessionViewSet,
    AttendanceExceptionViewSet,
    AttendanceReportViewSet
)
from backend.api import auth as auth_views


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'ok',
        'message': 'MunTech School Infrastructure API v1',
        'version': '1.0.0'
    })


router = DefaultRouter()
router.register(r'attendance/records', AttendanceViewSet, basename='attendance-record')
router.register(r'attendance/sessions', AttendanceSessionViewSet, basename='attendance-session')
router.register(r'attendance/exceptions', AttendanceExceptionViewSet, basename='attendance-exception')
router.register(r'attendance/reports', AttendanceReportViewSet, basename='attendance-report')

urlpatterns = [
    path('health/', health_check, name='health-check'),
    # Authentication endpoints
    path('auth/school-login/', auth_views.school_login, name='school-login'),
    path('auth/schools/', auth_views.get_schools, name='get-schools'),
    path('auth/switch-school/', auth_views.switch_school, name='switch-school'),
] + router.urls
