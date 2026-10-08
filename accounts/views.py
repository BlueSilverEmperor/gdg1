from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from .forms import StudentRegistrationForm, StudentLoginForm

User = get_user_model()


def register_view(request):
    """
    Direct, instant student registration using college email validation (.edu, .ac.in).
    Hashes password via set_password, sets is_active=True, and signs in immediately via login().
    Speed target: executes in under 100ms with zero SMTP TLS network delays.
    """
    if request.user.is_authenticated:
        return redirect('marketplace:listing_list')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = True
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome to Campus Marketplace, {user.first_name or user.username}!")
            return redirect('marketplace:listing_list')
        else:
            messages.error(request, "Please correct the errors below to complete registration.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Handle student user authentication with standard Django session authentication.
    """
    if request.user.is_authenticated:
        return redirect('marketplace:listing_list')

    if request.method == 'POST':
        form = StudentLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('marketplace:listing_list')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = StudentLoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """
    Log out the authenticated user and redirect to login page.
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f"Goodbye, {username}. You have been logged out.")
    return redirect('accounts:login')
