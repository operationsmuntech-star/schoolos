from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q, F
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta

from core.users.models import Teacher, TeacherAssignment, StudentClass, Student
from core.attendance.models import Attendance
from core.examinations.models import Marks
import json


def teacher_required(view_func):
    """Decorator to restrict view to teachers only"""
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'teacher'):
            return redirect('account_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@teacher_required
def teacher_dashboard(request):
    """
    Teacher portal dashboard - shows assigned classes, quick actions, pending tasks
    """
    teacher = request.user.teacher
    
    # Get teacher's assigned classes
    assigned_classes = TeacherAssignment.objects.filter(
        teacher=teacher,
        is_active=True
    ).select_related('student_class').distinct('student_class')
    
    # Also get classes where teacher is class teacher
    class_teacher_classes = teacher.classes_teaching.filter(is_active=True)
    
    all_classes = StudentClass.objects.filter(
        Q(teacher_assignments__teacher=teacher, teacher_assignments__is_active=True) |
        Q(class_teacher=teacher)
    ).distinct()
    
    # Calculate stats
    total_students = Student.objects.filter(
        student_class__in=all_classes,
        is_active=True
    ).count()
    
    # Today's attendance
    today = timezone.now().date()
    attendance_recorded = Attendance.objects.filter(
        student__student_class__in=all_classes,
        date=today
    ).count()
    
    # Pending tasks
    pending_tasks = []
    
    # Check for ungraded exams (if exams assigned)
    ungraded_count = Marks.objects.filter(
        student__student_class__in=all_classes,
        marks__isnull=True
    ).count()
    
    if ungraded_count > 0:
        pending_tasks.append({
            'title': f'{ungraded_count} Grades Pending',
            'action': 'Enter Grades',
            'url': '#'  # Will fill in
        })
    
    context = {
        'teacher': teacher,
        'assigned_classes': all_classes,
        'total_students': total_students,
        'total_classes': all_classes.count(),
        'attendance_recorded_today': attendance_recorded,
        'pending_tasks': pending_tasks,
    }
    
    return render(request, 'teacher/dashboard.html', context)


@login_required
@teacher_required
def attendance_marking(request):
    """
    Attendance marking interface - bulk mark students present/absent
    """
    teacher = request.user.teacher
    
    # Get teacher's classes
    classes = StudentClass.objects.filter(
        Q(teacher_assignments__teacher=teacher, teacher_assignments__is_active=True) |
        Q(class_teacher=teacher)
    ).distinct()
    
    selected_class_id = request.GET.get('class_id')
    selected_class = None
    students = []
    today_attendance = {}
    
    if selected_class_id:
        try:
            selected_class = classes.get(id=selected_class_id)
            students = Student.objects.filter(
                student_class=selected_class,
                is_active=True
            ).select_related('user').order_by('user__first_name', 'user__last_name')
            
            # Get today's attendance
            today = timezone.now().date()
            attendance_records = Attendance.objects.filter(
                student__in=students,
                date=today
            )
            today_attendance = {att.student_id: att.present for att in attendance_records}
        except StudentClass.DoesNotExist:
            pass
    
    context = {
        'classes': classes,
        'selected_class': selected_class,
        'students': students,
        'today_attendance': today_attendance,
        'today': timezone.now().date(),
    }
    
    return render(request, 'teacher/attendance.html', context)


@login_required
@teacher_required
@require_http_methods(["POST"])
def save_attendance(request):
    """
    Save attendance records via AJAX
    """
    teacher = request.user.teacher
    data = json.loads(request.body)
    
    class_id = data.get('class_id')
    attendance_data = data.get('attendance', {})  # {student_id: bool}
    
    # Verify teacher can access this class
    classes = StudentClass.objects.filter(
        Q(teacher_assignments__teacher=teacher, teacher_assignments__is_active=True) |
        Q(class_teacher=teacher)
    )
    
    student_class = get_object_or_404(classes, id=class_id)
    today = timezone.now().date()
    
    saved_count = 0
    try:
        for student_id, present in attendance_data.items():
            student = Student.objects.get(
                id=student_id,
                student_class=student_class,
                is_active=True
            )
            
            # Create or update attendance
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                date=today,
                defaults={'present': bool(present)}
            )
            saved_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Attendance for {saved_count} students recorded',
            'count': saved_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving attendance: {str(e)}'
        }, status=400)


