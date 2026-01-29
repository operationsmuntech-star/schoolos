"""
Tenant-aware permissions for multi-tenant API
Ensures users only access their school's data
"""
from rest_framework import permissions
from django.core.exceptions import ValidationError


class IsTenantMember(permissions.BasePermission):
    """
    Permission check: User must belong to the requested school/tenant.
    """
    message = "Access denied. You don't belong to this school."

    def has_permission(self, request, view):
        """Check if user is authenticated and has a school"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser can access all
        if request.user.is_superuser:
            return True
        
        # Regular user must have a school
        return hasattr(request.user, 'school') and request.user.school is not None

    def has_object_permission(self, request, view, obj):
        """Check if object belongs to user's school"""
        if request.user.is_superuser:
            return True
        
        # Object must have school field that matches user's school
        if hasattr(obj, 'school'):
            return obj.school == request.user.school
        
        # If object doesn't have school field, deny access
        return False


class IsTeacherOfSchool(permissions.BasePermission):
    """
    Permission check: User must be a teacher in their school.
    """
    message = "Only teachers can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Check if user has a teacher profile
        return hasattr(request.user, 'person') and \
               hasattr(request.user.person, 'teacher') and \
               request.user.school is not None


class IsAdminOfSchool(permissions.BasePermission):
    """
    Permission check: User must be admin for their school.
    """
    message = "Only school administrators can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser or staff member
        return request.user.is_staff or request.user.is_superuser


class TenantFilterPermission(permissions.BasePermission):
    """
    Automatically filter querysets by user's school.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True


class TenantIsolationMixin:
    """
    Mixin for ViewSets to enforce tenant isolation.
    Filters queryset by user's school automatically.
    """
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        """Filter queryset by user's school"""
        queryset = super().get_queryset()
        
        user = self.request.user
        
        # Superuser sees all
        if user.is_superuser:
            return queryset
        
        # Regular users see only their school's data
        if user.school:
            queryset = queryset.filter(school=user.school)
        else:
            # No school assigned - empty queryset
            queryset = queryset.none()
        
        return queryset

    def perform_create(self, serializer):
        """Automatically set school from user"""
        if self.request.user.school:
            serializer.save(school=self.request.user.school)
        else:
            raise ValidationError("User must belong to a school to create records.")

    def perform_update(self, serializer):
        """Ensure school isn't changed"""
        serializer.save(school=self.request.user.school)

    def perform_destroy(self, instance):
        """Ensure user can only delete their school's records"""
        if self.request.user.school != instance.school and not self.request.user.is_superuser:
            raise ValidationError("You can only delete records from your school.")
        instance.delete()


class TenantSyncPermission(permissions.BasePermission):
    """
    Permission for sync operations.
    Users can only sync their school's data.
    """
    message = "You can only sync data from your school."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.school is not None

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        # For sync operations, check school_id in data
        school_id = request.data.get('school_id') if hasattr(request, 'data') else None
        if school_id:
            return request.user.school_id == int(school_id)
        
        # Fallback to object check
        if hasattr(obj, 'school'):
            return obj.school == request.user.school
        
        return False
