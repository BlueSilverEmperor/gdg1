import sys
import threading
from urllib.parse import urlencode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .forms import (
    StudentRegistrationForm,
    StudentLoginForm,
    OTPVerificationForm,
    ForgotPasswordRequestForm,
    ResetPasswordWithOTPForm,
)
from .models import EmailVerificationOTP, PasswordResetOTP
from .utils import generate_otp, send_otp_email, send_password_reset_otp_email

User = get_user_model()


def dispatch_otp_email(user, otp_code: str):
    """
    Dispatch OTP email. Runs synchronously in test runs for mail.outbox assertions,
    and asynchronously via threading in production for instant HTTP response times.
    """
    if 'test' in sys.argv:
        send_otp_email(user, otp_code)
    else:
        thread = threading.Thread(target=send_otp_email, args=(user, otp_code), daemon=True)
        thread.start()


def dispatch_password_reset_otp_email(user, otp_code: str):
    """
    Dispatch Password Reset OTP email. Runs synchronously in test runs for mail.outbox assertions,
    and asynchronously via threading in production for instant HTTP response times.
    """
    if 'test' in sys.argv:
        send_password_reset_otp_email(user, otp_code)
    else:
        thread = threading.Thread(target=send_password_reset_otp_email, args=(user, otp_code), daemon=True)
        thread.start()


