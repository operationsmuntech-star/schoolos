"""
Core models for MunTech School Infrastructure
School, Term, Class, Subject - Phase 0 skeleton
"""
from django.db import models


class School(models.Model):
    """Root school entity"""
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    country = models.CharField(max_length=100, default='Kenya')
    county = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Schools'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Term(models.Model):
    """Academic term/semester"""
    TERM_CHOICES = [('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3')]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='terms')
    year = models.IntegerField()
    term = models.CharField(max_length=1, choices=TERM_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['school', 'year', 'term']
        ordering = ['-year', 'term']

    def __str__(self):
        return f"{self.school.code} - {self.year} Term {self.term}"


class Class(models.Model):
    """School class/stream"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes')
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=50)  # Form 1, Form 2, etc.
    stream = models.CharField(max_length=50, blank=True)  # A, B, C streams
    capacity = models.IntegerField(default=50)
    form_teacher = models.ForeignKey('people.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Classes'
        unique_together = ['school', 'level', 'stream']
        ordering = ['level', 'stream']

    def __str__(self):
        return f"{self.school.code} - {self.level} {self.stream or 'Main'}"


class Subject(models.Model):
    """School subject"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_compulsory = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['school', 'code']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"
