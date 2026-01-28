from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, School


class SchoolDirectorSignUpForm(UserCreationForm):
    """
    Director/Admin Signup: Creates School Director account
    Next step: Directs to School Setup Form
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email (will be your login)',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your first name',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your last name',
            'autocomplete': 'family-name'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact number (e.g., +233XXXXXXXXX)',
            'autocomplete': 'tel'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'autocomplete': 'new-password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'  # Director is admin of their school
        user.username = user.email
        user.is_verified = False  # Mark as unverified until school setup complete
        
        if commit:
            user.save()
        return user


class SchoolSetupForm(forms.ModelForm):
    """
    Comprehensive School Configuration Form
    Completed by directors after signup
    """
    
    SCHOOL_TYPE_CHOICES = (
        ('primary', 'Primary School'),
        ('secondary', 'Secondary School'),
        ('combined', 'Combined (Primary + Secondary)'),
        ('tertiary', 'Tertiary/Higher Education'),
    )
    
    COUNTRY_CHOICES = (
        ('GH', 'Ghana'),
        ('NG', 'Nigeria'),
        ('KE', 'Kenya'),
        ('ZA', 'South Africa'),
        ('TZ', 'Tanzania'),
        ('UG', 'Uganda'),
        ('CM', 'Cameroon'),
        ('CI', 'Côte d\'Ivoire'),
        ('SN', 'Senegal'),
        ('BJ', 'Benin'),
        ('BW', 'Botswana'),
        ('ET', 'Ethiopia'),
        ('GM', 'Gambia'),
        ('GN', 'Guinea'),
        ('LR', 'Liberia'),
        ('MW', 'Malawi'),
        ('ML', 'Mali'),
        ('MZ', 'Mozambique'),
        ('RW', 'Rwanda'),
        ('SL', 'Sierra Leone'),
        ('SO', 'Somalia'),
        ('SS', 'South Sudan'),
        ('SD', 'Sudan'),
        ('SZ', 'Eswatini'),
        ('TG', 'Togo'),
        ('ZM', 'Zambia'),
        ('ZW', 'Zimbabwe'),
    )
    
    ACADEMIC_CALENDAR_CHOICES = (
        ('January - December', 'January - December'),
        ('September - August', 'September - August'),
        ('April - March', 'April - March'),
        ('Custom', 'Custom (Will set later)'),
    )
    
    school_type = forms.ChoiceField(
        choices=SCHOOL_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="What type of school is this?",
        help_text="Select the educational level/type"
    )
    
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Country",
        help_text="Where is your school located?"
    )
    
    academic_calendar = forms.ChoiceField(
        choices=ACADEMIC_CALENDAR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Academic Calendar Year",
        help_text="When does your academic year start and end?"
    )
    
    currency = forms.CharField(
        max_length=3,
        initial='GHS',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., GHS, NGN, KES, ZAR',
            'autocomplete': 'off'
        }),
        label="Currency Code",
        help_text="Currency code for school fees (ISO 4217)"
    )
    
    class Meta:
        model = School
        fields = [
            'name', 'address', 'phone', 'email',
            'school_type', 'country', 'city', 'motto',
            'founded_year', 'student_population', 'teacher_count',
            'class_count', 'has_library', 'has_laboratory',
            'has_sports', 'has_computer_lab', 'academic_calendar', 'currency'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full School Name',
                'required': True,
                'autocomplete': 'organization'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Full School Address',
                'rows': 3,
                'autocomplete': 'street-address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number (e.g., +233XXXXXXXXX)',
                'autocomplete': 'tel'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'School Email Address',
                'autocomplete': 'email'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City/Town',
                'autocomplete': 'address-level2'
            }),
            'motto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'School Motto (optional)'
            }),
            'founded_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Year Founded (e.g., 2010)',
                'min': 1800,
                'max': 2100
            }),
            'student_population': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Total Number of Students',
                'min': 0
            }),
            'teacher_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of Teachers',
                'min': 0
            }),
            'class_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of Classes/Grades',
                'min': 0
            }),
            'has_library': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_laboratory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_sports': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_computer_lab': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'School Name *',
            'address': 'School Address *',
            'phone': 'Contact Phone *',
            'email': 'Contact Email *',
            'city': 'City/Town *',
            'motto': 'School Motto',
            'founded_year': 'Year Founded',
            'student_population': 'Total Students *',
            'teacher_count': 'Number of Teachers *',
            'class_count': 'Number of Classes/Grades *',
            'has_library': 'Has Library',
            'has_laboratory': 'Has Science Laboratory',
            'has_sports': 'Has Sports Facilities',
            'has_computer_lab': 'Has Computer Lab',
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if School.objects.filter(name=name).exists():
            raise forms.ValidationError("This school name is already registered. Please use a different name.")
        return name


class CustomAuthenticationForm(AuthenticationForm):
    """Log in using Email instead of Username"""
    username = forms.EmailField(
        label='Email Address',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autofocus': True,
            'autocomplete': 'email'
        })
    )
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )


class SchoolUserForm(forms.ModelForm):
    """Form for adding users to a school"""
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }


class SchoolUpdateForm(forms.ModelForm):
    """Form for updating school details after initial setup"""
    class Meta:
        model = School
        fields = [
            'name', 'address', 'phone', 'email', 'city', 'motto',
            'student_population', 'teacher_count', 'class_count',
            'has_library', 'has_laboratory', 'has_sports', 'has_computer_lab'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'disabled': True}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'motto': forms.TextInput(attrs={'class': 'form-control'}),
            'student_population': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'teacher_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'class_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'has_library': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_laboratory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_sports': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_computer_lab': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }