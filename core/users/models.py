from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
import json

class School(models.Model):
    """The Tenant Model: Every user and student belongs to a School"""
    
    SCHOOL_TYPE_CHOICES = (
        ('primary', 'Primary School'),
        ('secondary', 'Secondary School'),
        ('combined', 'Combined (Primary + Secondary)'),
        ('tertiary', 'Tertiary/Higher Education'),
    )
    
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True, help_text="URL friendly name (e.g. joyland-school)")
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # School Details
    school_type = models.CharField(max_length=50, choices=SCHOOL_TYPE_CHOICES, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    motto = models.CharField(max_length=200, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)
    
    # School Statistics
    student_population = models.IntegerField(default=0)
    teacher_count = models.IntegerField(default=0)
    class_count = models.IntegerField(default=0)
    
    # Facilities
    has_library = models.BooleanField(default=False)
    has_laboratory = models.BooleanField(default=False)
    has_sports = models.BooleanField(default=False)
    has_computer_lab = models.BooleanField(default=False)
    
    # Academic Settings
    academic_calendar = models.CharField(max_length=100, default="January - December")
    currency = models.CharField(max_length=3, default="GHS")
    
    # School Status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    setup_completed = models.BooleanField(default=False, help_text="Has director completed initial setup?")
    
    class Meta:
        db_table = 'schools'
        verbose_name = 'School'
        verbose_name_plural = 'Schools'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class CustomUser(AbstractUser):
    """Extended user model with school-specific fields"""
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE, 
        related_name='users',
        null=True,
        blank=True,
        help_text="The school this user belongs to. Null for superusers."
    )
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'

class Student(models.Model):
    """Student profile model"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student')
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='students',
        null=True,
        blank=True
    )
    registration_number = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=50, blank=True)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
    
    def __str__(self):
        return f'{self.user.get_full_name()} ({self.registration_number})'

class StudentClass(models.Model):
    """Class/Grade level in a school"""
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='classes'
    )
    name = models.CharField(max_length=50)  # e.g., "Form 1A", "Class 3", "Grade 10"
    level = models.CharField(max_length=50, blank=True)  # e.g., "Primary", "Secondary"
    capacity = models.IntegerField(default=40)
    class_teacher = models.ForeignKey(
        'Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes_teaching'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'student_classes'
        unique_together = ('school', 'name')
        ordering = ['level', 'name']
    
    def __str__(self):
        return f"{self.school.name} - {self.name}"


class Teacher(models.Model):
    """Teacher profile model"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher')
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='teachers',
        null=True,
        blank=True
    )
    employee_id = models.CharField(max_length=50, unique=True)
    subject = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'teachers'
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
    
    def __str__(self):
        return f'{self.user.get_full_name()} ({self.subject})'

class TeacherAssignment(models.Model):
    """Teacher assignment to specific classes and subjects"""
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    student_class = models.ForeignKey(
        StudentClass,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )
    subject = models.CharField(max_length=100)
    assigned_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'teacher_assignments'
        unique_together = ('teacher', 'student_class', 'subject')
        ordering = ['student_class', 'subject']
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.student_class.name} ({self.subject})"