"""
Parent Portal URLs

Routes for parents to access student data via REST API
/api/parent/students/{id}/fees/ - Invoices and fee information
/api/parent/students/{id}/payments/ - Payment history
/api/parent/students/{id}/attendance/ - Attendance records
/api/parent/students/{id}/exams/ - Exam results
/api/parent/notifications/ - Notification inbox
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .parent_portal_api import (
    StudentFeesViewSet, StudentPaymentHistoryViewSet,
    StudentAttendanceViewSet, StudentExamResultsViewSet,
    StudentNotificationsViewSet
)

# Router for nested viewsets
router = DefaultRouter()

urlpatterns = [
    # Fees - nested under student
    path('students/<int:student_id>/fees/', 
         StudentFeesViewSet.as_view({
             'get': 'list',
             'head': 'list',
             'options': 'list'
         }), name='student-fees-list'),
    path('students/<int:student_id>/fees/summary/', 
         StudentFeesViewSet.as_view({
             'get': 'summary',
         }), name='student-fees-summary'),
    path('students/<int:student_id>/fees/<int:pk>/', 
         StudentFeesViewSet.as_view({
             'get': 'retrieve',
             'head': 'retrieve',
             'options': 'retrieve'
         }), name='student-fees-detail'),
    
    # Payments - nested under student
    path('students/<int:student_id>/payments/', 
         StudentPaymentHistoryViewSet.as_view({
             'get': 'list',
             'head': 'list',
             'options': 'list'
         }), name='student-payments-list'),
    path('students/<int:student_id>/payments/stats/', 
         StudentPaymentHistoryViewSet.as_view({
             'get': 'stats',
         }), name='student-payments-stats'),
    path('students/<int:student_id>/payments/<int:pk>/', 
         StudentPaymentHistoryViewSet.as_view({
             'get': 'retrieve',
             'head': 'retrieve',
             'options': 'retrieve'
         }), name='student-payments-detail'),
    
    # Attendance - nested under student
    path('students/<int:student_id>/attendance/', 
         StudentAttendanceViewSet.as_view({
             'get': 'list',
             'head': 'list',
             'options': 'list'
         }), name='student-attendance-list'),
    path('students/<int:student_id>/attendance/summary/', 
         StudentAttendanceViewSet.as_view({
             'get': 'summary',
         }), name='student-attendance-summary'),
    path('students/<int:student_id>/attendance/<int:pk>/', 
         StudentAttendanceViewSet.as_view({
             'get': 'retrieve',
             'head': 'retrieve',
             'options': 'retrieve'
         }), name='student-attendance-detail'),
    
    # Exams - nested under student
    path('students/<int:student_id>/exams/', 
         StudentExamResultsViewSet.as_view({
             'get': 'list',
             'head': 'list',
             'options': 'list'
         }), name='student-exams-list'),
    path('students/<int:student_id>/exams/summary/', 
         StudentExamResultsViewSet.as_view({
             'get': 'summary',
         }), name='student-exams-summary'),
    path('students/<int:student_id>/exams/<int:pk>/', 
         StudentExamResultsViewSet.as_view({
             'get': 'retrieve',
             'head': 'retrieve',
             'options': 'retrieve'
         }), name='student-exams-detail'),
    
    # Notifications
    path('notifications/', 
         StudentNotificationsViewSet.as_view({
             'get': 'list',
             'head': 'list',
             'options': 'list'
         }), name='notifications-list'),
    path('notifications/unread-count/', 
         StudentNotificationsViewSet.as_view({
             'get': 'unread_count',
         }), name='notifications-unread-count'),
    path('notifications/<int:pk>/', 
         StudentNotificationsViewSet.as_view({
             'get': 'retrieve',
             'head': 'retrieve',
             'options': 'retrieve'
         }), name='notifications-detail'),
]
