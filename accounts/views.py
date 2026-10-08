from urllib.parse import urlencode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from .forms import (
    StudentRegistrationForm,
    StudentLoginForm,
    ForgotPasswordRequestForm,
    ResetPasswordForm,
)

User = get_user_model()


@never_cache
def register_view(request):
    """
    Handle student account registration with zero-latency campus authentication.
    Creates user, activates account immediately, logs in, and redirects straight to catalog.
    """
    if request.user.is_authenticated:
        return redirect('marketplace:listing_list')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = True
            user.is_verified = True
            if hasattr(user, 'profile'):
                user.profile.is_verified = True
            user.save()

            # Direct session login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome to Campus Marketplace, {user.username}! Your account is active.")
            return redirect('marketplace:listing_list')
        else:
            messages.error(request, "Please correct the errors below to register.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@never_cache
def login_view(request):
    """
    Handle student user authentication with standard session login.
    """
    if request.user.is_authenticated:
        return redirect('marketplace:listing_list')

    if request.method == 'POST':
        form = StudentLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
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


@never_cache
def forgot_password_view(request):
    """
    Handle forgot password request by email.
    Verifies user registration and forwards to password reset form.
    """
    if request.user.is_authenticated:
        return redirect('marketplace:listing_list')

    if request.method == 'POST':
        form = ForgotPasswordRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email__iexact=email).first()

            if user:
                request.session['reset_email'] = user.email
                query_params = urlencode({'email': user.email})
                return redirect(f"{reverse('accounts:reset_password')}?{query_params}")
            else:
                messages.info(
                    request,
                    f"If an account with {email} is registered, you can proceed to update your password."
                )
                request.session['reset_email'] = email
                query_params = urlencode({'email': email})
                return redirect(f"{reverse('accounts:reset_password')}?{query_params}")
    else:
        initial_email = request.GET.get('email') or request.session.get('reset_email', '')
        form = ForgotPasswordRequestForm(initial={'email': initial_email} if initial_email else None)

    return render(request, 'accounts/forgot_password.html', {'form': form})


@never_cache
def reset_password_view(request):
    """
    Set a new password directly with password complexity validation.
    """
    if request.user.is_authenticated:
        return redirect('marketplace:listing_list')

    email = request.GET.get('email') or request.POST.get('email') or request.session.get('reset_email', '')
    email = email.strip()

    user = None
    if email:
        user = User.objects.filter(email__iexact=email).first()

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST, user=user)
        if not user:
            form.add_error(None, "No registered account found for this email address. Please start the reset process again.")
        elif form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.is_active = True
            user.is_verified = True
            user.save()

            request.session.pop('reset_email', None)
            messages.success(
                request,
                "Your password has been successfully updated! Please log in with your new password."
            )
            return redirect('accounts:login')
    else:
        form = ResetPasswordForm(user=user)

    return render(request, 'accounts/reset_password.html', {
        'form': form,
        'email': email,
        'user_obj': user,
    })
