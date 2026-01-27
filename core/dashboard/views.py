from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.users.models import Student, Teacher
from core.attendance.models import Attendance

@login_required
def index(request):
    context = {
        'total_students': Student.objects.count(),
        'total_teachers': Teacher.objects.count(),
    }
    return render(request, 'dashboard/index.html', context)

@login_required
def stats_api(request):
    students = Student.objects.count()
    teachers = Teacher.objects.count()
    attendance_data = [100, 20, 10]
    finance_data = [1500, 2300, 3200, 4500, 1200, 5000, 3800]
    
    return JsonResponse({
        'counts': {'students': students, 'teachers': teachers},
        'attendance': attendance_data,
        'finance': finance_data,
    })
