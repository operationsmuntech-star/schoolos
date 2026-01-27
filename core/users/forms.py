from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db import transaction
from .models import CustomUser, Student, Teacher, School

class SchoolSignUpForm(UserCreationForm):
    """
    SaaS Onboarding Form: Creates a School AND an Admin User.
    """
    school_name = forms.CharField(max_length=200, help_text="Name of your school")
    school_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    email = forms.EmailField(required=True, help_text="This will be the school admin login")
    
    class Meta:
        model = CustomUser
        fields = ('school_name', 'school_address', 'email', 'first_name', 'last_name')

    @transaction.atomic
    def save(self, commit=True):
        # 1. Create the User first (but don't commit yet if we need to link)
        user = super().save(commit=False)
        user.role = 'admin'  # The person registering is always the School Admin
        user.username = user.email  # Use email as username since we use Email Auth
        
        if commit:
            # 2. Create the School
            school_name = self.cleaned_data['school_name']
            school_address = self.cleaned_data['school_address']
            school = School.objects.create(name=school_name, address=school_address)
            
            # 3. Link User to School
            user.school = school
            user.save()
            
        return user

class CustomAuthenticationForm(AuthenticationForm):
    """Log in using Email instead of Username"""
    username = forms.EmailField(label='Email Address', widget=forms.TextInput(attrs={'autofocus': True}))

# Keep your other forms
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('registration_number', 'date_of_birth', 'grade')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ('employee_id', 'subject', 'qualification')