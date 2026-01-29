import io
import csv
import datetime
import logging
from django.conf import settings
from core.attendance.models import Attendance
from core.fees.models import Invoice, FeePayment
from core.users.models import School

logger = logging.getLogger(__name__)


def generate_attendance_csv(school_id, start_date=None, end_date=None):
    school = School.objects.get(id=school_id)
    start_date = start_date or (datetime.date.today().replace(day=1))
    end_date = end_date or datetime.date.today()

    qs = Attendance.objects.filter(school=school, date__gte=start_date, date__lte=end_date).select_related('student')

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Student', 'Status', 'Remarks'])

    for rec in qs.order_by('date'):
        writer.writerow([
            rec.date.isoformat(),
            rec.student.user.get_full_name(),
            rec.status,
            rec.remarks or ''
        ])

    content = output.getvalue().encode('utf-8')
    output.close()
    filename = f'attendance_{school.slug}_{start_date.isoformat()}_{end_date.isoformat()}.csv'
    return filename, content


def generate_fees_csv(school_id, start_date=None, end_date=None):
    school = School.objects.get(id=school_id)
    start_date = start_date or (datetime.date.today().replace(day=1))
    end_date = end_date or datetime.date.today()

    invoices = Invoice.objects.filter(school=school, created_at__date__gte=start_date, created_at__date__lte=end_date).select_related('student_class')

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Invoice ID', 'Description', 'Total Amount', 'Paid Amount', 'Outstanding', 'Due Date', 'Created At'])

    for inv in invoices.order_by('created_at'):
        paid = FeePayment.objects.filter(invoice=inv, status='completed').aggregate(total_amount_sum=None)
        # safe calculations
        try:
            paid_amount = sum([float(p.amount) for p in inv.fee_payments.filter(status='completed')])
        except Exception:
            paid_amount = 0.0
        outstanding = float(inv.total_amount) - paid_amount
        writer.writerow([
            inv.id,
            inv.description,
            float(inv.total_amount),
            paid_amount,
            outstanding,
            inv.due_date.isoformat() if inv.due_date else '',
            inv.created_at.isoformat()
        ])

    content = output.getvalue().encode('utf-8')
    output.close()
    filename = f'fees_{school.slug}_{start_date.isoformat()}_{end_date.isoformat()}.csv'
    return filename, content
