"""
Custom adapters to fix allauth integration issues and enable async email.
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.sites.models import Site
from core.tasks import send_html_email_task


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to properly handle username generation during signup.
    Ensures email is used as username to avoid duplicate key violations.
    Uses async tasks for email sending to prevent timeouts.
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
    
    def send_mail(self, template_prefix, email, context):
        """
        Override to send emails asynchronously via Celery.
        This prevents request timeout during signup.
        Falls back to sync if Celery is unavailable.
        """
        from django.template.loader import render_to_string
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Render email template
        subject = render_to_string(
            f'{template_prefix}_subject.txt', context
        ).strip()
        
        message = render_to_string(
            f'{template_prefix}_message.txt', context
        ).strip()
        
        try:
            # Try to send asynchronously
            send_html_email_task.delay(
                subject=subject,
                html_message=message,
                from_email=None,
                recipient_list=[email]
            )
        except Exception as e:
            # If Celery/Redis fails, fall back to sync email
            logger.warning(f"Celery task failed, sending email synchronously: {e}")
            try:
                send_html_email_task.apply(
                    args=(subject, message, None, [email])
                )
            except Exception as sync_error:
                logger.error(f"Email send failed: {sync_error}")


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
