"""
Sync models for offline-first data synchronization
Phase 0: Skeleton
"""
from django.db import models
import json


class SyncLog(models.Model):
    """Log of synchronization events"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('syncing', 'Syncing'),
        ('success', 'Success'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sync_logs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    data_type = models.CharField(max_length=50)  # 'attendance', 'students', etc.
    records_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.data_type} - {self.status}"


class SyncQueue(models.Model):
    """Queue of changes pending sync"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sync_queue')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    data_type = models.CharField(max_length=50)
    record_id = models.CharField(max_length=100)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    synced = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.action} {self.data_type} - {self.record_id}"
