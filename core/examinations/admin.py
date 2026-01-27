from django.contrib import admin
from .models import Marks

@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'exam_type', 'marks_obtained', 'percentage']
    list_filter = ['subject', 'exam_type', 'date']
    search_fields = ['student__user__first_name']
