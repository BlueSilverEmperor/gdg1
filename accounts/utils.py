import secrets
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_otp() -> str:
    """
    Generate a cryptographically secure 6-digit numeric OTP (100000 - 999999).
    """
    # secrets.randbelow(900000) produces 0 .. 899999
    # + 100000 ensures 100000 .. 999999
    code = secrets.randbelow(900000) + 100000
    return f"{code:06d}"


def send_otp_email(user, otp_code: str) -> bool:
    """
    Dispatches a branded HTML and plain-text email with the OTP code
    and expiration details. Returns True on success, False on failure.
    """
    subject = f"{otp_code} is your Campus Marketplace verification code"
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

    try:
        print("\n=======================================================", flush=True)
        print("[CAMPUS MARKETPLACE OTP DISPATCHED]", flush=True)
        print(f"To: {user.email}", flush=True)
        print(f"User: {user.username}", flush=True)
        print(f"OTP Code: {otp_code}", flush=True)
        print("Expires in: 10 minutes", flush=True)
        print("=======================================================\n", flush=True)

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
