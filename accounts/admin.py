from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, EmailVerificationOTP



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


@admin.register(EmailVerificationOTP)
class EmailVerificationOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'created_at', 'attempts')
    search_fields = ('user__username', 'user__email', 'otp_code')
    readonly_fields = ('created_at',)

