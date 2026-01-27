from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify

class School(models.Model):
    """The Tenant Model: Every user and student belongs to a School"""
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True, help_text="URL friendly name (e.g. joyland-school)")
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'schools'
        verbose_name = 'School'
        verbose_name_plural = 'Schools'
        ordering = ['name']
    
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
