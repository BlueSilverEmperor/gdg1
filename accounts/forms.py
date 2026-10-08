import re
from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

User = get_user_model()


class StudentRegistrationForm(forms.ModelForm):
    """
    Registration form with email format validation (campus/student email)
    and secure password confirmation.
    Zero-latency instant account activation.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter strong password (min 6 characters)',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'autocomplete': 'new-password',
            'required': True,
        }),
        min_length=6,
        help_text="Minimum 6 characters."
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm your password',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'autocomplete': 'new-password',
            'required': True,
        }),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'campus_name', 'phone_number']
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'e.g. rahul_sharma',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
                'autocomplete': 'username',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'e.g. rahul@iitb.ac.in or student@campus.edu',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
                'autocomplete': 'email',
                'required': True,
            }),
            'campus_name': forms.TextInput(attrs={
                'placeholder': 'e.g. IIT Delhi, BITS Pilani, DU North Campus (Optional)',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            }),
            'phone_number': forms.TextInput(attrs={
                'placeholder': 'e.g. 9876543210 (Optional)',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError("Please choose a username.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another username.")
        return username

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if not phone:
            return ""

        digits = re.sub(r'[\s\-\(\)]', '', phone)
        if digits.startswith('+91'):
            digits = digits[3:]
        elif digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]

        if not re.match(r'^[6-9]\d{9}$', digits):
            raise ValidationError(
                "Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9 (e.g. +91 9876543210)."
            )

        return f"+91 {digits}"

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError("A valid campus email is required.")

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Please enter a valid email address.")

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")

        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match. Please verify your password.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if not user.campus_name or not user.campus_name.strip():
            user.campus_name = "Campus Community"
        user.is_active = True
        user.is_verified = True
        if commit:
            user.save()
        return user


class StudentLoginForm(AuthenticationForm):
    """
    Styled login form with Tailwind classes.
    Supports login with either Username OR Email address seamlessly.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter username or registered email',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'autocomplete': 'username',
            'required': True,
        }),
        label="Username or Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'autocomplete': 'current-password',
            'required': True,
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            clean_username = username.strip()
            # Allow login by either email or username (case-insensitive lookup)
            user_candidate = User.objects.filter(email__iexact=clean_username).first()
            if not user_candidate:
                user_candidate = User.objects.filter(username__iexact=clean_username).first()

            auth_username = user_candidate.username if user_candidate else clean_username

            self.user_cache = authenticate(
                self.request,
                username=auth_username,
                password=password,
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Invalid username/email or password. Please check your credentials.",
                    code='invalid_login'
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class ForgotPasswordRequestForm(forms.Form):
    """
    Form for requesting a password reset by registered student email.
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'e.g. rahul@iitb.ac.in or student@campus.edu.in',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'autocomplete': 'email',
            'autofocus': 'autofocus',
            'required': True,
        }),
        label="Registered Student Email",
        help_text="Enter your university or registered campus email address."
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError("Please enter your registered student email.")
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Please enter a valid email address.")
        return email


class ResetPasswordForm(forms.Form):
    """
    Form for directly resetting a student password without OTP friction.
    """
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter new password (min 6 characters)',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'autocomplete': 'new-password',
            'required': True,
        }),
        label="New Password",
        min_length=6,
        help_text="Choose a secure password (at least 6 characters)."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm your new password',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'autocomplete': 'new-password',
            'required': True,
        }),
        label="Confirm New Password",
        help_text="Re-type your new password to verify."
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match. Please re-enter both passwords.")
            else:
                try:
                    validate_password(new_password, user=self.user)
                except ValidationError as e:
                    self.add_error('new_password', e)

        return cleaned_data
