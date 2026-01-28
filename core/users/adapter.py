from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom adapter to ensure username is always set to email"""
    
    def save_user(self, request, sociallogin=None):
        """Override to set username = email"""
        user = super().save_user(request, sociallogin)
        
        # Ensure username is set to email if not already set
        if not user.username or user.username.strip() == '':
            user.username = user.email
            user.save()
        
        return user
    
    def populate_user(self, request, sociallogin, data):
        """Populate user data from sociallogin/data"""
        user = super().populate_user(request, sociallogin, data)
        
        # Ensure username is set to email
        if not user.username or user.username.strip() == '':
            user.username = user.email
        
        return user
