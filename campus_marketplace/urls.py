"""
URL configuration for campus_marketplace project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from marketplace.views import lookup_isbn_view, health_check
from accounts.views import register_view as accounts_register_view

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('register/', accounts_register_view, name='register'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('api/lookup-isbn/', lookup_isbn_view, name='root_lookup_isbn'),
    path('', include('marketplace.urls', namespace='marketplace')),
]

# Serve media and static files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
