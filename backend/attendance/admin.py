"""
Django admin configuration for attendance app - Phase 1
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from backend.attendance.models import AttendanceSession, Attendance, AttendanceException


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['formatted_session', 'klass', 'date', 'teacher', 'status', 'attendance_summary', 'synced_badge']
    search_fields = ['klass__name', 'date', 'teacher__person__first_name']
    list_filter = ['status', 'date', 'school', 'synced']
    ordering = ['-date']
    readonly_fields = ['opened_at', 'closed_at', 'synced_at', 'updated_at', 'attendance_summary_detailed']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('school', 'klass', 'term', 'date', 'subject', 'teacher')
        }),
        ('Status', {
            'fields': ('status', 'synced')
        }),
        ('Timestamps', {
            'fields': ('opened_at', 'closed_at', 'synced_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Offline Sync', {
            'fields': ('local_id',),
            'classes': ('collapse',)
        }),
        ('Summary', {
            'fields': ('attendance_summary_detailed',),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_session(self, obj):
        return f"{obj.klass.name} ({obj.date.strftime('%Y-%m-%d')})"
    formatted_session.short_description = 'Session'
    
    def attendance_summary(self, obj):
        total = obj.total_students
        present = obj.present_count
        absent = obj.absent_count
        if total == 0:
            return "No records"
        return f"P:{present}/{total} | A:{absent}/{total}"
    attendance_summary.short_description = 'Attendance'
    
    def synced_badge(self, obj):
        if obj.synced:
            return format_html('<span style="color: green;">✓ Synced</span>')
        return format_html('<span style="color: orange;">⏳ Pending</span>')
    synced_badge.short_description = 'Sync Status'
    
    def attendance_summary_detailed(self, obj):
        counts = obj.attendances.values('status').annotate(count=Count('id')).order_by('status')
        summary = "\n".join([f"{item['status']}: {item['count']}" for item in counts])
        return summary or "No records yet"
    attendance_summary_detailed.short_description = 'Attendance Summary'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'session_info', 'status_badge', 'marked_by', 'marked_at', 'synced_status']
    search_fields = ['student__person__first_name', 'student__person__last_name', 'student__admission_number']
    list_filter = ['status', 'synced', 'marked_at', 'session__date']
    ordering = ['-marked_at']
    readonly_fields = ['marked_at', 'updated_at', 'last_sync_at']
    
    fieldsets = (
        ('Record', {
            'fields': ('session', 'student', 'status', 'marked_by')
        }),
        ('Details', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('marked_at', 'updated_at', 'last_sync_at'),
            'classes': ('collapse',)
        }),
        ('Offline Sync', {
            'fields': ('synced', 'local_id'),
            'classes': ('collapse',)
        }),
    )
    
    def session_info(self, obj):
        return f"{obj.session.klass} ({obj.session.date})"
    session_info.short_description = 'Session'
    
    def status_badge(self, obj):
        colors = {
            'P': 'green',
            'A': 'red',
            'L': 'orange',
            'E': 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(f'<span style="color: {color}; font-weight: bold;">{obj.get_status_display()}</span>')
    status_badge.short_description = 'Status'
    
    def synced_status(self, obj):
        if obj.synced:
            return format_html('<span style="color: green;">✓ Synced</span>')
        return format_html('<span style="color: orange;">⏳ Pending</span>')
    synced_status.short_description = 'Sync Status'


@admin.register(AttendanceException)
class AttendanceExceptionAdmin(admin.ModelAdmin):
    list_display = ['student', 'category', 'date_range', 'approved_by', 'created_at']
    search_fields = ['student__person__first_name', 'student__person__last_name']
    list_filter = ['category', 'start_date', 'approved_by']
    ordering = ['-start_date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Exception Details', {
            'fields': ('student', 'category', 'start_date', 'end_date', 'reason')
        }),
        ('Approval', {
            'fields': ('approved_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def date_range(self, obj):
        return f"{obj.start_date} to {obj.end_date}"
    date_range.short_description = 'Period'
