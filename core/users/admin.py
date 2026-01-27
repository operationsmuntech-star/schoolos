from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Student, Teacher, School

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('School Details', {'fields': ('name', 'slug', 'address', 'is_active')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at',)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('School Info', {'fields': ('school', 'role', 'phone', 'is_verified')}),
    )
    list_display = ['username', 'email', 'get_full_name', 'role', 'school', 'is_staff']
    list_filter = ['school', 'role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'school__name']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['registration_number', 'get_user_name', 'school', 'grade', 'enrollment_date', 'is_active']
    list_filter = ['school', 'grade', 'is_active', 'enrollment_date']
    search_fields = ['user__first_name', 'user__last_name', 'registration_number', 'school__name']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()
    get_user_name.short_description = 'Name'

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_user_name', 'school', 'subject', 'hire_date', 'is_active']
    list_filter = ['school', 'subject', 'is_active', 'hire_date']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id', 'school__name']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()
    get_user_name.short_description = 'Name'
