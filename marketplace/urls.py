from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    # Core Marketplace Catalog
    path('', views.listing_list, name='listing_list'),
    path('register/', views.register_view, name='register'),
    path('feed-partial/', views.feed_items_partial, name='feed_partial'),
    path('create/', views.listing_create, name='listing_create'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('api/lookup-isbn/', views.lookup_isbn_view, name='lookup_isbn'),
    
    # Wishlist / Saved Listings
    path('wishlist/', views.saved_listings_view, name='wishlist_list'),
    path('saved/', views.saved_listings_view, name='saved_listings'),
    path('<int:listing_id>/toggle-save/', views.toggle_save_listing, name='toggle_save'),
    path('<int:pk>/toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    
    # Direct Inquiry Messaging (In-App Chat)
    path('inbox/', views.inbox_view, name='inbox'),
    path('<int:listing_id>/conversation/<int:other_user_id>/', views.conversation_view, name='conversation'),
    path('<int:listing_id>/send-message/', views.send_inquiry_message, name='send_message'),
    path('<int:listing_id>/chat-partial/<int:other_user_id>/', views.chat_messages_partial, name='chat_messages_partial'),
    
    # Listing Detail & Ownership Actions
    path('<int:pk>/', views.listing_detail, name='listing_detail'),
    path('<int:pk>/edit/', views.listing_update, name='listing_update'),
    path('<int:pk>/delete/', views.listing_delete, name='listing_delete'),
    path('<int:pk>/toggle-sold/', views.listing_toggle_sold, name='listing_toggle_sold'),
]
