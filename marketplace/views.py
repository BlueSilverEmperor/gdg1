from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods, require_POST

from .models import Listing, SavedListing, ListingMessage, Category, ListingStatus, CampusLocation
from .forms import ListingForm
from .services import fetch_book_by_isbn


User = get_user_model()


def health_check(request):
    """
    Ultra-lightweight zero-overhead health check endpoint for uptime monitors
    (e.g., UptimeRobot, cron-job.org) to keep the Render free tier warm.
    Directly returns HTTP 200 'ok' without database queries, session lookups, or template rendering.
    """
    return HttpResponse("ok", content_type="text/plain", status=200)


def lookup_isbn_view(request):
    """
    Dedicated API endpoint for looking up textbook details via Open Library API.
    Accepts GET ?isbn=...
    Returns JSON {title, authors, cover_image_url, publication_year, suggested_description}
    """
    isbn = request.GET.get('isbn', '').strip()
    if not isbn:
        return JsonResponse({
            'success': False,
            'error': 'Missing ISBN parameter. Please provide a 10- or 13-digit ISBN.'
        }, status=400)

    result = fetch_book_by_isbn(isbn)
    status_code = 200 if result.get('success') else 400
    return JsonResponse(result, status=status_code)


def _get_filtered_listings(request):
    """
    Internal helper to filter listings by search query, category, campus location,
    and status filter with sorting.
    """
    listings = Listing.objects.select_related('seller').all()

    # Search filter across title, description, and pickup location
    query = request.GET.get('q', '').strip()
    if query:
        listings = listings.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(pickup_location__icontains=query) |
            Q(campus_pickup_location__icontains=query)
        )

    # Category filter
    selected_category = request.GET.get('category', '').strip()
    if selected_category and selected_category in Listing.Category.values:
        listings = listings.filter(category=selected_category)

    # Campus Pickup Location filter
    selected_location = request.GET.get('pickup_location', '').strip()
    if selected_location and selected_location in CampusLocation.values:
        listings = listings.filter(pickup_location=selected_location)

    # Status filter (Available vs Sold vs All)
    status_filter = request.GET.get('status', 'AVAILABLE').strip().upper()
    if status_filter in [ListingStatus.AVAILABLE, ListingStatus.SOLD]:
        listings = listings.filter(status=status_filter)
    elif status_filter == 'ALL':
        pass  # Show both available and sold
    else:
        status_filter = ListingStatus.AVAILABLE
        listings = listings.filter(status=ListingStatus.AVAILABLE)

    # Sorting
    sort_by = request.GET.get('sort', 'newest').strip()
    if sort_by == 'price_asc':
        listings = listings.order_by('price', '-created_at')
    elif sort_by == 'price_desc':
        listings = listings.order_by('-price', '-created_at')
    else:
        sort_by = 'newest'
        listings = listings.order_by('-created_at')

    return listings, query, selected_category, selected_location, status_filter, sort_by


def listing_list(request):
    """
    Marketplace discovery feed with search, category filtering,
    campus pickup location filtering, status filtering, and sorting.
    """
    listings, query, selected_category, selected_location, status_filter, sort_by = _get_filtered_listings(request)

    # Saved listing IDs for logged-in user
    saved_listing_ids = set()
    if request.user.is_authenticated:
        saved_listing_ids = set(
            SavedListing.objects.filter(user=request.user).values_list('listing_id', flat=True)
        )

    context = {
        'listings': listings,
        'categories': Listing.Category.choices,
        'locations': CampusLocation.choices,
        'selected_category': selected_category,
        'selected_location': selected_location,
        'selected_status': status_filter,
        'sort_by': sort_by,
        'query': query,
        'total_count': listings.count(),
        'saved_listing_ids': saved_listing_ids,
    }
    return render(request, 'marketplace/listing_list.html', context)


