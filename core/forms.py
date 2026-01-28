from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSignupForm(SignupForm):
    """
    Custom signup form that allows re-signup with unverified emails.
    If a user exists with the same email but is not verified, allow updating their password.
    """
    
    def clean_email(self):
        """
        Allow signup with existing unverified email.
        If user is verified, raise error. If unverified, will update instead.
        """
        email = self.cleaned_data.get('email')
        
        if email:
            # Check if user already exists
            existing_user = User.objects.filter(email=email).first()
            
            if existing_user:
                # Check if user is verified
                if existing_user.is_active and existing_user.emailaddress_set.filter(verified=True).exists():
                    # User is verified, don't allow signup
                    raise forms.ValidationError(
                        "A user is already registered with this email address."
                    )
                # If unverified, allow re-signup (will update the existing user)
        
        return email
    
    def save(self, request):
        """
        Save signup, updating existing unverified users if needed.
        """
        email = self.cleaned_data.get('email')
        
        # Check if unverified user exists
        existing_user = User.objects.filter(email=email).first()
        
        if existing_user and not existing_user.is_active:
            # Update existing unverified user
            existing_user.email = email
            existing_user.set_password(self.cleaned_data['password1'])
            existing_user.username = email
            existing_user.save()
            
            # Return the updated user
            from allauth.account.models import EmailAddress
            # Mark old email addresses as unverified
            EmailAddress.objects.filter(user=existing_user).update(verified=False)
            
            # Create/update email address
            EmailAddress.objects.get_or_create(
                user=existing_user,
                email=email,
                defaults={'primary': True, 'verified': False}
            )
            
            return existing_user
        
        # Normal signup flow
        return super().save(request)
