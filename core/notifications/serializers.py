from rest_framework import serializers
from .models import (
    NotificationPreference, Notification, SMSLog, EmailLog, NotificationTemplate
)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.get_full_name', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'parent', 'parent_name', 'sms_enabled', 'email_enabled',
            'phone_number', 'invoice_issued', 'payment_received', 'arrears_warning',
            'arrears_critical', 'payment_reminder', 'exam_results', 'attendance_alert',
            'language', 'quiet_hours_start', 'quiet_hours_end', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'parent', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    student_name = serializers.CharField(
        source='student.user.get_full_name',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_name', 'event_type', 'event_type_display',
            'title', 'message', 'student', 'student_name', 'invoice', 'payment', 'arrears',
            'is_read', 'read_at', 'data', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'recipient', 'event_type', 'student', 'invoice', 'payment', 'arrears',
            'created_at', 'updated_at'
        ]


class SMSLogSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_retry = serializers.SerializerMethodField()
    
    class Meta:
        model = SMSLog
        fields = [
            'id', 'notification', 'phone_number', 'message', 'status', 'status_display',
            'provider', 'provider_message_id', 'attempt_count', 'max_retries', 'can_retry',
            'error_message', 'error_code', 'created_at', 'sent_at', 'delivered_at'
        ]
        read_only_fields = [
            'id', 'status', 'provider', 'created_at', 'sent_at', 'delivered_at'
        ]
    
    def get_can_retry(self, obj):
        return obj.can_retry()


class EmailLogSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_retry = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailLog
        fields = [
            'id', 'notification', 'recipient_email', 'subject', 'status', 'status_display',
            'provider', 'provider_message_id', 'attempt_count', 'max_retries', 'can_retry',
            'error_message', 'opened_at', 'clicked_at', 'created_at', 'sent_at', 'delivered_at'
        ]
        read_only_fields = [
            'id', 'status', 'provider', 'created_at', 'sent_at', 'delivered_at'
        ]
    
    def get_can_retry(self, obj):
        return obj.can_retry()


class NotificationTemplateSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True, allow_null=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'school', 'school_name', 'event_type', 'event_type_display',
            'language', 'language_display', 'title', 'sms_template', 'email_subject',
            'email_template', 'variables', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
