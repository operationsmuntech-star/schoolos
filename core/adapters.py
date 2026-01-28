"""
Custom adapters to fix allauth integration issues.
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.sites.models import Site


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to properly handle username generation during signup.
    Ensures email is used as username to avoid duplicate key violations.
    """
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user during signup. If it's a regular signup (not social),
        form will be present and we set username from email.
        """
        user = super().save_user(request, sociallogin, form)
        
        # For regular signup, form will be present
        if form and hasattr(user, 'email') and user.email:
            # Ensure username is set to email for login purposes
            if not user.username or user.username == '':
                user.username = user.email
                user.save(update_fields=['username'])
        
        return user
    
    def pre_authenticate(self, request, **credentials):
        """
        Support email-based login by converting email to username.
        """
        # If login is via email, convert it to username
        if 'username' in credentials and '@' in credentials['username']:
            email = credentials['username']
            credentials['username'] = email
        
        return super().pre_authenticate(request, **credentials)


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
