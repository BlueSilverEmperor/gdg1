from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from unittest.mock import patch

from marketplace.models import Listing, SavedListing, Category, ListingStatus
from marketplace.forms import ListingForm
from marketplace.services import sanitize_isbn, fetch_book_by_isbn

User = get_user_model()


class MarketplaceListingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(
            username='student_alice',
            email='alice@university.edu',
            password='Password123!',
            campus_name='Engineering Campus'
        )
        self.user_b = User.objects.create_user(
            username='student_bob',
            email='bob@university.edu',
            password='Password123!',
            campus_name='Science Campus'
        )

        self.listing_a = Listing.objects.create(
            seller=self.user_a,
            title='Organic Chemistry Textbook 5th Ed',
            description='Like new condition with study guide included. Pickup at campus library.',
            price=Decimal('45.00'),
            category=Category.TEXTBOOKS,
            campus_pickup_location='Science Library Entrance',
            status=ListingStatus.AVAILABLE
        )

    def test_listing_model_str_and_properties(self):
        self.assertEqual(
            str(self.listing_a),
            "Organic Chemistry Textbook 5th Ed (₹45.00) - Available"
        )
        self.assertFalse(self.listing_a.is_sold)
        self.listing_a.status = ListingStatus.SOLD
        self.assertTrue(self.listing_a.is_sold)

    def test_listing_creation_valid_data(self):
        self.client.login(username='student_alice', password='Password123!')
        url = reverse('marketplace:listing_create')
        data = {
            'title': 'Graphing Calculator TI-84 Plus',
            'category': Category.ELECTRONICS,
            'price': '60.00',
            'campus_pickup_location': 'North Hall Study Lounge',
            'description': 'Excellent condition with charger and batteries.',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Listing.objects.filter(title='Graphing Calculator TI-84 Plus').exists())
        listing = Listing.objects.get(title='Graphing Calculator TI-84 Plus')
        self.assertEqual(listing.seller, self.user_a)
        self.assertEqual(listing.category, Category.ELECTRONICS)
        self.assertEqual(listing.price, Decimal('60.00'))
        self.assertEqual(listing.campus_pickup_location, 'North Hall Study Lounge')

    def test_listing_creation_invalid_data(self):
        self.client.login(username='student_alice', password='Password123!')
        url = reverse('marketplace:listing_create')
        
        # Test negative price
        data_neg_price = {
            'title': 'Calculus Notes',
            'category': Category.TEXTBOOKS,
            'price': '-15.00',
            'campus_pickup_location': 'Hostel 4',
            'description': 'Handwritten notes',
        }
        response = self.client.post(url, data_neg_price)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Listing.objects.filter(title='Calculus Notes').exists())

        # Test zero price
        data_zero_price = {
            'title': 'Free Desk Lamp',
            'category': Category.FURNITURE,
            'price': '0.00',
            'campus_pickup_location': 'Hostel 4',
            'description': 'Desk lamp',
        }
        response = self.client.post(url, data_zero_price)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Listing.objects.filter(title='Free Desk Lamp').exists())

        # Test empty title
        data_empty_title = {
            'title': '',
            'category': Category.OTHER,
            'price': '10.00',
            'campus_pickup_location': 'Hostel 4',
            'description': 'Empty title test',
        }
        response = self.client.post(url, data_empty_title)
        self.assertEqual(response.status_code, 200)

    def test_ownership_authorization_security_update(self):
        """
        User B must receive 403 Forbidden when attempting to update User A's listing.
        """
        self.client.login(username='student_bob', password='Password123!')
        url = reverse('marketplace:listing_update', kwargs={'pk': self.listing_a.pk})
        
        # Unauthorized GET request
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 403)

        # Unauthorized POST request
        response_post = self.client.post(url, {
            'title': 'Hacked Listing Title',
            'category': Category.TEXTBOOKS,
            'price': '1.00',
            'campus_pickup_location': 'Hacked',
            'description': 'Malicious modification attempt',
        })
        self.assertEqual(response_post.status_code, 403)

        # Confirm listing in database was unmodified
        self.listing_a.refresh_from_db()
        self.assertEqual(self.listing_a.title, 'Organic Chemistry Textbook 5th Ed')

    def test_ownership_authorization_security_delete(self):
        """
        User B must receive 403 Forbidden when attempting to delete User A's listing.
        """
        self.client.login(username='student_bob', password='Password123!')
        url = reverse('marketplace:listing_delete', kwargs={'pk': self.listing_a.pk})
        
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 403)

        response_post = self.client.post(url)
        self.assertEqual(response_post.status_code, 403)

        # Verify listing still exists in database
        self.assertTrue(Listing.objects.filter(pk=self.listing_a.pk).exists())

    def test_ownership_authorization_security_toggle_sold(self):
        """
        User B must receive 403 Forbidden when attempting to mark User A's listing as sold.
        """
        self.client.login(username='student_bob', password='Password123!')
        url = reverse('marketplace:listing_toggle_sold', kwargs={'pk': self.listing_a.pk})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.listing_a.refresh_from_db()
        self.assertEqual(self.listing_a.status, ListingStatus.AVAILABLE)

    def test_owner_can_update_and_delete_own_listing(self):
        """
        Owner (User A) should successfully edit and delete their own listing.
        """
        self.client.login(username='student_alice', password='Password123!')
        
        # Test update
        update_url = reverse('marketplace:listing_update', kwargs={'pk': self.listing_a.pk})
        response = self.client.post(update_url, {
            'title': 'Organic Chemistry Textbook 5th Ed (Updated)',
            'category': Category.TEXTBOOKS,
            'price': '40.00',
            'campus_pickup_location': 'Science Library Gate',
            'description': 'Price dropped for quick campus sale!',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.listing_a.refresh_from_db()
        self.assertEqual(self.listing_a.title, 'Organic Chemistry Textbook 5th Ed (Updated)')
        self.assertEqual(self.listing_a.price, Decimal('40.00'))

        # Test delete
        delete_url = reverse('marketplace:listing_delete', kwargs={'pk': self.listing_a.pk})
        response_del = self.client.post(delete_url, follow=True)
        self.assertEqual(response_del.status_code, 200)
        self.assertFalse(Listing.objects.filter(pk=self.listing_a.pk).exists())

    def test_owner_htmx_toggle_sold(self):
        """
        Owner can toggle sold/available status with HTMX partial response.
        """
        self.client.login(username='student_alice', password='Password123!')
        url = reverse('marketplace:listing_toggle_sold', kwargs={'pk': self.listing_a.pk})
        
        # Request with HX-Request header
        response = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.listing_a.refresh_from_db()
        self.assertEqual(self.listing_a.status, ListingStatus.SOLD)
        self.assertContains(response, 'SOLD')
        self.assertContains(response, 'Re-list Available')

        # Toggle back to available
        response2 = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response2.status_code, 200)
        self.listing_a.refresh_from_db()
        self.assertEqual(self.listing_a.status, ListingStatus.AVAILABLE)
        self.assertContains(response2, 'AVAILABLE')
        self.assertContains(response2, 'Mark as Sold')

    def test_toggle_wishlist_functionality(self):
        """
        Test saving and removing items from student's Wishlist.
        """
        self.client.login(username='student_bob', password='Password123!')
        url = reverse('marketplace:toggle_wishlist', kwargs={'pk': self.listing_a.pk})

        # Save to wishlist
        response = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SavedListing.objects.filter(user=self.user_b, listing=self.listing_a).exists())

        # Unsave from wishlist
        response2 = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response2.status_code, 200)
        self.assertFalse(SavedListing.objects.filter(user=self.user_b, listing=self.listing_a).exists())

    def test_search_and_category_filtering_logic(self):
        """
        Feed supports searching keywords across title, description, and pickup location,
        and filtering by category/status/sort.
        """
        # Create additional test listings including LAB_SUPPLIES
        laptop = Listing.objects.create(
            seller=self.user_b,
            title='MacBook Pro 14 M2',
            description='16GB RAM 512GB SSD Space Gray. Includes original charger.',
            price=Decimal('950.00'),
            category=Category.ELECTRONICS,
            campus_pickup_location='Student Union Canteen',
            status=ListingStatus.AVAILABLE
        )
        lab_kit = Listing.objects.create(
            seller=self.user_a,
            title='Chemistry Lab Coat & Safety Goggles',
            description='Required for Chem 101 lab classes. Cotton unisex size M.',
            price=Decimal('25.00'),
            category=Category.LAB_SUPPLIES,
            campus_pickup_location='Chemistry Annex Room 204',
            status=ListingStatus.AVAILABLE
        )
        chair = Listing.objects.create(
            seller=self.user_a,
            title='Ergonomic Desk Chair',
            description='Adjustable lumbar support for dorm study desk.',
            price=Decimal('50.00'),
            category=Category.FURNITURE,
            campus_pickup_location='North Tower Dorms',
            status=ListingStatus.AVAILABLE
        )

        url = reverse('marketplace:listing_list')

        # 1. Search keyword "MacBook" in title
        res_search = self.client.get(url, {'q': 'MacBook'})
        self.assertEqual(res_search.status_code, 200)
        self.assertContains(res_search, 'MacBook Pro 14 M2')
        self.assertNotContains(res_search, 'Organic Chemistry')

        # 2. Search keyword across campus_pickup_location "Annex"
        res_pickup = self.client.get(url, {'q': 'Annex'})
        self.assertEqual(res_pickup.status_code, 200)
        self.assertContains(res_pickup, 'Chemistry Lab Coat')

        # 3. Filter category: LAB_SUPPLIES
        res_cat = self.client.get(url, {'category': Category.LAB_SUPPLIES})
        self.assertEqual(res_cat.status_code, 200)
        self.assertContains(res_cat, 'Chemistry Lab Coat')
        self.assertNotContains(res_cat, 'MacBook Pro')

    def test_isbn_lookup_api_view(self):
        """
        Test /api/lookup-isbn/ view handling missing and valid inputs.
        """
        url = reverse('marketplace:lookup_isbn')
        
        # Missing ISBN parameter -> 400
        res_missing = self.client.get(url)
        self.assertEqual(res_missing.status_code, 400)
        data = res_missing.json()
        self.assertFalse(data['success'])

        # Mocked Open Library response
        with patch('marketplace.services.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'ISBN:9780134685991': {
                    'title': 'Effective Java 3rd Edition',
                    'authors': [{'name': 'Joshua Bloch'}],
                    'publish_date': 'December 27, 2017',
                    'cover': {
                        'large': 'https://covers.openlibrary.org/b/id/8231990-L.jpg'
                    }
                }
            }

            res_valid = self.client.get(url, {'isbn': '978-0134685991'})
            self.assertEqual(res_valid.status_code, 200)
            res_data = res_valid.json()
            self.assertTrue(res_data['success'])
            self.assertEqual(res_data['title'], 'Effective Java 3rd Edition')
            self.assertEqual(res_data['authors'], 'Joshua Bloch')
            self.assertEqual(res_data['publication_year'], '2017')
            self.assertEqual(res_data['cover_image_url'], 'https://covers.openlibrary.org/b/id/8231990-L.jpg')
