"""
Attendance models - Phase 1
Complete attendance tracking with offline-first support
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class AttendanceSession(models.Model):
    """Attendance session for a class on a specific date"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('synced', 'Synced'),
    ]
    
    school = models.ForeignKey('core.School', on_delete=models.CASCADE, related_name='attendance_sessions')
    klass = models.ForeignKey('core.Class', on_delete=models.CASCADE, related_name='attendance_sessions')
    term = models.ForeignKey('core.Term', on_delete=models.SET_NULL, null=True, related_name='attendance_sessions')
    date = models.DateField()
    subject = models.ForeignKey('core.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey('people.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Metadata for sync
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Offline-first tracking
    synced = models.BooleanField(default=False)
    local_id = models.CharField(max_length=100, null=True, blank=True, help_text='UUID for offline sync')
    
    class Meta:
        unique_together = [('school', 'klass', 'date', 'subject')]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date', 'school']),
            models.Index(fields=['status', 'school']),
        ]
    
    def __str__(self):
        return f"{self.klass} - {self.date} ({self.get_status_display()})"
    
    def mark_closed(self):
        """Mark session as closed"""
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at'])
    
    def mark_synced(self):
        """Mark session as synced to server"""
        self.status = 'synced'
        self.synced = True
        self.synced_at = timezone.now()
        self.save(update_fields=['status', 'synced', 'synced_at'])
    
    def get_attendance_count(self, status=None):
        """Get count of attendance records with optional status filter"""
        qs = self.attendances.all()
        if status:
            qs = qs.filter(status=status)
        return qs.count()
    
    def get_attendance_percentage(self, status='P'):
        """Calculate attendance percentage for status"""
        total = self.attendances.count()
        if total == 0:
            return 0
        count = self.attendances.filter(status=status).count()
        return (count / total) * 100
    
    @property
    def total_students(self):
        return self.attendances.count()
    
    @property
    def present_count(self):
        return self.get_attendance_count('P')
    
    @property
    def absent_count(self):
        return self.get_attendance_count('A')


class Attendance(models.Model):
    """Individual attendance record"""
    PRESENT = 'P'
    ABSENT = 'A'
    LATE = 'L'
    EXCUSED = 'E'
    
    STATUS_CHOICES = [
        (PRESENT, 'Present'),
        (ABSENT, 'Absent'),
        (LATE, 'Late'),
        (EXCUSED, 'Excused'),
    ]
    
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey('people.Student', on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    
    # Metadata
    marked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    marked_by = models.ForeignKey('people.Teacher', on_delete=models.SET_NULL, null=True, blank=True, help_text='Teacher who marked attendance')
    
    # Offline-first tracking
    synced = models.BooleanField(default=False)
    local_id = models.CharField(max_length=100, null=True, blank=True, help_text='UUID for offline sync')
    last_sync_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['session', 'student']
        ordering = ['-marked_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['marked_at']),
            models.Index(fields=['synced']),
        ]
    
    def __str__(self):
        return f"{self.student} - {self.session.date} - {self.get_status_display()}"
    
    def mark_synced(self):
        """Mark record as synced to server"""
        self.synced = True
        self.last_sync_at = timezone.now()
        self.save(update_fields=['synced', 'last_sync_at'])
    
    def clean(self):
        """Validate attendance record"""
        if self.session.status == 'synced':
            raise ValidationError("Cannot modify attendance for synced session")
        if self.session.date > timezone.now().date():
            raise ValidationError("Cannot mark attendance for future dates")


class AttendanceException(models.Model):
    """Track excused absences, medical, family reasons, etc."""
    CATEGORY_CHOICES = [
        ('medical', 'Medical'),
        ('family', 'Family Event'),
        ('excused', 'Excused'),
        ('suspension', 'Suspension'),
        ('other', 'Other'),
    ]
    
    student = models.ForeignKey('people.Student', on_delete=models.CASCADE, related_name='attendance_exceptions')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    approved_by = models.ForeignKey('people.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.student} - {self.get_category_display()} ({self.start_date})"
    
    def covers_date(self, date):
        """Check if exception covers a specific date"""
        return self.start_date <= date <= self.end_date