@login_required
@teacher_required
def grade_entry(request):
    """
    Grade entry interface - enter marks for students
    """
    teacher = request.user.teacher
    
    # Get exams assigned to teacher's classes
    classes = StudentClass.objects.filter(
        Q(teacher_assignments__teacher=teacher, teacher_assignments__is_active=True) |
        Q(class_teacher=teacher)
    ).distinct()
    
    # Get exams for these classes
    exams = Exam.objects.filter(
        student_class__in=classes
    ).distinct()
    
    selected_exam_id = request.GET.get('exam_id')
    selected_exam = None
    students = []
    existing_marks = {}
    
    if selected_exam_id:
        try:
            selected_exam = exams.get(id=selected_exam_id)
            students = Student.objects.filter(
                student_class=selected_exam.student_class,
                is_active=True
            ).select_related('user').order_by('user__first_name', 'user__last_name')
            
            # Get existing marks
            existing_marks_qs = Marks.objects.filter(
                exam=selected_exam,
                student__in=students
            )
            existing_marks = {m.student_id: m.marks for m in existing_marks_qs}
        except Exam.DoesNotExist:
            pass
    
    context = {
        'exams': exams,
        'selected_exam': selected_exam,
        'students': students,
        'existing_marks': existing_marks,
    }
    
    return render(request, 'teacher/grades.html', context)


@login_required
@teacher_required
@require_http_methods(["POST"])
def save_grades(request):
    """
    Save grade marks via AJAX
    """
    teacher = request.user.teacher
    data = json.loads(request.body)
    
    exam_id = data.get('exam_id')
    grades_data = data.get('grades', {})  # {student_id: marks}
    
    # Verify exam is assigned to teacher's class
    classes = StudentClass.objects.filter(
        Q(teacher_assignments__teacher=teacher, teacher_assignments__is_active=True) |
        Q(class_teacher=teacher)
    )
    
    exam = get_object_or_404(Exam, id=exam_id, student_class__in=classes)
    
    saved_count = 0
    errors = []
    
    try:
        for student_id, marks_value in grades_data.items():
            try:
                student = Student.objects.get(
                    id=student_id,
                    student_class=exam.student_class,
                    is_active=True
                )
                
                # Validate marks
                try:
                    marks = float(marks_value) if marks_value else None
                    
                    if marks is not None and (marks < 0 or marks > 100):
                        errors.append(f"{student.user.get_full_name()}: Marks must be 0-100")
                        continue
                    
                    # Create or update marks
                    mark_obj, created = Marks.objects.update_or_create(
                        exam=exam,
                        student=student,
                        defaults={'marks': marks}
                    )
                    saved_count += 1
                except ValueError:
                    errors.append(f"{student.user.get_full_name()}: Invalid marks value")
                    
            except Student.DoesNotExist:
                errors.append(f"Student {student_id} not found")
        
        return JsonResponse({
            'success': True,
            'message': f'Grades for {saved_count} students saved',
            'count': saved_count,
            'errors': errors if errors else None
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving grades: {str(e)}'
        }, status=400)


@login_required
@teacher_required
def report_card(request, student_id):
    """
    Generate report card for a student
    """
    teacher = request.user.teacher
    
    # Verify teacher can access this student
    classes = StudentClass.objects.filter(
        Q(teacher_assignments__teacher=teacher, teacher_assignments__is_active=True) |
        Q(class_teacher=teacher)
    )
    
    student = get_object_or_404(
        Student,
        id=student_id,
        student_class__in=classes,
        is_active=True
    )
    
    # Get student's marks
    marks = Marks.objects.filter(student=student).select_related(
        'exam__subject'
    )
    
    # Get attendance
    attendance = Attendance.objects.filter(student=student)
    total_days = attendance.count()
    present_days = attendance.filter(present=True).count()
    attendance_percentage = round((present_days / total_days * 100) if total_days > 0 else 0)
    
    context = {
        'student': student,
        'marks': marks,
        'attendance_percentage': attendance_percentage,
        'present_days': present_days,
        'total_days': total_days,
    }
    
    return render(request, 'teacher/report-card.html', context)
