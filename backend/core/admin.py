"""
Django admin configuration for core app
"""
from django.contrib import admin
from backend.core.models import School, Term, Class, Subject


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'country', 'county']
    search_fields = ['name', 'code']
    list_filter = ['country', 'created_at']
    ordering = ['name']


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['school', 'year', 'term', 'start_date', 'end_date', 'is_active']
    search_fields = ['school__name']
    list_filter = ['year', 'term', 'is_active']
    ordering = ['-year', 'term']


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['school', 'level', 'stream', 'form_teacher', 'capacity']
    search_fields = ['school__name', 'level']
    list_filter = ['school', 'level']
    ordering = ['school', 'level', 'stream']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['school', 'name', 'code', 'is_compulsory']
    search_fields = ['name', 'code']
    list_filter = ['school', 'is_compulsory']
    ordering = ['school', 'name']
