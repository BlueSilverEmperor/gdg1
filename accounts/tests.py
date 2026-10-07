from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from .models import EmailVerificationOTP
from .utils import generate_otp

User = get_user_model()


class AccountsAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_student_registration_creates_inactive_user_and_sends_otp(self):
        """
        Registration must create an inactive user (is_active=False),
        generate a 6-digit OTP, send it via email, and redirect to verify-otp.
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
        response = self.client.post(url, data)
        # Should redirect to verify_otp
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:verify_otp'), response.url)
        self.assertIn('email=sam%40campus.ac.in', response.url)

        # User created but is_active is False
        self.assertTrue(User.objects.filter(username='student_sam').exists())
        user = User.objects.get(username='student_sam')
        self.assertFalse(user.is_active)
        self.assertEqual(user.phone_number, '+91 9876543210')

        # OTP record created
        self.assertTrue(hasattr(user, 'otp_record'))
        otp = user.otp_record.otp_code
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

        # Email dispatched to in-memory mail.outbox
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ['sam@campus.ac.in'])
        self.assertIn(otp, sent_email.subject)
        self.assertIn(otp, sent_email.body)

    def test_submit_valid_otp_activates_user_and_logs_in(self):
        """
        Submitting the correct OTP activates the student account,
        deletes the OTP record, logs the student in, and redirects to feed.
        """
        user = User.objects.create_user(
            username='sam_verify',
            email='verify@campus.ac.in',
            password='Password123!',
            is_active=False
        )
        otp_record = EmailVerificationOTP.objects.create(
            user=user,
            otp_code='654321',
            attempts=0
        )

        url = f"{reverse('accounts:verify_otp')}?email={user.email}"
        response = self.client.post(url, {
            'email': user.email,
            'otp_code': '654321',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        # User is now active
        user.refresh_from_db()
        self.assertTrue(user.is_active)

        # OTP record is cleaned up
        self.assertFalse(EmailVerificationOTP.objects.filter(user=user).exists())

        # User is authenticated in the session
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'sam_verify')

    def test_submit_incorrect_otp_increments_attempts_and_rejects(self):
        """
        Submitting an incorrect OTP fails, increments attempts, and keeps user inactive.
        """
        user = User.objects.create_user(
            username='sam_wrong',
            email='wrong@campus.ac.in',
            password='Password123!',
            is_active=False
        )
        otp_record = EmailVerificationOTP.objects.create(
            user=user,
            otp_code='123456',
            attempts=0
        )

        url = f"{reverse('accounts:verify_otp')}?email={user.email}"
        response = self.client.post(url, {
            'email': user.email,
            'otp_code': '999999',
        })

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        otp_record.refresh_from_db()
        self.assertEqual(otp_record.attempts, 1)
        self.assertFormError(
            response.context['form'],
            'otp_code',
            'Incorrect verification code. 4 attempt(s) remaining.'
        )

    def test_submit_expired_otp_fails(self):
        """
        Submitting an OTP older than 10 minutes fails with expiry error.
        """
        user = User.objects.create_user(
            username='sam_expired',
            email='expired@campus.ac.in',
            password='Password123!',
            is_active=False
        )
        otp_record = EmailVerificationOTP.objects.create(
            user=user,
            otp_code='888888',
            attempts=0
        )
        # Fast-forward created_at by 11 minutes
        EmailVerificationOTP.objects.filter(pk=otp_record.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )

        url = f"{reverse('accounts:verify_otp')}?email={user.email}"
        response = self.client.post(url, {
            'email': user.email,
            'otp_code': '888888',
        })

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertContains(response, 'expired')

    def test_resend_otp_cooldown_throttling(self):
        """
        Resend OTP is throttled to 60 seconds minimum cooldown.
        """
        user = User.objects.create_user(
            username='sam_cooldown',
            email='cooldown@campus.ac.in',
            password='Password123!',
            is_active=False
        )
        otp_record = EmailVerificationOTP.objects.create(
            user=user,
            otp_code='111111',
            attempts=0
        )
        mail.outbox = []

        resend_url = f"{reverse('accounts:resend_otp')}?email={user.email}"

        # 1. Immediate resend attempt (within 60s) -> should be throttled
        res_throttled = self.client.post(resend_url, follow=True)
        self.assertEqual(res_throttled.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)  # No email sent
        otp_record.refresh_from_db()
        self.assertEqual(otp_record.otp_code, '111111')  # Unchanged

        # 2. Fast-forward past 60 seconds cooldown (65 seconds ago)
        EmailVerificationOTP.objects.filter(pk=otp_record.pk).update(
            created_at=timezone.now() - timedelta(seconds=65)
        )

        # 3. Resend attempt after cooldown -> succeeds & dispatches new OTP
        res_allowed = self.client.post(resend_url, follow=True)
        self.assertEqual(res_allowed.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)  # New email dispatched
        otp_record.refresh_from_db()
        self.assertNotEqual(otp_record.otp_code, '111111')

    def test_inactive_user_cannot_login_directly(self):
        """
        An inactive user attempting to log in is warned and redirected to OTP verification.
        """
        User.objects.create_user(
            username='inactive_student',
            email='inactive@campus.ac.in',
            password='MyPassword123!',
            is_active=False
        )
        login_url = reverse('accounts:login')
        response = self.client.post(login_url, {
            'username': 'inactive_student',
            'password': 'MyPassword123!'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'pending email verification')

    def test_registration_invalid_indian_phone(self):
        """
        Validates phone formatting reject cases.
        """
        url = reverse('accounts:register')
        data_short = {
            'username': 'short_phone_user',
            'email': 'short@campus.ac.in',
            'phone_number': '98765',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
        }
        res_short = self.client.post(url, data_short)
        self.assertEqual(res_short.status_code, 200)
        self.assertFormError(
            res_short.context['form'],
            'phone_number',
            'Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9 (e.g. +91 9876543210).'
        )

    def test_registration_duplicate_email(self):
        User.objects.create_user(
            username='existing_user',
            email='existing@campus.edu.in',
            password='Password123!'
        )
        url = reverse('accounts:register')
        data = {
            'username': 'new_user',
            'email': 'existing@campus.edu.in',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'],
            'email',
            'An account with this email address already exists.'
        )
