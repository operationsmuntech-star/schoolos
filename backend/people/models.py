"""
People models: Student, Teacher, Guardian, Staff
Phase 0: Skeleton models
"""
from django.db import models
from backend.people.roles import ROLES


class Person(models.Model):
    """Base person class"""
    ROLE_CHOICES = [(v, k) for k, v in ROLES.items()]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    id_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    school = models.ForeignKey('core.School', on_delete=models.CASCADE, related_name='%(class)s_people')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'People'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Student(models.Model):
    """Student entity"""
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='student')
    admission_number = models.CharField(max_length=50, unique=True)
    current_class = models.ForeignKey('core.Class', on_delete=models.SET_NULL, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.person.full_name} ({self.admission_number})"


class Teacher(models.Model):
    """Teacher entity"""
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='teacher')
    teacher_code = models.CharField(max_length=50, unique=True)
    subjects = models.ManyToManyField('core.Subject', related_name='teachers')
    qualifications = models.TextField(blank=True)
    employment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.person.full_name} ({self.teacher_code})"


class Guardian(models.Model):
    """Guardian/Parent entity"""
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='guardian')
    relationship = models.CharField(max_length=50)  # Parent, Guardian, etc.
    students = models.ManyToManyField(Student, related_name='guardians')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.person.full_name} ({self.relationship})"


class Staff(models.Model):
    """Staff member entity"""
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='staff')
    staff_code = models.CharField(max_length=50, unique=True)
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Staff'

    def __str__(self):
        return f"{self.person.full_name} ({self.position})"
