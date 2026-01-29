from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from .generator import generate_attendance_csv, generate_fees_csv
import datetime
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_and_email_report(self, school_id, report_type, start_date=None, end_date=None, recipient_email=None):
    """Generate report and email it to the recipient (async task)"""
    try:
        if start_date:
            start_date = datetime.date.fromisoformat(start_date)
        if end_date:
            end_date = datetime.date.fromisoformat(end_date)

        if report_type == 'attendance':
            filename, content = generate_attendance_csv(school_id, start_date, end_date)
        elif report_type == 'fees':
            filename, content = generate_fees_csv(school_id, start_date, end_date)
        else:
            return {'success': False, 'error': 'Unknown report type'}

        subject = f"{report_type.title()} Report"
        body = f"Attached is the {report_type} report for the selected period."
        email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient_email])
        email.attach(filename, content, 'text/csv')
        email.send(fail_silently=False)

        logger.info(f"Report {filename} generated and emailed to {recipient_email}")
        return {'success': True, 'filename': filename}
    except Exception as e:
        logger.error(f"Error generating/emailing report: {str(e)}")
        return {'success': False, 'error': str(e)}
