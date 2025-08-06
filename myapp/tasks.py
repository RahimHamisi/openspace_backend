from django.core.mail import send_mail
from django.conf import settings # type: ignore
from celery import shared_task

@shared_task
def send_verification_email(email, verification_url):
    """
    Task to send email verification asynchronously.
    """
    subject = "Email Verification"
    message = f"Please verify your email by clicking on this link: {verification_url}"
    from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=[email],
    )