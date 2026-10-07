from .models import SavedListing, ListingMessage


def marketplace_counts(request):
    """
    Context processor providing dynamic navbar counts for saved wishlist items
    and unread buyer-seller inquiry messages.
    """
    if not request.user.is_authenticated:
        return {
            'navbar_saved_count': 0,
            'navbar_unread_count': 0,
        }

    saved_count = SavedListing.objects.filter(user=request.user).count()
    unread_count = ListingMessage.objects.filter(receiver=request.user, is_read=False).count()

    return {
        'navbar_saved_count': saved_count,
        'navbar_unread_count': unread_count,
    }
