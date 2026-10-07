from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
import requests
from decimal import Decimal
from .models import Listing, Category, ListingStatus


class ListingForm(forms.ModelForm):
    """
    Form for creating and editing marketplace listings with
    rich validation and optional ISBN helper autofill.
    """
    isbn_lookup = forms.CharField(
        required=False,
        max_length=20,
        label="Textbook ISBN (Optional)",
        help_text="Enter 10 or 13-digit ISBN to autofill textbook title, authors, year, and cover",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 9780140328721',
            'id': 'id_isbn_lookup',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition text-sm',
        })
    )

    remote_cover_url = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_remote_cover_url'})
    )

    class Meta:
        model = Listing
        fields = ['title', 'category', 'price', 'campus_pickup_location', 'description', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'id': 'id_title',
                'placeholder': 'e.g. Higher Engineering Mathematics - B.S. Grewal',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
                'required': True,
            }),
            'category': forms.Select(attrs={
                'id': 'id_category',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
                'required': True,
            }),
            'price': forms.NumberInput(attrs={
                'id': 'id_price',
                'placeholder': '450.00',
                'step': '0.01',
                'min': '0.01',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition font-semibold',
                'required': True,
            }),
            'campus_pickup_location': forms.TextInput(attrs={
                'id': 'id_campus_pickup_location',
                'placeholder': 'e.g. Student Union, North Dorms, Central Library Gate',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'id': 'id_description',
                'rows': 5,
                'placeholder': 'Describe item condition, edition, accessories included...',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none transition',
                'required': True,
            }),
            'image': forms.ClearableFileInput(attrs={
                'id': 'id_image',
                'accept': 'image/*',
                'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 dark:file:bg-indigo-950 dark:file:text-indigo-300',
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise ValidationError("Title is required.")
        if len(title) < 3:
            raise ValidationError("Title must be at least 3 characters long.")
        return title

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None:
            raise ValidationError("Price is required.")
        if price <= Decimal('0.00'):
            raise ValidationError("Price must be greater than ₹0.00.")
        if price > Decimal('999999.99'):
            raise ValidationError("Price cannot exceed ₹999,999.99.")
        return price

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if not description:
            raise ValidationError("Please provide a description.")
        return description

    def save(self, commit=True):
        listing = super().save(commit=False)
        # If no local image file uploaded, but an Open Library remote cover was retrieved
        remote_url = self.cleaned_data.get('remote_cover_url')
        if not self.cleaned_data.get('image') and remote_url and not listing.image:
            try:
                resp = requests.get(remote_url, timeout=5)
                if resp.status_code == 200 and resp.content:
                    file_name = f"isbn_cover_{listing.title[:15].replace(' ', '_')}.jpg"
                    listing.image.save(file_name, ContentFile(resp.content), save=False)
            except Exception:
                # Silently ignore image download errors to not block listing creation
                pass

        if commit:
            listing.save()
        return listing
