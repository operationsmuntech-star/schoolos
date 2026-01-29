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
    
    groups = models.ManyToManyField('auth.Group', related_name='custom_user_set', blank=True, help_text='The groups this user belongs to.')
    user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_user_set_perm', blank=True, help_text='Specific permissions for this user.')
    
    def __str__(self):
        return self.username
