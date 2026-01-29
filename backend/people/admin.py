"""
Django admin configuration for people app
"""
from django.contrib import admin
from backend.people.models import Person, Student, Teacher, Guardian, Staff


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'role', 'school', 'is_active']
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = ['role', 'school', 'is_active']
    ordering = ['first_name', 'last_name']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['person', 'admission_number', 'current_class']
    search_fields = ['admission_number', 'person__first_name', 'person__last_name']
    list_filter = ['current_class', 'person__school']
    ordering = ['admission_number']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['person', 'teacher_code', 'employment_date']
    search_fields = ['teacher_code', 'person__first_name', 'person__last_name']
    list_filter = ['person__school', 'employment_date']
    ordering = ['teacher_code']


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ['person', 'relationship']
    search_fields = ['person__first_name', 'person__last_name']
    list_filter = ['relationship']
    ordering = ['person__first_name']


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['person', 'staff_code', 'position', 'department']
    search_fields = ['staff_code', 'person__first_name', 'person__last_name']
    list_filter = ['position', 'department']
    ordering = ['staff_code']
