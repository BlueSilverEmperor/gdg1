from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from django.core.exceptions import PermissionDenied

from marketplace.models import (
    Listing, SavedListing, ListingMessage,
    Category, ListingStatus, CampusLocation
)

User = get_user_model()


class BonusFeaturesTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create three students
        self.seller_alice = User.objects.create_user(
            username='alice_seller',
            email='alice@campus.edu',
            password='Password123!',
            campus_name='Main Campus'
        )
        self.buyer_bob = User.objects.create_user(
            username='bob_buyer',
            email='bob@campus.edu',
            password='Password123!',
            campus_name='Engineering Campus'
        )
        self.eavesdropper_charlie = User.objects.create_user(
            username='charlie_third_party',
            email='charlie@campus.edu',
            password='Password123!',
            campus_name='Science Campus'
        )

        # Create sample listings with different campus locations
        self.listing_library = Listing.objects.create(
            seller=self.seller_alice,
            title='Data Structures in Java',
            description='Textbook in mint condition.',
            price=Decimal('500.00'),
            category=Category.TEXTBOOKS,
            pickup_location=CampusLocation.CENTRAL_LIBRARY,
            status=ListingStatus.AVAILABLE
        )

        self.listing_union = Listing.objects.create(
            seller=self.seller_alice,
            title='Dorm Study Desk Lamp',
            description='Warm LED desk lamp.',
            price=Decimal('250.00'),
            category=Category.FURNITURE,
            pickup_location=CampusLocation.STUDENT_UNION,
            status=ListingStatus.AVAILABLE
        )

    # ==========================================
    # ITERATION 1 TESTS: Campus Location & Feed
    # ==========================================

    def test_location_filter_returns_correct_listings(self):
        """Verify feed filters precisely by pickup_location."""
        # 1. Filter by CENTRAL_LIBRARY
        url = reverse('marketplace:listing_list') + '?pickup_location=' + CampusLocation.CENTRAL_LIBRARY
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Data Structures in Java')
        self.assertNotContains(resp, 'Dorm Study Desk Lamp')

        # 2. Filter by STUDENT_UNION
        url = reverse('marketplace:listing_list') + '?pickup_location=' + CampusLocation.STUDENT_UNION
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Dorm Study Desk Lamp')
        self.assertNotContains(resp, 'Data Structures in Java')

    def test_concurrent_search_and_location_filtering(self):
        """Verify search query + location filter work together."""
        url = reverse('marketplace:listing_list') + '?q=Java&pickup_location=' + CampusLocation.CENTRAL_LIBRARY
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Data Structures in Java')

        # Query that exists at union, but searching at library
        url = reverse('marketplace:listing_list') + '?q=Lamp&pickup_location=' + CampusLocation.CENTRAL_LIBRARY
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'Dorm Study Desk Lamp')

    # ==========================================
    # ITERATION 2 TESTS: Wishlist / Saved Listings
    # ==========================================

    def test_toggle_save_listing_workflow(self):
        """Test saving and un-saving a listing via toggle_save_listing."""
        self.client.login(username='bob_buyer', password='Password123!')
        toggle_url = reverse('marketplace:toggle_save', kwargs={'listing_id': self.listing_library.id})

        # 1. Save listing
        resp = self.client.post(toggle_url, HTTP_HX_REQUEST='true')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(SavedListing.objects.filter(user=self.buyer_bob, listing=self.listing_library).exists())
        self.assertEqual(self.listing_library.favorited_by.count(), 1)
        self.assertContains(resp, 'Remove from Wishlist')

        # 2. Toggle again to remove
        resp = self.client.post(toggle_url, HTTP_HX_REQUEST='true')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(SavedListing.objects.filter(user=self.buyer_bob, listing=self.listing_library).exists())
        self.assertEqual(self.listing_library.favorited_by.count(), 0)
        self.assertContains(resp, 'Save to Wishlist')

    def test_saved_listings_view(self):
        """Verify saved_listings_view renders all bookmarked items."""
        SavedListing.objects.create(user=self.buyer_bob, listing=self.listing_library)
        self.client.login(username='bob_buyer', password='Password123!')

        resp = self.client.get(reverse('marketplace:wishlist_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Data Structures in Java')

    # ==========================================
    # ITERATION 3 & 4 TESTS: In-App Messaging & Security
    # ==========================================

    def test_buyer_send_inquiry_message(self):
        """Test prospective buyer sending an inquiry to the seller."""
        self.client.login(username='bob_buyer', password='Password123!')
        send_url = reverse('marketplace:send_message', kwargs={'listing_id': self.listing_library.id})

        resp = self.client.post(send_url, {'message': 'Hello Alice, is this textbook still available?'}, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Check DB
        msg = ListingMessage.objects.filter(listing=self.listing_library, sender=self.buyer_bob).first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.receiver, self.seller_alice)
        self.assertEqual(msg.message, 'Hello Alice, is this textbook still available?')
        self.assertFalse(msg.is_read)

    def test_seller_reply_message(self):
        """Test seller replying back to the inquiring buyer."""
        # Initial buyer inquiry
        ListingMessage.objects.create(
            listing=self.listing_library,
            sender=self.buyer_bob,
            receiver=self.seller_alice,
            message='Is it available?'
        )

        self.client.login(username='alice_seller', password='Password123!')
        send_url = reverse('marketplace:send_message', kwargs={'listing_id': self.listing_library.id})

        resp = self.client.post(send_url, {
            'message': 'Yes Bob, can meet at Central Library at 4 PM.',
            'receiver_id': self.buyer_bob.id
        }, follow=True)
        self.assertEqual(resp.status_code, 200)

        reply = ListingMessage.objects.filter(
            listing=self.listing_library,
            sender=self.seller_alice,
            receiver=self.buyer_bob
        ).first()
        self.assertIsNotNone(reply)
        self.assertEqual(reply.message, 'Yes Bob, can meet at Central Library at 4 PM.')

    def test_unauthorized_user_conversation_access_forbidden(self):
        """Assert 403 Forbidden when a third party tries to read another user's chat."""
        # Chat thread between Alice and Bob
        ListingMessage.objects.create(
            listing=self.listing_library,
            sender=self.buyer_bob,
            receiver=self.seller_alice,
            message='Private negotiation message'
        )

        # Login as Charlie (third party trying to access Bob's buyer thread on Alice's listing)
        self.client.login(username='charlie_third_party', password='Password123!')
        conv_url = reverse('marketplace:conversation', kwargs={
            'listing_id': self.listing_library.id,
            'other_user_id': self.buyer_bob.id
        })

        resp = self.client.get(conv_url)
        # Must be 403 Forbidden
        self.assertEqual(resp.status_code, 403)

    def test_seller_cannot_message_themselves(self):
        """Assert seller cannot inquire on their own listing."""
        self.client.login(username='alice_seller', password='Password123!')
        send_url = reverse('marketplace:send_message', kwargs={'listing_id': self.listing_library.id})

        resp = self.client.post(send_url, {
            'message': 'Attempting to message myself',
            'receiver_id': self.seller_alice.id
        })
        self.assertEqual(resp.status_code, 403)

    def test_htmx_feed_polling_partial(self):
        """Test feed_items_partial endpoint for 15s HTMX polling."""
        url = reverse('marketplace:feed_partial') + '?pickup_location=' + CampusLocation.CENTRAL_LIBRARY
        resp = self.client.get(url, HTTP_HX_REQUEST='true')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'marketplace/partials/feed_grid.html')
        self.assertContains(resp, 'Data Structures in Java')
        self.assertNotContains(resp, 'Dorm Study Desk Lamp')

    def test_htmx_chat_polling_partial_and_read_receipt(self):
        """Test chat_messages_partial endpoint for 5s HTMX polling."""
        msg = ListingMessage.objects.create(
            listing=self.listing_library,
            sender=self.buyer_bob,
            receiver=self.seller_alice,
            message='Unread inquiry from Bob',
            is_read=False
        )

        self.client.login(username='alice_seller', password='Password123!')
        url = reverse('marketplace:chat_messages_partial', kwargs={
            'listing_id': self.listing_library.id,
            'other_user_id': self.buyer_bob.id
        })

        resp = self.client.get(url, HTTP_HX_REQUEST='true')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Unread inquiry from Bob')

        # Verify message was marked as read
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)
