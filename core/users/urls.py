from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Director Onboarding Flow
    path('director/signup/', views.director_signup, name='director_signup'),
    path('director/school-setup/', views.school_setup, name='school_setup'),
    path('director/setup-success/', views.setup_success, name='setup_success'),
    
    # User Management
    path('profile/', views.profile, name='profile'),
    path('school-profile/', views.school_profile, name='school_profile'),
]