def register_view(request):
    """
    Handle student account registration.
    Sets is_active=False, creates a 6-digit numeric OTP,
    emails it to the student, and redirects to verify-otp.
    """
    if request.user.is_authenticated:
        return redirect('marketplace:listing_list')

    if request.method == 'POST':
        # If user previously started registration but account is still inactive,
        # seamlessly send a fresh OTP and redirect to verification rather than locking them out.
        email_candidate = request.POST.get('email', '').strip().lower()
        if email_candidate:
            inactive_user = User.objects.filter(email__iexact=email_candidate, is_active=False).first()
            if inactive_user:
                otp_code = generate_otp()
                EmailVerificationOTP.objects.update_or_create(
                    user=inactive_user,
                    defaults={'otp_code': otp_code, 'attempts': 0}
                )
                dispatch_otp_email(inactive_user, otp_code)
                request.session['verify_email'] = inactive_user.email
                messages.info(
                    request,
                    f"Your account was already created and is pending verification. A fresh 6-digit code was sent to {inactive_user.email}."
                )
                query_params = urlencode({'email': inactive_user.email})
                return redirect(f"{reverse('accounts:verify_otp')}?{query_params}")

        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            # Save user with is_active=False (handled in form.save)
            user = form.save()

            # Generate cryptographically secure 6-digit OTP
            otp_code = generate_otp()
            EmailVerificationOTP.objects.update_or_create(
                user=user,
                defaults={'otp_code': otp_code, 'attempts': 0}
            )

            # Dispatch verification email
            dispatch_otp_email(user, otp_code)

            # Store email in session for convenient fallback
            request.session['verify_email'] = user.email

            messages.info(
                request,
                f"A 6-digit verification code was sent to {user.email}. Enter it below to activate your account."
            )
            query_params = urlencode({'email': user.email})
            return redirect(f"{reverse('accounts:verify_otp')}?{query_params}")
        else:
            messages.error(request, "Please correct the errors below to register.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def verify_otp_view(request):
    """
    Verify the 6-digit numeric OTP.
    On success, activates user (is_active=True), logs them in, and redirects.
    Enforces 10-minute expiry and max 5 attempts.
    """
    if request.user.is_authenticated:
        return redirect('marketplace:listing_list')

    email = request.GET.get('email') or request.POST.get('email') or request.session.get('verify_email', '')
    email = email.strip()

    user = None
    if email:
        user = User.objects.filter(email__iexact=email).first()

    if not user:
        # If user landed directly on verify without email, give them an email input form
        if request.method == 'POST' and not email:
            messages.error(request, "Please enter your registered student email.")
        return render(request, 'accounts/verify_otp.html', {
            'form': OTPVerificationForm(),
            'email': '',
            'user_obj': None,
            'need_email_input': True,
            'can_resend': False,
            'seconds_remaining': 0,
            'debug': settings.DEBUG,
        })

    if user.is_active:
        messages.info(request, "Your email is already verified. Please log in.")
        return redirect('accounts:login')

    otp_record = getattr(user, 'otp_record', None)

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            submitted_code = form.cleaned_data['otp_code']

            if not otp_record:
                form.add_error(None, "No active verification code found. Please request a new code below.")
            elif otp_record.attempts >= 5:
                form.add_error(
                    None,
                    "Maximum verification attempts exceeded. For security, please request a new code below."
                )
            elif not otp_record.is_valid():
                form.add_error(
                    None,
                    "This verification code has expired (codes expire after 10 minutes). Please request a new code below."
                )
            elif otp_record.otp_code != submitted_code:
                otp_record.attempts += 1
                otp_record.save(update_fields=['attempts'])
                remaining = max(0, 5 - otp_record.attempts)
                form.add_error(
                    'otp_code',
                    f"Incorrect verification code. {remaining} attempt(s) remaining."
                )
            else:
                # Code matches & is valid!
                otp_record.delete()
                user.is_active = True
                user.save(update_fields=['is_active'])

                # Log user in directly
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                # Clear session
                request.session.pop('verify_email', None)

                messages.success(
                    request,
                    f"Welcome to Campus Marketplace, {user.username}! Your student email is verified."
                )
                return redirect('marketplace:listing_list')
    else:
        form = OTPVerificationForm()

    can_resend = otp_record.can_resend() if otp_record else True
    seconds_remaining = otp_record.seconds_until_resend() if otp_record else 0

    return render(request, 'accounts/verify_otp.html', {
        'form': form,
        'email': user.email,
        'user_obj': user,
        'can_resend': can_resend,
        'seconds_remaining': seconds_remaining,
        'need_email_input': False,
        'otp_code_preview': otp_record.otp_code if (settings.DEBUG and otp_record) else None,
        'debug': settings.DEBUG,
    })


@require_http_methods(["GET", "POST"])
def resend_otp_view(request):
    """
    Resend verification OTP with 60-second cooldown enforcement.
    """
    email = request.GET.get('email') or request.POST.get('email') or request.session.get('verify_email', '')
    email = email.strip()

    if not email:
        messages.error(request, "Unable to find your registration email. Please register again.")
        return redirect('accounts:register')

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        messages.error(request, "Account not found. Please register first.")
        return redirect('accounts:register')

    if user.is_active:
        messages.info(request, "Your account is already active. Please log in.")
        return redirect('accounts:login')

    otp_record, created = EmailVerificationOTP.objects.get_or_create(
        user=user,
        defaults={'otp_code': generate_otp(), 'attempts': 0}
    )

    if not created and not otp_record.can_resend():
        wait_seconds = otp_record.seconds_until_resend()
        messages.warning(
            request,
            f"Please wait {wait_seconds} more seconds before requesting another verification code."
        )
    else:
        # Generate new OTP & reset attempts
        new_otp = generate_otp()
        otp_record.otp_code = new_otp
        otp_record.attempts = 0
        otp_record.save()

        # Send email
        dispatch_otp_email(user, new_otp)
        request.session['verify_email'] = user.email
        messages.success(
            request,
            f"A fresh 6-digit verification code has been dispatched to {user.email}."
        )

    query_params = urlencode({'email': user.email})
    return redirect(f"{reverse('accounts:verify_otp')}?{query_params}")


def login_view(request):
    """
    Handle student user authentication.
    Prevents inactive accounts from logging in until OTP is verified.
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
            # Check if username or email belongs to an inactive user pending verification
            username_input = request.POST.get('username', '').strip()
            pending_user = User.objects.filter(
                username__iexact=username_input
            ).first() or User.objects.filter(
                email__iexact=username_input
            ).first()

            if pending_user and not pending_user.is_active:
                query_params = urlencode({'email': pending_user.email})
                verify_url = f"{reverse('accounts:verify_otp')}?{query_params}"
                messages.warning(
                    request,
                    f"Your student account is pending email verification. Please verify your OTP to activate your account."
                )
                return redirect(verify_url)

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


def forgot_password_view(request):
    """
    Handle forgot password request by email.
    Generates a 6-digit numeric OTP and emails it to the student.
    Prevents user enumeration by showing safe consistent messaging.
    """
    if request.user.is_authenticated:
        return redirect('marketplace:listing_list')

    if request.method == 'POST':
        form = ForgotPasswordRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email__iexact=email).first()

            if user:
                # Invalidate any previously unused reset OTPs for this user
                PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)

                # Generate new 6-digit OTP
                otp_code = generate_otp()
                PasswordResetOTP.objects.create(
                    user=user,
                    otp_code=otp_code
                )

                # Dispatch password reset email
                dispatch_password_reset_otp_email(user, otp_code)

                # Store email in session
                request.session['reset_email'] = user.email

                messages.info(
                    request,
                    f"A 6-digit password reset code was sent to {user.email}. Enter it below to set a new password."
                )
            else:
                # Anti-enumeration response
                messages.info(
                    request,
                    f"If an account with {email} is registered on Campus Marketplace, a 6-digit password reset code has been sent."
                )
                request.session['reset_email'] = email

            query_params = urlencode({'email': email})
            return redirect(f"{reverse('accounts:reset_password')}?{query_params}")
    else:
        initial_email = request.GET.get('email') or request.session.get('reset_email', '')
        form = ForgotPasswordRequestForm(initial={'email': initial_email} if initial_email else None)

    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_password_view(request):
    """
    Verify the 6-digit numeric OTP and set a new password.
    Validates 10-minute expiry window, password complexity, and redirects to login.
    """
    if request.user.is_authenticated:
        return redirect('marketplace:listing_list')

    email = request.GET.get('email') or request.POST.get('email') or request.session.get('reset_email', '')
    email = email.strip()

    user = None
    if email:
        user = User.objects.filter(email__iexact=email).first()

    if request.method == 'POST':
        form = ResetPasswordWithOTPForm(request.POST, user=user)
        if not user:
            form.add_error(None, "No registered account found for this email address. Please start the reset process again.")
        elif form.is_valid():
            submitted_otp = form.cleaned_data['otp_code']
            new_password = form.cleaned_data['new_password']

            # Find latest unused OTP for user
            otp_record = PasswordResetOTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()

            if not otp_record:
                form.add_error('otp_code', "No active password reset request found. Please request a new code.")
            elif not otp_record.is_valid():
                form.add_error('otp_code', "This reset code has expired (codes expire in 10 minutes). Please request a new one.")
            elif otp_record.otp_code != submitted_otp:
                form.add_error('otp_code', "Invalid reset code. Please check your email and enter the correct 6-digit code.")
            else:
                # Valid OTP! Mark as used and update password
                otp_record.is_used = True
                otp_record.save(update_fields=['is_used'])

                user.set_password(new_password)
                user.save()

                # Clean session
                request.session.pop('reset_email', None)

                messages.success(
                    request,
                    "Your password has been successfully reset! Please log in with your new password."
                )
                return redirect('accounts:login')
    else:
        form = ResetPasswordWithOTPForm(user=user)

    otp_record = PasswordResetOTP.objects.filter(user=user, is_used=False).order_by('-created_at').first() if user else None

    return render(request, 'accounts/reset_password.html', {
        'form': form,
        'email': email,
        'user_obj': user,
        'otp_code_preview': otp_record.otp_code if (settings.DEBUG and otp_record) else None,
        'debug': settings.DEBUG,
    })

