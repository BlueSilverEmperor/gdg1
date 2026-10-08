from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class AccountsAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_student_registration_creates_active_user_and_logs_in_immediately(self):
        """
        Registration must create an active student account with is_active=True,
        log them in immediately via direct session, and redirect to listing catalog.
        """
        url = reverse('accounts:register')
        data = {
            'username': 'student_sam',
            'email': 'sam@campus.ac.in',
            'campus_name': 'IIT Delhi (Hostel Nilgiri)',
            'phone_number': '9876543210',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
        }
        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('marketplace:listing_list'))

        # User is created, active and verified
        self.assertTrue(User.objects.filter(username='student_sam').exists())
        user = User.objects.get(username='student_sam')
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)
        self.assertEqual(user.phone_number, '+91 9876543210')

        # User is authenticated in current session
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'student_sam')

    def test_registration_password_mismatch_fails(self):
        """
        Registration fails if password and confirmation do not match.
        """
        url = reverse('accounts:register')
        data = {
            'username': 'mismatch_user',
            'email': 'mismatch@campus.ac.in',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatch_user').exists())
        self.assertFormError(response.context['form'], 'password_confirm', "Passwords do not match. Please verify your password.")

    def test_duplicate_email_registration_rejected(self):
        """
        Duplicate registered emails are rejected with a clear validation error.
        """
        User.objects.create_user(
            username='existing_user',
            email='existing@campus.ac.in',
            password='Password123!'
        )
        url = reverse('accounts:register')
        data = {
            'username': 'new_user',
            'email': 'existing@campus.ac.in',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'email', "An account with this email address already exists.")

    def test_student_login_success_and_logout(self):
        """
        Students can log in with valid credentials and log out smoothly.
        """
        user = User.objects.create_user(
            username='active_student',
            email='active@campus.ac.in',
            password='Password123!'
        )
        # Login
        response = self.client.post(reverse('accounts:login'), {
            'username': 'active_student',
            'password': 'Password123!',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

        # Logout
        logout_resp = self.client.post(reverse('accounts:logout'), follow=True)
        self.assertEqual(logout_resp.status_code, 200)
        self.assertFalse(logout_resp.context['user'].is_authenticated)

    def test_student_login_with_email_address_success(self):
        """
        Students can log in seamlessly using their registered email address instead of username.
        """
        User.objects.create_user(
            username='sam_student',
            email='sam_email@campus.ac.in',
            password='Password123!'
        )
        response = self.client.post(reverse('accounts:login'), {
            'username': 'sam_email@campus.ac.in',
            'password': 'Password123!',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'sam_student')

    def test_student_registration_with_optional_fields_blank(self):
        """
        Registration succeeds cleanly when phone number and campus name are left blank.
        """
        url = reverse('accounts:register')
        data = {
            'username': 'minimal_student',
            'email': 'minimal@campus.ac.in',
            'campus_name': '',
            'phone_number': '',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('marketplace:listing_list'))
        user = User.objects.get(username='minimal_student')
        self.assertTrue(user.is_active)
        self.assertEqual(user.campus_name, 'Campus Community')
        self.assertEqual(user.phone_number, '')

    def test_student_login_invalid_credentials(self):
        """
        Invalid username or password displays clear error.
        """
        User.objects.create_user(
            username='real_student',
            email='real@campus.ac.in',
            password='Password123!'
        )
        response = self.client.post(reverse('accounts:login'), {
            'username': 'real_student',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username")

    def test_authenticated_user_redirected_from_login_and_register(self):
        """
        Logged in students accessing auth pages are redirected to listing catalog.
        """
        user = User.objects.create_user(
            username='logged_in_user',
            email='logged@campus.ac.in',
            password='Password123!'
        )
        self.client.force_login(user)

        for page in ['accounts:login', 'accounts:register', 'accounts:forgot_password', 'accounts:reset_password']:
            resp = self.client.get(reverse(page))
            self.assertEqual(resp.status_code, 302)
            self.assertRedirects(resp, reverse('marketplace:listing_list'))

    def test_direct_password_reset_flow(self):
        """
        Student enters email in forgot-password, forwards to reset-password,
        updates password directly, and can log in with the new password.
        """
        user = User.objects.create_user(
            username='reset_student',
            email='student_reset@campus.ac.in',
            password='OldPassword123!'
        )

        # Step 1: Request password reset
        forgot_url = reverse('accounts:forgot_password')
        response = self.client.post(forgot_url, {'email': user.email})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:reset_password'), response.url)

        # Step 2: Set new password
        reset_url = f"{reverse('accounts:reset_password')}?email={user.email}"
        reset_resp = self.client.post(reset_url, {
            'email': user.email,
            'new_password': 'NewSecurePassword123!',
            'confirm_password': 'NewSecurePassword123!',
        }, follow=True)

        self.assertEqual(reset_resp.status_code, 200)
        self.assertRedirects(reset_resp, reverse('accounts:login'))

        # Step 3: Login with new password
        login_resp = self.client.post(reverse('accounts:login'), {
            'username': 'reset_student',
            'password': 'NewSecurePassword123!',
        }, follow=True)
        self.assertEqual(login_resp.status_code, 200)
        self.assertTrue(login_resp.context['user'].is_authenticated)
