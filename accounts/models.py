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

    @property
    def is_verified(self):
        """All accounts are instantly verified upon registration."""
        return True

    @property
    def is_email_verified(self):
        """All accounts are instantly verified upon registration."""
        return True
