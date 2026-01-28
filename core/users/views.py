from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_http_methods
from .forms import SchoolDirectorSignUpForm, SchoolSetupForm
from .models import CustomUser, School


@require_http_methods(["GET", "POST"])
def director_signup(request):
    """
    Director signup view: Initial account creation for school directors
    On successful signup, redirects to school setup form
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = SchoolDirectorSignUpForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=True)
                # Log the user in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Account created successfully! Now let\'s set up your school.')
                return redirect('users:school_setup')
    else:
        form = SchoolDirectorSignUpForm()
    
    context = {
        'form': form,
        'page_title': 'Director Sign Up',
        'page_description': 'Create your director account to get started'
    }
    return render(request, 'account/director_signup.html', context)


@login_required(login_url='account_login')
@require_http_methods(["GET", "POST"])
def school_setup(request):
    """
    School setup form: Directors configure their school after signup
    Creates the School object and marks director's account as verified
    """
    # Check if user is a director
    if request.user.role != 'admin':
        messages.error(request, 'Only school directors can access this page.')
        return redirect('dashboard:index')
    
    # Check if user already has a verified school
    if request.user.school and request.user.school.setup_completed:
        messages.info(request, 'Your school setup is already complete!')
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = SchoolSetupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Create/update school
                school = form.save(commit=False)
                
                # If user already has a school, update it; otherwise create new
                if request.user.school:
                    # Update existing school
                    school.id = request.user.school.id
                    school.setup_completed = True
                    school.save()
                else:
                    # Create new school
                    school.setup_completed = True
                    school.save()
                    # Link user to school
                    request.user.school = school
                    request.user.is_verified = True
                    request.user.save()
                
                messages.success(
                    request,
                    f'Welcome to {school.name}! Your school setup is complete.'
                )
                return redirect('dashboard:index')
    else:
        # Pre-populate form if user already has a school
        if request.user.school:
            form = SchoolSetupForm(instance=request.user.school)
        else:
            form = SchoolSetupForm()
    
    context = {
        'form': form,
        'page_title': 'School Setup',
        'page_description': 'Configure your school details to get started',
        'step': 'setup'
    }
    return render(request, 'account/school_setup.html', context)


@login_required(login_url='account_login')
def setup_success(request):
    """
    Success page after school setup is complete
    Shows next steps for the director
    """
    if request.user.role != 'admin' or not request.user.school:
        return redirect('dashboard:index')
    
    school = request.user.school
    context = {
        'school': school,
        'page_title': 'Setup Complete',
    }
    return render(request, 'account/setup_success.html', context)


@login_required(login_url='account_login')
def school_profile(request):
    """
    School profile view: Directors can view/edit their school settings
    """
    if request.user.role != 'admin' or not request.user.school:
        messages.error(request, 'You do not have access to this page.')
        return redirect('dashboard:index')
    
    school = request.user.school
    context = {
        'school': school,
        'page_title': f'{school.name} Profile',
    }
    return render(request, 'users/school_profile.html', context)


@login_required(login_url='account_login')
def profile(request):
    """Director profile/account settings"""
    context = {
        'page_title': 'My Profile',
    }
    return render(request, 'users/profile.html', context)
