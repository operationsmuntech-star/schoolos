from django.urls import path
from . import views
from . import teacher_views
from . import student_views
from . import admin_views

app_name = 'dashboard'
urlpatterns = [
    path('', views.index, name='index'),
    path('api/stats/', views.stats_api, name='stats_api'),
    
    # Teacher Portal URLs
    path('teacher/', teacher_views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/attendance/', teacher_views.attendance_marking, name='attendance_marking'),
    path('teacher/attendance/save/', teacher_views.save_attendance, name='save_attendance'),
    path('teacher/grades/', teacher_views.grade_entry, name='grade_entry'),
    path('teacher/grades/save/', teacher_views.save_grades, name='save_grades'),
    path('teacher/report/<int:student_id>/', teacher_views.report_card, name='report_card'),
    
    # Student Portal URLs
    path('student/', student_views.student_dashboard, name='student_dashboard'),
    path('api/student/overview/', student_views.student_api_overview, name='student_api_overview'),
    path('api/student/grades/', student_views.student_api_grades, name='student_api_grades'),
    path('api/student/attendance/', student_views.student_api_attendance, name='student_api_attendance'),
    path('api/student/fees/', student_views.student_api_fees, name='student_api_fees'),
    path('api/student/notifications/', student_views.student_api_notifications, name='student_api_notifications'),
    path('api/student/notifications/<int:notification_id>/read/', student_views.student_api_mark_notification_read, name='student_api_mark_notification_read'),
    # Admin Analytics
    path('admin/analytics/', admin_views.analytics_dashboard, name='admin_analytics'),
]
