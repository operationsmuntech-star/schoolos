from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    NotificationPreference, Notification, SMSLog, EmailLog, NotificationTemplate
)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'parent_name', 'sms_enabled_badge', 'email_enabled_badge',
        'language', 'created_at'
    )
    list_filter = ('sms_enabled', 'email_enabled', 'language', 'created_at')
    search_fields = ('parent__first_name', 'parent__last_name', 'phone_number')
    
    fieldsets = (
        ('Parent Info', {
            'fields': ('parent',)
        }),
        ('Contact Details', {
            'fields': ('phone_number',)
        }),
        ('Notification Channels', {
            'fields': ('sms_enabled', 'email_enabled')
        }),
        ('Event Preferences', {
            'fields': (
                'invoice_issued', 'payment_received', 'arrears_warning',
                'arrears_critical', 'payment_reminder', 'exam_results',
                'attendance_alert'
            ),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('language', 'quiet_hours_start', 'quiet_hours_end')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def parent_name(self, obj):
        return obj.parent.get_full_name()
    parent_name.short_description = 'Parent'
    
    def sms_enabled_badge(self, obj):
        color = '#28a745' if obj.sms_enabled else '#dc3545'
        status = 'Enabled' if obj.sms_enabled else 'Disabled'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            status
        )
    sms_enabled_badge.short_description = 'SMS'
    
    def email_enabled_badge(self, obj):
        color = '#28a745' if obj.email_enabled else '#dc3545'
        status = 'Enabled' if obj.email_enabled else 'Disabled'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            status
        )
    email_enabled_badge.short_description = 'Email'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'recipient_name', 'event_type_badge', 'title', 'is_read_badge', 'created_at'
    )
    list_filter = ('event_type', 'is_read', 'created_at')
    search_fields = ('recipient__first_name', 'recipient__last_name', 'title', 'message')
    readonly_fields = (
        'recipient', 'event_type', 'student', 'invoice', 'payment', 'arrears',
        'is_read', 'read_at', 'created_at', 'updated_at', 'data_display'
    )
    
    fieldsets = (
        ('Recipient', {
            'fields': ('recipient',)
        }),
        ('Event Info', {
            'fields': ('event_type', 'student', 'invoice', 'payment', 'arrears')
        }),
        ('Message', {
            'fields': ('title', 'message')
        }),
        ('Metadata', {
            'fields': ('data_display',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'created_at', 'updated_at')
        }),
    )
    
    def recipient_name(self, obj):
        return obj.recipient.get_full_name()
    recipient_name.short_description = 'Recipient'
    
    def event_type_badge(self, obj):
        colors = {
            'invoice_issued': '#007bff',
            'payment_received': '#28a745',
            'arrears_warning': '#ffc107',
            'arrears_critical': '#dc3545',
            'payment_reminder': '#17a2b8',
            'exam_results': '#6f42c1',
            'attendance_alert': '#fd7e14',
            'system_alert': '#6c757d',
        }
        color = colors.get(obj.event_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_event_type_display()
        )
    event_type_badge.short_description = 'Event'
    
    def is_read_badge(self, obj):
        color = '#28a745' if obj.is_read else '#dc3545'
        status = 'Read' if obj.is_read else 'Unread'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            status
        )
    is_read_badge.short_description = 'Status'
    
    def data_display(self, obj):
        if obj.data:
            import json
            return json.dumps(obj.data, indent=2)
        return '(empty)'
    data_display.short_description = 'Extra Data'


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = (
        'phone_number', 'status_badge', 'provider', 'attempt_count',
        'created_at', 'sent_at'
    )
    list_filter = ('status', 'provider', 'created_at')
    search_fields = ('phone_number', 'message', 'provider_message_id')
    readonly_fields = (
        'notification', 'phone_number', 'message', 'provider', 'created_at',
        'sent_at', 'delivered_at', 'error_message_display'
    )
    
    fieldsets = (
        ('Recipient', {
            'fields': ('phone_number', 'notification')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('status', 'provider', 'provider_message_id')
        }),
        ('Retry Info', {
            'fields': ('attempt_count', 'max_retries')
        }),
        ('Error Info', {
            'fields': ('error_code', 'error_message_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'delivered_at')
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'queued': '#17a2b8',
            'sent': '#28a745',
            'delivered': '#6f42c1',
            'failed': '#dc3545',
            'bounced': '#fd7e14',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def error_message_display(self, obj):
        if obj.error_message:
            return format_html(
                '<div style="background-color: #f8d7da; padding: 10px; border-radius: 3px; color: #721c24;"><strong>Error:</strong> {}</div>',
                obj.error_message
            )
        return '(no error)'
    error_message_display.short_description = 'Error'

    actions = ['send_selected_sms']

    def send_selected_sms(self, request, queryset):
        """Admin action to attempt immediate send of selected queued SMS logs."""
        from django.contrib import messages
        from .services import SMSService

        sent = 0
        failed = 0
        for sms in queryset:
            if sms.status != 'queued':
                continue
            try:
                result = SMSService.send_via_provider(sms)
                if result.get('success'):
                    sent += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        messages.info(request, f"SMS action: {sent} sent, {failed} failed")
    send_selected_sms.short_description = 'Send selected queued SMS now'


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = (
        'recipient_email', 'status_badge', 'engagement_badge',
        'attempt_count', 'created_at', 'sent_at'
    )
    list_filter = ('status', 'provider', 'created_at')
    search_fields = ('recipient_email', 'subject', 'provider_message_id')
    readonly_fields = (
        'notification', 'recipient_email', 'subject', 'message_html_display',
        'provider', 'created_at', 'sent_at', 'delivered_at', 'opened_at',
        'clicked_at', 'error_message_display'
    )
    
    fieldsets = (
        ('Recipient', {
            'fields': ('recipient_email', 'notification')
        }),
        ('Message', {
            'fields': ('subject', 'message_html_display')
        }),
        ('Status', {
            'fields': ('status', 'provider', 'provider_message_id')
        }),
        ('Retry Info', {
            'fields': ('attempt_count', 'max_retries')
        }),
        ('Engagement', {
            'fields': ('opened_at', 'clicked_at')
        }),
        ('Error Info', {
            'fields': ('error_message_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'delivered_at')
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'queued': '#17a2b8',
            'sent': '#28a745',
            'delivered': '#6f42c1',
            'failed': '#dc3545',
            'bounced': '#fd7e14',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def engagement_badge(self, obj):
        if obj.opened_at and obj.clicked_at:
            return format_html(
                '<span style="background-color: #6f42c1; color: white; padding: 3px 8px; border-radius: 3px;">Opened & Clicked</span>'
            )
        elif obj.opened_at:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px;">Opened</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 3px;">Not Opened</span>'
        )
    engagement_badge.short_description = 'Engagement'
    
    def message_html_display(self, obj):
        return format_html(
            '<div style="background-color: #f8f9fa; padding: 10px; border-radius: 3px; border: 1px solid #dee2e6; overflow-x: auto;">{}</div>',
            obj.message_html[:500] + '...' if len(obj.message_html) > 500 else obj.message_html
        )
    message_html_display.short_description = 'Message (Preview)'
    
    def error_message_display(self, obj):
        if obj.error_message:
            return format_html(
                '<div style="background-color: #f8d7da; padding: 10px; border-radius: 3px; color: #721c24;"><strong>Error:</strong> {}</div>',
                obj.error_message
            )
        return '(no error)'
    error_message_display.short_description = 'Error'


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'school_name', 'event_type', 'language_display', 'is_active_badge', 'created_at'
    )
    list_filter = ('event_type', 'language', 'is_active', 'school', 'created_at')
    search_fields = ('school__name', 'title', 'event_type')
    
    fieldsets = (
        ('Template Info', {
            'fields': ('school', 'event_type', 'language', 'title', 'is_active')
        }),
        ('SMS Template', {
            'fields': ('sms_template', 'variables'),
            'description': 'Use {{variable_name}} for substitution'
        }),
        ('Email Template', {
            'fields': ('email_subject', 'email_template'),
            'description': 'Use {{variable_name}} for substitution. HTML supported.'
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def school_name(self, obj):
        return obj.school.name if obj.school else 'System (All Schools)'
    school_name.short_description = 'School'
    
    def language_display(self, obj):
        return obj.get_language_display()
    language_display.short_description = 'Language'
    
    def is_active_badge(self, obj):
        color = '#28a745' if obj.is_active else '#dc3545'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            status
        )
    is_active_badge.short_description = 'Status'
