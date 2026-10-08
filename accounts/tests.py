from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.forms import StudentRegistrationForm, StudentLoginForm

User = get_user_model()


class StudentRegistrationAndAuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_instant_registration_with_edu_email(self):
        """
        Instant registration with .edu email creates active user,
        hashes password, signs user in, and redirects to marketplace feed.
        """
        url = reverse('accounts:register')
        data = {
            'username': 'student_sam',
            'email': 'sam@campus.edu',
            'first_name': 'Sam',
            'last_name': 'Altman',
            'campus_name': 'IIT Delhi',
            'phone_number': '9876543210',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('marketplace:listing_list'))

        # User is created and instantly active
        self.assertTrue(User.objects.filter(username='student_sam').exists())
        user = User.objects.get(username='student_sam')
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.check_password('SecurePassword123!'))

        # User is authenticated in the session immediately
        feed_res = self.client.get(reverse('marketplace:listing_list'))
        self.assertTrue(feed_res.context['user'].is_authenticated)
        self.assertEqual(feed_res.context['user'].username, 'student_sam')

    def test_instant_registration_with_acin_email(self):
        """
        Registration with .ac.in email succeeds directly without OTP verification.
        """
        url = reverse('accounts:register')
        data = {
            'username': 'student_neha',
            'email': 'neha@iitb.ac.in',
            'password': 'StrongPassword456!',
            'confirm_password': 'StrongPassword456!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(username='student_neha')
        self.assertTrue(user.is_active)
        self.assertEqual(user.email, 'neha@iitb.ac.in')

    def test_registration_rejects_non_campus_emails(self):
        """
        Non-campus email providers (e.g. gmail, yahoo) must be rejected with validation error.
        """
        for domain in ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']:
            email = f'user@{domain}'
            data = {
                'username': f'user_{domain.split(".")[0]}',
                'email': email,
                'password': 'ValidPassword123!',
                'confirm_password': 'ValidPassword123!',
            }
            response = self.client.post(reverse('accounts:register'), data)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(User.objects.filter(email=email).exists())
            self.assertIn('email', response.context['form'].errors)
            self.assertIn(
                "Registration requires a recognized college/university email address (.edu or .ac.in).",
                response.context['form'].errors['email']
            )

    def test_registration_rejects_duplicate_email(self):
        """
        Cannot register with an already registered college email.
        """
        User.objects.create_user(
            username='existing_user',
            email='existing@campus.edu',
            password='Password123!'
        )
        data = {
            'username': 'new_user',
            'email': 'existing@campus.edu',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='new_user').exists())
        self.assertIn('email', response.context['form'].errors)
        self.assertIn(
            "An account with this campus email already exists.",
            response.context['form'].errors['email']
        )

    def test_registration_rejects_mismatched_password(self):
        """
        Mismatched password fields raise a validation error.
        """
        data = {
            'username': 'mismatch_tester',
            'email': 'tester@campus.edu',
            'password': 'Password123!',
            'confirm_password': 'DifferentPassword456!',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatch_tester').exists())

    def test_registration_rejects_short_password(self):
        """
        Passwords shorter than 8 characters are rejected.
        """
        data = {
            'username': 'short_tester',
            'email': 'short@campus.edu',
            'password': '12345',
            'confirm_password': '12345',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='short_tester').exists())

    def test_login_and_logout_flow(self):
        """
        Existing active student can log in and log out smoothly.
        """
        User.objects.create_user(
            username='campus_login_user',
            email='login@campus.edu',
            password='MyPassword123!'
        )

        # Login
        login_res = self.client.post(reverse('accounts:login'), {
            'username': 'campus_login_user',
            'password': 'MyPassword123!',
        })
        self.assertEqual(login_res.status_code, 302)

        # Authenticated
        feed_res = self.client.get(reverse('marketplace:listing_list'))
        self.assertTrue(feed_res.context['user'].is_authenticated)

        # Logout
        logout_res = self.client.get(reverse('accounts:logout'))
        self.assertEqual(logout_res.status_code, 302)
        feed_res2 = self.client.get(reverse('marketplace:listing_list'))
        self.assertFalse(feed_res2.context['user'].is_authenticated)
