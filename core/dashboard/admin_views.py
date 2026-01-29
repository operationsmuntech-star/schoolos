from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Sum
from core.users.models import School, Student
from core.fees.models import FeePayment, Invoice
from core.attendance.models import Attendance
from django.utils import timezone
import datetime

@staff_member_required
def analytics_dashboard(request):
    """Admin analytics dashboard with simple charts"""
    today = timezone.now().date()
    # Enrollment trend: students per month for last 6 months
    labels = []
    enrolled_counts = []
    for i in range(5, -1, -1):
        month = today - datetime.timedelta(days=30*i)
        label = month.strftime('%b %Y')
        labels.append(label)
        start = month.replace(day=1)
        # approximate month end
        end = (start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
        count = Student.objects.filter(enrollment_date__date__gte=start, enrollment_date__date__lte=end).count()
        enrolled_counts.append(count)

    # Revenue: fees collected per month last 6 months
    revenue = []
    for i in range(5, -1, -1):
        month = today - datetime.timedelta(days=30*i)
        start = month.replace(day=1)
        end = (start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
        amt = FeePayment.objects.filter(created_at__date__gte=start, created_at__date__lte=end, status='completed').aggregate(total=Sum('amount'))['total'] or 0
        revenue.append(float(amt))

    # Attendance summary for current month
    month_start = today.replace(day=1)
    attendance_total = Attendance.objects.filter(date__gte=month_start).count()
    attendance_present = Attendance.objects.filter(date__gte=month_start, status='present').count()
    attendance_percentage = (attendance_present / attendance_total * 100) if attendance_total else 0

    context = {
        'labels': labels,
        'enrolled_counts': enrolled_counts,
        'revenue': revenue,
        'attendance_percentage': round(attendance_percentage, 1),
    }
    return render(request, 'admin/analytics.html', context)
