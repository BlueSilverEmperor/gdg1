import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

User = get_user_model()


class StudentRegistrationForm(forms.ModelForm):
    """
    Direct, instant student registration form validating college domains (.edu, .ac.in).
    Hashes passwords securely and requires minimum 8 characters.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create password (min. 8 characters)',
            'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none text-sm',
            'autocomplete': 'new-password',
        }),
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password',
            'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none text-sm',
            'autocomplete': 'new-password',
        }),
        label="Confirm Password"
    )
    password_confirm = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password',
            'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none text-sm',
            'autocomplete': 'new-password',
        }),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'campus_name', 'phone_number']
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Student username',
                'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-lg text-sm',
                'autocomplete': 'username',
            }),
            'first_name': forms.TextInput(attrs={
                'placeholder': 'First name',
                'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-lg text-sm',
                'autocomplete': 'given-name',
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Last name',
                'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-lg text-sm',
                'autocomplete': 'family-name',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'student@campus.edu or college.ac.in',
                'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-lg text-sm',
                'autocomplete': 'email',
            }),
            'campus_name': forms.TextInput(attrs={
                'placeholder': 'e.g. IIT Delhi, BITS Pilani, NMIT',
                'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-lg text-sm',
            }),
            'phone_number': forms.TextInput(attrs={
                'placeholder': 'e.g. +91 9876543210',
                'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-lg text-sm',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure optional fields don't block validation if not supplied
        if 'first_name' in self.fields:
            self.fields['first_name'].required = False
        if 'last_name' in self.fields:
            self.fields['last_name'].required = False
        if 'campus_name' in self.fields:
            self.fields['campus_name'].required = False
        if 'phone_number' in self.fields:
            self.fields['phone_number'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError("A valid campus email is required.")

        # Enforce college domain restriction
        valid_suffixes = ('.edu', '.ac.in', '.edu.in', 'campus.edu')
        if not any(email.endswith(suffix) for suffix in valid_suffixes):
            raise ValidationError("Registration requires a recognized college/university email address (.edu or .ac.in).")

        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this campus email already exists.")

        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password') or cleaned_data.get('password_confirm')

        if not p2:
            raise ValidationError("Passwords do not match.")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")
        if p1 and len(p1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        # New accounts are instantly active and verified
        user.is_active = True
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
