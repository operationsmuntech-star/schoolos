from django.db import models
from core.users.models import Student, School

class Fee(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'), ('paid', 'Paid'), ('overdue', 'Overdue'))
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='fees', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fees'
    
    def __str__(self):
        return f'{self.student} - {self.amount} ({self.status})'
