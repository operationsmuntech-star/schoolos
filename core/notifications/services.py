from django.utils import timezone
from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings
import logging
import re

from .models import (
    Notification, SMSLog, EmailLog, NotificationTemplate,
    NotificationPreference
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Central service for creating and dispatching notifications"""
    
    @staticmethod
    def create_notification(
        recipient,
        event_type,
        title,
        message,
        student=None,
        invoice=None,
        payment=None,
        arrears=None,
        data=None
    ):
        """Create a notification record"""
        notification = Notification.objects.create(
            recipient=recipient,
            event_type=event_type,
            title=title,
            message=message,
            student=student,
            invoice=invoice,
            payment=payment,
            arrears=arrears,
            data=data or {}
        )
        return notification
    
    @staticmethod
    def should_notify(recipient, event_type):
        """Check if recipient wants to receive this type of notification"""
        try:
            prefs = NotificationPreference.objects.get(parent=recipient)
            
            # Check if in quiet hours
            if prefs.is_in_quiet_hours():
                return False
            
            # Check event-specific preference
            preference_map = {
                'invoice_issued': prefs.invoice_issued,
                'payment_received': prefs.payment_received,
                'arrears_warning': prefs.arrears_warning,
                'arrears_critical': prefs.arrears_critical,
                'payment_reminder': prefs.payment_reminder,
                'exam_results': prefs.exam_results,
                'attendance_alert': prefs.attendance_alert,
            }
            
            return preference_map.get(event_type, True)
        except NotificationPreference.DoesNotExist:
            # Default to sending if no preferences set
            return True
    
    @staticmethod
    def get_channels(recipient):
        """Get enabled notification channels for recipient"""
        try:
            prefs = NotificationPreference.objects.get(parent=recipient)
            channels = []
            if prefs.sms_enabled:
                channels.append('sms')
            if prefs.email_enabled:
                channels.append('email')
            return channels
        except NotificationPreference.DoesNotExist:
            return ['email']  # Default to email
    
    @staticmethod
    def dispatch_notification(
        notification,
        channels=None
    ):
        """Dispatch notification through specified channels"""
        if channels is None:
            channels = NotificationService.get_channels(notification.recipient)
        
        results = {'sms': None, 'email': None}
        
        for channel in channels:
            if channel == 'sms':
                results['sms'] = SMSService.send_sms(notification)
            elif channel == 'email':
                results['email'] = EmailService.send_email(notification)
        
        return results


class SMSService:
    """Service for sending SMS notifications"""
    
    @staticmethod
    def send_sms(notification):
        """Send SMS notification
        
        Returns:
            SMSLog instance or None if unable to send
        """
        try:
            # Get parent's phone number
            prefs = NotificationPreference.objects.get(parent=notification.recipient)
            phone_number = prefs.phone_number
            
            if not phone_number:
                logger.warning(
                    f"No phone number for user {notification.recipient.id}"
                )
                return None
            
            # Render message from template if available
            message = NotificationService._render_template(
                notification,
                'sms'
            )
            
            # Create SMS log
            sms_log = SMSLog.objects.create(
                notification=notification,
                phone_number=phone_number,
                message=message,
                provider=settings.SMS_PROVIDER if hasattr(settings, 'SMS_PROVIDER') else 'africas-talking'
            )
            
            # Queue for sending (will be picked up by Celery task)
            return sms_log
            
        except NotificationPreference.DoesNotExist:
            logger.warning(
                f"No notification preferences for user {notification.recipient.id}"
            )
            return None
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return None
    
    @staticmethod
    def send_via_provider(sms_log):
        """Send SMS via provider (called by Celery task)
        
        Delegates to SMS Gateway for provider routing.
        """
        try:
            from .sms_gateway import send_sms_via_provider
            
            result = send_sms_via_provider(sms_log)
            
            if result['success']:
                sms_log.mark_as_sent(result.get('message_id', ''))
                logger.info(f"SMS sent successfully: {sms_log.id}")
            else:
                sms_log.mark_as_failed(
                    result.get('error_message', 'Unknown error'),
                    result.get('error_code', '')
                )
                logger.error(f"SMS send failed: {sms_log.id} - {result['error_message']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in send_via_provider: {str(e)}")
            sms_log.mark_as_failed(str(e))
            return {'success': False, 'error_message': str(e)}


class EmailService:
    """Service for sending email notifications"""
    
    @staticmethod
    def send_email(notification):
        """Send email notification
        
        Returns:
            EmailLog instance or None if unable to send
        """
        try:
            recipient_email = notification.recipient.email
            
            if not recipient_email:
                logger.warning(
                    f"No email for user {notification.recipient.id}"
                )
                return None
            
            # Render message from template if available
            subject, html_message = NotificationService._render_template(
                notification,
                'email'
            )
            
            # Create email log
            email_log = EmailLog.objects.create(
                notification=notification,
                recipient_email=recipient_email,
                subject=subject,
                message_html=html_message
            )
            
            # Queue for sending (will be picked up by Celery task)
            return email_log
            
        except Exception as e:
            logger.error(f"Error creating email log: {str(e)}")
            return None
    
    @staticmethod
    def send_via_provider(email_log):
        """Send email via provider (called by Celery task)"""
        try:
            result = send_mail(
                subject=email_log.subject,
                message=email_log.subject,  # Fallback text
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_log.recipient_email],
                html_message=email_log.message_html,
                fail_silently=False,
            )
            
            if result > 0:
                email_log.mark_as_sent()
                logger.info(f"Email sent successfully: {email_log.id}")
                return {'success': True}
            else:
                email_log.mark_as_failed('Django send_mail returned 0')
                return {'success': False, 'error_message': 'Send failed'}
                
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            email_log.mark_as_failed(str(e))
            return {'success': False, 'error_message': str(e)}


class NotificationService:
    """Extended service with template rendering"""
    
    @staticmethod
    def _render_template(notification, channel_type):
        """Render notification using templates"""
        try:
            # Get school from recipient
            school = None
            if hasattr(notification.recipient, 'school'):
                school = notification.recipient.school
            
            # Get template
            template = NotificationTemplate.objects.filter(
                event_type=notification.event_type,
                is_active=True
            ).filter(
                models.Q(school=school) | models.Q(school__isnull=True)
            ).first()
            
            if not template:
                # Fall back to notification message
                if channel_type == 'sms':
                    return notification.message
                else:
                    return notification.title, notification.message
            
            # Build context
            context_dict = {
                'student_name': '',
                'amount': '',
                'due_date': '',
                'days_outstanding': '',
                'parent_name': notification.recipient.get_full_name(),
                'school_name': school.name if school else '',
            }
            
            # Add specific data
            if notification.student:
                context_dict['student_name'] = notification.student.user.get_full_name()
            if notification.invoice:
                context_dict['amount'] = str(notification.invoice.total_amount)
                context_dict['due_date'] = notification.invoice.due_date
            if notification.arrears:
                context_dict['days_outstanding'] = notification.arrears.days_outstanding
            
            # Merge with notification data
            context_dict.update(notification.data)
            
            if channel_type == 'sms':
                return template.render_sms(context_dict)
            else:
                subject = template.render_sms(context_dict) if template.email_subject else template.title
                html = template.render_email(context_dict)
                return subject, html
                
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            if channel_type == 'sms':
                return notification.message
            else:
                return notification.title, notification.message
