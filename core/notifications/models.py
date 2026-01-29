from django.db import models
from django.utils import timezone
from core.users.models import School, CustomUser, Student
from core.fees.models import Invoice, FeePayment, Arrears
import json


class NotificationPreference(models.Model):
    """Parent's notification preferences"""
    CHANNEL_CHOICES = (
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('both', 'SMS + Email'),
    )
    
    EVENT_TYPES = (
        ('invoice_issued', 'Invoice Issued'),
        ('payment_received', 'Payment Received'),
        ('arrears_warning', 'Arrears Warning (30+ days)'),
        ('arrears_critical', 'Arrears Critical (60+ days)'),
        ('payment_reminder', 'Payment Reminder (7 days before due)'),
        ('exam_results', 'Exam Results Posted'),
        ('attendance_alert', 'Low Attendance Alert'),
    )
    
    parent = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        limit_choices_to={'role': 'parent'}
    )
    
    # Notification channels
    sms_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=20, blank=True)  # For SMS
    
    # Event preferences
    invoice_issued = models.BooleanField(default=True)
    payment_received = models.BooleanField(default=True)
    arrears_warning = models.BooleanField(default=True)
    arrears_critical = models.BooleanField(default=True)
    payment_reminder = models.BooleanField(default=True)
    exam_results = models.BooleanField(default=False)
    attendance_alert = models.BooleanField(default=True)
    
    # Language preference
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('sw', 'Swahili'),
    )
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    
    # Quiet hours (don't send between these times)
    quiet_hours_start = models.TimeField(null=True, blank=True)  # e.g., 22:00 (10 PM)
    quiet_hours_end = models.TimeField(null=True, blank=True)    # e.g., 07:00 (7 AM)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_preference'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"{self.parent.get_full_name()} - Notifications"
    
    def is_in_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = timezone.now().time()
        if self.quiet_hours_start <= self.quiet_hours_end:
            # Normal case: quiet hours don't cross midnight
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:
            # Quiet hours cross midnight
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end


class Notification(models.Model):
    """Track all notifications sent to parents"""
    EVENT_CHOICES = (
        ('invoice_issued', 'Invoice Issued'),
        ('payment_received', 'Payment Received'),
        ('arrears_warning', 'Arrears Warning'),
        ('arrears_critical', 'Arrears Critical'),
        ('payment_reminder', 'Payment Reminder'),
        ('exam_results', 'Exam Results'),
        ('attendance_alert', 'Attendance Alert'),
        ('system_alert', 'System Alert'),
    )
    
    # Who receives the notification
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # What triggered the notification
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    
    # Related objects (for reference)
    student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    payment = models.ForeignKey(
        FeePayment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    arrears = models.ForeignKey(
        Arrears,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    # Message content
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Metadata
    data = models.JSONField(default=dict, blank=True)  # Extra data for tracking
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['event_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.recipient.get_full_name()} - {self.event_type}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class SMSLog(models.Model):
    """Track SMS messages sent"""
    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    )
    
    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name='sms_log',
        null=True,
        blank=True
    )
    
    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    
    # Provider info (M-Pesa, Twilio, Africa's Talking, etc.)
    provider = models.CharField(max_length=50, default='africas-talking')
    provider_message_id = models.CharField(max_length=100, blank=True)
    
    # Retry tracking
    attempt_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications_sms_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['phone_number']),
        ]
    
    def __str__(self):
        return f"SMS to {self.phone_number} - {self.status}"
    
    def can_retry(self):
        """Check if this SMS can be retried"""
        return self.status == 'failed' and self.attempt_count < self.max_retries
    
    def mark_as_sent(self, provider_message_id=''):
        """Mark SMS as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        if provider_message_id:
            self.provider_message_id = provider_message_id
        self.save()
    
    def mark_as_failed(self, error_message='', error_code=''):
        """Mark SMS as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.error_code = error_code
        self.attempt_count += 1
        self.save()


class EmailLog(models.Model):
    """Track email messages sent"""
    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    )
    
    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name='email_log',
        null=True,
        blank=True
    )
    
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    message_html = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    
    # Provider info (SendGrid, Mailgun, etc.)
    provider = models.CharField(max_length=50, default='django-email')
    provider_message_id = models.CharField(max_length=100, blank=True)
    
    # Retry tracking
    attempt_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    # Engagement tracking
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications_email_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['recipient_email']),
        ]
    
    def __str__(self):
        return f"Email to {self.recipient_email} - {self.status}"
    
    def can_retry(self):
        """Check if this email can be retried"""
        return self.status == 'failed' and self.attempt_count < self.max_retries
    
    def mark_as_sent(self, provider_message_id=''):
        """Mark email as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        if provider_message_id:
            self.provider_message_id = provider_message_id
        self.save()
    
    def mark_as_failed(self, error_message=''):
        """Mark email as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.attempt_count += 1
        self.save()


class NotificationTemplate(models.Model):
    """Reusable notification templates for different events"""
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='notification_templates',
        null=True,
        blank=True  # Null = system-wide template
    )
    
    event_type = models.CharField(max_length=30, choices=Notification.EVENT_CHOICES)
    language = models.CharField(max_length=5, choices=NotificationPreference.LANGUAGE_CHOICES, default='en')
    
    # Template content
    title = models.CharField(max_length=200)
    sms_template = models.TextField(help_text="SMS message template. Use {{var}} for variables.")
    email_subject = models.CharField(max_length=200, blank=True)
    email_template = models.TextField(blank=True, help_text="HTML email template")
    
    # Variables available in template
    variables = models.JSONField(
        default=list,
        blank=True,
        help_text="List of available variables: e.g., ['student_name', 'amount', 'due_date']"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_template'
        unique_together = ('school', 'event_type', 'language')
        ordering = ['school', 'event_type', 'language']
    
    def __str__(self):
        school_name = self.school.name if self.school else 'System'
        return f"{school_name} - {self.event_type} ({self.get_language_display()})"
    
    def render_sms(self, context):
        """Render SMS template with context variables"""
        from django.template import Template, Context
        template = Template(self.sms_template)
        return template.render(Context(context))
    
    def render_email(self, context):
        """Render email template with context variables"""
        from django.template import Template, Context
        template = Template(self.email_template)
        return template.render(Context(context))
