import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

User = get_user_model()


class StudentRegistrationForm(forms.ModelForm):
    """
    Registration form with email format validation (campus/student email)
    and secure password confirmation.
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
                'placeholder': 'e.g. rahul@iitb.ac.in or student@campus.edu.in',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
                'autocomplete': 'email',
                'required': True,
            }),
            'campus_name': forms.TextInput(attrs={
                'placeholder': 'e.g. IIT Delhi, BITS Pilani, DU North Campus',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            }),
            'phone_number': forms.TextInput(attrs={
                'placeholder': 'e.g. +91 98765 43210 (10 digits)',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            }),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if not phone:
            return ""

        # Remove spaces, hyphens, parentheses
        digits = re.sub(r'[\s\-\(\)]', '', phone)

        # Strip country code +91 or 91 or leading 0 if present
        if digits.startswith('+91'):
            digits = digits[3:]
        elif digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]

        # Validate standard Indian 10-digit mobile number starting with 6, 7, 8, or 9
        if not re.match(r'^[6-9]\d{9}$', digits):
            raise ValidationError(
                "Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9 (e.g. +91 9876543210)."
            )

        # Standardize format as +91 XXXXXXXXXX
        return f"+91 {digits}"

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError("A valid campus email is required.")

        # Check standard email pattern
        email_pattern = r'^[\w\.-]+@([\w\.-]+\.\w+)$'
        match = re.match(email_pattern, email)
        if not match:
            raise ValidationError("Please enter a valid email address.")

        domain = match.group(1).lower()
        # Ensure it looks like an institutional / academic / campus or standard verified email domain
        # Allow .edu, .ac.*, .edu.* or any university / standard domain while rejecting invalid syntax
        if User.objects.filter(email__iexact=email).exists():
            existing = User.objects.filter(email__iexact=email).first()
            if existing and not existing.is_active:
                raise ValidationError(
                    "An account with this email is already registered and pending verification. "
                    "Please check your inbox or click 'Verify Email' to enter your code."
                )
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
        # Require OTP email verification before account activation
        user.is_active = False
        if commit:
            user.save()
        return user


class StudentLoginForm(AuthenticationForm):
    """
    Styled login form with Tailwind classes.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your username or email',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'autocomplete': 'username',
            'required': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
            'autocomplete': 'current-password',
            'required': True,
        })
    )


class OTPVerificationForm(forms.Form):
    """
    Form for validating the 6-digit email verification OTP.
    """
    otp_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'placeholder': '••••••',
            'class': 'w-full text-center text-3xl font-mono tracking-[0.5em] font-bold py-3.5 px-4 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 focus:outline-none transition',
            'autofocus': 'autofocus',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'maxlength': '8',
            'required': True,
        }),
        label="6-Digit Verification Code",
        help_text="Enter the 6-digit numeric code sent to your student email."
    )

    def clean_otp_code(self):
        raw = self.cleaned_data.get('otp_code', '')
        # Strip all whitespace, hyphens, and non-digits
        code = re.sub(r'\D', '', str(raw).strip())
        if len(code) != 6:
            raise ValidationError("Please enter a valid 6-digit numeric verification code.")
        return code

