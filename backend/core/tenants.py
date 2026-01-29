"""
Multi-Tenant Infrastructure for School Management System
Provides tenant awareness across all models
"""
from django.db import models
from django.core.exceptions import ValidationError


class TenantMixin(models.Model):
    """
    Mixin for tenant-aware models.
    Every tenant-specific model should inherit from this.
    """
    school = models.ForeignKey(
        'core.School',
        on_delete=models.CASCADE,
        help_text="Tenant: School this record belongs to"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Ensure school is set before saving"""
        if not self.school_id:
            raise ValidationError("School must be specified for tenant-aware model")
        super().save(*args, **kwargs)


class TenantQuerySet(models.QuerySet):
    """
    QuerySet for filtering by tenant.
    Usage: Model.objects.for_school(school_obj).all()
    """
    def for_school(self, school):
        """Filter queryset by school (tenant)"""
        return self.filter(school=school)


class TenantManager(models.Manager):
    """
    Manager that provides tenant-aware querysets.
    """
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)

    def for_school(self, school):
        """Filter by school"""
        return self.get_queryset().for_school(school)


class TenantFilter:
    """
    Django admin filter for tenant.
    Shows list of schools to filter by.
    """
    title = 'School'
    parameter_name = 'school'

    def lookups(self, request, model_admin):
        from core.models import School
        return [(school.id, school.name) for school in School.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(school_id=self.value())
        return queryset


class TenantPermissionMixin:
    """
    Mixin for viewsets to enforce tenant permissions.
    """
    def get_queryset(self):
        """Filter queryset by school from request user"""
        queryset = super().get_queryset()
        
        school = self.request.user.school
        if school:
            queryset = queryset.filter(school=school)
        else:
            # Superuser can see all
            if not self.request.user.is_superuser:
                queryset = queryset.none()
        
        return queryset

    def perform_create(self, serializer):
        """Automatically set school from request user"""
        serializer.save(school=self.request.user.school)


class TenantMiddleware:
    """
    Middleware to attach tenant information to request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Attach school to request from user
        if request.user.is_authenticated:
            request.school = getattr(request.user, 'school', None)
        else:
            request.school = None

        response = self.get_response(request)
        return response
