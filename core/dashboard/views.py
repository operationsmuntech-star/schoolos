from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q, Sum
from core.users.models import Student, Teacher, School
from core.attendance.models import Attendance, AttendanceReport
from core.admissions.models import Admission
from core.fees.models import Invoice, FeePayment
import json
from datetime import datetime, timedelta

@login_required
def index(request):
    """
    Dashboard view: provides comprehensive overview of school metrics
    """
    # Get user's school
    school = request.user.school if hasattr(request.user, 'school') else None
    
    # Calculate key metrics
    if school:
        total_students = Student.objects.filter(school=school, is_active=True).count()
        total_teachers = Teacher.objects.filter(school=school, is_active=True).count()
        active_classes = 24  # This should be calculated from your Class model if it exists
        
        # Calculate attendance rate for the day
        today = datetime.now().date()
        attendance_today = Attendance.objects.filter(
            date=today,
            present=True
        ).count()
        total_expected = Student.objects.filter(school=school, is_active=True).count()
        attendance_rate = round((attendance_today / total_expected * 100) if total_expected > 0 else 0)
    else:
        # Fallback for non-school-affiliated users
        total_students = Student.objects.filter(is_active=True).count()
        total_teachers = Teacher.objects.filter(is_active=True).count()
        active_classes = 24
        attendance_rate = 92
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'active_classes': active_classes,
        'attendance_rate': attendance_rate,
        'user_role': getattr(request.user, 'role', 'admin'),
    }
    
    return render(request, 'dashboard/index.html', context)

@login_required
def stats_api(request):
    """
    API endpoint for dashboard statistics (JSON)
    Used by frontend charts and widgets
    """
    try:
        school = request.user.school if hasattr(request.user, 'school') else None
        
        # Student count
        students_query = Student.objects.filter(is_active=True)
        if school:
            students_query = students_query.filter(school=school)
        total_students = students_query.count()
        
        # Teacher count
        teachers_query = Teacher.objects.filter(is_active=True)
        if school:
            teachers_query = teachers_query.filter(school=school)
        total_teachers = teachers_query.count()
        
        # Attendance data for the week
        attendance_data = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).date()
            count = Attendance.objects.filter(date=date, present=True).count()
            attendance_data.append(count)
        
        # Finance data (sample - implement with actual fee data)
        finance_data = [1500, 2300, 3200, 4500, 1200, 5000, 3800]
        
        response_data = {
            'success': True,
            'counts': {
                'students': total_students,
                'teachers': total_teachers,
                'timestamp': datetime.now().isoformat()
            },
            'attendance': attendance_data,
            'finance': finance_data,
        }
        
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def module_stats(request, module_name):
    """
    Get statistics for a specific module
    """
    try:
        school = request.user.school if hasattr(request.user, 'school') else None
        stats = {}
        
        if module_name == 'admissions':
            admissions_query = Admission.objects.all()
            if school:
                admissions_query = admissions_query.filter(school=school)
            stats = {
                'total': admissions_query.count(),
                'pending': admissions_query.filter(status='pending').count(),
                'approved': admissions_query.filter(status='approved').count(),
                'rejected': admissions_query.filter(status='rejected').count(),
            }
        
        elif module_name == 'fees':
            invoices_query = Invoice.objects.all()
            if school:
                invoices_query = invoices_query.filter(student__school=school)
            stats = {
                'total': invoices_query.count(),
                'paid': invoices_query.filter(balance=0).count(),
                'pending': invoices_query.filter(balance__gt=0).count(),
            }
        
        elif module_name == 'attendance':
            today = datetime.now().date()
            attendance_query = Attendance.objects.filter(date=today)
            stats = {
                'present': attendance_query.filter(present=True).count(),
                'absent': attendance_query.filter(present=False).count(),
            }
        
        return JsonResponse({
            'success': True,
            'module': module_name,
            'stats': stats
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

