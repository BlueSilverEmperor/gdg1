from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.listing_list, name='listing_list'),
    path('create/', views.listing_create, name='listing_create'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('wishlist/', views.wishlist_list, name='wishlist_list'),
    path('api/lookup-isbn/', views.lookup_isbn_view, name='lookup_isbn'),
    path('<int:pk>/', views.listing_detail, name='listing_detail'),
    path('<int:pk>/edit/', views.listing_update, name='listing_update'),
    path('<int:pk>/delete/', views.listing_delete, name='listing_delete'),
    path('<int:pk>/toggle-sold/', views.listing_toggle_sold, name='listing_toggle_sold'),
    path('<int:pk>/toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
]
