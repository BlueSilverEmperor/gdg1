from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'campus_name', 'phone_number', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'campus_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Campus Information', {
            'fields': ('campus_name', 'phone_number')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Campus Information', {
            'fields': ('campus_name', 'phone_number')
        }),
    )
