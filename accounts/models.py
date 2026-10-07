from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model for Campus Marketplace.
    Inherits from AbstractUser with campus student profile fields.
    """
    campus_name = models.CharField(
        max_length=120,
        blank=True,
        default="Campus Community",
        help_text="Name of college or campus (e.g. IIT Delhi, BITS Pilani, DU)"
    )
    phone_number = models.CharField(
        max_length=25,
        blank=True,
        help_text="Indian 10-digit mobile number with +91 (e.g. +91 9876543210)"
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.email})" if self.email else self.username


class EmailVerificationOTP(models.Model):
    """
    Stores 6-digit numeric OTP for student email verification.
    """
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='otp_record'
    )
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now=True)
    attempts = models.IntegerField(default=0)  # Max 5 attempts before invalidating

    class Meta:
        verbose_name = "Email Verification OTP"
        verbose_name_plural = "Email Verification OTPs"

    def __str__(self):
        return f"OTP for {self.user.email} ({self.otp_code})"

    def is_valid(self):
        """
        Checks if current time is within 10 minutes of created_at and under 5 attempts.
        """
        from datetime import timedelta
        from django.utils import timezone
        if self.attempts >= 5:
            return False
        return timezone.now() - self.created_at <= timedelta(minutes=10)

    def can_resend(self):
        """
        Checks if at least 60 seconds have elapsed since created_at.
        """
        from datetime import timedelta
        from django.utils import timezone
        return timezone.now() - self.created_at >= timedelta(seconds=60)

    def seconds_until_resend(self):
        """
        Returns remaining cooldown seconds before a resend is permitted.
        """
        from django.utils import timezone
        elapsed = (timezone.now() - self.created_at).total_seconds()
        remaining = 60 - int(elapsed)
        return max(0, remaining)

