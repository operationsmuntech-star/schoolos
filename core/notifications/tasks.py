from celery import shared_task
from django.utils import timezone
import logging

from .models import SMSLog, EmailLog
from .services import SMSService, EmailService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_pending_sms(self):
    """Send all pending SMS notifications"""
    try:
        pending_sms = SMSLog.objects.filter(status='queued').order_by('created_at')[:100]
        
        sent = 0
        failed = 0
        
        for sms_log in pending_sms:
            try:
                result = SMSService.send_via_provider(sms_log)
                if result['success']:
                    sent += 1
                else:
                    failed += 1
                    
                    # Retry if allowed
                    if sms_log.can_retry():
                        self.retry(countdown=60 * (sms_log.attempt_count + 1))
            except Exception as e:
                logger.error(f"Error sending SMS {sms_log.id}: {str(e)}")
                failed += 1
        
        logger.info(f"SMS batch sent: {sent} successful, {failed} failed")
        return {'sent': sent, 'failed': failed}
        
    except Exception as e:
        logger.error(f"Error in send_pending_sms task: {str(e)}")
        raise


@shared_task(bind=True, max_retries=3)
def send_pending_emails(self):
    """Send all pending email notifications"""
    try:
        pending_emails = EmailLog.objects.filter(status='queued').order_by('created_at')[:100]
        
        sent = 0
        failed = 0
        
        for email_log in pending_emails:
            try:
                result = EmailService.send_via_provider(email_log)
                if result['success']:
                    sent += 1
                else:
                    failed += 1
                    
                    # Retry if allowed
                    if email_log.can_retry():
                        self.retry(countdown=120 * (email_log.attempt_count + 1))
            except Exception as e:
                logger.error(f"Error sending email {email_log.id}: {str(e)}")
                failed += 1
        
        logger.info(f"Email batch sent: {sent} successful, {failed} failed")
        return {'sent': sent, 'failed': failed}
        
    except Exception as e:
        logger.error(f"Error in send_pending_emails task: {str(e)}")
        raise


@shared_task
def cleanup_old_notifications():
    """Clean up old notification logs (keep last 90 days)"""
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Delete old SMS logs
        sms_deleted, _ = SMSLog.objects.filter(created_at__lt=cutoff_date).delete()
        logger.info(f"Deleted {sms_deleted} old SMS logs")
        
        # Delete old email logs
        email_deleted, _ = EmailLog.objects.filter(created_at__lt=cutoff_date).delete()
        logger.info(f"Deleted {email_deleted} old email logs")
        
        return {'sms_deleted': sms_deleted, 'email_deleted': email_deleted}
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_notifications: {str(e)}")
        raise


@shared_task
def send_payment_reminder_notifications():
    """Send payment reminder notifications for invoices due in 7 days"""
    try:
        from django.utils import timezone
        from datetime import timedelta
        from core.fees.models import Invoice
        from core.notifications.services import NotificationService
        
        due_soon = timezone.now().date() + timedelta(days=7)
        
        invoices = Invoice.objects.filter(
            due_date=due_soon,
            status__in=['issued', 'partial'],
            balance__gt=0
        )
        
        sent_count = 0
        for invoice in invoices:
            try:
                parent = invoice.student.user
                
                if NotificationService.should_notify(parent, 'payment_reminder'):
                    notification = NotificationService.create_notification(
                        recipient=parent,
                        event_type='payment_reminder',
                        title=f'Payment Due in 7 Days',
                        message=f'Invoice {invoice.invoice_number} is due on {invoice.due_date}. Amount: {invoice.balance}',
                        student=invoice.student,
                        invoice=invoice,
                        data={
                            'invoice_number': invoice.invoice_number,
                            'amount': str(invoice.balance),
                            'due_date': str(invoice.due_date),
                        }
                    )
                    
                    channels = NotificationService.get_channels(parent)
                    NotificationService.dispatch_notification(notification, channels)
                    sent_count += 1
            except Exception as e:
                logger.error(f"Error sending reminder for invoice {invoice.id}: {str(e)}")
        
        logger.info(f"Sent {sent_count} payment reminder notifications")
        return {'sent': sent_count}
        
    except Exception as e:
        logger.error(f"Error in send_payment_reminder_notifications: {str(e)}")
        raise


@shared_task
def send_arrears_notifications():
    """Send arrears notifications for students with overdue fees"""
    try:
        from core.fees.models import Arrears
        from core.notifications.services import NotificationService
        
        # Critical arrears (60+ days)
        critical_arrears = Arrears.objects.filter(
            days_outstanding__gte=60,
            is_resolved=False
        )
        
        for arrears in critical_arrears:
            try:
                parent = arrears.student.user
                
                if NotificationService.should_notify(parent, 'arrears_critical'):
                    notification = NotificationService.create_notification(
                        recipient=parent,
                        event_type='arrears_critical',
                        title='Urgent: Critical Arrears',
                        message=f'Student account has critical arrears of {arrears.total_arrears} ({arrears.days_outstanding} days overdue).',
                        student=arrears.student,
                        arrears=arrears,
                        data={
                            'total_arrears': str(arrears.total_arrears),
                            'days_outstanding': arrears.days_outstanding,
                        }
                    )
                    
                    channels = NotificationService.get_channels(parent)
                    NotificationService.dispatch_notification(notification, channels)
            except Exception as e:
                logger.error(f"Error sending critical arrears notification: {str(e)}")
        
        # Warning arrears (30-60 days)
        warning_arrears = Arrears.objects.filter(
            days_outstanding__gte=30,
            days_outstanding__lt=60,
            is_resolved=False
        )
        
        for arrears in warning_arrears:
            try:
                parent = arrears.student.user
                
                if NotificationService.should_notify(parent, 'arrears_warning'):
                    notification = NotificationService.create_notification(
                        recipient=parent,
                        event_type='arrears_warning',
                        title='Payment Required: School Fees Overdue',
                        message=f'Student account has pending fees of {arrears.total_arrears} ({arrears.days_outstanding} days overdue).',
                        student=arrears.student,
                        arrears=arrears,
                        data={
                            'total_arrears': str(arrears.total_arrears),
                            'days_outstanding': arrears.days_outstanding,
                        }
                    )
                    
                    channels = NotificationService.get_channels(parent)
                    NotificationService.dispatch_notification(notification, channels)
            except Exception as e:
                logger.error(f"Error sending arrears warning notification: {str(e)}")
        
        return {'critical': critical_arrears.count(), 'warning': warning_arrears.count()}
        
    except Exception as e:
        logger.error(f"Error in send_arrears_notifications: {str(e)}")
        raise
