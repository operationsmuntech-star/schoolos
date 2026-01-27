from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SchoolSignUpForm

def register_school(request):
    """
    Public View: Allows a new Principal to register their school.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = SchoolSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Welcome! {user.school.name} has been created. Please log in.')
            return redirect('account_login') # Redirects to Allauth login
    else:
        form = SchoolSignUpForm()
    
    return render(request, 'users/register_school.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'users/profile.html')