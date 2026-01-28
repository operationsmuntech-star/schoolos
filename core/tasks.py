from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_email_task(subject, message, from_email, recipient_list):
    """
    Async task to send emails without blocking the request.
    Used for email verification, password resets, etc.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return f"Email sent to {', '.join(recipient_list)}"
    except Exception as e:
        return f"Email send failed: {str(e)}"


@shared_task
def send_html_email_task(subject, html_message, from_email, recipient_list):
    """
    Async task to send HTML emails.
    """
    from django.core.mail import EmailMultiAlternatives
    
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=html_message,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send(fail_silently=False)
        return f"HTML email sent to {', '.join(recipient_list)}"
    except Exception as e:
        return f"HTML email send failed: {str(e)}"
