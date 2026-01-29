"""
User authentication models
Phase 0: Skeleton
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user model"""
    person = models.OneToOneField('people.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='user')
    school = models.ForeignKey('core.School', on_delete=models.SET_NULL, null=True, blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username
