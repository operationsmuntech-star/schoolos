from django.db import models
from core.users.models import Student, School

class Payment(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, default='completed')
    
    class Meta:
        db_table = 'payments'
    
    def __str__(self):
        return f'{self.student} - {self.amount} ({self.payment_date})'
