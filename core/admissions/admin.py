from django.contrib import admin
from .models import Admission

@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'grade', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']
