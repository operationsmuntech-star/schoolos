from django.db import models
from django.utils import timezone
from core.users.models import Student, School

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
        ('leave', 'Leave'),
    )
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='attendance_records', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attendance'
        unique_together = ('student', 'date')
    
    def __str__(self):
        return f'{self.student} - {self.date} ({self.status})'

class AttendanceReport(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='attendance_reports', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    month = models.DateField()
    present_count = models.IntegerField(default=0)
    absent_count = models.IntegerField(default=0)
    total_days = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'attendance_reports'
        unique_together = ('student', 'month')
