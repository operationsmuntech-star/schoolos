from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register-school/', views.register_school, name='register_school'),
    path('profile/', views.profile, name='profile'),
]