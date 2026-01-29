"""
Finance Engine Signals - Integration with Notifications Layer

Automatically trigger notifications when financial events occur:
- Invoice created → Send to student/parent
- Payment recorded → Confirmation SMS/email
- Arrears updated → Warning notifications
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal
import logging

from .models import Invoice, FeePayment, Arrears
from core.notifications.services import NotificationService
from core.users.models import Student

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Invoice)
def invoice_created_notify(sender, instance, created, **kwargs):
    """
    Signal: When an invoice is created, notify the student/parent
    
    Event: 'invoice_issued'
    Recipients: Student's parent(s)
    """
    if created and instance.status != 'cancelled':
        try:
            with transaction.atomic():
                # Get the student's parent/guardian
                student = instance.student
                if not student.user:
                    return
                
                # Create notification
                notification = NotificationService.create_notification(
                    recipient=student.user,
                    event_type='invoice_issued',
                    title=f'Invoice {instance.invoice_number} Issued',
                    message=f'New invoice for {instance.term.get_term_type_display()}: '
                            f'KES {instance.total_amount:,.2f} due on {instance.due_date.strftime("%B %d, %Y")}',
                    invoice=instance,
                    school=instance.school
                )
                
                # Dispatch immediately (async via Celery)
                if notification:
                    NotificationService.dispatch_notification(notification)
                    logger.info(f"Invoice notification queued for {student.user.email}")
        except Exception as e:
            logger.error(f"Error notifying on invoice creation: {str(e)}")


@receiver(post_save, sender=FeePayment)
def payment_recorded_notify(sender, instance, created, **kwargs):
    """
    Signal: When a payment is recorded, send confirmation
    
    Event: 'payment_received'
    Recipients: Student/parent who made payment
    """
    if created and instance.status == 'completed':
        try:
            with transaction.atomic():
                student = instance.invoice.student
                if not student.user:
                    return
                
                # Create notification
                notification = NotificationService.create_notification(
                    recipient=student.user,
                    event_type='payment_received',
                    title='Payment Received',
                    message=f'Payment of KES {instance.amount:,.2f} received via {instance.get_payment_method_display()} '
                            f'(Ref: {instance.reference}). New balance: KES {instance.invoice.balance:,.2f}',
                    invoice=instance.invoice,
                    payment=instance,
                    school=instance.school
                )
                
                if notification:
                    NotificationService.dispatch_notification(notification)
                    logger.info(f"Payment confirmation queued for {student.user.email}")
        except Exception as e:
            logger.error(f"Error notifying on payment: {str(e)}")


@receiver(post_save, sender=Arrears)
def arrears_updated_notify(sender, instance, created, **kwargs):
    """
    Signal: When arrears are updated, send warning notification
    
    Event: 'arrears_warning' (30-59 days) or 'arrears_critical' (60+ days)
    Recipients: Student/parent with arrears
    """
    if not instance.is_resolved:
        try:
            with transaction.atomic():
                student = instance.student
                if not student.user:
                    return
                
                # Determine event type based on days outstanding
                if instance.days_outstanding >= 60:
                    event_type = 'arrears_critical'
                    title = 'URGENT: Critical Arrears Notice'
                    message = f'Your account has {instance.days_outstanding} days of arrears. ' \
                              f'Total outstanding: KES {instance.total_arrears:,.2f}. ' \
                              f'Please contact the school office immediately.'
                elif instance.days_outstanding >= 30:
                    event_type = 'arrears_warning'
                    title = 'Arrears Warning'
                    message = f'You have {instance.days_outstanding} days of unpaid fees. ' \
                              f'Total outstanding: KES {instance.total_arrears:,.2f}. ' \
                              f'Please settle your account to avoid further action.'
                else:
                    # Don't notify for < 30 days
                    return
                
                # Create notification
                notification = NotificationService.create_notification(
                    recipient=student.user,
                    event_type=event_type,
                    title=title,
                    message=message,
                    arrears=instance,
                    school=instance.school
                )
                
                if notification:
                    NotificationService.dispatch_notification(notification)
                    logger.info(f"Arrears notification ({event_type}) queued for {student.user.email}")
        except Exception as e:
            logger.error(f"Error notifying on arrears: {str(e)}")


def connect_signals():
    """
    Explicitly connect signals. Call this in fees app config ready() method.
    """
    # Signals are auto-connected via @receiver decorator, but this function
    # can be called explicitly if needed for testing or reloading
    logger.info("Finance Engine signals registered")
