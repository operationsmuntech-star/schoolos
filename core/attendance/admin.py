from django.contrib import admin
from .models import Attendance, AttendanceReport

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status']
    list_filter = ['status', 'date']
    search_fields = ['student__user__first_name']

@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    list_display = ['student', 'month', 'present_count', 'absent_count']
