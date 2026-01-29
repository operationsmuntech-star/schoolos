"""
Student Dashboard Views
Provides student-facing views for checking grades, attendance, fees, and notifications
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from core.users.models import Student, CustomUser
from core.fees.models import Invoice, FeePayment
from core.attendance.models import Attendance
from core.examinations.models import Marks
from core.notifications.models import Notification
from datetime import datetime, timedelta
import json


def student_required(view_func):
    """Decorator to ensure user is a student"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        if request.user.role != 'student':
            return JsonResponse({'error': 'Only students can access this'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def student_dashboard(request):
    """
    Student dashboard view - displays grades, attendance, fees, notifications
    """
    # Verify user is a student
    if request.user.role != 'student':
        return render(request, '403.html', {'message': 'Only students can access this page'}, status=403)
    
    return render(request, 'student/dashboard.html')


@login_required
@student_required
def student_api_overview(request):
    """API endpoint: Student overview (GPA, attendance %, fees status)"""
    try:
        student = get_object_or_404(Student, user=request.user)
        
        # Calculate attendance percentage
        total_classes = Attendance.objects.filter(student_class=student.student_class).count()
        present_count = Attendance.objects.filter(
            student=student,
            status='present'
        ).count()
        attendance_percentage = (present_count / total_classes * 100) if total_classes > 0 else 0
        
        # Calculate fee status
        total_invoices = Invoice.objects.filter(
            student_class=student.student_class
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        total_paid = FeePayment.objects.filter(
            invoice__student_class=student.student_class,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        outstanding = total_invoices - total_paid
        
        # Get latest marks (GPA proxy)
        latest_marks = Marks.objects.filter(student=student).order_by('-date')[:5]
        # Use percentage if available, otherwise compute from marks_obtained/total_marks
        scores = []
        for m in latest_marks:
            if m.percentage is not None:
                scores.append(m.percentage)
            else:
                try:
                    scores.append((m.marks_obtained / m.total_marks) * 100)
                except Exception:
                    continue
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return JsonResponse({
            'success': True,
            'data': {
                'student_name': student.user.get_full_name(),
                'registration_number': student.registration_number,
                'grade': student.grade,
                'attendance_percentage': round(attendance_percentage, 1),
                'average_score': round(avg_score, 1),
                'fees_paid': round(total_paid, 2),
                'fees_outstanding': round(outstanding, 2),
                'enrollment_date': student.enrollment_date.isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@student_required
def student_api_grades(request):
    """API endpoint: Student grades and exam results"""
    try:
        student = get_object_or_404(Student, user=request.user)
        
        # Group marks by exam_type and date
        marks_qs = Marks.objects.filter(student=student).order_by('-date')
        grades_data = []
        grouped = {}
        for mark in marks_qs:
            key = (mark.exam_type or 'Exam', mark.date.date().isoformat())
            grouped.setdefault(key, []).append(mark)

        for (exam_type, date_str), marks in grouped.items():
            subject_marks = []
            for mark in marks:
                # compute percentage
                pct = mark.percentage if mark.percentage is not None else (
                    (mark.marks_obtained / mark.total_marks) * 100 if mark.total_marks else None
                )
                grade_letter = calculate_grade(pct) if pct is not None else 'N/A'
                subject_marks.append({
                    'subject': mark.subject or 'N/A',
                    'score': float(mark.marks_obtained),
                    'grade': grade_letter,
                    'comments': ''
                })

            grades_data.append({
                'exam_session': exam_type,
                'date': date_str,
                'term': 'N/A',
                'subjects': subject_marks
            })
        
        return JsonResponse({
            'success': True,
            'data': grades_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@student_required
def student_api_attendance(request):
    """API endpoint: Student attendance records"""
    try:
        student = get_object_or_404(Student, user=request.user)
        
        # Get attendance records for current month
        today = datetime.now().date()
        month_start = today.replace(day=1)
        
        attendance_records = Attendance.objects.filter(
            student=student,
            date__gte=month_start
        ).order_by('-date')
        
        # Aggregate statistics
        present = attendance_records.filter(status='present').count()
        absent = attendance_records.filter(status='absent').count()
        late = attendance_records.filter(status='late').count()
        excused = attendance_records.filter(status='excused').count()
        total = attendance_records.count()
        
        records = []
        for record in attendance_records[:30]:  # Last 30 records
            records.append({
                'date': record.date.isoformat(),
                'status': record.status,
                'remarks': record.remarks or ''
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'current_month': today.strftime('%B %Y'),
                'statistics': {
                    'present': present,
                    'absent': absent,
                    'late': late,
                    'excused': excused,
                    'total': total,
                    'percentage': round((present / total * 100) if total > 0 else 0, 1)
                },
                'records': records
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@student_required
def student_api_fees(request):
    """API endpoint: Student fees and payment history"""
    try:
        student = get_object_or_404(Student, user=request.user)
        
        # Get invoices for this student's class
        invoices = Invoice.objects.filter(
            student_class=student.student_class
        ).order_by('-created_at')
        
        invoices_data = []
        for invoice in invoices:
            # Get payments for this invoice
            payments = FeePayment.objects.filter(invoice=invoice, status='completed')
            paid_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
            outstanding = invoice.total_amount - paid_amount
            
            invoices_data.append({
                'id': invoice.id,
                'description': invoice.description,
                'total_amount': float(invoice.total_amount),
                'paid_amount': float(paid_amount),
                'outstanding': float(outstanding),
                'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                'status': 'paid' if outstanding == 0 else 'partial' if paid_amount > 0 else 'pending',
                'created_at': invoice.created_at.isoformat()
            })
        
        # Get payment history
        payments = FeePayment.objects.filter(
            invoice__student_class=student.student_class,
            status='completed'
        ).order_by('-created_at')
        
        payment_history = []
        for payment in payments[:20]:  # Last 20 payments
            payment_history.append({
                'amount': float(payment.amount),
                'method': payment.payment_method,
                'date': payment.created_at.isoformat(),
                'invoice': payment.invoice.description if payment.invoice else 'N/A'
            })
        
        total_invoiced = sum([inv['total_amount'] for inv in invoices_data])
        total_paid = sum([inv['paid_amount'] for inv in invoices_data])
        total_outstanding = total_invoiced - total_paid
        
        return JsonResponse({
            'success': True,
            'data': {
                'summary': {
                    'total_invoiced': round(total_invoiced, 2),
                    'total_paid': round(total_paid, 2),
                    'total_outstanding': round(total_outstanding, 2)
                },
                'invoices': invoices_data,
                'payment_history': payment_history
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@student_required
def student_api_notifications(request):
    """API endpoint: Student notifications"""
    try:
        student = get_object_or_404(Student, user=request.user)
        
        # Get notifications for this student
        notifications = Notification.objects.filter(
            student=student
        ).order_by('-created_at')[:20]
        
        notif_data = []
        for notif in notifications:
            notif_data.append({
                'id': notif.id,
                'event_type': notif.event_type,
                'title': notif.title,
                'message': notif.message,
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat(),
                'data': notif.data or {}
            })
        
        return JsonResponse({
            'success': True,
            'data': notif_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@student_required
def student_api_mark_notification_read(request, notification_id):
    """API endpoint: Mark notification as read"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        student = get_object_or_404(Student, user=request.user)
        notification = get_object_or_404(Notification, id=notification_id, student=student)
        notification.is_read = True
        notification.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def calculate_grade(score):
    """Convert numeric score to letter grade"""
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'
