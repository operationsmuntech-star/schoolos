from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSignupForm(forms.Form):
    """
    Custom signup form that allows re-signup with unverified emails.
    If a user exists with the same email but is not verified, allow updating their password.
    
    This form must NOT import SignupForm at the module level to avoid circular imports.
    """
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def clean_password2(self):
        """Verify passwords match."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        
        return password2
    
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
    
    def save(self, request=None):
        """
        Save signup, updating existing unverified users if needed.
        """
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password1')
        request = request or self.request
        
        # Check if unverified user exists
        existing_user = User.objects.filter(email=email).first()
        
        if existing_user and not existing_user.is_active:
            # Update existing unverified user
            existing_user.email = email
            existing_user.set_password(password)
            existing_user.username = email
            existing_user.save()
            
            # Update email address records
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
        
        # Create new user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        
        # Create email address record
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(
            user=user,
            email=email,
            primary=True,
            verified=False
        )
        
        return user
    
    def signup(self, request, user):
        """
        Called by allauth after user creation to perform post-signup actions.
        This is a required method for custom signup forms in django-allauth.
        """
        pass
