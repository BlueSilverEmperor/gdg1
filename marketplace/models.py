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


class CampusLocation(models.TextChoices):
    STUDENT_UNION = 'STUDENT_UNION', 'Student Union'
    CENTRAL_LIBRARY = 'CENTRAL_LIBRARY', 'Central Library'
    NORTH_QUAD_DORMS = 'NORTH_QUAD_DORMS', 'North Quad Dorms'
    SCIENCE_BLOCK = 'SCIENCE_BLOCK', 'Science Block'
    SPORTS_COMPLEX = 'SPORTS_COMPLEX', 'Sports Complex'
    MAIN_GATE = 'MAIN_GATE', 'Main Campus Gate'


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
    pickup_location = models.CharField(
        max_length=40,
        choices=CampusLocation.choices,
        default=CampusLocation.STUDENT_UNION,
        help_text="Designated safe campus meetup spot"
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
            models.Index(fields=['pickup_location']),
        ]

    def __str__(self):
        return f"{self.title} (₹{self.price:.2f}) - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Synchronize campus_pickup_location text with pickup_location label for display if not explicitly provided
        if self.pickup_location and not self.campus_pickup_location:
            self.campus_pickup_location = self.get_pickup_location_display()
        super().save(*args, **kwargs)

    @property
    def is_sold(self):
        return self.status == ListingStatus.SOLD

    @property
    def favorites_count(self):
        return self.favorited_by.count()

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


class ListingMessage(models.Model):
    """
    Direct buyer-seller inquiry messaging between students for a specific listing.
    """
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='inquiries'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_inquiries'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_inquiries'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['listing', 'sender', 'receiver']),
            models.Index(fields=['receiver', 'is_read']),
        ]

    def __str__(self):
        return f"Msg from {self.sender.username} to {self.receiver.username} on '{self.listing.title}'"
