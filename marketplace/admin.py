from django.contrib import admin
from .models import Listing, SavedListing, ListingMessage, Category, ListingStatus, CampusLocation


@admin.action(description="Mark selected listings as Sold")
def mark_as_sold(modeladmin, request, queryset):
    queryset.update(status=ListingStatus.SOLD)


@admin.action(description="Mark selected listings as Available")
def mark_as_available(modeladmin, request, queryset):
    queryset.update(status=ListingStatus.AVAILABLE)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'category', 'price', 'status', 'pickup_location', 'created_at')
    list_filter = ('category', 'status', 'pickup_location', 'created_at')
    search_fields = ('title', 'description', 'campus_pickup_location', 'seller__username', 'seller__email')
    ordering = ('-created_at',)
    list_editable = ('status',)
    actions = [mark_as_sold, mark_as_available]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Listing Information', {
            'fields': ('title', 'seller', 'category', 'price', 'status', 'pickup_location', 'campus_pickup_location')
        }),
        ('Details & Media', {
            'fields': ('description', 'image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SavedListing)
class SavedListingAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'listing__title')
    ordering = ('-created_at',)


@admin.register(ListingMessage)
class ListingMessageAdmin(admin.ModelAdmin):
    list_display = ('listing', 'sender', 'receiver', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('listing__title', 'sender__username', 'receiver__username', 'message')
    ordering = ('-created_at',)
