"""
Custom adapter to fix MultipleObjectsReturned error in allauth.
This handles the case where get_app() fails due to database issues.
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.sites.models import Site


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter that safely gets the social app without raising
    MultipleObjectsReturned errors.
    """
    
    def get_app(self, request, provider):
        """
        Safely get the social app for a provider.
        If MultipleObjectsReturned occurs, return the first one.
        """
        try:
            # Try the standard method first
            return super().get_app(request, provider)
        except Exception as e:
            # If there's any error, try a direct query
            from allauth.socialaccount.models import SocialApp
            from django.core.exceptions import ObjectDoesNotExist
            
            try:
                site = Site.objects.get_current()
                # Get app for current site
                app = SocialApp.objects.filter(
                    provider=provider,
                    sites=site
                ).first()
                
                if app:
                    return app
                
                # If not found for current site, try without site filter
                app = SocialApp.objects.filter(provider=provider).first()
                if app:
                    return app
                
                # If still not found, raise the original error
                raise ObjectDoesNotExist(f"SocialApp for provider '{provider}' not found")
            except Exception:
                raise e
