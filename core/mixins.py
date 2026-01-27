from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class SchoolContextMixin(LoginRequiredMixin):
    """
    Ensures the user belongs to a school and filters data automatically.
    All querysets will be filtered to only show data for the user's school.
    Superusers can see everything.
    """
    
    def get_queryset(self):
        """
        Filter queryset by user's school.
        Override this method in your views to add custom filtering.
        """
        qs = super().get_queryset()
        
        # Superusers (admin) can see everything
        if self.request.user.is_superuser:
            return qs
        
        # Check if user has a school assigned
        if not self.request.user.school:
            # User has no school assigned - show empty queryset
            return qs.none()
        
        # Filter by the user's school
        # This assumes the model has a 'school' field
        # If not, you may need to override this method in your view
        try:
            return qs.filter(school=self.request.user.school)
        except Exception:
            # If filtering by school fails, return empty queryset as fallback
            return qs.none()
    
    def get_context_data(self, **kwargs):
        """Add school context to all templates"""
        context = super().get_context_data(**kwargs)
        context['user_school'] = self.request.user.school
        return context