def feed_items_partial(request):
    """
    HTMX endpoint for live polling the marketplace listings grid every 15s.
    Preserves active search, category, location, and status filters.
    """
    listings, query, selected_category, selected_location, status_filter, sort_by = _get_filtered_listings(request)

    saved_listing_ids = set()
    if request.user.is_authenticated:
        saved_listing_ids = set(
            SavedListing.objects.filter(user=request.user).values_list('listing_id', flat=True)
        )

    context = {
        'listings': listings,
        'saved_listing_ids': saved_listing_ids,
    }
    return render(request, 'marketplace/partials/feed_grid.html', context)


def listing_detail(request, pk):
    """
    Detailed view of a single listing with seller details, timestamps,
    campus pickup location, large image display, and direct inquiry CTA.
    """
    listing = get_object_or_404(Listing.objects.select_related('seller'), pk=pk)

    # Related listings in same category (excluding current)
    related_listings = Listing.objects.filter(
        category=listing.category,
        status=ListingStatus.AVAILABLE
    ).exclude(pk=listing.pk).select_related('seller')[:3]

    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedListing.objects.filter(user=request.user, listing=listing).exists()

    context = {
        'listing': listing,
        'related_listings': related_listings,
        'is_owner': request.user.is_authenticated and (request.user == listing.seller),
        'is_saved': is_saved,
    }
    return render(request, 'marketplace/listing_detail.html', context)


@login_required
def listing_create(request):
    """
    Create a new listing. Enforces authentication and assigns seller = request.user.
    """
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.save()
            messages.success(request, f"Listing '{listing.title}' successfully posted to the campus marketplace!")
            return redirect('marketplace:listing_detail', pk=listing.pk)
        else:
            messages.error(request, "Please check the form for errors.")
    else:
        form = ListingForm()

    return render(request, 'marketplace/listing_form.html', {
        'form': form,
        'is_edit': False,
        'categories': Category.choices,
    })


