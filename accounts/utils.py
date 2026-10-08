import os
import secrets
import logging
import requests
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_otp() -> str:
    """
    Generate a cryptographically secure 6-digit numeric OTP (100000 - 999999).
    """
    code = secrets.randbelow(900000) + 100000
    return f"{code:06d}"


def _try_https_email(recipient_email: str, subject: str, html_message: str, plain_message: str) -> bool:
    """
    Dispatches transactional emails over outbound HTTPS (port 443) to bypass
    cloud host SMTP restrictions (e.g. Railway blocks TCP port 587/465).
    Supports Resend or Brevo HTTP APIs if configured in environment variables.
    """
    resend_key = os.environ.get('RESEND_API_KEY', '').strip()
    if resend_key:
        try:
            from_addr = os.environ.get('RESEND_FROM_EMAIL', 'Campus Marketplace <onboarding@resend.dev>').strip()
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": from_addr,
                    "to": [recipient_email],
                    "subject": subject,
                    "html": html_message or plain_message,
                    "text": plain_message,
                },
                timeout=10,
            )
            if resp.status_code in (200, 201):
                logger.info(f"Email successfully sent via Resend HTTPS API to {recipient_email}")
                return True
            logger.warning(f"Resend API error {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"Resend HTTP dispatch failed: {e}")

    brevo_key = os.environ.get('BREVO_API_KEY', '').strip()
    if brevo_key:
        try:
            sender_email = os.environ.get('EMAIL_HOST_USER', 'no-reply@campusmarketplace.local').strip()
            resp = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": brevo_key,
                    "Content-Type": "application/json",
                },
                json={
                    "sender": {"name": "Campus Marketplace", "email": sender_email},
                    "to": [{"email": recipient_email}],
                    "subject": subject,
                    "htmlContent": html_message or plain_message,
                    "textContent": plain_message,
                },
                timeout=10,
            )
            if resp.status_code in (200, 201):
                logger.info(f"Email successfully sent via Brevo HTTPS API to {recipient_email}")
                return True
            logger.warning(f"Brevo API error {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"Brevo HTTP dispatch failed: {e}")

    return False


def send_otp_email(user, otp_code: str) -> bool:
    """
    Dispatches a branded HTML and plain-text email with the OTP code
    and expiration details. Returns True on success, False on failure.
    """
    subject = f"Your Campus Marketplace Verification Code: {otp_code}"
    context = {
        'user': user,
        'otp_code': otp_code,
    }

    try:
        html_message = render_to_string('accounts/emails/otp_verification.html', context)
        plain_message = render_to_string('accounts/emails/otp_verification.txt', context)
    except Exception as e:
        logger.warning(f"Failed to render OTP email template, using fallback: {e}")
        plain_message = f"Hello {user.username},\n\nYour Campus Marketplace OTP verification code is: {otp_code}\n\nThis code expires in 10 minutes."
        html_message = None

    print("\n=======================================================", flush=True)
    print("[CAMPUS MARKETPLACE OTP DISPATCHED]", flush=True)
    print(f"To: {user.email}", flush=True)
    print(f"User: {user.username}", flush=True)
    print(f"OTP Code: {otp_code}", flush=True)
    print("Expires in: 10 minutes", flush=True)
    print("=======================================================\n", flush=True)

    # 1. Attempt HTTPS transactional email (works when SMTP ports are blocked)
    if _try_https_email(user.email, subject, html_message, plain_message):
        return True

    # 2. Attempt standard SMTP
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"OTP verification email successfully sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP verification email to {user.email}: {e}")
        print(f"[!] [EMAIL SMTP NOTICE] Failed to send via SMTP ({e}). Fallback code remains: {otp_code}", flush=True)
        return False


def send_password_reset_otp_email(user, otp_code: str) -> bool:
    """
    Dispatches a branded HTML and plain-text password reset email with the OTP code,
    10-minute validity, and security advisory. Returns True on success, False on failure.
    """
    subject = f"Your Campus Marketplace Password Reset Code: {otp_code}"
    context = {
        'user': user,
        'otp_code': otp_code,
    }

    try:
        html_message = render_to_string('accounts/emails/password_reset_otp.html', context)
        plain_message = render_to_string('accounts/emails/password_reset_otp.txt', context)
    except Exception as e:
        logger.warning(f"Failed to render password reset OTP email template, using fallback: {e}")
        plain_message = (
            f"Hello {user.username},\n\n"
            f"Your Campus Marketplace password reset code is: {otp_code}\n\n"
            f"This code expires in 10 minutes.\n\n"
            f"If you did not request this, please ignore this email."
        )
        html_message = None

    print("\n=======================================================", flush=True)
    print("[CAMPUS MARKETPLACE PASSWORD RESET OTP DISPATCHED]", flush=True)
    print(f"To: {user.email}", flush=True)
    print(f"User: {user.username}", flush=True)
    print(f"Reset OTP Code: {otp_code}", flush=True)
    print("Expires in: 10 minutes", flush=True)
    print("=======================================================\n", flush=True)

    # 1. Attempt HTTPS transactional email
    if _try_https_email(user.email, subject, html_message, plain_message):
        return True

    # 2. Attempt standard SMTP
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Password reset OTP email successfully sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset OTP email to {user.email}: {e}")
        print(f"[!] [EMAIL SMTP NOTICE] Failed to send password reset email via SMTP ({e}). Fallback code remains: {otp_code}", flush=True)
        return False
