from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.views.decorators.http import require_http_methods, require_POST

from .models import Listing, SavedListing, Category, ListingStatus
from .forms import ListingForm
from .services import fetch_book_by_isbn


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


def listing_list(request):
    """
    Marketplace discovery feed with search, category filtering, status filtering, and sorting.
    Searches across title, description, and campus_pickup_location.
    """
    listings = Listing.objects.select_related('seller').all()

    # Search filter across title, description, and campus_pickup_location
    query = request.GET.get('q', '').strip()
    if query:
        listings = listings.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(campus_pickup_location__icontains=query)
        )

    # Category filter
    selected_category = request.GET.get('category', '').strip()
    if selected_category and selected_category in Category.values:
        listings = listings.filter(category=selected_category)

    # Status filter (Available vs Sold vs All)
    status_filter = request.GET.get('status', 'AVAILABLE').strip().upper()
    if status_filter in [ListingStatus.AVAILABLE, ListingStatus.SOLD]:
        listings = listings.filter(status=status_filter)
    elif status_filter == 'ALL':
        pass  # Show both available and sold
    else:
        # Default to available for buyers
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

    # Saved listing IDs for logged-in user
    saved_listing_ids = set()
    if request.user.is_authenticated:
        saved_listing_ids = set(
            SavedListing.objects.filter(user=request.user).values_list('listing_id', flat=True)
        )

    context = {
        'listings': listings,
        'categories': Category.choices,
        'selected_category': selected_category,
        'selected_status': status_filter,
        'sort_by': sort_by,
        'query': query,
        'total_count': listings.count(),
        'saved_listing_ids': saved_listing_ids,
    }
    return render(request, 'marketplace/listing_list.html', context)


def listing_detail(request, pk):
    """
    Detailed view of a single listing with seller details, timestamps,
    campus pickup location, large image display, and sold status visual indicators.
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

    # Security check: strict object-level ownership
    if listing.seller != request.user:
        raise PermissionDenied("You do not have permission to modify this listing's status.")

    # Toggle status
    if listing.status == ListingStatus.AVAILABLE:
        listing.status = ListingStatus.SOLD
        status_msg = "marked as SOLD"
    else:
        listing.status = ListingStatus.AVAILABLE
        status_msg = "re-listed as AVAILABLE"

    listing.save(update_fields=['status', 'updated_at'])

    # If request was made via HTMX, return updated action fragment or badge
    if request.headers.get('HX-Request'):
        context = {'listing': listing, 'is_owner': True}
        return render(request, 'marketplace/partials/status_toggle_btn.html', context)

    messages.success(request, f"Listing '{listing.title}' was {status_msg}.")
    return redirect(request.META.get('HTTP_REFERER') or 'marketplace:my_listings')


@login_required
@require_POST
def toggle_wishlist(request, pk):
    """
    Single-click HTMX toggle to save or unsave items to the student's Wishlist.
    """
    listing = get_object_or_404(Listing, pk=pk)
    saved_item = SavedListing.objects.filter(user=request.user, listing=listing).first()

    if saved_item:
        saved_item.delete()
        is_saved = False
        msg = f"Removed '{listing.title}' from your saved items."
    else:
        SavedListing.objects.create(user=request.user, listing=listing)
        is_saved = True
        msg = f"Saved '{listing.title}' to your wishlist!"

    if request.headers.get('HX-Request'):
        return render(request, 'marketplace/partials/wishlist_btn.html', {
            'listing': listing,
            'is_saved': is_saved
        })

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER') or 'marketplace:listing_detail', pk=listing.pk)


@login_required
def wishlist_list(request):
    """
    Dedicated view displaying all items saved/favorited by the student.
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
