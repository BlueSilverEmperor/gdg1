from django.db import models
from django.conf import settings
from django.urls import reverse


class Category(models.TextChoices):
    TEXTBOOKS = 'TEXTBOOKS', 'Textbooks'
    ELECTRONICS = 'ELECTRONICS', 'Electronics'
    LAB_SUPPLIES = 'LAB_SUPPLIES', 'Lab Supplies'
    FURNITURE = 'FURNITURE', 'Furniture'
    CLOTHING = 'CLOTHING', 'Clothing'
    HOUSING = 'HOUSING', 'Housing'
    OTHER = 'OTHER', 'Other'


class ListingStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    SOLD = 'SOLD', 'Sold'


class Listing(models.Model):
    """
    Campus Marketplace item listing.
    """
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings'
    )
    title = models.CharField(max_length=120)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER
    )
    image = models.ImageField(
        upload_to='listings/',
        blank=True,
        null=True,
        help_text="Upload a clear photo of the item"
    )
    status = models.CharField(
        max_length=20,
        choices=ListingStatus.choices,
        default=ListingStatus.AVAILABLE
    )
    campus_pickup_location = models.CharField(
        max_length=150,
        default="Student Union / Campus Library",
        help_text="e.g. Student Union, North Dorms"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.title} (₹{self.price:.2f}) - {self.get_status_display()}"

    @property
    def is_sold(self):
        return self.status == ListingStatus.SOLD

    def get_absolute_url(self):
        return reverse('marketplace:listing_detail', kwargs={'pk': self.pk})


class SavedListing(models.Model):
    """
    User Wishlist / Saved items model allowing students to bookmark listings.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_items'
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'listing'], name='unique_user_saved_listing')
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.listing.title}"
