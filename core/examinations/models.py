from django.db import models
from core.users.models import Student, School

class Marks(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='marks', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    subject = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=100)
    marks_obtained = models.FloatField()
    total_marks = models.FloatField(default=100)
    percentage = models.FloatField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'marks'
    
    def save(self, *args, **kwargs):
        self.percentage = (self.marks_obtained / self.total_marks) * 100
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.student} - {self.subject}: {self.marks_obtained}/{self.total_marks}'