@login_required
def listing_update(request, pk):
    """
    Update an existing listing. Enforces strict object-level ownership check.
    Raises PermissionDenied (403) if request.user != listing.seller.
    """
    listing = get_object_or_404(Listing, pk=pk)

    # Security check: strict object-level ownership
    if listing.seller != request.user:
        raise PermissionDenied("You do not have permission to edit this listing.")

    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            form.save()
            messages.success(request, f"Listing '{listing.title}' updated successfully.")
            return redirect('marketplace:listing_detail', pk=listing.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ListingForm(instance=listing)

    return render(request, 'marketplace/listing_form.html', {
        'form': form,
        'listing': listing,
        'is_edit': True,
        'categories': Category.choices,
    })


@login_required
@require_http_methods(["GET", "POST"])
def listing_delete(request, pk):
    """
    Delete a listing. Enforces strict object-level ownership check.
    Raises PermissionDenied (403) if request.user != listing.seller.
    """
    listing = get_object_or_404(Listing, pk=pk)

    # Security check: strict object-level ownership
    if listing.seller != request.user:
        raise PermissionDenied("You do not have permission to delete this listing.")

    if request.method == 'POST':
        title = listing.title
        listing.delete()
        messages.success(request, f"Listing '{title}' was permanently deleted.")
        return redirect('marketplace:my_listings')

    return render(request, 'marketplace/listing_confirm_delete.html', {
        'listing': listing
    })


@login_required
@require_POST
def listing_toggle_sold(request, pk):
    """
    Toggle a listing's status between AVAILABLE and SOLD.
    Strict object-level ownership: only listing.seller can toggle status.
    Supports HTMX single-click action for instant UI updates.
    """
    listing = get_object_or_404(Listing, pk=pk)

    if listing.seller != request.user:
        raise PermissionDenied("You do not have permission to modify this listing's status.")

    if listing.status == ListingStatus.AVAILABLE:
        listing.status = ListingStatus.SOLD
        status_msg = "marked as SOLD"
    else:
        listing.status = ListingStatus.AVAILABLE
        status_msg = "re-listed as AVAILABLE"

    listing.save(update_fields=['status', 'updated_at'])

    if request.headers.get('HX-Request'):
        context = {'listing': listing, 'is_owner': True}
        return render(request, 'marketplace/partials/status_toggle_btn.html', context)

    messages.success(request, f"Listing '{listing.title}' was {status_msg}.")
    return redirect(request.META.get('HTTP_REFERER') or 'marketplace:my_listings')


@login_required
@require_POST
def toggle_save_listing(request, listing_id=None, pk=None):
    """
    Single-click HTMX toggle to save or unsave items to the student's Wishlist.
    Returns partial with updated heart state and favorite count.
    """
    target_id = listing_id if listing_id is not None else pk
    listing = get_object_or_404(Listing, pk=target_id)
    saved_item = SavedListing.objects.filter(user=request.user, listing=listing).first()

    if saved_item:
        saved_item.delete()
        is_saved = False
        msg = f"Removed '{listing.title}' from your saved items."
    else:
        SavedListing.objects.create(user=request.user, listing=listing)
        is_saved = True
        msg = f"Saved '{listing.title}' to your wishlist!"

    total_user_saved = SavedListing.objects.filter(user=request.user).count()

    if request.headers.get('HX-Request'):
        return render(request, 'marketplace/partials/wishlist_btn.html', {
            'listing': listing,
            'is_saved': is_saved,
            'favorites_count': listing.favorited_by.count(),
            'total_user_saved': total_user_saved,
        })

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER') or 'marketplace:listing_detail', pk=listing.pk)


# Backward-compatible alias
toggle_wishlist = toggle_save_listing


@login_required
def saved_listings_view(request):
    """
    Dedicated view displaying all active items saved/favorited by the student.
    """
    saved_items = SavedListing.objects.filter(
        user=request.user
    ).select_related('listing', 'listing__seller')

    saved_listing_ids = set(saved_items.values_list('listing_id', flat=True))

    return render(request, 'marketplace/wishlist_list.html', {
        'saved_items': saved_items,
        'saved_listing_ids': saved_listing_ids,
        'total_saved': saved_items.count(),
    })


# Backward-compatible alias
wishlist_list = saved_listings_view


@login_required
def my_listings(request):
    """
    Display listings created by the authenticated user with inventory stats and actions.
    """
    status_filter = request.GET.get('status', 'ALL').strip().upper()
    user_listings = Listing.objects.filter(seller=request.user)

    if status_filter == ListingStatus.AVAILABLE:
        user_listings = user_listings.filter(status=ListingStatus.AVAILABLE)
    elif status_filter == ListingStatus.SOLD:
        user_listings = user_listings.filter(status=ListingStatus.SOLD)

    user_listings = user_listings.order_by('-created_at')

    total_active = Listing.objects.filter(seller=request.user, status=ListingStatus.AVAILABLE).count()
    total_sold = Listing.objects.filter(seller=request.user, status=ListingStatus.SOLD).count()
    total_saved = SavedListing.objects.filter(user=request.user).count()

    context = {
        'listings': user_listings,
        'selected_status': status_filter,
        'total_active': total_active,
        'total_sold': total_sold,
        'total_all': total_active + total_sold,
        'total_saved': total_saved,
    }
    return render(request, 'marketplace/my_listings.html', context)


# ==========================================
# ITERATION 3 & 4: In-App Inquiry Messaging
# ==========================================

@login_required
def inbox_view(request):
    """
    Lists all distinct listing conversation threads where request.user is either
    the sender or the receiver, with unread counters and latest snippet.
    """
    messages_qs = ListingMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('listing', 'listing__seller', 'sender', 'receiver').order_by('-created_at')

    threads = []
    seen = set()

    for msg in messages_qs:
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        pair_key = (msg.listing_id, other_user.id)
        if pair_key not in seen:
            seen.add(pair_key)
            unread_count = ListingMessage.objects.filter(
                listing_id=msg.listing_id,
                sender=other_user,
                receiver=request.user,
                is_read=False
            ).count()
            threads.append({
                'listing': msg.listing,
                'other_user': other_user,
                'last_message': msg,
                'unread_count': unread_count,
            })

    return render(request, 'marketplace/inbox.html', {
        'threads': threads,
        'total_threads': len(threads),
    })


@login_required
def conversation_view(request, listing_id, other_user_id):
    """
    Renders direct buyer-seller message thread for a specific listing.
    Enforces strict authorization: user must be either buyer or seller.
    Automatically marks incoming messages from other_user as read.
    """
    listing = get_object_or_404(Listing.objects.select_related('seller'), pk=listing_id)
    other_user = get_object_or_404(User, pk=other_user_id)

    # Security check: users cannot message themselves
    if request.user == other_user:
        raise PermissionDenied("You cannot start a conversation with yourself.")

    # Security check: user must be either the listing's seller or prospective buyer
    is_seller_buyer_pair = (
        (request.user == listing.seller and other_user != listing.seller) or
        (request.user != listing.seller and other_user == listing.seller)
    )
    if not is_seller_buyer_pair:
        raise PermissionDenied("You do not have permission to access this conversation.")

    # Mark unread messages sent by other_user as read
    ListingMessage.objects.filter(
        listing=listing,
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    # Fetch ordered conversation history
    chat_messages = ListingMessage.objects.filter(
        listing=listing
    ).filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).select_related('sender').order_by('created_at')

    context = {
        'listing': listing,
        'other_user': other_user,
        'chat_messages': chat_messages,
        'is_seller': (request.user == listing.seller),
    }
    return render(request, 'marketplace/conversation.html', context)


@login_required
@require_POST
def send_inquiry_message(request, listing_id):
    """
    Handles new inquiry message submission. Prevents seller from messaging themselves as buyer.
    Supports both standard POST and HTMX live swapping.
    """
    listing = get_object_or_404(Listing.objects.select_related('seller'), pk=listing_id)
    message_text = request.POST.get('message', '').strip()

    if not message_text:
        if request.headers.get('HX-Request'):
            return HttpResponse(status=204)
        messages.error(request, "Message cannot be empty.")
        return redirect('marketplace:listing_detail', pk=listing.pk)

    # Determine receiver
    if request.user == listing.seller:
        # Seller replying to a buyer
        receiver_id = request.POST.get('receiver_id')
        if not receiver_id:
            raise PermissionDenied("Recipient is required.")
        receiver = get_object_or_404(User, pk=receiver_id)
        if receiver == listing.seller:
            raise PermissionDenied("Cannot send message to yourself.")
    else:
        # Buyer inquiring to seller
        receiver = listing.seller
        if request.user == listing.seller:
            raise PermissionDenied("Sellers cannot inquire on their own listings.")

    ListingMessage.objects.create(
        listing=listing,
        sender=request.user,
        receiver=receiver,
        message=message_text
    )

    if request.headers.get('HX-Request'):
        # Return updated messages container partial
        chat_messages = ListingMessage.objects.filter(
            listing=listing
        ).filter(
            (Q(sender=request.user) & Q(receiver=receiver)) |
            (Q(sender=receiver) & Q(receiver=request.user))
        ).select_related('sender').order_by('created_at')

        return render(request, 'marketplace/partials/chat_messages.html', {
            'chat_messages': chat_messages,
            'listing': listing,
            'other_user': receiver,
        })

    return redirect('marketplace:conversation', listing_id=listing.pk, other_user_id=receiver.pk)


@login_required
def chat_messages_partial(request, listing_id, other_user_id):
    """
    HTMX live polling endpoint (every 5s) returning updated message bubbles.
    Marks incoming messages as read so unread badge stays accurate.
    """
    listing = get_object_or_404(Listing.objects.select_related('seller'), pk=listing_id)
    other_user = get_object_or_404(User, pk=other_user_id)

    # Security check
    is_seller_buyer_pair = (
        (request.user == listing.seller and other_user != listing.seller) or
        (request.user != listing.seller and other_user == listing.seller)
    )
    if not is_seller_buyer_pair:
        raise PermissionDenied("Unauthorized conversation access.")

    # Mark newly polled messages as read
    ListingMessage.objects.filter(
        listing=listing,
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    chat_messages = ListingMessage.objects.filter(
        listing=listing
    ).filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).select_related('sender').order_by('created_at')

    return render(request, 'marketplace/partials/chat_messages.html', {
        'chat_messages': chat_messages,
        'listing': listing,
        'other_user': other_user,
    })
