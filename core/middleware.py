"""
Custom middleware for MunTech application
Handles performance, caching, and culture-specific features
"""

from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


class PerformanceHeadersMiddleware(MiddlewareMixin):
    """
    Add performance and security headers to all responses
    """
    
    def process_response(self, request, response):
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Performance headers
        response['Cache-Control'] = 'public, max-age=3600'
        
        # Feature headers
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class CacheMiddleware(MiddlewareMixin):
    """
    Cache static data to improve performance
    """
    
    CACHE_TIMEOUT = 300  # 5 minutes
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Don't cache if user is not authenticated
        if not request.user.is_authenticated:
            return None
        
        # Don't cache POST/DELETE requests
        if request.method != 'GET':
            return None
        
        # Create cache key from user and path
        cache_key = f"page_{request.user.id}_{request.path}"
        
        # Check cache
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for {request.path}")
            return cached_response
        
        return None
    
    def process_response(self, request, response):
        # Cache only successful GET responses
        if request.method == 'GET' and response.status_code == 200:
            if request.user.is_authenticated:
                cache_key = f"page_{request.user.id}_{request.path}"
                cache.set(cache_key, response, self.CACHE_TIMEOUT)
        
        return response


class SchoolContextMiddleware(MiddlewareMixin):
    """
    Add school context to all requests for multi-tenancy
    """
    
    def process_request(self, request):
        # Add school to request context
        if hasattr(request.user, 'school'):
            request.school = request.user.school
        else:
            request.school = None
        
        # Add theme preference
        request.theme = request.COOKIES.get('theme', 'light')
        
        return None


class UserActivityMiddleware(MiddlewareMixin):
    """
    Track user activity for analytics (optional)
    """
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Update last activity timestamp
            cache.set(
                f"user_last_activity_{request.user.id}",
                True,
                timeout=3600  # 1 hour
            )
        return None


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Custom error handling for better user experience
    """
    
    def process_exception(self, request, exception):
        logger.error(f"Exception in {request.path}: {str(exception)}")
        return None


class ThemeDetectionMiddleware(MiddlewareMixin):
    """
    Detect and manage theme preferences
    """
    
    def process_request(self, request):
        # Get theme from cookie or default to system preference
        theme = request.COOKIES.get('theme')
        
        if not theme:
            # Check if user prefers dark mode
            prefer_dark = request.META.get('HTTP_SEC_CH_PREFERS_COLOR_SCHEME') == 'dark'
            theme = 'dark' if prefer_dark else 'light'
        
        request.theme = theme
        return None
    
    def process_response(self, request, response):
        # Set theme cookie
        if hasattr(request, 'theme'):
            response.set_cookie('theme', request.theme, max_age=31536000)  # 1 year
        return response
